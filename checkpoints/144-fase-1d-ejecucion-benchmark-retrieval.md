# Checkpoint 144: Ejecución Canónica Exitosa del Benchmark de Retrieval de Fase 1D (Evidence Selection & Calibration)

**Fecha:** 2026-10-05T16:30:00-03:00  
**Fase:** FASE 1 — EVIDENCE RETRIEVAL / SUBFASE 1D — EVIDENCE SELECTION & CALIBRATION  
**Tipo de Documento:** CHECKPOINT DE EJECUCIÓN EXPERIMENTAL CANÓNICA  
**Autoridad:** Directiva Canónica de Autorización de Ejecución CP144 / Antigravity Agent  
**Predecesores Directos:**
* Checkpoint 143 (`checkpoints/143-fase-1d-especificacion-y-preregistro.md`)
* Checkpoint 143-R1 (`checkpoints/143-r1-reconciliacion-pre-ejecucion-fase-1d.md`)  
**Estatus de Fase 1D:** `EXECUTION_COMPLETED | RESULTS_PENDING_ADJUDICATION`  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`

---

## 1. ESTADO DE GOBERNANZA

```text
===============================================================================
TALOS V1.5 — CHECKPOINT 144: PHASE 1D BENCHMARK EXECUTION COMPLETED
===============================================================================

PHASE_1A                        = COMPLETE (CP131)
GATE_1A_1B                      = FORMALIZED (CP133)
FASE_1B                         = COMPLETE / CANONICALLY CLOSED (CP140)
FASE_1C                         = COMPLETE / CERTIFIED (CP142)
FASE_1D                         = EXECUTION_COMPLETED / RESULTS_PENDING_ADJUDICATION
  ├─ ESPECIFICACIÓN TÉCNICA     = v1.0.1-reconciled (CP143-R1)
  ├─ PREREGISTRO FORMAL         = v1.0.1-reconciled (CP143-R1)
  ├─ GUÍA METODOLÓGICA          = v1.0.1-reconciled (CP143-R1)
  ├─ INFORME DE RECONCILIACIÓN  = CP143-R1 (SHA-256: 20ba9ab0...)
  ├─ MANIFIESTO PRE-RUN         = FROZEN (SHA-256: b41a4031...)
  ├─ PREFLIGHT TÉCNICO          = PASSED (16/16)
  ├─ AUTORIZACIÓN DE EJECUCIÓN  = GRANTED (CP144 DIRECTIVE)
  ├─ EJECUCIÓN EXPERIMENTAL     = COMPLETED (176 celdas, 41.65s)
  ├─ CONTROLES NEGATIVOS        = PASSED (5/5 NC-01..NC-05)
  ├─ INFORME DE RESULTADOS      = CANONICAL (SHA-256: c517e279...)
  ├─ MANIFIESTO DE EJECUCIÓN    = EXECUTED (SHA-256: f4a3fe9c...)
  └─ RESULTADOS OFICIALES       = PENDING_ADJUDICATION
FASE_1E                         = BLOCKED (Promotion Gate)
FASE_2                          = NOT_AUTHORIZED
FASE_2.X (MODELOS DECISIÓN EST) = CANDIDATE / NOT_AUTHORIZED (CP138)

PRODUCTION_SELECTION            = NOT_PERFORMED
DATABASE_CHANGES                = 0
V1_RUNTIME_MODIFIED             = FALSE
PRODUCTION_ISOLATION            = INVIOLABLE (Certified Bit-for-Bit)

