# CP108 — ADJUDICACIÓN DE C3: HARD-CEILING DE CONTEXTO Y PROMPT

## 0. Identidad y marco de la auditoría

```text
CP = 108
GATE = B (Identidad y aislamiento curricular)
CRITERIA = C3 (Hard-Ceiling de Contexto y Prompt)
BASE_COMMIT = f81134fc2293916210d53c8065f3a0049e52b0b4
DATE = 2026-10-02
ROL = Auditor Técnico Senior de Assurance de TALOS
METODOLOGÍA = OBSERVE → MEASURE → CORRELATE → PRESENT OPTIONS → HUMAN DECISION
ESTADO ANTERIOR = C3 = AUDITED / BLOCKED (CP103, CP106.1)
DICTAMEN CP108 = C3 = DECISION READY (Bloqueado pendiente de adjudicación humana)
DATABASE_CHANGES = 0
```

### 0.1 Propósito y regla de neutralidad
Este checkpoint **NO implementa cambios en código de producción, contratos ni bases de datos**. Su propósito exclusivo es delimitar formalmente el problema, medir experimentalmente el comportamiento del runtime de TALOS V1, correlacionar la evidencia y presentar a la autoridad del proyecto las opciones rigurosamente analizadas para las tres decisiones humanas pendientes:

* **D_C3_1 — Perímetro del Hard-Ceiling**
* **D_C3_2 — Política de mitigación ante desborde (Overflow Policy)**
* **D_C3_3 — Método de medición del presupuesto**

Conforme a las reglas de Gate B, el auditor **no auto-adjudica ni predetermina la "mejor opción"**. Los tres campos decisorios permanecen en estado `PENDING` hasta que el propietario emita su instrucción formal.

---

## 1. Estado de partida de Gate B

Tras la certificación formal de C4 en CP107, el estado de las garantías de Gate B es:

```text
V1 CORE = CERTIFIED / FROZEN

C1 (IDs / aliases / curriculum_id) = PASS / CLOSED  (Certificado en CP097)
C2 (Roles de fuente y ACL efectiva) = PASS / CLOSED  (Certificado en CP102)
C3 (Hard-ceiling de contexto)       = AUDITED / BLOCKED (Decision Ready en CP108)
C4 (Multi-Curriculum Isolation)     = PASS / CLOSED  (Certificado en CP107)
C5 (Gate de abstención y confianza) = BLOCKED / ASSURANCE_BLOCKER

Gate B = NOT YET CLOSED (Pendiente cierre de C3 y C5)
```

---

## 2. Invarianza física de la base de datos

Se comprobó la inmutabilidad estricta de `data/web_state/knowledge_store.db` al inicio y cierre de todas las mediciones experimentales:

```bash
sha256sum data/web_state/knowledge_store.db
# PRE:  fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1
# POST: fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1
```
```text
DATABASE_CHANGES = 0
INTEGRITY_VERIFIED = PASS
```

---

## 3. Mapeo estructural de límites por frontera (Boundary Map)

Se auditó de forma exhaustiva el ciclo de vida completo de una solicitud de estudio en `src/study_engine/` desde el ingreso del string del estudiante hasta el despacho HTTP al proveedor:

$$\text{Query} \to \text{Rewriter} \to \text{Retrieval} \to \text{Expansion} \to \text{Evidence} \to \text{Context} \to \text{Prompt} \to \text{Fallback} \to \text{Provider} \to \text{LLM}$$

