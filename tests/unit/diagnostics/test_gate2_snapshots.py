import sqlite3
from pathlib import Path

import pytest

from study_engine.diagnostics.gate2_snapshots import (
    Gate2SnapshotError,
    authorized_source_ids,
    create_snapshots,
    verify_sources_unchanged,
)


def _database(path, schema):
    connection = sqlite3.connect(path)
    connection.executescript(schema)
    connection.commit()
    connection.close()


def test_creates_hashed_disposable_snapshots_without_mutating_sources(tmp_path):
    knowledge = tmp_path / "knowledge.db"
    vector = tmp_path / "vector.db"
    _database(
        knowledge,
        """
        CREATE TABLE notebook_sources (notebook_id TEXT, source_id TEXT);
        INSERT INTO notebook_sources VALUES ('nb-a', 'source-a');
        """,
    )
    _database(vector, "CREATE TABLE vectors (chunk_id TEXT);")

    before = (knowledge.read_bytes(), vector.read_bytes())
    temporary, manifest = create_snapshots(knowledge, vector, parent_dir=tmp_path)
    try:
        assert manifest["retrieval"] == {
            "executed": False,
            "concurrency": 0,
            "top_k": 0,
        }
        assert manifest["sources"]["knowledge_db"]["sha256"].startswith("sha256:")
        snapshot = Path(temporary.name) / "knowledge_store.db"
        assert authorized_source_ids(snapshot, "nb-a") == ["source-a"]
    finally:
        temporary.cleanup()
    assert (knowledge.read_bytes(), vector.read_bytes()) == before


def test_reads_acl_from_snapshot_and_detects_source_changes(tmp_path):
    knowledge = tmp_path / "knowledge.db"
    vector = tmp_path / "vector.db"
    _database(
        knowledge,
        """
        CREATE TABLE notebook_sources (notebook_id TEXT, source_id TEXT);
        INSERT INTO notebook_sources VALUES ('nb-a', 'source-b');
        INSERT INTO notebook_sources VALUES ('nb-a', 'source-a');
        """,
    )
    _database(vector, "CREATE TABLE vectors (chunk_id TEXT);")

    temporary, manifest = create_snapshots(knowledge, vector, parent_dir=tmp_path)
    try:
        snapshot = tmp_path / "talos-g2-snapshot-missing"
        snapshot = next(tmp_path.glob("talos-g2-snapshot-*/knowledge_store.db"))
        assert authorized_source_ids(snapshot, "nb-a") == ["source-a", "source-b"]
        verify_sources_unchanged(manifest, knowledge, vector)
        with knowledge.open("ab") as handle:
            handle.write(b"changed")
        with pytest.raises(Gate2SnapshotError, match="changed"):
            verify_sources_unchanged(manifest, knowledge, vector)
    finally:
        temporary.cleanup()


def test_rejects_same_database_for_both_snapshots(tmp_path):
    database = tmp_path / "same.db"
    _database(database, "CREATE TABLE t (id TEXT);")

    with pytest.raises(Gate2SnapshotError, match="must differ"):
        create_snapshots(database, database, parent_dir=tmp_path)
