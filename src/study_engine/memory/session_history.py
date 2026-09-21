"""SessionHistory: Cross-session episodic memory persistence (Ola 6, Fase 6.3).

Persists student session progress, topics treated, next topics, and turn summaries.
Invariants:
- Isolation per notebook: A notebook never accesses sessions from another notebook.
- Thread-safe SQLite persistence with in-memory support (:memory:).
- Deterministic retrieval ordered by timestamp descending.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import threading
from typing import Dict, List, Optional, Union


@dataclass(frozen=True)
class SessionRecord:
    """Episodic record of a completed or active study session."""
    session_id: str
    notebook_id: str
    topic: str
    next_topic: str
    student_id: str = "default_student"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    turn_count: int = 0
    compressed_summary: str = ""
    weak_kcs: List[str] = field(default_factory=list)
    hints_requested: int = 0


SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS session_records (
    session_id TEXT PRIMARY KEY NOT NULL,
    notebook_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    next_topic TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    turn_count INTEGER NOT NULL DEFAULT 0,
    compressed_summary TEXT NOT NULL DEFAULT '',
    weak_kcs_json TEXT NOT NULL DEFAULT '[]',
    hints_requested INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_session_nb_student ON session_records(notebook_id, student_id, timestamp);
"""


class SessionHistory:
    """Episodic session history repository with strict per-notebook isolation."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        self._lock = threading.RLock()
        if db_path is None or str(db_path) == ":memory:":
            self.db_path = ":memory:"
            self._is_memory = True
            self._mem_conn: Optional[sqlite3.Connection] = sqlite3.connect(":memory:", check_same_thread=False)
            self._mem_conn.execute("PRAGMA busy_timeout = 5000;")
            self._init_db(self._mem_conn)
        else:
            self.db_path = Path(db_path)
            self._is_memory = False
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with self._get_connection() as conn:
                self._init_db(conn)

    def _get_connection(self) -> sqlite3.Connection:
        if self._is_memory and self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def _init_db(self, conn: sqlite3.Connection) -> None:
        with conn:
            conn.executescript(SCHEMA_DDL)

    def record_session(self, record: SessionRecord) -> None:
        """Persist a session record."""
        with self._lock:
            conn = self._get_connection()
            with conn:
                conn.execute(
                    """
                    INSERT INTO session_records (
                        session_id, notebook_id, student_id, topic, next_topic,
                        timestamp, turn_count, compressed_summary, weak_kcs_json, hints_requested
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        topic = excluded.topic,
                        next_topic = excluded.next_topic,
                        timestamp = excluded.timestamp,
                        turn_count = excluded.turn_count,
                        compressed_summary = excluded.compressed_summary,
                        weak_kcs_json = excluded.weak_kcs_json,
                        hints_requested = excluded.hints_requested
                    """,
                    (
                        record.session_id,
                        record.notebook_id,
                        record.student_id,
                        record.topic,
                        record.next_topic,
                        record.timestamp.isoformat(),
                        record.turn_count,
                        record.compressed_summary,
                        json.dumps(record.weak_kcs),
                        record.hints_requested,
                    ),
                )

    def get_last(
        self,
        notebook_id: str,
        student_id: Optional[str] = None,
    ) -> Optional[SessionRecord]:
        """Fetch the most recent session for a specific notebook (strict isolation)."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            if student_id:
                cursor.execute(
                    """
                    SELECT session_id, notebook_id, student_id, topic, next_topic,
                           timestamp, turn_count, compressed_summary, weak_kcs_json, hints_requested
                    FROM session_records
                    WHERE notebook_id = ? AND (student_id = ? OR student_id = 'default_student')
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """,
                    (notebook_id, student_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT session_id, notebook_id, student_id, topic, next_topic,
                           timestamp, turn_count, compressed_summary, weak_kcs_json, hints_requested
                    FROM session_records
                    WHERE notebook_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """,
                    (notebook_id,),
                )
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_record(row)

    def get_history(
        self,
        notebook_id: str,
        student_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[SessionRecord]:
        """Fetch chronological session history for a notebook (ordered newest first)."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            if student_id:
                cursor.execute(
                    """
                    SELECT session_id, notebook_id, student_id, topic, next_topic,
                           timestamp, turn_count, compressed_summary, weak_kcs_json, hints_requested
                    FROM session_records
                    WHERE notebook_id = ? AND (student_id = ? OR student_id = 'default_student')
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (notebook_id, student_id, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT session_id, notebook_id, student_id, topic, next_topic,
                           timestamp, turn_count, compressed_summary, weak_kcs_json, hints_requested
                    FROM session_records
                    WHERE notebook_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (notebook_id, limit),
                )
            rows = cursor.fetchall()
            return [self._row_to_record(r) for r in rows]

    def _row_to_record(self, row: tuple) -> SessionRecord:
        weak_kcs = []
        try:
            weak_kcs = json.loads(row[8])
        except Exception:
            pass
        return SessionRecord(
            session_id=row[0],
            notebook_id=row[1],
            student_id=row[2],
            topic=row[3],
            next_topic=row[4],
            timestamp=datetime.fromisoformat(row[5]),
            turn_count=row[6],
            compressed_summary=row[7],
            weak_kcs=weak_kcs,
            hints_requested=row[9],
        )
