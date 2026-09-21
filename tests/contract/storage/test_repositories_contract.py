"""Contract tests for repository error behaviors, integrity and conflicts."""

from pathlib import Path
import pytest

from study_engine.contracts.catalog import (
    DocumentConflictError,
    DocumentNotFoundError,
    SourceConflictError,
    SourceNotFoundError,
    SourceRecord,
)
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.source import Source
from study_engine.storage.repositories import (
    SQLiteDocumentRepository,
    SQLiteSourceRepository,
)
from study_engine.storage.sqlite_engine import SQLiteStorageEngine


def create_record(source_id: str, sha256: str, meta: dict = None, title: str = "Title") -> SourceRecord:
    manifest = SourceManifest(
        source_id=source_id,
        filename="test.pdf",
        byte_size=500,
        sha256=sha256,
    )
    source_obj = Source(source_id=source_id, title=title)
    return SourceRecord(
        source_id=source_id,
        manifest=manifest,
        source=source_obj,
        metadata=meta or {},
    )


def test_source_repository_not_found(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "test.db")
    engine.initialize_schema()
    repo = SQLiteSourceRepository(engine)

    with pytest.raises(SourceNotFoundError):
        repo.get("non-existent")


def test_source_repository_rejects_conflicting_sha256(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "test.db")
    engine.initialize_schema()
    repo = SQLiteSourceRepository(engine)

    rec1 = create_record("src-1", "a" * 64)
    repo.save(rec1)

    rec2 = create_record("src-1", "b" * 64)
    with pytest.raises(SourceConflictError) as exc_info:
        repo.save(rec2)
    assert "differs from incoming" in str(exc_info.value)


def test_source_repository_rejects_divergent_metadata(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "test.db")
    engine.initialize_schema()
    repo = SQLiteSourceRepository(engine)

    rec1 = create_record("src-1", "a" * 64, meta={"tag": "v1"})
    repo.save(rec1)

    rec2 = create_record("src-1", "a" * 64, meta={"tag": "v2"})
    with pytest.raises(SourceConflictError) as exc_info:
        repo.save(rec2)
    assert "Divergent metadata" in str(exc_info.value)


def test_source_repository_rejects_divergent_source_entity(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "test.db")
    engine.initialize_schema()
    repo = SQLiteSourceRepository(engine)

    rec1 = create_record("src-1", "a" * 64, title="Original Title")
    repo.save(rec1)

    rec2 = create_record("src-1", "a" * 64, title="Modified Title")
    with pytest.raises(SourceConflictError) as exc_info:
        repo.save(rec2)
    assert "Divergent conceptual source attributes" in str(exc_info.value)


def test_document_repository_not_found(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "test.db")
    engine.initialize_schema()
    doc_repo = SQLiteDocumentRepository(engine)

    with pytest.raises(DocumentNotFoundError):
        doc_repo.get("non-existent")


def test_document_repository_rejects_missing_source(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "test.db")
    engine.initialize_schema()
    doc_repo = SQLiteDocumentRepository(engine)

    doc = Document(id="doc-1", source_id="missing-source", title="Title", content="Text")
    with pytest.raises(SourceNotFoundError) as exc_info:
        doc_repo.save(doc)
    assert "missing-source" in str(exc_info.value)


def test_document_repository_rejects_conflicting_content(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "test.db")
    engine.initialize_schema()
    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)

    src_repo.save(create_record("src-1", "a" * 64))

    doc1 = Document(id="doc-1", source_id="src-1", title="Title", content="Version 1")
    doc_repo.save(doc1)

    doc2 = Document(id="doc-1", source_id="src-1", title="Title", content="Version 2 Divergent")
    with pytest.raises(DocumentConflictError):
        doc_repo.save(doc2)


def test_repositories_invalid_argument_types(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "test.db")
    engine.initialize_schema()
    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)

    with pytest.raises(TypeError):
        src_repo.save("not-a-source-record")

    with pytest.raises(TypeError):
        doc_repo.save("not-a-document")
