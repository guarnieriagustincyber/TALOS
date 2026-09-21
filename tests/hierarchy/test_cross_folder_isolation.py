"""Tests verifying strict cross-folder isolation and boundary protection (Fase 5.7)."""

from datetime import datetime, timezone
import pytest

from study_engine.contracts.catalog import SourceManifest, SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.notebook import Notebook
from study_engine.hierarchy.folder import Folder
from study_engine.hierarchy.folder_orchestrator import FolderOrchestrator
from study_engine.hierarchy.scope_resolver import ScopeResolver, ScopeType
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def isolated_setup():
    store = KnowledgeStore(":memory:")
    store.initialize()

    now = datetime.now(timezone.utc)
    folder_a = store.create_folder(Folder(id="folder_a", name="Materia A", parent_folder_id="folder_root", created_at=now, updated_at=now))
    folder_b = store.create_folder(Folder(id="folder_b", name="Materia B", parent_folder_id="folder_root", created_at=now, updated_at=now))

    # Notebook A in Folder A
    nb_a = store.create_notebook(Notebook(id="nb_a", name="Cuaderno A", folder_id="folder_a"))
    # Notebook B in Folder B
    nb_b = store.create_notebook(Notebook(id="nb_b", name="Cuaderno B", folder_id="folder_b"))

    # Source and doc in Notebook A
    store.sources.save(SourceRecord(
        source_id="src_a",
        manifest=SourceManifest(source_id="src_a", filename="secret_a.txt", byte_size=10, sha256="0"*64, file_path=None),
    ))
    store.link_source_to_notebook("nb_a", "src_a")
    store.documents.save(Document(id="doc_a", source_id="src_a", title="Doc A", content="Confidencial A"))
    store.chunks.save_chunks([Chunk(id="chunk_a", document_id="doc_a", source_id="src_a", content="Clave secreta de la materia A", index=0)])

    # Source and doc in Notebook B
    store.sources.save(SourceRecord(
        source_id="src_b",
        manifest=SourceManifest(source_id="src_b", filename="secret_b.txt", byte_size=10, sha256="1"*64, file_path=None),
    ))
    store.link_source_to_notebook("nb_b", "src_b")
    store.documents.save(Document(id="doc_b", source_id="src_b", title="Doc B", content="Confidencial B"))
    store.chunks.save_chunks([Chunk(id="chunk_b", document_id="doc_b", source_id="src_b", content="Clave secreta de la materia B", index=0)])

    return store, folder_a, folder_b, nb_a, nb_b


def test_folder_orchestrator_does_not_leak_cross_folder_notebooks(isolated_setup):
    """FolderOrchestrator for Folder A strictly sees only notebooks in Folder A."""
    store, folder_a, folder_b, nb_a, nb_b = isolated_setup

    orch_a = FolderOrchestrator(folder_id="folder_a", knowledge_store=store)
    orch_b = FolderOrchestrator(folder_id="folder_b", knowledge_store=store)

    nbs_a = orch_a.list_notebooks()
    nbs_b = orch_b.list_notebooks()

    assert len(nbs_a) == 1
    assert nbs_a[0].id == "nb_a"

    assert len(nbs_b) == 1
    assert nbs_b[0].id == "nb_b"


def test_scope_resolver_enforces_exact_parent_folder(isolated_setup):
    """ScopeResolver correctly pairs notebook with its authoritative folder."""
    store, folder_a, folder_b, nb_a, nb_b = isolated_setup
    resolver = ScopeResolver(store)

    scope_a = resolver.resolve(ScopeType.NOTEBOOK, "nb_a")
    assert scope_a.folder_id == "folder_a"
    assert scope_a.folder_id != "folder_b"

    scope_b = resolver.resolve(ScopeType.NOTEBOOK, "nb_b")
    assert scope_b.folder_id == "folder_b"
    assert scope_b.folder_id != "folder_a"


def test_lexical_retrieval_isolation_between_folders(isolated_setup):
    """Lexical search in notebook A cannot match chunks from notebook B in another folder."""
    store, folder_a, folder_b, nb_a, nb_b = isolated_setup

    # Search for "secreta" in notebook A -> matches chunk_a only
    results_a = store.search(query="secreta", notebook_id="nb_a")
    assert len(results_a) == 1
    assert results_a[0].chunk_id == "chunk_a"
    assert "materia A" in results_a[0].snippet

    # Search for "secreta" in notebook B -> matches chunk_b only
    results_b = store.search(query="secreta", notebook_id="nb_b")
    assert len(results_b) == 1
    assert results_b[0].chunk_id == "chunk_b"
    assert "materia B" in results_b[0].snippet
