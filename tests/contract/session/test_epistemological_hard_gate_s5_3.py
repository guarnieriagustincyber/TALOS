"""The 12 Epistemological Hard Gates for Subsystem S5.3 (Session Orchestrator).

Verifies that S5.3 coordinates operational turns without usurping
epistemological, evaluative, or curricular authority:

HG-S5.3-EP-01: Formative Non-Evidence Invariant
HG-S5.3-EP-02: Zero Autonomous Evaluation (AST & runtime)
HG-S5.3-EP-03: Zero Evidence Gatekeeper Usurpation (Decoupled Port)
HG-S5.3-EP-04: Authorized Target Inviolability
HG-S5.3-EP-05: Session FSM != StudentState Isolation
HG-S5.3-EP-06: Session Authority for Provenance Context
HG-S5.3-EP-07: Zero Automatic Re-Execution on Recovery
HG-S5.3-EP-08: Ledger-Before-State Projection
HG-S5.3-EP-09: Durable Turn Idempotency (Canonical Request Digest)
HG-S5.3-EP-10: Temporal Validity & Terminal Immutability
HG-S5.3-EP-11: Forensic Audit Gate on Generation
HG-S5.3-EP-12: No Epistemological or Curricular Usurpation (Opaque Envelope)
"""

import ast
from datetime import datetime, timedelta, timezone
import inspect
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from unittest.mock import MagicMock
import pytest

