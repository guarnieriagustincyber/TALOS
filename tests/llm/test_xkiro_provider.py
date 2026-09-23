"""Unit tests for Xkiro (Qwen 3.8 Max) Provider and GLOBAL depth hierarchy."""

import pytest

from study_engine.llm.circuit_breaker import CircuitBreaker
from study_engine.llm.factory import PROVIDER_REGISTRY
from study_engine.llm.providers.gemini import GeminiProvider
from study_engine.llm.providers.groq import GroqProvider
from study_engine.llm.providers.xkiro import XkiroProvider
from study_engine.llm.registry import DEFAULT_PROVIDER_HIERARCHY, ModelRegistry


@pytest.fixture(autouse=True)
def isolate_xkiro_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate tests from external environment variables like XKIRO_MODEL loaded from .env."""
    monkeypatch.delenv("XKIRO_MODEL", raising=False)


def test_xkiro_provider_initialization() -> None:
    """Xkiro provider initializes with Qwen 3.8 Max and 1M context capacity."""
    provider = XkiroProvider(api_key="sk-test-xkiro-123")
    assert provider.provider_id == "xkiro"
    assert provider.default_model == "qwen/qwen3.8-max:free"
    assert provider.max_context_tokens() == 1_000_000
    assert not provider.supports_multimodal()

    health = provider.health_check()
    assert health.provider_id == "xkiro"
    assert health.context_capacity == 1_000_000
    assert health.is_healthy
    assert health.availability == 1.0


def test_xkiro_generation_and_streaming() -> None:
    """Xkiro provider generates and streams completions correctly."""
    provider = XkiroProvider(api_key="sk-test-xkiro-123")
    resp = provider.generate("Analizar dialéctica entre Bobbio y Schmitt")
    assert resp.provider_id == "xkiro"
    assert "Qwen 3.8 Max" in resp.text
    assert resp.tokens_used.total_tokens > 0

    chunks = list(provider.generate_stream("Sintetizar fuentes"))
    assert len(chunks) > 0
    full_text = "".join(chunks)
    assert "Qwen 3.8 Max" in full_text


def test_xkiro_prioritized_in_global_hierarchy() -> None:
    """ModelRegistry prioritizes Xkiro when depth='GLOBAL' is requested."""
    registry = ModelRegistry()
    xkiro = XkiroProvider(api_key="sk-test-xkiro")
    gemini = GeminiProvider(api_key="sk-test-gemini")
    groq = GroqProvider()

    registry.register_provider(xkiro)
    registry.register_provider(gemini)
    registry.register_provider(groq)

    # In GLOBAL hierarchy, xkiro is ranked first: ["xkiro", "gemini", "nvidia", "openrouter"]
    assert DEFAULT_PROVIDER_HIERARCHY["GLOBAL"][0] == "xkiro"

    provider, health = registry.select_best_provider(depth="GLOBAL")
    assert provider.provider_id == "xkiro"
    assert health.provider_id == "xkiro"


def test_xkiro_fallback_in_global_hierarchy() -> None:
    """If Xkiro circuit breaker opens, ModelRegistry falls back to Gemini in GLOBAL."""
    registry = ModelRegistry()
    cb_xkiro = CircuitBreaker(failure_threshold=2)
    xkiro = XkiroProvider()
    gemini = GeminiProvider()

    registry.register_provider(xkiro, circuit_breaker=cb_xkiro)
    registry.register_provider(gemini)

    # Simulate failures on xkiro
    registry.record_call_result("xkiro", success=False, is_429=True)
    registry.record_call_result("xkiro", success=False, is_429=True)

    # Circuit breaker is now open
    assert cb_xkiro.is_circuit_open()

    # ModelRegistry should fallback to gemini
    provider, health = registry.select_best_provider(depth="GLOBAL")
    assert provider.provider_id == "gemini"


def test_xkiro_in_factory_registry() -> None:
    """Xkiro is present in LLM factory PROVIDER_REGISTRY with valid spec."""
    assert "xkiro" in PROVIDER_REGISTRY
    spec = PROVIDER_REGISTRY["xkiro"]
    assert spec.provider_type == "xkiro"
    assert spec.default_model == "qwen/qwen3.8-max:free"
    assert spec.api_key_env == "XKIRO_API_KEY"
