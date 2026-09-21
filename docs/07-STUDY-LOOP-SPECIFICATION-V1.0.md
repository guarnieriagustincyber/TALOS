# 07-STUDY-LOOP-SPECIFICATION-V1.0.md
## Formal Specification of the KASIU Real Study Loop (Learning Loop V1)

**Version:** 1.0 (Specification Baseline — Hito 7)  
**Status:** FROZEN SPECIFICATION FOR IMPLEMENTATION  
**Applicability:** `study_engine.session`, `study_engine.tutor`, `study_engine.curriculum`  
**Core Invariant:**  
$$\text{Study Loop Invariant} \equiv \text{Deterministic State} \land \text{Grounded Explanation} \land \text{Sovereign Assessment}$$

---

## 1. Executive Summary & Architectural Purpose

El propósito de **Hito 7: Real Study Loop** es transformar a KASIU de un conjunto de subsistemas deterministas aislados y verificados adversarialmente en una **experiencia de estudio real completa y coherente**.

El Study Loop orquesta la progresión del estudiante a través del currículum acoplando dos modalidades complementarias:
1. **El Ciclo Conceptual (Diálogo Guiado y Grounded):** Donde el estudiante adquiere y clarifica modelos mentales basados estrictamente en el corpus autorizado, auditado por S4.4.
2. **El Ciclo Práctico (Ejecución Instrumental y Rúbrica Determinista):** Donde el estudiante demuestra maestría técnica resolviendo desafíos de programación en sandbox aislado, evaluados por S9.1 y persistidos en el ledger S5.2.B.

---

## 2. The 10-Stage Learning Loop Pipeline

El flujo de aprendizaje formal de KASIU se estructura en 10 etapas estrictamente secuenciales y gobernadas por compuertas duras:

```text
  [1] OBJECTIVE RESOLUTION (Curriculum & State)
             │
             ▼
  [2] EVIDENCE RETRIEVAL (Epistemic Scope Filter & Hybrid Retrieval)
             │
             ▼
  [3] GROUNDED EXPLANATION & ACTION PROPOSAL (TutorPolicy + S4.4 Audit)
             │
             ▼
  [4] STUDENT ACTION / INTERACTION (Question, Clarification, Ready)
             │
             ▼
  [5] PRACTICE DISPATCH (Task & Rubric Presentation)
             │
             ▼
  [6] INSTRUMENTAL EXECUTION (Tier 0 Sandbox Isolation)
             │
             ▼
  [7] DETERMINISTIC ASSESSMENT (Artifact Extraction & Rule Grading)
             │
             ▼
  [8] AUTHORITATIVE EVIDENCE INGESTION (Provenance & D(K, R) Gate)
             │
             ▼
  [9] PURE STATE DERIVATION (DAG Progress & Unlocks)
             │
             ▼
  [10] NEXT PEDAGOGICAL ACTION (Feedback, Remedy, or Advance)
```

