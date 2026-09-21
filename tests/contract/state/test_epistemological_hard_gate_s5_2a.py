"""Contract Epistemological Hard Gates for S5.2.A (HG-S5.2A-EP-01..12).

Validates static and runtime epistemological isolation of Subsystem S5.2.A:
- HG-S5.2A-EP-01: Rejection Non-Penalization (REJECTED produces 0 mutations)
- HG-S5.2A-EP-02: Inconclusive Non-Regression (0 regression triggered)
- HG-S5.2A-EP-03: Inconclusive Non-Satisfaction (INCONCLUSIVE != PASS)
- HG-S5.2A-EP-04: Digest Structural Verification (tampered byte fails closed)
- HG-S5.2A-EP-05: Anti-Replay Enforcement (preflight + ledger uniqueness)
- HG-S5.2A-EP-06: Provenance Lineage Binding (missing obs / spine mismatch)
- HG-S5.2A-EP-07: Deterministic Session Validity (evaluated at assessed_at)
- HG-S5.2A-EP-08: Single Sovereign Authority (EVIDENCE_POLICY mandatory)
- HG-S5.2A-EP-09: Zero Execution/LLM (AST: 0 subprocess, llm, or execution)
- HG-S5.2A-EP-10: Zero State Derivation (AST: 0 derive_student_state)
- HG-S5.2A-EP-11: Two-Stage Replay Guarantee (preflight + atomic commit)
- HG-S5.2A-EP-12: No Secondary Evaluation (overall_level copied verbatim)
"""

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Set
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
from study_engine.contracts.epistemology import (
    EpistemologicalAuthority,
    EpistemologicalAuthorityViolationError,
)
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
    CriteriaEvaluationVerdict,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
)
from study_engine.state.policy_engine import evaluate_node_criteria

SRC_DIR = Path(__file__).resolve().parent.parent.parent.parent / "src"
INGESTION_ENGINE_PATH = (
    SRC_DIR / "study_engine" / "state" / "ingestion_engine.py"
)
CONTRACTS_INGESTION_PATH = (
    SRC_DIR / "study_engine" / "contracts" / "evidence_ingestion.py"
)


def _get_ast_imported_modules(py_path: Path) -> Set[str]:
    """Parse python source file and return all imported module names."""
    tree = ast.parse(py_path.read_text(encoding="utf-8"))
    imports: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _get_ast_referenced_names(py_path: Path) -> Set[str]:
    """Return all referenced Name and Attribute identifiers from file."""
    tree = ast.parse(py_path.read_text(encoding="utf-8"))
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


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
) -> SessionProvenanceContext:
    now = datetime.now(timezone.utc)
    started_at = now - timedelta(hours=1)
    spine = _make_spine(student_id, node_id)

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


