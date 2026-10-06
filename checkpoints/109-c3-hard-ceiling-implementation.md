# CP109 — Implementación y Blindaje del Hard Ceiling C3

## 1. Decisión humana vinculante

Este checkpoint implementa y certifica la decisión humana formal tomada tras la auditoría y diagnóstico de CP108 para cerrar el criterio **C3 — Hard Ceiling de Contexto** del Gate B:

```text
D_C3_1 = C (Layered Budget)
D_C3_2 = A+B (Deterministic Hierarchical Pruning + Fail-Closed)
D_C3_3 = A (Conservative estimation: ceil(characters / 4) con 5% de margen de seguridad)
```

Condiciones vinculantes ratificadas:
* `NORMATIVE_CEILING = 5000 tokens`
* `SAFETY_MARGIN_RATIO = 0.05 (5%)`
* `EFFECTIVE_CEILING = 4761 tokens (19.044 caracteres)`
* `DATABASE_CHANGES = 0` (SHA: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1`)
* `BLIND_TRUNCATION = FORBIDDEN`
* `V1_5_IMPLEMENTATION = NOT_AUTHORIZED`
* `V2_IMPLEMENTATION = NOT_AUTHORIZED`
* `C5 = REMAINS_PENDING`

---

## 2. Contrato implementado

El hard ceiling C3 establece una garantía física pre-LLM:

$$\forall \text{payload} \in \text{LLM\_dispatched\_calls}: \text{estimate\_tokens}(\text{payload}) \le \text{EFFECTIVE\_CONTEXT\_CEILING\_TOKENS} (4.761)$$

Si el payload inicial excede 4.761 tokens:
1. Se activa el pipeline determinista de poda jerárquica: `REDUNDANT → OPTIONAL → PEDAGOGICALLY_USEFUL → EVIDENCE`.
2. Se re-verifica el payload real resultante.
3. Si el payload podado entra en el presupuesto: se despacha al modelo con los componentes podados y conservando la evidencia primaria y la directiva pedagógica crítica.
4. Si el desborde es irreducible: **FAIL-CLOSED**. Se emite un evento observable de error (`StreamEvent(event_type="error", payload={"error_code": "CONTEXT_BUDGET_EXCEEDED", ...})`), interrumpiendo la ejecución inmediatamente con **0 llamadas al proveedor LLM**.

---

## 3. Arquitectura real y chokepoints triples (Defensa en Profundidad)

El control físico no depende de metadatos declarativos de proveedores ni de la ventana de contexto del modelo. Se estructura en tres chokepoints físicos consecutivos:

```text
               User Query + Context Pack + Pedagogical Directives
                                      ↓
[CHOKEPOINT 1]    StructuredResponsePipeline.generate_phased_response
                  - Medición pre-stream
                  - Enforce C3 Layered Budget
                  - Poda jerárquica determinista
                  - Si irreducible: FAIL-CLOSED (StreamEvent: CONTEXT_BUDGET_EXCEEDED, 0 llamadas)
                                      ↓
[CHOKEPOINT 2]    StructuredResponsePipeline._stream_tokens
                  - Guardia terminal pre-adaptador
                  - Medición de payload real (stream o prompt_bundle)
                  - Si tokens > 4.761: raise ContextBudgetExceededError
                                      ↓
[CHOKEPOINT 3]    MultiFallbackBackend (complete & stream)
                  - Guardia terminal pre-proveedor
                  - Validación antes de contactar al proveedor primario o iterar fallbacks
                  - Si tokens > 4.761: raise ContextBudgetExceededError
                                      ↓
                             LLM Provider / API
```

---

## 4. Política estratificada de presupuesto (Layered Budget)

Se definieron los sub-presupuestos por componente, calibrados contra las mediciones empíricas de CP108 (donde el base system prompt fue medido en ~1.299 tokens):

| Componente | Prioridad Semántica | Sub-presupuesto (tokens) | Sub-presupuesto (chars) |
| :--- | :--- | :---: | :---: |
| `System / Base instructions` | `PEDAGOGICALLY_CRITICAL` | 1.350 | 5.400 |
| `User query` | `PEDAGOGICALLY_CRITICAL` | 250 | 1.000 |
| `Primary evidence` | `PEDAGOGICALLY_CRITICAL` | 1.800 | 7.200 |
| `Secondary / Peripheral evidence` | `OPTIONAL / USEFUL` | 350 | 1.400 |
| `Conversation history` | `PEDAGOGICALLY_USEFUL` | 350 | 1.400 |
| `Pedagogical directives (BKT, mode, style)` | `PEDAGOGICALLY_CRITICAL / USEFUL` | 400 | 1.600 |
| `Cognitive memory / Profile` | `PEDAGOGICALLY_USEFUL` | 200 | 800 |
| `Contextual reserve / Safety buffer` | `OPTIONAL` | 61 | 244 |
| **Total Estratificado** | — | **4.761** | **19.044** |

**Invariante:** $\sum \text{sub-presupuestos} = 4.761 \le \text{EFFECTIVE\_CONTEXT\_CEILING\_TOKENS}$.

---

## 5. Política de poda determinista (Hierarchical Pruning)

Cuando el payload supera 4.761 tokens, la poda se ejecuta determinísticamente en el siguiente orden estricto:

1. **Fase 1 (REDUNDANT):**
   - Remoción de saltos de línea excesivos y espaciado redundante.
   - Eliminación de encabezados idénticos duplicados consecutivamente.
   - Descarte de ítems de listas de verificación consecutivas duplicadas.
2. **Fase 2 (OPTIONAL):**
   - Supresión de contexto de fases predecesoras no requeridas (`predecessor_context`).
   - Supresión de directivas secundarias no esenciales.
3. **Fase 3 (PEDAGOGICALLY_USEFUL):**
   - Poda progresiva turno por turno del historial conversacional (del más antiguo al más reciente) hasta que el historial entre en su sub-presupuesto de 350 tokens.
   - Si persiste desborde, supresión del bloque de perfil cognitivo histórico (`cognitive_profile_block`).
   - Si persiste desborde, supresión de directivas secundarias de estilo (`style_directive`).
4. **Fase 4 (EVIDENCE REDUCTION):**
   - Poda de evidencia periférica / secundaria respetando los chunks primarios más relevantes.
   - Calibración de la evidencia primaria restante exactamente al espacio residual disponible en el presupuesto del prompt.
   - Si persiste desborde, remoción total de historial previo para maximizar espacio de evidencia.
5. **Fase 5 (VERIFY):**
   - Medición final del payload resultante.
   - Si $\text{estimated\_tokens} \le 4.761$: procede al LLM.
   - Si $\text{estimated\_tokens} > 4.761$: **FAIL-CLOSED**.

---

## 6. Blindaje de bypasses históricos

* **Bypass A (Fallback de citations en `chat.py`):**
  En `src/study_engine/web/routes/chat.py:1296`, cuando `expanded_context_text` es vacío, la unión `"\n\n".join(citations_formatted)` queda acotada previamente por `prune_evidence_text_deterministically(..., max_tokens=2150)` y posteriormente sujeta al chokepoint global C3 de 4.761 tokens.
* **Bypass B (Expansión vs Prompt):**
  La cota de expansión en `SectionExpander` (1.800 tokens) opera como límite local; el chokepoint pre-LLM garantiza que todo el ensamblado global no supere 4.761 tokens.
* **Bypass C (Metadatos de Provider):**
  El límite se aplica localmente con independencia de si el proveedor reporta 1.000 tokens o 1.000.000 tokens.
* **Bypass D (Historial conversacional):**
  Los turnos conversacionales son contabilizados en el presupuesto global y podados determinísticamente de forma progresiva.
* **Bypass E (Inyecciones pedagógicas post-retrieval):**
  BKT, modo de lucha, scaffolding, checklists y directivas de fase están totalmente integrados en la medición del payload real.

---

## 7. Resultados de la Suite Adversarial C3

Se implementó la suite completa en `tests/adversarial/test_c3_hard_ceiling.py` cubriendo 18 escenarios:

| Test / Escenario | Descripción | Tokens Iniciales | Acción C3 | Tokens Finales | Resultado |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `test_c3_normative_constants_and_sub_budgets` | Coherencia aritmética de constantes | — | Verificación estática | — | **PASSED** |
| `test_c3_token_estimation_conservative` | Fórmula $\lceil \text{chars} / 4 \rceil$ | — | Validación matemática | — | **PASSED** |
| `test_case_1_small_prompt_passes_intact` | Prompt dentro de presupuesto | 412 | Pasa intacto (0 podas) | 412 | **PASSED** |
| `test_case_2_evidence_overflow_prunes_secondary` | Evidencia masiva (3 chunks) | ~3.200 | Poda evidencia periférica | 2.148 | **PASSED** |
| `test_case_3_history_overflow_prunes_progressively` | Historial extenso (5 turnos) | ~2.800 | Poda turnos antiguos | 2.100 | **PASSED** |
| `test_case_4_memory_overflow_pruning` | Memoria contextual sobredimensionada | ~2.600 | Poda perfil cognitivo | 1.850 | **PASSED** |
| `test_case_5_fallback_overflow_protected` | Fallback de citas masivo (25 citas) | ~5.800 | Acotado y podado | 2.500 | **PASSED** |
| `test_case_6_irreducible_overflow_fails_closed` | Query de 25.000 chars irreducible | ~6.500 | **FAIL-CLOSED** (0 llamadas LLM) | 0 despachados | **PASSED** |
| `test_case_7_and_8_provider_window_independence` | Provider mock con ventana de 1.000.000 tokens | ~8.000 | Poda a ceiling TALOS | $\le 4.761$ | **PASSED** |
| `test_fixture_a_reproduction` | Fixture A de CP108 (retrieval modesto) | 6.306 | Podado a presupuesto | $\le 4.761$ | **PASSED** |
| `test_fixture_b_reproduction` | Fixture B de CP108 (retrieval cerca de ceiling) | 10.678 | Podado a presupuesto | $\le 4.761$ | **PASSED** |
| `test_fixture_c_reproduction` | Fixture C de CP108 (fallback citas vacío) | 10.886 | Bounded y podado | $\le 4.761$ | **PASSED** |
| `test_fixture_d_reproduction` | Fixture D de CP108 (long history 4 turnos) | 10.936 | Podado a presupuesto | $\le 4.761$ | **PASSED** |
| `test_fixture_e_reproduction` | Fixture E de CP108 (evidence 8k tokens) | 10.825 | Podado a presupuesto | $\le 4.761$ | **PASSED** |
| `test_chokepoint_2_stream_tokens_raises_on_breach` | Invocación directa de `_stream_tokens` con desborde | > 4.761 | Lanza `ContextBudgetExceededError` | 0 streams | **PASSED** |
| `test_chokepoint_3_multi_fallback_stream_raises` | Invocación directa de `MultiFallbackBackend.stream` | > 4.761 | Lanza `ContextBudgetExceededError` | 0 calls | **PASSED** |
| `test_chokepoint_3_multi_fallback_complete_raises` | Invocación directa de `MultiFallbackBackend.complete` | > 4.761 | Lanza `ContextBudgetExceededError` | 0 calls | **PASSED** |
| `test_performance_overhead_measurement` | Medición de latencia de cómputo de poda | — | 50 iteraciones consecutivas | avg = 0.003 ms | **PASSED** |

**Total suite C3:** **18 passed, 0 failed**.

---

## 8. Resultados de la Regresión del Sistema

* **Regresión C2 (L3 Integral Shield):**
  `tests/adversarial/test_c2_l3_integral_shield.py` $\to$ **6 passed, 0 failed**.
* **Regresión de Pedagogía:**
  `tests/pedagogy/` $\to$ **94 passed, 0 failed** (incluyendo tests e2e de NotebookLM, streaming y guards socráticos).
* **Regresión General (Retrieval, Contract, Web):**
  `tests/unit/retrieval tests/contract tests/unit/web` $\to$ **657 passed, 0 failed**.
* **Total general verificado:** **775 tests ejecutados, 0 fallos**.

---

## 9. Rendimiento y Overhead Observacional

Se ejecutó un benchmark de 50 repeticiones sobre payloads representativos del pipeline:
* **Tiempo promedio de ejecución de `enforce_c3_budget`:** **0,003 ms** (3 microsegundos).
* **Tiempo máximo registrado:** **0,012 ms** (12 microsegundos).
* **Impacto en latencia de respuesta:** Despreciable (orden de microsegundos frente a latencias de inferencia de 500-2000 ms).

---

## 10. Integridad de la Base de Datos

* `sha256sum data/web_state/knowledge_store.db`:
  - Antes de CP109: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1`
  - Después de CP109: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1`
* `DATABASE_CHANGES = 0`. La base de datos permaneció 100% inalterada.

---

## 11. Archivos Creados y Modificados

### Archivos Creados:
* [`src/study_engine/context/c3_budget.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/context/c3_budget.py): Módulo con constantes normativas y operativas de C3, sub-presupuestos estratificados, estimación conservadora con margen de seguridad, algoritmos de poda determinista jerárquica y fail-closed.
* [`tests/adversarial/test_c3_hard_ceiling.py`](file:///media/agustin/Laboratorio/study-engie/tests/adversarial/test_c3_hard_ceiling.py): Suite de 18 tests adversariales y contractuales para C3.
* [`checkpoints/109-c3-hard-ceiling-implementation.md`](file:///media/agustin/Laboratorio/study-engie/checkpoints/109-c3-hard-ceiling-implementation.md): Documento oficial de cierre de CP109.

### Archivos Modificados:
* [`src/study_engine/llm/exceptions.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/llm/exceptions.py): Incorporación de `ContextBudgetExceededError(LLMError)`.
* [`src/study_engine/llm/__init__.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/llm/__init__.py): Exportación de `ContextBudgetExceededError`.
* [`src/study_engine/llm/multi_fallback.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/llm/multi_fallback.py): Implementación del Chokepoint 3 (provider guard en `complete` y `stream`).
* [`src/study_engine/pedagogy/structured_pipeline.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/pedagogy/structured_pipeline.py): Implementación de Chokepoints 1 y 2 en `generate_phased_response` y `_stream_tokens`, con calibración residual de evidencia y fail-closed determinista.
* [`src/study_engine/web/routes/chat.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/web/routes/chat.py): Acotamiento de citas en fallback y salvaguarda de tipos en resolución de manifiesto.
* [`src/study_engine/contracts/l3_manifest.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/contracts/l3_manifest.py): Salvaguarda de tipo en `manifest_path`.
* [`checkpoints/index.md`](file:///media/agustin/Laboratorio/study-engie/checkpoints/index.md): Registro de cierre de CP109.

---

## 12. Régimen de Modificación de TALOS V1

* **Estado previo:** `V1 CORE = CERTIFIED / FROZEN`.
* **Clasificación del cambio:** `POST-CERTIFICATION ASSURANCE CHANGE`.
* **Justificación técnica:** Subsanación física del assurance blocker C3 de Gate B mediante implementación mínima y localizada.
* **Impacto en congelamiento:** Los cambios quedaron estrictamente confinados a los guards pre-LLM, sin introducir features de TALOS 1.5 ni de V2.

---

## 13. Estado Final C3

Conforme a los doce requisitos de cierre estipulados:
1. Existe ceiling global físico vinculado a 4.761 tokens efectivos (5.000 nominales con 5% de margen).
2. Existen sub-presupuestos internos coherentes ($\sum = 4.761$).
3. Ningún componente pedagógico ni de contexto puede bypassar los chokepoints.
4. Fallback de citas en `chat.py` está protegido.
5. Historial conversacional está protegido y entra en el presupuesto.
6. Inyecciones pedagógicas post-retrieval están contabilizadas.
7. La poda es determinista y jerárquica.
8. El desborde irreducible produce `FAIL-CLOSED` inmediato (`CONTEXT_BUDGET_EXCEEDED`).
9. Ningún llamado al proveedor puede ejecutarse sobre presupuesto.
10. La suite adversarial de 18 pruebas pasa al 100%.
11. La regresión del sistema (757 pruebas adicionales) pasa al 100%.
12. La base de datos SQLite permanece idéntica (`DATABASE_CHANGES = 0`).

```text
C3 = PASS / CLOSED
```
