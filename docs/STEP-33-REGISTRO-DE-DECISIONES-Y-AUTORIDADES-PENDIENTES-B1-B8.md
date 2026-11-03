# TALOS V1.5 — STEP-33

## REGISTRO FORMAL DE DECISIONES CONTRACTUALES PENDIENTES Y ADJUDICACIÓN DE AUTORIDADES B1–B8

**Tipo:** planificación y registro documental estático.
**Repositorio observado:** `/media/agustin/Laboratorio/study-engie`
**Rama observada:** `talos-current-audit`
**HEAD observado:** `cc8acfae623f9d10c8366871470319786b6a7ca4`
**Entregable único:** `docs/STEP-33-REGISTRO-DE-DECISIONES-Y-AUTORIDADES-PENDIENTES-B1-B8.md`

---

## 1. Objetivo

STEP-32 organizó las brechas B1-01 a B8-01 y propuso un orden de resolución. STEP-33 no repite la secuencia general ni re-audita la cadena documental completa. Con este documento se registra un conjunto de decisiones atómicas pendientes y se anota, para cada una, qué requisito contractual la exige, qué autoridad requiere, qué estado tiene y qué predicado de cierre sería necesario.

La intención es convertir la brecha general en decisiones individuales, ordenadas, discriminadas y expresadas con base documental. No se aprueban decisiones, no se nombra autoridad por inferencia, no se cierran brechas y no se autoriza implementación ni validación dinámica.

---

## 2. Estados canónicos de partida

Se mantienen sin alteración:

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

Estos valores se usan como estado de partida documental, no como certificación independiente del repositorio.

---

## 3. Alcance autorizado

Se permite exclusivamente:

1. inspeccionar mediante lectura estática los documentos STEP-27, STEP-28, STEP-29, STEP-31, STEP-31B, STEP-31C, STEP-31D, STEP-31E, STEP-31F, STEP-31G y STEP-32;
2. ejecutar únicamente comandos Git de lectura para observar la identidad del checkout y el estado del árbol;
3. extraer desde la documentación ya existente la estructura de decisiones pendientes, dependencias y autoridad requerida;
4. registrar decisiones atómicas, dependencias, autoridad no identificada, evidencias futuras y predicados de resolución;
5. crear únicamente el entregable STEP-33.

No se permite:

- ejecutar tests ni `pytest --collect-only`;
- ejecutar o importar código del proyecto;
- iniciar aplicaciones, workers, observers, verifiers, harnesses o preflight;
- acceder a bases de datos, corpus, modelos, proveedores o estado de aprendizaje;
- modificar código, tests, configuración, snapshots, bases de datos, corpus o documentos previos;
- ejecutar operaciones Git mutativas;
- publicar en GitHub;
- implementar contratos o convertir propuestas en decisiones aprobadas;
- identificar autoridades a partir de nombres de archivos, roles supuestos o inferencias;
- cerrar brechas o conceder autorizaciones.

Cuando una fuente o autoridad no puede verificarse, se registra como `NOT EVALUABLE`, `NOT LOCATED` o `AUTHORITY NOT IDENTIFIED`.

---

## 4. Metodología

Se usa una regla de descomposición atómica:

- una brecha general se convierte en varias decisiones accionables, cada una con un problema concreto;
- cada decisión conserva el vínculo con su brecha, sus criterios y su fundamentación documental;
- la necesidad de una decisión debe estar respaldada por requisito contractual u observación documental del flujo de autoridad;
- la ausencia de autoridad no se reemplaza por un nombre ni por una suposición de competencia;
- la aprobación documental no equivale a autorización operativa.

---

## 5. Registro central de decisiones atómicas

La siguiente tabla contiene una fila por decisión atómica. El identificador usa el formato `DEC-Bn-XX`, donde `n` identifica la brecha B1–B8 y `XX` es un número secuencial de dos dígitos.

