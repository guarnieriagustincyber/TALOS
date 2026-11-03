# CP103 — ARQUEOLOGÍA Y DIAGNÓSTICO ADVERSARIAL DE C3

## 1. Identidad y marco del diagnóstico

```text
CP = 103
GATE = B (Identidad y aislamiento curricular)
CRITERIA = C3 (Hard-ceiling de contexto)
DATE = 2026-10-02
ROL = Auditor técnico adversarial
METODOLOGÍA = OBSERVE → MEASURE → CORRELATE → CLASSIFY → DOCUMENT
ESTADO PREVIO = C3 = PARTIAL_EXISTING_EVIDENCE
DICTAMEN CP103 = C3 = BLOCKED / ASSURANCE_BLOCKER
PRECONDICIÓN ESTABLE = C1 = PASS (CP097), C2 = PASS (CP102)
CAMBIOS EN CÓDIGO DE PRODUCCIÓN = 0
CAMBIOS EN BASE DE DATOS = 0 (DATABASE_CHANGES = 0)
```

### 1.1 Invariante de aislamiento respecto de C2
La frontera L3 certificada en CP102 (81 `AUTHORIZED`, 1 `PENDING`, 17 `EXCLUDED`) se preserva intacta. No se modificó `config/l3_authorization_manifest.json`, `src/study_engine/contracts/l3_manifest.py`, ni ninguna regla de ACL.

### 1.2 Invariante de almacenamiento productivo
```bash
sha256sum data/web_state/knowledge_store.db
# fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1  data/web_state/knowledge_store.db
```
El archivo de base de datos permanece estrictamente inmutable (`DATABASE_CHANGES = 0`).

---

## 2. Definición operacional encontrada en el repositorio

El término "hard-ceiling" en TALOS proviene históricamente del commit `2fe70e3` y del ítem de backlog `BACKLOG-CTX-001` (`docs/audit_diagnostico.md:267`, `walkthrough.md:95`). En ese hito se implementó `HARD_CEILING_TOKENS` en `src/study_engine/retrieval/expansion.py` para prevenir picos de memoria RAM derivados de la expansión greedy de ventanas ($\pm 1$ chunk).

La documentación histórica y el código registran explícitamente:
> *"HARD_CEILING_TOKENS aplica únicamente a la evidencia de ENTRADA (ensamble pre-LLM en SectionExpander.expand_results(), expansion.py:116). No se suma ni comparte con el presupuesto de generación de SALIDA"* (`walkthrough.md:99`).

Sin embargo, a nivel de **Gate B / Product Complete (Criterio 3)**, la garantía requerida es:
> **"Hard-ceiling de contexto: El sistema garantiza físicamente que el contexto/prompt efectivo entregado al modelo jamás supera el techo delimitado."**

Existe una discrepancia conceptual entre:
1. **La definición histórica implementada:** un límite de poda local aplicado **exclusivamente a los chunks crudos de retrieval** en `SectionExpander`.
2. **La garantía contractual de C3:** un límite estricto sobre el **contexto total que entra al LLM**.

---

## 3. Flujo completo del contexto (Request → Provider)

Se auditó de extremo a extremo la ruta principal de chat (`/api/chat/query` en `src/study_engine/web/routes/chat.py` y `src/study_engine/pedagogy/structured_pipeline.py`):

