# CP117 — Resolución de Compatibilidad de IDs y Adjudicación de Evidencia

**Tipo:** Auditoría de Compatibilidad de Identidad + Trazabilidad de Provenance + Adjudicación Formal  
**Subdominio:** Corpus Intelligence / Benchmark Fixtures  
**Precondición:** CP116 = PASS (Benchmark Oficial Ejecutado en Colab GPU)  
**Integridad de Datos:** `DATABASE_CHANGES = 0`  
- `BASELINE_KNOWLEDGE_DB_SHA256 = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (`data/web_state/knowledge_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_VECTOR_DB_SHA256    = 013a2462e6de6ca7cf13443338e44b7795dce4b2f7f6117827bd2ccadd0c568f` (`data/web_state/vector_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_STUDENT_DB_SHA256   = f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` (`data/web_state/student_state.db` READ-ONLY / UNCHANGED)  
- `BASELINE_DATE                = 2026-10-03T18:35:00-03:00`  

**Estado Canónico Registrado:**
```text
CP117 = PASS

CP113_R1_OFFICIAL_STATUS = EXECUTED
CP113_R1_ADJUDICATION = BLOCKED_BY_UNRESOLVABLE_PROVENANCE

ID_COMPATIBILITY = PARTIALLY_RESOLVED_RESTRICTED_TO_D

STRUCTURAL_DIAGNOSTICS = AVAILABLE
STRUCTURAL_GOLDEN_SET = NOT_AVAILABLE

CHUNKING_OUTLIER_STATUS = ISSUE_FOUND
OUTLIER_IMPACT = LOW
OUTLIER_HANDLING = DIAGNOSTIC_ONLY
OUTLIER_RESOLUTION = DEFERRED

CANDIDATE_SELECTION = NOT_AUTHORIZED
HUMAN_ACCEPTANCE = PENDING
PRODUCTION_IMPORT = FORBIDDEN
PRODUCTION_STATUS = UNCHANGED
```

---

## 0. Resumen Ejecutivo

CP117 ejecutó la auditoría documental exhaustiva sobre la totalidad de los **67 qrels oficiales** de `benchmark_oracle.json` para resolver la incompatibilidad taxonómica detectada en CP116 frente a los candidatos del bundle `talos_corpus_bundle_20261003T162052Z.zip` (17.832 vectores).

1. **Regla de Autoridad y Prohibición de Heurísticas:**  
   Bajo prohibición estricta de recurrir a similitud semántica, substring matching o emparejamiento visual, se evaluó cada qrel según la jerarquía `document identity → page identity → source provenance → content identity → structural provenance`.

2. **Matriz Canónica de Compatibilidad (67 Qrels):**  
   - **`RESOLVED` (4 qrels en Strategy D):** Correspondientes a `prog_punteros.pdf` (`sha256:4ece5c39...`), donde el hash SHA-256 coincide 100% bit-a-bit, la página es 1, y el macro-chunk `c0000` de Strategy D subsume el 100% de la evidencia documental.
   - **`CONFLICTING_EVIDENCE` (4 qrels en Strategy B, C y Baseline):** En estos candidatos, la segmentación dividió el texto del qrel entre chunks adyacentes sin coincidencia exacta de límites.
   - **`NOT_RESOLVABLE` (63 qrels / 94.0%):**
     * *33 qrels de Sistemas Operativos:* Proceden de excerptos en español de Tanenbaum que están 100% ausentes del bundle (el cual contiene Stallings 7th en inglés).
     * *30 qrels de Programación:* Proceden de PDFs de capítulos aislados con metadatos de página `null`; aunque el libro de Joyanes está en el bundle, carecen de crosswalk autoritativo para demostrar correspondencia unívoca con chunks de Docling sin recurrir a heurísticas prohibidas.

3. **Adjudicación Humana Formal:**  
   Se adjudicaron los 4 casos resueltos en `strategy_d` bajo la rúbrica canónica 0–3: 3 casos con calificación `3 (Direct)` y 1 caso con `2 (Substantial partial)`. El chunk fue recuperado en Rank 3 en ambas consultas en el benchmark oficial.

4. **Veredicto Normativo:**  
   Se establece canónicamente:
   ```text
   CP113_R1_ADJUDICATION = BLOCKED_BY_UNRESOLVABLE_PROVENANCE
   ```
   El oráculo histórico no es aplicable directamente a un corpus de libros completos sin un proceso formal de reconciliación documental o re-anotación de ground truth.

5. **Inmutabilidad y No-Selección:**  
   Se ratifica `DATABASE_CHANGES = 0` (hashes verificados bit-a-bit) y `CANDIDATE_SELECTION = NOT_AUTHORIZED`.