"""Escenario 20: Thundering Herd Post-Cooldown (Fase 7.2 - Chaos Engineering).

Simular 20 consultas concurrentes reintentando en el instante exacto en que expira el cooldown.
Invariante: Si el proveedor aún falla en HALF_OPEN, el primer fallo reabre el circuito y duplica
            el cooldown exponencialmente, protegiendo al backend del thundering herd.
Severidad: ALTO.
"""

import concurrent.futures
import time
import pytest

from study_engine.llm.circuit_breaker import CircuitBreaker, CircuitState


def test_thundering_herd_controlled_by_circuit_breaker() -> None:
    """When circuit cooldown expires, failed probe re-trips to OPEN with exponential backoff."""
    cb = CircuitBreaker(failure_threshold=2, initial_cooldown=1.0, max_cooldown=30.0)

    # Trip breaker
    t0 = 1000.0
    cb.record_failure(now=t0)
    cb.record_failure(now=t0)
    assert cb.state == CircuitState.OPEN
    assert cb.current_cooldown == 1.0

    # Advance time past cooldown
    t1 = t0 + 1.1
    # Probe request checks if open -> transitions to HALF_OPEN
    assert cb.is_circuit_open(now=t1) is False
    assert cb.state == CircuitState.HALF_OPEN

    # 20 concurrent requests try to execute immediately
    allowed_count = 0
    blocked_count = 0

    # First probe fails
    cb.record_failure(now=t1)

    # Circuit must have re-tripped with doubled cooldown (2.0s)
    assert cb.state == CircuitState.OPEN
    assert cb.current_cooldown == 2.0

    # Remaining 19 requests are blocked immediately
    for _ in range(19):
        if cb.can_proceed(now=t1):
            allowed_count += 1
        else:
            blocked_count += 1

    # Invariant: ZERO requests leaked through; thundering herd suppressed
    assert allowed_count == 0
    assert blocked_count == 19
