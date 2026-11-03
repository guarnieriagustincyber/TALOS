# Checkpoint 146-R1: Reconciliación Canónica de la Adjudicación de Promotabilidad de Fase 1 (Promotion Gate Assessment)

**Fecha:** 2026-10-05T17:05:00-03:00  
**Fase:** FASE 1 — EVIDENCE RETRIEVAL / SUBFASE 1E — PROMOTION GATE  
**Tipo de Documento:** CHECKPOINT DE RECONCILIACIÓN DE GOBERNANZA Y PROMOTABILIDAD  
**Autoridad:** Directiva Canónica CP146-R1 — Reconciliación del Promotion Gate / Antigravity Agent  
**Predecesores Directos:**
* Checkpoint 146 (`checkpoints/146-phase-1e-promotion-gate.md`)
* Checkpoint 145-R1 (`checkpoints/145-r1-reconciliacion-dictamen-fase-1d.md`)
* Checkpoint 144 (`checkpoints/144-fase-1d-ejecucion-benchmark-retrieval.md`)
* Checkpoint 142 (`checkpoints/142-fase-1c-ejecucion-frontera-corpus-runtime.md`)
* Checkpoint 140 (`checkpoints/140-reconciliacion-canonica-fase-1b.md`)
* Checkpoint 133 (`checkpoints/133-formalizacion-gate-1a-1b.md`)
* Checkpoint 131 (`checkpoints/131-fase-1a-final-synthesis.md`)  
**Estatus Canónico:** **`FASE_1E = CANONICALLY_CLOSED | PHASE_1_PROMOTABLE = FALSE | PROMOTION = NOT_AUTHORIZED`**  
**Gobernanza:** `PROMOTION = NOT_AUTHORIZED | PHASE_2 = BLOCKED | FASE_2.X = NOT_AUTHORIZED`  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`

---

## 1. ESTADO DE GOBERNANZA RECONCILIADO

```text
===============================================================================
TALOS V1.5 — CHECKPOINT 146-R1: PHASE 1E PROMOTION GATE RECONCILIATION
===============================================================================

PHASE_1A                        = COMPLETE / CLOSED (CP131)
GATE_1A_1B                      = FORMALIZED / CLOSED (CP133)
FASE_1B                         = COMPLETE / CANONICALLY CLOSED (CP140)
FASE_1C                         = COMPLETE / CERTIFIED (CP142)
FASE_1D                         = COMPLETE / CANONICALLY CLOSED (CP145-R1)
FASE_1E                         = ADJUDICATED / CANONICALLY CLOSED (CP146-R1)
  ├─ PRE-AUDITORÍA INTEGRIDAD   = PASSED (11/11 artefactos primarios verificados)
  ├─ BASES DE PRODUCCIÓN        = 6/6 INTACTAS (DATABASE_CHANGES = 0)
  ├─ RUNTIME TALOS V1           = INALTERADO (V1_RUNTIME_MODIFIED = FALSE)
  ├─ ADJUDICACIÓN DE CANDIDATOS = C0..C7 EVALUADOS BAJO COMPUERTAS G1..G7
  │   ├─ C0 (FTS5 BM25)         = BASELINE RETAINED (Control histórico de V1 preservado)
  │   ├─ C1 (Dense Qwen)        = DEFER (Calibrable H4 pero sin guard integrado ni suficiencia)
  │   ├─ C2 (Dense BGE)         = DEFER (Mejora ranking pero sin suficiencia demostrada)
  │   ├─ C3 (Dense E5)          = REJECT (Degradación de ranking frente a C0)
  │   ├─ C4 (FTS5+Qwen RRF)     = DEFER (Mejor nDCG@5 y latencia 0.02ms, pero H3 inconcluso)
  │   ├─ C5 (RRF -> BGE Rerank) = REJECT (No promovible bajo contrato de Fase 1)
  │   ├─ C6 (C5 + Exp. Struct.) = REJECT (No promovible bajo contrato de Fase 1)
  │   └─ C7 (C6 + Guard t=0.35) = REJECT (FRR_ID=94.4% masivo y latencia p95=1840ms >> 150ms)
  └─ DICTAMEN SUBSISTEMA FASE 1 = PHASE_1_PROMOTABLE = FALSE (Ningún candidato apto)

