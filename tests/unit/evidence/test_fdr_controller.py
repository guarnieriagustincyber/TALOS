"""Unit tests for ConformalFDRController, Exchangeability, and CalibrationContract (Phase E2.5)."""

import json
from pathlib import Path
import pytest

from study_engine.evidence.fdr_controller import (
    CalibrationContract,
    ConformalFDRController,
    compute_ks_2sample,
)

DICT_PATH = Path("data/benchmark/bilingual_dict_v1.json")
CLAIMS_PATH = Path("data/benchmark/claims/golden_claims_v1.json")


def test_ks_2sample_identical_and_shifted():
    # Identical distributions should have p-value ~ 1.0
    d1 = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    d2 = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    ks_stat, p_val = compute_ks_2sample(d1, d2)
    assert ks_stat == 0.0
    assert p_val >= 0.90

    # Divergent distributions should have high KS stat and small p-value
    shifted_d2 = [0.91, 0.92, 0.93, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99]
    ks_stat_shift, p_val_shift = compute_ks_2sample(d1, shifted_d2)
    assert ks_stat_shift > 0.70
    assert p_val_shift < 0.05


def test_conformal_calibration_and_contract_h5():
    with open(CLAIMS_PATH, "r", encoding="utf-8") as f:
        all_claims = json.load(f)

    cal_claims = [c for c in all_claims if c["split"] == "calibration"]
    assert len(cal_claims) == 144

    controller = ConformalFDRController(bilingual_dict_path=DICT_PATH, alpha=0.05)
    contract = controller.calibrate(cal_claims)

    assert isinstance(contract, CalibrationContract)
    assert contract.sample_size == 144
    assert contract.alpha == 0.05
    assert contract.bilingual_dict_sha256 != ""
    assert contract.calibration_split_sha256 != ""
    assert 0.40 <= contract.tau_supported <= 0.70
    assert 0.10 <= contract.tau_partial < contract.tau_supported
    assert contract.is_conformal_valid is True

    # H5: Check quantiles and histogram
    assert "p50" in contract.score_quantiles
    assert "p95" in contract.score_quantiles
    assert len(contract.score_histogram) == 10

    # H6: Check exchangeability report
    assert contract.exchangeability_report is not None
    assert contract.exchangeability_report.es_count == 72
    assert contract.exchangeability_report.en_count == 72
    assert contract.exchangeability_report.is_exchangeable is True


def test_test_split_evaluation_h2():
    with open(CLAIMS_PATH, "r", encoding="utf-8") as f:
        all_claims = json.load(f)

    cal_claims = [c for c in all_claims if c["split"] == "calibration"]
    test_claims = [c for c in all_claims if c["split"] == "test"]
    assert len(test_claims) == 96

    controller = ConformalFDRController(bilingual_dict_path=DICT_PATH, alpha=0.05)
    controller.calibrate(cal_claims)

    test_res = controller.evaluate_test_split(test_claims)
    assert test_res["test_sample_size"] == 96
    assert test_res["ucr_critical"] == 0.0
    assert test_res["ucr_critical_pass"] is True
    assert test_res["ucr_non_critical"] < 0.03
    assert test_res["ucr_non_critical_pass"] is True
    assert test_res["false_acceptance_rate"] < 0.05
    assert test_res["far_pass"] is True
    assert test_res["false_rejection_rate"] < 0.05
    assert test_res["frr_pass"] is True
