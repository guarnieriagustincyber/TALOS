# TALOS V1.5 — INGESTION INTELLIGENCE LAB
## AUDITORÍA CANÓNICA DE EJECUCIÓN EN TEST Y EVALUACIÓN CIEGA (PROBE-1)

**Versión:** 1.0.0-canonical  
**Fecha de Auditoría:** 2026-10-06  
**Fase:** Ingestion Intelligence Lab (v2.0)  
**Experimento:** `exp_ingestion_probe0_v2` → `PROBE-1: Adaptive Structural Routing`  
**Estado:** `TEST_EXECUTION_COMPLETED | BLIND_ADJUDICATION_FINISHED | AUDIT_PASSED`  
**Autoridad:** Directiva Canónica de Ejecución del Holdout (v1.0) & Micro-Directiva de Preflight  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`  

---

## 1. RESUMEN EJECUTIVO DE AUDITORÍA

Se ha ejecutado la auditoría formal y forense de la evaluación en holdout (**TEST Set**, 19 páginas físicas independientes de Luis Joyanes Aguilar, Cap. 2) para el enrutador estructural adaptativo de **PROBE-1**.

La auditoría certifica que:
1. El enrutador evaluado correspondió bit a bit al enrutador congelado tras DEV (`ROUTER_HASH: 8753a32db341a6488aa58cb48de40712e7cacb963d6ef1dd2e78df31d70e71fe`).
2. Se aplicó estrictamente la regla de **CERO RECALIBRACIÓN**: ningún umbral ($\tau_{\text{dwg}}=12, \tau_{\text{grid}}=1.0, \tau_{\text{code}}=0.20, \tau_{\text{indent}}=3, \tau_{\text{dots}}=3$), regla ni feature fue alterado post-seal ni durante TEST.
3. Las extracciones de las 4 condiciones experimentales ($B_0=\text{pypdf}, B_1=\text{pymupdf}, B_2=\text{docling}, B_3=\text{adaptive}$) fueron ejecutadas en Google Colab sobre GPU T4 y verificadas contra el entorno canónico.
4. La adjudicación humana se ejecutó bajo protocolo de doble ciego criptográfico con anonimización de motores (`TOOL_ALPHA, TOOL_BETA, TOOL_GAMMA`) bajo modalidad $N=1$ especialista humano independiente (Control C01).
5. La verdad fundamental `DOCLING_BENEFICIAL` se derivó formalmente de `PROBE1_BENEFIT_DEFINITION.md` (Condición A y Condición B) sin definiciones circulares.
6. Todas las bases de datos de producción (`data/web_state/*.db`) permanecen estrictamente inmutadas (`DATABASE_CHANGES = 0`).

```text
┌────────────────────────────────────────────────────────────────────────┐
│ DICTAMEN DE AUDITORÍA DE EJECUCIÓN: TEST_AUDIT = PASSED                │
├────────────────────────────────────────────────────────────────────────┤
│ PRECONDICIONES CONGELADAS       : VERIFICADAS Y CONFORMES              │
│ INTEGRIDAD DEL HOLDOUT TEST     : 19 PÁGINAS FÍSICAS (SHA-256 CONFORME)│
│ REGLA DE CERO RECALIBRACIÓN     : 100% CUMPLIDA (0 PARÁMETROS TOCADOS) │
│ PROTOCOLO DOBLE CIEGO           : EJECUTADO Y AUDITADO (19 PÁGINAS)    │
│ CROSS-ENVIRONMENT REPRODUCIBILITY: COLAB GPU T4 ACREDITADO             │
│ MATRIZ DE CONFUSIÓN DEL ROUTER  : TP=5, FP=1, TN=9, FN=4               │
│ MISSED ESCALATION RATE (MER)    : 44.44% (> 10.0% TOLERANCIA PREVISTA) │
│ REDUCCIÓN DE COSTO COMPUTACIONAL: 86.79% (COSTO RELATIVO = 13.21%)     │
│ CALIDAD MEDIA ESTRUCTURAL       : Q(B3)=2.6842 vs Q(B2)=2.7895 (PARETO)│
│ EXIT GATE METODOLÓGICO          : FAIL (RECHAZO POR SEGURIDAD ESTRUCT) │
│ INTEGRIDAD DE PRODUCCIÓN        : 6/6 DB INTACTAS (DATABASE_CHANGES=0) │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. AUDITORÍA DEL ESTADO INICIAL Y CONGELAMIENTO DEL ROUTER

Conforme a la Sección 1 de la directiva canónica de TEST, se auditó el estado del enrutador antes de la ejecución:

| Control | Parámetro Requerido | Valor Auditado | Dictamen |
|---|---|---|:---:|
| `ROUTER_STATE` | `ROUTER_FROZEN = TRUE` | `TRUE` | **PASS** |
| `ROUTER_VERSION` | `v1.0.1-calibrated-frozen` | `v1.0.1-calibrated-frozen` | **PASS** |
| `ROUTER_DIGEST` | `8753a32db341a6488aa58cb48de40712e7cacb963d6ef1dd2e78df31d70e71fe` | `8753a32db341a6488aa58cb48de40712e7cacb963d6ef1dd2e78df31d70e71fe` | **PASS** |
| `IMPLEMENTATION_PREFLIGHT`| `GATE = VALIDATED` | `experiments/v1_5_ingestion/probe1/PROBE1_TEST_IMPLEMENTATION_PREFLIGHT.md` | **PASS** |
| `TAU_DWG` | `12` | `12` (Inmutable) | **PASS** |
| `TAU_GRID` | `1.0` | `1.0` (Inmutable) | **PASS** |
| `TAU_CODE` | `0.20` | `0.20` (Inmutable) | **PASS** |
| `TAU_INDENT` | `3` | `3` (Inmutable) | **PASS** |
| `TAU_DOTS` | `3` | `3` (Inmutable) | **PASS** |

---

## 3. AUDITORÍA DE INTEGRIDAD DEL CONJUNTO TEST (HOLDOUT)

### 3.1. Slice Físico Canónico de TEST
Se verificó la integridad física y criptográfica del documento procesado:
* **Archivo:** `drive_upload_ingestion_probe1_test/data/joyanes_ch02_test_19p.pdf`
* **SHA-256 Auditado:** `69d607feec38c4c34d52a6e10666a4c0520ebfe8846cc859f234e9b750ff2baf`
* **Páginas Físicas:** 19 páginas (`[76, 77, 78, 81, 85, 88, 90, 92, 93, 94, 98, 99, 104, 107, 108, 109, 110, 111, 112]`).
* **Intersección con DEV_SET:** $\text{TEST\_SET} \cap \text{DEV\_SET} = \emptyset$ ($0$ páginas en común).

### 3.2. Manifest Canónico
* **Archivo:** `experiments/v1_5_ingestion/probe1/PROBE1_TEST_MANIFEST.json`
* **Total de entradas:** 19 registros de página.
* **Hash del Manifiesto:** Conforme y validado por preflight.

---

## 4. AUDITORÍA DEL PAQUETE Y EJECUCIÓN EN GOOGLE COLAB

### 4.1. Configuración de Ejecución
* **Notebook:** `drive_upload_ingestion_probe1_test/PROBE1_TEST_EXECUTION.ipynb`
* **Entorno:** Google Colab, GPU Tesla T4 (15.3 GB VRAM), CUDA 12.x, Python 3.11.
* **Paquete de Retorno:** `drive_upload_ingestion_probe1_test/PROBE1_TEST_RESULTS.zip`
* **SHA-256 del Paquete:** `84f4f346b95b87198bb6246e4fd44e2195f2694a97491d9d8328da9d80c3eb14`

### 4.2. Integridad de Artefactos de Retorno
Los contenidos desempaquetados en `experiments/v1_5_ingestion/probe1/colab_test_results/results/` fueron auditados:
1. `PROBE1_TEST_FEATURES.jsonl`: 19 registros de características calculadas deterministamente.
2. `PROBE1_TEST_ROUTER_RESULTS.jsonl`: 19 decisiones de enrutamiento con telemetría completa.
3. `PROBE1_TEST_BASELINE_RESULTS.jsonl`: 19 registros de latencias y recuentos de caracteres para $B_0, B_1, B_2, B_3$.
4. `PROBE1_TEST_BLIND_ITEMS.json`: 19 textos ciegos (`tool_alpha_text, tool_beta_text, tool_gamma_text`).
5. `masking_key_unblind.json`: Clave de mapeo pseudoaleatorio por página.
6. `extractions/`: 19 archivos Markdown por cada motor ($19 \times 4 = 76$ archivos de texto extraído).

---

## 5. AUDITORÍA DE CERO RECALIBRACIÓN (STRICT NO-RECALIBRATION)

Se verificó el código y ejecución del enrutador en TEST:
* **Código de Enrutamiento:** `src/router.py` ejecutado en Colab coincidió exactamente con el hash sellado `49938915444ecf22142917e0b308647f41fb687828938223a249c4c3394c3f32`.
* **Reglas Ejecutadas:**
  - `R1_BORDERED_TABLE`: No gatillada en TEST (todas las tablas carecían de líneas ortogonales vectoriales completas).
  - `R2_VECTOR_FLOWCHART`: Gatillada en 5 páginas (`p093, p104, p107, p108, p109`) donde $\text{dwg\_count} \ge 12$.
  - `R3_PARALLEL_COLUMN`: No gatillada en TEST.
  - `R4_STRUCTURED_CODE`: Gatillada en 1 página (`p112`, $\text{code} \ge 0.20 \land \text{indent} \ge 3$).
  - `R0_FAST_DEFAULT`: Gatillada en las 13 páginas restantes.
* **Veredicto:** **CERO RECALIBRACIÓN CERTIFICADA**. Ningún umbral fue adaptado retrospectivamente a las peculiaridades del conjunto TEST.

---

## 6. AUDITORÍA DEL PROTOCOLO DE CEGAMIENTO Y ADJUDICACIÓN

### 6.1. Protocolo de Enmascaramiento Criptográfico
* Conforme a `PROBE1_HUMAN_ADJUDICATION_PROTOCOL.md` (Control C06), cada página $p$ recibió una permutación pseudoaleatoria de $\{	ext{pypdf}, 	ext{pymupdf}, 	ext{docling}\} 	o \{	ext{TOOL\_ALPHA}, 	ext{TOOL\_BETA}, 	ext{TOOL\_GAMMA}\}$.
* Se auditó que la asignación no tuviera correlaciones constantes entre páginas.

### 6.2. Adjudicación Humana Especialista ($N=1$)
* Conforme al Control C01 y a la sección 4 de `PROBE1_HUMAN_ADJUDICATION_PROTOCOL.md`:
  > Se declara formalmente que la adjudicación se realiza bajo modalidad $N=1$ especialista humano independiente en ingeniería de sistemas pedagógica, reconociendo la ausencia de coeficientes Kappa inter-evaluador como limitación metodológica preregistrada.
* Se adjudicaron las 19 páginas a lo largo de las 5 dimensiones formales: `TABLE_STRUCTURE`, `FLOWCHART_DIAGRAM_ISOLATION`, `CODE_STRUCTURE`, `HEADING_STRUCTURE`, `READING_ORDER`.
* Las celdas ausentes fueron rigurosamente marcadas como `NOT_APPLICABLE (N/A)`.

### 6.3. Verdad Fundamental `DOCLING_BENEFICIAL`
Conforme a `PROBE1_BENEFIT_DEFINITION.md`:
* **Condición A:** Salto de $\ge 1.0$ en dimensión mayor (`TABLE`, `DIAGRAM`, `CODE`) con $S_{\text{docling}} \ge 2$ y sin regresión severa ($\le 1.0$).
* **Condición B:** Ganancia promedio $\bar{\Delta} \ge 0.50$.
* **Regla de Empate (§5.1):** Prosa expositiva continua equivalente asignada contractualmente a `DOCLING_BENEFICIAL = FALSE` para evitar sesgo de costo injustificado.

---

## 7. AUDITORÍA MATEMÁTICA DE MÉTRICAS Y TELEMETRÍA

### 7.1. Matriz de Confusión
Sobre $|	ext{TEST}| = 19$ páginas físicas:

```text
                        ROUTER: DOCLING     ROUTER: PYMUPDF     TOTAL
DOCLING_BENEFICIAL: TRUE       5 (TP)              4 (FN)         9 (P)
DOCLING_BENEFICIAL: FALSE      1 (FP)              9 (TN)        10 (N)
TOTAL                          6                  13             19
```

* **True Positives ($TP = 5$):** `joyanes_ch02_p093`, `p104`, `p107`, `p108`, `p109`.
* **False Positives ($FP = 1$):** `joyanes_ch02_p112` (lista indentada de ejercicios 2.5–2.15 confundida con código estructurado por R4).
* **True Negatives ($TN = 9$):** `joyanes_ch02_p076`, `p077`, `p081`, `p088`, `p090`, `p094`, `p098`, `p099`, `p111`.
* **False Negatives ($FN = 4$):**
  1. `joyanes_ch02_p078`: Tabla de depreciación sin bordes vectoriales ($\text{grid\_score} = 0.0$).
  2. `joyanes_ch02_p085`: Diagrama conceptual de variables locales/globales ($\text{dwg\_count} = 7 < 12$).
  3. `joyanes_ch02_p092`: Diagramas UML de clases con 6 compartimentos ($\text{dwg\_count} = 3 < 12$).
  4. `joyanes_ch02_p110`: Diagramas Nassi-Schneiderman (§2.7.3, $\text{dwg\_count} = 9 < 12$).

### 7.2. Métricas de Clasificación
* **Missed Escalation Rate (MER):**
  $$\text{MER} = \frac{FN}{TP + FN} = \frac{4}{9} = \mathbf{44.44\%}$$
* **False Escalation Rate (FER):**
  $$\text{FER} = \frac{FP}{FP + TN} = \frac{1}{10} = \mathbf{10.00\%}$$
* **Accuracy:**
  $$\text{Accuracy} = \frac{5 + 9}{19} = \mathbf{73.68\%}$$
* **Precision:**
  $$\text{Precision} = \frac{5}{5 + 1} = \mathbf{83.33\%}$$
* **Recall:**
  $$\text{Recall} = \frac{5}{9} = \mathbf{55.56\%}$$

### 7.3. Calidad Estructural Media ($\bar{Q} \in [0, 3]$)
* $B_0$ (`pypdf`): $\bar{Q}(B_0) = \mathbf{2.3421}$
* $B_1$ (`pymupdf`): $\bar{Q}(B_1) = \mathbf{2.3596}$
* $B_2$ (`docling`): $\bar{Q}(B_2) = \mathbf{2.7895}$
* $B_3$ (`adaptive`): $\bar{Q}(B_3) = \mathbf{2.6842}$

$$\Delta \bar{Q}(B_3 - B_2) = 2.6842 - 2.7895 = -0.1053 \quad (\ge -0.15 \implies \text{Pareto Condition Satisfied})$$
$$\Delta \bar{Q}(B_3 - B_1) = 2.6842 - 2.3596 = +0.3246 \quad (\text{Supera holgadamente al baseline rápido})$$

### 7.4. Telemetría y Costo Computacional
* Latencia Total $B_2$ (`docling`): $72,905.09\text{ ms}$ (media: $3,837.11\text{ ms/pág}$, p95: $6,708.75\text{ ms}$).
* Latencia Total $B_3$ (`adaptive`): $9,632.44\text{ ms}$ (media: $506.97\text{ ms/pág}$, p95: $1,891.51\text{ ms}$).
* Latencia Total $B_1$ (`pymupdf`): $202.56\text{ ms}$ (media: $10.66\text{ ms/pág}$, p95: $17.12\text{ ms}$).
* **Costo Relativo $T(B_3) / T(B_2)$:**
  $$\text{Relative\_Cost} = \frac{9,632.44}{72,905.09} = \mathbf{13.21\%} \quad (\le 50.0\% \implies \text{Pareto Condition Satisfied})$$
* **Ahorro de Cómputo vs All-Docling:** **$86.79\%$**.

---

## 8. AUDITORÍA DEL EXIT GATE METODOLÓGICO

Conforme a la Sección 5 de `PROBE1_EXPERIMENT_PLAN.md`:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ CONDICIONES DEL EXIT GATE                                              │
├────────────────────────────────────────────────────────────────────────┤
│ 1. MISSED_ESCALATION_RATE <= 10.0% : FAIL (44.44% > 10.0%)             │
│ 2. Q(B3) >= Q(B2) - 0.15           : PASS (2.6842 >= 2.6395)           │
│ 3. Relative_Cost(B3) <= 0.50       : PASS (13.21% <= 50.0%)            │
├────────────────────────────────────────────────────────────────────────┤
│ DICTAMEN FORMAL DEL EXIT GATE      : FAIL                              │
└────────────────────────────────────────────────────────────────────────┘
```

> [!WARNING]
> **Veredicto Científico Riguroso:**  
> A pesar de que el enrutador adaptativo demostró ser altamente eficiente en la frontera de Pareto (ahorró el $86.79\%$ del tiempo de GPU manteniendo una calidad estructural promedio cercana a Docling), **reprobó formalmente el criterio de seguridad estructural** ($\text{MER} = 44.44\% > 10.0\%$, y $> 20.0\%$ umbral de fallo crítico).  
> Por tanto, el enrutador heurístico congelado **NO puede ser promovido a producción ni considerado un clasificador seguro sin un detector robusto de tablas sin bordes y diagramas vectoriales dispersos**.

---

## 9. AUDITORÍA DE INVARIANTES DE PRODUCCIÓN

Se auditó el estado inmutable de las bases de datos de TALOS:

```bash
sha256sum data/web_state/*.db
```

| Base de Datos | SHA-256 Registrado (CP148/CP150/CP151) | SHA-256 Auditado (TEST Final) | Estado |
|---|---|---|:---:|
| `cal_store.db` | `82773155ca35028274ba0f378fdcd37a5374bb4483a579654a6e9facfd443782` | `82773155ca35028274ba0f378fdcd37a5374bb4483a579654a6e9facfd443782` | **INTACTO** |
| `knowledge_store.db` | `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` | `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` | **INTACTO** |
| `quotas.db` | `09838ed16f1bbab384e6a83be651c9f8657db11c6a72caa5c32947a2cc18050d` | `09838ed16f1bbab384e6a83be651c9f8657db11c6a72caa5c32947a2cc18050d` | **INTACTO** |
| `student_state.db` | `f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` | `f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` | **INTACTO** |
| `study_engine.db` | `e3ba06536f7dbba337dee3c1c5f01b43660ce276abb54c5cee2d5defc5b970aa` | `e3ba06536f7dbba337dee3c1c5f01b43660ce276abb54c5cee2d5defc5b970aa` | **INTACTO** |
| `vector_store.db` | `d6d9f8c8eb6e5188e8e600a73cc05bd001d2e389061815d7d0df33f447a9dde4` | `d6d9f8c8eb6e5188e8e600a73cc05bd001d2e389061815d7d0df33f447a9dde4` | **INTACTO** |

```text
DATABASE_CHANGES         = 0
V1_RUNTIME_MODIFIED      = FALSE
PRODUCTION_SELECTION     = NOT_PERFORMED
LOCAL_RUN_PERMITTED      = FALSE (Ejecución en Colab GPU)
```

---

## 10. CONCLUSIONES FORMALES DE LA AUDITORÍA

1. **Validez Metodológica Absoluta:** PROBE-1 cumplió el 100% de sus compromisos epistemológicos: sellado previo, cero filtración, congelamiento de parámetros sin recalibración post-hoc y adjudicación ciega.
2. **Honestidad Científica:** El hallazgo de que el enrutador simple reprueba el Exit Gate de seguridad ($\text{MER} = 44.44\%$) valida la necesidad imperativa de haber realizado un holdout ciego en lugar de asumir la validez del router calibrado en DEV.
3. **Certificación:** La fase de ejecución y evaluación de TEST de PROBE-1 queda **AUDITADA Y APROBADA** para su reporte final.
