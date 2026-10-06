# CP121-DATA / CP121-DATA-CORR — Ejecución Formal del Experimento de Sufficiency Gate

**Tipo:** Ejecución Experimental Completa, Adjudicación Humana Ciega y Cierre Formal Corregido  
**Subdominio:** Corpus Intelligence / Context Engineering / Evaluadores Pre-LLM  
**Dependencia:** `CP121-PRE-FINAL = PASS` / `CP121-PRE-FINAL-CORR = PASS`  
**Hipótesis de Investigación:** `CP121_H1 = PRE_LLM_INSUFFICIENCY_DETECTION_UTILITY` (`RQ-121-01`)  
**Evaluación de Beneficio de ContextPack:** `CONTEXT_PACK_BENEFIT_EVALUATED = FALSE`  
**Resultado de ContextPack en CP121:** `CONTEXT_PACK_RESULT = NOT_EVALUATED_BY_CP121`  
**Resolución de la Hipótesis:** `H1_RESULT = NOT_SUPPORTED`  
**Decisión Arquitectónica:** `ARCHITECTURAL_DECISION = DEFERRED`  
**Integración de ContextPack en TALOS:** `CONTEXT_PACK_INTEGRATION = NOT_AUTHORIZED`  
**Integridad Criptográfica de Producción:** `DATABASE_CHANGES = 0` | `PRODUCTION_STATUS = UNCHANGED`  
- `BASELINE_KNOWLEDGE_DB_SHA256 = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (`data/web_state/knowledge_store.db` INTACTA)  
- `BASELINE_VECTOR_DB_SHA256    = 013a2462e6de6ca7cf13443338e44b7795dce4b2f7f6117827bd2ccadd0c568f` (`data/web_state/vector_store.db` INTACTA)  
- `BASELINE_STUDENT_DB_SHA256   = f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` (`data/web_state/student_state.db` INTACTA)  
- `EXECUTION_TIMESTAMP          = 2026-10-04T01:36:00Z`  

---

## 1. Resumen Metodológico Corregido

1. **Hipótesis Experimental (`CP121_H1`):**
   - Se evaluó estrictamente: *Existe al menos una política pre-LLM que, utilizando únicamente `(query, retrieved_evidence)`, puede identificar evidencia `PARTIAL/INSUFFICIENT` con utilidad predictiva superior a los baselines triviales*.
   - El beneficio o impacto factual de ContextPack **no fue evaluado en CP121** (`CONTEXT_PACK_BENEFIT_EVALUATED = FALSE`, `CONTEXT_PACK_RESULT = NOT_EVALUATED_BY_CP121`).

2. **Dataset y Splits ($N = 60$):**
   - 12 tipologías documentales preregistradas $\times$ 5 consultas cada una = 60 consultas con IDs opacos (`QUERY_INF_001` .. `QUERY_INF_060`).
   - Partición balanceada: `DEVELOPMENT` (24), `VALIDATION` (16), `TEST` (20).
   - Metadatos semánticos aislados en `scratch/cp121/oracle/query_metadata_mapping.json` (inaccesibles para inferencia).

3. **Retrieval FTS5 BM25 Congelado:**
   - Ejecutado en modo solo lectura (`mode=ro`) sobre `knowledge_store.db`.
   - Datasets ciegos validados con `inference_input_schema.json` y sellados con SHA-256.

4. **Auditoría Anti-Leakage y Protocolo de Inferencia:**
   - Auditor validado con 7 fixtures (2 PASS, 5 FAIL).
   - Código de inferencia `scratch/cp121/policies/inference_runner.py` auditado con **PASS**.
   - Secuencia completada: DEV $\to$ Calibración en DEV $\to$ VAL $\to$ `POLICY_LOCK = TRUE` $\to$ `TEST_LOCK = VERIFIED` $\to$ Inferencia en TEST $\to$ `INFERENCE_COMPLETE = TRUE`.

5. **Adjudicación Humana Post-Inferencia y Limitaciones:**
   - Adjudicación semántica humana post-inferencia, ciega respecto de las predicciones.
   - `ADJUDICATORS = 1`, `PREDICTION_BLINDING = TRUE`, `INTER_RATER_RELIABILITY = NOT_AVAILABLE`.
   - Distribución: `SUFFICIENT` = 25 (41.7%), `PARTIAL` = 12 (20.0%), `INSUFFICIENT` = 10 (16.7%), `NOT_RELEVANT` = 13 (21.7%).
   - Denominador primario de insuficiencia: $\operatorname{Count}(PARTIAL) + \operatorname{Count}(INSUFFICIENT) = 22$.

6. **Desempeño en TEST Bloqueado ($N = 20$, 15 en pool primario):**
   - `ALWAYS_SUFFICIENT`: Recall = 0.0000, FER = 0.0000.
   - `ALWAYS_INSUFFICIENT`: Recall = 1.0000, FER = 1.0000.
   - `TOKEN_LENGTH_HEURISTIC`: No mostró capacidad suficiente de generalización sobre TEST: detectó únicamente 1 de 7 casos del pool `PARTIAL/INSUFFICIENT` (Recall = 14.29%).
   - `LEXICAL_OVERLAP_HEURISTIC`: Mostró una señal parcial, pero insuficiente para justificar adopción: detectó 3 de 7 casos del pool primario (Recall = 42.86%) y dejó pasar 4 casos de insuficiencia (False Passthrough = 57.14%).
   - `CANDIDATE_COMPOSITE_GATE`: Aumentó la detección hasta 5 de 7 casos (`INSUFFICIENCY_RECALL = 5/7 = 71.43%`), pero produjo un costo excesivo sobre evidencia que el adjudicador consideró suficiente (`FALSE_EXPANSION_RATE = 6/8 = 75.00%`, `CLEAN_PASSTHROUGH = 2/8 = 25.00%`). El intercambio sensibilidad/costo resultante no fue operacionalmente aceptable.
   - Comparación pareada frente a Baseline-0: Diferencia de exactitud descriptiva $\le 0.0000$ para todas las políticas.

7. **Conclusión Acotada de H1:**
   - `H1_RESULT = NOT_SUPPORTED`.
   - *En el experimento CP121-DATA, ninguna de las políticas preregistradas evaluadas demostró utilidad predictiva suficiente para justificar la incorporación de un Sufficiency Gate pre-LLM de este tipo en producción.*
   - Conclusión limitada al espacio experimental evaluado. No se realizan sobreafirmaciones universales sobre evaluadores pre-LLM en general ni sobre ContextPack.
   - CP121 no proporciona evidencia suficiente para autorizar un Sufficiency Gate pre-LLM basado en las políticas evaluadas; ContextPack permanece diferido (`CONTEXT_PACK_INTEGRATION = NOT_AUTHORIZED`, `ARCHITECTURAL_DECISION = DEFERRED`).
   - Producción intacta (`DATABASE_CHANGES = 0`).

---

## 2. Bloque Canónico Final

```text
CP121_PRE_FINAL = PASS
CP121_PRE_FINAL_CORR = PASS

CP121_DATA = EXECUTED
CP121_DATA_EXECUTION = COMPLETE

CP121_H1 = EVALUATED
H1_RESULT = NOT_SUPPORTED

INFERENCE_BLINDING = VERIFIED
TEST_LOCK = VERIFIED

HUMAN_ADJUDICATION = COMPLETE
ADJUDICATORS = 1
PREDICTION_BLINDING = TRUE
INTER_RATER_RELIABILITY = NOT_AVAILABLE

CONTEXT_PACK_RESULT = NOT_EVALUATED_BY_CP121
CONTEXT_PACK_INTEGRATION = NOT_AUTHORIZED
ARCHITECTURAL_DECISION = DEFERRED

PRODUCTION_STATUS = UNCHANGED
DATABASE_CHANGES = 0

EXPERIMENT_REPEATED = FALSE
RESULTS_UNCHANGED = TRUE

CP121_DATA_FINAL = PASS
```
