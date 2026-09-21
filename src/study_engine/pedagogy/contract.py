"""Pedagogical contract model defining tutor persona, safety words and response phases (Fase 5.8)."""

from typing import List, Literal
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator

from study_engine.pedagogy.response_phase import ResponsePhase

PersonaType = Literal["socratic_rioplatense", "academic_strict", "cybersec_tactical"]


class PedagogicalContract(BaseModel):
    """Immutable pedagogical specification bound to a Notebook."""

    model_config = ConfigDict(strict=True, frozen=True)

    notebook_id: StrictStr = Field(
        ...,
        min_length=1,
        description="Authoritative notebook identifier to which this contract applies.",
    )
    persona: PersonaType = Field(
        default="socratic_rioplatense",
        description="Pedagogical tone and conversational archetype.",
    )
    base_system_prompt: StrictStr = Field(
        ...,
        min_length=10,
        description="Foundational system prompt establishing the pedagogical stance.",
    )
    forbidden_patterns: List[StrictStr] = Field(
        default_factory=lambda: ["```python", "```py", "import ", "def "],
        description="Regex or literal patterns blocked in non-code phases.",
    )
    safe_words: List[StrictStr] = Field(
        default_factory=lambda: [":solve", "DAME LA SOLUCIÓN COMPLETA", "TRADUCÍ ESTO A PYTHON"],
        description="Explicit user phrases that authorize code generation override.",
    )
    response_phases: List[ResponsePhase] = Field(
        ...,
        min_length=1,
        description="Ordered sequence of pedagogical generation phases.",
    )
    required_analogies: List[StrictStr] = Field(
        default_factory=list,
        description="Mandatory physical/mental analogies the tutor must incorporate.",
    )
    anti_errors: List[StrictStr] = Field(
        default_factory=list,
        description="Forbidden pedagogical mistakes (e.g. 'no digas esto es facil').",
    )

    @field_validator("response_phases")
    @classmethod
    def validate_unique_phase_ids(cls, v: List[ResponsePhase]) -> List[ResponsePhase]:
        phase_ids = [p.phase_id for p in v]
        if len(phase_ids) != len(set(phase_ids)):
            raise ValueError(f"Duplicate phase_ids found in contract: {phase_ids}")
        return v

    def get_phase(self, phase_id: str) -> ResponsePhase:
        """Retrieve a specific phase by ID or raise KeyError."""
        for phase in self.response_phases:
            if phase.phase_id == phase_id:
                return phase
        available = [p.phase_id for p in self.response_phases]
        raise KeyError(f"Phase '{phase_id}' not found in contract. Available: {available}")
