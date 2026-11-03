import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest

import scripts.quality_gate as quality_gate
from study_engine.diagnostics import test_isolation_snapshots
from scripts.quality_gate_isolation import run_isolated_process


NODEID = quality_gate.FOCAL_B06_NODEID


def _sha256(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _make_binding_inputs(tmp_path: Path):
    repository = tmp_path / "repository"
    repository.mkdir(parents=True)
    for relative in test_isolation_snapshots._GATE_FILES:
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"synthetic gate input: {relative}\n", encoding="utf-8"
        )
    test_file = repository / NODEID.split("::", 1)[0]
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(
        f"def {NODEID.split('::', 1)[1]}(web_state_test_copy):\n"
        "    AppContainer(working_dir=web_state_test_copy, use_mock=True)\n",
        encoding="utf-8",
    )
    (repository / "tests" / "conftest.py").write_text(
        "def web_state_test_copy(_test_isolated_workspace):\n"
        "    return database_files_for_workspace(\n"
        "        _test_isolated_workspace,\n"
        "        {\n"
        "            'knowledge_store': 'knowledge_store.db',\n"
        "            'vector_store': 'vector_store.db',\n"
        "            'student_state': 'student_state.db',\n"
        "        },\n"
        "    )\n",
        encoding="utf-8",
    )
    perimeter = repository / "config" / "test_perimeter.json"
    (repository / "src").mkdir(exist_ok=True)
    (repository / "src" / "runtime.py").write_text(
        "SYNTHETIC = True\n", encoding="utf-8"
    )
    (repository / "data").mkdir()
    (repository / "data" / "runtime.json").write_text(
        '{"fixture":"synthetic"}\n', encoding="utf-8"
    )
    scope_profile = {
        "profile_version": 1,
        "scope": "talos.b06.snapshot.v1",
        "nodeid": NODEID,
        "required_logical_inputs": {
            "knowledge_store": "knowledge_store.db",
            "vector_store": "vector_store.db",
            "student_state": "student_state.db",
        },
        "required_snapshot_payload": {
            "sidecar_suffixes": ["-wal", "-shm", "-journal"],
            "sidecar_policy": (
                "record_absent_or_present_for_each_database"
            ),
        },
        "external_execution_resources": ["data/runtime.json"],
        "effective_execution_paths": [
            "config",
            "data/runtime.json",
            "scripts/quality_gate.py",
            "src",
            "tests/conftest.py",
            NODEID.split("::", 1)[0],
        ],
        "excluded_path_components": [
            ".git",
            ".pytest_cache",
            "__pycache__",
        ],
        "fixture_constraints": {
            "fixture": "web_state_test_copy",
            "working_directory": "derived_snapshot_only",
            "use_mock": True,
            "database_identities": [
                "knowledge_store",
                "vector_store",
                "student_state",
            ],
        },
    }
    perimeter.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "focal_execution_profiles": {
                    "b06-snapshot-v1": scope_profile
                },
            }
        ),
        encoding="utf-8",
    )
    _, scope_profile_sha256 = (
        test_isolation_snapshots.load_focal_scope_profile(repository)
    )
    run_id = str(uuid4())
    manifest = {
        "snapshot_id": "snapshot-test-001",
        "source_identity": "synthetic-source-set",
        "source_fingerprint": _sha256(b"source"),
        "scope": scope_profile["scope"],
        "scope_profile_id": "b06-snapshot-v1",
        "scope_profile_version": scope_profile["profile_version"],
        "scope_profile_sha256": scope_profile_sha256,
        "databases": scope_profile["required_logical_inputs"],
        "destination_identity": str(tmp_path / "sealed-snapshot"),
        "run_identity": run_id,
        "gate_identity": "caller-gate-label",
        "policy_identity": "caller-policy-label",
        "gate_fingerprint": test_isolation_snapshots._gate_fingerprint(
            repository
        ),
        "git_tree_or_commit": "b" * 40,
        "capture_id": "synthetic-capture-001",
        "capture_attestation_sha256": _sha256(b"attestation"),
    }
    binding, binding_sha256 = quality_gate.build_focal_execution_binding(
        manifest=manifest,
        manifest_sha256=_sha256(b"manifest"),
        run_id=run_id,
        profile="release",
        repository_root=repository,
        perimeter_path=perimeter,
        worker_workspace_identity=str((tmp_path / "workspace").resolve()),
    )
    return (
        repository,
        perimeter,
        test_file,
        run_id,
        manifest,
        binding,
        binding_sha256,
    )


