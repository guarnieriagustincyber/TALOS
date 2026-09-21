"""Adversarial and Reference Oracle execution tests for LexicalRetriever in S3.3."""

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
from study_engine.retrieval.evaluator import OracleEvaluator
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def populated_reference_store(tmp_path: Path) -> KnowledgeStore:
    """Populate KnowledgeStore with authentic reference corpus."""
    with open("data/fixtures/reference_corpus.json", "r", encoding="utf-8") as f:
        corpus = json.load(f)

    store = KnowledgeStore(tmp_path / "reference_lexical.db")
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
    return store


def test_adversarial_lexical_query_fuzzing(populated_reference_store: KnowledgeStore):
    """Stress test query inputs with complex C syntax, pointers, unbalanced quotes, and long strings."""
    retriever = LexicalRetriever(populated_reference_store)
    fuzz_queries = [
        "malloc() void* free()",
        "*ptr = (uintptr_t*) malloc(sizeof(*ptr));",
        "O(log n) vs O(1) vs O(n^2)",
        "\"unclosed double quote",
        "'unclosed single quote",
        "SELECT * FROM chunks WHERE 1=1;",
        "<script>alert('xss')</script>",
        "🔥 Memoria Virtual y Paginación ⚡",
        "a" * 2500,
    ]

    for q in fuzz_queries:
        req = RetrievalRequest(query=q, notebook_id="fadena-prog", top_k=5)
        resp = retriever.retrieve(req)
        assert resp.notebook_id == "fadena-prog"
        assert resp.strategy_used == RetrievalStrategy.LEXICAL
        # Invariant: Each returned candidate rank must equal idx + 1
        for idx, item in enumerate(resp.items):
            assert item.rank == idx + 1
            assert item.notebook_id == "fadena-prog"


def test_adversarial_lexical_curricular_isolation(populated_reference_store: KnowledgeStore):
    """Verify that a query for programming concepts in the OS notebook returns ZERO programming chunks."""
    retriever = LexicalRetriever(populated_reference_store)

    # Ask for binary search trees inside SO notebook
    req = RetrievalRequest(
        query="árbol binario de búsqueda inorden",
        notebook_id="fadena-so",
        top_k=5,
    )
    resp = retriever.retrieve(req)
    # Binary trees exist in fadena-prog, but NOT in fadena-so
    assert len(resp.items) == 0, f"Leaked candidates into fadena-so: {[c.chunk_id for c in resp.items]}"


def test_adversarial_oracle_evaluator_end_to_end_smoke_benchmark(populated_reference_store: KnowledgeStore):
    """Execute the full OracleEvaluator against the Reference Oracle ground truth."""
    retriever = LexicalRetriever(populated_reference_store)
    evaluator = OracleEvaluator(populated_reference_store)

    with open("data/fixtures/reference_oracle.json", "r", encoding="utf-8") as f:
        oracle_data = json.load(f)

    oracle_dataset = OracleDataset.model_validate(oracle_data)

    report = evaluator.evaluate(retriever, oracle_dataset, strategy=RetrievalStrategy.LEXICAL)

    assert report.total_queries == 6
    assert report.global_metrics.leakage_rate == 0.0
    assert report.global_metrics.total_illegal_candidates_count == 0

    # Ensure all 6 categories were evaluated
    expected_categories = {
        "CODE_SYMBOL",
        "DEFINITION",
        "PARAPHRASE",
        "DIACRITICS_VARIANTS",
        "AMBIGUOUS",
        "CURRICULAR_LEAKAGE",
    }
    assert set(report.by_category.keys()) == expected_categories

    # Verify CODE_SYMBOL performance on BM25
    code_metrics = report.by_category["CODE_SYMBOL"]
    assert code_metrics.mean_direct_recall_at_1 == 1.0

    # Verify CURRICULAR_LEAKAGE zero leakage
    leak_metrics = report.by_category["CURRICULAR_LEAKAGE"]
    assert leak_metrics.leakage_rate == 0.0
    assert leak_metrics.total_illegal_candidates_count == 0


def test_evaluator_type_rejections(populated_reference_store: KnowledgeStore):
    with pytest.raises(TypeError):
        OracleEvaluator("not-a-store")  # type: ignore

    evaluator = OracleEvaluator(populated_reference_store)
    with pytest.raises(TypeError):
        evaluator.evaluate("not-a-retriever", OracleDataset(version="1.0", queries=[]))  # type: ignore

    with pytest.raises(TypeError):
        evaluator.evaluate(LexicalRetriever(populated_reference_store), "not-a-dataset")  # type: ignore
