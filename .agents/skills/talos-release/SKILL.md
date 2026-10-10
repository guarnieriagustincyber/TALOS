# TALOS — `talos-release`

**Versión:** 3.1  
**Jurisdicción:** Adjudicación de release y composición de gates  
**Estado:** Conceptualmente congelado  
**Ubicación canónica:** `.agents/skills/talos-release/SKILL.md`

---

# 1. Propósito

`talos-release` es la jurisdicción de TALOS encargada de responder:

> **¿Es este estado concreto del sistema liberable dentro del scope y la política de release aplicables?**

Una release es una adjudicación basada en evidencia ensamblada.

No es:

```text id="z4f3w7"
SUM(PASS)
```

---

# 2. Principio rector

> **A release is an adjudication based on assembled evidence, not the sum of passing components.**

Y la regla central:

> **`talos-release` nunca puede aumentar la fuerza epistemológica de sus inputs.**

Solo puede comprobar si la fuerza, scope, validez, provenance y aplicabilidad de los inputs satisfacen la política de release.

---

# 3. SKILL_INTERFACE

## 3.1. Produce

```text id="j9s6re"
GATE_EVALUATION
RELEASE_EVIDENCE_PACKET
RESIDUAL_RISK_RECORD
RELEASE_VERDICT
RELEASE_ARTIFACT
WAIVER_RECORD
```

---

## 3.2. Consume

Puede consumir:

```text id="x5k4zq"
AUDIT_FINDING
AUDIT_UNKNOWN
ISOLATION_VERDICT
TEST_EXECUTION_RESULT
TEST_HEALTH
TEST_ADMISSIBILITY
EVIDENCE_REF
EVIDENCE_INTEGRITY_STATUS
PEDAGOGICAL_CONFORMITY_STATUS
PEDAGOGICAL_IMPACT_RECORD
AUTHORIZATION_RECORD
ENVIRONMENT_PROFILE
POLICY_IDENTITY
ASSUMPTION_RECORD
CONTRADICTION_RECORD
UNKNOWN_RECORD
```

Todo objeto debe ser revalidado en el punto de consumo.

---

## 3.3. No produce

No puede producir:

```text id="2v3qf6"
TEST_EXECUTION_RESULT
ISOLATION_VERDICT
EVIDENCE_INTEGRITY
AUDIT_FINDING
PEDAGOGICAL_CONFORMITY
MASTERY
BKT
```

---

# 4. Release authority

La autoridad de release sigue:

```text id="s0m5yq"
AGENTS.md
    ↓
TALOS RELEASE POLICY
    ↓
talos-release
    ↓
RELEASE VERDICT
```

La skill no puede:

- modificar invariantes;
- relajar gates;
- reinterpretar evidencia;
- convertir unknown en pass;
- otorgar autorizaciones;
- convertir evidencia sintética en productiva.

---

# 5. Release scope

Todo release debe identificar:

```text id="a4t9cx"
RELEASE_ID
RELEASE_SCOPE_ID
AFFECTED_COMPONENTS
CROSSED_BOUNDARIES
REPOSITORY_STATE
APPLICABLE_GATES
REQUIRED_AUTHORIZATIONS
TEMPORAL_SCOPE
RELEASE_POLICY_ID
```

No existe un release abstracto separado de su scope.

---

# 6. Repository state

El estado del sistema debe quedar identificado mediante información suficiente para reconstruirlo, por ejemplo:

```text id="h6g8wb"
COMMIT
TREE / WORKTREE STATE
DEPENDENCY STATE
CONFIGURATION
ENVIRONMENT_PROFILE
POLICY_IDENTITY
EVIDENCE SET
```

Una evidencia histórica válida no se vuelve automáticamente aplicable a un estado nuevo.

---

# 7. Release policy identity

Registrar:

```text id="g1c5x4"
RELEASE_POLICY_ID
VERSION
HASH
STATUS
VALIDITY_INTERVAL
```

Un cambio material de política puede requerir reevaluación.

---

# 8. Release lifecycle

Separar:

```text id="b4j2mw"
RELEASE_REQUEST
    ↓
RELEASE_CANDIDATE
    ↓
RELEASE_ADJUDICATION
    ↓
RELEASE_VERDICT
    ↓
RELEASE_ARTIFACT
    ↓
DEPLOYMENT
    ↓
POST_RELEASE_OBSERVATION
```

Deployment no es parte del verdict de release.

---

# 9. Gate Contract

Cada gate debe definir:

