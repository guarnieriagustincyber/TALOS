"""Protected test suite for Core Epistemological Invariants.

PROTECTED STATUS: FROZEN ARCHITECTURAL CONTRACT.
Per System Specification Doc 01 §20-21 and Safety Policy Doc 04 §9:
This test suite defines non-negotiable architectural boundaries:
1. Notebook Isolation (Notebook A cannot contaminate Notebook B).
2. LLM Statelessness & Non-Authority (LLM cannot mutate StudentState).
3. Curricular Advancement Inviolability (LLM cannot advance Roadmap).
4. Epistemological Separation (Execution != Assessment != Evidence != Mastery).
5. Artifact != Evidence (Raw execution artifacts cannot be auto-cast).
6. Ledger Immutability (EvidenceLedger is strictly append-only).
7. Provenance Admissibility Hard Gate (Evidence requires valid provenance).

DO NOT MODIFY THESE TESTS TO MAKE FAILING CODE PASS.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from pydantic import ValidationError

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
from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.contracts.evidence_ingestion import (
    AdmissionDecision,
    RejectionReason,
    SessionProvenanceContext,
)
from study_engine.contracts.execution import (
    ExecutionObservation,
    ExecutionStatus,
    ProcessTelemetry,
)
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.spine import (
    ExecutionProvenanceSpine,
    SpineAssessment,
    SpineCurriculum,
    SpineExecution,
    SpineIdentity,
    SpineTerminalState,
)
from study_engine.curriculum.performance_contracts import PerformanceLevel
from study_engine.roadmap.contracts import (
    CurricularRoadmap,
    DependencyType,
    NodeType,
    RoadmapDependency,
    RoadmapNode,
)
from study_engine.roadmap.engine import compute_canonical_revision_id
from study_engine.state.ingestion_engine import EvidenceIngestionEngine
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import (
    DuplicateEvidenceError,
    LedgerIntegrityStatus,
)
from study_engine.state.policy_contracts import (
    AssessmentPolicy,
    EvidenceRequirement,
    EvidenceType,
    NodeAssessmentCriteria,
)
from study_engine.state.policy_engine import compute_canonical_policy_id
from study_engine.state.state_contracts import NodeProgressStatus, StudentState
from study_engine.state.state_engine import derive_student_state
from study_engine.storage.knowledge_store import KnowledgeStore


# ---------------------------------------------------------------------------
# Helpers for valid canonical contracts
# ---------------------------------------------------------------------------


def _make_spec_ref(
    spec_id: str = "spec-01", sha256: str = "a" * 64
) -> SpecificationReference:
    return SpecificationReference(
        specification_id=spec_id,
        revision_id="rev-1",
        specification_sha256=sha256,
    )


def _make_obs_ref(
    obs_id: str = "obs-01", sha256: str = "b" * 64
) -> ObservationReference:
    return ObservationReference(
        observation_id=obs_id,
        execution_id="exec-01",
        effective_script_sha256="c" * 64,
        observation_sha256=sha256,
    )


def _make_instrumental_fact() -> InstrumentalFact:
    return InstrumentalFact(
        fact_id="fact-inst-01",
        observation_id="obs-01",
        fact_type=InstrumentalFactType.PROCESS_EXIT_CODE,
        fact_value="0",
        observability=FactObservability.CONCLUSIVE,
        inspected_domain="scratch/workspace/",
        provenance_detail="Process exit observation",
    )


def _make_evaluative_fact() -> EvaluativeFact:
    return EvaluativeFact(
        fact_id="fact-eval-01",
        evaluator_id="eval-01",
        fact_type=EvaluativeFactType.EXIT_CODE_EXPECTED,
        fact_value="0",
        satisfied=True,
        based_on_instrumental_fact_ids=("fact-inst-01",),
        requirement_id="req-clean-exit",
        rationale="Process exited cleanly with code 0",
    )


def _make_dimension_eval() -> DimensionEvaluation:
    return DimensionEvaluation(
        dimension_id="dim-clean-exit",
        status=AssessmentStatus.ASSESSED,
        assigned_level=PerformanceLevel.N3_COMPETENT,
        passed_minimum=True,
        is_critical=True,
        evidence_evaluative_fact_ids=("fact-eval-01",),
        evaluator_rule_ids=("rule-01",),
        evaluation_rationale="Evaluated cleanly",
    )


def _make_valid_assessment(
    assessment_id: str = "asmt-p1",
    authority_id: str = EpistemologicalAuthority.ASSESSMENT_ENGINE.value,
) -> AssessmentResult:
    now = datetime.now(timezone.utc)
    interim = AssessmentResult(
        assessment_id=assessment_id,
        authority_id=authority_id,
        task=_make_spec_ref("task-01", "a" * 64),
        rubric=_make_spec_ref("rubric-01", "b" * 64),
        observations=(_make_obs_ref(),),
        instrumental_facts=(_make_instrumental_fact(),),
        evaluative_facts=(_make_evaluative_fact(),),
        dimension_evaluations=(_make_dimension_eval(),),
        aggregation=AggregationResult(
            overall_level=PerformanceLevel.N3_COMPETENT,
            passed=True,
        ),
        evaluator_id="S9_DETERMINISTIC_EVALUATOR",
        evaluator_version="1.0.0",
        assessed_at=now,
        assessment_digest="",
    )
    digest = compute_canonical_sha256(interim)
    return interim.model_copy(update={"assessment_digest": digest})


def _make_valid_context(
    student_id: str = "student-1",
    node_id: str = "prog-punteros",
) -> SessionProvenanceContext:
    valid_sha = "f" * 64
    spine = ExecutionProvenanceSpine(
        spine_id="spine-001",
        identity=SpineIdentity(
            student_id=student_id,
            session_id="session-1",
            attempt_id="attempt-1",
        ),
        curriculum=SpineCurriculum(
            curriculum_node_id=node_id,
            roadmap_revision_id=valid_sha,
            policy_revision_id=valid_sha,
            gateway_id="G1.1",
            gateway_revision_id=valid_sha,
        ),
        assessment=SpineAssessment(
            rubric_id="rubric-01",
            rubric_revision_id=valid_sha,
            task_id="task-01",
            task_revision_id=valid_sha,
            hoare_contract_id="hoare-01",
            assessment_result_id="asmt-001",
            evidence_record_id="ev-001",
            evaluator_version="1.0.0",
        ),
        execution=SpineExecution(
            observation_ids=("obs-01",),
            artifact_digests=(valid_sha,),
            perturbation_id="pert-01",
        ),
        terminal_state=SpineTerminalState(
            ledger_cutoff_hash=valid_sha,
            student_state_id="state-01",
        ),
    )
    now = datetime.now(timezone.utc)
    return SessionProvenanceContext(
        student_id=student_id,
        session_id="session-1",
        resolved_target_node_id=node_id,
        roadmap_revision_id=valid_sha,
        policy_revision_id=valid_sha,
        expected_task_specification_sha256="a" * 64,
        expected_rubric_specification_sha256="b" * 64,
        session_is_active=True,
        session_started_at=now - timedelta(hours=1),
        spine=spine,
    )


# ---------------------------------------------------------------------------
# Invariant 1: Notebook Isolation
# ---------------------------------------------------------------------------


def test_invariant_notebook_isolation(tmp_path: Path) -> None:
    """INVARIANT: Knowledge in Notebook A must NEVER leak into Notebook B."""
    db_path = tmp_path / "protected_isolation.db"
    store = KnowledgeStore(db_path)
    store.initialize()

    # Create Notebook A and store secret domain content
    store.create_notebook(Notebook(id="nb-crypto", name="Criptografía"))
    src_a = SourceRecord(
        source_id="src-crypto-01",
        manifest=SourceManifest(
            source_id="src-crypto-01",
            filename="crypto_secrets.pdf",
            byte_size=1024,
            sha256="1" * 64,
        ),
    )
    store.save_source(src_a)
    store.link_source_to_notebook("nb-crypto", "src-crypto-01")
    store.save_document(
        Document(
            id="doc-c1",
            source_id="src-crypto-01",
            title="Cifrado Simétrico",
            content="El algoritmo AES utiliza claves secretas de 256 bits.",
        )
    )
    store.save_chunks([
        Chunk(
            id="chunk-c1",
            document_id="doc-c1",
            source_id="src-crypto-01",
            content="El algoritmo AES utiliza claves secretas de 256 bits.",
            index=0,
        )
    ])

    # Create Notebook B (different domain)
    store.create_notebook(Notebook(id="nb-prog", name="Programación en C"))

    # Search Notebook B for the secret concept from Notebook A
    results_in_b = store.search("AES claves secretas", notebook_id="nb-prog")
    assert len(results_in_b) == 0, (
        "SECURITY LEAK: Content from Notebook A was leaked to Notebook B!"
    )

    # Search Notebook A returns the result
    results_in_a = store.search("AES claves secretas", notebook_id="nb-crypto")
    assert len(results_in_a) == 1
    assert results_in_a[0].chunk_id == "chunk-c1"


# ---------------------------------------------------------------------------
# Invariant 2: LLM Cannot Directly Mutate StudentState
# ---------------------------------------------------------------------------


def test_invariant_llm_cannot_mutate_student_state() -> None:
    """INVARIANT: StudentState is frozen and derived deterministically."""
    now = datetime.now(timezone.utc)
    state = StudentState(
        student_id="student-007",
        roadmap_revision_id="a" * 64,
        policy_revision_id="b" * 64,
        ledger_cutoff_hash="0" * 64,
        as_of_time=now,
        cutoff_mode="COMMIT_TIME",  # type: ignore[arg-type]
        node_states=(),
        canonical_state_id="c" * 64,
    )

    # Attempting in-place mutation must be rejected by Pydantic frozen model
    with pytest.raises(ValidationError):
        setattr(state, "student_id", "hacked-student")  # type: ignore[misc]

    with pytest.raises(ValidationError):
        setattr(state, "node_states", ())  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Invariant 3: Curricular Advancement Inviolability
# ---------------------------------------------------------------------------


def test_invariant_llm_cannot_advance_roadmap_nodes() -> None:
    """INVARIANT: LLM cannot advance nodes; only admitted evidence can."""
    node_a = RoadmapNode(
        node_id="prog-intro",
        title="Introducción",
        description="Conceptos básicos",
        node_type=NodeType.TOPIC,
        notebook_id="fadena-prog",
        priority=1,
    )
    node_b = RoadmapNode(
        node_id="prog-punteros",
        title="Punteros",
        description="Aritmética de punteros",
        node_type=NodeType.TOPIC,
        notebook_id="fadena-prog",
        priority=2,
    )
    dep = RoadmapDependency(
        source_node_id="prog-intro",
        target_node_id="prog-punteros",
        dependency_type=DependencyType.HARD,
    )
    nodes = {"prog-intro": node_a, "prog-punteros": node_b}
    deps = (dep,)
    rev_id = compute_canonical_revision_id(
        "rm-prog", "Roadmap C", "1.0.0", nodes, deps
    )
    roadmap = CurricularRoadmap(
        roadmap_id="rm-prog",
        title="Roadmap C",
        version="1.0.0",
        nodes=nodes,
        dependencies=deps,
        canonical_revision_id=rev_id,
    )

    req_topic = EvidenceRequirement(
        requirement_id="req-topic",
        evidence_type=EvidenceType.CODE_EXECUTION,
        min_count=1,
        min_score=0.8,
    )
    crit_topic = NodeAssessmentCriteria(
        criteria_id="crit-topic-default",
        target_node_type=NodeType.TOPIC,
        requirements=(req_topic,),
        regression_threshold_failures=2,
    )
    defaults = {NodeType.TOPIC: crit_topic}
    p_id = compute_canonical_policy_id(
        "pol-test", "Test Policy", "1.0.0", defaults, {}
    )
    policy = AssessmentPolicy(
        policy_id="pol-test",
        title="Test Policy",
        version="1.0.0",
        default_criteria=defaults,
        canonical_policy_id=p_id,
    )

    empty_ledger = EvidenceLedger()

    # Initial state with empty ledger: node_b is strictly LOCKED
    initial_state = derive_student_state(
        roadmap=roadmap,
        policy=policy,
        ledger=empty_ledger,
        student_id="student-001",
        as_of_time=datetime.now(timezone.utc),
    )
    node_map = {ns.node_id: ns for ns in initial_state.node_states}
    assert node_map["prog-punteros"].status == NodeProgressStatus.LOCKED
    assert node_map["prog-intro"].status == NodeProgressStatus.AVAILABLE

    # An LLM can say "You have mastered prog-intro!" in natural language,
    # but deriving state against the same ledger still yields LOCKED for node_b
    reevaluated_state = derive_student_state(
        roadmap=roadmap,
        policy=policy,
        ledger=empty_ledger,
        student_id="student-001",
        as_of_time=datetime.now(timezone.utc),
    )
    reeval_map = {ns.node_id: ns for ns in reevaluated_state.node_states}
    assert reeval_map["prog-punteros"].status == NodeProgressStatus.LOCKED


# ---------------------------------------------------------------------------
# Invariant 4: Execution Observation != Mastery
# ---------------------------------------------------------------------------


def test_invariant_execution_result_is_not_mastery() -> None:
    """INVARIANT: ExecutionObservation cannot be directly added to Ledger."""
    ledger = EvidenceLedger()

    obs = ExecutionObservation(
        observation_id="obs-12345",
        execution_id="exec-12345",
        tool_name="pytest",
        status=ExecutionStatus.COMPLETED,
        exit_code=0,
        telemetry=ProcessTelemetry(duration_ms=120.0),
    )

    # Invariant: Ledger accepts only EvidenceRecord, never raw observations
    with pytest.raises((AttributeError, TypeError)):
        ledger.append_record(obs)  # type: ignore[arg-type]

    # The ledger remains pristine
    assert len(ledger.get_all_records()) == 0


# ---------------------------------------------------------------------------
# Invariant 5: Artifact != Evidence
# ---------------------------------------------------------------------------


def test_invariant_artifact_is_not_evidence() -> None:
    """INVARIANT: Raw execution artifacts cannot be auto-cast into Evidence."""
    engine = EvidenceIngestionEngine()
    ledger = EvidenceLedger()

    raw_artifact = {
        "artifact_id": "art-001",
        "type": "test_report",
        "status": "PASS",
        "student_id": "student-1",
    }
    context = _make_valid_context()

    # Engine rejects raw artifacts lacking an AssessmentResult contract
    with pytest.raises((AttributeError, TypeError)):
        engine.ingest_assessment(
            raw_artifact,  # type: ignore[arg-type]
            context=context,
            ledger=ledger,
        )


# ---------------------------------------------------------------------------
# Invariant 6: Ledger Immutability & Tamper Evidence
# ---------------------------------------------------------------------------


def test_invariant_ledger_immutability_and_tamper_evidence() -> None:
    """INVARIANT: EvidenceLedger is append-only; tampering is rejected."""
    engine = EvidenceIngestionEngine()
    ledger = EvidenceLedger()

    asmt = _make_valid_assessment(assessment_id="asmt-p1")
    context = _make_valid_context(student_id="student-1", node_id="node-proc")

    # Ingest record 1
    res1 = engine.ingest_assessment(asmt, context=context, ledger=ledger)
    assert res1.admission.decision == AdmissionDecision.ADMITTED
    assert res1.evidence_record is not None
    assert len(ledger.get_all_records()) == 1

    # Ingesting the EXACT same assessment must be rejected by Anti-Replay Gate
    res2 = engine.ingest_assessment(asmt, context=context, ledger=ledger)
    assert res2.admission.decision == AdmissionDecision.REJECTED
    assert (
        res2.admission.rejection_reason
        == RejectionReason.DUPLICATE_ASSESSMENT_REPLAY
    )

    # Direct append of duplicate record raises DuplicateEvidenceError
    record = ledger.get_all_records()[0]
    with pytest.raises(DuplicateEvidenceError):
        ledger.append_record(record)

    # Direct ledger tamper detection
    assert ledger.verify_integrity().status == LedgerIntegrityStatus.VALID


# ---------------------------------------------------------------------------
# Invariant 7: Provenance Admissibility Hard Gate
# ---------------------------------------------------------------------------


def test_invariant_evidence_rejected_without_valid_provenance() -> None:
    """INVARIANT: AssessmentResult with invalid provenance is rejected."""
    engine = EvidenceIngestionEngine()
    ledger = EvidenceLedger()

    # Assessment claiming an unauthorized authority
    bogus_asmt = _make_valid_assessment(
        assessment_id="asmt-p2",
        authority_id="unauthorized-agent-or-student",
    )
    context = _make_valid_context()

    res = engine.ingest_assessment(bogus_asmt, context=context, ledger=ledger)
    assert res.admission.decision == AdmissionDecision.REJECTED
    assert (
        res.admission.rejection_reason
        == RejectionReason.UNAUTHORIZED_ASSESSMENT_AUTHORITY
    )
    assert len(ledger.get_all_records()) == 0