```text
Request: ChatQueryRequest (prompt / query, recent_turns, session_id)
  ↓
[Paso 1] Intent & Granularity Routing (GranularityRouter.route)
  - MICRO (1800 target tokens, max 6 leaf chunks)
  - MACRO (2200 target tokens, max 2 parent summaries)
  - HYBRID (2000 target tokens, 1 parent summary + 3 leaf chunks)
  ↓
[Paso 2] Retrieval Depth (_resolve_retrieval_depth)
  - Debug: 8 chunks, >=2 fuentes
  - General: 15 chunks, >=3 fuentes
  - Broad: 25 chunks, >=4 fuentes
  ↓
[Paso 3] Hybrid / Keyword Search (store.search_hybrid / store.search)
  - Recupera lista search_results (hasta 25 candidatos)
  ↓
[Paso 4] Section Expansion (SectionExpander.expand_results)
  - Expande ventanas contiguas [pos - 1, pos + 1]
  - APLICA HARD_CEILING_TOKENS (1800 si debug, 5000 estándar)
  - Poda por relevancia si sum(chunk.token_count) > ceiling
  - Formatea con metadatos: [CHUNK X | Pág Y | Source]
  - Salida: (expanded_chunks, expanded_context_text)
  ↓
[Paso 5] Ensamblado Epistémico (_assemble_epistemic_context)
  - Si expanded_context_text está vacío: FALLBACK a "\n\n".join(citations_formatted) (SIN LÍMITE)
  - Añade catálogo de unidades del cuaderno (Programa Oficial)
  - Construye EpistemicContextPack(formatted_context=final_formatted)
  ↓
[Paso 6] Inyección de Directivas Pedagógicas y Memoria en chat.py
  - Directiva BKT adaptativa (p_L, intentos)
  - Protocolo de Lucha (si >=3 fallos consecutivos en el KC)
  - Directiva de Andamiaje Metacognitivo (fading de dependencia)
  - Directiva de Currículo en Espiral (profundización retroactiva)
  - Memoria Soberana de Largo Plazo (Mem0)
  - Resumen de sesión previa (maybe_inject_session_digest)
  - Historial conversacional reciente (conv_turns[-4:])
  - Bloque de perfil cognitivo dinámico
  ↓
[Paso 7] Construcción del Prompt de Fase (pipeline.build_phase_prompt)
  - Prepend: Base System Prompt de cátedra (~10.000 chars / ~2.500 tokens)
  - Predecessor phase context
  - Evidencias Documentadas Autorizadas (context_pack.formatted_context)
  - Historial de turnos recientes (hasta 4 turnos, truncados a 600 chars c/u)
  - Directiva de estilo y conversación (ConversationStyleRouter)
  - Instrucción de fase / Protocolo de continuación / Protocolo anti-atajo
  - Checklist de entidades técnicas obligatorias
  - Directivas de seguridad y Threat Intel
  - Identificadores no estándar
  - Entregables estructurales solicitados (C, Python, SQL, etc.)
  - Directivas BKT / Lucha / Scaffolding / Spiral / Mem0 acumuladas
  - Bloque cognitivo histórico
  - Directiva de tono y andamiaje emocional
  - Reglas de salida pedagógica (consigna de palabras de prosa)
  - Consulta textual del estudiante
  - Instrucciones de estrategia e intención
  ↓
[Paso 8] Adapter y Streaming Provider (pipeline._stream_tokens → provider.stream / complete)
  - Construye payload HTTP: messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}]
  - CERO verificación, CERO recorte, CERO ceiling en la frontera de red.
  ↓
Provider / Modelo (Groq, Cerebras, Gemini, Cloudflare, Ollama)
```

### Tabla de etapas del flujo:
| Etapa | Entrada | Transformación | Salida | ¿Puede aumentar contexto? | ¿Tiene límite? |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **Retrieval** | Query + Allowlist L3 | Búsqueda híbrida/SQL | Lista de `SearchResult` (8-25) | SÍ (hasta 25 chunks) | `retrieval_limit` (8, 15, 25) |
| **Expansion** | `SearchResult` seeds | Expansión greedy $\pm 1$ | `expanded_chunks` contiguos | **SÍ (hasta triplicar chunks)** | **SÍ: `HARD_CEILING_TOKENS` (5.000 / 1.800)** |
| **Formatting** | `expanded_chunks` | Concatenación de tags `[CHUNK ...]` | `expanded_context_text` | **SÍ (+2% a +55% por metadata)** | **NO** |
| **Fallback** | `search_results` | `citations_formatted` | `final_formatted` | **SÍ (si expansion vacía)** | **NO (0 límite)** |
| **Epistemic Pack** | `final_formatted` | Empaqueta en `EpistemicContextPack` | `context_pack` | SÍ (+ unidades de catálogo) | **NO** |
| **Directives & Memory** | `context_pack` + Stores | Inyecta BKT, Mem0, Lucha, Espiral, Sesión | `bkt_directive`, `conv_turns` | **SÍ (+500 a +2.000 tokens)** | **NO** |
| **Prompt Builder** | Directivas + ContextPack + Historial | Concatena 15 bloques en `build_phase_prompt` | `phase_user_prompt` | **SÍ (+2.000 a +6.000 tokens)** | **NO** |
| **System Prompt** | Contrato de cátedra | Perfil curricular + fase | `system_prompt` | **SÍ (~2.500 tokens fijos)** | **NO** |
| **Provider Adapter** | `system_prompt` + `user_prompt` | Serializa a JSON payload HTTP | `messages` JSON para API | NO | **NO (CERO pre-LLM guard)** |

