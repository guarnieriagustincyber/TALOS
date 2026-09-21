"""Integration coverage for deterministic TutorPolicy follow-up metadata."""

from typing import Any, Dict, List, Tuple

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
from study_engine.roadmap.contracts import (
    CurricularRoadmap,
    DependencyType,
    NodeType,
    RoadmapDependency,
    RoadmapNode,
)
from study_engine.roadmap.engine import compute_canonical_revision_id
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


class _RetrievalPort:
    def retrieve_evidence(
        self, query: str, node_id: str, registry: Any, top_k: int = 5
    ) -> List[ScoredCandidate]:
        return [
            ScoredCandidate(
                chunk_id="chunk-a",
                document_id="doc-a",
                source_id="source-a",
                notebook_id="nb-a",
                rank=1,
                score=1.0,
                retrieval_method="test",
                content="El nodo A contiene el concepto factual de prueba.",
            )
        ]


class _TutorPort:
    def __init__(self) -> None:
        self._parser = GenerationOutputParser()

    def generate_tutoring(self, request: GenerationRequest) -> GenerationResponse:
        return self._parser.parse(
            RawGenerationResult(
                raw_content="El nodo A contiene el contenido factual [E1]."
            ),
            request,
        )


class _RecordingAuditPort:
    def __init__(self) -> None:
        self.audited_texts: List[str] = []

    def audit_response(
        self, request: GenerationRequest, response: GenerationResponse
    ) -> ForensicAuditReport:
        self.audited_texts.append(response.raw_content)
        return ForensicAuditReport(
            audit_id="audit-followup",
            request_id=request.request_id,
            notebook_id=request.notebook_id,
            overall_verdict=AuditVerdict.APPROVED,
            deterministic_checks=(
                DeterministicAuditCheck(
                    check_id="test-approved",
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.CRITICAL,
                    reason="The factual response was the only audited payload.",
                ),
            ),
            audit_latency_ms=0.0,
            auditor_backend="followup-test",
        )


def _build_controller() -> Tuple[StudyLoopController, _RecordingAuditPort]:
    node_a = RoadmapNode(
        node_id="A",
        title="Fundamentos A",
        description="Nodo curricular inicial.",
        node_type=NodeType.TOPIC,
        notebook_id="nb-a",
        priority=1,
        metadata={"code_example_available": True},
    )
    node_b = RoadmapNode(
        node_id="B",
        title="Profundización B",
        description="Primer nodo descendiente.",
        node_type=NodeType.TOPIC,
        notebook_id="nb-b",
        priority=1,
    )
    node_c = RoadmapNode(
        node_id="C",
        title="Profundización C",
        description="Segundo nodo descendiente.",
        node_type=NodeType.TOPIC,
        notebook_id="nb-c",
        priority=2,
    )
    nodes: Dict[str, RoadmapNode] = {"A": node_a, "B": node_b, "C": node_c}
    dependencies = (
        RoadmapDependency(
            source_node_id="A", target_node_id="C", dependency_type=DependencyType.HARD
        ),
        RoadmapDependency(
            source_node_id="A", target_node_id="B", dependency_type=DependencyType.HARD
        ),
    )
    roadmap = CurricularRoadmap(
        roadmap_id="followup-roadmap",
        title="Follow-up test roadmap",
        version="1.0.0",
        nodes=nodes,
        dependencies=dependencies,
        canonical_revision_id=compute_canonical_revision_id(
            "followup-roadmap", "Follow-up test roadmap", "1.0.0", nodes, dependencies
        ),
    )
    requirement = EvidenceRequirement(
        requirement_id="req",
        evidence_type=EvidenceType.CODE_EXECUTION,
        min_count=1,
        min_score=0.8,
    )
    criteria = NodeAssessmentCriteria(
        criteria_id="criteria",
        target_node_type=NodeType.TOPIC,
        requirements=(requirement,),
    )
    defaults = {NodeType.TOPIC: criteria}
    assessment_policy = AssessmentPolicy(
        policy_id="policy",
        title="Test policy",
        version="1.0.0",
        default_criteria=defaults,
        node_overrides={},
        canonical_policy_id=compute_canonical_policy_id(
            "policy", "Test policy", "1.0.0", defaults, {}
        ),
    )
    audit = _RecordingAuditPort()
    orchestrator = SessionOrchestrator(
        session_id="followup-session",
        student_id="student",
        roadmap=roadmap,
        policy=assessment_policy,
        ledger=EvidenceLedger(),
        retrieval_port=_RetrievalPort(),
        tutor_port=_TutorPort(),
        audit_port=audit,
    )
    orchestrator.start_session()
    return StudyLoopController(orchestrator=orchestrator), audit


@pytest.fixture
def controller_and_audit() -> Tuple[StudyLoopController, _RecordingAuditPort]:
    return _build_controller()


def test_followup_is_generated_deterministically(
    controller_and_audit: Tuple[StudyLoopController, _RecordingAuditPort],
) -> None:
    controller, _ = controller_and_audit

    first = controller.decide_next_action("Explicame A").followup
    second = controller.decide_next_action("Explicame A").followup

    assert first == second
    assert first is not None
    assert first.verification_question == (
        "¿Cómo explicarías con tus palabras el concepto central de Fundamentos A?"
    )
    assert first.code_example_available is True


def test_followup_is_not_submitted_to_s4_4(
    controller_and_audit: Tuple[StudyLoopController, _RecordingAuditPort],
) -> None:
    controller, audit = controller_and_audit

    result = controller.handle_conceptual_turn("Explicame A")

    assert result.pedagogical_followup is not None
    assert audit.audited_texts == ["El nodo A contiene el contenido factual [E1]."]
    assert "Fundamentos A" not in audit.audited_texts[0]
    assert "Profundización B" not in audit.audited_texts[0]


def test_followup_exposes_dag_deepening_options(
    controller_and_audit: Tuple[StudyLoopController, _RecordingAuditPort],
) -> None:
    controller, _ = controller_and_audit

    followup = controller.decide_next_action("Explicame A").followup

    assert followup is not None
    assert followup.deepen_options == ("B", "C")


def test_followup_next_node_is_a_curriculum_dependent(
    controller_and_audit: Tuple[StudyLoopController, _RecordingAuditPort],
) -> None:
    controller, _ = controller_and_audit

    followup = controller.decide_next_action("Explicame A").followup
    outgoing = {
        dependency.target_node_id
        for dependency in controller.orchestrator.roadmap.dependencies
        if dependency.source_node_id == "A"
    }

    assert followup is not None
    assert followup.next_node_id == "B"
    assert set(followup.deepen_options) == outgoing
    assert followup.next_node_id in outgoing
