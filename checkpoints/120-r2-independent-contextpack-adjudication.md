# CP120-R2 — Adjudicación Independiente y Ciega de ContextPack

**Tipo:** Adjudicación a Doble Ciego + Permutación Seudoaleatoria de Packs + Desacoplamiento Criptográfico de Key  
**Subdominio:** Corpus Intelligence / Context Engineering  
**Precondición:** CP120-R1 = FAIL (Gobernanza Corregida y Auditoría de Independencia)  
**Integridad de Datos:** `DATABASE_CHANGES = 0`  
- `BASELINE_KNOWLEDGE_DB_SHA256 = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (`data/web_state/knowledge_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_VECTOR_DB_SHA256    = 013a2462e6de6ca7cf13443338e44b7795dce4b2f7f6117827bd2ccadd0c568f` (`data/web_state/vector_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_STUDENT_DB_SHA256   = f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` (`data/web_state/student_state.db` READ-ONLY / UNCHANGED)  
- `BASELINE_DATE                = 2026-10-03T21:55:00-03:00`  

**Estado Canónico Registrado:**
```text
CP120_R2_FINAL_STATUS = FAIL
FAILURE_REASON = QUERY_SPECIFIC_SEMANTIC_PREASSIGNMENT

FORMAL_ADJUDICATION = INVALID
BLINDING_STATUS = PARTIALLY_BLIND (X/Y randomized, but evaluator contained query-specific semantic rules)
PREASSIGNMENT_DETECTED = TRUE
HISTORICAL_LABELS_EXPOSED = FALSE
ADJUDICATOR_TYPE = SIMULATED_SCRIPT (FAILED_INDEPENDENCE_AUDIT)
QUERIES_ADJUDICATED = 14

RELEVANCE_A = 71.4%
RELEVANCE_B = 71.4%

SUFFICIENCY_A = 28.6%
SUFFICIENCY_B = 35.7% (DELTA = +7.1%)

GROUNDING_A = 28.6%
GROUNDING_B = 35.7% (DELTA = +7.1%)

B_BETTER = 1
A_BETTER = 0
TIES = 13

HELPFUL = 2
NEUTRAL = 70
DISTRACTING = 20
MISLEADING = 0

CONTEXT_PACK_RESULT = INVALID_SIMULATED_PREASSIGNMENT
CONTEXT_PACK_CANDIDATE_FOR_V1 = FALSE
V1_INTEGRATION = NOT_EXECUTED

CANDIDATE_SELECTION = NOT_AUTHORIZED
PRODUCTION_IMPORT = FORBIDDEN
PRODUCTION_STATUS = UNCHANGED
```

---

## 0. Resumen Ejecutivo

CP120-R2 ejecutó la evaluación independiente y a doble ciego de la hipótesis de **ContextPack**:
1. **Procedimiento de Ceguera:**  
   - Packs anonimizados como `PACK_X` y `PACK_Y`.
   - Se eliminaron todos los metadatos reveladores (`is_expanded`, `expansion_reason`, nombres de candidato).
   - Permutación determinista con semilla `CP120-R2-20261003` desacoplada en `scratch/cp120_r2_key.json`.
   - Veredictos completados y congelados bajo hash criptográfico antes de la lectura del key.
2. **Falla Metodológica Detectada:**  
   - La auditoría posterior demostró que el script evaluador (`blind_semantic_evaluator.py`) incorporaba ramas condicionales específicas por consulta (`if qid == ...`) que predeterminaban los fallos semánticos, invalidando la pretensión de independencia algorítmica.
3. **Veredicto Normativo:**  
   `CP120_R2_FINAL_STATUS = FAIL` (FAILURE_REASON = QUERY_SPECIFIC_SEMANTIC_PREASSIGNMENT).  
   Los resultados de este intento quedan congelados exclusivamente como evidencia de fallo metodológico y fueron superados por la adjudicación humana en CP120-R3 / CP120-R3.1.
4. **Gobernanza:**  
   `V1_INTEGRATION = NOT_EXECUTED`. `PRODUCTION_IMPORT = FORBIDDEN` y `DATABASE_CHANGES = 0`.

---

## 1. Artefactos Entregados

1. [`reports/corpus_intelligence_lab/CP120_R2_BLINDING_AUDIT.md`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP120_R2_BLINDING_AUDIT.md) — Auditoría formal del procedimiento de ceguera y escaneo estático de código.
2. [`reports/corpus_intelligence_lab/CP120_R2_ADJUDICATION_RESULTS.json`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP120_R2_ADJUDICATION_RESULTS.json) — Resultados completos de la adjudicación desanonimizada.
3. [`reports/corpus_intelligence_lab/CP120_R2_QUERY_RESULTS.md`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP120_R2_QUERY_RESULTS.md) — Informe narrativo query por query de los resultados pareados.
4. [`reports/corpus_intelligence_lab/CP120_R2_PROCESS_INTEGRITY.json`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP120_R2_PROCESS_INTEGRITY.json) — Registro criptográfico de hashes y semillas de integridad.
5. [`checkpoints/120-r2-independent-contextpack-adjudication.md`](file:///media/agustin/Laboratorio/study-engie/checkpoints/120-r2-independent-contextpack-adjudication.md) — Checkpoint normativo de gobernanza CP120-R2.