def _write_workspace_receipt(
    root: Path,
    binding: dict,
    *,
    manifest_sha256: str | None = None,
    scope: str | None = None,
    run_id: str | None = None,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    workspace_identity = str(root.resolve())
    (root / ".talos-test-workspace.json").write_text(
        json.dumps(
            {
                "manifest_sha256": (
                    manifest_sha256 or binding["manifest_sha256"]
                ),
                "snapshot_id": binding["snapshot_id"],
                "scope": scope or binding["scope"],
                "workspace_identity": workspace_identity,
                "run_identity": run_id or binding["run_id"],
                "gate_identity": binding["gate_identity_operational_label"],
                "policy_identity": binding[
                    "policy_identity_operational_label"
                ],
                "scope_profile_id": binding["scope_profile_id"],
                "scope_profile_sha256": binding[
                    "scope_profile_sha256"
                ],
            }
        ),
        encoding="utf-8",
    )


def _worker_environment(binding: dict, workspace: Path) -> dict[str, str]:
    return {
        "TALOS_TEST_RUN_ID": binding["run_id"],
        "TALOS_TEST_GATE_ID": binding["gate_identity_operational_label"],
        "TALOS_TEST_POLICY_ID": binding[
            "policy_identity_operational_label"
        ],
        "TALOS_TEST_REPOSITORY_COMMIT": binding["git_commit"],
        "TALOS_TEST_WORKSPACE_ROOT": str(workspace.resolve()),
        "TALOS_TEST_WORKSPACE_IDENTITY": str(workspace.resolve()),
    }


@pytest.mark.parametrize(
    "nodeid",
    [
        "",
        "tests/pedagogy/test_talos_vs_notebooklm_e2e.py::test_other",
        NODEID + "::test_duplicate",
    ],
)
def test_focal_selector_rejects_empty_wrong_and_multiple_nodeids(
    nodeid: str,
) -> None:
    with pytest.raises(quality_gate.FocalExecutionError, match="exact B06"):
        quality_gate._validate_focal_nodeid(nodeid)


def test_focal_binding_records_current_test_and_operational_labels(
    tmp_path: Path,
) -> None:
    _, _, _, run_id, _, binding, binding_sha256 = _make_binding_inputs(
        tmp_path
    )

    assert binding["run_id"] == run_id
    assert binding["nodeid"] == NODEID
    assert binding["test_file_sha256"].startswith("sha256:")
    assert binding["perimeter_sha256"].startswith("sha256:")
    assert binding["profile"] == "release"
    assert binding["execution_mode"] == "focal_test"
    assert binding["scope_profile_id"] == "b06-snapshot-v1"
    assert binding["effective_execution_manifest_sha256"].startswith(
        "sha256:"
    )
    assert binding["effective_execution_manifest"]["entries"]
    assert (
        binding["effective_execution_manifest"]["manifest_schema_version"]
        == 1
    )
    assert binding["runtime_identity"]["pytest_version"] == pytest.__version__
    assert "not normative" in binding["identity_semantics"]["policy_identity"]
    assert binding_sha256 == (
        "sha256:"
        f"{hashlib.sha256(quality_gate._canonical_json(binding)).hexdigest()}"
    )


def test_effective_execution_manifest_tracks_dirty_and_untracked_files(
    tmp_path: Path,
) -> None:
    repository, _, _, _, _, _, _ = _make_binding_inputs(tmp_path)
    source = repository / "src" / "runtime.py"
    initial, initial_digest = (
        test_isolation_snapshots.build_effective_execution_manifest(
            repository
        )
    )

    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "add", "src/runtime.py"],
        check=True,
    )
    source.write_text("STAGED_CONTENT = True\n", encoding="utf-8")
    unstaged, unstaged_digest = (
        test_isolation_snapshots.build_effective_execution_manifest(
            repository
        )
    )
    assert unstaged_digest != initial_digest
    assert next(
        entry
        for entry in unstaged["entries"]
        if entry["path"] == "src/runtime.py"
    )["sha256"] == _sha256(source.read_bytes())

    subprocess.run(
        ["git", "-C", str(repository), "add", "src/runtime.py"],
        check=True,
    )
    staged, staged_digest = (
        test_isolation_snapshots.build_effective_execution_manifest(
            repository
        )
    )
    assert staged_digest == unstaged_digest
    assert staged == unstaged

    untracked = repository / "src" / "untracked_runtime.py"
    untracked.write_text("UNTRACKED = True\n", encoding="utf-8")
    _, untracked_digest = (
        test_isolation_snapshots.build_effective_execution_manifest(
            repository
        )
    )
    assert untracked_digest != staged_digest
    untracked.unlink()
    source.unlink()
    _, deleted_digest = (
        test_isolation_snapshots.build_effective_execution_manifest(
            repository
        )
    )
    assert deleted_digest != staged_digest
    assert initial["entries"]


