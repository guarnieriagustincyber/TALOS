# CP118 — Benchmark Canónico del Corpus Actual y Evaluación Comparativa de Retrieval

**Tipo:** Creación de Benchmark Canónico + Matriz QRELs de Propietario + Evaluación Comparativa de Retrieval + Adjudicación Formal  
**Subdominio:** Corpus Intelligence / Benchmark Fixtures  
**Precondición:** CP117 = PASS (Resolución de Compatibilidad de IDs)  
**Integridad de Datos:** `DATABASE_CHANGES = 0`  
- `BASELINE_KNOWLEDGE_DB_SHA256 = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (`data/web_state/knowledge_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_VECTOR_DB_SHA256    = 013a2462e6de6ca7cf13443338e44b7795dce4b2f7f6117827bd2ccadd0c568f` (`data/web_state/vector_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_STUDENT_DB_SHA256   = f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` (`data/web_state/student_state.db` READ-ONLY / UNCHANGED)  
- `BASELINE_DATE                = 2026-10-03T19:45:00-03:00`  

**Estado Canónico Registrado:**
```text
CP118 = PASS

CANONICAL_BENCHMARK = BUILT_AND_EXECUTED
CORPUS_PROVENANCE = 100%_ANCHORED_TO_CURRENT_PILOT
TAXONOMIC_SEPARATION = ENFORCED (HIT != RELEVANCE != SUFFICIENCY != GROUNDING)
CANDIDATE_COMPARISON = COMPLETED (BASELINE, B, C, D)
DESCRIPTIVE_RETRIEVAL_METRICS = AVAILABLE

OUTLIER_OBSERVED_IMPACT = ZERO_IN_TOP_K
OUTLIER_HANDLING = DIAGNOSTIC_ONLY
OUTLIER_RESOLUTION = DEFERRED

CANDIDATE_SELECTION = NOT_AUTHORIZED
HUMAN_ACCEPTANCE = PENDING
PRODUCTION_IMPORT = FORBIDDEN
PRODUCTION_STATUS = UNCHANGED
```

---

## 0. Resumen Ejecutivo

CP118 resolvió la pregunta funcional central del Corpus Intelligence Lab:
> **¿La nueva representación estructural del corpus mejora realmente la capacidad de recuperación de evidencia de TALOS frente a la representación productiva actual?**

1. **Benchmark Canónico y Fixture Oficial:**  
   Se construyó `data/benchmark/cp118_current_corpus_oracle.json` con **14 consultas canónicas** y **467 instancias de QRELs adjudicadas** ancladas bit-a-bit en los 3 documentos físicos del piloto actual (Joyanes 802p, Stallings 820p, prog_punteros 1p). Se desestimó formalmente el reuso de oráculos históricos no trazables.

2. **Separación Taxonómica Estricta:**  
   Se aplicó la taxonomía de 5 niveles (`Query → Retrieval Hit → Relevant Evidence → Sufficient Evidence → Grounded Response`). Se confirmó que la similitud coseno es una métrica puramente descriptiva (`DESCRIPTIVE_RETRIEVAL_METRICS`), no representativa de relevancia real ni de suficiencia fáctica.

3. **Resultados Comparativos Clave:**  
   - **`baseline` (Micro-chunks pypdf ~430 chars):** Lidera en precisión Top-1 (`Hit@1 = 64.3%`, `Relevant@1 = 57.1%`) debido a la alta densidad léxica de fragmentos pequeños para definiciones puntuales.
   - **`strategy_c` (Docling ~1.796 chars):** Lidera en completitud de respuesta (`Sufficient@5 = 42.9%`), superando al baseline (35.7%) al mantener secciones y párrafos enteros sin fragmentación.
   - **`strategy_b` (Docling ~1.012 chars):** Obtiene el mayor promedio de similitud coseno (0.6766), pero sufre en Hit@1 (42.9%).
   - **`strategy_d` (Docling ~2.489 chars):** Resuelve la unificación documental de archivos cortos (punteros), pero sufre dilución en libros extensos por rebasar los 512 tokens del modelo Qwen3.

4. **Outlier de 47.627 caracteres:**  
   Tuvo **cero apariciones** en el Top-5 de todas las consultas evaluadas (`OUTLIER_IMPACT = ZERO_IN_TOP_K`). Su tratamiento permanece como puramente diagnóstico (`OUTLIER_RESOLUTION = DEFERRED`).

5. **Gobernanza y Bloqueo:**  
   `CANDIDATE_SELECTION = NOT_AUTHORIZED` y `PRODUCTION_IMPORT = FORBIDDEN`. Producción permanece 100% inalterada con hashes bit-a-bit intactos.

---

## 1. Artefactos Entregados

1. [`data/benchmark/cp118_current_corpus_oracle.json`](file:///media/agustin/Laboratorio/study-engie/data/benchmark/cp118_current_corpus_oracle.json) — Oráculo canónico con 14 consultas y QRELs del corpus actual.
2. [`reports/corpus_intelligence_lab/CP118_CURRENT_CORPUS_BENCHMARK.md`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP118_CURRENT_CORPUS_BENCHMARK.md) — Informe oficial del benchmark canónico y diseño metodológico.
3. [`reports/corpus_intelligence_lab/CP118_CURRENT_CORPUS_QRELS.md`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP118_CURRENT_CORPUS_QRELS.md) — Catálogo canónico de QRELs con textos ancla y justificaciones.
4. [`reports/corpus_intelligence_lab/CP118_COMPARATIVE_RETRIEVAL.md`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP118_COMPARATIVE_RETRIEVAL.md) — Análisis comparativo de retrieval sobre los cuatro candidatos.
5. [`reports/corpus_intelligence_lab/CP118_ADJUDICATION.md`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP118_ADJUDICATION.md) — Registro formal de adjudicación humana y evidencia fáctica.
6. [`checkpoints/118-current-corpus-benchmark.md`](file:///media/agustin/Laboratorio/study-engie/checkpoints/118-current-corpus-benchmark.md) — Checkpoint normativo de gobernanza CP118.
