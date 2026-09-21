"""Contract tests for Subsystem S5.2.A Assessment Policy contracts."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.contracts.base import BaseContract
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.roadmap.contracts import NodeType
from study_engine.state.policy_contracts import (
    ActorType,
    AssessmentPolicy,
    CriteriaEvaluationResult,
    CriteriaEvaluationVerdict,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
)


def _make_dummy_evidence(
    evidence_type: EvidenceType = EvidenceType.CONCEPTUAL_EXPLANATION,
    outcome: EvidenceOutcome = EvidenceOutcome.PASS,
    score: float = 0.9,
    actor_type: ActorType = ActorType.AI_TUTOR,
    actor_id: str = "socratic-tutor",
) -> EvidenceRecord:
    return EvidenceRecord(
        record_id="rec-1",
        node_id="proc-intro",
        evidence_type=evidence_type,
        outcome=outcome,
        score=score,
        timestamp=datetime.now(timezone.utc),
        actor_type=actor_type,
        actor_id=actor_id,
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
    )


def _make_dummy_criteria() -> NodeAssessmentCriteria:
    req = EvidenceRequirement(
        requirement_id="req-conceptual",
        evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
        min_count=2,
        min_score=0.8,
        requires_audit_approved=True,
    )
    return NodeAssessmentCriteria(
        criteria_id="crit-topic-default",
        target_node_type=NodeType.TOPIC,
        requirements=(req,),
        regression_threshold_failures=2,
        allow_exempt=True,
    )


def test_contracts_immutability():
    """Verify state and policy models are frozen against in-place mutation."""
    ev = _make_dummy_evidence()
    with pytest.raises(ValidationError):
        ev.score = 0.5  # type: ignore[misc]

    crit = _make_dummy_criteria()
    with pytest.raises(ValidationError):
        crit.allow_exempt = False  # type: ignore[misc]

    policy = AssessmentPolicy(
        policy_id="policy-default",
        title="Default Policy",
        version="1.0.0",
        default_criteria={NodeType.TOPIC: crit},
        node_overrides={},
        canonical_policy_id="0" * 64,
    )
    with pytest.raises(ValidationError):
        policy.title = "Mutated Title"  # type: ignore[misc]

    result = CriteriaEvaluationResult(
        criteria_id="crit-1",
        verdict=CriteriaEvaluationVerdict.SATISFIED,
        satisfied_requirements=("req-conceptual",),
        missing_requirements=(),
        subsequent_failures_count=0,
        evaluation_timestamp=datetime.now(timezone.utc),
        rationale="All criteria met",
    )
    with pytest.raises(ValidationError):
        new_verdict = CriteriaEvaluationVerdict.REGRESSED
        result.verdict = new_verdict  # type: ignore[misc]


def test_evidence_record_score_range():

    """Verify score is bounded in [0.0, 1.0]."""
    valid = _make_dummy_evidence(score=0.0)
    assert valid.score == 0.0
    valid_max = _make_dummy_evidence(score=1.0)
    assert valid_max.score == 1.0

    with pytest.raises(ValidationError):
        _make_dummy_evidence(score=-0.1)

    with pytest.raises(ValidationError):
        _make_dummy_evidence(score=1.01)


def test_manual_override_sovereignty_guard():
    """Verify MANUAL_OVERRIDE strictly enforces human sovereignty."""
    valid_override = EvidenceRecord(
        record_id="rec-override-1",
        node_id="proc-intro",
        evidence_type=EvidenceType.MANUAL_OVERRIDE,
        outcome=EvidenceOutcome.PASS,
        score=1.0,
        timestamp=datetime.now(timezone.utc),
        actor_type=ActorType.HUMAN,
        actor_id="teacher-agustin",
        rationale="Estudiante demostró equivalencia universitaria",
        roadmap_revision_id="a" * 64,
        policy_revision_id="b" * 64,
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
    )
    assert valid_override.actor_type == ActorType.HUMAN

    # 1. AI_TUTOR cannot emit MANUAL_OVERRIDE
    with pytest.raises(ValidationError) as exc_ai:
        EvidenceRecord(
            record_id="rec-fake-1",
            node_id="proc-intro",
            evidence_type=EvidenceType.MANUAL_OVERRIDE,
            outcome=EvidenceOutcome.PASS,
            score=1.0,
            timestamp=datetime.now(timezone.utc),
            actor_type=ActorType.AI_TUTOR,
            actor_id="tutor-llm",
            rationale="Auto-exempting student",
            roadmap_revision_id="a" * 64,
            policy_revision_id="b" * 64,
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        )
    assert "Only HUMAN actors may produce MANUAL_OVERRIDE" in str(exc_ai.value)

    # 2. TOOL_VERIFIER cannot emit MANUAL_OVERRIDE
    with pytest.raises(ValidationError) as exc_tool:
        EvidenceRecord(
            record_id="rec-fake-2",
            node_id="proc-intro",
            evidence_type=EvidenceType.MANUAL_OVERRIDE,
            outcome=EvidenceOutcome.PASS,
            score=1.0,
            timestamp=datetime.now(timezone.utc),
            actor_type=ActorType.TOOL_VERIFIER,
            actor_id="wireshark-engine",
            rationale="Tool self-exemption",
            roadmap_revision_id="a" * 64,
            policy_revision_id="b" * 64,
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        )
    assert "Only HUMAN actors may produce MANUAL_OVERRIDE" in str(
        exc_tool.value
    )

    # 3. Empty rationale forbidden
    with pytest.raises(ValidationError) as exc_rat:
        EvidenceRecord(
            record_id="rec-fake-3",
            node_id="proc-intro",
            evidence_type=EvidenceType.MANUAL_OVERRIDE,
            outcome=EvidenceOutcome.PASS,
            score=1.0,
            timestamp=datetime.now(timezone.utc),
            actor_type=ActorType.HUMAN,
            actor_id="teacher",
            rationale="",
            roadmap_revision_id="a" * 64,
            policy_revision_id="b" * 64,
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        )
    assert "requires a non-empty rationale" in str(exc_rat.value)

    # 4. Missing revision IDs forbidden
    with pytest.raises(ValidationError):
        EvidenceRecord(
            record_id="rec-fake-4",
            node_id="proc-intro",
            evidence_type=EvidenceType.MANUAL_OVERRIDE,
            outcome=EvidenceOutcome.PASS,
            score=1.0,
            timestamp=datetime.now(timezone.utc),
            actor_type=ActorType.HUMAN,
            actor_id="teacher",
            rationale="Valid reason",
            roadmap_revision_id=None,
            policy_revision_id="b" * 64,
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        )


def test_closed_enums():
    """Verify all policy enums contain expected closed variants."""
    assert set(EvidenceType) == {
        EvidenceType.CONCEPTUAL_EXPLANATION,
        EvidenceType.CODE_EXECUTION,
        EvidenceType.LAB_TELEMETRY,
        EvidenceType.DIAGNOSTIC_QUIZ,
        EvidenceType.MANUAL_OVERRIDE,
    }
    assert set(EvidenceOutcome) == {
        EvidenceOutcome.PASS,
        EvidenceOutcome.FAIL,
        EvidenceOutcome.INCONCLUSIVE,
    }
    assert set(ActorType) == {
        ActorType.HUMAN,
        ActorType.AI_TUTOR,
        ActorType.TOOL_VERIFIER,
    }
    assert set(CriteriaEvaluationVerdict) == {
        CriteriaEvaluationVerdict.SATISFIED,
        CriteriaEvaluationVerdict.UNSATISFIED,
        CriteriaEvaluationVerdict.REGRESSED,
        CriteriaEvaluationVerdict.EXEMPT,
    }
