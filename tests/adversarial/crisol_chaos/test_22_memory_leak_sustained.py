"""Escenario 22: Memory Leak Bajo Carga Sostenida (Fase 7.2 - Chaos Engineering).

Simular 150 ciclos continuos de procesamiento fáctico y narración.
Invariante: Crecimiento de memoria retenida estrictamente controlado (< 10 MB);
            0 fugas de memoria lineales en el pipeline de ejecución.
Severidad: ALTO.
"""

import gc
import tracemalloc
import pytest

from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator


def test_sustained_load_memory_leak_bounded() -> None:
    """Memory growth remains tightly bounded (< 10 MB) across 150 consecutive request cycles."""
    controller = EpistemicController()
    narrator = PersonaNarrator()

    # Pre-warm
    pack = ContextPack(current_kc="memory_bench", total_tokens=40)
    pack.add_evidence(
        ChunkWithProvenance(
            chunk_id="chk_warm",
            document_id="doc_warm",
            source_id="src_warm",
            source_title="Operating Systems",
            page_start=1,
            pos_index=1,
            section="Bench",
            content="Evidencia constante de prueba de carga y estabilidad de memoria.",
            is_seed_hit=True,
            relevance_score=0.95,
            token_count=15,
        )
    )
    _ = narrator.narrate(controller.process("Warmup", pack))

    gc.collect()
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()

    # Execute 150 full pipeline cycles
    for i in range(150):
        p = controller.process(f"Consulta continua ciclo {i}", pack)
        _ = narrator.narrate(p)

    gc.collect()
    snapshot_after = tracemalloc.take_snapshot()
    tracemalloc.stop()

    top_stats = snapshot_after.compare_to(snapshot_before, "lineno")
    total_diff_bytes = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)
    total_diff_mb = total_diff_bytes / (1024 * 1024)

    # Invariant: Memory growth across 150 cycles must be strictly less than 10 MB
    assert total_diff_mb < 10.0, f"Memory growth too high: {total_diff_mb:.2f} MB >= 10.0 MB"
