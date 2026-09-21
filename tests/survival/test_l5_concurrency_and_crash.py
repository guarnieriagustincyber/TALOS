"""Layer L5 Hostile Survival Audit: Fault Injection, Concurrency & Crash Consistency.

Part of SYSTEM SURVIVAL AUDIT — SSA-0.
Modalidad: Read-Only / Red Team / No Patch.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import pytest

from study_engine.contracts.assessment import (
    AggregationResult,
    AssessmentResult,
    AssessmentStatus,
    DimensionEvaluation,
    EvaluativeFact,
    EvaluativeFactType,
    FactObservability,
    InstrumentalFact,
    InstrumentalFactType,
    ObservationReference,
    SpecificationReference,
    compute_canonical_sha256,
)
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.contracts.evidence_ingestion import (
    AdmissionDecision,
    RejectionReason,
    SessionProvenanceContext,
)
from study_engine.roadmap.contracts import (
    CurricularRoadmap,
    DependencyType,
    NodeType,
    RoadmapDependency,
    RoadmapNode,
)
from study_engine.roadmap.engine import compute_canonical_revision_id
from study_engine.state.ingestion_engine import EvidenceIngestionEngine
from study_engine.state.ledger import (
    DuplicateEvidenceError,
    EvidenceLedger,
)
from study_engine.state.ledger_contracts import LedgerIntegrityStatus
from study_engine.state.policy_contracts import (
    ActorType,
    AssessmentPolicy,
    CriteriaEvaluationVerdict,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
)
from study_engine.state.policy_engine import compute_canonical_policy_id
from study_engine.state.state_contracts import (
    HistoryCutoffMode,
    NodeProgressStatus,
    validate_student_state_hash,
)
from study_engine.state.state_engine import derive_student_state


def _build_test_assessment(digest_seed: str = "concurrency-01") -> AssessmentResult:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    task_ref = SpecificationReference(
        specification_id="task-c-pointer",
        revision_id="rev-1",
        specification_sha256="0" * 64,
    )
    rubric_ref = SpecificationReference(
        specification_id="rubric-c-pointer",
        revision_id="rev-1",
        specification_sha256="1" * 64,
    )
    obs_ref = ObservationReference(
        observation_id=f"obs-{digest_seed}",
        execution_id="exec-1",
        effective_script_sha256="a" * 64,
        observation_sha256="b" * 64,
    )
    inst_fact = InstrumentalFact(
        fact_id=f"inst-{digest_seed}",
        observation_id=f"obs-{digest_seed}",
        fact_type=InstrumentalFactType.PROCESS_EXIT_CODE,
        fact_value="0",
        observability=FactObservability.CONCLUSIVE,
        provenance_detail="exit 0",
    )
    eval_fact = EvaluativeFact(
        fact_id=f"eval-{digest_seed}",
        evaluator_id="eval-01",
        fact_type=EvaluativeFactType.EXIT_CODE_EXPECTED,
        fact_value="0",
        satisfied=True,
        based_on_instrumental_fact_ids=(f"inst-{digest_seed}",),
        requirement_id="req-1",
        rationale="Exit matched",
    )
    dim_eval = DimensionEvaluation(
        dimension_id="dim-1",
        status=AssessmentStatus.NOT_APPLICABLE,
        is_critical=False,
        evaluation_rationale="N/A",
    )
    agg = AggregationResult(
        passed=True,
        overall_level=None,
        critical_dimension_failures=(),
        insufficient_dimensions=(),
    )
    asmt_core = AssessmentResult(
        assessment_id=f"asmt-{digest_seed}",
        task=task_ref,
        rubric=rubric_ref,
        observations=(obs_ref,),
        instrumental_facts=(inst_fact,),
        evaluative_facts=(eval_fact,),
        dimension_evaluations=(dim_eval,),
        aggregation=agg,
        evaluator_id="eval-01",
        evaluator_version="1.0",
        authority_id=EpistemologicalAuthority.ASSESSMENT_ENGINE.value,
        assessment_digest="",
        assessed_at=now,
    )
    digest = compute_canonical_sha256(asmt_core)
    return asmt_core.model_copy(update={"assessment_digest": digest})


# =============================================================================
# L5.1: HIGH-CONCURRENCY REPLAY RACE AUDIT
# =============================================================================

# =============================================================================
# L5.1: REPLAY RACE AUDIT (SEQUENTIAL VS CONCURRENT)
# =============================================================================

def test_l5_1_sequential_replay_race_converges_to_single_persisted_evidence():
    """Sequential replay race: exactly 1 admitted, N-1 rejected at preflight Gate 4."""
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    engine = EvidenceIngestionEngine()
    asmt = _build_test_assessment(digest_seed="seq-race")

    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "evidence_ledger.jsonl"
        ledger = EvidenceLedger(file_path=ledger_path)

        ctx = SessionProvenanceContext(
            session_id="sess-seq-race",
            student_id="student-alpha",
            session_started_at=now - timedelta(hours=1),
            session_is_active=True,
            resolved_target_node_id="c-pointers-101",
            expected_task_specification_sha256="0" * 64,
            expected_rubric_specification_sha256="1" * 64,
            roadmap_revision_id="2" * 64,
            policy_revision_id="3" * 64,
        )

        metrics = {
            "ADMITTED": 0,
            "DUPLICATE_REJECTED": 0,
            "RACE_LOST": 0,
            "TOTAL": 10,
        }

        for i in range(10):
            res = engine.ingest_assessment(asmt, ctx, ledger)
            if res.admission.decision == AdmissionDecision.ADMITTED:
                metrics["ADMITTED"] += 1
            elif res.admission.rejection_reason == RejectionReason.DUPLICATE_ASSESSMENT_REPLAY:
                metrics["DUPLICATE_REJECTED"] += 1

        assert metrics["ADMITTED"] == 1
        assert metrics["DUPLICATE_REJECTED"] == 9
        assert ledger.total_entries == 1


@pytest.mark.parametrize("thread_count", [10, 50, 100])
def test_l5_1_concurrency_replay_race_disaggregation(thread_count: int):
    """High-concurrency replay race submitting the IDENTICAL assessment concurrently.

    Must disaggregate:
    - ADMITTED
    - DUPLICATE_REJECTED (preflight)
    - RACE_LOST (caught at atomic commit)
    - COMMIT_REJECTED
    - PERSISTED_ONCE (total entries in ledger == 1)
    """
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    engine = EvidenceIngestionEngine()
    asmt = _build_test_assessment(digest_seed=f"race-{thread_count}")

    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "evidence_ledger.jsonl"
        ledger = EvidenceLedger(file_path=ledger_path)

        ctx = SessionProvenanceContext(
            session_id=f"sess-race-{thread_count}",
            student_id="student-alpha",
            session_started_at=now - timedelta(hours=1),
            session_is_active=True,
            resolved_target_node_id="c-pointers-101",
            expected_task_specification_sha256="0" * 64,
            expected_rubric_specification_sha256="1" * 64,
            roadmap_revision_id="2" * 64,
            policy_revision_id="3" * 64,
        )

        metrics = {
            "ADMITTED": 0,
            "DUPLICATE_REJECTED": 0,
            "RACE_LOST": 0,
            "COMMIT_REJECTED": 0,
            "TOTAL_SUBMISSIONS": thread_count,
        }

        def submit():
            try:
                res = engine.ingest_assessment(
                    assessment=asmt,
                    context=ctx,
                    ledger=ledger,
                )
                return res
            except Exception as e:
                return e

        results = []
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = [executor.submit(submit) for _ in range(thread_count)]
            for future in as_completed(futures):
                results.append(future.result())

        for r in results:
            if isinstance(r, Exception):
                metrics["COMMIT_REJECTED"] += 1
            elif r.admission.decision == AdmissionDecision.ADMITTED and r.ledger_entry is not None:
                metrics["ADMITTED"] += 1
            elif r.admission.decision == AdmissionDecision.REJECTED:
                if "Concurrent duplicate detected during atomic commit" in (r.admission.rejection_detail or ""):
                    metrics["RACE_LOST"] += 1
                elif r.admission.rejection_reason == RejectionReason.DUPLICATE_ASSESSMENT_REPLAY:
                    metrics["DUPLICATE_REJECTED"] += 1
                else:
                    metrics["COMMIT_REJECTED"] += 1
            else:
                metrics["COMMIT_REJECTED"] += 1

        persisted_once = ledger.total_entries == 1

        print(f"\n[CONCURRENCY RACE N={thread_count}]")
        print(f"  ADMITTED: {metrics['ADMITTED']}")
        print(f"  DUPLICATE_REJECTED (Preflight): {metrics['DUPLICATE_REJECTED']}")
        print(f"  RACE_LOST (Atomic Commit): {metrics['RACE_LOST']}")
        print(f"  COMMIT_REJECTED: {metrics['COMMIT_REJECTED']}")
        print(f"  LEDGER TOTAL ENTRIES: {ledger.total_entries} (PERSISTED_ONCE={persisted_once})")

        # Save telemetry to repo
        telemetry_dir = Path(__file__).resolve().parent.parent.parent / "data" / "experiments" / "survival"
        telemetry_dir.mkdir(parents=True, exist_ok=True)
        import json
        telemetry_file = telemetry_dir / f"l5_concurrency_race_{thread_count}.json"
        telemetry_file.write_text(
            json.dumps(
                {
                    "layer": "L5.1",
                    "thread_count": thread_count,
                    "metrics": metrics,
                    "ledger_total_entries": ledger.total_entries,
                    "persisted_once": persisted_once,
                    "invariant_05_status": "CONTAINED" if persisted_once else "BROKEN",
                    "finding_classification": "REAL_DEFECT",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        # CRITICAL CONVERGENCE INVARIANT: Exactly 1 record persisted in the ledger!
        assert ledger.total_entries == 1, (
            f"CONCURRENCY BREACH: Expected 1 persisted entry, found {ledger.total_entries}!"
        )


# =============================================================================
# L5.2: CRASH & RECONSTRUCTION FAULT INJECTION AUDIT
# =============================================================================

def test_l5_2_crash_before_ledger_leaves_clean_uncommitted_state():
    """Crash Phase 1: Crash occurs during evaluation before ledger.append_record."""
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    engine = EvidenceIngestionEngine()
    asmt = _build_test_assessment(digest_seed="crash-phase-1")

    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "evidence_ledger.jsonl"
        ledger = EvidenceLedger(file_path=ledger_path)

        ctx = SessionProvenanceContext(
            session_id="sess-crash-1",
            student_id="student-alpha",
            session_started_at=now - timedelta(hours=1),
            session_is_active=True,
            resolved_target_node_id="c-pointers-101",
            expected_task_specification_sha256="0" * 64,
            expected_rubric_specification_sha256="1" * 64,
            roadmap_revision_id="2" * 64,
            policy_revision_id="3" * 64,
        )

        # 1. Preflight succeeds
        adm = engine.evaluate_admissibility(asmt, ctx, ledger)
        assert adm.decision == AdmissionDecision.ADMITTED

        # 2. Simulated CRASH (process exits before append_record)
        del engine
        del ledger

        # 3. RESTART: Reload ledger from disk
        restarted_ledger = EvidenceLedger(file_path=ledger_path)
        assert restarted_ledger.total_entries == 0  # Zero pollution!


def test_l5_2_crash_after_ledger_before_state_projection_deterministic_recovery():
    """Crash Phase 2: Crash occurs after ledger commit, but before StudentState is saved.

    Protocol: CRASH -> RESTART -> REPLAY/RECONSTRUCTION -> EXPECTED DERIVED STATE.
    Invariant: NO UNRECONCILABLE CRASH STATE.
    """
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    engine = EvidenceIngestionEngine()
    asmt = _build_test_assessment(digest_seed="crash-phase-2")

    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "evidence_ledger.jsonl"
        ledger = EvidenceLedger(file_path=ledger_path)

        ctx = SessionProvenanceContext(
            session_id="sess-crash-2",
            student_id="student-alpha",
            session_started_at=now - timedelta(hours=1),
            session_is_active=True,
            resolved_target_node_id="node-ptr",
            expected_task_specification_sha256="0" * 64,
            expected_rubric_specification_sha256="1" * 64,
            roadmap_revision_id="2" * 64,
            policy_revision_id="3" * 64,
        )

        # 1. Ingestion commits to ledger successfully
        ingestion_res = engine.ingest_assessment(asmt, ctx, ledger)
        assert ingestion_res.admission.decision == AdmissionDecision.ADMITTED
        assert ingestion_res.ledger_entry is not None

        # Build Roadmap & Policy
        node = RoadmapNode(
            node_id="node-ptr",
            title="Pointers",
            description="Pointer fundamentals",
            node_type=NodeType.TOPIC,
            notebook_id="nb-01",
        )
        nodes = {"node-ptr": node}
        rev_id = compute_canonical_revision_id(
            roadmap_id="rm-crash-02",
            title="Roadmap Crash",
            version="1.0",
            nodes=nodes,
            dependencies=(),
        )
        roadmap = CurricularRoadmap(
            roadmap_id="rm-crash-02",
            title="Roadmap Crash",
            version="1.0",
            nodes=nodes,
            dependencies=(),
            canonical_revision_id=rev_id,
        )

        crit = NodeAssessmentCriteria(
            criteria_id="crit-ptr",
            target_node_id="node-ptr",
            requirements=(
                EvidenceRequirement(
                    requirement_id="req-ptr",
                    evidence_type=EvidenceType.CODE_EXECUTION,
                    min_count=1,
                ),
            ),
        )
        overrides = {"node-ptr": crit}
        pol_id = compute_canonical_policy_id(
            policy_id="pol-crash-02",
            title="Policy Crash",
            version="1.0",
            default_criteria={},
            node_overrides=overrides,
        )
        policy = AssessmentPolicy(
            policy_id="pol-crash-02",
            title="Policy Crash",
            version="1.0",
            default_criteria={},
            node_overrides=overrides,
            canonical_policy_id=pol_id,
        )

        # 2. Simulated CRASH before saving state
        del engine
        del ledger

        # 3. RESTART: Reload ledger from durable disk
        recovered_ledger = EvidenceLedger(file_path=ledger_path)
        assert recovered_ledger.total_entries == 1
        integrity_report = recovered_ledger.verify_integrity()
        assert integrity_report.status == LedgerIntegrityStatus.VALID

        # 4. REPLAY / RECONSTRUCTION
        reconstructed_state = derive_student_state(
            student_id="student-alpha",
            roadmap=roadmap,
            policy=policy,
            ledger=recovered_ledger,
            as_of_time=datetime.now(timezone.utc),
        )

        # Verify reconstructed state
        validate_student_state_hash(reconstructed_state)
        n_state = reconstructed_state.get_node_state("node-ptr")
        assert n_state is not None
        assert n_state.status == NodeProgressStatus.ASSESSED_PROFICIENT
        assert n_state.evaluation_result.verdict == CriteriaEvaluationVerdict.SATISFIED
        print("\n--> NO UNRECONCILABLE CRASH STATE verified: state deterministically reconstructed from ledger.")
