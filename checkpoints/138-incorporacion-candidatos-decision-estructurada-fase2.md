# Checkpoint 138: Incorporación Formal de Candidatos de Modelos de Decisión Estructurada en Fase 2 (Laya, Jev, Especializados)

**Fecha:** 2026-10-05T15:20:00-03:00  
**Fase:** FASE 2 — PEDAGOGÍA / EXPLANATION QUALITY  
**Subfase:** FASE 2.X — STRUCTURED DECISION MODELS  
**Tipo de Documento:** CHECKPOINT DE GOBERNANZA E INCORPORACIÓN DE CANDIDATOS  
**Autoridad:** Directiva de Incorporación de Candidatos de Modelos de Decisión Estructurada / Antigravity Agent  
**Predecesores:** Checkpoint 137 (`checkpoints/137-ejecucion-experimental-fase-1b.md`)  
**Estatus de la Línea:** `CANDIDATE / NOT AUTHORIZED`  
**Dependencias:** Fase 1E completada y promoción formalmente autorizada  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE`  

---

## 1. ESTADO DE GOBERNANZA

```text
===============================================================================
TALOS V1.5 — CHECKPOINT 138: STRUCTURED DECISION MODELS INCORPORATION
===============================================================================

PHASE_1A                        = COMPLETE (CP131)
GATE_1A_1B                      = FORMALIZED (CP133)
PHASE_1B                        = RESULTS_AVAILABLE / ANALYSIS_PENDING (CP137)
PHASE_1C                        = PENDING
PHASE_1D                        = PENDING
PHASE_1E                        = BLOCKED

PHASE_2                         = NOT_AUTHORIZED
FASE_2.X_STRUCTURED_MODELS      = CANDIDATE / NOT_AUTHORIZED
CANDIDATE_LAYA                  = CANDIDATE / NOT_AUTHORIZED
CANDIDATE_JEV                   = CANDIDATE / NOT_AUTHORIZED

PRODUCTION_INTEGRATION          = NOT_AUTHORIZED
V1_RUNTIME_MODIFIED             = FALSE
PRODUCTION_DB_MODIFIED          = FALSE
DATABASE_CHANGES                = 0
PRODUCTION_ISOLATION            = INVIOLABLE (Certified Bit-for-Bit)

===============================================================================
```

---

## 2. RESUMEN DE LA DIRECTIVA INCORPORADA

1. **Propósito:** Abrir formalmente en el roadmap de TALOS V1.5 una línea de investigación bajo la Fase 2 dedicada a **modelos de decisión estructurada** (Laya, modelos estilo Jev y otros clasificadores/scorers pequeños especializados) como **componentes auxiliares de decisión**, no como sustitutos del LLM narrativo.
2. **Principio Rector Inviolable:**
   > **El modelo de decisión no debe convertirse en una nueva fuente de conocimiento.**  
   > **Deterministic code first. AI second.**
3. **Separación Arquitectónica de Roles:**
   * **Knowledge:** Retrieval Fabric + ContextPack + Corpus Joyanes.
   * **Decision:** Structured Decision Model + Política Determinista de TALOS.
   * **Generation:** Narrator / LLM.
   * **Student State:** BKT / SM-2 / Motor determinista de aprendizaje (`student_state.db`).
   * *Ningún candidato podrá asumir simultáneamente más de un rol.*
4. **Tareas Preregistradas (T1 a T6):**
   * T1: Evidence Sufficiency (`SUFFICIENT`, `PARTIALLY_SUFFICIENT`, `INSUFFICIENT`).
   * T2: Abstention Decision (distinción estricta de `ID + insufficient` vs `OOD`).
   * T3: Clarification Routing (`ANSWER`, `RETRIEVE_MORE`, `ASK_CLARIFICATION`, `ABSTAIN`).
   * T4: Pedagogical Routing (`DIRECT_EXPLANATION`, `SOCRATIC_HINT`, `MICRO_EXERCISE`, etc.).
   * T5: Rubric Scoring (evaluación contra rúbrica explícita y evidencia autorizada, sin invención).
   * T6: Evidence-to-Decision Consistency (estabilidad ante permutaciones o ruido en el contexto).
5. **Reglas Metodológicas Estrictas:**
   * **Cero Integración Prematura:** Secuencia `CANDIDATE` $\to$ `AUDIT` $\to$ `TASK SPEC` $\to$ `BENCHMARK` $\to$ `EVAL` $\to$ `PROMOTION`.
   * **Baseline Determinista Primero:** Toda tarea debe contar previamente con un control determinista.
   * **Salida Estructurada Obligatoria:** JSON validado contra schema formal (enum, rangos numéricos), sin texto libre no estructurado.
   * **Control de Calibración:** Los scores de confianza no se asumirán como probabilidades sin calibración empírica demostrada.
6. **No Interferencia con Fase 1:**
   * Queda expresamente prohibido alterar la secuencia de Fase 1 (1B, 1C, 1D, 1E), introducir Laya o Jev en los runners de Fase 1, o modificar la semántica de abstención ya congelada.

---

## 3. ARTEFACTOS GENERADOS Y ACTUALIZADOS

1. **Directiva Formal:** [`reports/v1_5_phase2/STRUCTURED_DECISION_MODELS_CANDIDATE_DIRECTIVE.md`](../reports/v1_5_phase2/STRUCTURED_DECISION_MODELS_CANDIDATE_DIRECTIVE.md)
2. **Roadmap Maestro:** [`docs/ROADMAP_V1_5_MASTER.md`](../docs/ROADMAP_V1_5_MASTER.md) (Sección 6H incorporada formalmente en Fase 2).
3. **Registro de Checkpoints:** [`checkpoints/index.md`](index.md) (CP138 registrado).

---

## 4. CERTIFICACIÓN DE AISLAMIENTO

* Bases de datos en `data/web_state/`: **0 modificaciones (bit-for-bit intactas)**.
* Runtime de TALOS V1 en `src/`: **0 modificaciones (`V1_RUNTIME_MODIFIED = FALSE`)**.
* Pipeline experimental de Fase 1B: **Preservado e inalterado**.

---

## 5. PRÓXIMO PASO AUTORIZADO

1. Continuar con la secuencia autorizada de Fase 1:
   * Despacho del paquete de adjudicación ciega de Fase 1B (`blind_package.json`).
   * Consolidación de `QREL_1B_FINAL` y análisis formal de hipótesis.
2. La línea de modelos de decisión estructurada permanece en estado `CANDIDATE / NOT AUTHORIZED` hasta que se alcance formalmente la Fase 2 tras la finalización y gate de Fase 1E.
