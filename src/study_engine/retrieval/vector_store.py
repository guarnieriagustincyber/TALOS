"""Dedicated SQLite vector storage for S3.4 Dense Retrieval."""

from pathlib import Path
import sqlite3
import struct
from typing import Any, List, Optional, Protocol, Tuple, Union, runtime_checkable

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


class SQLiteVectorStore:
    """Proportional SQLite vector store using raw binary BLOBs."""

    def __init__(self, db_path: Union[str, Path] = ":memory:") -> None:
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode = WAL;")
        self._conn.execute("PRAGMA synchronous = NORMAL;")
        self._initialize_schema()

    def _initialize_schema(self) -> None:
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
        """Fetch chunk IDs and stacked 2D float32 NumPy matrix directly from binary BLOBs."""
        import numpy as np

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
        cursor = self._conn.cursor()
        cursor.execute(
            "DELETE FROM chunk_embeddings WHERE notebook_id = ?;",
            (notebook_id,),
        )
        self._conn.commit()
        return cursor.rowcount

    def delete_by_source(self, source_id: str) -> int:
        """Delete all vectors belonging to a source."""
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
