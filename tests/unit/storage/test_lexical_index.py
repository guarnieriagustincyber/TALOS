"""Unit tests for SQLiteLexicalIndex and FTS5 search functionality."""

from pathlib import Path
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.storage.lexical_index import SQLiteLexicalIndex
from study_engine.storage.repositories import (
    SQLiteChunkRepository,
    SQLiteDocumentRepository,
    SQLiteSourceRepository,
)
from study_engine.storage.sqlite_engine import SQLiteStorageEngine


def setup_index(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "lexical.db")
    engine.initialize_schema()

    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)
    chunk_repo = SQLiteChunkRepository(engine)
    lexical_index = SQLiteLexicalIndex(engine)

    # Seed 2 sources
    src_repo.save(SourceRecord(
        source_id="src-joyanes",
        manifest=SourceManifest(source_id="src-joyanes", filename="j.pdf", byte_size=10, sha256="1"*64)
    ))
    src_repo.save(SourceRecord(
        source_id="src-tanenbaum",
        manifest=SourceManifest(source_id="src-tanenbaum", filename="t.pdf", byte_size=10, sha256="2"*64)
    ))

    # Seed 2 documents
    doc_repo.save(Document(id="doc-prog", source_id="src-joyanes", title="Programación", content="Texto"))
    doc_repo.save(Document(id="doc-so", source_id="src-tanenbaum", title="Sistemas", content="Texto"))

    # Seed chunks
    chunks = [
        Chunk(
            id="doc-prog:chunk_00",
            document_id="doc-prog",
            source_id="src-joyanes",
            content="Introducción a la programación en C y punteros a memoria.",
            index=0,
        ),
        Chunk(
            id="doc-prog:chunk_01",
            document_id="doc-prog",
            source_id="src-joyanes",
            content="Árbol binario de búsqueda y balanceo de memoria.",
            index=1,
        ),
        Chunk(
            id="doc-so:chunk_00",
            document_id="doc-so",
            source_id="src-tanenbaum",
            content="Gestión de memoria virtual, paginación y marcos de página en SO.",
            index=0,
        ),
    ]
    chunk_repo.save_chunks(chunks)

    return engine, lexical_index


def test_lexical_index_basic_search_and_snippet(tmp_path: Path):
    _, lexical_index = setup_index(tmp_path)

    results = lexical_index.search("punteros")
    assert len(results) == 1
    hit = results[0]
    assert hit.chunk_id == "doc-prog:chunk_00"
    assert hit.document_id == "doc-prog"
    assert hit.source_id == "src-joyanes"
    assert hit.score > 0
    assert "[MATCH]punteros[/MATCH]" in hit.snippet
    assert "Introducción a la programación" in hit.content
    assert hit.index == 0


def test_lexical_index_accent_and_case_insensitivity(tmp_path: Path):
    _, lexical_index = setup_index(tmp_path)

    # Search without accent "arbol" should match "Árbol"
    results_no_accent = lexical_index.search("arbol")
    assert len(results_no_accent) == 1
    assert results_no_accent[0].chunk_id == "doc-prog:chunk_01"

    # Search with uppercase accent "ÁRBOL"
    results_upper = lexical_index.search("ÁRBOL")
    assert len(results_upper) == 1
    assert results_upper[0].chunk_id == "doc-prog:chunk_01"

    # Search "programacion" without accent matches "programación"
    results_prog = lexical_index.search("programacion")
    assert len(results_prog) == 1
    assert results_prog[0].chunk_id == "doc-prog:chunk_00"


def test_lexical_index_filtering_by_source_and_document(tmp_path: Path):
    _, lexical_index = setup_index(tmp_path)

    # Word "memoria" appears in all 3 chunks
    all_hits = lexical_index.search("memoria")
    assert len(all_hits) == 3

    # Filter by source
    joyanes_hits = lexical_index.search("memoria", source_id="src-joyanes")
    assert len(joyanes_hits) == 2
    assert all(h.source_id == "src-joyanes" for h in joyanes_hits)

    # Filter by document
    so_hits = lexical_index.search("memoria", document_id="doc-so")
    assert len(so_hits) == 1
    assert so_hits[0].document_id == "doc-so"


def test_lexical_index_empty_and_limit_edge_cases(tmp_path: Path):
    _, lexical_index = setup_index(tmp_path)

    assert lexical_index.search("") == []
    assert lexical_index.search("   \n\t  ") == []
    assert lexical_index.search("memoria", limit=0) == []
    assert lexical_index.search("memoria", limit=-5) == []

    top_1 = lexical_index.search("memoria", limit=1)
    assert len(top_1) == 1


def test_lexical_index_rebuild_and_count(tmp_path: Path):
    _, lexical_index = setup_index(tmp_path)

    assert lexical_index.count() == 3
    # Rebuild must execute without error
    lexical_index.rebuild()
    assert lexical_index.count() == 3
