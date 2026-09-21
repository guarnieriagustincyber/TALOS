"""Unit tests for SQLiteVectorStore in S3.4."""

from pathlib import Path
import pytest
from pydantic import ValidationError

from study_engine.retrieval.vector_store import (
    SQLiteVectorStore,
    VectorRecord,
    VectorStore,
)


def test_vector_record_validation():
    # Valid
    rec = VectorRecord(
        chunk_id="c1",
        notebook_id="nb1",
        source_id="src1",
        provider_id="mock",
        model_id="v1",
        dimensions=3,
        vector=[0.1, 0.2, 0.3],
    )
    assert rec.chunk_id == "c1"

    # Empty vector rejected
    with pytest.raises(ValidationError):
        VectorRecord(
            chunk_id="c1",
            notebook_id="nb1",
            source_id="src1",
            provider_id="mock",
            model_id="v1",
            dimensions=3,
            vector=[],
        )


def test_sqlite_vector_store_crud(tmp_path: Path):
    db_file = tmp_path / "test_vec.db"
    store = SQLiteVectorStore(db_file)
    assert isinstance(store, VectorStore)

    rec1 = VectorRecord(
        chunk_id="c1", notebook_id="nb-so", source_id="src-so",
        provider_id="mock", model_id="v1", dimensions=3, vector=[1.0, 0.0, 0.0]
    )
    rec2 = VectorRecord(
        chunk_id="c2", notebook_id="nb-so", source_id="src-so",
        provider_id="mock", model_id="v1", dimensions=3, vector=[0.0, 1.0, 0.0]
    )
    rec_prog = VectorRecord(
        chunk_id="c3", notebook_id="nb-prog", source_id="src-prog",
        provider_id="mock", model_id="v1", dimensions=3, vector=[0.0, 0.0, 1.0]
    )

    # 1. Batch Save
    assert store.save_records([rec1, rec2, rec_prog]) == 3
    assert store.save_records([]) == 0
    assert store.count() == 3
    assert store.count("nb-so") == 2
    assert store.count("nb-prog") == 1

    # 2. Get by Notebook (Strict Isolation)
    so_recs = store.get_by_notebook("nb-so")
    assert len(so_recs) == 2
    assert {r.chunk_id for r in so_recs} == {"c1", "c2"}
    assert so_recs[0].vector == pytest.approx([1.0, 0.0, 0.0])

    # 3. Model / Provider Filter
    assert len(store.get_by_notebook("nb-so", provider_id="other")) == 0
    assert len(store.get_by_notebook("nb-so", model_id="other")) == 0

    # 4. Get by Chunk ID
    single = store.get_by_chunk_id("c1")
    assert single is not None
    assert single.chunk_id == "c1"
    assert store.get_by_chunk_id("non-existent") is None

    # 5. Delete by Source
    deleted_src = store.delete_by_source("src-prog")
    assert deleted_src == 1
    assert store.count("nb-prog") == 0

    # 6. Delete by Notebook
    deleted_nb = store.delete_by_notebook("nb-so")
    assert deleted_nb == 2
    assert store.count() == 0

    store.close()
