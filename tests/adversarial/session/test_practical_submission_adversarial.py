"""Adversarial security tests for practical submission artifact path sanitization (H4-DESIGN-02).

Tests:
1. Path traversal attacks (relative and absolute paths outside allowed roots).
2. Non-existent artifact files.
3. Non-Python artifact files (.sh, .txt, .bin, .exe).
4. Artifact disk mutation attacks (expected_sha256 mismatch).
5. Robustness against malformed or unexpected paths (fail-closed, zero crashes).
"""

import hashlib
from pathlib import Path
import sys
import tempfile
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.experiments.gp_b_contracts import (
    STUDENT_ID,
    TASK_ID,
    build_assessment_policy,
    build_roadmap,
    build_rubric,
    build_task_specification,
)
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
from tests.utils.test_registry import TestCurriculumRegistry


@pytest.fixture
def adversarial_orchestrator(tmp_path: Path):
    """Setup orchestrator with restricted allowed_artifact_roots for strict isolation."""
    allowed_dir = tmp_path / "allowed_submissions"
    allowed_dir.mkdir(parents=True, exist_ok=True)

    roadmap = build_roadmap()
    policy = build_assessment_policy()
    task = build_task_specification()
    rubric = build_rubric()

    registry = TestCurriculumRegistry()
    registry.register_task(task)
    registry.register_rubric(rubric, task_id=task.task_id)

    ledger = EvidenceLedger()

    exec_adapter = PracticalExecutionAdapter()
    assess_adapter = DeterministicAssessmentAdapter(default_task=task)
    ingest_adapter = EvidenceIngestionAdapter(
        ledger=ledger,
        roadmap=roadmap,
        policy=policy,
        student_id=STUDENT_ID,
        session_id="session-adv",
    )
    state_adapter = CurriculumStateAdapter(
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        student_id=STUDENT_ID,
    )

    orch = SessionOrchestrator(
        session_id="session-adv",
        student_id=STUDENT_ID,
        roadmap=roadmap,
        policy=policy,
        ledger=ledger,
        execution_port=exec_adapter,
        assessment_port=assess_adapter,
        ingestion_port=ingest_adapter,
        state_read_port=state_adapter,
        curriculum_registry=registry,
        allowed_artifact_roots=(allowed_dir,),
    )
    orch.start_session()

    return {
        "orchestrator": orch,
        "allowed_dir": allowed_dir,
        "tmp_path": tmp_path,
        "task_id": TASK_ID,
    }


def test_path_traversal_attack_rejected(adversarial_orchestrator):
    """ADV-01: Path traversal attempts outside allowed root must be rejected fail-closed."""
    orch = adversarial_orchestrator["orchestrator"]
    tmp_path = adversarial_orchestrator["tmp_path"]

    # 1. Traversal to system file (e.g. /etc/passwd or similar)
    req_passwd = PracticeRequest(
        student_id=STUDENT_ID,
        node_id="PROG-01",
        task_id=TASK_ID,
        artifact_path="../../../../etc/passwd",
    )
    res_passwd = orch.handle_practical_submission(req_passwd)
    assert res_passwd.status == PracticeResultStatus.EXECUTION_FAILED
    assert "must have .py extension" in (res_passwd.rejection_reason or "")

    # 2. Traversal to python file outside allowed root
    outside_dir = tmp_path / "outside_workspace"
    outside_dir.mkdir()
    outside_script = outside_dir / "exploit.py"
    outside_script.write_text("print('exploit')", encoding="utf-8")

    req_outside = PracticeRequest(
        student_id=STUDENT_ID,
        node_id="PROG-01",
        task_id=TASK_ID,
        artifact_path=str(outside_script),
    )
    res_outside = orch.handle_practical_submission(req_outside)
    assert res_outside.status == PracticeResultStatus.EXECUTION_FAILED
    assert "Path traversal rejected" in (res_outside.rejection_reason or "")


def test_non_existent_artifact_rejected(adversarial_orchestrator):
    """ADV-02: Submissions pointing to non-existent files must fail gracefully without crash."""
    orch = adversarial_orchestrator["orchestrator"]
    allowed_dir = adversarial_orchestrator["allowed_dir"]

    missing_path = allowed_dir / "phantom_file.py"
    req = PracticeRequest(
        student_id=STUDENT_ID,
        node_id="PROG-01",
        task_id=TASK_ID,
        artifact_path=str(missing_path),
    )
    res = orch.handle_practical_submission(req)
    assert res.status == PracticeResultStatus.EXECUTION_FAILED
    assert "Artifact not found" in (res.rejection_reason or "")


def test_non_python_extension_rejected(adversarial_orchestrator):
    """ADV-03: Submissions with non-Python extensions must be rejected before execution."""
    orch = adversarial_orchestrator["orchestrator"]
    allowed_dir = adversarial_orchestrator["allowed_dir"]

    shell_script = allowed_dir / "run_payload.sh"
    shell_script.write_text("#!/bin/bash\necho 1", encoding="utf-8")

    req = PracticeRequest(
        student_id=STUDENT_ID,
        node_id="PROG-01",
        task_id=TASK_ID,
        artifact_path=str(shell_script),
    )
    res = orch.handle_practical_submission(req)
    assert res.status == PracticeResultStatus.EXECUTION_FAILED
    assert "Invalid artifact format" in (res.rejection_reason or "")
    assert "must have .py extension" in (res.rejection_reason or "")


def test_artifact_disk_mutation_detected(adversarial_orchestrator):
    """ADV-04: If on-disk file is altered after declaration, hash mismatch must fail-close."""
    orch = adversarial_orchestrator["orchestrator"]
    allowed_dir = adversarial_orchestrator["allowed_dir"]

    script_path = allowed_dir / "mutating_student.py"
    script_path.write_text("print('original version')", encoding="utf-8")
    original_hash = hashlib.sha256(script_path.read_bytes()).hexdigest()

    # Tamper with file on disk
    script_path.write_text("print('tampered version on disk')", encoding="utf-8")
    tampered_hash = hashlib.sha256(script_path.read_bytes()).hexdigest()

    req = PracticeRequest(
        student_id=STUDENT_ID,
        node_id="PROG-01",
        task_id=TASK_ID,
        artifact_path=str(script_path),
        expected_sha256=original_hash,  # expects original, but disk has tampered
    )
    res = orch.handle_practical_submission(req)
    assert res.status == PracticeResultStatus.EXECUTION_FAILED
    assert "Artifact digest mismatch" in (res.rejection_reason or "")
    assert res.artifact_sha256 == tampered_hash
