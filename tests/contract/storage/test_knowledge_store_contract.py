"""Contract tests for KnowledgeStore exceptions and invariants."""

from pathlib import Path
import pytest

from study_engine.contracts.catalog import (
    NotebookConflictError,
    NotebookNotFoundError,
    SourceNotFoundError,
    SourceRecord,
)
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.storage.knowledge_store import KnowledgeStore


def test_knowledge_store_notebook_not_found(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "ks_not_found.db")
    store.initialize()

    with pytest.raises(NotebookNotFoundError):
        store.get_notebook("missing-nb")

    with pytest.raises(NotebookNotFoundError):
        store.get_notebook("")

    with pytest.raises(NotebookNotFoundError):
        store.list_notebook_sources("missing-nb")

    with pytest.raises(NotebookNotFoundError):
        store.link_source_to_notebook("missing-nb", "src-1")

    with pytest.raises(NotebookNotFoundError):
        store.search("query", notebook_id="missing-nb")

    with pytest.raises(NotebookNotFoundError):
        store.store_ingestion_bundle(
            record=SourceRecord(source_id="s1", manifest=SourceManifest(source_id="s1", filename="f.pdf", byte_size=10, sha256="1"*64)),
            documents=[],
            chunks=[],
            notebook_id="missing-nb",
        )


def test_knowledge_store_notebook_conflict(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "ks_conflict.db")
    store.initialize()

    nb1 = Notebook(id="nb-1", name="Original Name", subject="Subject 1")
    store.create_notebook(nb1)

    # Conflicting attributes for same ID
    nb2 = Notebook(id="nb-1", name="Divergent Name", subject="Subject 2")
    with pytest.raises(NotebookConflictError) as exc_info:
        store.create_notebook(nb2)
    assert "differ from already registered notebook" in str(exc_info.value)


def test_knowledge_store_link_source_not_found(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "ks_link_missing.db")
    store.initialize()

    store.create_notebook(Notebook(id="nb-1", name="N1"))

    with pytest.raises(SourceNotFoundError):
        store.link_source_to_notebook("nb-1", "missing-source")

    # Notebook with initial sources referencing missing source
    with pytest.raises(SourceNotFoundError):
        store.create_notebook(Notebook(id="nb-2", name="N2", sources=["missing-source-2"]))


def test_knowledge_store_invalid_type_arguments(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "ks_type.db")
    store.initialize()

    with pytest.raises(TypeError):
        store.create_notebook("not-a-notebook")  # type: ignore