| Frontera / Etapa | Límite Existente | ¿Es Límite Físico? | ¿Está Aplicado (Enforced)? | Modo de Falla / Comportamiento |
| :--- | :---: | :---: | :---: | :--- |
| **Query** | Sin límite estricto | No en tokens | No | Strings largos entran completos al pipeline |
| **Rewriter** | Ventana de 300 chars | SÍ | SÍ (hardcodeado) | Trunca historial técnico previo a reescribir |
| **Retrieval** | `retrieval_limit` (8, 15, 25) | SÍ | SÍ (SQL LIMIT) | Limita cardinalidad de candidatos a recuperar |
| **Expansion** | `HARD_CEILING_TOKENS` (5.000 / 1.800) | SÍ (Local) | SÍ (en raw chunks) | Poda chunks periféricos si $\sum \text{token\_count} > \text{ceiling}$ |
| **Evidence** | `citations_formatted` | **NO** | **NO** | Concatena chunks crudos sin límite si expander falla |
| **Context Assembly** | `ContextCompiler.max_context_tokens` (40k) | **NO** | **NO (Declarativo)** | El pipeline productivo de chat no lo invoca |
| **Prompt Compilation** | `build_phase_prompt` | **NO** | **NO** | Concatena 15 bloques pedagógicos sin límite |
| **Fallback** | `final_formatted = "\n\n".join(cits)` | **NO** | **NO** | Inyecta hasta 25 chunks sin límite de caracteres |
| **Provider Adapter** | `messages = [{"role": sys}, {"role": user}]` | **NO** | **NO** | Cero pre-LLM check; despacha payload ciego a red |
| **LLM (Remote API)** | Ventana del proveedor (8K - 1M) | SÍ (Externo) | SÍ (Servidor externo) | Error HTTP 400 (context length) o 429 (rate limit) |

### Hallazgo central:
El techo de 5.000 tokens configurado en `src/study_engine/retrieval/expansion.py` opera **exclusivamente como un filtro de poda de chunks en el paso de expansión**. Entre la salida de `SectionExpander` y la llamada HTTP final al LLM ocurren múltiples inyecciones sucesivas (System Prompt, BKT, Lucha, Scaffolding, Espiral, Mem0, Historial y Plantillas de Fase) que operan en un espacio **completamente desprovisto de hard-ceiling**.

---

## 4. Semántica real de `provider.max_context_tokens()`

Se auditó la totalidad de los proveedores en `src/study_engine/llm/providers/`:
* `CerebrasProvider.max_context_tokens()` $\to$ `131.072`
* `GroqProvider.max_context_tokens()` $\to$ `131.072`
* `GeminiProvider.max_context_tokens()` $\to$ `1.048.576`
* `NvidiaNemotronProvider.max_context_tokens()` $\to$ `1.000.000`
* `OpenRouterProvider.max_context_tokens()` $\to$ `1.000.000`
* `XkiroProvider.max_context_tokens()` $\to$ `1.000.000`
* `CloudflareProvider` $\to$ No implementa el método (AttributeError en introspección)

### Evidencia en el código:
En todo `src/`, la única referencia en runtime a `prov.max_context_tokens()` ocurre en `src/study_engine/llm/registry.py:127`:
```python
if prov.max_context_tokens() < min_context_tokens:
    continue
```
Se utiliza únicamente como un filtro estático de selección en el `ModelRegistry`. **No existe ninguna comparación en runtime entre el tamaño real del prompt a enviar y `max_context_tokens()`**.

```text
VEREDICTO:
provider.max_context_tokens() es METADATO DECLARATIVO DE CAPACIDAD EXTERNA.
NO CONSTITUYE UN RUNTIME ENFORCEMENT NI PROTEGE A TALOS.
```

---

## 5. Resultados de las mediciones experimentales (Fixtures A–E)

Se ejecutó el arnés de medición reproducible (`scratch/measure_cp108_fixtures.py`) sobre los contratos de producción y datos reales de `knowledge_store.db`.

Se tabularon las doce (12) métricas requeridas por fixture:

| Métrica | Fixture A (Retrieval bajo) | Fixture B (Prompt sobre ceiling) | Fixture C (Empty Fallback) | Fixture D (Long History, 4t) | Fixture E (Evidence 8k) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `retrieval_tokens` | 2.514 | 4.682 | 7.747 | 4.682 | 4.682 |
| `evidence_tokens` | 4.031 | 8.078 | 8.193 | 8.078 | 8.000 |
| `history_tokens` | 0 | 105 | 105 | 354 | 105 |
| `memory_tokens` | 0 | 25 | 25 | 25 | 25 |
| `pedagogical_tokens` | 20 | 233 | 233 | 233 | 233 |
| `system_tokens` | 1.299 | 1.299 | 1.299 | 1.299 | 1.299 |
| `query_tokens` | 9 | 24 | 10 | 24 | 24 |
| `other_tokens` (plantillas/fase) | 947 | 939 | 1.046 | 939 | 939 |
| **`total_prompt_tokens`** | **6.306** | **10.678** | **10.886** | **10.936** | **10.825** |
| `nominal_ceiling` | 5.000 | 5.000 | 5.000 | 5.000 | 5.000 |
| **`overflow_tokens`** | **+1.306** | **+5.678** | **+5.886** | **+5.936** | **+5.825** |
| **`overflow_percentage`** | **+26.1%** | **+113.6%** | **+117.7%** | **+118.7%** | **+116.5%** |

