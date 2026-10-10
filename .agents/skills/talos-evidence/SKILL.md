# TALOS — `talos-evidence`

**Versión:** 3.1  
**Jurisdicción:** Identificación, preservación, provenance, lineage e integridad de evidencia  
**Estado:** Conceptualmente congelado  
**Ubicación canónica:** `.agents/skills/talos-evidence/SKILL.md`

---

# 1. Propósito

`talos-evidence` es la jurisdicción de TALOS encargada de responder:

> **¿Qué evidencia existe, de dónde proviene, cómo se preservó, cómo puede identificarse y con qué alcance puede relacionarse?**

La skill protege la trazabilidad de la evidencia sin convertirla en una conclusión automática.

---

# 2. Principio rector

> **La evidencia puede respaldar un claim; la evidencia no se convierte por sí sola en el claim.**

> Evidence provenance no constituye autoridad epistemológica.

Separar siempre:

```text
OBSERVATION
≠
EVIDENCE
≠
CLAIM
≠
ASSESSMENT
≠
VERDICT
```

Y también:

```text
EVIDENCE_INTEGRITY
≠
TRUTH
≠
AUTHENTICITY
≠
CORRECTNESS
```

---

# 3. SKILL_INTERFACE

## 3.1. Produce

```text
EVIDENCE_REF
EVIDENCE_RECORD
PROVENANCE_RECORD
EVIDENCE_LINEAGE
PRESERVATION_RECORD
EVIDENCE_INTEGRITY_STATUS
TRANSFORMATION_RECORD
OBSERVABILITY_RECORD
RUBRIC_IDENTITY
```

---

## 3.2. Consume

Puede consumir:

```text
OBSERVATION_RECORD
TEST_EXECUTION_RESULT
RUNTIME_TRACE
LOG
COMMAND_OUTPUT
CONFIGURATION_SNAPSHOT
ENVIRONMENT_SNAPSHOT
SOURCE_CODE
DIFF
FIXTURE
DATABASE_RECORD
FILE_RECORD
NETWORK_OBSERVATION
PROCESS_OBSERVATION
METRIC
REPORT
HUMAN_JUDGMENT
DERIVED_RECORD
```

---

## 3.3. No produce

No produce:

```text
TRUTH
CLAIM_VALIDITY
TEST_EXECUTION_RESULT
ISOLATION_VERDICT
PEDAGOGICAL_CONFORMITY
RELEASE_VERDICT
MASTERY
BKT
```

---

# 4. Evidence Record

Un registro de evidencia debe poder expresar, según corresponda:

```text
EVIDENCE_REF_ID
TYPE
SOURCE
PRODUCER
RUN_ID / EXECUTION_ID
TIMESTAMP
CONTENT / LOCATION
PROVENANCE
INTEGRITY
SCOPE
RELATED_CLAIMS
RELATED_OBSERVATIONS
LIMITATIONS
STATUS
```

No todos los campos necesitan tener el mismo nivel de detalle para cada criticidad.

---

# 5. Evidence types

Tipos posibles:

```text
ARTIFACT
OBSERVATION
TEST_EXECUTION_RESULT
RUNTIME_TRACE
LOG
COMMAND_OUTPUT
CONFIGURATION_SNAPSHOT
ENVIRONMENT_SNAPSHOT
SOURCE_CODE
DIFF
FIXTURE
DATABASE_RECORD
FILE_RECORD
NETWORK_OBSERVATION
PROCESS_OBSERVATION
METRIC
REPORT
HUMAN_JUDGMENT
DERIVED_RECORD
```

La clasificación describe el tipo de evidencia, no su valor epistemológico.

---

# 6. Evidence lifecycle

El flujo conceptual es:

```text
CLAIM / QUESTION
        ↓
EVIDENCE REQUIRED
        ↓
OBSERVATION / ARTIFACT
        ↓
IDENTIFICATION
        ↓
PROVENANCE
        ↓
PRESERVATION
        ↓
INTEGRITY
        ↓
RELATION
        ↓
LIMITATIONS
        ↓
EVIDENCE STATUS
```

