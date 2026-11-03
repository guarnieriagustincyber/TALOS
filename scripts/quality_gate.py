"""Validate and run the repository's declared test perimeter."""

from __future__ import annotations

import argparse
import ast
import hashlib
import hmac
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PERIMETER_PATH = REPOSITORY_ROOT / "config" / "test_perimeter.json"
TESTS_ROOT = REPOSITORY_ROOT / "tests"
CLASSIFICATIONS = {"required", "qualification-required", "support-only"}
FOCAL_B06_NODEID = (
    "tests/pedagogy/test_talos_vs_notebooklm_e2e.py::"
    "test_p3_debug_query_abstains_without_sufficient_evidence_sse"
)
B06_SYNTHETIC_EXCEPTION = {
    "nodeid": FOCAL_B06_NODEID,
    "fixture": "b06_synthetic_state",
    "working_directory": "captured_workspace_sibling/b06-synthetic",
    "data_origin": "SYNTHETIC",
    "dataset_id": "b06-debug-related-v1",
    "captured_inputs": "provenance_only",
    "legacy_compatibility": "CAPTURED_VECTOR_SCHEMA_COMPATIBILITY_UNVERIFIED",
}
_RUN_ID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


class FocalExecutionError(ValueError):
    """Raised when the B06 execution binding is invalid."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _validate_focal_nodeid(nodeid: str | None) -> str:
    if nodeid != FOCAL_B06_NODEID:
        raise FocalExecutionError(
            "focal mode accepts only the exact B06 pytest nodeid"
        )
    return nodeid


def _validate_focal_fixture_contract(
    repository_root: Path, scope_profile: dict[str, Any]
) -> None:
    """Check that B06 consumes its declared isolated fixture."""
    constraints = scope_profile.get("fixture_constraints")
    if (
        not isinstance(constraints, dict)
        or constraints.get("fixture") != "web_state_test_copy"
        or constraints.get("working_directory") != "derived_snapshot_only"
        or constraints.get("use_mock") is not True
        or constraints.get("database_identities")
        != list(scope_profile.get("required_logical_inputs", {}))
    ):
        raise FocalExecutionError(
            "canonical B06 fixture constraints are invalid"
        )

    test_path = repository_root / FOCAL_B06_NODEID.split("::", 1)[0]
    conftest_path = repository_root / "tests" / "conftest.py"
    try:
        test_tree = ast.parse(test_path.read_text(encoding="utf-8"))
        conftest_tree = ast.parse(conftest_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeError) as exc:
        raise FocalExecutionError(
            f"cannot verify B06 fixture contract: {exc}"
        ) from exc
    function_name = FOCAL_B06_NODEID.split("::", 1)[1]
    fixture_name = constraints["fixture"]
    test_fixture_name = fixture_name
    synthetic = scope_profile.get("b06_synthetic_exception")
    if synthetic is not None:
        if synthetic != B06_SYNTHETIC_EXCEPTION or scope_profile.get("nodeid") != FOCAL_B06_NODEID:
            raise FocalExecutionError("synthetic fixture exception is restricted to exact B06")
        test_fixture_name = synthetic["fixture"]
        synthetic_function = next((node for node in conftest_tree.body
                                   if isinstance(node, ast.FunctionDef)
                                   and node.name == test_fixture_name), None)
        if synthetic_function is None or not any(
            isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "getfixturevalue"
            and any(isinstance(arg, ast.Constant) and arg.value == fixture_name for arg in node.args)
            for node in ast.walk(synthetic_function)
        ):
            raise FocalExecutionError("B06 synthetic fixture must retain captured input provenance")
    test_function = next(
        (
            node
            for node in test_tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == function_name
        ),
        None,
    )
    fixture_function = next(
        (
            node
            for node in conftest_tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == fixture_name
        ),
        None,
    )
    if (
        test_function is None
        or fixture_function is None
        or test_fixture_name
        not in {
            argument.arg
            for argument in (
                test_function.args.posonlyargs + test_function.args.args
            )
        }
        or "_test_isolated_workspace"
        not in {
            argument.arg
            for argument in (
                fixture_function.args.posonlyargs
                + fixture_function.args.args
            )
        }
    ):
        raise FocalExecutionError(
            "B06 test and fixture do not match the canonical scope contract"
        )
    expected_database_map = scope_profile["required_logical_inputs"]
    fixture_database_maps = []
    for node in ast.walk(fixture_function):
        if not isinstance(node, ast.Dict):
            continue
        if all(
            isinstance(key, ast.Constant)
            and isinstance(key.value, str)
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
            for key, value in zip(node.keys, node.values)
        ):
            fixture_database_maps.append(
                {
                    key.value: value.value
                    for key, value in zip(node.keys, node.values)
                }
            )
    if expected_database_map not in fixture_database_maps:
        raise FocalExecutionError(
            "B06 fixture database identities do not match its scope profile"
        )

    container_calls = [
        node
        for node in ast.walk(test_function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "AppContainer"
    ]
    if not any(
        any(
            keyword.arg == "working_dir"
            and isinstance(keyword.value, ast.Name)
            and keyword.value.id == test_fixture_name
            for keyword in call.keywords
        )
        and any(
            keyword.arg == "use_mock"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
            for keyword in call.keywords
        )
        for call in container_calls
    ):
        raise FocalExecutionError(
            "B06 must bind AppContainer to its isolated fixture in mock mode"
        )


def b06_synthetic_workspace(captured_root: Path, nodeid: str) -> Path:
    """The exception grants no caller-selected path and no other test scope."""
    _validate_focal_nodeid(nodeid)
    expected = os.environ.get("TALOS_TEST_WORKSPACE_ROOT")
    if os.environ.get("TALOS_TEST_ISOLATED") != "1" or not expected:
        raise FocalExecutionError("B06 synthetic workspace requires isolated captured inputs")
    captured_root = Path(captured_root)
    if (captured_root.is_symlink() or str(captured_root.resolve()) != expected
            or os.environ.get("TALOS_TEST_WORKSPACE_IDENTITY") != expected):
        raise FocalExecutionError("arbitrary captured workspace is forbidden")
    target = captured_root.parent / "b06-synthetic"
    if target.is_symlink():
        raise FocalExecutionError("B06 synthetic workspace cannot be a symlink")
    return target


def validate_b06_synthetic_state(captured_root: Path, nodeid: str) -> dict[str, Any]:
    from study_engine.retrieval.embedding import DeterministicHashEmbedder
    from study_engine.retrieval.vector_identity import vector_space_id

    workspace = b06_synthetic_workspace(captured_root, nodeid)
    run_id = os.environ.get("TALOS_TEST_RUN_ID", "")
    parent_receipt = captured_root / ".talos-test-workspace.json"
    if not _RUN_ID_PATTERN.fullmatch(run_id) or parent_receipt.is_symlink():
        raise FocalExecutionError("B06 synthetic captured provenance is invalid")
    parent = json.loads(parent_receipt.read_text())
    if (parent.get("run_identity") != run_id
            or parent.get("workspace_identity") != str(captured_root)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", str(parent.get("manifest_sha256", "")))):
        raise FocalExecutionError("B06 synthetic captured provenance mismatch")
    marker = workspace / ".b06-synthetic.json"
    if marker.is_symlink() or not marker.is_file():
        raise FocalExecutionError("B06 synthetic provenance is missing")
    expected = {
        **B06_SYNTHETIC_EXCEPTION,
        "run_id": run_id,
        "captured_manifest_sha256": parent["manifest_sha256"],
        "captured_workspace": str(captured_root),
        "workspace": str(workspace),
        "space_id": vector_space_id(DeterministicHashEmbedder(dimensions=128)),
    }
    if json.loads(marker.read_text()) != expected:
        raise FocalExecutionError("B06 synthetic provenance mismatch")
    for name in ("knowledge_store.db", "vector_store.db", "student_state.db"):
        path = workspace / name
        if path.is_symlink() or not path.is_file():
            raise FocalExecutionError("B06 synthetic database missing or redirected")
    return expected


def build_focal_execution_binding(
    *,
    manifest: dict[str, Any],
    manifest_sha256: str,
    run_id: str,
    profile: str,
    repository_root: Path,
    perimeter_path: Path,
    worker_workspace_identity: str = "/workspace/run/test-data",
) -> tuple[dict[str, Any], str]:
    """Bind B06 snapshot, canonical scope, dirty checkout, and runtime."""
    from study_engine.diagnostics.test_isolation_snapshots import (
        build_effective_execution_manifest,
        load_focal_scope_profile,
    )

    _validate_focal_nodeid(FOCAL_B06_NODEID)
    if profile != "release":
        raise FocalExecutionError("focal B06 requires profile=release")
    if not _RUN_ID_PATTERN.fullmatch(run_id):
        raise FocalExecutionError("focal run_id must be a canonical UUIDv4")
    if manifest.get("run_identity") != run_id:
        raise FocalExecutionError("snapshot run identity does not match")
    if manifest.get("scope") is None or not str(manifest["scope"]).strip():
        raise FocalExecutionError("snapshot scope must not be empty")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", manifest_sha256):
        raise FocalExecutionError("manifest SHA-256 is invalid")

    repository_root = Path(repository_root).resolve(strict=True)
    scope_profile_id = manifest.get("scope_profile_id")
    if not isinstance(scope_profile_id, str):
        raise FocalExecutionError(
            "snapshot is missing the canonical B06 scope profile"
        )
    scope_profile, scope_profile_sha256 = load_focal_scope_profile(
        repository_root, scope_profile_id
    )
    if (
        scope_profile_id != "b06-snapshot-v1"
        or manifest.get("scope") != scope_profile["scope"]
        or manifest.get("scope_profile_version")
        != scope_profile["profile_version"]
        or manifest.get("scope_profile_sha256") != scope_profile_sha256
        or manifest.get("databases")
        != scope_profile["required_logical_inputs"]
    ):
        raise FocalExecutionError(
            "snapshot does not satisfy the canonical B06 scope profile"
        )
    if scope_profile.get("nodeid") != FOCAL_B06_NODEID:
        raise FocalExecutionError(
            "canonical scope profile does not authorize the B06 nodeid"
        )
    _validate_focal_fixture_contract(repository_root, scope_profile)
    effective_manifest, effective_manifest_sha256 = (
        build_effective_execution_manifest(
            repository_root, scope_profile_id
        )
    )
    test_file = repository_root / FOCAL_B06_NODEID.split("::", 1)[0]
    if test_file.is_symlink() or not test_file.is_file():
        raise FocalExecutionError("B06 test file is missing or invalid")
    perimeter_path = Path(perimeter_path).resolve(strict=True)
    try:
        perimeter_path.relative_to(repository_root)
    except ValueError as exc:
        raise FocalExecutionError(
            "test perimeter must be inside the repository"
        ) from exc

    required_manifest_fields = (
        "snapshot_id",
        "source_identity",
        "source_fingerprint",
        "scope",
        "destination_identity",
        "run_identity",
        "gate_identity",
        "policy_identity",
        "gate_fingerprint",
        "git_tree_or_commit",
        "capture_id",
        "capture_attestation_sha256",
    )
    if any(
        not isinstance(manifest.get(field), str)
        or not manifest[field].strip()
        for field in required_manifest_fields
    ):
        raise FocalExecutionError(
            "snapshot manifest lacks required execution binding fields"
        )
    if (
        not isinstance(worker_workspace_identity, str)
        or not Path(worker_workspace_identity).is_absolute()
    ):
        raise FocalExecutionError("worker workspace identity is invalid")

    binding = {
        "schema_version": 2,
        "execution_mode": "focal_test",
        "run_id": run_id,
        "manifest_sha256": manifest_sha256,
        "snapshot_manifest_sha256": manifest_sha256,
        "snapshot_id": manifest["snapshot_id"],
        "scope": manifest["scope"],
        "scope_profile_id": scope_profile_id,
        "scope_profile_version": scope_profile["profile_version"],
        "scope_profile_sha256": scope_profile_sha256,
        "snapshot_database_identities": manifest["databases"],
        "source_identity": manifest["source_identity"],
        "source_fingerprint": manifest["source_fingerprint"],
        "capture_id": manifest["capture_id"],
        "capture_attestation_sha256": manifest[
            "capture_attestation_sha256"
        ],
        "destination_identity": manifest["destination_identity"],
        "profile": profile,
        "perimeter_path": perimeter_path.relative_to(
            repository_root
        ).as_posix(),
        "perimeter_sha256": _sha256_file(perimeter_path),
        "gate_fingerprint": manifest["gate_fingerprint"],
        "git_commit": manifest["git_tree_or_commit"],
        "nodeid": FOCAL_B06_NODEID,
        "b06_synthetic_exception": scope_profile.get("b06_synthetic_exception"),
        "worker_workspace_identity": worker_workspace_identity,
        "effective_execution_manifest_sha256": (
            effective_manifest_sha256
        ),
        "effective_execution_manifest_reference": (
            "binding.effective_execution_manifest"
        ),
        "effective_execution_manifest": effective_manifest,
        "runtime_identity": build_focal_runtime_identity(),
        "test_file": FOCAL_B06_NODEID.split("::", 1)[0],
        "test_file_sha256": _sha256_file(test_file),
        "gate_identity_operational_label": manifest["gate_identity"],
        "policy_identity_operational_label": manifest["policy_identity"],
        "identity_semantics": {
            "gate_identity": (
                "caller-supplied operational label; not normative"
            ),
            "policy_identity": (
                "caller-supplied operational label; not normative"
            ),
        },
    }
    binding_sha256 = (
        f"sha256:{hashlib.sha256(_canonical_json(binding)).hexdigest()}"
    )
    return binding, binding_sha256


def build_focal_runtime_identity() -> dict[str, Any]:
    """Identify only the Python interpreter and pytest runtime used by B06."""
    import pytest

    executable = Path(sys.executable).resolve(strict=True)
    pytest_module = Path(pytest.__file__).resolve(strict=True)
    return {
        "schema_version": 1,
        "python_implementation": sys.implementation.name,
        "python_version": list(sys.version_info[:3]),
        "python_cache_tag": sys.implementation.cache_tag,
        "python_executable_sha256": _sha256_file(executable),
        "pytest_version": pytest.__version__,
        "pytest_module_sha256": _sha256_file(pytest_module),
    }


def validate_focal_execution_binding(
    binding_path: Path,
    *,
    expected_sha256: str,
    profile: str,
    repository_root: Path,
    workspace_root: Path,
    environment: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Validate the worker's bound B06, snapshot receipt, and inputs."""
    from study_engine.diagnostics.test_isolation_snapshots import (
        TestSnapshotError,
        build_effective_execution_manifest,
        load_focal_scope_profile,
    )

    binding_path = Path(binding_path)
    if binding_path.is_symlink() or not binding_path.is_file():
        raise FocalExecutionError("focal execution binding is missing")
    try:
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FocalExecutionError(
            f"focal execution binding is invalid: {exc}"
        ) from exc
    if not isinstance(binding, dict):
        raise FocalExecutionError("focal execution binding must be an object")
    actual_sha256 = (
        f"sha256:{hashlib.sha256(_canonical_json(binding)).hexdigest()}"
    )
    if actual_sha256 != expected_sha256:
        raise FocalExecutionError("focal execution binding digest mismatch")
    if profile != "release" or binding.get("profile") != profile:
        raise FocalExecutionError("focal execution profile mismatch")
    if binding.get("schema_version") != 2:
        raise FocalExecutionError("unsupported focal execution binding")
    if binding.get("execution_mode") != "focal_test":
        raise FocalExecutionError("execution binding is not focal mode")
    _validate_focal_nodeid(binding.get("nodeid"))
    if binding.get("test_file") != FOCAL_B06_NODEID.split("::", 1)[0]:
        raise FocalExecutionError("focal test file identity mismatch")
    if binding.get("perimeter_path") != "config/test_perimeter.json":
        raise FocalExecutionError("bound test perimeter identity mismatch")

    repository_root = Path(repository_root).resolve(strict=True)
    workspace_root = Path(workspace_root).resolve(strict=True)
    if environment is None:
        environment = os.environ
    if environment.get("TALOS_TEST_WORKSPACE_ROOT") != str(workspace_root):
        raise FocalExecutionError("worker workspace identity mismatch")
    if (
        binding.get("worker_workspace_identity") != str(workspace_root)
        or environment.get("TALOS_TEST_WORKSPACE_IDENTITY")
        != binding.get("worker_workspace_identity")
    ):
        raise FocalExecutionError("bound worker workspace identity mismatch")

    scope_profile_id = binding.get("scope_profile_id")
    if not isinstance(scope_profile_id, str):
        raise FocalExecutionError("bound scope profile identity is missing")
    try:
        scope_profile, scope_profile_sha256 = load_focal_scope_profile(
            repository_root, scope_profile_id
        )
        current_effective_manifest, current_effective_sha256 = (
            build_effective_execution_manifest(
                repository_root, scope_profile_id
            )
        )
    except TestSnapshotError as exc:
        raise FocalExecutionError(
            f"worker execution identity is invalid: {exc}"
        ) from exc
    if (
        scope_profile_id != "b06-snapshot-v1"
        or scope_profile.get("nodeid") != FOCAL_B06_NODEID
        or binding.get("scope") != scope_profile.get("scope")
        or binding.get("scope_profile_version")
        != scope_profile.get("profile_version")
        or binding.get("scope_profile_sha256") != scope_profile_sha256
        or binding.get("effective_execution_manifest")
        != current_effective_manifest
        or binding.get("effective_execution_manifest_sha256")
        != current_effective_sha256
        or binding.get("effective_execution_manifest_reference")
        != "binding.effective_execution_manifest"
    ):
        raise FocalExecutionError(
            "worker scope or effective execution manifest mismatch"
        )
    _validate_focal_fixture_contract(repository_root, scope_profile)
    if binding.get("b06_synthetic_exception") != scope_profile.get("b06_synthetic_exception"):
        raise FocalExecutionError("bound B06 synthetic exception does not match scope")
    if binding.get("snapshot_database_identities") != (
        scope_profile.get("required_logical_inputs")
    ):
        raise FocalExecutionError(
            "bound snapshot database identities do not match B06 scope"
        )
    if binding.get("snapshot_manifest_sha256") != binding.get(
        "manifest_sha256"
    ):
        raise FocalExecutionError("bound snapshot manifest digest mismatch")
    if binding.get("runtime_identity") != build_focal_runtime_identity():
        raise FocalExecutionError("worker runtime identity mismatch")

    test_file = repository_root / binding["test_file"]
    perimeter_path = repository_root / binding.get("perimeter_path", "")
    if test_file.is_symlink() or not test_file.is_file():
        raise FocalExecutionError("B06 test file is missing or invalid")
    if _sha256_file(test_file) != binding.get("test_file_sha256"):
        raise FocalExecutionError("B06 test file fingerprint mismatch")
    if perimeter_path.is_symlink() or not perimeter_path.is_file():
        raise FocalExecutionError("bound test perimeter is missing or invalid")
    if _sha256_file(perimeter_path) != binding.get("perimeter_sha256"):
        raise FocalExecutionError("test perimeter fingerprint mismatch")
    from study_engine.diagnostics.test_isolation_snapshots import (
        _gate_fingerprint,
    )

    if _gate_fingerprint(repository_root) != binding.get("gate_fingerprint"):
        raise FocalExecutionError("test-gate input fingerprint mismatch")

    run_id = environment.get("TALOS_TEST_RUN_ID", "")
    if (
        not _RUN_ID_PATTERN.fullmatch(run_id)
        or binding.get("run_id") != run_id
    ):
        raise FocalExecutionError("worker run identity mismatch")
    if (
        binding.get("gate_identity_operational_label")
        != environment.get("TALOS_TEST_GATE_ID")
        or binding.get("policy_identity_operational_label")
        != environment.get("TALOS_TEST_POLICY_ID")
    ):
        raise FocalExecutionError("worker snapshot labels do not match")
    if binding.get("git_commit") != environment.get(
        "TALOS_TEST_REPOSITORY_COMMIT"
    ):
        raise FocalExecutionError("worker repository identity mismatch")
    if (
        not isinstance(binding.get("scope"), str)
        or not binding["scope"].strip()
    ):
        raise FocalExecutionError("bound snapshot scope is empty")
    if not re.fullmatch(
        r"sha256:[0-9a-f]{64}", str(binding.get("manifest_sha256", ""))
    ):
        raise FocalExecutionError("bound manifest digest is invalid")
    if not re.fullmatch(
        r"sha256:[0-9a-f]{64}",
        str(binding.get("capture_attestation_sha256", "")),
    ):
        raise FocalExecutionError(
            "bound capture attestation digest is invalid"
        )

    receipt_path = workspace_root / ".talos-test-workspace.json"
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise FocalExecutionError("derived workspace receipt is missing")
    try:
        workspace_receipt = json.loads(
            receipt_path.read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as exc:
        raise FocalExecutionError(
            f"derived workspace receipt is invalid: {exc}"
        ) from exc
    if not isinstance(workspace_receipt, dict):
        raise FocalExecutionError(
            "derived workspace receipt must be an object"
        )
    expected_receipt = {
        "manifest_sha256": binding["manifest_sha256"],
        "snapshot_id": binding["snapshot_id"],
        "scope": binding["scope"],
        "workspace_identity": environment.get(
            "TALOS_TEST_WORKSPACE_IDENTITY"
        ),
        "run_identity": run_id,
        "gate_identity": environment.get("TALOS_TEST_GATE_ID"),
        "policy_identity": environment.get("TALOS_TEST_POLICY_ID"),
        "scope_profile_id": binding["scope_profile_id"],
        "scope_profile_sha256": binding["scope_profile_sha256"],
    }
    if any(
        workspace_receipt.get(field) != value
        for field, value in expected_receipt.items()
    ):
        raise FocalExecutionError(
            "derived workspace receipt does not match focal binding"
        )
    return binding


class PerimeterError(ValueError):
    """Raised when the discovered tests do not match the declared perimeter."""


@dataclass(frozen=True)
class Suite:
    path: str
    classification: str
    reason: str
    modules: tuple[str, ...]


@dataclass(frozen=True)
class Perimeter:
    suites: tuple[Suite, ...]
    optional_modules: dict[str, str]
    module_classifications: dict[str, str]
    informative_tests: dict[str, str] = field(default_factory=dict)


def _repo_test_path(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise PerimeterError(f"{field} must be a repository-relative path.")
    path = Path(value)
    if (
        path.is_absolute()
        or ".." in path.parts
        or not path.parts
        or path.parts[0] != "tests"
    ):
        raise PerimeterError(f"Invalid {field} path: {value!r}.")
    return path.as_posix()


def validate_perimeter(repo_root: Path, manifest_path: Path) -> Perimeter:
    """Load the perimeter and reject unclassified discovered tests."""

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}.")
            result[key] = value
        return result

    try:
        manifest = json.loads(
            manifest_path.read_text(encoding="utf-8"),
            object_pairs_hook=unique_object,
        )
    except (OSError, ValueError) as error:
        raise PerimeterError(
            f"Cannot read test perimeter {manifest_path}: {error}"
        ) from error

    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise PerimeterError(
            "Test perimeter must be an object with schema_version 1."
        )

    suite_entries = manifest.get("suites")
    override_entries = manifest.get("module_overrides")
    informative_test_entries = manifest.get("informative_tests", [])
    if not isinstance(suite_entries, list) or not isinstance(
        override_entries, list
    ) or not isinstance(informative_test_entries, list):
        raise PerimeterError(
            "Test perimeter requires 'suites', 'module_overrides', and an "
            "optional 'informative_tests' list."
        )

    tests_root = repo_root / "tests"
    discovered_files = sorted(
        path
        for path in tests_root.rglob("test_*.py")
        if not any(
            part.startswith(".") or part == "__pycache__"
            for part in path.relative_to(tests_root).parts
        )
    )
    if not discovered_files:
        raise PerimeterError(
            "No test_*.py modules were discovered under tests/."
        )

    discovered_suites: dict[str, list[str]] = defaultdict(list)
    for path in discovered_files:
        relative = path.relative_to(repo_root).as_posix()
        parts = path.relative_to(tests_root).parts
        suite_path = "tests" if len(parts) == 1 else f"tests/{parts[0]}"
        discovered_suites[suite_path].append(relative)

    registered: dict[str, tuple[str, str]] = {}
    for entry in suite_entries:
        if not isinstance(entry, dict):
            raise PerimeterError("Every suite entry must be an object.")
        suite_path = _repo_test_path(entry.get("path"), "suite")
        classification = entry.get("classification")
        reason = entry.get("reason")
        if (
            not isinstance(classification, str)
            or classification not in CLASSIFICATIONS
        ):
            raise PerimeterError(
                f"{suite_path}: classification must be one of "
                f"{', '.join(sorted(CLASSIFICATIONS))}."
            )
        if not isinstance(reason, str) or not reason.strip():
            raise PerimeterError(
                f"{suite_path}: a non-empty classification reason is required."
            )
        if suite_path in registered:
            raise PerimeterError(
                f"Duplicate suite classification: {suite_path}."
            )
        registered[suite_path] = (classification, reason.strip())

    discovered_paths = set(discovered_suites)
    registered_paths = set(registered)
    unknown = sorted(discovered_paths - registered_paths)
    stale = sorted(registered_paths - discovered_paths)
    if unknown or stale:
        details = []
        if unknown:
            details.append(f"unclassified test suites: {', '.join(unknown)}")
        if stale:
            details.append(
                f"registered suites with no test modules: {', '.join(stale)}"
            )
        raise PerimeterError("; ".join(details))

    discovered_module_paths = discovered_files_as_strings(discovered_suites)
    optional_modules: dict[str, str] = {}
    informative_tests: dict[str, str] = {}
    module_classifications = {
        module: registered[suite_path][0]
        for suite_path, modules in discovered_suites.items()
        for module in modules
    }
    for entry in override_entries:
        if not isinstance(entry, dict):
            raise PerimeterError("Every module override must be an object.")
        module_path = _repo_test_path(entry.get("path"), "module override")
        reason = entry.get("reason")
        if entry.get("classification") != "optional":
            raise PerimeterError(
                f"{module_path}: module overrides must be optional."
            )
        if not isinstance(reason, str) or not reason.strip():
            raise PerimeterError(
                f"{module_path}: an optional module requires a reason."
            )
        if module_path not in discovered_module_paths:
            raise PerimeterError(
                f"Optional module is not a discovered test module: "
                f"{module_path}."
            )
        if module_classifications[module_path] != "required":
            raise PerimeterError(
                f"{module_path}: optional module override conflicts with "
                "suite classification "
                f"{module_classifications[module_path]!r}."
            )
        if module_path in optional_modules:
            raise PerimeterError(f"Duplicate module override: {module_path}.")
        optional_modules[module_path] = reason.strip()
        module_classifications[module_path] = "optional"

    for entry in informative_test_entries:
        if not isinstance(entry, dict):
            raise PerimeterError(
                "Every informative test entry must be an object."
            )
        nodeid = entry.get("nodeid")
        reason = entry.get("reason")
        if not isinstance(nodeid, str) or nodeid.count("::") != 1:
            raise PerimeterError(
                "Informative tests require an exact module::test nodeid."
            )
        module_path, test_name = nodeid.split("::")
        module_path = _repo_test_path(module_path, "informative test")
        if not test_name.isidentifier() or not test_name.startswith("test_"):
            raise PerimeterError(
                f"{nodeid}: informative test nodeid is not an exact test."
            )
        canonical_nodeid = f"{module_path}::{test_name}"
        if canonical_nodeid != nodeid:
            raise PerimeterError(
                f"{nodeid}: informative test nodeid is not canonical."
            )
        if not isinstance(reason, str) or not reason.strip():
            raise PerimeterError(
                f"{nodeid}: an informative test requires a reason."
            )
        if module_path not in discovered_module_paths:
            raise PerimeterError(
                f"Informative test module is not discovered: {module_path}."
            )
        if module_classifications[module_path] != "qualification-required":
            raise PerimeterError(
                f"{nodeid}: informative tests must belong to a "
                "qualification-required suite."
            )
        test_path = repo_root / module_path
        try:
            test_tree = ast.parse(test_path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeError) as error:
            raise PerimeterError(
                f"Cannot inspect informative test {nodeid}: {error}"
            ) from error
        if not any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == test_name
            for node in test_tree.body
        ):
            raise PerimeterError(
                f"Informative test nodeid does not identify a test function: "
                f"{nodeid}."
            )
        if nodeid in informative_tests:
            raise PerimeterError(f"Duplicate informative test: {nodeid}.")
        informative_tests[nodeid] = reason.strip()

    if set(module_classifications) != discovered_module_paths:
        raise PerimeterError(
            "Every discovered test module must resolve to exactly one "
            "classification."
        )

    suites = tuple(
        Suite(
            path=path,
            classification=registered[path][0],
            reason=registered[path][1],
            modules=tuple(discovered_suites[path]),
        )
        for path in sorted(registered)
    )
    return Perimeter(
        suites=suites,
        optional_modules=optional_modules,
        module_classifications=module_classifications,
        informative_tests=informative_tests,
    )


