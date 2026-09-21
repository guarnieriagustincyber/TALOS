"""Unit tests for StateEngine synthesis logic in Subsystem S5.2.C."""

from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple

from study_engine.roadmap.contracts import (
    CurricularRoadmap,
    DependencyType,
    NodeType,
    RoadmapDependency,
    RoadmapNode,
)
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.roadmap.engine import compute_canonical_revision_id
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import HistoryCutoffMode
from study_engine.state.policy_contracts import (
    ActorType,
    AssessmentPolicy,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
)
from study_engine.state.policy_engine import compute_canonical_policy_id
from study_engine.state.state_contracts import (
    NodeProgressStatus,
    validate_student_state_hash,
)
from study_engine.state.state_engine import derive_student_state


def _make_test_roadmap() -> CurricularRoadmap:
    n_a = RoadmapNode(
        node_id="node-a",
        title="Node A",
        description="Root topic",
        node_type=NodeType.TOPIC,
        notebook_id="nb-01",
        priority=1,
    )
    n_b = RoadmapNode(
        node_id="node-b",
        title="Node B",
        description="Dependent topic",
        node_type=NodeType.TOPIC,
        notebook_id="nb-01",
        priority=2,
    )
    n_c = RoadmapNode(
        node_id="node-c",
        title="Node C",
        description="Soft dependent lab",
        node_type=NodeType.LAB,
        notebook_id="nb-01",
        priority=3,
    )

    nodes: Dict[str, RoadmapNode] = {
        "node-a": n_a,
        "node-b": n_b,
        "node-c": n_c,
    }
    deps: Tuple[RoadmapDependency, ...] = (
        RoadmapDependency(
            source_node_id="node-a",
            target_node_id="node-b",
            dependency_type=DependencyType.HARD,
        ),
        RoadmapDependency(
            source_node_id="node-b",
            target_node_id="node-c",
            dependency_type=DependencyType.SOFT,
        ),
    )
    rev_id = compute_canonical_revision_id(
        "rm-test", "Test Roadmap", "1.0.0", nodes, deps
    )
    return CurricularRoadmap(
        roadmap_id="rm-test",
        title="Test Roadmap",
        version="1.0.0",
        nodes=nodes,
        dependencies=deps,
        canonical_revision_id=rev_id,
    )


def _make_test_policy() -> AssessmentPolicy:
    req_topic = EvidenceRequirement(
        requirement_id="req-topic",
        evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
        min_count=1,
        min_score=0.8,
    )
    crit_topic = NodeAssessmentCriteria(
        criteria_id="crit-topic-default",
        target_node_type=NodeType.TOPIC,
        requirements=(req_topic,),
        regression_threshold_failures=2,
    )

    req_lab = EvidenceRequirement(
        requirement_id="req-lab",
        evidence_type=EvidenceType.LAB_TELEMETRY,
        min_count=1,
        min_score=0.9,
    )
    crit_lab = NodeAssessmentCriteria(
        criteria_id="crit-lab-default",
        target_node_type=NodeType.LAB,
        requirements=(req_lab,),
        regression_threshold_failures=2,
    )

    defaults = {NodeType.TOPIC: crit_topic, NodeType.LAB: crit_lab}
    p_id = compute_canonical_policy_id(
        "pol-test", "Test Policy", "1.0.0", defaults, {}
    )
    return AssessmentPolicy(
        policy_id="pol-test",
        title="Test Policy",
        version="1.0.0",
        default_criteria=defaults,
        node_overrides={},
        canonical_policy_id=p_id,
    )


def _make_evidence(
    record_id: str,
    node_id: str,
    student_id: str = "alice",
    outcome: EvidenceOutcome = EvidenceOutcome.PASS,
    timestamp: datetime = None,
    evidence_type: EvidenceType = EvidenceType.CONCEPTUAL_EXPLANATION,
) -> EvidenceRecord:
    ts = timestamp or datetime.now(timezone.utc)
    return EvidenceRecord(
        record_id=record_id,
        student_id=student_id,
        node_id=node_id,
        evidence_type=evidence_type,
        outcome=outcome,
        score=1.0,
        timestamp=ts,
        actor_type=ActorType.AI_TUTOR,
        actor_id="tutor-1",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
    )


