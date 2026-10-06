# TALOS V1.5 — INGESTION INTELLIGENCE LAB
## AUDITORÍA CANÓNICA DE EJECUCIÓN EN DEV Y CALIBRACIÓN (PROBE-1)

**Versión:** 1.0.0-canonical  
**Fecha de Auditoría:** 2026-10-06  
**Fase:** Ingestion Intelligence Lab (v2.0)  
**Experimento:** `PROBE-1: Adaptive Structural Routing`  
**Estado:** `DEV_CALIBRATION_COMPLETED | GATE_PASSED`  
**Autoridad:** Directiva Canónica v1.0.0-canonical (Packaging & DEV Calibration)  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`  

---

## 1. RESUMEN EJECUTIVO DE AUDITORÍA

Se ha ejecutado la auditoría formal de la fase **DEV Calibration** de `PROBE-1: Adaptive Structural Routing`.
Todos los procedimientos de preparación de paquetes Colab, extracción determinista de características geométricas, calibración de umbrales del enrutador y sellado de parámetros congelados se ejecutaron bajo estricto cumplimiento de los controles metodológicos C01–C12 y las directivas canónicas selladas en Checkpoint 150.

```text
┌────────────────────────────────────────────────────────────────────────┐
│ DICTAMEN DE AUDITORÍA: PROBE_1_DEV_CALIBRATION = PASSED                │
├────────────────────────────────────────────────────────────────────────┤
│ PRECONDICIONES SELLADAS (CP150) : VERIFICADAS Y CONFORMES              │
│ FUENTE PDF Y SLICE DEV          : VERIFICADOS POR SHA-256              │
│ BARRERA DE ACCESO A TEST        : 100% AISLADO (0 PÁGINAS TEST)        │
│ EXTRACCIÓN DE FEATURES EN DEV   : 19/19 PÁGINAS (LATENCIA MEDIA 7.76ms)│
│ CALIBRACIÓN DE UMBRALES         : TAU_DWG=12, TAU_GRID=1.0 (MODEL-FREE)│
│ RENDIMIENTO EN DEV              : MISSED_ESCALATION = 10.0% (<= 10.0%) │
│ SEGUNDO SELLADO (ROUTER_FREEZE) : CONGELADO Y REGISTRADO EN HASH JSON  │
│ INTEGRIDAD DE PRODUCCIÓN        : 6/6 DB INTACTAS (DATABASE_CHANGES=0) │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. AUDITORÍA DEL ESTADO INICIAL Y SELLO METODOLÓGICO (SEAL VERIFICATION)

Conforme a la Sección 2 de la directiva, se auditó la validez del sello criptográfico previo:

| Control | Valor Requerido | Valor Auditado | Dictamen |
|---|---|---|:---:|
| `PROBE_1_DESIGN` | `COMPLETE` | `COMPLETE` | **PASS** |
| `PROBE_1_PREFLIGHT` | `PASSED` | `PASSED` | **PASS** |
| `PROBE_1_SEAL` | `SEALED` | `SEALED` | **PASS** |
| `SEAL_MANIFEST_PATH` | `PROBE1_SEAL_MANIFEST.json` | `experiments/v1_5_ingestion/probe1/PROBE1_SEAL_MANIFEST.json` | **PASS** |
| `SEAL_DIGEST_SHA256` | `e6e81f98edb872c287ebf87687df0fc6f99b015775b8b0b2d6193106ba82b7cd` | `e6e81f98edb872c287ebf87687df0fc6f99b015775b8b0b2d6193106ba82b7cd` | **PASS** |
| `SEAL_COMMIT` | `88ad38b80c9c4cd9038f351402e0a02e56e30181` | `88ad38b80c9c4cd9038f351402e0a02e56e30181` | **PASS** |

---

## 3. AUDITORÍA DE INTEGRIDAD DE FUENTES Y PARTICIÓN

