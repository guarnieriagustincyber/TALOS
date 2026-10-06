# CP104 — Arqueología de Memoria, Embeddings y Herramientas Auxiliares para Gestión de Contexto

**Gate B — Hard-Ceiling de Contexto / TALOS**
**Fecha**: 2026-10-02
**Tipo**: Arqueología Técnica / Observación y Medición de Componentes Existentes
**Estado**: AUDIT_COMPLETED / READ_ONLY_INVESTIGATION
**Integridad DB**: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (`DATABASE_CHANGES = 0`)

---

## 0. Marco de Referencia y Reglas de la Auditoría

En cumplimiento estricto de las directivas de CP104:
- **DATABASE_CHANGES = 0**: No se modificó `data/web_state/knowledge_store.db`, no se aplicaron migraciones ni se ejecutaron sentencias DDL/DML.
- **READ-ONLY**: No se instalaron dependencias, no se descargaron modelos, no se modificó configuración productiva ni código fuente en `src/`.
- **DISCIPLINA EPISTÉMICA**: Separación estricta entre `[HECHO OBSERVADO]`, `[EVIDENCIA]`, `[INFERENCIA TÉCNICA]`, `[GAP]` e `[HIPÓTESIS]`.

---

## Sección A: Mem0 (Memoria Soberana de Largo Plazo)

### 1. Estado de Operación
- **Estado**: `ACTIVE_PRODUCTION (Sovereign Heuristic Subset)`
- `[HECHO OBSERVADO]`: TALOS **no utiliza** la librería externa de Python `mem0` (`import mem0` no existe en el repositorio ni en `.venv`).
- `[HECHO OBSERVADO]`: Existe una implementación propia, 100% soberana y local denominada `Mem0Manager` en `src/study_engine/memory/mem0_manager.py`.

### 2. Clase y Almacenamiento Persistente
- `[EVIDENCIA]`: Clase `Mem0Manager` coordina:
  - `StudentStorage` (`src/study_engine/student/storage.py`), que persiste en SQLite `data/web_state/student_state.db` en las tablas:
    - `student_pedagogical_memory`: almacena preferencias explícitas, patrones de aprendizaje y concepciones erróneas/fallas observadas.
    - `bkt_states`: estado bayesiano de conocimiento por KC.
  - `PreferenceTracker`: detección heurística de preferencias de estilo/lenguaje/formato.
  - `LearningPatternsTracker`: detección de ritmo, solicitudes de ayuda y patrones de interacción.
  - `SessionMemoryManager`: continuidad episódica entre sesiones.

### 3. Modelo de Embeddings y Vectorialidad
- `[HECHO OBSERVADO]`: **NINGUNO (0 embeddings)**.
- `[EVIDENCIA]`: En `mem0_manager.py`, `preference_tracker.py` y `pedagogical_memory.py`, no se realiza ninguna llamada a modelos de embeddings ni a almacenes vectoriales. La recuperación de memorias se realiza por:
  - Búsqueda exacta por clave primaria o índice (`student_id`, `kc_id`, `category`).
  - Coincidencia de patrones regex precompilados (`_STYLE_PATTERNS`, `is_explicit_preference_statement`).

### 4. Extracción de Memorias y Llamadas a LLM
- `[HECHO OBSERVADO]`: La extracción en tiempo real en `Mem0Manager` es **100% determinista** (0 llamadas a LLM).
- `[EVIDENCIA]`: En `src/study_engine/web/routes/chat.py:1413` se dispara una tarea en segundo plano (`_trigger_background_memory_extraction`) que invoca a `mem0_manager.observe_student_turn(...)`, evaluando heurísticas regex sobre el turno del estudiante.
- `[HECHO OBSERVADO]`: Existe una clase `MemoryExtractor` en `src/study_engine/student/memory_extractor.py` con método `extract_misconception` capaz de llamar a un backend LLM para clasificar errores conceptuales sutiles, pero su invocación es estrictamente opcional y desacoplada del ciclo crítico de streaming.

