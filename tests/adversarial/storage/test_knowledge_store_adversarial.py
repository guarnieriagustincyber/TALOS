"""Adversarial security, asymmetric deletion and concurrency tests for KnowledgeStore."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.storage.knowledge_store import KnowledgeStore


def test_adversarial_empty_notebook_search_isolation(tmp_path: Path):
    """Ensure searching an existing but empty notebook returns [] without hallucinating other sources."""
    store = KnowledgeStore(tmp_path / "empty_nb.db")
    store.initialize()

    # Empty notebook
    store.create_notebook(Notebook(id="empty-nb", name="Empty Subject"))

    # Unrelated populated notebook with rich chunks
    store.create_notebook(Notebook(id="populated-nb", name="Populated Subject"))
    store.save_source(SourceRecord(
        source_id="src-pop",
        manifest=SourceManifest(source_id="src-pop", filename="p.pdf", byte_size=10, sha256="c"*64)
    ))
    store.link_source_to_notebook("populated-nb", "src-pop")
    store.save_document(Document(id="doc-pop", source_id="src-pop", title="Pop", content="Memoria y kernel"))
    store.save_chunks([
        Chunk(id="doc-pop:c0", document_id="doc-pop", source_id="src-pop", content="Memoria virtual y paginación del kernel", index=0)
    ])

    # Global search finds it
    assert len(store.search("kernel")) == 1

    # Populated notebook finds it
    assert len(store.search("kernel", notebook_id="populated-nb")) == 1

    # Empty notebook MUST return 0 results (strict isolation)
    assert store.search("kernel", notebook_id="empty-nb") == []


def test_adversarial_asymmetric_deletion_integrity(tmp_path: Path):
    """Verify that deleting a notebook NEVER deletes its sources, but deleting a source purges links."""
    store = KnowledgeStore(tmp_path / "asym_del.db")
    store.initialize()

    store.create_notebook(Notebook(id="nb-so", name="SO"))
    store.create_notebook(Notebook(id="nb-shared", name="Shared"))

    # Create source linked to both notebooks
    store.save_source(SourceRecord(
        source_id="src-tanenbaum",
        manifest=SourceManifest(source_id="src-tanenbaum", filename="t.pdf", byte_size=10, sha256="d"*64)
    ))

    store.link_source_to_notebook("nb-so", "src-tanenbaum")
    store.link_source_to_notebook("nb-shared", "src-tanenbaum")
    store.save_document(Document(id="doc-t", source_id="src-tanenbaum", title="T", content="Procesos"))
    store.save_chunks([
        Chunk(id="doc-t:c0", document_id="doc-t", source_id="src-tanenbaum", content="Gestión de procesos", index=0)
    ])

    # 1. Delete notebook nb-so
    assert store.delete_notebook("nb-so") is True

    # Invariant: source, document, chunks, FTS5 and nb-shared MUST remain 100% intact!
    assert store.sources.contains("src-tanenbaum") is True
    assert store.documents.contains("doc-t") is True
    assert store.chunks.contains("doc-t:c0") is True
    assert len(store.search("procesos")) == 1
    assert "src-tanenbaum" in store.get_notebook("nb-shared").sources

    # 2. Delete source src-tanenbaum
    assert store.delete_source("src-tanenbaum") is True

    # Invariant: source, document, chunks, FTS5 wiped, and link removed from nb-shared
    assert store.sources.contains("src-tanenbaum") is False
    assert store.documents.contains("doc-t") is False
    assert store.chunks.contains("doc-t:c0") is False
    assert len(store.search("procesos")) == 0
    assert store.get_notebook("nb-shared").sources == []


def test_adversarial_knowledge_store_concurrent_wal_access(tmp_path: Path):
    """Stress test: 15 workers concurrently creating notebooks, linking sources, and querying."""
    store = KnowledgeStore(tmp_path / "concurrent_ks.db")
    store.initialize()

    # Seed 5 base sources
    for i in range(5):
        store.save_source(SourceRecord(
            source_id=f"base-src-{i}",
            manifest=SourceManifest(source_id=f"base-src-{i}", filename=f"{i}.pdf", byte_size=10, sha256=f"{i:02x}"*32)
        ))

    errors = []

    def worker_task(worker_id: int):
        try:
            nb_id = f"nb-worker-{worker_id:02d}"
            store.create_notebook(Notebook(id=nb_id, name=f"Notebook {worker_id}"))

            # Link a shared source
            store.link_source_to_notebook(nb_id, f"base-src-{worker_id % 5}")

            # Verify link
            sources = store.list_notebook_sources(nb_id)
            assert len(sources) == 1

            # Stats check
            stats = store.get_stats()
            assert stats["schema_version"] >= 2
        except Exception as e:
            errors.append(f"Worker {worker_id} error: {type(e).__name__} {e}")

    with ThreadPoolExecutor(max_workers=15) as pool:
        futures = [pool.submit(worker_task, i) for i in range(30)]
        for f in futures:
            f.result()

    assert not errors, f"Concurrent KnowledgeStore errors: {errors}"
    assert len(store.list_notebooks()) == 30
