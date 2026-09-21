"""Unit tests for SQLiteSourceRepository and SQLiteDocumentRepository."""

from pathlib import Path
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.source import Source
from study_engine.storage.repositories import (
    SQLiteDocumentRepository,
    SQLiteSourceRepository,
)
from study_engine.storage.sqlite_engine import SQLiteStorageEngine


def create_sample_source_record(
    source_id: str = "src-joyanes",
    sha256: str = "a" * 64,
    filename: str = "joyanes.pdf",
) -> SourceRecord:
    manifest = SourceManifest(
        source_id=source_id,
        filename=filename,
        byte_size=1024,
        sha256=sha256,
        file_path=f"books/{filename}",
        media_type="application/pdf",
        metadata={"extraction": "pypdf"},
    )
    source_obj = Source(
        source_id=source_id,
        title="Fundamentos de Programación",
        author="Luis Joyanes Aguilar",
        subject="Programación",
        chapter="1",
    )
    return SourceRecord(
        source_id=source_id,
        manifest=manifest,
        source=source_obj,
        metadata={"registered_by": "unit-test"},
    )


def test_source_repository_save_and_get(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "repo.db")
    engine.initialize_schema()
    repo = SQLiteSourceRepository(engine)

    record = create_sample_source_record()
    repo.save(record)

    assert repo.count() == 1
    assert repo.contains("src-joyanes") is True
    assert repo.contains("non-existent") is False

    retrieved = repo.get("src-joyanes")
    assert retrieved.source_id == record.source_id
    assert retrieved.manifest.sha256 == record.manifest.sha256
    assert retrieved.source.title == "Fundamentos de Programación"
    assert retrieved.metadata["registered_by"] == "unit-test"


def test_source_repository_idempotent_save(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "idempotent.db")
    engine.initialize_schema()
    repo = SQLiteSourceRepository(engine)

    record = create_sample_source_record()
    repo.save(record)
    # Second save with exact same data is a no-op
    repo.save(record)
    assert repo.count() == 1


def test_source_repository_find_by_sha256(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "sha.db")
    engine.initialize_schema()
    repo = SQLiteSourceRepository(engine)

    sha = "f" * 64
    record = create_sample_source_record(source_id="src-sha", sha256=sha)
    repo.save(record)

    found = repo.find_by_sha256(sha)
    assert found is not None
    assert found.source_id == "src-sha"

    # Case insensitive lookup
    found_upper = repo.find_by_sha256(sha.upper())
    assert found_upper is not None
    assert found_upper.source_id == "src-sha"

    assert repo.find_by_sha256("0" * 64) is None
    assert repo.find_by_sha256("") is None
    assert repo.find_by_sha256(None) is None


def test_source_repository_list_all_deterministic_order(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "list.db")
    engine.initialize_schema()
    repo = SQLiteSourceRepository(engine)

    repo.save(create_sample_source_record(source_id="src-b", sha256="b" * 64))
    repo.save(create_sample_source_record(source_id="src-a", sha256="a" * 64))
    repo.save(create_sample_source_record(source_id="src-c", sha256="c" * 64))

    all_sources = repo.list_all()
    assert len(all_sources) == 3
    assert [s.source_id for s in all_sources] == ["src-a", "src-b", "src-c"]


def test_source_repository_delete(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "del.db")
    engine.initialize_schema()
    repo = SQLiteSourceRepository(engine)

    record = create_sample_source_record()
    repo.save(record)
    assert repo.count() == 1

    assert repo.delete("src-joyanes") is True
    assert repo.count() == 0
    assert repo.delete("src-joyanes") is False


