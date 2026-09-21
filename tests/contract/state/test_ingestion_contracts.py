"""Contract tests for Subsystem S5.2.A Evidence Ingestion contracts."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.contracts.evidence_ingestion import (
    AdmissionDecision,
    AdmissionResult,
    AdmissionTrace,
    EvidenceIngestionResult,
    GateVerdict,
    RejectionReason,
    SessionProvenanceContext,
)
from study_engine.state.ledger_contracts import EvidenceLedgerEntry
from study_engine.state.policy_contracts import (
    ActorType,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)


def _make_trace(
    integrity: GateVerdict = GateVerdict.PASS,
    provenance: GateVerdict = GateVerdict.PASS,
    session: GateVerdict = GateVerdict.PASS,
    anti_replay: GateVerdict = GateVerdict.PASS,
) -> AdmissionTrace:
    return AdmissionTrace(
        integrity=integrity,
        provenance=provenance,
        session=session,
        anti_replay=anti_replay,
        details={"trace.test": "ok"},
    )


def _make_dummy_evidence() -> EvidenceRecord:
    return EvidenceRecord(
        record_id="rec-test-1",
        node_id="NET-01",
        evidence_type=EvidenceType.CODE_EXECUTION,
        outcome=EvidenceOutcome.PASS,
        score=1.0,
        timestamp=datetime.now(timezone.utc),
        actor_type=ActorType.TOOL_VERIFIER,
        actor_id="s9_engine",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        assessment_digest="a" * 64,
        policy_revision_id="b" * 64,
        roadmap_revision_id="c" * 64,
    )


class TestIngestionContracts:
    """Contract verification for S5.2.A models and state validators."""

    def test_admission_result_admitted_invariants(self) -> None:
        """ADMITTED decision requires outcome and forbids rejection_reason."""
        trace = _make_trace()
        now = datetime.now(timezone.utc)

        # 1. Valid ADMITTED result
        res = AdmissionResult(
            decision=AdmissionDecision.ADMITTED,
            outcome=EvidenceOutcome.PASS,
            admission_trace=trace,
            evaluated_at=now,
        )
        assert res.decision == AdmissionDecision.ADMITTED
        assert res.outcome == EvidenceOutcome.PASS
        assert res.rejection_reason is None

        # 2. ADMITTED missing outcome fails
        with pytest.raises(ValidationError):
            AdmissionResult(
                decision=AdmissionDecision.ADMITTED,
                outcome=None,
                admission_trace=trace,
                evaluated_at=now,
            )

        # 3. ADMITTED with rejection_reason fails
        with pytest.raises(ValidationError):
            AdmissionResult(
                decision=AdmissionDecision.ADMITTED,
                outcome=EvidenceOutcome.PASS,
                rejection_reason=RejectionReason.CORRUPTED_ASSESSMENT_DIGEST,
                admission_trace=trace,
                evaluated_at=now,
            )

    def test_admission_result_rejected_invariants(self) -> None:
        """REJECTED decision requires rejection_reason and forbids outcome."""
        trace = _make_trace(integrity=GateVerdict.FAIL)
        now = datetime.now(timezone.utc)

        # 1. Valid REJECTED result
        res = AdmissionResult(
            decision=AdmissionDecision.REJECTED,
            rejection_reason=RejectionReason.CORRUPTED_ASSESSMENT_DIGEST,
            rejection_detail="Digest mismatch",
            admission_trace=trace,
            evaluated_at=now,
        )
        assert res.decision == AdmissionDecision.REJECTED
        assert res.outcome is None
        assert res.rejection_reason == (
            RejectionReason.CORRUPTED_ASSESSMENT_DIGEST
        )

        # 2. REJECTED missing rejection_reason fails
        with pytest.raises(ValidationError):
            AdmissionResult(
                decision=AdmissionDecision.REJECTED,
                rejection_reason=None,
                admission_trace=trace,
                evaluated_at=now,
            )

        # 3. REJECTED with outcome fails
        with pytest.raises(ValidationError):
            AdmissionResult(
                decision=AdmissionDecision.REJECTED,
                outcome=EvidenceOutcome.FAIL,
                rejection_reason=RejectionReason.DUPLICATE_ASSESSMENT_REPLAY,
                admission_trace=trace,
                evaluated_at=now,
            )

    def test_evidence_ingestion_result_state_invariants(self) -> None:
        """Verify invariants on EvidenceIngestionResult."""
        now = datetime.now(timezone.utc)
        rec = _make_dummy_evidence()
        entry = EvidenceLedgerEntry(
            entry_index=0,
            record=rec,
            parent_entry_hash="0" * 64,
            entry_hash="f" * 64,
            committed_at=now,
        )

        admitted_admission = AdmissionResult(
            decision=AdmissionDecision.ADMITTED,
            outcome=EvidenceOutcome.PASS,
            admission_trace=_make_trace(),
            evaluated_at=now,
        )

        rejected_admission = AdmissionResult(
            decision=AdmissionDecision.REJECTED,
            rejection_reason=RejectionReason.SESSION_INACTIVE_OR_EXPIRED,
            admission_trace=_make_trace(session=GateVerdict.FAIL),
            evaluated_at=now,
        )

        # 1. Valid ADMITTED preflight (no ledger entry)
        ing_pre = EvidenceIngestionResult(
            admission=admitted_admission,
            evidence_record=rec,
            ledger_entry=None,
        )
        assert ing_pre.evidence_record is not None
        assert ing_pre.ledger_entry is None

        # 2. Valid ADMITTED persisted
        ing_pers = EvidenceIngestionResult(
            admission=admitted_admission,
            evidence_record=rec,
            ledger_entry=entry,
        )
        assert ing_pers.evidence_record is not None
        assert ing_pers.ledger_entry is not None

        # 3. ADMITTED missing evidence_record fails
        with pytest.raises(ValidationError):
            EvidenceIngestionResult(
                admission=admitted_admission,
                evidence_record=None,
            )

        # 4. Valid REJECTED result
        ing_rej = EvidenceIngestionResult(
            admission=rejected_admission,
            evidence_record=None,
            ledger_entry=None,
        )
        assert ing_rej.evidence_record is None
        assert ing_rej.ledger_entry is None

        # 5. REJECTED with evidence_record fails
        with pytest.raises(ValidationError):
            EvidenceIngestionResult(
                admission=rejected_admission,
                evidence_record=rec,
            )

        # 6. REJECTED with ledger_entry fails
        with pytest.raises(ValidationError):
            EvidenceIngestionResult(
                admission=rejected_admission,
                ledger_entry=entry,
            )

    def test_session_provenance_context_validation(self) -> None:
        """Verify field lengths and validation rules for session context."""
        now = datetime.now(timezone.utc)
        ctx = SessionProvenanceContext(
            student_id="student-1",
            session_id="session-1",
            resolved_target_node_id="NET-01",
            roadmap_revision_id="0" * 64,
            policy_revision_id="1" * 64,
            session_started_at=now,
        )
        assert ctx.student_id == "student-1"
        assert ctx.resolved_target_node_id == "NET-01"

        # Invalid revision length fails
        with pytest.raises(ValidationError):
            SessionProvenanceContext(
                student_id="student-1",
                session_id="session-1",
                resolved_target_node_id="NET-01",
                roadmap_revision_id="short_hash",
                policy_revision_id="1" * 64,
                session_started_at=now,
            )
