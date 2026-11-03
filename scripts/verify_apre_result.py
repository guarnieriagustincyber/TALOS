"""Independently verify an A-PRE result artifact and referenced files."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

HASH_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
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
REPORT_FIELDS = {
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
COUNT_FIELDS = (
    "collected",
    "passed",
    "failed",
    "skipped",
    "collection_errors",
)
SUITE_FIELDS = {
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
}
IDENTITY_FIELDS = {
    "repository",
    "branch",
    "commit",
    "working_tree_clean",
    "working_tree_diff_sha256",
    "platform",
}
RUNTIME_FIELDS = {
    "python_executable",
    "python_version",
    "uv_version",
    "input_hashes",
}
CLASSIFICATIONS = {
    "required",
    "qualification-required",
    "support-only",
}


def _is_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and HASH_PATTERN.fullmatch(value) is not None


def _safe_file(root: Path, relative: str) -> Path | None:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    try:
        resolved_root = root.resolve()
        resolved = (resolved_root / candidate).resolve()
    except (OSError, RuntimeError, ValueError):
        return None
    return resolved if resolved.is_relative_to(resolved_root) else None


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_contract(
    manifest: Any,
) -> tuple[dict[str, str], dict[str, str], list[str]]:
    problems: list[str] = []
    if (
        not isinstance(manifest, dict)
        or not _is_integer(manifest.get("schema_version"))
        or manifest.get("schema_version") != 1
    ):
        return {}, {}, ["unsupported perimeter manifest schema"]

    suite_entries = manifest.get("suites")
    overrides = manifest.get("module_overrides")
    if not isinstance(suite_entries, list) or not isinstance(overrides, list):
        return {}, {}, ["manifest requires suites and module_overrides arrays"]

    suites: dict[str, str] = {}
    for entry in suite_entries:
        if not isinstance(entry, dict):
            problems.append("manifest suite must be an object")
            continue
        path = entry.get("path")
        category = entry.get("classification")
        pieces = Path(path).parts if isinstance(path, str) else ()
        if (
            not isinstance(path, str)
            or len(pieces) != 2
            or pieces[0] != "tests"
            or ".." in pieces
            or category not in CLASSIFICATIONS
            or path in suites
        ):
            problems.append("manifest contains an invalid or duplicate suite")
            continue
        suites[path] = category

    optional: dict[str, str] = {}
    for entry in overrides:
        if not isinstance(entry, dict):
            problems.append("manifest override must be an object")
            continue
        path = entry.get("path")
        reason = entry.get("reason")
        pieces = Path(path).parts if isinstance(path, str) else ()
        if (
            not isinstance(path, str)
            or len(pieces) < 3
            or pieces[0] != "tests"
            or ".." in pieces
            or not path.endswith(".py")
            or suites.get("/".join(pieces[:2])) != "required"
            or not isinstance(reason, str)
            or not reason.strip()
            or path in optional
        ):
            problems.append("manifest contains an invalid optional override")
            continue
        optional[path] = reason
    return suites, optional, problems


def verify_artifact(
    report: Any,
    manifest: Any,
    *,
    repository_root: Path,
    evidence_root: Path,
) -> list[str]:
    """Check the serialized evidence without using the emitter's validator."""
    issues: list[str] = []
    if not isinstance(report, dict):
        return ["report must be a JSON object"]

    suites_in_manifest, optional_in_manifest, manifest_issues = (
        _manifest_contract(manifest)
    )
    issues.extend(manifest_issues)
    try:
        canonical = json.loads(
            (repository_root / "config/test_perimeter.json").read_text(
                encoding="utf-8"
            )
        )
    except (OSError, json.JSONDecodeError) as error:
        return [f"cannot load canonical perimeter: {error}"]
    if canonical != manifest:
        issues.append("provided manifest differs from canonical perimeter")

    if set(report) != REPORT_FIELDS:
        issues.append("report keys do not match schema version 1")
    if (
        not _is_integer(report.get("schema_version"))
        or report.get("schema_version") != 1
    ):
        issues.append("schema_version must be 1")
    if (
        not isinstance(report.get("run_id"), str)
        or not report["run_id"].strip()
    ):
        issues.append("run_id must be a non-empty string")
    if report.get("profile") != "release":
        issues.append("profile must be release")

    timestamp = report.get("started_at")
    if not isinstance(timestamp, str):
        issues.append("started_at must be a timezone-aware timestamp")
    else:
        try:
            instant = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if instant.utcoffset() is None:
                raise ValueError("timezone missing")
        except ValueError:
            issues.append("started_at must be a timezone-aware timestamp")

    duration = report.get("duration_seconds")
    if (
        not isinstance(duration, (int, float))
        or isinstance(duration, bool)
        or not math.isfinite(duration)
        or duration < 0
    ):
        issues.append("duration_seconds must be finite and non-negative")
    if not _is_integer(report.get("exit_code")):
        issues.append("exit_code must be an integer")

    identity = report.get("identity")
    if not isinstance(identity, dict):
        issues.append("identity must be an object")
        identity = {}
    if set(identity) != IDENTITY_FIELDS:
        issues.append("identity keys do not match schema version 1")
    for field in ("repository", "branch", "platform"):
        value = identity.get(field)
        if not isinstance(value, str) or not value.strip():
            issues.append(f"identity.{field} must be a non-empty string")
    commit = identity.get("commit")
    if not isinstance(commit, str) or not COMMIT_PATTERN.fullmatch(commit):
        issues.append("identity.commit must be a full commit SHA")
    if (
        identity.get("working_tree_clean") is not True
        and report.get("global_status") != "ERROR"
    ):
        issues.append("working_tree_clean must be true unless status is ERROR")
    if not _is_digest(identity.get("working_tree_diff_sha256")):
        issues.append("working_tree_diff_sha256 must be a SHA-256 digest")
    if (
        identity.get("working_tree_clean") is True
        and identity.get("working_tree_diff_sha256") != EMPTY_SHA256
    ):
        issues.append("clean working tree must have the empty diff digest")

    runtime = report.get("runtime")
    if not isinstance(runtime, dict):
        issues.append("runtime must be an object")
        runtime = {}
    if set(runtime) != RUNTIME_FIELDS:
        issues.append("runtime keys do not match schema version 1")
    for field in ("python_executable", "python_version", "uv_version"):
        value = runtime.get(field)
        if not isinstance(value, str) or not value.strip():
            issues.append(f"runtime.{field} must be a non-empty string")
    python_executable = runtime.get("python_executable")
    if (
        isinstance(python_executable, str)
        and not Path(python_executable).is_absolute()
    ):
        issues.append("runtime.python_executable must be absolute")
    python_version = runtime.get("python_version")
    if isinstance(python_version, str) and not python_version.startswith(
        "3.10."
    ):
        issues.append("runtime.python_version must be Python 3.10")
    if runtime.get("uv_version") != "0.12.20":
        issues.append("runtime.uv_version must be 0.12.20")

    inputs = runtime.get("input_hashes")
    if not isinstance(inputs, dict):
        issues.append("runtime.input_hashes must be an object")
        inputs = {}
    if any(not isinstance(name, str) for name in inputs):
        issues.append("input hash paths must be strings")
    missing = REQUIRED_INPUTS - {
        name for name in inputs if isinstance(name, str)
    }
    if missing:
        issues.append(
            f"input hashes missing required files: {sorted(missing)}"
        )
    for name, expected in inputs.items():
        if not isinstance(name, str) or not _is_digest(expected):
            issues.append(f"invalid input hash entry: {name!r}")
            continue
        source = _safe_file(repository_root, name)
        if source is None or not source.is_file():
            issues.append(f"input file missing or outside repository: {name}")
            continue
        try:
            actual = _hash_file(source)
        except OSError:
            issues.append(f"input file cannot be hashed: {name}")
        else:
            if actual != expected:
                issues.append(f"input file hash differs: {name}")

    expected_command = [
        python_executable,
        "scripts/quality_gate.py",
        "--profile",
        "release",
    ]
    command = report.get("command")
    if (
        not isinstance(command, list)
        or not command
        or any(not isinstance(part, str) or not part for part in command)
    ):
        issues.append("command must be a non-empty argv array")
    elif command != expected_command:
        issues.append("command is not the specified release gate invocation")

    totals = report.get("collections")
    if not isinstance(totals, dict) or set(totals) != set(COUNT_FIELDS):
        issues.append("collections keys do not match schema version 1")
        totals = {}
    for field in COUNT_FIELDS:
        value = totals.get(field)
        if not _is_integer(value) or value < 0:
            issues.append(
                f"collections.{field} must be a non-negative integer"
            )

    suite_values = report.get("suites")
    if not isinstance(suite_values, list):
        issues.append("suites must be an array")
        suite_values = []
    suite_map: dict[str, dict[str, Any]] = {}
    for row in suite_values:
        if not isinstance(row, dict):
            issues.append("suite row must be an object")
            continue
        path = row.get("path")
        if not isinstance(path, str) or path in suite_map:
            issues.append("suite paths must be unique strings")
            continue
        suite_map[path] = row
        if set(row) != SUITE_FIELDS:
            issues.append(f"{path}: suite keys do not match schema version 1")
        category = row.get("classification")
        status = row.get("status")
        if category != suites_in_manifest.get(path):
            issues.append(f"{path}: classification differs from perimeter")
        if status not in {"PASS", "FAIL", "SKIP", "WARNING", "ERROR"}:
            issues.append(f"{path}: unsupported suite status")
        for field in COUNT_FIELDS:
            value = row.get(field)
            if not _is_integer(value) or value < 0:
                issues.append(f"{path}: {field} must be non-negative")
        case_counts = [
            row.get(field)
            for field in ("collected", "passed", "failed", "skipped")
        ]
        if all(_is_integer(value) and value >= 0 for value in case_counts):
            if case_counts[0] != sum(case_counts[1:]):
                issues.append(f"{path}: case counts do not reconcile")
        row_duration = row.get("duration_seconds")
        if (
            not isinstance(row_duration, (int, float))
            or isinstance(row_duration, bool)
            or not math.isfinite(row_duration)
            or row_duration < 0
        ):
            issues.append(f"{path}: duration must be finite and non-negative")
        for field in ("skip_reasons", "warnings", "errors"):
            values = row.get(field)
            if not isinstance(values, list) or any(
                not isinstance(value, str) or not value.strip()
                for value in values
            ):
                issues.append(f"{path}: {field} must be non-empty strings")
        if status == "PASS" and (
            row.get("collected", 0) == 0
            or row.get("failed", 0) != 0
            or row.get("skipped", 0) != 0
            or row.get("collection_errors", 0) != 0
        ):
            issues.append(f"{path}: PASS conflicts with counts")
        if status == "WARNING" and (
            row.get("collected", 0) == 0
            or row.get("failed", 0) != 0
            or row.get("collection_errors", 0) != 0
            or row.get("skipped", 0) == 0
            or not row.get("skip_reasons")
        ):
            issues.append(f"{path}: WARNING requires justified skips only")
        if status == "FAIL" and (
            row.get("failed", 0) == 0 and row.get("collection_errors", 0) == 0
        ):
            issues.append(f"{path}: FAIL requires a failure")
        if status == "ERROR" and not row.get("errors"):
            issues.append(f"{path}: ERROR requires details")
        if category == "support-only" and (
            status != "SKIP" or not row.get("skip_reasons")
        ):
            issues.append(f"{path}: support-only must be SKIP with a reason")
        if category != "support-only" and status == "SKIP":
            issues.append(f"{path}: executable suite cannot be wholly skipped")

    if set(suite_map) != set(suites_in_manifest):
        issues.append("suite paths differ from the canonical perimeter")
    active_rows = [
        row
        for path, row in suite_map.items()
        if suites_in_manifest.get(path)
        in {"required", "qualification-required"}
    ]
    if all(
        _is_integer(totals.get(field)) and totals[field] >= 0
        for field in COUNT_FIELDS
    ):
        for field in COUNT_FIELDS:
            observed = sum(
                row.get(field, 0)
                for row in active_rows
                if _is_integer(row.get(field)) and row[field] >= 0
            )
            if totals[field] != observed:
                issues.append(f"collections.{field} differs from suite totals")

    optional_values = report.get("optional_modules")
    if not isinstance(optional_values, list):
        issues.append("optional_modules must be an array")
        optional_values = []
    optional_map: dict[str, dict[str, Any]] = {}
    for row in optional_values:
        if not isinstance(row, dict):
            issues.append("optional module entry must be an object")
            continue
        path = row.get("path")
        if not isinstance(path, str) or path in optional_map:
            issues.append("optional module paths must be unique")
            continue
        optional_map[path] = row
        if set(row) != {"path", "status", "reason"}:
            issues.append(f"{path}: optional module keys are invalid")
        if row.get("status") != "SKIP":
            issues.append(f"{path}: optional module must be skipped")
        if row.get("reason") != optional_in_manifest.get(path):
            issues.append(f"{path}: optional reason differs from perimeter")
    if set(optional_map) != set(optional_in_manifest):
        issues.append("optional modules differ from the canonical perimeter")

    sterility = report.get("sterility")
    sterility_fields = {
        "before_state_sha256",
        "after_state_sha256",
        "unexpected_changes",
    }
    if not isinstance(sterility, dict) or set(sterility) != sterility_fields:
        issues.append("sterility keys do not match schema version 1")
        sterility = {}
    for field in ("before_state_sha256", "after_state_sha256"):
        if not _is_digest(sterility.get(field)):
            issues.append(f"sterility.{field} must be a SHA-256 digest")
    changes = sterility.get("unexpected_changes")
    if not isinstance(changes, list) or any(
        not isinstance(item, str) or not item.strip() for item in changes
    ):
        issues.append("unexpected_changes must be an array of descriptions")

    global_status = report.get("global_status")
    if global_status not in {"PASS", "FAIL", "ERROR"}:
        issues.append("global_status must be PASS, FAIL, or ERROR")
    if global_status == "PASS":
        if report.get("exit_code") != 0:
            issues.append("global PASS requires exit code 0")
        if changes:
            issues.append("global PASS forbids unexpected changes")
        if sterility.get("before_state_sha256") != sterility.get(
            "after_state_sha256"
        ):
            issues.append("global PASS requires identical state hashes")
        if report.get("errors"):
            issues.append("global PASS cannot contain errors")
        if any(
            row.get("status") in {"FAIL", "ERROR"}
            for row in suite_map.values()
        ):
            issues.append("global PASS conflicts with a failed suite")
    elif global_status == "FAIL":
        if report.get("exit_code") == 0:
            issues.append("global FAIL requires a non-zero exit code")
        if not any(row.get("status") == "FAIL" for row in suite_map.values()):
            issues.append("global FAIL requires a failed suite")
    elif global_status == "ERROR":
        if report.get("exit_code") == 0:
            issues.append("global ERROR requires a non-zero exit code")
        if not report.get("errors"):
            issues.append("global ERROR requires an explanation")

    warnings = report.get("warnings")
    errors = report.get("errors")
    for field, values in (("warnings", warnings), ("errors", errors)):
        if not isinstance(values, list) or any(
            not isinstance(value, str) or not value.strip() for value in values
        ):
            issues.append(f"{field} must be an array of non-empty strings")
    if isinstance(warnings, list) and all(
        isinstance(value, str) for value in warnings
    ):
        global_warnings = set(warnings)
        for path, row in suite_map.items():
            row_warnings = row.get("warnings")
            if isinstance(row_warnings, list) and not set(
                row_warnings
            ).issubset(global_warnings):
                issues.append(f"{path}: global warnings omit suite warnings")

    artifact_values = report.get("artifacts")
    if not isinstance(artifact_values, list):
        issues.append("artifacts must be an array")
        artifact_values = []
    evidence = evidence_root.resolve()
    artifact_names: set[str] = set()
    for entry in artifact_values:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            issues.append("artifact must have only path and sha256")
            continue
        name = entry.get("path")
        expected = entry.get("sha256")
        if (
            not isinstance(name, str)
            or Path(name).is_absolute()
            or ".." in Path(name).parts
            or name in artifact_names
        ):
            issues.append("artifact path must be unique and relative")
            continue
        artifact_names.add(name)
        if not _is_digest(expected):
            issues.append(f"{name}: invalid artifact digest")
            continue
        try:
            target = (evidence / name).resolve()
        except (OSError, RuntimeError, ValueError):
            issues.append(f"{name}: artifact path cannot be resolved")
            continue
        if not target.is_relative_to(evidence) or not target.is_file():
            issues.append(
                f"{name}: artifact is missing or escapes evidence root"
            )
            continue
        try:
            actual = _hash_file(target)
        except OSError:
            issues.append(f"{name}: artifact cannot be hashed")
        else:
            if actual != expected:
                issues.append(f"{name}: artifact digest differs")
    if not {"stdout.txt", "stderr.txt"}.issubset(artifact_names):
        issues.append("stdout.txt and stderr.txt are required artifacts")
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(
            json.dumps(
                {"status": "REVIEW REQUIRED", "findings": [str(error)]},
                sort_keys=True,
            )
        )
        return 2

    findings = verify_artifact(
        report,
        manifest,
        repository_root=args.repository_root,
        evidence_root=args.evidence_root,
    )
    status = "PASS" if not findings else "FAIL"
    print(json.dumps({"status": status, "findings": findings}, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