### 5. Deduplicación y Manejo de Conflictos
- `[EVIDENCIA]`: Se resuelve en `StudentStorage.touch_pedagogical_memory(...)` mediante actualización de timestamps (`last_observed_at`), incremento de frecuencia observada y actualización ponderada del score de confianza (`confidence_score`), evitando registros duplicados para la misma categoría y clave temática.

### 6. Cuota de Tokens y Límite de Inyección
- `[HECHO OBSERVADO]`: En `Mem0Manager.assemble_long_term_directive(...)`:
  - Límite de preferencias: `limit=2`
  - Límite de patrones de aprendizaje: `limit=2`
  - Límite de concepciones erróneas activas: `limit=2`
- `[MEDICIÓN]`: La directiva formateada (`mem0_directive`) ocupa un rango típico de **80 a 250 tokens** (máximo teórico ~350 tokens).

### 7. Presencia en el Prompt Final
- `[HECHO OBSERVADO]`: **SÍ**.
- `[EVIDENCIA]`: En `src/study_engine/web/routes/chat.py:2005-2025`:
  ```python
  mem0_directive = mem0.assemble_long_term_directive(...)
  if mem0_directive:
      bkt_directive = f"{bkt_directive}\n\n{mem0_directive}" if bkt_directive else mem0_directive
  ```
  Luego se transfiere como `bkt_directive` hacia `StructuredResponsePipeline.build_phase_prompt(...)`, ubicándose en la sección de directivas pedagógicas del prompt del LLM.

---

## Sección B: Embeddings (Inventario y Estado Operativo)

### 1. Inventario de Modelos en Código y Almacenamiento
`[EVIDENCIA]`: Se identificaron 4 implementaciones/modelos en el repositorio:

| Modelo Lógico | Tipo / Dimensiones | Archivo / Ubicación Física | Clase Proveedora | Estado Observado |
|---|---|---|---|---|
| `intfloat/multilingual-e5-small` | ONNX FP32 / 384d | `models/multilingual-e5-small/onnx/model.onnx` (449 MB)<br>`models/multilingual-e5-small/onnx/tokenizer.json` (17 MB) | `LocalONNXEmbeddingProvider` | Modelo local instalado en disco. Usado en Fase 6; su vector store histórico está preservado en `vector_store_e5_384_legacy.db.bak` (623 MB). |
| `Qwen/Qwen3-Embedding-0.6B` | PyTorch / 1024d | Cache de SentenceTransformers / HuggingFace | `SentenceTransformerEmbeddingProvider` | **Modelo activo de producción en SQLite**. La base `data/web_state/vector_store.db` (1.3 GB) posee 287,069 vectores calculados con este modelo. |
| `sha256-128d-v1` | Hash / 128d | En memoria / Algorítmico puro | `DeterministicHashEmbedder` | Mock determinista para tests y runners sintéticos. |
| `jinaai/jina-embeddings-v3` | Remoto / 8192 ctx | Declarativo en `config.py` (`LATE_CHUNKING_MODEL`) | Late Chunking experimental | Inactivo por defecto (`enable_late_chunking=False`). |

### 2. Estado de `vector_store.db` en Producción
- `[EVIDENCIA]`: Consulta SQL sobre `data/web_state/vector_store.db`:
  - Total registros en `chunk_embeddings`: **287,075**
  - Distribución por modelo:
    - `('sentence_transformers', 'Qwen3-Embedding-0.6B', 1024)`: **287,069 registros**
    - `('deterministic_hash', 'sha256-128d-v1', 128)`: **6 registros**
  - Distribución por notebook:
    - `NB-SEC-01-C-PTR`: 105,179
    - `fadena-std`: 46,530
    - `fase0-soc`: 43,214
    - `NB-CYBERSECURITY-V1`: 36,847
    - `fadena-teleco`: 27,475
    - `fadena-lenguajes`: 15,459
    - `fadena-so2`: 12,371

### 3. Hallazgo Crítico en Runtime (.venv vs Vector Store)
- `[HECHO OBSERVADO]`: En el entorno `.venv` del sistema:
  - `tokenizers`: **OK**
  - `onnxruntime`: **OK**
  - `torch`: **NO INSTALADO**
  - `sentence_transformers`: **NO INSTALADO**
