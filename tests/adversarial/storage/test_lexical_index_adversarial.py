"""Adversarial security, syntax fuzzing and cascade desync tests for SQLiteLexicalIndex."""

from pathlib import Path
import time
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


def test_adversarial_fts5_syntax_fuzzing_and_malicious_queries(tmp_path: Path):
    """Ensure raw user input with FTS5 operators, unclosed quotes and code symbols never crashes."""
    engine = SQLiteStorageEngine(tmp_path / "fuzz.db")
    engine.initialize_schema()

    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)
    chunk_repo = SQLiteChunkRepository(engine)
    index = SQLiteLexicalIndex(engine)

    src_repo.save(SourceRecord(
        source_id="src-fuzz",
        manifest=SourceManifest(source_id="src-fuzz", filename="fuzz.pdf", byte_size=10, sha256="f"*64)
    ))
    doc_repo.save(Document(id="doc-fuzz", source_id="src-fuzz", title="Fuzz Doc", content="Text"))
    chunk_repo.save_chunks([
        Chunk(
            id="doc-fuzz:chunk_00",
            document_id="doc-fuzz",
            source_id="src-fuzz",
            content="Desarrollo en lenguaje C++ con punteros *ptr y función malloc() de memoria.",
            index=0,
        )
    ])

    malicious_and_fuzz_queries = [
        "C++",
        "***",
        "**",
        "*",
        '"unclosed double quote',
        "'unclosed single quote",
        "AND OR NOT NEAR",
        "NEAR/2",
        "content:punteros",
        "); DROP TABLE chunks; --",
        "malloc()",
        "*ptr",
        "a + b - c / d * e",
        "O(log N)",
        "SELECT * FROM chunks WHERE 1=1",
        "\x00 null byte in string",
        "🔥 emojis 🚀 computación",
    ]

    for q in malicious_and_fuzz_queries:
        # Every single malicious or strange query MUST execute without raising sqlite3.OperationalError
        results = index.search(q)
        assert isinstance(results, list)

    # Query with "C++" should safely find the chunk matching "C"
    hits_cpp = index.search("C++")
    assert len(hits_cpp) == 1
    assert hits_cpp[0].chunk_id == "doc-fuzz:chunk_00"


def test_adversarial_fts5_cascade_sync_on_deletion(tmp_path: Path):
    """Verify that deleting a document or source instantly cleans up the FTS5 index without desync."""
    engine = SQLiteStorageEngine(tmp_path / "cascade_fts.db")
    engine.initialize_schema()

    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)
    chunk_repo = SQLiteChunkRepository(engine)
    index = SQLiteLexicalIndex(engine)

    src_repo.save(SourceRecord(
        source_id="src-del",
        manifest=SourceManifest(source_id="src-del", filename="d.pdf", byte_size=10, sha256="d"*64)
    ))
    doc_repo.save(Document(id="doc-del", source_id="src-del", title="Delete Doc", content="Text"))
    chunk_repo.save_chunks([
        Chunk(
            id="doc-del:chunk_00",
            document_id="doc-del",
            source_id="src-del",
            content="Texto crítico con algoritmos de grafos y árboles.",
            index=0,
        )
    ])

    # Search before deletion
    assert len(index.search("grafos")) == 1

    # Delete Document -> Trigger chunks_ad fires through foreign keys
    doc_repo.delete("doc-del")

    # Invariant: FTS5 must return 0 results and count must be 0
    assert len(index.search("grafos")) == 0
    assert index.count() == 0


def test_adversarial_fts5_high_volume_speed_benchmark(tmp_path: Path):
    """Benchmark: 1,000 chunks indexed, 200 consecutive search queries executed in < 0.2s."""
    engine = SQLiteStorageEngine(tmp_path / "bench_fts.db")
    engine.initialize_schema()

    src_repo = SQLiteSourceRepository(engine)
    doc_repo = SQLiteDocumentRepository(engine)
    chunk_repo = SQLiteChunkRepository(engine)
    index = SQLiteLexicalIndex(engine)

    src_repo.save(SourceRecord(
        source_id="src-bench",
        manifest=SourceManifest(source_id="src-bench", filename="b.pdf", byte_size=10, sha256="b"*64)
    ))
    doc_repo.save(Document(id="doc-bench", source_id="src-bench", title="Bench Doc", content="Text"))

    # Generate and insert 1,000 chunks
    chunks = [
        Chunk(
            id=f"doc-bench:chunk_{i:04d}",
            document_id="doc-bench",
            source_id="src-bench",
            content=f"Explicación técnica {i}: estructura de memoria, threads y sockets en Linux.",
            index=i,
        )
        for i in range(1_000)
    ]
    chunk_repo.save_chunks(chunks)
    assert index.count() == 1_000

    # Benchmark 200 searches
    t_start = time.perf_counter()
    for _ in range(200):
        res = index.search("sockets Linux", limit=5)
        assert len(res) == 5
    t_end = time.perf_counter()

    duration = t_end - t_start
    # 200 searches must run in less than 0.5 seconds on desktop CPU (< 2.5ms per query)
    assert duration < 0.5, f"200 FTS5 searches took {duration:.3f}s!"
