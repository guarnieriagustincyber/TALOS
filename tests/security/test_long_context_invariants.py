"""Tests for Long Context Invariants and Physical Pre-LLM Abstention Gate (Ola 5, E25, INV-W5-1)."""

import json
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from study_engine.contracts.generation import GenerationParameters, TokenUsage
from study_engine.llm.backends import ProviderCompletion
from study_engine.web.app import create_app
from study_engine.web.dependencies import get_container


def test_physical_pre_llm_abstention_gate_on_zero_chunks() -> None:
    """Verify that when 0 chunks are found in active sources, the cloud LLM is NEVER called (E25, INV-W5-1)."""
    app = create_app()
    container = get_container()

    # Mock the LLM backend to spy on completion calls
    mock_llm = MagicMock()
    mock_llm.complete.return_value = ProviderCompletion(
        text="Respuesta que jamás debería ser generada",
        latency_ms=10.0,
        tokens_used=TokenUsage(prompt_tokens=10, completion_tokens=10, total_tokens=20),
        model="mock-cloud-llm",
        generator_abstained=False,
    )
    container.llm_backend = mock_llm

    client = TestClient(app)

    # 1. Query with query completely out of scope on fadena-lenguajes
    response = client.post(
        "/api/chat/query",
        json={
            "prompt": "fotosintesis cloroplastos tilacoides celula vegetal",
            "scope_type": "notebook",
            "scope_id": "fadena-lenguajes",
            "requested_phase": "conceptual",
        },
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    lines = [l.strip() for l in response.text.split("\n") if l.startswith("data: ")]
    assert len(lines) > 0

    events = [json.loads(l[6:]) for l in lines]
    event_types = [e["event_type"] for e in events]

    # Invariant: Evidence manifest says abstained, followed immediately by abstention event
    assert "evidence_manifest" in event_types
    assert "abstention" in event_types
    assert "phase_start" not in event_types
    assert "phase_token" not in event_types

    # Invariant E25: The LLM backend was NEVER invoked
    assert mock_llm.complete.call_count == 0
    if hasattr(mock_llm, "stream"):
        assert mock_llm.stream.call_count == 0


def test_active_sources_filtering_restricts_retrieval_and_abtains_if_empty() -> None:
    """Verify that active_sources filters the retrieval scope and triggers gate if no hits match (E25)."""
    app = create_app()
    container = get_container()

    mock_llm = MagicMock()
    container.llm_backend = mock_llm
    client = TestClient(app)

    # Query about punteros, but filter active_sources to an unrelated non-existent source
    response = client.post(
        "/api/chat/query",
        json={
            "prompt": "¿Qué es un puntero en lenguaje C?",
            "scope_type": "notebook",
            "scope_id": "fadena-lenguajes",
            "active_sources": ["non_existent_source_id_xyz"],
            "requested_phase": "conceptual",
        },
    )

    assert response.status_code == 200
    lines = [l.strip() for l in response.text.split("\n") if l.startswith("data: ")]
    events = [json.loads(l[6:]) for l in lines]
    event_types = [e["event_type"] for e in events]

    assert "abstention" in event_types
    assert mock_llm.complete.call_count == 0


def test_empty_active_sources_is_an_explicit_empty_allowlist() -> None:
    app = create_app()
    container = get_container()

    mock_llm = MagicMock()
    container.llm_backend = mock_llm
    client = TestClient(app)

    response = client.post(
        "/api/chat/query",
        json={
            "prompt": "¿Qué es un puntero en lenguaje C?",
            "scope_type": "notebook",
            "scope_id": "fadena-lenguajes",
            "active_sources": [],
            "requested_phase": "conceptual",
        },
    )

    assert response.status_code == 200
    events = [
        json.loads(line[6:])
        for line in response.text.split("\n")
        if line.startswith("data: ")
    ]
    event_types = [event["event_type"] for event in events]
    assert "abstention" in event_types
    assert "phase_token" not in event_types
    assert mock_llm.complete.call_count == 0
