# Checkpoint 152: Ejecución en Holdout TEST, Adjudicación Ciega y Reporte Final (PROBE-1)

**Fecha:** 2026-10-06T02:00:00-03:00  
**Fase:** INGESTION INTELLIGENCE LAB (v2.0) — PROBE-1  
**Tipo de Documento:** CHECKPOINT CANÓNICO DE EJECUCIÓN TEST, AUDITORÍA Y CONCLUSIÓN DE EXPERIMENTO  
**Autoridad:** Directiva Canónica de Ejecución de TEST (v1.0) / Antigravity Agent  
**Predecesores Canónicos Directos:**
* Checkpoint 151 (`checkpoints/151-probe-1-dev-calibration.md`, Router Hash: `8753a32db341a6488aa58cb48de40712e7cacb963d6ef1dd2e78df31d70e71fe`)
* Checkpoint 150 (`checkpoints/150-probe-1-sello-criptografico.md`, Seal Digest: `e6e81f98edb872c287ebf87687df0fc6f99b015775b8b0b2d6193106ba82b7cd`)
* Checkpoint 149 (`checkpoints/149-probe-1-diseno-routing-adaptativo.md`)
* Checkpoint 148 (`checkpoints/148-probe-0-ejecucion-y-auditoria-ingestion-lab.md`)  
**Estatus Canónico:** **`PROBE_1_TEST_EXECUTION = COMPLETED | BLIND_ADJUDICATION = FINISHED | EXIT_GATE = FAIL | PROBE_1 = CONCLUDED | PRODUCTION_PROMOTION = PROHIBITED`**  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`  

---

## 1. ESTADO DE GOBERNANZA Y EXIT GATE

```text
==================================================================================================
TALOS V1.5 — CHECKPOINT 152: PROBE-1 TEST EXECUTION & EXPERIMENT CONCLUSION
==================================================================================================

EXPERIMENT_ID                   = exp_ingestion_probe0_v2 / PROBE-1
EXPERIMENT_VERSION              = 1.0.0-canonical
STAGE                           = TEST_EXECUTION_AND_FINAL_REPORT
ROUTER_FROZEN_HASH              = 8753a32db341a6488aa58cb48de40712e7cacb963d6ef1dd2e78df31d70e71fe
RECALIBRATION_PERMITTED         = STRICTLY_FALSE (Cero recalibración en holdout)

TEST_SET_SIZE                   = 19 páginas físicas (Capítulo 2 Joyanes)
TEST_SET_SHA256                 = 69d607feec38c4c34d52a6e10666a4c0520ebfe8846cc859f234e9b750ff2baf
EXECUTION_ENVIRONMENT           = Google Colab, GPU Tesla T4 (CUDA 12.x, PyTorch)
BLIND_ADJUDICATION_PROFILE      = N=1 especialista humano independiente (Control C01)

CONFUSION_MATRIX (19 páginas):
  - True Positives (TP)         = 5 (p093, p104, p107, p108, p109)
  - False Positives (FP)        = 1 (p112: lista indentada de ejercicios)
  - True Negatives (TN)         = 9 (p076, p077, p081, p088, p090, p094, p098, p099, p111)
  - False Negatives (FN)        = 4 (p078: tabla sin bordes, p085: variables, p092: UML, p110: N-S)

CLASSIFICATION_METRICS:
  - Missed Escalation Rate (MER)= 44.44% (TOLERANCIA <= 10.0%, LÍMITE FALLO > 20.0% -> REPROBADO)
  - False Escalation Rate (FER) = 10.00%
  - Accuracy                    = 73.68%
  - Precision                   = 83.33%
  - Recall                      = 55.56%

STRUCTURAL_QUALITY (Q in [0, 3]):
  - Q(B0 = pypdf)               = 2.3421
  - Q(B1 = pymupdf)             = 2.3596
  - Q(B2 = docling)             = 2.7895
  - Q(B3 = adaptive)            = 2.6842 (Delta vs B2: -0.1053, supera target >= -0.15)

COMPUTATIONAL_TELEMETRY:
  - Total Latency B2 (Docling)  = 72,905.09 ms (media: 3,837.11 ms, p95: 6,708.75 ms)
  - Total Latency B3 (Adaptive) = 9,632.44 ms (media: 506.97 ms, p95: 1,891.51 ms)
  - Relative Cost T(B3) / T(B2) = 13.21% (Ahorro de cómputo: 86.79% vs All-Docling)

PARETO_FRONTIER_ANALYSIS:
  - Condición de Calidad        = SATISFECHA (2.6842 >= 2.6395)
  - Condición de Costo          = SATISFECHA (13.21% <= 50.0%)
  - Pareto-Eficiente            = TRUE

