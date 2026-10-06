# Checkpoint 140: Reconciliación Canónica y Cierre Metodológico Formal de Fase 1B (Corpus → Evidence)

**Fecha:** 2026-10-05T15:45:00-03:00  
**Fase:** FASE 1 — EVIDENCE RETRIEVAL / SUBFASE 1B — CORPUS → EVIDENCE  
**Tipo de Documento:** CHECKPOINT DE RECONCILIACIÓN DOCUMENTAL Y GOBERNANZA  
**Autoridad:** Directiva Canónica CP140 / Antigravity Agent  
**Predecesores Directos:**
* Checkpoint 137 (`checkpoints/137-ejecucion-experimental-fase-1b.md`)
* Checkpoint 138 (`checkpoints/138-incorporacion-candidatos-decision-estructurada-fase2.md`)
* Checkpoint 139 (`checkpoints/139-adjudicacion-humana-ciega-qrel-1b-final.md`)  
**Estatus de CP140:** `CP140 = PASS`  
**Estatus Canónico de Fase 1B:** `FASE 1B = COMPLETE / CANONICALLY CLOSED`  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`

---

## 1. ESTADO DE GOBERNANZA Y RECONCILIACIÓN

```text
===============================================================================
TALOS V1.5 — CHECKPOINT 140: CANONICAL RECONCILIATION & PHASE 1B FORMAL CLOSURE
===============================================================================

SEALED_PROTOCOL_VERIFIED               = TRUE (reports/v1_5_phase1/PHASE_1B_EXPERIMENTAL_DESIGN.md)
H1_H5_DEFINITIONS_RECONCILED           = TRUE (Restored to exact literal sealed text)
C7_THRESHOLD_RECONCILED                = TRUE (Executed = 0.35, "0.50" = documentary errata)
QREL_FINAL_INTACT                      = TRUE (QREL_1B_FINAL.json unchanged, 176 cells)
FINAL_METRICS_TRACEABLE_TO_FINAL_QREL  = TRUE (100% derived from QREL_1B_FINAL)
POST_HOC_HYPOTHESIS_RELABELING_REMOVED = TRUE (Non-canonical labels corrected)
PROTECTED_ARTIFACTS_UNCHANGED          = TRUE (All experimental artifacts bit-for-bit identical)
PRODUCTION_UNCHANGED                   = TRUE (DATABASE_CHANGES = 0, 6 SQLite DBs identical)
V1_RUNTIME_UNCHANGED                   = TRUE (V1_RUNTIME_MODIFIED = FALSE)
DOCUMENTATION_CORRECTED                = TRUE (Only interpretive reports adjusted)

FASE_1A                                = COMPLETE (CP131)
GATE_1A_1B                             = FORMALIZED (CP133)
FASE_1B                                = CANONICALLY CLOSED (CP140)
FASE_1C                                = PENDING SEPARATE AUTHORIZATION
FASE_1D                                = PENDING
FASE_1E                                = BLOCKED (Promotion Gate)
FASE_2                                 = NOT AUTHORIZED
FASE_2.X (MODELOS DECISIÓN ESTRUC.)    = CANDIDATE / NOT AUTHORIZED (CP138)

