#!/usr/bin/env python3
"""Reproducible, retrieval-only Gate 2 baseline on temporary SQLite snapshots."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import platform
import resource
import sqlite3
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = ROOT / "data" / "web_state"
QUERIES = {
    "fadena-std": "¿Cómo se modela y transforma un conjunto de datos relacional?",
    "fase0-soc": (
        "¿Cómo se produce una condición de carrera al compartir memoria entre procesos?"
    ),
}
DEFAULT_CONCURRENCY = (1,)
DEFAULT_ITERATIONS = 12
VECTOR_DIMENSIONS = 1024


def _read_only(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)


def _snapshot(source: Path, destination: Path) -> None:
    source_conn = _read_only(source)
    destination_conn = sqlite3.connect(destination)
    try:
        source_conn.backup(destination_conn)
    finally:
        destination_conn.close()
        source_conn.close()


def _percentiles(values: List[float]) -> Dict[str, float]:
    import numpy as np

    return {
        "p50_ms": round(float(np.percentile(values, 50)), 2),
        "p95_ms": round(float(np.percentile(values, 95)), 2),
    }


def _peak_rss_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)


def _run_worker(args: List[str]) -> None:
    import numpy as np

    from study_engine.retrieval.embedding import DeterministicHashEmbedder
    from study_engine.retrieval.vector_store import SQLiteVectorStore
    from study_engine.storage.knowledge_store import KnowledgeStore

    (
        mode,
        knowledge_path,
        vector_path,
        notebook_id,
        source_json,
        query,
        vector_count,
        iterations,
        concurrency_json,
    ) = args
    source_ids = json.loads(source_json)
    concurrency = json.loads(concurrency_json)
    vector_count = int(vector_count)
    iterations = int(iterations)
    store = KnowledgeStore(knowledge_path)
    vector_store = SQLiteVectorStore(vector_path)
    embedder = DeterministicHashEmbedder(dimensions=VECTOR_DIMENSIONS)

    def operation(kind: str) -> List[Any]:
        if kind == "fts":
            return store.fts_search(
                query, notebook_id=notebook_id, limit=30, source_ids=source_ids
            )
        if kind == "dense":
            return store.vector_search(
                query,
                notebook_id=notebook_id,
                limit=30,
                vector_store=vector_store,
                embedder=embedder,
                source_ids=source_ids,
            )
        return store.search_hybrid(
            query,
            notebook_id=notebook_id,
            limit=30,
            min_sources=1,
            vector_store=vector_store,
            embedder=embedder,
            source_ids=source_ids,
        )

    started = time.perf_counter()
    first_results = operation(mode)
    first_query_ms = (time.perf_counter() - started) * 1000

    warm_latencies = []
    for _ in range(iterations):
        started = time.perf_counter()
        warm_results = operation(mode)
        warm_latencies.append((time.perf_counter() - started) * 1000)

    result: Dict[str, Any] = {
        "notebook_id": notebook_id,
        "mode": mode,
        "query": query,
        "authorized_source_count": len(source_ids),
        "matrix_vectors_scanned": int(vector_count) if mode != "fts" else 0,
        "matrix_bytes_float32_estimate": (
            int(vector_count) * VECTOR_DIMENSIONS * 4 if mode != "fts" else 0
        ),
        "first_query_matrix_cache_cold_ms": round(first_query_ms, 2),
        "warm_query": _percentiles(warm_latencies),
        "results_first": len(first_results),
        "results_warm": len(warm_results),
        "iterations": iterations,
        "process_peak_rss_mb": _peak_rss_mb(),
    }

    if mode == "hybrid":
        result["concurrency"] = {}
        for workers in concurrency:
            request_count = workers * 2

            def task(_: int) -> tuple[float, str | None]:
                started = time.perf_counter()
                try:
                    operation("hybrid")
                    return (time.perf_counter() - started) * 1000, None
                except Exception as exc:
                    return -1.0, type(exc).__name__

            latencies = []
            errors = 0
            started = time.perf_counter()
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                for elapsed, error in executor.map(task, range(request_count)):
                    if error:
                        errors += 1
                    else:
                        latencies.append(elapsed)
            duration = time.perf_counter() - started
            result["concurrency"][str(workers)] = {
                "requests": request_count,
                "errors": errors,
                "qps": round(request_count / duration, 2),
                "latency": _percentiles(latencies) if latencies else None,
                "process_peak_rss_mb": _peak_rss_mb(),
            }

    print(json.dumps(result, ensure_ascii=False))
    store.engine.close()
    vector_store.close()


def _run_benchmark(args: argparse.Namespace) -> Dict[str, Any]:
    data_dir = args.data_dir.resolve()
    knowledge_source = data_dir / "knowledge_store.db"
    vector_source = data_dir / "vector_store.db"
    for path in (knowledge_source, vector_source):
        if not path.is_file():
            raise FileNotFoundError(f"Required SQLite database is missing: {path}")

    unknown = sorted(set(args.notebooks) - QUERIES.keys())
    if unknown:
        raise ValueError(
            f"No frozen benchmark query for notebook(s): {', '.join(unknown)}"
        )
    if args.iterations < 1:
        raise ValueError("--iterations must be at least 1")
    if any(workers < 1 for workers in args.concurrency):
        raise ValueError("Concurrency levels must be positive")
    if (
        any(workers > 1 for workers in args.concurrency)
        and not args.allow_concurrent_load
    ):
        raise ValueError(
            "Concurrent retrieval can substantially increase CPU temperature and "
            "per-process RSS. Use --allow-concurrent-load only when actively "
            "monitoring the target machine."
        )

    with tempfile.TemporaryDirectory(
        prefix="talos-g2-retrieval-", dir=args.temp_dir
    ) as temp:
        temp_dir = Path(temp)
        knowledge_copy = temp_dir / "knowledge_store.db"
        vector_copy = temp_dir / "vector_store.db"
        _snapshot(knowledge_source, knowledge_copy)
        _snapshot(vector_source, vector_copy)

        knowledge_db = _read_only(knowledge_copy)
        vector_db = _read_only(vector_copy)
        notebook_data = []
        for notebook_id in args.notebooks:
            source_ids = [
                row[0]
                for row in knowledge_db.execute(
                    "SELECT source_id FROM notebook_sources "
                    "WHERE notebook_id = ? ORDER BY source_id",
                    (notebook_id,),
                )
            ]
            dimensions = vector_db.execute(
                "SELECT MIN(dimensions), MAX(dimensions), COUNT(*) "
                "FROM chunk_embeddings WHERE notebook_id = ?",
                (notebook_id,),
            ).fetchone()
            min_dim, max_dim, vector_count = dimensions
            if not vector_count:
                raise ValueError(f"No vectors found for notebook {notebook_id}")
            if min_dim != VECTOR_DIMENSIONS or max_dim != VECTOR_DIMENSIONS:
                raise ValueError(
                    f"{notebook_id} has mixed or unexpected dimensions: "
                    f"{min_dim}..{max_dim}; expected {VECTOR_DIMENSIONS}"
                )
            notebook_data.append(
                {
                    "notebook_id": notebook_id,
                    "source_ids": source_ids,
                    "vector_count": vector_count,
                }
            )
        knowledge_db.close()
        vector_db.close()

        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            [str(ROOT / "src"), env.get("PYTHONPATH", "")]
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

        measurements = []
        for item in notebook_data:
            for mode in ("fts", "dense", "hybrid"):
                command = [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--_worker",
                    mode,
                    str(knowledge_copy),
                    str(vector_copy),
                    item["notebook_id"],
                    json.dumps(item["source_ids"]),
                    QUERIES[item["notebook_id"]],
                    str(item["vector_count"]),
                    str(args.iterations),
                    json.dumps(args.concurrency),
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
                        f"Benchmark worker {item['notebook_id']}/{mode} failed "
                        f"with exit code {completed.returncode}.\n"
                        f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
                    )
                measurements.append(json.loads(completed.stdout))

        return {
            "benchmark": "Gate 2 retrieval baseline",
            "scope": (
                "Retrieval-only; deterministic hash query embeddings; excludes "
                "production embedding inference, quality evaluation, reranking "
                "beyond KnowledgeStore.search_hybrid, endpoint and LLM latency."
            ),
            "cache_definition": (
                "First query starts with an empty per-process SQLite vector-matrix "
                "cache. The OS page cache is not flushed and may be warm."
            ),
            "hardware": {
                "platform": platform.platform(),
                "processor": platform.processor() or "not reported by platform",
                "logical_cpus": os.cpu_count(),
            },
            "source_database_bytes": {
                "knowledge_store": knowledge_source.stat().st_size,
                "vector_store": vector_source.stat().st_size,
            },
            "temporary_snapshots_removed_on_exit": True,
            "measurements": measurements,
        }


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--_worker":
        _run_worker(sys.argv[2:])
        return

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument(
        "--temp-dir",
        type=Path,
        default=None,
        help="Parent for disposable snapshots (defaults to the system temp directory).",
    )
    parser.add_argument(
        "--notebooks",
        nargs="+",
        choices=sorted(QUERIES),
        default=list(QUERIES),
        help="Frozen curriculum scopes to measure.",
    )
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument(
        "--concurrency",
        nargs="+",
        type=int,
        default=list(DEFAULT_CONCURRENCY),
    )
    parser.add_argument(
        "--allow-concurrent-load",
        action="store_true",
        help=(
            "Explicitly permit concurrent retrieval load. Monitor CPU temperature "
            "and available memory; default is single-worker only."
        ),
    )
    args = parser.parse_args()
    print(json.dumps(_run_benchmark(args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
