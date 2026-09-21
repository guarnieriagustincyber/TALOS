"""False Discovery Rate (FDR) Controller and Conformal Risk Calibration (Phase E2).

Implements:
1. Split-conformal calibration on the 144 calibration split claims (frozen).
2. Amendment H5: CalibrationContract with full score quantiles, dataset hashes, and thresholds.
3. Amendment H6: Stratified exchangeability checks (ES vs EN, and across categories) with pure-Python KS-test.
4. Gate thresholds: FAR < 5%, FRR < 5%, UCR_críticos = 0.0%, UCR_no_críticos < 3.0%.
"""

from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from study_engine.evidence.claim_extractor import ClaimCriticality, ClaimType, ExtractedClaim
from study_engine.evidence.token_grounding import (
    ClaimGroundingResult,
    GroundingStatus,
    TokenGroundingEngine,
)


def compute_ks_2sample(data1: List[float], data2: List[float]) -> Tuple[float, float]:
    """Pure-Python two-sample Kolmogorov-Smirnov test.
    
    Returns:
        Tuple of (ks_statistic, p_value)
    """
    n1 = len(data1)
    n2 = len(data2)
    if n1 == 0 or n2 == 0:
        return 0.0, 1.0

    s1 = sorted(data1)
    s2 = sorted(data2)

    # Union of all distinct evaluation points
    all_vals = sorted(list(set(s1 + s2)))
    max_d = 0.0
    i1 = 0
    i2 = 0

    for val in all_vals:
        while i1 < n1 and s1[i1] <= val:
            i1 += 1
        while i2 < n2 and s2[i2] <= val:
            i2 += 1
        cdf1 = i1 / n1
        cdf2 = i2 / n2
        diff = abs(cdf1 - cdf2)
        if diff > max_d:
            max_d = diff

    # Asymptotic p-value approximation via Kolmogorov distribution
    en = math.sqrt((n1 * n2) / (n1 + n2))
    z = (en + 0.12 + 0.11 / en) * max_d

    if z <= 0.0:
        p_val = 1.0
    else:
        # Sum first 20 terms of Kolmogorov series
        term_sum = 0.0
        for k in range(1, 25):
            sign = 1.0 if k % 2 == 1 else -1.0
            term = sign * math.exp(-2.0 * (k * z) ** 2)
            term_sum += term
            if abs(term) < 1e-7:
                break
        p_val = min(1.0, max(0.0, 2.0 * term_sum))

    return round(max_d, 4), round(p_val, 4)


class StratifiedExchangeabilityReport(BaseModel):
    """Diagnostic report validating the conformal exchangeability assumption (H6)."""
    ks_statistic: float
    ks_pvalue: float
    is_exchangeable: bool  # True if p >= 0.05 (no significant distributional shift)
    es_count: int
    en_count: int
    es_mean_score: float
    en_mean_score: float
    category_deviations: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    diagnostic_notes: str = ""


class CalibrationContract(BaseModel):
    """Immutable calibration contract required by Amendment H5."""
    calibration_version: str = "2.0.0"
    alpha: float = 0.05
    calibration_split_sha256: str
    bilingual_dict_sha256: str
    sample_size: int
    tau_supported: float
    tau_partial: float
    empirical_far: float  # False Acceptance Rate
    empirical_frr: float  # False Rejection Rate
    score_quantiles: Dict[str, float]
    score_histogram: Dict[str, int]
    exchangeability_report: StratifiedExchangeabilityReport
    is_conformal_valid: bool = True
    notes: str = ""


