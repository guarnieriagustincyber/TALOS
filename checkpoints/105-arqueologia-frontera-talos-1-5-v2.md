# CP105 — Arqueología y Diseño de Frontera: TALOS 1.5 → TALOS V2

**Gate B / TALOS Evolution**  
**Fecha**: 2026-10-02  
**Tipo**: Read-only / Arqueología Técnica / Descubrimiento Arquitectónico / Clasificación de Evidencia  
**Estado**: AUDIT_COMPLETED / READ_ONLY_INVESTIGATION  
**Integridad DB**: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (`DATABASE_CHANGES = 0`)  

---

## 0. Marco Metodológico y Separación Canónica de Versiones

En cumplimiento estricto de las directivas de CP105:
- **DATABASE_CHANGES = 0**: No se modificó `data/web_state/knowledge_store.db`, no se alteraron bases de datos ni se aplicaron migraciones.
- **READ-ONLY**: Cero cambios de código en `src/`, cero cambios de configuración, cero mutación de manifests de autorización o fixtures de certificación.
- **MÉTODO**: `OBSERVE → MEASURE → CORRELATE → CLASSIFY → HUMAN DECISION → FUTURE CHANGE`.

### Separación Canónica de las Tres Capas:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        TALOS V1 — NÚCLEO CONGELADO                     │
│  Knowledge Components, BKT Oficial, Evaluación Determinista, RAG,     │
│  Autoridad Epistemológica, Abstención, Forensic Auditor, Socratic Pedagogy,│
│  Invariantes Certificadas de Aislamiento y ACL L3 (CP097, CP102).      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ sustrato
┌───────────────────────────────────▼────────────────────────────────────┐
│                  TALOS 1.5 — PLATAFORMA Y RUNTIME                      │
│  Memoria Longitudinal Jerárquica, Context Budgeting (C3), Continuidad, │
│  Retrieval Fabric Lite, Embeddings/ONNX, Enrutamiento Multi-Cloud USD 0,│
│  Infraestructura de Ingesta de Evidencia Externa, Presupuesto Desktop. │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ orquestación
┌───────────────────────────────────▼────────────────────────────────────┐
│              TALOS V2 — CUADERNO DE LABORATORIO Y PRÁCTICA             │
│  Observación de Práctica Externa (VMs, CTFs, IDEs, Terminal),           │
│  Evidence Processor, Pedagogical Assessor, Shadow BKT, Learning Events,│
│  Transferencia Controlada, Retención sin suplantar herramientas.       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Deliverable A — Inventario de Capacidades

A continuación se audita el estado real de cada capacidad identificada en el repositorio:

| Capacidad | Existe | Estado | Ubicación Principal | Ruta Activa | Evidencia Observable | Limitación Observada |
|---|:---:|---|---|:---:|---|---|
| **Mem0 Soberano** | SÍ | `ACTIVE_PRODUCTION` | `src/study_engine/memory/mem0_manager.py` | SÍ | Persiste en `student_state.db` (`student_pedagogical_memory`), inyecta en `chat.py:2025` | Sin embeddings; basado en regex; límite estricto a 2 ítems por categoría (~250 tok). |
| **Continuidad Conversacional** | SÍ | `ACTIVE_PARTIAL` | `src/study_engine/web/routes/chat.py:40-90` | SÍ | Buffer `_CONV_TURN_BUFFER` de hasta 12,000 chars | Descarte ciego de turnos viejos al desbordar; sin rolling summarization; conteo en chars, no tokens. |
| **Session Digest** | SÍ | `ACTIVE_PRODUCTION` | `src/study_engine/pedagogy/session_digest.py` | SÍ | Tabla `session_digests`; inyecta directiva en primer turno de sesión (`chat.py:1623`) | Solo KCs con lucha o maestría; JSON estructurado; 0 LLM libre; solo corre una vez por sesión. |
| **Student State / BKT** | SÍ | `ACTIVE_PRODUCTION` | `src/study_engine/student/` | SÍ | `BKTTracker`, `StudentStorage` en `student_state.db` | BKT oficial mono-KC en runtime web; Multi-KC restringido a tests y runners. |
| **Retrieval Fabric Lite** | SÍ | `ACTIVE_PRODUCTION` | `src/study_engine/retrieval/fabric.py` | SÍ | `QueryRewriter` → `SymbolGuard` → `AdaptiveRouter` → `search_hybrid` → `Reranker` | Tracing JSON activo en `logs/retrieval_trace.json`; depende del store subyacente. |
| **Embeddings Locales** | SÍ | `ACTIVE_PARTIAL` | `src/study_engine/retrieval/embedding.py` | SÍ | `LocalONNXEmbeddingProvider` (`multilingual-e5-small`, 384d, 449MB) | `vector_store.db` tiene vectores 1024d (Qwen3); en `.venv` aborta dense por dimensión y cae a FTS5. |
| **Embeddings Qwen3** | SÍ | `LEGACY` / `IN_STORE` | `data/web_state/vector_store.db` | NO | 287,069 vectores 1024d en SQLite | `sentence_transformers` no está instalado en `.venv`, por lo que el runtime local no genera nuevos vectores 1024d. |
| **Reranking Neural Local** | SÍ | `ACTIVE_PRODUCTION` | `src/study_engine/retrieval/reranker.py` | SÍ | `LocalONNXReranker` (`models/reranker/model.onnx`, 267MB INT8) | CPU Execution Provider en 4 hilos (~80ms); filtra top-5 pero no comprime longitud de chunks. |
| **Context Packing** | SÍ | `ACTIVE_PRODUCTION` | `src/study_engine/context/context_compiler.py` | SÍ | Ensambla chunks de evidencia con metadata de citas y páginas | Ensamblado aditivo sin poda proporcional al presupuesto restante. |
| **Hard-Ceiling de Contexto** | NO | `BLOCKED` | `src/study_engine/config.py` (`max_context_tokens`) | NO | Diagnosticado en CP103: `build_phase_prompt` suma componentes sin chokepoint terminal pre-LLM | Desborde demostrado de +50% a +165% sobre el techo nominal. |
| **Provider Routing** | SÍ | `ACTIVE_PRODUCTION` | `src/study_engine/llm/router.py` | SÍ | `TalosLLMRouter` con `ProviderCircuitBreaker` (CLOSED/OPEN/HALF_OPEN) | Soporta Cerebras, Groq, SambaNova, Nvidia, Gemini, Cloudflare, Ollama. Cooldown 300s. |
| **Provider Fallback** | SÍ | `ACTIVE_PRODUCTION` | `src/study_engine/llm/router.py:270-340` | SÍ | Descarta buffer parcial y reintenta en siguiente proveedor de la fase | Configurado por fase (`conceptual`, `verification`, `python_code`, etc.). |
| **Sandbox de Práctica (S6)** | SÍ | `DECLARATIVE_ONLY` | `src/study_engine/web/routes/practice.py` | SÍ | Endpoint `/api/practice/evaluate` retorna `PRACTICE_UNAVAILABLE` fail-closed | Sandbox real no montado en el servidor web; aserciones prácticas simuladas eliminadas. |
| **Lab Grader Bridge** | SÍ | `DISCONNECTED` | `src/study_engine/student/lab_observations.py` | NO | `LabGraderBridge` valida flags SHA-256 de 5 desafíos en `config/lab_kc_map.json` | Desconectado de FastAPI; no existe ruta HTTP `/api/lab/submit`. |
| **Ingesta de Evidencia (S5.2.A)** | SÍ | `INTEGRATED_BUT_LIMITED` | `src/study_engine/state/ingestion_engine.py` | NO | 4 gates de admisibilidad criptográfica (`ExecutionProvenanceSpine` → `EvidenceLedger`) | Totalmente funcional en runners de laboratorio y tests, pero no expuesta en API web pública. |
| **Grafo Curricular (Roadmap)** | SÍ | `ACTIVE_PRODUCTION` | `src/study_engine/roadmap/` y `curriculum/registry.py` | SÍ | Carga DAGs YAML (`data/curriculum/roadmaps/`), valida dependencias HARD/SOFT | Operativo para renderizado Mermaid y navegación; no modela subtemas ni transferencia multi-fase. |
| **Currículo en Espiral** | SÍ | `ACTIVE_PARTIAL` | `src/study_engine/pedagogy/spiral_curriculum.py` | SÍ | `SpiralCurriculumEngine` llamado en `chat.py:1980` | Diccionario hardcodeado a 7 relaciones en español coloquial; desconectado de los KC IDs canónicos. |
| **Compresión de Historia** | SÍ | `DEAD_CODE` | `src/study_engine/memory/conversation_state.py:76` | NO | `ConversationStateObject.compress_history` | Solo se invoca en fixtures de tests adversariales; no participa en el ciclo `/api/chat/query`. |
| **Resource Management** | NO | `NOT_IMPLEMENTED` | N/A | NO | No existe monitor de RAM, concurrencia o temperatura de CPU | El sistema asume recursos locales infinitos y no regula tareas en segundo plano. |

---

## Deliverable B — Gap Analysis

### 1. Ya Existe en Producción Plena (`ACTIVE_PRODUCTION`)
- BKT Oficial determinista y persistente en SQLite (`student_state.db`).
- Epistemic Retrieval Fabric Lite con reescritura, guard de símbolos y filtrado anti-fuga L3.
- Reranking Neural Local ONNX INT8 de ultra-baja latencia en CPU.
- Multi-cloud Router con Circuit Breakers automáticos (Cerebras, Groq, SambaNova, Gemini, Cloudflare).
- Persistencia de Session Digest entre sesiones.
- Invariantes de aislamiento curricular y autorización L3 certificadas (CP097, CP102).

### 2. Existe Parcialmente (`ACTIVE_PARTIAL`)
- **Memoria Mem0**: Existe y está activa, pero no utiliza semántica ni vectores; depende de regex rígidos sobre el texto del estudiante.
- **Continuidad Conversacional**: Existe buffer en memoria, pero recorta por caracteres sin entender límites de tokens ni condensar la trayectoria.
- **Currículo en Espiral**: El motor existe y se ejecuta en cada turno de chat, pero su taxonomía ("punteros", "concurrencia") no coincide con los IDs canónicos del catálogo (`SEC-01-C-PTR`), por lo que casi nunca produce sugerencias en producción.

### 3. Existe pero está Desconectado (`DISCONNECTED` / `INTEGRATED_BUT_LIMITED`)
- **LabGraderBridge**: Diseñado para calificar flags de Juice Shop, VAmPI y laboratorios C mediante hash SHA-256 hacia BKT, pero carece de endpoint HTTP en FastAPI.
- **EvidenceIngestionEngine y ExecutionProvenanceSpine (S5.2.A)**: Motor de admisibilidad criptográfica de 4 compuertas e integridad por ledger de evidencias; completamente operativo en `run_study_loop_v1.py` y tests, pero ausente en las rutas web de producción.

