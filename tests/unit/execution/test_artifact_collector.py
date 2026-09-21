"""Unit tests for artifact discovery and policy limits in S6.1."""

import hashlib
from pathlib import Path

from study_engine.contracts.execution import (
    ArtifactOmissionReason,
    ExecutionPolicy,
)
from study_engine.execution.artifact_collector import (
    collect_workspace_artifacts,
)


def test_collect_workspace_artifacts_empty(tmp_path: Path) -> None:
    """Verify empty directory returns empty collection."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    policy = ExecutionPolicy()
    collected, omitted, summary = collect_workspace_artifacts(ws, policy)
    assert collected == ()
    assert omitted == ()
    assert summary.artifacts_discovered == 0


def test_collect_workspace_artifacts_valid_files(tmp_path: Path) -> None:
    """Verify normal files are hashed and returned with SHA-256."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    f1 = ws / "report.txt"
    f1.write_text("TCP Handshake Analysis\n")
    f2 = ws / "data.pcap"
    f2.write_bytes(b"\xd4\xc3\xb2\xa1" + b"\x00" * 20)

    policy = ExecutionPolicy()
    collected, omitted, summary = collect_workspace_artifacts(ws, policy)

    assert len(collected) == 2
    assert omitted == ()
    assert summary.artifacts_collected == 2
    assert summary.collection_truncated is False

    # Check hashes
    f1_hash = hashlib.sha256(b"TCP Handshake Analysis\n").hexdigest()
    assert any(a.sha256_digest == f1_hash for a in collected)


def test_collect_workspace_artifacts_symlink_rejection(
    tmp_path: Path,
) -> None:
    """Verify symlinks are strictly rejected and recorded as omitted."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    target_secret = tmp_path / "host_secrets.txt"
    target_secret.write_text("super_secret_host_data")

    # Student code created a symlink to host file
    symlink_file = ws / "symlink_leak.txt"
    symlink_file.symlink_to(target_secret)

    policy = ExecutionPolicy()
    collected, omitted, summary = collect_workspace_artifacts(ws, policy)

    assert len(collected) == 0
    assert len(omitted) == 1
    assert omitted[0].reason == ArtifactOmissionReason.SYMLINK_REJECTED
    assert summary.artifacts_omitted == 1


def test_collect_workspace_artifacts_size_limit(tmp_path: Path) -> None:
    """Verify files exceeding max_artifact_bytes are omitted."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    huge_file = ws / "huge.bin"
    huge_file.write_bytes(b"0" * 2048)  # 2KB

    # Limit set to 1KB
    policy = ExecutionPolicy(max_artifact_bytes=1024)
    collected, omitted, summary = collect_workspace_artifacts(ws, policy)

    assert len(collected) == 0
    assert len(omitted) == 1
    assert omitted[0].reason == ArtifactOmissionReason.EXCEEDS_SIZE_LIMIT
    assert summary.artifacts_omitted == 1


def test_collect_workspace_artifacts_count_limit(tmp_path: Path) -> None:
    """Verify artifact discovery caps at max_artifact_count."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    for i in range(5):
        (ws / f"file_{i}.txt").write_text(f"content {i}")

    # Limit set to 3
    policy = ExecutionPolicy(max_artifact_count=3)
    collected, omitted, summary = collect_workspace_artifacts(ws, policy)

    assert len(collected) == 3
    assert len(omitted) == 2
    assert summary.artifacts_discovered == 5
    assert summary.artifacts_collected == 3
    assert summary.artifacts_omitted == 2
    assert summary.collection_truncated is True