def test_focal_worker_rechecks_execution_manifest_after_pytest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, _, _, _, _, binding, binding_sha256 = _make_binding_inputs(
        tmp_path
    )
    workspace = tmp_path / "workspace"
    _write_workspace_receipt(workspace, binding)
    binding_path = tmp_path / "binding.json"
    binding_path.write_bytes(quality_gate._canonical_json(binding) + b"\n")
    monkeypatch.setattr(quality_gate, "REPOSITORY_ROOT", repository)
    monkeypatch.setenv(
        "TALOS_TEST_WORKSPACE_ROOT", str(workspace.resolve())
    )
    monkeypatch.setenv(
        "TALOS_TEST_WORKSPACE_IDENTITY", str(workspace.resolve())
    )
    monkeypatch.setenv("TALOS_TEST_RUN_ID", binding["run_id"])
    monkeypatch.setenv(
        "TALOS_TEST_GATE_ID", binding["gate_identity_operational_label"]
    )
    monkeypatch.setenv(
        "TALOS_TEST_POLICY_ID", binding["policy_identity_operational_label"]
    )
    monkeypatch.setenv(
        "TALOS_TEST_REPOSITORY_COMMIT", binding["git_commit"]
    )

    def mutate_execution_input(*args, **kwargs):
        del args, kwargs
        (repository / "src" / "runtime.py").write_text(
            "CHANGED_DURING_TEST = True\n", encoding="utf-8"
        )
        return pytest.ExitCode.OK

    monkeypatch.setattr(pytest, "main", mutate_execution_input)
    perimeter = quality_gate.Perimeter(
        suites=(),
        optional_modules={},
        module_classifications={
            NODEID.split("::", 1)[0]: "required"
        },
    )

    result = quality_gate.run_gate(
        "release",
        perimeter,
        focal_nodeid=NODEID,
        focal_result_output=Path("/workspace/run/focal-result.json"),
        focal_binding_sha256=binding_sha256,
        focal_binding_path=binding_path,
    )

    assert result == 2


def test_effective_execution_manifest_is_order_independent_and_excludes_cache(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    profile = {
        "profile_version": 1,
        "scope": "talos.b06.snapshot.v1",
        "nodeid": NODEID,
        "required_logical_inputs": {
            "knowledge_store": "knowledge_store.db",
            "vector_store": "vector_store.db",
            "student_state": "student_state.db",
        },
        "required_snapshot_payload": {
            "sidecar_suffixes": ["-wal", "-shm", "-journal"],
            "sidecar_policy": (
                "record_absent_or_present_for_each_database"
            ),
        },
        "external_execution_resources": ["src/a.py"],
        "effective_execution_paths": ["config", "src"],
        "excluded_path_components": ["__pycache__", ".pytest_cache"],
        "fixture_constraints": {
            "fixture": "web_state_test_copy",
            "working_directory": "derived_snapshot_only",
            "use_mock": True,
            "database_identities": [
                "knowledge_store",
                "vector_store",
                "student_state",
            ],
        },
    }
    for root, order in ((first, ("a.py", "b.py")), (second, ("b.py", "a.py"))):
        (root / "config").mkdir()
        (root / "src").mkdir()
        (root / "config" / "test_perimeter.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "focal_execution_profiles": {
                        "b06-snapshot-v1": profile
                    },
                }
            ),
            encoding="utf-8",
        )
        for filename in order:
            (root / "src" / filename).write_text(
                f"{filename}\n", encoding="utf-8"
            )
    (first / "src" / "__pycache__").mkdir()
    (first / "src" / "__pycache__" / "ignored.pyc").write_bytes(b"ignored")
    (second / "src" / "__pycache__").mkdir()
    (second / "src" / "__pycache__" / "ignored.pyc").write_bytes(b"other")

    first_manifest, first_digest = (
        test_isolation_snapshots.build_effective_execution_manifest(first)
    )
    second_manifest, second_digest = (
        test_isolation_snapshots.build_effective_execution_manifest(second)
    )
    assert first_manifest == second_manifest
    assert first_digest == second_digest