EXIT_GATE_VERDICT               = FAIL (Rechazado por violación crítica de seguridad MER)
PRODUCTION_PROMOTION            = RECHAZADA (No promover a runtime V1)
PRODUCTION_ISOLATION            = 100% INTACTO (DATABASE_CHANGES = 0, 6/6 DBs inmutables)
==================================================================================================
```

---

## 2. ARTEFACTOS GENERADOS Y SELLADOS EN ESTA ETAPA

```text
==================================================================================================
ARTEFACTO GENERADO                                                      HASH SHA-256
==================================================================================================
[01] drive_upload_ingestion_probe1_test/data/joyanes_ch02_test_19p.pdf  69d607feec38c4c34d52a6e10666a4c0520ebfe8846cc859f234e9b750ff2baf
[02] experiments/v1_5_ingestion/probe1/PROBE1_TEST_MANIFEST.json        e272b5c8c494a7889f10b4c93acb50292dee81839ea22cdd531f71af93681265
[03] experiments/v1_5_ingestion/probe1/PROBE1_TEST_IMPLEMENTATION_PREFLIGHT.md 7d294e0f47973fed8a8a04e567a721ace2e65c95f202e121a07416dbf8ae823d
[04] drive_upload_ingestion_probe1_test/PROBE1_TEST_RESULTS.zip         3c4e766c46f813963ebc3e2d11313e0c71a04c4c318b5bc1ecf5c9e2cdfa537f
[05] experiments/v1_5_ingestion/probe1/PROBE1_TEST_FEATURES.jsonl       a3c6a35131e0f5a3945b1a8f0aefd448ab7b9fd565db90b1d7aa63c783615943
[06] experiments/v1_5_ingestion/probe1/PROBE1_TEST_ROUTER_RESULTS.jsonl 4f939122c52a3682c3e19a6bfed0a84e3fcaa5cd6e975b373c19624f504640fb
[07] experiments/v1_5_ingestion/probe1/PROBE1_TEST_BASELINE_RESULTS.jsonl 833400088689bb1146fdb0fd1859640b11ebb2ba8ccffbfa7de4b9b9cff94907
[08] experiments/v1_5_ingestion/probe1/PROBE1_TEST_ADJUDICATION.jsonl   338f14a196d6c9e581e556d835f143457ea4a6dbcaf77b6caaa23994a7bd3557
[09] experiments/v1_5_ingestion/probe1/PROBE1_TEST_METRICS.json        5260a10e2e965e877e23ced7771a00e360a9964b5d8fbb40de122e4f2cadc0c7
[10] experiments/v1_5_ingestion/probe1/PROBE1_TEST_EXECUTION_AUDIT.md   00eeb8b3ab650bccfccb2d54f2d97a9dbdf42c99f42ebd851666929982e4bb56
[11] experiments/v1_5_ingestion/probe1/PROBE1_TEST_FINAL_REPORT.md      19e6b2f16c7886bbdff3bb75e3a667b5b26c12d77afbbeafaa15410c91df8e37
[12] experiments/v1_5_ingestion/probe1/PROBE1_TEST_SEAL_MANIFEST.json   aae910b697c8a4e3fbead40cb0461b39e36b2701c19e2b8c91be11d954a61804
==================================================================================================
OVERALL TEST SEAL DIGEST: aae910b697c8a4e3fbead40cb0461b39e36b2701c19e2b8c91be11d954a61804
==================================================================================================
```

---

## 3. AUDITORÍA FORENSE DE INMUTABILIDAD DE PRODUCCIÓN

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
TOTAL BASE DE DATOS MODIFICADAS: 0 / 6 (INMUTABILIDAD ESTRICTA PRESERVADA)
```

---

## 4. HALLAZGOS Y CONCLUSIONES CLAVE

1. **Eficiencia de Pareto Verificada:** El enrutamiento adaptativo es viable y drásticamente más económico que All-Docling (reducción del $86.79\%$ en cómputo con calidad media indistinguible del extractor pesado).
2. **Puntos Ciegos Heurísticos:** El conteo de vectores y líneas ortogonales es ciego a tablas sin bordes (`p078`) y diagramas con trazos escasos (`p085, p092, p110`).
3. **Fallas Críticas de Docling v2:** Docling no puede ser adoptado como verdad universal debido a su tendencia a colapsar código indentado en un solo párrafo (`p081, p099`) y desfragmentar el orden de lectura (`p111`).
4. **Victoria Metodológica del Sellado:** El experimento prueba el valor incalculable de no alterar los umbrales en holdout.
5. **Transición:** El diseño de PROBE-1 queda formalmente cerrado y archivado. Las recomendaciones para PROBE-2 quedan registradas en el reporte final.
