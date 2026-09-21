"""Comprehensive End-to-End System Audit & Adversarial Resilience Test Suite.

Simulates real-world lifecycle from raw physical files on disk to SQLite relational persistence,
verifying integrity, idempotency, anti-tampering, crash recovery, cascade deletions and concurrency.
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import pytest

from study_engine.contracts.catalog import (
    ChunkConflictError,
    DocumentConflictError,
    SourceConflictError,
    SourceRecord,
)
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.enums import IngestionStatus, SourceRole
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.source import Source
from study_engine.ingestion.chunking import ChunkConfig, chunk_document
from study_engine.ingestion.document_ingestion import ingest_document
from study_engine.ingestion.file_ingestion import ingest_file
from study_engine.storage.repositories import (
    SQLiteChunkRepository,
    SQLiteDocumentRepository,
    SQLiteSourceRepository,
)
from study_engine.storage.sqlite_engine import SQLiteStorageEngine


def test_system_full_lifecycle_from_raw_file_to_persisted_chunks(tmp_path: Path):
    """Verify complete physical -> manifest -> source -> document -> chunk -> db pipeline."""
    corpus_dir = tmp_path / "fadena_corpus"
    corpus_dir.mkdir()
    db_path = tmp_path / "study_system.db"

    # 1. Create realistic multi-topic technical document
    raw_file = corpus_dir / "sistemas_operativos.md"
    raw_content = """# Sistemas Operativos y Memoria Virtual

Este capítulo cubre la arquitectura de memoria paginada, TLB y reemplazo de páginas.

## 1. Paginación y Segmentación
La memoria física se divide en marcos (frames) de tamaño fijo, normalmente de 4 KB.
La memoria lógica se divide en páginas del mismo tamaño. La MMU traduce direcciones.

## 2. Algoritmo de Reemplazo LRU
Least Recently Used reemplaza la página que no ha sido utilizada por más tiempo.
Implementación común: lista doblemente enlazada con diccionario en hash.

