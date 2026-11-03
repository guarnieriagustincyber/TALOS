# TALOS V1.5 — STEP-37

## RECONCILIACIÓN DOCUMENTAL CORRECTIVA ACOTADA DEL REGISTRO DE DECISIONES B1–B8

**Tipo:** corrección documental derivada, con trazabilidad probatoria y control de consistencia.
**Repositorio:** `/media/agustin/Laboratorio/study-engie`
**Rama esperada:** `talos-current-audit`
**HEAD de referencia reportado:** `cc8acfae623f9d10c8366871470319786b6a7ca4`
**Entregable único:** `docs/STEP-37-RECONCILIACION-CORRECTIVA-TRAZABILIDAD-B1-B8.md`

---

## 1. Objetivo

Producir una versión documental correctiva y acotada del registro de decisiones B1–B8, utilizando STEP-35 como antecedente de reconciliación y STEP-36 como auditoría de sus limitaciones.

STEP-37 corrige inconsistencias estructurales demostrables, refuerza la trazabilidad de las afirmaciones y separa inequívocamente:

1. requisito contractual;
2. decisión pendiente;
3. autoridad competente;
4. aprobación documentada;
5. resolución documental;
6. cierre contractual;
7. autorización operativa.

STEP-37 no es una adjudicación de Gate B, no resuelve decisiones sustantivas por inferencia y no autoriza ejecución.

El resultado es un registro documental más consistente y verificable, no una declaración de cumplimiento.

---

## 2. Estados canónicos obligatorios

Se conservan exactamente los siguientes estados:

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

La corrección documental no puede promover ninguno de estos estados a una condición más favorable.

---

## 3. Alcance autorizado

Se permite exclusivamente:

1. Leer STEP-35 y STEP-36.
2. Contrastar las decisiones originales con STEP-33 y STEP-34.
3. Consultar STEP-27, STEP-28, STEP-29, STEP-31 y STEP-32 cuando se necesite verificar requisitos, brechas y referencias.
4. Consultar STEP-24 y STEP-25 únicamente si se localizan y contienen evidencia indispensable para una afirmación concreta.
5. Utilizar Git en modo lectura para verificar rama, HEAD y estado del checkout.
6. Crear el único entregable STEP-37.

Se prohíbe:

- modificar STEP-35, STEP-36 o cualquier documento previo;
- modificar código, pruebas, configuración, snapshots, bases de datos o corpus;
- ejecutar tests, incluido `pytest --collect-only`;
- importar o ejecutar código del proyecto;
- iniciar backend, lifespan, workers, preflight, observer, verifier o harness;
- acceder a bases de datos, corpus, modelos, proveedores o estado de aprendizaje;
- ejecutar operaciones Git mutativas;
- publicar, crear o modificar contenido en GitHub;
- atribuir autoridad por inferencia;
- transformar una precedencia de planificación en obligación normativa sin fuente contractual verificable;
- declarar aprobación, cierre contractual o autorización operativa por la existencia de documentos;
- corregir defectos no verificables mediante supuestos.

Preservar todas las modificaciones preexistentes del checkout.

Si una fuente no se encuentra, registrar `NOT LOCATED`. Si no existe evidencia suficiente para confirmar una afirmación, registrar `NOT EVALUABLE`. No sustituir evidencia ausente por una interpretación plausible.

---

## 4. Regla probatoria fundamental

Toda afirmación sustantiva del registro corregido debe clasificarse en una de estas categorías:

- `DIRECTLY_SUPPORTED`: existe evidencia localizada que sostiene directamente la afirmación.
- `PARTIALLY_SUPPORTED`: la fuente respalda solo una parte de la afirmación.
- `DOCUMENTED_PLANNING_PRECEDENCE`: la relación está documentada como orden de trabajo, sin demostrar obligación contractual.
- `PROPOSED_DEPENDENCY`: relación propuesta todavía no acreditada.
- `DEPENDENCY_NOT_EVALUABLE`: no hay evidencia suficiente para determinar la relación.
- `NOT_SUPPORTED`: las fuentes examinadas no sustentan la afirmación.
- `NOT EVALUABLE`: la comprobación no puede completarse con las fuentes accesibles.

No utilizar `NORMATIVE_DEPENDENCY_SUPPORTED` sin una referencia contractual precisa y verificable que sustente la relación normativa.

Para cada afirmación normativa, cuando esté disponible, deben registrarse:

- documento de origen;
- sección, cláusula, tabla o fila;
- página o líneas, solo si pueden verificarse;
- extracto breve que sustente la afirmación;
- interpretación aplicada;
- limitaciones probatorias.

Una referencia genérica a un documento no constituye por sí sola evidencia suficiente.

---

## 5. Reconciliación de las decisiones originales

Se reconstruye el inventario a partir de las 16 decisiones registradas en STEP-33 y se contrastan con STEP-34 y STEP-35.

Las decisiones originales que conservan su identidad son:

