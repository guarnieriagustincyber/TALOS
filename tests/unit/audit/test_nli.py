"""Unit tests for NLI judge and aggregator in Subsystem S4.4."""

import pytest

from study_engine.audit.contracts import (
    AuditVerdict,
    ClaimSupportVerdict,
    ClaimType,
    ClaimVerification,
    LexicalAnomalyStatus,
    LexicalDiagnostics,
)
from study_engine.audit.nli import MockNLIJudge, NLIAggregator


def _make_dummy_claim_verification(
    verdict: ClaimSupportVerdict,
) -> ClaimVerification:
    diag = LexicalDiagnostics(
        status=LexicalAnomalyStatus.NO_ANOMALY,
        token_overlap_ratio=0.8,
    )
    return ClaimVerification(
        claim_index=0,
        claim_text="Afirmación evaluada.",
        claim_type=ClaimType.FACTUAL,
        cited_tags=("E1",),
        lexical_diagnostics=diag,
        nli_verdict=verdict,
    )


def test_mock_nli_default_behavior():
    """Verify default mock judge returns configured default verdict."""
    judge = MockNLIJudge(default_verdict=ClaimSupportVerdict.ENTAILED)
    res = judge.evaluate_claim(premise="P", hypothesis="H")
    assert res.verdict == ClaimSupportVerdict.ENTAILED
    assert res.confidence == 0.90


def test_mock_nli_canned_verdict():
    """Verify mock judge dispatches canned verdicts based on match."""
    canned = {
        "contradictorio": ClaimSupportVerdict.CONTRADICTED,
        "sin_sustento": ClaimSupportVerdict.NOT_ENTAILED,
    }
    judge = MockNLIJudge(canned_verdicts=canned)

    res1 = judge.evaluate_claim(
        premise="P", hypothesis="Esto es contradictorio."
    )
    assert res1.verdict == ClaimSupportVerdict.CONTRADICTED

    res2 = judge.evaluate_claim(premise="P", hypothesis="Dato sin_sustento.")
    assert res2.verdict == ClaimSupportVerdict.NOT_ENTAILED


def test_mock_nli_inject_error():
    """Verify error injection causes evaluate_claim to raise."""
    judge = MockNLIJudge(inject_error=RuntimeError("Judge offline"))
    with pytest.raises(RuntimeError) as exc_info:
        judge.evaluate_claim(premise="P", hypothesis="H")
    assert "Judge offline" in str(exc_info.value)


def test_nli_aggregator_rules():
    """Verify formal aggregation policy: CONTRADICTION > NOT_ENTAILED."""
    agg = NLIAggregator()

    # 1. Empty verifications -> APPROVED
    assert agg.aggregate([]) == AuditVerdict.APPROVED

    # 2. All entailed -> APPROVED
    c_ent = _make_dummy_claim_verification(ClaimSupportVerdict.ENTAILED)
    assert agg.aggregate([c_ent, c_ent]) == AuditVerdict.APPROVED

    # 3. Any contradicted -> REJECTED_CONTRADICTION
    c_con = _make_dummy_claim_verification(ClaimSupportVerdict.CONTRADICTED)
    c_not = _make_dummy_claim_verification(ClaimSupportVerdict.NOT_ENTAILED)
    c_una = _make_dummy_claim_verification(ClaimSupportVerdict.UNASSESSED)
    assert (
        agg.aggregate([c_ent, c_con, c_not])
        == AuditVerdict.REJECTED_CONTRADICTION
    )

    # 4. Any not entailed without contradiction -> REJECTED_UNSUPPORTED
    assert (
        agg.aggregate([c_ent, c_not, c_una])
        == AuditVerdict.REJECTED_UNSUPPORTED
    )

    assert agg.aggregate([c_ent, c_una]) == AuditVerdict.FLAGGED_UNASSESSED