| decision_id | gap_id | criterion_ids | decision_question | requirement_basis | source_document | source_location | source_evidence | authority_required | authority_identification_status | authority_basis | dependencies | options_status | decision_status | future_artifact | future_evidence | closure_predicate | authorization_boundary |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DEC-B1-01 | B1-01 | C01, C02 | ¿Cuál es la raíz de confianza y el artefacto protegido que define la política de la campaña? | La política protegida, trust root y anti-rollback no están establecidos como autoridad documental. | STEP-27, STEP-28, STEP-29, STEP-31G, STEP-32 | `NOT LOCATED` en la documentación actual | Los documentos describen la necesidad de una política protegida, but no se localiza la autoridad ni el artefacto final. | Función: autoridad de política y trust root. | `AUTHORITY NOT IDENTIFIED` | No existe base documental suficiente para nombrar la autoridad. | None | `OPTIONS_INCOMPLETE` | `BLOCKED_BY_AUTHORITY` | Política protegida, cláusula de autoridad y reglas de aprobación/revocación. | Artefacto protegido, autoridad identificada, versión mínima y regla de revocación. | Debe existir un artefacto protegido con autoridad, versión mínima, condiciones de aprobación y revocación documentadas. | No aprobar ni desplegar ninguna política ni trust root. |
| DEC-B1-02 | B1-01 | C01, C02 | ¿Quién puede aprobar, sustituir y revocar la política protegida? | La necesidad de autoridad para la política aparece como requisito, pero no queda identificado el órgano o rol competente. | STEP-27, STEP-28, STEP-29, STEP-31G, STEP-32 | `NOT LOCATED` | Los documentos exigen una autoridad, pero no la documentan. | Función: autoridad aprobadora de la política. | `AUTHORITY NOT IDENTIFIED` | Ausencia explícita de identificación documental. | DEC-B1-01 | `OPTIONS_INCOMPLETE` | `BLOCKED_BY_AUTHORITY` | Registro formal de decisiones de política. | Decisión formal de aprobación/revocación con competencia y límites definidos. | Debe existir un órgano o rol con competencia documentada para aprobar o revocar la política. | No se asume competencia por la mera presencia del documento. |
| DEC-B1-03 | B1-01 | C01, C02 | ¿Cuál es la versión mínima aceptada y cómo se impide el anti-rollback? | La política debe tener versión mínima y anti-rollback. Los documentos lo mencionan como requisito, pero no lo resuelven. | STEP-27, STEP-28, STEP-29, STEP-31, STEP-32 | `NOT LOCATED` | Requisito de política mínima y anti-rollback en la secuencia documental, sin decisión final. | Función: autoridad de versión y revocación. | `AUTHORITY NOT IDENTIFIED` | No aparece una autoridad documentada para ese tema. | DEC-B1-01, DEC-B1-02 | `OPTIONS_INCOMPLETE` | `BLOCKED_BY_AUTHORITY` | Cláusula de versión mínima, anti-rollback y revocación. | Reglas documentadas de versión, revocación y anti-rollback. | Debe existir una regla de versión mínima y de anti-rollback reconocida por la autoridad competente. | No se asume que un cambio “más reciente” es válido sin regla documental. |
| DEC-B1-04 | B1-01 | C01, C02 | ¿Qué Rama A, privilegios y límites de autoridad existen respecto de la política protegida? | La secuencia documenta una Rama A y límites de autoridad de forma parcial, pero no los autoriza. | STEP-26, STEP-27, STEP-29, STEP-32 | `NOT LOCATED` | Se menciona la Rama A y las restricciones, pero no se registra una decisión formal de privilegios. | Función: autoridad de segmentación y privilegios de rama. | `AUTHORITY NOT IDENTIFIED` | No aparece un responsable documental específico. | DEC-B1-01, DEC-B1-02 | `OPTIONS_INCOMPLETE` | `BLOCKED_BY_AUTHORITY` | Cláusula de privilegios y límites. | Decisión documentada de rama, privilegios y límites. | Debe existir una cláusula que delimite la autoridad, la rama y los límites de decisión. | No se usan privilegios por inferencia. |
| DEC-B2-01 | B2-01 | C03 | ¿Qué entidades necesitan identidad inequívoca y por qué? | El requisito exige identidad inequívoca para campaña, ejecución, caso, worker, intento, evidencia y decisión. | STEP-27, STEP-28, STEP-29, STEP-31, STEP-32 | `NOT LOCATED` | La necesidad está repetida en la documentación, pero no el esquema definitivo. | Función: autoridad de identidad y catálogo de entidades. | `AUTHORITY NOT IDENTIFIED` | No aparece una autoridad documentada para definir el esquema. | DEC-B1-01 | `OPTIONS_INCOMPLETE` | `PENDING` | Esquema de identidad y catálogo de entidades. | Especificación de entidades, reglas de generación e invalidación. | Debe existir un catálogo con entidades, campos relevantes y reglas de unicidad. | No diseñar ni implementar un esquema definitivo. |
| DEC-B2-02 | B2-01 | C03 | ¿Qué autoridad define el esquema de relaciones y la validación de la identidad? | La estructura de relaciones debe ser normativa y establecida por autoridad competente. | STEP-27, STEP-28, STEP-29, STEP-31G, STEP-32 | `NOT LOCATED` | Se menciona la necesidad de identidad y relaciones, pero no la autoridad que las aprueba. | Función: autoridad de esquema de identidad. | `AUTHORITY NOT IDENTIFIED` | No hay nombramiento documentado. | DEC-B2-01 | `OPTIONS_INCOMPLETE` | `BLOCKED_BY_AUTHORITY` | Documento formal del esquema de identidad y relaciones. | Esquema aprobado y reglas de invalidación. | Debe existir un esquema con autoridad documentada, campos y reglas de relación. | No se adopta un esquema por suposiciones de diseño. |
| DEC-B3-01 | B3-01 | C04, C05 | ¿Qué entidad produce, valida y custodia la evidencia y cómo se demarca la procedencia? | La documentación exige procedencia, autenticidad y separación de responsabilidades. | STEP-27, STEP-28, STEP-29, STEP-31, STEP-31G | `NOT LOCATED` | El requisito de procedencia y custodia está presente, pero no la decisión normativa. | Función: autoridad de evidencia y custodia. | `AUTHORITY NOT IDENTIFIED` | La documentación no nombra un responsable concreto. | DEC-B1-01, DEC-B2-01 | `OPTIONS_INCOMPLETE` | `PENDING` | Modelo de procedencia y flujo de evidencia. | Reglas de origen, custodia y validación documental. | Debe existir un camino de evidencia con productor, validación, custodia y rechazo explicados. | No asumir que una evidencia es válida por su presencia. |
| DEC-B3-02 | B3-01 | C04, C05 | ¿Qué separación entre producer, observer y verifier es suficiente para evitar autoría circular? | La secuencia repetidamente señala sobreposición de funciones y falta de independencia. | STEP-24, STEP-25, STEP-29, STEP-31G, STEP-32 | `NOT LOCATED` | La sobreposición es observada, pero no se documenta una separación aprobada. | Función: autoridad de separación de responsabilidades. | `AUTHORITY NOT IDENTIFIED` | No hay autoridad documentada establecida. | DEC-B3-01 | `OPTIONS_INCOMPLETE` | `BLOCKED_BY_AUTHORITY` | Matriz de roles, permisos y separación. | Modelo formal de separación de responsabilidades y controles. | Debe existir un diagrama o matriz que demuestre la separación de funciones y sus permisos. | No se da por válida la separación solo por nombrar roles. |
| DEC-B4-01 | B4-01 | C06 | ¿Qué estados y transiciones deben existir para cada entidad y para la campaña? | La documentación exige un catálogo de estados, transiciones y agregación. | STEP-27, STEP-28, STEP-29, STEP-31, STEP-32 | `NOT LOCATED` | Se exige la definición de estados y agregación, pero no el catálogo final. | Función: autoridad de estado y agregación. | `AUTHORITY NOT IDENTIFIED` | No aparece un responsable documental de estados. | DEC-B3-01 | `OPTIONS_INCOMPLETE` | `PENDING` | Tabla de estados y transiciones. | Regla de estados, transiciones y agregación documentadas. | Debe existir un catálogo formal con transiciones permitidas y consecuencias. | No se implementa una máquina de estados por inferencia. |
| DEC-B5-01 | B5-01 | C07, C14 | ¿Qué control de preflight es obligatorio, con qué predicado y qué evidencia lo soporta? | La necesidad de preflight y consecuencias de rechazo aparece como requisito. | STEP-27, STEP-28, STEP-29, STEP-31, STEP-32 | `NOT LOCATED` | Los documentos no publican un preflight final ni su evidencia. | Función: autoridad de preflight y rechazo. | `AUTHORITY NOT IDENTIFIED` | No aparece una autoridad responsable del control. | DEC-B1-01, DEC-B3-01, DEC-B4-01 | `OPTIONS_INCOMPLETE` | `BLOCKED_BY_AUTHORITY` | Tabla de preflight, decisiones de rechazo y evidencia requerida. | Predicado verificable y registro de rechazo. | Debe existir un control formal con predicado verificable, evidencia y consecuencia de rechazo. | No se puede ejecutar ni certificar preflight sin autoridad y evidencia. |
| DEC-B6-01 | B6-01 | C08, C09 | ¿Cuál es la definición canónica del árbol cubierto y del digest? | La documentación exige una especificación del árbol cubierto, orden canónico y aprobación indivisible. | STEP-27, STEP-28, STEP-29, STEP-31, STEP-32 | `NOT LOCATED` | Los requisitos están redactados, pero la definición final no aparece. | Función: autoridad de digest y serialización. | `AUTHORITY NOT IDENTIFIED` | No hay autoridad documental identificada para la definición final. | DEC-B1-01, DEC-B2-01, DEC-B5-01 | `OPTIONS_INCOMPLETE` | `BLOCKED_BY_AUTHORITY` | Documento de digest canónico y asignación de nodeids. | Algoritmo, serialización, orden canónico y aprobación. | Debe existir una definición canónica de digest y una relación documentada entre nodeids y árbol. | No se aprueba ni se usa un digest sin autoridad y algoritmo. |
| DEC-B6-02 | B6-01 | C08, C09 | ¿Qué autoridad aprueba el par indivisible `(nodeids, tree_digest)`? | La aprobación del par es un requisito, pero no se identifica la entidad que aprueba la pareja. | STEP-27, STEP-28, STEP-29, STEP-31G, STEP-32 | `NOT LOCATED` | La necesidad aparece, pero la autoridad no se documenta. | Función: autoridad de aprobación y revocación del par. | `AUTHORITY NOT IDENTIFIED` | No hay base documental para nombre o función. | DEC-B6-01 | `OPTIONS_INCOMPLETE` | `BLOCKED_BY_AUTHORITY` | Registro de aprobación de la pareja. | Aprobación, revocación y evidencia asociada. | Debe existir un par aprobado y revocable documentalmente. | No se puede asumir que una ejecución o un hash equivale a aprobación. |
| DEC-B7-01 | B7-01 | C10, C12 | ¿Cómo se define una campaña, sus intentos y sus condiciones de cierre? | La documentación exige campañas, reintentos, idempotencia y cierre con contradicciones. | STEP-27, STEP-28, STEP-29, STEP-31, STEP-32 | `NOT LOCATED` | Se requieren campañas y cierre, pero no un protocolo documental final. | Función: autoridad de campaña y cierre. | `AUTHORITY NOT IDENTIFIED` | No se documenta el órgano responsable. | DEC-B2-01, DEC-B4-01, DEC-B8-01 | `OPTIONS_INCOMPLETE` | `PENDING` | Protocolo de campaña y cierre. | Registros de campaña, intentos y decisiones finales. | Debe existir un protocolo con campaña, intentos, cierre y reglas de idempotencia. | No se asume cierre por documentación general. |
| DEC-B7-02 | B7-01 | C10, C12 | ¿Qué autoridad resuelve contradicciones y cómo se registra la adjudicación? | La secuencia documenta contradicciones, pero no un mecanismo formal de resolución. | STEP-25, STEP-29, STEP-31G, STEP-32 | `NOT LOCATED` | Se observa la existencia de contradicción, no su mecanismo de resolución. | Función: autoridad de resolución de contradicciones. | `AUTHORITY NOT IDENTIFIED` | No hay base documental suficiente para una entidad concreta. | DEC-B7-01 | `OPTIONS_INCOMPLETE` | `CONFLICT_REQUIRES_ADJUDICATION` | Registro de contradicciones y resolución. | Afirmación de conflicto y adjudicación autorizada. | Debe existir una clasificación y resolución documentada para cada contradicción. | No se adjudican contradicciones por clasificación histórica sin evidencia comparativa. |
| DEC-B8-01 | B8-01 | C11 | ¿Qué estructura tendrá la matriz final de trazabilidad requisito → decisión → evidencia? | La trazabilidad completa es un requisito, y la secuencia lo reitera como pendiente. | STEP-27, STEP-28, STEP-29, STEP-31, STEP-31G, STEP-32 | `NOT LOCATED` | No existe una matriz final o una trazabilidad completa. | Función: autoridad de suficiencia documental. | `AUTHORITY NOT IDENTIFIED` | No aparece una autoridad final documentada para adjudicar la suficiencia. | Todas las decisiones anteriores | `OPTIONS_INCOMPLETE` | `PENDING` | Matriz final de trazabilidad. | Requisito, cláusula, decisión, autoridad y evidencia asociados. | Debe existir una matriz con cada requisito ligado a decisión, autoridad y evidencia, o ausencia expresamente adjudicada. | No se declarará trazabilidad completa sin la matriz. |
| DEC-B8-02 | B8-01 | C11 | ¿Qué autoridad puede adjudicar la suficiencia documental de la trazabilidad? | La documentación distingue la necesidad de trazabilidad y la ausencia de adjudicación. | STEP-31D, STEP-31E, STEP-31F, STEP-31G, STEP-32 | `NOT LOCATED` | Se deja claro que la trazabilidad documental no equivale a cierre operacional ni autoridad. | Función: autoridad de suficiencia documental. | `AUTHORITY NOT IDENTIFIED` | No hay autoridad documentada. | DEC-B8-01 | `OPTIONS_INCOMPLETE` | `BLOCKED_BY_AUTHORITY` | Registro de adjudicación de suficiencia. | Evidencia de aprobaciones y límites de suficiencia. | Debe existir autoridad documentada que determine cuándo la trazabilidad es suficiente. | No se asume que la existencia de una tabla basta para adjudicar suficiencia. |

