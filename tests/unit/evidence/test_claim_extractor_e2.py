"""Unit tests for DeterministicClaimExtractor and SymbolicVerifier formal verification (E2.2 & E2.3)."""

import pytest
from study_engine.evidence.claim_extractor import (
    ClaimCriticality,
    ClaimType,
    DeterministicClaimExtractor,
    ExtractedClaim,
)
from study_engine.evidence.symbolic_verifier import (
    SymbolicVerdict,
    SymbolicVerifier,
)


def test_segmentation_with_abbreviations_and_citations():
    extractor = DeterministicClaimExtractor()
    text = (
        "El PCB contiene el contador de programa [E1]. "
        "En la memoria e.g. RAM, el valor de PI es 3.14 y no se pierde. "
        "La función termina correctamente [E1, E2]."
    )
    claims = extractor.extract_claims(text)
    assert len(claims) == 3
    assert claims[0].cited_evidence_indices == ["E1"]
    assert "3.14" in claims[1].text
    assert claims[2].cited_evidence_indices == ["E1", "E2"]


def test_claim_type_classification():
    extractor = DeterministicClaimExtractor()

    # Conversational
    c1 = extractor.extract_claims("¡Hola! Espero que tengas un excelente día de estudio.")
    assert len(c1) == 1
    assert c1[0].claim_type == ClaimType.CONVERSATIONAL
    assert c1[0].criticality == ClaimCriticality.NON_CRITICAL

    # Pedagogical
    c2 = extractor.extract_claims("Podemos imaginar la memoria RAM como una hilera de casilleros postales.")
    assert len(c2) == 1
    assert c2[0].claim_type == ClaimType.PEDAGOGICAL
    assert c2[0].is_pedagogical_analogy is True
    assert c2[0].criticality == ClaimCriticality.NON_CRITICAL

    # Formal Complexity
    c3 = extractor.extract_claims("El algoritmo de búsqueda binaria tiene complejidad temporal O(log n).")
    assert len(c3) == 1
    assert c3[0].claim_type == ClaimType.FORMAL_COMPLEXITY
    assert c3[0].criticality == ClaimCriticality.CRITICAL

    # Formal Arithmetic
    c4 = extractor.extract_claims("Con base 1000 e índice 3 de enteros de 4 bytes, la dirección es 1012.")
    assert len(c4) == 1
    assert c4[0].claim_type == ClaimType.FORMAL_ARITHMETIC
    assert c4[0].criticality == ClaimCriticality.CRITICAL

    # Factual Textual (Critical)
    c5 = extractor.extract_claims("La exclusión mutua previene condiciones de carrera en secciones críticas.")
    assert len(c5) == 1
    assert c5[0].claim_type == ClaimType.FACTUAL_TEXTUAL
    assert c5[0].criticality == ClaimCriticality.CRITICAL


def test_symbolic_verifier_formal_claim():
    verifier = SymbolicVerifier()

    # Valid complexity
    res1 = verifier.verify_formal_claim(
        claim_text="La búsqueda binaria tiene complejidad O(log n)",
        claim_type="FORMAL_COMPLEXITY",
        formal_data={"algorithm": "binary_search", "complexity": "O(log n)"},
    )
    assert res1.verdict == SymbolicVerdict.VERIFIED_TRUE

    # Invalid complexity (Hallucination)
    res2 = verifier.verify_formal_claim(
        claim_text="La búsqueda binaria tiene complejidad O(n^2)",
        claim_type="FORMAL_COMPLEXITY",
        formal_data={"algorithm": "binary_search", "complexity": "O(n^2)"},
    )
    assert res2.verdict == SymbolicVerdict.REJECTED_HALLUCINATION

    # Valid pointer arithmetic
    res3 = verifier.verify_formal_claim(
        claim_text="En un arreglo con base 1000 de enteros de 4 bytes, el índice 3 reside en 1012",
        claim_type="FORMAL_ARITHMETIC",
        formal_data={"base": 1000, "size": 4, "index": 3, "address": 1012},
    )
    assert res3.verdict == SymbolicVerdict.VERIFIED_TRUE

    # Invalid pointer arithmetic (Hallucination)
    res4 = verifier.verify_formal_claim(
        claim_text="En un arreglo con base 1000 de enteros de 4 bytes, el índice 3 reside en 1024",
        claim_type="FORMAL_ARITHMETIC",
        formal_data={"base": 1000, "size": 4, "index": 3, "address": 1024},
    )
    assert res4.verdict == SymbolicVerdict.REJECTED_HALLUCINATION
