"""Layer L1 Hostile Survival Audit: AST Sovereignty, Deep Immutability & Ontological Substitution.

Part of SYSTEM SURVIVAL AUDIT — SSA-0.
Modalidad: Read-Only / Red Team / No Patch.
"""

import ast
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple
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
from study_engine.contracts.epistemology import (
    EpistemologicalAuthority,
    EpistemologicalAuthorityViolationError,
    EpistemologicalStage,
    validate_epistemological_authority,
)
from study_engine.contracts.evidence_ingestion import (
    AdmissionDecision,
    RejectionReason,
    SessionProvenanceContext,
)
from study_engine.contracts.execution import ExecutionObservation
from study_engine.state.ingestion_engine import EvidenceIngestionEngine
from study_engine.state.policy_contracts import (
    ActorType,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)


repo_root = Path(__file__).resolve().parent.parent.parent
src_root = repo_root / "src" / "study_engine"


# =============================================================================
# L1.1: AST Authority Audit (Static Code Inspection)
# =============================================================================
def test_l1_1_ast_evidence_record_instantiation_sovereignty():
    """Verify that NO module outside S5.2.A instantiates EvidenceRecord."""
    unauthorized_instantiations: List[Tuple[str, int]] = []

    # Whitelisted modules permitted to instantiate EvidenceRecord in source
    allowed_source_files = {
        src_root / "state" / "ingestion_engine.py",
    }

    for py_file in src_root.rglob("*.py"):
        if py_file.resolve() in [f.resolve() for f in allowed_source_files]:
            continue

        try:
            tree = ast.parse(
                py_file.read_text(encoding="utf-8"), filename=str(py_file)
            )
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                is_evidence_instantiation = False
                if isinstance(func, ast.Name) and func.id == "EvidenceRecord":
                    is_evidence_instantiation = True
                elif (
                    isinstance(func, ast.Attribute)
                    and func.attr == "EvidenceRecord"
                ):
                    is_evidence_instantiation = True

                if is_evidence_instantiation:
                    rel_path = py_file.relative_to(repo_root)
                    unauthorized_instantiations.append(
                        (str(rel_path), node.lineno)
                    )

    assert len(unauthorized_instantiations) == 0, (
        f"CRITICAL AUTHORITY LEAK: EvidenceRecord is directly instantiated "
        f"outside S5.2.A ingestion_engine in: {unauthorized_instantiations}"
    )


# =============================================================================
# L1.2: Deep Immutability Attack (Shallow frozen=True vs Nested Structures)
# =============================================================================
def test_l1_2_deep_immutability_evidence_record():
    """Attack EvidenceRecord immutability: top-level vs nested mutations."""
    now = datetime.now(timezone.utc)
    rec = EvidenceRecord(
        record_id="ev-attack-01",
        student_id="student-alpha",
        node_id="so-proc-basics",
        evidence_type=EvidenceType.CODE_EXECUTION,
        outcome=EvidenceOutcome.PASS,
        score=1.0,
        timestamp=now,
        actor_type=ActorType.TOOL_VERIFIER,
        actor_id="valgrind-verifier",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        roadmap_revision_id="a" * 64,
        policy_revision_id="b" * 64,
        metadata={"original_key": "safe_value", "evaluator_version": "1.0"},
    )

    # 1. Top-level mutation MUST raise error
    with pytest.raises(Exception):
        rec.outcome = EvidenceOutcome.FAIL  # type: ignore[misc]

    with pytest.raises(Exception):
        rec.score = 0.0  # type: ignore[misc]

    # 2. Nested dictionary mutation probe (Shallow immutability vulnerability check)
    # Pydantic ConfigDict(frozen=True) protects attribute assignment on rec,
    # but does it protect against in-place dictionary modification?
    nested_mutation_succeeded = False
    try:
        rec.metadata["evil_injection"] = "MUTATED_AFTER_SEAL"
        rec.metadata["original_key"] = "CORRUPTED"
        nested_mutation_succeeded = True
    except Exception:
        nested_mutation_succeeded = False

    # Check if nested dict was actually modified in-place
    if nested_mutation_succeeded and rec.metadata.get("original_key") == "CORRUPTED":
        # We record this finding! It documents shallow immutability
        print("\n--> FINDING CONFIRMED: EvidenceRecord.metadata mutated in-place!")


