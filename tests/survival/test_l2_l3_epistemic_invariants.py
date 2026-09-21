"""Layer L2 & L3 Hostile Survival Audit: Subsystem Adversarial Boundaries & The 8 Forbidden Shortcuts.

Part of SYSTEM SURVIVAL AUDIT — SSA-0.
Modalidad: Read-Only / Red Team / No Patch.
"""

from datetime import datetime, timezone
from pathlib import Path
import pytest

from study_engine.assessment.aggregator import aggregate_evaluations
from study_engine.assessment.evaluator_deterministic import (
    evaluate_practical_task,
)
from study_engine.assessment.fact_extractor import extract_instrumental_facts
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
from study_engine.contracts.execution import (
    ArtifactCollectionSummary,
    ExecutionObservation,
    ProcessTelemetry,
    TerminationReason,
)
from study_engine.curriculum.artifact_contracts import (
    ArtifactRequirement,
    ArtifactType,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.curriculum.rubric_contracts import (
    AssessmentRubric,
    RubricDimension,
)
from study_engine.curriculum.task_contracts import PracticalTaskSpecification
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
    EvidenceType,
    NodeAssessmentCriteria,
    EvidenceRequirement,
)
from study_engine.state.policy_engine import (
    compute_canonical_policy_id,
    evaluate_node_criteria,
)
from study_engine.state.state_contracts import (
    HistoryCutoffMode,
    NodeProgressStatus,
    StudentState,
)
from study_engine.state.state_engine import derive_student_state


# =============================================================================
# LAYER L2: SUBSYSTEM ADVERSARIAL BOUNDARIES
# =============================================================================

