"""Benchmark TALOS v1.1 vs NotebookLM — 5 Pruebas Epistémicas y Pedagógicas."""

import json
import time
from pathlib import Path
from fastapi.testclient import TestClient
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container

def parse_sse_response(resp_text: str):
    tokens = []
    evidences = []
    abstained = False
    metadata = {}

    lines = [line.strip() for line in resp_text.split("\n") if line.startswith("data: ")]
    for line in lines:
        raw = line[6:].strip()
        if not raw or raw == "[DONE]":
            continue
        try:
            ev = json.loads(raw)
            ev_type = ev.get("event_type")
            payload = ev.get("payload", {})
            if ev_type == "phase_token":
                tokens.append(payload.get("token", ""))
            elif ev_type in ("evidence", "evidences"):
                if isinstance(payload, list):
                    evidences.extend(payload)
                else:
                    evidences.append(payload)
            elif ev_type == "abstain":
                abstained = True
            elif ev_type == "phase_complete":
                metadata = payload
        except Exception:
            pass

    full_text = "".join(tokens)
    return full_text, evidences, abstained, metadata

def run_benchmark():
    print("=" * 80)
    print("INICIANDO BENCHMARK TALOS v1.1 vs NOTEBOOKLM (5 PRUEBAS EPISTÉMICAS)")
    print("=" * 80)

    container = AppContainer(working_dir=Path("data/web_state"), use_mock=False)
    set_container(container)
    app = create_app()
    client = TestClient(app)

    benchmark_queries = [
        {
            "id": "Q1_SOCRATIC_ANTI_SHORTCUT",
            "name": "1. Anti-Atajo / Socrático (Condición de Carrera y Mutex)",
            "notebook_id": "fadena-so2",
            "prompt": "Tengo dos hilos que incrementan un contador global en C y el resultado final a veces da menos de lo esperado. ¿Cómo lo arreglo? Mostrame el código directo con pthread_mutex.",
            "notebooklm_behavior": "Entrega inmediatamente el código C completo con pthread_mutex_lock y pthread_mutex_unlock, resolviendo el problema por el estudiante sin andamiaje ni deducción activa.",
            "talos_target": "Reconoce el intento de solución, valida la dificultad sin revelar código en bandeja ('anti-leakage'), recurre a analogía física tangible y formula pregunta socrática activa.",
        },
        {
            "id": "Q2_FAIL_CLOSED_HALLUCINATION",
            "name": "2. Fail-Closed / Alucinación (__guarnieri_opt)",
            "notebook_id": "fase0-soc",
            "prompt": "Explicame cómo funciona la directiva de compilación __guarnieri_opt y en qué registros x86-64 guarda el frame pointer.",
            "notebooklm_behavior": "Tiende a especular o alucinar basándose en su preentrenamiento ('__guarnieri_opt parece ser una directiva interna o macro no estándar...').",
            "talos_target": "Fail-closed estricto (ADR-008): se abstiene explícitamente declarando no encontrar evidencia [E#] para __guarnieri_opt en el corpus soberano.",
        },
        {
            "id": "Q3_FEYNMAN_BARRIO_ANALOGY",
            "name": "3. Analogía Tangible 'Feynman de Barrio' (Punteros Dobles **p)",
            "notebook_id": "fadena-lenguajes",
            "prompt": "No entiendo nada de punteros dobles (**p) en C, me tiene re mareado, siento que no me da la cabeza para esto.",
            "notebooklm_behavior": "Respuesta fría, teórica y abstracta ('Un puntero a un puntero es una variable que almacena la dirección de memoria de otro puntero...').",
            "talos_target": "Detecta frustración rioplatense ('me tiene re mareado'), valida empáticamente la complejidad, usa analogía física ('Feynman de Barrio') y cita [E#].",
        },
        {
            "id": "Q4_SPIRAL_CURRICULUM",
            "name": "4. Currículo en Espiral (Buffer Overflow -> Stack Frame)",
            "notebook_id": "fadena-so2",
            "prompt": "¿Cómo se produce un buffer overflow en el stack y qué pasa con la dirección de retorno?",
            "notebooklm_behavior": "Explicación enciclopédica desvinculada del mapa cognitivo y de los prerrequisitos dominados por el estudiante.",
            "talos_target": "Conecta con el prerrequisito del stack frame (%rbp/%rsp) dominado previamente y proyecta el siguiente salto conceptual (protecciones ASLR/canarios).",
        },
        {
            "id": "Q5_CITATION_RIGOR",
            "name": "5. Rigor Epistémico de Citas [E#] (ABI System V x86-64)",
            "notebook_id": "fase0-soc",
            "prompt": "¿Cuáles son los primeros 6 registros utilizados para pasar enteros en System V AMD64 ABI y cuál es el registro de retorno?",
            "notebooklm_behavior": "Citas genéricas a capítulos enteros o páginas amplias sin correspondencia frase por frase.",
            "talos_target": "Atribución atómica [E#] con granularidad proposicional para los 6 registros (%rdi, %rsi, %rdx, %rcx, %r8, %r9) y el retorno (%rax).",
        }
    ]

    results = []

    for item in benchmark_queries:
        print(f"\n---> Ejecutando {item['name']}...")
        t0 = time.perf_counter()
        res = client.post(
            "/api/chat/query",
            json={
                "prompt": item["prompt"],
                "scope_type": "notebook",
                "scope_id": item["notebook_id"],
                "notebook_id": item["notebook_id"],
            }
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        raw_text = res.text
        full_text, evidences, abstained, metadata = parse_sse_response(raw_text)

        # Fallback if SSE response text was in raw text
        if not full_text and res.status_code == 200:
            full_text = raw_text

        has_citations = "[E#" in full_text or len(evidences) > 0
        has_socratic_q = "?" in full_text or "¿" in full_text
        has_code_leak = "pthread_mutex_lock(&" in full_text and "pthread_mutex_unlock(&" in full_text

        result_entry = {
            "id": item["id"],
            "name": item["name"],
            "prompt": item["prompt"],
            "notebook_id": item["notebook_id"],
            "status_code": res.status_code,
            "elapsed_ms": round(elapsed_ms, 1),
            "response_text": full_text,
            "evidence_count": len(evidences),
            "has_citations": has_citations,
            "has_socratic_q": has_socratic_q,
            "has_code_leak": has_code_leak,
            "abstained": abstained or ("fuera del alcance" in full_text.lower()) or ("no encontr" in full_text.lower()),
            "notebooklm_comparison": item["notebooklm_behavior"],
            "talos_target": item["talos_target"],
        }
        results.append(result_entry)
        print(f"     Status: {res.status_code} | Latencia: {elapsed_ms:.1f}ms | Longitud: {len(full_text)} chars")
        print(f"     Extracto: {full_text[:140]}...")

    out_file = Path("data/experiments/benchmark_vs_notebooklm.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[OK] Benchmark concluido exitosamente. Guardado en {out_file}")

if __name__ == "__main__":
    run_benchmark()
