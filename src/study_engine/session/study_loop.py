"""Study Loop Controller for Subsystem S5.3 & S7.

Coordinates the end-to-end 10-stage learning loop:
1. Objective Resolution (S1 Curriculum Registry)
2. Evidence Retrieval (S3 Epistemic Retrieval)
3. Grounded Explanation (S4.3 Generator + S4.4 Forensic Audit)
4. Student Comprehension Probing (S7 Check Understanding)
5. Practice Dispatch (S1 Task Specification)
6. Instrumental Execution (S6.1 Sandbox Execution)
7. Deterministic Assessment (S9.1 Evaluator)
8. Authoritative Evidence Ingestion (S5.2.A + S5.2.B Ledger)
9. Pure State Derivation (S5.2.C State Engine)
10. Pedagogical Feedback & Advancement (S7 DeterministicTutorPolicy)

Zero modifications to the frozen perimeter (state, execution, assessment, audit).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from study_engine.contracts.assessment import AssessmentResult
from study_engine.contracts.generation import ConversationRole, ConversationTurn, GenerationMode
from study_engine.contracts.tutor import (
    TutorContext,
    TutorPolicyDecision,
)
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.llm.exceptions import (
    LLMBackendError,
    LLMConnectionError,
    LLMTimeoutError,
)
from study_engine.llm.factory import LLMPricingTable
from study_engine.session.contracts import (
    PracticeRequest,
    PracticeResult,
    SessionRequest,
    SessionResult,
    SessionResultStatus,
)
from study_engine.session.orchestrator import SessionOrchestrator
from study_engine.state.state_contracts import StudentState
from study_engine.tutor.local_orchestrator import LocalOrchestrator
from study_engine.tutor.policy import DeterministicTutorPolicy
from study_engine.tutor.policy_validator import (
    AuthoritativeRoute,
    DeterministicPolicyValidator,
    RouteKind,
)
from study_engine.tutor.question_type import QuestionType, detect_question_type
from study_engine.tutor.semantic_router import IntentType, SemanticRouter


class StudyLoopController:
    """High-level facade orchestrating multi-turn study cycles under DeterministicTutorPolicy."""

    def __init__(
        self,
        orchestrator: SessionOrchestrator,
        tutor_policy: Optional[DeterministicTutorPolicy] = None,
        curriculum_registry: Optional[CurriculumRegistry] = None,
        active_node_id: Optional[str] = None,
        pricing_table: Optional[LLMPricingTable] = None,
        local_orchestrator: Optional[LocalOrchestrator] = None,
        semantic_router: Optional[SemanticRouter] = None,
    ) -> None:
        self.orchestrator = orchestrator
        self.tutor_policy = tutor_policy or DeterministicTutorPolicy()
        self.pricing_table = pricing_table or LLMPricingTable()
        self.local_orchestrator = local_orchestrator
        self.semantic_router = semantic_router
        self.curriculum_registry = (
            curriculum_registry
            if curriculum_registry is not None
            else getattr(orchestrator, "curriculum_registry", None)
        )

        self.active_node_id = active_node_id or (
            orchestrator.authorized_target.node_id
            if orchestrator.authorized_target
            else (
                next(iter(orchestrator.roadmap.nodes.keys()))
                if orchestrator.roadmap
                and hasattr(orchestrator.roadmap, "nodes")
                and orchestrator.roadmap.nodes
                else "ROOT"
            )
        )
        self.conceptual_turns_completed: int = 0
        self.practice_attempts_count: int = 0
        self.last_assessment_verdict: Optional[str] = None
        self.last_assessment_result: Optional[AssessmentResult] = None
        self.turn_history: List[Dict[str, Any]] = []
        # Conversational dialog turns (student + tutor) supplied to the LLM as
        # conversational context only — never epistemic evidence.
        self.conversation_history: List[ConversationTurn] = []

    def set_active_node(self, node_id: str) -> None:
        """Switch current curricular node target and reset turn counters for the node."""
        if node_id != self.active_node_id:
            self.active_node_id = node_id
            self.conceptual_turns_completed = 0
            self.practice_attempts_count = 0
            self.last_assessment_verdict = None
            self.last_assessment_result = None

    def get_context(self, student_message: Optional[str] = None) -> TutorContext:
        """Derive authoritative student state and build TutorContext for policy decision."""
        now = datetime.now(timezone.utc)
        current_state = self.orchestrator._derive_state(now)
        node_state = current_state.get_node_state(self.active_node_id)
        node_status = (
            node_state.status.value
            if node_state and hasattr(node_state.status, "value")
            else (str(node_state.status) if node_state else "LOCKED")
        )

        # Check hard unfulfilled prerequisites in the roadmap DAG
        unfulfilled: List[str] = []
        for dep in self.orchestrator.roadmap.dependencies:
            if dep.target_node_id == self.active_node_id:
                if dep.source_node_id not in current_state.proficient_node_ids:
                    unfulfilled.append(dep.source_node_id)

        active_node = self.orchestrator.roadmap.nodes.get(self.active_node_id)
        adjacent_node_ids = tuple(
            sorted(
                (
                    dep.target_node_id
                    for dep in self.orchestrator.roadmap.dependencies
                    if dep.source_node_id == self.active_node_id
                ),
                key=lambda node_id: (
                    self.orchestrator.roadmap.nodes[node_id].priority,
                    node_id,
                ),
            )
        )
        node_metadata = active_node.metadata if active_node is not None else {}
        code_example_available = bool(
            node_metadata.get("code_example_available", False)
        )

        return TutorContext(
            student_id=self.orchestrator.student_id,
            active_node_id=self.active_node_id,
            node_status=node_status,
            unfulfilled_prerequisites=unfulfilled,
            conceptual_turns_completed=self.conceptual_turns_completed,
            practice_attempts_count=self.practice_attempts_count,
            last_assessment_verdict=self.last_assessment_verdict,
            last_student_message=student_message,
            active_node_title=active_node.title if active_node is not None else None,
            adjacent_node_ids=adjacent_node_ids,
            code_example_available=code_example_available,
            next_node_id=(adjacent_node_ids[0] if adjacent_node_ids else None),
        )

    def decide_next_action(
        self, student_message: Optional[str] = None
    ) -> TutorPolicyDecision:
        """Evaluate deterministic pedagogical policy over current state and recent input."""
        context = self.get_context(student_message)
        decision = self.tutor_policy.decide(context)
        self.turn_history.append(
            {
                "event": "TUTOR_DECISION",
                "action": decision.action.value,
                "budget": decision.budget.value,
                "target_node_id": decision.target_node_id,
                "rationale": decision.rationale,
                "pedagogical_intent": decision.pedagogical_intent,
            }
        )
        return decision

    def handle_conceptual_turn(
        self,
        query: str,
        target_node_id: Optional[str] = None,
        budget_limit: Optional[int] = None,
        history: Optional[Sequence[ConversationTurn]] = None,
    ) -> SessionResult:
        """Execute factual generation/audit, then attach deterministic UI metadata.

        The orchestrator receives only the conceptual request and audits only
        its factual response text.  Follow-up controls are derived separately
        from TutorPolicy after no generated text has been inspected.

        ``history`` (optional) supplies stateless conversational context from
        the client, enabling multi-turn continuity across server restarts.
        When provided it takes precedence over the in-memory conversation
        history; the controller remains otherwise stateless.
        """
        if target_node_id is not None:
            self.set_active_node(target_node_id)

        route, qt_value = self._resolve_authoritative_route(query, history)

        if route.route_kind == RouteKind.REJECTED:
            return self._handle_rejected_route(route)

        if route.route_kind == RouteKind.GREETING:
            return self._handle_greeting_route(query, route, qt_value)

        if route.route_kind == RouteKind.NAVIGATION:
            return self._handle_navigation_route(query, route, qt_value)

        if route.route_kind == RouteKind.CLARIFICATION:
            return self._handle_clarification_route(query, route, qt_value)

        return self._handle_technical_conceptual_turn(
            query=query,
            route=route,
            qt_value=qt_value,
            budget_limit=budget_limit,
            history=history,
        )

    def _resolve_authoritative_route(
        self,
        query: str,
        history: Optional[Sequence[ConversationTurn]] = None,
    ) -> Tuple[AuthoritativeRoute, str]:
        validator = DeterministicPolicyValidator(
            roadmap=self.orchestrator.roadmap,
            current_node=self.active_node_id,
        )
        if self.semantic_router is not None:
            context_payload = {
                "active_node": self.active_node_id,
                "history": history or self.conversation_history,
            }
            intent = self.semantic_router.interpret(query, context_payload)
            route = validator.resolve(intent)
        else:
            qtype = detect_question_type(query)
            if qtype == QuestionType.GREETING:
                itype = IntentType.GREETING
            elif qtype == QuestionType.CURRICULAR:
                itype = IntentType.STUDY_NAVIGATION
            elif qtype == QuestionType.META:
                itype = IntentType.META_QUESTION
            else:
                itype = IntentType.TECHNICAL_QUESTION
            route = validator.resolve_from_intent_type(itype)

        _QT_VALUE = {
            RouteKind.GREETING: "greeting",
            RouteKind.NAVIGATION: "curricular",
            RouteKind.TECHNICAL: "technical",
            RouteKind.META: "meta",
            RouteKind.CLARIFICATION: "curricular",
            RouteKind.REJECTED: "technical",
        }
        qt_value = _QT_VALUE.get(route.route_kind, "technical")
        return route, qt_value

    def _handle_rejected_route(self, route: AuthoritativeRoute) -> SessionResult:
        return SessionResult(
            session_id=self.orchestrator.session_id,
            turn_id=f"turn-abstain-{self.orchestrator.current_turn_index}",
            node_id=self.active_node_id,
            status=SessionResultStatus.ABSTAINED,
            question_type=route.intent.value,
            response_text="No puedo procesar esa solicitud en el estado curricular actual.",
            abstention_reason=f"INVALID_INTENT:{route.rejected_reason}",
            audit_trace={
                "verdict": f"INVALID_INTENT:{route.rejected_reason}",
                "authoritative_route": route.model_dump(mode="json"),
            },
        )

    def _handle_greeting_route(
        self,
        query: str,
        route: AuthoritativeRoute,
        qt_value: str,
    ) -> SessionResult:
        response_text = "¡Hola! Soy el tutor de KASIU. ¿En qué puedo ayudarte?"
        conv_draft_meta = None
        if self.local_orchestrator is not None:
            active_node = (
                self.orchestrator.roadmap.nodes.get(self.active_node_id)
                if hasattr(self.orchestrator, "roadmap")
                and self.orchestrator.roadmap
                and self.active_node_id in self.orchestrator.roadmap.nodes
                else None
            )
            node_title = active_node.title if active_node is not None else self.active_node_id
            draft = self.local_orchestrator.generate_conversational_draft(
                query=query,
                route_kind=RouteKind.GREETING,
                context={
                    "current_node_id": self.active_node_id,
                    "current_node_title": node_title,
                },
            )
            response_text = draft.text
            conv_draft_meta = draft.model_dump(mode="json")

        audit_trace = {
            "verdict": "INTENT_VALIDATED",
            "authoritative_route": route.model_dump(mode="json"),
        }
        if conv_draft_meta is not None:
            audit_trace["conversational_draft"] = conv_draft_meta

        return SessionResult(
            session_id=self.orchestrator.session_id,
            turn_id=f"turn-greet-{self.orchestrator.current_turn_index}",
            node_id=self.active_node_id,
            status=SessionResultStatus.APPROVED,
            question_type=qt_value,
            response_text=response_text,
            audit_trace=audit_trace,
        )

    def _handle_navigation_route(
        self,
        query: str,
        route: AuthoritativeRoute,
        qt_value: str,
    ) -> SessionResult:
        followup = self.tutor_policy._generate_followup(self.get_context(query))
        next_label = followup.next_node_id if followup else None
        next_guidance = (
            f"Siguiente paso sugerido: '{next_label}'."
            if next_label
            else "Ya estás en el nodo más reciente del roadmap."
        )
        response_text = (
            f"Estás en '{self.active_node_id}'. "
            f"Te recomiendo empezar por el contenido y material de este nodo. "
            f"{next_guidance}"
        )
        conv_draft_meta = None
        if self.local_orchestrator is not None:
            active_node = (
                self.orchestrator.roadmap.nodes.get(self.active_node_id)
                if hasattr(self.orchestrator, "roadmap")
                and self.orchestrator.roadmap
                and self.active_node_id in self.orchestrator.roadmap.nodes
                else None
            )
            node_title = active_node.title if active_node is not None else self.active_node_id
            allowed_nodes = (
                list(self.orchestrator.roadmap.nodes.keys())
                if hasattr(self.orchestrator, "roadmap") and self.orchestrator.roadmap
                else [self.active_node_id]
            )
            next_node = (
                self.orchestrator.roadmap.nodes.get(next_label)
                if next_label
                and hasattr(self.orchestrator, "roadmap")
                and self.orchestrator.roadmap
                and next_label in self.orchestrator.roadmap.nodes
                else None
            )
            next_node_title = next_node.title if next_node is not None else next_label

            draft = self.local_orchestrator.generate_conversational_draft(
                query=query,
                route_kind=RouteKind.NAVIGATION,
                context={
                    "current_node_id": self.active_node_id,
                    "current_node_title": node_title,
                    "allowed_node_ids": allowed_nodes,
                    "next_node_title": next_node_title,
                },
            )
            response_text = draft.text
            conv_draft_meta = draft.model_dump(mode="json")

        audit_trace = {
            "verdict": "INTENT_VALIDATED",
            "authoritative_route": route.model_dump(mode="json"),
        }
        if conv_draft_meta is not None:
            audit_trace["conversational_draft"] = conv_draft_meta

        return SessionResult(
            session_id=self.orchestrator.session_id,
            turn_id=f"turn-curric-{self.orchestrator.current_turn_index}",
            node_id=self.active_node_id,
            status=SessionResultStatus.APPROVED,
            question_type=qt_value,
            response_text=response_text,
            audit_trace=audit_trace,
        )

    def _handle_clarification_route(
        self,
        query: str,
        route: AuthoritativeRoute,
        qt_value: str,
    ) -> SessionResult:
        response_text = (
            "¿Podrías reformular o detallar un poco más tu consulta? "
            "Podés preguntarme sobre el contenido conceptual del tema actual, "
            "consultar tu posición en el roadmap o pedir un ejercicio de práctica."
        )
        conv_draft_meta = None
        if self.local_orchestrator is not None:
            active_node = (
                self.orchestrator.roadmap.nodes.get(self.active_node_id)
                if hasattr(self.orchestrator, "roadmap")
                and self.orchestrator.roadmap
                and self.active_node_id in self.orchestrator.roadmap.nodes
                else None
            )
            node_title = active_node.title if active_node is not None else self.active_node_id
            draft = self.local_orchestrator.generate_conversational_draft(
                query=query,
                route_kind=RouteKind.CLARIFICATION,
                context={
                    "current_node_id": self.active_node_id,
                    "current_node_title": node_title,
                },
            )
            response_text = draft.text
            conv_draft_meta = draft.model_dump(mode="json")

        audit_trace = {
            "verdict": "INTENT_VALIDATED",
            "authoritative_route": route.model_dump(mode="json"),
        }
        if conv_draft_meta is not None:
            audit_trace["conversational_draft"] = conv_draft_meta

        return SessionResult(
            session_id=self.orchestrator.session_id,
            turn_id=f"turn-clarify-{self.orchestrator.current_turn_index}",
            node_id=self.active_node_id,
            status=SessionResultStatus.APPROVED,
            question_type=qt_value,
            response_text=response_text,
            audit_trace=audit_trace,
        )

    def _extract_tutor_telemetry(self) -> Dict[str, Any]:
        telemetry: Dict[str, Any] = {}
        tutor_port = getattr(self.orchestrator, "tutor_port", None)
        if tutor_port is not None and hasattr(tutor_port, "last_response"):
            last_resp = getattr(tutor_port, "last_response")
            if last_resp is not None:
                prompt_tok = (
                    last_resp.tokens_used.prompt_tokens
                    if last_resp.tokens_used
                    and last_resp.tokens_used.prompt_tokens is not None
                    else 0
                )
                comp_tok = (
                    last_resp.tokens_used.completion_tokens
                    if last_resp.tokens_used
                    and last_resp.tokens_used.completion_tokens is not None
                    else 0
                )
                total_tok = (
                    last_resp.tokens_used.total_tokens
                    if last_resp.tokens_used
                    and last_resp.tokens_used.total_tokens is not None
                    else prompt_tok + comp_tok
                )
                model_name = getattr(last_resp, "model", "unknown")
                latency_ms = getattr(last_resp, "latency_ms", 0.0)
                cost = self.pricing_table.calculate_cost(
                    "groq", model_name, prompt_tok, comp_tok
                )
                telemetry = {
                    "prompt_tokens": prompt_tok,
                    "completion_tokens": comp_tok,
                    "total_tokens": total_tok,
                    "model": model_name,
                    "latency_ms": latency_ms,
                    "estimated_cost_usd": cost,
                }
        return telemetry

    def _handle_technical_conceptual_turn(
        self,
        query: str,
        route: AuthoritativeRoute,
        qt_value: str,
        budget_limit: Optional[int],
        history: Optional[Sequence[ConversationTurn]],
    ) -> SessionResult:
        decision = self.tutor_policy.decide(self.get_context(query))

        if budget_limit is not None and hasattr(self.orchestrator, "audit_port"):
            audit_port = getattr(self.orchestrator, "audit_port")
            if audit_port is not None and hasattr(audit_port, "active_budget_limit"):
                setattr(audit_port, "active_budget_limit", budget_limit)

        if history is not None:
            history_snapshot = tuple(history[-6:])
        else:
            history_snapshot = tuple(self.conversation_history[-6:])

        sess_req = SessionRequest(
            session_id=self.orchestrator.session_id,
            student_id=self.orchestrator.student_id,
            node_id=self.active_node_id,
            query=query,
            mode=GenerationMode.EXPLANATION,
            turn_index=self.orchestrator.current_turn_index,
            history=history_snapshot,
        )

        try:
            sess_res = self.orchestrator.handle_session_request(sess_req)
        except (LLMTimeoutError, LLMConnectionError, LLMBackendError) as exc:
            sess_res = SessionResult(
                session_id=self.orchestrator.session_id,
                turn_id=f"turn-err-{self.orchestrator.current_turn_index}",
                node_id=self.active_node_id,
                status=SessionResultStatus.ABSTAINED,
                response_text="El servicio de asistencia pedagógica no está disponible temporalmente (PROVIDER_UNAVAILABLE).",
                audit_report_id=None,
                abstention_reason="PROVIDER_UNAVAILABLE",
                audit_trace={"error": str(exc), "error_type": type(exc).__name__},
            )

        if sess_res.status == SessionResultStatus.ABSTAINED:
            is_budget_violation = False
            for chk in sess_res.audit_trace.get("deterministic_checks", []):
                if chk.get("check_id") == "CHECK_BUDGET_CONTAINMENT" or "BUDGET_VIOLATION" in str(chk.get("reason", "")):
                    is_budget_violation = True
                    break
            if is_budget_violation:
                sess_res = SessionResult(
                    session_id=sess_res.session_id,
                    turn_id=sess_res.turn_id,
                    node_id=sess_res.node_id,
                    status=SessionResultStatus.ABSTAINED,
                    response_text="Respuesta omitida por exceder el presupuesto pedagógico asignado (BUDGET_VIOLATION).",
                    audit_report_id=sess_res.audit_report_id,
                    abstention_reason="BUDGET_VIOLATION",
                    audit_trace=sess_res.audit_trace,
                )

        if sess_res.status == SessionResultStatus.APPROVED:
            self.conceptual_turns_completed += 1

        telemetry = self._extract_tutor_telemetry()

        event_name = "CONCEPTUAL_TURN"
        if sess_res.abstention_reason == "BUDGET_VIOLATION":
            event_name = "BUDGET_VIOLATION"
        elif sess_res.abstention_reason == "PROVIDER_UNAVAILABLE":
            event_name = "PROVIDER_UNAVAILABLE"

        self.turn_history.append(
            {
                "event": event_name,
                "node_id": self.active_node_id,
                "query": query,
                "session_status": sess_res.status.value,
                "abstention_reason": sess_res.abstention_reason,
                "audit_report_id": sess_res.audit_report_id,
                "conceptual_turns_completed": self.conceptual_turns_completed,
                "authoritative_route": route.model_dump(mode="json"),
                **telemetry,
            }
        )
        self.conversation_history.append(
            ConversationTurn(role=ConversationRole.STUDENT, content=query)
        )
        self.conversation_history.append(
            ConversationTurn(role=ConversationRole.TUTOR, content=sess_res.response_text)
        )

        updated_audit_trace = dict(sess_res.audit_trace)
        updated_audit_trace["authoritative_route"] = route.model_dump(mode="json")

        return sess_res.model_copy(
            update={
                "pedagogical_followup": decision.followup,
                "question_type": qt_value,
                "audit_trace": updated_audit_trace,
            }
        )

    def check_understanding(
        self,
        student_message: str,
        target_node_id: Optional[str] = None,
        calibrated_nli_score: float = 0.90,
    ) -> Dict[str, Any]:
        """Execute Stage 4: Verify student grasp using calibrated NLI threshold without ledger commit."""
        if target_node_id is not None:
            self.set_active_node(target_node_id)

        conceptually_sound = self.tutor_policy.evaluate_understanding(
            calibrated_nli_score
        )
        ready_for_practice = conceptually_sound

        result = {
            "conceptually_sound": conceptually_sound,
            "ready_for_practice": ready_for_practice,
            "nli_score": calibrated_nli_score,
            "threshold_applied": self.tutor_policy.config.understanding_threshold,
            "ledger_delta": 0,
        }

        self.turn_history.append(
            {
                "event": "CHECK_UNDERSTANDING",
                "node_id": self.active_node_id,
                "student_message": student_message,
                **result,
            }
        )
        return result

    def dispatch_practice(self, target_node_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute Stage 5: Resolve and dispatch practical programming challenge for active node."""
        if target_node_id is not None:
            self.set_active_node(target_node_id)

        task_id = self.tutor_policy.config.node_to_task_mapping.get(
            self.active_node_id,
            f"task_{self.active_node_id.lower().replace('-', '_')}.json",
        )

        task = None
        if self.curriculum_registry is not None:
            try:
                task = self.curriculum_registry.load_task(task_id)
            except Exception:
                task = None

        dispatch_payload: Dict[str, Any] = {
            "node_id": self.active_node_id,
            "task_id": task_id,
            "task_title": task.title if task else None,
            "description": task.description if task else "Implement practical task.",
            "required_artifacts": (
                [req.model_dump(mode="json") for req in task.required_artifacts]
                if task
                else []
            ),
        }

        self.turn_history.append(
            {
                "event": "PRACTICE_DISPATCH",
                "node_id": self.active_node_id,
                "task_id": task_id,
            }
        )
        return dispatch_payload

    def submit_practice(
        self,
        artifact_path_or_request: Union[str, PracticeRequest],
        task_id: Optional[str] = None,
        rubric_id: Optional[str] = None,
    ) -> PracticeResult:
        """Execute Stage 6 to 8: Sandbox execution, deterministic assessment, and evidence ingestion."""
        res = self.orchestrator.handle_practical_submission(
            artifact_path_or_request,
            task_id=task_id,
            rubric_id=rubric_id,
        )

        self.practice_attempts_count += 1
        if res.assessment_result is not None:
            self.last_assessment_result = res.assessment_result
            passed = bool(res.assessment_result.aggregation.passed)
            self.last_assessment_verdict = "PASS" if passed else "FAIL"
        else:
            self.last_assessment_verdict = "FAIL"

        self.turn_history.append(
            {
                "event": "PRACTICE_SUBMISSION",
                "node_id": self.active_node_id,
                "status": res.status.value,
                "verdict": self.last_assessment_verdict,
                "evidence_record_id": res.evidence_record_id,
                "rejection_reason": res.rejection_reason,
            }
        )
        return res

    def derive_state(self) -> StudentState:
        """Execute Stage 9: Sovereign state projection from the authoritative ledger."""
        now = datetime.now(timezone.utc)
        return self.orchestrator._derive_state(now)

    def render_feedback(self, practice_result: Optional[PracticeResult] = None) -> str:
        """Execute Stage 10: Render structured, factual feedback strictly based on AssessmentResult.

        Enforces TUT-03: Zero solution code is ever revealed.
        """
        asmt = (
            practice_result.assessment_result
            if practice_result and practice_result.assessment_result
            else self.last_assessment_result
        )
        if asmt is None:
            return "No se dispone de resultados de evaluación para generar retroalimentación."

        passed = asmt.aggregation.passed
        overall_level = (
            asmt.aggregation.overall_level.name
            if asmt.aggregation.overall_level
            else "UNKNOWN"
        )
        verdict_str = "APROBADO (PASS)" if passed else "NO SUPERADO (FAIL)"

        lines = [
            "### 📋 Informe Pedagógico de Evaluación Determinista",
            "",
            f"- **Veredicto:** {verdict_str}",
            f"- **Nivel Alcanzado:** {overall_level}",
            f"- **Identificador de Tarea:** `{asmt.task.specification_id}`",
            f"- **Hash Criptográfico de Evaluación:** `{asmt.assessment_digest}`",
            "",
            "#### 🔍 Desglose por Dimensiones:",
        ]

        for dim in asmt.dimension_evaluations:
            status_symbol = "✅" if dim.passed_minimum else "❌"
            level_name = dim.assigned_level.name if dim.assigned_level else "UNASSESSED"
            lines.append(
                f"- {status_symbol} **{dim.dimension_id}**: {level_name} — *{dim.evaluation_rationale}*"
            )

        lines.append("")
        if passed:
            lines.append(
                "🎉 **¡Felicitaciones!** Has demostrado competencia técnica en este nodo. "
                "Las correlaciones posteriores en el grafo curricular han sido desbloqueadas."
            )
        else:
            lines.append(
                "💡 **Orientación Pedagógica:** Revisa las dimensiones marcadas como no superadas. "
                "Consulta el material de referencia autorizado del curso antes de intentar una nueva entrega."
            )

        return "\n".join(lines)

    def handle_post_feedback_clarification(self, student_query: str) -> str:
        """Clarification 3: Provide conceptual explanation on failed dimensions without revealing solution.

        Enforces TUT-03 (no code disclosure) and ResponseBudgetPolicy.SHORT.
        """
        asmt = self.last_assessment_result
        failed_dims = (
            [d for d in asmt.dimension_evaluations if not d.passed_minimum]
            if asmt
            else []
        )
        failed_names = (
            ", ".join(d.dimension_id for d in failed_dims) or "la dimensión evaluada"
        )

        return (
            f"Respecto a tu consulta sobre {failed_names}: la evaluación determinista verificó "
            f"los límites operacionales y la especificación formal del contrato Hoare. "
            f"Debes asegurar que el flujo de procesamiento respete estrictamente los tamaños de buffer "
            f"y los tipos de datos requeridos por la consigna técnica, sin desbordar memoria."
        )
