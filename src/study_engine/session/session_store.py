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

from study_engine.pedagogy.episode_contracts import Episode, EpisodePhase

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
CREATE TABLE IF NOT EXISTS study_episodes (
    episode_id   TEXT PRIMARY KEY NOT NULL,
    session_id   TEXT,
    notebook_id  TEXT NOT NULL,
    kc_id        TEXT NOT NULL,
    episode_blob TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_episodes_notebook ON study_episodes(notebook_id);
CREATE INDEX IF NOT EXISTS idx_episodes_kc ON study_episodes(kc_id);
CREATE TABLE IF NOT EXISTS turn_receipt_operations (
    session_id     TEXT NOT NULL,
    input_id       TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    status         TEXT NOT NULL CHECK(status IN ('IN_PROGRESS', 'COMPLETED')),
    receipt_blob   TEXT,
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL,
    PRIMARY KEY (session_id, input_id)
);
CREATE INDEX IF NOT EXISTS idx_turn_receipts_assessment ON turn_receipt_operations(status);
"""


class SessionStore:
    """Thread-safe SQLite store for AuthoritativeSessionState serialization."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        if db_path is None:
            repo_root = Path(__file__).resolve().parents[3]
            self.db_path = repo_root / "data" / "student" / "sessions.db"
        else:
            self.db_path = Path(db_path).resolve()
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
            episode_columns = {
                row[1] for row in conn.execute("PRAGMA table_info(study_episodes)").fetchall()
            }
            if "session_id" not in episode_columns:
                conn.execute("ALTER TABLE study_episodes ADD COLUMN session_id TEXT")
            conn.commit()
            conn.commit()

    def upsert(self, state_dict: Dict) -> None:
        """Persist or update a session state from its serialized dict."""
        required = ("session_id", "notebook_id", "student_id")
        if any(not isinstance(state_dict.get(key), str) or not state_dict[key].strip() for key in required):
            raise ValueError("Session persistence requires non-empty session, notebook, and student identities.")
        session_id = state_dict["session_id"]
        now = datetime.now(timezone.utc).isoformat()
        blob = json.dumps(state_dict, default=str, sort_keys=True)
        is_closed = 1 if state_dict.get("episode_phase") == "CLOSED" else 0
        with self._lock:
            conn = self._get_conn()
            with conn:
                existing = conn.execute(
                    "SELECT notebook_id, student_id, created_at FROM study_sessions WHERE session_id = ?",
                    (session_id,),
                ).fetchone()
                state_created_at = str(state_dict.get("created_at", now))
                if existing and (
                    existing[0] != state_dict["notebook_id"]
                    or existing[1] != state_dict["student_id"]
                    or existing[2] != state_created_at
                ):
                    raise ValueError(f"Session identity conflict for '{session_id}'.")
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
                    WHERE study_sessions.is_closed = 0 OR excluded.is_closed = 1
                    """,
                    (
                        session_id,
                        state_dict["notebook_id"],
                        state_dict["student_id"],
                        state_dict.get("episode_phase", ""),
                        blob,
                        state_created_at,
                        now,
                        is_closed,
                    ),
                )
                if conn.execute("SELECT changes()").fetchone()[0] == 0:
                    raise ValueError(f"Closed session '{session_id}' cannot be reopened.")

    def load_all_active(self) -> List[Dict]:
        """Return all non-closed session blobs for rehydration on startup."""
        with self._lock:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT session_id, notebook_id, student_id, state_blob "
                "FROM study_sessions WHERE is_closed = 0"
            ).fetchall()
        result = []
        for row in rows:
            try:
                state = json.loads(row["state_blob"])
                for key in ("session_id", "notebook_id", "student_id"):
                    if key not in state or not state[key]:
                        state[key] = row[key]
                if any(
                    state.get(key) != row[key]
                    for key in ("session_id", "notebook_id", "student_id")
                ):
                    raise ValueError("Session row identity does not match serialized state.")
                result.append(state)
            except Exception as exc:
                logger.warning("SessionStore: invalid active session skipped — %s", exc)
        return result

    def load_session(self, session_id: str) -> Optional[Dict]:
        """Read one active or archived session without changing its lifecycle."""
        with self._lock:
            row = self._get_conn().execute(
                "SELECT session_id, notebook_id, student_id, state_blob, is_closed FROM study_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        state = json.loads(row["state_blob"])
        if any(state.get(key) != row[key] for key in ("session_id", "notebook_id", "student_id")):
            raise ValueError("Session row identity does not match serialized state.")
        if bool(row["is_closed"]) != (state.get("episode_phase") == "CLOSED"):
            raise ValueError("Session closure flag does not match serialized state.")
        return state

    def save_episode(self, episode: Episode) -> Episode:
        """Durably persist an episode without allowing its canonical scope to change."""
        if not isinstance(episode, Episode):
            raise TypeError("SessionStore.save_episode requires an Episode.")
        blob = json.dumps(
            {
                "episode_id": episode.episode_id,
                "session_id": episode.session_id,
                "notebook_id": episode.notebook_id,
                "kc_id": episode.kc_id,
                "objective": episode.objective,
                "phase": episode.phase.value,
                "current_step_id": episode.current_step_id,
                "created_at": episode.created_at.isoformat(),
                "idempotency_keys_consumed": sorted(episode.idempotency_keys_consumed),
                "metadata": episode.metadata,
            },
            sort_keys=True,
            default=str,
        )
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_conn()
            with conn:
                existing = conn.execute(
                    "SELECT notebook_id, kc_id, session_id, episode_blob FROM study_episodes WHERE episode_id = ?",
                    (episode.episode_id,),
                ).fetchone()
                if existing:
                    existing_blob = json.loads(existing[3])
                    if (
                        existing[0] != episode.notebook_id
                        or existing[1] != episode.kc_id
                        or existing[2] != episode.session_id
                        or existing_blob.get("objective") != episode.objective
                        or existing_blob.get("created_at") != episode.created_at.isoformat()
                    ):
                        raise ValueError(f"Episode identity conflict for '{episode.episode_id}'.")
                conn.execute(
                    """
                    INSERT INTO study_episodes
                        (episode_id, notebook_id, kc_id, session_id, episode_blob, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(episode_id) DO UPDATE SET
                        episode_blob = excluded.episode_blob,
                        updated_at = excluded.updated_at
                    """,
                    (episode.episode_id, episode.notebook_id, episode.kc_id, episode.session_id, blob, now),
                )
        return episode

    def load_episode(self, episode_id: str) -> Optional[Episode]:
        """Load one episode and verify its indexed identity against its durable payload."""
        with self._lock:
            row = self._get_conn().execute(
                """SELECT notebook_id, kc_id, session_id, episode_blob
                   FROM study_episodes WHERE episode_id = ?""",
                (episode_id,),
            ).fetchone()
        if row is None:
            return None
        try:
            blob = json.loads(row["episode_blob"])
            if (
                blob.get("episode_id") != episode_id
                or blob.get("notebook_id") != row["notebook_id"]
                or blob.get("kc_id") != row["kc_id"]
                or blob.get("session_id") != row["session_id"]
            ):
                raise ValueError("Episode row identity does not match serialized payload.")
            return Episode(
                episode_id=episode_id,
                notebook_id=row["notebook_id"],
                kc_id=row["kc_id"],
                objective=blob["objective"],
                phase=EpisodePhase(blob["phase"]),
                current_step_id=blob["current_step_id"],
                created_at=datetime.fromisoformat(blob["created_at"]),
                idempotency_keys_consumed=frozenset(blob.get("idempotency_keys_consumed", [])),
                metadata=blob.get("metadata", {}),
                session_id=blob.get("session_id"),
            )
        except Exception as exc:
            logger.warning("SessionStore: invalid episode '%s' not rehydrated — %s", episode_id, exc)
            return None

    def begin_turn_operation(
        self,
        session_id: str,
        input_id: str,
        request_digest: str,
    ) -> tuple[str, Optional[Dict]]:
        """Reserve an operation or return its durable replay/conflict state.

        IN_PROGRESS is deliberately fail-closed after interruption: it prevents
        an automatic second mutation when completion cannot be proven.
        """
        if not session_id or not input_id or len(request_digest) != 64:
            raise ValueError("Turn operation requires session/input identities and a SHA-256 digest.")
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_conn()
            with conn:
                row = conn.execute(
                    """SELECT request_digest, status, receipt_blob
                       FROM turn_receipt_operations WHERE session_id=? AND input_id=?""",
                    (session_id, input_id),
                ).fetchone()
                if row is not None:
                    if row[0] != request_digest:
                        return "CONFLICT", None
                    if row[1] == "COMPLETED" and row[2]:
                        try:
                            return "REPLAY", json.loads(row[2])
                        except (TypeError, json.JSONDecodeError):
                            return "IN_PROGRESS", None
                    return "IN_PROGRESS", None
                conn.execute(
                    """INSERT INTO turn_receipt_operations
                       (session_id, input_id, request_digest, status, receipt_blob, created_at, updated_at)
                       VALUES (?, ?, ?, 'IN_PROGRESS', NULL, ?, ?)""",
                    (session_id, input_id, request_digest, now, now),
                )
        return "STARTED", None

    def complete_turn_operation(self, receipt_payload: Dict) -> None:
        """Commit the completed receipt after its educational operation succeeds."""
        session_id = receipt_payload.get("session_id")
        input_id = receipt_payload.get("input_id")
        request_digest = receipt_payload.get("request_digest")
        if not session_id or not input_id or not isinstance(request_digest, str):
            raise ValueError("Completed turn receipt is missing its identity or request digest.")
        now = datetime.now(timezone.utc).isoformat()
        blob = json.dumps(receipt_payload, sort_keys=True, default=str)
        with self._lock:
            conn = self._get_conn()
            with conn:
                cursor = conn.execute(
                    """UPDATE turn_receipt_operations
                       SET status='COMPLETED', receipt_blob=?, updated_at=?
                       WHERE session_id=? AND input_id=? AND request_digest=? AND status='IN_PROGRESS'""",
                    (blob, now, session_id, input_id, request_digest),
                )
                if cursor.rowcount != 1:
                    raise ValueError("Turn receipt has no matching in-progress reservation.")

    def get_turn_receipt(self, session_id: str, input_id: str) -> Optional[Dict]:
        with self._lock:
            row = self._get_conn().execute(
                """SELECT status, receipt_blob FROM turn_receipt_operations
                   WHERE session_id=? AND input_id=?""",
                (session_id, input_id),
            ).fetchone()
        if row is None or row[0] != "COMPLETED" or not row[1]:
            return None
        try:
            return json.loads(row[1])
        except (TypeError, json.JSONDecodeError):
            return None

    def find_turn_receipt_by_assessment_digest(self, digest: str) -> Optional[Dict]:
        if not digest:
            return None
        with self._lock:
            rows = self._get_conn().execute(
                """SELECT receipt_blob FROM turn_receipt_operations
                   WHERE status='COMPLETED' AND receipt_blob IS NOT NULL"""
            ).fetchall()
        for row in rows:
            try:
                payload = json.loads(row[0])
            except (TypeError, json.JSONDecodeError):
                continue
            if payload.get("assessment_digest") == digest:
                return payload
        return None

    def latest_turn_index(self, session_id: str) -> int:
        """Return the latest completed turn index for one session, or -1."""
        with self._lock:
            rows = self._get_conn().execute(
                """SELECT receipt_blob FROM turn_receipt_operations
                   WHERE session_id=? AND status='COMPLETED' AND receipt_blob IS NOT NULL""",
                (session_id,),
            ).fetchall()
        indices: List[int] = []
        for row in rows:
            try:
                payload = json.loads(row[0])
                value = payload.get("turn_index")
                if isinstance(value, int):
                    indices.append(value)
            except (TypeError, json.JSONDecodeError):
                continue
        return max(indices, default=-1)

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

    def close(self) -> None:
        """Close this thread's SQLite handle; reopening uses the same durable file."""
        with self._lock:
            conn = getattr(self._thread_local, "conn", None)
            if conn is not None:
                conn.close()
                del self._thread_local.conn
