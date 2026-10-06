# CHECKPOINT 128 — DISEÑO DEL EXPERIMENTO DE SELECCIÓN: PDF → CORPUS (FASE 1A.2)

**Fecha:** 2026-10-05  
**Fase:** TALOS V1.5 — Fase 1A.2 (Diseño Experimental de Selección PDF → Corpus)  
**Estado:** `PHASE_1A2_DESIGN = COMPLETE`  
**Subdominio:** Corpus Intelligence / Diseño Experimental / Evaluación de Evidencia  
**Autoridad:** Directiva Operativa TALOS V1.5 — Fase 1A.2 / Antigravity Agent  
**Referencia Documental:**
- `reports/v1_5_phase1/PHASE_1A2_EXPERIMENT_DESIGN.md`
- `reports/v1_5_phase1/PHASE_1A2_DATASET_SPEC.md`
- `reports/v1_5_phase1/PHASE_1A2_BENCHMARK_SPEC.md`
- `reports/v1_5_phase1/PHASE_1A2_CANDIDATE_MATRIX.md`
- `reports/v1_5_phase1/PHASE_1A2_METRICS_SPEC.md`
- `reports/v1_5_phase1/PHASE_1A2_COLAB_EXECUTION_SPEC.md`
- `reports/v1_5_phase1/PHASE_1A2_INTEGRITY_PROTOCOL.md`
- `experiments/v1_5_phase1a2/configs/input_manifest.json`
- `experiments/v1_5_phase1a2/configs/pipeline_configs.json`
- `experiments/v1_5_phase1a2/colab/phase1a2_colab_runner.py`

---

## 1. RESUMEN EJECUTIVO

La **Fase 1A.2** ha completado formalmente el diseño de ingeniería del experimento de selección comparativa para el pipeline de ingesta y construcción del corpus de TALOS (**PDF $\rightarrow$ Corpus $\rightarrow$ Evidence**) bajo una arquitectura estrictamente **Colab-First**.

Este diseño sustituye cualquier intuición técnica, preferencia por modelos populares o adopción precipitada de bibliotecas por un marco metodológico estricto basado en:
1. **Restricción Fundamental de Procesamiento:** `PDF_PROCESSING_LOCAL = FORBIDDEN` y `PDF_PROCESSING_COLAB = REQUIRED`. La PC local no ejecuta ingesta pesada sobre PDFs; Colab asume el procesamiento de la materia prima y la PC analiza la evidencia.
2. **Control V1 Inmutable (`CONTROL A`):** Definición canónica y reproducible del baseline histórico (`pypdf` + chunking léxico ~500c + Qwen3-Embedding-0.6B 1024d).
3. **Desacoplamiento de Variables:** Separación en seis ejes ortogonales (Extracción, Representación estructural, Limpieza, Chunking, Provenance, Embeddings).
4. **Diseño Factorial Reducido y Secuencial en 2 Etapas:**
   - *Etapa 1:* Filtro de higiene estructural y control absoluto de outliers (`NO_UNBOUNDED_CHUNK_SIZE = REQUIRED`).
   - *Etapa 2:* Benchmark de recuperación densa frente a 40 consultas canónicas y adjudicación humana independiente ($N=1$).
5. **Corpus Experimental Estratificado (`talos-1a2-exp-corpus-v1`):** Muestra representativa de 120 páginas procedentes de Joyanes Aguilar y Tanenbaum, estresando 11 fenómenos documentales críticos, incluyendo el outlier masivo de 47k caracteres de la p. 15 de Joyanes (`PROB-1A-03`).
6. **Evaluación Humana Rigurosa:** Protocolo de adjudicación ciega derivado de CP120-R3, con enmascaramiento criptográfico, prohibición de árbitros LLM para juicio principal y rúbricas categóricas de Relevancia, Suficiencia y Grounding.

---

## 2. INVENTARIO DE ENTREGABLES FORMALIZADOS

Bajo el directorio `reports/v1_5_phase1/` y `experiments/v1_5_phase1a2/` se han publicado los artefactos canónicos de especificación y orquestación:

1. **`PHASE_1A2_EXPERIMENT_DESIGN.md`:** Arquitectura metodológica, formulación de la pregunta experimental $\mathcal{Q}_{1A.2}$, definición del control e hipótesis globales.
2. **`PHASE_1A2_DATASET_SPEC.md`:** Especificación del corpus experimental balanceado de 120 páginas, cortes exactos (slices) y taxonomía de fenómenos (`PHEN-01` a `PHEN-11`).
3. **`PHASE_1A2_BENCHMARK_SPEC.md`:** Banco canónico de 40 consultas tipificadas en 12 arquetipos, rúbricas de adjudicación y casos de estrés de outliers.
4. **`PHASE_1A2_CANDIDATE_MATRIX.md`:** Espacio de búsqueda de 9 pipelines acotados (`PIPE-CTRL-A`, `PIPE-01` a `PIPE-08`), combinando extractores (`pypdf`, `PyMuPDF`, `Docling`), chunkings (léxico, AST, párrafos, jerárquico) y embeddings (`Qwen3`, `BGE-M3`, `E5-small`).
5. **`PHASE_1A2_METRICS_SPEC.md`:** Desglose en 3 planos (Estructural, Retrieval y Coste), protocolo de adjudicación ciega con $N=1$ y taxonomía de reproducibilidad.
6. **`PHASE_1A2_COLAB_EXECUTION_SPEC.md`:** Topología Colab-First, manifiesto de entrada, ciclo de vida del runner, gestión de embeddings pesados y límites operacionales.
7. **`PHASE_1A2_INTEGRITY_PROTOCOL.md`:** Protocolo de aislamiento físico, prohibición de escrituras en producción, barrera antitransición y verificación criptográfica.
8. **`experiments/v1_5_phase1a2/`:** Manifiestos de entrada (`input_manifest.json`), configuración de pipelines (`pipeline_configs.json`) y script runner para Google Colab (`phase1a2_colab_runner.py`).

---

## 3. ESTADO FORENSE Y VERIFICACIÓN DE INMUTABILIDAD

Se certifica que durante el desarrollo de esta especificación de diseño no se ha producido mutación física ni lógica en los entornos de producción:

### Hashes SHA-256 de Almacenamiento Canónico en `data/web_state/`
- `knowledge_store.db` (303.194.112 B): `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` — **INTACTO**
- `knowledge_store.db-wal` (0 B): `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` — **INTACTO**
- `knowledge_store.db-shm` (32.768 B): `fd4c9fda9cd3f9ae7c962b0ddf37232294d55580e1aa165aa06129b8549389eb` — **INTACTO**
- `vector_store.db` (1.369.837.568 B): `d6d9f8c8eb6e5188e8e600a73cc05bd001d2e389061815d7d0df33f447a9dde4` — **INTACTO**
- `vector_store.db-wal` (0 B): `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` — **INTACTO**
- `vector_store.db-shm` (32.768 B): `fd4c9fda9cd3f9ae7c962b0ddf37232294d55580e1aa165aa06129b8549389eb` — **INTACTO**
- `student_state.db` (172.032 B): `f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` — **INTACTO**
- `student_state.db-wal` (0 B): `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` — **INTACTO**
- `student_state.db-shm` (32.768 B): `fd4c9fda9cd3f9ae7c962b0ddf37232294d55580e1aa165aa06129b8549389eb` — **INTACTO**

### Runtime V1 (`src/`)
- Diferencias git en `src/`: **0 archivos modificados** (`V1_RUNTIME_MODIFIED = FALSE`).

---

## 4. DICTAMEN DE GOBERNANZA FORMAL

```text
PHASE_1A2_SPEC_CORRECTION = COMPLETE

VARIABLE_ISOLATION_MODEL = CORRECTED
BENCHMARK_STATUS = EXPLICITLY_CLASSIFIED
METRIC_GATES = PROVISIONAL_OR_EVIDENCE_BACKED
HUMAN_ADJUDICATION = METHODOLOGICALLY_BOUNDED
EMBEDDING_CONTRACT = EXPLICIT
DTYPE_CONTRACT = EXPLICIT
REPRODUCIBILITY_MODEL = EXPLICIT
COLAB_ISOLATION = EXPLICIT
FORENSIC_INTEGRITY = VERIFIED
CROSS_DOCUMENT_CONSISTENCY = PASS

EXPERIMENT_EXECUTION = NOT_STARTED
CANDIDATE_SELECTION = NOT_AUTHORIZED

PRODUCTION_STATUS = UNCHANGED
DATABASE_CHANGES = 0
CORPUS_CHANGES = 0
VECTOR_STORE_CHANGES = 0
STUDENT_STATE_CHANGES = 0
V1_RUNTIME_MODIFIED = FALSE
```

