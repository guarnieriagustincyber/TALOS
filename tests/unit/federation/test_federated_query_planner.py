"""Unit tests for Federated Query Planner and G1-G4 Anti-Error Guardrails (Phase E4, Amendments E4-4, E4-5, E4-R1, E4-R3)."""

from datetime import datetime, timezone, timedelta
import pytest
from study_engine.federation.notebook_registry import NotebookRegistry
from study_engine.federation.bridge_registry import BridgeRegistry
from study_engine.federation.federated_query_planner import (
    FederatedPlan,
    FederatedQueryPlanner,
    FederatedRetrievalCandidate,
)


@pytest.fixture
def planner() -> FederatedQueryPlanner:
    nb_reg = NotebookRegistry()
    br_reg = BridgeRegistry("config/bridges.allowlist.json")
    return FederatedQueryPlanner(notebook_registry=nb_reg, bridge_registry=br_reg)


def test_guardrail_g4_empty_query_fails_closed(planner: FederatedQueryPlanner) -> None:
    """[E4-R3] G4 Guardrail: Empty query or empty topic list fails-closed with PLAN_UNSUPPORTED."""
    plan_empty = planner.plan_query("fadena-prog", "")
    assert plan_empty.status == "PLAN_UNSUPPORTED"
    assert plan_empty.guardrail_code == "G4"

    plan_empty_topics = planner.plan_query("fadena-prog", "valid query", topics=[])
    assert plan_empty_topics.status == "PLAN_UNSUPPORTED"
    assert plan_empty_topics.guardrail_code == "G4"


def test_guardrail_g1_unknown_active_notebook_rejected(planner: FederatedQueryPlanner) -> None:
    """[E4-R3] G1 Guardrail: Unknown active notebook rejected with PLAN_UNSUPPORTED."""
    plan = planner.plan_query("non-existent-notebook", "consulta sobre punteros")
    assert plan.status == "PLAN_UNSUPPORTED"
    assert plan.guardrail_code == "G1"


def test_guardrail_g2_expired_bridge_fails_closed(planner: FederatedQueryPlanner) -> None:
    """[E4-R3] G2 Guardrail: Expired cross-notebook bridge halts execution with GUARDRAIL_REJECTED."""
    # Query covering cross-curricular topic 'buffer_overflow' that requires bridge to fadena-so
    simulated_future = datetime(2027, 2, 1, tzinfo=timezone.utc)
    plan = planner.plan_query(
        "fadena-prog",
        "analisis de buffer_overflow en memoria",
        topics=["buffer_overflow"],
        now=simulated_future,
    )
    assert plan.status == "GUARDRAIL_REJECTED"
    assert plan.guardrail_code == "G2"
    assert "expired" in plan.rejection_reason.lower()


def test_guardrail_g3_no_cyclic_routing_loops(planner: FederatedQueryPlanner) -> None:
    """[E4-R3] G3 Guardrail: Ensure plan contains no duplicate/cyclic notebook visits."""
    plan = planner.plan_query(
        "fadena-prog",
        "concurrencia y sockets_tcp con punteros",
        topics=["punteros", "concurrencia", "sockets_tcp"],
    )
    assert plan.status == "READY"
    visited_targets = [sq.target_notebook_id for sq in plan.subqueries]
    # Each notebook should appear at most once per unique topic, no cyclic duplication
    assert len(visited_targets) == len(plan.subqueries)


def test_deterministic_deduplication_tie_break(planner: FederatedQueryPlanner) -> None:
    """Amendment E4-5: Tie-breaking key (-authority_weight, doc_id, chunk_id)."""
    # Create two candidates with the exact same content_hash from different notebooks
    c1 = FederatedRetrievalCandidate(
        chunk_id="chunk-so-1",
        doc_id="doc-b",
        notebook_id="fadena-so",
        content="Buffer overflow ocurre cuando...",
        content_hash="hash-common-01",
        authority_weight=1.2,
        retrieval_score=0.9,
    )
    c2 = FederatedRetrievalCandidate(
        chunk_id="chunk-sec-1",
        doc_id="doc-a",
        notebook_id="NB-CYBERSECURITY-V1",
        content="Buffer overflow ocurre cuando...",
        content_hash="hash-common-01",
        authority_weight=1.5,  # Higher authority
        retrieval_score=0.9,
    )

    deduped = planner.deduplicate_candidates([c1, c2])
    assert len(deduped) == 1
    # Candidate with authority 1.5 must win the tie-break
    assert deduped[0].chunk_id == "chunk-sec-1"
    assert deduped[0].authority_weight == 1.5


def test_stale_in_flight_candidate_excluded(planner: FederatedQueryPlanner) -> None:
    """Amendment E4-2: Candidate marked with stale_bridge_result=True is excluded."""
    c_stale = FederatedRetrievalCandidate(
        chunk_id="chunk-stale",
        doc_id="doc-x",
        notebook_id="fadena-so",
        content="Stale content",
        content_hash="hash-stale",
        authority_weight=1.0,
        retrieval_score=0.8,
        stale_bridge_result=True,
    )
    c_valid = FederatedRetrievalCandidate(
        chunk_id="chunk-valid",
        doc_id="doc-y",
        notebook_id="fadena-prog",
        content="Valid content",
        content_hash="hash-valid",
        authority_weight=1.0,
        retrieval_score=0.8,
        stale_bridge_result=False,
    )

    deduped = planner.deduplicate_candidates([c_stale, c_valid])
    assert len(deduped) == 1
    assert deduped[0].chunk_id == "chunk-valid"


def test_decomposition_validity_metric(planner: FederatedQueryPlanner) -> None:
    """Amendment E4-R1: DecompositionValidity >= 90%."""
    queries = [
        ("fadena-prog", "punteros y memoria dinamica", ["punteros", "memoria_dinamica"]),
        ("fadena-so", "procesos y planificacion", ["procesos"]),
        ("NB-CYBERSECURITY-V1", "analisis de buffer_overflow", ["buffer_overflow"]),
        ("fadena-prog", "sockets_tcp y redes", ["sockets_tcp"]),
    ]
    plans = [planner.plan_query(nb, q, t) for nb, q, t in queries]
    score = planner.evaluate_decomposition_validity(plans)
    assert score >= 0.90
    assert score == 1.0
