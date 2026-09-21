"""Subsystem S5.3: Session Orchestrator."""

from study_engine.session.contracts import (
    AuditRejectionError,
    AuthorizedSessionTarget,
    compute_canonical_sha256,
    DuplicateTurnInputError,
    InvalidSessionTransitionError,
    LedgerCommitError,
    LockedNodeTargetError,
    ReExecutionForbiddenError,
    RecoveryDisposition,
    SessionDecision,
    SessionError,
    SessionExpiredError,
    SessionStatus,
    SessionTerminalError,
    SessionTurnOutput,
    StudentInput,
    StudentInputType,
    TerminalAction,
    TurnActionType,
    TurnIdConflictError,
    TurnReceipt,
    UnauthorizedTargetDeviationError,
)
from study_engine.session.fsm import SessionFSM
from study_engine.session.orchestrator import SessionOrchestrator
from study_engine.session.ports import (
    AssessmentPort,
    EvidenceIngestionPort,
    ExecutionPort,
    InMemoryTurnReceiptStore,
    RubricSpecificationProvider,
    TaskSpecificationProvider,
    TurnReceiptStore,
)

__all__ = [
    # Enums
    "SessionStatus",
    "StudentInputType",
    "TurnActionType",
    "RecoveryDisposition",
    "TerminalAction",
    # Contracts & Models
    "AuthorizedSessionTarget",
    "TurnReceipt",
    "StudentInput",
    "SessionDecision",
    "SessionTurnOutput",
    "compute_canonical_sha256",
    # FSM
    "SessionFSM",
    # Orchestrator
    "SessionOrchestrator",
    # Ports
    "ExecutionPort",
    "AssessmentPort",
    "EvidenceIngestionPort",
    "TaskSpecificationProvider",
    "RubricSpecificationProvider",
    "TurnReceiptStore",
    "InMemoryTurnReceiptStore",
    # Exceptions
    "SessionError",
    "InvalidSessionTransitionError",
    "LockedNodeTargetError",
    "UnauthorizedTargetDeviationError",
    "TurnIdConflictError",
    "SessionTerminalError",
    "SessionExpiredError",
    "ReExecutionForbiddenError",
    "AuditRejectionError",
    "LedgerCommitError",
    "DuplicateTurnInputError",
]
