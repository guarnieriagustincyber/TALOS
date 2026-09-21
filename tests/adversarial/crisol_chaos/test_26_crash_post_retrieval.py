"""Escenario 26: Crash Entre Retrieval y Call al LLM (Fase 7.2 - Chaos Engineering).

Simular un crash o interrupción una vez completado el retrieval y ensamblado el ContextPack,
pero antes de ejecutar la llamada a generación con el LLM.
Invariante: El fallo se detecta de forma explícita; la telemetría conserva la traza fáctica parcial
            y el sistema entrega una explicación determinista de respaldo en lugar de un 'silent nothing'.
Severidad: MEDIO.
"""

import pytest

from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator


def test_crash_post_retrieval_emits_grounded_fallback_not_silent_nothing() -> None:
    """When LLM stage crashes immediately after retrieval, system provides factual fallback."""
    pack = ContextPack(current_kc="virtual_memory_tlb", total_tokens=45)
    pack.add_evidence(
        ChunkWithProvenance(
            chunk_id="chk_tlb_1",
            document_id="doc_arch",
            source_id="src_arch",
            source_title="Computer Architecture",
            page_start=340,
            pos_index=1,
            section="Memory Hierarchy",
            content="El TLB (Translation Lookaside Buffer) almacena traducciones recientes de páginas para acelerar accesos.",
            is_seed_hit=True,
            relevance_score=0.98,
            token_count=20,
        )
    )

    controller = EpistemicController()
    payload = controller.process(
        query="¿Qué función cumple el TLB en la jerarquía?",
        context_pack=pack,
    )

    # Invariant 1: Facts extracted deterministically before LLM call
    assert len(payload.core_facts) == 1
    assert "TLB" in payload.core_facts[0].statement

    # Simulate catastrophic exception in LLM backend
    class CrashingLLMBackend:
        def generate(self, prompt: str, **kwargs):
            raise RuntimeError("Fatal OOM / abort right before LLM inference")

    narrator = PersonaNarrator(llm_backend=CrashingLLMBackend())

    # Invariant 2: Narrator catches backend failure and generates deterministic response from payload facts
    prose = narrator.narrate(payload)

    # Invariant 3: Output is NOT empty ("silent nothing") and contains the retrieved facts
    assert len(prose) > 30
    assert "TLB" in prose
    assert "Translation Lookaside Buffer" in prose
    assert "[E1]" in prose
