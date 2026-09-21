"""Contracts, models, and exceptions for Subsystem S5.3 (Session Orchestrator).

INVARIANTS:
1. Zero Autonomous Mastery Authority: Orchestrator coordinates, does not judge.
2. Inviolability of Authorized Target: resolved_target_node_id must match
   the sovereign AuthorizedSessionTarget.
3. Separation of Intent and Resolution:
   requested_node_id vs resolved_target_node_id.
4. Intermediate SessionDecision contract separates decision from execution.
5. Contractual crash recovery states via RecoveryDisposition.
6. Durable idempotency recorded via TurnReceipt and TurnReceiptStore.
7. Terminal states (COMPLETED, ABORTED, EXPIRED) are strictly immutable.
"""

from datetime import datetime
from enum import Enum
import hashlib
import json
from typing import Any, Dict, Optional, Tuple
from pydantic import ConfigDict, Field

from study_engine.contracts.base import BaseContract
from study_engine.contracts.assessment import AssessmentResult
from study_engine.contracts.evidence_ingestion import (
    AdmissionResult,
    EvidenceIngestionResult,
)
from study_engine.contracts.generation import (
    ConversationRole,
    ConversationTurn,
    GenerationMode,
)
from study_engine.contracts.tutor import PedagogicalFollowUp


def compute_canonical_sha256(contract: BaseContract) -> str:
    """Compute deterministic SHA-256 digest of contract JSON payload."""
    payload = json.dumps(
        contract.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class SessionStatus(str, Enum):
    """Lifecycle state of an instructional session FSM."""

    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    WAITING_FOR_STUDENT = "WAITING_FOR_STUDENT"
    EXECUTING = "EXECUTING"
    ASSESSING = "ASSESSING"
    INGESTING = "INGESTING"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"
    EXPIRED = "EXPIRED"

    # Deprecated transitional alias for backwards compatibility
    EVALUATING = "EVALUATING"


class StudentInputType(str, Enum):
    """Taxonomy of student inputs received by the session."""

    QUESTION = "QUESTION"
    ANSWER = "ANSWER"
    CODE_SUBMISSION = "CODE_SUBMISSION"
    EXPLANATION_REQUEST = "EXPLANATION_REQUEST"
    COMMAND = "COMMAND"
    EXTERNAL_EVIDENCE = "EXTERNAL_EVIDENCE"


class TurnActionType(str, Enum):
    """Action category determined for a session turn."""

    EXPLAIN = "EXPLAIN"
    CHALLENGE = "CHALLENGE"
    ASSESSMENT_REPORT = "ASSESSMENT_REPORT"
    ABSTENTION = "ABSTENTION"
    SESSION_TERMINATED = "SESSION_TERMINATED"


class RecoveryDisposition(str, Enum):
    """Explicit disposition for session crash recovery."""

    REPLAY_COMPLETED = "REPLAY_COMPLETED"
    RESTART_EVALUATION = "RESTART_EVALUATION"
    RETURN_TO_WAITING = "RETURN_TO_WAITING"


class TerminalAction(str, Enum):
    """Explicit terminal lifecycle directive emitted by turn decision."""

    NONE = "NONE"
    COMPLETE = "COMPLETE"
    ABORT = "ABORT"


class SessionError(Exception):
    """Base exception for session orchestration violations."""


class InvalidSessionTransitionError(SessionError):
    """Raised when an illegal FSM transition is attempted."""


class LockedNodeTargetError(SessionError):
    """Raised when attempting to focus on a LOCKED curricular node."""


class UnauthorizedTargetDeviationError(LockedNodeTargetError):
    """Raised when turn requests deviation from AuthorizedSessionTarget."""


class TurnIdConflictError(SessionError):
    """Raised when input_id reused with differing request digest."""


class SessionTerminalError(InvalidSessionTransitionError):
    """Raised when turn attempted on a terminal session."""


class SessionExpiredError(SessionError):
    """Raised when turn attempted on an expired session."""


class ReExecutionForbiddenError(SessionError):
    """Raised when recovery attempts illegal automated code re-execution."""


class AuditRejectionError(SessionError):
    """Raised when S4.4 Forensic Audit rejects generated response."""


class LedgerCommitError(SessionError):
    """Raised when ledger evidence append fails during turn processing."""


class DuplicateTurnInputError(SessionError):
    """Raised when duplicate turn input is submitted inappropriately."""


class MissingProvenanceError(SessionError, ValueError):
    """Raised when an assessment ingestion is attempted without explicit SessionProvenanceContext."""


class AuthorizedSessionTarget(BaseContract):
    """Curricular target authorized externally by S5.1 / GDA for a session."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    authorization_id: str = Field(
        ..., min_length=1, description="Unique target authorization token"
    )
    student_id: str = Field(
        ..., min_length=1, description="Authorized student identifier"
    )
    session_id: str = Field(
        ..., min_length=1, description="Authorized session identifier"
    )
    node_id: str = Field(..., min_length=1, description="Authorized target node ID")
    roadmap_revision_id: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="Roadmap revision ID this target is anchored to",
    )
    authorized_at: datetime = Field(
        ..., description="UTC timestamp when target was authorized"
    )


class TurnReceipt(BaseContract):
    """Durable operational idempotency receipt recorded for each turn."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    receipt_id: str = Field(
        ..., min_length=1, description="Unique turn receipt identifier"
    )
    input_id: str = Field(
        ..., min_length=1, description="Student input idempotency key"
    )
    session_id: str = Field(
        ..., min_length=1, description="Associated session identifier"
    )
    turn_index: int = Field(..., ge=0, description="Completed turn sequence index")
    request_digest: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="Canonical SHA-256 digest of StudentInput",
    )
    lifecycle_status: SessionStatus = Field(
        ..., description="FSM status when receipt was issued"
    )
    action_type: TurnActionType = Field(
        ..., description="Turn action category performed"
    )
    output_digest: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="Canonical SHA-256 digest of SessionTurnOutput",
    )
    execution_id: Optional[str] = Field(
        default=None, description="Lineage ID of execution observation (S6)"
    )
    assessment_digest: Optional[str] = Field(
        default=None,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="Canonical SHA-256 digest of AssessmentResult (S9/S10)",
    )
    evidence_record_id: Optional[str] = Field(
        default=None, description="Committed EvidenceRecord ID in ledger"
    )
    output_payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Serialized operational envelope for deterministic replay",
    )
    created_at: datetime = Field(
        ..., description="UTC timestamp of receipt persistence"
    )


