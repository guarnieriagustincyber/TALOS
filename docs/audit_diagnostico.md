# Auditoría Diagnóstica — TALOS (4 lentes)

- **Base:** código en `main@480ce17` (post-Fase 6), suites `tests/unit` (818+ tests), golden set v1.
- **Vocabulario por celda:** `ok` (verificado con archivo:línea o test citable) · `needs_review` (pregunta explícita adjunta) · `violation` (clase: fail-closed | leakage | autoridad) · `na`.
- **Regla de evidencia:** "ok" solo con cita verificada en el código actual o test existente. Lo no verificable con esa precisión es `needs_review`.
- **Insumo faltante:** `data/eval/manual_tests_v1.md` (transcript de PRUEBASTALOS) **no existe en el repo** — los caminos del transcript se evalúan contra la descripción textual de la consigna, no contra el transcript. Eso limita la precisión del Artefacto 4 (se marca donde aplica).

---

## ARTEFACTO 1 — Mapa de fronteras de confianza

| Punto de entrada | (a) Resolución | (b) ¿Cruza "no debe verse todavía"? | (c) Fail-closed ante ambigüedad | Evidencia |
|---|---|---|---|---|
| POST /api/chat/query (notebook) | Mixto: identidad exacta para scope (ScopeResolver) + similitud semántica para contenido (vector 0.87 + FTS guarda palabra-completa) | **needs_review** — los chunks que entran al prompt no se filtran por banda R2/p_L: la evidencia cruda alcanza al LLM pero el depth adapter restringe la voz. Pregunta: "¿la correctitud R2 debe gobernar qué chunks se presentan y no solo el tono?" | ok — abstención E2 si 0 chunks (chat.py:`_assemble_epistemic_context` E2) + gate pre-LLM | `web/routes/chat.py:503-540` (global), `storage/knowledge_store.py` (hybrid+guards); E25/E2 tests security |
| Fast-path conversacional (follow-ups "dale/sí") | Identidad: solo reglas regex + micro-LLM con output_guard; no retrieval | ok — no abre contenido nuevo; fallback determinista <1ms | ok — guard + fallback | `tutor/fastpath_service.py:127-160` (detect), `234-263` (generate+fallback) |
| POST /api/chat/evaluate | Identidad exacta (exercise_id) | ok — `is_presentable()` fail-closed; UNGRADED sin mutar BKT si no hay clave certificada | ok | `web/routes/chat.py:1492-1560`; `test_exercise_loop.py` |
| CLI `talos kc` (list/add/delete) | Identidad exacta (kc_id slug) | ok — los canónicos JSON son inalcanzables por delete (barrera origin='manual') | ok — duplicado → 409-semántico (exit 4) | `cli.py` `_cmd_kc_*`, `curriculum/kc_admin.py` |
| CLI ingesta (`export-pending` / `sync-vectors` / `verify-index`) | Identidad exacta (chunk_id, notebook_id, contract hash) | ok — solo INSERT de vectores nuevos, valida contract antes de tocar la DB | ok — sync ininterrumpido vía una sola transacción + pre-validación completa | `cli.py` `_parse_vectors_file`, `sync_vectors`; tests `test_colab_cycle.py` |
| Inyección session_digest | Identidad (student_id, último digest por timestamp) | needs_review — digest de sesión A puede mencionar KCs que en la sesión B aún no se vieron (¿recordar debilidades es leakage pedagógico aceptable?) | ok | `web/routes/chat.py` `maybe_inject_session_digest` |
| Inyección struggle (Protocolo de Lucha) | Identidad (kc_id de /evaluate) | ok | ok — solo si >=3 fallos consecutivos del mismo KC | `pedagogy/exercise_service.py` `StruggleTracker`; `web/routes/chat.py` inyección post-BKT |
| Planeado: certify / submit / ex-show | na | na | na | no existen en `web/routes` (grep `certify` = 0). ex-show vive solo como templates + audit script |

### Pregunta explícita por camino — P(L) ausente

**Estado actual (verificado):** `BKTStorage.get_bkt_state` devuelve None si no hay estado; `BKTTracker.get_state` devuelve un default **no persistido** con `p_L = params.p_L0 = 0.1` (`bkt_tracker.py:47-68`). Y `determine_pedagogical_context_mode` mapea `p_L < 0.30 → basic` (`student_context.py:118-121`).

| Camino | Comportamiento hoy con KC nunca evaluado |
|---|---|
| Chat (K2) con KC matcheado | **basic** (máximo andamiaje: analogías cotidianas + capas separadas) |
| Chat con KC no matcheado | **intermediate/neutral** (fallback=True, p_L=0.5) |
| /evaluate config | p_L inicial 0.1 explícito |