class ConformalFDRController:
    """Split-conformal risk controller for post-generation evidence verification."""

    def __init__(
        self,
        bilingual_dict_path: Path,
        alpha: float = 0.05,
    ) -> None:
        self.bilingual_dict_path = bilingual_dict_path
        self.alpha = alpha
        self.grounding_engine = TokenGroundingEngine(bilingual_dict_path=bilingual_dict_path)
        self.contract: Optional[CalibrationContract] = None

    def evaluate_claim_score(self, claim_data: Dict[str, Any]) -> Tuple[float, GroundingStatus]:
        """Compute raw grounding score and initial status for calibration/test claim."""
        claim_type = ClaimType(claim_data["type"])
        crit = ClaimCriticality(claim_data.get("crit", "CRITICAL"))
        formal_data = claim_data.get("formal")
        is_pedagogical = claim_data.get("pedagogical_analogy", False)

        extracted = ExtractedClaim(
            claim_id=claim_data.get("claim_id", "CLM-000"),
            text=claim_data["text"],
            claim_type=claim_type,
            criticality=crit,
            formal_parameters=formal_data,
            is_pedagogical_analogy=is_pedagogical,
            source_language=claim_data.get("lang", "es"),
        )

        evidence = []
        if "ev" in claim_data and claim_data["ev"]:
            evidence.append({"id": "ev-0", "content": claim_data["ev"]})
        elif "evidence_text" in claim_data and claim_data["evidence_text"]:
            evidence.append({"id": "ev-0", "content": claim_data["evidence_text"]})

        res = self.grounding_engine.ground_claim(extracted, evidence)
        return res.grounding_score, res.status

    def calibrate(self, calibration_claims: List[Dict[str, Any]]) -> CalibrationContract:
        """Execute split-conformal calibration on the frozen 144 calibration split claims."""
        cal_bytes = json.dumps(calibration_claims, sort_keys=True, ensure_ascii=False).encode("utf-8")
        cal_sha256 = hashlib.sha256(cal_bytes).hexdigest()

        scores: List[float] = []
        supported_scores: List[float] = []
        unsupported_scores: List[float] = []
        es_scores: List[float] = []
        en_scores: List[float] = []
        cat_scores: Dict[str, List[float]] = defaultdict(list)

        for claim in calibration_claims:
            score, status = self.evaluate_claim_score(claim)
            scores.append(score)
            cat = claim.get("category", "unknown")
            cat_scores[cat].append(score)

            if claim.get("lang") == "es":
                es_scores.append(score)
            else:
                en_scores.append(score)

            gt = claim.get("gt", "SUPPORTED")
            if gt in ("SUPPORTED", "EXEMPT"):
                supported_scores.append(score)
            elif gt in ("UNSUPPORTED", "CONTRADICTION"):
                unsupported_scores.append(score)

        # 1. Conformal Quantile Computation for tau_supported
        # To bound False Acceptance Rate at alpha (0.05), find the (1 - alpha)-quantile of unsupported scores
        sorted_unsupp = sorted(unsupported_scores)
        n_unsupp = len(sorted_unsupp)
        if n_unsupp > 0:
            q_unsupp_idx = min(n_unsupp - 1, int(math.ceil((1.0 - self.alpha) * n_unsupp)))
            tau_sup = round(max(0.40, sorted_unsupp[q_unsupp_idx] + 0.05), 2)
        else:
            tau_sup = 0.40

        # 2. Conformal Quantile Computation for tau_partial
        # To bound False Rejection Rate at alpha (0.05), ensure at most floor(alpha * n_supp) claims are below tau_part
        sorted_supp = sorted(supported_scores)
        n_supp = len(sorted_supp)
        if n_supp > 0:
            max_rej = int(math.floor(self.alpha * n_supp))
            if max_rej > 0:
                tau_part = round(sorted_supp[max_rej - 1] + 0.01, 2)
            else:
                tau_part = round(sorted_supp[0], 2)
            tau_part = round(min(tau_sup - 0.10, max(0.10, tau_part)), 2)
        else:
            tau_part = 0.15

        # Update grounding engine with calibrated thresholds
        self.grounding_engine.tau_supported = tau_sup
        self.grounding_engine.tau_partial = tau_part

        # 3. Empirical FAR & FRR on calibration split
        false_acceptances = 0
        false_rejections = 0
        total_unsupported = 0
        total_supported = 0

        for claim in calibration_claims:
            score, _ = self.evaluate_claim_score(claim)
            gt = claim.get("gt")
            if gt in ("UNSUPPORTED", "CONTRADICTION"):
                total_unsupported += 1
                if score >= tau_sup:
                    false_acceptances += 1
            elif gt == "SUPPORTED":
                total_supported += 1
                if score < tau_part:
                    false_rejections += 1

        far = round(false_acceptances / max(1, total_unsupported), 4)
        frr = round(false_rejections / max(1, total_supported), 4)

        # 4. Compute Quantiles and Histogram
        s_sorted = sorted(scores)
        n_total = len(s_sorted)
        quantiles = {
            "p10": round(s_sorted[int(0.10 * (n_total - 1))], 4),
            "p25": round(s_sorted[int(0.25 * (n_total - 1))], 4),
            "p50": round(s_sorted[int(0.50 * (n_total - 1))], 4),
            "p75": round(s_sorted[int(0.75 * (n_total - 1))], 4),
            "p90": round(s_sorted[int(0.90 * (n_total - 1))], 4),
            "p95": round(s_sorted[int(0.95 * (n_total - 1))], 4),
        }

        # Histogram with 10 bins [0.0-0.1, ..., 0.9-1.0]
        histogram: Dict[str, int] = {}
        for b in range(10):
            low = b / 10.0
            high = (b + 1) / 10.0
            bin_name = f"{low:.1f}-{high:.1f}"
            if b == 9:
                count = sum(1 for s in scores if low <= s <= 1.0)
            else:
                count = sum(1 for s in scores if low <= s < high)
            histogram[bin_name] = count

        # 5. Amendment H6: Stratified Exchangeability Check (ES vs EN)
        ks_stat, ks_pval = compute_ks_2sample(es_scores, en_scores)
        is_exchangeable = ks_pval >= 0.05

        cat_devs: Dict[str, Dict[str, float]] = {}
        for cat, sc_list in cat_scores.items():
            mean_sc = sum(sc_list) / len(sc_list)
            variance = sum((x - mean_sc) ** 2 for x in sc_list) / len(sc_list)
            cat_devs[cat] = {
                "count": len(sc_list),
                "mean": round(mean_sc, 4),
                "std": round(math.sqrt(variance), 4),
            }

        ex_report = StratifiedExchangeabilityReport(
            ks_statistic=ks_stat,
            ks_pvalue=ks_pval,
            is_exchangeable=is_exchangeable,
            es_count=len(es_scores),
            en_count=len(en_scores),
            es_mean_score=round(sum(es_scores) / max(1, len(es_scores)), 4),
            en_mean_score=round(sum(en_scores) / max(1, len(en_scores)), 4),
            category_deviations=cat_devs,
            diagnostic_notes="Exchangeability holds between ES and EN partitions (KS test p >= 0.05)"
            if is_exchangeable
            else f"Marginal distribution shift detected across languages (KS p={ks_pval:.4f} < 0.05)",
        )

        contract = CalibrationContract(
            calibration_version="2.0.0",
            alpha=self.alpha,
            calibration_split_sha256=cal_sha256,
            bilingual_dict_sha256=self.grounding_engine.bilingual_dict_hash,
            sample_size=len(calibration_claims),
            tau_supported=tau_sup,
            tau_partial=tau_part,
            empirical_far=far,
            empirical_frr=frr,
            score_quantiles=quantiles,
            score_histogram=histogram,
            exchangeability_report=ex_report,
            is_conformal_valid=far < 0.05 and frr < 0.05,
            notes="Calibrated deterministically on frozen 144 calibration split claims.",
        )

        self.contract = contract
        return contract

    def evaluate_test_split(
        self,
        test_claims: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Evaluate test split claims strictly with frozen calibrated thresholds."""
        if not self.contract:
            raise RuntimeError("Cannot evaluate test split without prior calibration contract.")

        total_critical = 0
        total_non_critical = 0
        unsupported_critical = 0
        unsupported_non_critical = 0

        total_positives = 0
        total_negatives = 0
        false_acceptances = 0
        false_rejections = 0

        per_claim_results: List[Dict[str, Any]] = []

        for claim in test_claims:
            score, status = self.evaluate_claim_score(claim)
            gt = claim.get("gt")
            crit = claim.get("crit", "CRITICAL")

            # Update GroundingStatus according to calibrated contract thresholds
            if status not in (GroundingStatus.EXEMPT, GroundingStatus.CONTRADICTION):
                if score >= self.contract.tau_supported - 1e-6:
                    assigned_status = GroundingStatus.SUPPORTED
                elif score >= self.contract.tau_partial - 1e-6:
                    assigned_status = GroundingStatus.PARTIALLY_SUPPORTED
                else:
                    assigned_status = GroundingStatus.UNSUPPORTED
            else:
                assigned_status = status

            # Check Criticality Gating (UCR: Unsupported Claim Rate)
            # UCR measures false acceptance of unsupported or contradictory claims
            is_approved = assigned_status == GroundingStatus.SUPPORTED
            is_hallucination = gt in ("UNSUPPORTED", "CONTRADICTION")

            if crit == "CRITICAL":
                total_critical += 1
                if is_approved and is_hallucination:
                    unsupported_critical += 1
            else:
                total_non_critical += 1
                if is_approved and is_hallucination:
                    unsupported_non_critical += 1

            # FAR / FRR metrics
            if gt in ("UNSUPPORTED", "CONTRADICTION"):
                total_negatives += 1
                if assigned_status == GroundingStatus.SUPPORTED:
                    false_acceptances += 1
            elif gt == "SUPPORTED":
                total_positives += 1
                if assigned_status in (GroundingStatus.UNSUPPORTED, GroundingStatus.CONTRADICTION):
                    false_rejections += 1

            per_claim_results.append({
                "claim_id": claim.get("claim_id"),
                "category": claim.get("category"),
                "text": claim.get("text"),
                "ground_truth": gt,
                "assigned_status": assigned_status.value,
                "score": score,
                "criticality": crit,
            })

        ucr_critical = round(unsupported_critical / max(1, total_critical), 4)
        ucr_non_critical = round(unsupported_non_critical / max(1, total_non_critical), 4)
        test_far = round(false_acceptances / max(1, total_negatives), 4)
        test_frr = round(false_rejections / max(1, total_positives), 4)

        return {
            "test_sample_size": len(test_claims),
            "calibrated_tau_supported": self.contract.tau_supported,
            "calibrated_tau_partial": self.contract.tau_partial,
            "ucr_critical": ucr_critical,
            "ucr_non_critical": ucr_non_critical,
            "false_acceptance_rate": test_far,
            "false_rejection_rate": test_frr,
            "ucr_critical_pass": ucr_critical == 0.0,
            "ucr_non_critical_pass": ucr_non_critical < 0.03,
            "far_pass": test_far < 0.05,
            "frr_pass": test_frr < 0.05,
            "per_claim_results": per_claim_results,
        }
