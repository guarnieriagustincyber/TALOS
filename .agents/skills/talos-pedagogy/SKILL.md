# TALOS — `talos-pedagogy`

**Versión:** 3.1  
**Jurisdicción:** Protección de invariantes pedagógicos durante ingeniería y verificación  
**Estado:** Conceptualmente congelado  
**Ubicación canónica:** `.agents/skills/talos-pedagogy/SKILL.md`

---

# 1. Propósito

`talos-pedagogy` es la jurisdicción de TALOS encargada de:

> **Identificar, clasificar y proteger los invariantes pedagógicos durante el trabajo de ingeniería, evitando que la asistencia sobre TALOS sea confundida con autoridad pedagógica o con rendimiento real del estudiante.**

Principio fundamental:

> **The agent works ON TALOS, not AS TALOS.**

La skill protege la frontera entre:

```text id="h8ckn4"
ENGINEERING
SIMULATION
PEDAGOGICAL SESSION
REAL STUDENT PERFORMANCE
ASSESSMENT
MASTERY
```

---

# 2. Principio rector

La ingeniería puede modificar o verificar mecanismos pedagógicos.

No puede apropiarse de la autoridad que esos mecanismos ejercen sobre el estudiante.

Por tanto:

```text id="v2n8xk"
ENGINEERING EVIDENCE
≠
STUDENT PERFORMANCE

STUDENT PERFORMANCE
≠
ASSESSMENT

ASSESSMENT
≠
MASTERY

AGENT_GENERATED
≠
REAL_STUDENT_PERFORMANCE
```

---

# 3. SKILL_INTERFACE

## 3.1. Produce

```text id="z8e4pc"
PEDAGOGICAL_IMPACT_RECORD
PEDAGOGICAL_CONFORMITY_STATUS
POLICY_CONFORMANCE_CHECK
PEDAGOGICAL_GUARD_DECISION
POLICY_DEVIATION
PEDAGOGICAL_RISK
```

Puede también producir observaciones sobre implementación pedagógica, pero no reemplaza la política pedagógica normativa.

```text
POLICY_CONFORMANCE_CHECK
        ↓
PEDAGOGICAL_CONFORMITY_STATUS
```

`POLICY_CONFORMANCE_CHECK` es la evaluación; `PEDAGOGICAL_CONFORMITY_STATUS` es su resultado.

---

## 3.2. Consume

```text id="p7j3gs"
PEDAGOGICAL_POLICY_IDENTITY
TASK_CONTEXT
STUDENT_STATE_BOUNDARY
TEST_CONTRACT
ENVIRONMENT_PROFILE
EVIDENCE_REF
OBSERVATION_RECORD
AUTHORIZATION_RECORD
```

Todo objeto externo debe validarse en el punto de consumo.

---

## 3.3. Puede decidir

Dentro de su jurisdicción:

- si una tarea tiene impacto pedagógico;
- qué controles de ingeniería requiere ese impacto;
- si una implementación parece desviarse de una política declarada;
- si un artefacto puede confundirse con rendimiento real;
- si una operación debe bloquearse por incumplimiento de una frontera pedagógica;
- si una verificación requiere datos sintéticos;
- si una tarea es `POLICY_DEPENDENT`.

---

## 3.4. No puede decidir

No puede decidir:

```text id="w1m8yr"
MASTERY
BKT
STUDENT_ASSESSMENT
CURRICULUM_PROGRESS
PREREQUISITE_SATISFACTION
PEDAGOGICAL_ACTION
HINT_LEVEL
REAL_STUDENT_PERFORMANCE
RELEASE_VERDICT
TEST_EXECUTION_RESULT
ISOLATION_VERDICT
```

La skill protege la política; no se convierte en juez de la política.

---

# 4. Authority hierarchy

La autoridad pedagógica sigue:

```text id="s4b8te"
AGENTS.md
    ↓
TALOS DETERMINISTIC PEDAGOGICAL POLICY
    ↓
talos-pedagogy
```

`talos-pedagogy` interpreta y verifica la política aplicable.

No puede inventar una política alternativa.

---

# 5. Policy identity

Toda verificación dependiente de política debe poder identificar:

```text id="4w7lqv"
PEDAGOGICAL_POLICY_ID
VERSION
HASH
STATUS
VALIDITY
```

Una prueba realizada contra una versión concreta no debe presentarse como prueba contra otra versión sin reevaluación.

---

