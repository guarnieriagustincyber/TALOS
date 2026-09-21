"""Contract tests for Rubrics and Dimensions (S5.4)."""

import pytest
from pydantic import ValidationError

from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.curriculum.rubric_contracts import (
    AssessmentRubric,
    CompensationRule,
    CompensationScope,
    RubricDimension,
    DIMENSION_LIVE_DEMO,
    DIMENSION_INVARIANT_JUSTIFICATION,
    DIMENSION_FOUNDATIONS,
    DIMENSION_QUESTIONS_PERTURBATIONS,
    DIMENSION_COMMUNICATION,
)


def test_rubric_dimension_immutability() -> None:
    """Verify RubricDimension is frozen and extra fields are forbidden."""
    dim = RubricDimension(
        dimension_id="dim-1",
        title="Live Demonstration",
        weight=0.5,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=True,
    )
    assert dim.dimension_id == "dim-1"
    with pytest.raises(ValidationError):
        dim.weight = 0.6

    with pytest.raises(ValidationError):
        RubricDimension(
            dimension_id="dim-2",
            title="Extra Field Attempt",
            weight=0.5,
            extra_field="disallowed",  # type: ignore[call-arg]
        )


def test_rubric_dimension_weight_strictly_positive() -> None:
    """HG-S5.4-01: Rubric dimension weights strictly positive (0 < w <= 1)."""
    with pytest.raises(ValidationError):
        RubricDimension(
            dimension_id="dim-zero",
            title="Zero Weight",
            weight=0.0,
        )

    with pytest.raises(ValidationError):
        RubricDimension(
            dimension_id="dim-neg",
            title="Negative Weight",
            weight=-0.1,
        )

    with pytest.raises(ValidationError):
        RubricDimension(
            dimension_id="dim-excess",
            title="Excess Weight",
            weight=1.5,
        )


def test_assessment_rubric_weight_summation() -> None:
    """Dimension weights must sum to 1.0 within tolerance."""
    d1 = RubricDimension(dimension_id="d1", title="D1", weight=0.6)
    d2 = RubricDimension(dimension_id="d2", title="D2", weight=0.4)

    rubric = AssessmentRubric(
        rubric_id="rubric-valid",
        title="Valid Rubric",
        dimensions=(d1, d2),
    )
    assert len(rubric.dimensions) == 2

    # Failing weight sum (< 1.0)
    d3 = RubricDimension(dimension_id="d3", title="D3", weight=0.3)
    with pytest.raises(ValidationError, match="weights must sum to 1.0"):
        AssessmentRubric(
            rubric_id="rubric-invalid-under",
            title="Under 1.0",
            dimensions=(d1, d3),  # 0.6 + 0.3 = 0.9
        )

    # Failing weight sum (> 1.0)
    d4 = RubricDimension(dimension_id="d4", title="D4", weight=0.5)
    with pytest.raises(ValidationError, match="weights must sum to 1.0"):
        AssessmentRubric(
            rubric_id="rubric-invalid-over",
            title="Over 1.0",
            dimensions=(d1, d4),  # 0.6 + 0.5 = 1.1
        )


def test_assessment_rubric_duplicate_dimensions_rejected() -> None:
    """Rubric must reject duplicate dimension IDs."""
    d1 = RubricDimension(dimension_id="dup-id", title="D1", weight=0.5)
    d2 = RubricDimension(dimension_id="dup-id", title="D2", weight=0.5)

    with pytest.raises(ValidationError, match="Duplicate dimension IDs"):
        AssessmentRubric(
            rubric_id="rubric-dup",
            title="Duplicate Dim",
            dimensions=(d1, d2),
        )