def test_state_engine_empty_ledger():
    """Verify state with empty ledger: root is AVAILABLE, child LOCKED."""
    roadmap = _make_test_roadmap()
    policy = _make_test_policy()
    ledger = EvidenceLedger()

    state = derive_student_state(roadmap, policy, ledger, student_id="alice")
    validate_student_state_hash(state)

    assert state.student_id == "alice"
    assert state.ledger_cutoff_hash == "0" * 64
    assert state.available_node_ids == ("node-a", "node-c")
    assert state.locked_node_ids == ("node-b",)

    # Node C has only a SOFT dependency on Node B -> it is AVAILABLE!

    node_c_state = state.get_node_state("node-c")
    assert node_c_state is not None
    assert node_c_state.status == NodeProgressStatus.AVAILABLE
    assert node_c_state.unfulfilled_soft_prerequisites == ("node-b",)


def test_state_engine_promotion_and_unlock():
    """Verify mastering root node promotes it and unlocks dependent node."""
    roadmap = _make_test_roadmap()
    policy = _make_test_policy()
    ledger = EvidenceLedger()

    # Commit passing evidence for node-a
    e1 = _make_evidence("rec-1", node_id="node-a", student_id="alice")
    ledger.append_record(e1)

    state = derive_student_state(roadmap, policy, ledger, student_id="alice")
    validate_student_state_hash(state)

    ns_a = state.get_node_state("node-a")
    assert ns_a is not None
    assert ns_a.status == NodeProgressStatus.ASSESSED_PROFICIENT

    # Node B was locked by Node A, now becomes AVAILABLE
    ns_b = state.get_node_state("node-b")
    assert ns_b is not None
    assert ns_b.status == NodeProgressStatus.AVAILABLE


def test_state_engine_soft_dependency_does_not_lock():
    """Verify unsatisfied SOFT dependency does not cause LOCKED status."""
    roadmap = _make_test_roadmap()
    policy = _make_test_policy()
    ledger = EvidenceLedger()

    state = derive_student_state(roadmap, policy, ledger, student_id="alice")
    node_c = state.get_node_state("node-c")
    assert node_c is not None
    assert node_c.status == NodeProgressStatus.AVAILABLE
    assert "node-b" in node_c.unfulfilled_soft_prerequisites


def test_state_engine_needs_review_cascade_blocking():
    """Verify node entering NEEDS_REVIEW cascades to LOCK dependent nodes."""
    roadmap = _make_test_roadmap()
    policy = _make_test_policy()
    ledger = EvidenceLedger()

    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    # 1 PASS, then 2 subsequent FAILs -> triggers regression (threshold=2)
    p1 = _make_evidence("p1", "node-a", timestamp=t0)
    t_f1 = t0 + timedelta(hours=1)
    f1 = _make_evidence(
        "f1", "node-a", outcome=EvidenceOutcome.FAIL, timestamp=t_f1
    )
    t_f2 = t0 + timedelta(hours=2)
    f2 = _make_evidence(
        "f2", "node-a", outcome=EvidenceOutcome.FAIL, timestamp=t_f2
    )

    ledger.append_record(p1, override_committed_at=t0)
    ledger.append_record(f1, override_committed_at=t_f1)
    ledger.append_record(f2, override_committed_at=t_f2)

    state = derive_student_state(roadmap, policy, ledger, student_id="alice")
    ns_a = state.get_node_state("node-a")
    assert ns_a is not None
    assert ns_a.status == NodeProgressStatus.NEEDS_REVIEW

    # Node B depends on Node A with HARD dependency -> MUST BE LOCKED!
    ns_b = state.get_node_state("node-b")
    assert ns_b is not None
    assert ns_b.status == NodeProgressStatus.LOCKED
    assert "node-a" in ns_b.unfulfilled_hard_prerequisites


