"""Unit tests for AdaptiveRetrievalRouter (Fase 7 / F1, F7)."""

import pytest
from study_engine.retrieval.adaptive_router import (
    AdaptiveRetrievalRouter,
    RouteDecision,
    RoutingStrategy,
)


def test_router_exact_lexical_classification_f1():
    """F1: count_matches(EXACT_LEXICAL_PATTERNS) >= 2 -> EXACT_LEXICAL."""
    router = AdaptiveRetrievalRouter()

    # Contiene 'pthread_mutex_lock' y 'NULL' (>= 2 matches)
    q1 = "cómo solucionar deadlock usando pthread_mutex_lock cuando ptr es NULL"
    d1 = router.route(q1)
    assert d1.strategy == RoutingStrategy.EXACT_LEXICAL
    assert d1.pool_depth == 20
    assert d1.lexical_weight == 1.0
    assert d1.dense_weight == 0.2
    assert d1.enable_rerank is False
    assert d1.use_facets is False

    # Contiene '%rax', '%rbx' y 'uint32_t'
    q2 = "mov %rax, %rbx con valor uint32_t"
    d2 = router.route(q2)
    assert d2.strategy == RoutingStrategy.EXACT_LEXICAL

    # Contiene 'malloc' y 'free'
    q3 = "depuración de malloc y free en heap"
    d3 = router.route(q3)
    assert d3.strategy == RoutingStrategy.EXACT_LEXICAL


def test_router_composite_faceted_classification_f1():
    """F1: count_matches(COMPOSITE_FACETED_INDICATORS) >= 1 -> COMPOSITE_FACETED (si no cumple >=2 exact)."""
    router = AdaptiveRetrievalRouter()

    q1 = "diferencias entre stack y heap en tiempo de ejecución"
    d1 = router.route(q1)
    assert d1.strategy == RoutingStrategy.COMPOSITE_FACETED
    assert d1.pool_depth == 50
    assert d1.lexical_weight == 0.6
    assert d1.dense_weight == 0.7
    assert d1.enable_rerank is True
    assert d1.use_facets is True

    q2 = "comparar ventajas y desventajas de paginación versus segmentación"
    d2 = router.route(q2)
    assert d2.strategy == RoutingStrategy.COMPOSITE_FACETED

    q3 = "pros y contras del paso de parámetros por valor vs referencia"
    d3 = router.route(q3)
    assert d3.strategy == RoutingStrategy.COMPOSITE_FACETED


def test_router_conceptual_semantic_classification_f1():
    """F1: Resto de consultas -> CONCEPTUAL_SEMANTIC."""
    router = AdaptiveRetrievalRouter()

    q1 = "explicar el concepto de condición de carrera"
    d1 = router.route(q1)
    assert d1.strategy == RoutingStrategy.CONCEPTUAL_SEMANTIC
    assert d1.pool_depth == 30
    assert d1.lexical_weight == 0.5
    assert d1.dense_weight == 0.8
    assert d1.enable_rerank is True
    assert d1.use_facets is False

    q2 = "¿cómo funciona la traducción de direcciones virtuales?"
    d2 = router.route(q2)
    assert d2.strategy == RoutingStrategy.CONCEPTUAL_SEMANTIC


def test_router_is_deterministic_f7():
    """F7: Misma query produce idéntica RouteDecision en 100 llamadas consecutivas y sin estado mutable."""
    router = AdaptiveRetrievalRouter()
    query = "¿cómo funciona pthread_mutex_lock cuando ptr es NULL?"

    decisions = [router.route(query) for _ in range(100)]

    # Todas las decisiones deben ser exactamente idénticas
    first = decisions[0]
    for d in decisions:
        assert d == first
        assert d.strategy == first.strategy
        assert d.pool_depth == first.pool_depth
        assert d.lexical_weight == first.lexical_weight
        assert d.dense_weight == first.dense_weight
        assert d.enable_rerank == first.enable_rerank
        assert d.use_facets == first.use_facets

    # Instancias separadas producen idéntico resultado
    router_alt = AdaptiveRetrievalRouter()
    assert router.route(query) == router_alt.route(query)


def test_router_empty_or_whitespace_query():
    """Manejo seguro de queries vacías."""
    router = AdaptiveRetrievalRouter()
    d_empty = router.route("")
    assert d_empty.strategy == RoutingStrategy.CONCEPTUAL_SEMANTIC
    assert d_empty.enable_rerank is False

    d_spaces = router.route("   \t\n  ")
    assert d_spaces.strategy == RoutingStrategy.CONCEPTUAL_SEMANTIC