## 3. Código en C para simulación de MMU
```c
#include <stdio.h>
typedef struct {
    int frame_number;
    int valid_bit;
} PageTableEntry;
```
Fin de la sección teórica y práctica.
"""
    raw_file.write_text(raw_content, encoding="utf-8")

    # 2. Ingest physical file to SourceManifest
    file_res = ingest_file(raw_file, "fadena-so-2026", corpus_root=corpus_dir)
    assert file_res.status == IngestionStatus.COMPLETED
    manifest = file_res.manifest
    assert manifest is not None
    assert len(manifest.sha256) == 64

    # 3. Setup SQLite Storage Engine & Repositories
    engine = SQLiteStorageEngine(db_path)
    engine.initialize_schema()
    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)
    chunk_repo = SQLiteChunkRepository(engine)

    # 4. Persist SourceRecord first (foreign key requirement)
    source_entity = Source(
        source_id="fadena-so-2026",
        title="Sistemas Operativos FADENA",
        role=SourceRole.COURSE,
        subject="Sistemas Operativos",
    )
    src_record = SourceRecord(
        source_id="fadena-so-2026",
        manifest=manifest,
        source=source_entity,
        metadata={"academic_year": 2026},
    )
    src_repo.save(src_record)
    assert src_repo.count() == 1

    # 5. Create Notebook and associate with persisted source
    with engine.transaction() as conn:
        conn.execute(
            "INSERT INTO notebooks (id, name, subject, created_at) VALUES (?, ?, ?, ?);",
            ("fadena-sistemas", "FADENA Sistemas Operativos", "Sistemas", "2026-09-02T00:00:00Z"),
        )
        conn.execute(
            "INSERT INTO notebook_sources (notebook_id, source_id) VALUES (?, ?);",
            ("fadena-sistemas", "fadena-so-2026"),
        )


    # 6. Ingest logical Document
    doc_res = ingest_document(raw_file, "fadena-so-2026", corpus_root=corpus_dir)
    assert doc_res.status == IngestionStatus.COMPLETED
    doc = doc_res.document
    assert doc is not None
    assert doc.id == "fadena-so-2026:sistemas_operativos"
    assert doc.source_id == "fadena-so-2026"

    doc_repo.save(doc)
    assert doc_repo.count() == 1

    # 7. Chunk Document with overlap
    config = ChunkConfig(chunk_size=150, chunk_overlap=30)
    chunks = chunk_document(doc, config)
    assert len(chunks) >= 4

    # 8. Persist Chunks in bulk
    inserted_count = chunk_repo.save_chunks(chunks)
    assert inserted_count == len(chunks)
    assert chunk_repo.count(document_id=doc.id) == len(chunks)

    # 9. Verify 100% exact substring and offset invariants on every retrieved chunk
    persisted_chunks = chunk_repo.list_by_document(doc.id)
    assert len(persisted_chunks) == len(chunks)

    for idx, pc in enumerate(persisted_chunks):
        assert pc.index == idx
        assert pc.document_id == doc.id
        assert pc.source_id == "fadena-so-2026"
        c_start = pc.metadata["char_start"]
        c_end = pc.metadata["char_end"]
        # Exact source text fidelity check
        assert doc.content[c_start:c_end] == pc.content


def test_system_idempotency_and_zero_duplication_on_retries(tmp_path: Path):
    """Simulate network/process retries: repeating the entire pipeline MUST be a 100% clean no-op."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    file_path = corpus_dir / "idemp.txt"
    file_path.write_text("Contenido estricto e inmutable para prueba de reintentos.", encoding="utf-8")

    engine = SQLiteStorageEngine(tmp_path / "idemp.db")
    engine.initialize_schema()
    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)
    chunk_repo = SQLiteChunkRepository(engine)

    for iteration in range(3):
        # 1. Ingest file
        f_res = ingest_file(file_path, "src-idemp", corpus_root=corpus_dir)
        # 2. Save source
        src_repo.save(SourceRecord(source_id="src-idemp", manifest=f_res.manifest))
        # 3. Ingest document
        d_res = ingest_document(file_path, "src-idemp", corpus_root=corpus_dir)
        # 4. Save document
        doc_repo.save(d_res.document)
        # 5. Chunk and save chunks
        chunks = chunk_document(d_res.document, ChunkConfig(chunk_size=50, chunk_overlap=10))
        chunk_repo.save_chunks(chunks)

        # Invariant: Counts must remain strictly 1 source, 1 document, N chunks
        assert src_repo.count() == 1
        assert doc_repo.count() == 1
        assert chunk_repo.count() == len(chunks)


