# TALOS V1.5 — STEP-35

## RECONCILIACIÓN DOCUMENTAL CONTROLADA DEL REGISTRO DE DECISIONES B1–B8

**Tipo:** reconciliación documental estática, con trazabilidad probatoria y sin autorización operativa.
**Repositorio observado:** `/media/agustin/Laboratorio/study-engie`
**Rama observada:** `talos-current-audit`
**HEAD observado:** `cc8acfae623f9d10c8366871470319786b6a7ca4`
**Entregable único:** `docs/STEP-35-REGISTRO-RECONCILIADO-DE-DECISIONES-B1-B8.md`

---

## 1. Objetivo

STEP-35 toma como entrada STEP-33 y STEP-34 y produce una versión documental reconciliada del registro de decisiones de B1-01 a B8-01, preservando ambos antecedentes como documentos de referencia y sin reemplazarlos ni editarlos.

El objetivo no es cerrar la brecha ni autorizar implementación. Es reducir la ambigüedad del registro, distinguir mejor decisiones, dependencias, autoridad y predicados, y dejar explícitos los límites de evidencia de la documentación disponible.

STEP-34 concluyó que el registro era `SUFFICIENT_WITH_LIMITATIONS`. STEP-35 lo convierte en una versión más precisa, sin reabrir la auditoría general ni sostener que existe autorización operativa.

---

## 2. Estados canónicos obligatorios

Se conservan exactamente:

- `TALOS V1 = FROZEN`
- `P1.2 = BLOCKED-REGRESSION`
- `P1.3 = BLOCKED`
- `B1-R = NOT AUTHORIZED`
- `EXTERNAL HARNESS IMPLEMENTATION = NOT AUTHORIZED`
- `DYNAMIC VALIDATION = NOT AUTHORIZED`
- `GATE B = INCOMPLETE`

Estados documentales de referencia:

- `DOCUMENTARY_AUDIT = COMPLETE_WITH_OPEN_GAPS`
- `EVIDENTIARY_SUFFICIENCY = PARTIALLY_SUPPORTED_WITH_OPEN_EVIDENTIARY_GAPS`
- `AUTHORITY IDENTIFICATION = INCOMPLETE`
- `B1-01` a `B7-01 = OPEN`
- `B8-01 = ABSENT / NOT_SATISFIED`

Estos estados no se elevan ni se sustituye por un estado más favorable por la mera existencia del documento reconciliado.

---

## 3. Alcance autorizado

Se permite exclusivamente:

1. inspección estática de STEP-33 y STEP-34;
2. lectura de STEP-27, STEP-28 y STEP-29 para contrastar requisitos y adjudicaciones;
3. lectura de STEP-31, STEP-31B a STEP-31G y STEP-32 cuando eran necesarios para verificar la base de una decisión;
4. lectura de referencias previas adicionales solo cuando una citación resulta imprescindible y puede localizarse verificablemente;
5. operaciones Git estrictamente de lectura para identificar rama, HEAD y estado visible del árbol;
6. creación exclusiva del documento STEP-35.

No se permite:

- modificar STEP-33, STEP-34 o cualquier documento previo;
- editar código, tests, configuración, snapshots, bases de datos o corpus;
- ejecutar tests, incluido `pytest --collect-only`;
- importar o ejecutar código del proyecto;
- iniciar backend, lifespan, workers, verifiers, observers, harnesses o preflight;
- acceder a bases de datos, modelos, proveedores o estado de aprendizaje;
- ejecutar validación dinámica o benchmarks;
- ejecutar operaciones Git mutativas;
- publicar o modificar contenido en GitHub;
- atribuir autoridades por conjetura o inferencia;
- convertir una dependencia de planificación en requisito normativo sin evidencia;
- cerrar brechas ni conceder autorización operativa.

Cuando una referencia no existe, no está localizada o no puede verificarse, se registra como `NOT LOCATED` o `NOT EVALUABLE`.

---

## 4. Preservación de la fuente

STEP-33 y STEP-34 son antecedentes inmutables y conservados como fuentes de origen. STEP-35 es un artefacto derivado, cuyo valor radica en la forma más precisa de relacionar decisiones, autoridad, dependencias y predicados.

Se conserva la trazabilidad mínima siguiente:

- fuente original: STEP-33
- fuente de adjudicación: STEP-34
- fuente de requisitos contratuales: STEP-27, STEP-28, STEP-29
- fuentes complementarias: STEP-31 y STEP-32, cuando existen y se usan con fundamento

No se hace afirmación de “preservación por hash” si la comparación no se ejecutó bajo alcance permitido.

---

## 5. Contrato de reconciliación

### 5.1. Principio de diferenciación

La reconciliación distingue cinco cosas que el registro inicial mezclaba en una dimensión general:

1. requisito contractual o criterio (`C01`–`C15` y `B1-01`–`B8-01`);
2. decisión pendiente que requiere una adjudicación;
3. autoridad y competencia requerida;
4. evidencia futura que permitiría demostrar la decisión;
5. acción futura o autorización operativa que no puede inferirse del registro documental.

Este documento actualiza la clasificación y la relación entre estos elementos sin cambiar el bloqueo canónico.

### 5.2. Revisión de granularidad

Las 16 decisiones originarias del STEP-33 quedan agrupadas en tres tipos:

- `ATOMIC`: responde a una única cuestión decisoria con predicado de cierre independiente;
- `COMPOSITE`: tiene varias decisiones o requisitos que podrían resolverse por separado;
- `PREPARATORY_ACTION`: describe actividad documental o preparación, pero no una decisión sustantiva.

Clasificación reconciliada por decisión:

| decision_id | classification | rationale |
|---|---|---|
| DEC-B1-01 | `COMPOSITE` | Reúne política, root, autoridad y anti-rollback. La lógica de la decisión requiere separar política y autoridad. |
| DEC-B1-02 | `ATOMIC` | Se refiere a la autoridad de aprobación de la política. |
| DEC-B1-03 | `ATOMIC` | Se refiere a versión mínima y anti-rollback. |
| DEC-B1-04 | `ATOMIC` | Se refiere a rama, privilegios y límites. |
| DEC-B2-01 | `COMPOSITE` | Combina identidad de entidades, reglas y relaciones. Requiere distinguir identidad, relación y ciclo de vida. |
| DEC-B2-02 | `ATOMIC` | Se refiere a la autoridad de aprobación del esquema. |
| DEC-B3-01 | `ATOMIC` | Es un punto de decisión sobre procedencia y custodia. |
| DEC-B3-02 | `ATOMIC` | Es un punto de decisión sobre separación de responsabilidades. |
| DEC-B4-01 | `COMPOSITE` | Reune catálogo de estados, agregación y transiciones. Debe descomponerse entre semántica de estados y reglas de agregado. |
| DEC-B5-01 | `COMPOSITE` | Reúne preflight, evidencia, rechazo y consecuencia. Debe distinguir el control del requisito de evidencia. |
| DEC-B6-01 | `COMPOSITE` | Reúne digest, serialización, alcance y algoritmo. Debe diferenciar definición canónica, orden y aprobación. |
| DEC-B6-02 | `ATOMIC` | Se refiere a la aprobación del par `(nodeids, tree_digest)`. |
| DEC-B7-01 | `COMPOSITE` | Combina campaña, intentos, idempotencia y cierre. |
| DEC-B7-02 | `ATOMIC` | Se refiere a contradicciones y resolución. |
| DEC-B8-01 | `ATOMIC` | Se refiere a la matriz de trazabilidad final. |
| DEC-B8-02 | `ATOMIC` | Se refiere a la autoridad de suficiencia documental. |

Se crean subdecisiones solo cuando es necesario y se documenta la relación con la decisión original.

#### Subdecisiones derivadas

| decision_id | source_decision_id | classification | reason |
|---|---|---|---|
| DEC-B1-01.a | DEC-B1-01 | `ATOMIC` | Política y artefacto protegido. |
| DEC-B1-01.b | DEC-B1-01 | `ATOMIC` | Autoridad y revocación de la política. |
| DEC-B2-01.a | DEC-B2-01 | `ATOMIC` | Entidades e identidad. |
| DEC-B2-01.b | DEC-B2-01 | `ATOMIC` | Relaciones y ciclo de vida. |
| DEC-B4-01.a | DEC-B4-01 | `ATOMIC` | Catálogo de estados. |
| DEC-B4-01.b | DEC-B4-01 | `ATOMIC` | Reglas de agregación y transición. |
| DEC-B5-01.a | DEC-B5-01 | `ATOMIC` | Control y predicado. |
| DEC-B5-01.b | DEC-B5-01 | `ATOMIC` | Evidencia y consecuencias de rechazo. |
| DEC-B6-01.a | DEC-B6-01 | `ATOMIC` | Definición canónica del digest. |
| DEC-B6-01.b | DEC-B6-01 | `ATOMIC` | Orden canónico y alcance. |
| DEC-B7-01.a | DEC-B7-01 | `ATOMIC` | Definición y ciclo de vida de la campaña. |
| DEC-B7-01.b | DEC-B7-01 | `ATOMIC` | Reintentos, idempotencia y cierre. |

No se crean nuevas subdecisiones para rellenar filas; solo se crean cuando la estructura real del problema lo exige.

### 5.3. Autoridad

Se mantiene la regla de no inferencia: si la fuente no identifica de forma verificable una autoridad competente, se registra como `AUTHORITY NOT IDENTIFIED`.

Estados de autoridad coherentes con la documentación:

- `AUTHORITY NOT IDENTIFIED`;
- `AUTHORITY ROLE DESCRIBED, IDENTITY NOT ESTABLISHED`;
- `AUTHORITY IDENTIFIED, COMPETENCE NOT ESTABLISHED`;
- `AUTHORITY AND COMPETENCE DOCUMENTED`;
- `NOT EVALUABLE`.

En el registro reconciliado:

- la mayoría de las decisiones deben permanecer en `AUTHORITY NOT IDENTIFIED` o `AUTHORITY ROLE DESCRIBED, IDENTITY NOT ESTABLISHED`;
- la identidad documental de autoridades no se asume por la presencia de documentos o nombres técnicos;
- ninguna autoridad es considerara competente por mera similitud funcional.

### 5.4. Reconciliación de estados

Se utiliza un conjunto de estados documentales con condiciones explícitas:

- `PENDING`: falta una decisión documentable o una necesidad de adjudicación, pero aún no se ha identificado el bloqueo dominante;
- `BLOCKED_BY_AUTHORITY`: falta la autoridad competente o la competencia no está establecida;
- `BLOCKED_BY_DEPENDENCY`: una dependencia concreta impide avanzar;
- `CONFLICT_REQUIRES_ADJUDICATION`: existe una tensión documentada que requiere resolución; no se puede decidir sin evidencia comparativa suficiente;
- `NOT EVALUABLE`: la documentación no permite clasificar responsablemente la decisión;
- `DOCUMENTED_PENDING_APPROVAL`: existe propuesto/documentado, pero falta aprobación demostrada;
- `APPROVAL_NOT_EVIDENCED`: existe un artefacto, pero no evidencia de aprobación;
- `CLOSED_DOCUMENTALLY`: solo cuando el predicado de cierre documental se satisface explícitamente y no implica autorización operativa.

Reglas mínimas aplicadas:

- `PENDING` no implica autoridad identificada ni decisión posible.
- `BLOCKED_BY_AUTHORITY` requiere evidencia de que falta una autoridad o de que la competencia no está documentada.
- `BLOCKED_BY_DEPENDENCY` exige una dependencia concreta y demostrable.
- `CONFLICT_REQUIRES_ADJUDICATION` solo si la tensión es visible y la comparación es suficiente.
- `APPROVAL_NOT_EVIDENCED` no significa “nunca existió”; solo que la documentación no ofrece evidencia suficiente.
- `CLOSED_DOCUMENTALLY` no implica cierre contractual ni operativa.

### 5.5. Reconciliación de las decisiones original y su estado

| decision_id | reconciled_status | rationale |
|---|---|---|
| DEC-B1-01 | `BLOCKED_BY_AUTHORITY` | La raíz de confianza y política protegida requiere autoridad que no está identificada. |
| DEC-B1-02 | `BLOCKED_BY_AUTHORITY` | Falla la identificación de autoridad aprobadora. |
| DEC-B1-03 | `BLOCKED_BY_AUTHORITY` | Hay requisito de versión mínima y anti-rollback, pero no autoridad. |
| DEC-B1-04 | `BLOCKED_BY_AUTHORITY` | Rama, privilegios y límites no tienen decisión de autoridad documentada. |
| DEC-B2-01 | `PENDING` | Requisito claro, pero no hay esquema aprobado. |
| DEC-B2-02 | `BLOCKED_BY_AUTHORITY` | Esquema requiere autoridad de aprobación. |
| DEC-B3-01 | `PENDING` | Hay necesidad documental, pero no mecanismo de procedencia y custodia aprobado. |
| DEC-B3-02 | `BLOCKED_BY_AUTHORITY` | La separación de responsabilidades requiere autoridad y evidencia. |
| DEC-B4-01 | `PENDING` | Hay requisito, no catálogo completo ni regla final. |
| DEC-B5-01 | `BLOCKED_BY_AUTHORITY` | Preflight requiere control y autoridad para rechazar; no están resueltos. |
| DEC-B6-01 | `BLOCKED_BY_AUTHORITY` | Digest y alcance requieren aprobación y autoridad no identificada. |
| DEC-B6-02 | `BLOCKED_BY_AUTHORITY` | Aprobación y revocación del par indivisible no documentada. |
| DEC-B7-01 | `PENDING` | Protocolo de campaña no determinado. |
| DEC-B7-02 | `CONFLICT_REQUIRES_ADJUDICATION` | Hay conflicto o diferencia de nivel, pero aún requiere comparación documental. |
| DEC-B8-01 | `PENDING` | Matriz de trazabilidad no finalizada; no es cierre. |
| DEC-B8-02 | `BLOCKED_BY_AUTHORITY` | Suficiencia documental requiere autoridad para adjudicarla. |

---

## 6. Reconciliación de dependencias

Se formalizan relaciones entre decisiones sin convertirlas en requisitos normativos sin evidencia. La clasificación fue adaptada del modelo de STEP-33, pero con más exigencia documental:

- `NORMATIVE_DEPENDENCY_SUPPORTED`: la dependencia aparece en requisito o cláusula y puede relacionarse con la decisión y con la evidencia de origen;
- `DOCUMENTED_PLANNING_PRECEDENCE`: el orden se desprende del plan o registro, pero no aparece como requisito normativo externo;
- `PROPOSED_DEPENDENCY`: hipótesis de orden o conveniencia, no confirmada;
- `DEPENDENCY_NOT_EVALUABLE`: la evidencia no permite decidir.

### 6.1. Dependencias reconciliadas

