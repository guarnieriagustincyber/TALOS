"""Integration tests for SemanticRouter, DeterministicPolicyValidator, and StudyLoop routing."""

import pytest
from typing import Any, Dict, List, Tuple

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
    TokenUsage,
)
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.generation.parser import GenerationOutputParser
from study_engine.llm.backends import MockBackend, ProviderCompletion
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
from study_engine.tutor.policy_validator import DeterministicPolicyValidator
from study_engine.tutor.semantic_router import IntentContract, IntentType, SemanticRouter


class _MockTutorPort:
    def __init__(self) -> None:
        self._parser = GenerationOutputParser()

    def generate_tutoring(self, request: GenerationRequest) -> GenerationResponse:
        return self._parser.parse(
            RawGenerationResult(
                raw_content="Un puntero en C almacena la dirección de memoria de una variable [E1]."
            ),
            request,
        )


class _MockAuditPort:
    def __init__(self) -> None:
        self.audited_requests: List[GenerationRequest] = []

    def audit_response(
        self, request: GenerationRequest, response: GenerationResponse
    ) -> ForensicAuditReport:
        self.audited_requests.append(request)
        return ForensicAuditReport(
            audit_id="audit-sem-test",
            request_id=request.request_id,
            notebook_id=request.notebook_id,
            overall_verdict=AuditVerdict.APPROVED,
            deterministic_checks=(
                DeterministicAuditCheck(
                    check_id="check-1",
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.CRITICAL,
                    reason="Audited strictly under S4.4",
                ),
            ),
            audit_latency_ms=1.0,
            auditor_backend="sem-audit-test",
        )


class _MockRetrievalPort:
    def retrieve_evidence(
        self, query: str, node_id: str, registry: Any, top_k: int = 5
    ) -> List[ScoredCandidate]:
        return [
            ScoredCandidate(
                chunk_id="chunk-c-ptr",
                document_id="doc-c-ptr",
                source_id="src-c-ptr",
                notebook_id="nb-c-ptr",
                rank=1,
                score=0.95,
                retrieval_method="semantic_test",
                content="Los punteros en C almacenan direcciones de memoria.",
            )
        ]


def _build_test_roadmap() -> CurricularRoadmap:
    node_ptr = RoadmapNode(
        node_id="SEC-01-C-PTR",
        title="Punteros en C",
        description="Conceptos fundamentales de punteros y aritmética de direcciones.",
        node_type=NodeType.TOPIC,
        notebook_id="nb-c-ptr",
        priority=1,
    )
    node_mem = RoadmapNode(
        node_id="SEC-02-C-MEM",
        title="Gestión de Memoria Dinámica",
        description="malloc, free y heap allocation.",
        node_type=NodeType.TOPIC,
        notebook_id="nb-c-mem",
        priority=1,
    )
    nodes = {"SEC-01-C-PTR": node_ptr, "SEC-02-C-MEM": node_mem}
    dependencies = (
        RoadmapDependency(
            source_node_id="SEC-01-C-PTR",
            target_node_id="SEC-02-C-MEM",
            dependency_type=DependencyType.HARD,
        ),
    )
    return CurricularRoadmap(
        roadmap_id="sem-roadmap",
        title="Semantic Router Test Roadmap",
        version="1.0.0",
        nodes=nodes,
        dependencies=dependencies,
        canonical_revision_id=compute_canonical_revision_id(
            "sem-roadmap", "Semantic Router Test Roadmap", "1.0.0", nodes, dependencies
        ),
    )


def _build_study_loop(mock_backend: MockBackend) -> Tuple[StudyLoopController, _MockAuditPort]:
    roadmap = _build_test_roadmap()
    requirement = EvidenceRequirement(
        requirement_id="req-sem",
        evidence_type=EvidenceType.CODE_EXECUTION,
        min_count=1,
        min_score=0.8,
    )
    criteria = NodeAssessmentCriteria(
        criteria_id="crit-sem",
        target_node_type=NodeType.TOPIC,
        requirements=(requirement,),
    )
    defaults = {NodeType.TOPIC: criteria}
    policy = AssessmentPolicy(
        policy_id="sem-policy",
        title="Semantic Test Policy",
        version="1.0.0",
        default_criteria=defaults,
        node_overrides={},
        canonical_policy_id=compute_canonical_policy_id(
            "sem-policy", "Semantic Test Policy", "1.0.0", defaults, {}
        ),
    )
    audit = _MockAuditPort()
    orchestrator = SessionOrchestrator(
        session_id="sem-session-1",
        student_id="student-1",
        roadmap=roadmap,
        policy=policy,
        ledger=EvidenceLedger(),
        retrieval_port=_MockRetrievalPort(),
        tutor_port=_MockTutorPort(),
        audit_port=audit,
    )
    orchestrator.start_session()
    semantic_router = SemanticRouter(local_backend=mock_backend)
    controller = StudyLoopController(
        orchestrator=orchestrator,
        active_node_id="SEC-01-C-PTR",
        semantic_router=semantic_router,
    )
    return controller, audit


