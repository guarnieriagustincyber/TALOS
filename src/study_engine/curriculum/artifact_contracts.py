"""Artifact and forensic provenance contracts for Subsystem S5.4.

INVARIANTS:
1. ArtifactRecord != EvidenceRecord (HG-S5.4-02).
   An artifact is an observable object with forensic integrity.
   It contains ZERO curricular competence judgements or mastery claims.
2. Separation of Operational UUID vs Cryptographic SHA-256 (R1.6):
   - artifact_id: Operational tracking identifier.
   - sha256: Cryptographic digest of actual file/data bytes.
   - canonical_content_id: Optional deterministic identifier.
3. All models are strictly immutable (frozen=True, extra="forbid").
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple
from pydantic import ConfigDict, Field

from study_engine.contracts.base import BaseContract


class ArtifactType(str, Enum):
    """Taxonomy of observable artifacts generated in practical tasks."""

    PCAP_CAPTURE = "pcap_capture"
    MEMORY_DUMP = "memory_dump"
    LOG_BUNDLE = "log_bundle"
    SOURCE_CODE = "source_code"
    BINARY_EXECUTABLE = "binary_executable"
    YARA_RULE = "yara_rule"
    SIGMA_RULE = "sigma_rule"
    FORENSIC_TIMELINE = "forensic_timeline"
    SECURITY_REPORT = "security_report"
    CONFIGURATION_FILE = "configuration_file"
    TEST_REPORT = "test_report"


class ArtifactProvenance(BaseContract):
    """Forensic provenance metadata recording artifact generation context."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_lab_id: str = Field(
        ..., min_length=1, description="Laboratory environment identifier"
    )
    tool_name: str = Field(
        ..., min_length=1, description="Tool used (e.g. Wireshark, Volatility)"
    )
    tool_version: Optional[str] = Field(
        default=None, description="Exact tool version string"
    )
    execution_environment_hash: Optional[str] = Field(
        default=None, description="Environment digest or container image hash"
    )
    captured_at: datetime = Field(
        ..., description="Timestamp when artifact was generated"
    )
    operator_id: Optional[str] = Field(
        default=None, description="Operator identifier"
    )


class ArtifactRecord(BaseContract):
    """Observable physical artifact generated in a laboratory session.

    INVARIANTS:
    - Possesses zero competency attributes or mastery levels.
    - artifact_id tracks execution; sha256 provides cryptographic integrity.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    artifact_id: str = Field(
        ..., min_length=1, description="Unique operational instance identifier"
    )
    sha256: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="Immutable 64-char lowercase hexadecimal SHA-256 digest",
    )
    canonical_content_id: Optional[str] = Field(
        default=None, description="Optional deterministic canonical ID"
    )
    artifact_type: ArtifactType = Field(
        ..., description="Type category of artifact"
    )
    filename: str = Field(
        ..., min_length=1, description="Artifact base filename"
    )
    size_bytes: int = Field(
        ..., ge=0, description="Content size in bytes"
    )
    mime_type: str = Field(
        ..., min_length=1, description="MIME format (e.g. application/pcap)"
    )
    provenance: ArtifactProvenance = Field(
        ..., description="Cryptographic and contextual provenance"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Custom laboratory metadata"
    )


class ArtifactRequirement(BaseContract):
    """Declarative specification of expected artifacts for a task/gateway."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    requirement_id: str = Field(
        ..., min_length=1, description="Unique requirement identifier"
    )
    artifact_type: ArtifactType = Field(
        ..., description="Required artifact category"
    )
    min_size_bytes: int = Field(
        default=0, ge=0, description="Minimum acceptable payload size"
    )
    max_size_bytes: Optional[int] = Field(
        default=None, gt=0, description="Optional maximum size boundary"
    )
    expected_mime_types: Tuple[str, ...] = Field(
        ..., min_length=1, description="Allowable MIME types"
    )
    required_provenance_tools: Tuple[str, ...] = Field(
        default_factory=tuple, description="Required generation tools"
    )
    description: str = Field(
        ..., min_length=1, description="Description of required artifact"
    )
