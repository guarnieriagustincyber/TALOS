"""Métricas de Latencia y Rendimiento Temporal para Fase 4-eval.

Calcula percentiles p50, p90, p95, p99 y tiempos totales.
"""

from typing import Dict, Sequence
import numpy as np


def compute_latency_percentiles(latencies_ms: Sequence[float]) -> Dict[str, float]:
    """Calcula estadísticas descriptivas y percentiles de latencia en milisegundos."""
    if not latencies_ms:
        return {
            "count": 0,
            "mean_ms": 0.0,
            "min_ms": 0.0,
            "p50_ms": 0.0,
            "p90_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "max_ms": 0.0,
        }

    arr = np.array(latencies_ms)
    return {
        "count": int(len(arr)),
        "mean_ms": round(float(np.mean(arr)), 2),
        "min_ms": round(float(np.min(arr)), 2),
        "p50_ms": round(float(np.percentile(arr, 50)), 2),
        "p90_ms": round(float(np.percentile(arr, 90)), 2),
        "p95_ms": round(float(np.percentile(arr, 95)), 2),
        "p99_ms": round(float(np.percentile(arr, 99)), 2),
        "max_ms": round(float(np.max(arr)), 2),
    }
