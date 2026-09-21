"""Test suite for Model Registry & Long-Context Backends (Ola 5, Fase 5.3).

8 tests requeridos:
1. test_registry_healthy_providers     -> filtra por contexto y multimodal
2. test_registry_selects_best_score    -> elige el de mayor composite score
3. test_circuit_breaker_opens_on_429   -> tras 3 fallos, estado OPEN
4. test_circuit_breaker_half_open      -> tras cooldown, permite reintento
5. test_circuit_breaker_resets         -> éxito resetea a CLOSED
6. test_no_provider_available          -> si todos caen, error claro
7. test_provider_health_updates        -> health se actualiza con cada llamada
8. test_multimodal_filter              -> si requiere multimodal, excluye texto-only
"""

import time
import pytest

from study_engine.llm.circuit_breaker import CircuitBreaker, CircuitState
from study_engine.llm.providers.cerebras import CerebrasProvider
from study_engine.llm.providers.gemini import GeminiProvider
from study_engine.llm.providers.groq import GroqProvider
from study_engine.llm.providers.nvidia import NvidiaNemotronProvider
from study_engine.llm.providers.openrouter import OpenRouterProvider
from study_engine.llm.registry import ModelRegistry


def test_registry_healthy_providers() -> None:
    """1. Test that ModelRegistry filters providers strictly by context capacity and multimodal support."""
    registry = ModelRegistry()
    groq = GroqProvider()       # 128K, text-only
    gemini = GeminiProvider()   # 1M, multimodal

    registry.register_provider(groq)
    registry.register_provider(gemini)

    # Require 500K tokens -> groq (128K) is filtered out, gemini (1M) is selected
    provider, health = registry.select_best_provider(min_context_tokens=500_000)
    assert provider.provider_id == "gemini"
    assert health.context_capacity >= 500_000


def test_registry_selects_best_score() -> None:
    """2. Test that ModelRegistry selects the highest composite scoring provider among eligible ones."""
    registry = ModelRegistry()
    groq = GroqProvider()       # avg_latency 45ms -> higher score
    cerebras = CerebrasProvider() # avg_latency 50ms

    registry.register_provider(groq)
    registry.register_provider(cerebras)

    provider, health = registry.select_best_provider(depth="NORMAL")
    assert provider.provider_id == "groq"
    assert health.composite_score >= 0.8


def test_circuit_breaker_opens_on_429() -> None:
    """3. Circuit breaker transitions to OPEN state after 3 consecutive failures."""
    cb = CircuitBreaker(failure_threshold=3, initial_cooldown=10.0)
    assert cb.state == CircuitState.CLOSED
    assert not cb.is_circuit_open()

    cb.record_failure()
    assert cb.state == CircuitState.CLOSED

    cb.record_failure()
    assert cb.state == CircuitState.CLOSED

    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.is_circuit_open()


def test_circuit_breaker_half_open() -> None:
    """4. Circuit breaker enters HALF_OPEN state after cooldown elapses."""
    cb = CircuitBreaker(failure_threshold=3, initial_cooldown=0.1)
    for _ in range(3):
        cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.is_circuit_open()

    # Wait for cooldown
    time.sleep(0.15)
    # is_circuit_open transitions OPEN -> HALF_OPEN once cooldown passes and returns False to allow canary
    assert not cb.is_circuit_open()
    assert cb.state == CircuitState.HALF_OPEN


def test_circuit_breaker_resets() -> None:
    """5. Successful invocation resets circuit breaker from OPEN/HALF_OPEN back to CLOSED."""
    cb = CircuitBreaker(failure_threshold=3, initial_cooldown=0.1)
    for _ in range(3):
        cb.record_failure()
    assert cb.state == CircuitState.OPEN

    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.consecutive_failures == 0
    assert not cb.is_circuit_open()


def test_no_provider_available() -> None:
    """6. When all eligible providers trip circuit breakers, an informative error is raised."""
    registry = ModelRegistry()
    groq = GroqProvider()
    cb = CircuitBreaker(failure_threshold=1)
    cb.record_failure() # Circuit OPEN

    registry.register_provider(groq, circuit_breaker=cb)

    with pytest.raises(RuntimeError, match="No healthy provider available"):
        registry.select_best_provider(depth="NORMAL")


def test_provider_health_updates() -> None:
    """7. Registry health score reflects live successes, latencies, and 429 rate limit penalties."""
    registry = ModelRegistry()
    nvidia = NvidiaNemotronProvider()
    registry.register_provider(nvidia)

    initial_health = registry.get_provider_health("nvidia")
    assert initial_health is not None
    initial_score = initial_health.composite_score

    # Simulate 429 rate limit error
    registry.record_call_result("nvidia", success=False, is_429=True)
    penalized_health = registry.get_provider_health("nvidia")
    assert penalized_health is not None
    assert penalized_health.rate_limit_429_count == 1
    assert penalized_health.composite_score < initial_score

    # Simulate success
    registry.record_call_result("nvidia", success=True, latency_ms=100.0)
    recovered_health = registry.get_provider_health("nvidia")
    assert recovered_health is not None
    assert recovered_health.rate_limit_429_count == 0


def test_multimodal_filter() -> None:
    """8. If multimodal is required, text-only providers (Nvidia, Groq, Cerebras) are excluded."""
    registry = ModelRegistry()
    nvidia = NvidiaNemotronProvider()  # Text-only 1M
    groq = GroqProvider()              # Text-only 128K
    openrouter = OpenRouterProvider()  # Multimodal 1M

    registry.register_provider(nvidia)
    registry.register_provider(groq)
    registry.register_provider(openrouter)

    # Require multimodal
    provider, health = registry.select_best_provider(requires_multimodal=True)
    assert provider.provider_id == "openrouter"
    assert health.multimodal_support is True
