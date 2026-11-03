"""Typed ports and protocols for Subsystem S5.3 Session Orchestrator.

Decouples operational turn coordination from concrete execution engines,
evaluators, ingestion pipelines, and receipt persistence.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from study_engine.audit.contracts import ForensicAuditReport
from study_engine.contracts.assessment import AssessmentResult
from study_engine.contracts.evidence_ingestion import (
    EvidenceIngestionResult,
    SessionProvenanceContext,
)
from study_engine.contracts.execution import ExecutionObservation
from study_engine.contracts.generation import (
    GenerationRequest,
    GenerationResponse,
)
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.curriculum.rubric_contracts import AssessmentRubric
from study_engine.curriculum.task_contracts import PracticalTaskSpecification
from study_engine.session.contracts import TurnReceipt
from study_engine.session.session_store import SessionStore
from study_engine.state.state_contracts import StudentState


@runtime_checkable
class ExecutionPort(Protocol):
    """Port for executing untrusted student scripts in sandbox (S6.1)."""

    def execute_task(
        self, task: PracticalTaskSpecification, artifact_path: str
    ) -> ExecutionObservation:
        """Execute practical task specification with student artifact."""
        ...

    def execute(
        self, script_content: str, timeout_seconds: float = 30.0
    ) -> ExecutionObservation:
        """Execute script in sandbox and capture execution observation."""
        ...


@runtime_checkable
class AssessmentPort(Protocol):
    """Port for evaluating execution observation against task rubric (S9.1)."""

    def evaluate_observation(
        self,
        observation: ExecutionObservation,
        rubric: AssessmentRubric,
        task: Optional[PracticalTaskSpecification] = None,
    ) -> AssessmentResult:
        """Evaluate observation against rubric and optional task specification."""
        ...

    def assess(
        self,
        observation: ExecutionObservation,
        task: PracticalTaskSpecification,
        rubric: AssessmentRubric,
    ) -> AssessmentResult:
        """Evaluate observation against task specification and rubric."""
        ...


@runtime_checkable
class EvidenceIngestionPort(Protocol):
    """Port for submitting AssessmentResult to S5.2.A Evidence Policy.

    NOTE: Concrete adapters encapsulate their own persistence bindings.
    """

    def ingest_assessment(
        self,
        assessment: AssessmentResult,
        context: Optional[SessionProvenanceContext] = None,
    ) -> Any:
        """Evaluate admissibility and commit to ledger if admitted."""
        ...



class TaskSpecificationProvider(Protocol):
    """Provider protocol for resolving practical task specifications."""

    def get_task_specification(
        self, task_id: str
    ) -> Optional[PracticalTaskSpecification]:
        """Return practical task specification by ID."""
        ...


class RubricSpecificationProvider(Protocol):
    """Provider protocol for resolving assessment rubric specifications."""

    def get_rubric_specification(
        self, rubric_id: str
    ) -> Optional[AssessmentRubric]:
        """Return assessment rubric specification by ID."""
        ...


class TurnReceiptStore(Protocol):
    """Durable operational idempotency receipt store."""

    def get_receipt(
        self, input_id: str, *, session_id: Optional[str] = None
    ) -> Optional[TurnReceipt]:
        """Retrieve stored turn receipt by input_id."""
        ...

    def begin_operation(
        self, session_id: str, input_id: str, request_digest: str
    ) -> tuple[str, Optional[TurnReceipt]]:
        """Atomically reserve or classify an operation identity."""
        ...

    def latest_turn_index(self, session_id: str) -> int:
        """Return the latest durably completed turn index for a session."""
        ...

    def store_receipt(self, receipt: TurnReceipt) -> None:
        """Persist turn receipt durably."""
        ...

    def find_by_assessment_digest(self, digest: str) -> Optional[TurnReceipt]:
        """Find turn receipt by canonical assessment digest."""
        ...


class InMemoryTurnReceiptStore:
    """Standard in-memory store for unit tests and ephemeral sessions."""

    def __init__(self) -> None:
        import threading

        self._lock = threading.RLock()
        self._receipts_by_input: Dict[tuple[str, str], TurnReceipt] = {}
        self._receipts_by_assessment: Dict[str, TurnReceipt] = {}
        self._in_progress: Dict[tuple[str, str], str] = {}

    def get_receipt(
        self, input_id: str, *, session_id: Optional[str] = None
    ) -> Optional[TurnReceipt]:
        """Retrieve stored turn receipt by input_id."""
        with self._lock:
            if session_id is not None:
                return self._receipts_by_input.get((session_id, input_id))
            return next(
                (receipt for (_, candidate), receipt in self._receipts_by_input.items()
                 if candidate == input_id),
                None,
            )

    def begin_operation(
        self, session_id: str, input_id: str, request_digest: str
    ) -> tuple[str, Optional[TurnReceipt]]:
        key = (session_id, input_id)
        with self._lock:
            receipt = self._receipts_by_input.get(key)
            if receipt is not None:
                if receipt.request_digest != request_digest:
                    return "CONFLICT", None
                return "REPLAY", receipt
            pending_digest = self._in_progress.get(key)
            if pending_digest is not None:
                if pending_digest != request_digest:
                    return "CONFLICT", None
                return "IN_PROGRESS", None
            self._in_progress[key] = request_digest
            return "STARTED", None

    def store_receipt(self, receipt: TurnReceipt) -> None:
        """Persist turn receipt in-memory."""
        key = (receipt.session_id, receipt.input_id)
        with self._lock:
            pending_digest = self._in_progress.get(key)
            if pending_digest is not None and pending_digest != receipt.request_digest:
                raise ValueError("Turn receipt request digest differs from its reservation.")
            self._receipts_by_input[key] = receipt
            self._in_progress.pop(key, None)
            if receipt.assessment_digest:
                self._receipts_by_assessment[receipt.assessment_digest] = receipt

    def find_by_assessment_digest(self, digest: str) -> Optional[TurnReceipt]:
        """Find turn receipt by canonical assessment digest."""
        return self._receipts_by_assessment.get(digest)

    def latest_turn_index(self, session_id: str) -> int:
        with self._lock:
            return max(
                (receipt.turn_index for (sid, _), receipt in self._receipts_by_input.items() if sid == session_id),
                default=-1,
            )


class SQLiteTurnReceiptStore:
    """Durable TurnReceipt adapter backed by the T13a SessionStore database."""

    def __init__(self, session_store: SessionStore) -> None:
        self.session_store = session_store

    def get_receipt(
        self, input_id: str, *, session_id: Optional[str] = None
    ) -> Optional[TurnReceipt]:
        if session_id is None:
            return None
        payload = self.session_store.get_turn_receipt(session_id, input_id)
        return TurnReceipt.model_validate(payload) if payload is not None else None

    def begin_operation(
        self, session_id: str, input_id: str, request_digest: str
    ) -> tuple[str, Optional[TurnReceipt]]:
        state, payload = self.session_store.begin_turn_operation(
            session_id,
            input_id,
            request_digest,
        )
        receipt = TurnReceipt.model_validate(payload) if payload is not None else None
        return state, receipt

    def store_receipt(self, receipt: TurnReceipt) -> None:
        self.session_store.complete_turn_operation(receipt.model_dump(mode="json"))

    def find_by_assessment_digest(self, digest: str) -> Optional[TurnReceipt]:
        payload = self.session_store.find_turn_receipt_by_assessment_digest(digest)
        return TurnReceipt.model_validate(payload) if payload is not None else None

    def latest_turn_index(self, session_id: str) -> int:
        return self.session_store.latest_turn_index(session_id)


@runtime_checkable
class RetrievalPort(Protocol):
    """Port for retrieving curriculum-authorized evidence candidates."""

    def retrieve_evidence(
        self,
        query: str,
        node_id: str,
        registry: Any,
        top_k: int = 5,
    ) -> List[ScoredCandidate]:
        """Retrieve candidates filtered by Epistemic Gatekeeper."""
        ...


@runtime_checkable
class TutorPort(Protocol):
    """Port for pedagogical generation and deterministic parsing."""

    def generate_tutoring(
        self,
        request: GenerationRequest,
    ) -> GenerationResponse:
        """Execute generation and certify response via GenerationOutputParser."""
        ...


@runtime_checkable
class AuditPort(Protocol):
    """Port for S4.4 forensic audit execution."""

    def audit_response(
        self,
        request: GenerationRequest,
        response: GenerationResponse,
    ) -> ForensicAuditReport:
        """Audit generation response against hermetic PackagedContext."""
        ...


@runtime_checkable
class StateReadPort(Protocol):
    """Port for projecting authoritative student state."""

    def get_student_state(
        self,
        student_id: str,
        as_of_time: Optional[datetime] = None,
    ) -> StudentState:
        """Derive or read student state as of time."""
        ...

    def get_node_state(self, node_id: str) -> Optional[Any]:
        """Read node state for a specific curricular node."""
        ...
