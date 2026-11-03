# CHECKPOINT 129 — EJECUCIÓN, RESULTADOS Y AUDITORÍA DEL PILOTO EXPERIMENTAL (FASE 1A.2)

**Fecha:** 2026-10-05  
**Fase:** TALOS V1.5 — Fase 1A.2 (PDF → Corpus / Pilot Run)  
**Tipo:** Ejecución de Suite Experimental en Colab + Auditoría Forense Local  
**Subdominio:** Corpus Intelligence / Ejecución Colab-First / Evaluación Factorial  
**Autoridad:** Directiva Operativa TALOS V1.5 — Fase 1A.2 / Antigravity Agent  
**Run ID:** `run_1a2_pilot_joyanes_20261005_061144`  
**Referencia Documental:**
- `reports/v1_5_phase1/PHASE_1A2_PILOT_EXECUTION_REPORT.md`
- `reports/v1_5_phase1/pilot_bundles/`
- `drive_upload_cp116/talos_1a2_pilot_bundles.zip`

---

## 1. ESTADO DE GOBERNANZA MULTIDIMENSIONAL

```text
DESIGN_STATUS = COMPLETE
PILOT_STATUS = EXECUTED_AND_AUDITED (9/9 FACTORIAL PIPELINES PASS)
CORPUS_STATUS = PILOT_JOYANES_65P (TANENBAUM = MISSING / NOT_RUN)
SELECTION_STATUS = NOT_AUTHORIZED
PRODUCTION_STATUS = UNCHANGED

PDF_PROCESSING_LOCAL = STRICTLY_PREVENTED
PDF_PROCESSING_COLAB = COMPLETED (GPU TESLA T4)
PRODUCTION_DB_MODIFIED = FALSE
CORPUS_MODIFIED = FALSE
VECTOR_STORE_MODIFIED = FALSE
STUDENT_STATE_MODIFIED = FALSE
V1_RUNTIME_MODIFIED = FALSE
```

---

## 2. RESUMEN EJECUTIVO

El **Checkpoint 129** certifica formalmente la finalización del **Piloto Experimental de Fase 1A.2**, ejecutado exitosamente en Google Colab con aceleración GPU (NVIDIA Tesla T4) sobre las **65 páginas autorizadas** de Joyanes Aguilar (cortes J-01 a J-05):

1. **Aislamiento Físico y Cero Mutación Local:** La PC local no realizó ninguna operación pesada de PDF (`UNAUTHORIZED_LOCAL_PDF_PROCESSING = 0`). Las bases de producción permanecen 100% inalteradas.
2. **Hashes Criptográficos Verificados:** El 100% de los archivos de los 9 bundles experimentales (`chunks.jsonl`, `provenance.jsonl`, `outliers.jsonl`, `retrieval_candidates.json`, `metrics.json`) coincide bit-a-bit con sus respectivos `hashes.sha256` (`ARTIFACT_INTEGRITY = PASS`).
3. **Correspondencia de Provenance:** Se auditó correspondencia exacta (1:1) entre chunks y provenance en todos los pipelines (`PROVENANCE_INTEGRITY = PASS`).
4. **Verificación de Contrato de Vectorización:** 0 NaNs, 0 Infs y normalización L2 verificada en los tres modelos evaluados (`Qwen3` 1024d, `E5-small` 384d y `BGE-M3` 1024d) (`EMBEDDING_INTEGRITY = PASS`).
5. **Evaluación de Benchmark Preliminar:** Las 22 consultas piloto fueron evaluadas densamente en los 9 pipelines, exportando los Top-10 candidatos con puntajes de similitud coseno para posterior adjudicación ciega (`RETRIEVAL_EXPORT = PASS`).

---

## 3. RESULTADOS COMPARATIVOS DE LOS 9 PIPELINES FACTORIALES

