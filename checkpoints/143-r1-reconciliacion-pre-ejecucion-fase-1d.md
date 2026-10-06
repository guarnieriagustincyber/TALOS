# Checkpoint 143-R1: Reconciliación Metodológica Pre-Ejecución y Re-Sellado Criptográfico de Fase 1D

**Fecha:** 2026-10-05T16:25:00-03:00  
**Fase:** FASE 1 — EVIDENCE RETRIEVAL / SUBFASE 1D — EVIDENCE SELECTION & CALIBRATION  
**Tipo de Documento:** CHECKPOINT DE RECONCILIACIÓN METODOLÓGICA Y RE-SELLADO  
**Autoridad:** Directiva Canónica de Reconciliación Pre-Ejecución — CP143-R1 / Antigravity Agent  
**Predecesores Directos:**
* Checkpoint 143 (`checkpoints/143-fase-1d-especificacion-y-preregistro.md`)  
**Estatus de Fase 1D:** `SPECIFICATION_RECONCILED | PREREGISTRATION_RESEALED | PREFLIGHT_PASSED | EXECUTION_NOT_AUTHORIZED`  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`

---

## 1. ESTADO DE GOBERNANZA

```text
===============================================================================
TALOS V1.5 — CHECKPOINT 143-R1: PHASE 1D METHODOLOGICAL RECONCILIATION
===============================================================================

PHASE_1A                        = COMPLETE (CP131)
GATE_1A_1B                      = FORMALIZED (CP133)
FASE_1B                         = COMPLETE / CANONICALLY CLOSED (CP140)
FASE_1C                         = COMPLETE / CERTIFIED (CP142)
FASE_1D                         = RECONCILED / RESEALED / PREFLIGHT_PASSED
  ├─ ESPECIFICACIÓN TÉCNICA     = v1.0.1-reconciled (SHA-256: 30058330...)
  ├─ PREREGISTRO FORMAL         = v1.0.1-reconciled (SHA-256: 05e0de81...)
  ├─ GUÍA METODOLÓGICA          = v1.0.1-reconciled (SHA-256: 667f2d83...)
  ├─ PREFLIGHT TÉCNICO          = PASSED (16/16, SHA-256: 3ed8855f...)
  ├─ REGISTRO DE RE-SELLO       = RESEALED (SHA-256: d3c0020e...)
  ├─ INFORME DE RECONCILIACIÓN  = CP143-R1 (SHA-256: 20ba9ab0...)
  ├─ MANIFIESTO DE EJECUCIÓN    = FROZEN (v1.0.1, SHA-256: b41a4031...)
  ├─ BANCO DE CONSULTAS         = FROZEN (22 queries, SHA-256: e15d5106...)
  ├─ QRELS BASELINE             = FROZEN (176 cells, SHA-256: ed1c1f30...)
  ├─ CONFIGURACIÓN BENCHMARK    = FROZEN (SHA-256: 50d3da8e...)
  └─ EJECUCIÓN EXPERIMENTAL     = NOT_AUTHORIZED (PRE-EXECUTION RECONCILED)
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

## 2. MOTIVACIÓN Y ALCANCE DE LA RECONCILIACIÓN

La Directiva Canónica CP143-R1 ordenó subsanar tres debilidades metodológicas en el diseño de la Fase 1D previo a cualquier autorización de ejecución:

1. **Eliminación del uso decorativo de $p < 0.05$ en $H_1$:**
   Se sustituyó la mención genérica de significancia por un marco estadístico formal y explícito:
   - **Unidad estadística:** Consulta curricular $q_i \in \text{SLICE\_IN\_DOMAIN}$ ($N = 18$ temas independientes).
   - **Variables emparejadas:** Indicadores binarios $X_i = \mathbb{I}(\text{rel}(c_{i,1}) \ge 2)$ y $Y_i = \mathbb{I}(\text{suff}(c_{i,1}) == 2)$.
   - **Hipótesis nula ($H_{0,1}$):** $\mathbb{P}(X=1, Y=0) \le \mathbb{P}(X=0, Y=1)$.
   - **Test estadístico:** Test exacto de McNemar para pares discordantes ($b = \sum \mathbb{I}(X_i = 1 \land Y_i = 0)$) con distribución binomial ($p_{\text{exact}} = 0.5^b$).
   - **Criterio de confirmación:** $\Delta_{\text{brecha}} \ge 0.15$ y $b \ge 5$ ($p_{\text{exact}} \le 0.03125$).

2. **Supresión de umbral único anticipado en $H_4$:**
   Se eliminó la anticipación de $\tau = 0.40$ como umbral ganador a priori para evitar el sesgo de "target painting". Se formalizó como la evaluación *ex-ante* de un grid discreto pre-registrado:
   $$\mathcal{T}_{\text{sim}} = \{0.30, 0.35, 0.40, 0.45, 0.50\}$$
   Se fijó una regla de selección objetiva pre-registrada ($\min \text{FRR}_{\text{ID}}$, mediana en caso de empate), manteniendo $\tau = 0.40$ únicamente como punto de referencia comparativo.

