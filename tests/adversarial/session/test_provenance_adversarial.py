"""Adversarial tests for SessionProvenanceContext and Epistemic Lineage.

Verifies:
1. Direct ingest_assessment call without SessionProvenanceContext strictly raises MissingProvenanceError.
2. Zero arbitrary node fallback occurs (no fallback to first roadmap node).
3. Zero ledger mutation occurs upon missing provenance context.
4. Curricular node mismatch between request and task is rejected before execution.
5. Valid provenance context admits evidence under the authoritative target node.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from typing import Any, Dict
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from study_engine.contracts.assessment import AssessmentResult
from study_engine.contracts.evidence_ingestion import SessionProvenanceContext
from study_engine.contracts.execution import ExecutionObservation
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.session.adapters import (
    CurriculumStateAdapter,
    DeterministicAssessmentAdapter,
    EvidenceIngestionAdapter,
    PracticalExecutionAdapter,
)
from study_engine.session.contracts import (
    MissingProvenanceError,
    PracticeRequest,
    PracticeResultStatus,
)
from study_engine.session.orchestrator import SessionOrchestrator
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.policy_contracts import AssessmentPolicy
from scripts.experiments.run_golden_path_e2e import build_cybersecurity_policy


@pytest.fixture
def session_env() -> Dict[str, Any]:
    repo_root = REPO_ROOT
    curriculum_dir = repo_root / "data/curriculum"
    registry = CurriculumRegistry(root_dir=curriculum_dir)
    roadmap = registry.load_roadmap("cybersecurity_v1.yaml")
    alignment = registry.load_alignment("cybersecurity_v1_alignment.json")
    task = registry.load_task("task_sec05_file_hasher.json")
    rubric = registry.load_rubric("rubric_sec05_deterministic.json")
    policy = build_cybersecurity_policy()
    ledger = EvidenceLedger()

    exec_adapter = PracticalExecutionAdapter()
    assess_adapter = DeterministicAssessmentAdapter()
    ingest_adapter = EvidenceIngestionAdapter(
        ledger=ledger,
        roadmap=roadmap,
        policy=policy,
        student_id="student-provenance-adv",
        session_id="session-provenance-adv",
    )
    state_adapter = CurriculumStateAdapter(
        ledger=ledger,
        roadmap=roadmap,
        policy=policy,
        student_id="student-provenance-adv",
    )

    artifact_path = repo_root / "scratch/fixtures/gp_b/student_clean_solution.py"
    obs: ExecutionObservation = exec_adapter.execute_task(task, str(artifact_path))
    asmt: AssessmentResult = assess_adapter.evaluate_observation(obs, rubric, task)

    orch = SessionOrchestrator(
        session_id="session-provenance-adv",
        student_id="student-provenance-adv",
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        execution_port=exec_adapter,
        assessment_port=assess_adapter,
        ingestion_port=ingest_adapter,
        state_read_port=state_adapter,
        curriculum_registry=registry,
    )
    orch.start_session()

    return {
        "registry": registry,
        "roadmap": roadmap,
        "alignment": alignment,
        "task": task,
        "rubric": rubric,
        "policy": policy,
        "ledger": ledger,
        "exec_adapter": exec_adapter,
        "assess_adapter": assess_adapter,
        "ingest_adapter": ingest_adapter,
        "state_adapter": state_adapter,
        "orchestrator": orch,
        "assessment": asmt,
        "artifact_path": str(artifact_path),
    }


def test_ingest_assessment_missing_context_raises_missing_provenance_error(
    session_env: Dict[str, Any],
) -> None:
    """CRIT: Missing SessionProvenanceContext must raise MissingProvenanceError and commit 0 entries."""
    ingest_adapter: EvidenceIngestionAdapter = session_env["ingest_adapter"]
    asmt: AssessmentResult = session_env["assessment"]
    ledger: EvidenceLedger = session_env["ledger"]

    assert len(ledger._entries) == 0

    with pytest.raises(MissingProvenanceError) as exc_info:
        ingest_adapter.ingest_assessment(assessment=asmt, context=None)

    assert "SessionProvenanceContext is mandatory" in str(exc_info.value)
    assert len(ledger._entries) == 0, "Ledger must not mutate when context is missing."


def test_handle_practical_submission_node_mismatch_rejected(
    session_env: Dict[str, Any],
) -> None:
    """CRIT: PracticeRequest specifying mismatched node_id must be rejected before execution."""
    orch: SessionOrchestrator = session_env["orchestrator"]
    ledger: EvidenceLedger = session_env["ledger"]
    artifact_path: str = session_env["artifact_path"]

    # task_sec05_file_hasher is anchored to SEC-05-BIN-SEC.
    # Attacking by requesting evaluation under SEC-01-C-PTR.
    req = PracticeRequest(
        student_id="student-provenance-adv",
        node_id="SEC-01-C-PTR",
        task_id="task_sec05_file_hasher.json",
        rubric_id="rubric_sec05_deterministic.json",
        artifact_path=artifact_path,
    )

    res = orch.handle_practical_submission(req)

    assert res.status == PracticeResultStatus.EXECUTION_FAILED
    assert "Curricular mismatch" in (res.rejection_reason or "")
    assert len(ledger._entries) == 0, "Zero entries committed on curricular node mismatch."


def test_handle_practical_submission_valid_provenance_admitted(
    session_env: Dict[str, Any],
) -> None:
    """Valid PracticeRequest with correct node_id must be admitted under authoritative node."""
    orch: SessionOrchestrator = session_env["orchestrator"]
    ledger: EvidenceLedger = session_env["ledger"]
    artifact_path: str = session_env["artifact_path"]

    req = PracticeRequest(
        student_id="student-provenance-adv",
        node_id="SEC-05-BIN-SEC",
        task_id="task_sec05_file_hasher.json",
        rubric_id="rubric_sec05_deterministic.json",
        artifact_path=artifact_path,
    )

    res = orch.handle_practical_submission(req)

    assert res.status == PracticeResultStatus.EVALUATED
    assert res.evidence_record_id is not None
    assert len(ledger._entries) == 1

    history = ledger.get_history_for_node("SEC-05-BIN-SEC")
    assert len(history) == 1
    committed_record = history[0]
    assert committed_record.node_id == "SEC-05-BIN-SEC"
    assert committed_record.student_id == "student-provenance-adv"
