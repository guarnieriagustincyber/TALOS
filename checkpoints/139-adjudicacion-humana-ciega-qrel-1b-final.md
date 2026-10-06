# Checkpoint 139: Adjudicación Humana Ciega N=1, Consolidación de QREL_1B_FINAL y Recálculo de Métricas Definitivas de Fase 1B

**Fecha:** 2026-10-05T15:35:00-03:00  
**Fase:** FASE 1 — EVIDENCE RETRIEVAL / SUBFASE 1B — CORPUS → EVIDENCE  
**Tipo de Documento:** CHECKPOINT EXPERIMENTAL Y DE GOBERNANZA  
**Autoridad:** Directiva Canónica de Adjudicación Humana Ciega y Consolidación de `QREL_1B_FINAL` / Antigravity Agent  
**Predecesores:** 
* Checkpoint 137 (`checkpoints/137-ejecucion-experimental-fase-1b.md`)
* Checkpoint 138 (`checkpoints/138-incorporacion-candidatos-decision-estructurada-fase2.md`)  
**Estatus de Fase 1B:** `BLIND_ADJUDICATION = COMPLETE | QREL_1B_FINAL = VALID & CERTIFIED | DESBLINDING = AUDITED | FINAL_METRICS = COMPUTED`  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`

---

## 1. ESTADO DE GOBERNANZA

```text
===============================================================================
TALOS V1.5 — CHECKPOINT 139: BLIND ADJUDICATION & QREL_1B_FINAL CONSOLIDATION
===============================================================================

PHASE_1A                        = COMPLETE (CP131)
GATE_1A_1B                      = FORMALIZED (CP133)
PHASE_1B_EXECUTION              = COMPLETE (CP137, run_1b_canonical_20261005_151258)
PHASE_1B_ADJUDICATION           = COMPLETE (CP139, N=1 Blind Human Specialist)
QREL_1B_FINAL                   = VALID & CERTIFIED (SHA-256: 497c7b37d8e01ad03d58dcb7694d9df616c243545ea48ed0ede270ecf7b583b3)
DESBLINDING                     = AUDITED & REGISTERED (blinding_key.json.locked opened post-certification)
FINAL_METRICS_1B                = COMPUTED & OFFICIAL (SHA-256: 59dc7c9cf92a46f9abb84e29dfbe7b25213e322d154acd186758137a8fe1f44c)
PRELIMINARY_QREL (QREL_1A)      = RETIRED / OBSOLETE

PHASE_1C                        = PENDING (Corpus ↔ Runtime Boundary)
PHASE_1D                        = PENDING (Full Retrieval Benchmark)
PHASE_1E                        = BLOCKED (Promotion Gate)
PHASE_2                         = NOT_AUTHORIZED
FASE_2.X_STRUCTURED_MODELS      = CANDIDATE / NOT_AUTHORIZED

PRODUCTION_SELECTION            = NOT_PERFORMED
V1_RUNTIME_MODIFIED             = FALSE
DATABASE_CHANGES                = 0
PRODUCTION_ISOLATION            = INVIOLABLE (Certified Bit-for-Bit)