---

## 6. Inventario de autoridades y competencias

La secuencia documental evidencia que se requieren varias funciones decisorias, pero no demuestra que estén ocupadas por entidades identificadas. Por ello, la siguiente sección mantiene la diferencia entre función requerida e identidad documental.

| function_required | identity_documental | competency_attributed | limits | evidence_status | current_status |
|---|---|---|---|---|---|
| autoridad de política y trust root | `NOT LOCATED` | `NOT EVALUABLE` | no se identifica la competencia ni los límites | `NOT EVALUABLE` | `AUTHORITY NOT IDENTIFIED` |
| autoridad aprobadora de la política | `NOT LOCATED` | `NOT EVALUABLE` | no se localiza una delegación o norma | `NOT EVALUABLE` | `AUTHORITY NOT IDENTIFIED` |
| autoridad de versión y revocación | `NOT LOCATED` | `NOT EVALUABLE` | no aparece una regla o órgano competente | `NOT EVALUABLE` | `AUTHORITY NOT IDENTIFIED` |
| autoridad de rama y privilegios | `NOT LOCATED` | `NOT EVALUABLE` | Rama A y privilegios no están definidos como decisión autorizada | `NOT EVALUABLE` | `AUTHORITY NOT IDENTIFIED` |
| autoridad de identidad y catálogo | `NOT LOCATED` | `NOT EVALUABLE` | no se localiza una especificación aprobada | `NOT EVALUABLE` | `AUTHORITY NOT IDENTIFIED` |
| autoridad de evidencia y custodia | `NOT LOCATED` | `NOT EVALUABLE` | no se localiza una cadena de custodia aprobada | `NOT EVALUABLE` | `AUTHORITY NOT IDENTIFIED` |
| autoridad de separación de responsabilidades | `NOT LOCATED` | `NOT EVALUABLE` | no se documenta separación efectiva | `NOT EVALUABLE` | `AUTHORITY NOT IDENTIFIED` |
| autoridad de estados y agregación | `NOT LOCATED` | `NOT EVALUABLE` | no se aprueba una máquina de estados | `NOT EVALUABLE` | `AUTHORITY NOT IDENTIFIED` |
| autoridad de preflight y rechazo | `NOT LOCATED` | `NOT EVALUABLE` | no se documenta un control final | `NOT EVALUABLE` | `AUTHORITY NOT IDENTIFIED` |
| autoridad de digest y serialización | `NOT LOCATED` | `NOT EVALUABLE` | no se aprueba un algoritmo canónico y una relación clara | `NOT EVALUABLE` | `AUTHORITY NOT IDENTIFIED` |
| autoridad de aprobación del par `(nodeids, tree_digest)` | `NOT LOCATED` | `NOT EVALUABLE` | no existe evidencia de aprobación formal | `NOT EVALUABLE` | `AUTHORITY NOT IDENTIFIED` |
| autoridad de campaña y cierre | `NOT LOCATED` | `NOT EVALUABLE` | no hay protocolo final de cierre | `NOT EVALUABLE` | `AUTHORITY NOT IDENTIFIED` |
| autoridad de resolución de contradicciones | `NOT LOCATED` | `NOT EVALUABLE` | no está demostrada una adjudicación formal | `NOT EVALUABLE` | `AUTHORITY NOT IDENTIFIED` |
| autoridad de suficiencia documental | `NOT LOCATED` | `NOT EVALUABLE` | no existe cierre ni aprobación formal de trazabilidad | `NOT EVALUABLE` | `AUTHORITY NOT IDENTIFIED` |

