"""End-to-end integration tests for Study Loop (Hito 4 / GP-B Formalization).

Orchestrates the full execution-to-state pipeline through SessionOrchestrator:
CurriculumRegistry -> ExecutionPort (S6.1) -> AssessmentPort (S9.1) ->
EvidenceIngestionPort (S5.2.A) -> StateReadPort (S5.2.C).

Validates:
- Escenario B.1: Execution SUCCESS (exit 0) + Assessment FAIL (20 bytes).
  Evidence admitted as FAIL, PROG-01 IN_PROGRESS, PROG-02 LOCKED.
- Escenario B.2: Execution SUCCESS (exit 0) + Assessment PASS (64 bytes).
  Evidence admitted as PASS, PROG-01 ASSESSED_PROFICIENT, PROG-02 AVAILABLE.
- Invariant: Execution Success != Mastery.
- Escenario B.3: EvidenceIngestionPort rejects identical (IdempotentReplayError)
  and divergent (InconsistentReplayError) replays.
"""

from datetime import timedelta
from pathlib import Path
import sys
import tempfile
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.experiments.gp_b_contracts import (
    ATTEMPT_B1,
    ATTEMPT_B2,
    CANONICAL_STDIN,
    NODE_DOWNSTREAM,
    NODE_ROOT,
    STUDENT_ID,
    TASK_ID,
    build_assessment_policy,
    build_roadmap,
    build_rubric,
    build_task_specification,
)
from study_engine.contracts.assessment import (
    AssessmentResult,
    compute_canonical_sha256,
)
from study_engine.contracts.evidence_ingestion import SessionProvenanceContext
from study_engine.curriculum.performance_contracts import PerformanceLevel
from tests.utils.test_registry import TestCurriculumRegistry
from study_engine.session.adapters import (
    CurriculumStateAdapter,
    DeterministicAssessmentAdapter,
    EvidenceIngestionAdapter,
    PracticalExecutionAdapter,
)
from study_engine.session.contracts import (
    PracticeRequest,
    PracticeResultStatus,
)
from study_engine.session.orchestrator import SessionOrchestrator
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import (
    IdempotentReplayError,
    InconsistentReplayError,
)
from study_engine.state.policy_contracts import EvidenceOutcome
from study_engine.state.state_contracts import NodeProgressStatus


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture
def bad_artifact_path(repo_root: Path) -> Path:
    path = repo_root / "scratch" / "fixtures" / "gp_b" / "student_bad_artifact.py"
    assert path.exists(), f"Bad fixture not found at {path}"
    return path


@pytest.fixture
def clean_solution_path(repo_root: Path) -> Path:
    path = repo_root / "scratch" / "fixtures" / "gp_b" / "student_clean_solution.py"
    assert path.exists(), f"Clean solution fixture not found at {path}"
    return path


@pytest.fixture
def study_loop_fixture():
    """Build shared curriculum, ledger, adapters, and orchestrator."""
    roadmap = build_roadmap()
    policy = build_assessment_policy()
    task = build_task_specification()
    rubric = build_rubric()

    registry = TestCurriculumRegistry()
    registry.register_task(task)
    registry.register_rubric(rubric, task_id=task.task_id)

    ledger = EvidenceLedger()

    exec_adapter = PracticalExecutionAdapter(default_stdin=CANONICAL_STDIN)
    assess_adapter = DeterministicAssessmentAdapter(default_task=task)
    ingest_adapter = EvidenceIngestionAdapter(
        ledger=ledger,
        roadmap=roadmap,
        policy=policy,
        student_id=STUDENT_ID,
        session_id="session-study-loop-e2e",
    )
    state_adapter = CurriculumStateAdapter(
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        student_id=STUDENT_ID,
    )

    orch = SessionOrchestrator(
        session_id="session-study-loop-e2e",
        student_id=STUDENT_ID,
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
        "roadmap": roadmap,
        "policy": policy,
        "task": task,
        "rubric": rubric,
        "registry": registry,
        "ledger": ledger,
        "exec_adapter": exec_adapter,
        "assess_adapter": assess_adapter,
        "ingest_adapter": ingest_adapter,
        "state_adapter": state_adapter,
        "orchestrator": orch,
    }