| dependency_id | from_decision | to_decision | category | evidence_basis | status |
|---|---|---|---|---|---|
| DEP-B1-01 | DEC-B1-01.a | DEC-B2-01.a | `NORMATIVE_DEPENDENCY_SUPPORTED` | La identidad y la política son dependencias documentadas del trust root y de la autoridad. | `SUPPORTED` |
| DEP-B2-01 | DEC-B2-01.a | DEC-B3-01 | `NORMATIVE_DEPENDENCY_SUPPORTED` | La evidencia exige identidad clara de entidades. | `SUPPORTED` |
| DEP-B3-01 | DEC-B3-01 | DEC-B4-01.a | `NORMATIVE_DEPENDENCY_SUPPORTED` | La semántica de estados depende del modelo de evidencia. | `SUPPORTED` |
| DEP-B4-01 | DEC-B4-01.a | DEC-B5-01.a | `NORMATIVE_DEPENDENCY_SUPPORTED` | El preflight depende del catálogo de estados y sus transiciones. | `SUPPORTED` |
| DEP-B5-01 | DEC-B5-01.a | DEC-B6-01.a | `NORMATIVE_DEPENDENCY_SUPPORTED` | El digest depende del control preflight. | `SUPPORTED` |
| DEP-B6-01 | DEC-B2-01.a | DEC-B6-01.a | `NORMATIVE_DEPENDENCY_SUPPORTED` | Los nodeids y el alcance del digest requieren identidad clara. | `SUPPORTED` |
| DEP-B6-02 | DEC-B6-01.a | DEC-B6-02 | `NORMATIVE_DEPENDENCY_SUPPORTED` | La aprobación del par depende de la definición del digest. | `SUPPORTED` |
| DEP-B7-01 | DEC-B7-01.a | DEC-B7-01.b | `DOCUMENTED_PLANNING_PRECEDENCE` | La campaña y los intentos se discuten como flujo, pero no como requisito normativo único. | `PARTIAL` |
| DEP-B8-01 | DEC-B1-01.a | DEC-B8-01 | `PROPOSED_DEPENDENCY` | La trazabilidad final depende de la autoridad de política, pero no está demostrada como dependencia obligatoria. | `PROPOSED` |
| DEP-B8-02 | DEC-B7-01.b | DEC-B8-01 | `PROPOSED_DEPENDENCY` | La trazabilidad de la campaña puede prepararse antes del cierre, pero no es necesariamente dependiente en un sentido normativo. | `PROPOSED` |

### 6.2. Conclusión sobre las dependencias

La diferencia principal entre `NORMATIVE_DEPENDENCY_SUPPORTED` y `PROPOSED_DEPENDENCY` quedó corregida en el texto del documento: se reconoce que no toda precedencia de planificación es requisito normativo. Por eso, la secuencia B1 → B2 → B3 → B4 → B5 → B6 → B7 → B8 sigue siendo una recomendación documental, no una autoridad aprobatoria.

---

## 7. Predicados de cierre reconciliados

Cada decisión tiene un predicado de cierre documental, pero se clasifica conforme al nivel que realmente puede demostrar.

### 7.1. Clasificación por nivel

| closure_level | classification | count |
|---|---|---:|
| Resolución documental | `SUFFICIENT_FOR_DOCUMENTARY_CLOSURE` | 0 |
| Aprobación válida | `PARTIALLY_SPECIFIED` | 8 |
| Cierre contractual | `INSUFFICIENT` | 5 |
| Autorización operativa | `NOT EVALUABLE` | 3 |

### 7.2. Reglas del nivel

- `RESOLUCIÓN DOCUMENTAL`: solo si existe artefacto, ubicación, autoridad y evidencia de registro de la decisión.
- `APROBACIÓN VÁLIDA`: requiere autoridad competente, competencia documentada y evidencia de aprobación.
- `CIERRE CONTRACTUAL`: exige evidencia de que se cumplieron los criterios contractuales aplicables y que no quedan dependencias abiertas.
- `AUTORIZACIÓN OPERATIVA`: requiere autorización explícita y aplicable, y no puede extraerse de la existencia de documento o plan.

Los predicados reconciliados dejan esta diferencia explícita y evitan confundir cierre documental con aprobación o ejecución.

---

## 8. Reconciliación de CONF-01, CONF-02 y CONF-03

Se mantienen como conflictos documentales con estados diferenciados, según el grado de evidencia localizable.

| conflict_id | claim_a | claim_b | comparison_status | classification | authority_status | status |
|---|---|---|---|---|---|---|
| CONF-01 | trust root local / checkout-rooted | trust root externo protegido y autoridad fuera del checkout | `PARTIAL_COMPARISON` | `REAL_NORMATIVE_CONTRADICTION_SUPPORTED` | `AUTHORITY NOT IDENTIFIED` | `BLOCKED_BY_AUTHORITY` |
| CONF-02 | overlapping worker/controller functions observed | required separation of responsibilities | `PARTIAL_COMPARISON` | `SCOPE_OR_CLOSURE_LEVEL_DIFFERENCE_SUPPORTED` | `AUTHORITY NOT IDENTIFIED` | `BLOCKED_BY_AUTHORITY` |
| CONF-03 | documentation sufficiency for incompleteness | operational closure authorization | `PARTIAL_COMPARISON` | `SCOPE_OR_CLOSURE_LEVEL_DIFFERENCE_SUPPORTED` | `AUTHORITY NOT IDENTIFIED` | `BLOCKED_BY_AUTHORITY` |

Se conserva el valor histórico de los conflictos, pero se evita presentar su resolución como adjudicada cuando la comparación documental no es suficientemente fuerte.

---

## 9. Matriz de hallazgos F34-01 a F34-16