---

## 7. Registro acotado de contradicciones y adjudicación pendiente

Se examinan únicamente las contradicciones que impactan directamente la toma de decisiones contractuales. El objetivo no es abrir una nueva auditoría profunda del historial, sino mantener una clasificación específica de conflictos que necesitan resolución de autoridad.

### CONF-01 — Local trust root versus external trust anchor

- Afirmación documental A: el sistema puede depender del checkout local y de la infraestructura contenida en la propia ejecución. Esto aparece en la trazabilidad y la revisión de trust root. (Fuente: STEP-25, STEP-29, STEP-31G, STEP-32.)
- Afirmación documental B: los documentos también exigen una fuente externa protegida y una autoridad fuera del checkout para la política y el trust root. (Fuente: STEP-27, STEP-28, STEP-31, STEP-32.)
- Relación: es una diferencia de autoridad y de alcance entre `local trust` y `external protected authority`.
- Clasificación: `REAL_NORMATIVE_CONTRADICTION`
- Decisión necesaria: decidir la raíz de confianza y la autoridad que la protege.
- Autoridad requerida: autoridad de política y trust root.
- Estado de adjudicación: `BLOCKED_BY_AUTHORITY`

### CONF-02 — worker/controller overlap versus required independence

- Afirmación documental A: se observan overlaps funcionales y responsabilidades compartidas entre workers, observers y verifiers. (Fuente: STEP-24, STEP-25, STEP-29, STEP-31G.)
- Afirmación documental B: los documentos exigen separación de responsabilidades y observabilidad independiente. (Fuente: STEP-27, STEP-28, STEP-31, STEP-32.)
- Relación: hay una diferencia entre la estructura observada y la estructura normativa requerida.
- Clasificación: `SCOPE_OR_CLOSURE_LEVEL_DIFFERENCE`
- Decisión necesaria: definir la separación y la autoridad que la valida.
- Autoridad requerida: autoridad de separación de responsabilidades.
- Estado de adjudicación: `BLOCKED_BY_AUTHORITY`

