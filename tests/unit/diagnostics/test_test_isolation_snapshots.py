from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

import pytest

from study_engine.diagnostics.test_isolation_snapshots import (
    TestSnapshotError as SnapshotError,
    database_files_for_workspace,
    derive_test_workspace,
    prepare_sealed_snapshot,
    validate_snapshot,
    verify_sealed_snapshot,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATABASES = {
    "knowledge_store": "knowledge_store.db",
    "vector_store": "vector_store.db",
}
CONTEXT = {
    "scope": "synthetic-release",
    "run_identity": "run-synthetic-001",
    "gate_identity": "release-gate-synthetic",
    "policy_identity": "test-isolation-v1",
}


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _make_capture(
    root: Path, *, include_wal: bool = True, capture_age_seconds: int = 0
) -> tuple[sqlite3.Connection, str]:
    root.mkdir()
    source = root / "knowledge_store.db"
    connection = sqlite3.connect(source)
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA wal_autocheckpoint = 0")
    connection.execute("CREATE TABLE state (value TEXT)")
    connection.execute("INSERT INTO state VALUES ('captured')")
    connection.commit()
    if include_wal:
        assert Path(f"{source}-wal").is_file()
        assert Path(f"{source}-shm").is_file()
    else:
        connection.close()
        connection = sqlite3.connect(source)

    vector = root / "vector_store.db"
    vector_connection = sqlite3.connect(vector)
    vector_connection.execute("CREATE TABLE vectors (id TEXT)")
    vector_connection.commit()
    vector_connection.close()

    attestation = {
        "capture_id": "synthetic-capture-001",
        "capture_method": "atomic_filesystem_snapshot",
        "consistency": "atomic",
        "created_at": (
            datetime.now(timezone.utc) - timedelta(seconds=capture_age_seconds)
        ).isoformat(),
        "read_only": True,
        "scope": CONTEXT["scope"],
        "source_identity": "synthetic-source-set",
    }
    attestation_path = root / "capture-attestation.json"
    attestation_path.write_text(json.dumps(attestation), encoding="utf-8")
    for path in root.iterdir():
        path.chmod(0o444)
    root.chmod(0o555)
    return connection, _sha256(attestation_path)


def _prepare(root: Path, output: Path, attestation_sha256: str):
    return prepare_sealed_snapshot(
        root,
        output,
        attestation_sha256=attestation_sha256,
        database_names=DATABASES,
        freshness_seconds=3600,
        repository_root=REPOSITORY_ROOT,
        **CONTEXT,
    )


def test_seals_wal_snapshot_and_derives_independent_writable_workspace(
    tmp_path,
):
    capture = tmp_path / "capture"
    source_connection, attestation_digest = _make_capture(capture)
    source_files = {
        path.name: path.read_bytes()
        for path in capture.iterdir()
        if path.is_file()
    }

    snapshot, manifest_digest = _prepare(
        capture, tmp_path / "sealed-snapshot", attestation_digest
    )
    validation = validate_snapshot(
        snapshot,
        expected_manifest_sha256=manifest_digest,
        **CONTEXT,
    )
    assert validation.status == "VALID", validation.reason
    assert validation.manifest is not None
    assert (
        validation.manifest["wal_state"]["knowledge_store"]["status"]
        == "present"
    )
    assert (
        validation.manifest["shm_state"]["knowledge_store"]["status"]
        == "present"
    )
    assert (
        validation.manifest["integrity_verification"]["knowledge_store"][
            "status"
        ]
        == "passed"
    )
    sealed_database_bytes = (
        snapshot / "payload/knowledge_store.db"
    ).read_bytes()

    workspace = derive_test_workspace(
        snapshot,
        tmp_path / "workspace",
        expected_manifest_sha256=manifest_digest,
        **CONTEXT,
    )
    with sqlite3.connect(workspace / "knowledge_store.db") as connection:
        assert connection.execute("SELECT value FROM state").fetchall() == [
            ("captured",)
        ]
        connection.execute("INSERT INTO state VALUES ('workspace-only')")

    verify_sealed_snapshot(snapshot, manifest_digest)
    assert (
        snapshot / "payload/knowledge_store.db"
    ).read_bytes() == sealed_database_bytes
    assert {
        path.name: path.read_bytes()
        for path in capture.iterdir()
        if path.is_file()
    } == source_files
    source_connection.close()


def test_snapshot_validation_fails_closed_for_tampered_artifact_and_manifest(
    tmp_path,
):
    capture = tmp_path / "capture"
    connection, attestation_digest = _make_capture(capture, include_wal=False)
    connection.close()
    snapshot, manifest_digest = _prepare(
        capture, tmp_path / "sealed-snapshot", attestation_digest
    )

    payload_database = snapshot / "payload/knowledge_store.db"
    payload_database.chmod(0o644)
    payload_database.write_bytes(payload_database.read_bytes() + b"tampered")
    assert (
        validate_snapshot(
            snapshot,
            expected_manifest_sha256=manifest_digest,
            **CONTEXT,
        ).status
        == "INVALID"
    )

    manifest_path = snapshot / "manifest.json"
    manifest_path.chmod(0o644)
    manifest_path.write_bytes(manifest_path.read_bytes() + b" ")
    assert (
        validate_snapshot(
            snapshot,
            expected_manifest_sha256=manifest_digest,
            **CONTEXT,
        ).status
        == "INVALID"
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("scope", "different-scope"),
        ("run_identity", "different-run"),
        ("gate_identity", "different-gate"),
        ("policy_identity", "different-policy"),
    ],
)
def test_snapshot_context_mismatch_is_invalid(tmp_path, field, value):
    capture = tmp_path / "capture"
    connection, attestation_digest = _make_capture(capture, include_wal=False)
    connection.close()
    snapshot, manifest_digest = _prepare(
        capture, tmp_path / "sealed-snapshot", attestation_digest
    )
    expected = {**CONTEXT, field: value}
    assert (
        validate_snapshot(
            snapshot,
            expected_manifest_sha256=manifest_digest,
            **expected,
        ).status
        == "INVALID"
    )


