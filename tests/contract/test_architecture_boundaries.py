"""Contract test suite for Global Architecture Boundaries (S5.5).

Uses Python's AST module to inspect module imports across the codebase
and statically enforce Global Dependency Matrix and Security Boundaries.
Also verifies runtime type guards for EvidenceLedger and Authority.
"""

import ast
from pathlib import Path
from typing import Dict, Set
import pytest

from study_engine.contracts.epistemology import (
    EpistemologicalAuthority,
    EpistemologicalAuthorityViolationError,
    EpistemologicalStage,
    validate_epistemological_authority,
)
from study_engine.contracts.events import OperationalEvent
from study_engine.contracts.execution import (
    ExecutionObservation,
    ExecutionPlaneTier,
    ExecutionPolicy,
    TIER_CAPABILITIES_MATRIX,
    ToolCapability,
)
from study_engine.contracts.spine import (
    ExecutionProvenanceSpine,
    LineageVerificationError,
    SpineAssessment,
    SpineCurriculum,
    SpineExecution,
    SpineIdentity,
    SpineTerminalState,
    verify_spine_lineage,
)
from study_engine.contracts.verdict_authority import GatewayDecisionAuthority
from study_engine.curriculum.gateway_contracts import (
    GatewayDefinition,
    GatewayFormat,
    GatewayVerdictCriteria,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.state.ledger import EvidenceLedger


def _get_imports_from_file(file_path: Path) -> Set[str]:
    """Parse a python file with AST and extract imported module paths."""
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    imported_modules: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)
    return imported_modules


def _collect_package_imports(package_dir: Path) -> Dict[str, Set[str]]:
    """Collect all imported modules per file in a package directory."""
    result: Dict[str, Set[str]] = {}
    for py_file in package_dir.rglob("*.py"):
        if py_file.name == "__pycache__":
            continue
        rel_path = str(py_file.relative_to(package_dir.parent.parent))
        result[rel_path] = _get_imports_from_file(py_file)
    return result


