"""Deterministic evidence ingestion engine for Subsystem S5.2.A.

INVARIANTS:
1. Two-stage pipeline: Admissibility determination -> Outcome.
2. 4 sequential admissibility gates: Integrity -> Provenance -> Session ->
   Anti-replay.
3. Halts on first failure; subsequent gates are SKIPPED.
4. REJECTED never generates EvidenceRecord, never touches ledger.
5. S5.2.A never recalibrates levels, scores, or pedagogical rationales.
6. Atomic duplicate race during ledger commit is safely converted to REJECTED.
"""

from datetime import datetime, timezone
from typing import Dict, Optional

from study_engine.contracts.assessment import (
    AssessmentResult,
    compute_canonical_sha256,
)
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
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import (
    DuplicateEvidenceError,
    InconsistentReplayError,
)
from study_engine.state.policy_contracts import (
    ActorType,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)


class EvidenceIngestionEngine:
    """Sovereign evidence intake engine enforcing admissibility policy."""

    def evaluate_admissibility(
        self,
        assessment: AssessmentResult,
        context: SessionProvenanceContext,
        ledger: Optional[EvidenceLedger] = None,
    ) -> AdmissionResult:
        """Evaluate assessment admissibility sequentially through 4 gates.

        Args:
            assessment: The sealed AssessmentResult from S9/S10.
            context: Verified session and curricular provenance context.
            ledger: Optional ledger for preflight anti-replay query.

        Returns:
            AdmissionResult with decision, outcome/reason, and trace.
        """
        now = datetime.now(timezone.utc)
        details: Dict[str, str] = {}

        # ---------------------------------------------------------------------
        # GATE 1: Integrity Gate
        # ---------------------------------------------------------------------
        core_for_hash = assessment.model_copy(update={"assessment_digest": ""})
        computed_digest = compute_canonical_sha256(core_for_hash)
        if (
            not assessment.assessment_digest
            or computed_digest != assessment.assessment_digest
        ):
            details["integrity.assessment_digest"] = "DIGEST_MISMATCH"
            trace = AdmissionTrace(
                integrity=GateVerdict.FAIL,
                provenance=GateVerdict.SKIPPED,
                session=GateVerdict.SKIPPED,
                anti_replay=GateVerdict.SKIPPED,
                details=details,
            )
            return AdmissionResult(
                decision=AdmissionDecision.REJECTED,
                rejection_reason=RejectionReason.CORRUPTED_ASSESSMENT_DIGEST,
                rejection_detail=(
                    f"Declared digest '{assessment.assessment_digest}' != "
                    f"computed canonical digest '{computed_digest}'."
                ),
                admission_trace=trace,
                evaluated_at=now,
            )

        if (
            assessment.authority_id
            != EpistemologicalAuthority.ASSESSMENT_ENGINE.value
        ):
            details["integrity.authority"] = "UNAUTHORIZED_AUTHORITY"
            trace = AdmissionTrace(
                integrity=GateVerdict.FAIL,
                provenance=GateVerdict.SKIPPED,
                session=GateVerdict.SKIPPED,
                anti_replay=GateVerdict.SKIPPED,
                details=details,
            )
            return AdmissionResult(
                decision=AdmissionDecision.REJECTED,
                rejection_reason=(
                    RejectionReason.UNAUTHORIZED_ASSESSMENT_AUTHORITY
                ),
                rejection_detail=(
                    f"Authority '{assessment.authority_id}' is not authorized "
                    f"for AssessmentResult."
                ),
                admission_trace=trace,
                evaluated_at=now,
            )

        # Specification hash matching against active curriculum
        if (
            context.expected_task_specification_sha256
            and assessment.task.specification_sha256
            != context.expected_task_specification_sha256
        ):
            details["integrity.specification"] = "TASK_SPEC_MISMATCH"
            trace = AdmissionTrace(
                integrity=GateVerdict.FAIL,
                provenance=GateVerdict.SKIPPED,
                session=GateVerdict.SKIPPED,
                anti_replay=GateVerdict.SKIPPED,
                details=details,
            )
            return AdmissionResult(
                decision=AdmissionDecision.REJECTED,
                rejection_reason=(
                    RejectionReason.SPECIFICATION_REVISION_MISMATCH
                ),
                rejection_detail="Task specification hash mismatch.",
                admission_trace=trace,
                evaluated_at=now,
            )

        if (
            context.expected_rubric_specification_sha256
            and assessment.rubric.specification_sha256
            != context.expected_rubric_specification_sha256
        ):
            details["integrity.specification"] = "RUBRIC_SPEC_MISMATCH"
            trace = AdmissionTrace(
                integrity=GateVerdict.FAIL,
                provenance=GateVerdict.SKIPPED,
                session=GateVerdict.SKIPPED,
                anti_replay=GateVerdict.SKIPPED,
                details=details,
            )
            return AdmissionResult(
                decision=AdmissionDecision.REJECTED,
                rejection_reason=(
                    RejectionReason.SPECIFICATION_REVISION_MISMATCH
                ),
                rejection_detail="Rubric specification hash mismatch.",
                admission_trace=trace,
                evaluated_at=now,
            )

        details["integrity.status"] = "PASSED"

        # ---------------------------------------------------------------------
        # GATE 2: Provenance Gate
        # ---------------------------------------------------------------------
        if not assessment.observations or len(assessment.observations) == 0:
            details["provenance.observations"] = "MISSING_OBSERVATIONS"
            trace = AdmissionTrace(
                integrity=GateVerdict.PASS,
                provenance=GateVerdict.FAIL,
                session=GateVerdict.SKIPPED,
                anti_replay=GateVerdict.SKIPPED,
                details=details,
            )
            return AdmissionResult(
                decision=AdmissionDecision.REJECTED,
                rejection_reason=RejectionReason.BROKEN_PROVENANCE_CHAIN,
                rejection_detail="Assessment lacks observation references.",
                admission_trace=trace,
                evaluated_at=now,
            )

        if context.spine is not None:
            # Lineage binding checks against spine
            spine_curriculum = context.spine.curriculum
            if (
                spine_curriculum.curriculum_node_id
                != context.resolved_target_node_id
            ):
                details["provenance.spine"] = "SPINE_NODE_MISMATCH"
                trace = AdmissionTrace(
                    integrity=GateVerdict.PASS,
                    provenance=GateVerdict.FAIL,
                    session=GateVerdict.SKIPPED,
                    anti_replay=GateVerdict.SKIPPED,
                    details=details,
                )
                return AdmissionResult(
                    decision=AdmissionDecision.REJECTED,
                    rejection_reason=RejectionReason.BROKEN_PROVENANCE_CHAIN,
                    rejection_detail="Spine curriculum node mismatch.",
                    admission_trace=trace,
                    evaluated_at=now,
                )

        details["provenance.status"] = "PASSED"

        # ---------------------------------------------------------------------
        # GATE 3: Session & Context Gate
        # ---------------------------------------------------------------------
        if context.spine is not None:
            if context.spine.identity.student_id != context.student_id:
                details["session.identity"] = "STUDENT_MISMATCH"
                trace = AdmissionTrace(
                    integrity=GateVerdict.PASS,
                    provenance=GateVerdict.PASS,
                    session=GateVerdict.FAIL,
                    anti_replay=GateVerdict.SKIPPED,
                    details=details,
                )
                return AdmissionResult(
                    decision=AdmissionDecision.REJECTED,
                    rejection_reason=RejectionReason.STUDENT_IDENTITY_MISMATCH,
                    rejection_detail=(
                        "Spine student_id does not match context."
                    ),
                    admission_trace=trace,
                    evaluated_at=now,
                )

        # Deterministic session temporal check at assessment.assessed_at
        if not context.session_is_active:
            details["session.temporal"] = "SESSION_INACTIVE"
            trace = AdmissionTrace(
                integrity=GateVerdict.PASS,
                provenance=GateVerdict.PASS,
                session=GateVerdict.FAIL,
                anti_replay=GateVerdict.SKIPPED,
                details=details,
            )
            return AdmissionResult(
                decision=AdmissionDecision.REJECTED,
                rejection_reason=RejectionReason.SESSION_INACTIVE_OR_EXPIRED,
                rejection_detail="Session is marked inactive.",
                admission_trace=trace,
                evaluated_at=now,
            )

        if assessment.assessed_at < context.session_started_at:
            details["session.temporal"] = "PREDATES_SESSION_START"
            trace = AdmissionTrace(
                integrity=GateVerdict.PASS,
                provenance=GateVerdict.PASS,
                session=GateVerdict.FAIL,
                anti_replay=GateVerdict.SKIPPED,
                details=details,
            )
            return AdmissionResult(
                decision=AdmissionDecision.REJECTED,
                rejection_reason=RejectionReason.SESSION_INACTIVE_OR_EXPIRED,
                rejection_detail=(
                    "Assessment timestamp predates session start."
                ),
                admission_trace=trace,
                evaluated_at=now,
            )

        if (
            context.session_expires_at is not None
            and assessment.assessed_at > context.session_expires_at
        ):
            details["session.temporal"] = "POSTDATES_SESSION_EXPIRATION"
            trace = AdmissionTrace(
                integrity=GateVerdict.PASS,
                provenance=GateVerdict.PASS,
                session=GateVerdict.FAIL,
                anti_replay=GateVerdict.SKIPPED,
                details=details,
            )
            return AdmissionResult(
                decision=AdmissionDecision.REJECTED,
                rejection_reason=RejectionReason.SESSION_INACTIVE_OR_EXPIRED,
                rejection_detail=(
                    "Assessment timestamp postdates session expiration."
                ),
                admission_trace=trace,
                evaluated_at=now,
            )

        details["session.status"] = "PASSED"

        # ---------------------------------------------------------------------
        # GATE 4: Anti-Replay Preflight Gate
        # ---------------------------------------------------------------------
        if ledger is not None and ledger.has_assessment_digest(
            assessment.assessment_digest
        ):
            details["anti_replay.preflight"] = "DUPLICATE_DIGEST"
            trace = AdmissionTrace(
                integrity=GateVerdict.PASS,
                provenance=GateVerdict.PASS,
                session=GateVerdict.PASS,
                anti_replay=GateVerdict.FAIL,
                details=details,
            )
            return AdmissionResult(
                decision=AdmissionDecision.REJECTED,
                rejection_reason=RejectionReason.DUPLICATE_ASSESSMENT_REPLAY,
                rejection_detail=(
                    f"Assessment digest '{assessment.assessment_digest}' "
                    f"already committed in ledger or detected by preflight "
                    f"oracle."
                ),
                admission_trace=trace,
                evaluated_at=now,
            )

        details["anti_replay.status"] = "PASSED"

        # ---------------------------------------------------------------------
        # ALL 4 GATES PASSED: Map Epistemological Outcome
        # ---------------------------------------------------------------------
        trace = AdmissionTrace(
            integrity=GateVerdict.PASS,
            provenance=GateVerdict.PASS,
            session=GateVerdict.PASS,
            anti_replay=GateVerdict.PASS,
            details=details,
        )

        # Epistemological outcome mapping
        if len(assessment.aggregation.insufficient_dimensions) > 0:
            outcome = EvidenceOutcome.INCONCLUSIVE
        elif assessment.aggregation.passed:
            outcome = EvidenceOutcome.PASS
        else:
            outcome = EvidenceOutcome.FAIL

        return AdmissionResult(
            decision=AdmissionDecision.ADMITTED,
            outcome=outcome,
            rejection_reason=None,
            rejection_detail=None,
            admission_trace=trace,
            evaluated_at=now,
        )

    def build_admitted_record(
        self,
        assessment: AssessmentResult,
        context: SessionProvenanceContext,
        outcome: EvidenceOutcome,
        trace: AdmissionTrace,
    ) -> EvidenceRecord:
        """Construct sealed EvidenceRecord with sovereign authority stamp.

        Copies overall_level verbatim from AssessmentResult without secondary
        re-scoring or evaluation.
        """
        score = 1.0 if outcome == EvidenceOutcome.PASS else 0.0
        spine_id = context.spine.spine_id if context.spine else None

        return EvidenceRecord(
            record_id=f"ev-{assessment.assessment_digest[:16]}",
            student_id=context.student_id,
            node_id=context.resolved_target_node_id,
            evidence_type=EvidenceType.CODE_EXECUTION,
            outcome=outcome,
            score=score,
            timestamp=assessment.assessed_at,
            actor_type=ActorType.TOOL_VERIFIER,
            actor_id=assessment.evaluator_id,
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
            assessment_digest=assessment.assessment_digest,
            spine_id=spine_id,
            overall_level=assessment.aggregation.overall_level,
            roadmap_revision_id=context.roadmap_revision_id,
            policy_revision_id=context.policy_revision_id,
            rationale=(
                f"Admitted practical assessment. Gates: "
                f"integrity={trace.integrity.value}, "
                f"provenance={trace.provenance.value}, "
                f"session={trace.session.value}, "
                f"anti_replay={trace.anti_replay.value}."
            ),
            metadata={
                "evaluator_version": assessment.evaluator_version,
                "insufficient_dimensions": list(
                    assessment.aggregation.insufficient_dimensions
                ),
                "critical_failures": list(
                    assessment.aggregation.critical_dimension_failures
                ),
                "admission_trace_details": trace.details,
            },
        )

    def ingest_assessment(
        self,
        assessment: AssessmentResult,
        context: SessionProvenanceContext,
        ledger: EvidenceLedger,
    ) -> EvidenceIngestionResult:
        """Perform preflight evaluation and atomic ledger commitment.

        Args:
            assessment: The sealed AssessmentResult.
            context: SessionProvenanceContext binding student and curriculum.
            ledger: EvidenceLedger for atomic persistence.

        Returns:
            EvidenceIngestionResult encapsulating admission, record, and entry.
        """
        # 1. Preflight admissibility evaluation
        admission = self.evaluate_admissibility(
            assessment=assessment,
            context=context,
            ledger=ledger,
        )

        if admission.decision == AdmissionDecision.REJECTED:
            return EvidenceIngestionResult(
                admission=admission,
                evidence_record=None,
                ledger_entry=None,
            )

        assert admission.outcome is not None

        # 2. Build sovereign EvidenceRecord
        record = self.build_admitted_record(
            assessment=assessment,
            context=context,
            outcome=admission.outcome,
            trace=admission.admission_trace,
        )

        # 3. Atomic commit to ledger
        try:
            entry = ledger.append_record(record)
            return EvidenceIngestionResult(
                admission=admission,
                evidence_record=record,
                ledger_entry=entry,
            )
        except InconsistentReplayError as exc:
            # Divergent assessment result submitted for existing evaluation attempt ID
            collision_details = dict(admission.admission_trace.details)
            collision_details["anti_replay.inconsistent_replay"] = str(exc)

            inconsistent_trace = AdmissionTrace(
                integrity=admission.admission_trace.integrity,
                provenance=admission.admission_trace.provenance,
                session=admission.admission_trace.session,
                anti_replay=GateVerdict.FAIL,
                details=collision_details,
            )
            rejected_admission = AdmissionResult(
                decision=AdmissionDecision.REJECTED,
                outcome=None,
                rejection_reason=RejectionReason.INCONSISTENT_ASSESSMENT_REPLAY,
                rejection_detail=(
                    "Divergent assessment digest submitted for existing evaluation attempt ID."
                ),
                admission_trace=inconsistent_trace,
                evaluated_at=datetime.now(timezone.utc),
            )
            return EvidenceIngestionResult(
                admission=rejected_admission,
                evidence_record=None,
                ledger_entry=None,
            )
        except DuplicateEvidenceError as exc:
            # Atomic race collision detected during ledger append!
            # Safely transform to final REJECTED result.
            collision_details = dict(admission.admission_trace.details)
            collision_details["anti_replay.atomic_collision"] = str(exc)

            race_trace = AdmissionTrace(
                integrity=admission.admission_trace.integrity,
                provenance=admission.admission_trace.provenance,
                session=admission.admission_trace.session,
                anti_replay=GateVerdict.FAIL,
                details=collision_details,
            )
            rejected_admission = AdmissionResult(
                decision=AdmissionDecision.REJECTED,
                outcome=None,
                rejection_reason=RejectionReason.DUPLICATE_ASSESSMENT_REPLAY,
                rejection_detail=(
                    "Concurrent duplicate detected during atomic commit."
                ),
                admission_trace=race_trace,
                evaluated_at=datetime.now(timezone.utc),
            )
            return EvidenceIngestionResult(
                admission=rejected_admission,
                evidence_record=None,
                ledger_entry=None,
            )
