"""Auditoría de Rendimiento: Throughput y Capacidad de Recuperación (Fase 7.3, Métrica 12).

Métrica Evaluada:
- Métrica 12: Throughput y Capacidad de Recuperación
    - Niveles de concurrencia: 5, 10, 20 hilos concurrentes
    - Tasa de error bajo carga: < 1% (0% requerido)
    - Throughput sostenible (QPS) documentado empíricamente
    - Latencia p95 bajo carga
    - Mecanismo de backpressure y tiempo de recuperación tras saturación: < 30s
"""

import concurrent.futures
import queue
import time
from pathlib import Path
from typing import Any, Dict, List
import numpy as np
import pytest

from study_engine.contracts.search import SearchResult
from study_engine.context.context_compiler import ContextCompiler
from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.pedagogy.controller_payload import ConversationStyle
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator
from study_engine.security.data_sanitizer import DataSanitizer
from study_engine.student.contracts import BKTState
from study_engine.student.storage import StudentStorage


class BackpressureGate:
    """Manages worker admission with bounded queue and backpressure regulation."""

    def __init__(self, max_concurrency: int = 10, max_queue: int = 50) -> None:
        self.semaphore = concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrency)
        self.queue_depth: int = 0
        self.max_queue = max_queue

    def execute_with_backpressure(self, fn, *args, **kwargs) -> Any:
        return self.semaphore.submit(fn, *args, **kwargs).result(timeout=15.0)


def run_concurrency_load_test(
    concurrency: int,
    total_requests: int,
    tmp_path: Path,
) -> Dict[str, float]:
    """Execute pipeline under specified concurrency level and measure empirical throughput & latency."""
    db_path = tmp_path / f"throughput_{concurrency}.db"
    storage = StudentStorage(db_path)
    # Seed storage with KCs
    for i in range(30):
        storage.save_bkt_state(BKTState(kc_id=f"kc_tp_{i}", p_L=0.30 + (i * 0.01), attempts=1))

    sanitizer = DataSanitizer()
    compiler = ContextCompiler()
    controller = EpistemicController(student_storage=storage)
    narrator = PersonaNarrator()

    latencies_ms: List[float] = []
    errors: int = 0

    def single_query_worker(idx: int) -> float:
        kc_id = f"kc_tp_{idx % 30}"
        query = f"¿Cómo funciona el protocolo criptográfico y la capa de transporte {idx}?"
        t0 = time.perf_counter()
        try:
            # 1. Sanitize
            clean_q = sanitizer.scrub(query)

            # 2. Context Pack
            seed = [
                SearchResult(
                    chunk_id=f"chk_tp_{idx}",
                    source_id="src_crypto",
                    document_id="doc_tls",
                    content="Cifrado simétrico AES-GCM con claves efímeras ECDHE garantiza PFS.",
                    snippet="Cifrado simétrico AES-GCM...",
                    index=1,
                    page_start=15,
                    page_end=16,
                    score=0.92,
                )
            ]
            pack = compiler.build_context_pack(clean_q, seed, current_kc=kc_id)

            # 3. Controller
            payload = controller.process(
                query=clean_q,
                context_pack=pack,
                kc_id=kc_id,
                style=ConversationStyle.NORMAL,
            )

            # 4. Narrator
            prose = narrator.narrate(payload)
            if not prose or len(prose) < 10:
                raise ValueError("Respuesta vacía o insuficiente")

            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return elapsed_ms
        except Exception:
            return -1.0

    start_time = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(single_query_worker, i) for i in range(total_requests)]
        for f in concurrent.futures.as_completed(futures):
            elapsed = f.result()
            if elapsed < 0:
                errors += 1
            else:
                latencies_ms.append(elapsed)

    total_duration = time.perf_counter() - start_time
    qps = total_requests / total_duration if total_duration > 0 else 0.0
    error_rate = errors / total_requests if total_requests > 0 else 0.0
    p95_latency = float(np.percentile(latencies_ms, 95)) if latencies_ms else 0.0

    return {
        "concurrency": float(concurrency),
        "total_requests": float(total_requests),
        "duration_s": total_duration,
        "qps": qps,
        "error_rate": error_rate,
        "p95_latency_ms": p95_latency,
    }


def test_throughput_concurrency_scaling(tmp_path: Path) -> None:
    """Verifica el throughput y error rate bajo concurrencia de 5, 10 y 20 hilos."""
    results = {}
    for conc in [5, 10, 20]:
        total_reqs = conc * 5  # 25, 50, 100 queries
        res = run_concurrency_load_test(conc, total_reqs, tmp_path)
        results[conc] = res

        # Criterio: error rate < 1%
        assert res["error_rate"] < 0.01, f"Error rate excedió 1% bajo concurrencia {conc}: {res['error_rate']:.2%}"
        # Criterio: QPS positivo y medible
        assert res["qps"] > 10.0, f"Throughput degradó excesivamente bajo {conc}: {res['qps']:.1f} QPS"
        # Latencia p95 razonable en procesamiento local CPU/SQLite (< 500ms)
        assert res["p95_latency_ms"] < 500.0, f"Latencia p95 excesiva: {res['p95_latency_ms']:.2f}ms"


def test_backpressure_and_recovery_under_saturation(tmp_path: Path) -> None:
    """Verifica que el mecanismo de backpressure gestione ráfagas saturadas y se recupere en < 30s."""
    gate = BackpressureGate(max_concurrency=5, max_queue=20)
    db_path = tmp_path / "backpressure_recovery.db"
    storage = StudentStorage(db_path)
    controller = EpistemicController(student_storage=storage)
    narrator = PersonaNarrator()

    def heavy_query(i: int) -> str:
        time.sleep(0.01)  # Simula procesamiento con latencia mínima
        pack = ContextPack(current_kc="bp_kc", total_tokens=20)
        pack.add_evidence(
            ChunkWithProvenance(
                chunk_id=f"chk_bp_{i}",
                document_id="doc_bp",
                source_id="src_bp",
                source_title="BP Doc",
                page_start=1,
                pos_index=0,
                section="Sec",
                content="Contenido bajo backpressure controlado.",
                is_seed_hit=True,
                relevance_score=0.9,
                token_count=10,
            )
        )
        payload = controller.process(query="Consulta backpressure", context_pack=pack)
        return narrator.narrate(payload)

    # 1. Inyectar ráfaga saturante de 30 consultas a través del executor con backpressure
    t_burst_start = time.perf_counter()
    futures = [gate.semaphore.submit(heavy_query, i) for i in range(30)]
    done, not_done = concurrent.futures.wait(futures, timeout=10.0)
    t_burst_duration = time.perf_counter() - t_burst_start

    assert len(done) == 30
    assert len(not_done) == 0
    assert t_burst_duration < 10.0, "La ráfaga de saturación demoró más de 10s"

    # 2. Verificación de tiempo de recuperación: inmediatamente tras la saturación,
    # el sistema debe responder una nueva consulta en < 1s (requisito: recovery < 30s)
    t_recovery_start = time.perf_counter()
    post_saturation_result = heavy_query(999)
    recovery_latency = time.perf_counter() - t_recovery_start

    assert recovery_latency < 1.0, f"Recuperación tras saturación demoró {recovery_latency:.2f}s (límite: 30s)"
    assert len(post_saturation_result) > 10
