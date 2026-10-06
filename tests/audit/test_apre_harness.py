"""Synthetic-only tests for the A-PRE OS isolation and syscall harness."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from scripts.apre_harness import _tree_fingerprint, build_result
from scripts.apre_result import REQUIRED_INPUTS, write_result
from scripts.verify_apre_result import verify_artifact
from scripts.apre_harness import (
    build_bwrap_argv,
    run_bwrap_command,
    run_sandboxed_command,
    trace_qualification_passes,
)
from scripts.quality_gate import validate_perimeter


def test_sandbox_allows_scratch_and_denies_host_writes_and_network(
    tmp_path: Path,
) -> None:
    if shutil.which("bwrap") is None or shutil.which("strace") is None:
        pytest.fail("A-PRE harness validation requires bwrap and strace")

    repository = tmp_path / "repository"
    evidence = tmp_path / "evidence"
    scratch = tmp_path / "scratch"
    repository.mkdir()
    evidence.mkdir()
    scratch.mkdir()
    result_path = scratch / "probe.json"
    program = """
import json
import socket
import sqlite3
import subprocess
from pathlib import Path

result = {}
Path("/work/scratch/allowed.txt").write_text("allowed", encoding="utf-8")
try:
    Path("/work/repository/denied.txt").write_text("denied", encoding="utf-8")
except OSError as error:
    result["repository_write_denied"] = True
    result["repository_write_error"] = type(error).__name__
else:
    result["repository_write_denied"] = False
try:
    Path("/usr/apre-harness-denied").write_text("denied", encoding="utf-8")
except OSError as error:
    result["host_write_denied"] = True
    result["host_write_error"] = type(error).__name__
else:
    result["host_write_denied"] = False
proc_status = Path("/proc/self/status").read_text(encoding="utf-8")
result["proc_visible"] = "NSpid:" in proc_status
with sqlite3.connect("/work/scratch/fixture.sqlite"):
    pass
subprocess.run(["/usr/bin/true"], check=True)
try:
    with socket.socket() as client:
        client.settimeout(0.2)
        client.connect(("1.1.1.1", 443))
except OSError as error:
    result["network_denied"] = True
    result["network_error"] = type(error).__name__
else:
    result["network_denied"] = False
