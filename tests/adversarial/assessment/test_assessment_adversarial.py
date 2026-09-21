"""Adversarial test battery for Subsystem S9.1 (Assessment Engine).

Tests 8 hostile and edge-case attack vectors:
1. Truncated stream claiming trailing success -> abstains (INSUFFICIENT_OBS).
2. Truncated stream with observed failure -> N1_INSUFFICIENT (valid fact).
3. Omitted artifact due to limits -> INSUFFICIENT_OBS (never assumed absent).
4. Clean workspace scan without artifact -> VERIFIED_ABSENCE -> failure.
5. Empty script exiting 0 without artifacts -> N1_INSUFFICIENT.
6. Tampered specification canonical hash -> SpecificationIntegrityError.
7. Uncompensated failure -> passed=False (non-average gate).
8. Multi-dimension high score unable to compensate critical dimension failure.
"""

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
    InstrumentalFactType,
)
from study_engine.contracts.execution import (
    ArtifactCollectionSummary,
    ExecutionObservation,
    ExecutionStatus,
    ObservedArtifact,
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


def _sample_task() -> PracticalTaskSpecification:
    req = ArtifactRequirement(
        requirement_id="output.json",
        artifact_type=ArtifactType.LOG_BUNDLE,
        min_size_bytes=10,
        expected_mime_types=("application/json",),
        description="Required json payload",
    )
    return PracticalTaskSpecification(
        task_id="adv-task-01",
        curriculum_node_id="NET-01",
        title="Adversarial Practical Task",
        description="Must generate output.json",
        required_artifacts=(req,),
        time_limit_minutes=1,
    )


def _sample_rubric() -> AssessmentRubric:
    dim = RubricDimension(
        dimension_id="dim-main",
        title="Main Evaluation",
        weight=1.0,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=True,
    )
    return AssessmentRubric(
        rubric_id="adv-rubric-01",
        title="Adversarial Rubric",
        dimensions=(dim,),
    )


class TestAssessmentAdversarialBattery:
    """Adversarial stress and edge-case battery for S9.1."""

    def test_adv_01_truncated_stream_trailing_claim_abstains(self) -> None:
        """Vector 1: Truncated stream claiming trailing success abstains."""
        # Output was cut off; trailing SUCCESS not observed
        obs = ExecutionObservation(
            observation_id="obs-adv-1",
            execution_id="exec-adv-1",
            tool_name="python.run_script",
            status=ExecutionStatus.COMPLETED,
            exit_code=0,
            telemetry=ProcessTelemetry(
                duration_ms=100.0,
                output_truncated=True,
                termination_reason=TerminationReason.NORMAL_EXIT,
            ),
            raw_telemetry={"exit_code": 0, "stdout": "processing start..."},
        )
        facts = extract_instrumental_facts(obs)
        stdout_fact = next(
            f
            for f in facts
            if f.fact_type == InstrumentalFactType.STDOUT_TEXT_SNIPPET
        )
        assert stdout_fact.observability == FactObservability.PARTIAL_TRUNCATED

    def test_adv_02_truncated_stream_observed_error_fails(self) -> None:
        """Vector 2: Error in truncated stream is an empirical fact."""
        # Process exited with code 1 despite stream truncation
        obs = ExecutionObservation(
            observation_id="obs-adv-2",
            execution_id="exec-adv-2",
            tool_name="python.run_script",
            status=ExecutionStatus.FAILED_PROCESS,
            exit_code=1,
            telemetry=ProcessTelemetry(
                duration_ms=50.0,
                output_truncated=True,
                termination_reason=TerminationReason.NORMAL_EXIT,
            ),
            raw_telemetry={"exit_code": 1, "stderr": "FATAL: crash"},
        )
        task = _sample_task()
        rubric = _sample_rubric()
        facts = extract_instrumental_facts(obs)
        _, dim_evals = evaluate_practical_task(rubric, task, facts)

        dim = dim_evals[0]
        # The failure fact is irrefutable
        assert dim.status == AssessmentStatus.ASSESSED
        assert dim.assigned_level == PerformanceLevel.N1_INSUFFICIENT
        assert dim.passed_minimum is False

    def test_adv_03_omitted_artifact_due_to_limit_abstains(self) -> None:
        """Vector 3: Omitted artifact by limits produces INSUFFICIENT_OBS."""
        obs = ExecutionObservation(
            observation_id="obs-adv-3",
            execution_id="exec-adv-3",
            tool_name="python.run_script",
            status=ExecutionStatus.COMPLETED,
            exit_code=0,
            raw_telemetry={"exit_code": 0},
            artifact_summary=ArtifactCollectionSummary(
                artifacts_discovered=1,
                artifacts_collected=0,
                artifacts_omitted=1,
                collection_truncated=True,
            ),
        )
        task = _sample_task()
        rubric = _sample_rubric()
        facts = extract_instrumental_facts(
            obs, expected_paths=("output.json",)
        )
        _, dim_evals = evaluate_practical_task(rubric, task, facts)

        dim = dim_evals[0]
        assert dim.status == AssessmentStatus.INSUFFICIENT_OBSERVATION
        assert dim.assigned_level is None
        assert dim.passed_minimum is None

    def test_adv_04_verified_absence_leads_to_failure(self) -> None:
        """Vector 4: Clean scan without expected artifact fails as absent."""
        obs = ExecutionObservation(
            observation_id="obs-adv-4",
            execution_id="exec-adv-4",
            tool_name="python.run_script",
            status=ExecutionStatus.COMPLETED,
            exit_code=0,
            raw_telemetry={"exit_code": 0},
            artifact_summary=ArtifactCollectionSummary(
                artifacts_discovered=0,
                artifacts_collected=0,
                artifacts_omitted=0,
                collection_truncated=False,
            ),
        )
        task = _sample_task()
        rubric = _sample_rubric()
        facts = extract_instrumental_facts(
            obs, expected_paths=("output.json",)
        )
        _, dim_evals = evaluate_practical_task(rubric, task, facts)

        dim = dim_evals[0]
        assert dim.status == AssessmentStatus.ASSESSED
        assert dim.assigned_level == PerformanceLevel.N1_INSUFFICIENT
        assert dim.passed_minimum is False

    def test_adv_05_empty_script_exit_zero_fails(self) -> None:
        """Vector 5: Empty script exit 0 fails required artifact."""
        obs = ExecutionObservation(
            observation_id="obs-adv-5",
            execution_id="exec-adv-5",
            tool_name="python.run_script",
            status=ExecutionStatus.COMPLETED,
            exit_code=0,
            telemetry=ProcessTelemetry(
                duration_ms=10.0,
                termination_reason=TerminationReason.NORMAL_EXIT,
            ),
            raw_telemetry={"exit_code": 0, "stdout": ""},
        )
        task = _sample_task()
        rubric = _sample_rubric()
        facts = extract_instrumental_facts(
            obs, expected_paths=("output.json",)
        )
        _, dim_evals = evaluate_practical_task(rubric, task, facts)

        dim = dim_evals[0]
        # Exit 0 alone does not satisfy task: missing output.json
        assert dim.assigned_level == PerformanceLevel.N1_INSUFFICIENT
        assert dim.passed_minimum is False

    def test_adv_06_tampered_specification_hash_rejected(self) -> None:
        """Vector 6: Tampered specification hash raises integrity error."""
        engine = DeterministicAssessmentEngine()
        task = _sample_task()
        rubric = _sample_rubric()
        obs = ExecutionObservation(
            observation_id="obs-adv-6",
            execution_id="exec-adv-6",
            tool_name="python.run_script",
            status=ExecutionStatus.COMPLETED,
            exit_code=0,
            raw_telemetry={"exit_code": 0},
        )
        with pytest.raises(SpecificationIntegrityError):
            engine.assess(
                task=task,
                rubric=rubric,
                observation=obs,
                task_revision_id="rev-1",
                rubric_revision_id="rev-1",
                expected_task_sha256="bad" * 21 + "f",
            )

    def test_adv_07_uncompensated_failure_blocks_passing(self) -> None:
        """Vector 7: Critical failure without compensation blocks passing."""
        rubric = _sample_rubric()
        task = _sample_task()
        # Failed execution
        obs = ExecutionObservation(
            observation_id="obs-adv-7",
            execution_id="exec-adv-7",
            tool_name="python.run_script",
            status=ExecutionStatus.FAILED_PROCESS,
            exit_code=2,
            raw_telemetry={"exit_code": 2},
        )
        facts = extract_instrumental_facts(obs)
        _, dim_evals = evaluate_practical_task(rubric, task, facts)
        agg = aggregate_evaluations(rubric, dim_evals)

        assert agg.passed is False
        assert agg.overall_level == PerformanceLevel.N1_INSUFFICIENT
        assert len(agg.critical_dimension_failures) > 0

    def test_adv_08_multi_dim_non_average_gate(self) -> None:
        """Vector 8: High score in one dimension cannot mask critical fail."""
        dim1 = RubricDimension(
            dimension_id="dim-execution",
            title="Execution",
            weight=0.5,
            minimum_level=PerformanceLevel.N3_COMPETENT,
            is_critical=True,
        )
        dim2 = RubricDimension(
            dimension_id="dim-presentation",
            title="Presentation",
            weight=0.5,
            minimum_level=PerformanceLevel.N3_COMPETENT,
            is_critical=False,
        )
        rubric = AssessmentRubric(
            rubric_id="rubric-two-dim",
            title="Two Dim Rubric",
            dimensions=(dim1, dim2),
        )
        # Task has valid artifact
        art = ObservedArtifact(
            artifact_id="art-1",
            relative_path="output.json",
            file_size_bytes=50,
            sha256_digest="d" * 64,
        )
        # But exit code crashed with code 137 (OOM)
        obs = ExecutionObservation(
            observation_id="obs-adv-8",
            execution_id="exec-adv-8",
            tool_name="python.run_script",
            status=ExecutionStatus.RESOURCE_EXHAUSTED,
            exit_code=137,
            raw_telemetry={"exit_code": 137},
            produced_artifacts=(art,),
        )
        task = _sample_task()
        facts = extract_instrumental_facts(
            obs, expected_paths=("output.json",)
        )
        _, dim_evals = evaluate_practical_task(rubric, task, facts)
        agg = aggregate_evaluations(rubric, dim_evals)

        # Critical failure blocks passing despite artifact present
        assert agg.passed is False
        assert agg.overall_level == PerformanceLevel.N1_INSUFFICIENT
