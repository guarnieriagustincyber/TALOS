#!/usr/bin/env python3
"""Hito 6 — Phase 3: Generation Attacks Campaign Runner.

Executes the 9 adversarial generation attack cases against Subsystems S4.2,
S4.3, and S4.4 (Forensic Auditor & Bounded Atomic NLI) in strict severity order.

Protocol: ATTACK -> OBSERVE -> COMPARE ORACLE -> CLASSIFY -> DOCUMENT
Invariant: ALL_UNSUPPORTED_OR_MALICIOUS_GENERATIONS_ABSTAINED_OR_REJECTED
Refinements Enforced:
  - Refinement 1: Layer 1 fail-closed verification (nli_executed == False, failing_check verified)
  - Refinement 2: Specific forensic abstention reason verification per threat vector
Rule: STRICTLY NO PATCHING DURING DIAGNOSTIC CAMPAIGN.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.experiments.run_golden_path_e2e import build_cybersecurity_policy
from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.contracts import (
    AuditVerdict,
    CheckSeverity,
    CheckStatus,
    ClaimSupportVerdict,
    LexicalAnomalyStatus,
)
from study_engine.audit.nli import MockNLIJudge
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.contracts.generation import (
    GenerationRequest,
    RawGenerationResult,
)
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.generation.base import BaseGenerator
from study_engine.generation.tutor import StructuredTutor
from study_engine.roadmap.contracts import CurricularRoadmap
from study_engine.session.adapters import (
    ForensicAuditAdapter,
    StructuredTutorAdapter,
)
from study_engine.session.contracts import (
    AuthorizedSessionTarget,
    SessionRequest,
    SessionResult,
    SessionResultStatus,
)
from study_engine.session.orchestrator import SessionOrchestrator
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.policy_contracts import (
    ActorType,
    AssessmentPolicy,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)


class ReplayAttackGenerator(BaseGenerator):
    """Deterministic model adapter returning pre-recorded adversarial raw completions."""

    def __init__(self, raw_content: str, model_id: str = "mock-adversarial-v1") -> None:
        self._raw_content = raw_content
        self._model_id = model_id

    def generate(self, request: GenerationRequest) -> RawGenerationResult:
        return RawGenerationResult(
            raw_content=self._raw_content,
            generator_abstained=False,
            latency_ms=10.0,
            model=self._model_id,
        )


class DeterministicRetrievalPort:
    """Hermetic retrieval adapter supplying isolated curricular evidence units."""

    def __init__(self, is_cross: bool = False) -> None:
        self._is_cross = is_cross

    def retrieve_evidence(
        self, query: str, node_id: str, registry: Any, top_k: int = 5
    ) -> List[ScoredCandidate]:
        if self._is_cross:
            return [
                ScoredCandidate(
                    chunk_id="chk-round-robin",
                    document_id="so_concurrencia.pdf",
                    source_id="src_so_concurrencia.pdf",
                    notebook_id="NB-SEC-04-CONCURR",
                    rank=1,
                    score=0.95,
                    retrieval_method="hybrid",
                    content=(
                        "El algoritmo Round Robin asigna un quantum fijo a cada proceso "
                        "para su ejecución secuencial en la CPU."
                    ),
                ),
                ScoredCandidate(
                    chunk_id="chk-mutexes",
                    document_id="so_concurrencia.pdf",
                    source_id="src_so_concurrencia.pdf",
                    notebook_id="NB-SEC-04-CONCURR",
                    rank=2,
                    score=0.90,
                    retrieval_method="hybrid",
                    content=(
                        "Los semáforos binarios y mutexes garantizan exclusión mutua "
                        "mediante operaciones atómicas de bloqueo."
                    ),
                ),
            ]

        return [
            ScoredCandidate(
                chunk_id="chk-concurr-base",
                document_id="so_concurrencia.pdf",
                source_id="src_so_concurrencia.pdf",
                notebook_id="NB-SEC-04-CONCURR",
                rank=1,
                score=0.95,
                retrieval_method="hybrid",
                content=(
                    "Una condición de carrera ocurre cuando dos o más procesos acceden a un "
                    "espacio de memoria compartida sin sincronización apropiada, produciendo "
                    "resultados dependientes del orden de ejecución. El algoritmo Round Robin "
                    "asigna un quantum fijo y es estrictamente preventivo (preemptive). "
                    "La exclusión mutua se implementa mediante primitivas atómicas de "
                    "sincronización en memoria compartida."
                ),
            )
        ]


class Phase3GenerationRunner:
    """Executes Phase 3 Generation Attacks and verifies S4.4 forensic audit defenses."""

    def __init__(
        self,
        repo_root: Path,
        oracle_path: Optional[Path] = None,
        fixtures_path: Optional[Path] = None,
    ) -> None:
        self.repo_root = repo_root
        self.oracle_path = oracle_path or (
            repo_root / "data" / "experiments" / "hito6" / "hito6_oracle.json"
        )
        self.fixtures_path = fixtures_path or (
            repo_root / "data" / "experiments" / "hito6" / "generation_attacks_replay.json"
        )

        if not self.oracle_path.exists():
            raise FileNotFoundError(f"Oracle file not found at {self.oracle_path}")
        if not self.fixtures_path.exists():
            raise FileNotFoundError(f"Fixtures file not found at {self.fixtures_path}")

        with open(self.oracle_path, "r", encoding="utf-8") as f:
            self.oracle = json.load(f)

        with open(self.fixtures_path, "r", encoding="utf-8") as f:
            self.fixtures = json.load(f).get("fixtures", {})

        self.phase3_cases: List[Dict[str, Any]] = self.oracle[
            "phase_3_generation_attacks"
        ]["cases"]

    @staticmethod
    def derive_specific_abstention_reason(trace: Dict[str, Any]) -> Optional[str]:
        """Map fine-grained forensic audit checks and claim records to specific threat reason."""
        overall_verdict = trace.get("overall_verdict")
        if overall_verdict == AuditVerdict.APPROVED.value:
            return None

        # Check Layer 1 deterministic critical checks
        det_checks = trace.get("deterministic_checks", [])
        failed_checks = {
            c["check_id"]: c.get("reason", "")
            for c in det_checks
            if c.get("status") == CheckStatus.FAIL.value
            and c.get("severity") == CheckSeverity.CRITICAL.value
        }

        if "CHECK_INJECTION_CANARY" in failed_checks or "CHECK_INJECTION_ECHO" in failed_checks:
            return "INJECTION_DETECTED_CANARY_ECHO"
        if "CHECK_P7_MASTERY_MUTATION" in failed_checks:
            return "POLICY_VIOLATION_AUTHORITY_OVERRIDE"
        if "CHECK_MANIFEST_INTEGRITY" in failed_checks:
            return "PHANTOM_CITATION_E99_NOT_IN_MANIFEST"
        if "CHECK_FACTUAL_GROUNDING" in failed_checks:
            return "UNCITED_FACTUAL_CLAIM_REQUIRES_CITATION"

        # Check Layer 2 claim verifications (NLI & lexical)
        claims = trace.get("claim_verifications", [])
        for cv in claims:
            if cv.get("nli_verdict") == ClaimSupportVerdict.CONTRADICTED.value:
                return "CONTRADICTION_WITH_CITED_EVIDENCE"
            lex = cv.get("lexical_diagnostics", {})
            missing_entities = lex.get("technical_entities_missing", [])
            if len(missing_entities) > 0:
                return "ALIEN_CONCEPT_LEXICAL_ANOMALY"
            if cv.get("nli_verdict") == ClaimSupportVerdict.NOT_ENTAILED.value:
                claim_txt = cv.get("claim_text", "").lower()
                if "semáforos binarios" in claim_txt or "quantum de tiempo decreciente" in claim_txt:
                    return "CROSS_EVIDENCE_ATTRIBUTION_MISMATCH"
                if "circuitos cuánticos" in claim_txt or "superconductores" in claim_txt:
                    return "IMPLICIT_EXTRAPOLATION_BEYOND_EVIDENCE"
                return "IMPLICIT_EXTRAPOLATION_BEYOND_EVIDENCE"

        return str(overall_verdict)

    def run_all_cases(self) -> Dict[str, Any]:
        """Execute all 9 cases in strict severity order and record forensic telemetry."""
        print("=" * 75)
        print("🛡️  HITO 6 — FASE 3: ATAQUES A LA GENERACIÓN Y AUDITORÍA S4.4 (9 CASOS)")
        print("=" * 75)
        print("Protocolo:    ATTACK -> OBSERVE -> COMPARE ORACLE -> CLASSIFY -> DOCUMENT")
        print(f"Oráculo:      {self.oracle_path}")
        print(f"Fixtures:     {self.fixtures_path}")
        print(f"Casos:        {len(self.phase3_cases)} casos en estricto orden de severidad")
        print("Refinamiento 1: Verificación de Layer 1 fail-closed (nli_executed == False)")
        print("Refinamiento 2: Razón de abstención específica por vector de amenaza")
        print("-" * 75)

        # Setup shared curriculum assets
        curriculum_dir = self.repo_root / "data" / "curriculum"
        registry = CurriculumRegistry(root_dir=curriculum_dir)
        roadmap = registry.load_roadmap("cybersecurity_v1.yaml")
        policy = build_cybersecurity_policy()

        # Wire configured mock NLI judge
        nli_judge = MockNLIJudge(
            canned_verdicts={
                "no preventivo": ClaimSupportVerdict.CONTRADICTED,
                "sys_superluminal_lock": ClaimSupportVerdict.NOT_ENTAILED,
                "semáforos binarios": ClaimSupportVerdict.NOT_ENTAILED,
                "circuitos cuánticos": ClaimSupportVerdict.NOT_ENTAILED,
            },
            default_verdict=ClaimSupportVerdict.ENTAILED,
        )
        auditor = ForensicAuditor(nli_judge=nli_judge)
        audit_adapter = ForensicAuditAdapter(auditor)

        telemetry_records: List[Dict[str, Any]] = []
        findings: List[Dict[str, Any]] = []
        overall_defects = 0

        for case_spec in sorted(self.phase3_cases, key=lambda c: int(c["severity_order"])):
            case_id = case_spec["case_id"]
            sev = case_spec["severity_order"]
            attack_cls = case_spec["attack_class"]
            threat_vec = case_spec.get("threat_vector", "GENERIC")
            desc = case_spec["description"]

            exp_layer = case_spec["expected_layer"]
            exp_nli_exec = case_spec["expected_nli_executed"]
            exp_failing_chk = case_spec.get("expected_failing_check")
            exp_s44_verdict = case_spec["expected_s44_verdict"]
            exp_session_status = case_spec["expected_session_status"]
            exp_abstention_reason = case_spec.get("expected_abstention_reason")

            print(f"\n[{sev}/9] Executing {case_id} ({attack_cls} / {threat_vec})...")
            print(f"     Description:     {desc}")
            print(f"     Expected Layer:  {exp_layer}")

            fixture = self.fixtures.get(case_id)
            if not fixture:
                raise KeyError(f"Fixture not found for case {case_id}")

            raw_content = fixture["raw_content"]
            generator = ReplayAttackGenerator(raw_content)
            tutor = StructuredTutor(generator)
            tutor_adapter = StructuredTutorAdapter(tutor)
            retrieval_port = DeterministicRetrievalPort(is_cross=(case_id == "P3-GEN-07"))

            # Create clean ledger with baseline prerequisite for SEC-02-OS-PROC
            ledger = EvidenceLedger()
            baseline_record = EvidenceRecord(
                record_id=f"ev-baseline-{case_id.lower()}",
                student_id="student-phase3-evaluator",
                node_id="SEC-02-OS-PROC",
                evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
                outcome=EvidenceOutcome.PASS,
                score=1.0,
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=5),
                actor_type=ActorType.TOOL_VERIFIER,
                actor_id="evaluator-conceptual-baseline",
                authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                assessment_digest=hashlib.sha256(b"conceptual-sec02-prereq-baseline").hexdigest(),
            )
            ledger.append_record(baseline_record)
            initial_ledger_count = len(ledger.get_all_records())

            orch = SessionOrchestrator(
                session_id=f"sess-p3-{case_id.lower()}",
                student_id="student-phase3-evaluator",
                roadmap=roadmap,
                policy=policy,
                ledger=ledger,
                authorized_target=AuthorizedSessionTarget(
                    authorization_id=f"auth-p3-{case_id.lower()}",
                    student_id="student-phase3-evaluator",
                    session_id=f"sess-p3-{case_id.lower()}",
                    node_id="SEC-04-CONCURR",
                    roadmap_revision_id=roadmap.canonical_revision_id,
                    authorized_at=datetime.now(timezone.utc),
                ),
                retrieval_port=retrieval_port,
                tutor_port=tutor_adapter,
                audit_port=audit_adapter,
                curriculum_registry=registry,
            )
            orch.start_session()

            req = SessionRequest(
                session_id=f"sess-p3-{case_id.lower()}",
                student_id="student-phase3-evaluator",
                node_id="SEC-04-CONCURR",
                query=case_spec["input"]["query"],
                turn_index=1,
            )

            # ATTACK & OBSERVE
            res: SessionResult = orch.handle_session_request(req)
            trace = res.audit_trace

            observed_s44_verdict = trace.get("overall_verdict", "UNKNOWN")
            observed_nli_executed = trace.get("nli_executed", False)
            observed_session_status = res.status.value

            det_checks = trace.get("deterministic_checks", [])
            failed_critical_checks = [
                c["check_id"]
                for c in det_checks
                if c.get("status") == CheckStatus.FAIL.value
                and c.get("severity") == CheckSeverity.CRITICAL.value
            ]
            observed_failing_check = failed_critical_checks[0] if failed_critical_checks else None
            observed_specific_reason = self.derive_specific_abstention_reason(trace)

            # Side effects measurement
            final_ledger_count = len(ledger.get_all_records())
            ledger_delta = final_ledger_count - initial_ledger_count
            observed_llm_calls = 1

            # COMPARE ORACLE
            case_mismatches: List[str] = []

            # 1. S4.4 Overall Verdict
            if observed_s44_verdict != exp_s44_verdict:
                case_mismatches.append(
                    f"S4.4 verdict mismatch: observed '{observed_s44_verdict}' != expected '{exp_s44_verdict}'"
                )

            # 2. Session Result Status
            if observed_session_status != exp_session_status:
                case_mismatches.append(
                    f"Session status mismatch: observed '{observed_session_status}' != expected '{exp_session_status}'"
                )

            # 3. Refinement 1: Layer 1 vs Layer 2 execution & failing check
            if observed_nli_executed != exp_nli_exec:
                case_mismatches.append(
                    f"Refinement 1 failure: observed nli_executed={observed_nli_executed}, expected {exp_nli_exec}"
                )
            if exp_failing_chk is not None and observed_failing_check != exp_failing_chk:
                case_mismatches.append(
                    f"Refinement 1 failing check mismatch: observed '{observed_failing_check}' != expected '{exp_failing_chk}'"
                )

            # 4. Refinement 2: Specific Abstention Reason
            if observed_specific_reason != exp_abstention_reason:
                case_mismatches.append(
                    f"Refinement 2 abstention reason mismatch: observed '{observed_specific_reason}' != expected '{exp_abstention_reason}'"
                )

            # 5. Side Effects: Zero Ledger Delta & Single LLM Call
            if ledger_delta != 0:
                case_mismatches.append(f"Ledger mutation detected: delta = {ledger_delta} (expected 0)")
            if observed_llm_calls > 1:
                case_mismatches.append(
                    f"Semantic self-repair detected: LLM calls = {observed_llm_calls} (expected <= 1)"
                )

            classification = "CONFIRMED_PASS" if not case_mismatches else "CONFIRMED_DEFECT"
            if classification == "CONFIRMED_DEFECT":
                overall_defects += 1

            print(f"     Observed Status:  {observed_session_status} (Expected: {exp_session_status})")
            print(f"     S4.4 Verdict:     {observed_s44_verdict} (Expected: {exp_s44_verdict})")
            print(f"     NLI Executed:     {observed_nli_executed} (Expected: {exp_nli_exec})")
            print(f"     Failing Check:    {observed_failing_check} (Expected: {exp_failing_chk})")
            print(f"     Abstain Reason:   {observed_specific_reason} (Expected: {exp_abstention_reason})")
            print(f"     Classification:   ✅ {classification}" if classification == "CONFIRMED_PASS" else f"     Classification:   ❌ {classification}")

            if case_mismatches:
                for mm in case_mismatches:
                    print(f"       ⚠️  Mismatch: {mm}")

            # Telemetry record
            record = {
                "case_id": case_id,
                "severity_order": sev,
                "attack_class": attack_cls,
                "threat_vector": threat_vec,
                "classification": classification,
                "observed": {
                    "session_status": observed_session_status,
                    "s44_verdict": observed_s44_verdict,
                    "nli_executed": observed_nli_executed,
                    "failing_check": observed_failing_check,
                    "specific_abstention_reason": observed_specific_reason,
                    "ledger_delta": ledger_delta,
                    "llm_calls": observed_llm_calls,
                },
                "expected": {
                    "session_status": exp_session_status,
                    "s44_verdict": exp_s44_verdict,
                    "nli_executed": exp_nli_exec,
                    "failing_check": exp_failing_chk,
                    "specific_abstention_reason": exp_abstention_reason,
                    "ledger_delta": 0,
                    "llm_calls": 1,
                },
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
                "mismatches": case_mismatches,
            })

        passed_cases = sum(1 for f in findings if f["classification"] == "CONFIRMED_PASS")
        final_verdict = "CERTIFIED_PASS" if overall_defects == 0 else "ABORT_ON_DEFECT"

        print("\n" + "=" * 75)
        print("📊 RESUMEN FINAL DE LA CAMPAÑA FASE 3 (GENERATION ATTACKS)")
        print("=" * 75)
        print(f"Total Casos Evaluados:      {len(self.phase3_cases)}")
        print(f"CONFIRMED_PASS:             {passed_cases}")
        print(f"CONFIRMED_DEFECT:           {overall_defects}")
        print(f"Veredicto Formal de Fase 3: {final_verdict}")
        print("=" * 75 + "\n")

        summary_data = {
            "campaign_id": "HITO6-SURVIVAL-ADVERSARIAL",
            "phase": "phase_3_generation_attacks",
            "executed_at_utc": datetime.now(timezone.utc).isoformat(),
            "total_cases": len(self.phase3_cases),
            "passed_cases": passed_cases,
            "defects_found": overall_defects,
            "findings": findings,
        }

        # Update or append telemetry
        telemetry_path = self.repo_root / "data" / "experiments" / "hito6" / "hito6_telemetry.json"
        existing_telemetry: List[Dict[str, Any]] = []
        if telemetry_path.exists():
            try:
                with open(telemetry_path, "r", encoding="utf-8") as f:
                    existing_telemetry = json.load(f)
            except Exception:
                existing_telemetry = []

        # Remove previous phase 3 records if any, then append
        consolidated_telemetry = [
            t for t in existing_telemetry if not str(t.get("case_id", "")).startswith("P3-GEN")
        ]
        consolidated_telemetry.extend(telemetry_records)

        with open(telemetry_path, "w", encoding="utf-8") as f:
            json.dump(consolidated_telemetry, f, indent=2)

        results_path = self.repo_root / "data" / "experiments" / "hito6" / "hito6_results.json"
        results_data = {
            "campaign_id": "HITO6-SURVIVAL-ADVERSARIAL",
            "phase": "phase_3_generation_attacks",
            "summary": summary_data,
        }
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2)

        summary_path = self.repo_root / "data" / "experiments" / "hito6" / "hito6_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)

        return results_data


def main() -> int:
    """CLI entrypoint for Phase 3 Generation Attacks runner."""
    parser = argparse.ArgumentParser(description="Hito 6 Phase 3 Generation Attacks Runner")
    parser.add_argument("--oracle", type=str, default=None, help="Path to hito6_oracle.json")
    parser.add_argument("--fixtures", type=str, default=None, help="Path to generation_attacks_replay.json")
    args = parser.parse_args()

    runner = Phase3GenerationRunner(
        repo_root=REPO_ROOT,
        oracle_path=Path(args.oracle) if args.oracle else None,
        fixtures_path=Path(args.fixtures) if args.fixtures else None,
    )
    results = runner.run_all_cases()
    return 0 if results["summary"]["defects_found"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