def discovered_files_as_strings(
    discovered_suites: dict[str, list[str]],
) -> set[str]:
    return {
        module for modules in discovered_suites.values() for module in modules
    }


def _is_assertion_failure(report: Any) -> bool:
    repr_crash = getattr(getattr(report, "longrepr", None), "reprcrash", None)
    message = getattr(repr_crash, "message", None)
    return isinstance(message, str) and (
        message == "AssertionError" or message.startswith("AssertionError:")
    )


class SuiteResults:
    """Collect pytest outcomes once per item, grouped by registered suite."""

    def __init__(
        self,
        suite_paths: list[str],
        *,
        expected_nodeid: str | None = None,
        informative_tests: dict[str, str] | None = None,
    ) -> None:
        self.suite_paths = suite_paths
        self.expected_nodeid = expected_nodeid
        self.informative_tests = informative_tests or {}
        self.collected_nodeids: list[str] = []
        self.collected: dict[str, int] = defaultdict(int)
        self.outcomes: dict[str, dict[str, str]] = defaultdict(dict)
        self.collection_failures: dict[str, int] = defaultdict(int)
        self.non_call_failures: dict[str, int] = defaultdict(int)
        self.durations: dict[str, float] = defaultdict(float)
        self.skip_reasons: dict[str, list[str]] = defaultdict(list)
        self.errors: dict[str, list[str]] = defaultdict(list)
        self.warnings: dict[str, list[str]] = defaultdict(list)
        self.global_warnings: list[str] = []

    def suite_for_nodeid(self, nodeid: str) -> str:
        module_path = nodeid.split("::", 1)[0]
        if not module_path.startswith("tests/"):
            module_path = f"tests/{module_path}"
        for suite_path in self.suite_paths:
            if module_path == suite_path or module_path.startswith(
                f"{suite_path}/"
            ):
                return suite_path
        return "unclassified"

    def pytest_collection_finish(self, session: Any) -> None:
        self.collected_nodeids = [
            item.nodeid for item in session.items
        ]
        if self.expected_nodeid is not None and self.collected_nodeids != [
            self.expected_nodeid
        ]:
            session.shouldfail = (
                "Focal Quality Gate must collect exactly the requested "
                f"nodeid: {self.expected_nodeid}"
            )
        for item in session.items:
            self.collected[self.suite_for_nodeid(item.nodeid)] += 1

    def pytest_runtest_logreport(self, report: Any) -> None:
        suite_path = self.suite_for_nodeid(report.nodeid)
        self.durations[suite_path] += float(report.duration)
        if report.when == "call":
            outcome = report.outcome
            if (
                outcome == "failed"
                and report.nodeid in self.informative_tests
                and _is_assertion_failure(report)
            ):
                outcome = "informative_failed"
            self.outcomes[suite_path][report.nodeid] = outcome
        elif report.failed:
            self.non_call_failures[suite_path] += 1
            self.outcomes[suite_path][report.nodeid] = "failed"
        elif report.skipped and report.nodeid not in self.outcomes[suite_path]:
            self.outcomes[suite_path][report.nodeid] = "skipped"
        if report.skipped:
            reason = str(report.longrepr)
            if reason not in self.skip_reasons[suite_path]:
                self.skip_reasons[suite_path].append(reason)
        elif report.failed:
            error = str(report.longrepr)
            if error not in self.errors[suite_path]:
                self.errors[suite_path].append(error)

    def pytest_collectreport(self, report: Any) -> None:
        if report.failed:
            suite_path = self.suite_for_nodeid(report.nodeid)
            self.collection_failures[suite_path] += 1
            self.errors[suite_path].append(str(report.longrepr))

    def pytest_warning_recorded(
        self,
        warning_message: Warning,
        when: str,
        nodeid: str,
        location: tuple[str, int, str] | None,
    ) -> None:
        del when, location
        message = str(warning_message.message)
        if nodeid:
            suite_path = self.suite_for_nodeid(nodeid)
            if message not in self.warnings[suite_path]:
                self.warnings[suite_path].append(message)
        elif message not in self.global_warnings:
            self.global_warnings.append(message)

    def counts(self, suite_path: str) -> dict[str, int]:
        outcomes = self.outcomes[suite_path].values()
        return {
            "collected": self.collected[suite_path],
            "passed": sum(outcome == "passed" for outcome in outcomes),
            "failed": sum(
                outcome in {"failed", "informative_failed"}
                for outcome in outcomes
            ),
            "skipped": sum(outcome == "skipped" for outcome in outcomes),
            "collection_errors": self.collection_failures[suite_path],
        }

    def informative_failures(self, perimeter: Perimeter) -> list[str]:
        return sorted(
            nodeid
            for suite_outcomes in self.outcomes.values()
            for nodeid, outcome in suite_outcomes.items()
            if outcome == "informative_failed"
            and nodeid in perimeter.informative_tests
        )

    def total_failed_tests(self) -> int:
        return sum(
            outcome in {"failed", "informative_failed"}
            for suite_outcomes in self.outcomes.values()
            for outcome in suite_outcomes.values()
        )

    def total_non_call_failures(self) -> int:
        return sum(self.non_call_failures.values()) + sum(
            self.collection_failures.values()
        )

    def suite_status(
        self,
        suite_path: str,
        counts: dict[str, int],
        informative_tests: dict[str, str],
    ) -> str:
        if counts["collection_errors"]:
            return "ERROR"
        if counts["collected"] == 0:
            return "ERROR"
        if counts["skipped"]:
            return "FAIL"
        if self.non_call_failures[suite_path]:
            return "ERROR"
        failed_nodeids = {
            nodeid
            for nodeid, outcome in self.outcomes[suite_path].items()
            if outcome == "failed"
        }
        informative_failed_nodeids = {
            nodeid
            for nodeid, outcome in self.outcomes[suite_path].items()
            if outcome == "informative_failed"
        }
        if failed_nodeids:
            return "FAIL"
        if informative_failed_nodeids:
            if informative_failed_nodeids <= informative_tests.keys():
                return "INFORMATIVE_FAIL"
            return "FAIL"
        return "PASS"

    def gate_result(
        self,
        perimeter: Perimeter,
        profile: str,
        pytest_exit_code: int,
    ) -> tuple[str, int]:
        active_suites = [
            suite
            for suite in perimeter.suites
            if suite.classification == "required"
            or (
                profile == "release"
                and suite.classification == "qualification-required"
            )
        ]
        statuses = {
            suite.path: self.suite_status(
                suite.path, self.counts(suite.path), perimeter.informative_tests
            )
            for suite in active_suites
        }
        statuses_allow_gate = all(
            status in {"PASS", "INFORMATIVE_FAIL"}
            for status in statuses.values()
        )
        informative_failures = self.informative_failures(perimeter)
        only_informative_failures = (
            bool(informative_failures)
            and self.total_failed_tests() == len(informative_failures)
            and self.total_non_call_failures() == 0
            and statuses_allow_gate
        )
        if (
            pytest_exit_code == 0
            and statuses_allow_gate
            and not informative_failures
            and self.total_failed_tests() == 0
            and self.total_non_call_failures() == 0
        ):
            return "PASS", 0
        if pytest_exit_code == 1 and only_informative_failures:
            return "PASS_WITH_INFORMATIVE_FAILURES", 0
        return "FAIL", 1

    def focal_payload(self, exit_code: int) -> dict[str, Any]:
        if self.expected_nodeid is None:
            raise ValueError("focal result requires an expected nodeid")
        outcomes = self.outcomes["tests/pedagogy"]
        return {
            "schema_version": 1,
            "profile": "release",
            "expected_nodeid": self.expected_nodeid,
            "collected_nodeids": self.collected_nodeids,
            "exactly_one_selected_test": self.collected_nodeids
            == [self.expected_nodeid],
            "test_outcome": outcomes.get(self.expected_nodeid),
            "pytest_exit_code": int(exit_code),
        }

    def collector_payload(
        self,
        perimeter: Perimeter,
        profile: str,
        exit_code: int,
    ) -> dict[str, Any]:
        suite_rows = []
        totals = {
            "collected": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "collection_errors": 0,
        }
        for suite in perimeter.suites:
            if suite.classification == "support-only":
                suite_rows.append(
                    {
                        "path": suite.path,
                        "classification": suite.classification,
                        "status": "SKIP",
                        "collected": 0,
                        "passed": 0,
                        "failed": 0,
                        "skipped": 0,
                        "collection_errors": 0,
                        "skip_reasons": [suite.reason],
                        "duration_seconds": 0.0,
                        "warnings": [],
                        "errors": [],
                    }
                )
                continue

            counts = self.counts(suite.path)
            active = suite.classification == "required" or (
                profile == "release"
                and suite.classification == "qualification-required"
            )
            if not active:
                status = "SKIP"
                skip_reasons = ["excluded by selected profile"]
                errors = []
            else:
                skip_reasons = self.skip_reasons[suite.path]
                status = self.suite_status(
                    suite.path, counts, perimeter.informative_tests
                )
                errors = self.errors[suite.path]
                if counts["collected"] == 0 and not errors:
                    errors = ["active suite collected no tests"]
                elif counts["skipped"] and not errors:
                    errors = ["active suite contains skipped tests"]

            suite_rows.append(
                {
                    "path": suite.path,
                    "classification": suite.classification,
                    "status": status,
                    **counts,
                    "skip_reasons": skip_reasons,
                    "duration_seconds": self.durations[suite.path],
                    "warnings": self.warnings[suite.path],
                    "errors": errors,
                }
            )
            if active:
                for field, count in counts.items():
                    totals[field] += count

        gate_status, gate_exit_code = self.gate_result(
            perimeter, profile, int(exit_code)
        )
        return {
            "schema_version": 1,
            "profile": profile,
            "pytest_exit_code": int(exit_code),
            "gate_status": gate_status,
            "gate_exit_code": gate_exit_code,
            "collections": totals,
            "suites": suite_rows,
            "informative_tests": [
                {
                    "nodeid": nodeid,
                    "reason": reason,
                    "outcome": (
                        "failed"
                        if self.outcomes[self.suite_for_nodeid(nodeid)].get(
                            nodeid
                        )
                        == "informative_failed"
                        else self.outcomes[
                            self.suite_for_nodeid(nodeid)
                        ].get(nodeid, "not_collected")
                    ),
                    "status": (
                        "INFORMATIVE_FAIL"
                        if self.outcomes[self.suite_for_nodeid(nodeid)].get(
                            nodeid
                        )
                        == "informative_failed"
                        else self.outcomes[self.suite_for_nodeid(nodeid)].get(
                            nodeid, "NOT_COLLECTED"
                        ).upper()
                    ),
                }
                for nodeid, reason in sorted(
                    perimeter.informative_tests.items()
                )
            ],
            "optional_modules": [
                {
                    "path": path,
                    "status": "SKIP",
                    "reason": reason,
                }
                for path, reason in sorted(perimeter.optional_modules.items())
            ],
            "warnings": self.global_warnings
            + [
                warning
                for suite_warnings in self.warnings.values()
                for warning in suite_warnings
                if warning not in self.global_warnings
            ],
        }

    def write_collector(
        self, output_path: Path, payload: dict[str, Any]
    ) -> None:
        output = output_path.resolve()
        if output.is_relative_to(REPOSITORY_ROOT.resolve()):
            raise ValueError("collector output must be outside the repository")
        output.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(
            payload, ensure_ascii=False, indent=2, sort_keys=True
        )
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(encoded + "\n")
            stream.flush()
        try:
            temporary_path.replace(output)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()


