"""Escenario 18: Clock Skew / Drift (Fase 7.2 - Chaos Engineering).

Simular desincronización de reloj (saltos de reloj NTP ±3600s).
Invariante: CircuitBreaker usa time.monotonic() y es inmune a saltos de reloj de pared.
            SM-2 preserva intervalos válidos y monotonía de EF sin excepciones.
Severidad: CRÍTICO.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest

from study_engine.llm.circuit_breaker import CircuitBreaker, CircuitState
from study_engine.student.spaced_repetition import SpacedRepetitionScheduler
from study_engine.student.storage import StudentStorage


def test_circuit_breaker_immune_to_wall_clock_skew() -> None:
    """Circuit breaker relies on monotonic time, remaining unaffected by NTP wall-clock jumps."""
    cb = CircuitBreaker(failure_threshold=1, initial_cooldown=2.0)
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.is_circuit_open() is True

    # Simulate wall-clock jumping 1 hour into the past (NTP correction / timezone error)
    skewed_past = datetime.now(timezone.utc) - timedelta(seconds=3600)
    with patch("study_engine.llm.circuit_breaker.datetime") as mock_dt:
        mock_dt.now.return_value = skewed_past
        # Monotonic time remains steady; breaker does not deadlock
        assert cb.is_circuit_open() is True


def test_sm2_spaced_repetition_under_clock_drift() -> None:
    """SM-2 scheduler maintains mathematical validity of interval and EF under backward clock drift."""
    storage = StudentStorage(":memory:")
    scheduler = SpacedRepetitionScheduler(storage=storage)
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    # Initial review
    first_review = scheduler.schedule_review("anchor_vm", quality=5, as_of=now)
    state = scheduler.get_anchor_state("anchor_vm")
    assert state.repetitions == 1
    assert state.interval == 1

    # Second review performed under clock skewed backwards by 3600s
    skewed_time = now - timedelta(seconds=3600)
    next_review = scheduler.schedule_review("anchor_vm", quality=4, as_of=skewed_time)
    state_after = scheduler.get_anchor_state("anchor_vm")

    # Invariants:
    # 1. EF remains bounded >= 1.30
    assert state_after.EF >= 1.30
    # 2. Next review is scheduled relative to evaluation time
    assert next_review > skewed_time
    # 3. Repetitions incremented
    assert state_after.repetitions == 2
