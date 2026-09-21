"""Adversarial and security test suite for Phase 5: Assessment Attacks (Hito 6).

Asserts full compliance against Subsystem S9.1 (Deterministic Assessment Engine),
verifying the sovereign deterministic authority invariants:
    1. Zero LLM / pure determinism (latency < 10ms, no external models).
    2. Non-average policy aggregation (no arithmetic compensation under allow_compensation=false).
    3. Cryptographic specification binding (canonical SHA-256 validation).
    4. Honest abstention semantics (INSUFFICIENT_OBSERVATION -> INCONCLUSIVE, no regression).

Tests:
1. P5-ASMT-01 (perfect_execution_failed_rubric): Exit 0 but artifact 200B > 128B max fails rubric.
2. P5-ASMT-02-A (partial_rubric_non_compensation): live_demo=N1, foundations=N4 cannot compensate.
3. P5-ASMT-02-B (partial_rubric_non_compensation_inverted): live_demo=N4, foundations=N1 cannot compensate.
4. P5-ASMT-03 (missing_artifact): Exit 0 but empty artifacts produces ARTIFACT_VERIFIED_ABSENT.
5. P5-ASMT-04 (wrong_artifact): Produces unexpected file; expected artifact verified absent.
6. P5-ASMT-05 (tampered_specification): Mismatched specification SHA-256 raises SpecificationIntegrityError.
7. P5-ASMT-06 (invalid_metadata_omitted): Truncated observation yields INSUFFICIENT_OBSERVATION & INCONCLUSIVE without regression.
8. P5-ASMT-07 (baseline_positive_control): Clean 64B artifact earns N3_COMPETENT and ASSESSED_PROFICIENT.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Tuple
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.experiments.run_golden_path_e2e import build_cybersecurity_policy
from study_engine.assessment.aggregator import aggregate_evaluations
from study_engine.assessment.service import (
    DeterministicAssessmentEngine,
    SpecificationIntegrityError,
)
from study_engine.contracts.assessment import (
    AssessmentResult,
    AssessmentStatus,
    DimensionEvaluation,
    FactObservability,
    InstrumentalFactType,
)
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.contracts.evidence_ingestion import SessionProvenanceContext
from study_engine.contracts.execution import (
    ArtifactCollectionSummary,
    ExecutionObservation,
    ExecutionStatus,
    ObservedArtifact,
    ProcessTelemetry,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.session.adapters import CurriculumStateAdapter
from study_engine.state.ingestion_engine import EvidenceIngestionEngine
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.policy_contracts import (
    ActorType,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)
from study_engine.state.state_contracts import NodeProgressStatus
from study_engine.state.state_engine import derive_student_state


@pytest.fixture(scope="module")
def phase5_setup() -> Dict[str, Any]:
    """Module-level setup for curriculum registry, task, rubric, policy, and engine."""
    curriculum_dir = REPO_ROOT / "data" / "curriculum"
    registry = CurriculumRegistry(root_dir=curriculum_dir)
    roadmap = registry.load_roadmap("cybersecurity_v1.yaml")
    alignment = registry.load_alignment("cybersecurity_v1_alignment.json")
    task = registry.load_task("task_sec05_file_hasher.json")
    rubric = registry.load_rubric("rubric_sec05_deterministic.json")
    policy = build_cybersecurity_policy()
    engine = DeterministicAssessmentEngine()
    ingestion_engine = EvidenceIngestionEngine()

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
        "engine": engine,
        "ingestion_engine": ingestion_engine,
        "oracle": oracle["phase_5_assessment_attacks"],
    }


def _setup_student_ledger(
    student_id: str,
    include_sec05_mastery: bool = False,
) -> EvidenceLedger:
    """Helper to populate isolated student ledger with prerequisites."""
    ledger = EvidenceLedger()
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

    if include_sec05_mastery:
        sec05_rec = EvidenceRecord(
            record_id=f"ev-baseline-sec05-prior-{student_id}",
            student_id=student_id,
            node_id="SEC-05-BIN-SEC",
            evidence_type=EvidenceType.CODE_EXECUTION,
            outcome=EvidenceOutcome.PASS,
            score=1.0,
            timestamp=now - timedelta(minutes=10),
            actor_type=ActorType.TOOL_VERIFIER,
            actor_id="prior-assessor",
            authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
            assessment_digest=hashlib.sha256(f"sec05-prior-{student_id}".encode("utf-8")).hexdigest(),
            overall_level=PerformanceLevel.N3_COMPETENT,
        )
        ledger.append_record(sec05_rec)

    return ledger


def test_p5_asmt_01_perfect_execution_failed_rubric(phase5_setup: Dict[str, Any]) -> None:
    """P5-ASMT-01: Exit code 0, 100ms, but artifact 200B > 128B max fails rubric."""
    engine: DeterministicAssessmentEngine = phase5_setup["engine"]
    task = phase5_setup["task"]
    rubric = phase5_setup["rubric"]
    ingestion: EvidenceIngestionEngine = phase5_setup["ingestion_engine"]
    roadmap = phase5_setup["roadmap"]
    policy = phase5_setup["policy"]

    student_id = "student-test-p5-01"
    ledger = _setup_student_ledger(student_id)

    obs = ExecutionObservation(
        observation_id="obs-p5-01-test",
        execution_id="exec-p5-01-test",
        tool_name="python.adapter",
        status=ExecutionStatus.COMPLETED,
        exit_code=0,
        telemetry=ProcessTelemetry(duration_ms=100.0),
        produced_artifacts=(
            ObservedArtifact(
                artifact_id="art-01",
                relative_path="output_hash.txt",
                file_size_bytes=200,
                sha256_digest="a" * 64,
            ),
        ),
    )

    t0 = time.perf_counter()
    res = engine.assess(task, rubric, obs, "rev-task-01", "rev-rubric-01")
    latency_ms = (time.perf_counter() - t0) * 1000.0

    assert latency_ms < 10.0, f"Latency SLA exceeded: {latency_ms:.2f}ms"
    assert res.aggregation.passed is False
    assert res.aggregation.overall_level == PerformanceLevel.N1_INSUFFICIENT
    assert "live_demo" in res.aggregation.critical_dimension_failures

    # Admission & Ingestion
    prov_ctx = SessionProvenanceContext(
        student_id=student_id,
        session_id="session-test-p5-01",
        resolved_target_node_id="SEC-05-BIN-SEC",
        requested_node_id="SEC-05-BIN-SEC",
        roadmap_revision_id=roadmap.canonical_revision_id,
        policy_revision_id=policy.canonical_policy_id,
        expected_task_specification_sha256=res.task.specification_sha256,
        expected_rubric_specification_sha256=res.rubric.specification_sha256,
        session_is_active=True,
        session_started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    admission = ingestion.evaluate_admissibility(res, prov_ctx, ledger)
    assert admission.outcome == EvidenceOutcome.FAIL

    rec = ingestion.build_admitted_record(res, prov_ctx, admission.outcome, admission.admission_trace)
    assert rec.score == 0.0
    ledger.append_record(rec)

    # State verification: node remains IN_PROGRESS, no mastery
    state = derive_student_state(roadmap, policy, ledger, student_id)
    sec05 = state.get_node_state("SEC-05-BIN-SEC")
    assert sec05 is not None
    assert sec05.status == NodeProgressStatus.IN_PROGRESS


def test_p5_asmt_02_a_partial_rubric_non_compensation(phase5_setup: Dict[str, Any]) -> None:
    """P5-ASMT-02-A: live_demo=N1, foundations=N4 cannot compensate under allow_compensation=false."""
    rubric = phase5_setup["rubric"]
    dim_evals = (
        DimensionEvaluation(
            dimension_id="live_demo",
            status=AssessmentStatus.ASSESSED,
            assigned_level=PerformanceLevel.N1_INSUFFICIENT,
            passed_minimum=False,
            is_critical=True,
            evidence_evaluative_fact_ids=("eval-live-demo-fail",),
            evaluation_rationale="Live demo failed",
        ),
        DimensionEvaluation(
            dimension_id="foundations",
            status=AssessmentStatus.ASSESSED,
            assigned_level=PerformanceLevel.N4_EXCELLENT,
            passed_minimum=True,
            is_critical=True,
            evidence_evaluative_fact_ids=("eval-foundations-pass",),
            evaluation_rationale="Foundations passed",
        ),
    )

    t0 = time.perf_counter()
    agg = aggregate_evaluations(rubric, dim_evals)
    latency_ms = (time.perf_counter() - t0) * 1000.0

    assert latency_ms < 10.0
    assert agg.passed is False
    assert agg.overall_level == PerformanceLevel.N1_INSUFFICIENT
    assert agg.critical_dimension_failures == ("live_demo",)
    assert len(agg.compensation_rules_applied) == 0


def test_p5_asmt_02_b_partial_rubric_non_compensation_inverted(phase5_setup: Dict[str, Any]) -> None:
    """P5-ASMT-02-B: live_demo=N4, foundations=N1 cannot compensate (symmetry invariant)."""
    rubric = phase5_setup["rubric"]
    dim_evals = (
        DimensionEvaluation(
            dimension_id="live_demo",
            status=AssessmentStatus.ASSESSED,
            assigned_level=PerformanceLevel.N4_EXCELLENT,
            passed_minimum=True,
            is_critical=True,
            evidence_evaluative_fact_ids=("eval-live-demo-pass",),
            evaluation_rationale="Live demo passed",
        ),
        DimensionEvaluation(
            dimension_id="foundations",
            status=AssessmentStatus.ASSESSED,
            assigned_level=PerformanceLevel.N1_INSUFFICIENT,
            passed_minimum=False,
            is_critical=True,
            evidence_evaluative_fact_ids=("eval-foundations-fail",),
            evaluation_rationale="Foundations failed",
        ),
    )

    t0 = time.perf_counter()
    agg = aggregate_evaluations(rubric, dim_evals)
    latency_ms = (time.perf_counter() - t0) * 1000.0

    assert latency_ms < 10.0
    assert agg.passed is False
    assert agg.overall_level == PerformanceLevel.N1_INSUFFICIENT
    assert agg.critical_dimension_failures == ("foundations",)
    assert len(agg.compensation_rules_applied) == 0


def test_p5_asmt_03_missing_artifact(phase5_setup: Dict[str, Any]) -> None:
    """P5-ASMT-03: Process exits cleanly 0 but produces no artifacts (verified absent)."""
    engine: DeterministicAssessmentEngine = phase5_setup["engine"]
    task = phase5_setup["task"]
    rubric = phase5_setup["rubric"]
    ingestion: EvidenceIngestionEngine = phase5_setup["ingestion_engine"]
    roadmap = phase5_setup["roadmap"]
    policy = phase5_setup["policy"]

    student_id = "student-test-p5-03"
    ledger = _setup_student_ledger(student_id)

    obs = ExecutionObservation(
        observation_id="obs-p5-03-test",
        execution_id="exec-p5-03-test",
        tool_name="python.adapter",
        status=ExecutionStatus.COMPLETED,
        exit_code=0,
        telemetry=ProcessTelemetry(duration_ms=100.0),
        produced_artifacts=(),
    )

    t0 = time.perf_counter()
    res = engine.assess(task, rubric, obs, "rev-task-01", "rev-rubric-01")
    latency_ms = (time.perf_counter() - t0) * 1000.0

    assert latency_ms < 10.0
    assert res.aggregation.passed is False
    assert res.aggregation.overall_level == PerformanceLevel.N1_INSUFFICIENT

    # Verify presence of ARTIFACT_VERIFIED_ABSENT fact
    abs_facts = [
        f
        for f in res.instrumental_facts
        if f.fact_type == InstrumentalFactType.ARTIFACT_VERIFIED_ABSENT
    ]
    assert len(abs_facts) == 1
    assert abs_facts[0].fact_value == "output_hash.txt"
    assert abs_facts[0].observability == FactObservability.VERIFIED_ABSENCE

    # Admission & Ingestion
    prov_ctx = SessionProvenanceContext(
        student_id=student_id,
        session_id="session-test-p5-03",
        resolved_target_node_id="SEC-05-BIN-SEC",
        requested_node_id="SEC-05-BIN-SEC",
        roadmap_revision_id=roadmap.canonical_revision_id,
        policy_revision_id=policy.canonical_policy_id,
        expected_task_specification_sha256=res.task.specification_sha256,
        expected_rubric_specification_sha256=res.rubric.specification_sha256,
        session_is_active=True,
        session_started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    admission = ingestion.evaluate_admissibility(res, prov_ctx, ledger)
    assert admission.outcome == EvidenceOutcome.FAIL

    rec = ingestion.build_admitted_record(res, prov_ctx, admission.outcome, admission.admission_trace)
    assert rec.score == 0.0
    ledger.append_record(rec)

    # State verification: node remains IN_PROGRESS
    state = derive_student_state(roadmap, policy, ledger, student_id)
    sec05 = state.get_node_state("SEC-05-BIN-SEC")
    assert sec05 is not None
    assert sec05.status == NodeProgressStatus.IN_PROGRESS


def test_p5_asmt_04_wrong_artifact(phase5_setup: Dict[str, Any]) -> None:
    """P5-ASMT-04: Process produces unexpected_binary.bin instead of output_hash.txt."""
    engine: DeterministicAssessmentEngine = phase5_setup["engine"]
    task = phase5_setup["task"]
    rubric = phase5_setup["rubric"]
    ingestion: EvidenceIngestionEngine = phase5_setup["ingestion_engine"]
    roadmap = phase5_setup["roadmap"]
    policy = phase5_setup["policy"]

    student_id = "student-test-p5-04"
    ledger = _setup_student_ledger(student_id)

    obs = ExecutionObservation(
        observation_id="obs-p5-04-test",
        execution_id="exec-p5-04-test",
        tool_name="python.adapter",
        status=ExecutionStatus.COMPLETED,
        exit_code=0,
        telemetry=ProcessTelemetry(duration_ms=100.0),
        produced_artifacts=(
            ObservedArtifact(
                artifact_id="art-wrong",
                relative_path="unexpected_binary.bin",
                file_size_bytes=64,
                sha256_digest="b" * 64,
            ),
        ),
    )

    t0 = time.perf_counter()
    res = engine.assess(task, rubric, obs, "rev-task-01", "rev-rubric-01")
    latency_ms = (time.perf_counter() - t0) * 1000.0

    assert latency_ms < 10.0
    assert res.aggregation.passed is False
    assert res.aggregation.overall_level == PerformanceLevel.N1_INSUFFICIENT

    # Expected artifact verified absent
    abs_facts = [
        f
        for f in res.instrumental_facts
        if f.fact_type == InstrumentalFactType.ARTIFACT_VERIFIED_ABSENT
    ]
    assert len(abs_facts) == 1
    assert abs_facts[0].fact_value == "output_hash.txt"

    # Admission & Ingestion
    prov_ctx = SessionProvenanceContext(
        student_id=student_id,
        session_id="session-test-p5-04",
        resolved_target_node_id="SEC-05-BIN-SEC",
        requested_node_id="SEC-05-BIN-SEC",
        roadmap_revision_id=roadmap.canonical_revision_id,
        policy_revision_id=policy.canonical_policy_id,
        expected_task_specification_sha256=res.task.specification_sha256,
        expected_rubric_specification_sha256=res.rubric.specification_sha256,
        session_is_active=True,
        session_started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    admission = ingestion.evaluate_admissibility(res, prov_ctx, ledger)
    assert admission.outcome == EvidenceOutcome.FAIL

    rec = ingestion.build_admitted_record(res, prov_ctx, admission.outcome, admission.admission_trace)
    ledger.append_record(rec)

    state = derive_student_state(roadmap, policy, ledger, student_id)
    sec05 = state.get_node_state("SEC-05-BIN-SEC")
    assert sec05 is not None
    assert sec05.status == NodeProgressStatus.IN_PROGRESS


def test_p5_asmt_05_tampered_specification(phase5_setup: Dict[str, Any]) -> None:
    """P5-ASMT-05: Mismatched specification SHA-256 raises SpecificationIntegrityError at Step 1."""
    engine: DeterministicAssessmentEngine = phase5_setup["engine"]
    task = phase5_setup["task"]
    rubric = phase5_setup["rubric"]

    obs = ExecutionObservation(
        observation_id="obs-p5-05-test",
        execution_id="exec-p5-05-test",
        tool_name="python.adapter",
        status=ExecutionStatus.COMPLETED,
        exit_code=0,
        telemetry=ProcessTelemetry(duration_ms=100.0),
        produced_artifacts=(),
    )

    t0 = time.perf_counter()
    with pytest.raises(SpecificationIntegrityError) as exc_info:
        engine.assess(
            task=task,
            rubric=rubric,
            observation=obs,
            task_revision_id="rev-task-01",
            rubric_revision_id="rev-rubric-01",
            expected_task_sha256="0" * 64,
        )
    latency_ms = (time.perf_counter() - t0) * 1000.0

    assert latency_ms < 10.0
    assert "Task specification SHA-256 mismatch" in str(exc_info.value)


def test_p5_asmt_06_honest_abstention_non_regression(phase5_setup: Dict[str, Any]) -> None:
    """P5-ASMT-06: Truncated observation yields INSUFFICIENT_OBSERVATION & INCONCLUSIVE without regression."""
    engine: DeterministicAssessmentEngine = phase5_setup["engine"]
    task = phase5_setup["task"]
    rubric = phase5_setup["rubric"]
    ingestion: EvidenceIngestionEngine = phase5_setup["ingestion_engine"]
    roadmap = phase5_setup["roadmap"]
    policy = phase5_setup["policy"]

    # Student with prior mastery (ASSESSED_PROFICIENT)
    student_id = "student-test-p5-06"
    ledger = _setup_student_ledger(student_id, include_sec05_mastery=True)

    # Initial state check
    state_init = derive_student_state(roadmap, policy, ledger, student_id)
    sec05_init = state_init.get_node_state("SEC-05-BIN-SEC")
    assert sec05_init is not None
    assert sec05_init.status == NodeProgressStatus.ASSESSED_PROFICIENT

    # Truncated observation
    obs = ExecutionObservation(
        observation_id="obs-p5-06-test",
        execution_id="exec-p5-06-test",
        tool_name="python.adapter",
        status=ExecutionStatus.COMPLETED,
        exit_code=0,
        telemetry=ProcessTelemetry(duration_ms=100.0),
        produced_artifacts=(),
        artifact_summary=ArtifactCollectionSummary(
            artifacts_discovered=1,
            artifacts_collected=0,
            artifacts_omitted=1,
            collection_truncated=True,
        ),
    )

    t0 = time.perf_counter()
    res = engine.assess(task, rubric, obs, "rev-task-01", "rev-rubric-01")
    latency_ms = (time.perf_counter() - t0) * 1000.0

    assert latency_ms < 10.0
    assert res.aggregation.passed is False
    assert res.aggregation.overall_level is None
    assert "live_demo" in res.aggregation.insufficient_dimensions

    # Verify fact extractor emitted ARTIFACT_OMITTED_BY_LIMIT
    omit_facts = [
        f
        for f in res.instrumental_facts
        if f.fact_type == InstrumentalFactType.ARTIFACT_OMITTED_BY_LIMIT
    ]
    assert len(omit_facts) == 1
    assert omit_facts[0].fact_value == "output_hash.txt"

    # Evidence ingestion: outcome must be INCONCLUSIVE, NOT FAIL!
    prov_ctx = SessionProvenanceContext(
        student_id=student_id,
        session_id="session-test-p5-06",
        resolved_target_node_id="SEC-05-BIN-SEC",
        requested_node_id="SEC-05-BIN-SEC",
        roadmap_revision_id=roadmap.canonical_revision_id,
        policy_revision_id=policy.canonical_policy_id,
        expected_task_specification_sha256=res.task.specification_sha256,
        expected_rubric_specification_sha256=res.rubric.specification_sha256,
        session_is_active=True,
        session_started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    admission = ingestion.evaluate_admissibility(res, prov_ctx, ledger)
    assert admission.outcome == EvidenceOutcome.INCONCLUSIVE

    rec = ingestion.build_admitted_record(res, prov_ctx, admission.outcome, admission.admission_trace)
    assert rec.outcome == EvidenceOutcome.INCONCLUSIVE
    assert rec.overall_level is None
    ledger.append_record(rec)

    # State verification: Non-regression invariant! Prior ASSESSED_PROFICIENT state must be preserved!
    state_after = derive_student_state(roadmap, policy, ledger, student_id)
    sec05_after = state_after.get_node_state("SEC-05-BIN-SEC")
    assert sec05_after is not None
    assert sec05_after.status == NodeProgressStatus.ASSESSED_PROFICIENT, (
        f"Regression detected! Status became {sec05_after.status} instead of remaining ASSESSED_PROFICIENT"
    )


def test_p5_asmt_07_baseline_positive_control(phase5_setup: Dict[str, Any]) -> None:
    """P5-ASMT-07: Positive control earns N3_COMPETENT and ASSESSED_PROFICIENT."""
    engine: DeterministicAssessmentEngine = phase5_setup["engine"]
    task = phase5_setup["task"]
    rubric = phase5_setup["rubric"]
    ingestion: EvidenceIngestionEngine = phase5_setup["ingestion_engine"]
    roadmap = phase5_setup["roadmap"]
    policy = phase5_setup["policy"]

    student_id = "student-test-p5-07"
    ledger = _setup_student_ledger(student_id)

    obs = ExecutionObservation(
        observation_id="obs-p5-07-test",
        execution_id="exec-p5-07-test",
        tool_name="python.adapter",
        status=ExecutionStatus.COMPLETED,
        exit_code=0,
        telemetry=ProcessTelemetry(duration_ms=150.0),
        produced_artifacts=(
            ObservedArtifact(
                artifact_id="art-clean-07",
                relative_path="output_hash.txt",
                file_size_bytes=64,
                sha256_digest="c" * 64,
            ),
        ),
        artifact_summary=ArtifactCollectionSummary(
            artifacts_discovered=1,
            artifacts_collected=1,
            artifacts_omitted=0,
            collection_truncated=False,
        ),
    )

    t0 = time.perf_counter()
    res = engine.assess(task, rubric, obs, "rev-task-01", "rev-rubric-01")
    latency_ms = (time.perf_counter() - t0) * 1000.0

    assert latency_ms < 10.0
    assert res.aggregation.passed is True
    assert res.aggregation.overall_level == PerformanceLevel.N3_COMPETENT
    assert len(res.aggregation.critical_dimension_failures) == 0

    # Admission & Ingestion
    prov_ctx = SessionProvenanceContext(
        student_id=student_id,
        session_id="session-test-p5-07",
        resolved_target_node_id="SEC-05-BIN-SEC",
        requested_node_id="SEC-05-BIN-SEC",
        roadmap_revision_id=roadmap.canonical_revision_id,
        policy_revision_id=policy.canonical_policy_id,
        expected_task_specification_sha256=res.task.specification_sha256,
        expected_rubric_specification_sha256=res.rubric.specification_sha256,
        session_is_active=True,
        session_started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )
    admission = ingestion.evaluate_admissibility(res, prov_ctx, ledger)
    assert admission.outcome == EvidenceOutcome.PASS

    rec = ingestion.build_admitted_record(res, prov_ctx, admission.outcome, admission.admission_trace)
    assert rec.score == 1.0
    assert rec.overall_level == PerformanceLevel.N3_COMPETENT
    ledger.append_record(rec)

    # State verification: mastery granted!
    state = derive_student_state(roadmap, policy, ledger, student_id)
    sec05 = state.get_node_state("SEC-05-BIN-SEC")
    assert sec05 is not None
    assert sec05.status == NodeProgressStatus.ASSESSED_PROFICIENT
