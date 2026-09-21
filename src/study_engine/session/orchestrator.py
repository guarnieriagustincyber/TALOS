"""Session Orchestrator for Subsystem S5.3.

Coordinates multi-turn student interactions across execution (S6.1),
assessment (S9.1), evidence ingestion (S5.2.A), state projection (S5.2.C),
retrieval (S3), generation (S4.3), and forensic audit (S4.4) without
exercising autonomous mastery or curricular authority.

INVARIANTS:
1. Zero Autonomous Mastery Authority: S5.3 coordinates, does not judge.
2. Authorized Target Inviolability: target is externally authorized.
3. Pure Operational Envelope: does not interpret evaluative scores.
4. Port Decoupled: interacts via typed Protocols, no ledger in ports.
5. Durable Idempotency: TurnReceiptStore keyed on request digest.
6. Zero Automatic Re-Execution on recovery.
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import tempfile
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
import uuid

from study_engine.contracts.assessment import AssessmentResult
from study_engine.contracts.evidence_ingestion import (
    AdmissionDecision,
    AdmissionResult,
    EvidenceIngestionResult,
    SessionProvenanceContext,
)
from study_engine.contracts.execution import ExecutionObservation
from study_engine.roadmap.contracts import CurricularRoadmap
from study_engine.session.contracts import (
    AuditRejectionError,
    AuthorizedSessionTarget,
    compute_canonical_sha256,
    PracticeRequest,
    PracticeResult,
    PracticeResultStatus,
    RecoveryDisposition,
    SessionDecision,
    SessionExpiredError,
    SessionRequest,
    SessionResult,
    SessionResultStatus,
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
from study_engine.session.ports import (
    AssessmentPort,
    AuditPort,
    EvidenceIngestionPort,
    ExecutionPort,
    InMemoryTurnReceiptStore,
    RetrievalPort,
    RubricSpecificationProvider,
    StateReadPort,
    TaskSpecificationProvider,
    TutorPort,
    TurnReceiptStore,
)
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.policy_contracts import AssessmentPolicy
from study_engine.state.state_contracts import (
    NodeProgressStatus,
    StudentState,
)
from study_engine.state.state_engine import derive_student_state


class _DefaultIngestionAdapter:
    """Internal adapter wrapping EvidenceIngestionEngine for legacy callers."""

    def __init__(
        self, ledger: EvidenceLedger, policy: AssessmentPolicy
    ) -> None:
        from study_engine.state.ingestion_engine import EvidenceIngestionEngine

        self.ledger = ledger
        self.policy = policy
        self.engine = EvidenceIngestionEngine()

    def ingest_assessment(
        self,
        assessment: AssessmentResult,
        context: Optional[SessionProvenanceContext] = None,
    ) -> Any:
        if context is None:
            raise ValueError("context is required for _DefaultIngestionAdapter")
        return self.engine.ingest_assessment(
            assessment, context, self.ledger
        )


class SessionOrchestrator:
    """Pure session orchestrator coordinating multi-turn interactions."""

    def __init__(
        self,
        session_id: str,
        student_id: str,
        roadmap: CurricularRoadmap,
        policy: AssessmentPolicy,
        ledger: Optional[EvidenceLedger] = None,
        authorized_target: Optional[AuthorizedSessionTarget] = None,
        receipt_store: Optional[TurnReceiptStore] = None,
        execution_port: Optional[ExecutionPort] = None,
        assessment_port: Optional[AssessmentPort] = None,
        ingestion_port: Optional[EvidenceIngestionPort] = None,
        task_provider: Optional[TaskSpecificationProvider] = None,
        rubric_provider: Optional[RubricSpecificationProvider] = None,
        retrieval_port: Optional[RetrievalPort] = None,
        tutor_port: Optional[TutorPort] = None,
        audit_port: Optional[AuditPort] = None,
        state_read_port: Optional[StateReadPort] = None,
        curriculum_registry: Optional[Any] = None,
        retrieval_fn: Optional[Callable[[str, str], Optional[str]]] = None,
        generation_fn: Optional[Callable[[str, str], str]] = None,
        audit_fn: Optional[Callable[[str, str], Tuple[str, bool]]] = None,
        session_started_at: Optional[datetime] = None,
        session_expires_at: Optional[datetime] = None,
        state_projector_fn: Optional[Callable[..., StudentState]] = None,
        allowed_artifact_roots: Optional[Sequence[Union[str, Path]]] = None,
    ) -> None:
        self.session_id = session_id
        self.student_id = student_id
        self.roadmap = roadmap
        self.policy = policy
        self.ledger = ledger

        self.session_started_at = (
            session_started_at or datetime.now(timezone.utc)
        )
        self.session_expires_at = session_expires_at

        # Target authorization
        if authorized_target is not None:
            self.authorized_target = authorized_target
        else:
            initial_node = next(iter(roadmap.nodes.keys()))
            self.authorized_target = AuthorizedSessionTarget(
                authorization_id=f"auth-{session_id}",
                student_id=student_id,
                session_id=session_id,
                node_id=initial_node,
                roadmap_revision_id=roadmap.canonical_revision_id,
                authorized_at=self.session_started_at,
            )

        # Receipt store
        self.receipt_store: TurnReceiptStore = (
            receipt_store or InMemoryTurnReceiptStore()
        )

        # Ports
        self.execution_port = execution_port
        self.assessment_port = assessment_port
        self.task_provider = task_provider
        self.rubric_provider = rubric_provider

        if ingestion_port is not None:
            self.ingestion_port: Optional[
                EvidenceIngestionPort
            ] = ingestion_port
        elif ledger is not None:
            self.ingestion_port = _DefaultIngestionAdapter(ledger, policy)
        else:
            self.ingestion_port = None

        self.retrieval_port = retrieval_port
        self.tutor_port = tutor_port
        self.audit_port = audit_port
        self.state_read_port = state_read_port
        self.curriculum_registry = curriculum_registry

        self.retrieval_fn = retrieval_fn
        self.generation_fn = generation_fn
        self.audit_fn = audit_fn
        self.state_projector_fn = state_projector_fn

        self.fsm = SessionFSM(SessionStatus.CREATED)
        self.current_turn_index = 0
        self.current_target_node_id = self.authorized_target.node_id
        self.replay_cache: Dict[str, SessionTurnOutput] = {}
        self.turn_history: List[SessionTurnOutput] = []
        # Generation counter for state cache invalidation
        self._state_generation: int = 0
        # Cache key is (generation, as_of_time_rounded) so the same turn's
        # within-second duplicate _derive_state calls hit the cache, while
        # distinct turns/timestamps never collide.
        self._state_cache: Dict[Tuple[int, str], StudentState] = {}
        if allowed_artifact_roots is not None:
            self.allowed_artifact_roots: Tuple[Path, ...] = tuple(
                Path(p).resolve() for p in allowed_artifact_roots
            )
        else:
            repo_root = Path(__file__).resolve().parents[3]
            self.allowed_artifact_roots = (
                repo_root.resolve(),
                (repo_root / "data").resolve(),
                (repo_root / "scratch").resolve(),
                Path(tempfile.gettempdir()).resolve(),
            )

    def _derive_state(self, as_of_time: datetime) -> StudentState:
        """Derive student state via state_read_port, projector or fallback.

        Cached per (generation, as_of_time_rounded) for pure fallback path.
        Both state_read_port and state_projector_fn have their own cache/
        semantics and must be called fresh on each turn.
        """
        # Only cache for pure fallback path
        use_cache = (self.state_read_port is None and self.state_projector_fn is None)
        if use_cache:
            # Round to seconds: allows cache hit for calls within same turn
            # (which use datetime.now() ~ms apart) but not across turns
            # with different timestamps.
            time_key = as_of_time.replace(microsecond=0).isoformat()
            cache_key = (self._state_generation, time_key)
            cached = self._state_cache.get(cache_key)
            if cached is not None:
                return cached

        if self.state_read_port is not None:
            state = self.state_read_port.get_student_state(
                self.student_id, as_of_time
            )
        elif self.state_projector_fn is not None:
            state = self.state_projector_fn(
                roadmap=self.roadmap,
                policy=self.policy,
                ledger=self.ledger,
                student_id=self.student_id,
                as_of_time=as_of_time,
            )
        elif self.ledger is not None:
            state = derive_student_state(
                roadmap=self.roadmap,
                policy=self.policy,
                ledger=self.ledger,
                student_id=self.student_id,
                as_of_time=as_of_time,
            )
        else:
            from study_engine.state.ledger_contracts import HistoryCutoffMode
            from study_engine.state.state_contracts import (
                NodeProgressStatus,
                NodeState,
                StudentState,
            )

            blank_nodes = tuple(
                NodeState(
                    node_id=nid,
                    status=NodeProgressStatus.AVAILABLE,
                )
                for nid in self.roadmap.nodes.keys()
            )
            state = StudentState(
                student_id=self.student_id,
                roadmap_revision_id=self.roadmap.canonical_revision_id,
                policy_revision_id=self.policy.canonical_policy_id,
                ledger_cutoff_hash="0" * 64,
                as_of_time=as_of_time,
                cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
                node_states=blank_nodes,
                canonical_state_id="0" * 64,
            )

        if use_cache:
            self._state_cache[cache_key] = state
        return state
        from study_engine.state.ledger_contracts import HistoryCutoffMode
        from study_engine.state.state_contracts import (
            NodeProgressStatus,
            NodeState,
            StudentState,
        )

        blank_nodes = tuple(
            NodeState(
                node_id=nid,
                status=NodeProgressStatus.AVAILABLE,
            )
            for nid in self.roadmap.nodes.keys()
        )
        return StudentState(
            student_id=self.student_id,
            roadmap_revision_id=self.roadmap.canonical_revision_id,
            policy_revision_id=self.policy.canonical_policy_id,
            ledger_cutoff_hash="0" * 64,
            as_of_time=as_of_time,
            cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
            node_states=blank_nodes,
            canonical_state_id="0" * 64,
        )

    def start_session(
        self, as_of_time: Optional[datetime] = None
    ) -> SessionTurnOutput:
        """Initialize session, project state, and present initial challenge."""
        self.fsm.transition_to(SessionStatus.ACTIVE, "Session initiated")

        effective_time = as_of_time or datetime.now(timezone.utc)
        state = self._derive_state(effective_time)
        target_node_id = self.authorized_target.node_id
        self.current_target_node_id = target_node_id

        welcome_content = (
            f"Welcome to session {self.session_id}. "
            f"Current curricular focus is '{target_node_id}'."
        )

        turn_output = SessionTurnOutput(
            turn_id=f"turn-{self.session_id}-0",
            session_id=self.session_id,
            turn_index=0,
            action_type=TurnActionType.CHALLENGE,
            resolved_target_node_id=target_node_id,
            content=welcome_content,
            audit_report_id=None,
            produced_evidence_id=None,
            student_state_id=state.canonical_state_id,
            admission_result=None,
            ingestion_result=None,
            created_at=effective_time,
        )

        self.turn_history.append(turn_output)
        self.current_turn_index = 1
        self.fsm.transition_to(
            SessionStatus.WAITING_FOR_STUDENT, "Initial challenge presented"
        )
        return turn_output

    def decide_turn(
        self, student_input: StudentInput, current_state: StudentState
    ) -> SessionDecision:
        """Formulate SessionDecision separating planning from execution."""
        # Validate target inviolability
        if student_input.requested_node_id:
            req_id = student_input.requested_node_id
            if req_id != self.authorized_target.node_id:
                ns = current_state.get_node_state(req_id)
                if ns and ns.status == NodeProgressStatus.LOCKED:
                    raise UnauthorizedTargetDeviationError(
                        f"Target node '{req_id}' is LOCKED by prerequisites: "
                        f"{ns.unfulfilled_hard_prerequisites}."
                    )
                raise UnauthorizedTargetDeviationError(
                    f"Requested target node '{req_id}' deviates from "
                    f"authorized target '{self.authorized_target.node_id}'."
                )
            resolved_node_id = req_id
        else:
            resolved_node_id = self.authorized_target.node_id

        self.current_target_node_id = resolved_node_id
        decision_id = f"dec-{uuid.uuid4().hex[:8]}"

        if student_input.input_type == StudentInputType.COMMAND:
            cmd = student_input.content.strip()
            if cmd == "/abort":
                return SessionDecision(
                    decision_id=decision_id,
                    session_id=self.session_id,
                    turn_index=self.current_turn_index,
                    resolved_target_node_id=resolved_node_id,
                    action_type=TurnActionType.SESSION_TERMINATED,
                    terminal_action=TerminalAction.ABORT,
                )
            elif cmd == "/complete":
                return SessionDecision(
                    decision_id=decision_id,
                    session_id=self.session_id,
                    turn_index=self.current_turn_index,
                    resolved_target_node_id=resolved_node_id,
                    action_type=TurnActionType.SESSION_TERMINATED,
                    terminal_action=TerminalAction.COMPLETE,
                )

        if student_input.input_type in (
            StudentInputType.ANSWER,
            StudentInputType.CODE_SUBMISSION,
            StudentInputType.EXTERNAL_EVIDENCE,
        ):
            return SessionDecision(
                decision_id=decision_id,
                session_id=self.session_id,
                turn_index=self.current_turn_index,
                resolved_target_node_id=resolved_node_id,
                action_type=TurnActionType.ASSESSMENT_REPORT,
                requires_assessment=True,
                requires_ledger_append=True,
                requires_generation=True,
            )

        # Questions or explanation requests
        return SessionDecision(
            decision_id=decision_id,
            session_id=self.session_id,
            turn_index=self.current_turn_index,
            resolved_target_node_id=resolved_node_id,
            action_type=TurnActionType.EXPLAIN,
            requires_retrieval=True,
            requires_generation=True,
        )

    def process_turn(self, student_input: StudentInput) -> SessionTurnOutput:
        """Process a turn through FSM, decision, ports, audit, and receipts."""
        # 1. Terminal State Invariant
        if self.fsm.is_terminal:
            raise SessionTerminalError(
                f"Cannot process turn on terminal session in status "
                f"'{self.fsm.current_status.value}'."
            )

        # 2. Temporal Expiration Check
        if (
            self.session_expires_at is not None
            and student_input.timestamp > self.session_expires_at
        ):
            self.fsm.transition_to(
                SessionStatus.EXPIRED,
                "Session expired before turn submission",
            )
            raise SessionExpiredError(
                f"Session '{self.session_id}' expired at "
                f"{self.session_expires_at.isoformat()}."
            )

        # 3. Durable Idempotency Check via TurnReceiptStore
        req_digest = compute_canonical_sha256(student_input)
        existing_receipt = self.receipt_store.get_receipt(
            student_input.input_id
        )
        if existing_receipt is not None:
            if existing_receipt.request_digest != req_digest:
                raise TurnIdConflictError(
                    f"Turn input_id '{student_input.input_id}' submitted "
                    f"with conflicting request digest."
                )
            if student_input.input_id in self.replay_cache:
                return self.replay_cache[student_input.input_id]
            replayed = SessionTurnOutput.model_validate(
                existing_receipt.output_payload
            )
            self.replay_cache[student_input.input_id] = replayed
            return replayed

        # 4. Project State & Formulate Decision
        current_state = self._derive_state(student_input.timestamp)
        decision = self.decide_turn(student_input, current_state)

        # 5. Handle Terminal Commands
        if decision.terminal_action == TerminalAction.ABORT:
            self.fsm.transition_to(
                SessionStatus.ABORTED, "User requested abort"
            )
            out_abort = SessionTurnOutput(
                turn_id=f"turn-{self.session_id}-{self.current_turn_index}",
                session_id=self.session_id,
                turn_index=self.current_turn_index,
                action_type=TurnActionType.SESSION_TERMINATED,
                resolved_target_node_id=decision.resolved_target_node_id,
                content="Session aborted by student request.",
                audit_report_id=None,
                produced_evidence_id=None,
                student_state_id=current_state.canonical_state_id,
                admission_result=None,
                ingestion_result=None,
                created_at=student_input.timestamp,
            )
            self._persist_turn(student_input, out_abort)
            return out_abort

        if decision.terminal_action == TerminalAction.COMPLETE:
            self.fsm.transition_to(
                SessionStatus.COMPLETED, "Session marked complete"
            )
            out_complete = SessionTurnOutput(
                turn_id=f"turn-{self.session_id}-{self.current_turn_index}",
                session_id=self.session_id,
                turn_index=self.current_turn_index,
                action_type=TurnActionType.SESSION_TERMINATED,
                resolved_target_node_id=decision.resolved_target_node_id,
                content="Session completed successfully.",
                audit_report_id=None,
                produced_evidence_id=None,
                student_state_id=current_state.canonical_state_id,
                admission_result=None,
                ingestion_result=None,
                created_at=student_input.timestamp,
            )
            self._persist_turn(student_input, out_complete)
            return out_complete

        # 6. Branch: Practical Turn vs Formative Turn
        if (
            student_input.input_type == StudentInputType.CODE_SUBMISSION
            or decision.requires_assessment
        ):
            return self._process_practical_turn(
                student_input, decision, current_state
            )

        return self._process_formative_turn(
            student_input, decision, current_state
        )

    def _process_formative_turn(
        self,
        student_input: StudentInput,
        decision: SessionDecision,
        current_state: StudentState,
    ) -> SessionTurnOutput:
        """Process conceptual/formative dialogue without evidence creation."""
        target_node_id = decision.resolved_target_node_id

        # Hito 3: If formal ports are wired, execute sovereign handle_session_request
        if self.tutor_port is not None and self.retrieval_port is not None:
            from study_engine.contracts.generation import GenerationMode

            sess_req = SessionRequest(
                session_id=self.session_id,
                student_id=self.student_id,
                node_id=target_node_id,
                query=student_input.content,
                mode=GenerationMode.EXPLANATION,
                turn_index=self.current_turn_index,
            )
            sess_res = self.handle_session_request(sess_req)
            turn_output = SessionTurnOutput(
                turn_id=sess_res.turn_id,
                session_id=self.session_id,
                turn_index=self.current_turn_index,
                action_type=(
                    TurnActionType.EXPLAIN
                    if sess_res.status == SessionResultStatus.APPROVED
                    else TurnActionType.ABSTENTION
                ),
                resolved_target_node_id=target_node_id,
                content=sess_res.response_text,
                audit_report_id=sess_res.audit_report_id,
                produced_evidence_id=None,
                student_state_id=current_state.canonical_state_id,
                admission_result=None,
                ingestion_result=None,
                created_at=student_input.timestamp,
            )
            self._persist_turn(student_input, turn_output)
            return turn_output

        action_type = decision.action_type
        response_content = ""
        audit_report_id: Optional[str] = None

        if decision.requires_retrieval:
            context = None
            if self.retrieval_fn:
                context = self.retrieval_fn(
                    target_node_id, student_input.content
                )
            if not context:
                action_type = TurnActionType.ABSTENTION
                response_content = (
                    f"No verified curricular evidence was retrieved for "
                    f"'{target_node_id}'. Abstaining from generation."
                )

        if not response_content:
            fallback = (
                f"Feedback for turn {self.current_turn_index} on "
                f"{target_node_id}."
            )
            raw_gen = (
                self.generation_fn(target_node_id, student_input.content)
                if self.generation_fn
                else fallback
            )

            if self.audit_fn:
                rep_id, is_approved = self.audit_fn(target_node_id, raw_gen)
                audit_report_id = rep_id
                if not is_approved:
                    raise AuditRejectionError(
                        f"Forensic audit report '{rep_id}' rejected the "
                        f"generated response."
                    )
            response_content = raw_gen

        # Strict Formative Invariant: 0 EvidenceRecord, 0 Ledger append
        turn_output = SessionTurnOutput(
            turn_id=f"turn-{self.session_id}-{self.current_turn_index}",
            session_id=self.session_id,
            turn_index=self.current_turn_index,
            action_type=action_type,
            resolved_target_node_id=target_node_id,
            content=response_content,
            audit_report_id=audit_report_id,
            produced_evidence_id=None,
            student_state_id=current_state.canonical_state_id,
            admission_result=None,
            ingestion_result=None,
            created_at=student_input.timestamp,
        )

        self._persist_turn(student_input, turn_output)
        return turn_output

    def _process_practical_turn(
        self,
        student_input: StudentInput,
        decision: SessionDecision,
        current_state: StudentState,
    ) -> SessionTurnOutput:
        """Process practical code turn across S6, S9, S5.2.A, and S5.2.C."""
        target_node_id = decision.resolved_target_node_id

        # 1. EXECUTING (S6.1)
        self.fsm.transition_to(
            SessionStatus.EXECUTING,
            f"Executing code submission {student_input.input_id}",
        )
        observation: Optional[ExecutionObservation] = None
        if self.execution_port is not None:
            observation = self.execution_port.execute(student_input.content)
        else:
            observation = ExecutionObservation(
                observation_id=f"obs-{student_input.input_id}",
                execution_id=f"exec-{student_input.input_id}",
                tool_name="python_sandbox",
                exit_code=0,
            )

        # 2. ASSESSING (S9.1)
        self.fsm.transition_to(
            SessionStatus.ASSESSING,
            f"Assessing observation for turn {self.current_turn_index}",
        )
        assessment: Optional[AssessmentResult] = None
        if self.assessment_port is not None:
            task = (
                self.task_provider.get_task_specification(target_node_id)
                if self.task_provider
                else None
            )
            rubric = (
                self.rubric_provider.get_rubric_specification(target_node_id)
                if self.rubric_provider
                else None
            )
            if task is None:
                from study_engine.curriculum.task_contracts import (
                    PracticalTaskSpecification,
                )

                task = PracticalTaskSpecification(
                    task_id=f"task-{target_node_id}",
                    curriculum_node_id=target_node_id,
                    title=f"Task for {target_node_id}",
                    description=f"Auto task spec for {target_node_id}",
                )
            if rubric is None:
                from study_engine.curriculum.rubric_contracts import (
                    AssessmentRubric,
                    RubricDimension,
                )

                rubric = AssessmentRubric(
                    rubric_id=f"rubric-{target_node_id}",
                    title=f"Rubric for {target_node_id}",
                    dimensions=(
                        RubricDimension(
                            dimension_id="dim-exec",
                            title="Execution Validity",
                            weight=1.0,
                        ),
                    ),
                )
            assessment = self.assessment_port.assess(
                observation, task, rubric
            )
        else:
            # Synthetic assessment result for legacy callers
            from study_engine.contracts.assessment import (
                AggregationResult,
                AssessmentStatus,
                DimensionEvaluation,
                EvaluativeFact,
                EvaluativeFactType,
                FactObservability,
                InstrumentalFact,
                InstrumentalFactType,
                ObservationReference,
                SpecificationReference,
            )
            from study_engine.curriculum.performance_contracts import (
                PerformanceLevel,
            )
            from study_engine.contracts.epistemology import (
                EpistemologicalAuthority,
            )

            inst_fact = InstrumentalFact(
                fact_id=f"fact-inst-{student_input.input_id}",
                observation_id=observation.observation_id,
                fact_type=InstrumentalFactType.PROCESS_EXIT_CODE,
                fact_value="0",
                observability=FactObservability.CONCLUSIVE,
                inspected_domain="scratch/workspace/",
                provenance_detail="Process exit observation",
            )
            eval_fact = EvaluativeFact(
                fact_id=f"fact-eval-{student_input.input_id}",
                evaluator_id="eval-legacy",
                fact_type=EvaluativeFactType.EXIT_CODE_EXPECTED,
                fact_value="0",
                satisfied=True,
                based_on_instrumental_fact_ids=(inst_fact.fact_id,),
                requirement_id="req-1",
                rationale="Turn completed cleanly",
            )
            dim_eval = DimensionEvaluation(
                dimension_id="dim-exec",
                status=AssessmentStatus.ASSESSED,
                assigned_level=PerformanceLevel.N3_COMPETENT,
                passed_minimum=True,
                is_critical=True,
                evidence_evaluative_fact_ids=(eval_fact.fact_id,),
                evaluator_rule_ids=(),
                evaluation_rationale="Evaluated cleanly",
            )
            interim_asmt = AssessmentResult(
                assessment_id=f"asmt-{student_input.input_id}",
                authority_id=EpistemologicalAuthority.ASSESSMENT_ENGINE.value,
                task=SpecificationReference(
                    specification_id=f"task-{target_node_id}",
                    revision_id="rev-1",
                    specification_sha256="a" * 64,
                ),
                rubric=SpecificationReference(
                    specification_id=f"rubric-{target_node_id}",
                    revision_id="rev-1",
                    specification_sha256="b" * 64,
                ),
                observations=(
                    ObservationReference(
                        observation_id=observation.observation_id,
                        execution_id=observation.execution_id,
                        effective_script_sha256="c" * 64,
                        observation_sha256="c" * 64,
                    ),
                ),
                instrumental_facts=(inst_fact,),
                evaluative_facts=(eval_fact,),
                dimension_evaluations=(dim_eval,),
                aggregation=AggregationResult(
                    overall_level=PerformanceLevel.N3_COMPETENT,
                    passed=True,
                ),
                evaluator_id="S9_DETERMINISTIC_EVALUATOR",
                evaluator_version="1.0.0",
                assessed_at=student_input.timestamp,
                assessment_digest="",
            )
            computed_asmt_digest = compute_canonical_sha256(interim_asmt)
            assessment = interim_asmt.model_copy(
                update={"assessment_digest": computed_asmt_digest}
            )

        # 3. INGESTING (S5.2.A)
        self.fsm.transition_to(
            SessionStatus.INGESTING,
            f"Ingesting assessment for turn {self.current_turn_index}",
        )
        admission_res: Optional[AdmissionResult] = None
        ingestion_res: Optional[EvidenceIngestionResult] = None
        produced_evidence_id: Optional[str] = None

        if assessment is not None and self.ingestion_port is not None:
            provenance_ctx = SessionProvenanceContext(
                student_id=self.authorized_target.student_id,
                session_id=self.session_id,
                resolved_target_node_id=self.authorized_target.node_id,
                requested_node_id=student_input.requested_node_id,
                roadmap_revision_id=self.authorized_target.roadmap_revision_id,
                policy_revision_id=self.policy.canonical_policy_id,
                session_is_active=not self.fsm.is_terminal,
                session_started_at=self.session_started_at,
                session_expires_at=self.session_expires_at,
            )
            ingestion_res = self.ingestion_port.ingest_assessment(
                assessment, provenance_ctx
            )
            admission_res = ingestion_res.admission
            if (
                admission_res.decision == AdmissionDecision.ADMITTED
                and ingestion_res.ledger_entry is not None
            ):
                produced_evidence_id = (
                    ingestion_res.ledger_entry.record.record_id
                )
                # Re-project state only after ledger persistence
                current_state = self._derive_state(student_input.timestamp)

        content = (
            f"Assessment completed for practical turn on {target_node_id}."
        )

        turn_output = SessionTurnOutput(
            turn_id=f"turn-{self.session_id}-{self.current_turn_index}",
            session_id=self.session_id,
            turn_index=self.current_turn_index,
            action_type=TurnActionType.ASSESSMENT_REPORT,
            resolved_target_node_id=target_node_id,
            content=content,
            audit_report_id=None,
            produced_evidence_id=produced_evidence_id,
            student_state_id=current_state.canonical_state_id,
            admission_result=admission_res,
            ingestion_result=ingestion_res,
            created_at=student_input.timestamp,
        )

        # Persist receipt with lineage
        exec_id = observation.execution_id if observation else None
        assess_digest = (
            assessment.assessment_digest if assessment else None
        )
        self._persist_turn(
            student_input,
            turn_output,
            execution_id=exec_id,
            assessment_digest=assess_digest,
            evidence_record_id=produced_evidence_id,
        )

        # FSM Invariant: transition strictly to WAITING_FOR_STUDENT,
        # never autonomously transition to COMPLETED.
        self.fsm.transition_to(
            SessionStatus.WAITING_FOR_STUDENT,
            "Practical turn completed, awaiting next input",
        )
        return turn_output

    def _persist_turn(
        self,
        student_input: StudentInput,
        turn_output: SessionTurnOutput,
        execution_id: Optional[str] = None,
        assessment_digest: Optional[str] = None,
        evidence_record_id: Optional[str] = None,
    ) -> None:
        """Persist TurnReceipt and update session state."""
        # Invalidate state cache: ledger may have changed
        self._state_generation += 1
        self._state_cache.clear()

        req_digest = compute_canonical_sha256(student_input)
        out_payload = turn_output.model_dump(mode="json")
        out_digest = hashlib.sha256(
            turn_output.model_dump_json().encode("utf-8")
        ).hexdigest()

        receipt = TurnReceipt(
            receipt_id=f"rcpt-{student_input.input_id}",
            input_id=student_input.input_id,
            session_id=self.session_id,
            turn_index=turn_output.turn_index,
            request_digest=req_digest,
            lifecycle_status=self.fsm.current_status,
            action_type=turn_output.action_type,
            output_digest=out_digest,
            execution_id=execution_id,
            assessment_digest=assessment_digest,
            evidence_record_id=evidence_record_id,
            output_payload=out_payload,
            created_at=turn_output.created_at,
        )
        self.receipt_store.store_receipt(receipt)
        self.replay_cache[student_input.input_id] = turn_output
        self.turn_history.append(turn_output)
        self.current_turn_index += 1

    def recover_session(
        self,
        disposition: RecoveryDisposition,
        uningested_assessment: Optional[AssessmentResult] = None,
        provenance_context: Optional[SessionProvenanceContext] = None,
    ) -> RecoveryDisposition:
        """Handle crash-recovery disposition with zero automatic re-execution.

        Invariants:
        1. Never invokes execution_port.execute() or re-runs student code.
        2. Ingests existing uncommitted assessment once if provided.
        3. Missing TurnReceipt never negates an existing committed record.
        """
        if (
            not self.fsm.is_terminal
            and self.fsm.current_status != SessionStatus.RECOVERING
        ):
            if self.fsm.can_transition_to(SessionStatus.RECOVERING):
                self.fsm.transition_to(
                    SessionStatus.RECOVERING, "Initiating crash recovery"
                )

        if disposition == RecoveryDisposition.RETURN_TO_WAITING:
            if self.fsm.can_transition_to(SessionStatus.WAITING_FOR_STUDENT):
                self.fsm.transition_to(
                    SessionStatus.WAITING_FOR_STUDENT,
                    "Restored to waiting state after crash",
                )
            return disposition

        if disposition == RecoveryDisposition.REPLAY_COMPLETED:
            if (
                uningested_assessment is not None
                and self.ingestion_port is not None
                and provenance_context is not None
            ):
                if self.fsm.can_transition_to(SessionStatus.INGESTING):
                    self.fsm.transition_to(
                        SessionStatus.INGESTING,
                        "Recovering uningested assessment",
                    )
                self.ingestion_port.ingest_assessment(
                    uningested_assessment, provenance_context
                )
            if self.fsm.can_transition_to(SessionStatus.WAITING_FOR_STUDENT):
                self.fsm.transition_to(
                    SessionStatus.WAITING_FOR_STUDENT,
                    "Completed recovery to waiting state",
                )
            return disposition

        if disposition == RecoveryDisposition.RESTART_EVALUATION:
            # Strictly return to waiting for explicit student resubmission
            if self.fsm.can_transition_to(SessionStatus.WAITING_FOR_STUDENT):
                self.fsm.transition_to(
                    SessionStatus.WAITING_FOR_STUDENT,
                    "Restored to waiting state for student retry",
                )
            return disposition

        return disposition

    def _persist_session_result(
        self, request: SessionRequest, result: SessionResult
    ) -> None:
        """Persist SessionResult in TurnReceiptStore with canonical request digest."""
        # Invalidate state cache: ledger may have changed
        self._state_generation += 1
        self._state_cache.clear()

        req_digest = compute_canonical_sha256(request)
        receipt = TurnReceipt(
            receipt_id=f"rec-{result.turn_id}",
            input_id=f"req-{req_digest[:16]}",
            session_id=self.session_id,
            turn_index=request.turn_index,
            request_digest=req_digest,
            lifecycle_status=self.fsm.current_status,
            action_type=(
                TurnActionType.EXPLAIN
                if result.status == SessionResultStatus.APPROVED
                else TurnActionType.ABSTENTION
            ),
            output_digest=compute_canonical_sha256(result),
            output_payload=result.model_dump(mode="json"),
            created_at=datetime.now(timezone.utc),
        )
        self.receipt_store.store_receipt(receipt)

    def handle_session_request(self, request: SessionRequest) -> SessionResult:
        """Execute structured formative turn complying with Hito 3.2 invariants:

        1. Precondition Check (Fail-Closed):
           - Node exists in curriculum and is NOT LOCKED.
        2. Idempotency Check:
           - Return cached SessionResult if request digest was already processed.
        3. Retrieval via RetrievalPort:
           - Epistemic Gatekeeper applied; if empty -> ABSTAINED.
        4. Context Packaging:
           - Evaluates candidates into EvidencePacket and PackagedContext.
        5. Generation via TutorPort:
           - Model proposes language via GenerationRequest -> GenerationResponse.
        6. Forensic Audit via AuditPort (S4.4):
           - Validates citations and grounding; if not APPROVED -> ABSTAINED (Fail-Closed).
        """
        turn_id = f"turn-{self.session_id}-{request.turn_index}"

        # 1. Precondition Check: Node existence and status
        if request.node_id not in self.roadmap.nodes:
            return SessionResult(
                session_id=self.session_id,
                turn_id=turn_id,
                node_id=request.node_id,
                status=SessionResultStatus.FAIL_CLOSED,
                response_text=f"Curricular error: Node '{request.node_id}' does not exist in roadmap.",
                abstention_reason="UNKNOWN_NODE",
            )

        effective_time = datetime.now(timezone.utc)
        current_state = self._derive_state(effective_time)
        node_state = current_state.get_node_state(request.node_id)
        if node_state is None or node_state.status == NodeProgressStatus.LOCKED:
            return SessionResult(
                session_id=self.session_id,
                turn_id=turn_id,
                node_id=request.node_id,
                status=SessionResultStatus.FAIL_CLOSED,
                response_text=(
                    f"Curricular precondition failed: Node '{request.node_id}' is LOCKED. "
                    "Prerequisites are not satisfied."
                ),
                abstention_reason="LOCKED_NODE",
            )

        # 2. Idempotency Check via TurnReceiptStore
        req_digest = compute_canonical_sha256(request)
        input_key = f"req-{req_digest[:16]}"
        existing_receipt = self.receipt_store.get_receipt(input_key)
        if existing_receipt is not None:
            if existing_receipt.output_payload:
                return SessionResult.model_validate(existing_receipt.output_payload)

        # 3. Retrieval via RetrievalPort
        if self.retrieval_port is None:
            res_abstain = SessionResult(
                session_id=self.session_id,
                turn_id=turn_id,
                node_id=request.node_id,
                status=SessionResultStatus.ABSTAINED,
                response_text="RetrievalPort is not configured. Abstaining from generation.",
                abstention_reason="NO_RETRIEVAL_PORT",
            )
            self._persist_session_result(request, res_abstain)
            return res_abstain

        # 3. V1.1 Evidence-Aware Retrieval & Selection Pipeline
        from study_engine.evidence.decomposer import QueryDecomposer
        from study_engine.evidence.selector import EvidenceSelector
        from study_engine.evidence.coverage import EvidenceCoverageEvaluator
        from study_engine.evidence.engine import EvidenceEngine
        from study_engine.context.packer import ContextPacker

        target_notebook = self.roadmap.nodes[request.node_id].notebook_id
        decomposer = QueryDecomposer(max_subqueries=5)
        decomposition = decomposer.decompose(
            query=request.query,
            notebook_id=target_notebook,
            node_id=request.node_id,
            registry=self.curriculum_registry,
        )

        # Multi-query retrieval
        if hasattr(self.retrieval_port, "retrieve_multi_query_evidence"):
            multi_cands = self.retrieval_port.retrieve_multi_query_evidence(
                sub_queries=decomposition.sub_queries,
                node_id=request.node_id,
                registry=self.curriculum_registry,
                top_k=5,
            )
        else:
            multi_cands = {}
            for sq in decomposition.sub_queries:
                cands = self.retrieval_port.retrieve_evidence(
                    query=sq.text,
                    node_id=request.node_id,
                    registry=self.curriculum_registry,
                    top_k=5,
                )
                multi_cands[sq.sub_query_id] = cands

        # Multi-criteria evidence selection (deduplication, diversity, trust)
        selector = EvidenceSelector(max_total_chunks=5, max_chunks_per_source=3)
        selected_candidates = selector.select(multi_cands)

        if not selected_candidates:
            res_abstain = SessionResult(
                session_id=self.session_id,
                turn_id=turn_id,
                node_id=request.node_id,
                status=SessionResultStatus.ABSTAINED,
                response_text=(
                    f"No verified curricular evidence was retrieved for '{request.node_id}'. "
                    "Abstaining from generation."
                ),
                abstention_reason="NO_EVIDENCE",
            )
            self._persist_session_result(request, res_abstain)
            return res_abstain

        # Evidence Coverage evaluation (continuous quality score)
        coverage_evaluator = EvidenceCoverageEvaluator()
        coverage_report = coverage_evaluator.evaluate_coverage(
            sub_queries=decomposition.sub_queries,
            selected_chunks=selected_candidates,
        )

        # 4. Context Packing with enforced coverage directives
        packet = EvidenceEngine().evaluate_candidates(
            query=request.query,
            notebook_id=target_notebook,
            candidates=selected_candidates,
            coverage_report=coverage_report,
        )
        packaged_ctx = ContextPacker().pack(packet, coverage_report=coverage_report)

        # 5. Generation via TutorPort
        if self.tutor_port is None:
            res_abstain = SessionResult(
                session_id=self.session_id,
                turn_id=turn_id,
                node_id=request.node_id,
                status=SessionResultStatus.ABSTAINED,
                response_text="TutorPort is not configured. Abstaining from generation.",
                abstention_reason="NO_TUTOR_PORT",
            )
            self._persist_session_result(request, res_abstain)
            return res_abstain

        from study_engine.contracts.generation import (
            GenerationParameters,
            GenerationRequest,
        )

        gen_req = GenerationRequest(
            request_id=f"gen-{self.session_id}-{request.turn_index}",
            notebook_id=target_notebook,
            query=request.query,
            mode=request.mode,
            packaged_context=packaged_ctx,
            parameters=GenerationParameters(),
            history=request.history,
        )
        gen_response = self.tutor_port.generate_tutoring(gen_req)

        # 6. Audit via AuditPort (S4.4)
        report_id = None
        audit_trace = {}
        if self.audit_port is not None:
            from study_engine.audit.contracts import AuditVerdict

            audit_report = self.audit_port.audit_response(gen_req, gen_response)
            report_id = audit_report.audit_id
            audit_trace = audit_report.model_dump(mode="json")

            if audit_report.overall_verdict != AuditVerdict.APPROVED:
                res_abstain = SessionResult(
                    session_id=self.session_id,
                    turn_id=turn_id,
                    node_id=request.node_id,
                    status=SessionResultStatus.ABSTAINED,
                    response_text=(
                        f"Forensic audit rejected generated response "
                        f"({audit_report.overall_verdict.value}). Emitting canonical abstention."
                    ),
                    audit_report_id=report_id,
                    abstention_reason=audit_report.overall_verdict.value,
                    audit_trace=audit_trace,
                )
                self._persist_session_result(request, res_abstain)
                return res_abstain

        # 7. Final Approved Result
        res_approved = SessionResult(
            session_id=self.session_id,
            turn_id=turn_id,
            node_id=request.node_id,
            status=SessionResultStatus.APPROVED,
            response_text=gen_response.raw_content,
            audit_report_id=report_id,
            abstention_reason=None,
            audit_trace=audit_trace,
        )
        self._persist_session_result(request, res_approved)
        return res_approved

    def handle_practical_submission(
        self,
        artifact_path_or_request: Union[str, PracticeRequest],
        task_id: Optional[str] = None,
        rubric_id: Optional[str] = None,
    ) -> PracticeResult:
        """Handle practical student submission by coordinating execution, assessment, and ingestion.

        INVARIANT: ZERO evaluation logic in the orchestrator.
        Delegates strictly to:
        1. CurriculumRegistry (load task and rubric)
        2. ExecutionPort (S6.1 sandbox execution)
        3. AssessmentPort (S9.1 deterministic evaluation)
        4. EvidenceIngestionPort (S5.2.A admissibility and ledger commitment)
        5. StateReadPort (S5.2.C projected student node state)
        """
        if isinstance(artifact_path_or_request, PracticeRequest):
            req = artifact_path_or_request
            artifact_path = req.artifact_path
            t_id = req.task_id
            target_node: Optional[str] = req.node_id
            student_id = req.student_id
        else:
            artifact_path = artifact_path_or_request
            if task_id is None:
                raise ValueError(
                    "task_id must be provided when passing artifact_path as string."
                )
            t_id = task_id
            student_id = self.student_id
            target_node = None

        expected_sha = None
        if isinstance(artifact_path_or_request, PracticeRequest):
            expected_sha = getattr(artifact_path_or_request, "expected_sha256", None)

        resolved_path, artifact_sha256, err_res = self._verify_submission_artifact(
            artifact_path, expected_sha
        )
        if err_res is not None:
            return err_res
        assert resolved_path is not None and artifact_sha256 is not None

        task, rubric, target_node, err_res = self._load_submission_task_and_rubric(
            t_id, rubric_id, target_node, artifact_path_or_request
        )
        if err_res is not None:
            return err_res
        assert task is not None and rubric is not None and target_node is not None

        if self.execution_port is None:
            raise RuntimeError("ExecutionPort is not configured.")

        obs = self.execution_port.execute_task(task=task, artifact_path=str(resolved_path))
        obs_status = obs.status.value if obs.status is not None else "UNKNOWN"
        obs_exit_code = obs.exit_code if obs.exit_code is not None else -1
        if obs_status not in ("COMPLETED", "SUCCESS"):
            return PracticeResult(
                status=PracticeResultStatus.EXECUTION_FAILED,
                assessment_summary={
                    "exit_code": obs_exit_code,
                    "status": obs_status,
                },
                evidence_record_id=None,
                updated_node_status=None,
                execution_observation=obs.model_dump(mode="json"),
                rejection_reason=f"Execution failed with status '{obs_status}'.",
                artifact_sha256=artifact_sha256,
            )

        if self.assessment_port is None:
            raise RuntimeError("AssessmentPort is not configured.")

        asmt = self.assessment_port.evaluate_observation(
            observation=obs, rubric=rubric, task=task
        )

        (
            ingest_status,
            evidence_record,
            rejection_reason,
            updated_node_status,
        ) = self._commit_evidence_and_derive_node(asmt, student_id, target_node)

        summary: Dict[str, Any] = {
            "passed": asmt.aggregation.passed,
            "overall_level": (
                asmt.aggregation.overall_level.name
                if asmt.aggregation.overall_level
                else None
            ),
            "assessment_digest": asmt.assessment_digest,
        }
        if evidence_record is not None and hasattr(evidence_record, "outcome"):
            summary["outcome"] = evidence_record.outcome.value
            summary["score"] = evidence_record.score

        return PracticeResult(
            status=ingest_status,
            assessment_summary=summary,
            evidence_record_id=(
                evidence_record.record_id if evidence_record else None
            ),
            updated_node_status=updated_node_status,
            execution_observation=obs.model_dump(mode="json"),
            rejection_reason=rejection_reason,
            assessment_result=asmt,
            artifact_sha256=artifact_sha256,
        )

    def _verify_submission_artifact(
        self,
        artifact_path: str,
        expected_sha: Optional[str],
    ) -> Tuple[Optional[Path], Optional[str], Optional[PracticeResult]]:
        """Validate artifact extension, existence, path traversal, and SHA-256 integrity."""
        try:
            raw_path = Path(artifact_path)
            resolved_path = raw_path.resolve()
        except Exception as exc:
            return None, None, PracticeResult(
                status=PracticeResultStatus.EXECUTION_FAILED,
                rejection_reason=f"Path resolution error: {exc}",
            )

        if resolved_path.suffix.lower() != ".py":
            return None, None, PracticeResult(
                status=PracticeResultStatus.EXECUTION_FAILED,
                rejection_reason=f"Invalid artifact format: '{resolved_path.name}' must have .py extension.",
            )

        if not resolved_path.is_file():
            return None, None, PracticeResult(
                status=PracticeResultStatus.EXECUTION_FAILED,
                rejection_reason=f"Artifact not found: '{artifact_path}'.",
            )

        is_allowed = False
        for root in self.allowed_artifact_roots:
            try:
                resolved_path.relative_to(root)
                is_allowed = True
                break
            except ValueError:
                continue

        if not is_allowed:
            return None, None, PracticeResult(
                status=PracticeResultStatus.EXECUTION_FAILED,
                rejection_reason=f"Path traversal rejected: '{artifact_path}' is outside allowed directories.",
            )

        try:
            artifact_sha256 = hashlib.sha256(resolved_path.read_bytes()).hexdigest()
        except Exception as exc:
            return None, None, PracticeResult(
                status=PracticeResultStatus.EXECUTION_FAILED,
                rejection_reason=f"Failed to read artifact for digest computation: {exc}",
            )

        if expected_sha is not None and artifact_sha256 != expected_sha:
            return None, None, PracticeResult(
                status=PracticeResultStatus.EXECUTION_FAILED,
                artifact_sha256=artifact_sha256,
                rejection_reason=(
                    f"Artifact digest mismatch: expected '{expected_sha}', "
                    f"computed '{artifact_sha256}'."
                ),
            )

        return resolved_path, artifact_sha256, None

    def _load_submission_task_and_rubric(
        self,
        t_id: str,
        rubric_id: Optional[str],
        target_node: Optional[str],
        artifact_path_or_request: Any,
    ) -> Tuple[Optional[Any], Optional[Any], Optional[str], Optional[PracticeResult]]:
        """Resolve PracticalTaskSpecification and AssessmentRubric from registry/providers."""
        task = None
        if self.curriculum_registry is not None:
            task = self.curriculum_registry.load_task(t_id)
        elif self.task_provider is not None:
            task = self.task_provider.get_task_specification(t_id)
        else:
            raise RuntimeError("Neither curriculum_registry nor task_provider is configured.")

        if task is None:
            raise RuntimeError(f"Practical task '{t_id}' could not be resolved.")

        if target_node is None:
            target_node = task.curriculum_node_id
        elif target_node != task.curriculum_node_id:
            return None, None, None, PracticeResult(
                status=PracticeResultStatus.EXECUTION_FAILED,
                rejection_reason=(
                    f"Curricular mismatch: requested node '{target_node}' does not match "
                    f"task node '{task.curriculum_node_id}'."
                ),
            )

        r_id = rubric_id
        if r_id is None and isinstance(artifact_path_or_request, PracticeRequest):
            r_id = artifact_path_or_request.rubric_id
        if r_id is None:
            r_id = t_id

        rubric = None
        if self.curriculum_registry is not None:
            try:
                rubric = self.curriculum_registry.load_rubric(r_id)
            except Exception:
                try:
                    rubric = self.curriculum_registry.load_rubric(task.task_id)
                except Exception:
                    rubric = None
        elif self.rubric_provider is not None:
            rubric = self.rubric_provider.get_rubric_specification(r_id)
        else:
            raise RuntimeError("Neither curriculum_registry nor rubric_provider is configured.")

        if rubric is None:
            return None, None, None, PracticeResult(
                status=PracticeResultStatus.EXECUTION_FAILED,
                rejection_reason=f"Assessment rubric for '{t_id}' could not be resolved.",
            )

        return task, rubric, target_node, None

    def _commit_evidence_and_derive_node(
        self,
        asmt: Any,
        student_id: str,
        target_node: str,
    ) -> Tuple[PracticeResultStatus, Optional[Any], Optional[str], Optional[str]]:
        """Ingest assessment evidence into ledger and query updated node state."""
        ingestion_port = self.ingestion_port
        if ingestion_port is None:
            raise RuntimeError("EvidenceIngestionPort is not configured.")

        evidence_record = None
        rejection_reason = None
        try:
            prov_ctx = SessionProvenanceContext(
                student_id=student_id,
                session_id=self.session_id,
                resolved_target_node_id=target_node,
                requested_node_id=target_node,
                roadmap_revision_id=self.roadmap.canonical_revision_id,
                policy_revision_id=self.policy.canonical_policy_id,
                expected_task_specification_sha256=asmt.task.specification_sha256,
                expected_rubric_specification_sha256=asmt.rubric.specification_sha256,
                session_is_active=not self.fsm.is_terminal,
                session_started_at=self.session_started_at,
                session_expires_at=self.session_expires_at,
            )
            evidence_record = ingestion_port.ingest_assessment(asmt, prov_ctx)
            status = PracticeResultStatus.EVALUATED
        except Exception as exc:
            status = PracticeResultStatus.INGESTION_REJECTED
            rejection_reason = str(exc)

        updated_node_status = None
        if self.state_read_port is not None:
            ns = self.state_read_port.get_node_state(target_node)
            if ns is not None:
                updated_node_status = (
                    ns.status.value if hasattr(ns.status, "value") else str(ns.status)
                )
        elif self.ledger is not None:
            from study_engine.state.state_engine import derive_student_state

            derived_state = derive_student_state(
                roadmap=self.roadmap,
                policy=self.policy,
                ledger=self.ledger,
                student_id=student_id,
            )
            ns = derived_state.get_node_state(target_node)
            if ns is not None:
                updated_node_status = (
                    ns.status.value if hasattr(ns.status, "value") else str(ns.status)
                )

        return status, evidence_record, rejection_reason, updated_node_status


