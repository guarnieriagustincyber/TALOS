"""Contract tests for SQLiteChunkRepository exceptions, constraints and conflict detection."""

from pathlib import Path
import pytest

from study_engine.contracts.catalog import (
    ChunkConflictError,
    ChunkNotFoundError,
    DocumentNotFoundError,
    SourceNotFoundError,
    SourceRecord,
)
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.storage.repositories import (
    SQLiteChunkRepository,
    SQLiteDocumentRepository,
    SQLiteSourceRepository,
)
from study_engine.storage.sqlite_engine import SQLiteStorageEngine


def setup_test_db(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "contract_chunks.db")
    engine.initialize_schema()

    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)
    chunk_repo = SQLiteChunkRepository(engine)

    manifest = SourceManifest(
        source_id="src-1",
        filename="book.pdf",
        byte_size=500,
        sha256="a" * 64,
    )
    src_repo.save(SourceRecord(source_id="src-1", manifest=manifest))
    doc_repo.save(Document(id="doc-1", source_id="src-1", title="Doc 1", content="Text"))

    return chunk_repo


def test_chunk_repository_not_found(tmp_path: Path):
    chunk_repo = setup_test_db(tmp_path)

    with pytest.raises(ChunkNotFoundError):
        chunk_repo.get("non-existent-chunk")

    with pytest.raises(ChunkNotFoundError):
        chunk_repo.get("")


def test_chunk_repository_rejects_missing_document(tmp_path: Path):
    chunk_repo = setup_test_db(tmp_path)

    chunk = Chunk(
        id="orphan:chunk_0000",
        document_id="missing-doc",
        source_id="src-1",
        content="Orphan chunk",
        index=0,
    )
    with pytest.raises(DocumentNotFoundError) as exc_info:
        chunk_repo.save_chunks([chunk])
    assert "missing-doc" in str(exc_info.value)


def test_chunk_repository_rejects_missing_source(tmp_path: Path):
    chunk_repo = setup_test_db(tmp_path)

    chunk = Chunk(
        id="doc-1:chunk_0000",
        document_id="doc-1",
        source_id="missing-source",
        content="Invalid source chunk",
        index=0,
    )
    with pytest.raises(SourceNotFoundError) as exc_info:
        chunk_repo.save_chunks([chunk])
    assert "missing-source" in str(exc_info.value)


def test_chunk_repository_rejects_duplicate_id_in_same_batch(tmp_path: Path):
    chunk_repo = setup_test_db(tmp_path)

    c1 = Chunk(id="doc-1:chunk_0000", document_id="doc-1", source_id="src-1", content="A", index=0)
    c2 = Chunk(id="doc-1:chunk_0000", document_id="doc-1", source_id="src-1", content="B", index=1)

    with pytest.raises(ChunkConflictError) as exc_info:
        chunk_repo.save_chunks([c1, c2])
    assert "Duplicate chunk ID" in str(exc_info.value)


def test_chunk_repository_rejects_duplicate_index_for_same_document(tmp_path: Path):
    chunk_repo = setup_test_db(tmp_path)

    c1 = Chunk(id="doc-1:chunk_0000", document_id="doc-1", source_id="src-1", content="A", index=0)
    c2 = Chunk(id="doc-1:chunk_0001", document_id="doc-1", source_id="src-1", content="B", index=0)

    with pytest.raises(ChunkConflictError) as exc_info:
        chunk_repo.save_chunks([c1, c2])
    assert "Duplicate (document_id, index) pair" in str(exc_info.value)


def test_chunk_repository_rejects_divergent_content_on_same_id(tmp_path: Path):
    chunk_repo = setup_test_db(tmp_path)

    c1 = Chunk(id="doc-1:chunk_0000", document_id="doc-1", source_id="src-1", content="Original content", index=0)
    chunk_repo.save_chunks([c1])

    c2 = Chunk(id="doc-1:chunk_0000", document_id="doc-1", source_id="src-1", content="Divergent content", index=0)
    with pytest.raises(ChunkConflictError) as exc_info:
        chunk_repo.save_chunks([c2])
    assert "conflicts with already registered chunk" in str(exc_info.value)


def test_chunk_repository_rejects_invalid_type(tmp_path: Path):
    chunk_repo = setup_test_db(tmp_path)

    with pytest.raises(TypeError):
        chunk_repo.save_chunks(["not-a-chunk"])


def test_chunk_repository_rejects_source_id_mismatch_with_parent_document(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "mismatch.db")
    engine.initialize_schema()
    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)
    chunk_repo = SQLiteChunkRepository(engine)

    # 2 sources
    src_repo.save(SourceRecord(source_id="src-a", manifest=SourceManifest(source_id="src-a", filename="a.pdf", byte_size=10, sha256="a"*64)))
    src_repo.save(SourceRecord(source_id="src-b", manifest=SourceManifest(source_id="src-b", filename="b.pdf", byte_size=10, sha256="b"*64)))

    # doc-a belongs to src-a
    doc_repo.save(Document(id="doc-a", source_id="src-a", title="Doc A", content="Text"))

    # Chunk points to doc-a but claims source_id="src-b"
    mismatched = Chunk(id="doc-a:chunk_00", document_id="doc-a", source_id="src-b", content="Mismatch", index=0)
    with pytest.raises(ChunkConflictError) as exc_info:
        chunk_repo.save_chunks([mismatched])
    assert "does not match parent document" in str(exc_info.value)