### 4. Existe Solamente como Infraestructura Declarativa (`DECLARATIVE_ONLY`)
- **Sandbox S6 (`/api/practice/evaluate`)**: Retorna `PRACTICE_UNAVAILABLE` fail-closed.
- **Context Ceiling (`MAX_CONTEXT_TOKENS`)**: Configurado en 5,000 / 16,000 tokens en `config.py` e `intent_router.py`, pero ningún middleware ni pipeline lo exige antes de despachar al LLM.

### 5. Existe como Legacy (`LEGACY`)
- **Vectores Qwen3 1024d en `vector_store.db`**: 287k vectores precalculados que no pueden ser consultados por dense retrieval en el `.venv` actual por falta de `sentence_transformers`, forzando el fallback a FTS5 BM25.
- **`vector_store_e5_384_legacy.db.bak`**: Archivo de respaldo de 623 MB de la arquitectura previa.

### 6. Código Muerto en Producción (`DEAD_CODE`)
- **`ConversationStateObject.compress_history`**: Algoritmo de compresión de diálogo que solo se ejecuta en la suite de pruebas.

### 7. No Existe (`NOT_IMPLEMENTED`)
- Hard-Ceiling de contexto terminal pre-LLM (C3).
- Memoria episódica/longitudinal jerárquica que vincule proyectos, decisiones y código.
- Modelo de observabilidad de práctica externa (ingesta de telemetría de VMs o terminales).
- Shadow BKT para separar la experimentación práctica del estado cognitivo oficial.
- Desktop Resource Manager para controlar la huella de TALOS en concurrencia con IDEs y navegadores.

---

## Deliverable C — Mapa de Asignación V1 → 1.5 → V2

Para evitar la fusión artificial de responsabilidades, cada capacidad se asigna a su plano natural:

| Capacidad | TALOS V1 (Core Epistémico Congelado) | TALOS 1.5 (Plataforma y Sustrato) | TALOS V2 (Práctica y Laboratorio) |
|---|---|---|---|
| **Memoria** | BKT Oficial (`p_L`), registro de fallas KC, historial pedagógico de mastery | Memoria longitudinal jerárquica, rolling conversation digest, cache de decisiones | Memoria de proyectos, bitácora de intentos de lab, historial de errores en terminal |
| **Contexto** | Directivas socráticas de fase, prompts base congelados | Hard-Ceiling C3 determinista, Budget Allocator pre-LLM, poda proporcional | Filtro y compresión de outputs masivos de herramientas (12k líneas → 300 tokens) |
| **Currículo** | Grafo DAG de KCs, prerrequisitos HARD/SOFT, catálogo formal | Indexación de KCs transversales, resolución unificada de identidades | Modelo espiral de reutilización práctica, desafíos multi-KC en laboratorios |
| **Retrieval / Embeddings** | Autorización L3 (allowlist estricta), contratos de evidencia autorizada | Dual runtime ONNX/FTS5 calibrado, Reranking INT8, caché matricial LRU | Búsqueda sobre write-ups, documentación técnica externa, manuales de labs |
| **Proveedores LLM** | Invariante de evaluación formal (0 LLM en la calificación de BKT) | TalosLLMRouter multi-cloud USD 0, circuit breakers, fallback transparente | Enrutamiento especializado (modelos rápidos para parsing de logs, modelos grandes para feedback) |
| **Herramientas (Tools)** | Prohibición estricta de ejecución arbitraria dentro del tutor | Protocolo de frontera Tool → Evidence → Context, validadores de schemas | Conectores pasivos para observar terminales, exportadores de Burp, logs de VMs |
| **Ingesta de Evidencia** | `EvidenceLedgerEntry`, 4 gates de admisibilidad criptográfica | API unificada `/api/evidence/ingest` protegida por tokens de sesión | Normalizador de telemetría externa (commands, exit codes, artifacts SHA-256) |
| **Evaluación Práctica** | Criterios deterministas de rúbrica, Hoare contracts | Despachador de tareas de evaluación desacopladas del event loop | Evaluador pedagógico de causalidad (distinguir copiar flag vs comprender falla) |
| **BKT** | BKT Oficial de release (solo muta por evidencia certificada) | Persistencia thread-safe de snapshots cognitivos | **Shadow BKT**: seguimiento experimental de destrezas prácticas antes de promover a V1 |
| **Transferencia y Retención**| Fórmulas SM-2 de repaso espaciado | Scheduler de revisiones en background | Detección de retención práctica y transferencia a nuevos entornos |

---

## Deliverable D — Grafo Curricular y Profundización Longitudinal

### 1. Auditoría del Modelo Curricular Actual
El sistema actual implementa la jerarquía:
```text
CurricularRoadmap
       ↓
RoadmapNode (node_type: TOPIC | COMPETENCY | LAB)
       ↓
CurricularNodeAlignment (document_id, page_start, page_end)
       ↓
Knowledge Components (KCs en notebook_kc_catalog.json)
```

### 2. Comparación contra la Visión Pedagógica Longitudinal

