"""Unit tests for LLMRequest and LLMResponse contracts."""

import pytest
from pydantic import ValidationError

from study_engine.contracts.llm import LLMRequest, LLMResponse


def test_llm_request_valid_minimal():
    req = LLMRequest(request_id="req-001")
    assert req.request_id == "req-001"
    assert req.mode == "tutor"
    assert req.temperature == 0.7
    assert req.messages == []


def test_llm_request_valid_full():
    req = LLMRequest(
        request_id="req-002",
        mode="tester",
        system_prompt="Eres el módulo Tester del Study Engine.",
        messages=[{"role": "user", "content": "Genera una pregunta sobre punteros en C."}],
        context="Capítulo 7 Joyanes - Punteros y Gestión Dinámica de Memoria",
        temperature=0.2,
        max_tokens=500,
        stop_sequences=["### END"],
        model="gpt-oss-120b",
        provider="groq",
        metadata={"session_id": "sess-123"},
    )
    assert req.mode == "tester"
    assert req.provider == "groq"
    assert len(req.messages) == 1
    assert req.stop_sequences == ["### END"]


def test_llm_request_invalid_temperature():
    with pytest.raises(ValidationError):
        LLMRequest(request_id="req-1", temperature=-0.5)

    with pytest.raises(ValidationError):
        LLMRequest(request_id="req-1", temperature=2.5)


def test_llm_response_valid():
    res = LLMResponse(
        request_id="req-002",
        content="¿Cuál es la diferencia entre un puntero nulo y un puntero desreferenciado?",
        mode="tester",
        model="gpt-oss-120b",
        provider="groq",
        tokens_used={"prompt": 45, "completion": 22, "total": 67},
        finish_reason="stop",
        latency_ms=185.4,
        metadata={"temperature": 0.2},
    )
    assert res.request_id == "req-002"
    assert res.latency_ms == 185.4
    assert res.tokens_used["total"] == 67


def test_llm_response_missing_required():
    with pytest.raises(ValidationError):
        LLMResponse(request_id="req-1")  # missing content

    with pytest.raises(ValidationError):
        LLMResponse(content="Response content")  # missing request_id
