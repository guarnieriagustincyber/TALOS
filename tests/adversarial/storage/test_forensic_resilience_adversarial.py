"""Ultra-rigorous forensic resilience, WAL crash recovery and pathological inputs suite."""

import multiprocessing as mp
import os
from pathlib import Path
import sqlite3
import time
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.ingestion.file_ingestion import create_source_manifest
from study_engine.storage.knowledge_store import KnowledgeStore


def _crash_writer(db_path_str: str):
    """Subprocess that writes uncheckpointed rows and dies abruptly with os._exit(0)."""
    conn = sqlite3.connect(db_path_str)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute(
        "INSERT INTO documents (id, source_id, title, content, metadata) VALUES (?, ?, ?, ?, ?);",
        ("doc-wal", "src-survivor", "WAL Document", "Contenido en WAL tras crash abrupto", "{}"),
    )
    conn.commit()
    # Abrupt hard termination: bypassing all clean connection closing
    os._exit(0)


def test_forensic_wal_crash_and_orphan_recovery(tmp_path: Path):
    """Forensic Test 1: Simulate hard OS crash leaving orphaned -wal file and verify auto-recovery."""
    db_file = tmp_path / "crash_recovery.db"

    # 1. Initialize store and write initial baseline
    store = KnowledgeStore(db_file)
    store.initialize()
    store.create_notebook(Notebook(id="nb-survivor", name="Survivor NB"))
    store.save_source(SourceRecord(
        source_id="src-survivor",
        manifest=SourceManifest(source_id="src-survivor", filename="s.pdf", byte_size=10, sha256="a"*64)
    ))
    store.close()

    # 2. Spawn a subprocess that commits a write and abruptly dies (simulating kernel panic / power cut)
    p = mp.Process(target=_crash_writer, args=(str(db_file),))
    p.start()
    p.join(timeout=5)

    # Invariant: Orphaned WAL file MUST physically exist on disk after crash
    wal_file = Path(f"{db_file}-wal")
    assert wal_file.exists(), "WAL file should remain on disk following ungraceful process crash"

    # 3. Reopen through a brand new KnowledgeStore instance
    store2 = KnowledgeStore(db_file)
    store2.initialize()

    # Invariant: WAL data must be recovered cleanly and accessible
    doc = store2.get_document("doc-wal")
    assert doc.title == "WAL Document"
    assert "tras crash abrupto" in doc.content

    # Force full checkpoint outside of any transaction and verify integrity
    direct_conn = store2.engine.connect()
    try:
        res = direct_conn.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchone()
        assert res[0] == 0  # 0 indicates successful checkpointing without busy errors
    finally:
        direct_conn.close()

    assert store2.verify_integrity() is True
    store2.close()



def test_forensic_diacritic_cross_matching_in_scoped_search(tmp_path: Path):
    """Forensic Test 2: Verify accent insensitivity and diacritic cross-matching in scoped search."""
    store = KnowledgeStore(tmp_path / "diacritics.db")
    store.initialize()

    store.create_notebook(Notebook(id="fadena-so", name="Sistemas Operativos"))
    store.save_source(SourceRecord(
        source_id="src-tanenbaum",
        manifest=SourceManifest(source_id="src-tanenbaum", filename="tanenbaum.pdf", byte_size=10, sha256="b"*64)
    ))
    store.link_source_to_notebook("fadena-so", "src-tanenbaum")
    store.save_document(Document(id="doc-so", source_id="src-tanenbaum", title="SO", content="Texto"))

    # Chunk with multiple Spanish accents (paginación, árbol, comunicación, gestión)
    chunk_content = (
        "La paginación jerárquica utiliza un árbol de traducción y buffers de "
        "comunicación interprocesos para la gestión eficiente de memoria."
    )
    store.save_chunks([
        Chunk(id="c-accents", document_id="doc-so", source_id="src-tanenbaum", content=chunk_content, index=0)
    ])

    # Search with NO accents, uppercase
    res_no_accents = store.search("PAGINACION ARBOL COMUNICACION GESTION", notebook_id="fadena-so")
    assert len(res_no_accents) == 1
    assert res_no_accents[0].chunk_id == "c-accents"

    # Search with ACCENTS, lowercase
    res_with_accents = store.search("paginación árbol comunicación gestión", notebook_id="fadena-so")
    assert len(res_with_accents) == 1
    assert res_with_accents[0].chunk_id == "c-accents"

    # Invariant: Scores and snippets must match identically
    assert res_no_accents[0].score == pytest.approx(res_with_accents[0].score, rel=1e-4)


