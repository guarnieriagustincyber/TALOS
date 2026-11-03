# CP110 — Auditoría Técnica de Assurance: C5 (Abstention / Trust Gate)

**Fecha:** 2026-10-02  
**Estado de Entrada:**
```text
V1 CORE = CERTIFIED / FROZEN
C1 = PASS / CLOSED
C2 = PASS / CLOSED
C3 = PASS / CLOSED (4761 tokens efectivos, triple chokepoint)
C4 = PASS / CLOSED (Aislamiento curricular verificado)
C5 = BLOCKED / PENDING
GATE B = NOT YET CLOSED
```
**Estado de Salida:**
```text
CP110_STATUS = COMPLETED
C5_STATUS = DECISION READY
GATE B = BLOCKED (Requiere implementación post-adjudicación)
DATABASE_CHANGES = 0
DB_SHA = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1
```

---

## 1. Resumen Ejecutivo

Durante el Checkpoint CP110 se ejecutó una auditoría exhaustiva, **estrictamente de solo lectura (READ-ONLY)**, sobre el criterio **C5 — Abstention / Trust Gate** de TALOS Gate B.

El objetivo fue verificar si TALOS dispone actualmente de una barrera epistemológica y operacional suficiente para reconocer cuándo la evidencia disponible no permite responder de forma confiable, abstenerse determinísticamente de llamar al LLM, e impedir alucinaciones no fundamentadas, preservando las garantías de aislamiento (C1, C4), autorización (C2) y presupuesto (C3).

### Conclusión Principal de la Auditoría
TALOS **no cuenta actualmente con un criterio C5 cerrado ni robusto**. Si bien existen mecanismos valiosos de mitigación parcial (enmiendas E2, E5, E25, guardas léxicas y el `StreamCitationBuffer` de la Enmienda E-UX1), la auditoría descubrió **cinco bypasses críticos** que violan el principio fundamental `NO_AUTHORIZED_SUFFICIENT_EVIDENCE → NO_UNGROUNDED_LLM_ANSWER` en el runtime de producción (`chat.py` / `StructuredResponsePipeline`).

El estado oficial adjudicado para C5 al cierre de CP110 es **`DECISION READY`**: disponemos de evidencia ejecutable, empírica y reproducible de cada frontera de confianza, modo de falla y bypass, permitiendo elevar a la autoridad humana el paquete de decisiones contractuales para su posterior remediación en CP111.

---

## 2. Mapa de Rutas y Arqueología Arquitectónica

La auditoría reveló la coexistencia de **dos arquitecturas desalineadas** en el repositorio:

```text
========================================================================================
ARQUITECTURA A: Session / Hexagonal Core (V1 Baseline - tests aislados)
========================================================================================
User Query → SessionOrchestrator → RetrievalPort (RetrievalService) → EvidenceSelector 
  → EvidenceCoverageEvaluator → EvidenceEngine → ContextPacker → TutorPort (LLM) 
  → AuditPort (S4.4 ForensicAuditor) → SessionResult(ABSTAINED if audit rejected)

========================================================================================
ARQUITECTURA B: Web / Streaming Runtime (Ruta Real de Producción en chat.py)
========================================================================================
User Query
    ↓
DataSanitizer (PII Guard)
    ↓
_prepare_chat_context
    ├── QueryRewriter (Descontextualización / Deícticos)
    ├── _is_non_curricular_intent (Regex _NON_CURRICULAR_INTENT_RE + Match KC)
    ├── _assemble_epistemic_context
    │     ├── Scope Allowlist (L3 Manifest / C2-C4)
    │     ├── KnowledgeStore.search (BM25 FTS5 + Vector Cosine)
    │     ├── ContentRegistry (Filter Presentation / Anti-leakage)
    │     ├── SectionExpander (Expansión de contexto)
    │     └── Enmienda E2: if not raw_chunks → EpistemicContextPack(abstained=True)
    ├── ConversationState Classifier (Inercia conversacional CAL §3.2)
    └── should_abstain (Rescate de _LAST_EPISTEMIC_PACK en seguimiento)
    ↓
StructuredResponsePipeline.generate_phased_response
    ├── Pre-LLM Guard (Enmienda E5 & E25): if pack.abstained and not is_offline_oracle
    ├── C3 Hard Budget Guard (Triple Chokepoint: 4761 tokens)
    ├── LLM Token Streaming (MultiFallbackBackend: Groq → Gemini → Cloudflare → OfflineOracle)
    ├── SocraticGuard (Anti-shortcut / Code leak token-by-token)
    └── Post-Stream S4.4 Forensic Audit (Asíncrono, NO bloquea tokens ya emitidos)
    ↓
StreamCitationBuffer (Enmienda E-UX1)
    └── Stripping / Rewrite de citas [E99] huérfanas en streaming
```