def run_gate(
    profile: str,
    perimeter: Perimeter,
    *,
    effects_output: Path | None = None,
    scratch_root: Path | None = None,
    collector_output: Path | None = None,
    focal_nodeid: str | None = None,
    focal_result_output: Path | None = None,
    focal_binding_sha256: str | None = None,
    focal_binding_path: Path | None = None,
) -> int:
    import pytest

    if focal_nodeid is not None:
        _validate_focal_nodeid(focal_nodeid)
        if (
            profile != "release"
            or focal_result_output is None
            or focal_binding_sha256 is None
            or focal_binding_path is None
        ):
            raise FocalExecutionError(
                "focal mode requires release profile, binding, and result paths"
            )
        test_module = focal_nodeid.split("::", 1)[0]
        if perimeter.module_classifications.get(test_module) != "required":
            raise FocalExecutionError(
                "allowlisted B06 is not required by the active perimeter"
            )
        if any(
            value is not None
            for value in (effects_output, scratch_root, collector_output)
        ):
            raise FocalExecutionError(
                "focal mode cannot use full-gate collector or A-PRE options"
            )
    elif any(
        value is not None
        for value in (
            focal_result_output,
            focal_binding_sha256,
            focal_binding_path,
        )
    ):
        raise FocalExecutionError(
            "focal worker metadata requires a focal nodeid"
        )

    active_suites = [
        suite
        for suite in perimeter.suites
        if suite.classification == "required"
        or (
            profile == "release"
            and suite.classification == "qualification-required"
        )
    ]
    suite_paths = [suite.path for suite in active_suites]
    pytest_args = ["-q", "-p", "no:cacheprovider"]
    basetemp = os.environ.get("TALOS_TEST_BASETEMP")
    if basetemp:
        pytest_args.append(f"--basetemp={basetemp}")
    if focal_nodeid is not None:
        suite_paths = ["tests/pedagogy"]
        pytest_args.append(focal_nodeid)
    else:
        selected_paths = [
            (
                f"{suite.path}/"
                if (REPOSITORY_ROOT / suite.path).is_dir()
                else suite.path
            )
            for suite in active_suites
        ]
        pytest_args.extend(selected_paths)
        for module_path in sorted(perimeter.optional_modules):
            pytest_args.extend(["--ignore", module_path])

    results = SuiteResults(
        suite_paths,
        expected_nodeid=focal_nodeid,
        informative_tests=perimeter.informative_tests,
    )
    plugins: list[Any] = [results]
    observer = None
    if (
        collector_output is not None
        and collector_output.resolve().is_relative_to(
            REPOSITORY_ROOT.resolve()
        )
    ):
        raise ValueError("collector output must be outside the repository")
    if effects_output is not None:
        if scratch_root is None:
            raise ValueError(
                "an explicit external scratch root is required for "
                "effects observation"
            )
        if effects_output.resolve().is_relative_to(REPOSITORY_ROOT.resolve()):
            raise ValueError("effects output must be outside the repository")
        from scripts.apre_effects import EffectObserver

        observer = EffectObserver(REPOSITORY_ROOT, scratch_root)
        observer.install()
        plugins.append(observer)

    previous_directory = Path.cwd()
    os.chdir(REPOSITORY_ROOT)
    exit_code = pytest.ExitCode.INTERNAL_ERROR
    try:
        exit_code = pytest.main(pytest_args, plugins=plugins)
    finally:
        os.chdir(previous_directory)
        if observer is not None:
            observer.close()
            observer.write_report(effects_output)
        if collector_output is not None:
            results.write_collector(
                collector_output,
                results.collector_payload(perimeter, profile, int(exit_code)),
            )

    if focal_nodeid is not None:
        try:
            workspace_root = Path(
                os.environ["TALOS_TEST_WORKSPACE_ROOT"]
            )
            validate_focal_execution_binding(
                focal_binding_path,
                expected_sha256=focal_binding_sha256,
                profile=profile,
                repository_root=REPOSITORY_ROOT,
                workspace_root=workspace_root,
            )
        except (
            FocalExecutionError,
            OSError,
            ValueError,
            KeyError,
            TypeError,
        ) as error:
            print(
                "QUALITY GATE BLOCKED: focal execution identity changed "
                f"during worker execution: {error}",
                file=sys.stderr,
            )
            return 2

        focal_payload = results.focal_payload(int(exit_code))
        from study_engine.diagnostics.test_isolation_snapshots import load_focal_scope_profile
        scope_profile, _ = load_focal_scope_profile(REPOSITORY_ROOT)
        if scope_profile.get("b06_synthetic_exception") is not None:
            try:
                focal_payload["b06_synthetic_provenance"] = validate_b06_synthetic_state(
                    workspace_root, focal_nodeid
                )
            except (FocalExecutionError, OSError, ValueError) as error:
                print(f"QUALITY GATE BLOCKED: {error}", file=sys.stderr)
                return 2
        focal_payload["binding_sha256"] = focal_binding_sha256
        focal_passed = (
            focal_payload["exactly_one_selected_test"]
            and focal_payload["test_outcome"] == "passed"
            and exit_code == pytest.ExitCode.OK
        )
        focal_payload["runner_exit_code"] = (
            0 if focal_passed else int(exit_code) or 1
        )
        result_path = Path(focal_result_output)
        if (
            result_path.is_symlink()
            or not result_path.is_absolute()
            or not result_path.is_relative_to(Path("/workspace/run"))
            or result_path.exists()
        ):
            raise FocalExecutionError(
                "focal worker result path is invalid or already exists"
            )
        result_path.write_bytes(_canonical_json(focal_payload) + b"\n")
        print(
            "FOCAL TEST RESULT: "
            f"nodeid={focal_nodeid} "
            f"collected_exactly_one="
            f"{focal_payload['exactly_one_selected_test']} "
            f"outcome={focal_payload['test_outcome']} "
            f"pytest_exit_code={int(exit_code)}"
        )
        return focal_payload["runner_exit_code"]

    print("\n" + "=" * 72)
    print(f"TEST PERIMETER REPORT — PROFILE: {profile.upper()}")
    print("=" * 72)
    for suite in perimeter.suites:
        if suite not in active_suites:
            if suite.classification == "support-only":
                print(f"{suite.path:<28} SUPPORT ONLY: {suite.reason}")
            else:
                print(
                    f"{suite.path:<28} NOT RUN "
                    "(qualification-required; run release profile)"
                )
            continue
        counts = results.counts(suite.path)
        status = results.suite_status(
            suite.path, counts, perimeter.informative_tests
        )
        print(
            f"{suite.path:<28} {status:<18} "
            f"tests={counts['collected']} passed={counts['passed']} "
            f"skipped={counts['skipped']} failed={counts['failed']}"
        )
        if status == "INFORMATIVE_FAIL":
            for nodeid in sorted(
                nodeid
                for nodeid in results.outcomes[suite.path]
                if nodeid in perimeter.informative_tests
                and results.outcomes[suite.path][nodeid]
                == "informative_failed"
            ):
                print(
                    f"  INFORMATIVE FAILURE: {nodeid} — "
                    f"{perimeter.informative_tests[nodeid]}"
                )

    for module_path, reason in sorted(perimeter.optional_modules.items()):
        print(f"{module_path:<52} NOT RUN (optional): {reason}")

    print("=" * 72)
    gate_status, gate_exit_code = results.gate_result(
        perimeter, profile, int(exit_code)
    )
    if gate_status == "PASS_WITH_INFORMATIVE_FAILURES":
        print(
            "RESULT: TEST GATE PASS WITH INFORMATIVE FAILURES — "
            "the failed measurement remains visible and is non-blocking."
        )
        return gate_exit_code
    if gate_status == "PASS":
        print(
            "RESULT: TEST GATE PASS — this is test evidence, not by itself "
            "a release certification."
        )
        return gate_exit_code
    print("RESULT: TEST GATE FAIL — release qualification is not established.")
    return gate_exit_code


