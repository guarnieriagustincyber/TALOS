# Checkpoint 145: Auditoría y Adjudicación Formal Post-Ejecución de Fase 1D (Evidence Selection & Calibration)

**Fecha:** 2026-10-05T16:35:00-03:00  
**Fase:** FASE 1 — EVIDENCE RETRIEVAL / SUBFASE 1D — EVIDENCE SELECTION & CALIBRATION  
**Tipo de Documento:** CHECKPOINT DE AUDITORÍA Y ADJUDICACIÓN CANÓNICA  
**Autoridad:** Directiva Canónica CP145 — Auditoría y Adjudicación Post-Ejecución / Antigravity Agent  
**Predecesores Directos:**
* Checkpoint 144 (`checkpoints/144-fase-1d-ejecucion-benchmark-retrieval.md`)
* Checkpoint 143-R1 (`checkpoints/143-r1-reconciliacion-pre-ejecucion-fase-1d.md`)  
**Estatus de Fase 1D:** **`ADJUDICATION_COMPLETED | RESULTS_CANONICAL | FASE_1D_CLOSED`**  
**Gobernanza:** `PROMOTION = NOT_AUTHORIZED | PHASE_1E = NOT_AUTHORIZED`  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`

---

## 1. ESTADO DE GOBERNANZA

```text
===============================================================================
TALOS V1.5 — CHECKPOINT 145: PHASE 1D ADJUDICATION & CANONICAL CLOSURE
===============================================================================

PHASE_1A                        = COMPLETE (CP131)
GATE_1A_1B                      = FORMALIZED (CP133)
FASE_1B                         = COMPLETE / CANONICALLY CLOSED (CP140)
FASE_1C                         = COMPLETE / CERTIFIED (CP142)
FASE_1D                         = ADJUDICATION_COMPLETED / RESULTS_CANONICAL (CP145)
  ├─ ESPECIFICACIÓN TÉCNICA     = v1.0.1-reconciled (CP143-R1)
  ├─ PREREGISTRO FORMAL         = v1.0.1-reconciled (CP143-R1)
  ├─ GUÍA METODOLÓGICA          = v1.0.1-reconciled (CP143-R1)
  ├─ PREFLIGHT TÉCNICO          = PASSED (16/16)
  ├─ EJECUCIÓN EXPERIMENTAL     = COMPLETED (176 celdas, 41.65s, CP144)
  ├─ CONTROLES NEGATIVOS        = PASSED (5/5 NC-01..NC-05)
  ├─ INFORME DE RESULTADOS      = CANONICAL (CP144)
  ├─ INFORME DE ADJUDICACIÓN    = CANONICAL (CP145, SHA-256: 306c6ec1...)
  ├─ ADJUDICACIÓN DE HIPÓTESIS  = RECONCILED (CP145)
  │   ├─ H1 (Brecha Rel-Suff)   = NOT_SUPPORTED (estricto) / INCONCLUSIVE (descriptivo)
  │   ├─ H2 (Expansión Struct)  = NOT_SUPPORTED (ΔS = 0 en 18/18 pares)
  │   ├─ H3 (Híbrido RRF)       = NOT_SUPPORTED (mejor nDCG@5, empate en MRR@5)
  │   ├─ H4 (Grid Similitud)    = SUPPORTED (τ* = 0.40 factible en grid)
  │   └─ H5 (Guard C7 τ=0.35)   = NOT_SUPPORTED (FRR_ID = 94.4% > 20%)
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

## 2. AUDITORÍA DE EJECUCIÓN E INTEGRIDAD

1. **Insumos y Resultados Intactos:**  
   Se auditó mediante SHA-256 que los 9 artefactos sellados en CP143-R1 y los 7 artefactos generados en CP144 permanecen 100% inmutables (`CP144_RAW_RESULTS_INTACT = TRUE`).
2. **Dimensiones y Exclusiones:**  
   Se verificaron las 176 celdas ($22 \text{ consultas} \times 8 \text{ condiciones}$). Cero exclusiones post-hoc.
