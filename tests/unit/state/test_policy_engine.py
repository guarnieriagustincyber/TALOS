"""Unit tests for PolicyEngine and evaluation logic in Subsystem S5.2.A."""

from datetime import datetime, timedelta, timezone
from typing import Optional
import pytest


from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.roadmap.contracts import NodeType
from study_engine.state.policy_contracts import (
    ActorType,
    AssessmentPolicy,
    CriteriaEvaluationVerdict,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
    PolicyHashMismatchError,
    SovereignExemptionViolationError,
)
from study_engine.state.policy_engine import (
    compute_canonical_policy_id,
    evaluate_node_criteria,
    validate_policy_hash,
)


def _make_criteria(
    min_count: int = 1,
    min_score: float = 0.8,
    max_age_days: Optional[int] = None,
    requires_audit_approved: bool = False,
    required_tool_backend: Optional[str] = None,
    regression_threshold_failures: int = 2,
    allow_exempt: bool = True,
    target_node_id: str = "node-proc",
    evidence_type: EvidenceType = EvidenceType.CONCEPTUAL_EXPLANATION,
) -> NodeAssessmentCriteria:
    req = EvidenceRequirement(
        requirement_id="req-1",
        evidence_type=evidence_type,
        min_count=min_count,
        min_score=min_score,
        max_age_days=max_age_days,
        requires_audit_approved=requires_audit_approved,
        required_tool_backend=required_tool_backend,
    )

    return NodeAssessmentCriteria(
        criteria_id="crit-proc",
        target_node_id=target_node_id,
        requirements=(req,),
        regression_threshold_failures=regression_threshold_failures,
        allow_exempt=allow_exempt,
    )


def _make_evidence(
    record_id: str,
    outcome: EvidenceOutcome,
    timestamp: datetime,
    score: float = 1.0,
    evidence_type: EvidenceType = EvidenceType.CONCEPTUAL_EXPLANATION,
    node_id: str = "node-proc",
    audit_verdict: str = None,
    tool_backend: str = None,
) -> EvidenceRecord:
    return EvidenceRecord(
        record_id=record_id,
        node_id=node_id,
        evidence_type=evidence_type,
        outcome=outcome,
        score=score,
        timestamp=timestamp,
        actor_type=ActorType.AI_TUTOR,
        actor_id="tutor-1",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        audit_verdict=audit_verdict,
        tool_backend=tool_backend,
    )


def test_compute_canonical_policy_id_stability():
    """Verify canonical policy hash is deterministic across dict orders."""
    c1 = _make_criteria()
    c2 = _make_criteria(target_node_id="node-net")

    hash1 = compute_canonical_policy_id(
        policy_id="pol-1",
        title="Policy 1",
        version="1.0.0",
        default_criteria={NodeType.TOPIC: c1, NodeType.LAB: c2},
        node_overrides={},
    )
    hash2 = compute_canonical_policy_id(
        policy_id="pol-1",
        title="Policy 1",
        version="1.0.0",
        default_criteria={NodeType.LAB: c2, NodeType.TOPIC: c1},
        node_overrides={},
    )
    assert hash1 == hash2
    assert len(hash1) == 64

    # Any change mutates hash
    c1_mutated = _make_criteria(min_score=0.9)
    hash_diff = compute_canonical_policy_id(
        policy_id="pol-1",
        title="Policy 1",
        version="1.0.0",
        default_criteria={NodeType.TOPIC: c1_mutated, NodeType.LAB: c2},
        node_overrides={},
    )
    assert hash_diff != hash1


def test_validate_policy_hash_strict_rejection():
    """Verify validate_policy_hash rejects tampered hash mismatch."""
    c1 = _make_criteria()

    computed_hash = compute_canonical_policy_id(
        policy_id="pol-1",
        title="Policy 1",
        version="1.0.0",
        default_criteria={NodeType.TOPIC: c1},
        node_overrides={},
    )
    valid_policy = AssessmentPolicy(
        policy_id="pol-1",
        title="Policy 1",
        version="1.0.0",
        default_criteria={NodeType.TOPIC: c1},
        node_overrides={},
        canonical_policy_id=computed_hash,
    )
    # Valid hash passes
    validate_policy_hash(valid_policy)

    # Tampered declared hash raises PolicyHashMismatchError
    tampered_policy = AssessmentPolicy(
        policy_id="pol-1",
        title="Policy 1",
        version="1.0.0",
        default_criteria={NodeType.TOPIC: c1},
        node_overrides={},
        canonical_policy_id="f" * 64,
    )
    with pytest.raises(PolicyHashMismatchError):
        validate_policy_hash(tampered_policy)


def test_evaluate_satisfaction_and_insufficient_evidence():
    """Verify evaluation correctly flags SATISFIED vs UNSATISFIED."""
    criteria = _make_criteria(min_count=2, min_score=0.8)
    now = datetime.now(timezone.utc)

    e1 = _make_evidence("e1", EvidenceOutcome.PASS, now - timedelta(hours=2))
    # Only 1 PASS out of 2 required -> UNSATISFIED
    res_unsat = evaluate_node_criteria(criteria, [e1], now)
    assert res_unsat.verdict == CriteriaEvaluationVerdict.UNSATISFIED
    assert "req-1" in res_unsat.missing_requirements

    # Second PASS arrives -> SATISFIED
    e2 = _make_evidence("e2", EvidenceOutcome.PASS, now - timedelta(hours=1))
    res_sat = evaluate_node_criteria(criteria, [e1, e2], now)
    assert res_sat.verdict == CriteriaEvaluationVerdict.SATISFIED
    assert "req-1" in res_sat.satisfied_requirements


