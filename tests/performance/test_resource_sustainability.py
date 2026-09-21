"""Auditoría de Rendimiento: Consumo de RAM y Sostenibilidad de Recursos (Fase 7.3, Métrica 13).

Métrica Evaluada:
- Métrica 13: Consumo de RAM y CPU Sostenido (1.000 consultas consecutivas)
    - Memory leak: crecimiento < 10MB por 1.000 consultas
    - Peak RAM: < 2GB
    - Estabilidad de memoria retenida y recolección de basura (GC)
"""

import gc
import time
import tracemalloc
from pathlib import Path
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


def test_resource_sustainability_1000_queries_memory_leak(tmp_path: Path) -> None:
    """Verifica que el consumo de memoria permanezca acotado (< 10 MB de crecimiento) en 1.000 consultas continuas."""
    db_path = tmp_path / "memory_sustained.db"
    storage = StudentStorage(db_path)
    storage.save_bkt_state(BKTState(kc_id="sustained_kc", p_L=0.50, attempts=1))

    sanitizer = DataSanitizer()
    compiler = ContextCompiler()
    controller = EpistemicController(student_storage=storage)
    narrator = PersonaNarrator()

    # Pre-warming del pipeline
    warm_seed = [
        SearchResult(
            chunk_id="chk_warm",
            source_id="src_sys",
            document_id="doc_sys",
            content="Información canónica de precarga para pruebas de memoria.",
            snippet="Información canónica...",
            index=0,
            page_start=1,
            page_end=2,
            score=0.9,
        )
    ]
    warm_pack = compiler.build_context_pack("Prewarm", warm_seed, current_kc="sustained_kc")
    warm_payload = controller.process("Prewarm", warm_pack, kc_id="sustained_kc")
    _ = narrator.narrate(warm_payload)

    gc.collect()
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()

    gc_times = []
    # Ejecución de 1.000 consultas consecutivas simulando una sesión de estudio intensiva
    for i in range(1000):
        query = f"Consulta técnica sostenida de estudio #{i} sobre paginación y memoria virtual."
        clean_q = sanitizer.scrub(query)

        seed = [
            SearchResult(
                chunk_id=f"chk_mem_{i % 20}",
                source_id="src_mem",
                document_id="doc_mem",
                content="La memoria virtual usa tablas de páginas multinivel para reducir el consumo de marcos.",
                snippet="La memoria virtual usa tablas...",
                index=i % 20,
                page_start=100 + (i % 10),
                page_end=101 + (i % 10),
                score=0.92,
            )
        ]
        pack = compiler.build_context_pack(clean_q, seed, current_kc="sustained_kc")
        payload = controller.process(
            query=clean_q,
            context_pack=pack,
            kc_id="sustained_kc",
            style=ConversationStyle.NORMAL if i % 2 == 0 else ConversationStyle.CASUAL,
        )
        prose = narrator.narrate(payload)

        # Medir pausas GC de generaciones jóvenes cada 250 ciclos
        if (i + 1) % 250 == 0:
            t_gc = time.perf_counter()
            gc.collect(1)
            gc_duration_ms = (time.perf_counter() - t_gc) * 1000.0
            gc_times.append(gc_duration_ms)

    gc.collect()
    snapshot_after = tracemalloc.take_snapshot()
    current, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Análisis de diferencias de memoria retenida
    top_stats = snapshot_after.compare_to(snapshot_before, "lineno")
    total_diff_bytes = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)
    total_diff_mb = total_diff_bytes / (1024 * 1024)
    peak_mb = peak_bytes / (1024 * 1024)

    # Criterios de la Métrica 13:
    # 1. Crecimiento neto < 10MB por 1.000 consultas
    assert total_diff_mb < 10.0, (
        f"Memory leak detectado: {total_diff_mb:.2f} MB acumulados en 1.000 consultas (límite: 10.0 MB)"
    )

    # 2. Peak RAM < 2GB (2048 MB)
    assert peak_mb < 2048.0, (
        f"Peak RAM excedió el límite de 2GB: {peak_mb:.2f} MB"
    )

    # 3. Pausas de GC < 50ms
    for pause in gc_times:
        assert pause < 50.0, f"Pausa GC excesiva detectada: {pause:.2f}ms >= 50ms"
