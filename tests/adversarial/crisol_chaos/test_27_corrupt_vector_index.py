"""Escenario 27: Corrupción del Índice Vectorial o Chunks (Fase 7.2 - Chaos Engineering).

Simular corrupción de índice vectorial, embeddings ausentes o chunks con metadatos inconsistentes.
Invariante: INV-W5-1: Ante evidencia ausente o invalidada, el sistema se abstiene de forma honesta
            fail-closed; nunca genera explicaciones inventadas basadas en índices corruptos.
Severidad: MEDIO.
"""

import pytest

from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator


def test_corrupt_or_empty_vector_index_triggers_honest_abstention() -> None:
    """When vector index returns 0 valid chunks due to corruption, system abstains fail-closed."""
    # Corrupted index returns empty pack (0 evidence chunks)
    corrupted_pack = ContextPack(current_kc="quantum_crypto", total_tokens=0)

    controller = EpistemicController()
    payload = controller.process(
        query="Explicame el protocolo BB84 para distribución de claves cuánticas.",
        context_pack=corrupted_pack,
    )

    # Invariant 1: 0 facts extracted
    assert len(payload.core_facts) == 0
    assert len(payload.citations) == 0

    # Invariant 2: Narrator emits honest abstention, never hallucinates quantum protocols
    narrator = PersonaNarrator()
    prose = narrator.narrate(payload)

    assert "no encontré evidencias suficientes" in prose.lower()
    assert "BB84" not in prose
    assert len(payload.citations) == 0
