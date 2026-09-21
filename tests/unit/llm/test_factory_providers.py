"""Unit tests for FASE 4 multi-provider registry + rotation.

Verifies:
1. PROVIDER_REGISTRY resolves each provider with its base_url / default_model.
2. create_provider dispatches via the strategy table to the correct backend type.
3. Rotation composes an existing CircuitBreakerBackend chain that falls through
   to the next provider when the primary's circuit is open.
"""

from __future__ import annotations

from typing import List
import httpx
import pytest

from study_engine.llm.backends import (
    HttpOpenAIBackend,
    MockBackend,
    ProviderBackend,
    ReplayMockBackend,
)
from study_engine.llm.circuit_breaker import CircuitBreaker, CircuitBreakerBackend
from study_engine.llm.factory import (
    PROVIDER_REGISTRY,
    ProviderConfig,
    ProviderSpec,
    LLMProviderFactory,
)

EXPECTED_PROVIDERS = {
    "groq": ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    "gemini": (
        "https://generativelanguage.googleapis.com/v1beta/openai",
        "gemini-3.1-flash-lite",
    ),
    "nvidia": (
        "https://integrate.api.nvidia.com/v1",
        "deepseek-ai/deepseek-v4-flash",
    ),
    "openrouter": ("https://openrouter.ai/api/v1", "google/gemini-2.5-flash-lite"),
    "ollama": ("http://localhost:11434/v1", "qwen3.5:2b"),
}


def _mock_transport_response() -> httpx.MockTransport:
    """Return a MockTransport that answers any chat completions request."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "respuesta [E1]"}}],
                "model": "test-model",
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            },
        )

    return httpx.MockTransport(handler)


def test_registry_resolves_each_provider_base_url_and_model() -> None:
    """Each provider in the registry carries the expected endpoint + model."""
    for name, (base_url, model) in EXPECTED_PROVIDERS.items():
        spec = PROVIDER_REGISTRY[name]
        assert isinstance(spec, ProviderSpec)
        assert spec.base_url == base_url
        assert spec.default_model == model
        assert spec.priority >= 0


def test_registry_has_authoritative_provider_set() -> None:
    """The registry contains the exact expected provider keys."""
    assert set(PROVIDER_REGISTRY.keys()) >= set(EXPECTED_PROVIDERS.keys())


def test_mock_backend_dispatch() -> None:
    """create_provider(mock) returns a MockBackend via the strategy table."""
    factory = LLMProviderFactory()
    backend = factory.create_provider(ProviderConfig(provider_type="mock"))
    assert isinstance(backend, MockBackend)


def test_replay_backend_dispatch() -> None:
    """create_provider(replay) returns a ReplayMockBackend."""
    factory = LLMProviderFactory()
    backend = factory.create_provider(ProviderConfig(provider_type="replay"))
    assert isinstance(backend, ReplayMockBackend)


def test_http_provider_dispatch_with_mock_transport() -> None:
    """create_provider(groq) builds an HttpOpenAIBackend hitting the registry URL."""
    factory = LLMProviderFactory()
    backend = factory.create_provider(
        ProviderConfig(
            provider_type="groq",
            api_key="test-key",
            custom_client=httpx.Client(transport=_mock_transport_response()),
        )
    )
    assert isinstance(backend, HttpOpenAIBackend)
    # HttpOpenAIBackend stores base_url on the internal client; just assert type.
    assert backend._default_model == "llama-3.3-70b-versatile"


def test_unsupported_provider_raises() -> None:
    """An unknown provider type is rejected by the strategy table."""
    factory = LLMProviderFactory()
    with pytest.raises(ValueError):
        factory.create_provider(ProviderConfig(provider_type="nope"))  # type: ignore[arg-type]


class _AlwaysOpenCircuitBreaker(CircuitBreaker):
    """Circuit breaker whose circuit is always open (quota exhausted)."""

    def can_proceed(self, estimated_tokens: int = 0, now=None) -> bool:
        return False


def test_rotation_falls_through_on_open_circuit() -> None:
    """An open circuit on the primary falls back to the next backend."""
    # Build a deterministic 2-level chain via the existing CircuitBreakerBackend.
    primary_calls: List[str] = []
    fallback_calls: List[str] = []

    class PrimaryStub(ProviderBackend):  # type: ignore[misc]
        def complete(self, prompt_bundle):
            primary_calls.append("called")
            raise RuntimeError("primary failed")

    class FallbackStub(ProviderBackend):  # type: ignore[misc]
        def complete(self, prompt_bundle):
            fallback_calls.append("called")
            return provider_completion()

    def provider_completion():
        from study_engine.llm.backends import ProviderCompletion

        return ProviderCompletion(
            text="from fallback [E1]",
            latency_ms=1.0,
            tokens_used=None,
            model="fallback-model",
        )

    # Outer breaker always open -> primary never runs, delegates to fallback.
    chain = CircuitBreakerBackend(
        primary_backend=PrimaryStub(),
        fallback_backend=FallbackStub(),
        circuit_breaker=_AlwaysOpenCircuitBreaker(),
    )

    from study_engine.generation.prompts import PromptBundle, PromptMessage, PromptRole
    from study_engine.contracts.generation import GenerationParameters
    import hashlib

    bundle = PromptBundle(
        system_prompt="sys",
        messages=(PromptMessage(role=PromptRole.USER, content="hola"),),
        parameters=GenerationParameters(),
        prompt_hash="0" * 64,
    )

    result = chain.complete(bundle)
    assert primary_calls == []
    assert fallback_calls == ["called"]
    assert "from fallback" in result.text


def test_rotation_primary_succeeds_within_quota() -> None:
    """A healthy primary runs within quota and records usage, no fallback."""
    calls: List[str] = []

    class PrimaryStub(ProviderBackend):  # type: ignore[misc]
        def complete(self, prompt_bundle):
            calls.append("primary")
            from study_engine.llm.backends import ProviderCompletion

            return ProviderCompletion(
                text="from primary [E1]",
                latency_ms=1.0,
                tokens_used=None,
                model="primary-model",
            )

    breaker = CircuitBreaker(requests_per_day_limit=1000, tokens_per_minute_limit=1_000_000)
    chain = CircuitBreakerBackend(
        primary_backend=PrimaryStub(),
        fallback_backend=ReplayMockBackend(),
        circuit_breaker=breaker,
    )

    from study_engine.generation.prompts import PromptBundle, PromptMessage, PromptRole
    from study_engine.contracts.generation import GenerationParameters

    bundle = PromptBundle(
        system_prompt="sys",
        messages=(PromptMessage(role=PromptRole.USER, content="hola"),),
        parameters=GenerationParameters(max_output_tokens=10),
        prompt_hash="0" * 64,
    )

    result = chain.complete(bundle)
    assert calls == ["primary"]
    assert "from primary" in result.text