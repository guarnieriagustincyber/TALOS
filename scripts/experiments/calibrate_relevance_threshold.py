#!/usr/bin/env python3
"""Benchmark de calibración para el relevance gate en RetrievalService (Hito 6).

Ejecuta retrieval sobre el corpus de benchmark con queries legítimas (in-domain)
y queries fuera de dominio (OOD / adversariales), evaluando tanto el embedder de
producción (LocalONNXEmbeddingProvider) como el embedder sintético determinista
(DeterministicHashEmbedder).

Mide la distribución de scores densos (similitud coseno), scores léxicos (BM25)
y scores RRF fusionados. Calcula histogramas, percentiles (p10, p25, p50, p75, p90, p95)
y evalúa la separabilidad empírica para fundamentar el relevance gate.

Genera:
  data/experiments/hito6/relevance_calibration_report.json
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from scripts.ingest_corpus import ingest_benchmark_corpus
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.retrieval.dense import DenseRetriever
from study_engine.retrieval.embedding import (
    DeterministicHashEmbedder,
    EmbeddingProvider,
    LocalONNXEmbeddingProvider,
)
from study_engine.retrieval.hybrid import HybridRetriever
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.retrieval.service import RetrievalService
from study_engine.retrieval.vector_store import SQLiteVectorStore, VectorRecord
from study_engine.storage.knowledge_store import KnowledgeStore


# -----------------------------------------------------------------------------
# BENCHMARK QUERY DATASETS
# -----------------------------------------------------------------------------

LEGITIMATE_QUERIES: List[Tuple[str, str, str]] = [
    ("SEC-04-CONCURR", "¿Qué es una condición de carrera?", "Pregunta conceptual directa"),
    ("SEC-04-CONCURR", "condiciones de carrera", "Keyword canónico"),
    ("SEC-04-CONCURR", "¿Cómo funcionan los mutexes?", "Pregunta de sincronización"),
    ("SEC-04-CONCURR", "¿Qué es un deadlock?", "Pregunta de interbloqueo"),
    ("SEC-04-CONCURR", "comunicación entre procesos y concurrencia", "Frase temática canónica"),
    ("SEC-04-CONCURR", "sección crítica y exclusión mutua", "Concepto nuclear concurrencia"),
    ("SEC-01-C-PTR", "¿Qué es un puntero en C?", "Pregunta conceptual punteros"),
    ("SEC-01-C-PTR", "¿Cómo se declara int *p?", "Sintaxis C punteros"),
    ("SEC-01-C-PTR", "punteros y direcciones de memoria en C", "Frase temática punteros"),
    ("SEC-03-MEM-MGMT", "¿Qué es malloc?", "Función de memoria dinámica"),
    ("SEC-03-MEM-MGMT", "¿Cómo funciona el stack?", "Estructura de memoria stack"),
    ("SEC-03-MEM-MGMT", "gestión de memoria dinámica heap y stack", "Frase temática memoria"),
    ("SEC-02-OS-PROC", "¿Qué es un proceso en sistemas operativos?", "Concepto de proceso"),
    ("SEC-02-OS-PROC", "estados de un proceso y PCB", "Frase temática procesos"),
]

OUT_OF_DOMAIN_QUERIES: List[Tuple[str, str, str]] = [
    ("SEC-04-CONCURR", "¿Cómo explotar vulnerabilidades zero-day en enclaves SGX?", "Hardware security OOD"),
    ("SEC-04-CONCURR", "¿Cuáles son las vulnerabilidades en curvas elípticas Ed25519?", "P1-CURR-04: Criptografía OOD"),
    ("SEC-04-CONCURR", "¿Cómo funciona la paginación multinivel y tablas de páginas invertidas?", "P1-CURR-05: Paginación fuera de rango"),
    ("SEC-04-CONCURR", "¿Cómo explotar enclaves SGX usando algoritmos cuánticos de Shor?", "P1-CURR-06-A: Cuántica SGX OOD"),
    ("SEC-04-CONCURR", "seguridad de procesos en infraestructuras cloud y criptografía asimétrica", "P1-CURR-06-B: Cloud/Crypto OOD"),
    ("SEC-04-CONCURR", "algoritmos cuánticos de factorización", "Computación cuántica pura OOD"),
    ("SEC-04-CONCURR", "criptografía asimétrica y firmas digitales RSA", "Criptografía pura OOD"),
    ("SEC-01-C-PTR", "¿Cómo funciona la paginación invertida?", "Arquitectura SO OOD para punteros"),
    ("SEC-01-C-PTR", "¿Qué es la computación cuántica?", "Computación cuántica OOD"),
    ("SEC-03-MEM-MGMT", "¿Cómo funciona el algoritmo de Shor?", "Algoritmos cuánticos OOD"),
    ("SEC-02-OS-PROC", "redes neuronales convolucionales y visión por computadora", "Machine Learning OOD"),
    ("SEC-02-OS-PROC", "bioinformática y secuenciación de ADN con CRISPR", "Biotecnología OOD"),
]


# -----------------------------------------------------------------------------
# STATISTICAL UTILITIES
# -----------------------------------------------------------------------------

def compute_percentiles(values: List[float]) -> Dict[str, float]:
    """Calculate descriptive statistics and percentiles."""
    if not values:
        return {
            "count": 0,
            "min": 0.0,
            "p10": 0.0,
            "p25": 0.0,
            "p50": 0.0,
            "mean": 0.0,
            "p75": 0.0,
            "p90": 0.0,
            "p95": 0.0,
            "max": 0.0,
            "std": 0.0,
        }
    sorted_vals = sorted(values)
    n = len(sorted_vals)

    def percentile(p: float) -> float:
        k = (n - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        return sorted_vals[int(f)] * (c - k) + sorted_vals[int(c)] * (k - f)

    mean_val = sum(sorted_vals) / n
    variance = sum((x - mean_val) ** 2 for x in sorted_vals) / n
    std_val = math.sqrt(variance)

    return {
        "count": n,
        "min": round(sorted_vals[0], 4),
        "p10": round(percentile(10.0), 4),
        "p25": round(percentile(25.0), 4),
        "p50": round(percentile(50.0), 4),
        "mean": round(mean_val, 4),
        "p75": round(percentile(75.0), 4),
        "p90": round(percentile(90.0), 4),
        "p95": round(percentile(95.0), 4),
        "max": round(sorted_vals[-1], 4),
        "std": round(std_val, 4),
    }


def make_ascii_histogram(
    legit_vals: List[float],
    ood_vals: List[float],
    bins: int = 10,
    val_range: Optional[Tuple[float, float]] = None,
) -> str:
    """Generate an aligned ASCII double histogram comparing two distributions."""
    if not legit_vals and not ood_vals:
        return "No data available."

    all_vals = legit_vals + ood_vals
    min_v = val_range[0] if val_range else min(all_vals)
    max_v = val_range[1] if val_range else max(all_vals)
    if min_v == max_v:
        max_v += 0.01

    step = (max_v - min_v) / bins
    legit_counts = [0] * bins
    ood_counts = [0] * bins

    for v in legit_vals:
        idx = min(int((v - min_v) / step), bins - 1)
        legit_counts[idx] += 1

    for v in ood_vals:
        idx = min(int((v - min_v) / step), bins - 1)
        ood_counts[idx] += 1

    max_count = max(max(legit_counts, default=0), max(ood_counts, default=0), 1)
    bar_width = 25

    lines = []
    lines.append(f"{'Rango':<18} | {'LEGÍTIMAS':<26} | {'FUERA DE DOMINIO':<26}")
    lines.append("-" * 75)
    for i in range(bins):
        low = min_v + i * step
        high = low + step
        l_cnt = legit_counts[i]
        o_cnt = ood_counts[i]
        l_bar = "#" * int((l_cnt / max_count) * bar_width)
        o_bar = "=" * int((o_cnt / max_count) * bar_width)
        lines.append(
            f"[{low:.3f} - {high:.3f}] | {l_bar:<25} ({l_cnt:>2}) | {o_bar:<25} ({o_cnt:>2})"
        )
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# CALIBRATION BENCHMARK RUNNER
# -----------------------------------------------------------------------------

class RelevanceCalibrationBenchmark:
    """Runs systematic retrieval benchmark on legitimate vs OOD queries."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.curriculum_dir = repo_root / "data" / "curriculum"
        self.sources_dir = repo_root / "data" / "benchmark" / "sources"

    def run_benchmark_for_provider(
        self,
        provider_name: str,
        provider: EmbeddingProvider,
    ) -> Dict[str, Any]:
        """Execute benchmark for a specific embedding provider."""
        print(f"\n{'='*75}")
        print(f"📊 EJECUTANDO BENCHMARK DE CALIBRACIÓN: {provider_name.upper()}")
        print(f"   Provider ID: {provider.provider_id} | Model: {provider.model_id} | Dims: {provider.dimensions}")
        print(f"{'='*75}")

        with tempfile.TemporaryDirectory(prefix=f"calib_{provider_name}_") as tmpdir:
            work_path = Path(tmpdir)
            db_path = work_path / "kstore.db"
            vec_path = work_path / "vstore.db"

            # 1. Ingestion of benchmark corpus into isolated KnowledgeStore
            store = KnowledgeStore(db_path=db_path)
            store.initialize()
            ingest_benchmark_corpus(
                store=store,
                sources_dir=self.sources_dir,
                notebook_id="NB-CYBERSECURITY-V1",
            )

            # 2. Vector indexing for all ingested documents
            vstore = SQLiteVectorStore(db_path=vec_path)
            docs = store.list_documents()
            all_chunks = []
            for doc in docs:
                all_chunks.extend(store.list_chunks_by_document(doc.id))

            print(f"[*] Chunks indexados en KnowledgeStore: {len(all_chunks)} chunks de {len(docs)} documentos")

            # Batch embed chunks
            records: List[VectorRecord] = []
            batch_size = 32
            for i in range(0, len(all_chunks), batch_size):
                batch = all_chunks[i : i + batch_size]
                texts = [c.content for c in batch]
                vectors = provider.embed_passages(texts)
                for c, vec in zip(batch, vectors):
                    records.append(
                        VectorRecord(
                            chunk_id=c.id,
                            source_id=c.source_id,
                            notebook_id="NB-CYBERSECURITY-V1",
                            provider_id=provider.provider_id,
                            model_id=provider.model_id,
                            dimensions=provider.dimensions,
                            vector=vec,
                        )
                    )
            vstore.save_records(records)
            print(f"[*] Vectores indexados en SQLiteVectorStore: {len(records)}")

            # 3. Setup Epistemic Retrieval Pipeline
            lexical = LexicalRetriever(store)
            dense = DenseRetriever(store, vstore, provider)
            hybrid = HybridRetriever(store, lexical, dense)
            retrieval_service = RetrievalService(store, hybrid)
            registry = CurriculumRegistry(root_dir=self.curriculum_dir)

            # 4. Execute Retrieval for Legitimate Queries
            print("\n--- Ejecutando Queries Legítimas (In-Domain) ---")
            legit_results: List[Dict[str, Any]] = []
            legit_dense_scores_all: List[float] = []
            legit_dense_scores_top1: List[float] = []
            legit_lexical_scores_all: List[float] = []
            legit_fused_scores_all: List[float] = []

            for node_id, query, note in LEGITIMATE_QUERIES:
                cands = retrieval_service.retrieve_evidence(
                    query=query,
                    node_id=node_id,
                    registry=registry,
                    matrix_id="alignment/cybersecurity_v1_alignment.json",
                    top_k=5,
                )
                cand_summaries = []
                for cand in cands:
                    d_score = float(cand.dense_score or 0.0)
                    l_score = float(cand.lexical_score or 0.0)
                    f_score = float(cand.score)
                    legit_dense_scores_all.append(d_score)
                    legit_lexical_scores_all.append(l_score)
                    legit_fused_scores_all.append(f_score)
                    cand_summaries.append(
                        {
                            "chunk_id": cand.chunk_id,
                            "document_id": cand.document_id,
                            "page_start": cand.page_start,
                            "dense_score": round(d_score, 4),
                            "lexical_score": round(l_score, 4),
                            "fused_score": round(f_score, 4),
                            "in_lexical": cand.metadata.get("in_lexical", False),
                            "in_dense": cand.metadata.get("in_dense", False),
                        }
                    )
                top1_d = cand_summaries[0]["dense_score"] if cand_summaries else 0.0
                top1_l = cand_summaries[0]["lexical_score"] if cand_summaries else 0.0
                if cand_summaries:
                    legit_dense_scores_top1.append(top1_d)

                legit_results.append(
                    {
                        "node_id": node_id,
                        "query": query,
                        "note": note,
                        "candidates_retrieved": len(cand_summaries),
                        "top1_dense_score": top1_d,
                        "top1_lexical_score": top1_l,
                        "candidates": cand_summaries,
                    }
                )
                top1_str = f"dense={top1_d:.4f} lex={top1_l:.4f}" if cand_summaries else "EMPTY"
                print(f"  [LEGIT] {node_id:<15} \"{query[:32]:<32}\" -> {len(cand_summaries)} cands ({top1_str})")

            # 5. Execute Retrieval for Out-of-Domain Queries
            print("\n--- Ejecutando Queries Fuera de Dominio (OOD / Adversariales) ---")
            ood_results: List[Dict[str, Any]] = []
            ood_dense_scores_all: List[float] = []
            ood_dense_scores_top1: List[float] = []
            ood_lexical_scores_all: List[float] = []
            ood_fused_scores_all: List[float] = []

            for node_id, query, note in OUT_OF_DOMAIN_QUERIES:
                cands = retrieval_service.retrieve_evidence(
                    query=query,
                    node_id=node_id,
                    registry=registry,
                    matrix_id="alignment/cybersecurity_v1_alignment.json",
                    top_k=5,
                )
                cand_summaries = []
                for cand in cands:
                    d_score = float(cand.dense_score or 0.0)
                    l_score = float(cand.lexical_score or 0.0)
                    f_score = float(cand.score)
                    ood_dense_scores_all.append(d_score)
                    ood_lexical_scores_all.append(l_score)
                    ood_fused_scores_all.append(f_score)
                    cand_summaries.append(
                        {
                            "chunk_id": cand.chunk_id,
                            "document_id": cand.document_id,
                            "page_start": cand.page_start,
                            "dense_score": round(d_score, 4),
                            "lexical_score": round(l_score, 4),
                            "fused_score": round(f_score, 4),
                            "in_lexical": cand.metadata.get("in_lexical", False),
                            "in_dense": cand.metadata.get("in_dense", False),
                        }
                    )
                top1_d = cand_summaries[0]["dense_score"] if cand_summaries else 0.0
                top1_l = cand_summaries[0]["lexical_score"] if cand_summaries else 0.0
                if cand_summaries:
                    ood_dense_scores_top1.append(top1_d)

                ood_results.append(
                    {
                        "node_id": node_id,
                        "query": query,
                        "note": note,
                        "candidates_retrieved": len(cand_summaries),
                        "top1_dense_score": top1_d,
                        "top1_lexical_score": top1_l,
                        "candidates": cand_summaries,
                    }
                )
                top1_str = f"dense={top1_d:.4f} lex={top1_l:.4f}" if cand_summaries else "EMPTY"
                print(f"  [OOD  ] {node_id:<15} \"{query[:32]:<32}\" -> {len(cand_summaries)} cands ({top1_str})")

            # 6. Statistical Analysis
            legit_dense_stats_all = compute_percentiles(legit_dense_scores_all)
            legit_dense_stats_top1 = compute_percentiles(legit_dense_scores_top1)
            ood_dense_stats_all = compute_percentiles(ood_dense_scores_all)
            ood_dense_stats_top1 = compute_percentiles(ood_dense_scores_top1)

            legit_lex_stats_all = compute_percentiles(legit_lexical_scores_all)
            ood_lex_stats_all = compute_percentiles(ood_lexical_scores_all)

            legit_fused_stats_all = compute_percentiles(legit_fused_scores_all)
            ood_fused_stats_all = compute_percentiles(ood_fused_scores_all)

            # Lexical coverage metrics
            legit_with_lex = sum(1 for s in legit_lexical_scores_all if s > 0.0)
            ood_with_lex = sum(1 for s in ood_lexical_scores_all if s > 0.0)

            # Threshold sweep for pure dense cosine
            min_score = min(legit_dense_scores_all + ood_dense_scores_all, default=0.0)
            max_score = max(legit_dense_scores_all + ood_dense_scores_all, default=1.0)
            sweep_steps = 100
            step_size = (max_score - min_score) / sweep_steps if max_score > min_score else 0.01

            best_pure_threshold = 0.0
            best_pure_f1 = -1.0
            best_pure_fpr = 1.0
            best_pure_fnr = 1.0
            separation_achieved_pure = False

            sweep_points: List[Dict[str, Any]] = []
            for step_idx in range(sweep_steps + 1):
                theta = min_score + step_idx * step_size
                tp = sum(1 for s in legit_dense_scores_all if s >= theta)
                fn = sum(1 for s in legit_dense_scores_all if s < theta)
                fp = sum(1 for s in ood_dense_scores_all if s >= theta)
                tn = sum(1 for s in ood_dense_scores_all if s < theta)

                tpr = tp / len(legit_dense_scores_all) if legit_dense_scores_all else 0.0
                fpr = fp / len(ood_dense_scores_all) if ood_dense_scores_all else 0.0
                fnr = fn / len(legit_dense_scores_all) if legit_dense_scores_all else 0.0
                prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                rec = tpr
                f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

                sweep_points.append(
                    {
                        "threshold": round(theta, 4),
                        "tpr": round(tpr, 4),
                        "fpr": round(fpr, 4),
                        "fnr": round(fnr, 4),
                        "f1": round(f1, 4),
                    }
                )

                if f1 > best_pure_f1:
                    best_pure_f1 = f1
                    best_pure_threshold = round(theta, 4)
                    best_pure_fpr = round(fpr, 4)
                    best_pure_fnr = round(fnr, 4)

                if fnr <= 0.05 and fpr <= 0.05:
                    separation_achieved_pure = True

            # Compound Gate Sweep:
            # Rule: Admit candidate iff (cand has lexical match) OR (dense_score >= theta_dense_high)
            compound_sweep_points: List[Dict[str, Any]] = []
            best_compound_threshold = 0.0
            best_compound_f1 = -1.0
            best_compound_fpr = 1.0
            best_compound_fnr = 1.0
            separation_achieved_compound = False

            legit_pairs = [
                (c["dense_score"], c["lexical_score"])
                for r in legit_results
                for c in r["candidates"]
            ]
            ood_pairs = [
                (c["dense_score"], c["lexical_score"])
                for r in ood_results
                for c in r["candidates"]
            ]

            for step_idx in range(sweep_steps + 1):
                theta_high = min_score + step_idx * step_size
                tp = sum(1 for (d, l) in legit_pairs if l > 0.0 or d >= theta_high)
                fn = sum(1 for (d, l) in legit_pairs if not (l > 0.0 or d >= theta_high))
                fp = sum(1 for (d, l) in ood_pairs if l > 0.0 or d >= theta_high)
                tn = sum(1 for (d, l) in ood_pairs if not (l > 0.0 or d >= theta_high))

                tpr = tp / len(legit_pairs) if legit_pairs else 0.0
                fpr = fp / len(ood_pairs) if ood_pairs else 0.0
                fnr = fn / len(legit_pairs) if legit_pairs else 0.0
                prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                rec = tpr
                f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

                compound_sweep_points.append(
                    {
                        "threshold_high": round(theta_high, 4),
                        "tpr": round(tpr, 4),
                        "fpr": round(fpr, 4),
                        "fnr": round(fnr, 4),
                        "f1": round(f1, 4),
                    }
                )

                if f1 > best_compound_f1:
                    best_compound_f1 = f1
                    best_compound_threshold = round(theta_high, 4)
                    best_compound_fpr = round(fpr, 4)
                    best_compound_fnr = round(fnr, 4)

                if fnr <= 0.05 and fpr <= 0.05:
                    separation_achieved_compound = True

            # ASCII Histograms
            hist_dense_all = make_ascii_histogram(
                legit_dense_scores_all,
                ood_dense_scores_all,
                bins=10,
                val_range=(min_score, max_score),
            )
            hist_dense_top1 = make_ascii_histogram(
                legit_dense_scores_top1,
                ood_dense_scores_top1,
                bins=10,
            )

            report_data: Dict[str, Any] = {
                "provider_id": provider.provider_id,
                "model_id": provider.model_id,
                "dimensions": provider.dimensions,
                "dataset_summary": {
                    "legitimate_queries_count": len(LEGITIMATE_QUERIES),
                    "ood_queries_count": len(OUT_OF_DOMAIN_QUERIES),
                    "legitimate_candidates_retrieved": len(legit_dense_scores_all),
                    "ood_candidates_retrieved": len(ood_dense_scores_all),
                    "legitimate_lexical_hits_count": legit_with_lex,
                    "legitimate_lexical_hit_rate": round(
                        legit_with_lex / len(legit_dense_scores_all), 4
                    )
                    if legit_dense_scores_all
                    else 0.0,
                    "ood_lexical_hits_count": ood_with_lex,
                    "ood_lexical_hit_rate": round(
                        ood_with_lex / len(ood_dense_scores_all), 4
                    )
                    if ood_dense_scores_all
                    else 0.0,
                },
                "distributions": {
                    "dense_scores_all_candidates": {
                        "legitimate": legit_dense_stats_all,
                        "out_of_domain": ood_dense_stats_all,
                    },
                    "dense_scores_top1": {
                        "legitimate": legit_dense_stats_top1,
                        "out_of_domain": ood_dense_stats_top1,
                    },
                    "lexical_scores_all": {
                        "legitimate": legit_lex_stats_all,
                        "out_of_domain": ood_lex_stats_all,
                    },
                    "fused_scores_all": {
                        "legitimate": legit_fused_stats_all,
                        "out_of_domain": ood_fused_stats_all,
                    },
                },
                "pure_dense_separability": {
                    "separation_criteria_met": separation_achieved_pure,
                    "best_threshold": best_pure_threshold,
                    "best_f1": best_pure_f1,
                    "best_fpr": best_pure_fpr,
                    "best_fnr": best_pure_fnr,
                },
                "compound_gate_separability": {
                    "separation_criteria_met": separation_achieved_compound,
                    "best_dense_threshold_no_lexical": best_compound_threshold,
                    "best_f1": best_compound_f1,
                    "best_fpr": best_compound_fpr,
                    "best_fnr": best_compound_fnr,
                },
                "ascii_histogram_dense_all": hist_dense_all,
                "ascii_histogram_dense_top1": hist_dense_top1,
                "raw_queries_legitimate": legit_results,
                "raw_queries_ood": ood_results,
            }

            return report_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Relevance Gate Calibration Benchmark")
    parser.add_argument(
        "--embedder",
        choices=["all", "onnx", "hash"],
        default="all",
        help="Embedder provider to benchmark (default: all)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "data" / "experiments" / "hito6" / "relevance_calibration_report.json",
        help="Path to output JSON calibration report",
    )
    args = parser.parse_args()

    benchmark = RelevanceCalibrationBenchmark(repo_root=REPO_ROOT)
    final_report: Dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark_title": "Hito 6 Relevance Gate Calibration Benchmark",
        "providers": {},
    }

    providers_to_test: List[Tuple[str, EmbeddingProvider]] = []
    if args.embedder in ("all", "onnx"):
        try:
            providers_to_test.append(("local_onnx", LocalONNXEmbeddingProvider()))
        except Exception as e:
            print(f"[!] Warning: Failed to load LocalONNXEmbeddingProvider: {e}")

    if args.embedder in ("all", "hash"):
        providers_to_test.append(("deterministic_hash", DeterministicHashEmbedder(dimensions=128)))

    for name, prov in providers_to_test:
        report = benchmark.run_benchmark_for_provider(name, prov)
        final_report["providers"][name] = report

    # Persist JSON report
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    print(f"\n[+] Reporte completo guardado en: {args.output}")

    # Print summary evaluation
    print("\n" + "=" * 75)
    print("📈 SÍNTESIS DE CALIBRACIÓN Y SEPARABILIDAD EMPÍRICA")
    print("=" * 75)
    for name, p_data in final_report["providers"].items():
        print(f"\nPROVEEDOR: {name.upper()} ({p_data['model_id']})")
        d_all = p_data["distributions"]["dense_scores_all_candidates"]
        print(f"  * LEGÍTIMO Dense:   min={d_all['legitimate']['min']} p25={d_all['legitimate']['p25']} p50={d_all['legitimate']['p50']} p75={d_all['legitimate']['p75']} max={d_all['legitimate']['max']}")
        print(f"  * OOD Dense:        min={d_all['out_of_domain']['min']} p25={d_all['out_of_domain']['p25']} p50={d_all['out_of_domain']['p50']} p75={d_all['out_of_domain']['p75']} max={d_all['out_of_domain']['max']}")

        pure_sep = p_data["pure_dense_separability"]
        print(f"  * Separación Pura Densa (FPR<0.05 y FNR<0.05): {'CUMPLE' if pure_sep['separation_criteria_met'] else 'NO CUMPLE (OVERLAP)'}")
        print(f"    - Mejor Threshold Denso Puro: {pure_sep['best_threshold']} (F1={pure_sep['best_f1']}, FPR={pure_sep['best_fpr']}, FNR={pure_sep['best_fnr']})")

        comp_sep = p_data["compound_gate_separability"]
        print(f"  * Separación Compuerta Compuesta (Léxico + Denso Alto): {'CUMPLE' if comp_sep['separation_criteria_met'] else 'NO CUMPLE'}")
        print(f"    - Mejor Threshold Denso Sin Soporte Léxico: {comp_sep['best_dense_threshold_no_lexical']} (F1={comp_sep['best_f1']}, FPR={comp_sep['best_fpr']}, FNR={comp_sep['best_fnr']})")

        print("\n  HISTOGRAMA ASCII (Scores Densos Todos los Candidatos):")
        for line in p_data["ascii_histogram_dense_all"].splitlines():
            print("   ", line)


if __name__ == "__main__":
    main()