### Divergencia Crítica entre Arquitecturas
1. **`RetrievalService` y `ContextCompiler`**: Los tests históricos de "OOD abstention = 100%" (`test_relevance_gate_regression.py` y `test_abstention_rate.py`) evaluaban componentes aislados de la Arquitectura A (`RetrievalService`, `ContextCompiler`, `EpistemicController`). **Ninguno de estos componentes es utilizado en la ruta web de producción (`chat.py`)**.
2. **`chat.py`** implementa su propio pipeline basado en `KnowledgeStore.search`, `_assemble_epistemic_context`, y `StructuredResponsePipeline`.

---

## 3. Arqueología de Mecanismos de Abstención Existentes

| Componente | Archivo / Función | Tipo de Decisión | Condición de Activación | Consecuencia Observada |
| :--- | :--- | :--- | :--- | :--- |
| **PII Guard** | `chat.py:chat_query` | Determinista (Regex) | Presencia de credenciales / PII | Emite `phase="pii_guard"`, bloquea llamada al LLM |
| **Non-Curricular Intent Gate** | `chat.py:_is_non_curricular_intent` | Heurística (Regex `_NON_CURRICULAR_INTENT_RE` + Match KC) | Palabras clave: opinión, fútbol, película, receta, chiste, videojuego, etc., sin match en catálogo KC | Setea `abstained=True, reason="Consulta fuera del ámbito curricular..."` |
| **Scope Authorization Guard** | `chat.py:_assemble_epistemic_context` | Determinista (L3 Manifest) | Sin fuentes autorizadas en el scope activo | Setea `abstained=True, reason="NO_AUTHORIZED_SOURCES_IN_SCOPE"` |
| **Presentation Filter** | `chat.py:filter_presentation` | Determinista (`ContentRegistry`) | Chunks contienen soluciones protegidas activas | Setea `abstained=True, reason="QUERY_OUT_OF_SCOPE"` |
| **Zero-Chunks Gate (Enmienda E2)** | `chat.py:_assemble_epistemic_context:1289` | Determinista (`not raw_chunks`) | 0 fragmentos canónicos recuperados | Setea `abstained=True, reason="QUERY_OUT_OF_SCOPE"` |
| **Pre-LLM Physical Gate (E5/E25)** | `structured_pipeline.py:1622` | Determinista (`context_pack.abstained`) | `context_pack.abstained == True and not is_offline_oracle` | Emite `StreamEvent(event_type="abstention")` como único evento, 0 llamadas a LLM |
| **Coverage Guard (Lexical)** | `knowledge_store.py:fts_search` | Heurística léxica en FTS5 | Términos de query no cubiertos en chunk | Descarta filas candidatas en búsqueda BM25 |
| **StreamCitationBuffer (E-UX1)** | `citation_validator.py` | Determinista sobre stream | LLM emite `[E#]` inexistente en chunks | Reemplaza por `[ref. no verificada]` o suprime etiqueta |
| **Forensic Auditor (S4.4)** | `structured_pipeline.py:1947` | Híbrida (Reglas + NLI) | Ejecuta post-hoc tras stream | Emite `event_type="audit_verdict"`, **no revoca tokens ya emitidos** |
| **Conversational Rescuer** | `chat.py:1889` / `conversation_state.py` | Heurística conversacional | Turno de seguimiento con 0 chunks y `has_fallback_pack=True` | **Inyecta context pack del turno anterior**, evitando la abstención |

---

## 4. Contrato Real Actual de Abstención

1. **¿Qué significa abstenerse hoy en TALOS?**  
   En la ruta web (`chat.py`), abstenerse significa emitir inmediatamente un payload SSE con `event_type: "abstention"`, código de abstención y sugerencia pedagógica, **sin invocar al LLM** (0 llamadas a API, 0 tokens generados).
