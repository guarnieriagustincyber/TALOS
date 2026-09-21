"""Contract and behavioral tests for Phase 4 endpoints: CAL, Federation, Threat Intel."""

import pytest
from fastapi.testclient import TestClient

from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


@pytest.fixture(scope="module")
def client_phase4(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("phase4_test_dir")
    container = AppContainer(working_dir=tmp_dir, use_mock=True)
    set_container(container)
    app = create_app()
    client = TestClient(app)
    return client, container


def test_get_ingestion_catalog(client_phase4):
    """GET /api/ingestion/catalog returns full CAL metadata with confidence and format indicators."""
    client, _ = client_phase4
    response = client.get("/api/ingestion/catalog")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    first = data[0]
    required_keys = {
        "source_id",
        "title",
        "doc_hash",
        "chunk_count",
        "converter_id",
        "converter_version",
        "conversion_score",
        "conflict_flag",
        "formulas_unextracted",
        "trust_level",
        "ocr_provenance",
        "ingested_at",
    }
    assert required_keys.issubset(first.keys())
    assert 0.0 <= first["conversion_score"] <= 1.0
    assert first["trust_level"] in ["verified", "unverified"]
    assert first["ocr_provenance"] in ["none", "local_tesseract", "cloud"]
    assert isinstance(first["formulas_unextracted"], bool)
    assert isinstance(first["conflict_flag"], bool)


def test_get_conversion_conflicts(client_phase4):
    """GET /api/ingestion/conflicts returns discrepancies between competing converters."""
    client, _ = client_phase4
    response = client.get("/api/ingestion/conflicts")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    first = data[0]
    required_keys = {
        "conflict_id",
        "source_sha256",
        "converter_a",
        "converter_b",
        "candidate_a_hash",
        "candidate_b_hash",
        "diff_stat",
        "resolution",
        "created_at",
    }
    assert required_keys.issubset(first.keys())
    assert first["resolution"] in ["PENDING", "ADJUDICATED"]
    assert first["diff_stat"] >= 0.0


def test_get_federation_notebooks(client_phase4):
    """GET /api/federation/notebooks returns sovereign notebooks in confinement mode."""
    client, _ = client_phase4
    response = client.get("/api/federation/notebooks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3

    nb_ids = [nb["notebook_id"] for nb in data]
    assert "fadena-prog" in nb_ids or "NB-CYBERSECURITY-V1" in nb_ids

    first = data[0]
    required_keys = {
        "notebook_id",
        "name",
        "subject",
        "level",
        "source_count",
        "default_scope",
        "created_at",
    }
    assert required_keys.issubset(first.keys())
    assert first["default_scope"] in ["confined", "federated"]


def test_get_federation_bridges(client_phase4):
    """GET /api/federation/bridges returns contractual bridges with computed TTL and status."""
    client, _ = client_phase4
    response = client.get("/api/federation/bridges")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    first = data[0]
    required_keys = {
        "bridge_id",
        "source_notebook",
        "target_notebook",
        "topic_allowlist",
        "direction",
        "ttl_days",
        "created_at",
        "expires_at",
        "status",
        "reviewer",
        "provenance_tag",
    }
    assert required_keys.issubset(first.keys())
    assert first["status"] in ["ACTIVE", "EXPIRED"]
    assert isinstance(first["topic_allowlist"], list)
    assert len(first["topic_allowlist"]) > 0
    assert first["ttl_days"] >= 0
    assert "[E#:bridge:" in first["provenance_tag"] or len(first["provenance_tag"]) > 0


def test_get_threat_intel_feed(client_phase4):
    """GET /api/threatintel/feed returns normalized IOCs with multi-feed quorum consensus.
    
    INVARIANT ADR-008:
    Threat intel items marked 'unverified' represent external threat data ([TF#])
    and must remain epistemically quarantined.
    """
    client, _ = client_phase4
    response = client.get("/api/threatintel/feed")
    assert response.status_code == 200
    assert response.headers.get("X-Warning") == "DEMO-DATA"
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    for ioc in data:
        required_keys = {
            "ioc_id",
            "type",
            "value",
            "verdict",
            "trust_level",
            "quorum",
            "conflicts",
            "last_updated",
        }
        assert required_keys.issubset(ioc.keys())
        assert ioc["type"] in ["ip", "domain", "sha256", "url"]
        assert ioc["verdict"] in ["malicious", "clean", "suspicious", "unknown"]
        assert ioc["trust_level"] in ["unverified", "verified_human"]

        quorum = ioc["quorum"]
        assert "feeds_agree" in quorum
        assert "total_feeds" in quorum
        assert quorum["feeds_agree"] <= quorum["total_feeds"]
        assert quorum["total_feeds"] >= 1
