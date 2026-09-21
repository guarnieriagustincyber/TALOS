"""Unit tests for EvidenceIngestionEngine in Subsystem S5.2.A.

Verifies end-to-end ingestion pipeline, outcome mapping (PASS, FAIL,
INCONCLUSIVE), sovereign authority stamping, and atomic concurrent race
resolution into safe REJECTED admission results.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock
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
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.state.ingestion_engine import EvidenceIngestionEngine
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import DuplicateEvidenceError
from study_engine.state.policy_contracts import (
    ActorType,
    EvidenceOutcome,
    EvidenceType,
)


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
    passed: Optional[bool] = True,
    status: AssessmentStatus = AssessmentStatus.ASSESSED,
    assigned_level: Optional[PerformanceLevel] = PerformanceLevel.N3_COMPETENT,
) -> DimensionEvaluation:
    passed_minimum = passed if status == AssessmentStatus.ASSESSED else None
    return DimensionEvaluation(
        dimension_id="dim-clean-exit",
        status=status,
        assigned_level=assigned_level,
        passed_minimum=passed_minimum,
        is_critical=True,
        evidence_evaluative_fact_ids=("fact-eval-01",),
        evaluator_rule_ids=("rule-clean-exit-n3",),
        evaluation_rationale="Evaluated cleanly",
    )


def _make_assessment_result(
    assessment_id: str = "asmt-001",
    task_sha256: str = "a" * 64,
    rubric_sha256: str = "c" * 64,
    passed: bool = True,
    overall_level: Optional[PerformanceLevel] = PerformanceLevel.N3_COMPETENT,
    insufficient_dimensions: tuple[str, ...] = (),
    assessed_at: Optional[datetime] = None,
) -> AssessmentResult:
    timestamp = assessed_at or datetime.now(timezone.utc)
    status = (
        AssessmentStatus.INSUFFICIENT_OBSERVATION
        if len(insufficient_dimensions) > 0
        else AssessmentStatus.ASSESSED
    )
    dim_level = None if len(insufficient_dimensions) > 0 else overall_level

    interim = AssessmentResult(
        assessment_id=assessment_id,
        authority_id=EpistemologicalAuthority.ASSESSMENT_ENGINE.value,
        task=_make_spec_ref("task-01", task_sha256),
        rubric=_make_spec_ref("rubric-01", rubric_sha256),
        observations=(_make_obs_ref(),),
        instrumental_facts=(_make_instrumental_fact(),),
        evaluative_facts=(_make_evaluative_fact(),),
        dimension_evaluations=(
            _make_dimension_eval(
                passed=passed,
                status=status,
                assigned_level=dim_level,
            ),
        ),
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
    with_spine: bool = True,
) -> SessionProvenanceContext:
    now = datetime.now(timezone.utc)
    started_at = now - timedelta(hours=1)
    spine = _make_spine(student_id, node_id) if with_spine else None

    return SessionProvenanceContext(
        student_id=student_id,
        session_id="session-1",
        resolved_target_node_id=node_id,
        roadmap_revision_id="e" * 64,
        policy_revision_id="f" * 64,
        expected_task_specification_sha256=task_sha256,
        expected_rubric_specification_sha256=rubric_sha256,
        session_is_active=True,
        session_started_at=started_at,
        spine=spine,
    )


class TestEvidenceIngestionEngineNominal:
    """Test suite for nominal ingestion flows."""

    def test_ingest_assessment_pass_admitted_and_committed(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Nominal passing assessment admitted and recorded in ledger."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result(
            passed=True,
            overall_level=PerformanceLevel.N3_COMPETENT,
        )
        context = _make_context()

        result = engine.ingest_assessment(assessment, context, ledger)

        # 1. Admission verified
        assert result.admission.decision == AdmissionDecision.ADMITTED
        assert result.admission.outcome == EvidenceOutcome.PASS
        assert result.admission.rejection_reason is None
        assert (
            result.admission.admission_trace.integrity == GateVerdict.PASS
        )
        assert (
            result.admission.admission_trace.provenance == GateVerdict.PASS
        )
        assert result.admission.admission_trace.session == GateVerdict.PASS
        assert (
            result.admission.admission_trace.anti_replay == GateVerdict.PASS
        )

        # 2. EvidenceRecord verified
        record = result.evidence_record
        assert record is not None
        assert record.authority_id == EpistemologicalAuthority.EVIDENCE_POLICY
        assert record.outcome == EvidenceOutcome.PASS
        assert record.score == 1.0
        assert record.overall_level == PerformanceLevel.N3_COMPETENT
        assert record.assessment_digest == assessment.assessment_digest
        assert record.node_id == context.resolved_target_node_id
        assert record.student_id == context.student_id
        assert record.actor_type == ActorType.TOOL_VERIFIER
        assert record.evidence_type == EvidenceType.CODE_EXECUTION

        # 3. LedgerEntry verified
        entry = result.ledger_entry
        assert entry is not None
        assert entry.record.record_id == record.record_id
        assert ledger.total_entries == 1
        assert ledger.has_assessment_digest(assessment.assessment_digest)

    def test_ingest_assessment_fail_admitted_and_committed(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Admissible failing assessment recorded as FAIL evidence."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result(
            passed=False,
            overall_level=PerformanceLevel.N1_INSUFFICIENT,
        )
        context = _make_context()

        result = engine.ingest_assessment(assessment, context, ledger)

        assert result.admission.decision == AdmissionDecision.ADMITTED
        assert result.admission.outcome == EvidenceOutcome.FAIL
        assert result.evidence_record is not None
        assert result.evidence_record.outcome == EvidenceOutcome.FAIL
        assert result.evidence_record.score == 0.0
        assert result.evidence_record.overall_level == (
            PerformanceLevel.N1_INSUFFICIENT
        )
        assert result.ledger_entry is not None
        assert ledger.total_entries == 1

    def test_ingest_assessment_inconclusive_admitted_neutrally(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Insufficient observation maps to INCONCLUSIVE evidence."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result(
            passed=False,
            overall_level=None,
            insufficient_dimensions=("dim-clean-exit",),
        )
        context = _make_context()

        result = engine.ingest_assessment(assessment, context, ledger)

        assert result.admission.decision == AdmissionDecision.ADMITTED
        assert result.admission.outcome == EvidenceOutcome.INCONCLUSIVE
        assert result.evidence_record is not None
        assert result.evidence_record.outcome == EvidenceOutcome.INCONCLUSIVE
        assert result.evidence_record.score == 0.0
        assert result.evidence_record.overall_level is None
        assert result.ledger_entry is not None
        assert ledger.total_entries == 1


class TestEvidenceIngestionEngineEdgeCases:
    """Test suite for edge cases, preflight, and concurrent race conditions."""

    def test_preflight_evaluation_without_ledger_reference(self) -> None:
        """Admissibility evaluation operates cleanly when ledger is None."""
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result(passed=True)
        context = _make_context()

        admission = engine.evaluate_admissibility(
            assessment, context, ledger=None
        )

        assert admission.decision == AdmissionDecision.ADMITTED
        assert admission.outcome == EvidenceOutcome.PASS
        assert admission.admission_trace.anti_replay == GateVerdict.PASS

    def test_rejection_prevents_ledger_mutation(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Rejected assessment produces None record and zero mutations."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result(task_sha256="1" * 64)
        context = _make_context(task_sha256="2" * 64)

        result = engine.ingest_assessment(assessment, context, ledger)

        assert result.admission.decision == AdmissionDecision.REJECTED
        assert (
            result.admission.rejection_reason
            == RejectionReason.SPECIFICATION_REVISION_MISMATCH
        )
        assert result.evidence_record is None
        assert result.ledger_entry is None
        assert ledger.total_entries == 0

    def test_concurrent_duplicate_race_transformed_to_rejected(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Atomic race caught during append_record is safely converted."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result(passed=True)
        context = _make_context()

        # Mock ledger.append_record to simulate concurrent duplicate collision
        mock_ledger = MagicMock(spec=ledger)
        mock_ledger.has_assessment_digest.return_value = False
        mock_ledger.append_record.side_effect = DuplicateEvidenceError(
            f"EvidenceRecord with assessment_digest "
            f"'{assessment.assessment_digest}' already committed to ledger."
        )

        result = engine.ingest_assessment(assessment, context, mock_ledger)

        # Must be converted into safe REJECTED admission
        assert result.admission.decision == AdmissionDecision.REJECTED
        assert (
            result.admission.rejection_reason
            == RejectionReason.DUPLICATE_ASSESSMENT_REPLAY
        )
        assert result.admission.admission_trace.anti_replay == (
            GateVerdict.FAIL
        )
        assert (
            "anti_replay.atomic_collision"
            in result.admission.admission_trace.details
        )
        assert result.evidence_record is None
        assert result.ledger_entry is None
