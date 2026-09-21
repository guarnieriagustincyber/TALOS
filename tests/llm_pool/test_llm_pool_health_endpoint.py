"""Integration tests for LLM Pool Health Check API (Fase 5.9 / Ajuste 4)."""

import pytest
from starlette.testclient import TestClient

from study_engine.llm.providers.mock_provider import MockProvider
from study_engine.llm.quota_manager import QuotaManager
from study_engine.llm.router import CircuitState, TalosLLMRouter
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


def test_llm_pool_health_endpoint_healthy(tmp_path):
    """GET /api/llm_pool/health should return diagnostic telemetry for all pool providers."""
    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)

    qm = QuotaManager(db_path=tmp_path / "health_quotas.db")
    p1 = MockProvider(name="cerebras")
    p2 = MockProvider(name="sambanova")

    router = TalosLLMRouter(
        providers={"cerebras": p1, "sambanova": p2},
        quota_manager=qm,
    )
    container.llm_router = router
    set_container(container)

    client = TestClient(app)
    response = client.get("/api/llm_pool/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "cerebras" in data["providers"]
    assert "sambanova" in data["providers"]
    assert data["providers"]["cerebras"]["state"] == "CLOSED"
    assert data["providers"]["cerebras"]["available"] is True
    assert data["total_requests_today"] == 0
    assert data["total_fallbacks_today"] == 0
    assert "routing_matrix" in data


def test_llm_pool_health_endpoint_degraded(tmp_path):
    """GET /api/llm_pool/health should report degraded when any provider circuit is OPEN."""
    import asyncio

    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)

    qm = QuotaManager(db_path=tmp_path / "health_quotas_deg.db")
    p1 = MockProvider(name="cerebras")
    p2 = MockProvider(name="sambanova")

    router = TalosLLMRouter(
        providers={"cerebras": p1, "sambanova": p2},
        quota_manager=qm,
        failure_threshold=1,
    )

    # Trigger failure on Cerebras to open its circuit breaker
    async def _fail_cerebras():
        await router.circuit_breakers["cerebras"].record_failure(RuntimeError("HTTP 429"))

    asyncio.run(_fail_cerebras())

    container.llm_router = router
    set_container(container)

    client = TestClient(app)
    response = client.get("/api/llm_pool/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "degraded"
    assert data["providers"]["cerebras"]["state"] == "OPEN"
    assert data["providers"]["cerebras"]["last_failure"] is not None
    assert data["providers"]["sambanova"]["state"] == "CLOSED"
