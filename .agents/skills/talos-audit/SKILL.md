# TALOS — `talos-audit`

**Versión:** 3.1  
**Jurisdicción:** Auditoría operacional y reconstrucción de comportamiento  
**Estado:** Conceptualmente congelado  
**Ubicación canónica:** `.agents/skills/talos-audit/SKILL.md`

---

## 1. Propósito

`talos-audit` es la jurisdicción de TALOS encargada de responder:

> **¿Qué hace realmente el sistema bajo las condiciones examinadas?**

Su función es reconstruir comportamiento efectivo, recorridos de ejecución, dependencias, efectos observables y discrepancias entre lo declarado y lo observado.

La skill produce **hallazgos de auditoría**, no autoridad sobre dominios pertenecientes a otras skills.

---

## 2. Principio rector

> **La auditoría describe y evalúa lo observado dentro de su scope; no convierte una observación en autoridad de otro dominio.**

Una auditoría puede demostrar que:

- una función llama a otra;
- un startup ejecuta determinado código;
- existe una escritura;
- una dependencia es alcanzable;
- un recurso es consultado;
- una condición no se cumple;
- documentación y runtime divergen.

No puede, por sí sola, convertir esas observaciones en:

- `ISOLATION_DEMONSTRATED`;
- `TEST_PASS`;
- `EVIDENCE_TRUE`;
- `PEDAGOGICAL_CONFORMITY`;
- `RELEASE_ELIGIBLE`;
- `MASTERY`.

---

# 3. SKILL_INTERFACE

## 3.1. Produce

`talos-audit` puede producir:

```text
AUDIT_OBSERVATION
AUDIT_FINDING
CLAIM
EXECUTION_PATH
SIDE_EFFECT_RECORD
CONTRADICTION_RECORD
UNKNOWN_RECORD
FOLLOW_UP
ASSUMPTION_RECORD
```

Puede además producir referencias a evidencia mediante la interfaz de `talos-evidence`, pero no asume la jurisdicción de preservación o integridad de evidencia.

---

## 3.2. Consume

Puede consumir, cuando corresponda:

```text
ENVIRONMENT_PROFILE
OBSERVATION_RECORD
EVIDENCE_REF
TEST_EXECUTION_RESULT
TEST_HEALTH
TEST_ADMISSIBILITY
ISOLATION_VERDICT
ISOLATION_CONTRACT
PEDAGOGICAL_IMPACT_RECORD
POLICY_IDENTITY
AUTHORIZATION_RECORD
CONTRADICTION_RECORD
UNKNOWN_RECORD
```

Todo objeto externo debe ser revalidado en el punto de consumo.

---

## 3.3. Puede decidir

Dentro de su jurisdicción:

- si una afirmación está respaldada por las observaciones auditadas;
- si existe una discrepancia observable;
- si una ruta de ejecución está reconstruida;
- si un efecto lateral fue observado;
- si una afirmación permanece `UNKNOWN`;
- si una cuestión requiere `FOLLOW_UP`;
- si existe una contradicción de auditoría.

---

## 3.4. No puede decidir

No puede producir autoridad sobre:

```text
ISOLATION_*
TEST_*
EVIDENCE_TRUTH
PEDAGOGICAL_CONFORMITY
MASTERY
BKT
RELEASE_*
```

En particular:

> `AUDIT_FINDING` no equivale a `ISOLATION_VERDICT`.

---

# 4. Postura por defecto

La postura predeterminada de una auditoría es:

```text
READ-ONLY
STATIC
MINIMUM-SUFFICIENT-CONTEXT
NO-PRODUCTION-SIDE-EFFECTS
FAIL-CLOSED
```

No asumir que una auditoría puede ejecutar runtime simplemente porque la tarea diga “auditar”.

Una operación dinámica requiere un plan explícito y límites conocidos.

---

# 5. Pre-flight

Antes de comenzar:

```text
[ ] QUESTION definida
[ ] ACCEPTANCE CRITERION definido
[ ] SCOPE definido
[ ] BOUNDARY definida
[ ] AUTHORIZATION revisada
[ ] RESOURCES protegidos identificados
[ ] LIFECYCLE relevante identificado
[ ] POLICY_IDENTITY conocida
[ ] PEDAGOGICAL_IMPACT evaluado si corresponde
[ ] BLAST_RADIUS estimado
```

Si una incertidumbre crítica impide saber si la operación es segura:

> **STOP.**

No inferir seguridad por intención.

---

# 6. Audit Contract

Toda auditoría no trivial debe establecer:

```text
AUDIT CONTRACT

QUESTION
ACCEPTANCE CRITERION
SCOPE
BOUNDARY
METHOD
EVIDENCE REQUIRED
STOP CONDITION
```

Durante la ejecución registrar:

```text
OBSERVATIONS
EVIDENCE
COUNTER-CHECK
INTERPRETATION
CONCLUSION
UNKNOWNS
```

---

# 7. Clasificación del modo de auditoría

## 7.1. Static audit

Inspección sin ejecutar el sistema.

Puede incluir:

- código;
- imports;
- configuración;
- dependency graph;
- tests;
- documentación;
- referencias;
- entrypoints.

Es el modo preferido cuando responde la pregunta.

---

## 7.2. Controlled runtime audit

Runtime únicamente cuando el comportamiento requerido no puede establecerse de forma suficiente mediante inspección estática.

Debe definir antes:

```text
EXECUTION PLAN
ENVIRONMENT_PROFILE
AUTHORIZED RESOURCES
FORBIDDEN RESOURCES
OBSERVATION MECHANISMS
STOP CONDITIONS
CLEANUP POLICY
```

La ejecución no debe convertirse automáticamente en una prueba de aislamiento.

---

## 7.3. Isolation-dependent audit

Si la auditoría depende de demostrar confinamiento:

```text
talos-audit
    consume
talos-isolation
```

No adjudicar aislamiento por inferencia propia.

---

## 7.4. Release audit

Puede aportar findings para `talos-release`.

No decide el release.

---

# 8. Reconstrucción de ejecución

Cuando sea necesario reconstruir un flujo:

```text
ENTRYPOINT
    ↓
IMPORTS
    ↓
CONSTRUCTION
    ↓
STARTUP
    ↓
DEPENDENCY RESOLUTION
    ↓
EXECUTION
    ↓
BACKGROUND TASKS
    ↓
PERSISTENCE
    ↓
SHUTDOWN
    ↓
CLEANUP
```

No limitarse a inspeccionar la función directamente mencionada por el usuario.

Identificar también:

- llamadas indirectas;
- factories;
- dependency injection;
- callbacks;
- background tasks;
- warmups;
- hooks;
- persistence;
- subprocesses;
- dynamic loading.

---

# 9. Side-effect ledger

Cuando una operación pueda producir efectos, registrar:

```text
RESOURCE
ACCESS_MODE
OPERATION
LIFECYCLE_PHASE
EXPECTED_EFFECT
OBSERVED_EFFECT
OBSERVATION_METHOD
STATUS
```

Ejemplos de recursos:

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
```

---

# 10. Estados de auditoría

Utilizar estados propios de auditoría:

```text
AUDIT_VERIFIED
AUDIT_INFERRED
AUDIT_UNKNOWN
AUDIT_CONTRADICTED
AUDIT_FAILED
AUDIT_RISK
AUDIT_FOLLOWUP
```

No utilizar estados pertenecientes a otras jurisdicciones para expresar conclusiones de auditoría.

Por ejemplo:

```text
AUDIT_VERIFIED
```

no debe convertirse en:

```text
ISOLATION_DEMONSTRATED
```

sin el correspondiente proceso de `talos-isolation`.

---

# 11. Evidencia

La auditoría debe distinguir:

```text
OBSERVATION
EVIDENCE
CLAIM
INTERPRETATION
CONCLUSION
```

Una observación puede respaldar un claim.

Un claim no convierte automáticamente la observación en verdad universal.

Cuando se necesite preservación, lineage o integridad formal:

```text
talos-audit
    →
talos-evidence
```

La auditoría consume y referencia evidencia; no redefine la semántica de integridad de evidencia.

---

# 12. Counter-check

Las afirmaciones importantes requieren una comprobación de contraevidencia apropiada.

Preguntas típicas:

- ¿Existe otra ruta que produzca el efecto?
- ¿El comportamiento observado es incidental?
- ¿El test usa un mock que elimina la dependencia relevante?
- ¿La configuración observada es realmente la que se ejecuta?
- ¿Existe una condición que cambie el comportamiento?
- ¿La observación cubre todo el lifecycle?
- ¿Existe evidencia contradictoria?

No buscar contraevidencia artificial cuando el scope no la requiere, pero sí cuando una afirmación crítica depende de ella.

---

# 13. Claims

Todo claim importante debe poder expresarse conceptualmente como:

```text
CLAIM
    ↓