Path("/work/scratch/probe.json").write_text(
    json.dumps(result), encoding="utf-8"
)
"""
    exit_code, command = run_bwrap_command(
        repository,
        evidence,
        scratch,
        ["/usr/bin/python3", "-c", program],
    )

    assert exit_code == 0
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["repository_write_denied"] is True
    assert result["host_write_denied"] is True
    assert result["proc_visible"] is True
    assert result["network_denied"] is True
    assert (scratch / "allowed.txt").read_text(encoding="utf-8") == "allowed"
    assert (scratch / "fixture.sqlite").is_file()
    assert not (repository / "denied.txt").exists()
    assert "--unshare-all" in command

    trace_code, trace_paths, _ = run_sandboxed_command(
        repository,
        evidence,
        scratch,
        ["/usr/bin/true"],
    )
    isolation = json.loads((evidence / "isolation.json").read_text())
    if trace_code == 0:
        assert trace_paths
        assert isolation["trace_started"] is True
        traces = "\n".join(
            path.read_text(encoding="utf-8") for path in trace_paths
        )
        assert "execve(" in traces
    else:
        assert isolation["trace_started"] is False
        assert "PTRACE_TRACEME" in isolation["trace_error"]
    assert isolation["network_namespace"] == "unshare-all"
    assert isolation["trace_complete"] is False
    assert isolation["repository"]["read_only"] is True
    assert isolation["host_home_mounted"] is False


def test_sandbox_rejects_evidence_or_scratch_inside_repository(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    evidence = repository / "evidence"
    scratch = tmp_path / "scratch"
    evidence.mkdir()
    scratch.mkdir()

    with pytest.raises(ValueError, match="outside repository"):
        build_bwrap_argv(
            repository,
            evidence,
            scratch,
            ["/usr/bin/true"],
        )


def test_sandbox_requires_disjoint_external_evidence_and_scratch(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    evidence = tmp_path / "evidence"
    scratch = evidence / "scratch"
    repository.mkdir()
    scratch.mkdir(parents=True)

    with pytest.raises(ValueError, match="must be disjoint"):
        build_bwrap_argv(
            repository,
            evidence,
            scratch,
            [sys.executable, "-c", "pass"],
        )


def test_sandbox_refuses_mounting_the_host_home_as_runtime_base(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    evidence = tmp_path / "evidence"
    scratch = tmp_path / "scratch"
    runtime = tmp_path / "runtime"
    for directory in (repository, evidence, scratch, runtime):
        directory.mkdir()

    with pytest.raises(ValueError, match="cannot expose the host home"):
        build_bwrap_argv(
            repository,
            evidence,
            scratch,
            ["/usr/bin/true"],
            runtime_root=runtime,
            runtime_base=Path.home(),
        )


def test_perimeter_discovery_works_under_hidden_snapshot_parent(
    tmp_path: Path,
) -> None:
    repository = tmp_path / ".copilot-session" / "snapshot"
    (repository / "tests/unit").mkdir(parents=True)
    (repository / "tests/support").mkdir(parents=True)
    (repository / "tests/unit/test_case.py").write_text("", encoding="utf-8")
    (repository / "tests/support/test_helper.py").write_text(
        "", encoding="utf-8"
    )
    manifest = {
        "schema_version": 1,
        "suites": [
            {
                "path": "tests/unit",
                "classification": "required",
                "reason": "synthetic perimeter fixture",
            },
            {
                "path": "tests/support",
                "classification": "support-only",
                "reason": "synthetic helper fixture",
            },
        ],
        "module_overrides": [],
    }
    manifest_path = repository / "config/test_perimeter.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    perimeter = validate_perimeter(repository, manifest_path)

    assert len(perimeter.suites) == 2
    assert len(perimeter.module_classifications) == 2


def test_result_builder_rejects_partial_trace_in_emitted_artifact(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    evidence = tmp_path / "evidence"
    repository.mkdir()
    evidence.mkdir()
    manifest = {
        "schema_version": 1,
        "suites": [
            {"path": "tests/unit", "classification": "required"},
            {"path": "tests/utils", "classification": "support-only"},
        ],
        "module_overrides": [
            {
                "path": "tests/unit/test_optional.py",
                "reason": "synthetic optional fixture",
            }
        ],
    }
    for relative in REQUIRED_INPUTS:
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        content = (
            json.dumps(manifest)
            if relative == "config/test_perimeter.json"
            else "fixture\n"
        )
        path.write_text(content, encoding="utf-8")

    subprocess.run(
        ["git", "init", "-b", "main", str(repository)],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(repository), "config", "user.name", "A-PRE fixture"],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "config",
            "user.email",
            "apre-fixture@example.invalid",
        ],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repository), "add", "-A"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-m", "synthetic fixture"],
        check=True,
        capture_output=True,
        text=True,
    )

    (evidence / "stdout.txt").write_text("synthetic gate output\n")
    (evidence / "stderr.txt").write_text("")
    (evidence / "effects.json").write_text("{}\n")
    (evidence / "syscall.trace.123").write_text("openat(...)\n")
    (evidence / "isolation.json").write_text(
        json.dumps(
            {
                "exit_code": 0,
                "trace_started": True,
                "trace_complete": False,
            }
        )
    )
    collector = {
        "collections": {
            "collected": 1,
            "passed": 1,
            "failed": 0,
            "skipped": 0,
            "collection_errors": 0,
        },
        "suites": [
            {
                "path": "tests/unit",
                "classification": "required",
                "status": "PASS",
                "collected": 1,
                "passed": 1,
                "failed": 0,
                "skipped": 0,
                "collection_errors": 0,
                "skip_reasons": [],
                "duration_seconds": 0.1,
                "warnings": [],
                "errors": [],
            },
            {
                "path": "tests/utils",
                "classification": "support-only",
                "status": "SKIP",
                "collected": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "collection_errors": 0,
                "skip_reasons": ["support-only fixture"],
                "duration_seconds": 0.0,
                "warnings": [],
                "errors": [],
            },
        ],
        "optional_modules": [
            {
                "path": "tests/unit/test_optional.py",
                "status": "SKIP",
                "reason": "synthetic optional fixture",
            }
        ],
        "warnings": [],
    }
    (evidence / "collector.json").write_text(json.dumps(collector))
    runtime_python = tmp_path / "python"
    runtime_python.write_text("#!/bin/sh\nprintf 'Python 3.10.21\\n'\n")
    runtime_python.chmod(0o755)

    tree_hash = _tree_fingerprint(repository)
    trace_path = evidence / "syscall.trace.123"
    report = build_result(
        repository,
        evidence,
        runtime_python=runtime_python,
        uv_version="0.12.20",
        command_exit_code=0,
        started_at="2026-09-30T00:00:00+00:00",
        duration_seconds=1.0,
        before_tree_hash=tree_hash,
        after_tree_hash=tree_hash,
        trace_paths=[trace_path],
    )
    assert not trace_qualification_passes(
        {
            "exit_code": 0,
            "trace_started": True,
            "trace_complete": False,
        }
    )
    result_path = evidence / "result.json"
    write_result(
        report,
        manifest,
        repository_root=repository,
        evidence_root=evidence,
        output_path=result_path,
    )

    assert report["global_status"] == "ERROR"
    assert report["exit_code"] != 0
    assert any(
        "syscall observation is incomplete" in item
        for item in report["errors"]
    )
    assert (
        verify_artifact(
            json.loads(result_path.read_text(encoding="utf-8")),
            manifest,
            repository_root=repository,
            evidence_root=evidence,
        )
        == []
    )