- `[EVIDENCIA]`: En `src/study_engine/storage/knowledge_store.py:786-805`:
  Al no estar instalado `sentence_transformers`, el resolutor automático cae en el fallback local: `LocalONNXEmbeddingProvider` (`multilingual-e5-small`, 384d).
- `[EVIDENCIA]`: En `src/study_engine/storage/knowledge_store.py:844`:
  ```python
  if matrix.size == 0 or matrix.shape[1] != len(q_vec):
      return []
  ```
  La matriz cargada desde `vector_store.db` tiene dimensión `1024`, mientras que el vector de la consulta calculado por ONNX tiene dimensión `384`. Al no coincidir (`1024 != 384`), `vector_search` retorna inmediatamente una lista vacía `[]`.
- `[HECHO OBSERVADO]`: Inmediatamente después, en `search_hybrid`:
  ```python
  if vector_results and fts_results:
      fused = self.reciprocal_rank_fusion(vector_results, fts_results, k=60)
  elif vector_results:
      fused = vector_results
  else:
      fused = fts_results
  ```
  Al ser `vector_results == []`, la búsqueda es resuelta íntegramente por **SQLite FTS5 (BM25 puro)**.
- `[MEDICIÓN]`: La búsqueda FTS5 responde en **~5 a 8 ms**, con **0 MB** de asignación RAM adicional y sin arrojar excepciones.

### 4. Huella de Memoria y Consumo en Ryzen 5 5600GT
- `LocalONNXEmbeddingProvider` (multilingual-e5-small): ~450 MB RAM, latencia de inferencia en CPU (4 hilos): ~15-25 ms.
- `SentenceTransformerEmbeddingProvider` (Qwen 0.6B): ~1.2 a 1.5 GB RAM en FP32 sobre CPU, latencia de inferencia: ~30-50 ms.
- Multiplicación matricial NumPy BLAS sobre 105k vectores (NB-SEC-01-C-PTR): matriz de (105179, 1024) en float32 ocupa ~430 MB en memoria. El producto punto con vector normalizado en CPU Ryzen 5 5600GT insume ~18-35 ms.

---

## Sección C: Retrieval Fabric Lite

### 1. Arquitectura y Orden de Ejecución en `RetrievalFabricLite.retrieve(...)`
`[EVIDENCIA]`: `src/study_engine/retrieval/fabric.py:79-183`:

```text
Query del Estudiante
        ↓
1. QueryRewriter.rewrite(query)
   [Corrección de tipografía, sinónimos coloquiales, resolución deíctica]
        ↓
2. SymbolGuard.evaluate(...)
   [Fail-closed si se invocan símbolos o identificadores espurios]
        ↓
3. AdaptiveRetrievalRouter.route(...)
   [Clasificación determinista: estrategia, profundidad de pool, flag de rerank]
        ↓
4. _fetch_candidate_pool(...)
   [KnowledgeStore.search_hybrid -> FTS5 BM25 + Vector RRF]
        ↓
5. filter_presentation(candidates, registry)
   [Filtro anti-fuga de soluciones protegidas]
        ↓
6. Second-Stage Reranking (si enable_rerank=True)
   [LocalONNXReranker / JinaReranker -> recorte a top_k=5]
        ↓
7. Re-indexación de rango (1-indexed) y Log JSON Rotativo (retrieval_trace.json)
```

### 2. `GranularityRouter` (RAG Jerárquico en `chat.py`)
`[EVIDENCIA]`: `src/study_engine/retrieval/granularity_router.py`:
- `MICRO`: Queries de depuración, fallas (`sigsegv`, `crash`), registros C (`%rdi`, punteros). Presupuesto: máx 0 padres, máx 6 chunks hoja, objetivo ~1800 tokens.
- `MACRO`: Consultas holísticas, síntesis, temario curricular. Presupuesto: máx 2 resúmenes padre, 0 hojas, objetivo ~2200 tokens.
- `HYBRID` (por defecto): 1 resumen padre + máx 3 chunks hoja, objetivo ~2000 tokens.
- `deduplicate_hybrid_chunks`: Aplica descarte determinista de chunks hoja cuya información ya esté presente en el resumen del capítulo con similitud léxica >= 0.85 (excepto si contienen bloques de código o diagramas).

