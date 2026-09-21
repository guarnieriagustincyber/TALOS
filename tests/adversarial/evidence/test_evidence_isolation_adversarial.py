"""Adversarial and security isolation tests for Subsystem S4.1."""

from pathlib import Path
import pytest

from study_engine.context.packer import ContextPacker
from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.evidence_engine import (
    BudgetError,
    CurricularIsolationError,
    EvidenceAssessmentError,
    EvidenceGrade,
)
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.evidence.engine import EvidenceEngine
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def store_with_isolation(tmp_path: Path) -> KnowledgeStore:
    """Fixture providing initialized KnowledgeStore with linked source."""
    db_path = tmp_path / "isolation_store.db"
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
        filename="so.pdf",
        byte_size=1000,
        sha256="b" * 64,
        metadata={"role": "PRIMARY", "priority": 1},
    )
    store.save_source(
        SourceRecord(source_id="tanenbaum-so", manifest=manifest)
    )
    store.link_source_to_notebook("fadena-so", "tanenbaum-so")
    return store


def test_cross_notebook_candidate_injection_fails():
    """Evaluating candidate from foreign notebook raises isolation error."""
    engine = EvidenceEngine()
    foreign_candidate = ScoredCandidate(
        chunk_id="prog:tree:1",
        document_id="doc-prog",
        source_id="joyanes-fp",
        notebook_id="fadena-prog",  # Foreign notebook!
        rank=1,
        score=0.92,
        content="Arbol binario de busqueda.",
        retrieval_method="HYBRID",
    )

    with pytest.raises(CurricularIsolationError) as exc_info:
        engine.evaluate_candidates(
            query="¿Qué es un árbol?",
            notebook_id="fadena-so",  # Target notebook
            candidates=[foreign_candidate],
        )
    assert "belongs to foreign notebook 'fadena-prog'" in str(exc_info.value)


def test_unlinked_source_injection_fails(store_with_isolation: KnowledgeStore):
    """Unlinked source raises CurricularIsolationError when store given."""
    engine = EvidenceEngine()
    unlinked_candidate = ScoredCandidate(
        chunk_id="so:rogue:1",
        document_id="doc-rogue",
        source_id="unlinked-book",  # Not linked to fadena-so!
        notebook_id="fadena-so",
        rank=1,
        score=0.99,
        content="Rogue chunk content.",
        retrieval_method="HYBRID",
    )

    with pytest.raises(CurricularIsolationError) as exc_info:
        engine.evaluate_candidates(
            query="Test query",
            notebook_id="fadena-so",
            candidates=[unlinked_candidate],
            store=store_with_isolation,
        )
    assert "source 'unlinked-book' is not linked to notebook" in str(
        exc_info.value
    )


def test_assessed_grades_unknown_chunk_id_fails():
    """Assessed grades with chunks not in candidate list fails closed."""
    engine = EvidenceEngine()

    candidate = ScoredCandidate(
        chunk_id="so:proc:1",
        document_id="doc-1",
        source_id="tanenbaum-so",
        notebook_id="fadena-so",
        rank=1,
        score=0.85,
        content="Contenido valido.",
        retrieval_method="HYBRID",
    )

    with pytest.raises(EvidenceAssessmentError) as exc_info:
        engine.evaluate_candidates(
            query="Test",
            notebook_id="fadena-so",
            candidates=[candidate],
            assessed_grades={
                "so:proc:1": EvidenceGrade.DIRECT,
                "so:proc:UNKNOWN": EvidenceGrade.DIRECT,  # Phantom ID!
            },
        )
    assert "unknown chunk IDs" in str(exc_info.value)
    assert "so:proc:UNKNOWN" in str(exc_info.value)


def test_invalid_query_and_notebook_inputs():
    """Empty or whitespace-only queries and notebook IDs are rejected."""
    engine = EvidenceEngine()

    with pytest.raises(ValueError):
        engine.evaluate_candidates(
            query="",
            notebook_id="fadena-so",
            candidates=[],
        )

    with pytest.raises(ValueError):
        engine.evaluate_candidates(
            query="   \t\n  ",
            notebook_id="fadena-so",
            candidates=[],
        )

    with pytest.raises(ValueError):
        engine.evaluate_candidates(
            query="Valid query",
            notebook_id="",
            candidates=[],
        )


def test_negative_or_zero_budget_fails():
    """Zero or negative budget raises ValueError."""
    packer = ContextPacker()
    engine = EvidenceEngine()
    packet = engine.evaluate_candidates(
        query="Test query",
        notebook_id="fadena-so",
        candidates=[],
    )

    with pytest.raises(ValueError):
        packer.pack(packet, max_characters=0)

    with pytest.raises(ValueError):
        packer.pack(packet, max_characters=-50)


def test_budget_below_mandatory_policy_fails():
    """Budget smaller than minimal policy block raises BudgetError."""
    packer = ContextPacker()
    engine = EvidenceEngine()
    packet = engine.evaluate_candidates(
        query="Test query",
        notebook_id="fadena-so",
        candidates=[],
    )

    # Policy block is > 200 characters, so budget of 50 must raise BudgetError
    with pytest.raises(BudgetError) as exc_info:
        packer.pack(packet, max_characters=50)
    assert "insufficient for mandatory" in str(exc_info.value)


def test_giant_chunk_budget_overflow_excludes_without_splitting():
    """Giant chunk exceeding budget is cleanly excluded without splitting."""
    engine = EvidenceEngine()

    packer = ContextPacker()

    giant_content = "V" * 5000  # Exceeds max_characters
    candidate = ScoredCandidate(
        chunk_id="so:huge:1",
        document_id="doc-1",
        source_id="tanenbaum-so",
        notebook_id="fadena-so",
        rank=1,
        score=0.99,
        content=giant_content,
        retrieval_method="HYBRID",
    )

    packet = engine.evaluate_candidates(
        query="Giant test",
        notebook_id="fadena-so",
        candidates=[candidate],
    )

    # Package with 2000 chars limit
    packaged = packer.pack(packet, max_characters=2000)

    assert packaged.was_truncated is True
    assert packaged.excluded_units_count == 1
    assert len(packaged.packaged_units) == 0
    assert len(packaged.citation_manifest.records) == 0
    assert len(packaged.formatted_context_block) <= 2000
    assert "V" * 5000 not in packaged.formatted_context_block
    assert "(Ninguna evidencia cupo en el presupuesto disponible.)" in (
        packaged.formatted_context_block
    )
