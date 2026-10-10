"""Tests for FastAPI SSE streaming endpoint /api/chat/query (Fase 5.8 / Refinamiento 3)."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.hierarchy.folder import Folder
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


@pytest.fixture(scope="module")
def client_with_setup(tmp_path_factory, knowledge_store_test_copy):
    tmp_dir = tmp_path_factory.mktemp("chat_sse_test")
    if knowledge_store_test_copy is not None:
        import shutil

        shutil.copy2(knowledge_store_test_copy, tmp_dir / "knowledge_store.db")
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
        assert [event["event_type"] for event in events] == [
            "evidence_manifest",
            "abstention",
        ]
        assert (
            events[-1]["payload"]["reason"]
            == "El corpus carece de respaldo verificable para responder sobre física cuántica."
        )
    finally:
        container.last_abstention_decision = None


def test_chat_query_sse_clarification_is_a_terminal_pedagogical_outcome(
    client_with_setup, monkeypatch
):
    client, container, _, _ = client_with_setup
    from study_engine.web.routes import chat as chat_route

    original_prepare = chat_route._prepare_chat_context
    clarification = "¿Podés indicar qué concepto del tema querés revisar?"

    def prepare_context_with_clarification(**kwargs):
        prepared = list(original_prepare(**kwargs))
        prepared[2] = chat_route.EpistemicContextPack(
            formatted_context="",
            citations=[],
            chunks=[],
            abstained=True,
            abstention_reason="NEEDS_CLARIFICATION",
            clarification_message=clarification,
        )
        prepared[3] = []
        return tuple(prepared)

    monkeypatch.setattr(
        chat_route, "_prepare_chat_context", prepare_context_with_clarification
    )
    response = client.post(
        "/api/chat/query",
        json={
            "prompt": "No entiendo esto",
            "scope_type": "notebook",
            "scope_id": "nb_prog_1",
            "requested_phase": "conceptual",
        },
    )

    events = [
        json.loads(line[6:])
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert response.text.endswith("\n\n")
    assert [event["event_type"] for event in events] == [
        "evidence_manifest",
        "clarification",
    ]
    assert sum(event["event_type"] == "phase_token" for event in events) == 0
    assert events[-1]["payload"]["abstained"] is True
    assert events[-1]["payload"]["abstention_code"] == "NEEDS_CLARIFICATION"
    assert events[-1]["payload"]["reason"] == clarification
    assert not any(event["event_type"] == "phase_complete" for event in events)


def test_chat_query_sse_error_does_not_expose_exception_details(
    client_with_setup, monkeypatch
):
    client, container, _, _ = client_with_setup
    from study_engine.web.routes import chat as chat_route

    original_prepare = chat_route._prepare_chat_context
    chunks = [
        {
            "id": "E1",
            "chunk_text": "Material curricular de prueba.",
            "source_id": "src_sse_error_test",
            "source_title": "Material curricular de prueba",
            "page_start": 1,
            "score": 0.95,
        }
    ]

    def prepare_sufficient_context(**kwargs):
        prepared = list(original_prepare(**kwargs))
        prepared[2] = chat_route.EpistemicContextPack(
            formatted_context="[E1] Material curricular de prueba.",
            citations=["[E1] Material curricular de prueba, pág. 1"],
            chunks=chunks,
            is_sufficient=True,
        )
        prepared[3] = chunks
        return tuple(prepared)

    class FailingPipeline:
        def __init__(self, **_kwargs):
            pass

        async def generate_phased_response(self, **_kwargs):
            raise RuntimeError("secret_backend_detail")
            yield

    monkeypatch.setattr(chat_route, "_prepare_chat_context", prepare_sufficient_context)
    monkeypatch.setattr(chat_route, "StructuredResponsePipeline", FailingPipeline)
    response = client.post(
        "/api/chat/query",
        json={
            "prompt": "Explicá el concepto de prueba.",
            "scope_type": "notebook",
            "scope_id": "nb_prog_1",
            "requested_phase": "conceptual",
        },
    )

    events = [
        json.loads(line[6:])
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert response.text.endswith("\n\n")
    assert [event["event_type"] for event in events] == ["error"]
    assert events[0]["payload"] == {
        "reason": (
            "TALOS no pudo completar la respuesta por un error técnico. "
            "Reintentá la consulta."
        )
    }
    assert "secret_backend_detail" not in response.text


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


@pytest.mark.parametrize(
    (
        "notebook_id",
        "curriculum_id",
        "expected_subject",
        "expected_guidance",
    ),
    [
        (
            "fase0-soc",
            "roadmap_kasiu_v4_fase0",
            "Programación y Pensamiento Algorítmico",
            "traza o pseudocódigo",
        ),
        (
            "fadena-lenguajes",
            "fadena_lenguajes_2026",
            "Lenguajes de Programación",
            "pseudocódigo, C, programación",
        ),
        (
            "fadena-so2",
            "fadena_so2_2026",
            "Sistemas Operativos II",
            "estados, intercalaciones",
        ),
        (
            "fadena-std",
            "fadena_std_2026",
            "Sistema de Tratamiento de Datos",
            "no conviertas toda explicación en SQL",
        ),
        (
            "fadena-teleco",
            "fadena_teleco_2025",
            "Infraestructura de Telecomunicaciones",
            "Señales, capas",
        ),
        (
            "fadena-so2-extra",
            "fadena_so2_2026",
            None,
            None,
        ),
    ],
)
def test_chat_sse_sends_only_the_exact_curriculum_profile_to_backend(
    client_with_setup,
    monkeypatch,
    notebook_id,
    curriculum_id,
    expected_subject,
    expected_guidance,
):
    client, container, _, _ = client_with_setup
    store = container.knowledge_store
    with store.engine.transaction() as conn:
        row = conn.execute(
            "SELECT subject, curriculum_id FROM notebooks WHERE id = ?",
            (notebook_id,),
        ).fetchone()
    created_notebook = row is None
    if created_notebook:
        store.create_notebook(
            Notebook(
                id=notebook_id,
                name=f"Gate 2 test notebook {notebook_id}",
                subject="Gate 2 test subject",
                curriculum_id=curriculum_id,
            )
        )
        previous_subject, previous_curriculum_id = None, None
    else:
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
                expected_subject or "Unmapped test subject",
                curriculum_id,
                notebook_id,
            ),
        )

    from study_engine.web.routes import chat as chat_route

    assembled_scopes = []

    def assemble_test_context(**kwargs):
        assembled_scopes.append(kwargs["target_notebook_id"])
        return (
            chat_route.EpistemicContextPack(
                formatted_context="[E1] El concepto está respaldado por material de prueba.",
                citations=["[E1] Material curricular de prueba, pág. 1"],
                chunks=evidence,
            ),
            evidence,
        )

    evidence = [
        {
            "id": "E1",
            "chunk_text": "El concepto está respaldado por material de prueba.",
            "source_id": "src_gate2_test",
            "source_title": "Material curricular de prueba",
            "page_start": 1,
            "score": 0.95,
        }
    ]
    monkeypatch.setattr(
        chat_route,
        "_assemble_epistemic_context",
        assemble_test_context,
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
                "prompt": "¿Qué significa este concepto?",
                "scope_type": "notebook",
                "scope_id": notebook_id,
                "requested_phase": "conceptual",
                "session_id": f"validated-curriculum-profile-{notebook_id}",
            },
        )
    finally:
        if created_notebook:
            store.delete_notebook(notebook_id)
        else:
            with store.engine.transaction() as conn:
                conn.execute(
                    "UPDATE notebooks SET subject = ?, curriculum_id = ? WHERE id = ?",
                    (previous_subject, previous_curriculum_id, notebook_id),
                )

    assert response.status_code == 200
    assert backend.calls
    assert assembled_scopes == [notebook_id]
    system_prompt = backend.calls[0]["system_prompt"]
    assert "x86-64" not in system_prompt
    if expected_subject is None:
        assert "PERFIL CURRICULAR VALIDADO" not in system_prompt
    else:
        assert f"Materia: {expected_subject}" in system_prompt
        assert f"curriculum_id: {curriculum_id}" in system_prompt
        assert expected_guidance in system_prompt
        for other_profile in (
            "Programación y Pensamiento Algorítmico",
            "Lenguajes de Programación",
            "Sistemas Operativos II",
            "Sistema de Tratamiento de Datos",
            "Infraestructura de Telecomunicaciones",
        ):
            if other_profile != expected_subject:
                assert other_profile not in system_prompt


def test_chat_sse_preserves_custom_contract_and_explicit_turn_request(
    client_with_setup, monkeypatch
):
    client, container, _, _ = client_with_setup
    store = container.knowledge_store
    notebook_id = "fadena-std"
    had_custom_contract = store.contains_pedagogical_contract(notebook_id)
    previous_contract = (
        store.get_pedagogical_contract(notebook_id) if had_custom_contract else None
    )
    custom_contract = PedagogicalContract(
        notebook_id=notebook_id,
        base_system_prompt="CUSTOM GATE2 CONTRACT: preserve this exact tutoring policy.",
        response_phases=[
            ResponsePhase(
                phase_id="conceptual",
                phase_prompt_template="Answer the requested concept: {user_query}",
                max_tokens=600,
            )
        ],
    )
    store.save_pedagogical_contract(custom_contract)

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
                    "context": context,
                }
            )
            yield "Respuesta de prueba [E1]."

    backend = CapturingBackend()
    from study_engine.web.routes import chat as chat_route

    evidence = [
        {
            "id": "E1",
            "chunk_text": "Evidencia de prueba para el turno.",
            "source_id": "src_gate2_custom_test",
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
                formatted_context="[E1] Evidencia de prueba para el turno.",
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
                "prompt": "Explicá el modelo relacional en una frase y sin código.",
                "scope_type": "notebook",
                "scope_id": notebook_id,
                "requested_phase": "conceptual",
                "session_id": "gate2-custom-contract-precedence",
            },
        )
    finally:
        if had_custom_contract:
            store.save_pedagogical_contract(previous_contract)
        else:
            store.delete_pedagogical_contract(notebook_id)

    assert response.status_code == 200
    assert backend.calls
    system_prompt = backend.calls[0]["system_prompt"]
    assert "CUSTOM GATE2 CONTRACT" in system_prompt
    assert "PERFIL CURRICULAR VALIDADO" not in system_prompt
    assert "en una frase y sin código" in backend.calls[0]["user_prompt"]


def test_chat_sse_retrieves_only_sources_authorized_for_notebook_scope(
    client_with_setup, monkeypatch
):
    client, container, _, _ = client_with_setup
    store = container.knowledge_store
    target_notebook_id = "fadena-std"
    fixture_id = uuid4().hex
    foreign_notebook_id = f"gate2-acl-foreign-{fixture_id}"
    target_source_id = f"src_gate2_acl_target_{fixture_id}"
    foreign_source_id = f"src_gate2_acl_foreign_{fixture_id}"
    target_document_id = f"doc_gate2_acl_target_{fixture_id}"
    foreign_document_id = f"doc_gate2_acl_foreign_{fixture_id}"
    notebook_created = not store.contains_notebook(target_notebook_id)
    foreign_notebook_created = False
    notebook_identity = None
    target_source_saved = False
    foreign_source_saved = False
    had_custom_contract = store.contains_pedagogical_contract(target_notebook_id)
    previous_contract = (
        store.get_pedagogical_contract(target_notebook_id)
        if had_custom_contract
        else None
    )

    if notebook_created:
        store.create_notebook(
            Notebook(
                id=target_notebook_id,
                name="Gate 2 temporary data notebook",
                subject="Sistema de Tratamiento de Datos",
                curriculum_id="fadena_std_2026",
            )
        )
    else:
        target_notebook = store.get_notebook(target_notebook_id)
        notebook_identity = (target_notebook.subject, target_notebook.curriculum_id)

    target_subject = "Sistema de Tratamiento de Datos"
    target_curriculum_id = "fadena_std_2026"
    assert not store.sources.contains(target_source_id)
    assert not store.sources.contains(foreign_source_id)
    with store.engine.transaction() as conn:
        conn.execute(
            "UPDATE notebooks SET subject = ?, curriculum_id = ? WHERE id = ?",
            (target_subject, target_curriculum_id, target_notebook_id),
        )

    if not store.contains_notebook(foreign_notebook_id):
        store.create_notebook(
            Notebook(
                id=foreign_notebook_id,
                name="Gate 2 foreign scope",
            )
        )
        foreign_notebook_created = True

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
                    "context": context,
                }
            )
            yield "El marcador gate2aclmarker identifica el registro autorizado [E1]."

    backend = CapturingBackend()
    from study_engine.web.routes import chat as chat_route

    try:
        if had_custom_contract:
            store.delete_pedagogical_contract(target_notebook_id)

        for source_id, document_id, content in (
            (
                target_source_id,
                target_document_id,
                "El marcador gate2aclmarker identifica el registro de datos autorizado TARGET_ONLY.",
            ),
            (
                foreign_source_id,
                foreign_document_id,
                "El marcador gate2aclmarker contiene información no autorizada FOREIGN_SECRET.",
            ),
        ):
            store.sources.save(
                SourceRecord(
                    source_id=source_id,
                    manifest=SourceManifest(
                        source_id=source_id,
                        filename=f"{source_id}.txt",
                        byte_size=len(content.encode("utf-8")),
                        sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                        file_path=None,
                        media_type="text/plain",
                    ),
                )
            )
            if source_id == target_source_id:
                target_source_saved = True
                store.link_source_to_notebook(target_notebook_id, source_id)
            else:
                foreign_source_saved = True
                store.link_source_to_notebook(foreign_notebook_id, source_id)
            store.documents.save(
                Document(
                    id=document_id,
                    source_id=source_id,
                    title=f"Gate 2 fixture {source_id}",
                    content=content,
                )
            )
            store.chunks.save_chunks(
                [
                    Chunk(
                        id=f"chunk_{source_id}",
                        document_id=document_id,
                        source_id=source_id,
                        content=content,
                        page_start=1,
                        page_end=1,
                    )
                ]
            )

        monkeypatch.setattr(
            chat_route,
            "_resolve_chat_backend",
            lambda *_args, **_kwargs: backend,
        )
        response = client.post(
            "/api/chat/query",
            json={
                "prompt": "¿Qué indica el marcador gate2aclmarker?",
                "scope_type": "notebook",
                "scope_id": target_notebook_id,
                "active_sources": [target_source_id, foreign_source_id],
                "requested_phase": "conceptual",
                "session_id": f"gate2-real-source-allowlist-{fixture_id}",
            },
        )
    finally:
        if target_source_saved:
            store.unlink_source_from_notebook(target_notebook_id, target_source_id)
            store.delete_source(target_source_id)
        if foreign_source_saved:
            store.unlink_source_from_notebook(foreign_notebook_id, foreign_source_id)
            store.delete_source(foreign_source_id)
        if foreign_notebook_created:
            store.delete_notebook(foreign_notebook_id)
        if notebook_created:
            store.delete_notebook(target_notebook_id)
        else:
            with store.engine.transaction() as conn:
                conn.execute(
                    "UPDATE notebooks SET subject = ?, curriculum_id = ? WHERE id = ?",
                    (*notebook_identity, target_notebook_id),
                )
            if previous_contract is not None:
                store.save_pedagogical_contract(previous_contract)

    assert response.status_code == 200
    assert backend.calls
    captured_prompt = backend.calls[0]["user_prompt"]
    assert "TARGET_ONLY" in captured_prompt
    assert "FOREIGN_SECRET" not in captured_prompt
    assert target_source_id in captured_prompt
    assert foreign_source_id not in captured_prompt
    assert (
        "Materia: Sistema de Tratamiento de Datos" in backend.calls[0]["system_prompt"]
    )

    events = [
        json.loads(line[6:])
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    complete_events = [
        event for event in events if event["event_type"] == "phase_complete"
    ]
    assert complete_events
    provenance = complete_events[-1]["payload"]["evidence_provenance"]
    assert provenance
    assert {item["source_id"] for item in provenance} == {target_source_id}


def test_fadena_std_real_corpus_isolation_on_temporary_database_copy(
    tmp_path, monkeypatch, knowledge_store_test_copy
):
    """Exercise actual fadena-std ACL, retrieval, provenance and SSE on a DB copy."""
    from study_engine.web import dependencies as dependencies_module
    import shutil

    copied_db = tmp_path / "knowledge_store.db"
    shutil.copy2(knowledge_store_test_copy, copied_db)

    with sqlite3.connect(copied_db) as copy_conn:
        assert copy_conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert (
            copy_conn.execute(
                "SELECT COUNT(*) FROM notebook_sources WHERE notebook_id = ?",
                ("fadena-std",),
            ).fetchone()[0]
            == 30
        )

    monkeypatch.setattr(AppContainer, "_seed_curriculum_tree", lambda *_args: None)
    app = create_app()
    container = AppContainer(
        repo_root=Path.cwd(),
        working_dir=tmp_path,
        use_mock=True,
    )
    monkeypatch.setattr(dependencies_module, "_container", container)
    store = container.knowledge_store
    assert store.engine.db_path.resolve() == copied_db.resolve()

    target_notebook_id = "fadena-std"
    target_source_id = "src_fadena_std_unidad1"
    foreign_notebook_id = "fadena-lenguajes"
    foreign_source_id = "src_fadena_leng_clase2"
    target_sources = {
        source.source_id for source in store.list_notebook_sources(target_notebook_id)
    }
    foreign_sources = {
        source.source_id for source in store.list_notebook_sources(foreign_notebook_id)
    }
    assert target_source_id in target_sources
    assert foreign_source_id in foreign_sources
    assert foreign_source_id not in target_sources

    with store.engine.transaction() as conn:
        notebook_before = conn.execute(
            "SELECT curriculum_id FROM notebooks WHERE id = ?",
            (target_notebook_id,),
        ).fetchone()[0]
        associations_before = conn.execute(
            "SELECT source_id FROM notebook_sources WHERE notebook_id = ? ORDER BY source_id",
            (target_notebook_id,),
        ).fetchall()
        contracts_before = conn.execute(
            "SELECT COUNT(*) FROM pedagogical_contracts WHERE notebook_id = ?",
            (target_notebook_id,),
        ).fetchone()[0]

    assert notebook_before == "fadena_v1"
    assert contracts_before == 0

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
                    "context": context,
                }
            )
            yield "Un dato adquiere significado al organizarse como información [E1]."

    backend = CapturingBackend()
    from study_engine.web.routes import chat as chat_route

    search_calls = []
    original_search_hybrid = store.search_hybrid

    def observe_search_hybrid(*args, **kwargs):
        if kwargs.get("notebook_id") == target_notebook_id:
            search_calls.append(
                {
                    "notebook_id": kwargs["notebook_id"],
                    "source_ids": set(kwargs.get("source_ids") or []),
                }
            )
        return original_search_hybrid(*args, **kwargs)

    monkeypatch.setattr(store, "search_hybrid", observe_search_hybrid)
    monkeypatch.setattr(
        chat_route,
        "_resolve_chat_backend",
        lambda *_args, **_kwargs: backend,
    )

    client = TestClient(app)
    response = client.post(
        "/api/chat/query",
        json={
            "prompt": "¿Qué diferencia hay entre dato, información y conocimiento?",
            "scope_type": "notebook",
            "scope_id": target_notebook_id,
            "active_sources": [target_source_id, foreign_source_id],
            "requested_phase": "conceptual",
            "session_id": "gate2-fadena-std-real-copy",
        },
    )

    assert response.status_code == 200
    assert search_calls
    assert all(call["notebook_id"] == target_notebook_id for call in search_calls)
    assert all(target_source_id in call["source_ids"] for call in search_calls)
    assert all(foreign_source_id not in call["source_ids"] for call in search_calls)

    assert backend.calls
    backend_call = backend.calls[0]
    assert "Dato, Información y Conocimiento" in backend_call["user_prompt"]
    assert foreign_source_id not in backend_call["user_prompt"]
    assert "FOREIGN_SECRET" not in backend_call["user_prompt"]
    # The copied DB still has the unapproved generic identity; the current
    # fallback must remain neutral rather than silently activating a profile.
    assert "PERFIL CURRICULAR VALIDADO" not in backend_call["system_prompt"]

    events = [
        json.loads(line[6:])
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert any(event["event_type"] == "phase_complete" for event in events)
    complete = next(
        event for event in events if event["event_type"] == "phase_complete"
    )
    provenance = complete["payload"]["evidence_provenance"]
    assert provenance
    assert {item["source_id"] for item in provenance} == {target_source_id}
    assert all(item["citation_id"] for item in provenance)
    assert all(item["doc_hash"] for item in provenance)

    with store.engine.transaction() as conn:
        notebook_after = conn.execute(
            "SELECT curriculum_id FROM notebooks WHERE id = ?",
            (target_notebook_id,),
        ).fetchone()[0]
        associations_after = conn.execute(
            "SELECT source_id FROM notebook_sources WHERE notebook_id = ? ORDER BY source_id",
            (target_notebook_id,),
        ).fetchall()
    assert notebook_after == notebook_before
    assert associations_after == associations_before
