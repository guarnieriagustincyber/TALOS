"""Layer L4 Hostile Survival Audit: End-to-End Hostile Scenarios & Confusion Matrices.

Part of SYSTEM SURVIVAL AUDIT — SSA-0.
Modalidad: Read-Only / Red Team / No Patch.
"""

from datetime import datetime, timedelta, timezone
import pytest

from study_engine.contracts.assessment import (
    AggregationResult,
    AssessmentResult,
    AssessmentStatus,
    DimensionEvaluation,
    EvaluativeFact,
    EvaluativeFactType,
    FactObservability,
    InstrumentalFact,
    InstrumentalFactType,
    ObservationReference,
    SpecificationReference,
    compute_canonical_sha256,
)
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.contracts.evidence_ingestion import (
    AdmissionDecision,
    AdmissionResult,
    AdmissionTrace,
    GateVerdict,
    RejectionReason,
    SessionProvenanceContext,
)
from study_engine.contracts.spine import (
    ExecutionProvenanceSpine,
    SpineAssessment,
    SpineCurriculum,
    SpineExecution,
    SpineIdentity,
    SpineTerminalState,
)
from study_engine.roadmap.contracts import (
    CurricularRoadmap,
    DependencyType,
    NodeType,
    RoadmapDependency,
    RoadmapNode,
)
from study_engine.roadmap.engine import compute_canonical_revision_id
from study_engine.state.ingestion_engine import EvidenceIngestionEngine
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.policy_contracts import (
    ActorType,
    AssessmentPolicy,
    CriteriaEvaluationVerdict,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
)
from study_engine.state.policy_engine import compute_canonical_policy_id
from study_engine.state.state_contracts import (
    HistoryCutoffMode,
    NodeProgressStatus,
)
from study_engine.state.state_engine import derive_student_state


def _build_valid_assessment(
    task_sha: str = "0" * 64,
    rubric_sha: str = "1" * 64,
    assessed_at: datetime = None,
) -> AssessmentResult:
    now = assessed_at or datetime.now(timezone.utc)
    task_ref = SpecificationReference(
        specification_id="task-c-pointer",
        revision_id="rev-1",
        specification_sha256=task_sha,
    )
    rubric_ref = SpecificationReference(
        specification_id="rubric-c-pointer",
        revision_id="rev-1",
        specification_sha256=rubric_sha,
    )
    obs_ref = ObservationReference(
        observation_id="obs-1",
        execution_id="exec-1",
        effective_script_sha256="a" * 64,
        observation_sha256="b" * 64,
    )
    inst_fact = InstrumentalFact(
        fact_id="inst-1",
        observation_id="obs-1",
        fact_type=InstrumentalFactType.PROCESS_EXIT_CODE,
        fact_value="0",
        observability=FactObservability.CONCLUSIVE,
        provenance_detail="exit 0",
    )
    eval_fact = EvaluativeFact(
        fact_id="eval-1",
        evaluator_id="eval-01",
        fact_type=EvaluativeFactType.EXIT_CODE_EXPECTED,
        fact_value="0",
        satisfied=True,
        based_on_instrumental_fact_ids=("inst-1",),
        requirement_id="req-1",
        rationale="Exit matched",
    )
    dim_eval = DimensionEvaluation(
        dimension_id="dim-1",
        status=AssessmentStatus.NOT_APPLICABLE,
        is_critical=False,
        evaluation_rationale="N/A",
    )
    agg = AggregationResult(
        passed=True,
        overall_level=None,
        critical_dimension_failures=(),
        insufficient_dimensions=(),
    )
    asmt_core = AssessmentResult(
        assessment_id="asmt-e2e-01",
        task=task_ref,
        rubric=rubric_ref,
        observations=(obs_ref,),
        instrumental_facts=(inst_fact,),
        evaluative_facts=(eval_fact,),
        dimension_evaluations=(dim_eval,),
        aggregation=agg,
        evaluator_id="eval-01",
        evaluator_version="1.0",
        authority_id=EpistemologicalAuthority.ASSESSMENT_ENGINE.value,
        assessment_digest="",
        assessed_at=now,
    )
    digest = compute_canonical_sha256(asmt_core)
    return asmt_core.model_copy(update={"assessment_digest": digest})


# =============================================================================
# L4.1: IDENTITY CONFUSION MATRIX
# =============================================================================

