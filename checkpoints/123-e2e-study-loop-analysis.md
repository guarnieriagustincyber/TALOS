# CHECKPOINT 123 — ANÁLISIS E INVESTIGACIÓN PROFUNDA DE INTEGRACIÓN E2E DEL STUDY LOOP

**Checkpoint:** `checkpoints/123-e2e-study-loop-analysis.md`  
**Directiva:** `DIRECTIVA — E2E STUDY LOOP INTEGRATION (FASE 0 — ANÁLISIS E INVESTIGACIÓN PROFUNDA)`  
**Subdominio:** V1 / Study Loop / Integración End-to-End  
**Tipo:** Investigación operacional, arqueología de código, análisis de contratos y diseño de pruebas  
**Estado:** FASE 0 COMPLETADA — NO IMPLEMENTAR  
**Fecha:** 2026-10-03  

---

## 1. ESTADO DE GOBERNANZA Y MÉTRICAS

```text
CP120_STATUS = CLOSED
CP121_STATUS = CLOSED
CP122_FINAL = PASS

CONTEXT_PACK_STATUS = DEFERRED_POST_V1
SUFFICIENCY_GATE_STATUS = DEFERRED_POST_V1

E2E_RESEARCH = COMPLETE
STUDY_LOOP_RECONSTRUCTION = COMPLETE
CONTRACT_MATRIX = COMPLETE
E2E_TEST_PLAN = PROPOSED
IMPLEMENTATION = NOT_STARTED

PRODUCTION_STATUS = UNCHANGED
DATABASE_CHANGES = 0

V1_BLOCKERS_FOUND = 0
V1_VALIDATION_GAPS = 1
P2_NONBLOCKING_DEFECTS = 2
P3_DOCUMENTATION_ITEMS = 1
POST_V1_ITEMS_FOUND = 7
NOT_A_BUG_ITEMS = 3
UNKNOWN_ITEMS = 0

DICTAMEN = D — READY_WITH_KNOWN_NONBLOCKING_GAPS
```

---

## 2. RESUMEN EJECUTIVO DE LA INVESTIGACIÓN

En cumplimiento de la **FASE 0**, se realizó una reconstrucción profunda, empírica y documental del **Study Loop real de TALOS V1**, analizando sus puntos de entrada HTTP, cadenas de llamadas internas, contratos epistémicos, modelos psicométricos y esquemas de persistencia SQLite.

Se determinó que el Study Loop de TALOS V1 está plenamente estructurado en torno a dos ejes coordinados:
1. **Flujo de Sesión y Progresión Curricular (`/api/study/session/*`):**  
   100% determinista, gobernado por `ProgressionPolicy`, resolviendo la elegibilidad y el posicionamiento de KCs mediante el DAG curricular y priors BKT, sin participación de LLMs en la apertura ni en la construcción del brief de partida.
2. **Flujo Epistémico Socrático y de Consulta (`/api/chat/query`):**  
   Protegido por chokepoints deterministas:
   * **C2 / L3 ACL:** Filtro de fuentes estrictamente autorizadas para el cuaderno.
   * **FTS5 BM25:** Búsqueda textual pura de alto rendimiento sobre `knowledge_store.db` (vectorial 1024d y reranker diferidos a Post-V1).
   * **C3 Hard Ceiling:** Presupuesto jerárquico acotado a $\le 2.000$ tokens nominales de evidencia ($\le 4.761$ tokens totales efectivos).
   * **C5 Trust Gate:** Evaluación pre-LLM que se abstiene fail-closed si la cobertura léxica es insuficiente, sin emitir llamadas a proveedores ni permitir alucinaciones.
   * **MultiFallbackBackend:** Cascada con degradación controlada hasta `OfflinePedagogicalBackend`.
   * **C1 Provenance:** Validación estricta de citas en tiempo real mediante `StreamCitationBuffer`.
3. **Flujo de Evaluación y Psicométrica BKT (`/api/chat/evaluate` y `/api/student/exercises/*/verify`):**  
   La actualización del modelo cognitivo $P(L)$ está **deliberadamente aislada del chat conversacional** como decisión arquitectónica anti-gaming, restringiéndose exclusivamente a evaluaciones formales con oráculos deterministas.
4. **Flujo de Práctica de Código (`/api/practice/evaluate`):**  
   Retorna de forma segura y controlada `EvaluationStatus.PRACTICE_UNAVAILABLE` fail-closed, dado que el sandbox de ejecución real (S6) está formalmente diferido para Post-V1.

---

## 3. ENTREGABLES PRODUCIDOS

Se generaron los cuatro informes normativos requeridos en `reports/e2e_study_loop/`:

1. **[`STUDY_LOOP_ARCHAEOLOGY.md`](../reports/e2e_study_loop/STUDY_LOOP_ARCHAEOLOGY.md):**  
   Reconstrucción de las 13 transiciones del ciclo de estudio, auditoría de 6 entrypoints HTTP, respuesta a las 10 preguntas fundamentales de progresión, trazabilidad de persistencia, arqueología de código desconectado (`SessionOrchestrator`, `RetrievalFabricLite`, `LabGraderBridge`) y matriz de failure modes.
2. **[`STUDY_LOOP_CONTRACT_MATRIX.md`](../reports/e2e_study_loop/STUDY_LOOP_CONTRACT_MATRIX.md):**  
   Matriz integral que mapea la implementación, integración, tests unitarios, de integración y E2E de los 13 contratos de TALOS (C1–C5, FTS5, BKT, Curriculum, Adaptivity, Grounding, SSE, Memory, Anti-leak) e invariantes I-01 a I-08.
3. **[`E2E_TEST_PLAN.md`](../reports/e2e_study_loop/E2E_TEST_PLAN.md):**  
   Definición del Minimum Viable Study Loop (MVSL), catálogo de 13 assertions cuantitativas (`AST-SES-01` a `AST-MEM-01`), especificación de 7 casos de prueba E2E (Happy path, OOD abstention, L3 ACL rejection, Retrieval failure, Provider failure, Memory continuity, Practice contract), principios de "No E2E Teatral" y estrategia de aislamiento con bases de datos temporales.
4. **[`E2E_GAP_REGISTER.md`](../reports/e2e_study_loop/E2E_GAP_REGISTER.md):**  
   Inventario clasificado con 0 bloqueantes P0, 1 gap de validación P1 (la suite E2E en sí misma), 2 defectos leves P2 de aislamiento de tests, 1 item P3 documental, 7 capacidades diferidas Post-V1 y 3 comportamientos confirmados como contractuales (`NOT_A_BUG`).

---

## 4. RESOLUCIÓN DE DRIFTS Y TESTS HISTÓRICOS

Durante la investigación se analizó el fallo del test histórico:
```text
tests/integration/test_web_api.py::test_socratic_practice_dispatch_endpoint
```
Se demostró que el test enviaba una consulta de práctica sin evidencia curricular suficiente (`/practicar punteros` en `fadena-lenguajes`) esperando generación de tokens. El C5 Trust Gate implementado con posterioridad en Gate B (CP111) interceptó la falta de sustento léxico y emitió un evento `abstention` fail-closed.  
**Resolución:** Se clasifica como `CONTRACT_DRIFT / OBSOLETE_TEST`. La respuesta de TALOS fue epistemológicamente correcta conforme al contrato C5 vigente.

---

## 5. DICTAMEN FINAL

Conforme a la Sección 27 de la directiva, se emite el dictamen formal:

### **DICTAMEN: D — READY_WITH_KNOWN_NONBLOCKING_GAPS**

### Justificación Basada en Evidencia:
1. **Claridad Arquitectónica:** Los contratos del Study Loop V1 están perfectamente delimitados, implementados y conectados en el runtime.
2. **Cero Bloqueantes V1:** No se detectó ningún gap P0 que impida la ejecución funcional de punta a punta.
3. **Gaps Conocidos No Bloqueantes:**
   * La falta de sandbox S6 en `/api/practice/evaluate` es un comportamiento contractual `PRACTICE_UNAVAILABLE` certificado para Post-V1.
   * La desconexión del BKT en el chat conversacional es un invariante de diseño normativo anti-gaming.
   * La búsqueda vectorial en chat y los rerankers están desacoplados en favor de FTS5 BM25 por diseño de estabilidad y latencia en CPU.
4. **El Único Paso Restante:** Construir la suite E2E especificada en el plan para certificar formalmente el release de V1.

---

## 6. CONDICIÓN DE INTEGRIDAD FÍSICA

Se confirma el cumplimiento absoluto de las reglas de no-modificación de producción:

```text
RUNTIME_MODIFIED = FALSE
PRODUCTION_DB_MODIFIED = FALSE
CORPUS_MODIFIED = FALSE
VECTOR_STORE_MODIFIED = FALSE
STUDENT_STATE_MODIFIED = FALSE
NEW_FEATURES = FALSE
POST_V1_INTEGRATION = FALSE
```

* Base de datos de conocimiento (`knowledge_store.db`): `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (Inmutable).
* Modificaciones de código en producción: 0 líneas.
* Modificaciones de esquemas o tablas: 0.
