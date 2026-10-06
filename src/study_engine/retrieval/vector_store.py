"""Dedicated SQLite vector storage for S3.4 Dense Retrieval."""

from collections import OrderedDict
from pathlib import Path
import sqlite3
import struct
import threading
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union, runtime_checkable

from pydantic import Field, field_validator

from study_engine.contracts.base import BaseContract


class VectorRecord(BaseContract):
    """Vector record with full model and curricular provenance."""

    chunk_id: str = Field(..., min_length=1)
    notebook_id: str = Field(..., min_length=1)
    source_id: str = Field(..., min_length=1)
    provider_id: str = Field(..., min_length=1)
    model_id: str = Field(..., min_length=1)
    dimensions: int = Field(..., gt=0)
    vector: List[float] = Field(...)

    @field_validator("vector")
    @classmethod
    def validate_vector_matches_dimensions(
        cls, v: List[float], info: object
    ) -> List[float]:
        # Basic validation: cannot be empty
        if not v:
            raise ValueError("Vector cannot be empty.")
        return v


@runtime_checkable
class VectorStore(Protocol):
    """Protocol for vector storage implementations."""

    def save_records(self, records: List[VectorRecord]) -> int:

        ...

    def get_by_notebook(
        self,
        notebook_id: str,
        provider_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> List[VectorRecord]:
        ...

    def delete_by_notebook(self, notebook_id: str) -> int:
        ...

    def count(self, notebook_id: Optional[str] = None) -> int:
        ...


class ReadOnlyVectorStoreError(RuntimeError):
    """Raised when a mutating operation is attempted on a read-only SQLiteVectorStore."""
    pass


class SQLiteVectorStore:
    """Proportional SQLite vector store using raw binary BLOBs."""

    def __init__(
        self,
        db_path: Union[str, Path] = ":memory:",
        read_only: bool = True,
    ) -> None:
        self.db_path = str(db_path)
        self.read_only = bool(read_only)

        if self.read_only:
            if self.db_path == ":memory:":
                raise ValueError("Cannot open an in-memory vector store in read-only mode.")
            path = Path(self.db_path)
            if not path.exists():
                raise FileNotFoundError(f"Vector store database not found: {self.db_path}")

            abs_path = path.resolve()
            uri = f"file:{abs_path.as_posix()}?mode=ro"
            self._conn = sqlite3.connect(uri, uri=True, check_same_thread=False)

            # Fail-closed check: verify schema has 'chunk_embeddings'
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='chunk_embeddings';"
            )
            if not cursor.fetchone():
                self._conn.close()
                raise RuntimeError(
                    f"Database at {self.db_path} does not contain required table 'chunk_embeddings'"
                )
        else:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode = WAL;")
            self._conn.execute("PRAGMA synchronous = NORMAL;")
            self._initialize_schema()

        # Caché LRU de matrices por (notebook_id, provider_id, model_id).
        # Máximo 2 cuadernos en memoria simultáneamente (evita fugas multi-GB).
        self._matrix_cache: OrderedDict[Tuple[str, Optional[str], Optional[str]], Tuple[int, List[str], Any]] = OrderedDict()
        self._matrix_lock = threading.Lock()

    def _initialize_schema(self) -> None:
        if self.read_only:
            raise ReadOnlyVectorStoreError(
                "Cannot initialize schema on a read-only SQLiteVectorStore."
            )
        # PK compuesta (chunk_id, notebook_id): una misma fuente puede pertenecer
        # a múltiples notebooks, y cada chunk debe ser recuperable semánticamente
        # en todos ellos sin colisiones de clave.
        sql = """
        CREATE TABLE IF NOT EXISTS chunk_embeddings (
            chunk_id TEXT NOT NULL,
            notebook_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            provider_id TEXT NOT NULL,
            model_id TEXT NOT NULL,
            dimensions INTEGER NOT NULL,
            vector BLOB NOT NULL,
            PRIMARY KEY (chunk_id, notebook_id)
        );
        CREATE INDEX IF NOT EXISTS idx_vec_notebook
            ON chunk_embeddings(notebook_id);
        CREATE INDEX IF NOT EXISTS idx_vec_source
            ON chunk_embeddings(source_id);
        """
        self._conn.executescript(sql)
        self._conn.commit()

    @staticmethod
    def _pack_vector(vector: List[float]) -> bytes:
        return struct.pack(f"{len(vector)}f", *vector)

    @staticmethod
    def _unpack_vector(blob: bytes, dimensions: int) -> List[float]:
        return list(struct.unpack(f"{dimensions}f", blob))

    def save_records(self, records: List[VectorRecord]) -> int:
        """Atomically insert or replace a batch of vector records."""
        if self.read_only:
            raise ReadOnlyVectorStoreError(
                "Cannot save records to a read-only SQLiteVectorStore."
            )
        if not records:
            return 0

        data = [
            (
                r.chunk_id,
                r.notebook_id,
                r.source_id,
                r.provider_id,
                r.model_id,
                r.dimensions,
                self._pack_vector(r.vector),
            )
            for r in records
        ]

        sql = """
        INSERT OR REPLACE INTO chunk_embeddings
            (chunk_id, notebook_id, source_id, provider_id,
             model_id, dimensions, vector)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        cursor = self._conn.cursor()
        cursor.executemany(sql, data)
        self._conn.commit()

        # PRAGMA data_version no cambia ante commits de ESTA misma conexión:
        # invalidar explícitamente los notebooks afectados para que la matriz
        # cacheada no quede obsoleta (cubre el path de sync-vectors).
        affected = {r.notebook_id for r in records}
        with self._matrix_lock:
            for k in [k for k in self._matrix_cache if k[0] in affected]:
                del self._matrix_cache[k]
        return len(records)

    def get_by_notebook(
        self,
        notebook_id: str,
        provider_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> List[VectorRecord]:
        """Fetch vectors strictly partitioned by notebook."""
        query = """
        SELECT chunk_id, notebook_id, source_id, provider_id,
               model_id, dimensions, vector
        FROM chunk_embeddings
        WHERE notebook_id = ?
        """
        params: List[Union[str, int]] = [notebook_id]

        if provider_id:
            query += " AND provider_id = ?"
            params.append(provider_id)
        if model_id:
            query += " AND model_id = ?"
            params.append(model_id)

        query += " ORDER BY chunk_id ASC;"

        cursor = self._conn.cursor()
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

        return [
            VectorRecord(
                chunk_id=r[0],
                notebook_id=r[1],
                source_id=r[2],
                provider_id=r[3],
                model_id=r[4],
                dimensions=r[5],
                vector=self._unpack_vector(r[6], r[5]),
            )
            for r in rows
        ]

    def get_vector_matrix(
        self,
        notebook_id: str,
        provider_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> Tuple[List[str], Any]:
        """Fetch chunk IDs and stacked 2D float32 NumPy matrix directly from binary BLOBs.

        Caché en memoria por (notebook_id, provider_id, model_id): la matriz
        se recarga solo si cambió `PRAGMA data_version` (commit de otra
        conexión/proceso) o si `save_records` invalidó el notebook.
        """
        import numpy as np

        key = (notebook_id, provider_id, model_id)
        with self._matrix_lock:
            try:
                row = self._conn.execute("PRAGMA data_version;").fetchone()
                data_version = int(row[0]) if row else 0
            except Exception:
                data_version = 0

            cached = self._matrix_cache.get(key)
            if cached is not None and cached[0] == data_version:
                self._matrix_cache.move_to_end(key)
                return cached[1], cached[2]

            query = """
            SELECT chunk_id, dimensions, vector
            FROM chunk_embeddings
            WHERE notebook_id = ?
            """
            params: List[Union[str, int]] = [notebook_id]
            if provider_id:
                query += " AND provider_id = ?"
                params.append(provider_id)
            if model_id:
                query += " AND model_id = ?"
                params.append(model_id)

            query += " ORDER BY chunk_id ASC;"
            cursor = self._conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            if not rows:
                return [], np.empty((0, 0), dtype=np.float32)

            dim = rows[0][1]
            chunk_ids = [r[0] for r in rows if len(r[2]) == dim * 4]
            raw_concat = b"".join(r[2] for r in rows if len(r[2]) == dim * 4)
            matrix = np.frombuffer(raw_concat, dtype=np.float32).reshape((len(chunk_ids), dim))

            # Mantener en RAM como máximo 8 cuadernos (LRU eviction)
            if len(self._matrix_cache) >= 8 and key not in self._matrix_cache:
                self._matrix_cache.popitem(last=False)
            self._matrix_cache[key] = (data_version, chunk_ids, matrix)
            self._matrix_cache.move_to_end(key)
            return chunk_ids, matrix

    def get_by_chunk_id(self, chunk_id: str) -> Optional[VectorRecord]:
        """Fetch a single vector record by chunk ID."""
        sql = """
        SELECT chunk_id, notebook_id, source_id, provider_id,
               model_id, dimensions, vector
        FROM chunk_embeddings
        WHERE chunk_id = ?;
        """
        cursor = self._conn.cursor()
        cursor.execute(sql, (chunk_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return VectorRecord(
            chunk_id=row[0],
            notebook_id=row[1],
            source_id=row[2],
            provider_id=row[3],
            model_id=row[4],
            dimensions=row[5],
            vector=self._unpack_vector(row[6], row[5]),
        )

    def delete_by_notebook(self, notebook_id: str) -> int:
        """Delete all vectors belonging to a notebook."""
        if self.read_only:
            raise ReadOnlyVectorStoreError(
                "Cannot delete records from a read-only SQLiteVectorStore."
            )
        cursor = self._conn.cursor()
        cursor.execute(
            "DELETE FROM chunk_embeddings WHERE notebook_id = ?;",
            (notebook_id,),
        )
        self._conn.commit()
        return cursor.rowcount

    def delete_by_source(self, source_id: str) -> int:
        """Delete all vectors belonging to a source."""
        if self.read_only:
            raise ReadOnlyVectorStoreError(
                "Cannot delete records from a read-only SQLiteVectorStore."
            )
        cursor = self._conn.cursor()
        cursor.execute(
            "DELETE FROM chunk_embeddings WHERE source_id = ?;",
            (source_id,),
        )
        self._conn.commit()
        return cursor.rowcount

    def count(self, notebook_id: Optional[str] = None) -> int:
        """Count stored vectors."""
        cursor = self._conn.cursor()
        if notebook_id:
            cursor.execute(
                "SELECT COUNT(*) FROM chunk_embeddings WHERE notebook_id = ?;",
                (notebook_id,),
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM chunk_embeddings;")
        res = cursor.fetchone()
        return int(res[0]) if res else 0

    def close(self) -> None:
        """Close SQLite database connection."""
        self._conn.close()


__all__ = [
    "VectorRecord",
    "VectorStore",
    "SQLiteVectorStore",
    "ReadOnlyVectorStoreError",
]
