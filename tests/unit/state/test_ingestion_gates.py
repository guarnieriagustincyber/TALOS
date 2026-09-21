"""Unit tests for S5.2.A Evidence Ingestion Admissibility Gates.

Verifies the 4 sequential gates (Integrity, Provenance, Session, Anti-Replay)
and enforces fail-closed short-circuit behavior with SKIPPED downstream gates.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
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
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.contracts.evidence_ingestion import (
    AdmissionDecision,
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
from study_engine.state.ingestion_engine import EvidenceIngestionEngine
from study_engine.state.ledger import EvidenceLedger


def _make_spec_ref(
    spec_id: str = "spec-01",
    sha256: str = "a" * 64,
) -> SpecificationReference:
    return SpecificationReference(
        specification_id=spec_id,
        revision_id="rev-1",
        specification_sha256=sha256,
    )


def _make_obs_ref(
    obs_id: str = "obs-01",
    sha256: str = "b" * 64,
) -> ObservationReference:
    return ObservationReference(
        observation_id=obs_id,
        execution_id="exec-01",
        effective_script_sha256="d" * 64,
        observation_sha256=sha256,
    )


def _make_instrumental_fact() -> InstrumentalFact:
    return InstrumentalFact(
        fact_id="fact-inst-01",
        observation_id="obs-01",
        fact_type=InstrumentalFactType.PROCESS_EXIT_CODE,
        fact_value="0",
        observability=FactObservability.CONCLUSIVE,
        inspected_domain="scratch/workspace/",
        provenance_detail="Process exit observation",
    )


def _make_evaluative_fact() -> EvaluativeFact:
    return EvaluativeFact(
        fact_id="fact-eval-01",
        evaluator_id="eval-01",
        fact_type=EvaluativeFactType.EXIT_CODE_EXPECTED,
        fact_value="0",
        satisfied=True,
        based_on_instrumental_fact_ids=("fact-inst-01",),
        requirement_id="req-clean-exit",
        rationale="Process exited cleanly with code 0",
    )


def _make_dimension_eval(
    passed: bool = True,
    status: AssessmentStatus = AssessmentStatus.ASSESSED,
    assigned_level: Optional[PerformanceLevel] = PerformanceLevel.N3_COMPETENT,
) -> DimensionEvaluation:
    return DimensionEvaluation(
        dimension_id="dim-clean-exit",
        status=status,
        assigned_level=assigned_level,
        passed_minimum=passed,
        is_critical=True,
        evidence_evaluative_fact_ids=("fact-eval-01",),
        evaluator_rule_ids=("rule-clean-exit-n3",),
        evaluation_rationale="Evaluated cleanly",
    )


def _make_assessment_result(
    assessment_id: str = "asmt-001",
    task_sha256: str = "a" * 64,
    rubric_sha256: str = "c" * 64,
    authority_id: str = EpistemologicalAuthority.ASSESSMENT_ENGINE.value,
    include_observations: bool = True,
    assessed_at: Optional[datetime] = None,
    passed: bool = True,
    overall_level: Optional[PerformanceLevel] = PerformanceLevel.N3_COMPETENT,
    insufficient_dimensions: tuple[str, ...] = (),
) -> AssessmentResult:
    timestamp = assessed_at or datetime.now(timezone.utc)
    obs = (_make_obs_ref(),) if include_observations else ()

    interim = AssessmentResult(
        assessment_id=assessment_id,
        authority_id=authority_id,
        task=_make_spec_ref("task-01", task_sha256),
        rubric=_make_spec_ref("rubric-01", rubric_sha256),
        observations=obs,
        instrumental_facts=(_make_instrumental_fact(),),
        evaluative_facts=(_make_evaluative_fact(),),
        dimension_evaluations=(_make_dimension_eval(passed=passed),),
        aggregation=AggregationResult(
            overall_level=overall_level,
            passed=passed,
            insufficient_dimensions=insufficient_dimensions,
        ),
        evaluator_id="S9_DETERMINISTIC_EVALUATOR",
        evaluator_version="1.0.0",
        assessed_at=timestamp,
    )
    digest = compute_canonical_sha256(interim)
    return interim.model_copy(update={"assessment_digest": digest})


def _make_spine(
    student_id: str = "student-1",
    node_id: str = "node-proc",
) -> ExecutionProvenanceSpine:
    valid_sha = "f" * 64
    return ExecutionProvenanceSpine(
        spine_id="spine-001",
        identity=SpineIdentity(
            student_id=student_id,
            session_id="session-1",
            attempt_id="attempt-1",
        ),
        curriculum=SpineCurriculum(
            curriculum_node_id=node_id,
            roadmap_revision_id=valid_sha,
            policy_revision_id=valid_sha,
            gateway_id="G1.1",
            gateway_revision_id=valid_sha,
        ),
        assessment=SpineAssessment(
            rubric_id="rubric-01",
            rubric_revision_id=valid_sha,
            task_id="task-01",
            task_revision_id=valid_sha,
            hoare_contract_id="hoare-01",
            assessment_result_id="asmt-001",
            evidence_record_id="ev-001",
            evaluator_version="1.0.0",
        ),
        execution=SpineExecution(
            observation_ids=("obs-01",),
            artifact_digests=(valid_sha,),
            perturbation_id="pert-01",
        ),
        terminal_state=SpineTerminalState(
            ledger_cutoff_hash=valid_sha,
            student_state_id="state-01",
        ),
    )


def _make_context(
    student_id: str = "student-1",
    node_id: str = "node-proc",
    task_sha256: Optional[str] = "a" * 64,
    rubric_sha256: Optional[str] = "c" * 64,
    session_is_active: bool = True,
    session_started_at: Optional[datetime] = None,
    session_expires_at: Optional[datetime] = None,
    with_spine: bool = True,
) -> SessionProvenanceContext:
    now = datetime.now(timezone.utc)
    started_at = session_started_at or (now - timedelta(hours=1))
    spine = _make_spine(student_id, node_id) if with_spine else None

    return SessionProvenanceContext(
        student_id=student_id,
        session_id="session-1",
        resolved_target_node_id=node_id,
        roadmap_revision_id="e" * 64,
        policy_revision_id="f" * 64,
        expected_task_specification_sha256=task_sha256,
        expected_rubric_specification_sha256=rubric_sha256,
        session_is_active=session_is_active,
        session_started_at=started_at,
        session_expires_at=session_expires_at,
        spine=spine,
    )


class TestAdmissibilityGate1Integrity:
    """Tests for Gate 1: Integrity Gate."""

    def test_gate1_valid_integrity_passes(self) -> None:
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        context = _make_context()

        admission = engine.evaluate_admissibility(assessment, context)
        assert admission.admission_trace.integrity == GateVerdict.PASS

    def test_gate1_digest_tampering_fails_and_short_circuits(self) -> None:
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        tampered = assessment.model_copy(
            update={"assessment_digest": "0" * 64}
        )
        context = _make_context()

        admission = engine.evaluate_admissibility(tampered, context)
        assert admission.decision == AdmissionDecision.REJECTED
        assert (
            admission.rejection_reason
            == RejectionReason.CORRUPTED_ASSESSMENT_DIGEST
        )
        assert admission.admission_trace.integrity == GateVerdict.FAIL
        assert admission.admission_trace.provenance == GateVerdict.SKIPPED
        assert admission.admission_trace.session == GateVerdict.SKIPPED
        assert admission.admission_trace.anti_replay == GateVerdict.SKIPPED

    def test_gate1_unauthorized_authority_fails(self) -> None:
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result(
            authority_id="UNAUTHORIZED_THIRD_PARTY"
        )
        context = _make_context()

        admission = engine.evaluate_admissibility(assessment, context)
        assert admission.decision == AdmissionDecision.REJECTED
        assert (
            admission.rejection_reason
            == RejectionReason.UNAUTHORIZED_ASSESSMENT_AUTHORITY
        )
        assert admission.admission_trace.integrity == GateVerdict.FAIL
        assert admission.admission_trace.provenance == GateVerdict.SKIPPED

    def test_gate1_task_specification_mismatch_fails(self) -> None:
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result(task_sha256="1" * 64)
        context = _make_context(task_sha256="2" * 64)

        admission = engine.evaluate_admissibility(assessment, context)
        assert admission.decision == AdmissionDecision.REJECTED
        assert (
            admission.rejection_reason
            == RejectionReason.SPECIFICATION_REVISION_MISMATCH
        )
        assert admission.admission_trace.integrity == GateVerdict.FAIL

    def test_gate1_rubric_specification_mismatch_fails(self) -> None:
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result(rubric_sha256="1" * 64)
        context = _make_context(rubric_sha256="2" * 64)

        admission = engine.evaluate_admissibility(assessment, context)
        assert admission.decision == AdmissionDecision.REJECTED
        assert (
            admission.rejection_reason
            == RejectionReason.SPECIFICATION_REVISION_MISMATCH
        )
        assert admission.admission_trace.integrity == GateVerdict.FAIL


class TestAdmissibilityGate2Provenance:
    """Tests for Gate 2: Provenance Gate."""

    def test_gate2_valid_provenance_passes(self) -> None:
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        context = _make_context()

        admission = engine.evaluate_admissibility(assessment, context)
        assert admission.admission_trace.provenance == GateVerdict.PASS

    def test_gate2_missing_observations_fails_and_short_circuits(
        self,
    ) -> None:
        engine = EvidenceIngestionEngine()
        # AssessmentResult validates observations min_length=1 on construction,
        # so bypass via model_construct to test engine defensive check
        valid = _make_assessment_result()
        bypassed = AssessmentResult.model_construct(
            assessment_id=valid.assessment_id,
            authority_id=valid.authority_id,
            task=valid.task,
            rubric=valid.rubric,
            observations=(),
            instrumental_facts=valid.instrumental_facts,
            evaluative_facts=valid.evaluative_facts,
            dimension_evaluations=valid.dimension_evaluations,
            aggregation=valid.aggregation,
            evaluator_id=valid.evaluator_id,
            evaluator_version=valid.evaluator_version,
            assessed_at=valid.assessed_at,
            assessment_digest="",
        )
        digest = compute_canonical_sha256(bypassed)
        bypassed_with_digest = bypassed.model_copy(
            update={"assessment_digest": digest}
        )
        context = _make_context()

        admission = engine.evaluate_admissibility(
            bypassed_with_digest, context
        )
        assert admission.decision == AdmissionDecision.REJECTED
        assert (
            admission.rejection_reason
            == RejectionReason.BROKEN_PROVENANCE_CHAIN
        )
        assert admission.admission_trace.integrity == GateVerdict.PASS
        assert admission.admission_trace.provenance == GateVerdict.FAIL
        assert admission.admission_trace.session == GateVerdict.SKIPPED
        assert admission.admission_trace.anti_replay == GateVerdict.SKIPPED

    def test_gate2_spine_curriculum_node_mismatch_fails(self) -> None:
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        mismatched_spine = _make_spine(
            student_id="student-1",
            node_id="node-other",
        )
        context = _make_context(node_id="node-proc", with_spine=False)
        context = context.model_copy(update={"spine": mismatched_spine})

        admission = engine.evaluate_admissibility(assessment, context)
        assert admission.decision == AdmissionDecision.REJECTED
        assert (
            admission.rejection_reason
            == RejectionReason.BROKEN_PROVENANCE_CHAIN
        )
        assert admission.admission_trace.provenance == GateVerdict.FAIL


class TestAdmissibilityGate3Session:
    """Tests for Gate 3: Session & Context Gate."""

    def test_gate3_valid_session_passes(self) -> None:
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        context = _make_context()

        admission = engine.evaluate_admissibility(assessment, context)
        assert admission.admission_trace.session == GateVerdict.PASS

    def test_gate3_spine_student_mismatch_fails(self) -> None:
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        mismatched_spine = _make_spine(
            student_id="student-attacker",
            node_id="node-proc",
        )
        context = _make_context(student_id="student-1", with_spine=False)
        context = context.model_copy(update={"spine": mismatched_spine})

        admission = engine.evaluate_admissibility(assessment, context)
        assert admission.decision == AdmissionDecision.REJECTED
        assert (
            admission.rejection_reason
            == RejectionReason.STUDENT_IDENTITY_MISMATCH
        )
        assert admission.admission_trace.integrity == GateVerdict.PASS
        assert admission.admission_trace.provenance == GateVerdict.PASS
        assert admission.admission_trace.session == GateVerdict.FAIL
        assert admission.admission_trace.anti_replay == GateVerdict.SKIPPED

    def test_gate3_session_inactive_fails(self) -> None:
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        context = _make_context(session_is_active=False)

        admission = engine.evaluate_admissibility(assessment, context)
        assert admission.decision == AdmissionDecision.REJECTED
        assert (
            admission.rejection_reason
            == RejectionReason.SESSION_INACTIVE_OR_EXPIRED
        )
        assert admission.admission_trace.session == GateVerdict.FAIL

    def test_gate3_timestamp_predating_session_start_fails(self) -> None:
        engine = EvidenceIngestionEngine()
        now = datetime.now(timezone.utc)
        assessment = _make_assessment_result(
            assessed_at=now - timedelta(hours=2)
        )
        context = _make_context(session_started_at=now - timedelta(hours=1))

        admission = engine.evaluate_admissibility(assessment, context)
        assert admission.decision == AdmissionDecision.REJECTED
        assert (
            admission.rejection_reason
            == RejectionReason.SESSION_INACTIVE_OR_EXPIRED
        )
        assert admission.admission_trace.session == GateVerdict.FAIL

    def test_gate3_timestamp_postdating_session_expiration_fails(
        self,
    ) -> None:
        engine = EvidenceIngestionEngine()
        now = datetime.now(timezone.utc)
        assessment = _make_assessment_result(assessed_at=now)
        context = _make_context(
            session_started_at=now - timedelta(hours=2),
            session_expires_at=now - timedelta(minutes=30),
        )

        admission = engine.evaluate_admissibility(assessment, context)
        assert admission.decision == AdmissionDecision.REJECTED
        assert (
            admission.rejection_reason
            == RejectionReason.SESSION_INACTIVE_OR_EXPIRED
        )
        assert admission.admission_trace.session == GateVerdict.FAIL


class TestAdmissibilityGate4AntiReplay:
    """Tests for Gate 4: Anti-Replay Preflight Gate."""

    def test_gate4_preflight_clean_ledger_passes(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "l.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        context = _make_context()

        admission = engine.evaluate_admissibility(
            assessment, context, ledger=ledger
        )
        assert admission.admission_trace.anti_replay == GateVerdict.PASS
        assert admission.decision == AdmissionDecision.ADMITTED

    def test_gate4_preflight_duplicate_detected_and_rejected(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "l.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        context = _make_context()

        res1 = engine.ingest_assessment(assessment, context, ledger)
        assert res1.admission.decision == AdmissionDecision.ADMITTED
        assert ledger.has_assessment_digest(assessment.assessment_digest)

        admission2 = engine.evaluate_admissibility(
            assessment, context, ledger=ledger
        )
        assert admission2.decision == AdmissionDecision.REJECTED
        assert (
            admission2.rejection_reason
            == RejectionReason.DUPLICATE_ASSESSMENT_REPLAY
        )
        assert admission2.admission_trace.integrity == GateVerdict.PASS
        assert admission2.admission_trace.provenance == GateVerdict.PASS
        assert admission2.admission_trace.session == GateVerdict.PASS
        assert admission2.admission_trace.anti_replay == GateVerdict.FAIL
