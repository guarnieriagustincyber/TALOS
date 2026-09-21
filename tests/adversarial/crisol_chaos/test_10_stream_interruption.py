"""Escenario 10: Fallo a Mitad de Stream SSE (Fase 7.2 - Chaos Engineering).

Simular desconexión intempestiva del cliente o interrupción en generador de streaming.
Invariante: Cierre limpio de generadores, liberación de cursores/locks y capacidad
            inmediata de procesar subsecuentes consultas sin bloqueo ni fugas.
Severidad: ALTO.
"""

import pytest

from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.pedagogy.controller_payload import ConversationStyle
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator


def test_streaming_interruption_resource_cleanup() -> None:
    """Stream generator handles premature consumer disconnect without resource deadlocks."""
    pack = ContextPack(current_kc="concurrency_mutex", total_tokens=45)
    pack.add_evidence(
        ChunkWithProvenance(
            chunk_id="chk_mutex_1",
            document_id="doc_posix",
            source_id="src_posix",
            source_title="POSIX Threads Programming",
            page_start=88,
            pos_index=1,
            section="Mutexes",
            content="pthread_mutex_lock adquiere el lock de exclusión mutua de manera atómica.",
            is_seed_hit=True,
            relevance_score=0.96,
            token_count=18,
        )
    )

    controller = EpistemicController()
    payload = controller.process(
        query="¿Qué garantiza pthread_mutex_lock?",
        context_pack=pack,
        style=ConversationStyle.CASUAL_CHAT,
    )

    narrator = PersonaNarrator()

    # Create stream iterator
    stream = narrator.narrate_stream(payload)

    # Consume partially (simulate client aborting after 3 tokens)
    tokens_read = []
    for _ in range(3):
        tokens_read.append(next(stream))

    assert len(tokens_read) == 3

    # Prematurely close generator (triggers GeneratorExit cleanup)
    stream.close()

    # Invariant: Subsequent requests proceed cleanly with zero locks hung
    payload_next = controller.process(
        query="Siguiente consulta tras desconexión",
        context_pack=pack,
    )
    res_next = narrator.narrate(payload_next)
    assert len(res_next) > 0
    assert "pthread_mutex_lock" in res_next