def test_effective_execution_manifest_requires_declared_external_resources(
    tmp_path: Path,
) -> None:
    repository, _, _, _, _, _, _ = _make_binding_inputs(tmp_path)
    (repository / "data" / "runtime.json").unlink()
    with pytest.raises(
        test_isolation_snapshots.TestSnapshotError,
        match="Effective execution input is missing",
    ):
        test_isolation_snapshots.build_effective_execution_manifest(repository)


def test_focal_worker_rejects_inconsistent_snapshot_binding(
    tmp_path: Path,
) -> None:
    repository, _, _, _, _, binding, _ = _make_binding_inputs(tmp_path)
    workspace = tmp_path / "workspace"
    _write_workspace_receipt(workspace, binding)
    inconsistent_binding = {
        **binding,
        "snapshot_manifest_sha256": _sha256(b"different snapshot"),
    }
    binding_path = tmp_path / "binding.json"
    binding_path.write_bytes(
        quality_gate._canonical_json(inconsistent_binding) + b"\n"
    )
    inconsistent_digest = _sha256(
        quality_gate._canonical_json(inconsistent_binding)
    )

    with pytest.raises(
        quality_gate.FocalExecutionError,
        match="snapshot manifest digest mismatch",
    ):
        quality_gate.validate_focal_execution_binding(
            binding_path,
            expected_sha256=inconsistent_digest,
            profile="release",
            repository_root=repository,
            workspace_root=workspace,
            environment=_worker_environment(binding, workspace),
        )


def test_focal_collection_requires_exactly_the_allowlisted_nodeid() -> None:
    results = quality_gate.SuiteResults(
        ["tests/pedagogy"],
        expected_nodeid=NODEID,
    )
    session = SimpleNamespace(items=[SimpleNamespace(nodeid=NODEID)])
    results.pytest_collection_finish(session)

    assert results.focal_payload(0)["exactly_one_selected_test"] is True
    assert not hasattr(session, "shouldfail")

    session = SimpleNamespace(
        items=[
            SimpleNamespace(nodeid=NODEID),
            SimpleNamespace(nodeid=NODEID + "::unexpected"),
        ]
    )
    results.pytest_collection_finish(session)

    assert results.focal_payload(1)["exactly_one_selected_test"] is False
    assert "exactly the requested nodeid" in session.shouldfail


def test_focal_worker_accepts_matching_binding_and_workspace_receipt(
    tmp_path: Path,
) -> None:
    repository, _, _, _, _, binding, binding_sha256 = _make_binding_inputs(
        tmp_path
    )
    workspace = tmp_path / "workspace"
    _write_workspace_receipt(workspace, binding)
    binding_path = tmp_path / "binding.json"
    binding_path.write_bytes(quality_gate._canonical_json(binding) + b"\n")

    actual = quality_gate.validate_focal_execution_binding(
        binding_path,
        expected_sha256=binding_sha256,
        profile="release",
        repository_root=repository,
        workspace_root=workspace,
        environment=_worker_environment(binding, workspace),
    )

    assert actual == binding


@pytest.mark.parametrize(
    ("workspace_changes", "environment_changes", "expected_error"),
    [
        ({"manifest_sha256": _sha256(b"other")}, {}, "workspace receipt"),
        ({"scope": "different-scope"}, {}, "workspace receipt"),
        ({}, {"TALOS_TEST_RUN_ID": ""}, "run identity"),
    ],
)
def test_focal_worker_rejects_snapshot_or_run_mismatch(
    tmp_path: Path,
    workspace_changes: dict[str, str],
    environment_changes: dict[str, str],
    expected_error: str,
) -> None:
    repository, _, _, _, _, binding, binding_sha256 = _make_binding_inputs(
        tmp_path
    )
    workspace = tmp_path / "workspace"
    _write_workspace_receipt(workspace, binding, **workspace_changes)
    binding_path = tmp_path / "binding.json"
    binding_path.write_bytes(quality_gate._canonical_json(binding) + b"\n")
    environment = _worker_environment(binding, workspace)
    environment.update(environment_changes)

    with pytest.raises(
        quality_gate.FocalExecutionError, match=expected_error
    ):
        quality_gate.validate_focal_execution_binding(
            binding_path,
            expected_sha256=binding_sha256,
            profile="release",
            repository_root=repository,
            workspace_root=workspace,
            environment=environment,
        )


