"""Unit tests for EvidenceLedger in Subsystem S5.2.B."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import (
    DuplicateEvidenceError,
    HistoryCutoffMode,
    LedgerIntegrityStatus,
    NonMonotonicCommitError,
)
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.state.policy_contracts import (
    ActorType,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)


def _make_record(
    record_id: str,
    node_id: str = "node-1",
    event_timestamp: datetime = None,
    outcome: EvidenceOutcome = EvidenceOutcome.PASS,
) -> EvidenceRecord:
    ts = event_timestamp or datetime.now(timezone.utc)
    return EvidenceRecord(
        record_id=record_id,
        node_id=node_id,
        evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
        outcome=outcome,
        score=1.0,
        timestamp=ts,
        actor_type=ActorType.AI_TUTOR,
        actor_id="tutor-1",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
    )


def test_ledger_in_memory_append_and_tip():
    """Verify in-memory ledger appends entries and maintains hash chain."""
    ledger = EvidenceLedger()
    assert ledger.total_entries == 0
    assert ledger.tip_hash == "0" * 64

    r1 = _make_record("rec-1", node_id="node-a")
    entry1 = ledger.append_record(r1)

    assert entry1.entry_index == 0
    assert entry1.parent_entry_hash == "0" * 64
    assert len(entry1.entry_hash) == 64
    assert ledger.total_entries == 1
    assert ledger.tip_hash == entry1.entry_hash

    r2 = _make_record("rec-2", node_id="node-b")
    entry2 = ledger.append_record(r2)

    assert entry2.entry_index == 1
    assert entry2.parent_entry_hash == entry1.entry_hash
    assert ledger.total_entries == 2
    assert ledger.tip_hash == entry2.entry_hash

    report = ledger.verify_integrity()
    assert report.status == LedgerIntegrityStatus.VALID
    assert report.valid_entries == 2


def test_ledger_duplicate_record_id_rejection():
    """Verify duplicate record_ids are rejected with DuplicateEvidenceError."""
    ledger = EvidenceLedger()
    r1 = _make_record("rec-dup")
    ledger.append_record(r1)

    r1_duplicate = _make_record("rec-dup")
    with pytest.raises(DuplicateEvidenceError):
        ledger.append_record(r1_duplicate)


def test_ledger_non_monotonic_commit_rejection():
    """Verify commits with backwards timestamps are strictly rejected."""
    ledger = EvidenceLedger()
    t0 = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    ledger.append_record(_make_record("r1"), override_committed_at=t0)

    t_past = t0 - timedelta(seconds=1)
    with pytest.raises(NonMonotonicCommitError):
        ledger.append_record(
            _make_record("r2"), override_committed_at=t_past
        )


def test_ledger_out_of_order_event_timestamps_allowed():
    """Verify event_timestamps can arrive out of order without rejection."""
    ledger = EvidenceLedger()
    t0 = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

    # Event 1 occurred at 12:00
    r1 = _make_record("r1", event_timestamp=t0)
    e1 = ledger.append_record(
        r1, override_committed_at=t0 + timedelta(minutes=1)
    )

    # Event 2 occurred at 11:30 (e.g. offline lab finished earlier)
    r2 = _make_record("r2", event_timestamp=t0 - timedelta(minutes=30))
    e2 = ledger.append_record(
        r2, override_committed_at=t0 + timedelta(minutes=2)
    )

    assert e1.entry_index == 0
    assert e2.entry_index == 1
    report = ledger.verify_integrity()
    assert report.status == LedgerIntegrityStatus.VALID


def test_ledger_cutoff_modes():
    """Verify COMMIT_TIME vs EVENT_TIME filtering on historical queries."""
    ledger = EvidenceLedger()
    t0 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)

    # Event A: event 10:00, commit 10:05
    r_a = _make_record("rA", node_id="node-x", event_timestamp=t0)
    ledger.append_record(r_a, override_committed_at=t0 + timedelta(minutes=5))

    # Event B: event 09:30 (past event!), commit 10:10
    r_b = _make_record(
        "rB", node_id="node-x", event_timestamp=t0 - timedelta(minutes=30)
    )
    ledger.append_record(r_b, override_committed_at=t0 + timedelta(minutes=10))

    # Event C: event 10:20, commit 10:25
    r_c = _make_record(
        "rC", node_id="node-x", event_timestamp=t0 + timedelta(minutes=20)
    )
    ledger.append_record(r_c, override_committed_at=t0 + timedelta(minutes=25))

    # 1. Query at commit_time = 10:08 (Should see only r_a)
    q_commit = ledger.get_history_for_node(
        node_id="node-x",
        as_of_time=t0 + timedelta(minutes=8),
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
    )
    assert [r.record_id for r in q_commit] == ["rA"]

    # 2. Query at event_time = 10:05 (Should see r_b and r_a, but not r_c)
    q_event = ledger.get_history_for_node(
        node_id="node-x",
        as_of_time=t0 + timedelta(minutes=5),
        cutoff_mode=HistoryCutoffMode.EVENT_TIME,
    )
    assert {r.record_id for r in q_event} == {"rA", "rB"}


def test_ledger_jsonl_persistence_and_reload(tmp_path: Path):
    """Verify ledger persists to JSONL and faithfully reloads chain."""
    file_path = tmp_path / "ledger" / "evidence.jsonl"

    ledger1 = EvidenceLedger(file_path=file_path)

    r1 = _make_record("rec-1")
    r2 = _make_record("rec-2")
    e1 = ledger1.append_record(r1)
    e2 = ledger1.append_record(r2)

    assert ledger1.total_entries == 2
    assert file_path.exists()

    # Re-instantiate from same file
    ledger2 = EvidenceLedger(file_path=file_path)
    assert ledger2.total_entries == 2
    assert ledger2.tip_hash == e2.entry_hash

    entry_reloaded_0 = ledger2.get_entry_by_index(0)
    assert entry_reloaded_0 is not None
    assert entry_reloaded_0.entry_hash == e1.entry_hash

    report = ledger2.verify_integrity()
    assert report.status == LedgerIntegrityStatus.VALID
    assert report.valid_entries == 2