### CONF-03 — static sufficiency versus operational closure

- Afirmación documental A: la secuencia precedente sostiene que la evidencia documental es suficiente para afirmar incompletitud y bloqueo. (Fuente: STEP-31D, STEP-31E, STEP-31F, STEP-31G.)
- Afirmación documental B: la documentación también exige que la prueba de cierre operativa no puede derivarse de la mera suficiencia documental. (Fuente: STEP-27, STEP-28, STEP-29, STEP-32.)
- Relación: es una diferencia entre `suficiencia documental para rechazar cierre` y `autorización operativa para cerrar`.
- Clasificación: `SCOPE_OR_CLOSURE_LEVEL_DIFFERENCE`
- Decisión necesaria: definir qué evidencia es suficiente para permitir una decisión de cierre y quién la adjudica.
- Autoridad requerida: autoridad de suficiencia documental.
- Estado de adjudicación: `BLOCKED_BY_AUTHORITY`

Se conserva una clasificación histórica, pero no se presenta como adjudicación definitiva sin una comparación documental suficiente y una autoridad competente.

---

## 8. Dependencias entre decisiones

La siguiente lista registra dependencias con los identificadores `DEC-Bn-XX`. Se usa la clasificación documental de la directiva STEP-33.

| from_decision | to_decision | dependency_kind | rationale | evidence_status |
|---|---|---|---|---|
| DEC-B1-01 | DEC-B1-02 | `DOCUMENTED_DEPENDENCY` | la autoridad para aprobar la política depende de la existencia del artefacto y de su alcance | `PARTIALLY_SUPPORTED` |
| DEC-B1-01 | DEC-B1-03 | `DOCUMENTED_DEPENDENCY` | la versión mínima y el anti-rollback dependen de la política base | `PARTIALLY_SUPPORTED` |
| DEC-B1-01 | DEC-B1-04 | `DOCUMENTED_DEPENDENCY` | la rama y los límites dependen de la identidad del artefacto protegido | `PARTIALLY_SUPPORTED` |
| DEC-B1-01 | DEC-B2-01 | `DOCUMENTED_DEPENDENCY` | la identidad del sistema depende del marco de autoridad de la política | `PARTIALLY_SUPPORTED` |
| DEC-B2-01 | DEC-B2-02 | `DOCUMENTED_DEPENDENCY` | la identidad y el esquema requieren autoridad aprobadora | `PARTIALLY_SUPPORTED` |
| DEC-B2-01 | DEC-B3-01 | `DOCUMENTED_DEPENDENCY` | la evidencia requiere entidades con identidad clara | `PARTIALLY_SUPPORTED` |
| DEC-B3-01 | DEC-B3-02 | `DOCUMENTED_DEPENDENCY` | la separación funcional depende del modelo de evidencias y roles | `PARTIALLY_SUPPORTED` |
| DEC-B3-01 | DEC-B4-01 | `DOCUMENTED_DEPENDENCY` | los estados y sobre la evidencia requieren un modelo de procedencia | `PARTIALLY_SUPPORTED` |
| DEC-B1-01 | DEC-B5-01 | `DOCUMENTED_DEPENDENCY` | el preflight depende del contexto y límites de autoridad | `PARTIALLY_SUPPORTED` |
| DEC-B3-01 | DEC-B5-01 | `DOCUMENTED_DEPENDENCY` | el preflight requiere evidencia y rechazo claro | `PARTIALLY_SUPPORTED` |
| DEC-B4-01 | DEC-B5-01 | `DOCUMENTED_DEPENDENCY` | el preflight depende de la semántica de estados | `PARTIALLY_SUPPORTED` |
| DEC-B1-01 | DEC-B6-01 | `DOCUMENTED_DEPENDENCY` | el digest requiere un contexto de autoridad y política | `PARTIALLY_SUPPORTED` |
| DEC-B2-01 | DEC-B6-01 | `DOCUMENTED_DEPENDENCY` | los nodeids y la relación con el árbol requieren identidad clara | `PARTIALLY_SUPPORTED` |
| DEC-B5-01 | DEC-B6-01 | `DOCUMENTED_DEPENDENCY` | el digest debe validarse bajo preflight | `PARTIALLY_SUPPORTED` |
| DEC-B6-01 | DEC-B6-02 | `DOCUMENTED_DEPENDENCY` | la aprobación del par depende de la definición del digest y del esquema | `PARTIALLY_SUPPORTED` |
| DEC-B2-01 | DEC-B7-01 | `DOCUMENTED_DEPENDENCY` | la campaña exige entidad y ciclo de vida definidos | `PARTIALLY_SUPPORTED` |
| DEC-B4-01 | DEC-B7-01 | `DOCUMENTED_DEPENDENCY` | el cierre y la repetición de intentos dependen del estado y de la agregación | `PARTIALLY_SUPPORTED` |
| DEC-B8-01 | DEC-B7-01 | `PROPOSED_DEPENDENCY` | la trazabilidad es útil para la campaña, pero no necesariamente antecedente directo del protocolo | `NOT EVALUABLE` |
| DEC-B1-01 | DEC-B8-01 | `PROPOSED_DEPENDENCY` | toda la trazabilidad final depende de la política y de la autoridad | `NOT EVALUABLE` |
| DEC-B8-01 | DEC-B8-02 | `DOCUMENTED_DEPENDENCY` | la adjudicación de suficiencia depende de la matriz final | `PARTIALLY_SUPPORTED` |