class TestGlobalArchitectureBoundaries:
    """Test AST-level isolation invariants of the Global Dependency Matrix."""

    SRC_ROOT = (
        Path(__file__).resolve().parent.parent.parent / "src" / "study_engine"
    )

    def test_s3_retrieval_isolation(self) -> None:
        """S3 (retrieval) cannot import S4, S5, session, state, or LLM."""
        retrieval_dir = self.SRC_ROOT / "retrieval"
        imports_per_file = _collect_package_imports(retrieval_dir)

        forbidden_prefixes = (
            "study_engine.generation",
            "study_engine.audit",
            "study_engine.session",
            "study_engine.state",
            "study_engine.llm",
        )

        for file_path, imported_mods in imports_per_file.items():
            for mod in imported_mods:
                for forbidden in forbidden_prefixes:
                    assert not mod.startswith(forbidden), (
                        f"Architecture violation in '{file_path}': "
                        f"S3 Retrieval is forbidden from importing '{mod}'."
                    )

    def test_s4_generation_audit_isolation(self) -> None:
        """S4 cannot import state, session, or curriculum."""
        gen_dir = self.SRC_ROOT / "generation"
        audit_dir = self.SRC_ROOT / "audit"
        imports_per_file = {
            **_collect_package_imports(gen_dir),
            **_collect_package_imports(audit_dir),
        }

        forbidden_prefixes = (
            "study_engine.state",
            "study_engine.session",
            "study_engine.curriculum",
            "study_engine.roadmap",
        )

        for file_path, imported_mods in imports_per_file.items():
            for mod in imported_mods:
                for forbidden in forbidden_prefixes:
                    assert not mod.startswith(forbidden), (
                        f"Architecture violation in '{file_path}': "
                        f"S4 is forbidden from importing '{mod}'."
                    )

    def test_s5_1_roadmap_isolation(self) -> None:
        """S5.1 cannot import state, generation, retrieval, or session."""
        roadmap_dir = self.SRC_ROOT / "roadmap"
        imports_per_file = _collect_package_imports(roadmap_dir)

        forbidden_prefixes = (
            "study_engine.state",
            "study_engine.generation",
            "study_engine.retrieval",
            "study_engine.session",
            "study_engine.audit",
        )

        for file_path, imported_mods in imports_per_file.items():
            for mod in imported_mods:
                for forbidden in forbidden_prefixes:
                    assert not mod.startswith(forbidden), (
                        f"Architecture violation in '{file_path}': "
                        f"S5.1 is forbidden from importing '{mod}'."
                    )

    def test_s5_2_state_isolation(self) -> None:
        """S5.2 cannot import generation, retrieval, session, or llm."""
        state_dir = self.SRC_ROOT / "state"
        imports_per_file = _collect_package_imports(state_dir)

        forbidden_prefixes = (
            "study_engine.generation",
            "study_engine.retrieval",
            "study_engine.session",
            "study_engine.llm",
            "study_engine.audit",
        )

        for file_path, imported_mods in imports_per_file.items():
            for mod in imported_mods:
                for forbidden in forbidden_prefixes:
                    assert not mod.startswith(forbidden), (
                        f"Architecture violation in '{file_path}': "
                        f"S5.2 State is forbidden from importing '{mod}'."
                    )

    def test_s5_4_curriculum_contracts_purity(self) -> None:
        """S5.4 cannot import state.ledger, session, or engines."""
        curriculum_dir = self.SRC_ROOT / "curriculum"
        imports_per_file = _collect_package_imports(curriculum_dir)

        forbidden_prefixes = (
            "study_engine.state.ledger",
            "study_engine.session",
            "study_engine.generation",
            "study_engine.retrieval",
            "study_engine.audit",
            "study_engine.llm",
        )

        for file_path, imported_mods in imports_per_file.items():
            for mod in imported_mods:
                for forbidden in forbidden_prefixes:
                    assert not mod.startswith(forbidden), (
                        f"Architecture violation in '{file_path}': "
                        f"S5.4 Curriculum is forbidden from importing '{mod}'."
                    )

    def test_s6_execution_isolation(self) -> None:
        """S6 execution cannot import state, curriculum, llm, or storage."""
        execution_dir = self.SRC_ROOT / "execution"
        imports_per_file = _collect_package_imports(execution_dir)

        forbidden_prefixes = (
            "study_engine.state",
            "study_engine.curriculum",
            "study_engine.generation",
            "study_engine.retrieval",
            "study_engine.audit",
            "study_engine.llm",
            "study_engine.storage",
            "study_engine.session",
        )

        for file_path, imported_mods in imports_per_file.items():
            for mod in imported_mods:
                for forbidden in forbidden_prefixes:
                    assert not mod.startswith(forbidden), (
                        f"Architecture violation in '{file_path}': "
                        f"S6 Execution is forbidden from importing '{mod}'."
                    )

    def test_s9_assessment_isolation(self) -> None:
        """S9 assessment cannot import state, session, llm, or storage."""
        assessment_dir = self.SRC_ROOT / "assessment"
        imports_per_file = _collect_package_imports(assessment_dir)

        forbidden_prefixes = (
            "study_engine.state",
            "study_engine.session",
            "study_engine.llm",
            "study_engine.storage",
            "study_engine.execution.adapter_python",
            "study_engine.execution.process_manager",
        )

        for file_path, imported_mods in imports_per_file.items():
            for mod in imported_mods:
                for forbidden in forbidden_prefixes:
                    assert not mod.startswith(forbidden), (
                        f"Architecture violation in '{file_path}': "
                        f"S9 Assessment is forbidden from importing '{mod}'."
                    )


class TestEpistemologicalAuthorityGuards:
    """Test runtime enforcement of single sovereign authorities per stage."""

    def test_authorized_emissions_succeed(self) -> None:
        """Legitimate authorities can emit their designated stages."""
        validate_epistemological_authority(
            stage=EpistemologicalStage.OBSERVATION,
            authority=EpistemologicalAuthority.EXECUTION_PLANE,
        )
        validate_epistemological_authority(
            stage=EpistemologicalStage.OBSERVATION,
            authority=EpistemologicalAuthority.ORAL_DEFENSE,
        )
        validate_epistemological_authority(
            stage=EpistemologicalStage.ASSESSMENT_RESULT,
            authority=EpistemologicalAuthority.ASSESSMENT_ENGINE,
        )
        validate_epistemological_authority(
            stage=EpistemologicalStage.EVIDENCE_RECORD,
            authority=EpistemologicalAuthority.EVIDENCE_POLICY,
        )
        validate_epistemological_authority(
            stage=EpistemologicalStage.GATEWAY_VERDICT,
            authority=EpistemologicalAuthority.GATEWAY_DECISION_AUTHORITY,
        )
        validate_epistemological_authority(
            stage=EpistemologicalStage.STUDENT_STATE,
            authority=EpistemologicalAuthority.STATE_ENGINE,
        )

    def test_unauthorized_emissions_fail_closed(self) -> None:
        """Unauthorized attempts to bypass authorities raise errors."""
        # S6 Execution Plane cannot emit GatewayVerdict
        with pytest.raises(EpistemologicalAuthorityViolationError):
            validate_epistemological_authority(
                stage=EpistemologicalStage.GATEWAY_VERDICT,
                authority=EpistemologicalAuthority.EXECUTION_PLANE,
            )

        # S6 Execution Plane cannot emit EvidenceRecord
        with pytest.raises(EpistemologicalAuthorityViolationError):
            validate_epistemological_authority(
                stage=EpistemologicalStage.EVIDENCE_RECORD,
                authority=EpistemologicalAuthority.EXECUTION_PLANE,
            )

        # S9 Assessment Engine cannot emit EvidenceRecord directly
        with pytest.raises(EpistemologicalAuthorityViolationError):
            validate_epistemological_authority(
                stage=EpistemologicalStage.EVIDENCE_RECORD,
                authority=EpistemologicalAuthority.ASSESSMENT_ENGINE,
            )

        # S5.2.A Evidence Policy cannot emit GatewayVerdict
        with pytest.raises(EpistemologicalAuthorityViolationError):
            validate_epistemological_authority(
                stage=EpistemologicalStage.GATEWAY_VERDICT,
                authority=EpistemologicalAuthority.EVIDENCE_POLICY,
            )

        # S5.3 Coordinator cannot emit StudentState
        with pytest.raises(EpistemologicalAuthorityViolationError):
            validate_epistemological_authority(
                stage=EpistemologicalStage.STUDENT_STATE,
                authority=EpistemologicalAuthority.EXECUTION_PLANE,
            )


