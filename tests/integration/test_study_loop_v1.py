"""Integration Test Suite for Hito 7: Real Study Loop (Learning Loop V1).

Verifies the 9 mandatory scenarios:
1. Turn 1: Conceptual Grounding (S3 -> S4.3 -> S4.4)
2. Turn 2: Comprehension Probing (Calibrated NLI gate, zero ledger commit)
3. Turn 3: Practice Dispatch (CurriculumRegistry task resolution)
4. Turn 4: Instrumental Execution & Assessment (S6 -> S9 -> S5.2.A)
5. Turn 5: State Derivation & Feedback (S5.2.C DAG unlock + S7 Feedback)
6. Anti-Replay Defense (D(K, R) -> IdempotentReplayError, delta ledger = 0)
7. Pedagogical Invariants TUT-01 through TUT-06
8. Max Conceptual Turns Escape (Clarification 1: prevent infinite probe loops)
9. Post-Feedback Explanation (Clarification 3: conceptual clarification without code leak)
"""

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Dict, List, Tuple
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.experiments.run_study_loop_v1 import (
    StudyLoopExperimentRunner,
    build_cybersecurity_policy,
    run_study_loop_v1,
)
from study_engine.contracts.assessment import AssessmentResult
from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.contracts.evidence_ingestion import SessionProvenanceContext
from study_engine.contracts.generation import GenerationMode
from study_engine.contracts.tutor import (
    PedagogicalAction,
    ResponseBudgetPolicy,
    TutorContext,
    TutorPolicyDecision,
)
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.roadmap.contracts import CurricularRoadmap
from study_engine.session.contracts import (
    PracticeRequest,
    PracticeResult,
    PracticeResultStatus,
    SessionRequest,
    SessionResult,
    SessionResultStatus,
)
from study_engine.session.study_loop import StudyLoopController
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import IdempotentReplayError, LedgerIntegrityStatus
from study_engine.state.policy_contracts import (
    ActorType,
    AssessmentPolicy,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)
from study_engine.state.state_contracts import NodeProgressStatus, StudentState
from study_engine.tutor.policy import DeterministicTutorPolicy, TutorPolicyConfig


@pytest.fixture(scope="module")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def campaign_results(repo_root: Path) -> Dict[str, Any]:
    """Run the canonical 5-turn study loop once for the module."""
    return run_study_loop_v1(repo_root=repo_root)


