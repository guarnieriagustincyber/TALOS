"""Escenario 12: Concurrencia Extrema (Fase 7.2 - Chaos Engineering).

Simular 20 consultas simultáneas desde múltiples hilos concurrentes hacia el EpistemicController
y el almacenamiento BKT del estudiante.
Invariante: 0 race conditions, 0 excepciones no controladas, integridad determinista del estado.
Severidad: ALTO.
"""

import concurrent.futures
from pathlib import Path
import pytest

from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator
from study_engine.student.contracts import BKTState
from study_engine.student.storage import StudentStorage


def test_20_concurrent_queries_thread_safety(tmp_path: Path) -> None:
    """20 concurrent requests execute without state corruption or race exceptions."""
    db_file = tmp_path / "concurrent_students.db"
    storage = StudentStorage(db_file)

    # Seed 20 distinct KCs
    for i in range(20):
        storage.save_bkt_state(BKTState(kc_id=f"kc_concurrency_{i}", p_L=0.20 + (i * 0.02), attempts=1))

    controller = EpistemicController(student_storage=storage)
    narrator = PersonaNarrator()

    def worker_task(idx: int) -> dict:
        kc = f"kc_concurrency_{idx}"
        pack = ContextPack(current_kc=kc, total_tokens=30)
        pack.add_evidence(
            ChunkWithProvenance(
                chunk_id=f"chk_{idx}",
                document_id="doc_os",
                source_id="src_os",
                source_title="OS Architecture",
                page_start=10 + idx,
                pos_index=1,
                section="Core",
                content=f"Invariante de concurrencia thread-safe para componente {idx}.",
                is_seed_hit=True,
                relevance_score=0.90,
                token_count=15,
            )
        )
        payload = controller.process(
            query=f"Explicame el funcionamiento del componente {idx}",
            context_pack=pack,
            kc_id=kc,
        )
        prose = narrator.narrate(payload)
        return {"idx": idx, "kc": kc, "p_L": payload.bkt_status.p_L, "prose_len": len(prose)}

    # Dispatch 20 concurrent threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(worker_task, i) for i in range(20)]
        results = [f.result(timeout=10.0) for f in concurrent.futures.as_completed(futures)]

    assert len(results) == 20
    # Verify every request processed cleanly without corruption
    for r in results:
        assert r["prose_len"] > 20
        assert r["p_L"] >= 0.20