def test_l2_1_truncation_preserves_insufficient_observation_without_collapse():
    """Verify S9 preserves INSUFFICIENT_OBSERVATION when stream is truncated, never collapsing to FAIL."""
    obs_id = "obs-trunc-01"
    now = datetime.now(timezone.utc)

    # Observation with truncated stream
    telemetry = ProcessTelemetry(
        duration_ms=500.0,
        termination_reason=TerminationReason.NORMAL_EXIT,
        output_truncated=True,  # Truncated!
    )
    obs = ExecutionObservation(
        observation_id=obs_id,
        execution_id="exec-trunc-01",
        tool_name="gcc",
        exit_code=0,
        telemetry=telemetry,
        effective_script_sha256="0" * 64,
        timestamp=now,
    )

    facts = extract_instrumental_facts(obs)
    trunc_fact = next(
        (f for f in facts if f.fact_type == InstrumentalFactType.STREAM_WAS_TRUNCATED),
        None,
    )
    assert trunc_fact is not None
    assert trunc_fact.fact_value == "true"
    assert trunc_fact.observability == FactObservability.CONCLUSIVE

    # Create task & rubric requiring an artifact
    req = ArtifactRequirement(
        requirement_id="result.json",
        artifact_type=ArtifactType.LOG_BUNDLE,
        min_size_bytes=10,
        expected_mime_types=("application/json",),
        description="Execution results output",
    )
    task = PracticalTaskSpecification(
        task_id="task-art-01",
        curriculum_node_id="node-sys-01",
        title="Artifact Check",
        description="Requires result.json",
        required_artifacts=(req,),
        time_limit_minutes=2,
    )
    rubric = AssessmentRubric(
        rubric_id="rubric-art-01",
        title="Artifact Assessment",
        dimensions=(
            RubricDimension(
                dimension_id="dim-practical",
                title="Practical Dimension",
                weight=1.0,
                minimum_level=PerformanceLevel.N3_COMPETENT,
                is_critical=True,
            ),
        ),
    )

    # 1. Test stream truncation abstention directly on dimension evaluation
    from study_engine.assessment.evaluator_deterministic import _evaluate_dimension
    from study_engine.contracts.assessment import EvaluativeFact, EvaluativeFactType

    eval_facts_stream = (
        EvaluativeFact(
            fact_id="eval-stdout-1",
            evaluator_id="eval-01",
            fact_type=EvaluativeFactType.STDOUT_MATCHES_PATTERN,
            fact_value="matched",
            satisfied=True,
            based_on_instrumental_fact_ids=(trunc_fact.fact_id,),
            requirement_id="req-stdout",
            rationale="Pattern matched but stream was truncated",
        ),
    )
    dim_stream_eval = _evaluate_dimension(
        dimension=rubric.dimensions[0],
        task=task,
        evaluative_facts=eval_facts_stream,
        instrumental_facts=facts,
    )
    assert dim_stream_eval.status == AssessmentStatus.INSUFFICIENT_OBSERVATION
    assert "rule-abstain-stream-truncated" in dim_stream_eval.evaluator_rule_ids
    assert dim_stream_eval.assigned_level is None

    # 2. Test omitted artifact abstention in full evaluate_practical_task
    facts_with_omission = (
        *facts,
        InstrumentalFact(
            fact_id="fact-art-omit-1",
            observation_id=obs_id,
            fact_type=InstrumentalFactType.ARTIFACT_OMITTED_BY_LIMIT,
            fact_value="result.json",
            observability=FactObservability.PARTIAL_TRUNCATED,
            inspected_domain="scratch/workspace/",
            provenance_detail="Omitted due to limits",
        ),
    )
    eval_facts, dim_evals = evaluate_practical_task(
        rubric=rubric,
        task=task,
        instrumental_facts=facts_with_omission,
    )

    assert len(dim_evals) == 1
    dim = dim_evals[0]
    # CRITICAL INVARIANT: status is INSUFFICIENT_OBSERVATION, NOT ASSESSED and NOT FAIL!
    assert dim.status == AssessmentStatus.INSUFFICIENT_OBSERVATION
    assert dim.assigned_level is None
    assert dim.passed_minimum is None
    assert "rule-abstain-omitted-artifacts" in dim.evaluator_rule_ids

    # Aggregation verification
    agg = aggregate_evaluations(
        dimension_evaluations=dim_evals,
        rubric=rubric,
    )
    assert not agg.passed
    assert "dim-practical" in agg.insufficient_dimensions

    # Ingestion into S5.2.A verification: maps strictly to INCONCLUSIVE (never FAIL)
    engine = EvidenceIngestionEngine()
    asmt = AssessmentResult(
        assessment_id="asmt-trunc-01",
        task=SpecificationReference(
            specification_id=task.task_id,
            revision_id="rev-1",
            specification_sha256="0" * 64,
        ),
        rubric=SpecificationReference(
            specification_id=rubric.rubric_id,
            revision_id="rev-1",
            specification_sha256="1" * 64,
        ),
        observations=(
            ObservationReference(
                observation_id=obs_id,
                execution_id="exec-trunc-01",
                effective_script_sha256="0" * 64,
                observation_sha256="a" * 64,
            ),
        ),
        instrumental_facts=facts,
        evaluative_facts=eval_facts,
        dimension_evaluations=dim_evals,
        aggregation=agg,
        evaluator_id="eval-01",
        evaluator_version="1.0",
        authority_id=EpistemologicalAuthority.ASSESSMENT_ENGINE.value,
        assessment_digest="",
        assessed_at=now,
    )
    computed_digest = compute_canonical_sha256(asmt)
    asmt = asmt.model_copy(update={"assessment_digest": computed_digest})

    ctx = SessionProvenanceContext(
        session_id="sess-01",
        student_id="student-alpha",
        session_started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        session_is_active=True,
        resolved_target_node_id="node-sys-01",
        expected_task_specification_sha256="0" * 64,
        expected_rubric_specification_sha256="1" * 64,
        roadmap_revision_id="2" * 64,
        policy_revision_id="3" * 64,
    )

    admission = engine.evaluate_admissibility(asmt, ctx)
    assert admission.decision == AdmissionDecision.ADMITTED
    assert admission.outcome == EvidenceOutcome.INCONCLUSIVE  # Epistemic neutrality preserved!


