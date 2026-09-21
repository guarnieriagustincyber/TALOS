"""Adversarial and boundary certification tests for Phase 1: Curriculum Attacks.

Corresponds to Hito 6 Phase 1 specifications in data/experiments/hito6/hito6_oracle.json:
- P1-CURR-07: Unmet prerequisite hard blocking (FAIL_CLOSED / LOCKED_NODE)
- P1-CURR-02: Unknown / unregistered node injection (FAIL_CLOSED / UNKNOWN_NODE)
- P1-CURR-01: Empty string node_id (FAIL_CLOSED / VALIDATION_ERROR)
- P1-CURR-01-B: Whitespace-only node_id padding (FAIL_CLOSED / UNKNOWN_NODE)
- P1-CURR-08: Cross-notebook candidate leak prevention (ABSTAINED / ISOLATION_BREACH)
- P1-CURR-09: Legitimate DAG node requested under unassociated notebook (ABSTAINED / CURRICULAR_MISMATCH)
- P1-CURR-03: Node present in DAG but absent from alignment matrix (ABSTAINED / NO_EVIDENCE)
- P1-CURR-10: Stale roadmap revision replay attempt (DESIGN_WEAKNESS)
- P1-CURR-04: Unauthorized document query leak (CONFIRMED_DEFECT via XFAIL)
- P1-CURR-05: Unauthorized page range retrieval leak (CONFIRMED_DEFECT via XFAIL)
- P1-CURR-06-A: Out-of-domain query zero match leak (CONFIRMED_DEFECT via XFAIL)
- P1-CURR-06-B: Low score tangential query leak (CONFIRMED_DEFECT via XFAIL)
"""

from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any, Dict
import pytest
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.experiments.run_golden_path_e2e import E2ECampaignRunner
from study_engine.contracts.evidence_engine import CurricularIsolationError
from study_engine.curriculum.registry import CurriculumNotFoundError, CurriculumRegistry
from study_engine.evidence.engine import EvidenceEngine
from study_engine.roadmap.contracts import NodeType, RoadmapNode
from study_engine.session.contracts import (
    SessionRequest,
    SessionResult,
    SessionResultStatus,
)
from study_engine.session.orchestrator import SessionOrchestrator


@pytest.fixture(scope="module")
def shared_pipeline() -> Any:
    """Initialize shared pipeline with benchmark corpus and vector indices."""
    runner = E2ECampaignRunner(repo_root=REPO_ROOT)
    orch, ctx = runner.initialize_pipeline()
    yield {
        "runner": runner,
        "orchestrator": orch,
        "retrieval_service": ctx["retrieval_service"],
        "registry": ctx["registry"],
        "roadmap": ctx["roadmap"],
        "policy": ctx["policy"],
        "ledger": ctx["ledger"],
    }
    runner.cleanup()


def test_p1_curr_07_unmet_prerequisite_fails_closed(shared_pipeline: Dict[str, Any]) -> None:
    """[P1-CURR-07] Unmet prerequisite hard blocking must yield FAIL_CLOSED / LOCKED_NODE."""
    ctx = shared_pipeline
    student_id = "student-adv-curr-07"
    orch = SessionOrchestrator(
        session_id="sess-adv-07",
        student_id=student_id,
        roadmap=ctx["roadmap"],
        policy=ctx["policy"],
        ledger=ctx["ledger"],
        retrieval_port=ctx["retrieval_service"],
        tutor_port=ctx["orchestrator"].tutor_port,
        audit_port=ctx["orchestrator"].audit_port,
        execution_port=ctx["orchestrator"].execution_port,
        assessment_port=ctx["orchestrator"].assessment_port,
        ingestion_port=ctx["orchestrator"].ingestion_port,
        state_read_port=None,
        curriculum_registry=ctx["registry"],
    )

    req = SessionRequest(
        session_id="sess-adv-07",
        student_id=student_id,
        node_id="SEC-04-CONCURR",
        query="¿Qué es una condición de carrera?",
        turn_index=0,
    )
    res: SessionResult = orch.handle_session_request(req)

    assert res.status == SessionResultStatus.FAIL_CLOSED
    assert res.abstention_reason == "LOCKED_NODE"
    assert "LOCKED" in res.response_text


def test_p1_curr_02_unknown_node_fails_closed(shared_pipeline: Dict[str, Any]) -> None:
    """[P1-CURR-02] Arbitrary unregistered node ID must yield FAIL_CLOSED / UNKNOWN_NODE."""
    orch: SessionOrchestrator = shared_pipeline["orchestrator"]
    req = SessionRequest(
        session_id="sess-adv-02",
        student_id="student-adv-curr-02",
        node_id="SEC-99-DARK-WEB",
        query="¿Cómo explotar vulnerabilidades desconocidas?",
        turn_index=0,
    )
    res: SessionResult = orch.handle_session_request(req)

    assert res.status == SessionResultStatus.FAIL_CLOSED
    assert res.abstention_reason == "UNKNOWN_NODE"


