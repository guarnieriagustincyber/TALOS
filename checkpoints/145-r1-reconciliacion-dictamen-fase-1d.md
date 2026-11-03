# Checkpoint 145-R1: Reconciliación Canónica del Dictamen Post-Ejecución de Fase 1D (Evidence Selection & Calibration)

**Fecha:** 2026-10-05T16:45:00-03:00  
**Fase:** FASE 1 — EVIDENCE RETRIEVAL / SUBFASE 1D — EVIDENCE SELECTION & CALIBRATION  
**Tipo de Documento:** CHECKPOINT DE RECONCILIACIÓN Y GOBERNANZA CANÓNICA  
**Autoridad:** Directiva Canónica CP145-R1 — Reconciliación del Dictamen Post-Ejecución / Antigravity Agent  
**Predecesores Directos:**
* Checkpoint 145 (`checkpoints/145-fase-1d-adjudicacion-post-ejecucion.md`)
* Checkpoint 144 (`checkpoints/144-fase-1d-ejecucion-benchmark-retrieval.md`)
* Checkpoint 143-R1 (`checkpoints/143-r1-reconciliacion-pre-ejecucion-fase-1d.md`)  
**Estatus Canónico de Fase 1D:** **`EXECUTION_VALID | ADJUDICATION_RECONCILED | CP145-R1_STATUS = CANONICAL | FASE_1D_CLOSED = TRUE`**  
**Gobernanza:** `PROMOTION = NOT_AUTHORIZED | PHASE_1E = BLOCKED | FASE_2 = NOT_AUTHORIZED`  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`

---

## 1. ESTADO DE GOBERNANZA

```text
===============================================================================
TALOS V1.5 — CHECKPOINT 145-R1: PHASE 1D ADJUDICATION RECONCILIATION & CLOSURE
===============================================================================

PHASE_1A                        = COMPLETE (CP131)
GATE_1A_1B                      = FORMALIZED (CP133)
FASE_1B                         = COMPLETE / CANONICALLY CLOSED (CP140)
FASE_1C                         = COMPLETE / CERTIFIED (CP142)
FASE_1D                         = RECONCILED / CANONICALLY CLOSED (CP145-R1)
  ├─ ESPECIFICACIÓN TÉCNICA     = v1.0.1-reconciled (CP143-R1)
  ├─ PREREGISTRO FORMAL         = v1.0.1-reconciled (CP143-R1)
  ├─ GUÍA METODOLÓGICA          = v1.0.1-reconciled (CP143-R1)
  ├─ PREFLIGHT TÉCNICO          = PASSED (16/16)
  ├─ EJECUCIÓN EXPERIMENTAL     = VALID (176 celdas, CP144)
  ├─ CONTROLES NEGATIVOS        = PASSED (5/5 NC-01..NC-05)
  ├─ INFORME DE RESULTADOS      = CANONICAL (CP144)
  ├─ ADJUDICACIÓN INICIAL       = AUDITADA / RECONCILIADA (CP145)
  ├─ INFORME RECONCILIADO       = CANONICAL (CP145-R1, SHA-256: 6b8da34c...)
  ├─ NOMENCLATURA CONDICIONES   = C0..C7 RESTAURADA Y VINCULANTE
  ├─ DICTÁMENES DE HIPÓTESIS    = RECONCILED
  │   ├─ H1 (Brecha Rel-Suff)   = NOT_SUPPORTED (inferencial) / INCONCLUSIVE (descriptivo)
  │   │                          (P@1=16.67%, S@1=0.00%, b=3, p_exact=0.1250 unilateral)
  │   ├─ H2 (Expansión Struct)  = INCONCLUSIVE (sin dif. det.) / NOT_SUPPORTED (sin ganancia)
  │   │                          (C5 vs C6 estrictamente pareado, ΔS=0 en 18/18 pares)
  │   ├─ H3 (Híbrido RRF)       = INCONCLUSIVE (empate en MRR) / NOT_SUPPORTED (compuesto)
  │   │                          (nDCG@5=0.1429 > 0.1111, MRR@5=0.1667 == 0.1667)
  │   ├─ H4 (Grid Similitud)    = SUPPORTED (τ* = 0.40 en Dense Qwen C1)
  │   │                          (A_OOD=100%, FRR_ID=11.1%, delimitado al benchmark)
  │   └─ H5 (Guard C7 τ=0.35)   = NOT_SUPPORTED
  │                              (FRR_ID = 94.4% > 20%, sobre-abstención severa)
  └─ CIERRE CANÓNICO 1D         = CERTIFIED
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

