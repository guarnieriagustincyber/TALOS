"""Dedicated Security & Integrity Audit Suite: Adversarial Boundary Penetration."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest

from study_engine.contracts.catalog import ChunkConflictError, SourceRecord
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


def test_adversarial_chunk_parent_source_mismatch_rejection(tmp_path: Path):
    """Ensure a chunk can NEVER be associated with a document belonging to a different source."""
    engine = SQLiteStorageEngine(tmp_path / "cross_source.db")
    engine.initialize_schema()

    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)
    chunk_repo = SQLiteChunkRepository(engine)

    # 2 independent sources
    src_repo.save(SourceRecord(
        source_id="src-alpha",
        manifest=SourceManifest(source_id="src-alpha", filename="a.pdf", byte_size=10, sha256="a"*64)
    ))
    src_repo.save(SourceRecord(
        source_id="src-beta",
        manifest=SourceManifest(source_id="src-beta", filename="b.pdf", byte_size=10, sha256="b"*64)
    ))

    # doc-alpha belongs to src-alpha
    doc_repo.save(Document(id="doc-alpha", source_id="src-alpha", title="Alpha Doc", content="Text Alpha"))

    # Attempt to inject chunk with document_id='doc-alpha' but source_id='src-beta'
    illegal_chunk = Chunk(
        id="doc-alpha:chunk_00",
        document_id="doc-alpha",
        source_id="src-beta",  # Contradicts parent document's source_id!
        content="Cross-source attack content",
        index=0,
    )

    with pytest.raises(ChunkConflictError) as exc_info:
        chunk_repo.save_chunks([illegal_chunk])

    assert "does not match parent document" in str(exc_info.value)
    assert chunk_repo.count() == 0


def test_adversarial_massive_dos_query_fuzzing(tmp_path: Path):
    """Stress test query sanitization against 100,000 character DoS payloads and exotic Unicode."""
    engine = SQLiteStorageEngine(tmp_path / "dos_fuzz.db")
    engine.initialize_schema()
    index = SQLiteLexicalIndex(engine)

    # 1. 100,000 character buffer overflow attempt
    huge_payload = "palabra " * 15_000
    res_huge = index.search(huge_payload)
    assert isinstance(res_huge, list)

    # 2. Exotic Unicode: zero-width spaces, RTL overrides, directional marks
    exotic_unicode = "\u200b\u200c\u200d \u202e RLO_text \u202d LRO_text \ufeff BOM"
    res_exotic = index.search(exotic_unicode)
    assert isinstance(res_exotic, list)

    # 3. Only punctuation and special syntax characters
    punctuation_only = "!!! ??? ;;; ::: <<< >>> === +++ --- *** /// \\\\\\ ~~~ ```"
    res_punct = index.search(punctuation_only)
    assert res_punct == []


def test_adversarial_concurrent_write_pressure_under_wal(tmp_path: Path):
    """Verify WAL lock resilience under 30 concurrent threads performing interleaved transactions."""
    engine = SQLiteStorageEngine(tmp_path / "wal_stress.db")
    engine.initialize_schema()

    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)
    chunk_repo = SQLiteChunkRepository(engine)
    index = SQLiteLexicalIndex(engine)

    # Seed 3 sources
    for i in range(3):
        src_repo.save(SourceRecord(
            source_id=f"src-{i}",
            manifest=SourceManifest(source_id=f"src-{i}", filename=f"{i}.pdf", byte_size=10, sha256=f"{i:02x}"*32)
        ))

    errors = []

    def task(task_id: int):
        try:
            s_id = f"src-{task_id % 3}"
            d_id = f"{s_id}:doc_{task_id:04d}"
            doc_repo.save(Document(id=d_id, source_id=s_id, title=f"Title {task_id}", content=f"Body {task_id}"))

            chunks = [
                Chunk(id=f"{d_id}:c_{c}", document_id=d_id, source_id=s_id, content=f"Keyword_{c} text for {task_id}", index=c)
                for c in range(4)
            ]
            chunk_repo.save_chunks(chunks)

            hits = index.search("Keyword_0", limit=5)
            assert len(hits) >= 1
        except Exception as e:
            errors.append(f"Task {task_id} failed: {type(e).__name__} {e}")

    with ThreadPoolExecutor(max_workers=15) as pool:
        futures = [pool.submit(task, i) for i in range(30)]
        for f in futures:
            f.result()

    assert not errors, f"Concurrent WAL write errors: {errors}"
    assert doc_repo.count() == 30
    assert chunk_repo.count() == 120
    assert index.count() == 120
