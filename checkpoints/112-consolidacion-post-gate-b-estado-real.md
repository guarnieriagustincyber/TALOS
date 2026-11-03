# CP112-R1 — Normalización Final del Estado Operacional de TALOS

**Tipo:** Corrección y Consolidación de Auditoría Post-Gate B  
**Rol:** Auditor Técnico Senior de Assurance de TALOS  
**Precondición:** CP112 ejecutado / Gate B cerrado (C1–C5 PASS / CLOSED)  
**Estado:** Gate B CLOSED / V1 Core Frozen / Baseline Post-Gate B Establecida  
**Integridad de Datos:** `DATABASE_CHANGES = 0` (`data/web_state/knowledge_store.db` SHA256: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` — `UNCHANGED`)  

---

## 0. Propósito y Separación Formal de Dominios

El presente checkpoint constituye la **versión normalizada oficial (CP112-R1)** que establece la **baseline factual del estado real de TALOS inmediatamente posterior al cierre de Gate B**.

Bajo la regla fundamental:
```text
OBSERVE → TRACE → MEASURE → CORRELATE → CLASSIFY
```
este informe separa estrictamente tres dimensiones que no deben confundirse:

```text
GATE B STATUS
        ↓
C1 / C2 / C3 / C4 / C5 = PASS / CLOSED
(Garantías epistemológicas y contractuales certificadas en sus perímetros)

        ≠

TALOS CAPABILITY COMPLETENESS
        ↓
Existen capacidades implementadas pero desconectadas,
inactivas en runtime o pendientes de completar.

        ≠

FUTURE BACKLOG
        ↓
Trabajo posterior a Gate B (P1–P3) a decidir sobre esta baseline.
```

Asimismo, se delimita con rigor el vocabulario técnico:
* **`IMPLEMENTED`**: El código existe y está estructurado en el repositorio.
* **`CONNECTED`**: El componente está integrado activamente en las rutas de ejecución principales.
* **`EXECUTED`**: El componente se invoca efectivamente en runtime durante las operaciones normales.
* **`VERIFIED`**: Existe evidencia empírica de tests que demuestran su comportamiento en condiciones controladas y adversariales.
* **`CERTIFIED`**: El comportamiento satisface formalmente un contrato normativo de auditoría (e.g. C1–C5 en Gate B).

---

## ARTIFACT A: Inventario Completo de Capacidades

**Escala de Clasificación:**
* **A — `OPERATIONAL / FULLY VERIFIED`**: Implementado, conectado en el flujo productivo y verificado con cobertura de tests.
* **B — `IMPLEMENTED + CONNECTED + PARTIALLY VERIFIED`**: Implementado y conectado, pero con cobertura parcial o umbrales no calibrados empíricamente.
* **C — `IMPLEMENTED BUT DISCONNECTED / OPERATIONALLY INACTIVE`**: Código existente y testeado en aislamiento, pero desconectado de la ruta principal o inactivo en runtime.
* **D — `DEAD / HISTORICAL / UNAVAILABLE`**: Endpoint o componente deprecado, no montado o que retorna rechazo explícito fail-closed.

| ID | Subsistema | Capacidad Auditada | Estado | Ubicación en Código | Ruta Runtime | Evidencia de Test | Dependencias de Datos | Limitación Actual | Reemplazo Histórico | Riesgo Regresión | Siguiente Acción |
| :--- | :--- | :--- | :---: | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **EP-01** | Epistemología | C1 Identity / Grounding | **A** | `retrieval/expansion.py`, `context/c5_trust.py` | `/api/chat/query` | `tests/adversarial/crisol/` | `knowledge_store.db` (chunks) | Requiere chunks canónicos | None | Alto | Mantener |
| **EP-02** | Epistemología | C2 Source Authorization (L3) | **A** | `contracts/l3_manifest.py`, `web/routes/chat.py` | `/api/chat/query` (`_authorized_sources_for_scope`) | `test_c2_l3_integral_shield.py` (6/6) | `l3_authorization_manifest.json` | Restringido a fuentes L3 autorizadas | None | Crítico | Mantener |
| **EP-03** | Epistemología | C3 Hard-Ceiling Budget (Normativo 5000 / Despacho $\le 4761$) | **A** | `context/c3_budget.py`, `pedagogy/structured_pipeline.py` | `generate_phased_response` | `test_c3_hard_ceiling.py` (18/18) | None (in-memory) | Medición conservadora `ceil(len/4)`; margen 5% | Retrieval ceiling previo | Alto | Mantener |
| **EP-04** | Epistemología | C4 Curriculum Isolation | **A** | `web/routes/chat.py`, `storage/knowledge_store.py` | `search`, `_assemble_epistemic_context` | `test_14_cross_notebook_isolation.py` | `notebook_sources` (SQLite) | Requiere `notebook_id` válido | None | Crítico | Mantener |
| **EP-05** | Epistemología | C5 Abstention / Trust Gate | **A** | `context/c5_trust.py`, `web/routes/chat.py` | `sse_generator`, `generate_phased_response` | `test_c5_trust_gate.py` (27/27) | `content_registry` | $\theta = \text{PENDING EMPIRICAL CALIBRATION}$ | Auditoría post-hoc | Crítico | Mantener |
| **EP-06** | Epistemología | S4.4 / Forensic Auditor | **B** | `pedagogy/dialogue_engine.py`, `concept_packet.py` | `/api/pedagogy/episode/.../concept` | `test_s44_*.py` | Chunks recuperados | Activo solo en Socratic Episode | None | Medio | Mantener |
| **EP-07** | Epistemología | Citation Grounding Buffer | **A** | `pedagogy/citation_validator.py` | `sse_generator` (stream buffer) | `test_c5_trust_gate.py` (I7) | None | Depura citas sintéticas `[E99]` en streaming | Post-hoc rewrite | Medio | Mantener |
| **EP-08** | Epistemología | Fail-Closed Architecture (Perímetro C1–C5) | **A** | `web/routes/chat.py`, `structured_pipeline.py` | Rutas de generación auditadas C1–C5 | `test_c5_trust_gate.py` (B, G, H, I, J) | None | Restringido al perímetro auditado de generación | Permissive defaults | Crítico | Mantener |
| **EP-09** | Epistemología | OOD Detection | **B** | `context/c5_trust.py` | `evaluate_epistemic_trust` | `test_fixture_c5_a_ood_detection` | Regex / Stopwords / Vocabulary | Cobertura semántica completa no calibrada empíricamente | Post-LLM refusal | Alto | Mantener / Calibrar en P3 |
| **EP-10** | Epistemología | Conflict Representation | **A** | `context/c5_trust.py` | `evaluate_epistemic_trust` | `test_fixture_c5_e_conflicting_evidence` | Metadatos de fuentes distintas | Perímetro léxico y de metadatos acotado | Silence / Hallucination | Medio | Mantener |
| **RT-01** | Retrieval | FTS5 Lexical Search (BM25) | **A** | `storage/lexical_index.py`, `knowledge_store.py` | `store.search`, `fts_search` | `test_knowledge_store.py` | `chunks_fts` (105.705 rows) | Sensible a stopwords en query | Basic SQL LIKE | Crítico | Mantener |
| **RT-02** | Retrieval | Semantic Vector Search | **C** | `storage/knowledge_store.py`, `retrieval/vector_store.py` | `store.vector_search` (inactivo en runtime) | `test_vector_store.py` (aislado) | `vector_store.db` (287k rows, 1024d) | **Inactivo en runtime por mismatch 1024d vs 384d** | None | Alto | Resolver en P1 |
| **RT-03** | Retrieval | Hybrid Retrieval (RRF) | **B** | `storage/knowledge_store.py:971` | `store.search_hybrid` | `test_knowledge_store.py` | `chunks_fts` + `vector_store.db` | Opera puramente como FTS5 por vector inactivo | Pure BM25 | Alto | Conectar vector |
| **RT-04** | Retrieval | QueryRewriter | **A** | `retrieval/query_rewriter.py` | `_prepare_chat_context` | `test_query_rewriter.py` | Historial de turnos | Reglas heurísticas deícticas | None | Medio | Mantener |
| **RT-05** | Retrieval | AdaptiveRouter | **C** | `retrieval/adaptive_router.py` | `/api/retrieval/fabric/inspect` | `test_adaptive_router.py` | None | Desconectado de `/api/chat/query` | None | Bajo | Evaluar en P2 |
| **RT-06** | Retrieval | CandidatePooler | **C** | `retrieval/candidate_pooler.py` | `RetrievalFabricLite.retrieve` | `test_candidate_pooler.py` | `knowledge_store.db` | Desconectado de `/api/chat/query` | None | Bajo | Evaluar en P2 |
| **RT-07** | Retrieval | PresentationFilter (Anti-Leak) | **A** | `retrieval/presentation_filter.py` | `_assemble_epistemic_context` | `test_chat_content_registry.py` | `content_registry` (8.334 rows) | Filtrado determinista de soluciones | None | Crítico | Mantener |
| **RT-08** | Retrieval | Reranker (Jina & Deterministic Local)| **C** | `retrieval/reranker.py` | `/api/retrieval/fabric/inspect` | `test_reranker.py` | None (Local) / Jina API | Desconectado de `/api/chat/query` | None | Medio | Evaluar en P2 |
| **RT-09** | Retrieval | GranularityRouter (Macro/Hybrid/Micro)| **A** | `retrieval/granularity_router.py` | `_assemble_epistemic_context` | `test_granularity_router.py` | `chapter_summaries` (40 rows) | Requiere resúmenes de capítulo | Direct chunk search | Medio | Mantener |
| **RT-10** | Retrieval | SectionExpander | **A** | `retrieval/expansion.py` | `_assemble_epistemic_context` | `test_c2_l3_integral_shield.py` | `chunks.pos_index` | Sub-budget interno (<1800 tokens) acotado por C3 | Unbounded chunk stitch | Alto | Mantener |
| **PD-01** | Pedagogía | Bayesian Knowledge Tracing (BKT) | **A** | `student/bkt_tracker.py`, `routes/chat.py:2819` | `/api/chat/evaluate`, `/api/student/exercises/verify` | `test_bkt_tracker.py` | `student_state.db` (`bkt_states`) | Actualizado solo en ejercicios formales; chat solo lee | Conversational guessing | Alto | Mantener |
| **PD-02** | Pedagogía | SM-2 Spaced Repetition | **B** | `student/spaced_repetition.py` | `session_briefing.py`, `routes/dialogue.py` | `test_spaced_repetition.py` | `student_state.db` | Conectado a briefing y diálogo | Static interval | Medio | Mantener |
| **PD-03** | Pedagogía | Knowledge Components Catalog | **A** | `pedagogy/orchestrator.py` (`_kc_catalog`) | Startup, `/api/curriculum/roadmap` | `test_kc_catalog.py` | JSONs en `config/kcs/` | Catálogos fijos por cuaderno | None | Alto | Mantener |
| **PD-04** | Pedagogía | Prerequisites Topology (DAG) | **A** | `routes/curriculum.py`, `session/progression_policy.py`| `/api/curriculum/roadmap`, `/api/study/session/open` | `test_curriculum.py` | KC definitions | Dependencias duras $P(L) \ge 0.60$ | Unstructured sequence | Alto | Mantener |
| **PD-05** | Pedagogía | Socratic Dialogue Engine | **B** | `pedagogy/dialogue_engine.py` | `/api/pedagogy/episode/.../dialogue` | `test_dialogue_engine.py` | None | Opera en endpoint específico de episodios | Pure LLM prompt | Medio | Mantener |
| **PD-06** | Pedagogía | Struggle Mode Protocol | **A** | `student/struggle_tracker.py` | `/api/chat/query`, `/api/chat/evaluate` | `test_struggle_mode.py` | `student_state.db` | Gatilla a $\ge 3$ fallos consecutivos en evaluación | Unbounded failure loop | Medio | Mantener |
| **PD-07** | Pedagogía | Solution Protection Anti-Leak | **A** | `pedagogy/solution_protection.py` | `sse_generator` (`chat.py:2438`) | `test_chat_content_registry.py` | `content_registry` | Bloquea soluciones directas canónicas | Raw output leak | Crítico | Mantener |
| **PD-08** | Pedagogía | Multi-KC Causal Exercise Generator | **A** | `pedagogy/exercise_compiler.py` | `/api/student/exercises/generate/multi-kc` | `test_exercise_compiler.py` | `container.generated_registry` | Requiere plantillas de composición | Generic LLM quiz | Medio | Mantener |
| **PD-09** | Pedagogía | BugSpotter Adversarial Debugger | **A** | `pedagogy/bug_generator.py` | `/api/student/exercises/generate/debugging` | `test_bug_generator.py` | CWE-120/190/362/416 templates | Mutaciones sintéticas controladas | None | Medio | Mantener |
| **PD-10** | Pedagogía | State Predictor Trace Tables | **A** | `pedagogy/state_predictor.py` | `/api/student/exercises/generate/trace` | `test_state_predictor.py` | x86-64 / C templates | Registros y memoria determinista | Free-form code execution | Medio | Mantener |
| **PD-11** | Pedagogía | SpiralCurriculumEngine | **A** | `pedagogy/spiral_curriculum.py` | `/api/chat/query`, `/api/chat/evaluate` | `test_spiral_curriculum.py` | `bkt_tracker` | Inyecta directiva si $P(L) \ge 0.60$ | Linear curriculum only | Medio | Mantener |
| **PD-12** | Pedagogía | ProgressionPolicy | **A** | `session/progression_policy.py` | `/api/study/session/open`, `/action` | `test_progression_policy.py` | BKT + Prerequisites | Máquina de estados determinista | LLM next-topic choice | Alto | Mantener |
| **PD-13** | Pedagogía | FastPath Conversational Service | **A** | `tutor/fastpath_service.py` | `_prepare_chat_context` | `test_chat_fastpath_conversational.py` (11/11)| None | Sub-100ms para saludos/meta | Unnecessary retrieval | Alto | Mantener |
| **MC-01** | Memoria | Conversation Turn Buffer | **A** | `web/routes/chat.py` (`_CONV_TURN_BUFFER`) | `/api/chat/query` | `test_c3_hard_ceiling.py` | In-memory `TTLCache` (1h TTL) | Volátil ante reinicio de servidor | None | Medio | Mantener |
| **MC-02** | Memoria | Mem0Manager Sovereign Core | **A** | `memory/mem0_manager.py` | `_trigger_background_memory_extraction` | `test_mem0_manager.py` | `student_state.db` | Extracción local asíncrona de preferencias | Cloud Mem0 API | Alto | Mantener |
| **MC-03** | Memoria | Pedagogical Memory Extractor | **A** | `student/memory_extractor.py` | `_trigger_background_memory_extraction` | `test_memory_extractor.py` | `student_pedagogical_memory` (2 rows) | Extracción asíncrona post-turno | Synchronous blocking | Medio | Mantener |
| **MC-04** | Memoria | Cognitive Profile Injector | **A** | `student/cognitive_profile.py` | `_build_cognitive_profile_block` | `test_cognitive_profile.py` | `student_cognitive_profile` (3 rows) | Sub-budget acotado a $<120$ tokens | Context bloat | Medio | Mantener |
| **MC-05** | Memoria | Session Digest Recorder | **A** | `pedagogy/session_digest.py` | `/api/chat/evaluate` | `test_session_digest.py` | `session_records` (2 rows) | Registra actividad por sesión | None | Bajo | Mantener |
| **PV-01** | Providers | MultiFallbackBackend | **A** | `llm/multi_fallback.py` | `sse_generator` | `test_multi_fallback.py` | Providers configurados | 9 proveedores en cascada ordenada | Single provider failure | Crítico | Mantener |
| **PV-02** | Providers | OfflinePedagogicalBackend | **A** | `llm/offline_oracle.py` | Fallback final / Offline mode | `test_offline_oracle.py` | Plantillas conceptuales locales | Citas huérfanas `[E1]` erradicadas | Hallucinated citations | Crítico | Mantener |
| **PV-03** | Providers | SSE Streaming Protocol | **A** | `web/routes/chat.py` (`sse_generator`) | `/api/chat/query` | `test_chat_sse_endpoint.py` | Network connection | Protocolo unificado de eventos SSE | Blocking JSON response | Crítico | Mantener |
| **PR-01** | Practice | Sandbox Execution S6 | **D** | `web/routes/practice.py` | `/api/practice/evaluate` | `test_practice.py` | None | **Retorna PRACTICE_UNAVAILABLE fail-closed**| Simulated mock assertions | Bajo | Mantener |
| **PR-02** | Practice | File-based Local Auditor (VSCode) | **A** | `web/routes/student_exercises.py` | `/api/student/exercises/{id}/verify` | `test_student_exercises.py` | `data/student_submissions/` | Requiere archivo Markdown en disco | Web-only text input | Alto | Mantener |
| **PR-03** | Practice | LabGraderBridge (Flag Hashes) | **C** | `student/lab_observations.py` | Invocable en Python; sin endpoint HTTP | `test_lab_observations.py` | `config/lab_kc_map.json` | Desconectado de FastAPI | None | Bajo | Evaluar en P2 |

---

## ARTIFACT B: Runtime Trace de Rutas Críticas

### 1. Jerarquía Presupuestaria de Contexto (C3)
En las rutas de generación se distingue contractualmente el límite normativo del presupuesto de despacho:
```text
C3 Normative Ceiling (Contrato Normativo C3)
                    5000 tokens
                         │
                         ▼
        Effective Dispatch Budget (Presupuesto de Despacho)
                    4761 tokens  [Margen de seguridad: 5% (239 tokens)]
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
Sub-budget de Expansión           Sub-budget de Evidencia
   < 1800 tokens                     < 2700 tokens
(SectionExpander)                 (prune_evidence_text)
                         │
                         ▼
             Provider Payload (MultiFallbackBackend)
                 <= 4761 tokens estimados (ceil(len/4))
```
Cualquier sub-límite interno de expansión opera como un **sub-budget** coordinado, sin sustituir el techo global efectivo de 4.761 tokens.

### 2. Traza de Producción: `POST /api/chat/query`
```text
Cliente Web / ChatWorkspace
  │
  ▼
[FastAPI Router: routes/chat.py]
  ├── Pre-flight: DataSanitizer (Accidental PII / API keys check) -> Bloqueo si PII
  ├── Input Sanitizer: sanitización de caracteres y bounds
  │
  ▼
[_prepare_chat_context (asyncio.to_thread)]
  ├── 1. Scope Resolver: valida notebook_id / folder_id contra knowledge_store.db
  ├── 2. FastPathConversationalService: detecta saludos / meta en sub-100ms -> Bypass LLM
  ├── 3. Conversation Turns Resolver: fusiona server TTLCache y client turns
  ├── 4. QueryRewriter: resolución deíctica y reescritura de contexto
  ├── 5. Non-Curricular Intent Filter: abstención pre-retrieval si query es trivial/ficción
  ├── 6. GranularityRouter: clasifica intención (MACRO, HYBRID, MICRO)
  │
  ▼
[_assemble_epistemic_context]
  ├── 7. ACL & Aislamiento (C2 / C4): _authorized_sources_for_scope filtra allowlist L3
  ├── 8. ReferenceExtractor & ContentRegistry: verifica ejercicios/ítems registrados
  ├── 9. Búsqueda Híbrida:
  │      - store.search_hybrid (FTS5 BM25 + Vector)
  │      - En runtime actual: Vector search retorna [] por mismatch 1024d vs 384d
  │      - FTS5 BM25 se convierte en la ruta de retrieval efectiva
  ├── 10. PresentationFilter (Anti-Leak): bloquea soluciones canónicas no autorizadas
  ├── 11. SectionExpander: expande chunks vecinos bajo sub-budget interno (<1800 tokens)
  ├── 12. C5 Epistemic Trust Gate: evaluate_epistemic_trust
  │       - Analiza cobertura léxica de entidades indispensables (OC-1..OC-5)
  │       - Detecta conflictos doctrinales (CONFLICTING_EVIDENCE banner)
  │       - Si la evidencia no es suficiente -> Retorna EpistemicContextPack(abstained=True)
  ├── 13. C3 Pre-pruning: prune_evidence_text_deterministically (sub-budget <2700 tokens)
  │
  ▼
[BKT & Memory Directive Assembly]
  ├── 14. StruggleDetector: comprueba si KC actual está en protocolo de lucha
  ├── 15. ScaffoldingDirective: modula nivel de soporte según solución de dependencia
  ├── 16. SpiralCurriculumEngine: inyecta directiva si P(L) >= 0.60
  ├── 17. Mem0Manager: sintetiza directiva de preferencias y patrones de error
  │
  ▼
[sse_generator: Streaming Response]
  ├── 18. C5 Universal Trust Gate (Chokepoint 1):
  │       - Si context_pack es None, abstained o not is_sufficient:
  │         * Dispara _trigger_background_memory_extraction
  │         * Emite evidence_manifest(abstained=True)
  │         * Emite abstención determinista
  │         * Cierra stream (CERO llamadas al LLM en fixtures no suficientes)
  ├── 19. SolutionProtection: intercepta si se pide solución directa en examen
  ├── 20. CitationValidator / StreamCitationBuffer: depura citas falsas en streaming
  ├── 21. StructuredResponsePipeline.generate_phased_response:
  │       - Chokepoint C5 de defensa en profundidad
  │       - Chokepoint C3 Hard Ceiling: estimate_payload_tokens <= 4.761 tokens
  │       - Invoca MultiFallbackBackend (Gemini -> Gemma -> Cloudflare -> Groq -> Offline)
  ├── 22. Background Memory Task: _trigger_background_memory_extraction
  │       - Persiste perfil cognitivo, memorias de sesión y preferencias en student_state.db
  │
  ▼
Fin del Turno SSE (HTTP 200 stream)
```

### 3. Traza de Evaluación de Práctica: `POST /api/chat/evaluate`
```text
Cliente Web / Panel de Práctica
  │
  ▼
[FastAPI Router: routes/chat.py:2768]
  ├── 1. Búsqueda de Ejercicio: ExerciseStore (certificados) o GeneratedRegistry (MultiKC, BugSpotter, Trace)
  │      - Si no existe: Retorna UNGRADED fail-closed (0 mutación BKT)
  ├── 2. Grader Determinista:
  │      - GeneratedOracleGrader / MCGrader / ExactGrader (Cero LLM en corrección)
  ├── 3. Registro de Intento: student_storage.record_exercise_attempt
  ├── 4. BKT Tracker:
  │      - Actualiza P(L) bajo Corbett & Anderson para todos los KCs involucrados
  ├── 5. Struggle Tracker:
  │      - Registra acierto/fallo consecutivo
  ├── 6. Session Digest:
  │      - Registra intento en sesión
  ├── 7. Spiral Curriculum Engine:
  │      - Si P(L) >= 0.60, detecta KCs prerequisito para retroalimentación
  │
  ▼
Respuesta JSON: status=GRADED, p_L, delta_p_L, struggle_mode, remediation
```

### 4. Traza de Sandbox de Práctica: `POST /api/practice/evaluate`
```text
Llamada a endpoint legado
  │
  ▼
[FastAPI Router: routes/practice.py:51]
  │
  ▼
Retorno Inmediato Fail-Closed:
  - status: "PRACTICE_UNAVAILABLE"
  - stdout: "[S6] Sandbox de ejecución real no disponible en esta versión."
  - assertions: []
```

---

## ARTIFACT C: Matriz de Componentes Activos, Desconectados e Históricos

| Componente | Clasificación | Estado de Cableado | Diagnóstico Factual |
| :--- | :---: | :--- | :--- |
| `FastPathConversationalService` | `ACTIVE` | Cableado en `chat.py` | Detecta saludos y navegación sub-100ms. |
| `SectionExpander` | `ACTIVE` | Cableado en `chat.py` | Expansión de contexto acotada por sub-budget interno (<1800 tokens). |
| `PresentationFilter` | `ACTIVE` | Cableado en `chat.py` | Bloquea soluciones de ejercicios de `content_registry`. |
| `C5 Epistemic Trust Gate` | `ACTIVE` | Cableado en `chat.py` y `pipeline` | Bloquea consultas sin evidencia suficiente antes del LLM. |
| `C3 Budget Guard` | `ACTIVE` | Cableado en `pipeline` y backends | Garantiza payloads $\le 4.761$ tokens efectivos. |
| `MultiFallbackBackend` | `ACTIVE` | Cableado en `pipeline` | Cascada ordenada de 9 proveedores con fallback final a oráculo offline. |
| `Mem0Manager` | `ACTIVE` | Cableado en `chat.py` (lectura/escritura) | Persiste y sintetiza memorias en `student_state.db`. |
| `BKTTracker` | `ACTIVE` | Cableado en `chat.py:evaluate` y `verify`| Actualiza estados de maestría deterministas en ejercicios formales. |
| `SpiralCurriculumEngine` | `ACTIVE` | Cableado en `chat.py` y `evaluate` | Sugiere KCs retroactivos al alcanzar $P(L) \ge 0.60$. |
| `BugSpotter` | `ACTIVE` | Cableado en `routes/student_exercises.py` | Genera ejercicios de depuración adversaria con oráculo determinista. |
| `MultiKCGenerator` | `ACTIVE` | Cableado en `routes/student_exercises.py` | Genera ejercicios de composición causal multi-KC. |
| `StatePredictor` | `ACTIVE` | Cableado en `routes/student_exercises.py` | Genera trace tables deterministas x86-64 y C. |
| `ProgressionPolicy` | `ACTIVE` | Cableado en `routes/study_session.py` | Determina siguiente acción pedagógica según BKT y DAG en sesión de estudio. |
| `LocalONNXEmbeddingProvider` | `ACTIVE` | Cableado en `knowledge_store.py` | Activo en memoria (384d), pero `vector_search` retorna `[]` por mismatch con DB (1024d). |
| `RetrievalFabricLite` | `DISCONNECTED` | Cableado solo en `/api/retrieval/inspect`| Desconectado del flujo principal `/api/chat/query`. |
| `AdaptiveRouter` | `DISCONNECTED` | Cableado solo en `RetrievalFabricLite` | No participa en el flujo de chat. |
| `CandidatePooler` | `DISCONNECTED` | Cableado solo en `RetrievalFabricLite` | No participa en el flujo de chat. |
| `DeterministicLocalReranker` | `DISCONNECTED` | Cableado solo en `RetrievalFabricLite` | No participa en el flujo de chat. |
| `JinaReranker` | `DISCONNECTED` | Cableado solo en `RetrievalFabricLite` | No participa en el flujo de chat. |
| `LabGraderBridge` | `DISCONNECTED` | Implementado en `student/lab_observations`| Sin endpoint HTTP en FastAPI. |
| `SentenceTransformerEmbeddingProvider` | `DISCONNECTED` | En código pero no instalado en `.venv` | Falta dependencia `sentence_transformers`. |
| `/api/session/*` | `DEAD_CONFIRMED`| Registrado en `app.py` | Retorna HTTP 410 GONE explícito. |
| `/api/practice/evaluate` (S6) | `DEAD_CONFIRMED`| Registrado en `routes/practice.py` | Retorna `PRACTICE_UNAVAILABLE` fail-closed. |

---

## ARTIFACT D: Pedagogía Diseñada vs Pedagogía Ejecutada

```text
========================================================================================================
DIMENSIÓN PEDAGÓGICA     DISEÑADA / DOCUMENTADA          EJECUTADA EN RUNTIME
========================================================================================================
Tracking de Maestría     Continuo durante el diálogo     continuous conversational mastery tracking
                         (actualiza BKT en cada turno)   = NOT EXECUTED.
                                                         BKT es OPERACIONAL pero se actualiza exclusivamente
                                                         en ejercicios formales (/api/chat/evaluate y verify).
                                                         El chat conversacional solo LEE el estado BKT.

Protocolo de Lucha       Activa pistas socráticas tras   OPERACIONAL. StruggleTracker contabiliza fallos
(Struggle Mode)          fracasos repetidos.             consecutivos en evaluación y modula prompts en chat.

Currículo en Espiral     Conecta conceptos nuevos con    OPERACIONAL. Si P(L) >= 0.60 inyecta directivas
                         prerequisitos consolidados.     retroactivas en contexto de generación.

Protección de Exámenes   Oculta soluciones canónicas     OPERACIONAL. Intercepta y bloquea soluciones
                         durante evaluaciones.           de content_registry en SSE y prompt.

Ejercicios con Oráculo   Genera desafíos Multi-KC,       OPERACIONAL vía /api/student/exercises y evaluate
                         BugSpotter y Trace Tables.      con calificación determinista por oráculo.

Progresión Curricular    El tutor decide automáticamente OPERACIONAL acotado: ProgressionPolicy decide
                         qué enseñar a continuación.     siguiente acción en /api/study/session/open.
                                                         En /api/chat/query es reactivo al input del alumno.
========================================================================================================
```

---

## ARTIFACT E: Retrieval Actual Real

### 1. Pipeline Efectivo en `/api/chat/query`
$$\text{Query} \longrightarrow \text{QueryRewriter} \longrightarrow \text{GranularityRouter} \longrightarrow \text{FTS5 BM25} \longrightarrow \text{PresentationFilter} \longrightarrow \text{SectionExpander} \longrightarrow \text{C5 Trust Gate} \longrightarrow \text{C3 Budget}$$

### 2. Cadena Factual del Retrieval Vectorial Inactivo (RT-02 = C)
```text
vector_store.db: 287.075 vectores (1024 dimensiones, Qwen3-Embedding-0.6B)
      │
      ▼
runtime embedder: sentence_transformers no instalado en .venv
      │
      ▼
fallback a LocalONNXEmbeddingProvider (384 dimensiones, multilingual-e5-small)
      │
      ▼
incompatibilidad dimensional detectada en storage/knowledge_store.py:844:
      matrix.shape[1] != len(q_vec)  [1024 != 384]
      │
      ▼
vector_search retorna [] silenciosamente
      │
      ▼
FTS5 BM25 se convierte en la ruta efectiva de retrieval
```
**Formulación Factual:** El código implementa una arquitectura híbrida FTS5 + vectorial, pero el camino vectorial no participa actualmente de manera efectiva en el runtime debido a una incompatibilidad dimensional; el retrieval operacional actual es predominantemente FTS5.

### 3. Estado de Rerankers (RT-08 = C)
* Implementados en `src/study_engine/retrieval/reranker.py` (`DeterministicLocalReranker` y `JinaReranker`).
* Están testeados en aislamiento pero **desconectados del flujo de producción**: `/api/chat/query` no invoca a `RetrievalFabricLite` ni al reranker.

### 4. Características de FTS5 BM25 (RT-01 = A)
* Tabla virtual `chunks_fts` con 105.705 registros indexados por BM25.
* Sanitización contra stopwords y términos conversacionales en español.
* Normalización léxica y bilingüe (`_BILINGUAL_MAP`).
* Soporte exacto para identificadores técnicos con guiones bajos (`_fts_phrase_for_symbol`).
* Latencia observada de búsqueda: **1,36 ms (warm) / 2,10 ms (cold)**.

---

## ARTIFACT F: Memoria y Estado del Estudiante Real

```text
========================================================================================================================
COMPONENTE             PERSISTENCIA           ESCRITOR                LECTOR                  EFECTO PEDAGÓGICO
========================================================================================================================
Conversation History   In-Memory TTLCache     sse_generator           _prepare_chat_context   Mantiene contexto de turnos
                       (1h TTL, 1000 items)   (fin de turno)          (inicio de turno)       recientes (hasta 10 mensajes).

Episodic Session       student_state.db       Mem0Manager             SessionBriefing         Registra topics y summaries
                       (session_records)      (background task)                               de turnos anteriores.

Cognitive Memory       student_state.db       CognitiveExtractor      _build_cognitive_block  Inyecta bloque <120 tokens
                       (cognitive_profile)    (background task)       (chat.py:2507)          de estilo y ritmo de aprendizaje.

Pedagogical Memory     student_state.db       MemoryExtractor         Mem0Manager             Inyecta directivas sobre
                       (pedagogical_memory)   (background task)       (chat.py:2147)          conceptos erróneos detectados.

BKT State              student_state.db       evaluate_exercise_answer /api/curriculum/roadmap Modula nivel de dificultad,
                       (bkt_states)           y verify_exercise       y chat.py:2102          activa struggle y espiral.

Curriculum State       student_state.db       ProgressionPolicy       StudySession            Determina KCs dominados,
                       (curriculum_progress)  (session actions)       Orchestrator            en progreso y pendientes.
========================================================================================================================
```

---

## ARTIFACT G: Estado Real de Practice y Curriculum

### 1. Practice Engine
* `/api/practice/evaluate` (S6 Sandbox): **DEAD / UNAVAILABLE** (retorna status fail-closed `PRACTICE_UNAVAILABLE`).
* `/api/chat/evaluate`: **OPERATIONAL** (califica ejercicios certificados y generados con oráculos deterministas y actualiza BKT).
* `/api/student/exercises/*`: **OPERATIONAL** (gestiona y verifica archivos Markdown de soluciones locales de estudiantes en VSCode contra oráculo determinista).
* `LabGraderBridge`: **DISCONNECTED** (código funcional sin endpoint HTTP en FastAPI).

### 2. Curriculum Engine
* **¿TALOS sabe dónde está el estudiante?** **SÍ.** Demostrado empíricamente a través de la integración de:
  $$\text{BKT State} + \text{KC State} + \text{Prerequisite DAG} + \text{ProgressionPolicy} + \text{StudySessionOrchestrator}$$
* **¿TALOS decide automáticamente todo lo que debe enseñar?** **NO.** La autonomía curricular está acotada al alcance de `ProgressionPolicy` en apertura/acciones formales de sesión (`/api/study/session/open`). En el endpoint interactivo `/api/chat/query`, TALOS opera de manera reactiva a la consulta del estudiante, adaptando explicaciones y scaffolding en función del estado pedagógico registrado sin imponer secuencias lineales obligatorias.

---

## ARTIFACT H: Performance Baseline (BASELINE ONLY)

> [!NOTE]
> Las métricas siguientes corresponden a **observaciones empíricas del entorno auditado** (`Linux`, Python 3.12, `.venv`, `data/web_state/knowledge_store.db`). **No constituyen SLOs, SLAs, targets ni requisitos contractuales de producción.**

```text
================================================================================
MÉTRICA DE RENDIMIENTO                     VALOR OBSERVADO (BASELINE)
================================================================================
Tiempo de Import (study_engine.web.app)    : 872,12 ms
Tiempo de Startup (create_app)             : 1,72 ms
Memoria RSS Post-Startup                   : 110,01 MB
Latencia FTS5 Retrieval (Cold)             : 2,10 ms
Latencia FTS5 Retrieval (Warm)             : 1,36 ms
Latencia Hybrid Retrieval (Cold - ONNX init): 2.180,75 ms (diagnóstica de init)
Latencia Hybrid Retrieval (Warm)           : 128,94 ms
Latencia Reranker Local (10 candidatos)    : 0,10 ms
Latencia Endpoint /api/health (Cold)       : 5,59 ms
Latencia Endpoint /api/health (Warm)       : 1,28 ms
Latencia SSE Primer Token (/api/chat/query): 576,21 ms
Tiempo Total de Turno SSE                  : 576,25 ms
Tokens Emitidos por Turno                  : 99 tokens
================================================================================
```
*Nota Diagnóstica:* El valor de `2.180,75 ms` en hybrid cold refleja la carga e inicialización en memoria del modelo ONNX local, no un régimen permanente de operación.

---

## ARTIFACT I: Matriz de Discrepancias

### 1. DOCUMENTATION ≠ IMPLEMENTATION
* **Fuente:** `ARCHITECTURE.md`
* **Afirmación:** S6 Sandboxed code execution sandbox operativo en `/api/practice/evaluate`.
* **Realidad Observada:** Retorna `PRACTICE_UNAVAILABLE` fail-closed.
* **Severidad:** BAJA (reemplazado por verificación local determinista en `student_exercises.py`).
* **Acción:** Actualizar documentación técnica de arquitectura.

### 2. IMPLEMENTATION ≠ RUNTIME
* **Fuente:** `src/study_engine/storage/knowledge_store.py:787`
* **Afirmación:** `SentenceTransformerEmbeddingProvider` resuelve embeddings densos.
* **Realidad Observada:** `sentence_transformers` no está instalado en `.venv`, por lo que cae en fallback ONNX de 384d incompatible con la DB de 1024d (`matrix.shape[1] != len(q_vec)`).
* **Severidad:** ALTA (búsqueda vectorial inactiva en runtime).
* **Acción:** P1 Backlog: resolver mismatch dimensional de embeddings.

### 3. RUNTIME ≠ TEST
* **Fuente:** `src/study_engine/retrieval/fabric.py`
* **Afirmación:** Reranker y AdaptiveRouter optimizan las respuestas en producción.
* **Realidad Observada:** Los tests de reranker pasan aislados, pero en runtime `/api/chat/query` no invoca a `RetrievalFabricLite`.
* **Severidad:** MEDIA.
* **Acción:** P2 Backlog: evaluar conexión de reranker o retiro de dependencias.

### 4. HISTORICAL ≠ CURRENT
* **Fuente:** Checkpoints legados (V1 Core inicial)
* **Afirmación:** La sesión conversacional se gestionaba en `/api/session/{session_id}`.
* **Realidad Observada:** Retorna HTTP 410 GONE explícito; migrado a `/api/chat/query` y `/api/study/session/open`.
* **Severidad:** NULA (comportamiento contractual conforme a diseño).
* **Acción:** Mantener regla 410.

---

## ARTIFACT J: TALOS CURRENT STATE (Declaración Factual)

### Matriz Conceptual de Estados
| Dimensión | Estado |
| :--- | :--- |
| Gate B C1–C5 | PASS / CLOSED |
| Epistemic perimeter | Operational |
| Chat generation path | Operational |
| FTS5 retrieval | Operational |
| Dense vector retrieval | Inactive due to dimensional mismatch |
| Reranking production path | Disconnected |
| RetrievalFabricLite | Disconnected from main chat |
| BKT formal evaluation | Operational |
| Curriculum DAG / progression | Operational |
| Exercise generators | Operational |
| S6 sandbox | Unavailable / historical |
| LabGraderBridge | Disconnected |
| $\theta$ empirical calibration | Pending |
| Database integrity | Unchanged |

---

### Diagnóstico Factual a Preguntas Fundamentales

1. **¿Qué puede hacer TALOS hoy?**  
   Puede responder consultas pedagógicas socráticas en streaming, verificar localmente soluciones de código en Markdown contra oráculos forenses deterministas, actualizar el modelo de maestría BKT del alumno en ejercicios formales, generar ejercicios causales/bugs/traces deterministas, proyectar el grafo curricular interactivo y proteger exámenes contra filtraciones canónicas.

2. **¿Qué hace realmente en `/api/chat/query`?**  
   Sanitiza la entrada (anti-PII), valida alcance y cuaderno, detecta fastpath conversacional, reescribe deícticos, busca chunks vía FTS5 BM25 bajo estricto aislamiento de fuentes autorizadas (C2/C4), filtra soluciones canónicas, expande secciones bajo sub-budget interno, valida suficiencia epistémica previa al LLM (C5) con abstención inmediata si la evidencia es insuficiente, poda el prompt bajo el Effective Dispatch Budget de $\le 4.761$ tokens (C3), invoca al LLM mediante cascada de fallback resiliente y transmite tokens vía SSE depurando citas no verificadas.

3. **¿Qué garantías epistemológicas posee?**  
   Posee las garantías certificadas en Gate B: C1 (Grounding con fuentes verificadas), C2 (Aislamiento de fuentes por ACL L3), C3 (Límite normativo de 5.000 tokens / presupuesto de despacho de $\le 4.761$ tokens estimados), C4 (Aislamiento multi-curricular estricto) y C5 (Frontera pre-LLM con abstención fail-closed).  
   *Delimitación de alcance:* **Las rutas de generación auditadas bajo C1–C5 poseen comportamiento fail-closed ante insuficiencia epistemológica, con cero llamadas al LLM en los fixtures no suficientes verificados.**

4. **¿Qué partes pedagógicas están activas?**  
   Catálogo KC, DAG de prerequisitos, tracking BKT en ejercicios formales, Protocolo de Lucha (Struggle Mode), Currículo en Espiral, Protección de Exámenes, Generadores de Ejercicios (Multi-KC, BugSpotter, StatePredictor) y Progresión Curricular de Sesión.

5. **¿Qué partes existen pero están desconectadas?**  
   `RetrievalFabricLite`, `AdaptiveRouter`, `CandidatePooler`, `DeterministicLocalReranker`, `JinaReranker` y `LabGraderBridge`.

6. **¿Qué partes son históricas?**  
   `/api/session/*` (HTTP 410 GONE) y `/api/practice/evaluate` (S6 Sandbox no disponible).

7. **¿Qué partes faltan?**  
   Alineación dimensional de embeddings para reactivar la búsqueda semántica densa prevista por la arquitectura híbrida, conexión o retiro de rerankers en chat y calibración empírica del threshold $\theta$.

8. **¿Qué dependencias externas existen?**  
   APIs de LLM en la nube (Gemini, Groq, Cloudflare, SambaNova, etc.) con fallback soberano a `OfflinePedagogicalBackend`.

9. **¿Qué limitaciones siguen abiertas?**  
   Relevance threshold $\theta$ permanece formalmente como `PENDING_EMPIRICAL_CALIBRATION`; el vector retrieval permanece inactivo en runtime operando el sistema predominantemente sobre FTS5. OOD detection está implementado y conectado en el perímetro C5, pero su cobertura semántica completa no está empíricamente calibrada.

10. **¿Qué no sabemos todavía?**  
    La ganancia cualitativa real en precisión que aportaría la búsqueda semántica densa sobre el índice léxico FTS5 BM25 actual (que ha sustentado de manera robusta la suite de regresión y certificación de Gate B).

---

## ARTIFACT K: Prioritized Backlog (P0–P3)

> [!IMPORTANT]
> Ningún ítem del backlog P1–P3 es implementado durante CP112-R1. Esta lista define exclusivamente los frentes de trabajo post-Gate B a adjudicar en ciclos futuros.

### P0 — BLOCKER / CORRECTNESS
*Ninguno.* Todos los contratos de Gate B están en estado `PASS / CLOSED`.

### P1 — REQUIRED FOR COMPLETE TALOS
* **Ítem P1-01: Restaurar la capacidad de recuperación semántica densa prevista por la arquitectura híbrida.**
  * **Problema:** Mismatch de dimensiones (1024d en `vector_store.db` vs 384d en `LocalONNXEmbeddingProvider`) que causa que `vector_search` retorne `[]` en runtime (`knowledge_store.py:844`).
  * **Alternativas Documentadas (a decidir en ciclo posterior):**
    * *Alternativa A:* Proporcionar runtime compatible con 1024d (e.g., empaquetar modelo ONNX o dependencias para `Qwen3-Embedding-0.6B`).
    * *Alternativa B:* Reconstruir índice vectorial compatible con 384d (re-indexar con `multilingual-e5-small`).
  * **Estado de Decisión:** La selección entre la Alternativa A y la Alternativa B queda formalmente fuera de CP112-R1 y deberá ser evaluada en un checkpoint posterior a Gate B.

### P2 — IMPORTANT IMPROVEMENT
* **Ítem P2-01: Evaluar integración o retiro de RetrievalFabricLite en flujo de chat**
  * **Problema:** `RetrievalFabricLite`, `AdaptiveRouter` y `DeterministicLocalReranker` están implementados pero desconectados de `/api/chat/query`.
  * **Alcance:** Medir impacto de latencia del reranker local en turnos interactivos SSE frente a la ganancia de relevancia.
* **Ítem P2-02: Evaluar exposición HTTP de LabGraderBridge**
  * **Problema:** Calificador de flags de Juice Shop / laboratorios C implementado en código sin endpoint HTTP en FastAPI.
  * **Alcance:** Diseñar ruta REST `/api/student/lab/submit` o integrar en flujo de práctica.

### P3 — OPTIMIZATION / QUALITY OF LIFE
* **Ítem P3-01: Calibración empírica del threshold $\theta$**
  * **Problema:** El parámetro normativo permanece en `RELEVANCE_THRESHOLD_STATUS = PENDING_EMPIRICAL_CALIBRATION`.
  * **Alcance:** Ejecutar muestreo empírico de similitudes en corpus real sin asignar valores heurísticos arbitrarios.
* **Ítem P3-02: Evaluación de warmup de embeddings**
  * **Problema:** Inicialización en frío de ONNX insume 2.180 ms en la primera consulta híbrida.
  * **Alcance:** Evaluar threadpool daemon de carga eager durante startup de FastAPI.

---

## CP112_FINAL_STATE

```text
Gate B C1–C5: PASS / CLOSED.

TALOS dispone actualmente de un núcleo conversacional pedagógico
operacional con grounding, autorización de fuentes, aislamiento
curricular, hard ceiling contextual y trust gate pre-LLM.

El retrieval efectivo del runtime principal es actualmente FTS5;
la capacidad vectorial densa implementada no opera debido a una
incompatibilidad dimensional entre el índice persistido y el
embedder disponible en runtime.

Existen componentes implementados pero desconectados, entre ellos
RetrievalFabricLite, rerankers y LabGraderBridge.

El motor de práctica S6 no está disponible; la evaluación de
ejercicios mediante oráculos deterministas sí permanece operacional.

BKT, estado curricular, progresión, struggle mode, memoria
pedagógica y generadores deterministas forman parte del runtime
activo dentro de sus respectivos endpoints.

θ permanece pendiente de calibración empírica.

No se modificó la base de datos durante Gate B ni durante CP112.

Este documento constituye la baseline operacional para el trabajo
posterior a Gate B y no implica que todas las capacidades diseñadas
de TALOS estén actualmente activas.
```

---

## Declaración Oficial de Cierre

```text
CP112-R1 = PASS / CLOSED
GATE_B = CLOSED
CP112_BASELINE = ESTABLISHED
CP112_IMPLEMENTATION = NONE
DATABASE_CHANGES = 0
```
