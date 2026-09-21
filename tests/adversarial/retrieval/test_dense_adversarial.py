"""Adversarial and side-by-side benchmark evaluation for DenseRetriever in S3.4."""

import json
from pathlib import Path
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.oracle import OracleDataset
from study_engine.contracts.retrieval import RetrievalRequest, RetrievalStrategy
from study_engine.retrieval.dense import DenseRetriever
from study_engine.retrieval.embedding import MockEmbeddingProvider
from study_engine.retrieval.evaluator import OracleEvaluator
from study_engine.retrieval.indexer import index_notebook_chunks
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.retrieval.vector_store import SQLiteVectorStore
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def populated_reference_env(tmp_path: Path):
    """Populate KnowledgeStore and SQLiteVectorStore with reference corpus."""
    with open("data/fixtures/reference_corpus.json", "r", encoding="utf-8") as f:
        corpus = json.load(f)

    store = KnowledgeStore(tmp_path / "reference_dense.db")
    store.initialize()

    for nb in corpus["notebooks"]:
        store.create_notebook(Notebook(
            id=nb["id"], name=nb["name"], description=nb["description"], subject=nb["subject"]
        ))

    for src in corpus["sources"]:
        manifest = SourceManifest(
            source_id=src["source_id"], filename=src["filename"], byte_size=src["byte_size"], sha256=src["sha256"]
        )
        store.save_source(SourceRecord(source_id=src["source_id"], manifest=manifest))
        store.link_source_to_notebook(src["notebook_id"], src["source_id"])

    for doc in corpus["documents"]:
        store.save_document(Document(
            id=doc["id"], source_id=doc["source_id"], title=doc["title"], content=doc["content"]
        ))

    chunks = [
        Chunk(
            id=c["id"], document_id=c["document_id"], source_id=c["source_id"],
            content=c["content"], index=c["index"]
        )
        for c in corpus["chunks"]
    ]
    store.save_chunks(chunks)

    vec_store = SQLiteVectorStore(tmp_path / "reference_vectors.db")
    provider = MockEmbeddingProvider(dimensions=384)

    # Index both notebooks separately
    index_notebook_chunks(store, vec_store, provider, "fadena-so")
    index_notebook_chunks(store, vec_store, provider, "fadena-prog")

    dense_retriever = DenseRetriever(store, vec_store, provider)
    lexical_retriever = LexicalRetriever(store)

    return store, vec_store, provider, dense_retriever, lexical_retriever


def test_adversarial_dense_query_fuzzing(populated_reference_env):
    """Stress test DenseRetriever with complex syntax, injections, and edge cases."""
    _, _, _, dense_retriever, _ = populated_reference_env
    fuzz_queries = [
        "malloc() void* free()",
        "*ptr = (uintptr_t*) malloc(sizeof(*ptr));",
        "O(log n) vs O(1)",
        "\"unclosed quote",
        "'unclosed single",
        "SELECT * FROM chunk_embeddings;",
        "<script>alert(1)</script>",
        "🔥 Memoria Virtual ⚡",
        "a" * 2500,
    ]

    for q in fuzz_queries:
        req = RetrievalRequest(query=q, notebook_id="fadena-prog", top_k=5)
        resp = dense_retriever.retrieve(req)
        assert resp.notebook_id == "fadena-prog"
        assert resp.strategy_used == RetrievalStrategy.DENSE
        for idx, item in enumerate(resp.items):
            assert item.rank == idx + 1
            assert item.notebook_id == "fadena-prog"
            assert -1.0 <= item.score <= 1.0


def test_adversarial_dense_curricular_isolation_attack(populated_reference_env):
    """Querying programming terms in OS notebook must yield 0 leakage."""
    _, _, _, dense_retriever, _ = populated_reference_env

    req = RetrievalRequest(
        query="árbol binario de búsqueda y recorrido inorden",
        notebook_id="fadena-so",
        top_k=5,
    )
    resp = dense_retriever.retrieve(req)
    # Binary search tree chunks are in fadena-prog.
    # Candidates returned from fadena-so must ONLY be fadena-so chunks.
    for item in resp.items:
        assert item.notebook_id == "fadena-so"
        assert not item.chunk_id.startswith("prog:")


def test_adversarial_dense_vs_lexical_comparative_oracle_benchmark(populated_reference_env):
    """Execute both LexicalRetriever and DenseRetriever against the Reference Oracle."""
    store, _, _, dense_retriever, lexical_retriever = populated_reference_env
    evaluator = OracleEvaluator(store)

    with open("data/fixtures/reference_oracle.json", "r", encoding="utf-8") as f:
        oracle_data = json.load(f)
    oracle_dataset = OracleDataset.model_validate(oracle_data)

    lexical_report = evaluator.evaluate(lexical_retriever, oracle_dataset, strategy=RetrievalStrategy.LEXICAL)
    dense_report = evaluator.evaluate(dense_retriever, oracle_dataset, strategy=RetrievalStrategy.DENSE)

    # Both must respect zero leakage
    assert lexical_report.global_metrics.leakage_rate == 0.0
    assert dense_report.global_metrics.leakage_rate == 0.0

    # Ensure Dense report covers all 6 categories
    assert len(dense_report.by_category) == 6