def test_evaluate_s4_audit_requirement():
    """Verify S4.4 audit is enforced when requires_audit_approved=True."""
    criteria = _make_criteria(requires_audit_approved=True)
    now = datetime.now(timezone.utc)

    # Unapproved evidence does not qualify
    e_unapproved = _make_evidence(
        "e1", EvidenceOutcome.PASS, now, audit_verdict="FLAGGED_UNASSESSED"
    )
    res1 = evaluate_node_criteria(criteria, [e_unapproved], now)
    assert res1.verdict == CriteriaEvaluationVerdict.UNSATISFIED

    # Approved evidence qualifies
    e_approved = _make_evidence(
        "e2", EvidenceOutcome.PASS, now, audit_verdict="APPROVED"
    )
    res2 = evaluate_node_criteria(criteria, [e_approved], now)
    assert res2.verdict == CriteriaEvaluationVerdict.SATISFIED


def test_evaluate_tool_verifier_backend():
    """Verify tool telemetry requires matching backend without S4.4."""
    criteria = _make_criteria(
        required_tool_backend="wireshark",
        evidence_type=EvidenceType.LAB_TELEMETRY,
    )
    now = datetime.now(timezone.utc)

    e_wrong_backend = _make_evidence(

        "e1",
        EvidenceOutcome.PASS,
        now,
        evidence_type=EvidenceType.LAB_TELEMETRY,
        tool_backend="tcpdump",
    )
    res1 = evaluate_node_criteria(criteria, [e_wrong_backend], now)
    assert res1.verdict == CriteriaEvaluationVerdict.UNSATISFIED

    e_correct_backend = _make_evidence(
        "e2",
        EvidenceOutcome.PASS,
        now,
        evidence_type=EvidenceType.LAB_TELEMETRY,
        tool_backend="wireshark",
    )
    res2 = evaluate_node_criteria(criteria, [e_correct_backend], now)
    assert res2.verdict == CriteriaEvaluationVerdict.SATISFIED


def test_evaluate_time_travel_and_decay():
    """Verify as_of_time filtering and max_age_days decay."""
    now = datetime.now(timezone.utc)
    criteria = _make_criteria(max_age_days=7)

    # Future evidence relative to as_of_time is ignored
    past_as_of = now - timedelta(days=2)
    e_future = _make_evidence("e1", EvidenceOutcome.PASS, now)
    res_future = evaluate_node_criteria(criteria, [e_future], past_as_of)
    assert res_future.verdict == CriteriaEvaluationVerdict.UNSATISFIED

    # Evidence older than max_age_days is decayed
    e_old = _make_evidence(
        "e2", EvidenceOutcome.PASS, now - timedelta(days=10)
    )
    res_decayed = evaluate_node_criteria(criteria, [e_old], now)
    assert res_decayed.verdict == CriteriaEvaluationVerdict.UNSATISFIED


def test_evaluate_alternating_vs_consecutive_regression():
    """Verify regression counts only failures strictly after last PASS."""
    criteria = _make_criteria(min_count=1, regression_threshold_failures=2)
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)

    # Sequence P -> F -> P -> F
    p1 = _make_evidence("p1", EvidenceOutcome.PASS, t0)
    f1 = _make_evidence("f1", EvidenceOutcome.FAIL, t0 + timedelta(hours=1))
    p2 = _make_evidence("p2", EvidenceOutcome.PASS, t0 + timedelta(hours=2))
    f2 = _make_evidence("f2", EvidenceOutcome.FAIL, t0 + timedelta(hours=3))

    as_of = t0 + timedelta(hours=4)
    res_alt = evaluate_node_criteria(criteria, [p1, f1, p2, f2], as_of)
    # Only f2 is strictly after p2 -> fail_count=1 < threshold(2) -> SATISFIED
    assert res_alt.verdict == CriteriaEvaluationVerdict.SATISFIED
    assert res_alt.subsequent_failures_count == 1

    # Now add another failure: P -> F -> P -> F -> F
    f3 = _make_evidence("f3", EvidenceOutcome.FAIL, t0 + timedelta(hours=5))
    as_of_reg = t0 + timedelta(hours=6)
    res_reg = evaluate_node_criteria(
        criteria, [p1, f1, p2, f2, f3], as_of_reg
    )
    # f2 and f3 are after p2 -> fail_count=2 >= threshold(2) -> REGRESSED
    assert res_reg.verdict == CriteriaEvaluationVerdict.REGRESSED
    assert res_reg.subsequent_failures_count == 2


def test_evaluate_sovereign_exemption_and_disallowed():

    """Verify MANUAL_OVERRIDE produces EXEMPT, or error if disallowed."""
    criteria_allowed = _make_criteria(allow_exempt=True)
    now = datetime.now(timezone.utc)
    override = EvidenceRecord(
        record_id="rec-ovr",
        node_id="node-proc",
        evidence_type=EvidenceType.MANUAL_OVERRIDE,
        outcome=EvidenceOutcome.PASS,
        score=1.0,
        timestamp=now,
        actor_type=ActorType.HUMAN,
        actor_id="teacher",
        rationale="Exención pedagógica",
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
    )
    res_exempt = evaluate_node_criteria(criteria_allowed, [override], now)
    assert res_exempt.verdict == CriteriaEvaluationVerdict.EXEMPT

    # If criteria disallows exempt, raise SovereignExemptionViolationError
    criteria_disallowed = _make_criteria(allow_exempt=False)
    with pytest.raises(SovereignExemptionViolationError):
        evaluate_node_criteria(criteria_disallowed, [override], now)