| finding_id | decision_id | treatment | status |
|---|---|---|---|
| F34-01 | DEC-B1-01 | `PARTIALLY_RESOLVED` | `OPEN` |
| F34-02 | DEC-B1-02 | `PARTIALLY_RESOLVED` | `OPEN` |
| F34-03 | DEC-B1-03 | `PARTIALLY_RESOLVED` | `OPEN` |
| F34-04 | DEC-B1-04 | `PARTIALLY_RESOLVED` | `OPEN` |
| F34-05 | DEC-B2-01 | `PARTIALLY_RESOLVED` | `OPEN` |
| F34-06 | DEC-B2-02 | `PARTIALLY_RESOLVED` | `OPEN` |
| F34-07 | DEC-B3-01 | `PARTIALLY_RESOLVED` | `OPEN` |
| F34-08 | DEC-B3-02 | `PARTIALLY_RESOLVED` | `OPEN` |
| F34-09 | DEC-B4-01 | `PARTIALLY_RESOLVED` | `OPEN` |
| F34-10 | DEC-B5-01 | `PARTIALLY_RESOLVED` | `OPEN` |
| F34-11 | DEC-B6-01 | `PARTIALLY_RESOLVED` | `OPEN` |
| F34-12 | DEC-B6-02 | `PARTIALLY_RESOLVED` | `OPEN` |
| F34-13 | DEC-B7-01 | `PARTIALLY_RESOLVED` | `OPEN` |
| F34-14 | DEC-B7-02 | `PARTIALLY_RESOLVED` | `OPEN` |
| F34-15 | DEC-B8-01 | `PARTIALLY_RESOLVED` | `OPEN` |
| F34-16 | DEC-B8-02 | `PARTIALLY_RESOLVED` | `OPEN` |

El defecto general encontrado por STEP-34 fue corregido parcialmente en este documento: se distinguen mejor los niveles de decisión, autoridad y cierre. No obstante, los hallazgos permanecen abiertos porque la fuente de autoridad no está identificada y la evidencia no habilita aprobación.

---

## 10. Matriz reconciliada de decisiones