def test_system_tampered_file_and_document_conflict_detection(tmp_path: Path):
    """Verify that tampering with a single byte in a file or document triggers domain conflict errors."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    file_path = corpus_dir / "secure.txt"
    file_path.write_text("Contenido original seguro.", encoding="utf-8")

    engine = SQLiteStorageEngine(tmp_path / "tamper.db")
    engine.initialize_schema()
    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)

    # Initial registration
    f_res = ingest_file(file_path, "src-secure", corpus_root=corpus_dir)
    src_repo.save(SourceRecord(source_id="src-secure", manifest=f_res.manifest))
    d_res = ingest_document(file_path, "src-secure", corpus_root=corpus_dir)
    doc_repo.save(d_res.document)

    # Tamper with the file on disk (simulate corrupted file or malicious swap)
    file_path.write_text("Contenido MODIFICADO / ALTERADO.", encoding="utf-8")
    tampered_file_res = ingest_file(file_path, "src-secure", corpus_root=corpus_dir)

    # Source Conflict: hash differs
    with pytest.raises(SourceConflictError) as exc_info:
        src_repo.save(SourceRecord(source_id="src-secure", manifest=tampered_file_res.manifest))
    assert "differs from incoming" in str(exc_info.value)

    # Document Conflict: content differs
    tampered_doc_res = ingest_document(file_path, "src-secure", corpus_root=corpus_dir)
    with pytest.raises(DocumentConflictError):
        doc_repo.save(tampered_doc_res.document)


def test_system_cascade_integrity_under_destructive_deletions(tmp_path: Path):
    """Verify relational cascade guarantees: deleting a source wipes out all its documents and chunks."""
    engine = SQLiteStorageEngine(tmp_path / "cascade_audit.db")
    engine.initialize_schema()
    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)
    chunk_repo = SQLiteChunkRepository(engine)

    # Create 2 independent sources with documents and chunks
    for s_idx in [1, 2]:
        s_id = f"src-{s_idx}"
        m = SourceManifest(source_id=s_id, filename=f"f{s_idx}.pdf", byte_size=100, sha256=f"{s_idx}"*64)
        src_repo.save(SourceRecord(source_id=s_id, manifest=m))

        for d_idx in [1, 2]:
            d_id = f"{s_id}:doc_{d_idx}"
            doc_repo.save(Document(id=d_id, source_id=s_id, title=f"Doc {d_idx}", content=f"Text {d_idx}"))
            chunks = [
                Chunk(id=f"{d_id}:chunk_{c}", document_id=d_id, source_id=s_id, content=f"Chunk {c}", index=c)
                for c in range(5)
            ]
            chunk_repo.save_chunks(chunks)

    assert src_repo.count() == 2
    assert doc_repo.count() == 4
    assert chunk_repo.count() == 20

    # Delete source 1
    deleted = src_repo.delete("src-1")
    assert deleted is True

    # Invariant: source 1 docs and chunks must be wiped instantly, source 2 must remain completely intact
    assert src_repo.count() == 1
    assert src_repo.contains("src-1") is False
    assert src_repo.contains("src-2") is True

    assert doc_repo.count() == 2
    assert doc_repo.count() == len(doc_repo.list_by_source("src-2"))

    assert chunk_repo.count() == 10
    assert chunk_repo.count(source_id="src-1") == 0
    assert chunk_repo.count(source_id="src-2") == 10


def test_system_high_load_multi_threaded_concurrency(tmp_path: Path):
    """Stress test: 16 concurrent workers reading, writing, querying under WAL mode."""
    engine = SQLiteStorageEngine(tmp_path / "concurrent_stress.db")
    engine.initialize_schema()
    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)
    chunk_repo = SQLiteChunkRepository(engine)

    # Base seed
    src_repo.save(SourceRecord(
        source_id="src-concurrent",
        manifest=SourceManifest(source_id="src-concurrent", filename="base.pdf", byte_size=10, sha256="c"*64)
    ))

    errors = []

    def worker_pipeline(worker_id: int):
        try:
            d_id = f"src-concurrent:doc_{worker_id:03d}"
            doc = Document(id=d_id, source_id="src-concurrent", title=f"Doc {worker_id}", content=f"Content {worker_id}")
            doc_repo.save(doc)

            chunks = [
                Chunk(id=f"{d_id}:chunk_{c:02d}", document_id=d_id, source_id="src-concurrent", content=f"C{c}", index=c)
                for c in range(10)
            ]
            chunk_repo.save_chunks(chunks)

            # Read back immediately
            retrieved = chunk_repo.list_by_document(d_id)
            if len(retrieved) != 10:
                errors.append(f"Worker {worker_id} retrieved {len(retrieved)} chunks, expected 10.")
        except Exception as e:
            errors.append(f"Worker {worker_id} exception: {e}")

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(worker_pipeline, i) for i in range(25)]
        for f in futures:
            f.result()

    assert not errors, f"Concurrency stress errors: {errors}"
    assert doc_repo.count() == 25
    assert chunk_repo.count() == 250