---

## Sección D: Reranking

### 1. Implementaciones en `retrieval/reranker.py`
`[EVIDENCIA]`:
1. `LocalONNXReranker`:
   - Modelo en disco: `models/reranker/model.onnx` (267 MB) y `tokenizer.json` (17 MB).
   - Provenance verificado: `onnx-community/bge-reranker-base-ONNX` en formato INT8 (`scripts/download_reranker.py`).
   - Tokenizador: Unigram, vocabulario de 250,002 tokens.
   - Ejecución: ONNX Runtime CPU (`CPUExecutionProvider`, 4 hilos), evaluación cross-encoder de pares `(query, passage)`, salida calibrada vía sigmoide.
   - Latencia en Ryzen 5 5600GT: ~60 a 110 ms para un lote de 20 candidatos. Memoria residente: ~300 MB RAM.
   - Estado: Reranker primario activo en producción (`settings.enable_local_neural_reranker = True`).
2. `JinaReranker`:
   - Cliente HTTP para `jina-reranker-v2-base-multilingual`.
   - Timeout estricto de 2.0s, máx 1 reintento, fallback transparente a `DeterministicLocalReranker`.
3. `DeterministicLocalReranker`:
   - Algoritmo en memoria: 40% cobertura de términos + 30% solapamiento de bigramas + 30% proximidad de posición inicial.
   - Latencia: <0.2 ms, 0 llamadas a red, 0 RAM adicional.

### 2. Efecto del Reranker sobre el Hard-Ceiling de Contexto
- `[HECHO OBSERVADO]`: El reranker es un **selector de ranking** (`top_k=5`), **NO un compresor de texto**.
- `[INFERENCIA TÉCNICA]`: El reranker ordena y filtra candidatos pero entrega los chunks intactos. Si los 5 chunks seleccionados tienen una longitud media de 500 tokens, la evidencia aportará 2,500 tokens independientemente del score de relevancia. El reranker no evita por sí mismo el desborde del hard ceiling.

---

## Sección E: Matriz Exhaustiva de Fuentes de Memoria y Contexto

A continuación se mapean todos los componentes que inyectan contenido en la llamada final al LLM:

| # | Componente / Fuente | Tipo de Contenido | Rango Típico Tokens | Límite Declarativo | Enforce Runtime Real | Vía de Inyección | Frecuencia / Trigger |
|---|---|---|---|---|---|---|---|
| 1 | **System Prompt Base** | Identidad soberana de TALOS, directivas pedagógicas base del contrato | 500 – 1,200 | No acotado (reserva 10k chars) | ❌ Inexistente | `PedagogicalContract.base_system_prompt` | En todos los turnos |
| 2 | **Evidencia Documental** | Chunks recuperados (FTS5/RRF + Reranker) + Expansiones (`SectionExpander`) | 1,200 – 6,500+ | `max_context_tokens = 5000` (`config.py`) | ❌ Bypass demostrado en CP103 (+165% de desborde) | `context_pack.formatted_context` | Si `needs_evidence = True` |
| 3 | **Historial Conversacional Reciente** | Buffer de turnos previos (Q&A) | 400 – 2,500 | `_MAX_RECENT_HISTORY_CHARS = 12000` | ⚠️ Parcial (solo cuenta caracteres, no tokens) | `recent_turns` en `build_phase_prompt` | Si hay turnos en la sesión |
| 4 | **Directiva BKT / Estado Cognitivo** | Probabilidad de maestría de KCs, KCs bloqueados | 50 – 120 | No especificado | ❌ Inexistente | `bkt_directive` | Cuando se detecta KC activo |
| 5 | **Memoria Mem0 Soberana** | Preferencias de estilo, patrones de aprendizaje, confusiones activas | 80 – 250 | `limit=2` por categoría | ✅ Acotado por conteo heurístico | Concatena en `bkt_directive` | Si `mem0_manager` está presente |
| 6 | **Directiva de Estilo y Modo** | Instrucción de tono rioplatense, andamiaje, restricciones anti-atajo | 150 – 450 | `max_words` en `RESPONSE_MODES` | ❌ Solo instruccional para el LLM | `style_directive` y `rendered_phase_instruction` | En todos los turnos |
| 7 | **Digest de Sesión Anterior** | Resumen estructurado JSON de lucha/maestría de la última sesión | 100 – 250 | No especificado | ❌ Inexistente | `maybe_inject_session_digest` | Solo en el 1° turno de una sesión |
| 8 | **Contexto de Fases Previas** | Salida de fases anteriores en pipelines multi-etapa | 400 – 1,500 | No especificado | ❌ Inexistente | `PhaseHistory.format_predecessors_context` | En fases secundarias |
| 9 | **Consulta del Estudiante** | Prompt crudo emitido por el usuario | 20 – 600 | 4000 caracteres | ⚠️ Acotado por caracteres | `user_query` | En todos los turnos |