===============================================================================
```

---

## 2. RESOLUCIÓN DE DISCREPANCIAS DOCUMENTALES

En estricta aplicación del principio rector **"No se corrige la evidencia para que coincida con el informe; se corrige el informe para que coincida con la evidencia y con el protocolo sellado"**:

### 2.1 Umbral Operativo de C7
* **Evidencia en Artefactos:** `PHASE_1B_EXECUTION_MANIFEST.json` (línea 197), `execution_trace.json` (líneas 10–23) y `phase_1b_runner.py` (líneas 14, 555, 558) demuestran que el threshold efectivamente ejecutado fue **$\tau = 0.35$**.
* **Corrección:** Se determinó que la mención a `0.50` en borradores narrativos previos constituyó una errata documental. `0.35` permanece como el único valor experimental válido y los informes fueron corregidos.

### 2.2 Eliminación del Re-etiquetado Post Hoc de Hipótesis
* **H1 (Brecha Estructural Relevancia-Suficiencia):** Se restauró el enunciado sellado. La suficiencia estricta Top-1 fue $0.0000$ ($0/18 \le 15\%$), demostrando el desacoplamiento respecto a la relevancia temática.
* **H2 (Expansión Contextual Determinista Pareada C5 vs C6):** Confirmada como `NOT_SUPPORTED` en el corpus piloto ($\Delta S = 0.0000$, 0/18 mejorados).
* **H3 (Complementariedad de Fusión Híbrida RRF C4 vs C0 y C1):** Confirmada como `SUPPORTED` en la muestra observada ($nDCG@5(C_4) = 0.1429 > C_0(0.0794)$ y $> C_1(0.1032)$ con $MRR@5 \ge$).
* **H4 (Inutilidad de Umbrales Estáticos Coseno):** Reconciliada como evaluable a partir de las puntuaciones crudas de similitud coseno. En BGE ($C_2$) y E5 ($C_3$), ningún $\tau \in [0.40, 0.85]$ separa OOD sin un falso rechazo masivo en dominio.
* **H5 (Abstención Operacional Mediante Cross-Encoder Multilingüe):** Confirmada como `NOT_SUPPORTED` bajo el criterio preregistrado ($\le 10\%$ de falso rechazo), ya que $C_7$ indujo un $94.4\%$ de falso rechazo in-domain.
* **Latencia (`Q-EXP-01`):** Se removió formalmente el etiquetado no canónico de latencia como "H5". La latencia permanece clasificada como telemetría operacional de ingeniería.

---

## 3. SEPARACIÓN EN CUATRO NIVELES METODOLÓGICOS

1. **Nivel A (Datos Observados):** Rankings crudos, latencias y decisiones binarias inmutables en `raw_rankings.json` y `execution_trace.json`.
2. **Nivel B (Métricas Calculadas):** Precisión, MRR, nDCG, suficiencia y tasas de abstención derivadas exclusivamente de `QREL_1B_FINAL.json`.
3. **Nivel C (Hipótesis Preregistradas):** Evaluación objetiva contra los enunciados y criterios preregistrados en `PHASE_1B_EXPERIMENTAL_DESIGN.md`.
4. **Nivel D (Interpretación y Límites):** Restricción estricta al tamaño muestral ($N=22$), ausencia de inferencia poblacional y no-promoción a producción.

---

## 4. INVENTARIO DE ARTEFACTOS Y VERIFICACIÓN FORENSE

| Artefacto | Ruta | SHA-256 | Estado |
| :--- | :--- | :--- | :--- |
| **Protocolo Sellado** | `reports/v1_5_phase1/PHASE_1B_EXPERIMENTAL_DESIGN.md` | `0f61adfbb5048982c77cab8388796319c8b8c99d1726f4fde9826ea992c9f426` | Inmutable |
| **Execution Trace** | `experiments/v1_5_phase1b/execution/technical_logs/execution_trace.json` | `7007d3647ff0adc78722b7e39b890eb079e0dcde16053b8c26093fac6b5ea4d1` | Inmutable |
| **Execution Manifest**| `experiments/v1_5_phase1b/execution/PHASE_1B_EXECUTION_MANIFEST.json` | `e8b50b35cb8c4ec8fa3e4fcdee88c1ce2b6c2abee48fb79cf42e1c9590375d32` | Inmutable |
| **Raw Rankings** | `experiments/v1_5_phase1b/execution/raw_results/raw_rankings.json` | `7a09cb6b52c9b493693f4054d8fc0b9b4eae5180ddea9f83792c581a42cc4a1f` | Inmutable |
| **QREL Definitivo** | `experiments/v1_5_phase1b/execution/metrics/QREL_1B_FINAL.json` | `497c7b37d8e01ad03d58dcb7694d9df616c243545ea48ed0ede270ecf7b583b3` | Inmutable |
| **Métricas Finales** | `experiments/v1_5_phase1b/execution/metrics/FINAL_METRICS_1B.json` | `59dc7c9cf92a46f9abb84e29dfbe7b25213e322d154acd186758137a8fe1f44c` | Inmutable |
| **Informe Reconciliación**| `reports/v1_5_phase1/CP140_PHASE_1B_CANONICAL_RECONCILIATION.md` | `860e80df45ede7d8f6ceda4b37930c0d79c886d8522873734686165d2a4831ea` | `OFFICIAL` |

---

## 5. AISLAMIENTO DE PRODUCCIÓN CERTIFICADO

Se ratifica la verificación bit a bit de las 6 bases de datos productivas:
* `cal_store.db`: `82773155ca35028274ba0f378fdcd37a5374bb4483a579654a6e9facfd443782`
* `knowledge_store.db`: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1`
* `quotas.db`: `09838ed16f1bbab384e6a83be651c9f8657db11c6a72caa5c32947a2cc18050d`
* `student_state.db`: `f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d`
* `study_engine.db`: `e3ba06536f7dbba337dee3c1c5f01b43660ce276abb54c5cee2d5defc5b970aa`
* `vector_store.db`: `d6d9f8c8eb6e5188e8e600a73cc05bd001d2e389061815d7d0df33f447a9dde4`

```text
DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED
```

---

## 6. TRANSICIÓN METODOLÓGICA Y SIGUIENTE PASO

Fase 1B queda **formalmente cerrada de manera canónica**.
El siguiente paso autorizado es la preparación de la directiva independiente para:

```text
FASE 1C — CORPUS ↔ RUNTIME BOUNDARY (PENDING SEPARATE AUTHORIZATION)
```
