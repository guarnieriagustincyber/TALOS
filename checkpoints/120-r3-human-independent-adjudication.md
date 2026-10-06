# CP120-R3 / CP120-R3.1 / CP120-R3.2 — Adjudicación Humana Independiente y Cierre Formal de ContextPack

**Tipo:** Protocolo de Adjudicación Humana Outcome-Blinded + Aislamiento de Clave + Unmask Determinista + Cierre Arquitectónico  
**Subdominio:** Corpus Intelligence / Context Engineering  
**Precondición:** CP120-R1 = FAIL (Preasignación en CP120), CP120-R2 = FAIL (Preasignación en evaluador simulado)  
**Integridad de Datos:** `DATABASE_CHANGES = 0`  
- `BASELINE_KNOWLEDGE_DB_SHA256 = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (`data/web_state/knowledge_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_VECTOR_DB_SHA256    = 013a2462e6de6ca7cf13443338e44b7795dce4b2f7f6117827bd2ccadd0c568f` (`data/web_state/vector_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_STUDENT_DB_SHA256   = f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` (`data/web_state/student_state.db` READ-ONLY / UNCHANGED)  
- `BASELINE_DATE                = 2026-10-03T21:47:00-03:00`  

**Estado Canónico Final:**
```text
CP120_R3.2 = PASS

CP120_R3_ADJUDICATION = COMPLETE
FORM_LOCK = VERIFIED
UNMASK = COMPLETE

CONTEXT_PACK_RESULT = INCONCLUSIVE
CONTEXT_PACK_STATUS = RESEARCH_HYPOTHESIS

A_BETTER = 8/14
B_BETTER = 5/14
TIES = 1/14

SUFFICIENCY_A = 9/14
SUFFICIENCY_B = 10/14

ARCHITECTURAL_DECISION = DEFERRED

NEXT_RESEARCH_HYPOTHESIS = CP121-H1
NEXT_RESEARCH_HYPOTHESIS_STATUS = NOT_EXECUTED

