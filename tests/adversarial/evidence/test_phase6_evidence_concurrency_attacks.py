"""Adversarial and security test suite for Phase 6: Evidence & Concurrency Attacks (Hito 6).

Asserts full compliance against Subsystems S5.2.A (Evidence Ingestion Engine)
and S5.2.B (Authoritative Evidence Ledger), verifying the nuclear invariants:
    1. Truth Table D(K, R) enforcement (idempotent replay vs inconsistent replay).
    2. Cryptographic Hash Chaining (tamper detection via verify_integrity).
    3. Epistemic Student Isolation (multi-tenant state isolation without cross-leakage).
    4. Atomic Concurrency Serialization (SQLite BEGIN IMMEDIATE serializes concurrent workers).

Tests:
1. P6-EVID-01 (duplicate_attempt): Preflight Gate 4 rejects duplicate assessment with DUPLICATE_ASSESSMENT_REPLAY.
2. P6-EVID-02 (same_K_same_R): Ledger D(K, R) raises IdempotentReplayError; cardinality=1.
3. P6-EVID-03 (same_K_different_R): Ledger D(K, R) raises InconsistentReplayError; transaction rolled back.
4. P6-EVID-04 (wrong_node): Gate 2 provenance detects curricular node mismatch fail-closed.
5. P6-EVID-05 (wrong_provenance): Gate 3 rejects inactive or expired session fail-closed.
6. P6-EVID-06 (missing_digest): Gate 1 rejects forged or corrupt SHA-256 digest fail-closed.
7. P6-EVID-07 (tampered_evidence): Direct SQLite row mutation breaks cryptographic hash chain.
8. P6-EVID-08 (cross_student_evidence): Multi-tenant isolation prevents state leakage between students.
9. P6-EVID-09 (concurrent_duplicate): Real OS threads serialized by BEGIN IMMEDIATE without deadlock.
"""

from __future__ import annotations

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
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
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
    AdmissionResult,
    RejectionReason,
    SessionProvenanceContext,
)
from study_engine.contracts.execution import (
    ExecutionObservation,
    ExecutionStatus,
    ObservedArtifact,
    ProcessTelemetry,
)
from study_engine.contracts.spine import (
    ExecutionProvenanceSpine,
    SpineAssessment,
    SpineCurriculum,
    SpineExecution,
    SpineIdentity,
    SpineTerminalState,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.curriculum.rubric_contracts import AssessmentRubric
from study_engine.curriculum.task_contracts import PracticalTaskSpecification
from study_engine.roadmap.contracts import CurricularRoadmap
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
    AssessmentPolicy,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)
from study_engine.state.state_contracts import NodeProgressStatus
from study_engine.state.state_engine import derive_student_state


@pytest.fixture(scope="module")
def phase6_setup() -> Dict[str, Any]:
    """Module-level fixture configuring the registry, roadmap, policy, task, rubric, and engines."""
    curriculum_dir = REPO_ROOT / "data" / "curriculum"
    registry = CurriculumRegistry(root_dir=curriculum_dir)
    roadmap = registry.load_roadmap("cybersecurity_v1.yaml")
    policy = build_cybersecurity_policy()

    task = registry.load_task("task_sec05_file_hasher.json")
    rubric = registry.load_rubric("rubric_sec05_deterministic.json")

    assessment_engine = DeterministicAssessmentEngine()
    ingestion_engine = EvidenceIngestionEngine()

    oracle_path = REPO_ROOT / "data" / "experiments" / "hito6" / "hito6_oracle.json"
    with open(oracle_path, "r", encoding="utf-8") as f:
        oracle_data = json.load(f)

    phase6_cases = {
        c["case_id"]: c
        for c in oracle_data.get("phase_6_evidence_concurrency_attacks", {}).get("cases", [])
    }

    return {
        "registry": registry,
        "roadmap": roadmap,
        "policy": policy,
        "task": task,
        "rubric": rubric,
        "assessment_engine": assessment_engine,
        "ingestion_engine": ingestion_engine,
        "cases": phase6_cases,
    }


