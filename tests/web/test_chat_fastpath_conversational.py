"""Unit and integration tests for Fast-Path Conversational Gatekeeper (Fase 1)."""

from datetime import datetime, timezone
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from study_engine.contracts.notebook import Notebook
from study_engine.hierarchy.folder import Folder
from study_engine.tutor.fastpath_service import FastPathConversationalService
from study_engine.tutor.policy_validator import RouteKind
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


class TestFastPathDetector:
    """Unit tests for the conversational route detection logic."""

    def test_greetings_detected(self):
        samples = [
            "hola",
            "HOLA",
            "Hola!",
            "buenas",
            "buen día",
            "buenas tardes",
            "buenas noches",
            "hey talos",
            "hola kasiu",
            "saludos",
            "qué tal?",
            "cómo estás?",
            "gracias!",
            "muchas gracias",
            "chau",
            "adiós",
        ]
        for s in samples:
            is_conv, route = FastPathConversationalService.detect_conversational_route(s)
            assert is_conv is True, f"Expected '{s}' to be detected as conversational"
            assert route == RouteKind.GREETING, f"Expected GREETING for '{s}', got {route}"

    def test_navigation_detected(self):
        samples = [
            "por dónde empezamos",
            "por dónde seguimos?",
            "qué tema sigue",
            "en qué tema quedamos",
            "cuál es el próximo paso",
            "siguiente paso",
            "qué vemos hoy?",
            "mostrame el roadmap",
        ]
        for s in samples:
            is_conv, route = FastPathConversationalService.detect_conversational_route(s)
            assert is_conv is True, f"Expected '{s}' to be detected as conversational"
            assert route == RouteKind.NAVIGATION, f"Expected NAVIGATION for '{s}', got {route}"

    def test_meta_detected(self):
        samples = [
            "quién sos",
            "quién eres?",
            "cómo funcionas",
            "qué podés hacer",
            "para qué servís?",
        ]
        for s in samples:
            is_conv, route = FastPathConversationalService.detect_conversational_route(s)
            assert is_conv is True, f"Expected '{s}' to be detected as conversational"
            assert route == RouteKind.CLARIFICATION, f"Expected CLARIFICATION for '{s}', got {route}"

    def test_followup_affirmations_detected(self):
        samples = [
            "dale",
            "DALE",
            "dale!",
            "de una",
            "de una!",
            "sí",
            "si",
            "si!",
            "sip",
            "se",
            "ok",
            "okay",
            "bueno",
            "joya",
            "buenísimo",
            "clarísimo",
            "de diez",
            "totalmente",
            "de acuerdo",
            "dale con eso",
            "vamos",
            "sigamos",
            "continúa",
            "continuemos",
            "avancemos",
            "next",
            "perfecto",
            "entendido",
            "si dale",
            "dale dale",
        ]
        for s in samples:
            is_conv, route = FastPathConversationalService.detect_conversational_route(s)
            assert is_conv is True, f"Expected '{s}' to be detected as conversational follow-up"
            assert route == RouteKind.FOLLOW_UP, f"Expected FOLLOW_UP for '{s}', got {route}"

    def test_followup_negations_detected(self):
        samples = [
            "no",
            "NO",
            "no!",
            "nop",
            "nope",
            "nel",
            "paso",
            "por ahora no",
            "después",
            "dejemos acá",
            "terminamos por hoy",
            "hasta acá por hoy",
            "no gracias",
            "hoy no",
        ]
        for s in samples:
            is_conv, route = FastPathConversationalService.detect_conversational_route(s)
            assert is_conv is True, f"Expected '{s}' to be detected as conversational follow-up"
            assert route == RouteKind.FOLLOW_UP, f"Expected FOLLOW_UP for '{s}', got {route}"

    def test_technical_questions_disqualified(self):
        technical_samples = [
            "¿Qué es la memoria dinámica?",
            "explicame qué es un puntero",
            "por qué la memoria se corrompe en un buffer overflow?",
            "cómo funciona el stack y el heap?",
            "hola, qué es la memoria dinámica?",
            "hola, explicame un buffer overflow",
            "dame un ejercicio de punteros",
            "qué significa el registro rbp?",
            "dale, explicame qué es la memoria",
            "sí, qué es un puntero?",
            "ok, dame un ejercicio de cpu",
        ]
        for s in technical_samples:
            is_conv, route = FastPathConversationalService.detect_conversational_route(s)
            assert is_conv is False, f"Expected technical query '{s}' NOT to be intercepted"
            assert route is None


@pytest.fixture(scope="module")
def client_with_fastpath(tmp_path_factory, knowledge_store_test_copy):
    tmp_dir = tmp_path_factory.mktemp("chat_fastpath_test")
    if knowledge_store_test_copy is not None:
        import shutil
        shutil.copy2(knowledge_store_test_copy, tmp_dir / "knowledge_store.db")

    app = create_app()
    container = AppContainer(working_dir=tmp_dir, use_mock=True)
    set_container(container)
    store = container.knowledge_store

    now = datetime.now(timezone.utc)
    if not store.contains_folder("f_test"):
        store.create_folder(
            Folder(
                id="f_test",
                name="Carpeta Test",
                parent_folder_id="folder_root",
                created_at=now,
                updated_at=now,
            )
        )

    if not store.contains_notebook("nb_test_fastpath"):
        store.create_notebook(
            Notebook(id="nb_test_fastpath", name="Arquitectura y Sistemas", folder_id="f_test")
        )

    client = TestClient(app)
    return client, container


