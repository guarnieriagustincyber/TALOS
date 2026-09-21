"""Contract tests for SQLite relational constraints and cascade integrity."""

from pathlib import Path
import sqlite3
import pytest

from study_engine.storage.sqlite_engine import SQLiteStorageEngine


def setup_engine(tmp_path: Path) -> SQLiteStorageEngine:
    db_file = tmp_path / "contract_store.db"
    engine = SQLiteStorageEngine(db_file)
    engine.initialize_schema()
    return engine


def test_foreign_key_rejects_document_with_missing_source(tmp_path: Path):
    engine = setup_engine(tmp_path)

    with pytest.raises(sqlite3.IntegrityError):
        with engine.transaction() as conn:
            conn.execute(
                """
                INSERT INTO documents (id, source_id, title, created_at)
                VALUES (?, ?, ?, ?);
                """,
                ("doc-1", "non-existent-source", "Document Title", "2026-09-02T00:00:00Z"),
            )


def test_foreign_key_rejects_chunk_with_missing_document_or_source(tmp_path: Path):
    engine = setup_engine(tmp_path)

    # Insert valid source
    with engine.transaction() as conn:
        conn.execute(
            """
            INSERT INTO sources (source_id, title, role, priority, created_at)
            VALUES (?, ?, ?, ?, ?);
            """,
            ("src-1", "Joyanes", "PRIMARY", 1, "2026-09-02T00:00:00Z"),
        )

    # Fail: document does not exist
    with pytest.raises(sqlite3.IntegrityError):
        with engine.transaction() as conn:
            conn.execute(
                """
                INSERT INTO chunks (id, document_id, source_id, content, pos_index)
                VALUES (?, ?, ?, ?, ?);
                """,
                ("chunk-1", "missing-doc", "src-1", "Content", 0),
            )


def test_cascade_deletion_from_source_deletes_documents_and_chunks(tmp_path: Path):
    engine = setup_engine(tmp_path)

    with engine.transaction() as conn:
        # Insert Source
        conn.execute(
            "INSERT INTO sources (source_id, title, role, priority, created_at) VALUES (?, ?, ?, ?, ?);",
            ("src-joyanes", "Joyanes", "PRIMARY", 1, "2026-09-02T00:00:00Z"),
        )
        # Insert Document
        conn.execute(
            "INSERT INTO documents (id, source_id, title, created_at) VALUES (?, ?, ?, ?);",
            ("doc-cap1", "src-joyanes", "Capítulo 1", "2026-09-02T00:00:00Z"),
        )
        # Insert Chunks
        conn.execute(
            "INSERT INTO chunks (id, document_id, source_id, content, pos_index) VALUES (?, ?, ?, ?, ?);",
            ("chunk-01", "doc-cap1", "src-joyanes", "Chunk 1 Content", 0),
        )
        conn.execute(
            "INSERT INTO chunks (id, document_id, source_id, content, pos_index) VALUES (?, ?, ?, ?, ?);",
            ("chunk-02", "doc-cap1", "src-joyanes", "Chunk 2 Content", 1),
        )

    # Verify everything was inserted
    with engine.transaction() as conn:
        assert conn.execute("SELECT COUNT(*) FROM documents;").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM chunks;").fetchone()[0] == 2

    # Delete Source -> CASCADE should delete Document and Chunks
    with engine.transaction() as conn:
        conn.execute("DELETE FROM sources WHERE source_id = 'src-joyanes';")

    # Verify cascade
    with engine.transaction() as conn:
        assert conn.execute("SELECT COUNT(*) FROM sources;").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM documents;").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM chunks;").fetchone()[0] == 0


def test_notebook_sources_association_and_cascade(tmp_path: Path):
    engine = setup_engine(tmp_path)

    with engine.transaction() as conn:
        conn.execute(
            "INSERT INTO notebooks (id, name, created_at) VALUES (?, ?, ?);",
            ("nb-fadena", "FADENA Redes", "2026-09-02T00:00:00Z"),
        )
        conn.execute(
            "INSERT INTO sources (source_id, title, role, priority, created_at) VALUES (?, ?, ?, ?, ?);",
            ("src-tanenbaum", "Tanenbaum Redes", "PRIMARY", 1, "2026-09-02T00:00:00Z"),
        )
        conn.execute(
            "INSERT INTO notebook_sources (notebook_id, source_id) VALUES (?, ?);",
            ("nb-fadena", "src-tanenbaum"),
        )

    # Deleting notebook cascades to notebook_sources association
    with engine.transaction() as conn:
        conn.execute("DELETE FROM notebooks WHERE id = 'nb-fadena';")

    with engine.transaction() as conn:
        # Notebook deleted
        assert conn.execute("SELECT COUNT(*) FROM notebooks;").fetchone()[0] == 0
        # Association deleted
        assert conn.execute("SELECT COUNT(*) FROM notebook_sources;").fetchone()[0] == 0
        # Underlying source is preserved
        assert conn.execute("SELECT COUNT(*) FROM sources;").fetchone()[0] == 1
