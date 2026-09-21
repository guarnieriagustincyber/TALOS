"""Adversarial and stress tests for SQLiteStorageEngine."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import pytest

from study_engine.storage.sqlite_engine import SQLiteStorageEngine


def test_adversarial_deeply_nested_directory_creation(tmp_path: Path):
    nested_path = tmp_path / "deeply" / "nested" / "sub" / "folder" / "store.db"
    assert not nested_path.parent.exists()

    engine = SQLiteStorageEngine(nested_path)
    engine.initialize_schema()

    assert nested_path.exists()
    assert nested_path.is_file()


def test_adversarial_sql_injection_attempt_in_parameters(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "sqli.db")
    engine.initialize_schema()

    # Attempt standard SQL injection payloads in parameters
    malicious_id = "nb-1'; DROP TABLE notebooks; --"
    malicious_name = "Robert'); DROP TABLE sources;--"

    with engine.transaction() as conn:
        conn.execute(
            "INSERT INTO notebooks (id, name, created_at) VALUES (?, ?, ?);",
            (malicious_id, malicious_name, "2026-09-02T00:00:00Z"),
        )

    # Verify tables were NOT dropped and record was safely stored literally
    with engine.transaction() as conn:
        assert conn.execute("SELECT COUNT(*) FROM notebooks;").fetchone()[0] == 1
        row = conn.execute("SELECT id, name FROM notebooks WHERE id = ?;", (malicious_id,)).fetchone()
        assert row is not None
        assert row[0] == malicious_id
        assert row[1] == malicious_name


def test_adversarial_multi_threaded_concurrency_in_wal_mode(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "wal_concurrency.db")
    engine.initialize_schema()

    # Seed an initial notebook
    with engine.transaction() as conn:
        conn.execute(
            "INSERT INTO notebooks (id, name, created_at) VALUES (?, ?, ?);",
            ("nb-shared", "Shared Notebook", "2026-09-02T00:00:00Z"),
        )

    errors = []

    def writer_task(worker_id: int):
        try:
            with engine.transaction() as conn:
                conn.execute(
                    "INSERT INTO sources (source_id, title, role, priority, created_at) VALUES (?, ?, ?, ?, ?);",
                    (f"src-worker-{worker_id}", f"Source from Worker {worker_id}", "PRIMARY", 1, "2026-09-02T00:00:00Z"),
                )
        except Exception as e:
            errors.append(f"Writer {worker_id} failed: {e}")

    def reader_task(worker_id: int):
        try:
            with engine.transaction() as conn:
                _ = conn.execute("SELECT COUNT(*) FROM sources;").fetchone()[0]
        except Exception as e:
            errors.append(f"Reader {worker_id} failed: {e}")

    # Run 20 concurrent readers and writers
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = []
        for i in range(10):
            futures.append(pool.submit(writer_task, i))
            futures.append(pool.submit(reader_task, i))
        for f in futures:
            f.result()

    assert not errors, f"Concurrency errors encountered: {errors}"

    with engine.transaction() as conn:
        count = conn.execute("SELECT COUNT(*) FROM sources;").fetchone()[0]
        assert count == 10


def test_adversarial_batch_atomic_rollback(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "atomic.db")
    engine.initialize_schema()

    with pytest.raises(sqlite3.IntegrityError):
        with engine.transaction() as conn:
            for i in range(10):
                conn.execute(
                    "INSERT INTO notebooks (id, name, created_at) VALUES (?, ?, ?);",
                    (f"nb-{i}", f"Notebook {i}", "2026-09-02T00:00:00Z"),
                )
            # 11th insert causes conflict with nb-0
            conn.execute(
                "INSERT INTO notebooks (id, name, created_at) VALUES (?, ?, ?);",
                ("nb-0", "Duplicate Notebook", "2026-09-02T00:00:00Z"),
            )

    # Verify that NONE of the 10 notebooks were committed
    with engine.transaction() as conn:
        assert conn.execute("SELECT COUNT(*) FROM notebooks;").fetchone()[0] == 0
