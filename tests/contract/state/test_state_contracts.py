"""Contract tests for Subsystem S5.2.C State contracts and canonicalization."""

from datetime import datetime, timezone, timedelta
import pytest
from pydantic import ValidationError

from study_engine.state.ledger_contracts import HistoryCutoffMode
from study_engine.state.policy_contracts import (
    CriteriaEvaluationResult,
    CriteriaEvaluationVerdict,
)
from study_engine.state.state_contracts import (
    NodeProgressStatus,
    NodeState,
    StateHashMismatchError,
    StudentState,
    compute_canonical_state_id,
    validate_student_state_hash,
)


def _make_node_state(
    node_id: str,
    status: NodeProgressStatus = NodeProgressStatus.AVAILABLE,
    evidence_count: int = 0,
) -> NodeState:
    eval_result = None
    if status == NodeProgressStatus.ASSESSED_PROFICIENT:
        eval_result = CriteriaEvaluationResult(
            criteria_id=f"crit-{node_id}",
            verdict=CriteriaEvaluationVerdict.SATISFIED,
            satisfied_requirements=("req-1",),
            missing_requirements=(),
            subsequent_failures_count=0,
            evaluation_timestamp=datetime(
                2026, 9, 1, 12, 0, tzinfo=timezone.utc
            ),
            rationale="Satisfied criteria",
        )

    return NodeState(
        node_id=node_id,
        status=status,
        evaluation_result=eval_result,
        total_evidence_count=evidence_count,
    )


def test_node_state_and_student_state_immutability():
    """Verify NodeState and StudentState are frozen with immutable tuples."""
    ns = _make_node_state("node-a")
    with pytest.raises(ValidationError):
        ns.status = NodeProgressStatus.LOCKED  # type: ignore[misc]

    as_of = datetime(2026, 9, 1, 15, 0, tzinfo=timezone.utc)
    state_id = compute_canonical_state_id(
        student_id="student-1",
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        ledger_cutoff_hash="2" * 64,
        as_of_time=as_of,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
        node_states=(ns,),
    )
    student_state = StudentState(
        student_id="student-1",
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        ledger_cutoff_hash="2" * 64,
        as_of_time=as_of,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
        node_states=(ns,),
        canonical_state_id=state_id,
    )

    with pytest.raises(ValidationError):
        student_state.student_id = "student-2"  # type: ignore[misc]

    assert isinstance(student_state.node_states, tuple)
    with pytest.raises(TypeError):
        new_node = _make_node_state("node-b")
        student_state.node_states[0] = new_node  # type: ignore[index]


def test_canonical_state_id_stability_and_ordering():

    """Verify state hash is invariant to node_states tuple input ordering."""
    ns1 = _make_node_state("node-1", NodeProgressStatus.AVAILABLE)
    ns2 = _make_node_state("node-2", NodeProgressStatus.LOCKED)
    as_of = datetime(2026, 9, 1, 15, 0, tzinfo=timezone.utc)

    # Hash with order [ns1, ns2]
    hash1 = compute_canonical_state_id(
        student_id="student-1",
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        ledger_cutoff_hash="2" * 64,
        as_of_time=as_of,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
        node_states=(ns1, ns2),
    )

    # Hash with reversed order [ns2, ns1]
    hash2 = compute_canonical_state_id(
        student_id="student-1",
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        ledger_cutoff_hash="2" * 64,
        as_of_time=as_of,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
        node_states=(ns2, ns1),
    )
    assert hash1 == hash2
    assert len(hash1) == 64

    # Any change mutates hash
    ns1_mutated = _make_node_state(
        "node-1", NodeProgressStatus.AVAILABLE, evidence_count=1
    )
    hash_diff = compute_canonical_state_id(
        student_id="student-1",
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        ledger_cutoff_hash="2" * 64,
        as_of_time=as_of,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
        node_states=(ns1_mutated, ns2),
    )
    assert hash_diff != hash1


def test_canonical_state_id_timezone_normalization():
    """Verify UTC normalization yields identical hash across timezones."""
    ns = _make_node_state("node-1")
    utc_time = datetime(2026, 9, 1, 18, 0, tzinfo=timezone.utc)
    offset_time = datetime(
        2026, 9, 1, 15, 0, tzinfo=timezone(timedelta(hours=-3))
    )

    hash_utc = compute_canonical_state_id(
        student_id="student-1",
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        ledger_cutoff_hash="2" * 64,
        as_of_time=utc_time,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
        node_states=(ns,),
    )
    hash_offset = compute_canonical_state_id(
        student_id="student-1",
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        ledger_cutoff_hash="2" * 64,
        as_of_time=offset_time,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
        node_states=(ns,),
    )
    assert hash_utc == hash_offset


def test_validate_student_state_hash_rejection():
    """Verify validate_student_state_hash rejects tampered state hashes."""
    ns = _make_node_state("node-1")
    as_of = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    valid_hash = compute_canonical_state_id(
        student_id="student-1",
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        ledger_cutoff_hash="2" * 64,
        as_of_time=as_of,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
        node_states=(ns,),
    )
    state = StudentState(
        student_id="student-1",
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        ledger_cutoff_hash="2" * 64,
        as_of_time=as_of,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
        node_states=(ns,),
        canonical_state_id=valid_hash,
    )
    # Valid passes
    validate_student_state_hash(state)

    # Tampered raises StateHashMismatchError
    tampered_state = StudentState(
        student_id="student-1",
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        ledger_cutoff_hash="2" * 64,
        as_of_time=as_of,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
        node_states=(ns,),
        canonical_state_id="f" * 64,
    )
    with pytest.raises(StateHashMismatchError):
        validate_student_state_hash(tampered_state)


def test_student_state_convenience_properties():
    """Verify indexed lookup and status category properties on StudentState."""
    n1 = _make_node_state("n1", NodeProgressStatus.AVAILABLE)
    n2 = _make_node_state("n2", NodeProgressStatus.LOCKED)
    n3 = _make_node_state("n3", NodeProgressStatus.ASSESSED_PROFICIENT)
    n4 = _make_node_state("n4", NodeProgressStatus.NEEDS_REVIEW)
    n5 = _make_node_state("n5", NodeProgressStatus.EXEMPT)
    n6 = _make_node_state("n6", NodeProgressStatus.IN_PROGRESS)

    nodes = (n1, n2, n3, n4, n5, n6)
    as_of = datetime.now(timezone.utc)
    state_id = compute_canonical_state_id(
        student_id="s1",
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        ledger_cutoff_hash="2" * 64,
        as_of_time=as_of,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
        node_states=nodes,
    )

    state = StudentState(
        student_id="s1",
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        ledger_cutoff_hash="2" * 64,
        as_of_time=as_of,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
        node_states=nodes,
        canonical_state_id=state_id,
    )

    assert state.get_node_state("n1") == n1
    assert state.get_node_state("n999") is None

    assert state.available_node_ids == ("n1",)
    assert state.locked_node_ids == ("n2",)
    assert state.proficient_node_ids == ("n3",)
    assert state.needs_review_node_ids == ("n4",)
    assert state.exempt_node_ids == ("n5",)
    assert state.in_progress_node_ids == ("n6",)
