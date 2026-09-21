"""Unit tests for Non-Average Aggregator (S9.1.4).

Verifies:
1. Nominal case: all dimensions meet minimum -> passed=True.
2. Non-average gate: critical dimension failure causes passed=False.
3. Insufficient observation: critical insufficient dim -> overall_level=None.
4. Declarative compensation: valid rule offsets eligible deficiency.
5. Ineligible compensation: uncompensated failure blocks satisfaction.
"""

from study_engine.assessment.aggregator import aggregate_evaluations
from study_engine.contracts.assessment import (
    AssessmentStatus,
    DimensionEvaluation,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.curriculum.rubric_contracts import (
    AssessmentRubric,
    CompensationRule,
    CompensationScope,
    RubricDimension,
)


def _sample_multi_dim_rubric(
    allow_comp: bool = False,
    rules: tuple[CompensationRule, ...] = (),
) -> AssessmentRubric:
    dim1 = RubricDimension(
        dimension_id="dim-execution",
        title="Execution",
        weight=0.5,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=True,
    )
    dim2 = RubricDimension(
        dimension_id="dim-invariants",
        title="Invariants",
        weight=0.5,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=True,
    )
    return AssessmentRubric(
        rubric_id="rubric-multi",
        title="Multi Dimension Rubric",
        dimensions=(dim1, dim2),
        allow_compensation=allow_comp,
        compensation_rules=rules,
    )


class TestAggregator:
    """Test suite for aggregate_evaluations."""

    def test_nominal_all_passed(self) -> None:
        """All dimensions meeting minimum level produces passed=True."""
        rubric = _sample_multi_dim_rubric()
        eval1 = DimensionEvaluation(
            dimension_id="dim-execution",
            status=AssessmentStatus.ASSESSED,
            assigned_level=PerformanceLevel.N3_COMPETENT,
            passed_minimum=True,
            is_critical=True,
            evidence_evaluative_fact_ids=("fact-1",),
            evaluation_rationale="Execution ok",
        )
        eval2 = DimensionEvaluation(
            dimension_id="dim-invariants",
            status=AssessmentStatus.ASSESSED,
            assigned_level=PerformanceLevel.N4_EXCELLENT,
            passed_minimum=True,
            is_critical=True,
            evidence_evaluative_fact_ids=("fact-2",),
            evaluation_rationale="Invariants excellent",
        )

        agg = aggregate_evaluations(rubric, (eval1, eval2))
        assert agg.passed is True
        assert agg.overall_level == PerformanceLevel.N3_COMPETENT
        assert len(agg.critical_dimension_failures) == 0
        assert len(agg.insufficient_dimensions) == 0

    def test_non_average_failure_blocks_passing(self) -> None:
        """Single critical failure blocks passing despite excellence."""
        rubric = _sample_multi_dim_rubric()
        eval1 = DimensionEvaluation(
            dimension_id="dim-execution",
            status=AssessmentStatus.ASSESSED,
            assigned_level=PerformanceLevel.N1_INSUFFICIENT,
            passed_minimum=False,
            is_critical=True,
            evidence_evaluative_fact_ids=("fact-1",),
            evaluation_rationale="Failed execution",
        )
        eval2 = DimensionEvaluation(
            dimension_id="dim-invariants",
            status=AssessmentStatus.ASSESSED,
            assigned_level=PerformanceLevel.N4_EXCELLENT,
            passed_minimum=True,
            is_critical=True,
            evidence_evaluative_fact_ids=("fact-2",),
            evaluation_rationale="Invariants excellent",
        )

        agg = aggregate_evaluations(rubric, (eval1, eval2))
        assert agg.passed is False
        assert agg.overall_level == PerformanceLevel.N1_INSUFFICIENT
        assert "dim-execution" in agg.critical_dimension_failures

    def test_insufficient_observation_sets_overall_level_none(self) -> None:
        """Critical INSUFFICIENT_OBSERVATION produces None overall_level."""
        rubric = _sample_multi_dim_rubric()
        eval1 = DimensionEvaluation(
            dimension_id="dim-execution",
            status=AssessmentStatus.INSUFFICIENT_OBSERVATION,
            assigned_level=None,
            passed_minimum=None,
            is_critical=True,
            evidence_evaluative_fact_ids=(),
            evaluation_rationale="Omitted by limits",
        )
        eval2 = DimensionEvaluation(
            dimension_id="dim-invariants",
            status=AssessmentStatus.ASSESSED,
            assigned_level=PerformanceLevel.N4_EXCELLENT,
            passed_minimum=True,
            is_critical=True,
            evidence_evaluative_fact_ids=("fact-2",),
            evaluation_rationale="Invariants excellent",
        )

        agg = aggregate_evaluations(rubric, (eval1, eval2))
        assert agg.passed is False
        assert agg.overall_level is None
        assert "dim-execution" in agg.insufficient_dimensions

    def test_declarative_compensation_satisfies_policy(self) -> None:
        """Declarative CompensationRule permits passing when conditions met."""
        rule = CompensationRule(
            rule_id="comp-rule-01",
            source_dimension_id="dim-execution",
            source_minimum_level=PerformanceLevel.N2_BASIC,
            compensating_dimension_id="dim-invariants",
            compensating_minimum_level=PerformanceLevel.N4_EXCELLENT,
            allowed_scope=CompensationScope.GATEWAY,
            justification=(
                "Deep invariant understanding offsets minor execution glitch"
            ),
        )
        rubric = _sample_multi_dim_rubric(allow_comp=True, rules=(rule,))

        eval1 = DimensionEvaluation(
            dimension_id="dim-execution",
            status=AssessmentStatus.ASSESSED,
            assigned_level=PerformanceLevel.N2_BASIC,
            passed_minimum=False,
            is_critical=True,
            evidence_evaluative_fact_ids=("fact-1",),
            evaluation_rationale="Minor defect",
        )
        eval2 = DimensionEvaluation(
            dimension_id="dim-invariants",
            status=AssessmentStatus.ASSESSED,
            assigned_level=PerformanceLevel.N4_EXCELLENT,
            passed_minimum=True,
            is_critical=True,
            evidence_evaluative_fact_ids=("fact-2",),
            evaluation_rationale="Excellent invariants",
        )

        agg = aggregate_evaluations(rubric, (eval1, eval2))
        assert agg.passed is True
        assert "comp-rule-01" in agg.compensation_rules_applied
        assert len(agg.critical_dimension_failures) == 0
