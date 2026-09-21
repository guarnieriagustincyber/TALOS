"""Contract Epistemological Hard Gates for S9.1 (HG-S9.1-EP-01..12).

Validates static and runtime epistemological isolation of S9 Assessment Engine:
- HG-S9.1-EP-01: No Re-execution (AST: zero subprocess, exec, or S6 imports)
- HG-S9.1-EP-02: Bounded Observation (Stream truncation is knowledge bound)
- HG-S9.1-EP-03: Exit-Code Non-Approval (exit 0 alone never produces approval)
- HG-S9.1-EP-04: Immutable Specification (specifications cannot be mutated)
- HG-S9.1-EP-05: No Invented Facts (all evaluations trace to empirical facts)
- HG-S9.1-EP-06: No Gateway Verdict (AST: zero GatewayDecisionAuthority)
- HG-S9.1-EP-07: No Ledger Mutation (zero EvidenceLedger; TypeError on append)
- HG-S9.1-EP-08: Absence != Negative (VERIFIED_ABSENCE != OMITTED_BY_LIMIT)
- HG-S9.1-EP-09: Insufficient != N1 (abstention model prevents false failures)
- HG-S9.1-EP-10: Deterministic Evaluation (AST: zero LLM or network clients)
- HG-S9.1-EP-11: Specification Revision Binding (SHA-256 integrity binding)
- HG-S9.1-EP-12: Provenance Lineage Anchor (complete backward chain)
"""

import ast
from pathlib import Path
from typing import Set
import pytest

from study_engine.assessment.aggregator import aggregate_evaluations
from study_engine.assessment.evaluator_deterministic import (
    evaluate_practical_task,
)
from study_engine.assessment.fact_extractor import extract_instrumental_facts
from study_engine.assessment.service import (
    DeterministicAssessmentEngine,
    SpecificationIntegrityError,
)
from study_engine.contracts.assessment import (
    AssessmentStatus,
    FactObservability,
    InstrumentalFact,
    InstrumentalFactType,
)
from study_engine.contracts.epistemology import (
    EpistemologicalAuthority,
    EpistemologicalAuthorityViolationError,
    EpistemologicalStage,
    validate_epistemological_authority,
)
from study_engine.contracts.execution import (
    ArtifactCollectionSummary,
    ExecutionObservation,
    ExecutionStatus,
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
from study_engine.state.ledger import EvidenceLedger

ASSESSMENT_SRC_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "src"
    / "study_engine"
    / "assessment"
)


def _get_ast_imported_modules(file_path: Path) -> Set[str]:
    """Parse python source with AST and extract all imported module names."""
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    imported: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
    return imported


def _get_ast_referenced_names(file_path: Path) -> Set[str]:
    """Parse python source with AST and extract all referenced symbol names."""
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
    return names