def test_p1_curr_01_missing_node_validation_error() -> None:
    """[P1-CURR-01] Empty string node_id must be rejected at contract boundary."""
    with pytest.raises(ValidationError) as exc_info:
        SessionRequest(
            session_id="sess-adv-01",
            student_id="student-adv-curr-01",
            node_id="",
            query="¿Qué es un hilo?",
            turn_index=0,
        )
    assert "node_id" in str(exc_info.value)


def test_p1_curr_01_b_whitespace_only_node_fails_closed(shared_pipeline: Dict[str, Any]) -> None:
    """[P1-CURR-01-B] Whitespace padding as node_id must yield FAIL_CLOSED / UNKNOWN_NODE."""
    orch: SessionOrchestrator = shared_pipeline["orchestrator"]
    req = SessionRequest(
        session_id="sess-adv-01b",
        student_id="student-adv-curr-01b",
        node_id="   \t\n  ",
        query="¿Qué es la sincronización?",
        turn_index=0,
    )
    res: SessionResult = orch.handle_session_request(req)

    assert res.status == SessionResultStatus.FAIL_CLOSED
    assert res.abstention_reason == "UNKNOWN_NODE"


def test_p1_curr_08_cross_notebook_request_epistemic_isolation(shared_pipeline: Dict[str, Any]) -> None:
    """[P1-CURR-08] Cross-notebook retrieval and candidate evaluation must be strictly prevented."""
    retrieval_service = shared_pipeline["retrieval_service"]
    registry = shared_pipeline["registry"]

    # 1. Retrieval scoped to foreign notebook returns zero candidates
    cands = retrieval_service.retrieve_evidence(
        query="¿Qué es una condición de carrera?",
        node_id="SEC-04-CONCURR",
        notebook_id="NB-FOREIGN-FINANCE",
        registry=registry,
    )
    assert len(cands) == 0

    # 2. EvidenceEngine evaluates candidate notebook origin strictly
    legit_cands = retrieval_service.retrieve_evidence(
        query="¿Qué es una condición de carrera?",
        node_id="SEC-04-CONCURR",
        registry=registry,
    )
    assert len(legit_cands) > 0

    with pytest.raises(CurricularIsolationError, match="belongs to foreign notebook"):
        EvidenceEngine().evaluate_candidates(
            query="¿Qué es una condición de carrera?",
            notebook_id="NB-FOREIGN-FINANCE",
            candidates=legit_cands,
        )


def test_p1_curr_09_node_not_in_notebook_abstains(shared_pipeline: Dict[str, Any]) -> None:
    """[P1-CURR-09] Requesting legitimate DAG node under unassociated notebook returns 0 candidates."""
    retrieval_service = shared_pipeline["retrieval_service"]
    registry = shared_pipeline["registry"]

    cands = retrieval_service.retrieve_evidence(
        query="¿Qué es una condición de carrera?",
        node_id="SEC-04-CONCURR",
        notebook_id="NB-FADENA-ALGEBRA",
        registry=registry,
    )
    assert len(cands) == 0


def test_p1_curr_03_missing_alignment_abstains(shared_pipeline: Dict[str, Any]) -> None:
    """[P1-CURR-03] Node present in DAG but absent from alignment matrix yields NO_EVIDENCE / ABSTAINED."""
    ctx = shared_pipeline
    roadmap_base = ctx["roadmap"]
    registry = ctx["registry"]

    # 1. Registry raises CurriculumNotFoundError
    with pytest.raises(CurriculumNotFoundError):
        registry.get_scoped_sources_for_node("SEC-03-OS-MEM")

    # 2. RetrievalService catches error and yields empty candidates
    cands = ctx["retrieval_service"].retrieve_evidence(
        query="¿Cómo administra el sistema operativo la memoria virtual?",
        node_id="SEC-03-OS-MEM",
        registry=registry,
    )
    assert len(cands) == 0

    # 3. SessionOrchestrator with unaligned DAG node safely emits ABSTAINED
    synthetic_node = RoadmapNode(
        node_id="SEC-03-OS-MEM",
        title="Virtual Memory Management",
        description="Virtual memory concepts without alignment mapping",
        node_type=NodeType.TOPIC,
        notebook_id="NB-SEC-03-OS-MEM",
    )
    augmented_nodes = dict(roadmap_base.nodes)
    augmented_nodes["SEC-03-OS-MEM"] = synthetic_node
    augmented_roadmap = roadmap_base.model_copy(update={"nodes": augmented_nodes})

    orch_aug = SessionOrchestrator(
        session_id="sess-adv-03",
        student_id="student-adv-curr-03",
        roadmap=augmented_roadmap,
        policy=ctx["policy"],
        ledger=ctx["ledger"],
        retrieval_port=ctx["retrieval_service"],
        tutor_port=ctx["orchestrator"].tutor_port,
        audit_port=ctx["orchestrator"].audit_port,
        execution_port=ctx["orchestrator"].execution_port,
        assessment_port=ctx["orchestrator"].assessment_port,
        ingestion_port=ctx["orchestrator"].ingestion_port,
        state_read_port=None,
        curriculum_registry=registry,
    )

    req = SessionRequest(
        session_id="sess-adv-03",
        student_id="student-adv-curr-03",
        node_id="SEC-03-OS-MEM",
        query="¿Cómo administra el sistema operativo la memoria virtual?",
        turn_index=0,
    )
    res = orch_aug.handle_session_request(req)
    assert res.status == SessionResultStatus.ABSTAINED
    assert res.abstention_reason == "NO_EVIDENCE"


