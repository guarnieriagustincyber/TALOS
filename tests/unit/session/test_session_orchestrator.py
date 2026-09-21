"""Unit tests for SessionOrchestrator core engine in Subsystem S5.3."""

from datetime import datetime, timezone
from typing import Dict, Tuple

from study_engine.roadmap.contracts import (
    CurricularRoadmap,
    DependencyType,
    NodeType,
    RoadmapDependency,
    RoadmapNode,
)
from study_engine.roadmap.engine import compute_canonical_revision_id
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.policy_contracts import (
    AssessmentPolicy,
    EvidenceOutcome,
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
)
from study_engine.state.policy_engine import compute_canonical_policy_id
from study_engine.audit.contracts import (
    AuditVerdict,
    CheckSeverity,
    CheckStatus,
    DeterministicAuditCheck,
    ForensicAuditReport,
)
from study_engine.contracts.generation import (
    GenerationMode,
    GenerationRequest,
    GenerationResponse,
    ParsedCitation,
    ResponseValidationStatus,
)
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.session.contracts import (
    RecoveryDisposition,
    SessionRequest,
    SessionResult,
    SessionResultStatus,
    SessionStatus,
    StudentInput,
    StudentInputType,
    TurnActionType,
)
from study_engine.session.orchestrator import SessionOrchestrator
from study_engine.session.ports import (
    AuditPort,
    RetrievalPort,
    TutorPort,
)


def _make_test_fixtures() -> Tuple[
    CurricularRoadmap, AssessmentPolicy, EvidenceLedger
]:

    n_a = RoadmapNode(
        node_id="node-a",
        title="Topic A",
        description="Root",
        node_type=NodeType.TOPIC,
        notebook_id="nb-1",
        priority=1,
    )
    n_b = RoadmapNode(
        node_id="node-b",
        title="Topic B",
        description="Child",
        node_type=NodeType.TOPIC,
        notebook_id="nb-1",
        priority=2,
    )
    nodes: Dict[str, RoadmapNode] = {"node-a": n_a, "node-b": n_b}
    deps: Tuple[RoadmapDependency, ...] = (
        RoadmapDependency(
            source_node_id="node-a",
            target_node_id="node-b",
            dependency_type=DependencyType.HARD,
        ),
    )
    rm_id = compute_canonical_revision_id("rm", "Roadmap", "1.0", nodes, deps)
    roadmap = CurricularRoadmap(
        roadmap_id="rm",
        title="Roadmap",
        version="1.0",
        nodes=nodes,
        dependencies=deps,
        canonical_revision_id=rm_id,
    )

    req = EvidenceRequirement(
        requirement_id="req-1",
        evidence_type=EvidenceType.CODE_EXECUTION,
        min_count=1,
        min_score=0.8,
    )
    crit = NodeAssessmentCriteria(
        criteria_id="crit-topic",
        target_node_type=NodeType.TOPIC,
        requirements=(req,),
        regression_threshold_failures=2,
    )
    defaults = {NodeType.TOPIC: crit}
    pol_id = compute_canonical_policy_id("pol", "Policy", "1.0", defaults, {})
    policy = AssessmentPolicy(
        policy_id="pol",
        title="Policy",
        version="1.0",
        default_criteria=defaults,
        node_overrides={},
        canonical_policy_id=pol_id,
    )
    ledger = EvidenceLedger()
    return roadmap, policy, ledger


def test_session_start_initialization() -> None:
    """Verify session start focuses on first available node and sets FSM."""
    roadmap, policy, ledger = _make_test_fixtures()
    orch = SessionOrchestrator("s-1", "alice", roadmap, policy, ledger)

    assert orch.fsm.current_status == SessionStatus.CREATED

    out = orch.start_session()
    current_status: SessionStatus = orch.fsm.current_status
    assert current_status == SessionStatus.WAITING_FOR_STUDENT
    assert out.turn_index == 0
    assert out.resolved_target_node_id == "node-a"
    assert out.action_type == TurnActionType.CHALLENGE
    assert len(out.student_state_id) == 64


