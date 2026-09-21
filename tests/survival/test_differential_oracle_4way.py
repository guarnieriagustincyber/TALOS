"""Independent Differential 4-Way Oracle for Concurrency & Semantic Identity.

Certifies the formal decision function D(K, R) per docs/06-CONCURRENCY-SPECIFICATION-V1.1.md:
D(K, R):
  - K not in DB                      => COMMIT_OK
  - K in DB and R_in == R_stored     => IDEMPOTENT_ACK
  - K in DB and R_in != R_stored     => INCONSISTENT_REPLAY (Fail-Closed)
  - K2 not in DB                     => COMMIT_OK
"""

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
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)


def _make_evidence_record(
    record_id: str,
    attempt_id: str,
    digest: str,
    student_id: str = "student-oracle",
    node_id: str = "node-oracle",
) -> EvidenceRecord:
    return EvidenceRecord(
        record_id=record_id,
        student_id=student_id,
        node_id=node_id,
        competency_id="comp-oracle",
        evidence_type=EvidenceType.CODE_EXECUTION,
        outcome=EvidenceOutcome.PASS,
        score=1.0,
        timestamp=datetime.now(timezone.utc),
        actor_type=ActorType.TOOL_VERIFIER,
        actor_id="oracle-verifier",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        assessment_digest=digest,
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        metadata={"evaluation_attempt_id": attempt_id},
    )


def _build_oracle_assessment(digest_seed: str, exit_code: str = "0") -> AssessmentResult:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    task_ref = SpecificationReference(
        specification_id="task-oracle",
        revision_id="rev-1",
        specification_sha256="0" * 64,
    )
    rubric_ref = SpecificationReference(
        specification_id="rubric-oracle",
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
        fact_value=exit_code,
        observability=FactObservability.CONCLUSIVE,
        provenance_detail=f"exit {exit_code}",
    )
    eval_fact = EvaluativeFact(
        fact_id=f"eval-{digest_seed}",
        evaluator_id="eval-oracle",
        fact_type=EvaluativeFactType.EXIT_CODE_EXPECTED,
        fact_value=exit_code,
        satisfied=(exit_code == "0"),
        based_on_instrumental_fact_ids=(f"inst-{digest_seed}",),
        requirement_id="req-1",
        rationale="Oracle check",
    )
    dim_eval = DimensionEvaluation(
        dimension_id="dim-1",
        status=AssessmentStatus.NOT_APPLICABLE,
        is_critical=False,
        evaluation_rationale="N/A",
    )
    agg = AggregationResult(
        passed=(exit_code == "0"),
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
        evaluator_id="eval-oracle",
        evaluator_version="1.0",
        authority_id=EpistemologicalAuthority.ASSESSMENT_ENGINE.value,
        assessment_digest="",
        assessed_at=now,
    )
    digest = compute_canonical_sha256(asmt_core)
    return asmt_core.model_copy(update={"assessment_digest": digest})


