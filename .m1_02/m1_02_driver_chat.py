#!/usr/bin/env python3
"""M1-02 chat driver: captura SSE COMPLETA de /api/chat/query (fase conceptual).

Diferencia clave vs driver M1-01: SIN truncado de eventos — captura
phase_token/phase_start/evidence_manifest/audit_verdict completos para
ensamblar el texto generado y analizar compliance de citas [E#] con el
ClaimExtractor real, offline.

Aislamiento: mismos bases working3 + server en :8000.
"""
import asyncio
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

REPO = Path("/media/agustin/Laboratorio/study-engie")
WORK_DIR = REPO / ".m1_01" / "working3"
PORT = 8001  # puerto aparte para no chocar con el driver de concepto
BASE = f"http://127.0.0.1:{PORT}"

EV_DIR = REPO / ".m1_02" / "evidence"
EV_DIR.mkdir(parents=True, exist_ok=True)
RUN_ID = f"m1_02chat_{datetime.now(tz=timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

QUERIES = [
    ("c1_conceptual", "¿Cómo funciona la aritmética de punteros y por qué p+1 avanza sizeof(T) bytes?"),
    ("c2_conceptual", "Explicá qué es el comportamiento indefinido al acceder fuera de los límites de un arreglo en C."),
    ("c3_conceptual", "¿Por qué una lista doblemente enlazada ocupa más memoria que una simplemente enlazada?"),
]


def t_utc():
    return datetime.now(tz=timezone.utc).isoformat()


async def chat_sse_full(c: httpx.AsyncClient, payload: dict, tag: str, timeout=300):
    """Captura TODOS los eventos SSE sin truncar, con latencia por evento."""
    t0 = time.perf_counter()
    events = []
    full_text = ""
    try:
        async with c.stream("POST", BASE + "/api/chat/query", json=payload, timeout=timeout) as r:
            events.append({"event": "_HTTP_STATUS", "status": r.status_code, "t_ms": 0.1})
            buf = {}
            async for line in r.aiter_lines():
                if not line:
                    continue
                if line.startswith("event:"):
                    buf = {"event": line[6:].strip(), "t_ms": round((time.perf_counter() - t0) * 1000, 1)}
                    continue
                if line.startswith("data:"):
                    raw = line[5:].strip()
                    try:
                        ev = json.loads(raw)
                    except Exception:
                        ev = {"raw": raw[:400]}
                    ev["_arrived_ms"] = round((time.perf_counter() - t0) * 1000, 1)
                    buf["data"] = ev
                    et = (ev.get("event_type") if isinstance(ev, dict) else None) or buf.get("event")
                    if et == "phase_token" and isinstance(ev, dict):
                        pl = ev.get("payload") or {}
                        full_text += (pl.get("token") or "")
                    events.append(dict(buf))
                    buf = {}
    except Exception as exc:
        events.append({"event": "CLIENT_ERROR", "raw": repr(exc)[:400]})
    total_ms = round((time.perf_counter() - t0) * 1000, 1)
    (EV_DIR / f"{RUN_ID}_sse_{tag}.log").write_text(
        "\n".join(json.dumps(e, ensure_ascii=False, default=str) for e in events),
        encoding="utf-8",
    )
    (EV_DIR / f"{RUN_ID}_text_{tag}.txt").write_text(full_text, encoding="utf-8")
    return {"tag": tag, "total_ms": total_ms, "events": len(events),
            "text_chars": len(full_text), "text_head": full_text[:220]}


async def main():
    server = subprocess.Popen(
        [str(REPO / ".venv" / "bin" / "python"), str(REPO / ".m1_01" / "m1_01_server.py"), str(WORK_DIR), str(PORT)],
        cwd=str(REPO), stdout=open(EV_DIR / f"{RUN_ID}_server.log", "w"), stderr=subprocess.STDOUT,
    )
    results = {"run_id": RUN_ID, "started_utc": t_utc(), "queries": []}
    try:
        async with httpx.AsyncClient() as c:
            for _ in range(120):
                try:
                    if (await c.get(BASE + "/api/health", timeout=4)).status_code == 200:
                        break
                except Exception:
                    pass
                await asyncio.sleep(1)
            else:
                raise RuntimeError("server no saludó")
            open_sid = None
            r = await c.post(BASE + "/api/study/session/open", json={"notebook_id": "fase0-soc"}, timeout=60)
            open_sid = (r.json() or {}).get("session_id")
            results["session_id"] = open_sid

            for tag, q in QUERIES:
                payload = {
                    "session_id": open_sid,
                    "notebook_id": "fase0-soc",
                    "prompt": q,
                    "query": q,
                    "requested_phase": "conceptual",
                }
                out = await chat_sse_full(c, payload, tag)
                print(f"[{tag}] total {out['total_ms']/1000:6.2f}s  chars={out['text_chars']}", flush=True)
                # M1-03 §2: archivar el reporte de auditoría del server
                # (env-gated TALOS_DEBUG_PROMPTS) por query, para no perder
                # la captura de cada fase al sobrescribirse el archivo.
                dbg = REPO / "debug_audit_report.txt"
                if dbg.exists():
                    (EV_DIR / f"{RUN_ID}_audit_{tag}.txt").write_text(
                        dbg.read_text(encoding="utf-8"), encoding="utf-8")
                results["queries"].append(out)
        (EV_DIR / f"{RUN_ID}_summary.json").write_text(
            json.dumps(results, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
        print("saved summary", flush=True)
    finally:
        server.terminate()
        try:
            server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    asyncio.run(main())
