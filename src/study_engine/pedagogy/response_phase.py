"""Response phase contract for structured multi-phase pedagogical generation (Fase 5.8)."""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr

PhaseIdType = Literal[
    "conceptual",
    "pseudocode",
    "python_code",
    "verification",
    "socratic_question",
]


class ResponsePhase(BaseModel):
    """Immutable configuration for an individual pedagogical response phase."""

    model_config = ConfigDict(strict=True, frozen=True)

    phase_id: PhaseIdType = Field(..., description="Unique phase identifier.")
    phase_prompt_template: StrictStr = Field(
        ...,
        min_length=5,
        description="Prompt template specialized for this phase.",
    )
    max_tokens: StrictInt = Field(
        ...,
        gt=0,
        description="Independent, dedicated token budget for this phase.",
    )
    requires_user_approval: StrictBool = Field(
        default=False,
        description="Whether advancing to this phase requires explicit student request.",
    )
    code_allowed: StrictBool = Field(
        default=False,
        description="Whether this phase is authorized to output raw source code blocks.",
    )
