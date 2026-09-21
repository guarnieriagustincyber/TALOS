"""Adversarial and tamper-evidence tests for EvidenceLedger."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import pytest

from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import (
    DuplicateEvidenceError,
    LedgerIntegrityStatus,
    LedgerIntegrityViolationError,
    NonMonotonicCommitError,
)
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.state.policy_contracts import (
    ActorType,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)


def _make_record(record_id: str) -> EvidenceRecord:
    return EvidenceRecord(
        record_id=record_id,
        node_id="node-sec",
        evidence_type=EvidenceType.CODE_EXECUTION,
        outcome=EvidenceOutcome.PASS,
        score=1.0,
        timestamp=datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc),
        actor_type=ActorType.TOOL_VERIFIER,
        actor_id="pytest-runner",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
    )


def test_adversarial_tampered_jsonl_content_fails_load(tmp_path: Path):
    """Verify modifying a single char in JSONL record breaks the chain."""
    file_path = tmp_path / "tampered.jsonl"

    ledger = EvidenceLedger(file_path=file_path)

    ledger.append_record(_make_record("r1"))
    ledger.append_record(_make_record("r2"))
    ledger.append_record(_make_record("r3"))

    # Read and mutate line 2 (r2 score altered from 1.0 to 0.5)
    lines = file_path.read_text(encoding="utf-8").splitlines()
    data = json.loads(lines[1])
    data["record"]["score"] = 0.5
    lines[1] = json.dumps(data)
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Reopening the ledger must fail-closed on tampered hash
    with pytest.raises(LedgerIntegrityViolationError) as exc_info:
        EvidenceLedger(file_path=file_path)
    assert "Tampered entry_hash" in str(exc_info.value)


def test_adversarial_deleted_entry_in_middle_breaks_chain(tmp_path: Path):
    """Verify deleting an entry in the middle breaks index and parent hash."""
    file_path = tmp_path / "deleted.jsonl"
    ledger = EvidenceLedger(file_path=file_path)

    ledger.append_record(_make_record("r1"))
    ledger.append_record(_make_record("r2"))
    ledger.append_record(_make_record("r3"))

    # Delete entry index 1 (r2)
    lines = file_path.read_text(encoding="utf-8").splitlines()
    remaining = [lines[0], lines[2]]
    file_path.write_text("\n".join(remaining) + "\n", encoding="utf-8")

    with pytest.raises(LedgerIntegrityViolationError) as exc_info:
        EvidenceLedger(file_path=file_path)
    assert "Non-sequential entry_index" in str(exc_info.value)


def test_adversarial_crash_truncated_last_line(tmp_path: Path):
    """HG-S5.2B-06: Truncated last line from power loss triggers error."""
    file_path = tmp_path / "crashed.jsonl"
    ledger = EvidenceLedger(file_path=file_path)

    ledger.append_record(_make_record("r1"))
    ledger.append_record(_make_record("r2"))

    # Simulate crash mid-write of 3rd line
    with file_path.open("a", encoding="utf-8") as f:
        f.write('{"entry_index": 2, "record": {"record_id": "r3"')

    with pytest.raises(LedgerIntegrityViolationError) as exc_info:
        EvidenceLedger(file_path=file_path)
    assert "Corrupted entry at line 3" in str(exc_info.value)


def test_adversarial_duplicate_evidence_id_in_file(tmp_path: Path):
    """HG-S5.2B-07: Injected duplicate record_id is rejected on load."""
    file_path = tmp_path / "dup.jsonl"
    ledger = EvidenceLedger(file_path=file_path)

    e1 = ledger.append_record(_make_record("r1"))

    # Craft an entry with the same record_id but new index and valid hash
    r_dup = _make_record("r1")
    t1 = datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc)
    from study_engine.state.ledger_contracts import (
        EvidenceLedgerEntry,
        compute_ledger_entry_hash,
    )

    h = compute_ledger_entry_hash(1, e1.entry_hash, r_dup, t1)
    entry_dup = EvidenceLedgerEntry(
        entry_index=1,
        record=r_dup,
        parent_entry_hash=e1.entry_hash,
        entry_hash=h,
        committed_at=t1,
    )
    with file_path.open("a", encoding="utf-8") as f:
        f.write(entry_dup.model_dump_json() + "\n")

    with pytest.raises(DuplicateEvidenceError) as exc_info:
        EvidenceLedger(file_path=file_path)
    assert "Duplicate record_id 'r1'" in str(exc_info.value)


def test_adversarial_non_monotonic_commit_in_file(tmp_path: Path):
    """HG-S5.2B-03: Injected non-monotonic commit timestamp is rejected."""
    file_path = tmp_path / "non_monotonic.jsonl"
    ledger = EvidenceLedger(file_path=file_path)

    t0 = datetime(2026, 9, 1, 15, 0, tzinfo=timezone.utc)
    e1 = ledger.append_record(_make_record("r1"), override_committed_at=t0)

    # Inject second entry with earlier commit timestamp
    t_past = t0 - timedelta(hours=1)
    r2 = _make_record("r2")
    from study_engine.state.ledger_contracts import (
        EvidenceLedgerEntry,
        compute_ledger_entry_hash,
    )

    h2 = compute_ledger_entry_hash(1, e1.entry_hash, r2, t_past)
    entry_bad = EvidenceLedgerEntry(
        entry_index=1,
        record=r2,
        parent_entry_hash=e1.entry_hash,
        entry_hash=h2,
        committed_at=t_past,
    )
    with file_path.open("a", encoding="utf-8") as f:
        f.write(entry_bad.model_dump_json() + "\n")

    with pytest.raises(NonMonotonicCommitError) as exc_info:
        EvidenceLedger(file_path=file_path)
    assert "Non-monotonic commit" in str(exc_info.value)


def test_adversarial_altered_genesis_parent_hash(tmp_path: Path):
    """Verify first entry with non-zero parent hash is rejected."""
    file_path = tmp_path / "bad_genesis.jsonl"
    r1 = _make_record("r1")
    t0 = datetime(2026, 9, 1, 16, 0, tzinfo=timezone.utc)
    from study_engine.state.ledger_contracts import (
        EvidenceLedgerEntry,
        compute_ledger_entry_hash,
    )

    bad_parent = "f" * 64
    h = compute_ledger_entry_hash(0, bad_parent, r1, t0)
    entry_bad_genesis = EvidenceLedgerEntry(
        entry_index=0,
        record=r1,
        parent_entry_hash=bad_parent,
        entry_hash=h,
        committed_at=t0,
    )
    file_path.write_text(
        entry_bad_genesis.model_dump_json() + "\n", encoding="utf-8"
    )

    with pytest.raises(LedgerIntegrityViolationError) as exc_info:
        EvidenceLedger(file_path=file_path)
    assert "Broken hash chain at line 1" in str(exc_info.value)


def test_adversarial_verify_integrity_diagnoses_broken_chain():
    """Verify verify_integrity reports HASH_CHAIN_BROKEN on corrupt entry."""
    ledger = EvidenceLedger()

    ledger.append_record(_make_record("r1"))
    ledger.append_record(_make_record("r2"))

    # In-memory corruption simulation
    corrupt_entry = ledger._entries[1]
    from study_engine.state.ledger_contracts import EvidenceLedgerEntry
    tampered_entry = EvidenceLedgerEntry(
        entry_index=corrupt_entry.entry_index,
        record=corrupt_entry.record,
        parent_entry_hash=corrupt_entry.parent_entry_hash,
        entry_hash="a" * 64,  # forged hash
        committed_at=corrupt_entry.committed_at,
    )
    ledger._entries[1] = tampered_entry

    report = ledger.verify_integrity()
    assert report.status == LedgerIntegrityStatus.HASH_CHAIN_BROKEN
    assert report.first_invalid_index == 1