def _publish_artifact(source: Path, destination: Path) -> None:
    destination = Path(destination)
    if destination.is_symlink():
        raise ValueError("gate artifact output cannot be a symlink")
    destination = destination.resolve()
    if destination.is_relative_to(REPOSITORY_ROOT.resolve()):
        raise ValueError("gate artifact output must be outside the repository")
    if not source.is_file() or source.is_symlink():
        raise ValueError(f"isolated gate artifact is missing: {source.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=destination.parent,
        prefix=f".{destination.name}.",
        delete=False,
    ) as stream:
        temporary_path = Path(stream.name)
        with source.open("rb") as artifact:
            for block in iter(lambda: artifact.read(1024 * 1024), b""):
                stream.write(block)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        temporary_path.replace(destination)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def _validate_focal_receipt_destination(
    destination: Path, *, snapshot_root: Path
) -> Path:
    destination = Path(destination)
    if destination.is_symlink() or destination.exists():
        raise FocalExecutionError(
            "focal execution receipt destination must be a new path"
        )
    destination = destination.resolve()
    repository_root = REPOSITORY_ROOT.resolve()
    if destination.is_relative_to(repository_root):
        raise FocalExecutionError(
            "focal execution receipt must be outside the repository"
        )
    snapshot_root = Path(snapshot_root).resolve(strict=True)
    if (
        destination == snapshot_root
        or destination.is_relative_to(snapshot_root)
        or snapshot_root.is_relative_to(destination)
    ):
        raise FocalExecutionError(
            "focal execution receipt cannot overlap the sealed snapshot"
        )
    if destination.parent.exists() and not destination.parent.is_dir():
        raise FocalExecutionError(
            "focal execution receipt parent must be a directory"
        )
    return destination