def test_l1_2_deep_immutability_admission_trace_details():
    """Attack AdmissionTrace immutability: probe nested details dictionary."""
    from study_engine.contracts.evidence_ingestion import AdmissionTrace, GateVerdict

    trace = AdmissionTrace(
        integrity=GateVerdict.PASS,
        provenance=GateVerdict.PASS,
        session=GateVerdict.PASS,
        anti_replay=GateVerdict.PASS,
        details={"gate.integrity": "VALID"},
    )

    # Top-level assignment fails
    with pytest.raises(Exception):
        trace.integrity = GateVerdict.FAIL  # type: ignore[misc]

    # Nested dictionary in-place mutation
    nested_mutated = False
    try:
        trace.details["gate.integrity"] = "FORGED_COMPROMISED"
        trace.details["injected_bypass"] = "TRUE"
        nested_mutated = True
    except Exception:
        nested_mutated = False

    # This confirms shallow immutability on AdmissionTrace.details as well
    if nested_mutated and trace.details.get("gate.integrity") == "FORGED_COMPROMISED":
        print("\n--> FINDING CONFIRMED: AdmissionTrace.details mutated in-place!")


def test_l1_2_legacy_student_state_lacks_immutability():
    """Probe study_engine.contracts.student_state.StudentState for lack of frozen config."""
    from study_engine.contracts.student_state import StudentState as LegacyStudentState

    legacy_state = LegacyStudentState(
        student_id="student-alpha",
        topic="threads",
        status="developing",
        understanding={"concurrency": False},
        strengths=["locks"],
        weaknesses=["deadlocks"],
    )

    # In legacy StudentState, attributes can be overwritten freely in memory!
    legacy_state.status = "mastered"
    legacy_state.understanding["concurrency"] = True
    assert legacy_state.status == "mastered"
    assert legacy_state.understanding["concurrency"] is True
    print("\n--> FINDING CONFIRMED: Legacy StudentState contract is fully mutable (DESIGN GAP).")


def test_l1_2_state_contracts_student_state_tamper_detection():
    """Verify that state_contracts.StudentState detects tamper via validate_student_state_hash."""
    from study_engine.state.state_contracts import (
        HistoryCutoffMode,
        NodeProgressStatus,
        NodeState,
        StudentState as SealedStudentState,
        StateHashMismatchError,
        compute_canonical_state_id,
        validate_student_state_hash,
    )

    now = datetime.now(timezone.utc)
    node_a = NodeState(
        node_id="proc-fork",
        status=NodeProgressStatus.IN_PROGRESS,
        total_evidence_count=1,
    )
    node_states = (node_a,)

    canonical_id = compute_canonical_state_id(
        student_id="student-01",
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        ledger_cutoff_hash="2" * 64,
        as_of_time=now,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
        node_states=node_states,
    )

    sealed_state = SealedStudentState(
        student_id="student-01",
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        ledger_cutoff_hash="2" * 64,
        as_of_time=now,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
        node_states=node_states,
        canonical_state_id=canonical_id,
    )

    # Valid state passes validation
    validate_student_state_hash(sealed_state)

    # Tampered state (forged status with same canonical_state_id)
    tampered_node_a = NodeState(
        node_id="proc-fork",
        status=NodeProgressStatus.ASSESSED_PROFICIENT,  # Tampered!
        total_evidence_count=1,
    )
    tampered_state = SealedStudentState(
        student_id="student-01",
        roadmap_revision_id="0" * 64,
        policy_revision_id="1" * 64,
        ledger_cutoff_hash="2" * 64,
        as_of_time=now,
        cutoff_mode=HistoryCutoffMode.COMMIT_TIME,
        node_states=(tampered_node_a,),
        canonical_state_id=canonical_id,  # Stale hash
    )

    with pytest.raises(StateHashMismatchError):
        validate_student_state_hash(tampered_state)