La secuencia B1 → B2 → B3 → B4 → B5 → B6 → B7 → B8 viene de STEP-32 y se conserva como recomendación documental, no como autoridad normativa.

---

## 9. Predicados de cierre y requisitos objetivos

Cada decisión pendiente exige un predicado de cierre verificable. En esta sección se enumeran los predicados mínimos y las restricciones de autoridad.

| decision_id | closure_predicate | current_status |
|---|---|---|
| DEC-B1-01 | Debe existir un artefacto protegido con autoridad, versión mínima, condiciones de aprobación y revocación documentadas. | `BLOCKED_BY_AUTHORITY` |
| DEC-B1-02 | Debe existir un órgano o rol especificado como competente, con límites de competencia y evidencia del ámbito de decisión. | `BLOCKED_BY_AUTHORITY` |
| DEC-B1-03 | Debe existir una regla escrita de versión mínima y anti-rollback aprobada por la autoridad competente. | `BLOCKED_BY_AUTHORITY` |
| DEC-B1-04 | Debe existir una cláusula que delimite rama, privilegios y límites de autoridad de la política. | `BLOCKED_BY_AUTHORITY` |
| DEC-B2-01 | Debe existir un catálogo formal de entidades y reglas de identidad y unicidad. | `PENDING` |
| DEC-B2-02 | Debe existir un esquema aprobado y validado por la autoridad competente. | `BLOCKED_BY_AUTHORITY` |
| DEC-B3-01 | Debe existir un flujo de evidencia con productor, validación, custodia y rechazo documentados. | `PENDING` |
| DEC-B3-02 | Debe existir una separación de responsabilidades con permisos y funciones claramente definidos. | `BLOCKED_BY_AUTHORITY` |
| DEC-B4-01 | Debe existir un catálogo de estados y una regla de agregación documentada. | `PENDING` |
| DEC-B5-01 | Debe existir un predicado verificable, evidencia requerida y decisión formal de rechazo. | `BLOCKED_BY_AUTHORITY` |
| DEC-B6-01 | Debe existir una definición canónica de digest y las reglas de serialización y orden canónico. | `BLOCKED_BY_AUTHORITY` |
| DEC-B6-02 | Debe existir una aprobación formal del par `(nodeids, tree_digest)` y su revocación. | `BLOCKED_BY_AUTHORITY` |
| DEC-B7-01 | Debe existir un protocolo documental con campaña, reintentos y cierre definidos. | `PENDING` |
| DEC-B7-02 | Debe existir un mecanismo de resolución de contradicciones y una autoridad formal. | `CONFLICT_REQUIRES_ADJUDICATION` |
| DEC-B8-01 | Debe existir una matriz final con requisito → cláusula → decisión → autoridad → evidencia → adjudicación. | `PENDING` |
| DEC-B8-02 | Debe existir una autoridad documentada que determine cuándo la trazabilidad es suficiente. | `BLOCKED_BY_AUTHORITY` |

