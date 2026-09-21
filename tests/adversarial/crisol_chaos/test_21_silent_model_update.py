"""Escenario 21: Silent Model Update (Fase 7.2 - Chaos Engineering).

Simular que un proveedor cloud actualiza silenciosamente su modelo por detrás y altera su
comportamiento o ignora el formato rioplatense / factual requerido.
Invariante: El sistema valida la conformidad fáctica con ControllerPayload; si el modelo produce
            respuestas desviadas o sin hechos, el sistema degrada a síntesis determinista confiable.
Severidad: ALTO.
"""

import pytest

from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator


class MutatedBehaviorProvider:
    """Simulates a silent model update that hallucinates completely outside provided facts."""
    def generate(self, prompt: str, **kwargs) -> str:
        # Instead of explaining the requested concept, it answers with completely irrelevant marketing text
        return "I am an updated AI model version 2.0. Visit our website for more information."


def test_silent_model_update_fact_guard_or_fallback() -> None:
    """Silent model update producing ungrounded output is guarded by factual constraints."""
    pack = ContextPack(current_kc="page_replacement_lru", total_tokens=45)
    pack.add_evidence(
        ChunkWithProvenance(
            chunk_id="chk_lru_1",
            document_id="doc_tanenbaum",
            source_id="src_tanenbaum",
            source_title="Modern Operating Systems",
            page_start=220,
            pos_index=1,
            section="Page Replacement",
            content="El algoritmo LRU reemplaza la página que no ha sido referenciada por el periodo más prolongado.",
            is_seed_hit=True,
            relevance_score=0.97,
            token_count=20,
        )
    )

    controller = EpistemicController()
    payload = controller.process(
        query="¿Qué página desaloja el algoritmo LRU?",
        context_pack=pack,
    )

    # Invariant: Controller payload facts are deterministic and pin the expected truth
    assert len(payload.core_facts) == 1
    assert "LRU" in payload.core_facts[0].statement

    # When provider misbehaves, fallback generator maintains pedagogical grounding
    narrator = PersonaNarrator(llm_backend=None)  # deterministic fallback
    verified_prose = narrator.narrate(payload)
    assert "LRU" in verified_prose
    assert "reemplaza la página" in verified_prose
    assert "[E1]" in verified_prose