from study_engine.contracts.assessment import (
    AggregationResult,
    AssessmentResult,
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
from study_engine.contracts.evidence_ingestion import (
    AdmissionDecision,
    AdmissionResult,
    AdmissionTrace,
    EvidenceIngestionResult,
    GateVerdict,
    SessionProvenanceContext,
)
from study_engine.contracts.execution import ExecutionObservation
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.state.ledger_contracts import (
    EvidenceLedgerEntry,
    HistoryCutoffMode,
)
from study_engine.roadmap.contracts import (
    CurricularRoadmap,
    DependencyType,
    NodeType,
    RoadmapDependency,
    RoadmapNode,
)
from study_engine.roadmap.engine import compute_canonical_revision_id
from study_engine.session.contracts import (
    AuditRejectionError,
    AuthorizedSessionTarget,
    compute_canonical_sha256,
    SessionExpiredError,
    SessionStatus,
    SessionTerminalError,
    StudentInput,
    StudentInputType,
    TurnIdConflictError,
    UnauthorizedTargetDeviationError,
)
from study_engine.session.fsm import SessionFSM
from study_engine.session.orchestrator import SessionOrchestrator
from study_engine.session.ports import (
    AssessmentPort,
    EvidenceIngestionPort,
    ExecutionPort,
    InMemoryTurnReceiptStore,
)
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.policy_contracts import (
    ActorType,
    AssessmentPolicy,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
)
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.state.policy_engine import compute_canonical_policy_id
from study_engine.state.state_contracts import StudentState


def _make_test_fixtures() -> Tuple[
    CurricularRoadmap,
    AssessmentPolicy,
    AuthorizedSessionTarget,
    EvidenceLedger,
]:
    """Construct minimal curriculum, policy, target, and ledger."""
    n_a = RoadmapNode(
        node_id="node-a",
        title="Node A",
        description="Root topic",
        node_type=NodeType.TOPIC,
        notebook_id="nb-1",
        priority=1,
    )
    n_b = RoadmapNode(
        node_id="node-b",
        title="Node B",
        description="Advanced topic",
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
    rm_id = compute_canonical_revision_id(
        "rm-test", "Test Roadmap", "1.0", nodes, deps
    )
    roadmap = CurricularRoadmap(
        roadmap_id="rm-test",
        title="Test Roadmap",
        version="1.0",
        nodes=nodes,
        dependencies=deps,
        canonical_revision_id=rm_id,
    )

    req = EvidenceRequirement(
        requirement_id="req-1",
        evidence_type=EvidenceType.CODE_EXECUTION,
        min_count=1,
        min_score=1.0,
    )
    crit = NodeAssessmentCriteria(
        criteria_id="crit-a",
        target_node_type=NodeType.TOPIC,
        requirements=(req,),
    )
    pol_id = compute_canonical_policy_id(
        "pol-test", "Policy Test", "1.0", {NodeType.TOPIC: crit}, {}
    )
    policy = AssessmentPolicy(
        policy_id="pol-test",
        title="Policy Test",
        version="1.0",
        default_criteria={NodeType.TOPIC: crit},
        node_overrides={},
        canonical_policy_id=pol_id,
    )

    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    target = AuthorizedSessionTarget(
        authorization_id="auth-001",
        student_id="student-1",
        session_id="sess-001",
        node_id="node-a",
        roadmap_revision_id=rm_id,
        authorized_at=t0,
    )
    ledger = EvidenceLedger()
    return roadmap, policy, target, ledger


def _make_spec_ref(
    spec_id: str = "spec-01",
    sha256: str = "a" * 64,
) -> SpecificationReference:
    return SpecificationReference(
        specification_id=spec_id,
        revision_id="rev-1",
        specification_sha256=sha256,
    )


def _make_obs_ref(
    obs_id: str = "obs-01",
    sha256: str = "b" * 64,
) -> ObservationReference:
    return ObservationReference(
        observation_id=obs_id,
        execution_id="exec-01",
        effective_script_sha256="d" * 64,
        observation_sha256=sha256,
    )


def _make_instrumental_fact() -> InstrumentalFact:
    return InstrumentalFact(
        fact_id="fact-inst-01",
        observation_id="obs-01",
        fact_type=InstrumentalFactType.PROCESS_EXIT_CODE,
        fact_value="0",
        observability=FactObservability.CONCLUSIVE,
        inspected_domain="scratch/workspace/",
        provenance_detail="Process exit observation",
    )


def _make_evaluative_fact() -> EvaluativeFact:
    return EvaluativeFact(
        fact_id="fact-eval-01",
        evaluator_id="eval-01",
        fact_type=EvaluativeFactType.EXIT_CODE_EXPECTED,
        fact_value="0",
        satisfied=True,
        based_on_instrumental_fact_ids=("fact-inst-01",),
        requirement_id="req-clean-exit",
        rationale="Process exited cleanly with code 0",
    )


def _make_dimension_eval() -> DimensionEvaluation:
    return DimensionEvaluation(
        dimension_id="dim-clean-exit",
        status=AssessmentStatus.ASSESSED,
        assigned_level=PerformanceLevel.N3_COMPETENT,
        passed_minimum=True,
        is_critical=True,
        evidence_evaluative_fact_ids=("fact-eval-01",),
        evaluator_rule_ids=("rule-clean-exit-n3",),
        evaluation_rationale="Evaluated cleanly",
    )


def _make_mock_assessment_result(
    node_id: str = "node-a",
    passed: bool = True,
) -> AssessmentResult:
    """Create a valid synthetic AssessmentResult."""
    return AssessmentResult(
        assessment_id="asmt-001",
        authority_id=EpistemologicalAuthority.ASSESSMENT_ENGINE.value,
        task=_make_spec_ref("task-01", "a" * 64),
        rubric=_make_spec_ref("rubric-01", "c" * 64),
        observations=(_make_obs_ref(),),
        instrumental_facts=(_make_instrumental_fact(),),
        evaluative_facts=(_make_evaluative_fact(),),
        dimension_evaluations=(_make_dimension_eval(),),
        aggregation=AggregationResult(
            overall_level=PerformanceLevel.N3_COMPETENT,
            passed=passed,
        ),
        evaluator_id="S9_DETERMINISTIC_EVALUATOR",
        evaluator_version="1.0.0",
        assessed_at=datetime(2026, 9, 1, 10, 15, tzinfo=timezone.utc),
        assessment_digest="e" * 64,
    )


def _make_execution_observation(
    obs_id: str = "obs-1",
    exec_id: str = "exec-1",
) -> ExecutionObservation:
    """Create a minimal valid ExecutionObservation."""
    return ExecutionObservation(
        observation_id=obs_id,
        execution_id=exec_id,
        tool_name="python_sandbox",
        exit_code=0,
    )


# ---------------------------------------------------------------------------
# HG-S5.3-EP-01: Formative Non-Evidence Invariant
# ---------------------------------------------------------------------------
def test_hg_s5_3_ep_01_formative_non_evidence_invariant() -> None:
    """Formative turns produce 0 evidence and 0 ledger mutations."""
    roadmap, policy, target, ledger = _make_test_fixtures()
    orch = SessionOrchestrator(
        session_id="sess-001",
        student_id="student-1",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        authorized_target=target,
        retrieval_fn=lambda nid, q: "Retrieved context for " + nid,
        generation_fn=lambda nid, q: "Generated answer for " + nid,
    )
    orch.start_session()

    s_input = StudentInput(
        input_id="in-formative-1",
        session_id="sess-001",
        turn_index=1,
        input_type=StudentInputType.QUESTION,
        content="What is polymorphism?",
        timestamp=datetime(2026, 9, 1, 10, 5, tzinfo=timezone.utc),
    )

    initial_ledger_count = ledger.total_entries
    out = orch.process_turn(s_input)

    assert out.produced_evidence_id is None
    assert out.admission_result is None
    assert out.ingestion_result is None
    assert ledger.total_entries == initial_ledger_count
    assert orch.fsm.current_status == SessionStatus.WAITING_FOR_STUDENT


# ---------------------------------------------------------------------------
# HG-S5.3-EP-02: Zero Autonomous Evaluation
# ---------------------------------------------------------------------------
def test_hg_s5_3_ep_02_zero_autonomous_evaluation_ast() -> None:
    """AST check: orchestrator.py has 0 evaluation logic and no eval fn."""
    orch_path = Path("src/study_engine/session/orchestrator.py")
    source = orch_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_names = {
        "evaluate_practical_task",
        "assessment_evaluator_fn",
        "evaluate_rubric",
        "score_rubric",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            assert node.name not in forbidden_names, (
                f"S5.3 AST violation: forbidden function '{node.name}'"
            )
        elif isinstance(node, ast.Name):
            assert node.id not in forbidden_names, (
                f"S5.3 AST violation: contains forbidden name '{node.id}'"
            )


# ---------------------------------------------------------------------------
# HG-S5.3-EP-03: Zero Evidence Gatekeeper Usurpation
# ---------------------------------------------------------------------------
def test_hg_s5_3_ep_03_zero_evidence_gatekeeper_usurpation() -> None:
    """S5.3 never passes EvidenceLedger to EvidenceIngestionPort signature."""
    from study_engine.session.ports import EvidenceIngestionPort

    sig = inspect.signature(EvidenceIngestionPort.ingest_assessment)
    params = list(sig.parameters.keys())

    assert "self" in params
    assert "assessment" in params
    assert "context" in params
    assert "ledger" not in params, (
        "HG-S5.3-EP-03: EvidenceLedger leaked into EvidenceIngestionPort!"
    )


# ---------------------------------------------------------------------------
# HG-S5.3-EP-04: Authorized Target Inviolability
# ---------------------------------------------------------------------------
def test_hg_s5_3_ep_04_authorized_target_inviolability() -> None:
    """S5.3 consumes AuthorizedSessionTarget and rejects deviation attempts."""
    roadmap, policy, target, ledger = _make_test_fixtures()
    orch = SessionOrchestrator(
        session_id="sess-001",
        student_id="student-1",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        authorized_target=target,
    )
    orch.start_session()

    # Attempt deviation to unauthorized node-b
    s_input = StudentInput(
        input_id="in-deviation-1",
        session_id="sess-001",
        turn_index=1,
        input_type=StudentInputType.QUESTION,
        content="Let me jump to advanced topic node-b",
        timestamp=datetime(2026, 9, 1, 10, 5, tzinfo=timezone.utc),
        requested_node_id="node-b",
    )

    with pytest.raises(UnauthorizedTargetDeviationError):
        orch.process_turn(s_input)


# ---------------------------------------------------------------------------
# HG-S5.3-EP-05: Session FSM != StudentState Isolation
# ---------------------------------------------------------------------------
def test_hg_s5_3_ep_05_fsm_student_state_isolation() -> None:
    """FSM transitions do not mutate StudentState, and vice versa."""
    fsm = SessionFSM(SessionStatus.CREATED)
    assert not fsm.is_terminal

    fsm.transition_to(SessionStatus.ACTIVE)
    fsm.transition_to(SessionStatus.WAITING_FOR_STUDENT)
    fsm.transition_to(SessionStatus.EXECUTING)
    fsm.transition_to(SessionStatus.ASSESSING)
    fsm.transition_to(SessionStatus.INGESTING)
    fsm.transition_to(SessionStatus.WAITING_FOR_STUDENT)

    assert fsm.current_status == SessionStatus.WAITING_FOR_STUDENT
    # FSM does not hold or mutate any student state
    assert not hasattr(fsm, "student_state")


# ---------------------------------------------------------------------------
# HG-S5.3-EP-06: Session Authority for Provenance Context
# ---------------------------------------------------------------------------
def test_hg_s5_3_ep_06_session_authority_provenance_context() -> None:
    """S5.3 constructs SessionProvenanceContext accurately."""
    roadmap, policy, target, ledger = _make_test_fixtures()
    t_start = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    t_expire = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

    mock_exec = MagicMock(spec=ExecutionPort)
    mock_exec.execute.return_value = _make_execution_observation()

    mock_assess = MagicMock(spec=AssessmentPort)
    mock_assess.assess.return_value = _make_mock_assessment_result("node-a")

    captured_context: Optional[SessionProvenanceContext] = None

    class MockIngestionPort(EvidenceIngestionPort):
        def ingest_assessment(
            self,
            assessment: AssessmentResult,
            context: SessionProvenanceContext,
        ) -> EvidenceIngestionResult:
            nonlocal captured_context
            captured_context = context
            rec = EvidenceRecord(
                record_id="ev-1",
                student_id=context.student_id,
                node_id=context.resolved_target_node_id,
                evidence_type=EvidenceType.CODE_EXECUTION,
                outcome=EvidenceOutcome.PASS,
                score=1.0,
                timestamp=assessment.assessed_at,
                actor_type=ActorType.AI_TUTOR,
                actor_id="s5.3",
                roadmap_revision_id=context.roadmap_revision_id,
                policy_revision_id=context.policy_revision_id,
                authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
            )
            return EvidenceIngestionResult(
                admission=AdmissionResult(
                    decision=AdmissionDecision.ADMITTED,
                    outcome=EvidenceOutcome.PASS,
                    rejection_reason=None,
                    rejection_detail=None,
                    admission_trace=AdmissionTrace(
                        integrity=GateVerdict.PASS,
                        provenance=GateVerdict.PASS,
                        session=GateVerdict.PASS,
                        anti_replay=GateVerdict.PASS,
                    ),
                    evaluated_at=assessment.assessed_at,
                ),
                evidence_record=rec,
                ledger_entry=EvidenceLedgerEntry(
                    entry_index=0,
                    record=rec,
                    parent_entry_hash="0" * 64,
                    entry_hash="1" * 64,
                    committed_at=assessment.assessed_at,
                ),
            )

    orch = SessionOrchestrator(
        session_id="sess-001",
        student_id="student-1",
        roadmap=roadmap,
        policy=policy,
        authorized_target=target,
        execution_port=mock_exec,
        assessment_port=mock_assess,
        ingestion_port=MockIngestionPort(),
        session_started_at=t_start,
        session_expires_at=t_expire,
    )
    orch.start_session(as_of_time=t_start)

    s_input = StudentInput(
        input_id="in-practical-1",
        session_id="sess-001",
        turn_index=1,
        input_type=StudentInputType.CODE_SUBMISSION,
        content="def solution(): return 42",
        timestamp=datetime(2026, 9, 1, 10, 10, tzinfo=timezone.utc),
    )
    orch.process_turn(s_input)

    assert captured_context is not None
    assert captured_context.session_id == "sess-001"
    assert captured_context.student_id == "student-1"
    assert captured_context.resolved_target_node_id == "node-a"
    assert captured_context.roadmap_revision_id == target.roadmap_revision_id
    assert captured_context.session_started_at == t_start
    assert captured_context.session_expires_at == t_expire
    assert captured_context.session_is_active is True


# ---------------------------------------------------------------------------
# HG-S5.3-EP-07: Zero Automatic Re-Execution on Recovery
# ---------------------------------------------------------------------------
def test_hg_s5_3_ep_07_zero_automatic_re_execution_on_recovery() -> None:
    """recover_session() never invokes execution_port.execute()."""
    roadmap, policy, target, ledger = _make_test_fixtures()
    mock_exec = MagicMock(spec=ExecutionPort)

    orch = SessionOrchestrator(
        session_id="sess-001",
        student_id="student-1",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        authorized_target=target,
        execution_port=mock_exec,
    )
    orch.start_session()

    from study_engine.session.contracts import RecoveryDisposition

    for disp in (
        RecoveryDisposition.RETURN_TO_WAITING,
        RecoveryDisposition.RESTART_EVALUATION,
        RecoveryDisposition.REPLAY_COMPLETED,
    ):
        orch.recover_session(disp)
        # Execution port must NEVER be called
        mock_exec.execute.assert_not_called()


# ---------------------------------------------------------------------------
# HG-S5.3-EP-08: Ledger-Before-State Projection
# ---------------------------------------------------------------------------
def test_hg_s5_3_ep_08_ledger_before_state_projection() -> None:
    """Ledger persistence strictly precedes student state re-derivation."""
    roadmap, policy, target, ledger = _make_test_fixtures()
    t_start = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)

    order_of_operations = []

    mock_exec = MagicMock(spec=ExecutionPort)
    mock_exec.execute.return_value = _make_execution_observation()

    mock_assess = MagicMock(spec=AssessmentPort)
    mock_assess.assess.return_value = _make_mock_assessment_result("node-a")

    class OrderedIngestionPort(EvidenceIngestionPort):
        def ingest_assessment(
            self,
            assessment: AssessmentResult,
            context: SessionProvenanceContext,
        ) -> EvidenceIngestionResult:
            order_of_operations.append("LEDGER_PERSISTENCE")
            rec = EvidenceRecord(
                record_id="ev-ordered-1",
                student_id=context.student_id,
                node_id=context.resolved_target_node_id,
                evidence_type=EvidenceType.CODE_EXECUTION,
                outcome=EvidenceOutcome.PASS,
                score=1.0,
                timestamp=assessment.assessed_at,
                actor_type=ActorType.AI_TUTOR,
                actor_id="s5.3",
                roadmap_revision_id=context.roadmap_revision_id,
                policy_revision_id=context.policy_revision_id,
                authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
            )
            return EvidenceIngestionResult(
                admission=AdmissionResult(
                    decision=AdmissionDecision.ADMITTED,
                    outcome=EvidenceOutcome.PASS,
                    rejection_reason=None,
                    rejection_detail=None,
                    admission_trace=AdmissionTrace(
                        integrity=GateVerdict.PASS,
                        provenance=GateVerdict.PASS,
                        session=GateVerdict.PASS,
                        anti_replay=GateVerdict.PASS,
                    ),
                    evaluated_at=assessment.assessed_at,
                ),
                evidence_record=rec,
                ledger_entry=EvidenceLedgerEntry(
                    entry_index=0,
                    record=rec,
                    parent_entry_hash="0" * 64,
                    entry_hash="1" * 64,
                    committed_at=assessment.assessed_at,
                ),
            )

    def mock_state_projector(
        **kwargs: Any,
    ) -> StudentState:
        order_of_operations.append("STATE_DERIVATION")
        return StudentState(
            student_id="student-1",
            roadmap_revision_id=roadmap.canonical_revision_id,
            policy_revision_id=policy.canonical_policy_id,
            ledger_cutoff_hash="0" * 64,
            as_of_time=t_start,
            cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
            node_states=(),
            canonical_state_id="f" * 64,
        )

    orch = SessionOrchestrator(
        session_id="sess-001",
        student_id="student-1",
        roadmap=roadmap,
        policy=policy,
        authorized_target=target,
        execution_port=mock_exec,
        assessment_port=mock_assess,
        ingestion_port=OrderedIngestionPort(),
        state_projector_fn=mock_state_projector,
    )
    orch.start_session(as_of_time=t_start)

    s_input = StudentInput(
        input_id="in-order-1",
        session_id="sess-001",
        turn_index=1,
        input_type=StudentInputType.CODE_SUBMISSION,
        content="solution()",
        timestamp=t_start,
    )
    orch.process_turn(s_input)

    assert "LEDGER_PERSISTENCE" in order_of_operations
    assert "STATE_DERIVATION" in order_of_operations
    first_persist = order_of_operations.index("LEDGER_PERSISTENCE")
    # State derivation in process_turn after ingest must come AFTER persistence
    later_derivations = [
        idx
        for idx, op in enumerate(order_of_operations)
        if op == "STATE_DERIVATION" and idx > first_persist
    ]
    assert len(later_derivations) > 0, (
        "State projection must occur strictly after ledger persistence"
    )


# ---------------------------------------------------------------------------
# HG-S5.3-EP-09: Durable Turn Idempotency
# ---------------------------------------------------------------------------
def test_hg_s5_3_ep_09_durable_turn_idempotency() -> None:
    """Matching request digest replays receipt; differing digest raises."""
    roadmap, policy, target, ledger = _make_test_fixtures()
    receipt_store = InMemoryTurnReceiptStore()

    orch = SessionOrchestrator(
        session_id="sess-001",
        student_id="student-1",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        authorized_target=target,
        receipt_store=receipt_store,
        retrieval_fn=lambda nid, q: "Context",
        generation_fn=lambda nid, q: "Answer",
    )
    orch.start_session()

    s_input1 = StudentInput(
        input_id="turn-idemp-1",
        session_id="sess-001",
        turn_index=1,
        input_type=StudentInputType.QUESTION,
        content="Explain recursion.",
        timestamp=datetime(2026, 9, 1, 10, 5, tzinfo=timezone.utc),
    )

    out1 = orch.process_turn(s_input1)
    stored_rcpt = receipt_store.get_receipt("turn-idemp-1")
    assert stored_rcpt is not None
    assert stored_rcpt.request_digest == compute_canonical_sha256(s_input1)

    # Identical replay returns matching output
    out2 = orch.process_turn(s_input1)
    assert out2.turn_id == out1.turn_id
    assert out2.content == out1.content

    # Modified payload with same input_id raises TurnIdConflictError
    tampered_input = StudentInput(
        input_id="turn-idemp-1",
        session_id="sess-001",
        turn_index=1,
        input_type=StudentInputType.QUESTION,
        content="Tampered question with same ID!",
        timestamp=datetime(2026, 9, 1, 10, 5, tzinfo=timezone.utc),
    )

    with pytest.raises(TurnIdConflictError):
        orch.process_turn(tampered_input)


# ---------------------------------------------------------------------------
# HG-S5.3-EP-10: Temporal Validity & Terminal Immutability
# ---------------------------------------------------------------------------
def test_hg_s5_3_ep_10_temporal_validity_and_terminal_immutability() -> None:
    """Post-expiration raises ExpiredError; terminal raises error."""
    roadmap, policy, target, ledger = _make_test_fixtures()
    t_start = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    t_expire = datetime(2026, 9, 1, 11, 0, tzinfo=timezone.utc)

    orch = SessionOrchestrator(
        session_id="sess-001",
        student_id="student-1",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        authorized_target=target,
        session_started_at=t_start,
        session_expires_at=t_expire,
    )
    orch.start_session(as_of_time=t_start)

    # Turn after expiration boundary
    post_expire_input = StudentInput(
        input_id="in-expired-1",
        session_id="sess-001",
        turn_index=1,
        input_type=StudentInputType.QUESTION,
        content="Too late question",
        timestamp=t_expire + timedelta(seconds=1),
    )

    with pytest.raises(SessionExpiredError):
        orch.process_turn(post_expire_input)

    assert orch.fsm.current_status == SessionStatus.EXPIRED
    assert orch.fsm.is_terminal is True

    # Interaction on terminal session raises SessionTerminalError
    with pytest.raises(SessionTerminalError):
        orch.process_turn(post_expire_input)


# ---------------------------------------------------------------------------
# HG-S5.3-EP-11: Forensic Audit Gate on Generation
# ---------------------------------------------------------------------------
def test_hg_s5_3_ep_11_forensic_audit_gate_on_generation() -> None:
    """Rejected response by S4.4 forensic audit raises AuditRejectionError."""
    roadmap, policy, target, ledger = _make_test_fixtures()

    # Audit function rejecting generation
    def rejecting_audit(nid: str, text: str) -> Tuple[str, bool]:
        return "audit-rep-fail", False

    orch = SessionOrchestrator(
        session_id="sess-001",
        student_id="student-1",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        authorized_target=target,
        retrieval_fn=lambda nid, q: "Context",
        generation_fn=lambda nid, q: "Hallucinated response",
        audit_fn=rejecting_audit,
    )
    orch.start_session()

    s_input = StudentInput(
        input_id="in-audit-fail-1",
        session_id="sess-001",
        turn_index=1,
        input_type=StudentInputType.QUESTION,
        content="Tell me about algorithms.",
        timestamp=datetime(2026, 9, 1, 10, 5, tzinfo=timezone.utc),
    )

    with pytest.raises(AuditRejectionError):
        orch.process_turn(s_input)


# ---------------------------------------------------------------------------
# HG-S5.3-EP-12: No Epistemological or Curricular Usurpation
# ---------------------------------------------------------------------------
def test_hg_s5_3_ep_12_no_curricular_usurpation_opaque_envelope() -> None:
    """S5.3 never autonomously transitions INGESTING to COMPLETED on pass."""
    roadmap, policy, target, ledger = _make_test_fixtures()
    t_start = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)

    mock_exec = MagicMock(spec=ExecutionPort)
    mock_exec.execute.return_value = _make_execution_observation()

    # 100% PASS on assessment
    mock_assess = MagicMock(spec=AssessmentPort)
    mock_assess.assess.return_value = _make_mock_assessment_result("node-a")

    class PassingIngestionPort(EvidenceIngestionPort):
        def ingest_assessment(
            self,
            assessment: AssessmentResult,
            context: SessionProvenanceContext,
        ) -> EvidenceIngestionResult:
            rec = EvidenceRecord(
                record_id="ev-pass-1",
                student_id=context.student_id,
                node_id=context.resolved_target_node_id,
                evidence_type=EvidenceType.CODE_EXECUTION,
                outcome=EvidenceOutcome.PASS,
                score=1.0,
                timestamp=assessment.assessed_at,
                actor_type=ActorType.AI_TUTOR,
                actor_id="s5.3",
                roadmap_revision_id=context.roadmap_revision_id,
                policy_revision_id=context.policy_revision_id,
                authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
            )
            return EvidenceIngestionResult(
                admission=AdmissionResult(
                    decision=AdmissionDecision.ADMITTED,
                    outcome=EvidenceOutcome.PASS,
                    rejection_reason=None,
                    rejection_detail=None,
                    admission_trace=AdmissionTrace(
                        integrity=GateVerdict.PASS,
                        provenance=GateVerdict.PASS,
                        session=GateVerdict.PASS,
                        anti_replay=GateVerdict.PASS,
                    ),
                    evaluated_at=assessment.assessed_at,
                ),
                evidence_record=rec,
                ledger_entry=EvidenceLedgerEntry(
                    entry_index=0,
                    record=rec,
                    parent_entry_hash="0" * 64,
                    entry_hash="1" * 64,
                    committed_at=assessment.assessed_at,
                ),
            )

    orch = SessionOrchestrator(
        session_id="sess-001",
        student_id="student-1",
        roadmap=roadmap,
        policy=policy,
        authorized_target=target,
        execution_port=mock_exec,
        assessment_port=mock_assess,
        ingestion_port=PassingIngestionPort(),
    )
    orch.start_session(as_of_time=t_start)

    s_input = StudentInput(
        input_id="in-practical-pass-1",
        session_id="sess-001",
        turn_index=1,
        input_type=StudentInputType.CODE_SUBMISSION,
        content="solution()",
        timestamp=t_start,
    )
    out = orch.process_turn(s_input)

    # Even on complete mastery PASS, FSM must return to WAITING_FOR_STUDENT,
    # NEVER declare COMPLETED autonomously!
    assert orch.fsm.current_status == SessionStatus.WAITING_FOR_STUDENT
    assert orch.fsm.is_terminal is False
    assert out.admission_result is not None
    assert out.admission_result.decision == AdmissionDecision.ADMITTED
