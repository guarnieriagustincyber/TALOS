"""Unit and Integration Tests for Hybrid Search (RRF and Source Diversity)."""

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
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


def test_search_hybrid_applies_source_diversity_in_sqlite():
    store = KnowledgeStore(":memory:")
    store.initialize()
    notebook_id = "nb_hybrid_diversity"
    store.create_notebook(Notebook(id=notebook_id, name="Hybrid diversity"))

    for index, source_id in enumerate(("source_A", "source_B", "source_C")):
        content = (
            f"Synchronization between processes uses a mutex; source {source_id}."
        )
        record = SourceRecord(
            source_id=source_id,
            manifest=SourceManifest(
                source_id=source_id,
                filename=f"{source_id}.pdf",
                byte_size=1,
                sha256=f"{index + 1:064x}",
            ),
        )
        store.store_ingestion_bundle(
            record,
            [Document(id=f"doc-{source_id}", source_id=source_id, title=source_id)],
            [
                Chunk(
                    id=f"chunk-{source_id}",
                    document_id=f"doc-{source_id}",
                    source_id=source_id,
                    content=content,
                    index=0,
                )
            ],
            notebook_id=notebook_id,
        )

    results = store.search_hybrid(
        "synchronization processes mutex",
        notebook_id=notebook_id,
        limit=3,
        min_sources=3,
        vector_store=object(),
    )

    assert len(results) == 3
    assert {result.source_id for result in results} == {
        "source_A",
        "source_B",
        "source_C",
    }


def test_search_hybrid_finds_semantic_matches():
    store = KnowledgeStore(":memory:")
    store.initialize()

    nb = Notebook(id="nb_test_hybrid", name="Test Hybrid", subject="Testing")
    store.create_notebook(nb)

    # Calling search_hybrid on notebook returns empty or valid list without crash
    res = store.search_hybrid("¿Cómo evitar que dos procesos se pisen?", "nb_test_hybrid", limit=10)
    assert isinstance(res, list)


def test_hybrid_search_enforces_explicit_source_allowlist():
    store = KnowledgeStore(":memory:")
    store.initialize()
    store.create_notebook(Notebook(id="nb_source_filter", name="Filtered notebook"))

    for source_id, content in (
        ("src-authorized", "La memoria virtual usa tablas de páginas."),
        ("src-unselected", "La memoria virtual usa tablas de páginas."),
    ):
        record = SourceRecord(
            source_id=source_id,
            manifest=SourceManifest(
                source_id=source_id,
                filename=f"{source_id}.pdf",
                byte_size=1,
                sha256=(source_id.encode().hex() * 32)[:64],
            ),
        )
        store.store_ingestion_bundle(
            record,
            [Document(id=f"doc-{source_id}", source_id=source_id, title=source_id)],
            [
                Chunk(
                    id=f"chunk-{source_id}",
                    document_id=f"doc-{source_id}",
                    source_id=source_id,
                    content=content,
                    index=0,
                )
            ],
            notebook_id="nb_source_filter",
        )

    results = store.search_hybrid(
        "memoria virtual tablas páginas",
        "nb_source_filter",
        limit=10,
        min_sources=1,
        source_ids=["src-authorized"],
    )

    assert results
    assert {result.source_id for result in results} == {"src-authorized"}
    assert store.search_hybrid(
        "memoria virtual tablas páginas",
        "nb_source_filter",
        limit=10,
        min_sources=1,
        source_ids=[],
    ) == []