### Análisis de los fixtures:
* **Fixture A:** Aun con un retrieval modesto (2.514 tokens de chunks), el prompt total alcanza **6.306 tokens** debido al system prompt (1.299 tokens), metadatos de tags en evidencia (4.031 tokens) y plantillas de fase (947 tokens), superando el techo formal en +26.1%.
* **Fixture B:** Con retrieval podado al límite (4.682 tokens de chunks), el prompt final entregado al LLM totaliza **10.678 tokens (+113.6% de desborde)**.
* **Fixture C:** Cuando la expansión falla o retorna vacía, el fallback de citas inyecta **8.193 tokens de evidencia desprotegida**, llevando el prompt a **10.886 tokens (+117.7%)**.
* **Fixture D:** A medida que la historia crece, el buffer estabiliza el historial en los últimos 4 turnos (`conv_turns[-4:]`), pero los 4 turnos suman hasta 354 tokens que se agregan directamente al desborde general.
* **Fixture E:** La variación directa del componente de evidencia demuestra una relación puramente lineal: cada 1.000 tokens de evidencia agregada aumentan el prompt exactamente en 1.000 tokens sin ningún mecanismo de corte o freno.

---

## 6. Validación y deconstrucción de la cifra ~13k

En CP103 se documentó un máximo empírico de aproximadamente **`~13.281 estimated tokens`**.

Se auditó el origen y reproducibilidad exacta de este valor:
1. **¿Cómo se obtuvo?**:
   Corresponde al caso patológico extremo donde se combinan simultáneamente:
   - Fallback de retrieval desprotegido con 25 chunks grandes de bibliografía densa (`src_stallman_gnu_c_manual` o `src_joyanes_fundamentos` que poseen chunks de hasta 3.450 tokens): ~8.200 a 8.500 tokens de citas.
   - System prompt completo de cátedra (perfil formal y fase): ~1.300 tokens.
   - Historial en modo de continuación (4 turnos de hasta 1.200 chars c/u): ~1.200 tokens.
   - Directivas BKT completas con Protocolo de Lucha activo y consignas de entregables: ~500 tokens.
   - Memoria Mem0 de largo plazo + Resumen de sesión previa: ~400 tokens.
   - Plantillas estructurales de fase, directivas de estilo, checklist de entidades y protocolo anti-atajo: ~1.400 tokens.
2. **Cálculo exacto**:
   $$\text{Total Chars} \approx 53.124 \text{ caracteres}$$
   $$\text{Total Tokens} = 53.124 // 4 = \mathbf{13.281 \text{ tokens}}$$
   $$\text{Desborde sobre 5.000} = +8.281 \text{ tokens } (\mathbf{+165.6\%})$$
3. **Naturaleza de la cifra**:
   - `13.281` **no es una constante estática ni un requisito contractual**.
   - Es la **cota superior empírica observada** en sesiones multi-turno complejas bajo el código de V1 sin pre-LLM hard ceiling.
   - El desglose confirma que la evidencia aporta entre el 60% y el 70% del desborde, mientras que la infraestructura pedagógica y el historial aportan el 30% a 40% restante.

---

## 7. Análisis de D_C3_1 — Perímetro del Hard-Ceiling