class TestLedgerTypeEnforcementGuard:
    """Test runtime type enforcement preventing OperationalEvents in Ledger."""

    def test_ledger_rejects_operational_event(self) -> None:
        """OperationalEvent passed to append raises TypeError."""
        ledger = EvidenceLedger()
        event = OperationalEvent(
            event_id="evt-100",
            correlation_id="corr-1",
            causation_id="cause-1",
            event_type="sandbox.executed",
            component="S6_EXECUTION_PLANE",
            payload={"exit_code": 0},
        )

        with pytest.raises(
            TypeError, match="Only EvidenceRecord can be committed"
        ):
            ledger.append_record(event)  # type: ignore[arg-type]

        with pytest.raises(
            TypeError, match="Only EvidenceRecord can be committed"
        ):
            ledger.append_evidence(event)  # type: ignore[arg-type]

    def test_ledger_rejects_dict_or_generic_object(self) -> None:
        """Arbitrary dictionaries or objects raise TypeError on append."""
        ledger = EvidenceLedger()
        with pytest.raises(TypeError):
            fake_dict = {"record_id": "fake"}
            ledger.append_record(fake_dict)  # type: ignore[arg-type]

        with pytest.raises(TypeError):
            fake_str = "not_an_evidence_record"
            ledger.append_evidence(fake_str)  # type: ignore[arg-type]


