"""Execution Provenance Spine contracts for Subsystem S5.5.

Functions as an immutable cryptographic lineage graph anchor that links:
    Curriculum -> Task -> Attempt -> Execution -> Observation ->
    Artifact -> Assessment -> Evidence -> Ledger -> State

INVARIANTS:
1. Pure lineage anchor: Does not compute mastery, score rubrics, or mutate
   student state.
2. Explicit multi-specification revision tracking (roadmap, policy, gateway,
   rubric, task, evaluator).
3. Deterministic lineage verification: Verifies all required references form
   a valid provenance DAG and match expected cryptographic revisions/hashes.
"""

from datetime import datetime, timezone
import re
from typing import Optional, Tuple
from pydantic import Field, field_validator

from study_engine.contracts.base import BaseContract

_SHA256_REGEX = re.compile(r"^[0-9a-f]{64}$")


def _validate_sha256_hash(value: Optional[str], field_name: str) -> None:
    """Validate 64-character lowercase hex SHA-256 digest."""
    if value is not None and not _SHA256_REGEX.match(value):
        raise ValueError(
            f"Field '{field_name}' must be a valid 64-character hex SHA-256 "
            f"digest, got '{value}'."
        )


class SpineIdentity(BaseContract):
    """Subject and session execution identifiers."""

    student_id: str = Field(..., min_length=1)
    session_id: Optional[str] = Field(default=None, min_length=1)
    attempt_id: Optional[str] = Field(default=None, min_length=1)


class SpineCurriculum(BaseContract):
    """Curriculum and policy revision anchors."""

    curriculum_node_id: str = Field(..., min_length=1)
    roadmap_revision_id: str = Field(..., min_length=64, max_length=64)
    policy_revision_id: str = Field(..., min_length=64, max_length=64)
    gateway_id: Optional[str] = Field(default=None, min_length=1)
    gateway_revision_id: Optional[str] = Field(
        default=None, min_length=64, max_length=64
    )

    @field_validator(
        "roadmap_revision_id",
        "policy_revision_id",
        "gateway_revision_id",
    )
    @classmethod
    def validate_hashes(cls, v: Optional[str]) -> Optional[str]:
        """Verify hexadecimal format of revision hashes."""
        if v is not None and not _SHA256_REGEX.match(v):
            raise ValueError("Revision hash must be 64-char lowercase hex.")
        return v


class SpineAssessment(BaseContract):
    """Assessment, rubric, and task revision anchors."""

    rubric_id: Optional[str] = Field(default=None, min_length=1)
    rubric_revision_id: Optional[str] = Field(
        default=None, min_length=64, max_length=64
    )
    task_id: Optional[str] = Field(default=None, min_length=1)
    task_revision_id: Optional[str] = Field(
        default=None, min_length=64, max_length=64
    )
    hoare_contract_id: Optional[str] = Field(default=None, min_length=1)
    assessment_result_id: Optional[str] = Field(default=None, min_length=1)
    evidence_record_id: Optional[str] = Field(default=None, min_length=1)
    evaluator_version: Optional[str] = Field(default=None, min_length=1)

    @field_validator("rubric_revision_id", "task_revision_id")
    @classmethod
    def validate_hashes(cls, v: Optional[str]) -> Optional[str]:
        """Verify hexadecimal format of revision hashes."""
        if v is not None and not _SHA256_REGEX.match(v):
            raise ValueError("Revision hash must be 64-char lowercase hex.")
        return v


class SpineExecution(BaseContract):
    """Execution, observation, artifact, and perturbation anchors."""

    observation_ids: Tuple[str, ...] = Field(default_factory=tuple)
    artifact_digests: Tuple[str, ...] = Field(default_factory=tuple)
    perturbation_id: Optional[str] = Field(default=None, min_length=1)

    @field_validator("artifact_digests")
    @classmethod
    def validate_digests(cls, v: Tuple[str, ...]) -> Tuple[str, ...]:
        """Verify each artifact digest is a valid SHA-256 hash."""
        for digest in v:
            if not _SHA256_REGEX.match(digest):
                raise ValueError(
                    f"Artifact digest '{digest}' is not a valid SHA-256 hash."
                )
        return v


