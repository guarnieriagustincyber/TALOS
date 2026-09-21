"""Unit tests for StageAwareDecomposer with G1-G4 deterministic guards."""

import pytest

from study_engine.retrieval.stage_aware_decomposer import (
    AtomicFacet,
    StageAwareDecomposer,
    compute_token_jaccard,
    extract_technical_anchors,
)


def test_extract_technical_anchors():
    query = "¿Cómo se relaciona el Program Counter con la física del stack frame y el análisis Big O?"
    anchors = extract_technical_anchors(query)
    assert "program counter" in anchors
    assert "stack frame" in anchors
    assert "big o" in anchors


def test_stage_aware_decomposition_composite_query():
    decomposer = StageAwareDecomposer(max_facets=3, min_facets=2)
    query = "Explicame el análisis del problema algorítmico, y cómo funciona la validación de tipos de entrada además de la formulación de proposiciones lógicas."
    result = decomposer.decompose(query=query, notebook_id="NB-1")

    assert not result.is_fallback
    assert result.validity_passed
    assert 2 <= len(result.facets) <= 3
    for f in result.facets:
        assert f.weight > 0.0
        assert len(f.text.split()) >= 3


def test_stage_aware_decomposition_simple_query_fallback():
    decomposer = StageAwareDecomposer(max_facets=3, min_facets=2)
    query = "¿Qué es una variable?"
    result = decomposer.decompose(query=query, notebook_id="NB-1")

    # Simple monolithic query cannot be split into 2-3 facets; must fallback safely
    assert result.is_fallback
    assert len(result.facets) == 1
    assert result.facets[0].facet_id == "f-global"
    assert result.facets[0].text == "¿Qué es una variable?"


def test_guard_g1_anchor_retention():
    decomposer = StageAwareDecomposer()
    query = "¿Cómo opera el Program Counter en saltos condicionales y el stack frame?"
    anchors = ["program counter", "stack frame"]

    # Valid facets containing all anchors
    facets_valid = [
        AtomicFacet(facet_id="f-1", text="operación del Program Counter en saltos condicionales"),
        AtomicFacet(facet_id="f-2", text="física del stack frame en memoria"),
    ]
    status, is_valid = decomposer.validate_decomposition(query, facets_valid, anchors, set())
    assert status["G1_anchor_retention"] is True
    assert is_valid is True

    # Invalid facets dropping "stack frame"
    facets_invalid = [
        AtomicFacet(facet_id="f-1", text="operación del Program Counter en saltos condicionales"),
        AtomicFacet(facet_id="f-2", text="comportamiento de la memoria general"),
    ]
    status, is_valid = decomposer.validate_decomposition(query, facets_invalid, anchors, set())
    assert status["G1_anchor_retention"] is False
    assert is_valid is False


def test_guard_g3_cardinality_bound():
    decomposer = StageAwareDecomposer(min_facets=2, max_facets=3)
    query = "consulta de prueba con varios temas"
    anchors = []

    # 4 facets exceeds max_facets=3
    facets_4 = [
        AtomicFacet(facet_id=f"f-{i}", text=f"faceta {i} de prueba tecnica") for i in range(4)
    ]
    status, is_valid = decomposer.validate_decomposition(query, facets_4, anchors, set())
    assert status["G3_cardinality_bound"] is False
    assert is_valid is False

    # 1 facet below min_facets=2
    facets_1 = [AtomicFacet(facet_id="f-1", text="faceta unica de prueba tecnica")]
    status, is_valid = decomposer.validate_decomposition(query, facets_1, anchors, set())
    assert status["G3_cardinality_bound"] is False
    assert is_valid is False


def test_guard_g4_non_duplication():
    decomposer = StageAwareDecomposer()
    query = "¿Cómo funciona la memoria RAM y la memoria RAM?"
    facets_dup = [
        AtomicFacet(facet_id="f-1", text="cómo funciona la memoria RAM del sistema"),
        AtomicFacet(facet_id="f-2", text="cómo funciona la memoria RAM del sistema"),
    ]
    status, is_valid = decomposer.validate_decomposition(query, facets_dup, [], set())
    assert status["G4_non_triviality"] is False
    assert is_valid is False


def test_score_facet_coverage():
    facet = AtomicFacet(
        facet_id="f-1",
        text="análisis del problema algorítmico",
        anchor_terms=["algoritmo"],
    )
    cand_match = "La fase inicial consiste en el análisis riguroso del problema mediante un algoritmo estructurado."
    cand_unrelated = "La arquitectura Von Neumann tiene un bus de datos y bus de direcciones."

    cov_high = StageAwareDecomposer.score_facet_coverage(cand_match, facet)
    cov_low = StageAwareDecomposer.score_facet_coverage(cand_unrelated, facet)

    assert cov_high > 0.50
    assert cov_low < 0.20