3. **Controles Negativos (NC-01 a NC-05):**  
   Los 5 controles deterministas registraron veredicto `PASS` al 100%.
4. **Integridad de Producción:**  
   Las 6 bases productivas en `data/web_state/*.db` conservan sus hashes baseline idénticos bit a bit (`DATABASE_CHANGES = 0`). El directorio `src/` no recibió ninguna edición (`V1_RUNTIME_MODIFIED = FALSE`).

---

## 3. TABLA CANÓNICA DE MÉTRICAS OFICIALES AGREGADAS

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

## 4. MATRIZ CANÓNICA DEFINITIVA DE ADJUDICACIÓN H1–H5

```text
┌───────────┬──────────────────────────────────────────┬──────────────────────────────────────┬────────────────────────┐
│ Hipótesis │ Resultado Observado (CP144)              │ Criterio Preregistrado (CP143-R1)    │ Dictamen Final CP145   │
├───────────┼──────────────────────────────────────────┼──────────────────────────────────────┼────────────────────────┤
│ H1        │ Brecha descriptiva 0.1667; b=3, p=0.1250 │ Δ >= 0.15 Y test exacto p < 0.05     │ NOT_SUPPORTED (Estricto│
│           │                                          │ (b >= 5)                             │ / INCONCLUSIVE en cat.)│
│ H2        │ ΔS = 0; 18/18 neutrales; P@5 idéntica    │ Incremento de suficiencia pareada    │ NOT_SUPPORTED          │
│ H3        │ nDCG@5: 0.1429 vs 0.1111; MRR: 0.1667 emp│ nDCG@5 > max Y MRR@5 > max           │ NOT_SUPPORTED          │
│ H4        │ τ = 0.40: A_OOD = 100.0%, FRR_ID = 11.1% │ A_OOD = 100% Y FRR_ID <= 15% en grid │ SUPPORTED (τ* = 0.40)  │
│ H5        │ A_OOD = 100.0%, FRR_ID = 94.4%           │ A_OOD = 100% Y FRR_ID <= 10% (C7)    │ NOT_SUPPORTED          │
└───────────┴──────────────────────────────────────────┴──────────────────────────────────────┴────────────────────────┘
```

### Fundamentos de Reconciliación Epistemológica:
1. **H1:** La brecha sustantiva se observa ($\Delta = 0.1667 \ge 0.15$), pero con $b=3 < 5$ pares discordantes el p-valor exacto es $p=0.1250 \ge 0.05$. Se prohíbe declarar soporte estadístico inferencial con $N=18$.
2. **H2:** La hipótesis exigía una mejora observable de suficiencia por expansión estructural. Al registrarse $\Delta S = 0$ en el 100% de los casos, el dictamen formal es **`NOT_SUPPORTED`**.
3. **H3:** $C_4$ alcanzó el mejor nDCG@5 del benchmark ($0.1429$ vs $0.1111$), pero empató en MRR@5 ($0.1667 == 0.1667$). Bajo la regla compuesta estricta pre-registrada, el empate técnico no se transforma en victoria: **`NOT_SUPPORTED`**.
4. **H4:** Dentro de la grilla $\mathcal{T}_{\text{sim}}$, $\tau = 0.40$ cumple unívocamente ambos criterios pre-registrados ($A_{\text{OOD}} = 100\%, \text{FRR}_{\text{ID}} = 11.1\% \le 15\%$). Dictamen: **`SUPPORTED`** como parámetro óptimo de la grilla auditada.
5. **H5:** El guard $C_7$ con $\tau_{\text{abstain}} = 0.35$ produce un falso rechazo masivo e inaceptable ($94.4\% > 20\%$). Dictamen: **`NOT_SUPPORTED`**, prohibiendo cualquier re-sintonización retroactiva.

---

## 5. OBSERVACIONES DE INGENIERÍA (DESACOPLADAS DE LAS HIPÓTESIS)

