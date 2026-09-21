"""Unit tests for LexicalRetriever in S3.3."""

from pathlib import Path
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.retrieval import (
    RetrievalRequest,
    RetrievalStrategy,
)
from study_engine.retrieval.base import BaseRetriever
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def test_store(tmp_path: Path) -> KnowledgeStore:
    store = KnowledgeStore(tmp_path / "lexical_test.db")
    store.initialize()

    store.create_notebook(Notebook(id="nb-so", name="SO"))
    rec = SourceRecord(
        source_id="src-so",
        manifest=SourceManifest(source_id="src-so", filename="so.pdf", byte_size=10, sha256="a"*64),
    )
    docs = [
        Document(id="doc-1", source_id="src-so", title="Procesos", content="Procesos y memoria"),
        Document(id="doc-2", source_id="src-so", title="Memoria", content="Memoria y paginacion"),
    ]
    chunks = [
        Chunk(id="c1", document_id="doc-1", source_id="src-so", content="Un proceso zombie es un proceso difunto", index=0),
        Chunk(id="c2", document_id="doc-1", source_id="src-so", content="Algoritmo de planificacion Round Robin", index=1),
        Chunk(id="c3", document_id="doc-2", source_id="src-so", content="La memoria virtual y las tablas de paginas", index=0),
        Chunk(id="c4", document_id="doc-1", source_id="src-so", content="Un deadlock ocurre cuando dos procesos esperan recursos mutuamente", index=2),
        Chunk(id="c5", document_id="doc-1", source_id="src-so", content="Las condiciones de carrera surgen cuando multiples hilos acceden a memoria", index=3),
    ]
    store.store_ingestion_bundle(rec, docs, chunks, notebook_id="nb-so")
    return store


def test_lexical_retriever_initialization(test_store: KnowledgeStore) -> None:
    retriever = LexicalRetriever(test_store)
    assert isinstance(retriever, BaseRetriever)

    with pytest.raises(TypeError):
        LexicalRetriever("not-a-store")  # type: ignore


def test_lexical_retriever_basic_search(test_store: KnowledgeStore) -> None:
    retriever = LexicalRetriever(test_store)
    req = RetrievalRequest(query="proceso zombie", notebook_id="nb-so", top_k=5)

    response = retriever.retrieve(req)
    assert response.query == "proceso zombie"
    assert response.notebook_id == "nb-so"
    assert response.strategy_used == RetrievalStrategy.LEXICAL
    assert len(response.items) > 0

    first = response.items[0]
    assert first.chunk_id == "c1"
    assert first.rank == 1
    assert first.retrieval_method == "lexical"
    assert first.score > 0.0  # -bm25 is positive in S2
    assert first.lexical_score == first.score
    assert first.dense_score is None

    # Telemetry
    assert response.diagnostics.lexical_candidates_count is not None
    assert response.diagnostics.lexical_candidates_count >= 1
    assert response.diagnostics.latencies_ms["retrieval_ms"] >= 0.0


def test_lexical_retriever_filters(test_store: KnowledgeStore) -> None:
    retriever = LexicalRetriever(test_store)

    # Filter to doc-2 only
    req_doc2 = RetrievalRequest(
        query="memoria",
        notebook_id="nb-so",
        top_k=5,
        document_ids=["doc-2"],
    )
    resp2 = retriever.retrieve(req_doc2)
    assert all(c.document_id == "doc-2" for c in resp2.items)

    # Filter to doc-1 only
    req_doc1 = RetrievalRequest(
        query="memoria",
        notebook_id="nb-so",
        top_k=5,
        document_ids=["doc-1"],
    )
    resp1 = retriever.retrieve(req_doc1)
    assert all(c.document_id == "doc-1" for c in resp1.items)


def test_lexical_retriever_rejects_invalid_request_type(test_store: KnowledgeStore) -> None:
    retriever = LexicalRetriever(test_store)
    with pytest.raises(TypeError):
        retriever.retrieve("not-a-request")  # type: ignore

def test_lexical_retriever_multi_filters(test_store: KnowledgeStore) -> None:
    retriever = LexicalRetriever(test_store)

    # Multi-document filter
    req_multi_doc = RetrievalRequest(
        query="memoria",
        notebook_id="nb-so",
        top_k=5,
        document_ids=["doc-1", "doc-2"],
    )
    resp_docs = retriever.retrieve(req_multi_doc)
    assert len(resp_docs.items) > 0
    assert all(c.document_id in {"doc-1", "doc-2"} for c in resp_docs.items)

    # Multi-source filter
    req_multi_src = RetrievalRequest(
        query="memoria",
        notebook_id="nb-so",
        top_k=5,
        source_ids=["src-so", "src-non-existent"],
    )
    resp_src = retriever.retrieve(req_multi_src)
    assert len(resp_src.items) > 0
    assert all(c.source_id == "src-so" for c in resp_src.items)

def test_lexical_retriever_single_source_filter(test_store: KnowledgeStore) -> None:
    retriever = LexicalRetriever(test_store)
    req = RetrievalRequest(
        query="memoria",
        notebook_id="nb-so",
        top_k=5,
        source_ids=["src-so"],
    )
    resp = retriever.retrieve(req)
    assert len(resp.items) > 0
    assert all(c.source_id == "src-so" for c in resp.items)


def test_lexical_stopwords_filtered(test_store: KnowledgeStore) -> None:
    """Verificar que '¿Qué es un deadlock?' produce match léxico si 'deadlock' existe en el corpus."""
    retriever = LexicalRetriever(test_store)
    req = RetrievalRequest(
        query="¿Qué es un deadlock?",
        notebook_id="nb-so",
        top_k=5,
    )
    resp = retriever.retrieve(req)
    assert len(resp.items) > 0
    assert resp.items[0].chunk_id == "c4"
    assert resp.items[0].score > 0.0
    assert resp.items[0].lexical_score is not None and resp.items[0].lexical_score > 0.0
    assert resp.diagnostics.rejection_reason is None


def test_lexical_all_stopwords_rejected(test_store: KnowledgeStore) -> None:
    """Verificar que '¿Qué es?' (solo stopwords) retorna vacío con motivo QUERY_ALL_STOPWORDS."""
    retriever = LexicalRetriever(test_store)
    req = RetrievalRequest(
        query="¿Qué es?",
        notebook_id="nb-so",
        top_k=5,
    )
    resp = retriever.retrieve(req)
    assert len(resp.items) == 0
    assert resp.diagnostics.unique_candidates_count == 0
    assert resp.diagnostics.rejection_reason == "QUERY_ALL_STOPWORDS"


def test_lexical_existing_queries_still_work(test_store: KnowledgeStore) -> None:
    """Verificar que queries que ya funcionaban (ej. 'condiciones de carrera') siguen funcionando."""
    retriever = LexicalRetriever(test_store)
    req = RetrievalRequest(
        query="condiciones de carrera",
        notebook_id="nb-so",
        top_k=5,
    )
    resp = retriever.retrieve(req)
    assert len(resp.items) > 0
    assert resp.items[0].chunk_id == "c5"
    assert resp.items[0].score > 0.0
    assert resp.items[0].lexical_score is not None and resp.items[0].lexical_score > 0.0
    assert resp.diagnostics.rejection_reason is None