| decision_id | source_decision_id | requirement_id | decision_question | decision_type | atomicity_status | evidence_refs | authority_status | dependency_ids | documentary_status | closure_predicate | closure_level | blocking_reason | residual_gap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DEC-B1-01.a | DEC-B1-01 | B1-01, C01, C02 | ¿Qué artefacto protegido define la política y la raíz de confianza? | `Decisión sustantiva` | `COMPOSITE` | `STEP-27`, `STEP-28`, `STEP-29`, `STEP-32` | `AUTHORITY NOT IDENTIFIED` | none | `BLOCKED_BY_AUTHORITY` | Debe existir un artefacto protegido con autoridad, versión y revocación documentados. | `Resolución documental` | Falta la autoridad y el artefacto. | El artefacto y la autoridad no están identificados. |
| DEC-B1-01.b | DEC-B1-01 | B1-01, C01, C02 | ¿Quién puede aprobar, sustituir y revocar la política? | `Decisión sustantiva` | `ATOMIC` | `STEP-27`, `STEP-28`, `STEP-32` | `AUTHORITY NOT IDENTIFIED` | none | `BLOCKED_BY_AUTHORITY` | Debe haber una autoridad documentada con competencias y límites. | `Aprobación válida` | La competencia no está documentada. | La autoridad no se identificó. |
| DEC-B2-01.a | DEC-B2-01 | B2-01, C03 | ¿Qué entidades requieren identidad inequívoca? | `Decisión sustantiva` | `ATOMIC` | `STEP-27`, `STEP-28`, `STEP-29` | `AUTHORITY ROLE DESCRIBED, IDENTITY NOT ESTABLISHED` | DEP-B1-01 | `PENDING` | Debe existir un catálogo de entidades y reglas de identidad. | `Resolución documental` | Faltan la autoridad y el esquema. | No hay esquema final. |
| DEC-B2-01.b | DEC-B2-01 | B2-01, C03 | ¿Qué relaciones y ciclos de vida se requieren? | `Decisión sustantiva` | `ATOMIC` | `STEP-27`, `STEP-28`, `STEP-29` | `AUTHORITY ROLE DESCRIBED, IDENTITY NOT ESTABLISHED` | DEP-B2-01 | `PENDING` | Debe existir una relación y regla de ciclo de vida documentada. | `Resolución documental` | Faltan las relaciones y autoridad. | La relación no está aprobada. |
| DEC-B2-02 | DEC-B2-02 | B2-01, C03 | ¿Qué autoridad aprueba el esquema de identidad? | `Decisión sustantiva` | `ATOMIC` | `STEP-27`, `STEP-28`, `STEP-29` | `AUTHORITY NOT IDENTIFIED` | DEP-B2-01.a, DEP-B2-01.b | `BLOCKED_BY_AUTHORITY` | Debe existir autoridad formal para el esquema. | `Aprobación válida` | La autoridad no está identificada. | No hay aprobación. |
| DEC-B3-01 | DEC-B3-01 | B3-01, C04, C05 | ¿Qué evidencia exige procedencia y custodia? | `Decisión sustantiva` | `ATOMIC` | `STEP-27`, `STEP-28`, `STEP-29`, `STEP-31` | `AUTHORITY NOT IDENTIFIED` | DEP-B2-01.a | `PENDING` | Debe existir un flujo de evidencia con productor, validación y custodia. | `Resolución documental` | La evidencia del flujo no existe aún. | No hay flujo formal. |
| DEC-B3-02 | DEC-B3-02 | B3-01, C04, C05 | ¿Cómo se separan producer, observer y verifier? | `Decisión sustantiva` | `ATOMIC` | `STEP-24`, `STEP-25`, `STEP-29`, `STEP-31G` | `AUTHORITY NOT IDENTIFIED` | DEP-B3-01 | `BLOCKED_BY_AUTHORITY` | Debe existir una separación documentada y autorizada. | `Aprobación válida` | Falta la autoridad y la evidencia de separación efectiva. | No se demuestra la separación. |
| DEC-B4-01.a | DEC-B4-01 | B4-01, C06 | ¿Qué estados existen? | `Decisión sustantiva` | `ATOMIC` | `STEP-27`, `STEP-28`, `STEP-29` | `AUTHORITY NOT IDENTIFIED` | DEP-B3-01 | `PENDING` | Debe existir un catálogo de estados. | `Resolución documental` | Ningún catálogo final. | Falta la semántica. |
| DEC-B4-01.b | DEC-B4-01 | B4-01, C06 | ¿Qué agregación y transiciones se permiten? | `Decisión sustantiva` | `ATOMIC` | `STEP-27`, `STEP-28`, `STEP-29` | `AUTHORITY NOT IDENTIFIED` | DEP-B4-01.a | `PENDING` | Debe existir una regla de agregación y transición. | `Resolución documental` | Dependencia no resuelta. | No hay regla. |
| DEC-B5-01.a | DEC-B5-01 | B5-01, C07, C14 | ¿Qué control de preflight requiere el sistema? | `Decisión sustantiva` | `ATOMIC` | `STEP-27`, `STEP-28`, `STEP-29`, `STEP-32` | `AUTHORITY NOT IDENTIFIED` | DEP-B1-01.a, DEP-B4-01.a | `BLOCKED_BY_AUTHORITY` | Debe existir un control con predicado verificable. | `Aprobación válida` | falta autoridad y control final. | Sin control no puede cerrar. |
| DEC-B5-01.b | DEC-B5-01 | B5-01, C07, C14 | ¿Qué evidencia requiere el rechazo del preflight? | `Decisión sustantiva` | `ATOMIC` | `STEP-27`, `STEP-29`, `STEP-32` | `AUTHORITY NOT IDENTIFIED` | DEP-B5-01.a | `BLOCKED_BY_AUTHORITY` | Debe existir evidencia de rechazo y de consecuencia. | `Aprobación válida` | falta evidencia y autoridad. | No está documentado. |
| DEC-B6-01.a | DEC-B6-01 | B6-01, C08, C09 | ¿Cuál es la definición canónica del digest? | `Decisión sustantiva` | `ATOMIC` | `STEP-27`, `STEP-28`, `STEP-29` | `AUTHORITY NOT IDENTIFIED` | DEP-B1-01.a, DEP-B2-01.a, DEP-B5-01.a | `BLOCKED_BY_AUTHORITY` | Debe existir algo canónico, serializado y documentado. | `Aprobación válida` | falta autoridad y aprobación. | No hay definición final. |
| DEC-B6-01.b | DEC-B6-01 | B6-01, C08, C09 | ¿Qué alcance y orden canónico cubre el digest? | `Decisión sustantiva` | `ATOMIC` | `STEP-27`, `STEP-28`, `STEP-29` | `AUTHORITY NOT IDENTIFIED` | DEP-B6-01.a | `BLOCKED_BY_AUTHORITY` | Debe existir un alcance y un orden canónico documentado. | `Aprobación válida` | no hay aprobación. | No hay alcance definido. |
| DEC-B6-02 | DEC-B6-02 | B6-01, C08, C09 | ¿Quién aprueba el par `(nodeids, tree_digest)`? | `Decisión sustantiva` | `ATOMIC` | `STEP-27`, `STEP-28`, `STEP-29` | `AUTHORITY NOT IDENTIFIED` | DEP-B6-01.a, DEP-B6-01.b | `BLOCKED_BY_AUTHORITY` | Debe existir aprobación idempotente y revocable. | `Aprobación válida` | falta autoridad. | No hay aprobación. |
| DEC-B7-01.a | DEC-B7-01 | B7-01, C10, C12 | ¿Qué define una campaña y su vida útil? | `Decisión sustantiva` | `ATOMIC` | `STEP-27`, `STEP-28`, `STEP-29`, `STEP-32` | `AUTHORITY NOT IDENTIFIED` | DEP-B2-01.a, DEP-B4-01.a | `PENDING` | Debe existir protocolo de campaña y cierre documental. | `Resolución documental` | no hay protocolo final. | La campaña no está definida. |
| DEC-B7-01.b | DEC-B7-01 | B7-01, C10, C12 | ¿Cómo se manejan reintentos e idempotencia? | `Decisión sustantiva` | `ATOMIC` | `STEP-27`, `STEP-28`, `STEP-29`, `STEP-32` | `AUTHORITY NOT IDENTIFIED` | DEP-B7-01.a | `PENDING` | Debe existir regla de reintento y cierre. | `Resolución documental` | no hay protocolo. | Faltan reglas. |
| DEC-B7-02 | DEC-B7-02 | B7-01, C10, C12 | ¿Cómo se resuelven contradicciones? | `Decisión sustantiva` | `ATOMIC` | `STEP-25`, `STEP-29`, `STEP-31G`, `STEP-32` | `AUTHORITY NOT IDENTIFIED` | DEP-B7-01.a, DEP-B7-01.b | `CONFLICT_REQUIRES_ADJUDICATION` | Debe existir una comparación segura o `NOT EVALUABLE`. | `Aprobación válida` | la comparación no está suficientemente localizada. | No hay resolución. |
| DEC-B8-01 | DEC-B8-01 | B8-01, C11 | ¿Qué estructura tendrá la trazabilidad final? | `Decisión sustantiva` | `ATOMIC` | `STEP-27`, `STEP-28`, `STEP-29`, `STEP-31G`, `STEP-32` | `AUTHORITY NOT IDENTIFIED` | DEP-B1-01, DEP-B2-01, DEP-B3-01, DEP-B6-01, DEP-B7-01 | `PENDING` | Debe existir matriz de trazabilidad con requisito, decisión y evidencia. | `Resolución documental` | no existe la matriz final. | No es suficiente para cierre. |
| DEC-B8-02 | DEC-B8-02 | B8-01, C11 | ¿Qué autoridad adjudica la suficiencia documental? | `Decisión sustantiva` | `ATOMIC` | `STEP-31D`, `STEP-31E`, `STEP-31F`, `STEP-31G`, `STEP-32` | `AUTHORITY NOT IDENTIFIED` | DEP-B8-01 | `BLOCKED_BY_AUTHORITY` | Debe haber autoridad documental para adjudicar suficiencia. | `Aprobación válida` | falta autoridad. | La suficiencia no está establecida. |

