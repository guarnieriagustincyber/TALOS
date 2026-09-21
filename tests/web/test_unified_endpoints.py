"""Tests for unified TALOS frontend-backend integration endpoints."""

from datetime import datetime, timezone
import json
import pytest
from fastapi.testclient import TestClient

from study_engine.contracts.notebook import Notebook
from study_engine.hierarchy.folder import Folder
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


@pytest.fixture(scope="module")
def client_with_env(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("web_unified_test")
    app = create_app()
    container = AppContainer(working_dir=tmp_dir, use_mock=True)
    set_container(container)
    store = container.knowledge_store

    now = datetime.now(timezone.utc)
    if not store.contains_folder("folder_root"):
        store.create_folder(
            Folder(
                id="folder_root",
                name="Root Workspace",
                parent_folder_id=None,
                created_at=now,
                updated_at=now,
            )
        )
    if not store.contains_folder("folder_fase0"):
        store.create_folder(
            Folder(
                id="folder_fase0",
                name="Fase 0 - Ciberseguridad",
                parent_folder_id="folder_root",
                created_at=now,
                updated_at=now,
            )
        )
    if not store.contains_notebook("nb_prog_basica"):
        store.create_notebook(
            Notebook(
                id="nb_prog_basica",
                name="Programación Básica",
                folder_id="folder_fase0",
            )
        )

    client = TestClient(app)
    return client, container


def test_get_curriculum_graph(client_with_env):
    """GET /api/curriculum/graph returns 501 Not Implemented (Fix 1.4 / 2.2)."""
    client, _ = client_with_env
    response = client.get("/api/curriculum/graph")
    assert response.status_code == 501
    assert "no disponible" in response.json()["detail"].lower()


def test_practice_evaluate(client_with_env):
    """POST /api/practice/evaluate returns PRACTICE_UNAVAILABLE fail-closed (Fix 2.1)."""
    client, _ = client_with_env
    response = client.post(
        "/api/practice/evaluate",
        json={
            "task_id": "task_net_tcp_01",
            "file_path": "labs/net_tcp_syn.py",
            "command": ":eval",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "task_net_tcp_01"
    assert data["status"] == "PRACTICE_UNAVAILABLE"
    assert data["assertions_passed"] == 0
    assert data["assertions_total"] == 0
    assert data["ledger_block_hash"] is None
    assert "no disponible" in data["stdout"].lower()


def test_sources_page_render_and_validation(client_with_env):
    """GET /api/sources/{doc_hash}/page-render tests validation and error branches."""
    client, _ = client_with_env
    # Invalid hash format
    bad_res = client.get("/api/sources/invalid_hash/page-render?page=1")
    assert bad_res.status_code == 400

    # Non-existent hash
    missing_hash = "a" * 64
    missing_res = client.get(f"/api/sources/{missing_hash}/page-render?page=1")
    assert missing_res.status_code == 404


def test_chat_query_ui_format_compatibility(client_with_env):
    """POST /api/chat/query works with UI format (query + notebook_id)."""
    client, _ = client_with_env
    response = client.post(
        "/api/chat/query",
        json={
            "query": "¿Qué es una variable?",
            "notebook_id": "nb_prog_basica",
            "requested_scope_id": "Programación Básica",
        },
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    lines = [line.strip() for line in response.text.split("\n") if line.startswith("data: ")]
    assert len(lines) > 0
    events = [json.loads(line[6:]) for line in lines]
    types = [e["event_type"] for e in events]
    assert "phase_start" in types or "abstention" in types


def test_get_student_cognitive_state_endpoint(client_with_env):
    """GET /api/student/cognitive-state returns real BKT mastery and active alerts (Fix 3.3)."""
    client, _ = client_with_env
    response = client.get("/api/student/cognitive-state")
    assert response.status_code == 200
    data = response.json()
    assert "kc_mastery" in data
    assert "active_alerts" in data
    assert "student_id" in data


def test_evidence_claims_and_contradictions(client_with_env):
    """GET /api/evidence/claims/{session_id} returns claims, redactions and contradictions."""
    from study_engine.web.routes.evidence import _claims_cache
    _claims_cache["sess_test_1"] = {
        "session_id": "sess_test_1",
        "verdict": "PARTIAL_ABSTENTION",
        "claims": [
            {
                "claim_id": "C1",
                "claim_text": "El puntero en C almacena la dirección de memoria física o virtual del objeto referenciado.",
                "claim_type": "FACTUAL_TEXTUAL",
                "criticality": "CRITICAL",
                "status": "SUPPORTED",
                "grounding_ratio": 0.96,
                "cited_evidence_indices": ["E1"],
                "has_redaction": False,
            },
            {
                "claim_id": "C2",
                "claim_text": "La aritmética de punteros escala el desplazamiento por sizeof(T) en tiempo de compilación.",
                "claim_type": "FORMAL_ARITHMETIC",
                "criticality": "CRITICAL",
                "status": "SUPPORTED",
                "grounding_ratio": 1.0,
                "cited_evidence_indices": ["E1", "E2"],
                "has_redaction": False,
            },
            {
                "claim_id": "C3",
                "claim_text": "El estándar C99 garantiza límites automáticos de array en tiempo de ejecución.",
                "claim_type": "FACTUAL_TEXTUAL",
                "criticality": "NON_CRITICAL",
                "status": "UNSUPPORTED",
                "grounding_ratio": 0.18,
                "cited_evidence_indices": [],
                "has_redaction": True,
            },
        ],
        "contradictions": [
            {
                "claim_id": "C-CONTRA-1",
                "claim_text": "Frecuencia y resolución de avance del reloj de Sequence Numbers (ISN)",
                "source_a": "RFC 793 (Pág. 24) [E1]",
                "assertion_a": "El reloj de ISN se incrementa aproximadamente cada 4 microsegundos (frecuencia ~250 kHz).",
                "source_b": "Reporte ThreatIntel TF-02 [TF1]",
                "assertion_b": "El reloj de sequence numbers avanza a intervalos discretos de 1 milisegundo en kernels virtualizados.",
                "conflict_type": "TEMPORAL_RESOLUTION_MISMATCH",
                "status": "UNRESOLVED_CONTRADICTION",
            }
        ],
        "redacted_text": (
            "En arquitectura de sistemas, la memoria se organiza linealmente. "
            "El puntero en C almacena la dirección de memoria [E1]. "
            "La aritmética de punteros escala por sizeof(T) [E1, E2]. "
            "El estándar C99 garantiza límites automáticos de array en tiempo de ejecución [SIN_RESPALDO]."
        ),
    }

    client, _ = client_with_env
    response = client.get("/api/evidence/claims/sess_test_1")
    assert response.status_code == 200
    data = response.json()

    assert data["session_id"] == "sess_test_1"
    assert data["verdict"] in ("APPROVED", "PARTIAL_ABSTENTION", "REJECTED_UNSUPPORTED")
    assert len(data["claims"]) >= 3

    # Verify claim types and statuses
    c1 = data["claims"][0]
    assert c1["status"] == "SUPPORTED"
    assert c1["grounding_ratio"] > 0.90

    c3 = [c for c in data["claims"] if c["status"] == "UNSUPPORTED"][0]
    assert c3["has_redaction"] is True

    # Verify [SIN_RESPALDO] redaction in text
    assert "[SIN_RESPALDO]" in data["redacted_text"]

    # Verify side-by-side contradiction
    assert len(data["contradictions"]) >= 1
    contra = data["contradictions"][0]
    assert contra["status"] == "UNRESOLVED_CONTRADICTION"
    assert contra["source_a"] is not None
    assert contra["source_b"] is not None
    assert contra["assertion_a"] is not None
    assert contra["assertion_b"] is not None


def test_evidence_coverage_evaluation(client_with_env):
    """GET /api/evidence/coverage/{session_id} returns facet coverage and grounding rate."""
    from study_engine.web.routes.evidence import _coverage_cache
    _coverage_cache["sess_test_1"] = {
        "session_id": "sess_test_1",
        "facets": {
            "modelo_memoria_punteros": "SUFFICIENT",
            "aritmetica_offsets": "SUFFICIENT",
            "gestion_heap_stack": "PARTIAL",
            "seguridad_buffer_overflow": "MISSING",
        },
        "coverage_ratio": 0.62,
        "sufficient_count": 2,
        "partial_count": 1,
        "missing_count": 1,
        "status": "PARTIAL_COVERAGE",
        "grounding_rate": 0.88,
        "notes": "Evaluación de cobertura de facetas y grounding rate bajo política E2.",
    }

    client, _ = client_with_env
    response = client.get("/api/evidence/coverage/sess_test_1")
    assert response.status_code == 200
    data = response.json()

    assert data["session_id"] == "sess_test_1"
    assert "facets" in data
    assert data["coverage_ratio"] > 0
    assert data["sufficient_count"] >= 1
    assert data["grounding_rate"] > 0.5


def test_evidence_fail_closed_validation(client_with_env):
    """Evidence endpoints reject empty or invalid session IDs fail-closed."""
    client, _ = client_with_env
    res_claims = client.get("/api/evidence/claims/%20")
    assert res_claims.status_code == 400

    res_cov = client.get("/api/evidence/coverage/%20")
    assert res_cov.status_code == 400


def test_student_telemetry_and_fail_closed(client_with_env):
    """Test student cognitive state, SM-2, and remediation validation."""
    client, _ = client_with_env

    # Cognitive state
    cog_res = client.get("/api/student/cognitive-state")
    assert cog_res.status_code == 200
    cog_data = cog_res.json()
    assert "kc_mastery" in cog_data
    assert "active_alerts" in cog_data

    # Spaced repetition due
    due_res = client.get("/api/student/spaced-repetition/due")
    assert due_res.status_code == 200
    due_data = due_res.json()
    assert isinstance(due_data, list)
    if len(due_data) >= 1:
        assert "anchor_id" in due_data[0]
        assert "is_due" in due_data[0]

    # Readiness probe (deterministic plan_only=True)
    ready_res = client.post(
        "/api/student/readiness/assess",
        json={"topic_id": "SEC-02-OS-PROC", "plan_only": True},
    )
    assert ready_res.status_code == 200
    ready_data = ready_res.json()
    assert "recommendation" in ready_data
    assert "prerequisites" in ready_data

    # Remediation fail-closed on invalid choice
    bad_remed = client.post(
        "/api/student/remediation/respond",
        json={"interrupt_id": "SEC-03-MEM-MGMT", "choice": "INVALID_POLICY"},
    )
    assert bad_remed.status_code == 400
    assert "Elección inválida" in bad_remed.json()["detail"]

    # Remediation success on normative choice
    good_remed = client.post(
        "/api/student/remediation/respond",
        json={"interrupt_id": "SEC-03-MEM-MGMT", "choice": "PAUSE_AND_REMEDIATE"},
    )
    assert good_remed.status_code == 200
    assert good_remed.json()["choice"] == "PAUSE_AND_REMEDIATE"


def test_sources_open_local_fail_closed(client_with_env):
    """POST /api/sources/open-local rejects malformed hashes fail-closed."""
    client, _ = client_with_env
    res = client.post("/api/sources/open-local", json={"doc_hash": "not-a-valid-sha256"})
    assert res.status_code == 400


def test_evidence_open_local_pdf(client_with_env):
    """GET /api/evidence/open-local-pdf validates hashes and handles requests (Fix 1.1)."""
    client, _ = client_with_env
    # 1. Invalid hash -> 400
    res_bad = client.get("/api/evidence/open-local-pdf?hash=invalid_hash")
    assert res_bad.status_code == 400

    # 2. Non-existent valid SHA-256 -> 404
    dummy_sha = "a" * 64
    res_404 = client.get(f"/api/evidence/open-local-pdf?hash={dummy_sha}&page=3")
    assert res_404.status_code == 404
    assert "no hallado" in res_404.json()["detail"].lower()


