"""Persistent SQLite repositories for Sources and Documents in Study Engine."""

import json
from typing import Any, List, Optional

from study_engine.contracts.catalog import (
    ChunkConflictError,
    ChunkNotFoundError,
    DocumentConflictError,
    DocumentNotFoundError,
    SourceConflictError,
    SourceNotFoundError,
    SourceRecord,
)
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.source import Source
from study_engine.storage.sqlite_engine import SQLiteStorageEngine


class SQLiteSourceRepository:
    """Persistent repository for SourceRecord entities backed by SQLite."""


    def __init__(self, engine: SQLiteStorageEngine):
        self.engine = engine

    def save(self, record: SourceRecord) -> None:
        """Persist a SourceRecord with strict idempotency and conflict detection."""
        if not isinstance(record, SourceRecord):
            raise TypeError(f"record must be an instance of SourceRecord, got {type(record).__name__}")

        manifest = record.manifest
        source_obj = record.source
        sha256 = manifest.sha256.lower()

        with self.engine.transaction() as conn:
            cursor = conn.cursor()

            # Check if source_id already exists
            cursor.execute(
                "SELECT manifest_json, source_json, metadata FROM sources WHERE source_id = ?;",
                (record.source_id,),
            )
            row = cursor.fetchone()

            if row is not None:
                existing_manifest = SourceManifest.model_validate_json(row[0])
                existing_source = Source.model_validate_json(row[1]) if row[1] else None
                existing_metadata = json.loads(row[2])

                # Check SHA-256 conflict
                if existing_manifest.sha256.lower() != sha256:
                    raise SourceConflictError(
                        source_id=record.source_id,
                        existing_sha256=existing_manifest.sha256,
                        new_sha256=manifest.sha256,
                        reason=f"Existing SHA-256 '{existing_manifest.sha256}' differs from incoming '{manifest.sha256}'.",
                    )

                # Check metadata divergence
                if existing_metadata != record.metadata:
                    raise SourceConflictError(
                        source_id=record.source_id,
                        existing_sha256=existing_manifest.sha256,
                        new_sha256=manifest.sha256,
                        reason="Divergent metadata for identical source_id.",
                    )

                # Check source domain entity divergence
                if existing_source != source_obj:
                    raise SourceConflictError(
                        source_id=record.source_id,
                        existing_sha256=existing_manifest.sha256,
                        new_sha256=manifest.sha256,
                        reason="Divergent conceptual source attributes for identical source_id.",
                    )

                # Check manifest filename divergence
                if existing_manifest.filename != manifest.filename:
                    raise SourceConflictError(
                        source_id=record.source_id,
                        existing_sha256=existing_manifest.sha256,
                        new_sha256=manifest.sha256,
                        reason="Divergent manifest filename for identical source_id.",
                    )

                # Exact match -> idempotent no-op
                return

            # Insert new record
            manifest_json = manifest.model_dump_json()
            source_json = source_obj.model_dump_json() if source_obj else None
            metadata_json = json.dumps(record.metadata, sort_keys=True)

            title = source_obj.title if source_obj else manifest.filename
            author = source_obj.author if source_obj else None
            src_type = source_obj.type if source_obj else manifest.media_type
            language = source_obj.language if source_obj else "es"
            role = source_obj.role.value if source_obj else "PRIMARY"
            priority = source_obj.priority if source_obj else 1
            subject = source_obj.subject if source_obj else None
            course = source_obj.course if source_obj else None
            phase = source_obj.phase if source_obj else None
            chapter = source_obj.chapter if source_obj else None
            section = source_obj.section if source_obj else None
            page = source_obj.page if source_obj else None

            cursor.execute(
                """
                INSERT INTO sources (
                    source_id, sha256, manifest_json, source_json,
                    title, author, type, language, role, priority,
                    subject, course, phase, chapter, section, page,
                    metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    record.source_id,
                    sha256,
                    manifest_json,
                    source_json,
                    title,
                    author,
                    src_type,
                    language,
                    role,
                    priority,
                    subject,
                    course,
                    phase,
                    chapter,
                    section,
                    page,
                    metadata_json,
                ),
            )

    def get(self, source_id: str) -> SourceRecord:
        """Retrieve a SourceRecord by ID or raise SourceNotFoundError."""
        if not source_id or not isinstance(source_id, str):
            raise SourceNotFoundError(str(source_id))

        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT source_id, manifest_json, source_json, metadata FROM sources WHERE source_id = ?;",
                (source_id,),
            )
            row = cursor.fetchone()

        if row is None:
            raise SourceNotFoundError(source_id)

        manifest = SourceManifest.model_validate_json(row[1])
        source_obj = Source.model_validate_json(row[2]) if row[2] else None
        meta = json.loads(row[3])

        return SourceRecord(
            source_id=row[0],
            manifest=manifest,
            source=source_obj,
            metadata=meta,
        )

    def find_by_sha256(self, sha256: str) -> Optional[SourceRecord]:
        """Lookup a source by its exact SHA-256 hash in O(1) via index."""
        if not sha256 or not isinstance(sha256, str):
            return None

        clean_hash = sha256.lower().strip()
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT source_id, manifest_json, source_json, metadata FROM sources WHERE sha256 = ? LIMIT 1;",
                (clean_hash,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        manifest = SourceManifest.model_validate_json(row[1])
        source_obj = Source.model_validate_json(row[2]) if row[2] else None
        meta = json.loads(row[3])

        return SourceRecord(
            source_id=row[0],
            manifest=manifest,
            source=source_obj,
            metadata=meta,
        )

    def contains(self, source_id: str) -> bool:
        """Check if source_id exists in storage."""
        if not source_id:
            return False
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM sources WHERE source_id = ?;", (source_id,))
            return cursor.fetchone() is not None

    def list_all(self) -> List[SourceRecord]:
        """List all sources ordered deterministically by source_id."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT source_id, manifest_json, source_json, metadata FROM sources ORDER BY source_id ASC;"
            )
            rows = cursor.fetchall()

        records: List[SourceRecord] = []
        for r in rows:
            manifest = SourceManifest.model_validate_json(r[1])
            source_obj = Source.model_validate_json(r[2]) if r[2] else None
            meta = json.loads(r[3])
            records.append(
                SourceRecord(
                    source_id=r[0],
                    manifest=manifest,
                    source=source_obj,
                    metadata=meta,
                )
            )
        return records

    def delete(self, source_id: str) -> bool:
        """Delete a source and cascade-delete its documents and chunks."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sources WHERE source_id = ?;", (source_id,))
            return cursor.rowcount > 0

    def count(self) -> int:
        """Return total count of registered sources."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sources;")
            return int(cursor.fetchone()[0])


