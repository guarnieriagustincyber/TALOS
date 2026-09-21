"""Deterministic audit engine coordinating Layer 1 checks for S4.4.

Enforces:
- HG-S4.4-01: Fail-Closed Deterministic Evaluation.
- HG-S4.4-02: Input Identity Verification.
- HG-S4.4-03: Manifest and Hash Integrity.
- HG-S4.4-04: Mandatory Abstention Compliance.
- HG-S4.4-05: P7 Structural Mastery Protection.
- HG-S4.4-06: Lexical Diagnostics (Telemetry only).
"""

from typing import Dict, List, Optional, Tuple
from pydantic import ConfigDict, Field

from study_engine.contracts.base import BaseContract
from study_engine.audit.contracts import (
    AuditVerdict,
    CheckSeverity,
    CheckStatus,
    ClaimType,
    DeterministicAuditCheck,
    ForensicAuditInput,
    LexicalDiagnostics,
)
from study_engine.audit.claim_extractor import ClaimExtractor, ExtractedClaim
from study_engine.audit.citation_verifier import CitationVerifier
from study_engine.audit.policy_guard import PolicyGuard
from study_engine.audit.injection_guard import InjectionGuard
from study_engine.audit.lexical_guard import LexicalGuard


class DeterministicEngineResult(BaseContract):
    """Immutable output from Layer 1 deterministic audit engine."""

    model_config = ConfigDict(frozen=True)

    claims: Tuple[ExtractedClaim, ...] = Field(
        default_factory=tuple,
        description="Extracted and classified claims from response text",
    )
    checks: Tuple[DeterministicAuditCheck, ...] = Field(
        default_factory=tuple,
        description="Executed deterministic audit checks",
    )
    lexical_diagnostics: Dict[int, LexicalDiagnostics] = Field(
        default_factory=dict,
        description="Lexical diagnostics keyed by claim index",
    )
    has_critical_failure: bool = Field(
        ..., description="True if any critical check failed (fail-closed)"
    )
    early_verdict: Optional[AuditVerdict] = Field(
        default=None,
        description="Immediate rejection verdict if critical failure occurred",
    )


class DeterministicAuditEngine:
    """Coordinating engine for all Layer 1 deterministic audit checks."""

    def __init__(
        self,
        claim_extractor: Optional[ClaimExtractor] = None,
        citation_verifier: Optional[CitationVerifier] = None,
        policy_guard: Optional[PolicyGuard] = None,
        injection_guard: Optional[InjectionGuard] = None,
        lexical_guard: Optional[LexicalGuard] = None,
    ) -> None:
        self._claim_extractor = claim_extractor or ClaimExtractor()
        self._citation_verifier = citation_verifier or CitationVerifier()
        self._policy_guard = policy_guard or PolicyGuard()
        self._injection_guard = injection_guard or InjectionGuard()
        self._lexical_guard = lexical_guard or LexicalGuard()

    def evaluate(
        self, audit_input: ForensicAuditInput
    ) -> DeterministicEngineResult:
        """Run all Layer 1 checks and return deterministic result."""
        checks: List[DeterministicAuditCheck] = []

        # 1. Input identity and manifest integrity
        checks.extend(self._citation_verifier.verify(audit_input))

        # 2. Policy, abstention, and P7
        checks.extend(self._policy_guard.verify(audit_input))

        # 3. Injection and canary scans
        checks.extend(self._injection_guard.verify(audit_input))

        # 4. Extract claims
        resp_text = audit_input.response.text
        claims = self._claim_extractor.extract_claims(resp_text)

        # 5. Check grounding: factual claims must cite evidence
        ctx = audit_input.request.packaged_context
        unsupported_factual_indices: List[int] = []

        if not ctx.packet.abstention_required:
            for c in claims:
                if c.claim_type == ClaimType.FACTUAL and not c.cited_tags:
                    unsupported_factual_indices.append(c.claim_index)

        if unsupported_factual_indices:
            checks.append(
                DeterministicAuditCheck(
                    check_id="CHECK_FACTUAL_GROUNDING",
                    status=CheckStatus.FAIL,
                    severity=CheckSeverity.CRITICAL,
                    reason=(
                        f"Factual claims without citations detected: "
                        f"indices {unsupported_factual_indices}"
                    ),
                )
            )
        else:
            checks.append(
                DeterministicAuditCheck(
                    check_id="CHECK_FACTUAL_GROUNDING",
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.CRITICAL,
                    reason="All factual claims cite packaged evidence tags.",
                )
            )

        # 6. Lexical diagnostics per claim
        diagnostics_map: Dict[int, LexicalDiagnostics] = {}
        unit_map = {u.citation.citation_id: u for u in ctx.packaged_units}
        for c in claims:
            evidence_texts: List[str] = []
            for tag in c.cited_tags:
                if tag in unit_map:
                    evidence_texts.append(unit_map[tag].content)
            combined_evidence = " ".join(evidence_texts)

            diag = self._lexical_guard.diagnose(

                claim_text=c.claim_text,
                evidence_text=combined_evidence,
                claim_type=c.claim_type,
            )
            diagnostics_map[c.claim_index] = diag

        # 7. Evaluate fail-closed critical failures
        failed_critical = [
            c for c in checks
            if c.status == CheckStatus.FAIL
            and c.severity == CheckSeverity.CRITICAL
        ]
        has_critical_failure = len(failed_critical) > 0
        early_verdict = (
            self._determine_early_verdict(checks)
            if has_critical_failure
            else None
        )

        return DeterministicEngineResult(
            claims=claims,
            checks=tuple(checks),
            lexical_diagnostics=diagnostics_map,
            has_critical_failure=has_critical_failure,
            early_verdict=early_verdict,
        )

    def _determine_early_verdict(
        self, checks: List[DeterministicAuditCheck]
    ) -> AuditVerdict:
        """Map specific check failures to definitive audit verdicts."""
        failed_ids = {
            c.check_id for c in checks
            if c.status == CheckStatus.FAIL
            and c.severity == CheckSeverity.CRITICAL
        }

        if "CHECK_INPUT_IDENTITY" in failed_ids:
            return AuditVerdict.REJECTED_INPUT_MISMATCH
        if "CHECK_MANDATORY_ABSTENTION" in failed_ids:
            return AuditVerdict.REJECTED_ABSTENTION_VIOLATION
        if "CHECK_P7_MASTERY_MUTATION" in failed_ids:
            return AuditVerdict.REJECTED_POLICY_VIOLATION
        if (
            "CHECK_INJECTION_CANARY" in failed_ids
            or "CHECK_INJECTION_ECHO" in failed_ids
        ):
            return AuditVerdict.REJECTED_INJECTION_DETECTED
        if (
            "CHECK_MANIFEST_INTEGRITY" in failed_ids
            or "CHECK_FACTUAL_GROUNDING" in failed_ids
        ):
            return AuditVerdict.REJECTED_UNSUPPORTED
        if "CHECK_SOURCE_PROVENANCE" in failed_ids:
            return AuditVerdict.UNVERIFIED_SOURCE

        return AuditVerdict.REJECTED_POLICY_VIOLATION