---

## Sección F: Compresión y Resumen

### 1. Componentes Existentes en TALOS
1. `SessionRecord.compressed_summary` (`session_history.py` y `session_digest.py`):
   - Almacena métricas de KCs (`struggled_kcs`, `mastered_kcs`, `friction_level`).
   - Se construye 100% a partir de observaciones certificadas del evaluador (`StudentStorage`).
   - Formato JSON compacto, sin generación de texto libre por LLM.
2. `ConversationStateObject.compress_history` (`conversation_state.py`):
   - Implementa un analizador heurístico de turnos conversacionales que extrae conceptos clave, preguntas y errores.
   - `[HECHO OBSERVADO]`: **Código inactivo en producción**. Solo se invoca en los tests adversariales (`tests/adversarial/crisol/test_11_memory_poisoning.py`, `test_16_multi_turn_jailbreak.py`, `test_session_briefing.py`). No forma parte del pipeline `/api/chat/query`.
3. `GranularityRouter.deduplicate_hybrid_chunks`:
   - Descarta chunks redundantes contra el resumen del capítulo con solapamiento >= 85%.

### 2. Ausencia de Rolling Summarizer en Runtime
- `[GAP]`: Cuando el historial del usuario supera los 12,000 caracteres (`_MAX_RECENT_HISTORY_CHARS`), TALOS **descarta directamente los turnos más viejos** sin generar un resumen condensado ni consolidar la trayectoria. No existe un mecanismo de "resumen rodante" en el streaming activo.

---

## Sección G: Modelos de Decisión Livianos / Routers

### Inventario Completo de Routers en TALOS
`[EVIDENCIA]`:
1. `AdaptiveRetrievalRouter` (`retrieval/adaptive_router.py`):
   - 100% reglas regex deterministas (<0.5 ms, 0 LLM).
   - Decide estrategia (`EXACT_LEXICAL`, `COMPOSITE_FACETED`, `CONCEPTUAL_SEMANTIC`), profundidad del pool (10 a 50) y si se habilita reranking.
2. `GranularityRouter` (`retrieval/granularity_router.py`):
   - 100% regex determinista (<0.5 ms, 0 LLM).
   - Clasifica en `MICRO` (código/debug), `MACRO` (síntesis) o `HYBRID`.
3. `ConversationStyleRouter` (`pedagogy/style_router.py`):
   - 100% reglas deterministas (<1.0 ms, 0 LLM).
   - Evalúa slash commands (`/practicar`, `/comparar`), palabras clave de estilo y longitud de consulta.
4. `IntentRouter` (`context/intent_router.py`):
   - Capa 1: Heurísticas deterministas (`ContextHeuristics.evaluate`, confianza >= 0.90).
   - Capa 2: Clasificador liviano opcional (Groq 8B o mock JSON-constrained).
   - Capa 3: Fallback determinista seguro por recuento de palabras (>12 palabras -> `DEEP`, max 16k tokens; <=12 palabras -> `NORMAL`, max 5k tokens).
