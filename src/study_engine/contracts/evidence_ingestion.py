"""Contracts for Subsystem S5.2.A (Evidence Ingestion & Admissibility Policy).

INVARIANTS:
1. Strict separation of admissibility (ADMITTED | REJECTED) from outcome.
2. REJECTED never generates EvidenceRecord, never mutates ledger, no penalty.
3. INCONCLUSIVE is an autonomous neutral outcome (never defaults to FAIL).
4. Session validity is evaluated deterministically at assessment timestamp.
5. EvidenceIngestionResult enforces state constraints via model validator.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from pydantic import ConfigDict, Field, model_validator

from study_engine.contracts.base import BaseContract
from study_engine.contracts.spine import ExecutionProvenanceSpine
from study_engine.state.ledger_contracts import EvidenceLedgerEntry
from study_engine.state.policy_contracts import EvidenceOutcome, EvidenceRecord


class GateVerdict(str, Enum):
    """Evaluation verdict for a single sequential admissibility gate.

    SKIPPED strictly signifies unreached due to earlier gate short-circuit,
    never an optional or bypassed gate.
    """

    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"


class AdmissionDecision(str, Enum):
    """Sovereign admissibility decision rendered by S5.2.A Evidence Policy."""

    ADMITTED = "ADMITTED"
    REJECTED = "REJECTED"


class RejectionReason(str, Enum):
    """Structured taxonomy of admissibility rejection reasons."""

    CORRUPTED_ASSESSMENT_DIGEST = "CORRUPTED_ASSESSMENT_DIGEST"
    UNAUTHORIZED_ASSESSMENT_AUTHORITY = "UNAUTHORIZED_ASSESSMENT_AUTHORITY"
    SPECIFICATION_REVISION_MISMATCH = "SPECIFICATION_REVISION_MISMATCH"
    SESSION_INACTIVE_OR_EXPIRED = "SESSION_INACTIVE_OR_EXPIRED"
    STUDENT_IDENTITY_MISMATCH = "STUDENT_IDENTITY_MISMATCH"
    NODE_NOT_IN_SESSION = "NODE_NOT_IN_SESSION"
    DUPLICATE_ASSESSMENT_REPLAY = "DUPLICATE_ASSESSMENT_REPLAY"
    INCONSISTENT_ASSESSMENT_REPLAY = "INCONSISTENT_ASSESSMENT_REPLAY"
    BROKEN_PROVENANCE_CHAIN = "BROKEN_PROVENANCE_CHAIN"


class AdmissionTrace(BaseContract):
    """Deterministic audit trace of sequential admissibility gate checks."""

    model_config = ConfigDict(frozen=True)

    integrity: GateVerdict = Field(
        ..., description="Result of canonical digest and authority check"
    )
    provenance: GateVerdict = Field(
        ..., description="Result of observation references and spine check"
    )
    session: GateVerdict = Field(
        ..., description="Result of student, node, and temporal session check"
    )
    anti_replay: GateVerdict = Field(
        ..., description="Result of preflight digest replay check"
    )
    details: Dict[str, str] = Field(
        default_factory=dict,
        description="Structured key-value audit metadata for gates",
    )


class AdmissionResult(BaseContract):
    """Sovereign determination of assessment admissibility and outcome."""

    model_config = ConfigDict(frozen=True)

    decision: AdmissionDecision = Field(
        ..., description="ADMITTED or REJECTED"
    )
    outcome: Optional[EvidenceOutcome] = Field(
        default=None,
        description="Epistemological outcome if ADMITTED; None if REJECTED",
    )
    rejection_reason: Optional[RejectionReason] = Field(
        default=None,
        description="Structured rejection reason if REJECTED",
    )
    rejection_detail: Optional[str] = Field(
        default=None,
        description="Descriptive diagnostic detail explaining rejection",
    )
    admission_trace: AdmissionTrace = Field(
        ..., description="Deterministic audit trace across all 4 gates"
    )
    evaluated_at: datetime = Field(
        ..., description="UTC timestamp of admissibility determination"
    )

    @model_validator(mode="after")
    def validate_decision_consistency(self) -> "AdmissionResult":
        """Enforce strict consistency between decision, reason, and outcome."""
        if self.decision == AdmissionDecision.REJECTED:
            if self.rejection_reason is None:
                raise ValueError(
                    "rejection_reason must be provided when decision is "
                    "REJECTED"
                )
            if self.outcome is not None:
                raise ValueError(
                    "outcome must be None when decision is REJECTED"
                )
        elif self.decision == AdmissionDecision.ADMITTED:
            if self.outcome is None:
                raise ValueError(
                    "outcome must be provided when decision is ADMITTED"
                )
            if self.rejection_reason is not None:
                raise ValueError(
                    "rejection_reason must be None when decision is ADMITTED"
                )
        return self


class SessionProvenanceContext(BaseContract):
    """Immutable context binding student, session, and curricular revisions."""

    model_config = ConfigDict(frozen=True)

    student_id: str = Field(
        ..., min_length=1, description="Active student identifier"
    )
    session_id: str = Field(
        ..., min_length=1, description="Active session identifier"
    )
    resolved_target_node_id: str = Field(
        ..., min_length=1, description="Authoritative curricular target node"
    )
    requested_node_id: Optional[str] = Field(
        default=None, description="Original requested node (if different)"
    )
    roadmap_revision_id: str = Field(
        ..., min_length=64, max_length=64, description="Active roadmap"
    )
    policy_revision_id: str = Field(
        ..., min_length=64, max_length=64, description="Active policy"
    )
    expected_task_specification_sha256: Optional[str] = Field(
        default=None,
        min_length=64,
        max_length=64,
        description="Expected task specification hash",
    )
    expected_rubric_specification_sha256: Optional[str] = Field(
        default=None,
        min_length=64,
        max_length=64,
        description="Expected rubric specification hash",
    )
    session_is_active: bool = Field(
        default=True, description="Whether session is currently active"
    )
    session_started_at: datetime = Field(
        ..., description="UTC timestamp of session start"
    )
    session_expires_at: Optional[datetime] = Field(
        default=None, description="Optional UTC expiration boundary"
    )
    spine: Optional[ExecutionProvenanceSpine] = Field(
        default=None, description="Optional lineage spine DAG reference"
    )


class EvidenceIngestionResult(BaseContract):
    """Composite result of evaluation and optional ledger commitment."""

    model_config = ConfigDict(frozen=True)

    admission: AdmissionResult = Field(
        ..., description="Admissibility determination and gate trace"
    )
    evidence_record: Optional[EvidenceRecord] = Field(
        default=None,
        description="Generated EvidenceRecord if ADMITTED; None if REJECTED",
    )
    ledger_entry: Optional[EvidenceLedgerEntry] = Field(
        default=None,
        description="Committed ledger entry if persisted; None if preflight",
    )

    @model_validator(mode="after")
    def validate_ingestion_invariants(self) -> "EvidenceIngestionResult":
        """Enforce strict invariant mapping between admission and artifacts."""
        if self.admission.decision == AdmissionDecision.REJECTED:
            if self.evidence_record is not None:
                raise ValueError(
                    "evidence_record must be None when decision is REJECTED"
                )
            if self.ledger_entry is not None:
                raise ValueError(
                    "ledger_entry must be None when decision is REJECTED"
                )
        elif self.admission.decision == AdmissionDecision.ADMITTED:
            if self.evidence_record is None:
                raise ValueError(
                    "evidence_record must not be None when decision is "
                    "ADMITTED"
                )
        return self