class TestDifferentialOracle4Way:
    """Verifies the exact 4-way truth table for D(K, R)."""

    def test_oracle_direct_ledger_truth_table(self):
        """Test D(K, R) decisions directly on the EvidenceLedger storage layer."""
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "oracle_ledger.db"
            ledger = EvidenceLedger(file_path=db_path)

            K1_attempt = "attempt-alpha-001"
            R1_digest = "a" * 64
            R2_divergent = "b" * 64
            K2_attempt = "attempt-beta-002"

            # 1. Scenario 1: Initial (K1, R1) -> COMMIT_OK
            rec1 = _make_evidence_record("rec-1", K1_attempt, R1_digest)
            entry1 = ledger.append_record(rec1)
            assert entry1.entry_index == 0
            assert ledger.total_entries == 1

            # 2. Scenario 2: Replay (K1, R1) with identical digest -> IDEMPOTENT_ACK
            rec1_replay = _make_evidence_record("rec-1-retry", K1_attempt, R1_digest)
            with pytest.raises(IdempotentReplayError) as exc_info:
                ledger.append_record(rec1_replay)
            assert "Idempotent replay detected" in str(exc_info.value)
            assert ledger.total_entries == 1  # Invariant: cardinality remains 1

            # 3. Scenario 3: Replay (K1, R2) with divergent digest -> INCONSISTENT_REPLAY (Fail-Closed)
            rec1_divergent = _make_evidence_record("rec-1-divergent", K1_attempt, R2_divergent)
            with pytest.raises(InconsistentReplayError) as exc_info:
                ledger.append_record(rec1_divergent)
            assert "Inconsistent replay detected" in str(exc_info.value)
            assert ledger.total_entries == 1  # Invariant: rejected, cardinality remains 1

            # 4. Scenario 4: New Attempt (K2, R2) -> COMMIT_OK
            rec2 = _make_evidence_record("rec-2", K2_attempt, R2_divergent)
            entry2 = ledger.append_record(rec2)
            assert entry2.entry_index == 1
            assert ledger.total_entries == 2

            # Cryptographic chain integrity check
            report = ledger.verify_integrity()
            assert report.status == LedgerIntegrityStatus.VALID
            assert report.valid_entries == 2

    def test_oracle_ingestion_engine_truth_table(self):
        """Test D(K, R) decisions through the EvidenceIngestionEngine layer."""
        now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        engine = EvidenceIngestionEngine()

        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "ingest_oracle.jsonl"
            ledger = EvidenceLedger(file_path=ledger_path)

            ctx = SessionProvenanceContext(
                session_id="sess-oracle",
                student_id="student-oracle",
                session_started_at=now - timedelta(hours=1),
                session_is_active=True,
                resolved_target_node_id="c-pointers-101",
                expected_task_specification_sha256="0" * 64,
                expected_rubric_specification_sha256="1" * 64,
                roadmap_revision_id="2" * 64,
                policy_revision_id="3" * 64,
            )

            asmt_ok = _build_oracle_assessment("seed-ok", exit_code="0")

            # 1. Initial ingestion -> ADMITTED
            res1 = engine.ingest_assessment(asmt_ok, ctx, ledger)
            assert res1.admission.decision == AdmissionDecision.ADMITTED
            assert res1.ledger_entry is not None
            assert ledger.total_entries == 1

            # 2. Sequential retry of identical assessment -> REJECTED (DUPLICATE_ASSESSMENT_REPLAY)
            res2 = engine.ingest_assessment(asmt_ok, ctx, ledger)
            assert res2.admission.decision == AdmissionDecision.REJECTED
            assert res2.admission.rejection_reason == RejectionReason.DUPLICATE_ASSESSMENT_REPLAY
            assert ledger.total_entries == 1

            # 3. Inconsistent retry under same attempt ID -> REJECTED (INCONSISTENT_ASSESSMENT_REPLAY)
            # Create divergent record with same attempt ID in ledger
            divergent_record = _make_evidence_record(
                record_id="rec-incon-test",
                attempt_id=f"ev-{asmt_ok.assessment_digest[:16]}",  # Same attempt key
                digest="f" * 64,  # Divergent digest
                student_id="student-oracle",
                node_id="c-pointers-101",
            )
            with pytest.raises(InconsistentReplayError):
                ledger.append_record(divergent_record)

            assert ledger.total_entries == 1

    def test_jsonl_export_deterministic_regeneration(self):
        """Verify export_jsonl regenerates the audit view deterministically after simulated loss."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ledger_file = tmp_path / "regenerate.jsonl"
            ledger = EvidenceLedger(file_path=ledger_file)

            # Commit 5 records
            for i in range(5):
                rec = _make_evidence_record(f"rec-{i}", f"att-{i}", f"{i:02x}" + "0" * 62)
                ledger.append_record(rec)

            assert ledger.total_entries == 5
            assert ledger_file.exists()

            # Delete derived JSONL file (simulating crash or loss)
            ledger_file.unlink()
            assert not ledger_file.exists()

            # Deterministic regeneration from authoritative SQLite DB
            exported_path = ledger.export_jsonl()
            assert exported_path.exists()

            lines = [line.strip() for line in exported_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            assert len(lines) == 5

            # Reload a fresh EvidenceLedger from the regenerated JSONL
            reloaded = EvidenceLedger(file_path=exported_path)
            assert reloaded.total_entries == 5
            assert reloaded.verify_integrity().status == LedgerIntegrityStatus.VALID
