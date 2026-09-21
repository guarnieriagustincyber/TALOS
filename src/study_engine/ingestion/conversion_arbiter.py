"""Conversion Arbiter and Representation Conflict Engine for CAL (Subsystem S1).

Arbitrates dual-conversion outputs and exposes CONVERSION_CONFLICT without smoothing or averaging.
INVARIANTS:
1. CONVERSION_DIFF != CONTENT_CONTRADICTION: Exposed as structural representation divergence.
2. Canonical selection rule (CAL-1):
   - In conflict: Canonical = Primary from routing table with conflict_flag=True,
     unless secondary score exceeds primary by at least delta_canon (>= 0.15).
3. PROHIBITED: Text averaging, blending, fusion, or interpolating.
4. Stability invariant: Immune to epsilon perturbations (+/- 0.02) of scores.
"""

from difflib import SequenceMatcher
import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from study_engine.ingestion.conversion_audit import ConversionAuditReport, ConversionAuditor
from study_engine.ingestion.converters.base import ConversionResult

DELTA_CANONICAL_THRESHOLD = 0.15
TAU_CONFLICT_THRESHOLD = 0.12


class ConversionConflict(BaseModel):
    """Immutable record of representation conflict between two converters."""

    model_config = ConfigDict(frozen=True)

    source_sha256: str
    converter_a: str
    converter_b: str
    candidate_a_sha256: str
    candidate_b_sha256: str
    diff_stat: float = Field(..., description="Normalized divergence ratio [0.0, 1.0]")
    reason: str = Field(default="Divergencia estructural significativa entre salidas de conversores")


class ArbitrationDecision(BaseModel):
    """Final arbitration result declaring canonical output and audit conflict metadata."""

    model_config = ConfigDict(frozen=True)

    canonical_result: ConversionResult
    canonical_audit: ConversionAuditReport
    conflict_flag: bool
    conflict: Optional[ConversionConflict] = None
    all_candidates: List[ConversionResult]


class ConversionArbiter:
    """Arbitrates multiple converter outputs and enforces representation conflict rules."""

    def __init__(
        self,
        auditor: Optional[ConversionAuditor] = None,
        delta_canon: float = DELTA_CANONICAL_THRESHOLD,
        tau_conflict: float = TAU_CONFLICT_THRESHOLD,
    ) -> None:
        self.auditor = auditor or ConversionAuditor()
        self.delta_canon = delta_canon
        self.tau_conflict = tau_conflict

    @staticmethod
    def compute_normalized_diff(text_a: str, text_b: str) -> float:
        """Compute structural divergence ratio insensitive to superficial whitespace."""
        norm_a = re.sub(r"[ \t]+", " ", text_a.strip().lower())
        norm_b = re.sub(r"[ \t]+", " ", text_b.strip().lower())

        if not norm_a and not norm_b:
            return 0.0
        if not norm_a or not norm_b:
            return 1.0

        # Fast token-level overlap
        tokens_a = norm_a.split()
        tokens_b = norm_b.split()
        if not tokens_a or not tokens_b:
            return 1.0

        matcher = SequenceMatcher(None, tokens_a, tokens_b)
        similarity = matcher.ratio()
        return max(0.0, min(1.0, 1.0 - similarity))

    def arbitrate(
        self,
        primary_result: ConversionResult,
        secondary_result: Optional[ConversionResult] = None,
        expected_pages: int = 1,
        source_sha256: str = "",
    ) -> ArbitrationDecision:
        """Arbitrate candidate outputs and emit canonical output."""
        audit_prim = self.auditor.audit(primary_result, expected_pages=expected_pages)

        if secondary_result is None:
            return ArbitrationDecision(
                canonical_result=primary_result,
                canonical_audit=audit_prim,
                conflict_flag=False,
                conflict=None,
                all_candidates=[primary_result],
            )

        audit_sec = self.auditor.audit(secondary_result, expected_pages=expected_pages)
        divergence = self.compute_normalized_diff(
            primary_result.markdown_content,
            secondary_result.markdown_content,
        )

        candidates = [primary_result, secondary_result]
        src_hash = source_sha256 or hashlib.sha256(primary_result.markdown_content.encode("utf-8")).hexdigest()

        is_conflict = divergence > self.tau_conflict
        conflict_obj: Optional[ConversionConflict] = None

        if is_conflict:
            conflict_obj = ConversionConflict(
                source_sha256=src_hash,
                converter_a=primary_result.converter_id,
                converter_b=secondary_result.converter_id,
                candidate_a_sha256=primary_result.sha256_output,
                candidate_b_sha256=secondary_result.sha256_output,
                diff_stat=round(divergence, 4),
            )

            # CAL-1 Explicit Rule:
            # In conflict, Canonical = Primary from routing table with conflict_flag=True,
            # UNLESS secondary score exceeds primary by at least delta_canon.
            score_diff = audit_sec.overall_quality_score - audit_prim.overall_quality_score
            if score_diff >= self.delta_canon:
                canonical_res = secondary_result
                canonical_aud = audit_sec
            else:
                canonical_res = primary_result
                canonical_aud = audit_prim
        else:
            # No conflict: pick higher score or primary
            if audit_sec.overall_quality_score > audit_prim.overall_quality_score:
                canonical_res = secondary_result
                canonical_aud = audit_sec
            else:
                canonical_res = primary_result
                canonical_aud = audit_prim

        return ArbitrationDecision(
            canonical_result=canonical_res,
            canonical_audit=canonical_aud,
            conflict_flag=is_conflict,
            conflict=conflict_obj,
            all_candidates=candidates,
        )
