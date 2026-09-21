"""Adversarial Red Team Suite for Phase E4: Federation & Ontological Namespaces.

Tests 5 Critical Attack Vectors:
1. Cross-notebook evidence leakage attempt without an authorized bridge.
2. Stale bridge replay attack after TTL expiration (fail-closed check).
3. Untrusted threat feed pollution: [TF#] trying to inject evidence for a curricular [E#] claim.
4. Single-feed false positive bypass attempt against CrossCheckEngine.
5. Conversational LLM prompt injection attempting to update student BKT mastery.
"""

from datetime import datetime, timezone, timedelta
import hashlib
import pytest

from study_engine.federation.notebook_registry import NotebookRegistry
from study_engine.federation.bridge_registry import BridgeRegistry
from study_engine.federation.curriculum_gate import CurriculumGate, ScopeConstraint
from study_engine.federation.federated_query_planner import FederatedQueryPlanner
from study_engine.federation.namespace import (
    NamespaceItem,
    NamespacePrefix,
    NamespaceTrust,
    NamespaceValidator,
)
from study_engine.adapters.threatintel.base import IOCIndicator, IOCType, ThreatIntelResult
from study_engine.adapters.threatintel.cross_check import CrossCheckEngine
from study_engine.student.lab_observations import LabGraderBridge


def test_red_team_vector_1_cross_notebook_leakage_prevented() -> None:
    """Vector 1: Attempt to query unauthorized topic across notebooks without bridge.

    Must strictly confine search to active notebook or fail-closed.
    """
    nb_reg = NotebookRegistry()
    br_reg = BridgeRegistry("config/bridges.allowlist.json")
    planner = FederatedQueryPlanner(notebook_registry=nb_reg, bridge_registry=br_reg)

    # Active notebook is fadena-prog. Topic 'concurrencia' is only allowed to fadena-so via
    # B-SO-SEC-CONCURR (fadena-so <-> NB-CYBERSECURITY-V1), NOT from fadena-prog!
    plan = planner.plan_query(
        active_notebook_id="fadena-prog",
        query_text="explotacion de race conditions en concurrencia",
        topics=["concurrencia"],
    )

    # Cross-curricular target must NOT include unauthorized notebooks
    target_notebooks = {sq.target_notebook_id for sq in plan.subqueries}
    assert "NB-CYBERSECURITY-V1" not in target_notebooks


def test_red_team_vector_2_stale_bridge_replay_attack() -> None:
    """Vector 2: Replay query across a bridge that has expired its 90-day TTL.

    Must fail-closed with GUARDRAIL_REJECTED and BRIDGE_EXPIRED.
    """
    nb_reg = NotebookRegistry()
    br_reg = BridgeRegistry("config/bridges.allowlist.json")
    planner = FederatedQueryPlanner(notebook_registry=nb_reg, bridge_registry=br_reg)

    # Future date exceeding 90 days
    future_time = datetime(2027, 3, 1, tzinfo=timezone.utc)
    plan = planner.plan_query(
        active_notebook_id="fadena-prog",
        query_text="analisis de punteros en memoria",
        topics=["buffer_overflow"],
        now=future_time,
    )

    # Check that bridge authorization failed or plan rejected
    assert plan.status in ("GUARDRAIL_REJECTED", "PLAN_UNSUPPORTED")
    assert plan.guardrail_code == "G2" or "expired" in (plan.rejection_reason or "").lower()


def test_red_team_vector_3_threat_feed_pollution_of_curricular_claim() -> None:
    """Vector 3: Attacker provides threat intelligence [TF#] IOC pretending to be canonical curricular [E#] proof.

    Must be rejected with REJECTED_UNSUPPORTED_TF_CURRICULAR (Amendment E4-3).
    """
    validator = NamespaceValidator()

    result = validator.validate_claim_evidence_namespace(
        claim_type="curricular",
        claim_namespace=NamespacePrefix.CURRICULAR,
        evidence_namespace=NamespacePrefix.THREAT_INTEL,
        evidence_trust=NamespaceTrust.VERIFIED_HUMAN,  # Even if human verified!
    )

    assert result.valid is False
    assert result.status_code == "REJECTED_UNSUPPORTED_TF_CURRICULAR"


def test_red_team_vector_4_single_feed_false_positive_bypass() -> None:
    """Vector 4: Attacker submits single feed poisoned malicious report.

    CrossCheckEngine must strictly reject single feed as UNSUPPORTED_SINGLE_FEED.
    """
    engine = CrossCheckEngine()
    ioc = "192.0.2.133"
    poisoned_single_result = ThreatIntelResult(
        feed_name="malicious_honeypot_feed",
        ioc_value=ioc,
        verdict="malicious",
        confidence_score=0.99,
        fetched_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
    )

    verdict = engine.evaluate_results(ioc, [poisoned_single_result])
    assert verdict.corroborated is False
    assert verdict.status_code == "UNSUPPORTED_SINGLE_FEED"


def test_red_team_vector_5_conversational_llm_grading_bypass() -> None:
    """Vector 5: Adversarial LLM attempt to inject simulated student answer into BKT.

    LabGraderBridge must raise ValueError and reject the update.
    """
    grader = LabGraderBridge(config_path="config/lab_kc_map.json")

    with pytest.raises(ValueError, match="Zero LLM dialogue updates are permitted"):
        grader.grade_and_record_submission(
            lab_id="local-c-lab",
            challenge_id="buffer-overflow-return-address",
            submitted_flag="ANY",
            source_context="CONVERSATION",
        )

    with pytest.raises(ValueError, match="Zero LLM dialogue updates are permitted"):
        grader.grade_and_record_submission(
            lab_id="local-c-lab",
            challenge_id="buffer-overflow-return-address",
            submitted_flag="ANY",
            source_context="UNVERIFIED_DIALOGUE",
        )
