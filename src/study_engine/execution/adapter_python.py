"""Python execution adapter implementation for Phase 0 Tier 0 (S6.1).

INVARIANTS:
1. Tier 0 Controlled Process: Strictly supports TIER_0; rejects higher tiers.
2. Script Snapshotting: Reads, hashes, and snapshots script before execution.
3. Directory Isolation: Script runs with cwd=scratch/workspace/; engine files
   reside in scratch/.engine/.
4. Bounded I/O: Output is capped at max_output_bytes; no memory explosion.
5. Epistemological Purity: Emits ExecutionObservation only; never
   EvidenceRecord or StudentState mutations.
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.contracts.execution import (
    ArtifactCollectionSummary,
    ExecutionObservation,
    ExecutionPlaneTier,
    ExecutionRequest,
    ExecutionResult,
    ExecutionSnapshot,
    ExecutionStatus,
    LimitEnforcementReport,
    ProcessTelemetry,
    TerminationReason,
)
from study_engine.execution.artifact_collector import (
    collect_workspace_artifacts,
)
from study_engine.execution.base import BaseExecutionAdapter
from study_engine.execution.env_sanitizer import (
    build_sanitized_environment,
)
from study_engine.execution.process_manager import (
    run_managed_process_group,
)


class PythonExecutionAdapter(BaseExecutionAdapter):
    """Tier 0 controlled Python execution adapter."""

    ADAPTER_ID = "python.adapter"
    ADAPTER_VERSION = "S6.1.0"
    SUPPORTED_CAPABILITY = "python.run_script"

    @property
    def adapter_id(self) -> str:
        return self.ADAPTER_ID

    @property
    def adapter_version(self) -> str:
        return self.ADAPTER_VERSION

    def execute(
        self, request: ExecutionRequest, workspace_root: Path
    ) -> ExecutionResult:
        """Execute Python script under strict resource bounds and snapshotting.

        Args:
            request: Authoritative ExecutionRequest.
            workspace_root: Physical path to workspace on host.

        Returns:
            ExecutionResult containing execution facts and observed artifacts.
        """
        execution_id = f"exec-{uuid.uuid4().hex[:16]}"
        t_started = datetime.now(timezone.utc)

        # 1. Tier Validation: S6.1 Tier 0 strictly rejects unsupported tiers
        if request.tier != ExecutionPlaneTier.TIER_0:
            return self._build_rejected_result(
                request=request,
                execution_id=execution_id,
                error_msg=(
                    f"Tier '{request.tier.value}' is not supported by "
                    f"PythonExecutionAdapter (TIER_0 only)."
                ),
            )

        # 2. Capability Validation
        if request.capability.capability_name != self.SUPPORTED_CAPABILITY:
            return self._build_rejected_result(
                request=request,
                execution_id=execution_id,
                error_msg=(
                    f"Capability '{request.capability.capability_name}' "
                    f"is not supported (expected "
                    f"'{self.SUPPORTED_CAPABILITY}')."
                ),
            )

        # 3. Path & Containment Validation
        policy = request.policy
        try:
            full_script_path = (
                workspace_root / request.relative_script_path
            ).resolve()
            resolved_workspace = workspace_root.resolve()
            if not str(full_script_path).startswith(str(resolved_workspace)):
                return self._build_rejected_result(
                    request=request,
                    execution_id=execution_id,
                    error_msg="Path escapes designated workspace root.",
                )
            if not full_script_path.is_file():
                return self._build_rejected_result(
                    request=request,
                    execution_id=execution_id,
                    error_msg="Script file does not exist in workspace.",
                )
        except (ValueError, OSError):
            return self._build_rejected_result(
                request=request,
                execution_id=execution_id,
                error_msg="Invalid script path resolution.",
            )

        # 4. Command line argument bounds check
        cli_args = request.cli_arguments
        if len(cli_args) > policy.max_argument_count:
            return self._build_rejected_result(
                request=request,
                execution_id=execution_id,
                error_msg="Exceeded max_argument_count limit.",
            )
        total_arg_bytes = sum(len(a.encode("utf-8")) for a in cli_args)
        if total_arg_bytes > policy.max_total_argument_bytes:
            return self._build_rejected_result(
                request=request,
                execution_id=execution_id,
                error_msg="Exceeded max_total_argument_bytes limit.",
            )
        for arg in cli_args:
            if len(arg.encode("utf-8")) > policy.max_argument_length:
                return self._build_rejected_result(
                    request=request,
                    execution_id=execution_id,
                    error_msg="Argument exceeded max_argument_length.",
                )

        # 5. Stdin bounds check
        if request.stdin_payload is not None:
            stdin_bytes = len(request.stdin_payload.encode("utf-8"))
            if stdin_bytes > policy.max_stdin_bytes:
                return self._build_rejected_result(
                    request=request,
                    execution_id=execution_id,
                    error_msg="Exceeded max_stdin_bytes limit.",
                )

        # 6. Read script, compute hash, and verify expectation
        try:
            with open(full_script_path, "rb") as f:
                script_bytes = f.read()
        except OSError:
            return self._build_rejected_result(
                request=request,
                execution_id=execution_id,
                error_msg="Failed to read script file from disk.",
            )

        effective_sha = hashlib.sha256(script_bytes).hexdigest()
        if request.expected_script_sha256 is not None:
            if request.expected_script_sha256 != effective_sha:
                return self._build_rejected_result(
                    request=request,
                    execution_id=execution_id,
                    error_msg="Script SHA-256 mismatch against expected hash.",
                )

        # 7. Create ephemeral scratch workspace
        scratch_dir = Path(tempfile.mkdtemp(prefix="s6_scratch_"))
        engine_dir = scratch_dir / ".engine"
        student_workspace_dir = scratch_dir / "workspace"
        engine_dir.mkdir(parents=True, exist_ok=True)
        student_workspace_dir.mkdir(parents=True, exist_ok=True)

        snapshot_path = engine_dir / "snapshot_script.py"
        with open(snapshot_path, "wb") as f:
            f.write(script_bytes)

        _ = ExecutionSnapshot(
            snapshot_id=f"snap-{execution_id}",
            workspace_id=request.workspace_id,
            relative_script_path=request.relative_script_path,
            effective_script_sha256=effective_sha,
            size_bytes=len(script_bytes),
            captured_at=t_started,
        )

        # 8. Build sanitized environment & command vector
        env = build_sanitized_environment(policy.env_policy)
        cmd = [sys.executable, "-u", str(snapshot_path), *cli_args]

        try:
            outcome = run_managed_process_group(
                cmd=cmd,
                cwd=str(student_workspace_dir),
                env=env,
                timeout_seconds=policy.timeout_seconds,
                max_output_bytes=policy.max_output_bytes,
                stdin_payload=request.stdin_payload,
            )

            # Collect produced artifacts from student workspace only
            collected, omitted, summary = collect_workspace_artifacts(
                workspace_dir=student_workspace_dir,
                policy=policy,
            )

            if outcome.timed_out:
                status = ExecutionStatus.TIMED_OUT
            elif outcome.exit_code == 0:
                status = ExecutionStatus.COMPLETED
            else:
                status = ExecutionStatus.FAILED_PROCESS

            telemetry = ProcessTelemetry(
                duration_ms=outcome.duration_ms,
                output_bytes_captured=outcome.streams.bytes_captured,
                output_bytes_discarded=outcome.streams.bytes_discarded,
                output_truncated=outcome.streams.truncated,
                termination_reason=outcome.termination_reason,
                limits_report=LimitEnforcementReport(
                    timeout_enforced=True,
                    output_enforced=True,
                    stdin_enforced=True,
                    artifact_size_enforced=True,
                    artifact_count_enforced=True,
                    memory_enforced=False,
                    cpu_enforced=False,
                    network_enforced=False,
                    filesystem_enforced=False,
                ),
            )

            artifact_digests = tuple(a.sha256_digest for a in collected)

            return ExecutionResult(
                request_id=request.request_id,
                execution_id=execution_id,
                status=status,
                exit_code=outcome.exit_code,
                stdout=outcome.streams.stdout,
                stderr=outcome.streams.stderr,
                duration_ms=outcome.duration_ms,
                telemetry=telemetry,
                effective_script_sha256=effective_sha,
                produced_artifacts=collected,
                produced_artifact_digests=artifact_digests,
                omitted_artifacts=omitted,
                artifact_summary=summary,
                resource_usage={
                    "duration_ms": outcome.duration_ms,
                    "exit_code": outcome.exit_code,
                },
            )
        finally:
            shutil.rmtree(scratch_dir, ignore_errors=True)

    def observe(
        self, result: ExecutionResult, tool_name: str = "python.run_script"
    ) -> ExecutionObservation:
        """Derive instrumental observation from execution result."""
        obs_id = f"obs-{result.execution_id[5:17]}"
        return ExecutionObservation(
            observation_id=obs_id,
            execution_id=result.execution_id,
            tool_name=tool_name,
            tool_version=self.adapter_version,
            request_id=result.request_id,
            status=result.status,
            exit_code=result.exit_code,
            effective_script_sha256=result.effective_script_sha256,
            telemetry=result.telemetry,
            raw_telemetry={
                "exit_code": result.exit_code,
                "duration_ms": result.duration_ms,
                "status": result.status.value,
                "termination_reason": (
                    result.telemetry.termination_reason.value
                ),
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
            produced_artifacts=result.produced_artifacts,
            produced_artifact_digests=result.produced_artifact_digests,
            artifact_summary=result.artifact_summary,
            observed_at=datetime.now(timezone.utc),
            authority_id=EpistemologicalAuthority.EXECUTION_PLANE.value,
        )

    def _build_rejected_result(
        self,
        request: ExecutionRequest,
        execution_id: str,
        error_msg: str,
    ) -> ExecutionResult:
        """Create sanitized policy-rejected ExecutionResult without running."""
        telemetry = ProcessTelemetry(
            duration_ms=0.0,
            output_bytes_captured=0,
            termination_reason=TerminationReason.POLICY_REJECTED,
        )
        return ExecutionResult(
            request_id=request.request_id,
            execution_id=execution_id,
            status=ExecutionStatus.POLICY_REJECTED,
            exit_code=-1,
            stdout="",
            stderr="",
            duration_ms=0.0,
            telemetry=telemetry,
            sanitized_engine_error=error_msg,
            produced_artifacts=(),
            produced_artifact_digests=(),
            omitted_artifacts=(),
            artifact_summary=ArtifactCollectionSummary(),
        )
