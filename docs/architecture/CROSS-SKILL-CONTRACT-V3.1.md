
# TALOS Skills V3.1 — Canonical Normalization Notes

Este documento acompaña la revisión V3.1 y define las modificaciones obligatorias sobre las seis skills existentes.

---

## 1. talos-audit

Agregar formalmente:

### Contradiction ownership

`talos-audit` es el propietario de contradicciones **cross-skill**.

```text
INTRA-SKILL CONTRADICTION
→ owning skill

CROSS-SKILL CONTRADICTION
→ talos-audit
```

Audit puede recibir contradicciones producidas por consumidores y adjudicar su relación transversal.

También debe declarar:

```text
F-17 BOUNDED META-VERIFICATION
```

Audit constituye uno de los terminales de revisión transversal.

No crea una nueva autoridad a partir de esa revisión.

---

## 2. talos-isolation

Canonicalizar:

```text
ISOLATION_VERDICT
BOUNDARY_STATUS
STATIC_ISOLATION_ASSESSMENT
```

No utilizar `TEST_RESULT` como tipo producido.

Cuando isolation consume un test:

```text
TEST_EXECUTION_RESULT
```

debe crear su propia evaluación de precondición.

Si detecta una contradicción interna, la posee isolation.

Si el conflicto es entre resultados de distintas jurisdicciones:

```text
→ talos-audit
```

Agregar referencia explícita a F-17.

---

## 3. talos-testing

Canonicalizar:

```text
TEST_EXECUTION_RESULT
```

como nombre contractual.

`TEST_RESULT` queda solamente como shorthand textual.

Testing produce su propio:

```text
EVALUATION_RECORD
```

cuando evalúa inputs externos.

Un `TEST_EXECUTION_RESULT` no puede transformarse en:

```text
ISOLATION_VERDICT
PEDAGOGICAL_CONFORMITY_STATUS
GATE_SATISFIED
```

sin una composición autorizada.

---

## 4. talos-evidence

Mantener:

```text
EVIDENCE_REF
EVIDENCE_RECORD
PROVENANCE_RECORD
EVIDENCE_LINEAGE
```

Agregar explícitamente:

> Evidence provenance no constituye autoridad epistemológica.

Y:

```text
AGENT_GENERATED
TEST_FIXTURE
SYNTHETIC
```

deben permanecer identificables durante todo el lineage.

Una transformación nunca puede eliminar la provenance crítica.

Si una transformación intenta producir:

```text
REAL_STUDENT_PERFORMANCE
PRODUCTION_EVIDENCE
```

desde datos sintéticos/agentes sin una operación autorizada:

```text
BLOCK
```

---

## 5. talos-pedagogy

Adoptar definitivamente la taxonomía:

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

Ejemplo válido:

```text
DATA_ORIGIN = SYNTHETIC_STUDENT
PROVENANCE = HUMAN_AUTHORED
USAGE_ROLE = TEST_FIXTURE
```

Otro:

```text
DATA_ORIGIN = AGENT_SIMULATED_STUDENT
PROVENANCE = AGENT_GENERATED
USAGE_ROLE = TEST_FIXTURE
```

Agregar explícitamente:

```text
AGENT_GENERATED
≠
REAL_STUDENT_PERFORMANCE
```

y:

```text
TEST_FIXTURE
≠
PRODUCTION_DATA
```

Toda transición requiere operación autorizada y auditable.

Canonicalizar:

```text
POLICY_CONFORMANCE_CHECK
        ↓
PEDAGOGICAL_CONFORMITY_STATUS
```

`POLICY_CONFORMANCE_CHECK` es la evaluación.

`PEDAGOGICAL_CONFORMITY_STATUS` es su resultado.

---

## 6. talos-release

Canonicalizar:

```text
TEST_EXECUTION_RESULT
```

como input de testing.

Agregar la semántica exacta:

```text
GATE_WAIVED
≠
GATE_SATISFIED
```

y:

```text
UNKNOWN
≠
PASS
```

Formalizar:

```text
RELEASE_ELIGIBLE
RELEASE_ELIGIBLE_WITH_RISKS
RELEASE_BLOCKED
RELEASE_NOT_DEMONSTRATED
RELEASE_EXCEPTIONALLY_ELIGIBLE
```

con las definiciones del Contract V3.1.

Agregar F-14:

```text
cross-skill contradiction
→ consume contradiction record
→ does not own cross-skill adjudication
```

Agregar F-17:

```text
GATE_EVALUATION
→ may be meta-verified
→ terminal audit/human review
→ bounded recursion
```

---

# 7. AGENTS.md

AGENTS debe incorporar únicamente las reglas normativas.

Agregar:

```text
CROSS-SKILL CONTRACT VERSION = V3.1
```

y las siguientes reglas:

```text
CROSS-SKILL CONTRADICTION
→ talos-audit owns adjudication

GATE_WAIVED
≠
GATE_SATISFIED

UNKNOWN
≠
PASS

AGENT_GENERATED
≠
REAL_STUDENT_PERFORMANCE

TEST_FIXTURE
≠
PRODUCTION_DATA
```

También debe declarar:

```text
F-17:
META-VERIFICATION IS BOUNDED.
TERMINAL REVIEW DOES NOT CREATE NEW TRANSVERSAL AUTHORITY.
```

No convertir las tablas operativas de provenance, gate lifecycle o meta-verification en una segunda política escondida.

---

# 8. Rule against duplication

Ninguna skill debe copiar en detalle el contrato completo V3.1.

El contrato define:

```text
INTERFACE
AUTHORITY
OWNERSHIP
COMPOSITION
INVARIANTS
```

Cada skill define:

```text
PROCEDURE
DOMAIN-SPECIFIC CHECKS
OUTPUTS
LIMITATIONS
COMPLETION CRITERIA
```

Por tanto:

```text
AGENTS.md
    = normative core

CROSS-SKILL CONTRACT
    = interface/authority contract

SKILL.md
    = operational procedure
```

---

# 9. Final consistency requirement

Después de aplicar esta normalización:

```text
AGENTS.md
    ↕
CROSS-SKILL CONTRACT
    ↕
talos-audit
talos-isolation
talos-testing
talos-evidence
talos-pedagogy
talos-release
```

debe existir una única semántica para:

```text
authority
producer
consumer
scope
temporal validity
provenance
unknown
contradiction
composition
release
pedagogical origin
```

No debe existir una definición local incompatible con la definición contractual.

---

# 10. Closure condition

La arquitectura queda cerrada cuando:

```text
[✓] no authority inversion
[✓] no jurisdiction overlap
[✓] no hidden delegation
[✓] no pass-through
[✓] no synthetic → production leakage
[✓] no unknown → pass
[✓] no waiver → satisfaction
[✓] contradiction ownership explicit
[✓] meta-verification bounded
[✓] release states unambiguous
[✓] object names canonical
[✓] pedagogical taxonomy orthogonal
[✓] routing fail-closed
[✓] temporal identity preserved
```

**STATUS: READY FOR FINAL FREEZE**