---

## 4. Identificación de todas las unidades de medida

En el repositorio conviven cinco (5) unidades de medida no homogéneas:

| Unidad | Magnitud típica | Dónde se define | Componente que la aplica | Comportamiento |
| :--- | :---: | :--- | :--- | :--- |
| **Tokens (columna DB)** | 1 a 3.450 / chunk | Tabla SQLite `chunks.token_count` | `retrieval/expansion.py` | Estimado en ingesta (`words * 4/3`) |
| **Tokens (estimación chars/4)** | 500 a 15.000 | `chat.py:2191` | `_resolve_chat_backend` | `(sys_len + ctx_len + q_len) // 4` para enrutar tiers |
| **Caracteres** | 4.000 chars | `context/packer.py:22` | `ContextPacker.pack()` | `DEFAULT_MAX_CHARACTERS = 4000` (Hito 3) |
| **Palabras** | 200 a 1.200 palabras | `contracts/tutor.py`, `structured_pipeline.py` | Prompt instruction | Regla de prosa pedagógica ("hasta 400 palabras") |
| **Chunks** | 6 a 25 chunks | `granularity_router.py`, `chat.py` | Retrieval pool | Cardinalidad de registros recuperados |
| **Dólares (USD)** | \$1.00 / \$5.00 | `llm/quota_manager.py:184` | `BudgetCeilingManager` | Circuit breaker financiero por sesión/día |

**Hallazgo:** "Tokens" en `SectionExpander` se calcula como el valor pre-almacenado en la columna `chunks.token_count`. No se tokeniza el texto formateado final, no se miden los metadatos agregados, ni se utiliza un tokenizador real (tiktoken/BPE) en runtime.

---

## 5. Clasificación: HARD vs SOFT

Se evaluaron todos los límites identificados en el código:

| Límite (ID) | Valor | Unidad | Punto de Aplicación | Tipo | ¿Expansión posterior? |
| :--- | :---: | :---: | :--- | :---: | :---: |
| `HARD_CEILING_TOKENS` (Retrieval) | 5.000 | Tokens (chunks) | `SectionExpander.expand_results()` | **SOFT (respecto al LLM)** | **SÍ (Bypass 2 y 3)** |
| `HARD_CEILING_TOKENS` (Debug Q) | 1.800 | Tokens (chunks) | `chat.py:1212` | **SOFT (respecto al LLM)** | **SÍ (Bypass 2 y 3)** |
| `DEFAULT_MAX_CHARACTERS` | 4.000 | Caracteres | `ContextPacker.pack()` (Hito 3) | **SOFT (respecto al LLM)** | **SÍ (System prompt + History)** |
| `ContextCompiler.max_context_tokens` | 40.000 | Tokens | `context_compiler.py:31` | **DECLARATIVO (INACTIVO)** | N/A (parámetro ignorado) |
| `IntentRouter.max_context_tokens` | 0 - 40.000 | Tokens | `intent_router.py:88` | **DECLARATIVO (HUÉRFANO)** | N/A (no se llama en runtime) |
| `GranularityRouter.target_token_budget`| 1.800 - 2.200| Tokens | `granularity_router.py:31` | **INFORMATIVO** | N/A (chat.py no lo consulta) |
| `ResponseBudgetPolicy` | 200 - 1.200 | Tokens | `contracts/tutor.py` | **HARD (Salida LLM)** | NO (aplica a output) |
| `effective_max_tokens` | 800 - 3.500 | Tokens | `pipeline.generate_phased_response` | **HARD (Salida LLM)** | NO (parámetro `max_tokens` API) |
| Provider `max_context_tokens()` | 8K - 1M | Tokens | `abstract_provider.py` | **EXTERNO / HARD** | NO (falla con HTTP 400 si supera) |

---

## 6. Punto de verdad del prompt final

Se identificó el punto exacto donde se formula el payload antes de cruzar la frontera hacia el proveedor LLM:

* **Constructor del prompt final (`PROMPT_FINAL_BUILDER`):**
  `src/study_engine/pedagogy/structured_pipeline.py::StructuredResponsePipeline.build_phase_prompt` (líneas 1122–1462) y `StructuredResponsePipeline._stream_tokens` (líneas 1464–1530).

* **Consumidor del prompt final (`PROMPT_FINAL_CONSUMER`):**
  `src/study_engine/llm/backends.py::OpenAICompatibleBackend.stream` (línea 392):
  ```python
  messages = [
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": user_prompt},
  ]
  payload = {
      "model": self._default_model,
      "messages": messages,
      "max_tokens": max_tokens,
      "stream": True,
  }
  await client.stream("POST", url, headers=headers, json=payload)
  ```
  O `src/study_engine/llm/gemini_backend.py::GeminiBackend.stream` (línea 251).

**Demostración:** El objeto `payload["messages"]` es la estructura terminal. Entre `build_phase_prompt` y `client.stream("POST", ...)` **no existe ninguna función, middleware, guard ni interceptor que mida o acote el tamaño total del prompt**.

---

## 7. Resultados de pruebas y mediciones (Fixtures A–F)

Se ejecutaron pruebas sintéticas y sobre datos reales en `scratch/measure_c3_fixtures.py` y `scratch/adversarial_c3_test.py`:

### Fixture A — Contexto pequeño (< límite)
* **Entrada:** 1 chunk semilla de 77 tokens.
* **Comportamiento:** Expandido a 2 chunks contiguos (77 tokens, 317 caracteres en `formatted_context`).
* **Resultado:** `ACCEPTED` (se mantiene dentro de la cuota).

### Fixture B — Contexto exactamente en el límite
* **Entrada:** 4 chunks de 250 tokens cada uno = 1.000 tokens exactos vs `ceiling = 1000`.
* **Comportamiento:** `SectionExpander` evalúa `total_tokens > self.hard_ceiling_tokens` ($1000 > 1000 \to \text{False}$). No aplica poda.
* **Resultado:** `ACCEPTED` (el límite es inclusivo a nivel de suma de chunks).

### Fixture C — Contexto ligeramente superior (1.001 tokens)
* **Entrada:** 4 chunks de 250 tokens + 1 chunk de 1 token = 1.001 tokens vs `ceiling = 1000`.
* **Comportamiento:** `SectionExpander` detecta desborde ($1001 > 1000$). Ordena por relevancia y retiene los primeros 4 chunks (1.000 tokens). El chunk excedente de 1 token es descartado.
* **Resultado:** `TRUNCATED / BOUNDED` (la poda descarta el fragmento que supera el techo).

### Fixture D — Expansión posterior que supera el límite
* **Caso 1:** Conjunto de 20 semillas dispersas que sin techo generan 5.327 tokens. Bajo `ceiling = 2000`, `SectionExpander` poda a 8 chunks y 1.623 tokens.
* **Caso 2 (Fallo de límite unitario):** Una semilla única cuyo contenido individual supera el techo (ej. chunk de 1.200 tokens con `ceiling = 1000`).
  * En la primera iteración `curr_tokens + c.token_count <= ceiling` ($0 + 1200 \le 1000 \to \text{False}$).
  * `accumulated` queda vacío y `SectionExpander` retorna `([], "")`.
  * **Efecto colateral:** Provoca la activación inmediata de **Bypass 1** (fallback desprotegido en `chat.py`).

### Fixture E — Ensamblado posterior y sobrecosto de metadatos
* **Escenario:** Chunks crudos suman 2.500 tokens. Se formatean con tags canónicos `[CHUNK {pos} | Pág {page} | {title}]\n`.
* **Medición:**
  * Caracteres de contenido crudo: 3.750 chars.
  * Caracteres formateados: 5.839 chars.
  * **Sobrecosto de metadatos:** **+2.089 caracteres (+55.7%)**.
  * Ese sobrecosto **no se computa** dentro de `curr_tokens` en `SectionExpander`.