def _setup_student_ledger(
    student_id: str,
    file_path: Optional[Path] = None,
) -> EvidenceLedger:
    """Initialize a ledger with prerequisite masteries for SEC-01, SEC-02, SEC-03."""
    ledger = EvidenceLedger(file_path=file_path) if file_path else EvidenceLedger()
    now = datetime.now(timezone.utc)

    prereqs = [
        ("SEC-01-C-PTR", EvidenceType.CONCEPTUAL_EXPLANATION),
        ("SEC-02-OS-PROC", EvidenceType.CONCEPTUAL_EXPLANATION),
        ("SEC-03-MEM-MGMT", EvidenceType.CODE_EXECUTION),
    ]

    for nid, etype in prereqs:
        rec = EvidenceRecord(
            record_id=f"rec-prereq-{nid}-{student_id}",
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


def _create_canonical_assessment(
    setup: Dict[str, Any],
    observation_id: str = "obs-clean",
) -> AssessmentResult:
    """Generate a canonical AssessmentResult for SEC-05."""
    engine: DeterministicAssessmentEngine = setup["assessment_engine"]
    task: PracticalTaskSpecification = setup["task"]
    rubric: AssessmentRubric = setup["rubric"]

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
    return engine.assess(
        task=task,
        rubric=rubric,
        observation=obs,
        task_revision_id="rev-task-01",
        rubric_revision_id="rev-rubric-01",
    )


# ---------------------------------------------------------------------------
# Test 1: P6-EVID-01 — Preflight Gate 4 Anti-Replay
# ---------------------------------------------------------------------------
def test_p6_evid_01_duplicate_attempt_preflight_anti_replay(phase6_setup: Dict[str, Any]) -> None:
    """Assert duplicate assessment is intercepted early by Gate 4 before reaching ledger."""
    case = phase6_setup["cases"]["P6-EVID-01"]
    cin = case["input"]
    exp = case["expected"]

    roadmap: CurricularRoadmap = phase6_setup["roadmap"]
    policy: AssessmentPolicy = phase6_setup["policy"]
    engine: EvidenceIngestionEngine = phase6_setup["ingestion_engine"]

    student_id = cin["student_id"]
    ledger = _setup_student_ledger(student_id)
    initial_count = len(ledger._entries)

    asmt = _create_canonical_assessment(phase6_setup, observation_id="obs-p6-01")

    prov_ctx = SessionProvenanceContext(
        student_id=student_id,
        session_id="session-p6-01",
        resolved_target_node_id=cin["node_id"],
        requested_node_id=cin["node_id"],
        roadmap_revision_id=roadmap.canonical_revision_id,
        policy_revision_id=policy.canonical_policy_id,
        expected_task_specification_sha256=asmt.task.specification_sha256,
        expected_rubric_specification_sha256=asmt.rubric.specification_sha256,
        session_is_active=True,
        session_started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )

    # 1st Submission: ADMITTED and committed
    adm1 = engine.evaluate_admissibility(asmt, prov_ctx, ledger)
    assert adm1.decision.value == exp["first_decision"]
    assert adm1.outcome is not None
    assert adm1.outcome.value == exp["first_outcome"]
    rec1 = engine.build_admitted_record(asmt, prov_ctx, adm1.outcome, adm1.admission_trace)
    rec1 = rec1.model_copy(update={"metadata": {**rec1.metadata, "evaluation_attempt_id": cin["evaluation_attempt_id"]}})
    ledger.append_record(rec1)

    # 2nd Submission: REJECTED by Gate 4 preflight anti-replay
    adm2 = engine.evaluate_admissibility(asmt, prov_ctx, ledger)
    assert adm2.decision.value == exp["second_decision"]
    assert adm2.rejection_reason is not None
    assert adm2.rejection_reason.value == exp["second_rejection_reason"]

    final_count = len(ledger._entries)
    ledger_delta = final_count - initial_count
    assert ledger_delta == exp["ledger_delta_total"]

    # Verify attempt cardinality is strictly 1
    attempt_count = sum(
        1
        for e in ledger._entries
        if e.record.metadata and e.record.metadata.get("evaluation_attempt_id") == cin["evaluation_attempt_id"]
    )
    assert attempt_count == 1

    # Verify hash chain integrity
    rep = ledger.verify_integrity()
    assert rep.status.value == exp["hash_chain_status"]

    # Verify student state progression
    state = derive_student_state(roadmap, policy, ledger, student_id)
    node_state = state.get_node_state(cin["node_id"])
    assert node_state is not None
    assert node_state.status.value == exp["node_status_after"]


# ---------------------------------------------------------------------------
# Test 2: P6-EVID-02 — Ledger D(K, R) Idempotent Replay
# ---------------------------------------------------------------------------
def test_p6_evid_02_same_k_same_r_idempotent_replay(phase6_setup: Dict[str, Any]) -> None:
    """Assert identical replay (K, R) directly on ledger raises IdempotentReplayError with cardinality=1."""
    case = phase6_setup["cases"]["P6-EVID-02"]
    cin = case["input"]
    exp = case["expected"]

    student_id = cin["student_id"]
    ledger = _setup_student_ledger(student_id)
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

    with pytest.raises(IdempotentReplayError):
        ledger.append_record(rec2)

    final_count = len(ledger._entries)
    assert final_count - initial_count == exp["ledger_delta_total"]

    attempt_count = sum(
        1
        for e in ledger._entries
        if e.record.metadata and e.record.metadata.get("evaluation_attempt_id") == cin["evaluation_attempt_id"]
    )
    assert attempt_count == exp["attempt_cardinality"]

    rep = ledger.verify_integrity()
    assert rep.status.value == exp["hash_chain_status"]


# ---------------------------------------------------------------------------
# Test 3: P6-EVID-03 — Ledger D(K, R) Inconsistent Replay
# ---------------------------------------------------------------------------
def test_p6_evid_03_same_k_different_r_inconsistent_replay(phase6_setup: Dict[str, Any]) -> None:
    """Assert conflicting replay (K, R') directly on ledger raises InconsistentReplayError fail-closed."""
    case = phase6_setup["cases"]["P6-EVID-03"]
    cin = case["input"]
    exp = case["expected"]

    student_id = cin["student_id"]
    ledger = _setup_student_ledger(student_id)
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

    with pytest.raises(InconsistentReplayError):
        ledger.append_record(rec2)

    final_count = len(ledger._entries)
    assert final_count - initial_count == exp["ledger_delta_total"]

    attempt_count = sum(
        1
        for e in ledger._entries
        if e.record.metadata and e.record.metadata.get("evaluation_attempt_id") == cin["evaluation_attempt_id"]
    )
    assert attempt_count == exp["attempt_cardinality"]

    rep = ledger.verify_integrity()
    assert rep.status.value == exp["hash_chain_status"]


# ---------------------------------------------------------------------------
# Test 4: P6-EVID-04 — Gate 2 Spine Node Mismatch
# ---------------------------------------------------------------------------
def test_p6_evid_04_wrong_node_spine_node_mismatch(phase6_setup: Dict[str, Any]) -> None:
    """Assert Gate 2 detects discrepancy between spine node and resolved target node."""
    case = phase6_setup["cases"]["P6-EVID-04"]
    cin = case["input"]
    exp = case["expected"]

    roadmap: CurricularRoadmap = phase6_setup["roadmap"]
    policy: AssessmentPolicy = phase6_setup["policy"]
    engine: EvidenceIngestionEngine = phase6_setup["ingestion_engine"]

    student_id = cin["student_id"]
    ledger = _setup_student_ledger(student_id)
    initial_count = len(ledger._entries)

    asmt = _create_canonical_assessment(phase6_setup, observation_id="obs-p6-04")

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
            roadmap_revision_id=roadmap.canonical_revision_id,
            policy_revision_id=policy.canonical_policy_id,
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
        roadmap_revision_id=roadmap.canonical_revision_id,
        policy_revision_id=policy.canonical_policy_id,
        expected_task_specification_sha256=asmt.task.specification_sha256,
        expected_rubric_specification_sha256=asmt.rubric.specification_sha256,
        spine=spine,
        session_is_active=True,
        session_started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )

    adm = engine.evaluate_admissibility(asmt, prov_ctx, ledger)
    assert adm.decision.value == exp["decision"]
    assert adm.rejection_reason is not None
    assert adm.rejection_reason.value == exp["rejection_reason"]
    assert exp["rejection_detail_substring"] in (adm.rejection_detail or "")

    final_count = len(ledger._entries)
    assert final_count - initial_count == exp["ledger_delta"]

    rep = ledger.verify_integrity()
    assert rep.status.value == exp["hash_chain_status"]


