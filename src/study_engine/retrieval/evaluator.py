"""Oracle benchmark evaluation runner and metrics calculator for S3."""

import time
from typing import Dict, List, Set
from pydantic import Field

from study_engine.contracts.base import BaseContract
from study_engine.contracts.oracle import (
    BenchmarkCategory,
    OracleDataset,
    OracleQuery,
    RelevanceGrade,
)
from study_engine.contracts.retrieval import (
    RetrievalRequest,
    RetrievalStrategy,
)
from study_engine.retrieval.base import BaseRetriever
from study_engine.retrieval.oracle import validate_oracle_dataset
from study_engine.storage.knowledge_store import KnowledgeStore


class QueryEvaluationResult(BaseContract):
    """Detailed evaluation telemetry for a single benchmark query."""

    query_id: str = Field(..., min_length=1)
    category: BenchmarkCategory
    direct_recall_at_1: float = Field(ge=0.0, le=1.0)
    direct_recall_at_5: float = Field(ge=0.0, le=1.0)
    overall_recall_at_1: float = Field(ge=0.0, le=1.0)
    overall_recall_at_5: float = Field(ge=0.0, le=1.0)
    reciprocal_rank: float = Field(ge=0.0, le=1.0)
    is_leakage_query: bool
    illegal_candidates_count: int = Field(ge=0)
    retrieval_latency_ms: float = Field(ge=0.0)
    evaluation_latency_ms: float = Field(ge=0.0)


class CategoryMetrics(BaseContract):
    """Aggregated statistical metrics for an evaluation cohort or category."""

    query_count: int = Field(ge=0)
    mean_direct_recall_at_1: float = Field(ge=0.0, le=1.0)
    mean_direct_recall_at_5: float = Field(ge=0.0, le=1.0)
    mean_overall_recall_at_1: float = Field(ge=0.0, le=1.0)
    mean_overall_recall_at_5: float = Field(ge=0.0, le=1.0)
    mrr: float = Field(ge=0.0, le=1.0)
    leakage_queries_count: int = Field(ge=0)
    queries_with_leakage_count: int = Field(ge=0)
    leakage_rate: float = Field(ge=0.0, le=1.0)
    total_illegal_candidates_count: int = Field(ge=0)
    p50_retrieval_ms: float = Field(ge=0.0)
    p95_retrieval_ms: float = Field(ge=0.0)


class EvaluationReport(BaseContract):
    """Comprehensive benchmark execution report."""

    oracle_version: str = Field(..., min_length=1)
    total_queries: int = Field(ge=0)
    global_metrics: CategoryMetrics
    by_category: Dict[str, CategoryMetrics] = Field(default_factory=dict)
    query_results: List[QueryEvaluationResult] = Field(default_factory=list)
    total_evaluator_ms: float = Field(ge=0.0)


