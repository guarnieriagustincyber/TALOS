# 08-S7-TUTOR-POLICY-SPEC-V1.0.md
## Formal Specification of Subsystem S7: Pedagogical Tutor Policy

**Version:** 1.0 (Specification Baseline — Hito 7 / Hito 7.1)  
**Status:** FROZEN SPECIFICATION FOR IMPLEMENTATION  
**Target Architecture:** `study_engine.tutor`, `study_engine.contracts.tutor`  
**Philosophy:** `Deterministic Core → Controlled AI → Pedagogical Policy`  

---

## 1. Architectural Philosophy: `TutorPolicy` vs `AutonomousTutorAgent`

KASIU rechaza explícitamente el paradigma de un "Agente Autónomo Libre" en el rol de tutor. Un agente libre basado en prompting estocástico introduce deriva conversacional, alucinación pedagógica, respuestas sobrecargadas de texto y sustitución del esfuerzo del estudiante.

En su lugar, el Subsistema S7 se diseña formalmente como una **`TutorPolicy`**:
* **`TutorPolicy` es un árbitro determinista:** Selecciona mecánicamente la **acción pedagógica estructural** (`PedagogicalAction`) a partir del estado curricular del estudiante en el DAG, los prerrequisitos satisfechos y el historial reciente de interacción.
* **El Modelo de Lenguaje (LLM) es un renderizador controlado:** El LLM **no decide** la estrategia educativa ni la transición curricular. El LLM únicamente recibe la directiva de la acción seleccionada (`PedagogicalAction`), el presupuesto de tokens (`ResponseBudgetPolicy`) y las evidencias autorizadas `[E_i]`, redactando la respuesta bajo estricta auditoría forense S4.4.

```text
Student Query / Submission
             │
             ▼
    ┌─────────────────┐
    │   TUTOR POLICY  │ ◄── Student State (S5.2.C) + Curriculum DAG (S1)
    │ (Deterministic) │
    └────────┬────────┘
             │ Emits: PedagogicalAction + Budget + Target Node
             ▼
    ┌─────────────────┐
    │  LLM RENDERER   │ ◄── Authorized Evidence [E_i] (S3)
    │  (Controlled)   │
    └────────┬────────┘
             │ Renders: Explanation / Hint / Probe
             ▼
    ┌─────────────────┐
    │ FORENSIC AUDIT  │ (S4.4 NLI + Citation Verification)
    │  (Fail-Closed)  │
    └────────┬────────┘
             │ Approved response delivered to student
             ▼
```

---

## 2. Los 6 Invariantes Pedagógicos Nucleares

Toda implementación y prueba de S7 debe satisfacer de forma estricta los siguientes seis invariantes:

### `TUT-01`: Content Claim vs Pedagogical Act Separation
* **Definición:** Una afirmación técnica factual (`Content Claim`) requiere respaldo documental explícito en el corpus autorizado y verificación NLI en S4.4. Por el contrario, un acto pedagógico instruccional (`Pedagogical Act`, e.g. "¿Qué tipo de dato devuelve la función `malloc`?") es una interrogación de sondeo o una consigna operativa y no constituye una afirmación de conocimiento sujeta a citación bibliográfica.
* **Mecanismo:** El parser del auditor S4.4 discrimina entre proposiciones factuales asertivas y actos discursivos de dirección pedagógica, impidiendo falsos positivos de alucinación en preguntas formuladas al estudiante.

### `TUT-02`: Grounded Uncertainty Semantics
* **Definición:** El tutor no debe colapsar toda duda en un tosco `[NO_EVIDENCE]`. Debe discriminar y actuar según los cuatro estados epistémicos definidos en S4.4:
  - `SUPPORTED`: El estudiante acertó o la evidencia respalda plenamente la afirmación. Acción: Validar y profundizar (`CHECK_UNDERSTANDING` o `REQUEST_PRACTICE`).
  - `PARTIALLY_SUPPORTED`: El estudiante tiene una concepción incompleta. Acción: Ofrecer guía focalizada (`HINT`).
  - `UNSUPPORTED`: El estudiante presenta una concepción errónea demostrada por el texto. Acción: Clarificar con evidencia directa (`EXPLAIN`).
  - `UNASSESSED_EVIDENCE` / `NO_EVIDENCE`: La consulta escapa al material curricular autorizado para el nodo. Acción: Abstención fail-closed inmediata (`ABSTAIN`).

