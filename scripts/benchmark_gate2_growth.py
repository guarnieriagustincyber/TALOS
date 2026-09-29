#!/usr/bin/env python3
"""Measure 1x/2x/5x scoped retrieval growth on disposable SQLite snapshots."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Tuple

from benchmark_gate2_retrieval import DEFAULT_DATA_DIR, QUERIES, ROOT

VECTOR_DIMENSIONS = 1024
RETRIEVAL_RUNNER = ROOT / "scripts" / "benchmark_gate2_retrieval.py"


def _snapshot(source: Path, destination: Path) -> None:
    source_conn = sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True)
    destination_conn = sqlite3.connect(destination)
    try:
        source_conn.backup(destination_conn)
    finally:
        destination_conn.close()
        source_conn.close()


def _file_bytes(path: Path) -> int:
    return sum(
        candidate.stat().st_size for candidate in path.parent.glob(path.name + "*")
    )


def _expand_scope(
    knowledge_path: Path,
    vector_path: Path,
    notebook_id: str,
    factor: int,
) -> Tuple[float, int, int, int]:
    knowledge = sqlite3.connect(knowledge_path)
    vectors = sqlite3.connect(vector_path)
    try:
        knowledge.execute("PRAGMA journal_mode=DELETE")
        vectors.execute("PRAGMA journal_mode=DELETE")
        source_ids = [
            row[0]
            for row in knowledge.execute(
                "SELECT source_id FROM notebook_sources "
                "WHERE notebook_id = ? ORDER BY source_id",
                (notebook_id,),
            )
        ]
        if not source_ids:
            raise ValueError(f"No authorized sources found for {notebook_id}")
        placeholders = ",".join("?" for _ in source_ids)
        knowledge.execute(
            "CREATE TEMP TABLE g2_base_chunks AS "
            "SELECT id, document_id, source_id, content, page_start, page_end, "
            "chapter, section, token_count, pos_index, metadata, parent_chapter_id "
            f"FROM chunks WHERE source_id IN ({placeholders})",
            source_ids,
        )
        vectors.execute(
            "CREATE TEMP TABLE g2_base_vectors AS "
            "SELECT chunk_id, notebook_id, source_id, provider_id, model_id, "
            "dimensions, vector FROM chunk_embeddings WHERE notebook_id = ?",
            (notebook_id,),
        )
        base_chunks = knowledge.execute(
            "SELECT COUNT(*) FROM g2_base_chunks"
        ).fetchone()[0]
        base_vectors = vectors.execute(
            "SELECT COUNT(*) FROM g2_base_vectors"
        ).fetchone()[0]
        if not base_chunks or base_chunks != base_vectors:
            raise ValueError(
                f"{notebook_id} must have one vector per authorized chunk for "
                f"this controlled curve; chunks={base_chunks}, vectors={base_vectors}"
            )
        dimensions = vectors.execute(
            "SELECT MIN(dimensions), MAX(dimensions) FROM g2_base_vectors"
        ).fetchone()
        if dimensions != (VECTOR_DIMENSIONS, VECTOR_DIMENSIONS):
            raise ValueError(
                f"{notebook_id} has unexpected vector dimensions: {dimensions}"
            )

        started = time.perf_counter()
        for replica in range(1, factor):
            prefix = f"g2scale{replica}:"
            knowledge.execute(
                "INSERT INTO chunks (id, document_id, source_id, content, "
                "page_start, page_end, chapter, section, token_count, pos_index, "
                "metadata, parent_chapter_id) "
                "SELECT ? || id, document_id, source_id, content, page_start, "
                "page_end, chapter, section, token_count, "
                "pos_index + ? , metadata, parent_chapter_id FROM g2_base_chunks",
                (prefix, replica * 1_000_000),
            )
            vectors.execute(
                "INSERT INTO chunk_embeddings "
                "(chunk_id, notebook_id, source_id, provider_id, model_id, "
                "dimensions, vector) "
                "SELECT ? || chunk_id, notebook_id, source_id, provider_id, "
                "model_id, dimensions, vector FROM g2_base_vectors",
                (prefix,),
            )
            knowledge.commit()
            vectors.commit()
        duplication_seconds = time.perf_counter() - started

        final_chunks = knowledge.execute(
            f"SELECT COUNT(*) FROM chunks WHERE source_id IN ({placeholders})",
            source_ids,
        ).fetchone()[0]
        final_vectors = vectors.execute(
            "SELECT COUNT(*) FROM chunk_embeddings WHERE notebook_id = ?",
            (notebook_id,),
        ).fetchone()[0]
        if (
            final_chunks != base_chunks * factor
            or final_vectors != base_vectors * factor
        ):
            raise RuntimeError(
                f"Growth factor verification failed for {notebook_id}: "
                f"chunks={final_chunks}/{base_chunks * factor}, "
                f"vectors={final_vectors}/{base_vectors * factor}"
            )
        return duplication_seconds, base_chunks, final_chunks, final_vectors
    finally:
        knowledge.close()
        vectors.close()


def _run_worker(
    temp_dir: Path,
    notebook_id: str,
    source_ids: List[str],
    vector_count: int,
    mode: str,
    iterations: int,
) -> Dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "src"), str(ROOT / "scripts"), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    env.update(
        {
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
        }
    )
    command = [
        sys.executable,
        str(RETRIEVAL_RUNNER),
        "--_worker",
        mode,
        str(temp_dir / "knowledge_store.db"),
        str(temp_dir / "vector_store.db"),
        notebook_id,
        json.dumps(source_ids),
        QUERIES[notebook_id],
        str(vector_count),
        str(iterations),
        "[]",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )
    if completed.returncode:
        raise RuntimeError(
            f"Worker {notebook_id}/{mode} failed with exit code "
            f"{completed.returncode}.\nstdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    return json.loads(completed.stdout)


def _measure_factor(
    data_dir: Path,
    notebook_id: str,
    factor: int,
    iterations: int,
    temp_dir: Path | None,
) -> Dict[str, Any]:
    with tempfile.TemporaryDirectory(
        prefix=f"talos-g2-{notebook_id}-{factor}x-", dir=temp_dir
    ) as temp:
        snapshot_dir = Path(temp)
        knowledge_path = snapshot_dir / "knowledge_store.db"
        vector_path = snapshot_dir / "vector_store.db"
        _snapshot(data_dir / "knowledge_store.db", knowledge_path)
        _snapshot(data_dir / "vector_store.db", vector_path)

        source_db = sqlite3.connect(
            f"file:{knowledge_path.resolve()}?mode=ro", uri=True
        )
        source_ids = [
            row[0]
            for row in source_db.execute(
                "SELECT source_id FROM notebook_sources "
                "WHERE notebook_id = ? ORDER BY source_id",
                (notebook_id,),
            )
        ]
        source_db.close()

        duplication_seconds, base_chunks, final_chunks, final_vectors = _expand_scope(
            knowledge_path, vector_path, notebook_id, factor
        )
        measurements = [
            _run_worker(
                snapshot_dir,
                notebook_id,
                source_ids,
                final_vectors,
                mode,
                iterations,
            )
            for mode in ("fts", "dense", "hybrid")
        ]
        return {
            "notebook_id": notebook_id,
            "growth_factor": factor,
            "base_chunks_and_vectors": base_chunks,
            "final_chunks": final_chunks,
            "final_vectors": final_vectors,
            "sql_duplication_seconds": round(duplication_seconds, 3),
            "snapshot_database_bytes": {
                "knowledge_store": _file_bytes(knowledge_path),
                "vector_store": _file_bytes(vector_path),
            },
            "measurements": measurements,
            "synthetic_duplicate_content": True,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--temp-dir", type=Path, default=None)
    parser.add_argument(
        "--notebooks",
        nargs="+",
        choices=sorted(QUERIES),
        default=list(QUERIES),
    )
    parser.add_argument("--factors", nargs="+", type=int, default=[1, 2])
    parser.add_argument("--iterations", type=int, default=4)
    parser.add_argument(
        "--allow-high-load",
        action="store_true",
        help=(
            "Permit growth factors above 2x. A measured 5x run required "
            "2.6-2.9 GiB peak RSS per dense-search process and sustained CPU load."
        ),
    )
    args = parser.parse_args()

    if args.iterations < 1 or any(factor < 1 for factor in args.factors):
        raise ValueError("Iterations and growth factors must be positive")
    if any(factor > 2 for factor in args.factors) and not args.allow_high_load:
        raise ValueError(
            "Growth factors above 2x require --allow-high-load. A 5x dense "
            "search previously reached 2.6-2.9 GiB peak RSS; monitor CPU "
            "temperature and memory before opting in."
        )

    data_dir = args.data_dir.resolve()
    for filename in ("knowledge_store.db", "vector_store.db"):
        if not (data_dir / filename).is_file():
            raise FileNotFoundError(
                f"Required SQLite database is missing: {data_dir / filename}"
            )

    results = [
        _measure_factor(
            data_dir,
            notebook_id,
            factor,
            args.iterations,
            args.temp_dir,
        )
        for notebook_id in args.notebooks
        for factor in args.factors
    ]
    print(
        json.dumps(
            {
                "benchmark": "Gate 2 scoped retrieval growth curve",
                "method": (
                    "Duplicate existing authorized chunks and their 1024d vectors "
                    "inside disposable SQLite snapshots; no source database writes."
                ),
                "limits": (
                    "Synthetic duplicate content measures storage/scan scaling, "
                    "not real ingestion cost, unique-content quality, or semantic recall."
                ),
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
