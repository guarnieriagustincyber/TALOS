"""Test suite for Conversational Style Router (Ola 6, Fase 6.2).

8 tests requeridos:
1. test_style_router_casual         -> "che, no entendí" se clasifica como CASUAL_CHAT
2. test_style_router_analogy        -> "haceme una analogía" se clasifica como ANALOGY_REQUEST
3. test_style_router_formal         -> Consulta > 12 palabras se clasifica como FORMAL_EXPLANATION
4. test_style_router_verification   -> "¿es verdad que...?" se clasifica como VERIFICATION
5. test_style_router_practice       -> "/practicar punteros" se clasifica como PRACTICE
6. test_style_router_cross_source   -> "compará X vs Y" se clasifica como CROSS_SOURCE
7. test_casual_response_no_headers  -> La prosa generada en CASUAL_CHAT no tiene headers '###'
8. test_formal_response_tri_layer   -> La prosa en FORMAL_EXPLANATION tiene estructura tri-capa con '###'
"""

import pytest

from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.pedagogy.controller_payload import (
    BKTStatus,
    Citation,
    ControllerPayload,
    ConversationStyle,
    Fact,
    PedagogicalConstraints,
)
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator
from study_engine.pedagogy.style_contracts import STYLE_CONTRACTS, STYLE_DIRECTIVES
from study_engine.pedagogy.style_router import ConversationStyleRouter, StyleRouteResult


def _create_mock_context_pack() -> ContextPack:
    chk1 = ChunkWithProvenance(
        chunk_id="chk_ptr_1",
        document_id="doc_c",
        source_id="src_kr_c",
        source_title="Kernighan & Ritchie C",
        page_start=94,
        pos_index=1,
        section="Punteros y Memoria",
        content="Un puntero contiene la dirección de memoria de una variable.",
        is_seed_hit=True,
        relevance_score=0.95,
        token_count=12,
    )
    chk2 = ChunkWithProvenance(
        chunk_id="chk_ptr_2",
        document_id="doc_c",
        source_id="src_kr_c",
        source_title="Kernighan & Ritchie C",
        page_start=95,
        pos_index=2,
        section="Punteros y Memoria",
        content="El operador unario * es el operador de indirección o desreferenciación.",
        is_seed_hit=True,
        relevance_score=0.90,
        token_count=13,
    )
    pack = ContextPack(
        current_kc="punteros_basicos",
        previous_errors=["confundir puntero con valor"],
        total_tokens=25,
    )
    pack.add_evidence(chk1)
    pack.add_evidence(chk2)
    return pack


def test_style_router_casual() -> None:
    """1. Short/casual query with signal word classifies as CASUAL_CHAT."""
    res = ConversationStyleRouter.detect_style("che, no entendí")
    assert res.style == ConversationStyle.CASUAL_CHAT
    assert "PROHIBIDO usar headers" in res.instruction_directive


def test_style_router_analogy() -> None:
    """2. Query requesting everyday analogy classifies as ANALOGY_REQUEST."""
    res = ConversationStyleRouter.detect_style("haceme una analogía")
    assert res.style == ConversationStyle.ANALOGY_REQUEST
    assert "ANALOGÍA" in res.instruction_directive


def test_style_router_formal() -> None:
    """3. Queries with >12 words fall back to FORMAL_EXPLANATION."""
    query = "explicame en detalle cómo funciona la memoria virtual en sistemas operativos modernos con paginación jerárquica y TLB"
    assert len(query.split()) > 12
    res = ConversationStyleRouter.detect_style(query)
    assert res.style == ConversationStyle.FORMAL_EXPLANATION
    assert "TRI-CAPA" in res.instruction_directive or "FORMAL" in res.instruction_directive


def test_style_router_verification() -> None:
    """4. Verification query starting with '¿es verdad que...?' classifies as VERIFICATION."""
    res = ConversationStyleRouter.detect_style("¿es verdad que un puntero NULL apunta a la dirección 0?")
    assert res.style == ConversationStyle.VERIFICATION
    assert "VERIFICACIÓN" in res.instruction_directive


def test_style_router_practice() -> None:
    """5. Slash command /practicar classifies as PRACTICE with target argument."""
    res = ConversationStyleRouter.detect_style("/practicar punteros")
    assert res.style == ConversationStyle.PRACTICE
    assert res.target_arg == "punteros"
    assert "PRÁCTICA" in res.instruction_directive


def test_style_router_cross_source() -> None:
    """6. Multi-source comparison query classifies as CROSS_SOURCE."""
    res = ConversationStyleRouter.detect_style("compará X vs Y")
    assert res.style == ConversationStyle.CROSS_SOURCE
    assert "SÍNTESIS DIALÉCTICA" in res.instruction_directive or "CROSS_SOURCE" in str(res.style)


def test_casual_response_no_headers() -> None:
    """7. Generated response in CASUAL_CHAT strictly contains NO markdown headers ('###')."""
    pack = _create_mock_context_pack()
    controller = EpistemicController()
    narrator = PersonaNarrator()

    payload = controller.process(
        query="che, no entendí",
        context_pack=pack,
        style=ConversationStyle.CASUAL_CHAT,
    )

    prose = narrator.narrate(payload)

    # Invariant: CASUAL_CHAT must NOT contain '###' headers
    assert "###" not in prose
    # Must contain factual grounding
    assert "Un puntero contiene la dirección de memoria" in prose
    # Must use natural rioplatense voseo
    assert any(w in prose.lower() for w in ("fijate", "mirá", "considerá", "tenés"))
    # Must close with guiding question
    assert "?" in prose


def test_formal_response_tri_layer() -> None:
    """8. Generated response in FORMAL_EXPLANATION strictly contains tri-layer markdown headers."""
    pack = _create_mock_context_pack()
    controller = EpistemicController()
    narrator = PersonaNarrator()

    payload = controller.process(
        query="explicame en detalle la estructura de punteros",
        context_pack=pack,
        style=ConversationStyle.FORMAL_EXPLANATION,
    )

    prose = narrator.narrate(payload)

    # Invariant: Tri-layer structure must be present
    assert "### 1. Intuición Conceptual" in prose
    assert "### 2. Mecanismo Formal" in prose
    assert "### 3. Nivel de Máquina" in prose
    # Must contain factual grounding and citations
    assert "Un puntero contiene la dirección de memoria" in prose
    assert "[E1]" in prose
