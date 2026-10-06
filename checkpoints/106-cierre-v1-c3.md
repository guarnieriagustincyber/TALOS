# CP106 — Cierre de TALOS V1 y Hoja de Ruta Oficial V1 → V1.5 → V2

**Gate B / TALOS Evolution & Architecture**  
**Fecha**: 2026-10-02  
**Tipo**: Read-only / Auditoría de Readiness C3 / Formalización de Hoja de Ruta  
**Estado**: AUDIT_COMPLETED / READ_ONLY_INVESTIGATION  
**Integridad DB**: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (`DATABASE_CHANGES = 0`)  
**Revisión Epistemológica**: CP106.1  

---

## 0. Resumen Ejecutivo y Mandato Canónico

En estricto cumplimiento de las directivas de CP106 y su calibración epistemológica CP106.1:
1. **DATABASE_CHANGES = 0**: No se modificó `data/web_state/knowledge_store.db`, no se alteraron bases de datos ni se aplicaron migraciones (hash SHA-256 verificado antes y después).
2. **READ-ONLY**: Cero modificaciones de código productivo en `src/`, cero alteraciones de contratos de V1, cero implementación anticipada de V1.5 o V2.
3. **DOBLE OBJETIVO CUMPLIDO**:
   - Se formalizó en el repositorio el documento normativo permanente [`docs/TALOS_ROADMAP_V1_V1_5_V2.md`](file:///media/agustin/Laboratorio/study-engie/docs/TALOS_ROADMAP_V1_V1_5_V2.md), fijando la frontera inmutable entre el núcleo epistemológico V1 (congelado), el espacio de diseño de plataforma V1.5 (candidato, no decidido) y el cuaderno de laboratorio V2 (futuro, no implementado).
   - Se realizó la auditoría exhaustiva de preparación y cierre (*readiness audit*) del Criterio 3 de Gate B (C3 — Hard Context Ceiling), reconstruyendo la traza completa desde retrieval hasta los proveedores LLM, auditando las superficies de inflación de tokens, clasificando los mecanismos de fallback y estructurando el paquete de decisión humana indispensable para desbloquear su implementación.

---

## 1. Contexto Canónico de Versiones

Queda asentado de manera explícita e incontrovertible en el proyecto:

### TALOS V1 — Core Epistemológico / Pedagógico
Es el núcleo fundacional ya construido, evaluado y formalizado. Incluye:
- Catálogo atómico de Knowledge Components (`notebook_kc_catalog.json`).
- Bayesian Knowledge Tracing (BKT) Oficial determinista ($p(L_0), p(T), p(S), p(G)$ en `student_state.db`).
- Algoritmo de repaso espaciado SM-2.
- Registro de estado del estudiante y persistencia relacional.
- Retrieval híbrido FTS5 BM25 + Reranking neural local INT8 ONNX.
- Validación epistémica, abstención pedagógica y contratos *fail-closed*.
- Auditoría forense inmutable de citas y justificaciones.
- Andamiaje socrático escalonado (*fading*) y prevención de fuga de respuestas (*anti-solution leakage*).
- Autoridad normativa y ACL efectiva L3 (`config/l3_authorization_manifest.json`, blindado en CP101/CP102).
- Perfil cognitivo dinámico de fortalezas y brechas.

```text
ESTADO NORMATIVO: V1 CORE = CERTIFIED / FROZEN
```
> **Definición de "Frozen"**: El núcleo conceptual y algorítmico de V1 está **terminado**. No está sujeto a rediseño ni en desarrollo activo.

---

## 2. Gate B — Estado Actual de Criterios

La resolución de pendientes de Gate B **no significa reconstruir V1**, sino certificar de manera reproducible sus garantías operacionales:

| Criterio | Descripción | Estado Oficial | Checkpoint de Cierre / Diagnóstico |
|---|---|:---:|---|
| **C1** | Reconciliación estricta de IDs, aliases y namespaces curriculares | **PASS / CLOSED** | CP096 (formalización), CP097 (certificación material) |
| **C2** | Roles de fuentes, allowlist técnica y ACL efectiva L3 | **PASS / CLOSED** | CP098 (auditoría), CP101 (blindaje), CP102 (certificación) |
| **C3** | Hard Context Ceiling terminal por llamada al backend LLM | **BLOCKED / ASSURANCE BLOCKER** | CP103 (diagnóstico), CP104 (arqueología runtime), CP106 (readiness) |
| **C4** | Aislamiento multi-curricular en ejecución concurrente | **PARTIAL / EXISTING EVIDENCE** | CP095 (clasificación corregida), previsto CP107 |
| **C5** | Compuerta de abstención estricta y confianza epistémica | **BLOCKED / ASSURANCE BLOCKER** | Previsto CP108 |

### Registro Histórico de Checkpoints Recientes
- **C1 cerrado en CP097**: Demostración material reproducible de aislamiento de 5 currículos en storage virgen.
- **C2 cerrado en CP102**: Certificación de 99/99 relaciones (81 autorizadas, 1 pendiente, 17 excluidas), cero fugas multi-doc o cross-notebook y validación de fixtures A-E.
- **C3 diagnosticado en CP103**: Descubrimiento de desbordes sistemáticos pre-LLM (+50% a +165%).
- **CP104**: Arqueología de infraestructura cognitiva, memoria Mem0, embeddings y runtime local.
- **CP105**: Arqueología de frontera V1.5 → V2, inventario de capacidades y paquete D105-01 a D105-08.
- **CP106**: Auditoría de readiness de C3 y formalización de hoja de ruta V1 → V1.5 → V2.

---

## 3. Resumen Canónico del Problema C3 (Diagnóstico CP103 / CP106)

> **Declaración Epistémica Fundamental**:  
> CP106 confirmó con evidencia material que el límite actual de evidencia recuperada no constituye un hard ceiling físico del prompt final enviado al LLM.  
> **C3 está auditado, pero no está resuelto.** La solución del contrato C3 todavía requiere decisión humana del propietario del proyecto.

El estado del criterio C3 es exactamente:
```text
C3 = BLOCKED / ASSURANCE_BLOCKER
AUDIT = COMPLETED
CONTRACT = NOT YET ADJUDICATED
IMPLEMENTATION = NOT AUTHORIZED
```

### Hallazgos Materiales Reconfirmados:
1. **Capa 1 — Límite de Expansión en Retrieval**:
   `SectionExpander.expand_results()` respeta el límite nominal `settings.max_context_tokens = 5000` para acotar la evidencia primaria recuperada.
2. **Capa 2 — Inflación y Desprotección Post-Retrieval**:
   Entre el retrieval y el despacho terminal al proveedor LLM, el pipeline concatena múltiples fuentes de texto sin ningún control de presupuesto agregado:
   - Directivas de modo de respuesta (`RESPONSE_MODES`);
   - Historial de conversación en memoria (`_CONV_TURN_BUFFER`);
   - Directivas pedagógicas de BKT, lucha cognitiva y andamiaje;
   - Memoria pedagógica Mem0;
   - Inyección de session digest en primer turno;
   - Reglas de estilo socrático y anti-shortcut blocks.
3. **Evidencia Material Observada (CP103 Fixtures A–F)**:
   Mientras el bloque de evidencia recuperada se mantuvo en ~5,000 tokens, el prompt total compuesto alcanzó hasta **13,281 tokens estimados**, siendo despachado sin restricción a través de Google Gemini.

> **Conclusión Inequívoca**: C3 permanece como **ASSURANCE BLOCKER** porque no existe un guard físico terminal inmediatamente antes de la llamada al backend LLM. No debe confundirse un diagnóstico completo con un problema cerrado.

---

## 4. Paquete de Decisiones Humanas Pendientes para C3

Antes de autorizar cualquier modificación en el runtime, el propietario del proyecto debe adjudicar soberanamente las siguientes tres decisiones:

```text
D_C3_1 = HUMAN DECISION PENDING
D_C3_2 = HUMAN DECISION PENDING
D_C3_3 = HUMAN DECISION PENDING
```

### D_C3_1 — Perímetro del Hard Context Ceiling
- **Opción A (Evidencia Únicamente)**: El techo limita exclusivamente los fragmentos documentales recuperados (RAG).  
  *Implicación*: No garantiza presupuesto total al LLM; el historial y directivas pueden causar overflow o exceder rate limits (TPM).
- **Opción B (Prompt Total al LLM)**: El techo se aplica sobre la suma total de tokens de todos los mensajes enviados al provider.  
  *Implicación*: Requiere un mecanismo de poda o rechazo cuando el total exceda la cuota.
- **Opción C (Presupuestos por Capas / Layered Quotas) — [PROPUESTA DE AUDITORÍA]**:
  - Cuota fija inmutable para System Prompt + Directivas de Seguridad (~800 tok).
  - Cuota máxima para Evidencia Epistémica RAG (~2,500 tok).
  - Cuota máxima para Historial Reciente + Memoria (~1,200 tok).
  - Cuota para Query del Usuario + Scratchpad (~500 tok).
  - Techo duro global infranqueable (ej. 5,000 tokens totales).  
  *(Estado: Propuesta arquitectónica sujeta a decisión humana; NO está aprobada ni decidida).*

### D_C3_2 — Comportamiento ante Overflow de Presupuesto
- **Opción A (Poda Jerárquica Determinista) — [PROPUESTA DE AUDITORÍA]**: Si la suma supera el techo, podar en orden inverso de prioridad pedagógica:
  1. Recortar turnos antiguos del historial conversacional;
  2. Reducir chunks de menor score del reranker;
  3. Comprimir directivas secundarias;
  4. Preservar intactas la evidencia nuclear y las directivas de seguridad.  
  *(Estado: Propuesta técnica sujeta a decisión humana; NO está aprobada ni decidida).*
- **Opción B (Fail-Closed / Error Explícito)**: Abortar la petición emitiendo un error estructurado `CONTEXT_BUDGET_EXCEEDED` sin llamar al LLM.  
  *Implicación*: Interrumpe la experiencia del usuario ante preguntas complejas o sesiones extensas.
- **Opción C (Truncamiento Ciego de Cola)**: Cortar abruptamente los últimos caracteres del prompt.  
  *Implicación*: Altamente riesgoso; rompe sintaxis de instrucciones o citas a mitad de frase.

### D_C3_3 — Método de Medición de Tokens
- **Opción A (Estimación Heurística Conservadora) — [PROPUESTA DE AUDITORÍA]**: $\text{tokens} = \lceil\text{caracteres} / 3.5\rceil$ con factor de seguridad del 15%.  
  *Ventaja*: Cero sobrecarga de CPU/RAM, 0 ms de latencia. *(Estado: Propuesta sujeta a decisión humana).*
- **Opción B (Tokenizador BPE Exacto)**: Ejecución de `tiktoken` (cl100k_base) o tokenizador HuggingFace local antes del despacho.  
  *Ventaja*: Precisión matemática absoluta. *Costo*: +20 ms y dependencia externa.
- **Opción C (Tokens Prealmacenados de Chunks)**: Sumar `chunk.token_count` ya indexado en SQLite más estimación de directivas.  
  *Ventaja*: Aprovecha metadatos existentes de FTS5.

### Resumen de Opciones y Estado de Recomendaciones

| Decisión | Opciones Disponibles | Recomendación Técnica de Auditoría | Estado Epistémico Oficial |
|---|---|---|:---:|
| **D_C3_1: Perímetro** | **A**: Solo RAG.<br>**B**: Prompt total.<br>**C**: Cuotas por capas. | **AUDITOR RECOMMENDATION**: Opción C (Layered Quotas) | **HUMAN DECISION PENDING** |
| **D_C3_2: Overflow** | **A**: Poda jerárquica.<br>**B**: Fail-closed.<br>**C**: Truncamiento ciego. | **AUDITOR RECOMMENDATION**: Opción A (Poda Jerárquica) | **HUMAN DECISION PENDING** |
| **D_C3_3: Medición** | **A**: Heurística ($\text{chars}/3.5$).<br>**B**: Tokenizador BPE exacto.<br>**C**: Conteo de chunks SQLite. | **AUDITOR RECOMMENDATION**: Opción A (Heurística) | **HUMAN DECISION PENDING** |

> **Nota Epistemológica**: Las recomendaciones del auditor son exclusivamente opiniones técnicas fundamentadas para facilitar la decisión; **NO constituyen decisiones aprobadas, requeridas ni canónicas**. La potestad decisoria pertenece al propietario del proyecto.

---

## 5. Auditoría de Readiness C3: Call-Graph y Superficies de Inflación

### 5.1. Call-Graph End-to-End Auditado en Código
Se rastreó exhaustivamente la ruta de ejecución en `src/study_engine/web/routes/chat.py`, `src/study_engine/pedagogy/structured_pipeline.py` y `src/study_engine/llm/multi_fallback.py`:

```text
[Cliente Web / API]
        │ POST /api/chat/query
        ▼
[chat.py:2058] DataSanitizer.sanitize_prompt()  --> [FAIL-CLOSED si detecta PII]
        │
        ▼
[chat.py:1920] IntentRouter / GranularityRouter
        │
        ▼
[chat.py:1945] Retrieval Fabric Lite: search_hybrid()
        │
        ▼
[chat.py:1960] SectionExpander.expand_results() --> [LÍMITE ACOTADO: max_context_tokens = 5000]
        │
        ▼
[chat.py:1975] _assemble_epistemic_context()    --> Ensambla chunks + citas formateadas
        │
        ▼
[chat.py:1980] SpiralCurriculumEngine.suggest() --> [INFLACIÓN: +150-300 caracteres]
        │
        ▼
[chat.py:1995] BKTTracker + StruggleDetector    --> [INFLACIÓN: directivas pedagógicas de andamiaje]
        │
        ▼
[chat.py:2025] Mem0Manager.get_memories()       --> [INFLACIÓN: hasta 2 ítems por categoría, ~250 tok]
        │
        ▼
[chat.py:1623] SessionDigest injection (T=1)    --> [INFLACIÓN: directiva estructurada de sesión previa]
        │
        ▼
[chat.py:2080] Historial de Conversación        --> [INFLACIÓN: buffer _CONV_TURN_BUFFER hasta 12k chars]
        │
        ▼
[structured_pipeline.py:1590] build_phase_prompt()
   ├── system_prompt (contract base + phase + assessment)
   ├── rendered_phase_instruction (anti-shortcut rules)
   ├── context_pack.formatted_context (evidencia RAG)
   ├── predecessor_context (PhaseHistory context)
   ├── recent_turns (últimos turnos formateados)
   ├── style_directive (ConversationStyleRouter)
   ├── cognitive_profile_block
   └── user_query
        │
        ▼
[chat.py:2140] _resolve_chat_backend()          --> [BYPASS: calcula // 4 solo para cambiar provider]
        │
        ▼
[structured_pipeline.py:1695] _stream_tokens()  --> [BRECHA C3: Despacha strings al LLM sin guard]
        │
        ▼
[multi_fallback.py:180] MultiFallbackBackend.stream()
        │
        ▼
[Provider Cloud: Cerebras / Groq / Gemini]      --> [DESPACHO EFECTIVO AL LLM]
```

### 5.2. Inventario de Superficies de Inflación Post-Retrieval

| Superficie | Ubicación en Código | Mecanismo de Inflación | Límite Actual | Estado de Protección |
|---|---|---|:---:|:---:|
| **Formatted Context (RAG)** | `chat.py:1975` | Evidencia expandida + tags XML | 5,000 tok en expander | **ACOTADO PARCIAL** (tags no medidos) |
| **Historial de Turnos** | `chat.py:2080` | `_CONV_TURN_BUFFER` | 12,000 chars (~3,000 tok) | **DESBORDABLE** (no coordinado con RAG) |
| **Directivas Pedagógicas** | `structured_pipeline.py` | Reglas de andamiaje y fading | ~600 tok | **SIN LÍMITE FORMAL** |
| **Memoria Mem0** | `chat.py:2025` | Recuerdos heurísticos | 2 ítems (~250 tok) | **ACOTADO HEURÍSTICO** |
| **Session Digest** | `chat.py:1623` | KCs con lucha de sesión previa | ~300 tok | **ACOTADO FIJO** |
| **Style Directives** | `chat.py:2040` | Router de tono socrático | ~150 tok | **SIN LÍMITE FORMAL** |
| **Anti-Shortcut Blocks** | `contract.py` | Instrucciones de protección | ~400 tok | **SIN LÍMITE FORMAL** |
| **System Prompt Base** | `contract.py` | Definición de rol y rúbrica | ~500 tok | **ESTÁTICO** |
| **Prompt Total Terminal** | `structured_pipeline.py:1695` | Concatenación de todas las anteriores | **NINGUNO** | **DESPROTEGIDO (FAIL-OPEN)** |

---

## 6. Clasificación de Fallbacks y Garantías Fail-Closed

Se evaluaron los 9 escenarios operacionales de contingencia para determinar si el sistema preserva la integridad pedagógica:

| Escenario Operacional | Comportamiento Observado en Runtime | Clasificación | Evidencia en Código |
|---|---|:---:|---|
| **Retrieval devuelve 0 chunks** | Emite evento SSE `abstention` o reutiliza deictic pack verificado sin alucinar | **SAFE / FAIL-CLOSED** | `chat.py:1955` y `_LAST_EPISTEMIC_PACK` |
| **SectionExpander devuelve 0** | Mantiene chunks semilla originales; si son 0, activa abstención socrática | **SAFE / FAIL-CLOSED** | `section_expander.py:145` |
| **Citations existen sin evidencia** | El pipeline descarta citas huérfanas antes del renderizado de respuesta | **SAFE** | `evidence_assembler.py:88` |
| **Contexto total supera techo** | Concatena todo y conmuta dinámicamente de Groq a Gemini para evitar error 429 | **UNBOUNDED / FAIL-OPEN** | `chat.py:2140` (`_resolve_chat_backend`) |
| **Provider rechaza el prompt (400)** | `MultiFallbackBackend` captura excepción y escala al siguiente proveedor | **SAFE** | `multi_fallback.py:195` |
| **Provider agota timeout (>60s)** | Cancela generador, activa circuit breaker y conmuta a provider secundario | **SAFE** | `router.py:310` |
| **Falla total de red externa** | Cascada completa cae en `OfflinePedagogicalBackend` determinista local | **SAFE / FAIL-CLOSED** | `multi_fallback.py:245` |
| **Conmutación entre providers** | Descarta buffer parcial generado para evitar respuestas truncadas incoherentes | **SAFE** | `router.py:285` |
| **Detección de PII / Inyección** | `DataSanitizer` aborta la petición en el primer milisegundo antes de RAG | **SAFE / FAIL-CLOSED** | `chat.py:2058` |

---

## 7. Chokepoint Técnico Recomendado para Enforzamiento de C3

El punto arquitectónicamente óptimo y seguro para ubicar el interceptor terminal del contrato C3 (una vez adjudicadas las decisiones) es:

```text
StructuredResponsePipeline._stream_tokens()
Ubicación: src/study_engine/pedagogy/structured_pipeline.py (línea ~1695)
```

### Justificación Técnica:
1. **Punto de no retorno**: Es el último método síncrono antes de entregar el payload al adaptador de streaming (`self.llm.stream(...)`).
2. **Visibilidad completa**: En este punto, todos los componentes (system prompt, evidencia RAG, historial, memoria y directivas pedagógicas) ya han sido completamente renderizados a texto.
3. **Independencia del transporte**: Protege tanto las llamadas HTTP de streaming SSE de FastAPI como las invocaciones en batch o runners de consola.
4. **Cero bypass posible**: Ninguna rama de ejecución de `generate_phased_response()` puede alcanzar el backend sin atravesar `_stream_tokens()`.

---

## 8. Criterio de Éxito: Respuestas Epistémicas a las 10 Preguntas Obligatorias

### 1. ¿Qué es TALOS V1?
Es el núcleo fundacional epistémico y pedagógico de TALOS, diseñado para la enseñanza rigurosa de seguridad informática mediante Knowledge Components atómicos, modelado probabilístico determinista de maestría del estudiante (BKT), repaso espaciado (SM-2), retrieval documental estricto y andamiaje socrático con prevención de fuga de respuestas.

### 2. ¿Está terminado?
Sí. El diseño algorítmico, conceptual y pedagógico de V1 está completo y congelado. Los trabajos actuales sobre V1 no añaden funcionalidades, sino que certifican rigurosamente su aseguramiento de calidad (Gate B Assurance).

### 3. ¿Qué significa "frozen"?
Significa que sus contratos Hoare, modelos de datos, fórmulas BKT, catálogo de KCs y esquemas relacionales están protegidos contra modificaciones arbitrarias o rediseños arquitectónicos.

### 4. ¿Qué falta para cerrar formalmente Gate B?
Completar el cierre y certificación material de los tres criterios restantes:
- C3: Adjudicar las decisiones humanas D_C3_1 a D_C3_3 e implementar el Hard Context Ceiling terminal pre-LLM;
- C4: Certificar el aislamiento multi-curricular en entornos concurrentes;
- C5: Formalizar la compuerta de abstención estricta y confianza epistémica.

### 5. ¿Qué es TALOS 1.5?
Es el área de evolución prevista / arquitectura candidata de plataforma e infraestructura de runtime (memoria longitudinal, control presupuestario de contexto, enrutamiento multi-cloud USD 0 y conectores de evidencia) destinada a que el Core V1 opere en sesiones reales de escritorio. Sus componentes concretos todavía están sujetos a investigación, decisión y validación.

### 6. ¿Por qué no es V2?
Porque 1.5 no incluye la observabilidad de prácticas externas en laboratorios (VMs, CTFs, terminal) ni altera el modelo cognitivo oficial. 1.5 es puramente el sustrato técnico propuesto para sostener a V1.

### 7. ¿Qué es TALOS V2?
Es el futuro Cuaderno de Laboratorio y Práctica Técnica (`FUTURE / NOT IMPLEMENTED`). Su objetivo conceptual es capturar telemetría de herramientas externas de seguridad, evaluarla socráticamente y rastrearla en un Shadow BKT experimental antes de promoverla al BKT oficial.

### 8. ¿Qué ya fue investigado?
La arqueología de memoria y runtime en CP104, la arqueología de frontera V1.5 → V2 en CP105 con su inventario de capacidades y gap analysis, y el diagnóstico adversarial y de readiness de C3 en CP103 y CP106.

### 9. ¿Qué todavía necesita decisión humana?
- Las decisiones de contrato de C3: Perímetro de control (**D_C3_1**), Comportamiento ante overflow (**D_C3_2**) y Método de medición (**D_C3_3**).
- Las decisiones de arquitectura de plataforma V1.5 (**D105-01 a D105-08**), que se evaluarán tras el cierre de Gate B.

### 10. ¿Cuál es el próximo checkpoint?
El próximo checkpoint planificado en la secuencia canónica es:
- **CP107**: Auditoría y certificación de **C4 (Multi-Curriculum Isolation)**, manteniendo la secuencia formal de cierre de criterios de Gate B.

---

## 9. Integridad y Trazabilidad

### 9.1. Integridad de la Base de Datos
- **SHA-256 `data/web_state/knowledge_store.db` (Antes)**:  
  `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1`
- **SHA-256 `data/web_state/knowledge_store.db` (Después)**:  
  `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1`
- **Variación de Datos**: `DATABASE_CHANGES = 0` (Bit-for-bit preservado).

### 9.2. Estado de Control de Versiones
- **Archivos Creados / Corregidos**:
  - `docs/TALOS_ROADMAP_V1_V1_5_V2.md`
  - `checkpoints/106-cierre-v1-c3.md`
- **Archivos Modificados**:
  - `checkpoints/index.md`

---

## 10. Bloque Final Estandarizado de Certificación

```text
CP106_STATUS=AUDIT_COMPLETED
C3_STATUS=BLOCKED / ASSURANCE_BLOCKER (HUMAN_DECISION_PENDING)
DATABASE_CHANGES=0
DB_SHA_BEFORE=fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1
DB_SHA_AFTER=fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1
FILES_CREATED=docs/TALOS_ROADMAP_V1_V1_5_V2.md, checkpoints/106-cierre-v1-c3.md
FILES_MODIFIED=checkpoints/index.md
HUMAN_DECISIONS_REQUIRED=D_C3_1, D_C3_2, D_C3_3
NEXT_CHECKPOINT=CP107
```