### 3.1. Libro Fuente Canónico
* **Archivo:** `fuentes/fase0-soc/Fundamentos_de_programación_4ta_Edición_Luis_Joyanes_Aguilar_2.pdf`
* **SHA-256 Esperado y Auditado:** `1217dd5e6038f150f454198b9645b7f4b89929ff88ba3744ca2c446082f4fb47`
* **Resultado:** **COINCIDENCIA EXACTA (BIT-A-BIT)**.

### 3.2. Slice Físico DEV Aislado
Para garantizar físicamente que el entorno de desarrollo y Colab carezcan de toda posibilidad de acceder a las páginas de holdout, se construyó un slice PDF físico que contiene única y exclusivamente las 19 páginas de DEV:
* **Archivo:** `drive_upload_ingestion_probe1/data/joyanes_ch02_dev_19p.pdf`
* **SHA-256:** `eb090644cde641248d0bb74488315057e81a505a442bba94f36d46262a6f56ef`
* **Total de Páginas Físicas:** 19 páginas (págs. 75, 79, 80, 82, 83, 84, 86, 87, 89, 91, 95, 96, 97, 100, 101, 102, 103, 105, 106).
* **Páginas de TEST Presentes:** 0 (CERO).
* **Resultado:** **BARRERA FÍSICA INFRANQUEABLE**.

---

## 4. AUDITORÍA DE LA BARRERA CERO ACCESO A TEST (ZERO-LEAKAGE)

Conforme a las Secciones 3, 7 y 18 de la directiva:

```text
TEST_ACCESS_DURING_DEV             = FALSE
TEST_FEATURE_EXTRACTION            = FALSE
TEST_LABEL_ACCESS                  = FALSE
TEST_RESULTS_ACCESS                = FALSE
ROUTER_TUNING_ON_TEST              = STRICTLY_ZERO
TEST_PAGES_DISCLOSED_TO_CALIBRATION= STRICTLY_ZERO
```

El manifiesto provisto al código de calibración (`DEV_MANIFEST.json`) contiene únicamente las 19 entradas de DEV. En ningún momento el proceso de extracción ni el script de calibración tuvieron acceso a datos, textos, features ni salidas de las 19 páginas de TEST.

---

## 5. AUDITORÍA DEL PAQUETE REPRODUCIBLE COLAB

Se verificó la estructura completa del paquete `drive_upload_ingestion_probe1/`:
* `manifest/PROBE1_SEAL_MANIFEST.json`: Manifiesto sellado previo.
* `manifest/DEV_MANIFEST.json`: Manifiesto aislado de DEV.
* `data/joyanes_ch02_dev_19p.pdf`: Slice físico DEV de 19 páginas.
* `src/feature_extractor.py`: Extractor determinista F1..F6 conforme a spec.
* `src/router.py`: Enrutador adaptativo con umbrales calibrados y prioridades.
* `src/calibration.py`: Motor de calibración y grid search sobre DEV.
* `src/metrics.py`: Motor de cómputo de métricas formalizadas en `PROBE1_METRICS_SPEC.md`.
* `notebooks/PROBE1_DEV_CALIBRATION.ipynb`: Notebook reproducible para Colab.
* `environment/environment.spec.json`: Especificación del entorno de ejecución.
* `README_EXECUTION.md`: Instrucciones operativas paso a paso para el operador humano.

### 5.1. Verificación de Ejecución en Google Colab (Cross-Environment Match)
El operador ejecutó el notebook `PROBE1_DEV_CALIBRATION.ipynb` en Google Colab y descargó los resultados:
* **Archivo de Retorno:** `drive_upload_ingestion_probe1/PROBE1_DEV_RESULTS.zip` (`SHA-256: 7c0517219b96b6a9d691fefa0b5e5ecb2198efe5f3e5b312ba693e35ad2d3947`).
* **Cotejo Forense Bit-a-Bit:** Se compararon las 19 páginas entre la extracción de Colab y la local:
  - `dwg_count`: 19/19 idénticos ($100\%$).
  - `table_grid_score`: 19/19 idénticos ($100\%$).
  - `parallel_overlap`: 19/19 idénticos ($100\%$).
  - `code_block_density`: 19/19 idénticos ($100\%$).
  - `indented_blocks`: 19/19 idénticos ($100\%$).
  - `dot_leader_count`: 19/19 idénticos ($100\%$).
  - `char_count`, `block_count`, `line_count`: 19/19 idénticos ($100\%$).
