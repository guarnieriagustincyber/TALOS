"""Unit tests for EvidenceEngine in Subsystem S4.1."""

from pathlib import Path
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.enums import SourceRole
from study_engine.contracts.evidence_engine import (
    EpistemicClaimType,
    EvidenceGrade,
    GroundingDecision,
)
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.evidence.engine import EvidenceEngine
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def store_with_metadata(tmp_path: Path) -> KnowledgeStore:
    """Fixture providing initialized KnowledgeStore with linked source."""
    db_path = tmp_path / "metadata_store.db"
    store = KnowledgeStore(db_path)
    store.initialize()

    nb = Notebook(
        id="fadena-so",
        name="Sistemas Operativos",
        description="SO course",
        subject="Computer Science",
    )
    store.create_notebook(nb)

    manifest = SourceManifest(
        source_id="tanenbaum-so",
        filename="so_tanenbaum.pdf",
        byte_size=1000,
        sha256="c" * 64,
        metadata={
            "role": "PRIMARY",
            "priority": 1,
            "author": "Andrew S. Tanenbaum",
        },
    )
    store.save_source(
        SourceRecord(source_id="tanenbaum-so", manifest=manifest)
    )
    store.link_source_to_notebook("fadena-so", "tanenbaum-so")
    return store


def test_query_normalization_deterministic():
    """Query normalization uses NFC and collapses whitespace."""
    engine = EvidenceEngine()

    packet = engine.evaluate_candidates(
        query="  ¿Qué    es    un   \t proceso?  \n ",
        notebook_id="fadena-so",
        candidates=[],
    )
    assert packet.original_query == "  ¿Qué    es    un   \t proceso?  \n "
    assert packet.normalized_query == "¿Qué es un proceso?"


def test_no_candidates_produces_no_candidates_decision():
    """Empty candidate list yields NO_CANDIDATES and requires abstention."""
    engine = EvidenceEngine()
    packet = engine.evaluate_candidates(
        query="Explain paging",
        notebook_id="fadena-so",
        candidates=[],
    )
    assert packet.grounding_decision == GroundingDecision.NO_CANDIDATES
    assert packet.abstention_required is True
    assert packet.abstention_reason is not None
    assert len(packet.allowed_claims) == 0
    assert len(packet.unsupported_claims) == len(EpistemicClaimType)


def test_unassessed_candidates_default_safely():
    """Unassessed candidates default to UNASSESSED without score guessing."""
    engine = EvidenceEngine()
    c1 = ScoredCandidate(
        chunk_id="so:proc:1",
        document_id="doc-1",
        source_id="tanenbaum-so",
        notebook_id="fadena-so",
        rank=1,
        score=0.99,  # High score does NOT make it DIRECT!
        content="Un proceso es un programa en ejecución.",
        retrieval_method="HYBRID",
    )
    c2 = ScoredCandidate(
        chunk_id="so:proc:2",
        document_id="doc-1",
        source_id="tanenbaum-so",
        notebook_id="fadena-so",
        rank=2,
        score=0.51,  # Low score does NOT make it CONTEXTUAL!
        content="El concepto de proceso es clave.",
        retrieval_method="HYBRID",
    )

    packet = engine.evaluate_candidates(
        query="¿Qué es un proceso?",
        notebook_id="fadena-so",
        candidates=[c1, c2],
    )

    assert packet.grounding_decision == GroundingDecision.UNASSESSED_EVIDENCE
    assert packet.abstention_required is False
    assert packet.has_full_provenance is False
    for item in packet.evidence_items:
        assert item.grade == EvidenceGrade.UNASSESSED
        # Default invariants: role & priority are None when store omitted
        assert item.source_role is None
        assert item.priority is None

    # Allowed claims: citing allowed; canonical definition disallowed
    assert EpistemicClaimType.CITE_EVIDENCE in packet.allowed_claims
    assert (
        EpistemicClaimType.CANONICAL_DEFINITION in packet.unsupported_claims
    )


def test_assessed_grades_supported_decision():
    """Explicit DIRECT assessment promotes packet to SUPPORTED."""
    engine = EvidenceEngine()
    c1 = ScoredCandidate(
        chunk_id="so:proc:1",
        document_id="doc-1",
        source_id="tanenbaum-so",
        notebook_id="fadena-so",
        rank=1,
        score=0.90,
        content="Definición canónica de proceso.",
        retrieval_method="HYBRID",
    )

    packet = engine.evaluate_candidates(
        query="Definición",
        notebook_id="fadena-so",
        candidates=[c1],
        assessed_grades={"so:proc:1": EvidenceGrade.DIRECT},
    )

    assert packet.grounding_decision == GroundingDecision.SUPPORTED
    assert packet.abstention_required is False
    assert (
        EpistemicClaimType.DIRECT_FACTUAL_ASSERTION in packet.allowed_claims
    )
    assert EpistemicClaimType.CANONICAL_DEFINITION in packet.allowed_claims
    assert len(packet.unsupported_claims) == 0


