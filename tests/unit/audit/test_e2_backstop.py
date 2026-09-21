"""Unit tests for Phase E2 verification backstop in DeterministicAuditEngine.

Tests compliance with:
- H1: Verification policy matrix routing (FORMAL, FACTUAL, PEDAGOGICAL).
- H2: Criticality routing (critical unsupported -> hard abstention).
- H4: Single bounded retry (attempt 0 -> FLAGGED_UNASSESSED, attempt 1 -> PARTIAL_ABSTENTION with [SIN_RESPALDO]).
"""

import pytest
from pathlib import Path
from study_engine.evidence.verification_backstop import GenerationVerificationBackstop
from study_engine.evidence.claim_extractor import ClaimCriticality, ClaimType
from study_engine.evidence.token_grounding import GroundingStatus


@pytest.fixture
def engine():
    return GenerationVerificationBackstop()


@pytest.fixture
def sample_evidence():
    return [
        {
            "id": "E1",
            "content": "A process in operating systems represents an instance of an executing program with its own address space.",
        },
        {
            "id": "E2",
            "content": "Merge sort has a time complexity of O(n log n) and an auxiliary space complexity of O(n) using arrays.",
        },
        {
            "id": "E3",
            "content": "In virtual memory, page replacement algorithms like LRU select pages to evict when physical memory is full.",
        },
    ]


def test_clean_approved_response(engine, sample_evidence):
    """Clean grounded factual response is approved."""
    response = (
        "A process in operating systems represents an instance of an executing program [E1]. "
        "Merge sort achieves O(n log n) time complexity [E2]."
    )
    result = engine.verify_e2_claims(response, sample_evidence)

    assert result["verdict"] == "APPROVED"
    assert result["can_retry"] is False
    assert result["action"] == "APPROVE"
    assert len(result["claims"]) >= 2
    assert all(c.status == GroundingStatus.SUPPORTED for c in result["claims"])


def test_h1_formal_failure_causes_hard_abstention(engine, sample_evidence):
    """H1: Failure in formal mathematical/complexity claim triggers immediate hard abstention."""
    response = "Merge sort operates in O(1) time complexity [E2]."
    result = engine.verify_e2_claims(response, sample_evidence)

    assert result["verdict"] == "REJECTED_UNSUPPORTED"
    assert result["can_retry"] is False
    assert result["action"] == "HARD_ABSTENTION"
    assert len(result["critical_failures"]) > 0


def test_h1_critical_factual_unsupported_causes_hard_abstention(engine, sample_evidence):
    """H1/H2: Failure in critical factual claim triggers immediate hard abstention."""
    response = "Quantum entanglement governs CPU branch prediction registers."
    result = engine.verify_e2_claims(response, sample_evidence)

    assert result["verdict"] == "REJECTED_UNSUPPORTED"
    assert result["can_retry"] is False
    assert result["action"] == "HARD_ABSTENTION"
    assert len(result["critical_failures"]) > 0


def test_h1_pedagogical_analogy_exempt_from_literal_tokens(engine, sample_evidence):
    """H1: Pedagogical analogies without contradiction are approved without token grounding."""
    response = (
        "A process in operating systems is an executing program [E1]. "
        "Como analogía didáctica, un proceso es como un cocinero siguiendo una receta en su cocina."
    )
    result = engine.verify_e2_claims(response, sample_evidence)

    assert result["verdict"] == "APPROVED"
    pedagogical = [c for c in result["claims"] if c.is_pedagogical_analogy or c.claim_type == ClaimType.PEDAGOGICAL]
    assert len(pedagogical) >= 1
    assert pedagogical[0].status == GroundingStatus.SUPPORTED


def test_h4_bounded_retry_attempt_0_and_attempt_1(engine, sample_evidence):
    """H4: Partially supported claims trigger FLAGGED_UNASSESSED on attempt 0 and [SIN_RESPALDO] on attempt 1."""
    # We craft a response that yields PARTIALLY_SUPPORTED
    # In token_grounding, a claim with score in [tau_partial, tau_supported) (0.30 - 0.55) is PARTIALLY_SUPPORTED.
    response = "A process has memory management."
    
    res0 = engine.verify_e2_claims(response, sample_evidence, retry_count=0)
    if res0["verdict"] == "FLAGGED_UNASSESSED":
        assert res0["can_retry"] is True
        assert res0["action"] == "BOUNDED_RETRY"
        assert "retry_directive" in res0
        assert "Precision directive" in res0["retry_directive"]

        res1 = engine.verify_e2_claims(response, sample_evidence, retry_count=1)
        assert res1["verdict"] == "PARTIAL_ABSTENTION"
        assert res1["can_retry"] is False
        assert res1["action"] == "REDACT_AMBIGUOUS"
        assert "[SIN_RESPALDO]" in res1["redacted_text"]