class SpineTerminalState(BaseContract):
    """Terminal state anchors linking to Evidence Ledger and Student State."""

    ledger_cutoff_hash: Optional[str] = Field(
        default=None, min_length=64, max_length=64
    )
    student_state_id: Optional[str] = Field(default=None, min_length=1)

    @field_validator("ledger_cutoff_hash")
    @classmethod
    def validate_hash(cls, v: Optional[str]) -> Optional[str]:
        """Verify hexadecimal format of ledger cutoff hash."""
        if v is not None and not _SHA256_REGEX.match(v):
            raise ValueError("Ledger cutoff hash must be 64-char hex.")
        return v


class ExecutionProvenanceSpine(BaseContract):
    """Immutable cryptographic lineage anchor connecting lifecycle stages."""

    spine_id: str = Field(..., min_length=1)
    identity: SpineIdentity
    curriculum: SpineCurriculum
    assessment: SpineAssessment
    execution: SpineExecution
    terminal_state: SpineTerminalState
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class LineageVerificationError(Exception):
    """Raised when deterministic lineage graph validation fails."""

    pass


def verify_spine_lineage(
    spine: ExecutionProvenanceSpine,
    expected_artifact_digests: Optional[Tuple[str, ...]] = None,
    expected_ledger_cutoff_hash: Optional[str] = None,
    expected_student_state_id: Optional[str] = None,
) -> bool:
    """Verify deterministically that spine forms a valid provenance DAG.

    Validates:
    1. Gateway specification completeness (gateway_id requires revision).
    2. Assessment specification completeness (task/rubric require revisions).
    3. Artifact digest matching if expected artifacts are provided.
    4. Terminal state matching against ledger cutoff and student state.

    Args:
        spine: The provenance spine record to verify.
        expected_artifact_digests: Optional expected artifact SHA-256 digests.
        expected_ledger_cutoff_hash: Optional expected ledger tip cutoff hash.
        expected_student_state_id: Optional expected student state ID.

    Returns:
        True if all provenance assertions hold.

    Raises:
        LineageVerificationError: If any provenance constraint is violated.
    """
    # 1. Gateway specification completeness
    if spine.curriculum.gateway_id is not None:
        if spine.curriculum.gateway_revision_id is None:
            raise LineageVerificationError(
                f"Gateway '{spine.curriculum.gateway_id}' referenced without "
                f"gateway_revision_id."
            )

    # 2. Task revision completeness
    if spine.assessment.task_id is not None:
        if spine.assessment.task_revision_id is None:
            raise LineageVerificationError(
                f"Task '{spine.assessment.task_id}' referenced without "
                f"task_revision_id."
            )

    # 3. Rubric revision completeness
    if spine.assessment.rubric_id is not None:
        if spine.assessment.rubric_revision_id is None:
            raise LineageVerificationError(
                f"Rubric '{spine.assessment.rubric_id}' referenced without "
                f"rubric_revision_id."
            )

    # 4. Artifact digest verification (tamper-detection)
    if expected_artifact_digests is not None:
        if sorted(spine.execution.artifact_digests) != sorted(
            expected_artifact_digests
        ):
            msg = (
                f"Artifact digest mismatch in spine '{spine.spine_id}': "
                f"recorded={spine.execution.artifact_digests}, "
                f"expected={expected_artifact_digests}."
            )
            raise LineageVerificationError(msg)

    # 5. Terminal state verification
    if expected_ledger_cutoff_hash is not None:
        if (
            spine.terminal_state.ledger_cutoff_hash
            != expected_ledger_cutoff_hash
        ):
            msg = (
                f"Ledger cutoff hash mismatch in spine '{spine.spine_id}': "
                f"recorded='{spine.terminal_state.ledger_cutoff_hash}', "
                f"expected='{expected_ledger_cutoff_hash}'."
            )
            raise LineageVerificationError(msg)

    if expected_student_state_id is not None:
        if spine.terminal_state.student_state_id != expected_student_state_id:
            msg = (
                f"Student state ID mismatch in spine '{spine.spine_id}': "
                f"recorded='{spine.terminal_state.student_state_id}', "
                f"expected='{expected_student_state_id}'."
            )
            raise LineageVerificationError(msg)

    return True
