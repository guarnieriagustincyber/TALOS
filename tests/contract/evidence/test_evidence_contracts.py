"""Contract tests for Subsystem S4.1 Evidence Engine data models."""

import pytest
from pydantic import ValidationError

from study_engine.contracts.enums import SourceRole
from study_engine.contracts.evidence_engine import (
    CitationManifest,
    CitationRecord,
    EpistemicClaimType,
    EvaluatedEvidenceItem,
    EvidenceGrade,
    EvidencePacket,
    GroundingDecision,
    PackagedContext,
    PackagedEvidenceUnit,
)

VALID_HASH = "a" * 64


def test_citation_record_immutability():
    """Verify CitationRecord is strictly immutable (frozen)."""
    rec = CitationRecord(
        citation_id="E1",
        chunk_id="so:proc:1",
        document_id="doc-1",
        source_id="tanenbaum-so",
        source_title="Sistemas Operativos",
        content_hash=VALID_HASH,
    )
    # Default invariants: role and priority are None (not PRIMARY/1)
    assert rec.source_role is None
    assert rec.priority is None
    assert rec.grade == EvidenceGrade.UNASSESSED

    with pytest.raises((ValidationError, TypeError)):
        rec.source_title = "Modified Title"  # type: ignore[misc]


def test_citation_record_hash_validation():
    """Verify content_hash must be valid 64-char hex string."""
    # Invalid length
    with pytest.raises(ValidationError):
        CitationRecord(
            citation_id="E1",
            chunk_id="c1",
            document_id="d1",
            source_id="s1",
            source_title="Book",
            content_hash="short_hash",
        )

    # Invalid non-hex characters
    with pytest.raises(ValidationError):
        CitationRecord(
            citation_id="E1",
            chunk_id="c1",
            document_id="d1",
            source_id="s1",
            source_title="Book",
            content_hash="z" * 64,
        )


def test_evaluated_evidence_item_immutability():
    """Verify EvaluatedEvidenceItem is frozen."""
    item = EvaluatedEvidenceItem(
        chunk_id="c1",
        document_id="d1",
        source_id="s1",
        source_title="Title",
        content_hash=VALID_HASH,
        content="Evidence content text.",
        retrieval_score=0.95,
        retrieval_rank=1,
        retrieval_method="HYBRID",
    )
    assert item.grade == EvidenceGrade.UNASSESSED
    assert item.source_role is None
    assert item.priority is None

    with pytest.raises((ValidationError, TypeError)):
        item.content = "New content"  # type: ignore[misc]


def test_packaged_evidence_unit_immutability():
    """Verify PackagedEvidenceUnit is frozen and stores SourceRole."""
    rec = CitationRecord(
        citation_id="E1",
        chunk_id="c1",
        document_id="d1",
        source_id="s1",
        source_title="Title",
        source_role=SourceRole.PRIMARY,
        priority=1,
        content_hash=VALID_HASH,
    )
    unit = PackagedEvidenceUnit(
        citation=rec,
        content="Some content",
        retrieval_score=0.88,
        retrieval_rank=1,
        retrieval_method="HYBRID",
    )
    assert unit.citation.source_role == SourceRole.PRIMARY

    with pytest.raises((ValidationError, TypeError)):
        unit.content = "Changed"  # type: ignore[misc]


def test_evidence_packet_immutability():

    """Verify EvidencePacket is frozen."""
    packet = EvidencePacket(
        original_query="What is a process?",
        normalized_query="What is a process?",
        notebook_id="fadena-so",
        grounding_decision=GroundingDecision.NO_CANDIDATES,
        abstention_required=True,
    )
    with pytest.raises((ValidationError, TypeError)):
        packet.abstention_required = False  # type: ignore[misc]


def test_packaged_context_immutability():
    """Verify PackagedContext is frozen."""
    packet = EvidencePacket(
        original_query="What is a process?",
        normalized_query="What is a process?",
        notebook_id="fadena-so",
        grounding_decision=GroundingDecision.NO_CANDIDATES,
        abstention_required=True,
    )
    ctx = PackagedContext(
        packet=packet,
        citation_manifest=CitationManifest(records={}),
        formatted_context_block="Some prompt context",
        total_characters=19,
        epistemic_policy="Mandatory policy",
    )
    with pytest.raises((ValidationError, TypeError)):
        ctx.total_characters = 100  # type: ignore[misc]


def test_enums_integrity():
    """Verify closed domain enums retain all expected contract values."""
    assert EvidenceGrade.DIRECT.value == "DIRECT"
    assert EvidenceGrade.CONTEXTUAL.value == "CONTEXTUAL"
    assert EvidenceGrade.UNASSESSED.value == "UNASSESSED"

    assert GroundingDecision.SUPPORTED.value == "SUPPORTED"
    assert GroundingDecision.PARTIALLY_SUPPORTED.value == "PARTIALLY_SUPPORTED"
    assert GroundingDecision.UNASSESSED_EVIDENCE.value == "UNASSESSED_EVIDENCE"
    assert GroundingDecision.NO_CANDIDATES.value == "NO_CANDIDATES"

    assert EpistemicClaimType.DIRECT_FACTUAL_ASSERTION.value == (
        "DIRECT_FACTUAL_ASSERTION"
    )
    assert EpistemicClaimType.CANONICAL_DEFINITION.value == (
        "CANONICAL_DEFINITION"
    )
    assert EpistemicClaimType.CONTEXTUAL_EXPLANATION.value == (
        "CONTEXTUAL_EXPLANATION"
    )
    assert EpistemicClaimType.CITE_EVIDENCE.value == "CITE_EVIDENCE"
    assert EpistemicClaimType.QUALIFIED_EXPLANATION.value == (
        "QUALIFIED_EXPLANATION"
    )
