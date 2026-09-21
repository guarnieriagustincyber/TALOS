"""Adversarial and cascade resilience tests for S5.2.C StateEngine."""

from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple
import pytest

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
    CriteriaEvaluationVerdict,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
    PolicyHashMismatchError,
)
from study_engine.state.policy_engine import compute_canonical_policy_id
from study_engine.state.state_contracts import (
    NodeProgressStatus,
    StateHashMismatchError,
    StudentState,
    validate_student_state_hash,
)
from study_engine.state.state_engine import derive_student_state


def _build_linear_roadmap() -> CurricularRoadmap:

    """Build linear chain A -> B -> C -> D with HARD dependencies."""
    nodes: Dict[str, RoadmapNode] = {
        f"n-{k}": RoadmapNode(
            node_id=f"n-{k}",
            title=f"Node {k.upper()}",
            description=f"Node {k}",
            node_type=NodeType.TOPIC,
            notebook_id="nb-linear",
            priority=idx,
        )
        for idx, k in enumerate(["a", "b", "c", "d"], start=1)
    }
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
        RoadmapDependency(
            source_node_id="n-c",
            target_node_id="n-d",
            dependency_type=DependencyType.HARD,
        ),
    )
    rev_id = compute_canonical_revision_id(
        "rm-linear", "Linear Roadmap", "1.0.0", nodes, deps
    )
    return CurricularRoadmap(
        roadmap_id="rm-linear",
        title="Linear Roadmap",
        version="1.0.0",
        nodes=nodes,
        dependencies=deps,
        canonical_revision_id=rev_id,
    )


def _build_test_policy() -> AssessmentPolicy:
    req = EvidenceRequirement(
        requirement_id="req-std",
        evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
        min_count=1,
        min_score=0.8,
    )
    crit = NodeAssessmentCriteria(
        criteria_id="crit-std",
        target_node_type=NodeType.TOPIC,
        requirements=(req,),
        regression_threshold_failures=2,
    )
    defaults = {NodeType.TOPIC: crit}
    p_id = compute_canonical_policy_id(
        "pol-std", "Std Policy", "1.0.0", defaults, {}
    )
    return AssessmentPolicy(
        policy_id="pol-std",
        title="Std Policy",
        version="1.0.0",
        default_criteria=defaults,
        node_overrides={},
        canonical_policy_id=p_id,
    )


def _rec(
    record_id: str,
    node_id: str,
    outcome: EvidenceOutcome = EvidenceOutcome.PASS,
    timestamp: datetime = None,
    student_id: str = "alice",
) -> EvidenceRecord:
    ts = timestamp or datetime.now(timezone.utc)
    return EvidenceRecord(
        record_id=record_id,
        student_id=student_id,
        node_id=node_id,
        evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
        outcome=outcome,
        score=1.0,
        timestamp=ts,
        actor_type=ActorType.AI_TUTOR,
        actor_id="tutor-1",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
    )


def test_adversarial_transitive_cascade_blocking():
    """Verify regression in root node blocks entire descendant chain."""
    roadmap = _build_linear_roadmap()
    policy = _build_test_policy()
    ledger = EvidenceLedger()

    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)

    # All nodes initially mastered
    ledger.append_record(_rec("a-p", "n-a", timestamp=t0))
    ledger.append_record(_rec("b-p", "n-b", timestamp=t0 + timedelta(hours=1)))
    ledger.append_record(_rec("c-p", "n-c", timestamp=t0 + timedelta(hours=2)))
    ledger.append_record(_rec("d-p", "n-d", timestamp=t0 + timedelta(hours=3)))

    state_before = derive_student_state(
        roadmap, policy, ledger, student_id="alice"
    )
    assert state_before.proficient_node_ids == ("n-a", "n-b", "n-c", "n-d")

    # Now n-a regresses via 2 subsequent failures
    t_f1 = t0 + timedelta(hours=4)
    t_f2 = t0 + timedelta(hours=5)
    ledger.append_record(
        _rec("a-f1", "n-a", EvidenceOutcome.FAIL, timestamp=t_f1)
    )
    ledger.append_record(
        _rec("a-f2", "n-a", EvidenceOutcome.FAIL, timestamp=t_f2)
    )

    state_after = derive_student_state(
        roadmap, policy, ledger, student_id="alice"
    )

    # Root is in NEEDS_REVIEW
    ns_a = state_after.get_node_state("n-a")
    assert ns_a is not None
    assert ns_a.status == NodeProgressStatus.NEEDS_REVIEW

    # All descendants (n-b, n-c, n-d) are now LOCKED!
    assert state_after.locked_node_ids == ("n-b", "n-c", "n-d")


