"""Adversarial tests for Subsystem S5.3 Session Orchestrator and Hard Gates."""

from datetime import datetime, timedelta, timezone

from typing import Dict, Tuple
from unittest.mock import MagicMock
import pytest

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
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
)
from study_engine.state.policy_engine import compute_canonical_policy_id
from study_engine.session.contracts import (
    AuditRejectionError,
    InvalidSessionTransitionError,
    LockedNodeTargetError,
    SessionStatus,
    StudentInput,
    StudentInputType,
    TurnActionType,
)
from study_engine.session.orchestrator import SessionOrchestrator


def _build_chain_roadmap() -> CurricularRoadmap:
    """A -> B -> C (all HARD)."""
    n_a = RoadmapNode(
        node_id="n-a",
        title="A",
        description="A",
        node_type=NodeType.TOPIC,
        notebook_id="nb-1",
        priority=1,
    )
    n_b = RoadmapNode(
        node_id="n-b",
        title="B",
        description="B",
        node_type=NodeType.TOPIC,
        notebook_id="nb-1",
        priority=2,
    )
    n_c = RoadmapNode(
        node_id="n-c",
        title="C",
        description="C",
        node_type=NodeType.TOPIC,
        notebook_id="nb-1",
        priority=3,
    )
    nodes: Dict[str, RoadmapNode] = {"n-a": n_a, "n-b": n_b, "n-c": n_c}
    deps: Tuple[RoadmapDependency, ...] = (
        RoadmapDependency(
            source_node_id="n-a",
            target_node_id="n-b",
            dependency_type=DependencyType.HARD,
        ),
        RoadmapDependency(
            source_node_id="n-b",
            target_node_id="n-c",
            dependency_type=DependencyType.HARD,
        ),
    )
    rev_id = compute_canonical_revision_id("rm", "Chain", "1.0", nodes, deps)
    return CurricularRoadmap(
        roadmap_id="rm",
        title="Chain",
        version="1.0",
        nodes=nodes,
        dependencies=deps,
        canonical_revision_id=rev_id,
    )


