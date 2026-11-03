"""Observation Bridge connecting deterministic grading to BKT mastery updates.

INVARIANTS:
1. Idempotency protection: (episode_id, step_id) processed at most once.
2. Only consumes the authoritative canonical BKTTracker instance.
3. Maps GradeResult deterministically to ObservationPayload with EXACT_CORRECTOR source.
"""

import hashlib
import json
from typing import Any, Dict, Optional, Tuple

from study_engine.pedagogy.graders import GradeResult
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.spaced_repetition import SpacedRepetitionScheduler
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
        self.storage = bkt_tracker.storage
        self.spaced_scheduler = SpacedRepetitionScheduler(self.storage)
        # Cache is only an optimization; StudentStorage's SQLite receipt is authoritative.
        self._consumed_idempotency_keys: Dict[str, Tuple[GradeResult, BKTState]] = {}

    def process_grade(
        self,
        episode_id: str,
        step_id: str,
        session_id: str,
        exercise_id: str,
        kc_id: str,
        grade_result: GradeResult,
        n_options: Optional[int] = None,
        anchor_id: Optional[str] = None,
    ) -> Tuple[BKTState, bool]:
        """Submit a deterministic grade to BKT, enforcing idempotency.

        Returns:
            Tuple of (BKTState, was_new_observation).
            If idempotency key was already consumed, was_new_observation is False,
            and existing state is returned without mutating P(L).
        """
        if not all((session_id, episode_id, step_id, exercise_id, kc_id)):
            raise ValueError("session, episode, exercise, step, and KC identities are required.")
        if anchor_id is not None and anchor_id != kc_id:
            raise ValueError("Review anchor must identify the evaluated KC.")

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

        operation_payload = {
            "session_id": session_id,
            "episode_id": episode_id,
            "step_id": step_id,
            "exercise_id": exercise_id,
            "kc_id": kc_id,
            "correct": observation.correct,
            "format": observation.format.value,
            "n_options": n_options,
            "raw_answer": grade_result.raw_answer,
            "normalized_answer": grade_result.normalized_answer,
        }
        digest = hashlib.sha256(
            json.dumps(operation_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        with self.storage.transaction():
            receipt = self.storage.get_operation_receipt(
                session_id=session_id,
                episode_id=episode_id,
                exercise_id=exercise_id,
                attempt_id=step_id,
            )
            if receipt is not None:
                stored_digest, result_json = receipt
                if stored_digest != digest:
                    raise ValueError("step_id was already used with different graded content.")
                result = json.loads(result_json)
                return BKTState.model_validate(result), False

            new_state = self.bkt_tracker.update(observation)
            if anchor_id is not None:
                self.spaced_scheduler.schedule_from_observation(anchor_id, observation, as_of=observation.timestamp)
            self.storage.store_operation_receipt(
                session_id=session_id,
                episode_id=episode_id,
                exercise_id=exercise_id,
                attempt_id=step_id,
                request_digest=digest,
                result_json=new_state.model_dump_json(),
            )
            self._consumed_idempotency_keys[f"{episode_id}::{step_id}"] = (grade_result, new_state)
            return new_state, True