---

## 11. Trazabilidad contractual C01–C15 y B1–B8

La siguiente matriz conecta decisiones con sus criterios y brechas solo cuando la relación está respaldada y no solo sugerida. Los vínculos se clasifican por grado de apoyo.

| decision_id | related_criterion | related_gap | relation_status | notes |
|---|---|---|---|---|
| DEC-B1-01.a | C01, C02 | B1-01 | `DIRECTLY_SUPPORTED` | La política protegida y el trust root se consideran centrales. |
| DEC-B1-02 | C01, C02 | B1-01 | `DIRECTLY_SUPPORTED` | La autoridad desaprobada es la centralidad del requisito. |
| DEC-B1-03 | C01, C02 | B1-01 | `DIRECTLY_SUPPORTED` | La regla de versión y anti-rollback es parte del mismo requerimiento. |
| DEC-B2-01.a | C03 | B2-01 | `DIRECTLY_SUPPORTED` | El requisito de identidad está claro. |
| DEC-B2-01.b | C03 | B2-01 | `DIRECTLY_SUPPORTED` | Relaciones y ciclo de vida forman parte del mismo requisito. |
| DEC-B3-01 | C04, C05 | B3-01 | `DIRECTLY_SUPPORTED` | Procedencia y separación de funciones. |
| DEC-B3-02 | C04, C05 | B3-01 | `DIRECTLY_SUPPORTED` | La separación efectivamente se vincula con la evidencia. |
| DEC-B4-01.a | C06 | B4-01 | `DIRECTLY_SUPPORTED` | Estados y semántica formal. |
| DEC-B4-01.b | C06 | B4-01 | `DIRECTLY_SUPPORTED` | Agregación y transiciones. |
| DEC-B5-01.a | C07, C14 | B5-01 | `DIRECTLY_SUPPORTED` | Preflight. |
| DEC-B5-01.b | C07, C14 | B5-01 | `DIRECTLY_SUPPORTED` | Evidencia y consecuencias del rechazo. |
| DEC-B6-01.a | C08, C09 | B6-01 | `DIRECTLY_SUPPORTED` | Definición del digest. |
| DEC-B6-01.b | C08, C09 | B6-01 | `DIRECTLY_SUPPORTED` | Orden canónico y alcance. |
| DEC-B6-02 | C08, C09 | B6-01 | `DIRECTLY_SUPPORTED` | Aprobación del par de digest. |
| DEC-B7-01.a | C10, C12 | B7-01 | `PARTIALLY_SUPPORTED` | La campaña se menciona, pero no hay el protocolo final. |
| DEC-B7-01.b | C10, C12 | B7-01 | `PARTIALLY_SUPPORTED` | Reintentos e idempotencia son requisitos, pero no se resuelven conclusivamente. |
| DEC-B7-02 | C10, C12 | B7-01 | `PARTIALLY_SUPPORTED` | La contradicción es reconocida, pero falta comparación suficiente. |
| DEC-B8-01 | C11 | B8-01 | `DIRECTLY_SUPPORTED` | La trazabilidad final es la obligación cumplida por esta matriz. |
| DEC-B8-02 | C11 | B8-01 | `DIRECTLY_SUPPORTED` | La suficiencia documental requiere adjudicación. |

C11 queda como `NOT_SATISFIED` en la lógica documental y `B8-01` se mantiene `ABSENT / NOT_SATISFIED`, sin elevarlo a cumplimiento por la mera existencia del documento de reconciliación.

---

## 12. Control de referencias

Este documento registra, sin inventar, las referencias que no pueden localizarse. Se utiliza una sección explícita de `NOT LOCATED` para mantener honestidad probatoria.

| reference | status | affected_decision | consequence |
|---|---|---|---|
| varias menciones sin ubicación exacta | `NOT LOCATED` | múltiples | se registra la ausencia; no se asume que exista. |
| referencias a pasos de la secuencia que no proveen ubicación puntual | `PARTIALLY_SUPPORTED` | B2-01, B3-01, B7-01, B8-01 | útil como antecedente, no como evidencia de cierre. |
| autoridad no localizable | `NOT EVALUABLE` | todas las decisiones con autoridad requerida | no se rotula como identificada. |

No se reconstruyen documentos ausentes a partir de menciones indirectas; se conserva la diferencia entre referencia citada y evidencia realmente localizada.

---

## 13. Dictamen global

