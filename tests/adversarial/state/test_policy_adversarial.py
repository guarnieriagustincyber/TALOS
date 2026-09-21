from datetime import datetime, timedelta, timezone
import pytest
from pydantic import ValidationError

from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.roadmap.contracts import NodeType
from study_engine.state.policy_contracts import (
    ActorType,
    CriteriaEvaluationVerdict,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
)
from study_engine.state.policy_engine import (
    compute_canonical_policy_id,
    evaluate_node_criteria,
)


def _make_req(

    req_id: str = "req-1",
    ev_type: EvidenceType = EvidenceType.CONCEPTUAL_EXPLANATION,
    min_count: int = 1,
    min_score: float = 0.8,
    max_age_days: int = None,
    requires_audit: bool = False,
) -> EvidenceRequirement:
    return EvidenceRequirement(
        requirement_id=req_id,
        evidence_type=ev_type,
        min_count=min_count,
        min_score=min_score,
        max_age_days=max_age_days,
        requires_audit_approved=requires_audit,
    )


def test_adversarial_ai_tutor_cannot_forge_manual_override():
    """Verify AI_TUTOR is forbidden from creating MANUAL_OVERRIDE records."""
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError) as exc_info:
        EvidenceRecord(
            record_id="adv-ovr-ai",
            node_id="proc-intro",
            evidence_type=EvidenceType.MANUAL_OVERRIDE,
            outcome=EvidenceOutcome.PASS,
            score=1.0,
            timestamp=now,
            actor_type=ActorType.AI_TUTOR,
            actor_id="gpt-4o-tutor",
            rationale="Prompt injection claimed user is proficient",
            roadmap_revision_id="0" * 64,
            policy_revision_id="1" * 64,
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        )
    assert "Only HUMAN actors may produce MANUAL_OVERRIDE" in str(
        exc_info.value
    )


def test_adversarial_tool_verifier_cannot_self_exempt():
    """Verify automated tool verifiers cannot emit MANUAL_OVERRIDE."""
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError) as exc_info:
        EvidenceRecord(
            record_id="adv-ovr-tool",
            node_id="proc-intro",
            evidence_type=EvidenceType.MANUAL_OVERRIDE,
            outcome=EvidenceOutcome.PASS,
            score=1.0,
            timestamp=now,
            actor_type=ActorType.TOOL_VERIFIER,
            actor_id="packet-tracer-sandbox",
            rationale="Simulated network converged",
            roadmap_revision_id="0" * 64,
            policy_revision_id="1" * 64,
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        )
    assert "Only HUMAN actors may produce MANUAL_OVERRIDE" in str(
        exc_info.value
    )


def test_adversarial_inconclusive_outcome_does_not_satisfy_nor_regress():
    """Verify INCONCLUSIVE outcome never satisfies nor triggers regression."""
    criteria = NodeAssessmentCriteria(

        criteria_id="crit-test",
        target_node_id="node-1",
        requirements=(_make_req(min_count=1),),
        regression_threshold_failures=2,
    )
    t0 = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

    # 1. Only INCONCLUSIVE -> UNSATISFIED
    e_inc = EvidenceRecord(
        record_id="inc-1",
        node_id="node-1",
        evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
        outcome=EvidenceOutcome.INCONCLUSIVE,
        score=0.9,
        timestamp=t0,
        actor_type=ActorType.AI_TUTOR,
        actor_id="tutor",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
    )
    res1 = evaluate_node_criteria(criteria, [e_inc], t0)
    assert res1.verdict == CriteriaEvaluationVerdict.UNSATISFIED

    # 2. PASS followed by INCONCLUSIVE -> Remains SATISFIED, not regressed
    e_pass = EvidenceRecord(
        record_id="pass-1",
        node_id="node-1",
        evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
        outcome=EvidenceOutcome.PASS,
        score=0.9,
        timestamp=t0 + timedelta(hours=1),
        actor_type=ActorType.AI_TUTOR,
        actor_id="tutor",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
    )
    e_inc2 = EvidenceRecord(
        record_id="inc-2",
        node_id="node-1",
        evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
        outcome=EvidenceOutcome.INCONCLUSIVE,
        score=0.5,
        timestamp=t0 + timedelta(hours=2),
        actor_type=ActorType.AI_TUTOR,
        actor_id="tutor",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
    )
    res2 = evaluate_node_criteria(
        criteria, [e_pass, e_inc2], t0 + timedelta(hours=3)
    )
    assert res2.verdict == CriteriaEvaluationVerdict.SATISFIED
    assert res2.subsequent_failures_count == 0


