"""Unit tests for KnowledgeStore facade in S2.5."""

from pathlib import Path
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.enums import SourceRole
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.source import Source
from study_engine.storage.knowledge_store import KnowledgeStore


def test_knowledge_store_lifecycle_and_notebooks(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "ks_unit.db")
    store.initialize()

    # 1. Create Notebook
    nb = Notebook(
        id="fadena-so",
        name="Sistemas Operativos FADENA",
        description="Materia obligatoria tercer año",
        subject="Sistemas Operativos",
        metadata={"year": 2026},
    )
    created = store.create_notebook(nb)
    assert created.id == "fadena-so"
    assert created.name == nb.name
    assert store.contains_notebook("fadena-so") is True
    assert store.contains_notebook("missing") is False
    assert store.contains_notebook("") is False

    # 2. Idempotent creation
    idemp = store.create_notebook(nb)
    assert idemp.id == "fadena-so"

    # 3. Retrieve
    retrieved = store.get_notebook("fadena-so")
    assert retrieved.id == nb.id
    assert retrieved.metadata["year"] == 2026
    assert retrieved.sources == []

    # 4. List Notebooks
    all_nbs = store.list_notebooks()
    assert len(all_nbs) == 1
    assert all_nbs[0].id == "fadena-so"

    # 5. Delete Notebook
    assert store.delete_notebook("fadena-so") is True
    assert store.contains_notebook("fadena-so") is False
    assert store.delete_notebook("fadena-so") is False


def test_knowledge_store_linking_and_unlinking_sources(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "ks_links.db")
    store.initialize()

    # Create Notebook and 2 Sources
    store.create_notebook(Notebook(id="nb-1", name="Cuaderno 1"))
    store.save_source(SourceRecord(
        source_id="src-1",
        manifest=SourceManifest(source_id="src-1", filename="1.pdf", byte_size=10, sha256="1"*64)
    ))
    store.save_source(SourceRecord(
        source_id="src-2",
        manifest=SourceManifest(source_id="src-2", filename="2.pdf", byte_size=10, sha256="2"*64)
    ))

    # Link sources
    store.link_source_to_notebook("nb-1", "src-1")
    store.link_source_to_notebook("nb-1", "src-2")
    # Idempotent link
    store.link_source_to_notebook("nb-1", "src-1")

    # Verify sources in notebook
    nb_sources = store.list_notebook_sources("nb-1")
    assert len(nb_sources) == 2
    assert [s.source_id for s in nb_sources] == ["src-1", "src-2"]

    nb = store.get_notebook("nb-1")
    assert nb.sources == ["src-1", "src-2"]

    # Unlink
    assert store.unlink_source_from_notebook("nb-1", "src-1") is True
    assert store.unlink_source_from_notebook("nb-1", "src-1") is False

    nb_updated = store.get_notebook("nb-1")
    assert nb_updated.sources == ["src-2"]


def test_knowledge_store_ingestion_bundle_and_delegations(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "ks_bundle.db")
    store.initialize()

    store.create_notebook(Notebook(id="nb-so", name="SO"))

    record = SourceRecord(
        source_id="tanenbaum",
        manifest=SourceManifest(source_id="tanenbaum", filename="tanenbaum.pdf", byte_size=5000, sha256="a"*64),
        source=Source(source_id="tanenbaum", title="Modern Operating Systems", role=SourceRole.PRIMARY),
    )
    docs = [
        Document(id="tanenbaum:cap_01", source_id="tanenbaum", title="Cap 1", content="Memoria y procesos."),
        Document(id="tanenbaum:cap_02", source_id="tanenbaum", title="Cap 2", content="Sistemas de archivos."),
    ]
    chunks = [
        Chunk(id="tanenbaum:cap_01:c0", document_id="tanenbaum:cap_01", source_id="tanenbaum", content="Memoria virtual paginada", index=0),
        Chunk(id="tanenbaum:cap_02:c0", document_id="tanenbaum:cap_02", source_id="tanenbaum", content="Sistemas de archivos ext4", index=0),
    ]

    count = store.store_ingestion_bundle(record, docs, chunks, notebook_id="nb-so")
    assert count == 2

    # Direct delegations
    assert store.get_source("tanenbaum").source_id == "tanenbaum"
    assert store.find_source_by_sha256("a"*64) is not None
    assert store.find_source_by_sha256("0"*64) is None
    assert store.get_document("tanenbaum:cap_01").title == "Cap 1"
    assert len(store.list_documents("tanenbaum")) == 2
    assert len(store.list_documents(None)) == 2
    assert store.get_chunk("tanenbaum:cap_01:c0").content == "Memoria virtual paginada"
    assert len(store.list_chunks_by_document("tanenbaum:cap_01")) == 1

    # Notebook association
    assert "tanenbaum" in store.get_notebook("nb-so").sources


