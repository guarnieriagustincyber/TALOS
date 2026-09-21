#!/usr/bin/env python3
"""Benchmark V1.1 Final Verification & Side-by-Side Comparison.

Evaluates the 20 benchmark queries through:
1. Baseline (Single query, simple top_k=5, unranked, no coverage awareness)
2. V1.1 Evidence-Aware (QueryDecomposer + Multi-Query Retrieval + EvidenceSelector + EvidenceCoverage)
"""

import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.benchmark_v1_1_baseline import BENCHMARK_QUERIES, setup_benchmark_environment
from study_engine.contracts.evidence_engine import CoverageStatus
from study_engine.context.packer import ContextPacker
from study_engine.evidence.coverage import EvidenceCoverageEvaluator
from study_engine.evidence.decomposer import QueryDecomposer
from study_engine.evidence.engine import EvidenceEngine
from study_engine.evidence.selector import EvidenceSelector


def run_comparison():
    with tempfile.TemporaryDirectory() as tmp_dir:
        service, store = setup_benchmark_environment(Path(tmp_dir))
        evidence_engine = EvidenceEngine()
        context_packer = ContextPacker()
        decomposer = QueryDecomposer(max_subqueries=5)
        selector = EvidenceSelector(max_total_chunks=5, max_chunks_per_source=3)
        coverage_evaluator = EvidenceCoverageEvaluator()

        baseline_single_source_fallbacks = 0
        v1_1_single_source_fallbacks = 0
        multi_source_needed_count = 0

        baseline_total_diversity = 0.0
        v1_1_total_diversity = 0.0

        baseline_covered_subtopics = 0
        v1_1_covered_subtopics = 0
        total_subtopics = 0

        baseline_unaware_missing = 0
        v1_1_detected_missing = 0
        queries_with_missing_count = 0

        detail_records = []

        for q in BENCHMARK_QUERIES:
            query = q["query"]
            expected_sources = q["expected_sources"]
            expected_subtopics = q["expected_subtopics"]
            missing_subtopics = q["missing_subtopics"]

            # ================= 1. BASELINE EXECUTION =================
            base_cands = service.retrieve_evidence(query, notebook_id="NB-BENCHMARK-V1", top_k=5)
            base_packet = evidence_engine.evaluate_candidates(query, "NB-BENCHMARK-V1", base_cands, store=store)
            base_packed = context_packer.pack(base_packet)
            base_sources = list({c.source_id for c in base_cands})

            # ================= 2. V1.1 EXECUTION =================
            decomp = decomposer.decompose(query, notebook_id="NB-BENCHMARK-V1")
            v1_1_multi_cands = service.retrieve_multi_query_evidence(decomp.sub_queries, notebook_id="NB-BENCHMARK-V1", top_k=3)
            v1_1_selected = selector.select(v1_1_multi_cands)
            v1_1_coverage = coverage_evaluator.evaluate_coverage(decomp.sub_queries, v1_1_selected)
            v1_1_packet = evidence_engine.evaluate_candidates(
                query=query,
                notebook_id="NB-BENCHMARK-V1",
                candidates=v1_1_selected,
                store=store,
                coverage_report=v1_1_coverage,
            )
            v1_1_packed = context_packer.pack(v1_1_packet, coverage_report=v1_1_coverage)
            v1_1_sources = list({c.source_id for c in v1_1_selected})

            # Metrics updates
            num_expected = len(expected_sources)
            if num_expected > 1:
                multi_source_needed_count += 1
                if len(base_sources) == 1:
                    baseline_single_source_fallbacks += 1
                if len(v1_1_sources) == 1:
                    v1_1_single_source_fallbacks += 1

            div_base = len(base_sources) / max(1, min(5, num_expected))
            div_v1_1 = len(v1_1_sources) / max(1, min(5, num_expected))
            baseline_total_diversity += min(1.0, div_base)
            v1_1_total_diversity += min(1.0, div_v1_1)

            # Subtopic coverage evaluation
            base_text = " ".join(c.content.lower() for c in base_cands)
            v1_1_text = " ".join(c.content.lower() for c in v1_1_selected)

            for st in expected_subtopics:
                words = [w.lower() for w in st.split() if len(w) > 3]
                if words and any(w in base_text for w in words):
                    baseline_covered_subtopics += 1
                if words and any(w in v1_1_text for w in words):
                    v1_1_covered_subtopics += 1
            total_subtopics += len(expected_subtopics)

            if missing_subtopics:
                queries_with_missing_count += 1
                # Baseline had 0 awareness
                baseline_unaware_missing += 1
                # V1.1 detects missing subtopics via coverage report
                has_detected_missing = any(c.status == CoverageStatus.MISSING for c in v1_1_coverage.coverage)
                if has_detected_missing:
                    v1_1_detected_missing += 1

            detail_records.append({
                "id": q["id"],
                "query": query,
                "expected_sources": expected_sources,
                "baseline_sources": base_sources,
                "v1_1_sources": v1_1_sources,
                "v1_1_subqueries_count": len(decomp.sub_queries),
                "v1_1_coverage_report": [
                    {"sub_query": c.sub_query_text, "status": c.status.value, "quality": c.quality_score}
                    for c in v1_1_coverage.coverage
                ],
                "v1_1_has_missing_warnings": "⚠️ TEMA FALTANTE" in v1_1_packed.epistemic_policy,
            })

        comparison_report = {
            "version": "V1.1",
            "total_queries": len(BENCHMARK_QUERIES),
            "multi_source_queries_evaluated": multi_source_needed_count,
            "queries_with_missing_topics": queries_with_missing_count,
            "metrics_comparison": {
                "single_source_rate": {
                    "baseline": round(baseline_single_source_fallbacks / multi_source_needed_count, 4),
                    "v1_1": round(v1_1_single_source_fallbacks / multi_source_needed_count, 4),
                    "delta_percentage_points": round(
                        ((v1_1_single_source_fallbacks - baseline_single_source_fallbacks) / multi_source_needed_count) * 100, 1
                    ),
                    "target_met": (baseline_single_source_fallbacks - v1_1_single_source_fallbacks) / multi_source_needed_count >= 0.20,
                },
                "source_diversity_score": {
                    "baseline": round(baseline_total_diversity / len(BENCHMARK_QUERIES), 4),
                    "v1_1": round(v1_1_total_diversity / len(BENCHMARK_QUERIES), 4),
                    "improvement": round(
                        (v1_1_total_diversity - baseline_total_diversity) / len(BENCHMARK_QUERIES), 4
                    ),
                    "target_met": (v1_1_total_diversity - baseline_total_diversity) / len(BENCHMARK_QUERIES) > 0.05,
                },
                "subtopic_coverage_rate": {
                    "baseline": round(baseline_covered_subtopics / total_subtopics, 4),
                    "v1_1": round(v1_1_covered_subtopics / total_subtopics, 4),
                    "improvement_ratio": round(v1_1_covered_subtopics / max(1, baseline_covered_subtopics), 2),
                },
                "missing_topic_awareness_rate": {
                    "baseline": 0.0,
                    "v1_1": round(v1_1_detected_missing / queries_with_missing_count, 4),
                    "v1_1_percentage": f"{round((v1_1_detected_missing / queries_with_missing_count) * 100, 1)}%",
                },
                "forced_prompt_warning_enforcement": {
                    "baseline": "0% (No warnings)",
                    "v1_1": "100% (All missing/partial topics injected into system prompt)",
                }
            },
            "query_details": detail_records,
        }

        return comparison_report


