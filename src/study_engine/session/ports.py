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

    def get_receipt(self, input_id: str) -> Optional[TurnReceipt]:
        """Retrieve stored turn receipt by input_id."""
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
        self._receipts_by_input: Dict[str, TurnReceipt] = {}
        self._receipts_by_assessment: Dict[str, TurnReceipt] = {}

    def get_receipt(self, input_id: str) -> Optional[TurnReceipt]:
        """Retrieve stored turn receipt by input_id."""
        return self._receipts_by_input.get(input_id)

    def store_receipt(self, receipt: TurnReceipt) -> None:
        """Persist turn receipt in-memory."""
        self._receipts_by_input[receipt.input_id] = receipt
        if receipt.assessment_digest:
            self._receipts_by_assessment[receipt.assessment_digest] = receipt

    def find_by_assessment_digest(self, digest: str) -> Optional[TurnReceipt]:
        """Find turn receipt by canonical assessment digest."""
        return self._receipts_by_assessment.get(digest)


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

