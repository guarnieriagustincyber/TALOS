"""Observation Bridge for Subsystem E3 (Student Cognitive Layer) (Amendment H2).

Bridges deterministic evaluation outcomes (SymbolicVerifier / ExactCorrector)
to the student cognitive layer by composition without altering the frozen assessment perimeter.

INVARIANTS:
1. Pure composition: does not mutate or import frozen internal assessment state.
2. Atomic execution: updates BKT, triggers LagunaDetector, and optionally schedules SM-2 review.
3. Fail-closed: rejects unverified or non-verifiable claims.
"""

from typing import Any, Optional, Tuple, Union

from study_engine.evidence.symbolic_verifier import SymbolicVerdict
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.contracts import (
    BKTState,
    ExerciseFormat,
    ObservationPayload,
    ObservationSource,
    RemediationInterrupt,
)
from study_engine.student.laguna_detector import LagunaDetector
from study_engine.student.spaced_repetition import SpacedRepetitionScheduler


class ObservationBridge:
    """Consumes grading events and atomically propagates them to BKT, LagunaDetector, and SM-2."""

    def __init__(
        self,
        bkt: BKTTracker,
        laguna_detector: LagunaDetector,
        spaced_repetition: Optional[SpacedRepetitionScheduler] = None,
    ) -> None:
        self.bkt = bkt
        self.laguna_detector = laguna_detector
        self.spaced_repetition = spaced_repetition

    def process_symbolic_result(
        self,
        kc_id: str,
        symbolic_verdict: Union[SymbolicVerdict, str],
        current_topic_id: str,
        anchor_id: Optional[str] = None,
    ) -> Tuple[BKTState, Optional[RemediationInterrupt]]:
        """Process a formal verdict from SymbolicVerifier and update cognitive state.

        VERIFIED_TRUE -> correct=True (p_G=0.02)
        REJECTED_HALLUCINATION -> correct=False (p_G=0.02)
        UNVERIFIABLE -> raises ValueError (cannot mutate student mastery on unverified data)
        """
        verdict_str = (
            symbolic_verdict.value
            if hasattr(symbolic_verdict, "value")
            else str(symbolic_verdict)
        )

        if verdict_str == SymbolicVerdict.VERIFIED_TRUE.value:
            is_correct = True
        elif verdict_str == SymbolicVerdict.REJECTED_HALLUCINATION.value:
            is_correct = False
        else:
            raise ValueError(
                f"Cannot update BKT with non-verifiable verdict: {verdict_str} (H2 Fail-Closed)"
            )

        payload = ObservationPayload(
            kc_id=kc_id,
            correct=is_correct,
            source=ObservationSource.SYMBOLIC_VERIFIER,
            format=ExerciseFormat.SYMBOLIC_OPEN,
            n_options=None,
        )

        # Atomic execution: laguna check triggers BKT update internally
        interrupt = self.laguna_detector.check_after_exercise(
            kc_id_or_payload=payload,
            current_topic_id=current_topic_id,
        )
        bkt_state = self.bkt.get_state(kc_id)

        if anchor_id and self.spaced_repetition is not None:
            self.spaced_repetition.schedule_from_observation(anchor_id, payload)

        return bkt_state, interrupt

    def process_exact_correction(
        self,
        kc_id: str,
        correct: bool,
        current_topic_id: str,
        format_type: ExerciseFormat = ExerciseFormat.CLOSED_CHOICE,
        n_options: Optional[int] = 4,
        is_retry: bool = False,
        is_recoverable: bool = False,
        anchor_id: Optional[str] = None,
    ) -> Tuple[BKTState, Optional[RemediationInterrupt]]:
        """Process an exact deterministic grading result (H2)."""
        payload = ObservationPayload(
            kc_id=kc_id,
            correct=correct,
            source=ObservationSource.EXACT_CORRECTOR,
            format=format_type,
            n_options=n_options,
            is_retry=is_retry,
            is_recoverable_error=is_recoverable,
        )

        interrupt = self.laguna_detector.check_after_exercise(
            kc_id_or_payload=payload,
            current_topic_id=current_topic_id,
        )
        bkt_state = self.bkt.get_state(kc_id)

        if anchor_id and self.spaced_repetition is not None:
            self.spaced_repetition.schedule_from_observation(anchor_id, payload)

        return bkt_state, interrupt