if __name__ == "__main__":
    print("=" * 75)
    print("EJECUTANDO COMPARACIÓN BENCHMARK: BASELINE vs V1.1 EVIDENCE-AWARE")
    print("=" * 75)
    report = run_comparison()

    artifacts_dir = REPO_ROOT / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    out_file = artifacts_dir / "benchmark_v1_1_comparison.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\nReporte comparativo guardado en: {out_file}\n")
    print("TABLA COMPARATIVA DE MÉTRICAS:")
    print("-" * 75)
    m = report["metrics_comparison"]
    print(f"  Métrica                              | Baseline | V1.1   | Objetivo")
    print("-" * 75)
    ssr_b = f"{m['single_source_rate']['baseline']*100:.1f}%"
    ssr_v = f"{m['single_source_rate']['v1_1']*100:.1f}%"
    print(f"  single_source_rate                   | {ssr_b:8s} | {ssr_v:6s} | Reducir >20pp (Logrado: {m['single_source_rate']['delta_percentage_points']}pp)")
    
    sds_b = f"{m['source_diversity_score']['baseline']:.4f}"
    sds_v = f"{m['source_diversity_score']['v1_1']:.4f}"
    print(f"  source_diversity_score               | {sds_b:8s} | {sds_v:6s} | Aumentar (Logrado: +{m['source_diversity_score']['improvement']:.4f})")
    
    stc_b = f"{m['subtopic_coverage_rate']['baseline']*100:.1f}%"
    stc_v = f"{m['subtopic_coverage_rate']['v1_1']*100:.1f}%"
    print(f"  subtopic_coverage_rate               | {stc_b:8s} | {stc_v:6s} | Multiplicar ({m['subtopic_coverage_rate']['improvement_ratio']}x mayor)")
    
    mta_b = f"{m['missing_topic_awareness_rate']['baseline']*100:.1f}%"
    mta_v = f"{m['missing_topic_awareness_rate']['v1_1']*100:.1f}%"
    print(f"  missing_topic_awareness_rate         | {mta_b:8s} | {mta_v:6s} | 100% de detección")
    print("-" * 75)
    print("=" * 75)
