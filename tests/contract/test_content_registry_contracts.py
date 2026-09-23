"""Contract tests for Content Registry (Slice 6.0.5).

Asserts canonical invariants:
1. UnitType contains exclusively {'exercise', 'section'}.
2. ContentStatus contains exclusively {'ok', 'needs_review'}.
3. ContentItem roundtrip serialization.
"""

from study_engine.contracts.content_registry import ContentItem, ContentStatus, UnitType


def test_unit_type_enum_strictly_restricted() -> None:
    """Invariant: UnitType contains ONLY 'exercise' and 'section'.
    
    Adding 'example' or 'definition' requires parser and tests in the exact same commit.
    """
    valid_values = {t.value for t in UnitType}
    assert valid_values == {"exercise", "section"}, (
        f"UnitType altered without parser/test synchronization: {valid_values}"
    )
    assert len(UnitType) == 2


def test_content_status_enum_invariants() -> None:
    """ContentStatus contains OK and NEEDS_REVIEW."""
    assert {s.value for s in ContentStatus} == {"ok", "needs_review"}


def test_content_item_roundtrip_serialization() -> None:
    """ContentItem roundtrip via to_dict and from_dict preserves all fields."""
    item = ContentItem(
        content_id="guia4:ej3",
        source_id="src-guia-4",
        unit_type=UnitType.EXERCISE,
        statement_text="Escribir un programa que invierta una lista enlazada.",
        chunk_ids=["chk-g4-01", "chk-g4-02"],
        solution_chunk_ids=["chk-g4-sol-01"],
        status=ContentStatus.OK,
        metadata={"subject": "Algoritmos", "difficulty": "medium"},
    )

    data = item.to_dict()
    assert data["content_id"] == "guia4:ej3"
    assert data["source_id"] == "src-guia-4"
    assert data["unit_type"] == "exercise"
    assert data["statement_text"] == "Escribir un programa que invierta una lista enlazada."
    assert data["chunk_ids"] == ["chk-g4-01", "chk-g4-02"]
    assert data["solution_chunk_ids"] == ["chk-g4-sol-01"]
    assert data["status"] == "ok"
    assert data["metadata"]["subject"] == "Algoritmos"

    restored = ContentItem.from_dict(data)
    assert restored.content_id == item.content_id
    assert restored.source_id == item.source_id
    assert restored.unit_type == UnitType.EXERCISE
    assert restored.statement_text == item.statement_text
    assert restored.chunk_ids == item.chunk_ids
    assert restored.solution_chunk_ids == item.solution_chunk_ids
    assert restored.status == ContentStatus.OK
    assert restored.metadata == item.metadata
