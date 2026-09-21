"""Unit tests for PythonExecutionAdapter in Subsystem S6.1."""

from pathlib import Path

from study_engine.contracts.execution import (
    ExecutionPlaneTier,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionStatus,
    TerminationReason,
    ToolCapability,
)
from study_engine.execution.adapter_python import PythonExecutionAdapter


def test_python_adapter_happy_path(tmp_path: Path) -> None:
    """Verify clean execution of a student script returning exit code 0."""
    ws = tmp_path / "student_ws"
    ws.mkdir()
    script = ws / "hello.py"
    script.write_text("print('Hello from S6.1 sandbox!')\n")

    adapter = PythonExecutionAdapter()
    req = ExecutionRequest(
        request_id="req-happy",
        capability=ToolCapability(capability_name="python.run_script"),
        workspace_id="ws-alice",
        relative_script_path="hello.py",
        policy=ExecutionPolicy(timeout_seconds=5),
        tier=ExecutionPlaneTier.TIER_0,
    )

    result = adapter.execute(req, ws)
    assert result.status == ExecutionStatus.COMPLETED
    assert result.exit_code == 0
    assert "Hello from S6.1 sandbox!" in result.stdout
    assert result.stderr == ""
    assert result.telemetry.termination_reason == TerminationReason.NORMAL_EXIT
    assert len(result.effective_script_sha256) == 64

    # Derive observation
    obs = adapter.observe(result)
    assert obs.status == ExecutionStatus.COMPLETED
    assert obs.exit_code == 0
    assert obs.tool_name == "python.run_script"
    assert obs.tool_version == "S6.1.0"
    assert obs.authority_id == "S6_EXECUTION_PLANE"


def test_python_adapter_non_zero_exit(tmp_path: Path) -> None:
    """Verify script error is recorded as FAILED_PROCESS without error."""
    ws = tmp_path / "student_ws"
    ws.mkdir()
    script = ws / "fail.py"
    script.write_text(
        "import sys\nprint('Error details', file=sys.stderr)\nsys.exit(42)\n"
    )

    adapter = PythonExecutionAdapter()
    req = ExecutionRequest(
        request_id="req-fail",
        capability=ToolCapability(capability_name="python.run_script"),
        workspace_id="ws-alice",
        relative_script_path="fail.py",
    )

    result = adapter.execute(req, ws)
    assert result.status == ExecutionStatus.FAILED_PROCESS
    assert result.exit_code == 42
    assert "Error details" in result.stderr
    assert result.sanitized_engine_error is None
    assert (
        result.telemetry.termination_reason == TerminationReason.NONZERO_EXIT
    )


def test_python_adapter_stdin_payload(tmp_path: Path) -> None:
    """Verify stdin payload is passed to child script."""
    ws = tmp_path / "student_ws"
    ws.mkdir()
    script = ws / "echo_stdin.py"
    script.write_text(
        "import sys\ndata = sys.stdin.read()\nprint(f'Received: {data}')\n"
    )

    adapter = PythonExecutionAdapter()
    req = ExecutionRequest(
        request_id="req-stdin",
        capability=ToolCapability(capability_name="python.run_script"),
        workspace_id="ws-alice",
        relative_script_path="echo_stdin.py",
        stdin_payload="Payload 123",
    )

    result = adapter.execute(req, ws)
    assert result.status == ExecutionStatus.COMPLETED
    assert "Received: Payload 123" in result.stdout


def test_python_adapter_produces_artifacts(tmp_path: Path) -> None:
    """Verify script writing to cwd produces ObservedArtifact."""
    ws = tmp_path / "student_ws"
    ws.mkdir()
    script = ws / "gen_artifact.py"
    script.write_text(
        "with open('output.txt', 'w') as f:\n"
        "    f.write('Simulated Network Telemetry\\n')\n"
    )

    adapter = PythonExecutionAdapter()
    req = ExecutionRequest(
        request_id="req-art",
        capability=ToolCapability(capability_name="python.run_script"),
        workspace_id="ws-alice",
        relative_script_path="gen_artifact.py",
    )

    result = adapter.execute(req, ws)
    assert result.status == ExecutionStatus.COMPLETED
    assert len(result.produced_artifacts) == 1
    art = result.produced_artifacts[0]
    assert art.relative_path == "output.txt"
    assert len(art.sha256_digest) == 64


def test_python_adapter_unsupported_tier_rejection(tmp_path: Path) -> None:
    """Verify request for TIER_1 is rejected by Tier 0 adapter."""
    ws = tmp_path / "student_ws"
    ws.mkdir()
    script = ws / "code.py"
    script.write_text("print('test')\n")

    adapter = PythonExecutionAdapter()
    req = ExecutionRequest(
        request_id="req-tier1",
        capability=ToolCapability(capability_name="python.run_script"),
        workspace_id="ws-alice",
        relative_script_path="code.py",
        tier=ExecutionPlaneTier.TIER_1,  # Unsupported by T0 adapter!
    )

    result = adapter.execute(req, ws)
    assert result.status == ExecutionStatus.POLICY_REJECTED
    assert result.exit_code == -1
    assert "TIER_0 only" in (result.sanitized_engine_error or "")
