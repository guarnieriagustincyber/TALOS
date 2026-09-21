"""Unit tests for SQLiteStorageEngine in S2.1."""

from pathlib import Path
import sqlite3
import pytest

from study_engine.storage.sqlite_engine import SQLiteStorageEngine


def test_sqlite_engine_in_memory_initialization():
    engine = SQLiteStorageEngine(":memory:")
    engine.initialize_schema()

    conn = engine.connect()
    cursor = conn.cursor()

    # Check foreign keys enabled
    fk = cursor.execute("PRAGMA foreign_keys;").fetchone()[0]
    assert fk == 1

    # Check busy timeout
    timeout = cursor.execute("PRAGMA busy_timeout;").fetchone()[0]
    assert timeout == 5000

    # Verify all tables exist
    tables = [
        row[0]
        for row in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        ).fetchall()
    ]
    assert "notebooks" in tables
    assert "sources" in tables
    assert "notebook_sources" in tables
    assert "documents" in tables
    assert "chunks" in tables

    engine.close()


def test_sqlite_engine_disk_initialization_and_wal(tmp_path: Path):
    db_file = tmp_path / "test_store.db"
    engine = SQLiteStorageEngine(db_file)
    engine.initialize_schema()

    conn = engine.connect()
    cursor = conn.cursor()

    # Check WAL mode on disk
    journal_mode = cursor.execute("PRAGMA journal_mode;").fetchone()[0].lower()
    assert journal_mode == "wal"

    # Check foreign keys
    fk = cursor.execute("PRAGMA foreign_keys;").fetchone()[0]
    assert fk == 1

    conn.close()


def test_schema_initialization_is_idempotent(tmp_path: Path):
    db_file = tmp_path / "idempotent.db"
    engine = SQLiteStorageEngine(db_file)

    # Calling initialize_schema multiple times should not error or duplicate tables
    engine.initialize_schema()
    engine.initialize_schema()
    engine.initialize_schema()

    with engine.transaction() as conn:
        cursor = conn.cursor()
        count = cursor.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='chunks';"
        ).fetchone()[0]
        assert count == 1


def test_transaction_commit_on_success(tmp_path: Path):
    db_file = tmp_path / "commit.db"
    engine = SQLiteStorageEngine(db_file)
    engine.initialize_schema()

    with engine.transaction() as conn:
        conn.execute(
            "INSERT INTO notebooks (id, name, created_at) VALUES (?, ?, ?);",
            ("nb-1", "Notebook 1", "2026-09-02T00:00:00Z"),
        )

    # Reconnect and verify data was committed
    with engine.transaction() as conn:
        row = conn.execute("SELECT name FROM notebooks WHERE id = 'nb-1';").fetchone()
        assert row is not None
        assert row[0] == "Notebook 1"


def test_transaction_rollback_on_error(tmp_path: Path):
    db_file = tmp_path / "rollback.db"
    engine = SQLiteStorageEngine(db_file)
    engine.initialize_schema()

    with pytest.raises(RuntimeError):
        with engine.transaction() as conn:
            conn.execute(
                "INSERT INTO notebooks (id, name, created_at) VALUES (?, ?, ?);",
                ("nb-fail", "Should Rollback", "2026-09-02T00:00:00Z"),
            )
            raise RuntimeError("Simulated crash inside transaction")

    # Verify data was rolled back and does not exist
    with engine.transaction() as conn:
        row = conn.execute("SELECT name FROM notebooks WHERE id = 'nb-fail';").fetchone()
        assert row is None


def test_schema_version_tracking(tmp_path: Path):
    db_file = tmp_path / "version.db"
    engine = SQLiteStorageEngine(db_file)
    assert engine.get_schema_version() == 0

    engine.initialize_schema()
    assert engine.get_schema_version() == engine.SCHEMA_VERSION

    # Test explicit version setting
    engine.set_schema_version(42)
    assert engine.get_schema_version() == 42


def test_nested_savepoint_rollback_on_error(tmp_path: Path):
    db_file = tmp_path / "nested_rollback.db"
    engine = SQLiteStorageEngine(db_file)
    engine.initialize_schema()

    with engine.transaction() as conn:
        conn.execute("INSERT INTO notebooks (id, name, created_at) VALUES ('outer-1', 'Outer', 'now');")

        # Nested transaction that fails and rolls back to savepoint
        with pytest.raises(ValueError):
            with engine.transaction() as nested_conn:
                nested_conn.execute("INSERT INTO notebooks (id, name, created_at) VALUES ('inner-1', 'Inner', 'now');")
                raise ValueError("Nested failure")

        # Outer transaction should still be able to commit outer-1
        conn.execute("INSERT INTO notebooks (id, name, created_at) VALUES ('outer-2', 'Outer 2', 'now');")

    with engine.transaction() as conn:
        assert conn.execute("SELECT name FROM notebooks WHERE id = 'outer-1';").fetchone() is not None
        assert conn.execute("SELECT name FROM notebooks WHERE id = 'inner-1';").fetchone() is None
        assert conn.execute("SELECT name FROM notebooks WHERE id = 'outer-2';").fetchone() is not None


