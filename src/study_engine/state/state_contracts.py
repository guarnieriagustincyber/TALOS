"""Contracts and serialization for Subsystem S5.2.C (State Engine).

INVARIANTS:
1. Pure function determinism: same inputs -> bitwise identical StudentState.
2. Canonical state hash excludes itself, eliminating circularity.
3. NodeState sequence is immutable Tuple[NodeState, ...] sorted by node_id.
4. Intrinsic evaluation is decoupled from curricular availability (LOCKED).
5. Explicit event vs commit temporal semantics for last evidence timestamps.
6. Strict student_id isolation.
"""


from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Dict, Optional, Tuple
from pydantic import ConfigDict, Field

from study_engine.contracts.base import BaseContract
from study_engine.state.ledger_contracts import HistoryCutoffMode
from study_engine.state.policy_contracts import CriteriaEvaluationResult


class NodeProgressStatus(str, Enum):
    """Curricular availability and mastery status of a roadmap node."""

    LOCKED = "LOCKED"
    AVAILABLE = "AVAILABLE"
    IN_PROGRESS = "IN_PROGRESS"
    ASSESSED_PROFICIENT = "ASSESSED_PROFICIENT"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    EXEMPT = "EXEMPT"


class StateContractError(Exception):
    """Base exception for state contract and derivation violations."""


class StateHashMismatchError(StateContractError):
    """Raised when declared canonical_state_id does not match computed hash."""


class StudentIsolationViolationError(StateContractError):
    """Raised when evidence from an alien student leaks into student state."""


class NodeState(BaseContract):
    """Immutable state of a single curricular node for a student."""

    model_config = ConfigDict(frozen=True)

    node_id: str = Field(
        ..., min_length=1, description="Associated roadmap node ID"
    )
    status: NodeProgressStatus = Field(
        ..., description="Curricular progress status"
    )
    evaluation_result: Optional[CriteriaEvaluationResult] = Field(
        default=None,
        description="Intrinsic assessment evaluation result from S5.2.A",
    )
    unfulfilled_hard_prerequisites: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="IDs of unsatisfied HARD prerequisites causing LOCKED",
    )
    unfulfilled_soft_prerequisites: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="IDs of unsatisfied SOFT prerequisites (advisory only)",
    )
    total_evidence_count: int = Field(
        default=0, ge=0, description="Total matching evidence records"
    )
    last_event_timestamp: Optional[datetime] = Field(
        default=None,
        description="Real-world event timestamp of the latest cutoff evidence",
    )
    last_commit_timestamp: Optional[datetime] = Field(
        default=None,
        description="Ledger commit timestamp of the latest cutoff evidence",
    )


class StudentState(BaseContract):
    """Complete, immutable, cryptographically sealed student state."""

    model_config = ConfigDict(frozen=True)

    student_id: str = Field(
        ..., min_length=1, description="Student identifier"
    )
    roadmap_revision_id: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="SHA-256 revision hash of CurricularRoadmap (S5.1)",
    )
    policy_revision_id: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="SHA-256 revision hash of AssessmentPolicy (S5.2.A)",
    )
    ledger_cutoff_hash: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="SHA-256 of cutoff entry (or '0'*64 if empty)",
    )

    as_of_time: datetime = Field(
        ..., description="Temporal boundary of historical evaluation"
    )
    cutoff_mode: HistoryCutoffMode = Field(
        ..., description="Temporal cutoff mode (COMMIT_TIME vs EVENT_TIME)"
    )
    node_states: Tuple[NodeState, ...] = Field(
        default_factory=tuple,
        description="Immutable sequence of node states ordered by node_id",
    )
    canonical_state_id: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="Deterministic SHA-256 hash sealing this exact state",
    )

    def get_node_state(self, node_id: str) -> Optional[NodeState]:
        """Retrieve state for a specific node ID."""
        for ns in self.node_states:
            if ns.node_id == node_id:
                return ns
        return None

    @property
    def available_node_ids(self) -> Tuple[str, ...]:
        """Return IDs of all nodes currently AVAILABLE."""
        return tuple(
            ns.node_id
            for ns in self.node_states
            if ns.status == NodeProgressStatus.AVAILABLE
        )

    @property
    def proficient_node_ids(self) -> Tuple[str, ...]:
        """Return IDs of all nodes currently ASSESSED_PROFICIENT."""
        return tuple(
            ns.node_id
            for ns in self.node_states
            if ns.status == NodeProgressStatus.ASSESSED_PROFICIENT
        )

    @property
    def needs_review_node_ids(self) -> Tuple[str, ...]:
        """Return IDs of all nodes currently in NEEDS_REVIEW."""
        return tuple(
            ns.node_id
            for ns in self.node_states
            if ns.status == NodeProgressStatus.NEEDS_REVIEW
        )

    @property
    def locked_node_ids(self) -> Tuple[str, ...]:
        """Return IDs of all nodes currently LOCKED."""
        return tuple(
            ns.node_id
            for ns in self.node_states
            if ns.status == NodeProgressStatus.LOCKED
        )

    @property
    def exempt_node_ids(self) -> Tuple[str, ...]:
        """Return IDs of all nodes currently EXEMPT."""
        return tuple(
            ns.node_id
            for ns in self.node_states
            if ns.status == NodeProgressStatus.EXEMPT
        )

    @property
    def in_progress_node_ids(self) -> Tuple[str, ...]:
        """Return IDs of all nodes currently IN_PROGRESS."""
        return tuple(
            ns.node_id
            for ns in self.node_states
            if ns.status == NodeProgressStatus.IN_PROGRESS
        )