---

# 7. Evidence status

Utilizar estados de procesamiento:

```text
EVIDENCE_DISCOVERED
EVIDENCE_CAPTURED
EVIDENCE_IDENTIFIED
EVIDENCE_PRESERVED
EVIDENCE_INTEGRITY_CHECKED
EVIDENCE_REFERENCED
EVIDENCE_DERIVED
EVIDENCE_REDACTED
EVIDENCE_INCOMPLETE
EVIDENCE_MISSING
EVIDENCE_CORRUPTED
EVIDENCE_CONTRADICTED
EVIDENCE_SUPERSEDED
```

No utilizar:

```text
EVIDENCE_TRUE
EVIDENCE_CONFIRMED
EVIDENCE_TRUSTED
```

como estados normativos de esta skill.

---

# 8. Identification

Cada evidencia relevante debe tener identidad estable:

```text
EVIDENCE_REF_ID
```

Cuando corresponda incluir:

```text
content hash
artifact identity
run identity
source identity
version
location
timestamp
```

Un hash identifica/integrity-checks un contenido bajo el algoritmo utilizado.

No demuestra que el contenido sea verdadero.

---

# 9. Provenance

Registrar, cuando sea posible:

```text
PRODUCER
SOURCE
RUN_ID
EXECUTION_ID
ACTOR
TIMESTAMP
ENVIRONMENT
POLICY
TRANSFORMATION
PARENT_EVIDENCE
```

La provenance responde:

> ¿De dónde salió esto?

No:

> ¿Es verdadero?

---

# 10. Source independence

La evidencia puede clasificarse por relación con su fuente:

```text
SELF_REPORTED
INDEPENDENT
EXTERNAL
```

Esto describe independencia del observador/productor.

No constituye automáticamente un score de confianza.

Una política de release puede requerir evidencia independiente para un gate crítico.

`talos-evidence` no inventa ese requisito.

---

# 11. Integrity

La integridad puede comprobar:

```text
content identity
hash consistency
artifact continuity
preservation state
```

No puede demostrar:

```text
truth
correctness
authenticity
policy compliance
```

Regla:

> **Integrity ≠ truth.**

---

# 12. Preservation

La preservación debe permitir reconstruir la evidencia histórica dentro de sus límites.

Cuando corresponda registrar:

```text
CAPTURE_TIME
STORAGE_LOCATION
CONTENT_IDENTITY
HASH
RETENTION
ACCESS_CONTROL
REDACTION
PRESERVATION_STATUS
```

No alterar evidencia original sin registrar transformación.

---

# 13. Pre-teardown capture

Cuando un framework o runtime destruya información efímera:

```text
capture before teardown
```

cuando esa información sea necesaria para el claim.

Ejemplos:

```text
temporary filesystem state
process tree
runtime environment
in-memory state
network observations
locks
temporary files
```

Si no fue capturada:

```text
EVIDENCE_MISSING
```

puede ser apropiado.

No invalidar automáticamente toda evidencia histórica relacionada.

---

# 14. Non-reproducibility

La imposibilidad de reproducir una observación no implica automáticamente que la evidencia histórica sea inválida.

Puede existir:

```text
historically preserved evidence
+
NON_REPRODUCIBLE CURRENTLY
```

La reproducibilidad y la preservación son propiedades diferentes.

---

# 15. Transformation lineage

La evidencia derivada debe conservar lineage:

```text
PARENT_EVIDENCE
TRANSFORMATION_ID
TRANSFORMATION_VERSION
TRANSFORMATION_HASH
PARAMETERS
OUTPUT_ID
LOSSINESS
```

Ejemplo:

```text
raw trace
    ↓
parser v2
    ↓
structured observation
```

La salida debe poder relacionarse con el input.

---

# 16. Lossy transformations

Si una transformación elimina información:

