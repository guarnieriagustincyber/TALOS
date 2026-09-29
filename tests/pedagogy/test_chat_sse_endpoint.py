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
            Notebook(
                id="nb_prog_1",
                name="Punteros y Memoria",
                folder_id="f_prog",
                sources=["src_fadena_prog_punteros"],
            )
        )
    else:
        nb = store.get_notebook("nb_prog_1")
        if not nb.sources:
            store.link_source_to_notebook("nb_prog_1", "src_fadena_prog_punteros")

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
    lines = [
        line.strip() for line in response.text.split("\n") if line.startswith("data: ")
    ]
    assert len(lines) > 0

    events = [json.loads(line[6:]) for line in lines]
    event_types = [e["event_type"] for e in events]

    assert "phase_start" in event_types
    assert "phase_token" in event_types
    assert "phase_complete" in event_types

    complete_ev = [e for e in events if e["event_type"] == "phase_complete"][0]
    assert complete_ev["payload"]["completed_phase"] == "conceptual"
    assert "pseudocode" in complete_ev["payload"]["next_phases"]
    conversation_context = complete_ev["payload"]["conversation_context"]
    assert conversation_context["source"] == "none"
    assert conversation_context["missing"] is True
    assert conversation_context["truncated"] is False
    provenance = complete_ev["payload"]["evidence_provenance"]
    assert provenance
    assert all(
        {"citation_id", "source_id", "source_title", "page_start", "doc_hash"}
        <= set(item)
        for item in provenance
    )


def test_chat_ui_global_folder_scope_streams_compatible_sse(client_with_setup):
    client, container, nb, folder = client_with_setup
    response = client.post(
        "/api/chat/query",
        json={
            "prompt": "Tema curricular activo: punteros (KC-POINTERS). Consulta del estudiante: ¿Qué es un puntero?",
            "scope_type": "folder",
            "scope_id": "folder_root",
            "requested_scope_id": "KC-POINTERS",
            "requested_phase": "conceptual",
            "session_id": "chat-ui-folder-scope-test",
            "recent_turns": [],
        },
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    events = [
        json.loads(line[6:])
        for line in response.text.split("\n")
        if line.startswith("data: ")
    ]
    assert any(event["event_type"] == "phase_token" for event in events)
    assert any(event["event_type"] == "phase_complete" for event in events)


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

    lines = [
        line.strip() for line in response.text.split("\n") if line.startswith("data: ")
    ]
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

        lines = [
            line.strip()
            for line in response.text.split("\n")
            if line.startswith("data: ")
        ]
        assert len(lines) > 0
        events = [json.loads(line[6:]) for line in lines]

        # Verify evidence_manifest event contains honest abstention
        manifest_events = [e for e in events if e["event_type"] == "evidence_manifest"]
        assert len(manifest_events) == 1, "Debe emitirse un evento evidence_manifest"

        payload = manifest_events[0]["payload"]
        assert payload["abstained"] is True, "El manifest debe reportar abstained: True"
        assert (
            payload["abstention_reason"]
            == "El corpus carece de respaldo verificable para responder sobre física cuántica."
        )
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

    lines = [
        line.strip() for line in response.text.split("\n") if line.startswith("data: ")
    ]
    events = [json.loads(line[6:]) for line in lines]
    event_types = [e["event_type"] for e in events]

    assert "phase_start" in event_types
    assert "phase_token" in event_types
    assert "phase_complete" in event_types

    complete_ev = [e for e in events if e["event_type"] == "phase_complete"][0]
    assert complete_ev["payload"]["completed_phase"] == "folder_organizational"
    assert "Entorno de estudio" in complete_ev["payload"]["decision"]["message"]


def test_chat_sse_sends_validated_curriculum_profile_to_backend(
    client_with_setup, monkeypatch
):
    client, container, _, _ = client_with_setup
    store = container.knowledge_store
    notebook_id = "fadena-std"
    with store.engine.transaction() as conn:
        row = conn.execute(
            "SELECT subject, curriculum_id FROM notebooks WHERE id = ?",
            (notebook_id,),
        ).fetchone()
    assert row is not None
    previous_subject, previous_curriculum_id = row

    class CapturingBackend:
        def __init__(self):
            self.calls = []

        async def stream(
            self,
            system_prompt,
            user_prompt,
            phase_id=None,
            context=None,
            max_tokens=None,
        ):
            self.calls.append(
                {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                }
            )
            yield "El modelo relacional organiza los datos en relaciones [E1]."

    backend = CapturingBackend()
    with store.engine.transaction() as conn:
        conn.execute(
            "UPDATE notebooks SET subject = ?, curriculum_id = ? WHERE id = ?",
            (
                "Sistema de Tratamiento de Datos",
                "fadena_std_2026",
                notebook_id,
            ),
        )

    from study_engine.web.routes import chat as chat_route

    evidence = [
        {
            "id": "E1",
            "chunk_text": "El modelo relacional organiza los datos en relaciones.",
            "source_id": "src_std_test",
            "source_title": "Material curricular de prueba",
            "page_start": 1,
            "score": 0.95,
        }
    ]
    monkeypatch.setattr(
        chat_route,
        "_assemble_epistemic_context",
        lambda **_: (
            chat_route.EpistemicContextPack(
                formatted_context="[E1] El modelo relacional organiza los datos en relaciones.",
                citations=["[E1] Material curricular de prueba, pág. 1"],
                chunks=evidence,
            ),
            evidence,
        ),
    )
    monkeypatch.setattr(
        chat_route,
        "_resolve_chat_backend",
        lambda *_args, **_kwargs: backend,
    )

    try:
        response = client.post(
            "/api/chat/query",
            json={
                "prompt": "¿Qué es el modelo relacional?",
                "scope_type": "notebook",
                "scope_id": notebook_id,
                "requested_phase": "conceptual",
                "session_id": "validated-curriculum-profile",
            },
        )
    finally:
        with store.engine.transaction() as conn:
            conn.execute(
                "UPDATE notebooks SET subject = ?, curriculum_id = ? WHERE id = ?",
                (previous_subject, previous_curriculum_id, notebook_id),
            )

    assert response.status_code == 200
    assert backend.calls
    system_prompt = backend.calls[0]["system_prompt"]
    assert "Materia: Sistema de Tratamiento de Datos" in system_prompt
    assert "curriculum_id: fadena_std_2026" in system_prompt
    assert "no conviertas toda explicación en SQL" in system_prompt
    assert "Lenguajes de Programación" not in system_prompt
    assert "x86-64" not in system_prompt