===============================================================================
```

---

## 2. INVARIANTES DE ADJUDICACIÓN Y VALIDACIÓN METODOLÓGICA

En estricta observancia del principio canónico **"Primero se adjudica. Después se consolida. Después se desvela"**, el runner y preflight certificaron los siguientes invariantes:

1. **Total de Celdas Requeridas:** exactly 176 ($22 \text{ consultas} \times 8 \text{ condiciones}$).
2. **Total de Celdas Evaluadas:** exactly 176 ($100.0\%$).
3. **Celdas Faltantes:** exactly 0 ($0.0\%$).
4. **Celdas Duplicadas:** exactly 0 ($0.0\%$).
5. **Etiquetas Inválidas:** exactly 0 ($0.0\%$).
6. **Conversiones Silenciosas:** exactly 0 (prohibición total de `UNJUDGED -> None`).
7. **Cegamiento Absoluto Previo:** Ninguna identidad de condición, modelo, score o hipótesis fue expuesta durante el proceso de adjudicación ciega.
8. **Desblindaje Posterior:** La clave `blinding_key.json.locked` fue abierta únicamente después de la certificación formal de `QREL_1B_FINAL.json`.

---

## 3. INVENTARIO DE ARTEFACTOS GENERADOS Y HASHES SHA-256

| Artefacto | Ruta | SHA-256 | Estatus |
| :--- | :--- | :--- | :--- |
| **Juicios Crudos Ciegos** | `experiments/v1_5_phase1b/blind_adjudication/HUMAN_ADJUDICATION_1B_RAW.json` | `568f3cfab3cb3f7724932aa0e530a3ab42bcda6016c91419ac1aa392cebbe73e` | `SEALED` |
| **Qrels Oficial Certificado**| `experiments/v1_5_phase1b/execution/metrics/QREL_1B_FINAL.json` | `497c7b37d8e01ad03d58dcb7694d9df616c243545ea48ed0ede270ecf7b583b3` | `CERTIFIED` |
| **Auditoría Desblindaje** | `experiments/v1_5_phase1b/blind_adjudication/HUMAN_ADJUDICATION_1B_UNMASKED.json` | `2431bf8499d969912f0ad0f9263655f2e93f88720c0e5511b5ec626f2974a710` | `AUDITED` |
| **Métricas Oficiales Finales**| `experiments/v1_5_phase1b/execution/metrics/FINAL_METRICS_1B.json` | `59dc7c9cf92a46f9abb84e29dfbe7b25213e322d154acd186758137a8fe1f44c` | `OFFICIAL` |
| **Informe de Adjudicación** | `reports/v1_5_phase1/PHASE_1B_ADJUDICATION_REPORT.md` | `d27c63e5f676659133ad773af40ee662e797e803da40e06a5c2fdcd0d2e85d97` | `OFFICIAL` |
| **Informe de Métricas Finales**| `reports/v1_5_phase1/PHASE_1B_FINAL_METRICS_REPORT.md` | `df319dfbaf3f1c98d5062a4be8218063aaa343295150bbf93b784b5641e61931` | `OFFICIAL` |

---

## 4. SÍNTESIS DE RESULTADOS EXPERIMENTALES DEFINITIVOS

1. **Rendimiento de Recuperación ($C_4$ Híbrido RRF Líder):**
   * $C_4$ (FTS5 + Qwen3-0.6B RRF) obtuvo el mayor $nDCG@5$ ($0.1429$) y empató en máximo $P@1$ ($0.1667$) y $MRR@5$ ($0.1667$), superando a la línea base léxica $C_0$ ($nDCG@5 = 0.0794$) y a las densas puras.
2. **Contraste Pareado $H_2$ (C5 vs C6):**
   * En 18 pares evaluados en dominio, la diferencia media de suficiencia pedagógica fue $\Delta S = 0.0000$ (0 pares mejorados). En el corpus piloto, la ampliación de contexto a 1500 caracteres no suplió la dispersión multi-sección de conceptos de programación complejos.
3. **Mecanismo de Guarda ($C_7$):**
   * Logró $100\%$ de abstención ante consultas OOD (2/2), pero indujo un $94.4\%$ de falso rechazo en dominio (17/18 consultas) debido a la severidad del umbral estático ejecutado ($\tau = 0.35$, corregido documentalmente en CP140).
4. **Costo Computacional de Reranker ($C_5, C_6, C_7$):**
   * El modelo cross-encoder BGE-Reranker-M3 consumió una media de $1746.9 \text{ ms}$ por consulta (99.98% de la latencia total).

---

## 5. CERTIFICACIÓN DE AISLAMIENTO INVIOLABLE DE PRODUCCIÓN

Se ratifica formalmente la verificación de hash SHA-256 de las 6 bases de datos productivas de TALOS V1:
* `cal_store.db`: `82773155ca35028274ba0f378fdcd37a5374bb4483a579654a6e9facfd443782`
* `knowledge_store.db`: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1`
* `quotas.db`: `09838ed16f1bbab384e6a83be651c9f8657db11c6a72caa5c32947a2cc18050d`
* `student_state.db`: `f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d`
* `study_engine.db`: `e3ba06536f7dbba337dee3c1c5f01b43660ce276abb54c5cee2d5defc5b970aa`
* `vector_store.db`: `d6d9f8c8eb6e5188e8e600a73cc05bd001d2e389061815d7d0df33f447a9dde4`

El código de TALOS V1 en `src/` no ha sufrido ninguna modificación (`V1_RUNTIME_MODIFIED = FALSE`).
No se ha realizado selección de producción (`PRODUCTION_SELECTION = NOT_PERFORMED`).