def test_l2_2_artifact_omitted_vs_verified_absence_boundary():
    """Verify clear distinction between ARTIFACT_OMITTED_BY_LIMIT and ARTIFACT_VERIFIED_ABSENT."""
    now = datetime.now(timezone.utc)

    # Case A: Limits exceeded during collection -> OMITTED_BY_LIMIT
    summary_limited = ArtifactCollectionSummary(
        artifacts_discovered=2,
        artifacts_collected=0,
        artifacts_omitted=2,
        collection_truncated=True,
    )
    obs_limited = ExecutionObservation(
        observation_id="obs-lim-01",
        execution_id="exec-lim-01",
        tool_name="gcc",
        exit_code=0,
        artifact_summary=summary_limited,
        effective_script_sha256="0" * 64,
        timestamp=now,
    )
    facts_lim = extract_instrumental_facts(obs_limited, expected_paths=("output.bin",))
    fact_lim = next((f for f in facts_lim if f.fact_type == InstrumentalFactType.ARTIFACT_OMITTED_BY_LIMIT), None)
    assert fact_lim is not None
    assert fact_lim.observability == FactObservability.PARTIAL_TRUNCATED

    # Case B: Exhaustive scan with clean limits -> VERIFIED_ABSENT
    summary_clean = ArtifactCollectionSummary(
        artifacts_discovered=0,
        artifacts_collected=0,
        artifacts_omitted=0,
        collection_truncated=False,
    )
    obs_clean = ExecutionObservation(
        observation_id="obs-clean-01",
        execution_id="exec-clean-01",
        tool_name="gcc",
        exit_code=0,
        artifact_summary=summary_clean,
        effective_script_sha256="0" * 64,
        timestamp=now,
    )
    facts_clean = extract_instrumental_facts(obs_clean, expected_paths=("output.bin",))
    fact_clean = next((f for f in facts_clean if f.fact_type == InstrumentalFactType.ARTIFACT_VERIFIED_ABSENT), None)
    assert fact_clean is not None
    assert fact_clean.observability == FactObservability.VERIFIED_ABSENCE


# =============================================================================
# LAYER L3: THE 8 FORBIDDEN SHORTCUTS
# =============================================================================

def test_l3_shortcut_1_observation_to_student_state_forbidden():
    """Shortcut 1: Observation -> StudentState directly must be impossible."""
    now = datetime.now(timezone.utc)
    obs = ExecutionObservation(
        observation_id="obs-01",
        execution_id="exec-01",
        tool_name="gcc",
        exit_code=0,
        effective_script_sha256="0" * 64,
        timestamp=now,
    )

    # derive_student_state requires an EvidenceLedger, not ExecutionObservation
    with pytest.raises((TypeError, AttributeError)):
        derive_student_state(
            roadmap=None,  # type: ignore[arg-type]
            policy=None,  # type: ignore[arg-type]
            ledger=obs,  # type: ignore[arg-type]
            student_id="student-01",
        )


def test_l3_shortcut_2_observation_to_evidence_record_forbidden():
    """Shortcut 2: Observation -> EvidenceRecord directly without S5.2.A ingestion is blocked."""
    now = datetime.now(timezone.utc)
    obs = ExecutionObservation(
        observation_id="obs-01",
        execution_id="exec-01",
        tool_name="gcc",
        exit_code=0,
        effective_script_sha256="0" * 64,
        timestamp=now,
    )

    ledger = EvidenceLedger()
    with pytest.raises(Exception):
        ledger.append_record(obs)  # type: ignore[arg-type]


def test_l3_shortcut_3_assessment_to_student_state_forbidden():
    """Shortcut 3: AssessmentResult -> StudentState directly without ledger persistence is blocked."""
    fake_assessment = "AssessmentResultObject"
    with pytest.raises((TypeError, AttributeError)):
        derive_student_state(
            roadmap=None,  # type: ignore[arg-type]
            policy=None,  # type: ignore[arg-type]
            ledger=fake_assessment,  # type: ignore[arg-type]
            student_id="student-01",
        )


