"""Test de regresión para BACKLOG-CTX-001 (Presupuesto de Contexto a 5.000 Tokens)."""

from study_engine.config import get_settings


def test_context_budget_increased_to_5000():
    """Verifica que el presupuesto de contexto sea 5.000 tokens."""
    settings = get_settings()
    assert settings.max_context_tokens == 5000
