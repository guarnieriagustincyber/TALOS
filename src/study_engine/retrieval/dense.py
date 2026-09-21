"""Dense semantic retriever using vector embeddings and cosine similarity."""

import math
import time
from typing import List, Optional, Set, Tuple

from study_engine.contracts.catalog import NotebookNotFoundError
from study_engine.contracts.retrieval import (
    RetrievalDiagnostics,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalStrategy,
    ScoredCandidate,
)
from study_engine.retrieval.embedding import (
    EmbeddingDimensionMismatchError,
    EmbeddingProvider,
)
from study_engine.retrieval.vector_store import (
    VectorRecord,
    VectorStore,
)
from study_engine.storage.knowledge_store import KnowledgeStore


class DenseRetrievalError(RuntimeError):
    """Raised when dense retrieval encounters an integrity violation."""
    pass


class DenseRetriever:
    """Dense retriever computing cosine similarity over vector stores."""

    def __init__(
        self,
        store: KnowledgeStore,
        vector_store: VectorStore,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        if not isinstance(store, KnowledgeStore):
            msg = f"Expected KnowledgeStore, got {type(store).__name__}."
            raise TypeError(msg)
        if not isinstance(vector_store, VectorStore):
            msg = f"Expected VectorStore, got {type(vector_store).__name__}."
            raise TypeError(msg)
        if not isinstance(embedding_provider, EmbeddingProvider):
            msg = (
                f"Expected EmbeddingProvider, got "
                f"{type(embedding_provider).__name__}."
            )
            raise TypeError(msg)

        self.store = store
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        """Execute dense retrieval scoped strictly to requested notebook."""
        if not isinstance(request, RetrievalRequest):
            msg = f"Expected RetrievalRequest, got {type(request).__name__}."
            raise TypeError(msg)

        t_total_start = time.perf_counter()

        # Check notebook existence in store
        if not self.store.contains_notebook(request.notebook_id):
            raise NotebookNotFoundError(request.notebook_id)

        # 1. T_query_embedding
        t_emb_start = time.perf_counter()
        query_vector = self.embedding_provider.embed_query(request.query)
        t_query_embedding_ms = (time.perf_counter() - t_emb_start) * 1000.0

        if len(query_vector) != self.embedding_provider.dimensions:
            raise EmbeddingDimensionMismatchError(
                f"Query vector dimension {len(query_vector)} does not match "
                f"expected {self.embedding_provider.dimensions}."
            )

        # 2. T_vector_store_load (Layer 1 Isolation: SQLite query filtered)
        t_load_start = time.perf_counter()
        records = self.vector_store.get_by_notebook(
            notebook_id=request.notebook_id,
            provider_id=self.embedding_provider.provider_id,
            model_id=self.embedding_provider.model_id,
        )
        t_vector_load_ms = (time.perf_counter() - t_load_start) * 1000.0

        # If notebook has no vectors, return empty response immediately
        if not records:
            t_total_ms = (time.perf_counter() - t_total_start) * 1000.0
            diagnostics = RetrievalDiagnostics(
                dense_candidates_count=0,
                unique_candidates_count=0,
                latencies_ms={
                    "retrieval_ms": t_total_ms,
                    "query_embedding_ms": t_query_embedding_ms,
                    "vector_load_ms": t_vector_load_ms,
                    "similarity_ms": 0.0,
                    "top_k_ms": 0.0,
                    "hydration_ms": 0.0,
                },
            )
            return RetrievalResponse(
                query=request.query,
                notebook_id=request.notebook_id,
                strategy_used=RetrievalStrategy.DENSE,
                items=[],
                diagnostics=diagnostics,
            )

        # 3. T_similarity: Pure cosine similarity computation
        t_sim_start = time.perf_counter()
        scored_records: List[Tuple[float, VectorRecord]] = []
        q_norm = math.sqrt(sum(x * x for x in query_vector))

        for rec in records:
            # Dimension integrity check
            if len(rec.vector) != len(query_vector):
                raise EmbeddingDimensionMismatchError(
                    f"Stored vector for chunk '{rec.chunk_id}' has dimension "
                    f"{len(rec.vector)}, expected {len(query_vector)}."
                )

            dot = sum(a * b for a, b in zip(query_vector, rec.vector))
            d_norm = math.sqrt(sum(y * y for y in rec.vector))

            if q_norm > 0.0 and d_norm > 0.0:
                sim = dot / (q_norm * d_norm)
            else:
                sim = 0.0

            # Cosine similarity must remain in [-1.0, 1.0] without scaling
            sim = max(-1.0, min(1.0, sim))
            scored_records.append((sim, rec))

        t_similarity_ms = (time.perf_counter() - t_sim_start) * 1000.0

        # 4. T_top_k: Deterministic sort by score DESC, chunk_id ASC
        t_topk_start = time.perf_counter()
        scored_records.sort(key=lambda x: (-x[0], x[1].chunk_id))

        # Apply optional source_id or document_id filters
        allowed_sources: Optional[Set[str]] = (
            set(request.source_ids) if request.source_ids else None
        )
        allowed_docs: Optional[Set[str]] = (
            set(request.document_ids) if request.document_ids else None
        )

        filtered_scored: List[Tuple[float, VectorRecord]] = []
        for sim, rec in scored_records:
            if allowed_sources and rec.source_id not in allowed_sources:
                continue
            filtered_scored.append((sim, rec))

        top_candidates = filtered_scored[: request.top_k]
        t_topk_ms = (time.perf_counter() - t_topk_start) * 1000.0

        # 5. T_hydration & Multi-layer Isolation Checks
        t_hyd_start = time.perf_counter()
        items: List[ScoredCandidate] = []

        linked_source_ids = {
            s.source_id
            for s in self.store.list_notebook_sources(request.notebook_id)
        }

        for sim_score, rec in filtered_scored:
            if len(items) >= request.top_k:
                break

            # Layer 2 Isolation Check: record metadata matches notebook
            if rec.notebook_id != request.notebook_id:
                raise DenseRetrievalError(
                    f"Curricular isolation violated: VectorRecord "
                    f"'{rec.chunk_id}' has notebook_id='{rec.notebook_id}' "
                    f"!= '{request.notebook_id}'."
                )

            # Relational check: chunk exists in KnowledgeStore
            if not self.store.chunks.contains(rec.chunk_id):
                raise DenseRetrievalError(
                    f"VectorRecord references non-existent chunk "
                    f"'{rec.chunk_id}'."
                )

            chunk = self.store.get_chunk(rec.chunk_id)
            if chunk.source_id not in linked_source_ids:
                raise DenseRetrievalError(
                    f"Curricular isolation violated: Chunk '{rec.chunk_id}' "
                    f"belongs to source '{chunk.source_id}' not linked to "
                    f"'{request.notebook_id}'."
                )

            if allowed_docs and chunk.document_id not in allowed_docs:
                continue

            items.append(
                ScoredCandidate(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    source_id=chunk.source_id,
                    notebook_id=request.notebook_id,
                    rank=len(items) + 1,
                    score=sim_score,
                    dense_score=sim_score,
                    lexical_score=None,
                    retrieval_method="dense",
                    content=chunk.content,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    pos_index=chunk.index,
                    metadata={
                        "provider_id": rec.provider_id,
                        "model_id": rec.model_id,
                    },
                )
            )

        t_hydration_ms = (time.perf_counter() - t_hyd_start) * 1000.0
        t_total_ms = (time.perf_counter() - t_total_start) * 1000.0

        diagnostics = RetrievalDiagnostics(
            dense_candidates_count=len(records),
            unique_candidates_count=len(items),
            latencies_ms={
                "retrieval_ms": t_total_ms,
                "query_embedding_ms": t_query_embedding_ms,
                "vector_load_ms": t_vector_load_ms,
                "similarity_ms": t_similarity_ms,
                "top_k_ms": t_topk_ms,
                "hydration_ms": t_hydration_ms,
            },
        )

        return RetrievalResponse(
            query=request.query,
            notebook_id=request.notebook_id,
            strategy_used=RetrievalStrategy.DENSE,
            items=items,
            diagnostics=diagnostics,
        )
