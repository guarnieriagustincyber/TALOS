"""Contract tests for Subsystem S6.1 Execution Plane Contracts."""

import pytest
from pydantic import ValidationError

from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.contracts.execution import (
    ArtifactCollectionSummary,
    ArtifactOmissionReason,
    EnvironmentPolicy,
    ExecutionObservation,
    ExecutionPlaneTier,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionResult,
    ExecutionSnapshot,
    ExecutionStatus,
    FilesystemPolicy,
    LimitEnforcementReport,
    NetworkPolicy,
    ObservedArtifact,
    OmittedArtifact,
    ProcessTelemetry,
    TerminationReason,
    ToolCapability,
)


def test_tool_capability_contracts() -> None:
    """Verify ToolCapability immutability and default tiers."""
    cap = ToolCapability(
        capability_name="python.run_script",
        supported_tiers=(ExecutionPlaneTier.TIER_0,),
        required_parameters=("script_path",),
        produces_artifacts=True,
    )
    assert cap.capability_name == "python.run_script"
    assert cap.supported_tiers == (ExecutionPlaneTier.TIER_0,)
    assert cap.produces_artifacts is True

    with pytest.raises(ValidationError):
        # Frozen contract
        setattr(cap, "capability_name", "other")


def test_observed_artifact_contract() -> None:
    """Verify ObservedArtifact fields and SHA-256 validation."""
    valid_sha = "a" * 64
    art = ObservedArtifact(
        artifact_id="art-01",
        relative_path="output/results.pcap",
        file_size_bytes=1024,
        sha256_digest=valid_sha,
        mime_type="application/vnd.tcpdump.pcap",
    )
    assert art.artifact_id == "art-01"
    assert art.relative_path == "output/results.pcap"
    assert art.file_size_bytes == 1024
    assert art.sha256_digest == valid_sha

    # Invalid SHA-256
    with pytest.raises(ValidationError):
        ObservedArtifact(
            artifact_id="art-02",
            relative_path="bad.txt",
            file_size_bytes=10,
            sha256_digest="invalid-sha",
        )


def test_omitted_artifact_contract() -> None:
    """Verify OmittedArtifact records reason and size."""
    omitted = OmittedArtifact(
        relative_path="huge.bin",
        reason=ArtifactOmissionReason.EXCEEDS_SIZE_LIMIT,
        file_size_bytes=60_000_000,
        details="File exceeded 50MB limit",
    )
    assert omitted.reason == ArtifactOmissionReason.EXCEEDS_SIZE_LIMIT
    assert omitted.file_size_bytes == 60_000_000


def test_execution_snapshot_contract() -> None:
    """Verify ExecutionSnapshot stores sealed script state."""
    snap = ExecutionSnapshot(
        snapshot_id="snap-01",
        workspace_id="ws-alice",
        relative_script_path="labs/tcp_client.py",
        effective_script_sha256="b" * 64,
        size_bytes=420,
    )
    assert snap.snapshot_id == "snap-01"
    assert snap.workspace_id == "ws-alice"
    assert snap.effective_script_sha256 == "b" * 64
    assert snap.size_bytes == 420


def test_execution_request_path_traversal_rejection() -> None:
    """Verify ExecutionRequest rejects parent traversal or absolute paths."""
    cap = ToolCapability(capability_name="python.run_script")

    # Valid relative path
    req = ExecutionRequest(
        request_id="req-01",
        capability=cap,
        workspace_id="ws-01",
        relative_script_path="client.py",
    )
    assert req.relative_script_path == "client.py"

    # Traversal rejected
    with pytest.raises(ValidationError, match="cannot contain '..'"):
        ExecutionRequest(
            request_id="req-02",
            capability=cap,
            workspace_id="ws-01",
            relative_script_path="../../etc/passwd",
        )

    # Absolute path rejected
    with pytest.raises(ValidationError, match="must be relative"):
        ExecutionRequest(
            request_id="req-03",
            capability=cap,
            workspace_id="ws-01",
            relative_script_path="/home/user/script.py",
        )


def test_environment_policy_allowlist() -> None:
    """Verify EnvironmentPolicy provides default safe allowlist."""
    env_pol = EnvironmentPolicy()
    assert "PATH" in env_pol.allowed_names
    assert "LANG" in env_pol.allowed_names
    assert "*KEY*" in env_pol.forbidden_patterns
    assert "*TOKEN*" in env_pol.forbidden_patterns


def test_execution_policy_defaults() -> None:
    """Verify ExecutionPolicy resource bounds and honest policies."""
    pol = ExecutionPolicy()
    assert pol.timeout_seconds == 30
    assert pol.memory_limit_mb == 512
    assert pol.max_output_bytes == 1_048_576
    assert pol.max_stdin_bytes == 65_536
    assert pol.max_artifact_bytes == 52_428_800
    assert pol.network_policy == NetworkPolicy.LOOPBACK_ONLY
    assert pol.filesystem_policy == FilesystemPolicy.WORKSPACE_CONTAINED


def test_limit_enforcement_report() -> None:
    """Verify LimitEnforcementReport accurately reports capabilities."""
    report = LimitEnforcementReport(
        timeout_enforced=True,
        memory_enforced=False,
        cpu_enforced=False,
        output_enforced=True,
        stdin_enforced=True,
        process_count_enforced=False,
        artifact_size_enforced=True,
        artifact_count_enforced=True,
        network_enforced=False,
        filesystem_enforced=False,
    )
    assert report.timeout_enforced is True
    assert report.cpu_enforced is False
    assert report.network_enforced is False


def test_execution_result_contract() -> None:
    """Verify ExecutionResult encapsulates complete physical run facts."""
    res = ExecutionResult(
        request_id="req-01",
        execution_id="exec-01",
        status=ExecutionStatus.COMPLETED,
        exit_code=0,
        stdout="Hello World\n",
        stderr="",
        duration_ms=45.2,
        telemetry=ProcessTelemetry(
            duration_ms=45.2,
            output_bytes_captured=12,
            termination_reason=TerminationReason.NORMAL_EXIT,
        ),
        effective_script_sha256="c" * 64,
        produced_artifacts=(),
        artifact_summary=ArtifactCollectionSummary(
            artifacts_discovered=0,
            artifacts_collected=0,
            artifacts_omitted=0,
        ),
    )
    assert res.status == ExecutionStatus.COMPLETED
    assert res.exit_code == 0
    assert res.stdout == "Hello World\n"
    assert res.telemetry.termination_reason == TerminationReason.NORMAL_EXIT


def test_execution_observation_authority() -> None:
    """Verify ExecutionObservation enforces S6_EXECUTION_PLANE authority."""
    obs = ExecutionObservation(
        observation_id="obs-01",
        execution_id="exec-01",
        tool_name="python.run_script",
        tool_version="S6.1.0",
        request_id="req-01",
        status=ExecutionStatus.COMPLETED,
        exit_code=0,
        effective_script_sha256="d" * 64,
    )
    assert obs.authority_id == EpistemologicalAuthority.EXECUTION_PLANE.value
    assert obs.tool_version == "S6.1.0"
