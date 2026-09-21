"""Unit tests for QueryDecomposer and Multi-query Retrieval (V1.1 Fase C)."""

import pytest

from study_engine.contracts.evidence_engine import SubQuery
from study_engine.evidence.decomposer import QueryDecomposer


def test_rule_based_query_decomposition():
    decomposer = QueryDecomposer(max_subqueries=5)
    query = (
        "Explícame cómo se crea un proceso con fork(), cómo compite por la CPU en la planificación "
        "y cómo se produce una condición de carrera si comparten memoria."
    )
    result = decomposer.decompose(query, notebook_id="NB-SO")

    assert not result.is_fallback
    assert len(result.sub_queries) >= 3
    assert len(result.sub_queries) <= 5
    assert all(isinstance(sq, SubQuery) for sq in result.sub_queries)


def test_subquery_prioritization_curricular_node():
    """Verifica que las sub-queries se priorizan por relevancia curricular (Refinamiento 1)."""
    decomposer = QueryDecomposer(max_subqueries=5)
    # Question contains process creation, scheduling, race conditions, memory paging, and pointers
    query = (
        "Explícame cómo se crea un proceso con fork, cómo funciona la planificación de CPU, "
        "qué es una condición de carrera, cómo se gestiona la memoria virtual paginada, "
        "y cómo se usan los punteros en C."
    )

    # Scoped to node for Process Model (node_id = 'SEC-02-OS-PROC')
    result = decomposer.decompose(
        query=query,
        notebook_id="NB-SO",
        node_id="SEC-02-OS-PROC",
    )

    # Top prioritized subquery should be about processes / fork
    top_subquery = result.sub_queries[0]
    assert "proceso" in top_subquery.text.lower() or "fork" in top_subquery.text.lower()


def test_subquery_prioritization_with_mastery_penalty():
    """Verifica que un tema ya dominado sufre penalización para dar paso a temas frescos."""
    decomposer = QueryDecomposer(max_subqueries=3)
    query = (
        "Explícame qué es una condición de carrera y cómo funciona la alternancia estricta."
    )

    # Case A: Student has 100% mastery in "carrera" (race conditions) and 0% in "alternancia"
    mastery_a = {"carrera": 1.0, "alternancia": 0.0}
    result_a = decomposer.decompose(
        query=query,
        notebook_id="NB-SO",
        mastery=mastery_a,
    )

    # Alternancia should have higher priority score than carrera
    sq_alt = next(sq for sq in result_a.sub_queries if "alternancia" in sq.text.lower())
    sq_car = next(sq for sq in result_a.sub_queries if "carrera" in sq.text.lower())
    assert sq_alt.priority_score > sq_car.priority_score


def test_query_decomposer_fallback_on_single_topic():
    decomposer = QueryDecomposer()
    simple_query = "¿Qué es un proceso?"
    result = decomposer.decompose(simple_query, notebook_id="NB-SO")

    assert len(result.sub_queries) == 1
    assert result.is_fallback
    assert result.sub_queries[0].text == simple_query