def test_document_repository_save_and_get(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "doc.db")
    engine.initialize_schema()
    source_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)

    source_record = create_sample_source_record()
    source_repo.save(source_record)

    doc = Document(
        id="src-joyanes:cap-01",
        source_id="src-joyanes",
        title="Capítulo 1",
        content="Contenido del capítulo uno sobre programación.",
        path="books/joyanes.pdf",
        page_count=20,
        metadata={"chapter_number": 1},
    )
    doc_repo.save(doc)

    assert doc_repo.count() == 1
    assert doc_repo.contains("src-joyanes:cap-01") is True
    assert doc_repo.contains("missing") is False

    retrieved = doc_repo.get("src-joyanes:cap-01")
    assert retrieved.id == doc.id
    assert retrieved.source_id == "src-joyanes"
    assert retrieved.content == doc.content
    assert retrieved.page_count == 20
    assert retrieved.metadata["chapter_number"] == 1


def test_document_repository_list_by_source_and_include_content(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "doc_list.db")
    engine.initialize_schema()
    source_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)

    source_repo.save(create_sample_source_record(source_id="src-1", sha256="1" * 64))
    source_repo.save(create_sample_source_record(source_id="src-2", sha256="2" * 64))

    doc_repo.save(Document(id="doc-1-b", source_id="src-1", title="B", content="Long content B"))
    doc_repo.save(Document(id="doc-1-a", source_id="src-1", title="A", content="Long content A"))
    doc_repo.save(Document(id="doc-2-x", source_id="src-2", title="X", content="Long content X"))

    # list_by_source ordered by id
    src_1_docs = doc_repo.list_by_source("src-1", include_content=True)
    assert len(src_1_docs) == 2
    assert [d.id for d in src_1_docs] == ["doc-1-a", "doc-1-b"]
    assert src_1_docs[0].content == "Long content A"

    # include_content=False (scale optimization)
    light_docs = doc_repo.list_by_source("src-1", include_content=False)
    assert light_docs[0].content is None
    assert light_docs[0].title == "A"

    all_docs = doc_repo.list_all(include_content=True)
    assert len(all_docs) == 3


def test_document_repository_delete(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "doc_del.db")
    engine.initialize_schema()
    source_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)

    source_repo.save(create_sample_source_record())
    doc = Document(id="doc-del", source_id="src-joyanes", title="Del", content="Text")
    doc_repo.save(doc)

    assert doc_repo.count() == 1
    assert doc_repo.delete("doc-del") is True
    assert doc_repo.count() == 0
    assert doc_repo.delete("doc-del") is False


def test_repositories_empty_id_and_idempotent_doc_save(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "edge.db")
    engine.initialize_schema()
    source_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)

    # Empty contains
    assert source_repo.contains("") is False
    assert doc_repo.contains("") is False

    # Get empty / invalid ID raises not found
    from study_engine.contracts.catalog import DocumentNotFoundError, SourceNotFoundError
    with pytest.raises(SourceNotFoundError):
        source_repo.get("")
    with pytest.raises(DocumentNotFoundError):
        doc_repo.get("")

    # Idempotent document save
    source_repo.save(create_sample_source_record())
    doc = Document(id="doc-idemp", source_id="src-joyanes", title="Idemp", content="Text")
    doc_repo.save(doc)
    doc_repo.save(doc)  # Idempotent no-op
    assert doc_repo.count() == 1

    # list_all without content
    light_all = doc_repo.list_all(include_content=False)
    assert len(light_all) == 1
    assert light_all[0].content is None


def test_source_repository_rejects_divergent_manifest_filename(tmp_path: Path):
    from study_engine.contracts.catalog import SourceConflictError
    engine = SQLiteStorageEngine(tmp_path / "fn_diverge.db")
    engine.initialize_schema()
    source_repo = SQLiteSourceRepository(engine)

    rec1 = create_sample_source_record(source_id="src-fn", filename="file1.pdf")
    source_repo.save(rec1)

    rec2 = create_sample_source_record(source_id="src-fn", filename="file2_divergent.pdf")
    with pytest.raises(SourceConflictError) as exc_info:
        source_repo.save(rec2)
    assert "Divergent manifest filename" in str(exc_info.value)