def test_focal_worker_rejects_digest_and_test_fingerprint_mismatch(
    tmp_path: Path,
) -> None:
    repository, _, test_file, _, _, binding, binding_sha256 = (
        _make_binding_inputs(tmp_path)
    )
    workspace = tmp_path / "workspace"
    _write_workspace_receipt(workspace, binding)
    binding_path = tmp_path / "binding.json"
    binding_path.write_bytes(quality_gate._canonical_json(binding) + b"\n")
    with pytest.raises(
        quality_gate.FocalExecutionError, match="binding digest"
    ):
        quality_gate.validate_focal_execution_binding(
            binding_path,
            expected_sha256=_sha256(b"wrong"),
            profile="release",
            repository_root=repository,
            workspace_root=workspace,
            environment=_worker_environment(binding, workspace),
        )

    test_file.write_text(
        f"def {NODEID.split('::', 1)[1]}(web_state_test_copy):\n"
        "    AppContainer(working_dir=web_state_test_copy, use_mock=True)\n"
        "    assert False\n",
        encoding="utf-8",
    )
    with pytest.raises(
        quality_gate.FocalExecutionError,
        match="effective execution manifest",
    ):
        quality_gate.validate_focal_execution_binding(
            binding_path,
            expected_sha256=binding_sha256,
            profile="release",
            repository_root=repository,
            workspace_root=workspace,
            environment=_worker_environment(binding, workspace),
        )


def test_focal_scope_profile_rejects_arbitrary_payload_and_bad_digest(
    tmp_path: Path,
) -> None:
    repository, _, _, _, manifest, binding, _ = _make_binding_inputs(
        tmp_path
    )
    valid_snapshot = {
        **manifest,
        "scope_profile_id": binding["scope_profile_id"],
        "scope_profile_version": binding["scope_profile_version"],
        "scope_profile_sha256": binding["scope_profile_sha256"],
        "databases": binding["snapshot_database_identities"],
        "wal_state": {
            name: {"status": "absent"}
            for name in binding["snapshot_database_identities"]
        },
        "shm_state": {
            name: {"status": "absent"}
            for name in binding["snapshot_database_identities"]
        },
        "journal_state": {
            name: {"status": "absent"}
            for name in binding["snapshot_database_identities"]
        },
    }
    profile, digest = test_isolation_snapshots.validate_scope_profile_manifest(
        valid_snapshot, repository
    )
    assert profile["scope"] == valid_snapshot["scope"]
    assert digest == binding["scope_profile_sha256"]

    for invalid in (
        {**valid_snapshot, "scope": "arbitrary-wide-scope"},
        {
            **valid_snapshot,
            "databases": {
                **valid_snapshot["databases"],
                "extra": "extra.db",
            },
        },
        {**valid_snapshot, "scope_profile_sha256": _sha256(b"wrong")},
    ):
        with pytest.raises(test_isolation_snapshots.TestSnapshotError):
            test_isolation_snapshots.validate_scope_profile_manifest(
                invalid, repository
            )


