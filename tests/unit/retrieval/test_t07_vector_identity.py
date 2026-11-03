"""T07: synthetic vector-space binding and lexical baseline controls."""

from unittest.mock import patch
import sqlite3
import struct

import numpy as np
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.retrieval import RetrievalRequest
from study_engine.retrieval.dense import DenseRetrievalError, DenseRetriever
from study_engine.retrieval.embedding import (
    MockEmbeddingProvider, SentenceTransformerEmbeddingProvider,
)
from study_engine.retrieval.indexer import index_notebook_chunks
from study_engine.retrieval.vector_identity import vector_space_id
from study_engine.retrieval.vector_store import SQLiteVectorStore, VectorRecord
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def synthetic_index():
    store = KnowledgeStore(":memory:")
    store.initialize()
    store.create_notebook(Notebook(id="nb-a", name="Synthetic A"))
    store.create_notebook(Notebook(id="nb-b", name="Synthetic B"))
    source = SourceRecord(
        source_id="src-a",
        manifest=SourceManifest(
            source_id="src-a", filename="synthetic.txt", byte_size=1, sha256="a" * 64,
        ),
    )
    store.store_ingestion_bundle(
        source,
        [Document(id="doc-a", source_id="src-a", title="Synthetic")],
        [Chunk(id="chunk-a", document_id="doc-a", source_id="src-a",
               content="alpha deterministic retrieval", index=0)],
        notebook_id="nb-a",
    )
    vectors = SQLiteVectorStore(":memory:", read_only=False)
    provider = MockEmbeddingProvider(dimensions=16)
    index_notebook_chunks(store, vectors, provider, "nb-a")
    yield store, vectors, provider
    vectors.close()
    store.close()


def test_compatible_space_is_persisted_and_compared(synthetic_index):
    store, vectors, provider = synthetic_index
    record = vectors.get_by_notebook("nb-a")[0]
    assert record.space_id == vector_space_id(provider)
    assert store.vector_search("alpha deterministic retrieval", "nb-a", vector_store=vectors,
                               embedder=provider)[0].chunk_id == "chunk-a"
    assert store._vector_search_status == "COMPATIBLE"


@pytest.mark.parametrize("other", [
    MockEmbeddingProvider(dimensions=16, model_id="different-model"),
    MockEmbeddingProvider(dimensions=16, provider_id="different-provider"),
    MockEmbeddingProvider(dimensions=16, use_e5_prefix=True),
    MockEmbeddingProvider(dimensions=8),
])
def test_incompatible_identity_never_reaches_similarity(synthetic_index, other):
    store, vectors, _ = synthetic_index
    with patch.object(np, "dot", side_effect=AssertionError("similarity ran")):
        assert store.vector_search("alpha", "nb-a", vector_store=vectors,
                                   embedder=other) == []
    assert store._vector_search_status == "INCOMPATIBLE"


def test_legacy_unknown_cannot_rank_and_fts5_remains_available(synthetic_index):
    store, vectors, provider = synthetic_index
    record = vectors.get_by_notebook("nb-a")[0]
    vectors.save_records([record.model_copy(update={"space_id": None})])
    with patch.object(np, "dot", side_effect=AssertionError("similarity ran")):
        results = store.search_hybrid("alpha deterministic retrieval", "nb-a",
                                      vector_store=vectors, embedder=provider)
    assert store._vector_search_status == "UNKNOWN"
    assert [item.chunk_id for item in results] == ["chunk-a"]
    with pytest.raises(DenseRetrievalError):
        DenseRetriever(store, vectors, provider).retrieve(
            RetrievalRequest(query="alpha", notebook_id="nb-a", top_k=1)
        )


def test_other_notebook_vectors_cannot_influence_rank(synthetic_index):
    store, vectors, provider = synthetic_index
    assert store.vector_search("alpha", "nb-b", vector_store=vectors, embedder=provider) == []
    assert store.search_hybrid("alpha deterministic retrieval", "nb-a",
                               vector_store=vectors, embedder=provider)[0].chunk_id == "chunk-a"


def test_unconfigured_dense_is_not_implicitly_promoted(synthetic_index):
    store, _, _ = synthetic_index
    assert store.search_hybrid("alpha deterministic retrieval", "nb-a")[0].chunk_id == "chunk-a"
    assert store._vector_search_status == "VECTOR_DISABLED"


def test_unknown_provider_does_not_embed_or_compare(synthetic_index):
    store, vectors, _ = synthetic_index

    class Unknown:
        provider_id = "mock"
        model_id = "mock-sha256-v1"
        dimensions = 16

        def embed_query(self, _query):
            raise AssertionError("unknown provider was executed")

    assert store.vector_search("alpha", "nb-a", vector_store=vectors, embedder=Unknown()) == []
    assert store._vector_search_status == "UNKNOWN"


def test_pinned_model_revision_changes_space_identity():
    original = SentenceTransformerEmbeddingProvider(revision="revision-a")
    another = SentenceTransformerEmbeddingProvider(revision="revision-b")
    assert vector_space_id(original) != vector_space_id(another)


def test_matrix_filter_excludes_same_dimension_foreign_space(synthetic_index):
    store, vectors, provider = synthetic_index
    vectors.save_records([VectorRecord(
        chunk_id="foreign", notebook_id="nb-a", source_id="src-a",
        provider_id=provider.provider_id, model_id=provider.model_id,
        dimensions=provider.dimensions, vector=provider.embed_query("alpha"),
        space_id=vector_space_id(MockEmbeddingProvider(dimensions=16, use_e5_prefix=True)),
    )])
    assert [item.chunk_id for item in store.vector_search(
        "alpha", "nb-a", vector_store=vectors, embedder=provider
    )] == ["chunk-a"]


def test_legacy_schema_without_space_column_is_unknown(synthetic_index, tmp_path):
    store, _, provider = synthetic_index
    path = tmp_path / "legacy-vectors.db"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE chunk_embeddings (chunk_id TEXT, notebook_id TEXT, "
            "source_id TEXT, provider_id TEXT, model_id TEXT, dimensions INTEGER, vector BLOB)"
        )
        connection.execute(
            "INSERT INTO chunk_embeddings VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("chunk-a", "nb-a", "src-a", provider.provider_id, provider.model_id,
             provider.dimensions, struct.pack("16f", *provider.embed_query("alpha"))),
        )
    legacy = SQLiteVectorStore(path, read_only=True)
    try:
        assert store.vector_search("alpha", "nb-a", vector_store=legacy,
                                   embedder=provider) == []
        assert store._vector_search_status == "UNKNOWN"
        assert store.search_hybrid("alpha deterministic retrieval", "nb-a",
                                   vector_store=legacy, embedder=provider)
    finally:
        legacy.close()