# ---------------------------------------------------------------------------
# Test 5: P6-EVID-05 — Gate 3 Session Inactive or Expired
# ---------------------------------------------------------------------------
def test_p6_evid_05_wrong_provenance_session_inactive(phase6_setup: Dict[str, Any]) -> None:
    """Assert Gate 3 rejects inactive session fail-closed before anti-replay or ledger."""
    case = phase6_setup["cases"]["P6-EVID-05"]
    cin = case["input"]
    exp = case["expected"]

    roadmap: CurricularRoadmap = phase6_setup["roadmap"]
    policy: AssessmentPolicy = phase6_setup["policy"]
    engine: EvidenceIngestionEngine = phase6_setup["ingestion_engine"]

    student_id = cin["student_id"]
    ledger = _setup_student_ledger(student_id)
    initial_count = len(ledger._entries)

    asmt = _create_canonical_assessment(phase6_setup, observation_id="obs-p6-05")

    prov_ctx = SessionProvenanceContext(
        student_id=student_id,
        session_id="session-p6-05",
        resolved_target_node_id=cin["node_id"],
        requested_node_id=cin["node_id"],
        roadmap_revision_id=roadmap.canonical_revision_id,
        policy_revision_id=policy.canonical_policy_id,
        expected_task_specification_sha256=asmt.task.specification_sha256,
        expected_rubric_specification_sha256=asmt.rubric.specification_sha256,
        session_is_active=cin["session_is_active"],  # False
        session_started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )

    adm = engine.evaluate_admissibility(asmt, prov_ctx, ledger)
    assert adm.decision.value == exp["decision"]
    assert adm.rejection_reason is not None
    assert adm.rejection_reason.value == exp["rejection_reason"]

    final_count = len(ledger._entries)
    assert final_count - initial_count == exp["ledger_delta"]

    rep = ledger.verify_integrity()
    assert rep.status.value == exp["hash_chain_status"]