# =============================================================================
# L1.3: Ontological Authority Substitution Attacks
# =============================================================================
def test_l1_3_ontological_authority_substitution_observation_as_assessment():
    """Attack: Fabricate an ExecutionObservation attempting to act as Assessment."""
    obs = ExecutionObservation(
        observation_id="obs-evil-01",
        execution_id="exec-evil-01",
        tool_name="gcc",
        exit_code=139,
        effective_script_sha256="0" * 64,
        timestamp=datetime.now(timezone.utc),
    )

    engine = EvidenceIngestionEngine()
    ctx = SessionProvenanceContext(
        session_id="sess-01",
        student_id="student-alpha",
        session_started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        session_is_active=True,
        resolved_target_node_id="so-proc-basics",
        roadmap_revision_id="a" * 64,
        policy_revision_id="b" * 64,
    )

    with pytest.raises(Exception):
        engine.evaluate_admissibility(obs, ctx)  # type: ignore[arg-type]


def test_l1_3_ontological_authority_substitution_usurped_authority_id():
    """Attack: AssessmentResult claiming an observation authority (EXECUTION_PLANE)."""
    now = datetime.now(timezone.utc)
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
        observation_id="obs-1",
        execution_id="exec-1",
        effective_script_sha256="a" * 64,
        observation_sha256="b" * 64,
    )
    inst_fact = InstrumentalFact(
        fact_id="inst-1",
        observation_id="obs-1",
        fact_type=InstrumentalFactType.PROCESS_EXIT_CODE,
        fact_value="0",
        observability=FactObservability.CONCLUSIVE,
        provenance_detail="exit code check",
    )
    eval_fact = EvaluativeFact(
        fact_id="eval-1",
        evaluator_id="eval-01",
        fact_type=EvaluativeFactType.EXIT_CODE_EXPECTED,
        fact_value="0",
        satisfied=True,
        based_on_instrumental_fact_ids=("inst-1",),
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

    # Fabricate AssessmentResult with unauthorized authority_id (EXECUTION_PLANE usurping ASSESSMENT_ENGINE)
    evil_assessment_core = AssessmentResult(
        assessment_id="asmt-usurp-01",
        task=task_ref,
        rubric=rubric_ref,
        observations=(obs_ref,),
        instrumental_facts=(inst_fact,),
        evaluative_facts=(eval_fact,),
        dimension_evaluations=(dim_eval,),
        aggregation=agg,
        evaluator_id="eval-01",
        evaluator_version="1.0",
        authority_id=EpistemologicalAuthority.EXECUTION_PLANE.value,  # ILLEGITIMATE!
        assessment_digest="",
        assessed_at=now,
    )
    computed_digest = compute_canonical_sha256(evil_assessment_core)
    evil_assessment = evil_assessment_core.model_copy(
        update={"assessment_digest": computed_digest}
    )

    engine = EvidenceIngestionEngine()
    ctx = SessionProvenanceContext(
        session_id="sess-01",
        student_id="student-alpha",
        session_started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        session_is_active=True,
        resolved_target_node_id="c-pointers-101",
        expected_task_specification_sha256="0" * 64,
        expected_rubric_specification_sha256="1" * 64,
        roadmap_revision_id="2" * 64,
        policy_revision_id="3" * 64,
    )

    result = engine.evaluate_admissibility(evil_assessment, ctx)
    assert result.decision == AdmissionDecision.REJECTED
    assert result.rejection_reason == RejectionReason.UNAUTHORIZED_ASSESSMENT_AUTHORITY