class TestChatFastPathIntegration:
    """Integration tests for POST /api/chat/query FastPath interception."""

    def test_notebook_greeting_fastpath_stream(self, client_with_fastpath):
        """Pure greeting in notebook scope triggers conversational phase with zero abstention."""
        client, container = client_with_fastpath

        response = client.post(
            "/api/chat/query",
            json={
                "prompt": "¡Hola!",
                "scope_type": "notebook",
                "scope_id": "nb_test_fastpath",
            },
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        lines = [line.strip() for line in response.text.split("\n") if line.startswith("data: ")]
        assert len(lines) > 0

        events = [json.loads(line[6:]) for line in lines]
        event_types = [e["event_type"] for e in events]

        assert "evidence_manifest" in event_types
        assert "phase_start" in event_types
        assert "phase_token" in event_types
        assert "phase_complete" in event_types

        # Verify evidence_manifest indicates NOT abstained
        manifest = [e for e in events if e["event_type"] == "evidence_manifest"][0]
        assert manifest["payload"]["abstained"] is False
        assert manifest["payload"]["citations"] == []

        # Verify phase is conversational
        start_ev = [e for e in events if e["event_type"] == "phase_start"][0]
        assert start_ev["payload"]["phase"] == "conversational"

        complete_ev = [e for e in events if e["event_type"] == "phase_complete"][0]
        assert complete_ev["payload"]["completed_phase"] == "conversational"
        assert complete_ev["payload"]["decision"]["action"] == "conversational_reply"

    def test_notebook_navigation_fastpath_stream(self, client_with_fastpath):
        """Navigation query in notebook scope returns conversational advice with notebook context."""
        client, container = client_with_fastpath

        response = client.post(
            "/api/chat/query",
            json={
                "prompt": "¿Por dónde empezamos?",
                "scope_type": "notebook",
                "scope_id": "nb_test_fastpath",
            },
        )
        assert response.status_code == 200
        lines = [line.strip() for line in response.text.split("\n") if line.startswith("data: ")]
        events = [json.loads(line[6:]) for line in lines]

        complete_ev = [e for e in events if e["event_type"] == "phase_complete"][0]
        assert complete_ev["payload"]["completed_phase"] == "conversational"
        assert complete_ev["payload"]["decision"]["route_kind"] == "navigation"
        assert "nb_test_fastpath" in complete_ev["payload"]["decision"]["message"] or "Arquitectura" in complete_ev["payload"]["decision"]["message"]

    def test_nonexistent_notebook_still_returns_404(self, client_with_fastpath):
        """Even for greeting, non-existent scope must return 404."""
        client, container = client_with_fastpath

        response = client.post(
            "/api/chat/query",
            json={
                "prompt": "Hola",
                "scope_type": "notebook",
                "scope_id": "nonexistent_notebook_999",
            },
        )
        assert response.status_code == 404

    def test_notebook_followup_affirmation_fastpath_stream(self, client_with_fastpath):
        """Follow-up affirmation ('dale') in notebook scope returns instant conversational reply."""
        client, container = client_with_fastpath

        response = client.post(
            "/api/chat/query",
            json={
                "prompt": "dale",
                "scope_type": "notebook",
                "scope_id": "nb_test_fastpath",
            },
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        lines = [line.strip() for line in response.text.split("\n") if line.startswith("data: ")]
        assert len(lines) > 0

        events = [json.loads(line[6:]) for line in lines]
        event_types = [e["event_type"] for e in events]

        assert "evidence_manifest" in event_types
        assert "phase_start" in event_types
        assert "phase_token" in event_types
        assert "phase_complete" in event_types

        manifest = [e for e in events if e["event_type"] == "evidence_manifest"][0]
        assert manifest["payload"]["abstained"] is False

        start_ev = [e for e in events if e["event_type"] == "phase_start"][0]
        assert start_ev["payload"]["phase"] == "conversational"

        complete_ev = [e for e in events if e["event_type"] == "phase_complete"][0]
        assert complete_ev["payload"]["completed_phase"] == "conversational"
        assert complete_ev["payload"]["decision"]["route_kind"] == "follow_up"
        assert complete_ev["payload"]["decision"]["action"] == "conversational_reply"
        message = complete_ev["payload"]["decision"]["message"]
        assert len(message) > 10

    def test_notebook_followup_negation_fastpath_stream(self, client_with_fastpath):
        """Follow-up negation ('por ahora no') in notebook scope returns empathetic conversational pause."""
        client, container = client_with_fastpath

        response = client.post(
            "/api/chat/query",
            json={
                "prompt": "por ahora no",
                "scope_type": "notebook",
                "scope_id": "nb_test_fastpath",
            },
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        lines = [line.strip() for line in response.text.split("\n") if line.startswith("data: ")]
        assert len(lines) > 0

        events = [json.loads(line[6:]) for line in lines]
        complete_ev = [e for e in events if e["event_type"] == "phase_complete"][0]
        assert complete_ev["payload"]["completed_phase"] == "conversational"
        assert complete_ev["payload"]["decision"]["route_kind"] == "follow_up"
        message = complete_ev["payload"]["decision"]["message"]
        assert len(message) > 10
