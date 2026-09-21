"""Authoritative ForensicAuditor facade coordinating Layers 1 & 2 for S4.4.

Enforces:
- HG-S4.4-01: Fail-Closed Deterministic Evaluation.
- HG-S4.4-07: Atomic Isolation of NLI.
- HG-S4.4-08: NLI Failure Is Not Approval.
- HG-S4.4-09: No Corpus Re-Retrieval.
- HG-S4.4-10: Immutable Forensic Traceability.
"""

import time
import uuid
from typing import List, Optional

from study_engine.audit.contracts import (
    AuditVerdict,
    CheckStatus,
    ClaimSupportVerdict,
    ClaimVerification,
    ForensicAuditInput,
    ForensicAuditReport,
    LexicalAnomalyStatus,
    LexicalDiagnostics,
)
from study_engine.audit.engine import DeterministicAuditEngine
from study_engine.audit.nli import BaseNLIJudge, MockNLIJudge, NLIAggregator


class ForensicAuditor:
    """Primary forensic auditor orchestrating deterministic & NLI checks."""

    def __init__(
        self,
        engine: Optional[DeterministicAuditEngine] = None,
        nli_judge: Optional[BaseNLIJudge] = None,
        nli_aggregator: Optional[NLIAggregator] = None,
        auditor_backend: str = "forensic-auditor-v1",
    ) -> None:
        self._engine = engine or DeterministicAuditEngine()
        self._nli_judge = nli_judge or MockNLIJudge()
        self._nli_aggregator = nli_aggregator or NLIAggregator()
        self._auditor_backend = auditor_backend

    def audit(self, audit_input: ForensicAuditInput) -> ForensicAuditReport:
        """Perform end-to-end forensic audit on a generation response."""
        start_time = time.perf_counter()
        req = audit_input.request
        ctx = req.packaged_context

        # Gather evidence hashes

        evidence_hashes = tuple(
            rec.content_hash for rec in ctx.citation_manifest.records.values()
        )

        # 1. Execute Layer 1 Deterministic Audit Engine
        det_res = self._engine.evaluate(audit_input)

        # 2. Check for Fail-Closed Critical Failure (HG-S4.4-01)
        if det_res.has_critical_failure:
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            # Build unassessed claim records
            verifications: List[ClaimVerification] = []
            for c in det_res.claims:
                diag = det_res.lexical_diagnostics.get(
                    c.claim_index,
                    LexicalDiagnostics(
                        status=LexicalAnomalyStatus.INCONCLUSIVE,
                        token_overlap_ratio=0.0,
                    ),
                )
                verifications.append(
                    ClaimVerification(
                        claim_index=c.claim_index,
                        claim_text=c.claim_text,
                        claim_type=c.claim_type,
                        cited_tags=c.cited_tags,
                        lexical_diagnostics=diag,
                        nli_verdict=ClaimSupportVerdict.UNASSESSED,
                        nli_confidence=None,
                        nli_rationale=(
                            "Bypassed by Layer 1 fail-closed critical failure"
                        ),
                    )
                )

            verdict = (
                det_res.early_verdict
                or AuditVerdict.REJECTED_POLICY_VIOLATION
            )
            return ForensicAuditReport(
                audit_id=f"audit_{uuid.uuid4().hex[:12]}",
                request_id=req.request_id,
                notebook_id=req.notebook_id,
                overall_verdict=verdict,
                deterministic_checks=det_res.checks,
                claim_verifications=tuple(verifications),
                nli_executed=False,
                nli_judge_id=None,
                prompt_hash=audit_input.prompt_hash,
                evidence_hashes=evidence_hashes,
                audit_latency_ms=round(latency_ms, 2),
                auditor_backend=self._auditor_backend,
            )

        # 3. Layer 2: Bounded Atomic NLI Evaluation (HG-S4.4-07, HG-S4.4-08)
        unit_map = {u.citation.citation_id: u for u in ctx.packaged_units}
        claim_verifications: List[ClaimVerification] = []

        for c in det_res.claims:
            diag = det_res.lexical_diagnostics.get(
                c.claim_index,
                LexicalDiagnostics(
                    status=LexicalAnomalyStatus.INCONCLUSIVE,
                    token_overlap_ratio=0.0,
                ),
            )

            # Conversational/pedagogical sentences default to entailed
            if not c.cited_tags:
                claim_verifications.append(
                    ClaimVerification(
                        claim_index=c.claim_index,
                        claim_text=c.claim_text,
                        claim_type=c.claim_type,
                        cited_tags=(),
                        lexical_diagnostics=diag,
                        nli_verdict=ClaimSupportVerdict.ENTAILED,
                        nli_confidence=1.0,
                        nli_rationale=(
                            "Non-factual sentence; no evidence required"
                        ),
                    )
                )
                continue

            # Evaluate claim against cited evidence
            # Multi-tag citations evaluate against the joint premise
            evidence_units = [
                unit_map[t] for t in c.cited_tags if t in unit_map
            ]
            premise = "\n\n".join(u.content for u in evidence_units)

            try:
                res = self._nli_judge.evaluate_claim(
                    premise=premise, hypothesis=c.claim_text
                )
                claim_verdict = res.verdict
                avg_conf = res.confidence
                tag_rationales = [res.rationale] if res.rationale else []
            except Exception as exc:
                # HG-S4.4-08: Failure is NOT approval
                claim_verdict = ClaimSupportVerdict.UNASSESSED
                avg_conf = None
                tag_rationales = [f"Judge error: {exc}"]

            claim_verifications.append(
                ClaimVerification(
                    claim_index=c.claim_index,
                    claim_text=c.claim_text,
                    claim_type=c.claim_type,
                    cited_tags=c.cited_tags,
                    lexical_diagnostics=diag,
                    nli_verdict=claim_verdict,
                    nli_confidence=round(avg_conf, 2) if avg_conf else None,
                    nli_rationale="; ".join(tag_rationales) or None,
                )
            )

        # 4. Aggregate claim verifications
        nli_verdict = self._nli_aggregator.aggregate(claim_verifications)

        # Invariant: ENTAILMENT from NLI is NOT automatic approval.
        # It proceeds to approval only if Layer 1 checks also passed.
        if nli_verdict == AuditVerdict.APPROVED:
            failing_checks = [
                ch for ch in det_res.checks if ch.status == CheckStatus.FAIL
            ]
            if failing_checks:
                overall_verdict = (
                    det_res.early_verdict
                    or AuditVerdict.REJECTED_POLICY_VIOLATION
                )
            else:
                overall_verdict = AuditVerdict.APPROVED
        else:
            overall_verdict = nli_verdict

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return ForensicAuditReport(
            audit_id=f"audit_{uuid.uuid4().hex[:12]}",
            request_id=req.request_id,
            notebook_id=req.notebook_id,
            overall_verdict=overall_verdict,
            deterministic_checks=det_res.checks,
            claim_verifications=tuple(claim_verifications),
            nli_executed=True,
            nli_judge_id=self._nli_judge.judge_id,
            prompt_hash=audit_input.prompt_hash,
            evidence_hashes=evidence_hashes,
            audit_latency_ms=round(latency_ms, 2),
            auditor_backend=self._auditor_backend,
        )
