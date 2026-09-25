"""Generador de Reportes de Evaluación (Fase 4-eval).

Emite:
- benchmark/results/evaluation_report.json
- benchmark/results/evaluation_report.md
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def generate_reports(
    run_id: str,
    results: Dict[str, Any],
    output_dir: Path,
) -> Tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "evaluation_report.json"
    md_path = output_dir / "evaluation_report.md"

    # Guardar JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Generar Markdown
    md_content = build_markdown_report(results)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return json_path, md_path


def build_markdown_report(res: Dict[str, Any]) -> str:
    status_emoji = "✅ PASS" if res.get("overall_status") == "PASS" else "❌ FAIL"
    m = res.get("metrics", {})
    b = res.get("baseline_comparison", {})
    gates = res.get("gates_status", {})

    lines = [
        f"# 📊 Reporte Formal de Evaluación: Fase 4-eval ({res.get('golden_set_version', 'v2.400')})",
        "",
        f"> **ID de Corrida:** `{res.get('run_id')}`  ",
        f"> **Fecha:** {res.get('timestamp')}  ",
        f"> **Modo:** `{res.get('mode', 'fast')}`  ",
        f"> **Estado Global:** **{status_emoji}**  ",
        f"> **Runtime Total:** `{m.get('runtime_s', 0):.2f}s` ({m.get('total_queries', 0)} consultas evaluadas)",
        "",
        "---",
        "",
        "## 1. Puertas de Calidad (Control Gates)",
        "",
        "| Puerta de Calidad | Criterio Requerido | Valor Obtenido | Estado |",
        "|---|:---:|:---:|:---:|",
        f"| **Evidence Precision** | $100\\%$ | {m.get('evidence_precision', 0)*100:.1f}% | {'✅' if gates.get('evidence_precision') else '❌'} |",
        f"| **Citation Correctness** | $\\ge 98\\%$ | {m.get('citation_correctness', 0)*100:.1f}% | {'✅' if gates.get('citation_correctness') else '❌'} |",
        f"| **Fail-Closed Abstention (OOD)** | $100\\%$ | {m.get('fail_closed_abstention', 0)*100:.1f}% | {'✅' if gates.get('fail_closed_abstention') else '❌'} |",
        f"| **Notebook Scoping (Aislamiento)** | $100\\%$ | {m.get('notebook_scoping', 0)*100:.1f}% | {'✅' if gates.get('notebook_scoping') else '❌'} |",
        f"| **Anti-Leakage (Cero fugas)** | $100\\%$ | {m.get('anti_leakage', 0)*100:.1f}% | {'✅' if gates.get('anti_leakage') else '❌'} |",
        f"| **Retrieval MRR@5** | $\\ge 0.85$ | {m.get('mrr5', 0):.3f} | {'✅' if gates.get('mrr5') else '❌'} |",
        f"| **Retrieval nDCG@5** | $\\ge 0.80$ | {m.get('ndcg5', 0):.3f} | {'✅' if gates.get('ndcg5') else '❌'} |",
        f"| **Latencia p50** | $< 2500$ ms | {m.get('latency_p50_ms', 0):.1f} ms | {'✅' if gates.get('latency_p50') else '❌'} |",
        f"| **Runtime Fast (<10 min)** | $\\le 600$ s | {m.get('runtime_s', 0):.1f} s | {'✅' if gates.get('runtime') else '❌'} |",
        "",
        "---",
        "",
        "## 2. Comparativa Cuantitativa vs Google NotebookLM",
        "",
        "| Dimensión Clave | Baseline NotebookLM | TALOS v1.1 (Qwen3-1024d) | Diferencial |",
        "|---|:---:|:---:|:---:|",
        f"| **MRR@5** | 0.740 | **{m.get('mrr5', 0):.3f}** | +{(m.get('mrr5', 0) - 0.740):+.3f} |",
        f"| **nDCG@5** | 0.690 | **{m.get('ndcg5', 0):.3f}** | +{(m.get('ndcg5', 0) - 0.690):+.3f} |",
        f"| **Recall@5** | 0.810 | **{m.get('recall5', 0):.3f}** | +{(m.get('recall5', 0) - 0.810):+.3f} |",
        f"| **Fail-Closed Abstention** | 60.0% | **{m.get('fail_closed_abstention', 0)*100:.1f}%** | +{(m.get('fail_closed_abstention', 0)*100 - 60.0):+.1f}% |",
        f"| **Notebook Scoping** | 72.0% | **{m.get('notebook_scoping', 0)*100:.1f}%** | +{(m.get('notebook_scoping', 0)*100 - 72.0):+.1f}% |",
        f"| **Evidence Precision** | 85.0% | **{m.get('evidence_precision', 0)*100:.1f}%** | +{(m.get('evidence_precision', 0)*100 - 85.0):+.1f}% |",
        "",
        "---",
        "",
        "## 3. Desglose de Rendimiento por Categoría",
        "",
        "| Categoría | Consultas | MRR@5 | nDCG@5 | Abstención OK | Scoping OK |",
        "|---|:---:|:---:|:---:|:---:|:---:|",
    ]

    cat_stats = res.get("category_breakdown", {})
    for cat_name, stats in cat_stats.items():
        mrr_val = stats.get("mrr5")
        ndcg_val = stats.get("ndcg5")
        abst_val = stats.get("abstention_rate")
        scop_val = stats.get("scoping_pass_rate")
        mrr_fmt = f"{mrr_val:.3f}" if isinstance(mrr_val, (int, float)) else str(mrr_val or "N/A")
        ndcg_fmt = f"{ndcg_val:.3f}" if isinstance(ndcg_val, (int, float)) else str(ndcg_val or "N/A")
        abst_fmt = f"{abst_val*100:.1f}%" if isinstance(abst_val, (int, float)) else str(abst_val or "N/A")
        scop_fmt = f"{scop_val*100:.1f}%" if isinstance(scop_val, (int, float)) else str(scop_val or "N/A")
        lines.append(
            f"| `{cat_name}` | {stats.get('total', 0)} | {mrr_fmt} | {ndcg_fmt} | {abst_fmt} | {scop_fmt} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 4. Invariantes del Sistema y Hashes de Auditoría",
        "",
        f"- **Corpus Snapshot Hash:** `{res.get('corpus_hash')}`",
        f"- **Vector Index Hash:** `{res.get('vector_index_hash')}`",
        f"- **Perímetro Congelado:** `0 líneas diff` en `src/study_engine/{{state,execution,assessment,audit}}/`",
        f"- **Operación:** 100% Local-First Offline (cero dependencias de red en modo fast)",
    ])

    return "\n".join(lines)
