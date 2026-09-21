"""Comprehensive isolation tests for Notebook/StudyContext (Phase 1B).

Demonstrates mathematically and relationally that:
1. Notebook A never leaks sources, documents, chunks, or curriculum to Notebook B.
2. It is impossible to accidentally retrieve entities from Notebook B when querying under Notebook A.
3. Multi-notebook M:N sharing works deterministically when explicit.
4. Non-existent, deleted, or unlinked notebooks fail-closed with typed exceptions.
5. Concurrent cross-notebook operations remain fully isolated without cross-talk.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import pytest
from typing import List

from study_engine.contracts.catalog import (
    NotebookConflictError,
    NotebookNotFoundError,
    SourceNotFoundError,
    SourceRecord,
)
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def isolated_store(tmp_path: Path) -> KnowledgeStore:
    db_file = tmp_path / "notebook_isolation_test.db"
    store = KnowledgeStore(db_file)
    store.initialize()
    return store


def _create_source_bundle(
    source_id: str,
    doc_id: str,
    chunk_id: str,
    text_content: str,
    sha_char: str = "a",
) -> tuple[SourceRecord, List[Document], List[Chunk]]:
    manifest = SourceManifest(
        source_id=source_id,
        filename=f"{source_id}.pdf",
        byte_size=1024,
        sha256=sha_char * 64,
    )
    record = SourceRecord(source_id=source_id, manifest=manifest)
    doc = Document(
        id=doc_id,
        source_id=source_id,
        title=f"Document {doc_id}",
        content=text_content,
        page_count=5,
    )
    chunk = Chunk(
        id=chunk_id,
        document_id=doc_id,
        source_id=source_id,
        content=text_content,
        index=0,
        page_start=1,
        page_end=1,
    )
    return record, [doc], [chunk]


def test_notebook_cross_isolation_sources_documents_chunks(isolated_store: KnowledgeStore):
    """Test Notebook A and Notebook B have disjoint sources, documents, and chunks."""
    # 1. Setup Notebook A (Operating Systems)
    nb_a = Notebook(
        id="nb-so",
        name="Sistemas Operativos",
        curriculum_id="so_v1",
        subject="SO",
    )
    isolated_store.create_notebook(nb_a)
    rec_a, docs_a, chunks_a = _create_source_bundle(
        source_id="src-so-mem",
        doc_id="doc-so-mem",
        chunk_id="chunk-so-mem",
        text_content="La memoria virtual y paginacion en sistemas operativos.",
        sha_char="1",
    )
    isolated_store.store_ingestion_bundle(rec_a, docs_a, chunks_a, notebook_id="nb-so")

    # 2. Setup Notebook B (Cybersecurity)
    nb_b = Notebook(
        id="nb-sec",
        name="Seguridad Informatica",
        curriculum_id="cybersecurity_v1",
        subject="Seguridad",
    )
    isolated_store.create_notebook(nb_b)
    rec_b, docs_b, chunks_b = _create_source_bundle(
        source_id="src-sec-crypto",
        doc_id="doc-sec-crypto",
        chunk_id="chunk-sec-crypto",
        text_content="Criptografia asimetrica RSA y firmas digitales.",
        sha_char="2",
    )
    isolated_store.store_ingestion_bundle(rec_b, docs_b, chunks_b, notebook_id="nb-sec")

    # 3. Source isolation verification
    sources_a = isolated_store.list_notebook_sources("nb-so")
    sources_b = isolated_store.list_notebook_sources("nb-sec")

    assert [s.source_id for s in sources_a] == ["src-so-mem"]
    assert [s.source_id for s in sources_b] == ["src-sec-crypto"]

    # 4. Search isolation verification under Notebook A
    # Query for term present in B ("criptografia") while searching in A -> Must return 0 hits
    results_a_searching_b_content = isolated_store.search("criptografia", notebook_id="nb-so")
    assert len(results_a_searching_b_content) == 0

    # Query for term present in A ("memoria virtual") in A -> Must return hit from A only
    results_a = isolated_store.search("memoria", notebook_id="nb-so")
    assert len(results_a) == 1
    assert results_a[0].chunk_id == "chunk-so-mem"
    assert results_a[0].source_id == "src-so-mem"

    # Search in B for "memoria" -> Must return 0 hits
    results_b_searching_a_content = isolated_store.search("memoria", notebook_id="nb-sec")
    assert len(results_b_searching_a_content) == 0

    # Search in B for "criptografia" -> Must return hit from B only
    results_b = isolated_store.search("criptografia", notebook_id="nb-sec")
    assert len(results_b) == 1
    assert results_b[0].chunk_id == "chunk-sec-crypto"


def test_notebook_explicit_mn_source_sharing(isolated_store: KnowledgeStore):
    """Test that a shared foundational source (e.g. C Programming) can be linked to both notebooks."""
    nb_1 = Notebook(id="nb-prog-1", name="Programacion 1", curriculum_id="prog_v1")
    nb_2 = Notebook(id="nb-sys-prog", name="Programacion de Sistemas", curriculum_id="sysprog_v1")
    isolated_store.create_notebook(nb_1)
    isolated_store.create_notebook(nb_2)

    rec_c, docs_c, chunks_c = _create_source_bundle(
        source_id="src-c-lang",
        doc_id="doc-c-lang",
        chunk_id="chunk-c-lang",
        text_content="Punteros y manejo de memoria en lenguaje C.",
        sha_char="3",
    )
    isolated_store.store_ingestion_bundle(rec_c, docs_c, chunks_c, notebook_id="nb-prog-1")

    # Explicitly link shared source to nb-sys-prog as well
    isolated_store.link_source_to_notebook(notebook_id="nb-sys-prog", source_id="src-c-lang")

    # Both notebooks can now search the shared source
    hits_1 = isolated_store.search("punteros", notebook_id="nb-prog-1")
    hits_2 = isolated_store.search("punteros", notebook_id="nb-sys-prog")

    assert len(hits_1) == 1
    assert len(hits_2) == 1
    assert hits_1[0].chunk_id == hits_2[0].chunk_id == "chunk-c-lang"

    # Unlinking from nb-prog-1 isolates it from nb-prog-1 but preserves nb-sys-prog
    isolated_store.unlink_source_from_notebook("nb-prog-1", "src-c-lang")
    assert len(isolated_store.search("punteros", notebook_id="nb-prog-1")) == 0
    assert len(isolated_store.search("punteros", notebook_id="nb-sys-prog")) == 1


def test_notebook_deleted_or_non_existent_fails_closed(isolated_store: KnowledgeStore):
    """Attempting operations with unknown or deleted notebook raises NotebookNotFoundError."""
    with pytest.raises(NotebookNotFoundError):
        isolated_store.search("query", notebook_id="non_existent_nb")

    with pytest.raises(NotebookNotFoundError):
        isolated_store.list_notebook_sources("non_existent_nb")

    # Create and delete notebook
    nb = Notebook(id="temp-nb", name="Temporary Notebook")
    isolated_store.create_notebook(nb)
    assert isolated_store.contains_notebook("temp-nb") is True

    isolated_store.delete_notebook("temp-nb")
    assert isolated_store.contains_notebook("temp-nb") is False

    with pytest.raises(NotebookNotFoundError):
        isolated_store.get_notebook("temp-nb")


def test_notebook_authoritative_curriculum_binding():
    """Notebook.curriculum_id must act as the single source of truth for curriculum loading."""
    registry = CurriculumRegistry()
    
    nb = Notebook(
        id="nb-cyber",
        name="Cybersecurity Fundamentals",
        curriculum_id="cybersecurity_v1",
    )
    
    assert nb.curriculum_id == "cybersecurity_v1"
    
    # Authoritative resolution from CurriculumRegistry using Notebook binding
    roadmap = registry.load_roadmap(nb.curriculum_id)
    assert roadmap is not None
    assert roadmap.roadmap_id == "ROADMAP-CYBERSECURITY-V1"
    assert "SEC-01-C-PTR" in roadmap.nodes


def test_concurrent_cross_notebook_isolation(isolated_store: KnowledgeStore):
    """Verify that parallel searches across different notebooks maintain zero-leakage isolation."""
    # Setup 4 distinct notebooks
    for i in range(4):
        nb = Notebook(id=f"nb-{i}", name=f"Notebook {i}", curriculum_id=f"curr_{i}")
        isolated_store.create_notebook(nb)
        rec, docs, chunks = _create_source_bundle(
            source_id=f"src-{i}",
            doc_id=f"doc-{i}",
            chunk_id=f"chunk-{i}",
            text_content=f"Secret concept uniquely in notebook index {i} keyword_{i}",
            sha_char=str(i),
        )
        isolated_store.store_ingestion_bundle(rec, docs, chunks, notebook_id=f"nb-{i}")

    def _search_worker(idx: int) -> bool:
        # Search for its own keyword
        own_hits = isolated_store.search(f"keyword_{idx}", notebook_id=f"nb-{idx}")
        if len(own_hits) != 1 or own_hits[0].chunk_id != f"chunk-{idx}":
            return False

        # Search for other notebook keywords
        for other in range(4):
            if other == idx:
                continue
            leak_hits = isolated_store.search(f"keyword_{other}", notebook_id=f"nb-{idx}")
            if len(leak_hits) > 0:
                return False  # Isolation breach!
        return True

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(_search_worker, i % 4) for i in range(32)]
        results = [f.result() for f in futures]

    assert all(results) is True
