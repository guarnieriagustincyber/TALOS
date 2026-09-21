"""Unit tests for RetrievalService facade in Subsystem S3 -> S4."""

from pathlib import Path
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.retrieval import (
    RetrievalStrategy,
    ScoredCandidate,
)
from study_engine.retrieval.service import RetrievalService
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def populated_store(tmp_path: Path) -> KnowledgeStore:
    """Fixture providing populated KnowledgeStore for retrieval tests."""
    db_path = tmp_path / "service_store.db"
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
        sha256="e" * 64,
        metadata={"role": "PRIMARY", "priority": 1},
    )
    store.save_source(
        SourceRecord(source_id="tanenbaum-so", manifest=manifest)
    )
    store.link_source_to_notebook("fadena-so", "tanenbaum-so")

    doc = Document(
        id="doc-1",
        source_id="tanenbaum-so",
        title="Procesos",
        content="Los procesos en ejecucion.",
    )
    store.save_document(doc)

    c1 = Chunk(
        id="so:proc:1",
        document_id="doc-1",
        source_id="tanenbaum-so",
        content="Un proceso es un programa en ejecucion con sus registros.",
        index=0,
    )
    store.save_chunks([c1])
    return store


def test_retrieval_service_facade(populated_store: KnowledgeStore):
    """RetrievalService provides transparent candidate retrieval."""
    service = RetrievalService(store=populated_store)
    assert service.store is populated_store

    candidates = service.retrieve_evidence(
        query="proceso ejecucion",
        notebook_id="fadena-so",
        top_k=5,
    )

    assert isinstance(candidates, list)
    assert len(candidates) >= 1
    assert isinstance(candidates[0], ScoredCandidate)
    assert candidates[0].chunk_id == "so:proc:1"
    assert candidates[0].notebook_id == "fadena-so"


def test_retrieval_service_strategy_override(populated_store: KnowledgeStore):
    """RetrievalService allows explicit strategy override."""
    service = RetrievalService(store=populated_store)
    candidates = service.retrieve_evidence(
        query="proceso",
        notebook_id="fadena-so",
        top_k=1,
        strategy=RetrievalStrategy.LEXICAL,
    )
    assert len(candidates) <= 1
