"""Observation Bridge connecting deterministic grading to BKT mastery updates.

INVARIANTS:
1. Idempotency protection: (episode_id, step_id) processed at most once.
2. Only consumes the authoritative canonical BKTTracker instance.
3. Maps GradeResult deterministically to ObservationPayload with EXACT_CORRECTOR source.
"""

from typing import Any, Dict, Optional, Tuple

from study_engine.pedagogy.graders import GradeResult
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.contracts import (
    BKTState,
    ExerciseFormat,
    ObservationPayload,
    ObservationSource,
)


class ObservationBridge:
    """Bridges deterministic grading output to the canonical BKT state machine."""

    def __init__(self, bkt_tracker: BKTTracker) -> None:
        self.bkt_tracker = bkt_tracker
        # Memory ledger of idempotency keys: (episode_id, step_id) -> (GradeResult, BKTState)
        self._consumed_idempotency_keys: Dict[str, Tuple[GradeResult, BKTState]] = {}

    def process_grade(
        self,
        episode_id: str,
        step_id: str,
        kc_id: str,
        grade_result: GradeResult,
        n_options: Optional[int] = None,
    ) -> Tuple[BKTState, bool]:
        """Submit a deterministic grade to BKT, enforcing idempotency.

        Returns:
            Tuple of (BKTState, was_new_observation).
            If idempotency key was already consumed, was_new_observation is False,
            and existing state is returned without mutating P(L).
        """
        idempotency_key = f"{episode_id}::{step_id}"

        if idempotency_key in self._consumed_idempotency_keys:
            _, prior_state = self._consumed_idempotency_keys[idempotency_key]
            return prior_state, False

        # Format mapping
        obs_format = (
            ExerciseFormat.CLOSED_CHOICE
            if n_options is not None
            else ExerciseFormat.SYMBOLIC_OPEN
        )

        observation = ObservationPayload(
            kc_id=kc_id,
            correct=grade_result.is_correct,
            source=ObservationSource.EXACT_CORRECTOR,
            format=obs_format,
            n_options=n_options,
        )

        # Mutate authoritative BKT state
        new_state = self.bkt_tracker.update(observation)

        self._consumed_idempotency_keys[idempotency_key] = (grade_result, new_state)
        return new_state, True
