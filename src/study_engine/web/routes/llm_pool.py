"""LLM Pool Health and Telemetry Endpoints (Fase 5.9 / Ajuste 4)."""

from typing import Any, Dict
from fastapi import APIRouter, Depends

from study_engine.web.dependencies import AppContainer, get_container

router = APIRouter(prefix="/api/llm_pool", tags=["LLM Pool"])


@router.get("/health")
def get_llm_pool_health(
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Retrieve operational state, circuit status, and remaining quota across providers."""
    if hasattr(container, "llm_router") and container.llm_router is not None:
        return container.llm_router.get_health()

    return {
        "status": "uninitialized",
        "providers": {},
        "total_requests_today": 0,
        "total_fallbacks_today": 0,
        "routing_matrix": {},
    }