2. **¿Cuándo se activa actualmente?**  
   Únicamente bajo cuatro condiciones discretas:
   - Coincidencia con la regex cerrada de temas no curriculares (Star Wars, fútbol, recetas, chistes).
   - Ausencia total de fuentes autorizadas en el cuaderno (fallo de autorización L3 / C2).
   - Referencia deíctica ambigua en multi-turn sin antecedente resoluble.
   - **Cero chunks (`len(raw_chunks) == 0`)** devueltos por el motor de búsqueda tras los filtros.
3. **¿Qué NO activa la abstención?**  
   - Chunks con score de relevancia extremadamente bajo (cualquier chunk devuelto por vector/BM25 es aceptado).
   - Chunks irrelevantes que coinciden por términos comunes en español (ej. "general", "teoría", "datos").
   - Preguntas fuera de dominio (OOD) no contempladas en la regex (ej. física cuántica, biología, mecánica).
   - Evidencia contradictoria entre autores autorizados.
   - Alucinaciones del LLM durante el streaming (el auditor forense corre post-hoc).
   - Fallos técnicos de retrieval (la excepción no manejada provoca un fail-open sin contexto).

---

## 5. Trust Boundaries (Fronteras de Confianza)

```text
[UNTRUSTED] Raw User Query
    │
    ▼ [Frontera 1: Sanitización & PII]
    ├─ Entrada: Texto crudo del usuario.
    ├─ Validación: Regex de PII / API keys.
    ├─ Falla: FAIL-CLOSED (Emite aviso de seguridad, bloquea LLM).
    │
    ▼ [Frontera 2: Intención No Curricular]
    ├─ Entrada: Query normalizada + Catálogo KC.
    ├─ Validación: Regex heurística (`_NON_CURRICULAR_INTENT_RE`) y ausencia de match KC.
    ├─ Falla: FAIL-OPEN (Cualquier OOD que no esté en la regex pasa a retrieval).
    │
    ▼ [Frontera 3: Autorización de Fuentes (C2 / C4)]
    ├─ Entrada: Scope ID (Notebook o Carpeta).
    ├─ Validación: L3 Manifest allowlist (`_source_ids_for_notebook`).
    ├─ Falla: FAIL-CLOSED (Si no hay fuentes autorizadas, abstiene).
    │
    ▼ [Frontera 4: Búsqueda y Selección de Evidencia]
    ├─ Entrada: Query + Fuentes autorizadas.
    ├─ Validación: FTS5 BM25 + Vector Search + Anti-ruido (0.87 / 0.78).
    ├─ Falla: FAIL-OPEN parcial (Ruido semántico y términos genéricos admiten chunks irrelevantes).
    │
    ▼ [Frontera 5: Evaluación de Suficiencia Epistémica]
    ├─ Entrada: Chunks recuperados.
    ├─ Validación: ÚNICAMENTE `len(raw_chunks) > 0`.
    ├─ Falla: CRITICAL FAIL-OPEN (NO existe chequeo de suficiencia ni score mínimo; 1 chunk débil habilita LLM).
    │
    ▼ [Frontera 6: Pre-LLM Physical Gate (E5 / E25)]
    ├─ Entrada: `EpistemicContextPack`.
    ├─ Validación: `context_pack.abstained == True and not is_offline_oracle`.
    ├─ Falla: FAIL-CLOSED para backends normales; BYPASS para `OfflinePedagogicalBackend`.
    │
    ▼ [Frontera 7: Presupuesto C3]
    ├─ Entrada: Payload ensamblado previo al LLM.
    ├─ Validación: Límite estricto de 4.761 tokens estimados.
    ├─ Falla: FAIL-CLOSED (Pruning determinístico o aborto seguro).
    │
    ▼ [Frontera 8: LLM / Generación Streaming]
    ├─ Entrada: System prompt + User prompt con evidencia.
    ├─ Falla: Emisión de afirmaciones no fundamentadas o citas huérfanas en streaming progresivo.
    │
    ▼ [Frontera 9: Post-Generación & Buffer de Citas]
    ├─ Entrada: Tokens emitidos.
    ├─ Validación: `StreamCitationBuffer` detecta `[E#]` huérfanas; Auditoría S4.4 post-hoc.
    ├─ Falla: FAIL-OPEN (El texto alucinado ya fue entregado al alumno; la cita se suprime pero la afirmación queda).
```

---

## 6. Resultados de las Fixtures de Auditoría (C5-A a C5-J)

Todas las fixtures se ejecutaron contra el entorno vivo y el store oficial de TALOS (`knowledge_store.db`):

| Fixture | Caso Evaluado | Query / Vector de Prueba | Comportamiento Observado | Veredicto |
| :--- | :--- | :--- | :--- | :--- |
| **C5-A** | OOD con Regex | "Dame una receta de empanadas salteñas" | Bloqueado por `_is_non_curricular_intent`, 0 chunks, 0 llamadas a LLM | **PASS** |
| **C5-A** | OOD con Regex pero match léxico | "¿Quién ganó el último partido de fútbol?" | `_is_non_curricular_intent` detecta OOD; pero en retrieval directo encuentra 1 chunk de un ejercicio ("partido de fútbol") | **PASS en chat / FAIL en ensamble directo** |
| **C5-A** | OOD sin Regex (Biología) | "¿Cómo se realiza la fotosíntesis en las plantas C4?" | 0 hits en FTS5 y vectores; `len(chunks)==0` → abstiene por Enmienda E2 | **PASS (por casualidad léxica)** |
| **C5-A** | OOD sin Regex (Física) | "Explicame la teoría de la relatividad general de Einstein" | Recupera 15 chunks de Joyanes (por "teoría" y "general"); `abstained=False` → **Llama al LLM** | **FAIL (Bypass OOD)** |
| **C5-B** | Zero Evidence | `concepto_inexistente_completamente_ausente_123456789` | 0 chunks; `abstained=True`, reason `QUERY_OUT_OF_SCOPE`, 0 llamadas a LLM | **PASS** |
| **C5-C** | Low Relevance | "dinámica de fluidos computacional y turbulencia" | Si devuelve 0 chunks abstiene; pero si devuelve chunks con score bajo, los admite sin filtrar | **PARTIAL / FAIL** |
| **C5-D** | Unauthorized Evidence | "transmisión de datos teleco ancho de banda nyquist shannon" | Aísla fuentes de Telecomunicaciones, pero recupera chunks autorizados que tienen las palabras "datos" y "banda" | **PARTIAL (Aísla fuente, admite ruido)** |
| **C5-E** | Conflicting Evidence | Chunks con afirmaciones contradictorias sobre Round Robin | No existe detector de conflicto; concatena ambas al prompt y delega al LLM | **FAIL (Delegación ciega al LLM)** |
| **C5-F** | Citation Mismatch | Texto con citas huérfanas `[E99]` | `StreamCitationBuffer` suprime la etiqueta `[E99]`, pero emite la prosa alucinada al usuario | **FAIL (No previene la alucinación)** |
| **C5-G** | Retrieval Failure | Excepción forzada en `KnowledgeStore.search` | Retorna `None, []`; `context_pack is None` bypassa el check de abstención y **llama al LLM sin contexto** | **CRITICAL FAIL (Fail-Open)** |
| **C5-H** | Provider Failure Fallback | Fallo en proveedores primarios → Cascada a `OfflinePedagogicalBackend` | Emite respuesta enlatada con cita ficticia `[E1]` afirmando falsamente que el tema está en el cuaderno | **CRITICAL FAIL (Bypass Epistémico)** |
| **C5-I** | Fallback Bypass Universal | `context_pack.abstained=True` contra todos los backends | Respeta la abstención en backends normales; **ignora la abstención en `OfflinePedagogicalBackend`** | **CRITICAL FAIL (Bypass Offline)** |
| **C5-J** | Zero Chunks + Fallback Citations | Query sin chunks | `if not raw_chunks` retorna antes de armar `citations_formatted`. No hay fuga de citas huérfanas | **PASS (Protegido por E2)** |

---

## 7. Bypasses y Vulnerabilidades Demostradas

### Bypass 1: Catastrophic Retrieval Failure Fail-Open (`CRITICAL`)
* **Ubicación:** `study_engine/web/routes/chat.py:1322–1325` y `structured_pipeline.py:1622`.
* **Mecanismo:** Si `store.search` o `SectionExpander` lanzan una excepción no capturada (ej. bloqueo de SQLite, timeout, fallo de I/O), `_assemble_epistemic_context` captura el error y retorna `None, []`.
* **Consecuencia:** En `pipeline.generate_phased_response`:
  ```python
  if context_pack is not None and getattr(context_pack, "abstained", False) and not is_offline_oracle:
  ```
  Al ser `context_pack is None`, la condición evalúa a `False`. El pipeline continúa su ejecución, compila un prompt con la pregunta del usuario pero **sin ninguna evidencia**, e invoca al LLM para responder desde memoria paramétrica.
* **Evidencia Ejecutada (`scratch/probe_retrieval_failure.py`):**
  ```text
  LLM called when context_pack is None: True
  Tokens streamed: "Respondo sin evidencia!"
  ```

### Bypass 2: Offline Pedagogical Oracle Bypass (`CRITICAL`)
* **Ubicación:** `structured_pipeline.py:1621–1622` y `chat.py:2244`.
* **Mecanismo:** El código contiene explícitamente: `and not is_offline_oracle`.
* **Consecuencia:** Si el backend activo es `OfflinePedagogicalBackend` (o si `MultiFallbackBackend` cae a él por timeout de red), el trust gate queda completamente desactivado. El oráculo emite respuestas enlatadas con `generator_abstained=False` y citas `[E1]` inventadas, incluso ante preguntas de biología o física ajenas al cuaderno.
* **Evidencia Ejecutada (`scratch/audit_c5_live.py` - Probe 4):**
  ```text
  Pipeline with OfflinePedagogicalBackend on abstained pack:
    Token events count: 101
    Emitted text: "Conforme a las fuentes autorizadas de tu plan curricular [E1]..."
  ```

### Bypass 3: Semantic OOD / Weak Chunks Infiltration (`HIGH`)
* **Ubicación:** `chat.py:_prepare_chat_context` y `_assemble_epistemic_context`.
* **Mecanismo:** El filtro de intención no curricular depende de una lista fija de expresiones regulares (`_NON_CURRICULAR_INTENT_RE`: fútbol, película, receta, chiste). Cualquier consulta fuera de dominio que no coincida con esas palabras (ej. teoría de la relatividad, fotosíntesis, mecánica, medicina) ingresa a búsqueda vectorial y BM25.
* **Consecuencia:** Si los textos autorizados contienen palabras comunes (como "teoría", "general", "datos"), el motor devuelve chunks con score alto. Como `_assemble_epistemic_context` solo valida `if not raw_chunks:`, al haber al menos 1 chunk marca `abstained=False`. El LLM recibe chunks irrelevantes y responde preguntas fuera del programa.

### Bypass 4: Conversational Inertia Epistemic Leakage (`HIGH`)
* **Ubicación:** `study_engine/web/routes/chat.py:1889–1905` y `conversation_state.py`.
* **Mecanismo:** En una conversación activa, si el alumno realiza una consulta corta (≤ 6 palabras) que no contiene un corte explícito de tema ("cambiando de tema"), `classify_conversation_state` la clasifica como `ConversationState.AMBIGUOUS_FOLLOWUP`.
* **Consecuencia:** `should_abstain()` dictamina que **nunca se debe abstener** si existe un paquete previo (`has_fallback_pack=True`). `chat.py` rescata el `EpistemicContextPack` del turno previo. Si el alumno venía hablando de paginación y pregunta "¿Qué es la fotosíntesis oxigénica?", el sistema inyecta la evidencia de paginación y le pide al LLM responder.
* **Evidencia Ejecutada (`scratch/probe_inertia_leak.py`):**
  ```text
  Query: '¿Qué es la fotosíntesis oxigénica?' (words=5)
    _is_non_curricular_intent: False
    classified state: ConversationState.AMBIGUOUS_FOLLOWUP
    should_abstain: False (reason=None)
    -> WOULD REUSE PREVIOUS PACK: True
  ```

### Bypass 5: Streaming Post-Hoc Audit Decoupling (`MEDIUM`)
* **Ubicación:** `study_engine/web/routes/chat.py:2378–2416` y `citation_validator.py`.
* **Mecanismo:** Los tokens generados por el LLM se transmiten inmediatamente al frontend vía SSE (`phase_token`). `StreamCitationBuffer` detecta citas a fuentes no existentes (ej. `[E99]`) y las suprime o reemplaza por `[ref. no verificada]`, pero no interrumpe el flujo.
* **Consecuencia:** La auditoría forense S4.4 (`audit_generation_payload`) se ejecuta **después de que el streaming ha terminado**. Su veredicto (`audit_verdict`) se envía al final del stream como evento informativo; para ese momento, el estudiante ya leyó la afirmación alucinada en su pantalla.

---

## 8. Casos de Sobreconfianza (Overconfidence Probes)

Se diseñaron e implementaron 5 casos de prueba de sobreconfianza (`query plausible + weak evidence`) para verificar si TALOS distingue `RELATED` de `SUFFICIENT`:

| Caso | Hipótesis Evaluada | Query | Chunks | Término Ausente | Veredicto Observado |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **OC-1** | Cobertura parcial | "¿Cómo mitigar el ataque Rowhammer en memorias DDR4 según Tanenbaum?" | 15 | "rowhammer" ausente | `ADMITTED (Weak Evidence)` |
| **OC-2** | Concepto relacionado sin demostración | "Demostrá por qué el problema de la parada implica que el banquero de Dijkstra es NP-completo" | 15 | "np-completo" ausente | `ADMITTED (Weak Evidence)` |
| **OC-3** | Cruce indebido de temas | "¿Cómo afecta el algoritmo de Nagle al latency de paginación en memoria virtual?" | 15 | "nagle" ausente | `ADMITTED (Weak Evidence)` |
| **OC-4** | Causalidad falsa con estadística inventada | "¿Por qué el cambio de Linux 2.4 a Linux 2.6 redujo la fragmentación externa en un 42.5%?" | 13 | "42.5%" ausente | `ADMITTED (Weak Evidence)` |
| **OC-5** | Información anacrónica ausente | "¿Cuál fue el fallo de seguridad en Linux CVE-2024-1086 según el libro de Silberschatz?" | 15 | "cve-2024-1086" ausente | `ADMITTED (Weak Evidence)` |

**Resultado:** En el 100% de los casos (5/5), TALOS admitió la consulta y ensambló un payload con 13 a 15 fragmentos débiles o periféricos. **TALOS no distingue actualmente entre evidencia relacionada y evidencia suficiente.**

---

## 9. Auditoría de la Evidencia Histórica ("OOD Abstention = 100%")

La afirmación histórica de que TALOS contaba con `OOD abstention = 100%` fue investigada a nivel de código y trazabilidad:

1. **Origen:** La métrica proviene del test `tests/integration/test_relevance_gate_regression.py:108` (`test_relevance_gate_blocks_all_12_ood_queries`), implementado en el Hito 6 Paso 2.
2. **Perímetro real:** Evaluó exclusivamente la función `RetrievalService.retrieve_evidence` sobre una lista sintética de 12 consultas OOD (gastronomía, extraterrestres, etc.) utilizando embeddings ONNX locales y un threshold $\theta = 0.84$.
3. **Desconexión con Producción:**
   - `RetrievalService` **no es invocado por la API web (`chat.py`)**.
   - No evaluó el flujo end-to-end con LLMs ni el streaming SSE.
   - No evaluó queries OOD con vocabulario superpuesto (ej. conceptos teóricos o palabras comunes en español).
   - No evaluó el comportamiento multi-turno ni el fallback de proveedores.
4. **Conclusión:** La cifra histórica de 100% es un artefacto de un benchmark unitario aislado sobre un componente desvinculado del runtime de producción. En el sistema real, la tasa de abstención efectiva ante consultas OOD no catalogadas en la regex es **prácticamente 0%** si la búsqueda recupera al menos un fragmento por coincidencia léxica.

---

## 10. Relación con Criterios Previos (C1–C4)

* **C1 (Identidad y Trazabilidad):** Se mantiene. Los identificadores de cuaderno, sesión y fases se preservan.
* **C2 (Autorización L3):** Se mantiene. La lista de fuentes autorizadas por cuaderno (`_source_ids_for_notebook`) se aplica estrictamente en `_assemble_epistemic_context`. Si una consulta solo tiene evidencia en fuentes no autorizadas, esas fuentes no entran al contexto.
* **C3 (Presupuesto de Contexto):** Se mantiene plenamente. Los tres chokepoints certificados en CP109 garantizan que ninguna llamada al LLM exceda los 4.761 tokens efectivos, incluso cuando se produce una alucinación o un bypass de C5.
* **C4 (Aislamiento Curricular):** Se mantiene a nivel de frontera de fuentes. Sin embargo, si una query de otro currículo contiene términos genéricos que existen en el currículo actual, se filtran fragmentos locales irrelevantes, rompiendo la suficiencia epistemológica sin romper el aislamiento de fuentes.

---

## 11. Métricas Obligatorias Observadas

```text
Total queries auditadas: 20
Queries con evidencia suficiente verificada: 2
Abstenciones correctas observadas: 8
Abstenciones incorrectas / falsos positivos: 0
Respuestas no fundamentadas admitidas al LLM (Overconfidence + OOD): 8
Abstenciones por OOD (Regex): 2 / 2 (100%)
Abstenciones por OOD (Semántico sin regex): 1 / 3 (33% - solo cuando hits=0)
Abstenciones por Zero Evidence: 2 / 2 (100%)
Comportamiento ante Low Relevance: FAIL-OPEN (Admite si hits > 0)
Comportamiento ante Conflicting Evidence: FAIL-OPEN (Delega ciegamente al LLM)
Comportamiento ante Unauthorized Evidence: PASS en aislamiento de fuentes / FAIL en filtración de ruido local
Comportamiento ante Retrieval Failure: CRITICAL FAIL-OPEN (Invoca LLM sin contexto)
Comportamiento ante Provider Fallback: CRITICAL FAIL-OPEN (Oráculo offline emite [E1] falso)
Llamadas al LLM con evidencia insuficiente: 8 / 10 casos no fundamentados
```

---

## 12. Paquete de Decisión Humana (Adjudicación de C5)

Para cerrar C5 en el próximo checkpoint, se somete a la decisión del arquitecto humano la siguiente matriz técnica:

| Decisión | Opción A | Opción B (Recomendada) | Opción C | Trade-off / Impacto |
| :--- | :--- | :--- | :--- | :--- |
| **D_C5_1: Perímetro de Abstención** | Solo abstener si `raw_chunks == 0` (Estado actual) | **Abstener si `raw_chunks == 0` O si el score máximo de relevancia es inferior al umbral mínimo $\theta$** | Abstener mediante clasificador LLM previo | La Opción B cierra el bypass semántico con 0 costo de red y latencia despreciable. |
| **D_C5_2: Sufficiency Gate** | Presencia de ≥ 1 chunk (Estado actual) | **Validación de cobertura de términos clave de la query en los chunks candidatos (Coverage Guard Pre-LLM)** | Evaluación NLI completa previa a la generación | La Opción B impide que chunks con palabras accidentales ("teoría", "datos") habiliten respuestas OOD. |
| **D_C5_3: Conflicto de Evidencia** | Delegar al LLM (Estado actual) | **Exponer el conflicto explícitamente en el prompt obligando al tutor a contrastar ambas fuentes** | Abstención total ante conflicto | La Opción B preserva el valor socrático y pedagógico sin inventar consenso inexistente. |
| **D_C5_4: Semántica de Fallo Técnico** | Fallar abierto llamando al LLM sin contexto (Estado actual) | **Fail-Closed Estricto: cualquier error de retrieval emite evento `error` o `abstention` técnico, nunca invoca al LLM** | Reintentar indefinidamente | La Opción B garantiza la inviolabilidad del grounding epistémico. |
| **D_C5_5: Provider Fallback & Offline Oracle** | Mantener bypass de oráculo offline (Estado actual) | **Hacer el Trust Gate universal: NINGÚN backend (incluyendo el oráculo offline) puede responder si el context pack está abstenido** | Eliminar el oráculo offline | La Opción B elimina la emisión de citas `[E1]` fraudulentas por parte del oráculo offline. |
| **D_C5_6: Inercia Conversacional** | Rescatar siempre el context pack previo si la query es corta (Estado actual) | **Exigir match temático mínimo entre la nueva query y el context pack previo antes de permitir el rescate** | Desactivar el rescate conversacional | La Opción B previene que preguntas OOD cortas hereden contexto técnico ajeno. |

---

## 13. Verificación de Integridad de Base de Datos

* **Estado de Base de Datos:** Intacta. 0 modificaciones.
* **SHA-256 Inicial:** `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1`
* **SHA-256 Final:** `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1`
* **Resultado:** `INTEGRITY_VERIFIED`

---

## 14. Próximo Paso Recomendado

* **Checkpoint:** **`CP111 — Implementación y Blindaje de C5: Abstention / Trust Gate`**.
* **Objetivo:** Implementar las decisiones humanas acordadas (`D_C5_1` a `D_C5_6`), cerrar los 5 bypasses detectados, blindar el fail-closed en fallos técnicos y unificar la barrera epistémica antes del cierre definitivo de Gate B.
