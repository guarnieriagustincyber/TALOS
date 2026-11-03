"""Write and validate structured A-PRE run evidence."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import tempfile
from datetime import datetime
from typing import Any

SCHEMA_VERSION = 1
GLOBAL_STATUSES = {"PASS", "FAIL", "ERROR"}
SUITE_STATUSES = {"PASS", "FAIL", "SKIP", "WARNING", "ERROR"}
CLASSIFICATIONS = {
    "required",
    "qualification-required",
    "optional",
    "support-only",
}
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
REQUIRED_INPUTS = {
    "pyproject.toml",
    "requirements.lock",
    "config/test_perimeter.json",
    "scripts/quality_gate.py",
    "scripts/apre_effects.py",
    "scripts/apre_harness.py",
    "scripts/apre_result.py",
    "scripts/verify_apre_result.py",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _safe_repo_file(root: Path, relative: str) -> Path | None:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        return None
    try:
        resolved_root = root.resolve()
        resolved_path = (resolved_root / path).resolve()
    except (OSError, RuntimeError, ValueError):
        return None
    if not resolved_path.is_relative_to(resolved_root):
        return None
    return resolved_path


def _manifest_contract(manifest: Any) -> tuple[dict[str, str], dict[str, str]]:
    if (
        not isinstance(manifest, dict)
        or not _is_integer(manifest.get("schema_version"))
        or manifest.get("schema_version") != 1
    ):
        raise ValueError("unsupported perimeter manifest schema")
    suites = manifest.get("suites")
    overrides = manifest.get("module_overrides")
    if not isinstance(suites, list) or not isinstance(overrides, list):
        raise ValueError(
            "perimeter manifest requires suites and module_overrides"
        )

    suite_classes: dict[str, str] = {}
    for suite in suites:
        if not isinstance(suite, dict):
            raise ValueError("manifest suite entry must be an object")
        path = suite.get("path")
        classification = suite.get("classification")
        path_parts = Path(path).parts if isinstance(path, str) else ()
        if (
            not isinstance(path, str)
            or len(path_parts) != 2
            or path_parts[0] != "tests"
            or ".." in path_parts
            or not isinstance(classification, str)
            or classification
            not in {"required", "qualification-required", "support-only"}
            or path in suite_classes
        ):
            raise ValueError("invalid or duplicate manifest suite")
        suite_classes[path] = classification

    optional: dict[str, str] = {}
    for override in overrides:
        if not isinstance(override, dict):
            raise ValueError("manifest override entry must be an object")
        path = override.get("path")
        reason = override.get("reason")
        path_parts = Path(path).parts if isinstance(path, str) else ()
        if (
            not isinstance(path, str)
            or len(path_parts) < 3
            or path_parts[0] != "tests"
            or ".." in path_parts
            or not path.endswith(".py")
            or suite_classes.get("/".join(path_parts[:2])) != "required"
            or not isinstance(reason, str)
            or not reason.strip()
            or path in optional
        ):
            raise ValueError("invalid or duplicate optional module override")
        optional[path] = reason
    return suite_classes, optional


def verify_result(
    report: Any,
    manifest: Any,
    *,
    repository_root: Path,
    evidence_root: Path,
) -> list[str]:
    """Return all schema, consistency, and referenced-file findings."""
    findings: list[str] = []
    if not isinstance(report, dict):
        return ["report root must be a JSON object"]
    try:
        manifest_suites, manifest_optional = _manifest_contract(manifest)
    except ValueError as error:
        return [str(error)]
    canonical_manifest_path = (
        repository_root / "config" / "test_perimeter.json"
    )
    try:
        canonical_manifest = json.loads(
            canonical_manifest_path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as error:
        return [f"cannot read canonical test perimeter: {error}"]
    if canonical_manifest != manifest:
        findings.append("provided manifest differs from repository perimeter")

    required_top_level = {
        "schema_version",
        "run_id",
        "global_status",
        "started_at",
        "duration_seconds",
        "identity",
        "runtime",
        "command",
        "profile",
        "exit_code",
        "collections",
        "suites",
        "optional_modules",
        "artifacts",
        "sterility",
        "warnings",
        "errors",
    }
    if set(report) != required_top_level:
        findings.append("report fields do not exactly match schema_version 1")
    if (
        not _is_integer(report.get("schema_version"))
        or report.get("schema_version") != SCHEMA_VERSION
    ):
        findings.append("schema_version must equal 1")
    if (
        not isinstance(report.get("run_id"), str)
        or not report["run_id"].strip()
    ):
        findings.append("run_id must be a non-empty string")
    started_at = report.get("started_at")
    if not isinstance(started_at, str):
        findings.append("started_at must be an RFC3339 timestamp")
    else:
        try:
            parsed_time = datetime.fromisoformat(
                started_at.replace("Z", "+00:00")
            )
            if parsed_time.tzinfo is None:
                raise ValueError("timezone is required")
        except ValueError:
            findings.append("started_at must be an RFC3339 timestamp")
    global_status = report.get("global_status")
    if (
        not isinstance(global_status, str)
        or global_status not in GLOBAL_STATUSES
    ):
        findings.append("global_status must be PASS, FAIL, or ERROR")
    if report.get("profile") != "release":
        findings.append("profile must equal release")
    if not _is_integer(report.get("exit_code")):
        findings.append("exit_code must be an integer")

    duration = report.get("duration_seconds")
    if (
        not isinstance(duration, (int, float))
        or isinstance(duration, bool)
        or not math.isfinite(duration)
        or duration < 0
    ):
        findings.append("duration_seconds must be finite and non-negative")

    identity = report.get("identity")
    if not isinstance(identity, dict):
        findings.append("identity must be an object")
        identity = {}
    required_identity = {
        "repository",
        "branch",
        "commit",
        "working_tree_clean",
        "working_tree_diff_sha256",
        "platform",
    }
    if set(identity) != required_identity:
        findings.append("identity fields do not match schema_version 1")
    for field in ("repository", "branch", "platform"):
        if (
            not isinstance(identity.get(field), str)
            or not identity[field].strip()
        ):
            findings.append(f"identity.{field} must be a non-empty string")
    commit = identity.get("commit")
    if not isinstance(commit, str) or not SHA_RE.fullmatch(commit):
        findings.append("identity.commit must be a full 40-character SHA")
    if (
        identity.get("working_tree_clean") is not True
        and report.get("global_status") != "ERROR"
    ):
        findings.append("working_tree_clean must be true")
    if not isinstance(
        identity.get("working_tree_diff_sha256"), str
    ) or not HASH_RE.fullmatch(identity["working_tree_diff_sha256"]):
        findings.append("working_tree_diff_sha256 must be a SHA-256 digest")

    runtime = report.get("runtime")
    if not isinstance(runtime, dict):
        findings.append("runtime must be an object")
        runtime = {}
    if set(runtime) != {
        "python_executable",
        "python_version",
        "uv_version",
        "input_hashes",
    }:
        findings.append("runtime fields do not match schema_version 1")
    for field in ("python_executable", "python_version", "uv_version"):
        if (
            not isinstance(runtime.get(field), str)
            or not runtime[field].strip()
        ):
            findings.append(f"runtime.{field} must be a non-empty string")
    if (
        isinstance(runtime.get("python_executable"), str)
        and not Path(runtime["python_executable"]).is_absolute()
    ):
        findings.append("runtime.python_executable must be absolute")
    if isinstance(runtime.get("python_version"), str) and not runtime[
        "python_version"
    ].startswith("3.10."):
        findings.append("runtime.python_version must use Python 3.10")
    if runtime.get("uv_version") != "0.12.20":
        findings.append("runtime.uv_version must equal 0.12.20")
    input_hashes = runtime.get("input_hashes")
    if not isinstance(input_hashes, dict):
        findings.append("runtime.input_hashes must be an object")
        input_hashes = {}
    if any(not isinstance(key, str) for key in input_hashes):
        findings.append("runtime.input_hashes keys must be strings")
    missing_inputs = REQUIRED_INPUTS - {
        key for key in input_hashes if isinstance(key, str)
    }
    if missing_inputs:
        findings.append(
            f"runtime.input_hashes missing: {sorted(missing_inputs)}"
        )
    for relative, expected_hash in input_hashes.items():
        if (
            not isinstance(relative, str)
            or not isinstance(expected_hash, str)
            or not HASH_RE.fullmatch(expected_hash)
        ):
            findings.append(f"invalid input hash entry: {relative!r}")
            continue
        input_path = _safe_repo_file(repository_root, relative)
        if input_path is None or not input_path.is_file():
            findings.append(
                f"input file is missing or outside repository: {relative}"
            )
        else:
            try:
                actual_hash = sha256_file(input_path)
            except OSError:
                findings.append(f"input file cannot be hashed: {relative}")
            else:
                if actual_hash != expected_hash:
                    findings.append(f"input hash mismatch: {relative}")

    command = report.get("command")
    if (
        not isinstance(command, list)
        or not command
        or any(not isinstance(part, str) or not part for part in command)
    ):
        findings.append("command must be a non-empty argv array")
    elif isinstance(runtime.get("python_executable"), str) and command != [
        runtime["python_executable"],
        "scripts/quality_gate.py",
        "--profile",
        "release",
    ]:
        findings.append(
            "command differs from the fixed release gate invocation"
        )

    collections = report.get("collections")
    count_fields = (
        "collected",
        "passed",
        "failed",
        "skipped",
        "collection_errors",
    )
    if not isinstance(collections, dict) or set(collections) != set(
        count_fields
    ):
        findings.append("collections fields do not match schema_version 1")
        collections = {}
    for field in count_fields:
        if not _is_integer(collections.get(field)) or collections[field] < 0:
            findings.append(
                f"collections.{field} must be a non-negative integer"
            )

    suite_rows = report.get("suites")
    if not isinstance(suite_rows, list):
        findings.append("suites must be an array")
        suite_rows = []
    observed_suites: dict[str, dict[str, Any]] = {}
    for row in suite_rows:
        if not isinstance(row, dict):
            findings.append("suite entry must be an object")
            continue
        path = row.get("path")
        if not isinstance(path, str) or path in observed_suites:
            findings.append("suite path must be a unique string")
            continue
        observed_suites[path] = row
        if row.get("classification") != manifest_suites.get(path):
            findings.append(f"{path}: classification differs from manifest")
        if set(row) != {
            "path",
            "classification",
            "status",
            "collected",
            "passed",
            "failed",
            "skipped",
            "collection_errors",
            "skip_reasons",
            "duration_seconds",
            "warnings",
            "errors",
        }:
            findings.append(f"{path}: fields do not match suite schema")
        classification = row.get("classification")
        status = row.get("status")
        if (
            not isinstance(classification, str)
            or classification not in CLASSIFICATIONS
        ):
            findings.append(f"{path}: invalid classification")
        if not isinstance(status, str) or status not in SUITE_STATUSES:
            findings.append(f"{path}: invalid suite status")
        for field in count_fields:
            value = row.get(field)
            if not _is_integer(value) or value < 0:
                findings.append(
                    f"{path}: {field} must be non-negative integer"
                )
        suite_duration = row.get("duration_seconds")
        if (
            not isinstance(suite_duration, (int, float))
            or isinstance(suite_duration, bool)
            or not math.isfinite(suite_duration)
            or suite_duration < 0
        ):
            findings.append(
                f"{path}: duration_seconds must be finite and non-negative"
            )
        for field in ("skip_reasons", "warnings", "errors"):
            values = row.get(field)
            if not isinstance(values, list) or any(
                not isinstance(value, str) or not value.strip()
                for value in values
            ):
                findings.append(
                    f"{path}: {field} must be an array of non-empty strings"
                )
        if status == "PASS" and (
            row.get("collected", 0) == 0
            or row.get("failed", 0) != 0
            or row.get("skipped", 0) != 0
            or row.get("collection_errors", 0) != 0
        ):
            findings.append(f"{path}: PASS conflicts with suite counts")
        if status == "WARNING" and (
            row.get("collected", 0) == 0
            or row.get("failed", 0) != 0
            or row.get("collection_errors", 0) != 0
            or row.get("skipped", 0) == 0
            or not row.get("skip_reasons")
        ):
            findings.append(
                f"{path}: WARNING requires no failures, collected cases, "
                "and explicit skip reasons"
            )
        if (
            status == "FAIL"
            and row.get("failed", 0) == 0
            and row.get("collection_errors", 0) == 0
        ):
            findings.append(
                f"{path}: FAIL requires a test or collection failure"
            )
        if status == "ERROR" and not row.get("errors"):
            findings.append(f"{path}: ERROR requires an explanation")
        if classification == "support-only" and (
            status != "SKIP" or not row.get("skip_reasons")
        ):
            findings.append(
                f"{path}: support-only suite must be SKIP with a reason"
            )
        if classification != "support-only" and status == "SKIP":
            findings.append(
                f"{path}: executable suite cannot be wholly SKIP in release"
            )
        if (
            classification == "qualification-required"
            and report.get("profile") == "release"
            and status == "SKIP"
        ):
            findings.append(
                f"{path}: release profile must run "
                "qualification-required suite"
            )
        row_counts = [
            row.get(field)
            for field in ("collected", "passed", "failed", "skipped")
        ]
        valid_counts = all(
            _is_integer(value) and value >= 0 for value in row_counts
        )
        if valid_counts and row_counts[0] != sum(row_counts[1:]):
            findings.append(f"{path}: collected count does not reconcile")
    if set(observed_suites) != set(manifest_suites):
        findings.append("suite paths do not exactly match the manifest")

    active = [
        row
        for path, row in observed_suites.items()
        if manifest_suites.get(path) in {"required", "qualification-required"}
    ]
    if all(
        _is_integer(collections.get(field)) and collections[field] >= 0
        for field in count_fields
    ):
        expected_totals = {
            field: sum(
                row.get(field, 0)
                for row in active
                if _is_integer(row.get(field)) and row[field] >= 0
            )
            for field in count_fields
        }
        for field, expected in expected_totals.items():
            if collections.get(field) != expected:
                findings.append(
                    f"collections.{field} does not match suite totals"
                )

    optional_rows = report.get("optional_modules")
    if not isinstance(optional_rows, list):
        findings.append("optional_modules must be an array")
        optional_rows = []
    optional_by_path: dict[str, dict[str, Any]] = {}
    for row in optional_rows:
        if not isinstance(row, dict):
            findings.append("optional module entry must be an object")
            continue
        path = row.get("path")
        if not isinstance(path, str) or path in optional_by_path:
            findings.append("optional module path must be unique")
            continue
        optional_by_path[path] = row
        if set(row) != {"path", "status", "reason"}:
            findings.append(
                f"{path}: optional module fields do not match schema"
            )
        if row.get("status") != "SKIP":
            findings.append(f"{path}: optional module must be SKIP")
        if row.get("reason") != manifest_optional.get(path):
            findings.append(f"{path}: optional reason differs from manifest")
    if set(optional_by_path) != set(manifest_optional):
        findings.append(
            "optional module paths do not exactly match the manifest"
        )

    sterility = report.get("sterility")
    if not isinstance(sterility, dict) or set(sterility) != {
        "before_state_sha256",
        "after_state_sha256",
        "unexpected_changes",
    }:
        findings.append("sterility fields do not match schema_version 1")
        sterility = {}
    for field in ("before_state_sha256", "after_state_sha256"):
        value = sterility.get(field)
        if not isinstance(value, str) or not HASH_RE.fullmatch(value):
            findings.append(f"sterility.{field} must be a SHA-256 digest")
    changes = sterility.get("unexpected_changes")
    if not isinstance(changes, list) or any(
        not isinstance(value, str) or not value.strip() for value in changes
    ):
        findings.append("sterility.unexpected_changes must be a string array")
    if report.get("global_status") == "PASS":
        if report.get("exit_code") != 0:
            findings.append("global PASS requires exit_code 0")
        if changes:
            findings.append(
                "global PASS forbids unexpected filesystem changes"
            )
        if sterility.get("before_state_sha256") != sterility.get(
            "after_state_sha256"
        ):
            findings.append(
                "global PASS requires identical before/after state hashes"
            )
        if any(
            row.get("status") in {"FAIL", "ERROR"}
            for row in observed_suites.values()
        ):
            findings.append("global PASS conflicts with a failing suite")
    elif report.get("global_status") == "FAIL":
        if report.get("exit_code") == 0:
            findings.append("global FAIL requires non-zero exit_code")
        if not any(
            row.get("status") == "FAIL" for row in observed_suites.values()
        ):
            findings.append("global FAIL requires a failing suite")
    elif report.get("global_status") == "ERROR":
        if not report.get("errors"):
            findings.append("global ERROR requires an explanation")
        if report.get("exit_code") == 0:
            findings.append("global ERROR requires non-zero exit_code")
    if (
        identity.get("working_tree_clean") is True
        and identity.get("working_tree_diff_sha256") != EMPTY_SHA256
    ):
        findings.append("clean working tree requires the empty diff SHA-256")

    artifacts = report.get("artifacts")
    if not isinstance(artifacts, list):
        findings.append("artifacts must be an array")
        artifacts = []
    evidence_root = evidence_root.resolve()
    artifact_paths: set[str] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict) or set(artifact) != {
            "path",
            "sha256",
        }:
            findings.append("artifact entry must contain path and sha256")
            continue
        relative = artifact.get("path")
        expected_hash = artifact.get("sha256")
        if (
            not isinstance(relative, str)
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or relative in artifact_paths
        ):
            findings.append("artifact path must be unique and relative")
            continue
        artifact_paths.add(relative)
        if not isinstance(expected_hash, str) or not HASH_RE.fullmatch(
            expected_hash
        ):
            findings.append(f"{relative}: invalid artifact SHA-256")
            continue
        try:
            artifact_path = (evidence_root / relative).resolve()
        except (OSError, RuntimeError, ValueError):
            findings.append(f"{relative}: invalid artifact path")
            continue
        if (
            not artifact_path.is_relative_to(evidence_root)
            or not artifact_path.is_file()
        ):
            findings.append(
                f"{relative}: artifact missing or outside evidence directory"
            )
        else:
            try:
                actual_hash = sha256_file(artifact_path)
            except OSError:
                findings.append(f"{relative}: artifact cannot be hashed")
            else:
                if actual_hash != expected_hash:
                    findings.append(f"{relative}: artifact hash mismatch")

    for field in ("warnings", "errors"):
        values = report.get(field)
        if not isinstance(values, list) or any(
            not isinstance(value, str) or not value.strip() for value in values
        ):
            findings.append(f"{field} must be an array of non-empty strings")
    if isinstance(report.get("warnings"), list) and all(
        isinstance(value, str) for value in report["warnings"]
    ):
        global_warnings = set(report["warnings"])
        for row in observed_suites.values():
            suite_warnings = row.get("warnings")
            if (
                isinstance(suite_warnings, list)
                and all(isinstance(value, str) for value in suite_warnings)
                and not set(suite_warnings).issubset(global_warnings)
            ):
                findings.append("global warnings omit a suite warning")
    if report.get("global_status") == "PASS" and report.get("errors"):
        findings.append("global PASS cannot include errors")
    if not {
        "stdout.txt",
        "stderr.txt",
    }.issubset(artifact_paths):
        findings.append("report requires stdout.txt and stderr.txt artifacts")
    return findings


def write_result(
    report: dict[str, Any],
    manifest: dict[str, Any],
    *,
    repository_root: Path,
    evidence_root: Path,
    output_path: Path,
) -> None:
    findings = verify_result(
        report,
        manifest,
        repository_root=repository_root,
        evidence_root=evidence_root,
    )
    if findings:
        raise ValueError("invalid A-PRE result: " + "; ".join(findings))
    resolved_evidence = evidence_root.resolve()
    resolved_output = output_path.resolve()
    if not resolved_output.is_relative_to(resolved_evidence):
        raise ValueError("result output must be inside the evidence directory")
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=resolved_output.parent,
        prefix=f".{resolved_output.name}.",
        delete=False,
    ) as stream:
        temporary_path = Path(stream.name)
        stream.write(encoded)
        stream.flush()
    try:
        temporary_path.replace(resolved_output)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
