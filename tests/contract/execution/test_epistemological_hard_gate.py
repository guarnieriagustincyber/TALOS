"""Contract Epistemological Hard Gate HG-S6.1-EP-01.

Validates that Subsystem S6.1 (Controlled Practical Execution Engine)
strictly complies with the cardinal epistemological invariant:

    Observation (S6/S7)
        != AssessmentResult (S9/S10)
        != EvidenceRecord (S5.2.A)
        != GatewayVerdictRecord (GDA)
        != StudentState (S5.2.C)

Statically and dynamically enforces that:
1. S6 source files never import forbidden modules (state, curriculum,
   LLM, generation, audit, storage, or external HTTP clients).
2. S6 source files never reference or instantiate EvidenceRecord,
   AssessmentResult, GatewayVerdictRecord, or StudentState.
3. S6 adapter signatures strictly return ExecutionResult and
   ExecutionObservation.
4. S6 ExecutionObservation carries EpistemologicalAuthority.EXECUTION_PLANE
   and cannot be committed directly to EvidenceLedger.
"""

import ast
import inspect
from pathlib import Path
from typing import Set
import pytest

from study_engine.contracts.epistemology import (
    EpistemologicalAuthority,
    EpistemologicalAuthorityViolationError,
    EpistemologicalStage,
    validate_epistemological_authority,
)
from study_engine.contracts.execution import (
    ExecutionObservation,
    ExecutionResult,
    ExecutionStatus,
    ProcessTelemetry,
    TerminationReason,
)
from study_engine.execution.adapter_python import PythonExecutionAdapter
from study_engine.execution.base import BaseExecutionAdapter
from study_engine.state.ledger import EvidenceLedger


EXECUTION_SRC_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "src"
    / "study_engine"
    / "execution"
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