def _build_test_policy() -> AssessmentPolicy:
    req = EvidenceRequirement(
        requirement_id="req-1",
        evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
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
    return AssessmentPolicy(
        policy_id="pol",
        title="Policy",
        version="1.0",
        default_criteria=defaults,
        node_overrides={},
        canonical_policy_id=pol_id,
    )


def test_adversarial_hg_s5_3_02_locked_node_target_rejected() -> None:
    """HG-S5.3-02: Orchestrator rejects target on LOCKED node."""
    roadmap = _build_chain_roadmap()
    policy = _build_test_policy()
    ledger = EvidenceLedger()
    orch = SessionOrchestrator("sess-adv-1", "alice", roadmap, policy, ledger)
    orch.start_session()

    # n-c is transitively LOCKED because n-a and n-b are not yet satisfied
    s_input = StudentInput(
        input_id="in-locked",
        session_id="sess-adv-1",
        turn_index=1,
        input_type=StudentInputType.QUESTION,
        content="Jump ahead to Node C",
        timestamp=datetime.now(timezone.utc),
        requested_node_id="n-c",
    )

    with pytest.raises(LockedNodeTargetError) as exc_info:
        orch.process_turn(s_input)

    assert "Target node 'n-c' is LOCKED" in str(exc_info.value)


def test_adversarial_hg_s5_3_03_audit_rejection_blocks_unapproved_response(
) -> None:

    """HG-S5.3-03: S4.4 audit rejection blocks delivery of response."""
    roadmap = _build_chain_roadmap()
    policy = _build_test_policy()
    ledger = EvidenceLedger()

    # Mock audit function rejecting generated content
    audit_mock = MagicMock(return_value=("audit-hallucination-99", False))

    orch = SessionOrchestrator(
        session_id="sess-adv-2",
        student_id="alice",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        retrieval_fn=lambda nid, q: "Context text",
        generation_fn=lambda nid, q: "Hallucinated response",
        audit_fn=audit_mock,
    )
    orch.start_session()

    s_input = StudentInput(
        input_id="in-hallucination",
        session_id="sess-adv-2",
        turn_index=1,
        input_type=StudentInputType.QUESTION,
        content="What is Node A?",
        timestamp=datetime.now(timezone.utc),
    )

    with pytest.raises(AuditRejectionError) as exc_info:
        orch.process_turn(s_input)

    assert "audit-hallucination-99" in str(exc_info.value)
    # Ensure unapproved turn is not committed to history
    assert len(orch.turn_history) == 1  # only turn 0


def test_adversarial_hg_s5_3_04_strict_replay_idempotency() -> None:
    """HG-S5.3-04: Repeated submission does not pollute ledger."""
    roadmap = _build_chain_roadmap()
    policy = _build_test_policy()
    ledger = EvidenceLedger()
    orch = SessionOrchestrator("sess-adv-3", "alice", roadmap, policy, ledger)
    orch.start_session()

    s_input = StudentInput(
        input_id="in-repeat-1",
        session_id="sess-adv-3",
        turn_index=1,
        input_type=StudentInputType.ANSWER,
        content="Answer for Node A",
        timestamp=datetime.now(timezone.utc),
    )

    out1 = orch.process_turn(s_input)
    assert len(ledger._entries) == 1
    initial_tip = ledger._entries[0].entry_hash

    # Repeat twice
    out2 = orch.process_turn(s_input)
    out3 = orch.process_turn(s_input)

    assert out1.turn_id == out2.turn_id == out3.turn_id
    assert out1.content == out2.content == out3.content
    assert len(ledger._entries) == 1  # Not duplicated!
    assert ledger._entries[0].entry_hash == initial_tip


def test_adversarial_hg_s5_3_07_faithful_abstention_on_empty_context() -> None:
    """HG-S5.3-07: Abstain explicitly when retrieval yields no context."""
    roadmap = _build_chain_roadmap()
    policy = _build_test_policy()
    ledger = EvidenceLedger()

    orch = SessionOrchestrator(
        session_id="sess-adv-4",
        student_id="alice",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        retrieval_fn=lambda nid, q: None,  # empty context
    )
    orch.start_session()

    s_input = StudentInput(
        input_id="in-no-context",
        session_id="sess-adv-4",
        turn_index=1,
        input_type=StudentInputType.QUESTION,
        content="Question with no context",
        timestamp=datetime.now(timezone.utc),
    )

    out = orch.process_turn(s_input)
    assert out.action_type == TurnActionType.ABSTENTION
    assert "No verified curricular evidence was retrieved" in out.content
    assert "Abstaining from generation" in out.content


def test_adversarial_hg_s5_3_08_ledger_append_failure_fail_closed() -> None:
    """HG-S5.3-08: If ledger commit fails, fail-closed without advance."""
    roadmap = _build_chain_roadmap()
    policy = _build_test_policy()
    ledger = EvidenceLedger()

    # Simulate filesystem / lock failure on ledger append
    mock_append = MagicMock(side_effect=IOError("Disk write failure"))
    ledger.append_record = mock_append  # type: ignore[method-assign]

    orch = SessionOrchestrator("sess-adv-5", "alice", roadmap, policy, ledger)
    orch.start_session()

    s_input = StudentInput(
        input_id="in-fail-append",
        session_id="sess-adv-5",
        turn_index=1,
        input_type=StudentInputType.ANSWER,
        content="Passing answer",
        timestamp=datetime.now(timezone.utc),
    )

    with pytest.raises(IOError):
        orch.process_turn(s_input)

    # State was never advanced, output was never cached
    assert "in-fail-append" not in orch.replay_cache
    assert len(orch.turn_history) == 1


def test_adversarial_fsm_illegal_invocation_rejected() -> None:
    """HG-S5.3-05: Reject turn if FSM is in terminal ABORTED state."""
    roadmap = _build_chain_roadmap()
    policy = _build_test_policy()
    ledger = EvidenceLedger()
    orch = SessionOrchestrator("sess-adv-6", "alice", roadmap, policy, ledger)
    orch.start_session()

    # Abort session
    orch.fsm.transition_to(SessionStatus.ABORTED, "Cancelled")

    s_input = StudentInput(

        input_id="in-after-abort",
        session_id="sess-adv-6",
        turn_index=1,
        input_type=StudentInputType.QUESTION,
        content="Hello?",
        timestamp=datetime.now(timezone.utc),
    )

    with pytest.raises(InvalidSessionTransitionError):
        orch.process_turn(s_input)


def test_adversarial_hg_s5_3_01_provenance_student_state_id_pure_projection(
) -> None:
    """HG-S5.3-01: Verify student_state_id strictly derives from S5.2.C."""
    from study_engine.state.state_contracts import validate_student_state_hash
    from study_engine.state.state_engine import derive_student_state

    roadmap = _build_chain_roadmap()
    policy = _build_test_policy()
    ledger = EvidenceLedger()
    orch = SessionOrchestrator(
        "sess-adv-prov", "alice", roadmap, policy, ledger
    )

    # Turn 0: Start session
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    out0 = orch.start_session(as_of_time=t0)
    expected_state0 = derive_student_state(
        roadmap, policy, ledger, "alice", as_of_time=t0
    )
    validate_student_state_hash(expected_state0)

    # Verify turn 0 state hash matches independent projection
    assert out0.student_state_id == expected_state0.canonical_state_id

    # Turn 1: Process answer
    t1 = t0 + timedelta(minutes=5)
    s_input = StudentInput(
        input_id="in-prov-1",
        session_id="sess-adv-prov",
        turn_index=1,
        input_type=StudentInputType.ANSWER,
        content="Pass n-a",
        timestamp=t1,
    )
    out1 = orch.process_turn(s_input)

    # Verify turn 1 state hash strictly matches independent S5.2.C projection
    expected_state1 = derive_student_state(
        roadmap, policy, ledger, "alice", as_of_time=t1
    )
    validate_student_state_hash(expected_state1)
    assert out1.student_state_id == expected_state1.canonical_state_id
    assert out1.student_state_id != expected_state0.canonical_state_id

    # Turn 2: Question without new evidence
    t2 = t1 + timedelta(minutes=5)
    s_input2 = StudentInput(
        input_id="in-prov-2",
        session_id="sess-adv-prov",
        turn_index=2,
        input_type=StudentInputType.QUESTION,
        content="Query on n-b",
        timestamp=t2,
    )
    out2 = orch.process_turn(s_input2)
    # Turn without evidence matches independent projection at t2
    expected_state2 = derive_student_state(
        roadmap, policy, ledger, "alice", as_of_time=t2
    )
    assert out2.student_state_id == expected_state2.canonical_state_id
