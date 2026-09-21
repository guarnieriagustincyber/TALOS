"""S6 Execution Plane contracts, tier matrix, and security boundaries (S6.1).

CRITICAL ARCHITECTURAL BOUNDARIES:
1. Zero SQLite Access: The execution plane has no database credentials
   or access.
2. Zero LLM Access: The execution plane has no access to LLM API keys.
3. Zero State Authority: S6 cannot directly mutate StudentState.
4. Zero Evidence Authority: S6 produces instrumental ExecutionObservations and
   ObservedArtifacts; it NEVER emits EvidenceRecord.
5. Capability-Based Execution: Execution is invoked strictly through strongly
   typed ToolCapability objects, never via raw unparsed shell strings.
6. Honest Isolation Semantics: Tier 0 provides controlled process execution,
   not an OS-level kernel sandbox.
"""

from datetime import datetime, timezone
from enum import Enum
import re
from typing import Any, Dict, Optional, Tuple
from pydantic import ConfigDict, Field, field_validator

from study_engine.contracts.base import BaseContract
from study_engine.contracts.epistemology import (
    EpistemologicalAuthority,
    EpistemologicalStage,
    validate_epistemological_authority,
)

_SHA256_REGEX = re.compile(r"^[0-9a-f]{64}$")


class ExecutionPlaneTier(str, Enum):
    """Execution sandbox isolation tiers."""

    TIER_0 = "TIER_0"  # Controlled local process (Phase 0)
    TIER_1 = "TIER_1"  # Airgapped container / OS namespace sandbox
    TIER_2 = "TIER_2"  # Virtual bridge network simulation
    TIER_3 = "TIER_3"  # Disposable VM for binary exploitation / malware
    TIER_4 = "TIER_4"  # Hardware-isolated airgapped enclave


TIER_CAPABILITIES_MATRIX: Dict[ExecutionPlaneTier, Dict[str, str]] = {
    ExecutionPlaneTier.TIER_0: {
        "filesystem": "scratch_tmp_only",
        "network": "none",
        "subprocess": "restricted_python",
        "resource_limits": "memory_512mb_cpu_1",
        "host_access": "sandboxed_process",
        "artifact_output": "stdout_and_json",
    },
    ExecutionPlaneTier.TIER_1: {
        "filesystem": "isolated_ro_mount",
        "network": "loopback_only",
        "subprocess": "allowlist_binaries",
        "resource_limits": "cgroup_hard_limits",
        "host_access": "no_host_access",
        "artifact_output": "hashed_files",
    },
    ExecutionPlaneTier.TIER_2: {
        "filesystem": "virtual_rootfs",
        "network": "virtual_bridge_no_egress",
        "subprocess": "containerized",
        "resource_limits": "cgroup_hard_limits",
        "host_access": "no_host_access",
        "artifact_output": "pcaps_and_logs",
    },
    ExecutionPlaneTier.TIER_3: {
        "filesystem": "disposable_vm_disk",
        "network": "emulated_lan_isolated",
        "subprocess": "full_guest_os",
        "resource_limits": "hypervisor_limits",
        "host_access": "hypervisor_isolated",
        "artifact_output": "memory_dumps_and_traces",
    },
    ExecutionPlaneTier.TIER_4: {
        "filesystem": "hardware_isolated",
        "network": "dedicated_airgap",
        "subprocess": "bare_metal_controlled",
        "resource_limits": "host_hardware_bounds",
        "host_access": "out_of_band_mgmt",
        "artifact_output": "forensic_disk_images",
    },
}


class NetworkPolicy(str, Enum):
    """Network egress policy for execution."""

    DISABLED = "DISABLED"
    LOOPBACK_ONLY = "LOOPBACK_ONLY"
    ALLOWLIST = "ALLOWLIST"
    UNRESTRICTED = "UNRESTRICTED"


class FilesystemPolicy(str, Enum):
    """Filesystem containment policy for execution."""

    WORKSPACE_CONTAINED = "WORKSPACE_CONTAINED"
    HOST_ACCESS_PERMITTED = "HOST_ACCESS_PERMITTED"


