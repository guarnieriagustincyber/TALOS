# CP116 — Ejecución Oficial del Benchmark y Resolución de Bloqueos Pre-Importación

**Tipo:** Validación Oficial de Retrieval + Resolución de Bloqueo de Fixture + Diagnóstico Forense de Outlier  
**Subdominio:** Corpus Intelligence / Ingestión Pre-V1  
**Precondición:** CP115-R1 = PASS (Bundle Rerun Auditado y Gobernanza Corregida)  
**Integridad de Datos:** `DATABASE_CHANGES = 0`  
- `BASELINE_KNOWLEDGE_DB_SHA256 = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (`data/web_state/knowledge_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_VECTOR_DB_SHA256    = 013a2462e6de6ca7cf13443338e44b7795dce4b2f7f6117827bd2ccadd0c568f` (`data/web_state/vector_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_STUDENT_DB_SHA256   = f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` (`data/web_state/student_state.db` READ-ONLY / UNCHANGED)  
- `BASELINE_DATE                = 2026-10-03T18:25:00-03:00`  

**Estado Canónico Registrado:**
```text
CP116 = PASS

CP113_R1_ORACLE = AVAILABLE
CP113_R1_OFFICIAL_STATUS = EXECUTED
CP113_R1_ADJUDICATION = PENDING

STRUCTURAL_DIAGNOSTICS = AVAILABLE
STRUCTURAL_GOLDEN_SET = NOT_AVAILABLE

CHUNKING_OUTLIER_STATUS = ISSUE_FOUND
OUTLIER_IMPACT = LOW
OUTLIER_HANDLING = DIAGNOSTIC_ONLY
OUTLIER_RESOLUTION = PENDING

CANDIDATE_SELECTION = NOT_AUTHORIZED
HUMAN_ACCEPTANCE = PENDING
PRODUCTION_IMPORT = FORBIDDEN
PRODUCTION_STATUS = UNCHANGED
```

---

## 0. Resumen Ejecutivo

CP116 completó con éxito la ejecución del benchmark oficial de retrieval CP113-R1 sobre los 4 candidatos del bundle `talos_corpus_bundle_20261003T162052Z.zip` (17.832 vectores) utilizando GPU Tesla T4 en Google Colab:

1. **Integridad del Oráculo Fixture:** Validado en Fail-Closed (`dd3d3912ddd59183f80edf08c9e4c9f9648de768e53be0d8d3006d1190d5fe2b`, 40 consultas, 67 qrels).
2. **Resultados Oficiales:** Serializados en `cp116_official_benchmark_results.json` (703 KB):
   - Baseline: Mean Top-1 `0.6303` | Mean Top-5 `0.5991`
   - Strategy B: Mean Top-1 `0.6334` | Mean Top-5 `0.6010` (19 queries mejoradas, 16 empeoradas, 5 sin cambio frente al baseline)
   - Strategy C: Mean Top-1 `0.6003` | Mean Top-5 `0.5679` (5 mejoradas, 26 empeoradas, 9 sin cambio)
   - Strategy D: Mean Top-1 `0.5876` | Mean Top-5 `0.5555` (2 mejoradas, 32 empeoradas, 6 sin cambio)
3. **Compatibilidad Ontológica:** Identificada y registrada formalmente como `ID_COMPATIBILITY = INCOMPATIBLE_TAXONOMY_REQUIRES_ADJUDICATION` sin inventar falsos mappings heurísticos.
4. **Diagnóstico Forense de Outlier:** Resueltas las 7 preguntas normativas para los bloques de Joyanes Aguilar p.15 (47.627 chars) y p.16 (40.799 chars); 0 apariciones en retrieval (`OUTLIER_IMPACT = LOW`).
5. **Inmutabilidad y Bloqueo de Selección:** `DATABASE_CHANGES = 0` verificado bit-a-bit en bases de datos productivas. Prohibición estricta de selección anticipada (`CANDIDATE_SELECTION = NOT_AUTHORIZED`, `PRODUCTION_IMPORT = FORBIDDEN`).