# ---------------------------------------------------------------------------
# Test 6: P6-EVID-06 — Gate 1 Integrity Corrupted Digest
# ---------------------------------------------------------------------------
def test_p6_evid_06_missing_or_forged_digest_corrupted(phase6_setup: Dict[str, Any]) -> None:
    """Assert Gate 1 detects forged assessment_digest via recomputed canonical hash."""
    case = phase6_setup["cases"]["P6-EVID-06"]
    cin = case["input"]
    exp = case["expected"]

    roadmap: CurricularRoadmap = phase6_setup["roadmap"]
    policy: AssessmentPolicy = phase6_setup["policy"]
    engine: EvidenceIngestionEngine = phase6_setup["ingestion_engine"]

    student_id = cin["student_id"]
    ledger = _setup_student_ledger(student_id)
    initial_count = len(ledger._entries)

    asmt = _create_canonical_assessment(phase6_setup, observation_id="obs-p6-06")
    forged_asmt = asmt.model_copy(update={"assessment_digest": cin["forged_digest"]})

    prov_ctx = SessionProvenanceContext(
        student_id=student_id,
        session_id="session-p6-06",
        resolved_target_node_id=cin["node_id"],
        requested_node_id=cin["node_id"],
        roadmap_revision_id=roadmap.canonical_revision_id,
        policy_revision_id=policy.canonical_policy_id,
        expected_task_specification_sha256=asmt.task.specification_sha256,
        expected_rubric_specification_sha256=asmt.rubric.specification_sha256,
        session_is_active=True,
        session_started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )

    adm = engine.evaluate_admissibility(forged_asmt, prov_ctx, ledger)
    assert adm.decision.value == exp["decision"]
    assert adm.rejection_reason is not None
    assert adm.rejection_reason.value == exp["rejection_reason"]

    final_count = len(ledger._entries)
    assert final_count - initial_count == exp["ledger_delta"]

    rep = ledger.verify_integrity()
    assert rep.status.value == exp["hash_chain_status"]


