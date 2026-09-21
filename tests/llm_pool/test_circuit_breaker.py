"""Unit and Concurrency tests for ProviderCircuitBreaker (Fase 5.9 / Pilar 2 / Ajuste 1)."""

import asyncio
import time
import pytest

from study_engine.llm.router import CircuitState, ProviderCircuitBreaker


def test_circuit_breaker_initial_state():
    """Circuit breaker should start in CLOSED state and permit requests."""
    async def _run():
        cb = ProviderCircuitBreaker("test-provider", failure_threshold=3, cooldown_seconds=60.0)
        assert cb.state == CircuitState.CLOSED
        assert await cb.can_proceed() is True

    asyncio.run(_run())


def test_circuit_breaker_opens_after_threshold():
    """Circuit breaker should open after consecutive failures reach threshold."""
    async def _run():
        cb = ProviderCircuitBreaker("test-provider", failure_threshold=3, cooldown_seconds=60.0)
        await cb.record_failure(RuntimeError("Temporary error 1"))
        assert cb.state == CircuitState.CLOSED
        assert await cb.can_proceed() is True

        await cb.record_failure(RuntimeError("Temporary error 2"))
        assert cb.state == CircuitState.CLOSED
        assert await cb.can_proceed() is True

        await cb.record_failure(RuntimeError("Temporary error 3"))
        assert cb.state == CircuitState.OPEN
        assert await cb.can_proceed() is False
        assert cb.last_failure is not None

    asyncio.run(_run())


def test_circuit_breaker_opens_immediately_on_429():
    """Circuit breaker should immediately open when receiving HTTP 429."""
    async def _run():
        cb = ProviderCircuitBreaker("test-provider", failure_threshold=5, cooldown_seconds=60.0)
        await cb.record_failure(RuntimeError("HTTP 429 Too Many Requests"))
        assert cb.state == CircuitState.OPEN
        assert await cb.can_proceed() is False

    asyncio.run(_run())


def test_circuit_breaker_cooldown_and_half_open_recovery():
    """Circuit breaker should transition to HALF_OPEN after cooldown and recover on success."""
    async def _run():
        cb = ProviderCircuitBreaker("test-provider", failure_threshold=1, cooldown_seconds=0.05)
        await cb.record_failure(RuntimeError("Failure"))
        assert cb.state == CircuitState.OPEN
        assert await cb.can_proceed() is False

        # Wait for cooldown
        await asyncio.sleep(0.06)

        # First request after cooldown should transition to HALF_OPEN and proceed
        assert await cb.can_proceed() is True
        assert cb.state == CircuitState.HALF_OPEN

        # Second concurrent request in HALF_OPEN should be rejected
        assert await cb.can_proceed() is False

        # Success in trial request closes circuit
        await cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert await cb.can_proceed() is True

    asyncio.run(_run())


def test_circuit_breaker_half_open_failure_reopens():
    """If trial request fails in HALF_OPEN, circuit should immediately reopen."""
    async def _run():
        cb = ProviderCircuitBreaker("test-provider", failure_threshold=3, cooldown_seconds=0.05)
        await cb.record_failure(RuntimeError("HTTP 429"))
        assert cb.state == CircuitState.OPEN

        await asyncio.sleep(0.06)
        assert await cb.can_proceed() is True
        assert cb.state == CircuitState.HALF_OPEN

        # Trial request fails
        await cb.record_failure(RuntimeError("Trial failed"))
        assert cb.state == CircuitState.OPEN
        assert await cb.can_proceed() is False

    asyncio.run(_run())


def test_circuit_breaker_concurrency_thread_safety():
    """Ajuste 1: Concurrent access protected by asyncio.Lock() must not cause race conditions."""
    async def _run():
        cb = ProviderCircuitBreaker("test-concurrency", failure_threshold=5, cooldown_seconds=60.0)

        # Launch 50 concurrent tasks attempting can_proceed and recording mixed outcomes
        async def worker(idx: int):
            allowed = await cb.can_proceed()
            if allowed:
                if idx % 3 == 0:
                    await cb.record_failure(RuntimeError("Failure from worker"))
                else:
                    await cb.record_success()

        tasks = [worker(i) for i in range(50)]
        await asyncio.gather(*tasks)

        # State must remain valid without exception or deadlock
        assert cb.state in (CircuitState.CLOSED, CircuitState.OPEN)

    asyncio.run(_run())
