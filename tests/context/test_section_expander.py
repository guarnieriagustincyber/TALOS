"""Test suite for SectionExpander (Ola 5, Fase 5.4, E23, E26).

6 tests requeridos:
1. test_expansion_merges_contiguous    -> hits contiguos se fusionan
2. test_expansion_window_pm2           -> expande +-2 chunks máximo
3. test_expansion_respects_ceiling     -> nunca supera el budget
4. test_expansion_cuts_by_relevance    -> al llegar al techo, corta por BM25/relevancia
5. test_context_pack_has_provenance    -> cada chunk tiene source_id + page
6. test_no_floating_citations          -> citas apuntan a chunks del pack [CHUNK X | Pág Y]
"""

from study_engine.context.section_expander import SectionExpander
from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.search import SearchResult
from study_engine.contracts.source import Source, SourceRole
from study_engine.storage.knowledge_store import KnowledgeStore


def test_expansion_merges_contiguous() -> None:
    """1. Test that contiguous or overlapping seed hit windows are merged cleanly into a single span."""
    store = KnowledgeStore(":memory:")
    store.initialize()

    nb = Notebook(id="nb-os", name="Sistemas Operativos")
    store.create_notebook(nb)

    src_record = SourceRecord(
        source_id="src-tanenbaum",
        manifest=SourceManifest(
            source_id="src-tanenbaum",
            filename="tanenbaum.pdf",
            byte_size=1024,
            sha256="a" * 64,
        ),
        source=Source(source_id="src-tanenbaum", title="Tanenbaum Modern OS", role=SourceRole.PRIMARY),
    )
    store.save_source(src_record)
    store.link_source_to_notebook(nb.id, src_record.source_id)

    doc = Document(id="doc-mem", source_id=src_record.source_id, title="Gestión de Memoria")
    store.save_document(doc)

    chunks = [
        Chunk(
            id=f"chk-{i}",
            document_id=doc.id,
            source_id=src_record.source_id,
            content=f"Contenido del bloque {i} de memoria.",
            page_start=50 + i,
            page_end=50 + i,
            chapter="Memoria",
            section="Paginación",
            token_count=100,
            index=i,
            metadata={},
        )
        for i in range(12)
    ]
    store.save_chunks(chunks)

    # Seed hits at chunk 3 and chunk 5 (windows: [1, 5] and [3, 7]) -> merged window [1, 7]
    seed_results = [
        SearchResult(chunk_id="chk-3", document_id=doc.id, source_id=src_record.source_id, score=0.9, snippet="...", content="...", index=3, page_start=53),
        SearchResult(chunk_id="chk-5", document_id=doc.id, source_id=src_record.source_id, score=0.85, snippet="...", content="...", index=5, page_start=55),
    ]

    expander = SectionExpander(engine=store.engine, hard_ceiling_tokens=5000)
    expanded, text = expander.expand_results(seed_results)

    indices = [c.pos_index for c in expanded]
    assert indices == [1, 2, 3, 4, 5, 6, 7]
    assert len(expanded) == 7


def test_expansion_window_pm2() -> None:
    """2. Test that expansion is strictly bounded to +-2 chunks around seed hit."""
    store = KnowledgeStore(":memory:")
    store.initialize()

    nb = Notebook(id="nb-net", name="Redes")
    store.create_notebook(nb)

    src_record = SourceRecord(
        source_id="src-kurose",
        manifest=SourceManifest(
            source_id="src-kurose",
            filename="kurose.pdf",
            byte_size=1024,
            sha256="b" * 64,
        ),
        source=Source(source_id="src-kurose", title="Kurose Ross", role=SourceRole.PRIMARY),
    )
    store.save_source(src_record)
    store.link_source_to_notebook(nb.id, src_record.source_id)

    doc = Document(id="doc-tcp", source_id=src_record.source_id, title="Transporte")
    store.save_document(doc)

    chunks = [
        Chunk(
            id=f"chk-tcp-{i}",
            document_id=doc.id,
            source_id=src_record.source_id,
            content=f"Contenido TCP bloque {i}",
            page_start=100 + i,
            token_count=100,
            index=i,
            metadata={},
        )
        for i in range(15)
    ]
    store.save_chunks(chunks)

    # Seed hit at index 6 -> window is exactly [4, 8] (5 chunks)
    seeds = [
        SearchResult(chunk_id="chk-tcp-6", document_id=doc.id, source_id=src_record.source_id, score=0.95, snippet="...", content="...", index=6, page_start=106)
    ]

    expander = SectionExpander(engine=store.engine, hard_ceiling_tokens=10000)
    expanded, _ = expander.expand_results(seeds)

    indices = [c.pos_index for c in expanded]
    assert indices == [4, 5, 6, 7, 8]
    assert min(indices) == 6 - 2
    assert max(indices) == 6 + 2


