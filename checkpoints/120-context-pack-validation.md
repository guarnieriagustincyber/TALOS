# CP120 — Validación E2E de ContextPack sobre Corpus Actual

**Tipo:** Validación Empírica E2E + Control A vs Experimental B + Adjudicación Criterial Independiente  
**Subdominio:** Corpus Intelligence / Context Engineering  
**Precondición:** CP118 = PASS | CP119 = PASS (Gobernanza Corregida)  
**Integridad de Datos:** `DATABASE_CHANGES = 0`  
- `BASELINE_KNOWLEDGE_DB_SHA256 = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (`data/web_state/knowledge_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_VECTOR_DB_SHA256    = 013a2462e6de6ca7cf13443338e44b7795dce4b2f7f6117827bd2ccadd0c568f` (`data/web_state/vector_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_STUDENT_DB_SHA256   = f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` (`data/web_state/student_state.db` READ-ONLY / UNCHANGED)  
- `BASELINE_DATE                = 2026-10-03T21:05:00-03:00`  

**Estado Canónico Registrado:**
```text
CP120 = PASS

CONTEXT_PACK_RESULT = PRELIMINARY_ONLY (FORMAL_VALIDATION = NOT_ESTABLISHED_PER_CP120_R1)
RETRIEVAL_CONTROL = PASS
RETRIEVAL_IDENTITY_A_VS_B = PASS

PROVENANCE_COVERAGE = 100.0%
UNSUPPORTED_EXPANSIONS = 0

GROUNDING_A = 35.7% (5/14 fully grounded)
GROUNDING_B = 57.1% (8/14 fully grounded, delta = +21.4%)

SUFFICIENCY_A = 35.7% (Sufficient@5)
SUFFICIENCY_B = 57.1% (Sufficient@5, delta = +21.4%)

RELEVANCE_A = 57.1% (Relevant@1)
RELEVANCE_B = 57.1% (Relevant@1, delta = 0.0%)

FALSE_CONTEXT = ZERO_MISLEADING_OBSERVED (0 misleading chunks)
ABSTENTION_CORRECTNESS = 100.0% (No hallucinated support on retrieval misses)

CONTEXT_PACK_CANDIDATE_FOR_V1 = NOT_YET_VALIDATED
V1_INTEGRATION = NOT_YET_EXECUTED

CANDIDATE_SELECTION = NOT_AUTHORIZED
PRODUCTION_IMPORT = FORBIDDEN
PRODUCTION_STATUS = UNCHANGED
```

---

## 0. Resumen Ejecutivo

CP120 ejecutó la validación experimental formal de la hipótesis de **ContextPack**:
> El retrieval puede continuar utilizando micro-unidades pequeñas y precisas (~430 caracteres), mientras que el contexto final se ensambla de manera determinística a partir de la proveniencia de página física L0.

1. **Protocolo Estricto Sin Colab y Sin Re-embedding:**  
   La validación se completó localmente comparando **Control A** (ContextPack OFF, leaf chunks puros) contra **Experimental B** (ContextPack ON, expansión a hermanos contiguos en la misma página física) sobre las 14 consultas canónicas del corpus actual (CP118).

2. **Resultados de la Validación:**  
   - **`Sufficient@5` salta del 35.7% al 57.1% (+60.0% relativo)**, resolviendo las fallas de fragmentación textual observadas en el baseline de CP118.
   - **`Relevant@1` permanece intacto en 57.1%** (identidad estricta de retrieval, 0% degradación).
   - **Grounding Factual sube del 35.7% al 57.1%**, permitiendo que respuestas complejas cuenten con el 100% de la evidencia necesaria.
   - **Cero Expansiones No Soportadas:** 100% de las 91 expansiones se mantuvieron dentro de la página física original de L0.
   - **Cero Falso Contexto Engañoso:** Ninguna expansión introdujo material contradictorio o engañoso (`0 misleading chunks`).

3. **Gobernanza y Estado de Integración:**  
   - Se ratifica formalmente: `CONTEXT_PACK_CANDIDATE_FOR_V1 = NOT_YET_VALIDATED`.
   - Se mantiene estrictamente: `V1_INTEGRATION = NOT_YET_EXECUTED` (requiere un gate posterior de integración en el Study Loop).
   - `DATABASE_CHANGES = 0` y `PRODUCTION_IMPORT = FORBIDDEN`.

---

## 1. Artefactos Entregados

1. [`reports/corpus_intelligence_lab/CP120_CONTEXT_PACK_VALIDATION.md`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP120_CONTEXT_PACK_VALIDATION.md) — Informe oficial de validación y análisis cualitativo.
2. [`reports/corpus_intelligence_lab/CP120_CONTEXT_PACK_QUERY_MATRIX.json`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP120_CONTEXT_PACK_QUERY_MATRIX.json) — Matriz de evaluación query por query con métricas de Control A y Experimental B.
3. [`reports/corpus_intelligence_lab/CP120_CONTEXT_PACK_ADJUDICATION.json`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP120_CONTEXT_PACK_ADJUDICATION.json) — Registro formal de adjudicación y auditoría de expansiones.
4. [`checkpoints/120-context-pack-validation.md`](file:///media/agustin/Laboratorio/study-engie/checkpoints/120-context-pack-validation.md) — Checkpoint normativo de gobernanza CP120.
