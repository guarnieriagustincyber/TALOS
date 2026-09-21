"""Adversarial and security test suite for Phase 4: Execution Attacks (Hito 6).

Asserts full compliance against Subsystems S6.1 (Execution Sandbox) and S9.1
(Deterministic Assessment Engine), verifying the nuclear invariant:
    execution_success != mastery

Tests:
1. P4-EXEC-01 (exit_zero_wrong_artifact): Exit 0 but malformed artifact fails assessment.
2. P4-EXEC-02 (exit_zero_empty_artifact): Exit 0 but 0-byte file fails min_size_bytes.
3. P4-EXEC-03 (wrong_hash): Exit 0 but 32-byte MD5 digest fails size and validation.
4. P4-EXEC-04 (timeout): Process group times out at 2.0s, terminated by SIGTERM (exit -15).
5. P4-EXEC-05 (nonzero_exit): Process exits with code 42, fail-closed before assessment.
6. P4-EXEC-06 (missing_artifact): Process exits 0 but creates no artifact, verified absent.
7. P4-EXEC-07 (artifact_mutation): Tampered artifact rejected before execution via SHA mismatch.
8. P4-EXEC-08 (baseline_clean_pass): Positive control: canonical SHA-256 earns ASSESSED_PROFICIENT.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, Generator, Tuple
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
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


@pytest.fixture(scope="module")
def phase4_setup() -> Dict[str, Any]:
    """Module-level setup for curriculum registry, task, rubric, and policy."""
    curriculum_dir = REPO_ROOT / "data" / "curriculum"
    registry = CurriculumRegistry(root_dir=curriculum_dir)
    roadmap = registry.load_roadmap("cybersecurity_v1.yaml")
    alignment = registry.load_alignment("cybersecurity_v1_alignment.json")
    task = registry.load_task("task_sec05_file_hasher.json")
    rubric = registry.load_rubric("rubric_sec05_deterministic.json")
    policy = build_cybersecurity_policy()

    oracle_path = REPO_ROOT / "data" / "experiments" / "hito6" / "hito6_oracle.json"
    with open(oracle_path, "r", encoding="utf-8") as f:
        oracle = json.load(f)

    return {
        "registry": registry,
        "roadmap": roadmap,
        "alignment": alignment,
        "task": task,
        "rubric": rubric,
        "policy": policy,
        "oracle": oracle["phase_4_execution_attacks"],
    }


def _execute_case(
    setup: Dict[str, Any], case_id: str
) -> Tuple[PracticeResult, int, CurriculumStateAdapter, Dict[str, Any]]:
    """Helper to execute an isolated scenario and return result, delta ledger, state, and expected oracle."""
    oracle_cases = setup["oracle"]["cases"]
    case_spec = next(c for c in oracle_cases if c["case_id"] == case_id)
    cin = case_spec["input"]
    student_id = cin["student_id"]
    session_id = f"test-session-{case_id.lower()}"

    ledger = EvidenceLedger()

    # Commit baseline prerequisites:
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
            record_id=f"ev-test-base-{nid}-{case_id}",
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

    initial_cardinality = len(ledger._entries)

    exec_adapter = PracticalExecutionAdapter(
        default_stdin="STUDY_ENGINE_CANONICAL_INPUT",
        timeout_seconds=2,
    )
    assess_adapter = DeterministicAssessmentAdapter(default_task=setup["task"])
    ingest_adapter = EvidenceIngestionAdapter(
        ledger=ledger,
        roadmap=setup["roadmap"],
        policy=setup["policy"],
        student_id=student_id,
        session_id=session_id,
    )
    state_adapter = CurriculumStateAdapter(
        roadmap=setup["roadmap"],
        policy=setup["policy"],
        ledger=ledger,
        student_id=student_id,
    )

    orch = SessionOrchestrator(
        session_id=session_id,
        student_id=student_id,
        roadmap=setup["roadmap"],
        policy=setup["policy"],
        ledger=ledger,
        execution_port=exec_adapter,
        assessment_port=assess_adapter,
        ingestion_port=ingest_adapter,
        state_read_port=state_adapter,
        curriculum_registry=setup["registry"],
        allowed_artifact_roots=(REPO_ROOT / "scratch" / "fixtures" / "gp_b",),
        session_started_at=now - timedelta(minutes=5),
    )
    orch.start_session()

    artifact_abs = (REPO_ROOT / cin["artifact_path"]).resolve()
    req = PracticeRequest(
        student_id=student_id,
        node_id=cin["node_id"],
        task_id=cin["task_id"],
        rubric_id=cin["rubric_id"],
        artifact_path=str(artifact_abs),
        expected_sha256=cin.get("expected_sha256"),
    )

    res = orch.handle_practical_submission(req)
    final_cardinality = len(ledger._entries)
    delta_ledger = final_cardinality - initial_cardinality

    return res, delta_ledger, state_adapter, case_spec


def test_p4_exec_01_exit_zero_wrong_artifact(phase4_setup: Dict[str, Any]) -> None:
    """P4-EXEC-01: Exit 0 but malformed artifact fails assessment (proves execution != mastery)."""
    res, delta_ledger, state_adapter, case_spec = _execute_case(phase4_setup, "P4-EXEC-01")

    assert res.status == PracticeResultStatus.EVALUATED
    assert res.execution_observation is not None
    assert res.execution_observation["exit_code"] == 0
    assert res.execution_observation["status"] == "COMPLETED"

    assert res.assessment_result is not None
    assert res.assessment_result.aggregation.passed is False
    assert res.assessment_result.aggregation.overall_level is not None
    assert res.assessment_result.aggregation.overall_level.name == "N1_INSUFFICIENT"

    assert delta_ledger == 1
    st = state_adapter.get_student_state(case_spec["input"]["student_id"])
    ns = st.get_node_state("SEC-05-BIN-SEC")
    assert ns is not None
    assert ns.status == NodeProgressStatus.IN_PROGRESS
    assert ns.status.value != NodeProgressStatus.ASSESSED_PROFICIENT.value


def test_p4_exec_02_exit_zero_empty_artifact(phase4_setup: Dict[str, Any]) -> None:
    """P4-EXEC-02: Exit 0 but 0-byte artifact fails min_size_bytes postcondition."""
    res, delta_ledger, state_adapter, case_spec = _execute_case(phase4_setup, "P4-EXEC-02")

    assert res.status == PracticeResultStatus.EVALUATED
    assert res.execution_observation is not None
    assert res.execution_observation["exit_code"] == 0
    assert res.execution_observation["status"] == "COMPLETED"

    assert res.assessment_result is not None
    assert res.assessment_result.aggregation.passed is False
    assert res.assessment_result.aggregation.overall_level is not None
    assert res.assessment_result.aggregation.overall_level.name == "N1_INSUFFICIENT"

    assert delta_ledger == 1
    st = state_adapter.get_student_state(case_spec["input"]["student_id"])
    ns = st.get_node_state("SEC-05-BIN-SEC")
    assert ns is not None
    assert ns.status == NodeProgressStatus.IN_PROGRESS
    assert ns.status.value != NodeProgressStatus.ASSESSED_PROFICIENT.value


def test_p4_exec_03_wrong_hash(phase4_setup: Dict[str, Any]) -> None:
    """P4-EXEC-03: Exit 0 but 32-byte MD5 digest fails size constraints for SHA-256."""
    res, delta_ledger, state_adapter, case_spec = _execute_case(phase4_setup, "P4-EXEC-03")

    assert res.status == PracticeResultStatus.EVALUATED
    assert res.execution_observation is not None
    assert res.execution_observation["exit_code"] == 0
    assert res.execution_observation["status"] == "COMPLETED"

    assert res.assessment_result is not None
    assert res.assessment_result.aggregation.passed is False
    assert res.assessment_result.aggregation.overall_level is not None
    assert res.assessment_result.aggregation.overall_level.name == "N1_INSUFFICIENT"

    assert delta_ledger == 1
    st = state_adapter.get_student_state(case_spec["input"]["student_id"])
    ns = st.get_node_state("SEC-05-BIN-SEC")
    assert ns is not None
    assert ns.status == NodeProgressStatus.IN_PROGRESS
    assert ns.status.value != NodeProgressStatus.ASSESSED_PROFICIENT.value


def test_p4_exec_04_timeout(phase4_setup: Dict[str, Any]) -> None:
    """P4-EXEC-04: Process group exceeds timeout limit, terminated by SIGTERM (exit -15)."""
    res, delta_ledger, state_adapter, case_spec = _execute_case(phase4_setup, "P4-EXEC-04")

    assert res.status == PracticeResultStatus.EXECUTION_FAILED
    assert res.execution_observation is not None
    assert res.execution_observation["status"] == "TIMED_OUT"
    assert res.execution_observation["exit_code"] == -15
    assert "TIMED_OUT" in (res.rejection_reason or "")

    assert res.assessment_result is None
    assert delta_ledger == 0
    st = state_adapter.get_student_state(case_spec["input"]["student_id"])
    ns = st.get_node_state("SEC-05-BIN-SEC")
    assert ns is not None
    assert ns.status == NodeProgressStatus.AVAILABLE


def test_p4_exec_05_nonzero_exit(phase4_setup: Dict[str, Any]) -> None:
    """P4-EXEC-05: Nonzero exit code (42) triggers FAILED_PROCESS before assessment."""
    res, delta_ledger, state_adapter, case_spec = _execute_case(phase4_setup, "P4-EXEC-05")

    assert res.status == PracticeResultStatus.EXECUTION_FAILED
    assert res.execution_observation is not None
    assert res.execution_observation["status"] == "FAILED_PROCESS"
    assert res.execution_observation["exit_code"] == 42
    assert "FAILED_PROCESS" in (res.rejection_reason or "")

    assert res.assessment_result is None
    assert delta_ledger == 0
    st = state_adapter.get_student_state(case_spec["input"]["student_id"])
    ns = st.get_node_state("SEC-05-BIN-SEC")
    assert ns is not None
    assert ns.status == NodeProgressStatus.AVAILABLE


def test_p4_exec_06_missing_artifact(phase4_setup: Dict[str, Any]) -> None:
    """P4-EXEC-06: Exit 0 but missing output_hash.txt fails assessment via verified absence."""
    res, delta_ledger, state_adapter, case_spec = _execute_case(phase4_setup, "P4-EXEC-06")

    assert res.status == PracticeResultStatus.EVALUATED
    assert res.execution_observation is not None
    assert res.execution_observation["exit_code"] == 0
    assert res.execution_observation["status"] == "COMPLETED"

    assert res.assessment_result is not None
    assert res.assessment_result.aggregation.passed is False
    assert res.assessment_result.aggregation.overall_level is not None
    assert res.assessment_result.aggregation.overall_level.name == "N1_INSUFFICIENT"

    assert delta_ledger == 1
    st = state_adapter.get_student_state(case_spec["input"]["student_id"])
    ns = st.get_node_state("SEC-05-BIN-SEC")
    assert ns is not None
    assert ns.status == NodeProgressStatus.IN_PROGRESS
    assert ns.status.value != NodeProgressStatus.ASSESSED_PROFICIENT.value


def test_p4_exec_07_artifact_mutation(phase4_setup: Dict[str, Any]) -> None:
    """P4-EXEC-07: Disk mutation / expected hash mismatch rejected fail-closed before execution."""
    res, delta_ledger, state_adapter, case_spec = _execute_case(phase4_setup, "P4-EXEC-07")

    assert res.status == PracticeResultStatus.EXECUTION_FAILED
    assert res.execution_observation is None
    assert "Artifact digest mismatch" in (res.rejection_reason or "")

    assert res.assessment_result is None
    assert delta_ledger == 0
    st = state_adapter.get_student_state(case_spec["input"]["student_id"])
    ns = st.get_node_state("SEC-05-BIN-SEC")
    assert ns is not None
    assert ns.status == NodeProgressStatus.AVAILABLE


def test_p4_exec_08_baseline_clean_pass(phase4_setup: Dict[str, Any]) -> None:
    """P4-EXEC-08: Positive control: valid canonical solution earns ASSESSED_PROFICIENT mastery."""
    res, delta_ledger, state_adapter, case_spec = _execute_case(phase4_setup, "P4-EXEC-08")

    assert res.status == PracticeResultStatus.EVALUATED
    assert res.execution_observation is not None
    assert res.execution_observation["exit_code"] == 0
    assert res.execution_observation["status"] == "COMPLETED"

    assert res.assessment_result is not None
    assert res.assessment_result.aggregation.passed is True
    assert res.assessment_result.aggregation.overall_level is not None
    assert res.assessment_result.aggregation.overall_level.name == "N3_COMPETENT"

    assert delta_ledger == 1
    assert res.updated_node_status == NodeProgressStatus.ASSESSED_PROFICIENT.value
    st = state_adapter.get_student_state(case_spec["input"]["student_id"])
    ns = st.get_node_state("SEC-05-BIN-SEC")
    assert ns is not None
    assert ns.status == NodeProgressStatus.ASSESSED_PROFICIENT
