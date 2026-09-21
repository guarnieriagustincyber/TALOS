"""Phase 3 Test Suite: StudyLoop as Central Orchestrator & AuthoritativeRoute Invariants.

Verifies the core Phase 3 invariants:
1. Every input produces exactly one AuthoritativeRoute before any handler execution.
2. Deep immutability of AuthoritativeRoute (frozen=True, attributes and collections immutable).
3. Derived permissions: execution_allowed and mutation_allowed are derived by policy,
   never influenced by LLM confidence or requested flags.
4. Route monotonicity / No privilege escalation:
   - STUDY_NAVIGATION cannot trigger epistemic retrieval.
   - CLARIFICATION_REQUEST cannot trigger retrieval, execution, or mutation.
   - TECHNICAL_QUESTION requires the full Retrieval -> ContextPacker -> Generation -> S4.4 audit pipeline.
5. Zero side-effects on consultative turns:
   - StudentState (at fixed reference time), EvidenceLedger, and Roadmap nodes are unchanged before and after.
6. Fail-closed behavior on REJECTED routes.
7. Observability: AuthoritativeRoute is captured in audit_trace and turn_history as evidence.
8. Per-turn consistency: legacy/fallback queries (no router) resolve through the same AuthoritativeRoute contract.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pytest

from study_engine.audit.contracts import (
    AuditVerdict,
    CheckSeverity,
    CheckStatus,
    DeterministicAuditCheck,
    ForensicAuditReport,
)
from study_engine.contracts.generation import (
    GenerationRequest,
    GenerationResponse,
    RawGenerationResult,
)
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.generation.parser import GenerationOutputParser
from study_engine.llm.backends import MockBackend
from study_engine.roadmap.contracts import (
    CurricularRoadmap,
    DependencyType,
    NodeType,
    RoadmapDependency,
    RoadmapNode,
)
from study_engine.roadmap.engine import compute_canonical_revision_id
from study_engine.session.contracts import SessionResultStatus
from study_engine.session.orchestrator import SessionOrchestrator
from study_engine.session.study_loop import StudyLoopController
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.policy_contracts import (
    AssessmentPolicy,
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
)
from study_engine.state.policy_engine import compute_canonical_policy_id
from study_engine.tutor.policy_validator import (
    AuthoritativeRoute,
    DeterministicPolicyValidator,
    RouteKind,
)
from study_engine.tutor.semantic_router import (
    IntentContract,
    IntentType,
    SemanticRouter,
)


# ---------------------------------------------------------------------------
# Test Doubles / Fixtures
# ---------------------------------------------------------------------------

class _TrackingAuditPort:
    def __init__(self) -> None:
        self.audited_requests: List[GenerationRequest] = []

    def audit_response(
        self, request: GenerationRequest, response: GenerationResponse
    ) -> ForensicAuditReport:
        self.audited_requests.append(request)
        return ForensicAuditReport(
            audit_id="audit-phase3-orchestration",
            request_id=request.request_id,
            notebook_id=request.notebook_id,
            overall_verdict=AuditVerdict.APPROVED,
            deterministic_checks=(
                DeterministicAuditCheck(
                    check_id="check-p3-s4-4",
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.CRITICAL,
                    reason="Audited strictly under S4.4 in Phase 3",
                ),
            ),
            audit_latency_ms=1.5,
            auditor_backend="phase3-audit-verifier",
        )


class _TrackingRetrievalPort:
    def __init__(self) -> None:
        self.retrieval_queries: List[str] = []

    def retrieve_evidence(
        self, query: str, node_id: str, registry: Any, top_k: int = 5
    ) -> List[ScoredCandidate]:
        self.retrieval_queries.append(query)
        return [
            ScoredCandidate(
                chunk_id="chunk-p3-1",
                document_id="doc-p3-1",
                source_id="src-p3-1",
                notebook_id="nb-c-ptr",
                rank=1,
                score=0.98,
                retrieval_method="hybrid_p3",
                content="Los punteros en C permiten acceso directo a memoria.",
            )
        ]


class _MockTutorPort:
    def __init__(self) -> None:
        self._parser = GenerationOutputParser()
        self.generated_queries: List[str] = []

    def generate_tutoring(self, request: GenerationRequest) -> GenerationResponse:
        self.generated_queries.append(request.query)
        return self._parser.parse(
            RawGenerationResult(
                raw_content="Un puntero almacena una dirección física de memoria [E1]."
            ),
            request,
        )


def _build_test_roadmap() -> CurricularRoadmap:
    nodes = {
        "SEC-01-C-PTR": RoadmapNode(
            node_id="SEC-01-C-PTR",
            title="Punteros en C",
            description="Aritmética de punteros y memoria.",
            node_type=NodeType.TOPIC,
            notebook_id="nb-c-ptr",
            priority=1,
        ),
        "SEC-02-C-MEM": RoadmapNode(
            node_id="SEC-02-C-MEM",
            title="Gestión de Memoria",
            description="Heap, stack y fugas.",
            node_type=NodeType.TOPIC,
            notebook_id="nb-c-ptr",
            priority=2,
        ),
    }
    deps = (
        RoadmapDependency(
            source_node_id="SEC-01-C-PTR",
            target_node_id="SEC-02-C-MEM",
            dependency_type=DependencyType.HARD,
        ),
    )
    return CurricularRoadmap(
        roadmap_id="roadmap-p3",
        title="Roadmap de Fase 3",
        version="1.0.0",
        nodes=nodes,
        dependencies=deps,
        canonical_revision_id=compute_canonical_revision_id(
            "roadmap-p3", "Roadmap de Fase 3", "1.0.0", nodes, deps
        ),
    )


def _build_test_policy() -> AssessmentPolicy:
    req = EvidenceRequirement(
        requirement_id="req-p3-concept",
        evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
        min_count=1,
        min_score=0.8,
    )
    crit = NodeAssessmentCriteria(
        criteria_id="crit-p3-topic",
        target_node_type=NodeType.TOPIC,
        requirements=(req,),
        regression_threshold_failures=2,
    )
    defaults = {NodeType.TOPIC: crit}
    policy_id = "pol-p3-test"
    canon_id = compute_canonical_policy_id(
        policy_id=policy_id,
        title="Policy P3",
        version="1.0.0",
        default_criteria=defaults,
        node_overrides={},
    )
    return AssessmentPolicy(
        policy_id=policy_id,
        title="Policy P3",
        version="1.0.0",
        default_criteria=defaults,
        node_overrides={},
        canonical_policy_id=canon_id,
    )


def _build_harness(
    canned_llm_json: Optional[str] = None,
) -> tuple[StudyLoopController, _TrackingAuditPort, _TrackingRetrievalPort, EvidenceLedger, CurricularRoadmap]:
    roadmap = _build_test_roadmap()
    policy = _build_test_policy()
    ledger = EvidenceLedger()

    audit_port = _TrackingAuditPort()
    retrieval_port = _TrackingRetrievalPort()
    tutor_port = _MockTutorPort()

    orchestrator = SessionOrchestrator(
        session_id="sess-p3-test",
        student_id="student-p3",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        retrieval_port=retrieval_port,
        tutor_port=tutor_port,
        audit_port=audit_port,
    )
    orchestrator.start_session()

    router = None
    if canned_llm_json is not None:
        router = SemanticRouter(local_backend=MockBackend(canned_text=canned_llm_json))

    controller = StudyLoopController(
        orchestrator=orchestrator,
        active_node_id="SEC-01-C-PTR",
        semantic_router=router,
    )
    return controller, audit_port, retrieval_port, ledger, roadmap


# ---------------------------------------------------------------------------
# Test Cases: Invariants of Phase 3
# ---------------------------------------------------------------------------

def test_authoritative_route_deep_immutability():
    """Invariant 2 & 3: AuthoritativeRoute is deeply immutable and rejects any mutation."""
    validator = DeterministicPolicyValidator(roadmap=_build_test_roadmap(), current_node="SEC-01-C-PTR")
    route = validator.resolve_from_intent_type(IntentType.TECHNICAL_QUESTION)

    assert route.route_kind == RouteKind.TECHNICAL
    assert route.needs_evidence is True
    assert route.execution_allowed is False
    assert route.mutation_allowed is False

    with pytest.raises(Exception):
        # Attribute assignment must fail due to frozen config
        route.action = "tampered_action"  # type: ignore[misc]

    with pytest.raises(Exception):
        route.execution_allowed = True  # type: ignore[misc]

    with pytest.raises(Exception):
        route.mutation_allowed = True  # type: ignore[misc]


def test_derived_permissions_cannot_be_injected_by_llm():
    """Invariant 3 & 4: LLM requesting execution/mutation/evidence is completely ignored."""
    adversarial_intent = IntentContract(
        intent=IntentType.STUDY_NAVIGATION,
        action="start_current_curriculum",
        needs_evidence=True,        # Untrusted injection
        needs_curriculum=True,
        needs_execution=True,       # Untrusted injection
        needs_clarification=False,
        entities=["exploit"],
        references=["root"],
        confidence=1.0,             # Confidence grants zero permissions
    )
    validator = DeterministicPolicyValidator(roadmap=_build_test_roadmap(), current_node="SEC-01-C-PTR")
    route = validator.resolve(adversarial_intent)

    # Derived solely from policy: STUDY_NAVIGATION never gets execution or evidence
    assert route.route_kind == RouteKind.NAVIGATION
    assert route.needs_evidence is False
    assert route.needs_execution is False
    assert route.execution_allowed is False
    assert route.mutation_allowed is False


def test_study_navigation_never_calls_retrieval_or_audit():
    """Invariant 4: STUDY_NAVIGATION answers from curriculum/state with 0 retrieval and 0 S4.4 audit."""
    nav_json = """{
        "intent": "study_navigation",
        "action": "start_current_curriculum",
        "needs_evidence": false,
        "needs_curriculum": true,
        "needs_execution": false,
        "needs_clarification": false,
        "confidence": 0.95
    }"""
    controller, audit_port, retrieval_port, ledger, roadmap = _build_harness(nav_json)

    res = controller.handle_conceptual_turn("¿por dónde empezamos?")

    assert res.status == SessionResultStatus.APPROVED
    assert res.question_type == "curricular"
    assert "SEC-01-C-PTR" in res.response_text
    # 0 retrieval calls
    assert len(retrieval_port.retrieval_queries) == 0
    # 0 S4.4 audit calls
    assert len(audit_port.audited_requests) == 0
    # Trace contains authoritative route evidence
    route_trace = res.audit_trace.get("authoritative_route")
    assert route_trace is not None
    assert route_trace["route_kind"] == "navigation"
    assert route_trace["needs_evidence"] is False
    assert route_trace["execution_allowed"] is False
    assert route_trace["mutation_allowed"] is False


def test_clarification_turn_has_zero_retrieval_execution_or_mutation():
    """Invariant 4 & 5: CLARIFICATION_REQUEST triggers zero retrieval, zero execution, and zero mutation."""
    clarify_json = """{
        "intent": "clarification_request",
        "action": "clarify_query",
        "needs_evidence": false,
        "needs_curriculum": false,
        "needs_execution": false,
        "needs_clarification": true,
        "confidence": 0.3
    }"""
    controller, audit_port, retrieval_port, ledger, roadmap = _build_harness(clarify_json)

    before_ledger_len = ledger.total_entries
    res = controller.handle_conceptual_turn("¿y eso?")

    assert res.status == SessionResultStatus.APPROVED
    assert len(retrieval_port.retrieval_queries) == 0
    assert len(audit_port.audited_requests) == 0
    assert ledger.total_entries == before_ledger_len

    route_trace = res.audit_trace.get("authoritative_route")
    assert route_trace is not None
    assert route_trace["route_kind"] == "clarification"
    assert route_trace["needs_evidence"] is False
    assert route_trace["execution_allowed"] is False
    assert route_trace["mutation_allowed"] is False


def test_technical_question_strictly_enforces_retrieval_generation_and_s4_4_audit():
    """Invariant 4: TECHNICAL_QUESTION strictly traverses Retrieval -> Generation -> S4.4 Audit."""
    tech_json = """{
        "intent": "technical_question",
        "action": "explain_concept",
        "needs_evidence": true,
        "needs_curriculum": false,
        "needs_execution": false,
        "needs_clarification": false,
        "confidence": 0.99
    }"""
    controller, audit_port, retrieval_port, ledger, roadmap = _build_harness(tech_json)

    res = controller.handle_conceptual_turn("¿qué es un puntero?")

    assert res.status == SessionResultStatus.APPROVED
    assert res.question_type == "technical"
    # Retrieval port was invoked
    assert len(retrieval_port.retrieval_queries) == 1
    assert retrieval_port.retrieval_queries[0] == "¿qué es un puntero?"
    # S4.4 Forensic Audit was invoked
    assert len(audit_port.audited_requests) == 1
    assert res.audit_report_id == "audit-phase3-orchestration"

    route_trace = res.audit_trace.get("authoritative_route")
    assert route_trace is not None
    assert route_trace["route_kind"] == "technical"
    assert route_trace["needs_evidence"] is True
    assert route_trace["execution_allowed"] is False
    assert route_trace["mutation_allowed"] is False


def test_consultative_turns_never_mutate_state_ledger_or_roadmap():
    """Invariant 5: Consultative turns (Greeting, Navigation, Clarification, Technical) never mutate system state."""
    tech_json = """{
        "intent": "technical_question",
        "action": "explain_concept",
        "needs_evidence": true,
        "needs_curriculum": false,
        "needs_execution": false,
        "needs_clarification": false,
        "confidence": 0.99
    }"""
    controller, _, _, ledger, roadmap = _build_harness(tech_json)

    ref_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    before_ledger_len = ledger.total_entries
    before_state = controller.orchestrator._derive_state(ref_time)
    before_node_keys = set(roadmap.nodes.keys())

    # Run technical turn
    controller.handle_conceptual_turn("¿cómo funciona la memoria?")

    after_ledger_len = ledger.total_entries
    after_state = controller.orchestrator._derive_state(ref_time)
    after_node_keys = set(roadmap.nodes.keys())

    assert after_ledger_len == before_ledger_len
    assert after_state.canonical_state_id == before_state.canonical_state_id
    assert after_node_keys == before_node_keys


def test_rejected_routes_fail_closed_without_handler_execution():
    """Invariant 6: Action tampering or illegal intent is rejected fail-closed immediately."""
    tampered_json = """{
        "intent": "technical_question",
        "action": "execute_code",
        "needs_evidence": false,
        "needs_curriculum": false,
        "needs_execution": true,
        "needs_clarification": false,
        "confidence": 1.0
    }"""
    controller, audit_port, retrieval_port, _, _ = _build_harness(tampered_json)

    res = controller.handle_conceptual_turn("executing arbitrary code")

    assert res.status == SessionResultStatus.ABSTAINED
    assert "INVALID_INTENT" in (res.abstention_reason or "")
    assert len(retrieval_port.retrieval_queries) == 0
    assert len(audit_port.audited_requests) == 0

    route_trace = res.audit_trace.get("authoritative_route")
    assert route_trace is not None
    assert route_trace["route_kind"] == "rejected"
    assert route_trace["rejected_reason"] == "forbidden_action:execute_code"
    assert route_trace["execution_allowed"] is False
    assert route_trace["mutation_allowed"] is False


def test_legacy_or_fallback_resolution_produces_identical_authoritative_route():
    """Invariant 8: When no SemanticRouter is configured, fallback resolves through canonical AuthoritativeRoute."""
    controller, _, _, _, _ = _build_harness(canned_llm_json=None)

    # Greeting via fallback
    res_greet = controller.handle_conceptual_turn("hola")
    assert res_greet.status == SessionResultStatus.APPROVED
    assert res_greet.question_type == "greeting"
    route_greet = res_greet.audit_trace.get("authoritative_route")
    assert route_greet is not None
    assert route_greet["route_kind"] == "greeting"
    assert route_greet["action"] == "greet_student"
    assert route_greet["execution_allowed"] is False
    assert route_greet["mutation_allowed"] is False

    # Curricular via fallback
    res_nav = controller.handle_conceptual_turn("qué tema sigue")
    assert res_nav.status == SessionResultStatus.APPROVED
    assert res_nav.question_type == "curricular"
    route_nav = res_nav.audit_trace.get("authoritative_route")
    assert route_nav is not None
    assert route_nav["route_kind"] == "navigation"
    assert route_nav["action"] == "start_current_curriculum"


def test_observability_contains_authoritative_route_in_turn_history():
    """Invariant 7: Every completed turn logs authoritative_route in turn_history."""
    tech_json = """{
        "intent": "technical_question",
        "action": "explain_concept",
        "needs_evidence": true,
        "needs_curriculum": false,
        "needs_execution": false,
        "needs_clarification": false,
        "confidence": 0.95
    }"""
    controller, _, _, _, _ = _build_harness(tech_json)

    controller.handle_conceptual_turn("explica punteros")

    assert len(controller.turn_history) > 0
    conceptual_record = next(
        r for r in controller.turn_history if r.get("event") == "CONCEPTUAL_TURN"
    )
    assert "authoritative_route" in conceptual_record
    assert conceptual_record["authoritative_route"]["route_kind"] == "technical"
    assert conceptual_record["authoritative_route"]["execution_allowed"] is False
    assert conceptual_record["authoritative_route"]["mutation_allowed"] is False
