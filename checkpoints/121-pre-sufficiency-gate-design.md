# CP121-PRE / CP121-PRE-CORR — Diseño y Preregistro Corregido del Sufficiency Gate para Expansión Contextual Condicional

**Tipo:** Protocolo de Diseño Experimental y Preregistro Metodológico Corregido  
**Subdominio:** Corpus Intelligence / Context Engineering / Evaluadores Pre-LLM  
**Dependencia:** `CP120-R3.2-CORR = PASS`  
**Hipótesis:** `CP121-H1 = CONDITIONAL_CONTEXT_EXPANSION`  
**Integridad de Datos:** `DATABASE_CHANGES = 0`  
- `BASELINE_KNOWLEDGE_DB_SHA256 = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (`data/web_state/knowledge_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_VECTOR_DB_SHA256    = 013a2462e6de6ca7cf13443338e44b7795dce4b2f7f6117827bd2ccadd0c568f` (`data/web_state/vector_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_STUDENT_DB_SHA256   = f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` (`data/web_state/student_state.db` READ-ONLY / UNCHANGED)  
- `BASELINE_DATE                = 2026-10-03T21:59:00-03:00`  

**Estado Canónico Final:**
```text
CP121_PRE = PASS

CP121_H1 = PREREGISTERED
CP121_EXECUTION = NOT_STARTED

CP121_DATA = AUTHORIZED
CP121_TEST = NOT_CREATED
TEST_LOCK_STATUS = NOT_YET_CREATED

RQ = RQ-121-01
PRIMARY_METRIC = INSUFFICIENCY_DETECTION_RECALL
DENOMINATOR = PARTIAL_PLUS_INSUFFICIENT
NOT_RELEVANT_HANDLING = EXCLUDED_DIAGNOSTIC_ONLY

THRESHOLD_STATUS = PROVISIONAL
STATISTICAL_TEST_STATUS = PENDING_STATISTICAL_REVIEW
SAMPLE_SIZE_POWER = NOT_ESTABLISHED

SELF_AUDIT = INVALID
AUDITOR_FIXTURE_SUITE = VERIFIED_PASS
BLINDING_AUDIT_STATUS = OPERATIONAL