class TestExecutionProvenanceSpine:
    """Test cryptographic lineage graph anchor and verification predicates."""

    VALID_SHA256_A = "a" * 64
    VALID_SHA256_B = "b" * 64
    VALID_SHA256_C = "c" * 64
    VALID_SHA256_D = "d" * 64
    VALID_SHA256_E = "e" * 64

    def _build_valid_spine(self) -> ExecutionProvenanceSpine:
        return ExecutionProvenanceSpine(
            spine_id="spine-001",
            identity=SpineIdentity(
                student_id="student-alpha",
                session_id="session-1",
                attempt_id="attempt-1",
            ),
            curriculum=SpineCurriculum(
                curriculum_node_id="SEC-01",
                roadmap_revision_id=self.VALID_SHA256_A,
                policy_revision_id=self.VALID_SHA256_B,
                gateway_id="G1.1",
                gateway_revision_id=self.VALID_SHA256_C,
            ),
            assessment=SpineAssessment(
                rubric_id="rubric-sec-01",
                rubric_revision_id=self.VALID_SHA256_D,
                task_id="task-p1",
                task_revision_id=self.VALID_SHA256_E,
                hoare_contract_id="hoare-sec-01",
                assessment_result_id="asmt-res-1",
                evidence_record_id="ev-rec-1",
                evaluator_version="1.0.0",
            ),
            execution=SpineExecution(
                observation_ids=("obs-1", "obs-2"),
                artifact_digests=(self.VALID_SHA256_A, self.VALID_SHA256_B),
                perturbation_id="pert-01",
            ),
            terminal_state=SpineTerminalState(
                ledger_cutoff_hash=self.VALID_SHA256_C,
                student_state_id="state-hash-99",
            ),
        )

    def test_complete_spine_lineage_verification_succeeds(self) -> None:
        """Complete valid spine passes deterministic lineage verification."""
        spine = self._build_valid_spine()
        assert verify_spine_lineage(
            spine=spine,
            expected_artifact_digests=(
                self.VALID_SHA256_A,
                self.VALID_SHA256_B,
            ),
            expected_ledger_cutoff_hash=self.VALID_SHA256_C,
            expected_student_state_id="state-hash-99",
        )

    def test_spine_tampered_artifact_rejected(self) -> None:
        """Tampered artifact digests fail verification immediately."""
        spine = self._build_valid_spine()
        with pytest.raises(
            LineageVerificationError, match="Artifact digest mismatch"
        ):
            verify_spine_lineage(
                spine=spine,
                expected_artifact_digests=(self.VALID_SHA256_C,),
            )

    def test_spine_missing_gateway_revision_rejected(self) -> None:
        """Referencing a gateway without revision ID raises error."""
        spine = ExecutionProvenanceSpine(
            spine_id="spine-002",
            identity=SpineIdentity(student_id="student-alpha"),
            curriculum=SpineCurriculum(
                curriculum_node_id="SEC-01",
                roadmap_revision_id=self.VALID_SHA256_A,
                policy_revision_id=self.VALID_SHA256_B,
                gateway_id="G1.1",
                gateway_revision_id=None,
            ),
            assessment=SpineAssessment(),
            execution=SpineExecution(),
            terminal_state=SpineTerminalState(),
        )
        with pytest.raises(
            LineageVerificationError, match="gateway_revision_id"
        ):
            verify_spine_lineage(spine)

    def test_spine_missing_task_revision_rejected(self) -> None:
        """Referencing a task without revision ID raises error."""
        spine = ExecutionProvenanceSpine(
            spine_id="spine-003",
            identity=SpineIdentity(student_id="student-alpha"),
            curriculum=SpineCurriculum(
                curriculum_node_id="SEC-01",
                roadmap_revision_id=self.VALID_SHA256_A,
                policy_revision_id=self.VALID_SHA256_B,
            ),
            assessment=SpineAssessment(
                task_id="task-01",
                task_revision_id=None,
            ),
            execution=SpineExecution(),
            terminal_state=SpineTerminalState(),
        )
        with pytest.raises(
            LineageVerificationError, match="task_revision_id"
        ):
            verify_spine_lineage(spine)

    def test_spine_ledger_hash_mismatch_rejected(self) -> None:
        """Ledger cutoff hash mismatch fails verification."""
        spine = self._build_valid_spine()
        with pytest.raises(
            LineageVerificationError, match="Ledger cutoff hash mismatch"
        ):
            verify_spine_lineage(
                spine=spine,
                expected_ledger_cutoff_hash="f" * 64,
            )

    def test_spine_student_state_mismatch_rejected(self) -> None:
        """Student state mismatch fails verification."""
        spine = self._build_valid_spine()
        with pytest.raises(
            LineageVerificationError, match="Student state ID mismatch"
        ):
            verify_spine_lineage(
                spine=spine,
                expected_student_state_id="wrong-state-id",
            )


