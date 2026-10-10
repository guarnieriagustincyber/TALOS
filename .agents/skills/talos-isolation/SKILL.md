# TALOS — `talos-isolation`

**Versión:** 3.1  
**Jurisdicción:** Aislamiento, fronteras alcanzables y efectos autorizados  
**Estado:** Conceptualmente congelado  
**Ubicación canónica:** `.agents/skills/talos-isolation/SKILL.md`

---

## 1. Propósito

`talos-isolation` es la jurisdicción de TALOS encargada de responder:

> **¿Hasta dónde puede llegar realmente una operación y qué recursos puede alcanzar bajo el lifecycle examinado?**

La skill determina si una operación está:

- aislada;
- confinada sintéticamente;
- autorizada solo para lectura;
- autorizada externamente;
- no tocando un recurso;
- desconocida;
- comprometida.

---

# 2. Principio rector

> **El aislamiento es una propiedad demostrada de efectos alcanzables, no una intención declarada.**

No aceptar como demostración suficiente:

```text
use_mock=True
fake_provider
test_db
fixture_copy
temporary_name
configuration label
```

La pregunta real es:

> **¿Qué recursos puede alcanzar la operación durante todo el lifecycle relevante?**

---

# 3. SKILL_INTERFACE

## 3.1. Produce

```text
ISOLATION_CONTRACT
ISOLATION_MATRIX
STATIC_ISOLATION_ASSESSMENT
ESCAPE_TEST_REQUEST
ISOLATION_VERDICT
BOUNDARY_STATUS
```

Puede producir observaciones de aislamiento, pero los resultados de ejecución de tests pertenecen a `talos-testing`.

---

## 3.2. Consume

```text
PROTECTED_RESOURCE_REGISTRY
ENVIRONMENT_PROFILE
OBSERVATION_RECORD
ESCAPE_OBSERVATION
SIDE_EFFECT_RECORD
EVIDENCE_REF
TEST_EXECUTION_RESULT
TEST_HEALTH
AUTHORIZATION_RECORD
POLICY_IDENTITY
```

Todos los objetos deben validarse en el punto de consumo.

---

## 3.3. Decide

Dentro de su jurisdicción:

- estado de una frontera de aislamiento;
- clasificación de recursos alcanzables;
- si una operación está demostrablemente confinada;
- si existe evidencia de escape;
- verdict global de aislamiento.

---

## 3.4. No decide

No puede producir:

```text
TEST_PASS
TEST_FAIL
TEST_HEALTH
EVIDENCE_TRUTH
PEDAGOGICAL_CONFORMITY
MASTERY
RELEASE_VERDICT
```

---

# 4. Postura por defecto

La postura predeterminada es:

```text
SYNTHETIC
READ-ONLY
MINIMUM-SCOPE
FAIL-CLOSED
NO-PRODUCTION-ACCESS
```

La operación real solo se habilita cuando existe autorización explícita y el contrato de aislamiento lo permite.

---

# 5. Modelo de recurso protegido

Los recursos relevantes incluyen:

```text
DATABASE
CORPUS
MODEL
PROVIDER
FILESYSTEM
PERSISTENCE
STUDENT_STATE
SECRETS
ENVIRONMENT
CACHE
TEMPORARY_STATE
NETWORK
TELEMETRY
LOCKS
SCHEDULERS
PROCESS
SUBPROCESS
DYNAMIC_LOADING
RELEASE
DEPLOYMENT
```

Para cada recurso identificar:

```text
RESOURCE_ID
CRITICALITY
SENSITIVITY
AUTHORIZED_ACCESS_MODE
FORBIDDEN_ACCESS_MODE
SYNTHETIC_SUBSTITUTE
OBSERVATION_MECHANISM
```

---

# 6. Isolation Contract

Toda operación crítica debe tener:

```text
OPERATION
PURPOSE
SCOPE
LIFECYCLE
AUTHORIZED_RESOURCES
FORBIDDEN_RESOURCES
AUTHORIZED_ACCESS_MODES
FORBIDDEN_ACCESS_MODES
OBSERVATION_METHODS
STOP CONDITIONS
RECOVERY CONDITIONS
POLICY_IDENTITY
```

---

# 7. Isolation Matrix

La matriz debe permitir responder, por cada frontera:

```text
RESOURCE
EXPECTED ACCESS
AUTHORIZED ACCESS
OBSERVED ACCESS
OBSERVATION METHOD
STATUS
EVIDENCE
LIMITATIONS
```

---

# 8. Lifecycle completo

El aislamiento debe analizar el lifecycle relevante:

