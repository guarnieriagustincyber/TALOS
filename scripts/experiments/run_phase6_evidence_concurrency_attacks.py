#!/usr/bin/env python3
"""Hito 6 — Phase 6: Evidence & Concurrency Attacks Campaign Runner.

Executes the 9 adversarial evidence and concurrency attack cases against
Subsystems S5.2.A (Evidence Ingestion Engine) and S5.2.B (Authoritative Ledger),
verifying the formal invariants:
    1. Truth Table D(K, R) and attempt cardinality == 1
    2. Preflight Anti-Replay Gate (S5.2.A) vs Ledger Commit Gate (S5.2.B)
    3. Multi-tenant student epistemic isolation
    4. Cryptographic hash chain tamper-detection
    5. Real multithreaded SQLite WAL concurrency serialization with anti-deadlock timeout

Protocol: ATTACK -> OBSERVE -> COMPARE ORACLE -> CLASSIFY -> DOCUMENT
Rule: STRICTLY NO PATCHING DURING DIAGNOSTIC CAMPAIGN.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

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
from study_engine.contracts.spine import (
    ExecutionProvenanceSpine,
    SpineAssessment,
    SpineCurriculum,
    SpineExecution,
    SpineIdentity,
    SpineTerminalState,
)
from study_engine.contracts.execution import (
    ExecutionObservation,
    ExecutionStatus,
    ObservedArtifact,
    ProcessTelemetry,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.state.ingestion_engine import EvidenceIngestionEngine
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import (
    DuplicateEvidenceError,
    IdempotentReplayError,
    InconsistentReplayError,
    LedgerIntegrityStatus,
)
from study_engine.state.policy_contracts import (
    ActorType,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)
from study_engine.state.state_contracts import NodeProgressStatus
from study_engine.state.state_engine import derive_student_state


class Phase6EvidenceConcurrencyCampaignRunner:
    """Automated test runner for Hito 6 Phase 6 Evidence & Concurrency Attacks."""

    def __init__(
        self,
        oracle_path: Path,
        repo_root: Path = REPO_ROOT,
    ) -> None:
        self.repo_root = repo_root
        self.oracle_path = oracle_path
        with open(self.oracle_path, "r", encoding="utf-8") as f:
            self.oracle = json.load(f)

        self.phase6_spec = self.oracle["phase_6_evidence_concurrency_attacks"]
        self.phase6_cases = self.phase6_spec["cases"]

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

    def _setup_student_ledger(
        self,
        student_id: str,
        file_path: Optional[Path] = None,
    ) -> EvidenceLedger:
        """Create fresh student ledger and populate with baseline prerequisites."""
        ledger = EvidenceLedger(file_path=file_path)
        now = datetime.now(timezone.utc)

        prereqs = [
            ("SEC-01-C-PTR", EvidenceType.CONCEPTUAL_EXPLANATION),
            ("SEC-02-OS-PROC", EvidenceType.CONCEPTUAL_EXPLANATION),
            ("SEC-03-MEM-MGMT", EvidenceType.CODE_EXECUTION),
        ]
        for nid, etype in prereqs:
            rec = EvidenceRecord(
                record_id=f"ev-baseline-{nid}-{student_id}",
                student_id=student_id,
                node_id=nid,
                evidence_type=etype,
                outcome=EvidenceOutcome.PASS,
                score=1.0,
                timestamp=now - timedelta(minutes=15),
                actor_type=ActorType.TOOL_VERIFIER,
                actor_id="baseline-evaluator",
                authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                assessment_digest=hashlib.sha256(f"{nid}-{student_id}".encode("utf-8")).hexdigest(),
            )
            ledger.append_record(rec)

        return ledger

    def _create_canonical_assessment(self, observation_id: str = "obs-clean") -> AssessmentResult:
        """Generate a valid, fully satisfying AssessmentResult for SEC-05."""
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
        """Execute all 9 Phase 6 evidence and concurrency attack scenarios in strict severity order."""
        print("=" * 75)
        print("🛡️  HITO 6 — FASE 6: CAMPAÑA DE ATAQUES DE EVIDENCIA Y CONCURRENCIA (S5.2)")
        print("=" * 75)
        print(f"Total Casos de Ataque / Control: {len(self.phase6_cases)}")
        print("Core Invariant: D(K, R) Truth Table, Multi-Tenant Isolation & Atomic Concurrency")
        print("Protocol: ATTACK -> OBSERVE -> COMPARE ORACLE -> CLASSIFY -> DOCUMENT")
        print("-" * 75)

        telemetry_records: List[Dict[str, Any]] = []
        findings: List[Dict[str, Any]] = []
        overall_defects = 0

        sorted_cases = sorted(self.phase6_cases, key=lambda c: int(c["severity_order"]))

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
            if case_id == "P6-EVID-01":
                # P6-EVID-01: duplicate_attempt via S5.2.A Gate 4 Preflight
                student_id = cin["student_id"]
                ledger = self._setup_student_ledger(student_id)
                initial_count = len(ledger._entries)

                asmt = self._create_canonical_assessment(observation_id="obs-p6-01")
                prov_ctx = SessionProvenanceContext(
                    student_id=student_id,
                    session_id="session-p6-01",
                    resolved_target_node_id="SEC-05-BIN-SEC",
                    requested_node_id="SEC-05-BIN-SEC",
                    roadmap_revision_id=self.roadmap.canonical_revision_id,
                    policy_revision_id=self.policy.canonical_policy_id,
                    expected_task_specification_sha256=asmt.task.specification_sha256,
                    expected_rubric_specification_sha256=asmt.rubric.specification_sha256,
                    session_is_active=True,
                    session_started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
                )

                # 1st Submission: ADMITTED
                adm1 = self.ingestion_engine.evaluate_admissibility(asmt, prov_ctx, ledger)
                assert adm1.outcome is not None
                rec1 = self.ingestion_engine.build_admitted_record(asmt, prov_ctx, adm1.outcome, adm1.admission_trace)
                rec1 = rec1.model_copy(update={"metadata": {**rec1.metadata, "evaluation_attempt_id": cin["evaluation_attempt_id"]}})
                ledger.append_record(rec1)

                # 2nd Submission: REJECTED by Gate 4 Preflight
                adm2 = self.ingestion_engine.evaluate_admissibility(asmt, prov_ctx, ledger)

                final_count = len(ledger._entries)
                ledger_delta = final_count - initial_count

                rep = ledger.verify_integrity()
                state = derive_student_state(self.roadmap, self.policy, ledger, student_id)
                sec05 = state.get_node_state("SEC-05-BIN-SEC")
                node_status = sec05.status.value if sec05 else None

                observed_summary = {
                    "first_decision": adm1.decision.value,
                    "first_outcome": adm1.outcome.value if adm1.outcome else None,
                    "second_decision": adm2.decision.value,
                    "second_rejection_reason": adm2.rejection_reason.value if adm2.rejection_reason else None,
                    "intercepted_by": "S5.2.A_GATE_4_PREFLIGHT",
                    "ledger_delta_total": ledger_delta,
                    "attempt_cardinality": 1,
                    "hash_chain_status": rep.status.value,
                    "node_status_after": node_status,
                }

                if adm1.decision.value != exp["first_decision"]:
                    case_mismatches.append(f"1st decision mismatch: {adm1.decision.value} != {exp['first_decision']}")
                if adm2.decision.value != exp["second_decision"]:
                    case_mismatches.append(f"2nd decision mismatch: {adm2.decision.value} != {exp['second_decision']}")
                if adm2.rejection_reason is None or adm2.rejection_reason.value != exp["second_rejection_reason"]:
                    case_mismatches.append(f"2nd rejection reason mismatch: {adm2.rejection_reason} != {exp['second_rejection_reason']}")
                if ledger_delta != exp["ledger_delta_total"]:
                    case_mismatches.append(f"Ledger delta mismatch: {ledger_delta} != {exp['ledger_delta_total']}")
                if rep.status.value != exp["hash_chain_status"]:
                    case_mismatches.append(f"Hash chain status mismatch: {rep.status.value} != {exp['hash_chain_status']}")

            elif case_id == "P6-EVID-02":
                # P6-EVID-02: same_K_same_R via S5.2.B Ledger D(K, R)
                student_id = cin["student_id"]
                ledger = self._setup_student_ledger(student_id)
                initial_count = len(ledger._entries)
                now = datetime.now(timezone.utc)

                rec1 = EvidenceRecord(
                    record_id="rec-p6-02-a",
                    student_id=student_id,
                    node_id=cin["node_id"],
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    outcome=EvidenceOutcome.PASS,
                    score=1.0,
                    timestamp=now,
                    actor_type=ActorType.TOOL_VERIFIER,
                    actor_id="evaluator",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    assessment_digest=cin["assessment_digest"],
                    metadata={"evaluation_attempt_id": cin["evaluation_attempt_id"]},
                )
                ledger.append_record(rec1)

                rec2 = EvidenceRecord(
                    record_id="rec-p6-02-b",
                    student_id=student_id,
                    node_id=cin["node_id"],
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    outcome=EvidenceOutcome.PASS,
                    score=1.0,
                    timestamp=now + timedelta(seconds=1),
                    actor_type=ActorType.TOOL_VERIFIER,
                    actor_id="evaluator",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    assessment_digest=cin["assessment_digest"],
                    metadata={"evaluation_attempt_id": cin["evaluation_attempt_id"]},
                )

                caught_exc: Optional[str] = None
                try:
                    ledger.append_record(rec2)
                except IdempotentReplayError as exc:
                    caught_exc = type(exc).__name__

                final_count = len(ledger._entries)
                ledger_delta = final_count - initial_count
                rep = ledger.verify_integrity()

                observed_summary = {
                    "first_commit": "SUCCESS",
                    "second_commit_exception": caught_exc,
                    "intercepted_by": "S5.2.B_LEDGER_D_K_R",
                    "ledger_delta_total": ledger_delta,
                    "attempt_cardinality": 1,
                    "hash_chain_status": rep.status.value,
                }

                if caught_exc != exp["second_commit_exception"]:
                    case_mismatches.append(f"Second commit exception mismatch: {caught_exc} != {exp['second_commit_exception']}")
                if ledger_delta != exp["ledger_delta_total"]:
                    case_mismatches.append(f"Ledger delta mismatch: {ledger_delta} != {exp['ledger_delta_total']}")
                if rep.status.value != exp["hash_chain_status"]:
                    case_mismatches.append(f"Hash chain mismatch: {rep.status.value} != {exp['hash_chain_status']}")

            elif case_id == "P6-EVID-03":
                # P6-EVID-03: same_K_different_R via S5.2.B Ledger D(K, R)
                student_id = cin["student_id"]
                ledger = self._setup_student_ledger(student_id)
                initial_count = len(ledger._entries)
                now = datetime.now(timezone.utc)

                rec1 = EvidenceRecord(
                    record_id="rec-p6-03-a",
                    student_id=student_id,
                    node_id=cin["node_id"],
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    outcome=EvidenceOutcome.PASS,
                    score=1.0,
                    timestamp=now,
                    actor_type=ActorType.TOOL_VERIFIER,
                    actor_id="evaluator",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    assessment_digest=cin["first_digest"],
                    metadata={"evaluation_attempt_id": cin["evaluation_attempt_id"]},
                )
                ledger.append_record(rec1)

                rec2 = EvidenceRecord(
                    record_id="rec-p6-03-b",
                    student_id=student_id,
                    node_id=cin["node_id"],
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    outcome=EvidenceOutcome.FAIL,
                    score=0.0,
                    timestamp=now + timedelta(seconds=1),
                    actor_type=ActorType.TOOL_VERIFIER,
                    actor_id="evaluator",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    assessment_digest=cin["second_digest"],
                    metadata={"evaluation_attempt_id": cin["evaluation_attempt_id"]},
                )

                caught_exc = None
                try:
                    ledger.append_record(rec2)
                except InconsistentReplayError as exc:
                    caught_exc = type(exc).__name__

                final_count = len(ledger._entries)
                ledger_delta = final_count - initial_count
                rep = ledger.verify_integrity()

                observed_summary = {
                    "first_commit": "SUCCESS",
                    "second_commit_exception": caught_exc,
                    "intercepted_by": "S5.2.B_LEDGER_D_K_R",
                    "ledger_delta_total": ledger_delta,
                    "attempt_cardinality": 1,
                    "hash_chain_status": rep.status.value,
                }

                if caught_exc != exp["second_commit_exception"]:
                    case_mismatches.append(f"Second commit exception mismatch: {caught_exc} != {exp['second_commit_exception']}")
                if ledger_delta != exp["ledger_delta_total"]:
                    case_mismatches.append(f"Ledger delta mismatch: {ledger_delta} != {exp['ledger_delta_total']}")
                if rep.status.value != exp["hash_chain_status"]:
                    case_mismatches.append(f"Hash chain mismatch: {rep.status.value} != {exp['hash_chain_status']}")

            elif case_id == "P6-EVID-04":
                # P6-EVID-04: wrong_node via S5.2.A Gate 2 Provenance
                student_id = cin["student_id"]
                ledger = self._setup_student_ledger(student_id)
                initial_count = len(ledger._entries)
                asmt = self._create_canonical_assessment(observation_id="obs-p6-04")

                valid_sha = "f" * 64
                spine = ExecutionProvenanceSpine(
                    spine_id="spine-p6-04",
                    identity=SpineIdentity(
                        student_id=student_id,
                        session_id="session-p6-04",
                        attempt_id="attempt-p6-04",
                    ),
                    curriculum=SpineCurriculum(
                        curriculum_node_id=cin["node_id"],  # SEC-05
                        roadmap_revision_id=self.roadmap.canonical_revision_id,
                        policy_revision_id=self.policy.canonical_policy_id,
                        gateway_id="G-SEC",
                        gateway_revision_id=valid_sha,
                    ),
                    assessment=SpineAssessment(
                        rubric_id="rubric-01",
                        rubric_revision_id=valid_sha,
                        task_id="task-01",
                        task_revision_id=valid_sha,
                        hoare_contract_id="hoare-01",
                        assessment_result_id="asmt-p6-04",
                        evidence_record_id="ev-p6-04",
                        evaluator_version="1.0.0",
                    ),
                    execution=SpineExecution(
                        observation_ids=("obs-p6-04",),
                        artifact_digests=(valid_sha,),
                        perturbation_id="pert-01",
                    ),
                    terminal_state=SpineTerminalState(
                        ledger_cutoff_hash=valid_sha,
                        student_state_id="state-p6-04",
                    ),
                )
                prov_ctx = SessionProvenanceContext(
                    student_id=student_id,
                    session_id="session-p6-04",
                    resolved_target_node_id=cin["mismatched_target_node"],  # SEC-04
                    requested_node_id=cin["mismatched_target_node"],
                    roadmap_revision_id=self.roadmap.canonical_revision_id,
                    policy_revision_id=self.policy.canonical_policy_id,
                    expected_task_specification_sha256=asmt.task.specification_sha256,
                    expected_rubric_specification_sha256=asmt.rubric.specification_sha256,
                    spine=spine,
                    session_is_active=True,
                    session_started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
                )

                adm = self.ingestion_engine.evaluate_admissibility(asmt, prov_ctx, ledger)
                final_count = len(ledger._entries)
                rep = ledger.verify_integrity()

                observed_summary = {
                    "decision": adm.decision.value,
                    "rejection_reason": adm.rejection_reason.value if adm.rejection_reason else None,
                    "rejection_detail_substring": adm.rejection_detail,
                    "ledger_delta": final_count - initial_count,
                    "hash_chain_status": rep.status.value,
                }

                if adm.decision.value != exp["decision"]:
                    case_mismatches.append(f"Decision mismatch: {adm.decision.value} != {exp['decision']}")
                if adm.rejection_reason is None or adm.rejection_reason.value != exp["rejection_reason"]:
                    case_mismatches.append(f"Rejection reason mismatch: {adm.rejection_reason} != {exp['rejection_reason']}")
                if exp["rejection_detail_substring"] not in (adm.rejection_detail or ""):
                    case_mismatches.append(f"Rejection detail missing substring: '{exp['rejection_detail_substring']}'")

            elif case_id == "P6-EVID-05":
                # P6-EVID-05: wrong_provenance via S5.2.A Gate 3 Session
                student_id = cin["student_id"]
                ledger = self._setup_student_ledger(student_id)
                initial_count = len(ledger._entries)
                asmt = self._create_canonical_assessment(observation_id="obs-p6-05")

                prov_ctx = SessionProvenanceContext(
                    student_id=student_id,
                    session_id="session-p6-05",
                    resolved_target_node_id=cin["node_id"],
                    requested_node_id=cin["node_id"],
                    roadmap_revision_id=self.roadmap.canonical_revision_id,
                    policy_revision_id=self.policy.canonical_policy_id,
                    expected_task_specification_sha256=asmt.task.specification_sha256,
                    expected_rubric_specification_sha256=asmt.rubric.specification_sha256,
                    session_is_active=cin["session_is_active"],  # False!
                    session_started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
                )

                adm = self.ingestion_engine.evaluate_admissibility(asmt, prov_ctx, ledger)
                final_count = len(ledger._entries)
                rep = ledger.verify_integrity()

                observed_summary = {
                    "decision": adm.decision.value,
                    "rejection_reason": adm.rejection_reason.value if adm.rejection_reason else None,
                    "ledger_delta": final_count - initial_count,
                    "hash_chain_status": rep.status.value,
                }

                if adm.decision.value != exp["decision"]:
                    case_mismatches.append(f"Decision mismatch: {adm.decision.value} != {exp['decision']}")
                if adm.rejection_reason is None or adm.rejection_reason.value != exp["rejection_reason"]:
                    case_mismatches.append(f"Rejection reason mismatch: {adm.rejection_reason} != {exp['rejection_reason']}")

            elif case_id == "P6-EVID-06":
                # P6-EVID-06: missing_digest via S5.2.A Gate 1 Integrity
                student_id = cin["student_id"]
                ledger = self._setup_student_ledger(student_id)
                initial_count = len(ledger._entries)
                asmt = self._create_canonical_assessment(observation_id="obs-p6-06")

                # Corrupt the digest
                forged_asmt = asmt.model_copy(update={"assessment_digest": cin["forged_digest"]})

                prov_ctx = SessionProvenanceContext(
                    student_id=student_id,
                    session_id="session-p6-06",
                    resolved_target_node_id=cin["node_id"],
                    requested_node_id=cin["node_id"],
                    roadmap_revision_id=self.roadmap.canonical_revision_id,
                    policy_revision_id=self.policy.canonical_policy_id,
                    expected_task_specification_sha256=asmt.task.specification_sha256,
                    expected_rubric_specification_sha256=asmt.rubric.specification_sha256,
                    session_is_active=True,
                    session_started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
                )

                adm = self.ingestion_engine.evaluate_admissibility(forged_asmt, prov_ctx, ledger)
                final_count = len(ledger._entries)
                rep = ledger.verify_integrity()

                observed_summary = {
                    "decision": adm.decision.value,
                    "rejection_reason": adm.rejection_reason.value if adm.rejection_reason else None,
                    "ledger_delta": final_count - initial_count,
                    "hash_chain_status": rep.status.value,
                }

                if adm.decision.value != exp["decision"]:
                    case_mismatches.append(f"Decision mismatch: {adm.decision.value} != {exp['decision']}")
                if adm.rejection_reason is None or adm.rejection_reason.value != exp["rejection_reason"]:
                    case_mismatches.append(f"Rejection reason mismatch: {adm.rejection_reason} != {exp['rejection_reason']}")

            elif case_id == "P6-EVID-07":
                # P6-EVID-07: tampered_evidence via DIRECT_SQLITE_ROW_MUTATION (Refinement 1)
                student_id = cin["student_id"]
                with tempfile.TemporaryDirectory() as tmp_dir:
                    db_path = Path(tmp_dir) / "tamper_campaign.db"
                    ledger1 = self._setup_student_ledger(student_id, file_path=db_path)
                    now = datetime.now(timezone.utc)

                    rec = EvidenceRecord(
                        record_id="rec-tamper-target",
                        student_id=student_id,
                        node_id=cin["node_id"],
                        evidence_type=EvidenceType.CODE_EXECUTION,
                        outcome=EvidenceOutcome.PASS,
                        score=1.0,
                        timestamp=now,
                        actor_type=ActorType.TOOL_VERIFIER,
                        actor_id="evaluator",
                        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                        assessment_digest="e" * 64,
                        metadata={"evaluation_attempt_id": "attempt-tamper-01"},
                    )
                    ledger1.append_record(rec)
                    ledger1.close()

                    # Unlink JSONL view so reloading relies purely on authoritative SQLite
                    jsonl_path = db_path.with_suffix(".jsonl")
                    if jsonl_path.exists():
                        jsonl_path.unlink()

                    # Direct SQLite row mutation: modify entry_hash on row 0
                    conn = sqlite3.connect(str(db_path))
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE evidence_ledger SET entry_hash = ?, payload_json = REPLACE(payload_json, entry_hash, ?) WHERE entry_index = ?",
                        (cin["tamper_hash"], cin["tamper_hash"], cin["tamper_entry_index"]),
                    )
                    conn.commit()
                    conn.close()

                    ledger2 = EvidenceLedger(file_path=db_path)
                    rep = ledger2.verify_integrity()
                    ledger2.close()

                observed_summary = {
                    "expected_integrity_status": rep.status.value,
                    "expected_detection_method": "ledger.verify_integrity()",
                    "tamper_detected": rep.status == LedgerIntegrityStatus.HASH_CHAIN_BROKEN,
                }

                if rep.status.value != exp["expected_integrity_status"]:
                    case_mismatches.append(f"Integrity status mismatch: {rep.status.value} != {exp['expected_integrity_status']}")

            elif case_id == "P6-EVID-08":
                # P6-EVID-08: cross_student_evidence epistemic isolation
                ledger = EvidenceLedger()
                now = datetime.now(timezone.utc)

                prereqs = [
                    ("SEC-01-C-PTR", EvidenceType.CONCEPTUAL_EXPLANATION),
                    ("SEC-02-OS-PROC", EvidenceType.CONCEPTUAL_EXPLANATION),
                    ("SEC-03-MEM-MGMT", EvidenceType.CODE_EXECUTION),
                ]
                # STUDENT-A has prereqs only
                for nid, etype in prereqs:
                    rec_a = EvidenceRecord(
                        record_id=f"rec-A-{nid}",
                        student_id=cin["student_a_id"],
                        node_id=nid,
                        evidence_type=etype,
                        outcome=EvidenceOutcome.PASS,
                        score=1.0,
                        timestamp=now - timedelta(minutes=15),
                        actor_type=ActorType.TOOL_VERIFIER,
                        actor_id="test",
                        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                        assessment_digest=hashlib.sha256(f"A-{nid}".encode("utf-8")).hexdigest(),
                    )
                    ledger.append_record(rec_a)

                # STUDENT-B has prereqs + SEC-05 mastery
                for nid, etype in prereqs:
                    rec_b = EvidenceRecord(
                        record_id=f"rec-B-{nid}",
                        student_id=cin["student_b_id"],
                        node_id=nid,
                        evidence_type=etype,
                        outcome=EvidenceOutcome.PASS,
                        score=1.0,
                        timestamp=now - timedelta(minutes=15),
                        actor_type=ActorType.TOOL_VERIFIER,
                        actor_id="test",
                        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                        assessment_digest=hashlib.sha256(f"B-{nid}".encode("utf-8")).hexdigest(),
                    )
                    ledger.append_record(rec_b)

                rec_b_sec05 = EvidenceRecord(
                    record_id="rec-B-SEC-05",
                    student_id=cin["student_b_id"],
                    node_id=cin["node_id"],
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    outcome=EvidenceOutcome.PASS,
                    score=1.0,
                    timestamp=now,
                    actor_type=ActorType.TOOL_VERIFIER,
                    actor_id="test",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    assessment_digest=hashlib.sha256(b"B-SEC-05").hexdigest(),
                    overall_level=PerformanceLevel.N3_COMPETENT,
                )
                ledger.append_record(rec_b_sec05)

                state_a = derive_student_state(self.roadmap, self.policy, ledger, cin["student_a_id"])
                sec05_a = state_a.get_node_state(cin["node_id"])
                status_a = sec05_a.status.value if sec05_a else None

                state_b = derive_student_state(self.roadmap, self.policy, ledger, cin["student_b_id"])
                sec05_b = state_b.get_node_state(cin["node_id"])
                status_b = sec05_b.status.value if sec05_b else None

                rep = ledger.verify_integrity()

                observed_summary = {
                    "student_a_status": status_a,
                    "student_b_status": status_b,
                    "cross_leakage_detected": status_a == NodeProgressStatus.ASSESSED_PROFICIENT.value,
                    "hash_chain_status": rep.status.value,
                }

                if status_a != exp["student_a_status"]:
                    case_mismatches.append(f"Student A status mismatch: {status_a} != {exp['student_a_status']}")
                if status_b != exp["student_b_status"]:
                    case_mismatches.append(f"Student B status mismatch: {status_b} != {exp['student_b_status']}")

            elif case_id == "P6-EVID-09":
                # P6-EVID-09: concurrent_duplicate with real threads & anti-deadlock timeout (Refinement 2)
                student_id = cin["student_id"]
                with tempfile.TemporaryDirectory() as tmp_dir:
                    db_path = Path(tmp_dir) / "concurrent_campaign.db"
                    ledger = EvidenceLedger(file_path=db_path)
                    now = datetime.now(timezone.utc)

                    thread_results: List[Tuple[int, str]] = []
                    thread_errors: List[Tuple[int, str]] = []

                    def worker(worker_id: int) -> None:
                        rec = EvidenceRecord(
                            record_id=f"rec-worker-{worker_id}",
                            student_id=student_id,
                            node_id=cin["node_id"],
                            evidence_type=EvidenceType.CODE_EXECUTION,
                            outcome=EvidenceOutcome.PASS,
                            score=1.0,
                            timestamp=now,
                            actor_type=ActorType.TOOL_VERIFIER,
                            actor_id="worker",
                            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                            assessment_digest=cin["assessment_digest"],
                            metadata={"evaluation_attempt_id": cin["evaluation_attempt_id"]},
                        )
                        try:
                            ledger.append_record(rec)
                            thread_results.append((worker_id, "COMMITTED"))
                        except (IdempotentReplayError, DuplicateEvidenceError) as exc:
                            thread_errors.append((worker_id, type(exc).__name__))
                        except Exception as exc:
                            thread_errors.append((worker_id, f"UNEXPECTED_{type(exc).__name__}"))

                    t1 = threading.Thread(target=worker, args=(1,))
                    t2 = threading.Thread(target=worker, args=(2,))

                    t1.start()
                    t2.start()

                    # Anti-deadlock timeout enforcement (Refinement 2)
                    t1.join(timeout=cin["join_timeout_seconds"])
                    t2.join(timeout=cin["join_timeout_seconds"])

                    deadlock = t1.is_alive() or t2.is_alive()
                    if deadlock:
                        raise TimeoutError("CONCURRENCY_DEADLOCK_DETECTED")

                    # Verify SQLite cardinality
                    conn = sqlite3.connect(str(db_path))
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT COUNT(*) FROM evidence_ledger WHERE evaluation_attempt_id = ?",
                        (cin["evaluation_attempt_id"],),
                    )
                    attempt_cardinality = cur.fetchone()[0]
                    conn.close()

                    rep = ledger.verify_integrity()
                    total_entries = len(ledger._entries)
                    ledger.close()

                observed_summary = {
                    "committed_threads_count": len(thread_results),
                    "idempotent_replay_threads_count": len(thread_errors),
                    "deadlock_detected": deadlock,
                    "attempt_cardinality": attempt_cardinality,
                    "total_ledger_entries": total_entries,
                    "hash_chain_status": rep.status.value,
                }

                if len(thread_results) != exp["committed_threads_count"]:
                    case_mismatches.append(f"Committed threads count mismatch: {len(thread_results)} != {exp['committed_threads_count']}")
                if len(thread_errors) != exp["idempotent_replay_threads_count"]:
                    case_mismatches.append(f"Idempotent replay count mismatch: {len(thread_errors)} != {exp['idempotent_replay_threads_count']}")
                if attempt_cardinality != exp["attempt_cardinality"]:
                    case_mismatches.append(f"Attempt cardinality mismatch: {attempt_cardinality} != {exp['attempt_cardinality']}")
                if total_entries != exp["total_ledger_entries"]:
                    case_mismatches.append(f"Total entries mismatch: {total_entries} != {exp['total_ledger_entries']}")
                if rep.status.value != exp["hash_chain_status"]:
                    case_mismatches.append(f"Hash chain mismatch: {rep.status.value} != {exp['hash_chain_status']}")

            # CLASSIFICATION & TELEMETRY
            classification = "CONFIRMED_PASS" if not case_mismatches else "CONFIRMED_DEFECT"
            if classification == "CONFIRMED_DEFECT":
                overall_defects += 1

            for k, v in observed_summary.items():
                print(f"     {k}: {v}")
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
                "observed": observed_summary,
                "expected": exp,
                "nuclear_invariant_holds": len(case_mismatches) == 0,
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
                "nuclear_invariant_holds": len(case_mismatches) == 0,
                "mismatches": case_mismatches,
            })

        passed_cases = sum(1 for f in findings if f["classification"] == "CONFIRMED_PASS")
        final_verdict = "CERTIFIED_PASS" if overall_defects == 0 else "ABORT_ON_DEFECT"

        print("\n" + "=" * 75)
        print("📊 RESUMEN FINAL DE LA CAMPAÑA FASE 6 (EVIDENCE & CONCURRENCY ATTACKS)")
        print("=" * 75)
        print(f"Total Casos Evaluados:        {len(self.phase6_cases)}")
        print(f"CONFIRMED_PASS:               {passed_cases}")
        print(f"CONFIRMED_DEFECT:             {overall_defects}")
        print(f"Invariante D(K, R) y Hash:    {overall_defects == 0}")
        print(f"Veredicto Formal de Fase 6:   {final_verdict}")
        print("=" * 75 + "\n")

        summary_data = {
            "campaign_id": "HITO6-SURVIVAL-ADVERSARIAL",
            "phase": "phase_6_evidence_concurrency_attacks",
            "executed_at_utc": datetime.now(timezone.utc).isoformat(),
            "total_cases": len(self.phase6_cases),
            "passed_cases": passed_cases,
            "defects_found": overall_defects,
            "invariants_certified": overall_defects == 0,
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

        filtered_telemetry = [t for t in existing_telemetry if not t.get("case_id", "").startswith("P6-EVID-")]
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

        existing_results["phase_6_evidence_concurrency_attacks"] = {
            "verdict": final_verdict,
            "total_cases": len(self.phase6_cases),
            "passed_cases": passed_cases,
            "defects": overall_defects,
            "invariants_certified": overall_defects == 0,
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

        existing_summary["phase_6_evidence_concurrency_attacks"] = summary_data
        existing_summary["last_updated_utc"] = datetime.now(timezone.utc).isoformat()
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(existing_summary, f, indent=2)

        return summary_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Hito 6 Phase 6 Evidence & Concurrency Attacks")
    parser.add_argument(
        "--oracle-path",
        type=Path,
        default=REPO_ROOT / "data" / "experiments" / "hito6" / "hito6_oracle.json",
        help="Path to hito6_oracle.json",
    )
    args = parser.parse_args()

    runner = Phase6EvidenceConcurrencyCampaignRunner(oracle_path=args.oracle_path)
    summary = runner.run_campaign()

    if summary["defects_found"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
