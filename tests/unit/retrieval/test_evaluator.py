"""Unit tests for OracleEvaluator and evaluation metrics in S3.3."""

from pathlib import Path
import pytest

from study_engine.contracts.oracle import (
    BenchmarkCategory,
    OracleDataset,
    OracleQuery,
    RelevanceGrade,
    RelevantChunk,
)
from study_engine.contracts.retrieval import (
    RetrievalDiagnostics,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalStrategy,
    ScoredCandidate,
)
from study_engine.retrieval.evaluator import (
    CategoryMetrics,
    OracleEvaluator,
    QueryEvaluationResult,
)
from study_engine.storage.knowledge_store import KnowledgeStore


class DummyRetriever:
    """Mock retriever returning predetermined candidates for metric verification."""

    def __init__(self, returned_chunk_ids: list, notebook_id: str = None):
        self.returned_chunk_ids = returned_chunk_ids
        self.notebook_id = notebook_id

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        nb_id = self.notebook_id or request.notebook_id
        items = [
            ScoredCandidate(
                chunk_id=cid,
                document_id="doc1",
                source_id="src1",
                notebook_id=nb_id,
                rank=idx + 1,
                score=10.0 - idx,
                content="content",
                retrieval_method="dummy",
            )

            for idx, cid in enumerate(self.returned_chunk_ids[:request.top_k])
        ]
        return RetrievalResponse(
            query=request.query,
            notebook_id=request.notebook_id,
            strategy_used=request.strategy,
            items=items,
            diagnostics=RetrievalDiagnostics(latencies_ms={"retrieval_ms": 1.5}),
        )


def test_percentile_calculation():
    # Empty list
    assert OracleEvaluator._percentile([], 50.0) == 0.0

    # Single element
    assert OracleEvaluator._percentile([42.0], 95.0) == 42.0

    # Ordered list
    data = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert OracleEvaluator._percentile(data, 50.0) == 30.0
    assert OracleEvaluator._percentile(data, 0.0) == 10.0
    assert OracleEvaluator._percentile(data, 100.0) == 50.0


def test_aggregate_metrics_empty():
    evaluator = OracleEvaluator.__new__(OracleEvaluator)
    empty_res = evaluator._aggregate_metrics([])
    assert empty_res.query_count == 0
    assert empty_res.mean_direct_recall_at_1 == 0.0
    assert empty_res.mrr == 0.0
    assert empty_res.leakage_rate == 0.0


def test_single_query_metric_calculation():
    evaluator = OracleEvaluator.__new__(OracleEvaluator)
    q = OracleQuery(
        id="q1",
        notebook_id="nb-so",
        query="zombie",
        category=BenchmarkCategory.DEFINITION,
        relevant=[
            RelevantChunk(chunk_id="target_direct", grade=RelevanceGrade.DIRECT, rationale="Exact"),
            RelevantChunk(chunk_id="target_partial", grade=RelevanceGrade.PARTIAL, rationale="Context"),
        ],
        rationale="r",
    )

    # Case A: target_direct is rank 1
    retriever_top1 = DummyRetriever(["target_direct", "other1", "other2"])
    res1 = evaluator._evaluate_single_query(retriever_top1, q, RetrievalStrategy.LEXICAL)
    assert res1.direct_recall_at_1 == 1.0
    assert res1.direct_recall_at_5 == 1.0
    assert res1.overall_recall_at_1 == 1.0
    assert res1.reciprocal_rank == 1.0

    # Case B: target_partial is rank 1, target_direct is rank 3
    retriever_top3 = DummyRetriever(["target_partial", "other1", "target_direct"])
    res2 = evaluator._evaluate_single_query(retriever_top3, q, RetrievalStrategy.LEXICAL)
    assert res2.direct_recall_at_1 == 0.0  # target_direct not in top 1
    assert res2.direct_recall_at_5 == 1.0  # target_direct is in top 5
    assert res2.overall_recall_at_1 == 1.0  # target_partial is in top 1
    assert res2.reciprocal_rank == 1.0  # rank 1 was a relevant chunk

    # Case C: only target_partial is at rank 4 (no direct)
    retriever_partial = DummyRetriever(["other1", "other2", "other3", "target_partial"])
    res3 = evaluator._evaluate_single_query(retriever_partial, q, RetrievalStrategy.LEXICAL)
    assert res3.direct_recall_at_1 == 0.0
    assert res3.direct_recall_at_5 == 0.0
    assert res3.overall_recall_at_1 == 0.0
    assert res3.overall_recall_at_5 == 1.0
    assert res3.reciprocal_rank == 0.25  # 1 / 4