class TestEpistemologicalHardGateHG61:
    """Epistemological hard gate tests for S6.1 execution plane."""

    FORBIDDEN_MODULE_PREFIXES = (
        "study_engine.state",
        "study_engine.curriculum",
        "study_engine.generation",
        "study_engine.audit",
        "study_engine.llm",
        "study_engine.retrieval",
        "study_engine.storage",
        "study_engine.session",
        "sqlite3",
        "sqlalchemy",
        "requests",
        "httpx",
        "urllib.request",
        "openai",
        "google.generativeai",
        "anthropic",
    )

    FORBIDDEN_EPISTEMOLOGICAL_SYMBOLS = (
        "EvidenceRecord",
        "AssessmentResult",
        "GatewayVerdictRecord",
        "StudentState",
        "EvidenceLedger",
        "GatewayDecisionAuthority",
    )

    def test_ep_01_ast_no_forbidden_module_imports(self) -> None:
        """Every file in S6 execution must not import forbidden packages."""
        py_files = list(EXECUTION_SRC_DIR.glob("*.py"))
        assert len(py_files) >= 6, "Expected at least 6 source files in S6"

        for py_file in py_files:
            imports = _get_ast_imported_modules(py_file)
            for mod in imports:
                for forbidden in self.FORBIDDEN_MODULE_PREFIXES:
                    assert not (
                        mod == forbidden or mod.startswith(forbidden + ".")
                    ), (
                        f"Hard Gate EP-01 Violation in '{py_file.name}': "
                        f"S6 is forbidden from importing '{mod}'."
                    )

    def test_ep_02_ast_no_forbidden_symbol_references(self) -> None:
        """S6 source files must not reference pedagogical/eval symbols."""
        py_files = list(EXECUTION_SRC_DIR.glob("*.py"))
        for py_file in py_files:
            names = _get_ast_referenced_names(py_file)
            for forbidden_sym in self.FORBIDDEN_EPISTEMOLOGICAL_SYMBOLS:
                assert forbidden_sym not in names, (
                    f"Hard Gate EP-01 Violation in '{py_file.name}': "
                    f"Forbidden symbol '{forbidden_sym}' referenced in S6."
                )

    def test_ep_03_base_adapter_contract_signatures(self) -> None:
        """BaseExecutionAdapter signatures return ExecutionResult/Obs."""
        hints_execute = inspect.get_annotations(BaseExecutionAdapter.execute)
        assert hints_execute.get("return") in (
            "ExecutionResult",
            ExecutionResult,
        )

        hints_observe = inspect.get_annotations(BaseExecutionAdapter.observe)
        assert hints_observe.get("return") in (
            "ExecutionObservation",
            ExecutionObservation,
        )

    def test_ep_04_python_adapter_contract_signatures(self) -> None:
        """PythonExecutionAdapter adheres strictly to base adapter protocol."""
        adapter = PythonExecutionAdapter()
        assert isinstance(adapter, BaseExecutionAdapter)

        # Check return annotations
        hints_execute = inspect.get_annotations(PythonExecutionAdapter.execute)
        assert hints_execute.get("return") is ExecutionResult

        hints_observe = inspect.get_annotations(PythonExecutionAdapter.observe)
        assert hints_observe.get("return") is ExecutionObservation

        # Check adapter has zero pedagogical or evaluation methods
        adapter_members = set(dir(adapter))
        for forbidden in (
            "evaluate",
            "grade",
            "score",
            "assess",
            "commit",
            "record_evidence",
            "mutate_state",
            "verify_rubric",
        ):
            assert forbidden not in adapter_members, (
                f"Adapter must not expose pedagogical method '{forbidden}'"
            )

    def test_ep_05_execution_observation_authority_invariant(self) -> None:
        """ExecutionObservation carries S6_EXECUTION_PLANE authority."""
        # Legitimate authority validation succeeds
        validate_epistemological_authority(
            stage=EpistemologicalStage.OBSERVATION,
            authority=EpistemologicalAuthority.EXECUTION_PLANE,
        )

        # S6 Execution Plane cannot claim authority for subsequent stages
        for forbidden_stage in (
            EpistemologicalStage.ASSESSMENT_RESULT,
            EpistemologicalStage.EVIDENCE_RECORD,
            EpistemologicalStage.GATEWAY_VERDICT,
            EpistemologicalStage.STUDENT_STATE,
        ):
            with pytest.raises(EpistemologicalAuthorityViolationError):
                validate_epistemological_authority(
                    stage=forbidden_stage,
                    authority=EpistemologicalAuthority.EXECUTION_PLANE,
                )

    def test_ep_06_observe_emits_pure_instrumental_facts(self) -> None:
        """Adapter.observe emits only instrumental facts, no verdicts."""
        adapter = PythonExecutionAdapter()
        res = ExecutionResult(
            request_id="req-gate-01",
            execution_id="exec-gate-01",
            status=ExecutionStatus.COMPLETED,
            exit_code=0,
            stdout="hello world\n",
            stderr="",
            duration_ms=100.0,
            telemetry=ProcessTelemetry(
                duration_ms=100.0,
                termination_reason=TerminationReason.NORMAL_EXIT,
            ),
            effective_script_sha256="a" * 64,
        )

        obs = adapter.observe(res)
        assert isinstance(obs, ExecutionObservation)
        assert obs.authority_id == EpistemologicalAuthority.EXECUTION_PLANE
        assert obs.execution_id == "exec-gate-01"
        assert obs.raw_telemetry["status"] == "COMPLETED"
        assert obs.raw_telemetry["exit_code"] == 0

        # Epistemological check: no evaluative attributes exist on observation
        obs_dict = obs.model_dump()
        assert "score" not in obs_dict
        assert "grade" not in obs_dict
        assert "rubric" not in obs_dict
        assert "passed" not in obs_dict
        assert "mastery" not in obs_dict

    def test_ep_07_adapter_cannot_commit_to_ledger(self) -> None:
        """Ledger rejects S6 ExecutionObservation and ExecutionResult."""
        ledger = EvidenceLedger()
        res = ExecutionResult(
            request_id="req-gate-02",
            execution_id="exec-gate-02",
            status=ExecutionStatus.COMPLETED,
            exit_code=0,
            stdout="",
            stderr="",
            duration_ms=50.0,
            telemetry=ProcessTelemetry(
                duration_ms=50.0,
                termination_reason=TerminationReason.NORMAL_EXIT,
            ),
            effective_script_sha256="b" * 64,
        )
        obs = PythonExecutionAdapter().observe(res)

        # ExecutionObservation rejected
        with pytest.raises(
            TypeError, match="Only EvidenceRecord can be committed"
        ):
            ledger.append_record(obs)  # type: ignore[arg-type]

        # ExecutionResult rejected
        with pytest.raises(
            TypeError, match="Only EvidenceRecord can be committed"
        ):
            ledger.append_record(res)  # type: ignore[arg-type]