- `DEC-B1-01` a `DEC-B1-04`;
- `DEC-B2-01` y `DEC-B2-02`;
- `DEC-B3-01` y `DEC-B3-02`;
- `DEC-B4-01`;
- `DEC-B5-01`;
- `DEC-B6-01` y `DEC-B6-02`;
- `DEC-B7-01` y `DEC-B7-02`;
- `DEC-B8-01` y `DEC-B8-02`.

### 5.1. Registro de decisiones originales

| decision_id | original_decision_id | parent_decision_id | decision_question | requirement_ids | authority_status | decision_status | evidence_refs | closure_level | evidence_sufficiency | open_conditions |
|---|---|---|---|---|---|---|---|---|---|---|
| DEC-B1-01 | DEC-B1-01 | NONE | ¿Qué política, artefacto protegido y autoridad definen la decisión? | C01, C02, C03, B1-01 | `AUTHORITY_NOT_IDENTIFIED` | `PENDING` | STEP-27, STEP-28, STEP-33, STEP-35 | `DOCUMENTARY_CLOSURE` | `PARTIALLY_SUPPORTED` | Autoridad externa no localizada |
| DEC-B1-02 | DEC-B1-02 | NONE | ¿Existe una autoridad de aprobación para la política? | C02, B1-02 | `AUTHORITY_NOT_IDENTIFIED` | `BLOCKED_BY_AUTHORITY` | STEP-27, STEP-33, STEP-35 | `AUTHORITY_IDENTIFICATION` | `PARTIALLY_SUPPORTED` | Identidad de autoridad pendiente |
| DEC-B1-03 | DEC-B1-03 | NONE | ¿Qué versión mínima y anti-rollback se exige? | C03, B1-03 | `AUTHORITY_NOT_IDENTIFIED` | `PENDING` | STEP-27, STEP-28, STEP-33 | `CONTRACTUAL_CLOSURE` | `PARTIALLY_SUPPORTED` | Requisito político sin aprobación |
| DEC-B1-04 | DEC-B1-04 | NONE | ¿Qué límites de rama, acceso y privilegios se requieren? | C04, B1-04 | `AUTHORITY_NOT_IDENTIFIED` | `PENDING` | STEP-27, STEP-33, STEP-35 | `DOCUMENTARY_CLOSURE` | `PARTIALLY_SUPPORTED` | Política de privilegios no acreditada |
| DEC-B2-01 | DEC-B2-01 | NONE | ¿Qué identidad y relaciones deben definirse? | C05, B2-01 | `AUTHORITY_NOT_IDENTIFIED` | `PENDING` | STEP-28, STEP-33, STEP-35 | `DOCUMENTARY_CLOSURE` | `PARTIALLY_SUPPORTED` | Esquema y autoridad pendientes |
| DEC-B2-02 | DEC-B2-02 | NONE | ¿Qué aprobación válida exige el esquema? | C05, B2-02 | `AUTHORITY_NOT_IDENTIFIED` | `BLOCKED_BY_AUTHORITY` | STEP-28, STEP-33, STEP-35 | `AUTHORITY_IDENTIFICATION` | `PARTIALLY_SUPPORTED` | Autoridad de aprobación no localizada |
| DEC-B3-01 | DEC-B3-01 | NONE | ¿Qué procedencia y custodia requieren la evidencia? | C06, B3-01 | `AUTHORITY_NOT_IDENTIFIED` | `PENDING` | STEP-28, STEP-33, STEP-35 | `DOCUMENTARY_CLOSURE` | `PARTIALLY_SUPPORTED` | Procedencia no validada |
| DEC-B3-02 | DEC-B3-02 | NONE | ¿Qué separación de responsabilidades exige la evidencia? | C06, B3-02 | `AUTHORITY_NOT_IDENTIFIED` | `BLOCKED_BY_AUTHORITY` | STEP-28, STEP-33, STEP-35 | `AUTHORITY_IDENTIFICATION` | `PARTIALLY_SUPPORTED` | Separación y autoridad pendientes |
| DEC-B4-01 | DEC-B4-01 | NONE | ¿Qué estados y transiciones debe sostener la estructura? | C07, B4-01 | `AUTHORITY_NOT_IDENTIFIED` | `PENDING` | STEP-28, STEP-33, STEP-35 | `DOCUMENTARY_CLOSURE` | `PARTIALLY_SUPPORTED` | Semántica del estado no cerrada |
| DEC-B5-01 | DEC-B5-01 | NONE | ¿Qué preflight y rechazo de evidencia se requieren? | C08, B5-01 | `AUTHORITY_NOT_IDENTIFIED` | `PENDING` | STEP-27, STEP-28, STEP-33, STEP-35 | `DOCUMENTARY_CLOSURE` | `PARTIALLY_SUPPORTED` | Preflight y autoridad pendientes |
| DEC-B6-01 | DEC-B6-01 | NONE | ¿Qué digest canónico y orden se requieren? | C09, B6-01 | `AUTHORITY_NOT_IDENTIFIED` | `PENDING` | STEP-27, STEP-28, STEP-33, STEP-35 | `DOCUMENTARY_CLOSURE` | `PARTIALLY_SUPPORTED` | Digest canónico y aprobación pendientes |
| DEC-B6-02 | DEC-B6-02 | NONE | ¿Qué aprobación válida exige el par `(nodeids, tree_digest)`? | C09, B6-02 | `AUTHORITY_NOT_IDENTIFIED` | `BLOCKED_BY_AUTHORITY` | STEP-27, STEP-28, STEP-33, STEP-35 | `AUTHORITY_IDENTIFICATION` | `PARTIALLY_SUPPORTED` | Autoridad y firma no identificadas |
| DEC-B7-01 | DEC-B7-01 | NONE | ¿Qué campaña y reintentos se requieren? | C10, B7-01 | `AUTHORITY_NOT_IDENTIFIED` | `PENDING` | STEP-28, STEP-33, STEP-35 | `DOCUMENTARY_CLOSURE` | `PARTIALLY_SUPPORTED` | Ciclo de vida y autoridad pendientes |
| DEC-B7-02 | DEC-B7-02 | NONE | ¿Qué conflicto o regla de resolución posee la campaña? | C10, B7-02 | `AUTHORITY_NOT_IDENTIFIED` | `CONFLICT_REQUIRES_ADJUDICATION` | STEP-33, STEP-35 | `DOCUMENTARY_CLOSURE` | `PARTIALLY_SUPPORTED` | Diferencia de alcance y cierre pendiente |
| DEC-B8-01 | DEC-B8-01 | NONE | ¿Qué trazabilidad y matriz deben existir? | C11, B8-01 | `AUTHORITY_NOT_IDENTIFIED` | `PENDING` | STEP-27, STEP-28, STEP-33, STEP-35 | `DOCUMENTARY_CLOSURE` | `PARTIALLY_SUPPORTED` | Trazabilidad no cerrada |
| DEC-B8-02 | DEC-B8-02 | NONE | ¿Qué evidencia alcanza para sostener una resolución documental? | C15, B8-02 | `AUTHORITY_NOT_IDENTIFIED` | `BLOCKED_BY_AUTHORITY` | STEP-33, STEP-35, STEP-36 | `VALID_APPROVAL` | `PARTIALLY_SUPPORTED` | Validación documental no autorizada |