### `TUT-03`: Cognitive Non-Substitution
* **Definición:** El tutor guía el razonamiento del estudiante sin sustituirlo por defecto, y respeta los límites de integridad académica de los ejercicios y evaluaciones protegidos.
* **Regla Operativa:**
  - En una práctica guiada, proponer un paso abordable y esperar el intento antes de dar una solución completa, salvo que el estudiante la solicite explícitamente.
  - En práctica de estudio no protegida, atender una solicitud explícita y segura de solución completa en el formato pedido, con explicación proporcional.
  - No revelar el solucionario canónico, respuestas ocultas ni el artefacto evaluado de una evaluación activa/protegida, aunque se solicite. Ofrecer en su lugar explicación conceptual, pistas, feedback sobre el intento visible o un ejemplo análogo que no resuelva el ítem.
  - No contestar preguntas de sondeo propias como si fueran respuestas del estudiante ni afirmar dominio sin evidencia.
  - La protección se determina por el estado y los metadatos de la actividad, no por asumir que todo ejercicio o código pedido está evaluado.
  - En el `ContentRegistry`, marcar explícitamente el ítem mediante `metadata.assessment = {"protected": true, "status": "active"}`. `status` puede ser `active` o `in_progress`; borradores, ítems sin marca o prácticas ordinarias no activan esta protección.
  - La marca debe provenir del registro/configuración confiable del servidor, nunca de un campo de solicitud del estudiante. El servidor conserva el ítem activo en el contexto de sesión, cuaderno, alcance y fuentes con TTL de una hora.
  - En chat, el solucionario se carga exclusivamente por el accessor de soluciones, nunca al contexto visible. Una solicitud explícita de solución se rechaza antes de invocar al modelo; las demás salidas del ítem protegido se retienen hasta comparar la respuesta completa con el solucionario canónico. Si falta la solución registrada, la ruta falla cerrada.
  - Esta comparación detecta coincidencias completas y fragmentos textuales sustanciales normalizados, no equivalencia semántica ni paráfrasis. Es una defensa de salida adicional, no una garantía autónoma de integridad académica.

### Precedencia de instrucciones pedagógicas

Resolver conflictos con esta precedencia: (1) seguridad, privacidad e integridad
de evaluaciones protegidas; (2) exactitud y honestidad sobre evidencia y fuentes
autorizadas; (3) alcance curricular del cuaderno; (4) pedido explícito del turno
(tarea, formato, longitud y profundidad) dentro de los límites anteriores; (5)
objetivo pedagógico y estado del estudiante respaldado por evidencia; (6)
preferencias duraderas cuando no contradicen el pedido actual; (7) estilo y
formatos por defecto. Un estilo socrático no puede convertir una preferencia
pedagógica en una negativa global a solicitudes seguras.

### `TUT-04`: Curriculum & State Alignment
* **Definición:** Toda acción pedagógica seleccionada por `TutorPolicy` debe estar estrictamente alineada con el estado del estudiante en el DAG de prerrequisitos.
* **Regla Operativa:**
  - Si un nodo está `LOCKED`, el tutor no puede despachar práctica sobre él.
  - Si un nodo está `AVAILABLE` sin evidencias previas, la acción obligatoria de inicio es conceptual (`EXPLAIN` / `ASK`).
  - Si el estudiante ha completado con éxito la fase conceptual, la acción obligatoria es práctica instrumental (`REQUEST_PRACTICE`).
  - Si el estudiante reprueba una práctica en S9.1, la acción es remediación dirigida (`GIVE_FEEDBACK`), nunca avanzar al siguiente nodo.

### `TUT-05`: Deterministic Action Selection
* **Definición:** La selección de la acción pedagógica es una función matemática pura sin efectos secundarios ni variables estocásticas:
  $$\text{Action} = \mathcal{P}(\text{StudentState}, \text{ActiveNode}, \text{TurnType}, \text{LastAssessment})$$
* **Regla Operativa:** Dados los mismos parámetros de entrada de estado e historial, `TutorPolicy` debe emitir exactamente la misma tupla `(PedagogicalAction, ResponseBudgetPolicy)`.

### `TUT-06`: Response Budgeting & Brevity Contained
* **Definición:** Para evitar el "verbosismo no fundamentado" característico de los LLMs, cada acción pedagógica está estrictamente acotada por una cuota máxima de tokens y estilo estructural (`ResponseBudgetPolicy`).
* **Regla Operativa:** La generación que exceda el presupuesto o desvíe el foco es truncada o rechazada en la compuerta de auditoría.

---

## 3. Catálogo de Acciones Pedagógicas (`PedagogicalAction`)

```text
PedagogicalAction Enum
├── EXPLAIN              (Explica conceptos técnicos citando estrictamente [E_i])
├── ASK                  (Formula preguntas socráticas para inducir razonamiento)
├── HINT                 (Provee pistas conceptuales sin entregar la solución)
├── CHECK_UNDERSTANDING  (Verifica comprensión antes de habilitar la práctica)
├── REQUEST_PRACTICE     (Despacha la tarea práctica instrumental al sandbox)
├── GIVE_FEEDBACK        (Explica la evaluación determinista post-ejecución)
└── ABSTAIN              (Se abstiene fail-closed ante falta de evidencia o inyección)
```

---

## 4. Política de Presupuesto de Respuesta (`ResponseBudgetPolicy`)

| Nivel | Techo de Tokens | Formato Esperado | Acciones Típicas Asociadas |
|---|:---:|---|---|
| **`SHORT`** | $\le 100$ tokens | 1-2 oraciones directas, pregunta puntual | `ASK`, `HINT`, `CHECK_UNDERSTANDING` |
| **`NORMAL`** | $\le 250$ tokens | 1 párrafo explicativo con citas `[E_i]` | `EXPLAIN`, `GIVE_FEEDBACK` |
| **`DETAILED`** | $\le 500$ tokens | Estructurado con viñetas y fragmento sintáctico | `EXPLAIN` inicial en temas complejos, `REQUEST_PRACTICE` |