class OracleEvaluator:
    """Benchmark runner executing an Oracle dataset against a BaseRetriever."""

    def __init__(self, store: KnowledgeStore) -> None:
        """Initialize evaluator with authoritative knowledge store."""
        if not isinstance(store, KnowledgeStore):
            msg = f"Expected KnowledgeStore, got {type(store).__name__}."
            raise TypeError(msg)
        self.store = store

    def evaluate(
        self,
        retriever: BaseRetriever,
        dataset: OracleDataset,
        strategy: RetrievalStrategy = RetrievalStrategy.LEXICAL,
    ) -> EvaluationReport:
        """Run benchmark evaluation and compute relevance/leakage metrics."""
        if not isinstance(retriever, BaseRetriever):
            msg = f"Expected BaseRetriever, got {type(retriever).__name__}."
            raise TypeError(msg)
        if not isinstance(dataset, OracleDataset):
            msg = f"Expected OracleDataset, got {type(dataset).__name__}."
            raise TypeError(msg)

        # First validate relational integrity against store
        validate_oracle_dataset(dataset, store=self.store)

        evaluator_start = time.perf_counter()
        query_results: List[QueryEvaluationResult] = []

        for q in dataset.queries:
            result = self._evaluate_single_query(retriever, q, strategy)
            query_results.append(result)

        total_evaluator_ms = (
            time.perf_counter() - evaluator_start
        ) * 1000.0

        # Compute per-category and global metrics
        global_metrics = self._aggregate_metrics(query_results)
        by_category: Dict[str, CategoryMetrics] = {}

        categories = {q.category for q in dataset.queries}
        for cat in categories:
            cat_results = [r for r in query_results if r.category == cat]
            by_category[cat.value] = self._aggregate_metrics(cat_results)

        return EvaluationReport(
            oracle_version=dataset.version,
            total_queries=len(dataset.queries),
            global_metrics=global_metrics,
            by_category=by_category,
            query_results=query_results,
            total_evaluator_ms=total_evaluator_ms,
        )

    def _evaluate_single_query(
        self,
        retriever: BaseRetriever,
        oracle_query: OracleQuery,
        strategy: RetrievalStrategy,
    ) -> QueryEvaluationResult:
        """Execute and score an individual query."""
        eval_t0 = time.perf_counter()

        req = RetrievalRequest(
            query=oracle_query.query,
            notebook_id=oracle_query.notebook_id,
            top_k=5,
            strategy=strategy,
        )

        response = retriever.retrieve(req)
        eval_ms = (time.perf_counter() - eval_t0) * 1000.0
        retrieval_ms = response.diagnostics.latencies_ms.get(
            "retrieval_ms", 0.0
        )

        cat = oracle_query.category
        is_leakage = cat == BenchmarkCategory.CURRICULAR_LEAKAGE

        # Check for illegal cross-curricular leaks (Curricular Isolation)
        illegal_chunks = []
        if getattr(self, "store", None) is not None:
            linked_sources = {
                s.source_id
                for s in self.store.list_notebook_sources(
                    oracle_query.notebook_id
                )
            }
            for c in response.items:
                if c.notebook_id != oracle_query.notebook_id:
                    illegal_chunks.append(c)
                elif not self.store.chunks.contains(c.chunk_id):
                    illegal_chunks.append(c)
                else:
                    chunk = self.store.get_chunk(c.chunk_id)
                    if chunk.source_id not in linked_sources:
                        illegal_chunks.append(c)
        else:
            illegal_chunks = [
                c
                for c in response.items
                if c.notebook_id != oracle_query.notebook_id
            ]

        illegal_count = len(illegal_chunks)

        if is_leakage:
            return QueryEvaluationResult(
                query_id=oracle_query.id,
                category=oracle_query.category,
                direct_recall_at_1=0.0,
                direct_recall_at_5=0.0,
                overall_recall_at_1=0.0,
                overall_recall_at_5=0.0,
                reciprocal_rank=0.0,
                is_leakage_query=True,
                illegal_candidates_count=illegal_count,
                retrieval_latency_ms=retrieval_ms,
                evaluation_latency_ms=eval_ms,
            )

        # Standard relevant queries

        grade_dir = RelevanceGrade.DIRECT
        direct_expected: Set[str] = {
            r.chunk_id for r in oracle_query.relevant if r.grade == grade_dir
        }
        all_expected: Set[str] = {r.chunk_id for r in oracle_query.relevant}

        returned_chunks = [c.chunk_id for c in response.items]
        top_1 = returned_chunks[:1]
        top_5 = returned_chunks[:5]

        # Recall calculations
        direct_rec_1 = (
            1.0 if any(c in direct_expected for c in top_1) else 0.0
        )
        direct_rec_5 = (
            1.0 if any(c in direct_expected for c in top_5) else 0.0
        )
        overall_rec_1 = (
            1.0 if any(c in all_expected for c in top_1) else 0.0
        )
        overall_rec_5 = (
            1.0 if any(c in all_expected for c in top_5) else 0.0
        )

        # MRR calculation (1 / rank of first relevant chunk found)
        reciprocal_rank = 0.0
        for rank_idx, c_id in enumerate(returned_chunks, start=1):
            if c_id in all_expected:
                reciprocal_rank = 1.0 / rank_idx
                break

        return QueryEvaluationResult(
            query_id=oracle_query.id,
            category=oracle_query.category,
            direct_recall_at_1=direct_rec_1,
            direct_recall_at_5=direct_rec_5,
            overall_recall_at_1=overall_rec_1,
            overall_recall_at_5=overall_rec_5,
            reciprocal_rank=reciprocal_rank,
            is_leakage_query=False,
            illegal_candidates_count=0,
            retrieval_latency_ms=retrieval_ms,
            evaluation_latency_ms=eval_ms,
        )

    def _aggregate_metrics(
        self, results: List[QueryEvaluationResult]
    ) -> CategoryMetrics:
        """Compute aggregated metrics and percentiles for a results cohort."""
        if not results:
            return CategoryMetrics(
                query_count=0,
                mean_direct_recall_at_1=0.0,
                mean_direct_recall_at_5=0.0,
                mean_overall_recall_at_1=0.0,
                mean_overall_recall_at_5=0.0,
                mrr=0.0,
                leakage_queries_count=0,
                queries_with_leakage_count=0,
                leakage_rate=0.0,
                total_illegal_candidates_count=0,
                p50_retrieval_ms=0.0,
                p95_retrieval_ms=0.0,
            )

        n = len(results)
        leakage_results = [r for r in results if r.is_leakage_query]
        standard_results = [r for r in results if not r.is_leakage_query]

        n_std = len(standard_results)
        s_dr1 = sum(r.direct_recall_at_1 for r in standard_results)
        s_dr5 = sum(r.direct_recall_at_5 for r in standard_results)
        s_or1 = sum(r.overall_recall_at_1 for r in standard_results)
        s_or5 = sum(r.overall_recall_at_5 for r in standard_results)
        s_mrr = sum(r.reciprocal_rank for r in standard_results)

        mean_dr1 = s_dr1 / n_std if n_std > 0 else 0.0
        mean_dr5 = s_dr5 / n_std if n_std > 0 else 0.0
        mean_or1 = s_or1 / n_std if n_std > 0 else 0.0
        mean_or5 = s_or5 / n_std if n_std > 0 else 0.0
        mean_mrr = s_mrr / n_std if n_std > 0 else 0.0

        n_leak = len(leakage_results)
        leaked_q = sum(
            1 for r in leakage_results if r.illegal_candidates_count > 0
        )
        total_illegal = sum(
            r.illegal_candidates_count for r in leakage_results
        )
        leakage_rate = (leaked_q / n_leak) if n_leak > 0 else 0.0

        # Latency percentiles
        latencies = sorted(r.retrieval_latency_ms for r in results)
        p50 = self._percentile(latencies, 50.0)
        p95 = self._percentile(latencies, 95.0)

        return CategoryMetrics(
            query_count=n,
            mean_direct_recall_at_1=mean_dr1,
            mean_direct_recall_at_5=mean_dr5,
            mean_overall_recall_at_1=mean_or1,
            mean_overall_recall_at_5=mean_or5,
            mrr=mean_mrr,
            leakage_queries_count=n_leak,
            queries_with_leakage_count=leaked_q,
            leakage_rate=leakage_rate,
            total_illegal_candidates_count=total_illegal,
            p50_retrieval_ms=p50,
            p95_retrieval_ms=p95,
        )

    @staticmethod
    def _percentile(sorted_vals: List[float], p: float) -> float:
        """Compute nearest rank percentile on a sorted list of numbers."""
        if not sorted_vals:
            return 0.0
        idx = int(round((p / 100.0) * (len(sorted_vals) - 1)))
        return sorted_vals[max(0, min(len(sorted_vals) - 1, idx))]
