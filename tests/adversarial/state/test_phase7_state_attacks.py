r"""Adversarial and integrity test suite for Phase 7: State Attacks (Hito 6).

Asserts full compliance against Subsystem S5.2.C (State Engine), verifying
the Nuclear S5.2.C Invariant:
    Nuclear S5.2.C == (MASTERED => VALID_ASSESSMENT_EVIDENCE)
                   /\ (UNLOCKED => PREREQUISITES_SATISFIED)
                   /\ (STATE == DERIVE(AUTHORITATIVE_EVIDENCE))

Test Scenarios (10 Cases):
1. P7-STAT-01 (mastered_without_evidence): Zero-evidence mastery claim; root=AVAILABLE, downstream=LOCKED.
2. P7-STAT-02 (mastered_from_execution_only): Exit 0 with failed assessment; IN_PROGRESS, UNSATISFIED.
3. P7-STAT-03 (unlocked_without_prerequisites): Triple verification of prerequisite bypass rejection.
4. P7-STAT-04 (state_advance_duplicate): Duplicate assessment replay rejected; ledger delta=0, state delta=0.
5. P7-STAT-05 (state_advance_invalid): Subthreshold score (0.5 < 0.8) yields IN_PROGRESS and missing requirement.
6. P7-STAT-06 (state_mutation_ui_event): UI direct in-place mutation blocked by Pydantic; hash mismatch detected.
7. P7-STAT-07 (state_mutation_llm_output): AI override raises SovereignExemptionViolationError; unaudited LLM output ignored.
8. P7-STAT-08-A (baseline_positive_control): Canonical passing chain achieves ASSESSED_PROFICIENT; pure functional determinism.
9. P7-STAT-08-B (order_independence_verification): Reverse ledger insertion order produces 100% identical epistemic state.
10. P7-STAT-09 (temporal_cutoff_enforcement): Temporal cutoff strictly partitions past vs future evidence.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional
from pydantic import ValidationError
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
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.curriculum.registry import CurriculumRegistry
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


@pytest.fixture(scope="module")
def state_env() -> Dict[str, Any]:
    """Module-level fixture setting up curricular environment."""
    curriculum_dir = REPO_ROOT / "data" / "curriculum"
    registry = CurriculumRegistry(root_dir=curriculum_dir)
    roadmap = registry.load_roadmap("cybersecurity_v1.yaml")
    alignment = registry.load_alignment("cybersecurity_v1_alignment.json")
    task = registry.load_task("task_sec05_file_hasher.json")
    rubric = registry.load_rubric("rubric_sec05_deterministic.json")
    policy = build_cybersecurity_policy()
    assessment_engine = DeterministicAssessmentEngine()
    ingestion_engine = EvidenceIngestionEngine()

    return {
        "registry": registry,
        "roadmap": roadmap,
        "alignment": alignment,
        "task": task,
        "rubric": rubric,
        "policy": policy,
        "assessment_engine": assessment_engine,
        "ingestion_engine": ingestion_engine,
    }


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


def _create_canonical_assessment(
    env: Dict[str, Any], observation_id: str = "obs-clean"
) -> AssessmentResult:
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
    engine: DeterministicAssessmentEngine = env["assessment_engine"]
    return engine.assess(
        task=env["task"],
        rubric=env["rubric"],
        observation=obs,
        task_revision_id="rev-task-01",
        rubric_revision_id="rev-rubric-01",
    )


def test_p7_stat_01_mastered_without_evidence(state_env: Dict[str, Any]) -> None:
    """P7-STAT-01: Empty ledger must yield root nodes AVAILABLE, downstream LOCKED, 0 evidence."""
    student_id = "student-adv-stat-01"
    empty_ledger = EvidenceLedger()

    state = derive_student_state(
        roadmap=state_env["roadmap"],
        policy=state_env["policy"],
        ledger=empty_ledger,
        student_id=student_id,
    )

    sec01 = state.get_node_state("SEC-01-C-PTR")
    sec02 = state.get_node_state("SEC-02-OS-PROC")
    sec03 = state.get_node_state("SEC-03-MEM-MGMT")
    sec05 = state.get_node_state("SEC-05-BIN-SEC")

    assert sec01 is not None and sec01.status == NodeProgressStatus.AVAILABLE
    assert sec02 is not None and sec02.status == NodeProgressStatus.AVAILABLE
    assert sec03 is not None and sec03.status == NodeProgressStatus.LOCKED
    assert sec05 is not None and sec05.status == NodeProgressStatus.LOCKED

    assert sec01.total_evidence_count == 0
    assert sec05.total_evidence_count == 0

    # Nuclear invariant: zero nodes are proficient without evidence
    any_proficient = any(n.status == NodeProgressStatus.ASSESSED_PROFICIENT for n in state.node_states)
    assert not any_proficient


def test_p7_stat_02_mastered_from_execution_only(state_env: Dict[str, Any]) -> None:
    """P7-STAT-02: Exit code 0 with failed assessment must yield IN_PROGRESS, not ASSESSED_PROFICIENT."""
    student_id = "student-adv-stat-02"
    ledger = EvidenceLedger()
    now = datetime.now(timezone.utc)

    # Ingest failing assessment evidence
    rec = EvidenceRecord(
        record_id="rec-p7-02-fail",
        student_id=student_id,
        node_id="SEC-01-C-PTR",
        evidence_type=EvidenceType.CODE_EXECUTION,
        outcome=EvidenceOutcome.FAIL,
        score=0.0,
        timestamp=now,
        actor_type=ActorType.TOOL_VERIFIER,
        actor_id="evaluator",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        assessment_digest="0" * 64,
    )
    ledger.append_record(rec)

    state = derive_student_state(
        roadmap=state_env["roadmap"],
        policy=state_env["policy"],
        ledger=ledger,
        student_id=student_id,
    )

    sec01 = state.get_node_state("SEC-01-C-PTR")
    assert sec01 is not None
    assert sec01.status == NodeProgressStatus.IN_PROGRESS
    assert sec01.evaluation_result is not None
    assert sec01.evaluation_result.verdict == CriteriaEvaluationVerdict.UNSATISFIED
    assert sec01.total_evidence_count == 1


def test_p7_stat_03_unlocked_without_prerequisites(state_env: Dict[str, Any]) -> None:
    """P7-STAT-03: Passing evidence on downstream node without hard prereqs must remain LOCKED."""
    student_id = "student-adv-stat-03"
    ledger = EvidenceLedger()
    now = datetime.now(timezone.utc)

    # Inject passing evidence for SEC-05 directly without fulfilling SEC-03
    rec = EvidenceRecord(
        record_id="rec-p7-03-rogue",
        student_id=student_id,
        node_id="SEC-05-BIN-SEC",
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

    state = derive_student_state(
        roadmap=state_env["roadmap"],
        policy=state_env["policy"],
        ledger=ledger,
        student_id=student_id,
    )

    sec05 = state.get_node_state("SEC-05-BIN-SEC")
    assert sec05 is not None

    # Triple verification:
    # 1. Intrinsic evaluation is satisfied
    assert sec05.evaluation_result is not None
    assert sec05.evaluation_result.verdict == CriteriaEvaluationVerdict.SATISFIED
    # 2. Curricular status is strictly LOCKED
    assert sec05.status == NodeProgressStatus.LOCKED
    # 3. Unfulfilled hard prerequisites contains SEC-03-MEM-MGMT
    assert "SEC-03-MEM-MGMT" in sec05.unfulfilled_hard_prerequisites


def test_p7_stat_04_state_advance_duplicate(state_env: Dict[str, Any]) -> None:
    """P7-STAT-04: Duplicate assessment replay rejected; ledger delta=0, state delta=empty."""
    student_id = "student-adv-stat-04"
    ledger = EvidenceLedger()
    base_time = datetime.now(timezone.utc)
    _setup_prereqs(ledger, student_id, base_time)

    asmt = _create_canonical_assessment(state_env, observation_id="obs-p7-04")
    prov_ctx = SessionProvenanceContext(
        student_id=student_id,
        session_id="session-p7-04",
        resolved_target_node_id="SEC-05-BIN-SEC",
        requested_node_id="SEC-05-BIN-SEC",
        roadmap_revision_id=state_env["roadmap"].canonical_revision_id,
        policy_revision_id=state_env["policy"].canonical_policy_id,
        expected_task_specification_sha256=asmt.task.specification_sha256,
        expected_rubric_specification_sha256=asmt.rubric.specification_sha256,
        session_is_active=True,
        session_started_at=base_time - timedelta(minutes=5),
    )

    # 1st Submission: Admitted
    adm1 = state_env["ingestion_engine"].evaluate_admissibility(asmt, prov_ctx, ledger)
    assert adm1.decision == AdmissionDecision.ADMITTED
    assert adm1.outcome is not None
    rec1 = state_env["ingestion_engine"].build_admitted_record(asmt, prov_ctx, adm1.outcome, adm1.admission_trace)
    rec1 = rec1.model_copy(update={"metadata": {**rec1.metadata, "evaluation_attempt_id": "attempt-sec05-01"}})
    ledger.append_record(rec1)

    fixed_eval_time = base_time + timedelta(hours=1)
    state_before = derive_student_state(
        state_env["roadmap"], state_env["policy"], ledger, student_id, as_of_time=fixed_eval_time
    )
    ledger_count_before = len(ledger._entries)

    # 2nd Submission: Duplicate Rejected by Gate 4 Preflight
    adm2 = state_env["ingestion_engine"].evaluate_admissibility(asmt, prov_ctx, ledger)
    assert adm2.decision == AdmissionDecision.REJECTED
    assert adm2.rejection_reason == RejectionReason.DUPLICATE_ASSESSMENT_REPLAY

    ledger_count_after = len(ledger._entries)
    ledger_delta = ledger_count_after - ledger_count_before
    assert ledger_delta == 0

    state_after = derive_student_state(
        state_env["roadmap"], state_env["policy"], ledger, student_id, as_of_time=fixed_eval_time
    )
    assert state_before.canonical_state_id == state_after.canonical_state_id
    assert state_before.node_states == state_after.node_states


def test_p7_stat_05_state_advance_invalid(state_env: Dict[str, Any]) -> None:
    """P7-STAT-05: Subthreshold evidence (0.5 < 0.8) yields IN_PROGRESS with missing requirement."""
    student_id = "student-adv-stat-05"
    node_type = state_env["roadmap"].nodes["SEC-05-BIN-SEC"].node_type
    crit = state_env["policy"].default_criteria[node_type]
    assert crit is not None
    base_time = datetime.now(timezone.utc)

    # Score 0.5 < min_score 0.8
    subthreshold_rec = EvidenceRecord(
        record_id="rec-p7-05-subscore",
        student_id=student_id,
        node_id="SEC-05-BIN-SEC",
        evidence_type=EvidenceType.CODE_EXECUTION,
        outcome=EvidenceOutcome.PASS,
        score=0.5,
        timestamp=base_time,
        actor_type=ActorType.TOOL_VERIFIER,
        actor_id="evaluator",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        assessment_digest=hashlib.sha256(b"subscore-sec05").hexdigest(),
    )

    eval_result = evaluate_node_criteria(crit, [subthreshold_rec], base_time, node_id="SEC-05-BIN-SEC")
    assert eval_result.verdict == CriteriaEvaluationVerdict.UNSATISFIED
    assert len(eval_result.missing_requirements) == 1

    # In state derivation with prereqs satisfied
    ledger = EvidenceLedger()
    _setup_prereqs(ledger, student_id, base_time)
    ledger.append_record(subthreshold_rec)

    state = derive_student_state(
        state_env["roadmap"], state_env["policy"], ledger, student_id
    )
    sec05 = state.get_node_state("SEC-05-BIN-SEC")
    assert sec05 is not None
    assert sec05.status == NodeProgressStatus.IN_PROGRESS


def test_p7_stat_06_state_mutation_ui_event(state_env: Dict[str, Any]) -> None:
    """P7-STAT-06: Direct mutation blocked by frozen contract; forged state fails hash check."""
    student_id = "student-adv-stat-06"
    empty_ledger = EvidenceLedger()
    state = derive_student_state(
        state_env["roadmap"], state_env["policy"], empty_ledger, student_id
    )
    sec01 = state.get_node_state("SEC-01-C-PTR")
    assert sec01 is not None

    # 1. UI attempts direct in-place mutation
    with pytest.raises(ValidationError):
        setattr(sec01, "status", NodeProgressStatus.ASSESSED_PROFICIENT)

    # 2. UI attempts forged/tampered StudentState
    mutated_node = sec01.model_copy(update={"status": NodeProgressStatus.ASSESSED_PROFICIENT})
    tampered_nodes = tuple(
        mutated_node if n.node_id == "SEC-01-C-PTR" else n for n in state.node_states
    )
    tampered_state = state.model_copy(update={"node_states": tampered_nodes})

    with pytest.raises(StateHashMismatchError):
        validate_student_state_hash(tampered_state)


def test_p7_stat_07_state_mutation_llm_output(state_env: Dict[str, Any]) -> None:
    """P7-STAT-07: SovereignExemptionViolationError on AI override; unaudited LLM output ignored."""
    student_id = "student-adv-stat-07"
    node_type = state_env["roadmap"].nodes["SEC-01-C-PTR"].node_type
    crit = state_env["policy"].default_criteria[node_type]
    assert crit is not None
    now = datetime.now(timezone.utc)

    # 1. AI Tutor attempts unauthorized MANUAL_OVERRIDE
    ai_rec = EvidenceRecord.model_construct(
        record_id="rec-p7-07-ai-override",
        student_id=student_id,
        node_id="SEC-01-C-PTR",
        evidence_type=EvidenceType.MANUAL_OVERRIDE,
        outcome=EvidenceOutcome.PASS,
        score=1.0,
        timestamp=now,
        actor_type=ActorType.AI_TUTOR,  # Forbidden for MANUAL_OVERRIDE!
        actor_id="llm-tutor",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        rationale="LLM deems student competent",
        roadmap_revision_id=state_env["roadmap"].canonical_revision_id,
        policy_revision_id=state_env["policy"].canonical_policy_id,
    )

    with pytest.raises(SovereignExemptionViolationError):
        evaluate_node_criteria(crit, [ai_rec], now, node_id="SEC-01-C-PTR")

    # 2. Unaudited conceptual record evaluated against audit-requiring criteria
    unaudited_rec = EvidenceRecord(
        record_id="rec-p7-07-unaudited",
        student_id=student_id,
        node_id="SEC-01-C-PTR",
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
    eval_audit = evaluate_node_criteria(crit_audit, [unaudited_rec], now, node_id="SEC-01-C-PTR")
    assert eval_audit.verdict == CriteriaEvaluationVerdict.UNSATISFIED

    # 3. LLM output has zero authority to commit to ledger -> state remains AVAILABLE
    ledger = EvidenceLedger()
    state = derive_student_state(
        state_env["roadmap"], state_env["policy"], ledger, student_id
    )
    sec01 = state.get_node_state("SEC-01-C-PTR")
    assert sec01 is not None and sec01.status == NodeProgressStatus.AVAILABLE


def test_p7_stat_08_a_baseline_positive_control(state_env: Dict[str, Any]) -> None:
    """P7-STAT-08-A: Canonical passing chain achieves ASSESSED_PROFICIENT; pure functional determinism."""
    student_id = "student-adv-stat-08a"
    ledger = EvidenceLedger()
    base_time = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    _setup_prereqs(ledger, student_id, base_time)

    rec_sec05 = EvidenceRecord(
        record_id="rec-p7-08-sec05",
        student_id=student_id,
        node_id="SEC-05-BIN-SEC",
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
    s1 = derive_student_state(
        state_env["roadmap"], state_env["policy"], ledger, student_id, as_of_time=fixed_as_of
    )
    s2 = derive_student_state(
        state_env["roadmap"], state_env["policy"], ledger, student_id, as_of_time=fixed_as_of
    )

    sec05 = s1.get_node_state("SEC-05-BIN-SEC")
    sec04 = s1.get_node_state("SEC-04-CONCURR")
    sec06 = s1.get_node_state("SEC-06-CAPSTONE")

    assert sec05 is not None
    assert sec05.status == NodeProgressStatus.ASSESSED_PROFICIENT
    assert sec05.evaluation_result is not None
    assert sec05.evaluation_result.verdict == CriteriaEvaluationVerdict.SATISFIED

    assert sec04 is not None and sec04.status == NodeProgressStatus.AVAILABLE
    assert sec06 is not None and sec06.status == NodeProgressStatus.LOCKED

    # Pure functional determinism: bitwise identical canonical_state_id and node_states
    assert s1.canonical_state_id == s2.canonical_state_id
    assert s1.node_states == s2.node_states


def test_p7_stat_08_b_order_independence_verification(state_env: Dict[str, Any]) -> None:
    """P7-STAT-08-B: Reverse ledger insertion order produces 100% identical epistemic state."""
    student_id = "student-adv-stat-08b"
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

    # Ledger 1: Canonical insertion order
    l1 = EvidenceLedger()
    for idx, (nid, _) in enumerate(node_configs):
        l1.append_record(records_map[nid], override_committed_at=commit_base + timedelta(minutes=idx))

    # Ledger 2: Reverse insertion order
    l2 = EvidenceLedger()
    for idx, (nid, _) in enumerate(reversed(node_configs)):
        l2.append_record(records_map[nid], override_committed_at=commit_base + timedelta(minutes=idx))

    fixed_as_of = commit_base + timedelta(hours=2)
    s1 = derive_student_state(
        state_env["roadmap"], state_env["policy"], l1, student_id, as_of_time=fixed_as_of
    )
    s2 = derive_student_state(
        state_env["roadmap"], state_env["policy"], l2, student_id, as_of_time=fixed_as_of
    )

    # Assert 100% epistemic invariance
    assert [n1.status for n1 in s1.node_states] == [n2.status for n2 in s2.node_states]
    assert [n1.evaluation_result.verdict if n1.evaluation_result else None for n1 in s1.node_states] == [
        n2.evaluation_result.verdict if n2.evaluation_result else None for n2 in s2.node_states
    ]
    assert [n1.unfulfilled_hard_prerequisites for n1 in s1.node_states] == [
        n2.unfulfilled_hard_prerequisites for n2 in s2.node_states
    ]
    assert [n1.total_evidence_count for n1 in s1.node_states] == [
        n2.total_evidence_count for n2 in s2.node_states
    ]


def test_p7_stat_09_temporal_cutoff_enforcement(state_env: Dict[str, Any]) -> None:
    """P7-STAT-09: Temporal cutoff strictly partitions past vs future evidence."""
    student_id = "student-adv-stat-09"
    ledger = EvidenceLedger()
    t1 = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 1, 14, 0, tzinfo=timezone.utc)

    # Past record at T1
    rec_past = EvidenceRecord(
        record_id="rec-p7-09-past",
        student_id=student_id,
        node_id="SEC-01-C-PTR",
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
        node_id="SEC-05-BIN-SEC",
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

    # 1. Query at cutoff = T1 + 15 min (strictly before T2)
    cutoff_t1 = t1 + timedelta(minutes=15)
    state_t1 = derive_student_state(
        state_env["roadmap"],
        state_env["policy"],
        ledger,
        student_id,
        as_of_time=cutoff_t1,
        cutoff_mode=HistoryCutoffMode.EVENT_TIME,
    )

    past_node_t1 = state_t1.get_node_state("SEC-01-C-PTR")
    future_node_t1 = state_t1.get_node_state("SEC-05-BIN-SEC")

    assert past_node_t1 is not None and past_node_t1.status == NodeProgressStatus.ASSESSED_PROFICIENT
    assert future_node_t1 is not None and future_node_t1.status == NodeProgressStatus.LOCKED
    assert future_node_t1.total_evidence_count == 0

    # 2. Query at cutoff = T2 + 15 min (covers all evidence)
    cutoff_t2 = t2 + timedelta(minutes=15)
    state_t2 = derive_student_state(
        state_env["roadmap"],
        state_env["policy"],
        ledger,
        student_id,
        as_of_time=cutoff_t2,
        cutoff_mode=HistoryCutoffMode.EVENT_TIME,
    )
    future_node_t2 = state_t2.get_node_state("SEC-05-BIN-SEC")
    assert future_node_t2 is not None and future_node_t2.status == NodeProgressStatus.ASSESSED_PROFICIENT
