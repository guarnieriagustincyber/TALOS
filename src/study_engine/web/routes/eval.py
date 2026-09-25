"""Evaluation and Benchmark Endpoints (Fase 4-eval).

Exposes read-only metrics, benchmark reports, and invariant gates to the UI/Dashboard.
Strictly read-only: does NOT mutate student state, BKT parameters, or knowledge stores.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/eval", tags=["Evaluation"])

REPO_ROOT = Path(__file__).resolve().parents[4]
RESULTS_DIR = REPO_ROOT / "benchmark/results"


@router.get("/summary")
def get_latest_eval_summary() -> Dict[str, Any]:
    """Return the latest Fase 4 evaluation summary and gate statuses."""
    latest_file = RESULTS_DIR / "latest_summary.json"
    if not latest_file.exists():
        # Fallback to evaluation_report.json if available
        fallback_file = RESULTS_DIR / "evaluation_report.json"
        if fallback_file.exists():
            try:
                with open(fallback_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Error reading evaluation report fallback: %s", e)
        return {
            "status": "NO_RUNS_RECORDED",
            "message": "No se encontraron ejecuciones de Fase 4-eval aún.",
            "metrics": {},
            "gates": {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Error reading latest_summary.json: %s", e)
        raise HTTPException(status_code=500, detail=f"Error leyendo resumen de evaluación: {e}")


@router.get("/runs")
def list_eval_runs() -> List[Dict[str, Any]]:
    """List available historical benchmark runs."""
    if not RESULTS_DIR.exists():
        return []

    runs = []
    for f in RESULTS_DIR.glob("fase4-eval-*.json"):
        try:
            with open(f, "r", encoding="utf-8") as rf:
                data = json.load(rf)
                runs.append({
                    "run_id": data.get("run_id", f.stem),
                    "timestamp": data.get("timestamp_utc", ""),
                    "mode": data.get("mode", "fast"),
                    "mrr5": data.get("retrieval", {}).get("mrr5", 0.0),
                    "ndcg5": data.get("retrieval", {}).get("ndcg5", 0.0),
                    "ood_abstention_rate": data.get("epistemic", {}).get("ood_abstention_rate", 1.0),
                    "scoping_pass_rate": data.get("epistemic", {}).get("scoping_pass_rate", 1.0),
                    "gate_pass": data.get("gates", {}).get("all_gates_passed", False),
                })
        except Exception as err:
            logger.debug("Error parsing run file %s: %s", f, err)

    runs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return runs


@router.get("/report/{run_id}")
def get_run_report(run_id: str) -> Dict[str, Any]:
    """Retrieve full JSON and Markdown report for a specific run ID."""
    clean_id = Path(run_id).name
    json_path = RESULTS_DIR / f"{clean_id}.json"
    md_path = RESULTS_DIR / f"{clean_id}.md"

    if not json_path.exists():
        raise HTTPException(status_code=404, detail=f"Ejecución '{clean_id}' no encontrada.")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        md_text = ""
        if md_path.exists():
            with open(md_path, "r", encoding="utf-8") as mf:
                md_text = mf.read()

        return {
            "run_id": clean_id,
            "data": data,
            "markdown_report": md_text,
        }
    except Exception as e:
        logger.error("Error reading run report for %s: %s", clean_id, e)
        raise HTTPException(status_code=500, detail=f"Error cargando informe de ejecución: {e}")