| Nivel Pedagógico Deseado | Existencia en TALOS | Implementación / Archivo | Persistencia | Uso Real Observado | Gaps Críticos Identificados |
|---|:---:|---|---|:---:|---|
| **Phase** | SÍ | `CurricularRoadmap.roadmap_id` | YAML en disco | Activo | Se usa como contenedor global; no hay transiciones formales entre fases. |
| **Unit** | NO | No modelado | N/A | Ninguno | Los roadmaps agrupan nodos sin una capa intermedia de unidad temática. |
| **Topic** | SÍ | `RoadmapNode(node_type=TOPIC)` | YAML en disco | Activo | Es la unidad primaria del roadmap en la UI. |
| **Subtopic** | NO | No modelado | N/A | Ninguno | Un topic salta directamente a la evidencia de páginas de libros. |
| **KC** | SÍ | `notebook_kc_catalog.json` | JSON en disco | Activo | Catálogo canónico; desacoplado estructuralmente del YAML del roadmap. |
| **Prerequisites** | SÍ | `RoadmapDependency(HARD/SOFT)` | YAML en disco | Activo | Valida bloqueo de nodos; no calcula propagación de maestría bayesiana. |
| **Exercises** | PARCIAL | `data/curriculum/tasks/` | JSON en disco | Parcial | Tareas JSON aisladas (`task_sec05_file_hasher.json`); no asociadas dinámicamente a KCs. |
| **Assessment** | SÍ | `data/curriculum/rubrics/` | JSON en disco | Parcial | Rúbricas formales de 4 niveles; desconectadas de la interacción conversacional web. |
| **Transfer** | NO | No modelado | N/A | Ninguno | No hay tracking de si un concepto aprendido en C aplica en Assembly o Web. |
| **Later Reuse** | PARCIAL | `SpiralCurriculumEngine` | Código en memoria | Test/Limitado | 7 reglas hardcodeadas en texto libre; no lee el grafo curricular canónico. |

---

## Deliverable E — Matriz de Observabilidad de la Práctica Externa

Para conectar TALOS con actividades prácticas externas (ej. resolver un lab en Juice Shop, PortSwigger, exploit local o VM), se comparan cinco niveles técnicos:

| Nivel | Tipo de Evidencia | Valor Pedagógico | Nivel de Ruido | Privacidad / Fuga | Complejidad & Coste | Factibilidad TALOS 1.5/V2 |
|:---:|---|---|---|---|---|---|
| **A** | **Solo Resultado Final**<br>(Hash de flag o código de retorno) | **Bajo**.<br>Demuestra que se obtuvo la flag, pero no si hubo comprensión, guessing o trampa. | Nulo.<br>1 string (hash 64 chars). | Total.<br>Cero exposición de datos del sistema. | Mínima.<br>Ya implementado en `LabGraderBridge` (`config/lab_kc_map.json`). | **INMEDIATA**.<br>Solo requiere exponer endpoint `/api/lab/submit`. |
| **B** | **Evidencia Seleccionada por el Estudiante**<br>(Comando clave + output + explicación causal del estudiante) | **Muy Alto**.<br>Obliga a la metacognición; evalúa razonamiento y justificación. | Muy Bajo.<br>Datos acotados y curados por el usuario (~300 tokens). | Alta.<br>El estudiante decide qué pegar; sanitizable por `DataSanitizer`. | Baja.<br>Entra por la interfaz de diálogo estructurada existente. | **ALTA**.<br>Compatible con la arquitectura conversacional actual. |
| **C** | **Commands, Logs y Salidas Relevantes**<br>(Historial de shell bash/zsh, errores y comandos filtrados) | **Alto**.<br>Permite reconstruir el proceso de prueba y error, herramientas y sintaxis. | Medio.<br>Requiere parser/filtro para descartar comandos irrelevantes (`ls`, `cd`, `clear`). | Media.<br>Riesgo de enviar contraseñas o tokens tipeados en terminal. | Media.<br>Requiere agente/hook local (script de shell o daemon ligero). | **MEDIA**.<br>Requiere pipeline de filtrado en TALOS 1.5. |
| **D** | **Trayectoria Completa de Ejecución**<br>(Session transcript completo de terminal / asciinema / keystrokes) | **Medio-Bajo**.<br>Sobrecarga masiva de datos; difícil aislar la intención pedagógica. | Extremo.<br>Miles de líneas de scroll, escapes ANSI, outputs binarios. | Baja.<br>Captura accidental de credenciales, paths locales y archivos personales. | Alta.<br>Requiere almacenamiento masivo y compresión pesada. | **BAJA**.<br>Inviable bajo límite de hardware y cuota USD 0. |
| **E** | **Instrumentación Automática de Herramientas**<br>(Plugins en Burp, hooks en GDB, extensiones en VS Code, eBPF) | **Máximo**.<br>Datos contextuales exactos (puntos de quiebre, payloads HTTP, inspección de memoria). | Alto.<br>Genera eventos continuos; requiere deduplicación y ventanas temporales. | Variable.<br>Depende del alcance del plugin/hook. | Muy Alta.<br>Desarrollo y mantenimiento de plugins para múltiples herramientas de terceros. | **FUTURA (V2 Avanzado)**.<br>Viable como plugins modulares desacoplados. |

---

## Deliverable F — Frontera Contexto / Memoria / Herramientas / LLM

