# CP120-R1 — Auditoría Metodológica de Independencia y Validez de la Adjudicación de ContextPack

**Tipo:** Auditoría Epistemológica + Detección de Reglas Inseguras + Auditoría de Blindaje y Contabilidad  
**Subdominio:** Corpus Intelligence / Context Engineering  
**Precondición:** CP120 = EXECUTED  
**Integridad de Datos:** `DATABASE_CHANGES = 0`  
- `BASELINE_KNOWLEDGE_DB_SHA256 = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (`data/web_state/knowledge_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_VECTOR_DB_SHA256    = 013a2462e6de6ca7cf13443338e44b7795dce4b2f7f6117827bd2ccadd0c568f` (`data/web_state/vector_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_STUDENT_DB_SHA256   = f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` (`data/web_state/student_state.db` READ-ONLY / UNCHANGED)  
- `BASELINE_DATE                = 2026-10-03T21:45:00-03:00`  

**Estado Canónico Registrado:**
```text
CP120_GOVERNANCE_STATUS:
  CP120 = NOT_FORMALLY_VALIDATED
  CP120_R1 = FAIL
  CONTEXT_PACK_HYPOTHESIS = PROMISING
  CONTEXT_PACK_EVIDENCE = PRELIMINARY
  CONTEXT_PACK_FORMAL_VALIDATION = NOT_ESTABLISHED
  CONTEXT_PACK_RESULT = PRELIMINARY_ONLY

  CANDIDATE_FOR_V1 = NOT_YET_VALIDATED
  V1_INTEGRATION = NOT_EXECUTED

  CANDIDATE_SELECTION = NOT_AUTHORIZED
  PRODUCTION_IMPORT = FORBIDDEN
  PRODUCTION_STATUS = UNCHANGED
```

---

## 0. Resumen Ejecutivo

CP120-R1 auditó metódicamente la adjudicación de CP120 para determinar si la evidencia presentada permitía certificar formalmente que ContextPack mejora la suficiencia de evidencia de TALOS de forma independiente.

1. **Veredicto Normativo:**  
   `CP120_R1 = FAIL`.  
   Se detectó que el script de adjudicación formal (`scratch/execute_formal_adjudication.py`) utilizó **14 ramas de código inseguras (`UNSAFE`) con asignación directa de veredictos por `query_id`**, careciendo de un motor de adjudicación independiente y ciego.
2. **Reclasificación de Resultados:**  
   - `CONTEXT_PACK_RESULT` se degrada de `VALIDATED_POSITIVE` a **`PRELIMINARY_ONLY`**.
   - La hipótesis de ContextPack permanece como **`PROMISING`**, conservando intactos los resultados anteriores como evidencia exploratoria histórica (`CP120_LEGACY_EXPLORATORY_RESULT`).
   - `CANDIDATE_FOR_V1 = NOT_YET_VALIDATED`.
   - `V1_INTEGRATION = NOT_EXECUTED`.
3. **Resolución de Contabilidad y Blindaje:**  
   - La discrepancia 91 vs 92 chunks expandidos quedó formalmente resuelta: la suma canónica real es **92 elementos expandidos** (80 chunks únicos a nivel global; 12 compartidos entre consultas solapadas).
   - Se certificó que el proceso no fue a doble ciego: `BLINDING_STATUS = NOT_BLIND`.
   - `MISLEADING = 0` y `ABSTENTION_CORRECTNESS = 100%` quedaron reclasificadas a `NOT_VALIDATED` y `NOT_EVALUATED` respectivamente, al haber sido fijadas por defecto sin arnés de desafío semántico.
4. **Desacoplamiento Canónico:**  
   Se generó la matriz tripartita `CP120_R1_EVIDENCE_MATRIX.json` que separa de forma pura: Evidencia L0/L1 $\neq$ Criterio Mínimo $\neq$ Veredicto.

---

## 1. Artefactos Entregados

1. [`reports/corpus_intelligence_lab/CP120_R1_METHODOLOGICAL_AUDIT.md`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP120_R1_METHODOLOGICAL_AUDIT.md) — Informe oficial de auditoría metodológica.
2. [`reports/corpus_intelligence_lab/CP120_R1_PREASSIGNMENT_AUDIT.json`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP120_R1_PREASSIGNMENT_AUDIT.json) — Catálogo de ramas de código inseguras y preasignadas.
3. [`reports/corpus_intelligence_lab/CP120_R1_EVIDENCE_MATRIX.json`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP120_R1_EVIDENCE_MATRIX.json) — Matriz de desacoplamiento de evidencia y criterios para las 14 consultas.
4. [`reports/corpus_intelligence_lab/CP120_R1_ACCOUNTING_AUDIT.json`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP120_R1_ACCOUNTING_AUDIT.json) — Auditoría matemática y resolución de la contabilidad de expansiones.
5. [`reports/corpus_intelligence_lab/CP120_R1_BLINDING_STATUS.md`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP120_R1_BLINDING_STATUS.md) — Dictamen normativo sobre el estado de blindaje.
6. [`checkpoints/120-r1-context-pack-methodological-audit.md`](file:///media/agustin/Laboratorio/study-engie/checkpoints/120-r1-context-pack-methodological-audit.md) — Checkpoint normativo de gobernanza CP120-R1.