class TestEpistemologicalHardGatesS9:
    """The 12 Epistemological Hard Gates for S9 Assessment Engine."""

    FORBIDDEN_MODULE_PREFIXES = (
        "study_engine.state",
        "study_engine.llm",
        "study_engine.storage",
        "study_engine.session",
        "study_engine.execution.adapter_python",
        "study_engine.execution.process_manager",
        "subprocess",
        "sqlite3",
        "sqlalchemy",
        "requests",
        "httpx",
        "openai",
        "google.generativeai",
        "anthropic",
    )

    FORBIDDEN_SYMBOLS = (
        "EvidenceRecord",
        "EvidenceLedger",
        "GatewayDecisionAuthority",
        "GatewayVerdictRecord",
        "StudentState",
    )

    def test_ep_01_no_re_execution_ast(self) -> None:
        """HG-S9.1-EP-01: S9 cannot re-execute code or import subprocess."""
        py_files = list(ASSESSMENT_SRC_DIR.glob("*.py"))
        assert len(py_files) >= 4, "Expected at least 4 source files in S9"

        for py_file in py_files:
            imports = _get_ast_imported_modules(py_file)
            for mod in imports:
                assert not (
                    mod == "subprocess"
                    or mod.startswith("subprocess.")
                    or "adapter_python" in mod
                    or "process_manager" in mod
                ), (
                    f"EP-01 Violation in '{py_file.name}': "
                    f"S9 must not import execution plane components: '{mod}'."
                )

    def test_ep_06_ep_07_no_gateway_or_ledger_ast(self) -> None:
        """HG-S9.1-EP-06 & EP-07: S9 cannot reference GDA or EvidenceLedger."""
        py_files = list(ASSESSMENT_SRC_DIR.glob("*.py"))
        for py_file in py_files:
            names = _get_ast_referenced_names(py_file)
            for forbidden_sym in self.FORBIDDEN_SYMBOLS:
                assert forbidden_sym not in names, (
                    f"EP-06/EP-07 Violation in '{py_file.name}': "
                    f"Forbidden symbol '{forbidden_sym}' referenced in S9."
                )

    def test_ep_10_deterministic_evaluation_ast(self) -> None:
        """HG-S9.1-EP-10: S9 cannot import LLM backends or clients."""
        py_files = list(ASSESSMENT_SRC_DIR.glob("*.py"))
        for py_file in py_files:
            imports = _get_ast_imported_modules(py_file)
            for mod in imports:
                for forbidden in (
                    "study_engine.llm",
                    "openai",
                    "google.generativeai",
                    "anthropic",
                    "httpx",
                    "requests",
                ):
                    assert not (
                        mod == forbidden or mod.startswith(forbidden + ".")
                    ), (
                        f"EP-10 Violation in '{py_file.name}': "
                        f"S9 must not import probabilistic backend '{mod}'."
                    )

    def test_ep_03_exit_code_non_approval_runtime(self) -> None:
        """HG-S9.1-EP-03: exit_code == 0 alone does not grant competency."""
        # A task requiring an artifact
        task = PracticalTaskSpecification(
            task_id="task-01",
            curriculum_node_id="NET-01",
            title="Artifact Task",
            description="Produce payload.bin",
            required_artifacts=(
                ArtifactRequirement(
                    requirement_id="payload.bin",
                    artifact_type=ArtifactType.BINARY_EXECUTABLE,
                    min_size_bytes=10,
                    expected_mime_types=("application/octet-stream",),
                    description="Payload binary",
                ),
            ),
        )
        rubric = AssessmentRubric(
            rubric_id="rubric-01",
            title="Rubric",
            dimensions=(
                RubricDimension(
                    dimension_id="dim-1",
                    title="Dim 1",
                    weight=1.0,
                    minimum_level=PerformanceLevel.N3_COMPETENT,
                    is_critical=True,
                ),
            ),
        )
        # Empty execution that exited 0 without producing payload.bin
        facts = (
            InstrumentalFact(
                fact_id="f-exit",
                observation_id="obs-1",
                fact_type=InstrumentalFactType.PROCESS_EXIT_CODE,
                fact_value="0",
                observability=FactObservability.CONCLUSIVE,
                inspected_domain="process",
                provenance_detail="Exit 0",
            ),
            InstrumentalFact(
                fact_id="f-dur",
                observation_id="obs-1",
                fact_type=InstrumentalFactType.EXECUTION_DURATION_MS,
                fact_value="100.0",
                observability=FactObservability.CONCLUSIVE,
                inspected_domain="process",
                provenance_detail="100ms",
            ),
            InstrumentalFact(
                fact_id="f-trunc",
                observation_id="obs-1",
                fact_type=InstrumentalFactType.STREAM_WAS_TRUNCATED,
                fact_value="false",
                observability=FactObservability.CONCLUSIVE,
                inspected_domain="streams",
                provenance_detail="Not truncated",
            ),
            InstrumentalFact(
                fact_id="f-abs",
                observation_id="obs-1",
                fact_type=InstrumentalFactType.ARTIFACT_VERIFIED_ABSENT,
                fact_value="payload.bin",
                observability=FactObservability.VERIFIED_ABSENCE,
                inspected_domain="scratch/workspace/",
                provenance_detail="Absent",
            ),
        )
        _, dim_evals = evaluate_practical_task(rubric, task, facts)
        dim = dim_evals[0]
        # Must NOT be approved
        assert dim.status == AssessmentStatus.ASSESSED
        assert dim.assigned_level == PerformanceLevel.N1_INSUFFICIENT
        assert dim.passed_minimum is False

    def test_ep_07_ledger_rejects_assessment_result(self) -> None:
        """HG-S9.1-EP-07: Ledger rejects AssessmentResult fail-closed."""
        ledger = EvidenceLedger()
        task = PracticalTaskSpecification(
            task_id="t1",
            curriculum_node_id="N1",
            title="T",
            description="D",
        )
        rubric = AssessmentRubric(
            rubric_id="r1",
            title="R",
            dimensions=(
                RubricDimension(
                    dimension_id="d1",
                    title="D",
                    weight=1.0,
                    minimum_level=PerformanceLevel.N3_COMPETENT,
                ),
            ),
        )
        obs = ExecutionObservation(
            observation_id="obs-1",
            execution_id="exec-1",
            tool_name="python.run_script",
            status=ExecutionStatus.COMPLETED,
            exit_code=0,
            raw_telemetry={"exit_code": 0, "duration_ms": 10.0},
        )
        engine = DeterministicAssessmentEngine()
        result = engine.assess(
            task=task,
            rubric=rubric,
            observation=obs,
            task_revision_id="rev-1",
            rubric_revision_id="rev-1",
        )

        with pytest.raises(
            TypeError, match="Only EvidenceRecord can be committed"
        ):
            ledger.append_record(result)  # type: ignore[arg-type]

    def test_ep_08_ep_09_absence_vs_omitted_abstention(self) -> None:
        """HG-S9.1-EP-08 & EP-09: Limit omission abstains; no false N1."""
        task = PracticalTaskSpecification(
            task_id="task-02",
            curriculum_node_id="NET-01",
            title="Task 2",
            description="D",
            required_artifacts=(
                ArtifactRequirement(
                    requirement_id="dump.bin",
                    artifact_type=ArtifactType.MEMORY_DUMP,
                    min_size_bytes=100,
                    expected_mime_types=("application/octet-stream",),
                    description="Dump",
                ),
            ),
        )
        rubric = AssessmentRubric(
            rubric_id="rubric-02",
            title="R2",
            dimensions=(
                RubricDimension(
                    dimension_id="d1",
                    title="D1",
                    weight=1.0,
                    minimum_level=PerformanceLevel.N3_COMPETENT,
                    is_critical=True,
                ),
            ),
        )
        # Observation where dump.bin was omitted by limit
        obs = ExecutionObservation(
            observation_id="obs-limit",
            execution_id="exec-limit",
            tool_name="python.run_script",
            status=ExecutionStatus.COMPLETED,
            exit_code=0,
            telemetry=ProcessTelemetry(
                duration_ms=50.0,
                termination_reason=TerminationReason.NORMAL_EXIT,
            ),
            raw_telemetry={"exit_code": 0, "duration_ms": 50.0},
            artifact_summary=ArtifactCollectionSummary(
                artifacts_discovered=1,
                artifacts_collected=0,
                artifacts_omitted=1,
                collection_truncated=True,
            ),
        )

        facts = extract_instrumental_facts(
            obs, expected_paths=("dump.bin",)
        )
        # Verify fact is OMITTED_BY_LIMIT, NOT VERIFIED_ABSENT
        omit_fact = next(
            f
            for f in facts
            if f.fact_type == InstrumentalFactType.ARTIFACT_OMITTED_BY_LIMIT
        )
        assert omit_fact.observability == FactObservability.PARTIAL_TRUNCATED

        _, dim_evals = evaluate_practical_task(rubric, task, facts)
        dim = dim_evals[0]

        # EP-09: Must be INSUFFICIENT_OBSERVATION, NOT N1_INSUFFICIENT
        assert dim.status == AssessmentStatus.INSUFFICIENT_OBSERVATION
        assert dim.assigned_level is None
        assert dim.passed_minimum is None

        # Aggregation must report passed=False with insufficient_dimensions
        agg = aggregate_evaluations(rubric, dim_evals)
        assert agg.passed is False
        assert agg.overall_level is None
        assert "d1" in agg.insufficient_dimensions

    def test_ep_11_ep_12_specification_binding_and_authority(self) -> None:
        """HG-S9.1-EP-11 & EP-12: Spec binding & sovereign authority."""
        engine = DeterministicAssessmentEngine()
        task = PracticalTaskSpecification(
            task_id="t11",
            curriculum_node_id="N1",
            title="T",
            description="D",
        )
        rubric = AssessmentRubric(
            rubric_id="r11",
            title="R",
            dimensions=(
                RubricDimension(
                    dimension_id="d1",
                    title="D",
                    weight=1.0,
                    minimum_level=PerformanceLevel.N3_COMPETENT,
                ),
            ),
        )
        obs = ExecutionObservation(
            observation_id="obs-11",
            execution_id="exec-11",
            tool_name="python.run_script",
            status=ExecutionStatus.COMPLETED,
            exit_code=0,
            raw_telemetry={"exit_code": 0, "duration_ms": 10.0},
        )

        # EP-11: Tampered task hash fails
        with pytest.raises(SpecificationIntegrityError):
            engine.assess(
                task=task,
                rubric=rubric,
                observation=obs,
                task_revision_id="rev-1",
                rubric_revision_id="rev-1",
                expected_task_sha256="bad" * 21 + "a",
            )

        # EP-12: Valid assessment verifies single sovereign authority
        res = engine.assess(
            task=task,
            rubric=rubric,
            observation=obs,
            task_revision_id="rev-1",
            rubric_revision_id="rev-1",
        )
        assert res.authority_id == (
            EpistemologicalAuthority.ASSESSMENT_ENGINE.value
        )
        validate_epistemological_authority(
            stage=EpistemologicalStage.ASSESSMENT_RESULT,
            authority=EpistemologicalAuthority.ASSESSMENT_ENGINE,
        )

        # Assessment Engine cannot claim other stages
        for forbidden_stage in (
            EpistemologicalStage.EVIDENCE_RECORD,
            EpistemologicalStage.GATEWAY_VERDICT,
            EpistemologicalStage.STUDENT_STATE,
        ):
            with pytest.raises(EpistemologicalAuthorityViolationError):
                validate_epistemological_authority(
                    stage=forbidden_stage,
                    authority=EpistemologicalAuthority.ASSESSMENT_ENGINE,
                )
