#!/usr/bin/env python
"""Golden Set v1 runner — mide el sistema EN VIVO contra el endpoint de chat.

Requiere backend arriba (uvicorn :8000) con provider real (Gemini). Corre cada
query del golden set vía SSE y contrasta contra las expectativas del caso:

- abstención (OOD), kc_id/fallback (K2/K1), groundedness (citaciones >= min),
- first_token_ms y latencia total.

Escribe reports/golden_set_v1_<ts>.json (+ .md resumen) y devuelve exit code
0 si TODAS las expectativas se cumplen, 1 en caso contrario.

Uso:
    .venv/bin/python scripts/run_golden_set.py [--base-url http://localhost:8000]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_SET_PATH = REPO_ROOT / "data" / "eval" / "golden_set_v1.json"
REPORTS_DIR = REPO_ROOT / "reports"

# Primer request tras boot paga warmup residual; margen sobre el objetivo 3s.
FIRST_TOKEN_BUDGET_MS = 3000


def run_query(
    base_url: str,
    notebook_id: str,
    query: str,
    timeout_s: float = 120.0,
    scope_override: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Ejecuta una query SSE y extrae métricas del stream."""
    t0 = time.perf_counter()
    first_token_ms: Optional[int] = None
    abstained = False
    bkt_context = None
    n_citations = 0
    invalid_citations: List[str] = []
    final_event = None
    saw_error = False

    payload: Dict[str, Any] = {"query": query, "notebook_id": notebook_id, "requested_phase": "conceptual"}
    # K5 y casos cross-scope: permitir override explícito desde el golden set
    if scope_override:
        payload = {
            "query": query,
            "requested_phase": "conceptual",
            "scope_type": scope_override.get("scope_type"),
            "scope_id": scope_override.get("scope_id"),
        }

    with httpx.stream(
        "POST",
        f"{base_url}/api/chat/query",
        json=payload,
        timeout=timeout_s,
    ) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line.startswith("data: "):
                continue
            try:
                ev = json.loads(line[6:])
            except json.JSONDecodeError:
                continue
            et = ev.get("event_type")
            payload = ev.get("payload") or {}
            if et == "phase_token" and first_token_ms is None:
                first_token_ms = round((time.perf_counter() - t0) * 1000)
            elif et == "evidence_manifest":
                n_citations = len(payload.get("citations") or [])
            elif et == "phase_complete":
                bkt_context = payload.get("bkt_context")
            elif et == "abstention":
                abstained = True
            elif et == "citation_audit":
                invalid_citations = payload.get("invalid_citations") or []
            elif et == "error":
                saw_error = True
            final_event = et

    return {
        "first_token_ms": first_token_ms,
        "total_ms": round((time.perf_counter() - t0) * 1000),
        "abstained": abstained,
        "bkt_context": bkt_context,
        "n_citations": n_citations,
        "invalid_citations": invalid_citations,
        "final_event": final_event,
        "saw_error": saw_error,
    }


def evaluate(entry: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    """Contrast una medición contra la expectativa del golden set."""
    failures: List[str] = []

    if result["saw_error"]:
        failures.append("evento 'error' en el stream")

    if result["abstained"] != entry["expected_abstain"]:
        failures.append(
            f"abstained={result['abstained']} != esperado {entry['expected_abstain']}"
        )

    if not entry["expected_abstain"]:
        if result["final_event"] != "phase_complete":
            failures.append(f"final_event={result['final_event']} != phase_complete")
        if result["n_citations"] < entry["min_citations"]:
            failures.append(f"citas {result['n_citations']} < min {entry['min_citations']}")
        bkt = result["bkt_context"] or {}
        expected_fallback = entry.get("expected_fallback")
        if expected_fallback is not None and bkt.get("fallback") != expected_fallback:
            failures.append(f"bkt fallback={bkt.get('fallback')} != esperado {expected_fallback}")
        expected_kc = entry.get("expected_kc_id")
        if expected_kc is not None and bkt.get("kc_id") != expected_kc:
            failures.append(f"kc_id={bkt.get('kc_id')} != esperado {expected_kc}")
    else:
        if result["n_citations"] != 0:
            failures.append(f"OOD con {result['n_citations']} citas (debería ser 0)")
        if result["final_event"] != "abstention":
            failures.append(f"final_event={result['final_event']} != abstention")

    return {"pass": not failures, "failures": failures}


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(rows)
    passed = sum(1 for r in rows if r["pass"])
    by_case: Dict[str, Dict[str, int]] = {}
    for r in rows:
        c = r["case"]
        by_case.setdefault(c, {"n": 0, "pass": 0})
        by_case[c]["n"] += 1
        by_case[c]["pass"] += int(r["pass"])

    lat = sorted(r["result"]["first_token_ms"] or 0 for r in rows if not r["result"]["abstained"])
    kc_rows = [r for r in rows if r["case"] == "K2"]
    kc_hits = sum(1 for r in kc_rows if r["result"].get("bkt_context") and r["result"]["bkt_context"].get("kc_id") == r["expected_kc_id"] if r["expected_kc_id"])

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "by_case": by_case,
        "kc_accuracy": (kc_hits / max(sum(1 for r in kc_rows if r["expected_kc_id"]), 1)),
        "first_token_p50_ms": lat[len(lat) // 2] if lat else None,
        "first_token_max_ms": lat[-1] if lat else None,
        "first_token_within_budget": all(v <= FIRST_TOKEN_BUDGET_MS for v in lat) if lat else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Golden Set v1 runner (requiere backend vivo)")
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--golden-set", default=str(GOLDEN_SET_PATH))
    args = ap.parse_args()

    gs = json.loads(Path(args.golden_set).read_text(encoding="utf-8"))
    notebook_id = gs["notebook_id"]
    rows: List[Dict[str, Any]] = []

    print(f"Golden Set v1 — {len(gs['queries'])} queries contra {args.base_url} (notebook {notebook_id})")
    for entry in gs["queries"]:
        t_start = time.perf_counter()
        try:
            result = run_query(
                args.base_url,
                entry.get("notebook_id") or notebook_id,
                entry["query"],
                scope_override=entry.get("scope"),
            )
        except Exception as exc:
            result = {"saw_error": True, "abstained": None, "bkt_context": None,
                      "n_citations": -1, "final_event": f"HARNESS:{type(exc).__name__}",
                      "invalid_citations": [], "first_token_ms": None, "total_ms": -1}
        verdict = evaluate(entry, result)
        row = {**entry, "result": result, **verdict}
        rows.append(row)
        mark = "PASS" if verdict["pass"] else "FAIL"
        print(f"  [{mark}] {entry['id']}: first={result['first_token_ms']}ms "
              f"abst={result['abstained']} kc={(result['bkt_context'] or {}).get('kc_id')}"
              + ("" if verdict["pass"] else f" -> {'; '.join(verdict['failures'])}"))

    summary = summarize(rows)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_json = REPORTS_DIR / f"golden_set_v1_{ts}.json"
    out_json.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False))

    print("\n== RESUMEN ==")
    print(f"  pass/total: {summary['passed']}/{summary['total']}")
    for case, agg in summary["by_case"].items():
        print(f"  {case}: {agg['pass']}/{agg['n']}")
    print(f"  kc_accuracy (K2): {summary['kc_accuracy']:.2%}")
    print(f"  first_token p50: {summary['first_token_p50_ms']}ms | max: {summary['first_token_max_ms']}ms | <={FIRST_TOKEN_BUDGET_MS}ms: {summary['first_token_within_budget']}")
    print(f"  report: {out_json}")

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