def test_compensation_rule_validation() -> None:
    """Compensation rules reference declared dimensions; no self-comp."""
    d1 = RubricDimension(dimension_id="demo", title="Demo", weight=0.5)
    d2 = RubricDimension(
        dimension_id="justification", title="Justification", weight=0.5
    )

    valid_rule = CompensationRule(
        rule_id="comp-1",
        source_dimension_id="demo",
        source_minimum_level=PerformanceLevel.N2_BASIC,
        compensating_dimension_id="justification",
        compensating_minimum_level=PerformanceLevel.N4_EXCELLENT,
        allowed_scope=CompensationScope.GATEWAY,
        justification="Deep formal justification compensates for minor flaw",
    )

    rubric = AssessmentRubric(
        rubric_id="rubric-comp",
        title="Rubric with Compensation",
        dimensions=(d1, d2),
        allow_compensation=True,
        compensation_rules=(valid_rule,),
    )
    assert len(rubric.compensation_rules) == 1

    # Unknown source dimension
    bad_rule_source = CompensationRule(
        rule_id="comp-bad-src",
        source_dimension_id="nonexistent",
        source_minimum_level=PerformanceLevel.N2_BASIC,
        compensating_dimension_id="justification",
        compensating_minimum_level=PerformanceLevel.N4_EXCELLENT,
        allowed_scope=CompensationScope.GATEWAY,
        justification="Invalid source",
    )
    with pytest.raises(
        ValidationError, match="references unknown source dimension"
    ):
        AssessmentRubric(
            rubric_id="rubric-bad-src",
            title="Bad Source",
            dimensions=(d1, d2),
            compensation_rules=(bad_rule_source,),
        )

    # Self compensation
    bad_rule_self = CompensationRule(
        rule_id="comp-self",
        source_dimension_id="demo",
        source_minimum_level=PerformanceLevel.N2_BASIC,
        compensating_dimension_id="demo",
        compensating_minimum_level=PerformanceLevel.N4_EXCELLENT,
        allowed_scope=CompensationScope.GATEWAY,
        justification="Self compensation disallowed",
    )
    with pytest.raises(
        ValidationError, match="cannot compensate dimension with itself"
    ):
        AssessmentRubric(
            rubric_id="rubric-self",
            title="Self Comp",
            dimensions=(d1, d2),
            compensation_rules=(bad_rule_self,),
        )


def test_canonical_5_dimensions_g6a_representation() -> None:
    """Demonstrate representation of G6A 5-dimension rubric."""
    d_demo = RubricDimension(
        dimension_id=DIMENSION_LIVE_DEMO,
        title="Demostración en vivo",
        weight=0.30,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=True,
    )
    d_just = RubricDimension(
        dimension_id=DIMENSION_INVARIANT_JUSTIFICATION,
        title="Justificación",
        weight=0.25,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=True,
    )
    d_found = RubricDimension(
        dimension_id=DIMENSION_FOUNDATIONS,
        title="Conexión fundamentos",
        weight=0.20,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=True,
    )
    d_quest = RubricDimension(
        dimension_id=DIMENSION_QUESTIONS_PERTURBATIONS,
        title="Preguntas / Perturbaciones",
        weight=0.15,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=True,
    )
    d_comm = RubricDimension(
        dimension_id=DIMENSION_COMMUNICATION,
        title="Comunicación ejecutiva",
        weight=0.10,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=False,
    )

    # G6A rule: N2 in one dimension compensates with N4 in another
    g6a_rule = CompensationRule(
        rule_id="g6a-compensation",
        source_dimension_id=DIMENSION_LIVE_DEMO,
        source_minimum_level=PerformanceLevel.N2_BASIC,
        compensating_dimension_id=DIMENSION_INVARIANT_JUSTIFICATION,
        compensating_minimum_level=PerformanceLevel.N4_EXCELLENT,
        allowed_scope=CompensationScope.GATEWAY,
        justification="Umbral G6A: N3 en todas. N2 compensa con N4.",
    )

    g6a_rubric = AssessmentRubric(
        rubric_id="rubric-g6a",
        title="Rúbrica Capstone G6A (5 Dimensiones)",
        dimensions=(d_demo, d_just, d_found, d_quest, d_comm),
        default_pass_level=PerformanceLevel.N3_COMPETENT,
        allow_compensation=True,
        compensation_rules=(g6a_rule,),
    )

    assert len(g6a_rubric.dimensions) == 5
    assert sum(d.weight for d in g6a_rubric.dimensions) == pytest.approx(1.0)
    assert g6a_rubric.allow_compensation is True
