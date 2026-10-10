"""Sealed test snapshots and per-run writable workspaces.

This module consumes an externally-created, read-only filesystem capture. It
never opens the protected source with SQLite; SQLite validation runs only on a
disposable copy of the captured files.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import stat
import subprocess
import tempfile
from typing import Any, Literal, Mapping
from urllib.parse import quote
from uuid import uuid4


class TestSnapshotError(ValueError):
    """Raised when safe snapshot preparation or consumption fails."""


@dataclass(frozen=True)
class SnapshotValidation:
    status: Literal["VALID", "INVALID"]
    reason: str
    manifest: Mapping[str, Any] | None = None


_FORMAT_VERSION = 1
_PRODUCER = "study_engine.diagnostics.test_isolation_snapshots"
_PRODUCER_VERSION = "1"
_SIDECARS = ("-wal", "-shm", "-journal")
_GATE_FILES = (
    "config/test_perimeter.json",
    "scripts/quality_gate.py",
    "scripts/test.sh",
    "tests/conftest.py",
)
_REQUIRED_ATTESTATION_FIELDS = {
    "capture_id",
    "capture_method",
    "consistency",
    "created_at",
    "read_only",
    "scope",
    "source_identity",
}
_REQUIRED_MANIFEST_FIELDS = {
    "capture_attestation_sha256",
    "capture_id",
    "capture_created_at",
    "capture_method",
    "created_at",
    "databases",
    "destination_identity",
    "files",
    "freshness",
    "gate_fingerprint",
    "gate_identity",
    "git_tree_or_commit",
    "integrity_verification",
    "policy_identity",
    "producer",
    "producer_version",
    "run_identity",
    "schema_versions",
    "schema_fingerprints",
    "scope",
    "source_files",
    "shm_state",
    "snapshot_id",
    "source_fingerprint",
    "source_identity",
    "wal_state",
    "workspace_contract",
    "format_version",
}


def _sha256_bytes(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _load_json_object(path: Path) -> dict[str, Any]:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise TestSnapshotError(f"Duplicate JSON key in {path}: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TestSnapshotError(
            f"Cannot read JSON object {path}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise TestSnapshotError(f"Expected a JSON object: {path}")
    return value


def _utc_timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise TestSnapshotError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TestSnapshotError(f"Invalid {field}: {value!r}") from exc
    if parsed.tzinfo is None:
        raise TestSnapshotError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _require_identity(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TestSnapshotError(f"{field} is required")
    return value.strip()


def _assert_read_only_capture(source_root: Path) -> None:
    if not source_root.is_dir() or source_root.is_symlink():
        raise TestSnapshotError(
            "Capture root must be an existing non-symlink directory: "
            f"{source_root}"
        )
    for path in (source_root, *source_root.rglob("*")):
        if path.is_symlink():
            raise TestSnapshotError(
                f"Symlinks are not allowed in a capture: {path}"
            )
        if path.is_file() or path.is_dir():
            if stat.S_IMODE(path.stat().st_mode) & 0o222:
                raise TestSnapshotError(
                    "Capture is not read-only (write permission present): "
                    f"{path}"
                )


def _source_file_record(path: Path, relative_path: str) -> dict[str, Any]:
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode):
        raise TestSnapshotError(f"Capture input is not a regular file: {path}")
    return {
        "path": relative_path,
        "sha256": _sha256_file(path),
        "size_bytes": metadata.st_size,
        "mode": stat.S_IMODE(metadata.st_mode),
        "mtime_ns": metadata.st_mtime_ns,
    }


def _repository_identity(repository_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise TestSnapshotError(
            f"Cannot identify the repository commit: {exc}"
        ) from exc
    commit = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(
        r"[0-9a-fA-F]{40,64}", commit
    ):
        raise TestSnapshotError(
            "Cannot determine an exact Git commit for this snapshot"
        )
    return commit.lower()


def _gate_fingerprint(repository_root: Path) -> str:
    records = []
    for relative in _GATE_FILES:
        path = repository_root / relative
        if not path.is_file() or path.is_symlink():
            raise TestSnapshotError(
                f"Cannot fingerprint gate input: {relative}"
            )
        records.append({"path": relative, "sha256": _sha256_file(path)})
    return _sha256_bytes(_canonical_json(records))


def _read_schema_metadata(database: Path) -> tuple[int, str]:
    uri = f"file:{quote(str(database.resolve()))}?mode=ro"
    connection = None
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=2)
        integrity = connection.execute("PRAGMA integrity_check").fetchall()
        if integrity != [("ok",)]:
            raise TestSnapshotError(
                "SQLite integrity check failed for captured database "
                f"{database.name}"
            )
        version = connection.execute("PRAGMA user_version").fetchone()
        schema = connection.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name, tbl_name"
        ).fetchall()
    except sqlite3.Error as exc:
        raise TestSnapshotError(
            f"Cannot validate captured database {database.name}: {exc}"
        ) from exc
    finally:
        if connection is not None:
            connection.close()
    if version is None or not isinstance(version[0], int):
        raise TestSnapshotError(
            f"Cannot determine schema version for {database.name}"
        )
    return version[0], _sha256_bytes(_canonical_json(schema))


def _verify_sqlite_copies(
    payload: Path, database_names: Mapping[str, str]
) -> tuple[dict[str, int], dict[str, str]]:
    versions: dict[str, int] = {}
    schema_fingerprints: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="talos-snapshot-verify-") as temp:
        validation_root = Path(temp)
        for identity, filename in database_names.items():
            for suffix in ("", *_SIDECARS):
                source = payload / f"{filename}{suffix}"
                if source.exists():
                    shutil.copyfile(source, validation_root / source.name)
            versions[identity], schema_fingerprints[identity] = (
                _read_schema_metadata(validation_root / filename)
            )
    return versions, schema_fingerprints


def _set_sealed_permissions(root: Path) -> None:
    for path in sorted(
        root.rglob("*"), key=lambda item: len(item.parts), reverse=True
    ):
        if path.is_dir():
            path.chmod(0o555)
        else:
            path.chmod(0o444)
    root.chmod(0o555)


def _remove_snapshot_tree(root: Path) -> None:
    if not root.exists():
        return
    for path in root.rglob("*"):
        if path.is_dir():
            path.chmod(0o700)
        else:
            path.chmod(0o600)
    root.chmod(0o700)
    shutil.rmtree(root)


def _file_inventory(root: Path) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for path in sorted((root / "payload").iterdir()):
        if path.is_symlink() or not path.is_file():
            raise TestSnapshotError(
                f"Unexpected snapshot payload entry: {path}"
            )
        inventory.append(
            {
                "path": path.name,
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return inventory


def _sidecar_state(
    database_names: Mapping[str, str],
    inventory: list[dict[str, Any]],
    suffix: str,
) -> dict[str, dict[str, Any]]:
    records = {record["path"]: record for record in inventory}
    result: dict[str, dict[str, Any]] = {}
    for identity, filename in database_names.items():
        path = f"{filename}{suffix}"
        record = records.get(path)
        result[identity] = (
            {"status": "present", **record}
            if record is not None
            else {"status": "absent"}
        )
    return result


def prepare_sealed_snapshot(
    capture_root: Path,
    artifact_root: Path,
    *,
    attestation_sha256: str,
    database_names: Mapping[str, str],
    scope: str,
    run_identity: str,
    gate_identity: str,
    policy_identity: str,
    freshness_seconds: int,
    repository_root: Path,
) -> tuple[Path, str]:
    """Seal a copy of an externally attested, read-only filesystem capture.

    The caller must provide the attestation digest through a separate trusted
    channel. No SQLite connection is opened against ``capture_root``.
    """
    capture_input = Path(capture_root)
    artifact_input = Path(artifact_root)
    if capture_input.is_symlink() or artifact_input.is_symlink():
        raise TestSnapshotError(
            "Capture and artifact paths cannot be symlinks"
        )
    try:
        capture_root = capture_input.resolve(strict=True)
        repository_root = Path(repository_root).resolve(strict=True)
    except OSError as exc:
        raise TestSnapshotError(
            f"Cannot resolve snapshot input paths: {exc}"
        ) from exc
    artifact_root = artifact_input.resolve()
    if artifact_root.exists():
        raise TestSnapshotError(
            f"Snapshot destination already exists: {artifact_root}"
        )
    try:
        artifact_root.relative_to(capture_root)
    except ValueError:
        pass
    else:
        raise TestSnapshotError(
            "Snapshot destination cannot be inside the capture"
        )
    try:
        capture_root.relative_to(repository_root / "data")
    except ValueError:
        pass
    else:
        raise TestSnapshotError(
            "Capture must be an external snapshot, not a live repository "
            "data path"
        )
    try:
        artifact_root.relative_to(repository_root / "data")
    except ValueError:
        pass
    else:
        raise TestSnapshotError(
            "Snapshot artifact cannot be written inside repository data"
        )

    scope = _require_identity(scope, "scope")
    run_identity = _require_identity(run_identity, "run_identity")
    gate_identity = _require_identity(gate_identity, "gate_identity")
    policy_identity = _require_identity(policy_identity, "policy_identity")
    if (
        not isinstance(freshness_seconds, int)
        or isinstance(freshness_seconds, bool)
        or freshness_seconds <= 0
    ):
        raise TestSnapshotError("freshness_seconds must be a positive integer")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", attestation_sha256):
        raise TestSnapshotError(
            "attestation_sha256 must be a full SHA-256 fingerprint"
        )
    if not database_names:
        raise TestSnapshotError("At least one database identity is required")
    for identity, filename in database_names.items():
        _require_identity(identity, "database identity")
        if (
            not isinstance(filename, str)
            or Path(filename).name != filename
            or not filename.endswith(".db")
        ):
            raise TestSnapshotError(f"Invalid database filename: {filename!r}")
    if len(set(database_names.values())) != len(database_names):
        raise TestSnapshotError("Database filenames must be unique")

    _assert_read_only_capture(capture_root)
    attestation_path = capture_root / "capture-attestation.json"
    if not attestation_path.is_file():
        raise TestSnapshotError("Missing capture-attestation.json")
    if _sha256_file(attestation_path) != attestation_sha256:
        raise TestSnapshotError(
            "Capture attestation fingerprint does not match"
        )
    attestation = _load_json_object(attestation_path)
    missing = _REQUIRED_ATTESTATION_FIELDS - attestation.keys()
    if missing:
        raise TestSnapshotError(
            f"Capture attestation is incomplete: {', '.join(sorted(missing))}"
        )
    if (
        attestation["capture_method"] != "atomic_filesystem_snapshot"
        or attestation["consistency"] != "atomic"
        or attestation["read_only"] is not True
    ):
        raise TestSnapshotError(
            "Capture attestation must declare an atomic, read-only "
            "filesystem snapshot"
        )
    if attestation["scope"] != scope:
        raise TestSnapshotError(
            "Capture attestation scope does not match requested scope"
        )
    for field in ("capture_id", "source_identity"):
        _require_identity(attestation[field], f"attestation.{field}")
    capture_created_at = _utc_timestamp(
        attestation["created_at"], "attestation.created_at"
    )
    current_time = datetime.now(timezone.utc)
    if current_time < capture_created_at:
        raise TestSnapshotError("Capture timestamp is in the future")
    if current_time >= capture_created_at + timedelta(
        seconds=freshness_seconds
    ):
        raise TestSnapshotError("Source capture is already stale")

    file_names = {
        f"{filename}{suffix}"
        for filename in database_names.values()
        for suffix in ("", *_SIDECARS)
    }
    source_paths = {
        name: capture_root / name
        for name in sorted(file_names)
        if (capture_root / name).exists()
    }
    missing_databases = [
        filename
        for filename in database_names.values()
        if filename not in source_paths
    ]
    if missing_databases:
        raise TestSnapshotError(
            f"Capture is missing databases: {', '.join(missing_databases)}"
        )
    expected_entries = set(source_paths) | {"capture-attestation.json"}
    actual_entries = {path.name for path in capture_root.iterdir()}
    if actual_entries != expected_entries:
        raise TestSnapshotError(
            "Capture must contain only declared databases, SQLite sidecars, "
            "and capture-attestation.json"
        )

    before_records = [
        _source_file_record(path, name)
        for name, path in sorted(source_paths.items())
    ]
    source_fingerprint = _sha256_bytes(_canonical_json(before_records))
    artifact_root.parent.mkdir(parents=True, exist_ok=True)
    staging_parent = artifact_root.parent
    staging_dir = Path(
        tempfile.mkdtemp(prefix=".talos-snapshot-staging-", dir=staging_parent)
    )
    try:
        payload = staging_dir / "payload"
        payload.mkdir()
        for name, source_path in source_paths.items():
            shutil.copyfile(source_path, payload / name)
        after_records = [
            _source_file_record(path, name)
            for name, path in sorted(source_paths.items())
        ]
        if before_records != after_records:
            raise TestSnapshotError(
                "Capture changed while the snapshot was prepared"
            )

        inventory = _file_inventory(staging_dir)
        schema_versions, schema_fingerprints = _verify_sqlite_copies(
            payload, database_names
        )
        now = datetime.now(timezone.utc)
        if now >= capture_created_at + timedelta(seconds=freshness_seconds):
            raise TestSnapshotError(
                "Source capture expired while the artifact was prepared"
            )
        snapshot_id = str(uuid4())
        manifest = {
            "format_version": _FORMAT_VERSION,
            "snapshot_id": snapshot_id,
            "source_identity": attestation["source_identity"],
            "source_fingerprint": source_fingerprint,
            "source_files": before_records,
            "git_tree_or_commit": _repository_identity(repository_root),
            "gate_fingerprint": _gate_fingerprint(repository_root),
            "wal_state": _sidecar_state(database_names, inventory, "-wal"),
            "shm_state": _sidecar_state(database_names, inventory, "-shm"),
            "schema_versions": schema_versions,
            "schema_fingerprints": schema_fingerprints,
            "databases": dict(database_names),
            "producer": _PRODUCER,
            "producer_version": _PRODUCER_VERSION,
            "created_at": now.isoformat(),
            "capture_created_at": capture_created_at.isoformat(),
            "scope": scope,
            "freshness": {
                "created_at": capture_created_at.isoformat(),
                "expires_at": (
                    capture_created_at + timedelta(seconds=freshness_seconds)
                ).isoformat(),
                "max_age_seconds": freshness_seconds,
            },
            "destination_identity": str(artifact_root),
            "run_identity": run_identity,
            "gate_identity": gate_identity,
            "policy_identity": policy_identity,
            "capture_method": attestation["capture_method"],
            "capture_id": attestation["capture_id"],
            "capture_attestation_sha256": attestation_sha256,
            "files": inventory,
            "integrity_verification": {
                identity: {
                    "status": "passed",
                    "method": "PRAGMA integrity_check",
                    "result": "ok",
                }
                for identity in database_names
            },
            "workspace_contract": {
                "pytest_reads": "derived_workspace_only",
                "workspace_writable": True,
                "snapshot_writable": False,
            },
        }
        manifest_path = staging_dir / "manifest.json"
        manifest_path.write_bytes(_canonical_json(manifest) + b"\n")
        manifest_digest = _sha256_file(manifest_path)
        _set_sealed_permissions(staging_dir)
        staging_dir.rename(artifact_root)
        return artifact_root, manifest_digest
    except Exception:
        _remove_snapshot_tree(staging_dir)
        raise


def _validate_payload(
    snapshot_root: Path, manifest: Mapping[str, Any]
) -> None:
    payload = snapshot_root / "payload"
    if not payload.is_dir() or payload.is_symlink():
        raise TestSnapshotError(
            "Snapshot payload directory is missing or invalid"
        )
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise TestSnapshotError("Snapshot manifest has no file inventory")
    expected_names: set[str] = set()
    for entry in files:
        if not isinstance(entry, dict):
            raise TestSnapshotError("Invalid snapshot file inventory entry")
        name = entry.get("path")
        if not isinstance(name, str) or Path(name).name != name:
            raise TestSnapshotError(
                "Snapshot inventory contains an invalid path"
            )
        expected_names.add(name)
        path = payload / name
        if path.is_symlink() or not path.is_file():
            raise TestSnapshotError(
                f"Snapshot file is missing or invalid: {name}"
            )
        digest = entry.get("sha256")
        if not isinstance(digest, str) or _sha256_file(path) != digest:
            raise TestSnapshotError(
                f"Snapshot file fingerprint mismatch: {name}"
            )
        if path.stat().st_size != entry.get("size_bytes"):
            raise TestSnapshotError(f"Snapshot file size mismatch: {name}")
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            raise TestSnapshotError(
                f"Snapshot file fingerprint is invalid: {name}"
            )
        if stat.S_IMODE(path.stat().st_mode) & 0o222:
            raise TestSnapshotError(
                f"Sealed snapshot file is writable: {name}"
            )
    if len(expected_names) != len(files):
        raise TestSnapshotError("Snapshot inventory contains duplicate files")
    actual_names = {path.name for path in payload.iterdir()}
    if actual_names != expected_names:
        raise TestSnapshotError("Snapshot payload contains unmanifested files")
    if {path.name for path in snapshot_root.iterdir()} != {
        "manifest.json",
        "payload",
    }:
        raise TestSnapshotError(
            "Snapshot artifact contains unmanifested entries"
        )
    manifest_path = snapshot_root / "manifest.json"
    if manifest_path.is_symlink():
        raise TestSnapshotError("Snapshot manifest cannot be a symlink")
    for path in (snapshot_root, payload, manifest_path):
        if stat.S_IMODE(path.stat().st_mode) & 0o222:
            raise TestSnapshotError(f"Snapshot directory is writable: {path}")

    source_files = manifest.get("source_files")
    if not isinstance(source_files, list) or not source_files:
        raise TestSnapshotError("Snapshot source provenance is missing")
    if _sha256_bytes(_canonical_json(source_files)) != manifest.get(
        "source_fingerprint"
    ):
        raise TestSnapshotError("Snapshot source fingerprint is inconsistent")
    if any(not isinstance(record, dict) for record in source_files):
        raise TestSnapshotError("Snapshot source inventory entry is invalid")
    source_file_hashes = {
        record.get("path"): record.get("sha256") for record in source_files
    }
    if set(source_file_hashes) != expected_names or len(
        source_file_hashes
    ) != len(source_files):
        raise TestSnapshotError(
            "Snapshot source inventory does not match payload files"
        )
    if any(
        not isinstance(record.get("size_bytes"), int)
        or record["size_bytes"] < 0
        or not isinstance(record.get("mtime_ns"), int)
        or not isinstance(record.get("mode"), int)
        or not isinstance(record.get("sha256"), str)
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", record.get("sha256", ""))
        for record in source_files
    ):
        raise TestSnapshotError(
            "Snapshot source inventory metadata is invalid"
        )
    if any(
        source_file_hashes.get(entry["path"]) != entry["sha256"]
        for entry in files
    ):
        raise TestSnapshotError(
            "Snapshot payload does not match its source inventory"
        )

    database_names = manifest.get("databases")
    schema_versions = manifest.get("schema_versions")
    schema_fingerprints = manifest.get("schema_fingerprints")
    integrity = manifest.get("integrity_verification")
    if (
        not isinstance(database_names, dict)
        or not database_names
        or not isinstance(schema_versions, dict)
        or set(schema_versions) != set(database_names)
        or not isinstance(schema_fingerprints, dict)
        or set(schema_fingerprints) != set(database_names)
    ):
        raise TestSnapshotError("Snapshot schema provenance is missing")
    if not isinstance(integrity, dict) or set(integrity) != set(
        database_names
    ):
        raise TestSnapshotError(
            "Snapshot integrity results do not match its databases"
        )
    if any(
        not isinstance(version, int)
        or isinstance(version, bool)
        or version < 0
        for version in schema_versions.values()
    ):
        raise TestSnapshotError("Snapshot schema version is invalid")
    if any(
        not isinstance(fingerprint, str)
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", fingerprint)
        for fingerprint in schema_fingerprints.values()
    ):
        raise TestSnapshotError("Snapshot schema fingerprint is invalid")
    for result in integrity.values():
        if (
            not isinstance(result, dict)
            or result.get("status") != "passed"
            or result.get("method") != "PRAGMA integrity_check"
            or result.get("result") != "ok"
        ):
            raise TestSnapshotError(
                "Snapshot database integrity was not verified"
            )

    inventory_by_name = {entry["path"]: entry for entry in files}
    for sidecar_key, suffix in (("wal_state", "-wal"), ("shm_state", "-shm")):
        sidecars = manifest.get(sidecar_key)
        if not isinstance(sidecars, dict) or set(sidecars) != set(
            database_names
        ):
            raise TestSnapshotError(
                f"Snapshot {sidecar_key} provenance is invalid"
            )
        for identity, state in sidecars.items():
            filename = database_names.get(identity)
            if (
                not isinstance(filename, str)
                or Path(filename).name != filename
            ):
                raise TestSnapshotError(
                    "Snapshot database identity is invalid"
                )
            if not isinstance(state, dict):
                raise TestSnapshotError(
                    f"Invalid {sidecar_key} for {identity}"
                )
            record = inventory_by_name.get(f"{filename}{suffix}")
            if state.get("status") == "absent":
                if record is not None or set(state) != {"status"}:
                    raise TestSnapshotError(
                        f"Snapshot {sidecar_key} state is inconsistent"
                    )
            elif state.get("status") == "present":
                if (
                    record is None
                    or state.get("path") != record["path"]
                    or state.get("sha256") != record["sha256"]
                    or state.get("size_bytes") != record["size_bytes"]
                ):
                    raise TestSnapshotError(
                        f"Snapshot {sidecar_key} state is inconsistent"
                    )
            else:
                raise TestSnapshotError(
                    f"Snapshot {sidecar_key} state is unknown"
                )


def validate_snapshot(
    snapshot_root: Path,
    *,
    expected_manifest_sha256: str,
    scope: str,
    run_identity: str,
    gate_identity: str,
    policy_identity: str,
    now: datetime | None = None,
    repository_root: Path | None = None,
) -> SnapshotValidation:
    """Return an unambiguous VALID/INVALID decision for a pinned snapshot."""
    snapshot_input = Path(snapshot_root)
    if snapshot_input.is_symlink():
        return SnapshotValidation(
            "INVALID", "snapshot root cannot be a symlink"
        )
    snapshot_root = snapshot_input.resolve()
    try:
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", expected_manifest_sha256):
            raise TestSnapshotError(
                "A full expected manifest SHA-256 is required"
            )
        manifest_path = snapshot_root / "manifest.json"
        if _sha256_file(manifest_path) != expected_manifest_sha256:
            raise TestSnapshotError("Snapshot manifest fingerprint mismatch")
        manifest = _load_json_object(manifest_path)
        missing = _REQUIRED_MANIFEST_FIELDS - manifest.keys()
        if missing:
            raise TestSnapshotError(
                "Snapshot manifest is incomplete: "
                f"{', '.join(sorted(missing))}"
            )
        if manifest["format_version"] != _FORMAT_VERSION:
            raise TestSnapshotError("Unsupported snapshot manifest format")
        for field in (
            "snapshot_id",
            "source_identity",
            "git_tree_or_commit",
            "producer",
            "producer_version",
            "capture_id",
            "capture_method",
        ):
            _require_identity(manifest[field], field)
        if (
            manifest["producer"] != _PRODUCER
            or manifest["producer_version"] != _PRODUCER_VERSION
        ):
            raise TestSnapshotError("Snapshot producer identity is unsupported")
        if not re.fullmatch(
            r"[0-9a-f]{40,64}", manifest["git_tree_or_commit"]
        ):
            raise TestSnapshotError("Snapshot Git commit identity is invalid")
        if not re.fullmatch(
            r"sha256:[0-9a-f]{64}", manifest["capture_attestation_sha256"]
        ):
            raise TestSnapshotError(
                "Snapshot capture attestation fingerprint is invalid"
            )
        if manifest["capture_method"] != "atomic_filesystem_snapshot":
            raise TestSnapshotError("Snapshot capture method is unsupported")
        if manifest["destination_identity"] != str(snapshot_root):
            raise TestSnapshotError("Snapshot destination identity mismatch")
        for field, expected in (
            ("scope", scope),
            ("run_identity", run_identity),
            ("gate_identity", gate_identity),
            ("policy_identity", policy_identity),
        ):
            if manifest[field] != expected:
                raise TestSnapshotError(f"Snapshot {field} does not match")
        current_repository = Path(
            repository_root or Path(__file__).resolve().parents[3]
        )
        if manifest["git_tree_or_commit"] != _repository_identity(
            current_repository
        ):
            raise TestSnapshotError(
                "Snapshot Git commit does not match this checkout"
            )
        if manifest["gate_fingerprint"] != _gate_fingerprint(
            current_repository
        ):
            raise TestSnapshotError(
                "Snapshot test-gate inputs do not match this checkout"
            )
        if manifest["workspace_contract"] != {
            "pytest_reads": "derived_workspace_only",
            "workspace_writable": True,
            "snapshot_writable": False,
        }:
            raise TestSnapshotError("Snapshot workspace contract mismatch")
        created_at = _utc_timestamp(manifest["created_at"], "created_at")
        capture_created_at = _utc_timestamp(
            manifest["capture_created_at"], "capture_created_at"
        )
        if created_at < capture_created_at:
            raise TestSnapshotError("Snapshot predates its source capture")
        freshness = manifest["freshness"]
        if not isinstance(freshness, dict):
            raise TestSnapshotError("Snapshot freshness is missing")
        expires_at = _utc_timestamp(
            freshness.get("expires_at"), "freshness.expires_at"
        )
        if (
            _utc_timestamp(freshness.get("created_at"), "freshness.created_at")
            != capture_created_at
        ):
            raise TestSnapshotError(
                "Snapshot freshness timestamp is inconsistent"
            )
        max_age_seconds = freshness.get("max_age_seconds")
        if (
            not isinstance(max_age_seconds, int)
            or isinstance(max_age_seconds, bool)
            or max_age_seconds <= 0
            or expires_at
            != capture_created_at + timedelta(seconds=max_age_seconds)
        ):
            raise TestSnapshotError(
                "Snapshot freshness metadata is inconsistent"
            )
        if now is not None and (
            now.tzinfo is None or now.utcoffset() is None
        ):
            raise TestSnapshotError("Validation time must include a timezone")
        current_time = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        if current_time < capture_created_at or current_time >= expires_at:
            raise TestSnapshotError("Snapshot is not fresh")
        _validate_payload(snapshot_root, manifest)
        return SnapshotValidation(
            "VALID", "snapshot provenance and payload verified", manifest
        )
    except (OSError, TestSnapshotError, TypeError, ValueError) as exc:
        return SnapshotValidation("INVALID", str(exc))


def derive_test_workspace(
    snapshot_root: Path,
    workspace_root: Path,
    *,
    expected_manifest_sha256: str,
    scope: str,
    run_identity: str,
    gate_identity: str,
    policy_identity: str,
) -> Path:
    """Materialize an independent writable copy for one pytest run."""
    snapshot_input = Path(snapshot_root)
    if snapshot_input.is_symlink():
        raise TestSnapshotError("Sealed snapshot cannot be a symlink")
    try:
        snapshot_root = snapshot_input.resolve(strict=True)
    except OSError as exc:
        raise TestSnapshotError(
            f"Cannot resolve sealed snapshot: {exc}"
        ) from exc
    workspace_input = Path(workspace_root)
    if workspace_input.is_symlink():
        raise TestSnapshotError("Writable workspace cannot be a symlink")
    workspace_root = workspace_input.resolve()
    validation = validate_snapshot(
        snapshot_root,
        expected_manifest_sha256=expected_manifest_sha256,
        scope=scope,
        run_identity=run_identity,
        gate_identity=gate_identity,
        policy_identity=policy_identity,
    )
    if validation.status != "VALID" or validation.manifest is None:
        raise TestSnapshotError(f"Snapshot is INVALID: {validation.reason}")
    if workspace_root.exists():
        raise TestSnapshotError(
            f"Workspace destination already exists: {workspace_root}"
        )
    repository_root = Path(__file__).resolve().parents[3]
    try:
        workspace_root.relative_to(repository_root / "data")
    except ValueError:
        pass
    else:
        raise TestSnapshotError(
            "Writable test workspace cannot be inside repository data"
        )
    try:
        workspace_root.relative_to(snapshot_root)
    except ValueError:
        pass
    else:
        raise TestSnapshotError(
            "Writable workspace cannot be inside the sealed snapshot"
        )
    workspace_root.mkdir(parents=True)
    try:
        for entry in validation.manifest["files"]:
            source = snapshot_root / "payload" / entry["path"]
            destination = workspace_root / entry["path"]
            shutil.copyfile(source, destination)
            destination.chmod(0o600)
        receipt = {
            "snapshot_id": validation.manifest["snapshot_id"],
            "manifest_sha256": expected_manifest_sha256,
            "workspace_identity": str(workspace_root),
            "run_identity": run_identity,
            "gate_identity": gate_identity,
            "policy_identity": policy_identity,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        (workspace_root / ".talos-test-workspace.json").write_bytes(
            _canonical_json(receipt) + b"\n"
        )
        (workspace_root / ".talos-test-workspace.json").chmod(0o400)
        return workspace_root
    except Exception:
        shutil.rmtree(workspace_root)
        raise


def verify_sealed_snapshot(
    snapshot_root: Path, expected_manifest_sha256: str
) -> None:
    """Verify post-run that pytest did not alter the sealed artifact."""
    snapshot_input = Path(snapshot_root)
    if snapshot_input.is_symlink():
        raise TestSnapshotError("Sealed snapshot root became a symlink")
    snapshot_root = snapshot_input.resolve()
    manifest_path = snapshot_root / "manifest.json"
    if manifest_path.is_symlink():
        raise TestSnapshotError("Sealed snapshot manifest became a symlink")
    if _sha256_file(manifest_path) != expected_manifest_sha256:
        raise TestSnapshotError(
            "Sealed snapshot manifest changed during pytest"
        )
    manifest = _load_json_object(manifest_path)
    _validate_payload(snapshot_root, manifest)


def database_files_for_workspace(
    workspace_root: Path, database_names: Mapping[str, str]
) -> dict[str, Path]:
    """Resolve required database files from a derived workspace only."""
    workspace_input = Path(workspace_root)
    if workspace_input.is_symlink():
        raise TestSnapshotError("Derived workspace cannot be a symlink")
    try:
        workspace_root = workspace_input.resolve(strict=True)
    except OSError as exc:
        raise TestSnapshotError(
            f"Cannot resolve derived workspace: {exc}"
        ) from exc
    repository_root = Path(__file__).resolve().parents[3]
    try:
        workspace_root.relative_to(repository_root / "data")
    except ValueError:
        pass
    else:
        raise TestSnapshotError(
            "Protected repository data cannot be used as a test workspace"
        )
    if stat.S_IMODE(workspace_root.stat().st_mode) & 0o200 == 0:
        raise TestSnapshotError("Derived workspace is not writable")
    receipt_path = workspace_root / ".talos-test-workspace.json"
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise TestSnapshotError("Workspace provenance receipt is missing")
    receipt = _load_json_object(receipt_path)
    if receipt.get("workspace_identity") != str(workspace_root):
        raise TestSnapshotError("Workspace provenance identity mismatch")
    for field in (
        "manifest_sha256",
        "run_identity",
        "gate_identity",
        "policy_identity",
        "snapshot_id",
    ):
        _require_identity(receipt.get(field), f"workspace.{field}")
    result: dict[str, Path] = {}
    for identity, filename in database_names.items():
        path = workspace_root / filename
        if not path.is_file() or path.is_symlink():
            raise TestSnapshotError(
                f"Derived test workspace is missing {identity}: {filename}"
            )
        result[identity] = path
    return result
