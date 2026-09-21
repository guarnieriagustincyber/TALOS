#!/usr/bin/env python3
"""Hito 6 — Phase 4: Execution Attacks Campaign Runner.

Executes the 8 adversarial execution attack cases against Subsystems S6.1
(Execution Sandbox) and S9.1 (Deterministic Assessment Engine), verifying the
nuclear invariant:
    execution_success != mastery

Protocol: ATTACK -> OBSERVE -> COMPARE ORACLE -> CLASSIFY -> DOCUMENT
Nuclear Invariant: Clean process exit code (exit 0) NEVER confers mastery
                  unless all rubric postconditions are deterministically met.
Rule: STRICTLY NO PATCHING DURING DIAGNOSTIC CAMPAIGN.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.experiments.run_golden_path_e2e import build_cybersecurity_policy
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.curriculum.registry import CurriculumRegistry
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
from study_engine.state.policy_contracts import (
    ActorType,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)
from study_engine.state.state_contracts import NodeProgressStatus


class Phase4ExecutionCampaignRunner:
    """Automated test runner for Hito 6 Phase 4 Execution Attacks."""

    def __init__(
        self,
        oracle_path: Path,
        repo_root: Path = REPO_ROOT,
    ) -> None:
        self.repo_root = repo_root
        self.oracle_path = oracle_path
        with open(self.oracle_path, "r", encoding="utf-8") as f:
            self.oracle = json.load(f)

        self.phase4_spec = self.oracle["phase_4_execution_attacks"]
        self.phase4_cases = self.phase4_spec["cases"]

        # Setup Curricular Environment
        curriculum_dir = self.repo_root / "data" / "curriculum"
        self.registry = CurriculumRegistry(root_dir=curriculum_dir)
        self.roadmap = self.registry.load_roadmap("cybersecurity_v1.yaml")
        self.alignment = self.registry.load_alignment("cybersecurity_v1_alignment.json")
        self.task = self.registry.load_task("task_sec05_file_hasher.json")
        self.rubric = self.registry.load_rubric("rubric_sec05_deterministic.json")
        self.policy = build_cybersecurity_policy()

    def _setup_student_environment(
        self, student_id: str, session_id: str
    ) -> Tuple[EvidenceLedger, SessionOrchestrator, CurriculumStateAdapter]:
        """Create fresh isolated student ledger, baseline prerequisites, and orchestrator."""
        ledger = EvidenceLedger()

        # Commit baseline prerequisite passing evidence:
        # SEC-01-C-PTR (TOPIC -> CONCEPTUAL_EXPLANATION)
        # SEC-02-OS-PROC (TOPIC -> CONCEPTUAL_EXPLANATION)
        # SEC-03-MEM-MGMT (COMPETENCY -> CODE_EXECUTION)
        prereqs = [
            ("SEC-01-C-PTR", EvidenceType.CONCEPTUAL_EXPLANATION),
            ("SEC-02-OS-PROC", EvidenceType.CONCEPTUAL_EXPLANATION),
            ("SEC-03-MEM-MGMT", EvidenceType.CODE_EXECUTION),
        ]
        now = datetime.now(timezone.utc)
        for nid, etype in prereqs:
            rec = EvidenceRecord(
                record_id=f"ev-baseline-{nid}-{student_id}",
                student_id=student_id,
                node_id=nid,
                evidence_type=etype,
                outcome=EvidenceOutcome.PASS,
                score=1.0,
                timestamp=now - timedelta(minutes=10),
                actor_type=ActorType.TOOL_VERIFIER,
                actor_id="baseline-evaluator",
                authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                assessment_digest=hashlib.sha256(nid.encode("utf-8")).hexdigest(),
            )
            ledger.append_record(rec)

        exec_adapter = PracticalExecutionAdapter(
            default_stdin="STUDY_ENGINE_CANONICAL_INPUT",
            timeout_seconds=2,
        )
        assess_adapter = DeterministicAssessmentAdapter(default_task=self.task)
        ingest_adapter = EvidenceIngestionAdapter(
            ledger=ledger,
            roadmap=self.roadmap,
            policy=self.policy,
            student_id=student_id,
            session_id=session_id,
        )
        state_adapter = CurriculumStateAdapter(
            roadmap=self.roadmap,
            policy=self.policy,
            ledger=ledger,
            student_id=student_id,
        )

        orch = SessionOrchestrator(
            session_id=session_id,
            student_id=student_id,
            roadmap=self.roadmap,
            policy=self.policy,
            ledger=ledger,
            execution_port=exec_adapter,
            assessment_port=assess_adapter,
            ingestion_port=ingest_adapter,
            state_read_port=state_adapter,
            curriculum_registry=self.registry,
            allowed_artifact_roots=(self.repo_root / "scratch" / "fixtures" / "gp_b",),
            session_started_at=now - timedelta(minutes=5),
        )
        orch.start_session()

        return ledger, orch, state_adapter

    def run_campaign(self) -> Dict[str, Any]:
        """Execute all 8 Phase 4 execution attack scenarios in strict severity order."""
        print("=" * 75)
        print("🛡️  HITO 6 — FASE 4: CAMPAÑA DE ATAQUES DE EJECUCIÓN (S6.1 & S9.1)")
        print("=" * 75)
        print(f"Total Casos de Ataque / Control: {len(self.phase4_cases)}")
        print("Nuclear Invariant: execution_success != mastery")
        print("Protocol: ATTACK -> OBSERVE -> COMPARE ORACLE -> CLASSIFY -> DOCUMENT")
        print("-" * 75)

        telemetry_records: List[Dict[str, Any]] = []
        findings: List[Dict[str, Any]] = []
        overall_defects = 0

        # Sort cases by severity order
        sorted_cases = sorted(self.phase4_cases, key=lambda c: int(c["severity_order"]))

        for case_spec in sorted_cases:
            case_id = case_spec["case_id"]
            sev = case_spec["severity_order"]
            attack_cls = case_spec["attack_class"]
            threat_vec = case_spec["threat_vector"]
            desc = case_spec["description"]
            cin = case_spec["input"]
            exp = case_spec["expected"]

            print(f"\n▶️  [{case_id}] Sev {sev}: {attack_cls} ({threat_vec})")
            print(f"     Desc: {desc}")

            # 1. SETUP ISOLATED ENVIRONMENT
            student_id = cin["student_id"]
            session_id = f"session-{case_id.lower()}"
            ledger, orch, state_adapter = self._setup_student_environment(student_id, session_id)
            initial_ledger_cardinality = len(ledger._entries)

            # 2. ATTACK EXECUTION
            artifact_rel = cin["artifact_path"]
            artifact_abs = (self.repo_root / artifact_rel).resolve()
            expected_sha = cin.get("expected_sha256")

            practice_req = PracticeRequest(
                student_id=student_id,
                node_id=cin["node_id"],
                task_id=cin["task_id"],
                rubric_id=cin["rubric_id"],
                artifact_path=str(artifact_abs),
                expected_sha256=expected_sha,
            )

            res: PracticeResult = orch.handle_practical_submission(practice_req)

            # 3. OBSERVE
            final_ledger_cardinality = len(ledger._entries)
            observed_ledger_delta = final_ledger_cardinality - initial_ledger_cardinality

            observed_practice_status = res.status.value
            obs_dict: Dict[str, Any] = res.execution_observation or {}
            observed_execution_status = obs_dict.get("status")
            observed_exit_code = obs_dict.get("exit_code")

            asmt_res = res.assessment_result
            observed_assessment_passed: Optional[bool] = (
                asmt_res.aggregation.passed if asmt_res else None
            )
            observed_overall_level: Optional[str] = (
                asmt_res.aggregation.overall_level.name
                if (asmt_res and asmt_res.aggregation.overall_level)
                else None
            )

            # Query projected node state
            student_state = state_adapter.get_student_state(student_id)
            sec05_state = student_state.get_node_state("SEC-05-BIN-SEC")
            observed_node_status = (
                sec05_state.status.value if sec05_state else None
            )
            observed_mastery_granted = (
                observed_node_status == NodeProgressStatus.ASSESSED_PROFICIENT.value
            )

            observed_evidence_outcome: Optional[str] = None
            observed_score: Optional[float] = None
            if res.assessment_summary:
                observed_evidence_outcome = res.assessment_summary.get("outcome")
                observed_score = res.assessment_summary.get("score")

            observed_rejection_reason = res.rejection_reason

            # 4. COMPARE AGAINST ORACLE
            case_mismatches: List[str] = []

            # Practice status
            if observed_practice_status != exp["practice_status"]:
                case_mismatches.append(
                    f"Practice status mismatch: observed '{observed_practice_status}' != expected '{exp['practice_status']}'"
                )

            # Execution status (if expected)
            if exp["execution_status"] is not None:
                if observed_execution_status != exp["execution_status"]:
                    case_mismatches.append(
                        f"Execution status mismatch: observed '{observed_execution_status}' != expected '{exp['execution_status']}'"
                    )

            # Exit code (if expected)
            if exp["exit_code"] is not None:
                if observed_exit_code != exp["exit_code"]:
                    case_mismatches.append(
                        f"Exit code mismatch: observed {observed_exit_code} != expected {exp['exit_code']}"
                    )

            # Assessment passed (if expected)
            if exp["assessment_passed"] is not None:
                if observed_assessment_passed != exp["assessment_passed"]:
                    case_mismatches.append(
                        f"Assessment passed mismatch: observed {observed_assessment_passed} != expected {exp['assessment_passed']}"
                    )

            # Overall level (if expected)
            if exp["overall_level"] is not None:
                if observed_overall_level != exp["overall_level"]:
                    case_mismatches.append(
                        f"Overall level mismatch: observed '{observed_overall_level}' != expected '{exp['overall_level']}'"
                    )

            # Evidence outcome (if expected)
            if exp["evidence_outcome"] is not None:
                if observed_evidence_outcome != exp["evidence_outcome"]:
                    case_mismatches.append(
                        f"Evidence outcome mismatch: observed '{observed_evidence_outcome}' != expected '{exp['evidence_outcome']}'"
                    )

            # Score (if expected)
            if exp["score"] is not None:
                if observed_score != exp["score"]:
                    case_mismatches.append(
                        f"Score mismatch: observed {observed_score} != expected {exp['score']}"
                    )

            # Ledger delta
            if observed_ledger_delta != exp["ledger_delta"]:
                case_mismatches.append(
                    f"Ledger delta mismatch: observed {observed_ledger_delta} != expected {exp['ledger_delta']}"
                )

            # Node status after
            if exp["node_status_after"] is not None:
                if observed_node_status != exp["node_status_after"]:
                    case_mismatches.append(
                        f"Node status mismatch: observed '{observed_node_status}' != expected '{exp['node_status_after']}'"
                    )

            # Mastery granted
            if observed_mastery_granted != exp["mastery_granted"]:
                case_mismatches.append(
                    f"Mastery granted mismatch: observed {observed_mastery_granted} != expected {exp['mastery_granted']}"
                )

            # Rejection reason substring check (if expected)
            if exp["rejection_reason"] is not None:
                if not observed_rejection_reason or exp["rejection_reason"] not in observed_rejection_reason:
                    case_mismatches.append(
                        f"Rejection reason mismatch: observed '{observed_rejection_reason}' does not contain '{exp['rejection_reason']}'"
                    )

            # Nuclear Invariant Validation:
            # If exit_code == 0, mastery MUST be False for all attack scenarios!
            nuclear_invariant_passed = True
            if observed_exit_code == 0 and attack_cls != "baseline_clean_pass":
                if observed_mastery_granted:
                    case_mismatches.append(
                        "NUCLEAR INVARIANT VIOLATION: exit_code == 0 conferred mastery despite attack!"
                    )
                    nuclear_invariant_passed = False

            # 5. CLASSIFY
            classification = "CONFIRMED_PASS" if not case_mismatches else "CONFIRMED_DEFECT"
            if classification == "CONFIRMED_DEFECT":
                overall_defects += 1

            print(f"     Practice Status:  {observed_practice_status} (Expected: {exp['practice_status']})")
            print(f"     Execution Status: {observed_execution_status} (Expected: {exp['execution_status']})")
            print(f"     Exit Code:        {observed_exit_code} (Expected: {exp['exit_code']})")
            print(f"     Assessment Pass:  {observed_assessment_passed} (Expected: {exp['assessment_passed']})")
            print(f"     Performance Lvl:  {observed_overall_level} (Expected: {exp['overall_level']})")
            print(f"     Evidence Outcome: {observed_evidence_outcome} (Expected: {exp['evidence_outcome']})")
            print(f"     Ledger Delta:     +{observed_ledger_delta} (Expected: +{exp['ledger_delta']})")
            print(f"     Node Status:      {observed_node_status} (Expected: {exp['node_status_after']})")
            print(f"     Mastery Granted:  {observed_mastery_granted} (Expected: {exp['mastery_granted']})")
            print(f"     Invariant Holds:  {nuclear_invariant_passed}")
            print(f"     Classification:   ✅ {classification}" if classification == "CONFIRMED_PASS" else f"     Classification:   ❌ {classification}")

            if case_mismatches:
                for mm in case_mismatches:
                    print(f"       ⚠️  Mismatch: {mm}")

            record = {
                "case_id": case_id,
                "severity_order": sev,
                "attack_class": attack_cls,
                "threat_vector": threat_vec,
                "classification": classification,
                "observed": {
                    "practice_status": observed_practice_status,
                    "execution_status": observed_execution_status,
                    "exit_code": observed_exit_code,
                    "assessment_passed": observed_assessment_passed,
                    "overall_level": observed_overall_level,
                    "evidence_outcome": observed_evidence_outcome,
                    "score": observed_score,
                    "ledger_delta": observed_ledger_delta,
                    "node_status": observed_node_status,
                    "mastery_granted": observed_mastery_granted,
                    "rejection_reason": observed_rejection_reason,
                },
                "expected": exp,
                "nuclear_invariant_holds": nuclear_invariant_passed,
                "mismatches": case_mismatches,
            }
            telemetry_records.append(record)
            findings.append({
                "case_id": case_id,
                "severity_order": sev,
                "attack_class": attack_cls,
                "threat_vector": threat_vec,
                "classification": classification,
                "description": desc,
                "nuclear_invariant_holds": nuclear_invariant_passed,
                "mismatches": case_mismatches,
            })

        passed_cases = sum(1 for f in findings if f["classification"] == "CONFIRMED_PASS")
        final_verdict = "CERTIFIED_PASS" if overall_defects == 0 else "ABORT_ON_DEFECT"

        print("\n" + "=" * 75)
        print("📊 RESUMEN FINAL DE LA CAMPAÑA FASE 4 (EXECUTION ATTACKS)")
        print("=" * 75)
        print(f"Total Casos Evaluados:        {len(self.phase4_cases)}")
        print(f"CONFIRMED_PASS:               {passed_cases}")
        print(f"CONFIRMED_DEFECT:             {overall_defects}")
        print(f"Invariante Nuclear Certificada: {overall_defects == 0}")
        print(f"Veredicto Formal de Fase 4:   {final_verdict}")
        print("=" * 75 + "\n")

        summary_data = {
            "campaign_id": "HITO6-SURVIVAL-ADVERSARIAL",
            "phase": "phase_4_execution_attacks",
            "executed_at_utc": datetime.now(timezone.utc).isoformat(),
            "total_cases": len(self.phase4_cases),
            "passed_cases": passed_cases,
            "defects_found": overall_defects,
            "nuclear_invariant_certified": overall_defects == 0,
            "findings": findings,
        }

        # Update telemetry
        telemetry_path = self.repo_root / "data" / "experiments" / "hito6" / "hito6_telemetry.json"
        existing_telemetry: List[Dict[str, Any]] = []
        if telemetry_path.exists():
            try:
                with open(telemetry_path, "r", encoding="utf-8") as f:
                    existing_telemetry = json.load(f)
            except Exception:
                existing_telemetry = []

        filtered_telemetry = [t for t in existing_telemetry if not t.get("case_id", "").startswith("P4-EXEC-")]
        filtered_telemetry.extend(telemetry_records)

        with open(telemetry_path, "w", encoding="utf-8") as f:
            json.dump(filtered_telemetry, f, indent=2)

        # Update hito6_results.json
        results_path = self.repo_root / "data" / "experiments" / "hito6" / "hito6_results.json"
        existing_results: Dict[str, Any] = {}
        if results_path.exists():
            try:
                with open(results_path, "r", encoding="utf-8") as f:
                    existing_results = json.load(f)
            except Exception:
                existing_results = {}

        existing_results["phase_4_execution_attacks"] = {
            "verdict": final_verdict,
            "total_cases": len(self.phase4_cases),
            "passed_cases": passed_cases,
            "defects": overall_defects,
            "nuclear_invariant_certified": overall_defects == 0,
            "cases": telemetry_records,
        }
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(existing_results, f, indent=2)

        # Update hito6_summary.json
        summary_path = self.repo_root / "data" / "experiments" / "hito6" / "hito6_summary.json"
        existing_summary: Dict[str, Any] = {}
        if summary_path.exists():
            try:
                with open(summary_path, "r", encoding="utf-8") as f:
                    existing_summary = json.load(f)
            except Exception:
                existing_summary = {}

        existing_summary["phase_4_execution_attacks"] = summary_data
        existing_summary["last_updated_utc"] = datetime.now(timezone.utc).isoformat()
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(existing_summary, f, indent=2)

        return summary_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Hito 6 Phase 4 Execution Attacks")
    parser.add_argument(
        "--oracle-path",
        type=Path,
        default=REPO_ROOT / "data" / "experiments" / "hito6" / "hito6_oracle.json",
        help="Path to hito6_oracle.json",
    )
    args = parser.parse_args()

    runner = Phase4ExecutionCampaignRunner(oracle_path=args.oracle_path)
    summary = runner.run_campaign()

    if summary["defects_found"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