```text id="c7k5z9"
GATE_ID
GATE_TYPE
ACCEPTANCE_CRITERION
REQUIRED_EVIDENCE
PRODUCER_SKILL
VERIFICATION_METHOD
BLOCKING
AUTHORITY
DEPENDENCIES
```

Tipos:

```text id="v8p0n3"
INVARIANT
SCOPE_DEPENDENT
AUTHORIZATION
```

---

# 10. Gate statuses

```text id="s6r4bc"
GATE_SATISFIED
GATE_NOT_SATISFIED
GATE_BLOCKED
GATE_UNKNOWN
GATE_NOT_APPLICABLE
GATE_WAIVED
```

Por defecto:

```text id="1h3n7a"
NOT_SATISFIED
BLOCKED
UNKNOWN
```

bloquean release cuando el gate es blocking.

---

# 11. Waivers

`GATE_WAIVED` no significa:

```text id="x7r0p5"
GATE_SATISFIED
```

Una waiver debe tener:

```text id="s8z4q1"
WAIVER_ID
AUTHORITY
SCOPE
RATIONALE
COMPENSATING_CONTROLS
EXPIRY
POLICY_REFERENCE
```

La waiver no altera retrospectivamente el resultado técnico del gate.

---

# 12. Release verdicts

Estados:

```text id="2n8x4r"
RELEASE_ELIGIBLE
RELEASE_ELIGIBLE_WITH_RISKS
RELEASE_BLOCKED
RELEASE_NOT_DEMONSTRATED
RELEASE_EXCEPTIONALLY_ELIGIBLE
```

Una excepción requiere política explícita y autorización correspondiente.

La waiver no debe convertirse automáticamente en un verdict global separado.

---

# 13. Blocking logic

Si un gate blocking está:

```text id="3m7k8q"
GATE_NOT_SATISFIED
GATE_BLOCKED
GATE_UNKNOWN
```

el release correspondiente queda bloqueado o no demostrado según la política.

Nunca:

```text id="v0h3ks"
UNKNOWN → PASS
```

---

# 14. Gate dependency graph

Los gates deben modelarse como DAG:

```text id="j3m6h1"
GATE A
   ↓
GATE B
   ↓
GATE C
```

No introducir dependencias cíclicas necesarias para adjudicar un release.

Las reevaluaciones posteriores pueden formar ciclos históricos de revisión, pero no una dependencia circular necesaria para el primer verdict.

---

# 15. Cross-skill dependency

Ejemplo:

```text id="s3f4yv"
ISOLATION_VERDICT
        ↓
TEST_ADMISSIBILITY
        ↓
GATE_EVALUATION
```

La existencia de un objeto no demuestra que sea aplicable.

Cada consumer valida:

```text id="x2f7a6"
IDENTITY
PRODUCER
SCOPE
TEMPORALITY
POLICY
STATUS
PROVENANCE
```

---

# 16. Consumer evaluation

Release debe evaluar explícitamente:

> ¿Este input satisface la precondición de este gate para este release?

No:

> ¿Este input es verdadero?

Registrar, cuando corresponda:

```text id="h8k1v6"
CONSUMER_EVALUATION
```

separado del objeto consumido.

---

# 17. Evidence integrity

Un gate puede requerir:

```text id="q4t7p2"
EVIDENCE_INTEGRITY_CHECKED
```

pero:

```text id="k3s9d5"
EVIDENCE_INTEGRITY_CHECKED
≠
GATE_SATISFIED
```

Debe además comprobar:

- scope;
- temporalidad;
- provenance;
- applicability;
- required evidence coverage.

---

# 18. Test result

Release puede consumir:

```text id="m7c4x1"
TEST_PASS
```

pero debe comprobar:

```text id="4g9p2w"
TEST_HEALTH
TEST_ADMISSIBILITY
SCOPE
ENVIRONMENT
PROPERTY
LIMITATIONS
ISOLATION DEPENDENCIES
```

Un test `PASS` no es automáticamente gate evidence.

---

# 19. Isolation

Un:

```text id="0m2h7n"
ISOLATION_BREACHED
```

crítico no puede ser cancelado por:

```text id="q5r8x3"
TEST_PASS
```

No existe composición ad-hoc de autoridad.

La política determina cómo los inputs afectan al gate.

---

# 20. Audit

Release puede consumir:

```text id="1p7z3w"
AUDIT_FINDING
AUDIT_UNKNOWN
AUDIT_CONTRADICTED
```

No debe reinterpretarlos para crear un nuevo authority type.

Si necesita un nuevo verdict, debe existir una regla de gate/composición autorizada.

---

# 21. Pedagogy

