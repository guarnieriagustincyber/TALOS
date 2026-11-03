import sqlite3
from pathlib import Path

import pytest

from study_engine.diagnostics.gate2_snapshots import (
    Gate2SnapshotError,
    authorized_source_ids,
    backup_read_only_database,
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


def test_read_only_backup_captures_wal_without_changing_database_or_wal(
    tmp_path,
):
    source = tmp_path / "source.db"
    destination = tmp_path / "snapshot.db"
    source_connection = sqlite3.connect(source)
    try:
        assert source_connection.execute(
            "PRAGMA journal_mode = WAL"
        ).fetchone()[0].lower() == "wal"
        source_connection.execute("CREATE TABLE state (value TEXT)")
        source_connection.execute("INSERT INTO state VALUES ('committed')")
        source_connection.commit()

        wal_path = Path(f"{source}-wal")
        assert wal_path.is_file() and wal_path.stat().st_size > 0
        source_database_and_wal = {
            path: path.read_bytes()
            for path in (source, wal_path)
        }

        backup_read_only_database(source, destination)

        with sqlite3.connect(destination) as snapshot_connection:
            assert snapshot_connection.execute(
                "SELECT value FROM state"
            ).fetchall() == [("committed",)]
            snapshot_connection.execute(
                "INSERT INTO state VALUES ('temporary-only')"
            )

        assert source_connection.execute(
            "SELECT value FROM state ORDER BY value"
        ).fetchall() == [("committed",)]
        assert {
            path: path.read_bytes() for path in source_database_and_wal
        } == source_database_and_wal
    finally:
        source_connection.close()


def test_read_only_backup_rejects_missing_source_and_same_destination(
    tmp_path,
):
    missing = tmp_path / "missing.db"
    with pytest.raises(Gate2SnapshotError, match="does not exist"):
        backup_read_only_database(missing, tmp_path / "snapshot.db")

    database = tmp_path / "same.db"
    _database(database, "CREATE TABLE state (value TEXT);")
    with pytest.raises(Gate2SnapshotError, match="source and snapshot"):
        backup_read_only_database(database, database)
