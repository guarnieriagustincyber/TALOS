"""Infrastructure adapters implementing session ports (Hito 3).

Decouples SessionOrchestrator from concrete retrieval, generation, and
S4.4 forensic auditor implementations while strictly protecting frozen perimeters.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.contracts import (
    AuditVerdict,
    CheckSeverity,
    CheckStatus,
    DeterministicAuditCheck,
    ForensicAuditInput,
    ForensicAuditReport,
)
from study_engine.contracts.generation import (
    GenerationMode,
    GenerationRequest,
    GenerationResponse,
)
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.generation.tutor import StructuredTutor
from study_engine.retrieval.service import RetrievalService
from study_engine.session.ports import (
    AuditPort,
    RetrievalPort,
    TutorPort,
)


class ForensicAuditAdapter(AuditPort):
    """Translation layer adapter wrapping S4.4 ForensicAuditor without mutating it."""

    def __init__(
        self,
        auditor: Optional[ForensicAuditor] = None,
        active_budget_limit: Optional[int] = None,
    ) -> None:
        self._auditor = auditor or ForensicAuditor()
        self.active_budget_limit = active_budget_limit

    def audit_response(
        self,
        request: GenerationRequest,
        response: GenerationResponse,
    ) -> ForensicAuditReport:
        """Construct ForensicAuditInput and execute S4.4 audit with TUT-06 budget check."""
        # 1. Check budget containment (TUT-06 / Refinement 2)
        limit = self.active_budget_limit
        completion_tokens = (
            response.tokens_used.completion_tokens
            if response.tokens_used and response.tokens_used.completion_tokens is not None
            else len(response.text.split())
        )
        if limit is not None and completion_tokens > limit:
            budget_check = DeterministicAuditCheck(
                check_id="CHECK_BUDGET_CONTAINMENT",
                status=CheckStatus.FAIL,
                severity=CheckSeverity.CRITICAL,
                reason=(
                    f"BUDGET_VIOLATION: generated tokens ({completion_tokens}) "
                    f"exceed configured budget ({limit})."
                ),
            )
            return ForensicAuditReport(
                audit_id=f"audit-budget-fail-{request.request_id[:8]}",
                request_id=request.request_id,
                notebook_id=request.notebook_id,
                overall_verdict=AuditVerdict.REJECTED_POLICY_VIOLATION,
                deterministic_checks=(budget_check,),
                claim_verifications=(),
                nli_executed=False,
                nli_judge_id=None,
                prompt_hash=None,
                evidence_hashes=(),
                audit_latency_ms=0.5,
                auditor_backend="ForensicAuditAdapter-BudgetGuard-v1.0",
            )

        audit_input = ForensicAuditInput(
            request=request,
            response=response,
            prompt_hash=None,
        )
        return self._auditor.audit(audit_input)



class CurriculumRetrievalAdapter(RetrievalPort):
    """Adapter wrapping RetrievalService and CurriculumRegistry."""

    def __init__(
        self,
        service: RetrievalService,
        registry: Optional[CurriculumRegistry] = None,
    ) -> None:
        self._service = service
        self._registry = registry or CurriculumRegistry()

    def retrieve_evidence(
        self,
        query: str,
        node_id: str,
        registry: Any,
        top_k: int = 5,
    ) -> List[ScoredCandidate]:
        """Delegate to RetrievalService.retrieve_evidence with Epistemic Gatekeeper."""
        reg = registry or self._registry
        return self._service.retrieve_evidence(
            query=query,
            node_id=node_id,
            registry=reg,
            top_k=top_k,
        )

    def retrieve_multi_query_evidence(
        self,
        sub_queries: Any,
        node_id: str,
        registry: Any,
        top_k: int = 5,
    ) -> Dict[str, List[ScoredCandidate]]:
        """Delegate to RetrievalService.retrieve_multi_query_evidence with Epistemic Gatekeeper."""
        reg = registry or self._registry
        return self._service.retrieve_multi_query_evidence(
            sub_queries=sub_queries,
            node_id=node_id,
            registry=reg,
            top_k=top_k,
        )


class StructuredTutorAdapter(TutorPort):
    """Adapter wrapping StructuredTutor for controlled generation and deterministic parsing."""

    def __init__(self, tutor: StructuredTutor) -> None:
        self._tutor = tutor
        self.last_response: Optional[GenerationResponse] = None

    def generate_tutoring(
        self,
        request: GenerationRequest,
    ) -> GenerationResponse:
        """Execute generation and certify response via GenerationOutputParser."""
        response = self._tutor.answer(request)
        self.last_response = response
        return response



class ReplayFixtureBackend:
    """Mock backend executing deterministic completions from generation_replay.json."""

    def __init__(
        self,
        fixtures_path: Optional[Path] = None,
        default_model: str = "mock-replay-v1",
    ) -> None:
        self._fixtures_path = fixtures_path or (
            Path(__file__).resolve().parents[3]
            / "data"
            / "experiments"
            / "hito3"
            / "generation_replay.json"
        )
        self._default_model = default_model
        self._fixtures: Dict[str, Any] = {}
        self._load_fixtures()

    def _load_fixtures(self) -> None:
        if self._fixtures_path.exists():
            with open(self._fixtures_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._fixtures = data.get("fixtures", {})

    def get_fixture_by_id(self, fixture_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a raw fixture dict by identifier."""
        return self._fixtures.get(fixture_id)

    def find_by_query_or_node(
        self, query: str, node_id: str
    ) -> Optional[Dict[str, Any]]:
        """Find matching fixture by query and node_id."""
        for k, fix in self._fixtures.items():
            if fix.get("node_id") == node_id and (
                query in fix.get("query", "")
                or fix.get("query", "") in query
            ):
                res = dict(fix)
                res.setdefault("fixture_id", k)
                return res
        return None