def test_expansion_respects_ceiling() -> None:
    """3. Test that token hard ceiling is never breached."""
    store = KnowledgeStore(":memory:")
    store.initialize()

    nb = Notebook(id="nb-heavy", name="Heavy")
    store.create_notebook(nb)

    src_record = SourceRecord(
        source_id="src-heavy",
        manifest=SourceManifest(source_id="src-heavy", filename="h.pdf", byte_size=2048, sha256="c" * 64),
        source=Source(source_id="src-heavy", title="Heavy Book", role=SourceRole.PRIMARY),
    )
    store.save_source(src_record)
    store.link_source_to_notebook(nb.id, src_record.source_id)

    doc = Document(id="doc-heavy", source_id=src_record.source_id, title="Heavy Doc")
    store.save_document(doc)

    chunks = [
        Chunk(
            id=f"chk-h-{i}",
            document_id=doc.id,
            source_id=src_record.source_id,
            content="Texto pesado " * 100,
            page_start=i + 1,
            token_count=1000,
            index=i,
            metadata={},
        )
        for i in range(10)
    ]
    store.save_chunks(chunks)

    seeds = [
        SearchResult(chunk_id="chk-h-5", document_id=doc.id, source_id=src_record.source_id, score=0.99, snippet="...", content="", index=5)
    ]

    # Window would be [3, 7] -> 5 chunks = 5000 tokens. Ceiling = 2500 tokens.
    expander = SectionExpander(engine=store.engine, hard_ceiling_tokens=2500)
    expanded, _ = expander.expand_results(seeds)

    total_tokens = sum(c.token_count for c in expanded)
    assert total_tokens <= 2500
    assert len(expanded) <= 2


def test_expansion_cuts_by_relevance() -> None:
    """4. When ceiling is reached, pruning prioritizes seed hits and higher relevance."""
    store = KnowledgeStore(":memory:")
    store.initialize()

    nb = Notebook(id="nb-rev", name="Relevance")
    store.create_notebook(nb)

    src_record = SourceRecord(
        source_id="src-rev",
        manifest=SourceManifest(source_id="src-rev", filename="r.pdf", byte_size=1024, sha256="d" * 64),
        source=Source(source_id="src-rev", title="Rev Doc", role=SourceRole.PRIMARY),
    )
    store.save_source(src_record)
    store.link_source_to_notebook(nb.id, src_record.source_id)

    doc = Document(id="doc-rev", source_id=src_record.source_id, title="Rev Doc")
    store.save_document(doc)

    chunks = [
        Chunk(
            id=f"chk-r-{i}",
            document_id=doc.id,
            source_id=src_record.source_id,
            content=f"Chunk {i} relevante",
            page_start=i + 1,
            token_count=500,
            index=i,
            metadata={},
        )
        for i in range(8)
    ]
    store.save_chunks(chunks)

    # Seed hit is chunk 4 (high score)
    seeds = [
        SearchResult(chunk_id="chk-r-4", document_id=doc.id, source_id=src_record.source_id, score=0.98, snippet="...", content="", index=4)
    ]

    # Ceiling allows exactly 1 chunk (600 tokens)
    expander = SectionExpander(engine=store.engine, hard_ceiling_tokens=600)
    expanded, _ = expander.expand_results(seeds)

    assert len(expanded) == 1
    assert expanded[0].chunk_id == "chk-r-4"
    assert expanded[0].is_seed_hit is True


