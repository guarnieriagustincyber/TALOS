"""Hybrid retrieval pipeline combining lexical and dense candidate fusion."""


import time
from typing import Any, List, Optional, Union

from study_engine.contracts.catalog import NotebookNotFoundError
from study_engine.contracts.retrieval import (
    RetrievalDiagnostics,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalStrategy,
    ScoredCandidate,
)
from study_engine.retrieval.base import BaseRetriever
from study_engine.retrieval.dense import DenseRetrievalError
from study_engine.retrieval.fusion import (
    FusionStrategy,
    ReciprocalRankFusion,
)
from study_engine.storage.knowledge_store import KnowledgeStore


class HybridRetriever:
    """Hybrid retriever combining lexical and dense retrievers via fusion."""

    def __init__(
        self,
        store: KnowledgeStore,
        lexical_retriever: BaseRetriever,
        dense_retriever: BaseRetriever,
        fusion_strategy: Optional[FusionStrategy] = None,
        candidate_pool_factor: int = 2,
    ) -> None:
        if not isinstance(store, KnowledgeStore):
            msg = f"Expected KnowledgeStore, got {type(store).__name__}."
            raise TypeError(msg)
        if not isinstance(lexical_retriever, BaseRetriever):
            msg = (
                f"Expected BaseRetriever for lexical, got "
                f"{type(lexical_retriever).__name__}."
            )
            raise TypeError(msg)
        if not isinstance(dense_retriever, BaseRetriever):
            msg = (
                f"Expected BaseRetriever for dense, got "
                f"{type(dense_retriever).__name__}."
            )
            raise TypeError(msg)

        if fusion_strategy is not None and not isinstance(
            fusion_strategy, FusionStrategy
        ):
            msg = (
                f"Expected FusionStrategy, got "
                f"{type(fusion_strategy).__name__}."
            )
            raise TypeError(msg)

        if candidate_pool_factor < 1:
            raise ValueError("candidate_pool_factor must be >= 1.")

        self.store = store
        self.lexical_retriever = lexical_retriever
        self.dense_retriever = dense_retriever
        self.fusion_strategy = fusion_strategy or ReciprocalRankFusion(k=60)
        self.candidate_pool_factor = candidate_pool_factor

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        """Execute hybrid retrieval scoped strictly to requested notebook."""
        if not isinstance(request, RetrievalRequest):
            msg = f"Expected RetrievalRequest, got {type(request).__name__}."
            raise TypeError(msg)

        t_total_start = time.perf_counter()

        # Check notebook existence in authoritative store
        if not self.store.contains_notebook(request.notebook_id):
            raise NotebookNotFoundError(request.notebook_id)

        # Determine candidate pool depth to ensure sufficient recall for fusion
        k_pool = max(request.top_k * self.candidate_pool_factor, 20)

        # 1. Execute Lexical Retrieval
        lex_req = request.model_copy(
            update={"top_k": k_pool, "strategy": RetrievalStrategy.LEXICAL}
        )
        t_lex_start = time.perf_counter()
        lex_resp = self.lexical_retriever.retrieve(lex_req)
        t_lexical_ms = (time.perf_counter() - t_lex_start) * 1000.0

        # 2. Execute Dense Retrieval
        dense_req = request.model_copy(
            update={"top_k": k_pool, "strategy": RetrievalStrategy.DENSE}
        )
        t_dense_start = time.perf_counter()
        dense_resp = self.dense_retriever.retrieve(dense_req)
        t_dense_ms = (time.perf_counter() - t_dense_start) * 1000.0

        # 3. Execute Fusion Strategy
        t_fusion_start = time.perf_counter()
        fused_candidates = self.fusion_strategy.fuse(
            lexical_items=lex_resp.items,
            dense_items=dense_resp.items,
            top_k=request.top_k,
        )
        t_fusion_ms = (time.perf_counter() - t_fusion_start) * 1000.0

        # 4. Multi-layer Isolation and Relational Verification
        linked_sources = {
            s.source_id
            for s in self.store.list_notebook_sources(request.notebook_id)
        }

        items: List[ScoredCandidate] = []
        for idx, fc in enumerate(fused_candidates):
            # Layer 2 Check: notebook_id must strictly match
            if fc.notebook_id != request.notebook_id:
                raise DenseRetrievalError(
                    f"Curricular isolation violated: Fused candidate "
                    f"'{fc.chunk_id}' has notebook_id='{fc.notebook_id}' "
                    f"!= '{request.notebook_id}'."
                )

            # Relational check: chunk exists in KnowledgeStore and is linked
            if not self.store.chunks.contains(fc.chunk_id):
                raise DenseRetrievalError(
                    f"Fused candidate references non-existent chunk "
                    f"'{fc.chunk_id}'."
                )

            chunk = self.store.get_chunk(fc.chunk_id)
            if chunk.source_id not in linked_sources:
                raise DenseRetrievalError(
                    f"Curricular isolation violated: Chunk '{fc.chunk_id}' "
                    f"belongs to source '{chunk.source_id}' not linked to "
                    f"'{request.notebook_id}'."
                )

            # Metadata with complete audit trail for S4
            provenance_meta = dict(fc.metadata)
            provenance_meta.update(
                {
                    "lexical_rank": fc.lexical_rank,
                    "dense_rank": fc.dense_rank,
                    "in_lexical": fc.lexical_rank is not None,
                    "in_dense": fc.dense_rank is not None,
                    "fused_score": fc.score,
                }
            )

            items.append(
                ScoredCandidate(
                    chunk_id=fc.chunk_id,
                    document_id=fc.document_id,
                    source_id=fc.source_id,
                    notebook_id=request.notebook_id,
                    rank=idx + 1,
                    score=fc.score,
                    lexical_score=fc.lexical_score,
                    dense_score=fc.dense_score,
                    retrieval_method="hybrid_rrf",
                    content=fc.content,
                    page_start=fc.page_start,
                    page_end=fc.page_end,
                    pos_index=fc.pos_index,
                    metadata=provenance_meta,
                )
            )

        t_total_ms = (time.perf_counter() - t_total_start) * 1000.0

        unique_cids = {c.chunk_id for c in lex_resp.items} | {
            c.chunk_id for c in dense_resp.items
        }

        diagnostics = RetrievalDiagnostics(
            lexical_candidates_count=len(lex_resp.items),
            dense_candidates_count=len(dense_resp.items),
            unique_candidates_count=len(unique_cids),
            latencies_ms={
                "retrieval_ms": t_total_ms,
                "lexical_ms": t_lexical_ms,
                "dense_ms": t_dense_ms,
                "fusion_ms": t_fusion_ms,
            },
        )

        return RetrievalResponse(
            query=request.query,
            notebook_id=request.notebook_id,
            strategy_used=RetrievalStrategy.HYBRID,
            items=items,
            diagnostics=diagnostics,
        )

    def retrieve_evidence(
        self,
        query: str,
        notebook_id_or_node_id: Optional[str] = None,
        registry_or_top_k: Union[int, Any, None] = None,
        top_k: int = 5,
        strategy: Optional[RetrievalStrategy] = None,
        *,
        node_id: Optional[str] = None,
        registry: Optional[Any] = None,
        notebook_id: Optional[str] = None,
        matrix_id: Optional[str] = None,
    ) -> List[ScoredCandidate]:
        """Retrieve authoritative evidence candidates with Epistemic Gatekeeper isolation."""
        effective_node_id = node_id
        effective_registry = registry
        effective_notebook_id = notebook_id
        effective_top_k = top_k

        if registry_or_top_k is not None:
            if isinstance(registry_or_top_k, int):
                effective_top_k = registry_or_top_k
                if notebook_id_or_node_id is not None and effective_notebook_id is None:
                    effective_notebook_id = notebook_id_or_node_id
            else:
                effective_registry = registry_or_top_k
                if notebook_id_or_node_id is not None and effective_node_id is None:
                    effective_node_id = notebook_id_or_node_id
        elif notebook_id_or_node_id is not None:
            if effective_node_id is None and effective_registry is not None:
                effective_node_id = notebook_id_or_node_id
            elif effective_notebook_id is None:
                effective_notebook_id = notebook_id_or_node_id

        if not effective_notebook_id:
            notebooks = self.store.list_notebooks()
            effective_notebook_id = notebooks[0].id if notebooks else "NB-CYBERSECURITY-V1"

        if effective_node_id is not None and effective_registry is not None:
            try:
                allowed_scopes = effective_registry.get_scoped_sources_for_node(
                    node_id=effective_node_id,
                    matrix_id_or_path=matrix_id or "cybersecurity_v1_alignment.json",
                )
            except Exception:
                return []

            if not allowed_scopes:
                return []

            allowed_doc_ids = list({scope.document_id for scope in allowed_scopes})
            k_pool = max(effective_top_k * 5, 25)

            request = RetrievalRequest(
                query=query,
                notebook_id=effective_notebook_id,
                top_k=k_pool,
                document_ids=allowed_doc_ids,
                strategy=strategy or RetrievalStrategy.HYBRID,
            )

            try:
                response = self.retrieve(request)
            except Exception:
                return []

            filtered_candidates: List[ScoredCandidate] = []
            for cand in response.items:
                cand_doc = cand.document_id
                cand_page = cand.page_start or cand.metadata.get("page_number")

                is_authorized = False
                for scope in allowed_scopes:
                    if scope.document_id == cand_doc:
                        if cand_page is None:
                            is_authorized = True
                            break
                        elif scope.page_start <= cand_page <= scope.page_end:
                            is_authorized = True
                            break

                if is_authorized:
                    filtered_candidates.append(cand)

            if not filtered_candidates:
                return []

            final_items: List[ScoredCandidate] = []
            for idx, cand in enumerate(filtered_candidates[:effective_top_k], start=1):
                final_items.append(
                    cand.model_copy(update={"rank": idx})
                )
            return final_items

        request = RetrievalRequest(
            query=query,
            notebook_id=effective_notebook_id,
            top_k=effective_top_k,
            strategy=strategy or RetrievalStrategy.HYBRID,
        )
        response = self.retrieve(request)
        return response.items