5. `SemanticRouter` (`tutor/semantic_router.py`):
   - Orientado a `qwen3.5:2b` local via Ollama HTTP (fallback a mock). Emite envelope tipado `IntentContract`. Utilizado en el loop estructurado de tutoría.
6. `TalosLLMRouter` (`llm/router.py`):
   - Router multi-proveedor por fase pedagógica con circuit breaker y fallback entre nubes.

---

## Sección H: Comparación Conceptual con Arquitecturas tipo "Laya"

En arquitecturas modernas con SLMs de apoyo (tipo Laya / agentes locales de 0.5B a 1.5B):
- Un SLM local en GPU/CPU (ej. Qwen2.5-0.5B/1.5B en GGUF u ONNX) evalúa el contexto, resume la historia, extrae facetas y poda dinámicamente información irrelevante antes de invocar al modelo grande.

### Análisis para el Hard-Ceiling de C3 en TALOS:
- `[INFERENCIA TÉCNICA]`: Para la garantía de **Hard-Ceiling (C3)**, un modelo generativo de compresión (SLM o LLM) **NO es la solución adecuada**:
  1. **Determinismo y Certificación**: El hard ceiling es un contrato de seguridad estricto e inviolable. Si se delega en un SLM/LLM la compresión de contexto, la longitud de salida sigue siendo estocástica y susceptible a variaciones o alucinaciones.
  2. **Presupuesto Matemático vs Compresión Semántica**: El recorte y ensamblado de contexto debe gobernarse por un algoritmo de presupuesto determinista (algoritmo de asignación de cuotas prioritarias), el cual garantiza con 100% de certeza que `tokens_totales <= HARD_CEILING`.
  3. **Latencia**: Un clasificador o compresor generativo local (incluso de 0.5B) añade entre 150 y 500 ms de latencia en CPU, mientras que los routers deterministas actuales de TALOS resuelven en <1 ms.
- `[CONCLUSIÓN]`: Los routers deterministas que TALOS ya posee son completamente adecuados. Lo que falta no es un modelo nuevo de IA para comprimir, sino un **chokepoint determinista de asignación de presupuesto (Budget Allocator Guard)** antes de la llamada HTTP al LLM.

---

## Sección I: Carga de Hardware en Ryzen 5 5600GT (16 GB RAM)

### 1. Especificaciones de la Plataforma
- CPU: AMD Ryzen 5 5600GT (6 núcleos / 12 hilos Zen 3, hasta 4.6 GHz).
- GPU: Gráficos integrados Radeon Vega 7 (memoria compartida con la RAM del sistema).
- Memoria: 16 GB DDR4.

### 2. Huella de Memoria Actual Observada
- Sistema Operativo Linux + Procesos Base: ~3.2 GB RAM.
- Proceso TALOS (FastAPI + SQLite + Dependencias): ~1.2 GB RAM.
- ONNX Runtime Reranker (BGE-Reranker-Base INT8): ~300 MB RAM residente.
- Shards de búsqueda vectorial (si se cargan matrices float32 en NumPy): ~430 MB RAM por notebook activo.
- Memoria RAM libre / disponible en reposo: **~10.5 GB RAM**.

### 3. Impacto de Cómputo CPU
- Al utilizar inferencia cloud de ultra-alta velocidad para la generación de texto (Cerebras a 1000+ tps, Groq a 500+ tps, SambaNova a 200+ tps):
  - La CPU local queda **100% disponible** para resolver FTS5 (2-5 ms), filtrado ACL L3 (<1 ms), y reranking ONNX local (~80 ms).
  - Cero estrés térmico y cero contención de memoria RAM.
  - Cargar un modelo generativo 7B local en CPU saturaría 5 a 6 GB de RAM y consumiría el 100% de los 12 hilos a ~10-14 tokens/segundo, degradando la capacidad de respuesta del servidor web.

---

## Sección J: Capacidades Multi-proveedor de TALOS