class TestEpistemologicalHardGatesS52A:
    """The 12 Epistemological Hard Gates for S5.2.A Evidence Ingestion."""

    def test_ep_01_rejection_non_penalization(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """HG-S5.2A-EP-01: REJECTED produces 0 records, 0 mutations."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result(task_sha256="1" * 64)
        context = _make_context(task_sha256="2" * 64)

        result = engine.ingest_assessment(assessment, context, ledger)

        assert result.admission.decision == AdmissionDecision.REJECTED
        assert result.evidence_record is None
        assert result.ledger_entry is None
        assert ledger.total_entries == 0

    def test_ep_02_inconclusive_non_regression(self) -> None:
        """HG-S5.2A-EP-02: INCONCLUSIVE records cause zero regression."""
        now = datetime.now(timezone.utc)
        criteria = NodeAssessmentCriteria(
            criteria_id="crit-proc",
            target_node_id="node-proc",
            requirements=(
                EvidenceRequirement(
                    requirement_id="req-code",
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    min_count=1,
                    min_score=0.8,
                ),
            ),
            regression_threshold_failures=2,
        )

        pass_record = EvidenceRecord(
            record_id="ev-pass",
            student_id="student-1",
            node_id="node-proc",
            evidence_type=EvidenceType.CODE_EXECUTION,
            outcome=EvidenceOutcome.PASS,
            score=1.0,
            timestamp=now - timedelta(hours=3),
            actor_type=ActorType.TOOL_VERIFIER,
            actor_id="tool-verifier-01",
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
            roadmap_revision_id="e" * 64,
            policy_revision_id="f" * 64,
        )

        # 5 subsequent INCONCLUSIVE records
        history: List[EvidenceRecord] = [pass_record]
        for i in range(5):
            inconclusive_record = EvidenceRecord(
                record_id=f"ev-inconclusive-{i}",
                student_id="student-1",
                node_id="node-proc",
                evidence_type=EvidenceType.CODE_EXECUTION,
                outcome=EvidenceOutcome.INCONCLUSIVE,
                score=0.0,
                timestamp=now - timedelta(hours=2) + timedelta(minutes=i * 10),
                actor_type=ActorType.TOOL_VERIFIER,
                actor_id="tool-verifier-01",
                authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                roadmap_revision_id="e" * 64,
                policy_revision_id="f" * 64,
            )
            history.append(inconclusive_record)

        eval_result = evaluate_node_criteria(
            criteria=criteria,
            history=history,
            as_of_time=now,
        )

        assert eval_result.verdict == CriteriaEvaluationVerdict.SATISFIED
        assert eval_result.subsequent_failures_count == 0

    def test_ep_03_inconclusive_non_satisfaction(self) -> None:
        """HG-S5.2A-EP-03: INCONCLUSIVE evidence does not satisfy criteria."""
        now = datetime.now(timezone.utc)
        criteria = NodeAssessmentCriteria(
            criteria_id="crit-proc",
            target_node_id="node-proc",
            requirements=(
                EvidenceRequirement(
                    requirement_id="req-code",
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    min_count=1,
                    min_score=0.8,
                ),
            ),
            regression_threshold_failures=2,
        )

        # 5 INCONCLUSIVE records, 0 PASS records
        history: List[EvidenceRecord] = []
        for i in range(5):
            inconclusive_record = EvidenceRecord(
                record_id=f"ev-inconclusive-{i}",
                student_id="student-1",
                node_id="node-proc",
                evidence_type=EvidenceType.CODE_EXECUTION,
                outcome=EvidenceOutcome.INCONCLUSIVE,
                score=0.0,
                timestamp=now - timedelta(hours=2) + timedelta(minutes=i * 10),
                actor_type=ActorType.TOOL_VERIFIER,
                actor_id="tool-verifier-01",
                authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                roadmap_revision_id="e" * 64,
                policy_revision_id="f" * 64,
            )
            history.append(inconclusive_record)

        eval_result = evaluate_node_criteria(
            criteria=criteria,
            history=history,
            as_of_time=now,
        )

        assert eval_result.verdict == CriteriaEvaluationVerdict.UNSATISFIED
        assert "req-code" in eval_result.missing_requirements

    def test_ep_04_digest_structural_verification(self) -> None:
        """HG-S5.2A-EP-04: Altered payload causes hash mismatch rejection."""
        engine = EvidenceIngestionEngine()
        valid = _make_assessment_result()
        tampered = valid.model_copy(
            update={"assessment_digest": "deadbeef" * 8}
        )
        context = _make_context()

        admission = engine.evaluate_admissibility(tampered, context)
        assert admission.decision == AdmissionDecision.REJECTED
        assert (
            admission.rejection_reason
            == RejectionReason.CORRUPTED_ASSESSMENT_DIGEST
        )
        assert admission.admission_trace.integrity == GateVerdict.FAIL

    def test_ep_05_anti_replay_enforcement(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """HG-S5.2A-EP-05: Ledger and oracle detect and reject duplicates."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        context = _make_context()

        # Ingest once
        res1 = engine.ingest_assessment(assessment, context, ledger)
        assert res1.admission.decision == AdmissionDecision.ADMITTED
        assert ledger.has_assessment_digest(assessment.assessment_digest)

        # Preflight reject duplicate
        admission = engine.evaluate_admissibility(
            assessment, context, ledger=ledger
        )
        assert admission.decision == AdmissionDecision.REJECTED
        assert (
            admission.rejection_reason
            == RejectionReason.DUPLICATE_ASSESSMENT_REPLAY
        )
        assert admission.admission_trace.anti_replay == GateVerdict.FAIL

    def test_ep_06_provenance_lineage_binding(self) -> None:
        """HG-S5.2A-EP-06: Missing observations or broken spine fails."""
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        mismatched_spine = _make_spine(
            student_id="student-1",
            node_id="node-other",
        )
        context = _make_context(node_id="node-proc")
        context = context.model_copy(update={"spine": mismatched_spine})

        admission = engine.evaluate_admissibility(assessment, context)
        assert admission.decision == AdmissionDecision.REJECTED
        assert (
            admission.rejection_reason
            == RejectionReason.BROKEN_PROVENANCE_CHAIN
        )
        assert admission.admission_trace.provenance == GateVerdict.FAIL

    def test_ep_07_deterministic_session_validity(self) -> None:
        """HG-S5.2A-EP-07: Session evaluated strictly at assessed_at."""
        engine = EvidenceIngestionEngine()
        now = datetime.now(timezone.utc)
        # Assessed at now, but session expired 10 minutes ago
        assessment = _make_assessment_result(assessed_at=now)
        context = _make_context()
        expired_context = context.model_copy(
            update={"session_expires_at": now - timedelta(minutes=10)}
        )

        admission = engine.evaluate_admissibility(assessment, expired_context)
        assert admission.decision == AdmissionDecision.REJECTED
        assert (
            admission.rejection_reason
            == RejectionReason.SESSION_INACTIVE_OR_EXPIRED
        )
        assert admission.admission_trace.session == GateVerdict.FAIL

    def test_ep_08_single_sovereign_authority(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """HG-S5.2A-EP-08: EvidenceRecord requires EVIDENCE_POLICY."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        context = _make_context()

        result = engine.ingest_assessment(assessment, context, ledger)
        assert result.evidence_record is not None
        assert (
            result.evidence_record.authority_id
            == EpistemologicalAuthority.EVIDENCE_POLICY
        )

        # Non-EVIDENCE_POLICY rejected by ledger
        spoofed = result.evidence_record.model_copy(
            update={"authority_id": EpistemologicalAuthority.EXECUTION_PLANE}
        )
        with pytest.raises(EpistemologicalAuthorityViolationError):
            ledger.append_record(spoofed)

    def test_ep_09_zero_code_execution_ast_purity(self) -> None:
        """HG-S5.2A-EP-09: S5.2.A contains 0 execution or LLM imports."""
        for file_path in (INGESTION_ENGINE_PATH, CONTRACTS_INGESTION_PATH):
            imports = _get_ast_imported_modules(file_path)
            for mod in imports:
                assert not (
                    mod == "subprocess"
                    or mod.startswith("subprocess.")
                    or "study_engine.llm" in mod
                    or "study_engine.execution" in mod
                    or "requests" in mod
                    or "httpx" in mod
                    or "urllib" in mod
                ), (
                    f"EP-09 Violation in '{file_path.name}': "
                    f"Forbidden execution or network module imported: '{mod}'."
                )

    def test_ep_10_zero_state_derivation_ast_purity(self) -> None:
        """HG-S5.2A-EP-10: Ingestion engine cannot import state derivation."""
        imports = _get_ast_imported_modules(INGESTION_ENGINE_PATH)
        for mod in imports:
            assert "state_engine" not in mod, (
                f"EP-10 Violation in '{INGESTION_ENGINE_PATH.name}': "
                f"Forbidden state derivation module imported: '{mod}'."
            )
        names = _get_ast_referenced_names(INGESTION_ENGINE_PATH)
        assert "derive_student_state" not in names, (
            f"EP-10 Violation: 'derive_student_state' referenced in "
            f"{INGESTION_ENGINE_PATH.name}."
        )

    def test_ep_11_replay_guarantee_across_preflight_and_persistence(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """HG-S5.2A-EP-11: Preflight oracle + atomic race guarantee."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result()
        context = _make_context()

        # 1. First ingestion succeeds
        res1 = engine.ingest_assessment(assessment, context, ledger)
        assert res1.admission.decision == AdmissionDecision.ADMITTED

        # 2. Layer 1: Preflight query oracle rejects before persistence
        admission_preflight = engine.evaluate_admissibility(
            assessment, context, ledger=ledger
        )
        assert admission_preflight.decision == AdmissionDecision.REJECTED
        assert (
            admission_preflight.rejection_reason
            == RejectionReason.DUPLICATE_ASSESSMENT_REPLAY
        )

        # 3. Layer 2: Atomic concurrent race during commit converted safely
        mock_ledger = MagicMock(spec=ledger)
        mock_ledger.has_assessment_digest.return_value = False
        mock_ledger.append_record.side_effect = DuplicateEvidenceError(
            "Concurrent race duplicate detected"
        )
        race_res = engine.ingest_assessment(assessment, context, mock_ledger)
        assert race_res.admission.decision == AdmissionDecision.REJECTED
        assert (
            race_res.admission.rejection_reason
            == RejectionReason.DUPLICATE_ASSESSMENT_REPLAY
        )
        assert race_res.evidence_record is None
        assert race_res.ledger_entry is None

    def test_ep_12_no_secondary_evaluation(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """HG-S5.2A-EP-12: S5.2.A copies overall_level verbatim."""
        ledger = EvidenceLedger(file_path=Path(str(tmp_path)) / "ledger.jsonl")
        engine = EvidenceIngestionEngine()
        assessment = _make_assessment_result(
            passed=True,
            overall_level=PerformanceLevel.N4_EXCELLENT,
        )
        context = _make_context()

        result = engine.ingest_assessment(assessment, context, ledger)
        assert result.evidence_record is not None
        assert (
            result.evidence_record.overall_level
            == PerformanceLevel.N4_EXCELLENT
        )

        # AST inspection: no recalculation methods
        names = _get_ast_referenced_names(INGESTION_ENGINE_PATH)
        for forbidden in (
            "evaluate_practical_task",
            "aggregate_evaluations",
            "calculate_level",
            "recompute_level",
        ):
            assert forbidden not in names, (
                f"EP-12 Violation: '{forbidden}' referenced in S5.2.A."
            )
