"""Formal automated certification test suite for Golden Path B (GP-B-V0).

Validates the complete execution-to-state pipeline and proves:
  Execution Success != Mastery
Verifies all 12 criteria and extended criteria independently.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid
import pytest

from study_engine.assessment.service import DeterministicAssessmentEngine
from study_engine.contracts.assessment import compute_canonical_sha256
from study_engine.contracts.evidence_ingestion import (
    AdmissionDecision,
    SessionProvenanceContext,
)
from study_engine.contracts.execution import (
    ExecutionPlaneTier,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionStatus,
    ToolCapability,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.execution.adapter_python import PythonExecutionAdapter
from study_engine.roadmap.contracts import DependencyType
from study_engine.state.ingestion_engine import EvidenceIngestionEngine
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import (
    IdempotentReplayError,
    InconsistentReplayError,
    LedgerIntegrityStatus,
)
from study_engine.state.policy_contracts import (
    CriteriaEvaluationVerdict,
    EvidenceOutcome,
)
from study_engine.state.state_contracts import NodeProgressStatus
from study_engine.state.state_engine import derive_student_state

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.experiments.gp_b_contracts import (
    ATTEMPT_B1,
    ATTEMPT_B2,
    CAMPAIGN_ID,
    CANONICAL_STDIN,
    EXPECTED_CLEAN_ARTIFACT_FILENAME,
    EXPECTED_CLEAN_ARTIFACT_MAX_SIZE,
    EXPECTED_CLEAN_ARTIFACT_MIN_SIZE,
    NODE_DOWNSTREAM,
    NODE_ROOT,
    STUDENT_ID,
    TASK_ID,
    build_assessment_policy,
    build_node_criteria,
    build_roadmap,
    build_rubric,
    build_task_specification,
)


@pytest.fixture(scope="module")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def oracle(repo_root: Path) -> dict:
    oracle_path = repo_root / "data" / "experiments" / "gp_b_oracle.json"
    assert oracle_path.exists(), "Oracle must exist at data/experiments/gp_b_oracle.json"
    with open(oracle_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def campaign_setup(repo_root: Path, tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("gp_b_cert")
    ledger_path = tmp_dir / "test_ledger.db"
    ledger = EvidenceLedger(file_path=ledger_path)

    task = build_task_specification()
    rubric = build_rubric()
    policy = build_assessment_policy()
    roadmap = build_roadmap()

    task_sha = compute_canonical_sha256(task)
    rubric_sha = compute_canonical_sha256(rubric)

    assessment_engine = DeterministicAssessmentEngine()
    execution_adapter = PythonExecutionAdapter()
    ingestion_engine = EvidenceIngestionEngine()

    return {
        "tmp_dir": tmp_dir,
        "ledger": ledger,
        "task": task,
        "rubric": rubric,
        "policy": policy,
        "roadmap": roadmap,
        "task_sha": task_sha,
        "rubric_sha": rubric_sha,
        "assessment_engine": assessment_engine,
        "execution_adapter": execution_adapter,
        "ingestion_engine": ingestion_engine,
    }


# =============================================================================
# M0 & M1: Baseline, Perimeter & Oracle Tests
# =============================================================================

def test_m0_frozen_perimeter_unchanged(repo_root: Path):
    """CRIT-11: Verify only the normatively frozen source perimeter.

    The GP-B manifest records a historical whole-source snapshot.  The current
    perimeter is deliberately narrower: session, tutor, and additive contracts
    may evolve without reopening certified state, execution, assessment, or
    audit engines.
    """
    manifest_path = repo_root / "artifacts" / "gp_b" / "frozen_manifest.json"
    hashes_path = repo_root / "artifacts" / "gp_b" / "frozen_src_hashes.txt"

    assert manifest_path.exists(), "Frozen manifest must exist"
    assert hashes_path.exists(), "Frozen hashes file must exist"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    with open(hashes_path, "rb") as f:
        computed_hashes_digest = hashlib.sha256(f.read()).hexdigest()

    assert computed_hashes_digest == manifest["frozen_src_hashes_sha256"]

    frozen_prefixes = (
        "src/study_engine/state/",
        "src/study_engine/execution/",
        "src/study_engine/assessment/",
        "src/study_engine/audit/",
    )
    verified_files = 0
    with open(hashes_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            expected_hash, rel_file = line.split(maxsplit=1)
            if not rel_file.startswith(frozen_prefixes):
                continue
            file_path = repo_root / rel_file
            assert file_path.exists(), f"File {rel_file} missing!"
            with open(file_path, "rb") as sf:
                actual_hash = hashlib.sha256(sf.read()).hexdigest()
            assert actual_hash == expected_hash, f"Perimeter breach: {rel_file} modified!"
            verified_files += 1

    assert verified_files > 0, "Frozen manifest must contain protected source files"


def test_m1_oracle_schema_is_valid(oracle: dict):
    """M1: Validate that gp_b_oracle.json conforms to the frozen specification."""
    assert oracle["campaign_id"] == "GP-B-V0"
    assert oracle["spec_version"] == "SPEC-GP-B-V0"
    assert oracle["canonical_stdin"] == CANONICAL_STDIN

    expected_digest = hashlib.sha256(CANONICAL_STDIN.encode("utf-8")).hexdigest()
    assert oracle["expected_clean_digest_sha256"] == expected_digest

    for scenario_key in ("B1", "B2", "B3a", "B3b"):
        assert scenario_key in oracle["scenarios"]


# =============================================================================
# M2: Controlled Fixtures Determinism Tests
# =============================================================================

def test_m2_bad_fixture_direct_behavior(repo_root: Path):
    """M2: Verify student_bad_artifact.py runs cleanly, writes 20-byte error, exit 0."""
    fixture = repo_root / "scratch" / "fixtures" / "gp_b" / "student_bad_artifact.py"
    with tempfile.TemporaryDirectory() as td:
        p = subprocess.run(
            [sys.executable, str(fixture)],
            input=CANONICAL_STDIN.encode("utf-8"),
            cwd=td,
            capture_output=True,
        )
        assert p.returncode == 0
        art = Path(td) / "output_hash.txt"
        assert art.exists()
        assert art.stat().st_size == 20
        with open(art, "r", encoding="ascii") as f:
            content = f.read()
        assert content == "ERROR: INVALID_INPUT"


def test_m2_clean_fixture_direct_behavior(repo_root: Path):
    """M2: Verify student_clean_solution.py computes exact 64-char SHA-256 digest."""
    fixture = repo_root / "scratch" / "fixtures" / "gp_b" / "student_clean_solution.py"
    expected_digest = hashlib.sha256(CANONICAL_STDIN.encode("utf-8")).hexdigest()
    with tempfile.TemporaryDirectory() as td:
        p = subprocess.run(
            [sys.executable, str(fixture)],
            input=CANONICAL_STDIN.encode("utf-8"),
            cwd=td,
            capture_output=True,
        )
        assert p.returncode == 0
        art = Path(td) / "output_hash.txt"
        assert art.exists()
        assert art.stat().st_size == 64
        with open(art, "r", encoding="ascii") as f:
            content = f.read()
        assert content == expected_digest


# =============================================================================
# M3: Contracts Validation Tests
# =============================================================================

def test_m3_task_contract_is_canonical():
    """M3: Verify PracticalTaskSpecification adheres to PF-FINDING-01."""
    task = build_task_specification()
    assert task.task_id == TASK_ID
    assert task.curriculum_node_id == NODE_ROOT
    assert len(task.required_artifacts) == 1
    req = task.required_artifacts[0]
    assert req.requirement_id == EXPECTED_CLEAN_ARTIFACT_FILENAME
    assert req.min_size_bytes == EXPECTED_CLEAN_ARTIFACT_MIN_SIZE
    assert req.max_size_bytes == EXPECTED_CLEAN_ARTIFACT_MAX_SIZE


def test_m3_policy_contract_is_canonical():
    """M3: Verify NodeAssessmentCriteria and AssessmentPolicy."""
    policy = build_assessment_policy()
    assert NODE_ROOT in policy.node_overrides
    assert NODE_DOWNSTREAM in policy.node_overrides
    crit = policy.node_overrides[NODE_ROOT]
    assert crit.requirements[0].min_score == 0.8
    assert crit.requirements[0].required_tool_backend == "python.adapter"


def test_m3_rubric_contract_is_canonical():
    """M3: Verify AssessmentRubric has 2 critical dimensions summing to 1.0."""
    rubric = build_rubric()
    assert len(rubric.dimensions) == 2
    assert rubric.dimensions[0].dimension_id == "live_demo"
    assert rubric.dimensions[0].is_critical is True
    assert rubric.dimensions[1].dimension_id == "foundations"
    assert rubric.dimensions[1].is_critical is True
    assert sum(d.weight for d in rubric.dimensions) == 1.0


# =============================================================================
# SCENARIO B.1 TESTS: Execution Success != Mastery
# =============================================================================

@pytest.fixture(scope="module")
def b1_execution(campaign_setup, repo_root: Path):
    setup = campaign_setup
    ws = setup["tmp_dir"] / "ws_b1"
    ws.mkdir()
    shutil.copy(
        repo_root / "scratch" / "fixtures" / "gp_b" / "student_bad_artifact.py",
        ws / "student_script.py",
    )

    req = ExecutionRequest(
        request_id="req-b1-test",
        capability=ToolCapability(capability_name="python.run_script"),
        workspace_id="ws-b1",
        relative_script_path="student_script.py",
        stdin_payload=CANONICAL_STDIN,
        policy=ExecutionPolicy(timeout_seconds=5),
        tier=ExecutionPlaneTier.TIER_0,
    )

    res = setup["execution_adapter"].execute(req, ws)
    obs = setup["execution_adapter"].observe(res)

    asmt = setup["assessment_engine"].assess(
        task=setup["task"],
        rubric=setup["rubric"],
        observation=obs,
        task_revision_id="rev-task-01",
        rubric_revision_id="rev-rubric-01",
        expected_task_sha256=setup["task_sha"],
        expected_rubric_sha256=setup["rubric_sha"],
    )

    now = datetime.now(timezone.utc)
    ctx = SessionProvenanceContext(
        session_id="sess-b1-test",
        student_id=STUDENT_ID,
        resolved_target_node_id=NODE_ROOT,
        roadmap_revision_id=setup["roadmap"].canonical_revision_id,
        policy_revision_id=setup["policy"].canonical_policy_id,
        expected_task_specification_sha256=setup["task_sha"],
        expected_rubric_specification_sha256=setup["rubric_sha"],
        session_started_at=now - timedelta(minutes=10),
        session_is_active=True,
    )

    admission = setup["ingestion_engine"].evaluate_admissibility(asmt, ctx, setup["ledger"])
    rec = setup["ingestion_engine"].build_admitted_record(asmt, ctx, admission.outcome, admission.admission_trace)
    rec = rec.model_copy(
        update={
            "tool_backend": "python.adapter",
            "metadata": {**rec.metadata, "evaluation_attempt_id": ATTEMPT_B1},
        }
    )
    entry = setup["ledger"].append_record(rec)

    state = derive_student_state(
        roadmap=setup["roadmap"],
        policy=setup["policy"],
        ledger=setup["ledger"],
        student_id=STUDENT_ID,
    )

    return {
        "execution_result": res,
        "observation": obs,
        "assessment": asmt,
        "admission": admission,
        "record": rec,
        "entry": entry,
        "state": state,
    }


def test_b1_observation_matches_oracle(b1_execution, oracle: dict):
    """CRIT-01: B.1 observation matches oracle."""
    obs_oracle = oracle["scenarios"]["B1"]["observation"]
    assert b1_execution["execution_result"].exit_code == obs_oracle["exit_code"]
    assert b1_execution["observation"].produced_artifacts[0].file_size_bytes == obs_oracle["artifact_size_bytes"]


def test_b1_evaluation_fails_despite_success_exit(b1_execution):
    """CRIT-02: B.1 emits passed=False despite exit_code=0."""
    assert b1_execution["execution_result"].exit_code == 0
    assert b1_execution["assessment"].aggregation.passed is False
    assert b1_execution["assessment"].aggregation.overall_level == PerformanceLevel.N1_INSUFFICIENT


def test_b1_evidence_is_admitted_as_fail(b1_execution):
    """CRIT-04: S5.2.A admits FAIL evidence into the authoritative ledger."""
    assert b1_execution["admission"].decision == AdmissionDecision.ADMITTED
    assert b1_execution["admission"].outcome == EvidenceOutcome.FAIL
    assert b1_execution["record"].score == 0.0
    assert b1_execution["entry"].entry_index == 0


def test_b1_state_keeps_prog02_locked(b1_execution):
    """CRIT-06: B.1 keeps PROG-01 in IN_PROGRESS and PROG-02 in LOCKED."""
    state = b1_execution["state"]
    ns_root = state.get_node_state(NODE_ROOT)
    ns_down = state.get_node_state(NODE_DOWNSTREAM)

    assert ns_root.status == NodeProgressStatus.IN_PROGRESS
    assert ns_root.evaluation_result.verdict == CriteriaEvaluationVerdict.UNSATISFIED
    assert ns_down.status == NodeProgressStatus.LOCKED


# =============================================================================
# SCENARIO B.2 TESTS: Clean Solution Unlocks Proficiency
# =============================================================================

@pytest.fixture(scope="module")
def b2_execution(campaign_setup, b1_execution, repo_root: Path):
    setup = campaign_setup
    ws = setup["tmp_dir"] / "ws_b2"
    ws.mkdir()
    shutil.copy(
        repo_root / "scratch" / "fixtures" / "gp_b" / "student_clean_solution.py",
        ws / "student_script.py",
    )

    req = ExecutionRequest(
        request_id="req-b2-test",
        capability=ToolCapability(capability_name="python.run_script"),
        workspace_id="ws-b2",
        relative_script_path="student_script.py",
        stdin_payload=CANONICAL_STDIN,
        policy=ExecutionPolicy(timeout_seconds=5),
        tier=ExecutionPlaneTier.TIER_0,
    )

    res = setup["execution_adapter"].execute(req, ws)
    obs = setup["execution_adapter"].observe(res)

    asmt = setup["assessment_engine"].assess(
        task=setup["task"],
        rubric=setup["rubric"],
        observation=obs,
        task_revision_id="rev-task-01",
        rubric_revision_id="rev-rubric-01",
        expected_task_sha256=setup["task_sha"],
        expected_rubric_sha256=setup["rubric_sha"],
    )

    now = datetime.now(timezone.utc)
    ctx = SessionProvenanceContext(
        session_id="sess-b2-test",
        student_id=STUDENT_ID,
        resolved_target_node_id=NODE_ROOT,
        roadmap_revision_id=setup["roadmap"].canonical_revision_id,
        policy_revision_id=setup["policy"].canonical_policy_id,
        expected_task_specification_sha256=setup["task_sha"],
        expected_rubric_specification_sha256=setup["rubric_sha"],
        session_started_at=now - timedelta(minutes=5),
        session_is_active=True,
    )

    admission = setup["ingestion_engine"].evaluate_admissibility(asmt, ctx, setup["ledger"])
    rec = setup["ingestion_engine"].build_admitted_record(asmt, ctx, admission.outcome, admission.admission_trace)
    rec = rec.model_copy(
        update={
            "tool_backend": "python.adapter",
            "metadata": {**rec.metadata, "evaluation_attempt_id": ATTEMPT_B2},
        }
    )
    entry = setup["ledger"].append_record(rec)

    state = derive_student_state(
        roadmap=setup["roadmap"],
        policy=setup["policy"],
        ledger=setup["ledger"],
        student_id=STUDENT_ID,
    )

    return {
        "execution_result": res,
        "observation": obs,
        "assessment": asmt,
        "admission": admission,
        "record": rec,
        "entry": entry,
        "state": state,
    }


def test_b2_observation_matches_oracle(b2_execution, oracle: dict):
    """CRIT-01: B.2 observation matches oracle."""
    obs_oracle = oracle["scenarios"]["B2"]["observation"]
    assert b2_execution["execution_result"].exit_code == obs_oracle["exit_code"]
    assert b2_execution["observation"].produced_artifacts[0].file_size_bytes == obs_oracle["artifact_size_bytes"]


def test_b2_evaluation_passes_with_n3_competent(b2_execution):
    """CRIT-03: B.2 evaluation passes with N3_COMPETENT."""
    assert b2_execution["execution_result"].exit_code == 0
    assert b2_execution["assessment"].aggregation.passed is True
    assert b2_execution["assessment"].aggregation.overall_level == PerformanceLevel.N3_COMPETENT


def test_b2_evidence_is_admitted_as_pass(b2_execution):
    """CRIT-04: S5.2.A admits PASS evidence into the authoritative ledger."""
    assert b2_execution["admission"].decision == AdmissionDecision.ADMITTED
    assert b2_execution["admission"].outcome == EvidenceOutcome.PASS
    assert b2_execution["record"].score == 1.0
    assert b2_execution["entry"].entry_index == 1


def test_b2_state_unlocks_prog02(b2_execution):
    """CRIT-07: B.2 transitions PROG-01 to ASSESSED_PROFICIENT and unlocks PROG-02 to AVAILABLE."""
    state = b2_execution["state"]
    ns_root = state.get_node_state(NODE_ROOT)
    ns_down = state.get_node_state(NODE_DOWNSTREAM)

    assert ns_root.status == NodeProgressStatus.ASSESSED_PROFICIENT
    assert ns_root.evaluation_result.verdict == CriteriaEvaluationVerdict.SATISFIED
    assert ns_down.status == NodeProgressStatus.AVAILABLE


def test_crit_08_execution_success_is_not_mastery(b1_execution, b2_execution):
    """CRIT-08: Invariant Execution Success != Mastery is empirically proven."""
    # In B.1: Process executed with exit_code 0, but failed mastery & PROG-02 stayed LOCKED
    assert b1_execution["execution_result"].exit_code == 0
    assert b1_execution["record"].outcome == EvidenceOutcome.FAIL
    assert b1_execution["state"].get_node_state(NODE_DOWNSTREAM).status == NodeProgressStatus.LOCKED

    # In B.2: Process executed with exit_code 0, passed mastery & unlocked PROG-02 to AVAILABLE
    assert b2_execution["execution_result"].exit_code == 0
    assert b2_execution["record"].outcome == EvidenceOutcome.PASS
    assert b2_execution["state"].get_node_state(NODE_DOWNSTREAM).status == NodeProgressStatus.AVAILABLE


# =============================================================================
# SCENARIO B.3a & B.3b: REPLAY DEFENSE TESTS
# =============================================================================

def test_b3a_idempotent_replay_error(campaign_setup, b2_execution):
    """CRIT-09: Replay of identical assessment (K, R) raises IdempotentReplayError."""
    ledger = campaign_setup["ledger"]
    rec = b2_execution["record"]
    rec_replay = rec.model_copy(update={"record_id": f"ev-retry-{uuid.uuid4().hex[:8]}"})

    with pytest.raises(IdempotentReplayError) as exc_info:
        ledger.append_record(rec_replay)

    assert "Idempotent replay detected" in str(exc_info.value)
    assert ledger.total_entries == 2


def test_b3b_inconsistent_replay_error(campaign_setup, b2_execution):
    """CRIT-10: Divergent replay with same K and divergent R' raises InconsistentReplayError."""
    ledger = campaign_setup["ledger"]
    rec = b2_execution["record"]
    rec_divergent = rec.model_copy(
        update={
            "record_id": f"ev-div-{uuid.uuid4().hex[:8]}",
            "assessment_digest": "e" * 64,
            "score": 0.0,
            "outcome": EvidenceOutcome.FAIL,
        }
    )

    with pytest.raises(InconsistentReplayError) as exc_info:
        ledger.append_record(rec_divergent)

    assert "Inconsistent replay detected" in str(exc_info.value)
    assert ledger.total_entries == 2


