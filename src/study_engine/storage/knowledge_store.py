"""Unified high-level KnowledgeStore facade for Study Engine storage subsystem."""

from datetime import datetime, timezone
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

logger = logging.getLogger(__name__)

from study_engine.contracts.catalog import (
    NotebookConflictError,
    NotebookNotFoundError,
    SourceNotFoundError,
    SourceRecord,
)
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.search import SearchResult
from study_engine.hierarchy.folder import Folder
from study_engine.storage.lexical_index import (
    _BILINGUAL_MAP,
    SPANISH_STOPWORDS,
    SQLiteLexicalIndex,
)
from study_engine.storage.repositories import (
    SQLiteChunkRepository,
    SQLiteDocumentRepository,
    SQLiteSourceRepository,
)
from study_engine.storage.sqlite_engine import SQLiteStorageEngine

# Umbral provisional de similitud coseno para aceptar evidencia vectorial
# (gate de abstención E25 / INV-W5-1). Medido sobre el corpus FADENA
# (multilingual-e5-small): consultas in-scope top-1 >= 0.88; consultas fuera de
# alcance top-1 <= 0.86. e5-small es anisotrópico: TODO chunk supera ~0.83, así
# que el piso es deliberadamente alto. Ajustar en calibración (P1) o vía env.
MIN_VECTOR_SIMILARITY = float(os.environ.get("TALOS_MIN_VECTOR_SIMILARITY", "0.87"))



def _normalize_coverage_word(w: str) -> str:
    """Normaliza palabra para matching de cobertura: minúsculas, mapa bilingüe y sufijo plural."""
    import unicodedata
    t = w.lower().strip()
    unaccented = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    if unaccented in _BILINGUAL_MAP:
        return _BILINGUAL_MAP[unaccented]
    if len(t) > 4 and t.endswith("es"):
        t = t[:-2]
    elif len(t) > 3 and t.endswith("s"):
        t = t[:-1]
    unaccented_stem = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    if unaccented_stem in _BILINGUAL_MAP:
        return _BILINGUAL_MAP[unaccented_stem]
    return t


class FolderNotFoundError(Exception):
    """Raised when a requested folder cannot be found."""

    def __init__(self, folder_id: str) -> None:
        super().__init__(f"Folder '{folder_id}' not found.")
        self.folder_id = folder_id


