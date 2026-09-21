"""Adversarial stress and attack vector tests for S5.2.A Evidence Ingestion.

Covers 9 distinct adversarial attack vectors:
1. Forged assessment digest payload
2. Spoofed authority_id on assessment result
3. Sequential duplicate assessment replay
4. Concurrent race condition with duplicate assessment_digest
5. Expired session at assessment timestamp
6. Cross-student identity injection
7. Curricular node mismatch
8. Specification revision tampering
9. Invariant: Rejected assessment cannot mutate ledger
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
    authority_id: str = EpistemologicalAuthority.ASSESSMENT_ENGINE.value,
    assessed_at: Optional[datetime] = None,
) -> AssessmentResult:
    timestamp = assessed_at or datetime.now(timezone.utc)

    interim = AssessmentResult(
        assessment_id=assessment_id,
        authority_id=authority_id,
        task=_make_spec_ref("task-01", task_sha256),
        rubric=_make_spec_ref("rubric-01", rubric_sha256),
        observations=(_make_obs_ref(),),
        instrumental_facts=(_make_instrumental_fact(),),
        evaluative_facts=(_make_evaluative_fact(),),
        dimension_evaluations=(
            _make_dimension_eval(
                passed=passed,
                status=AssessmentStatus.ASSESSED,
                assigned_level=overall_level,
            ),
        ),
        aggregation=AggregationResult(
            overall_level=overall_level,
            passed=passed,
            insufficient_dimensions=(),
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


class TestAdversarialEvidenceIngestion:
    """Adversarial test suite challenging S5.2.A boundaries."""

    def test_adversarial_v01_forged_assessment_digest(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Vector 1: Attacker forges digest; rejected at Gate 1."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        tampered = assessment.model_copy(
            update={"assessment_digest": "badc0ffee0" * 6 + "0000"}
        )
        context = _make_context()

        result = engine.ingest_assessment(tampered, context, ledger)

        assert result.admission.decision == AdmissionDecision.REJECTED
        assert (
            result.admission.rejection_reason
            == RejectionReason.CORRUPTED_ASSESSMENT_DIGEST
        )
        assert result.admission.admission_trace.integrity == GateVerdict.FAIL
        assert result.evidence_record is None
        assert result.ledger_entry is None
        assert ledger.total_entries == 0

    def test_adversarial_v02_spoofed_authority_id(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Vector 2: Attacker injects unauthorized authority."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result(
            authority_id="S6_EXECUTION_PLANE"
        )
        context = _make_context()

        result = engine.ingest_assessment(assessment, context, ledger)

        assert result.admission.decision == AdmissionDecision.REJECTED
        assert (
            result.admission.rejection_reason
            == RejectionReason.UNAUTHORIZED_ASSESSMENT_AUTHORITY
        )
        assert result.admission.admission_trace.integrity == GateVerdict.FAIL
        assert result.evidence_record is None
        assert ledger.total_entries == 0

    def test_adversarial_v03_sequential_duplicate_replay(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Vector 3: Attacker replays genuine passing assessment."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        context = _make_context()

        # Legitimate submission
        res1 = engine.ingest_assessment(assessment, context, ledger)
        assert res1.admission.decision == AdmissionDecision.ADMITTED
        assert ledger.total_entries == 1

        # Replay attempt
        res2 = engine.ingest_assessment(assessment, context, ledger)
        assert res2.admission.decision == AdmissionDecision.REJECTED
        assert (
            res2.admission.rejection_reason
            == RejectionReason.DUPLICATE_ASSESSMENT_REPLAY
        )
        assert (
            res2.admission.admission_trace.anti_replay == GateVerdict.FAIL
        )
        assert res2.evidence_record is None
        assert ledger.total_entries == 1  # Not mutated

    def test_adversarial_v04_concurrent_race_condition(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Vector 4: Concurrent commit collision converted to REJECTED."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        context = _make_context()

        mock_ledger = MagicMock(spec=ledger)
        mock_ledger.has_assessment_digest.return_value = False
        mock_ledger.append_record.side_effect = DuplicateEvidenceError(
            f"EvidenceRecord with assessment_digest "
            f"'{assessment.assessment_digest}' already committed to ledger."
        )

        result = engine.ingest_assessment(assessment, context, mock_ledger)

        assert result.admission.decision == AdmissionDecision.REJECTED
        assert (
            result.admission.rejection_reason
            == RejectionReason.DUPLICATE_ASSESSMENT_REPLAY
        )
        assert (
            result.admission.admission_trace.anti_replay == GateVerdict.FAIL
        )
        assert result.evidence_record is None
        assert result.ledger_entry is None

    def test_adversarial_v05_expired_session(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Vector 5: Attacker submits assessment from expired session."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        now = datetime.now(timezone.utc)
        assessment = _make_assessment_result(assessed_at=now)
        context = _make_context(
            session_started_at=now - timedelta(hours=3),
            session_expires_at=now - timedelta(hours=1),
        )

        result = engine.ingest_assessment(assessment, context, ledger)

        assert result.admission.decision == AdmissionDecision.REJECTED
        assert (
            result.admission.rejection_reason
            == RejectionReason.SESSION_INACTIVE_OR_EXPIRED
        )
        assert result.admission.admission_trace.session == GateVerdict.FAIL
        assert result.evidence_record is None
        assert ledger.total_entries == 0

    def test_adversarial_v06_cross_student_injection(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Vector 6: Assessment spine belonging to Student B into Student A."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        mismatched_spine = _make_spine(
            student_id="student-victim",
            node_id="node-proc",
        )
        context = _make_context(
            student_id="student-attacker", with_spine=False
        )
        context = context.model_copy(update={"spine": mismatched_spine})

        result = engine.ingest_assessment(assessment, context, ledger)

        assert result.admission.decision == AdmissionDecision.REJECTED
        assert (
            result.admission.rejection_reason
            == RejectionReason.STUDENT_IDENTITY_MISMATCH
        )
        assert result.admission.admission_trace.session == GateVerdict.FAIL
        assert result.evidence_record is None
        assert ledger.total_entries == 0

    def test_adversarial_v07_curricular_node_mismatch(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Vector 7: Spine bound to node X submitted for node Y."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        mismatched_spine = _make_spine(
            student_id="student-1",
            node_id="node-foreign",
        )
        context = _make_context(node_id="node-proc", with_spine=False)
        context = context.model_copy(update={"spine": mismatched_spine})

        result = engine.ingest_assessment(assessment, context, ledger)

        assert result.admission.decision == AdmissionDecision.REJECTED
        assert (
            result.admission.rejection_reason
            == RejectionReason.BROKEN_PROVENANCE_CHAIN
        )
        assert (
            result.admission.admission_trace.provenance == GateVerdict.FAIL
        )
        assert result.evidence_record is None
        assert ledger.total_entries == 0

    def test_adversarial_v08_specification_revision_tampering(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Vector 8: Outdated or altered task specification hash."""
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
        assert result.admission.admission_trace.integrity == GateVerdict.FAIL
        assert result.evidence_record is None
        assert ledger.total_entries == 0

    def test_adversarial_v09_rejected_assessment_cannot_mutate_ledger(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Vector 9: Universal invariant: REJECTED never touches ledger."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        context = _make_context()
        initial_tip = ledger.tip_hash
        assert initial_tip == "0" * 64

        # Array of malicious assessment variants
        variants = [
            # Bad digest
            _make_assessment_result().model_copy(
                update={"assessment_digest": "0" * 64}
            ),
            # Bad authority
            _make_assessment_result(authority_id="S6_EXECUTION_PLANE"),
            # Spec mismatch
            _make_assessment_result(task_sha256="9" * 64),
        ]

        for i, bad_assessment in enumerate(variants):
            res = engine.ingest_assessment(bad_assessment, context, ledger)
            assert res.admission.decision == AdmissionDecision.REJECTED
            assert res.evidence_record is None
            assert res.ledger_entry is None
            assert ledger.total_entries == 0
            assert ledger.tip_hash == initial_tip
