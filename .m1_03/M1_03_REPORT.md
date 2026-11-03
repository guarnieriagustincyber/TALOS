# M1-03 — Reporte de cierre

**Fecha:** 2026-10-21 04:5x UTC
**Clasificación:** `M1_03_COMPLETE`
**Base de comparación:** HEAD `845480c` (worktree `.m1_03/talos_head` removido tras verificación)
**Evidencia preservada:** `/media/agustin/Almacenamiento/Facultad/TALOS/m1-03-evidence-20261021/` (226 archivos, `SHA256SUMS.txt` verificado `INTEGRITY_OK`, 8.3 MB)

---

## 1. Objetivo y resultado

Recuperar el chat académico generativo (retrieval → generación → S4.4 → SSE) y el diálogo
socrático auténtico, con al menos una conversación académica real en navegador. **Logrado:** el
escenario de 8 pasos (§5) corre end-to-end en cliente real — 3 corridas completas — con
explicación generada y aprobada (badge `S4.4: APPROVED`), corrección pedagógica fundada ante
error del estudiante, y continuidad persistente. Target ≤25s E2E por respuesta completa
cumplido en todos los turnos salvo una anomalía única del provider (documentada en §6).

## 2. Causas raíz y correcciones

### RCA-1 — El chat nunca alcanza generación (brecha preexistente M1-01, [01])
`resolver → statement_chunks → 0 hits` para queries conceptuales: el C5 gate abstenía
`QUERY_OUT_OF_SCOPE` pre-LLM para toda query académica de contenido.
**Corrección (determinista, sin IA):** `_recover_coverage_gaps` en `chat.py` — mismos
extractores y allowlist del propio gate C5, límite 4 snippets/término, máx 8 chunks — más
**poda C3 con protección dinámica** `_drop_is_safe(i)`: un drop es seguro solo si cada término
crítico que cubre el chunk queda cubierto por otro chunk de la selección ACTUAL (la versión
estática destruía cobertura cuando dos chunks compartían términos → no regresar a esa
semántica). Nada droppable → el chokepoint decide fail-closed.
**Nota normativa:** el conteo de tokens del chokepoint es el payload REAL (system+user); la
evidencia viaja embebida en el user prompt dentro del sub-presupuesto 2150 (1800+350).
Offline repro: c1/c2/c3 → `abstained=False, SUFFICIENT_EVIDENCE, coverage 1.0`
(c1: 14 chunks / 2137 ev-tokens ≤ 2150; c2: 4/2034; c3: 1/573). Control OOS abstuvo ✓.

### RCA-2 — Presupuesto C3 violado por tokens fantasma en live
`context=str(context_pack)` en `_stream_tokens` (structured_pipeline ~L2042) sumaba ~20 tokens
fantasma → 4769 > 4761 en live. **Corrección:** `context=None` (documentado: el backend Gemini
stream ignora `context`; el router solo lo usa para screening de sensibilidad, que ya cubre
system+user). El repro que lo demostraba era `repr(pack)` de 76 chars sobre el payload plan.

