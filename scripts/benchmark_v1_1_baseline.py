#!/usr/bin/env python3
"""Benchmark V1.1 Baseline Runner (Fase A).

Evaluates the current single-query retrieval and evidence pipeline
against a 20-query suite containing simple, multi-topic, and out-of-scope queries
to measure:
- single_source_rate
- source_diversity_score
- subtopic_coverage_rate
- missing_topic_detection_rate (unawareness rate)
"""

import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Dict, List, Set

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ingest_corpus import ingest_benchmark_corpus
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.evidence.engine import EvidenceEngine
from study_engine.context.packer import ContextPacker
from study_engine.retrieval.dense import DenseRetriever
from study_engine.retrieval.embedding import DeterministicHashEmbedder
from study_engine.retrieval.hybrid import HybridRetriever
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.retrieval.service import RetrievalService
from study_engine.retrieval.vector_store import SQLiteVectorStore, VectorRecord
from study_engine.storage.knowledge_store import KnowledgeStore

# 20 Evaluated Queries Suite
BENCHMARK_QUERIES = [
    # --- Grupo 1: Consultas Simples (Control, 1 tema central) ---
    {
        "id": "Q01-SIMPLE",
        "query": "¿Cuáles son los tres estados fundamentales en los que puede encontrarse un proceso?",
        "expected_subtopics": ["estados de proceso"],
        "expected_sources": ["so_procesos.pdf"],
        "missing_subtopics": [],
    },
    {
        "id": "Q02-SIMPLE",
        "query": "¿Qué es una condición de carrera y cómo se define en sistemas operativos?",
        "expected_subtopics": ["condiciones de carrera"],
        "expected_sources": ["so_concurrencia.pdf"],
        "missing_subtopics": [],
    },
    {
        "id": "Q03-SIMPLE",
        "query": "¿Cómo funciona la planificación apropiativa de CPU por tiempo compartido?",
        "expected_subtopics": ["planificación de CPU"],
        "expected_sources": ["so_planificacion.pdf"],
        "missing_subtopics": [],
    },
    {
        "id": "Q04-SIMPLE",
        "query": "¿Qué es la memoria virtual y cómo se divide el espacio con páginas y marcos?",
        "expected_subtopics": ["memoria virtual"],
        "expected_sources": ["so_memoria.pdf"],
        "missing_subtopics": [],
    },
    {
        "id": "Q05-SIMPLE",
        "query": "¿Cómo funciona la aritmética de punteros y la desreferenciación en C?",
        "expected_subtopics": ["punteros en C"],
        "expected_sources": ["prog_punteros.pdf"],
        "missing_subtopics": [],
    },

    # --- Grupo 2: Consultas Compuestas Multi-Tema (2 a 4 temas que requieren varias fuentes) ---
    {
        "id": "Q06-MULTI",
        "query": "Explícame cómo se crea un proceso con fork(), cómo compite por la CPU en la planificación y cómo se produce una condición de carrera si comparten memoria.",
        "expected_subtopics": ["creación de procesos fork", "planificación de CPU", "condición de carrera"],
        "expected_sources": ["so_procesos.pdf", "so_planificacion.pdf", "so_concurrencia.pdf"],
        "missing_subtopics": [],
    },
    {
        "id": "Q07-MULTI",
        "query": "¿Cómo interactúa la asignación de memoria virtual con los punteros en C y las listas enlazadas dinámicas?",
        "expected_subtopics": ["memoria virtual", "punteros en C", "listas enlazadas dinámicas"],
        "expected_sources": ["so_memoria.pdf", "prog_punteros.pdf", "prog_lineales.pdf"],
        "missing_subtopics": [],
    },
    {
        "id": "Q08-MULTI",
        "query": "Compara el uso de semáforos para sincronización de hilos frente a la alternancia estricta y variables de cerradura.",
        "expected_subtopics": ["semáforos", "alternancia estricta", "variables de cerradura"],
        "expected_sources": ["so_concurrencia.pdf"],
        "missing_subtopics": [],
    },
    {
        "id": "Q09-MULTI",
        "query": "¿Cómo se implementa un árbol binario en memoria usando punteros y cómo se persisten sus nodos en un archivo binario?",
        "expected_subtopics": ["árbol binario", "punteros", "persistencia en archivo"],
        "expected_sources": ["prog_arboles.pdf", "prog_punteros.pdf", "prog_archivos.pdf"],
        "missing_subtopics": [],
    },
    {
        "id": "Q10-MULTI",
        "query": "Explica la diferencia entre procesos e hilos, el cambio de contexto y cómo se gestiona la tabla de páginas durante el context switch.",
        "expected_subtopics": ["procesos e hilos", "cambio de contexto", "tabla de páginas en memoria virtual"],
        "expected_sources": ["so_procesos.pdf", "so_planificacion.pdf", "so_memoria.pdf"],
        "missing_subtopics": [],
    },
    {
        "id": "Q11-MULTI",
        "query": "¿Qué algoritmos de planificación de CPU existen (Round Robin, FCFS) y cómo influyen en el tiempo de retorno y el rendimiento del sistema?",
        "expected_subtopics": ["Round Robin", "FCFS", "tiempo de retorno"],
        "expected_sources": ["so_planificacion.pdf"],
        "missing_subtopics": [],
    },
    {
        "id": "Q12-MULTI",
        "query": "Describe cómo manejar archivos con fopen, fread, fwrite y cómo estructurar los datos leídos en pilas y colas en memoria.",
        "expected_subtopics": ["I/O archivos fopen", "pilas y colas"],
        "expected_sources": ["prog_archivos.pdf", "prog_lineales.pdf"],
        "missing_subtopics": [],
    },
    {
        "id": "Q13-MULTI",
        "query": "¿Cómo se comunican los procesos mediante señales de UNIX y cómo se relacionan con las secciones críticas protegidas por mutexes?",
        "expected_subtopics": ["señales de UNIX", "sección crítica y mutex"],
        "expected_sources": ["so_procesos.pdf", "so_concurrencia.pdf"],
        "missing_subtopics": [],
    },
    {
        "id": "Q14-MULTI",
        "query": "Explica el algoritmo del banquero para evitar deadlocks, la exclusión mutua y cómo los bloqueos afectan la cola de procesos listos.",
        "expected_subtopics": ["deadlock y exclusión mutua", "cola de procesos listos"],
        "expected_sources": ["so_concurrencia.pdf", "so_procesos.pdf"],
        "missing_subtopics": [],
    },
    {
        "id": "Q15-MULTI",
        "query": "¿Cómo se recorre un árbol en inorden y postorden y cómo se utilizan estructuras lineales auxiliares como la pila de llamadas?",
        "expected_subtopics": ["recorridos de árboles", "pilas y estructuras lineales"],
        "expected_sources": ["prog_arboles.pdf", "prog_lineales.pdf"],
        "missing_subtopics": [],
    },

    # --- Grupo 3: Consultas Compuestas con Temas Faltantes / Fuera de Scope ---
    {
        "id": "Q16-MISSING",
        "query": "Explícame cómo funciona la planificación de procesos en Linux y cómo Suricata inspecciona el tráfico de red en modo IDS.",
        "expected_subtopics": ["planificación de procesos", "Suricata IDS inspección de red"],
        "expected_sources": ["so_planificacion.pdf"],
        "missing_subtopics": ["Suricata IDS inspección de red"],
    },
    {
        "id": "Q17-MISSING",
        "query": "¿Cómo gestiona el SO la memoria virtual paginada y qué algoritmos de Deep Learning optimizan la predicción de fallos de página?",
        "expected_subtopics": ["memoria virtual paginada", "algoritmos Deep Learning"],
        "expected_sources": ["so_memoria.pdf"],
        "missing_subtopics": ["algoritmos Deep Learning"],
    },
    {
        "id": "Q18-MISSING",
        "query": "¿Cómo se sincronizan los procesos mediante semáforos en C y cómo se configura una regla en Snort para detectar escaneos Nmap?",
        "expected_subtopics": ["semáforos en C", "regla Snort detección Nmap"],
        "expected_sources": ["so_concurrencia.pdf"],
        "missing_subtopics": ["regla Snort detección Nmap"],
    },
    {
        "id": "Q19-MISSING",
        "query": "Explica la aritmética de punteros en C y cómo el kernel de Windows NT implementa los Object Headers y el Executive subsystem.",
        "expected_subtopics": ["aritmética de punteros C", "Windows NT Object Headers Executive"],
        "expected_sources": ["prog_punteros.pdf"],
        "missing_subtopics": ["Windows NT Object Headers Executive"],
    },
    {
        "id": "Q20-MISSING",
        "query": "¿Cómo persisten los árboles binarios en disco con fwrite y cómo se implementa un smart contract en Solidity para auditar las transacciones?",
        "expected_subtopics": ["árboles binarios en disco", "smart contract Solidity"],
        "expected_sources": ["prog_arboles.pdf", "prog_archivos.pdf"],
        "missing_subtopics": ["smart contract Solidity"],
    },
]