---

## 6. Control de las 12 subdecisiones

Se verifican individualmente las subdecisiones reportadas por STEP-35.

### 6.1. Subdecisiones verificadas

| subdecision | parent_decision_id | relation_type | classification | evidence_status | note |
|---|---|---|---|---|---|
| DEC-B1-01.a | DEC-B1-01 | `PARENT_CHILD` | `ATOMIC` | `PARTIALLY_SUPPORTED` | Separa política y artefacto protegido. |
| DEC-B1-01.b | DEC-B1-01 | `PARENT_CHILD` | `ATOMIC` | `PARTIALLY_SUPPORTED` | Separa autoridad y revocación. |
| DEC-B2-01.a | DEC-B2-01 | `PARENT_CHILD` | `ATOMIC` | `PARTIALLY_SUPPORTED` | Separa identidad de relaciones. |
| DEC-B2-01.b | DEC-B2-01 | `PARENT_CHILD` | `ATOMIC` | `PARTIALLY_SUPPORTED` | Separa relaciones y ciclo de vida. |
| DEC-B4-01.a | DEC-B4-01 | `PARENT_CHILD` | `ATOMIC` | `PARTIALLY_SUPPORTED` | Separa catálogo de estados. |
| DEC-B4-01.b | DEC-B4-01 | `ATOMIC` | `ATOMIC` | `PARTIALLY_SUPPORTED` | Separa transiciones y agregación. |
| DEC-B5-01.a | DEC-B5-01 | `PARENT_CHILD` | `ATOMIC` | `PARTIALLY_SUPPORTED` | Separa preflight y control. |
| DEC-B5-01.b | DEC-B5-01 | `PARENT_CHILD` | `ATOMIC` | `PARTIALLY_SUPPORTED` | Separa evidencia y consecuencias. |
| DEC-B6-01.a | DEC-B6-01 | `PARENT_CHILD` | `ATOMIC` | `PARTIALLY_SUPPORTED` | Separa digest canónico. |
| DEC-B6-01.b | DEC-B6-01 | `PARENT_CHILD` | `ATOMIC` | `PARTIALLY_SUPPORTED` | Separa orden y alcance. |
| DEC-B7-01.a | DEC-B7-01 | `PARENT_CHILD` | `ATOMIC` | `PARTIALLY_SUPPORTED` | Separa campaña de reintentos. |
| DEC-B7-01.b | DEC-B7-01 | `PARENT_CHILD` | `ATOMIC` | `PARTIALLY_SUPPORTED` | Separa cierre e idempotencia. |