Release puede exigir gates pedagógicos.

Consume:

```text id="n6k4s0"
PEDAGOGICAL_CONFORMITY_STATUS
PEDAGOGICAL_IMPACT_RECORD
```

No puede declarar por sí mismo:

```text id="z9h1q2"
PEDAGOGICALLY_CORRECT
```

si esa autoridad pertenece a `talos-pedagogy`.

Puede únicamente evaluar si el resultado de esa skill satisface el gate de release.

---

# 22. Release Evidence Packet

El paquete debe contener, según criticidad:

```text id="j4n7b8"
RELEASE_ID
SCOPE
REPOSITORY_STATE
ENVIRONMENT_PROFILE
GATE_EVALUATIONS
RESIDUAL_RISKS
UNKNOWNS
CONTRADICTIONS
WAIVERS
AUTHORIZATION_REFS
VERDICT
```

Debe ser reconstruible.

---

# 23. Residual risk

Los riesgos deben clasificarse según la política:

```text id="t4v8c1"
ACCEPTABLE
CONDITIONALLY_ACCEPTABLE
BLOCKING
UNKNOWN
```

Un riesgo no convierte un gate fallido en satisfecho.

---

# 24. Unknowns

Un unknown debe conservar:

```text id="w5q9e3"
UNKNOWN_ID
QUESTION
CRITICALITY
AFFECTED_SCOPE
BLOCKING
REQUIRED_EVIDENCE
FOLLOW_UP
CREATED_AT
```

---

# 25. Temporal unknowns

Un unknown tiene dimensión temporal.

Registrar:

```text id="e8x3m4"
AGE
AFFECTED_COMMITS
POLICY_VERSIONS
LAST_REVIEW
REVIEW_DEADLINE
TEMPORAL_STATUS
```

Estados de gestión:

```text id="a2c6n8"
CURRENT
STALE
```

`STALE_UNKNOWN` es un descriptor temporal.

No significa:

```text id="y7r4q0"
RESOLVED
RISK_ACCEPTED
PASS
```

---

# 26. Unknown lineage

Un unknown no puede desaparecer por omisión.

Debe evolucionar explícitamente hacia:

```text id="n1b5v7"
RESOLVED
SUPERSEDED
REMAINS_UNKNOWN
```

con evidencia o explicación correspondiente.

---

# 27. Contradictions

Si inputs relevantes son incompatibles:

```text id="k8s2d1"
CONTRADICTION_RECORD
```

debe ser considerado antes del verdict.

No elegir silenciosamente el resultado conveniente.

Una contradicción crítica puede bloquear el gate según política.

Conforme a F-14, release consume el `CONTRADICTION_RECORD` cross-skill, pero no posee su adjudicación; esa propiedad corresponde a `talos-audit`.

## F-17 — Bounded meta-verification

```text
GATE_EVALUATION
→ may be meta-verified
→ terminal audit/human review
→ bounded recursion
```

La revisión terminal no crea autoridad transversal nueva.

---

# 28. Composition and authority

Release no obtiene autoridad adicional simplemente acumulando objetos válidos.

Regla:

> **Only a policy-defined composition rule can produce a new authority.**

Debe existir:

```text id="g7w4m2"
COMPOSITION_RULE
```

con:

```text id="z3c8p6"
INPUTS_REQUIRED
PRODUCER_REQUIRED_PER_INPUT
SCOPE_COMPATIBILITY_REQUIRED
TEMPORAL_COMPATIBILITY_REQUIRED
OUTPUT_AUTHORITY
AUTHORIZED_COMPOSER
POLICY_REFERENCE
```

Y:

```text id="n5m1v8"
OUTPUT_AUTHORITY
    ∈
AUTHORIZED_COMPOSER.MAY_PRODUCE
```

---

# 29. Anti-pass-through

Release debe ejercer su propia jurisdicción.

Incorrecto:

```text id="q8c3v6"
testing:
    TEST_PASS

release:
    RELEASE_ELIGIBLE
```

sin evaluar:

```text id="c5x7m2"
applicable gates
evidence
scope
dependencies
unknowns
contradictions
authorization
```

El problema no es consumir evidencia externa.

El problema es **copiar la conclusión de otro productor como si fuera una conclusión propia**.

---

# 30. No-transfer of authority

Un release input no transfiere su autoridad al release skill.

Ejemplo:

```text id="x1q6m9"
TEST_PASS
```

conserva autoridad de testing.

Release puede utilizarlo como input de adjudicación, pero no puede convertirlo en un `TEST_PASS` producido por release ni extender su alcance arbitrariamente.

