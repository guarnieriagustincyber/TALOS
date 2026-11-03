import errno
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

import pytest

from scripts.quality_gate_isolation import (
    IsolationError,
    PROTECTED_DIRECTORIES,
    run_isolated_process,
    workspace_guest_path,
)
from study_engine.diagnostics.test_isolation_snapshots import (
    _repository_identity,
)


def _fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_workspace_guest_path_maps_host_path_to_mounted_workspace(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "execution"
    pytest_tmp = workspace / "pytest-tmp"
    pytest_tmp.mkdir(parents=True)

    assert workspace_guest_path(workspace, pytest_tmp) == Path(
        "/workspace/run/pytest-tmp"
    )


def test_workspace_guest_path_rejects_paths_outside_workspace(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "execution"
    workspace.mkdir()
    outside = tmp_path / "pytest-tmp"
    outside.mkdir()

    with pytest.raises(IsolationError, match="inside the host workspace"):
        workspace_guest_path(workspace, outside)


def test_bubblewrap_denies_protected_paths_and_allows_derived_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    student = repository / "data" / "student"
    web_state = repository / "data" / "web_state"
    student.mkdir(parents=True)
    web_state.mkdir(parents=True)
    source_db = student / "student_state.db"
    source_db.write_bytes(b"synthetic-protected-student-db")
    hardlink_alias = repository / "data" / "student-state-alias.txt"
    os.link(source_db, hardlink_alias)
    source_wal = student / "student_state.db-wal"
    source_wal.write_bytes(b"synthetic-protected-student-wal")
    source_shm = student / "student_state.db-shm"
    source_shm.write_bytes(b"synthetic-protected-student-shm")
    web_db = web_state / "vector_store.db"
    web_db.write_bytes(b"synthetic-protected-web-db")
    web_wal = web_state / "vector_store.db-wal"
    web_wal.write_bytes(b"synthetic-protected-web-wal")
    web_shm = web_state / "vector_store.db-shm"
    web_shm.write_bytes(b"synthetic-protected-web-shm")
    absent_db = web_state / "sessions.db"
    absent_db.write_bytes(b"synthetic-protected-no-sidecars")
    loose_db = repository / "data" / "other-protected.db"
    loose_db.write_bytes(b"synthetic-protected-database-alias")
    extra_protected_sources = {}
    for relative in PROTECTED_DIRECTORIES:
        directory = repository / relative
        directory.mkdir(parents=True, exist_ok=True)
        source = directory / "synthetic.db"
        source.write_bytes(f"protected:{relative}".encode("utf-8"))
        extra_protected_sources[relative] = source
    environment_file = repository / ".env"
    environment_file.write_text(
        "TALOS_TEST_HOST_SECRET=not-for-pytest", encoding="utf-8"
    )
    monkeypatch.setenv("TALOS_TEST_HOST_SECRET", "not-for-pytest")
    absent_sidecars = (
        Path(f"{absent_db}-wal"),
        Path(f"{absent_db}-shm"),
    )
    source_hashes = {
        source_db: _fingerprint(source_db),
        hardlink_alias: _fingerprint(hardlink_alias),
        source_wal: _fingerprint(source_wal),
        source_shm: _fingerprint(source_shm),
        web_db: _fingerprint(web_db),
        web_wal: _fingerprint(web_wal),
        web_shm: _fingerprint(web_shm),
        absent_db: _fingerprint(absent_db),
        loose_db: _fingerprint(loose_db),
        **{
            path: _fingerprint(path)
            for path in extra_protected_sources.values()
        },
    }

    workspace = tmp_path / "execution"
    workspace.mkdir()
    (workspace / "derived.db").write_bytes(b"derived-before")
    probe = {
        "source_db": str(source_db),
        "source_wal": str(source_wal),
        "source_dir_db": (
            "/workspace/repository/data/student/" "student_state.db"
        ),
        "source_dir_wal": (
            "/workspace/repository/data/student/" "student_state.db-wal"
        ),
        "source_shm": str(source_shm),
        "source_dir_shm": (
            "/workspace/repository/data/student/" "student_state.db-shm"
        ),
        "web_db": str(web_db),
        "web_wal": str(web_wal),
        "web_shm": str(web_shm),
        "web_dir_db": (
            "/workspace/repository/data/web_state/" "vector_store.db"
        ),
        "web_dir_wal": (
            "/workspace/repository/data/web_state/" "vector_store.db-wal"
        ),
        "web_dir_shm": (
            "/workspace/repository/data/web_state/" "vector_store.db-shm"
        ),
        "absent_db": str(absent_db),
        "absent_dir_db": "/workspace/repository/data/web_state/sessions.db",
        "loose_db": str(loose_db),
        "loose_repo_db": "/workspace/repository/data/other-protected.db",
        "hardlink_alias": (
            "/workspace/repository/data/student-state-alias.txt"
        ),
        "env_file": "/workspace/repository/.env",
        "workspace_db": "/workspace/run/derived.db",
        "workspace": "/workspace/run",
        "extra_protected": [
            {
                "absolute": str(path),
                "sandbox": str(
                    Path("/workspace/repository") / relative / "synthetic.db"
                ),
            }
            for relative, path in extra_protected_sources.items()
        ],
    }
    code = f"""
import json
import os
import pathlib
import sqlite3
import ctypes

probe = json.loads({json.dumps(json.dumps(probe))})
result = {{
    "mnt_namespace": os.readlink("/proc/self/ns/mnt"),
    "net_namespace": os.readlink("/proc/self/ns/net"),
    "pid_namespace": os.readlink("/proc/self/ns/pid"),
    "host_secret_environment": os.environ.get(
        "TALOS_TEST_HOST_SECRET", "absent"
    ),
}}
status = pathlib.Path("/proc/self/status").read_text(encoding="utf-8")
result["cap_eff"] = next(
    line.split()[1]
    for line in status.splitlines()
    if line.startswith("CapEff:")
)
unmount = ctypes.CDLL(None, use_errno=True).umount2
unmount_result = unmount(
    b"/workspace/repository/data/student", 2
)
result["unmount_protected_result"] = unmount_result
result["unmount_protected_errno"] = (
    ctypes.get_errno() if unmount_result != 0 else 0
)
try:
    pathlib.Path(
        "/workspace/repository/data/student/student_state.db"
    ).read_bytes()
    result["read_after_unmount"] = "allowed"
except OSError:
    result["read_after_unmount"] = "denied"
for label in ("source_db", "source_wal", "source_shm",
              "source_dir_db", "source_dir_wal", "source_dir_shm",
              "web_db", "web_wal", "web_shm",
              "web_dir_db", "web_dir_wal", "web_dir_shm",
              "absent_db", "absent_dir_db", "loose_db", "loose_repo_db",
              "hardlink_alias"):
    path = pathlib.Path(probe[label])
    try:
        content = path.read_bytes()
        result[label + "_read"] = "allowed"
        result[label + "_content"] = content.decode(
            "utf-8", errors="replace"
        )
    except OSError:
        result[label + "_read"] = "denied"
    try:
        with open(path, "rb"):
            result[label + "_open"] = "allowed"
    except OSError:
        result[label + "_open"] = "denied"
    try:
        path.write_bytes(b"must-not-write")
        result[label + "_write"] = "allowed"
    except OSError:
        result[label + "_write"] = "denied"
    if label.endswith("_db") or label == "hardlink_alias":
        try:
            connection = sqlite3.connect(str(path), timeout=0)
            connection.execute("SELECT 1")
            connection.close()
            result[label + "_sqlite"] = "allowed"
        except sqlite3.Error:
            result[label + "_sqlite"] = "denied"

for index, entry in enumerate(probe["extra_protected"]):
    path = pathlib.Path(entry["sandbox"])
    try:
        path.read_bytes()
        result[f"extra_{{index}}_read"] = "allowed"
    except OSError:
        result[f"extra_{{index}}_read"] = "denied"
    try:
        path.write_bytes(b"must-not-write")
        result[f"extra_{{index}}_write"] = "allowed"
    except OSError:
        result[f"extra_{{index}}_write"] = "denied"

derived = pathlib.Path(probe["workspace_db"])
result["derived_read"] = derived.read_bytes().decode()
derived.write_bytes(b"derived-after")
result["derived_after"] = derived.read_bytes().decode()
result["env_file_content"] = pathlib.Path(probe["env_file"]).read_text(
    encoding="utf-8"
)

escape = pathlib.Path(probe["workspace"]) / "escape.db"
escape.symlink_to(probe["source_db"])
try:
    escape.read_bytes()
    result["symlink_escape"] = "allowed"
except OSError:
    result["symlink_escape"] = "denied"

traversal = pathlib.Path("/workspace/run/../repository") / (
    "data/student/student_state.db"
)
try:
    traversal.read_bytes()
    result["traversal_escape"] = "allowed"
except OSError:
    result["traversal_escape"] = "denied"

pathlib.Path("/workspace/run/isolation-result.json").write_text(
    json.dumps(result), encoding="utf-8"
)
"""
    completed = run_isolated_process(
        repository,
        workspace,
        ["/usr/bin/python3", "-c", code],
        python_executable="/usr/bin/python3",
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(
        (workspace / "isolation-result.json").read_text(encoding="utf-8")
    )
    for label in (
        "source_db",
        "source_wal",
        "source_shm",
        "source_dir_db",
        "source_dir_wal",
        "source_dir_shm",
        "web_db",
        "web_wal",
        "web_shm",
        "web_dir_db",
        "web_dir_wal",
        "web_dir_shm",
        "absent_db",
        "absent_dir_db",
        "loose_db",
        "loose_repo_db",
        "hardlink_alias",
    ):
        assert result[f"{label}_read"] == "denied", label
        assert result[f"{label}_open"] == "denied"
        assert result[f"{label}_write"] == "denied"
    assert result["source_db_sqlite"] == "denied"
    assert result["source_dir_db_sqlite"] == "denied"
    assert result["web_db_sqlite"] == "denied"
    assert result["web_dir_db_sqlite"] == "denied"
    assert result["absent_db_sqlite"] == "denied"
    assert result["absent_dir_db_sqlite"] == "denied"
    assert result["loose_repo_db_sqlite"] == "denied"
    assert result["hardlink_alias_sqlite"] == "denied"
    assert result["symlink_escape"] == "denied"
    assert result["traversal_escape"] == "denied"
    assert result["unmount_protected_result"] == -1
    assert result["unmount_protected_errno"] == errno.EPERM
    assert result["read_after_unmount"] == "denied"
    assert int(result["cap_eff"], 16) == 0
    assert result["host_secret_environment"] == "absent"
    assert result["env_file_content"] == ""
    assert "not-for-pytest" in environment_file.read_text(encoding="utf-8")
    for index in range(len(extra_protected_sources)):
        assert result[f"extra_{index}_read"] == "denied"
        assert result[f"extra_{index}_write"] == "denied"
    assert result["derived_read"] == "derived-before"
    assert result["derived_after"] == "derived-after"
    assert result["mnt_namespace"] != os.readlink("/proc/self/ns/mnt")
    assert result["net_namespace"] != os.readlink("/proc/self/ns/net")
    assert result["pid_namespace"] != os.readlink("/proc/self/ns/pid")
    assert {
        path: _fingerprint(path) for path in source_hashes
    } == source_hashes
    assert all(not sidecar.exists() for sidecar in absent_sidecars)


def test_isolation_fails_closed_when_bubblewrap_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    workspace = tmp_path / "execution"
    workspace.mkdir()
    monkeypatch.setattr(
        "scripts.quality_gate_isolation.shutil.which",
        lambda _name: None,
    )

    with pytest.raises(IsolationError, match="bubblewrap is unavailable"):
        run_isolated_process(
            repository,
            workspace,
            ["/usr/bin/python3", "-c", "raise SystemExit(0)"],
            python_executable="/usr/bin/python3",
        )


def test_isolated_process_exit_code_is_preserved(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    workspace = tmp_path / "execution"
    workspace.mkdir()
    if shutil.which("bwrap") is None:
        pytest.fail("bubblewrap is required for the isolation contract tests")

    completed = run_isolated_process(
        repository,
        workspace,
        ["/usr/bin/python3", "-c", "raise SystemExit(23)"],
        python_executable="/usr/bin/python3",
    )

    assert completed.returncode == 23


def test_active_virtual_environment_is_available_read_only_in_sandbox(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    workspace = tmp_path / "execution"
    workspace.mkdir()
    code = (
        "import pathlib, pytest, sys; "
        "pathlib.Path('/workspace/run/runtime.txt').write_text("
        "sys.prefix + ':' + pytest.__version__, encoding='utf-8')"
    )

    completed = run_isolated_process(
        repository,
        workspace,
        [sys.executable, "-c", code],
        python_executable=sys.executable,
    )

    assert completed.returncode == 0, completed.stderr
    runtime = (workspace / "runtime.txt").read_text(encoding="utf-8")
    assert runtime.startswith("/opt/talos-venv:")


def test_synthetic_pytest_runs_inside_the_process_boundary(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    protected = repository / "data" / "student"
    protected.mkdir(parents=True)
    source = protected / "student_state.db"
    source.write_bytes(b"synthetic-production-state")
    workspace = tmp_path / "execution"
    test_directory = workspace / "synthetic"
    test_directory.mkdir(parents=True)
    derived = workspace / "derived.db"
    derived.write_bytes(b"isolated-state")
    test_file = test_directory / "test_boundary.py"
    test_file.write_text(
        f"""
from pathlib import Path
import sqlite3

import pytest


def test_only_derived_workspace_is_accessible():
    protected = Path({str(source)!r})
    masked = Path(
        "/workspace/repository/data/student/student_state.db"
    )
    for path in (protected, masked):
        with pytest.raises(OSError):
            path.read_bytes()
        with pytest.raises(OSError):
            path.write_bytes(b"forbidden")
        with pytest.raises(sqlite3.Error):
            sqlite3.connect(str(path), timeout=0)

    derived = Path("/workspace/run/derived.db")
    assert derived.read_bytes() == b"isolated-state"
    derived.write_bytes(b"writable-test-state")
    assert derived.read_bytes() == b"writable-test-state"
""",
        encoding="utf-8",
    )

    completed = run_isolated_process(
        repository,
        workspace,
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "/workspace/run/synthetic/test_boundary.py",
        ],
        python_executable=sys.executable,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "1 passed" in completed.stdout
    assert (
        _fingerprint(source)
        == hashlib.sha256(b"synthetic-production-state").hexdigest()
    )


def test_snapshot_contract_tests_run_without_git_or_production_mounts(
    tmp_path: Path,
) -> None:
    repository = Path(__file__).resolve().parents[3]
    workspace = tmp_path / "execution"
    workspace.mkdir()
    completed = run_isolated_process(
        repository,
        workspace,
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "/workspace/repository/tests/unit/diagnostics/"
            "test_test_isolation_snapshots.py",
        ],
        environment={
            "TALOS_TEST_REPOSITORY_COMMIT": _repository_identity(repository),
        },
        python_executable=sys.executable,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
