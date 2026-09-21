"""Deterministic practical evaluator for Subsystem S9.1.

INVARIANTS:
1. Evaluates InstrumentalFacts against Task & Rubric specifications.
2. Derives EvaluativeFacts with explicit audit references to InstrumentalFacts.
3. Strict abstention: if required facts were truncated or omitted by limits,
   emits AssessmentStatus.INSUFFICIENT_OBSERVATION (never assumes N1).
4. Declarative rule execution: performance levels belong to the rubric,
   never hardcoded by the evaluator.
5. Zero execution capabilities: purely functional deterministic logic.
"""

from typing import List, Tuple

from study_engine.contracts.assessment import (
    AssessmentStatus,
    DimensionEvaluation,
    EvaluativeFact,
    EvaluativeFactType,
    InstrumentalFact,
    InstrumentalFactType,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.curriculum.rubric_contracts import (
    AssessmentRubric,
    RubricDimension,
)
from study_engine.curriculum.task_contracts import PracticalTaskSpecification


def _derive_evaluative_facts(
    task: PracticalTaskSpecification,
    instrumental_facts: Tuple[InstrumentalFact, ...],
    evaluator_id: str,
) -> Tuple[EvaluativeFact, ...]:
    """Derive formal EvaluativeFacts comparing facts to task specs."""
    eval_facts: List[EvaluativeFact] = []

    # 1. Exit code conformance
    exit_fact = next(
        (
            f
            for f in instrumental_facts
            if f.fact_type == InstrumentalFactType.PROCESS_EXIT_CODE
        ),
        None,
    )
    if exit_fact is not None:
        is_clean_exit = exit_fact.fact_value == "0"
        eval_facts.append(
            EvaluativeFact(
                fact_id=f"eval-exit-{task.task_id}",
                evaluator_id=evaluator_id,
                fact_type=EvaluativeFactType.EXIT_CODE_EXPECTED,
                fact_value=exit_fact.fact_value,
                satisfied=is_clean_exit,
                based_on_instrumental_fact_ids=(exit_fact.fact_id,),
                requirement_id="req-process-clean-exit",
                rationale=(
                    f"Process exit code {exit_fact.fact_value} "
                    f"{'matched' if is_clean_exit else 'did not match'} "
                    f"expected 0"
                ),
            )
        )

    # 2. Timing SLA conformance
    dur_fact = next(
        (
            f
            for f in instrumental_facts
            if f.fact_type == InstrumentalFactType.EXECUTION_DURATION_MS
        ),
        None,
    )
    if dur_fact is not None:
        max_ms = (
            float(task.time_limit_minutes * 60 * 1000)
            if task.time_limit_minutes
            else 60000.0  # 60s default SLA
        )
        duration = float(dur_fact.fact_value)
        within_sla = duration <= max_ms
        eval_facts.append(
            EvaluativeFact(
                fact_id=f"eval-timing-{task.task_id}",
                evaluator_id=evaluator_id,
                fact_type=EvaluativeFactType.DURATION_WITHIN_SLA,
                fact_value=f"{duration:.1f}ms <= {max_ms:.1f}ms",
                satisfied=within_sla,
                based_on_instrumental_fact_ids=(dur_fact.fact_id,),
                requirement_id="req-execution-sla",
                rationale=(
                    f"Execution duration {duration:.1f}ms was "
                    f"{'within' if within_sla else 'exceeded'} limit "
                    f"of {max_ms:.1f}ms"
                ),
            )
        )

    # 3. Artifact conformance
    size_facts = {
        f.fact_value.split(":")[0]: (f, int(f.fact_value.split(":")[1]))
        for f in instrumental_facts
        if f.fact_type == InstrumentalFactType.ARTIFACT_SIZE_BYTES
    }
    omitted_facts = {
        f.fact_value: f
        for f in instrumental_facts
        if f.fact_type == InstrumentalFactType.ARTIFACT_OMITTED_BY_LIMIT
    }
    absent_facts = {
        f.fact_value: f
        for f in instrumental_facts
        if f.fact_type == InstrumentalFactType.ARTIFACT_VERIFIED_ABSENT
    }

    for req in task.required_artifacts:
        target_path = req.requirement_id
        matching_size_entry = size_facts.get(target_path)

        if matching_size_entry is not None:
            size_fact, file_size = matching_size_entry
            size_ok = file_size >= req.min_size_bytes and (
                req.max_size_bytes is None or file_size <= req.max_size_bytes
            )
            eval_facts.append(
                EvaluativeFact(
                    fact_id=f"eval-art-{req.requirement_id}",
                    evaluator_id=evaluator_id,
                    fact_type=(
                        EvaluativeFactType.ARTIFACT_CONFORMS_TO_REQUIREMENT
                    ),
                    fact_value=f"size={file_size}, conformance={size_ok}",
                    satisfied=size_ok,
                    based_on_instrumental_fact_ids=(size_fact.fact_id,),
                    requirement_id=req.requirement_id,
                    rationale=(
                        f"Artifact '{target_path}' present ({file_size} B); "
                        f"boundaries [{req.min_size_bytes}, "
                        f"{req.max_size_bytes}] satisfied={size_ok}"
                    ),
                )
            )
        elif target_path in omitted_facts:
            omit_fact = omitted_facts[target_path]
            eval_facts.append(
                EvaluativeFact(
                    fact_id=f"eval-art-{req.requirement_id}",
                    evaluator_id=evaluator_id,
                    fact_type=(
                        EvaluativeFactType.ARTIFACT_CONFORMS_TO_REQUIREMENT
                    ),
                    fact_value="omitted_by_limits",
                    satisfied=False,
                    based_on_instrumental_fact_ids=(omit_fact.fact_id,),
                    requirement_id=req.requirement_id,
                    rationale=(
                        f"Artifact '{target_path}' could not be evaluated "
                        f"because collection limits were exceeded"
                    ),
                )
            )
        elif target_path in absent_facts:
            abs_fact = absent_facts[target_path]
            eval_facts.append(
                EvaluativeFact(
                    fact_id=f"eval-art-{req.requirement_id}",
                    evaluator_id=evaluator_id,
                    fact_type=(
                        EvaluativeFactType.ARTIFACT_CONFORMS_TO_REQUIREMENT
                    ),
                    fact_value="verified_absent",
                    satisfied=False,
                    based_on_instrumental_fact_ids=(abs_fact.fact_id,),
                    requirement_id=req.requirement_id,
                    rationale=(
                        f"Artifact '{target_path}' verified absent in "
                        f"workspace during exhaustive scan"
                    ),
                )
            )

    return tuple(eval_facts)


def _evaluate_dimension(
    dimension: RubricDimension,
    task: PracticalTaskSpecification,
    evaluative_facts: Tuple[EvaluativeFact, ...],
    instrumental_facts: Tuple[InstrumentalFact, ...],
) -> DimensionEvaluation:
    """Evaluate a single rubric dimension against facts and rubric criteria."""
    dim_id = dimension.dimension_id

    # Check if any required observation was omitted or truncated
    has_omitted_artifacts = any(
        f.fact_type == InstrumentalFactType.ARTIFACT_OMITTED_BY_LIMIT
        for f in instrumental_facts
    )
    is_stream_truncated = any(
        f.fact_type == InstrumentalFactType.STREAM_WAS_TRUNCATED
        and f.fact_value == "true"
        for f in instrumental_facts
    )

    # In Phase 0, if an expected artifact was omitted by collection limits,
    # the practical dimension is incomplete: abstain with INSUFFICIENT_OBS
    if has_omitted_artifacts and len(task.required_artifacts) > 0:
        return DimensionEvaluation(
            dimension_id=dim_id,
            status=AssessmentStatus.INSUFFICIENT_OBSERVATION,
            assigned_level=None,
            passed_minimum=None,
            is_critical=dimension.is_critical,
            evidence_evaluative_fact_ids=(),
            evaluator_rule_ids=("rule-abstain-omitted-artifacts",),
            evaluation_rationale=(
                f"Evaluation for dimension '{dim_id}' abstained: required "
                f"artifacts were omitted by engine limits."
            ),
        )

    # Gather evaluative facts relevant to this dimension
    relevant_eval_facts = [
        ef
        for ef in evaluative_facts
        if ef.fact_type
        in (
            EvaluativeFactType.EXIT_CODE_EXPECTED,
            EvaluativeFactType.ARTIFACT_CONFORMS_TO_REQUIREMENT,
            EvaluativeFactType.DURATION_WITHIN_SLA,
            EvaluativeFactType.STDOUT_MATCHES_PATTERN,
        )
    ]
    eval_fact_ids = tuple(ef.fact_id for ef in relevant_eval_facts)

    if not relevant_eval_facts:
        return DimensionEvaluation(
            dimension_id=dim_id,
            status=AssessmentStatus.NOT_APPLICABLE,
            assigned_level=None,
            passed_minimum=None,
            is_critical=dimension.is_critical,
            evidence_evaluative_fact_ids=(),
            evaluator_rule_ids=(),
            evaluation_rationale=(
                f"Dimension '{dim_id}' has no applicable facts."
            ),
        )

    # If dimension relies on stdout and stream was truncated, abstain
    if is_stream_truncated and any(
        ef.fact_type == EvaluativeFactType.STDOUT_MATCHES_PATTERN
        for ef in relevant_eval_facts
    ):
        return DimensionEvaluation(
            dimension_id=dim_id,
            status=AssessmentStatus.INSUFFICIENT_OBSERVATION,
            assigned_level=None,
            passed_minimum=None,
            is_critical=dimension.is_critical,
            evidence_evaluative_fact_ids=(),
            evaluator_rule_ids=("rule-abstain-stream-truncated",),
            evaluation_rationale=(
                f"Evaluation for dimension '{dim_id}' abstained: output "
                f"stream was truncated by engine limits."
            ),
        )

    # Check rule satisfaction
    all_satisfied = all(ef.satisfied for ef in relevant_eval_facts)
    rules_applied: List[str] = []

    if all_satisfied:
        rules_applied.append(f"rule-{dim_id}-criteria-met")
        assigned = dimension.minimum_level
        passed = True
        rationale = (
            f"All {len(relevant_eval_facts)} evaluative requirements "
            f"satisfied. Assigned level {assigned.name} according to rubric "
            f"minimum criteria."
        )
    else:
        failed_reqs = [
            ef.requirement_id for ef in relevant_eval_facts if not ef.satisfied
        ]
        rules_applied.append(f"rule-{dim_id}-criteria-failed")
        assigned = PerformanceLevel.N1_INSUFFICIENT
        passed = False
        rationale = (
            f"Requirements failed: {failed_reqs}. Assigned level "
            f"{assigned.name} due to unsatisfied rubric criteria."
        )

    return DimensionEvaluation(
        dimension_id=dim_id,
        status=AssessmentStatus.ASSESSED,
        assigned_level=assigned,
        passed_minimum=passed,
        is_critical=dimension.is_critical,
        evidence_evaluative_fact_ids=eval_fact_ids,
        evaluator_rule_ids=tuple(rules_applied),
        evaluation_rationale=rationale,
    )


def evaluate_practical_task(
    rubric: AssessmentRubric,
    task: PracticalTaskSpecification,
    instrumental_facts: Tuple[InstrumentalFact, ...],
    evaluator_id: str = "S9_DETERMINISTIC_EVALUATOR",
) -> Tuple[Tuple[EvaluativeFact, ...], Tuple[DimensionEvaluation, ...]]:
    """Evaluate practical task facts against rubric specifications."""
    evaluative_facts = _derive_evaluative_facts(
        task=task,
        instrumental_facts=instrumental_facts,
        evaluator_id=evaluator_id,
    )

    dimension_evaluations = tuple(
        _evaluate_dimension(
            dimension=dim,
            task=task,
            evaluative_facts=evaluative_facts,
            instrumental_facts=instrumental_facts,
        )
        for dim in rubric.dimensions
    )

    return evaluative_facts, dimension_evaluations
