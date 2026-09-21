"""Subsystem S5.2: Student State & Assessment Policy."""

from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import (
    DuplicateEvidenceError,
    EvidenceLedgerEntry,
    HistoryCutoffMode,
    IdempotentReplayError,
    InconsistentReplayError,
    LedgerContractError,
    LedgerIntegrityReport,
    LedgerIntegrityStatus,
    LedgerIntegrityViolationError,
    NonMonotonicCommitError,
    canonicalize_ledger_entry_payload,
    compute_ledger_entry_hash,
)
from study_engine.state.policy_contracts import (
    ActorType,
    AssessmentPolicy,
    CriteriaEvaluationResult,
    CriteriaEvaluationVerdict,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceRequirement,
    EvidenceType,
    InvalidCriteriaConfigurationError,
    NodeAssessmentCriteria,
    PolicyContractError,
    PolicyHashMismatchError,
    SovereignExemptionViolationError,
)
from study_engine.state.policy_engine import (
    compute_canonical_policy_id,
    evaluate_node_criteria,
    validate_policy_hash,
)
from study_engine.state.state_contracts import (
    NodeProgressStatus,
    NodeState,
    StateContractError,
    StateHashMismatchError,
    StudentIsolationViolationError,
    StudentState,
    canonicalize_student_state_payload,
    compute_canonical_state_id,
    validate_student_state_hash,
)
from typing import TYPE_CHECKING, Any

from study_engine.state.state_engine import derive_student_state

if TYPE_CHECKING:
    from study_engine.state.ingestion_engine import EvidenceIngestionEngine

__all__ = [
    # Policy contracts & engine
    "EvidenceType",
    "EvidenceOutcome",
    "ActorType",
    "CriteriaEvaluationVerdict",
    "EvidenceRecord",
    "EvidenceRequirement",
    "NodeAssessmentCriteria",
    "AssessmentPolicy",
    "CriteriaEvaluationResult",
    "PolicyContractError",
    "PolicyHashMismatchError",
    "SovereignExemptionViolationError",
    "InvalidCriteriaConfigurationError",
    "compute_canonical_policy_id",
    "validate_policy_hash",
    "evaluate_node_criteria",
    "EvidenceIngestionEngine",
    # Ledger contracts & engine
    "HistoryCutoffMode",
    "LedgerIntegrityStatus",
    "EvidenceLedgerEntry",
    "LedgerIntegrityReport",
    "LedgerContractError",
    "DuplicateEvidenceError",
    "InconsistentReplayError",
    "IdempotentReplayError",
    "LedgerIntegrityViolationError",
    "NonMonotonicCommitError",
    "canonicalize_ledger_entry_payload",
    "compute_ledger_entry_hash",
    "EvidenceLedger",
    # State contracts & engine
    "NodeProgressStatus",
    "NodeState",
    "StudentState",
    "StateContractError",
    "StateHashMismatchError",
    "StudentIsolationViolationError",
    "canonicalize_student_state_payload",
    "compute_canonical_state_id",
    "validate_student_state_hash",
    "derive_student_state",
]


def __getattr__(name: str) -> Any:
    if name == "EvidenceIngestionEngine":
        from study_engine.state.ingestion_engine import (
            EvidenceIngestionEngine,
        )

        return EvidenceIngestionEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
