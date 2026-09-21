"""Phase E2 Generation Verification Backstop enforcing H1 policy matrix and H4 bounded retry.

Architectural Guarantees:
- H1: Policy matrix routing per ClaimType (FORMAL, FACTUAL, PEDAGOGICAL, CONVERSATIONAL).
- H2: Dual UCR enforcement (zero tolerance for critical hallucinations; bounded non-critical).
- H3: Technical bilingual dictionary expansion.
- H4: Single bounded retry (max 1 retry with precision directive; subsequent redaction with [SIN_RESPALDO]; never tacit approval).
- Preserves frozen perimeter: leaves src/study_engine/audit/ unmutated.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from study_engine.evidence.claim_extractor import (
    ClaimCriticality,
    ClaimType,
    DeterministicClaimExtractor,
)
from study_engine.evidence.token_grounding import (
    GroundingStatus,
    TokenGroundingEngine,
)


class GenerationVerificationBackstop:
    """Zero-LLM deterministic generation verification backstop for Phase E2."""

    def __init__(self, bilingual_dict_path: Optional[Path] = None) -> None:
        self.bilingual_dict_path = (
            bilingual_dict_path
            if bilingual_dict_path
            else Path("data/benchmark/bilingual_dict_v1.json")
        )
        self.extractor = DeterministicClaimExtractor()
        self.grounder = TokenGroundingEngine(bilingual_dict_path=self.bilingual_dict_path)

    def verify_e2_claims(
        self,
        response_text: str,
        evidence_chunks: List[Any],
        bilingual_dict_path: Optional[Any] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """Verify response against admitted evidence enforcing H1 matrix and H4 bounded retry."""
        extracted_claims = self.extractor.extract_claims(response_text)

        dict_p = (
            Path(bilingual_dict_path)
            if bilingual_dict_path
            else self.bilingual_dict_path
        )
        grounder = (
            self.grounder
            if dict_p == self.bilingual_dict_path
            else TokenGroundingEngine(bilingual_dict_path=dict_p)
        )
        claim_results = grounder.ground_claims(extracted_claims, evidence_chunks)

        # Apply H1 Policy Matrix
        critical_unsupported = []
        has_formal_failure = False
        partially_supported = []

        for cr in claim_results:
            if cr.claim_type in (ClaimType.FORMAL_COMPLEXITY, ClaimType.FORMAL_ARITHMETIC):
                if cr.status != GroundingStatus.SUPPORTED:
                    has_formal_failure = True
                    critical_unsupported.append(cr)
            elif cr.claim_type == ClaimType.FACTUAL_TEXTUAL:
                if cr.status == GroundingStatus.CONTRADICTION:
                    critical_unsupported.append(cr)
                elif cr.status == GroundingStatus.UNSUPPORTED:
                    if cr.criticality == ClaimCriticality.CRITICAL:
                        critical_unsupported.append(cr)
                    else:
                        partially_supported.append(cr)
                elif cr.status == GroundingStatus.PARTIALLY_SUPPORTED:
                    partially_supported.append(cr)
            elif cr.claim_type == ClaimType.PEDAGOGICAL:
                # Handled in ground_claims (exempt from literal token grounding, passes if non-contradictory)
                if cr.status == GroundingStatus.CONTRADICTION:
                    critical_unsupported.append(cr)

        # Immediate hard abstention if formal check failed or critical factual claim is unsupported
        if has_formal_failure or critical_unsupported:
            return {
                "verdict": "REJECTED_UNSUPPORTED",
                "can_retry": False,
                "claims": claim_results,
                "critical_failures": [c.claim_id for c in critical_unsupported],
                "action": "HARD_ABSTENTION",
                "notes": "Hard abstention: formal calculation failed or critical factual claim is unsupported.",
            }

        # Apply H4: Single Bounded Retry for FLAGGED_UNASSESSED / PARTIALLY_SUPPORTED
        if partially_supported:
            if retry_count == 0:
                retry_directive = (
                    "Precision directive: Please clarify or provide grounded support for: "
                    + ", ".join(f"[{c.claim_id}] {c.claim_text}" for c in partially_supported)
                )
                return {
                    "verdict": "FLAGGED_UNASSESSED",
                    "can_retry": True,
                    "claims": claim_results,
                    "retry_directive": retry_directive,
                    "action": "BOUNDED_RETRY",
                    "notes": "Single bounded retry triggered for ambiguous/partially supported claims.",
                }
            else:
                # retry_count >= 1: Redact with [SIN_RESPALDO], never tacit approval
                redacted_text = response_text
                for c in partially_supported:
                    redacted_text = redacted_text.replace(c.claim_text, f"{c.claim_text} [SIN_RESPALDO]")
                return {
                    "verdict": "PARTIAL_ABSTENTION",
                    "can_retry": False,
                    "claims": claim_results,
                    "redacted_text": redacted_text,
                    "action": "REDACT_AMBIGUOUS",
                    "notes": "Retry limit reached (1/1); redacted ambiguous claims with [SIN_RESPALDO].",
                }

        return {
            "verdict": "APPROVED",
            "can_retry": False,
            "claims": claim_results,
            "action": "APPROVE",
            "notes": "All claims verified against H1 policy matrix.",
        }


# Convenience singleton function
def verify_e2_claims(
    response_text: str,
    evidence_chunks: List[Any],
    bilingual_dict_path: Optional[Any] = None,
    retry_count: int = 0,
) -> Dict[str, Any]:
    """Module-level convenience wrapper for GenerationVerificationBackstop.verify_e2_claims."""
    backstop = GenerationVerificationBackstop(bilingual_dict_path=bilingual_dict_path)
    return backstop.verify_e2_claims(
        response_text=response_text,
        evidence_chunks=evidence_chunks,
        bilingual_dict_path=bilingual_dict_path,
        retry_count=retry_count,
    )