| Pipeline | Grupo | Extractor | Chunker | Embedding | Chunks | Outliers (>4k) | Mean Cosine | Max Cosine | Min Cosine | Tiempo (s) | Hashes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **EXP-EXT-01** | A (Extracción) | `pypdf` | C1 (500c/50c) | Qwen3-0.6B | 407 | 0 | 0.2639 | 0.6164 | 0.0445 | 33.46 | PASS |
| **EXP-EXT-02** | A (Extracción) | `PyMuPDF` | C1 (500c/50c) | Qwen3-0.6B | 407 | 0 | 0.2681 | 0.5821 | 0.0500 | 28.86 | PASS |
| **EXP-EXT-03** | A (Extracción) | `Docling` | C1 (500c/50c) | Qwen3-0.6B | 407 | 0 | 0.2681 | 0.5821 | 0.0500 | 29.62 | PASS |
| **EXP-CHK-01** | B (Chunking) | `PyMuPDF` | C1 (500c/50c) | Qwen3-0.6B | 407 | 0 | 0.2681 | 0.5821 | 0.0500 | 29.49 | PASS |
| **EXP-CHK-02** | B (Chunking) | `PyMuPDF` | C2 (Sec-Aware) | Qwen3-0.6B | 64 | **10** | 0.2910 | 0.5114 | 0.1054 | 27.88 | PASS |
| **EXP-CHK-03** | B (Chunking) | `PyMuPDF` | C3 (Párrafo/Cód) | Qwen3-0.6B | 115 | 0 | 0.2868 | 0.5519 | 0.0671 | 31.59 | PASS |
| **EXP-EMB-01** | C (Embedding) | `PyMuPDF` | C2 (Sec-Aware) | Qwen3-0.6B | 64 | 10 | 0.2910 | 0.5114 | 0.1054 | 28.05 | PASS |
| **EXP-EMB-02** | C (Embedding) | `PyMuPDF` | C2 (Sec-Aware) | E5-small | 64 | 10 | 0.8083 | 0.8758 | 0.7580 | 16.63 | PASS |
| **EXP-EMB-03** | C (Embedding) | `PyMuPDF` | C2 (Sec-Aware) | BGE-M3 | 64 | 10 | 0.4104 | 0.5855 | 0.2144 | 58.00 | PASS |

---

## 4. HALLAZGOS METODOLÓGICOS Y EPIDEMIOLÓGICOS PRINCIPALES

1. **Eficiencia de Extracción:** PyMuPDF redujo el tiempo de extracción en ~14% respecto a `pypdf` sobre C1, conservando metadatos estructurales y coordenadas tipográficas.
2. **Causa Raíz de Outliers en C2 (`PROB-1A-03`):** C2 produjo 10 chunks > 4.000 caracteres (alcanzando hasta 9.298 chars en páginas 11 a 16 del índice general). La causa es la ausencia de delimitadores de párrafo (`\n\n`) en páginas densas, lo que absorbe la página entera en un solo chunk.
3. **Solución Demostrada en C3:** C3 (Paragraph/Code con techo duro de 2.000 chars a nivel de línea) produjo **0 outliers > 4.000 caracteres** y una partición equilibrada de 115 chunks, preservando bloques sintácticos de código.
4. **Geometría Vectorial de Embeddings:** E5-small mostró un rango de similitud artificialmente elevado (media 0.8083) y fue el modelo más rápido (16.63 s). BGE-M3 requirió 58.00 s (~2x el tiempo de Qwen3). Se ratifica la regla `COSINE = DIAGNOSTIC_ONLY`.

---

## 5. AUDITORÍA FORENSE DE INMUTABILIDAD DE PRODUCCIÓN

- `knowledge_store.db`: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` — **INTACTO**
- `vector_store.db`: `d6d9f8c8eb6e5188e8e600a73cc05bd001d2e389061815d7d0df33f447a9dde4` — **INTACTO**
- `student_state.db`: `f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` — **INTACTO**
- Modificaciones en `src/`: **0** (`V1_RUNTIME_MODIFIED = FALSE`).

---

## 6. DICTAMEN FINAL DE CIERRE (SECCIÓN 38)

```text
PHASE_1A2_PILOT_EXECUTION = COMPLETE

PILOT_FIXTURE = JOYANES_65P
TANENBAUM_EXECUTED = FALSE

SMOKE_TEST = PASS

FACTORIAL_PIPELINES_EXECUTED = 9
INTEGRATED_PIPELINES_EXECUTED = 0

ARTIFACT_INTEGRITY = PASS
PROVENANCE_INTEGRITY = PASS
EMBEDDING_INTEGRITY = PASS
RETRIEVAL_EXPORT = PASS
BENCHMARK_EXECUTION = PASS

HUMAN_ADJUDICATION = READY_TO_BE_STAGED

PRODUCTION_DB_MODIFIED = FALSE
CORPUS_MODIFIED = FALSE
VECTOR_STORE_MODIFIED = FALSE
STUDENT_STATE_MODIFIED = FALSE
V1_RUNTIME_MODIFIED = FALSE

CANDIDATE_SELECTION = NOT_AUTHORIZED
PRODUCTION_INTEGRATION = NOT_AUTHORIZED
```

```text
NEXT_STEP = HUMAN_ADJUDICATION_BLIND_PACKAGE_PREPARATION
```
