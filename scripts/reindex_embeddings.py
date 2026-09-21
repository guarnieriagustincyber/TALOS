#!/usr/bin/env python3
"""Reindex de embeddings semánticos del corpus completo (Semana 1 - Chat NotebookLM).

Genera vectores reales con multilingual-e5-small (ONNX local, sin red) para todos
los chunks del knowledge store y los persiste en el vector store SQLite por par
(chunk_id, notebook_id), respetando la pertenencia multi-notebook de cada fuente.

Uso:
    python scripts/reindex_embeddings.py                    # corpus completo web_state
    python scripts/reindex_embeddings.py --workers 4 --batch 48

Idempotente: reconstruye la tabla chunk_embeddings desde cero (backup previo).
"""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

DEFAULT_KNOWLEDGE_DB = REPO_ROOT / "data" / "web_state" / "knowledge_store.db"
DEFAULT_VECTOR_DB = REPO_ROOT / "data" / "web_state" / "vector_store.db"
SHARD_DIR_NAME = "vec_shards"

PROVIDER_ID = "local_onnx"
MODEL_ID = "multilingual-e5-small"
DIMENSIONS = 384

ChunkRow = Tuple[str, str, str]  # (chunk_id, source_id, content)


def _load_chunks(knowledge_db: Path) -> Tuple[List[ChunkRow], Dict[str, List[str]]]:
    """Load all chunks and the source_id -> [notebook_id, ...] mapping."""
    con = sqlite3.connect(f"file:{knowledge_db}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT id, source_id, content FROM chunks ORDER BY id"
        ).fetchall()
        mapping: Dict[str, List[str]] = {}
        for src_id, nb_id in con.execute(
            "SELECT source_id, notebook_id FROM notebook_sources"
        ).fetchall():
            mapping.setdefault(src_id, []).append(nb_id)
    finally:
        con.close()
    return [(r[0], r[1], r[2] or "") for r in rows], mapping


def _read_cpu_temp_c() -> Optional[float]:
    """Best-effort CPU temperature (°C) from sysfs thermal zones. None if unreadable."""
    import glob

    for pattern in (
        "/sys/class/thermal/thermal_zone*/temp",
        "/sys/devices/platform/coretemp.*/hwmon/hwmon*/temp*_input",
    ):
        for path in sorted(glob.glob(pattern)):
            try:
                with open(path) as fh:
                    return int(fh.read().strip()) / 1000.0
            except (OSError, ValueError):
                continue
    return None