CONTEXT_PACK_IMPLEMENTATION = NOT_AUTHORIZED
PRODUCTION_STATUS = UNCHANGED
DATABASE_CHANGES = 0
```

---

## 0. Resumen y Mandato Arquitectónico

En cumplimiento de la Directiva CP121-PRE-CORR, el preregistro metodológico de CP121 fue sometido a una corrección exhaustiva para garantizar que la pregunta experimental central:

> **"¿Puede un evaluador pre-LLM detectar evidencia insuficiente sin conocer la respuesta correcta?"**

sea evaluada sin sesgos, sin auto-auditorías circulares, con separación estricta entre la evaluación semántica y la decisión operativa de expansión, y sin sobreafirmaciones estadísticas.

---

## 1. Correcciones Metodológicas Aplicadas (CP121-PRE-CORR)

1. **Eliminación del Auto-Audit y Creación de Suite de Fixtures:**
   - Se descartó la ejecución del auditor sobre sí mismo (`SELF_AUDIT = INVALID`).
   - Se crearon 7 fixtures en `scratch/cp121/fixtures/` (`clean_inference.py`, `clean_inference_with_normal_metadata.py`, `intentional_oracle_leak.py`, `intentional_query_branch.py`, `intentional_filesystem_leak.py`, `intentional_adjudication_import.py`, `intentional_qrels_leak.py`).
   - El auditor `scratch/cp121/auditors/audit_inference_blinding.py` fue validado: **PASS** en código limpio y **FAIL (Caught)** en cada fixture contaminado (auditoría léxica, AST de branching por query y llamadas I/O).

2. **Desacoplamiento de Inferencia y Evaluación:**
   - Se separaron los esquemas:
     * `scratch/cp121/schemas/inference_input_schema.json`
     * `scratch/cp121/schemas/inference_output_schema.json`
     * `scratch/cp121/schemas/adjudication_oracle_schema.json`
   - Se eliminó la variable `canonical_expansion_need` como ground truth humano. El oráculo solo contiene juicios semánticos (`RELEVANCE`, `SUFFICIENCY`). La asignación de roles operativos es estrictamente derivada y determinista.

3. **Tratamiento Separado de `NOT_RELEVANT`:**
   - Se formalizan cuatro categorías semánticas independientes: `SUFFICIENT`, `PARTIAL`, `INSUFFICIENT`, `NOT_RELEVANT`.
   - `NOT_RELEVANT` representa un fallo primario de retrieval y se excluye estrictamente del denominador de la variable primaria. Se computa como métrica diagnóstica independiente.

4. **Redefinición Rigurosa de la Variable Primaria:**
   - `INSUFFICIENCY_DETECTION_RECALL = TP / (PARTIAL + INSUFFICIENT)`.
   - Denominador exacto: $\operatorname{Count}(PARTIAL) + \operatorname{Count}(INSUFFICIENT)$.

5. **Ajuste Estadístico y de Umbrales:**
   - Se eliminó la exigencia prematura de $p < 0.05$ frente a BASELINE-0 (`STATISTICAL_TEST_STATUS = PENDING_STATISTICAL_REVIEW`), formalizando que las comparaciones son apareadas y requieren análisis específico (ej. test de McNemar).
   - Se eliminó la afirmación de potencia $>80\%$ en TEST ($N=20$), fijando `SAMPLE_SIZE_POWER = NOT_ESTABLISHED`.
   - Todos los umbrales numéricos de rendimiento fueron etiquetados como `THRESHOLD_STATUS = PROVISIONAL`.

6. **Estado del Test Lock:**
   - Se corrigió el estado a `CP121_TEST = NOT_CREATED` (`TEST_LOCK_STATUS = NOT_YET_CREATED`) dado que el dataset de prueba no ha sido generado aún.

---

## 2. Checklist Final de Validación de CP121-PRE-CORR

```text
[x] self-audit eliminado
[x] clean fixture PASS
[x] oracle leak fixture FAIL
[x] query branch fixture FAIL
[x] filesystem leak fixture FAIL
[x] adjudication import fixture FAIL
[x] inference/evaluation separation documented
[x] NOT_RELEVANT separated
[x] canonical_expansion_need removed as human ground truth
[x] primary metric corrected (denominator = PARTIAL + INSUFFICIENT)
[x] statistical test reviewed (PENDING_STATISTICAL_REVIEW)
[x] power claim corrected (SAMPLE_SIZE_POWER = NOT_ESTABLISHED)
[x] arbitrary thresholds reviewed (THRESHOLD_STATUS = PROVISIONAL)
[x] TEST lock state corrected (CP121_TEST = NOT_CREATED)
[x] production hashes verified (DATABASE_CHANGES = 0)
[x] CP120 untouched
[x] ContextPack remains unauthorized
```

---

## 3. Bloque Canónico de Cierre

```text
CP121_PRE = PASS

CP121_H1 = PREREGISTERED
CP121_EXECUTION = NOT_STARTED

CP121_DATA = AUTHORIZED
CP121_TEST = NOT_CREATED
TEST_LOCK_STATUS = NOT_YET_CREATED

RQ = RQ-121-01
PRIMARY_METRIC = INSUFFICIENCY_DETECTION_RECALL
DENOMINATOR = PARTIAL_PLUS_INSUFFICIENT
NOT_RELEVANT_HANDLING = EXCLUDED_DIAGNOSTIC_ONLY

THRESHOLD_STATUS = PROVISIONAL
STATISTICAL_TEST_STATUS = PENDING_STATISTICAL_REVIEW
SAMPLE_SIZE_POWER = NOT_ESTABLISHED

SELF_AUDIT = INVALID
AUDITOR_FIXTURE_SUITE = VERIFIED_PASS
BLINDING_AUDIT_STATUS = OPERATIONAL

CONTEXT_PACK_IMPLEMENTATION = NOT_AUTHORIZED
PRODUCTION_STATUS = UNCHANGED
DATABASE_CHANGES = 0
```
