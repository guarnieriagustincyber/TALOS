#!/usr/bin/env python3
"""Hito 6 — Phase 0: Critical Regression Runner (Provenance Context Validation).

Tests whether an assessment submission lacking explicit SessionProvenanceContext
is strictly rejected (FAIL-CLOSED) or improperly admitted via arbitrary node fallback.

Protocol: ATTACK -> OBSERVE -> COMPARE ORACLE -> CLASSIFY -> DOCUMENT
Rule: DO NOT PATCH BEFORE CLOSING DIAGNOSTIC CAMPAIGN.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Dict, Optional

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from study_engine.contracts.assessment import AssessmentResult
from study_engine.contracts.evidence_ingestion import SessionProvenanceContext
from study_engine.contracts.execution import ExecutionObservation
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.curriculum.rubric_contracts import AssessmentRubric
from study_engine.curriculum.task_contracts import PracticalTaskSpecification
from study_engine.session.adapters import (
    CurriculumStateAdapter,
    DeterministicAssessmentAdapter,
    EvidenceIngestionAdapter,
    PracticalExecutionAdapter,
)
from study_engine.session.contracts import (
    PracticeRequest,
    PracticeResult,
    PracticeResultStatus,
)
from study_engine.session.orchestrator import SessionOrchestrator
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.policy_contracts import AssessmentPolicy
from study_engine.roadmap.contracts import CurricularRoadmap


def run_phase_0_regression() -> Dict[str, Any]:
    """Execute Phase 0 Critical Regression and return diagnostic telemetry."""
    oracle_path = REPO_ROOT / "data/experiments/hito6/hito6_oracle.json"
    with open(oracle_path, "r", encoding="utf-8") as f:
        oracle = json.load(f)

    p0_spec = oracle["phase_0_critical_regression"]
    print("=" * 70)
    print("🧪 HITO 6 — FASE 0: REGRESIÓN CRÍTICA (PRE-CAMPAÑA)")
    print("=" * 70)
    print(f"Case ID:        {p0_spec['case_id']}")
    print(f"Attack Class:   {p0_spec['attack_class']}")
    print(f"Description:    {p0_spec['description']}")
    print("-" * 70)

    # 1. Setup Curricular Environment
    curriculum_dir = REPO_ROOT / "data/curriculum"
    registry = CurriculumRegistry(root_dir=curriculum_dir)
    roadmap = registry.load_roadmap("cybersecurity_v1.yaml")
    alignment = registry.load_alignment("cybersecurity_v1_alignment.json")
    task = registry.load_task("task_sec05_file_hasher.json")
    rubric = registry.load_rubric("rubric_sec05_deterministic.json")
    from scripts.experiments.run_golden_path_e2e import build_cybersecurity_policy
    policy = build_cybersecurity_policy()
    ledger = EvidenceLedger()

    exec_adapter = PracticalExecutionAdapter()
    assess_adapter = DeterministicAssessmentAdapter()
    ingest_adapter = EvidenceIngestionAdapter(
        ledger=ledger,
        roadmap=roadmap,
        policy=policy,
        student_id=p0_spec["input"]["student_id"],
        session_id="session-adversarial-p0",
    )
    state_adapter = CurriculumStateAdapter(
        ledger=ledger,
        roadmap=roadmap,
        policy=policy,
        student_id=p0_spec["input"]["student_id"],
    )

    # 2. Produce valid student observation and assessment
    artifact_path = REPO_ROOT / p0_spec["input"]["artifact_path"]
    obs: ExecutionObservation = exec_adapter.execute_task(task, str(artifact_path))
    asmt: AssessmentResult = assess_adapter.evaluate_observation(obs, rubric, task)

    # 3. ATTACK INVOCATION: Test direct ingestion without SessionProvenanceContext
    initial_cardinality = len(ledger._entries)
    ingestion_status = "UNKNOWN"
    admitted_record_id: Optional[str] = None
    attributed_node_id: Optional[str] = None
    caught_exception: Optional[str] = None

    print("\n[ATTACK] Invocando ingest_assessment(asmt, context=None)...")
    try:
        record = ingest_adapter.ingest_assessment(assessment=asmt, context=None)
        ingestion_status = "ADMITTED"
        admitted_record_id = record.record_id
        attributed_node_id = record.node_id
    except Exception as exc:
        ingestion_status = "REJECTED"
        caught_exception = f"{type(exc).__name__}: {exc}"

    final_cardinality = len(ledger._entries)
    ledger_delta = final_cardinality - initial_cardinality

    # 4. OBSERVE
    first_node_in_roadmap = next(iter(roadmap.nodes.keys()))
    arbitrary_fallback_occurred = (
        attributed_node_id == first_node_in_roadmap
        and attributed_node_id != task.curriculum_node_id
    )

    observation = {
        "case_id": p0_spec["case_id"],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input": {
            "task_id": task.task_id,
            "task_target_node": task.curriculum_node_id,
            "provided_context": None,
        },
        "observation": {
            "ingestion_status": ingestion_status,
            "caught_exception": caught_exception,
            "admitted_record_id": admitted_record_id,
            "attributed_node_id": attributed_node_id,
            "first_node_in_roadmap": first_node_in_roadmap,
            "arbitrary_fallback_occurred": arbitrary_fallback_occurred,
            "initial_ledger_cardinality": initial_cardinality,
            "final_ledger_cardinality": final_cardinality,
            "ledger_delta": ledger_delta,
        },
    }

    # 5. COMPARE AGAINST ORACLE
    mismatches = []
    if ingestion_status != "REJECTED":
        mismatches.append(
            f"Expected ingestion_status to be REJECTED, but got '{ingestion_status}'"
        )
    if ledger_delta != p0_spec["expected_ledger_delta"]:
        mismatches.append(
            f"Expected ledger_delta == {p0_spec['expected_ledger_delta']}, but got {ledger_delta}"
        )
    if arbitrary_fallback_occurred:
        mismatches.append(
            f"Arbitrary node fallback occurred: evidence attributed to '{attributed_node_id}' "
            f"(first node in roadmap) instead of target '{task.curriculum_node_id}' or failing closed."
        )

    # 6. CLASSIFY (Strict taxonomy: CONFIRMED_PASS, CONFIRMED_DEFECT, DESIGN_WEAKNESS, TEST_GAP, etc.)
    if not mismatches:
        classification = "CONFIRMED_PASS"
        action = "PROCEED_TO_PHASE_1"
    else:
        classification = "CONFIRMED_DEFECT"
        action = "ABORT_CAMPAIGN"

    results = {
        "campaign_id": oracle["campaign_id"],
        "phase": "phase_0_critical_regression",
        "case_id": p0_spec["case_id"],
        "classification": classification,
        "action": action,
        "oracle_expected": {
            "expected_route": p0_spec["expected_route"],
            "expected_verdict": p0_spec["expected_verdict"],
            "expected_ledger_delta": p0_spec["expected_ledger_delta"],
            "expected_cardinality": p0_spec["expected_cardinality"],
            "expected_side_effects": p0_spec["expected_side_effects"],
        },
        "actual_observed": observation["observation"],
        "mismatches": mismatches,
    }

    print("\n" + "=" * 70)
    print("📋 RESUMEN DIAGNÓSTICO DE LA FASE 0")
    print("=" * 70)
    print(f"Ingestion Status:            {ingestion_status}")
    print(f"Ledger Delta:                +{ledger_delta} entries")
    print(f"Attributed Node ID:          {attributed_node_id}")
    print(f"Task True Node ID:           {task.curriculum_node_id}")
    print(f"Arbitrary Fallback Detected: {arbitrary_fallback_occurred}")
    print(f"Mismatches contra Oráculo:   {len(mismatches)}")
    for m in mismatches:
        print(f"  ❌ {m}")
    print(f"Clasificación Formal:        {classification}")
    print(f"Acción Mandatoria:           {action}")
    print("=" * 70)

    # 7. DOCUMENT
    results_path = REPO_ROOT / "data/experiments/hito6/hito6_results.json"
    telemetry_path = REPO_ROOT / "data/experiments/hito6/hito6_telemetry.json"
    summary_path = REPO_ROOT / "data/experiments/hito6/hito6_summary.json"

    results_path.write_text(json.dumps(results, indent=2) + "\n")
    telemetry_path.write_text(json.dumps(observation, indent=2) + "\n")
    summary_path.write_text(
        json.dumps(
            {
                "campaign_id": oracle["campaign_id"],
                "phase": "phase_0_critical_regression",
                "status": classification,
                "action": action,
                "findings": [
                    {
                        "case_id": p0_spec["case_id"],
                        "classification": classification,
                        "description": p0_spec["description"],
                        "mismatches": mismatches,
                    }
                ],
            },
            indent=2,
        )
        + "\n"
    )

    return results


if __name__ == "__main__":
    res = run_phase_0_regression()
    if res["action"] == "ABORT_CAMPAIGN":
        sys.exit(1)
    sys.exit(0)