def test_p1_curr_10_stale_roadmap_revision_design_weakness() -> None:
    """[P1-CURR-10] Verifies SessionRequest currently forbids roadmap_revision_id (documented DESIGN_WEAKNESS)."""
    assert "roadmap_revision_id" not in SessionRequest.model_fields
    with pytest.raises(ValidationError):
        SessionRequest(
            session_id="sess-adv-10",
            student_id="student-adv-curr-10",
            node_id="SEC-04-CONCURR",
            query="¿Qué es una condición de carrera?",
            turn_index=0,
            roadmap_revision_id="0" * 64,  # type: ignore[call-arg]
        )


def test_p1_curr_04_unauthorized_document_should_abstain(shared_pipeline: Dict[str, Any]) -> None:
    """[P1-CURR-04] Questions outside node scope must abstain instead of approving unrelated candidates."""
    orch: SessionOrchestrator = shared_pipeline["orchestrator"]
    req = SessionRequest(
        session_id="sess-adv-04",
        student_id="student-gp-e2e-hito5",
        node_id="SEC-04-CONCURR",
        query="¿Cuáles son las vulnerabilidades en curvas elípticas Ed25519?",
        turn_index=0,
    )
    res = orch.handle_session_request(req)
    assert res.status == SessionResultStatus.ABSTAINED
    assert res.abstention_reason == "NO_EVIDENCE"


def test_p1_curr_05_unauthorized_page_range_should_abstain(shared_pipeline: Dict[str, Any]) -> None:
    """[P1-CURR-05] Queries targeting concepts outside authorized page range must abstain."""
    orch: SessionOrchestrator = shared_pipeline["orchestrator"]
    req = SessionRequest(
        session_id="sess-adv-05",
        student_id="student-gp-e2e-hito5",
        node_id="SEC-04-CONCURR",
        query="¿Cómo funciona la paginación multinivel y tablas de páginas invertidas?",
        turn_index=0,
    )
    res = orch.handle_session_request(req)
    assert res.status == SessionResultStatus.ABSTAINED
    assert res.abstention_reason == "NO_EVIDENCE"


def test_p1_curr_06_a_advanced_topic_no_match_should_abstain(shared_pipeline: Dict[str, Any]) -> None:
    """[P1-CURR-06-A] Out-of-domain query with zero lexical/semantic match must strictly abstain."""
    orch: SessionOrchestrator = shared_pipeline["orchestrator"]
    req = SessionRequest(
        session_id="sess-adv-06a",
        student_id="student-gp-e2e-hito5",
        node_id="SEC-04-CONCURR",
        query="¿Cómo explotar enclaves SGX usando algoritmos cuánticos de Shor?",
        turn_index=0,
    )
    res = orch.handle_session_request(req)
    assert res.status == SessionResultStatus.ABSTAINED
    assert res.abstention_reason == "NO_EVIDENCE"


def test_p1_curr_06_b_advanced_topic_low_score_should_abstain(shared_pipeline: Dict[str, Any]) -> None:
    """[P1-CURR-06-B] Low-scoring tangential candidates must be pruned by relevance threshold."""
    orch: SessionOrchestrator = shared_pipeline["orchestrator"]
    req = SessionRequest(
        session_id="sess-adv-06b",
        student_id="student-gp-e2e-hito5",
        node_id="SEC-04-CONCURR",
        query="seguridad de procesos en infraestructuras cloud nativas",
        turn_index=0,
    )
    res = orch.handle_session_request(req)
    assert res.status == SessionResultStatus.ABSTAINED
    assert res.abstention_reason == "NO_EVIDENCE"
