"""Unit tests for HybridRetriever in S3.5."""

from pathlib import Path
import pytest

from study_engine.contracts.catalog import (
    NotebookNotFoundError,
    SourceRecord,
)
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.retrieval import (
    RetrievalRequest,
    RetrievalStrategy,
)
from study_engine.retrieval.dense import DenseRetriever
from study_engine.retrieval.embedding import MockEmbeddingProvider
from study_engine.retrieval.fusion import FusedCandidate

from study_engine.retrieval.hybrid import HybridRetriever
from study_engine.retrieval.indexer import index_notebook_chunks
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.retrieval.vector_store import SQLiteVectorStore
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def setup_hybrid_env(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "hybrid_ks.db")
    store.initialize()
    store.create_notebook(Notebook(id="nb-so", name="SO"))

    rec = SourceRecord(
        source_id="src-so",
        manifest=SourceManifest(
            source_id="src-so",
            filename="so.pdf",
            byte_size=100,
            sha256="a" * 64,
        ),
    )
    docs = [
        Document(
            id="doc-1",
            source_id="src-so",
            title="Procesos",
            content="Los procesos en sistemas operativos",
        ),
        Document(
            id="doc-2",
            source_id="src-so",
            title="Memoria",
            content="La memoria virtual y paginacion",
        ),
    ]
    chunks = [
        Chunk(
            id="c1",
            document_id="doc-1",
            source_id="src-so",
            content="Un proceso zombie es un proceso finalizado",
            index=0,
        ),
        Chunk(
            id="c2",
            document_id="doc-1",
            source_id="src-so",
            content="El algoritmo Round Robin asigna un quantum",
            index=1,
        ),
        Chunk(
            id="c3",
            document_id="doc-2",
            source_id="src-so",
            content="La paginacion jerarquica multinivel",
            index=0,
        ),
    ]
    store.store_ingestion_bundle(rec, docs, chunks, notebook_id="nb-so")

    vec_store = SQLiteVectorStore(tmp_path / "hybrid_vecs.db")
    provider = MockEmbeddingProvider(dimensions=384)
    index_notebook_chunks(store, vec_store, provider, "nb-so")

    lex_retriever = LexicalRetriever(store)
    dense_retriever = DenseRetriever(store, vec_store, provider)
    hybrid_retriever = HybridRetriever(store, lex_retriever, dense_retriever)

    return store, lex_retriever, dense_retriever, hybrid_retriever


def test_hybrid_retriever_initialization_type_checks(setup_hybrid_env):
    store, lex_retriever, dense_retriever, _ = setup_hybrid_env

    with pytest.raises(TypeError):
        HybridRetriever("bad", lex_retriever, dense_retriever)  # type: ignore

    with pytest.raises(TypeError):
        HybridRetriever(store, "bad", dense_retriever)  # type: ignore

    with pytest.raises(TypeError):
        HybridRetriever(store, lex_retriever, "bad")  # type: ignore

    with pytest.raises(TypeError):
        HybridRetriever(
            store,
            lex_retriever,
            dense_retriever,
            fusion_strategy="bad",  # type: ignore
        )

    with pytest.raises(ValueError):

        HybridRetriever(
            store, lex_retriever, dense_retriever, candidate_pool_factor=0
        )


def test_hybrid_retriever_rejects_invalid_request_type(setup_hybrid_env):
    _, _, _, hybrid_retriever = setup_hybrid_env
    with pytest.raises(TypeError):
        hybrid_retriever.retrieve("not-a-request")  # type: ignore


def test_hybrid_retriever_rejects_non_existent_notebook(setup_hybrid_env):
    _, _, _, hybrid_retriever = setup_hybrid_env
    req = RetrievalRequest(
        query="test", notebook_id="nb-non-existent", top_k=5
    )
    with pytest.raises(NotebookNotFoundError):
        hybrid_retriever.retrieve(req)


def test_hybrid_retriever_basic_search_and_provenance(setup_hybrid_env):
    _, _, _, hybrid_retriever = setup_hybrid_env
    req = RetrievalRequest(
        query="proceso zombie",
        notebook_id="nb-so",
        top_k=3,
        strategy=RetrievalStrategy.HYBRID,
    )
    resp = hybrid_retriever.retrieve(req)

    assert resp.strategy_used == RetrievalStrategy.HYBRID
    assert resp.notebook_id == "nb-so"
    assert len(resp.items) > 0
    assert len(resp.items) <= 3

    # Check top candidate provenance
    top = resp.items[0]
    assert top.rank == 1
    assert top.retrieval_method == "hybrid_rrf"
    assert "fused_score" in top.metadata
    assert "in_lexical" in top.metadata
    assert "in_dense" in top.metadata

    # Diagnostics check
    diag = resp.diagnostics
    assert diag.lexical_candidates_count is not None
    assert diag.dense_candidates_count is not None
    assert diag.unique_candidates_count > 0
    assert "retrieval_ms" in diag.latencies_ms
    assert "lexical_ms" in diag.latencies_ms
    assert "dense_ms" in diag.latencies_ms
    assert "fusion_ms" in diag.latencies_ms


def test_hybrid_retriever_custom_fusion_strategy(setup_hybrid_env):
    store, lex_retriever, dense_retriever, _ = setup_hybrid_env

    class CustomFixedFusion:
        def fuse(self, lexical_items, dense_items, top_k):
            # Returns items strictly from dense

            return [
                FusedCandidate(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    source_id=c.source_id,
                    notebook_id=c.notebook_id,
                    score=999.0,
                    content=c.content,
                    dense_rank=c.rank,
                    dense_score=c.score,
                )
                for c in dense_items[:top_k]
            ]

    custom_hybrid = HybridRetriever(
        store,
        lex_retriever,
        dense_retriever,
        fusion_strategy=CustomFixedFusion(),
    )
    req = RetrievalRequest(query="proceso", notebook_id="nb-so", top_k=2)
    resp = custom_hybrid.retrieve(req)
    assert len(resp.items) <= 2
    assert resp.items[0].score == 999.0
