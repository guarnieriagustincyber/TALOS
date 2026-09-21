"""Unit tests for DenseRetriever in S3.4."""

from pathlib import Path
import pytest

from study_engine.contracts.catalog import NotebookNotFoundError, SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook

from study_engine.contracts.retrieval import (
    RetrievalRequest,
    RetrievalStrategy,
)
from study_engine.retrieval.base import BaseRetriever
from study_engine.retrieval.dense import DenseRetriever
from study_engine.retrieval.embedding import (
    EmbeddingDimensionMismatchError,
    MockEmbeddingProvider,
)
from study_engine.retrieval.indexer import index_notebook_chunks
from study_engine.retrieval.vector_store import SQLiteVectorStore, VectorRecord

from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def setup_environment(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "dense_test.db")
    store.initialize()

    store.create_notebook(Notebook(id="nb-so", name="SO"))
    rec = SourceRecord(
        source_id="src-so",
        manifest=SourceManifest(source_id="src-so", filename="so.pdf", byte_size=10, sha256="a"*64),
    )
    docs = [
        Document(id="doc-1", source_id="src-so", title="Procesos", content="Procesos"),
        Document(id="doc-2", source_id="src-so", title="Memoria", content="Memoria"),
    ]
    chunks = [
        Chunk(id="c1", document_id="doc-1", source_id="src-so", content="Un proceso zombie es un proceso difunto", index=0),
        Chunk(id="c2", document_id="doc-1", source_id="src-so", content="Algoritmo de planificacion Round Robin", index=1),
        Chunk(id="c3", document_id="doc-2", source_id="src-so", content="La memoria virtual y las tablas de paginas", index=0),
    ]
    store.store_ingestion_bundle(rec, docs, chunks, notebook_id="nb-so")

    vec_store = SQLiteVectorStore(tmp_path / "vecs.db")
    provider = MockEmbeddingProvider(dimensions=384)
    index_notebook_chunks(store, vec_store, provider, "nb-so")

    retriever = DenseRetriever(store, vec_store, provider)
    return store, vec_store, provider, retriever


def test_dense_retriever_initialization_type_checks(setup_environment):
    store, vec_store, provider, retriever = setup_environment
    assert isinstance(retriever, BaseRetriever)

    with pytest.raises(TypeError):
        DenseRetriever("not-store", vec_store, provider)  # type: ignore

    with pytest.raises(TypeError):
        DenseRetriever(store, "not-vec-store", provider)  # type: ignore

    with pytest.raises(TypeError):
        DenseRetriever(store, vec_store, "not-provider")  # type: ignore


def test_dense_retriever_basic_search(setup_environment):
    store, vec_store, provider, retriever = setup_environment

    req = RetrievalRequest(query="proceso zombie", notebook_id="nb-so", top_k=2)
    resp = retriever.retrieve(req)

    assert resp.query == "proceso zombie"
    assert resp.notebook_id == "nb-so"
    assert resp.strategy_used == RetrievalStrategy.DENSE
    assert len(resp.items) == 2

    # ScoredCandidate checks
    for idx, item in enumerate(resp.items):
        assert item.rank == idx + 1
        assert item.retrieval_method == "dense"
        assert item.lexical_score is None
        assert item.dense_score == item.score
        assert -1.0 <= item.score <= 1.0
        assert item.notebook_id == "nb-so"

    # Telemetry breakdown
    lats = resp.diagnostics.latencies_ms
    assert "retrieval_ms" in lats
    assert "query_embedding_ms" in lats
    assert "vector_load_ms" in lats
    assert "similarity_ms" in lats
    assert "top_k_ms" in lats
    assert "hydration_ms" in lats


def test_dense_retriever_empty_notebook(setup_environment):
    store, vec_store, provider, retriever = setup_environment
    store.create_notebook(Notebook(id="nb-empty", name="Empty"))

    req = RetrievalRequest(query="test", notebook_id="nb-empty", top_k=5)
    resp = retriever.retrieve(req)

    assert len(resp.items) == 0
    assert resp.diagnostics.dense_candidates_count == 0


def test_dense_retriever_rejects_non_existent_notebook(setup_environment):
    _, _, _, retriever = setup_environment
    req = RetrievalRequest(query="test", notebook_id="non-existent", top_k=5)

    with pytest.raises(NotebookNotFoundError):
        retriever.retrieve(req)


def test_dense_retriever_dimension_mismatch(setup_environment):
    store, vec_store, _, _ = setup_environment

    # Provider with different dimensions
    bad_prov = MockEmbeddingProvider(dimensions=128)
    bad_retriever = DenseRetriever(store, vec_store, bad_prov)

    req = RetrievalRequest(query="test", notebook_id="nb-so", top_k=5)
    with pytest.raises(EmbeddingDimensionMismatchError):
        bad_retriever.retrieve(req)

def test_dense_retriever_rejects_invalid_request_type(setup_environment):
    _, _, _, retriever = setup_environment
    with pytest.raises(TypeError):
        retriever.retrieve("not-a-request")  # type: ignore


def test_dense_retriever_query_dimension_mismatch(setup_environment):
    store, vec_store, provider, retriever = setup_environment

    class BadQueryProvider(MockEmbeddingProvider):
        def embed_query(self, query):
            return [0.1] * 10  # 10 instead of 384

    bad_retriever = DenseRetriever(store, vec_store, BadQueryProvider(dimensions=384))
    req = RetrievalRequest(query="test", notebook_id="nb-so", top_k=5)
    with pytest.raises(EmbeddingDimensionMismatchError):
        bad_retriever.retrieve(req)


def test_dense_retriever_source_and_document_filters(setup_environment):
    store, vec_store, provider, retriever = setup_environment

    # Document filter
    req_doc = RetrievalRequest(
        query="proceso",
        notebook_id="nb-so",
        top_k=5,
        document_ids=["doc-1"],
    )
    resp_doc = retriever.retrieve(req_doc)
    assert len(resp_doc.items) > 0
    assert all(c.document_id == "doc-1" for c in resp_doc.items)

    # Source filter
    req_src = RetrievalRequest(
        query="proceso",
        notebook_id="nb-so",
        top_k=5,
        source_ids=["src-so"],
    )
    resp_src = retriever.retrieve(req_src)
    assert len(resp_src.items) > 0
    assert all(c.source_id == "src-so" for c in resp_src.items)

    # Non-matching source filter
    req_no_src = RetrievalRequest(
        query="proceso",
        notebook_id="nb-so",
        top_k=5,
        source_ids=["src-non-existent"],
    )
    resp_no_src = retriever.retrieve(req_no_src)
    assert len(resp_no_src.items) == 0


def test_dense_retriever_zero_vector_similarity(setup_environment):
    store, vec_store, provider, retriever = setup_environment
    # Add a zero vector record
    zero_rec = VectorRecord(
        chunk_id="c1",
        notebook_id="nb-so",
        source_id="src-so",
        provider_id=provider.provider_id,
        model_id=provider.model_id,
        dimensions=provider.dimensions,
        vector=[0.0] * provider.dimensions,
    )
    vec_store.save_records([zero_rec])

    req = RetrievalRequest(query="test", notebook_id="nb-so", top_k=5)
    resp = retriever.retrieve(req)
    assert len(resp.items) > 0
    c1_candidate = next(c for c in resp.items if c.chunk_id == "c1")
    # Zero vector cosine similarity evaluates to 0.0
    assert c1_candidate.score == 0.0