def test_adversarial_audit_rejected_never_satisfies():
    """Verify REJECTED or FLAGGED audit verdict blocks satisfaction."""
    criteria = NodeAssessmentCriteria(
        criteria_id="crit-test",
        target_node_id="node-1",
        requirements=(_make_req(requires_audit=True),),
    )
    now = datetime.now(timezone.utc)

    for bad_verdict in ("REJECTED_CONTRADICTION", "FLAGGED_UNASSESSED", None):
        e_bad = EvidenceRecord(
            record_id=f"rec-{bad_verdict}",
            node_id="node-1",
            evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
            outcome=EvidenceOutcome.PASS,
            score=0.95,
            timestamp=now,
            actor_type=ActorType.AI_TUTOR,
            actor_id="tutor",
            audit_verdict=bad_verdict,
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        )
        res = evaluate_node_criteria(criteria, [e_bad], now)
        assert res.verdict == CriteriaEvaluationVerdict.UNSATISFIED


def test_adversarial_foreign_node_evidence_ignored():
    """Verify evidence from other nodes does not count towards target."""
    criteria = NodeAssessmentCriteria(

        criteria_id="crit-test",
        target_node_id="node-target",
        requirements=(_make_req(min_count=1),),
    )
    now = datetime.now(timezone.utc)

    e_foreign = EvidenceRecord(
        record_id="foreign-1",
        node_id="other-node-99",
        evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
        outcome=EvidenceOutcome.PASS,
        score=1.0,
        timestamp=now,
        actor_type=ActorType.AI_TUTOR,
        actor_id="tutor",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
    )
    res = evaluate_node_criteria(criteria, [e_foreign], now)
    assert res.verdict == CriteriaEvaluationVerdict.UNSATISFIED


def test_adversarial_policy_hash_single_rule_mutation():
    """Verify mutating a single criteria rule alters canonical hash."""

    base_req = _make_req(min_score=0.8)
    base_crit = NodeAssessmentCriteria(
        criteria_id="c1",
        target_node_type=NodeType.TOPIC,
        requirements=(base_req,),
        regression_threshold_failures=2,
    )
    base_hash = compute_canonical_policy_id(
        policy_id="p1",
        title="P1",
        version="1.0.0",
        default_criteria={NodeType.TOPIC: base_crit},
        node_overrides={},
    )

    # 1. Mutate threshold failures (2 -> 3)
    mutated_crit1 = NodeAssessmentCriteria(
        criteria_id="c1",
        target_node_type=NodeType.TOPIC,
        requirements=(base_req,),
        regression_threshold_failures=3,
    )
    hash_mut1 = compute_canonical_policy_id(
        policy_id="p1",
        title="P1",
        version="1.0.0",
        default_criteria={NodeType.TOPIC: mutated_crit1},
        node_overrides={},
    )
    assert hash_mut1 != base_hash

    # 2. Mutate min_score (0.8 -> 0.81)
    mutated_req2 = _make_req(min_score=0.81)
    mutated_crit2 = NodeAssessmentCriteria(
        criteria_id="c1",
        target_node_type=NodeType.TOPIC,
        requirements=(mutated_req2,),
        regression_threshold_failures=2,
    )
    hash_mut2 = compute_canonical_policy_id(
        policy_id="p1",
        title="P1",
        version="1.0.0",
        default_criteria={NodeType.TOPIC: mutated_crit2},
        node_overrides={},
    )
    assert hash_mut2 != base_hash