class ExecutionStatus(str, Enum):
    """Execution lifecycle status."""

    COMPLETED = "COMPLETED"  # Ran to normal completion without interruption
    FAILED_PROCESS = "FAILED_PROCESS"  # Non-zero exit code
    TIMED_OUT = "TIMED_OUT"  # Killed by timeout monitor
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"  # Limit hit
    ENGINE_ERROR = "ENGINE_ERROR"  # Adapter or host engine failure
    POLICY_REJECTED = "POLICY_REJECTED"  # Request violated policy/capability


class TerminationReason(str, Enum):
    """Exact operational reason for process termination."""

    NORMAL_EXIT = "NORMAL_EXIT"
    NONZERO_EXIT = "NONZERO_EXIT"
    TIMEOUT = "TIMEOUT"
    MEMORY_LIMIT = "MEMORY_LIMIT"
    OUTPUT_LIMIT = "OUTPUT_LIMIT"
    PROCESS_LIMIT = "PROCESS_LIMIT"
    POLICY_REJECTED = "POLICY_REJECTED"
    ENGINE_ERROR = "ENGINE_ERROR"


class ArtifactOmissionReason(str, Enum):
    """Reason a detected scratch file was omitted from collection."""

    EXCEEDS_SIZE_LIMIT = "EXCEEDS_SIZE_LIMIT"
    EXCEEDS_COUNT_LIMIT = "EXCEEDS_COUNT_LIMIT"
    SYMLINK_REJECTED = "SYMLINK_REJECTED"
    UNREADABLE_FILE = "UNREADABLE_FILE"


class ToolCapability(BaseContract):
    """Strongly typed execution capability specification."""

    model_config = ConfigDict(frozen=True)

    capability_name: str = Field(
        ...,
        min_length=1,
        description="Qualified capability identifier e.g. python.run_script",
    )
    supported_tiers: Tuple[ExecutionPlaneTier, ...] = Field(
        default_factory=lambda: (ExecutionPlaneTier.TIER_0,)
    )
    required_parameters: Tuple[str, ...] = Field(default_factory=tuple)
    produces_artifacts: bool = Field(default=False)


class ObservedArtifact(BaseContract):
    """Physical artifact discovered in scratch workspace post-execution.

    INVARIANT: S6 observes physical files and hashes; S6 never assigns
    pedagogical or curricular meaning.
    """

    model_config = ConfigDict(frozen=True)

    artifact_id: str = Field(..., min_length=1)
    relative_path: str = Field(..., min_length=1)
    file_size_bytes: int = Field(..., ge=0)
    sha256_digest: str = Field(..., pattern=r"^[0-9a-f]{64}$")
    mime_type: str = Field(default="application/octet-stream")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class OmittedArtifact(BaseContract):
    """Scratch file detected but omitted from collection due to policy."""

    model_config = ConfigDict(frozen=True)

    relative_path: str = Field(..., min_length=1)
    reason: ArtifactOmissionReason = Field(...)
    file_size_bytes: Optional[int] = Field(default=None, ge=0)
    details: Optional[str] = Field(default=None)


class ArtifactCollectionSummary(BaseContract):
    """Auditable summary of artifact discovery and collection."""

    model_config = ConfigDict(frozen=True)

    artifacts_discovered: int = Field(default=0, ge=0)
    artifacts_collected: int = Field(default=0, ge=0)
    artifacts_omitted: int = Field(default=0, ge=0)
    collection_truncated: bool = Field(default=False)


class LimitEnforcementReport(BaseContract):
    """Detailed report of limits actively enforced versus not available."""

    model_config = ConfigDict(frozen=True)

    timeout_enforced: bool = Field(default=True)
    memory_enforced: bool = Field(default=False)
    cpu_enforced: bool = Field(default=False)
    output_enforced: bool = Field(default=True)
    stdin_enforced: bool = Field(default=True)
    process_count_enforced: bool = Field(default=False)
    artifact_size_enforced: bool = Field(default=True)
    artifact_count_enforced: bool = Field(default=True)
    network_enforced: bool = Field(default=False)
    filesystem_enforced: bool = Field(default=False)