def test_session_decision_formation() -> None:
    """Verify decide_turn creates decoupled SessionDecision."""
    roadmap, policy, ledger = _make_test_fixtures()
    orch = SessionOrchestrator("s-1", "alice", roadmap, policy, ledger)
    orch.start_session()

    s_input = StudentInput(
        input_id="in-1",
        session_id="s-1",
        turn_index=1,
        input_type=StudentInputType.QUESTION,
        content="Explain concept A",
        timestamp=datetime.now(timezone.utc),
    )

    from study_engine.state.state_engine import derive_student_state

    current_state = derive_student_state(roadmap, policy, ledger, "alice")
    decision = orch.decide_turn(s_input, current_state)

    assert decision.resolved_target_node_id == "node-a"
    assert decision.action_type == TurnActionType.EXPLAIN
    assert decision.requires_retrieval is True
    assert decision.requires_generation is True
    assert decision.requires_assessment is False


def test_session_turn_processing_and_ledger_commit() -> None:
    """HG-S5.3-08: Verify ledger append occurs and promotes student state."""
    roadmap, policy, ledger = _make_test_fixtures()
    orch = SessionOrchestrator("s-1", "alice", roadmap, policy, ledger)
    orch.start_session()

    # Student submits answer to node-a
    s_input = StudentInput(
        input_id="in-pass",
        session_id="s-1",
        turn_index=1,
        input_type=StudentInputType.ANSWER,
        content="Correct answer for Node A",
        timestamp=datetime.now(timezone.utc),
    )

    out = orch.process_turn(s_input)
    assert out.produced_evidence_id is not None
    assert out.produced_evidence_id == ledger._entries[0].record.record_id
    assert orch.fsm.current_status == SessionStatus.WAITING_FOR_STUDENT

    # Verify ledger has 1 record committed
    assert len(ledger._entries) == 1
    assert ledger._entries[0].record.node_id == "node-a"
    assert ledger._entries[0].record.outcome == EvidenceOutcome.PASS

    # Verify Node A is proficient and Node B unlocked in projected state
    from study_engine.state.state_engine import derive_student_state

    current_state = derive_student_state(roadmap, policy, ledger, "alice")
    ns_a = current_state.get_node_state("node-a")
    assert ns_a is not None
    assert ns_a.status.value == "ASSESSED_PROFICIENT"

    ns_b = current_state.get_node_state("node-b")
    assert ns_b is not None
    assert ns_b.status.value == "AVAILABLE"


def test_session_idempotency_replay_vs_reexecution() -> None:
    """Ajuste 3: Replay exact output without duplicating ledger."""

    roadmap, policy, ledger = _make_test_fixtures()
    orch = SessionOrchestrator("s-1", "alice", roadmap, policy, ledger)
    orch.start_session()

    s_input = StudentInput(
        input_id="in-idem-1",
        session_id="s-1",
        turn_index=1,
        input_type=StudentInputType.ANSWER,
        content="Answer",
        timestamp=datetime.now(timezone.utc),
    )

    out1 = orch.process_turn(s_input)
    assert len(ledger._entries) == 1

    # Resubmit identical input_id -> Replay exact output without ledger append
    out2 = orch.process_turn(s_input)
    assert out2.turn_id == out1.turn_id
    assert out2.content == out1.content
    assert len(ledger._entries) == 1  # Not duplicated!


def test_session_terminal_command_abort() -> None:
    """Verify /abort command terminates session and updates FSM."""
    roadmap, policy, ledger = _make_test_fixtures()
    orch = SessionOrchestrator("s-1", "alice", roadmap, policy, ledger)
    orch.start_session()

    s_input = StudentInput(
        input_id="in-abort",
        session_id="s-1",
        turn_index=1,
        input_type=StudentInputType.COMMAND,
        content="/abort",
        timestamp=datetime.now(timezone.utc),
    )

    out = orch.process_turn(s_input)
    assert out.action_type == TurnActionType.SESSION_TERMINATED
    assert orch.fsm.current_status == SessionStatus.ABORTED
    assert orch.fsm.is_terminal is True