# 6. Policy states

Distinguir:

```text id="l5j6cy"
PRESENT
VERSIONED
INCOMPLETE
MISSING
CONTRADICTORY
UNKNOWN
```

Reglas:

```text id="7k7q2d"
PRESENT
→ follow

VERSIONED
→ pin version

INCOMPLETE
→ block only policy-dependent verification

MISSING
→ block policy-dependent implementation

CONTRADICTORY
→ STOP

UNKNOWN
→ do not infer
```

Una tarea independiente de la política puede continuar si está correctamente delimitada.

---

# 7. Pedagogical impact

Antes de actuar sobre una zona pedagógica debe clasificarse:

```text id="o6m3t7"
PEDAGOGICAL_IMPACT
```

Valores:

```text id="ik4v5j"
NONE
LOW
MEDIUM
HIGH
CRITICAL
UNKNOWN
```

Regla:

> `UNKNOWN ≠ LOW`.

Si el impacto real resulta mayor que el inicialmente clasificado:

```text id="b4o2zv"
STOP
RECLASSIFY
APPLY STRONGER CONTROLS
```

---

# 8. Impact dimensions

Evaluar, cuando corresponda:

```text id="l98t2d"
HINTING
STUDENT_STATE
BKT
ASSESSMENT
SOURCE_SCOPE
PREREQUISITES
CURRICULUM_PROGRESS
ACTION_AVAILABILITY
BYPASS_PATHS
PEDAGOGICAL_INVARIANTS
```

---

# 9. Pedagogical guard

El guard se ejecuta **antes de la acción**, no después.

Flujo:

```text id="1i8d3o"
TASK
 ↓
POLICY
 ↓
DATA ORIGIN
 ↓
STATE BOUNDARY
 ↓
TEMPORAL SCOPE
 ↓
PEDAGOGICAL IMPACT
 ↓
REQUIRED CONTROLS
 ↓
ACTION
```

---

# 10. Data origin

Distinguir estrictamente:

```text id="j6p7ct"
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

Estas categorías no son intercambiables.

```text
AGENT_GENERATED
≠
REAL_STUDENT_PERFORMANCE

TEST_FIXTURE
≠
PRODUCTION_DATA
```

Ejemplo:

```text
DATA_ORIGIN = SYNTHETIC_STUDENT
PROVENANCE = HUMAN_AUTHORED
USAGE_ROLE = TEST_FIXTURE
```

Y para una simulación generada por agente:

```text
DATA_ORIGIN = AGENT_SIMULATED_STUDENT
PROVENANCE = AGENT_GENERATED
USAGE_ROLE = TEST_FIXTURE
```

---

# 11. Synthetic student

Un `SYNTHETIC_STUDENT` es una representación controlada y explícita utilizada para pruebas.

Debe ser:

```text id="6j7i5v"
DECLARED
SYNTHETIC
BOUNDED
NON-PRODUCTION
TRACEABLE
```

---

# 12. Agent simulated student

Un `AGENT_SIMULATED_STUDENT` es una salida generada por un agente que representa comportamiento estudiantil.

No debe confundirse con un fixture manual.

Debe conservar:

```text id="0f0yz5"
AGENT_GENERATED
```

y permanecer fuera del pipeline de rendimiento real salvo una operación explícita, autorizada y auditada cuando la política lo permita.

---

# 13. Provenance non-convertibility

La etiqueta `AGENT_GENERATED` por sí sola no constituye protección suficiente.

Debe existir una barrera estructural o semántica que impida por defecto:

```text id="1ewf7z"
AGENT_GENERATED
      ↓
