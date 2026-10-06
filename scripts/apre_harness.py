"""Run the A-PRE release gate in an OS-isolated, traced environment."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import uuid
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SANDBOX_REPOSITORY = Path("/work/repository")
SANDBOX_EVIDENCE = Path("/work/evidence")
SANDBOX_SCRATCH = Path("/work/scratch")
SANDBOX_RUNTIME = Path("/opt/apre-runtime")
COUNTS = ("collected", "passed", "failed", "skipped", "collection_errors")
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


def _contained(path: Path, parent: Path) -> bool:
    return path == parent or path.is_relative_to(parent)


def _validate_roots(
    repository: Path, evidence: Path, scratch: Path
) -> tuple[Path, Path, Path]:
    roots = tuple(path.resolve() for path in (repository, evidence, scratch))
    repository_root, evidence_root, scratch_root = roots
    if not repository_root.is_dir():
        raise ValueError("repository root must be an existing directory")
    if not evidence_root.is_dir() or not scratch_root.is_dir():
        raise ValueError("evidence and scratch roots must already exist")
    if _contained(evidence_root, repository_root) or _contained(
        scratch_root, repository_root
    ):
        raise ValueError(
            "evidence and scratch roots must be outside repository"
        )
    if _contained(evidence_root, scratch_root) or _contained(
        scratch_root, evidence_root
    ):
        raise ValueError("evidence and scratch roots must be disjoint")
    return roots


def _add_mount_parent_directories(command: list[str], target: Path) -> None:
    parents = list(reversed(target.parents))
    for parent in parents:
        if parent == Path("/"):
            continue
        command.extend(["--dir", str(parent)])


def build_bwrap_argv(
    repository: Path,
    evidence: Path,
    scratch: Path,
    argv: list[str],
    *,
    runtime_root: Path | None = None,
    runtime_base: Path | None = None,
    environment: dict[str, str] | None = None,
) -> list[str]:
    """Build a minimal filesystem view without network or host home."""
    if not argv or any(not part for part in argv):
        raise ValueError("sandbox command must be a non-empty argv array")
    repository, evidence, scratch = _validate_roots(
        repository, evidence, scratch
    )
    bwrap = shutil.which("bwrap")
    if bwrap is None:
        raise FileNotFoundError("bubblewrap (bwrap) is required")
    command = [
        bwrap,
        "--unshare-all",
        "--die-with-parent",
        "--new-session",
        "--tmpfs",
        "/",
        "--dir",
        "/usr",
        "--ro-bind",
        "/usr",
        "/usr",
        "--symlink",
        "usr/bin",
        "/bin",
        "--symlink",
        "usr/lib",
        "/lib",
        "--symlink",
        "usr/lib64",
        "/lib64",
        "--dev",
        "/dev",
        "--proc",
        "/proc",
        "--tmpfs",
        "/tmp",
        "--dir",
        "/tmp/home",
        "--dir",
        "/work",
        "--ro-bind",
        str(repository),
        str(SANDBOX_REPOSITORY),
        "--bind",
        str(evidence),
        str(SANDBOX_EVIDENCE),
        "--bind",
        str(scratch),
        str(SANDBOX_SCRATCH),
        "--setenv",
        "PATH",
        f"{SANDBOX_RUNTIME}/bin:/usr/bin:/bin",
        "--setenv",
        "HOME",
        "/tmp/home",
        "--setenv",
        "TMPDIR",
        str(SANDBOX_SCRATCH),
        "--setenv",
        "PYTHONDONTWRITEBYTECODE",
        "1",
        "--setenv",
        "LANG",
        "C.UTF-8",
        "--chdir",
        str(SANDBOX_REPOSITORY),
    ]
    if runtime_root is not None:
        runtime_root = runtime_root.resolve()
        if not runtime_root.is_dir():
            raise ValueError("runtime root must be an existing directory")
        if _contained(runtime_root, repository):
            raise ValueError("runtime root must be outside the repository")
        if any(
            _contained(runtime_root, root) or _contained(root, runtime_root)
            for root in (evidence, scratch)
        ):
            raise ValueError(
                "runtime root must be separate from evidence/scratch"
            )
        command.extend(["--dir", "/opt"])
        command.extend(["--ro-bind", str(runtime_root), str(SANDBOX_RUNTIME)])
    if runtime_base is not None:
        runtime_base = runtime_base.resolve()
        if not runtime_base.is_dir():
            raise ValueError("runtime base must be an existing directory")
        home = Path.home().resolve()
        if runtime_base == home or home.is_relative_to(runtime_base):
            raise ValueError(
                "runtime base cannot expose the host home directory"
            )
        if any(
            _contained(runtime_base, root) or _contained(root, runtime_base)
            for root in (repository, evidence, scratch)
        ):
            raise ValueError(
                "runtime base must be separate from "
                "repository/evidence/scratch"
            )
        if not runtime_base.is_relative_to(Path("/usr")):
            _add_mount_parent_directories(command, runtime_base)
            command.extend(["--ro-bind", str(runtime_base), str(runtime_base)])
    for name, value in sorted((environment or {}).items()):
        if not name or "\x00" in name or "\x00" in value:
            raise ValueError("sandbox environment contains an invalid value")
        command.extend(["--setenv", name, value])
    command.extend(["--", *argv])
    return command


def run_sandboxed_command(
    repository: Path,
    evidence: Path,
    scratch: Path,
    argv: list[str],
    *,
    runtime_root: Path | None = None,
    runtime_base: Path | None = None,
    trace_prefix: str = "syscall.trace",
) -> tuple[int, list[Path], list[str]]:
    """Run a synthetic or fixed gate command while persisting its evidence."""
    repository, evidence, scratch = _validate_roots(
        repository, evidence, scratch
    )
    if Path(trace_prefix).name != trace_prefix:
        raise ValueError("trace prefix must be a filename, not a path")
    bwrap_argv = build_bwrap_argv(
        repository,
        evidence,
        scratch,
        argv,
        runtime_root=runtime_root,
        runtime_base=runtime_base,
    )
    strace = shutil.which("strace")
    if strace is None:
        raise FileNotFoundError("strace is required")
    trace_path = evidence / trace_prefix
    traced_argv = [
        strace,
        "-ff",
        "-qq",
        "-ttt",
        "-yy",
        "-s",
        "128",
        "-e",
        "trace=%file,%network,%process,%ipc,%memory",
        "-o",
        str(trace_path),
        "--",
        *bwrap_argv,
    ]
    stdout_path = evidence / "stdout.txt"
    stderr_path = evidence / "stderr.txt"
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        completed = subprocess.run(
            traced_argv,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            check=False,
            env={
                "PATH": "/usr/bin:/bin",
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
            },
        )
    trace_paths = sorted(evidence.glob(f"{trace_prefix}.*"))
    tracer_stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
    trace_started = bool(trace_paths) and "PTRACE_TRACEME" not in tracer_stderr
    isolation = {
        "schema_version": 1,
        "bubblewrap": shutil.which("bwrap"),
        "strace": strace,
        "network_namespace": "unshare-all",
        "repository": {
            "sandbox_path": str(SANDBOX_REPOSITORY),
            "read_only": True,
        },
        "runtime": {
            "sandbox_path": str(SANDBOX_RUNTIME),
            "read_only": True,
        },
        "writable_paths": [
            str(SANDBOX_EVIDENCE),
            str(SANDBOX_SCRATCH),
            "/tmp",
        ],
        "host_home_mounted": False,
        "trace_filter": "%file,%network,%process,%ipc,%memory",
        "trace_complete": False,
        "trace_started": trace_started,
        "trace_error": (
            tracer_stderr.strip()
            if not trace_started and tracer_stderr.strip()
            else None
        ),
        "trace_limitation": (
            "The selected syscall classes omit data-bearing read/write "
            "syscalls; read-only mounts and network namespace enforce the "
            "primary filesystem/network boundary."
        ),
        "exit_code": completed.returncode,
        "trace_files": [path.name for path in trace_paths],
    }
    (evidence / "isolation.json").write_text(
        json.dumps(isolation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return completed.returncode, trace_paths, traced_argv


def run_bwrap_command(
    repository: Path,
    evidence: Path,
    scratch: Path,
    argv: list[str],
) -> tuple[int, list[str]]:
    """Run an OS-boundary fixture without claiming syscall-trace coverage."""
    command = build_bwrap_argv(repository, evidence, scratch, argv)
    with (
        (evidence / "bwrap.stdout").open("wb") as stdout,
        (evidence / "bwrap.stderr").open("wb") as stderr,
    ):
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            check=False,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        )
    return completed.returncode, command


def trace_qualification_passes(isolation: dict[str, Any]) -> bool:
    return (
        isolation.get("exit_code") == 0
        and isolation.get("trace_started") is True
        and isolation.get("trace_complete") is True
    )


def _git(repository: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _tree_fingerprint(repository: Path) -> str:
    digest = hashlib.sha256()
    paths = _git(repository, "ls-files", "-z").split("\0")
    for relative in sorted(path for path in paths if path):
        path = repository / relative
        digest.update(relative.encode("utf-8", errors="surrogateescape"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        digest.update(b"\0")
    return digest.hexdigest()


def _clean_worktree(repository: Path) -> bool:
    return not _git(
        repository, "status", "--porcelain", "--untracked-files=all"
    )


def _manifest(repository: Path) -> dict[str, Any]:
    return json.loads(
        (repository / "config/test_perimeter.json").read_text(encoding="utf-8")
    )


def _empty_collection(manifest: dict[str, Any], error: str) -> dict[str, Any]:
    suites = []
    totals = dict.fromkeys(COUNTS, 0)
    for suite in manifest["suites"]:
        support_only = suite["classification"] == "support-only"
        suites.append(
            {
                "path": suite["path"],
                "classification": suite["classification"],
                "status": "SKIP" if support_only else "ERROR",
                **dict.fromkeys(COUNTS, 0),
                "skip_reasons": (
                    ["support-only helper suite"] if support_only else []
                ),
                "duration_seconds": 0.0,
                "warnings": [],
                "errors": [] if support_only else [error],
            }
        )
    return {
        "collections": totals,
        "suites": suites,
        "optional_modules": [
            {
                "path": item["path"],
                "status": "SKIP",
                "reason": item["reason"],
            }
            for item in manifest["module_overrides"]
        ],
    }


def build_result(
    repository: Path,
    evidence: Path,
    *,
    runtime_python: Path,
    uv_version: str,
    command_exit_code: int,
    started_at: str,
    duration_seconds: float,
    before_tree_hash: str,
    after_tree_hash: str,
    trace_paths: list[Path],
) -> dict[str, Any]:
    from scripts.apre_result import REQUIRED_INPUTS, sha256_file

    manifest = _manifest(repository)
    collector_path = evidence / "collector.json"
    errors: list[str] = []
    collector: Any = None
    try:
        collector = json.loads(collector_path.read_text(encoding="utf-8"))
        if not isinstance(collector, dict):
            raise ValueError("collector root must be an object")
        result_data = {
            "collections": collector["collections"],
            "suites": collector["suites"],
            "optional_modules": collector["optional_modules"],
        }
        if (
            not isinstance(result_data["collections"], dict)
            or not isinstance(result_data["suites"], list)
            or not isinstance(result_data["optional_modules"], list)
            or any(
                not isinstance(row, dict)
                or not isinstance(row.get("status"), str)
                for row in result_data["suites"]
            )
        ):
            raise ValueError("collector fields have invalid types")
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors.append(f"collector is missing or invalid: {error}")
        result_data = _empty_collection(manifest, errors[0])

    changed = before_tree_hash != after_tree_hash or not _clean_worktree(
        repository
    )
    unexpected_changes = (
        ["read-only snapshot tree fingerprint changed"] if changed else []
    )
    if changed:
        errors.append("snapshot changed during isolated run")
    isolation_path = evidence / "isolation.json"
    try:
        isolation = json.loads(isolation_path.read_text(encoding="utf-8"))
        if not isinstance(isolation, dict):
            raise ValueError("isolation report root must be an object")
    except (OSError, ValueError, TypeError) as error:
        errors.append(f"isolation report is missing or invalid: {error}")
        isolation = {
            "exit_code": command_exit_code,
            "trace_started": False,
            "trace_complete": False,
            "trace_error": str(error),
        }
    required_artifacts = (
        "stdout.txt",
        "stderr.txt",
        "collector.json",
        "effects.json",
        "isolation.json",
    )
    for relative in required_artifacts:
        if not (evidence / relative).is_file():
            message = f"required evidence artifact is missing: {relative}"
            if message not in errors:
                errors.append(message)
    if isolation["exit_code"] != command_exit_code:
        errors.append("sandbox and gate exit codes differ")
    if not isolation.get("trace_started"):
        errors.append(
            "strace could not attach to the sandboxed process: "
            + str(
                isolation.get("trace_error") or "no syscall trace was recorded"
            )
        )
    if not isolation.get("trace_complete"):
        errors.append(
            "syscall observation is incomplete; PRE cannot be accepted"
        )
    if not trace_paths:
        errors.append("strace produced no per-process trace files")
    if command_exit_code and not any(
        row["status"] == "FAIL" for row in result_data["suites"]
    ):
        errors.append(f"isolated gate exited with status {command_exit_code}")
    for row in result_data["suites"]:
        if row.get("status") == "ERROR":
            errors.extend(
                f"{row.get('path', 'unknown suite')}: {message}"
                for message in row.get("errors", [])
                if isinstance(message, str) and message
            )

    if errors:
        global_status = "ERROR"
        exit_code = command_exit_code or 2
    elif (
        command_exit_code == 0
        and not changed
        and not any(
            row["status"] in {"FAIL", "ERROR"} for row in result_data["suites"]
        )
    ):
        global_status = "PASS"
        exit_code = 0
    elif any(row["status"] == "FAIL" for row in result_data["suites"]):
        global_status = "FAIL"
        exit_code = command_exit_code or 1
    else:
        global_status = "ERROR"
        exit_code = command_exit_code or 2

    repository_clean = _clean_worktree(repository)
    commit = _git(repository, "rev-parse", "HEAD").strip()
    branch = _git(repository, "branch", "--show-current").strip()
    version = subprocess.run(
        [str(runtime_python), "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    version = (version.stdout or version.stderr).strip()
    version = version.removeprefix("Python ")
    artifact_paths = sorted(
        (
            path
            for path in evidence.rglob("*")
            if path.is_file() and path.name not in {"result.json"}
        ),
        key=lambda path: path.relative_to(evidence).as_posix(),
    )
    artifacts = [
        {
            "path": artifact.relative_to(evidence).as_posix(),
            "sha256": sha256_file(artifact),
        }
        for artifact in artifact_paths
        if artifact.is_file()
    ]
    totals = result_data["collections"]
    warnings = [
        "syscall trace excludes data-bearing read/write syscall classes",
        "Python audit observer reports native coverage as incomplete",
    ]
    if isinstance(collector, dict):
        warnings.extend(
            warning
            for warning in collector.get("warnings", [])
            if warning not in warnings
        )
    if errors and global_status == "ERROR":
        error_rows = [
            row for row in result_data["suites"] if row["status"] == "ERROR"
        ]
        if error_rows:
            for row in error_rows:
                row["errors"] = list(dict.fromkeys(row["errors"] + errors))
    report = {
        "schema_version": 1,
        "run_id": f"apre-{uuid.uuid4()}",
        "global_status": global_status,
        "started_at": started_at,
        "duration_seconds": duration_seconds,
        "identity": {
            "repository": repository.name,
            "branch": branch or "detached",
            "commit": commit,
            "working_tree_clean": repository_clean,
            "working_tree_diff_sha256": hashlib.sha256(
                _git(repository, "diff", "HEAD", "--binary").encode("utf-8")
            ).hexdigest(),
            "platform": platform.platform(),
        },
        "runtime": {
            "python_executable": str(SANDBOX_RUNTIME / "bin" / "python"),
            "python_version": version,
            "uv_version": uv_version,
            "input_hashes": {
                key: sha256_file(repository / key)
                for key in sorted(REQUIRED_INPUTS)
            },
        },
        "command": [
            str(SANDBOX_RUNTIME / "bin" / "python"),
            "scripts/quality_gate.py",
            "--profile",
            "release",
        ],
        "profile": "release",
        "exit_code": exit_code,
        "collections": totals,
        "suites": result_data["suites"],
        "optional_modules": result_data["optional_modules"],
        "artifacts": artifacts,
        "sterility": {
            "before_state_sha256": before_tree_hash,
            "after_state_sha256": after_tree_hash,
            "unexpected_changes": unexpected_changes,
        },
        "warnings": warnings,
        "errors": errors,
    }
    return report


def run_release_gate(
    repository: Path,
    evidence: Path,
    scratch: Path,
    *,
    runtime_root: Path,
    runtime_base: Path,
    runtime_python: Path,
    uv_executable: Path,
) -> int:
    from scripts.apre_result import write_result

    repository, evidence, scratch = _validate_roots(
        repository, evidence, scratch
    )
    if any(evidence.iterdir()) or any(scratch.iterdir()):
        raise ValueError("evidence and scratch roots must be empty before run")
    if not _clean_worktree(repository):
        raise ValueError("A-PRE release harness requires a clean snapshot")
    uv_version = subprocess.run(
        [str(uv_executable), "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    uv_version_text = (uv_version.stdout or uv_version.stderr).strip()
    if uv_version_text != "uv 0.12.20":
        raise ValueError("A-PRE requires uv 0.12.20")
    if not runtime_python.is_file() or not runtime_root.is_dir():
        raise ValueError("the isolated runtime interpreter/root are required")
    python_version = subprocess.run(
        [str(runtime_python), "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    python_version_text = (
        python_version.stdout or python_version.stderr
    ).strip()
    if not python_version_text.startswith("Python 3.10."):
        raise ValueError("A-PRE requires a CPython 3.10 runtime")
    expected_python = runtime_root.absolute() / "bin" / "python"
    if runtime_python.absolute() != expected_python:
        raise ValueError("runtime interpreter must be runtime-root/bin/python")
    config_path = runtime_root / "pyvenv.cfg"
    if not config_path.is_file():
        raise ValueError("runtime root must contain pyvenv.cfg")
    home_lines = [
        line.partition("=")[2].strip()
        for line in config_path.read_text(encoding="utf-8").splitlines()
        if line.partition("=")[0].strip() == "home"
    ]
    if len(home_lines) != 1 or not home_lines[0]:
        raise ValueError("runtime pyvenv.cfg must define exactly one home")
    expected_base = Path(home_lines[0]).parent.resolve()
    if runtime_base.resolve() != expected_base:
        raise ValueError(
            "runtime base must match the Python home in pyvenv.cfg"
        )
    if _contained(evidence, repository) or _contained(scratch, repository):
        raise ValueError("evidence and scratch must remain external")

    started = datetime.now(timezone.utc).isoformat()
    start_time = time.monotonic()
    before_tree_hash = _tree_fingerprint(repository)
    command = [
        str(SANDBOX_RUNTIME / "bin" / "python"),
        "scripts/quality_gate.py",
        "--profile",
        "release",
    ]
    sandbox_command = build_bwrap_argv(
        repository,
        evidence,
        scratch,
        command,
        runtime_root=runtime_root,
        runtime_base=runtime_base,
        environment={
            "TALOS_APRE_EFFECTS_OUTPUT": str(
                SANDBOX_EVIDENCE / "effects.json"
            ),
            "TALOS_APRE_SCRATCH_ROOT": str(SANDBOX_SCRATCH),
            "TALOS_APRE_COLLECTOR_OUTPUT": str(
                SANDBOX_EVIDENCE / "collector.json"
            ),
        },
    )
    strace = shutil.which("strace")
    if strace is None:
        raise FileNotFoundError("strace is required")
    probe_evidence = evidence / "tracer-preflight"
    probe_evidence.mkdir()
    probe_code, probe_traces, _ = run_sandboxed_command(
        repository,
        probe_evidence,
        scratch,
        ["/usr/bin/true"],
        trace_prefix="preflight.trace",
    )
    probe_isolation = json.loads(
        (probe_evidence / "isolation.json").read_text(encoding="utf-8")
    )
    if not trace_qualification_passes(probe_isolation):
        (evidence / "stdout.txt").write_text(
            "A-PRE gate was not started: syscall tracing preflight failed.\n",
            encoding="utf-8",
        )
        (evidence / "stderr.txt").write_text(
            str(
                probe_isolation.get("trace_error")
                or probe_isolation.get("trace_limitation")
            )
            + "\n",
            encoding="utf-8",
        )
        isolation = {
            **probe_isolation,
            "gate_started": False,
            "exit_code": 2,
            "trace_files": [
                path.relative_to(evidence).as_posix() for path in probe_traces
            ],
        }
        command_exit_code = 2
        trace_paths = probe_traces
    else:
        trace_prefix = evidence / "syscall.trace"
        traced_command = [
            strace,
            "-ff",
            "-qq",
            "-ttt",
            "-yy",
            "-s",
            "128",
            "-e",
            "trace=%file,%network,%process,%ipc,%memory",
            "-o",
            str(trace_prefix),
            "--",
            *sandbox_command,
        ]
        with (
            (evidence / "stdout.txt").open("wb") as stdout,
            (evidence / "stderr.txt").open("wb") as stderr,
        ):
            completed = subprocess.run(
                traced_command,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                check=False,
                env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
            )
        trace_paths = sorted(evidence.glob("syscall.trace.*"))
        isolation = {
            **probe_isolation,
            "gate_started": True,
            "trace_complete": False,
            "exit_code": completed.returncode,
            "trace_files": [path.name for path in trace_paths],
        }
        command_exit_code = completed.returncode
    (evidence / "isolation.json").write_text(
        json.dumps(isolation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    after_tree_hash = _tree_fingerprint(repository)
    report = build_result(
        repository,
        evidence,
        runtime_python=runtime_python,
        uv_version=uv_version_text.removeprefix("uv "),
        command_exit_code=command_exit_code,
        started_at=started,
        duration_seconds=time.monotonic() - start_time,
        before_tree_hash=before_tree_hash,
        after_tree_hash=after_tree_hash,
        trace_paths=trace_paths,
    )
    write_result(
        report,
        _manifest(repository),
        repository_root=repository,
        evidence_root=evidence,
        output_path=evidence / "result.json",
    )
    verifier = subprocess.run(
        [
            sys.executable,
            str(repository / "scripts/verify_apre_result.py"),
            "--report",
            str(evidence / "result.json"),
            "--manifest",
            str(repository / "config/test_perimeter.json"),
            "--repository-root",
            str(repository),
            "--evidence-root",
            str(evidence),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    (evidence / "verification.json").write_text(
        verifier.stdout or verifier.stderr,
        encoding="utf-8",
    )
    return (
        0
        if verifier.returncode == 0 and report["global_status"] == "PASS"
        else 1
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--runtime-base", type=Path, required=True)
    parser.add_argument("--runtime-python", type=Path, required=True)
    parser.add_argument("--uv", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        return run_release_gate(
            args.repository,
            args.evidence,
            args.scratch,
            runtime_root=args.runtime_root,
            runtime_base=args.runtime_base,
            runtime_python=args.runtime_python,
            uv_executable=args.uv,
        )
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"A-PRE harness error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