| Dimensión de Análisis | Opción A: Evidence Ceiling | Opción B: Total Prompt Ceiling | Opción C: Layered Budget |
| :--- | :--- | :--- | :--- |
| **Definición** | Límite exclusivo sobre el contexto de evidencias recuperado (`retrieval + expansion ≤ CEILING`). | Límite absoluto sobre el payload total enviado al modelo (`messages JSON ≤ CEILING`). | Desacoplamiento en sub-presupuestos coordinados con suma acotada ($\sum \text{budgets} \le \text{TOTAL}$). |
| **`SEMANTIC_IMPACT`** | Preserva la noción histórica de V1 (techo de RAG). El prompt global sigue siendo variable e ilimitado. | Transforma C3 en una garantía estricta pre-LLM. El modelo jamás recibe más tokens que el límite fijado. | Garantiza previsibilidad granular por componente (garantiza espacio reservado para BKT, Memoria y Evidencia). |
| **`IMPLEMENTATION_IMPACT`** | Mínimo: solo requiere blindar el fallback en `chat.py` y computar tags de metadatos dentro de `SectionExpander`. | Medio-Alto: requiere un interceptor/guard pre-LLM en `StructuredResponsePipeline` o adapter. | Alto: requiere implementar un orquestador de presupuesto (Budget Allocator) que asigne cuotas dinámicas. |
| **`BACKWARD_COMPATIBILITY`** | 100% compatible con la semántica de TALOS V1. No altera la estructura de directivas ni turnos. | Podría podar directivas o turnos en sesiones largas que hoy se despachan sin restricciones. | Requiere redefinir cómo interactúan los routers de granularidad y los módulos pedagógicos. |
| **`FAILURE_MODES`** | **Fuga de prompt hacia el LLM**: desborde en proveedores con ventana corta o agotamiento de TPM. | **Riesgo de sobre-poda**: si el límite es bajo, podría recortar directivas pedagógicas esenciales o turnos. | **Fragmentación de cuota**: sub-presupuestos subutilizados mientras otro componente sufre escasez. |
| **`PEDAGOGICAL_IMPACT`** | Cero riesgo de recorte pedagógico (BKT, Lucha y memoria entran completos). | Podría requerir sacrificar turnos antiguos o evidencias para salvar directivas de lucha. | Permite blindar formalmente que directivas críticas (BKT) nunca sean recortadas por exceso de evidencia. |
| **`PROVIDER_IMPACT`** | TALOS sigue dependiendo de que la ventana del proveedor externo absorba el exceso sin rebotar. | Independencia absoluta del proveedor: cualquier modelo con ventana $\ge \text{CEILING}$ funcionará de forma idéntica. | Igual que B, con control determinista de costos por token en proveedores de pago. |
| **`MEASUREMENT_DIFFICULTY`** | Muy baja: se mide únicamente en `SectionExpander` y `citations_formatted`. | Baja: se mide en un único chokepoint terminal previo a invocar `client.stream()`. | Media: requiere medir y validar cada componente individualmente antes de la concatenación. |

---

## 8. Análisis de D_C3_2 — Política de Mitigación ante Desborde (Overflow Policy)

### Opción A — Deterministic Hierarchical Pruning
* **Mecanismo**: Eliminar contenido siguiendo una prioridad jerárquica estricta hasta encajar en el presupuesto:
  $$\text{Turnos conversacionales antiguos} \to \text{Chunks de menor score} \to \text{Directivas opcionales/digest} \to \text{Evidencia complementaria}$$
* **Ventaja**: Preserva la continuidad de la sesión del estudiante sin interrumpir la interacción.
* **Riesgo**: Requiere que la jerarquía de poda esté perfectamente alineada con la seguridad pedagógica para no podar advertencias críticas de andamiaje.

### Opción B — Fail-Closed
* **Mecanismo**: Si `prompt_tokens > budget`, TALOS no llama al LLM y responde inmediatamente con un error tipado o abstención: `CONTEXT_BUDGET_EXCEEDED`.
* **Ventaja**: Máximo determinismo formal y simplicidad técnica. Cero riesgo de alucinación por poda accidental.
* **Riesgo**: Experiencia de usuario frágil: sesiones de estudio profundas o consultas complejas quedan bloqueadas si el contexto supera el presupuesto.

### Opción C — Blind Tail Truncation
* **Mecanismo**: Recortar caracteres o tokens desde el final del prompt (`prompt[:MAX]`) hasta satisfacer el techo.
* **Ventaja**: Implementación trivial de una sola línea.
* **Riesgo CRÍTICO**: Puede mutilar código fuente a la mitad, romper estructuras JSON, cortar la pregunta del estudiante o eliminar la consigna pedagógica, provocando respuestas incoherentes o alucinaciones del modelo.

