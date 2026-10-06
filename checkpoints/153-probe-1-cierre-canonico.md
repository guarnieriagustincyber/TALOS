# Checkpoint 153: Cierre Canónico Formal y Gobernanza de PROBE-1

**Fecha:** 2026-10-06T02:05:00-03:00  
**Fase:** INGESTION INTELLIGENCE LAB (v2.0) — PROBE-1  
**Tipo de Documento:** CHECKPOINT CANÓNICO DE CIERRE FORMAL Y ARCHIVO DE EXPERIMENTO  
**Autoridad:** Directiva de Cierre Canónico — PROBE-1 / Antigravity Agent  
**Predecesores Canónicos Directos:**
* Checkpoint 152 (`checkpoints/152-probe-1-test-execution.md`, Holdout TEST Execution & Blind Evaluation)
* Checkpoint 151 (`checkpoints/151-probe-1-dev-calibration.md`, Router Hash: `8753a32db341a6488aa58cb48de40712e7cacb963d6ef1dd2e78df31d70e71fe`)
* Checkpoint 150 (`checkpoints/150-probe-1-sello-criptografico.md`, Seal Digest: `e6e81f98edb872c287ebf87687df0fc6f99b015775b8b0b2d6193106ba82b7cd`)
* Checkpoint 149 (`checkpoints/149-probe-1-diseno-routing-adaptativo.md`)
* Checkpoint 148 (`checkpoints/148-probe-0-ejecucion-y-auditoria-ingestion-lab.md`)  
**Estatus Canónico:** **`PROBE_1 = CLOSED | PROBE_1_RESULT = FAILED_PRODUCTION_GATE | ROUTER_PRODUCTION_STATUS = REJECTED | ROUTER_AVAILABLE_FOR_PRODUCTION = FALSE | PROBE_2 = NOT_STARTED | PROBE_2_EXECUTION = FORBIDDEN`**  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`  

---

## 1. ESTADO DE GOBERNANZA FINAL DE PROBE-1

```text
==================================================================================================
TALOS V1.5 — CHECKPOINT 153: CIERRE CANÓNICO DEFINITIVO DE PROBE-1
==================================================================================================

EXPERIMENT_ID                   = exp_ingestion_probe0_v2 / PROBE-1
EXPERIMENT_STATUS               = CLOSED
EXPERIMENT_RESULT               = FAILED_PRODUCTION_GATE
ROUTER_PRODUCTION_STATUS        = REJECTED
ROUTER_AVAILABLE_FOR_PRODUCTION = FALSE

TEST_SEAL_INTEGRITY             = VERIFIED (Digest: aae910b697c8a4e3fbead40cb0461b39e36b2701c19e2b8c91be11d954a61804)
TEST_SEAL_RECOMPUTED            = TRUE (11/11 artefactos coincidentes bit a bit)
ARTIFACT_INTEGRITY              = VERIFIED (100% íntegros y accesibles)
METRICS_CONSISTENCY             = VERIFIED (Coherencia matemática 100%)

CONFUSION_MATRIX (19 páginas holdout):
  - True Positives (TP)         = 5 (joyanes_ch02_p093, p104, p107, p108, p109)
  - False Positives (FP)        = 1 (joyanes_ch02_p112: lista indentada de ejercicios)
  - True Negatives (TN)         = 9 (joyanes_ch02_p076, p077, p081, p088, p090, p094, p098, p099, p111)
  - False Negatives (FN)        = 4 (p078: tabla sin bordes, p085: variables, p092: UML, p110: N-S)

MÉTRICAS FORMALES AUDITADAS:
  - Missed Escalation Rate (MER)= 44.44% (TOLERANCIA <= 10.0%, FALLO CRÍTICO > 20.0% -> REPROBADO)
  - False Escalation Rate (FER) = 10.00%
  - Accuracy                    = 73.68%
  - Precision                   = 83.33%
  - Recall                      = 55.56%
  - Q̄(B0 = pypdf)               = 2.3421
  - Q̄(B1 = pymupdf)             = 2.3596
  - Q̄(B2 = docling)             = 2.7895
  - Q̄(B3 = adaptive)            = 2.6842 (Delta vs B2: -0.1053 >= -0.15 -> Pareto Cumplido)
  - Costo Relativo T(B3)/T(B2)  = 13.21% (Ahorro de cómputo GPU: 86.79% -> Pareto Cumplido)