## 2. FUENTES DE AUTORIDAD Y REGLA DE NO-MODIFICACIÓN PRIMARIA

En conformidad con la Directiva CP145-R1:
1. Los artefactos primarios crudos de CP144 (`phase1d_raw_execution_results.json`, `phase1d_per_query_results.json`, `phase1d_aggregate_metrics.json`, etc.) **permanecen estrictamente intactos y sin modificación**.
2. No se efectuó ninguna re-ejecución experimental, ninguna modificación de queries, qrels, condiciones, thresholds ni configuración.
3. Todas las correcciones de CP145-R1 se circunscriben al dictamen y sus deducciones metodológicas.

---

## 3. RECONCILIACIÓN DE NOMENCLATURA CANÓNICA C0–C7

Se restaura y certifica la correspondencia canónica de las condiciones evaluadas en CP144:

```text
C0 = COND-BASE-FTS5 (BM25 FTS5 puro)
C1 = COND-DENSE-QWEN (Dense Qwen2.5-Coder-0.5B)
C2 = COND-DENSE-BGE (Dense BGE-small-en-v1.5)
C3 = COND-DENSE-E5 (Dense Multilingual-E5-small)
C4 = COND-HYBRID-RRF (FTS5 + Dense Qwen vía RRF k=60)
C5 = COND-RERANK-BGE (RRF Híbrido + Reranker BGE ONNX CPU)
C6 = COND-EXP-STRUCTURAL (C5 + Expansión Estructural de Chunks)
C7 = COND-GUARDED-FULL (C6 + Compuerta Operacional Guard tau=0.35)
```

Quedan formalmente anuladas y eliminadas designaciones espurias ("Baseline Mock", "C1'", "C2'", etc.).

---

## 4. TABLA CANÓNICA DE MÉTRICAS OFICIALES AGREGADAS (176 CELDAS)

Valores oficiales reproducidos directamente de `phase1d_aggregate_metrics.json` sobre el estrato In-Domain ($N=18$ consultas curriculares):

| ID | Condición Canónica | $P@1$ | $P@3$ | $P@5$ | MRR@5 | nDCG@5 | $S@1$ (Strict) | $S@1$ (Any) | $\Delta_{\text{brecha}}$ | $A_{\text{OOD}}$ | $\text{FRR}_{\text{ID}}$ | Latencia Media (ms) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **C0** | COND-BASE-FTS5 | 0.0556 | 0.0185 | 0.0111 | 0.0556 | 0.0794 | 0.0000 | 0.0556 | 0.0556 | 0.0% | 0.0% | 0.20 |
| **C1** | COND-DENSE-QWEN | **0.1667** | **0.0556** | **0.0333** | **0.1667** | 0.1032 | 0.0000 | 0.0000 | **0.1667** | 0.0% | 0.0% | 0.00 |
| **C2** | COND-DENSE-BGE | **0.1667** | **0.0556** | **0.0333** | **0.1667** | 0.1111 | 0.0000 | 0.0556 | **0.1667** | 0.0% | 0.0% | 0.00 |
| **C3** | COND-DENSE-E5 | 0.0556 | 0.0185 | 0.0111 | 0.0556 | 0.0476 | 0.0000 | 0.0000 | 0.0556 | 0.0% | 0.0% | 0.00 |
| **C4** | COND-HYBRID-RRF | **0.1667** | **0.0556** | **0.0333** | **0.1667** | **0.1429** | 0.0000 | 0.0556 | **0.1667** | 0.0% | 0.0% | 0.02 |
| **C5** | COND-RERANK-BGE | 0.0556 | 0.0185 | 0.0111 | 0.0556 | 0.0635 | 0.0000 | 0.0000 | 0.0556 | 0.0% | 0.0% | 1726.22 |
| **C6** | COND-EXP-STRUCTURAL | 0.0556 | 0.0185 | 0.0111 | 0.0556 | 0.0635 | 0.0000 | 0.0000 | 0.0556 | 0.0% | 0.0% | 1726.30 |
| **C7** | COND-GUARDED-FULL | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0079 | 0.0000 | 0.0000 | 0.0000 | **100.0%** | **94.4%** | 1726.30 |

