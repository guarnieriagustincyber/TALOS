"""Integration tests for LocalOrchestrator powered by Qwen 3.5 2B (Bloque C1)."""

import pytest

from study_engine.llm.backends import MockBackend, ProviderCompletion
from study_engine.tutor.local_orchestrator import LocalOrchestrator


@pytest.mark.integration
def test_local_orchestrator_greeting() -> None:
    """Verificar que un saludo es orquestado localmente usando Ollama/Qwen sin tocar cloud."""
    orch = LocalOrchestrator()
    decision = orch.orchestrate("Hola, buenos días", {})
    assert decision.use_local is True
    assert decision.provider == "ollama"
    assert decision.model == "qwen3.5:2b"
    assert decision.response is not None
    assert "Hola" in decision.response


@pytest.mark.integration
def test_local_orchestrator_technical_routing() -> None:
    """Verificar que una pregunta técnica selecciona provider cloud y reformula query."""
    orch = LocalOrchestrator()
    decision = orch.orchestrate("¿Cómo funciona la asignación dinámica de memoria con malloc?", {"detail_level": "normal"})
    assert decision.use_local is False
    assert decision.provider in ["groq", "gemini", "nvidia", "openrouter"]
    assert decision.model is not None
    assert decision.reformulated_query is not None


@pytest.mark.integration
def test_local_orchestrator_context_routing() -> None:
    """Verificar que el selector de providers responde al contexto pedagógico."""
    orch = LocalOrchestrator()
    
    # Practical task -> nvidia / deepseek
    decision_code = orch.orchestrate("Revisá mi implementación en C", {"has_practical_task": True})
    assert decision_code.provider == "nvidia"
    assert decision_code.model == "deepseek-ai/deepseek-v4-flash"

    # Detailed explanation -> gemini
    decision_detailed = orch.orchestrate("Explicación profunda de punteros dobles", {"detail_level": "detailed"})
    assert decision_detailed.provider == "gemini"
    assert decision_detailed.model == "gemini-3.1-flash-lite"