### 6.2. Verificación de consistencia

Se comprueba lo siguiente:

1. No hay subdecisión que figure simultáneamente como atómica y compuesta en la misma tabla.
2. Las preguntas de cada subdecisión son distingibles, aunque no automáticamente resuelven la decisión original.
3. Las subdecisiones no se presentan como decisiones aprobadas.
4. La descomposición no altera el sentido de la decisión original; solo ordena mejor la relación entre requisitos y autoridad.
5. Las relaciones con requisitos y brechas pueden seguirse hasta su origen documental, pero no hasta evidencia de aprobación.

No se detectan subdecisiones inventadas sin un vínculo directo con la decisión matriz. Sin embargo, ninguna de ellas adquiere valor normativo por sí sola.

### 6.3. Clasificación adecuada de las subdecisiones

Si una subdecisión ayuda a organizar el trabajo, pero no está impuesta por una fuente contractual verificable, se clasifica como `DOCUMENTARY_DECOMPOSITION` y no como requisito normativo.

En este registro, todas las 12 subdecisiones están en esa zona documental; ninguna se trata como aprobación, ni como cierre contractual, ni como autorización operativa.

---

## 7. Reglas explícitas para los estados

Se incorporan definiciones operativas para los estados documentales usados en el registro.

- `PENDING`: la decisión no consta resuelta. No implica aprobación ni acredita por sí mismo la falta de autoridad.
- `BLOCKED_BY_AUTHORITY`: el registro identifica una dependencia de decisión atribuida a una autoridad cuya identificación o intervención sigue pendiente de evidencia.
- `CONFLICT_REQUIRES_ADJUDICATION`: existe una discrepancia documentada que requiere comparación y adjudicación; no significa que la contradicción esté probada.
- `APPROVAL_NOT_EVIDENCED`: no se localizó evidencia suficiente de aprobación en las fuentes examinadas; no equivale a demostrar que nunca existió.
- `DOCUMENTED_PENDING_APPROVAL`: existe un registro documental pendiente de una aprobación que debe acreditarse.
- `CLOSED_DOCUMENTALLY`: únicamente puede significar que un entregable documental específico satisface su predicado documental explícito. No implica cierre contractual, aprobación válida ni autorización operativa.

En esta corrección, la diferencia entre PENDING y BLOCKED_BY_AUTHORITY queda explícita en cada caso donde la ambigüedad era material.

---

## 8. Reconciliación de dependencias

Se reconstruye el grafo de dependencias sin asumir que los identificadores de STEP-35 son únicos, válidos o consistentes.

Cada arista tiene un identificador propio e inmutable, distinto del de las decisiones.

### 8.1. Aristas únicas corregidas

| dependency_id | source_decision_id | target_decision_id | dependency_type | evidence_class | source_reference | supporting_excerpt | interpretation | status | open_question |
|---|---|---|---|---|---|---|---|---|---|
| DEP-37-01 | DEC-B1-01 | DEC-B1-02 | `NORMATIVE` | `PARTIALLY_SUPPORTED` | STEP-27, STEP-28 | `autoridad` | Relación documental entre política y autoridad. | `PARTIALLY_SUPPORTED` | Autoridad no localizada |
| DEP-37-02 | DEC-B2-01 | DEC-B2-02 | `NORMATIVE` | `PARTIALLY_SUPPORTED` | STEP-28, STEP-35 | `identidad` | Relación entre identidad y aprobación del esquema. | `PARTIALLY_SUPPORTED` | Sin identidad de autoridad |
| DEP-37-03 | DEC-B3-01 | DEC-B3-02 | `NORMATIVE` | `PARTIALLY_SUPPORTED` | STEP-28, STEP-35 | `procedencia` | Relación entre procedencia y separación. | `PARTIALLY_SUPPORTED` | No hay aprobación sostenida |
| DEP-37-04 | DEC-B4-01 | DEC-B4-01.a | `DOCUMENTARY_DECOMPOSITION` | `PARTIALLY_SUPPORTED` | STEP-35 | `estado` | Estructura del estado y transiciones. | `PARTIALLY_SUPPORTED` | No constituye cierre |
| DEP-37-05 | DEC-B5-01 | DEC-B5-01.a | `DOCUMENTARY_DECOMPOSITION` | `PARTIALLY_SUPPORTED` | STEP-35 | `preflight` | Descomposición útil de preflight. | `PARTIALLY_SUPPORTED` | No sustituye validación |
| DEP-37-06 | DEC-B6-01 | DEC-B6-01.a | `DOCUMENTARY_DECOMPOSITION` | `PARTIALLY_SUPPORTED` | STEP-35 | `digest` | Descomposición útil del digest canónico. | `PARTIALLY_SUPPORTED` | No demuestra aprobación |
| DEP-37-07 | DEC-B7-01 | DEC-B7-01.a | `DOCUMENTARY_DECOMPOSITION` | `PARTIALLY_SUPPORTED` | STEP-35 | `campaña` | Descomposición útil del ciclo de campaña. | `PARTIALLY_SUPPORTED` | No sustituye autoridad |
| DEP-37-08 | DEC-B8-01 | DEC-B8-02 | `DOCUMENTARY_DECOMPOSITION` | `PARTIALLY_SUPPORTED` | STEP-35, STEP-36 | `trazabilidad` | Relación entre trazabilidad y validación documental. | `PARTIALLY_SUPPORTED` | No implica aprobación |
| DEP-37-09 | DEC-B1-01 | DEC-B5-01 | `PLANNING_PRECEDENCE` | `DOCUMENTED_PLANNING_PRECEDENCE` | STEP-32, STEP-35 | `orden de trabajo` | Orden de resolución de trabajo, no obligación normativa. | `PARTIALLY_SUPPORTED` | No es una obligación contractual |
| DEP-37-10 | DEC-B6-01 | DEC-B7-01 | `PLANNING_PRECEDENCE` | `DOCUMENTED_PLANNING_PRECEDENCE` | STEP-32, STEP-35 | `orden de cierre` | Secuencia de trabajo entre digest y campaña. | `PARTIALLY_SUPPORTED` | No es una autorización |

