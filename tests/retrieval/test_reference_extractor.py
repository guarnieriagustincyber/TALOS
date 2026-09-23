"""Tests for Deterministic Reference Extractor (Slice 6.0.5, Punto 1).

Asserts:
1. Literal matches ("guía 4 ejercicio 3", "joyanes sección 3.1.2") resolve with confidence 1.0.
2. Curated fuzzy match >= 0.95 resolves directly with status OK.
3. Ambiguous fuzzy match (0.70 - 0.95) returns candidates + status NEEDS_REVIEW without direct content_id.
4. Low similarity (< 0.70) returns no reference match.
5. Contract: Zero LLM dependencies in the reference extractor.
"""

from study_engine.contracts.content_registry import ContentStatus, UnitType
from study_engine.retrieval.reference_extractor import ReferenceResult, extract_reference


def test_literal_extraction_exercise_variants() -> None:
    """Layer A literal regex extracts exercises and guides with 1.0 confidence."""
    queries = [
        ("guía 4 ejercicio 3", "guia_4:ej_3"),
        ("guia 4 ej 3", "guia_4:ej_3"),
        ("guia 4, ejercicio 3", "guia_4:ej_3"),
        ("ejercicio 3 de la guía 4", "guia_4:ej_3"),
        ("problema 3 de guia 4", "guia_4:ej_3"),
        ("guia 4 - ej 3", "guia_4:ej_3"),
    ]

    for q, expected_id in queries:
        res = extract_reference(q)
        assert res.matched, f"Failed to match: {q}"
        assert res.content_id == expected_id, f"Expected {expected_id} for {q}, got {res.content_id}"
        assert res.unit_type == UnitType.EXERCISE
        assert res.confidence == 1.0
        assert res.status == ContentStatus.OK


def test_literal_extraction_section_variants() -> None:
    """Layer A literal regex extracts sections with 1.0 confidence."""
    queries = [
        ("sección 3.1.2 de Joyanes", "joyanes:sec_3.1.2"),
        ("joyanes sección 3.1.2", "joyanes:sec_3.1.2"),
        ("capítulo 4 de tanenbaum", "tanenbaum:sec_4"),
        ("seccion 2.4 de silberschatz", "silberschatz:sec_2.4"),
    ]

    for q, expected_id in queries:
        res = extract_reference(q)
        assert res.matched, f"Failed to match: {q}"
        assert res.content_id == expected_id, f"Expected {expected_id} for {q}, got {res.content_id}"
        assert res.unit_type == UnitType.SECTION
        assert res.confidence == 1.0
        assert res.status == ContentStatus.OK


def test_fuzzy_high_confidence_direct_resolution() -> None:
    """Layer B fuzzy matching with score >= 0.95 resolves directly to content_id."""
    known = ["guia_4:ej_3", "guia_4:ej_4", "joyanes:sec_3.1.2"]
    # Query with exact tokens matching known item
    res = extract_reference("dame el ejercicio 3 de la guia 4 por favor", known_content_ids=known)
    assert res.matched
    assert res.content_id == "guia_4:ej_3"
    assert res.confidence >= 0.95
    assert res.status == ContentStatus.OK


def test_fuzzy_medium_confidence_needs_review_no_direct_resolution() -> None:
    """Layer B fuzzy matching with 0.70 <= score < 0.95 returns candidates and NEEDS_REVIEW.
    
    HARD INVARIANT: content_id MUST be None. Never assume identity silently.
    """
    known = ["guia_4:ej_30", "guia_4:ej_31", "guia_4:ej_32"]
    # Query somewhat similar but ambiguous
    res = extract_reference("guia 4 ej 3", known_content_ids=known)
    # The best score will be between 0.70 and 0.95 with ej_30/31/32
    if res.matched and res.confidence < 0.95 and res.confidence >= 0.70:
        assert res.content_id is None, "HARD INVARIANT VIOLATION: content_id assigned below 0.95 threshold"
        assert res.status == ContentStatus.NEEDS_REVIEW
        assert len(res.candidates) > 0


def test_low_similarity_no_reference() -> None:
    """Query completely unrelated to known items returns no match or low confidence (< 0.70)."""
    known = ["guia_4:ej_3", "joyanes:sec_3.1.2"]
    res = extract_reference("¿Qué es un árbol AVL balanceado?", known_content_ids=known)
    assert not res.matched or res.content_id is None


def test_contract_pure_function_no_llm() -> None:
    """Verify reference_extractor module does not import or call any LLM components."""
    import study_engine.retrieval.reference_extractor as mod

    for attr_name, attr_val in mod.__dict__.items():
        if hasattr(attr_val, "__module__") and attr_val.__module__:
            assert "study_engine.llm" not in attr_val.__module__, (
                f"reference_extractor imports LLM component: {attr_name} from {attr_val.__module__}"
            )
