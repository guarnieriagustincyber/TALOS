"""Escenario 09: Apagón de Proveedores Cloud (Fase 7.2 - Chaos Engineering).

Simular que todos los proveedores LLM caen simultáneamente (Circuit Breakers abiertos o errores de red).
Invariante: El sistema no arroja 500 no controlado; conmuta limpiamente a síntesis determinista
o a la abstención honesta preservando las invariantes INV-W5-1 y INV-W6-1.
Severidad: CRÍTICO.
"""

import pytest

from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.llm.circuit_breaker import CircuitBreaker, CircuitState
from study_engine.llm.registry import ModelRegistry
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator


class DeadCloudProvider:
    def __init__(self, name: str):
        self.name = name

    def generate(self, prompt: str, **kwargs):
        raise ConnectionError(f"HTTP 503 Service Unavailable: {self.name} is completely down")


def test_provider_blackout_graceful_fallback() -> None:
    """When all cloud providers blackout, system degrades gracefully to deterministic prose."""
    pack = ContextPack(current_kc="ipc_pipes", total_tokens=40)
    pack.add_evidence(
        ChunkWithProvenance(
            chunk_id="chk_pipe_1",
            document_id="doc_unix",
            source_id="src_stevens",
            source_title="Advanced Programming in the UNIX Environment",
            page_start=410,
            pos_index=1,
            section="Pipes",
            content="pipe() crea un canal unidireccional con dos descriptores de archivo: lectura y escritura.",
            is_seed_hit=True,
            relevance_score=0.94,
            token_count=18,
        )
    )

    controller = EpistemicController()
    payload = controller.process(
        query="¿Cómo funciona la llamada pipe() en UNIX?",
        context_pack=pack,
    )

    # All providers dead
    narrator = PersonaNarrator(llm_backend=DeadCloudProvider("all_cloud_blackout"))

    # Execution must NOT raise an unhandled exception
    prose = narrator.narrate(payload)

    # Invariant: Output is grounded in core facts despite total cloud blackout
    assert len(prose) > 20
    assert "pipe()" in prose or "descriptores" in prose
    assert "[E1]" in prose


def test_provider_blackout_all_circuits_open_registry_handling() -> None:
    """ModelRegistry cleanly indicates failure without crashing when all breakers are OPEN."""
    registry = ModelRegistry()
    cb = CircuitBreaker()
    cb.state = CircuitState.OPEN

    # When all circuits open, select_best_provider raises RuntimeError, caught by callers
    with pytest.raises(RuntimeError, match="No healthy provider available"):
        registry.select_best_provider()