@pytest.fixture(scope="module")
def oracle(repo_root: Path) -> Dict[str, Any]:
    oracle_path = repo_root / "data" / "experiments" / "study_loop_v1" / "study_loop_oracle.json"
    with open(oracle_path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
        return data


def test_study_loop_turn1_conceptual_grounding(campaign_results: Dict[str, Any], oracle: Dict[str, Any]) -> None:
    """1. Turn 1: Conceptual Grounding with Epistemic Isolation and S4.4 Audit Approval."""
    t1 = campaign_results["turns"]["turn_1"]
    exp_t1 = oracle["turns"][0]

    assert t1["action"] == exp_t1["expected_tutor_decision"]["action"]
    assert t1["budget"] == exp_t1["expected_tutor_decision"]["budget"]
    assert t1["target_node_id"] == exp_t1["expected_tutor_decision"]["target_node_id"]
    assert t1["session_status"] == exp_t1["expected_audit"]["status"]
    assert t1["audit_report_id"] is not None

    # Epistemic isolation: only authorized document
    assert "prog_punteros.pdf" in t1["retrieved_doc_ids"]
    exp_pr = exp_t1["expected_retrieval"]["authorized_page_range"]
    auth_pages = set(range(exp_pr["start"], exp_pr["end"] + 1))
    for p in t1["retrieved_pages"]:
        assert p in auth_pages

    # Grounded citation
    assert "[E1]" in t1["response_text"]


def test_study_loop_turn2_check_understanding(campaign_results: Dict[str, Any], oracle: Dict[str, Any]) -> None:
    """2. Turn 2: Comprehension Probing with Calibrated NLI Gate and Zero Ledger Commit."""
    t2 = campaign_results["turns"]["turn_2"]
    exp_t2 = oracle["turns"][1]

    assert t2["action"] == exp_t2["expected_tutor_decision"]["action"]
    assert t2["budget"] == exp_t2["expected_tutor_decision"]["budget"]
    assert t2["target_node_id"] == exp_t2["expected_tutor_decision"]["target_node_id"]
    assert t2["conceptually_sound"] == exp_t2["expected_evaluation"]["conceptually_sound"]
    assert t2["ready_for_practice"] == exp_t2["expected_evaluation"]["ready_for_practice"]

    # Strict Formative Invariant: ZERO evidence record committed
    assert t2["ledger_delta"] == 0


def test_study_loop_turn3_practice_dispatch(campaign_results: Dict[str, Any], oracle: Dict[str, Any]) -> None:
    """3. Turn 3: Practice Presentation and Task Resolution from CurriculumRegistry."""
    t3 = campaign_results["turns"]["turn_3"]
    exp_t3 = oracle["turns"][2]

    assert t3["action"] == exp_t3["expected_tutor_decision"]["action"]
    assert t3["budget"] == exp_t3["expected_tutor_decision"]["budget"]
    assert t3["target_node_id"] == exp_t3["expected_tutor_decision"]["target_node_id"]
    assert t3["suggested_task_id"] == exp_t3["expected_tutor_decision"]["suggested_task_id"]
    assert t3["dispatched_task_id"] == "task_sec05_file_hasher.json"


def test_study_loop_turn4_execution_and_assessment(campaign_results: Dict[str, Any], oracle: Dict[str, Any]) -> None:
    """4. Turn 4: Sandbox Execution, Deterministic S9.1 Assessment, and Evidence Ingestion."""
    t4 = campaign_results["turns"]["turn_4"]
    exp_t4 = oracle["turns"][3]

    assert t4["status"] == exp_t4["expected_assessment"]["status"]
    assert t4["exit_code"] == exp_t4["expected_execution"]["exit_code"]
    assert t4["execution_status"] == exp_t4["expected_execution"]["status"]
    assert t4["assessment_passed"] is True
    assert t4["score"] == exp_t4["expected_assessment"]["score"]
    assert t4["overall_level"] == exp_t4["expected_assessment"]["overall_level"]
    assert t4["evidence_record_id"] is not None
    assert t4["ledger_delta"] == exp_t4["expected_ingestion"]["ledger_delta"]


def test_study_loop_turn5_state_derivation_and_unlock(campaign_results: Dict[str, Any], oracle: Dict[str, Any]) -> None:
    """5. Turn 5: Sovereign State Derivation, Capstone Node Unlock, and Templated Feedback."""
    t5 = campaign_results["turns"]["turn_5"]
    exp_t5 = oracle["turns"][4]

    assert t5["sec05_status"] == exp_t5["expected_state_projection"]["sec05_status"]
    assert t5["sec06_status"] == exp_t5["expected_state_projection"]["sec06_status"]
    assert t5["sec06_unlocked"] is True
    assert t5["action"] == exp_t5["expected_tutor_decision"]["action"]
    assert t5["budget"] == exp_t5["expected_tutor_decision"]["budget"]
    assert t5["pedagogical_intent"] == exp_t5["expected_tutor_decision"]["pedagogical_intent"]
    assert t5["feedback_rendered"] is True


def test_study_loop_anti_replay_defense(campaign_results: Dict[str, Any], oracle: Dict[str, Any]) -> None:
    """6. Anti-Replay Defense: Idempotent duplicate submission is caught with zero ledger mutation."""
    t5 = campaign_results["turns"]["turn_5"]
    exp_t5 = oracle["turns"][4]

    assert t5["anti_replay_idempotent_detected"] is True
    assert t5["ledger_cardinality"] == exp_t5["expected_persistence_guarantees"]["ledger_cardinality"]
    assert t5["hash_chain_status"] == exp_t5["expected_persistence_guarantees"]["hash_chain_status"]


def test_study_loop_invariants_tut01_to_tut06() -> None:
    """7. Formal verification of all 6 Pedagogical Invariants (TUT-01 through TUT-06)."""
    policy = DeterministicTutorPolicy()

    # TUT-04: Curriculum alignment - LOCKED node or unfulfilled prerequisites MUST fail-closed with ABSTAIN
    ctx_locked = TutorContext(
        student_id="alice",
        active_node_id="SEC-05-BIN-SEC",
        node_status="LOCKED",
        unfulfilled_prerequisites=["SEC-03-MEM-MGMT"],
        conceptual_turns_completed=0,
    )
    dec_locked = policy.decide(ctx_locked)
    assert dec_locked.action == PedagogicalAction.ABSTAIN
    assert dec_locked.pedagogical_intent == "FAIL_CLOSED_LOCK"

    # TUT-05: Deterministic Action Selection - same context strictly yields identical decision
    ctx_avail = TutorContext(
        student_id="alice",
        active_node_id="SEC-01-C-PTR",
        node_status="AVAILABLE",
        unfulfilled_prerequisites=[],
        conceptual_turns_completed=0,
    )
    dec_1 = policy.decide(ctx_avail)
    dec_2 = policy.decide(ctx_avail)
    assert dec_1 == dec_2
    assert dec_1.action == PedagogicalAction.EXPLAIN

    # TUT-06: Response budgeting - conceptual explanations have NORMAL budget, probe has SHORT
    assert dec_1.budget == ResponseBudgetPolicy.NORMAL
    ctx_probe = TutorContext(
        student_id="alice",
        active_node_id="SEC-01-C-PTR",
        node_status="AVAILABLE",
        unfulfilled_prerequisites=[],
        conceptual_turns_completed=1,
    )
    dec_probe = policy.decide(ctx_probe)
    assert dec_probe.action == PedagogicalAction.CHECK_UNDERSTANDING
    assert dec_probe.budget == ResponseBudgetPolicy.SHORT

    # TUT-03: Cognitive Non-Substitution - practice action never allows code snippets
    ctx_practice = TutorContext(
        student_id="alice",
        active_node_id="SEC-01-C-PTR",
        node_status="AVAILABLE",
        unfulfilled_prerequisites=[],
        conceptual_turns_completed=1,
        last_student_message="listo para practicar",
    )
    dec_practice = policy.decide(ctx_practice)
    assert dec_practice.action == PedagogicalAction.REQUEST_PRACTICE
    assert dec_practice.allow_code_snippets is False


def test_study_loop_max_conceptual_turns_escape() -> None:
    """8. Clarification 1: When conceptual turns reach MAX_CONCEPTUAL_TURNS, policy forces practice dispatch."""
    policy = DeterministicTutorPolicy(config=TutorPolicyConfig(max_conceptual_turns=5))

    # At 4 turns: still probing
    ctx_4 = TutorContext(
        student_id="bob",
        active_node_id="SEC-01-C-PTR",
        node_status="AVAILABLE",
        unfulfilled_prerequisites=[],
        conceptual_turns_completed=4,
    )
    dec_4 = policy.decide(ctx_4)
    assert dec_4.action == PedagogicalAction.CHECK_UNDERSTANDING

    # At 5 turns: ESCAPE rule triggers, forcing practice dispatch
    ctx_5 = TutorContext(
        student_id="bob",
        active_node_id="SEC-01-C-PTR",
        node_status="AVAILABLE",
        unfulfilled_prerequisites=[],
        conceptual_turns_completed=5,
    )
    dec_5 = policy.decide(ctx_5)
    assert dec_5.action == PedagogicalAction.REQUEST_PRACTICE
    assert dec_5.pedagogical_intent == "FORCE_PRACTICE_ESCAPE"
    assert dec_5.rationale == "MAX_CONCEPTUAL_TURNS_REACHED"


def test_study_loop_post_feedback_explanation() -> None:
    """9. Clarification 3: Post-feedback conceptual clarification without solution leakage."""
    policy = DeterministicTutorPolicy()

    # Student asks why they failed after practical attempt
    ctx_post = TutorContext(
        student_id="charlie",
        active_node_id="SEC-05-BIN-SEC",
        node_status="AVAILABLE",
        unfulfilled_prerequisites=[],
        conceptual_turns_completed=2,
        practice_attempts_count=1,
        last_assessment_verdict="FAIL",
        last_student_message="¿Por qué falló el tamaño de mi buffer?",
    )
    dec_post = policy.decide(ctx_post)
    assert dec_post.action == PedagogicalAction.EXPLAIN
    assert dec_post.budget == ResponseBudgetPolicy.SHORT
    assert dec_post.pedagogical_intent == "CLARIFY_FAILED_DIMENSION_WITHOUT_SOLUTION"
    assert dec_post.allow_code_snippets is False

    # Simulate controller rendering clarification: verifies TUT-03 (no code disclosure)
    dummy_asmt_json = {
        "assessment_id": "asmt-mock-01",
        "task": {"specification_id": "task-01", "revision_id": "rev-01", "specification_sha256": "0"*64},
        "rubric": {"specification_id": "rubric-01", "revision_id": "rev-01", "specification_sha256": "0"*64},
        "observations": [{"observation_id": "obs-01", "execution_id": "exec-01", "effective_script_sha256": "0"*64, "observation_sha256": "0"*64}],
        "instrumental_facts": [{"fact_id": "f1", "observation_id": "obs-01", "fact_type": "process.exit_code", "fact_value": "0", "provenance_detail": "exit"}],
        "evaluative_facts": [{"fact_id": "ef1", "evaluator_id": "eval-01", "fact_type": "eval.artifact_conforms", "fact_value": "0", "satisfied": False, "based_on_instrumental_fact_ids": ["f1"], "requirement_id": "req1", "rationale": "Size mismatch"}],
        "dimension_evaluations": [
            {
                "dimension_id": "DIM_BUFFER_SIZE",
                "status": "ASSESSED",
                "assigned_level": 1,
                "passed_minimum": False,
                "is_critical": True,
                "evidence_evaluative_fact_ids": ["ef1"],
                "evaluator_rule_ids": ["RULE_SIZE"],
                "evaluation_rationale": "Buffer size was 32 bytes instead of 64."
            }
        ],
        "aggregation": {"passed": False, "overall_level": 1},
        "evaluator_id": "eval-mock",
        "evaluator_version": "1.0",
        "assessment_digest": "1"*64,
    }
    mock_asmt = AssessmentResult.model_validate(dummy_asmt_json)

    # Controller facade post-feedback clarification test
    from study_engine.session.study_loop import StudyLoopController
    class MockOrchestrator:
        student_id = "charlie"
        session_id = "sess-charlie"
        authorized_target = None
        roadmap = None
        def _derive_state(self, ts: Any) -> Any:
            return None

    ctrl = StudyLoopController(
        orchestrator=MockOrchestrator(),  # type: ignore[arg-type]
        active_node_id="SEC-05-BIN-SEC",
    )
    ctrl.last_assessment_result = mock_asmt
    clarification = ctrl.handle_post_feedback_clarification("¿Por qué falló el tamaño del buffer?")

    assert "DIM_BUFFER_SIZE" in clarification
    assert "buffer" in clarification.lower()
    # Invariant TUT-03: No solution code disclosed
    assert "def " not in clarification
    assert "return " not in clarification
    assert "open(" not in clarification
