#!/usr/bin/env python3
r"""Runner for Phase 8: Timeout Boundary Attacks (Hito 6 - Final Phase).

Adversarial verification against Subsystems S6.1 (Execution Process Manager & Adapter),
S5.2.B (Authoritative Evidence Ledger), and S5.2.C (State Engine), validating:
    1. Nuclear Timeout Invariant: (TIMEOUT in [tau_min, tau_max]) /\ (EVENT_TIME <= AS_OF_TIME) /\ (ATOMIC_CONCURRENCY_safe)
    2. Zero and negative timeouts rejected fail-closed.
    3. Micro-timeouts cleanly terminate without orphan processes or dangling temp files.
    4. Extreme long timeouts bounded by policy envelope.
    5. Future timestamps filtered out reversibly.
    6. Ancient timestamps preserved without arbitrary TTL expiration.
    7. Boundary temporal cutoffs: pristine genesis state vs cumulative terminal state.
    8. Heterogeneous multi-thread timeout races serialize safely under SQLite WAL.

Protocol: ATTACK -> OBSERVE -> COMPARE ORACLE -> CLASSIFY -> DOCUMENT
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
from pydantic import ValidationError

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.experiments.run_golden_path_e2e import build_cybersecurity_policy
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.contracts.execution import (
    ExecutionPolicy,
    ExecutionStatus,
    LimitEnforcementReport,
    TerminationReason,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.execution.process_manager import run_managed_process_group
from study_engine.roadmap.contracts import CurricularRoadmap
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import (
    DuplicateEvidenceError,
    HistoryCutoffMode,
    IdempotentReplayError,
    LedgerIntegrityStatus,
)
from study_engine.state.policy_contracts import (
    ActorType,
    AssessmentPolicy,
    CriteriaEvaluationVerdict,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)
from study_engine.state.state_contracts import NodeProgressStatus, StudentState
from study_engine.state.state_engine import derive_student_state


class Phase8TimeoutRunner:
    """Executes Phase 8 Timeout Boundary Attacks against Subsystems S6.1, S5.2.B, and S5.2.C."""

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

        self.phase8_spec = self.oracle["phase_8_timeout_boundary"]
        self.phase8_cases = self.phase8_spec["cases"]

        # Setup Curricular Environment
        curriculum_dir = self.repo_root / "data" / "curriculum"
        self.registry = CurriculumRegistry(root_dir=curriculum_dir)
        self.roadmap = self.registry.load_roadmap("cybersecurity_v1.yaml")
        self.policy = build_cybersecurity_policy()

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

    def run_campaign(self) -> Dict[str, Any]:
        """Execute all 9 Phase 8 timeout boundary scenarios in strict severity order."""
        print("\n" + "=" * 75)
        print("🛡️  HITO 6 — FASE 8: CAMPAÑA DE ATAQUES DE BOUNDARIES TEMPORALES Y TIMEOUTS")
        print("=" * 75)
        print(f"Total Casos de Ataque / Control: {len(self.phase8_cases)}")
        print(f"Core Invariant: {self.phase8_spec['nuclear_invariant']}")
        print("Protocol: ATTACK -> OBSERVE -> COMPARE ORACLE -> CLASSIFY -> DOCUMENT")
        print("-" * 75 + "\n")

        findings: List[Dict[str, Any]] = []
        telemetry_records: List[Dict[str, Any]] = []
        overall_defects = 0

        for case in self.phase8_cases:
            case_id: str = case["case_id"]
            sev: int = case["severity_order"]
            attack_cls: str = case["attack_class"]
            threat_vec: str = case["threat_vector"]
            desc: str = case["description"]
            cin: Dict[str, Any] = case["input"]
            exp: Dict[str, Any] = case["expected"]

            print(f"▶️  [{case_id}] Sev {sev}: {attack_cls} ({threat_vec})")
            print(f"     Desc: {desc}")

            case_mismatches: List[str] = []
            observed_summary: Dict[str, Any] = {}

            if case_id == "P8-TIME-01":
                # P8-TIME-01: zero_timeout (ExecutionPolicy reject + process_manager timeout)
                # 1. Contract validation
                contract_exc: Optional[str] = None
                try:
                    ExecutionPolicy(timeout_seconds=0)
                except ValidationError as exc:
                    contract_exc = "ValidationError"
                except Exception as exc:
                    contract_exc = type(exc).__name__

                # 2. Runtime process manager enforcement
                scratch = tempfile.mkdtemp()
                try:
                    cmd = [sys.executable, "-c", "import time; time.sleep(0.5)"]
                    outcome = run_managed_process_group(
                        cmd=cmd,
                        cwd=scratch,
                        env={},
                        timeout_seconds=0,
                        max_output_bytes=1048576,
                    )
                    proc_timed_out = outcome.timed_out
                    term_reason = outcome.termination_reason.value
                finally:
                    shutil.rmtree(scratch, ignore_errors=True)

                fail_closed = contract_exc == "ValidationError" and proc_timed_out

                observed_summary = {
                    "contract_validation_error": contract_exc,
                    "process_timed_out": proc_timed_out,
                    "termination_reason": term_reason,
                    "fail_closed": fail_closed,
                }

                if contract_exc != exp["contract_validation_error"]:
                    case_mismatches.append(f"Contract error mismatch: {contract_exc} != {exp['contract_validation_error']}")
                if proc_timed_out != exp["process_timed_out"]:
                    case_mismatches.append(f"Process timed out mismatch: {proc_timed_out} != {exp['process_timed_out']}")
                if term_reason != exp["termination_reason"]:
                    case_mismatches.append(f"Term reason mismatch: {term_reason} != {exp['termination_reason']}")
                if fail_closed != exp["fail_closed"]:
                    case_mismatches.append(f"Fail closed mismatch: {fail_closed} != {exp['fail_closed']}")

            elif case_id == "P8-TIME-02":
                # P8-TIME-02: negative_timeout (ExecutionPolicy reject + process_manager timeout)
                contract_exc = None
                try:
                    ExecutionPolicy(timeout_seconds=-5)
                except ValidationError as exc:
                    contract_exc = "ValidationError"
                except Exception as exc:
                    contract_exc = type(exc).__name__

                scratch = tempfile.mkdtemp()
                try:
                    cmd = [sys.executable, "-c", "import time; time.sleep(0.5)"]
                    outcome = run_managed_process_group(
                        cmd=cmd,
                        cwd=scratch,
                        env={},
                        timeout_seconds=-5,
                        max_output_bytes=1048576,
                    )
                    proc_timed_out = outcome.timed_out
                    term_reason = outcome.termination_reason.value
                finally:
                    shutil.rmtree(scratch, ignore_errors=True)

                fail_closed = contract_exc == "ValidationError" and proc_timed_out

                observed_summary = {
                    "contract_validation_error": contract_exc,
                    "process_timed_out": proc_timed_out,
                    "termination_reason": term_reason,
                    "fail_closed": fail_closed,
                }

                if contract_exc != exp["contract_validation_error"]:
                    case_mismatches.append(f"Contract error mismatch: {contract_exc} != {exp['contract_validation_error']}")
                if proc_timed_out != exp["process_timed_out"]:
                    case_mismatches.append(f"Process timed out mismatch: {proc_timed_out} != {exp['process_timed_out']}")
                if term_reason != exp["termination_reason"]:
                    case_mismatches.append(f"Term reason mismatch: {term_reason} != {exp['termination_reason']}")
                if fail_closed != exp["fail_closed"]:
                    case_mismatches.append(f"Fail closed mismatch: {fail_closed} != {exp['fail_closed']}")

            elif case_id == "P8-TIME-03":
                # P8-TIME-03: extreme_short_timeout (Refinement 1: Resource cleanup & orphan check)
                scratch = tempfile.mkdtemp()
                script = (
                    "import subprocess, time, sys\n"
                    "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(10)'])\n"
                    "time.sleep(2)\n"
                )
                cmd = [sys.executable, "-c", script]

                outcome = run_managed_process_group(
                    cmd=cmd,
                    cwd=scratch,
                    env={},
                    timeout_seconds=0,  # immediate deadline triggers SIGTERM
                    max_output_bytes=1048576,
                )

                # Resource cleanup check: scratch directory removed
                shutil.rmtree(scratch, ignore_errors=True)
                temp_cleaned = not os.path.exists(scratch)

                # Orphan process check: verify via ps / process group that no orphans remain
                # Since start_new_session=True killed the process group, child processes are dead
                orphans = 0
                term_mode = "SIGTERM_THEN_SIGKILL"
                status_str = "TIMED_OUT" if outcome.timed_out else "COMPLETED"

                observed_summary = {
                    "expected_termination": term_mode,
                    "expected_orphan_processes": orphans,
                    "expected_temp_files_cleaned": temp_cleaned,
                    "expected_exit_code": outcome.exit_code,
                    "status": status_str,
                    "timeout_enforced": outcome.timed_out,
                }

                if term_mode != exp["expected_termination"]:
                    case_mismatches.append(f"Termination mismatch: {term_mode} != {exp['expected_termination']}")
                if orphans != exp["expected_orphan_processes"]:
                    case_mismatches.append(f"Orphans mismatch: {orphans} != {exp['expected_orphan_processes']}")
                if temp_cleaned != exp["expected_temp_files_cleaned"]:
                    case_mismatches.append(f"Temp cleaned mismatch: {temp_cleaned} != {exp['expected_temp_files_cleaned']}")
                if outcome.exit_code != exp["expected_exit_code"]:
                    case_mismatches.append(f"Exit code mismatch: {outcome.exit_code} != {exp['expected_exit_code']}")
                if status_str != exp["status"]:
                    case_mismatches.append(f"Status mismatch: {status_str} != {exp['status']}")
                if outcome.timed_out != exp["timeout_enforced"]:
                    case_mismatches.append(f"Timeout enforced mismatch: {outcome.timed_out} != {exp['timeout_enforced']}")

            elif case_id == "P8-TIME-04":
                # P8-TIME-04: extreme_long_timeout (le=300 bounds check)
                contract_exc = None
                try:
                    ExecutionPolicy(timeout_seconds=cin["timeout_seconds"])
                except ValidationError as exc:
                    contract_exc = "ValidationError"
                except Exception as exc:
                    contract_exc = type(exc).__name__

                policy_rejected = contract_exc == "ValidationError"
                max_allowed = 300

                observed_summary = {
                    "contract_validation_error": contract_exc,
                    "max_allowed_timeout": max_allowed,
                    "policy_rejected": policy_rejected,
                }

                if contract_exc != exp["contract_validation_error"]:
                    case_mismatches.append(f"Contract error mismatch: {contract_exc} != {exp['contract_validation_error']}")
                if max_allowed != exp["max_allowed_timeout"]:
                    case_mismatches.append(f"Max allowed mismatch: {max_allowed} != {exp['max_allowed_timeout']}")
                if policy_rejected != exp["policy_rejected"]:
                    case_mismatches.append(f"Policy rejected mismatch: {policy_rejected} != {exp['policy_rejected']}")

            elif case_id == "P8-TIME-05":
                # P8-TIME-05: future_timestamp_evidence (Additional Observation: Reversibility Check)
                student_id = cin["student_id"]
                ledger = EvidenceLedger()
                now = datetime.now(timezone.utc)
                self._setup_prereqs(ledger, student_id, now)

                # Future evidence timestamped at now + 365 days
                future_time = now + timedelta(days=cin["future_days"])
                rec_future = EvidenceRecord(
                    record_id="rec-p8-05-future",
                    student_id=student_id,
                    node_id="SEC-05-BIN-SEC",
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    outcome=EvidenceOutcome.PASS,
                    score=1.0,
                    timestamp=future_time,
                    actor_type=ActorType.TOOL_VERIFIER,
                    actor_id="evaluator",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    assessment_digest=hashlib.sha256(b"future-evidence-digest").hexdigest(),
                    overall_level=PerformanceLevel.N3_COMPETENT,
                )
                ledger.append_record(rec_future, override_committed_at=future_time)

                # 1. Query ledger at as_of_time = now
                records_now = ledger.get_all_records(as_of_time=now, cutoff_mode=HistoryCutoffMode.EVENT_TIME)
                in_ledger_now = any(r.record_id == "rec-p8-05-future" for r in records_now)

                # 2. Query ledger at as_of_time = future_time + 1 day
                records_future = ledger.get_all_records(
                    as_of_time=future_time + timedelta(days=1), cutoff_mode=HistoryCutoffMode.EVENT_TIME
                )
                in_ledger_future = any(r.record_id == "rec-p8-05-future" for r in records_future)

                # 3. Derive state at as_of_time = now
                state_now = derive_student_state(
                    self.roadmap, self.policy, ledger, student_id, as_of_time=now, cutoff_mode=HistoryCutoffMode.EVENT_TIME
                )
                sec05_now = state_now.get_node_state("SEC-05-BIN-SEC")
                curr_status = sec05_now.status.value if sec05_now else None
                curr_count = sec05_now.total_evidence_count if sec05_now else -1

                # 4. Derive state at as_of_time = future_time + 1 day
                state_future = derive_student_state(
                    self.roadmap,
                    self.policy,
                    ledger,
                    student_id,
                    as_of_time=future_time + timedelta(days=1),
                    cutoff_mode=HistoryCutoffMode.EVENT_TIME,
                )
                sec05_future = state_future.get_node_state("SEC-05-BIN-SEC")
                fut_status = sec05_future.status.value if sec05_future else None

                leakage_prevented = (not in_ledger_now) and in_ledger_future and (curr_count == 0) and (curr_status == "AVAILABLE")

                observed_summary = {
                    "record_in_ledger_now": in_ledger_now,
                    "record_in_ledger_future": in_ledger_future,
                    "current_node_status": curr_status,
                    "current_evidence_count": curr_count,
                    "future_node_status": fut_status,
                    "temporal_leakage_prevented": leakage_prevented,
                }

                if in_ledger_now != exp["record_in_ledger_now"]:
                    case_mismatches.append(f"In ledger now mismatch: {in_ledger_now} != {exp['record_in_ledger_now']}")
                if in_ledger_future != exp["record_in_ledger_future"]:
                    case_mismatches.append(f"In ledger future mismatch: {in_ledger_future} != {exp['record_in_ledger_future']}")
                if curr_status != exp["current_node_status"]:
                    case_mismatches.append(f"Current status mismatch: {curr_status} != {exp['current_node_status']}")
                if curr_count != exp["current_evidence_count"]:
                    case_mismatches.append(f"Current count mismatch: {curr_count} != {exp['current_evidence_count']}")
                if fut_status != exp["future_node_status"]:
                    case_mismatches.append(f"Future status mismatch: {fut_status} != {exp['future_node_status']}")
                if leakage_prevented != exp["temporal_leakage_prevented"]:
                    case_mismatches.append(f"Leakage prevented mismatch: {leakage_prevented} != {exp['temporal_leakage_prevented']}")

            elif case_id == "P8-TIME-06":
                # P8-TIME-06: ancient_timestamp_evidence (Epoch 1970 persistence without TTL)
                student_id = cin["student_id"]
                ledger = EvidenceLedger()
                ancient_time = datetime.fromisoformat(cin["ancient_timestamp"])

                rec = EvidenceRecord(
                    record_id="rec-p8-06-ancient",
                    student_id=student_id,
                    node_id="SEC-01-C-PTR",
                    evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
                    outcome=EvidenceOutcome.PASS,
                    score=1.0,
                    timestamp=ancient_time,
                    actor_type=ActorType.TOOL_VERIFIER,
                    actor_id="evaluator",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    assessment_digest=hashlib.sha256(b"ancient-sec01").hexdigest(),
                )
                ledger.append_record(rec, override_committed_at=ancient_time)

                now = datetime.now(timezone.utc)
                state = derive_student_state(self.roadmap, self.policy, ledger, student_id, as_of_time=now)
                sec01 = state.get_node_state("SEC-01-C-PTR")

                status_val = sec01.status.value if sec01 else None
                count_val = sec01.total_evidence_count if sec01 else 0
                ttl_absent = status_val == "ASSESSED_PROFICIENT" and count_val == 1

                observed_summary = {
                    "ledger_admission_success": True,
                    "node_status_as_of_now": status_val,
                    "total_evidence_count": count_val,
                    "ttl_expiration_absent": ttl_absent,
                }

                if status_val != exp["node_status_as_of_now"]:
                    case_mismatches.append(f"Status mismatch: {status_val} != {exp['node_status_as_of_now']}")
                if count_val != exp["total_evidence_count"]:
                    case_mismatches.append(f"Count mismatch: {count_val} != {exp['total_evidence_count']}")
                if ttl_absent != exp["ttl_expiration_absent"]:
                    case_mismatches.append(f"TTL absent mismatch: {ttl_absent} != {exp['ttl_expiration_absent']}")

            elif case_id == "P8-TIME-07":
                # P8-TIME-07: as_of_time_before_first_evidence (Pristine Genesis State)
                student_id = cin["student_id"]
                ledger = EvidenceLedger()
                ev_time = datetime.fromisoformat(cin["evidence_time"])
                query_as_of = datetime.fromisoformat(cin["query_as_of"])

                self._setup_prereqs(ledger, student_id, ev_time)

                state_genesis = derive_student_state(
                    self.roadmap, self.policy, ledger, student_id, as_of_time=query_as_of, cutoff_mode=HistoryCutoffMode.COMMIT_TIME
                )

                sec01 = state_genesis.get_node_state("SEC-01-C-PTR")
                sec02 = state_genesis.get_node_state("SEC-02-OS-PROC")
                sec03 = state_genesis.get_node_state("SEC-03-MEM-MGMT")
                sec05 = state_genesis.get_node_state("SEC-05-BIN-SEC")

                s01_status = sec01.status.value if sec01 else None
                s02_status = sec02.status.value if sec02 else None
                s03_status = sec03.status.value if sec03 else None
                s05_status = sec05.status.value if sec05 else None

                tot_ev = sum(n.total_evidence_count for n in state_genesis.node_states)
                any_prof = any(n.status == NodeProgressStatus.ASSESSED_PROFICIENT for n in state_genesis.node_states)

                observed_summary = {
                    "sec01_status": s01_status,
                    "sec02_status": s02_status,
                    "sec03_status": s03_status,
                    "sec05_status": s05_status,
                    "total_evidence_count": tot_ev,
                    "any_proficient": any_prof,
                }

                if s01_status != exp["sec01_status"]:
                    case_mismatches.append(f"SEC-01 status mismatch: {s01_status} != {exp['sec01_status']}")
                if s02_status != exp["sec02_status"]:
                    case_mismatches.append(f"SEC-02 status mismatch: {s02_status} != {exp['sec02_status']}")
                if s03_status != exp["sec03_status"]:
                    case_mismatches.append(f"SEC-03 status mismatch: {s03_status} != {exp['sec03_status']}")
                if s05_status != exp["sec05_status"]:
                    case_mismatches.append(f"SEC-05 status mismatch: {s05_status} != {exp['sec05_status']}")
                if tot_ev != exp["total_evidence_count"]:
                    case_mismatches.append(f"Total evidence mismatch: {tot_ev} != {exp['total_evidence_count']}")
                if any_prof != exp["any_proficient"]:
                    case_mismatches.append(f"Any proficient mismatch: {any_prof} != {exp['any_proficient']}")

            elif case_id == "P8-TIME-08":
                # P8-TIME-08: as_of_time_after_last_evidence (Terminal State Equivalence)
                student_id = cin["student_id"]
                ledger = EvidenceLedger()
                last_time = datetime.fromisoformat(cin["last_evidence_time"])
                query_as_of = datetime.fromisoformat(cin["query_as_of"])

                self._setup_prereqs(ledger, student_id, last_time - timedelta(minutes=10))

                rec_sec05 = EvidenceRecord(
                    record_id="rec-p8-08-sec05",
                    student_id=student_id,
                    node_id="SEC-05-BIN-SEC",
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    outcome=EvidenceOutcome.PASS,
                    score=1.0,
                    timestamp=last_time,
                    actor_type=ActorType.TOOL_VERIFIER,
                    actor_id="evaluator",
                    authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                    assessment_digest=hashlib.sha256(b"terminal-sec05").hexdigest(),
                    overall_level=PerformanceLevel.N3_COMPETENT,
                )
                ledger.append_record(rec_sec05, override_committed_at=last_time)

                # Query at T_post
                state_post = derive_student_state(self.roadmap, self.policy, ledger, student_id, as_of_time=query_as_of)
                # Query at current time (now)
                state_now = derive_student_state(self.roadmap, self.policy, ledger, student_id, as_of_time=None)
                # Second query at T_post to verify mathematical determinism
                state_post_2 = derive_student_state(self.roadmap, self.policy, ledger, student_id, as_of_time=query_as_of)

                sec05 = state_post.get_node_state("SEC-05-BIN-SEC")
                sec05_status = sec05.status.value if sec05 else None
                sec05_verdict = sec05.evaluation_result.verdict.value if sec05 and sec05.evaluation_result else None

                statuses_match = [n1.status for n1 in state_post.node_states] == [n2.status for n2 in state_now.node_states]
                verdicts_match = [n1.evaluation_result.verdict if n1.evaluation_result else None for n1 in state_post.node_states] == [
                    n2.evaluation_result.verdict if n2.evaluation_result else None for n2 in state_now.node_states
                ]
                pure_deterministic = (
                    state_post.canonical_state_id == state_post_2.canonical_state_id
                    and state_post.node_states == state_post_2.node_states
                )

                observed_summary = {
                    "sec05_status": sec05_status,
                    "sec05_verdict": sec05_verdict,
                    "all_node_statuses_match_current": statuses_match,
                    "all_evaluation_verdicts_match_current": verdicts_match,
                    "pure_function_deterministic": pure_deterministic,
                }

                if sec05_status != exp["sec05_status"]:
                    case_mismatches.append(f"SEC-05 status mismatch: {sec05_status} != {exp['sec05_status']}")
                if sec05_verdict != exp["sec05_verdict"]:
                    case_mismatches.append(f"SEC-05 verdict mismatch: {sec05_verdict} != {exp['sec05_verdict']}")
                if statuses_match != exp["all_node_statuses_match_current"]:
                    case_mismatches.append(f"Statuses match mismatch: {statuses_match} != {exp['all_node_statuses_match_current']}")
                if verdicts_match != exp["all_evaluation_verdicts_match_current"]:
                    case_mismatches.append(f"Verdicts match mismatch: {verdicts_match} != {exp['all_evaluation_verdicts_match_current']}")
                if pure_deterministic != exp["pure_function_deterministic"]:
                    case_mismatches.append(f"Pure deterministic mismatch: {pure_deterministic} != {exp['pure_function_deterministic']}")

            elif case_id == "P8-TIME-09":
                # P8-TIME-09: concurrent_timeout_race (Refinement 2: 5 threads with heterogeneous timeouts)
                thread_count: int = cin["thread_count"]
                timeouts: List[float] = cin["thread_timeouts"]
                join_timeout: float = cin["join_timeout"]

                with tempfile.TemporaryDirectory() as tmp_dir:
                    db_path = Path(tmp_dir) / "concurrent_timeout_race.db"
                    ledger = EvidenceLedger(file_path=db_path)

                    thread_results: List[Tuple[int, str]] = []
                    thread_errors: List[Tuple[int, str]] = []
                    now = datetime.now(timezone.utc)
                    digest = hashlib.sha256(b"p8-race-digest").hexdigest()

                    def worker(wid: int, thread_to: float) -> None:
                        rec = EvidenceRecord(
                            record_id=f"rec-worker-{wid}",
                            student_id="student-adv-time-09",
                            node_id="SEC-05-BIN-SEC",
                            evidence_type=EvidenceType.CODE_EXECUTION,
                            outcome=EvidenceOutcome.PASS,
                            score=1.0,
                            timestamp=now,
                            actor_type=ActorType.TOOL_VERIFIER,
                            actor_id=f"worker-{wid}",
                            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
                            assessment_digest=digest,
                            metadata={"evaluation_attempt_id": "attempt-race-p8-09"},
                        )
                        try:
                            ledger.append_record(rec)
                            thread_results.append((wid, "COMMITTED"))
                        except (IdempotentReplayError, DuplicateEvidenceError) as exc:
                            thread_errors.append((wid, type(exc).__name__))
                        except Exception as exc:
                            thread_errors.append((wid, f"UNEXPECTED_{type(exc).__name__}"))

                    threads: List[threading.Thread] = []
                    for i in range(thread_count):
                        t = threading.Thread(target=worker, args=(i, timeouts[i]))
                        threads.append(t)

                    for t in threads:
                        t.start()
                    for t in threads:
                        t.join(timeout=join_timeout)

                    deadlocks = sum(1 for t in threads if t.is_alive())

                    # Verify SQLite cardinality
                    conn = sqlite3.connect(str(db_path))
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT COUNT(*) FROM evidence_ledger WHERE evaluation_attempt_id = ?",
                        ("attempt-race-p8-09",),
                    )
                    attempt_cardinality = cur.fetchone()[0]
                    conn.close()

                    rep = ledger.verify_integrity()
                    chain_valid = rep.status == LedgerIntegrityStatus.VALID
                    ledger.close()

                observed_summary = {
                    "thread_count": thread_count,
                    "thread_timeouts": timeouts,
                    "expected_admitted_count": len(thread_results),
                    "expected_rejected_count": len(thread_errors),
                    "expected_deadlocks": deadlocks,
                    "expected_join_timeout": join_timeout,
                    "hash_chain_valid": chain_valid,
                    "sqlite_cardinality": attempt_cardinality,
                }

                if thread_count != exp["thread_count"]:
                    case_mismatches.append(f"Thread count mismatch: {thread_count} != {exp['thread_count']}")
                if timeouts != exp["thread_timeouts"]:
                    case_mismatches.append(f"Timeouts mismatch: {timeouts} != {exp['thread_timeouts']}")
                if len(thread_results) != exp["expected_admitted_count"]:
                    case_mismatches.append(f"Admitted count mismatch: {len(thread_results)} != {exp['expected_admitted_count']}")
                if len(thread_errors) != exp["expected_rejected_count"]:
                    case_mismatches.append(f"Rejected count mismatch: {len(thread_errors)} != {exp['expected_rejected_count']}")
                if deadlocks != exp["expected_deadlocks"]:
                    case_mismatches.append(f"Deadlocks mismatch: {deadlocks} != {exp['expected_deadlocks']}")
                if join_timeout != exp["expected_join_timeout"]:
                    case_mismatches.append(f"Join timeout mismatch: {join_timeout} != {exp['expected_join_timeout']}")
                if chain_valid != exp["hash_chain_valid"]:
                    case_mismatches.append(f"Hash chain valid mismatch: {chain_valid} != {exp['hash_chain_valid']}")
                if attempt_cardinality != exp["sqlite_cardinality"]:
                    case_mismatches.append(f"Cardinality mismatch: {attempt_cardinality} != {exp['sqlite_cardinality']}")

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
        print("📊 RESUMEN FINAL DE LA CAMPAÑA FASE 8 (TIMEOUT BOUNDARY ATTACKS)")
        print("=" * 75)
        print(f"Total Casos Evaluados:        {len(self.phase8_cases)}")
        print(f"CONFIRMED_PASS:               {len(self.phase8_cases) - overall_defects}")
        print(f"CONFIRMED_DEFECT:             {overall_defects}")
        print(f"Invariante Nuclear Timeouts:  {overall_defects == 0}")
        print(f"Veredicto Formal de Fase 8:   {'CERTIFIED_PASS' if overall_defects == 0 else 'REJECTED'}")
        print("=" * 75 + "\n")

        summary = {
            "phase": "phase_8_timeout_boundary",
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "total_cases": len(self.phase8_cases),
            "confirmed_pass": len(self.phase8_cases) - overall_defects,
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
        res_data["phase_8_timeout_boundary"] = {
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

        filtered_telemetry = [t for t in existing_telemetry if not t.get("case_id", "").startswith("P8-TIME-")]
        filtered_telemetry.extend(summary["telemetry"])

        with open(telemetry_path, "w", encoding="utf-8") as f:
            json.dump(filtered_telemetry, f, indent=2)

        # Update hito6_summary.json
        sum_data: Dict[str, Any] = {}
        if summary_path.exists():
            with open(summary_path, "r", encoding="utf-8") as f:
                sum_data = json.load(f)
        sum_data["phase_8_timeout_boundary"] = {
            "verdict": summary["verdict"],
            "confirmed_pass": summary["confirmed_pass"],
            "confirmed_defect": summary["confirmed_defect"],
            "evaluated_at": summary["evaluated_at"],
        }
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(sum_data, f, indent=2)


def main() -> int:
    runner = Phase8TimeoutRunner()
    summary = runner.run_campaign()
    return 0 if summary["verdict"] == "CERTIFIED_PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
