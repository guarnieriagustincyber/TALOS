# STUDY ENGINE

## Especificación de Ingeniería V1.0

**Estado:** FROZEN
**Objetivo:** Sistema personal de estudio basado en conocimiento verificable, planificación pedagógica, tutoría socrática y evaluación determinista/LLM-asistida.

---

## 1. PROPÓSITO

Study Engine tiene como objetivo reducir la fricción de aprender dominios complejos con múltiples fuentes.

El sistema debe transformar:

**Roadmap + fuentes + programa académico + estado del estudiante**

en:

**plan de estudio → explicación → práctica → evaluación → evidencia de dominio.**

No reemplaza la lectura de los libros ni el trabajo intelectual del estudiante.

La función del sistema es reducir la fricción de:

* seleccionar qué estudiar;
* ordenar contenidos;
* identificar prerequisitos;
* localizar evidencia;
* explicar conceptos;
* complementar fuentes;
* generar práctica;
* detectar lagunas;
* evaluar razonamiento;
* mantener continuidad.

---

# 2. PRINCIPIOS INMUTABLES

### P1 — Roadmap First

El roadmap es la raíz estructural del sistema.

Los libros, PDFs y demás fuentes aportan conocimiento, pero no reemplazan ni modifican automáticamente el roadmap.

---

### P2 — Deterministic First → AI Second

Todo lo que pueda resolverse determinísticamente debe resolverse mediante código.

La IA se utiliza para:

* interpretación;
* explicación;
* contextualización;
* comparación;
* generación de preguntas;
* evaluación lingüística;
* razonamiento asistido.

---

### P3 — Stateless LLM

El LLM no posee memoria implícita.

Todo contexto necesario debe ser construido explícitamente por el sistema.

---

### P4 — Evidence First

Toda afirmación factual derivada de conocimiento externo debe poder rastrearse hasta una fuente.

Estados permitidos:

```text
[SUPPORTED]
[PARTIALLY_SUPPORTED]
[COMPLEMENT]
[INFERENCE]
[NO_EVIDENCE]
```

---

### P5 — Abstention

Cuando no exista evidencia suficiente:

```text
[NO_EVIDENCE]
```

es una salida válida y preferible a inventar.

---

### P6 — Human Learning Remains Human

El estudiante debe:

* leer;
* pensar;
* escribir;
* programar;
* resolver;
* explicar;
* corregir.

La IA no debe convertirse en una máquina de producir respuestas que el alumno simplemente consume.

---

### P7 — No Automatic Advancement

El LLM nunca decide por sí solo que el estudiante dominó un tema.

El avance depende de evidencia y reglas.

---

# 3. ARQUITECTURA GENERAL

```text
                    ┌─────────────────────┐
                    │   MASTER ROADMAP    │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
          PLANIFICADOR                  PREREQUISITOS
                │                             │
                └──────────────┬──────────────┘
                               ▼
                        CURRENT OBJECTIVE
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
          BOOKS              COURSES          OTHER SOURCES
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                         KNOWLEDGE/RAG
                               │
                               ▼
                       CONTEXT PACKER
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
      TUTOR                  TESTER                 AUDITOR
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               ▼
                         OUTPUT VALIDATOR
                               │
                               ▼
                      STUDENT INTERACTION
                               │
                               ▼
                        EVIDENCE / STATE
```

---

# 4. CAPA 1 — KNOWLEDGE

El sistema debe permitir incorporar:

* libros;
* PDFs;
* documentación;
* apuntes;
* programas analíticos;
* material docente;
* documentación oficial;
* fuentes complementarias.

Cada fuente tendrá metadata.

Mínimo:

```yaml
source_id:
title:
author:
type:
language:
role:
priority:
subject:
course:
phase:
chapter:
section:
page:
```

Metadata incompleta no debe bloquear la ingesta.

---

# 5. ROLES DE FUENTE

Una fuente puede ser:

```text
PRIMARY
SECONDARY
REFERENCE
OFFICIAL
COURSE
PRACTICAL
COMPLEMENTARY
```

El sistema no debe asumir que PRIMARY significa "infalible".

Significa:

> fuente utilizada como referencia principal para esa trayectoria.

---

# 6. CUADERNOS / KNOWLEDGE BASES

Cada dominio puede tener un cuaderno independiente.

Ejemplo:

```text
knowledge/
├── fase_0_programacion/
├── redes/
├── sistemas_operativos/
├── criptografia/
├── deteccion/
├── incident_response/
└── threat_intelligence/
```

Además:

```text
university/
├── materia_redes/
├── materia_programacion/
└── materia_sistemas/
```

Cada cuaderno puede contener:

* fuentes;
* metadata;
* roadmap asociado;
* programa analítico;
* estado del estudiante;
* evaluaciones.

No se mezclan automáticamente conocimientos de cuadernos distintos.

---

# 7. MASTER ROADMAP

El roadmap debe definir:

```yaml
module:
  objective:
  prerequisites:
  concepts:
  exercises:
  evaluation:
  gateway:
```

La estructura mínima será:

```text
FASE
 └── MÓDULO
      └── SUBMÓDULO
           └── TEMA
                ├── prerequisitos
                ├── fuentes
                ├── explicación
                ├── ejercicios
                ├── evaluación
                └── evidencia de dominio
```

---

# 8. DIRECTOR PEDAGÓGICO

El Director Pedagógico transforma el roadmap en una secuencia de estudio.

Debe poder:

1. interpretar el módulo;
2. descomponerlo;
3. identificar prerequisitos;
4. localizar fuentes;
5. seleccionar la mejor fuente para cada objetivo;
6. detectar huecos;
7. solicitar fuentes adicionales;
8. generar el recorrido punto por punto;
9. adaptar profundidad;
10. registrar progreso.

No debe cambiar silenciosamente el roadmap.

Si propone modificarlo:

```text
ROADMAP CONFLICT DETECTED
```

y requiere decisión humana.

---

# 9. SOURCE SELECTION

El sistema no debe ser dogmático con un único autor.

Para cada concepto puede seleccionar:

```text
PRIMARY SOURCE
+
BEST COMPLEMENTARY SOURCE
+
OPTIONAL DEEP-DIVE SOURCE
```

La selección debe responder:

* ¿qué fuente explica mejor este concepto?
* ¿cuál aporta rigor?
* ¿cuál aporta intuición?
* ¿cuál aporta práctica?
* ¿cuál cubre una laguna?

---

# 10. SOURCE EXPANSION

El Director puede solicitar nuevas fuentes.

Pero solamente cuando pueda justificar:

```text
GAP:
qué falta

IMPACT:
por qué importa

CURRENT_COVERAGE:
qué tenemos

MISSING_DEPTH:
qué falta

REQUESTED_SOURCE:
qué tipo de fuente necesitamos

MANDATORY / OPTIONAL:
nivel de necesidad
```

Nunca se debe recomendar bibliografía indefinidamente.

---

# 11. RAG

V1 debe priorizar:

```text
lexical retrieval
+
semantic retrieval
+
reranking
+
metadata filtering
```

La arquitectura debe permitir cambiar:

* embedding model;
* vector store;
* reranker;
* retrieval strategy.

Open WebUI puede utilizar búsqueda híbrida BM25 + vectorial + CrossEncoder, además de Knowledge Bases y herramientas de búsqueda documental.

---

# 12. CONTEXT PACKER

Python construye el contexto final.

Debe contener:

```text
ROADMAP CONTEXT
CURRENT OBJECTIVE
PREREQUISITES
STUDENT STATE
ACTIVE MODE
SOURCE HIERARCHY
RETRIEVED EVIDENCE
CITATIONS
OUTPUT CONTRACT
```

El LLM recibe únicamente el contexto necesario.

---

# 13. MODOS

V1 tendrá cuatro modos principales.

### TUTOR

Objetivo:

comprender.

Puede:

* explicar;
* utilizar analogías;
* dividir conceptos;
* hacer preguntas;
* comparar fuentes;
* detectar confusión;
* continuar el recorrido.

No debe resumir excesivamente.

---

### TESTER

Objetivo:

demostrar comprensión.

Puede:

* preguntar;
* generar ejercicios;
* generar edge cases;
* pedir explicación;
* evaluar respuestas;
* detectar errores;
* generar contraejemplos.

No debe entregar inmediatamente la solución.

---

### AUDITOR

Objetivo:

análisis profundo.

Se utiliza cuando:

* existen contradicciones;
* hay una duda conceptual compleja;
* hay múltiples fuentes;
* el estudiante cuestiona una explicación;
* se necesita una revisión profunda.

---

### PLANNER

Objetivo:

organizar el estudio.

Produce:

```text
qué estudiar
por qué
prerequisitos
fuentes
orden
profundidad
ejercicios
criterio de dominio
```

---

# 14. CHAT

La interfaz debe sentirse como un chat normal.

No se requiere consola para estudiar.

La consola queda para:

* desarrollo;
* ejecución de tests;
* administración;
* debugging.

El estudiante puede conversar normalmente:

> "No entendí esto."

> "Explicamelo desde cero."

> "¿Por qué Joyanes lo plantea así?"

> "¿Spraul agrega algo importante?"

> "Sigamos con el siguiente punto."

> "Tomame una evaluación."

El sistema mantiene el contexto mediante el Context Packer, no mediante memoria implícita del LLM.

---

# 15. EVALUACIÓN

El dominio de un tema debe construirse con múltiples evidencias.

Ejemplo:

```text
CONCEPTUAL
✓ puede explicar

RECOGNITION
✓ identifica correctamente

APPLICATION
✓ resuelve ejercicio

TRANSFER
✓ aplica a problema nuevo

REASONING
✓ puede justificar

PRACTICAL
✓ implementa

TEST
✓ supera pruebas

TEACH-BACK
✓ puede explicarlo con sus palabras
```

La evaluación debe poder detectar:

```text
memorization
vs
understanding
vs
transfer
```

---

# 16. CÓDIGO

El sistema nunca debe reemplazar el trabajo manual del estudiante.

Flujo:

```text
STUDENT
   ↓
writes code
   ↓
pytest
   ↓
deterministic result
   ↓
TESTER
   ↓
conceptual audit
```

Python/pytest determina si el programa funciona.

El LLM interpreta y enseña.

---

# 17. ESTADO DEL ESTUDIANTE

El sistema debe mantener estado estructurado.

Ejemplo:

```yaml
topic:
  status: developing

understanding:
  conceptual: true
  application: false
  transfer: false

strengths:
  - loops

weaknesses:
  - nested conditions

recurring_errors:
  - boundary conditions

last_evaluation:
  score: ...

next_action:
  type: targeted_exercise
```

Este estado no depende de la memoria del modelo.

---

# 18. QUALITY ENGINEERING

Cada subsistema se desarrolla como una unidad certificable.

Estados:

```text
DESIGN
↓
IMPLEMENTATION
↓
TESTING
↓
FAILURE ANALYSIS
↓
REPAIR
↓
RETEST
↓
CERTIFICATION
```

---

# 19. TIPOS DE TEST

Cada subsistema debe incluir, cuando corresponda:

### Unit Tests

Funciones individuales.

### Integration Tests

Interacción entre componentes.

### Contract Tests

Interfaces y schemas.

### Failure Tests

Inputs inválidos, ausencia de datos, APIs caídas, metadata corrupta.

### Regression Tests

Evitar que una corrección rompa funcionalidades anteriores.

### Security Tests

Secrets, permisos, path traversal, inyección, datos sensibles.

### Performance Tests

Latencia, memoria, tamaño de contexto.

### Adversarial Tests

Intentos deliberados de romper:

* retrieval;
* validación;
* abstención;
* contratos;
* separación de fuentes;
* permisos;
* estado.

### Benchmark Tests

Calidad objetiva del componente.

---

# 20. PROTECTED TESTS

Existirá una suite:

```text
tests/protected/
```

Los agentes no podrán modificarla silenciosamente.

La protección será determinista mediante Git/CI/checksum.

Un agente que necesite modificar un test protegido deberá demostrar:

```text
SPEC_CONTRADICTION
+
REPRODUCTION
+
JUSTIFICATION
```

Nunca:

> "cambié el test porque estaba fallando."

---

# 21. QUALITY GATE

No habrá un "score promedio" que permita ocultar fallos.

### HARD GATES

Todos deben pasar:

```text
unit
integration
contracts
protected tests
critical failure tests
security checks
schema validation
```

### SOFT METRICS

Se informan:

```text
coverage
latency
memory
retrieval recall
benchmark score
```

pero no sustituyen un hard gate.

---

# 22. DEBUG AGENT

Un agente puede investigar automáticamente un fallo.

Flujo:

```text
FAIL
 ↓
COLLECT EVIDENCE
 ↓
FORM HYPOTHESIS
 ↓
REPRODUCE
 ↓
PATCH
 ↓
TEST
 ↓
REGRESSION
 ↓
ADVERSARIAL TEST
 ↓
PASS?
 ├── NO → repeat
 └── YES → candidate certification
```

