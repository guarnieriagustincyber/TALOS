"""STEP-14 focal contract: supervisor-side Git sterility observation.

The observation runs host-side only; the sandboxed worker keeps no access to
``.git``.  Every test uses a throwaway repository under pytest's temporary
directory and never mutates the real checkout.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.quality_gate import (
    GIT_OBSERVATION_FILE,
    GitObservationError,
    GitSterilityViolation,
    build_signed_git_observation,
    capture_git_observation,
    load_delivered_git_observation,
    verify_git_observation_pair,
    verify_signed_git_observation,
)
from study_engine.diagnostics import test_isolation_snapshots as snapshots

RUN = "step14-test-run"
GATE = "step14-test-gate"
TOKEN = "step14-run-token"
B1R_NODEID = (
    "tests/audit/test_b1_route_repeatability.py::"
    "test_synthetic_chat_route_is_repeatable_and_sterile"
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _temp_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.email=step14@example.invalid",
            "-c",
            "user.name=step14",
            "commit",
            "--allow-empty",
            "-m",
            "init",
            "-q",
        ],
        check=True,
    )
    return repo


def _observation(repo: Path, phase: str, *, run_identity: str = RUN):
    return capture_git_observation(
        repo,
        run_identity=run_identity,
        gate_identity=GATE,
        run_token=TOKEN,
        phase=phase,
    )


def _clean_environment(**overrides: str) -> dict[str, str]:
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("TALOS_", "PYTEST_"))
    }
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment.update(overrides)
    return environment


def _run_b1r(environment: dict[str, str], tmp_path: Path):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            B1R_NODEID,
            "-q",
            "-p",
            "no:cacheprovider",
            "--basetemp",
            str(tmp_path / "basetemp"),
        ],
        cwd=str(REPOSITORY_ROOT),
        env=environment,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


def test_s14_01_valid_observation_brackets_an_unchanged_checkout(tmp_path):
    repo = _temp_repo(tmp_path)
    pre = _observation(repo, "pre")
    post = _observation(repo, "post")
    verify_git_observation_pair(
        pre, post, run_identity=RUN, gate_identity=GATE
    )
    secret = b"step14-authority-secret"
    signed = build_signed_git_observation(pre, secret)
    assert verify_signed_git_observation(signed, secret) == pre


def test_s14_02_real_changes_are_detected(tmp_path):
    repo = _temp_repo(tmp_path)
    pre = _observation(repo, "pre")
    (repo / "leak.txt").write_text("untracked mutation")
    post = _observation(repo, "post")
    with pytest.raises(GitSterilityViolation):
        verify_git_observation_pair(
            pre, post, run_identity=RUN, gate_identity=GATE
        )
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.email=step14@example.invalid",
            "-c",
            "user.name=step14",
            "commit",
            "--allow-empty",
            "-m",
            "second",
            "-q",
        ],
        check=True,
    )
    moved = _observation(repo, "post")
    with pytest.raises(GitSterilityViolation):
        verify_git_observation_pair(
            pre, moved, run_identity=RUN, gate_identity=GATE
        )


def test_s14_03_foreign_identity_is_rejected(tmp_path):
    repo = _temp_repo(tmp_path)
    foreign = _observation(repo, "pre", run_identity="another-gate-run")
    post = _observation(repo, "post")
    with pytest.raises(GitObservationError):
        verify_git_observation_pair(
            foreign, post, run_identity=RUN, gate_identity=GATE
        )
    with pytest.raises(GitObservationError):
        verify_git_observation_pair(
            post, _observation(repo, "post"),
            run_identity=RUN, gate_identity=GATE,
        )
    # Worker side: a delivered observation from another run fails the test.
    envelope = tmp_path / "observation.json"
    envelope.write_text(
        json.dumps(build_signed_git_observation(foreign, b"any-secret"))
        + "\n"
    )
    completed = _run_b1r(
        _clean_environment(
            TALOS_TEST_ISOLATED="1",
            TALOS_QUALITY_GATE_GIT_OBSERVATION=str(envelope),
            TALOS_TEST_RUN_ID=RUN,
            TALOS_TEST_GATE_ID=GATE,
            TALOS_QUALITY_GATE_START_TOKEN=TOKEN,
        ),
        tmp_path,
    )
    assert completed.returncode != 0
    assert "does not match this run" in completed.stdout + completed.stderr


def test_s14_04_missing_observation_fails_closed(tmp_path):
    # Supervisor side: an unreadable delivered file is fatal.
    with pytest.raises(GitObservationError):
        load_delivered_git_observation(
            tmp_path / "absent.json",
            secret=b"step14-authority-secret",
            expected_pre_record={"schema_version": 1},
        )
    # Worker side: a gate sandbox without a supervisor observation fails.
    completed = _run_b1r(
        _clean_environment(TALOS_TEST_ISOLATED="1"),
        tmp_path,
    )
    assert completed.returncode != 0
    assert "without a supervisor Git observation" in (
        completed.stdout + completed.stderr
    )


def test_s14_05_tampered_observations_are_rejected(tmp_path):
    repo = _temp_repo(tmp_path)
    secret = b"step14-authority-secret"
    record = _observation(repo, "pre")
    signed = build_signed_git_observation(record, secret)
    altered = {**record, "porcelain": "M  forged-status\n"}
    with pytest.raises(GitObservationError):
        verify_signed_git_observation(
            {"record": altered, "hmac_sha256": signed["hmac_sha256"]},
            secret,
        )
    with pytest.raises(GitObservationError):
        verify_signed_git_observation(
            build_signed_git_observation(record, b"worker-key"), secret
        )
    delivered = tmp_path / GIT_OBSERVATION_FILE
    delivered.write_text(json.dumps(signed) + "\n")
    assert (
        load_delivered_git_observation(
            delivered, secret=secret, expected_pre_record=record
        )
        == record
    )
    # A worker that deletes, corrupts, or replaces the file is detected.
    delivered.write_text("{not-json")
    with pytest.raises(GitObservationError):
        load_delivered_git_observation(
            delivered, secret=secret, expected_pre_record=record
        )
    delivered.write_text(
        json.dumps(build_signed_git_observation(record, b"worker-key"))
        + "\n"
    )
    with pytest.raises(GitObservationError):
        load_delivered_git_observation(
            delivered, secret=secret, expected_pre_record=record
        )
    other = _observation(repo, "pre")
    delivered.write_text(
        json.dumps(build_signed_git_observation(other, secret)) + "\n"
    )
    with pytest.raises(GitObservationError):
        load_delivered_git_observation(
            delivered, secret=secret, expected_pre_record=record
        )


def test_s14_06_sandbox_keeps_git_masked(tmp_path, monkeypatch):
    """The worker still runs without `.git`; STEP-14 adds no writable mount."""
    import scripts.quality_gate_isolation as isolation

    repo = _temp_repo(tmp_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    captured: dict[str, list[str]] = {}

    def fake_run(arguments, **kwargs):
        captured["arguments"] = list(arguments)
        return subprocess.CompletedProcess(arguments, 0, "", "")

    monkeypatch.setattr(isolation.shutil, "which", lambda _: "/usr/bin/bwrap")
    monkeypatch.setattr(isolation.subprocess, "run", fake_run)
    isolation.run_isolated_process(
        repo,
        workspace,
        ["/usr/bin/python3", "-c", "pass"],
        environment={
            "TALOS_QUALITY_GATE_GIT_OBSERVATION": "/workspace/run/"
            "git-observation.json"
        },
        python_executable="/usr/bin/python3",
    )
    arguments = captured["arguments"]
    # The repository itself stays read-only.
    repository_mount = arguments.index("/workspace/repository")
    assert arguments[repository_mount - 1] == str(repo)
    assert arguments[repository_mount - 2] == "--ro-bind"
    # `.git` is masked by an empty read-only directory, never the real one.
    git_mask = arguments.index("/workspace/repository/.git")
    assert arguments[git_mask - 2] == "--ro-bind"
    assert Path(arguments[git_mask - 1]).resolve() != (repo / ".git").resolve()
    # No writable mount reaches the repository or `.git`.
    for index, flag in enumerate(arguments):
        if flag == "--bind":
            destination = Path(arguments[index + 2])
            assert not destination.is_relative_to("/workspace/repository")
    # The observation channel is delivered as an environment variable only.
    observation = arguments.index("TALOS_QUALITY_GATE_GIT_OBSERVATION")
    assert arguments[observation - 1] == "--setenv"
    assert (
        arguments[observation + 1]
        == "/workspace/run/git-observation.json"
    )


def test_s14_07_gate_contracts_still_reject_invalid_inputs(tmp_path):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    (snapshot / "manifest.json").write_text("{}")
    with pytest.raises(snapshots.TestSnapshotError):
        snapshots.verify_sealed_snapshot(snapshot, "sha256:" + "0" * 64)
    plain = tmp_path / "plain"
    plain.mkdir()
    with pytest.raises(GitObservationError):
        capture_git_observation(
            plain,
            run_identity=RUN,
            gate_identity=GATE,
            run_token=TOKEN,
            phase="pre",
        )
    with pytest.raises(GitObservationError):
        capture_git_observation(
            _temp_repo(tmp_path),
            run_identity=RUN,
            gate_identity=GATE,
            run_token=TOKEN,
            phase="unknown-phase",
        )