EVIDENCE
    ↓
METHOD
    ↓
COUNTER-CHECK
    ↓
STATUS
    ↓
CONFIDENCE
```

Ejemplo:

```text
Claim:
create_app() intenta crear determinado directorio.

Evidence:
inspección del código + runtime controlado.

Method:
static reconstruction + controlled observation.

Counter-check:
ruta alternativa / condición de ejecución.

Status:
AUDIT_VERIFIED.
```

---

# 14. Contradicciones

`talos-audit` es propietario de la adjudicación de contradicciones cross-skill. Las contradicciones intra-skill permanecen bajo la propiedad de la skill correspondiente.

Cuando dos observaciones relevantes sean incompatibles:

```text
A → X
B → NOT-X
```

crear:

```text
CONTRADICTION_RECORD
```

No resolver la contradicción seleccionando arbitrariamente la observación más conveniente.

Registrar:

```text
CONTRADICTION_ID
OBSERVATION_A
OBSERVATION_B
AFFECTED_CLAIMS
SCOPE
TEMPORALITY
CRITICALITY
STATUS
```

Una contradicción crítica bloquea conclusiones dependientes hasta que sea resuelta o explícitamente clasificada por la política aplicable.

## F-17 — Bounded meta-verification

Una `GATE_EVALUATION` puede ser meta-verificada con revisión terminal de `talos-audit` o humana. La recursión de meta-verificación es acotada; esta revisión terminal no crea autoridad transversal nueva.

---

# 15. UNKNOWN

`UNKNOWN` es un resultado válido.

Ejemplos:

```text
no se pudo observar el proceso
no se pudo reconstruir una ruta completa
la dependencia dinámica no pudo determinarse
la instrumentación fue insuficiente
la documentación contradice el runtime
```

No rellenar:

```text
UNKNOWN
```

con:

```text
“probablemente”
“seguramente”
“por diseño”
“debería”
```

---

# 16. Isolation boundary

Cuando la auditoría encuentre una cuestión de aislamiento:

```text
¿qué ocurrió?
```

es responsabilidad de audit.

La pregunta:

```text
¿estaba realmente aislado?
```

pertenece a `talos-isolation`.

Audit puede producir:

```text
OBSERVED_ESCAPE_ATTEMPT
UNEXPECTED_SIDE_EFFECT
OBSERVED_RESOURCE_ACCESS
```

pero no adjudicar el verdict global de aislamiento.

---

# 17. Testing boundary

Audit puede consumir:

```text
TEST_EXECUTION_RESULT
TEST_HEALTH
TEST_ADMISSIBILITY
```

y evaluar qué evidencia aporta el test a una afirmación de auditoría.

No puede reinterpretar:

```text
TEST_FAIL → PASS
TEST_BLOCKED → PASS
TEST_UNKNOWN → PASS
```

ni cambiar la semántica del resultado.

Un test green demuestra solamente lo que su contrato permite demostrar.

---

# 18. Evidence boundary

`talos-evidence` posee la semántica de:

- identificación;
- preservación;
- lineage;
- integridad;
- provenance.

Audit puede:

- solicitar evidencia;
- relacionarla con claims;
- observar su suficiencia para una pregunta de auditoría.

No puede declarar:

```text
EVIDENCE_TRUE
EVIDENCE_TRUSTED
```

porque esos estados no pertenecen a la capa de evidencia.

---

# 19. Pedagogical boundary

Si la auditoría toca:

- StudentState;
- BKT;
- mastery;
- hinting;
- exercise flow;
- pedagogical policy;
- curriculum;

debe activar o consultar `talos-pedagogy`.

Audit puede identificar:

```text
PEDAGOGICAL_IMPACT_OBSERVED
PEDAGOGICAL_RISK
POLICY_DEVIATION
```

No adjudicar por sí mismo la conformidad pedagógica.

---

# 20. Release boundary

Audit puede producir:

```text
AUDIT_FINDING
AUDIT_VERIFIED
AUDIT_UNKNOWN
AUDIT_RISK
```

para consumo de release.

No puede producir:

```text
GATE_SATISFIED
RELEASE_ELIGIBLE
RELEASE_BLOCKED
```

salvo que esos estados sean producidos por la jurisdicción de release.

---

# 21. Cross-Skill Object Validation

Cada objeto recibido debe validarse en el punto de consumo:

```text
IDENTITY
PRODUCER
PROVENANCE
SCOPE
TEMPORALITY
POLICY
STATUS
RUN_ID
```

Una validación realizada por el productor no sustituye la validación del consumidor.

---

# 22. Consumer Evaluation

Cuando `talos-audit` consuma un objeto crítico de otra skill, debe registrar su propia evaluación cuando la política o el contrato lo requieran.

La evaluación responde:

> ¿Este objeto satisface mi precondición para esta auditoría?

No:

> ¿Este objeto es verdadero?

---

# 23. Composition

Audit no puede crear una nueva autoridad mediante composición ad-hoc.

Si una composición produce una autoridad nueva:

```text
COMPOSITION_RULE
```

debe existir y:

```text
OUTPUT_AUTHORITY
    ∈