El agente no certifica.

El Quality Gate certifica.

---

# 23. RAG BENCHMARK

Existirá:

```text
study_engine_rag_bench/
```

con un dataset humano de preguntas.

Cada caso tendrá:

```yaml
question:
expected_sources:
required_concepts:
forbidden_claims:
acceptable_evidence:
expected_abstention:
```

Se medirán al menos:

```text
retrieval accuracy
citation accuracy
grounding
abstention correctness
source-priority correctness
cross-source reasoning
```

---

# 24. OBSERVABILITY

V1 almacenará eventos estructurados:

```text
sessions/
events/
student_state/
evaluations/
retrieval_logs/
```

Esto permitirá posteriormente construir dashboards.

---

# 25. OBSIDIAN

No forma parte de V1.

Pero V1 debe producir datos exportables.

V2 podrá utilizar Obsidian como:

**visualizador de telemetría del sistema.**

No será el lugar donde se escriban las síntesis manuales del estudiante.

---

# 26. APPFLOWY

AppFlowy permanece fuera de la arquitectura automática.

La síntesis manual continúa siendo manual.

Esto protege la función pedagógica de:

```text
leer
→ procesar
→ sintetizar
→ escribir
```

---

# 27. MODELOS

Los modelos son componentes intercambiables.

No se codificará la arquitectura alrededor de:

* un proveedor;
* un modelo;
* una API;
* una cuota gratuita.

La configuración podrá definir:

```yaml
tutor:
  provider:
  model:

tester:
  provider:
  model:

auditor:
  provider:
  model:
```

Como ejemplo actual, GPT-OSS 120B en Groq dispone de structured outputs, reasoning y code execution, por lo que puede encajar técnicamente en el rol Tester, pero el sistema no dependerá de ese modelo.

---

# 28. PRIVACIDAD

Nunca enviar automáticamente a APIs cloud:

* API keys;
* passwords;
* tokens;
* secretos;
* información privada innecesaria;
* datos sensibles del sistema.

El Context Packer debe aplicar una política de sanitización antes de cualquier llamada cloud.

---

# 29. V1 — IN SCOPE

```text
✓ Knowledge ingestion
✓ Metadata
✓ Cuadernos/Knowledge Bases
✓ Roadmap
✓ Prerequisites
✓ Planner
✓ Tutor
✓ Tester
✓ Auditor
✓ RAG
✓ Evidence
✓ Citations
✓ Abstention
✓ Context Packer
✓ Output Validator
✓ Student State
✓ Evaluation
✓ pytest integration
✓ Quality Gates
✓ Protected Tests
✓ RAG Benchmark
✓ Logs/Event Store
✓ API abstraction
```

---

# 30. V1 — OUT OF SCOPE

```text
✗ Obsidian integration
✗ AppFlowy automation
✗ Mobile app
✗ Custom frontend
✗ Multi-user system
✗ SaaS
✗ Marketplace
✗ Autonomous code writing
✗ Autonomous progression
✗ Autonomous curriculum modification
✗ Fully autonomous agents
✗ Commercialization
✗ Complex dashboards
```

---

# 31. CRITERIO DE "V1 TERMINADA"

V1 no estará terminada cuando:

> "funcione el chat."

Estará terminada cuando:

```text
ALL SUBSYSTEMS CERTIFIED
        +
PROTECTED TESTS GREEN
        +
INTEGRATION GREEN
        +
SECURITY GATES GREEN
        +
RAG BENCHMARK ACCEPTABLE
        +
ABSTENTION VERIFIED
        +
CITATIONS VERIFIED
        +
ROADMAP INTEGRATION VERIFIED
        +
TUTOR/TESTER CONTRACTS VERIFIED
        +
REPRODUCIBLE DEPLOYMENT
```

La regla definitiva es:

> **No se avanza al siguiente subsistema mientras el actual no esté certificado.**

---

# 32. PRINCIPIO FINAL

El sistema no intenta construir una IA "más inteligente".

Construye un entorno donde:

**mejor contexto + mejores fuentes + mejor recuperación + mejores contratos + mejores tests + mejor evaluación**

producen un sistema de estudio más confiable.

La inteligencia del modelo es solamente una variable dentro de ese sistema.

