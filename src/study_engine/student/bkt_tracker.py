"""Bayesian Knowledge Tracing (BKT) Engine for Subsystem E3 (Student Cognitive Layer).

Based on Corbett & Anderson (1995):
Tracks the probability P(L) that a student has mastered a Knowledge Component (KC).

INVARIANTS:
1. Deterministic Bayesian updates; zero LLM hallucination or subjectivity.
2. Only verifiable grading sources (SymbolicVerifier, ExactCorrector, DiagnosticBank)
   are permitted. Free dialogue is rejected fail-closed.
3. p_G adapts dynamically to format: 1/n_options for closed-choice, 0.02 for symbolic-open (H3).
4. kc_id is strictly validated and mandatory (H4).
"""

from datetime import datetime, timezone
import threading
from typing import Dict, Optional


from study_engine.student.contracts import (
    BKTState,
    ExerciseFormat,
    ObservationPayload,
    ObservationSource,
)
from study_engine.student.storage import StudentStorage

DEFAULT_BKT_PARAMS = {
    "p_L0": 0.1,  # Initial prior probability of knowing
    "p_T": 0.3,   # Transition probability (learning on this step)
    "p_G": 0.25,  # Default guess probability (4-option multiple choice)
    "p_S": 0.1,   # Slip probability (knowing but making an error)
}


class BKTTracker:
    """Manages and updates Bayesian Knowledge Tracing states per Knowledge Component."""

    def __init__(
        self,
        storage: Optional[StudentStorage] = None,
        default_params: Optional[Dict[str, float]] = None,
    ) -> None:
        self.storage = storage or StudentStorage(db_path=":memory:")
        self.params = default_params or dict(DEFAULT_BKT_PARAMS)
        self._lock = threading.RLock()

    def get_state(self, kc_id: str) -> BKTState:
        """Fetch current BKT state for kc_id, or initialize with defaults."""
        if not kc_id or not kc_id.strip():
            raise ValueError("kc_id cannot be empty or blank (H4 Fail-Closed)")

        kc_id = kc_id.strip()
        with self._lock:
            state = self.storage.get_bkt_state(kc_id)
            if state is None:
                state = BKTState(
                    kc_id=kc_id,
                    p_L=self.params["p_L0"],
                    p_T=self.params["p_T"],
                    p_G=self.params["p_G"],
                    p_S=self.params["p_S"],
                    attempts=0,
                    last_update=datetime.now(timezone.utc),
                )
            return state

    def save_state(self, state: BKTState) -> None:
        """Persist state to underlying storage."""
        with self._lock:
            self.storage.save_bkt_state(state)

    def reset(self, kc_id: str) -> BKTState:
        """Reset a Knowledge Component to default initial state."""
        if not kc_id or not kc_id.strip():
            raise ValueError("kc_id cannot be empty or blank (H4 Fail-Closed)")

        kc_id = kc_id.strip()
        with self._lock:
            state = BKTState(
                kc_id=kc_id,
                p_L=self.params["p_L0"],
                p_T=self.params["p_T"],
                p_G=self.params["p_G"],
                p_S=self.params["p_S"],
                attempts=0,
                last_update=datetime.now(timezone.utc),
            )
            self.save_state(state)
            return state

    def compute_p_G(
        self,
        format_type: ExerciseFormat,
        n_options: Optional[int] = None,
    ) -> float:
        """Derive guess probability dynamically from exercise format (H3)."""
        if format_type == ExerciseFormat.SYMBOLIC_OPEN:
            return 0.02

        if n_options is not None and n_options >= 2:
            return 1.0 / float(n_options)

        return self.params["p_G"]

    def update(
        self,
        observation: Optional[ObservationPayload] = None,
        kc_id: Optional[str] = None,
        correct: Optional[bool] = None,
        source: ObservationSource = ObservationSource.EXACT_CORRECTOR,
        format_type: ExerciseFormat = ExerciseFormat.CLOSED_CHOICE,
        n_options: Optional[int] = None,
    ) -> BKTState:
        """Update P(L) given an observation under Corbett & Anderson formulas.

        Supports passing either an explicit ObservationPayload or positional/keyword arguments.
        """
        if observation is not None:
            payload = observation
            target_kc = payload.kc_id
            obs_correct = payload.correct
            obs_source = payload.source
            obs_format = payload.format
            obs_n_options = payload.n_options
        elif isinstance(kc_id, ObservationPayload):
            payload = kc_id
            target_kc = payload.kc_id
            obs_correct = payload.correct
            obs_source = payload.source
            obs_format = payload.format
            obs_n_options = payload.n_options
        else:
            if kc_id is None:
                raise ValueError("kc_id or observation payload is required")
            if correct is None:
                raise ValueError("correct boolean is required when passing kc_id")
            target_kc = kc_id
            obs_correct = correct
            obs_source = source
            obs_format = format_type
            obs_n_options = n_options

        # FAIL-CLOSED VALIDATION: Dialogue / unverified LLM output is forbidden
        if obs_source == ObservationSource.UNVERIFIED_DIALOGUE:
            raise ValueError(
                "UNVERIFIED_DIALOGUE observation rejected: LLM conversation is forbidden from mutating student mastery."
            )

        if not target_kc or not target_kc.strip():
            raise ValueError("kc_id cannot be empty or whitespace (H4 Fail-Closed)")

        target_kc = target_kc.strip()
        with self._lock:
            state = self.get_state(target_kc)

            # Dynamic guess probability (H3)
            effective_p_G = self.compute_p_G(obs_format, obs_n_options)
            p_S = state.p_S
            p_T = state.p_T
            p_L_prior = state.p_L

            # Corbett & Anderson (1995) Bayesian update
            if obs_correct:
                numerator = p_L_prior * (1.0 - p_S)
                denominator = numerator + (1.0 - p_L_prior) * effective_p_G
            else:
                numerator = p_L_prior * p_S
                denominator = numerator + (1.0 - p_L_prior) * (1.0 - effective_p_G)

            # Numerical safety: avoid division by zero
            if denominator <= 0.0:
                p_L_obs = 1.0 if obs_correct else 0.0
            else:
                p_L_obs = numerator / denominator

            # Transition to learned state
            p_L_next = p_L_obs + (1.0 - p_L_obs) * p_T

            # Clamping to valid probability interval [0.0, 1.0]
            p_L_next = max(0.0, min(1.0, p_L_next))

            state.p_L = p_L_next
            state.p_G = effective_p_G
            state.attempts += 1
            state.last_update = datetime.now(timezone.utc)

            self.save_state(state)
            return state