AUTHORIZED_COMPOSER.MAY_PRODUCE
```

Audit no puede utilizar una colección de findings para fabricar una autoridad perteneciente a isolation, testing, pedagogy o release.

---

# 24. Anti-pass-through

Audit no debe producir:

```text
AUDIT_VERIFIED
```

simplemente porque otra skill declaró un resultado.

Debe ejercer su propia función:

```text
inspect
→ correlate
→ evaluate
→ counter-check
→ classify
```

Puede depender completamente de evidencia externa.

La prohibición es el **pass-through de autoridad**, no el consumo de evidencia externa.

---

# 25. Context economy

No cargar:

- todo el repositorio;
- todas las skills;
- todos los logs;
- todo el corpus;

si la pregunta puede responderse con un contexto menor.

Orden recomendado:

```text
QUESTION
    ↓
SCOPE
    ↓
LIKELY ENTRYPOINT
    ↓
DIRECT DEPENDENCIES
    ↓
RELEVANT ARTIFACTS
    ↓
COUNTER-EVIDENCE
```

Expandir solo cuando la evidencia lo requiera.

---

# 26. Runtime safety

Antes de runtime:

```text
[ ] operation defined
[ ] lifecycle defined
[ ] protected resources classified
[ ] isolation boundary known
[ ] authorized resources known
[ ] observation mechanism available
[ ] stop condition defined
```

Si alguna condición crítica es desconocida:

> **STOP.**

---

# 27. B0 / B0.5 / B1

## B0

Objetivo:

> reconstrucción operacional estática.

No arrancar TALOS ni tocar recursos de producción salvo autorización específica.

---

## B0.5

Objetivo:

> comprobar construcción/startup sintético y ausencia de efectos sobre recursos protegidos.

Audit puede reconstruir:

- imports;
- construction;
- startup;
- dependency resolution;
- side effects.

La adjudicación formal de aislamiento corresponde a `talos-isolation`.

---

## B1

La auditoría debe respetar:

```text
synthetic environment
+
controlled dependencies
+
explicit isolation verdict
+
test evidence
```

No considerar un `TEST_PASS` suficiente por sí solo.

---

# 28. Three-strike circuit breaker

Si tres intentos de investigación/corrección no producen progreso significativo:

```text
STOP
PRESERVE
RECLASSIFY
REVIEW ASSUMPTIONS
```

No continuar acumulando cambios sin aumentar la evidencia.

---

# 29. Completion criteria

Una auditoría se considera completa cuando:

```text
[ ] QUESTION respondida dentro del scope
[ ] ACCEPTANCE CRITERION evaluado
[ ] METHOD documentado
[ ] EXECUTION PATH reconstruido cuando corresponda
[ ] SIDE EFFECTS clasificados
[ ] EVIDENCE identificada
[ ] COUNTER-CHECK realizado cuando corresponde
[ ] CONTRADICTIONS visibles
[ ] UNKNOWNS visibles
[ ] LIMITATIONS documentadas
[ ] JURISDICTION boundaries respetadas
[ ] ningún resultado de otra skill fue reinterpretado
[ ] conclusión proporcional a la evidencia
```

---

# 30. Regla final

> **`talos-audit` debe decir qué se observó, qué puede sostenerse a partir de ello y qué permanece desconocido.**

No debe convertir su interpretación en autoridad ajena.

**Auditar no es certificar.**
**Observar no es probar universalmente.**
**Describir comportamiento no es adjudicar aislamiento.**
**Encontrar un problema no autoriza a corregirlo automáticamente.**