class FolderConflictError(Exception):
    """Raised when attempting to create a conflicting folder."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class KnowledgeStore:
    """Unified, ACID-compliant facade for knowledge persistence, notebook isolation, and retrieval."""

    def __init__(self, db_path: Union[str, Path] = ":memory:"):
        self.engine = SQLiteStorageEngine(db_path)
        self.sources = SQLiteSourceRepository(self.engine)
        self.documents = SQLiteDocumentRepository(self.engine)
        self.chunks = SQLiteChunkRepository(self.engine)
        self.lexical_index = SQLiteLexicalIndex(self.engine)
        from study_engine.storage.content_registry import ContentRegistryRepository
        self.content_registry = ContentRegistryRepository(self.engine)

    def initialize(self) -> None:
        """Initialize all tables, indexes, and FTS5 triggers idempotently."""
        self.engine.initialize_schema()

    # ------------------------------------------------------------------
    # NOTEBOOK MANAGEMENT
    # ------------------------------------------------------------------
    def create_notebook(self, notebook: Notebook) -> Notebook:
        """Register a new Notebook or return existing if identical (idempotent)."""
        if not isinstance(notebook, Notebook):
            raise TypeError(f"Expected Notebook instance, got {type(notebook).__name__}")

        folder_id = getattr(notebook, "folder_id", "folder_root") or "folder_root"

        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT name, description, subject, curriculum_id, folder_id, metadata, created_at, updated_at
                FROM notebooks WHERE id = ?;
                """,
                (notebook.id,),
            )
            row = cursor.fetchone()

            if row is not None:
                existing_name = row[0]
                existing_desc = row[1]
                existing_subj = row[2]
                existing_curr = row[3]
                existing_folder = row[4] or "folder_root"
                existing_meta = json.loads(row[5])

                if (
                    existing_name == notebook.name
                    and existing_desc == notebook.description
                    and existing_subj == notebook.subject
                    and existing_curr == notebook.curriculum_id
                    and existing_folder == folder_id
                    and existing_meta == notebook.metadata
                ):
                    return self.get_notebook(notebook.id)

                raise NotebookConflictError(
                    notebook_id=notebook.id,
                    reason="Incoming notebook attributes differ from already registered notebook with identical ID.",
                )

            # Check unique constraint (name, folder_id)
            cursor.execute(
                "SELECT id FROM notebooks WHERE name = ? AND folder_id = ? AND id != ?;",
                (notebook.name, folder_id, notebook.id),
            )
            if cursor.fetchone() is not None:
                raise NotebookConflictError(
                    notebook_id=notebook.id,
                    reason=f"A notebook with name '{notebook.name}' already exists in folder '{folder_id}'.",
                )

            # Ensure folder exists
            cursor.execute("SELECT 1 FROM folders WHERE id = ?;", (folder_id,))
            if cursor.fetchone() is None:
                if folder_id == "folder_root":
                    cursor.execute(
                        "INSERT OR IGNORE INTO folders (id, name, parent_folder_id, description, created_at, updated_at) "
                        "VALUES ('folder_root', 'Root Folder', NULL, 'Default root folder for notebooks', datetime('now'), datetime('now'));"
                    )
                else:
                    raise FolderNotFoundError(folder_id)

            # Insert notebook
            created_str = notebook.created_at.isoformat() if notebook.created_at else datetime.now().isoformat()
            updated_str = notebook.updated_at.isoformat() if notebook.updated_at else created_str

            cursor.execute(
                """
                INSERT INTO notebooks (id, name, description, subject, curriculum_id, folder_id, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    notebook.id,
                    notebook.name,
                    notebook.description,
                    notebook.subject,
                    notebook.curriculum_id,
                    folder_id,
                    created_str,
                    updated_str,
                    json.dumps(notebook.metadata, sort_keys=True),
                ),
            )

            # Link initial sources if specified
            if notebook.sources:
                for s_id in notebook.sources:
                    cursor.execute("SELECT 1 FROM sources WHERE source_id = ?;", (s_id,))
                    if cursor.fetchone() is None:
                        raise SourceNotFoundError(s_id)
                    cursor.execute(
                        "INSERT OR IGNORE INTO notebook_sources (notebook_id, source_id) VALUES (?, ?);",
                        (notebook.id, s_id),
                    )

        return self.get_notebook(notebook.id)

    def get_notebook(self, notebook_id: str) -> Notebook:
        """Retrieve a Notebook by ID along with its associated sources."""
        if not notebook_id or not isinstance(notebook_id, str):
            raise NotebookNotFoundError(str(notebook_id))

        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, description, subject, curriculum_id, folder_id, created_at, updated_at, metadata
                FROM notebooks WHERE id = ?;
                """,
                (notebook_id,),
            )
            row = cursor.fetchone()

            if row is None:
                raise NotebookNotFoundError(notebook_id)

            cursor.execute(
                "SELECT source_id FROM notebook_sources WHERE notebook_id = ? ORDER BY source_id ASC;",
                (notebook_id,),
            )
            source_ids = [r[0] for r in cursor.fetchall()]

        folder_id = row[5] or "folder_root"
        created_dt = datetime.fromisoformat(row[6]) if row[6] else None
        updated_dt = datetime.fromisoformat(row[7]) if row[7] else None

        return Notebook(
            id=row[0],
            name=row[1],
            description=row[2],
            subject=row[3],
            curriculum_id=row[4],
            folder_id=folder_id,
            sources=source_ids,
            created_at=created_dt,
            updated_at=updated_dt,
            metadata=json.loads(row[8]),
        )

    def contains_notebook(self, notebook_id: str) -> bool:
        """Check if notebook exists in storage."""
        if not notebook_id:
            return False
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM notebooks WHERE id = ?;", (notebook_id,))
            return cursor.fetchone() is not None

    def list_notebooks(self) -> List[Notebook]:
        """List all notebooks ordered by ID."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM notebooks ORDER BY id ASC;")
            ids = [r[0] for r in cursor.fetchall()]

        return [self.get_notebook(nid) for nid in ids]

    def delete_notebook(self, notebook_id: str) -> bool:
        """Delete a notebook and its association links without deleting underlying sources."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notebooks WHERE id = ?;", (notebook_id,))
            return cursor.rowcount > 0

    # ------------------------------------------------------------------
    # FOLDER MANAGEMENT (FASE 5.7)
    # ------------------------------------------------------------------
    def create_folder(self, folder: Folder) -> Folder:
        """Register a new Folder in storage with unique name per parent folder."""
        folder.validate_not_self_referencing()
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM folders WHERE id = ?;", (folder.id,))
            if cursor.fetchone() is not None:
                raise FolderConflictError(f"Folder with id '{folder.id}' already exists.")

            # Validate unique (name, parent_folder_id)
            if folder.parent_folder_id is not None:
                cursor.execute("SELECT 1 FROM folders WHERE id = ?;", (folder.parent_folder_id,))
                if cursor.fetchone() is None:
                    raise FolderNotFoundError(folder.parent_folder_id)

                cursor.execute(
                    "SELECT id FROM folders WHERE name = ? AND parent_folder_id = ?;",
                    (folder.name, folder.parent_folder_id),
                )
            else:
                cursor.execute(
                    "SELECT id FROM folders WHERE name = ? AND parent_folder_id IS NULL;",
                    (folder.name,),
                )

            if cursor.fetchone() is not None:
                raise FolderConflictError(
                    f"A folder with name '{folder.name}' already exists in parent '{folder.parent_folder_id}'."
                )

            cursor.execute(
                """
                INSERT INTO folders (id, name, parent_folder_id, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    folder.id,
                    folder.name,
                    folder.parent_folder_id,
                    folder.description,
                    folder.created_at.isoformat(),
                    folder.updated_at.isoformat(),
                ),
            )
        return self.get_folder(folder.id)

    def get_folder(self, folder_id: str) -> Folder:
        """Retrieve a Folder by ID."""
        if not folder_id or not isinstance(folder_id, str):
            raise FolderNotFoundError(str(folder_id))

        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, parent_folder_id, description, created_at, updated_at FROM folders WHERE id = ?;",
                (folder_id.strip(),),
            )
            row = cursor.fetchone()
            if row is None:
                raise FolderNotFoundError(folder_id)

        return Folder(
            id=row[0],
            name=row[1],
            parent_folder_id=row[2],
            description=row[3],
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5]),
        )

    def contains_folder(self, folder_id: str) -> bool:
        """Check if folder exists in storage."""
        if not folder_id:
            return False
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM folders WHERE id = ?;", (folder_id.strip(),))
            return cursor.fetchone() is not None

    def list_folders(self, parent_folder_id: Optional[str] = None) -> List[Folder]:
        """List folders, optionally filtered by parent_folder_id."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            if parent_folder_id is not None:
                cursor.execute(
                    "SELECT id FROM folders WHERE parent_folder_id = ? ORDER BY name ASC;",
                    (parent_folder_id,),
                )
            else:
                cursor.execute("SELECT id FROM folders ORDER BY name ASC;")
            ids = [r[0] for r in cursor.fetchall()]

        return [self.get_folder(fid) for fid in ids]

    def delete_folder(self, folder_id: str) -> bool:
        """Delete a folder. Protects 'folder_root' from deletion and re-parents orphan notebooks to folder_root."""
        clean_id = folder_id.strip()
        if clean_id == "folder_root":
            raise ValueError("Cannot delete the default root folder 'folder_root'.")

        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            # Move any child notebooks back to folder_root
            cursor.execute(
                "UPDATE notebooks SET folder_id = 'folder_root' WHERE folder_id = ?;",
                (clean_id,),
            )
            cursor.execute("DELETE FROM folders WHERE id = ?;", (clean_id,))
            return cursor.rowcount > 0

    def list_notebooks_in_folder(self, folder_id: str) -> List[Notebook]:
        """List all notebooks residing in the specified folder."""
        clean_id = folder_id.strip()
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM notebooks WHERE folder_id = ? ORDER BY name ASC, id ASC;",
                (clean_id,),
            )
            ids = [r[0] for r in cursor.fetchall()]
        return [self.get_notebook(nid) for nid in ids]

    # ------------------------------------------------------------------
    # NOTEBOOK - SOURCE RELATIONS (M:N)
    # ------------------------------------------------------------------
    def link_source_to_notebook(self, notebook_id: str, source_id: str) -> None:
        """Link a physical source to a study notebook."""
        if not self.contains_notebook(notebook_id):
            raise NotebookNotFoundError(notebook_id)

        if not self.sources.contains(source_id):
            raise SourceNotFoundError(source_id)

        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO notebook_sources (notebook_id, source_id) VALUES (?, ?);",
                (notebook_id, source_id),
            )

    def unlink_source_from_notebook(self, notebook_id: str, source_id: str) -> bool:
        """Unlink a source from a notebook without deleting the source."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM notebook_sources WHERE notebook_id = ? AND source_id = ?;",
                (notebook_id, source_id),
            )
            return cursor.rowcount > 0

    def list_notebook_sources(self, notebook_id: str) -> List[SourceRecord]:
        """List all SourceRecords associated with a notebook."""
        if not self.contains_notebook(notebook_id):
            raise NotebookNotFoundError(notebook_id)

        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT source_id FROM notebook_sources WHERE notebook_id = ? ORDER BY source_id ASC;",
                (notebook_id,),
            )
            source_ids = [r[0] for r in cursor.fetchall()]

        return [self.sources.get(sid) for sid in source_ids]

    # ------------------------------------------------------------------
    # DIRECT DELEGATIONS
    # ------------------------------------------------------------------
    def save_source(self, record: SourceRecord) -> None:
        self.sources.save(record)

    def get_source(self, source_id: str) -> SourceRecord:
        return self.sources.get(source_id)

    def find_source_by_sha256(self, sha256: str) -> Optional[SourceRecord]:
        return self.sources.find_by_sha256(sha256)

    def delete_source(self, source_id: str) -> bool:
        return self.sources.delete(source_id)

    def save_document(self, document: Document) -> None:
        self.documents.save(document)

    def get_document(self, document_id: str) -> Document:
        return self.documents.get(document_id)

    def list_documents(self, source_id: Optional[str] = None, include_content: bool = True) -> List[Document]:
        if source_id:
            return self.documents.list_by_source(source_id, include_content=include_content)
        return self.documents.list_all(include_content=include_content)

    def save_chunks(self, chunks: List[Chunk]) -> int:
        return self.chunks.save_chunks(chunks)

    def get_chunk(self, chunk_id: str) -> Chunk:
        return self.chunks.get(chunk_id)

    def list_chunks_by_document(self, document_id: str) -> List[Chunk]:
        return self.chunks.list_by_document(document_id)

    # ------------------------------------------------------------------
    # ATOMIC BUNDLE INGESTION
    # ------------------------------------------------------------------
    def store_ingestion_bundle(
        self,
        record: SourceRecord,
        documents: List[Document],
        chunks: List[Chunk],
        notebook_id: Optional[str] = None,
    ) -> int:
        """Persist a complete ingestion bundle in a single atomic transaction."""
        if notebook_id and not self.contains_notebook(notebook_id):
            raise NotebookNotFoundError(notebook_id)

        with self.engine.transaction():
            self.sources.save(record)
            if notebook_id:
                self.link_source_to_notebook(notebook_id, record.source_id)

            for doc in documents:
                self.documents.save(doc)

            if chunks:
                self.chunks.save_chunks(chunks)
                try:
                    from study_engine.storage.content_parser import parse_content_items
                    items = parse_content_items(chunks, record.source_id)
                    for item in items:
                        self.content_registry.save(item)
                except Exception as err:
                    logger.warning("[CONTENT REGISTRY HOOK] Error parsing content items: %s", err)

        return len(chunks)

    # ------------------------------------------------------------------
    # NOTEBOOK-ISOLATED LEXICAL SEARCH
    # ------------------------------------------------------------------
    def search(
        self,
        query: str,
        notebook_id: Optional[str] = None,
        source_id: Optional[str] = None,
        document_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[SearchResult]:
        """BM25 search with strict relational isolation by notebook."""
        if limit <= 0:
            return []

        if notebook_id:
            if not self.contains_notebook(notebook_id):
                raise NotebookNotFoundError(notebook_id)

            sanitized = self.lexical_index.sanitize_query(query)
            if not sanitized:
                return []

            sql = """
            SELECT
                c.id,
                c.document_id,
                c.source_id,
                -bm25(chunks_fts) AS score,
                snippet(chunks_fts, 0, '[MATCH]', '[/MATCH]', '...', 32) AS snippet,
                c.content,
                c.pos_index,
                c.page_start,
                c.page_end
            FROM chunks_fts
            JOIN chunks c ON c.rowid = chunks_fts.rowid
            JOIN notebook_sources ns ON ns.source_id = c.source_id
            WHERE chunks_fts MATCH ?
              AND ns.notebook_id = ?
              AND (? IS NULL OR c.source_id = ?)
              AND (? IS NULL OR c.document_id = ?)
            ORDER BY score DESC, c.document_id ASC, c.pos_index ASC
            LIMIT ?;
            """

            clean_source_id = source_id.strip() if source_id and source_id.strip() else None
            clean_doc_id = document_id.strip() if document_id and document_id.strip() else None

            params = (
                sanitized,
                notebook_id,
                clean_source_id,
                clean_source_id,
                clean_doc_id,
                clean_doc_id,
                limit,
            )

            with self.engine.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()

            # Fallback to disjunctive OR ranking if multi-term conjunctive search returned 0 results
            if not rows and " " in sanitized:
                disjunctive_query = self.lexical_index.sanitize_query(query, disjunctive=True)
                if disjunctive_query and disjunctive_query != sanitized:
                    fallback_limit = max(limit * 10, 50)
                    fallback_params = (
                        disjunctive_query,
                        notebook_id,
                        clean_source_id,
                        clean_source_id,
                        clean_doc_id,
                        clean_doc_id,
                        fallback_limit,
                    )
                    with self.engine.transaction() as conn:
                        cursor = conn.cursor()
                        cursor.execute(sql, fallback_params)
                        fallback_rows = cursor.fetchall()

                    # Enmienda E-HF3: Cobertura FTS5 sin estrangulamiento
                    _GENERIC_KEYWORDS = {"int", "char", "void", "float", "double", "short", "long", "main", "null", "true", "false"}
                    raw_terms = [
                        t.strip('"*').lower()
                        for t in sanitized.split()
                        if len(t.strip('"*')) > 1 and t.strip('"*').lower() not in SPANISH_STOPWORDS and t.strip('"*').lower() not in ("and", "or", "not")
                    ]
                    norm_query_terms = list(dict.fromkeys(_normalize_coverage_word(t) for t in raw_terms if len(t) > 1))
                    n_terms = len(norm_query_terms)

                    filtered_rows = []
                    if n_terms > 0:
                        required_hits = 1 if n_terms <= 2 else 2
                        for r in fallback_rows:
                            chunk_words = re.findall(r"[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]+", r[5].lower())
                            chunk_norm_set = {_normalize_coverage_word(w) for w in chunk_words}
                            matched_terms = [
                                term for term in norm_query_terms
                                if term in chunk_norm_set or _BILINGUAL_MAP.get(term) in chunk_norm_set
                            ]
                            hits = len(matched_terms)
                            if hits >= required_hits:
                                # Prevenir falsos positivos: si n_terms == 2 y solo coincide 1 término:
                                # 1. No admitir si el único término coincidente es una palabra clave genérica
                                if n_terms == 2 and hits == 1 and all(t in _GENERIC_KEYWORDS for t in matched_terms):
                                    continue
                                # 2. No admitir si alguno de los términos no coincidentes es un término clave de 4-5 caracteres (A5)
                                if n_terms == 2 and hits < n_terms:
                                    unmatched_4_5 = [
                                        t for t in norm_query_terms
                                        if t not in matched_terms and 4 <= len(t) <= 5
                                    ]
                                    if unmatched_4_5:
                                        for term in unmatched_4_5:
                                            logger.warning(
                                                "COVERAGE_GUARD_MISS: term='%s' (len=%d) not covered in chunk '%s' for query='%s'",
                                                term, len(term), r[0], query,
                                            )
                                        continue
                                filtered_rows.append(r)
                            else:
                                # Detección de misses para logging estructurado
                                for term in norm_query_terms:
                                    if term not in chunk_norm_set and 4 <= len(term) <= 5:
                                        logger.warning(
                                            "COVERAGE_GUARD_MISS: term='%s' (len=%d) not covered in chunk '%s' for query='%s'",
                                            term, len(term), r[0], query,
                                        )

                    if not filtered_rows and n_terms > 0:
                        for term in norm_query_terms:
                            if 4 <= len(term) <= 5:
                                logger.warning(
                                    "COVERAGE_GUARD_MISS: term='%s' (len=%d) yielded 0 admissions for query='%s'",
                                    term, len(term), query,
                                )

                    rows = filtered_rows[:limit]

            return [
                SearchResult(
                    chunk_id=r[0],
                    document_id=r[1],
                    source_id=r[2],
                    score=float(r[3]),
                    snippet=r[4],
                    content=r[5],
                    index=int(r[6]),
                    page_start=r[7] if len(r) > 7 else None,
                    page_end=r[8] if len(r) > 8 else None,
                )
                for r in rows
            ]

        return self.lexical_index.search(
            query=query,
            limit=limit,
            source_id=source_id,
            document_id=document_id,
        )

    # ------------------------------------------------------------------
    # HYBRID SEARCH (SEMANTIC VECTOR + LEXICAL FTS5 WITH RRF & DIVERSITY)
    # ------------------------------------------------------------------
    def fts_search(
        self,
        query: str,
        notebook_id: Optional[str] = None,
        source_id: Optional[str] = None,
        document_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[SearchResult]:
        """Direct FTS5 lexical BM25 search."""
        return self.search(
            query=query,
            notebook_id=notebook_id,
            source_id=source_id,
            document_id=document_id,
            limit=limit,
        )

    def vector_search(
        self,
        query: str,
        notebook_id: Optional[str] = None,
        limit: int = 100,
        vector_store: Optional[Any] = None,
        embedder: Optional[Any] = None,
    ) -> List[SearchResult]:
        """Dense semantic search across chunk embeddings with cosine similarity."""
        if not notebook_id:
            return []

        # Resolve vector store
        v_store = vector_store
        if v_store is None:
            if hasattr(self, "_vector_store") and self._vector_store:
                v_store = self._vector_store
            else:
                try:
                    from study_engine.retrieval.vector_store import SQLiteVectorStore
                    candidate_paths = [
                        Path("data/web_state/vector_store.db"),
                        Path("data/benchmark/db/benchmark_vectors.db"),
                        Path(__file__).resolve().parents[3] / "data/web_state/vector_store.db",
                        Path(__file__).resolve().parents[3] / "data/benchmark/db/benchmark_vectors.db",
                    ]
                    for cp in candidate_paths:
                        if cp.exists():
                            v_store = SQLiteVectorStore(cp)
                            self._vector_store = v_store
                            break
                except Exception as ex:
                    logger.debug("VectorStore resolution: %s", ex)
                    v_store = None

        # Si el almacén de vectores no tiene vectores para este cuaderno,
        # NO cargar el modelo ONNX ni calcular embeddings en RAM innecesariamente.
        # FTS5 (SQLite puro) resolverá la búsqueda en ~6ms con 0 RAM extra.
        if v_store is not None and hasattr(v_store, "get_vector_matrix"):
            chunk_ids, matrix = v_store.get_vector_matrix(notebook_id)
            if len(chunk_ids) == 0 or matrix is None or matrix.size == 0:
                return []
        else:
            return []

        # Resolve embedder solo si hay vectores que comparar
        emb = embedder
        if emb is None:
            if hasattr(self, "_embedder") and self._embedder:
                emb = self._embedder
            else:
                try:
                    import sentence_transformers  # noqa: F401
                    from study_engine.retrieval.embedding import SentenceTransformerEmbeddingProvider
                    emb = SentenceTransformerEmbeddingProvider()
                    self._embedder = emb
                except Exception as ex_st:
                    logger.debug("SentenceTransformerEmbeddingProvider resolution: %s", ex_st)
                    emb = None

                if emb is None:
                    try:
                        from study_engine.retrieval.embedding import LocalONNXEmbeddingProvider
                        repo_root = Path(__file__).resolve().parents[3]
                        candidate_models = [
                            Path("models/multilingual-e5-small/onnx/model.onnx"),
                            repo_root / "models/multilingual-e5-small/onnx/model.onnx",
                        ]
                        for mp in candidate_models:
                            tp = mp.parent / "tokenizer.json"
                            if mp.exists() and tp.exists():
                                emb = LocalONNXEmbeddingProvider(model_path=mp, tokenizer_path=tp, num_threads=4)
                                self._embedder = emb
                                break
                    except Exception as ex_onnx:
                        logger.debug("LocalONNXEmbeddingProvider resolution: %s", ex_onnx)
                        emb = None

                if emb is None:
                    try:
                        from study_engine.retrieval.embedding import DeterministicHashEmbedder
                        dim = 1024
                        if matrix is not None and hasattr(matrix, "shape") and len(matrix.shape) > 1 and matrix.shape[1] > 0:
                            dim = matrix.shape[1]
                        emb = DeterministicHashEmbedder(dimensions=dim)
                        self._embedder = emb
                    except Exception as ex:
                        logger.debug("DeterministicHashEmbedder resolution: %s", ex)
                        emb = None

        if not emb:
            return []

        try:
            q_vec = emb.embed_query(query)
            q_arr = np.array(q_vec, dtype=np.float32)
            q_norm = np.linalg.norm(q_arr)
            if q_norm > 0:
                q_arr /= q_norm

            if len(chunk_ids) == 0 or matrix is None or matrix.size == 0:
                # Fallback to get_by_notebook if get_vector_matrix returned empty or wasn't available
                records = v_store.get_by_notebook(notebook_id)
                valid_recs = [rec for rec in records if len(rec.vector) == len(q_vec)]
                if not valid_recs:
                    return []
                chunk_ids = [r.chunk_id for r in valid_recs]
                matrix = np.array([r.vector for r in valid_recs], dtype=np.float32)

            if matrix.size == 0 or matrix.shape[1] != len(q_vec):
                return []

            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            norms = np.clip(norms, a_min=1e-9, a_max=None)
            norm_matrix = matrix / norms

            sims = np.dot(norm_matrix, q_arr)
            top_k_indices = np.argsort(sims)[::-1][:limit]

            results: List[SearchResult] = []
            for idx in top_k_indices:
                sim = float(sims[idx])
                cid = chunk_ids[idx]
                chunk = None
                try:
                    chunk = self.get_chunk(cid)
                except Exception:
                    chunk = None

                if chunk:
                    results.append(
                        SearchResult(
                            chunk_id=chunk.id,
                            document_id=chunk.document_id,
                            source_id=chunk.source_id,
                            score=round(sim, 4),
                            snippet=chunk.content[:160] + "...",
                            content=chunk.content,
                            index=getattr(chunk, "index", 0),
                            page_start=chunk.page_start,
                            page_end=chunk.page_end,
                        )
                    )
            return results
        except Exception as e:
            logger.warning("Vector search fallback exception: %s", e)
            return []

    def reciprocal_rank_fusion(
        self,
        *result_lists: List[SearchResult],
        k: int = 60,
    ) -> List[SearchResult]:
        """Combine rankings from multiple search streams via Reciprocal Rank Fusion (RRF)."""
        scores: Dict[str, Dict[str, Any]] = {}
        for r_list in result_lists:
            for rank, item in enumerate(r_list):
                cid = item.chunk_id
                if cid not in scores:
                    scores[cid] = {"item": item, "score": 0.0}
                scores[cid]["score"] += 1.0 / float(k + rank + 1)

        sorted_items = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
        out: List[SearchResult] = []
        for r in sorted_items:
            it = r["item"]
            out.append(
                SearchResult(
                    chunk_id=it.chunk_id,
                    document_id=it.document_id,
                    source_id=it.source_id,
                    score=round(r["score"], 6),
                    snippet=it.snippet,
                    content=it.content,
                    index=it.index,
                    page_start=it.page_start,
                    page_end=it.page_end,
                )
            )
        return out

    def _ensure_source_diversity(
        self,
        chunks: List[SearchResult],
        min_sources: int = 3,
    ) -> List[SearchResult]:
        """Ensure chunk diversity across multiple distinct sources."""
        if not chunks or min_sources <= 1:
            return list(chunks)

        by_source: Dict[str, List[SearchResult]] = {}
        for c in chunks:
            by_source.setdefault(c.source_id, []).append(c)

        diverse: List[SearchResult] = []
        seen_ids = set()

        # Step 1: take top chunk from distinct sources up to min_sources
        for src_id in list(by_source.keys())[:min_sources]:
            if by_source[src_id]:
                c = by_source[src_id].pop(0)
                diverse.append(c)
                seen_ids.add(c.chunk_id)

        # Step 2: append remaining chunks by original rank order
        for c in chunks:
            if c.chunk_id not in seen_ids:
                diverse.append(c)
                seen_ids.add(c.chunk_id)

        return diverse

    def search_hybrid(
        self,
        query: str,
        notebook_id: str,
        limit: int = 30,
        min_sources: int = 3,
        vector_store: Optional[Any] = None,
        embedder: Optional[Any] = None,
    ) -> List[SearchResult]:
        # Query passed from upstream retrieval chokepoint (C1)
        effective_query = query

        vector_results = self.vector_search(
            query=effective_query,
            notebook_id=notebook_id,
            limit=max(limit * 2, 50),
            vector_store=vector_store,
            embedder=embedder,
        )

        # Enmienda E1: Limitar disyunciones a top-50 por BM25 para evitar ruido
        fts_results = self.fts_search(
            query=effective_query,
            notebook_id=notebook_id,
            limit=50,
        )

        # Gate anti-ruido calibrado: para evitar ruido puro en consultas OOD,
        # filtrar por similitud mínima. Si hay resultados FTS5, el umbral es el canónico (MIN_VECTOR_SIMILARITY);
        # si FTS5 devuelve vacío pero hay evidencia vectorial densa coherente (score >= 0.78),
        # permitir que los vectores aporten candidatos por proximidad semántica (fusión aditiva RRF sin hard gates).
        threshold = MIN_VECTOR_SIMILARITY if fts_results else min(MIN_VECTOR_SIMILARITY, 0.78)
        vector_results = [r for r in vector_results if r.score >= threshold]

        if vector_results and fts_results:
            fused = self.reciprocal_rank_fusion(vector_results, fts_results, k=60)
        elif vector_results:
            fused = vector_results
        else:
            fused = fts_results

        diverse = self._ensure_source_diversity(fused, min_sources=min_sources)
        return diverse[:limit]

    # ------------------------------------------------------------------
    # STATS & HEALTH
    # ------------------------------------------------------------------
    def get_stats(self) -> Dict[str, Any]:
        """Return consolidated counts and disk footprint."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM notebooks;")
            nb_count = int(cursor.fetchone()[0])

            cursor.execute("SELECT COUNT(*) FROM sources;")
            src_count = int(cursor.fetchone()[0])

            cursor.execute("SELECT COUNT(*) FROM documents;")
            doc_count = int(cursor.fetchone()[0])

            cursor.execute("SELECT COUNT(*) FROM chunks;")
            chk_count = int(cursor.fetchone()[0])

            cursor.execute("SELECT COUNT(*) FROM chunks_fts;")
            fts_count = int(cursor.fetchone()[0])

        db_size = 0
        if not self.engine._is_memory and isinstance(self.engine.db_path, Path):
            if self.engine.db_path.exists():
                db_size = self.engine.db_path.stat().st_size

        return {
            "notebooks_count": nb_count,
            "sources_count": src_count,
            "documents_count": doc_count,
            "chunks_count": chk_count,
            "fts_chunks_count": fts_count,
            "schema_version": self.engine.get_schema_version(),
            "db_size_bytes": db_size,
        }

    def verify_integrity(self) -> bool:
        """Run SQLite integrity check and verify index synchronization."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            row = cursor.fetchone()
            if row is None or row[0] != "ok":
                return False

            try:
                cursor.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('integrity-check');")
            except Exception:
                return False

            return True

    # ------------------------------------------------------------------
    # PEDAGOGICAL CONTRACTS (FASE 5.8)
    # ------------------------------------------------------------------
    def save_pedagogical_contract(self, contract: Any) -> None:
        """Persist or update a PedagogicalContract bound to a notebook."""
        if not self.contains_notebook(contract.notebook_id):
            raise NotebookNotFoundError(contract.notebook_id)

        now = datetime.now(timezone.utc).isoformat()
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO pedagogical_contracts (
                    notebook_id, persona, base_system_prompt, forbidden_patterns_json,
                    safe_words_json, response_phases_json, required_analogies_json,
                    anti_errors_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(notebook_id) DO UPDATE SET
                    persona=excluded.persona,
                    base_system_prompt=excluded.base_system_prompt,
                    forbidden_patterns_json=excluded.forbidden_patterns_json,
                    safe_words_json=excluded.safe_words_json,
                    response_phases_json=excluded.response_phases_json,
                    required_analogies_json=excluded.required_analogies_json,
                    anti_errors_json=excluded.anti_errors_json,
                    updated_at=excluded.updated_at;
                """,
                (
                    contract.notebook_id,
                    contract.persona,
                    contract.base_system_prompt,
                    json.dumps(contract.forbidden_patterns),
                    json.dumps(contract.safe_words),
                    json.dumps([p.model_dump(mode="json") for p in contract.response_phases]),
                    json.dumps(contract.required_analogies),
                    json.dumps(contract.anti_errors),
                    now,
                    now,
                ),
            )

    def get_pedagogical_contract(self, notebook_id: str) -> Any:
        """Retrieve PedagogicalContract for notebook, falling back to canonical default."""
        clean_id = notebook_id.strip()
        try:
            with self.engine.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT persona, base_system_prompt, forbidden_patterns_json,
                           safe_words_json, response_phases_json, required_analogies_json,
                           anti_errors_json
                    FROM pedagogical_contracts
                    WHERE notebook_id = ?;
                    """,
                    (clean_id,),
                )
                row = cursor.fetchone()
        except Exception:
            row = None

        if row is None:
            from study_engine.pedagogy.fase0_seed import get_default_contract
            return get_default_contract(clean_id)

        persona, base_prompt, forbidden_j, safe_j, phases_j, analogies_j, anti_j = row
        phases_data = json.loads(phases_j)
        from study_engine.pedagogy.contract import PedagogicalContract
        from study_engine.pedagogy.response_phase import ResponsePhase
        phases = [ResponsePhase(**p) for p in phases_data]
        return PedagogicalContract(
            notebook_id=clean_id,
            persona=persona,
            base_system_prompt=base_prompt,
            forbidden_patterns=json.loads(forbidden_j),
            safe_words=json.loads(safe_j),
            response_phases=phases,
            required_analogies=json.loads(analogies_j),
            anti_errors=json.loads(anti_j),
        )

    def contains_pedagogical_contract(self, notebook_id: str) -> bool:
        """Check if an explicit custom PedagogicalContract exists for notebook."""
        clean_id = notebook_id.strip()
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM pedagogical_contracts WHERE notebook_id = ?;",
                (clean_id,),
            )
            return cursor.fetchone() is not None

    def delete_pedagogical_contract(self, notebook_id: str) -> bool:
        """Delete an explicit PedagogicalContract for notebook."""
        clean_id = notebook_id.strip()
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM pedagogical_contracts WHERE notebook_id = ?;",
                (clean_id,),
            )
            return cursor.rowcount > 0

    def compute_domain_distribution(
        self, notebook_id: str, kcs: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Compute chunk distribution for a given sovereign notebook.
        
        If kcs are provided, counts indexed chunks dynamically matching each KC's terms.
        Otherwise, counts chunks grouped by source_id.
        """
        clean_id = notebook_id.strip()
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            if kcs:
                cursor.execute(
                    """
                    SELECT c.content FROM chunks c
                    JOIN notebook_sources ns ON c.source_id = ns.source_id
                    WHERE ns.notebook_id = ?;
                    """,
                    (clean_id,),
                )
                chunk_contents = [row[0].lower() for row in cursor.fetchall()]
                results = []
                for kc in kcs:
                    kc_id = kc.get("kc_id", "")
                    title = kc.get("title", "")
                    words = [w.lower() for w in title.split() if len(w) > 4]
                    if words:
                        cnt = sum(1 for content in chunk_contents if any(w in content for w in words))
                    else:
                        cnt = len(chunk_contents)
                    results.append({"kc_id": kc_id, "chunk_count": cnt})
                return results

            # 1. Count chunks grouped by source_id for sources bound to this notebook
            cursor.execute(
                """
                SELECT c.source_id, COUNT(c.id) as chunk_count
                FROM chunks c
                JOIN notebook_sources ns ON c.source_id = ns.source_id
                WHERE ns.notebook_id = ?
                GROUP BY c.source_id
                ORDER BY chunk_count DESC;
                """,
                (clean_id,),
            )
            rows = cursor.fetchall()
            return [{"source_id": r[0], "chunk_count": r[1]} for r in rows]

    def get_notebook_sources_detailed(self, notebook_id: str) -> List[Dict[str, Any]]:
        """Retrieve detailed metadata and chunk counts of all sources linked to a notebook."""
        clean_id = notebook_id.strip()
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    s.source_id,
                    s.title,
                    s.sha256,
                    s.author,
                    s.metadata,
                    COUNT(c.id) as chunk_count
                FROM notebook_sources ns
                JOIN sources s ON ns.source_id = s.source_id
                LEFT JOIN chunks c ON s.source_id = c.source_id
                WHERE ns.notebook_id = ?
                GROUP BY s.source_id, s.title, s.sha256, s.author, s.metadata
                ORDER BY chunk_count DESC, s.title ASC;
                """,
                (clean_id,),
            )
            rows = cursor.fetchall()
            result = []
            for r in rows:
                meta = {}
                try:
                    if r[4]:
                        meta = json.loads(r[4])
                except Exception:
                    pass
                result.append({
                    "source_id": r[0],
                    "title": r[1] or r[0],
                    "sha256": r[2] or meta.get("sha256", ""),
                    "author": r[3] or "Cátedra",
                    "filename": meta.get("filename", f"{r[0]}.pdf"),
                    "page_count": meta.get("page_count", 0),
                    "chunk_count": r[5],
                })
            return result

    # ------------------------------------------------------------------
    # CHUNKING & EMBEDDINGS (LATE CHUNKING FASE 5)
    # ------------------------------------------------------------------
    def chunk_document(
        self,
        document_text: str,
        source_id: str,
        chunk_size: int = 512,
        overlap: int = 100,
    ) -> List[Dict[str, Any]]:
        """Chunking con soporte para Late Chunking opcional.

        Si enable_late_chunking está activo y el documento no excede
        max_document_tokens, usa Late Chunking. Si no, fallback a
        chunking tradicional.
        """
        from study_engine.config import get_settings

        settings = get_settings()

        # Intentar Late Chunking si está habilitado
        if settings.enable_late_chunking:
            try:
                from study_engine.retrieval.late_chunking import LateChunker

                late_chunker = LateChunker(
                    model_name=settings.late_chunking_model,
                    max_document_tokens=settings.late_chunking_max_tokens,
                )

                # Verificar si puede procesar el documento
                if late_chunker.can_process(document_text):
                    chunks = late_chunker.late_chunk(
                        document_text,
                        chunk_size=chunk_size,
                        overlap=overlap,
                    )
                    logger.info("Late Chunking applied to %s: %d chunks", source_id, len(chunks))
                    return chunks
                else:
                    logger.warning(
                        "Document %s exceeds max_document_tokens (%d), falling back to traditional chunking",
                        source_id,
                        settings.late_chunking_max_tokens,
                    )
            except Exception as e:
                logger.error("Late Chunking failed for %s: %s, falling back", source_id, e)

        # Fallback a chunking tradicional
        return self._traditional_chunk(document_text, chunk_size, overlap)

    def _traditional_chunk(
        self,
        document_text: str,
        chunk_size: int = 512,
        overlap: int = 100,
    ) -> List[Dict[str, Any]]:
        """Chunking tradicional por tamaño fijo."""
        chunks: List[Dict[str, Any]] = []
        words = document_text.split()
        if not words:
            return chunks

        safe_overlap = max(0, min(overlap, chunk_size - 1))
        step = max(1, chunk_size - safe_overlap)

        for i in range(0, len(words), step):
            chunk_words = words[i : i + chunk_size]
            chunk_text = " ".join(chunk_words)

            chunks.append({
                "text": chunk_text,
                "embedding": self._get_embedding(chunk_text),
                "start_token": i,
                "end_token": i + len(chunk_words),
                "chunking_method": "traditional",
            })

        return chunks

    def _get_embedding(self, text: str) -> List[float]:
        """Obtiene el embedding vectorial de un texto usando el embedder disponible en KnowledgeStore."""
        emb = getattr(self, "_embedder", None)
        if emb is None:
            try:
                import sentence_transformers  # noqa: F401
                from study_engine.retrieval.embedding import SentenceTransformerEmbeddingProvider
                emb = SentenceTransformerEmbeddingProvider()
                self._embedder = emb
            except Exception as ex_st:
                logger.debug("SentenceTransformerEmbeddingProvider resolution in _get_embedding: %s", ex_st)
                emb = None

            if emb is None:
                try:
                    from study_engine.retrieval.embedding import LocalONNXEmbeddingProvider
                    repo_root = Path(__file__).resolve().parents[3]
                    candidate_models = [
                        Path("models/multilingual-e5-small/onnx/model.onnx"),
                        repo_root / "models/multilingual-e5-small/onnx/model.onnx",
                    ]
                    for mp in candidate_models:
                        tp = mp.parent / "tokenizer.json"
                        if mp.exists() and tp.exists():
                            emb = LocalONNXEmbeddingProvider(model_path=mp, tokenizer_path=tp, num_threads=4)
                            self._embedder = emb
                            break
                except Exception as ex_onnx:
                    logger.debug("LocalONNXEmbeddingProvider resolution in _get_embedding: %s", ex_onnx)
                    emb = None

            if emb is None:
                try:
                    from study_engine.retrieval.embedding import DeterministicHashEmbedder
                    emb = DeterministicHashEmbedder(dimensions=1024)
                    self._embedder = emb
                except Exception as ex:
                    logger.debug("DeterministicHashEmbedder resolution: %s", ex)
                    emb = None

        if emb is not None:
            try:
                if hasattr(emb, "embed_passages"):
                    return emb.embed_passages([text])[0]
                elif hasattr(emb, "embed_query"):
                    return emb.embed_query(text)
            except Exception as ex_emb:
                logger.debug("Error computing embedding: %s", ex_emb)

        return []

    def close(self) -> None:
        """Close storage engine connections."""
        self.engine.close()