def test_assessed_grades_partially_supported_decision():
    """Explicit CONTEXTUAL assessment sets PARTIALLY_SUPPORTED."""
    engine = EvidenceEngine()
    c1 = ScoredCandidate(
        chunk_id="so:proc:1",
        document_id="doc-1",
        source_id="tanenbaum-so",
        notebook_id="fadena-so",
        rank=1,
        score=0.90,
        content="Contexto general histórico de SO.",
        retrieval_method="HYBRID",
    )

    packet = engine.evaluate_candidates(
        query="Historia",
        notebook_id="fadena-so",
        candidates=[c1],
        assessed_grades={"so:proc:1": EvidenceGrade.CONTEXTUAL},
    )

    assert packet.grounding_decision == GroundingDecision.PARTIALLY_SUPPORTED
    assert packet.abstention_required is False
    assert (
        EpistemicClaimType.CONTEXTUAL_EXPLANATION in packet.allowed_claims
    )
    assert (
        EpistemicClaimType.CANONICAL_DEFINITION in packet.unsupported_claims
    )
    assert (
        EpistemicClaimType.DIRECT_FACTUAL_ASSERTION
        in packet.unsupported_claims
    )


def test_retrieval_ranking_is_preserved_not_priority_hijacked(
    store_with_metadata: KnowledgeStore,
):
    """Retrieval order is strictly preserved; priority does not reorder."""
    engine = EvidenceEngine()

    c1 = ScoredCandidate(

        chunk_id="so:proc:1",
        document_id="doc-1",
        source_id="tanenbaum-so",
        notebook_id="fadena-so",
        rank=1,
        score=0.95,
        content="Top 1 content",
        retrieval_method="HYBRID",
    )
    c2 = ScoredCandidate(
        chunk_id="so:proc:2",
        document_id="doc-1",
        source_id="tanenbaum-so",
        notebook_id="fadena-so",
        rank=2,
        score=0.85,
        content="Top 2 content",
        retrieval_method="HYBRID",
    )

    packet = engine.evaluate_candidates(
        query="Order test",
        notebook_id="fadena-so",
        candidates=[c1, c2],
        store=store_with_metadata,
    )

    assert packet.has_full_provenance is True
    assert len(packet.evidence_items) == 2
    assert packet.evidence_items[0].chunk_id == "so:proc:1"
    assert packet.evidence_items[1].chunk_id == "so:proc:2"
    assert packet.evidence_items[0].source_role == SourceRole.PRIMARY
    assert packet.evidence_items[0].priority == 1
    assert packet.evidence_items[0].author == "Andrew S. Tanenbaum"


def test_invalid_metadata_safely_defaulted_to_none():
    """Invalid roles and priority strings safely fall back to None."""
    engine = EvidenceEngine()
    c = ScoredCandidate(
        chunk_id="so:proc:1",
        document_id="doc-1",
        source_id="tanenbaum-so",
        notebook_id="fadena-so",
        rank=1,
        score=0.9,
        content="Content",
        retrieval_method="HYBRID",
        metadata={
            "source_role": "INVALID_ROLE",
            "priority": "not_an_int",
        },
    )
    packet = engine.evaluate_candidates(
        query="Metadata test",
        notebook_id="fadena-so",
        candidates=[c],
    )
    item = packet.evidence_items[0]
    assert item.source_role is None
    assert item.priority is None


def test_invalid_store_metadata_safely_defaulted_to_none(tmp_path: Path):
    """Store manifest with invalid metadata gracefully defaults to None."""
    db_path = tmp_path / "bad_meta_store.db"
    store = KnowledgeStore(db_path)
    store.initialize()

    nb = Notebook(
        id="fadena-so",
        name="SO",
        description="SO",
        subject="CS",
    )
    store.create_notebook(nb)

    manifest = SourceManifest(
        source_id="tanenbaum-so",
        filename="so.pdf",
        byte_size=100,
        sha256="f" * 64,
        metadata={
            "role": "NOT_A_VALID_ROLE",
            "priority": "not_an_int",
        },
    )
    store.save_source(
        SourceRecord(source_id="tanenbaum-so", manifest=manifest)
    )
    store.link_source_to_notebook("fadena-so", "tanenbaum-so")

    engine = EvidenceEngine()
    c = ScoredCandidate(
        chunk_id="so:1",
        document_id="d1",
        source_id="tanenbaum-so",
        notebook_id="fadena-so",
        rank=1,
        score=0.9,
        content="Content",
        retrieval_method="HYBRID",
    )
    packet = engine.evaluate_candidates(
        query="Query",
        notebook_id="fadena-so",
        candidates=[c],
        store=store,
    )
    item = packet.evidence_items[0]
    assert item.source_role is None
    assert item.priority is None
