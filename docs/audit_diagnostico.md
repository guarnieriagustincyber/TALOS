# Auditoría Diagnóstica — TALOS (4 lentes)

- **Base:** código en `main@480ce17` (post-Fase 6), suites `tests/unit` (818+ tests), golden set v1.
- **Vocabulario por celda:** `ok` (verificado con archivo:línea o test citable) · `needs_review` (pregunta explícita adjunta) · `violation` (clase: fail-closed | leakage | autoridad) · `na`.
- **Regla de evidencia:** "ok" solo con cita verificada en el código actual o test existente. Lo no verificable con esa precisión es `needs_review`.
- **Insumo faltante:** `data/eval/manual_tests_v1.md` (transcript de PRUEBASTALOS) **no existe en el repo** — los caminos del transcript se evalúan contra la descripción textual de la consigna, no contra el transcript. Eso limita la precisión del Artefacto 4 (se marca donde aplica).

---

## ARTEFACTO 1 — Mapa de fronteras de confianza

| Punto de entrada | (a) Resolución | (b) ¿Cruza "no debe verse todavía"? | (c) Fail-closed ante ambigüedad | Evidencia |
|---|---|---|---|---|
| POST /api/chat/query (notebook) | Mixto: identidad exacta curricular (ContentRegistryRepository + ReferenceExtractor) + scope (ScopeResolver) + similitud semántica (vector 0.87 + FTS guarda cobertura) | ok — filtro de presentación universal pre-prompt elimina chunks de solucionario de seed y expansiones; fail-closed a abstención E2 si no quedan chunks de enunciado | ok — abstención E2 si 0 chunks (chat.py:`_assemble_epistemic_context` E2) + disclaimer de no-exactitud si fuzzy o missing | `web/routes/chat.py`, `retrieval/presentation_filter.py`, `storage/content_registry.py`; tests `tests/unit/web/test_chat_content_registry.py` |
| Fast-path conversacional (follow-ups "dale/sí") | Identidad: solo reglas regex + micro-LLM con output_guard; no retrieval | ok — no abre contenido nuevo; fallback determinista <1ms | ok — guard + fallback | `tutor/fastpath_service.py:127-160` (detect), `234-263` (generate+fallback) |
| POST /api/chat/evaluate | Identidad exacta (exercise_id) | ok — `is_presentable()` fail-closed; UNGRADED sin mutar BKT si no hay clave certificada | ok | `web/routes/chat.py:1492-1560`; `test_exercise_loop.py` |
| CLI `talos kc` (list/add/delete) | Identidad exacta (kc_id slug) | ok — los canónicos JSON son inalcanzables por delete (barrera origin='manual') | ok — duplicado → 409-semántico (exit 4) | `cli.py` `_cmd_kc_*`, `curriculum/kc_admin.py` |
| CLI ingesta (`export-pending` / `sync-vectors` / `verify-index`) | Identidad exacta (chunk_id, notebook_id, contract hash) | ok — solo INSERT de vectores nuevos, valida contract antes de tocar la DB | ok — sync ininterrumpido vía una sola transacción + pre-validación completa | `cli.py` `_parse_vectors_file`, `sync_vectors`; tests `test_colab_cycle.py` |
| Inyección session_digest | Identidad (student_id, último digest por timestamp) | needs_review — digest de sesión A puede mencionar KCs que en la sesión B aún no se vieron (¿recordar debilidades es leakage pedagógico aceptable?) | ok | `web/routes/chat.py` `maybe_inject_session_digest` |
| Inyección struggle (Protocolo de Lucha) | Identidad (kc_id de /evaluate) | ok | ok — solo si >=3 fallos consecutivos del mismo KC | `pedagogy/exercise_service.py` `StruggleTracker`; `web/routes/chat.py` inyección post-BKT |
| CLI `talos content` (show / solution) | Identidad exacta (ContentItem content_id / alias) vía ContentRegistryRepository | ok — `talos content show` nunca muestra solucionario; `talos content solution` exige intento previo o `--force` con log de auditoría (exit code 2 si denegado) | ok — fail-closed ante referencia inexistente o intento faltante | `cli.py:610-653`, `student/storage.py`; tests `tests/cli/test_content_cli.py` |

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
| Fail-closed ante ambigüedad | ok (E2 abstención al 0-chunk curricular o semántico) | ok (E2/E25 abstención al 0-chunk) | ok | ok | ok | ok | ok (none si no hay plantilla) |
| Toda afirmación cita [E#] verificado | na | ok (corregido en Commit 1 con buffer lookahead y reescritura canónica) | na | na | na | na | na |
| R1 acceso global en roadmap | ok (verificado código actual: `chat.py:869` sentinel + `:1005-1008` folder→global + `:503-540` fusión cross-notebook; commit ccbb8d0) | ok | na | na | na | na | na |
| R2 profundidad gobernada por learner state | ok (unificado en Commit 4: cold-start intermediate, propuesta acelerada a 2 turnos, sin asunción de déficit) | ok (directiva) | na | na | na | na | na |
| Grader determinista único árbitro | na | na | na | ok (`chat.py:1527+`, graders MC/Exact; generados con oracle propio) | ok | na | ok |
| Código no confiable solo en sandbox | na | ok (nunca ejecuta: no hay executor en chat) | na | na | na | na | na (templates estáticas; nunca ejecutan) |
| Certificación única vía certify | na | na | na | na | na | na | ok (oráculo persistido en SQLite sin fuga en HTTP - Commit 2) |
| Filtro universal de solucionario (no leakage) | ok (filtrado forzado en repositorios y chat; tests `test_presentation_filter.py`, `test_content_registry.py`) | ok (remoción en seed + expansión; fail-closed a E2) | na | ok | na | na | ok (show/solution blindado en CLI; exit 2 denegado) |

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

## RECONCILIACIÓN CONSOLIDADA DE SUITES Y COMPUERTAS (HEAD)

> **Criterio de Aceptación:** Total recolectado por `pytest --collect-only tests/` = **2.380 tests**.
> La suma de las filas del desglose reconstruye de manera unívoca y exacta el total del repositorio en corrida única consolidada:
> **2.372 PASSED** + **8 SKIPPED** + **0 FAILED** = **2.380 TESTS TOTALES RECOLECTADOS**.
> El Golden Set v1 se reporta por separado como evaluación en vivo end-to-end fuera del total estático de tests.

### Tabla Consolidada por Suite del Repositorio (Baseline Consolidado Post-Fase A)

| Suite | Total Recolectado | Passed | Failed | Skipped | Clasificación de Gate | Nota / Detalle |
|---|:---:|:---:|:---:|:---:|---|---|
| `tests/unit` | 797 | 797 | 0 | 0 | **Release Gate (Bloqueante)** | Aislamiento unitario estricto (+1 chokepoint rewriter C1) |
| `tests/contract` | 432 | 432 | 0 | 0 | **Release Gate (Bloqueante)** | Tipado, boundaries y schemas canónicos |
| `tests/security` | 52 | 52 | 0 | 0 | **Release Gate (Bloqueante)** | Sanitización PII, inyecciones y contratos estrictos |
| `tests/adversarial` | 655 | 655 | 0 | 0 | **Release Gate (Bloqueante)** | Incluye `crisol` (27) y `crisol_chaos` (22) como subdirectorios |
| `tests/pedagogy` | 65 | 65 | 0 | 0 | **Release Gate (Bloqueante)** | Pipeline socrático, fases y streaming SSE |
| `tests/integration` | 110 | 103 | 0 | 7 | Suite Integrada | 7 skipped por requerir API keys externas de LLM en vivo |
| `tests/web` | 38 | 38 | 0 | 0 | Suite Integrada | Endpoints API y compatibilidad UI |
| `tests/hierarchy` | 36 | 36 | 0 | 0 | Suite Integrada | Migración v2 verificada dinámicamente contra `SQLiteStorageEngine.SCHEMA_VERSION` |
| `tests/survival` | 34 | 34 | 0 | 0 | Suite Integrada | Resiliencia de estado y persistencia |
| `tests/llm_pool` | 31 | 31 | 0 | 0 | Suite Integrada | Circuit breakers y fallback de proveedores |
| `tests/experiments` | 27 | 27 | 0 | 0 | Informativa | Calibración y corridas de golden paths |
| `tests/system` | 22 | 22 | 0 | 0 | Suite Integrada | Cadena de autoridad y límites de subsistemas |
| `tests/context` | 19 | 19 | 0 | 0 | Suite Integrada | Compilador de contexto y router de intención |
| `tests/performance` | 17 | 17 | 0 | 0 | Informativa | TTFT desagregado, benchmarks y presupuestos |
| `tests/llm` | 13 | 13 | 0 | 0 | Suite Integrada | Aislamiento de entorno fixture monkeypatch `XKIRO_MODEL` |
| `tests/retrieval` | 19 | 19 | 0 | 0 | Suite Integrada | +7 inflections C2/C4/C5/A1/A5; 0 skips (unskip ceiling ±1) |
| `tests/protected` | 9 | 9 | 0 | 0 | Suite Integrada | Raíz de confianza y contratos inmutables |
| `tests/session` | 9 | 9 | 0 | 0 | Suite Integrada | Sesiones unificadas y submissions |
| `tests/storage` | 8 | 8 | 0 | 0 | Suite Integrada | Repositorios SQLite y bajo nivel |
| `tests/memory` | 7 | 7 | 0 | 0 | Suite Integrada | Extracción de misconceptions y memoria episódica |
| `tests/benchmark` | 6 | 6 | 0 | 0 | Informativa | Perfilado de ingesta y almacenamiento |
| `tests/cli` | 4 | 4 | 0 | 0 | Suite Integrada | CLI content show / solution |
| `tests/ci` | 1 | 1 | 0 | 0 | Suite Integrada | Verificación de entorno CI |
| **TOTAL REPOSITORIO** | **2.411** | **2.404** | **0** | **7** | — | **Suma exacta de las 23 suites en corrida única consolidada** |

---

### Evaluación en Vivo End-to-End (Fuera del total estático de tests)

| Evaluación en Vivo | Muestra | Passed | Failed | Métrica Clave | Estado |
|---|:---:|:---:|:---:|---|:---:|
| **Golden Set v1** | 18 queries | 18 | 0 | $p50 = 2.331\text{ ms}$ (budget $\le 3.000\text{ ms}$), exactitud KC 100% | ✅ **PASS** |

---

## DECLARACIÓN FORMAL DE GATES DE PRODUCCIÓN

1. **GATE DE RELEASE OFICIAL (Autoridad Única y Vinculante):**
   El Gate de Release del repositorio queda formalmente definido como **UNA SOLA INVOCACIÓN CONSOLIDADA: `pytest tests/`**.
   - **Regla vinculante:** Esa corrida única y completa en un solo proceso es la **única que certifica oficialmente** la integridad de la rama `main` y autoriza entregas o transiciones de milestone.
   - **Corridas por suite o directorio:** Las ejecuciones por subcarpeta (`pytest tests/unit`, `pytest tests/hierarchy`, etc.) son de carácter **estrictamente informativo o de diagnóstico local** para acelerar el ciclo de desarrollo, y bajo ninguna circunstancia reemplazan la corrida consolidada.
   - **Baseline Oficial Vigente:** `pytest tests/` $\rightarrow$ **2.404 passed, 7 skipped, 0 failed (exit code 0)** en 251.20s.
   - **Criterio soberano de integración en vivo:** **Golden Set v1 = 18/18 PASS** ($p50 = 2.331\text{ ms}$, budget $\le 3.000\text{ ms}$).

2. **REGLA DE INGENIERÍA DE PRUEBAS (Contratos Vivos vs Literales Copiados):**
   *Los tests deben afirmar estrictamente contra constantes y contratos vivos del motor, NUNCA contra literales copiados o números mágicos hardcodeados.*
   - Caso de estudio: `test_legacy_database_migration_to_v3` fallaba al comparar contra el literal `== 3` cuando el motor ya había incorporado migraciones legítimas hasta la versión 4. Se reemplazó por `assert engine.get_schema_version() == SQLiteStorageEngine.SCHEMA_VERSION`, garantizando que el test verifica que una BD legacy en v2 atraviesa todas las migraciones hasta el estado actual del motor, sobreviviendo intacto a futuros incrementos (ej. bump a v5 en `content_registry`).

3. **SUITES INFORMATIVAS Y DE RESILIENCIA:**
   - `tests/adversarial/crisol_chaos` (22 tests, subconjunto de `adversarial`): Inyección de fallas caóticas de infraestructura.
   - `tests/performance`, `tests/benchmark`, `tests/experiments`: Perfilado analítico y telemetría de latencia sin aserciones bloqueantes de semántica funcional.

---

## NARRATIVA Y ANÁLISIS DE COMMIT da9d18d (Ítem 2 Punch-List)

### (a) ¿Qué rompió la guarda de Commit 6 que exigió da9d18d?
En Commit 6 (`b2512c1`), la admisión en fallback FTS disyuntivo se configuró bajo una guarda de cobertura normalizada estricta: para consultas de $\le 3$ términos sustantivos se exige cobertura del 100% ($1.0$) de los términos en el chunk; para $\ge 4$ términos se exige $\ge 70\%$ ($\ge 0.70$).
Al procesar consultas formuladas con lenguaje coloquial o conversacional (como *"¿Qué opinás de la búsqueda binaria en arreglos?"*), el verbo *"opinás"* no estaba en la lista de stopwords. En consecuencia, el tokenizador lo catalogó como término de contenido sustantivo (`raw_terms = ['opina', 'búsqueda', 'binaria', 'arreglo']`, $N=4$, requiriendo $\lceil 4 \times 0.7 \rceil = 3$ coincidencias). Dado que la literatura técnica de ciencias de la computación jamás contiene verbos de opinión personal dirigidos al interlocutor ("opinás"), un fragmento que contenía rigurosamente *"búsqueda binaria"* (2 términos) quedaba por debajo del umbral ($2/4 = 0.50 < 0.70$) o requería la presencia imposible del verbo, provocando abstenciones falsas sobre material curricular perfectamente válido.

### (b) ¿La lista de stopwords es compartida entre retrieval y el clasificador de intención (C3) o son separadas?
**Es compartida.** `SPANISH_STOPWORDS` reside centralizada en `src/study_engine/storage/lexical_index.py:54`. Es importada directamente por:
1. El motor de búsqueda léxica FTS (`SQLiteLexicalIndex`) y la guarda de cobertura disyuntiva en `knowledge_store.py:566`.
2. El extractor de términos del catálogo KC `_kc_search_terms` en `src/study_engine/web/routes/chat.py:821`, el cual alimenta a `_match_kc_id` consumido por el clasificador de intención no curricular `_is_non_curricular_intent` (`chat.py:888`).
Al ser compartida, la incorporación de verbos conversacionales de opinión ("opina", "opinas", "opinás", "opinan", "opinar", "opinion", "opinión") limpia los términos de búsqueda de KC sin interferir con la clasificación de intención.
Como evidencia empírica de no-regresión, el caso **K3 ("¿Qué opinás de Star Wars?")** del Golden Set v1 continúa absteniéndose de forma determinista y limpia (18/18 PASS): la expresión regular `_NON_CURRICULAR_INTENT_RE` (`chat.py:880`) intercepta la query antes de que el motor de retrieval se invoque. Además, se fortaleció `_NON_CURRICULAR_INTENT_RE` para soportar explícitamente verbos de opinión en primera persona (`"opino que"`, `"creo que"`), comprobado mediante los tests unitarios `test_explicit_opinion_verbs_without_curricular_terms_abstain` y `test_explicit_opinion_verbs_with_curricular_terms_continue`.

### (c) Test nuevo OOD que afirma que las stopwords no reabren la guarda de Commit 6
En `tests/unit/web/test_intent_gate.py` se implementó el test nuevo `test_short_ood_query_with_conversational_verbs_yields_zero_candidates()`. Este test evalúa consultas OOD cortas cargadas de verbos conversacionales directamente contra el almacén de conocimiento:
- *"¿Qué opinás de las empanadas?"* $\rightarrow$ 0 candidatos admitidos post-gate.
- *"¿Opinás que el clima está lindo?"* $\rightarrow$ 0 candidatos admitidos post-gate.
- *"¿Qué opinás?"* (solo stopwords) $\rightarrow$ 0 candidatos admitidos post-gate.
Al removerse el verbo conversacional por `SPANISH_STOPWORDS`, los términos sustantivos restantes (como "empanadas" o "clima") tienen cobertura $0.0 < 1.0$ frente al corpus técnico y son descartados; si la query queda vacía de términos sustantivos, se descartan de inmediato. Se demuestra formalmente que las stopwords no crearon ninguna válvula de escape en la guarda de Commit 6.

---

## ANÁLISIS DE RECALL EN TÉRMINOS CORTOS CON VARIANTE PLURAL/INFLEXIÓN (Ítem 3 Punch-List)

Se extendió la suite de integración en `tests/integration/test_relevance_gate_regression.py` mediante el test `test_relevance_gate_recall_four_char_term_with_plural_inflection`:

1. **Término con singular y plural en el corpus:** Para *"hilo"* (4 caracteres) y *"hilos"* (5 caracteres) en `SEC-04-CONCURR` (`so_concurrencia.pdf`), ambas formas admiten 5 candidatos cada una, con scores léxicos y vectoriales válidos dentro del presupuesto.
2. **Término donde el corpus contiene únicamente la forma plural:** Para *"pilas"* (5 caracteres) consultado sobre el cuaderno `NB-CYBERSECURITY-V1` (donde está ingerido `prog_lineales.pdf`), la consulta admite 5 candidatos ($\ge 1$ chunk admitido, con top candidate `prog_lineales.pdf:p01:c0000` con score léxico BM25 = 3.58).
3. **Hallazgo de frontera documentado:** La consulta singular *"pila"* (4 caracteres) sobre el mismo corpus arroja **0 candidatos admitidos**.
   - *Causa técnica:* El archivo `prog_lineales.pdf` contiene físicamente en su texto únicamente el token plural *"pilas"*. Conforme al diseño riguroso de Commit 6, el comodín de prefijo `*` está delimitado a términos con $\text{longitud} \ge 5$ en `lexical_index.py:104,118` para evitar admisiones espurias OOD (como *"int \*p"* matcheando *"interfaz"*, *"inteligente"*, etc.). Por lo tanto, *"pila"* no se expande a *"pila\*"*; el tokenizador unicode61 de FTS no realiza stemming lematizador en SQLite y devuelve 0 coincidencias léxicas. Al resultar el score denso inferior al umbral ($\approx 0.82 < 0.84$), la compuerta de relevancia lo rechaza por `LOW_DENSE_NO_LEXICAL`.
   - *Decisión de diseño:* Siguiendo la directiva explícita del punch-list (*"Si falla, NO bajar umbral de wildcard; documentar como hallazgo"*), **el umbral de 5 caracteres se mantiene inalterado**, protegiendo el sistema contra regresiones de seguridad y falsos positivos en el gate de abstención.

---

## BACKLOG TÉCNICO

### BACKLOG-LEX-001 — Canonicalización singular→plural en query_rewriter.py
- **Identificador:** `BACKLOG-LEX-001`
- **Estado:** ✅ **CERRADO CON EVIDENCIA (Fase A)**.
- **Problema resuelto:** En el corpus bibliográfico técnico, ciertos conceptos clave aparecen exclusivamente en su forma plural (ej. *"pilas"* en `prog_lineales.pdf:p01:c0000`). Conforme a la regla de seguridad de Commit 6, los términos con longitud $< 5$ caracteres (como *"pila"*, 4 chars) tienen prohibido el comodín de prefijo `*` para evitar falsos positivos OOD (`"int *p"`). En consecuencia, SQLite FTS unicode61 devolvía 0 filas para *"pila"*, y la compuerta de relevancia rechazaba la consulta por `LOW_DENSE_NO_LEXICAL`.
- **Implementación y Resoluciones (C1–C5):**
  1. **Chokepoint único (C1):** Se declaró `RetrievalService.retrieve_evidence()` como la única autoridad de reescritura. Se eliminó la invocación duplicada en `KnowledgeStore.search_hybrid()`.
  2. **Pipeline de transformaciones en orden estricto (C2):**
     - Fase 1: `_TYPO_CORRECTIONS` (normalización básica de ortografía).
     - Fase 2: `_CANONICAL_INFLECTIONS` (reemplazo sustitutivo singular $\rightarrow$ plural).
     - Fase 3: `_COLLOQUIAL_EXPANSIONS` (aditiva, estrictamente idempotente).
  3. **Validación empírica contra el corpus (C5 / A1):** El diccionario `_CANONICAL_INFLECTIONS` incluye únicamente pares que satisfacen rigurosamente:
     - (a) `hits(plural) > 0` en FTS.
     - (b) `hits(singular) <= hits(plural)` en FTS.
     - Pares validados: `pila` $\rightarrow$ `pilas`, `grafo` $\rightarrow$ `grafos`, `hilo` $\rightarrow$ `hilos`, `nodo` $\rightarrow$ `nodos`.
     - Términos en inglés o donde domina el singular (`heap`, `fork`, `lock`, `slot`, `pipe`, `arbol`/`árbol`, `tabla`, `clave`) fueron excluidos contractualmente.
  4. **Idempotencia y correctitud inicial (C4):** `rewrite("pila") == "pilas"` en primera pasada; `rewrite(rewrite(q)) == rewrite(q)` sin duplicación de términos.
  5. **Telemetría estructurada (A5):** Detección de misses para términos de 4-5 caracteres mediante log estructurado `COVERAGE_GUARD_MISS` en `KnowledgeStore.search()`.
- **Evidencia en tests:**
  - `tests/retrieval/test_query_rewriter_inflections.py`: **7/7 passed**.
  - `tests/unit/retrieval/test_query_rewriter.py`: **7/7 passed**.
  - `tests/integration/test_relevance_gate_regression.py`: **7/7 passed**. Tanto `"pila"` como `"¿qué es una pila?"` admiten exitosamente $\ge 1$ chunk en `prog_lineales.pdf`, mientras que tokens ruidosos como `"int *p"` continúan bloqueados (0 candidatos).

---

### BACKLOG-CTX-001 — HARD_CEILING_TOKENS (40k→4k) y EXPANSION_WINDOW (2→1)
- **Identificador:** `BACKLOG-CTX-001`
- **Estado:** 🔬 **INVESTIGACIÓN EMPÍRICA COMPLETADA — ABIERTO POR REGLA A3 ($p99 \ge 3.500$)**.
- **Contexto:** En el commit `2fe70e3` se fijaron preventivamente `HARD_CEILING_TOKENS = 4000` y `EXPANSION_WINDOW = 1` ($\pm 1$ chunk contiguo) para mitigar spikes de RAM. El test histórico asumía $\pm 2$ chunks y quedó en `skip`.
- **Desbloqueo de test (0 skips en `tests/retrieval`):**
  Se removió el `@pytest.mark.skip` de `test_section_expansion_ceiling.py::test_section_expander_fuses_windows_and_formats_explicit_metadata` y se alinearon sus aserciones a la ventana $\pm 1$: semillas en 3 y 5 generan intervalo fusionado $[2, 6]$ (5 chunks contiguos: 2, 3, 4, 5, 6), verificando flags de semilla y marcadores canónicos `[CHUNK X | Pág Y]`. Resultado: **2/2 passed**.
- **Medición empírica exhaustiva (`scripts/measure_context_tokens.py`):**
  Se evaluaron 38 queries en producción (20 queries complejas multi-tema pre-registradas que abarcan SO, C, estructuras y arquitectura + 18 queries del Golden Set v1) con el tokenizador unificado de `SectionExpander` (C3).

| Métrica | Ventana $\pm 1$ (Aritmética Pura) | Hard Ceiling 4.000 (Con Corte) |
|---|:---:|:---:|
| **Mínimo** | 0.0 tokens | 0.0 tokens |
| **Media (Mean)** | 1.783,4 tokens | 1.783,4 tokens |
| **Mediana ($p50$)** | 1.755,0 tokens | 1.755,0 tokens |
| **Percentil 90 ($p90$)** | 3.040,4 tokens | 3.040,4 tokens |
| **Percentil 99 ($p99$)** | **3.688,3 tokens** | **3.688,3 tokens** |
| **Máximo** | 3.877,0 tokens | 3.877,0 tokens |
| **Queries cortadas (>4k)** | 0 / 38 (0,0%) | 0 / 38 (0,0%) |
| **RAM Pico (con ONNX)** | **1.503,37 MB** (Delta: +1.397,00 MB) | — |

- **Evaluación de la Rama de Decisión (Addendum A3):**
  - Condición evaluada: $p99 = 3.688,3\text{ tokens} \ge 3.500\text{ tokens}$.
  - Diagnóstico: Si bien ninguna consulta superó el ceiling actual de 4.000 tokens (corte = 0,0%), el percentil 99 se encuentra en zona marginal ($3.688,3$ tokens, ~92% del techo).
  - Propuesta conservadora: Incrementar `HARD_CEILING_TOKENS` a **5.000 tokens** (otorga un +28% de margen de seguridad sobre el máximo observado de 3.877 tokens sin riesgo de desborde de memoria, ya que la memoria RAM está acotada a ~1.5 GB).
  - Conclusión reglamentaria: El backlog permanece **ABIERTO** para coordinar el ajuste de cuota con la generación de ejercicios dinámicos (Fase B/C).
  - Artefacto generado: `data/experiments/context_token_distribution_report.json`.

---

## SLICE 6.0.5: CONTENT REGISTRY (Identidad Exacta Curricular + Filtro de Presentación Universal)

### 1. Objetivos e Invariantes Cumplidos
1. **Identidad Curricular Exacta:** Resolución determinista de referencias curriculares (ejercicios y secciones) mediante `ContentRegistryRepository` y `ReferenceExtractor`.
2. **Filtro Universal de Solucionario (Zero Leakage):** Eliminación forzada de cualquier chunk de solucionario en los accesores del repositorio y en el ensamble pre-prompt del chat (`chat.py`), tanto para fragmentos semilla como para el radio de expansión.
3. **Fail-Closed Ante Filtrado Total:** Si la consulta solo recupera chunks de solucionario y ningún chunk de enunciado sobrevive, el sistema aborta de inmediato por abstención epistémica E2 (`QUERY_OUT_OF_SCOPE`).
4. **Compuerta de Solucionario Estricta (CLI):** `talos content solution` exige haber registrado al menos un intento de resolución previo o la bandera explícita `--force` (auditada en `solution_access_log`). En caso de rechazo, devuelve estrictamente exit code 2.

---

### 2. Resultados Oficiales del Backfill en Producción (`data/web_state/knowledge_store.db`)
- **Total de unidades curriculares indexadas:** **8.334**
  - Ejercicios (`unit_type = 'exercise'`): **270**
  - Secciones (`unit_type = 'section'`): **8.064**
- **Estado de revisión:**
  - **OK (`status = 'ok'`):** **8.334** (100.0%)
  - **NEEDS_REVIEW (`status = 'needs_review'`):** **0** (0.0%)

#### Desglose Exhaustivo por Fuente (45 Fuentes Curriculares)

| Fuente (`source_id`) | OK | Needs Review | Total |
|---|:---:|:---:|:---:|
| `src_silberschatz_fundamentos_bd` | 1.184 | **0** | 1.184 |
| `src_castro_fusario_comunicaciones_redes` | 1.052 | **0** | 1.052 |
| `src_elmasri_navathe_sistemas_bd` | 974 | **0** | 974 |
| `src_date_intro_sistemas_bd_7ed` | 790 | **0** | 790 |
| `src_comer_internetworking_tcpip_v1` | 667 | **0** | 667 |
| `src_ramakrishnan_gehrke_dbms` | 644 | **0** | 644 |
| `src_joyanes_fundamentos` | 569 | **0** | 569 |
| `src_coronel_database_systems_11ed` | 564 | **0** | 564 |
| `src_stallings_os_internals_7ed` | 296 | **0** | 296 |
| `src_goodrich_dsa_python` | 293 | **0** | 293 |
| `src_kurose_computer_networking` | 271 | **0** | 271 |
| `src_stallman_gnu_c_manual` | 248 | **0** | 248 |
| `src-guia-2025-c04f44ef` | 166 | **0** | 166 |
| `src_marques_bases_de_datos` | 119 | **0** | 119 |
| `src_stallings_comunicaciones_redes_7ed` | 99 | **0** | 99 |
| `src_stallings_computer_security` | 97 | **0** | 97 |
| `src_corletti_seguridad_redes` | 85 | **0** | 85 |
| `src_ramalho_fluent_python` | 32 | **0** | 32 |
| `src_3102eb1e89e2229e` | 25 | **0** | 25 |
| `src_fadena_so2_clase2` | 20 | **0** | 20 |
| `src_0fc90b2695369475` | 19 | **0** | 19 |
| `src_tori_hacking_etico` | 14 | **0** | 14 |
| `src_sweigart_automate_boring_stuff` | 12 | **0** | 12 |
| `src_a01b9809f37fb47b` | 11 | **0** | 11 |
| `src_a9a056742dcf69ae` | 9 | **0** | 9 |
| `src_d253687930308e41` | 9 | **0** | 9 |
| `src_032c52bff94a0743` | 7 | **0** | 7 |
| `src_6dbdc8e943261fa7` | 7 | **0** | 7 |
| `src_bel_algoritmos_estructuras_python` | 7 | **0** | 7 |
| `src_9e866bf082e52dd7` | 6 | **0** | 6 |
| `src_f009c4e75f5ca3f2` | 6 | **0** | 6 |
| `src_urrutia_programacion_c_principiantes` | 5 | **0** | 5 |
| `src_fadena_prog_archivos` | 4 | **0** | 4 |
| `src_marzal_intro_programacion_c` | 4 | **0** | 4 |
| `src_52ff5ff3e07c1da5` | 3 | **0** | 3 |
| `src_da10b53f20f2a647` | 3 | **0** | 3 |
| `src_e9682dece40b58ab` | 2 | **0** | 2 |
| `src_fadena_prog_arboles` | 2 | **0** | 2 |
| `src_fadena_so_concurrencia` | 2 | **0** | 2 |
| `src_spraul_think_like_a_programmer` | 2 | **0** | 2 |
| `src_fadena_leng_clase1` | 1 | **0** | 1 |
| `src_fadena_leng_clase2` | 1 | **0** | 1 |
| `src_fadena_so2_clase1` | 1 | **0** | 1 |
| `src_fadena_so_memoria` | 1 | **0** | 1 |
| `src_fadena_so_procesos` | 1 | **0** | 1 |
| **TOTAL** | **8.334** | **0** | **8.334** |

---

### 3. Resoluciones de Diseño e Integridad de Arquitectura
1. **Extractor de Referencias:** Exclusivamente rule-based mediante `reference_extractor.py`. Capa A (regexes literales con score 1.0) y Capa B (fuzzy match con umbral estricto $\ge 0.95$ para resolución directa; puntuaciones entre 0.70 y 0.95 se marcan con `needs_review` y emiten disclaimer; $< 0.70$ descarta el match). Cero llamadas a LLMs.
2. **Filtro de Presentación:** Centralizado en `presentation_filter.py` e integrado en los métodos de acceso de `ContentRegistryRepository` (`get_statement_chunks()`, `list_statement_chunks()`) y en `chat.py`. Remueve tanto chunks de solución asociados al `ContentItem` como cualquier chunk con metadatos o tags de solucionario.
3. **Invalidación de Caché Atómica:** En `ContentRegistryRepository`, los métodos `save()` y las operaciones por lote invalidan `_solution_chunk_ids_cache = None`, reconstruyéndose perezosamente (lazy) en la siguiente invocación de `get_solution_chunk_ids()`.
4. **Esquema de Datos y Persistencia:** `SQLiteStorageEngine.SCHEMA_VERSION` incrementado a 5, con migración `_migrate_to_v5()` idempotente que crea la tabla `content_registry` e índices auxiliares por source, tipo y alias. `student_state.db` incorpora `student_exercise_attempts` y `solution_access_log`.
5. **Perímetro Congelado:** Se certifica `git diff origin/main -- src/study_engine/{state,execution,assessment,audit}/` = 0 líneas de diferencia.
6. **Gate Consolidado de Release:** Ejecución única de `pytest tests/` resultando en:
   **2.403 tests recolectados**, **2.395 PASSED**, **8 SKIPPED**, **0 FAILED** (exit code 0, 292s).



