"""Deterministic Assessment Engine service facade for Subsystem S9.1.

INVARIANTS:
1. Sovereign authority: EpistemologicalAuthority.ASSESSMENT_ENGINE.
2. Cryptographic binding: validates canonical SHA-256 of task & rubric.
3. Complete backward provenance lineage: connects Observation -> Facts ->
   Evaluations -> Aggregation -> AssessmentResult.
4. Zero execution, zero LLM, zero ledger mutations.
"""

from datetime import datetime, timezone
import uuid

from study_engine.assessment.aggregator import aggregate_evaluations
from study_engine.assessment.evaluator_deterministic import (
    evaluate_practical_task,
)
from study_engine.assessment.fact_extractor import extract_instrumental_facts
from study_engine.contracts.assessment import (
    AssessmentResult,
    ObservationReference,
    SpecificationReference,
    compute_canonical_sha256,
)
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.contracts.execution import ExecutionObservation
from study_engine.curriculum.rubric_contracts import AssessmentRubric
from study_engine.curriculum.task_contracts import PracticalTaskSpecification


class SpecificationIntegrityError(Exception):
    """Raised when specification canonical SHA-256 fails verification."""

    pass


class DeterministicAssessmentEngine:
    """S9.1 deterministic evaluator for Phase 0 practical tasks."""

    def __init__(
        self,
        evaluator_id: str = "S9_DETERMINISTIC_PRACTICAL_EVALUATOR",
        evaluator_version: str = "1.0.0",
    ) -> None:
        self.evaluator_id = evaluator_id
        self.evaluator_version = evaluator_version

    def assess(
        self,
        task: PracticalTaskSpecification,
        rubric: AssessmentRubric,
        observation: ExecutionObservation,
        task_revision_id: str,
        rubric_revision_id: str,
        expected_task_sha256: str | None = None,
        expected_rubric_sha256: str | None = None,
    ) -> AssessmentResult:
        """Perform deterministic assessment of an execution observation."""
        # 1. Cryptographic specification verification
        actual_task_sha = compute_canonical_sha256(task)
        if expected_task_sha256 and actual_task_sha != expected_task_sha256:
            raise SpecificationIntegrityError(
                f"Task specification SHA-256 mismatch: expected "
                f"'{expected_task_sha256}', computed '{actual_task_sha}'"
            )

        actual_rubric_sha = compute_canonical_sha256(rubric)
        if (
            expected_rubric_sha256
            and actual_rubric_sha != expected_rubric_sha256
        ):
            raise SpecificationIntegrityError(
                f"Rubric specification SHA-256 mismatch: expected "
                f"'{expected_rubric_sha256}', computed '{actual_rubric_sha}'"
            )

        task_ref = SpecificationReference(
            specification_id=task.task_id,
            revision_id=task_revision_id,
            specification_sha256=actual_task_sha,
        )
        rubric_ref = SpecificationReference(
            specification_id=rubric.rubric_id,
            revision_id=rubric_revision_id,
            specification_sha256=actual_rubric_sha,
        )

        # 2. Cryptographic observation reference
        obs_ref = ObservationReference(
            observation_id=observation.observation_id,
            execution_id=observation.execution_id,
            effective_script_sha256=(
                observation.effective_script_sha256 or ("0" * 64)
            ),
            observation_sha256=compute_canonical_sha256(observation),
        )

        # 3. Extract instrumental facts
        expected_paths = tuple(
            req.requirement_id for req in task.required_artifacts
        )
        instrumental_facts = extract_instrumental_facts(
            observation=observation,
            expected_paths=expected_paths,
        )

        # 4. Evaluate practical task -> EvaluativeFacts & DimensionEvaluations
        evaluative_facts, dimension_evaluations = evaluate_practical_task(
            rubric=rubric,
            task=task,
            instrumental_facts=instrumental_facts,
            evaluator_id=self.evaluator_id,
        )

        # 5. Non-average policy aggregation
        aggregation = aggregate_evaluations(
            rubric=rubric,
            dimension_evaluations=dimension_evaluations,
        )

        # 6. Assemble AssessmentResult
        asmt_id = f"asmt-{uuid.uuid4().hex[:12]}"
        interim_result = AssessmentResult(
            assessment_id=asmt_id,
            task=task_ref,
            rubric=rubric_ref,
            observations=(obs_ref,),
            instrumental_facts=instrumental_facts,
            evaluative_facts=evaluative_facts,
            dimension_evaluations=dimension_evaluations,
            aggregation=aggregation,
            evaluator_id=self.evaluator_id,
            evaluator_version=self.evaluator_version,
            assessed_at=datetime.now(timezone.utc),
            authority_id=EpistemologicalAuthority.ASSESSMENT_ENGINE.value,
        )

        # 7. Compute assessment digest
        digest = compute_canonical_sha256(interim_result)
        final_result = interim_result.model_copy(
            update={"assessment_digest": digest}
        )

        return final_result
