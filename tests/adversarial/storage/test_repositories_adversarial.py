"""Adversarial and stress tests for persistent repositories."""

from concurrent.futures import ThreadPoolExecutor
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


def test_adversarial_large_volume_sources_and_documents(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "scale.db")
    engine.initialize_schema()
    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)

    # Insert 50 sources
    for i in range(50):
        src_id = f"src-{i:03d}"
        manifest = SourceManifest(
            source_id=src_id,
            filename=f"book_{i}.pdf",
            byte_size=1000 + i,
            sha256=f"{i:02x}" * 32,
        )
        source = Source(source_id=src_id, title=f"Book {i}")
        src_repo.save(SourceRecord(source_id=src_id, manifest=manifest, source=source))

    assert src_repo.count() == 50

    # Insert 200 documents (4 per source)
    for i in range(50):
        src_id = f"src-{i:03d}"
        for d in range(4):
            doc_id = f"{src_id}:doc_{d:02d}"
            doc = Document(
                id=doc_id,
                source_id=src_id,
                title=f"Doc {d} of {src_id}",
                content=f"Content for doc {d}",
                metadata={"index": d},
            )
            doc_repo.save(doc)

    assert doc_repo.count() == 200

    # Query by source
    docs_for_10 = doc_repo.list_by_source("src-010")
    assert len(docs_for_10) == 4
    assert [d.id for d in docs_for_10] == [
        "src-010:doc_00",
        "src-010:doc_01",
        "src-010:doc_02",
        "src-010:doc_03",
    ]


def test_adversarial_large_content_and_unicode_emojis(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "large.db")
    engine.initialize_schema()
    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)

    manifest = SourceManifest(
        source_id="src-large",
        filename="large.pdf",
        byte_size=2_000_000,
        sha256="e" * 64,
    )
    src_repo.save(SourceRecord(source_id="src-large", manifest=manifest))

    # 2 MB content with complex UTF-8 symbols and quotes
    paragraph = "Texto técnico sobre estructuras de datos, grafos y árboles AVL 🚀 \n\n"
    huge_content = (paragraph * 30_000) + "Final con caracteres 'comillas' \"dobles\" y \x00 null bytes."
    doc = Document(
        id="src-large:doc-huge",
        source_id="src-large",
        title="Documento Gigante",
        content=huge_content,
        metadata={"nested": {"deep": [1, 2, {"key": "val"}]}},
    )
    doc_repo.save(doc)

    retrieved = doc_repo.get("src-large:doc-huge")
    assert retrieved.content == huge_content
    assert retrieved.metadata["nested"]["deep"][2]["key"] == "val"


def test_adversarial_concurrent_repository_access(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "concurrent_repo.db")
    engine.initialize_schema()
    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)

    # Seed base source
    manifest = SourceManifest(
        source_id="src-concurrent",
        filename="concurrent.pdf",
        byte_size=5000,
        sha256="c" * 64,
    )
    src_repo.save(SourceRecord(source_id="src-concurrent", manifest=manifest))

    errors = []

    def writer_worker(idx: int):
        try:
            doc = Document(
                id=f"src-concurrent:doc_{idx:03d}",
                source_id="src-concurrent",
                title=f"Doc {idx}",
                content=f"Worker {idx} content",
            )
            doc_repo.save(doc)
        except Exception as e:
            errors.append(f"Writer {idx} failed: {e}")

    def reader_worker(idx: int):
        try:
            _ = doc_repo.list_by_source("src-concurrent")
        except Exception as e:
            errors.append(f"Reader {idx} failed: {e}")

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = []
        for i in range(20):
            futures.append(pool.submit(writer_worker, i))
            futures.append(pool.submit(reader_worker, i))
        for f in futures:
            f.result()

    assert not errors, f"Errors in concurrent repo operations: {errors}"
    assert doc_repo.count() == 20