* **Retrieval Híbrido ($C_4$):** Ofrece la mejor combinación observada de ranking global (nDCG@5 = 0.1429) y eficiencia de ingeniería ($0.02\text{ ms}$ de latencia en memoria).
* **Reranker Neuronal ($C_5$):** Añade $\approx 1.7\text{ s}$ de latencia en CPU sin mejorar la precisión Top-1 en este corpus pequeño de 64 chunks frente a los métodos densos directos.
* **Calibración de Rechazo:** La calibración estática de similitud en $C_1$ con $\tau = 0.40$ exhibe un balance significativamente más viable ($\text{FRR} = 11.1\%$) que el guard actual de $C_7$ bajo $\tau = 0.35$ ($\text{FRR} = 94.4\%$).

---

## 6. INVENTARIO DE ARTEFACTOS Y VERIFICACIÓN CRIPTOGRÁFICA

```text
┌────────────────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────┐
│ Artefacto de CP145                                                     │ Hash SHA-256                                                     │
├────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│ reports/v1_5_phase1/CP145_PHASE_1D_ADJUDICATION_REPORT.md              │ 306c6ec1f3790d0afe1f3e79d2c294188946573e94d07e117dd9c4425ab3acd9 │
│ reports/v1_5_phase1/PHASE_1D_RETRIEVAL_BENCHMARK_REPORT.md             │ c517e279e87dfb146aa74c98b3f853bd9283bab9671b6b92eaaafc9073236680 │
│ experiments/v1_5_phase1d/execution/PHASE_1D_BENCHMARK_EXECUTION_MANIFEST│ f4a3fe9c670f38684c1e96d8fb43964724087edf67ce401a4cee57ef68a541bc │
│ experiments/v1_5_phase1d/execution/raw_results/phase1d_raw_execution_re│ 86eb541ffbd1de66a4d092be472bcd2cc09c0f09580097a872965b676ad155e1 │
│ experiments/v1_5_phase1d/execution/metrics/phase1d_aggregate_metrics.j │ 9cb4b9cd38604f37a197e712d0a48aaa69f4787647ea5cab0cc6c4f2b84ac592 │
│ experiments/v1_5_phase1d/execution/metrics/phase1d_hypotheses_evaluatio│ fa503edacc918e73b764b165ff275e345b8b710c13577e6bb03db0aa27d068ae │
│ experiments/v1_5_phase1d/execution/metrics/phase1d_negative_controls.js│ 8f8cefdb462c99547ad6507862b213c29d7a6281de6b5fc017030eaee2762f1c │
└────────────────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────┘
```

---

## 7. AUDITORÍA DE INMUTABILIDAD DE LAS BASES PRODUCTIVAS

```text
┌──────────────────────────────────┬──────────────────────────────────────────────────────────────────┬──────────────┐
│ Base de Datos de Producción      │ Hash SHA-256 Verificado Post-Adjudicación                        │ Estado       │
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

## 8. CONDICIÓN DE CIERRE Y ESTADO DE GOBERNANZA

```text
FASE_1D_SPECIFICATION       = RECONCILED
FASE_1D_PREREGISTRATION     = RESEALED
FASE_1D_PREFLIGHT           = PASSED
FASE_1D_EXECUTION           = COMPLETED
FASE_1D_ADJUDICATION        = COMPLETED
FASE_1D_RESULTS             = CANONICAL
DATABASE_CHANGES            = 0
V1_RUNTIME_MODIFIED         = FALSE
PRODUCTION_SELECTION        = NOT_PERFORMED
PROMOTION                   = NOT_AUTHORIZED
PHASE_1E                    = NOT_AUTHORIZED
```

La auditoría y adjudicación de la Fase 1D quedan formalmente concluidas. La Fase 1D queda canónicamente cerrada. Cualquier decisión de promoción arquitectónica y el eventual inicio de la Fase 1E permanecen **estrictamente bloqueados** a la espera de la correspondiente directiva independiente de Promotion Gate.