def test_knowledge_store_search_notebook_scoping(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "ks_search.db")
    store.initialize()

    # 2 notebooks
    store.create_notebook(Notebook(id="nb-so", name="SO"))
    store.create_notebook(Notebook(id="nb-algebra", name="Álgebra"))

    # Source 1 for SO
    store.save_source(SourceRecord(
        source_id="src-so",
        manifest=SourceManifest(source_id="src-so", filename="so.pdf", byte_size=10, sha256="1"*64)
    ))
    store.link_source_to_notebook("nb-so", "src-so")
    store.save_document(Document(id="doc-so", source_id="src-so", title="SO", content="Texto"))
    store.save_chunks([
        Chunk(id="doc-so:c0", document_id="doc-so", source_id="src-so", content="Algoritmos de memoria y paginación en SO.", index=0)
    ])

    # Source 2 for Algebra
    store.save_source(SourceRecord(
        source_id="src-alg",
        manifest=SourceManifest(source_id="src-alg", filename="alg.pdf", byte_size=10, sha256="2"*64)
    ))
    store.link_source_to_notebook("nb-algebra", "src-alg")
    store.save_document(Document(id="doc-alg", source_id="src-alg", title="Alg", content="Texto"))
    store.save_chunks([
        Chunk(id="doc-alg:c0", document_id="doc-alg", source_id="src-alg", content="Algoritmos matriciales y vectores en álgebra.", index=0)
    ])

    # Global search (both notebooks)
    global_results = store.search("algoritmos")
    assert len(global_results) == 2

    # Scoped search in SO notebook
    so_results = store.search("algoritmos", notebook_id="nb-so")
    assert len(so_results) == 1
    assert so_results[0].source_id == "src-so"
    assert "memoria" in so_results[0].content

    # Scoped search in Algebra notebook
    alg_results = store.search("algoritmos", notebook_id="nb-algebra")
    assert len(alg_results) == 1
    assert alg_results[0].source_id == "src-alg"
    assert "matriciales" in alg_results[0].content

    # Empty query or limit <= 0
    assert store.search("algoritmos", limit=0) == []
    assert store.search("   ", notebook_id="nb-so") == []


def test_knowledge_store_stats_and_integrity(tmp_path: Path):
    db_file = tmp_path / "ks_stats.db"
    store = KnowledgeStore(db_file)
    store.initialize()

    store.create_notebook(Notebook(id="nb-1", name="N1"))
    store.save_source(SourceRecord(
        source_id="src-1",
        manifest=SourceManifest(source_id="src-1", filename="1.pdf", byte_size=10, sha256="1"*64)
    ))
    store.save_document(Document(id="doc-1", source_id="src-1", title="D1", content="T1"))
    store.save_chunks([
        Chunk(id="doc-1:c0", document_id="doc-1", source_id="src-1", content="Chunk one", index=0)
    ])

    stats = store.get_stats()
    assert stats["notebooks_count"] == 1
    assert stats["sources_count"] == 1
    assert stats["documents_count"] == 1
    assert stats["chunks_count"] == 1
    assert stats["fts_chunks_count"] == 1
    assert stats["schema_version"] >= 2
    assert stats["db_size_bytes"] > 0

    assert store.verify_integrity() is True

    # 1. Simulate SQLite integrity corruption
    from contextlib import contextmanager

    class BadCursor:
        def execute(self, q): pass
        def fetchone(self): return ["corruption"]
    class BadConn:
        def cursor(self): return BadCursor()

    @contextmanager
    def mock_corrupt_tx():
        yield BadConn()

    orig_tx = store.engine.transaction
    store.engine.transaction = mock_corrupt_tx
    assert store.verify_integrity() is False

    # 2. Simulate FTS5 integrity failure
    class FtsFailCursor:
        def execute(self, q):
            if "integrity-check" in q:
                raise RuntimeError("FTS5 corrupt")
        def fetchone(self): return ["ok"]
    class FtsFailConn:
        def cursor(self): return FtsFailCursor()

    @contextmanager
    def mock_fts_fail_tx():
        yield FtsFailConn()

    store.engine.transaction = mock_fts_fail_tx
    assert store.verify_integrity() is False

    store.engine.transaction = orig_tx
    store.close()



def test_knowledge_store_create_notebook_with_initial_sources(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "ks_init_src.db")
    store.initialize()

    store.save_source(SourceRecord(
        source_id="src-valid",
        manifest=SourceManifest(source_id="src-valid", filename="v.pdf", byte_size=10, sha256="a"*64)
    ))

    nb = Notebook(id="nb-with-src", name="Notebook with Sources", sources=["src-valid"])
    created = store.create_notebook(nb)
    assert created.sources == ["src-valid"]
    assert store.get_notebook("nb-with-src").sources == ["src-valid"]