def test_session_crash_recovery_disposition() -> None:
    """Ajuste 4: Explicit recovery restores FSM from EVALUATING to WAITING."""
    roadmap, policy, ledger = _make_test_fixtures()
    orch = SessionOrchestrator("s-1", "alice", roadmap, policy, ledger)
    orch.start_session()

    # Simulate crash during evaluation
    orch.fsm.transition_to(SessionStatus.EVALUATING)
    assert orch.fsm.current_status == SessionStatus.EVALUATING

    disposition = orch.recover_session(RecoveryDisposition.RETURN_TO_WAITING)
    assert disposition == RecoveryDisposition.RETURN_TO_WAITING
    recovered_status: SessionStatus = orch.fsm.current_status
    assert recovered_status == SessionStatus.WAITING_FOR_STUDENT


# ===========================================================================
# HITO 3 TESTS: Puertos, Precondition Fail-Closed, S4.4 Abstention, Idempotencia
# ===========================================================================

from typing import Any, List, Optional


class DummyRetrievalPort:
    def __init__(self, candidates: Optional[List[ScoredCandidate]] = None) -> None:
        self.invoked = False
        self.candidates = candidates if candidates is not None else [
            ScoredCandidate(
                chunk_id="chunk-1",
                document_id="doc-1.pdf",
                source_id="src-1",
                notebook_id="nb-1",
                rank=1,
                score=0.95,
                retrieval_method="hybrid",
                content="Concept A definition grounded in facts.",
            )
        ]

    def retrieve_evidence(
        self, query: str, node_id: str, registry: Any, top_k: int = 5
    ) -> List[ScoredCandidate]:
        self.invoked = True
        return self.candidates


class DummyTutorPort:
    def __init__(self, response_text: str = "Respuesta válida [E1]") -> None:
        self.invoked = False
        self.response_text = response_text
        from study_engine.generation.parser import GenerationOutputParser
        self.parser = GenerationOutputParser()

    def generate_tutoring(
        self, request: GenerationRequest
    ) -> GenerationResponse:
        self.invoked = True
        from study_engine.contracts.generation import RawGenerationResult
        raw = RawGenerationResult(raw_content=self.response_text)
        return self.parser.parse(raw_result=raw, request=request)


class DummyAuditPort:
    def __init__(self, verdict: AuditVerdict = AuditVerdict.APPROVED) -> None:
        self.verdict = verdict

    def audit_response(
        self, request: GenerationRequest, response: GenerationResponse
    ) -> ForensicAuditReport:
        return ForensicAuditReport(
            audit_id="aud-1",
            request_id=request.request_id,
            notebook_id="nb-1",
            overall_verdict=self.verdict,
            audit_latency_ms=1.5,
            auditor_backend="dummy-auditor-v1",
            deterministic_checks=(
                DeterministicAuditCheck(
                    check_id="chk-1",
                    status=(
                        CheckStatus.PASS
                        if self.verdict == AuditVerdict.APPROVED
                        else CheckStatus.FAIL
                    ),
                    severity=CheckSeverity.CRITICAL,
                    reason=(
                        "Deterministic check verified"
                        if self.verdict == AuditVerdict.APPROVED
                        else "Deterministic check failed"
                    ),
                ),
            ),
        )


def test_session_h3_happy_path_approved() -> None:
    """Hito 3: Formative turn happy path with valid evidence, generation and S4.4 approval."""
    roadmap, policy, ledger = _make_test_fixtures()
    retrieval = DummyRetrievalPort()
    tutor = DummyTutorPort(response_text="Conforme a [E1], el concepto se define rigurosamente.")
    audit = DummyAuditPort(AuditVerdict.APPROVED)

    orch = SessionOrchestrator(
        session_id="s-h3-1",
        student_id="alice",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        retrieval_port=retrieval,
        tutor_port=tutor,
        audit_port=audit,
    )
    orch.start_session()

    req = SessionRequest(
        session_id="s-h3-1",
        student_id="alice",
        node_id="node-a",
        query="Explícame el concepto A",
        mode=GenerationMode.EXPLANATION,
        turn_index=1,
    )

    res = orch.handle_session_request(req)

    assert res.status == SessionResultStatus.APPROVED
    assert "Conforme a [E1]" in res.response_text
    assert res.audit_report_id == "aud-1"
    assert res.abstention_reason is None
    assert retrieval.invoked is True
    assert tutor.invoked is True


