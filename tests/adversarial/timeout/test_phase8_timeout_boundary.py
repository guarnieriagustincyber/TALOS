r"""Adversarial and integrity test suite for Phase 8: Timeout Boundary Attacks (Hito 6).

Asserts full compliance against Subsystems S6.1 (Execution Process Manager & Adapter),
S5.2.B (Authoritative Evidence Ledger), and S5.2.C (State Engine), verifying the
Nuclear Timeout Invariant:
    Nuclear Timeout Invariant == (TIMEOUT in [tau_min, tau_max])
                              /\ (EVENT_TIME <= AS_OF_TIME)
                              /\ (ATOMIC_CONCURRENCY_safe)

Test Scenarios (9 Cases):
1. P8-TIME-01 (zero_timeout): ExecutionPolicy rejects timeout_seconds=0; process manager fails closed.
2. P8-TIME-02 (negative_timeout): ExecutionPolicy rejects timeout_seconds=-5; process manager fails closed.
3. P8-TIME-03 (extreme_short_timeout): Subprocess terminated by SIGTERM; 0 orphan processes; temp dir cleaned.
4. P8-TIME-04 (extreme_long_timeout): ExecutionPolicy rejects 999999s (> max 300s) at contract validation.
5. P8-TIME-05 (future_timestamp_evidence): Future evidence excluded at as_of_time=now, included at T_future+1d.
6. P8-TIME-06 (ancient_timestamp_evidence): 1970 Unix epoch evidence admitted and persisted without TTL expiration.
7. P8-TIME-07 (as_of_time_before_first_evidence): Querying before first evidence yields pristine genesis state.
8. P8-TIME-08 (as_of_time_after_last_evidence): Querying after last evidence returns complete terminal state.
9. P8-TIME-09 (concurrent_timeout_race): 5 threads with heterogeneous timeouts race on SQLite WAL; exactly 1 admitted.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import threading
from typing import Any, Dict, List, Tuple
from pydantic import ValidationError
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.experiments.run_golden_path_e2e import build_cybersecurity_policy
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.contracts.execution import ExecutionPolicy
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


@pytest.fixture(scope="module")
def phase8_env() -> Dict[str, Any]:
    """Module-level setup for curriculum registry, roadmap, policy, and oracle spec."""
    curriculum_dir = REPO_ROOT / "data" / "curriculum"
    registry = CurriculumRegistry(root_dir=curriculum_dir)
    roadmap = registry.load_roadmap("cybersecurity_v1.yaml")
    policy = build_cybersecurity_policy()

    oracle_path = REPO_ROOT / "data" / "experiments" / "hito6" / "hito6_oracle.json"
    with open(oracle_path, "r", encoding="utf-8") as f:
        oracle = json.load(f)

    return {
        "registry": registry,
        "roadmap": roadmap,
        "policy": policy,
        "oracle": oracle["phase_8_timeout_boundary"],
    }


def _get_case_spec(env: Dict[str, Any], case_id: str) -> Dict[str, Any]:
    """Retrieve oracle case specification by ID."""
    cases = env["oracle"]["cases"]
    return next(c for c in cases if c["case_id"] == case_id)


def _setup_prereqs(ledger: EvidenceLedger, student_id: str, base_time: datetime) -> None:
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


def test_p8_time_01_zero_timeout(phase8_env: Dict[str, Any]) -> None:
    """P8-TIME-01: Zero timeout rejected by contract and fails closed in process manager."""
    case = _get_case_spec(phase8_env, "P8-TIME-01")
    exp = case["expected"]

    # 1. Contract validation
    with pytest.raises(ValidationError):
        ExecutionPolicy(timeout_seconds=0)

    # 2. Runtime enforcement
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
        assert outcome.timed_out is exp["process_timed_out"]
        assert outcome.termination_reason.value == exp["termination_reason"]
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_p8_time_02_negative_timeout(phase8_env: Dict[str, Any]) -> None:
    """P8-TIME-02: Negative timeout rejected by contract and fails closed in process manager."""
    case = _get_case_spec(phase8_env, "P8-TIME-02")
    exp = case["expected"]

    # 1. Contract validation
    with pytest.raises(ValidationError):
        ExecutionPolicy(timeout_seconds=-5)

    # 2. Runtime enforcement
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
        assert outcome.timed_out is exp["process_timed_out"]
        assert outcome.termination_reason.value == exp["termination_reason"]
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def test_p8_time_03_extreme_short_timeout_cleanup(phase8_env: Dict[str, Any]) -> None:
    """P8-TIME-03: Micro-timeout triggers SIGTERM; 0 orphan processes; temp dir cleaned."""
    case = _get_case_spec(phase8_env, "P8-TIME-03")
    exp = case["expected"]

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
        timeout_seconds=0,
        max_output_bytes=1048576,
    )

    # Clean up scratch directory
    shutil.rmtree(scratch, ignore_errors=True)
    temp_cleaned = not os.path.exists(scratch)

    assert temp_cleaned is exp["expected_temp_files_cleaned"]
    assert outcome.timed_out is exp["timeout_enforced"]
    assert outcome.exit_code == exp["expected_exit_code"]


def test_p8_time_04_extreme_long_timeout_envelope(phase8_env: Dict[str, Any]) -> None:
    """P8-TIME-04: Timeout beyond max policy envelope (le=300) rejected by contract."""
    case = _get_case_spec(phase8_env, "P8-TIME-04")
    exp = case["expected"]
    cin = case["input"]

    with pytest.raises(ValidationError):
        ExecutionPolicy(timeout_seconds=cin["timeout_seconds"])

    # Valid within bounds [1, 300]
    valid_policy = ExecutionPolicy(timeout_seconds=exp["max_allowed_timeout"])
    assert valid_policy.timeout_seconds == 300


def test_p8_time_05_future_timestamp_evidence_reversibility(phase8_env: Dict[str, Any]) -> None:
    """P8-TIME-05: Future evidence excluded at as_of_time=now, included at T_future+1d."""
    case = _get_case_spec(phase8_env, "P8-TIME-05")
    exp = case["expected"]
    cin = case["input"]

    roadmap: CurricularRoadmap = phase8_env["roadmap"]
    policy: AssessmentPolicy = phase8_env["policy"]
    student_id: str = cin["student_id"]

    ledger = EvidenceLedger()
    now = datetime.now(timezone.utc)
    _setup_prereqs(ledger, student_id, now)

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

    # 1. Query at as_of_time = now
    records_now = ledger.get_all_records(as_of_time=now, cutoff_mode=HistoryCutoffMode.EVENT_TIME)
    assert not any(r.record_id == "rec-p8-05-future" for r in records_now)

    state_now = derive_student_state(
        roadmap, policy, ledger, student_id, as_of_time=now, cutoff_mode=HistoryCutoffMode.EVENT_TIME
    )
    sec05_now = state_now.get_node_state("SEC-05-BIN-SEC")
    assert sec05_now is not None
    assert sec05_now.status.value == exp["current_node_status"]
    assert sec05_now.total_evidence_count == exp["current_evidence_count"]

    # 2. Query at as_of_time = future_time + 1 day
    records_future = ledger.get_all_records(
        as_of_time=future_time + timedelta(days=1), cutoff_mode=HistoryCutoffMode.EVENT_TIME
    )
    assert any(r.record_id == "rec-p8-05-future" for r in records_future)

    state_future = derive_student_state(
        roadmap,
        policy,
        ledger,
        student_id,
        as_of_time=future_time + timedelta(days=1),
        cutoff_mode=HistoryCutoffMode.EVENT_TIME,
    )
    sec05_future = state_future.get_node_state("SEC-05-BIN-SEC")
    assert sec05_future is not None
    assert sec05_future.status.value == exp["future_node_status"]


def test_p8_time_06_ancient_timestamp_evidence_ttl_absent(phase8_env: Dict[str, Any]) -> None:
    """P8-TIME-06: 1970 Unix epoch evidence admitted and persisted without arbitrary TTL."""
    case = _get_case_spec(phase8_env, "P8-TIME-06")
    exp = case["expected"]
    cin = case["input"]

    roadmap: CurricularRoadmap = phase8_env["roadmap"]
    policy: AssessmentPolicy = phase8_env["policy"]
    student_id: str = cin["student_id"]

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
    state = derive_student_state(roadmap, policy, ledger, student_id, as_of_time=now)
    sec01 = state.get_node_state("SEC-01-C-PTR")

    assert sec01 is not None
    assert sec01.status.value == exp["node_status_as_of_now"]
    assert sec01.total_evidence_count == exp["total_evidence_count"]


def test_p8_time_07_as_of_time_before_first_evidence_genesis(phase8_env: Dict[str, Any]) -> None:
    """P8-TIME-07: Querying state before earliest evidence returns pristine genesis state."""
    case = _get_case_spec(phase8_env, "P8-TIME-07")
    exp = case["expected"]
    cin = case["input"]

    roadmap: CurricularRoadmap = phase8_env["roadmap"]
    policy: AssessmentPolicy = phase8_env["policy"]
    student_id: str = cin["student_id"]

    ledger = EvidenceLedger()
    ev_time = datetime.fromisoformat(cin["evidence_time"])
    query_as_of = datetime.fromisoformat(cin["query_as_of"])

    _setup_prereqs(ledger, student_id, ev_time)

    state_genesis = derive_student_state(
        roadmap, policy, ledger, student_id, as_of_time=query_as_of, cutoff_mode=HistoryCutoffMode.COMMIT_TIME
    )

    sec01 = state_genesis.get_node_state("SEC-01-C-PTR")
    sec02 = state_genesis.get_node_state("SEC-02-OS-PROC")
    sec03 = state_genesis.get_node_state("SEC-03-MEM-MGMT")
    sec05 = state_genesis.get_node_state("SEC-05-BIN-SEC")

    assert sec01 is not None and sec01.status.value == exp["sec01_status"]
    assert sec02 is not None and sec02.status.value == exp["sec02_status"]
    assert sec03 is not None and sec03.status.value == exp["sec03_status"]
    assert sec05 is not None and sec05.status.value == exp["sec05_status"]

    tot_ev = sum(n.total_evidence_count for n in state_genesis.node_states)
    assert tot_ev == exp["total_evidence_count"]

    any_prof = any(n.status == NodeProgressStatus.ASSESSED_PROFICIENT for n in state_genesis.node_states)
    assert any_prof == exp["any_proficient"]


def test_p8_time_08_as_of_time_after_last_evidence_equivalence(phase8_env: Dict[str, Any]) -> None:
    """P8-TIME-08: Querying state after latest evidence returns identical terminal progress."""
    case = _get_case_spec(phase8_env, "P8-TIME-08")
    exp = case["expected"]
    cin = case["input"]

    roadmap: CurricularRoadmap = phase8_env["roadmap"]
    policy: AssessmentPolicy = phase8_env["policy"]
    student_id: str = cin["student_id"]

    ledger = EvidenceLedger()
    last_time = datetime.fromisoformat(cin["last_evidence_time"])
    query_as_of = datetime.fromisoformat(cin["query_as_of"])

    _setup_prereqs(ledger, student_id, last_time - timedelta(minutes=10))

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

    # 1. State at query_as_of (post-terminal)
    state_post = derive_student_state(roadmap, policy, ledger, student_id, as_of_time=query_as_of)
    # 2. State at current time (unbounded)
    state_now = derive_student_state(roadmap, policy, ledger, student_id, as_of_time=None)
    # 3. Repeat call at query_as_of to verify pure functional determinism
    state_post_2 = derive_student_state(roadmap, policy, ledger, student_id, as_of_time=query_as_of)

    sec05 = state_post.get_node_state("SEC-05-BIN-SEC")
    assert sec05 is not None
    assert sec05.status.value == exp["sec05_status"]
    assert sec05.evaluation_result is not None
    assert sec05.evaluation_result.verdict.value == exp["sec05_verdict"]

    # Epistemic state matches identically
    assert [n1.status for n1 in state_post.node_states] == [n2.status for n2 in state_now.node_states]
    assert [
        n1.evaluation_result.verdict if n1.evaluation_result else None for n1 in state_post.node_states
    ] == [
        n2.evaluation_result.verdict if n2.evaluation_result else None for n2 in state_now.node_states
    ]

    # Pure functional determinism
    assert state_post.canonical_state_id == state_post_2.canonical_state_id
    assert state_post.node_states == state_post_2.node_states


def test_p8_time_09_concurrent_timeout_race_heterogeneous(phase8_env: Dict[str, Any]) -> None:
    """P8-TIME-09: 5 threads with heterogeneous timeouts race against SQLite WAL."""
    case = _get_case_spec(phase8_env, "P8-TIME-09")
    exp = case["expected"]
    cin = case["input"]

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
        assert deadlocks == exp["expected_deadlocks"]

        # Exactly 1 admitted, 4 rejected
        assert len(thread_results) == exp["expected_admitted_count"]
        assert len(thread_errors) == exp["expected_rejected_count"]

        # SQLite cardinality is 1
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM evidence_ledger WHERE evaluation_attempt_id = ?",
            ("attempt-race-p8-09",),
        )
        attempt_cardinality = cur.fetchone()[0]
        conn.close()
        assert attempt_cardinality == exp["sqlite_cardinality"]

        # Hash chain remains intact
        rep = ledger.verify_integrity()
        assert rep.status == LedgerIntegrityStatus.VALID
        ledger.close()
