"""Tests for DataSanitizer pre-flight PII & Credential guard (Ola 5, Fase 5.1)."""

import json
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from study_engine.security.classification import DataClassification, is_cloud_allowed
from study_engine.security.data_sanitizer import DataSanitizer
from study_engine.web.app import create_app
from study_engine.web.dependencies import get_container


def test_detects_openai_key() -> None:
    sanitizer = DataSanitizer()
    prompt = "Che, mi key es sk-abcdef123456789012345678 como la configuro?"
    res = sanitizer.scrub(prompt)
    assert res.has_pii is True
    assert "OPENAI_API_KEY" in res.detected_patterns


def test_detects_github_token() -> None:
    sanitizer = DataSanitizer()
    prompt = "Tengo este token ghp_123456789012345678901234567890123456 para el repo"
    res = sanitizer.scrub(prompt)
    assert res.has_pii is True
    assert "GITHUB_PERSONAL_TOKEN" in res.detected_patterns


def test_detects_aws_key() -> None:
    sanitizer = DataSanitizer()
    prompt = "Uso la key AKIAIOSFODNN7EXAMPLE para s3"
    res = sanitizer.scrub(prompt)
    assert res.has_pii is True
    assert "AWS_ACCESS_KEY" in res.detected_patterns


def test_detects_email() -> None:
    sanitizer = DataSanitizer()
    prompt = "Escribime a profesor.alumno@fadena.edu.ar para coordinar"
    res = sanitizer.scrub(prompt)
    assert res.has_pii is True
    assert "EMAIL_ADDRESS" in res.detected_patterns


def test_detects_dni_punteado() -> None:
    sanitizer = DataSanitizer()
    prompt = "Mi documento es 34.567.890 para el examen"
    res = sanitizer.scrub(prompt)
    assert res.has_pii is True
    assert "DNI_PUNTEADO" in res.detected_patterns


def test_technical_number_passes() -> None:
    sanitizer = DataSanitizer()
    prompt = "Asigno un buffer de 10000000 bytes para procesar el stream de audio a 44100 hz"
    res = sanitizer.scrub(prompt)
    assert res.has_pii is False
    assert len(res.detected_patterns) == 0


def test_hex_address_passes() -> None:
    sanitizer = DataSanitizer()
    prompt = "El puntero base apunta a 0x7fff5fbff8 y el offset es de 4 bytes"
    res = sanitizer.scrub(prompt)
    assert res.has_pii is False
    assert len(res.detected_patterns) == 0


def test_empty_prompt_passes() -> None:
    sanitizer = DataSanitizer()
    res = sanitizer.scrub("")
    assert res.has_pii is False
    assert len(res.detected_patterns) == 0


def test_pii_blocks_request_in_chat_query() -> None:
    """Verify in integration that passing an API key in /api/chat/query blocks external LLM call."""
    app = create_app()
    container = get_container()

    mock_llm = MagicMock()
    container.llm_backend = mock_llm
    client = TestClient(app)

    response = client.post(
        "/api/chat/query",
        json={
            "prompt": "Che, cómo uso sk-abcdef123456789012345678 con python?",
            "scope_type": "notebook",
            "scope_id": "fadena-lenguajes",
        },
    )
    assert response.status_code == 200
    lines = [l.strip() for l in response.text.split("\n") if l.startswith("data: ")]
    events = [json.loads(l[6:]) for l in lines]
    event_types = [e["event_type"] for e in events]

    assert "evidence_manifest" in event_types
    assert "phase_start" in event_types
    assert "phase_complete" in event_types

    # Invariant: Completed phase is pii_guard with status BLOCKED_PII
    comp = [e for e in events if e["event_type"] == "phase_complete"][0]
    assert comp["payload"]["completed_phase"] == "pii_guard"
    assert comp["payload"]["status"] == "BLOCKED_PII"

    # Invariant: External LLM was NEVER called
    assert mock_llm.complete.call_count == 0


def test_data_classification_cloud_allowed() -> None:
    assert is_cloud_allowed(DataClassification.PUBLIC_EDUCATIONAL) is True
    assert is_cloud_allowed(DataClassification.ACCIDENTAL_PII) is False
    assert is_cloud_allowed(DataClassification.STUDENT_PRIVATE) is False