def test_session_h3_abstention_on_s4_4_rejection() -> None:
    """Hito 3: S4.4 rejection enforces canonical abstention (Fail-Closed, zero self-repair loop)."""
    roadmap, policy, ledger = _make_test_fixtures()
    retrieval = DummyRetrievalPort()
    tutor = DummyTutorPort(response_text="Afirmación con cita inválida [E99]")
    audit = DummyAuditPort(AuditVerdict.REJECTED_UNSUPPORTED)

    orch = SessionOrchestrator(
        session_id="s-h3-2",
        student_id="alice",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        retrieval_port=retrieval,
        tutor_port=tutor,
        audit_port=audit,
    )
    orch.start_session()

    req = SessionRequest(
        session_id="s-h3-2",
        student_id="alice",
        node_id="node-a",
        query="Explícame conjeturas no documentadas",
        mode=GenerationMode.EXPLANATION,
        turn_index=1,
    )

    res = orch.handle_session_request(req)

    assert res.status == SessionResultStatus.ABSTAINED
    assert res.abstention_reason == "REJECTED_UNSUPPORTED"
    assert "Forensic audit rejected generated response" in res.response_text
    assert res.audit_report_id == "aud-1"


def test_session_h3_fail_closed_on_locked_node() -> None:
    """Hito 3: Querying a LOCKED node aborts early (FAIL_CLOSED) before retrieval or LLM."""
    roadmap, policy, ledger = _make_test_fixtures()
    retrieval = DummyRetrievalPort()
    tutor = DummyTutorPort()

    orch = SessionOrchestrator(
        session_id="s-h3-3",
        student_id="alice",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        retrieval_port=retrieval,
        tutor_port=tutor,
    )
    orch.start_session()

    # node-b is locked because node-a is not completed
    req = SessionRequest(
        session_id="s-h3-3",
        student_id="alice",
        node_id="node-b",
        query="Explícame el nodo avanzado B",
        mode=GenerationMode.EXPLANATION,
        turn_index=1,
    )

    res = orch.handle_session_request(req)

    assert res.status == SessionResultStatus.FAIL_CLOSED
    assert res.abstention_reason == "LOCKED_NODE"
    assert "LOCKED" in res.response_text
    assert retrieval.invoked is False  # Zero retrieval resources spent!
    assert tutor.invoked is False      # Zero LLM generation!


def test_session_h3_idempotency_replay_from_receipt_store() -> None:
    """Hito 3: TurnReceiptStore replays exact cached SessionResult on repeated request."""
    roadmap, policy, ledger = _make_test_fixtures()
    retrieval = DummyRetrievalPort()
    tutor = DummyTutorPort(response_text="Respuesta determinista [E1]")

    orch = SessionOrchestrator(
        session_id="s-h3-4",
        student_id="alice",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        retrieval_port=retrieval,
        tutor_port=tutor,
    )
    orch.start_session()

    req = SessionRequest(
        session_id="s-h3-4",
        student_id="alice",
        node_id="node-a",
        query="Pregunta idéntica",
        mode=GenerationMode.EXPLANATION,
        turn_index=1,
    )

    res1 = orch.handle_session_request(req)
    assert res1.status == SessionResultStatus.APPROVED

    # Reset flags to prove second call does not re-execute retrieval or tutor
    retrieval.invoked = False
    tutor.invoked = False

    res2 = orch.handle_session_request(req)
    assert res2.turn_id == res1.turn_id
    assert res2.response_text == res1.response_text
    assert res2.status == res1.status
    assert retrieval.invoked is False  # Retrieved from TurnReceiptStore!
    assert tutor.invoked is False