### Detalle Operativo por Etapa:
1. **`[1] Objective Resolution`:** Consulta `CurriculumRegistry` y `CurriculumStateAdapter`. Determina el nodo curricular activo del estudiante (`target_node_id`), verifica que sus prerrequisitos duros estén satisfechos (`status == AVAILABLE` o `IN_PROGRESS`) y extrae los objetivos pedagógicos asociados.
2. **`[2] Evidence Retrieval`:** Invoca `RetrievalService`. Aplica el filtro del ámbito autorizado (`AUTHORIZED_SCOPE`) según la matriz de alineación curricular del nodo. Extrae únicamente fragmentos con fidelidad de página verificada. Si no hay evidencia autorizada, la etapa se abstiene inmediatamente (`NO_EVIDENCE`).
3. **`[3] Grounded Explanation`:** `TutorPolicy` selecciona la acción pedagógica adecuada (`EXPLAIN`, `CHECK_UNDERSTANDING`). El generador redacta la explicación consumiendo el contexto formateado `[E_i]`. `ForensicAuditor` (S4.4) audita el texto: si hay alucinación o citas no fundamentadas, la respuesta se bloquea fail-closed.
4. **`[4] Student Action`:** El estudiante interactúa formulando dudas conceptuales o respondiendo a la pregunta de sondeo socrático emitida por el tutor.
5. **`[5] Practice Dispatch`:** Cuando el entendimiento conceptual ha sido constatado, `TutorPolicy` emite `REQUEST_PRACTICE`. El sistema recupera la tarea práctica (`PracticalTaskSpecification`) y presenta las instrucciones y el contrato de entrega al estudiante.
6. **`[6] Instrumental Execution`:** El estudiante remite su artefacto de código. `PracticalExecutionAdapter` ejecuta el proceso dentro de una sesión POSIX aislada con variables de entorno limpias, directorio efímero y cuota temporal de CPU ($\le 300\text{ s}$).
7. **`[7] Deterministic Assessment`:** `DeterministicAssessmentAdapter` (S9.1) analiza los artefactos resultantes (existencia, tamaño de archivo, digest SHA-256 de salida, código de retorno) y emite un `AssessmentResult` inmutable.
8. **`[8] Authoritative Evidence Ingestion`:** `EvidenceIngestionAdapter` (S5.2.A) evalúa la tupla contra la función de decisión $D(K, R)$ y la inscribe en el ledger SQLite WAL con sellado criptográfico y proveniencia verificada.
9. **`[9] Pure State Derivation`:** `CurriculumStateAdapter` invoca `derive_student_state()`, actualizando el estado de maestría del nodo (`ASSESSED_PROFICIENT`) y habilitando nodos downstream en el DAG (`AVAILABLE`).
10. **`[10] Next Pedagogical Action`:** El tutor analiza el nuevo estado del DAG y el resultado evaluativo, emitiendo retroalimentación inmediata (`GIVE_FEEDBACK`) y orientando al estudiante hacia el siguiente objetivo curricular.

---

## 3. Hexagonal Architecture: Ports & Adapters

Para salvaguardar el perímetro congelado, la orquestación del Study Loop interactúa exclusivamente mediante puertos abstractos:

```text
                             STUDY LOOP CONTROLLER
                                (Session Engine)
                                       │
        ┌──────────────┬───────────────┼───────────────┬──────────────┐
        ▼              ▼               ▼               ▼              ▼
   CurriculumPort  RetrievalPort   TutorPolicyPort  ExecutionPort  AssessmentPort
        │              │               │               │              │
        ▼              ▼               ▼               ▼              ▼
    Curriculum     Retrieval      Deterministic     Python         Deterministic
     Registry       Service        TutorPolicy      Adapter          Engine
      (S1)           (S3)             (S7)          (S6.1)           (S9.1)
                                                       │              │
                                                       └──────┬───────┘
                                                              ▼
                                                   EvidenceIngestionPort
                                                              │
                                                              ▼
                                                        IngestionEngine
                                                            (S5.2.A)
                                                              │
                                                              ▼
                                                       AuthoritativeLedger
                                                            (S5.2.B)
                                                              │
                                                              ▼
                                                        StateReadPort
                                                              │
                                                              ▼
                                                         StateEngine
                                                            (S5.2.C)
```

### Puertos de Salida (Outbound Ports):
* **`CurriculumPort`:** Provee acceso de solo lectura al roadmap, tareas, rúbricas y matriz de alineación.
* **`RetrievalPort`:** Ejecuta la recuperación híbrida restringida por el ámbito epistémico del nodo.
* **`TutorPolicyPort`:** Función pura que decide la siguiente acción pedagógica según el estado del estudiante y el historial de diálogo.
* **`GenerationPort`:** Renderiza texto pedagógico a partir de la acción seleccionada y las citas autorizadas.
* **`AuditPort`:** Realiza auditoría forense NLI de las afirmaciones y citas antes de entregarlas al estudiante.
* **`ExecutionPort`:** Ejecuta código del estudiante en sandbox Tier 0.
* **`AssessmentPort`:** Evalúa observaciones instrumentales contra la rúbrica determinista.
* **`EvidenceIngestionPort`:** Persiste evidencias autorizadas en el ledger bajo la semántica $D(K, R)$.
* **`StateReadPort`:** Deriva el estado proyectado del estudiante a partir del ledger.