### Fixture F — Pipeline completo: Retrieval + Memoria + Directivas + System Prompt
* **Escenario de producción:** Retrieval en el techo formal de 5.000 tokens (`tokens_chunks = 4.829`) + perfil de cátedra + directivas BKT/Lucha/Mem0 + 4 turnos conversacionales previos.
* **Medición cuantitativa:**
  * `formatted_context` (evidencias): 19.500 chars (~4.875 tokens)
  * `system_prompt` (perfil canónico): 5.199 chars (~1.299 tokens)
  * Directivas pedagógicas + Memoria Mem0 + Historial: 5.415 chars (~1.353 tokens)
  * **TOTAL ENVIADO AL LLM:** **30.114 caracteres (~7.528 tokens)**
  * **Techo retrieval declarado:** 5.000 tokens
  * **Real entregado al modelo:** **7.528 tokens**
  * **Desborde neto:** **+2.528 tokens (+50.6%)**

---

## 8. Bypasses estructurales identificados

Se identificaron y verificaron materialmente tres (3) bypasses estructurales:

### Bypass 1: Fallback desprotegido en `chat.py` (`FALLBACK_CITATIONS_UNBOUNDED`)
* **Ubicación:** `src/study_engine/web/routes/chat.py:1296`:
  ```python
  if citations_formatted:
      final_formatted = expanded_context_text if expanded_context_text else "\n\n".join(citations_formatted)
  ```
* **Mecanismo:** Si `expanded_context_text` resulta vacío (debido a que el expander falló, a que la primera semilla excedía el techo, o a que no hay SQLite engine en el store), TALOS recurre a `"\n\n".join(citations_formatted)`.
* **Impacto:** `citations_formatted` concatena la totalidad de los `search_results` recuperados (hasta 25 chunks) **sin aplicar ningún límite de caracteres, tokens ni poda**. En prueba sintética con 15 chunks grandes se registraron **23.080 caracteres (~5.770 tokens)** inyectados directamente al prompt sin filtro.

### Bypass 2: Inflación por metadatos de sección (`TAG_INFLATION`)
* **Ubicación:** `src/study_engine/retrieval/expansion.py:213-214`:
  ```python
  tag = f"[CHUNK {c.pos_index} | Pág {c.page_start} | {c.source_title}]"
  formatted_lines.append(f"{tag}\n{c.content}\n")
  ```
* **Mecanismo:** El bucle de hard ceiling solo suma `c.token_count`. Posteriormente se inyecta el prefijo `tag`. Con fuentes de títulos largos o muchos chunks pequeños, los tags aumentan el volumen entre un 2.7% y un 55.7% por encima de lo medido por el ceiling.

### Bypass 3: Inyección post-techo en el Pipeline (`ZERO_PRE_LLM_PROMPT_GUARD`)
* **Ubicación:** `src/study_engine/pedagogy/structured_pipeline.py:1254–1462`.
* **Mecanismo:** El límite de 5.000 tokens se aplica en la etapa de retrieval. Posterior a esa etapa, `chat.py` y `StructuredResponsePipeline` concatenan:
  1. Base system prompt de cátedra (~1.300 tokens)
  2. Directivas BKT y Protocolo de Lucha
  3. Andamiaje metacognitivo
  4. Currículo en espiral
  5. Memoria soberana de largo plazo Mem0
  6. Resumen de sesión previa
  7. Historial reciente (hasta 4 turnos)
  8. Perfil cognitivo dinámico
  9. Reglas y plantillas pedagógicas
* **Impacto:** Con un contexto recuperado dentro del ceiling de 5.000 tokens, el prompt final entregado a la API del modelo alcanza **7.500 a 13.200 tokens**. No existe ningún límite global de prompt.

---

## 9. Inventario de proveedores y ventanas de contexto

| Proveedor | Modelo por defecto | Ventana declarada (`max_context_tokens`) | Límite TALOS configurado | Límite efectivo de prompt | Garantía propia de TALOS |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Cerebras** | `llama3.3-70b` | 131.072 tokens | 5.000 (retrieval) | **NINGUNO (Ilimitado hasta 131k)** | `NOT_PROVEN` |
| **Groq** | `llama-3.3-70b-versatile` | 131.072 tokens | 5.000 (retrieval) | **NINGUNO (Ilimitado hasta 131k)** | `NOT_PROVEN` |
| **Gemini** | `gemini-2.5-flash` | 1.048.576 tokens | 5.000 (retrieval) | **NINGUNO (Ilimitado hasta 1M)** | `NOT_PROVEN` |
| **Nvidia** | `meta/llama-3.3-70b-instruct` | 128.000 tokens | 5.000 (retrieval) | **NINGUNO (Ilimitado hasta 128k)** | `NOT_PROVEN` |
| **Cloudflare**| `@cf/meta/llama-3.1-8b-instruct`| 8.192 tokens | 5.000 (retrieval) | **NINGUNO (Ilimitado hasta 8k)** | `NOT_PROVEN` |
| **Ollama** | `qwen2.5-coder:7b` / `2b` | 32.768 tokens | 5.000 (retrieval) | **NINGUNO (Ilimitado hasta 32k)** | `NOT_PROVEN` |