---

## 5. RESOLUCIÓN DE PUNTOS CLAVE DE LA AUDITORÍA CP145-R1

### 5.1. Reconciliación de H1 (Resolución de Contradicción sobre P@1):
* **Contradicción resuelta:** Se elimina el valor preliminar $33.33\%$ (que correspondía a relevancia débil $\text{rel} \ge 1$). La definición contractual de $P@1$ en CP143-R1 exige unívocamente **$\text{rel} \ge 2$**.
* **Valores unívocos:**
  - $N = 18$ consultas In-Domain.
  - $\overline{P@1} = 3/18 = 0.1667$ ($16.67\%$).
  - $\overline{S@1} = 0/18 = 0.0000$ ($0.00\%$).
  - $\Delta_{\text{brecha}} = 0.1667 \ge 0.15$.
  - Pares discordantes: $b = 3$ (`Q1A2-03`, `Q1A2-07`, `Q1A2-14`), $c = 0$.
* **Test estadístico preregistrado:** Test unilateral exacto de McNemar (binomial):
  $$p_{\text{exact}} = 0.5^b = 0.5^3 = 0.1250$$
* **Dictamen:** **`NOT_SUPPORTED`** bajo criterio inferencial conjunto (requería $p < 0.05$, $b \ge 5$) / **`INCONCLUSIVE`** descriptivo (muestra $N=18$ insuficiente para significancia).

### 5.2. Reconciliación de H2 (Comparación Pareada C5 vs C6):
* **Condiciones:** $C_5$ (Atómica) vs $C_6$ (Expandida).
* **Observación empírica:** En los 18 pares In-Domain, $\Delta S_i = S(C6, q_i) - S(C5, q_i) = 0$ (18 neutrales, 0 mejoradas, 0 degradadas; $\Delta P@5 = 0.0000$).
* **Dictamen:** **`INCONCLUSIVE`** (sin diferencia detectable) / **`NOT_SUPPORTED`** (la ganancia positiva postulada fue nula en este corpus).

### 5.3. Reconciliación de H3 (Retrieval Híbrido RRF):
* **Condiciones:** $C_4$ vs baselines monomodales individuales $C_0 \dots C_3$.
* **Observación empírica:** $\text{nDCG}@5(C4) = 0.1429 > \max(0.1111)$ (+28.6% relativo), pero $\text{MRR}@5(C4) = 0.1667 == \max(0.1667)$ (empate técnico).
* **Dictamen:** **`INCONCLUSIVE`** (bajo regla tripartita de decisión por ventaja en nDCG@5 y empate en MRR@5) / **`NOT_SUPPORTED`** (bajo criterio compuesto estricto).

### 5.4. Reconciliación de H4 (Modelo y Grilla OOD):
* **Identidad del modelo:** **Dense Qwen ($C_1$)**, confirmada por CP143-R1. Se elimina cualquier referencia a "BGE-small".
* **Grilla $\mathcal{T}_{\text{sim}}$ recalculada desde datos brutos:**
  - $\tau = 0.30$: $A_{\text{OOD}} = 0.0\%$, $\text{FRR}_{\text{ID}} = 0.0\%$
  - $\tau = 0.35$: $A_{\text{OOD}} = 0.0\%$, $\text{FRR}_{\text{ID}} = 0.0\%$ (se corrigen valores erróneos de $50\%$ y $5.6\%$)
  - $\tau = 0.40$: $A_{\text{OOD}} = 100.0\%$, $\text{FRR}_{\text{ID}} = 11.1\%$ (Factible: $A=100\% \land \text{FRR} \le 15\%$)
  - $\tau = 0.45$: $A_{\text{OOD}} = 100.0\%$, $\text{FRR}_{\text{ID}} = 50.0\%$ (se corrige valor erróneo de $38.9\%$)
  - $\tau = 0.50$: $A_{\text{OOD}} = 100.0\%$, $\text{FRR}_{\text{ID}} = 88.9\%$