class ProcessTelemetry(BaseContract):
    """Detailed telemetry of process run and resource enforcement."""

    model_config = ConfigDict(frozen=True)

    duration_ms: float = Field(default=0.0, ge=0.0)
    peak_memory_mb: Optional[float] = Field(default=None, ge=0.0)
    output_bytes_captured: int = Field(default=0, ge=0)
    output_bytes_discarded: int = Field(default=0, ge=0)
    output_truncated: bool = Field(default=False)
    termination_reason: TerminationReason = Field(
        default=TerminationReason.NORMAL_EXIT
    )
    limits_report: LimitEnforcementReport = Field(
        default_factory=LimitEnforcementReport
    )
    raw_metrics: Dict[str, Any] = Field(default_factory=dict)


class EnvironmentPolicy(BaseContract):
    """Strict environment variable construction policy."""

    model_config = ConfigDict(frozen=True)

    allowed_names: Tuple[str, ...] = Field(
        default=(
            "PATH",
            "LANG",
            "LC_ALL",
            "TMPDIR",
            "SYSTEMROOT",
            "PYTHONIOENCODING",
            "PYTHONUNBUFFERED",
            "PYTHONDONTWRITEBYTECODE",
        )
    )
    forbidden_patterns: Tuple[str, ...] = Field(
        default=(
            "*KEY*",
            "*TOKEN*",
            "*SECRET*",
            "*PASSWORD*",
            "AWS_*",
            "OPENAI_*",
            "GEMINI_*",
            "ANTHROPIC_*",
        )
    )
    custom_allowlist: Dict[str, str] = Field(default_factory=dict)
    max_value_bytes: int = Field(default=4096, ge=1, le=65536)


class ExecutionPolicy(BaseContract):
    """Strict resource bounds and constraints preventing exhaustion."""

    model_config = ConfigDict(frozen=True)

    timeout_seconds: int = Field(default=30, ge=1, le=300)
    memory_limit_mb: int = Field(default=512, ge=64, le=8192)
    cpu_cores: float = Field(default=1.0, ge=0.1, le=4.0)
    network_egress: bool = Field(default=False)
    network_policy: NetworkPolicy = Field(default=NetworkPolicy.LOOPBACK_ONLY)
    filesystem_policy: FilesystemPolicy = Field(
        default=FilesystemPolicy.WORKSPACE_CONTAINED
    )

    # Resource exhaustion safety limits
    max_output_bytes: int = Field(
        default=1_048_576, ge=1024, le=10_485_760
    )  # 1MB combined
    max_stdin_bytes: int = Field(
        default=65_536, ge=0, le=1_048_576
    )  # 64KB stdin
    max_artifact_bytes: int = Field(
        default=52_428_800, ge=1024, le=524_288_000
    )  # 50MB
    max_total_artifact_bytes: int = Field(
        default=104_857_600, ge=1024, le=524_288_000
    )  # 100MB
    max_artifact_count: int = Field(default=50, ge=1, le=200)
    max_process_count: int = Field(default=10, ge=1, le=50)
    max_file_count: int = Field(default=200, ge=1, le=1000)
    max_workspace_bytes: int = Field(
        default=104_857_600, ge=1024, le=1_073_741_824
    )  # 100MB

    # Command line argument bounds
    max_argument_count: int = Field(default=50, ge=0, le=100)
    max_argument_length: int = Field(default=1024, ge=1, le=8192)
    max_total_argument_bytes: int = Field(default=16384, ge=1, le=65536)

    env_policy: EnvironmentPolicy = Field(default_factory=EnvironmentPolicy)


