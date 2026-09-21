"""Unit tests for ContextPacker in Subsystem S4.1."""

import pytest

from study_engine.context.packer import ContextPacker
from study_engine.contracts.evidence_engine import (
    BudgetError,
    EpistemicClaimType,

    EvaluatedEvidenceItem,
    EvidenceGrade,
    EvidencePacket,
    GroundingDecision,
)


def _make_item(
    chunk_id: str, content: str, rank: int
) -> EvaluatedEvidenceItem:
    """Helper to build EvaluatedEvidenceItem."""
    return EvaluatedEvidenceItem(
        chunk_id=chunk_id,
        document_id="doc-1",
        source_id="tanenbaum-so",
        source_title="Sistemas Operativos",
        author="Andrew S. Tanenbaum",
        page_start=100 + rank,
        grade=EvidenceGrade.UNASSESSED,
        content_hash="d" * 64,
        content=content,
        retrieval_score=1.0 / rank,
        retrieval_rank=rank,
        retrieval_method="HYBRID",
    )


def test_strict_bijection_manifest_and_context():
    """Manifest records match exactly [E#] citations in context block."""
    packer = ContextPacker()

    items = [
        _make_item("so:1", "Primer concepto.", 1),
        _make_item("so:2", "Segundo concepto.", 2),
        _make_item("so:3", "Tercer concepto.", 3),
    ]
    packet = EvidencePacket(
        original_query="Conceptos",
        normalized_query="Conceptos",
        notebook_id="fadena-so",
        grounding_decision=GroundingDecision.UNASSESSED_EVIDENCE,
        evidence_items=items,
        allowed_claims=[EpistemicClaimType.CITE_EVIDENCE],
    )

    packaged = packer.pack(packet, max_characters=4000)

    # Invariant 1: Bijection between manifest records and included units
    manifest_keys = set(packaged.citation_manifest.records.keys())
    assert manifest_keys == {"E1", "E2", "E3"}
    assert len(packaged.packaged_units) == 3

    # Invariant 2: Context contains exactly [E1], [E2], [E3]
    for cid in ["E1", "E2", "E3"]:
        assert f"[{cid}]" in packaged.formatted_context_block
    assert "[E4]" not in packaged.formatted_context_block

    # Invariant 3: Clean sequential numbering without gaps
    for idx, unit in enumerate(packaged.packaged_units, start=1):
        assert unit.citation.citation_id == f"E{idx}"

    assert packaged.was_truncated is False
    assert packaged.excluded_units_count == 0
    assert len(packaged.formatted_context_block) <= 4000
    assert packaged.total_characters == len(packaged.formatted_context_block)


def test_budget_truncation_on_chunk_boundary():
    """Units not fitting in budget are excluded whole without chunk slicing."""
    packer = ContextPacker()

    # Create items with known content sizes (~300 chars each)

    items = [
        _make_item("so:1", "A" * 200, 1),
        _make_item("so:2", "B" * 200, 2),
        _make_item("so:3", "C" * 200, 3),
        _make_item("so:4", "D" * 200, 4),
    ]
    packet = EvidencePacket(
        original_query="Budget query",
        normalized_query="Budget query",
        notebook_id="fadena-so",
        grounding_decision=GroundingDecision.UNASSESSED_EVIDENCE,
        evidence_items=items,
    )

    # Budget of 1200 chars will fit header and E1, E2, but not E3
    packaged = packer.pack(packet, max_characters=1200)

    assert packaged.was_truncated is True
    assert packaged.excluded_units_count >= 1
    assert len(packaged.packaged_units) == 2

    # Manifest contains ONLY E1 and E2! (No E3 or E4 phantom citations)
    assert set(packaged.citation_manifest.records.keys()) == {"E1", "E2"}
    assert "[E1]" in packaged.formatted_context_block
    assert "[E2]" in packaged.formatted_context_block
    assert "[E3]" not in packaged.formatted_context_block
    assert "[E4]" not in packaged.formatted_context_block

    # Strict invariant: context block never exceeds max_characters
    assert len(packaged.formatted_context_block) <= 1200
    assert packaged.total_characters <= 1200


def test_abstention_context_packaging():

    """Abstention produces empty manifest and clear pedagogical directive."""
    packer = ContextPacker()

    packet = EvidencePacket(
        original_query="Tema inexistente",
        normalized_query="Tema inexistente",
        notebook_id="fadena-so",
        grounding_decision=GroundingDecision.NO_CANDIDATES,
        evidence_items=[],
        abstention_required=True,
        abstention_reason="No candidates found in notebook.",
    )

    packaged = packer.pack(packet, max_characters=4000)

    assert packaged.citation_manifest.records == {}
    assert len(packaged.packaged_units) == 0
    assert "=== AVISO DE ABSTENCIÓN DOCUMENTAL ===" in (
        packaged.formatted_context_block
    )
    assert "No candidates found in notebook." in (
        packaged.formatted_context_block
    )
    assert "INSTRUCCIÓN AL TUTOR" in packaged.formatted_context_block
    assert len(packaged.formatted_context_block) <= 4000


def test_budget_below_header_block_fails():
    """Budget smaller than policy header raises BudgetError."""
    packer = ContextPacker()
    items = [_make_item("so:1", "Contenido", 1)]
    packet = EvidencePacket(
        original_query="Query",
        normalized_query="Query",
        notebook_id="fadena-so",
        grounding_decision=GroundingDecision.UNASSESSED_EVIDENCE,
        evidence_items=items,
        abstention_required=False,
    )
    with pytest.raises(BudgetError) as exc_info:
        packer.pack(packet, max_characters=50)
    assert "insufficient for mandatory policy header" in str(exc_info.value)
