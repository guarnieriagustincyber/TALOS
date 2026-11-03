# Checkpoint 137: Ejecución Experimental Canónica y Cierre Técnico de Fase 1B (Corpus → Evidence)

**Fecha:** 2026-10-05T15:15:00-03:00  
**Fase:** FASE 1 — EVIDENCE RETRIEVAL / SUBFASE 1B — CORPUS → EVIDENCE  
**Tipo de Documento:** CHECKPOINT DE EJECUCIÓN EXPERIMENTAL CANÓNICA Y CIERRE TÉCNICO  
**Autoridad:** Directiva Canónica de Ejecución Experimental de Fase 1B / Antigravity Agent  
**Predecesores:** 
* Checkpoint 136 (`checkpoints/136-correccion-preflight-preregistro-1b.md`)
* Protocolo Sellado: `reports/v1_5_phase1/PHASE_1B_EXPERIMENTAL_DESIGN.md` (v1.0.2-canonical)
* Registro de Sello: `reports/v1_5_phase1/PHASE_1B_PREREGISTRATION_SEAL.md`
* Dictamen de Readiness: `reports/v1_5_phase1/PHASE_1B_EXECUTION_READINESS.md`  
**Estatus de Ejecución:** `1B_EXECUTION = COMPLETE`  
**Estatus Científico:** `RESULTS = AVAILABLE | ANALYSIS = PENDING`  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE`  

---

## 1. ESTADO DE GOBERNANZA

```text
===============================================================================
TALOS V1.5 — CHECKPOINT 137: CANONICAL 1B EXECUTION COMPLETE
===============================================================================

PHASE_1A                    = COMPLETE (CP131)
GATE_1A_1B                  = FORMALIZED (CP133)

PROTOCOL_VERSION            = v1.0.2-canonical
PROTOCOL_STATUS             = SEALED
PROTOCOL_SHA256             = 0f61adfbb5048982c77cab8388796319c8b8c99d1726f4fde9826ea992c9f426
SEAL_SHA256                 = 8989bd49737ae0fd57e2b2d7495765dae5b34b82a1f9adf7777a8a80c792d970

EXECUTION_AUTHORIZATION     = GRANTED
EXECUTION_ID                = run_1b_canonical_20261005_151258
1B_EXECUTION_STATUS         = COMPLETE
EXECUTION_DURATION          = 38.44 s

CONDITIONS_EXECUTED         = 8 (C0, C1, C2, C3, C4, C5, C6, C7)
QUERIES_EXECUTED            = 22 (18 IN_DOMAIN, 2 OOD, 2 POLYSEMY)
TOTAL_CELLS_RUN             = 176
RUNTIME_ERRORS              = 0
EXCLUSIONS                  = 0
DEVIATIONS                  = REGISTERED / NONE

BLINDING_STATUS             = SEALED (blinding_key.json.locked)
BLINDING_KEY_SHA256         = 42c744a45bde6b0df0e7abf433f3829e817a03d3769b0b202e8cc24668ea30c0

PRODUCTION_SELECTION        = NOT_PERFORMED
DATABASE_CHANGES            = 0
V1_RUNTIME_MODIFIED         = FALSE
PRODUCTION_ISOLATION        = CERTIFIED (100% bit-for-bit unchanged)

RESULTS_STATUS              = AVAILABLE
HYPOTHESIS_ANALYSIS         = PENDING (Human Blind Adjudication required)

