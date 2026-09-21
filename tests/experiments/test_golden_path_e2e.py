"""Automated integration test suite for Hito 5: Golden Path End-to-End.

Validates the full learning loop combining:
- Golden Path A (Conceptual Turn with Epistemic Isolation and S4.4 Forensic Audit)
- Golden Path B (Practical Turn with S6 Sandbox Execution, S9 Assessment, and S5 Ingestion)
- State Engine (Deterministic Projection from Immutable Ledger)
- Differential Oracle Verification against gp_e2e_oracle.json
- Cryptographic Hash Chain and Anti-Replay Defense
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
import pytest

from scripts.experiments.run_golden_path_e2e import (
    E2ECampaignRunner,
    run_golden_path_e2e,
)
from study_engine.state.ledger_contracts import IdempotentReplayError


@pytest.fixture(scope="module")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def oracle(repo_root: Path) -> Dict[str, Any]:
    oracle_path = repo_root / "data" / "experiments" / "hito5" / "gp_e2e_oracle.json"
    assert oracle_path.exists(), f"Oracle must exist at {oracle_path}"
    with open(oracle_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def campaign_results(repo_root: Path, oracle: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the end-to-end campaign runner once for the test module."""
    return run_golden_path_e2e(repo_root=repo_root)


def test_golden_path_e2e_overall_certification(campaign_results: Dict[str, Any]) -> None:
    """Certify that the end-to-end campaign achieves full certification with zero oracle mismatches."""
    assert campaign_results["verdict"] == "CERTIFIED"
    comp = campaign_results["oracle_comparison"]
    assert comp["status"] == "PASS"
    assert comp["mismatch_count"] == 0
    assert comp["mismatches"] == []


def test_golden_path_e2e_phase1_conceptual_turn(
    campaign_results: Dict[str, Any], oracle: Dict[str, Any]
) -> None:
    """Verify Phase 1 (Golden Path A): Epistemic retrieval, grounded generation, and S4.4 audit."""
    p1 = campaign_results["phases"]["phase_1_conceptual"]
    exp_p1 = oracle["phase_1_conceptual"]

    # 1. Session status must be APPROVED
    assert p1["session_status"] == exp_p1["expected_audit"]["session_status"]
    assert p1["abstention_reason"] is None
    assert p1["audit_report_id"] is not None

    # 2. Epistemic isolation: exact candidate count and document origin
    assert p1["candidate_count"] == exp_p1["expected_retrieval"]["candidate_count"]
    assert p1["retrieved_document_ids"] == [exp_p1["expected_retrieval"]["primary_document_id"]]
    exp_auth = exp_p1["expected_retrieval"]["expected_authorized_page_range"]
    auth_range = set(range(exp_auth["start"], exp_auth["end"] + 1))
    retrieved_pages = set(p1.get("retrieved_pages", []))
    assert retrieved_pages.issubset(auth_range), f"{retrieved_pages} not subset of {auth_range}"
    assert retrieved_pages == set(exp_p1["expected_retrieval"]["expected_retrieved_page_set"]["pages"])

    # 3. Grounded generation citations
    for cit in exp_p1["expected_generation"]["citations_manifest_expected"]:
        assert f"[{cit}]" in p1["response_text"]

    # 4. Forensic audit checks
    audit_trace = p1["audit_trace"]
    assert audit_trace["overall_verdict"] == exp_p1["expected_audit"]["overall_verdict"]
    check_statuses = {chk["check_id"]: chk["status"] for chk in audit_trace["deterministic_checks"]}
    assert check_statuses["CHECK_INPUT_IDENTITY"] == "PASS"
    assert check_statuses["CHECK_MANIFEST_INTEGRITY"] == "PASS"
    assert check_statuses["CHECK_FACTUAL_GROUNDING"] == "PASS"
    assert check_statuses["CHECK_P7_MASTERY_MUTATION"] == "PASS"


def test_golden_path_e2e_phase2_practical_turn(
    campaign_results: Dict[str, Any], oracle: Dict[str, Any]
) -> None:
    """Verify Phase 2 (Golden Path B): Execution, deterministic assessment, and evidence emission."""
    p2 = campaign_results["phases"]["phase_2_practical"]
    exp_p2 = oracle["phase_2_practical"]["expected_practice"]

    # 1. Practice submission status
    assert p2["practice_status"] == exp_p2["assessment_result"]["practice_result_status"]
    assert p2["rejection_reason"] is None
    assert p2["evidence_record_id"] is not None

    # 2. Execution observation
    assert p2["exit_code"] == exp_p2["execution_observation"]["exit_code"]
    assert p2["execution_status"] == exp_p2["execution_observation"]["status"]

    # 3. Assessment evaluation
    assert p2["assessment_passed"] == exp_p2["assessment_result"]["passed"]
    assert p2["overall_level"] == exp_p2["assessment_result"]["overall_level"]


def test_golden_path_e2e_phase3_state_projection(
    campaign_results: Dict[str, Any], oracle: Dict[str, Any]
) -> None:
    """Verify Phase 3: Curricular progression derived strictly from ledger evidence."""
    p3 = campaign_results["phases"]["phase_3_state"]
    node_states = p3["node_states"]
    exp_trans = oracle["phase_3_state"]["expected_node_transitions"]

    # Prerequisite topic SEC-02 is proficient
    assert node_states["SEC-02-OS-PROC"] == exp_trans["SEC-02-OS-PROC"]
    # Downstream competency SEC-04 is unlocked and available
    assert node_states["SEC-04-CONCURR"] == exp_trans["SEC-04-CONCURR"]


def test_golden_path_e2e_phase4_ledger_and_anti_replay(
    campaign_results: Dict[str, Any], oracle: Dict[str, Any]
) -> None:
    """Verify Phase 4: Ledger cardinality, cryptographic hash chain, and anti-replay defense."""
    p4 = campaign_results["phases"]["phase_4_ledger"]
    exp_p4 = oracle["phase_4_ledger"]

    # Cardinality: 1 conceptual baseline + 1 practical submission = 2 entries
    assert p4["ledger_cardinality"] == exp_p4["expected_cardinality"]
    assert p4["cardinality_after_replay"] == exp_p4["expected_cardinality"]

    # Hash chain integrity
    assert p4["hash_chain_status"] == exp_p4["expected_hash_chain_status"]

    # Anti-replay defense
    assert p4["anti_replay_idempotent_detected"] is True


def test_golden_path_e2e_runner_lifecycle(repo_root: Path, tmp_path: Path) -> None:
    """Verify isolated runner initialization and execution with custom working directory."""
    runner = E2ECampaignRunner(repo_root=repo_root, working_dir=tmp_path)
    try:
        results = runner.execute_campaign()
        assert results["verdict"] == "CERTIFIED"
        assert results["oracle_comparison"]["status"] == "PASS"
    finally:
        runner.cleanup()