### 1. Diagrama de la Frontera Arquitectónica

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   FUENTES DE ENTRADA AL TURNO                          │
├───────────────────┬───────────────────┬────────────────────────────────┤
│ MEMORIA ALUMNO    │ CONTEXTO TURNO    │ HERRAMIENTA / LAB EXTERNO      │
│ - BKT Masteries   │ - Historial Rec.  │ - Shell / Script output        │
│ - Mem0 Directives │ - User Prompt     │ - Burp / Network log           │
│ - Session Digest  │ - Fase Pedagógica │ - Flag / Proof submission      │
└─────────┬─────────┴─────────┬─────────┴───────────────┬────────────────┘
          │                   │                         │
          │                   │              ┌──────────▼──────────┐
          │                   │              │   EVIDENCE FILTER   │
          │                   │              │ - Regex sanitization│
          │                   │              │ - Error & exit code │
          │                   │              │ - Max 1500 chars    │
          │                   │              └──────────┬──────────┘
          │                   │                         │
          │         ┌─────────▼─────────┐               │
          │         │    RETRIEVAL /    │               │
          │         │   RAG EXPANDER    │               │
          │         │ - FTS5 / Vectors  │               │
          │         │ - Reranker top-k  │               │
          │         └─────────┬─────────┘               │
          │                   │                         │
          ▼                   ▼                         ▼