def test_adversarial_philosophical_recovery_without_re_evidence():
    """T13: Dependent recovers automatically once prerequisite recovers."""
    roadmap = _build_linear_roadmap()
    policy = _build_test_policy()
    ledger = EvidenceLedger()

    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)

    # 1. t1: Both A and B are PROFICIENT
    ledger.append_record(
        _rec("a-p1", "n-a", timestamp=t0), override_committed_at=t0
    )
    t1 = t0 + timedelta(hours=1)
    ledger.append_record(
        _rec("b-p1", "n-b", timestamp=t1), override_committed_at=t1
    )

    s1 = derive_student_state(
        roadmap, policy, ledger, student_id="alice", as_of_time=t1
    )
    ns_b_1 = s1.get_node_state("n-b")
    assert ns_b_1 is not None
    assert ns_b_1.status == NodeProgressStatus.ASSESSED_PROFICIENT

    # 2. t2: A suffers 2 failures -> NEEDS_REVIEW
    t_f1 = t0 + timedelta(hours=2)
    t_f2 = t0 + timedelta(hours=3)
    ledger.append_record(
        _rec("a-f1", "n-a", EvidenceOutcome.FAIL, timestamp=t_f1),
        override_committed_at=t_f1,
    )
    ledger.append_record(
        _rec("a-f2", "n-a", EvidenceOutcome.FAIL, timestamp=t_f2),
        override_committed_at=t_f2,
    )

    s2 = derive_student_state(
        roadmap, policy, ledger, student_id="alice", as_of_time=t_f2
    )
    ns_b_2 = s2.get_node_state("n-b")
    assert ns_b_2 is not None
    # B is LOCKED due to prerequisite regression...
    assert ns_b_2.status == NodeProgressStatus.LOCKED
    # ...BUT its intrinsic evaluation remains SATISFIED!
    assert ns_b_2.evaluation_result is not None
    assert (
        ns_b_2.evaluation_result.verdict == CriteriaEvaluationVerdict.SATISFIED
    )

    # 3. t3: A recovers via a new PASS
    t_rec = t0 + timedelta(hours=4)
    ledger.append_record(
        _rec("a-rec", "n-a", timestamp=t_rec), override_committed_at=t_rec
    )

    s3 = derive_student_state(
        roadmap, policy, ledger, student_id="alice", as_of_time=t_rec
    )
    ns_a_3 = s3.get_node_state("n-a")
    assert ns_a_3 is not None
    assert ns_a_3.status == NodeProgressStatus.ASSESSED_PROFICIENT

    # B RECOVERS AUTOMATICALLY to ASSESSED_PROFICIENT without new evidence!
    ns_b_3 = s3.get_node_state("n-b")
    assert ns_b_3 is not None
    assert ns_b_3.status == NodeProgressStatus.ASSESSED_PROFICIENT