class ExecutionSnapshot(BaseContract):
    """Sealed snapshot of student script taken prior to execution."""

    model_config = ConfigDict(frozen=True)

    snapshot_id: str = Field(..., min_length=1)
    workspace_id: str = Field(..., min_length=1)
    relative_script_path: str = Field(..., min_length=1)
    effective_script_sha256: str = Field(..., pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(..., ge=0)
    captured_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ExecutionRequest(BaseContract):
    """Request submitted to the Execution Plane."""

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(..., min_length=1)
    capability: ToolCapability
    workspace_id: str = Field(default="default_ws", min_length=1)
    relative_script_path: str = Field(default="main.py", min_length=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    cli_arguments: Tuple[str, ...] = Field(default_factory=tuple)
    stdin_payload: Optional[str] = Field(default=None)
    expected_script_sha256: Optional[str] = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    policy: ExecutionPolicy = Field(default_factory=ExecutionPolicy)
    tier: ExecutionPlaneTier = Field(default=ExecutionPlaneTier.TIER_0)

    @field_validator("relative_script_path")
    @classmethod
    def validate_relative_path(cls, v: str) -> str:
        """Reject path traversal or absolute paths."""
        if ".." in v or v.startswith("/"):
            raise ValueError(
                f"Path '{v}' must be relative and cannot contain '..'."
            )
        return v


class ExecutionResult(BaseContract):
    """Low-level execution result produced by the adapter/sandbox."""

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(..., min_length=1)
    execution_id: str = Field(..., min_length=1)
    status: ExecutionStatus = Field(default=ExecutionStatus.COMPLETED)
    exit_code: int = Field(default=0)
    stdout: str = Field(default="")
    stderr: str = Field(default="")
    duration_ms: float = Field(default=0.0, ge=0.0)
    telemetry: ProcessTelemetry = Field(default_factory=ProcessTelemetry)
    effective_script_sha256: str = Field(
        default="0" * 64, pattern=r"^[0-9a-f]{64}$"
    )
    produced_artifacts: Tuple[ObservedArtifact, ...] = Field(
        default_factory=tuple
    )
    produced_artifact_digests: Tuple[str, ...] = Field(default_factory=tuple)
    omitted_artifacts: Tuple[OmittedArtifact, ...] = Field(
        default_factory=tuple
    )
    artifact_summary: ArtifactCollectionSummary = Field(
        default_factory=ArtifactCollectionSummary
    )
    sanitized_engine_error: Optional[str] = Field(default=None)
    resource_usage: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("produced_artifact_digests")
    @classmethod
    def validate_hashes(cls, v: Tuple[str, ...]) -> Tuple[str, ...]:
        """Validate artifact digests format."""
        for digest in v:
            if not _SHA256_REGEX.match(digest):
                raise ValueError(
                    f"Artifact digest '{digest}' is not a valid SHA-256 hash."
                )
        return v


class ExecutionObservation(BaseContract):
    """Instrumental observation emitted by S6 for assessment by S9/S10."""

    model_config = ConfigDict(frozen=True)

    observation_id: str = Field(..., min_length=1)
    execution_id: str = Field(..., min_length=1)
    tool_name: str = Field(..., min_length=1)
    tool_version: str = Field(default="S6.1.0", min_length=1)
    request_id: Optional[str] = Field(default=None)
    status: Optional[ExecutionStatus] = Field(default=None)
    exit_code: Optional[int] = Field(default=None)
    effective_script_sha256: Optional[str] = Field(
        default=None, pattern=r"^[0-9a-f]{64}$"
    )
    telemetry: Optional[ProcessTelemetry] = Field(default=None)
    raw_telemetry: Dict[str, Any] = Field(default_factory=dict)
    produced_artifacts: Tuple[ObservedArtifact, ...] = Field(
        default_factory=tuple
    )
    produced_artifact_digests: Tuple[str, ...] = Field(default_factory=tuple)
    artifact_summary: Optional[ArtifactCollectionSummary] = Field(default=None)
    execution_started_at: Optional[datetime] = Field(default=None)
    execution_finished_at: Optional[datetime] = Field(default=None)
    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    authority_id: str = Field(
        default=EpistemologicalAuthority.EXECUTION_PLANE.value,
        min_length=1,
    )

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        # Verify that S6 is authorized to emit OBSERVATION stage
        validate_epistemological_authority(
            stage=EpistemologicalStage.OBSERVATION,
            authority=EpistemologicalAuthority.EXECUTION_PLANE,
        )
