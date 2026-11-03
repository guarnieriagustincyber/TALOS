# TALOS V1.5 — STEP-41

## RECONCILIACIÓN DOCUMENTAL CORRECTIVA DE STEP-39 CONFORME A LOS HALLAZGOS F40
**Tipo:** directiva de reconciliación documental estática, con trazabilidad probatoria individualizada y preservación de autoridad.

**Repositorio:** `/media/agustin/Laboratorio/study-engie`

**Rama esperada:** `talos-current-audit`

**HEAD histórico de referencia reportado:** `cc8acfae623f9d10c8366871470319786b6a7ca4`

**Entregable único autorizado:**

`docs/STEP-41-RECONCILIACION-CORRECTIVA-STEP-39-Y-HALLAZGOS-F40.md`

**Antecedente inmediato:** `docs/STEP-40-AUDITORIA-INTEGRIDAD-Y-SUFICIENCIA-PROBATORIA-STEP-39.md`

**Objetivo:** especificar y documentar una reconciliación correctiva de STEP-39 a partir de los ocho hallazgos F40, preservando la identidad de los antecedentes, la separación entre propuesta y ejecución, y los límites de autoridad. El entregable debe permitir una auditoría posterior de sus propias afirmaciones sin presentar como ejecutadas las correcciones que solo se especifican.

---

## 1. Estado canónico obligatorio

Conservar exactamente los siguientes estados, sin reinterpretación ni promoción:

- `TALOS V1 = FROZEN`
- `P1.2 = BLOCKED-REGRESSION`
- `P1.3 = BLOCKED`
- `B1-R = NOT AUTHORIZED`
- `EXTERNAL HARNESS IMPLEMENTATION = NOT AUTHORIZED`
- `DYNAMIC VALIDATION = NOT AUTHORIZED`
- `GATE B = INCOMPLETE`

Estados documentales:

- `DOCUMENTARY_AUDIT = COMPLETE_WITH_OPEN_GAPS`
- `EVIDENTIARY_SUFFICIENCY = PARTIALLY_SUPPORTED_WITH_OPEN_EVIDENTIARY_GAPS`
- `AUTHORITY IDENTIFICATION = INCOMPLETE`
- `B1-01` a `B7-01 = OPEN`
- `B8-01 = ABSENT / NOT_SATISFIED`

Estos estados son invariantes de esta directiva. La creación de STEP-41 no los modifica.

El resultado `SPECIFICATION_PARTIALLY_SUFFICIENT` de STEP-40 se conserva como dictamen histórico de ese documento. No debe reemplazarse retroactivamente ni reinterpretarse como cierre de los hallazgos F40.

---

## 2. Alcance y límites de autorización

### 2.1. Permitido

Realizar exclusivamente:

1. Lectura documental de STEP-40 y STEP-39.
2. Consulta puntual de STEP-38 y STEP-37 para preservar la identidad y el contexto de cada hallazgo.
3. Consulta de STEP-35, STEP-36, STEP-33 y STEP-34 cuando sea necesaria para verificar identificadores históricos o afirmaciones concretas.
4. Consulta de STEP-27 a STEP-32 únicamente cuando una afirmación requiera contrastarse con una fuente específica.
5. Inspección de Git de solo lectura para identificar rama, HEAD y estado visible del checkout, siempre que pueda hacerse sin alterar el repositorio.
6. Creación exclusiva del documento STEP-41.
7. Registro explícito de información no encontrada, no verificable o insuficientemente sustentada.

### 2.2. Prohibido

- Modificar STEP-39, STEP-40 o cualquier antecedente documental.
- Modificar código, pruebas, configuraciones, snapshots, bases de datos, corpus o modelos.
- Ejecutar pruebas, incluido `pytest --collect-only`.
- Importar o ejecutar código del proyecto.
- Construir o iniciar aplicaciones, servicios, workers, runners o harnesses.
- Ejecutar benchmarks o validación dinámica.
- Acceder a bases de datos, corpus, modelos, proveedores o estado de aprendizaje.
- Ejecutar operaciones Git mutativas: `checkout`, `switch`, `reset`, `clean`, `stash`, `commit`, `push`, `rebase`, `cherry-pick` o equivalentes.
- Publicar, editar o modificar contenido en GitHub.
- Inventar fuentes, extractos, autoridades, aprobaciones o ubicaciones.
- Convertir una recomendación documental en requisito normativo sin evidencia.
- declarar que una corrección fue ejecutada cuando solo se definió su procedimiento.
- Cerrar brechas, aprobar decisiones o autorizar operaciones.
- Declarar el checkout íntegro si la evidencia obtenida no permite reproducir esa conclusión.

Si una fuente o ubicación no puede localizarse, registrar `NOT LOCATED`. Si la información disponible no permite adjudicar una afirmación, registrar `NOT EVALUABLE` o `INSUFFICIENTLY SUPPORTED`, según corresponda.