def test_ledger_hash_chain_is_valid(campaign_setup):
    """CRIT-05: Ledger maintains a valid cryptographic hash chain."""
    ledger = campaign_setup["ledger"]
    report = ledger.verify_integrity()
    assert report.status == LedgerIntegrityStatus.VALID
    assert report.valid_entries == 2


def test_ledger_cardinality_after_replays(campaign_setup):
    """EXT-04: Total entries in ledger strictly equals 2 after all attempts and replays."""
    ledger = campaign_setup["ledger"]
    assert ledger.total_entries == 2


def test_telemetry_schema_is_valid(repo_root: Path):
    """EXT-03: Verify data/experiments/golden_path_b_telemetry.json exists and is schema-valid."""
    telemetry_file = repo_root / "data" / "experiments" / "golden_path_b_telemetry.json"
    assert telemetry_file.exists(), "Telemetry file must exist"

    with open(telemetry_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["campaign_id"] == "GP-B-V0"
    assert "run_id" in data
    assert "started_at_utc" in data
    assert "finished_at_utc" in data
    assert "scenarios" in data
    assert "B1" in data["scenarios"]
    assert "B2" in data["scenarios"]
    assert "B3a" in data["scenarios"]
    assert "B3b" in data["scenarios"]
    assert data["ledger"]["hash_chain_status"] == "VALID"
    assert data["ledger"]["entry_count"] == 2

    for cid in (
        "CRIT-01", "CRIT-02", "CRIT-03", "CRIT-04", "CRIT-05", "CRIT-06",
        "CRIT-07", "CRIT-08", "CRIT-09", "CRIT-10", "CRIT-11", "CRIT-12",
    ):
        assert data["acceptance_criteria"].get(cid) == "PASS", f"Acceptance criterion {cid} failed in telemetry!"