Ningún predicado de cierre permite asumir implementación, ejecución o cierre operativo. Una decisión documentalmente aceptada no equivale a autorización para probar ni ejecutar.

---

## 10. Preservación y límites de evidencia

Se usa lectura estática y consulta Git de solo lectura para registrar:

- repositorio observado: `/media/agustin/Laboratorio/study-engie`
- rama observada: `talos-current-audit`
- HEAD observado: `cc8acfae623f9d10c8366871470319786b6a7ca4`
- límites de la comprobación: solo lectura y registros documentales; no se ejecutan tests ni código del proyecto.

No se declara preservación histórica demostrada cuando la comparación reproducible no está disponible. Si una afirmación no puede verificarse, se registra como `NOT EVALUABLE`.

---

## 11. Estado cuantitativo por brecha

| gap_id | decisions_registered | identified_authority | partially_identified | authority_not_identified | blocked_by_authority | blocked_by_dependency | pending | conflict_requires_adjudication |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B1-01 | 4 | 0 | 0 | 4 | 4 | 0 | 0 | 0 |
| B2-01 | 2 | 0 | 0 | 2 | 1 | 0 | 1 | 0 |
| B3-01 | 2 | 0 | 0 | 2 | 1 | 0 | 1 | 0 |
| B4-01 | 1 | 0 | 0 | 1 | 0 | 0 | 1 | 0 |
| B5-01 | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |
| B6-01 | 2 | 0 | 0 | 2 | 2 | 0 | 0 | 0 |
| B7-01 | 2 | 0 | 0 | 2 | 0 | 0 | 1 | 1 |
| B8-01 | 2 | 0 | 0 | 2 | 1 | 0 | 1 | 0 |
| Total | 16 | 0 | 0 | 16 | 10 | 0 | 5 | 1 |

