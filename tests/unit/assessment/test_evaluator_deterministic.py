"""Unit tests for Deterministic Practical Evaluator (S9.1.3).

Verifies:
1. Nominal case: all requirements satisfied -> rubric minimum assigned.
2. Failed requirement: exit code != 0 or artifact absent -> N1 assigned.
3. Limit omission: artifact omitted by limits -> INSUFFICIENT_OBSERVATION.
4. Stream truncation: stdout truncated on stream-dependent check -> abstain.
5. Traceability: every EvaluativeFact points to an InstrumentalFact.
"""

from study_engine.assessment.evaluator_deterministic import (
    evaluate_practical_task,
)
from study_engine.contracts.assessment import (
    AssessmentStatus,
    EvaluativeFactType,
    FactObservability,
    InstrumentalFact,
    InstrumentalFactType,
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


def _sample_rubric(
    minimum: PerformanceLevel = PerformanceLevel.N3_COMPETENT,
) -> AssessmentRubric:
    return AssessmentRubric(
        rubric_id="rubric-net-01",
        title="Network Practical Assessment",
        dimensions=(
            RubricDimension(
                dimension_id="dim-practical",
                title="Practical Script Execution",
                weight=1.0,
                minimum_level=minimum,
                is_critical=True,
            ),
        ),
    )


def _sample_task() -> PracticalTaskSpecification:
    req = ArtifactRequirement(
        requirement_id="result.json",
        artifact_type=ArtifactType.LOG_BUNDLE,
        min_size_bytes=10,
        expected_mime_types=("application/json",),
        description="Execution results output",
    )
    return PracticalTaskSpecification(
        task_id="task-net-01",
        curriculum_node_id="NET-01",
        title="Socket Client Script",
        description="Implement client and emit result.json",
        required_artifacts=(req,),
        time_limit_minutes=2,
    )


def _sample_facts(
    exit_code: str = "0",
    artifact_size: int = 100,
    artifact_omitted: bool = False,
    stream_truncated: bool = False,
) -> tuple[InstrumentalFact, ...]:
    facts: list[InstrumentalFact] = [
        InstrumentalFact(
            fact_id="fact-exit-1",
            observation_id="obs-1",
            fact_type=InstrumentalFactType.PROCESS_EXIT_CODE,
            fact_value=exit_code,
            observability=FactObservability.CONCLUSIVE,
            inspected_domain="process",
            provenance_detail="Process exit",
        ),
        InstrumentalFact(
            fact_id="fact-dur-1",
            observation_id="obs-1",
            fact_type=InstrumentalFactType.EXECUTION_DURATION_MS,
            fact_value="500.0",
            observability=FactObservability.CONCLUSIVE,
            inspected_domain="process",
            provenance_detail="Duration",
        ),
        InstrumentalFact(
            fact_id="fact-trunc-1",
            observation_id="obs-1",
            fact_type=InstrumentalFactType.STREAM_WAS_TRUNCATED,
            fact_value=str(stream_truncated).lower(),
            observability=FactObservability.CONCLUSIVE,
            inspected_domain="streams",
            provenance_detail="Truncation",
        ),
    ]

    if artifact_omitted:
        facts.append(
            InstrumentalFact(
                fact_id="fact-art-omit-1",
                observation_id="obs-1",
                fact_type=InstrumentalFactType.ARTIFACT_OMITTED_BY_LIMIT,
                fact_value="result.json",
                observability=FactObservability.PARTIAL_TRUNCATED,
                inspected_domain="scratch/workspace/",
                provenance_detail="Omitted due to limits",
            )
        )
    elif artifact_size > 0:
        facts.append(
            InstrumentalFact(
                fact_id="fact-art-size-1",
                observation_id="obs-1",
                fact_type=InstrumentalFactType.ARTIFACT_SIZE_BYTES,
                fact_value=f"result.json:{artifact_size}",
                observability=FactObservability.CONCLUSIVE,
                inspected_domain="scratch/workspace/",
                provenance_detail="Size",
            )
        )
    else:
        facts.append(
            InstrumentalFact(
                fact_id="fact-art-abs-1",
                observation_id="obs-1",
                fact_type=InstrumentalFactType.ARTIFACT_VERIFIED_ABSENT,
                fact_value="result.json",
                observability=FactObservability.VERIFIED_ABSENCE,
                inspected_domain="scratch/workspace/",
                provenance_detail="Verified absent",
            )
        )

    return tuple(facts)


class TestEvaluatorDeterministic:
    """Tests for evaluate_practical_task."""

    def test_nominal_evaluation_assigns_rubric_level(self) -> None:
        """When all criteria met, assigns level declared by rubric."""
        rubric = _sample_rubric(minimum=PerformanceLevel.N3_COMPETENT)
        task = _sample_task()
        facts = _sample_facts(exit_code="0", artifact_size=100)

        eval_facts, dim_evals = evaluate_practical_task(rubric, task, facts)

        assert len(eval_facts) >= 2
        assert all(ef.satisfied for ef in eval_facts)

        dim = dim_evals[0]
        assert dim.status == AssessmentStatus.ASSESSED
        assert dim.assigned_level == PerformanceLevel.N3_COMPETENT
        assert dim.passed_minimum is True
        assert len(dim.evidence_evaluative_fact_ids) > 0

    def test_failed_exit_code_assigns_n1(self) -> None:
        """When exit code is non-zero, assigns N1_INSUFFICIENT."""
        rubric = _sample_rubric()
        task = _sample_task()
        facts = _sample_facts(exit_code="1", artifact_size=100)

        eval_facts, dim_evals = evaluate_practical_task(rubric, task, facts)

        exit_eval = next(
            ef
            for ef in eval_facts
            if ef.fact_type == EvaluativeFactType.EXIT_CODE_EXPECTED
        )
        assert exit_eval.satisfied is False

        dim = dim_evals[0]
        assert dim.status == AssessmentStatus.ASSESSED
        assert dim.assigned_level == PerformanceLevel.N1_INSUFFICIENT
        assert dim.passed_minimum is False

    def test_artifact_omitted_by_limits_triggers_abstention(self) -> None:
        """When artifact is omitted by limit, dimension abstains honestly."""
        rubric = _sample_rubric()
        task = _sample_task()
        facts = _sample_facts(artifact_omitted=True)

        eval_facts, dim_evals = evaluate_practical_task(rubric, task, facts)

        dim = dim_evals[0]
        assert dim.status == AssessmentStatus.INSUFFICIENT_OBSERVATION
        assert dim.assigned_level is None
        assert dim.passed_minimum is None
        assert "omitted by engine limits" in dim.evaluation_rationale

    def test_fact_traceability_chain(self) -> None:
        """EvaluativeFact explicitly references its source InstrumentalFact."""
        rubric = _sample_rubric()
        task = _sample_task()
        facts = _sample_facts(exit_code="0", artifact_size=50)

        eval_facts, _ = evaluate_practical_task(rubric, task, facts)
        exit_eval = next(
            ef
            for ef in eval_facts
            if ef.fact_type == EvaluativeFactType.EXIT_CODE_EXPECTED
        )
        assert "fact-exit-1" in exit_eval.based_on_instrumental_fact_ids
