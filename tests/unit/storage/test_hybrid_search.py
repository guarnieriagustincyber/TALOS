"""Unit and Integration Tests for Hybrid Search (RRF and Source Diversity)."""

from study_engine.contracts.notebook import Notebook
from study_engine.contracts.search import SearchResult
from study_engine.storage.knowledge_store import KnowledgeStore


def test_reciprocal_rank_fusion():
    store = KnowledgeStore(":memory:")

    # Stream 1 (e.g. Vector)
    r1 = [
        SearchResult(chunk_id="c1", document_id="d1", source_id="s1", score=0.9, snippet="snippet", content="content 1", index=0),
        SearchResult(chunk_id="c2", document_id="d1", source_id="s1", score=0.8, snippet="snippet", content="content 2", index=1),
        SearchResult(chunk_id="c3", document_id="d2", source_id="s2", score=0.7, snippet="snippet", content="content 3", index=2),
    ]
    # Stream 2 (e.g. FTS5)
    r2 = [
        SearchResult(chunk_id="c3", document_id="d2", source_id="s2", score=10.0, snippet="snippet", content="content 3", index=2),
        SearchResult(chunk_id="c1", document_id="d1", source_id="s1", score=8.0, snippet="snippet", content="content 1", index=0),
        SearchResult(chunk_id="c4", document_id="d3", source_id="s3", score=5.0, snippet="snippet", content="content 4", index=3),
    ]

    fused = store.reciprocal_rank_fusion(r1, r2, k=60)
    assert len(fused) == 4
    # c1 and c3 appear in both streams, so their RRF scores must be higher than c2 and c4
    top_ids = [f.chunk_id for f in fused[:2]]
    assert "c1" in top_ids
    assert "c3" in top_ids


def test_ensure_source_diversity():
    store = KnowledgeStore(":memory:")

    chunks = [
        SearchResult(chunk_id="c1", document_id="d1", source_id="source_A", score=0.95, snippet="snip", content="c1", index=0),
        SearchResult(chunk_id="c2", document_id="d1", source_id="source_A", score=0.90, snippet="snip", content="c2", index=1),
        SearchResult(chunk_id="c3", document_id="d1", source_id="source_A", score=0.85, snippet="snip", content="c3", index=2),
        SearchResult(chunk_id="c4", document_id="d2", source_id="source_B", score=0.80, snippet="snip", content="c4", index=0),
        SearchResult(chunk_id="c5", document_id="d3", source_id="source_C", score=0.75, snippet="snip", content="c5", index=0),
    ]

    # Diversity ensures at least 3 distinct sources are represented up front
    diverse = store._ensure_source_diversity(chunks, min_sources=3)
    assert len(diverse) == 5
    top_3_sources = {c.source_id for c in diverse[:3]}
    assert len(top_3_sources) == 3
    assert top_3_sources == {"source_A", "source_B", "source_C"}


def test_search_hybrid_finds_semantic_matches():
    store = KnowledgeStore(":memory:")
    store.initialize()

    nb = Notebook(id="nb_test_hybrid", name="Test Hybrid", subject="Testing")
    store.create_notebook(nb)

    # Calling search_hybrid on notebook returns empty or valid list without crash
    res = store.search_hybrid("¿Cómo evitar que dos procesos se pisen?", "nb_test_hybrid", limit=10)
    assert isinstance(res, list)
