"""Tests for FastAPI SSE streaming endpoint /api/chat/query (Fase 5.8 / Refinamiento 3)."""

from datetime import datetime, timezone
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from study_engine.contracts.notebook import Notebook
from study_engine.hierarchy.folder import Folder
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


@pytest.fixture(scope="module")
def client_with_setup(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("chat_sse_test")
    existing_db = Path("data/web_state/knowledge_store.db")
    if existing_db.exists():
        import shutil
        shutil.copy2(existing_db, tmp_dir / "knowledge_store.db")
    app = create_app()
    container = AppContainer(working_dir=tmp_dir, use_mock=True)
    set_container(container)
    store = container.knowledge_store

    now = datetime.now(timezone.utc)
    if not store.contains_folder("f_prog"):
        folder = store.create_folder(
            Folder(
                id="f_prog",
                name="Carrera Programación",
                parent_folder_id="folder_root",
                created_at=now,
                updated_at=now,
            )
        )
    else:
        folder = store.get_folder("f_prog")

    if not store.contains_notebook("nb_prog_1"):
        nb = store.create_notebook(
            Notebook(id="nb_prog_1", name="Punteros y Memoria", folder_id="f_prog")
        )
    else:
        nb = store.get_notebook("nb_prog_1")

    client = TestClient(app)
    return client, container, nb, folder


def test_chat_query_sse_notebook_streaming(client_with_setup):
    """POST /api/chat/query streams SSE events for conceptual phase."""
    client, container, nb, folder = client_with_setup

    response = client.post(
        "/api/chat/query",
        json={
            "prompt": "¿Qué es la memoria dinámica?",
            "scope_type": "notebook",
            "scope_id": "nb_prog_1",
            "requested_phase": "conceptual",
        },
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    # Parse SSE lines
    lines = [line.strip() for line in response.text.split("\n") if line.startswith("data: ")]
    assert len(lines) > 0

    events = [json.loads(line[6:]) for line in lines]
    event_types = [e["event_type"] for e in events]

    assert "phase_start" in event_types
    assert "phase_token" in event_types
    assert "phase_complete" in event_types

    complete_ev = [e for e in events if e["event_type"] == "phase_complete"][0]
    assert complete_ev["payload"]["completed_phase"] == "conceptual"
    assert "pseudocode" in complete_ev["payload"]["next_phases"]


def test_chat_query_sse_folder_organizational(client_with_setup):
    """POST /api/chat/query on folder scope handles organizational queries via SSE."""
    client, container, nb, folder = client_with_setup

    response = client.post(
        "/api/chat/query",
        json={
            "prompt": "¿Cuál es mi progreso en esta carpeta?",
            "scope_type": "folder",
            "scope_id": "f_prog",
        },
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    lines = [line.strip() for line in response.text.split("\n") if line.startswith("data: ")]
    events = [json.loads(line[6:]) for line in lines]
    event_types = [e["event_type"] for e in events]

    assert "phase_start" in event_types
    assert "phase_complete" in event_types
    complete_ev = [e for e in events if e["event_type"] == "phase_complete"][0]
    assert complete_ev["payload"]["completed_phase"] == "folder_organizational"


def test_chat_query_nonexistent_scope_returns_404(client_with_setup):
    """Querying an unknown notebook or folder scope returns HTTP 404 fail-closed."""
    client, container, nb, folder = client_with_setup

    response = client.post(
        "/api/chat/query",
        json={
            "prompt": "hola",
            "scope_type": "notebook",
            "scope_id": "nb_inexistente",
        },
    )
    assert response.status_code == 404


def test_chat_query_fv2_e2e_abstention(client_with_setup):
    """FV-2 E2E Test: Out-of-domain or ungrounded query triggers honest abstention with reason."""
    client, container, nb, folder = client_with_setup

    class MockAbstentionDecision:
        abstained = True
        abstention_reason = "El corpus carece de respaldo verificable para responder sobre física cuántica."

    container.last_abstention_decision = MockAbstentionDecision()

    try:
        response = client.post(
            "/api/chat/query",
            json={
                "prompt": "¿Cómo construir un reactor cuántico en Marte?",
                "scope_type": "notebook",
                "scope_id": "nb_prog_1",
                "requested_phase": "conceptual",
            },
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        lines = [line.strip() for line in response.text.split("\n") if line.startswith("data: ")]
        assert len(lines) > 0
        events = [json.loads(line[6:]) for line in lines]

        # Verify evidence_manifest event contains honest abstention
        manifest_events = [e for e in events if e["event_type"] == "evidence_manifest"]
        assert len(manifest_events) == 1, "Debe emitirse un evento evidence_manifest"

        payload = manifest_events[0]["payload"]
        assert payload["abstained"] is True, "El manifest debe reportar abstained: True"
        assert payload["abstention_reason"] == "El corpus carece de respaldo verificable para responder sobre física cuántica."
    finally:
        container.last_abstention_decision = None


def test_chat_query_root_global_greeting(client_with_setup):
    """POST /api/chat/query on root_global entity returns 200 SSE greeting."""
    client, container, nb, folder = client_with_setup

    response = client.post(
        "/api/chat/query",
        json={
            "query": "hola",
            "prompt": "hola",
            "notebook_id": "root_global",
            "scope_id": "root_global",
            "scope_type": "notebook",
            "requested_scope_id": "Chat General",
        },
    )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    lines = [line.strip() for line in response.text.split("\n") if line.startswith("data: ")]
    events = [json.loads(line[6:]) for line in lines]
    event_types = [e["event_type"] for e in events]

    assert "phase_start" in event_types
    assert "phase_token" in event_types
    assert "phase_complete" in event_types

    complete_ev = [e for e in events if e["event_type"] == "phase_complete"][0]
    assert complete_ev["payload"]["completed_phase"] == "folder_organizational"
    assert "Entorno de estudio" in complete_ev["payload"]["decision"]["message"]