GIT_OBSERVATION_FILE = "git-observation.json"
GUEST_GIT_OBSERVATION_PATH = "/workspace/run/git-observation.json"
GIT_OBSERVATION_ENV = "TALOS_QUALITY_GATE_GIT_OBSERVATION"
_GIT_STATUS_ARGUMENTS = ("status", "--porcelain", "--untracked-files=all")


class GitObservationError(ValueError):
    """Raised when the supervisor-side Git observation cannot be trusted."""


class GitSterilityViolation(GitObservationError):
    """Raised when the checkout changed during the isolated gate run."""


def capture_git_observation(
    repository_root: Path,
    *,
    run_identity: str,
    gate_identity: str,
    run_token: str,
    phase: str,
) -> dict[str, Any]:
    """Observe host checkout status from the supervisor only (STEP-14).

    The sandboxed worker never observes Git state itself: ``.git`` is masked
    by design.  Both the pre and the post observation run in this supervisor
    process, and any failure is fatal to the gate.
    """
    if phase not in ("pre", "post"):
        raise GitObservationError(f"unknown observation phase: {phase!r}")
    status_command = [
        "git",
        "-C",
        str(repository_root),
        *_GIT_STATUS_ARGUMENTS,
    ]
    try:
        status = subprocess.run(
            status_command,
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )
        head = subprocess.run(
            ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise GitObservationError(
            f"cannot observe repository status ({phase}): {error}"
        ) from error
    return {
        "schema_version": 1,
        "phase": phase,
        "run_identity": run_identity,
        "gate_identity": gate_identity,
        "run_token": run_token,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "git_command": status_command,
        "head_commit": head.stdout.strip(),
        "porcelain": status.stdout,
    }


def _git_observation_hmac(record: dict[str, Any], secret: bytes) -> str:
    return hmac.new(secret, _canonical_json(record), hashlib.sha256).hexdigest()


def build_signed_git_observation(
    record: dict[str, Any], secret: bytes
) -> dict[str, Any]:
    return {
        "record": record,
        "hmac_sha256": _git_observation_hmac(record, secret),
    }


def verify_signed_git_observation(
    signed: Any, secret: bytes
) -> dict[str, Any]:
    """Return the record only if its supervisor HMAC is valid."""
    if (
        not isinstance(signed, dict)
        or set(signed) != {"record", "hmac_sha256"}
        or not isinstance(signed.get("record"), dict)
        or not isinstance(signed.get("hmac_sha256"), str)
    ):
        raise GitObservationError("git observation envelope is malformed")
    if not hmac.compare_digest(
        _git_observation_hmac(signed["record"], secret), signed["hmac_sha256"]
    ):
        raise GitObservationError(
            "git observation HMAC does not match: record altered or signed "
            "by another authority"
        )
    return signed["record"]


def verify_git_observation_pair(
    pre: Any, post: Any, *, run_identity: str, gate_identity: str
) -> None:
    """Fail closed unless both observations bracket one identical checkout."""
    for record, phase in ((pre, "pre"), (post, "post")):
        if (
            not isinstance(record, dict)
            or record.get("schema_version") != 1
            or record.get("phase") != phase
            or record.get("run_identity") != run_identity
            or record.get("gate_identity") != gate_identity
            or not isinstance(record.get("porcelain"), str)
            or not isinstance(record.get("head_commit"), str)
            or not record["head_commit"]
            or not isinstance(record.get("captured_at"), str)
            or not record["captured_at"]
        ):
            raise GitObservationError(
                f"git observation is invalid for the {phase} phase of this run"
            )
    try:
        pre_at = datetime.fromisoformat(pre["captured_at"])
        post_at = datetime.fromisoformat(post["captured_at"])
    except ValueError as error:
        raise GitObservationError(
            f"git observation timestamp is invalid: {error}"
        ) from error
    if pre_at > post_at:
        raise GitObservationError("git observation timestamps are inconsistent")
    if pre["porcelain"] != post["porcelain"]:
        raise GitSterilityViolation(
            "repository worktree status changed during the isolated run"
        )
    if pre["head_commit"] != post["head_commit"]:
        raise GitSterilityViolation(
            "repository HEAD changed during the isolated run"
        )


def load_delivered_git_observation(
    path: Path, *, secret: bytes, expected_pre_record: dict[str, Any]
) -> dict[str, Any]:
    """Re-read the observation delivered to the sandbox after the run.

    A worker that deleted or replaced the delivered file cannot pass this
    check: the supervisor secret never enters the sandbox.
    """
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise GitObservationError(
            f"delivered git observation is unreadable: {error}"
        ) from error
    try:
        signed = json.loads(raw)
    except ValueError as error:
        raise GitObservationError(
            f"delivered git observation is not valid JSON: {error}"
        ) from error
    record = verify_signed_git_observation(signed, secret)
    if _canonical_json(record) != _canonical_json(expected_pre_record):
        raise GitObservationError(
            "delivered git observation differs from the authoritative "
            "pre-run capture"
        )
    return record


def run_isolated_gate(
    profile: str,
    *,
    effects_output: Path | None = None,
    scratch_root: Path | None = None,
    collector_output: Path | None = None,
    focal_nodeid: str | None = None,
    execution_receipt_output: Path | None = None,
) -> int:
    """Prepare test inputs on the host and run pytest inside bubblewrap."""
    from scripts.quality_gate_isolation import (
        IsolationError,
        PROTECTED_DIRECTORIES,
        run_isolated_process,
        workspace_guest_path,
    )
    from study_engine.diagnostics.test_isolation_snapshots import (
        TestSnapshotError,
        _repository_identity,
        derive_test_workspace,
        validate_snapshot,
        verify_sealed_snapshot,
    )

    if focal_nodeid is not None:
        try:
            _validate_focal_nodeid(focal_nodeid)
        except FocalExecutionError as error:
            print(f"QUALITY GATE BLOCKED: {error}", file=sys.stderr)
            return 2
        if profile != "release":
            print(
                "QUALITY GATE BLOCKED: focal B06 requires profile=release",
                file=sys.stderr,
            )
            return 2
        if execution_receipt_output is None:
            print(
                "QUALITY GATE BLOCKED: focal B06 requires an execution "
                "receipt destination",
                file=sys.stderr,
            )
            return 2
        if any(
            value is not None
            for value in (effects_output, scratch_root, collector_output)
        ):
            print(
                "QUALITY GATE BLOCKED: focal B06 does not accept full-gate "
                "collector or A-PRE options",
                file=sys.stderr,
            )
            return 2
    elif execution_receipt_output is not None:
        print(
            "QUALITY GATE BLOCKED: execution receipt destination requires "
            "focal mode",
            file=sys.stderr,
        )
        return 2

    snapshot_environment = {
        "TALOS_TEST_SNAPSHOT_ROOT": os.environ.get(
            "TALOS_TEST_SNAPSHOT_ROOT"
        ),
        "TALOS_TEST_SNAPSHOT_MANIFEST_SHA256": os.environ.get(
            "TALOS_TEST_SNAPSHOT_MANIFEST_SHA256"
        ),
        "TALOS_TEST_SNAPSHOT_SCOPE": os.environ.get(
            "TALOS_TEST_SNAPSHOT_SCOPE"
        ),
        "TALOS_TEST_RUN_ID": os.environ.get("TALOS_TEST_RUN_ID"),
        "TALOS_TEST_GATE_ID": os.environ.get("TALOS_TEST_GATE_ID"),
        "TALOS_TEST_POLICY_ID": os.environ.get("TALOS_TEST_POLICY_ID"),
    }
    missing = [
        name for name, value in snapshot_environment.items() if not value
    ]
    if missing:
        print(
            "QUALITY GATE BLOCKED: sealed snapshot provenance is incomplete; "
            "missing " + ", ".join(missing),
            file=sys.stderr,
        )
        return 2

    snapshot_root = Path(snapshot_environment["TALOS_TEST_SNAPSHOT_ROOT"])
    if snapshot_root.is_symlink():
        print(
            "QUALITY GATE BLOCKED: snapshot root cannot be a symlink",
            file=sys.stderr,
        )
        return 2
    try:
        snapshot_root = snapshot_root.resolve(strict=True)
    except OSError as error:
        print(
            f"QUALITY GATE BLOCKED: snapshot root is unavailable: {error}",
            file=sys.stderr,
        )
        return 2
    repository_root = REPOSITORY_ROOT.resolve()
    if (
        snapshot_root.is_relative_to(repository_root)
        or repository_root.is_relative_to(snapshot_root)
    ):
        print(
            "QUALITY GATE BLOCKED: sealed snapshot must be external to the "
            "repository",
            file=sys.stderr,
        )
        return 2
    manifest_digest = snapshot_environment[
        "TALOS_TEST_SNAPSHOT_MANIFEST_SHA256"
    ]
    scope = snapshot_environment["TALOS_TEST_SNAPSHOT_SCOPE"]
    run_identity = snapshot_environment["TALOS_TEST_RUN_ID"]
    gate_identity = snapshot_environment["TALOS_TEST_GATE_ID"]
    policy_identity = snapshot_environment["TALOS_TEST_POLICY_ID"]
    assert all(
        isinstance(value, str)
        for value in (
            manifest_digest,
            scope,
            run_identity,
            gate_identity,
            policy_identity,
        )
    )

    receipt_destination = None
    if focal_nodeid is not None:
        if not _RUN_ID_PATTERN.fullmatch(run_identity):
            print(
                "QUALITY GATE BLOCKED: focal run ID must be a canonical "
                "UUIDv4",
                file=sys.stderr,
            )
            return 2
        try:
            assert execution_receipt_output is not None
            receipt_destination = _validate_focal_receipt_destination(
                execution_receipt_output,
                snapshot_root=snapshot_root,
            )
        except (FocalExecutionError, OSError) as error:
            print(
                "QUALITY GATE BLOCKED: invalid focal receipt destination: "
                f"{error}",
                file=sys.stderr,
            )
            return 2

    run_token = str(uuid4())
    sandbox_workspace_identity = "/workspace/run/test-data"
    try:
        host_namespaces = {
            name: os.readlink(f"/proc/self/ns/{name}")
            for name in ("mnt", "net", "pid")
        }
    except OSError as error:
        print(
            f"QUALITY GATE BLOCKED: cannot identify host namespaces: {error}",
            file=sys.stderr,
        )
        return 2
    execution_outputs: dict[Path, Path] = {}
    additional_mounts: list[tuple[Path, str]] = []

    if scratch_root is not None:
        scratch_root = Path(scratch_root)
        if scratch_root.is_symlink() or not scratch_root.is_dir():
            print(
                "QUALITY GATE BLOCKED: A-PRE scratch root must be an existing "
                "non-symlink directory",
                file=sys.stderr,
            )
            return 2
        scratch_root = scratch_root.resolve()
        if scratch_root.is_relative_to(REPOSITORY_ROOT.resolve()):
            print(
                "QUALITY GATE BLOCKED: A-PRE scratch root cannot be inside "
                "the repository",
                file=sys.stderr,
            )
            return 2
        if (
            not scratch_root.is_relative_to(Path("/tmp"))
            or scratch_root.parent != Path("/tmp")
        ):
            print(
                "QUALITY GATE BLOCKED: A-PRE scratch root must be a dedicated "
                "direct child of /tmp",
                file=sys.stderr,
            )
            return 2
        if (
            scratch_root == snapshot_root
            or scratch_root.is_relative_to(snapshot_root)
            or snapshot_root.is_relative_to(scratch_root)
        ):
            print(
                "QUALITY GATE BLOCKED: A-PRE scratch root cannot overlap the "
                "sealed snapshot",
                file=sys.stderr,
            )
            return 2
        if any(scratch_root.iterdir()):
            print(
                "QUALITY GATE BLOCKED: A-PRE scratch root must be empty "
                "before "
                "the run",
                file=sys.stderr,
            )
            return 2
        for relative in PROTECTED_DIRECTORIES:
            protected = (REPOSITORY_ROOT / relative).resolve()
            if scratch_root == protected or scratch_root.is_relative_to(
                protected
            ):
                print(
                    "QUALITY GATE BLOCKED: A-PRE scratch root overlaps a "
                    f"protected path: {relative}",
                    file=sys.stderr,
                )
                return 2
        additional_mounts.append((scratch_root, "/workspace/run/scratch"))

    requested_outputs = [
        path.resolve()
        for path in (
            effects_output,
            collector_output,
            receipt_destination,
        )
        if path is not None
    ]
    if len(set(requested_outputs)) != len(requested_outputs):
        print(
            "QUALITY GATE BLOCKED: effects and collector outputs must be "
            "different files",
            file=sys.stderr,
        )
        return 2
    if any(
        path.is_relative_to(REPOSITORY_ROOT.resolve())
        for path in requested_outputs
    ):
        print(
            "QUALITY GATE BLOCKED: gate artifact outputs must be outside the "
            "repository",
            file=sys.stderr,
        )
        return 2

    try:
        with tempfile.TemporaryDirectory(
            prefix="talos-quality-gate-", dir="/tmp"
        ) as temporary_root_value:
            temporary_root = Path(temporary_root_value)
            execution_root = temporary_root / "execution"
            execution_root.mkdir()
            (execution_root / "home").mkdir()
            (execution_root / "pytest-tmp").mkdir()
            if scratch_root is None and effects_output is not None:
                (execution_root / "scratch").mkdir()

            repository_commit = _repository_identity(REPOSITORY_ROOT)
            test_workspace = execution_root / "test-data"
            snapshot_validation = validate_snapshot(
                snapshot_root,
                expected_manifest_sha256=manifest_digest,
                scope=scope,
                run_identity=run_identity,
                gate_identity=gate_identity,
                policy_identity=policy_identity,
                repository_root=REPOSITORY_ROOT,
            )
            if (
                snapshot_validation.status != "VALID"
                or snapshot_validation.manifest is None
            ):
                raise TestSnapshotError(
                    "Snapshot is INVALID: "
                    f"{snapshot_validation.reason}"
                )
            derive_test_workspace(
                snapshot_root,
                test_workspace,
                expected_manifest_sha256=manifest_digest,
                scope=scope,
                run_identity=run_identity,
                gate_identity=gate_identity,
                policy_identity=policy_identity,
                workspace_identity=sandbox_workspace_identity,
            )
            verify_sealed_snapshot(snapshot_root, manifest_digest)

            focal_binding = None
            focal_binding_sha256 = None
            if focal_nodeid is not None:
                focal_binding, focal_binding_sha256 = (
                    build_focal_execution_binding(
                        manifest=snapshot_validation.manifest,
                        manifest_sha256=manifest_digest,
                        run_id=run_identity,
                        profile=profile,
                        repository_root=REPOSITORY_ROOT,
                        perimeter_path=PERIMETER_PATH,
                    )
                )
                (execution_root / "focal-binding.json").write_bytes(
                    _canonical_json(focal_binding) + b"\n"
                )

            worker_arguments = [
                "/workspace/repository/scripts/quality_gate.py",
                "--_sandbox-worker",
                "--profile",
                profile,
            ]
            if focal_binding is not None:
                worker_arguments.extend(
                    [
                        "--_focal-nodeid",
                        focal_nodeid,
                        "--_focal-binding-path",
                        "/workspace/run/focal-binding.json",
                        "--_focal-result-path",
                        "/workspace/run/focal-result.json",
                    ]
                )
            if effects_output is not None:
                effects_path = execution_root / "effects.json"
                worker_arguments.extend(
                    [
                        "--apre-effects-output",
                        "/workspace/run/effects.json",
                        "--apre-scratch-root",
                        "/workspace/run/scratch",
                    ]
                )
                execution_outputs[effects_path] = effects_output
            if collector_output is not None:
                collector_path = execution_root / "collector.json"
                worker_arguments.extend(
                    [
                        "--apre-collector-output",
                        "/workspace/run/collector.json",
                    ]
                )
                execution_outputs[collector_path] = collector_output

            pytest_tmp_root = execution_root / "pytest-tmp"
            pytest_guest_tmp_root = workspace_guest_path(
                execution_root, pytest_tmp_root
            )
            child_environment = {
                "TALOS_TEST_ISOLATED": "1",
                "TALOS_TEST_WORKSPACE_ROOT": sandbox_workspace_identity,
                "TALOS_TEST_WORKSPACE_IDENTITY": sandbox_workspace_identity,
                "TALOS_TEST_BASETEMP": str(pytest_guest_tmp_root),
                "TALOS_TEST_RUN_ID": run_identity,
                "TALOS_TEST_GATE_ID": gate_identity,
                "TALOS_TEST_POLICY_ID": policy_identity,
                "TALOS_TEST_REPOSITORY_COMMIT": repository_commit,
                "TALOS_QUALITY_GATE_START_TOKEN": run_token,
                "TALOS_QUALITY_GATE_HOST_MNT_NS": host_namespaces["mnt"],
                "TALOS_QUALITY_GATE_HOST_NET_NS": host_namespaces["net"],
                "TALOS_QUALITY_GATE_HOST_PID_NS": host_namespaces["pid"],
            }
            if focal_binding_sha256 is not None:
                child_environment[
                    "TALOS_TEST_EXECUTION_BINDING_SHA256"
                ] = focal_binding_sha256
            if scratch_root is not None:
                (execution_root / "scratch").mkdir()
            # STEP-14: the supervisor owns the Git sterility observation.
            git_observation_secret = secrets.token_bytes(32)
            try:
                pre_git_observation = capture_git_observation(
                    REPOSITORY_ROOT,
                    run_identity=run_identity,
                    gate_identity=gate_identity,
                    run_token=run_token,
                    phase="pre",
                )
            except GitObservationError as error:
                print(
                    "QUALITY GATE BLOCKED: git sterility observation failed: "
                    f"{error}",
                    file=sys.stderr,
                )
                return 2
            (execution_root / GIT_OBSERVATION_FILE).write_bytes(
                _canonical_json(
                    build_signed_git_observation(
                        pre_git_observation, git_observation_secret
                    )
                )
                + b"\n"
            )
            child_environment[GIT_OBSERVATION_ENV] = GUEST_GIT_OBSERVATION_PATH
            completed = run_isolated_process(
                REPOSITORY_ROOT,
                execution_root,
                [sys.executable, *worker_arguments],
                environment=child_environment,
                additional_writable_mounts=additional_mounts,
                python_executable=sys.executable,
            )

            try:
                load_delivered_git_observation(
                    execution_root / GIT_OBSERVATION_FILE,
                    secret=git_observation_secret,
                    expected_pre_record=pre_git_observation,
                )
                post_git_observation = capture_git_observation(
                    REPOSITORY_ROOT,
                    run_identity=run_identity,
                    gate_identity=gate_identity,
                    run_token=run_token,
                    phase="post",
                )
                verify_git_observation_pair(
                    pre_git_observation,
                    post_git_observation,
                    run_identity=run_identity,
                    gate_identity=gate_identity,
                )
            except GitSterilityViolation as error:
                print(
                    "QUALITY GATE FAILED: git sterility violated during the "
                    f"isolated run: {error}",
                    file=sys.stderr,
                )
                return 1
            except GitObservationError as error:
                print(
                    "QUALITY GATE BLOCKED: git sterility observation failed: "
                    f"{error}",
                    file=sys.stderr,
                )
                return 2

            if completed.stdout:
                print(completed.stdout, end="")
            if completed.stderr:
                print(completed.stderr, end="", file=sys.stderr)

            marker = execution_root / ".quality-gate-worker-started"
            if marker.is_symlink() or not marker.is_file():
                print(
                    "QUALITY GATE BLOCKED: isolated worker did not produce "
                    "a regular startup evidence file",
                    file=sys.stderr,
                )
                return 2
            try:
                marker_record = json.loads(marker.read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                print(
                    "QUALITY GATE BLOCKED: isolated worker did not produce "
                    f"valid startup evidence: {error}",
                    file=sys.stderr,
                )
                return 2
            if (
                marker.is_symlink()
                or not isinstance(marker_record, dict)
                or marker_record.get("token") != run_token
                or not isinstance(marker_record.get("pid"), int)
                or isinstance(marker_record.get("pid"), bool)
                or marker_record.get("pid") == os.getpid()
                or any(
                    not isinstance(
                        marker_record.get(f"{namespace}_namespace"), str
                    )
                    or marker_record.get(f"{namespace}_namespace")
                    == host_namespaces[namespace]
                    for namespace in ("mnt", "net", "pid")
                )
            ):
                print(
                    "QUALITY GATE BLOCKED: isolated worker did not prove "
                    "separate process, mount, network, and PID namespaces",
                    file=sys.stderr,
                )
                return 2

            verify_sealed_snapshot(snapshot_root, manifest_digest)
            if focal_binding is not None:
                focal_result_path = execution_root / "focal-result.json"
                if (
                    focal_result_path.is_symlink()
                    or not focal_result_path.is_file()
                ):
                    print(
                        "QUALITY GATE BLOCKED: focal worker result is "
                        "missing or invalid",
                        file=sys.stderr,
                    )
                    return 2
                try:
                    focal_result = json.loads(
                        focal_result_path.read_text(encoding="utf-8")
                    )
                except (OSError, ValueError) as error:
                    print(
                        "QUALITY GATE BLOCKED: focal worker result is "
                        f"invalid: {error}",
                        file=sys.stderr,
                    )
                    return 2
                expected_result = {
                    "schema_version": 1,
                    "profile": "release",
                    "expected_nodeid": FOCAL_B06_NODEID,
                    "collected_nodeids": [FOCAL_B06_NODEID],
                    "exactly_one_selected_test": True,
                    "binding_sha256": focal_binding_sha256,
                    "runner_exit_code": completed.returncode,
                }
                if not isinstance(focal_result, dict) or any(
                    focal_result.get(key) != value
                    for key, value in expected_result.items()
                ):
                    print(
                        "QUALITY GATE BLOCKED: focal worker result does not "
                        "match the requested execution contract",
                        file=sys.stderr,
                    )
                    return 2
                worker_outcome = focal_result.get("test_outcome")
                worker_pytest_exit = focal_result.get("pytest_exit_code")
                if (
                    worker_outcome
                    not in ("passed", "failed", "skipped", None)
                    or not isinstance(worker_pytest_exit, int)
                    or isinstance(worker_pytest_exit, bool)
                    or (
                        completed.returncode == 0
                        and (
                            worker_outcome != "passed"
                            or worker_pytest_exit != 0
                        )
                    )
                ):
                    print(
                        "QUALITY GATE BLOCKED: focal worker result has an "
                        "inconsistent test outcome",
                        file=sys.stderr,
                    )
                    return 2
                final_receipt = {
                    "schema_version": 2,
                    "execution_mode": "focal_test",
                    "execution_status": (
                        "PASS"
                        if completed.returncode == 0
                        and focal_result.get("test_outcome") == "passed"
                        else "FAIL"
                    ),
                    "binding_sha256": focal_binding_sha256,
                    "run_id": focal_binding["run_id"],
                    "nodeid": focal_binding["nodeid"],
                    "exactly_one": focal_result[
                        "exactly_one_selected_test"
                    ],
                    "snapshot_manifest_sha256": focal_binding[
                        "snapshot_manifest_sha256"
                    ],
                    "scope_profile_id": focal_binding["scope_profile_id"],
                    "scope_profile_sha256": focal_binding[
                        "scope_profile_sha256"
                    ],
                    "effective_execution_manifest_sha256": (
                        focal_binding[
                            "effective_execution_manifest_sha256"
                        ]
                    ),
                    "effective_execution_manifest_reference": (
                        focal_binding[
                            "effective_execution_manifest_reference"
                        ]
                    ),
                    "runtime_identity": focal_binding["runtime_identity"],
                    "binding": focal_binding,
                    "result": focal_result,
                    "isolation": {
                        "mechanism": "bubblewrap",
                        "worker_pid": marker_record["pid"],
                        "mount_namespace": marker_record["mnt_namespace"],
                        "network_namespace": marker_record["net_namespace"],
                        "pid_namespace": marker_record["pid_namespace"],
                    },
                }
                focal_receipt_path = execution_root / "focal-receipt.json"
                focal_receipt_path.write_bytes(
                    json.dumps(
                        final_receipt,
                        ensure_ascii=True,
                        indent=2,
                        sort_keys=True,
                    ).encode("utf-8")
                    + b"\n"
                )
                if receipt_destination is None:
                    raise FocalExecutionError(
                        "focal receipt destination was not validated"
                    )
                _publish_artifact(
                    focal_receipt_path,
                    receipt_destination,
                )
            for source, destination in execution_outputs.items():
                _publish_artifact(source, destination)
            if completed.returncode >= 0:
                return completed.returncode
            return 128 - completed.returncode
    except (IsolationError, TestSnapshotError, OSError, ValueError) as error:
        print(
            "QUALITY GATE BLOCKED: isolation or snapshot precondition failed: "
            f"{error}",
            file=sys.stderr,
        )
        return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--_sandbox-worker",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--focal-nodeid",
        help="run only the allowlisted B06 nodeid inside the isolated gate",
    )
    parser.add_argument(
        "--execution-receipt",
        type=Path,
        help="write the focal execution receipt outside the repository",
    )
    parser.add_argument(
        "--_focal-nodeid",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--_focal-binding-path",
        type=Path,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--_focal-result-path",
        type=Path,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--profile",
        choices=("required", "release"),
        default="required",
        help=(
            "required runs deterministic suites; release also runs "
            "controlled qualification suites"
        ),
    )
    parser.add_argument(
        "--apre-effects-output",
        type=Path,
        help=(
            "write Python audit-hook events to an external JSON artifact; "
            "this is not complete syscall or sterility proof"
        ),
    )
    parser.add_argument(
        "--apre-scratch-root",
        type=Path,
        help="existing writable temporary directory outside the repository",
    )
    parser.add_argument(
        "--apre-collector-output",
        type=Path,
        help="write collected per-suite results to an external JSON artifact",
    )
    args = parser.parse_args(argv)
    focal_worker_arguments = (
        args._focal_nodeid,
        args._focal_binding_path,
        args._focal_result_path,
    )
    if args._sandbox_worker:
        if args.focal_nodeid is not None or args.execution_receipt is not None:
            parser.error("sandbox worker cannot receive host focal options")
        if any(value is None for value in focal_worker_arguments) and any(
            value is not None for value in focal_worker_arguments
        ):
            parser.error("incomplete isolated focal worker contract")
        if args._focal_nodeid is not None and (
            args._focal_binding_path
            != Path("/workspace/run/focal-binding.json")
            or args._focal_result_path
            != Path("/workspace/run/focal-result.json")
        ):
            parser.error("isolated focal worker paths are not canonical")
    elif any(value is not None for value in focal_worker_arguments):
        parser.error("internal focal worker options require --_sandbox-worker")
    elif (args.focal_nodeid is None) != (args.execution_receipt is None):
        parser.error(
            "--focal-nodeid and --execution-receipt must be used together"
        )
    if args.focal_nodeid is not None:
        try:
            _validate_focal_nodeid(args.focal_nodeid)
        except FocalExecutionError as error:
            parser.error(str(error))
        if args.profile != "release":
            parser.error("focal B06 requires --profile release")

    if args._sandbox_worker:
        if (
            os.environ.get("TALOS_TEST_ISOLATED") != "1"
            or not os.environ.get("TALOS_TEST_WORKSPACE_ROOT")
            or not os.environ.get("TALOS_TEST_WORKSPACE_IDENTITY")
            or str(REPOSITORY_ROOT) != "/workspace/repository"
        ):
            print(
                "QUALITY GATE BLOCKED: sandbox worker requires the isolated "
                "workspace contract and mounted repository path",
                file=sys.stderr,
            )
            return 2
        expected_namespaces = {
            "mnt": os.environ.get("TALOS_QUALITY_GATE_HOST_MNT_NS"),
            "net": os.environ.get("TALOS_QUALITY_GATE_HOST_NET_NS"),
            "pid": os.environ.get("TALOS_QUALITY_GATE_HOST_PID_NS"),
        }
        current_namespaces = {
            name: os.readlink(f"/proc/self/ns/{name}")
            for name in expected_namespaces
        }
        if any(
            not expected_namespaces[name]
            or expected_namespaces[name] == current_namespaces[name]
            for name in expected_namespaces
        ):
            print(
                "QUALITY GATE BLOCKED: required mount, network, and PID "
                "namespaces are not isolated",
                file=sys.stderr,
            )
            return 2
        start_token = os.environ.get("TALOS_QUALITY_GATE_START_TOKEN")
        marker = Path("/workspace/run/.quality-gate-worker-started")
        if not start_token or marker.exists() or marker.is_symlink():
            print(
                "QUALITY GATE BLOCKED: sandbox worker startup token is "
                "missing or duplicated",
                file=sys.stderr,
            )
            return 2
        marker.write_text(
            json.dumps(
                {
                    "token": start_token,
                    "pid": os.getpid(),
                    "mnt_namespace": os.readlink("/proc/self/ns/mnt"),
                    "net_namespace": os.readlink("/proc/self/ns/net"),
                    "pid_namespace": os.readlink("/proc/self/ns/pid"),
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        if args._focal_nodeid is not None:
            expected_binding_digest = os.environ.get(
                "TALOS_TEST_EXECUTION_BINDING_SHA256"
            )
            try:
                if not expected_binding_digest:
                    raise FocalExecutionError(
                        "worker execution binding digest is missing"
                    )
                validate_focal_execution_binding(
                    args._focal_binding_path,
                    expected_sha256=expected_binding_digest,
                    profile=args.profile,
                    repository_root=REPOSITORY_ROOT,
                    workspace_root=Path(
                        os.environ["TALOS_TEST_WORKSPACE_ROOT"]
                    ),
                )
            except (OSError, ValueError, KeyError, TypeError) as error:
                print(
                    f"QUALITY GATE BLOCKED: invalid focal worker contract: "
                    f"{error}",
                    file=sys.stderr,
                )
                return 2
    elif any(value is not None for value in focal_worker_arguments):
        parser.error("internal focal worker options require --_sandbox-worker")
    environment_options = {
        "apre_effects_output": "TALOS_APRE_EFFECTS_OUTPUT",
        "apre_scratch_root": "TALOS_APRE_SCRATCH_ROOT",
        "apre_collector_output": "TALOS_APRE_COLLECTOR_OUTPUT",
    }
    for argument, variable in environment_options.items():
        environment_value = os.environ.get(variable)
        if environment_value is None:
            continue
        if not environment_value.strip():
            parser.error(f"{variable} must not be empty")
        environment_path = Path(environment_value)
        argument_path = getattr(args, argument)
        if argument_path is not None and argument_path.resolve() != (
            environment_path.resolve()
        ):
            parser.error(
                f"--{argument.replace('_', '-')} conflicts with {variable}"
            )
        setattr(args, argument, argument_path or environment_path)

    if (args.apre_effects_output is None) != (args.apre_scratch_root is None):
        parser.error(
            "--apre-effects-output and --apre-scratch-root must be "
            "used together"
        )
    if args.apre_collector_output is not None and (
        args.apre_effects_output is None
    ):
        parser.error("--apre-collector-output requires effects observation")
    if args.apre_effects_output is not None and args.profile != "release":
        parser.error(
            "A-PRE observation is defined only for the release profile"
        )

    sys.path[:0] = [
        str(REPOSITORY_ROOT),
        str(REPOSITORY_ROOT / "src"),
    ]
    try:
        perimeter = validate_perimeter(REPOSITORY_ROOT, PERIMETER_PATH)
    except PerimeterError as error:
        print(f"TEST PERIMETER ERROR: {error}", file=sys.stderr)
        return 2

    from study_engine.contracts.trust_root import verify_manifest_trust_root

    try:
        verify_manifest_trust_root(TESTS_ROOT / "protected" / "manifest.json")
    except Exception as error:
        print(
            "CRITICAL SECURITY BREACH: trust root verification failed: "
            f"{error}",
            file=sys.stderr,
        )
        return 1

    module_count = sum(len(suite.modules) for suite in perimeter.suites)
    print(
        f"Validated {module_count} test_*.py files across "
        f"{len(perimeter.suites)} suites, including "
        "support-only helpers."
    )
    print("Protected manifest trust root: OK.")
    if args._sandbox_worker:
        return run_gate(
            args.profile,
            perimeter,
            effects_output=args.apre_effects_output,
            scratch_root=args.apre_scratch_root,
            collector_output=args.apre_collector_output,
            focal_nodeid=args._focal_nodeid,
            focal_result_output=args._focal_result_path,
            focal_binding_sha256=os.environ.get(
                "TALOS_TEST_EXECUTION_BINDING_SHA256"
            )
            if args._focal_nodeid is not None
            else None,
            focal_binding_path=args._focal_binding_path,
        )
    return run_isolated_gate(
        args.profile,
        effects_output=args.apre_effects_output,
        scratch_root=args.apre_scratch_root,
        collector_output=args.apre_collector_output,
        focal_nodeid=args.focal_nodeid,
        execution_receipt_output=args.execution_receipt,
    )


if __name__ == "__main__":
    sys.exit(main())