```text
LOSSY = TRUE
```

debe registrarse qué limitaciones introduce.

Ejemplo:

```text
full log
→ summary
```

El summary no debe tratarse como equivalente al log original para claims que dependan de información eliminada.

---

# 17. Parser changes

Cambiar un parser no implica automáticamente que la evidencia histórica deje de existir.

Puede requerirse:

```text
new derivation
new transformation identity
re-evaluation
```

La evidencia original permanece históricamente identificable si fue preservada.

---

# 18. Observability guarantee

Para claims de ausencia:

```text
“No ocurrió X”
```

la evidencia debe incluir información suficiente sobre la observabilidad.

Registrar:

```text
OBSERVABILITY_STATUS
OBSERVATION_MECHANISM
COVERAGE
BLIND_SPOTS
OBSERVATION_WINDOW
```

Estados:

```text
OBSERVABILITY_PROVEN
OBSERVABILITY_PARTIAL
OBSERVABILITY_UNKNOWN
OBSERVABILITY_FAILED
```

Una observación negativa significa:

> no se observó X mediante el mecanismo disponible.

No:

> X era imposible.

La adjudicación formal de aislamiento pertenece a `talos-isolation`.

---

# 19. Configuration and environment evidence

Las snapshots de:

```text
configuration
environment
dependency versions
filesystem policy
database policy
network policy
secret policy
```

son evidencia de contexto y deben poder relacionarse con el run correspondiente.

Un hash confirma identidad del contenido capturado.

No sustituye la representación segura del contenido cuando la pregunta requiere conocerlo.

---

# 20. Secrets

Nunca preservar secretos innecesariamente.

Utilizar:

```text
REDACTION
MINIMIZATION
SAFE REPRESENTATION
```

Cuando sea necesario demostrar ausencia de un secreto, una representación segura debe demostrar la propiedad requerida sin revelar el secreto.

Un hash por sí solo puede demostrar identidad de un valor conocido, pero no necesariamente:

> “no había un secreto”.

---

# 21. Human judgment

Los juicios humanos deben tener identidad propia.

Registrar cuando corresponda:

```text
ACTOR
TIMESTAMP
RUBRIC_ID
RUBRIC_VERSION
RUBRIC_HASH
INPUT_SCOPE
DECISION
JUSTIFICATION
PROVENANCE
ADJUDICATION_CONTEXT
```

---

# 22. Rubric identity

Un juicio debe quedar asociado a la rúbrica con la que fue realizado.

Un cambio posterior de rúbrica no modifica retroactivamente el juicio histórico.

Puede requerir:

```text
new adjudication
new rubric identity
new evidence relationship
```

---

# 23. Evidence budget

La profundidad de evidencia debe ser proporcional a la criticidad.

## LOW

```text
result
test ID
commit
```

## MEDIUM

```text
result
assertions
side effects
environment summary
```

## HIGH / GATE

```text
primary evidence
configuration
environment
instrumentation
independent observation when relevant
fixture/input IDs
hashes
limitations
```

## ADVERSARIAL

Además:

```text
exact input
pre-state
post-state
escape observations
recovery observations
```

La política específica puede exigir más.

---

# 24. Evidence and release

`talos-release` puede requerir evidencia determinada.

`talos-evidence` garantiza que la evidencia:

- tenga identidad;
- tenga provenance;
- tenga lineage cuando corresponda;
- tenga integridad verificable;
- exponga limitaciones.

Pero:

```text
EVIDENCE_INTEGRITY_CHECKED
```

no equivale a:

```text
GATE_SATISFIED
```

---

# 25. Evidence and testing

Testing produce resultados de ejecución.

Evidence preserva y referencia esos resultados.

Por tanto:

```text
TEST_EXECUTION_RESULT
    →
EVIDENCE_RECORD
```

no significa:

```text
EVIDENCE_RECORD
    →
TEST_EXECUTION_RESULT
```

Evidence no puede fabricar un resultado de test.

