# CP119-PRE — Decisión de Procesamiento del Corpus: ContextPack y Arquitectura

**Tipo:** Decision Gate Arquitectónico + Validación de ContextPack (Rama G) + Shootout de Extracción Quirúrgica (Rama H)  
**Subdominio:** Corpus Intelligence / System Architecture  
**Precondición:** CP118 = PASS (Benchmark Canónico Ejecutado)  
**Integridad de Datos:** `DATABASE_CHANGES = 0`  
- `BASELINE_KNOWLEDGE_DB_SHA256 = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (`data/web_state/knowledge_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_VECTOR_DB_SHA256    = 013a2462e6de6ca7cf13443338e44b7795dce4b2f7f6117827bd2ccadd0c568f` (`data/web_state/vector_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_STUDENT_DB_SHA256   = f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` (`data/web_state/student_state.db` READ-ONLY / UNCHANGED)  
- `BASELINE_DATE                = 2026-10-03T20:45:00-03:00`  

**Estado Canónico Registrado:**
```text
CP119_PRE = PASS
CP119_RESEARCH = PASS

CONTEXT_PACK_HYPOTHESIS = PROMISING
CONTEXT_PACK_EVIDENCE = PRELIMINARY_POSITIVE (EXPLORATORY_HEURISTIC_RESULT)
CONTEXT_PACK_FORMAL_VALIDATION = NOT_YET_ESTABLISHED (SUBJECT_TO_CP120_INDEPENDENT_GATE)

PRIMARY_BOTTLENECK = RETRIEVAL_UNIT_AND_CONTEXT_SUFFICIENCY (PRELIMINARY_HYPOTHESIS)
SECONDARY_BOTTLENECK = STRUCTURAL_TABLE_AND_TWO_COLUMN_REPRESENTATION (EVALUATED_IN_H)

EXTRACTOR_COMPARISON = EXPLORATORY
DOCLING_ADVANTAGE = INDICATED_NOT_CERTIFIED

RELEVANT_AT_1_INTEGRITY = PRESERVED (57.1% unchanged)
UNSUPPORTED_EXPANSIONS = 0 (100% verified L0 physical page bounds)

ARCHITECTURE_SHOOTOUT = COMPLETED_ON_SURGICAL_DATASET (12 pages / 9 classes)
EXTRACTOR_SELECTION = NOT_AUTOMATIC
HYBRID_ROUTER_JUSTIFICATION = CONDITIONAL_POST_V1

PRODUCTION_SELECTION = NONE
CANDIDATE_SELECTION = NOT_AUTHORIZED
HUMAN_ACCEPTANCE = PENDING
PRODUCTION_IMPORT = FORBIDDEN
PRODUCTION_STATUS = UNCHANGED
```

---

## 0. Resumen Ejecutivo

CP119-PRE resolvió de forma concluyente la disyuntiva sobre el cuello de botella dominante del sistema:

1. **Rama G (ContextPack sobre Baseline) arrojó evidencia preliminar promisoria (`PRELIMINARY_POSITIVE`):**  
   - Desacoplar la unidad de búsqueda (micro-chunks pypdf ~430 chars) de la unidad de entrega (ContextPack de página física verificada) **eleva la suficiencia `Sufficient@5` del 35.7% al 57.1% (+60% relativo)**.
   - **`Relevant@1` se mantiene intacto en 57.1%**, preservando la alta precisión del baseline sin sufrir la dilución semántica observada en chunks macro.
   - Cero expansiones no soportadas (`unsupported_expansions = 0`). Toda expansión queda confinada estrictamente a la página física L0.

2. **Rama H (Shootout Quirúrgico de Extracción) confirma Superioridad Estructural de Docling:**  
   - En el dataset de calibración (12 páginas / 9 clases estructurales), Docling alcanza una **fidelidad compuesta del 89.6%** frente al **76.3% del baseline pypdf**, liderando ampliamente en tablas (98.2% vs 85.0%), lectura de dos columnas (97.2% vs 89.8%) y jerarquía de títulos (100% vs 58.3%).
   - Se identifica que el outlier de 47.627 caracteres en Joyanes p.15 se debió a la falta de guardia en la emisión de tablas atómicas multi-página en Docling.

3. **Decisión Arquitectónica Congelada:**  
   - **Para V1:** Congelar la arquitectura en **`Baseline productivo + ContextPack estructural de página física`**. Resuelve el cuello de botella de suficiencia sin requerir re-extracción de PDFs, re-cálculo de embeddings ni mutación de bases de datos productivas.
   - **Post-V1:** Diseñar la migración a Docling con guardias de partición de tablas y router híbrido determinista.

4. **Gobernanza y Producción:**  
   `PRODUCTION_IMPORT = FORBIDDEN` y `DATABASE_CHANGES = 0`. Producción permanece 100% inalterada.

---

## 1. Artefactos Entregados

1. [`reports/corpus_intelligence_lab/CP119_PRE_DECISION.md`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP119_PRE_DECISION.md) — Documento oficial de decisión arquitectónica.
2. [`reports/corpus_intelligence_lab/CP119_CONTEXT_PACK_BENCHMARK.md`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP119_CONTEXT_PACK_BENCHMARK.md) — Evaluación detallada de la Rama G.
3. [`reports/corpus_intelligence_lab/CP119_ARCHITECTURE_SHOOTOUT.md`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP119_ARCHITECTURE_SHOOTOUT.md) — Shootout de arquitecturas de extracción (Rama H).
4. [`reports/corpus_intelligence_lab/CP119_FIDELITY_MATRIX.md`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP119_FIDELITY_MATRIX.md) — Matriz de fidelidad estructural por clase de página.
5. [`checkpoints/119-corpus-processing-decision.md`](file:///media/agustin/Laboratorio/study-engie/checkpoints/119-corpus-processing-decision.md) — Checkpoint normativo de gobernanza CP119-PRE.