class StudentInput(BaseContract):
    """Immutable input payload submitted by the student."""

    model_config = ConfigDict(frozen=True)

    input_id: str = Field(
        ..., min_length=1, description="Unique turn input idempotency key"
    )
    session_id: str = Field(
        ..., min_length=1, description="Associated session identifier"
    )
    turn_index: int = Field(
        ..., ge=0, description="Monotonically increasing turn sequence index"
    )
    input_type: StudentInputType = Field(..., description="Taxonomic input category")
    content: str = Field(
        ..., min_length=1, description="Raw student text, code, or command"
    )
    timestamp: datetime = Field(
        ..., description="UTC timestamp of student input submission"
    )
    requested_node_id: Optional[str] = Field(
        default=None,
        description="Optional node requested by student (intent, not auth)",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Extensible interaction telemetry"
    )


class SessionDecision(BaseContract):
    """Operational decision record for a validated turn.

    Expresses the operational decision of the Orchestrator for a validated
    turn. Does not contain rules of mastery, curricular progression, evidence
    grading, or epistemic validation (which belong to S5.1 and S5.2).
    """

    model_config = ConfigDict(frozen=True)

    decision_id: str = Field(
        ..., min_length=1, description="Unique decision record identifier"
    )
    session_id: str = Field(
        ..., min_length=1, description="Associated session identifier"
    )
    turn_index: int = Field(
        ..., ge=0, description="Target turn index for this decision"
    )
    resolved_target_node_id: str = Field(
        ..., min_length=1, description="Curricular node resolved by authority"
    )
    action_type: TurnActionType = Field(
        ..., description="Determined pedagogical action for this turn"
    )
    requires_assessment: bool = Field(
        default=False, description="Whether input requires S5.2.A evaluation"
    )
    requires_retrieval: bool = Field(
        default=False, description="Whether turn requires S3 retrieval"
    )
    requires_generation: bool = Field(
        default=False, description="Whether turn requires S4 generation"
    )
    requires_ledger_append: bool = Field(
        default=False, description="Whether turn commits new EvidenceRecord"
    )
    terminal_action: TerminalAction = Field(
        default=TerminalAction.NONE,
        description="Explicit terminal signal (NONE/COMPLETE/ABORT)",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Decision diagnostics and rationale"
    )


class SessionTurnOutput(BaseContract):
    """Immutable response payload delivered to the student after turn."""

    model_config = ConfigDict(frozen=True)

    turn_id: str = Field(
        ..., min_length=1, description="Unique turn execution identifier"
    )
    session_id: str = Field(
        ..., min_length=1, description="Associated session identifier"
    )
    turn_index: int = Field(..., ge=0, description="Completed turn sequence index")
    action_type: TurnActionType = Field(
        ..., description="Pedagogical action type performed"
    )
    resolved_target_node_id: str = Field(
        ..., min_length=1, description="Sovereignly resolved target node ID"
    )
    content: str = Field(..., min_length=1, description="User-facing response content")
    audit_report_id: Optional[str] = Field(
        default=None,
        description="S4.4 Forensic Audit Report ID (if generated)",
    )
    produced_evidence_id: Optional[str] = Field(
        default=None, description="Committed EvidenceRecord ID (if evaluated)"
    )
    student_state_id: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="Canonical SHA-256 state ID derived after this turn",
    )
    admission_result: Optional[AdmissionResult] = Field(
        default=None,
        description="Sovereign S5.2.A admission decision and trace",
    )
    ingestion_result: Optional[EvidenceIngestionResult] = Field(
        default=None,
        description="S5.2.A ingestion composite result (admission + commit)",
    )
    created_at: datetime = Field(..., description="UTC timestamp of turn completion")