* **Selección ex-ante:** $\tau^* = 0.40$.
* **Dictamen:** **`SUPPORTED`** dentro del grid preregistrado para Dense Qwen ($C_1$), delimitado a la muestra experimental.

### 5.5. Reconciliación de H5 (Compuerta Operacional $C_7$):
* **Parámetro evaluado:** $\tau_{\text{abstain}} = 0.35$ en $C_7$.
* **Observación empírica:** $A_{\text{OOD}} = 100.0\%$, $\text{FRR}_{\text{ID}} = 94.4\%$ (17/18 consultas ID válidas falsamente rechazadas).
* **Dictamen:** **`NOT_SUPPORTED`**.

---

## 6. RECONCILIACIÓN DE CONCLUSIONES DE INGENIERÍA

* **Reranking neuronal ($C_5$) en CPU:** $C_5$ presentó en este benchmark menor desempeño agregado que $C_4$ y una latencia de aproximadamente $1.7\text{ s}$ por consulta en CPU; por tanto, **no existe evidencia en esta muestra experimental para justificar su promoción como mecanismo local de retrieval de Fase 1D**.
* **Calibración de Similitud ($C_1$):** El threshold $\tau^* = 0.40$ seleccionado dentro del grid preregistrado para Dense Qwen satisfizo los criterios definidos en esta muestra experimental.

---

## 7. AUDITORÍA FINAL Y ESTADO DE CIERRE

```text
===============================================================================
CHECKLIST FINAL DE CUMPLIMIENTO CP145-R1
===============================================================================
[PASS] RAW_RESULTS_UNCHANGED         = TRUE (Hash SHA-256 verificado bit a bit)
[PASS] PER_QUERY_RESULTS_UNCHANGED   = TRUE (Hash SHA-256 verificado bit a bit)
[PASS] EXECUTION_MANIFEST_UNCHANGED  = TRUE (Hash SHA-256 verificado bit a bit)
[PASS] QUERIES_UNCHANGED             = TRUE (22 consultas idénticas)
[PASS] QRELS_UNCHANGED               = TRUE (176 celdas idénticas)
[PASS] CONFIG_UNCHANGED              = TRUE (Configuración inalterada)
[PASS] MODEL_IDENTITIES_RECONCILED   = TRUE (H4 anclado exclusivamente en Dense Qwen)
[PASS] C0_C7_NOMENCLATURE_RECONCILED = TRUE (Correspondencia C0..C7 restaurada)
[PASS] H1_STATISTICS_RECONCILED      = TRUE (P@1=16.67%, S@1=0%, b=3, p_exact=0.1250)
[PASS] H2_RECONCILED                 = TRUE (C5 vs C6 estrictamente pareado, ΔS=0)
[PASS] H3_RECONCILED                 = TRUE (nDCG@5 gana, MRR@5 empata, dictamen formal)
[PASS] H4_GRID_RECONCILED            = TRUE (Grilla 0.30..0.50 exacta con τ*=0.40)
[PASS] H5_RECONCILED                 = TRUE (FRR_ID=94.4%, NOT_SUPPORTED formal)
[PASS] DATABASE_CHANGES              = 0 (6 bases SQLite de producción intactas)
[PASS] V1_RUNTIME_MODIFIED           = FALSE (Directorio src/ inalterado)
[PASS] PRODUCTION_SELECTION          = NOT_PERFORMED (Sin selección de producción)
===============================================================================
ESTADO: FASE 1D CANONICALLY CLOSED — PROMOTION & PHASE 1E BLOCKED
===============================================================================
```