### RCA-3 — Falso REJECTED global de abstinencias honestas (L1 claim-layer)
`ClaimExtractor` clasificaba la honestidad epistémica en primera persona ("No tengo evidencia
en las fuentes autorizadas…") como FACTUAL sin tags → CHECK_FACTUAL_GROUNDING FAIL global →
`REJECTED` de respuestas correctamente abstencionistas.
**Corrección:** patrón `_EVIDENCE_META_PATTERNS` acotado (≤160 chars, exige fuentes/evidencia/
cuaderno) → CONVERSATIONAL. El requisito de citas queda intocado para hechos del dominio.
Verificado offline repro L1 (`offline_chat_l1.py`): primera persona → CONVERSATIONAL;
factual tageado [E1][E2] → FACTUAL NO_ANOMALY.

### RCA-4 — Turnos de diálogo del cliente real no llegaban al DialogueEngine
Hallazgo del escenario en navegador (run `browser_20261021040922`): el turno de conversación
"no entiendo, explícame de otra forma" procesado por `/api/chat/query` (chat real con
`session_id` de la sesión de estudio) abstenía `QUERY_OUT_OF_SCOPE` — la continuidad
pedagógica se rompía: pedir reformulación no es una consulta fuera de scope.
**Corrección:** `_maybe_dialogue_turn_stream` en `chat.py` — delegación acotada, determinista
y fail-closed: SOLO si (1) marcadores de meta-discurso (11 strings cerrados,
misma clase que `DialogueEngine._propose_intent`), (2) sesión con episodio activo en fase
EXPLAINING/DIALOGUE, (3) ConceptPacket ya APROBADO reutilizable (`_load_or_reuse_concept_response`).
Una vez delegado, reusa EXACTAMENTE la maquinaria de la ruta de diálogo
(`process_dialogue_turn`): transición, reuse del packet, S4.4 por cache
idempotente — no se genera contenido nuevo ni se re-audita lo aprobado. Los mensajes de
contenido (ej. el error del estudiante "El puntero guarda el valor…") NO delegan → corrección
fundada por el propio pipeline de chat (retrieval + S4.4). Fallo técnico post-delegación →
SSE `error` (jamás abstinencia); veredicto no aprobatorio → `abstention` sin tokens
(normalización de enum: `str(verdict).upper().split(".")[-1]` — defecto de `.upper()` puro
corregido durante el implementado). `evidence_manifest` emitido con los CitationRecords del
turno → chips verificados [E1] p.77 / [E2] p.22 en el cliente real (contrato de match:
citation_id + namespace, nunca posición).

## 3. Instrucciones de generación (§2, protocolo de citas) — 3 iteraciones

`CITATION_PROTOCOL_BLOCK`: 280 → 209 tokens (regla NO-infieras: contrastes, cantidades nuevas),
luego oraciones de ausencia SEPARADAS y SIN tags (materializar "pero no detallan" dentro de un
claim citado → refutación NLI en c2), luego cláusula ANTES-de-abstener (revisar TODO el bloque
y usar la evidencia que respalda el tema) + prohibición de meta-atribución ("enunciá los
hechos de forma directa… el verificador evalúa la afirmación técnica, no la atribución").
**Balance final: 309 tokens netos; c1 ≈ 4698/4761 (~63 tokens de holgura).** Dump por query
`debug_audit_report.txt` env-gated (`TALOS_DEBUG_PROMPTS=true`), archivado por run
`_audit_<tag>.txt` (21 dumps preservados).

## 4. Generaciones reales y aprobaciones S4.4 (§2)

12 runs live × 3 queries (evidencia `chat_live/m1_02chat_*`): resumen cuantitativo en
`chat_live/m1_03_latency_summary.json` (regenerado con extractor corregido).

- **Texto generado con citas y veredictos reales:** runs con tokens emitidos y badge
  `audit_verdict` en stream (solo se emiten tokens con veredicto normalizado APPROVED —
  fail-closed de emisión mantenido).
- **Compliance de citas analizado por adjudicador determinista** (`analyze_chat_citations.py`
  → `citation_compliance_analysis.json`): **c3 (run 040346Z): 2 claims FACTUAL, ambos tageados
  [E1], compliance = 1.0.**
- **NLI real observado:** semcheck 1–4 claims/turno; ejemplo c1 040253Z `nli_executed=true,
  nli_calls=2, sem=2`. `nli_cache_hits=0` en todos los turnos observados (queries distintas
  por turno — el reuse cache M1-02 permanece disponible pero no hit en este escenario).
- **Cobertura empírica de veredictos sobre los 36 turnos:** 11 APPROVED-con-texto, 1 APPROVED
  de abstinencia honesta, 15 REJECTED académicos (sin tokens — fail-closed correcto),
  2 DEFERRED_RETRY técnicos (juez), 7 abstinencias tempranas pre-LLM (~0.8s).

## 5. Comportamiento socrático (§3/§5)

**Engine (`dialogue_engine.py`):** pregunta socrática determinista desde el ConceptPacket
aprobado (`_FIELD_ROLL` core_concept→mental_model→reasoning_guidance→formalization→
implementation; rotación por `turn_count`; pasaje verbatim), reformulación progresiva
(mental_model tageado), corrección ante error con pitfalls tag-LEADING verbatim +
`_MISCONCEPTION_MARKERS` (15 marcadores conservadores). `comprehension_signal=UNKNOWN`
(no se acredita comprensión). Preguntas con formato limpio ("¿Qué caso concreto ilustra
eso?" — espacio espurio eliminado tras la corrida 041802).

**Cliente real (3 corridas × 8 pasos):**
- Turno 4 (error del estudiante): "El puntero guarda el valor del objeto, no la dirección de
  memoria." → corrección fundada por retrieval+S4.4 con claims verificados:
  `[E1] p.775 "Un puntero es una variable que contiene una dirección."` + operador de
  indirección `[E1] p.775` + pregunta de contraste ("¿Qué es lo que almacena exactamente una
  variable puntero según la evidencia?"). **Textos distintos entre corridas** (runs
  040922 / 041802 / 042403: ausencia enunciada + [E3] en la primera; solo operador de
  indirección en las siguientes; preguntas de contraste reformuladas) — no hay repetición
  de template.
- Turno 6 (meta-discurso): "no entiendo, explícame de otra forma" → **delegación funcional**:
  turno del episodio con claims del packet aprobado (métodos algorítmicos [E1] p.77 / [E2]
  p.22) + pregunta socrática del packet ("¿Qué caso concreto ilustra eso?") y chips
  verificados — ya no `QUERY_OUT_OF_SCOPE` (corrección de RCA-4, validada en runs
  041802 y 042403).

## 6. Latencias §4 (respuesta COMPLETA ≤ 25s)

`chat_live/m1_03_latency_summary.json` — E2E medido de phase_start a último evento, desde
logs con `_arrived_ms`; 36 turnos en 12 runs × 3 queries:

| Clase (veredicto) | n | E2E típico | Máx |
|---|---|---|---|
| Abstención pre-LLM (sin proveedor) | 7 | 0.76–0.91 s | 0.91 s |
| REJECTED académico | 15 | 1.88–4.33 s | 4.33 s |
| DEFERRED_RETRY técnico (juez) | 2 | 3.98–4.06 s | 4.06 s |
| APPROVED con texto | 11 | 1.93–5.18 s; 8.95 s (c3 040346Z) | **40.19 s (anomalía c1 035608Z)** |

- time-to-first-progress típico 1.85–3.1 s (start retrieval/gate 0.6–1.0 s).
- **Anomalía registrada como técnico, no académica:** c1 035608Z gen=37.9 s (provider stall) →
  E2E 40.19 s. Ninguna otra RUN superó 8.95 s ≪ 25 s.
- **503/429 HTTP: 0** en los logs server de los 12 runs (grep `HTTP/1.1" 503|429` — el match
  previo era timestamp. Fallo de medición corregido).
- **Errores del juez: 2** ("Invalid structured semantic assessment", 035227Z/035418Z) →
  clasificados técnicos DEFERRED_RETRY con reintento (según §4: caso técnico ≠ abstinencia
  académica).

## 7. Regresiones §6 — comparación contra HEAD `845480c`

| Suite | Cambios | HEAD puro | Δ |
|---|---|---|---|
| web+retrieval+context | 9 F + 11 E | **9 F + 11 E (re-verificado hoy en worktree HEAD)** | 0 |
| pedagogy+audit | 4 F + 3 E | 4 F + 3 E (idénticos, re-verificado) | 0 |
| tests nuevos (coverage/delegación/socrático) | 5+7+4 = **16 passed** | — (nuevos) | +16 |

Los 9F web (content_registry×2, exercise_generation_leak×4, t04_exercise_identity×3) y 11E
(symbol_guard×8, context_flood, disclaimer×2) **pre-existen en HEAD**: reproduce la lista
idéntica con el mismo intérprete en el worktree limpio. No se tocaron bases productivas ni
contratos protegidos.

## 8. Continuidad (§5 pasos 6–8)

localStorage `talos_study_session:agustin:fase0-soc` + historial de chat por session_id;
reload → `restored:true` + diálogo presente (pasos 7 y 8 en las 3 corridas; SNAPSHOT
`/snapshot` 200 tras reload). El KC del turno 4 por chat general es clasificación del chat
(tramo3) — comportamiento intencional del diseño: el chat general para contenido, el
episodio (tramo1) para meta-discurso.

## 9. Tests y archivos para checkpoint

**Tests nuevos (16 pasados):** `tests/unit/web/test_chat_coverage_recovery.py` (5),
`tests/unit/web/test_chat_dialogue_delegation.py` (7: contenido no delega; sin
session/packet → fallback; técnico → error; veredicto rechazado → abstención sin tokens),
`tests/unit/pedagogy/test_dialogue_socratic_turns.py` (4).
**Repros offline verificados al cierre:** `offline_chat_retrieval_repro.py` (query válida →
generador ✓; OOS → abstención ✓), `offline_chat_l1.py` ✓.
**Código:** `chat.py` (recovery+poda+delegación+manifest), `structured_pipeline.py`
(protocolo 309 tokens, `context=None`, dump), `claim_extractor.py` (meta-patterns),
`dialogue_engine.py` (respuesta socrática, probes).
**Staging focal SIN commit (decisión M1-02/M1-03):** archivos anteriores + tests +
`docs/CAPABILITY_MATRIX.md` + driver + repros. Logs extensos y SQLite NO versionados (§6).
**Preservación:** `m1-03-evidence-20261021/{chat_live,browser,debug_reports}/` +
`SHA256SUMS.txt`.

## 10. Notas honestas

- **c2 inestable ante meta-atribuciones** ("Las fuentes autorizadas definen que…" →
  4 REJECTED UNSUPPORTED_GENERALIZATION en 11 runs) pese a la instrucción anti-meta
  (4 iteraciones sobre el protocolo). Registrado fielmente; no se fuerza aprobación ni se
  reasignan citas. c1/c3 ceden en la mayoría de los runs; c3 4× APPROVED al final.
- **Anomalía provider única** (40.19 s) registrada como stall técnico.
- Las 2 instancias de juez técnico y la retracha quedan documentadas; ningún rechazo
  académico fue reintentado ni convertido en aprobación.

---

**Resultado: `M1_03_COMPLETE`** — cada requisito §1–§7 tiene evidencia identificable y
reconstruyible; los unknowns (c2 meta-atribución, latencia provider) permanecen visibles.