**Conclusión:** TALOS **no garantiza su propio ceiling** de manera independiente a la ventana del proveedor. Si el prompt acumulado desborda los 5.000 tokens, simplemente se transmite al modelo, dependiendo enteramente de que la ventana del proveedor externo (128K o 1M) absorba el exceso sin rebotar con un error 400. En proveedores con ventanas ajustadas (ej. Cloudflare 8K o capa gratuita de Groq con 7.000 tokens por minuto), este desborde arriesga fallos de servicio.

---

## 10. Rutas alternativas auditadas

Se auditaron todas las rutas que generan contexto o invocan modelos en `src/`:

| Ruta / Componente | Origen del contexto | ¿Aplica ceiling de retrieval? | Límite de prompt final | Estado C3 |
| :--- | :--- | :---: | :---: | :---: |
| **Chat SSE** (`/api/chat/query`) | SQLite Search + Expander | SÍ (`SectionExpander`, 5.000) | **NO TIENE** | `BLOCKED` |
| **Chat SSE Fallback** (`chat.py:1296`) | `search_results` directos | **NO** | **NO TIENE** | `BLOCKED` |
| **FastPath** (`fastpath_service.py`) | Metadata de cuaderno/KC | N/A (sin corpus) | Acotado (<300 tokens) | `PASS_DEF` |
| **Session Orchestrator** (`session/orchestrator.py`) | `ContextPacker` (Hito 3) | SÍ (4.000 chars) | **NO TIENE (post-policy)** | `BLOCKED` |
| **Query Rewriter** (`query_rewriter.py`) | Historial técnico (300 chars) | N/A | Acotado (<200 tokens) | `PASS_DEF` |
| **Memory Extractor** (`memory_extractor.py`) | Turno de usuario (400 chars) | N/A | Acotado (<300 tokens) | `PASS_DEF` |
| **Local Orchestrator** (`local_orchestrator.py`) | Títulos de nodos | N/A | Acotado (<200 tokens) | `PASS_DEF` |
| **Evidence Decomposer** (`decomposer.py`) | Consulta del usuario | N/A | Acotado (<200 tokens) | `PASS_DEF` |
| **Exercise Generators** (`student_exercises.py`) | Catálogo de KCs | N/A (Algorítmico) | N/A (Sin LLM) | `NOT_APPLICABLE` |

---

## 11. Estado de memoria (Mem0, BKT y Sesión)

La memoria interactúa directamente con el presupuesto de contexto:
1. **Mem0 (Memoria soberana de largo plazo):** Ensambla directivas en `mem0.assemble_long_term_directive` o `PedagogicalMemoryTracker.format_tutor_directive` (hasta 3 memorias previas).
2. **Short-Term Memory (`recent_turns`):** Recupera turnos previos de `_CONV_TURN_BUFFER`. Trunca cada mensaje a 600 caracteres (o 1.200 en modo continuación). En un intercambio de 4 turnos, aporta hasta **2.400 caracteres (~600 tokens)**.
3. **Session Digest:** Inyecta resúmenes de turnos previos.
4. **BKT & Scaffolding:** Inyectan directivas de andamiaje, estado de maestría y advertencias de lucha.

**Veredicto sobre memoria:** Todos estos componentes se inyectan **después** de que `SectionExpander` aplicó su límite. Ninguno se descuenta del presupuesto de 5.000 tokens ni cuenta con un sub-presupuesto coordinado.

---

## 12. Evidencia concluyente de Overrun

```text
================================================================================
EVIDENCIA DE OVERRUN OBSERVADO:
DECLARED CEILING (retrieval) = 5.000 tokens
ACTUAL PROMPT SENT TO MODEL  = 7.528 - 13.281 tokens
NET OVERRUN                  = +50.6% a +165.6%
================================================================================
C3_BYPASS = OBSERVED
```