CANDIDATE_SELECTION = NOT_AUTHORIZED
V1_INTEGRATION = NOT_EXECUTED
PRODUCTION_IMPORT = FORBIDDEN
PRODUCTION_STATUS = UNCHANGED
```

---

## 0. Resumen de Fases

1. **CP120-R3 (Preparación y Adjudicación Humana):**  
   - Eliminación formal de todo evaluador o juez sintético en software.
   - Creación de paquete ciego outcome-blinded (`scratch/cp120_r3_blind/`) con 14 casos anonimizados (`CASE-01` a `CASE-14`).
   - Clave de mapeo aislada (`scratch/cp120_r3_key.json`) sin acceso previo al freeze.
   - Adjudicación de los 14 casos evaluada y aprobada explícitamente por el propietario humano del proyecto.
   - Formulario congelado con SHA-256 `3a22de04201b655e49cb105ce9ace0af240728198acf6afcc25328fbb3090f4c` y sellado en `adjudication.lock`.

2. **CP120-R3.1 (Unmask Criptográfico):**  
   - Verificación estricta de pre-flight y hash del lockfile.
   - Lectura mecánica de la clave aislada post-lock.
   - Mapeo determinista X/Y $\to$ A/B sin reevaluación semántica.
   - Cálculo de métricas completas por condición.

3. **CP120-R3.2 (Cierre Formal y Post-Mortem):**  
   - Publicación del informe formal post-mortem (`reports/corpus_intelligence_lab/CP120_R3_POSTMORTEM.md`).
   - Registro de los hallazgos arquitectónicos (`CP120_POSTMORTEM_FINDINGS`).
   - Formulación de la hipótesis de expansión condicional `CP121-H1` (no ejecutada).

---

## 1. Artefactos de Auditoría Producidos

* `reports/corpus_intelligence_lab/CP120_R3_POSTMORTEM.md` (Post-mortem integral y lecciones arquitectónicas)
* `reports/corpus_intelligence_lab/CP120_R3_UNMASKED_RESULTS.md` (Informe unmasked detallado)
* `reports/corpus_intelligence_lab/CP120_R3_UNMASKED_RESULTS.json` (Resultados estructurados)
* `reports/corpus_intelligence_lab/CP120_R3_ADJUDICATION_RESULTS.json` (Estado normativo de adjudicación)
* `reports/corpus_intelligence_lab/CP120_R3_HUMAN_ADJUDICATION_PROTOCOL.md` (Protocolo y rúbrica pre-registrada)
* `reports/corpus_intelligence_lab/CP120_R3_PROCESS_INTEGRITY.json` (Integridad criptográfica)
* `scratch/cp120_r3_blind/adjudication_form_completed.json` (Formulario humano congelado)
* `scratch/cp120_r3_blind/adjudication.lock` (Lock criptográfico SHA-256)
* Directorio de descarga sincronizado: `drive_upload/cp120_r3/`

---

## 2. Métricas y Datos Observados (CP120-R3.1)

* **Casos Evaluados:** 14
* **Control A (Baseline Leaf):**
  - Suficiencia: 9/14 SUFFICIENT (64.29%), 1 PARTIAL, 4 INSUFFICIENT
  - Relevancia: 9 RELEVANT (64.29%), 3 PARTIAL, 2 NOT_RELEVANT
  - Grounding: 9 FULLY_GROUNDED (64.29%), 4 PARTIALLY_GROUNDED, 1 UNGROUNDED
  - Calidad Contextual: 7 HELPFUL, 0 NEUTRAL, 7 DISTRACTING, 0 MISLEADING
* **Experimental B (ContextPack):**
  - Suficiencia: 10/14 SUFFICIENT (71.43%), 1 PARTIAL, 3 INSUFFICIENT ($\Delta = +1$ caso, +7.14%)
  - Relevancia: 9 RELEVANT (64.29%), 3 PARTIAL, 2 NOT_RELEVANT ($\Delta = 0$)
  - Grounding: 9 FULLY_GROUNDED (64.29%), 4 PARTIALLY_GROUNDED, 1 UNGROUNDED ($\Delta = 0$)
  - Calidad Contextual: 6 HELPFUL, 0 NEUTRAL, 8 DISTRACTING, 0 MISLEADING
* **Comparación Pareada (Preferencia Humana):**
  - `A_BETTER`: 8 / 14 (57.14%)
  - `B_BETTER`: 5 / 14 (35.71%)
  - `TIES`: 1 / 14 (7.14%)

---

## 3. Dictamen y Conclusiones del Post-Mortem (CP120-R3.2)

1. **`CONTEXT_PACK_RESULT = INCONCLUSIVE`**:  
   La suficiencia factual favorece a ContextPack B (+7.14%), pero la preferencia pareada favorece a Control A (57.14%) debido al rechazo humano del ruido contextual cuando el fragmento base es suficiente. Al no existir una regla pre-registrada que pondere analíticamente cobertura vs concisión, no se introduce ningún umbral post-hoc.
2. **`ARCHITECTURAL_DECISION = DEFERRED`**:  
   Se suspende la integración de ContextPack a producción en TALOS V1. ContextPack permanece clasificado como hipótesis de investigación (`RESEARCH_HYPOTHESIS`) para ciclos posteriores.
3. **`NEXT_RESEARCH_HYPOTHESIS = CP121-H1` (`NOT_EXECUTED`)**:  
   Se formula la hipótesis de expansión contextual condicional (`CONDITIONAL_CONTEXT_EXPANSION`), sujeta a diseño formal con 17 criterios de pre-registro antes de cualquier ejecución.
4. **Inmutabilidad Absoluta:**  
   Bases de datos de producción intactas (`DATABASE_CHANGES = 0`), sin mutaciones de corpus, embeddings ni retrieval.

### CP120-R3.2-CORR

Se corrigieron dos sobreafirmaciones metodológicas del post-mortem:

1. La evidencia positiva de ContextPack se limita a casos concretos observados en la muestra y no constituye una demostración general de superioridad.
2. Se eliminó la estimación no sustentada de un incremento de consumo C3 superior al 50%.
3. La hipótesis CP121-H1 fue reformulada como hipótesis investigable, eliminando la formulación lógica "si y solo si".

Los resultados de CP120-R3.1 no fueron modificados.
`CONTEXT_PACK_RESULT` permanece `INCONCLUSIVE`.

---

## 4. Bloque Canónico de Cierre

```text
CP120_R3.2 = PASS

CP120_R3_ADJUDICATION = COMPLETE
FORM_LOCK = VERIFIED
UNMASK = COMPLETE

CONTEXT_PACK_RESULT = INCONCLUSIVE
CONTEXT_PACK_STATUS = RESEARCH_HYPOTHESIS

A_BETTER = 8/14
B_BETTER = 5/14
TIES = 1/14

SUFFICIENCY_A = 9/14
SUFFICIENCY_B = 10/14

ARCHITECTURAL_DECISION = DEFERRED

NEXT_RESEARCH_HYPOTHESIS = CP121-H1
NEXT_RESEARCH_HYPOTHESIS_STATUS = NOT_EXECUTED

CANDIDATE_SELECTION = NOT_AUTHORIZED
V1_INTEGRATION = NOT_EXECUTED
PRODUCTION_IMPORT = FORBIDDEN
PRODUCTION_STATUS = UNCHANGED
```