⚠️ Inconsistencia de diseño detectada (verificada en código): *mismo* estudiante, *misma* KC nunca evaluada → "basic" si alcanzó a matchear el KC pero "neutral" si no. Coincide con la observación del audit (andamiaje máximo por defecto para lo nunca evaluado). El candidato a contrastar (P(L) ausente → neutral + acelerar primera señal graded) hoy **no está implementado**; elThreshold 0.30 es el valor actual.

---

## ARTEFACTO 2 — Matriz de invariantes

Verificado = test o archivo:línea en código actual. "sin testear" ≠ decay: significa que el comportamiento existe pero sin test de regresión.

| Invariante \ Módulo | retrieval (hybrid/vector/fts) | chat (SSE epistémico) | fast-path | evaluate (graders) | BKT/Struggle | Mem0/Digest | ExerciseStore/ex-generators |
|---|---|---|---|---|---|---|---|
| LLM nunca escribe estado/corrección/dominio | ok (`structured_pipeline.py` guards + abstención pre-LLM; `test_long_context_invariants`) | ok (cita solo de pack) | ok (guard + fallback estático) | ok (fail-closed; mutation solo por grader determinista `chat.py:1527-1555`) | ok (`bkt_tracker.py`: ValueError si source=UNVERIFIED_DIALOGUE, `:143-147`) | ok | ok (generados con oracle determinista) |
| Fail-closed ante ambigüedad | needs_review (R1: ver abajo) | ok (E2/E25 abstención al 0-chunk) | ok | ok | ok | ok | ok (none si no hay plantilla) |
| Toda afirmación cita [E#] verificado | na | ok (corregido en Commit 1 con buffer lookahead y reescritura canónica) | na | na | na | na | na |
| R1 acceso global en roadmap | ok (verificado código actual: `chat.py:869` sentinel + `:1005-1008` folder→global + `:503-540` fusión cross-notebook; commit ccbb8d0) | ok | na | na | na | na | na |
| R2 profundidad gobernada por learner state | ok (unificado en Commit 4: cold-start intermediate, propuesta acelerada a 2 turnos, sin asunción de déficit) | ok (directiva) | na | na | na | na | na |
| Grader determinista único árbitro | na | na | na | ok (`chat.py:1527+`, graders MC/Exact; generados con oracle propio) | ok | na | ok |
| Código no confiable solo en sandbox | na | ok (nunca ejecuta: no hay executor en chat) | na | na | na | na | na (templates estáticas; nunca ejecutan) |
| Certificación única vía certify | na | na | na | na | na | na | ok (oráculo persistido en SQLite sin fuga en HTTP - Commit 2) |

### REGLA R1 (tal cual pedido)

`ok por diseño` citando commit + líneas verificadas en el código actual:
- Commit `ccbb8d0` — `src/study_engine/web/routes/chat.py:869` (`GLOBAL_SCOPE_ID`), `:1005-1008` (folder+delegate→global), `:502-540` (fusión cross-notebook por chunk_id, test `test_global_scope.py`).

---

## ARTEFACTO 3 — Trazabilidad pedagógica

| Capacidad | Estado | Referencia verificada |
|---|---|---|
| ZDP por bandas (basic/intermediate/advanced/prereq) | implementado | `pedagogy/student_context.py:110-130`, consumido en `chat.py:1076-1086` |
| DepthModulator (0.5/0.8 scales) | eliminado (huérfano) | Resuelto en Commit 5: `student/depth_modulator.py` eliminado; `student_context.py` consagrado como autoridad única |
| Protocolo de Lucha | implementado | `exercise_service.py` `StruggleTracker` + inyección en `chat.py` tras bkt_directive; tests `test_struggle_protocol.py`; commit `2ece816` |
| Auto-explicación del error | implementado (parcial) | remediación determinista en `/evaluate` (chat.py) + struggle directive paso 1; extracción de misconceptions por micro-LLM separada (`memory_extractor.py`) |
| Interleaving | no iniciado | — |
| Calibración de confianza | no iniciado | — |
| Espiral / profundización retroactiva | no iniciado | — |
| Session digest | implementado | `pedagogy/session_digest.py` + `maybe_inject_session_digest` en chat; tests `test_session_digest.py`; commit `7969049` |
| Fading (andamiaje decreciente) | no iniciado | — |

---

## ARTEFACTO 4 — Superficie real vs cobertura

### Caminos reales × test

| Camino real (incl. transcript) | Test | Nota |
|---|---|---|
| chat notebook grounded | ok (suite + golden K1/K2/K6/K5) | |
| abstención OOD | ok (`test_long_context_invariants`) | |
| preferencia meta declara→persiste | ok (`test_meta_declaration_survives_gate.py`) | |
| follow-ups "dale/sí" | sin testear unitariamente (fastpath tiene tests unitarios de detección; el pipeline SSE de follow-up no tiene test de regresión SSE) | needs_review: "¿qué test fija el follow-up completo?" |
| Stream truncamiento (finish_reason=length) | ok (`test_stream_finish_reason.py`); evento `truncated` emitido | |
| Citas `[E#]` / `[E# 0]` inválidas | ok formato (`test_citation_format.py`) PERO see violation A | |

### Regresión de bugs históricos

| Bug histórico | Test presente |
|---|---|
| Guard FTS por palabra completa (no substring; "ajo"≠"abajo") | **no** — existe test de sistema (_long_context_invariants), no test unitario de la regla | 
| Intento "Star Wars" + match léxico | ok (`test_intent_gate.py`) |
| Scope SJF cross-materia | ok (`test_global_scope.py`) |
| Preferencia Mem0 vs gate | ok (`test_meta_declaration_survives_gate.py`) |
| finish_reason/truncamiento | ok (`test_stream_finish_reason.py`) |
| Citas `[E#]` / `[E# 0]` | ok formato (`test_citation_format.py`) | ver violation de leakage (no reescritura) |
| kc=None warmup race | **no** (needs_review: "¿qué test fija el catálogo preload antes de aceptar queries?") |
| p_T estricto | ok (`test_bkt_strict_params.py`) |

### FILA OBLIGATORIA — fallback identidad → similitud

| Regla | Estado | Evidencia |
|---|---|---|
| "Si no hay fila confirmada, la respuesta declara explícitamente la no-exactitud" | ok (corregido en Commit 3) | El fallback declara explícitamente la no-exactitud mediante disclaimer determinista hablado en el stream de respuesta (`chat.py`) ante ausencia de KC confirmado en el cuaderno. |

---

---

## CIERRE — Lista Tier-0 (Actualizado Post-Investigaciones I1–I4)

### (1) Fail-closed violado
**Ninguna violación verificada (655/655 tests adversariales PASS).**
Se ejecutó la suite completa `tests/adversarial/` en 5 tandas controladas de memoria:
- Tanda 1 (assessment, audit, contracts, curriculum, evidence): 260 passed (1.50s)
- Tanda 2 (execution, federation, generation, ingestion, llm): 119 passed (9.70s)
- Tanda 3 (pedagogy, retrieval, roadmap, session, state, storage, system, timeout, tutor): 227 passed (29.74s)
- Tanda 4 (crisol): 27 passed (0.28s)
- Tanda 5 (crisol_chaos): 22 passed (6.13s)
Total: **655 passed, 0 failed**. El perímetro transaccional y de fail-closed queda formalmente confirmado y limpio con evidencia.

### (2) Leakage en presentación y Fuga de Gate
1. **`[E###]` alucinados llegan al usuario:** `citation_validator.validate_and_rewrite` existe pero el chat solo llama `audit_only` (`chat.py:1356`). Corregido en Commit 1 con buffer de lookahead gramatical y reescritura canónica.
2. **Fallback sin disclaimer hablado:** La respuesta no dice "no puedo confirmar que esto sea exactamente X". Corregido en Commit 3 con disclaimer determinista.
3. **Exposición de oracle en `/generate/*`:** Los endpoints de generación devuelven el `oracle` al cliente HTTP. Corregido en Commit 2 ocultando el oráculo en la vista HTTP (persistido en SQLite `generated_exercises`).
4. **Fuga de Gate FTS (Hallazgo D / I2):** Al consultar `¿Cómo se declara int *p?`, el comodín `*` en términos cortos (`int*`) sumado a la omisión de guarda disyuntiva en `knowledge_store.py:553` para consultas de 2 términos permitió la admisión indebida de 6 chunks de `so_planificacion.pdf` al prompt context. Reclasificado formalmente como **Tier-0 Fuga de Gate** y corregido en Commit 6 con guarda de cobertura normalizada (sin escape hatch).

### (3) Inversión de autoridad y Fronteras
- **Inversión de autoridad:** **Ninguna.** Estado siempre mutado deterministamente.
- **Hallazgo A / I1 (`query_rewriter.py` importa `generation.prompts`):** Reclasificado. No es falla Tier-0 porque `rewrite_with_llm` no se invoca en tiempo de chat (la búsqueda usa `rewrite()` regex heurístico y degrada fail-closed a query cruda). Sin embargo, viola la frontera arquitectónica S3 -> S4 en `tests/contract`. Resuelto en Commit 7 eliminando definitivamente `rewrite_with_llm`.

---

## Notas de alcance verificadas

- Conteo global de pruebas verificado: **2.366 tests recolectados** tras resolver la colisión de nombres en `tests/llm_pool/test_provider_circuit_breaker.py`.
- Suites `tests/unit/` (780 passed) y `tests/adversarial/` (655 passed) verificadas al 100%.