def test_focal_worker_rejects_changed_profile_runtime_nodeid_and_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, perimeter, _, _, _, binding, binding_sha256 = (
        _make_binding_inputs(tmp_path)
    )
    workspace = tmp_path / "workspace"
    _write_workspace_receipt(workspace, binding)
    binding_path = tmp_path / "binding.json"

    original_runtime = quality_gate.build_focal_runtime_identity
    monkeypatch.setattr(
        quality_gate,
        "build_focal_runtime_identity",
        lambda: {**original_runtime(), "pytest_version": "changed"},
    )
    binding_path.write_bytes(quality_gate._canonical_json(binding) + b"\n")
    with pytest.raises(
        quality_gate.FocalExecutionError, match="runtime identity"
    ):
        quality_gate.validate_focal_execution_binding(
            binding_path,
            expected_sha256=binding_sha256,
            profile="release",
            repository_root=repository,
            workspace_root=workspace,
            environment=_worker_environment(binding, workspace),
        )
    monkeypatch.setattr(
        quality_gate, "build_focal_runtime_identity", original_runtime
    )

    changed_profile = json.loads(perimeter.read_text(encoding="utf-8"))
    changed_profile["focal_execution_profiles"]["b06-snapshot-v1"][
        "scope"
    ] = "changed"
    perimeter.write_text(json.dumps(changed_profile), encoding="utf-8")
    with pytest.raises(
        quality_gate.FocalExecutionError,
        match="scope or effective execution manifest",
    ):
        quality_gate.validate_focal_execution_binding(
            binding_path,
            expected_sha256=binding_sha256,
            profile="release",
            repository_root=repository,
            workspace_root=workspace,
            environment=_worker_environment(binding, workspace),
        )

    repository, _, _, _, _, binding, binding_sha256 = _make_binding_inputs(
        tmp_path / "nodeid-case"
    )
    workspace = tmp_path / "nodeid-case" / "workspace"
    _write_workspace_receipt(workspace, binding)
    changed_binding = {**binding, "nodeid": NODEID + "::extra"}
    binding_path = tmp_path / "nodeid-case" / "binding.json"
    binding_path.write_bytes(
        quality_gate._canonical_json(changed_binding) + b"\n"
    )
    changed_digest = _sha256(quality_gate._canonical_json(changed_binding))
    with pytest.raises(quality_gate.FocalExecutionError, match="exact B06"):
        quality_gate.validate_focal_execution_binding(
            binding_path,
            expected_sha256=changed_digest,
            profile="release",
            repository_root=repository,
            workspace_root=workspace,
            environment=_worker_environment(binding, workspace),
        )


