"""Rubric and dimension contracts for Subsystem S5.4.

INVARIANTS:
1. S5.4 defines declarative rubric specifications;
   it NEVER computes grades or verdicts.
2. Canonical 5 dimensions form a reusable standard;
   rubrics may define valid subsets.
3. Sum of dimension weights must equal 1.0 within tolerance (1e-6).
4. All dimension weights must be strictly positive (0 < w <= 1.0).
5. Non-average gate: high scores cannot compensate a critical dimension
   unless explicitly authorized by a declarative CompensationRule.
6. CompensationScope is strictly typed (Enum).
"""

import math
from enum import Enum
from typing import Dict, Tuple
from pydantic import ConfigDict, Field, model_validator

from study_engine.contracts.base import BaseContract
from study_engine.curriculum.performance_contracts import PerformanceLevel

# Canonical 5 Dimensions
DIMENSION_LIVE_DEMO = "live_demo"
DIMENSION_INVARIANT_JUSTIFICATION = "invariant_justification"
DIMENSION_FOUNDATIONS = "foundations"
DIMENSION_QUESTIONS_PERTURBATIONS = "questions_perturbations"
DIMENSION_COMMUNICATION = "communication"

CANONICAL_DIMENSIONS = (
    DIMENSION_LIVE_DEMO,
    DIMENSION_INVARIANT_JUSTIFICATION,
    DIMENSION_FOUNDATIONS,
    DIMENSION_QUESTIONS_PERTURBATIONS,
    DIMENSION_COMMUNICATION,
)


class CompensationScope(str, Enum):
    """Strict scope where a declarative compensation rule applies."""

    GATEWAY = "gateway"
    DIMENSION = "dimension"
    FINAL_ASSESSMENT = "final_assessment"


class CompensationRule(BaseContract):
    """Declarative policy specifying how a deficiency may be offset.

    Example (G6A): Level N2 on one dimension compensated by N4 on another.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str = Field(
        ..., min_length=1, description="Unique rule identifier"
    )
    source_dimension_id: str = Field(
        ..., min_length=1, description="Dimension being compensated"
    )
    source_minimum_level: PerformanceLevel = Field(
        ..., description="Minimum performance level eligible (e.g. N2)"
    )
    compensating_dimension_id: str = Field(
        ..., min_length=1, description="Dimension providing the offset"
    )
    compensating_minimum_level: PerformanceLevel = Field(
        ..., description="Minimum level required on compensating dimension"
    )
    allowed_scope: CompensationScope = Field(
        default=CompensationScope.GATEWAY,
        description="Scope where compensation is valid",
    )
    justification: str = Field(
        ..., min_length=1, description="Pedagogical justification"
    )


class RubricDimension(BaseContract):
    """Declarative definition of a competency assessment dimension."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    dimension_id: str = Field(
        ..., min_length=1, description="Unique dimension identifier"
    )
    title: str = Field(..., min_length=1, description="Human readable title")
    weight: float = Field(
        ..., gt=0.0, le=1.0, description="Normalized weight (0 < w <= 1.0)"
    )
    minimum_level: PerformanceLevel = Field(
        default=PerformanceLevel.N3_COMPETENT,
        description="Minimum non-average level required",
    )
    is_critical: bool = Field(
        default=True,
        description="If True, failure below minimum causes overall failure",
    )
    level_descriptors: Dict[PerformanceLevel, str] = Field(
        default_factory=dict,
        description="Descriptors of expected performance at each level",
    )


class AssessmentRubric(BaseContract):
    """Declarative rubric specifying multi-dimensional assessment criteria.

    INVARIANTS:
    - Sum of dimension weights must equal 1.0 (+- 1e-6).
    - Dimension IDs must be unique.
    - All dimension weights must be strictly positive.
    - Compensation rules must reference valid dimensions declared here.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    rubric_id: str = Field(
        ..., min_length=1, description="Unique rubric identifier"
    )
    title: str = Field(..., min_length=1, description="Rubric title")
    dimensions: Tuple[RubricDimension, ...] = Field(
        ..., min_length=1, description="Ordered collection of dimensions"
    )
    default_pass_level: PerformanceLevel = Field(
        default=PerformanceLevel.N3_COMPETENT,
        description="Default minimum passing level",
    )
    allow_compensation: bool = Field(
        default=False,
        description="Whether compensation rules are enabled",
    )
    compensation_rules: Tuple[CompensationRule, ...] = Field(
        default_factory=tuple,
        description="Declarative compensation policies",
    )

    @model_validator(mode="after")
    def validate_rubric_integrity(self) -> "AssessmentRubric":
        """Enforce weight sum, dimension uniqueness, and rule consistency."""
        dim_ids = [d.dimension_id for d in self.dimensions]
        if len(dim_ids) != len(set(dim_ids)):
            raise ValueError(
                f"Duplicate dimension IDs found in rubric "
                f"'{self.rubric_id}': {dim_ids}"
            )

        total_weight = sum(d.weight for d in self.dimensions)
        if not math.isclose(total_weight, 1.0, rel_tol=1e-5, abs_tol=1e-6):
            raise ValueError(
                f"Rubric '{self.rubric_id}' dimension weights must sum "
                f"to 1.0 (got {total_weight:.6f})"
            )

        valid_dims = set(dim_ids)
        for rule in self.compensation_rules:
            if rule.source_dimension_id not in valid_dims:
                raise ValueError(
                    f"CompensationRule '{rule.rule_id}' references "
                    f"unknown source dimension: "
                    f"'{rule.source_dimension_id}'"
                )
            if rule.compensating_dimension_id not in valid_dims:
                raise ValueError(
                    f"CompensationRule '{rule.rule_id}' references "
                    f"unknown compensating dimension: "
                    f"'{rule.compensating_dimension_id}'"
                )
            if rule.source_dimension_id == rule.compensating_dimension_id:
                raise ValueError(
                    f"CompensationRule '{rule.rule_id}' cannot "
                    f"compensate dimension with itself: "
                    f"'{rule.source_dimension_id}'"
                )

        return self
