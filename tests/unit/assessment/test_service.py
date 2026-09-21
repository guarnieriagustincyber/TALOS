"""Unit tests for DeterministicAssessmentEngine service (S9.1.5).

Verifies:
1. Full end-to-end execution of the assessment pipeline.
2. Specification hash mismatch detection and fail-closed integrity error.
3. Cryptographic backward lineage anchor verification across all entities.
4. Epistemological authority validation on emitted AssessmentResult.
"""

import pytest

from study_engine.assessment.service import (
    DeterministicAssessmentEngine,
    SpecificationIntegrityError,
)
from study_engine.contracts.assessment import (
    AssessmentStatus,
    compute_canonical_sha256,
)
from study_engine.contracts.epistemology import EpistemologicalAuthority
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
        requirement_id="client.log",
        artifact_type=ArtifactType.LOG_BUNDLE,
        min_size_bytes=5,
        expected_mime_types=("text/plain",),
        description="Client communication log",
    )
    return PracticalTaskSpecification(
        task_id="task-py-01",
        curriculum_node_id="NET-01",
        title="Python Socket Task",
        description="Connect and log",
        required_artifacts=(req,),
        time_limit_minutes=1,
    )


def _sample_rubric() -> AssessmentRubric:
    return AssessmentRubric(
        rubric_id="rubric-py-01",
        title="Socket Script Rubric",
        dimensions=(
            RubricDimension(
                dimension_id="dim-execution",
                title="Execution & Output",
                weight=1.0,
                minimum_level=PerformanceLevel.N3_COMPETENT,
                is_critical=True,
            ),
        ),
    )


def _sample_observation(exit_code: int = 0) -> ExecutionObservation:
    art = ObservedArtifact(
        artifact_id="art-log-01",
        relative_path="client.log",
        file_size_bytes=25,
        sha256_digest="f" * 64,
    )
    return ExecutionObservation(
        observation_id="obs-svc-001",
        execution_id="exec-svc-001",
        tool_name="python.run_script",
        status=ExecutionStatus.COMPLETED,
        exit_code=exit_code,
        telemetry=ProcessTelemetry(
            duration_ms=250.0,
            termination_reason=TerminationReason.NORMAL_EXIT,
        ),
        raw_telemetry={"exit_code": exit_code, "duration_ms": 250.0},
        produced_artifacts=(art,),
        artifact_summary=ArtifactCollectionSummary(
            artifacts_discovered=1,
            artifacts_collected=1,
            artifacts_omitted=0,
            collection_truncated=False,
        ),
    )


class TestDeterministicAssessmentEngine:
    """Test suite for DeterministicAssessmentEngine."""

    def test_nominal_assessment_pipeline(self) -> None:
        """Full pipeline executes and generates sealed AssessmentResult."""
        engine = DeterministicAssessmentEngine()
        task = _sample_task()
        rubric = _sample_rubric()
        obs = _sample_observation(exit_code=0)

        result = engine.assess(
            task=task,
            rubric=rubric,
            observation=obs,
            task_revision_id="rev-task-01",
            rubric_revision_id="rev-rubric-01",
        )

        assert result.authority_id == (
            EpistemologicalAuthority.ASSESSMENT_ENGINE.value
        )
        assert result.aggregation.passed is True
        assert (
            result.aggregation.overall_level == PerformanceLevel.N3_COMPETENT
        )
        assert len(result.assessment_digest) == 64
        assert len(result.instrumental_facts) > 0
        assert len(result.evaluative_facts) > 0
        assert result.dimension_evaluations[0].status == (
            AssessmentStatus.ASSESSED
        )

    def test_specification_hash_mismatch_rejected(self) -> None:
        """Mismatch between expected hash and computed spec hash fails."""
        engine = DeterministicAssessmentEngine()
        task = _sample_task()
        rubric = _sample_rubric()
        obs = _sample_observation()

        with pytest.raises(
            SpecificationIntegrityError, match="Task specification SHA-256"
        ):
            engine.assess(
                task=task,
                rubric=rubric,
                observation=obs,
                task_revision_id="rev-1",
                rubric_revision_id="rev-1",
                expected_task_sha256="0" * 64,
            )

    def test_full_backward_provenance_lineage(self) -> None:
        """Lineage chain is verifiable from result to all inputs."""
        engine = DeterministicAssessmentEngine()
        task = _sample_task()
        rubric = _sample_rubric()
        obs = _sample_observation()

        task_sha = compute_canonical_sha256(task)
        rubric_sha = compute_canonical_sha256(rubric)

        result = engine.assess(
            task=task,
            rubric=rubric,
            observation=obs,
            task_revision_id="rev-task-02",
            rubric_revision_id="rev-rubric-02",
            expected_task_sha256=task_sha,
            expected_rubric_sha256=rubric_sha,
        )

        # 1. Specification references
        assert result.task.specification_sha256 == task_sha
        assert result.rubric.specification_sha256 == rubric_sha

        # 2. Observation reference
        assert result.observations[0].observation_id == obs.observation_id

        # 3. Facts linkage
        eval_fact = result.evaluative_facts[0]
        assert len(eval_fact.based_on_instrumental_fact_ids) > 0
        inst_fact_ids = {f.fact_id for f in result.instrumental_facts}
        for parent_id in eval_fact.based_on_instrumental_fact_ids:
            assert parent_id in inst_fact_ids

        # 4. Dimension evaluation linkage
        dim_eval = result.dimension_evaluations[0]
        eval_fact_ids = {ef.fact_id for ef in result.evaluative_facts}
        for parent_ef_id in dim_eval.evidence_evaluative_fact_ids:
            assert parent_ef_id in eval_fact_ids