def test_leakage_query_evaluation(tmp_path: Path):
    from study_engine.contracts.catalog import SourceRecord
    from study_engine.contracts.chunk import Chunk
    from study_engine.contracts.document import Document
    from study_engine.contracts.ingestion import SourceManifest
    from study_engine.contracts.notebook import Notebook

    store = KnowledgeStore(tmp_path / "leak_eval.db")
    store.initialize()
    store.create_notebook(Notebook(id="nb-so", name="SO"))

    rec_so = SourceRecord(
        source_id="src-so",
        manifest=SourceManifest(
            source_id="src-so", filename="so.pdf", byte_size=10, sha256="a" * 64
        ),
    )
    docs = [Document(id="doc-so", source_id="src-so", title="SO", content="c")]
    chunks = [
        Chunk(
            id="c-so",
            document_id="doc-so",
            source_id="src-so",
            content="content",
            index=0,
        )
    ]
    store.store_ingestion_bundle(rec_so, docs, chunks, notebook_id="nb-so")

    evaluator = OracleEvaluator(store)
    q_leak = OracleQuery(
        id="q-leak",
        notebook_id="nb-so",
        query="árboles",
        category=BenchmarkCategory.CURRICULAR_LEAKAGE,
        relevant=[],
        rationale="Leakage test",
    )

    # Clean case: candidates belong to requested notebook and linked source
    retriever_clean = DummyRetriever(["c-so"])
    res_clean = evaluator._evaluate_single_query(
        retriever_clean, q_leak, RetrievalStrategy.LEXICAL
    )
    assert res_clean.is_leakage_query is True
    assert res_clean.illegal_candidates_count == 0

    # Leaking case: 2 candidates returned that are not linked to this notebook
    retriever_leaking = DummyRetriever(["unlinked_chunk1", "unlinked_chunk2"])
    res_leaking = evaluator._evaluate_single_query(
        retriever_leaking, q_leak, RetrievalStrategy.LEXICAL
    )
    assert res_leaking.is_leakage_query is True
    assert res_leaking.illegal_candidates_count == 2



def test_evaluator_catches_unvalidated_illegal_candidates_defense_in_depth(tmp_path: Path):
    from study_engine.contracts.catalog import SourceRecord
    from study_engine.contracts.chunk import Chunk
    from study_engine.contracts.document import Document
    from study_engine.contracts.ingestion import SourceManifest
    from study_engine.contracts.notebook import Notebook

    store = KnowledgeStore(tmp_path / "defense_eval.db")
    store.initialize()
    store.create_notebook(Notebook(id="nb-so", name="SO"))
    store.create_notebook(Notebook(id="nb-prog", name="Prog"))

    rec_so = SourceRecord(source_id="src-so", manifest=SourceManifest(source_id="src-so", filename="so.pdf", byte_size=1, sha256="a"*64))
    rec_prog = SourceRecord(source_id="src-prog", manifest=SourceManifest(source_id="src-prog", filename="prog.pdf", byte_size=1, sha256="b"*64))

    docs_so = [Document(id="doc-so", source_id="src-so", title="SO", content="c")]
    chunks_so = [Chunk(id="c-so", document_id="doc-so", source_id="src-so", content="c", index=0)]
    store.store_ingestion_bundle(rec_so, docs_so, chunks_so, notebook_id="nb-so")

    docs_prog = [Document(id="doc-prog", source_id="src-prog", title="Prog", content="c")]
    chunks_prog = [Chunk(id="c-prog", document_id="doc-prog", source_id="src-prog", content="c", index=0)]
    store.store_ingestion_bundle(rec_prog, docs_prog, chunks_prog, notebook_id="nb-prog")

    evaluator = OracleEvaluator(store)
    q_leak = OracleQuery(id="q1", notebook_id="nb-so", query="test", category=BenchmarkCategory.CURRICULAR_LEAKAGE, relevant=[], rationale="r")

    # Construct unvalidated response with candidate from another notebook to test defense in depth
    illegal_candidate_nb = ScoredCandidate(
        chunk_id="c-so", document_id="doc-so", source_id="src-so",
        notebook_id="nb-prog", rank=1, score=1.0, retrieval_method="dummy", content="c"
    )
    raw_resp_nb = RetrievalResponse.model_construct(
        query="test", notebook_id="nb-so", strategy_used=RetrievalStrategy.LEXICAL,
        items=[illegal_candidate_nb], diagnostics=RetrievalDiagnostics(latencies_ms={})
    )

    class FixedRetriever:
        def retrieve(self, req):
            return raw_resp_nb

    res_nb = evaluator._evaluate_single_query(FixedRetriever(), q_leak, RetrievalStrategy.LEXICAL)
    assert res_nb.illegal_candidates_count == 1

    # Construct unvalidated response with chunk from unlinked source
    illegal_candidate_src = ScoredCandidate(
        chunk_id="c-prog", document_id="doc-prog", source_id="src-prog",
        notebook_id="nb-so", rank=1, score=1.0, retrieval_method="dummy", content="c"
    )
    raw_resp_src = RetrievalResponse.model_construct(
        query="test", notebook_id="nb-so", strategy_used=RetrievalStrategy.LEXICAL,
        items=[illegal_candidate_src], diagnostics=RetrievalDiagnostics(latencies_ms={})
    )


    class FixedRetriever2:
        def retrieve(self, req):
            return raw_resp_src

    res_src = evaluator._evaluate_single_query(FixedRetriever2(), q_leak, RetrievalStrategy.LEXICAL)
    assert res_src.illegal_candidates_count == 1
