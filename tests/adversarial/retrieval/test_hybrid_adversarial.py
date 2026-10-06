"""Adversarial tests and 3-way benchmark verification for HybridRetriever."""

import json
from pathlib import Path
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.oracle import OracleDataset
from study_engine.contracts.retrieval import (
    RetrievalRequest,
    RetrievalStrategy,
)
from study_engine.retrieval.dense import DenseRetriever
from study_engine.retrieval.embedding import MockEmbeddingProvider
from study_engine.retrieval.evaluator import OracleEvaluator
from study_engine.retrieval.hybrid import HybridRetriever
from study_engine.retrieval.indexer import index_notebook_chunks
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.retrieval.vector_store import SQLiteVectorStore
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def populated_hybrid_environment(tmp_path: Path):
    corpus_path = Path("data/fixtures/reference_corpus.json")
    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus_data = json.load(f)

    store = KnowledgeStore(tmp_path / "adversarial_hybrid_corpus.db")
    store.initialize()

    for nb in corpus_data["notebooks"]:
        store.create_notebook(
            Notebook(
                id=nb["id"],
                name=nb["name"],
                description=nb["description"],
                subject=nb["subject"],
            )
        )

    for src in corpus_data["sources"]:
        manifest = SourceManifest(
            source_id=src["source_id"],
            filename=src["filename"],
            byte_size=src["byte_size"],
            sha256=src["sha256"],
        )
        store.save_source(
            SourceRecord(source_id=src["source_id"], manifest=manifest)
        )
        store.link_source_to_notebook(src["notebook_id"], src["source_id"])

    for doc in corpus_data["documents"]:
        store.save_document(
            Document(
                id=doc["id"],
                source_id=doc["source_id"],
                title=doc["title"],
                content=doc["content"],
            )
        )

    chunks = [
        Chunk(
            id=c["id"],
            document_id=c["document_id"],
            source_id=c["source_id"],
            content=c["content"],
            index=c["index"],
        )
        for c in corpus_data["chunks"]
    ]
    store.save_chunks(chunks)

    vec_store = SQLiteVectorStore(tmp_path / "adversarial_hybrid_vecs.db", read_only=False)
    provider = MockEmbeddingProvider(dimensions=384)

    index_notebook_chunks(store, vec_store, provider, "fadena-so")
    index_notebook_chunks(store, vec_store, provider, "fadena-prog")

    lex = LexicalRetriever(store)
    dense = DenseRetriever(store, vec_store, provider)
    hybrid = HybridRetriever(store, lex, dense)

    return store, vec_store, provider, lex, dense, hybrid


def test_adversarial_hybrid_query_fuzzing(populated_hybrid_environment):
    _, _, _, _, _, hybrid = populated_hybrid_environment

    fuzz_queries = [
        "   ",
        "'; DROP TABLE chunks; --",
        "SELECT * FROM chunks_fts WHERE content MATCH 'x'",
        "🚀 🤖 🔥 💻",
        "a" * 1000,
        "(((((((((((((((())))))))))))))))",
        '""" AND OR NOT NEAR """',
    ]

    for q in fuzz_queries:
        if not q.strip():
            with pytest.raises(ValueError):
                RetrievalRequest(query=q, notebook_id="fadena-so", top_k=5)
            continue

        req = RetrievalRequest(
            query=q,
            notebook_id="fadena-so",
            top_k=5,
            strategy=RetrievalStrategy.HYBRID,
        )
        resp = hybrid.retrieve(req)
        assert resp.notebook_id == "fadena-so"
        for c in resp.items:
            assert c.notebook_id == "fadena-so"


def test_adversarial_hybrid_curricular_isolation_attack(
    populated_hybrid_environment,
):
    _, _, _, _, _, hybrid = populated_hybrid_environment

    # Query in Operating Systems asking explicitly about Programming in C
    cross_query = RetrievalRequest(
        query="árbol binario de búsqueda y recorrido inorden recursivo",
        notebook_id="fadena-so",
        top_k=10,
        strategy=RetrievalStrategy.HYBRID,
    )
    resp = hybrid.retrieve(cross_query)

    # Hard Invariant: 0 candidates from fadena-prog can leak
    for c in resp.items:
        assert c.notebook_id == "fadena-so"
        assert not c.chunk_id.startswith("prog:")
        assert c.source_id == "src-so-silberschatz"


def test_adversarial_hybrid_3way_oracle_benchmark(
    populated_hybrid_environment,
):
    """Verify 3-way evaluation on Oracle with 0 leakage across strategies."""
    store, _, _, lex, dense, hybrid = populated_hybrid_environment

    oracle_path = Path("data/fixtures/reference_oracle.json")
    with open(oracle_path, "r", encoding="utf-8") as f:
        oracle_data = json.load(f)

    dataset = OracleDataset.model_validate(oracle_data)
    evaluator = OracleEvaluator(store)

    lex_rep = evaluator.evaluate(
        lex, dataset, strategy=RetrievalStrategy.LEXICAL
    )
    dense_rep = evaluator.evaluate(
        dense, dataset, strategy=RetrievalStrategy.DENSE
    )
    hybrid_rep = evaluator.evaluate(
        hybrid, dataset, strategy=RetrievalStrategy.HYBRID
    )

    assert lex_rep.total_queries == 6
    assert dense_rep.total_queries == 6
    assert hybrid_rep.total_queries == 6

    # Zero leakage hard gate on all 3 strategies
    assert lex_rep.global_metrics.leakage_rate == 0.0
    assert dense_rep.global_metrics.leakage_rate == 0.0
    assert hybrid_rep.global_metrics.leakage_rate == 0.0

    # Latencies recorded
    assert hybrid_rep.global_metrics.p50_retrieval_ms > 0.0
    assert hybrid_rep.total_evaluator_ms > 0.0