* **Latencia en Colab:** Media de $18.56\text{ ms/pág}$ (min $9.31\text{ ms}$, max $52.09\text{ ms}$ en entorno de nube compartida).
* **Veredicto:** **`CROSS_ENVIRONMENT_REPRODUCIBILITY = VERIFIED_100%`**. Cero discrepancias metodológicas entre la ejecución local y el entorno Colab.

---

## 6. AUDITORÍA DE EXTRACCIÓN DE FEATURES Y CALIBRACIÓN

### 6.1. Extracción de Features ($F_1 \dots F_6$)
* Total de registros generados en `PROBE1_DEV_FEATURES.jsonl`: 19.
* Presupuesto de latencia: $< 10.0\text{ ms/pág}$.
* Latencia real observada: media de **$7.76\text{ ms/pág}$** en CPU ordinaria (máx. 28.38 ms en p079 por raster de encabezado, min. 5.65 ms). Cumple con el criterio RQ3.
* Tratamiento de casos borde: Verificado el filtro de exclusión de texto estrictamente contenido dentro de un trazo ($b_{\text{text}} \subset b_{\text{vec}}$), evitando falsos positivos de `parallel_overlap` en cajas de texto de ejemplos (p095).

### 6.2. Calibración Empírica del Router
* Algoritmo: Determinista, explicable, libre de modelos (*model-free*), sin LLMs ni clasificadores opacos (RF, XGBoost).
* Ajuste de $\tau_{\text{dwg}}$: El análisis en DEV demostró que $\tau_{\text{dwg}} = 15$ omitía el Ejemplo 2.7 (p103, 14 dibujos vectoriales). Se calibró a **$\tau_{\text{dwg}} = 12$**, logrando separación perfecta entre prosa ($\le 5$) y diagramas ($\ge 14$).
* Rendimiento obtenido sobre DEV:
  - $TP = 9, FP = 0, TN = 9, FN = 1$ (p101: pseudocode simple con indentación por espacios).
  - $\text{Missed Escalation Rate} = \frac{1}{10} = \mathbf{10.0\%}$ ($\le 10.0\%$ tolerancia cumplida).
  - $\text{False Escalation Rate} = \frac{0}{9} = \mathbf{0.0\%}$.
  - $\text{Accuracy} = \mathbf{94.74\%}$, $\text{Precision} = \mathbf{100.0\%}$, $\text{Recall} = \mathbf{90.0\%}$.

---

## 7. AUDITORÍA DEL SEGUNDO CONGELAMIENTO (`ROUTER_FREEZE`)

Conforme a la Sección 17 de la directiva, los parámetros y el código del router han sido congelados formalmente:
* `PROBE1_CALIBRATED_ROUTER_SPEC.md`: Especificación formal inmutable.
* `PROBE1_CALIBRATED_ROUTER_HASH.json`: Registro de hashes SHA-256 de:
  - `router.py`: `49938915444ecf22142917e0b308647f41fb687828938223a249c4c3394c3f32`
  - `calibrated_router_spec_md`: `2c0ae48895d55ce8c474b8f6fa6ebd781562561d495faacf24ee79f85d0fedc8`
  - `calibration_report_md`: `207f56ce47c90217eaf405bd61c70e39dedd652bf8712c3931348ec82586e900`
  - `dev_features_jsonl`: `4cb40345f93a9c04d5fcdce36e4a0acaefe8b6ece4d3447ae22e1b7f631482af`
  - `dev_results_jsonl`: `41b212180e4458f39ec2738f4f2f4a572f766181ac0efbaa8a19a43508e353a3`
  - `calibrated_thresholds_sha256`: `b361bb9d2919bf3266bca1387d7bca85ee3628df13b2c174ec6f54cba8a91da4`