def test_l4_1_student_identity_mismatch_in_session_provenance():
    """Attack: Student A attempts to ingest assessment bound to Student B via Spine."""
    now = datetime.now(timezone.utc)
    engine = EvidenceIngestionEngine()
    asmt = _build_valid_assessment(assessed_at=now)

    # Spine explicitly bound to student-beta
    spine = ExecutionProvenanceSpine(
        spine_id="spine-beta-01",
        identity=SpineIdentity(student_id="student-beta", session_id="sess-beta"),
        curriculum=SpineCurriculum(
            curriculum_node_id="c-pointers-101",
            roadmap_revision_id="2" * 64,
            policy_revision_id="3" * 64,
        ),
        assessment=SpineAssessment(
            task_id="task-c-pointer",
            task_revision_id="0" * 64,
            rubric_id="rubric-c-pointer",
            rubric_revision_id="1" * 64,
        ),
        execution=SpineExecution(
            observation_ids=("obs-1",),
            artifact_digests=(),
        ),
        terminal_state=SpineTerminalState(),
    )

    # Context maliciously claiming student-alpha
    ctx = SessionProvenanceContext(
        session_id="sess-alpha",
        student_id="student-alpha",  # MISMATCH with spine student-beta!
        session_started_at=now - timedelta(hours=1),
        session_is_active=True,
        resolved_target_node_id="c-pointers-101",
        expected_task_specification_sha256="0" * 64,
        expected_rubric_specification_sha256="1" * 64,
        roadmap_revision_id="2" * 64,
        policy_revision_id="3" * 64,
        spine=spine,
    )

    res = engine.evaluate_admissibility(asmt, ctx)
    assert res.decision == AdmissionDecision.REJECTED
    assert res.rejection_reason == RejectionReason.STUDENT_IDENTITY_MISMATCH


def test_l4_1_cross_student_evidence_contamination_in_state_derivation():
    """Verify strict student isolation: evidence from student B is 100% ignored for student A."""
    now = datetime.now(timezone.utc)
    student_a = "student-alpha"
    student_b = "student-beta"

    node = RoadmapNode(
        node_id="node-sys-01",
        title="System Call Basics",
        description="Syscall node",
        node_type=NodeType.TOPIC,
        notebook_id="nb-01",
    )
    nodes = {"node-sys-01": node}
    rev_id = compute_canonical_revision_id(
        roadmap_id="rm-iso-01",
        title="Roadmap Isolation",
        version="1.0",
        nodes=nodes,
        dependencies=(),
    )
    roadmap = CurricularRoadmap(
        roadmap_id="rm-iso-01",
        title="Roadmap Isolation",
        version="1.0",
        nodes=nodes,
        dependencies=(),
        canonical_revision_id=rev_id,
    )

    crit = NodeAssessmentCriteria(
        criteria_id="crit-sys",
        target_node_id="node-sys-01",
        requirements=(
            EvidenceRequirement(
                requirement_id="req-sys",
                evidence_type=EvidenceType.CODE_EXECUTION,
                min_count=1,
            ),
        ),
    )
    overrides = {"node-sys-01": crit}
    pol_id = compute_canonical_policy_id(
        policy_id="pol-iso-01",
        title="Policy Isolation",
        version="1.0",
        default_criteria={},
        node_overrides=overrides,
    )
    policy = AssessmentPolicy(
        policy_id="pol-iso-01",
        title="Policy Isolation",
        version="1.0",
        default_criteria={},
        node_overrides=overrides,
        canonical_policy_id=pol_id,
    )

    # In ledger: student B has qualifying PASS evidence, student A has ZERO evidence
    ev_b = EvidenceRecord(
        record_id="ev-b-01",
        student_id=student_b,  # Belonging to student B
        node_id="node-sys-01",
        evidence_type=EvidenceType.CODE_EXECUTION,
        outcome=EvidenceOutcome.PASS,
        score=1.0,
        timestamp=now,
        actor_type=ActorType.TOOL_VERIFIER,
        actor_id="gcc",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        roadmap_revision_id=roadmap.canonical_revision_id,
        policy_revision_id=policy.canonical_policy_id,
    )

    ledger = EvidenceLedger()
    ledger.append_record(ev_b, override_committed_at=now)

    # Derive state for student A
    state_a = derive_student_state(
        student_id=student_a,
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        as_of_time=now,
    )

    # Invariant: Student A MUST have 0 evidence and remain UNSATISFIED / NOT_STARTED!
    node_state_a = state_a.get_node_state("node-sys-01")
    assert node_state_a is not None
    assert node_state_a.total_evidence_count == 0
    assert node_state_a.evaluation_result is not None
    assert node_state_a.evaluation_result.verdict == CriteriaEvaluationVerdict.UNSATISFIED


# =============================================================================
# L4.2: TEMPORAL CONFUSION MATRIX
# =============================================================================

def test_l4_2_temporal_confusion_predating_session_start():
    """Attack: Assessment timestamp predating session start timestamp."""
    now = datetime.now(timezone.utc)
    engine = EvidenceIngestionEngine()

    # Assessed at 10:00, but session started at 11:00
    asmt = _build_valid_assessment(assessed_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc))

    ctx = SessionProvenanceContext(
        session_id="sess-01",
        student_id="student-alpha",
        session_started_at=datetime(2026, 1, 1, 11, 0, tzinfo=timezone.utc),  # Later!
        session_is_active=True,
        resolved_target_node_id="c-pointers-101",
        expected_task_specification_sha256="0" * 64,
        expected_rubric_specification_sha256="1" * 64,
        roadmap_revision_id="2" * 64,
        policy_revision_id="3" * 64,
    )

    res = engine.evaluate_admissibility(asmt, ctx)
    assert res.decision == AdmissionDecision.REJECTED
    assert res.rejection_reason == RejectionReason.SESSION_INACTIVE_OR_EXPIRED
    assert "predates session start" in (res.rejection_detail or "").lower()


