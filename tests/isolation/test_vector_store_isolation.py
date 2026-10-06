"""Dedicated test suite for production isolation and non-mutation verification (CP126).

Normative Reference:
- CP125: reports/e2e_study_loop/CP125_FORENSIC_ISOLATION_AUDIT.md
- CP125: checkpoints/125-forensic-isolation-audit.md
- CP126 Directive: Minimal Isolation Fix

Test Index:
- TEST-ISO-01: SQLiteVectorStore(existing_db, read_only=True) preserves SHA256, SIZE, MTIME
- TEST-ISO-02: AppContainer(use_mock=True) without working_dir uses isolated synthetic directory
- TEST-ISO-03: create_app() in test configuration suppresses background warmup
- TEST-ISO-04: vector_search() automatically resolves vector store with read_only=True
- TEST-ISO-05: Mutating operations on read-only store fail deterministically with ReadOnlyVectorStoreError
- TEST-ISO-06: Administrative write path (read_only=False) retains full write capability on isolated DB
- TEST-ISO-07: Existing DB schema is read without running DDL _initialize_schema()
- TEST-ISO-FORENSIC: End-to-end execution of AppContainer, create_app, and vector_search leaves production vector_store.db byte-identical
"""

import hashlib
import os
from pathlib import Path
import sqlite3
import struct
import time
from typing import Tuple
import pytest

from study_engine.config import settings
from study_engine.retrieval.vector_store import (
    ReadOnlyVectorStoreError,
    SQLiteVectorStore,
    VectorRecord,
)
from study_engine.storage.knowledge_store import KnowledgeStore
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


def _file_fingerprint(path: Path) -> Tuple[int, int, str]:
    """Compute (st_size, st_mtime_ns, sha256) tuple for strict physical verification."""
    stat = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return stat.st_size, stat.st_mtime_ns, digest.hexdigest()


def _create_sample_db(path: Path) -> None:
    """Helper to create a populated vector database with standard schema."""
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE chunk_embeddings (
            chunk_id TEXT NOT NULL,
            notebook_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            provider_id TEXT NOT NULL,
            model_id TEXT NOT NULL,
            dimensions INTEGER NOT NULL,
            vector BLOB NOT NULL,
            PRIMARY KEY (chunk_id, notebook_id)
        );
        """
    )
    vec = struct.pack("3f", 0.1, 0.2, 0.3)
    conn.execute(
        """
        INSERT INTO chunk_embeddings
            (chunk_id, notebook_id, source_id, provider_id, model_id, dimensions, vector)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        ("chunk_1", "nb_test", "src_test", "prov_test", "mod_test", 3, vec),
    )
    conn.commit()
    conn.close()


def test_iso_01_read_only_default_preserves_db_state(tmp_path: Path) -> None:
    """TEST-ISO-01: SQLiteVectorStore(existing_db, read_only=True) leaves SHA256 and MTIME unchanged."""
    test_db = tmp_path / "iso_sample.db"
    _create_sample_db(test_db)

    # Allow filesystem timestamps to settle
    time.sleep(0.01)
    size_before, mtime_before, sha_before = _file_fingerprint(test_db)

    # Open in read_only mode (the new default)
    store = SQLiteVectorStore(test_db, read_only=True)
    assert store.read_only is True

    # Perform read operations
    assert store.count() == 1
    assert store.count("nb_test") == 1
    recs = store.get_by_notebook("nb_test")
    assert len(recs) == 1
    assert recs[0].chunk_id == "chunk_1"

    chunk_ids, matrix = store.get_vector_matrix("nb_test")
    assert chunk_ids == ["chunk_1"]
    assert matrix.shape == (1, 3)

    single = store.get_by_chunk_id("chunk_1")
    assert single is not None

    store.close()

    size_after, mtime_after, sha_after = _file_fingerprint(test_db)
    assert size_before == size_after, "File size must not change on read_only access"
    assert mtime_before == mtime_after, "mtime must not change on read_only access"
    assert sha_before == sha_after, "SHA-256 must remain identical"


