"""Seal approved B06 captures and derive per-run writable workspaces.

SQLite validation never opens protected source files; it runs only on a
disposable copy of the captured files.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
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


_ATOMIC_FORMAT_VERSION = 2
_QUIESCED_FORMAT_VERSION = 3
_PRODUCER = "study_engine.diagnostics.test_isolation_snapshots"
_PRODUCER_VERSION = "2"
_B06_SCOPE_PROFILE_ID = "b06-snapshot-v1"
_SIDECARS = ("-wal", "-shm", "-journal")
_GATE_FILES = (
    "config/test_perimeter.json",
    "scripts/capture_quiesced_test_sources.py",
    "scripts/quality_gate.py",
    "scripts/quality_gate_isolation.py",
    "scripts/test.sh",
    "src/study_engine/diagnostics/test_isolation_snapshots.py",
    "tests/conftest.py",
    "tests/unit/diagnostics/test_quality_gate_isolation.py",
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
    "journal_state",
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


def load_focal_scope_profile(
    repository_root: Path, profile_id: str = _B06_SCOPE_PROFILE_ID
) -> tuple[dict[str, Any], str]:
    """Load the versioned B06 scope profile from the canonical perimeter."""
    perimeter_path = Path(repository_root) / "config" / "test_perimeter.json"
    if perimeter_path.is_symlink() or not perimeter_path.is_file():
        raise TestSnapshotError("Canonical test perimeter is missing")
    perimeter = _load_json_object(perimeter_path)
    profiles = perimeter.get("focal_execution_profiles")
    if not isinstance(profiles, dict):
        raise TestSnapshotError("Focal execution profiles are missing")
    profile = profiles.get(profile_id)
    if not isinstance(profile, dict):
        raise TestSnapshotError(
            f"Unknown focal execution scope profile: {profile_id}"
        )
    if (
        profile.get("profile_version") != 1
        or isinstance(profile.get("profile_version"), bool)
        or not isinstance(profile.get("scope"), str)
        or not profile["scope"].strip()
        or not isinstance(profile.get("nodeid"), str)
        or not isinstance(profile.get("required_logical_inputs"), dict)
        or not isinstance(profile.get("required_snapshot_payload"), dict)
        or not isinstance(profile.get("effective_execution_paths"), list)
        or not isinstance(profile.get("external_execution_resources"), list)
        or not isinstance(profile.get("excluded_path_components"), list)
        or not isinstance(profile.get("fixture_constraints"), dict)
        or any(
            not isinstance(item, str) or not item
            for item in profile.get("effective_execution_paths", [])
        )
        or any(
            not isinstance(item, str) or not item
            for item in profile.get("external_execution_resources", [])
        )
        or any(
            not isinstance(item, str) or not item
            for item in profile.get("excluded_path_components", [])
        )
    ):
        raise TestSnapshotError(
            f"Focal execution scope profile is malformed: {profile_id}"
        )
    digest = _sha256_bytes(_canonical_json(profile))
    return profile, digest


def focal_scope_profile_for_scope(
    repository_root: Path, scope: str
) -> tuple[str, dict[str, Any], str] | None:
    perimeter_path = Path(repository_root) / "config" / "test_perimeter.json"
    if perimeter_path.is_symlink() or not perimeter_path.is_file():
        raise TestSnapshotError("Canonical test perimeter is missing")
    perimeter = _load_json_object(perimeter_path)
    profiles = perimeter.get("focal_execution_profiles")
    if not isinstance(profiles, dict):
        raise TestSnapshotError("Focal execution profiles are missing")
    matches = [
        profile_id
        for profile_id in profiles
        if isinstance(profile_id, str)
        and isinstance(profiles[profile_id], dict)
        and profiles[profile_id].get("scope") == scope
    ]
    if not matches:
        return None
    if len(matches) != 1:
        raise TestSnapshotError("Focal scope identity is ambiguous")
    profile_id = matches[0]
    profile, digest = load_focal_scope_profile(repository_root, profile_id)
    return profile_id, profile, digest


def validate_scope_profile_manifest(
    manifest: Mapping[str, Any], repository_root: Path
) -> tuple[dict[str, Any], str]:
    """Fail closed unless snapshot identities and sidecars match B06 scope."""
    profile_id = manifest.get("scope_profile_id")
    if not isinstance(profile_id, str):
        raise TestSnapshotError("Snapshot scope profile identity is missing")
    profile, profile_digest = load_focal_scope_profile(
        repository_root, profile_id
    )
    if manifest.get("scope") != profile["scope"]:
        raise TestSnapshotError("Snapshot scope does not match its profile")
    if manifest.get("scope_profile_version") != profile["profile_version"]:
        raise TestSnapshotError("Snapshot scope profile version mismatch")
    if manifest.get("scope_profile_sha256") != profile_digest:
        raise TestSnapshotError("Snapshot scope profile digest mismatch")
    logical_inputs = profile["required_logical_inputs"]
    if (
        not logical_inputs
        or any(
            not isinstance(identity, str)
            or not identity
            or not isinstance(filename, str)
            or Path(filename).name != filename
            or not filename.endswith(".db")
            for identity, filename in logical_inputs.items()
        )
        or manifest.get("databases") != logical_inputs
    ):
        raise TestSnapshotError(
            "Snapshot database identities do not satisfy the B06 scope"
        )
    payload_contract = profile["required_snapshot_payload"]
    suffixes = payload_contract.get("sidecar_suffixes")
    if (
        payload_contract.get("sidecar_policy")
        != "record_absent_or_present_for_each_database"
        or not isinstance(suffixes, list)
        or any(not isinstance(suffix, str) for suffix in suffixes)
        or set(suffixes) != set(_SIDECARS)
        or len(suffixes) != len(_SIDECARS)
    ):
        raise TestSnapshotError("B06 snapshot payload profile is invalid")
    for suffix in suffixes:
        state_key = {
            "-wal": "wal_state",
            "-shm": "shm_state",
            "-journal": "journal_state",
        }[suffix]
        sidecar_states = manifest.get(state_key)
        if (
            not isinstance(sidecar_states, dict)
            or set(sidecar_states) != set(logical_inputs)
            or any(
                not isinstance(state, dict)
                or state.get("status") not in {"absent", "present"}
                for state in sidecar_states.values()
            )
        ):
            raise TestSnapshotError(
                f"Snapshot {state_key} does not satisfy the B06 scope"
            )
    return profile, profile_digest


def build_effective_execution_manifest(
    repository_root: Path, profile_id: str = _B06_SCOPE_PROFILE_ID
) -> tuple[dict[str, Any], str]:
    """Fingerprint execution-relevant files, including dirty and untracked."""
    repository_root = Path(repository_root).resolve(strict=True)
    profile, profile_digest = load_focal_scope_profile(
        repository_root, profile_id
    )
    excluded = set(profile["excluded_path_components"])
    roots = profile["effective_execution_paths"]
    if not roots or any(not isinstance(root, str) for root in roots):
        raise TestSnapshotError("Effective execution paths are invalid")

    entries: dict[str, dict[str, str]] = {}
    for relative_root in roots:
        root_path = Path(relative_root)
        if (
            root_path.is_absolute()
            or ".." in root_path.parts
            or not root_path.parts
            or root_path.as_posix() != relative_root
        ):
            raise TestSnapshotError(
                f"Invalid effective execution path: {relative_root!r}"
            )
        target = repository_root / root_path
        if target.is_symlink() or not target.exists():
            raise TestSnapshotError(
                f"Effective execution input is missing or a symlink: "
                f"{relative_root}"
            )
        if target.is_file():
            candidates = [target]
        elif target.is_dir():
            candidates = []

            def raise_walk_error(error: OSError) -> None:
                raise TestSnapshotError(
                    f"Cannot inspect effective execution input: {error}"
                ) from error

            for current, directory_names, filenames in os.walk(
                target,
                topdown=True,
                followlinks=False,
                onerror=raise_walk_error,
            ):
                current_path = Path(current)
                if any(
                    name not in excluded
                    and (current_path / name).is_symlink()
                    for name in directory_names
                ):
                    raise TestSnapshotError(
                        f"Effective execution tree contains a symlink: "
                        f"{relative_root}"
                    )
                directory_names[:] = sorted(
                    name for name in directory_names if name not in excluded
                )
                candidates.extend(
                    current_path / name
                    for name in sorted(filenames)
                    if name not in excluded
                )
        else:
            raise TestSnapshotError(
                f"Effective execution input is not a regular file or "
                f"directory: {relative_root}"
            )

        for candidate in candidates:
            relative_path = candidate.relative_to(repository_root).as_posix()
            if candidate.is_symlink() or not candidate.is_file():
                raise TestSnapshotError(
                    f"Effective execution entry is not a regular file: "
                    f"{relative_path}"
                )
            if any(part in excluded for part in Path(relative_path).parts):
                continue
            if relative_path in entries:
                continue
            entries[relative_path] = {
                "path": relative_path,
                "entry_type": "regular_file",
                "sha256": _sha256_file(candidate),
            }

    entry_list = [entries[path] for path in sorted(entries)]
    for resource in profile["external_execution_resources"]:
        resource_path = Path(resource)
        if (
            resource_path.is_absolute()
            or ".." in resource_path.parts
            or not resource_path.parts
        ):
            raise TestSnapshotError(
                f"Invalid external execution resource: {resource!r}"
            )
        resource_target = repository_root / resource_path
        if resource_target.is_dir():
            if not any(
                entry["path"].startswith(resource_path.as_posix() + "/")
                for entry in entry_list
            ):
                raise TestSnapshotError(
                    f"Required external execution resource is empty: "
                    f"{resource}"
                )
        elif resource_path.as_posix() not in entries:
            raise TestSnapshotError(
                f"Required external execution resource is not bound: "
                f"{resource}"
            )

    manifest = {
        "manifest_schema_version": 1,
        "scope_profile_id": profile_id,
        "scope_profile_sha256": profile_digest,
        "entries": entry_list,
    }
    return manifest, _sha256_bytes(_canonical_json(manifest))


def validate_effective_execution_manifest(
    repository_root: Path,
    manifest: Mapping[str, Any],
    expected_sha256: str,
    profile_id: str,
) -> None:
    """Verify the bound manifest against the worker-visible filesystem."""
    actual_manifest, actual_digest = build_effective_execution_manifest(
        repository_root, profile_id
    )
    if actual_digest != expected_sha256 or dict(manifest) != actual_manifest:
        raise TestSnapshotError(
            "Effective execution manifest does not match the worker checkout"
        )


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
    if Path(__file__).resolve().parents[3] == Path("/workspace/repository"):
        attested_commit = os.environ.get("TALOS_TEST_REPOSITORY_COMMIT")
        if not isinstance(attested_commit, str) or not re.fullmatch(
            r"[0-9a-fA-F]{40,64}", attested_commit
        ):
            raise TestSnapshotError(
                "The isolated worker lacks a host-attested repository commit"
            )
        return attested_commit.lower()

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
    scope_profile_record = focal_scope_profile_for_scope(
        repository_root, scope
    )
    if scope_profile_record is not None:
        profile_id, scope_profile, _ = scope_profile_record
        if database_names != scope_profile["required_logical_inputs"]:
            raise TestSnapshotError(
                "Database identities do not satisfy the canonical B06 scope"
            )
    else:
        profile_id = None
        scope_profile = None
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
    is_atomic_capture = (
        attestation["capture_method"] == "atomic_filesystem_snapshot"
        and attestation["consistency"] == "atomic"
        and attestation["read_only"] is True
    )
    capture_contracts = (
        scope_profile.get("capture_contracts", {})
        if scope_profile is not None
        else {}
    )
    quiesced_contract = (
        capture_contracts.get(policy_identity)
        if isinstance(capture_contracts, dict)
        else None
    )
    is_quiesced_capture = (
        isinstance(quiesced_contract, dict)
        and attestation["capture_method"]
        == quiesced_contract.get("capture_method")
        and attestation["consistency"] == quiesced_contract.get("consistency")
        and attestation["read_only"] is True
        and attestation.get("read_only_semantics")
        == quiesced_contract.get("read_only_semantics")
        and attestation.get("attestation_authority")
        == quiesced_contract.get("attestation_authority")
        and attestation.get("authentication_model")
        == quiesced_contract.get("authentication_model")
        and attestation.get("run_identity") == run_identity
        and attestation.get("gate_identity") == gate_identity
        and attestation.get("policy_identity") == policy_identity
        and attestation.get("quiescence")
        == quiesced_contract.get("quiescence")
    )
    if not (is_atomic_capture or is_quiesced_capture):
        raise TestSnapshotError(
            "Capture attestation method, consistency, policy, or "
            "read-only declaration is unsupported"
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
        if is_quiesced_capture:
            attested_source_files = attestation.get("source_files")
            if not isinstance(attested_source_files, list):
                raise TestSnapshotError(
                    "Quiesced capture source file evidence is missing"
                )
            if attested_source_files != before_records:
                raise TestSnapshotError(
                    "Quiesced capture source file evidence does not match"
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
            "format_version": (
                _QUIESCED_FORMAT_VERSION
                if is_quiesced_capture
                else _ATOMIC_FORMAT_VERSION
            ),
            "snapshot_id": snapshot_id,
            "source_identity": attestation["source_identity"],
            "source_fingerprint": source_fingerprint,
            "source_files": before_records,
            "git_tree_or_commit": _repository_identity(repository_root),
            "gate_fingerprint": _gate_fingerprint(repository_root),
            "wal_state": _sidecar_state(database_names, inventory, "-wal"),
            "shm_state": _sidecar_state(database_names, inventory, "-shm"),
            "journal_state": _sidecar_state(
                database_names, inventory, "-journal"
            ),
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
        if is_quiesced_capture:
            manifest["capture_consistency"] = attestation["consistency"]
            manifest["capture_verification"] = attestation["quiescence"]
        if scope_profile is not None and profile_id is not None:
            _, profile_sha256 = load_focal_scope_profile(
                repository_root, profile_id
            )
            manifest.update(
                {
                    "scope_profile_id": profile_id,
                    "scope_profile_version": scope_profile["profile_version"],
                    "scope_profile_sha256": profile_sha256,
                }
            )
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
    for sidecar_key, suffix in (
        ("wal_state", "-wal"),
        ("shm_state", "-shm"),
        ("journal_state", "-journal"),
    ):
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
        format_version = manifest["format_version"]
        if format_version not in {
            _ATOMIC_FORMAT_VERSION,
            _QUIESCED_FORMAT_VERSION,
        }:
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
            raise TestSnapshotError(
                "Snapshot producer identity is unsupported"
            )
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
        if format_version == _ATOMIC_FORMAT_VERSION:
            if (
                manifest["capture_method"] != "atomic_filesystem_snapshot"
                or manifest.get("capture_consistency", "atomic") != "atomic"
            ):
                raise TestSnapshotError(
                    "Atomic snapshot manifest method is inconsistent"
                )
        else:
            policy_contracts = {}
            scope_record = focal_scope_profile_for_scope(
                Path(repository_root or Path(__file__).resolve().parents[3]),
                scope,
            )
            if scope_record is not None:
                _, profile, _ = scope_record
                policy_contracts = profile.get("capture_contracts", {})
            quiesced_contract = (
                policy_contracts.get(policy_identity)
                if isinstance(policy_contracts, dict)
                else None
            )
            if (
                not isinstance(quiesced_contract, dict)
                or manifest["capture_method"]
                != quiesced_contract.get("capture_method")
                or manifest.get("capture_consistency")
                != quiesced_contract.get("consistency")
                or manifest.get("capture_verification")
                != quiesced_contract.get("quiescence")
            ):
                raise TestSnapshotError(
                    "Quiesced snapshot policy or evidence is unsupported"
                )
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
        current_time = (now or datetime.now(timezone.utc)).astimezone(
            timezone.utc
        )
        if current_time < capture_created_at or current_time >= expires_at:
            raise TestSnapshotError("Snapshot is not fresh")
        _validate_payload(snapshot_root, manifest)
        current_repository = Path(
            repository_root or Path(__file__).resolve().parents[3]
        )
        if (
            focal_scope_profile_for_scope(current_repository, scope)
            is not None
            or "scope_profile_id" in manifest
        ):
            validate_scope_profile_manifest(manifest, current_repository)
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
    workspace_identity: str | None = None,
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
    workspace_identity_value = _require_identity(
        workspace_identity or str(workspace_root), "workspace_identity"
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
            "scope": scope,
            "workspace_identity": workspace_identity_value,
            "run_identity": run_identity,
            "gate_identity": gate_identity,
            "policy_identity": policy_identity,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if "scope_profile_id" in validation.manifest:
            receipt.update(
                {
                    "scope_profile_id": validation.manifest[
                        "scope_profile_id"
                    ],
                    "scope_profile_sha256": validation.manifest[
                        "scope_profile_sha256"
                    ],
                }
            )
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
    workspace_root: Path,
    database_names: Mapping[str, str],
    *,
    expected_workspace_identity: str | None = None,
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
    workspace_identity = _require_identity(
        expected_workspace_identity or str(workspace_root),
        "workspace_identity",
    )
    if receipt.get("workspace_identity") != workspace_identity:
        raise TestSnapshotError("Workspace provenance identity mismatch")
    for field in (
        "manifest_sha256",
        "scope",
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