def test_expired_snapshot_and_unpinned_manifest_are_invalid(tmp_path):
    capture = tmp_path / "capture"
    connection, attestation_digest = _make_capture(capture, include_wal=False)
    connection.close()
    snapshot, manifest_digest = _prepare(
        capture, tmp_path / "sealed-snapshot", attestation_digest
    )

    expired = validate_snapshot(
        snapshot,
        expected_manifest_sha256=manifest_digest,
        now=datetime.now(timezone.utc) + timedelta(hours=2),
        **CONTEXT,
    )
    assert expired.status == "INVALID"
    assert (
        validate_snapshot(
            snapshot,
            expected_manifest_sha256="sha256:" + "0" * 64,
            **CONTEXT,
        ).status
        == "INVALID"
    )


def test_producer_rejects_writable_capture_and_incomplete_attestation(
    tmp_path,
):
    capture = tmp_path / "capture"
    connection, attestation_digest = _make_capture(capture, include_wal=False)
    connection.close()
    (capture / "knowledge_store.db").chmod(0o644)
    with pytest.raises(SnapshotError, match="not read-only"):
        _prepare(capture, tmp_path / "rejected-writable", attestation_digest)

    (capture / "knowledge_store.db").chmod(0o444)
    attestation_path = capture / "capture-attestation.json"
    attestation_path.chmod(0o644)
    attestation_path.write_text('{"scope":"incomplete"}', encoding="utf-8")
    attestation_path.chmod(0o444)
    capture.chmod(0o555)
    incomplete_digest = _sha256(attestation_path)
    with pytest.raises(SnapshotError, match="incomplete"):
        _prepare(capture, tmp_path / "rejected-attestation", incomplete_digest)


def test_producer_rejects_stale_source_capture(tmp_path):
    capture = tmp_path / "capture"
    connection, attestation_digest = _make_capture(
        capture, include_wal=False, capture_age_seconds=7200
    )
    connection.close()
    with pytest.raises(SnapshotError, match="already stale"):
        _prepare(capture, tmp_path / "rejected-stale", attestation_digest)


def test_database_resolution_rejects_unprovenanced_workspace(tmp_path):
    with pytest.raises(SnapshotError, match="receipt"):
        database_files_for_workspace(
            tmp_path, {"knowledge_store": "knowledge_store.db"}
        )