Las cifras son el resultado de la clasificación documental de estas decisiones. No expresan aprobación ni cierre; solo reflejan la ausencia de autoridad suficiente y el estado de la decisión documental.

---

## 12. Informe de cierre

- Ruta del único documento creado: `docs/STEP-33-REGISTRO-DE-DECISIONES-Y-AUTORIDADES-PENDIENTES-B1-B8.md`
- Identidad observada del checkout: `talos-current-audit` / `cc8acfae623f9d10c8366871470319786b6a7ca4`
- Número total de decisiones registradas: `16`
- Decisiones con autoridad identificada: `0`
- Decisiones con autoridad parcialmente identificada: `0`
- Decisiones con autoridad no identificada: `16`
- Decisiones bloqueadas por autoridad: `10`
- Decisiones pendientes: `5`
- Contradicciones registradas y no resueltas: `CONF-01`, `CONF-02`, `CONF-03`
- Dependencias documentadas: `DOCUMENTED_DEPENDENCY`
- Dependencias propuestas: `PROPOSED_DEPENDENCY`
- Estado del árbol y preservación: solo se verificó el estado actual del checkout mediante Git de lectura; no se atribuye preservación histórica sin evidencia suficiente.
- Confirmación: no se ejecutaron tests ni código del proyecto.
- Confirmación: no hubo operaciones Git mutativas.
- Confirmación: no se cerraron brechas ni se concedieron autorizaciones.

Si una cifra o afirmación no puede verificarse, se marca como `NOT EVALUABLE` y no se rellena por estimación.

---

## 13. Condiciones de aceptación

STEP-33 se considera documentalmente completo solo si:

- cada brecha B1-01–B8-01 está descompuesta en decisiones atómicas identificables;
- cada decisión tiene fundamento, estado, autoridad requerida y predicado de cierre;
- la ausencia de autoridad está explícitamente registrada, sin nombramientos inferidos;
- las dependencias están clasificadas como documentadas o propuestas;
- CONF-01–CONF-03 no se presentan como adjudicadas sin evidencia comparativa suficiente;
- las afirmaciones no verificables están marcadas como tales;
- solo se creó el entregable especificado;
- no se alteraron las fuentes anteriores ni se ejecutaron operaciones prohibidas.

La aceptación documental de STEP-33 no implica la aceptación de ninguna decisión contractual pendiente.

---

## 14. Declaración final obligatoria

> STEP-33 formaliza el registro de decisiones contractuales pendientes y de sus requisitos de autoridad. No aprueba decisiones, no inventa competencias, no resuelve por inferencia contradicciones no demostradas, no cierra B1-01–B8-01, no satisface C11 por la mera existencia de este registro y no autoriza implementación ni validación dinámica. TALOS V1 permanece FROZEN. P1.2 continúa BLOCKED-REGRESSION; P1.3 continúa BLOCKED; B1-R permanece NOT AUTHORIZED; EXTERNAL HARNESS IMPLEMENTATION y DYNAMIC VALIDATION permanecen NOT AUTHORIZED. GATE B continúa INCOMPLETE.

**FIN DE DIRECTIVA STEP-33**
