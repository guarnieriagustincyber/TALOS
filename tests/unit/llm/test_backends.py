"""Unit tests for ProviderBackend implementations in Subsystem S4.3."""

import json
import httpx

from study_engine.contracts.generation import (
    GenerationParameters,
    TokenUsage,
)
from study_engine.generation.prompts import (
    PromptBundle,
    PromptMessage,
    PromptRole,
)
from study_engine.llm.backends import (
    HttpOpenAIBackend,
    MockBackend,
    RuleBasedBackend,
)


def _make_bundle(query: str = "¿Qué es memoria virtual?") -> PromptBundle:
    """Helper to build PromptBundle for backend testing."""
    msg = PromptMessage(role=PromptRole.USER, content=query)
    return PromptBundle(
        system_prompt="System policy",
        messages=(msg,),
        parameters=GenerationParameters(
            temperature=0.2,
            max_output_tokens=250,
            suggested_model="test-model-v1",
        ),
        prompt_hash="b" * 64,
    )


def test_mock_backend_default_behavior():
    """Verify MockBackend default completion references [E1]."""
    backend = MockBackend()
    bundle = _make_bundle()
    comp = backend.complete(bundle)

    assert "[E1]" in comp.text
    assert comp.generator_abstained is False
    assert comp.model == "mock-llm-v1"


def test_mock_backend_canned_abstained():
    """Verify MockBackend respects canned abstention flag."""
    backend = MockBackend(
        canned_text="No puedo responder por falta de evidencia.",
        canned_abstained=True,
    )
    bundle = _make_bundle()
    comp = backend.complete(bundle)

    assert comp.generator_abstained is True
    assert "No puedo responder" in comp.text


def test_rule_based_backend_completion():
    """Verify RuleBasedBackend produces deterministic slot-filled answer."""
    backend = RuleBasedBackend(model_name="rule-v2")
    bundle = _make_bundle(query="Explica paginación")
    comp = backend.complete(bundle)

    assert "Explica paginación" in comp.text
    assert "[E1]" in comp.text
    assert comp.model == "rule-v2"
    assert comp.tokens_used is None


def test_http_backend_success_with_mock_transport():
    """Verify HttpOpenAIBackend handles 200 OK OpenAI-compatible response."""
    captured_requests = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        body = json.loads(request.content.decode("utf-8"))
        assert body["model"] == "test-model-v1"
        assert len(body["messages"]) == 2  # 1 system + 1 user message

        response_payload = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "model": "test-model-v1",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": (
                            "La memoria virtual mapea direcciones [E1]."
                        ),
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 42,
                "completion_tokens": 15,
                "total_tokens": 57,
            },
        }
        return httpx.Response(200, json=response_payload)

    client = httpx.Client(transport=httpx.MockTransport(mock_handler))
    backend = HttpOpenAIBackend(
        base_url="http://mock-llm.local",
        api_key="sk-test-secret-key",
        client=client,
    )

    bundle = _make_bundle()
    comp = backend.complete(bundle)

    assert comp.text == "La memoria virtual mapea direcciones [E1]."
    assert comp.model == "test-model-v1"
    assert comp.tokens_used == TokenUsage(
        prompt_tokens=42, completion_tokens=15, total_tokens=57
    )
    assert comp.latency_ms >= 0.0

    # Verify authorization header
    assert len(captured_requests) == 1
    req = captured_requests[0]
    assert req.headers["Authorization"] == "Bearer sk-test-secret-key"


def test_http_backend_context_boundary():
    """Verify HG-S4.3-09: Payload receives exclusively PromptBundle data."""

    recorded_payloads = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        recorded_payloads.append(json.loads(request.content.decode("utf-8")))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Respuesta válida [E1].",
                        }
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(mock_handler))
    backend = HttpOpenAIBackend(client=client)
    bundle = _make_bundle()

    backend.complete(bundle)

    assert len(recorded_payloads) == 1
    payload = recorded_payloads[0]

    # Only OpenAI-compatible schema fields allowed
    allowed_keys = {"model", "messages", "temperature", "max_tokens"}
    assert set(payload.keys()).issubset(
        allowed_keys.union({"stop", "seed"})
    )


def test_http_backend_missing_usage_telemetry():
    """Verify unprovided usage telemetry leaves tokens_used as None."""
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Respuesta sin telemetría de tokens.",
                        }
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(mock_handler))
    backend = HttpOpenAIBackend(client=client)
    bundle = _make_bundle()

    comp = backend.complete(bundle)
    assert comp.tokens_used is None


def test_http_backend_with_stop_and_seed():
    """Verify stop sequences and seed are forwarded in request payload."""
    captured = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content.decode("utf-8")))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Con parada [E1].",
                        }
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(mock_handler))
    backend = HttpOpenAIBackend(client=client)

    msg = PromptMessage(role=PromptRole.USER, content="Query")
    bundle = PromptBundle(
        system_prompt="Sys",
        messages=(msg,),
        parameters=GenerationParameters(
            stop_sequences=("STOP",),
            seed=42,
        ),
        prompt_hash="d" * 64,
    )
    backend.complete(bundle)

    assert len(captured) == 1
    assert captured[0]["stop"] == ["STOP"]
    assert captured[0]["seed"] == 42


def test_http_backend_non_200_raises_backend_error():
    """Verify HTTP 500 error raises LLMBackendError."""
    import pytest
    from study_engine.llm.exceptions import LLMBackendError

    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    client = httpx.Client(transport=httpx.MockTransport(mock_handler))
    backend = HttpOpenAIBackend(client=client)
    bundle = _make_bundle()

    with pytest.raises(LLMBackendError) as exc_info:
        backend.complete(bundle)
    assert "Backend HTTP 500" in str(exc_info.value)
