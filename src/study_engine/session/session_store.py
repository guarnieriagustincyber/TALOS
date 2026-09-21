"""SQLite-backed session store for AuthoritativeSessionState persistence.

Solves the critical bug where all in-progress study sessions were lost on
server restart because the orchestrator only kept them in a Python dict.

INVARIANTS:
1. Sessions are serialized as JSON blobs in SQLite — survives restarts.
2. On orchestrator startup, all non-closed sessions are rehydrated into memory.
3. Thread-safe via a single threading.Lock.
4. Schema is append-only; never destroys existing session rows.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)

_SESSION_SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS study_sessions (
    session_id   TEXT PRIMARY KEY NOT NULL,
    notebook_id  TEXT NOT NULL,
    student_id   TEXT NOT NULL,
    episode_phase TEXT NOT NULL,
    state_blob   TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    is_closed    INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sessions_notebook ON study_sessions(notebook_id);
CREATE INDEX IF NOT EXISTS idx_sessions_student  ON study_sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_sessions_phase    ON study_sessions(episode_phase);
"""


class SessionStore:
    """Thread-safe SQLite store for AuthoritativeSessionState serialization."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        if db_path is None:
            self.db_path = Path("data/student/sessions.db")
        else:
            self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._thread_local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = getattr(self._thread_local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.row_factory = sqlite3.Row
            self._thread_local.conn = conn
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_conn()
            conn.executescript(_SESSION_SCHEMA_DDL)
            conn.commit()

    def upsert(self, state_dict: Dict) -> None:
        """Persist or update a session state from its serialized dict."""
        session_id = state_dict["session_id"]
        now = datetime.now(timezone.utc).isoformat()
        blob = json.dumps(state_dict, default=str)
        is_closed = 1 if state_dict.get("episode_phase") == "CLOSED" else 0
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                """
                INSERT INTO study_sessions
                    (session_id, notebook_id, student_id, episode_phase,
                     state_blob, created_at, updated_at, is_closed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    episode_phase = excluded.episode_phase,
                    state_blob    = excluded.state_blob,
                    updated_at    = excluded.updated_at,
                    is_closed     = excluded.is_closed
                """,
                (
                    session_id,
                    state_dict.get("notebook_id", ""),
                    state_dict.get("student_id", ""),
                    state_dict.get("episode_phase", ""),
                    blob,
                    state_dict.get("created_at", now),
                    now,
                    is_closed,
                ),
            )
            conn.commit()

    def load_all_active(self) -> List[Dict]:
        """Return all non-closed session blobs for rehydration on startup."""
        with self._lock:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT state_blob FROM study_sessions WHERE is_closed = 0"
            ).fetchall()
        result = []
        for row in rows:
            try:
                result.append(json.loads(row["state_blob"]))
            except Exception as exc:
                logger.warning("SessionStore: corrupt blob skipped — %s", exc)
        return result

    def mark_closed(self, session_id: str) -> None:
        """Mark a session as closed so it won't be rehydrated on next startup."""
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "UPDATE study_sessions SET is_closed=1, updated_at=? WHERE session_id=?",
                (now, session_id),
            )
            conn.commit()

    def delete_old_closed(self, keep_days: int = 30) -> int:
        """Housekeeping: remove closed sessions older than keep_days. Returns count deleted."""
        from datetime import timedelta
        cutoff = (datetime.now(timezone.utc) - timedelta(days=keep_days)).isoformat()
        with self._lock:
            conn = self._get_conn()
            cur = conn.execute(
                "DELETE FROM study_sessions WHERE is_closed=1 AND updated_at < ?",
                (cutoff,),
            )
            conn.commit()
        return cur.rowcount