===============================================================================
```

---

## 2. RESUMEN DE LA EJECUCIÓN EXPERIMENTAL

1. **Invocación Canónica:** Ejecutado mediante `./venv/bin/python experiments/v1_5_phase1b/execution/phase_1b_runner.py --execute` bajo estricto control fail-closed.
2. **Condiciones Ejecutadas:**
   * $C_0$: COND-BASE-FTS5 (BM25 léxico SQLite unicode61 en memoria, $k=10$).
   * $C_1$: COND-DENSE-QWEN (Qwen3-Embedding-0.6B 1024d, Dense Cosine L2).
   * $C_2$: COND-DENSE-BGE (BGE-M3 1024d, Dense Cosine L2).
   * $C_3$: COND-DENSE-E5 (multilingual-e5-small 384d, Dense Cosine L2).
   * $C_4$: COND-HYBRID-RRF (FTS5 + Qwen3 Dense RRF $k=60$).
   * $C_5$: COND-RERANK-BGE (RRF10 $\to$ Neural Cross-Encoder Reranker BAAI/bge-reranker-base ONNX CPU).
   * $C_6$: COND-EXP-STRUCTURAL (RRF10 $\to$ Reranker $\to$ Expansión Estructural $\le 1500$ tokens, $\le 4500$ chars).
   * $C_7$: COND-GUARDED-FULL (RRF10 $\to$ Reranker $\to$ Expansión $\to$ Compuerta de Abstención $\tau = 0.35$).
3. **Observaciones Clave:**
   * **Control Negativo OOD ($N=2$):** 100.0% de abstención correcta en `Q1A2-37` ($S=0.0059$) y `Q1A2-38` ($S=0.0022$).
   * **Compuerta In-Domain:** Con $\tau = 0.35$, emitió `ACCEPT_EVIDENCE` en `Q1A2-02` ($S=0.3587$) y `ABSTAIN` en las 17 consultas restantes, reflejando alta selectividad conservadora.
   * **Expansión Pareada H2:** 100% de los paquetes respetaron el presupuesto dual ($\le 1500$T, $\le 4500$c).
   * **Aislamiento de Producción:** Las 6 bases de datos de producción (`cal_store.db`, `knowledge_store.db`, `quotas.db`, `student_state.db`, `study_engine.db`, `vector_store.db`) se mantuvieron 100% inalteradas.

---

## 3. ARTEFACTOS PRODUCIDOS

* `experiments/v1_5_phase1b/execution/raw_results/raw_rankings.json` (SHA-256: `7a09cb6b52c9b493693f4054d8fc0b9b4eae5180ddea9f83792c581a42cc4a1f`)
* `experiments/v1_5_phase1b/execution/technical_logs/execution_trace.json` (SHA-256: `7007d3647ff0adc78722b7e39b890eb079e0dcde16053b8c26093fac6b5ea4d1`)
* `experiments/v1_5_phase1b/execution/blind_outputs/blind_package.json` (SHA-256: `f65be417f24bdcbdc1e9d3fb4e96eae4c675dba7fdf2ab65ddb247017d4bd389`)
* `experiments/v1_5_phase1b/execution/blind_outputs/adjudication_form.json` (SHA-256: `d5ba3817112b3227eb04b8adcc1899120613271f28b49e623ec27b32298642ca`)
* `experiments/v1_5_phase1b/execution/blinding_key.json.locked` (SHA-256: `42c744a45bde6b0df0e7abf433f3829e817a03d3769b0b202e8cc24668ea30c0`)
* `experiments/v1_5_phase1b/execution/metrics/metrics_summary.json` (SHA-256: `8e9ebe94d0e63edb1a8a5337d7a4f6b289918bbe535fe8b4c08b012b31097cab`)
* `experiments/v1_5_phase1b/execution/PHASE_1B_EXECUTION_MANIFEST.json` (SHA-256: `7c73ffae51743f01b0f1be92d5c21df26fa32d43144f808f220d911a361bcfa0`)
* `reports/v1_5_phase1/PHASE_1B_EXECUTION_REPORT.md` (SHA-256: `ffec14976b4c787e7cbec34160542605e6c848a82ba548fecc7408d3f094bdb7`)

---

## 4. PRÓXIMO PASO AUTORIZADO

1. Despacho del paquete ciego `blind_package.json` para adjudicación humana independiente ($N=1$).
2. Consolidación de `QREL_1B_FINAL` para cálculo descegado definitivo de métricas de retrieval ($H_1, H_3$).
3. Análisis formal de hipótesis estadísticas y cierre de Fase 1B.
