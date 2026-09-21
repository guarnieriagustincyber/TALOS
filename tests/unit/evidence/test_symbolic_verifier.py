"""Unit tests for SymbolicVerifier with formal Big O and AST math."""

import pytest

from study_engine.evidence.symbolic_verifier import (
    SymbolicVerdict,
    SymbolicVerifier,
    normalize_big_o,
    safe_eval_arithmetic,
)


def test_pointer_arithmetic_verification():
    verifier = SymbolicVerifier()

    # Correct Q-SIMP-07 case: base=1000, index=3, sizeof(int)=4 -> 1012
    res_valid = verifier.verify_memory_offset(
        base_address=1000,
        index=3,
        type_size_bytes=4,
        claimed_address=1012,
    )
    assert res_valid.verdict == SymbolicVerdict.VERIFIED_TRUE
    assert res_valid.expected_value == "1012"

    # Hallucination case: 1016 claimed instead of 1012
    res_invalid = verifier.verify_memory_offset(
        base_address=1000,
        index=3,
        type_size_bytes=4,
        claimed_address=1016,
    )
    assert res_invalid.verdict == SymbolicVerdict.REJECTED_HALLUCINATION


def test_big_o_normalization_rules():
    # Rule 1: Theta(f) -> O(f)
    norm, valid = normalize_big_o("θ(n)")
    assert norm == "o(n)"
    assert valid is True

    # Rule 2: Constant factor removal O(5n) -> O(n)
    norm, valid = normalize_big_o("O(5n)")
    assert norm == "o(n)"
    assert valid is True

    # Rule 3: O(f + g) -> dominant term O(n^2 + n) -> O(n^2)
    norm, valid = normalize_big_o("O(n^2 + n)")
    assert norm == "o(n^2)"
    assert valid is True

    # Rule 4: Omega bounds marked UNVERIFIABLE
    norm, valid = normalize_big_o("Ω(n)")
    assert valid is False


def test_asymptotic_complexity_comparison():
    verifier = SymbolicVerifier()

    # Valid: binary search O(log n) is faster than sequential search O(n)
    res_valid = verifier.verify_complexity_comparison(
        algo_or_term_a="búsqueda binaria",
        algo_or_term_b="búsqueda secuencial",
        claimed_relation="faster",
    )
    assert res_valid.verdict == SymbolicVerdict.VERIFIED_TRUE

    # Hallucination: claiming sequential search is faster than binary search
    res_invalid = verifier.verify_complexity_comparison(
        algo_or_term_a="búsqueda secuencial",
        algo_or_term_b="búsqueda binaria",
        claimed_relation="faster",
    )
    assert res_invalid.verdict == SymbolicVerdict.REJECTED_HALLUCINATION


def test_safe_ast_arithmetic_evaluator():
    # Valid expressions
    assert safe_eval_arithmetic("1000 + 3 * 4") == 1012.0
    assert safe_eval_arithmetic("(256 / 4) + 16") == 80.0
    assert safe_eval_arithmetic("2^10") == 1024.0

    # Malicious or disallowed inputs return None safely
    assert safe_eval_arithmetic("__import__('os').system('ls')") is None
    assert safe_eval_arithmetic("exec('print(1)')") is None
    assert safe_eval_arithmetic("open('/etc/passwd').read()") is None
    assert safe_eval_arithmetic("x + 1") is None


def test_verify_generation_claims_hook():
    verifier = SymbolicVerifier()
    response_text = (
        "La dirección exacta en memoria RAM del índice 3 es 1012. "
        "Además, la búsqueda binaria permite reducir la complejidad temporal frente a la búsqueda secuencial."
    )
    query_context = {
        "base_address": 1000,
        "index": 3,
        "type_size": 4,
    }

    results = verifier.verify_generation_claims(response_text, query_context)
    assert len(results) >= 2
    assert all(r.verdict == SymbolicVerdict.VERIFIED_TRUE for r in results)
