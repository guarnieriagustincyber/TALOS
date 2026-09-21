"""Non-average policy aggregator for Subsystem S9.1.

INVARIANTS:
1. S5.4 Non-Average Rule: Critical dimensions cannot be compensated by
   higher scores in non-critical dimensions unless explicitly authorized by
   a declarative CompensationRule.
2. Honest Abstention Semantics: passed=False with insufficient_dimensions
   indicates the evaluation policy cannot be declared satisfied due to
   observation limits; it does NOT assert student failure.
3. Zero hardcoded formulas: aggregates strictly according to rubric policy.
"""

from typing import List, Optional, Tuple

from study_engine.contracts.assessment import (
    AggregationResult,
    AssessmentStatus,
    DimensionEvaluation,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.curriculum.rubric_contracts import AssessmentRubric


def aggregate_evaluations(
    rubric: AssessmentRubric,
    dimension_evaluations: Tuple[DimensionEvaluation, ...],
) -> AggregationResult:
    """Aggregate dimension evaluations under S5.4 non-average policy."""
    dim_map = {d.dimension_id: d for d in dimension_evaluations}

    critical_failures: List[str] = []
    insufficient_dims: List[str] = []
    compensations_applied: List[str] = []

    # 1. Identify insufficient observations and critical failures
    for dim_def in rubric.dimensions:
        evaluation = dim_map.get(dim_def.dimension_id)
        if evaluation is None:
            continue

        if evaluation.status == AssessmentStatus.INSUFFICIENT_OBSERVATION:
            insufficient_dims.append(dim_def.dimension_id)
        elif evaluation.status == AssessmentStatus.ASSESSED:
            if not evaluation.passed_minimum:
                critical_failures.append(dim_def.dimension_id)

    # 2. Check declarative compensation rules for failures
    uncompensated_failures: List[str] = []
    if rubric.allow_compensation and rubric.compensation_rules:
        for failed_dim_id in critical_failures:
            compensated = False
            for rule in rubric.compensation_rules:
                if rule.source_dimension_id == failed_dim_id:
                    comp_eval = dim_map.get(rule.compensating_dimension_id)
                    failed_eval = dim_map.get(failed_dim_id)

                    if (
                        comp_eval is not None
                        and comp_eval.assigned_level is not None
                        and failed_eval is not None
                        and failed_eval.assigned_level is not None
                    ):
                        if (
                            comp_eval.assigned_level
                            >= rule.compensating_minimum_level
                            and failed_eval.assigned_level
                            >= rule.source_minimum_level
                        ):
                            compensations_applied.append(rule.rule_id)
                            compensated = True
                            break
            if not compensated:
                uncompensated_failures.append(failed_dim_id)
    else:
        uncompensated_failures = list(critical_failures)

    # 3. Determine overall policy satisfaction and level
    has_critical_insufficient = any(
        dim_map[d_id].is_critical
        for d_id in insufficient_dims
        if d_id in dim_map
    )

    passed: bool
    overall_level: Optional[PerformanceLevel]

    if has_critical_insufficient:
        # Policy cannot be declared satisfied due to missing observations
        passed = False
        overall_level = None
    elif len(uncompensated_failures) > 0:
        # Critical dimensions failed without compensation
        passed = False
        assessed_levels = [
            d.assigned_level
            for d in dimension_evaluations
            if d.assigned_level is not None
        ]
        overall_level = (
            min(assessed_levels)
            if assessed_levels
            else PerformanceLevel.N1_INSUFFICIENT
        )
    else:
        # All required dimensions satisfied or compensated
        passed = True
        assessed_levels = [
            d.assigned_level
            for d in dimension_evaluations
            if d.assigned_level is not None
        ]
        overall_level = (
            min(assessed_levels)
            if assessed_levels
            else PerformanceLevel.N3_COMPETENT
        )

    return AggregationResult(
        aggregation_policy="S5.4_NON_AVERAGE_CRITICAL_DIMENSIONS",
        overall_level=overall_level,
        passed=passed,
        critical_dimension_failures=tuple(uncompensated_failures),
        compensation_rules_applied=tuple(compensations_applied),
        insufficient_dimensions=tuple(insufficient_dims),
    )
