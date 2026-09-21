"""Perturbation and adversarial template contracts for Subsystem S5.4.

INVARIANTS:
1. S5.4 defines declarative perturbation templates;
   it NEVER executes fault injections or attacks.
2. Models explicit behavioral expectations for N3 and N4 levels.
3. All contracts are immutable (frozen=True, extra="forbid").
"""

from enum import Enum
from typing import Dict
from pydantic import ConfigDict, Field, model_validator

from study_engine.contracts.base import BaseContract
from study_engine.curriculum.performance_contracts import PerformanceLevel


class PerturbationType(str, Enum):
    """Taxonomy of pedagogical perturbations used across Gateways."""

    PARAMETER_MUTATION = "parameter_mutation"
    FAULT_INJECTION = "fault_injection"
    BOUNDARY_CONDITION = "boundary_condition"
    ADVERSARIAL_INPUT = "adversarial_input"
    ENVIRONMENT_DEGRADATION = "environment_degradation"
    PROTOCOL_VIOLATION = "protocol_violation"


class ExpectedBehavior(BaseContract):
    """Declarative definition of student response under perturbation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    performance_level: PerformanceLevel = Field(
        ..., description="Performance level demonstrated by this response"
    )
    expected_reasoning: str = Field(
        ..., min_length=1, description="Expected conceptual justification"
    )
    expected_action: str = Field(
        ..., min_length=1, description="Expected diagnostic action or patch"
    )


class PerturbationTemplate(BaseContract):
    """Declarative perturbation specification for practical challenges.

    Example (G1.2 #1): Change '!' to '<' in struct.unpack.
    - Baseline: Network byte order (big-endian).
    - Mutated: Little-endian.
    - N3 expectation: 'Fields 16+ bits are byte-swapped'.
    - N4 expectation: Predicts precisely which fields break and which stay.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    perturbation_id: str = Field(
        ..., min_length=1, description="Unique perturbation identifier"
    )
    type: PerturbationType = Field(
        ..., description="Perturbation category"
    )
    name: str = Field(
        ..., min_length=1, description="Short human readable name"
    )
    description: str = Field(
        ..., min_length=1, description="Detailed description"
    )
    baseline_condition: str = Field(
        ..., min_length=1, description="Standard operating condition"
    )
    mutated_condition: str = Field(
        ..., min_length=1, description="Perturbed condition injected"
    )
    level_expectations: Dict[PerformanceLevel, ExpectedBehavior] = Field(
        ..., min_length=1, description="Mapping of levels to expectations"
    )

    @model_validator(mode="after")
    def validate_expectations_contain_competent_level(
        self,
    ) -> "PerturbationTemplate":
        """Perturbation must define at least an N3 expectation."""
        if PerformanceLevel.N3_COMPETENT not in self.level_expectations:
            raise ValueError(
                f"PerturbationTemplate '{self.perturbation_id}' must define "
                f"expectations for PerformanceLevel.N3_COMPETENT"
            )
        return self