def test_semantic_router_interpretation_json_parsing():
    json_response = """
    {
        "intent": "study_navigation",
        "action": "start_current_curriculum",
        "needs_evidence": false,
        "needs_curriculum": true,
        "needs_execution": false,
        "needs_clarification": false,
        "entities": ["punteros"],
        "references": [],
        "confidence": 0.95
    }
    """
    mock_backend = MockBackend(canned_text=json_response)
    router = SemanticRouter(local_backend=mock_backend)
    intent = router.interpret("por donde empezamos?", {"active_node": "SEC-01-C-PTR"})

    assert intent.intent == IntentType.STUDY_NAVIGATION
    assert intent.action == "start_current_curriculum"
    assert intent.needs_curriculum is True
    assert intent.needs_evidence is False
    assert intent.confidence == 0.95


def test_semantic_router_fallback_on_corrupt_output():
    mock_backend = MockBackend(canned_text="This is not valid JSON!")
    router = SemanticRouter(local_backend=mock_backend)

    # Corrupt output on known heuristic navigation query -> falls back to navigation safely
    intent_nav = router.interpret("por donde empezamos?", {"active_node": "SEC-01-C-PTR"})
    assert intent_nav.intent == IntentType.STUDY_NAVIGATION
    assert intent_nav.needs_curriculum is True
    assert intent_nav.needs_evidence is False

    # Corrupt output on arbitrary ambiguous query -> falls back to CLARIFICATION_REQUEST (NEVER ungrounded technical)
    intent_ambiguous = router.interpret("una query totalmente ambigua y desconocida", {"active_node": "SEC-01-C-PTR"})
    assert intent_ambiguous.intent == IntentType.CLARIFICATION_REQUEST
    assert intent_ambiguous.needs_evidence is False
    assert intent_ambiguous.needs_clarification is True


def test_policy_validator_rules():
    roadmap = _build_test_roadmap()
    validator = DeterministicPolicyValidator(roadmap=roadmap, current_node="SEC-01-C-PTR")

    # Greeting
    greeting_intent = IntentContract(
        intent=IntentType.GREETING,
        action="greet",
        needs_evidence=False,
        needs_curriculum=False,
        confidence=1.0,
    )
    valid, reason = validator.validate(greeting_intent)
    assert valid is True
    assert reason == "greeting_allowed"

    # Navigation valid
    nav_intent = IntentContract(
        intent=IntentType.STUDY_NAVIGATION,
        action="start_current_curriculum",
        needs_evidence=False,
        needs_curriculum=True,
        confidence=0.9,
    )
    valid, reason = validator.validate(nav_intent)
    assert valid is True
    assert reason == "navigation_allowed"

    # Navigation invalid when active node is None or not in roadmap
    invalid_validator = DeterministicPolicyValidator(roadmap=roadmap, current_node=None)
    valid, reason = invalid_validator.validate(nav_intent)
    assert valid is False
    assert reason == "no_active_node"

    invalid_node_validator = DeterministicPolicyValidator(roadmap=roadmap, current_node="UNKNOWN-NODE")
    valid, reason = invalid_node_validator.validate(nav_intent)
    assert valid is False
    assert reason == "node_not_in_roadmap"


def test_study_loop_navigation_turn_without_evidence_search():
    nav_json = """
    {
        "intent": "study_navigation",
        "action": "start_current_curriculum",
        "needs_evidence": false,
        "needs_curriculum": true,
        "needs_execution": false,
        "needs_clarification": false,
        "entities": [],
        "references": [],
        "confidence": 0.92
    }
    """
    mock_backend = MockBackend(canned_text=nav_json)
    controller, audit = _build_study_loop(mock_backend)

    result = controller.handle_conceptual_turn("por donde empezamos?")

    assert result.status == SessionResultStatus.APPROVED
    # question_type is the canonical legacy projection consumed by the UI.
    assert result.question_type == "curricular"
    assert "SEC-01-C-PTR" in result.response_text
    assert result.audit_trace.get("verdict") == "INTENT_VALIDATED"
    # S4.4 audit was NOT invoked for study navigation
    assert len(audit.audited_requests) == 0


def test_study_loop_technical_question_with_s4_4_audit():
    tech_json = """
    {
        "intent": "technical_question",
        "action": "explain_concept",
        "needs_evidence": true,
        "needs_curriculum": false,
        "needs_execution": false,
        "needs_clarification": false,
        "entities": ["puntero"],
        "references": [],
        "confidence": 0.98
    }
    """
    mock_backend = MockBackend(canned_text=tech_json)
    controller, audit = _build_study_loop(mock_backend)

    result = controller.handle_conceptual_turn("qué es un puntero?")

    assert result.status == SessionResultStatus.APPROVED
    assert result.question_type == "technical"
    assert "puntero" in result.response_text.lower()
    # S4.4 forensic audit WAS invoked
    assert len(audit.audited_requests) == 1