```text
IMPORT
    ↓
CONSTRUCTION
    ↓
STARTUP
    ↓
LIFESPAN
    ↓
EXECUTION
    ↓
BACKGROUND TASKS
    ↓
SHUTDOWN
    ↓
CLEANUP
    ↓
POST-OPERATION OBSERVATION WINDOW
```

No considerar aislada una operación simplemente porque la función principal no accede al recurso.

Los efectos pueden aparecer:

- durante imports;
- factories;
- startup;
- warmups;
- background tasks;
- shutdown;
- cleanup;
- threads;
- subprocesses;
- callbacks.

---

# 9. Reachability

La frontera se define por efectos alcanzables.

No por:

- intención;
- nombre;
- documentación;
- flag;
- mock;
- variable;
- comentario.

Conceptualmente:

```text
CONFIGURATION
    ↓
DEPENDENCY GRAPH
    ↓
EXECUTION PATHS
    ↓
REACHABLE EFFECTS
    ↓
RESOURCE BOUNDARY
```

---

# 10. Assurance levels

Puede utilizarse una escala:

```text
L0 — UNKNOWN
L1 — DECLARED
L2 — STATICALLY ANALYZED
L3 — OBSERVED
L4 — DYNAMICALLY VERIFIED
L5 — ADVERSARIALLY VERIFIED
```

Un nivel superior no debe inferirse simplemente porque exista documentación.

La política aplicable determina qué nivel requiere una conclusión concreta.

---

# 11. Estados de frontera

Cada recurso puede clasificarse como:

```text
ISOLATION_PROVEN_ISOLATED
ISOLATION_PROVEN_SYNTHETIC
ISOLATION_AUTHORIZED_READ_ONLY
ISOLATION_AUTHORIZED_EXTERNAL
ISOLATION_PROVEN_IRRELEVANT
ISOLATION_NOT_TOUCHED
ISOLATION_UNKNOWN
ISOLATION_BREACHED
```

### Importante

```text
NOT_TOUCHED
```

no significa:

```text
PROVEN_ISOLATED
```

La ausencia de acceso observado puede ser una observación útil, pero solo constituye demostración de incapacidad cuando la observabilidad y el método permiten sostener esa conclusión.

---

# 12.1. Global isolation verdict

Los estados globales son:

```text
ISOLATION_DEMONSTRATED
ISOLATION_PARTIALLY_DEMONSTRATED
ISOLATION_NOT_DEMONSTRATED
ISOLATION_BREACHED
```

Reglas:

```text
critical boundary BREACHED
    → ISOLATION_BREACHED
```

y:

```text
critical boundary UNKNOWN
    +
no sufficient proof
    → ISOLATION_NOT_DEMONSTRATED
```

No transformar unknown crítico en demostración.

---

# 13. Instrumentation

Para demostrar ausencia de efectos es necesario que exista observabilidad suficiente.

Distinguir:

```text
OBSERVABILITY_PROVEN
OBSERVABILITY_PARTIAL
OBSERVABILITY_UNKNOWN
OBSERVABILITY_FAILED
```

Una ausencia observada mediante instrumentación válida significa:

> **No se observó el efecto mediante el mecanismo X.**

No significa automáticamente:

> **El efecto es imposible.**

---

# 14. Positive proof

La demostración positiva debe comprobar que los recursos autorizados son alcanzables dentro de los límites esperados.

Ejemplo:

```text
synthetic DB
    ↓
operation
    ↓
expected interaction
    ↓
observed
```

Esto demuestra comportamiento sobre el recurso autorizado.

---

# 15. Negative proof / escape test

Para fronteras críticas se requiere, cuando sea seguro y apropiado:

```text
POSITIVE PROOF
+
NEGATIVE PROOF / SAFE ESCAPE TEST
```

Un escape test debe ser:

```text
SAFE
SYNTHETIC
BOUNDED
OBSERVABLE
REVERSIBLE
```

Nunca utilizar producción como campo de experimentación para demostrar aislamiento si existe una alternativa segura.

---

# 16. Escape Test Request

Cuando `talos-isolation` necesita verificar una frontera mediante testing puede producir:

```text
ESCAPE_TEST_REQUEST
```

que describa:

```text
TARGET_BOUNDARY
EXPECTED_BLOCK
SAFE_INPUT
EXPECTED_OBSERVATION
FORBIDDEN_EFFECT
OBSERVATION_MECHANISM
STOP_CONDITION
RECOVERY_CONDITION
```

`talos-testing` ejecuta el test.

Isolation interpreta el resultado dentro de su propia jurisdicción.

---

# 17. Boundary between testing and isolation

La secuencia canónica es:

```text
STATIC_ISOLATION_ANALYSIS
        ↓
ISOLATION_TEST_BOUNDARY
        ↓
TEST_EXECUTION
        ↓
ESCAPE_OBSERVATIONS
        ↓
FINAL_ISOLATION_VERDICT
        ↓
GATE_ADMISSIBILITY
```

Importante:

```text
TEST_EXECUTION_ELIGIBLE
        ≠
GATE_ELIGIBLE
```

Un test puede ejecutarse legítimamente para producir evidencia de aislamiento aunque todavía no sea admisible como evidencia suficiente para un gate.

---

# 18. Testing no adjudica isolation

`talos-testing` puede producir:

```text
ESCAPE_OBSERVATION
UNEXPECTED_SIDE_EFFECT
TEST_EXECUTION_RESULT
```

Pero no puede producir:

```text
ISOLATION_DEMONSTRATED
ISOLATION_BREACHED
```

La clasificación formal pertenece a `talos-isolation`.

---

# 19. Audit boundary

`talos-audit` puede reconstruir:

- execution paths;
- side effects;
- dependencies;
- startup;
- persistence;
- subprocesses.

Isolation consume esas observaciones cuando sean relevantes.

Pero:

```text
AUDIT_VERIFIED
```

no equivale automáticamente a:

```text
ISOLATION_DEMONSTRATED
```

---

# 20. Evidence boundary

`talos-evidence` proporciona:

- evidence refs;
- provenance;
- lineage;
- preservation;
- integrity.

Isolation puede consumirlos para sustentar un verdict.

Pero:

```text
EVIDENCE_INTEGRITY_CHECKED
```

no equivale automáticamente a:

```text
ISOLATION_DEMONSTRATED
```

La evidencia debe satisfacer las precondiciones de aislamiento actuales.

---

# 21. Consumer evaluation

Cuando isolation consume un objeto externo para satisfacer una precondición propia debe registrar una evaluación:

```text
CONSUMER_EVALUATION
```

La evaluación responde:

> ¿Este objeto satisface la precondición de aislamiento que necesito ahora?

No:

> ¿Este objeto es verdadero universalmente?

---

# 22. Composition rule

Isolation puede producir un `ISOLATION_VERDICT` compuesto a partir de inputs externos cuando una política aplicable lo permite.

Debe existir una:

```text
COMPOSITION_RULE
```

y:

```text
OUTPUT_AUTHORITY
    ∈
AUTHORIZED_COMPOSER.MAY_PRODUCE
```

La composición debe verificar:

```text
INPUTS_REQUIRED
PRODUCER_REQUIRED_PER_INPUT
SCOPE_COMPATIBILITY
TEMPORAL_COMPATIBILITY
POLICY
STATUS
```

---

# 23. Anti-pass-through

F-16 no exige que isolation duplique las observaciones de testing.

Sí exige que isolation ejerza su propia jurisdicción.

### Correcto

```text
testing
    → ESCAPE_OBSERVATION

evidence
    → EVIDENCE_REF

isolation
    → valida inputs
    → evalúa boundary
    → ejecuta su lógica de aislamiento
    → registra CONSUMER_EVALUATION
    → produce ISOLATION_VERDICT
```

### Incorrecto

```text
testing
    → “no hubo escape”

isolation
    → “entonces ISOLATION_DEMONSTRATED”
```

sin ejecutar su evaluación de aislamiento.

La diferencia es:

```text
CONSUMO DE EVIDENCIA
        ≠
DELEGACIÓN DE AUTORIDAD
```

---

# 24. No-transferencia

Un objeto de testing no transfiere autoridad de testing a isolation.

Un objeto de evidence no transfiere autoridad de evidence a isolation.

Isolation conserva su propia jurisdicción.

---

# 25. Contradicciones

Si isolation recibe objetos incompatibles:

```text
A → no escape
B → escape
```

debe ejecutar:

```text
CONTRADICTION_CHECK
```

antes de producir un verdict compuesto.

No seleccionar silenciosamente el input conveniente.

Las contradicciones cross-skill se reportan a `talos-audit` para su adjudicación; isolation no asume esa propiedad.

## F-17 — Bounded meta-verification

Una `GATE_EVALUATION` puede ser meta-verificada con revisión terminal de audit/humana. La recursión es acotada y la revisión terminal no crea autoridad transversal nueva.

---

# 26. Unknown

Si una frontera crítica es:

```text
ISOLATION_UNKNOWN
```

y no existe evidencia suficiente para resolverla:

```text
ISOLATION_NOT_DEMONSTRATED
```

No:

```text
ISOLATION_DEMONSTRATED
```

por ausencia de síntomas.

---

# 27. Blast radius

Ante un side effect inesperado:

```text
STOP
    ↓
PRESERVE
    ↓
CLASSIFY
    ↓
VERIFY
    ↓
ASSESS BLAST RADIUS
    ↓
RECOVER IF AUTHORIZED
```

Nunca continuar el experimento para “confirmar”.

---

# 28. Protected production resources

Por defecto proteger:

```text
production DB
real corpus
production indexes
real StudentState
production models
persistent storage
secrets
real provider credentials
production caches
real telemetry
production schedulers
```

Una operación que necesite alguno debe declarar:

```text
RESOURCE
ACCESS MODE
AUTHORIZATION
PURPOSE
BOUNDARY
OBSERVATION
RECOVERY
```

---

# 29. B0.5

El perfil conceptual B0.5 requiere demostrar:

```text
IMPORT
CONSTRUCTION
STARTUP
```

sin acceso no autorizado a:

- production DB;
- real corpus;
- real model;
- provider;
- StudentState;
- secrets;
- protected persistence.

El uso de:

```text
AppContainer(use_mock=True)
```

por sí solo no constituye demostración.

---

# 30. B1

B1 debe ejecutarse dentro de un entorno sintético explícitamente definido.

Debe existir:

```text
ENVIRONMENT_PROFILE
ISOLATION_CONTRACT
STATIC_ISOLATION_ASSESSMENT
TEST_CONTRACTS
OBSERVATION_MECHANISMS
ISOLATION_VERDICT
```

El test B1 no puede satisfacer su propia dependencia de aislamiento.

---

# 31. Context routing

Para una tarea centrada en aislamiento:

```text
CORE
    AGENTS.md

ACTIVE
    talos-isolation

SUPPORTING
    talos-testing
    talos-evidence
    talos-audit

DORMANT
    talos-pedagogy
    talos-release
```

Esto puede cambiar si el scope demuestra que otra skill está materialmente afectada.

Ante boundary desconocida:

> ampliar contexto, no reducirlo.

---

# 32. Temporalidad

Un verdict de aislamiento está ligado a:

```text
ENVIRONMENT_PROFILE
POLICY_IDENTITY
SCOPE
RUN_ID
RELEVANT COMMIT / TREE
OBSERVATION WINDOW
```

Un cambio material del entorno puede requerir reevaluación.

No asumir:

```text
ISOLATION_DEMONSTRATED en T1
=
ISOLATION_DEMONSTRATED en T2
```

sin comprobar aplicabilidad.

---

# 33. Revalidation at consumption

Incluso si un `ISOLATION_VERDICT` fue válido cuando se produjo, el consumidor debe comprobar:

```text
IDENTITY
SCOPE
TEMPORALITY
POLICY
STATUS
PROVENANCE
```

antes de utilizarlo para una nueva decisión.

> **Un verdict histórico no es automáticamente aplicable al presente.**

---

# 34. Three-strike circuit breaker

Tras tres intentos sin progreso significativo:

```text
STOP
PRESERVE
RECLASSIFY
REVIEW
```

No seguir modificando el entorno para conseguir un verdict conveniente.

---

# 35. Completion criteria

Un aislamiento está suficientemente evaluado cuando:

```text
[ ] OPERATION definida
[ ] LIFECYCLE definido
[ ] RESOURCES clasificados
[ ] ACCESS MODES definidos
[ ] BOUNDARIES definidas
[ ] STATIC ANALYSIS realizada cuando corresponde
[ ] OBSERVABILITY evaluada
[ ] POSITIVE PROOF realizado cuando corresponde
[ ] NEGATIVE / ESCAPE PROOF realizado cuando corresponde
[ ] ESCAPE OBSERVATIONS preservadas
[ ] CONTRADICTIONS revisadas
[ ] UNKNOWN visibles
[ ] AUTHORIZATION comprobada
[ ] ENVIRONMENT_PROFILE identificado
[ ] POLICY_IDENTITY identificada
[ ] VERDICT emitido dentro de jurisdicción
[ ] LIMITATIONS documentadas
```

---

# 36. Regla final

> **Isolation is a demonstrated property.**

No se demuestra mediante nombres, intención o confianza.

Se demuestra mediante:

```text
ALCANCE DEFINIDO
+
LIFECYCLE
+
RECURSOS CLASIFICADOS
+
OBSERVABILIDAD
+
PRUEBA POSITIVA
+
PRUEBA NEGATIVA CUANDO CORRESPONDA
+
EVIDENCIA
+
EVALUACIÓN PROPIA
+
VERDICT DENTRO DE JURISDICCIÓN
```

Y siempre:

> **La ausencia de evidencia de escape no equivale, por sí sola, a prueba de imposibilidad de escape.**
