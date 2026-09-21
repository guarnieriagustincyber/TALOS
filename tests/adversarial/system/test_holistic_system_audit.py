"""Holistic System-Wide Deep Audit: OS-Level Concurrency, FD Leaks, RAM Boundedness & Crash Recovery."""

import multiprocessing as mp
import os
from pathlib import Path
import tracemalloc
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.storage.knowledge_store import KnowledgeStore


def _mp_worker(db_path_str: str, worker_id: int, err_queue: mp.Queue):
    """Worker running in a completely separate OS process with its own PID and memory space."""
    try:
        store = KnowledgeStore(db_path_str)
        nb_id = f"nb-mp-{worker_id}"
        store.create_notebook(Notebook(id=nb_id, name=f"OS Process Notebook {worker_id}"))

        src_id = f"src-mp-{worker_id}"
        record = SourceRecord(
            source_id=src_id,
            manifest=SourceManifest(
                source_id=src_id,
                filename=f"proc_{worker_id}.pdf",
                byte_size=1024,
                sha256=f"{worker_id:02x}" * 32,
            ),
        )
        docs = [
            Document(id=f"{src_id}:d0", source_id=src_id, title=f"Doc {worker_id}", content=f"Process content {worker_id}")
        ]
        chunks = [
            Chunk(id=f"{src_id}:d0:c0", document_id=f"{src_id}:d0", source_id=src_id, content=f"Process keyword_{worker_id} memory", index=0)
        ]
        store.store_ingestion_bundle(record, docs, chunks, notebook_id=nb_id)

        # Query back
        res = store.search(f"keyword_{worker_id}", notebook_id=nb_id)
        assert len(res) == 1
    except Exception as e:
        err_queue.put(f"Process {worker_id} (PID {os.getpid()}) failed: {type(e).__name__} - {e}")


def test_adversarial_multiprocess_os_concurrency(tmp_path: Path):
    """Audit: Multiple distinct OS processes writing and reading simultaneously under WAL mode."""
    db_path = tmp_path / "multiprocess_audit.db"
    store = KnowledgeStore(db_path)
    store.initialize()

    err_queue = mp.Queue()
    num_processes = 4
    processes = [
        mp.Process(target=_mp_worker, args=(str(db_path), i, err_queue))
        for i in range(num_processes)
    ]

    for p in processes:
        p.start()
    for p in processes:
        p.join(timeout=10)

    errors = []
    while not err_queue.empty():
        errors.append(err_queue.get())

    assert not errors, f"Multi-process OS concurrency errors: {errors}"
    assert len(store.list_notebooks()) == num_processes
    assert store.verify_integrity() is True


def test_adversarial_file_descriptor_leak_audit(tmp_path: Path):
    """Audit: Verify that repeated transactions never leak OS file descriptors."""
    db_path = tmp_path / "fd_audit.db"
    store = KnowledgeStore(db_path)
    store.initialize()

    def get_fd_count() -> int:
        return len(os.listdir("/proc/self/fd"))

    # Warmup
    store.save_source(SourceRecord(
        source_id="src-init",
        manifest=SourceManifest(source_id="src-init", filename="init.pdf", byte_size=10, sha256="0"*64)
    ))
    baseline_fds = get_fd_count()

    # 150 consecutive operations
    for i in range(150):
        s_id = f"src-fd-{i}"
        store.save_source(SourceRecord(
            source_id=s_id,
            manifest=SourceManifest(source_id=s_id, filename=f"{i}.pdf", byte_size=10, sha256=f"{i:04x}".rjust(64, "0"))
        ))
        res = store.get_source(s_id)
        assert res.source_id == s_id

    final_fds = get_fd_count()
    delta = final_fds - baseline_fds
    assert delta <= 2, f"Leaked {delta} file descriptors during 150 transactions!"


def test_adversarial_memory_flatness_audit(tmp_path: Path):
    """Audit: Verify that continuous search queries maintain flat RAM usage without heap bloat."""
    db_path = tmp_path / "ram_audit.db"
    store = KnowledgeStore(db_path)
    store.initialize()

    store.save_source(SourceRecord(
        source_id="src-ram",
        manifest=SourceManifest(source_id="src-ram", filename="ram.pdf", byte_size=10, sha256="a"*64)
    ))
    store.save_document(Document(id="doc-ram", source_id="src-ram", title="RAM Doc", content="Text"))
    store.save_chunks([
        Chunk(id=f"doc-ram:c_{i}", document_id="doc-ram", source_id="src-ram", content=f"Virtual memory chunk {i} benchmark", index=i)
        for i in range(50)
    ])

    tracemalloc.start()
    snap_before = tracemalloc.take_snapshot()

    for _ in range(250):
        hits = store.search("Virtual memory", limit=5)
        assert len(hits) == 5

    snap_after = tracemalloc.take_snapshot()
    tracemalloc.stop()

    diff = snap_after.compare_to(snap_before, "lineno")
    total_kb = sum(stat.size_diff for stat in diff) / 1024
    # Total memory delta over 250 queries must be negligible (< 100 KB)
    assert total_kb < 100, f"Excessive heap allocation detected: {total_kb:.1f} KB"


def test_adversarial_bundle_crash_recovery_integrity(tmp_path: Path):
    """Audit: Verify atomic rollback when an unhandled failure occurs mid-bundle."""
    db_path = tmp_path / "crash_audit.db"
    store = KnowledgeStore(db_path)
    store.initialize()

    store.create_notebook(Notebook(id="nb-valid", name="Valid NB"))

    rec = SourceRecord(
        source_id="src-atomic",
        manifest=SourceManifest(source_id="src-atomic", filename="a.pdf", byte_size=10, sha256="f"*64)
    )
    docs = [Document(id="src-atomic:d0", source_id="src-atomic", title="Doc 0", content="Text")]
    # Corrupt chunk batch with duplicate ID
    chunks = [
        Chunk(id="c0", document_id="src-atomic:d0", source_id="src-atomic", content="C0", index=0),
        Chunk(id="c0", document_id="src-atomic:d0", source_id="src-atomic", content="C0 Dup", index=1),
    ]

    with pytest.raises(Exception):
        store.store_ingestion_bundle(rec, docs, chunks, notebook_id="nb-valid")

    # Invariant: Neither source, nor document, nor chunk, nor link were saved!
    assert store.sources.contains("src-atomic") is False
    assert store.documents.contains("src-atomic:d0") is False
    assert store.chunks.contains("c0") is False
    assert store.get_notebook("nb-valid").sources == []
    assert store.verify_integrity() is True