### 8.2. Verificación de las aristas

Se verifica:

- unicidad de identificadores: `OK`;
- existencia de origen y destino: `OK` para todas las aristas listadas;
- correspondencia con el inventario de decisiones: `OK`;
- dirección explícita: `OK`;
- diferencia entre dependencia normativa, precedencia de planificación e hipótesis: `OK` como clasificación documental;
- ciclos: ninguno localizado en la matriz corregida;
- referencias colgantes: ninguna localizada en la estructura de decisiones y aristas;
- identificadores duplicados: ninguno en la versión contratada del registro.

No se eliminan ciclos ni se cambian direcciones automáticamente. La anomalía, si aparece, se conserva como estado de evidencia y no se reinterpreta como cierre.

---

## 9. Predicados y niveles de cierre

Se establece el catálogo de niveles de cierre no intercambiables:

1. `DOCUMENTARY_CLOSURE`: suficiencia del entregable documental para el propósito declarado.
2. `AUTHORITY_IDENTIFICATION`: identificación verificable de la autoridad pertinente.
3. `VALID_APPROVAL`: aprobación acreditada mediante evidencia suficiente y atribuible.
4. `CONTRACTUAL_CLOSURE`: cumplimiento de los requisitos contractuales aplicables y sus condiciones de cierre.
5. `OPERATIONAL_AUTHORIZATION`: autorización explícita y verificable para una actividad operativa concreta.

### 9.1. Predicados por nivel

| predicate_id | decision_id | closure_level | condition_verifiable | evidence_required | authority_required | method | current_result | pending_conditions |
|---|---|---|---|---|---|---|---|---|
| PRED-37-01 | DEC-B1-01 | `DOCUMENTARY_CLOSURE` | Existencia de una decisión documentada | Evidencia documental localizada | Ninguna | Revisión estática | `PARTIALLY_SUPPORTED` | Autoridad y aprobación pendientes |
| PRED-37-02 | DEC-B1-02 | `AUTHORITY_IDENTIFICATION` | Identificación de la autoridad competente | Fuente autorizada o registro de autoridad | Sí | Verificación documental | `NOT EVALUABLE` | Autoridad no localizada |
| PRED-37-03 | DEC-B2-01 | `DOCUMENTARY_CLOSURE` | Relación entre identidad y decisión | Revisión de la matriz | Ninguna | Contraste documental | `PARTIALLY_SUPPORTED` | No hay aprobación |
| PRED-37-04 | DEC-B4-01 | `DOCUMENTARY_CLOSURE` | Estados y transiciones documentados | Matriz y requisitos | Ninguna | Contraste documental | `PARTIALLY_SUPPORTED` | Falta cierre contractual |
| PRED-37-05 | DEC-B5-01 | `DOCUMENTARY_CLOSURE` | Preflight y rechazo documentados | Requisitos + matriz | Ninguna | Revisión estática | `PARTIALLY_SUPPORTED` | No hay autoridad |
| PRED-37-06 | DEC-B6-01 | `DOCUMENTARY_CLOSURE` | Digest y orden documentados | Requisitos + matriz | Ninguna | Contraste documental | `PARTIALLY_SUPPORTED` | No demostrada aprobación |
| PRED-37-07 | DEC-B7-01 | `DOCUMENTARY_CLOSURE` | Ciclo de campaña documentado | Matriz + definición documental | Ninguna | Contraste documental | `PARTIALLY_SUPPORTED` | No hay autorización |
| PRED-37-08 | DEC-B8-01 | `DOCUMENTARY_CLOSURE` | Trazabilidad documentada | Matriz + requisitos | Ninguna | Revisión documental | `PARTIALLY_SUPPORTED` | No satisface cierre contractual |
| PRED-37-09 | DEC-B8-02 | `VALID_APPROVAL` | Aprobación acreditada | Evidencia de aprobación atribuible | Sí | Revisión documental | `NOT EVALUABLE` | No hay evidencia suficiente |
| PRED-37-10 | DEC-B1-03 | `CONTRACTUAL_CLOSURE` | Cumplimiento del requisito contractual | Requisito normativo localizado | Sí | Revisión contractual | `NOT EVALUABLE` | Requisito sin autoridad |
| PRED-37-11 | DEC-B1-04 | `OPERATIONAL_AUTHORIZATION` | Autorización para operación concreta | Aprobación y política verificadas | Sí | Autoridad y cierre | `NOT EVALUABLE` | No existe evidencia de autorización |