---

## 3. Principio rector: especificación, ejecución y cierre son estados distintos

STEP-41 debe establecer explícitamente tres niveles independientes:

1. Especificación correctiva: define qué debe cambiarse, con qué evidencia, mediante qué criterio y cómo se comprobará.
2. Ejecución documental: acredita que una corrección concreta fue efectivamente incorporada en el artefacto autorizado y aporta una referencia verificable a esa ejecución.
3. Cierre sustantivo: determina si la evidencia satisface el predicado de cierre pertinente, sin confundirlo con la mera existencia de un documento corregido.

Una especificación puede estar completa como plan sin que exista ejecución. Una corrección documental ejecutada puede seguir siendo insuficiente para acreditar una autoridad, una aprobación o un requisito contractual. Ninguno de estos estados permite inferir autorización operativa.

La directiva actual autoriza únicamente producir STEP-41 como documento de reconciliación. No autoriza modificar STEP-39 ni ejecutar las correcciones allí descritas.

---

## 4. Matriz de identidad y tratamiento de F40

Reproducir los ocho hallazgos F40 con sus identificadores originales y registrar para cada uno:

- `finding_id`
- `source_artifact`
- `source_location`
- `identity_result`
- `condition_preserved`
- `correction_specified`
- `supporting_evidence`
- `execution_status`
- `closure_status`
- `limitations`
- `final_adjudication`

Los identificadores F40-01 a F40-08 deben conservarse literalmente. No fusionar hallazgos por similitud temática, no dividirlos sin mantener una relación explícita con el original y no convertirlos en nuevos identificadores canónicos B1–B8.

La matriz debe partir de las siguientes condiciones históricas reportadas por STEP-40:

| Hallazgo | Condición que debe preservarse | Tratamiento exigido |
|---|---|---|
| F40-01 | Separación insuficientemente explícita entre propuesta y ejecución | Diferenciar especificación, ejecución acreditada y cierre |
| F40-02 | Fuentes reales y extractos no incorporados en la especificación | Definir evidencia localizable sin simular que ya existe |
| F40-03 | Ausencia de regla reproducible de agregación del dictamen | Especificar una regla determinista y auditable |
| F40-04 | GAP-01 a GAP-06 sin origen canónico visible | Identificarlos como auxiliares y establecer límites de correspondencia |
| F40-05 | Reglas incompletas del esquema de evidencia | Definir tratamiento de citas, paráfrasis, ausencias, autoridad y vigencia |
| F40-06 | `SPECIFICATION_COMPLETE` sobreafirmado respecto de la suficiencia probatoria | Separar cobertura nominal de suficiencia probatoria |
| F40-07 | Mezcla de observación, inferencia y afirmación histórica en el informe de ejecución | Exigir clasificación y soporte por afirmación |
| F40-08 | Riesgo de inferir autoridad externa a partir de referencias no localizadas | Mantener la autoridad como no identificada hasta que exista evidencia competente |

Esta tabla es una guía de tratamiento basada en el informe STEP-40, no una afirmación de que STEP-39 haya sido inspeccionado independientemente durante la ejecución local.

Si las ubicaciones reales de STEP-39 difieren de las citadas por STEP-40, registrar la discrepancia. No ajustar silenciosamente las referencias.

### 4.1. Matriz de tratamiento de F40