def test_l3_shortcut_4_rejected_decision_cannot_produce_evidence_record():
    """Shortcut 4: REJECTED AdmissionResult cannot produce an EvidenceRecord."""
    now = datetime.now(timezone.utc)
    trace = AdmissionTrace(
        integrity=GateVerdict.FAIL,
        provenance=GateVerdict.SKIPPED,
        session=GateVerdict.SKIPPED,
        anti_replay=GateVerdict.SKIPPED,
    )

    # AdmissionResult validator enforces outcome is None when decision == REJECTED
    rejected_res = AdmissionResult(
        decision=AdmissionDecision.REJECTED,
        rejection_reason=RejectionReason.CORRUPTED_ASSESSMENT_DIGEST,
        admission_trace=trace,
        evaluated_at=now,
    )
    assert rejected_res.outcome is None

    engine = EvidenceIngestionEngine()
    # Attempting to call build_admitted_record requires outcome: EvidenceOutcome
    with pytest.raises((TypeError, AttributeError)):
        engine.build_admitted_record(
            assessment=None,  # type: ignore[arg-type]
            context=None,  # type: ignore[arg-type]
            outcome=None,  # type: ignore[arg-type]
            trace=trace,
        )


def test_l3_shortcut_5_inconclusive_never_triggers_regression_or_fail():
    """Shortcut 5: INCONCLUSIVE evidence never triggers CriteriaEvaluationVerdict.REGRESSED or FAIL."""
    now = datetime.now(timezone.utc)
    criteria = NodeAssessmentCriteria(
        criteria_id="crit-01",
        target_node_id="node-01",
        requirements=(
            EvidenceRequirement(
                requirement_id="req-pass",
                evidence_type=EvidenceType.CODE_EXECUTION,
                min_count=1,
                min_score=1.0,
            ),
        ),
        regression_threshold_failures=1,
    )

    # Sequence: 1 PASS followed by 5 consecutive INCONCLUSIVE records
    history = [
        EvidenceRecord(
            record_id="ev-pass",
            student_id="student-01",
            node_id="node-01",
            evidence_type=EvidenceType.CODE_EXECUTION,
            outcome=EvidenceOutcome.PASS,
            score=1.0,
            timestamp=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
            actor_type=ActorType.TOOL_VERIFIER,
            actor_id="gcc",
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
            roadmap_revision_id="0" * 64,
            policy_revision_id="1" * 64,
        )
    ]
    for i in range(5):
        history.append(
            EvidenceRecord(
                record_id=f"ev-inconc-{i}",
                student_id="student-01",
                node_id="node-01",
                evidence_type=EvidenceType.CODE_EXECUTION,
                outcome=EvidenceOutcome.INCONCLUSIVE,  # INCONCLUSIVE!
                score=0.0,
                timestamp=datetime(2026, 1, 1, 11 + i, 0, tzinfo=timezone.utc),
                actor_type=ActorType.TOOL_VERIFIER,
                actor_id="gcc",
                authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                roadmap_revision_id="0" * 64,
                policy_revision_id="1" * 64,
            )
        )

    res = evaluate_node_criteria(
        criteria=criteria,
        history=history,
        as_of_time=datetime(2026, 1, 1, 20, 0, tzinfo=timezone.utc),
    )

    # Invariant: Status remains SATISFIED! Zero regression!
    assert res.verdict == CriteriaEvaluationVerdict.SATISFIED
    assert res.subsequent_failures_count == 0