┌────────────────────────────────────────────────────────────────────────┐
│             BUDGET ALLOCATOR GUARD (CHOKEPOINT TERMINAL C3)            │
│  Presupuesto Total = HARD_CEILING_TOKENS (ej. 5,000 tokens)            │
│                                                                        │
│  1. System & Safety Directives  [Prioridad 1 - Fijo: ~800 tokens]      │
│  2. User Prompt                 [Prioridad 2 - Fijo: ~300 tokens]      │
│  3. Pedagogical & BKT State     [Prioridad 3 - Fijo: ~250 tokens]      │
│  4. Tool Evidence Sanitized     [Prioridad 4 - Cuota: ~600 tokens]     │
│  5. Document Evidence (RAG)     [Prioridad 5 - Cuota: ~1,800 tokens]   │
│  6. Conversation History        [Prioridad 6 - Residuo: ~1,250 tokens] │
│                                                                        │
│  * Regla de Truncamiento: Poda atómica por chunks/turnos completos     │
│  * Fail-Closed: Si (P1 + P2) > HARD_CEILING -> Error controlado        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Prompt Compilado y Acotado
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       TALOS LLM ROUTER MULTI-CLOUD                     │
│               (Cerebras / Groq / SambaNova / Gemini / Ollama)          │
└────────────────────────────────────────────────────────────────────────┘
```

### 2. Identificación de Puntos Críticos de Fuga o Inflación

1. **Inflación por Herramientas Externas**: Si un comando como `nmap` o `cat /etc/passwd` vuelca 2,000 líneas directamente al prompt, satura el contexto inmediatamente. El `Evidence Filter` debe actuar de aislante obligatorio antes de que el texto llegue al budgeter.
2. **Duplicación Memoria vs Historial**: Si `Session Digest` repite conceptos que ya están visibles en los últimos 4 turnos conversacionales, se desperdician entre 200 y 400 tokens en directivas redundantes.
3. **Bypass de Expansión (Demostrado en CP103)**: `SectionExpander` no consultaba el acumulado del turno, inyectando hasta 15,000 caracteres adicionales fuera de control.
4. **Crecimiento No Acotado del Historial**: La heurística de 12,000 caracteres en `chat.py` carece de compresión rodante; turnos de código extensos desplazan prematuramente preguntas conceptuales previas.

---

## Deliverable G — Matriz de Proveedores y Embeddings

### 1. Inferencia LLM (Generación y Razonamiento)

| Proveedor | Modelos Principales | Free Tier / Límites | Latencia Típica | Fortalezas | Riesgos / Mitigación en TALOS |
|---|---|---|---|---|---|
| **Cerebras** | Llama 3.1 8B, Llama 3.3 70B | ~30 RPM, 60k TPM | Ultra-rápida (~1200 tps) | Ideal para streaming conversacional instantáneo | Límites de TPM bajos; requiere circuit breaker hacia Groq. |
| **Groq** | Llama 3.3 70B, Llama 3.1 8B, Gemma 2 | 30 RPM, 7k ITPM (gratis) | Ultra-rápida (~500 tps) | Calidad de razonamiento y respuestas estructuradas | Límite estricto de 7k input tokens/min; `chat.py` ya desvía si el prompt > 5k tokens. |
| **SambaNova** | Llama 3.3 70B, Qwen 2.5 72B | Generoso en beta | Rápida (~250 tps) | Soporta modelos de 72B con alto paralelismo | Fallback secundario de alta fidelidad. |
| **Google Gemini** | Gemini 2.0 Flash, Gemini 1.5 Flash | 15 RPM, 1M TPM, 1,500 RPD | Media (~80 tps) | Ventana de contexto masiva (1M+ tokens); multimodalidad | Términos de uso de AI Studio permiten revisión de datos en free tier; no apto para PII. |
| **Cloudflare** | Workers AI (@cf/meta/llama-3.1-8b) | 10k neuronas/día (~free) | Media (~60 tps) | Infraestructura edge sin claves de API centralizadas | Respuestas más lentas y contexto máximo reducido (4k-8k). |
| **Ollama Local** | Qwen 2.5 / Llama 3.2 (local) | Ilimitado (offline) | Baja (~10-18 tps en CPU) | 100% privado y soberano; 0 fugas de red | Consume CPU y memoria local; reservado para fail-closed de PII. |

### 2. Embeddings y Reranking

| Componente | Proveedor / Modelo | Dimensiones | Contexto | Estado en TALOS | Free Tier / Costo | Evaluación para TALOS 1.5 |
|---|---|:---:|:---:|---|---|---|
| **Reranker Local** | `bge-reranker-base-ONNX` | N/A (Cross-enc) | 512 | `ACTIVE_PRODUCTION` | USD 0 (Local CPU) | Excelente (~80ms, 300MB RAM). Mantener como estándar local. |
| **Embedding Local ONNX** | `intfloat/multilingual-e5-small` | 384d | 512 | `ACTIVE_PRODUCTION` (en disco) | USD 0 (Local CPU) | Rápido (~20ms, 450MB RAM). Puede usarse de inmediato si se regeneran shards a 384d. |
| **Embedding Local ST** | `Qwen/Qwen3-Embedding-0.6B` | 1024d | 8192 | `IN_STORE` (287k vectores) | USD 0 (Local CPU) | Requiere PyTorch en `.venv` (~1.5GB RAM). Desactivado en runtime actual. |
| **Google Gemini Embed 001** | `gemini-embedding-001` | 128 a 3072 (MRL) | 2,048 | `EXTERNAL_CANDIDATE` | Free tier AI Studio / $0.15/1M tok | Requiere conexión a internet; cuota compartida por proyecto. |
| **Google Gemini Embed 2** | `gemini-embedding-2` | 128 a 3072 (MRL) | 8,192 | `EXTERNAL_CANDIDATE` | Free tier AI Studio | Nativamente multimodal (PDF, imágenes, texto). Muy potente para diagramas. |

### 3. Investigación Exhaustiva de Google Embeddings (Consultada: 2026-10-02)
- **Deprecaciones Oficiales**: `text-embedding-004` fue oficialmente discontinuado y dado de baja el 14 de enero de 2026. Los modelos estándar activos son `gemini-embedding-001` (texto) y `gemini-embedding-2` (nativamente multimodal: texto, audio, imágenes y PDFs consolidados).
- **Matryoshka Representation Learning (MRL)**: Ambos modelos permiten seleccionar dinámicamente dimensiones reducidas (ej. 768d o 1536d) sin reentrenar ni perder drásticamente precisión semántica, reduciendo a la mitad el almacenamiento de vectores en SQLite.
- **Entidad de Cuota (Desmitificación)**: La cuota de Google AI Studio pertenece al **Proyecto de Google Cloud (GCP Project)**, no a la API key individual. Crear 3 claves dentro del mismo proyecto comparte exactamente el mismo límite de RPM/TPM. La cuota gratuita aplica por proyecto y por cuenta de Google. Además, el Free Tier de AI Studio incluye cláusulas de entrenamiento/revisión de datos, por lo que **no debe enviarse código confidencial ni datos de estudiante sin sanitizar**.

---

## Deliverable H — Presupuesto de Recursos Desktop (TALOS Concurrent Contract)

Para garantizar que TALOS opere fluidamente en un **Ryzen 5 5600GT (16 GB RAM)** mientras el estudiante utiliza activamente Brave, VS Code, terminales y máquinas virtuales de laboratorio:

### Presupuesto Máximo de Recursos Asignado a TALOS 1.5

```text
┌────────────────────────────────────────────────────────────────────────┐
│               DESKTOP CONCURRENT OPERATION CONTRACT                    │
├────────────────────────────────┬───────────────────────────────────────┤
│ Métrica                        │ Límite Asignado para TALOS 1.5        │
├────────────────────────────────┼───────────────────────────────────────┤
│ Memoria RAM en Reposo (Idle)   │ ≤ 1.2 GB RAM                          │
│ Memoria RAM en Pico Operativo  │ ≤ 2.2 GB RAM (durante RAG + Reranking)│
│ Uso de CPU en Reposo           │ ≤ 0.5% CPU (0 hilos activos)          │
│ Uso de CPU en Reranking Local  │ ≤ 4 hilos por máx 150 ms              │
│ Latencia de Pipeline Local     │ ≤ 120 ms (FTS5 + ONNX Reranker)       │
│ Concurrencia Máxima Local      │ 2 requests concurrentes en streaming  │
│ Tareas en Background           │ Máximo 1 tarea I/O desacoplada        │
│ Almacenamiento en Disco        │ ≤ 3.5 GB (DBs SQLite + Modelos ONNX)  │
└────────────────────────────────┴───────────────────────────────────────┘
```

### Justificación de Coexistencia en 16 GB RAM:
- Sistema Operativo + Entorno Gráfico: ~3.0 GB
- Brave Browser (10-15 pestañas de estudio/docs): ~3.5 GB
- VS Code / Cursor: ~1.5 GB
- VM de Laboratorio (Linux lightweight / Docker): ~4.0 GB
- **TALOS 1.5 Runtime (máximo)**: **~2.2 GB**
- **Margen de Seguridad / Buffer Libre**: **~1.8 GB RAM**

---

## Deliverable I — Paquete de Decisiones Humanas (D105-01 a D105-08)

### D105-01 — Modelo de Memoria Longitudinal
- **Pregunta**: ¿Qué fidelidad de memoria longitudinal debe conservar TALOS entre sesiones?
- **Opciones Observadas**:
  - **Opción A (Fact-based)**: Conservar solo KCs y directivas de estilo en `student_pedagogical_memory` (estado actual de Mem0).
  - **Opción B (Jerárquica / Tripartita - Recomendada)**:
    1. *Episódica*: Digest estructurado de la sesión previa (lo que se practicó y dónde hubo fricción).
    2. *Cognitiva*: Estado de maestría BKT por KC.
    3. *Proyecto / Laboratorio*: Bitácora de desafíos completados, herramientas utilizadas y errores causales observados.
  - **Opción C (Transcripción Completa)**: Almacenar transcripciones integrales con RAG sobre diálogos pasados.
- **Evidencia**: Opción C satura la base de datos y añade latencia sin aportar valor pedagógico directo. Opción A pierde el contexto de qué estaba construyendo el estudiante.
- **Recomendación**: Adoptar **Opción B**.

### D105-02 — Representación Curricular Longitudinal
- **Pregunta**: ¿Se extiende el DAG de Roadmap para admitir unidades intermedias y relaciones espirales canónicas?
- **Opciones Observadas**:
  - **Opción A**: Mantener el modelo actual plano (`RoadmapNode` directo a KCs).
  - **Opción B**: Normalizar `SpiralCurriculumEngine` para que sus relaciones causales apunten a los KC IDs canónicos del catálogo (`SEC-01-C-PTR`), permitiendo sugerir revisiones de temas anteriores cuando se domina un KC nuevo.
  - **Opción C**: Reestructurar formalmente el esquema de roadmaps a 5 capas (`Phase → Unit → Topic → KC → Exercise`).
- **Recomendación**: **Opción B** en el corto plazo (desbloquea el currículo espiral con cero impacto en el esquema); evaluar **Opción C** para TALOS V2.

### D105-03 — Nivel de Observabilidad de Práctica Externa
- **Pregunta**: ¿Qué nivel de telemetría de laboratorios externos debe procesar TALOS V2?
- **Opciones Observadas**:
  - **Nivel A**: Solo hash de flags/resultados finales.
  - **Nivel B (Recomendada)**: Evidencia seleccionada por el estudiante (comando ejecutado + fragmento de output + breve justificación causal).
  - **Nivel C**: Hook en bash/zsh que capture historial de comandos.
- **Evidencia**: Nivel A no evalúa comprensión (permite atajos). Nivel C captura contraseñas accidentales y ruido irrelevante. Nivel B maximiza la metacognición pedagógica con mínimo ruido y cero riesgo de privacidad.
- **Recomendación**: **Nivel B** como interfaz primaria de TALOS V2, complementada con **Nivel A** para comprobaciones deterministas rápidas.

### D105-04 — Frontera de Herramientas y Evidencia
- **Pregunta**: ¿Cómo debe ingresar la salida de una herramienta externa a TALOS?
- **Opciones Observadas**:
  - **Opción A (Inyección Directa)**: El estudiante o herramienta vuelca el log crudo en el chat.
  - **Opción B (Sanitización y Cuota Fija - Recomendada)**: Canalizar toda entrada práctica a través de un `EvidenceFilter` que elimine ruido ANSI, trunque a un máximo de 1,500 caracteres y extraiga metadatos (comando, exit code, error).
- **Recomendación**: **Opción B** para preservar el hard ceiling de contexto.

### D105-05 — Presupuesto y Hard-Ceiling C3
- **Pregunta**: ¿Cómo debe aplicarse el techo de contexto en el runtime?
- **Opciones Observadas**:
  - **Opción A**: Recorte libre basado en conteo de caracteres en `chat.py`.
  - **Opción B (Budget Allocator Terminal - Recomendada)**: Un chokepoint matemático determinista previo a la llamada HTTP que asigne cuotas prioritarias innegociables (Sistema > Usuario > Estado Pedagógico > Evidencia Documental > Historial) con poda a nivel de chunks enteros.
- **Recomendación**: **Opción B** (resuelve C3 sin alterar la base de datos).

### D105-06 — Estrategia de Proveedores LLM (USD 0)
- **Pregunta**: ¿Qué política de enrutamiento garantiza disponibilidad continua a costo cero?
- **Opciones Observadas**:
  - **Opción A**: Depender de un único proveedor principal.
  - **Opción B (Cascada Resiliente Multi-Cloud - Recomendada)**: Priorizar Cerebras (velocidad ultra-alta) → Groq (calidad) → SambaNova → Gemini (contexto amplio) → Ollama local (fallback offline y datos sensibles).
- **Recomendación**: **Opción B** (ya soportada por `TalosLLMRouter`).

### D105-07 — Estrategia de Embeddings y Vector Store
- **Pregunta**: ¿Cómo resolver la desconexión entre el vector store de 1024d y el runtime local de 384d?
- **Opciones Observadas**:
  - **Opción A**: Mantener FTS5 BM25 como motor principal de recuperación (costo cero de memoria, ~6ms de respuesta, 100% determinista).
  - **Opción B**: Instalar `sentence_transformers` en `.venv` para activar dense retrieval sobre los 287k vectores Qwen3 existentes (costo: +1.5 GB RAM).
  - **Opción C**: Reindexar el corpus completo con `multilingual-e5-small` ONNX local a 384d (costo: tiempo de cómputo único, bajo consumo RAM permanente).
- **Evidencia**: FTS5 BM25 está respondiendo con excelente precisión y cero sobrecarga de memoria.
- **Recomendación**: Mantener **Opción A** durante el cierre de Gate B; evaluar **Opción B o C** para cuando se certifique C3.

### D105-08 — Contrato de Recursos Desktop
- **Pregunta**: ¿Se adopta el límite formal de ≤ 2.2 GB RAM y ≤ 4 hilos CPU para TALOS en reposo y pico?
- **Recomendación**: **Aprobar** el contrato propuesto en el Deliverable H para garantizar coexistencia con entornos de ciberseguridad (VMs, Burp Suite, IDEs).

---

## Deliverable J — Respuestas Epistémicas a las 22 Preguntas del Criterio de Éxito

1. **¿Qué memoria tiene realmente TALOS hoy?**  
   Tiene una implementación propia en SQLite (`student_state.db`): estados BKT (`bkt_states`), preferencias y patrones heurísticos (`student_pedagogical_memory`), y resúmenes estructurados de sesión (`session_digests`). No usa embeddings.
2. **¿Qué memoria necesita conceptualmente para soportar aprendizaje longitudinal?**  
   Una memoria tripartita: cognitiva (BKT), episódica (resúmenes de sesión rodantes) y de laboratorio (bitácora de proyectos y desafíos resueltos con sus dificultades causales).
3. **¿Qué estructuras curriculares existen?**  
   Roadmaps en DAG YAML (`RoadmapNode`, `RoadmapDependency`), alineaciones documento-nodo (`CurricularNodeAlignment`), catálogo canónico de KCs (`notebook_kc_catalog.json`) y tareas prácticas aisladas en JSON.
4. **¿Pueden representar profundización progresiva?**  
   Parcialmente. El motor `SpiralCurriculumEngine` existe y se ejecuta, pero está restringido a 7 reglas de texto libre en lugar de navegar el grafo curricular formal.
5. **¿Pueden reutilizar KCs y ejercicios entre fases?**  
   Conceptualmente sí; materialmente no está cableado entre diferentes roadmaps. Los KCs están acotados por notebook.
6. **¿Qué puede observar TALOS de una práctica externa?**  
   Hoy puede observar únicamente el resultado final (hash SHA-256 de flags) mediante `LabGraderBridge`.
7. **¿Qué niveles de observabilidad son técnicamente posibles?**  
   Nivel A (resultado final), Nivel B (evidencia y justificación seleccionada por el estudiante), Nivel C (logs filtrados de shell), Nivel D (transcript crudo) y Nivel E (plugins/instrumentación).
8. **¿Qué información debería convertirse en evidencia?**  
   El comando ejecutado, el resultado relevante (código de salida o mensaje de error), el artefacto producido y la explicación causal del estudiante anclada a un KC específico.
9. **¿Cómo se separan Tool → Evidence → Context → LLM?**  
   La herramienta genera datos crudos; un `EvidenceFilter` extrae hechos relevantes sanitizados (<1500 chars); el `Budget Allocator` asigna cuota en el contexto; el LLM interpreta pedagógicamente sin saturarse.
10. **¿Qué límites de contexto existen realmente?**  
    Límites parciales por caracteres (12k chars en historial, 4k chars en prompt de usuario) y cuotas fijas en `RESPONSE_MODES`. No existe un hard ceiling total sobre el prompt final despachado al LLM.
11. **¿Qué embeddings están realmente activos?**  
    `multilingual-e5-small` (384d ONNX) está presente en disco; pero en runtime web actual, al detectar disparidad con la base de 1024d, aborta dense retrieval y opera FTS5 BM25.
12. **¿Qué retrieval es realmente operativo?**  
    Retrieval Fabric Lite con FTS5 léxico BM25, filtrado anti-fuga L3 y `LocalONNXReranker` INT8 en CPU.
13. **¿Qué arquitectura multi-provider es viable?**  
    `TalosLLMRouter` con circuit breakers thread-safe y cascada por fases (Cerebras → Groq → SambaNova → Gemini → Ollama).
14. **¿Qué significa realmente USD 0?**  
    Operar exclusivamente sobre capas gratuitas legítimas (Free Tiers de proveedores cloud) y motores locales en CPU (FTS5, ONNX), sin incurrir en costos de suscripción ni violar términos de servicio mediante multi-cuentas abusivas.
15. **¿Qué recursos necesita TALOS mientras el usuario trabaja en el desktop?**  
    Máximo 2.2 GB de RAM en pico operativo, ≤0.5% CPU en reposo y hasta 4 hilos temporales (~80ms) durante reranking, dejando >10 GB libres para Brave, VS Code y VMs.
16. **¿Qué corresponde a V1?**  
    El núcleo epistémico congelado: catálogo de KCs, fórmulas BKT, evaluación formal, autoridad de fuentes L3 y pedagogía socrática.
17. **¿Qué corresponde a V1.5?**  
    La infraestructura y runtime: Hard-Ceiling C3, Budget Allocator, memoria longitudinal jerárquica, router multi-cloud, y conectores de evidencia de herramientas.
18. **¿Qué corresponde a V2?**  
    La capa práctica: orquestación de laboratorios, Shadow BKT, ingesta de telemetría de práctica externa, y evaluación de transferencia y retención.
19. **¿Qué está implementado?**  
    BKT, RAG FTS5 + Reranker ONNX, routers deterministas, circuit breakers de proveedores, Mem0 heurístico, y verificación criptográfica de evidencia en runners de test.
20. **¿Qué está solamente diseñado?**  
    El sandbox de práctica S6 (retorna stub), la ingesta pública de evidencia web, y el motor curricular espiral multi-fase.
21. **¿Qué no existe?**  
    Hard-Ceiling C3 pre-LLM, rolling summarizer de diálogo activo, Shadow BKT y monitor de recursos desktop.
22. **¿Qué decisiones requieren aprobación humana?**  
    Las 8 decisiones del Deliverable I (D105-01 a D105-08).