def test_l4_2_temporal_confusion_postdating_session_expiration():
    """Attack: Assessment timestamp postdating session expiration timestamp."""
    now = datetime.now(timezone.utc)
    engine = EvidenceIngestionEngine()

    # Assessed at 13:00, but session expired at 12:00
    asmt = _build_valid_assessment(assessed_at=datetime(2026, 1, 1, 13, 0, tzinfo=timezone.utc))

    ctx = SessionProvenanceContext(
        session_id="sess-01",
        student_id="student-alpha",
        session_started_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        session_expires_at=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),  # Expired at 12:00!
        session_is_active=True,
        resolved_target_node_id="c-pointers-101",
        expected_task_specification_sha256="0" * 64,
        expected_rubric_specification_sha256="1" * 64,
        roadmap_revision_id="2" * 64,
        policy_revision_id="3" * 64,
    )

    res = engine.evaluate_admissibility(asmt, ctx)
    assert res.decision == AdmissionDecision.REJECTED
    assert res.rejection_reason == RejectionReason.SESSION_INACTIVE_OR_EXPIRED
    assert "postdates session expiration" in (res.rejection_detail or "").lower()


def test_l4_2_temporal_confusion_inactive_session():
    """Attack: Ingesting into a session marked session_is_active=False."""
    now = datetime.now(timezone.utc)
    engine = EvidenceIngestionEngine()
    asmt = _build_valid_assessment(assessed_at=now)

    ctx = SessionProvenanceContext(
        session_id="sess-01",
        student_id="student-alpha",
        session_started_at=now - timedelta(hours=1),
        session_is_active=False,  # INACTIVE!
        resolved_target_node_id="c-pointers-101",
        expected_task_specification_sha256="0" * 64,
        expected_rubric_specification_sha256="1" * 64,
        roadmap_revision_id="2" * 64,
        policy_revision_id="3" * 64,
    )

    res = engine.evaluate_admissibility(asmt, ctx)
    assert res.decision == AdmissionDecision.REJECTED
    assert res.rejection_reason == RejectionReason.SESSION_INACTIVE_OR_EXPIRED


# =============================================================================
# L4.3: HASH VS SEMANTIC / REVISION SUBSTITUTION MATRIX
# =============================================================================

def test_l4_4_hash_substitution_task_specification_mismatch():
    """Attack: Assessment references valid hash, but differs from context expected task spec."""
    now = datetime.now(timezone.utc)
    engine = EvidenceIngestionEngine()

    # Task SHA in assessment is "a"*64
    asmt = _build_valid_assessment(task_sha="a" * 64, rubric_sha="1" * 64, assessed_at=now)

    # Expected Task SHA in context is "0"*64
    ctx = SessionProvenanceContext(
        session_id="sess-01",
        student_id="student-alpha",
        session_started_at=now - timedelta(hours=1),
        session_is_active=True,
        resolved_target_node_id="c-pointers-101",
        expected_task_specification_sha256="0" * 64,  # MISMATCH!
        expected_rubric_specification_sha256="1" * 64,
        roadmap_revision_id="2" * 64,
        policy_revision_id="3" * 64,
    )

    res = engine.evaluate_admissibility(asmt, ctx)
    assert res.decision == AdmissionDecision.REJECTED
    assert res.rejection_reason == RejectionReason.SPECIFICATION_REVISION_MISMATCH


def test_l4_4_hash_substitution_rubric_specification_mismatch():
    """Attack: Assessment references valid hash, but differs from context expected rubric spec."""
    now = datetime.now(timezone.utc)
    engine = EvidenceIngestionEngine()

    # Rubric SHA in assessment is "b"*64
    asmt = _build_valid_assessment(task_sha="0" * 64, rubric_sha="b" * 64, assessed_at=now)

    # Expected Rubric SHA in context is "1"*64
    ctx = SessionProvenanceContext(
        session_id="sess-01",
        student_id="student-alpha",
        session_started_at=now - timedelta(hours=1),
        session_is_active=True,
        resolved_target_node_id="c-pointers-101",
        expected_task_specification_sha256="0" * 64,
        expected_rubric_specification_sha256="1" * 64,  # MISMATCH!
        roadmap_revision_id="2" * 64,
        policy_revision_id="3" * 64,
    )

    res = engine.evaluate_admissibility(asmt, ctx)
    assert res.decision == AdmissionDecision.REJECTED
    assert res.rejection_reason == RejectionReason.SPECIFICATION_REVISION_MISMATCH
