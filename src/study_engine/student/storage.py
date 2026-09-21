"""Deterministic SQLite storage engine for Student Cognitive State (Phase E3).

Provides isolated, thread-safe persistence for:
1. `bkt_states`: Bayesian Knowledge Tracing parameters and state per KC.
2. `anchor_states`: Spaced repetition SM-2 states per conceptual anchor.
3. `remediation_choices`: Recorded student remediation selections (H6).
"""

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, List, Optional, Union

from study_engine.student.contracts import (
    AnchorState,
    BKTState,
    RemediationInterrupt,
    RemediationOption,
)

STUDENT_SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS bkt_states (
    kc_id TEXT PRIMARY KEY NOT NULL,
    p_L REAL NOT NULL,
    p_T REAL NOT NULL,
    p_G REAL NOT NULL,
    p_S REAL NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_update TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS anchor_states (
    anchor_id TEXT PRIMARY KEY NOT NULL,
    interval INTEGER NOT NULL,
    repetitions INTEGER NOT NULL,
    EF REAL NOT NULL,
    next_review TEXT NOT NULL,
    last_quality INTEGER NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS remediation_choices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kc_id TEXT NOT NULL,
    current_topic_id TEXT NOT NULL,
    p_L REAL NOT NULL,
    reason TEXT NOT NULL,
    chosen_option TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS student_hints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id TEXT NOT NULL,
    exercise_id TEXT NOT NULL,
    kc_id TEXT NOT NULL,
    hint_level INTEGER NOT NULL,
    hint_text TEXT NOT NULL,
    timestamp REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS student_pedagogical_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    category TEXT NOT NULL,
    kc_id TEXT,
    insight TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    last_accessed TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_remediation_topic ON remediation_choices(current_topic_id);
CREATE INDEX IF NOT EXISTS idx_anchor_next_review ON anchor_states(next_review);
CREATE INDEX IF NOT EXISTS idx_hints_episode ON student_hints(episode_id);
CREATE INDEX IF NOT EXISTS idx_hints_exercise ON student_hints(exercise_id);
CREATE INDEX IF NOT EXISTS idx_hints_kc ON student_hints(kc_id);
CREATE INDEX IF NOT EXISTS idx_ped_mem_student_cat ON student_pedagogical_memory(student_id, category);
CREATE INDEX IF NOT EXISTS idx_ped_mem_kc ON student_pedagogical_memory(kc_id);
"""


class StudentStorage:
    """ACID-compliant, thread-safe SQLite persistence for student cognitive state."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        if db_path is None:
            self.db_path = Path("data/student/student_state.db")
            self._is_memory = False
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        elif str(db_path) == ":memory:":
            self.db_path = Path(":memory:")
            self._is_memory = True
        else:
            self.db_path = Path(db_path)
            self._is_memory = False
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._thread_local = threading.local()
        self._mem_conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._is_memory:
            if self._mem_conn is None:
                self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
                self._mem_conn.execute("PRAGMA busy_timeout = 5000;")
            return self._mem_conn

        conn = getattr(self._thread_local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.execute("PRAGMA busy_timeout = 5000;")
            self._thread_local.conn = conn
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_connection()
            with conn:
                conn.executescript(STUDENT_SCHEMA_DDL)

    def get_bkt_state(self, kc_id: str) -> Optional[BKTState]:
        """Fetch BKT state for a knowledge component."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT kc_id, p_L, p_T, p_G, p_S, attempts, last_update FROM bkt_states WHERE kc_id = ?",
            (kc_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return BKTState(
            kc_id=row[0],
            p_L=row[1],
            p_T=row[2],
            p_G=row[3],
            p_S=row[4],
            attempts=row[5],
            last_update=datetime.fromisoformat(row[6]),
        )

    def save_bkt_state(self, state: BKTState) -> None:
        """Upsert BKT state for a knowledge component."""
        with self._lock:
            conn = self._get_connection()
            with conn:
                conn.execute(
                    """
                    INSERT INTO bkt_states (kc_id, p_L, p_T, p_G, p_S, attempts, last_update)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(kc_id) DO UPDATE SET
                        p_L = excluded.p_L,
                        p_T = excluded.p_T,
                        p_G = excluded.p_G,
                        p_S = excluded.p_S,
                        attempts = excluded.attempts,
                        last_update = excluded.last_update
                    """,
                    (
                        state.kc_id,
                        state.p_L,
                        state.p_T,
                        state.p_G,
                        state.p_S,
                        state.attempts,
                        state.last_update.isoformat(),
                    ),
                )

    def get_all_bkt_states(self, limit: Optional[int] = None, offset: int = 0) -> Dict[str, BKTState]:
        """Retrieve all tracked BKT states with optional pagination."""
        conn = self._get_connection()
        cursor = conn.cursor()
        if limit is not None:
            cursor.execute(
                "SELECT kc_id, p_L, p_T, p_G, p_S, attempts, last_update FROM bkt_states LIMIT ? OFFSET ?",
                (limit, offset),
            )
        else:
            cursor.execute("SELECT kc_id, p_L, p_T, p_G, p_S, attempts, last_update FROM bkt_states")
        rows = cursor.fetchall()
        return {
            row[0]: BKTState(
                kc_id=row[0],
                p_L=row[1],
                p_T=row[2],
                p_G=row[3],
                p_S=row[4],
                attempts=row[5],
                last_update=datetime.fromisoformat(row[6]),
            )
            for row in rows
        }

    def get_anchor_state(self, anchor_id: str) -> Optional[AnchorState]:
        """Fetch SM-2 state for a conceptual anchor."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT anchor_id, interval, repetitions, EF, next_review, last_quality, updated_at
            FROM anchor_states WHERE anchor_id = ?
            """,
            (anchor_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return AnchorState(
            anchor_id=row[0],
            interval=row[1],
            repetitions=row[2],
            EF=row[3],
            next_review=datetime.fromisoformat(row[4]),
            last_quality=row[5],
            updated_at=datetime.fromisoformat(row[6]),
        )

    def save_anchor_state(self, state: AnchorState) -> None:
        """Upsert SM-2 state for a conceptual anchor."""
        with self._lock:
            conn = self._get_connection()
            with conn:
                conn.execute(
                    """
                    INSERT INTO anchor_states (anchor_id, interval, repetitions, EF, next_review, last_quality, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(anchor_id) DO UPDATE SET
                        interval = excluded.interval,
                        repetitions = excluded.repetitions,
                        EF = excluded.EF,
                        next_review = excluded.next_review,
                        last_quality = excluded.last_quality,
                        updated_at = excluded.updated_at
                    """,
                    (
                        state.anchor_id,
                        state.interval,
                        state.repetitions,
                        state.EF,
                        state.next_review.isoformat(),
                        state.last_quality,
                        state.updated_at.isoformat(),
                    ),
                )

    def get_all_anchor_states(self, limit: Optional[int] = None, offset: int = 0) -> Dict[str, AnchorState]:
        """Fetch all conceptual anchor states with optional pagination."""
        conn = self._get_connection()
        cursor = conn.cursor()
        if limit is not None:
            cursor.execute(
                """
                SELECT anchor_id, interval, repetitions, EF, next_review, last_quality, updated_at
                FROM anchor_states LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
        else:
            cursor.execute(
                """
                SELECT anchor_id, interval, repetitions, EF, next_review, last_quality, updated_at
                FROM anchor_states
                """
            )
        rows = cursor.fetchall()
        return {
            row[0]: AnchorState(
                anchor_id=row[0],
                interval=row[1],
                repetitions=row[2],
                EF=row[3],
                next_review=datetime.fromisoformat(row[4]),
                last_quality=row[5],
                updated_at=datetime.fromisoformat(row[6]),
            )
            for row in rows
        }

    def record_remediation_choice(
        self,
        interrupt: RemediationInterrupt,
        chosen_option: RemediationOption,
    ) -> None:
        """Record student remediation choice in local student state (H6)."""
        with self._lock:
            conn = self._get_connection()
            with conn:
                conn.execute(
                    """
                    INSERT INTO remediation_choices (kc_id, current_topic_id, p_L, reason, chosen_option, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        interrupt.kc_id,
                        interrupt.current_topic_id,
                        interrupt.p_L,
                        interrupt.reason,
                        chosen_option.value,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )

    def get_remediation_choices(self, topic_id: Optional[str] = None) -> List[Dict[str, Union[str, float]]]:
        """Query recorded remediation selections."""
        conn = self._get_connection()
        cursor = conn.cursor()
        if topic_id:
            cursor.execute(
                """
                SELECT kc_id, current_topic_id, p_L, reason, chosen_option, created_at
                FROM remediation_choices WHERE current_topic_id = ? ORDER BY id DESC
                """,
                (topic_id,),
            )
        else:
            cursor.execute(
                """
                SELECT kc_id, current_topic_id, p_L, reason, chosen_option, created_at
                FROM remediation_choices ORDER BY id DESC
                """
            )
        rows = cursor.fetchall()
        return [
            {
                "kc_id": r[0],
                "current_topic_id": r[1],
                "p_L": r[2],
                "reason": r[3],
                "chosen_option": r[4],
                "created_at": r[5],
            }
            for r in rows
        ]

    def record_hint(
        self,
        episode_id: str,
        exercise_id: str,
        kc_id: str,
        hint_level: int,
        hint_text: str,
    ) -> int:
        """Record a socratic hint given to the student for auditability (E15, E18)."""
        import time
        ts = time.time()
        conn = self._get_connection()
        with self._lock:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO student_hints (episode_id, exercise_id, kc_id, hint_level, hint_text, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (episode_id, exercise_id, kc_id, hint_level, hint_text, ts),
                )
                return cursor.lastrowid

    def get_hints_for_exercise(self, exercise_id: str) -> List[Dict[str, Union[str, int, float]]]:
        """Retrieve all hints recorded for an exercise candidate."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT hint_level, hint_text, timestamp, episode_id, kc_id
            FROM student_hints
            WHERE exercise_id = ?
            ORDER BY hint_level ASC
            """,
            (exercise_id,),
        )
        rows = cursor.fetchall()
        return [
            {
                "hint_level": r[0],
                "hint_text": r[1],
                "timestamp": r[2],
                "episode_id": r[3],
                "kc_id": r[4],
            }
            for r in rows
        ]

    def count_hints(self, episode_id: str) -> int:
        """Count total hints emitted in an episode."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM student_hints WHERE episode_id = ?",
            (episode_id,),
        )
        row = cursor.fetchone()
        return row[0] if row else 0

    # -------------------------------------------------------------------------
    # Pedagogical Memory (Fase 3: Memoria Soberana del Estudiante)
    # -------------------------------------------------------------------------
    def save_pedagogical_memory(
        self,
        student_id: str,
        category: str,
        insight: str,
        kc_id: Optional[str] = None,
        confidence: float = 1.0,
    ) -> int:
        """Persist a qualitative pedagogical memory or learning pattern."""
        now_str = datetime.now(timezone.utc).isoformat()
        conn = self._get_connection()
        with self._lock:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO student_pedagogical_memory (
                        student_id, category, kc_id, insight, confidence, created_at, last_accessed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (student_id, category, kc_id, insight, float(confidence), now_str, now_str),
                )
                return cursor.lastrowid

    def get_pedagogical_memories(
        self,
        student_id: str,
        category: Optional[str] = None,
        kc_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Fetch qualitative insights for a student ordered by most recent activity."""
        conn = self._get_connection()
        cursor = conn.cursor()
        query = (
            "SELECT id, student_id, category, kc_id, insight, confidence, created_at, last_accessed "
            "FROM student_pedagogical_memory WHERE student_id = ?"
        )
        params: List[Any] = [student_id]
        if category:
            query += " AND category = ?"
            params.append(category)
        if kc_id:
            query += " AND kc_id = ?"
            params.append(kc_id)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [
            {
                "id": r[0],
                "student_id": r[1],
                "category": r[2],
                "kc_id": r[3],
                "insight": r[4],
                "confidence": r[5],
                "created_at": r[6],
                "last_accessed": r[7],
            }
            for r in rows
        ]

    def touch_pedagogical_memory(self, memory_id: int) -> bool:
        """Update last_accessed timestamp of a memory record."""
        now_str = datetime.now(timezone.utc).isoformat()
        conn = self._get_connection()
        with self._lock:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE student_pedagogical_memory SET last_accessed = ? WHERE id = ?",
                    (now_str, memory_id),
                )
                return cursor.rowcount > 0

    def delete_pedagogical_memory(self, memory_id: int) -> bool:
        """Remove a pedagogical memory record by ID."""
        conn = self._get_connection()
        with self._lock:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM student_pedagogical_memory WHERE id = ?",
                    (memory_id,),
                )
                return cursor.rowcount > 0
