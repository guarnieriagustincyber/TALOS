"""Synthetic checks of the existing lexical entrypoint, not a Phase 2 experiment.

Exercise BM25, conjunctive/OR paths and reopen using temporary SQLite only.
No providers, pedagogy or student state. Source IDs are caller-supplied filters,
not evidence that this low-level entrypoint resolves normative L3 permissions.
"""

import hashlib
import sqlite3

import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def lexical_db(tmp_path):
    path = tmp_path / "synthetic-fts.db"
    store = KnowledgeStore(path)
    store.initialize()
    content = "Los punteros contienen direcciones."
    source_bytes = "\n".join([content] * 7).encode()
    try:
        for name in ("a", "b"):
            store.create_notebook(Notebook(id=name, name=f"Synthetic {name}"))
            for source in (f"allowed-{name}", f"other-{name}"):
                store.store_ingestion_bundle(
                    SourceRecord(source_id=source, manifest=SourceManifest(
                        source_id=source, filename="synthetic.txt", byte_size=len(source_bytes),
                        sha256=hashlib.sha256(source_bytes).hexdigest(),
                    )),
                    [Document(id=f"doc-{source}", source_id=source, title="Synthetic")],
                    [Chunk(id=f"{source}-{i}", source_id=source,
                           document_id=f"doc-{source}", content=content,
                           index=i, page_start=i + 1, page_end=i + 1) for i in range(7)],
                    notebook_id=name,
                )
    finally:
        store.close()
    return path


def forbid_nonlexical(*args, **kwargs):
    raise AssertionError("The lexical entrypoint must not invoke hybrid/vector retrieval")


@pytest.mark.parametrize("query", ["punteros", "punteros inexistente"])
@pytest.mark.parametrize("notebook_id", ["a", None])
def test_fts_bm25_repeats_after_reopen_without_writes(lexical_db, monkeypatch, query, notebook_id):
    expected = None
    for _ in range(2):
        store = KnowledgeStore(lexical_db)
        try:
            monkeypatch.setattr(store, "vector_search", forbid_nonlexical)
            monkeypatch.setattr(store, "search_hybrid", forbid_nonlexical)
            conn = store.engine.connect()
            conn.execute("PRAGMA query_only=ON")
            before = conn.total_changes
            statements = []
            conn.set_trace_callback(statements.append)
            hits = store.fts_search(query, notebook_id=notebook_id, source_ids=["allowed-a"], limit=10)
            assert len(hits) == 7
            assert [hit.chunk_id for hit in hits] == [f"allowed-a-{i}" for i in range(7)]
            assert all(hit.source_id == "allowed-a" and hit.document_id == "doc-allowed-a" for hit in hits)
            if notebook_id:
                assert [hit.page_start for hit in hits] == list(range(1, 8))
            assert all(hit.content == "Los punteros contienen direcciones." for hit in hits)
            if "inexistente" in query:
                assert any(" OR " in statement for statement in statements)
            # Independent SQL oracle for these equal-content BM25 ties.
            rows = conn.execute(
                """SELECT c.id, -bm25(chunks_fts) FROM chunks_fts
                   JOIN chunks c ON c.rowid=chunks_fts.rowid
                   WHERE chunks_fts MATCH 'punteros' AND c.source_id='allowed-a'
                   ORDER BY -bm25(chunks_fts) DESC, c.document_id, c.pos_index LIMIT 10""",
            ).fetchall()
            assert [(hit.chunk_id, hit.score) for hit in hits] == rows
            assert store.fts_search(query, notebook_id=notebook_id, source_ids=["allowed-a"], limit=5) == hits[:5]
            snapshot = [hit.model_dump() for hit in hits]
            if expected is None:
                expected = snapshot
            assert snapshot == expected
            assert conn.total_changes == before
        finally:
            store.close()


def test_explicit_empty_source_filter_returns_no_hits(lexical_db, monkeypatch):
    store = KnowledgeStore(lexical_db)
    try:
        monkeypatch.setattr(store, "vector_search", forbid_nonlexical)
        monkeypatch.setattr(store, "search_hybrid", forbid_nonlexical)
        assert store.fts_search("punteros", notebook_id="a", source_ids=[]) == []
        assert store.fts_search("punteros inexistente", notebook_id="a", source_ids=[]) == []
        assert store.fts_search("", notebook_id="a", source_ids=["allowed-a"]) == []
    finally:
        store.close()