---

# 26. Evidence and isolation

Isolation puede consumir evidencia para demostrar una frontera.

Evidence no produce:

```text
ISOLATION_VERDICT
```

Ejemplo válido:

```text
filesystem trace
+
DB observation
+
environment snapshot
    ↓
evidence package
    ↓
talos-isolation evaluates boundary
```

---

# 27. Evidence and audit

Audit puede relacionar:

```text
AUDIT_OBSERVATION
```

con:

```text
EVIDENCE_REF
```

Evidence conserva la trazabilidad.

No convierte:

```text
AUDIT_FINDING
```

en verdad universal.

---

# 28. Evidence and pedagogy

Los datos de ingeniería pueden ser evidencia de comportamiento del sistema.

No deben convertirse automáticamente en:

```text
REAL_STUDENT_PERFORMANCE
```

Distinguish:

```text
DATA_ORIGIN
├── REAL_STUDENT
├── SYNTHETIC_STUDENT
└── AGENT_SIMULATED_STUDENT

PROVENANCE
├── HUMAN_AUTHORED
├── SYSTEM_GENERATED
└── AGENT_GENERATED

USAGE_ROLE
├── TEST_FIXTURE
├── SIMULATION_INPUT
└── PRODUCTION_DATA
```

La protección pedagógica pertenece a `talos-pedagogy`.

---

# 29. Synthetic evidence

Marcar explícitamente:

```text
SYNTHETIC
AGENT_GENERATED
TEST_FIXTURE
```

cuando corresponda.

Estas etiquetas deben permanecer identificables durante todo el lineage; ninguna transformación puede eliminar provenance crítica.

No permitir conversión implícita:

```text
SYNTHETIC_EVIDENCE
        →
PRODUCTION_EVIDENCE
```

Una transición requiere una operación explícita, autorizada y auditable cuando la política la permita.

Si una transformación intenta producir `REAL_STUDENT_PERFORMANCE` o `PRODUCTION_EVIDENCE` desde datos sintéticos o generados por agentes sin una operación autorizada:

```text
BLOCK
```

---

# 30. Agent-generated evidence

El agente puede producir artefactos o simulaciones.

Eso no convierte automáticamente esos artefactos en:

```text
REAL_WORLD_OBSERVATION
REAL_STUDENT_PERFORMANCE
PRODUCTION_EVIDENCE
```

La provenance debe conservar:

```text
AGENT_GENERATED
```

cuando corresponda.

---

# 31. Scope

Toda evidencia tiene alcance.

Registrar cuando sea relevante:

```text
SYSTEM
COMPONENT
RESOURCE
RUN
TIME
COMMIT/TREE
ENVIRONMENT
POLICY
```

No reutilizar evidencia fuera de su scope sin una evaluación de aplicabilidad.

---

# 32. Temporal validity

La evidencia histórica puede seguir siendo auténtica sin ser aplicable al estado actual.

Distinguir:

```text
HISTORICAL_VALIDITY
```

de:

```text
CURRENT_APPLICABILITY
```

Un cambio de:

- commit;
- environment;
- policy;
- fixture;
- dependency;

puede exigir reevaluación.

---

# 33. Superseded evidence

Cuando nueva evidencia sustituya a otra:

```text
EVIDENCE_SUPERSEDED
```

no significa que la evidencia histórica desaparezca.

Debe conservarse la relación:

```text
SUPERSEDES
SUPERSEDED_BY
REASON
TIME
```

---

# 34. Contradicted evidence

Si dos evidencias son incompatibles:

```text
EVIDENCE_CONTRADICTED
```

puede ser apropiado.

No resolver la contradicción simplemente descartando una evidencia sin registrar la decisión y su autoridad.

---

# 35. Missing evidence

Si una evidencia requerida no existe:

```text
EVIDENCE_MISSING
```

No fabricar un sustituto silencioso.

No convertir:

```text
missing evidence
```

en:

```text
negative evidence
```

