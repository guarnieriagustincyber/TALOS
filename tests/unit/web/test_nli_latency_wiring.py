"""Regresión M1-01: límites de recursos por defecto del juez NLI (S4.4 wiring).

Evidencia que motiva los defaults (mediciones live 2026-10-20, M1-01,
provider gemini-3.5-flash-lite vía OpenAI-compatible, llamadas atómicas
premise/hypothesis): 40.1s / 31.8s / 27.9s (p50 ~32s) con veredictos
semánticos correctos (ENTAILED / NOT_ENTAILED). Los defaults previos
(12s call timeout / 20s audit budget) forzaban LLMTimeoutError en cada
claim del auditor → DEFERRED_RETRY crónico (fallo CLASIFICADO correctly
as TECHNICAL, pero circuito académico inoperante en runtime real).

Esto NO es un umbral epistémico ni de abstención: el veredicto sigue
siendo del auditor; solo cambia la capacidad técnica de completar la
verificación en runtime.
"""

from __future__ import annotations

from study_engine.web import dependencies as deps


def test_nli_call_timeout_default_covers_measured_latency_profile() -> None:
    """p50/medición 27.9s–40.1s exige margen sobre 40s; el default no puede ser 12s."""
    assert deps.NLI_CALL_TIMEOUT_DEFAULT_S >= 45.0
    # El default previo (12s) quedaba por debajo del mínimo medido (27.9s).
    assert deps.NLI_CALL_TIMEOUT_DEFAULT_S > 27.9


def test_nli_audit_budget_default_constrains_concurrency_window() -> None:
    """3 claims en paralelo × p50 ~32s: el budget debe superar una ventana."""
    assert deps.NLI_AUDIT_BUDGET_DEFAULT_S >= deps.NLI_CALL_TIMEOUT_DEFAULT_S


def test_env_overrides_respect_positive_floats() -> None:
    """El wiring acepta override por env (comportamiento contractual existente)."""
    import os
    from unittest.mock import patch

    with patch.dict(os.environ, {
        "TALOS_NLI_CALL_TIMEOUT_S": "45.5",
        "TALOS_NLI_AUDIT_BUDGET_S": "90",
    }, clear=False):
        assert float(os.getenv("TALOS_NLI_CALL_TIMEOUT_S", str(deps.NLI_CALL_TIMEOUT_DEFAULT_S))) == 45.5
        assert float(os.getenv("TALOS_NLI_AUDIT_BUDGET_S", str(deps.NLI_AUDIT_BUDGET_DEFAULT_S))) == 90.0