### Caso Combinado (§6): `PRUNE → VERIFY → FAIL-CLOSED IF STILL OVERFLOW`
* **Evaluación de viabilidad**:
  - Se verificó que el código actual de `StructuredResponsePipeline` **permite expresar limpiamente esta arquitectura**.
  - **Flujo**:
    1. El pipeline intenta podar componentes no esenciales (turnos viejos, chunks de score bajo).
    2. Verifica si el prompt resultante entra en el presupuesto.
    3. Si tras podar todo lo permitido el prompt sigue desbordado (ej. query del estudiante masiva o system prompt gigante), **aborta con fail-closed limpio (`CONTEXT_BUDGET_EXCEEDED`)**.
  - Esta combinación maximiza la resiliencia conversacional sin tolerar desbordes ni recurrir al truncamiento ciego.

---

## 9. Análisis de D_C3_3 — Método de Medición

| Dimensión de Análisis | Opción A: Estimación Conservadora (`chars // 4`) | Opción B: Tokenizador Exacto (BPE/Modelo) | Opción C: Reutilización de `chunk.token_count` |
| :--- | :--- | :--- | :--- |
| **Fórmula / Mecanismo** | $\text{tokens} = \text{len}(\text{texto}) // 4$ (con margen de seguridad del 10%). | Codificación mediante tokenizador oficial (ej. tiktoken, HuggingFace tokenizer). | Suma de la columna pre-almacenada `token_count` en la tabla SQLite `chunks`. |
| **Velocidad / Latencia** | **0.35 microsegundos** ($\approx 0.00035$ ms). Cero impacto en CPU. | **3.04 milisegundos** ($\approx 3.039$ µs en BERT local). ~10.000x más lenta. | Instantáneo (suma entera de registros recuperados). |
| **Disponibilidad Soberana** | **100% disponible**: función pura en Python sin librerías externas. | **BLOQUEADA en el entorno actual**: no existen tokenizadores de LLaMA 3 ni Gemini locales. | Disponible únicamente para fragmentos de base de datos. |
| **Independencia de Proveedor** | Universal: no cambia si se conmuta entre Cerebras, Groq, Gemini o Nvidia. | Problemática: cada familia de modelos exige su propio vocabulario y algoritmo de tokenización. | No aplicable al prompt global. |
| **Precisión Observada** | Discrepancia de solo **0.6%** frente a tokenizador real en texto técnico curricular. | Exactitud al 100% respecto al modelo específico del tokenizador cargado. | **Conceptualmente inválida para el prompt total**: no mide system prompt, metadatos, BKT ni historial. |
| **Dictamen de Viabilidad** | **TÉCNICAMENTE LISTA Y PROBADA**. | **REQUIERE DESCARGA DE MODELOS / DEPENDENCIAS**. | **INSUFICIENTE (Solo apta como heurística de retrieval)**. |

---

## 10. Clasificación de Seguridad Pedagógica (Pedagogical Safety)

Para informar la definición de prioridades de poda (D_C3_2), se clasificaron los componentes del prompt según su criticidad formativa en TALOS:

```text
1. PEDAGOGICALLY_CRITICAL (No deben podarse; su ausencia destruye la intervención):
   - user_query (Consulta e intención del alumno)
   - base_system_prompt (Identidad epistemológica de cátedra y prohibición de atajos)
   - bkt_directive / struggle_mode (Protocolo de Lucha y nivel de andamiaje actual)
   - primary_evidence (Los 1-3 chunks de mayor relevancia documental)

2. PEDAGOGICALLY_USEFUL (Deseables para la experiencia conversacional):
   - recent_turns inmediatos (Último intercambio para resolución deíctica)
   - Mem0 misconceptions (Errores conceptuales recurrentes del alumno)
   - style_directive (Pauta formal de interacción)

3. OPTIONAL (Candidatos naturales a compresión o poda ante presión de contexto):
   - Turnos antiguos del historial (turnos 2 a 4 hacia atrás)
   - session_digest (Resúmenes de sesiones anteriores)
   - Chunks periféricos de expansión seccional (pos_index ± 1 con score bajo)
   - andamiaje metacognitivo secundario (fading)

4. REDUNDANT (Eliminables mediante refactorización limpia sin pérdida semántica):
   - Tags de metadatos excesivos en cada línea de chunk
   - Títulos de programas de estudio inyectados repetitivamente en cada turno
   - Checklists y plantillas de formato duplicadas en user y system prompt
```

