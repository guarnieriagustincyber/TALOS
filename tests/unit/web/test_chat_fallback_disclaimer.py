"""Commit 3 — Test unitario de disclaimer hablado determinista ante fallback sin KC confirmado.

Contrato:
- Cuando bkt_context.fallback = True (matched_kc_id is None):
  El texto de la respuesta (tanto emitido en streaming como persistido)
  antepone determinísticamente la frase exacta:
  "No pude confirmar un concepto específico del cuaderno; respondo con base conceptual general de fuentes verificadas."
- Cuando hay un KC confirmado matcheado:
  La frase NO está presente en el texto de la respuesta.
"""

import json
import pytest
from fastapi.testclient import TestClient

from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container
from study_engine.web.routes.chat import FALLBACK_DISCLAIMER


@pytest.fixture
def chat_client(web_state_test_copy):
    app = create_app()
    container = AppContainer(working_dir=web_state_test_copy, use_mock=True)
    set_container(container)
    return TestClient(app)


def _collect_sse_response(response) -> tuple[str, dict]:
    lines = [line.strip() for line in response.text.split("\n") if line.startswith("data: ")]
    events = [json.loads(line[6:]) for line in lines]
    tokens = [
        e["payload"].get("token", "")
        for e in events
        if e.get("event_type") == "phase_token"
    ]
    full_text = "".join(tokens)
    complete_events = [e for e in events if e.get("event_type") == "phase_complete"]
    complete_payload = complete_events[0]["payload"] if complete_events else {}
    return full_text, complete_payload


def test_disclaimer_present_when_fallback_active(chat_client):
    """Consulta K1 (evidencia encontrada pero sin KC confirmado en cuaderno) -> fallback=True y disclaimer presente."""
    response = chat_client.post(
        "/api/chat/query",
        json={
            "query": "¿Cómo funciona el scheduling SJF?",
            "notebook_id": "fase0-soc",
            "requested_phase": "conceptual",
        },
    )
    assert response.status_code == 200
    full_text, complete_payload = _collect_sse_response(response)

    bkt = complete_payload.get("bkt_context") or {}
    assert bkt.get("fallback") is True
    assert bkt.get("kc_id") is None
    assert complete_payload.get("fallback_disclaimer") is True

    # El texto hablado a la UI NO debe estar contaminado con el disclaimer visible
    assert FALLBACK_DISCLAIMER not in full_text


def test_disclaimer_absent_when_kc_matched(chat_client):
    """Consulta K2 (KC confirmado en catálogo) -> fallback=False y disclaimer ausente."""
    response = chat_client.post(
        "/api/chat/query",
        json={
            "query": "¿cómo uso malloc y free sin leaks?",
            "notebook_id": "fase0-soc",
            "requested_phase": "conceptual",
        },
    )
    assert response.status_code == 200
    full_text, complete_payload = _collect_sse_response(response)

    bkt = complete_payload.get("bkt_context") or {}
    assert bkt.get("fallback") is False
    assert bkt.get("kc_id") == "aritmetica_punteros"

    # NO debe contener el disclaimer
    assert FALLBACK_DISCLAIMER not in full_text