PROMOTION_TO_PRODUCTION         = NOT_AUTHORIZED
PRODUCTION_SELECTION            = NOT_PERFORMED
FASE_2 (PEDAGOGÍA)              = BLOCKED (Regla de Secuencia: sin nuevo sustrato promovido)
FASE_2.X (MODELOS DECISIÓN EST) = CANDIDATE / NOT_AUTHORIZED (CP138)

===============================================================================
```

---

## 2. MODIFICACIONES DOCUMENTALES INTRODUCIDAS EN CP146-R1

En estricta observancia de la directiva de reconciliación documental, se fijan cuatro clarificaciones epistemológicas y de gobernanza:

1. **Aclaración Canónica de $ (FTS5 BM25):** Se explicita su condición de `CONTROL / BASELINE` histórico de TALOS V1. $ no está sujeto a una decisión de sustitución por sí mismo;  = 	ext{NOT\_APPLICABLE}$ y su veredicto final es unívocamente `BASELINE_RETAINED`.
2. **Corrección Epistemológica de la Condición Futura sobre $:** Se elimina cualquier fijación de  \ge 5$ como objetivo de diseño ex-ante (evitando el target-painting metodológico) y se adopta la formulación formal:
   > *"Diseñar una futura evaluación con un tamaño muestral previamente justificado que permita evaluar H1 con potencia estadística suficiente, sin fijar ex ante un número de discordancias objetivo."*
3. **Acotamiento Contractual de Conclusiones sobre $ y $:** Se restringe la calificación de no-promotabilidad estrictamente a las condiciones evaluadas en este benchmark y al contrato de Fase 1:
   > *"No son promovibles bajo el contrato de Fase 1 y las condiciones evaluadas en este benchmark."*
4. **Síntesis Estratégica Fundamental:**
   > **TALOS no concluye la Fase 1 "sin retrieval". Concluye la Fase 1 sabiendo, con evidencia formal congelada, que el baseline FTS5 sigue siendo la opción operativa de producción y que C4 es el candidato técnicamente más promisorio para una futura línea de investigación, pero ninguno cuenta aún con autorización contractual para sustituirlo.**

---

## 3. INMUTABILIDAD Y PRE-AUDITORÍA DE INTEGRIDAD CRIPTOGRÁFICA

Se certifica mediante cómputo directo de SHA-256 la correspondencia bit a bit de todos los artefactos primarios congelados:
* `phase1d_raw_execution_results.json`: `86eb541ffbd1de66a4d092be472bcd2cc09c0f09580097a872965b676ad155e1` (MATCH)
* `phase1d_per_query_results.json`: `2c496bb8a87e32cd65d17d1ed0c210511c2b26cd4acac37fb397015db4fa3f50` (MATCH)
* `phase1d_aggregate_metrics.json`: `9cb4b9cd38604f37a197e712d0a48aaa69f4787647ea5cab0cc6c4f2b84ac592` (MATCH)
* `phase1d_hypotheses_evaluation.json`: `fa503edacc918e73b764b165ff275e345b8b710c13577e6bb03db0aa27d068ae` (MATCH)
* `phase1d_negative_controls.json`: `8f8cefdb462c99547ad6507862b213c29d7a6281de6b5fc017030eaee2762f1c` (MATCH)
* `PHASE_1D_BENCHMARK_EXECUTION_MANIFEST.json`: `f4a3fe9c670f38684c1e96d8fb43964724087edf67ce401a4cee57ef68a541bc` (MATCH)
* `benchmark_queries.json`: `e15d5106ea2a14964572485be3b6e06145d4e4b0a6aa2e0c9e27d23de1b7d90c` (MATCH)
* `QREL_1D_BASELINE.json`: `ed1c1f30ab87ef64b0c1647b8d6cef9ddc473fe0538f1d15730277568dbf38aa` (MATCH)
* `benchmark_config.json`: `50d3da8efc631e3855461ddfd1b33fcb08739b15398e5fb65ab8ff4869e14962` (MATCH)
* `CP145_R1_PHASE_1D_ADJUDICATION_RECONCILIATION.md`: `6b8da34cc97b0ba78b89a9fd44df519650091daacf80c50ae758c0da99d9756a` (MATCH)
* `PHASE_1C_CORPUS_RUNTIME_BOUNDARY_REPORT.md`: `3cf0f6a0e5f47a4f64bf9bac007e36562deba3ba7237a64f55bfe40b27d6fda2` (MATCH)
* `CP146_R1_PHASE_1E_PROMOTION_GATE_RECONCILIATION.md`: `c925b357ded23534a8f7123b6b7549edd940eb5873cc5751401cdc1f1b0d3843` (MATCH)
* Las 6 bases SQLite en `data/web_state/*.db`: 100% intactas (`DATABASE_CHANGES = 0`).
* Código fuente `src/`: inalterado (`V1_RUNTIME_MODIFIED = FALSE`).

---

## 4. MATRIZ CANÓNICA RECONCILIADA DE ADJUDICACIÓN (G1 A G7)

```text
┌────┬─────────────────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬───────────────────┐
│ ID │ Candidato Canónico      │ G1 (Rel/Suf) │ G2 (OOD Abst)│ G3 (Context) │ G4 (Proven.) │ G5 (Compat.) │ G6 (Latency) │ G7 (Determ.) │ DICTAMEN FINAL    │
├────┼─────────────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼───────────────────┤
│ C0 │ FTS5 BM25 (Control)     │ NOT_APPLIC.  │ NOT_SUPPORT. │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ BASELINE RETAINED │
│ C1 │ Dense Qwen              │ INCONCLUSIVE │ INCONCLUSIVE │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ DEFER             │
│ C2 │ Dense BGE               │ INCONCLUSIVE │ NOT_SUPPORT. │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ DEFER             │
│ C3 │ Dense E5                │ NOT_SUPPORT. │ NOT_SUPPORT. │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ REJECT            │
│ C4 │ FTS5 + Qwen RRF         │ INCONCLUSIVE │ NOT_SUPPORT. │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ DEFER             │
│ C5 │ RRF → BGE reranker      │ NOT_SUPPORT. │ NOT_SUPPORT. │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ NOT_SUPPORT. │ SUPPORTED    │ REJECT            │
│ C6 │ C5 + expansión estruct. │ NOT_SUPPORT. │ NOT_SUPPORT. │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ NOT_SUPPORT. │ SUPPORTED    │ REJECT            │
│ C7 │ C6 + guardia tau=0.35   │ NOT_SUPPORT. │ NOT_SUPPORT. │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ NOT_SUPPORT. │ SUPPORTED    │ REJECT            │
└────┴─────────────────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴───────────────────┘
```

---

## 5. DICTAMEN FORMAL POR CANDIDATO

1. **C0 (FTS5 BM25) — `BASELINE RETAINED IN PRODUCTION`:** Rol `CONTROL / BASELINE`. Punto cero contractual del runtime V1. No sujeto a sustitución por sí mismo ( = 	ext{NOT\_APPLICABLE}$). Permanece como motor de producción activo.
2. **C4 (FTS5 + Qwen RRF) — `DEFER`:** Máxima eficiencia ( = 0.02	ext{ ms}$) y mayor $	ext{nDCG}@5$ (bash.1429$, $+28.6\%$). Sin embargo, empató en $	ext{MRR}@5 = 0.1667$ frente al baseline mono-modal, su suficiencia estricta fue nula (@1 = 0$) y carece de compuerta OOD integrada activa. Se defiere como el candidato técnicamente más promisorio para futuras investigaciones.
3. **C1 (Dense Qwen) y C2 (Dense BGE) — `DEFER`:** Exhiben mejora en precisión frente al BM25 (@1 = 0.1667$), pero suficiencia nula (@1 = 0$) y ausencia de guardia OOD integrada en runtime.
4. **C3 (Dense E5) — `REJECT`:** Degradación cuantitativa de ranking frente al baseline $ ($	ext{nDCG}@5 = 0.0476$ vs bash.0794$).
5. **C5 (RRF → BGE Reranker) y C6 (C5 + Expansión Estructural) — `REJECT`:** Degradan el ranking frente a retrievers directos y violan críticamente el contrato de latencia de servicio ( pprox 1840	ext{ ms} \gg 150	ext{ ms}$). En $, la expansión no aportó ganancia de suficiencia ($\Delta S = 0$ en 18/18 pares). No son promovibles bajo el contrato de Fase 1 y las condiciones evaluadas en este benchmark.
6. **C7 (C6 + Guardia $	au=0.35$) — `REJECT`:** Falso rechazo masivo del currículo ($	ext{FRR}_{	ext{ID}} = 94.4\%$) y violación de latencia ( = 1840.53	ext{ ms}$).

---

## 6. DICTAMEN GLOBAL Y REGLA DE SECUENCIA SOBRE FASE 2

```text
PHASE_1_PROMOTABLE    = FALSE
PROMOTION_TO_PROD     = NOT_AUTHORIZED
CURRENT_BASELINE      = C0 (FTS5 BM25) RETAINED IN PRODUCTION
PRODUCTION_SELECTION  = NOT_PERFORMED
DATABASE_CHANGES      = 0
V1_RUNTIME_MODIFIED   = FALSE
```

### Aplicación de la Regla de Secuencia (Roadmap Sección 2):
* **Fase 2 (Pedagogía / Explanation Quality):** Permanece formalmente **`BLOCKED / NOT_AUTHORIZED`**.
* **Fase 2.X (Modelos de Decisión Estructurada — CP138):** Permanece en estatus **`CANDIDATE / NOT_AUTHORIZED`**.
* **Runtime de Producción:** TALOS continúa operando de forma 100% estable sobre su baseline contractual $ y los contratos de frontera certificados en CP142.

---

## 7. INVENTARIO DE ARTEFACTOS Y VERIFICACIÓN CRIPTOGRÁFICA

```text
┌────────────────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────┐
│ Artefacto de Cierre CP146-R1                                           │ Hash SHA-256                                                     │
├────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│ reports/v1_5_phase1/CP146_R1_PHASE_1E_PROMOTION_GATE_RECONCILIATION.md │ c925b357ded23534a8f7123b6b7549edd940eb5873cc5751401cdc1f1b0d3843 │
│ reports/v1_5_phase1/CP146_PHASE_1E_PROMOTION_GATE_ASSESSMENT.md        │ 276d4a9a515184e8b7aafb013488f37c0940befdd827502a914f9f98eaa29ba5 │
│ reports/v1_5_phase1/CP145_R1_PHASE_1D_ADJUDICATION_RECONCILIATION.md   │ 6b8da34cc97b0ba78b89a9fd44df519650091daacf80c50ae758c0da99d9756a │
│ reports/v1_5_phase1/PHASE_1C_CORPUS_RUNTIME_BOUNDARY_REPORT.md         │ 3cf0f6a0e5f47a4f64bf9bac007e36562deba3ba7237a64f55bfe40b27d6fda2 │
│ experiments/v1_5_phase1d/execution/raw_results/phase1d_raw_execution_re│ 86eb541ffbd1de66a4d092be472bcd2cc09c0f09580097a872965b676ad155e1 │
│ experiments/v1_5_phase1d/execution/metrics/phase1d_per_query_results.js│ 2c496bb8a87e32cd65d17d1ed0c210511c2b26cd4acac37fb397015db4fa3f50 │
│ experiments/v1_5_phase1d/execution/metrics/phase1d_aggregate_metrics.j │ 9cb4b9cd38604f37a197e712d0a48aaa69f4787647ea5cab0cc6c4f2b84ac592 │
│ experiments/v1_5_phase1d/execution/metrics/phase1d_hypotheses_evaluatio│ fa503edacc918e73b764b165ff275e345b8b710c13577e6bb03db0aa27d068ae │
│ experiments/v1_5_phase1d/execution/metrics/phase1d_negative_controls.js│ 8f8cefdb462c99547ad6507862b213c29d7a6281de6b5fc017030eaee2762f1c │
└────────────────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────┘
```

La **Fase 1E queda canónica, formal y definitivamente cerrada bajo CP146-R1**.
