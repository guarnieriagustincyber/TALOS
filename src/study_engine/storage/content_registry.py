"""Content Registry Repository (Slice 6.0.5, Puntos 2 y 3).

Provides persistence and query access for exact-identity ContentItem entities.
Enforces:
1. Universal presentation filtering inside chunk accessor methods (no unfiltered accessor exists).
2. Explicit cache invalidation on save() and backfill batches with lazy reconstruction.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from study_engine.contracts.content_registry import ContentItem, ContentStatus, UnitType
from study_engine.retrieval.presentation_filter import filter_presentation
from study_engine.storage.sqlite_engine import SQLiteStorageEngine

logger = logging.getLogger(__name__)


class ContentRegistryRepository:
    """Repository managing content_registry table in knowledge_store.db."""

    def __init__(self, engine: SQLiteStorageEngine) -> None:
        self.engine = engine
        self._solution_chunk_ids_cache: Optional[Set[str]] = None

    def invalidate_solution_cache(self) -> None:
        """Explicitly invalidate in-memory solution chunk cache (Punto 3)."""
        self._solution_chunk_ids_cache = None

    def get_solution_chunk_ids(self) -> Set[str]:
        """Retrieve set of all solution chunk IDs across the registry with lazy caching."""
        if self._solution_chunk_ids_cache is not None:
            return self._solution_chunk_ids_cache

        solution_ids: Set[str] = set()
        with self.engine.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT solution_chunk_ids
                FROM content_registry
                WHERE solution_chunk_ids IS NOT NULL AND solution_chunk_ids != '' AND solution_chunk_ids != '[]';
                """
            )
            for row in cur.fetchall():
                try:
                    cids = json.loads(row[0])
                    if isinstance(cids, list):
                        solution_ids.update(cids)
                except Exception as err:
                    logger.warning("Error parsing solution_chunk_ids JSON '%s': %s", row[0], err)

        self._solution_chunk_ids_cache = solution_ids
        return self._solution_chunk_ids_cache

    def save(self, item: ContentItem) -> None:
        """Persist or update a ContentItem and invalidate cache immediately (Punto 3)."""
        chunk_ids_json = json.dumps(item.chunk_ids)
        sol_chunk_ids_json = json.dumps(item.solution_chunk_ids or [])
        unit_type_val = item.unit_type.value if isinstance(item.unit_type, UnitType) else str(item.unit_type)
        status_val = item.status.value if isinstance(item.status, ContentStatus) else str(item.status)
        meta_json = json.dumps(item.metadata)

        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT INTO content_registry (
                    content_id, source_id, unit_type, statement_text,
                    chunk_ids, solution_chunk_ids, status, created_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(content_id) DO UPDATE SET
                    source_id = excluded.source_id,
                    unit_type = excluded.unit_type,
                    statement_text = excluded.statement_text,
                    chunk_ids = excluded.chunk_ids,
                    solution_chunk_ids = excluded.solution_chunk_ids,
                    status = excluded.status,
                    metadata = excluded.metadata;
                """,
                (
                    item.content_id,
                    item.source_id,
                    unit_type_val,
                    item.statement_text,
                    chunk_ids_json,
                    sol_chunk_ids_json,
                    status_val,
                    item.created_at,
                    meta_json,
                ),
            )

        # Invalidate solution chunk cache immediately (Punto 3)
        self.invalidate_solution_cache()

    def get(self, content_id: str) -> Optional[ContentItem]:
        """Fetch ContentItem by exact content_id."""
        with self.engine.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT content_id, source_id, unit_type, statement_text,
                       chunk_ids, solution_chunk_ids, status, created_at, metadata
                FROM content_registry
                WHERE content_id = ?;
                """,
                (content_id,),
            )
            row = cur.fetchone()
            if not row:
                return None

            return self._row_to_item(row)

    def list_all(self) -> List[ContentItem]:
        """List all indexed content units."""
        with self.engine.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT content_id, source_id, unit_type, statement_text,
                       chunk_ids, solution_chunk_ids, status, created_at, metadata
                FROM content_registry
                ORDER BY content_id ASC;
                """
            )
            return [self._row_to_item(row) for row in cur.fetchall()]

    def list_by_source(self, source_id: str) -> List[ContentItem]:
        """List content units belonging to a specific source."""
        with self.engine.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT content_id, source_id, unit_type, statement_text,
                       chunk_ids, solution_chunk_ids, status, created_at, metadata
                FROM content_registry
                WHERE source_id = ?
                ORDER BY content_id ASC;
                """,
                (source_id,),
            )
            return [self._row_to_item(row) for row in cur.fetchall()]

    def list_by_type(self, unit_type: UnitType) -> List[ContentItem]:
        """List content units by unit_type."""
        type_val = unit_type.value if isinstance(unit_type, UnitType) else str(unit_type)
        with self.engine.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT content_id, source_id, unit_type, statement_text,
                       chunk_ids, solution_chunk_ids, status, created_at, metadata
                FROM content_registry
                WHERE unit_type = ?
                ORDER BY content_id ASC;
                """,
                (type_val,),
            )
            return [self._row_to_item(row) for row in cur.fetchall()]

    # -----------------------------------------------------------------
    # ACCESORES CON FILTRADO MANDATORIO (Punto 2: Sin escape hatch)
    # -----------------------------------------------------------------

    def get_statement_chunks(
        self,
        content_id: str,
        chunk_repository: Any,
    ) -> Tuple[List[Any], bool]:
        """Retrieve statement chunks for an item, strictly applying filter_presentation.

        Returns:
            Tuple[List[Any], bool]: (filtered_chunks, had_solution_removed)
        """
        item = self.get(content_id)
        if not item or not item.chunk_ids:
            return [], False

        raw_chunks = self._fetch_raw_chunks(item.chunk_ids, chunk_repository)
        # Apply mandatory presentation filter
        return filter_presentation(raw_chunks, self)

    def get_solution_chunks(
        self,
        content_id: str,
        chunk_repository: Any,
    ) -> List[Any]:
        """Retrieve solution chunks for an item (explicit authorized flow only)."""
        item = self.get(content_id)
        if not item or not item.solution_chunk_ids:
            return []

        return self._fetch_raw_chunks(item.solution_chunk_ids, chunk_repository)

    def list_chunks_for_item(
        self,
        content_id: str,
        chunk_repository: Any,
    ) -> Tuple[List[Any], bool]:
        """Retrieve all chunks for an item with presentation filtering applied."""
        return self.get_statement_chunks(content_id, chunk_repository)

    def _fetch_raw_chunks(self, chunk_ids: List[str], chunk_repo: Any) -> List[Any]:
        """Internal helper to retrieve chunk objects from ChunkRepository or KnowledgeStore."""
        if not chunk_ids:
            return []

        if hasattr(chunk_repo, "get_many"):
            return chunk_repo.get_many(chunk_ids)
        if hasattr(chunk_repo, "get"):
            chunks = []
            for cid in chunk_ids:
                c = chunk_repo.get(cid)
                if c:
                    chunks.append(c)
            return chunks
        if hasattr(chunk_repo, "engine"):
            # Direct SQLite retrieval
            with chunk_repo.engine.transaction() as conn:
                placeholders = ",".join("?" for _ in chunk_ids)
                cur = conn.cursor()
                cur.execute(
                    f"SELECT id, document_id, source_id, content, page_start, pos_index, section FROM chunks WHERE id IN ({placeholders});",
                    chunk_ids,
                )
                return cur.fetchall()

        return []

    def _row_to_item(self, row: Tuple[Any, ...]) -> ContentItem:
        """Convert SQLite row to ContentItem instance."""
        c_id, s_id, u_type, stmt, c_ids, sol_ids, st, dt, meta = row
        return ContentItem(
            content_id=c_id,
            source_id=s_id,
            unit_type=UnitType(u_type),
            statement_text=stmt,
            chunk_ids=json.loads(c_ids) if c_ids else [],
            solution_chunk_ids=json.loads(sol_ids) if sol_ids else [],
            status=ContentStatus(st),
            created_at=dt,
            metadata=json.loads(meta) if meta else {},
        )