def test_context_pack_has_provenance() -> None:
    """5. Each expanded chunk retains authoritative source_id, document_id, and page_start."""
    store = KnowledgeStore(":memory:")
    store.initialize()

    nb = Notebook(id="nb-prov", name="Provenance")
    store.create_notebook(nb)

    src_record = SourceRecord(
        source_id="src-silberschatz",
        manifest=SourceManifest(source_id="src-silberschatz", filename="s.pdf", byte_size=1024, sha256="e" * 64),
        source=Source(source_id="src-silberschatz", title="Operating System Concepts", role=SourceRole.PRIMARY),
    )
    store.save_source(src_record)
    store.link_source_to_notebook(nb.id, src_record.source_id)

    doc = Document(id="doc-sync", source_id=src_record.source_id, title="Synchronization")
    store.save_document(doc)

    c = Chunk(
        id="chk-sem-1",
        document_id=doc.id,
        source_id=src_record.source_id,
        content="Los semáforos son variables protegidas...",
        page_start=234,
        token_count=80,
        index=1,
        metadata={},
    )
    store.save_chunks([c])

    seeds = [
        SearchResult(chunk_id="chk-sem-1", document_id=doc.id, source_id=src_record.source_id, score=0.91, snippet="...", content="...", index=1, page_start=234)
    ]

    expander = SectionExpander(engine=store.engine)
    meta_cache = {"src-silberschatz": {"title": "Operating System Concepts"}}
    expanded, _ = expander.expand_results(seeds, source_meta_cache=meta_cache)

    assert len(expanded) == 1
    chk = expanded[0]
    assert chk.source_id == "src-silberschatz"
    assert chk.source_title == "Operating System Concepts"
    assert chk.page_start == 234
    assert chk.document_id == doc.id


def test_no_floating_citations() -> None:
    """6. Formatted context injects explicit [CHUNK X | Pág Y | Source] tags (E26)."""
    store = KnowledgeStore(":memory:")
    store.initialize()

    nb = Notebook(id="nb-cite", name="Citations")
    store.create_notebook(nb)

    src_record = SourceRecord(
        source_id="src-c-lang",
        manifest=SourceManifest(source_id="src-c-lang", filename="c.pdf", byte_size=1024, sha256="f" * 64),
        source=Source(source_id="src-c-lang", title="K&R C", role=SourceRole.PRIMARY),
    )
    store.save_source(src_record)
    store.link_source_to_notebook(nb.id, src_record.source_id)

    doc = Document(id="doc-ptrs", source_id=src_record.source_id, title="Pointers")
    store.save_document(doc)

    chunks = [
        Chunk(
            id=f"chk-p-{i}",
            document_id=doc.id,
            source_id=src_record.source_id,
            content=f"Regla de punteros bloque {i}",
            page_start=80 + i,
            token_count=50,
            index=i,
            metadata={},
        )
        for i in range(5)
    ]
    store.save_chunks(chunks)

    seeds = [
        SearchResult(chunk_id="chk-p-2", document_id=doc.id, source_id=src_record.source_id, score=0.88, snippet="...", content="...", index=2, page_start=82)
    ]

    expander = SectionExpander(engine=store.engine)
    meta_cache = {"src-c-lang": {"title": "K&R C"}}
    _, formatted_text = expander.expand_results(seeds, source_meta_cache=meta_cache)

    assert "[CHUNK 2 | Pág 82 | K&R C]" in formatted_text
    assert "[CHUNK 0 | Pág 80 | K&R C]" in formatted_text
    assert "[CHUNK 4 | Pág 84 | K&R C]" in formatted_text