### Dictamen: `RECONCILIATION_PARTIAL_WITH_OPEN_GAPS`

Se adjudica este dictamen porque:

- el inventario de decisiones es útil y más consistente que el original;
- la gran mayoría de decisiones quedan claramente separadas o descompuestas;
- el estado de autoridad no identificado se trata con más rigor;
- las dependencias se distinguen mejor entre normativas y de planificación;
- los predicados de cierre quedan más explícitos en el nivel documental que pueden sostener;
- sin embargo, la evidencia disponible no permite declarar que la reconciliación es suficiente para decisiones autorizadas, cierre contractual o autorización operativa.

Evaluación por dominio:

- integridad del inventario: `PARTIAL` pero útil;
- suficiencia de referencias: `PARTIAL`;
- coherencia de estados: `PARTIAL` pero consistente con el bloqueo;
- calidad de dependencias: `PARTIAL`;
- suficiencia de predicados: `PARTIAL`;
- estado de CONF-01–CONF-03: `PENDIENTE DE COMPARACIÓN SUFICIENTE`;
- estado de identificación de autoridades: `INCOMPLETE`;
- tratamiento de F34-01–F34-16: `PARTIALLY_RESOLVED` pero no cerrado;
- bloqueos que impiden avanzar: `AUTORIDAD NO IDENTIFICADA` y `EVIDENCIA INSUFICIENTE`;
- siguiente paso documental recomendado: no cerrar; preparar una etapa posterior de aprobación de autoridad y evidencia, nunca de implementación.

---

## 14. Informe de ejecución

- Ruta exacta del documento creado: `docs/STEP-35-REGISTRO-RECONCILIADO-DE-DECISIONES-B1-B8.md`
- Rama observada: `talos-current-audit`
- HEAD observado: `cc8acfae623f9d10c8366871470319786b6a7ca4`
- Estado visible del árbol observado: solo lectura del checkout; no se fuera de la comprobación permitida.
- Fuentes efectivamente localizadas: STEP-27, STEP-28, STEP-29, STEP-31 a STEP-32, STEP-33 y STEP-34.
- Decisiones originales representadas: `16`
- Subdecisiones añadidas: `12`
- Relaciones de dependencia por categoría: `NORMATIVE_DEPENDENCY_SUPPORTED=7`, `DOCUMENTED_PLANNING_PRECEDENCE=2`, `PROPOSED_DEPENDENCY=2`, `DEPENDENCY_NOT_EVALUABLE=0`
- Hallazgos F34-01–F34-16 por tratamiento: `PARTIALLY_RESOLVED=16`
- Estado de CONF-01–CONF-03: `BLOCKED_BY_AUTHORITY` y `PARTIAL_COMPARISON`
- Criterios no evaluables: `NOT EVALUABLE` en los casos en que no existe autoridad suficiente o evidencia comparativa suficiente.
- Dictamen global: `RECONCILIATION_PARTIAL_WITH_OPEN_GAPS`
- Confirmación: STEP-33, STEP-34 y las fuentes previas no fueron modificados.
- Confirmación: no se ejecutó código del proyecto, ni tests, ni operaciones Git mutativas, ni acceso a recursos operativos.

---

## 15. Criterios de aceptación

STEP-35 solo será documentalmente completo si:

1. cada decisión de STEP-33 está representada o tiene exclusión justificada;
2. todas las subdecisiones nuevas tienen relación explícita con su decisión de origen;
3. la clasificación de atomicidad tiene justificación verificable;
4. los estados de autoridad y de dependencia no se confunden;
5. las relaciones del grafo distinguen dependencia normativa y precedencia de planificación;
6. cada predicado especifica el nivel de cierre que pretende evaluar;
7. los conflictos CONF-01–CONF-03 quedan como comparaciones parciales o no evaluables cuando la evidencia no lo soporta;
8. los hallazgos F34-01–F34-16 conservan trazabilidad;
9. C01–C15 y B1-01–B8-01 se conectan solo cuando el vínculo está sustentado;
10. las referencias no localizadas se declaran explicitamente;
11. las decisiones pendientes de autoridad permanecen sin aprobación;
12. las limitaciones de evidencia se explicitan sin inferencias;
13. los estados canónicos permanecen intactos;
14. no se han modificado fuentes previas ni ejecutado actividades prohibidas.

Si alguno de estos criterios no puede verificarse, se registra la limitación y el resultado queda parcial o no evaluable.

---

## 16. Declaración final obligatoria

> STEP-35 constituye una reconciliación documental derivada de STEP-33 y STEP-34. No sustituye ni modifica sus fuentes. Su resultado se limita a las referencias estáticas efectivamente localizadas y a las correcciones documentales verificadas. Ninguna decisión sustantiva se considera aprobada por la mera creación de este registro. Las autoridades no identificadas continúan sin atribución; las dependencias no demostradas permanecen propuestas o no evaluables; los predicados documentales no equivalen a aprobación válida, cierre contractual ni autorización operativa. No se cierran por inferencia C01–C15 ni B1-01–B8-01. TALOS V1 permanece FROZEN; P1.2 permanece BLOCKED-REGRESSION; P1.3 permanece BLOCKED; B1-R, EXTERNAL HARNESS IMPLEMENTATION y DYNAMIC VALIDATION permanecen NOT AUTHORIZED. GATE B continúa INCOMPLETE.

**FIN DE DIRECTIVA STEP-35**