EXIT_GATE_VERDICT               = FAIL (Rechazado por violación crítica del límite MER)
PROBE_2_STATUS                  = NOT_STARTED
PROBE_2_EXECUTION               = FORBIDDEN
PROBE_2_IMPLEMENTATION          = NOT_AUTHORIZED
PROBE_2_CALIBRATION             = NOT_AUTHORIZED

PRODUCTION_ISOLATION            = 100% INTACTO (DATABASE_CHANGES = 0, 6/6 DBs inmutables)
V1_RUNTIME_MODIFIED             = FALSE
PRODUCTION_SELECTION            = NOT_PERFORMED
==================================================================================================
```

---

## 2. CIERRE EPISTÉMICO: LO QUE PROBE-1 DEMOSTRÓ Y NO DEMOSTRÓ

### 2.1. Lo que PROBE-1 Demostró Rigurosamente
1. **Viabilidad Económica del Enrutamiento Adaptativo:** El enrutador redujo el costo computacional en un **$86.79\%$** respecto a Docling universal, alcanzando una calidad estructural media de $2.6842$ (estadísticamente indistinguible de los $2.7895$ de Docling en el promedio del capítulo).
2. **Insuficiencia de la Inspección Geométrica Superficial:** Los umbrales lineales basados exclusivamente en recuento de trazos vectoriales ($\tau_{\text{dwg}}=12$) y presencia de líneas de grilla ortogonales ($\tau_{\text{grid}}=1.0$) producen una tasa de omisión inadmisible ($\text{MER} = 44.44\% > 10.0\%$).
3. **No-Universalidad de Docling v2:** Docling no constituye un *ground truth* absoluto; exhibe fallas severas de colapso de código multilínea (`p081`, `p099`) y fracturas de orden de lectura (`p111`).
4. **Eficacia del Sellado Criptográfico:** La barrera de sellado impidió el sobreajuste (*overfitting*) post-hoc, aislando empíricamente la verdad del holdout.

### 2.2. Lo que PROBE-1 NO Demostró (Límites Epistémicos)
1. **No demostró que el routing adaptativo sea inviable:** La hipótesis general de enrutamiento sigue abierta; se refutó específicamente el enrutador lineal basado en trazos vectoriales.
2. **No demostró que Docling o PyMuPDF sean universalmente superiores:** Cada motor posee fortalezas y debilidades complementarias según la tipología de página.
3. **No demostró que los umbrales sean transferibles a otros libros o capítulos:** La calibración fue específica al Capítulo 2 de Joyanes.
4. **No demostró que PROBE-2 vaya a resolver automáticamente los fallos:** Toda hipótesis para PROBE-2 deberá ser preregistrada y sellada independientemente.
5. **No demostró generalización fuera del dominio evaluado.**

---

## 3. MODOS DE FALLA PRESERVADOS CANÓNICAMENTE

### 3.1. False Negatives del Router (Omisiones Críticas)
* **`joyanes_ch02_p078` (Tabla Sin Bordes):** $\text{table\_grid\_score} = 0.0$ por ausencia de líneas ortogonales vectoriales. PyMuPDF linealizó las 4 columnas verticalmente ($S=0$); Docling generó Markdown tabular perfecto ($S=3$).  
  *Hipótesis Estructural:* La complejidad tabular no requiere necesariamente líneas vectoriales; se requiere análisis de espacios en blanco (*whitespace column gaps*).
* **`joyanes_ch02_p085` (Diagrama Conceptual de Variables):** $\text{dwg\_count} = 7 < 12$. PyMuPDF derramó 8 líneas de etiquetas sobre la prosa; Docling lo aisló como imagen.
* **`joyanes_ch02_p092` (Diagramas de Clases UML):** $\text{dwg\_count} = 3 < 12$. Cajas con trazos mínimos o imágenes causaron desorden caótico de atributos y métodos en PyMuPDF.
* **`joyanes_ch02_p110` (Diagramas Nassi-Schneiderman):** $\text{dwg\_count} = 9 < 12$. Rectángulos concéntricos sin diagonales quedaron bajo el umbral $\tau_{\text{dwg}}=12$.  
  *Hipótesis Estructural:* La complejidad estructural relevante no siempre produce una firma vectorial densa.

### 3.2. False Positive del Router (Escalación Innecesaria)
* **`joyanes_ch02_p112` (Lista Indentada de Ejercicios):** Densidad léxica e indentación de la enumeración 2.5–2.15 activaron indebidamente `R4_STRUCTURED_CODE`, gastando $1.48\text{ s}$ en Docling frente a $8.7\text{ ms}$ en PyMuPDF sin ganancia alguna.

### 3.3. Fallas Críticas de Docling v2
* **`joyanes_ch02_p081` y `joyanes_ch02_p099` (Colapso Horizontal de Pseudocódigo):** Docling colapsó bloques completos de algoritmos indentados en un único párrafo continuo dentro de triple comilla (\`\`\`), destruyendo la sangría y estructura que PyMuPDF preservó.
* **`joyanes_ch02_p111` (Desgarro del Orden de Lectura):** Docling intercaló la sección de ejercicios dentro de una frase incompleta del resumen del capítulo, destruyendo la coherencia sintáctica.

---

## 4. AUDITORÍA FORENSE DE INMUTABILIDAD DE PRODUCCIÓN

```text
==================================================================================================
VERIFICACIÓN DE PRODUCCIÓN (data/web_state/*.db)
==================================================================================================
[PASS] cal_store.db:                    82773155ca35028274ba0f378fdcd37a5374bb4483a579654a6e9facfd443782
[PASS] knowledge_store.db:              fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1
[PASS] quotas.db:                       09838ed16f1bbab384e6a83be651c9f8657db11c6a72caa5c32947a2cc18050d
[PASS] student_state.db:                f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d
[PASS] study_engine.db:                 e3ba06536f7dbba337dee3c1c5f01b43660ce276abb54c5cee2d5defc5b970aa
[PASS] vector_store.db:                 d6d9f8c8eb6e5188e8e600a73cc05bd001d2e389061815d7d0df33f447a9dde4
==================================================================================================
DATABASE_CHANGES = 0 (INMUTABILIDAD ESTRICTA PRESERVADA)
V1_RUNTIME_MODIFIED = FALSE
PRODUCTION_SELECTION = NOT_PERFORMED
```

---

## 5. PROHIBICIÓN Y BLOQUEO DE PROBE-2

Conforme a la Sección 7 de la Directiva de Cierre:
```text
PROBE_2_EXECUTION      = FORBIDDEN
PROBE_2_IMPLEMENTATION = NOT_AUTHORIZED
PROBE_2_CALIBRATION    = NOT_AUTHORIZED
```
Queda terminantemente prohibido crear código, datasets, modificar umbrales o ejecutar benchmarks para PROBE-2 sin una directiva formal independiente aprobada previamente por el usuario.

---

## 6. REFERENCIA A ARTEFACTOS CANÓNICOS SELLADOS

* Manifiesto de Sello TEST: `experiments/v1_5_ingestion/probe1/PROBE1_TEST_SEAL_MANIFEST.json` (`SHA-256: aae910b697c8a4e3fbead40cb0461b39e36b2701c19e2b8c91be11d954a61804`)
* Reporte Científico Final: `experiments/v1_5_ingestion/probe1/PROBE1_TEST_FINAL_REPORT.md` (`SHA-256: 19e6b2f16c7886bbdff3bb75e3a667b5b26c12d77afbbeafaa15410c91df8e37`)
* Auditoría de Ejecución: `experiments/v1_5_ingestion/probe1/PROBE1_TEST_EXECUTION_AUDIT.md` (`SHA-256: 00eeb8b3ab650bccfccb2d54f2d97a9dbdf42c99f42ebd851666929982e4bb56`)
* Métricas Formales: `experiments/v1_5_ingestion/probe1/PROBE1_TEST_METRICS.json` (`SHA-256: 5260a10e2e965e877e23ced7771a00e360a9964b5d8fbb40de122e4f2cadc0c7`)
* Adjudicación Humana Ciega: `experiments/v1_5_ingestion/probe1/PROBE1_TEST_ADJUDICATION.jsonl` (`SHA-256: 338f14a196d6c9e581e556d835f143457ea4a6dbcaf77b6caaa23994a7bd3557`)
* Checkpoint de Ejecución TEST: `checkpoints/152-probe-1-test-execution.md` (`SHA-256: c3c2e9f237c0a8c5114696843123a7a9c4246833af934ffdb6b0b12c4b30fd07`)