===============================================================================
```

---

## 2. RESUMEN DE LA CORRIDA EXPERIMENTAL

1. **Cumplimiento de Invariantes:**  
   Se verificaron los 9 artefactos sellados en CP143-R1 antes de la ejecución física. Todos los hashes SHA-256 coincidieron bit a bit.
2. **Dimensiones de la Corrida:**  
   - 22 consultas canónicas (18 In-Domain, 2 OOD, 2 Polysemy).
   - 8 condiciones ($C_0 \dots C_7$).
   - 176 celdas evaluadas contra el ground truth de `QREL_1D_BASELINE.json`.
   - Tiempo de ejecución total en CPU: 41.65 segundos.
3. **Controles Negativos (NC-01..NC-05):**  
   Los 5 controles deterministas resultaron APROBADOS (`PASS 100%`).
4. **Integridad de Producción:**  
   Las 6 bases de datos operacionales de SQLite en `data/web_state/*.db` no recibieron escrituras (`DATABASE_CHANGES = 0`), y no se modificó ningún archivo en `src/` (`V1_RUNTIME_MODIFIED = FALSE`).

---

## 3. TABLA DE MÉTRICAS OFICIALES AGREGADAS

| ID | Condición Canónica | $P@1$ | $P@3$ | $P@5$ | MRR@5 | nDCG@5 | $S@1$ (Strict) | $S@1$ (Any) | $\Delta_{\text{brecha}}$ | $A_{\text{OOD}}$ | $\text{FRR}_{\text{ID}}$ | Latencia Media (ms) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **C0** | COND-BASE-FTS5 | 0.0556 | 0.0185 | 0.0111 | 0.0556 | 0.0794 | 0.0000 | 0.0556 | 0.0556 | 0.0% | 0.0% | 0.20 |
| **C1** | COND-DENSE-QWEN | **0.1667** | **0.0556** | **0.0333** | **0.1667** | 0.1032 | 0.0000 | 0.0000 | 0.1667 | 0.0% | 0.0% | 0.00 |
| **C2** | COND-DENSE-BGE | **0.1667** | **0.0556** | **0.0333** | **0.1667** | 0.1111 | 0.0000 | 0.0556 | 0.1667 | 0.0% | 0.0% | 0.00 |
| **C3** | COND-DENSE-E5 | 0.0556 | 0.0185 | 0.0111 | 0.0556 | 0.0476 | 0.0000 | 0.0000 | 0.0556 | 0.0% | 0.0% | 0.00 |
| **C4** | COND-HYBRID-RRF | **0.1667** | **0.0556** | **0.0333** | **0.1667** | **0.1429** | 0.0000 | 0.0556 | 0.1667 | 0.0% | 0.0% | 0.02 |
| **C5** | COND-RERANK-BGE | 0.0556 | 0.0185 | 0.0111 | 0.0556 | 0.0635 | 0.0000 | 0.0000 | 0.0556 | 0.0% | 0.0% | 1726.22 |
| **C6** | COND-EXP-STRUCTURAL | 0.0556 | 0.0185 | 0.0111 | 0.0556 | 0.0635 | 0.0000 | 0.0000 | 0.0556 | 0.0% | 0.0% | 1726.30 |
| **C7** | COND-GUARDED-FULL | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0079 | 0.0000 | 0.0000 | 0.0000 | **100.0%** | **94.4%** | 1726.30 |

---

## 4. DICTAMEN DE HIPÓTESIS CIENTÍFICAS (H1 A H5)

Bajo las reglas estrictas de decisión de CP143-R1:

* **H1 (Brecha Relevancia vs Suficiencia): `INCONCLUSIVE`**  
  $\Delta_{\text{brecha}} = 0.1667 \ge 0.15$ evidencia sustantiva, pero $b=3 < 5$ pares discordantes ($p_{\text{exact}} = 0.1250 \ge 0.05$). No alcanza significancia formal por tamaño muestral $N=18$.
* **H2 (Valor de la Expansión Estructural): `INCONCLUSIVE`**  
  18 de 18 pares pareados fueron neutrales ($\Delta S = 0$, 0 mejoradas, 0 degradadas) sin degradación de $P@5$ ($0.0111 == 0.0111$).
* **H3 (Superioridad del Retrieval Híbrido RRF): `INCONCLUSIVE`**  
  $C_4$ supera a todos los baselines individuales en nDCG@5 ($0.1429 > 0.1111$), pero empata técnicamente en MRR@5 ($0.1667 == 0.1667$).
* **H4 (Calibración de Umbral Similitud en Grilla): `SUPPORTED`**  
  En la grilla $\mathcal{T}_{\text{sim}} = \{0.30, 0.35, 0.40, 0.45, 0.50\}$, el umbral $\tau = 0.40$ logra simultáneamente $A_{\text{OOD}} = 100.0\%$ y $\text{FRR}_{\text{ID}} = 11.1\% \le 15.0\%$. Seleccionado unívocamente por la regla pre-registrada $\tau^* = 0.40$.
* **H5 (Abstención Confiable de Guardia $C_7$): `NOT_SUPPORTED`**  
  Bajo el parámetro operacional $\tau_{\text{abstain}} = 0.35$, $A_{\text{OOD}} = 100.0\%$, pero $\text{FRR}_{\text{ID}} = 94.4\% > 20\%$. El guard bloquea el 94.4% del currículo legítimo.

---

## 5. INVENTARIO DE ARTEFACTOS Y VERIFICACIÓN CRIPTOGRÁFICA

```text
┌────────────────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────┐
│ Artefacto de Ejecución                                                 │ Hash SHA-256                                                     │
├────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│ reports/v1_5_phase1/                                                   │                                                                  │
│   PHASE_1D_RETRIEVAL_BENCHMARK_REPORT.md                               │ c517e279e87dfb146aa74c98b3f853bd9283bab9671b6b92eaaafc9073236680 │
│ experiments/v1_5_phase1d/execution/                                    │                                                                  │
│   PHASE_1D_BENCHMARK_EXECUTION_MANIFEST.json                          │ f4a3fe9c670f38684c1e96d8fb43964724087edf67ce401a4cee57ef68a541bc │
│ experiments/v1_5_phase1d/execution/raw_results/                        │                                                                  │
│   phase1d_raw_execution_results.json                                   │ 86eb541ffbd1de66a4d092be472bcd2cc09c0f09580097a872965b676ad155e1 │
│ experiments/v1_5_phase1d/execution/metrics/                            │                                                                  │
│   phase1d_per_query_results.json                                       │ 2c496bb8a87e32cd65d17d1ed0c210511c2b26cd4acac37fb397015db4fa3f50 │
│   phase1d_aggregate_metrics.json                                       │ 9cb4b9cd38604f37a197e712d0a48aaa69f4787647ea5cab0cc6c4f2b84ac592 │
│   phase1d_hypotheses_evaluation.json                                   │ fa503edacc918e73b764b165ff275e345b8b710c13577e6bb03db0aa27d068ae │
│   phase1d_negative_controls.json                                       │ 8f8cefdb462c99547ad6507862b213c29d7a6281de6b5fc017030eaee2762f1c │
│ experiments/v1_5_phase1d/execution/technical_logs/                     │                                                                  │
│   phase1d_execution.log                                                │ 489627ea9e89c2d1885d238239f304ca58c16f90515e70c8d001090b206c7219 │
└────────────────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────┘
```

---

## 6. AUDITORÍA DE INMUTABILIDAD DE LAS BASES PRODUCTIVAS

```text
┌──────────────────────────────────┬──────────────────────────────────────────────────────────────────┬──────────────┐
│ Base de Datos de Producción      │ Hash SHA-256 Verificado Post-Ejecución                           │ Estado       │
├──────────────────────────────────┼──────────────────────────────────────────────────────────────────┼──────────────┤
│ data/web_state/cal_store.db      │ 82773155ca35028274ba0f378fdcd37a5374bb4483a579654a6e9facfd443782 │ INTACTA      │
│ data/web_state/knowledge_store.db│ fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1 │ INTACTA      │
│ data/web_state/quotas.db         │ 09838ed16f1bbab384e6a83be651c9f8657db11c6a72caa5c32947a2cc18050d │ INTACTA      │
│ data/web_state/student_state.db  │ f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d │ INTACTA      │
│ data/web_state/study_engine.db   │ e3ba06536f7dbba337dee3c1c5f01b43660ce276abb54c5cee2d5defc5b970aa │ INTACTA      │
│ data/web_state/vector_store.db   │ d6d9f8c8eb6e5188e8e600a73cc05bd001d2e389061815d7d0df33f447a9dde4 │ INTACTA      │
└──────────────────────────────────┴──────────────────────────────────────────────────────────────────┴──────────────┘
```

---

## 7. CONDICIÓN DE PASO Y PRÓXIMO PASO

La corrida física de benchmark de la Fase 1D ha concluido satisfactoriamente y sus resultados se encuentran registrados y congelados.  
Los resultados pasan formalmente al estado de **`PENDING_ADJUDICATION`**.  
No se autoriza ninguna promoción a producción ni inicio de Fase 1E hasta completar la directiva correspondiente de adjudicación y auditoría post-ejecución.
