"""Retrieval Fabric Lite: Adaptive Multi-Stage Retrieval & Reranking Orchestrator (Fase 7 / F5, F6).

Integrates:
- QueryRewriter (single chokepoint)
- AdaptiveRetrievalRouter (F1, F7)
- First-stage Candidate Pooling (Lexical / Dense / TwoStage)
- Universal Presentation Filtering (Anti-leakage)
- Second-stage Reranking (Jina API with local fallback, F2, F3)
- Rotating structured JSON audit logging (F5)
"""

from datetime import datetime, timezone
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Sequence, Union

from study_engine.contracts.retrieval import (
    RetrievalRequest,
    RetrievalStrategy,
    ScoredCandidate,
)
from study_engine.contracts.search import SearchResult
from study_engine.retrieval.adaptive_router import AdaptiveRetrievalRouter, RouteDecision
from study_engine.retrieval.presentation_filter import filter_presentation
from study_engine.retrieval.query_rewriter import QueryRewriter
from study_engine.retrieval.reranker import BaseReranker, JinaReranker

logger = logging.getLogger(__name__)


def get_retrieval_trace_logger() -> logging.Logger:
    """Configures and returns a dedicated logger with RotatingFileHandler for retrieval traces (F5)."""
    trace_logger = logging.getLogger("study_engine.retrieval.fabric")
    if not any(isinstance(h, RotatingFileHandler) for h in trace_logger.handlers):
        try:
            logs_dir = Path("logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(
                filename=str(logs_dir / "retrieval_trace.json"),
                maxBytes=10_485_760,  # 10 MB
                backupCount=5,  # 5 historical files
                encoding="utf-8",
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            trace_logger.addHandler(handler)
            trace_logger.setLevel(logging.INFO)
            trace_logger.propagate = False
        except Exception as err:
            logger.debug("Could not configure RotatingFileHandler for retrieval trace: %s", err)
    return trace_logger


class RetrievalFabricLite:
    """Unified facade orchestrating adaptive routing, candidate pooling, anti-leakage, and reranking (F6)."""

    def __init__(
        self,
        store: Optional[Any] = None,
        retriever: Optional[Any] = None,
        router: Optional[AdaptiveRetrievalRouter] = None,
        reranker: Optional[BaseReranker] = None,
        query_rewriter: Optional[QueryRewriter] = None,
        content_registry: Optional[Any] = None,
    ) -> None:
        self.store = store
        self.retriever = retriever
        self.router = router or AdaptiveRetrievalRouter()
        self.reranker = reranker or JinaReranker()
        self.query_rewriter = query_rewriter or QueryRewriter()
        self.content_registry = content_registry or getattr(store, "content_registry", None)
        self.trace_logger = get_retrieval_trace_logger()

    def retrieve(
        self,
        query: str,
        notebook_id: str,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
        source_ids: Optional[List[str]] = None,
    ) -> List[ScoredCandidate]:
        """Execute multi-stage retrieval adhering strictly to F6 pipeline order:
        1. rewritten_query = self.query_rewriter.rewrite(query)
        2. route_decision = self.router.route(rewritten_query)
        3. candidates = self._fetch_candidate_pool(...)
        4. candidates = filter_presentation(...)
        5. if route_decision.enable_rerank: candidates = self.reranker.rerank(...)
        6. return candidates[:top_k]
        """
        t_start = time.perf_counter()

        # 1. Query re-writing (chokepoint único)
        rewritten_query = self.query_rewriter.rewrite(query) if self.query_rewriter else query

        # 2. Adaptive routing
        route_decision = self.router.route(rewritten_query)

        # 3. Candidate pool fetch
        candidates = self._fetch_candidate_pool(
            query=rewritten_query,
            notebook_id=notebook_id,
            decision=route_decision,
            document_ids=document_ids,
            source_ids=source_ids,
        )

        # 4. Anti-leakage presentation filter (preservado universalmente)
        registry = self.content_registry or getattr(self.store, "content_registry", None)
        if registry and candidates:
            filtered, _ = filter_presentation(candidates, registry)
            candidates = filtered

        # 5. Second-stage reranking
        reranker_used = "none"
        if route_decision.enable_rerank and candidates:
            candidates = self.reranker.rerank(rewritten_query, candidates, top_k=top_k)
            reranker_used = (
                candidates[0].metadata.get("reranker", "reranked")
                if candidates and hasattr(candidates[0], "metadata")
                else "reranked"
            )
        else:
            candidates = candidates[:top_k]

        # Re-assign 1-indexed deterministic rank
        final_items: List[ScoredCandidate] = []
        for idx, item in enumerate(candidates[:top_k], start=1):
            if isinstance(item, ScoredCandidate):
                final_items.append(item.model_copy(update={"rank": idx}))
            else:
                final_items.append(item)

        elapsed_ms = (time.perf_counter() - t_start) * 1000.0

        # 6. Structured JSON trace log (F5)
        try:
            trace_payload = {
                "event": "RETRIEVAL_FABRIC_TRACE",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "query": query,
                "rewritten_query": rewritten_query,
                "strategy": route_decision.strategy.value,
                "pool_depth": route_decision.pool_depth,
                "pool_size_fetched": len(candidates),
                "top_k_returned": len(final_items),
                "reranker_used": reranker_used,
                "latency_ms": round(elapsed_ms, 2),
            }
            self.trace_logger.info(json.dumps(trace_payload))
        except Exception as log_err:
            logger.debug("Error writing retrieval trace: %s", log_err)

        return final_items

    def _fetch_candidate_pool(
        self,
        query: str,
        notebook_id: str,
        decision: RouteDecision,
        document_ids: Optional[List[str]] = None,
        source_ids: Optional[List[str]] = None,
    ) -> List[ScoredCandidate]:
        """Fetch candidates from retriever or store according to route decision pool depth."""
        # 1. Delegar a BaseRetriever si está provisto
        if self.retriever is not None and hasattr(self.retriever, "retrieve"):
            try:
                strat = (
                    RetrievalStrategy.LEXICAL
                    if decision.strategy.value == "EXACT_LEXICAL"
                    else RetrievalStrategy.HYBRID
                )
                req = RetrievalRequest(
                    query=query,
                    notebook_id=notebook_id,
                    top_k=decision.pool_depth,
                    document_ids=document_ids,
                    source_ids=source_ids,
                    strategy=strat,
                )
                resp = self.retriever.retrieve(req)
                return list(resp.items)
            except Exception as ret_err:
                logger.debug("Fabric retriever search fallback: %s", ret_err)

        # 2. Delegar a KnowledgeStore.search_hybrid o search
        if self.store is not None:
            results: List[Any] = []
            if hasattr(self.store, "search_hybrid"):
                try:
                    results = self.store.search_hybrid(
                        query=query,
                        notebook_id=notebook_id,
                        limit=decision.pool_depth,
                    )
                except Exception as hybrid_err:
                    logger.debug("Fabric store search_hybrid fallback: %s", hybrid_err)
                    results = []

            if not results and hasattr(self.store, "search"):
                try:
                    results = self.store.search(
                        query=query,
                        notebook_id=notebook_id,
                        limit=decision.pool_depth,
                    )
                except Exception as search_err:
                    logger.debug("Fabric store search fallback: %s", search_err)
                    results = []

            # Filtrar por document_ids / source_ids si fueron especificados
            if source_ids:
                s_set = set(source_ids)
                results = [r for r in results if getattr(r, "source_id", "") in s_set]
            if document_ids:
                d_set = set(document_ids)
                results = [r for r in results if getattr(r, "document_id", "") in d_set]

            # Convertir SearchResult a ScoredCandidate
            candidates: List[ScoredCandidate] = []
            for rank, r in enumerate(results, start=1):
                if isinstance(r, ScoredCandidate):
                    candidates.append(r)
                elif isinstance(r, SearchResult):
                    candidates.append(
                        ScoredCandidate(
                            chunk_id=r.chunk_id,
                            document_id=r.document_id,
                            source_id=r.source_id,
                            notebook_id=notebook_id,
                            rank=rank,
                            score=round(float(r.score), 4),
                            content=r.content,
                            lexical_score=round(float(r.score), 4),
                            dense_score=None,
                            retrieval_method="fabric_hybrid",
                            page_start=r.page_start,
                            page_end=r.page_end,
                            pos_index=r.index,
                            metadata={},
                        )
                    )
            return candidates

        return []