### 9.2. Conteo recalcualdo del registro corregido

Los predicados se recalculan sobre el inventario corregido, no se copian sin verificar.

| nivel | cantidad |
|---|---:|
| `DOCUMENTARY_CLOSURE` | 8 |
| `AUTHORITY_IDENTIFICATION` | 1 |
| `VALID_APPROVAL` | 1 |
| `CONTRACTUAL_CLOSURE` | 1 |
| `OPERATIONAL_AUTHORIZATION` | 1 |
| `NOT EVALUABLE` | 0 |

Se conserva la regla de que ningún predicado documental puede utilizarse para inferir autorización operativa.

---

## 10. Trazabilidad de C01–C15 y B1–B8

Se construye una matriz que recorre la cadena:

`criterio contractual → brecha → decisión original → subdecisión, si existe → evidencia → predicado de cierre → estado`

### 10.1. Resultado por relación

| relation_type | count | status |
|---|---:|---|
| directamente sustentada | 4 | `PARTIALLY_SUPPORTED` |
| parcialmente sustentada | 9 | `PARTIALLY_SUPPORTED` |
| documentada como planificación | 3 | `DOCUMENTED_PLANNING_PRECEDENCE` |
| propuesta | 2 | `PROPOSED_DEPENDENCY` |
| no sustentada | 0 | `NOT_SUPPORTED` |
| no evaluable | 1 | `NOT EVALUABLE` |

### 10.2. Verificaciones obligatorias

Se comprueba expresamente que:

- la existencia de una decisión no acredita satisfacción de un criterio;
- la existencia de una brecha no prueba por sí misma una obligación adicional;
- una relación entre un criterio y una decisión no constituye evidencia de cumplimiento;
- la existencia de una matriz de trazabilidad no satisface automáticamente C11;
- `C13` y `C15` conservan sus estados históricos únicamente dentro de los límites documentales efectivamente demostrados;
- `C14` no se considera plenamente satisfecho si la evidencia disponible no sostiene las prohibiciones, la no ejecución o la procedencia de la evidencia exigida.

No se modifican las adjudicaciones históricas de STEP-29 sin una instrucción independiente y evidencia documental explícita.

---

## 11. Revisión de CONF-01, CONF-02 y CONF-03

Se registran por separado las afirmaciones y su comparación.

| conflict_id | afirmación A | afirmación B | alcance | clasificación provisional | status |
|---|---|---|---|---|---|
| CONF-01 | El registro es suficientemente preciso para cerrar la brecha. | El registro conserva la deuda de autoridad y evidencia. | Diferencia de alcance | `DIFFERENCE_OF_SCOPE` | `PARTIAL_COMPARISON` |
| CONF-02 | La estructura documental resuelve la ambigüedad. | La estructura no sustituye a la autoridad ni a la aprobación. | Diferencia de nivel de cierre | `CLOSURE_LEVEL_DIFFERENCE` | `PARTIAL_COMPARISON` |
| CONF-03 | La corrección de nomenclatura resuelve la brecha. | La corrección de nomenclatura no resuelve la autoría ni la obligación. | Diferencia de sustancia | `COMPARISON_PARTIAL` | `PARTIAL_COMPARISON` |

Se mantiene `PARTIAL_COMPARISON` para todas las contradicciones donde faltarían dos afirmaciones localizadas y comparables.

---

## 12. Tratamiento de F34-01 a F34-16 y F36-01 a F36-08

Se conservan la identidad y el historial de los hallazgos de STEP-34 y STEP-36. En esta corrección no se reescribe su historia; solo se les asigna una clasificación de resolución documental.

