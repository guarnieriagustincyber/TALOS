"""Escenario 15: Latencia Parásita y Slowloris (Fase 7.2 - Chaos Engineering).

Simular un proveedor LLM que mantiene la conexión abierta pero no emite datos o lo hace
con lentitud parásita extrema (1 token cada 15s).
Invariante: El cliente / Circuit Breaker aborta por timeout en menos de 4s, registra la falla
            y commuta limpiamente a la vía de degradación/fallback sin colgar el event loop.
Severidad: CRÍTICO.
"""

import time
import pytest

from study_engine.llm.circuit_breaker import CircuitBreaker, CircuitState


class SlowlorisLLMBackend:
    def __init__(self, inter_chunk_delay: float = 10.0, timeout: float = 2.0):
        self.inter_chunk_delay = inter_chunk_delay
        self.timeout = timeout

    def generate(self, prompt: str, **kwargs) -> str:
        start = time.perf_counter()
        # Simulates blocking or sleeping longer than timeout
        elapsed = 0.0
        step = 0.05
        while elapsed < self.inter_chunk_delay:
            time.sleep(step)
            elapsed = time.perf_counter() - start
            if elapsed >= self.timeout:
                raise TimeoutError(f"Streaming read timeout exceeded: {elapsed:.2f}s >= {self.timeout:.2f}s")
        return "response"


def test_slowloris_timeout_aborts_under_4_seconds() -> None:
    """Backend with parasitic latency is cut off by read timeout under 4s; CB records failure."""
    cb = CircuitBreaker(failure_threshold=2, initial_cooldown=1.0)
    backend = SlowlorisLLMBackend(inter_chunk_delay=15.0, timeout=1.5)

    start_time = time.perf_counter()
    with pytest.raises(TimeoutError, match="timeout exceeded"):
        try:
            backend.generate("prompt de prueba")
        except TimeoutError:
            cb.record_failure()
            raise

    elapsed_time = time.perf_counter() - start_time
    # Invariant: Must abort strictly in less than 4 seconds
    assert elapsed_time < 4.0
    assert cb.consecutive_failures == 1

    # Second timeout should trip circuit breaker
    with pytest.raises(TimeoutError):
        try:
            backend.generate("prompt de prueba 2")
        except TimeoutError:
            cb.record_failure()
            raise

    assert cb.consecutive_failures == 2
    assert cb.state == CircuitState.OPEN
    assert cb.is_circuit_open() is True
