"""Contract tests for Subsystem S5.2.B Evidence Ledger contracts."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.state.ledger_contracts import (
    EvidenceLedgerEntry,
    HistoryCutoffMode,
    LedgerIntegrityReport,
    LedgerIntegrityStatus,
    canonicalize_ledger_entry_payload,
    compute_ledger_entry_hash,
)
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.state.policy_contracts import (
    ActorType,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)


def _make_dummy_record(
    record_id: str = "rec-1",
    metadata: dict = None,
) -> EvidenceRecord:
    return EvidenceRecord(
        record_id=record_id,
        node_id="proc-intro",
        evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
        outcome=EvidenceOutcome.PASS,
        score=0.95,
        timestamp=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        actor_type=ActorType.AI_TUTOR,
        actor_id="tutor-1",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        audit_verdict="APPROVED",
        metadata=metadata or {},
    )


def test_ledger_entry_immutability():
    """Verify EvidenceLedgerEntry is frozen against mutation."""
    rec = _make_dummy_record()
    committed = datetime(2026, 9, 1, 10, 5, tzinfo=timezone.utc)
    entry = EvidenceLedgerEntry(
        entry_index=0,
        record=rec,
        parent_entry_hash="0" * 64,
        entry_hash="a" * 64,
        committed_at=committed,
    )

    with pytest.raises(ValidationError):
        entry.entry_index = 1  # type: ignore[misc]

    with pytest.raises(ValidationError):
        entry.entry_hash = "b" * 64  # type: ignore[misc]


def test_ledger_integrity_report_immutability():
    """Verify LedgerIntegrityReport is frozen against mutation."""
    report = LedgerIntegrityReport(
        status=LedgerIntegrityStatus.VALID,
        total_entries=5,
        valid_entries=5,
        tip_hash="a" * 64,
        details="Chain valid",
    )
    with pytest.raises(ValidationError):
        broken = LedgerIntegrityStatus.HASH_CHAIN_BROKEN
        report.status = broken  # type: ignore[misc]


def test_hash_field_validation():
    """Verify parent_entry_hash and entry_hash must be exactly 64 hex chars."""
    rec = _make_dummy_record()
    committed = datetime.now(timezone.utc)

    # Invalid length
    with pytest.raises(ValidationError):
        EvidenceLedgerEntry(
            entry_index=0,
            record=rec,
            parent_entry_hash="short",
            entry_hash="a" * 64,
            committed_at=committed,
        )

    # Non-hex characters
    with pytest.raises(ValidationError):
        EvidenceLedgerEntry(
            entry_index=0,
            record=rec,
            parent_entry_hash="z" * 64,
            entry_hash="a" * 64,
            committed_at=committed,
        )


def test_canonicalize_payload_determinism():
    """Verify canonical payload is invariant to dict key insertion order."""

    r1 = _make_dummy_record(metadata={"z_key": 1, "a_key": 2, "m_key": 3})
    r2 = _make_dummy_record(metadata={"a_key": 2, "m_key": 3, "z_key": 1})

    committed = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    payload1 = canonicalize_ledger_entry_payload(
        entry_index=0,
        parent_entry_hash="0" * 64,
        record=r1,
        committed_at=committed,
    )
    payload2 = canonicalize_ledger_entry_payload(
        entry_index=0,
        parent_entry_hash="0" * 64,
        record=r2,
        committed_at=committed,
    )
    assert payload1 == payload2

    hash1 = compute_ledger_entry_hash(0, "0" * 64, r1, committed)
    hash2 = compute_ledger_entry_hash(0, "0" * 64, r2, committed)
    assert hash1 == hash2
    assert len(hash1) == 64


def test_closed_enums():
    """Verify all ledger enums contain expected closed variants."""
    assert set(HistoryCutoffMode) == {
        HistoryCutoffMode.COMMIT_TIME,
        HistoryCutoffMode.EVENT_TIME,
    }
    assert set(LedgerIntegrityStatus) == {
        LedgerIntegrityStatus.VALID,
        LedgerIntegrityStatus.HASH_CHAIN_BROKEN,
        LedgerIntegrityStatus.NON_MONOTONIC_COMMIT,
        LedgerIntegrityStatus.DUPLICATE_EVIDENCE_ID,
        LedgerIntegrityStatus.GENESIS_MISMATCH,
        LedgerIntegrityStatus.CORRUPTED_ENTRY,
    }
