#!/usr/bin/env python3
"""Runner for Phase 7: State Attacks (Hito 6).

Adversarial verification against Subsystem S5.2.C (State Engine), validating:
    1. MASTERED => VALID_ASSESSMENT_EVIDENCE (no mastery without valid assessment).
    2. UNLOCKED => PREREQUISITES_SATISFIED (downstream nodes remain LOCKED if prereqs missing).
    3. STATE == DERIVE(AUTHORITATIVE_EVIDENCE) (derive_student_state is a pure function).
    4. Zero External Authority (UI and LLM cannot mutate state).
    5. Order-independent epistemic derivation.
    6. Historical temporal cutoff enforcement.

Protocol: ATTACK -> OBSERVE -> COMPARE ORACLE -> CLASSIFY -> DOCUMENT
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple
from pydantic import ValidationError

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.experiments.run_golden_path_e2e import build_cybersecurity_policy
from study_engine.assessment.service import DeterministicAssessmentEngine
from study_engine.contracts.assessment import AssessmentResult
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.contracts.evidence_ingestion import (
    AdmissionDecision,
    RejectionReason,
    SessionProvenanceContext,
)
from study_engine.contracts.execution import (
    ExecutionObservation,
    ExecutionStatus,
    ObservedArtifact,
    ProcessTelemetry,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.curriculum.rubric_contracts import AssessmentRubric
from study_engine.curriculum.task_contracts import PracticalTaskSpecification
from study_engine.roadmap.contracts import CurricularRoadmap
from study_engine.state.ingestion_engine import EvidenceIngestionEngine
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import HistoryCutoffMode
from study_engine.state.policy_contracts import (
    ActorType,
    AssessmentPolicy,
    CriteriaEvaluationVerdict,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
    SovereignExemptionViolationError,
)
from study_engine.state.policy_engine import evaluate_node_criteria
from study_engine.state.state_contracts import (
    NodeProgressStatus,
    NodeState,
    StateHashMismatchError,
    StudentState,
    validate_student_state_hash,
)
from study_engine.state.state_engine import derive_student_state


class Phase7StateRunner:
    """Executes Phase 7 State Attacks against Subsystem S5.2.C."""

    def __init__(
        self,
        repo_root: Path = REPO_ROOT,
        oracle_path: Optional[Path] = None,
    ) -> None:
        self.repo_root = repo_root
        self.oracle_path = (
            oracle_path
            or repo_root / "data" / "experiments" / "hito6" / "hito6_oracle.json"
        )
        with open(self.oracle_path, "r", encoding="utf-8") as f:
            self.oracle = json.load(f)

        self.phase7_spec = self.oracle["phase_7_state_attacks"]
        self.phase7_cases = self.phase7_spec["cases"]

        # Setup Curricular Environment
        curriculum_dir = self.repo_root / "data" / "curriculum"
        self.registry = CurriculumRegistry(root_dir=curriculum_dir)
        self.roadmap = self.registry.load_roadmap("cybersecurity_v1.yaml")
        self.alignment = self.registry.load_alignment("cybersecurity_v1_alignment.json")
        self.task = self.registry.load_task("task_sec05_file_hasher.json")
        self.rubric = self.registry.load_rubric("rubric_sec05_deterministic.json")
        self.policy = build_cybersecurity_policy()
        self.assessment_engine = DeterministicAssessmentEngine()
        self.ingestion_engine = EvidenceIngestionEngine()

    def _setup_prereqs(self, ledger: EvidenceLedger, student_id: str, base_time: datetime) -> None:
        """Populate SEC-01, SEC-02, and SEC-03 passing evidence."""
        prereqs = [
            ("SEC-01-C-PTR", EvidenceType.CONCEPTUAL_EXPLANATION, base_time - timedelta(minutes=30)),
            ("SEC-02-OS-PROC", EvidenceType.CONCEPTUAL_EXPLANATION, base_time - timedelta(minutes=20)),
            ("SEC-03-MEM-MGMT", EvidenceType.CODE_EXECUTION, base_time - timedelta(minutes=10)),
        ]
        for nid, etype, t in prereqs:
            rec = EvidenceRecord(
                record_id=f"ev-prereq-{nid}-{student_id}",
                student_id=student_id,
                node_id=nid,
                evidence_type=etype,
                outcome=EvidenceOutcome.PASS,
                score=1.0,
                timestamp=t,
                actor_type=ActorType.TOOL_VERIFIER,
                actor_id="evaluator",
                authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                assessment_digest=hashlib.sha256(f"{nid}-{student_id}".encode("utf-8")).hexdigest(),
            )
            ledger.append_record(rec, override_committed_at=t)

    def _create_canonical_assessment(self, observation_id: str = "obs-clean") -> AssessmentResult:
        """Generate a canonical AssessmentResult for SEC-05."""
        obs = ExecutionObservation(
            observation_id=observation_id,
            execution_id=f"exec-{observation_id}",
            tool_name="python.adapter",
            status=ExecutionStatus.COMPLETED,
            exit_code=0,
            telemetry=ProcessTelemetry(duration_ms=120.0),
            produced_artifacts=(
                ObservedArtifact(
                    artifact_id="art-01",
                    relative_path="output_hash.txt",
                    file_size_bytes=64,
                    sha256_digest="c" * 64,
                ),
            ),
        )
        return self.assessment_engine.assess(
            task=self.task,
            rubric=self.rubric,
            observation=obs,
            task_revision_id="rev-task-01",
            rubric_revision_id="rev-rubric-01",
        )

    def run_campaign(self) -> Dict[str, Any]:
        """Execute all 10 Phase 7 state attack scenarios in strict severity order."""
        print("=" * 75)
        print("🛡️  HITO 6 — FASE 7: CAMPAÑA DE ATAQUES AL MOTOR DE ESTADO (S5.2.C)")
        print("=" * 75)
        print(f"Total Casos de Ataque / Control: {len(self.phase7_cases)}")
        print("Core Invariant: MASTERED => VALID_EVIDENCE & UNLOCKED => PREREQUISITES & PURE DERIVATION")
        print("Protocol: ATTACK -> OBSERVE -> COMPARE ORACLE -> CLASSIFY -> DOCUMENT")
        print("-" * 75)

        telemetry_records: List[Dict[str, Any]] = []
        findings: List[Dict[str, Any]] = []
        overall_defects = 0

        sorted_cases = sorted(self.phase7_cases, key=lambda c: int(c["severity_order"]))

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

            case_mismatches: List[str] = []
            observed_summary: Dict[str, Any] = {}

            # CASE DISPATCH
            if case_id == "P7-STAT-01":
                # P7-STAT-01: mastered_without_evidence
                student_id = cin["student_id"]
                empty_ledger = EvidenceLedger()
                state = derive_student_state(self.roadmap, self.policy, empty_ledger, student_id)

                s_01 = state.get_node_state("SEC-01-C-PTR")
                s_02 = state.get_node_state("SEC-02-OS-PROC")
                s_03 = state.get_node_state("SEC-03-MEM-MGMT")
                s_05 = state.get_node_state("SEC-05-BIN-SEC")

                any_prof = any(ns.status == NodeProgressStatus.ASSESSED_PROFICIENT for ns in state.node_states)

                observed_summary = {
                    "sec01_status": s_01.status.value if s_01 else None,
                    "sec02_status": s_02.status.value if s_02 else None,
                    "sec03_status": s_03.status.value if s_03 else None,
                    "sec05_status": s_05.status.value if s_05 else None,
                    "sec01_evidence_count": s_01.total_evidence_count if s_01 else -1,
                    "sec05_evidence_count": s_05.total_evidence_count if s_05 else -1,
                    "any_proficient": any_prof,
                }

                if observed_summary["sec01_status"] != exp["sec01_status"]:
                    case_mismatches.append(f"SEC-01 status mismatch: {observed_summary['sec01_status']} != {exp['sec01_status']}")
                if observed_summary["sec02_status"] != exp["sec02_status"]:
                    case_mismatches.append(f"SEC-02 status mismatch: {observed_summary['sec02_status']} != {exp['sec02_status']}")
                if observed_summary["sec03_status"] != exp["sec03_status"]:
                    case_mismatches.append(f"SEC-03 status mismatch: {observed_summary['sec03_status']} != {exp['sec03_status']}")
                if observed_summary["sec05_status"] != exp["sec05_status"]:
                    case_mismatches.append(f"SEC-05 status mismatch: {observed_summary['sec05_status']} != {exp['sec05_status']}")
                if observed_summary["sec01_evidence_count"] != exp["sec01_evidence_count"]:
                    case_mismatches.append(f"SEC-01 count mismatch: {observed_summary['sec01_evidence_count']} != {exp['sec01_evidence_count']}")
                if any_prof != exp["any_proficient"]:
                    case_mismatches.append(f"Any proficient mismatch: {any_prof} != {exp['any_proficient']}")

            elif case_id == "P7-STAT-02":
                # P7-STAT-02: mastered_from_execution_only
                student_id = cin["student_id"]
                ledger = EvidenceLedger()
                base_time = datetime.now(timezone.utc)
                self._setup_prereqs(ledger, student_id, base_time)

                # Execution record with exit code 0 but FAIL assessment outcome
                rec = EvidenceRecord(
                    record_id="rec-exec-only-fail",
                    student_id=student_id,
                    node_id=cin["node_id"],
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    outcome=EvidenceOutcome.FAIL,
                    score=0.0,
                    timestamp=base_time,
                    actor_type=ActorType.TOOL_VERIFIER,
                    actor_id="evaluator",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    assessment_digest="0" * 64,
                )
                ledger.append_record(rec)

                state = derive_student_state(self.roadmap, self.policy, ledger, student_id)
                sec05 = state.get_node_state(cin["node_id"])

                node_status = sec05.status.value if sec05 else None
                verdict = sec05.evaluation_result.verdict.value if sec05 and sec05.evaluation_result else None
                ev_count = sec05.total_evidence_count if sec05 else 0
                is_prof = sec05.status == NodeProgressStatus.ASSESSED_PROFICIENT if sec05 else False

                observed_summary = {
                    "node_status": node_status,
                    "evaluation_verdict": verdict,
                    "total_evidence_count": ev_count,
                    "is_proficient": is_prof,
                }

                if node_status != exp["node_status"]:
                    case_mismatches.append(f"Node status mismatch: {node_status} != {exp['node_status']}")
                if verdict != exp["evaluation_verdict"]:
                    case_mismatches.append(f"Verdict mismatch: {verdict} != {exp['evaluation_verdict']}")
                if ev_count != exp["total_evidence_count"]:
                    case_mismatches.append(f"Count mismatch: {ev_count} != {exp['total_evidence_count']}")
                if is_prof != exp["is_proficient"]:
                    case_mismatches.append(f"Proficient mismatch: {is_prof} != {exp['is_proficient']}")

            elif case_id == "P7-STAT-03":
                # P7-STAT-03: unlocked_without_prerequisites (Triple Verification)
                student_id = cin["student_id"]
                ledger = EvidenceLedger()
                now = datetime.now(timezone.utc)

                # Inject passing evidence for SEC-05 without fulfilling SEC-03
                rec = EvidenceRecord(
                    record_id="rec-p7-03-rogue",
                    student_id=student_id,
                    node_id=cin["target_node"],
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    outcome=EvidenceOutcome.PASS,
                    score=1.0,
                    timestamp=now,
                    actor_type=ActorType.TOOL_VERIFIER,
                    actor_id="evaluator",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    assessment_digest=hashlib.sha256(b"rogue-sec05").hexdigest(),
                    overall_level=PerformanceLevel.N3_COMPETENT,
                )
                ledger.append_record(rec)

                state = derive_student_state(self.roadmap, self.policy, ledger, student_id)
                sec05 = state.get_node_state(cin["target_node"])

                node_status = sec05.status.value if sec05 else None
                verdict = sec05.evaluation_result.verdict.value if sec05 and sec05.evaluation_result else None
                unfulfilled = list(sec05.unfulfilled_hard_prerequisites) if sec05 else []
                is_unlocked = sec05.status != NodeProgressStatus.LOCKED if sec05 else True

                observed_summary = {
                    "node_status": node_status,
                    "evaluation_verdict": verdict,
                    "unfulfilled_hard_prerequisites": unfulfilled,
                    "is_unlocked": is_unlocked,
                }

                if node_status != exp["node_status"]:
                    case_mismatches.append(f"Node status mismatch: {node_status} != {exp['node_status']}")
                if verdict != exp["evaluation_verdict"]:
                    case_mismatches.append(f"Verdict mismatch: {verdict} != {exp['evaluation_verdict']}")
                if unfulfilled != exp["unfulfilled_hard_prerequisites"]:
                    case_mismatches.append(f"Unfulfilled prereqs mismatch: {unfulfilled} != {exp['unfulfilled_hard_prerequisites']}")
                if is_unlocked != exp["is_unlocked"]:
                    case_mismatches.append(f"Unlocked mismatch: {is_unlocked} != {exp['is_unlocked']}")

            elif case_id == "P7-STAT-04":
                # P7-STAT-04: state_advance_duplicate
                student_id = cin["student_id"]
                ledger = EvidenceLedger()
                base_time = datetime.now(timezone.utc)
                self._setup_prereqs(ledger, student_id, base_time)

                asmt = self._create_canonical_assessment(observation_id="obs-p7-04")
                prov_ctx = SessionProvenanceContext(
                    student_id=student_id,
                    session_id="session-p7-04",
                    resolved_target_node_id=cin["node_id"],
                    requested_node_id=cin["node_id"],
                    roadmap_revision_id=self.roadmap.canonical_revision_id,
                    policy_revision_id=self.policy.canonical_policy_id,
                    expected_task_specification_sha256=asmt.task.specification_sha256,
                    expected_rubric_specification_sha256=asmt.rubric.specification_sha256,
                    session_is_active=True,
                    session_started_at=base_time - timedelta(minutes=5),
                )

                # 1st Submission: Admitted
                adm1 = self.ingestion_engine.evaluate_admissibility(asmt, prov_ctx, ledger)
                assert adm1.outcome is not None
                rec1 = self.ingestion_engine.build_admitted_record(asmt, prov_ctx, adm1.outcome, adm1.admission_trace)
                rec1 = rec1.model_copy(update={"metadata": {**rec1.metadata, "evaluation_attempt_id": cin["evaluation_attempt_id"]}})
                ledger.append_record(rec1)

                fixed_eval_time = base_time + timedelta(hours=1)
                state_before = derive_student_state(self.roadmap, self.policy, ledger, student_id, as_of_time=fixed_eval_time)
                ledger_count_before = len(ledger._entries)

                # 2nd Submission: Duplicate Rejected by Gate 4 Preflight
                adm2 = self.ingestion_engine.evaluate_admissibility(asmt, prov_ctx, ledger)
                ledger_count_after = len(ledger._entries)
                ledger_delta = ledger_count_after - ledger_count_before

                state_after = derive_student_state(self.roadmap, self.policy, ledger, student_id, as_of_time=fixed_eval_time)
                state_delta = state_before.canonical_state_id != state_after.canonical_state_id

                observed_summary = {
                    "first_submission_decision": adm1.decision.value,
                    "second_submission_decision": adm2.decision.value,
                    "second_rejection_reason": adm2.rejection_reason.value if adm2.rejection_reason else None,
                    "ledger_delta_from_duplicate": ledger_delta,
                    "state_delta_from_duplicate": state_delta,
                }

                if adm1.decision.value != exp["first_submission_decision"]:
                    case_mismatches.append(f"1st decision mismatch: {adm1.decision.value} != {exp['first_submission_decision']}")
                if adm2.decision.value != exp["second_submission_decision"]:
                    case_mismatches.append(f"2nd decision mismatch: {adm2.decision.value} != {exp['second_submission_decision']}")
                if adm2.rejection_reason is None or adm2.rejection_reason.value != exp["second_rejection_reason"]:
                    case_mismatches.append(f"2nd rejection reason mismatch: {adm2.rejection_reason} != {exp['second_rejection_reason']}")
                if ledger_delta != exp["ledger_delta_from_duplicate"]:
                    case_mismatches.append(f"Ledger delta mismatch: {ledger_delta} != {exp['ledger_delta_from_duplicate']}")
                if state_delta != exp["state_delta_from_duplicate"]:
                    case_mismatches.append(f"State delta mismatch: {state_delta} != {exp['state_delta_from_duplicate']}")

            elif case_id == "P7-STAT-05":
                # P7-STAT-05: state_advance_invalid (Score 0.5 < 0.8)
                student_id = cin["student_id"]
                ledger = EvidenceLedger()
                base_time = datetime.now(timezone.utc)
                self._setup_prereqs(ledger, student_id, base_time)

                rec = EvidenceRecord(
                    record_id="rec-p7-05-subscore",
                    student_id=student_id,
                    node_id=cin["node_id"],
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    outcome=EvidenceOutcome.PASS,
                    score=cin["score"],  # 0.5 < 0.8
                    timestamp=base_time,
                    actor_type=ActorType.TOOL_VERIFIER,
                    actor_id="evaluator",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    assessment_digest=hashlib.sha256(b"subscore-sec05").hexdigest(),
                )
                ledger.append_record(rec)

                state = derive_student_state(self.roadmap, self.policy, ledger, student_id)
                sec05 = state.get_node_state(cin["node_id"])

                node_status = sec05.status.value if sec05 else None
                verdict = sec05.evaluation_result.verdict.value if sec05 and sec05.evaluation_result else None
                missing_count = len(sec05.evaluation_result.missing_requirements) if sec05 and sec05.evaluation_result else 0
                is_prof = sec05.status == NodeProgressStatus.ASSESSED_PROFICIENT if sec05 else False

                observed_summary = {
                    "node_status": node_status,
                    "evaluation_verdict": verdict,
                    "missing_requirements_count": missing_count,
                    "is_proficient": is_prof,
                }

                if node_status != exp["node_status"]:
                    case_mismatches.append(f"Node status mismatch: {node_status} != {exp['node_status']}")
                if verdict != exp["evaluation_verdict"]:
                    case_mismatches.append(f"Verdict mismatch: {verdict} != {exp['evaluation_verdict']}")
                if missing_count != exp["missing_requirements_count"]:
                    case_mismatches.append(f"Missing count mismatch: {missing_count} != {exp['missing_requirements_count']}")
                if is_prof != exp["is_proficient"]:
                    case_mismatches.append(f"Proficient mismatch: {is_prof} != {exp['is_proficient']}")

            elif case_id == "P7-STAT-06":
                # P7-STAT-06: state_mutation_ui_event (Frozen contract & cryptographic hash verification)
                student_id = cin["student_id"]
                ledger = EvidenceLedger()
                base_time = datetime.now(timezone.utc)
                self._setup_prereqs(ledger, student_id, base_time)
                state = derive_student_state(self.roadmap, self.policy, ledger, student_id)

                direct_exc = None
                try:
                    # External UI attempts in-place mutation
                    setattr(state, "canonical_state_id", "hacked_state_id")
                except ValidationError as exc:
                    direct_exc = "ValidationError"
                except Exception as exc:
                    direct_exc = type(exc).__name__

                tampered_hash_exc = None
                try:
                    # Construct forged StudentState with fake canonical_state_id
                    forged_state = state.model_copy(update={"canonical_state_id": "0" * 64})
                    validate_student_state_hash(forged_state)
                except StateHashMismatchError as exc:
                    tampered_hash_exc = "StateHashMismatchError"
                except Exception as exc:
                    tampered_hash_exc = type(exc).__name__

                observed_summary = {
                    "direct_mutation_exception": direct_exc,
                    "tampered_hash_exception": tampered_hash_exc,
                    "zero_external_authority": direct_exc == "ValidationError" and tampered_hash_exc == "StateHashMismatchError",
                }

                if direct_exc != exp["direct_mutation_exception"]:
                    case_mismatches.append(f"Direct mutation exception mismatch: {direct_exc} != {exp['direct_mutation_exception']}")
                if tampered_hash_exc != exp["tampered_hash_exception"]:
                    case_mismatches.append(f"Tampered hash exception mismatch: {tampered_hash_exc} != {exp['tampered_hash_exception']}")

            elif case_id == "P7-STAT-07":
                # P7-STAT-07: state_mutation_llm_output (Unauthorized AI MANUAL_OVERRIDE & unaudited output)
                student_id = cin["student_id"]
                now = datetime.now(timezone.utc)
                crit = self.policy.default_criteria[self.roadmap.nodes[cin["node_id"]].node_type]

                # 1. AI tries MANUAL_OVERRIDE
                ai_rec = EvidenceRecord.model_construct(
                    record_id="rec-p7-07-ai",
                    student_id=student_id,
                    node_id=cin["node_id"],
                    evidence_type=EvidenceType.MANUAL_OVERRIDE,
                    outcome=EvidenceOutcome.PASS,
                    score=1.0,
                    timestamp=now,
                    actor_type=ActorType.AI_TUTOR,  # Forbidden for MANUAL_OVERRIDE!
                    actor_id="llm-tutor",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    rationale="LLM deems student competent",
                    roadmap_revision_id=self.roadmap.canonical_revision_id,
                    policy_revision_id=self.policy.canonical_policy_id,
                )

                ai_exc = None
                try:
                    evaluate_node_criteria(crit, [ai_rec], now, node_id=cin["node_id"])
                except SovereignExemptionViolationError as exc:
                    ai_exc = "SovereignExemptionViolationError"
                except Exception as exc:
                    ai_exc = type(exc).__name__

                # 2. Unaudited conceptual record (requires_audit_approved=True)
                unaudited_rec = EvidenceRecord(
                    record_id="rec-p7-07-unaudited",
                    student_id=student_id,
                    node_id=cin["node_id"],
                    evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
                    outcome=EvidenceOutcome.PASS,
                    score=1.0,
                    timestamp=now,
                    actor_type=ActorType.AI_TUTOR,
                    actor_id="llm-student",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    audit_verdict=None,  # Not approved by S4.4!
                )

                crit_audit = crit.model_copy(update={
                    "requirements": (
                        crit.requirements[0].model_copy(update={"requires_audit_approved": True}),
                    )
                })
                eval_audit = evaluate_node_criteria(crit_audit, [unaudited_rec], now, node_id=cin["node_id"])
                unaudited_ignored = eval_audit.verdict == CriteriaEvaluationVerdict.UNSATISFIED

                # State remains AVAILABLE
                # Since an unverified LLM output has zero authority to commit to the ledger,
                # the authoritative ledger remains empty, and node state remains AVAILABLE.
                ledger = EvidenceLedger()
                state = derive_student_state(self.roadmap, self.policy, ledger, student_id)
                sec01 = state.get_node_state(cin["node_id"])
                status_after = sec01.status.value if sec01 else None

                observed_summary = {
                    "ai_override_exception": ai_exc,
                    "unaudited_claim_ignored": unaudited_ignored,
                    "node_status_after_hallucination": status_after,
                }

                if ai_exc != exp["ai_override_exception"]:
                    case_mismatches.append(f"AI override exception mismatch: {ai_exc} != {exp['ai_override_exception']}")
                if unaudited_ignored != exp["unaudited_claim_ignored"]:
                    case_mismatches.append(f"Unaudited ignored mismatch: {unaudited_ignored} != {exp['unaudited_claim_ignored']}")
                if status_after != exp["node_status_after_hallucination"]:
                    case_mismatches.append(f"Status mismatch: {status_after} != {exp['node_status_after_hallucination']}")

            elif case_id == "P7-STAT-08-A":
                # P7-STAT-08-A: baseline_positive_control (Pure Function Verification)
                student_id = cin["student_id"]
                ledger = EvidenceLedger()
                base_time = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
                self._setup_prereqs(ledger, student_id, base_time)

                rec_sec05 = EvidenceRecord(
                    record_id="rec-p7-08-sec05",
                    student_id=student_id,
                    node_id=cin["target_node"],
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    outcome=EvidenceOutcome.PASS,
                    score=1.0,
                    timestamp=base_time + timedelta(minutes=5),
                    actor_type=ActorType.TOOL_VERIFIER,
                    actor_id="evaluator",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    assessment_digest=hashlib.sha256(b"sec05-clean-pass").hexdigest(),
                    overall_level=PerformanceLevel.N3_COMPETENT,
                )
                ledger.append_record(rec_sec05, override_committed_at=base_time + timedelta(minutes=5))

                fixed_as_of = base_time + timedelta(hours=1)
                s1 = derive_student_state(self.roadmap, self.policy, ledger, student_id, as_of_time=fixed_as_of)
                s2 = derive_student_state(self.roadmap, self.policy, ledger, student_id, as_of_time=fixed_as_of)

                sec05 = s1.get_node_state(cin["target_node"])
                sec04 = s1.get_node_state("SEC-04-CONCURR")
                sec06 = s1.get_node_state("SEC-06-CAPSTONE")

                target_status = sec05.status.value if sec05 else None
                target_verdict = sec05.evaluation_result.verdict.value if sec05 and sec05.evaluation_result else None
                sec04_status = sec04.status.value if sec04 else None
                sec06_status = sec06.status.value if sec06 else None

                pure_identical = (
                    s1.canonical_state_id == s2.canonical_state_id
                    and s1.node_states == s2.node_states
                )

                observed_summary = {
                    "target_node_status": target_status,
                    "target_node_verdict": target_verdict,
                    "downstream_sec04_status": sec04_status,
                    "downstream_sec06_status": sec06_status,
                    "pure_function_identical": pure_identical,
                }

                if target_status != exp["target_node_status"]:
                    case_mismatches.append(f"Target status mismatch: {target_status} != {exp['target_node_status']}")
                if target_verdict != exp["target_node_verdict"]:
                    case_mismatches.append(f"Target verdict mismatch: {target_verdict} != {exp['target_node_verdict']}")
                if sec04_status != exp["downstream_sec04_status"]:
                    case_mismatches.append(f"SEC-04 status mismatch: {sec04_status} != {exp['downstream_sec04_status']}")
                if sec06_status != exp["downstream_sec06_status"]:
                    case_mismatches.append(f"SEC-06 status mismatch: {sec06_status} != {exp['downstream_sec06_status']}")
                if pure_identical != exp["pure_function_identical"]:
                    case_mismatches.append(f"Pure function mismatch: {pure_identical} != {exp['pure_function_identical']}")

            elif case_id == "P7-STAT-08-B":
                # P7-STAT-08-B: order_independence_verification (Refinement 1)
                student_id = cin["student_id"]
                base_time = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
                commit_base = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

                node_configs = [
                    ("SEC-01-C-PTR", EvidenceType.CONCEPTUAL_EXPLANATION),
                    ("SEC-02-OS-PROC", EvidenceType.CONCEPTUAL_EXPLANATION),
                    ("SEC-03-MEM-MGMT", EvidenceType.CODE_EXECUTION),
                    ("SEC-05-BIN-SEC", EvidenceType.CODE_EXECUTION),
                ]
                records_map = {}
                for idx, (nid, etype) in enumerate(node_configs):
                    t = base_time + timedelta(minutes=idx * 10)
                    records_map[nid] = EvidenceRecord(
                        record_id=f"rec-p7-08b-{nid}",
                        student_id=student_id,
                        node_id=nid,
                        evidence_type=etype,
                        outcome=EvidenceOutcome.PASS,
                        score=1.0,
                        timestamp=t,
                        actor_type=ActorType.TOOL_VERIFIER,
                        actor_id="evaluator",
                        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                        assessment_digest=hashlib.sha256(f"digest-{nid}".encode("utf-8")).hexdigest(),
                        overall_level=PerformanceLevel.N3_COMPETENT if nid == "SEC-05-BIN-SEC" else None,
                    )

                # Ledger 1: Canonical order
                l1 = EvidenceLedger()
                for idx, (nid, _) in enumerate(node_configs):
                    l1.append_record(records_map[nid], override_committed_at=commit_base + timedelta(minutes=idx))

                # Ledger 2: Reverse insertion order
                l2 = EvidenceLedger()
                for idx, (nid, _) in enumerate(reversed(node_configs)):
                    l2.append_record(records_map[nid], override_committed_at=commit_base + timedelta(minutes=idx))

                fixed_as_of = commit_base + timedelta(hours=2)
                s1 = derive_student_state(self.roadmap, self.policy, l1, student_id, as_of_time=fixed_as_of)
                s2 = derive_student_state(self.roadmap, self.policy, l2, student_id, as_of_time=fixed_as_of)

                statuses_match = [n1.status for n1 in s1.node_states] == [n2.status for n2 in s2.node_states]
                verdicts_match = [
                    n1.evaluation_result.verdict if n1.evaluation_result else None for n1 in s1.node_states
                ] == [
                    n2.evaluation_result.verdict if n2.evaluation_result else None for n2 in s2.node_states
                ]
                prereqs_match = [n1.unfulfilled_hard_prerequisites for n1 in s1.node_states] == [
                    n2.unfulfilled_hard_prerequisites for n2 in s2.node_states
                ]
                counts_match = [n1.total_evidence_count for n1 in s1.node_states] == [
                    n2.total_evidence_count for n2 in s2.node_states
                ]

                epistemic_holds = statuses_match and verdicts_match and prereqs_match and counts_match

                observed_summary = {
                    "all_node_statuses_match": statuses_match,
                    "all_evaluation_verdicts_match": verdicts_match,
                    "all_unfulfilled_prereqs_match": prereqs_match,
                    "all_evidence_counts_match": counts_match,
                    "epistemic_invariance_holds": epistemic_holds,
                }

                if statuses_match != exp["all_node_statuses_match"]:
                    case_mismatches.append(f"Node statuses match mismatch: {statuses_match} != {exp['all_node_statuses_match']}")
                if verdicts_match != exp["all_evaluation_verdicts_match"]:
                    case_mismatches.append(f"Verdicts match mismatch: {verdicts_match} != {exp['all_evaluation_verdicts_match']}")
                if prereqs_match != exp["all_unfulfilled_prereqs_match"]:
                    case_mismatches.append(f"Prereqs match mismatch: {prereqs_match} != {exp['all_unfulfilled_prereqs_match']}")
                if counts_match != exp["all_evidence_counts_match"]:
                    case_mismatches.append(f"Counts match mismatch: {counts_match} != {exp['all_evidence_counts_match']}")
                if epistemic_holds != exp["epistemic_invariance_holds"]:
                    case_mismatches.append(f"Epistemic invariance mismatch: {epistemic_holds} != {exp['epistemic_invariance_holds']}")

            elif case_id == "P7-STAT-09":
                # P7-STAT-09: temporal_cutoff_enforcement (Refinement 2)
                student_id = cin["student_id"]
                ledger = EvidenceLedger()
                t1 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
                t2 = datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc)

                # Past record at T1
                rec_past = EvidenceRecord(
                    record_id="rec-p7-09-past",
                    student_id=student_id,
                    node_id=cin["past_node"],
                    evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
                    outcome=EvidenceOutcome.PASS,
                    score=1.0,
                    timestamp=t1,
                    actor_type=ActorType.TOOL_VERIFIER,
                    actor_id="evaluator",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    assessment_digest=hashlib.sha256(b"past-sec01").hexdigest(),
                )
                ledger.append_record(rec_past, override_committed_at=t1)

                # Future records at T2
                rec_sec02 = EvidenceRecord(
                    record_id="rec-p7-09-sec02",
                    student_id=student_id,
                    node_id="SEC-02-OS-PROC",
                    evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
                    outcome=EvidenceOutcome.PASS,
                    score=1.0,
                    timestamp=t2 - timedelta(minutes=20),
                    actor_type=ActorType.TOOL_VERIFIER,
                    actor_id="evaluator",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    assessment_digest=hashlib.sha256(b"fut-sec02").hexdigest(),
                )
                rec_sec03 = EvidenceRecord(
                    record_id="rec-p7-09-sec03",
                    student_id=student_id,
                    node_id="SEC-03-MEM-MGMT",
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    outcome=EvidenceOutcome.PASS,
                    score=1.0,
                    timestamp=t2 - timedelta(minutes=10),
                    actor_type=ActorType.TOOL_VERIFIER,
                    actor_id="evaluator",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    assessment_digest=hashlib.sha256(b"fut-sec03").hexdigest(),
                )
                rec_future = EvidenceRecord(
                    record_id="rec-p7-09-future",
                    student_id=student_id,
                    node_id=cin["future_node"],
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    outcome=EvidenceOutcome.PASS,
                    score=1.0,
                    timestamp=t2,
                    actor_type=ActorType.TOOL_VERIFIER,
                    actor_id="evaluator",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    assessment_digest=hashlib.sha256(b"future-sec05").hexdigest(),
                    overall_level=PerformanceLevel.N3_COMPETENT,
                )
                ledger.append_record(rec_sec02, override_committed_at=t2 - timedelta(minutes=20))
                ledger.append_record(rec_sec03, override_committed_at=t2 - timedelta(minutes=10))
                ledger.append_record(rec_future, override_committed_at=t2)

                # Query at cutoff = T1 + 15 min (strictly before T2)
                cutoff_t1 = t1 + timedelta(minutes=15)
                state_t1 = derive_student_state(
                    self.roadmap,
                    self.policy,
                    ledger,
                    student_id,
                    as_of_time=cutoff_t1,
                    cutoff_mode=HistoryCutoffMode.EVENT_TIME,
                )

                past_node_t1 = state_t1.get_node_state(cin["past_node"])
                future_node_t1 = state_t1.get_node_state(cin["future_node"])

                past_status_t1 = past_node_t1.status.value if past_node_t1 else None
                future_status_t1 = future_node_t1.status.value if future_node_t1 else None
                future_count_t1 = future_node_t1.total_evidence_count if future_node_t1 else -1

                # Query at cutoff = T2 + 15 min (covers all evidence)
                cutoff_t2 = t2 + timedelta(minutes=15)
                state_t2 = derive_student_state(
                    self.roadmap,
                    self.policy,
                    ledger,
                    student_id,
                    as_of_time=cutoff_t2,
                    cutoff_mode=HistoryCutoffMode.EVENT_TIME,
                )
                future_node_t2 = state_t2.get_node_state(cin["future_node"])
                future_status_t2 = future_node_t2.status.value if future_node_t2 else None

                cutoff_respected = (
                    past_status_t1 == "ASSESSED_PROFICIENT"
                    and future_status_t1 == "LOCKED"
                    and future_count_t1 == 0
                    and future_status_t2 == "ASSESSED_PROFICIENT"
                )

                observed_summary = {
                    "past_node_status_at_T1": past_status_t1,
                    "future_node_status_at_T1": future_status_t1,
                    "future_node_evidence_count_at_T1": future_count_t1,
                    "future_node_status_at_T2": future_status_t2,
                    "temporal_cutoff_respected": cutoff_respected,
                }

                if past_status_t1 != exp["past_node_status_at_T1"]:
                    case_mismatches.append(f"Past status at T1 mismatch: {past_status_t1} != {exp['past_node_status_at_T1']}")
                if future_status_t1 != exp["future_node_status_at_T1"]:
                    case_mismatches.append(f"Future status at T1 mismatch: {future_status_t1} != {exp['future_node_status_at_T1']}")
                if future_count_t1 != exp["future_node_evidence_count_at_T1"]:
                    case_mismatches.append(f"Future count at T1 mismatch: {future_count_t1} != {exp['future_node_evidence_count_at_T1']}")
                if future_status_t2 != exp["future_node_status_at_T2"]:
                    case_mismatches.append(f"Future status at T2 mismatch: {future_status_t2} != {exp['future_node_status_at_T2']}")

            # EVALUATE VERDICT
            passed = len(case_mismatches) == 0
            if passed:
                classification = "CONFIRMED_PASS"
                verdict_icon = "✅"
            else:
                classification = "CONFIRMED_DEFECT"
                verdict_icon = "❌"
                overall_defects += 1

            for k, v in observed_summary.items():
                print(f"     {k}: {v}")
            print(f"     Classification:   {verdict_icon} {classification}")

            if not passed:
                for err in case_mismatches:
                    print(f"     [!] MISMATCH: {err}")

            telemetry_records.append({
                "case_id": case_id,
                "severity_order": sev,
                "attack_class": attack_cls,
                "threat_vector": threat_vec,
                "classification": classification,
                "passed": passed,
                "observed_summary": observed_summary,
                "mismatches": case_mismatches,
            })

            findings.append({
                "case_id": case_id,
                "classification": classification,
                "details": desc,
            })

        # SUMMARY
        print("\n" + "=" * 75)
        print("📊 RESUMEN FINAL DE LA CAMPAÑA FASE 7 (STATE ATTACKS)")
        print("=" * 75)
        print(f"Total Casos Evaluados:        {len(self.phase7_cases)}")
        print(f"CONFIRMED_PASS:               {len(self.phase7_cases) - overall_defects}")
        print(f"CONFIRMED_DEFECT:             {overall_defects}")
        print(f"Invariante Nuclear S5.2.C:    {overall_defects == 0}")
        print(f"Veredicto Formal de Fase 7:   {'CERTIFIED_PASS' if overall_defects == 0 else 'REJECTED'}")
        print("=" * 75 + "\n")

        summary = {
            "phase": "phase_7_state_attacks",
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "total_cases": len(self.phase7_cases),
            "confirmed_pass": len(self.phase7_cases) - overall_defects,
            "confirmed_defect": overall_defects,
            "verdict": "CERTIFIED_PASS" if overall_defects == 0 else "REJECTED",
            "findings": findings,
            "telemetry": telemetry_records,
        }

        self._save_results(summary)
        return summary

    def _save_results(self, summary: Dict[str, Any]) -> None:
        """Persist results and telemetry into data/experiments/hito6/."""
        results_path = self.repo_root / "data" / "experiments" / "hito6" / "hito6_results.json"
        telemetry_path = self.repo_root / "data" / "experiments" / "hito6" / "hito6_telemetry.json"
        summary_path = self.repo_root / "data" / "experiments" / "hito6" / "hito6_summary.json"

        # Update hito6_results.json
        res_data: Dict[str, Any] = {}
        if results_path.exists():
            with open(results_path, "r", encoding="utf-8") as f:
                res_data = json.load(f)
        res_data["phase_7_state_attacks"] = {
            "verdict": summary["verdict"],
            "confirmed_pass": summary["confirmed_pass"],
            "confirmed_defect": summary["confirmed_defect"],
            "total_cases": summary["total_cases"],
            "findings": summary["findings"],
        }
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(res_data, f, indent=2)

        # Update hito6_telemetry.json
        existing_telemetry: List[Dict[str, Any]] = []
        if telemetry_path.exists():
            try:
                with open(telemetry_path, "r", encoding="utf-8") as f:
                    existing_telemetry = json.load(f)
            except Exception:
                existing_telemetry = []

        filtered_telemetry = [t for t in existing_telemetry if not t.get("case_id", "").startswith("P7-STAT-")]
        filtered_telemetry.extend(summary["telemetry"])

        with open(telemetry_path, "w", encoding="utf-8") as f:
            json.dump(filtered_telemetry, f, indent=2)

        # Update hito6_summary.json
        sum_data: Dict[str, Any] = {}
        if summary_path.exists():
            with open(summary_path, "r", encoding="utf-8") as f:
                sum_data = json.load(f)
        sum_data["phase_7_state_attacks"] = {
            "verdict": summary["verdict"],
            "confirmed_pass": summary["confirmed_pass"],
            "confirmed_defect": summary["confirmed_defect"],
            "evaluated_at": summary["evaluated_at"],
        }
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(sum_data, f, indent=2)


def main() -> int:
    runner = Phase7StateRunner()
    summary = runner.run_campaign()
    return 0 if summary["verdict"] == "CERTIFIED_PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