def _to_utc_iso(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime as UTC ISO 8601 string deterministically."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).isoformat()
    return dt.replace(tzinfo=timezone.utc).isoformat()


def canonicalize_student_state_payload(
    student_id: str,
    roadmap_revision_id: str,
    policy_revision_id: str,
    ledger_cutoff_hash: str,
    as_of_time: datetime,
    cutoff_mode: HistoryCutoffMode,
    node_states: Tuple[NodeState, ...],
) -> bytes:
    """Serialize StudentState payload excluding canonical_state_id.

    Invariants:
    - node_states sorted stably by node_id.
    - Datetimes normalized to UTC ISO 8601 strings.
    - Enums converted to .value strings.
    - Compact separators without whitespace: (',', ':').
    """
    normalized_as_of = _to_utc_iso(as_of_time)
    assert normalized_as_of is not None

    serialized_nodes = []
    # Sort node_states stably by node_id
    for ns in sorted(node_states, key=lambda n: n.node_id):
        eval_dict: Optional[Dict[str, Any]] = None
        if ns.evaluation_result:
            ev_ts_iso = _to_utc_iso(ns.evaluation_result.evaluation_timestamp)
            assert ev_ts_iso is not None
            eval_dict = {
                "criteria_id": ns.evaluation_result.criteria_id,
                "verdict": ns.evaluation_result.verdict.value,
                "satisfied_requirements": sorted(
                    ns.evaluation_result.satisfied_requirements
                ),
                "missing_requirements": sorted(
                    ns.evaluation_result.missing_requirements
                ),
                "subsequent_failures_count": (
                    ns.evaluation_result.subsequent_failures_count
                ),
                "evaluation_timestamp": ev_ts_iso,
                "rationale": ns.evaluation_result.rationale,
            }

        node_dict: Dict[str, Any] = {
            "node_id": ns.node_id,
            "status": ns.status.value,
            "evaluation_result": eval_dict,
            "unfulfilled_hard_prerequisites": sorted(
                ns.unfulfilled_hard_prerequisites
            ),
            "unfulfilled_soft_prerequisites": sorted(
                ns.unfulfilled_soft_prerequisites
            ),
            "total_evidence_count": ns.total_evidence_count,
            "last_event_timestamp": _to_utc_iso(ns.last_event_timestamp),
            "last_commit_timestamp": _to_utc_iso(ns.last_commit_timestamp),
        }
        serialized_nodes.append(node_dict)

    payload = {

        "student_id": student_id,
        "roadmap_revision_id": roadmap_revision_id,
        "policy_revision_id": policy_revision_id,
        "ledger_cutoff_hash": ledger_cutoff_hash,
        "as_of_time": normalized_as_of,
        "cutoff_mode": cutoff_mode.value,
        "node_states": serialized_nodes,
    }

    raw_json = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return raw_json.encode("utf-8")


def compute_canonical_state_id(
    student_id: str,
    roadmap_revision_id: str,
    policy_revision_id: str,
    ledger_cutoff_hash: str,
    as_of_time: datetime,
    cutoff_mode: HistoryCutoffMode,
    node_states: Tuple[NodeState, ...],
) -> str:
    """Compute SHA-256 digest of canonicalized student state payload."""
    payload_bytes = canonicalize_student_state_payload(
        student_id=student_id,
        roadmap_revision_id=roadmap_revision_id,
        policy_revision_id=policy_revision_id,
        ledger_cutoff_hash=ledger_cutoff_hash,
        as_of_time=as_of_time,
        cutoff_mode=cutoff_mode,
        node_states=node_states,
    )
    return hashlib.sha256(payload_bytes).hexdigest()


def validate_student_state_hash(state: StudentState) -> None:
    """Verify that state's declared canonical_state_id matches computed hash.

    Raises:
        StateHashMismatchError: If declared hash does not match computed hash.
    """
    computed = compute_canonical_state_id(
        student_id=state.student_id,
        roadmap_revision_id=state.roadmap_revision_id,
        policy_revision_id=state.policy_revision_id,
        ledger_cutoff_hash=state.ledger_cutoff_hash,
        as_of_time=state.as_of_time,
        cutoff_mode=state.cutoff_mode,
        node_states=state.node_states,
    )
    if state.canonical_state_id != computed:
        msg = (
            f"Tampered StudentState hash: declared "
            f"'{state.canonical_state_id}' != computed '{computed}'."
        )
        raise StateHashMismatchError(msg)