def _shard_worker(
    shard_idx: int,
    jobs: Sequence[ChunkRow],
    src_to_nbs: Dict[str, List[str]],
    batch_size: int,
    num_threads: int,
    shards_dir: Path,
    throttle_ms: int = 0,
    max_temp_c: float = 0.0,
) -> Tuple[int, int, float]:
    """Embed a partition of chunks and persist them into a shard SQLite file.

    Runs inside a worker process: instantiates its own ONNX session to avoid
    fork-safety issues with onnxruntime.
    """
    import struct

    from study_engine.retrieval.embedding import LocalONNXEmbeddingProvider

    shard_path = shards_dir / f"shard_{shard_idx}.db"
    # No borrar el shard si existe: contiene los chunks ya embebidos para RESUME.
    conn = sqlite3.connect(str(shard_path))
    conn.execute("PRAGMA journal_mode = OFF;")
    conn.execute("PRAGMA synchronous = OFF;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunk_embeddings (
            chunk_id TEXT NOT NULL,
            notebook_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            provider_id TEXT NOT NULL,
            model_id TEXT NOT NULL,
            dimensions INTEGER NOT NULL,
            vector BLOB NOT NULL,
            PRIMARY KEY (chunk_id, notebook_id)
        );
        """
    )

    embedder = LocalONNXEmbeddingProvider(num_threads=num_threads)

    # RESUME: los chunks ya presentes en este shard (por ejecuciones previas
    # canceladas) se saltan y no se vuelven a embeber.
    already_done = {
        r[0]
        for r in conn.execute("SELECT DISTINCT chunk_id FROM chunk_embeddings")
    }
    pending = [c for c in jobs if c[0] not in already_done]
    if already_done:
        print(
            f"[shard {shard_idx}] RESUMIENDO: {len(already_done)} chunks ya indexados; "
            f"quedan {len(pending)} de {len(jobs)}.",
            flush=True,
        )

    total_rows = 0
    t0 = time.time()
    done = len(already_done)
    for i in range(0, len(pending), batch_size):
        batch = pending[i : i + batch_size]
        vectors = embedder.embed_passages([c[2] for c in batch])

        payload = []
        for (chunk_id, source_id, _content), vec in zip(batch, vectors):
            for nb_id in src_to_nbs.get(source_id, []):
                payload.append(
                    (
                        chunk_id,
                        nb_id,
                        source_id,
                        PROVIDER_ID,
                        MODEL_ID,
                        DIMENSIONS,
                        struct.pack(f"{DIMENSIONS}f", *vec),
                    )
                )
        conn.executemany(
            "INSERT OR REPLACE INTO chunk_embeddings VALUES (?, ?, ?, ?, ?, ?, ?)",
            payload,
        )
        conn.commit()
        total_rows += len(payload)
        done += len(batch)
        if done % (batch_size * 10) == 0 or done == len(jobs):
            elapsed = time.time() - t0
            rate = done / max(elapsed, 1e-6)
            # El ETA se calcula sobre los pendientes reales de esta ejecución.
            processed_now = done - len(already_done)
            rate_now = processed_now / max(elapsed, 1e-6) if processed_now else rate
            remaining = (len(jobs) - done) / max(rate_now, 1e-6)
            temp = _read_cpu_temp_c()
            temp_str = f", {temp:.0f}°C" if temp is not None else ""
            print(
                f"[shard {shard_idx}] {done}/{len(jobs)} chunks "
                f"({rate_now:.0f} c/s, ETA {remaining/60:.1f} min{temp_str})",
                flush=True,
            )

        # Control térmico: pausa activa entre batches
        if throttle_ms > 0:
            time.sleep(throttle_ms / 1000.0)
        if max_temp_c > 0:
            temp_now = _read_cpu_temp_c()
            while temp_now is not None and temp_now >= max_temp_c:
                print(
                    f"[shard {shard_idx}] PAUSA TÉRMICA: {temp_now:.0f}°C >= {max_temp_c:.0f}°C. "
                    "Enfriando 20s...",
                    flush=True,
                )
                time.sleep(20.0)
                temp_now = _read_cpu_temp_c()
    conn.close()
    return shard_idx, total_rows, time.time() - t0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge-db", type=Path, default=DEFAULT_KNOWLEDGE_DB)
    parser.add_argument("--vector-db", type=Path, default=DEFAULT_VECTOR_DB)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--batch", type=int, default=48)
    parser.add_argument("--threads-per-worker", type=int, default=0,
                        help="Threads ONNX por worker (default: ceil(12/workers))")
    parser.add_argument("--max-chunks", type=int, default=0,
                        help="Limitar a N chunks (smoke test; 0 = corpus completo)")
    parser.add_argument("--throttle-ms", type=int, default=0,
                        help="Pausa en ms entre batches por worker (reduce carga térmica sostenida)")
    parser.add_argument("--max-temp", type=float, default=0.0,
                        help="Si la CPU supera esta temperatura (°C), el worker pausa hasta enfriar")
    args = parser.parse_args()

    knowledge_db: Path = args.knowledge_db
    vector_db: Path = args.vector_db
    if not knowledge_db.exists():
        print(f"ERROR: knowledge db no existe: {knowledge_db}")
        return 1

    print(f"[reindex] Cargando chunks de {knowledge_db} ...", flush=True)
    chunks, src_to_nbs = _load_chunks(knowledge_db)
    if not chunks:
        print("ERROR: 0 chunks en la base; nada que indexar.")
        return 1
    if args.max_chunks and args.max_chunks > 0:
        chunks = chunks[: args.max_chunks]
        print(f"[reindex] SMOKE TEST: limitado a {len(chunks)} chunks.")
    print(
        f"[reindex] {len(chunks)} chunks únicos, {len(src_to_nbs)} fuentes mapeadas a notebooks.",
        flush=True,
    )

    # Asignaciones útiles para reporte final
    orphans = [c for c in chunks if not src_to_nbs.get(c[1])]
    if orphans:
        print(f"[reindex] WARN: {len(orphans)} chunks sin notebook (se omiten de filas).", flush=True)

    workers = max(1, args.workers)
    threads = args.threads_per_worker or max(1, math.ceil((os.cpu_count() or 4) / workers))
    shards_dir = vector_db.parent / SHARD_DIR_NAME
    shards_dir.mkdir(parents=True, exist_ok=True)

    # Particionado round-robin por índice para distribución homogénea
    partitions: List[List[ChunkRow]] = [[] for _ in range(workers)]
    for idx, ch in enumerate(chunks):
        partitions[idx % workers].append(ch)

    t_start = time.time()
    print(
        f"[reindex] Iniciando {workers} workers x {threads} threads, batch={args.batch}...",
        flush=True,
    )

    total_rows = 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(
                _shard_worker,
                shard_idx=i,
                jobs=partitions[i],
                src_to_nbs=src_to_nbs,
                batch_size=args.batch,
                num_threads=threads,
                shards_dir=shards_dir,
                throttle_ms=args.throttle_ms,
                max_temp_c=args.max_temp,
            )
            for i in range(workers)
        ]
        for fut in as_completed(futures):
            shard_idx, n_rows, secs = fut.result()
            total_rows += n_rows
            print(f"[reindex] shard {shard_idx} completo: {n_rows} filas en {secs/60:.1f} min.", flush=True)

    # Backup del vector store anterior y merge de shards
    if vector_db.exists():
        backup = vector_db.with_suffix(".db.bak")
        shutil.copy2(vector_db, backup)
        print(f"[reindex] Backup del vector store previo -> {backup}", flush=True)

    final_conn = sqlite3.connect(str(vector_db))
    final_conn.execute("PRAGMA journal_mode = WAL;")
    final_conn.execute("PRAGMA synchronous = NORMAL;")
    final_conn.execute("DROP TABLE IF EXISTS chunk_embeddings;")
    final_conn.execute(
        """
        CREATE TABLE chunk_embeddings (
            chunk_id TEXT NOT NULL,
            notebook_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            provider_id TEXT NOT NULL,
            model_id TEXT NOT NULL,
            dimensions INTEGER NOT NULL,
            vector BLOB NOT NULL,
            PRIMARY KEY (chunk_id, notebook_id)
        );
        """
    )
    final_conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_vec_notebook ON chunk_embeddings(notebook_id);"
    )
    final_conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_vec_source ON chunk_embeddings(source_id);"
    )

    # Merge atómico: una sola transacción para todos los shards. Si el proceso
    # se interrumpe aquí, la tabla final queda completamente vieja o completamente
    # nueva (nunca a medias) y la corrida siguiente rehace el merge en segundos.
    shard_aliases = []
    for i in range(len(partitions)):
        shard_path = shards_dir / f"shard_{i}.db"
        alias = f"shard_{i}"
        final_conn.execute(f"ATTACH DATABASE '{shard_path}' AS {alias}")
        shard_aliases.append(alias)
    final_conn.commit()

    final_conn.execute("BEGIN")
    try:
        for alias in shard_aliases:
            final_conn.execute(
                "INSERT OR REPLACE INTO chunk_embeddings "
                "SELECT chunk_id, notebook_id, source_id, provider_id, model_id, dimensions, vector "
                f"FROM {alias}.chunk_embeddings"
            )
        final_conn.commit()
    except Exception:
        final_conn.rollback()
        raise
    finally:
        for alias in shard_aliases:
            try:
                final_conn.execute(f"DETACH DATABASE {alias}")
            except sqlite3.Error:
                pass
    final_conn.commit()

    counts = final_conn.execute(
        "SELECT notebook_id, COUNT(*) FROM chunk_embeddings GROUP BY notebook_id ORDER BY 2 DESC"
    ).fetchall()
    total_final = final_conn.execute("SELECT COUNT(*) FROM chunk_embeddings").fetchone()[0]
    final_conn.close()

    elapsed = time.time() - t_start
    print(f"[reindex] Filas por notebook:")
    for nb, n in counts:
        print(f"  - {nb}: {n}")
    print(
        f"[reindex] COMPLETADO: {total_final} filas ({len(chunks)} chunks únicos) "
        f"en {elapsed/60:.1f} min. Vector DB: {vector_db}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