REAL_STUDENT_PERFORMANCE
```

La conversión no puede ocurrir implícitamente.

---

# 14. StudentState protection

Por defecto:

```text id="hup4e7"
STUDENT_STATE_TYPE = SYNTHETIC
PERSISTENCE = TEMPORARY
```

Un agente de ingeniería no puede:

- crear rendimiento real;
- modificar StudentState real;
- actualizar BKT real;
- alterar mastery real;
- registrar progreso pedagógico real.

Si una operación requiere `REAL_STUDENT`:

```text id="t2f4sp"
explicit authorization
+
policy compatibility
+
auditability
+
appropriate evidence
```

son obligatorias.

---

# 15. BKT boundary

Durante ingeniería:

```text id="qf8a8r"
BKT values
```

son artefactos de prueba si provienen de datos sintéticos.

No deben entrar al pipeline de mastery real.

Nunca utilizar:

```text id="3o3o6h"
fake observation
```

para generar un estado indistinguible de una observación pedagógica real.

---

# 16. Scaffolding

La política pedagógica determina los niveles de ayuda.

Por ejemplo:

```text id="flqv5m"
LEVEL 0
LEVEL 1
LEVEL 2
LEVEL 3
LEVEL 4
```

`talos-pedagogy` puede:

- verificar implementación;
- construir fixtures;
- comprobar transiciones;
- detectar bypasses;
- comprobar cumplimiento.

No puede elegir arbitrariamente un nivel pedagógico.

---

# 17. Scaffolding test contract

Los tests de scaffolding deben declarar, cuando corresponda:

```text id="5l2d5c"
SIMULATED_STUDENT_KNOWLEDGE_LEVEL
SIMULATED_STUDENT_RESPONSE
PEDAGOGICAL_POLICY_IDENTITY
EXPECTED_POLICY_BEHAVIOR
```

El resultado esperado debe derivarse de la política.

No de la preferencia del agente.

---

# 18. Pacto pedagógico

Cuando la política de TALOS establece que durante un ejercicio activo las ayudas deben ser socráticas:

```text id="7c2wpl"
Socratic assistance
```

es un requisito de comportamiento.

El agente no puede:

- revelar la solución;
- saltarse el mecanismo;
- proporcionar una solución completa;

si eso contradice la política aplicable.

La skill puede detectar el bypass.

No puede cambiar la política para justificarlo.

---

# 19. Evidence vs performance

Separar:

```text id="f1g5xj"
ENGINEERING_EVIDENCE
SYNTHETIC_TEST_RESULT
AGENT_OUTPUT
REAL_STUDENT_RESPONSE
ASSESSMENT
MASTERY
```

Un test sobre BKT no es una medición del estudiante.

Una simulación de estudiante no es una sesión real.

Una salida del agente no es una respuesta humana real.

---

# 20. Policy conformity

`talos-pedagogy` puede producir:

```text id="1r8f6e"
POLICY_CONFORMANCE_CHECK
```

para responder:

> ¿La implementación observada corresponde con la política declarada?

Esto no significa:

> ¿La política es pedagógicamente correcta?

La calidad o conveniencia de la política queda fuera de esta jurisdicción salvo que una política superior explícitamente delegue esa evaluación.

---

# 21. Policy deviation

Puede registrar:

```text id="ak8x7m"
POLICY_DEVIATION
```

cuando:

```text id="tv4b9j"
IMPLEMENTATION
≠
DECLARED POLICY
```

La desviación debe quedar como observación/riesgo según corresponda.

No inventar una política alternativa para “corregirla”.

---

# 22. Context and temporal scope

Una evaluación pedagógica debe identificar:

```text id="i6v2r9"
TASK_CONTEXT
POLICY_VERSION
DATA_ORIGIN
EXECUTION_CONTEXT
TEMPORAL_SCOPE
```

Una evidencia histórica no debe confundirse automáticamente con comportamiento pedagógico actual.

---

# 23. Controls by risk

Los controles requeridos dependen de:

```text id="5qf9k8"
PEDAGOGICAL_IMPACT
+
CHANGE_TYPE
+
AFFECTED_AUTHORITY
```

No solamente de severity.

Ejemplo:

```text id="n1l7xs"
LOW impact
+
documentation-only
```

puede requerir controles mínimos.

Mientras:

```text id="h2j7cf"
MEDIUM impact
+
StudentState boundary
```

puede requerir aislamiento y evidencia adicionales.

---

# 24. Cross-skill boundaries

### Testing

Testing determina:

```text id="qv3g1k"
TEST_EXECUTION_RESULT
```

Pedagogy determina qué controles pedagógicos debe cumplir el test.

---

### Evidence

Evidence preserva:

```text id="r1m5yx"
EVIDENCE
```

Pedagogy determina si esa evidencia puede tocar o representar datos pedagógicos sensibles.

---

### Isolation

Isolation determina:

```text id="qj3f4z"
ISOLATION_VERDICT
```

Pedagogy determina qué recursos pedagógicos deben considerarse protegidos.

---

### Audit

Audit puede detectar:

```text id="x1w0z7"
PEDAGOGICAL_RISK
```

Pedagogy clasifica el impacto y la conformidad pedagógica.

---

### Release

Release determina:

```text id="l7f5v4"
RELEASE_VERDICT
```

Pedagogy aporta:

```text id="m8w3z1"
PEDAGOGICAL_IMPACT
POLICY_CONFORMANCE
PEDAGOGICAL_EVIDENCE
```

pero no adjudica release.

---

# 25. Consumer validation

Todo objeto externo debe validarse:

```text id="w0r6ax"
IDENTITY
PRODUCER
PROVENANCE
SCOPE
TEMPORALITY
POLICY
STATUS
```

La validación realizada por otra skill no sustituye la validación propia.

---

# 26. Consumer evaluation

Cuando corresponda, crear:

```text id="w7p3ym"
CONSUMER_EVALUATION
```

separada del objeto consumido.

Debe responder:

> ¿Este objeto satisface mi precondición pedagógica actual?

No:

> ¿Este objeto es verdadero?

---

# 27. No-transfer of authority

Consumir:

```text id="3r6lqp"
TEST_EXECUTION_RESULT
```

no convierte a pedagogy en testing.

Consumir:

```text id="5j9p4c"
EVIDENCE_REF
```

no convierte a pedagogy en evidence.

Consumir:

```text id="2t5q4e"
ISOLATION_VERDICT
```

no convierte a pedagogy en isolation.

Cada skill conserva su jurisdicción.

---

# 28. Composition

Pedagogy no puede crear ad-hoc:

```text id="3m1qz0"
TEST_PASS
+
POLICY_CONFORMANCE
+
EVIDENCE_INTEGRITY
```

para producir:

```text id="z1o5p6"
RELEASE_ELIGIBLE
```

Toda nueva autoridad requiere una `COMPOSITION_RULE` autorizada por la política correspondiente.

---

# 29. Anti-pass-through

Una conclusión pedagógica no puede ser un simple renombrado de la conclusión de otra skill.

Ejemplo incorrecto:

```text id="5f1t9h"
testing:
    TEST_PASS

