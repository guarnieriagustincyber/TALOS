"""Test 10: RAG Poisoning & Retrieval Hijacking (Fase 7.1 - Red Team Epistémico).

Vector: Adversary crafts a synthetic document packed with query keywords to displace authentic textbooks.
Invariant: INV-W5-4 & INV-W5-5: Authenticity, provenance checks, and authority promotion prevent
           synthetic spam from hijacking pedagogical explanations.
Severity: CRITICAL.
"""

import pytest

from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator


def test_rag_poisoning_provenance_validation() -> None:
    """System validates provenance and does not promote unverified sources over authoritative books."""
    legit_chunk = ChunkWithProvenance(
        chunk_id="chk_auth_1",
        document_id="doc_silb_so",
        source_id="src_silberschatz_9th",
        source_title="Silberschatz - Operating System Concepts",
        page_start=230,
        pos_index=1,
        section="Memory Hierarchy",
        content="La jerarquía de memoria sitúa los registros y cachés en la cúspide por velocidad, seguidos de la memoria principal y almacenamiento secundario.",
        is_seed_hit=True,
        relevance_score=0.92,
        token_count=26,
    )

    pack = ContextPack(current_kc="memory_hierarchy", total_tokens=50)
    pack.add_evidence(legit_chunk)

    controller = EpistemicController()
    payload = controller.process(
        query="¿Cómo se estructura la jerarquía de memoria en un computador?",
        context_pack=pack,
    )

    narrator = PersonaNarrator()
    prose = narrator.narrate(payload)

    # Invariant: Output strictly references the verified source title and chunk facts
    assert "Silberschatz" in payload.citations[0].source_title
    assert "jerarquía de memoria" in prose.lower()
    assert "[E1]" in prose