3. **Clarificación operacional de $C_7$ en $H_5$:**
   Se explicitó formalmente que el umbral de abstención $\tau_{\text{abstain}} = 0.35$ utilizado por el guard de $C_7$ es un **parámetro operativo pre-registrado** derivado de la ejecución de Fase 1B, y no un hallazgo demostrado u óptimo universal.

---

## 3. AUDITORÍA DE INMUTABILIDAD Y NO-CONTAMINACIÓN RETROSPECTIVA

Se certifica que:
- No se alteró ninguna de las 22 consultas canónicas (`benchmark_queries.json`).
- No se modificó ninguna de las 176 celdas de ground truth (`QREL_1D_BASELINE.json`).
- No se agregaron ni alteraron condiciones experimentales ($C_0 \dots C_7$).
- No se realizaron modificaciones en el código de producción (`src/` inmutable).
- Las 6 bases de datos operacionales de SQLite en `data/web_state/*.db` se mantienen 100% íntegras:
  - `cal_store.db`: `82773155ca35028274ba0f378fdcd37a5374bb4483a579654a6e9facfd443782`
  - `knowledge_store.db`: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1`
  - `quotas.db`: `09838ed16f1bbab384e6a83be651c9f8657db11c6a72caa5c32947a2cc18050d`
  - `student_state.db`: `f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d`
  - `study_engine.db`: `e3ba06536f7dbba337dee3c1c5f01b43660ce276abb54c5cee2d5defc5b970aa`
  - `vector_store.db`: `d6d9f8c8eb6e5188e8e600a73cc05bd001d2e389061815d7d0df33f447a9dde4`

---

## 4. INVENTARIO COMPLETO DE ARTEFACTOS Y HASHES SHA-256 RE-SELLADOS

| Artefacto | Ruta Canónica | SHA-256 | Estatus |
| :--- | :--- | :--- | :---: |
| **Especificación de Benchmark**| `reports/v1_5_phase1/PHASE_1D_RETRIEVAL_BENCHMARK_SPECIFICATION.md` | `3005833080e5797131f88b8dc34afba9fcba40281456174d662f389774e1ade1` | `RECONCILED` |
| **Preregistro Experimental** | `reports/v1_5_phase1/PHASE_1D_PREREGISTRATION.md` | `05e0de813f0066aa409e64ed5ab978cc5388d8546d167a20f16077ca00e6b301` | `RESEALED` |
| **Guía Metodológica** | `reports/v1_5_phase1/PHASE_1D_METHODOLOGY.md` | `667f2d8313c41894b9244c0dfe181ad0fe59bd03b654f6381496747ddd4a2321` | `RECONCILED` |
| **Informe de Preflight** | `reports/v1_5_phase1/PHASE_1D_PREFLIGHT_REPORT.md` | `3ed8855fc5f4aca2d532871929abc39c31d00a6b8e2085421f7ec57df64a6e46` | `PASSED (16/16)` |
| **Registro de Re-Sello** | `reports/v1_5_phase1/PHASE_1D_PROTOCOL_SEAL.md` | `d3c0020ed295c3b14d50ba51483b13a7befc10d2f61aa01418bb37cfa4017775` | `CERTIFIED` |
| **Informe de Reconciliación** | `reports/v1_5_phase1/CP143_R1_PHASE_1D_RECONCILIATION.md` | `20ba9ab065222a4f9b4923443d1ad10a19e40c01f50ecc22023ed541501c4f0e` | `CANONICAL` |
| **Manifiesto de Ejecución** | `experiments/v1_5_phase1d/manifests/PHASE_1D_EXECUTION_MANIFEST.json` | `b41a40316c6e0d438a4a8892116a9da5e991d0ca290a7a7143194bfe60675f93` | `FROZEN` |
| **Banco de Consultas** | `experiments/v1_5_phase1d/benchmark_queries.json` | `e15d5106ea2a14964572485be3b6e06145d4e4b0a6aa2e0c9e27d23de1b7d90c` | `FROZEN` |
| **Qrels Baseline** | `experiments/v1_5_phase1d/qrels/QREL_1D_BASELINE.json` | `ed1c1f30ab87ef64b0c1647b8d6cef9ddc473fe0538f1d15730277568dbf38aa` | `FROZEN` |
| **Configuración del Benchmark**| `experiments/v1_5_phase1d/configs/benchmark_config.json` | `50d3da8efc631e3855461ddfd1b33fcb08739b15398e5fb65ab8ff4869e14962` | `FROZEN` |
| **Protocolo de Cegamiento** | `experiments/v1_5_phase1d/protocol/blinding_protocol.json` | `df72f8b58b3f4f532ce5bcb6fd8998ae28ed532500ba3d0dd089f9fdf635bccf` | `FROZEN` |

---

## 5. CONDICIÓN DE PASO Y PRÓXIMOS PASOS

La reconciliación pre-ejecución concluye con éxito pleno. El protocolo de Fase 1D queda blindado epistemológicamente y re-sellado criptográficamente.  
La ejecución física del benchmark queda estrictamente pendiente de la correspondiente **Directiva Canónica de Autorización de Ejecución**.
