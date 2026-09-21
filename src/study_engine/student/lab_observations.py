"""Deterministic Lab Grader Interface to BKT ObservationBridge (Phase E4, Amendment E4-7, Namespace [LAB#]).

Translates deterministic practical lab challenges (Juice Shop, VAmPI, local C labs)
into student cognitive observations:
1. Validates challenge against config/lab_kc_map.json.
2. Checks submitted flag/proof deterministically via SHA-256 hash matching.
3. Produces ObservationPayload with source=EXACT_CORRECTOR and format=SYMBOLIC_OPEN.
4. Strictly REJECTS any update attempt originating from LLM dialogue or unstructured chat.
5. Feeds observations into BKTTracker via ObservationBridge or directly.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from study_engine.student.contracts import (
    BKTState,
    ExerciseFormat,
    ObservationPayload,
    ObservationSource,
    RemediationInterrupt,
)
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.observation_bridge import ObservationBridge


class LabChallengeMapping(BaseModel):
    """Mapping from deterministic lab challenge to Knowledge Component."""

    model_config = ConfigDict(frozen=True)

    lab_id: str = Field(..., min_length=1)
    challenge_id: str = Field(..., min_length=1)
    kc_id: str = Field(..., min_length=1)
    exercise_format: ExerciseFormat = Field(default=ExerciseFormat.SYMBOLIC_OPEN)
    expected_flag_hash: str = Field(..., min_length=64, max_length=64)
    weight: float = Field(default=1.0, ge=0.1, le=2.0)


class LabSubmissionResult(BaseModel):
    """Result of evaluating a lab challenge submission."""

    model_config = ConfigDict(frozen=True)

    lab_id: str
    challenge_id: str
    kc_id: str
    is_correct: bool
    status_code: str  # "CORRECT", "INCORRECT", "UNKNOWN_CHALLENGE", "REJECTED_LLM_UPDATE"
    details: Dict[str, Any] = Field(default_factory=dict)
    bkt_state: Optional[BKTState] = None
    interrupt: Optional[RemediationInterrupt] = None


class LabGraderBridge:
    """Evaluates deterministic lab submissions and propagates observations to BKT."""

    def __init__(
        self,
        bkt_tracker: Optional[BKTTracker] = None,
        observation_bridge: Optional[ObservationBridge] = None,
        config_path: Optional[str] = "config/lab_kc_map.json",
    ) -> None:
        self.bkt_tracker = bkt_tracker or BKTTracker()
        self.observation_bridge = observation_bridge
        self.config_path = Path(config_path) if config_path else None
        self._mappings: Dict[Tuple[str, str], LabChallengeMapping] = {}
        self._lock = threading.Lock()

        if self.config_path and self.config_path.exists():
            self._load_mappings()

    def _load_mappings(self) -> None:
        raw_bytes = self.config_path.read_bytes()
        data = json.loads(raw_bytes.decode("utf-8"))
        loaded: Dict[Tuple[str, str], LabChallengeMapping] = {}
        for m in data.get("mappings", []):
            mapping = LabChallengeMapping(
                lab_id=m["lab_id"],
                challenge_id=m["challenge_id"],
                kc_id=m["kc_id"],
                exercise_format=ExerciseFormat(m.get("exercise_format", "SYMBOLIC_OPEN")),
                expected_flag_hash=m["expected_flag_hash"],
                weight=m.get("weight", 1.0),
            )
            loaded[(mapping.lab_id, mapping.challenge_id)] = mapping
        self._mappings = loaded

    def register_challenge(self, mapping: LabChallengeMapping) -> None:
        with self._lock:
            self._mappings[(mapping.lab_id, mapping.challenge_id)] = mapping

    def grade_and_record_submission(
        self,
        lab_id: str,
        challenge_id: str,
        submitted_flag: str,
        current_topic_id: Optional[str] = None,
        source_context: str = "DETERMINISTIC_GRADER",
    ) -> LabSubmissionResult:
        """Deterministically grade a lab challenge submission and update student BKT state.

        Strict Invariant:
        Zero LLM dialogue updates: Any attempt to invoke grading with source_context
        indicating LLM dialogue, conversational assessment, or prompt generation is rejected.
        """
        # Strict LLM dialogue rejection
        prohibited_sources = {"LLM", "LLM_DIALOGUE", "CHAT", "PROMPT", "CONVERSATION", "UNVERIFIED_DIALOGUE"}
        if source_context.upper() in prohibited_sources:
            raise ValueError(
                f"Prohibited grading source: {source_context}. Zero LLM dialogue updates are permitted in cognitive layer (E4-7)."
            )

        with self._lock:
            mapping = self._mappings.get((lab_id.strip(), challenge_id.strip()))

        if not mapping:
            return LabSubmissionResult(
                lab_id=lab_id,
                challenge_id=challenge_id,
                kc_id="UNKNOWN",
                is_correct=False,
                status_code="UNKNOWN_CHALLENGE",
                details={"error": f"Challenge '{challenge_id}' in lab '{lab_id}' is not in lab_kc_map.json"},
            )

        # Hash verification
        submitted_clean = submitted_flag.strip()
        computed_hash = hashlib.sha256(submitted_clean.encode("utf-8")).hexdigest()
        is_correct = (computed_hash == mapping.expected_flag_hash)

        # Construct deterministic ObservationPayload
        payload = ObservationPayload(
            kc_id=mapping.kc_id,
            correct=is_correct,
            source=ObservationSource.EXACT_CORRECTOR,
            format=mapping.exercise_format,
            n_options=None,
        )

        # Propagate to BKT and LagunaDetector
        bkt_state: Optional[BKTState] = None
        interrupt: Optional[RemediationInterrupt] = None

        if self.observation_bridge:
            # Atomic update through ObservationBridge
            topic_for_laguna = current_topic_id or mapping.kc_id
            interrupt = self.observation_bridge.laguna_detector.check_after_exercise(
                kc_id_or_payload=payload,
                current_topic_id=topic_for_laguna,
            )
            bkt_state = self.observation_bridge.bkt.get_state(mapping.kc_id)
        else:
            # Direct BKT update
            bkt_state = self.bkt_tracker.update(payload)

        return LabSubmissionResult(
            lab_id=lab_id,
            challenge_id=challenge_id,
            kc_id=mapping.kc_id,
            is_correct=is_correct,
            status_code="CORRECT" if is_correct else "INCORRECT",
            details={
                "submitted_hash": computed_hash,
                "expected_hash": mapping.expected_flag_hash,
                "weight": mapping.weight,
            },
            bkt_state=bkt_state,
            interrupt=interrupt,
        )
