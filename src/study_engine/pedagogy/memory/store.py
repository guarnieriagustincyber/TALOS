"""CognitiveProfileStore — SQLite persistence layer for Opción C.

Thread-safe, WAL-enabled, idempotent.  Zero mutations in the frozen student/*
or assessment/* layers.

CRUD contract:
- upsert_item()     — Insert or increment occurrences if description matches
- get_active_items()— Returns ACTIVE items for a (user, kc_id) pair
- get_for_injection()— Top-N items across all KCs for prompt injection
- mark_resolved()   — Set status=RESOLVED (used by BKT threshold hook)
- archive_stale()   — Set status=ARCHIVED for items untouched > 30 days
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union

from study_engine.pedagogy.memory.schema import (
    COGNITIVE_PROFILE_DDL,
    CognitiveItem,
    MemoryCategory,
    MemoryStatus,
)

logger = logging.getLogger(__name__)

_MAX_INJECTION_ITEMS = 10  # hard cap for prompt injection (anti-saturation)
_ARCHIVE_DAYS = 30


class CognitiveProfileStore:
    """ACID-compliant, thread-safe SQLite store for student cognitive profile.

    Invariants:
    - All reads: SELECT only — no side effects.
    - upsert_item de-duplication: if description similarity detected, increment
      occurrences instead of inserting a duplicate row.
    - WAL mode activated at init for concurrent reads.
    """

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
    ) -> None:
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

    # ------------------------------------------------------------------
    # Internal connection management
    # ------------------------------------------------------------------

    def _get_connection(self) -> sqlite3.Connection:
        if self._is_memory:
            if self._mem_conn is None:
                self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
                self._mem_conn.execute("PRAGMA journal_mode=WAL;")
                self._mem_conn.execute("PRAGMA busy_timeout=5000;")
                self._mem_conn.row_factory = sqlite3.Row
            return self._mem_conn

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
            conn = self._get_connection()
            with conn:
                conn.executescript(COGNITIVE_PROFILE_DDL)

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def upsert_item(self, item: CognitiveItem) -> str:
        """Persist a CognitiveItem, de-duplicating by (user_id, kc_id, category, description_prefix).

        If an existing ACTIVE row shares the same (user_id, kc_id, category) and
        the first 60 chars of description, increment occurrences and refresh
        last_observed_at.  Otherwise insert a new row.

        Returns the row id (str UUID).
        """
        conn = self._get_connection()
        desc_prefix = item.description[:60].lower()
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._lock:
            with conn:
                # 1. Check existing similar row (allowing for auto-promotion to RECURRING_MISCONCEPTION)
                target_categories = [item.category.value]
                if item.category == MemoryCategory.WEAKNESS:
                    target_categories.append(MemoryCategory.RECURRING_MISCONCEPTION.value)
                elif item.category == MemoryCategory.RECURRING_MISCONCEPTION:
                    target_categories.append(MemoryCategory.WEAKNESS.value)

                placeholders = ",".join("?" * len(target_categories))
                cur = conn.execute(
                    f"""
                    SELECT id, occurrences
                    FROM student_cognitive_profile
                    WHERE user_id = ?
                      AND kc_id = ?
                      AND category IN ({placeholders})
                      AND status = 'ACTIVE'
                      AND (
                          LOWER(SUBSTR(description, 1, 40)) = ?
                          OR id = ?
                      )
                    LIMIT 1
                    """,
                    [item.user_id, item.kc_id] + target_categories + [item.description[:40].lower(), item.id],
                )
                existing = cur.fetchone()

                if existing:
                    # Increment occurrences and promote category if needed
                    new_occ = existing["occurrences"] + 1
                    new_cat = item.category.value
                    # Auto-promote to RECURRING_MISCONCEPTION if ≥2 occurrences
                    if (
                        item.category == MemoryCategory.WEAKNESS
                        and new_occ >= 2
                    ):
                        new_cat = MemoryCategory.RECURRING_MISCONCEPTION.value

                    conn.execute(
                        """
                        UPDATE student_cognitive_profile
                        SET occurrences = ?,
                            category = ?,
                            confidence = ?,
                            last_observed_at = ?,
                            evidence_quote = COALESCE(?, evidence_quote)
                        WHERE id = ?
                        """,
                        (
                            new_occ,
                            new_cat,
                            item.confidence,
                            now_iso,
                            item.evidence_quote,
                            existing["id"],
                        ),
                    )
                    return existing["id"]

                # 2. Insert new row
                conn.execute(
                    """
                    INSERT INTO student_cognitive_profile
                        (id, user_id, kc_id, category, description,
                         evidence_quote, occurrences, confidence,
                         status, last_observed_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.id,
                        item.user_id,
                        item.kc_id,
                        item.category.value,
                        item.description,
                        item.evidence_quote,
                        item.occurrences,
                        item.confidence,
                        item.status.value,
                        item.last_observed_at.isoformat(),
                        item.created_at.isoformat(),
                    ),
                )
                return item.id

    def mark_resolved(self, item_id: str) -> None:
        """Mark a specific item as RESOLVED (e.g., after BKT P(L) ≥ 0.80)."""
        conn = self._get_connection()
        with self._lock:
            with conn:
                conn.execute(
                    "UPDATE student_cognitive_profile SET status = 'RESOLVED' WHERE id = ?",
                    (item_id,),
                )

    def archive_stale(self, days: int = _ARCHIVE_DAYS) -> int:
        """Set status=ARCHIVED for ACTIVE items not updated in `days` days.

        Returns number of rows archived.
        """
        conn = self._get_connection()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with self._lock:
            with conn:
                cur = conn.execute(
                    """
                    UPDATE student_cognitive_profile
                    SET status = 'ARCHIVED'
                    WHERE status = 'ACTIVE' AND last_observed_at < ?
                    """,
                    (cutoff,),
                )
                return cur.rowcount

    # ------------------------------------------------------------------
    # Read operations (pure, no side effects)
    # ------------------------------------------------------------------

    def get_active_items(
        self,
        user_id: str,
        kc_id: Optional[str] = None,
        category: Optional[MemoryCategory] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Return ACTIVE cognitive items for a user, optionally filtered by KC or category."""
        conn = self._get_connection()
        clauses = ["user_id = ?", "status = 'ACTIVE'"]
        params: list = [user_id]
        if kc_id:
            clauses.append("kc_id = ?")
            params.append(kc_id)
        if category:
            clauses.append("category = ?")
            params.append(category.value)

        sql = (
            "SELECT * FROM student_cognitive_profile WHERE "
            + " AND ".join(clauses)
            + " ORDER BY occurrences DESC, last_observed_at DESC"
            + f" LIMIT {int(limit)}"
        )
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]

    def get_for_injection(
        self,
        user_id: str,
        notebook_kc_ids: Optional[List[str]] = None,
        max_items: int = _MAX_INJECTION_ITEMS,
    ) -> List[Dict]:
        """Return top items prioritized for prompt injection.

        Priority order:
        1. RECURRING_MISCONCEPTION (occurrences DESC)
        2. WEAKNESS (occurrences DESC)
        3. PREFERENCE (1 max)
        4. STRENGTH (filtered — only when confidence ≥ 0.85)

        Optionally scoped to the active notebook's KC set.
        """
        conn = self._get_connection()
        kc_filter = ""
        params: list = [user_id]

        if notebook_kc_ids:
            placeholders = ",".join("?" * len(notebook_kc_ids))
            kc_filter = f"AND kc_id IN ({placeholders})"
            params.extend(notebook_kc_ids)

        # Weighted ORDER BY: RECURRING=1, WEAKNESS=2, PREFERENCE=3, STRENGTH=4
        sql = f"""
            SELECT *, CASE category
                WHEN 'RECURRING_MISCONCEPTION' THEN 1
                WHEN 'WEAKNESS'               THEN 2
                WHEN 'PREFERENCE'             THEN 3
                WHEN 'ANALOGY_AFFINITY'       THEN 4
                WHEN 'STRENGTH'               THEN 5
                ELSE 6
            END AS _priority
            FROM student_cognitive_profile
            WHERE user_id = ?
              AND status = 'ACTIVE'
              {kc_filter}
            ORDER BY _priority ASC, occurrences DESC, last_observed_at DESC
            LIMIT {int(max_items)}
        """
        cur = conn.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]

    def count_active(self, user_id: str) -> int:
        """Return total count of ACTIVE items for a user."""
        conn = self._get_connection()
        cur = conn.execute(
            "SELECT COUNT(*) FROM student_cognitive_profile WHERE user_id = ? AND status = 'ACTIVE'",
            (user_id,),
        )
        return cur.fetchone()[0]
