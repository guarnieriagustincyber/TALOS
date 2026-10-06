# Checkpoint 147: Síntesis Global y Cierre Canónico de Fase 1 (Evidence / Retrieval)

**Fecha:** 2026-10-05T17:15:00-03:00  
**Fase:** FASE 1 — EVIDENCE / RETRIEVAL  
**Tipo de Documento:** CHECKPOINT DE SÍNTESIS GLOBAL Y CIERRE CANÓNICO DE FASE 1  
**Autoridad:** Directiva Operativa de Síntesis Global y Cierre Canónico de Fase 1 / Antigravity Agent  
**Referencia Documental Primaria:**
* [`reports/v1_5_phase1/PHASE_1_CANONICAL_SYNTHESIS_AND_CLOSURE.md`](file:///media/agustin/Laboratorio/study-engie/reports/v1_5_phase1/PHASE_1_CANONICAL_SYNTHESIS_AND_CLOSURE.md) (SHA-256: `86479597735cbdee4149abce78d2b89c43639bb5ef567c06387f8c736b9d4e86`)  
**Predecesores Canónicos Directos:**
* Checkpoint 146-R1 (`checkpoints/146-r1-phase-1e-promotion-gate.md`)
* Checkpoint 145-R1 (`checkpoints/145-r1-reconciliacion-dictamen-fase-1d.md`)
* Checkpoint 144 (`checkpoints/144-fase-1d-ejecucion-benchmark-retrieval.md`)
* Checkpoint 142 (`checkpoints/142-fase-1c-ejecucion-frontera-corpus-runtime.md`)
* Checkpoint 140 (`checkpoints/140-reconciliacion-canonica-fase-1b.md`)
* Checkpoint 133 (`checkpoints/133-formalizacion-gate-1a-1b.md`)
* Checkpoint 131 (`checkpoints/131-fase-1a-final-synthesis.md`)  
**Estatus Canónico Final:** **`PHASE_1 = CLOSED | PHASE_1_PROMOTABLE = FALSE | PROMOTION = NOT_AUTHORIZED`**  
**Gobernanza:** `BASELINE = C0 (FTS5 BM25) RETAINED | PHASE_2 = BLOCKED / NOT_AUTHORIZED | PHASE_2.X = CANDIDATE / NOT_AUTHORIZED`  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`

---

## 1. ESTADO EJECUTIVO DE GOBERNANZA

```text
╔══════════════════════════════════════════════════════╗
║              TALOS V1.5 — FASE 1                    ║
║                                                      ║
║  1A  Corpus / Evidence Preparation       CLOSED     ║
║  1B  Evidence / Retrieval Analysis       CLOSED     ║
║  1C  Corpus ↔ Runtime Boundary           CLOSED     ║
║  1D  Retrieval Benchmark                 CLOSED     ║
║  1E  Promotion Gate                      CLOSED     ║
║                                                      ║
║  PHASE 1 PROMOTABLE                    FALSE         ║
║  PROMOTION                             NOT_AUTHORIZED║
║  PRODUCTION BASELINE                   C0 / FTS5    ║
║                                                      ║
║  PHASE 2                              BLOCKED         ║
║  PHASE 2.X                            CANDIDATE       ║
║                                                      ║
║  PRODUCTION DB CHANGES                         0     ║
║  V1 RUNTIME MODIFIED                      FALSE      ║
╚══════════════════════════════════════════════════════╝
```

---

## 2. PREGUNTA CENTRAL Y DICTAMEN DE SÍNTESIS

> **¿Qué quedó demostrado, qué quedó descartado, qué permanece incierto y qué puede —y qué no puede— afirmarse sobre el subsistema de Evidence/Retrieval de TALOS V1.5 al cierre de la Fase 1?**

### 2.1. Síntesis por Subfases
1. **Fase 1A (PDF → Corpus):** Se consolidaron 242 juicios humanos ciegos. Se demostró que modelos de embedding distintos (Qwen, BGE, E5) proyectan geometrías incompatibles sobre el mismo texto (Jaccard@10 $\le 0.313$), prohibiéndose el uso de coseno cruzado (*cross-model cosine prohibited*). Se desagregó el efecto del modelo de la longitud del input, demostrándose que la homogeneización común mitiga la dilución semántica.
2. **Fase 1B (Corpus → Evidence):** Se definió formalmente la brecha entre relevancia atómica y suficiencia didáctica estricta ($S@1$). Se diseñaron y formalizaron en CP140 las hipótesis H1–H5, el framework de 4 niveles y la compuerta operacional.
3. **Fase 1C (Corpus ↔ Runtime Boundary):** Bajo CP142 se verificó de extremo a extremo la cadena de 9 pasos:  
   `SOURCE → EXTRACTED DOCUMENT → CANONICAL CHUNK → HARMONIZED REPRESENTATION → EMBEDDING / INDEX → RUNTIME STORE → RETRIEVAL HIT → CONTEXT PACK → CITATION / PROVENANCE`.  
   Los 9 controles positivos (C0–C8) y 5 controles negativos (NC-01…NC-05) pasaron al 100%, certificando la integridad de identidad y fail-closed de la frontera.
4. **Fase 1D (Retrieval Benchmark):** Se ejecutaron de forma determinista 176 celdas experimentales (22 consultas $\times$ 8 condiciones C0–C7). Se confirmaron las limitaciones de la expansión simple (H2 no soportada) y del guardia operacional C7 (H5 no soportada por falso rechazo masivo del 94.4%), mientras que la calibrabilidad de Qwen quedó demostrada analíticamente (H4 soportada con $\tau^*=0.40$).
5. **Fase 1E (Promotion Gate):** Sometidos los 7 candidatos alternativos a los 7 criterios simultáneos ($G1\dots G7$), ninguno satisfizo el contrato compuesto. En consecuencia, ningún candidato fue promovido y el baseline histórico $C_0$ permanece como motor de producción.

---

## 3. MATRIZ CANÓNICA DE CANDIDATOS

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

> [!IMPORTANT]
> **Aclaración Canónica Obligatoria sobre Dictámenes `DEFER`:**  
> `DEFER` significa que el candidato conserva interés técnico para evaluación en una eventual investigación futura, pero **no posee autorización de promoción, no cuenta con aprobación de sustitución de producción ni constituye una selección implícita de arquitectura futura**.

---

## 4. QUÉ QUEDÓ DEMOSTRADO

1. El baseline $C_0$ continúa siendo operacionalmente válido bajo el contrato evaluado.
2. Ningún candidato $C_1\dots C_7$ satisfizo todos los criterios aplicables de promoción.
3. $C_4$ presentó la mejor señal agregada de $\text{nDCG}@5$ del benchmark ($0.1429$, $+28.6\%$), pero no cumplió el contrato compuesto de promoción.
4. La expansión estructural $C_5 \to C_6$ no produjo mejora observable de suficiencia en el diseño ejecutado ($\Delta S = 0$ en 18/18 pares).
5. $C_7$ consiguió 100% de abstención OOD en el benchmark, pero a costa de un 94.4% de false rejection ID.
6. El reranking $C_5/C_6/C_7$ presentó una penalización de latencia incompatible con el criterio G6 del contrato evaluado ($p95 \approx 1840\text{ ms} \gg 150\text{ ms}$).
7. La frontera corpus/runtime/provenance fue validada íntegramente bajo CP142.
8. La producción permaneció 100% aislada durante todo el ciclo experimental (`DATABASE_CHANGES = 0`, `V1_RUNTIME_MODIFIED = FALSE`).

---

## 5. QUÉ NO QUEDÓ DEMOSTRADO

La Fase 1 **NO demuestra**:
* Que FTS5 sea universalmente superior al retrieval semántico.
* Que los embeddings densos sean inútiles para TALOS.
* Que los modelos Qwen, BGE o E5 sean intrínsecamente deficientes.
* Que el reranking sea inviable en cualquier condición de hardware.
* Que la expansión estructural no pueda funcionar con otro diseño.
* Que $C_4$ sea la arquitectura definitiva de TALOS.
* Que un threshold determinado sea un clasificador universal ID/OOD.
* Que los resultados obtenidos sean generalizables fuera de este benchmark.
* Que una futura ampliación del dataset produzca necesariamente otro resultado.

---

## 6. C4 — LÍNEA DE INVESTIGACIÓN FUTURA (DEFERRED RESEARCH CANDIDATE)

> **C4 NO ES UNA PROMOCIÓN.**

$C_4$ queda formalmente registrado como:
```text
C4 = DEFERRED RESEARCH CANDIDATE
```
Presentó la señal técnica más promisoria en ranking ($\text{nDCG}@5 = 0.1429$) y latencia óptima ($p95 = 0.02\text{ ms}$), pero carece de suficiencia demostrada ($S@1 = 0$) y de guardia OOD integrada. No tiene autorización para sustituir al baseline de producción.

---

## 7. LIMITACIONES ESTADÍSTICAS Y DIRECTRIZ METODOLÓGICA

> **La evaluación observó una brecha descriptiva entre relevancia y suficiencia, pero el tamaño muestral y el número de discordancias observadas no permitieron establecer inferencia estadística concluyente bajo el criterio preregistrado.**

Cualquier futura evaluación de $H_1$ deberá definir **ex ante** un tamaño muestral y una justificación de potencia adecuados. **No deberá fijarse un número objetivo de discordancias para obtener un resultado deseado.**

---

## 8. INTEGRIDAD Y AISLAMIENTO DE PRODUCCIÓN

```text
===============================================================================
AUDITORÍA FORENSE FINAL DE PRODUCCIÓN
===============================================================================
[PASS] cal_store.db:       82773155ca35028274ba0f378fdcd37a5374bb4483a579654a6e9facfd443782
[PASS] knowledge_store.db: fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1
[PASS] quotas.db:          09838ed16f1bbab384e6a83be651c9f8657db11c6a72caa5c32947a2cc18050d
[PASS] student_state.db:   f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d
[PASS] study_engine.db:    e3ba06536f7dbba337dee3c1c5f01b43660ce276abb54c5cee2d5defc5b970aa
[PASS] vector_store.db:    d6d9f8c8eb6e5188e8e600a73cc05bd001d2e389061815d7d0df33f447a9dde4

DATABASE_CHANGES      = 0
V1_RUNTIME_MODIFIED   = FALSE
PRODUCTION_SELECTION  = NOT_PERFORMED
===============================================================================
```

---

## 9. CONCLUSIÓN CANÓNICA DE FASE 1

> **La Fase 1 de TALOS V1.5 queda formalmente cerrada.**
>
> La fase estableció una cadena trazable desde el corpus hasta el runtime, ejecutó el benchmark de retrieval preregistrado y aplicó una compuerta explícita de promoción. Ningún candidato evaluado satisfizo integralmente las condiciones requeridas para sustituir al baseline.
>
> Por tanto, **$C_0$ / FTS5 BM25 permanece como baseline de producción**, sin que ello implique una afirmación de superioridad universal.
>
> **$C_4$ / FTS5 + Qwen RRF queda como línea de investigación futura `DEFERRED`**, no como arquitectura promovida.
>
> La evidencia producida no autoriza actualmente el reemplazo del baseline ni la promoción de un nuevo sustrato de retrieval.
>
> En consecuencia:
>
> ```text
> PHASE_1 = CLOSED
> PHASE_1_PROMOTABLE = FALSE
> PROMOTION = NOT_AUTHORIZED
> BASELINE = C0
> PHASE_2 = BLOCKED / NOT_AUTHORIZED
> PHASE_2.X = CANDIDATE / NOT_AUTHORIZED
> ```
>
> El cierre de la Fase 1 no representa un fracaso del sistema experimental. Representa el cumplimiento de su función: **determinar mediante evidencia qué puede promoverse y qué no puede promoverse sin evidencia suficiente.**

---

## 10. INVENTARIO DE ARTEFACTOS Y VERIFICACIÓN CRIPTOGRÁFICA

```text
┌────────────────────────────────────────────────────────────────────────┬──────────────────────────────────────────────────────────────────┐
│ Artefacto de Cierre CP147                                              │ Hash SHA-256                                                     │
├────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────┤
│ reports/v1_5_phase1/PHASE_1_CANONICAL_SYNTHESIS_AND_CLOSURE.md         │ 86479597735cbdee4149abce78d2b89c43639bb5ef567c06387f8c736b9d4e86 │
│ reports/v1_5_phase1/CP146_R1_PHASE_1E_PROMOTION_GATE_RECONCILIATION.md │ c925b357ded23534a8f7123b6b7549edd940eb5873cc5751401cdc1f1b0d3843 │
│ reports/v1_5_phase1/CP145_R1_PHASE_1D_ADJUDICATION_RECONCILIATION.md   │ 6b8da34cc97b0ba78b89a9fd44df519650091daacf80c50ae758c0da99d9756a │
│ reports/v1_5_phase1/PHASE_1C_CORPUS_RUNTIME_BOUNDARY_REPORT.md         │ 3cf0f6a0e5f47a4f64bf9bac007e36562deba3ba7237a64f55bfe40b27d6fda2 │
│ reports/v1_5_phase1/CP140_PHASE_1B_CANONICAL_RECONCILIATION.md         │ b53b927e366113b91fa02f694601eb0a8524453443a504b8dfcf94d1f27157bc │
│ reports/v1_5_phase1/PHASE_1A_FINAL_SYNTHESIS.md                        │ 0fa35dbfaeb1efb2fb1e36c243bc5529f8f413d964fe514e86121404ea576ceb │
│ experiments/v1_5_phase1d/execution/raw_results/phase1d_raw_execution_re│ 86eb541ffbd1de66a4d092be472bcd2cc09c0f09580097a872965b676ad155e1 │
│ experiments/v1_5_phase1d/execution/metrics/phase1d_per_query_results.js│ 2c496bb8a87e32cd65d17d1ed0c210511c2b26cd4acac37fb397015db4fa3f50 │
│ experiments/v1_5_phase1d/execution/metrics/phase1d_aggregate_metrics.j │ 9cb4b9cd38604f37a197e712d0a48aaa69f4787647ea5cab0cc6c4f2b84ac592 │
│ experiments/v1_5_phase1d/execution/metrics/phase1d_hypotheses_evaluatio│ fa503edacc918e73b764b165ff275e345b8b710c13577e6bb03db0aa27d068ae │
│ experiments/v1_5_phase1d/execution/metrics/phase1d_negative_controls.js│ 8f8cefdb462c99547ad6507862b213c29d7a6281de6b5fc017030eaee2762f1c │
└────────────────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────┘
```

La **Fase 1 de TALOS V1.5 queda formal, canónica y definitivamente cerrada en su totalidad**.