def test_fts_reads_committed_snapshot_while_another_connection_writes(lexical_db):
    store = KnowledgeStore(lexical_db)
    writer = sqlite3.connect(lexical_db)
    try:
        conn = store.engine.connect()
        conn.execute("PRAGMA busy_timeout=100")
        writer.execute("BEGIN IMMEDIATE")
        writer.execute("UPDATE chunks SET content='Contenido no confirmado' WHERE id='allowed-a-0'")
        hits = store.fts_search("punteros", notebook_id="a", source_ids=["allowed-a"])
        assert [hit.chunk_id for hit in hits] == [f"allowed-a-{i}" for i in range(7)]
        assert all(hit.content == "Los punteros contienen direcciones." for hit in hits)
        # The caller's write transaction remains active; retrieval did not commit it.
        assert writer.in_transaction
    finally:
        writer.rollback()
        writer.close()
        store.close()


def test_fts_file_uri_read_only_preserves_database_and_blocks_writes(lexical_db):
    seed = sqlite3.connect(lexical_db)
    try:
        seed.execute("UPDATE chunks SET content='punteros punteros direcciones' WHERE id='allowed-a-0'")
        seed.commit()
        seed.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        seed.execute("PRAGMA journal_mode=DELETE")
    finally:
        seed.close()
    before = {p.name: p.read_bytes() for p in lexical_db.parent.iterdir() if p.is_file()}
    store = KnowledgeStore(lexical_db.as_uri() + "?mode=ro")
    try:
        conn = store.engine.connect()
        assert store.engine.connect() is conn
        assert conn.execute("PRAGMA query_only").fetchone()[0] == 0
        hits = store.fts_search("punteros", notebook_id="a", source_ids=["allowed-a"], limit=5)
        oracle = conn.execute(
            """SELECT c.id, -bm25(chunks_fts) FROM chunks_fts
               JOIN chunks c ON c.rowid=chunks_fts.rowid
               WHERE chunks_fts MATCH 'punteros' AND c.source_id='allowed-a'
               ORDER BY -bm25(chunks_fts) DESC, c.document_id, c.pos_index LIMIT 5""",
        ).fetchall()
        assert len(hits) == 5
        assert [(h.chunk_id, h.score) for h in hits] == oracle
        assert hits[0].chunk_id == "allowed-a-0" and hits[0].score > hits[1].score
        assert {h.source_id for h in hits} == {"allowed-a"}
        assert store.fts_search("punteros", notebook_id="b", source_ids=["allowed-a"]) == []
        assert store.fts_search("punteros", notebook_id="a", source_ids=[]) == []
        assert store.fts_search("punteros", notebook_id="a", source_ids=["allowed-a"], document_id="doc-other-a") == []
        assert [h.chunk_id for h in store.fts_search(
            "punteros", source_id="allowed-a", limit=5,
        )] == [h.chunk_id for h in hits]
        conn.execute("BEGIN DEFERRED")
        try:
            with pytest.raises(sqlite3.OperationalError, match="readonly"):
                conn.execute("DELETE FROM chunks WHERE id='allowed-a-0'")
        finally:
            conn.rollback()
        assert conn.total_changes == 0
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    finally:
        store.close()
    assert {p.name: p.read_bytes() for p in lexical_db.parent.iterdir() if p.is_file()} == before
    missing_path = lexical_db.parent / "absent" / "missing.db"
    missing_store = KnowledgeStore(missing_path.as_uri() + "?mode=ro")
    try:
        with pytest.raises(sqlite3.OperationalError, match="unable to open"):
            missing_store.engine.connect()
        assert not missing_path.parent.exists()
    finally:
        missing_store.close()
    with pytest.raises(ValueError, match="Ambiguous"):
        KnowledgeStore(lexical_db.as_uri() + "?mode=ro&mode=rw")
