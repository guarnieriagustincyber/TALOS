"""Spaced Repetition Scheduler (SM-2) for Subsystem E3 (Student Cognitive Layer).

Schedules reviews for conceptual anchors using a deterministic SM-2 algorithm.
INVARIANTS:
1. EF (Easiness Factor) has an absolute floor of 1.30.
2. Review quality is deterministically mapped from verifiable observations (H7).
3. Student state persistence across reboots.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from study_engine.student.contracts import (
    AnchorState,
    ExerciseFormat,
    ObservationPayload,
)
from study_engine.student.storage import StudentStorage


def derive_sm2_quality(
    correct: bool,
    format_type: ExerciseFormat = ExerciseFormat.CLOSED_CHOICE,
    is_retry: bool = False,
    is_recoverable: bool = False,
) -> int:
    """Deterministically map graded interaction to SM-2 quality grade 0-5 (H7).

    Rules:
    - Symbolic correct: 5 (perfect recall & rigorous calculation)
    - Correct with retry: 4 (correct after minor hesitation)
    - Closed-choice correct: 4 (correct option identified)
    - Incorrect recoverable / near-miss: 3 (serious effort with minor error)
    - Incorrect: 1 (failure / conceptual gap)
    """
    if correct:
        if format_type == ExerciseFormat.SYMBOLIC_OPEN and not is_retry:
            return 5
        return 4
    else:
        if is_recoverable:
            return 3
        return 1


class SpacedRepetitionScheduler:
    """Schedules review of key conceptual anchors using the SM-2 algorithm."""

    def __init__(self, storage: Optional[StudentStorage] = None) -> None:
        self.storage = storage or StudentStorage(db_path=":memory:")

    def get_anchor_state(self, anchor_id: str) -> AnchorState:
        """Retrieve anchor state or initialize with default SM-2 values."""
        if not anchor_id or not anchor_id.strip():
            raise ValueError("anchor_id cannot be empty or blank")

        anchor_id = anchor_id.strip()
        state = self.storage.get_anchor_state(anchor_id)
        if state is None:
            now = datetime.now(timezone.utc)
            state = AnchorState(
                anchor_id=anchor_id,
                interval=1,
                repetitions=0,
                EF=2.5,
                next_review=now,
                last_quality=5,
                updated_at=now,
            )
        return state

    def save_anchor_state(self, state: AnchorState) -> None:
        """Persist anchor state."""
        self.storage.save_anchor_state(state)

    def schedule_review(
        self,
        anchor_id: str,
        quality: int,
        as_of: Optional[datetime] = None,
    ) -> datetime:
        """Update anchor interval and schedule next review timestamp according to SM-2.

        quality: int 0 to 5 (0=blackout, 5=perfect)
        """
        if not (0 <= quality <= 5):
            raise ValueError(f"SM-2 quality must be between 0 and 5, got {quality}")

        state = self.get_anchor_state(anchor_id)
        current_time = as_of or datetime.now(timezone.utc)

        if quality < 3:
            # Memory lapsed: reset intervals
            state.interval = 1
            state.repetitions = 0
        else:
            # Successful recall: advance repetitions and calculate interval
            if state.repetitions == 0:
                state.interval = 1
            elif state.repetitions == 1:
                state.interval = 6
            else:
                state.interval = max(1, int(round(state.interval * state.EF)))

            state.repetitions += 1

        # Adjust EF: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        delta = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        state.EF = max(1.30, state.EF + delta)

        next_review = current_time + timedelta(days=state.interval)
        state.next_review = next_review
        state.last_quality = quality
        state.updated_at = current_time

        self.save_anchor_state(state)
        return next_review

    def schedule_from_observation(
        self,
        anchor_id: str,
        observation: ObservationPayload,
        as_of: Optional[datetime] = None,
    ) -> datetime:
        """Schedule review directly from an evaluated observation (H7)."""
        quality = derive_sm2_quality(
            correct=observation.correct,
            format_type=observation.format,
            is_retry=observation.is_retry,
            is_recoverable=observation.is_recoverable_error,
        )
        return self.schedule_review(anchor_id=anchor_id, quality=quality, as_of=as_of)

    def get_due_anchors(self, as_of: Optional[datetime] = None) -> List[str]:
        """Return IDs of all conceptual anchors due for review on or before as_of."""
        ref_time = as_of or datetime.now(timezone.utc)
        all_states = self.storage.get_all_anchor_states()
        return [
            anchor_id
            for anchor_id, state in all_states.items()
            if state.next_review <= ref_time
        ]

    def record_review(
        self,
        anchor_id: str,
        correct: bool,
        format_type: ExerciseFormat = ExerciseFormat.CLOSED_CHOICE,
        is_retry: bool = False,
        is_recoverable: bool = False,
        as_of: Optional[datetime] = None,
    ) -> datetime:
        """Deterministically record an evaluation and advance the SM-2 schedule (E14)."""
        quality = derive_sm2_quality(
            correct=correct,
            format_type=format_type,
            is_retry=is_retry,
            is_recoverable=is_recoverable,
        )
        return self.schedule_review(anchor_id=anchor_id, quality=quality, as_of=as_of)
