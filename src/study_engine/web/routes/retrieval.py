"""Retrieval Fabric Lite Diagnostic and Inspection Endpoints (Fase 7 / F4).

Endpoints:
- GET /api/retrieval/fabric/status: Diagnostic health and capability status.
- POST /api/retrieval/fabric/inspect: Inspected routing decision and reranked candidates.
  Protected by X-Admin-Token (403) and in-memory rate limiting (10 requests/minute, 429).
"""

from collections import defaultdict, deque
import threading
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

from study_engine.config import settings
from study_engine.web.admin_auth import require_admin_token
from study_engine.web.dependencies import AppContainer, get_container

router = APIRouter(prefix="/api/retrieval", tags=["Retrieval"])


class InMemoryRateLimiter:
    """Thread-safe sliding window rate limiter (F4: 10 requests per minute)."""

    def __init__(self, max_requests: int = 10, window_seconds: float = 60.0) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: Dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def check_rate_limit(self, client_id: str) -> bool:
        """Returns True if request is allowed, False if rate limit exceeded."""
        now = time.time()
        with self._lock:
            queue = self._history[client_id]
            while queue and queue[0] <= now - self.window_seconds:
                queue.popleft()
            if len(queue) >= self.max_requests:
                return False
            queue.append(now)
            return True

    def reset(self) -> None:
        """Reset rate limiter state (useful in tests)."""
        with self._lock:
            self._history.clear()


limiter = InMemoryRateLimiter(max_requests=10, window_seconds=60.0)


class FabricInspectRequest(BaseModel):
    """Payload for administrative retrieval inspection."""

    query: str = Field(..., min_length=1, description="Query string to inspect")
    notebook_id: Optional[str] = Field(default=None, description="Target notebook identifier")
    top_k: int = Field(default=5, ge=1, le=50, description="Top-k candidates to return")


@router.get("/fabric/status")
def get_fabric_status(container: AppContainer = Depends(get_container)) -> Dict[str, Any]:
    """Diagnostic health check of the Retrieval Fabric Lite subsystem."""
    fabric = getattr(container, "retrieval_fabric", None)
    reranker = getattr(fabric, "reranker", None) if fabric else None

    return {
        "status": "healthy" if fabric is not None else "degraded",
        "subsystem": "RetrievalFabricLite",
        "jina_model": getattr(reranker, "model", settings.jina_rerank_model),
        "jina_api_key_configured": bool(settings.jina_api_key or getattr(reranker, "api_key", None)),
        "local_fallback_available": True,
        "timeout_seconds": getattr(reranker, "timeout", 2.0),
        "supported_strategies": [
            "EXACT_LEXICAL",
            "CONCEPTUAL_SEMANTIC",
            "COMPOSITE_FACETED",
        ],
        "rate_limit_inspect": "10/minute",
    }


@router.post("/fabric/inspect")
def inspect_fabric(
    request: Request,
    payload: FabricInspectRequest,
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Inspects adaptive routing and reranking with rate limiting and admin token (F4)."""
    # 1. Rate limiting check (10/min)
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not limiter.check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too Many Requests: límite de 10 inspecciones por minuto excedido.",
        )

    # 2. X-Admin-Token verification
    require_admin_token(
        x_admin_token,
        forbidden_detail="Forbidden: se requiere header X-Admin-Token válido.",
    )

    fabric = getattr(container, "retrieval_fabric", None)
    if not fabric:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RetrievalFabricLite no inicializado en el contenedor.",
        )

    store = getattr(container, "knowledge_store", None)
    target_nb = payload.notebook_id
    if not target_nb and store and hasattr(store, "list_notebooks"):
        nbs = store.list_notebooks()
        if nbs:
            target_nb = nbs[0].id
    if not target_nb:
        target_nb = "fase0-soc"

    # Route decision preview
    rewritten = fabric.query_rewriter.rewrite(payload.query) if fabric.query_rewriter else payload.query
    decision = fabric.router.route(rewritten)

    # Candidate retrieval
    candidates = fabric.retrieve(
        query=payload.query,
        notebook_id=target_nb,
        top_k=payload.top_k,
    )

    reranker = getattr(fabric, "reranker", None)
    return {
        "status": "OK",
        "query": payload.query,
        "rewritten_query": rewritten,
        "notebook_id": target_nb,
        "routing_decision": {
            "strategy": decision.strategy.value,
            "pool_depth": decision.pool_depth,
            "lexical_weight": decision.lexical_weight,
            "dense_weight": decision.dense_weight,
            "enable_rerank": decision.enable_rerank,
            "use_facets": decision.use_facets,
            "reasons": decision.reasons,
        },
        "reranker_info": {
            "model": getattr(reranker, "model", settings.jina_rerank_model),
            "jina_api_key_configured": bool(settings.jina_api_key or getattr(reranker, "api_key", None)),
            "fallback_engaged": bool(
                candidates and candidates[0].metadata.get("reranker") == "local_fallback"
            ),
        },
        "candidates": [
            {
                "chunk_id": c.chunk_id,
                "score": c.score,
                "rank": c.rank,
                "reranker": c.metadata.get("reranker", "none"),
                "content_preview": c.content[:120] + "..." if len(c.content) > 120 else c.content,
            }
            for c in candidates
        ],
    }
