"""Adversarial and high-volume stress tests for SQLiteChunkRepository."""

from pathlib import Path
import time
import pytest

from study_engine.contracts.catalog import DocumentNotFoundError, SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.storage.repositories import (
    SQLiteChunkRepository,
    SQLiteDocumentRepository,
    SQLiteSourceRepository,
)
from study_engine.storage.sqlite_engine import SQLiteStorageEngine


def test_adversarial_10000_chunks_bulk_loading_benchmark(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "scale_chunks.db")
    engine.initialize_schema()

    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)
    chunk_repo = SQLiteChunkRepository(engine)

    manifest = SourceManifest(
        source_id="src-scale",
        filename="encyclopedia.pdf",
        byte_size=10_000_000,
        sha256="a" * 64,
    )
    src_repo.save(SourceRecord(source_id="src-scale", manifest=manifest))
    doc_repo.save(Document(id="doc-scale", source_id="src-scale", title="Scale Doc", content="Big Text"))

    # Generate 10,000 chunks
    t_gen_start = time.perf_counter()
    chunks = [
        Chunk(
            id=f"doc-scale:chunk_{i:05d}",
            document_id="doc-scale",
            source_id="src-scale",
            content=f"Parágrafo técnico {i} explicando memoria virtual y algoritmos.",
            index=i,
            metadata={"char_start": i * 50, "char_end": (i + 1) * 50},
        )
        for i in range(10_000)
    ]

    # Benchmark bulk insertion
    t_insert_start = time.perf_counter()
    inserted = chunk_repo.save_chunks(chunks)
    t_insert_end = time.perf_counter()

    insert_duration = t_insert_end - t_insert_start
    assert inserted == 10_000
    assert chunk_repo.count(document_id="doc-scale") == 10_000
    # Must insert 10,000 chunks in less than 1.0 second (typically < 0.2s on desktop)
    assert insert_duration < 1.0, f"Bulk insert took {insert_duration:.3f}s, expected < 1.0s!"

    # Benchmark retrieval
    t_query_start = time.perf_counter()
    retrieved = chunk_repo.list_by_document("doc-scale")
    t_query_end = time.perf_counter()

    query_duration = t_query_end - t_query_start
    assert len(retrieved) == 10_000
    assert retrieved[0].index == 0
    assert retrieved[-1].index == 9_999
    assert query_duration < 0.5, f"Query 10k chunks took {query_duration:.3f}s!"


def test_adversarial_mixed_documents_batch_and_atomic_rollback(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "mixed_chunks.db")
    engine.initialize_schema()

    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)
    chunk_repo = SQLiteChunkRepository(engine)

    src_repo.save(SourceRecord(
        source_id="src-m",
        manifest=SourceManifest(source_id="src-m", filename="m.pdf", byte_size=10, sha256="b"*64)
    ))
    doc_repo.save(Document(id="doc-valid-1", source_id="src-m", title="Doc 1", content="T1"))
    doc_repo.save(Document(id="doc-valid-2", source_id="src-m", title="Doc 2", content="T2"))

    # Batch with 2 valid documents and 1 invalid missing document at the end
    batch = [
        Chunk(id="doc-valid-1:chunk_0000", document_id="doc-valid-1", source_id="src-m", content="C1", index=0),
        Chunk(id="doc-valid-2:chunk_0000", document_id="doc-valid-2", source_id="src-m", content="C2", index=0),
        Chunk(id="doc-missing:chunk_0000", document_id="doc-missing", source_id="src-m", content="C3", index=0),
    ]

    with pytest.raises(DocumentNotFoundError):
        chunk_repo.save_chunks(batch)

    # Verify atomic rollback: neither doc-valid-1 nor doc-valid-2 chunks were committed
    assert chunk_repo.count() == 0


def test_adversarial_complex_code_symbols_and_null_bytes(tmp_path: Path):
    engine = SQLiteStorageEngine(tmp_path / "symbols_chunks.db")
    engine.initialize_schema()

    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)
    chunk_repo = SQLiteChunkRepository(engine)

    src_repo.save(SourceRecord(
        source_id="src-c",
        manifest=SourceManifest(source_id="src-c", filename="c.pdf", byte_size=10, sha256="c"*64)
    ))

    doc_repo.save(Document(id="doc-c", source_id="src-c", title="C Code", content="Text"))

    code_content = """
    #include <stdio.h>
    int main(int argc, char **argv) {
        char *ptr = "quotes 'single' \"double\" & \x00 null";
        printf("Output: %s\\n", ptr);
        return 0;
    }
    """
    chunk = Chunk(
        id="doc-c:chunk_0000",
        document_id="doc-c",
        source_id="src-c",
        content=code_content,
        index=0,
        metadata={"compiler": "gcc -O3", "symbols": ["*", "&", "\"", "'"]},
    )
    chunk_repo.save_chunks([chunk])

    retrieved = chunk_repo.get("doc-c:chunk_0000")
    assert retrieved.content == code_content
    assert retrieved.metadata["symbols"] == ["*", "&", "\"", "'"]
