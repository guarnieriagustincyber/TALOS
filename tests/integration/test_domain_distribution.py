"""Integration tests for GET /api/notebook/{notebook_id}/domain-distribution."""

import pytest
from fastapi.testclient import TestClient

from study_engine.web.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_domain_distribution_success_fadena_so2(client):
    """Retorna 200 y distribución válida con KCs y display names para fadena-so2."""
    res = client.get("/api/notebook/fadena-so2/domain-distribution")
    assert res.status_code == 200
    data = res.json()
    assert data["notebook_id"] == "fadena-so2"
    assert "total_chunks" in data
    assert isinstance(data["distribution"], list)
    assert len(data["distribution"]) > 0

    first = data["distribution"][0]
    assert "kc_id" in first
    assert "kc_display_name" in first
    assert "unit" in first
    assert "chunk_count" in first
    assert "percentage" in first
    assert first["kc_display_name"] != ""


def test_domain_distribution_success_fase0_soc(client):
    """Retorna 200 y distribución válida con KCs y display names para fase0-soc."""
    res = client.get("/api/notebook/fase0-soc/domain-distribution")
    assert res.status_code == 200
    data = res.json()
    assert data["notebook_id"] == "fase0-soc"
    assert len(data["distribution"]) == 8  # 8 Tramos canónicos de Fase 0


def test_domain_distribution_404_for_unknown_notebook(client):
    """Retorna 404 para notebook inexistente."""
    res = client.get("/api/notebook/notebook-inexistente-xyz/domain-distribution")
    assert res.status_code == 404
