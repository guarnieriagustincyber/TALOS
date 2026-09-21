"""Unit tests for embedding indexer in S3.4."""

from pathlib import Path
import pytest

from study_engine.contracts.catalog import NotebookNotFoundError, SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook

from study_engine.retrieval.embedding import (
    EmbeddingDimensionMismatchError,
    MockEmbeddingProvider,
)
from study_engine.retrieval.indexer import index_notebook_chunks
from study_engine.retrieval.vector_store import SQLiteVectorStore
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def populated_store(tmp_path: Path) -> KnowledgeStore:
    store = KnowledgeStore(tmp_path / "indexer_test.db")
    store.initialize()

    store.create_notebook(Notebook(id="nb-so", name="SO"))
    rec = SourceRecord(
        source_id="src-so",
        manifest=SourceManifest(source_id="src-so", filename="so.pdf", byte_size=10, sha256="a"*64),
    )
    docs = [Document(id="doc-1", source_id="src-so", title="SO", content="c")]
    chunks = [
        Chunk(id="c1", document_id="doc-1", source_id="src-so", content="Chunk 1", index=0),
        Chunk(id="c2", document_id="doc-1", source_id="src-so", content="Chunk 2", index=1),
    ]
    store.store_ingestion_bundle(rec, docs, chunks, notebook_id="nb-so")
    return store


def test_index_notebook_chunks_success(populated_store: KnowledgeStore, tmp_path: Path):
    vec_store = SQLiteVectorStore(tmp_path / "vecs.db")
    prov = MockEmbeddingProvider(dimensions=384)

    indexed = index_notebook_chunks(populated_store, vec_store, prov, "nb-so")
    assert indexed == 2
    assert vec_store.count("nb-so") == 2

    # Verify stored record integrity
    recs = vec_store.get_by_notebook("nb-so")
    assert len(recs) == 2
    assert recs[0].dimensions == 384
    assert recs[0].provider_id == "mock"
    assert recs[0].model_id == "mock-sha256-v1"


def test_index_notebook_chunks_non_existent_notebook(populated_store: KnowledgeStore, tmp_path: Path):
    vec_store = SQLiteVectorStore(tmp_path / "vecs.db")
    prov = MockEmbeddingProvider(dimensions=384)

    with pytest.raises(NotebookNotFoundError):
        index_notebook_chunks(populated_store, vec_store, prov, "non-existent-nb")


def test_index_notebook_chunks_empty_notebook(populated_store: KnowledgeStore, tmp_path: Path):
    populated_store.create_notebook(Notebook(id="nb-empty", name="Empty"))
    vec_store = SQLiteVectorStore(tmp_path / "vecs.db")
    prov = MockEmbeddingProvider(dimensions=384)

    indexed = index_notebook_chunks(populated_store, vec_store, prov, "nb-empty")
    assert indexed == 0


def test_index_notebook_chunks_dimension_mismatch(populated_store: KnowledgeStore, tmp_path: Path):
    vec_store = SQLiteVectorStore(tmp_path / "vecs.db")

    class BadDimProvider(MockEmbeddingProvider):
        def embed_passages(self, texts):
            return [[0.1] * 128 for _ in texts]  # Returns 128 instead of declared 384

    bad_prov = BadDimProvider(dimensions=384)
    with pytest.raises(EmbeddingDimensionMismatchError):
        index_notebook_chunks(populated_store, vec_store, bad_prov, "nb-so")

def test_index_notebook_chunks_vector_count_mismatch(populated_store: KnowledgeStore, tmp_path: Path):
    vec_store = SQLiteVectorStore(tmp_path / "vecs.db")

    class BadCountProvider(MockEmbeddingProvider):
        def embed_passages(self, texts):
            return [[0.1] * 384]  # Returns 1 vector instead of 2

    bad_prov = BadCountProvider(dimensions=384)
    with pytest.raises(ValueError) as exc:
        index_notebook_chunks(populated_store, vec_store, bad_prov, "nb-so")
    assert "Provider returned 1 vectors for 2 chunks" in str(exc.value)