class SQLiteDocumentRepository:
    """Persistent repository for Document entities backed by SQLite."""

    def __init__(self, engine: SQLiteStorageEngine):
        self.engine = engine

    def save(self, document: Document) -> None:
        """Persist a Document, validating referential integrity and idempotency."""
        if not isinstance(document, Document):
            raise TypeError(f"document must be an instance of Document, got {type(document).__name__}")

        with self.engine.transaction() as conn:
            cursor = conn.cursor()

            # Check if source exists
            cursor.execute("SELECT 1 FROM sources WHERE source_id = ?;", (document.source_id,))
            if cursor.fetchone() is None:
                raise SourceNotFoundError(document.source_id)

            # Check if document already exists
            cursor.execute(
                """
                SELECT source_id, title, content, path, page_count, language, metadata
                FROM documents WHERE id = ?;
                """,
                (document.id,),
            )
            row = cursor.fetchone()

            if row is not None:
                existing_doc = Document(
                    id=document.id,
                    source_id=row[0],
                    title=row[1],
                    content=row[2],
                    path=row[3],
                    page_count=row[4],
                    language=row[5],
                    metadata=json.loads(row[6]),
                )

                if existing_doc == document:
                    return  # Exact idempotent match

                raise DocumentConflictError(
                    document_id=document.id,
                    reason="Incoming document differs from already registered document with identical ID.",
                )

            # Insert new document
            created_at_str = document.created_at.isoformat() if document.created_at else None
            metadata_json = json.dumps(document.metadata, sort_keys=True)

            cursor.execute(
                """
                INSERT INTO documents (
                    id, source_id, title, content, path, page_count, language, created_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    document.id,
                    document.source_id,
                    document.title,
                    document.content,
                    document.path,
                    document.page_count,
                    document.language,
                    created_at_str,
                    metadata_json,
                ),
            )

    def get(self, document_id: str) -> Document:
        """Retrieve a Document by ID or raise DocumentNotFoundError."""
        if not document_id or not isinstance(document_id, str):
            raise DocumentNotFoundError(str(document_id))

        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, source_id, title, content, path, page_count, language, created_at, metadata
                FROM documents WHERE id = ?;
                """,
                (document_id,),
            )
            row = cursor.fetchone()

        if row is None:
            raise DocumentNotFoundError(document_id)

        return Document(
            id=row[0],
            source_id=row[1],
            title=row[2],
            content=row[3],
            path=row[4],
            page_count=row[5],
            language=row[6],
            created_at=row[7],
            metadata=json.loads(row[8]),
        )

    def contains(self, document_id: str) -> bool:
        """Check if document_id exists in storage."""
        if not document_id:
            return False
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM documents WHERE id = ?;", (document_id,))
            return cursor.fetchone() is not None

    def list_by_source(self, source_id: str, include_content: bool = True) -> List[Document]:
        """List all documents for a given source, ordered deterministically by ID."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            if include_content:
                cursor.execute(
                    """
                    SELECT id, source_id, title, content, path, page_count, language, created_at, metadata
                    FROM documents WHERE source_id = ? ORDER BY id ASC;
                    """,
                    (source_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, source_id, title, NULL, path, page_count, language, created_at, metadata
                    FROM documents WHERE source_id = ? ORDER BY id ASC;
                    """,
                    (source_id,),
                )
            rows = cursor.fetchall()

        return [
            Document(
                id=r[0],
                source_id=r[1],
                title=r[2],
                content=r[3],
                path=r[4],
                page_count=r[5],
                language=r[6],
                created_at=r[7],
                metadata=json.loads(r[8]),
            )
            for r in rows
        ]

    def list_all(self, include_content: bool = True) -> List[Document]:
        """List all documents ordered deterministically by ID."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            if include_content:
                cursor.execute(
                    """
                    SELECT id, source_id, title, content, path, page_count, language, created_at, metadata
                    FROM documents ORDER BY id ASC;
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT id, source_id, title, NULL, path, page_count, language, created_at, metadata
                    FROM documents ORDER BY id ASC;
                    """
                )
            rows = cursor.fetchall()

        return [
            Document(
                id=r[0],
                source_id=r[1],
                title=r[2],
                content=r[3],
                path=r[4],
                page_count=r[5],
                language=r[6],
                created_at=r[7],
                metadata=json.loads(r[8]),
            )
            for r in rows
        ]

    def delete(self, document_id: str) -> bool:
        """Delete a document and cascade-delete its chunks."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE id = ?;", (document_id,))
            return cursor.rowcount > 0

    def count(self) -> int:
        """Return total count of registered documents."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents;")
            return int(cursor.fetchone()[0])


class SQLiteChunkRepository:
    """Persistent repository for Chunk entities backed by SQLite."""

    def __init__(self, engine: SQLiteStorageEngine):
        self.engine = engine

    def save_chunks(self, chunks: List[Chunk]) -> int:
        """Bulk persist a list of Chunk entities within a single atomic transaction.

        Returns:
            int: Number of newly inserted chunks.
        """
        if not chunks:
            return 0

        for c in chunks:
            if not isinstance(c, Chunk):
                raise TypeError(f"All items must be Chunk instances, got {type(c).__name__}")

        # Check internal batch uniqueness
        seen_ids = set()
        seen_doc_idx = set()
        for c in chunks:
            if c.id in seen_ids:
                raise ChunkConflictError(c.id, f"Duplicate chunk ID '{c.id}' within incoming batch.")
            seen_ids.add(c.id)
            doc_idx_key = (c.document_id, c.index)
            if doc_idx_key in seen_doc_idx:
                raise ChunkConflictError(
                    c.id,
                    f"Duplicate (document_id, index) pair ({c.document_id}, {c.index}) within incoming batch.",
                )
            seen_doc_idx.add(doc_idx_key)

        with self.engine.transaction() as conn:
            cursor = conn.cursor()

            # Verify referential integrity for all unique source_ids and document_ids
            unique_doc_ids = {c.document_id for c in chunks}
            unique_src_ids = {c.source_id for c in chunks}

            if unique_src_ids:
                placeholders = ",".join("?" for _ in unique_src_ids)
                cursor.execute(
                    f"SELECT source_id FROM sources WHERE source_id IN ({placeholders});",
                    list(unique_src_ids),
                )
                found_src_ids = {r[0] for r in cursor.fetchall()}
                for s_id in unique_src_ids:
                    if s_id not in found_src_ids:
                        raise SourceNotFoundError(s_id)

            doc_parent_sources = {}
            if unique_doc_ids:
                placeholders = ",".join("?" for _ in unique_doc_ids)
                cursor.execute(
                    f"SELECT id, source_id FROM documents WHERE id IN ({placeholders});",
                    list(unique_doc_ids),
                )
                for row in cursor.fetchall():
                    doc_parent_sources[row[0]] = row[1]
                for d_id in unique_doc_ids:
                    if d_id not in doc_parent_sources:
                        raise DocumentNotFoundError(d_id)

            # Invariant: Each chunk's source_id must match its parent document's source_id
            for c in chunks:
                expected_src = doc_parent_sources[c.document_id]
                if c.source_id != expected_src:
                    raise ChunkConflictError(
                        c.id,
                        f"Chunk source_id '{c.source_id}' does not match parent document '{c.document_id}' source_id '{expected_src}'.",
                    )

            # Check existing chunks for idempotency and conflict via batch fetch
            chunk_ids = [c.id for c in chunks]
            existing_chunks_by_id = {}
            if chunk_ids:
                placeholders = ",".join("?" for _ in chunk_ids)
                cursor.execute(
                    f"""
                    SELECT id, document_id, source_id, content, page_start, page_end,
                           chapter, section, token_count, pos_index, metadata
                    FROM chunks WHERE id IN ({placeholders});
                    """,
                    chunk_ids,
                )
                for row in cursor.fetchall():
                    existing_chunks_by_id[row[0]] = Chunk(
                        id=row[0],
                        document_id=row[1],
                        source_id=row[2],
                        content=row[3],
                        page_start=row[4],
                        page_end=row[5],
                        chapter=row[6],
                        section=row[7],
                        token_count=row[8],
                        index=row[9],
                        metadata=json.loads(row[10]),
                    )

            new_chunks_to_insert = []
            for c in chunks:
                if c.id in existing_chunks_by_id:
                    existing_chunk = existing_chunks_by_id[c.id]
                    if existing_chunk == c:
                        continue  # Idempotent match

                    raise ChunkConflictError(
                        c.id,
                        f"Incoming chunk '{c.id}' conflicts with already registered chunk.",
                    )

                new_chunks_to_insert.append(c)

            if not new_chunks_to_insert:
                return 0

            # Execute bulk insertion
            param_tuples = [
                (
                    c.id,
                    c.document_id,
                    c.source_id,
                    c.content,
                    c.page_start,
                    c.page_end,
                    c.chapter,
                    c.section,
                    c.token_count,
                    c.index,
                    json.dumps(c.metadata, sort_keys=True),
                )
                for c in new_chunks_to_insert
            ]

            cursor.executemany(
                """
                INSERT INTO chunks (
                    id, document_id, source_id, content, page_start, page_end,
                    chapter, section, token_count, pos_index, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                param_tuples,
            )

            return len(new_chunks_to_insert)

    def get(self, chunk_id: str) -> Chunk:
        """Retrieve a Chunk by ID or raise ChunkNotFoundError."""
        if not chunk_id or not isinstance(chunk_id, str):
            raise ChunkNotFoundError(str(chunk_id))

        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, document_id, source_id, content, page_start, page_end,
                       chapter, section, token_count, pos_index, metadata
                FROM chunks WHERE id = ?;
                """,
                (chunk_id,),
            )
            row = cursor.fetchone()

        if row is None:
            raise ChunkNotFoundError(chunk_id)

        return Chunk.model_construct(
            id=row[0],
            document_id=row[1],
            source_id=row[2],
            content=row[3],
            page_start=row[4],
            page_end=row[5],
            chapter=row[6],
            section=row[7],
            token_count=row[8],
            index=row[9],
            metadata=json.loads(row[10]),
        )

    def contains(self, chunk_id: str) -> bool:
        """Check if chunk_id exists in storage."""
        if not chunk_id:
            return False
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM chunks WHERE id = ?;", (chunk_id,))
            return cursor.fetchone() is not None

    def list_by_document(self, document_id: str) -> List[Chunk]:
        """List all chunks for a document ordered strictly by pos_index ASC."""
        if not document_id:
            return []
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, document_id, source_id, content, page_start, page_end,
                       chapter, section, token_count, pos_index, metadata
                FROM chunks WHERE document_id = ? ORDER BY pos_index ASC;
                """,
                (document_id,),
            )
            rows = cursor.fetchall()

        return [
            Chunk.model_construct(
                id=r[0],
                document_id=r[1],
                source_id=r[2],
                content=r[3],
                page_start=r[4],
                page_end=r[5],
                chapter=r[6],
                section=r[7],
                token_count=r[8],
                index=r[9],
                metadata=json.loads(r[10]),
            )
            for r in rows
        ]

    def list_by_source(
        self,
        source_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Chunk]:
        """List chunks for a source ordered by document_id and pos_index."""
        if not source_id:
            return []
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            query = """
                SELECT id, document_id, source_id, content, page_start, page_end,
                       chapter, section, token_count, pos_index, metadata
                FROM chunks WHERE source_id = ? ORDER BY document_id ASC, pos_index ASC
            """
            params: List[Any] = [source_id]
            if limit is not None and limit >= 0:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, max(0, offset)])


            cursor.execute(query + ";", params)
            rows = cursor.fetchall()

        return [
            Chunk.model_construct(
                id=r[0],
                document_id=r[1],
                source_id=r[2],
                content=r[3],
                page_start=r[4],
                page_end=r[5],
                chapter=r[6],
                section=r[7],
                token_count=r[8],
                index=r[9],
                metadata=json.loads(r[10]),
            )
            for r in rows
        ]


    def delete_by_document(self, document_id: str) -> int:
        """Delete all chunks for a document."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks WHERE document_id = ?;", (document_id,))
            return cursor.rowcount

    def count(
        self,
        source_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> int:
        """Count total chunks or filtered by source/document."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            query = "SELECT COUNT(*) FROM chunks WHERE 1=1"
            params = []
            if source_id:
                query += " AND source_id = ?"
                params.append(source_id)
            if document_id:
                query += " AND document_id = ?"
                params.append(document_id)
            cursor.execute(query + ";", params)
            return int(cursor.fetchone()[0])