# ===========================================================================
# HITO 4 ADAPTERS: ExecutionPort, AssessmentPort, EvidenceIngestionPort, StateReadPort
# ===========================================================================

import shutil
import tempfile
import uuid
from datetime import datetime, timedelta, timezone

from study_engine.assessment.service import DeterministicAssessmentEngine
from study_engine.contracts.assessment import (
    AssessmentResult,
    compute_canonical_sha256,
)
from study_engine.contracts.evidence_ingestion import (
    AdmissionDecision,
    RejectionReason,
    SessionProvenanceContext,
)
from study_engine.contracts.execution import (
    ExecutionObservation,
    ExecutionPlaneTier,
    ExecutionPolicy,
    ExecutionRequest,
    ToolCapability,
)
from study_engine.curriculum.rubric_contracts import AssessmentRubric
from study_engine.curriculum.task_contracts import PracticalTaskSpecification
from study_engine.execution.adapter_python import PythonExecutionAdapter
from study_engine.roadmap.contracts import CurricularRoadmap
from study_engine.session.ports import (
    AssessmentPort,
    ExecutionPort,
    EvidenceIngestionPort,
    StateReadPort,
)
from study_engine.state.ingestion_engine import EvidenceIngestionEngine
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import (
    IdempotentReplayError,
    InconsistentReplayError,
)
from study_engine.session.contracts import MissingProvenanceError
from study_engine.state.policy_contracts import (
    AssessmentPolicy,
    EvidenceRecord,
)
from study_engine.state.state_contracts import StudentState
from study_engine.state.state_engine import derive_student_state


