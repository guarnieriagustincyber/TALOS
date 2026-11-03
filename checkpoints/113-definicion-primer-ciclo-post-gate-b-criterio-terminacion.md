# CP113-R1 — Adjudicación Final de Definition of Done y Criterio de Terminación de TALOS V1

**Tipo:** Adjudicación final de alcance + normalización de Definition of Done  
**Rol:** Auditor Técnico Senior de Assurance + Arquitectura de TALOS  
**Precondición:** CP113 ejecutado / Requiere correcciones R1  
**Gate B:** C1–C5 = PASS / CLOSED  
**Baseline Operacional:** CP112-R1 = ESTABLISHED  
**Integridad de Datos:** `DATABASE_CHANGES = 0` (`data/web_state/knowledge_store.db` SHA256: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` — `UNCHANGED`)  
**Restricciones:** `PRODUCTION_SOURCE_CHANGES = 0`, `CHECKPOINT_DOCUMENTATION_ONLY = TRUE`  

---

## 0. Propósito y Separación Canónica de Conceptos

El presente checkpoint adjudica de forma definitiva el alcance, las brechas y los criterios de aceptación de **TALOS V1**, eliminando toda métrica subjetiva o porcentaje informal de completitud.

Queda formalmente establecida la separación de cuatro dominios conceptuales:

```text
GATE B STATUS
        ↓
C1 / C2 / C3 / C4 / C5 = PASS / CLOSED
(Garantías epistemológicas y contractuales certificadas en su perímetro)

        ≠

V1 CAPABILITY COMPLETENESS
        ↓
El conjunto de capacidades requeridas por la especificación original
frente al estado implementado, conectado y ejecutable.

        ≠

V1 PRODUCT ACCEPTANCE
        ↓
La validación de integración de extremo a extremo que demuestra
que los componentes certificados operan en armonía pedagógica.

        ≠

POST-V1 BACKLOG
        ↓
Mejoras de aseguramiento, optimizaciones y extensiones de plataforma
(embeddings densos, rerankers en chat, calibración estadística de θ, sandbox S6).
```

### Jerarquía de Fuentes de Autoridad
En caso de discrepancia documental, rige el siguiente orden de precedencia:
$$\text{CURRENT EXECUTABLE CONTRACT} > \text{TESTS} > \text{WIRING / RUNTIME} > \text{CURRENT DOCS} > \text{HISTORICAL DOCS}$$

---

## ARTIFACT A: `V1_FINAL_ADJUDICATION_MATRIX`

Evaluación categórica de cada dimensión de TALOS V1. Se sustituye cualquier métrica porcentual por estados binarios/categóricos:

| Dimensión | Intención Original V1 | Implementación | Conectado | Ejecutado | Verificado | Efecto en Producto | ¿Bloquea V1? | Estado Final |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :---: | :---: |
| **Grounding (C1)** | No inventar hechos ni citas; proveniencia por chunk canónico. | SÍ | SÍ | SÍ | SÍ | Atribución trazable; citas falsas suprimidas. | NO | **SATISFIED** |
| **ACL de Fuentes (C2)** | Restringir evidencia a fuentes L3 autorizadas por cuaderno. | SÍ | SÍ | SÍ | SÍ | Allowlist estricta de 99 relaciones en retrieval y prompt. | NO | **SATISFIED** |
| **Hard Ceiling (C3)** | Context ceiling determinista: $\le 4.761$ tokens efectivos. | SÍ | SÍ | SÍ | SÍ | Poda jerárquica y chokepoints triples contra desbordes. | NO | **SATISFIED** |
| **Aislamiento Curricular (C4)** | Cero fuga cross-cuaderno entre trayectorias de estudio. | SÍ | SÍ | SÍ | SÍ | Matriz 5x5 certificada; aislamiento estricto de SQLite/caché. | NO | **SATISFIED** |
| **Abstención Trust Gate (C5)** | Bloqueo pre-LLM fail-closed ante insuficiencia o temas OOD. | SÍ | SÍ | SÍ | SÍ | Cero llamadas al LLM ante falta de evidencia demostrada. | NO | **SATISFIED** |
| **Retrieval Léxico (RT-01)** | Búsqueda precisa sobre el corpus técnico del curso. | SÍ | SÍ | SÍ | SÍ | FTS5 BM25 a 1,36 ms resolviendo las entidades del curso. | NO | **SATISFIED** |
| **Dense Vector Retrieval (RT-02)**| Búsqueda semántica complementaria por similitud de coseno. | SÍ | SÍ | NO | SÍ (aislado)| Inactivo en runtime por mismatch 1024d vs 384d. | NO | **POST-V1** |
| **BKT Tracker (PD-01)** | Modelar maestría $P(L)$ por KC sin alucinación. | SÍ | SÍ | SÍ | SÍ | Actualizado por oráculos deterministas; chat libre solo lee. | NO | **SATISFIED** |
| **Adaptatividad Core** | Modulación pedagógica ante fracasos o consolidación. | SÍ | SÍ | SÍ | SÍ | Struggle Mode ($\ge 3$ fallos), Currículo en Espiral y Scaffolding. | NO | **SATISFIED** |
| **Curriculum DAG (PD-04/PD-12)** | Conocer posición del alumno y dirigir la siguiente acción. | SÍ | SÍ | SÍ | SÍ | Grafo de KCs y ProgressionPolicy determinista v1.0. | NO | **SATISFIED** |
| **Evaluación de Código (PR-02)** | Auditar soluciones de programación sin consumo pasivo. | SÍ | SÍ | SÍ | SÍ | Verificación local determinista en VSCode contra oráculo. | NO | **SATISFIED** |
| **S6 Sandbox (PR-01)** | Ejecución aislada de código/syscalls en servidor. | SÍ | SÍ | NO | SÍ | Retorna `PRACTICE_UNAVAILABLE` fail-closed (501). | NO | **POST-V1** |
| **Anti-Leak (PD-07/RT-07)** | Ocultar soluciones canónicas durante evaluaciones. | SÍ | SÍ | SÍ | SÍ | Bloqueo en retrieval (`PresentationFilter`) y SSE. | NO | **SATISFIED** |
| **Memoria Soberana (MC-01/02)**| Continuidad de turnos y estado relacional persistente. | SÍ | SÍ | SÍ | SÍ | TTLCache en memoria, `student_state.db` y Mem0 local. | NO | **SATISFIED** |
| **Runtime / Streaming (PV-03)** | Streaming fluido SSE sin bloqueos ni errores 500. | SÍ | SÍ | SÍ | SÍ | Endpoint SSE con manifest, fallback ordenado y oráculo offline. | NO | **SATISFIED** |
| **E2E Study Loop** | Ciclo completo unificado: Apertura $\to$ Chat $\to$ Ejercicio $\to$ BKT $\to$ Siguiente paso. | SÍ | SÍ | PARCIAL | PARCIAL | Los componentes funcionan aislados; falta prueba E2E unificada. | **SÍ** | **REQUIRED GAP** |
| **Calibración de $\theta$ (C5)** | Umbral estadístico calibrado de similitud semántica. | PARCIAL | SÍ | NO | PARCIAL | C5 opera fail-closed por cobertura léxica; $\theta$ pendiente. | NO | **POST-V1** |

---

## ARTIFACT B: `V1_DEFINITION_OF_DONE_FINAL` (Criterio Objetivo de Terminación)

Para declarar formalmente **`TALOS V1 PRODUCT COMPLETE`**, deben satisfacerse los criterios organizados en tres niveles verificables:

```text
========================================================================================================
NIVEL A: PRODUCT CAPABILITIES (Lo que TALOS debe poder hacer funcionalmente)
========================================================================================================
[x] CAP-01: El estudiante puede interactuar socráticamente en streaming sobre las fuentes autorizadas del
            cuaderno activo, recibiendo explicaciones y andamiaje según su nivel de autonomía.
[x] CAP-02: El sistema prohíbe la entrega en bandeja de soluciones completas de ejercicios protegidos,
            forzando al estudiante a pensar, programar y deducir activamente (Principio P6).
[x] CAP-03: El estudiante puede resolver ejercicios de programación, depuración y traza, recibiendo
            calificación determinista e inmediata basada en oráculos formales (0 LLM en la nota).
[x] CAP-04: El estado de conocimiento del estudiante se modela probabilísticamente por KC mediante BKT,
            desbloqueando o requiriendo repaso de prerrequisitos según el DAG curricular.
[x] CAP-05: El sistema reconoce cuándo la evidencia disponible es insuficiente o ajena al material,
            emitiendo una abstención explícita con cero llamadas al LLM (Principio P5).

========================================================================================================
NIVEL B: ASSURANCE (Lo que debe estar demostrado para confiar en el sistema)
========================================================================================================
[x] ASSUR-01: Gate B C1–C5 formalmente cerrado con suites adversariales aprobadas al 100% (51/51 tests).
[x] ASSUR-02: Ningún payload despachado a backends LLM supera los 4.761 tokens estimados (C3).
[x] ASSUR-03: Cero fugas cross-cuaderno en la matriz 5x5 de aislamiento multi-curricular (C4).
[x] ASSUR-04: Cero mutaciones de BKT originadas por diálogo conversacional libre o claims no verificadas
              del estudiante (`test_21_bkt_gaming.py`).
[ ] ASSUR-05: Validación de integración de extremo a extremo que demuestre que el ciclo completo de estudio
              (Apertura $\to$ Diálogo $\to$ Práctica $\to$ BKT $\to$ Progresión) opera sin excepciones.

========================================================================================================
NIVEL C: RELEASE INTEGRITY (Sincronización operacional previa al cierre)
========================================================================================================
[x] REL-01: Integridad inmutable de datos: DATABASE_CHANGES = 0 verificado por SHA-256 en knowledge_store.db.
[ ] REL-02: Sincronización de documentación y contratos de API: las rutas activas (/api/chat/query,
            /api/chat/evaluate, /api/study/session/open, /api/student/exercises/*) quedan formalmente
            declaradas, y los componentes desconectados (RetrievalFabricLite, S6, rerankers) quedan
            formalmente rotulados como POST-V1 en la especificación de release.
[ ] REL-03: Suite de regresión del perímetro oficial limpia, con los tests históricos desfasados
            formalmente archivados o adaptados al contrato C5.
========================================================================================================
```

---

## ARTIFACT C: `THETA_STATUS_ADJUDICATION` (Adjudicación del Umbral $\theta$)

### Pregunta de Adjudicación
¿El estado `RELEVANCE_THRESHOLD_STATUS = PENDING_EMPIRICAL_CALIBRATION` impide declarar TALOS V1 terminado, o constituye una mejora de aseguramiento post-V1?

### Evidencia Documental y Contractual
1. **Especificación V1 (`docs/01-SPEC-V1.0.md`):** Define el principio de abstención (P5: *"Cuando no exista evidencia suficiente, [NO_EVIDENCE] es una salida válida y preferible a inventar"*). En ninguna sección se exige un umbral numérico $\theta$ calibrado estadísticamente para habilitar el producto.
2. **Addendum Vinculante CP111:** Prohibió expresamente inventar un threshold numérico arbitrario: *"Si no existe una escala comparable y calibrable, mantener: $\theta = \text{PENDING EMPIRICAL CALIBRATION}$. Un valor arbitrario no puede utilizarse como garantía epistemológica."*
3. **Comportamiento en Runtime (`src/study_engine/context/c5_trust.py`):** El Trust Gate C5 evalúa deterministamente la cobertura de entidades indispensables (`evaluate_term_coverage`), detecta contradicciones entre fuentes (`detect_evidence_conflicts`) y valida la continuidad temática. **Es 100% operativo, determinista y fail-closed sin requerir un $\theta$ numérico.**
4. **Cierre de Gate B:** Gate B cerró formalmente con **C5 = PASS / CLOSED** bajo esta misma condición.

### Adjudicación Oficial
```text
THETA_STATUS = POST_V1
```
* **Dictamen:** La calibración empírica de $\theta$ **NO es un requisito de aceptación funcional para V1**. C5 ya protege la frontera pre-LLM de forma fail-closed. Convertir la calibración estadística de $\theta$ en un bloqueador de V1 contradiría el contrato de Gate B y las especificaciones normativas originales.

---

## ARTIFACT D: `RETRIEVAL_CLAIM_ADJUDICATION` (Adjudicación de la Capacidad de Retrieval)

### Deconstrucción del Proceso de Recuperación
Queda prohibido utilizar "resolver" como sinónimo de "recuperar un chunk" (*hit*). La evaluación rigurosa distingue:
$$\text{Query} \;\longrightarrow\; \text{Retrieval Hit} \;\longrightarrow\; \text{Relevant Evidence} \;\longrightarrow\; \text{Sufficient Evidence} \;\longrightarrow\; \text{Correct Grounded Response}$$

### Análisis del Benchmark Histórico de 20 Preguntas
Al contrastar las 20 preguntas del benchmark con la evidencia instrumental conservada (`docs/FASE0_LINEA_BASE_TALOS_NOTEBOOKLM.md`):

| Métrica sobre 20 Preguntas | Resultado Observado | Diagnóstico Factual |
| :--- | :---: | :--- |
| **Retrieval Hit** | **17 / 20** | En 17 consultas FTS5 recuperó chunks coincidentes. En 3 consultas no hubo hit útil o no se localizó la respuesta. |
| **Relevance Verified** | **14 / 20** | Los chunks recuperados correspondían con precisión a la entidad técnica buscada (procesos, memoria, fork, threads). |
| **Sufficiency Verified** | **11 / 20** | En 11 consultas la evidencia fue suficiente. En 2 consultas hubo truncamiento por longitud (previo a C3); en 2 hubo demoras por red; en 1 hubo error 500 de API; en 1 el ejercicio no registró respuesta. |
| **Answer Correctness** | **11 / 20** | Las 11 respuestas completas emitidas fueron conceptualmente exactas y bien fundamentadas. |

### Adjudicación Oficial
```text
FTS5_CURRENT_STATUS = SUFFICIENT_FOR_V1
```
* **Dictamen:** Los fallos históricos del benchmark **nunca fueron provocados por deficiencias de FTS5**, sino por desbordes de longitud, demoras de proveedores y falta de control de formato por turno (problemas ya resueltos en Gate B por C3, C5 y F1–F6). FTS5 BM25 es **completamente suficiente para los objetivos de V1**.

---

## ARTIFACT E: `S6_STATUS_ADJUDICATION` (Adjudicación del Sandbox S6)

### Separación Conceptual Obligatoria
* **`S6 Sandbox`**: Entorno de ejecución en servidor de código arbitrario con captura de syscalls y aislamiento en contenedores.
* **`VSCode Local Verification (PR-02)`**: Flujo de evaluación determinista donde el estudiante ejecuta y prueba su código en su propio entorno local (VSCode/Linux), y TALOS audita el artefacto resultante mediante oráculos formales.

### Análisis contra la Especificación Original
En `docs/01-SPEC-V1.0.md` Sección 16 (*CÓDIGO*):
> *"El sistema nunca debe reemplazar el trabajo manual del estudiante. Flujo: STUDENT writes code $\to$ pytest $\to$ deterministic result $\to$ TESTER $\to$ conceptual audit. Python/pytest determina si el programa funciona. El LLM interpreta y enseña."*

La intención de V1 **siempre fue que el estudiante programara localmente** y que el sistema auditara determinísticamente la evidencia de ejecución. S6 surgió posteriormente como una aspiración de infraestructura centralizada.

### Adjudicación Oficial
```text
S6_STATUS = POST_V1
```
* **Dictamen:** S6 **NO bloquea la terminación de V1**. La evaluación determinista local en VSCode satisface plenamente el requisito pedagógico de V1 sin introducir la complejidad ni los riesgos de seguridad de un sandbox multi-tenant.

---

## ARTIFACT F: `E2E_STUDY_LOOP_STATUS` (Adjudicación del Gap de Integración)

### Diagnóstico de Integración
* Los componentes individuales de TALOS funcionan y están verificados:
  * Apertura de sesión y política de progresión: `test_unified_study_session.py` (14/14 passed).
  * Streaming socrático y sanitización: `test_chat_sse_endpoint.py` (passed).
  * Evaluación determinista y actualización de BKT: `test_exercise_loop.py` (passed).
  * Protocolo de lucha y currículo en espiral: `test_struggle_protocol.py` y `test_spiral_curriculum.py` (16/16 passed).
* **El Gap Real:** No existe actualmente una prueba automatizada que ejecute el ciclo pedagógico **de punta a punta en una sola secuencia continua**:
  $$\text{Session Open} \;\longrightarrow\; \text{Orientation} \;\longrightarrow\; \text{Chat Query} \;\longrightarrow\; \text{Exercise Attempt} \;\longrightarrow\; \text{Deterministic Grading} \;\longrightarrow\; \text{BKT Update} \;\longrightarrow\; \text{Next Progression Action}$$

### Diagnóstico de los Tests Históricos Rotos (`test_talos_vs_notebooklm_e2e.py`)
Los 3 fallos observados en esta suite obedecen a:
```text
TEST_OBSOLETE / CONTRACT_MISMATCH
```
Los tests antiguos utilizaban objetos `MagicMock` toscos que colisionan con el tipado estricto y el fail-closed de C5 (`TypeError: sequence item 3: expected str instance, MagicMock found`). No reflejan una regresión de producción, sino un desfasaje del arnés de prueba histórico respecto a las garantías certificadas en Gate B.

### Adjudicación Oficial
```text
E2E_STUDY_LOOP = REQUIRED_VALIDATION_GAP
```
* **Significado:** `PRODUCT BEHAVIOR NOT YET INTEGRATION-VERIFIED`. Es el único gap técnico sustantivo que debe ser cerrado para declarar la terminación de V1.

---

## ARTIFACT G: `CP113_FINAL_SCOPE` (Desglose de Runtime y UX)

El estado del subsistema Runtime/UX se desagrega de forma precisa:

1. **`FUNCTIONAL_RUNTIME`**: `SATISFIED`. FastAPI, SSE generator, `MultiFallbackBackend` (9 proveedores) y `OfflinePedagogicalBackend` completamente operativos.
2. **`INTEGRATION`**: `REQUIRED GAP`. Falta la validación unificada del Study Loop de extremo a extremo.
3. **`UX`**: `SATISFIED`. Interfaz conversacional con streaming fluido, eventos estructurados, citas depuradas en vivo y abstenciones pedagógicas explícitas.
4. **`PERFORMANCE`**: `BASELINE ESTABLISHED` (No SLO/SLA). FTS5 a 1,36 ms warm; SSE primer token a 576 ms warm. Completamente compatible con uso interactivo.
5. **`TEST_HEALTH`**: `REQUIRES SYNCHRONIZATION`. Perímetro oficial en `config/test_perimeter.json` saludable; tests históricos obsoletos desfasados respecto a C5.

---

## ARTIFACT H: `POST_GATE_B_CYCLE_1_FINAL` (Definición del Primer Ciclo Post-Gate B)

Tras las adjudicaciones normativas (donde $\theta$, vector search y S6 quedan formalmente diferidos a `POST-V1`), el **Ciclo 1 Post-Gate B se reconfigura y reduce estrictamente a dos objetivos esenciales de cierre de V1**:

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           POST-GATE-B CYCLE 1: CIERRE V1                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  OBJETIVO 1: VALIDACIÓN E2E DEL CICLO DE ESTUDIO UNIFICADO                      │
│  - Tipo: Required Validation Gap (Level B DoD).                                 │
│  - Alcance: Implementar la suite de prueba de integración que recorra el flujo  │
│             completo real (Session Open -> Chat SSE -> Exercise Grading ->      │
│             BKT Update -> Progression Policy Next Action).                      │
│  - Criterio de Terminación: Suite E2E ejecutada y aprobada al 100%.              │
│                                                                                 │
│  OBJETIVO 2: SINCRONIZACIÓN DE RELEASE Y DOCUMENTACIÓN DE SUPERFICIE            │
│  - Tipo: Release Integrity (Level C DoD).                                       │
│  - Alcance: Formalizar el catálogo de rutas soportadas de la API V1, documentar │
│             explícitamente los componentes diferidos (RetrievalFabricLite, S6,  │
│             rerankers) como POST-V1 y sanear arneses de prueba obsoletos.       │
│  - Criterio de Terminación: Manifiesto de release V1 publicado y sincronizado.  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## ARTIFACT I: `DEFERRED_WORK_FINAL` (Trabajo Postergado a Post-V1)

Queda formalmente excluido de los requisitos de cierre de TALOS V1:

1. **Calibración Empírica del Umbral $\theta$ de C5:** `POST-V1 / ASSURANCE`.
2. **Realineación Dimensional de Embeddings Vectoriales (1024d vs 384d):** `POST-V1 / V1.5`.
3. **Conexión de Rerankers Locales y Neurales al Flujo de Chat:** `POST-V1 / V1.5`.
4. **Sandbox de Ejecución de Syscalls / Contenedores (S6):** `POST-V1 / V2`.
5. **Exposición de Endpoint HTTP para LabGraderBridge:** `POST-V1 / V2`.
6. **Clon de Funcionalidades de NotebookLM (Audio, resúmenes masivos):** `NOT_REQUIRED / EXCLUDED`.
7. **Arquitectura Multi-Usuario y Autenticación en la Nube:** `NOT_REQUIRED / V2`.

---

## ARTIFACT J: `CP113-R1_VERDICT` y Respuesta Final Obligatoria

### Veredicto Oficial
```text
CP113_R1_VERDICT = V1_READY_FOR_FINAL_VALIDATION
```

> **Significado Normativo:** La definición de TALOS V1 está cerrada. Todas las capacidades de producto requeridas están satisfechas o formalmente diferidas. Lo que separa a TALOS de ser declarado `PRODUCT_COMPLETE` es exclusivamente la ejecución satisfactoria de las validaciones finales del Ciclo 1.

---

## RESPUESTA FINAL OBLIGATORIA

> **¿Qué falta exactamente para poder decir “TALOS V1 está terminado”?**

```text
V1_REQUIRED_REMAINING = [
    "E2E_STUDY_LOOP_INTEGRATION_TEST",
    "RELEASE_SURFACE_SYNCHRONIZATION"
]

V1_ALREADY_SATISFIED = [
    "GROUNDING_C1",
    "SOURCE_AUTHORIZATION_C2",
    "HARD_CEILING_C3",
    "CURRICULUM_ISOLATION_C4",
    "ABSTENTION_TRUST_GATE_C5",
    "LEXICAL_RETRIEVAL_FTS5",
    "BKT_FORMAL_EVALUATION",
    "ADAPTIVITY_CORE",
    "CURRICULUM_DAG_PROGRESSION",
    "CODE_EVALUATION_DETERMINISTIC",
    "ANTI_LEAK_SOLUTION_PROTECTION",
    "SESSION_MEMORY_SOVEREIGN",
    "SSE_STREAMING_RESILIENT"
]

POST_V1 = [
    "THETA_EMPIRICAL_CALIBRATION",
    "DENSE_VECTOR_SEARCH_REALIGNMENT",
    "RERANKER_CHAT_INTEGRATION",
    "S6_SANDBOX_SYSCALL_EXECUTION",
    "LAB_GRADER_BRIDGE_HTTP_ENDPOINT"
]

OPTIONAL = [
    "WARMUP_EMBEDDINGS_DAEMON",
    "DESKTOP_MEMORY_OPTIMIZATION_UNDER_2_2GB"
]

UNKNOWN = []

FINAL_VALIDATION_REQUIRED = [
    "RUN_UNIFIED_STUDY_LOOP_E2E_TEST"
]

CP113_R1_VERDICT = V1_READY_FOR_FINAL_VALIDATION
CP113_R1_STATUS = PASS / CLOSED
```
