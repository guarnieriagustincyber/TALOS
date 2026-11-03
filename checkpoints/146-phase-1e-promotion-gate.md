# Checkpoint 146: Adjudicación Formal de Promotabilidad de Fase 1 (Promotion Gate Assessment)

**Fecha:** 2026-10-05T17:00:00-03:00  
**Fase:** FASE 1 — EVIDENCE RETRIEVAL / SUBFASE 1E — PROMOTION GATE  
**Tipo de Documento:** CHECKPOINT DE ADJUDICACIÓN DE GOBERNANZA Y PROMOTABILIDAD  
**Autoridad:** Directiva Canónica CP146 — Promotion Gate Assessment / Antigravity Agent  
**Predecesores Directos:**
* Checkpoint 145-R1 (`checkpoints/145-r1-reconciliacion-dictamen-fase-1d.md`)
* Checkpoint 144 (`checkpoints/144-fase-1d-ejecucion-benchmark-retrieval.md`)
* Checkpoint 142 (`checkpoints/142-fase-1c-ejecucion-frontera-corpus-runtime.md`)
* Checkpoint 140 (`checkpoints/140-reconciliacion-canonica-fase-1b.md`)
* Checkpoint 133 (`checkpoints/133-formalizacion-gate-1a-1b.md`)
* Checkpoint 131 (`checkpoints/131-fase-1a-final-synthesis.md`)  
**Estatus Canónico:** **`FASE_1E = CLOSED | PHASE_1_PROMOTABLE = FALSE | PROMOTION = NOT_AUTHORIZED`**  
**Gobernanza:** `PROMOTION = NOT_AUTHORIZED | PHASE_2 = BLOCKED | FASE_2.X = NOT_AUTHORIZED`  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`

---

## 1. ESTADO DE GOBERNANZA

```text
===============================================================================
TALOS V1.5 — CHECKPOINT 146: PHASE 1E PROMOTION GATE ASSESSMENT & SUBSYSTEM CLOSURE
===============================================================================

PHASE_1A                        = COMPLETE / CLOSED (CP131)
GATE_1A_1B                      = FORMALIZED / CLOSED (CP133)
FASE_1B                         = COMPLETE / CANONICALLY CLOSED (CP140)
FASE_1C                         = COMPLETE / CERTIFIED (CP142)
FASE_1D                         = COMPLETE / CANONICALLY CLOSED (CP145-R1)
FASE_1E                         = ADJUDICATED / CANONICALLY CLOSED (CP146)
  ├─ PRE-AUDITORÍA INTEGRIDAD   = PASSED (11/11 artefactos primarios verificados)
  ├─ BASES DE PRODUCCIÓN        = 6/6 INTACTAS (DATABASE_CHANGES = 0)
  ├─ RUNTIME TALOS V1           = INALTERADO (V1_RUNTIME_MODIFIED = FALSE)
  ├─ ADJUDICACIÓN DE CANDIDATOS = C0..C7 EVALUADOS BAJO COMPUERTAS G1..G7
  │   ├─ C0 (FTS5 BM25)         = BASELINE RETAINED (Motor de producción V1 preservado)
  │   ├─ C1 (Dense Qwen)        = DEFER (Calibrable H4 pero sin guard integrado ni suficiencia)
  │   ├─ C2 (Dense BGE)         = DEFER (Mejora ranking pero sin suficiencia demostrada)
  │   ├─ C3 (Dense E5)          = REJECT (Degradación de ranking frente a C0)
  │   ├─ C4 (FTS5+Qwen RRF)     = DEFER (Mejor nDCG@5 y latencia 0.02ms, pero H3 inconcluso)
  │   ├─ C5 (RRF -> BGE Rerank) = REJECT (Degradación ranking y latencia p95=1840ms >> 150ms)
  │   ├─ C6 (C5 + Exp. Struct.) = REJECT (ΔS=0 en 18/18 pares y latencia p95=1840ms >> 150ms)
  │   └─ C7 (C6 + Guard t=0.35) = REJECT (FRR_ID=94.4% masivo y latencia p95=1840ms >> 150ms)
  └─ DICTAMEN SUBSISTEMA FASE 1 = PHASE_1_PROMOTABLE = FALSE (Ningún candidato apto)

PROMOTION_TO_PRODUCTION         = NOT_AUTHORIZED
PRODUCTION_SELECTION            = NOT_PERFORMED
FASE_2 (PEDAGOGÍA)              = BLOCKED (Regla de Secuencia: sin nuevo sustrato)
FASE_2.X (MODELOS DECISIÓN EST) = CANDIDATE / NOT_AUTHORIZED (CP138)