def test_adversarial_cutoff_hash_differs_from_live_tip():
    """HG-S5.2C-06: Historical cutoff hash matches past entry not tip."""
    roadmap = _build_linear_roadmap()
    policy = _build_test_policy()
    ledger = EvidenceLedger()

    t0 = datetime(2026, 9, 1, 8, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(hours=1)
    t2 = t0 + timedelta(hours=2)

    ledger.append_record(
        _rec("r1", "n-a", timestamp=t0), override_committed_at=t0
    )
    e2 = ledger.append_record(
        _rec("r2", "n-a", timestamp=t1), override_committed_at=t1
    )

    e3 = ledger.append_record(
        _rec("r3", "n-a", timestamp=t2), override_committed_at=t2
    )

    # Live tip is e3
    assert ledger.tip_hash == e3.entry_hash

    # Query historical state at t1 (e2 is latest matching entry)
    s_hist = derive_student_state(
        roadmap,
        policy,
        ledger,
        student_id="alice",
        as_of_time=t1 + timedelta(minutes=10),
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
    )
    # Cutoff hash must be e2.entry_hash, strictly not e3.entry_hash!
    assert s_hist.ledger_cutoff_hash == e2.entry_hash
    assert s_hist.ledger_cutoff_hash != ledger.tip_hash


def test_adversarial_policy_hash_mismatch_rejection():
    """Verify tampered policy hash is strictly rejected."""
    roadmap = _build_linear_roadmap()
    policy = _build_test_policy()
    ledger = EvidenceLedger()

    tampered_policy = AssessmentPolicy(
        policy_id=policy.policy_id,
        title=policy.title,
        version=policy.version,
        default_criteria=policy.default_criteria,
        node_overrides={},
        canonical_policy_id="f" * 64,  # forged hash
    )

    with pytest.raises(PolicyHashMismatchError):
        derive_student_state(
            roadmap, tampered_policy, ledger, student_id="alice"
        )


def test_adversarial_state_hash_tamper_detection():
    """Verify validate_student_state_hash detects manipulated state hash."""

    roadmap = _build_linear_roadmap()
    policy = _build_test_policy()
    ledger = EvidenceLedger()

    state = derive_student_state(roadmap, policy, ledger, student_id="alice")
    validate_student_state_hash(state)

    tampered_state = StudentState(
        student_id=state.student_id,
        roadmap_revision_id=state.roadmap_revision_id,
        policy_revision_id=state.policy_revision_id,
        ledger_cutoff_hash=state.ledger_cutoff_hash,
        as_of_time=state.as_of_time,
        cutoff_mode=state.cutoff_mode,
        node_states=state.node_states,
        canonical_state_id="e" * 64,  # forged state hash
    )
    with pytest.raises(StateHashMismatchError):
        validate_student_state_hash(tampered_state)


def test_adversarial_future_evidence_exclusion():
    """Verify records with timestamps strictly in the future are ignored."""
    roadmap = _build_linear_roadmap()
    policy = _build_test_policy()
    ledger = EvidenceLedger()

    now = datetime.now(timezone.utc)
    future_time = now + timedelta(days=1)

    # Future record
    ledger.append_record(_rec("fut-1", "n-a", timestamp=future_time))

    # Evaluate at current time
    state = derive_student_state(
        roadmap,
        policy,
        ledger,
        student_id="alice",
        as_of_time=now,
        cutoff_mode=HistoryCutoffMode.EVENT_TIME,
    )
    ns_a = state.get_node_state("n-a")
    assert ns_a is not None
    assert ns_a.status == NodeProgressStatus.AVAILABLE
    assert ns_a.total_evidence_count == 0


def test_adversarial_event_time_non_prefix_cutoff_semantics():
    """Verify out-of-order event arrivals and distinct cutoff semantics."""
    roadmap = _build_linear_roadmap()
    policy = _build_test_policy()
    ledger = EvidenceLedger()

    base_time = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    t_event_1 = base_time
    t_commit_1 = base_time

    t_event_2 = base_time + timedelta(hours=2)
    t_commit_2 = base_time + timedelta(hours=1)

    t_event_3 = base_time - timedelta(hours=1)  # delayed arrival
    t_commit_3 = base_time + timedelta(hours=2)

    # e1: committed 10:00, event 10:00
    ledger.append_record(
        _rec("r1", "n-a", timestamp=t_event_1),
        override_committed_at=t_commit_1,
    )
    # e2: committed 11:00, event 12:00
    e2 = ledger.append_record(
        _rec("r2", "n-b", timestamp=t_event_2),
        override_committed_at=t_commit_2,
    )
    # e3: committed 12:00, event 09:00 (arrived late)
    e3 = ledger.append_record(
        _rec("r3", "n-a", timestamp=t_event_3),
        override_committed_at=t_commit_3,
    )

    # Query EVENT_TIME cutoff at 10:30
    cutoff_event_time = base_time + timedelta(minutes=30)
    state_event = derive_student_state(
        roadmap,
        policy,
        ledger,
        student_id="alice",
        as_of_time=cutoff_event_time,
        cutoff_mode=HistoryCutoffMode.EVENT_TIME,
    )

    # e1 (10:00) and e3 (09:00) are included; e2 (12:00) is excluded
    ns_a = state_event.get_node_state("n-a")
    assert ns_a is not None
    assert ns_a.total_evidence_count == 2
    ns_b = state_event.get_node_state("n-b")
    assert ns_b is not None
    assert ns_b.total_evidence_count == 0  # e2 excluded!

    # Under EVENT_TIME, highest-committed entry matching cutoff is e3
    assert state_event.ledger_cutoff_hash == e3.entry_hash

    # By contrast, query COMMIT_TIME cutoff at 11:30
    cutoff_commit_time = base_time + timedelta(minutes=90)
    state_commit = derive_student_state(
        roadmap,
        policy,
        ledger,
        student_id="alice",
        as_of_time=cutoff_commit_time,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
    )
    # Under COMMIT_TIME, strict physical prefix up to e2
    assert state_commit.ledger_cutoff_hash == e2.entry_hash
    ns_a_commit = state_commit.get_node_state("n-a")
    assert ns_a_commit is not None
    assert ns_a_commit.total_evidence_count == 1  # e3 not yet committed!
