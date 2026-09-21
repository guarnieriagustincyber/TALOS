"""Real-time Prerequisite Lag Detector for Subsystem E3 (Student Cognitive Layer).

Monitors graded exercises during active study sessions. If a student exhibits weakness
in a Knowledge Component that constitutes a prerequisite of the current topic (P(L) < 0.6
after an incorrect attempt), raises a non-blocking RemediationInterrupt.
"""

from typing import Any, Callable, Dict, List, Optional, Set, Union

from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.contracts import (
    ExerciseFormat,
    ObservationPayload,
    ObservationSource,
    RemediationInterrupt,
    RemediationOption,
)
from study_engine.student.storage import StudentStorage


class LagunaDetector:
    """Detects lagging prerequisite concepts and offers pedagogical remediation options."""

    def __init__(
        self,
        bkt: BKTTracker,
        is_prerequisite_fn: Optional[Callable[[str, str], bool]] = None,
        prerequisite_map: Optional[Dict[str, Set[str]]] = None,
        storage: Optional[StudentStorage] = None,
    ) -> None:
        self.bkt = bkt
        self._is_prerequisite_fn = is_prerequisite_fn
        self._prerequisite_map = prerequisite_map or {}
        self.storage = storage or getattr(bkt, "storage", None) or StudentStorage(db_path=":memory:")

    def register_prerequisites(self, topic_id: str, prerequisites: Set[str]) -> None:
        """Register immediate or transitive prerequisites for a topic."""
        self._prerequisite_map[topic_id] = set(prerequisites)

    def is_prerequisite(self, candidate_kc: str, current_topic_id: str) -> bool:
        """Determine if candidate_kc is a prerequisite of current_topic_id."""
        if self._is_prerequisite_fn is not None:
            try:
                return self._is_prerequisite_fn(candidate_kc, current_topic_id)
            except Exception:
                pass

        if current_topic_id in self._prerequisite_map:
            return candidate_kc in self._prerequisite_map[current_topic_id]

        return False

    def check_after_exercise(
        self,
        kc_id_or_payload: Union[ObservationPayload, str],
        correct: Optional[bool] = None,
        current_topic_id: Optional[str] = None,
        source: ObservationSource = ObservationSource.EXACT_CORRECTOR,
        format_type: ExerciseFormat = ExerciseFormat.CLOSED_CHOICE,
        n_options: Optional[int] = None,
    ) -> Optional[RemediationInterrupt]:
        """Process graded exercise and detect prerequisite lag.

        If the KC is a prerequisite of current_topic_id and the student's mastery P(L)
        drops or remains below 0.60 on an incorrect attempt, emit RemediationInterrupt.
        """
        if isinstance(kc_id_or_payload, ObservationPayload):
            payload = kc_id_or_payload
            kc_id = payload.kc_id
            obs_correct = payload.correct
            if current_topic_id is None:
                raise ValueError("current_topic_id is required when checking after exercise")
            bkt_state = self.bkt.update(payload)
        else:
            kc_id = kc_id_or_payload
            if correct is None or current_topic_id is None:
                raise ValueError("correct and current_topic_id are required")
            obs_correct = correct
            bkt_state = self.bkt.update(
                kc_id=kc_id,
                correct=obs_correct,
                source=source,
                format_type=format_type,
                n_options=n_options,
            )

        # Check if evaluated KC is a prerequisite of the currently studied topic
        if not self.is_prerequisite(kc_id, current_topic_id):
            return None

        # Remediation trigger: failure in a prerequisite with P(L) < 0.60
        if not obs_correct and bkt_state.p_L < 0.60:
            return RemediationInterrupt(
                kc_id=kc_id,
                p_L=bkt_state.p_L,
                reason="Prerequisito flaqueó durante estudio",
                options=[
                    RemediationOption.PAUSE_AND_REMEDIATE,
                    RemediationOption.NOTE_AND_CONTINUE,
                    RemediationOption.DUAL_TRACK,
                ],
                current_topic_id=current_topic_id,
            )

        return None

    def record_choice(
        self,
        interrupt: RemediationInterrupt,
        chosen_option: RemediationOption,
    ) -> None:
        """Record the student's selected remediation option into state (H6)."""
        interrupt.chosen_option = chosen_option
        self.storage.record_remediation_choice(interrupt, chosen_option)