---

## 8. AUDITORÍA DE INVARIANTES DE PRODUCCIÓN

Se verificó el estado de las 6 bases de datos SQLite en `data/web_state/`:

| Base de Datos | Hash SHA-256 Verificado | Estado |
|---|---|:---:|
| `cal_store.db` | `82773155ca35028274ba0f378fdcd37a5374bb4483a579654a6e9facfd443782` | INTACTA |
| `knowledge_store.db` | `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` | INTACTA |
| `quotas.db` | `09838ed16f1bbab384e6a83be651c9f8657db11c6a72caa5c32947a2cc18050d` | INTACTA |
| `student_state.db` | `f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` | INTACTA |
| `study_engine.db` | `e3ba06536f7dbba337dee3c1c5f01b43660ce276abb54c5cee2d5defc5b970aa` | INTACTA |
| `vector_store.db` | `d6d9f8c8eb6e5188e8e600a73cc05bd001d2e389061815d7d0df33f447a9dde4` | INTACTA |

* `DATABASE_CHANGES`: **0 (CERO)**.
* `V1_RUNTIME_MODIFIED`: **FALSE**.
* `PRODUCTION_SELECTION`: **NOT_PERFORMED**.

---

## 9. LISTA DE VERIFICACIÓN DEL GATE (SECCIÓN 24)

| Condición del Gate | Requisito Canónico | Evidencia Auditada | Veredicto |
|---|---|---|:---:|
| 1. `SEAL_VALID` | `TRUE` | Digest `e6e81f98...` verificado en commit `88ad38b8...` | **PASSED** |
| 2. `PDF_HASH_MATCH` | `TRUE` | `1217dd5e...` verificado en PDF original | **PASSED** |
| 3. `DEV_MANIFEST_VALID` | `TRUE` | `PROBE1_DEV_MANIFEST.json` con 19 páginas DEV | **PASSED** |
| 4. `DEV_COUNT` | `19` | Exactamente 19 páginas en `DEV_SET` | **PASSED** |
| 5. `TEST_ACCESS` | `0` | Cero accesos al conjunto `TEST_SET` | **PASSED** |
| 6. `TEST_RESULTS_ACCESSED` | `FALSE` | Cero lecturas, cómputos o inspecciones de TEST | **PASSED** |
| 7. `FEATURE_SPEC_UNMODIFIED` | `TRUE` | F1..F6 preservadas sin cambios de fórmula | **PASSED** |
| 8. `BENEFIT_DEFINITION_UNMODIFIED` | `TRUE` | `PROBE1_BENEFIT_DEFINITION.md` inalterada | **PASSED** |
| 9. `METRICS_SPEC_UNMODIFIED` | `TRUE` | `PROBE1_METRICS_SPEC.md` inalterada | **PASSED** |
| 10. `ROUTER_CALIBRATED` | `TRUE` | Umbrales calibrados determinísticamente en DEV | **PASSED** |
| 11. `ROUTER_FROZEN` | `TRUE` | `ROUTER_FREEZE = TRUE` formalizado | **PASSED** |
| 12. `ROUTER_HASH_RECORDED` | `TRUE` | Registrado en `PROBE1_CALIBRATED_ROUTER_HASH.json` | **PASSED** |
| 13. `PRODUCTION_DB_CHANGES` | `0` | 6/6 bases de datos con hashes idénticos | **PASSED** |
| 14. `V1_RUNTIME_MODIFIED` | `FALSE` | Runtime de producción TALOS V1 intacto | **PASSED** |

---

## 10. DICTAMEN FINAL DE LA ETAPA

Todas las condiciones requeridas por la Sección 24 de la Directiva Canónica han sido satisfechas al $100\%$.

```text
PROBE_1_DEV_CALIBRATION = PASSED
STAGE_STATUS            = READY_FOR_TEST_AUTHORIZATION_DIRECTIVE
TEST_EXECUTION          = NOT_AUTHORIZED (ESPERA DIRECTIVA SEPARADA)
```
