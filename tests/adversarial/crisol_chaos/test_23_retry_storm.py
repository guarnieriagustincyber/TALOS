"""Escenario 23: Retry Storm / Denial of Wallet Prevention (Fase 7.2 - Chaos Engineering).

Simular que un proveedor devuelve errores 429 Too Many Requests de forma repetida.
Invariante: El sistema no entra en bucle infinito de reintentos; el Circuit Breaker corta
            las llamadas al alcanzar el umbral, protegiendo contra el agotamiento de cuota.
Severidad: ALTO.
"""

import pytest

from study_engine.llm.circuit_breaker import CircuitBreaker, CircuitState
from study_engine.llm.registry import ModelRegistry


def test_retry_storm_suppression_and_circuit_tripping() -> None:
    """Repeated 429 rate limit responses trip circuit breaker and halt outgoing calls."""
    cb = CircuitBreaker(failure_threshold=3, initial_cooldown=5.0)

    call_count = 0

    # Simulate gateway trying to invoke provider returning 429
    for i in range(10):
        if not cb.can_proceed():
            # Request rejected by circuit breaker; call aborted without hitting provider
            continue

        call_count += 1
        # Provider returns 429 Too Many Requests
        cb.record_failure()

    # Invariant 1: Calls are capped strictly at failure_threshold (3), not 10!
    assert call_count == 3
    # Invariant 2: Circuit tripped to OPEN
    assert cb.state == CircuitState.OPEN
    assert cb.is_circuit_open() is True