---

## 4. Perímetro Modificable vs Perímetro Congelado

### Perímetro Estrictamente Congelado (PROHIBIDO MODIFICAR):
* `src/study_engine/state/` (Ingestion, Ledger SQLite WAL, State Engine, Policy Engine).
* `src/study_engine/execution/` (Python Adapter, Process Manager, Sanitizer).
* `src/study_engine/assessment/` (Evaluator Deterministic, Aggregator, Service).
* `src/study_engine/audit/` (Auditor S4.4, Citation Verifier, NLI Engine, Guards).

### Perímetro Habilitado para Modificación / Implementación:
* `src/study_engine/session/` (Orchestrator, Controllers, Loop Adapters).
* `src/study_engine/contracts/` (Nuevos contratos como `tutor.py`).
* `src/study_engine/tutor/` (Implementación de `TutorPolicy`).
* `data/experiments/study_loop_v1/` (Oráculos diferenciales y telemetría).
* `tests/integration/` y `tests/experiments/` (Suites del Study Loop).

### 4.1 Compatibilidad aditiva de contratos de sesión (Aclaración M1)

`src/study_engine/session/contracts.py` pertenece al perímetro habilitado. Sus
contratos públicos pueden evolucionar de forma **aditiva y compatible** para
transportar metadata de interacción del Study Loop, incluidos campos opcionales
tipados como `SessionResult.pedagogical_followup`.

Quedan prohibidos en esa evolución la eliminación de campos existentes y el
cambio de tipo, semántica o autoridad de un campo existente. La metadata
pedagógica no otorga autoridad sobre el ledger, el estado o la evaluación, y
no amplía el payload factual auditado por S4.4.

Los manifiestos de hash GP-B que abarcan todo `src/study_engine/` son evidencia
histórica de esa campaña; no redefinen este perímetro normativo ni bloquean una
extensión compatible en `session/`, `contracts/` o `tutor/`.

---

## 5. Máquina de Estados Finitos del Study Loop (FSM)

El ciclo de sesión implementa una FSM determinista:

```text
           ┌──────────────┐
           │ UNINITIALIZED│
           └──────┬───────┘
                  │ initialize(student_id, roadmap_id)
                  ▼
           ┌──────────────┐
           │    READY     │◄────────────────────────────────┐
           └──────┬───────┘                                 │
                  │ student_query (conceptual)              │
                  ▼                                         │
           ┌──────────────┐                                 │
           │ CONCEPTUAL_  │──(Audited Explanation)──────────┤
           │ EXPLANATION  │                                 │
           └──────┬───────┘                                 │
                  │ check_understanding passed              │
                  ▼                                         │
           ┌──────────────┐                                 │
           │  PRACTICE_   │                                 │
           │  DISPATCHED  │                                 │
           └──────┬───────┘                                 │
                  │ submit_solution(artifact)               │
                  ▼                                         │
           ┌──────────────┐                                 │
           │  EVALUATING_ │                                 │
           │  PRACTICE    │                                 │
           └──────┬───────┘                                 │
                  │ assessment complete + evidence ingested │
                  ▼                                         │
           ┌──────────────┐                                 │
           │ STATE_UPDATED│─────────────────────────────────┘
           └──────────────┘
```

### Transiciones y Eventos:
* `INIT`: Carga estado inicial (raíces `AVAILABLE`, resto `LOCKED`).
* `CONCEPTUAL_TURN`: Ejecuta recuperación, empaquetado, generación y auditoría S4.4. Transiciona a `READY`.
* `PRACTICE_TURN`: Despacha la tarea, ejecuta el sandbox, evalúa con S9.1, persiste en S5.2.B y actualiza S5.2.C. Si aprueba, transiciona a `STATE_UPDATED` y desbloquea el siguiente nodo.
