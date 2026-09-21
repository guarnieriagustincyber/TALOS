#!/usr/bin/env python3
"""Exchangeability Kolmogorov-Smirnov Test between Calibration and Test Splits (F7)."""

import json
from pathlib import Path
from typing import List, Tuple

from study_engine.evidence.fdr_controller import ConformalFDRController, compute_ks_2sample


def load_and_score_splits() -> Tuple[List[float], List[float]]:
    claims_path = Path("data/benchmark/claims/golden_claims_v1.json")
    dict_path = Path("data/benchmark/bilingual_dict_v1.json")
    with open(claims_path, "r", encoding="utf-8") as f:
        claims = json.load(f)

    controller = ConformalFDRController(bilingual_dict_path=dict_path)

    cal_scores: List[float] = []
    test_scores: List[float] = []

    for c in claims:
        score, _ = controller.evaluate_claim_score(c)
        split = c.get("split", "calibration")
        if split == "calibration":
            cal_scores.append(score)
        else:
            test_scores.append(score)

    return cal_scores, test_scores


def main() -> None:
    cal_scores, test_scores = load_and_score_splits()

    try:
        from scipy.stats import ks_2samp
        res = ks_2samp(cal_scores, test_scores)
        statistic = float(res.statistic)
        p_value = float(res.pvalue)
    except ImportError:
        statistic, p_value = compute_ks_2sample(cal_scores, test_scores)

    print("==========================================================")
    print("EXCHANGEABILITY TEST: CALIBRATION VS TEST SPLITS")
    print("==========================================================")
    print(f"Calibration count: {len(cal_scores)}")
    print(f"Test count:        {len(test_scores)}")
    print(f"KS statistic: {statistic:.4f}")
    print(f"p-value:      {p_value:.4f}")

    if p_value >= 0.05:
        print("✅ Exchangeability verificada (p >= 0.05)")
    else:
        print("❌ Exchangeability violada - calibrar por estrato")


if __name__ == "__main__":
    main()