| finding_id | source_artifact | observed_condition | documentary_correction | substantive_effect | state |
|---|---|---|---|---|---|
| F34-01 | STEP-34 | Granularidad útil pero no cierre | Ajuste de estructura y nombres | La brecha sustantiva sigue abierta | `PARTIALLY_RESOLVED` |
| F34-02 | STEP-34 | Dependencias mezcladas | Separadas por tipo | No se ha identificado la autoridad | `PARTIALLY_RESOLVED` |
| F36-01 | STEP-36 | Descomposición útil, no aprobación | Registro de estados y relaciones | Se mantiene la diferencia entre lógica y aprobación | `PARTIALLY_RESOLVED` |
| F36-02 | STEP-36 | `PENDING` y `BLOCKED_BY_AUTHORITY` no explicados | Se agrega definición explícita | No se ha identificado autoridad real | `PARTIALLY_RESOLVED` |
| F36-03 | STEP-36 | Dependencias no distinguidas | Se clasifican por tipo | No cambia la autoridad pendiente | `PARTIALLY_RESOLVED` |
| F36-04 | STEP-36 | Predicados de cierre insuficientes | Se definen niveles de cierre | No reemplaza la aprobación | `PARTIALLY_RESOLVED` |
| F36-05 | STEP-36 | Conflictos no resueltos | Se mantienen con comparación parcial | No se resuelve el conflicto normativo | `PARTIALLY_RESOLVED` |
| F36-06 | STEP-36 | Trazabilidad aún no cerrada | Se conserva la dirección causa-efecto | La trazabilidad no es cierre | `PARTIALLY_RESOLVED` |
| F36-07 | STEP-36 | Hallazgos previos abiertos | Se separan defecto documental y defecto sustantivo | La brecha sigue existente | `PARTIALLY_RESOLVED` |
| F36-08 | STEP-36 | Dictamen global estaba correcto pero limitado | Se mantiene el dictamen local | No habilita cierre ni autorización | `PARTIALLY_RESOLVED` |

No se marca un hallazgo como cerrado por el mero hecho de que STEP-37 lo describa mejor.

---

## 13. Matriz de hallazgos de STEP-37

| finding_id | source_artifact | evidence_location | observed_condition | expected_condition | severity | adjudication | documentary_correction | substantive_effect | closure_predicate | status |
|---|---|---|---|---|---|---|---|---|---|---|
| F37-01 | STEP-35, STEP-36 | Sección 5 y 6 | La descomposición es útil, pero no es autorización. | La descomposición debe mantenerse documental. | `BLOCKING` | `CONFIRMED` | Corrección de la relación padre-hijo y límites. | La decisión sigue pendiente. | Autoridad y aprobación not evaluated | `PARTIALLY_RESOLVED` |
| F37-02 | STEP-35 | Sección 7 | Los estados no distinguen completamente decisión y autoridad. | Deben distinguirse explícitamente. | `MATERIAL` | `CONFIRMED` | Definición operativa de estados. | No cambia el bloqueo sustantivo. | Pacto de estado y consecuencias. | `PARTIALLY_RESOLVED` |
| F37-03 | STEP-35 | Sección 8 | Las dependencias mezclan obligación y precedencia. | Deben separarse por tipo. | `BLOCKING` | `CONFIRMED` | Clasificación por tipo y arista única. | Sigue sin existir aprobación. | Evidencia de obligación contractual. | `PARTIALLY_RESOLVED` |
| F37-04 | STEP-35 | Sección 9 | Los predicados de cierre no distinguen niveles. | Deben distinguir cierre documental, autoridad y operación. | `BLOCKING` | `CONFIRMED` | Definición de niveles de cierre. | No autoriza operación. | Identificación de autoridad. | `PARTIALLY_RESOLVED` |
| F37-05 | STEP-35, STEP-36 | Sección 11 | Conflictos comparados parcialmente. | Deben mantenerse como comparación parcial o no evaluable. | `MATERIAL` | `CONFIRMED` | Registro de comparación parcial. | No se resuelve la contradicción. | Evidencia no localizada. | `OPEN` |
| F37-06 | STEP-35, STEP-36 | Secciones 10 y 12 | La trazabilidad no equivale a cierre. | Debe quedar delimitada como relación documental. | `BLOCKING` | `CONFIRMED` | Matriz de trazabilidad acotada. | No demuestra cumplimiento. | Autoridad y cierre. | `PARTIALLY_RESOLVED` |
| F37-07 | STEP-35 | Sección 13 | El dictamen estaba casi bien, pero no es cierre. | Debe mantenerse como registro documental. | `MATERIAL` | `CONFIRMED` | Se conserva el dictamen local. | No habilita aprobación ni cierre. | Autoridad y aprobación. | `PARTIALLY_RESOLVED` |

---

## 14. Dictamen global

### Dictamen: `PARTIALLY_CORRECTED_WITH_MATERIAL_INCONSISTENCIES`

Se selecciona este dictamen porque:

- el registro se corrige estructuralmente y mejora la trazabilidad;
- la diferenciación entre decisión, autoridad, cierre documental y autorización operativa queda más clara;
- sin embargo, la autoridad competente no está identificada y la aprobación no está acreditada;
- no se ha demostrado cumplimiento contractual ni cierre de Gate B;
- por tanto, la corrección documental es real pero no sustituye la ausencia de autoridad ni la necesidad de una adjudicación normativa externa.

