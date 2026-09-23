"""Deterministic SQLite storage engine for Student Cognitive State (Phase E3).

Provides isolated, thread-safe persistence for:
1. `bkt_states`: Bayesian Knowledge Tracing parameters and state per KC.
2. `anchor_states`: Spaced repetition SM-2 states per conceptual anchor.
3. `remediation_choices`: Recorded student remediation selections (H6).
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, List, Optional, Union

from study_engine.config import CANONICAL_STUDENT_ID
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

CREATE TABLE IF NOT EXISTS solution_access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    forced INTEGER NOT NULL DEFAULT 0,
    timestamp TEXT NOT NULL,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS student_exercise_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    success INTEGER DEFAULT 0,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_remediation_topic ON remediation_choices(current_topic_id);
CREATE INDEX IF NOT EXISTS idx_anchor_next_review ON anchor_states(next_review);
CREATE INDEX IF NOT EXISTS idx_hints_episode ON student_hints(episode_id);
CREATE INDEX IF NOT EXISTS idx_hints_exercise ON student_hints(exercise_id);
CREATE INDEX IF NOT EXISTS idx_hints_kc ON student_hints(kc_id);
CREATE INDEX IF NOT EXISTS idx_ped_mem_student_cat ON student_pedagogical_memory(student_id, category);
CREATE INDEX IF NOT EXISTS idx_ped_mem_kc ON student_pedagogical_memory(kc_id);
CREATE INDEX IF NOT EXISTS idx_sol_access_content ON solution_access_log(content_id);
CREATE INDEX IF NOT EXISTS idx_sol_access_student ON solution_access_log(student_id);
CREATE INDEX IF NOT EXISTS idx_ex_attempts_content ON student_exercise_attempts(content_id);
CREATE INDEX IF NOT EXISTS idx_ex_attempts_student ON student_exercise_attempts(student_id);
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

    # -------------------------------------------------------------------------
    # Content Registry & Solution Access Audit (Slice 6.0.5)
    # -------------------------------------------------------------------------
    def record_exercise_attempt(
        self,
        content_id: str,
        student_id: str = CANONICAL_STUDENT_ID,
        success: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Record an attempt made by a student on an exercise (Slice 6.0.5)."""
        now_str = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(metadata) if metadata else None
        conn = self._get_connection()
        with self._lock:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO student_exercise_attempts (content_id, student_id, timestamp, success, metadata)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (content_id, student_id, now_str, 1 if success else 0, meta_json),
                )
                return cursor.lastrowid

    def has_exercise_attempt(self, content_id: str, student_id: str = CANONICAL_STUDENT_ID) -> bool:
        """Check if student has recorded at least one attempt for this content unit."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM student_exercise_attempts WHERE content_id = ? AND student_id = ?",
            (content_id, student_id),
        )
        row = cursor.fetchone()
        if row and row[0] > 0:
            return True

        # Check hints table for matching exercise_id
        cursor.execute(
            "SELECT COUNT(*) FROM student_hints WHERE exercise_id = ?",
            (content_id,),
        )
        row = cursor.fetchone()
        if row and row[0] > 0:
            return True

        return False

    def log_solution_access(
        self,
        content_id: str,
        student_id: str = CANONICAL_STUDENT_ID,
        forced: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Log access to a solution in solution_access_log (Slice 6.0.5)."""
        now_str = datetime.now(timezone.utc).isoformat()
        meta_json = json.dumps(metadata) if metadata else None
        conn = self._get_connection()
        with self._lock:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO solution_access_log (content_id, student_id, forced, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (content_id, student_id, 1 if forced else 0, now_str, meta_json),
                )
                return cursor.lastrowid

    def get_solution_access_logs(
        self,
        content_id: Optional[str] = None,
        student_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query logged solution accesses."""
        conn = self._get_connection()
        cursor = conn.cursor()
        query = "SELECT id, content_id, student_id, forced, timestamp, metadata FROM solution_access_log WHERE 1=1"
        params: List[Any] = []
        if content_id:
            query += " AND content_id = ?"
            params.append(content_id)
        if student_id:
            query += " AND student_id = ?"
            params.append(student_id)
        query += " ORDER BY id DESC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [
            {
                "id": r[0],
                "content_id": r[1],
                "student_id": r[2],
                "forced": bool(r[3]),
                "timestamp": r[4],
                "metadata": json.loads(r[5]) if r[5] else None,
            }
            for r in rows
        ]

    def calculate_solution_dependency(
        self,
        student_id: str = CANONICAL_STUDENT_ID,
    ) -> Dict[str, Any]:
        """Calcula el perfil de dependencia de solucionario y autonomía metacognitiva (Slice 6.0.6 / M1-M10)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, content_id, forced, metadata FROM solution_access_log WHERE student_id = ?",
            (student_id,),
        )
        sol_rows = cursor.fetchall()

        cursor.execute(
            "SELECT id, content_id, success, metadata FROM student_exercise_attempts WHERE student_id = ?",
            (student_id,),
        )
        att_rows = cursor.fetchall()

        total_attempts = len(att_rows)
        successful_attempts = sum(1 for r in att_rows if r[2] == 1)
        total_solutions = len(sol_rows)
        forced_solutions = sum(1 for r in sol_rows if r[2] == 1)

        # M7: Cold start estricto
        if total_attempts == 0 and total_solutions == 0:
            return {
                "student_id": student_id,
                "total_attempts": 0,
                "successful_attempts": 0,
                "total_solutions": 0,
                "forced_solutions": 0,
                "ratio": 0.0,
                "raw_ratio": 0.0,
                "classification": "moderada",  # Neutral por defecto
                "autonomy_score": 0.5,
                "evasion_kcs": [],
                "overconfident_kcs": [],
                "is_overconfident": False,
            }

        # M2: Cálculo de ratio y clasificación
        if total_solutions == 0:
            ratio = float("inf") if total_attempts > 0 else 0.0
            classification = "baja"
        else:
            ratio = round(total_attempts / total_solutions, 4)
            if ratio < 2.0 or total_attempts == 0:
                classification = "alta"
            elif 2.0 <= ratio <= 5.0:
                classification = "moderada"
            else:
                classification = "baja"

        autonomy_score = calculate_autonomy_score(
            total_attempts, total_solutions, ratio if ratio != float("inf") else 10.0
        )

        # M1: Agregación por KC y umbrales de evasión / sobreconfianza
        kc_stats: Dict[str, Dict[str, int]] = {}

        def _record_kc(kc: str, is_attempt: bool, is_success: bool, is_solution: bool) -> None:
            if not kc:
                return
            if kc not in kc_stats:
                kc_stats[kc] = {
                    "attempts": 0,
                    "successful_attempts": 0,
                    "solutions": 0,
                }
            if is_attempt:
                kc_stats[kc]["attempts"] += 1
                if is_success:
                    kc_stats[kc]["successful_attempts"] += 1
            if is_solution:
                kc_stats[kc]["solutions"] += 1

        for r in att_rows:
            meta = json.loads(r[3]) if r[3] else {}
            kcs = meta.get("kc_ids") or ([meta.get("kc_id")] if meta.get("kc_id") else [])
            for k in kcs:
                _record_kc(str(k), is_attempt=True, is_success=(r[2] == 1), is_solution=False)

        for r in sol_rows:
            meta = json.loads(r[3]) if r[3] else {}
            kcs = meta.get("kc_ids") or ([meta.get("kc_id")] if meta.get("kc_id") else [])
            for k in kcs:
                _record_kc(str(k), is_attempt=False, is_success=False, is_solution=True)

        evasion_kcs = [
            kc_id for kc_id, stats in sorted(kc_stats.items())
            if stats["attempts"] >= 2
            and (stats["solutions"] / stats["attempts"]) > 0.5
        ]

        overconfident_kcs = [
            kc_id for kc_id, stats in sorted(kc_stats.items())
            if stats["attempts"] >= 3
            and stats["successful_attempts"] == 0
            and stats["solutions"] == 0
        ]

        return {
            "student_id": student_id,
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "total_solutions": total_solutions,
            "forced_solutions": forced_solutions,
            "ratio": 0.0 if ratio == float("inf") else ratio,
            "raw_ratio": ratio,
            "classification": classification,
            "autonomy_score": autonomy_score,
            "evasion_kcs": evasion_kcs,
            "overconfident_kcs": overconfident_kcs,
            "is_overconfident": len(overconfident_kcs) > 0,
        }


def calculate_autonomy_score(total_attempts: int, total_solutions: int, ratio: float) -> float:
    """Calcula el score de autonomía (0.0 a 1.0) conforme a M2."""
    if total_solutions == 0 and total_attempts == 0:
        return 0.5  # Cold start neutral
    elif total_solutions == 0 and total_attempts > 0:
        return 1.0  # Alta autonomía (nunca pidió solución)
    else:
        return min(1.0, round(ratio / 10.0, 4))  # Escala lineal hasta ratio=10

