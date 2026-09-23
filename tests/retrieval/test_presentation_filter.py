"""Tests for Presentation Filter and Anti-Leakage Invariants (Slice 6.0.5, Punto 2).

Asserts:
1. Universal anti-leakage: Solution chunks are intercepted and removed.
2. Fail-closed boundary: If all candidate chunks are solutions, returns empty list with had_solution_removed=True.
3. No over-filtering: Legitimate statement chunks pass through intact.
4. Polymorphic support: Works with strings, dicts, Chunk, and SearchResult objects.
"""

from study_engine.contracts.chunk import Chunk
from study_engine.contracts.search import SearchResult
from study_engine.retrieval.presentation_filter import filter_chunk_ids, filter_presentation


class DummyRegistry:
    """Mock registry exposing get_solution_chunk_ids."""

    def __init__(self, solution_ids: set) -> None:
        self._solutions = solution_ids

    def get_solution_chunk_ids(self) -> set:
        return self._solutions


def test_anti_leakage_filters_solution_chunks() -> None:
    """Universal anti-leakage intercepts solution chunks from list of SearchResults."""
    registry = DummyRegistry(solution_ids={"chk-sol-1", "chk-sol-2"})

    candidates = [
        SearchResult(chunk_id="chk-stmt-1", document_id="d1", source_id="s1", score=0.9, snippet="...", content="statement 1", index=0),
        SearchResult(chunk_id="chk-sol-1", document_id="d1", source_id="s1", score=0.88, snippet="...", content="sol 1", index=1),
        SearchResult(chunk_id="chk-stmt-2", document_id="d1", source_id="s1", score=0.85, snippet="...", content="statement 2", index=2),
    ]

    clean_chunks, had_removed = filter_presentation(candidates, registry)
    assert had_removed is True
    assert len(clean_chunks) == 2
    assert [c.chunk_id for c in clean_chunks] == ["chk-stmt-1", "chk-stmt-2"]


def test_fail_closed_edge_when_all_chunks_are_solutions() -> None:
    """If all retrieved chunks happen to be solution chunks, returns empty list and had_removed=True."""
    registry = DummyRegistry(solution_ids={"chk-sol-1", "chk-sol-2"})

    candidates = [
        SearchResult(chunk_id="chk-sol-1", document_id="d1", source_id="s1", score=0.9, snippet="...", content="sol 1", index=0),
        SearchResult(chunk_id="chk-sol-2", document_id="d1", source_id="s1", score=0.88, snippet="...", content="sol 2", index=1),
    ]

    clean_chunks, had_removed = filter_presentation(candidates, registry)
    assert had_removed is True
    assert len(clean_chunks) == 0


def test_no_overfiltering_preserves_all_legitimate_chunks() -> None:
    """Chunks not present in solution set pass completely untouched."""
    registry = DummyRegistry(solution_ids={"chk-sol-99"})

    candidates = [
        SearchResult(chunk_id="chk-stmt-1", document_id="d1", source_id="s1", score=0.9, snippet="...", content="stmt 1", index=0),
        SearchResult(chunk_id="chk-stmt-2", document_id="d1", source_id="s1", score=0.85, snippet="...", content="stmt 2", index=1),
    ]

    clean_chunks, had_removed = filter_presentation(candidates, registry)
    assert had_removed is False
    assert len(clean_chunks) == 2
    assert [c.chunk_id for c in clean_chunks] == ["chk-stmt-1", "chk-stmt-2"]


def test_polymorphic_filter_chunk_ids_and_dicts() -> None:
    """Filter operates uniformly on strings, dicts, and Chunk domain objects."""
    registry = DummyRegistry(solution_ids={"sol-1"})

    # 1. Plain string IDs
    cids = ["stmt-1", "sol-1", "stmt-2"]
    clean_ids, removed = filter_chunk_ids(cids, registry)
    assert removed is True
    assert clean_ids == ["stmt-1", "stmt-2"]

    # 2. Dicts
    dict_chunks = [{"id": "stmt-1", "text": "foo"}, {"id": "sol-1", "text": "bar"}]
    clean_dicts, removed = filter_presentation(dict_chunks, registry)
    assert removed is True
    assert len(clean_dicts) == 1
    assert clean_dicts[0]["id"] == "stmt-1"
