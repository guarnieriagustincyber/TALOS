"""Domain contracts for Subsystem S7: Pedagogical Tutor Policy.

Defines the formal vocabulary for pedagogical action selection, response budgeting,
and decision contracts, enforcing the 6 Pedagogical Invariants (TUT-01 to TUT-06).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field


class PedagogicalAction(str, Enum):
    """Permitted structural actions decided by the deterministic TutorPolicy."""

    EXPLAIN = "EXPLAIN"
    """Explains conceptual principles citing strictly authorized evidence [E_i]."""

    ASK = "ASK"
    """Poses a focused inquiry to stimulate student reflection without asserting new facts."""

    HINT = "HINT"
    """Provides targeted scaffolding or direction without revealing the complete solution."""

    CHECK_UNDERSTANDING = "CHECK_UNDERSTANDING"
    """Formally evaluates student grasp of concepts prior to dispatching practical tasks."""

    REQUEST_PRACTICE = "REQUEST_PRACTICE"
    """Directs the student to attempt the practical programming task in the sandbox."""

    GIVE_FEEDBACK = "GIVE_FEEDBACK"
    """Provides pedagogical feedback on a completed execution/assessment outcome."""

    ABSTAIN = "ABSTAIN"
    """Fails closed with abstention when evidence is absent, injection is detected, or scope is exceeded."""
    GUIDE_CURRICULUM = "GUIDE_CURRICULUM"
    """Provides curriculum guidance such as next topic or prerequisites."""

class ResponseBudgetPolicy(str, Enum):
    """Strict token and complexity ceilings to prevent verbose ungrounded drift."""

    SHORT = "SHORT"
    """Max 200 tokens. Direct, concise (1-2 sentences). Suited for ASK, HINT, CHECK."""

    NORMAL = "NORMAL"
    """Max 600 tokens. Standard conceptual explanations with citations."""

    PEDAGOGICAL = "PEDAGOGICAL"
    """Max 900 tokens. Didactic explanations with code examples, citations, and follow-ups."""

    DETAILED = "DETAILED"
    """Max 1200 tokens. Deep structural walkthroughs, multi-step code illustrations."""

    @property
    def token_limit(self) -> int:
        limits = {
            "SHORT": 200,
            "NORMAL": 600,
            "PEDAGOGICAL": 900,
            "DETAILED": 1200,
        }
        return limits.get(self.value, 600)

    def __int__(self) -> int:
        return self.token_limit


@dataclass(frozen=True)
class PedagogicalFollowUp:
    """Deterministic UI metadata accompanying an audited conceptual response.

    This payload is produced exclusively from the curricular context.  It is
    intentionally not part of the factual response text submitted to S4.4.
    """

    verification_question: Optional[str]
    deepen_options: Tuple[str, ...]
    code_example_available: bool
    next_node_id: Optional[str]
    suggested_budget: ResponseBudgetPolicy


class TutorContext(BaseModel):
    """Input context consumed by TutorPolicy to decide the next pedagogical action."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    student_id: str = Field(..., description="Unique identifier of the active student.")
    active_node_id: str = Field(..., description="Curricular node currently targeted.")
    node_status: str = Field(
        ..., description="Current NodeProgressStatus string value."
    )
    unfulfilled_prerequisites: List[str] = Field(
        default_factory=list,
        description="List of unfulfilled hard prerequisite node IDs.",
    )
    conceptual_turns_completed: int = Field(
        default=0, ge=0, description="Count of validated conceptual turns on this node."
    )
    practice_attempts_count: int = Field(
        default=0, ge=0, description="Count of practical submissions on this node."
    )
    last_assessment_verdict: Optional[str] = Field(
        default=None,
        description="Verdict from most recent assessment attempt (PASS/FAIL).",
    )
    last_student_message: Optional[str] = Field(
        default=None, description="Most recent textual input from the student."
    )
    active_node_title: Optional[str] = Field(
        default=None,
        description="Curricular title of the active node for deterministic UI copy.",
    )
    adjacent_node_ids: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="Deterministically ordered downstream nodes adjacent in the curriculum DAG.",
    )
    code_example_available: bool = Field(
        default=False,
        description="Whether the active node declares an available code example.",
    )
    next_node_id: Optional[str] = Field(
        default=None,
        description="Deterministic next curricular node selected from adjacent_node_ids.",
    )


class TutorPolicyDecision(BaseModel):
    """Deterministic decision emitted by TutorPolicy governing the next interaction turn."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: PedagogicalAction = Field(
        ..., description="Structural pedagogical action selected."
    )
    budget: ResponseBudgetPolicy = Field(
        default=ResponseBudgetPolicy.NORMAL, description="Token and formatting ceiling."
    )
    target_node_id: str = Field(
        ..., description="Curricular node targeted by this action."
    )
    rationale: str = Field(
        ..., description="Deterministic justification for selecting this action."
    )
    pedagogical_intent: str = Field(..., description="Instructional goal of the turn.")
    required_evidence_keys: List[str] = Field(
        default_factory=list,
        description="Identifiers of evidence records needed for rendering.",
    )
    suggested_task_id: Optional[str] = Field(
        default=None, description="Task specification ID if action is REQUEST_PRACTICE."
    )
    allow_code_snippets: bool = Field(
        default=False,
        description="Whether code examples are permitted in the rendered response.",
    )
    followup: Optional[PedagogicalFollowUp] = Field(
        default=None,
        description="Deterministic pedagogical follow-up metadata; never part of audited response text.",
    )