# ---------------------------------------------------------------------------
# Test 7: P6-EVID-07 — Refinement 1: Direct SQLite Row Mutation Tamper
# ---------------------------------------------------------------------------
def test_p6_evid_07_tampered_evidence_hash_chain_broken(phase6_setup: Dict[str, Any]) -> None:
    """Assert direct out-of-band SQLite database mutation breaks cryptographic hash chain."""
    case = phase6_setup["cases"]["P6-EVID-07"]
    cin = case["input"]
    exp = case["expected"]

    student_id = cin["student_id"]

    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "tamper_pytest.db"
        ledger1 = _setup_student_ledger(student_id, file_path=db_path)
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

        # Unlink JSONL view so reloading relies purely on mutated SQLite table
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

    assert rep.status.value == exp["expected_integrity_status"]
    assert rep.status == LedgerIntegrityStatus.HASH_CHAIN_BROKEN


# ---------------------------------------------------------------------------
# Test 8: P6-EVID-08 — Cross-Student Multi-Tenant Isolation
# ---------------------------------------------------------------------------
def test_p6_evid_08_cross_student_evidence_epistemic_isolation(phase6_setup: Dict[str, Any]) -> None:
    """Assert multi-tenant evidence isolation prevents Student A from inheriting Student B's mastery."""
    case = phase6_setup["cases"]["P6-EVID-08"]
    cin = case["input"]
    exp = case["expected"]

    roadmap: CurricularRoadmap = phase6_setup["roadmap"]
    policy: AssessmentPolicy = phase6_setup["policy"]

    ledger = EvidenceLedger()
    now = datetime.now(timezone.utc)

    prereqs = [
        ("SEC-01-C-PTR", EvidenceType.CONCEPTUAL_EXPLANATION),
        ("SEC-02-OS-PROC", EvidenceType.CONCEPTUAL_EXPLANATION),
        ("SEC-03-MEM-MGMT", EvidenceType.CODE_EXECUTION),
    ]

    # Student A has prereqs only
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

    # Student B has prereqs + SEC-05 mastery
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

    # Derive state independently
    state_a = derive_student_state(roadmap, policy, ledger, cin["student_a_id"])
    sec05_a = state_a.get_node_state(cin["node_id"])
    status_a = sec05_a.status.value if sec05_a else None

    state_b = derive_student_state(roadmap, policy, ledger, cin["student_b_id"])
    sec05_b = state_b.get_node_state(cin["node_id"])
    status_b = sec05_b.status.value if sec05_b else None

    assert status_a == exp["student_a_status"]  # AVAILABLE
    assert status_b == exp["student_b_status"]  # ASSESSED_PROFICIENT
    assert status_a != NodeProgressStatus.ASSESSED_PROFICIENT.value

    rep = ledger.verify_integrity()
    assert rep.status.value == "VALID"


# ---------------------------------------------------------------------------
# Test 9: P6-EVID-09 — Refinement 2: Concurrent Duplicate with Anti-Deadlock Timeout
# ---------------------------------------------------------------------------
def test_p6_evid_09_concurrent_duplicate_atomic_serialization(phase6_setup: Dict[str, Any]) -> None:
    """Assert real OS threads competing on identical attempt (K, R) are serialized atomically by BEGIN IMMEDIATE."""
    case = phase6_setup["cases"]["P6-EVID-09"]
    cin = case["input"]
    exp = case["expected"]

    student_id = cin["student_id"]

    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "concurrent_pytest.db"
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

        # Enforce anti-deadlock timeout (Refinement 2)
        t1.join(timeout=cin["join_timeout_seconds"])
        t2.join(timeout=cin["join_timeout_seconds"])

        assert not t1.is_alive(), "Worker thread 1 deadlocked!"
        assert not t2.is_alive(), "Worker thread 2 deadlocked!"

        # Assert exactly one thread committed and one caught idempotent replay
        assert len(thread_results) == exp["committed_threads_count"]
        assert len(thread_errors) == exp["idempotent_replay_threads_count"]

        # Check SQLite persistence cardinality
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM evidence_ledger WHERE evaluation_attempt_id = ?",
            (cin["evaluation_attempt_id"],),
        )
        row = cur.fetchone()
        cur_count = row[0] if row else 0
        conn.close()

        assert cur_count == exp["attempt_cardinality"]

        # Check in-memory ledger cardinality
        assert len(ledger._entries) == exp["total_ledger_entries"]

        rep = ledger.verify_integrity()
        assert rep.status.value == exp["hash_chain_status"]

        ledger.close()
