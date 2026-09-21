"""Auditoría de Rendimiento: Techo de Presupuesto y Corte Automático (Fase 7.3, Métrica 17).

Métrica Evaluada:
- Métrica 17: Techo de Presupuesto y Corte Automático
    - Límite de gasto por sesión: < $1.00 USD
    - Límite de gasto por día: < $5.00 USD
    - Corte automático activo y verificado
    - Prevención de facturación descontrolada ante loops infinitos de reintentos
"""

import pytest

from study_engine.llm.quota_manager import (
    BudgetCeilingExceededError,
    BudgetCeilingManager,
)


def test_session_budget_ceiling_enforcement() -> None:
    """Verifica que el límite de gasto por sesión (< $1.00 USD) se cumpla y active el corte automático."""
    manager = BudgetCeilingManager(max_session_usd=1.00, max_daily_usd=5.00)
    session_id = "sess_pedagogical_01"

    assert manager.can_proceed(session_id) is True
    assert manager.get_session_spend(session_id) == 0.0

    # 1. Simular consumo acumulativo normal dentro de la sesión
    # 30 turnos a ~$0.015 por turno = $0.45 USD (bajo el límite)
    for _ in range(30):
        assert manager.can_proceed(session_id, estimated_cost_usd=0.015) is True
        manager.record_spend(session_id, 0.015)

    spend_so_far = manager.get_session_spend(session_id)
    assert spend_so_far == pytest.approx(0.45, rel=1e-3)
    assert manager.is_session_tripped(session_id) is False

    # 2. Agregar más consumo hasta acercarse al límite: 36 turnos adicionales * 0.015 = 0.54 -> Total = 0.99 USD
    for _ in range(36):
        manager.record_spend(session_id, 0.015)

    assert manager.get_session_spend(session_id) == pytest.approx(0.99, rel=1e-3)
    assert manager.can_proceed(session_id, estimated_cost_usd=0.005) is True
    # Intento de consulta que excede el límite de $1.00
    assert manager.can_proceed(session_id, estimated_cost_usd=0.02) is False

    # 3. Superar el límite -> Se dispara el corte automático
    with pytest.raises(BudgetCeilingExceededError) as exc_info:
        manager.record_spend(session_id, 0.02)

    assert "Session budget ceiling exceeded" in str(exc_info.value)
    assert manager.is_session_tripped(session_id) is True
    assert manager.can_proceed(session_id) is False


def test_daily_budget_ceiling_enforcement() -> None:
    """Verifica que el límite de gasto global diario (< $5.00 USD) bloquee todas las sesiones al alcanzarse."""
    manager = BudgetCeilingManager(max_session_usd=1.00, max_daily_usd=5.00)

    # 5 sesiones consumiendo $0.90 USD cada una = $4.50 USD
    for i in range(5):
        sess = f"sess_user_day_{i}"
        assert manager.can_proceed(sess) is True
        manager.record_spend(sess, 0.90)

    daily_spend = manager.get_daily_spend()
    assert daily_spend == pytest.approx(4.50, rel=1e-3)
    assert manager.is_daily_tripped() is False

    # Sexta sesión intenta consumir $0.60 USD -> Total sería $5.10 USD (excede $5.00)
    sess_6 = "sess_user_day_5"
    assert manager.can_proceed(sess_6, estimated_cost_usd=0.60) is False

    # Forzar intento de gasto que supera el techo diario
    with pytest.raises(BudgetCeilingExceededError) as exc_info:
        manager.record_spend(sess_6, 0.60)

    assert "Daily budget ceiling exceeded" in str(exc_info.value)
    assert manager.is_daily_tripped() is True

    # Todas las sesiones posteriores deben ser rechazadas inmediatamente
    assert manager.can_proceed("sess_user_day_new") is False


def test_infinite_retry_storm_runaway_prevention() -> None:
    """Verifica que un loop infinito de reintentos fallidos sea cortado automáticamente antes de $1.00 USD."""
    manager = BudgetCeilingManager(max_session_usd=1.00, max_daily_usd=5.00)
    session_id = "sess_runaway_storm"

    attempts = 0
    blocked_attempts = 0
    cost_per_failing_retry = 0.03  # $0.03 por reintento con payload grande

    # Simular bucle descontrolado de 100 reintentos
    for _ in range(100):
        if not manager.can_proceed(session_id, estimated_cost_usd=cost_per_failing_retry):
            blocked_attempts += 1
            # Si un proceso rebelde intenta ignorar el corte e invocar el LLM, record_spend lanza y tripea
            with pytest.raises(BudgetCeilingExceededError):
                manager.record_spend(session_id, cost_per_failing_retry)
            break

        attempts += 1
        manager.record_spend(session_id, cost_per_failing_retry)

    # Debe haber cortado exactamente en el intento 33 (33 * 0.03 = 0.99 USD)
    assert attempts == 33
    assert blocked_attempts == 1
    final_spend = manager.get_session_spend(session_id)
    assert final_spend <= 1.02  # Gasto acotado estrictamente en el techo
    assert manager.is_session_tripped(session_id) is True
    assert manager.can_proceed(session_id) is False