pedagogy:
    PEDAGOGICAL_CONFORMITY = PASS
```

sin que pedagogy haya evaluado su propia pregunta:

> ¿La implementación cumple la política pedagógica aplicable?

---

# 30. Unknown and contradiction

Si la política necesaria es desconocida:

```text id="h7d0a3"
UNKNOWN
```

no inferir.

Si existen políticas contradictorias:

```text id="x6f8k9"
CONTRADICTION
→ STOP
```

No seleccionar arbitrariamente la versión conveniente.

---

# 31. Agent boundaries

El agente puede:

```text id="6r7y0w"
inspect
simulate
test
propose
modify authorized code
document
report
```

No puede:

```text id="q9f3zc"
declare mastery
modify real BKT
invent student performance
weaken pedagogical policy
bypass scaffolding
convert synthetic data to real performance
```

---

# 32. Context routing

Para tareas pedagógicas:

```text id="b6o5kx"
CORE
    AGENTS.md

ACTIVE
    talos-pedagogy

SUPPORTING
    talos-testing
    talos-evidence
    talos-isolation
    talos-audit

DORMANT
    talos-release salvo gate/release
```

Si el boundary pedagógico es desconocido:

> ampliar contexto.

---

# 33. Completion criteria

Una evaluación pedagógica de ingeniería está completa cuando:

```text id="9m6y9a"
[ ] POLICY_IDENTITY
[ ] DATA_ORIGIN
[ ] EXECUTION_CONTEXT
[ ] TEMPORAL_SCOPE
[ ] PEDAGOGICAL_IMPACT
[ ] STATE_BOUNDARY
[ ] REQUIRED_CONTROLS
[ ] POLICY_CONFORMANCE
[ ] DEVIATIONS
[ ] UNKNOWN
[ ] CONTRADICTIONS
[ ] EVIDENCE_REFERENCES
[ ] LIMITATIONS
```

---

# 34. Regla final

> **El agente trabaja sobre TALOS, no como TALOS.**

La ingeniería puede verificar la implementación pedagógica.

No puede convertirse en:

```text id="t8z8z9"
TALOS PEDAGOGICAL AUTHORITY
```

ni convertir:

```text id="8x5y9k"
SYNTHETIC
AGENT_GENERATED
TEST_FIXTURE
```

en:

```text id="4r3v8w"
REAL_STUDENT_PERFORMANCE
```

sin una operación explícita, autorizada y auditable.

**Proteger la pedagogía no significa apropiarse de ella.**