class PracticalExecutionAdapter(ExecutionPort):
    """Adapter executing student artifacts inside Tier 0 sandbox via PythonExecutionAdapter."""

    def __init__(
        self,
        adapter: Optional[PythonExecutionAdapter] = None,
        default_stdin: str = "STUDY_ENGINE_CANONICAL_INPUT",
        timeout_seconds: Optional[int] = None,
    ) -> None:
        self._adapter = adapter or PythonExecutionAdapter()
        self._default_stdin = default_stdin
        self._timeout_seconds = timeout_seconds

    def execute_task(
        self, task: PracticalTaskSpecification, artifact_path: str
    ) -> ExecutionObservation:
        """Execute practical task specification with student artifact."""
        src_path = Path(artifact_path).resolve()
        if not src_path.exists():
            raise FileNotFoundError(f"Student artifact not found at '{artifact_path}'.")

        with tempfile.TemporaryDirectory(prefix="study_exec_") as tmp_dir:
            ws_dir = Path(tmp_dir) / "workspace"
            ws_dir.mkdir(parents=True, exist_ok=True)

            target_script = ws_dir / "student_script.py"
            shutil.copy(src_path, target_script)

            timeout = (
                self._timeout_seconds
                if self._timeout_seconds is not None
                else (
                    min(task.time_limit_minutes * 60, 300)
                    if task.time_limit_minutes
                    else 5
                )
            )

            req = ExecutionRequest(
                request_id=f"req-exec-{uuid.uuid4().hex[:8]}",
                capability=ToolCapability(capability_name="python.run_script"),
                workspace_id=f"ws-{uuid.uuid4().hex[:8]}",
                relative_script_path="student_script.py",
                stdin_payload=self._default_stdin,
                policy=ExecutionPolicy(timeout_seconds=int(timeout)),
                tier=ExecutionPlaneTier.TIER_0,
            )

            exec_res = self._adapter.execute(req, ws_dir)
            return self._adapter.observe(exec_res)

    def execute(
        self, script_content: str, timeout_seconds: float = 30.0
    ) -> ExecutionObservation:
        """Legacy compatibility execution."""
        with tempfile.TemporaryDirectory(prefix="study_exec_legacy_") as tmp_dir:
            ws_dir = Path(tmp_dir) / "workspace"
            ws_dir.mkdir(parents=True, exist_ok=True)

            target_script = ws_dir / "student_script.py"
            target_script.write_text(script_content, encoding="utf-8")

            req = ExecutionRequest(
                request_id=f"req-exec-{uuid.uuid4().hex[:8]}",
                capability=ToolCapability(capability_name="python.run_script"),
                workspace_id=f"ws-{uuid.uuid4().hex[:8]}",
                relative_script_path="student_script.py",
                stdin_payload=self._default_stdin,
                policy=ExecutionPolicy(timeout_seconds=int(timeout_seconds)),
                tier=ExecutionPlaneTier.TIER_0,
            )

            exec_res = self._adapter.execute(req, ws_dir)
            return self._adapter.observe(exec_res)


class DeterministicAssessmentAdapter(AssessmentPort):
    """Adapter evaluating ExecutionObservation against AssessmentRubric via S9.1."""

    def __init__(
        self,
        engine: Optional[DeterministicAssessmentEngine] = None,
        default_task: Optional[PracticalTaskSpecification] = None,
    ) -> None:
        self._engine = engine or DeterministicAssessmentEngine()
        self._default_task = default_task

    def evaluate_observation(
        self,
        observation: ExecutionObservation,
        rubric: AssessmentRubric,
        task: Optional[PracticalTaskSpecification] = None,
    ) -> AssessmentResult:
        resolved_task = task or self._default_task
        if resolved_task is None:
            raise ValueError(
                "Cannot evaluate observation: PracticalTaskSpecification was not provided."
            )

        task_sha = compute_canonical_sha256(resolved_task)
        rubric_sha = compute_canonical_sha256(rubric)

        return self._engine.assess(
            task=resolved_task,
            rubric=rubric,
            observation=observation,
            task_revision_id="rev-task-01",
            rubric_revision_id="rev-rubric-01",
            expected_task_sha256=task_sha,
            expected_rubric_sha256=rubric_sha,
        )

    def assess(
        self,
        observation: ExecutionObservation,
        task: PracticalTaskSpecification,
        rubric: AssessmentRubric,
    ) -> AssessmentResult:
        return self.evaluate_observation(
            observation=observation, rubric=rubric, task=task
        )


