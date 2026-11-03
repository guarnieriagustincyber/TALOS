# CP122 — Gate de Decisión Arquitectónica Post-CP121

**Tipo:** Decisión Arquitectónica y Gobernanza de Release V1  
**Subdominio:** Corpus Intelligence / Context Engineering / Arquitectura TALOS  
**Dependencias:** `CP120-R3.2-CORR = PASS`, `CP121-PRE-FINAL-CORR = PASS`, `CP121-DATA-CORR = PASS`  
**Decisión Arquitectónica:** `ARCHITECTURAL_DECISION = DEFERRED_POST_V1`  
**Estado de Investigación Inmediata:** `NEXT_EXPERIMENT = NOT_JUSTIFIED`  
**Integridad Criptográfica de Producción:** `DATABASE_CHANGES = 0` | `PRODUCTION_STATUS = UNCHANGED`  
- `BASELINE_KNOWLEDGE_DB_SHA256 = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (`data/web_state/knowledge_store.db` INTACTA)  
- `BASELINE_VECTOR_DB_SHA256    = 013a2462e6de6ca7cf13443338e44b7795dce4b2f7f6117827bd2ccadd0c568f` (`data/web_state/vector_store.db` INTACTA)  
- `BASELINE_STUDENT_DB_SHA256   = f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` (`data/web_state/student_state.db` INTACTA)  
- `TIMESTAMP                    = 2026-10-04T01:42:00Z`  

---

## 1. Síntesis de la Decisión Arquitectónica

1. **Evaluación de Evidencia Existente:**
   - CP120 demostró que ContextPack produce mejoras en casos concretos pero introduce riesgo de distracción y consumo de presupuesto C3 cuando el retrieval no es preciso (`CONTEXT_PACK_RESULT = INCONCLUSIVE`).
   - CP121 evaluó si era viable un Sufficiency Gate pre-LLM basado en señales superficiales (longitud, solapamiento léxico, combinaciones) para activar condicionalmente la expansión, concluyendo formalmente `H1_RESULT = NOT_SUPPORTED` debido a alta tasa de falsas expansiones ($FER = 75.0\%$) o bajo recall out-of-sample.

2. **Desacoplamiento Conceptual:**
   - **Q1 (Retrieval):** Localización de evidencia (Retrieval Fabric / FTS5 / Dense / Reranking).
   - **Q2 (Sufficiency):** Discriminación lógica de suficiencia (no alcanzable con heurísticas pre-LLM simples evaluadas en CP121).
   - **Q3 (Context Expansion):** Aporte factual de la expansión (trade-offs mixtos observados en CP120).

3. **Criterio de Terminación de Investigación en V1:**
   - La evaluación frente a los 7 criterios metodológicos dictaminó que una nueva investigación pre-LLM inmediata (`CP123`) no está justificada (`NEXT_EXPERIMENT = NOT_JUSTIFIED`).
   - Un evaluador semántico pre-LLM basado en un modelo adicional introduciría una nueva etapa de inferencia no medida experimentalmente por CP122, no justificada arquitectónicamente para el alcance de V1 (`SEMANTIC_PRE_LLM_COST_MEASURED = FALSE`, `SEMANTIC_PRE_LLM_V1_AUTHORIZED = FALSE`).
   - Diseñar otra heurística superficial inmediatamente después de CP121 tendría un alto riesgo de convertirse en optimización post-hoc sobre el espacio experimental ya explorado sin una pregunta nueva preregistrada.

4. **Alineación con el Roadmap V1:**
   - Se evita el scope creep dentro del alcance actual de V1. Las líneas ContextPack y Sufficiency Gate permanecen explícitamente diferidas a Post-V1 (`CONTEXT_PACK_STATUS = DEFERRED_POST_V1`, `SUFFICIENCY_GATE_STATUS = DEFERRED_POST_V1`) y no quedan refutadas ni cerradas como líneas de investigación futuras.
   - El proyecto retorna al camino crítico de finalización de TALOS V1: `E2E_STUDY_LOOP_INTEGRATION` y `RELEASE_INTEGRITY_AND_DOCUMENTATION_SYNC`.

---

## 2. Bloque Canónico Final

```text
CP122 = PASS

CP120_STATUS = CLOSED
CP121_STATUS = CLOSED

CP121_H1 = EVALUATED
H1_RESULT = NOT_SUPPORTED

CONTEXT_PACK_RESULT = NOT_EVALUATED_BY_CP121
CONTEXT_PACK_INTEGRATION = NOT_AUTHORIZED

SUFFICIENCY_GATE_STATUS = NOT_AUTHORIZED

ARCHITECTURAL_DECISION = DEFERRED_POST_V1
NEXT_EXPERIMENT = NOT_JUSTIFIED

PRODUCTION_STATUS = UNCHANGED
DATABASE_CHANGES = 0

CP122_FINAL = PASS
```