def test_study_loop_e2e_full_lifecycle(
    study_loop_fixture, bad_artifact_path: Path, clean_solution_path: Path
):
    """Formal test covering B.1, B.2, Invariant Verification, and B.3 Replay Defense."""
    orch = study_loop_fixture["orchestrator"]
    state_adapter = study_loop_fixture["state_adapter"]
    ingest_adapter = study_loop_fixture["ingest_adapter"]
    ledger = study_loop_fixture["ledger"]
    task = study_loop_fixture["task"]
    rubric = study_loop_fixture["rubric"]
    exec_adapter = study_loop_fixture["exec_adapter"]
    assess_adapter = study_loop_fixture["assess_adapter"]

    # Initial state verification
    init_root = state_adapter.get_node_state(NODE_ROOT)
    init_down = state_adapter.get_node_state(NODE_DOWNSTREAM)
    assert init_root is not None
    assert init_down is not None
    assert init_root.status == NodeProgressStatus.AVAILABLE
    assert init_down.status == NodeProgressStatus.LOCKED

    # =========================================================================
    # ESCENARIO B.1: Execution SUCCESS (exit 0) + Assessment FAIL (20 bytes)
    # =========================================================================
    req_b1 = PracticeRequest(
        student_id=STUDENT_ID,
        node_id=NODE_ROOT,
        task_id=TASK_ID,
        artifact_path=str(bad_artifact_path),
    )

    res_b1 = orch.handle_practical_submission(req_b1)

    assert res_b1.status == PracticeResultStatus.EVALUATED
    assert res_b1.assessment_summary["passed"] is False
    assert res_b1.assessment_summary["overall_level"] == PerformanceLevel.N1_INSUFFICIENT.name
    assert res_b1.assessment_summary["outcome"] == EvidenceOutcome.FAIL.value
    assert res_b1.assessment_summary["score"] == 0.0
    assert res_b1.evidence_record_id is not None
    assert ledger.total_entries == 1

    # State verification after B.1: PROG-01 is IN_PROGRESS, PROG-02 remains LOCKED
    state_b1_root = state_adapter.get_node_state(NODE_ROOT)
    state_b1_down = state_adapter.get_node_state(NODE_DOWNSTREAM)
    assert state_b1_root is not None
    assert state_b1_down is not None
    assert state_b1_root.status == NodeProgressStatus.IN_PROGRESS
    assert state_b1_down.status == NodeProgressStatus.LOCKED

    # =========================================================================
    # ESCENARIO B.2: Execution SUCCESS (exit 0) + Assessment PASS (64 bytes)
    # =========================================================================
    req_b2 = PracticeRequest(
        student_id=STUDENT_ID,
        node_id=NODE_ROOT,
        task_id=TASK_ID,
        artifact_path=str(clean_solution_path),
    )

    res_b2 = orch.handle_practical_submission(req_b2)

    assert res_b2.status == PracticeResultStatus.EVALUATED
    assert res_b2.assessment_summary["passed"] is True
    assert res_b2.assessment_summary["overall_level"] == PerformanceLevel.N3_COMPETENT.name
    assert res_b2.assessment_summary["outcome"] == EvidenceOutcome.PASS.value
    assert res_b2.assessment_summary["score"] == 1.0
    assert res_b2.evidence_record_id is not None
    assert ledger.total_entries == 2

    # State verification after B.2: PROG-01 is ASSESSED_PROFICIENT, PROG-02 is AVAILABLE
    state_b2_root = state_adapter.get_node_state(NODE_ROOT)
    state_b2_down = state_adapter.get_node_state(NODE_DOWNSTREAM)
    assert state_b2_root is not None
    assert state_b2_down is not None
    assert state_b2_root.status == NodeProgressStatus.ASSESSED_PROFICIENT
    assert state_b2_down.status == NodeProgressStatus.AVAILABLE

    # =========================================================================
    # INVARIANT: Execution Success != Mastery
    # =========================================================================
    # Both B.1 and B.2 executed with exit_code 0 in the sandbox
    obs_b1 = res_b1.execution_observation
    obs_b2 = res_b2.execution_observation
    assert obs_b1 is not None and obs_b1["exit_code"] == 0
    assert obs_b2 is not None and obs_b2["exit_code"] == 0

    # Yet B.1 failed mastery while B.2 demonstrated mastery
    assert res_b1.assessment_summary["passed"] is False
    assert res_b2.assessment_summary["passed"] is True
    assert state_b1_down.status == NodeProgressStatus.LOCKED
    assert state_b2_down.status == NodeProgressStatus.AVAILABLE

    # =========================================================================
    # ESCENARIO B.3: Replay Defense in EvidenceIngestionPort
    # =========================================================================
    # Retrieve the exact evaluated assessment from B.2
    asmt_b2 = res_b2.assessment_result
    assert asmt_b2 is not None

    roadmap = study_loop_fixture["roadmap"]
    policy = study_loop_fixture["policy"]
    prov_ctx = SessionProvenanceContext(
        student_id=STUDENT_ID,
        session_id=orch.session_id,
        resolved_target_node_id=NODE_ROOT,
        requested_node_id=NODE_ROOT,
        roadmap_revision_id=roadmap.canonical_revision_id,
        policy_revision_id=policy.canonical_policy_id,
        expected_task_specification_sha256=asmt_b2.task.specification_sha256,
        expected_rubric_specification_sha256=asmt_b2.rubric.specification_sha256,
        session_is_active=True,
        session_started_at=orch.session_started_at,
    )

    # 1. Identical replay raises IdempotentReplayError
    with pytest.raises(IdempotentReplayError):
        ingest_adapter.ingest_assessment(asmt_b2, context=prov_ctx)

    # 2. Divergent replay (same attempt/core but modified digest) raises InconsistentReplayError
    interim = asmt_b2.model_copy(
        update={
            "assessment_digest": "",
            "assessed_at": asmt_b2.assessed_at + timedelta(seconds=10),
        }
    )
    div_digest = compute_canonical_sha256(interim)
    asmt_divergent = interim.model_copy(
        update={"assessment_digest": div_digest}
    )
    with pytest.raises(InconsistentReplayError):
        ingest_adapter.ingest_assessment(asmt_divergent, context=prov_ctx)

    # 3. Verify ledger remains intact with exactly 2 entries and valid hash chain
    assert ledger.total_entries == 2
    integrity = ledger.verify_integrity()
    assert integrity.status.value == "VALID"