def test_iso_02_appcontainer_mock_uses_synthetic_dir() -> None:
    """TEST-ISO-02: AppContainer(use_mock=True) without working_dir uses isolated synthetic directory."""
    repo_root = Path(__file__).resolve().parents[2]
    prod_vec = repo_root / "data" / "web_state" / "vector_store.db"
    size_before, mtime_before, sha_before = _file_fingerprint(prod_vec)

    container = AppContainer(use_mock=True)
    try:
        # Container working_dir must NOT be data/web_state
        assert container.working_dir != (repo_root / "data" / "web_state")
        assert "talos_mock_state_" in str(container.working_dir)
        assert container.working_dir.exists()

        # Production vector store must be untouched
        size_after, mtime_after, sha_after = _file_fingerprint(prod_vec)
        assert size_before == size_after
        assert mtime_before == mtime_after
        assert sha_before == sha_after
    finally:
        if hasattr(container, "_temp_working_dir") and container._temp_working_dir:
            container._temp_working_dir.cleanup()


def test_iso_03_create_app_warmup_suppressed_in_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-ISO-03: create_app() suppresses background warmup in test configuration."""
    repo_root = Path(__file__).resolve().parents[2]
    prod_vec = repo_root / "data" / "web_state" / "vector_store.db"
    size_before, mtime_before, sha_before = _file_fingerprint(prod_vec)

    # Explicitly verify TALOS_ENABLE_WARMUP=0 configuration
    monkeypatch.setenv("TALOS_ENABLE_WARMUP", "0")
    monkeypatch.setattr(settings, "enable_retrieval_warmup", False)

    # Create app
    app = create_app()
    assert app is not None

    # Wait briefly to ensure no daemon thread executes write
    time.sleep(0.05)

    size_after, mtime_after, sha_after = _file_fingerprint(prod_vec)
    assert size_before == size_after
    assert mtime_before == mtime_after
    assert sha_before == sha_after


def test_iso_04_vector_search_resolves_readonly() -> None:
    """TEST-ISO-04: vector_search() resolves vector store with read_only=True without mutating production."""
    repo_root = Path(__file__).resolve().parents[2]
    prod_vec = repo_root / "data" / "web_state" / "vector_store.db"
    size_before, mtime_before, sha_before = _file_fingerprint(prod_vec)

    store = KnowledgeStore(":memory:")
    store.initialize()

    # Call vector_search without injected store, letting it auto-resolve candidate paths
    results = store.vector_search("warmup", notebook_id="nb_nonexistent", limit=1)
    assert results == []

    # If store resolved _vector_store, it must be read_only
    if hasattr(store, "_vector_store") and store._vector_store:
        assert getattr(store._vector_store, "read_only", None) is True

    # Assert production DB is untouched
    size_after, mtime_after, sha_after = _file_fingerprint(prod_vec)
    assert size_before == size_after
    assert mtime_before == mtime_after
    assert sha_before == sha_after


def test_iso_05_readonly_mutations_fail_closed(tmp_path: Path) -> None:
    """TEST-ISO-05: All mutation attempts on read_only store raise ReadOnlyVectorStoreError."""
    test_db = tmp_path / "ro_guard.db"
    _create_sample_db(test_db)

    store = SQLiteVectorStore(test_db, read_only=True)

    dummy_rec = VectorRecord(
        chunk_id="c_new",
        notebook_id="nb_test",
        source_id="src_test",
        provider_id="p",
        model_id="m",
        dimensions=3,
        vector=[1.0, 2.0, 3.0],
    )

    with pytest.raises(ReadOnlyVectorStoreError, match="Cannot save records to a read-only"):
        store.save_records([dummy_rec])

    with pytest.raises(ReadOnlyVectorStoreError, match="Cannot delete records from a read-only"):
        store.delete_by_notebook("nb_test")

    with pytest.raises(ReadOnlyVectorStoreError, match="Cannot delete records from a read-only"):
        store.delete_by_source("src_test")

    with pytest.raises(ReadOnlyVectorStoreError, match="Cannot initialize schema on a read-only"):
        store._initialize_schema()

    store.close()

    # Fail-closed: in-memory read_only is rejected
    with pytest.raises(ValueError, match="Cannot open an in-memory vector store in read-only mode"):
        SQLiteVectorStore(":memory:", read_only=True)

    # Fail-closed: missing file raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        SQLiteVectorStore(tmp_path / "non_existent.db", read_only=True)


def test_iso_06_admin_write_mode_allowed_on_isolated_db(tmp_path: Path) -> None:
    """TEST-ISO-06: Administrative write path (read_only=False) retains full write capability on isolated DB."""
    admin_db = tmp_path / "admin_test.db"
    store = SQLiteVectorStore(admin_db, read_only=False)
    assert store.read_only is False

    rec = VectorRecord(
        chunk_id="c_admin",
        notebook_id="nb_admin",
        source_id="src_admin",
        provider_id="mock",
        model_id="v1",
        dimensions=3,
        vector=[0.5, 0.5, 0.5],
    )

    saved = store.save_records([rec])
    assert saved == 1
    assert store.count("nb_admin") == 1

    # Verify retrieval
    recs = store.get_by_notebook("nb_admin")
    assert len(recs) == 1
    assert recs[0].chunk_id == "c_admin"

    deleted = store.delete_by_notebook("nb_admin")
    assert deleted == 1
    assert store.count("nb_admin") == 0
    store.close()


def test_iso_07_existing_schema_read_without_init(tmp_path: Path) -> None:
    """TEST-ISO-07: Verify schema of existing DB is queried without running DDL _initialize_schema()."""
    test_db = tmp_path / "no_init.db"
    _create_sample_db(test_db)

    # Ensure schema table exists before opening
    con = sqlite3.connect(test_db)
    con.execute("PRAGMA journal_mode = DELETE;")
    mode_before = con.execute("PRAGMA journal_mode;").fetchone()[0]
    con.close()
    assert mode_before == "delete"

    # Open with read_only=True: it must NOT execute PRAGMA journal_mode=WAL nor _initialize_schema()
    store = SQLiteVectorStore(test_db, read_only=True)
    count = store.count("nb_test")
    assert count == 1
    store.close()

    # Re-verify journal_mode was untouched (not switched to WAL)
    con = sqlite3.connect(test_db)
    mode_after = con.execute("PRAGMA journal_mode;").fetchone()[0]
    con.close()
    assert mode_after == "delete", f"Expected delete journal mode, got {mode_after}"


def test_iso_08_forensic_no_mutation_end_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    """TEST-ISO-FORENSIC: End-to-end execution of AppContainer, create_app, and vector_search leaves production vector_store.db byte-identical."""
    repo_root = Path(__file__).resolve().parents[2]
    prod_vec = repo_root / "data" / "web_state" / "vector_store.db"
    size_before, mtime_before, sha_before = _file_fingerprint(prod_vec)

    # 1. Instantiate AppContainer in mock mode without working_dir
    container = AppContainer(use_mock=True)
    set_container(container)

    # 2. Build FastAPI application
    app = create_app()
    assert app is not None

    # 3. Execute vector search on container's knowledge store
    res = container.knowledge_store.vector_search("warmup", notebook_id="nb_nonexistent", limit=1)
    assert res == []

    # 4. Strict forensic verification: production vector_store.db must be 100% byte-identical
    size_after, mtime_after, sha_after = _file_fingerprint(prod_vec)
    assert size_before == size_after, f"SIZE altered! before={size_before}, after={size_after}"
    assert mtime_before == mtime_after, f"MTIME altered! before={mtime_before}, after={mtime_after}"
    assert sha_before == sha_after, f"SHA256 altered! before={sha_before}, after={sha_after}"
