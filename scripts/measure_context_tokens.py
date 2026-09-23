#!/usr/bin/env python3
"""Empirical Context Token Measurement Script (BACKLOG-CTX-001 / FASE A).

Measures token distribution and RAM usage across:
1. 20 Pre-registered complex queries (broad, deep context across OS, C, structures, architecture).
2. 18 Golden Set v1 queries from data/eval/golden_set_v1.json.

Uses SectionExpander's token count logic (C3: Chunk.token_count or len(content.split()) * 4 // 3)
with EXPANSION_WINDOW = 1 (±1 chunk).

Evaluates the decision branch (A3):
- p99 < 3500 tokens -> Confirm 4,000 ceiling and recommend closing BACKLOG-CTX-001.
- p99 >= 3500 tokens -> Propose 5,000 or 6,000 ceiling with RAM measurement, keep open.

Outputs:
- Aligned distribution table (min, max, mean, p50, p90, p99).
- Tokens window ±1 vs ceiling tokens.
- Peak RAM usage in MB.
- Saves data/experiments/context_token_distribution_report.json.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
import resource
import sys
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from study_engine.contracts.retrieval import RetrievalRequest
from study_engine.contracts.search import SearchResult
from study_engine.retrieval.dense import DenseRetriever
from study_engine.retrieval.embedding import LocalONNXEmbeddingProvider
from study_engine.retrieval.expansion import SectionExpander, EXPANSION_WINDOW, HARD_CEILING_TOKENS
from study_engine.retrieval.hybrid import HybridRetriever
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.retrieval.service import RetrievalService
from study_engine.retrieval.vector_store import SQLiteVectorStore
from study_engine.storage.knowledge_store import KnowledgeStore

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("measure_context_tokens")

# -----------------------------------------------------------------------------
# 20 PRE-REGISTERED COMPLEX QUERIES (A4)
# -----------------------------------------------------------------------------
COMPLEX_QUERIES: List[str] = [
    "explicar el ciclo de vida completo de un proceso incluyendo estados, transiciones, PCB y cambio de contexto con syscalls",
    "comparación detallada entre memoria virtual, paginación, tablas de páginas y segmentación con traducción de direcciones MMU",
    "mecanismos de sincronización concurrente: semáforos contadores, mutex, variables de condición y monitores con problemas clásicos",
    "gestión integral de memoria en C: stack frame, registros de activación, heap, malloc, free y prevención de memory leaks",
    "árboles binarios de búsqueda autobalanceados AVL y rojo-negro: rotaciones, inserción, eliminación y complejidad asintótica",
    "interbloqueo o deadlock: condiciones de Coffman, detección mediante grafos de asignación de recursos y algoritmo del banquero",
    "comunicación entre procesos IPC mediante pipes anónimos, FIFOs, memoria compartida y pasaje de mensajes con sockets",
    "planificación de CPU a corto y largo plazo: algoritmos FCFS, Round Robin, SJF con envejecimiento y colas multinivel con retroalimentación",
    "arquitectura del conjunto de instrucciones x86-64: registros de propósito general, convención de llamada ABI y stack layout",
    "estructuras de datos lineales fundamentales: pilas, colas, listas simplemente enlazadas y doblemente enlazadas con operaciones de punteros",
    "llamadas al sistema vs funciones de biblioteca: transición modo usuario a modo kernel, vectores de interrupción e IDT",
    "manejo de archivos y sistemas de archivos: inodos, tablas de descriptores de archivos abiertos, enlaces duros y simbólicos",
    "análisis asintótico de algoritmos: notación Big-O, Omega, Theta, relaciones de recurrencia y teorema maestro",
    "algoritmos de ordenamiento cuadráticos vs logarítmicos: quicksort, mergesort, heapsort con estabilidad y espacio auxiliar",
    "manejo de señales POSIX: sigaction, máscaras de señales, reentrancia y controladores de señales asíncronos",
    "recursión vs iteración: optimización de recursión por la cola (tail call optimization), consumo de stack y desbordamiento de pila",
    "representación de datos en bajo nivel: complemento a dos, punto flotante IEEE-754, endianness y alineación de memoria",
    "seguridad en memoria: desbordamiento de buffer (buffer overflow), canarios de stack, ASLR y páginas no ejecutables NX/DEP",
    "hilos de usuario vs hilos de kernel: modelos 1:1, M:N y primitivas de la biblioteca POSIX pthreads",
    "estructuras de datos no lineales: grafos, matrices de adyacencia, listas de adyacencia, recorridos BFS y DFS con aplicaciones",
]


def load_golden_set_queries() -> List[str]:
    """Load queries from data/eval/golden_set_v1.json."""
    golden_path = REPO_ROOT / "data" / "eval" / "golden_set_v1.json"
    if not golden_path.exists():
        logger.warning("Golden Set v1 not found at %s", golden_path)
        return []
    data = json.loads(golden_path.read_text(encoding="utf-8"))
    return [q["query"] for q in data.get("queries", [])]


def compute_statistics(values: List[int]) -> Dict[str, float]:
    """Calculate min, max, mean, p50, p90, p99 percentiles."""
    if not values:
        return {"count": 0, "min": 0, "max": 0, "mean": 0, "p50": 0, "p90": 0, "p99": 0}
    sorted_vals = sorted(values)
    n = len(sorted_vals)

    def percentile(p: float) -> float:
        k = (n - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return float(sorted_vals[int(k)])
        d0 = sorted_vals[int(f)] * (c - k)
        d1 = sorted_vals[int(c)] * (k - f)
        return float(d0 + d1)

    return {
        "count": n,
        "min": float(sorted_vals[0]),
        "max": float(sorted_vals[-1]),
        "mean": round(sum(sorted_vals) / n, 2),
        "p50": round(percentile(50.0), 2),
        "p90": round(percentile(90.0), 2),
        "p99": round(percentile(99.0), 2),
    }


def get_current_rss_mb() -> float:
    """Return max RSS in megabytes."""
    rusage = resource.getrusage(resource.RUSAGE_SELF)
    # On Linux, ru_maxrss is in kilobytes
    return rusage.ru_maxrss / 1024.0


def main() -> int:
    logger.info("Starting context token measurement (BACKLOG-CTX-001)...")
    initial_rss = get_current_rss_mb()

    # Resolve database paths
    ks_path = REPO_ROOT / "data" / "web_state" / "knowledge_store.db"
    vs_path = REPO_ROOT / "data" / "web_state" / "vector_store.db"

    if not ks_path.exists() or not vs_path.exists():
        logger.error("Required databases not found: %s or %s", ks_path, vs_path)
        return 1

    store = KnowledgeStore(ks_path)
    vstore = SQLiteVectorStore(vs_path)
    provider = LocalONNXEmbeddingProvider()
    dense = DenseRetriever(store, vstore, provider)
    lex = LexicalRetriever(store=store)
    hybrid = HybridRetriever(store, lex, dense)
    service = RetrievalService(store=store, retriever=hybrid)

    # Instantiate two expanders:
    # 1. Unbounded expander (measuring pure arithmetic window ±1 tokens)
    # 2. Hard-ceiling expander (measuring tokens delivered under HARD_CEILING_TOKENS)
    expander_unbounded = SectionExpander(engine=store.engine, hard_ceiling_tokens=1_000_000)
    expander_ceiling = SectionExpander(engine=store.engine, hard_ceiling_tokens=HARD_CEILING_TOKENS)

    golden_queries = load_golden_set_queries()
    logger.info("Loaded %d Golden Set v1 queries and %d complex queries.", len(golden_queries), len(COMPLEX_QUERIES))

    all_query_entries: List[Tuple[str, str, str]] = []
    for q in COMPLEX_QUERIES:
        all_query_entries.append(("complex_20", "NB-CYBERSECURITY-V1", q))
    for q in golden_queries:
        all_query_entries.append(("golden_set_v1", "fase0-soc", q))

    results: List[Dict[str, Any]] = []
    tokens_window_list: List[int] = []
    tokens_ceiling_list: List[int] = []
    pruned_count = 0

    for group, notebook_id, query_str in all_query_entries:
        try:
            candidates = service.retrieve_evidence(
                query=query_str,
                notebook_id=notebook_id,
                top_k=5,
            )
        except Exception as e:
            logger.warning("Retrieval failed for query '%s': %s", query_str[:50], e)
            candidates = []

        search_results = [
            SearchResult(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                source_id=c.source_id,
                score=c.score,
                snippet=c.content[:100],
                content=c.content,
                index=c.pos_index,
                page_start=c.page_start,
                page_end=c.page_end,
            )
            for c in candidates
        ]

        # 1. Unbounded expansion (arithmetic window ±1)
        expanded_unbounded, _ = expander_unbounded.expand_results(search_results)
        tok_window = sum(c.token_count for c in expanded_unbounded)

        # 2. Hard-ceiling expansion
        expanded_ceiling, _ = expander_ceiling.expand_results(search_results)
        tok_ceiling = sum(c.token_count for c in expanded_ceiling)

        exceeded = tok_window > HARD_CEILING_TOKENS
        if exceeded:
            pruned_count += 1

        tokens_window_list.append(tok_window)
        tokens_ceiling_list.append(tok_ceiling)

        results.append({
            "group": group,
            "notebook_id": notebook_id,
            "query": query_str,
            "seed_hits": len(candidates),
            "expanded_chunks_window": len(expanded_unbounded),
            "expanded_chunks_ceiling": len(expanded_ceiling),
            "tokens_window": tok_window,
            "tokens_ceiling": tok_ceiling,
            "ceiling_exceeded": exceeded,
        })

    peak_rss = get_current_rss_mb()
    delta_rss = max(0.0, peak_rss - initial_rss)

    stats_window = compute_statistics(tokens_window_list)
    stats_ceiling = compute_statistics(tokens_ceiling_list)

    # Evaluate decision rule (A3)
    p99 = stats_window["p99"]
    decision_closed = p99 < 3500.0

    # Print summary report
    print("\n" + "=" * 80)
    print("DISTRIBUCIÓN DE TOKENS DE CONTEXTO — INVESTIGACIÓN BACKLOG-CTX-001 (FASE A)")
    print("=" * 80)
    print(f"Total queries evaluadas: {len(all_query_entries)} (20 complejas + {len(golden_queries)} Golden Set v1)")
    print(f"Radio de expansión:      EXPANSION_WINDOW = ±{EXPANSION_WINDOW} chunks")
    print(f"Hard ceiling configurado: HARD_CEILING_TOKENS = {HARD_CEILING_TOKENS} tokens")
    print(f"Memoria RAM pico:        {peak_rss:.2f} MB (Delta: +{delta_rss:.2f} MB)")
    print("-" * 80)
    print(f"{'Métrica':<25} | {'Ventana ±1 (Aritmética)':<25} | {'Ceiling (Con corte)':<20}")
    print("-" * 80)
    print(f"{'Mínimo':<25} | {stats_window['min']:<25.1f} | {stats_ceiling['min']:<20.1f}")
    print(f"{'Media (Mean)':<25} | {stats_window['mean']:<25.1f} | {stats_ceiling['mean']:<20.1f}")
    print(f"{'Mediana (p50)':<25} | {stats_window['p50']:<25.1f} | {stats_ceiling['p50']:<20.1f}")
    print(f"{'Percentil 90 (p90)':<25} | {stats_window['p90']:<25.1f} | {stats_ceiling['p90']:<20.1f}")
    print(f"{'Percentil 99 (p99)':<25} | {stats_window['p99']:<25.1f} | {stats_ceiling['p99']:<20.1f}")
    print(f"{'Máximo':<25} | {stats_window['max']:<25.1f} | {stats_ceiling['max']:<20.1f}")
    print("-" * 80)
    print(f"Queries con corte (>4000 tok): {pruned_count} / {len(all_query_entries)} ({pruned_count / len(all_query_entries) * 100:.1f}%)")
    print("-" * 80)
    print("DECISIÓN BACKLOG-CTX-001 (Addendum A3):")
    if decision_closed:
        print(f"  [✓] p99 ({p99:.1f} tokens) < 3.500 tokens.")
        print(f"  --> HARD_CEILING_TOKENS = {HARD_CEILING_TOKENS} CONFIRMADO.")
        print("  --> BACKLOG-CTX-001 queda CERRADO con evidencia empírica.")
    else:
        print(f"  [!] p99 ({p99:.1f} tokens) >= 3.500 tokens.")
        print("  --> Proponer incremento conservador a 5.000 o 6.000 tokens.")
        print("  --> BACKLOG-CTX-001 permanece abierto para ajuste de cuota.")
    print("=" * 80 + "\n")

    # Save detailed JSON report
    report_path = REPO_ROOT / "data" / "experiments" / "context_token_distribution_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_data = {
        "metadata": {
            "schema": "talos-context-token-measurement-v1",
            "expansion_window": EXPANSION_WINDOW,
            "hard_ceiling_tokens": HARD_CEILING_TOKENS,
            "total_queries": len(all_query_entries),
            "complex_queries_count": len(COMPLEX_QUERIES),
            "golden_set_queries_count": len(golden_queries),
            "peak_rss_mb": round(peak_rss, 2),
            "delta_rss_mb": round(delta_rss, 2),
            "decision": "CLOSED" if decision_closed else "OPEN_PROPOSE_EXPANSION",
            "decision_rule": "p99 < 3500 confirms 4k and closes backlog; p99 >= 3500 proposes 5k/6k",
        },
        "stats_window_arithmetic": stats_window,
        "stats_ceiling": stats_ceiling,
        "pruned_queries_count": pruned_count,
        "queries_detail": results,
    }
    report_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Report saved to %s", report_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