def test_focal_binding_is_validated_inside_bubblewrap(tmp_path: Path) -> None:
    repository = Path(quality_gate.__file__).resolve().parents[1]
    run_id = str(uuid4())
    manifest = {
        "snapshot_id": "synthetic-snapshot-bwrap",
        "source_identity": "synthetic-source-set",
        "source_fingerprint": _sha256(b"source"),
        "scope": "talos.b06.snapshot.v1",
        "scope_profile_id": "b06-snapshot-v1",
        "scope_profile_version": 1,
        "scope_profile_sha256": (
            test_isolation_snapshots.load_focal_scope_profile(repository)[1]
        ),
        "databases": {
            "knowledge_store": "knowledge_store.db",
            "vector_store": "vector_store.db",
            "student_state": "student_state.db",
        },
        "destination_identity": str(tmp_path / "sealed-snapshot"),
        "run_identity": run_id,
        "gate_identity": "caller-gate-label",
        "policy_identity": "caller-policy-label",
        "gate_fingerprint": test_isolation_snapshots._gate_fingerprint(
            repository
        ),
        "git_tree_or_commit": test_isolation_snapshots._repository_identity(
            repository
        ),
        "capture_id": "synthetic-capture-bwrap",
        "capture_attestation_sha256": _sha256(b"attestation"),
    }
    binding, binding_sha256 = quality_gate.build_focal_execution_binding(
        manifest=manifest,
        manifest_sha256=_sha256(b"manifest"),
        run_id=run_id,
        profile="release",
        repository_root=repository,
        perimeter_path=repository / "config" / "test_perimeter.json",
    )
    execution_root = tmp_path / "execution"
    workspace = execution_root / "test-data"
    workspace.mkdir(parents=True)
    (workspace / ".talos-test-workspace.json").write_text(
        json.dumps(
            {
                "manifest_sha256": binding["manifest_sha256"],
                "snapshot_id": binding["snapshot_id"],
                "scope": binding["scope"],
                "workspace_identity": "/workspace/run/test-data",
                "run_identity": run_id,
                "gate_identity": manifest["gate_identity"],
                "policy_identity": manifest["policy_identity"],
                "scope_profile_id": binding["scope_profile_id"],
                "scope_profile_sha256": binding[
                    "scope_profile_sha256"
                ],
            }
        ),
        encoding="utf-8",
    )
    (execution_root / "focal-binding.json").write_bytes(
        quality_gate._canonical_json(binding) + b"\n"
    )
    host_namespaces = {
        name: os.readlink(f"/proc/self/ns/{name}")
        for name in ("mnt", "net", "pid")
    }
    environment = {
        "TALOS_TEST_RUN_ID": run_id,
        "TALOS_TEST_GATE_ID": manifest["gate_identity"],
        "TALOS_TEST_POLICY_ID": manifest["policy_identity"],
        "TALOS_TEST_REPOSITORY_COMMIT": manifest["git_tree_or_commit"],
        "TALOS_TEST_WORKSPACE_ROOT": "/workspace/run/test-data",
        "TALOS_TEST_WORKSPACE_IDENTITY": "/workspace/run/test-data",
        "TALOS_TEST_EXECUTION_BINDING_SHA256": binding_sha256,
        "EXPECTED_MNT_NAMESPACE": host_namespaces["mnt"],
        "EXPECTED_NET_NAMESPACE": host_namespaces["net"],
        "EXPECTED_PID_NAMESPACE": host_namespaces["pid"],
    }
    code = """
import json
import os
from pathlib import Path
from scripts.quality_gate import validate_focal_execution_binding

binding = validate_focal_execution_binding(
    Path("/workspace/run/focal-binding.json"),
    expected_sha256=os.environ["TALOS_TEST_EXECUTION_BINDING_SHA256"],
    profile="release",
    repository_root=Path("/workspace/repository"),
    workspace_root=Path(os.environ["TALOS_TEST_WORKSPACE_ROOT"]),
)
print(json.dumps({
    "nodeid": binding["nodeid"],
    "run_id": binding["run_id"],
    "mnt_namespace": os.readlink("/proc/self/ns/mnt"),
    "net_namespace": os.readlink("/proc/self/ns/net"),
    "pid_namespace": os.readlink("/proc/self/ns/pid"),
}))
"""

    completed = run_isolated_process(
        repository,
        execution_root,
        [sys.executable, "-c", code],
        environment=environment,
        python_executable=sys.executable,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["nodeid"] == NODEID
    assert result["run_id"] == run_id
    assert result["mnt_namespace"] != host_namespaces["mnt"]
    assert result["net_namespace"] != host_namespaces["net"]
    assert result["pid_namespace"] != host_namespaces["pid"]


def test_isolated_focal_runner_propagates_binding_and_writes_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, perimeter, _, run_id, manifest, _, _ = _make_binding_inputs(
        tmp_path
    )
    # STEP-14 observes a real throwaway repository, not a directory named repository.
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    subprocess.run([
        "git", "-C", str(repository), "-c", "user.name=Synthetic gate test",
        "-c", "user.email=gate@example.invalid", "commit", "--allow-empty", "-qm", "fixture",
    ], check=True)
    snapshot = tmp_path / "sealed-snapshot"
    snapshot.mkdir()
    receipt_output = tmp_path / "focal-receipt.json"
    manifest_sha256 = _sha256(b"sealed manifest")
    manifest = {
        **manifest,
        "run_identity": run_id,
        "destination_identity": str(snapshot),
    }
    validation = SimpleNamespace(
        status="VALID",
        reason="valid synthetic snapshot",
        manifest=manifest,
    )
    events: list[str] = []
    monkeypatch.setattr(quality_gate, "REPOSITORY_ROOT", repository)
    monkeypatch.setattr(quality_gate, "PERIMETER_PATH", perimeter)
    monkeypatch.setattr(
        test_isolation_snapshots, "_repository_identity", lambda _: "b" * 40
    )

    def validate_snapshot(*args, **kwargs):
        del args, kwargs
        events.append("validate_snapshot")
        return validation

    monkeypatch.setattr(
        test_isolation_snapshots, "validate_snapshot", validate_snapshot
    )

    def derive_workspace(
        snapshot_root: Path,
        workspace_root: Path,
        **kwargs,
    ) -> Path:
        del snapshot_root
        events.append("derive_workspace")
        workspace_root.mkdir(parents=True)
        (workspace_root / ".talos-test-workspace.json").write_text(
            json.dumps(
                {
                    "snapshot_id": manifest["snapshot_id"],
                    "manifest_sha256": manifest_sha256,
                    "scope": manifest["scope"],
                    "run_identity": run_id,
                    "gate_identity": manifest["gate_identity"],
                    "policy_identity": manifest["policy_identity"],
                    "scope_profile_id": manifest["scope_profile_id"],
                    "scope_profile_sha256": manifest[
                        "scope_profile_sha256"
                    ],
                    "workspace_identity": kwargs["workspace_identity"],
                }
            ),
            encoding="utf-8",
        )
        return workspace_root

    monkeypatch.setattr(
        test_isolation_snapshots, "derive_test_workspace", derive_workspace
    )

    def verify_snapshot(*args):
        del args
        events.append("verify_snapshot")

    monkeypatch.setattr(
        test_isolation_snapshots, "verify_sealed_snapshot", verify_snapshot
    )
    for key, value in {
        "TALOS_TEST_SNAPSHOT_ROOT": str(snapshot),
        "TALOS_TEST_SNAPSHOT_MANIFEST_SHA256": manifest_sha256,
        "TALOS_TEST_SNAPSHOT_SCOPE": manifest["scope"],
        "TALOS_TEST_RUN_ID": run_id,
        "TALOS_TEST_GATE_ID": manifest["gate_identity"],
        "TALOS_TEST_POLICY_ID": manifest["policy_identity"],
    }.items():
        monkeypatch.setenv(key, value)

    captured: dict[str, object] = {}

    def fake_isolated_process(
        repository_root: Path,
        workspace_root: Path,
        command: list[str],
        *,
        environment: dict[str, str],
        **kwargs,
    ) -> subprocess.CompletedProcess[str]:
        del repository_root, kwargs
        events.append("bubblewrap")
        captured["command"] = command
        captured["environment"] = environment
        binding_path = workspace_root / "focal-binding.json"
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        binding_sha256 = environment["TALOS_TEST_EXECUTION_BINDING_SHA256"]
        assert command[command.index("--_focal-nodeid") + 1] == NODEID
        assert environment["TALOS_TEST_RUN_ID"] == run_id
        assert binding["nodeid"] == NODEID
        binding_digest = hashlib.sha256(
            quality_gate._canonical_json(binding)
        ).hexdigest()
        assert binding_sha256 == f"sha256:{binding_digest}"
        (workspace_root / ".quality-gate-worker-started").write_text(
            json.dumps(
                {
                    "token": environment["TALOS_QUALITY_GATE_START_TOKEN"],
                    "pid": os.getpid() + 1,
                    "mnt_namespace": "worker-mnt",
                    "net_namespace": "worker-net",
                    "pid_namespace": "worker-pid",
                }
            ),
            encoding="utf-8",
        )
        (workspace_root / "focal-result.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "profile": "release",
                    "expected_nodeid": NODEID,
                    "collected_nodeids": [NODEID],
                    "exactly_one_selected_test": True,
                    "test_outcome": "passed",
                    "pytest_exit_code": 0,
                    "binding_sha256": binding_sha256,
                    "runner_exit_code": 0,
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(
        "scripts.quality_gate_isolation.run_isolated_process",
        fake_isolated_process,
    )

    result = quality_gate.run_isolated_gate(
        "release",
        focal_nodeid=NODEID,
        execution_receipt_output=receipt_output,
    )

    assert result == 0
    assert receipt_output.is_file()
    receipt = json.loads(receipt_output.read_text(encoding="utf-8"))
    assert receipt["execution_mode"] == "focal_test"
    assert receipt["schema_version"] == 2
    assert receipt["exactly_one"] is True
    assert receipt["scope_profile_id"] == "b06-snapshot-v1"
    assert receipt["effective_execution_manifest_sha256"] == (
        receipt["binding"]["effective_execution_manifest_sha256"]
    )
    assert receipt["runtime_identity"] == receipt["binding"][
        "runtime_identity"
    ]
    assert receipt["binding"]["run_id"] == run_id
    assert receipt["result"]["collected_nodeids"] == [NODEID]
    assert receipt["isolation"]["mechanism"] == "bubblewrap"
    assert captured["environment"]["TALOS_TEST_RUN_ID"] == run_id
    assert events == [
        "validate_snapshot",
        "derive_workspace",
        "verify_snapshot",
        "bubblewrap",
        "verify_snapshot",
    ]
