"""Unified Retrieval Service Facade for Subsystem S3 -> S4.

Provides a clean boundary between retrieval internals and downstream
evidence packaging, guaranteeing that S4 interacts solely with
ScoredCandidate lists without knowledge of retrieval algorithms.

"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from study_engine.contracts.retrieval import (
    RetrievalRequest,
    RetrievalStrategy,
    ScoredCandidate,
)
from study_engine.retrieval.base import BaseRetriever
from study_engine.retrieval.dense import DenseRetriever
from study_engine.retrieval.embedding import (
    EmbeddingProvider,
    LocalONNXEmbeddingProvider,
)
from study_engine.retrieval.hybrid import HybridRetriever
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.retrieval.vector_store import SQLiteVectorStore
from study_engine.storage.knowledge_store import KnowledgeStore

# Custom exception for retrieval service errors
class RetrievalError(Exception):
    """Raised when the RetrievalService encounters a critical error, such as missing notebooks."""
    pass

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("data/config/retrieval_config.json")


def load_retrieval_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load external retrieval configuration with safe fallback."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.is_absolute():
        candidates = [path, Path(__file__).resolve().parents[3] / path]
        for c in candidates:
            if c.is_file():
                path = c
                break

    if path.is_file():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)  # type: ignore[no-any-return]
        except Exception as e:
            logger.warning("Failed to parse retrieval config at %s: %s. Using defaults.", path, e)

    return {
        "relevance_gate": {
            "dense_threshold_no_lexical": 0.84,
            "calibration_model": "Qwen/Qwen3-Embedding-8B",
        }
    }


class RetrievalService:
    """Unified service facade for evidence candidate retrieval."""

    def __init__(
        self,
        store: KnowledgeStore,
        retriever: Optional[BaseRetriever] = None,
        vector_store: Optional[SQLiteVectorStore] = None,
        provider: Optional[EmbeddingProvider] = None,
        dense_threshold: Optional[float] = None,
        fabric: Optional[Any] = None,
    ) -> None:
        """Initialize RetrievalService.

        If retriever is not provided, defaults to HybridRetriever (RRF).
        """
        self._store = store
        self._fabric = fabric
        self._last_rejections: List[Dict[str, Any]] = []

        config = load_retrieval_config()
        self._dense_threshold: float = (
            dense_threshold
            if dense_threshold is not None
            else float(
                config.get("relevance_gate", {}).get(
                    "dense_threshold_no_lexical", 0.84
                )
            )
        )

        if retriever is not None:
            self._retriever = retriever
        else:
            lexical = LexicalRetriever(store)
            if vector_store is not None:
                if provider is not None:
                    emb_provider = provider
                else:
                    try:
                        import sentence_transformers  # noqa: F401
                        from study_engine.retrieval.embedding import SentenceTransformerEmbeddingProvider
                        emb_provider = SentenceTransformerEmbeddingProvider()
                    except Exception:
                        try:
                            emb_provider = LocalONNXEmbeddingProvider()
                        except Exception:
                            from study_engine.retrieval.embedding import DeterministicHashEmbedder
                            emb_provider = DeterministicHashEmbedder(dimensions=4096)
                dense = DenseRetriever(store, vector_store, emb_provider)
                self._retriever = HybridRetriever(store, lexical, dense)
            else:
                # Fallback to lexical if vector store is omitted
                self._retriever = lexical

    @property
    def store(self) -> KnowledgeStore:
        """Access the authoritative KnowledgeStore."""
        return self._store

    @property
    def dense_threshold(self) -> float:
        """Effective dense threshold for non-lexical candidates."""
        return self._dense_threshold

    @property
    def last_rejections(self) -> List[Dict[str, Any]]:
        """Telemetry records of candidates rejected by the relevance gate."""
        return list(self._last_rejections)

    @property
    def fabric(self) -> Optional[Any]:
        """Access the optional RetrievalFabricLite instance."""
        return self._fabric

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
        """Retrieve authoritative evidence candidates with Epistemic Gatekeeper isolation.

        Parameters
        ----------
        query : str
            Search query string.
        notebook_id_or_node_id : Optional[str]
            Curricular node_id (if registry is provided) or notebook_id (legacy).
        registry_or_top_k : Union[int, Any, None]
            CurriculumRegistry instance or integer top_k (legacy positional).
        top_k : int
            Maximum number of candidates to retrieve.
        strategy : Optional[RetrievalStrategy]
            Retrieval strategy override.
        node_id : Optional[str]
            Curricular node identifier for epistemic scoping (e.g. 'SEC-01-C-PTR').
        registry : Optional[Any]
            CurriculumRegistry instance containing alignment matrices.
        notebook_id : Optional[str]
            Explicit notebook identifier override.
        matrix_id : Optional[str]
            Explicit alignment matrix identifier override.

        Returns
        -------
        List[ScoredCandidate]
            Ranked list of authorized candidates (Fail-Closed: empty if unauthorized).
        """
        self._last_rejections = []

        # Chokepoint único de reescritura de consultas (C1)
        effective_query = query
        try:
            from study_engine.retrieval.query_rewriter import QueryRewriter
            effective_query = QueryRewriter().rewrite(query)
        except Exception as rew_err:
            logger.debug("Query rewriting fallback to raw query in RetrievalService: %s", rew_err)

        # Resolve overloaded positional arguments
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
                # registry_or_top_k is a CurriculumRegistry instance
                effective_registry = registry_or_top_k
                if notebook_id_or_node_id is not None and effective_node_id is None:
                    effective_node_id = notebook_id_or_node_id
        elif notebook_id_or_node_id is not None:
            if effective_node_id is None and effective_registry is not None:
                effective_node_id = notebook_id_or_node_id
            elif effective_notebook_id is None:
                effective_notebook_id = notebook_id_or_node_id

        default_strat = getattr(
            self._retriever, "strategy", RetrievalStrategy.HYBRID
        )
        request_strategy: RetrievalStrategy = (
            strategy if strategy is not None else default_strat
        )

        # Resolve authoritative notebook if not explicitly provided
        if not effective_notebook_id:
            notebooks = self._store.list_notebooks()
            if not notebooks:
                raise RetrievalError(
                    "No notebooks registered; run scripts/ingest_pdfs.py first."
                )
            effective_notebook_id = notebooks[0].id

        # Epistemic Gatekeeper Branch
        if effective_node_id is not None and effective_registry is not None:
            try:
                allowed_scopes = effective_registry.get_scoped_sources_for_node(
                    node_id=effective_node_id,
                    matrix_id_or_path=matrix_id or "cybersecurity_v1_alignment.json",
                )
            except Exception:
                # Fail-Closed: unaligned or unknown node yields zero candidates
                return []

            if not allowed_scopes:
                return []

            allowed_doc_ids = list({scope.document_id for scope in allowed_scopes})
            k_pool = max(effective_top_k * 5, 25)

            request = RetrievalRequest(
                query=effective_query,
                notebook_id=effective_notebook_id,
                top_k=k_pool,
                document_ids=allowed_doc_ids,
                strategy=request_strategy,
            )

            try:
                response = self._retriever.retrieve(request)
            except Exception:
                return []

            # Page-Fidelity Epistemic Filter
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

            relevance_gated = self._apply_relevance_gate(filtered_candidates)
            if not relevance_gated:
                return []

            # Deterministic re-ranking
            final_items: List[ScoredCandidate] = []
            for idx, cand in enumerate(relevance_gated[:effective_top_k], start=1):
                final_items.append(
                    cand.model_copy(update={"rank": idx})
                )
            # Log retrieval outcome
            logger.info(
                f"Retrieval: query='{query}', notebook={effective_notebook_id}, results={len(final_items)}"
            )
            return final_items

        # Standard Retrieval Branch (delegates to Fabric if configured)
        if self._fabric is not None:
            final_items = self._fabric.retrieve(
                query=effective_query,
                notebook_id=effective_notebook_id,
                top_k=effective_top_k,
            )
            logger.info(
                f"Retrieval Fabric: query='{query}', notebook={effective_notebook_id}, results={len(final_items)}"
            )
            return final_items

        request = RetrievalRequest(
            query=effective_query,
            notebook_id=effective_notebook_id,
            top_k=effective_top_k,
            strategy=request_strategy,
        )
        response = self._retriever.retrieve(request)
        final_items = self._apply_relevance_gate(response.items)[:effective_top_k]
        # Log retrieval outcome
        logger.info(
            f"Retrieval: query='{query}', notebook={effective_notebook_id}, results={len(final_items)}"
        )
        return final_items

    def _apply_relevance_gate(
        self, candidates: List[ScoredCandidate]
    ) -> List[ScoredCandidate]:
        """Filter candidates through the hybrid relevance gate.

        A candidate is admitted if:
        1. It has lexical support (lexical_score > 0.0 or metadata['in_lexical'] is True).
        2. OR the retrieval candidate pool contains verified lexical hits confirming
           that the query is curricularly in-domain.
        3. OR its dense similarity meets or exceeds dense_threshold.

        Otherwise, the candidate is pruned and recorded in rejection telemetry.
        """
        query_has_lexical = any(
            (c.lexical_score is not None and c.lexical_score > 0.0)
            or bool(c.metadata.get("in_lexical"))
            or (float(c.metadata.get("lexical_score", 0.0)) > 0.0)
            for c in candidates
        )

        gated: List[ScoredCandidate] = []
        for cand in candidates:
            has_cand_lexical = (
                (cand.lexical_score is not None and cand.lexical_score > 0.0)
                or bool(cand.metadata.get("in_lexical"))
                or (float(cand.metadata.get("lexical_score", 0.0)) > 0.0)
            )
            dense_score = (
                float(cand.dense_score)
                if cand.dense_score is not None
                else float(cand.metadata.get("dense_score", 0.0))
            )

            if has_cand_lexical or query_has_lexical:
                gated.append(cand)
            elif dense_score >= self._dense_threshold:
                gated.append(cand)
            else:
                rejection = {
                    "chunk_id": cand.chunk_id,
                    "document_id": cand.document_id,
                    "reason": "LOW_DENSE_NO_LEXICAL",
                    "dense_score": dense_score,
                    "threshold": self._dense_threshold,
                }
                self._last_rejections.append(rejection)
                logger.debug(
                    "Rejected candidate %s (doc=%s): dense=%.4f < threshold=%.4f without lexical support",
                    cand.chunk_id,
                    cand.document_id,
                    dense_score,
                    self._dense_threshold,
                )
        return gated

    def retrieve_multi_query_evidence(
        self,
        sub_queries: Sequence[Any],
        notebook_id_or_node_id: Optional[str] = None,
        registry_or_top_k: Union[int, Any, None] = None,
        top_k: int = 5,
        strategy: Optional[RetrievalStrategy] = None,
        *,
        node_id: Optional[str] = None,
        registry: Optional[Any] = None,
        notebook_id: Optional[str] = None,
        matrix_id: Optional[str] = None,
    ) -> Dict[str, List[ScoredCandidate]]:
        """Retrieve evidence candidates concurrently across multiple sub-queries.

        Parameters
        ----------
        sub_queries : Sequence[Any]
            List of sub-queries (strings or SubQuery instances).
        ...

        Returns
        -------
        Dict[str, List[ScoredCandidate]]
            Map of sub_query_id -> candidates tagged with sub_query_id.
        """
        from study_engine.contracts.evidence_engine import SubQuery

        results: Dict[str, List[ScoredCandidate]] = {}

        for idx, item in enumerate(sub_queries, start=1):
            if isinstance(item, SubQuery):
                sq_id = item.sub_query_id
                query_text = item.text
            elif isinstance(item, str):
                sq_id = f"sq-{idx}"
                query_text = item
            else:
                sq_id = getattr(item, "sub_query_id", f"sq-{idx}")
                query_text = getattr(item, "text", str(item))

            cands = self.retrieve_evidence(
                query=query_text,
                notebook_id_or_node_id=notebook_id_or_node_id,
                registry_or_top_k=registry_or_top_k,
                top_k=top_k,
                strategy=strategy,
                node_id=node_id,
                registry=registry,
                notebook_id=notebook_id,
                matrix_id=matrix_id,
            )

            # Annotate metadata with sub_query_id
            annotated_cands: List[ScoredCandidate] = []
            for c in cands:
                meta = dict(c.metadata)
                meta["sub_query_id"] = sq_id
                annotated_cands.append(c.model_copy(update={"metadata": meta}))

            results[sq_id] = annotated_cands

        return results