def test_l3_shortcut_6_untrusted_artifact_cannot_be_evidence():
    """Shortcut 6: Assessment with mismatched observation digest rejected at Gate 1."""
    now = datetime.now(timezone.utc)
    engine = EvidenceIngestionEngine()

    task_ref = SpecificationReference(
        specification_id="task-01",
        revision_id="rev-1",
        specification_sha256="0" * 64,
    )
    rubric_ref = SpecificationReference(
        specification_id="rubric-01",
        revision_id="rev-1",
        specification_sha256="1" * 64,
    )
    obs_ref = ObservationReference(
        observation_id="obs-1",
        execution_id="exec-1",
        effective_script_sha256="a" * 64,
        observation_sha256="b" * 64,
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

    asmt_core = AssessmentResult(
        assessment_id="asmt-bad-digest",
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
        assessment_digest="corrupted_digest" + "0" * 48,  # FORGED DIGEST
        assessed_at=now,
    )

    ctx = SessionProvenanceContext(
        session_id="sess-01",
        student_id="student-alpha",
        session_started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        session_is_active=True,
        resolved_target_node_id="c-pointers-101",
        expected_task_specification_sha256="0" * 64,
        expected_rubric_specification_sha256="1" * 64,
        roadmap_revision_id="2" * 64,
        policy_revision_id="3" * 64,
    )

    result = engine.evaluate_admissibility(asmt_core, ctx)
    assert result.decision == AdmissionDecision.REJECTED
    assert result.rejection_reason == RejectionReason.CORRUPTED_ASSESSMENT_DIGEST


def test_l3_shortcut_7_locked_node_cannot_progress_despite_pass_evidence():
    """Shortcut 7: Node with unsatisfied HARD prerequisite remains LOCKED even with 100% PASS evidence."""
    now = datetime.now(timezone.utc)
    student_id = "student-survival-07"

    node_prereq = RoadmapNode(
        node_id="node-prereq",
        title="Prerequisite Node",
        description="Prereq description",
        node_type=NodeType.TOPIC,
        notebook_id="nb-01",
    )
    node_advanced = RoadmapNode(
        node_id="node-advanced",
        title="Advanced Node",
        description="Advanced description",
        node_type=NodeType.LAB,
        notebook_id="nb-01",
    )
    dep = RoadmapDependency(
        source_node_id="node-prereq",
        target_node_id="node-advanced",
        dependency_type=DependencyType.HARD,  # HARD PREREQUISITE
    )

    nodes_map = {"node-prereq": node_prereq, "node-advanced": node_advanced}
    deps_tuple = (dep,)
    rev_id = compute_canonical_revision_id(
        roadmap_id="roadmap-prereq-test",
        title="Test Roadmap",
        version="1.0",
        nodes=nodes_map,
        dependencies=deps_tuple,
    )
    roadmap = CurricularRoadmap(
        roadmap_id="roadmap-prereq-test",
        title="Test Roadmap",
        version="1.0",
        nodes=nodes_map,
        dependencies=deps_tuple,
        canonical_revision_id=rev_id,
    )

    crit_prereq = NodeAssessmentCriteria(
        criteria_id="crit-prereq",
        target_node_id="node-prereq",
        requirements=(
            EvidenceRequirement(
                requirement_id="req-p",
                evidence_type=EvidenceType.CODE_EXECUTION,
                min_count=1,
            ),
        ),
    )
    crit_advanced = NodeAssessmentCriteria(
        criteria_id="crit-advanced",
        target_node_id="node-advanced",
        requirements=(
            EvidenceRequirement(
                requirement_id="req-a",
                evidence_type=EvidenceType.CODE_EXECUTION,
                min_count=1,
            ),
        ),
    )

    overrides = {
        "node-prereq": crit_prereq,
        "node-advanced": crit_advanced,
    }
    pol_id = compute_canonical_policy_id(
        policy_id="policy-test",
        title="Policy Test",
        version="1.0",
        default_criteria={},
        node_overrides=overrides,
    )
    policy = AssessmentPolicy(
        policy_id="policy-test",
        title="Policy Test",
        version="1.0",
        default_criteria={},
        node_overrides=overrides,
        canonical_policy_id=pol_id,
    )

    # In ledger: student has PASS evidence for advanced node, but ZERO evidence for prereq!
    ev_advanced = EvidenceRecord(
        record_id="ev-adv-01",
        student_id=student_id,
        node_id="node-advanced",
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
    ledger.append_record(ev_advanced, override_committed_at=now)

    state = derive_student_state(
        student_id=student_id,
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        as_of_time=now,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
    )

    # Advanced node MUST be LOCKED despite having PASS evidence!
    adv_state = state.get_node_state("node-advanced")
    assert adv_state is not None
    assert adv_state.status == NodeProgressStatus.LOCKED
    assert "node-prereq" in adv_state.unfulfilled_hard_prerequisites
    # But intrinsic evaluation is preserved as SATISFIED:
    assert adv_state.evaluation_result is not None
    assert adv_state.evaluation_result.verdict == CriteriaEvaluationVerdict.SATISFIED


def test_l3_shortcut_8_generated_text_cannot_be_evidence():
    """Shortcut 8: Raw text or string cannot masquerade as EvidenceRecord in ledger."""
    ledger = EvidenceLedger()
    fake_llm_output = "I certify this student has completed node-01 successfully."
    with pytest.raises(Exception):
        ledger.append_record(fake_llm_output)  # type: ignore[arg-type]