---

# 36. Evidence package

Para gates críticos puede construirse un paquete:

```text
RELEASE / AUDIT / TEST / ISOLATION
        ↓
EVIDENCE PACKAGE
        ↓
IDENTITY
PROVENANCE
INTEGRITY
LINEAGE
SCOPE
LIMITATIONS
```

El paquete debe ser reconstruible.

---

# 37. Consumer validation

Cuando otra skill consume una `EVIDENCE_REF`, el consumidor debe validar:

```text
IDENTITY
PRODUCER
PROVENANCE
SCOPE
TEMPORALITY
POLICY
STATUS
```

La validez histórica del objeto no garantiza su aplicabilidad actual.

---

# 38. Consumer evaluation

Cuando corresponda, el consumidor produce:

```text
CONSUMER_EVALUATION
```

separado del objeto de evidencia.

Debe responder:

> ¿Esta evidencia satisface mi precondición actual?

No:

> ¿Esta evidencia es verdadera?

---

# 39. No-transfer of authority

Registrar evidencia no transfiere la autoridad del observador al consumidor.

Ejemplo:

```text
TEST_EXECUTION_RESULT
```

preservado por evidence no convierte evidence en testing.

De igual modo:

```text
ISOLATION_VERDICT
```

preservado por evidence no convierte evidence en isolation.

---

# 40. Composition

Evidence no puede componer ad-hoc:

```text
TEST_EXECUTION_RESULT
+
AUDIT_FINDING
+
INTEGRITY_CHECK
```

para fabricar:

```text
RELEASE_ELIGIBLE
```

Una nueva autoridad requiere una `COMPOSITION_RULE` autorizada por la política aplicable y ejecutada por el compositor autorizado.

---

# 41. Integrity vs epistemic strength

Nunca asumir:

```text
integrity checked
    →
stronger truth
```

La integridad responde:

> ¿El artefacto preservado coincide con la identidad esperada?

No responde:

> ¿La afirmación contenida en él es correcta?

---

# 42. Context routing

Para tareas de evidencia:

```text
CORE
    AGENTS.md

ACTIVE
    talos-evidence

SUPPORTING
    talos-testing
    talos-isolation
    talos-audit
    talos-pedagogy cuando corresponda
    talos-release cuando corresponda

DORMANT
    skills no afectadas
```

Boundary desconocida:

> ampliar contexto.

---

# 43. Completion criteria

Una evidencia crítica está suficientemente registrada cuando:

```text
[ ] EVIDENCE_REF_ID
[ ] TYPE
[ ] SOURCE
[ ] PRODUCER
[ ] RUN/EXECUTION ID
[ ] TIMESTAMP
[ ] CONTENT/LOCATION
[ ] PROVENANCE
[ ] INTEGRITY
[ ] SCOPE
[ ] RELATED CLAIMS/OBSERVATIONS
[ ] LIMITATIONS
[ ] STATUS
```

Para evidencia derivada:

```text
[ ] PARENT_EVIDENCE
[ ] TRANSFORMATION_ID
[ ] VERSION/HASH
[ ] PARAMETERS
[ ] LOSSINESS
```

Para ausencia:

```text
[ ] OBSERVABILITY_STATUS
[ ] OBSERVATION_MECHANISM
[ ] COVERAGE
[ ] BLIND_SPOTS
```

Para juicio humano:

```text
[ ] ACTOR
[ ] RUBRIC_ID
[ ] RUBRIC_VERSION
[ ] INPUT_SCOPE
[ ] DECISION
[ ] JUSTIFICATION
```

---

# 44. Regla final

> **La función de `talos-evidence` es hacer que la evidencia pueda ser identificada, preservada, trazada y limitada; no convertirla en autoridad epistemológica que no posee.**

En TALOS:

```text
EVIDENCE
    SUPPORTS
CLAIMS

pero

EVIDENCE
    DOES NOT AUTOMATICALLY BECOME
TRUTH
```