Se verificó reproduciblemente en los scripts de auditoría que:
1. Con un conjunto de chunks que respeta estrictamente el límite de 5.000 tokens en `SectionExpander`, el modelo recibe más de **7.500 tokens**.
2. Si el expander falla o retorna vacío, el fallback inyecta chunks sin límite alguno.
3. El sistema carece de un hard-ceiling pre-LLM integral.

---

## 13. Evidencia faltante para certificar C3

Para que C3 pueda transicionar hacia `ASSURANCE_READY` y eventualmente `PASS`, se requiere:

1. **Definición contractual y normativa única de C3:** Determinar el perímetro exacto del techo (retrieval vs prompt total) mediante decisión humana.
2. **Punto de control físico Pre-LLM (Nivel 4 Defense in Depth):** Implementar un interceptor o validador terminal inmediatamente antes de llamar a `provider.stream` / `provider.complete` que garantice:
   $$\text{tokens}(\text{system\_prompt} + \text{user\_prompt}) \le \text{PROMPT\_HARD\_CEILING}$$
3. **Mecanismo determinista de poda de desborde:** Establecer qué componentes se comprimen o recortan si el prompt total excede el techo (ej. recortar turnos antiguos, podar chunks periféricos, etc.).
4. **Blindaje de la ruta de fallback:** Aplicar el mismo techo a `citations_formatted` en `chat.py`.
5. **Suite de regresión adversarial:** Demostrar formalmente que bajo ninguna combinación de parámetros el payload enviado al proveedor supera la cuota establecida.

---

## 14. Decisiones humanas requeridas (`HUMAN_DECISIONS_REQUIRED`)

Conforme a las reglas de Gate B, estas definiciones no deben asumirse técnicamente, sino someterse a adjudicación del propietario:

```text
HUMAN_DECISIONS_REQUIRED = [
    {
        "decision_id": "D_C3_1",
        "description": "Perímetro formal del Hard-Ceiling",
        "options": [
            "A: Techo sobre Evidencia de Entrada (retrieval context pack únicamente, ej. 5.000 tokens)",
            "B: Techo sobre Prompt Total (system_prompt + user_prompt + memoria + evidencias, ej. 8.000 tokens)",
            "C: Techo desacoplado por componentes (ej. 4.000 evidencia + 2.000 directivas/turnos + 2.000 sistema = 8.000 total)"
        ]
    },
    {
        "decision_id": "D_C3_2",
        "description": "Política de mitigación ante desborde en el límite pre-LLM",
        "options": [
            "A: Poda jerárquica determinista (1º turnos viejos -> 2º directivas opcionales -> 3º chunks de menor score)",
            "B: Fail-Closed con abstención explícita ('CONTEXT_BUDGET_EXCEEDED')",
            "C: Truncamiento ciego del tail de contexto"
        ]
    },
    {
        "decision_id": "D_C3_3",
        "description": "Unidad de medida normativa para C3",
        "options": [
            "A: Conteo estimado estándar (chars // 4) con factor de seguridad",
            "B: Tokenizador BPE exacto (tiktoken cl100k_base / o200k_base)",
            "C: Suma de token_count reportado por base de datos SQLite"
        ]
    }
]
```

---

## 15. Clasificación final de C3

Habiéndose demostrado la existencia de bypasses materiales (`C3_BYPASS = OBSERVED`) y la ausencia de un guard pre-LLM físico para el prompt completo:

```text
================================================================================
CLASIFICACIÓN DE GATE B — CRITERIO 3:
C3 = BLOCKED / ASSURANCE_BLOCKER
================================================================================
```

---

## 16. Estado consolidado de Gate B

```text
C1 (IDs / aliases / curriculum_id) = PASS / CLOSED              (Certificado en CP097)
C2 (Roles de fuente y ACL efectiva) = PASS / CLOSED              (Certificado en CP102)
C3 (Hard-ceiling de contexto)       = BLOCKED / ASSURANCE_BLOCKER (Diagnosticado en CP103)
C4 (Aislamiento cross-curriculum)   = PARTIAL_EXISTING_EVIDENCE  (Assurance pendiente)
C5 (Gate de abstención y confianza) = BLOCKED / ASSURANCE_BLOCKER
```