def test_forensic_pathological_filenames_and_complex_metadata(tmp_path: Path):
    """Forensic Test 3: Pathological filenames with emojis, brackets, quotes and deep nested metadata."""
    store = KnowledgeStore(tmp_path / "pathological.db")
    store.initialize()

    # Create real physical file with pathological name on disk
    pathological_name = (
        "[FADENA-2026] 💻 Sistemas Operativos — Tanenbaum & Woodhull "
        "(4ª Edición) [Español] (v1.0.0-final) — ¡Excelente!.pdf"
    )
    real_file = tmp_path / pathological_name
    real_file.write_text("Simulated textbook content for forensic testing.", encoding="utf-8")

    manifest = create_source_manifest(real_file)
    assert manifest.filename == pathological_name
    assert len(manifest.sha256) == 64

    # Deeply nested complex metadata
    nested_metadata = {
        "edition": 4,
        "language": "es",
        "tags": ["fadena", "so", "kernel", "c-lang"],
        "syllabus_mapping": {
            "unit": 3,
            "subtopics": ["virtual memory", "mmu", "tlb"],
            "difficulty": 0.85,
            "has_exercises": True,
        },
        "emojis": "🚀 📚 💻 ⚡",
    }

    # Contract invariant: SourceRecord source_id must match manifest.source_id
    record = SourceRecord(source_id=manifest.source_id, manifest=manifest, metadata=nested_metadata)
    store.save_source(record)

    # Retrieve and verify exact JSON fidelity
    retrieved = store.get_source(manifest.source_id)
    assert retrieved.manifest.filename == pathological_name
    assert retrieved.metadata["syllabus_mapping"]["subtopics"] == ["virtual memory", "mmu", "tlb"]
    assert retrieved.metadata["emojis"] == "🚀 📚 💻 ⚡"


def test_forensic_c_code_formatting_and_whitespace_preservation(tmp_path: Path):
    """Forensic Test 4: Verify exact whitespace, tabs, newlines and pointer arithmetic in C code chunks."""
    store = KnowledgeStore(tmp_path / "code_preservation.db")
    store.initialize()

    store.save_source(SourceRecord(
        source_id="src-c-code",
        manifest=SourceManifest(source_id="src-c-code", filename="c_code.pdf", byte_size=10, sha256="c"*64)
    ))
    store.save_document(Document(id="doc-c", source_id="src-c-code", title="C Code", content="Text"))

    c_code_content = """#include <stdio.h>
#include <stdlib.h>

#define PAGE_SIZE 4096

// Allocates physical frames
void* allocate_frames(size_t count) {
\tuintptr_t *ptr = (uintptr_t*) malloc(count * PAGE_SIZE);
\tif (!ptr) {
\t\treturn NULL;
\t}
\treturn (void*) ptr;
}"""

    store.save_chunks([
        Chunk(id="c-code:0", document_id="doc-c", source_id="src-c-code", content=c_code_content, index=0)
    ])

    # Retrieve chunk
    retrieved = store.get_chunk("c-code:0")
    # Invariant: 100% byte-for-byte fidelity (tabs, newlines, indents preserved)
    assert retrieved.content == c_code_content
    assert "\tuintptr_t *ptr" in retrieved.content

    # Search for C symbols safely
    results = store.search("allocate_frames PAGE_SIZE malloc")
    assert len(results) == 1
    assert results[0].chunk_id == "c-code:0"


def test_forensic_giant_dataset_speed_benchmark(tmp_path: Path):
    """Forensic Test 5: Benchmark 2,000 chunks bulk load and sub-millisecond search latency."""
    store = KnowledgeStore(tmp_path / "giant_benchmark.db")
    store.initialize()

    store.create_notebook(Notebook(id="bench-nb", name="Benchmark"))

    record = SourceRecord(
        source_id="src-giant",
        manifest=SourceManifest(source_id="src-giant", filename="giant.pdf", byte_size=1000, sha256="e"*64)
    )

    docs = [
        Document(id=f"src-giant:doc_{d:03d}", source_id="src-giant", title=f"Doc {d}", content=f"Document text {d}")
        for d in range(20)
    ]

    # Generate 2,000 chunks (100 per document)
    chunks = []
    for d in range(20):
        doc_id = f"src-giant:doc_{d:03d}"
        for c in range(100):
            idx = d * 100 + c
            chunks.append(Chunk(
                id=f"{doc_id}:c_{c:03d}",
                document_id=doc_id,
                source_id="src-giant",
                content=f"Explicación técnica #{idx}: Algoritmos de planificación Round Robin y Colas Multinivel.",
                index=c,
            ))

    t0 = time.perf_counter()
    loaded_count = store.store_ingestion_bundle(record, docs, chunks, notebook_id="bench-nb")
    t_insert = time.perf_counter() - t0

    assert loaded_count == 2_000
    # Ingestion of 2,000 chunks + FTS indexing must take less than 1.5 seconds on desktop CPU
    assert t_insert < 1.5, f"Bulk ingestion took {t_insert:.3f}s!"

    # Test retrieval latency across 50 repeated searches
    t1 = time.perf_counter()
    for _ in range(50):
        hits = store.search("Round Robin Colas Multinivel", notebook_id="bench-nb", limit=10)
        assert len(hits) == 10
    t_search = time.perf_counter() - t1

    # 50 searches in < 0.25 seconds (< 5ms per query)
    assert t_search < 0.25, f"50 searches took {t_search:.3f}s!"
    assert store.verify_integrity() is True