| finding_id | source_artifact | source_location | identity_result | condition_preserved | correction_specified | supporting_evidence | execution_status | closure_status | limitations | final_adjudication |
|---|---|---|---|---|---|---|---|---|---|---|
| F40-01 | STEP-39 | §4, §10, §11 | `CONFIRMED` | `CONFIRMED` | `CONFIRMED` | `PARTIALLY CONFIRMED` | `SPECIFIED_NOT_EXECUTED` | `OPEN` | El documento exige separar estados, pero no ejecuta la corrección | `SPECIFICATION_REQUIRED` |
| F40-02 | STEP-39 | §5, §8 | `CONFIRMED` | `CONFIRMED` | `CONFIRMED` | `PARTIALLY CONFIRMED` | `SPECIFIED_NOT_EXECUTED` | `OPEN` | No se presenta la fuente real que validaría la corrección | `SPECIFICATION_REQUIRED` |
| F40-03 | STEP-39 | §7 | `CONFIRMED` | `CONFIRMED` | `CONFIRMED` | `PARTIALLY CONFIRMED` | `SPECIFIED_NOT_EXECUTED` | `OPEN` | La regla de agregación se propone, pero no se ejecuta | `SPECIFICATION_REQUIRED` |
| F40-04 | STEP-39 | §9 | `CONFIRMED` | `CONFIRMED` | `CONFIRMED` | `PARTIALLY CONFIRMED` | `SPECIFIED_NOT_EXECUTED` | `OPEN` | Los GAP siguen siendo auxiliares de la especificación, no identificadores canónicos | `SPECIFICATION_REQUIRED` |
| F40-05 | STEP-39 | §8, §9 | `CONFIRMED` | `CONFIRMED` | `CONFIRMED` | `PARTIALLY CONFIRMED` | `SPECIFIED_NOT_EXECUTED` | `OPEN` | La evidencia requiere más reglas de vigencia y autoridad | `SPECIFICATION_REQUIRED` |
| F40-06 | STEP-39 | §9, §11 | `CONFIRMED` | `CONFIRMED` | `CONFIRMED` | `PARTIALLY CONFIRMED` | `SPECIFIED_NOT_EXECUTED` | `OPEN` | La suficiencia probatoria no se demuestra en el documento | `SPECIFICATION_REQUIRED` |
| F40-07 | STEP-39 | §10, §12 | `CONFIRMED` | `CONFIRMED` | `CONFIRMED` | `PARTIALLY CONFIRMED` | `SPECIFIED_NOT_EXECUTED` | `OPEN` | El informe sigue siendo narrativo si no se documentan las fuentes reales | `SPECIFICATION_REQUIRED` |
| F40-08 | STEP-39 | §12 | `CONFIRMED` | `CONFIRMED` | `CONFIRMED` | `PARTIALLY CONFIRMED` | `SPECIFIED_NOT_EXECUTED` | `OPEN` | La autoridad permanece no identificada | `SPECIFICATION_REQUIRED` |

---

## 5. Corrección documental de F40-01: separación de estados

Especificar un modelo de estados que permita distinguir, como mínimo:

- `SPECIFIED_NOT_EXECUTED`
- `EXECUTION_REPORTED_NOT_REPRODUCED`
- `EXECUTION_EVIDENCED`
- `DOCUMENTARY_CLOSURE_SUPPORTED`
- `SUBSTANTIVE_CLOSURE_NOT_ESTABLISHED`
- `NOT_EVALUABLE`

No deben interpretarse como una secuencia automática de progreso. Cada estado requiere evidencia propia y el cumplimiento de su predicado correspondiente.

Para cada corrección propuesta, el registro debe identificar:

1. Qué documento o afirmación se pretende corregir.
2. Qué defecto concreto se pretende resolver.
3. Qué evidencia permitiría demostrar la ejecución.
4. Qué comprobación permite reproducir el resultado.
5. Qué aspectos seguirían abiertos aun si la corrección documental se ejecutara.

**Criterio de aceptación:** ningún resumen, plan, especificación o informe declarativo puede clasificarse como corrección ejecutada sin un soporte localizable y una comprobación reproducible.

### 5.1. Matriz de estados para STEP-41

| state_id | meaning | evidence_required | effect_if_missing |
|---|---|---|---|
| `SPECIFIED_NOT_EXECUTED` | la corrección existe como propuesta | texto de la especificación y alcance | no demuestra ejecución |
| `EXECUTION_REPORTED_NOT_REPRODUCED` | existe un reporte de ejecución no corroborado | evidencia de lectura, comparación o reproducibilidad | no habilita cierre |
| `EXECUTION_EVIDENCED` | se puede localizar la ejecución real | referencia documental y prueba de modificación o incorporación | requiere predicado de cierre |
| `DOCUMENTARY_CLOSURE_SUPPORTED` | la corrección se ejecutó documentalmente | evidencia de incorporación y enlace con Hallazgo F40 | no reemplaza autoridad ni aprobación |
| `SUBSTANTIVE_CLOSURE_NOT_ESTABLISHED` | la corrección es útil pero no cierra la brecha de fondo | evidencia de cumplimiento del requisito real | no autoriza operación ni cierre |
| `NOT_EVALUABLE` | no hay base para adjudicar el estado | ausencia de evidencias reales | mantiene el estado como abierto o bloqueado |

---

## 6. Corrección documental de F40-02: registro probatorio localizable

Especificar una estructura de evidencia con los siguientes campos:

- `evidence_id`
- `claim_id`
- `source_artifact`
- `source_location`
- `excerpt_or_observation`
- `evidence_type`
- `evidence_role`
- `verification_result`
- `temporal_status`
- `limitations`
- `adjudication_basis`

`evidence_type` debe distinguir, al menos:

- `LITERAL_QUOTE`
- `PARAPHRASE`
- `DIRECT_OBSERVATION`
- `HISTORICAL_REPORT`
- `ABSENCE_OBSERVATION`
- `INFERENCE`

`evidence_role` debe distinguir entre:

- `NORMATIVE_REQUIREMENT`
- `DESCRIPTIVE_CONTEXT`
- `DECISION_OR_APPROVAL`
- `EXECUTION_EVIDENCE`
- `CONTRADICTORY_EVIDENCE`
- `CONTEXT_ONLY`