class TestGatewayDecisionAuthorityContract:
    """Test GatewayDecisionAuthority compositional verdict evaluations."""

    def _sample_gateway_def(self) -> GatewayDefinition:
        criteria = GatewayVerdictCriteria(
            criteria_id="crit-g1",
            minimum_overall_level=PerformanceLevel.N3_COMPETENT,
        )
        return GatewayDefinition(
            gateway_id="G0.1",
            curriculum_node_id="N-01",
            title="Gateway 0.1 Assessment",
            format=GatewayFormat.INDIVIDUAL_PRACTICAL,
            rubric_id="rubric-01",
            verdict_criteria=criteria,
            practical_task_ids=("task-01",),
            perturbation_ids=("pert-01",),
            oral_defense_id="defense-01",
            required_evidence_outcomes=("outcome-01",),
        )

    def test_gateway_decision_authority_happy_path(self) -> None:
        """Authority produces passed verdict when all criteria satisfied."""
        gda = GatewayDecisionAuthority()
        gdef = self._sample_gateway_def()

        verdict = gda.evaluate_gateway(
            verdict_id="verdict-101",
            student_id="student-alpha",
            gateway_def=gdef,
            assessment_results=[{"passed": True, "details": "Score 100%"}],
            oral_defense_result={
                "passed": True,
                "details": "Defense accepted",
            },
            perturbation_results=[{"passed": True, "details": "Robust"}],
            evidence_eligibility={"eligible": True},
        )

        assert verdict.passed is True
        assert verdict.gateway_id == "G0.1"
        assert len(verdict.verdict_digest) == 64
        assert verdict.authority_id == "GATEWAY_DECISION_AUTHORITY"

    def test_gateway_decision_authority_practical_failure(self) -> None:
        """Practical assessment failure produces passed=False verdict."""
        gda = GatewayDecisionAuthority()
        gdef = self._sample_gateway_def()

        verdict = gda.evaluate_gateway(
            verdict_id="verdict-102",
            student_id="student-alpha",
            gateway_def=gdef,
            assessment_results=[{"passed": False, "details": "Rubric failed"}],
            oral_defense_result={"passed": True},
            perturbation_results=[{"passed": True}],
            evidence_eligibility={"eligible": True},
        )

        assert verdict.passed is False
        assert "Assessment 0 failed" in str(verdict.component_evaluations)

    def test_gateway_decision_authority_missing_oral_defense(self) -> None:
        """Missing oral defense when required produces passed=False."""
        gda = GatewayDecisionAuthority()
        gdef = self._sample_gateway_def()

        verdict = gda.evaluate_gateway(
            verdict_id="verdict-103",
            student_id="student-alpha",
            gateway_def=gdef,
            assessment_results=[{"passed": True}],
            oral_defense_result=None,
            perturbation_results=[{"passed": True}],
            evidence_eligibility={"eligible": True},
        )

        assert verdict.passed is False
        assert "Missing required oral defense" in str(
            verdict.component_evaluations
        )

    def test_gateway_decision_authority_missing_perturbation(self) -> None:
        """Missing perturbation evaluation produces passed=False."""
        gda = GatewayDecisionAuthority()
        gdef = self._sample_gateway_def()

        verdict = gda.evaluate_gateway(
            verdict_id="verdict-104",
            student_id="student-alpha",
            gateway_def=gdef,
            assessment_results=[{"passed": True}],
            oral_defense_result={"passed": True},
            perturbation_results=[],
            evidence_eligibility={"eligible": True},
        )

        assert verdict.passed is False
        assert "Missing required perturbation" in str(
            verdict.component_evaluations
        )

    def test_gateway_decision_authority_ineligible_evidence(self) -> None:
        """Ineligible historical evidence produces passed=False."""
        gda = GatewayDecisionAuthority()
        gdef = self._sample_gateway_def()

        verdict = gda.evaluate_gateway(
            verdict_id="verdict-105",
            student_id="student-alpha",
            gateway_def=gdef,
            assessment_results=[{"passed": True}],
            oral_defense_result={"passed": True},
            perturbation_results=[{"passed": True}],
            evidence_eligibility={
                "eligible": False,
                "reason": "Missing prerequisite mastery",
            },
        )

        assert verdict.passed is False
        assert "Historical evidence ineligible" in str(
            verdict.component_evaluations
        )


class TestS6ExecutionContracts:
    """Test S6 execution plane tier capabilities and resource bounds."""

    def test_tier_capabilities_matrix_completeness(self) -> None:
        """All 5 execution plane tiers define explicit capabilities."""
        for tier in ExecutionPlaneTier:
            assert tier in TIER_CAPABILITIES_MATRIX
            caps = TIER_CAPABILITIES_MATRIX[tier]
            assert "filesystem" in caps
            assert "network" in caps
            assert "subprocess" in caps
            assert "resource_limits" in caps
            assert "host_access" in caps
            assert "artifact_output" in caps

    def test_execution_policy_bounds(self) -> None:
        """Execution policy enforces valid bounds and rejects out-of-range."""
        policy = ExecutionPolicy()
        assert policy.max_output_bytes == 1_048_576
        assert policy.max_artifact_bytes == 52_428_800
        assert policy.max_artifact_count == 50
        assert policy.max_process_count == 10
        assert policy.max_file_count == 200
        assert policy.max_workspace_bytes == 104_857_600

        with pytest.raises(Exception):
            ExecutionPolicy(max_output_bytes=500)

    def test_tool_capability_schema(self) -> None:
        """Tool capability validates qualified capability naming."""
        cap = ToolCapability(
            capability_name="python.run_script",
            supported_tiers=(ExecutionPlaneTier.TIER_0,),
            required_parameters=("script_path",),
            produces_artifacts=True,
        )
        assert cap.capability_name == "python.run_script"
        assert cap.produces_artifacts is True

    def test_execution_observation_authority(self) -> None:
        """ExecutionObservation carries S6_EXECUTION_PLANE authority."""
        obs = ExecutionObservation(
            observation_id="obs-100",
            execution_id="exec-100",
            tool_name="python.run_script",
            raw_telemetry={"exit_code": 0},
            produced_artifact_digests=("a" * 64,),
        )
        assert obs.authority_id == "S6_EXECUTION_PLANE"
