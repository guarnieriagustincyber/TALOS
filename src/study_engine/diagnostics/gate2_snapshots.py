"""Safe, read-only snapshot preparation for the Gate 2 generator."""

from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
import sqlite3
import tempfile
from typing import Dict, Iterable


class Gate2SnapshotError(ValueError):
    """Raised when a snapshot cannot be prepared or verified safely."""


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def backup_read_only_database(source: Path, destination: Path) -> None:
    """Copy a SQLite database to a writable destination using a read-only source."""
    source = Path(source).resolve()
    destination = Path(destination).resolve()
    if source == destination:
        raise Gate2SnapshotError("SQLite source and snapshot must differ")
    if not source.is_file():
        raise Gate2SnapshotError(f"SQLite source does not exist: {source}")
    source_connection = None
    destination_connection = None
    try:
        source_connection = sqlite3.connect(
            f"{source.as_uri()}?mode=ro", uri=True
        )
        destination_connection = sqlite3.connect(destination)
        source_connection.backup(destination_connection)
    except sqlite3.Error as exc:
        raise Gate2SnapshotError(f"Cannot snapshot {source}: {exc}") from exc
    finally:
        if destination_connection is not None:
            destination_connection.close()
        if source_connection is not None:
            source_connection.close()


def create_snapshots(
    knowledge_db: Path,
    vector_db: Path,
    *,
    parent_dir: Path | None = None,
) -> tuple[tempfile.TemporaryDirectory[str], Dict[str, object]]:
    """Create disposable SQLite copies and return their manifest.

    The source databases are opened read-only and are never used as output
    destinations. The caller owns the returned temporary directory.
    """
    knowledge_db = Path(knowledge_db).resolve()
    vector_db = Path(vector_db).resolve()
    if knowledge_db == vector_db:
        raise Gate2SnapshotError("Knowledge and vector databases must differ")
    temporary = tempfile.TemporaryDirectory(
        prefix="talos-g2-snapshot-", dir=str(parent_dir) if parent_dir else None
    )
    directory = Path(temporary.name)
    try:
        knowledge_copy = directory / "knowledge_store.db"
        vector_copy = directory / "vector_store.db"
        backup_read_only_database(knowledge_db, knowledge_copy)
        backup_read_only_database(vector_db, vector_copy)
        manifest = {
            "sources": {
                "knowledge_db": {
                    "path": str(knowledge_db),
                    "sha256": _hash_file(knowledge_db),
                    "size_bytes": knowledge_db.stat().st_size,
                },
                "vector_db": {
                    "path": str(vector_db),
                    "sha256": _hash_file(vector_db),
                    "size_bytes": vector_db.stat().st_size,
                },
            },
            "snapshots": {
                "knowledge_db": {
                    "path": str(knowledge_copy),
                    "sha256": _hash_file(knowledge_copy),
                    "size_bytes": knowledge_copy.stat().st_size,
                },
                "vector_db": {
                    "path": str(vector_copy),
                    "sha256": _hash_file(vector_copy),
                    "size_bytes": vector_copy.stat().st_size,
                },
            },
            "retrieval": {"executed": False, "concurrency": 0, "top_k": 0},
        }
        return temporary, manifest
    except Exception:
        temporary.cleanup()
        raise


def authorized_source_ids(
    knowledge_snapshot: Path, notebook_id: str
) -> list[str]:
    """Read the persisted ACL from a snapshot in read-only mode."""
    connection = sqlite3.connect(
        f"file:{Path(knowledge_snapshot).resolve()}?mode=ro", uri=True
    )
    try:
        rows = connection.execute(
            "SELECT source_id FROM notebook_sources "
            "WHERE notebook_id = ? ORDER BY source_id",
            (notebook_id,),
        ).fetchall()
    except sqlite3.Error as exc:
        raise Gate2SnapshotError(
            f"Cannot read ACL for notebook {notebook_id!r}: {exc}"
        ) from exc
    finally:
        connection.close()
    return [row[0] for row in rows]


def verify_sources_unchanged(
    manifest: Dict[str, object], knowledge_db: Path, vector_db: Path
) -> None:
    """Fail if active source databases changed during a snapshot operation."""
    sources = manifest.get("sources")
    if not isinstance(sources, dict):
        raise Gate2SnapshotError("Snapshot manifest is missing source hashes")
    for key, path in (("knowledge_db", knowledge_db), ("vector_db", vector_db)):
        record = sources.get(key)
        if not isinstance(record, dict) or record.get("sha256") != _hash_file(Path(path)):
            raise Gate2SnapshotError(f"Source database changed during snapshot: {path}")