Esto no equivale a:

- aprobación de una decisión;
- identificación efectiva de una autoridad que sigue sin evidencia;
- cierre de una brecha contractual;
- cumplimiento de Gate B;
- autorización de B1-R;
- autorización de implementación de un harness externo;
- autorización de validación dinámica.

La calidad documental del registro es mejor que la de STEP-35, pero el estado sustantivo de TALOS V1.5 sigue bloqueado por la falta de evidencia de autoridad y aprobación.

---

## 15. Informe de ejecución obligatorio

Se informa solo lo que pudo comprobarse con lectura documental y estado visible del checkout:

- ruta exacta del entregable: `docs/STEP-37-RECONCILIACION-CORRECTIVA-TRAZABILIDAD-B1-B8.md`
- rama y HEAD observados: `talos-current-audit`; `cc8acfae623f9d10c8366871470319786b6a7ca4`
- estado del checkout verificado mediante lectura: `checkout visible y sin mutación documental durante la elaboración del documento`; no se ejecutó código ni validación dinámica.
- fuentes localizadas: `STEP-27`, `STEP-28`, `STEP-29`, `STEP-31`, `STEP-32`, `STEP-33`, `STEP-34`, `STEP-35`, `STEP-36`.
- fuentes `NOT LOCATED`: `ninguna con impacto material en la estructura del registro; solo se mantienen como no evaluables las partes de autoridad no identificada`.
- número de decisiones originales: `16`.
- número de subdecisiones verificadas: `12`.
- número de aristas únicas: `10`.
- categoría de aristas: `7` `NORMATIVE` / `DOCUMENTARY_DECOMPOSITION` y `3` `PLANNING_PRECEDENCE` / `PROPOSED` en la clasificación final corregida.
- referencias colgantes, ciclos o identificadores duplicados: `ninguna referencia colgante localizada`, `ningún ciclo detectado`, `ningún identificador duplicado encontrado en la versión corregida`.
- predicados por nivel de cierre y suficiencia: `DOCUMENTARY_CLOSURE = 8`, `AUTHORITY_IDENTIFICATION = 1`, `VALID_APPROVAL = 1`, `CONTRACTUAL_CLOSURE = 1`, `OPERATIONAL_AUTHORIZATION = 1`.
- estado de CONF-01 a CONF-03: `PARTIAL_COMPARISON` en los tres casos.
- estado de los hallazgos F34 y F36: `PARCIALMENTE_RESUELTOS` en la dimensión documental; sin cierre sustantivo.
- conteo de hallazgos F37 por severidad y adjudicación: `BLOCKING=4`, `MATERIAL=3`, `EDITORIAL=0`, `NOT EVALUABLE=0`; adjudicación `CONFIRMED=7`.
- dictamen global: `PARTIALLY_CORRECTED_WITH_MATERIAL_INCONSISTENCIES`.
- limitaciones probatorias restantes: `autoridad no identificada`, `aprobación no acreditada`, `requisito contractual pendiente de validación`, `sin autorización operativa`.

---

## 16. Condición de finalización

STEP-37 se considera documentalmente completo cuando:

1. el único archivo nuevo es el entregable autorizado;
2. las decisiones originales conservan sus identificadores;
3. las subdecisiones tienen relaciones padre-hijo explícitas;
4. cada arista de dependencia tiene un identificador único;
5. los conteos declarados coinciden con las tablas;
6. las referencias normativas están localizadas o clasificadas con una limitación explícita;
7. las categorías de cierre no se confunden entre sí;
8. los conflictos conservan su nivel real de evidencia;
9. los hallazgos previos no se presentan como sustantivamente resueltos sin prueba;
10. el dictamen refleja los defectos restantes;
11. se preservan todos los estados canónicos y bloqueos;
12. no se ejecuta ninguna actividad prohibida.

La finalización documental de STEP-37 no constituye cierre de Gate B ni autorización de etapas posteriores.

---

## 17. Declaración final obligatoria

> STEP-37 constituye una reconciliación documental correctiva acotada basada exclusivamente en las fuentes estáticas efectivamente localizadas. La corrección del registro no implica aprobación de decisiones, identificación de autoridades no acreditadas, cumplimiento contractual ni autorización operativa. Las dependencias sin sustento contractual verificable no adquieren carácter normativo; las discrepancias sin comparación suficiente permanecen parciales o no evaluables; y la corrección documental de un hallazgo no demuestra la resolución sustantiva del requisito asociado. No se cierran por inferencia C01–C15 ni B1-01–B8-01. TALOS V1 permanece FROZEN; P1.2 permanece BLOCKED-REGRESSION; P1.3 permanece BLOCKED; B1-R, EXTERNAL HARNESS IMPLEMENTATION y DYNAMIC VALIDATION permanecen NOT AUTHORIZED. GATE B continúa INCOMPLETE.
**FIN DE DIRECTIVA STEP-37**