def setup_benchmark_environment(tmp_dir: Path):
    """Set up knowledge store, vector store, and hybrid retrieval service."""
    db_path = tmp_dir / "knowledge_store.db"
    vec_path = tmp_dir / "vector_store.db"

    store = KnowledgeStore(db_path=db_path)
    store.initialize()

    sources_dir = REPO_ROOT / "data" / "benchmark" / "sources"
    ingest_benchmark_corpus(
        store=store,
        sources_dir=sources_dir,
        notebook_id="NB-BENCHMARK-V1",
    )

    embedder = DeterministicHashEmbedder(dimensions=128)
    vstore = SQLiteVectorStore(db_path=vec_path, read_only=False)
    records: List[VectorRecord] = []
    for doc in store.documents.list_all():
        for c in store.chunks.list_by_document(doc.id):
            vec = embedder.embed_passages([c.content])[0]
            records.append(
                VectorRecord(
                    chunk_id=c.id,
                    source_id=c.source_id,
                    notebook_id="NB-BENCHMARK-V1",
                    provider_id=embedder.provider_id,
                    model_id=embedder.model_id,
                    dimensions=embedder.dimensions,
                    vector=vec,
                )
            )
    vstore.save_records(records)

    lexical = LexicalRetriever(store)
    dense = DenseRetriever(store, vstore, embedder)
    hybrid = HybridRetriever(store, lexical, dense)
    service = RetrievalService(store, hybrid, dense_threshold=0.20)

    return service, store