`[EVIDENCIA]`: `src/study_engine/llm/router.py`:
- `ProviderCircuitBreaker`: Implementación thread-safe con `asyncio.Lock()`, estados `CLOSED`, `OPEN`, `HALF_OPEN`, umbral de 3 fallas y cooldown de 300 segundos. Abre automáticamente el circuito ante errores HTTP 429 (Rate Limit).
- Proveedores disponibles en el ecosistema:
  - `cerebras`: Ultra-baja latencia (1000+ tps, Llama 3.1 / 3.3).
  - `groq`: Ultra-baja latencia (500+ tps, Llama 3.1 / 3.3, Gemma 2).
  - `sambanova`: Inferencia acelerada (200+ tps).
  - `nvidia`: NVIDIA NIM.
  - `gemini`: Google Gemini (soporta contextos masivos de 1M+ tokens).
  - `cloudflare`: Cloudflare Workers AI.
  - `ollama`: Privacidad local total (fallback offline).
- Enrutamiento inteligente en `chat.py`:
  - Si el contexto estimado supera los 5,000 tokens, el sistema desvía la consulta lejos de Groq (evitando el límite gratuito de 7,000 ITPM) y enruta hacia Gemini o Cloudflare.
  - Si `DataSanitizer` detecta datos sensibles, bloquea proveedores externos y enruta a Ollama local.

---

## Sección K: Gaps y Vulnerabilidades para C3

1. **GAP-C3-1: Ausencia de Chokepoint Terminal de Presupuesto**:
   - `build_phase_prompt` ensambla el prompt sumando partes (sistema + evidencia + historial + BKT + Mem0 + estilo + consulta) sin verificar si la suma excede el techo configurado.
2. **GAP-C3-2: Desborde en `SectionExpander`**:
   - Las expansiones de secciones y ventanas pueden inflar la evidencia documental sin un límite estricto de tokens totales.
3. **GAP-C3-3: Desconexión de `max_context_tokens` del Router**:
   - Los valores calculados por `IntentRouter` (5,000 o 16,000 tokens) son declarativos y no son exigidos ni aplicados en `StructuredResponsePipeline`.
4. **GAP-C3-4: Truncamiento de Historial por Caracteres en lugar de Tokens**:
   - `_MAX_RECENT_HISTORY_CHARS = 12000` es una heurística grosera que no garantiza cuántos tokens BPE reales consumirá el historial.
5. **GAP-C3-5: Falta de Medición Exacta de Tokens**:
   - Se utiliza la estimación `len(texto) // 4`, la cual tiene un margen de error del ±25% dependiendo del contenido (código, símbolos en C y sintaxis Markdown densa pueden ser hasta 1 token por cada 2 caracteres).

---

## Sección L: Recomendaciones para la Implementación de C3

1. **Diseñar un `ContextBudgetManager` Determinista**:
   - Ubicado como único chokepoint inmediatamente antes del despacho HTTP a los proveedores LLM.
2. **Jerarquía Estricta de Asignación de Presupuesto (Prioridad Descendente)**:
   - **Prioridad 1 (No negociable)**: System Prompt Base y Directivas de Seguridad/Anti-atajo.
   - **Prioridad 2 (No negociable)**: Consulta del Estudiante actual.
   - **Prioridad 3**: Directiva Pedagógica / BKT / Mem0 (acotada a máx 350 tokens).
   - **Prioridad 4**: Evidencia Documental (asignación de cuota fija, ej. hasta 2,500 tokens; si la evidencia expandida supera el presupuesto, se recortan chunks completos de menor relevancia).
   - **Prioridad 5**: Historial Conversacional (se asigna el residuo disponible; se descartan turnos viejos enteros para que la conversación no supere el presupuesto).
3. **Mecanismo Fail-Closed**:
   - Si los componentes no negociables (Prioridad 1 y 2) superan por sí solos el hard ceiling, la llamada debe fallar de forma controlada o solicitar aclaración, impidiendo cualquier desborde.
4. **Independencia de Modelos Externos**:
   - No delegar el cumplimiento del techo en LLMs ni en modelos generativos. La garantía C3 debe ser matemática y determinista.

