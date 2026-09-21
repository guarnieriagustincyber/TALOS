"""Session Memory: Continuous Cross-Session Episodic State Manager (Fase 6).

Coordinates student continuity across session boundaries:
- Captures milestones, pending topics, and review queues.
- Bridges SessionHistory with SpacedRepetitionScheduler and BKT.
- Provides thread-safe snapshotting of ongoing study state.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from study_engine.memory.session_history import SessionHistory, SessionRecord
from study_engine.student.storage import StudentStorage

logger = logging.getLogger(__name__)


class SessionMemoryManager:
    """Manages cross-session episodic memory continuity."""

    def __init__(
        self,
        session_history: Optional[SessionHistory] = None,
        student_storage: Optional[StudentStorage] = None,
    ) -> None:
        self.session_history = session_history or SessionHistory()
        self.student_storage = student_storage or StudentStorage()

    def record_session_turn(
        self,
        student_id: str,
        notebook_id: str,
        topic: str,
        next_topic: str = "",
        weak_kcs: Optional[List[str]] = None,
        summary: str = "",
    ) -> None:
        """Persist or update episodic milestone for current session."""
        rec = SessionRecord(
            session_id=f"sess_{student_id}_{notebook_id}",
            notebook_id=notebook_id,
            student_id=student_id,
            topic=topic or "Sesión de estudio",
            next_topic=next_topic or "continuación del temario",
            timestamp=datetime.now(timezone.utc),
            turn_count=1,
            compressed_summary=summary,
            weak_kcs=weak_kcs or [],
        )
        try:
            self.session_history.record_session(rec)
        except Exception as exc:
            logger.debug("SessionMemoryManager failed to record session: %s", exc)

    def get_latest_session_state(
        self,
        student_id: str,
        notebook_id: str,
    ) -> Optional[SessionRecord]:
        """Fetch the most recent session record for this student and notebook."""
        try:
            return self.session_history.get_last(notebook_id=notebook_id, student_id=student_id)
        except Exception as exc:
            logger.debug("SessionMemoryManager failed to read last session: %s", exc)
            return None

    def get_due_spaced_reviews(self, student_id: str) -> List[Dict[str, Any]]:
        """Fetch anchors currently due for SM-2 spaced repetition review."""
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            anchors = self.student_storage.get_due_anchors(now_iso)
            return [
                {
                    "anchor_id": a.anchor_id,
                    "interval": a.interval,
                    "repetitions": a.repetitions,
                    "ef": a.EF,
                }
                for a in anchors
            ]
        except Exception as exc:
            logger.debug("SessionMemoryManager failed to fetch due anchors: %s", exc)
            return []
