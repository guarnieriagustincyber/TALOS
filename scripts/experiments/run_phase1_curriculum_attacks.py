#!/usr/bin/env python3
"""Hito 6 — Phase 1: Curriculum Attacks Campaign Runner.

Executes the 12 curriculum adversarial attack cases against SessionOrchestrator
and RetrievalService in strict severity order.

Protocol: ATTACK -> OBSERVE -> COMPARE ORACLE -> CLASSIFY -> DOCUMENT
Rule: STRICTLY NO PATCHING DURING DIAGNOSTIC CAMPAIGN.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.experiments.run_golden_path_e2e import E2ECampaignRunner
from study_engine.contracts.evidence_engine import CurricularIsolationError
from study_engine.curriculum.registry import CurriculumNotFoundError
from study_engine.evidence.engine import EvidenceEngine
from study_engine.roadmap.contracts import NodeType, RoadmapNode
from study_engine.session.contracts import (
    SessionRequest,
    SessionResult,
    SessionResultStatus,
)
from study_engine.session.orchestrator import SessionOrchestrator


class Phase1CurriculumRunner:
    """Executes Phase 1 Curriculum Attacks and compares against differential oracle."""

    def __init__(
        self,
        repo_root: Path,
        oracle_path: Optional[Path] = None,
    ) -> None:
        self.repo_root = repo_root
        self.oracle_path = oracle_path or (
            repo_root / "data" / "experiments" / "hito6" / "hito6_oracle.json"
        )
        if not self.oracle_path.exists():
            raise FileNotFoundError(f"Oracle file not found at {self.oracle_path}")

        with open(self.oracle_path, "r", encoding="utf-8") as f:
            self.oracle = json.load(f)

        self.phase1_cases: List[Dict[str, Any]] = self.oracle[
            "phase_1_curriculum_attacks"
        ]["cases"]

    def run_all_cases(self) -> Dict[str, Any]:
        """Execute all 12 cases in severity order and collect telemetry."""
        print("=" * 75)
        print("🧪 HITO 6 — FASE 1: CAMPAÑA DE ATAQUES CURRICULARES (12 CASOS)")
        print("=" * 75)
        print(f"Protocolo:  ATTACK -> OBSERVE -> COMPARE ORACLE -> CLASSIFY -> DOCUMENT")
        print(f"Oráculo:    {self.oracle_path}")
        print(f"Casos:      {len(self.phase1_cases)} casos en orden de severidad")
        print("-" * 75)

        # Initialize base pipeline once
        e2e_runner = E2ECampaignRunner(repo_root=self.repo_root)
        orch_base, ctx = e2e_runner.initialize_pipeline()
        retrieval_service = ctx["retrieval_service"]
        registry = ctx["registry"]
        roadmap_base = ctx["roadmap"]
        ledger = ctx["ledger"]
        policy = ctx["policy"]

        telemetry_records: List[Dict[str, Any]] = []
        findings: List[Dict[str, Any]] = []
        overall_mismatches = 0

        try:
            for case_spec in self.phase1_cases:
                case_id = case_spec["case_id"]
                sev = case_spec["severity_order"]
                attack_cls = case_spec["attack_class"]
                desc = case_spec["description"]
                exp_route = case_spec["expected_route"]
                exp_verdict = case_spec["expected_verdict"]

                print(f"\n[{sev}/12] Executing {case_id} ({attack_cls})...")
                print(f"     Description: {desc}")

                initial_ledger_count = len(ledger._entries)
                observed_route = "UNKNOWN"
                observed_verdict = "UNKNOWN"
                candidate_count = 0
                retrieved_doc_ids: List[str] = []
                retrieved_pages: List[int] = []
                caught_exception: Optional[str] = None
                side_effects: List[str] = []

                # -------------------------------------------------------------
                # CASE 1: P1-CURR-07 (unmet_prerequisite)
                # -------------------------------------------------------------
                if case_id == "P1-CURR-07":
                    # Student without prerequisite evidence (student-adv-curr-07)
                    student_id = case_spec["input"]["student_id"]
                    orch_07 = SessionOrchestrator(
                        session_id=f"sess-{case_id}",
                        student_id=student_id,
                        roadmap=roadmap_base,
                        policy=policy,
                        ledger=ledger,
                        retrieval_port=ctx["retrieval_service"],
                        tutor_port=orch_base.tutor_port,
                        audit_port=orch_base.audit_port,
                        execution_port=orch_base.execution_port,
                        assessment_port=orch_base.assessment_port,
                        ingestion_port=orch_base.ingestion_port,
                        state_read_port=None,
                        curriculum_registry=registry,
                    )
                    req = SessionRequest(
                        session_id=f"sess-{case_id}",
                        student_id=student_id,
                        node_id=case_spec["input"]["node_id"],
                        query=case_spec["input"]["query"],
                        turn_index=0,
                    )
                    res: SessionResult = orch_07.handle_session_request(req)
                    observed_route = res.status.value
                    observed_verdict = res.abstention_reason or "APPROVED"

                # -------------------------------------------------------------
                # CASE 2: P1-CURR-02 (unknown_node)
                # -------------------------------------------------------------
                elif case_id == "P1-CURR-02":
                    req = SessionRequest(
                        session_id=f"sess-{case_id}",
                        student_id=case_spec["input"]["student_id"],
                        node_id=case_spec["input"]["node_id"],
                        query=case_spec["input"]["query"],
                        turn_index=0,
                    )
                    res = orch_base.handle_session_request(req)
                    observed_route = res.status.value
                    observed_verdict = res.abstention_reason or "APPROVED"

                # -------------------------------------------------------------
                # CASE 3: P1-CURR-01 (missing_node)
                # -------------------------------------------------------------
                elif case_id == "P1-CURR-01":
                    try:
                        SessionRequest(
                            session_id=f"sess-{case_id}",
                            student_id=case_spec["input"]["student_id"],
                            node_id=case_spec["input"]["node_id"],
                            query=case_spec["input"]["query"],
                            turn_index=0,
                        )
                        observed_route = "BYPASSED_VALIDATION"
                        observed_verdict = "UNVALIDATED"
                    except ValidationError as ve:
                        caught_exception = str(ve)
                        observed_route = "FAIL_CLOSED"
                        observed_verdict = "VALIDATION_ERROR"

                # -------------------------------------------------------------
                # CASE 4: P1-CURR-01-B (whitespace_only_node)
                # -------------------------------------------------------------
                elif case_id == "P1-CURR-01-B":
                    req = SessionRequest(
                        session_id=f"sess-{case_id}",
                        student_id=case_spec["input"]["student_id"],
                        node_id=case_spec["input"]["node_id"],
                        query=case_spec["input"]["query"],
                        turn_index=0,
                    )
                    res = orch_base.handle_session_request(req)
                    observed_route = res.status.value
                    observed_verdict = res.abstention_reason or "APPROVED"

                # -------------------------------------------------------------
                # CASE 5: P1-CURR-08 (cross_notebook_request)
                # -------------------------------------------------------------
                elif case_id == "P1-CURR-08":
                    foreign_nb = case_spec["input"]["foreign_notebook_id"]
                    node_id = case_spec["input"]["node_id"]
                    query = case_spec["input"]["query"]
                    cands = retrieval_service.retrieve_evidence(
                        query=query,
                        node_id=node_id,
                        notebook_id=foreign_nb,
                        registry=registry,
                    )
                    candidate_count = len(cands)
                    # Also assert EvidenceEngine isolation
                    legit_cands = retrieval_service.retrieve_evidence(
                        query=query,
                        node_id=node_id,
                        registry=registry,
                    )
                    isolation_violation_caught = False
                    if legit_cands:
                        try:
                            EvidenceEngine().evaluate_candidates(
                                query=query,
                                notebook_id=foreign_nb,
                                candidates=legit_cands,
                            )
                        except CurricularIsolationError:
                            isolation_violation_caught = True

                    if candidate_count == 0 and isolation_violation_caught:
                        observed_route = "ABSTAINED"
                        observed_verdict = "ISOLATION_BREACH"
                    else:
                        observed_route = "LEAKED"
                        observed_verdict = "UNISOLATED"

                # -------------------------------------------------------------
                # CASE 6: P1-CURR-09 (node_not_in_notebook)
                # -------------------------------------------------------------
                elif case_id == "P1-CURR-09":
                    nb_id = case_spec["input"]["notebook_id"]
                    node_id = case_spec["input"]["node_id"]
                    query = case_spec["input"]["query"]
                    cands = retrieval_service.retrieve_evidence(
                        query=query,
                        node_id=node_id,
                        notebook_id=nb_id,
                        registry=registry,
                    )
                    candidate_count = len(cands)
                    if candidate_count == 0:
                        observed_route = "ABSTAINED"
                        observed_verdict = "CURRICULAR_MISMATCH"
                    else:
                        observed_route = "ADMITTED"
                        observed_verdict = "MISMATCH_IGNORED"

                # -------------------------------------------------------------
                # CASE 7: P1-CURR-04 (unauthorized_document)
                # -------------------------------------------------------------
                elif case_id == "P1-CURR-04":
                    node_id = case_spec["input"]["node_id"]
                    query = case_spec["input"]["query"]
                    cands = retrieval_service.retrieve_evidence(
                        query=query,
                        node_id=node_id,
                        registry=registry,
                    )
                    candidate_count = len(cands)
                    retrieved_doc_ids = list({c.document_id for c in cands})
                    req = SessionRequest(
                        session_id=f"sess-{case_id}",
                        student_id=case_spec["input"]["student_id"],
                        node_id=node_id,
                        query=query,
                        turn_index=0,
                    )
                    res = orch_base.handle_session_request(req)
                    observed_route = res.status.value
                    observed_verdict = res.abstention_reason or "APPROVED"

                # -------------------------------------------------------------
                # CASE 8: P1-CURR-05 (unauthorized_page_range)
                # -------------------------------------------------------------
                elif case_id == "P1-CURR-05":
                    node_id = case_spec["input"]["node_id"]
                    query = case_spec["input"]["query"]
                    cands = retrieval_service.retrieve_evidence(
                        query=query,
                        node_id=node_id,
                        registry=registry,
                    )
                    candidate_count = len(cands)
                    retrieved_doc_ids = list({c.document_id for c in cands})
                    retrieved_pages = sorted(
                        list({c.page_start for c in cands if c.page_start is not None})
                    )
                    req = SessionRequest(
                        session_id=f"sess-{case_id}",
                        student_id=case_spec["input"]["student_id"],
                        node_id=node_id,
                        query=query,
                        turn_index=0,
                    )
                    res = orch_base.handle_session_request(req)
                    observed_route = res.status.value
                    observed_verdict = res.abstention_reason or "APPROVED"

                # -------------------------------------------------------------
                # CASE 9: P1-CURR-03 (missing_alignment)
                # -------------------------------------------------------------
                elif case_id == "P1-CURR-03":
                    node_id = case_spec["input"]["node_id"]
                    query = case_spec["input"]["query"]

                    # 1. Test direct registry and retrieval behavior
                    alignment_missing_error_caught = False
                    try:
                        registry.get_scoped_sources_for_node(node_id)
                    except CurriculumNotFoundError:
                        alignment_missing_error_caught = True

                    cands = retrieval_service.retrieve_evidence(
                        query=query,
                        node_id=node_id,
                        registry=registry,
                    )
                    candidate_count = len(cands)

                    # 2. Test orchestrator behavior when node exists in DAG but has no alignment
                    synthetic_node = RoadmapNode(
                        node_id=node_id,
                        title="Virtual Memory Management",
                        description="Virtual memory concepts without alignment mapping",
                        node_type=NodeType.TOPIC,
                        notebook_id="NB-SEC-03-OS-MEM",
                    )
                    augmented_nodes = dict(roadmap_base.nodes)
                    augmented_nodes[node_id] = synthetic_node
                    augmented_roadmap = roadmap_base.model_copy(
                        update={"nodes": augmented_nodes}
                    )

                    orch_aug = SessionOrchestrator(
                        session_id=f"sess-{case_id}",
                        student_id=case_spec["input"]["student_id"],
                        roadmap=augmented_roadmap,
                        policy=policy,
                        ledger=ledger,
                        retrieval_port=ctx["retrieval_service"],
                        tutor_port=orch_base.tutor_port,
                        audit_port=orch_base.audit_port,
                        execution_port=orch_base.execution_port,
                        assessment_port=orch_base.assessment_port,
                        ingestion_port=orch_base.ingestion_port,
                        state_read_port=None,
                        curriculum_registry=registry,
                    )
                    req = SessionRequest(
                        session_id=f"sess-{case_id}",
                        student_id=case_spec["input"]["student_id"],
                        node_id=node_id,
                        query=query,
                        turn_index=0,
                    )
                    res = orch_aug.handle_session_request(req)
                    observed_route = res.status.value
                    observed_verdict = res.abstention_reason or "APPROVED"

                # -------------------------------------------------------------
                # CASE 10: P1-CURR-06-A (advanced_topic_no_match)
                # -------------------------------------------------------------
                elif case_id == "P1-CURR-06-A":
                    node_id = case_spec["input"]["node_id"]
                    query = case_spec["input"]["query"]
                    cands = retrieval_service.retrieve_evidence(
                        query=query,
                        node_id=node_id,
                        registry=registry,
                    )
                    candidate_count = len(cands)
                    req = SessionRequest(
                        session_id=f"sess-{case_id}",
                        student_id=case_spec["input"]["student_id"],
                        node_id=node_id,
                        query=query,
                        turn_index=0,
                    )
                    res = orch_base.handle_session_request(req)
                    observed_route = res.status.value
                    observed_verdict = res.abstention_reason or "APPROVED"

                # -------------------------------------------------------------
                # CASE 11: P1-CURR-06-B (advanced_topic_low_score)
                # -------------------------------------------------------------
                elif case_id == "P1-CURR-06-B":
                    node_id = case_spec["input"]["node_id"]
                    query = case_spec["input"]["query"]
                    cands = retrieval_service.retrieve_evidence(
                        query=query,
                        node_id=node_id,
                        registry=registry,
                    )
                    candidate_count = len(cands)
                    req = SessionRequest(
                        session_id=f"sess-{case_id}",
                        student_id=case_spec["input"]["student_id"],
                        node_id=node_id,
                        query=query,
                        turn_index=0,
                    )
                    res = orch_base.handle_session_request(req)
                    observed_route = res.status.value
                    observed_verdict = res.abstention_reason or "APPROVED"

                # -------------------------------------------------------------
                # CASE 12: P1-CURR-10 (stale_roadmap_revision)
                # -------------------------------------------------------------
                elif case_id == "P1-CURR-10":
                    # Check if SessionRequest has roadmap_revision_id field
                    has_field = "roadmap_revision_id" in SessionRequest.model_fields
                    if not has_field:
                        observed_route = "DESIGN_WEAKNESS"
                        observed_verdict = "FIELD_NOT_IN_SESSION_REQUEST"
                        caught_exception = (
                            "SessionRequest schema currently does not define 'roadmap_revision_id' "
                            "(extra='forbid'). Replay protection deferred to Hito 8 release hardening."
                        )
                    else:
                        observed_route = "FAIL_CLOSED"
                        observed_verdict = "STALE_ROADMAP"

                final_ledger_count = len(ledger._entries)
                ledger_delta = final_ledger_count - initial_ledger_count

                # Compare against Oracle
                mismatches: List[str] = []
                if observed_route != exp_route:
                    mismatches.append(
                        f"Route mismatch: expected '{exp_route}', got '{observed_route}'"
                    )
                if observed_verdict != exp_verdict:
                    mismatches.append(
                        f"Verdict mismatch: expected '{exp_verdict}', got '{observed_verdict}'"
                    )
                if ledger_delta != case_spec["expected_ledger_delta"]:
                    mismatches.append(
                        f"Ledger delta mismatch: expected {case_spec['expected_ledger_delta']}, got {ledger_delta}"
                    )

                # Classify
                if not mismatches:
                    if exp_route == "DESIGN_WEAKNESS":
                        classification = "DESIGN_WEAKNESS"
                    else:
                        classification = "CONFIRMED_PASS"
                else:
                    classification = "CONFIRMED_DEFECT"
                    overall_mismatches += 1

                print(f"     Observed Route:    {observed_route} (Expected: {exp_route})")
                print(f"     Observed Verdict:  {observed_verdict} (Expected: {exp_verdict})")
                print(f"     Candidates Found:  {candidate_count}")
                print(f"     Classification:    {classification}")
                if mismatches:
                    for m in mismatches:
                        print(f"     ❌ {m}")

                record = {
                    "case_id": case_id,
                    "severity_order": sev,
                    "attack_class": attack_cls,
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "classification": classification,
                    "input": case_spec["input"],
                    "oracle_expected": {
                        "route": exp_route,
                        "verdict": exp_verdict,
                        "ledger_delta": case_spec["expected_ledger_delta"],
                    },
                    "observed": {
                        "route": observed_route,
                        "verdict": observed_verdict,
                        "ledger_delta": ledger_delta,
                        "candidate_count": candidate_count,
                        "retrieved_doc_ids": retrieved_doc_ids,
                        "retrieved_pages": retrieved_pages,
                        "caught_exception": caught_exception,
                    },
                    "mismatches": mismatches,
                }
                telemetry_records.append(record)

                finding = {
                    "case_id": case_id,
                    "severity_order": sev,
                    "attack_class": attack_cls,
                    "classification": classification,
                    "description": desc,
                    "mismatches": mismatches,
                }
                findings.append(finding)

        finally:
            e2e_runner.cleanup()

        # Build campaign summary
        summary = {
            "campaign_id": self.oracle["campaign_id"],
            "phase": "phase_1_curriculum_attacks",
            "executed_at_utc": datetime.now(timezone.utc).isoformat(),
            "total_cases": len(self.phase1_cases),
            "passed_cases": sum(
                1 for f in findings if f["classification"] == "CONFIRMED_PASS"
            ),
            "defects_found": sum(
                1 for f in findings if f["classification"] == "CONFIRMED_DEFECT"
            ),
            "design_weaknesses": sum(
                1 for f in findings if f["classification"] == "DESIGN_WEAKNESS"
            ),
            "findings": findings,
            "verdict": (
                "ABORT_ON_DEFECT" if overall_mismatches > 0 else "CERTIFIED_PASS"
            ),
        }

        results_data = {
            "campaign_id": self.oracle["campaign_id"],
            "phase": "phase_1_curriculum_attacks",
            "summary": summary,
            "cases": telemetry_records,
        }

        # Write output artifacts
        results_file = self.repo_root / "data/experiments/hito6/hito6_results.json"
        telemetry_file = self.repo_root / "data/experiments/hito6/hito6_telemetry.json"
        summary_file = self.repo_root / "data/experiments/hito6/hito6_summary.json"

        results_file.write_text(json.dumps(results_data, indent=2) + "\n")
        telemetry_file.write_text(json.dumps(telemetry_records, indent=2) + "\n")
        summary_file.write_text(json.dumps(summary, indent=2) + "\n")

        print("\n" + "=" * 75)
        print("📊 RESUMEN FINAL DE LA CAMPAÑA FASE 1")
        print("=" * 75)
        print(f"Total Casos Evaluados:      {summary['total_cases']}")
        print(f"CONFIRMED_PASS:             {summary['passed_cases']}")
        print(f"CONFIRMED_DEFECT:           {summary['defects_found']}")
        print(f"DESIGN_WEAKNESS:            {summary['design_weaknesses']}")
        print(f"Veredicto Formal de Fase 1: {summary['verdict']}")
        print("=" * 75)

        return results_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Hito 6 Phase 1 Runner")
    parser.add_argument(
        "--oracle",
        type=str,
        default=str(REPO_ROOT / "data/experiments/hito6/hito6_oracle.json"),
        help="Path to differential oracle",
    )
    args = parser.parse_args()

    runner = Phase1CurriculumRunner(repo_root=REPO_ROOT, oracle_path=Path(args.oracle))
    results = runner.run_all_cases()
    verdict = results["summary"]["verdict"]
    return 0 if verdict == "CERTIFIED_PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