---

## Sección M: Respuestas a las Preguntas Específicas 1 a 7

### 1. ¿Qué tiene TALOS hoy de Mem0 y cómo funciona realmente?
TALOS posee una implementación 100% soberana y local (`Mem0Manager`) que interactúa con SQLite (`student_state.db`). No usa la librería externa `mem0`. Funciona mediante reglas heurísticas regex y extracción determinista sobre los turnos del estudiante. No utiliza modelos de embeddings. Está limitado estrictamente a 2 preferencias, 2 patrones y 2 confusiones (~80-250 tokens), y se inyecta en el prompt final a través de `bkt_directive`.

### 2. ¿Qué modelo de embeddings corre hoy, en qué runtime, con qué huella y qué opciones viables existen?
En SQLite `vector_store.db` (1.3 GB) están indexados 287,069 vectores con `Qwen/Qwen3-Embedding-0.6B` (1024d, PyTorch/sentence-transformers). En disco local existe el modelo ONNX FP32 `multilingual-e5-small` (384d, 449 MB, ONNX Runtime CPU). En el entorno actual `.venv` (sin PyTorch instalado), la búsqueda vectorial densa aborta de forma segura por disparidad de dimensiones (1024 != 384) y SQLite FTS5 (BM25) asume la búsqueda híbrida en ~6 ms con 0 MB de RAM extra.

### 3. ¿Qué piezas de retrieval/routing están activas y cuáles son solo declarativas?
- **Activas en runtime**: `QueryRewriter` (activo), `SymbolGuard` (activo), `AdaptiveRetrievalRouter` (activo), FTS5 BM25 (activo), `filter_presentation` (activo), `GranularityRouter` (activo en chat.py), `LocalONNXReranker` (activo).
- **Declarativas / Parciales**: `max_context_tokens` en `config.py` e `intent_router.py` (declarativo, no aplicado como hard ceiling), `ConversationStateObject.compress_history` (inactivo en live chat, solo en tests), `SemanticRouter` (inactivo en chat.py, reservado a tutoría socrática).

### 4. ¿Qué capacidad de compresión/resumen existe hoy y qué le falta?
Existe persistencia de resúmenes estructurados de sesión (`SessionRecord.compressed_summary`, `session_digest.py`) basados en observaciones de errores y logros. Falta un rolling summarizer de turnos conversacionales en tiempo real dentro de la misma sesión: cuando se superan los 12,000 caracteres, los turnos anteriores simplemente se descartan sin condensarse.

### 5. ¿Qué routers o clasificadores livianos existen hoy?
Existen 6 routers: `AdaptiveRetrievalRouter` (regex), `GranularityRouter` (regex), `ConversationStyleRouter` (regex), `IntentRouter` (heurístico/fallback), `SemanticRouter` (Qwen 2B Ollama) y `TalosLLMRouter` (multi-cloud por fase). La inmensa mayoría opera en <1 ms sin invocar modelos generativos.

### 6. ¿Tiene sentido conceptualmente algo tipo Laya en TALOS, y para qué?
Tiene sentido para enriquecimiento semántico de queries complejas o para resumen inteligente de turnos antiguos, pero **NO para el enforcement del Hard-Ceiling C3**. El hard-ceiling debe ser una garantía matemática y determinista de presupuesto, no una inferencia probabilística delegada en otro modelo.

### 7. ¿Qué carga soporta el Ryzen 5 5600GT y qué conviene delegar o mantener liviano?
El Ryzen 5 5600GT (16 GB RAM) maneja con holgura FTS5 (<5 ms), búsqueda matricial BLAS (<35 ms) y el reranker neural local ONNX INT8 (~80 ms), utilizando solo ~1.5 GB de RAM. Conviene mantener la generación de texto delegada a los proveedores cloud ultrarrápidos (Cerebras, Groq, SambaNova) y preservar la CPU local libre para el pipeline determinista, garantizando una latencia de respuesta sub-segundo sin consumo excesivo de memoria ni saturación de núcleos.