===============================================================================
```

---

## 2. INMUTABILIDAD Y PRE-AUDITORÍA DE INTEGRIDAD CRIPTOGRÁFICA

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
* Las 6 bases SQLite en `data/web_state/*.db`: 100% intactas (`DATABASE_CHANGES = 0`).
* Código fuente `src/`: inalterado (`V1_RUNTIME_MODIFIED = FALSE`).

---

## 3. MATRIZ CANÓNICA DE ADJUDICACIÓN DE COMPUERTAS (G1 A G7)

```text
┌────┬─────────────────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬─────────────────┐
│ ID │ Candidato Canónico      │ G1 (Rel/Suf) │ G2 (OOD Abst)│ G3 (Context) │ G4 (Proven.) │ G5 (Compat.) │ G6 (Latency) │ G7 (Determ.) │ DICTAMEN FINAL  │
├────┼─────────────────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼─────────────────┤
│ C0 │ FTS5 BM25               │ NOT_APPLIC.  │ NOT_SUPPORT. │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ BASELINE RETAIN │
│ C1 │ Dense Qwen              │ INCONCLUSIVE │ INCONCLUSIVE │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ DEFER           │
│ C2 │ Dense BGE               │ INCONCLUSIVE │ NOT_SUPPORT. │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ DEFER           │
│ C3 │ Dense E5                │ NOT_SUPPORT. │ NOT_SUPPORT. │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ REJECT          │
│ C4 │ FTS5 + Qwen RRF         │ INCONCLUSIVE │ NOT_SUPPORT. │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ DEFER           │
│ C5 │ RRF → BGE reranker      │ NOT_SUPPORT. │ NOT_SUPPORT. │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ NOT_SUPPORT. │ SUPPORTED    │ REJECT          │
│ C6 │ C5 + expansión estruct. │ NOT_SUPPORT. │ NOT_SUPPORT. │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ NOT_SUPPORT. │ SUPPORTED    │ REJECT          │
│ C7 │ C6 + guardia tau=0.35   │ NOT_SUPPORT. │ NOT_SUPPORT. │ SUPPORTED    │ SUPPORTED    │ SUPPORTED    │ NOT_SUPPORT. │ SUPPORTED    │ REJECT          │
└────┴─────────────────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴─────────────────┘
```

---

## 4. DICTAMEN FORMAL DE CADA CANDIDATO

1. **C0 (FTS5 BM25) — `BASELINE RETAINED`:** Se preserva intacto como el motor en producción de TALOS V1. Ningún candidato demostró superioridad simultánea en relevancia, suficiencia didáctica y preservación OOD para justificar contractualmente su reemplazo.
2. **C4 (FTS5 + Qwen RRF) — `DEFER`:** Es el candidato más eficiente ($p95 = 0.02\text{ ms}$) y con mayor $\text{nDCG}@5$ del benchmark ($0.1429$, $+28.6\%$ sobre el mejor baseline monomodal). No obstante, conforme a la regla directiva, **el mejor nDCG@5 observado no autoriza promoción por sí mismo**: en $H_3$ empató técnicamente en $\text{MRR}@5$, su suficiencia estricta fue nula ($S@1 = 0$), y no cuenta con compuerta OOD integrada activa. Se defiere formalmente para una futura ampliación de corpus.
3. **C1 (Dense Qwen) y C2 (Dense BGE) — `DEFER`:** Exhiben mejora en ranking respecto al BM25 puro, pero sufren de suficiencia nula ($S@1 = 0$) y carecen de un mecanismo de compuerta operacional integrado que garantice contención OOD sin falso rechazo.
4. **C3 (Dense E5) — `REJECT`:** Su desempeño de ranking fue inferior al baseline $C_0$ ($\text{nDCG}@5 = 0.0476$ vs $0.0794$).
5. **C5 (RRF → BGE Reranker) y C6 (C5 + Expansión Estructural) — `REJECT`:** Degradan el ranking respecto a retrievers directos y violan críticamente el contrato de latencia de servicio ($p95 \approx 1840\text{ ms} \gg 150\text{ ms}$). Además, en $H_2$ la expansión estructural aportó cero mejora ($\Delta S = 0$ en el 100% de los pares).
6. **C7 (C6 + Guardia $\tau=0.35$) — `REJECT`:** Produce un falso rechazo masivo e inaceptable ($\text{FRR}_{\text{ID}} = 94.4\%$, 17 de 18 consultas curriculares legítimas bloqueadas) combinado con violación crítica de latencia ($p95 = 1840.53\text{ ms}$).

---

## 5. DICTAMEN GLOBAL DE FASE 1 Y DECISIÓN DE GOBERNANZA

En estricta aplicación del principio de no-inversión de causalidad:

```text
PHASE_1_PROMOTABLE    = FALSE
PROMOTION_TO_PROD     = NOT_AUTHORIZED
CURRENT_BASELINE      = C0 (FTS5 BM25) RETAINED
PRODUCTION_SELECTION  = NOT_PERFORMED
DATABASE_CHANGES      = 0
V1_RUNTIME_MODIFIED   = FALSE
```

### Decisión sobre Fase 2:
En virtud de la **Regla de Secuencia** (Roadmap Maestro Sección 2), no se puede edificar una capa superior (Pedagogía / Intervención) sobre un sustrato inferior de retrieval que no haya alcanzado promoción contractual.  
Por lo tanto:
* **Fase 2 (Pedagogía / Explanation Quality):** Permanece formalmente **`BLOCKED / NOT_AUTHORIZED`**.
* **Fase 2.X (Modelos de Decisión Estructurada — CP138):** Permanece en estatus **`CANDIDATE / NOT_AUTHORIZED`**.
* **Runtime de Producción:** TALOS continúa operando de forma 100% estable sobre su baseline contractual $C_0$ y los contratos de frontera certificados en CP142.

---

## 6. INVENTARIO DE ARTEFACTOS Y VERIFICACIÓN CRIPTOGRÁFICA

```text
┌────────────────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────┐
│ Artefacto de Cierre CP146                                              │ Hash SHA-256                                                     │
├────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
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

La **Fase 1E queda formal, canónica y definitivamente cerrada**.