def test_state_engine_sovereign_exemption():
    """Verify HUMAN MANUAL_OVERRIDE marks node EXEMPT and unlocks child."""
    roadmap = _make_test_roadmap()
    policy = _make_test_policy()
    ledger = EvidenceLedger()

    override = EvidenceRecord(
        record_id="rec-ovr",
        student_id="alice",
        node_id="node-a",
        evidence_type=EvidenceType.MANUAL_OVERRIDE,
        outcome=EvidenceOutcome.PASS,
        score=1.0,
        timestamp=datetime.now(timezone.utc),
        actor_type=ActorType.HUMAN,
        actor_id="professor",
        rationale="Previous degree validated",
        roadmap_revision_id=roadmap.canonical_revision_id,
        policy_revision_id=policy.canonical_policy_id,
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
    )
    ledger.append_record(override)

    state = derive_student_state(roadmap, policy, ledger, student_id="alice")
    ns_a = state.get_node_state("node-a")
    assert ns_a is not None
    assert ns_a.status == NodeProgressStatus.EXEMPT

    ns_b = state.get_node_state("node-b")
    assert ns_b is not None
    assert ns_b.status == NodeProgressStatus.AVAILABLE


def test_state_engine_student_isolation():
    """Verify evidence from other students is strictly ignored."""
    roadmap = _make_test_roadmap()
    policy = _make_test_policy()
    ledger = EvidenceLedger()

    # Bob completes Node A
    e_bob = _make_evidence("rec-bob", node_id="node-a", student_id="bob")
    ledger.append_record(e_bob)

    # Derive state for Alice
    state_alice = derive_student_state(
        roadmap, policy, ledger, student_id="alice"
    )
    ns_alice_a = state_alice.get_node_state("node-a")
    assert ns_alice_a is not None
    assert ns_alice_a.status == NodeProgressStatus.AVAILABLE
    assert ns_alice_a.total_evidence_count == 0

    # Derive state for Bob
    state_bob = derive_student_state(roadmap, policy, ledger, student_id="bob")
    ns_bob_a = state_bob.get_node_state("node-a")
    assert ns_bob_a is not None
    assert ns_bob_a.status == NodeProgressStatus.ASSESSED_PROFICIENT
    assert ns_bob_a.total_evidence_count == 1


def test_state_engine_historical_cutoff_and_seal():
    """Verify as_of_time time-travel and accurate ledger_cutoff_hash."""
    roadmap = _make_test_roadmap()
    policy = _make_test_policy()
    ledger = EvidenceLedger()

    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(hours=1)
    t2 = t0 + timedelta(hours=2)

    entry1 = ledger.append_record(
        _make_record("r1", "node-a", timestamp=t0), override_committed_at=t0
    )
    entry2 = ledger.append_record(
        _make_record("r2", "node-b", timestamp=t1), override_committed_at=t1
    )

    # State at t0 (only entry1 committed)
    s_t0 = derive_student_state(
        roadmap,
        policy,
        ledger,
        student_id="alice",
        as_of_time=t0 + timedelta(minutes=30),
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
    )
    assert s_t0.ledger_cutoff_hash == entry1.entry_hash
    ns_a_t0 = s_t0.get_node_state("node-a")
    assert ns_a_t0 is not None
    assert ns_a_t0.status == NodeProgressStatus.ASSESSED_PROFICIENT
    ns_b_t0 = s_t0.get_node_state("node-b")
    assert ns_b_t0 is not None
    assert ns_b_t0.status == NodeProgressStatus.AVAILABLE

    # State at t2 (both entry1 and entry2 committed)
    s_t2 = derive_student_state(
        roadmap,
        policy,
        ledger,
        student_id="alice",
        as_of_time=t2,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
    )
    assert s_t2.ledger_cutoff_hash == entry2.entry_hash
    ns_b_t2 = s_t2.get_node_state("node-b")
    assert ns_b_t2 is not None
    assert ns_b_t2.status == NodeProgressStatus.ASSESSED_PROFICIENT


def _make_record(
    record_id: str,
    node_id: str,
    timestamp: datetime,
) -> EvidenceRecord:
    return _make_evidence(
        record_id=record_id,
        node_id=node_id,
        student_id="alice",
        timestamp=timestamp,
    )