class EvidenceIngestionAdapter(EvidenceIngestionPort):
    """Adapter evaluating admissibility (S5.2.A) and committing evidence to ledger (S5.2.B)."""

    def __init__(
        self,
        engine: Optional[EvidenceIngestionEngine] = None,
        ledger: Optional[EvidenceLedger] = None,
        roadmap: Optional[CurricularRoadmap] = None,
        policy: Optional[AssessmentPolicy] = None,
        student_id: str = "student-gp-b",
        session_id: str = "session-practical",
    ) -> None:
        self._engine = engine or EvidenceIngestionEngine()
        self._ledger = ledger or EvidenceLedger()
        self._roadmap = roadmap
        self._policy = policy
        self._student_id = student_id
        self._session_id = session_id

    @property
    def ledger(self) -> EvidenceLedger:
        return self._ledger

    def ingest_assessment(
        self,
        assessment: AssessmentResult,
        context: Optional[SessionProvenanceContext] = None,
    ) -> EvidenceRecord:
        """Admit assessment result and commit atomic record to ledger."""
        if context is None:
            raise MissingProvenanceError(
                "SessionProvenanceContext is mandatory for assessment ingestion (missing provenance context)."
            )

        # 1. Evaluate admissibility with S5.2.A
        admission = self._engine.evaluate_admissibility(
            assessment=assessment,
            context=context,
            ledger=self._ledger,
        )

        if admission.decision == AdmissionDecision.REJECTED:
            if admission.rejection_reason == RejectionReason.DUPLICATE_ASSESSMENT_REPLAY:
                raise IdempotentReplayError(
                    f"Idempotent replay detected by anti-replay gate: {admission.rejection_detail}"
                )
            if admission.rejection_reason == RejectionReason.INCONSISTENT_ASSESSMENT_REPLAY:
                raise InconsistentReplayError(
                    f"Inconsistent replay detected by anti-replay gate: {admission.rejection_detail}"
                )
            reason_str = (
                admission.rejection_reason.value
                if admission.rejection_reason is not None
                else "REJECTED"
            )
            raise ValueError(
                f"Assessment rejected by S5.2.A: {reason_str}: {admission.rejection_detail}"
            )

        assert admission.outcome is not None

        # 2. Build admitted record
        record = self._engine.build_admitted_record(
            assessment=assessment,
            context=context,
            outcome=admission.outcome,
            trace=admission.admission_trace,
        )

        eval_attempt_id = (
            getattr(assessment, "evaluation_attempt_id", None)
            or assessment.assessment_id
        )
        record = record.model_copy(
            update={
                "tool_backend": "python.adapter",
                "metadata": {
                    **record.metadata,
                    "evaluation_attempt_id": eval_attempt_id,
                },
            }
        )

        # 3. Commit to authoritative ledger (enforces D(K, R))
        self._ledger.append_record(record)
        return record


class CurriculumStateAdapter(StateReadPort):
    """Adapter reading projected student state (S5.2.C) with deterministic cutoff-based caching."""

    def __init__(
        self,
        roadmap: CurricularRoadmap,
        policy: AssessmentPolicy,
        ledger: EvidenceLedger,
        student_id: str,
    ) -> None:
        self._roadmap = roadmap
        self._policy = policy
        self._ledger = ledger
        self._student_id = student_id
        self._cached_state: Optional[StudentState] = None
        self._cached_cutoff_hash: Optional[str] = None
        self._cached_as_of_time: Optional[datetime] = None
        self._projection_count: int = 0
        self._cache_hit_count: int = 0

    @property
    def projection_count(self) -> int:
        """Total number of times full state derivation was executed."""
        return self._projection_count

    @property
    def cache_hit_count(self) -> int:
        """Total number of times cached projection was returned."""
        return self._cache_hit_count

    def invalidate_cache(self) -> None:
        """Explicitly clear cached projection."""
        self._cached_state = None
        self._cached_cutoff_hash = None
        self._cached_as_of_time = None

    def get_student_state(
        self,
        student_id: str,
        as_of_time: Optional[datetime] = None,
    ) -> StudentState:
        """Derive or return cached student state using deterministic ledger cutoff hash."""
        if student_id == self._student_id:
            current_cutoff_hash = self._ledger.get_cutoff_tip_hash(
                as_of_time=as_of_time
            )
            if (
                self._cached_state is not None
                and self._cached_cutoff_hash == current_cutoff_hash
                and self._cached_as_of_time == as_of_time
            ):
                self._cache_hit_count += 1
                return self._cached_state

            state = derive_student_state(
                roadmap=self._roadmap,
                policy=self._policy,
                ledger=self._ledger,
                student_id=student_id,
                as_of_time=as_of_time,
            )
            self._cached_state = state
            self._cached_cutoff_hash = current_cutoff_hash
            self._cached_as_of_time = as_of_time
            self._projection_count += 1
            return state

        return derive_student_state(
            roadmap=self._roadmap,
            policy=self._policy,
            ledger=self._ledger,
            student_id=student_id,
            as_of_time=as_of_time,
        )

    def get_node_state(self, node_id: str) -> Optional[Any]:
        state = self.get_student_state(self._student_id)
        return state.get_node_state(node_id)

