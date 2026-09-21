"""Unit tests for SQLiteChunkRepository."""

from pathlib import Path
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.storage.repositories import (
    SQLiteChunkRepository,
    SQLiteDocumentRepository,
    SQLiteSourceRepository,
)
from study_engine.storage.sqlite_engine import SQLiteStorageEngine


def setup_test_environment(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "chunks.db")
    engine.initialize_schema()

    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)
    chunk_repo = SQLiteChunkRepository(engine)

    # Seed source and document
    manifest = SourceManifest(
        source_id="src-1",
        filename="joyanes.pdf",
        byte_size=1000,
        sha256="1" * 64,
    )
    src_repo.save(SourceRecord(source_id="src-1", manifest=manifest))

    doc = Document(
        id="doc-1",
        source_id="src-1",
        title="Capítulo 1",
        content="Texto de prueba para el documento número 1.",
    )
    doc_repo.save(doc)

    return engine, src_repo, doc_repo, chunk_repo


def test_chunk_repository_empty_batch(tmp_path: Path):
    _, _, _, chunk_repo = setup_test_environment(tmp_path)
    assert chunk_repo.save_chunks([]) == 0
    assert chunk_repo.count() == 0


def test_chunk_repository_save_and_get(tmp_path: Path):
    _, _, _, chunk_repo = setup_test_environment(tmp_path)

    chunk = Chunk(
        id="doc-1:chunk_0000",
        document_id="doc-1",
        source_id="src-1",
        content="Primer chunk del documento.",
        page_start=1,
        page_end=2,
        chapter="Cap 1",
        section="Sec 1.1",
        token_count=None,
        index=0,
        metadata={"char_start": 0, "char_end": 27},
    )

    inserted = chunk_repo.save_chunks([chunk])
    assert inserted == 1
    assert chunk_repo.count() == 1
    assert chunk_repo.contains("doc-1:chunk_0000") is True
    assert chunk_repo.contains("missing") is False
    assert chunk_repo.contains("") is False
    assert chunk_repo.contains(None) is False

    retrieved = chunk_repo.get("doc-1:chunk_0000")
    assert retrieved.id == chunk.id
    assert retrieved.document_id == "doc-1"
    assert retrieved.source_id == "src-1"
    assert retrieved.content == chunk.content
    assert retrieved.index == 0
    assert retrieved.metadata["char_start"] == 0
    assert retrieved.chapter == "Cap 1"


def test_chunk_repository_idempotent_save(tmp_path: Path):
    _, _, _, chunk_repo = setup_test_environment(tmp_path)

    chunk = Chunk(
        id="doc-1:chunk_0000",
        document_id="doc-1",
        source_id="src-1",
        content="Contenido idéntico.",
        index=0,
    )

    assert chunk_repo.save_chunks([chunk]) == 1
    # Repeated save of exact same chunk is a clean no-op
    assert chunk_repo.save_chunks([chunk]) == 0
    assert chunk_repo.count() == 1


def test_chunk_repository_list_by_document_strictly_ordered(tmp_path: Path):
    _, _, _, chunk_repo = setup_test_environment(tmp_path)

    chunks = [
        Chunk(id=f"doc-1:chunk_{i:04d}", document_id="doc-1", source_id="src-1", content=f"Chunk {i}", index=i)
        for i in range(5)
    ]
    # Pass in shuffled/reverse order to test DB sorting
    chunk_repo.save_chunks(list(reversed(chunks)))

    retrieved = chunk_repo.list_by_document("doc-1")
    assert len(retrieved) == 5
    assert [c.index for c in retrieved] == [0, 1, 2, 3, 4]
    assert [c.content for c in retrieved] == [f"Chunk {i}" for i in range(5)]

    assert chunk_repo.list_by_document("") == []
    assert chunk_repo.list_by_document(None) == []


def test_chunk_repository_list_by_source_and_pagination(tmp_path: Path):
    _, _, doc_repo, chunk_repo = setup_test_environment(tmp_path)

    # Add second document
    doc_repo.save(Document(id="doc-2", source_id="src-1", title="Doc 2", content="Text 2"))

    chunks = [
        Chunk(id=f"doc-1:chunk_{i:04d}", document_id="doc-1", source_id="src-1", content=f"D1-{i}", index=i)
        for i in range(3)
    ] + [
        Chunk(id=f"doc-2:chunk_{i:04d}", document_id="doc-2", source_id="src-1", content=f"D2-{i}", index=i)
        for i in range(3)
    ]
    chunk_repo.save_chunks(chunks)

    all_src_chunks = chunk_repo.list_by_source("src-1")
    assert len(all_src_chunks) == 6

    # Test pagination
    page1 = chunk_repo.list_by_source("src-1", limit=2, offset=0)
    page2 = chunk_repo.list_by_source("src-1", limit=2, offset=2)
    assert len(page1) == 2
    assert len(page2) == 2
    assert [c.id for c in page1] == ["doc-1:chunk_0000", "doc-1:chunk_0001"]
    assert [c.id for c in page2] == ["doc-1:chunk_0002", "doc-2:chunk_0000"]

    assert chunk_repo.list_by_source("") == []
    assert chunk_repo.list_by_source(None) == []


def test_chunk_repository_delete_by_document(tmp_path: Path):
    _, _, doc_repo, chunk_repo = setup_test_environment(tmp_path)

    doc_repo.save(Document(id="doc-2", source_id="src-1", title="Doc 2", content="Text 2"))
    chunk_repo.save_chunks([
        Chunk(id="doc-1:chunk_0000", document_id="doc-1", source_id="src-1", content="C1", index=0),
        Chunk(id="doc-2:chunk_0000", document_id="doc-2", source_id="src-1", content="C2", index=0),
    ])

    assert chunk_repo.count() == 2
    deleted = chunk_repo.delete_by_document("doc-1")
    assert deleted == 1
    assert chunk_repo.count() == 1
    assert chunk_repo.contains("doc-1:chunk_0000") is False
    assert chunk_repo.contains("doc-2:chunk_0000") is True


def test_chunk_repository_counts_with_filters(tmp_path: Path):
    _, _, doc_repo, chunk_repo = setup_test_environment(tmp_path)

    doc_repo.save(Document(id="doc-2", source_id="src-1", title="Doc 2", content="Text 2"))
    chunk_repo.save_chunks([
        Chunk(id="doc-1:chunk_0000", document_id="doc-1", source_id="src-1", content="C1", index=0),
        Chunk(id="doc-1:chunk_0001", document_id="doc-1", source_id="src-1", content="C1b", index=1),
        Chunk(id="doc-2:chunk_0000", document_id="doc-2", source_id="src-1", content="C2", index=0),
    ])

    assert chunk_repo.count() == 3
    assert chunk_repo.count(document_id="doc-1") == 2
    assert chunk_repo.count(document_id="doc-2") == 1
    assert chunk_repo.count(source_id="src-1") == 3
    assert chunk_repo.count(source_id="missing") == 0
