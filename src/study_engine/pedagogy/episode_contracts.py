"""Episode and pedagogical lifecycle contracts.

INVARIANTS:
1. Pure deterministic state transitions: EXPLAINING -> EVALUATING -> CLOSED.
2. The orchestrator never decides mastery or curricular advancement.
3. Every step in an episode has an idempotency key to prevent double grading.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Literal, Optional, Tuple


class EpisodePhase(str, Enum):
    """Deterministic phases of a study episode."""

    EXPLAINING = "EXPLAINING"
    DIALOGUE = "DIALOGUE"
    DIALOGUE_LIMIT_REACHED = "DIALOGUE_LIMIT_REACHED"
    SUGGEST_EXERCISE = "SUGGEST_EXERCISE"
    EVALUATING = "EVALUATING"
    CLOSED = "CLOSED"


@dataclass(frozen=True)
class Episode:
    """Authoritative lifecycle tracking of an interactive study episode."""

    episode_id: str
    notebook_id: str
    kc_id: str
    objective: str
    phase: EpisodePhase = EpisodePhase.EXPLAINING
    current_step_id: str = "step_concept"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    idempotency_keys_consumed: FrozenSet[str] = field(default_factory=frozenset)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def transition_to(
        self,
        next_phase: EpisodePhase,
        next_step_id: str,
        consumed_key: Optional[str] = None,
    ) -> "Episode":
        """Deterministic state transition creating an immutable next Episode."""
        # Enforce valid forward transitions
        valid_transitions = {
            EpisodePhase.EXPLAINING: {EpisodePhase.DIALOGUE, EpisodePhase.EVALUATING, EpisodePhase.CLOSED},
            EpisodePhase.DIALOGUE: {EpisodePhase.DIALOGUE_LIMIT_REACHED, EpisodePhase.SUGGEST_EXERCISE, EpisodePhase.EVALUATING, EpisodePhase.CLOSED},
            EpisodePhase.DIALOGUE_LIMIT_REACHED: {EpisodePhase.SUGGEST_EXERCISE, EpisodePhase.DIALOGUE, EpisodePhase.EVALUATING, EpisodePhase.CLOSED},
            EpisodePhase.SUGGEST_EXERCISE: {EpisodePhase.EVALUATING, EpisodePhase.DIALOGUE, EpisodePhase.CLOSED},
            EpisodePhase.EVALUATING: {EpisodePhase.EVALUATING, EpisodePhase.DIALOGUE, EpisodePhase.CLOSED},
            EpisodePhase.CLOSED: set(),
        }
        if next_phase not in valid_transitions.get(self.phase, set()):
            raise ValueError(
                f"Invalid episode transition from {self.phase} to {next_phase}."
            )

        keys = set(self.idempotency_keys_consumed)
        if consumed_key:
            keys.add(consumed_key)

        return Episode(
            episode_id=self.episode_id,
            notebook_id=self.notebook_id,
            kc_id=self.kc_id,
            objective=self.objective,
            phase=next_phase,
            current_step_id=next_step_id,
            created_at=self.created_at,
            idempotency_keys_consumed=frozenset(keys),
            metadata=dict(self.metadata),
        )

    def is_key_consumed(self, idempotency_key: str) -> bool:
        """Check if an evaluation idempotency key was already consumed."""
        return idempotency_key in self.idempotency_keys_consumed