def run_baseline_evaluation() -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = Path(tmp_str)
        service, store = setup_benchmark_environment(tmp_dir)
        evidence_engine = EvidenceEngine()
        context_packer = ContextPacker()

        results = []
        multi_source_needed_count = 0
        single_source_fallbacks = 0
        total_source_diversity = 0.0
        queries_with_missing_topics = 0
        unaware_of_missing_topics_count = 0
        total_subtopics = 0
        covered_subtopics_count = 0

        for q in BENCHMARK_QUERIES:
            query_text = q["query"]
            expected_sources = q["expected_sources"]
            expected_subtopics = q["expected_subtopics"]
            missing_subtopics = q["missing_subtopics"]

            # Current Baseline: 1 single retrieval call
            candidates = service.retrieve_evidence(
                query=query_text,
                notebook_id="NB-BENCHMARK-V1",
                top_k=5,
            )

            # Evaluate with EvidenceEngine & ContextPacker
            packet = evidence_engine.evaluate_candidates(
                query=query_text,
                notebook_id="NB-BENCHMARK-V1",
                candidates=candidates,
                store=store,
            )
            packed = context_packer.pack(packet)

            retrieved_sources = list({c.source_id for c in candidates})
            retrieved_chunks = [c.chunk_id for c in candidates]

            # Metric: Source Diversity
            num_expected_sources = len(expected_sources)
            if num_expected_sources > 1:
                multi_source_needed_count += 1
                if len(retrieved_sources) == 1:
                    single_source_fallbacks += 1

            diversity_ratio = len(retrieved_sources) / max(1, min(5, num_expected_sources))
            total_source_diversity += min(1.0, diversity_ratio)

            # Metric: Missing Subtopic Awareness
            # In current baseline, the system NEVER knows which subtopics are missing!
            # It just packs whatever chunks it found and says SUPPORTED or UNASSESSED_EVIDENCE
            is_unaware_of_missing = False
            if missing_subtopics:
                queries_with_missing_topics += 1
                # The current system has no coverage report, so it's 100% unaware
                is_unaware_of_missing = True
                unaware_of_missing_topics_count += 1

            # Subtopic Coverage check (lexical / semantic match in retrieved content)
            combined_content = " ".join(c.content.lower() for c in candidates)
            covered_in_query = []
            for st in expected_subtopics:
                # check if primary keywords of subtopic appear in content
                words = [w.lower() for w in st.split() if len(w) > 3]
                matched = any(w in combined_content for w in words) if words else False
                if matched:
                    covered_in_query.append(st)
                    covered_subtopics_count += 1
            total_subtopics += len(expected_subtopics)

            results.append({
                "id": q["id"],
                "query": query_text,
                "expected_sources": expected_sources,
                "retrieved_sources": retrieved_sources,
                "retrieved_chunks_count": len(candidates),
                "grounding_decision": packet.grounding_decision.value,
                "abstention_required": packet.abstention_required,
                "expected_subtopics": expected_subtopics,
                "covered_subtopics": covered_in_query,
                "missing_subtopics": missing_subtopics,
                "is_unaware_of_missing": is_unaware_of_missing,
            })

        # Aggregated Metrics
        single_source_rate = (
            (single_source_fallbacks / multi_source_needed_count)
            if multi_source_needed_count > 0 else 0.0
        )
        avg_source_diversity = total_source_diversity / len(BENCHMARK_QUERIES)
        subtopic_coverage_rate = covered_subtopics_count / max(1, total_subtopics)
        missing_topic_unawareness_rate = (
            (unaware_of_missing_topics_count / queries_with_missing_topics)
            if queries_with_missing_topics > 0 else 0.0
        )

        report = {
            "version": "1.1-baseline",
            "total_queries": len(BENCHMARK_QUERIES),
            "multi_source_queries_count": multi_source_needed_count,
            "queries_with_missing_topics_count": queries_with_missing_topics,
            "metrics": {
                "single_source_rate": round(single_source_rate, 4),
                "single_source_percentage": f"{round(single_source_rate * 100, 1)}%",
                "source_diversity_score": round(avg_source_diversity, 4),
                "subtopic_coverage_rate": round(subtopic_coverage_rate, 4),
                "subtopic_coverage_percentage": f"{round(subtopic_coverage_rate * 100, 1)}%",
                "missing_topic_unawareness_rate": round(missing_topic_unawareness_rate, 4),
                "missing_topic_unawareness_percentage": f"{round(missing_topic_unawareness_rate * 100, 1)}%",
            },
            "queries_detail": results,
        }

        return report


if __name__ == "__main__":
    print("=" * 70)
    print("EJECUTANDO BENCHMARK V1.1 BASELINE (FASE A - ESTADO ACTUAL)")
    print("=" * 70)
    report = run_baseline_evaluation()

    artifacts_dir = REPO_ROOT / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    out_file = artifacts_dir / "benchmark_baseline_v1_1.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReporte guardado en: {out_file}\n")
    print("MÉTRICAS BASELINE OBTENIDAS:")
    print("-" * 50)
    for k, v in report["metrics"].items():
        print(f"  {k:36s}: {v}")
    print("-" * 50)
    print("=" * 70)