class SessionResultStatus(str, Enum):
    """Taxonomía cerrada de estados de respuesta de una sesión formativa."""

    APPROVED = "APPROVED"  # Verificado por S4.4 y admitido
    ABSTAINED = "ABSTAINED"  # Sin evidencia o rechazado por S4.4 (Fail-Closed)
    FAIL_CLOSED = "FAIL_CLOSED"  # Violación de precondición o bloqueo curricular duro


class SessionRequest(BaseContract):
    """Petición formal de interacción enviada por el estudiante al orquestador."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: str = Field(..., min_length=1, description="Identificador de sesión")
    student_id: str = Field(
        ..., min_length=1, description="Identificador del estudiante"
    )
    node_id: str = Field(..., min_length=1, description="Nodo curricular foco")
    query: str = Field(..., min_length=1, description="Consulta del estudiante")
    mode: GenerationMode = Field(
        default=GenerationMode.EXPLANATION,
        description="Modo de interacción formativa solicitado",
    )
    turn_index: int = Field(default=0, ge=0, description="Índice secuencial del turno")
    history: Tuple[ConversationTurn, ...] = Field(
        default_factory=tuple,
        description="Prior conversational turns supplied as contextual dialog only.",
    )


class SessionResult(BaseContract):
    """Resultado final inmutable entregado al alumno y persistido operativamente.

    ``pedagogical_followup`` is deterministic UI metadata.  It is attached
    after the factual ``response_text`` has passed S4.4 and therefore is not
    submitted to, nor audited by, S4.4.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: str = Field(..., min_length=1, description="ID de sesión")
    turn_id: str = Field(..., min_length=1, description="ID único del turno procesado")
    node_id: str = Field(..., min_length=1, description="Nodo curricular autorizado")
    status: SessionResultStatus = Field(..., description="Veredicto final de la sesión")
    response_text: str = Field(
        ..., min_length=1, description="Texto de respuesta o aviso de abstención"
    )
    audit_report_id: Optional[str] = Field(
        default=None, description="ID del reporte de auditoría S4.4 asociado"
    )
    abstention_reason: Optional[str] = Field(
        default=None, description="Razón formal de abstención si status != APPROVED"
    )
    question_type: Optional[str] = Field(
        default=None,
        description=(
            "Routed question type (greeting, curricular, technical, meta). "
            "Single source of truth for the UI; never part of the S4.4 audit payload."
        ),
    )
    audit_trace: Dict[str, Any] = Field(
        default_factory=dict, description="Metadatos forenses inmutables del turno"
    )
    pedagogical_followup: Optional[PedagogicalFollowUp] = Field(
        default=None,
        description="Deterministic follow-up metadata; explicitly outside the S4.4 factual audit payload.",
    )


class PracticeResultStatus(str, Enum):
    """Status of a practical submission evaluation."""

    EVALUATED = "EVALUATED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    INGESTION_REJECTED = "INGESTION_REJECTED"


class PracticeRequest(BaseContract):
    """Student request submitting a practical artifact for deterministic evaluation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    student_id: str = Field(
        ..., min_length=1, description="Student submitting artifact"
    )
    node_id: str = Field(..., min_length=1, description="Curricular node identifier")
    task_id: str = Field(
        ..., min_length=1, description="Practical task specification identifier"
    )
    artifact_path: str = Field(
        ..., min_length=1, description="Path to student script/artifact"
    )
    rubric_id: Optional[str] = Field(
        default=None, description="Optional rubric identifier if distinct from task_id"
    )
    expected_sha256: Optional[str] = Field(
        default=None, description="Optional expected SHA-256 digest of artifact"
    )


class PracticeResult(BaseContract):
    """Authoritative result of an evaluated practical submission."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: PracticeResultStatus = Field(
        ..., description="High-level status of the practice submission"
    )
    assessment_summary: Dict[str, Any] = Field(
        default_factory=dict, description="Summary metrics of S9.1 assessment"
    )
    evidence_record_id: Optional[str] = Field(
        default=None, description="Admitted EvidenceRecord identifier if committed"
    )
    updated_node_status: Optional[str] = Field(
        default=None, description="Node status in student state after admission"
    )
    execution_observation: Optional[Dict[str, Any]] = Field(
        default=None, description="Serialized execution observation"
    )
    rejection_reason: Optional[str] = Field(
        default=None, description="Reason if execution or ingestion failed"
    )
    assessment_result: Optional[AssessmentResult] = Field(
        default=None, description="Authoritative S9.1 assessment result contract"
    )
    artifact_sha256: Optional[str] = Field(
        default=None, description="Pre-execution SHA-256 digest of student artifact"
    )
