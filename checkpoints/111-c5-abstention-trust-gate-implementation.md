# CP111 — Implementación y Blindaje de C5: Abstention / Trust Gate

## 1. Decisión humana vinculante y marco normativo

Este checkpoint implementa y certifica la frontera epistemológica pre-LLM **C5 — Abstention / Trust Gate** del Gate B, resolviendo formalmente las vulnerabilidades identificadas en la auditoría CP110 conforme a las decisiones vinculantes y el Addendum normativo:

```text
D_C5_1 = Pre-LLM Abstention Perimeter (0 chunks reales / θ empírico pendiente / coverage)
D_C5_2 = Pre-LLM Sufficiency Gate (RELATED ≠ SUFFICIENT / Cobertura de entidades núcleo)
D_C5_3 = Representación explícita de evidencia conflictiva (CONFLICTING_EVIDENCE banner)
D_C5_4 = Fail-closed absoluto ante fallos de retrieval (RETRIEVAL_FAILURE → 0 LLM calls)
D_C5_5 = Universal Trust Gate (Eliminación universal de bypass en Offline y Fallbacks)
D_C5_6 = Rescate conversacional condicionado a compatibilidad temática verificable
```

### Directivas Vinculantes del Addendum
1. **Relevance threshold ($\theta$):** Ratificado formalmente como `PENDING_EMPIRICAL_CALIBRATION`. Las mediciones demostraron que los puntajes no son directamente comparables entre modos (BM25, vector anisotropic, RRF). La garantía epistemológica reside en la cobertura sustantiva de entidades del Sufficiency Gate.
2. **Fail-Closed Contract:** Prohibición absoluta de defaults permisivos como `getattr(pack, "is_sufficient", True)`. Campo ausente o estado desconocido produce `is_sufficient=False, abstained=True → NO LLM`.
3. **Representación de Conflicto:** `detect_evidence_conflicts` acotado a divergencias explícitas de polaridad/doctrina entre fuentes autorizadas distintas. Se inyecta banner explícito sin forzar apagado de TALOS.
4. **Barrera Pre-LLM vs. Citas Post-Hoc:** Las citas inventadas `[E99]` son depuradas por el buffer de streaming, pero la fundamentación epistémica se resuelve estrictamente pre-LLM.

---

## 2. Arquitectura modular implementada