---

# 31. Release state identity

Cada verdict debe estar vinculado a:

```text id="p4n8r2"
RELEASE_STATE_ID
COMMIT/TREE
POLICY_IDENTITY
ENVIRONMENT_PROFILE
EVIDENCE_SET
GATE_GRAPH
```

Un nuevo estado material requiere delta analysis o reevaluación apropiada.

---

# 32. Incremental release

No heredar ciegamente todos los verdicts anteriores.

Analizar:

```text id="b7k2m5"
WHAT CHANGED
AFFECTED COMPONENTS
AFFECTED BOUNDARIES
AFFECTED GATES
EVIDENCE STILL APPLICABLE
NEW UNKNOWN
NEW CONTRADICTIONS
```

Revalidar lo afectado.

---

# 33. Hotfix / emergency profile

Un perfil de emergencia puede reducir evidencia únicamente si una política previamente definida lo permite.

Debe utilizar:

```text id="u5j9c4"
PREDEFINED REDUCED PROFILE
COMPENSATING CONTROLS
EXPLICIT AUTHORIZATION
DOCUMENTED LIMITATIONS
```

Nunca:

```text id="q2w8e6"
UNKNOWN → PASS
```

---

# 34. Authorization

Release puede verificar autorizaciones.

No puede concederlas.

Un requisito de autorización debe identificar:

```text id="d6r3x8"
AUTHORIZATION_ID
AUTHORITY
SCOPE
ACTION
RESOURCE
CONDITIONS
EXPIRY
```

---

# 35. Post-release observation

La observación posterior al release es una fase posterior:

```text id="r7m2x9"
DEPLOYMENT
    ↓
POST_RELEASE_OBSERVATION
```

No debe utilizarse retroactivamente para afirmar que el release original era correcto.

Si aparece nueva evidencia:

```text id="x3k6p1"
RE-EVALUATE
```

La evidencia posterior puede motivar rollback o reevaluación.

---

# 36. Pedagogical release boundary

Si un release modifica:

- hinting;
- StudentState;
- BKT;
- assessment;
- curriculum;
- exercise behavior;

debe existir la evaluación correspondiente de `talos-pedagogy`.

Release no puede saltarse esa jurisdicción.

---

# 37. Security boundary

Release debe comprobar que los gates de seguridad requeridos fueron satisfechos.

No convierte:

```text id="m5v8q2"
security scan passed
```

en:

```text id="x9c3k7"
system universally secure
```

---

# 38. Context routing

Para release:

```text id="f3j8n5"
CORE
    AGENTS.md

ACTIVE
    talos-release

SUPPORTING
    talos-audit
    talos-isolation
    talos-testing
    talos-evidence
    talos-pedagogy

DORMANT
    none when gate graph spans all domains
```

Si el release scope es limitado, reducir contexto solo después de clasificar las fronteras afectadas.

Boundary desconocida:

> ampliar contexto.

---

# 39. Completion criteria

Una adjudicación de release está completa cuando:

```text id="v6k1q8"
[ ] RELEASE_ID
[ ] RELEASE_SCOPE
[ ] REPOSITORY_STATE
[ ] POLICY_IDENTITY
[ ] ENVIRONMENT
[ ] APPLICABLE_GATES
[ ] GATE_GRAPH
[ ] GATE_EVALUATIONS
[ ] REQUIRED_EVIDENCE
[ ] EVIDENCE_APPLICABILITY
[ ] ISOLATION_DEPENDENCIES
[ ] TEST_HEALTH
[ ] TEST_ADMISSIBILITY
[ ] PEDAGOGICAL_REQUIREMENTS
[ ] AUTHORIZATIONS
[ ] UNKNOWNS
[ ] CONTRADICTIONS
[ ] RESIDUAL_RISKS
[ ] WAIVERS
[ ] FINAL_VERDICT
[ ] LIMITATIONS
```

---

# 40. Regla final

> **Release no crea evidencia ni aumenta su fuerza epistemológica.**

Su función es:

```text id="c4m7x2"
IDENTIFY SCOPE
    ↓
ENUMERATE GATES
    ↓
VALIDATE INPUTS
    ↓
CHECK APPLICABILITY
    ↓
EVALUATE GATES
    ↓
HANDLE UNKNOWN / CONTRADICTION
    ↓
ASSESS RISKS
    ↓
VERIFY AUTHORIZATION
    ↓
COMPOSE POLICY-AUTHORIZED VERDICT
```

Por tanto:

> **Un release es una adjudicación trazable de un estado concreto del sistema, no una colección de checks verdes.**
