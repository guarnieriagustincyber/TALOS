from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts import capture_quiesced_test_sources
from study_engine.diagnostics.test_isolation_snapshots import (
    TestSnapshotError as SnapshotError,
)
from study_engine.diagnostics.test_isolation_snapshots import (
    _source_file_record,
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
        validation.manifest["journal_state"]["knowledge_store"]["status"]
        == "absent"
    )
    assert validation.manifest["format_version"] == 2
    assert (
        validation.manifest["integrity_verification"]["knowledge_store"][
            "status"
        ]
        == "passed"
    )
    sealed_database_bytes = (
        snapshot / "payload/knowledge_store.db"
    ).read_bytes()

    workspace_identity = "/workspace/run/test-data"
    workspace = derive_test_workspace(
        snapshot,
        tmp_path / "workspace",
        expected_manifest_sha256=manifest_digest,
        workspace_identity=workspace_identity,
        **CONTEXT,
    )
    assert database_files_for_workspace(
        workspace,
        {"knowledge_store": "knowledge_store.db"},
        expected_workspace_identity=workspace_identity,
    )["knowledge_store"].is_file()
    with pytest.raises(SnapshotError, match="Workspace provenance identity"):
        database_files_for_workspace(
            workspace, {"knowledge_store": "knowledge_store.db"}
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


def _make_quiesced_b06_capture(root: Path) -> str:
    root.mkdir()
    database_names = {
        "knowledge_store": "knowledge_store.db",
        "vector_store": "vector_store.db",
        "student_state": "student_state.db",
    }
    for filename in database_names.values():
        connection = sqlite3.connect(root / filename)
        connection.execute("CREATE TABLE state (value TEXT)")
        connection.execute("INSERT INTO state VALUES ('synthetic')")
        connection.commit()
        connection.close()

    for path in root.iterdir():
        path.chmod(0o444)
    source_files = [
        _source_file_record(path, path.name)
        for path in sorted(root.iterdir(), key=lambda item: item.name)
    ]
    attestation = {
        "capture_id": "synthetic-quiesced-capture",
        "capture_method": "quiesced_file_copy",
        "consistency": "quiesced",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "read_only_semantics": "capture_copy_does_not_write_source_files",
        "attestation_authority": "project-delegated-local-executor",
        "authentication_model": "local_integrity_only",
        "scope": "talos.b06.snapshot.v1",
        "source_identity": "synthetic-runtime-web",
        "run_identity": "123e4567-e89b-42d3-a456-426614174000",
        "gate_identity": "talos-p1.2-b06-quality-gate-v1",
        "policy_identity": "talos.b06.quiesced-consistency.v1",
        "source_files": source_files,
        "quiescence": {
            "mode": "no_open_handles",
            "verification": "lsof_before_and_after_copy",
            "source_stability": (
                "source_file_fingerprints_match_before_and_after"
            ),
        },
    }
    attestation_path = root / "capture-attestation.json"
    attestation_path.write_text(json.dumps(attestation), encoding="utf-8")
    attestation_path.chmod(0o444)
    root.chmod(0o555)
    return _sha256(attestation_path)


def test_quiesced_b06_policy_is_versioned_and_validated(tmp_path):
    capture = tmp_path / "quiesced-capture"
    attestation_digest = _make_quiesced_b06_capture(capture)
    database_names = {
        "knowledge_store": "knowledge_store.db",
        "vector_store": "vector_store.db",
        "student_state": "student_state.db",
    }
    context = {
        "scope": "talos.b06.snapshot.v1",
        "run_identity": "123e4567-e89b-42d3-a456-426614174000",
        "gate_identity": "talos-p1.2-b06-quality-gate-v1",
        "policy_identity": "talos.b06.quiesced-consistency.v1",
    }
    snapshot, manifest_digest = prepare_sealed_snapshot(
        capture,
        tmp_path / "quiesced-snapshot",
        attestation_sha256=attestation_digest,
        database_names=database_names,
        freshness_seconds=3600,
        repository_root=REPOSITORY_ROOT,
        **context,
    )
    validation = validate_snapshot(
        snapshot,
        expected_manifest_sha256=manifest_digest,
        **context,
    )
    assert validation.status == "VALID", validation.reason
    assert validation.manifest is not None
    assert validation.manifest["format_version"] == 3
    assert validation.manifest["capture_method"] == "quiesced_file_copy"
    assert validation.manifest["capture_consistency"] == "quiesced"
    assert (
        validation.manifest["capture_verification"]["mode"]
        == "no_open_handles"
    )


def test_quiesced_b06_rejects_unapproved_policy(tmp_path):
    capture = tmp_path / "quiesced-capture"
    attestation_digest = _make_quiesced_b06_capture(capture)
    with pytest.raises(SnapshotError, match="method, consistency, policy"):
        prepare_sealed_snapshot(
            capture,
            tmp_path / "rejected-quiesced-snapshot",
            attestation_sha256=attestation_digest,
            database_names={
                "knowledge_store": "knowledge_store.db",
                "vector_store": "vector_store.db",
                "student_state": "student_state.db",
            },
            scope="talos.b06.snapshot.v1",
            run_identity="123e4567-e89b-42d3-a456-426614174000",
            gate_identity="talos-p1.2-b06-quality-gate-v1",
            policy_identity="unapproved-policy",
            freshness_seconds=3600,
            repository_root=REPOSITORY_ROOT,
        )


def _make_quiesced_capture_sources(tmp_path: Path, monkeypatch) -> Path:
    repository = tmp_path / "repository"
    source_root = repository / "data" / "web_state"
    source_root.mkdir(parents=True)
    monkeypatch.setattr(capture_quiesced_test_sources, "REPOSITORY_ROOT", repository)
    monkeypatch.setattr(capture_quiesced_test_sources, "SOURCE_ROOT", source_root)
    for filename in capture_quiesced_test_sources.DATABASES.values():
        connection = sqlite3.connect(source_root / filename)
        connection.execute("CREATE TABLE state (value TEXT)")
        connection.execute("INSERT INTO state VALUES ('source')")
        connection.commit()
        connection.close()
    return source_root


def test_quiesced_capture_copies_sources_read_only_without_open_handles(
    tmp_path, monkeypatch
):
    source_root = _make_quiesced_capture_sources(tmp_path, monkeypatch)
    monkeypatch.setattr(
        capture_quiesced_test_sources, "_assert_no_open_handles", lambda paths: None
    )
    before = {
        path.name: _sha256(path)
        for path in source_root.iterdir()
    }
    destination = tmp_path / "external" / "capture"
    run_id = "123e4567-e89b-42d3-a456-426614174000"

    capture_root, capture_id = capture_quiesced_test_sources._capture(
        destination, run_id
    )

    assert capture_root == destination
    assert capture_id
    assert {
        path.name: _sha256(path)
        for path in source_root.iterdir()
    } == before
    assert (capture_root / "capture-attestation.json").is_file()
    assert not (capture_root / "knowledge_store.db").stat().st_mode & 0o222
    attestation = json.loads(
        (capture_root / "capture-attestation.json").read_text(
            encoding="utf-8"
        )
    )
    assert attestation["consistency"] == "quiesced"
    assert attestation["read_only"] is True


def test_quiesced_capture_rejects_sidecar_inventory_changes_and_cleans_staging(
    tmp_path, monkeypatch
):
    source_root = _make_quiesced_capture_sources(tmp_path, monkeypatch)
    monkeypatch.setattr(
        capture_quiesced_test_sources, "_assert_no_open_handles", lambda paths: None
    )
    copy_source = capture_quiesced_test_sources._copy_source
    sidecar_created = False

    def copy_source_and_create_sidecar(source: Path, target: Path) -> None:
        nonlocal sidecar_created
        copy_source(source, target)
        if not sidecar_created:
            (source_root / "knowledge_store.db-wal").write_bytes(b"new sidecar")
            sidecar_created = True

    monkeypatch.setattr(
        capture_quiesced_test_sources,
        "_copy_source",
        copy_source_and_create_sidecar,
    )
    capture_parent = tmp_path / "external"
    destination = capture_parent / "capture"

    with pytest.raises(
        capture_quiesced_test_sources.CaptureError,
        match="inventory changed",
    ):
        capture_quiesced_test_sources._capture(
            destination, "123e4567-e89b-42d3-a456-426614174000"
        )

    assert not destination.exists()
    assert not list(capture_parent.glob(".talos-b06-quiesced-*"))


def test_quiesced_capture_rejects_open_source_handles(tmp_path, monkeypatch):
    source_root = _make_quiesced_capture_sources(tmp_path, monkeypatch)
    connection = sqlite3.connect(source_root / "knowledge_store.db")
    connection.execute("SELECT value FROM state").fetchall()
    try:
        with pytest.raises(
            capture_quiesced_test_sources.CaptureError,
            match="Open file handles found",
        ):
            capture_quiesced_test_sources._capture(
                tmp_path / "external" / "blocked-capture",
                "123e4567-e89b-42d3-a456-426614174000",
            )
    finally:
        connection.close()


def test_database_resolution_rejects_unprovenanced_workspace(tmp_path):
    with pytest.raises(SnapshotError, match="receipt"):
        database_files_for_workspace(
            tmp_path, {"knowledge_store": "knowledge_store.db"}
        )