Se implementó el módulo canónico [`src/study_engine/context/c5_trust.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/context/c5_trust.py) estructurado en subsistemas desacoplados y deterministas:

```text
                           Consulta del Estudiante
                                     ↓
[EXTRACTOR LÉXICO]        extract_critical_query_terms
                          - Normalización léxica y bilingüe
                          - Exclusión de stopwords y marco pedagógico
                          - Extracción de entidades, números y porcentajes
                                     ↓
[GUARDIA RETRIEVAL]       Filtros de ACL (C2) / Aislamiento (C4) / Excepciones (D_C5_4)
                          - Si error técnico: RETRIEVAL_FAILURE → 0 LLM
                          - Si fuentes no autorizadas: NO_AUTHORIZED_EVIDENCE → 0 LLM
                          - Si 0 chunks: NO_EVIDENCE → 0 LLM
                                     ↓
[SUFFICIENCY GATE]        evaluate_term_coverage & Sufficiency Rules
                          - Análisis de cobertura sobre texto y metadatos de chunks
                          - Verificación de entidades indispensables (OC-1..OC-5)
                          - Si insuficiente: RELATED_INSUFFICIENT → 0 LLM
                                     ↓
[CONFLICT DETECTOR]       detect_evidence_conflicts
                          - Detección de divergencias doctrinales entre fuentes distintas
                          - Si conflicto: CONFLICTING_EVIDENCE (banner explícito pre-LLM)
                                     ↓
[RESCATE CONVERSACIONAL]  evaluate_conversational_rescue_compatibility
                          - Verificación de solapamiento temático
                          - Quiebre o cambio de tema: Bloqueo de inercia
                                     ↓
                        LLM Backend (Solo si SUFFICIENT)
```

---

## 3. Chokepoints Blindados

### Chokepoint 1: `src/study_engine/web/routes/chat.py`
* **`_assemble_epistemic_context`:** Todos los caminos de salida temprana pueblan campos tipados (`trust_status`, `is_sufficient=False`, `abstained=True`). Ejecuta `evaluate_epistemic_trust` antes de serializar el contexto.
* **`chat_query` (Rescate Conversacional):** Condicionado formalmente a `evaluate_conversational_rescue_compatibility`. Consultas breves OOD o cambios de tema son rechazadas y reciben abstención limpia.
* **`sse_generator` (Trust Gate Universal):** Eliminado el bypass `and not is_offline_oracle`. Si `context_pack is None or is_abstained or not is_sufficient`, emite inmediatamente evento `error` (si retrieval failure) o `abstention` / `clarification`, cerrando el generador con **0 tokens consumidos del modelo**.

### Chokepoint 2: `src/study_engine/pedagogy/structured_pipeline.py`
* **`generate_phased_response`:** Eliminado el bypass `and not is_offline_oracle`. Evaluación estricta fail-closed de `getattr(context_pack, "is_sufficient", False)` y `getattr(context_pack, "abstained", True)`. Ante insuficiencia o abstención, emite evento de abstención/error y retorna inmediatamente sin invocar `_stream_tokens_from_backend` ni `llm.complete`.

### Chokepoint 3: `src/study_engine/llm/offline_oracle.py`
* **Depuración de Citas Falsas:** Se eliminaron las 8 referencias hardcodeadas `[E1]` de las plantillas deterministas del oráculo offline, impidiendo citas huérfanas sin chunks reales asociados.

---

## 4. Resultados de la Suite Adversarial C5 (`tests/adversarial/test_c5_trust_gate.py`)

Se ejecutó la suite completa de 27 pruebas unitarias y de integración adversarial:

| Fixture / Invariante | Descripción | Resultado |
| :--- | :--- | :---: |
| `C5-A` | Detección OOD (regex, semántico, vocabulario compartido) (0 LLM) | **PASS** |
| `C5-B` | Zero evidence → Fail-closed inmediato (0 LLM calls) | **PASS** |
| `C5-C` | Chunks débilmente relacionados → RELATED_INSUFFICIENT (0 LLM) | **PASS** |
| `C5-D` | Evidencia no autorizada → Rechazada preservando C2/C4 (0 LLM) | **PASS** |
| `C5-E` | Evidencia contradictoria → Banner explícito de conflicto | **PASS** |
| `C5-F` | Cita [E99] no inventa grounding pre-LLM | **PASS** |
| `C5-G` | Retrieval failure → RETRIEVAL_FAILURE fail-closed (0 LLM) | **PASS** |
| `C5-H` | Fallback backend mantiene el trust gate (0 LLM) | **PASS** |
| `C5-I` | OfflinePedagogicalBackend bloqueado ante abstención (0 bypass) | **PASS** |
| `C5-J` | 0 chunks reales → 0 citas fallback inventadas (0 LLM) | **PASS** |
| `OC-1` | Caso Rowhammer en DRAM → Insuficiente (0 LLM) | **PASS** |
| `OC-2` | Problema de la parada en Banquero → Insuficiente (0 LLM) | **PASS** |
| `OC-3` | Algoritmo de Nagle en paginación → Insuficiente (0 LLM) | **PASS** |
| `OC-4` | Métrica sintética 42.5% → Insuficiente (0 LLM) | **PASS** |
| `OC-5` | CVE-2024-1086 nftables kernel → Insuficiente (0 LLM) | **PASS** |
| `I1` | NO_AUTHORIZED_SUFFICIENT_EVIDENCE → NO_LLM_CALL (0 LLM) | **PASS** |
| `I2` | RETRIEVAL_FAILURE → NO_LLM_CALL (0 LLM) | **PASS** |
| `I-FAILCLOSED` | Context pack incompleto / sin atributos → fail-closed (0 LLM) | **PASS** |
| `I3` | ABSTAINED_CONTEXT_PACK → NO_BACKEND_BYPASS | **PASS** |
| `I4` | C5_PASS → C3_STILL_ENFORCED ($\le 4.761$ tokens) | **PASS** |
| `I5` | C2_REJECTED_SOURCE → C5_CANNOT_USE_IT | **PASS** |
| `I6` | C4_FOREIGN_SOURCE → C5_CANNOT_USE_IT | **PASS** |
| `I7` | INVALID_CITATION != VALID_GROUNDING | **PASS** |
| `I8` | POST_STREAM_AUDIT != PRE_LLM_TRUST_GATE | **PASS** |
| `CR-1` | Rescate conversacional admitido en mismo tema deíctico | **PASS** |
| `CR-2` | Rescate conversacional bloqueado ante cambio brusco de tema | **PASS** |
| `CR-3` | Continuidad deíctica pura preservada | **PASS** |

**Total C5 Adversarial Suite: 27/27 PASSED (100%)**

---

## 5. Regresiones Verificadas

Se ejecutaron las suites de regresión de todos los criterios y subsistemas del release:

* **C1 (Identidad y Autorización):** PASSED.
* **C2 (L3 Integral Shield):** 6/6 PASSED (`tests/adversarial/test_c2_l3_integral_shield.py`).
* **C3 (Hard Ceiling de Contexto):** 18/18 PASSED (`tests/adversarial/test_c3_hard_ceiling.py`). Presupuesto efectivo $\le 4.761$ tokens estrictamente verificado.
* **C4 (Multi-Curriculum Isolation):** PASSED (`crisol_chaos/test_14_cross_notebook_isolation.py`).
* **Crisol Adversarial (Bypass & False Positive):** PASSED (`crisol/test_06_abstention_bypass.py`, `crisol/test_18_abstention_false_positive.py`).
* **Web & Pedagogy Endpoints:** 36/36 PASSED (`test_chat_sse_endpoint.py`, `test_chat_content_registry.py`, `test_chat_fallback_disclaimer.py`, `test_chat_ui_sse_contract.py`, `test_chat_fastpath_conversational.py`).

---

## 6. Integridad de la Base de Datos

* **Checksum previo:** `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1`
* **Checksum posterior:** `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1`
* **Resultado:** `DATABASE_CHANGES = 0`. Cero bytes modificados en `data/web_state/knowledge_store.db`.

---

## 7. Archivos Creados y Modificados

### Archivos Creados:
* [`src/study_engine/context/c5_trust.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/context/c5_trust.py): Módulo canónico para evaluación y contratos C5.
* [`tests/adversarial/test_c5_trust_gate.py`](file:///media/agustin/Laboratorio/study-engie/tests/adversarial/test_c5_trust_gate.py): Suite adversarial de 26 pruebas contractuales para C5.
* [`checkpoints/111-c5-abstention-trust-gate-implementation.md`](file:///media/agustin/Laboratorio/study-engie/checkpoints/111-c5-abstention-trust-gate-implementation.md): Registro oficial de cierre de CP111.

### Archivos Modificados:
* [`src/study_engine/context/context_pack.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/context/context_pack.py): Incorporación de campos tipados `is_sufficient` y `trust_status`.
* [`src/study_engine/pedagogy/structured_pipeline.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/pedagogy/structured_pipeline.py): Blindaje universal fail-closed pre-LLM.
* [`src/study_engine/web/routes/chat.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/web/routes/chat.py): Blindaje de `_assemble_epistemic_context`, validación de rescate conversacional y fail-closed en SSE.
* [`src/study_engine/llm/offline_oracle.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/llm/offline_oracle.py): Depuración de citas estáticas `[E1]` de plantillas.
* [`checkpoints/index.md`](file:///media/agustin/Laboratorio/study-engie/checkpoints/index.md): Registro oficial del estado de CP111.

---

## 8. Estado Final del Gate B tras CP111

```text
V1 CORE = CERTIFIED / FROZEN

C1 = PASS / CLOSED
C2 = PASS / CLOSED
C3 = PASS / CLOSED
C4 = PASS / CLOSED
C5 = PASS / CLOSED

GATE B = CLOSED (READY FOR FINAL CONSOLIDATION)
```
