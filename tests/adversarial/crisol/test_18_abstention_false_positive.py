"""Test 18: Abstention False Positive & Availability Guard (Fase 7.1 - Red Team Epistémico).

Vector: System receives legitimate queries with valid, focused evidence (e.g. single authoritative chunk).
Invariant: System must NOT falsely abstain; facts are preserved and grounded pedagogical response is emitted.
Severity: MEDIUM.
"""

import pytest

from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator


def test_no_false_abstention_with_valid_single_chunk() -> None:
    """Legitimate single chunk provides sufficient evidence; abstention is not triggered."""
    pack = ContextPack(current_kc="virtual_memory_paging", total_tokens=50)
    pack.add_evidence(
        ChunkWithProvenance(
            chunk_id="chk_paging_1",
            document_id="doc_tanenbaum",
            source_id="src_tanenbaum_mos",
            source_title="Modern Operating Systems",
            page_start=184,
            pos_index=1,
            section="Paging Mechanisms",
            content="La MMU utiliza la tabla de páginas para traducir direcciones virtuales a marcos de memoria física.",
            is_seed_hit=True,
            relevance_score=0.88,
            token_count=25,
        )
    )

    controller = EpistemicController()
    payload = controller.process(
        query="¿Qué componente traduce las direcciones virtuales a marcos físicos?",
        context_pack=pack,
    )

    # Invariant 1: Facts and citations extracted cleanly
    assert len(payload.core_facts) == 1
    assert len(payload.citations) == 1
    assert "MMU" in payload.core_facts[0].statement
    assert payload.citations[0].citation_id == "E1"

    # Invariant 2: Narrator emits grounded response, NOT abstention
    narrator = PersonaNarrator()
    prose = narrator.narrate(payload)

    assert "no encontré evidencias" not in prose.lower()
    assert "MMU" in prose or "tabla de páginas" in prose
    assert len(prose) > 20
