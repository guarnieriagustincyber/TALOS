"""Contract and behavioral tests for Phase 5 endpoints: Telemetry, Quality Gates, and Read-Only Config."""

import pytest
from fastapi.testclient import TestClient

from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


@pytest.fixture(scope="module")
def client_phase5(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("phase5_test_dir")
    container = AppContainer(working_dir=tmp_dir, use_mock=True)
    set_container(container)
    app = create_app()
    client = TestClient(app)
    return client, container


def test_get_telemetry_metrics(client_phase5):
    """GET /api/telemetry/metrics returns authoritative scientific telemetry for Phase E5."""
    client, _ = client_phase5
    response = client.get("/api/telemetry/metrics")
    assert response.status_code == 200
    data = response.json()

    required_fields = {
        "sac",
        "eeu_oracle",
        "eeu_internal",
        "redundancy_rate",
        "far",
        "fgr",
        "raf",
        "tp_abstain",
        "fp_abstain",
        "latency_p50_ms",
        "latency_p95_ms",
        "zero_llm_epistemic_calls",
        "protocolary_comparisons",
        "timestamp",
    }
    assert required_fields.issubset(data.keys())
    assert 0.0 <= data["sac"] <= 100.0
    assert 0.0 <= data["eeu_oracle"] <= 1.0
    assert data["raf"] == 1.0
    assert data["far"] == 0.0
    assert data["tp_abstain"] >= 90
    assert data["fp_abstain"] == 0
    assert data["latency_p50_ms"] >= 0.0

    comparisons = data["protocolary_comparisons"]
    assert isinstance(comparisons, list)
    assert len(comparisons) > 0
    first_comp = comparisons[0]
    assert "benchmark_name" in first_comp
    assert "talos_sac" in first_comp
    assert "industry_baseline_sac" in first_comp
    assert first_comp["talos_sac"] > first_comp["industry_baseline_sac"]


def test_get_telemetry_gates(client_phase5):
    """GET /api/telemetry/gates returns evaluation of all formal architecture gates (E1-E5 + CAL)."""
    client, _ = client_phase5
    response = client.get("/api/telemetry/gates")
    assert response.status_code == 200
    gates = response.json()
    assert isinstance(gates, list)
    assert len(gates) >= 7

    gate_ids = [g["gate_id"] for g in gates]
    assert "G-E1" in gate_ids
    assert "G-E2" in gate_ids
    assert "G-E3" in gate_ids
    assert "G-CAL" in gate_ids
    assert "G-E4" in gate_ids
    assert "G5a-E5" in gate_ids
    assert "G5b-E5" in gate_ids
    assert "G-ABSTAIN" in gate_ids

    for g in gates:
        assert "name" in g
        assert "layer" in g
        assert "status" in g
        assert "criteria" in g
        assert "measured_value" in g
        assert "threshold" in g
        assert "pinned_commit" in g
        assert "report_path" in g
        assert g["status"] in ["PASSED", "CONDICIONAL", "BLOCKED"]

    # Verify G5b-E5 conditional behavior
    g5b = next(g for g in gates if g["gate_id"] == "G5b-E5")
    assert g5b["status"] == "CONDICIONAL"
    assert g5b["limitation_note"] is not None
    assert "n>=120" in g5b["limitation_note"]


def test_get_read_only_config(client_phase5):
    """GET /api/config/read-only returns frozen configuration snapshot (ADR-008 read-only isolation)."""
    client, _ = client_phase5
    response = client.get("/api/config/read-only")
    assert response.status_code == 200
    data = response.json()

    required_fields = {
        "bridges_allowlist",
        "lab_kc_map",
        "namespace_registry",
        "routing_table_frozen",
        "e1_category_policy",
        "frozen_perimeters",
        "adr_compliance",
        "fetched_at",
    }
    assert required_fields.issubset(data.keys())
    assert "ADR-008" in data["adr_compliance"]

    perimeters = data["frozen_perimeters"]
    assert isinstance(perimeters, list)
    assert len(perimeters) == 4

    paths = [p["path"] for p in perimeters]
    assert "src/study_engine/evidence/verification_backstop.py" in paths
    assert "src/study_engine/student/" in paths
    assert "src/study_engine/ingestion/" in paths
    assert "src/study_engine/federation/" in paths

    for p in perimeters:
        assert p["status"] == "IMMUTABLE_LOCKED"
