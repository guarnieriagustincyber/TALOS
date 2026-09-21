"""Oral defense contracts for Subsystem S5.4.

INVARIANTS:
1. S5.4 defines declarative oral defense specifications;
   it NEVER conducts defenses or scores responses (S7/S9 responsibility).
2. Question templates specify declarative target concepts and expectations.
3. All models are strictly immutable (frozen=True, extra="forbid").
"""

from enum import Enum
from typing import Tuple
from pydantic import ConfigDict, Field, model_validator

from study_engine.contracts.base import BaseContract


class DefenseCategory(str, Enum):
    """Pedagogical category of oral defense questioning."""

    ARCHITECTURE_JUSTIFICATION = "architecture_justification"
    INVARIANT_DEFENSE = "invariant_defense"
    INCIDENT_ROOT_CAUSE = "incident_root_cause"
    ADVERSARIAL_ANALYSIS = "adversarial_analysis"
    EXECUTIVE_SYNTHESIS = "executive_synthesis"


class DefenseQuestionTemplate(BaseContract):
    """Declarative question template used in oral gateway defense."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    question_id: str = Field(
        ..., min_length=1, description="Unique question identifier"
    )
    category: DefenseCategory = Field(
        ..., description="Thematic category of questioning"
    )
    prompt_text: str = Field(
        ..., min_length=1, description="Question prompt delivered to candidate"
    )
    target_concepts: Tuple[str, ...] = Field(
        ..., min_length=1, description="Concepts candidate must touch upon"
    )
    expected_points_n3: Tuple[str, ...] = Field(
        ..., min_length=1, description="Points required for N3 (Competent)"
    )
    expected_points_n4: Tuple[str, ...] = Field(
        default_factory=tuple, description="Advanced insights for N4"
    )


class OralDefenseSpecification(BaseContract):
    """Declarative specification of an oral defense examination.

    INVARIANTS:
    - required_questions_count must not exceed size of question_pool.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    defense_id: str = Field(
        ..., min_length=1, description="Unique defense identifier"
    )
    duration_minutes: int = Field(
        ..., gt=0, description="Scheduled duration in minutes"
    )
    panel_size: int = Field(
        default=1, ge=1, description="Number of examiners (1 or 3)"
    )
    question_pool: Tuple[DefenseQuestionTemplate, ...] = Field(
        ..., min_length=1, description="Pool of defense questions"
    )
    required_questions_count: int = Field(
        ..., ge=1, description="Number of questions candidate must answer"
    )
    rubric_id: str = Field(
        ..., min_length=1, description="Rubric ID applied to oral responses"
    )

    @model_validator(mode="after")
    def validate_question_count(self) -> "OralDefenseSpecification":
        """Verify question pool is sufficiently large."""
        if self.required_questions_count > len(self.question_pool):
            raise ValueError(
                f"required_questions_count ({self.required_questions_count}) "
                f"exceeds question_pool size ({len(self.question_pool)}) "
                f"in defense '{self.defense_id}'"
            )
        return self