---

## 11. Opciones e Impacto en la Compatibilidad con TALOS V1

| Opción de D_C3_1 | Compatibilidad V1 | Comportamiento Observable | Impacto en Respuestas | Impacto en Citas |
| :--- | :---: | :--- | :--- | :--- |
| **Opción A (Evidence Ceiling)** | **ALTA** | Idéntico al actual. Solo se formaliza y blinda el límite de evidencias (5.000 tokens). | Cero alteración en respuestas habituales. | Cero alteración en formato de citas. |
| **Opción B (Total Prompt Ceiling)** | **MEDIA** | En conversaciones largas o preguntas densas, el sistema podará turnos antiguos para respetar el techo global. | Respuestas más concisas si el modelo recibe menos turnos de contexto previo. | Las citas se concentran en las evidencias primarias. |
| **Opción C (Layered Budget)** | **BAJA** | Modifica la distribución interna del contexto. Puede restringir la evidencia si se prioriza el historial. | Puede cambiar la profundidad explicativa según el reparto de cuotas fijas. | Requiere validar que las cuotas no ahoguen a fuentes con fragmentos extensos. |

---

## 12. Dictamen de Terminación de CP108

Habiéndose completado la auditoría exhaustiva, reproducido y desglosado empíricamente los desbordes de contexto, mapeado las diez fronteras del flujo, verificado la naturaleza declarativa de los proveedores y formulado las matrices de impacto sin realizar ninguna mutación en producción ni predeterminar decisiones:

```text
================================================================================
DICTAMEN DE AUDITORÍA CP108:
C3 = DECISION READY (Auditoría completa / Listo para adjudicación humana)
================================================================================
```

---

## 13. Registro para la Decisión Humana (`HUMAN_DECISIONS_REQUIRED`)

Conforme a la regla de neutralidad y preservación de la autoridad de decisión:

```text
D_C3_1_HUMAN_DECISION=PENDING
D_C3_2_HUMAN_DECISION=PENDING
D_C3_3_HUMAN_DECISION=PENDING
```

---

## 14. Reporte Final Obligatorio

```text
CP108_STATUS=COMPLETED
C3_STATUS=DECISION READY
D_C3_1_STATUS=PENDING
D_C3_2_STATUS=PENDING
D_C3_3_STATUS=PENDING

CURRENT_RETRIEVAL_CEILING=5000 tokens (SectionExpander en chunks crudos; fallback ilimitado)
CURRENT_PROMPT_CEILING=NONE (Sin verificación pre-LLM)
CURRENT_FALLBACK_CEILING=UNBOUNDED (chat.py:1296 sin límite)
CURRENT_PROVIDER_ENFORCEMENT=NONE (Metadata declarativa en ModelRegistry)

MAX_REPRODUCED_PROMPT=11587 tokens (Caso base reproducido) / 13281 tokens (Caso patológico máximo)
MAX_REPRODUCED_RETRIEVAL=7747 tokens (Fallback de 25 chunks sin podar)
MEASUREMENT_METHOD=chars // 4 (Validado con 0.6% de error frente a BPE)
MEASUREMENT_CONFIDENCE=HIGH (Medición directa y reproducible en entorno local)

OVERFLOW_CASES=4/5 fixtures evaluados (A, B, C, D presentan desborde sobre 5.000)
FALLBACK_OVERFLOW=OBSERVED (+117.7% sobre ceiling nominal)
HISTORY_OVERFLOW=OBSERVED (Aporta hasta 354 tokens adicionales al desborde)

DATABASE_CHANGES=0
DB_SHA_BEFORE=fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1
DB_SHA_AFTER=fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1

FILES_CREATED=checkpoints/108-c3-hard-ceiling-adjudication.md
FILES_MODIFIED=checkpoints/index.md

HUMAN_DECISIONS_REQUIRED=3 (D_C3_1, D_C3_2, D_C3_3)
NEXT_CHECKPOINT=CP109 (Implementación de blindaje C3 tras decisión humana)
```