No se debe inferir que una fuente es normativa únicamente porque contiene palabras como “debe”, “autoridad”, “política”, “aprobación” o equivalentes. La clasificación exige contexto y ubicación verificable.

Para cada cita literal, conservar el texto tal como aparece en la fuente y su ubicación. Para una paráfrasis, identificarla explícitamente como tal y no presentarla entre comillas como si fuera una cita. Para una observación de ausencia, delimitar el ámbito efectivamente inspeccionado: no encontrar una referencia en un documento no demuestra que no exista en todo el repositorio.

Cuando no exista una fuente localizable, utilizar `NOT LOCATED` y explicar qué afirmación queda sin soporte. No completar la ausencia con reconstrucciones hipotéticas.

**Criterio de aceptación:** toda afirmación material de STEP-41 debe tener una fuente identificable o una declaración explícita de que no puede sustentarse con la evidencia disponible.

---

## 7. Corrección documental de F40-03: regla determinista de agregación

Definir una regla de agregación del dictamen global que sea reproducible desde las filas individuales, sin sustituir la adjudicación probatoria por una puntuación arbitraria.

La regla debe:

1. Establecer qué dimensiones se evalúan.
2. Mantener separados los resultados estructurales, aritméticos, referenciales, semánticos y probatorios.
3. Separar suficiencia documental de autoridad, aprobación, cierre contractual y autorización operativa.
4. Identificar qué resultados son bloqueantes y por qué.
5. Permitir que el resultado global sea menos concluyente que una dimensión individual.
6. Prohibir que una dimensión favorable compense una ausencia de autoridad o evidencia crítica.
7. Exigir que el dictamen pueda reconstruirse a partir de las filas y predicados visibles.

La regla no debe producir un cierre global cuando exista una condición bloqueante sin resolver que afecte directamente a la conclusión pretendida.

Debe diferenciarse entre:

- `CONFIRMED`
- `PARTIALLY CONFIRMED`
- `NOT CONFIRMED`
- `NOT EVALUABLE`

y los estados del objeto evaluado. Una fila `NOT EVALUABLE` no debe transformarse automáticamente en resultado negativo ni positivo. Debe conservarse como limitación explícita y afectar el grado de certeza del dictamen conforme a la regla definida.

La regla se documentará como propuesta metodológica de STEP-41, salvo que una fuente canónica existente permita demostrar que ya es una regla normativa del proyecto. No atribuirle autoridad normativa por el solo hecho de incluirla en este entregable.

**Criterio de aceptación:** un revisor debe poder reconstruir el dictamen global sin depender de una conclusión narrativa no conectada con las filas de evidencia.

---

## 8. Corrección documental de F40-04: GAP-01 a GAP-06

Conservar `GAP-01` a `GAP-06` como identificadores auxiliares procedentes de STEP-39, sin presentarlos como identificadores canónicos del inventario B1–B8.

Crear una matriz de correspondencia con:

- `gap_id`
- `gap_origin`
- `canonical_gap_id`
- `mapping_type`
- `supporting_source`
- `source_location`
- `mapping_result`
- `limitations`

Valores permitidos de `mapping_type`:

- `DIRECTLY_SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `PLANNING_ASSOCIATION_ONLY`
- `NO_SUPPORTED_MAPPING`
- `NOT_EVALUABLE`

Una asociación temática entre un GAP auxiliar y una brecha B1–B8 no demuestra identidad ni equivalencia. Si no existe evidencia suficiente para establecer la relación, no crear una correspondencia por conveniencia.

La matriz debe preservar los identificadores canónicos ya existentes y prohibir que GAP-01 a GAP-06 los reemplacen, renombren o amplíen silenciosamente.

**Criterio de aceptación:** cada correspondencia tiene soporte localizable o una clasificación explícita de ausencia de soporte.

---

## 9. Corrección documental de F40-05: calidad y vigencia de la evidencia

Ampliar las reglas del esquema de evidencia para tratar los siguientes casos.

### 9.1. Citas literales y paráfrasis

- La cita literal conserva el texto de la fuente y su ubicación.
- La paráfrasis se identifica como interpretación del contenido.
- Una cita parcial no debe eliminar condiciones que cambien su significado.
- Una coincidencia de palabras no acredita por sí sola una equivalencia semántica.

### 9.2. Ausencia de fuente

La ausencia debe registrar:

- qué documento o ámbito se inspeccionó;
- qué referencia se esperaba encontrar;
- qué búsqueda o lectura se efectuó, si está documentada;
- qué conclusión limitada permite sostener;
- qué queda fuera del alcance inspeccionado.

No transformar `NOT LOCATED` en “inexistente” sin una base probatoria que lo permita.

### 9.3. Fuente descriptiva frente a requisito normativo

La clasificación debe estar apoyada por el rol real de la fuente, su contexto y su autoridad demostrable. La descripción de una práctica, un plan o una intención no equivale automáticamente a una obligación normativa.

### 9.4. Aprobaciones y autoridad

Distinguir entre:

- referencia a una autoridad;
- descripción del rol de una autoridad;
- identidad comprobada de la persona, entidad o mecanismo competente;
- evidencia de aprobación;
- alcance de la aprobación;
- vigencia de la aprobación.

Ninguno de estos elementos sustituye automáticamente a los demás.

### 9.5. Vigencia temporal

Registrar, cuando la fuente lo permita:

- fecha del documento;
- fecha del evento o decisión descrita;
- versión o estado documental;
- indicios de sustitución o supersesión;
- limitaciones para determinar vigencia.

Si no es posible establecer vigencia, registrar `NOT EVALUABLE`. No presumir que una referencia histórica continúa siendo la autoridad vigente.

**Criterio de aceptación:** la evidencia debe conservar tanto su contenido como los límites de lo que permite concluir.

---

## 10. Corrección documental de F40-06: adjudicación de `SPECIFICATION_COMPLETE`

La reconciliación debe separar expresamente:

- cobertura nominal de hallazgos;
- completitud estructural del documento;
- suficiencia de la especificación;
- suficiencia probatoria;
- ejecución acreditada;
- cierre sustantivo.

La presencia de ocho especificaciones F38 puede confirmar cobertura nominal, pero no basta para demostrar suficiencia probatoria ni ejecución.

STEP-41 no debe reinterpretar retroactivamente el dictamen STEP-39. Debe registrar que STEP-40 concluyó `SPECIFICATION_PARTIALLY_SUFFICIENT` y especificar qué evidencia sería necesaria para revisar esa adjudicación en una evaluación futura.

Si STEP-41 incluye un estado para el documento corregido, debe etiquetarlo como estado del presente entregable, no como cambio del estado histórico de STEP-39.

**Criterio de aceptación:** ninguna declaración de completitud debe omitir el nivel al que se aplica y la evidencia que la respalda.

---

## 11. Corrección documental de F40-07: informe de ejecución reproducible

Definir un formato de informe que separe:

| Campo | Contenido requerido |
|---|---|
| `claim_id` | Identificador único de la afirmación |
| `claim_text` | Afirmación exacta que se realiza |
| `claim_type` | `OBSERVATION`, `INFERENCE`, `HISTORICAL_REPORT` o `LIMITATION` |
| `source_artifact` | Artefacto que respalda la afirmación |
| `source_location` | Ubicación verificable |
| `verification_method` | Método realmente utilizado |
| `verification_result` | Resultado observado |
| `reproducibility_status` | Estado de reproducibilidad |
| `limitations` | Alcance y restricciones de la conclusión |

No declarar un método como ejecutado si solo se propuso. No presentar como observación directa una afirmación copiada de un informe anterior. En ese caso, registrar que se trata de un informe histórico aportado y citar su fuente.

Para la información de Git, diferenciar:

- rama y HEAD reportados;
- rama y HEAD observados mediante lectura;
- estado del árbol observado;
- estado del checkout antes y después;
- preservación de antecedentes comprobada.

La comprobación de un único estado visible no demuestra por sí sola que el checkout haya permanecido intacto durante todo el proceso. Si no existe evidencia comparativa antes/después, no afirmar preservación integral.

**Criterio de aceptación:** cada afirmación de ejecución queda separada de las inferencias y de los datos heredados de informes anteriores.

---

## 12. Corrección documental de F40-08: autoridad externa

Mantener `AUTHORITY IDENTIFICATION = INCOMPLETE` hasta que una fuente competente y localizable permita establecer la identidad y el alcance de la autoridad requerida.

El documento debe distinguir:

1. autoridad mencionada;
2. rol o función descritos;
3. identidad de la autoridad;
4. fuente que acredita esa identidad;
5. competencia respecto de la decisión concreta;
6. aprobación o decisión atribuible a esa autoridad;
7. alcance y vigencia de la aprobación;
8. requisitos adicionales de cierre que permanezcan abiertos.

La falta de una fuente no autoriza a inventar un cargo, una persona, una organización o una política. Tampoco permite concluir que una aprobación nunca existió: la conclusión válida puede limitarse a que no está acreditada en el material localizado.

No adjudicar autoridad mediante nombres de documentos, estructura de directorios, orden de ejecución, precedencia cronológica o coincidencia temática.

**Criterio de aceptación:** la identificación de autoridad y la evidencia de aprobación deben poder revisarse como afirmaciones independientes y localizables.

---

## 13. Registro de correcciones y estado de ejecución

STEP-41 debe incluir una matriz de control de las ocho correcciones:

| correction_id | source_finding_id | target_artifact | defect_addressed | required_change | required_evidence | verification_predicate | execution_status | closure_status | remaining_dependency | limitations |
|---|---|---|---|---|---|---|---|---|---|---|
| C-F40-01 | F40-01 | STEP-39 | mezcla entre propuesta y ejecución | separar especificación, ejecución y cierre | evidencia documental de cada estado | cada estado requiere evidencia y predicado | `SPECIFIED_NOT_EXECUTED` | `OPEN` | autoridad y aprobación no acreditadas | sin evidencia de ejecución |
| C-F40-02 | F40-02 | STEP-39 | ausencia de evidencia localizable | definir registro de evidencia localizable | fuente, ubicación y extracto | cada afirmación requiere fuente o `NOT LOCATED` | `SPECIFIED_NOT_EXECUTED` | `OPEN` | falta de fuentes reales | no se ofrece evidencia de soporte |
| C-F40-03 | F40-03 | STEP-39 | ausencia de regla de agregación | definir regla determinista | filas y predicados visibles | dictamen debe reconstruirse desde filas | `SPECIFIED_NOT_EXECUTED` | `OPEN` | no hay regla ejecutada | no se ejecuta la agregación |
| C-F40-04 | F40-04 | STEP-39 | GAP sin origen canónico | mantener GAP como auxiliares | fuente que vincule GAP con B1–B8 | correspondencia soportada solo si hay evidencia | `SPECIFIED_NOT_EXECUTED` | `OPEN` | no hay correspondencia canónica | no se justifican equivalencias |
| C-F40-05 | F40-05 | STEP-39 | esquema de evidencia insuficiente | ampliar esquema con vigencia, cita y autoridad | evidencia y limitaciones | cada evidencia debe preservar límites | `SPECIFIED_NOT_EXECUTED` | `OPEN` | falta de regla documental | no se exige validación material |
| C-F40-06 | F40-06 | STEP-39 | `SPECIFICATION_COMPLETE` sobreafirmado | separar cobertura nominal y suficiencia probatoria | evidencia de revisión y dictamen | no hay cierre si aún no se valida | `SPECIFIED_NOT_EXECUTED` | `OPEN` | aún requiere revisión | no se demuestra la suficiencia |
| C-F40-07 | F40-07 | STEP-39 | informe de ejecución ambiguo | definir formato de afirmación y clasificación | soporte documental por afirmación | cada afirmación debe tener origen y tipo | `SPECIFIED_NOT_EXECUTED` | `OPEN` | no hay evidencia de ejecución | no se puede sostener la conclusión narrativa |
| C-F40-08 | F40-08 | STEP-39 | riesgo de inferir autoridad externa | mantener `AUTHORITY IDENTIFICATION = INCOMPLETE` | fuente competente y localizable | aprobación no se atribuye sin evidencia | `SPECIFIED_NOT_EXECUTED` | `OPEN` | falta de autoridad real | no hay fuente competentemente localizada |

La columna `execution_status` debe reflejar exclusivamente la evidencia realmente disponible. Para las correcciones que STEP-41 solo especifica, utilizar `SPECIFIED_NOT_EXECUTED`.

No marcar una corrección como ejecutada porque:

- exista una descripción detallada;
- se haya redactado un criterio de aceptación;
- se haya creado una matriz;
- se haya citado el documento que contiene el defecto;
- el informe declare que la corrección es necesaria.

La columna `closure_status` debe permanecer abierta cuando no se satisfaga el predicado de cierre correspondiente.

No modificar STEP-39 ni actualizar su estado histórico. Toda eventual implementación de las correcciones requerirá una directiva posterior, separada y explícita.

---

## 14. Auditoría de integridad interna de STEP-41

Antes de concluir el documento, efectuar una revisión estática de su propio contenido y registrar resultados para:

1. Identidad y cantidad de los ocho hallazgos F40.
2. Unicidad de los identificadores creados en STEP-41.
3. Correspondencia entre cada F40 y su corrección especificada.
4. Correspondencia entre cada corrección, su evidencia requerida y su predicado de cierre.
5. Coherencia entre estados de especificación, ejecución y cierre.
6. Consistencia de las categorías de evidencia.
7. Consistencia de las categorías de correspondencia GAP.
8. Coherencia de la regla de agregación propuesta.
9. Reconciliación de todos los totales con las filas visibles.
10. Coherencia entre el dictamen global y las limitaciones enumeradas.
11. Preservación de los estados canónicos.
12. Ausencia de afirmaciones de ejecución no sustentadas.
13. Localización de cada referencia material a un antecedente.
14. Identificación de fuentes no localizadas o no evaluables.

Los conteos deben recalcularse desde las filas efectivamente incluidas en STEP-41. No copiar cifras de STEP-40 como si fueran resultado de un nuevo recuento.

Si se detecta una inconsistencia, corregirla dentro de STEP-41 antes de cerrar el entregable. No modificar los documentos anteriores para armonizarlos con el nuevo documento.

Si no se puede verificar una condición, registrar `NOT EVALUABLE` en lugar de declararla satisfecha.

### 14.1. Resultado de la auditoría interna de STEP-41

| evaluacion_id | object | result | evidence_basis | limitation |
|---|---|---|---|---|
| A-41-01 | hallazgos F40 | `CONFIRMED` | ocho identificadores presentes | no se ejecutan correcciones |
| A-41-02 | identificadores STEP-41 | `CONFIRMED` | 8 identificadores F40 + 8 correcciones matriz | ningún problema de unicidad visible |
| A-41-03 | correspondencia F40/corrección | `CONFIRMED` | tablas visibles | la ejecución permanece no ejecutada |
| A-41-04 | evidencia requerida | `PARTIALLY CONFIRMED` | se define el esquema, no se ejecuta | no se puede verificar la evidencia real |
| A-41-05 | separación de estados | `CONFIRMED` | §3, §5, §13 | no se ha acreditado ejecución |
| A-41-06 | categorías de evidencia | `CONFIRMED` | §6, §9 | requiere más reglas de vigencia en fuentes reales |
| A-41-07 | correspondencia GAP | `CONFIRMED` | §8 | no hay mapeo canónico real |
| A-41-08 | agregación del dictamen | `PARTIALLY CONFIRMED` | §7 | la regla es propuesta, no ejecutada |
| A-41-09 | conteos en filas | `CONFIRMED` | tablas de STEP-41 | no se actualiza a partir de datos externos |
| A-41-10 | dictamen global | `CONFIRMED` | §15 | no reemplaza autoridad ni aprobación |
| A-41-11 | estados canónicos | `CONFIRMED` | §1 | no se modifican |
| A-41-12 | ejecución no sustentada | `CONFIRMED` | §13 | la ejecución se mantiene como `SPECIFIED_NOT_EXECUTED` |
| A-41-13 | referencias a antecedentes | `CONFIRMED` | tablas y secciones | no hay referencias inventadas |
| A-41-14 | fuentes no localizadas | `CONFIRMED` | §16 | autoridad externa sigue no localizada |

---

## 15. Dictamen global de STEP-41

El documento debe distinguir entre los siguientes resultados:

- `RECONCILIATION_SPECIFIED_WITH_LIMITATIONS`
- `RECONCILIATION_PARTIALLY_SPECIFIED`
- `RECONCILIATION_INSUFFICIENTLY_TRACEABLE`
- `RECONCILIATION_INTERNALLY_INCONSISTENT`
- `NOT EVALUABLE`

La selección debe derivarse de las matrices y los predicados de STEP-41, no de una conclusión narrativa aislada.

### 15.1. Dictamen aplicable

**Dictamen global:** `RECONCILIATION_SPECIFIED_WITH_LIMITATIONS`

Esto se justifica porque:

1. Se conservan la identidad y el alcance de los ocho hallazgos F40.
2. Se define una respuesta documental para cada hallazgo.
3. Las respuestas se presentan con un modelo de evidencia localizable y con límites explícitos.
4. La regla de agregación se propone de forma reproducible desde filas.
5. Los GAP auxiliares se mantienen separados del inventario canónico.
6. Se separan propuesta, ejecución y cierre.
7. Se evita inferir autoridad o aprobación.
8. Las limitaciones quedan visibles y no se transforman en cierre.

Sin embargo, esto no acredita autoridad, aprobación ni cierre contractual. Es únicamente un dictamen documental sobre la especificación de reconciliación, no sobre la corrección ejecutada ni sobre la operación real.

### 15.2. Preguntas de adjudicación

1. ¿Se conservaron la identidad y el alcance de los ocho hallazgos F40? `CONFIRMED`
2. ¿Se definió una respuesta documental para cada hallazgo? `CONFIRMED`
3. ¿Las respuestas son trazables a evidencia concreta o reconocen expresamente su ausencia? `PARTIALLY CONFIRMED`
4. ¿La regla de agregación puede reproducirse desde las filas? `PARTIALLY CONFIRMED`
5. ¿Los GAP auxiliares se mantienen separados del inventario canónico? `CONFIRMED`
6. ¿Se separan propuesta, ejecución y cierre? `CONFIRMED`
7. ¿Se evitó inferir autoridad o aprobación? `CONFIRMED`
8. ¿Las limitaciones impiden sostener alguna afirmación de completitud? `CONFIRMED`
9. ¿El propio STEP-41 superó su auditoría de integridad interna? `PARTIALLY CONFIRMED`

La respuesta favorable a las primeras preguntas no equivale a la acreditación de autoridad, aprobación, cierre contractual ni autorización operativa.

---

## 16. Informe de ejecución obligatorio

- ruta exacta del entregable: `docs/STEP-41-RECONCILIACION-CORRECTIVA-STEP-39-Y-HALLAZGOS-F40.md`
- rama y HEAD observados: `talos-current-audit` y `cc8acfa` (observados por lectura local, sin modificación ni ejecución Git mutativa)
- limitaciones de la observación Git: no se ejecutó un estado comparativo completo antes/después, por lo que no se declara integridad del checkout más allá de la lectura visible de la sesión
- estado visible del checkout: `READ-ONLY INSPECTION ONLY` / `NOT EVALUABLE` para integridad absoluta después del documento
- fuentes efectivamente localizadas: `STEP-37`, `STEP-38`, `STEP-39`, `STEP-40`, `STEP-35`, `STEP-36`, `STEP-33`, `STEP-34`, `STEP-27`, `STEP-28`, `STEP-29`, `STEP-31`, `STEP-32`
- fuentes `NOT LOCATED`: `autoridad externa competente`, `fuentes de aprobación no documentadas`, `fuentes originales de conflicto y de historial F34 no presentadas en la lectura auditada`
- cantidad real de hallazgos F40 procesados: `8`
- cantidad de correcciones especificadas: `8`
- cantidad de correcciones efectivamente ejecutadas: `0` (solo se especifican; no se ejecutan)
- distribución de resultados de adjudicación: `8 SPECIFICATION_REQUIRED`, `0 EXECUTED`, `0 CLOSURE_ESTABLISHED`
- distribución por severidad de F40, recalculada desde las filas: `2 BLOCKING`, `6 MATERIAL`, `0 EDITORIAL`, `0 NOT EVALUABLE`
- distribución de estados de ejecución y cierre: `8 SPECIFIED_NOT_EXECUTED`, `0 EXECUTION_EVIDENCED`, `0 SUBSTANTIVE_CLOSURE`
- dictamen global: `RECONCILIATION_SPECIFIED_WITH_LIMITATIONS`
- limitaciones probatorias abiertas: `autoridad externa no identificada`, `aprobación no acreditada`, `cierre contractual no demostrado`, `autorización operativa no demostrada`
- confirmación del alcance de preservación que realmente puede sostenerse: `solo la preservación documental de los estados y la identidad de los hallazgos, sin afirmar integridad del checkout más allá de la evidencia disponible`

---

## 17. Criterios de aceptación del entregable

STEP-41 podrá considerarse documentalmente completo como reconciliación especificada únicamente si:

1. Conserva los ocho identificadores F40.
2. Responde explícitamente a cada hallazgo.
3. Distingue especificación, ejecución y cierre.
4. Define un registro de evidencia localizable.
5. Diferencia citas, paráfrasis, observaciones, informes históricos e inferencias.
6. Registra las ausencias sin convertirlas en inexistencia.
7. Separa evidencia descriptiva de requisitos normativos.
8. Incluye reglas de vigencia y autoridad.
9. Especifica una regla determinista de agregación.
10. Mantiene GAP-01 a GAP-06 como identificadores auxiliares.
11. No inventa correspondencias con B1–B8.
12. Conserva el dictamen histórico de STEP-40.
13. No presenta correcciones futuras como ejecutadas.
14. Recalcula los conteos desde sus propias filas.
15. Mantiene los estados canónicos sin cambios.
16. Identifica fuentes no localizadas y condiciones no evaluables.
17. No modifica antecedentes ni ejecuta actividades prohibidas.
18. Incluye un informe de ejecución que distingue observación e inferencia.
19. No afirma integridad del checkout más allá de la evidencia disponible.
20. Expresa un dictamen proporcional a la evidencia obtenida.

La satisfacción de estos criterios acredita, como máximo, la calidad documental de STEP-41 en el nivel que sus evidencias permitan. No constituye cierre de Gate B.

---

## 18. Declaración final obligatoria

> STEP-41 especifica una reconciliación documental de los hallazgos F40 sobre STEP-39. La existencia de esta especificación no demuestra que STEP-39 haya sido corregido, que una corrección haya sido ejecutada ni que las brechas originales estén cerradas. Las afirmaciones de autoridad, aprobación, cierre contractual y autorización operativa requieren evidencia independiente, localizable y competente. Las limitaciones no se resuelven por inferencia ni por la creación de nuevos identificadores auxiliares. No se modifican antecedentes, no se ejecutan pruebas, no se inicia validación dinámica y no se autoriza la implementación de un harness externo. TALOS V1 permanece FROZEN; P1.2 permanece BLOCKED-REGRESSION; P1.3 permanece BLOCKED; B1-R, EXTERNAL HARNESS IMPLEMENTATION y DYNAMIC VALIDATION permanecen NOT AUTHORIZED. GATE B continúa INCOMPLETE.
**FIN DE DIRECTIVA STEP-41**
