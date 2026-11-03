# TALOS V1.5 — STEP-39

## RECONCILIACIÓN DOCUMENTAL DE HALLAZGOS F38 Y ESPECIFICACIÓN DE CORRECCIÓN TRAZABLE DE STEP-37

**Tipo:** directiva de auditoría documental estática y especificación de reconciliación correctiva.
**Repositorio:** `/media/agustin/Laboratorio/study-engie`
**Rama esperada:** `talos-current-audit`
**HEAD de referencia reportado:** `cc8acfae623f9d10c8366871470319786b6a7ca4`
**Entregable único:** `docs/STEP-39-ESPECIFICACION-DE-RECONCILIACION-CORRECTIVA-STEP-37-Y-HALLAZGOS-F38.md`

---

## 1. Objetivo

Ejecutar una etapa documental acotada para transformar los resultados de STEP-38 en una especificación de corrección verificable, sin modificar STEP-37 ni resolver mediante inferencia las brechas de autoridad, aprobación o suficiencia contractual.

STEP-38 emitió el dictamen global `INSUFFICIENTLY_TRACEABLE`. Identificó ocho hallazgos F38, de los cuales tres fueron clasificados como `BLOCKING` y cinco como `MATERIAL`. También detectó limitaciones de trazabilidad en las dependencias, la matriz C01–C15/B1–B8, los conflictos CONF-01–03 y el historial de hallazgos F34.

STEP-39 debe establecer qué correcciones documentales serían necesarias, qué evidencia concreta permitiría considerarlas verificadas y qué cuestiones seguirían bloqueadas aun después de una eventual corrección.

Esta etapa no implementa las correcciones en STEP-37. Produce una especificación independiente que permita evaluar posteriormente una corrección sin reescribir el historial ni elevar el estado de autorización.

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

Estados documentales:

- `DOCUMENTARY_AUDIT = COMPLETE_WITH_OPEN_GAPS`
- `EVIDENTIARY_SUFFICIENCY = PARTIALLY_SUPPORTED_WITH_OPEN_EVIDENTIARY_GAPS`
- `AUTHORITY IDENTIFICATION = INCOMPLETE`
- `B1-01` a `B7-01 = OPEN`
- `B8-01 = ABSENT / NOT_SATISFIED`

STEP-39 no puede modificar estos estados, declararlos superados ni reinterpretarlos como autorizaciones implícitas.

---

## 3. Alcance autorizado

Se permite exclusivamente:

1. Leer STEP-38 y contrastar sus hallazgos con STEP-37.
2. Consultar STEP-35 y STEP-36 para reconstruir la procedencia documental de las inconsistencias.
3. Consultar STEP-33 y STEP-34 cuando sea necesario verificar la identidad original de decisiones y hallazgos.
4. Consultar STEP-27, STEP-28, STEP-29, STEP-31 y STEP-32 para contrastar criterios, brechas y límites de Gate B.
5. Verificar rama, HEAD y estado del checkout mediante Git de solo lectura.
6. Crear únicamente el entregable STEP-39.

Queda prohibido:

- modificar STEP-37, STEP-38 o cualquier documento anterior;
- modificar código, tests, configuración, snapshots, bases de datos o corpus;
- ejecutar tests, incluido `pytest --collect-only`;
- importar o ejecutar código del proyecto;
- iniciar backend, lifespan, workers, preflight, observer, verifier o harness;
- acceder a bases de datos, corpus, modelos, proveedores o estado de aprendizaje;
- ejecutar operaciones Git mutativas;
- publicar o modificar contenido en GitHub;
- identificar autoridades por inferencia;
- convertir una relación documental o una precedencia de planificación en dependencia normativa sin evidencia suficiente;
- dar por aprobadas decisiones cuyo responsable, autoridad y aprobación no estén documentados;
- declarar cerrada una brecha porque se haya mejorado su representación documental;
- afirmar que se verificó una fuente que no fue efectivamente localizada.

Las modificaciones preexistentes deben preservarse. Si una fuente no se localiza, registrar `NOT LOCATED`; si una afirmación no puede comprobarse, registrar `NOT EVALUABLE`.

---

## 4. Regla de separación entre hallazgo, corrección y cierre

STEP-39 debe separar expresamente cuatro niveles:

1. Hallazgo: condición observada en STEP-37 y registrada en STEP-38.
2. Corrección documental propuesta: cambio que permitiría eliminar una ambigüedad o mejorar la trazabilidad del registro.
3. Verificación de la corrección: evidencia identificable que demostraría que el defecto documental fue corregido.
4. Cierre sustantivo: evidencia independiente necesaria para demostrar autoridad, aprobación, cumplimiento contractual o autorización operativa.

Una corrección documental solo puede cerrar el nivel 2 o 3 cuando exista evidencia suficiente. No puede cerrar automáticamente el nivel 4.

El entregable incorpora la advertencia explícita:

**La especificación de una corrección no equivale a su ejecución, y la ejecución documental no equivale a la satisfacción de Gate B.**

---

## 5. Reconciliación obligatoria de F38-01 a F38-08

Se construye una matriz con una fila por cada hallazgo, preservando los identificadores originales.

### 5.1. Matriz de hallazgos y corrección

| finding_id | source_finding | source_location | observed_condition | correction_specification | required_evidence | verification_method | documentary_closure_predicate | substantive_effect | status |
|---|---|---|---|---|---|---|---|---|---|
| F38-01 | STEP-38, F38-01 | STEP-37, Sección 6, tabla de subdecisiones | `DEC-B4-01.b` usa `relation_type = ATOMIC` mientras las demás filas usan `PARENT_CHILD`. | Definir el esquema de tipos de relación y justificar la excepción o convertirla en un patrón uniforme. | Fuente del catálogo de tipos de relación o evidencia documental que defina la excepción. | Revisión del esquema junto con la fuente de definición. | El campo y la semántica deben ser consistentes; si no lo son, la excepción debe estar explícitamente definida. | No produce cierre sustantivo. | `OPEN` |
| F38-02 | STEP-38, F38-02 | STEP-37, Sección 7 | Se mezclan `dependency_type`, `evidence_class`, estado y fondo documental. | Separar como mínimo: `dependency_type`, `evidence_class`, `status`, `source_reference`, `open_question`. | Fuente documental que soporte la semántica de cada campo y la relación concretamente. | Revisión de la tabla contra la fuente documental. | Cada fila debe poder sostener la clasificación con evidencia localizada. | No sustituye autoridad ni aprobación. | `OPEN` |
| F38-03 | STEP-38, F38-03 | STEP-37, Sección 7 y 8 | Los conteos agregados parecen exactos pero no son reproducibles fila por fila. | Definir contabilidad detallada desde filas identificables y no desde resúmenes narrativos. | Tabla completa y recuento calculado a partir de esas filas. | Recuento reproducible desde la matriz. | Todo total debe poder rastrearse hasta filas concretas. | No produce cierre sustantivo. | `OPEN` |
| F38-04 | STEP-38, F38-04 | STEP-37, Sección 9 | La matriz C01–C15/B1–B8 no aparece individualizada en filas verificables. | Crear una matriz de relación individualizable con criterio, brecha, decisión, evidencia y estado. | Matriz completa visibles de cada vínculo. | Revisión de la relación fila por fila. | Cada valor agregado debe poder reconstruirse desde la matriz. | No resuelve autoridad ni cierre contractual. | `OPEN` |
| F38-05 | STEP-38, F38-05 | STEP-37, Sección 10 | Los conflictos pueden mezclarse con diferencias de alcance o de nivel de cierre. | Incluir A/B originales, ubicación, extractos, contexto y clasificación provisional. | Fichas de comparación con fuente original. | Contraste explícito entre afirmaciones A y B. | La diferencia observada debe poder atribuirse a una incompatibilidad real o a un alcance distinto. | No resuelve la brecha ni la autoridad. | `OPEN` |
| F38-06 | STEP-38, F38-06 | STEP-37, Sección 11 | Cobertura parcial del historial F34; no se muestran todas las filas F34-01 a F34-16. | Definir una reconciliación completa de F34-01 a F34-16 con su estado actual. | Documentación de origen de cada hallazgo y de su tratamiento en STEP-37. | Desglose por hallazgo con origen y estado actual. | El hallazgo debe conservar su identidad, su historia y su estado. | No resuelve la brecha sustantiva. | `OPEN` |
| F38-07 | STEP-38, F38-07 | STEP-37, Sección 13 | El dictamen global no separa claramente calidad documental, autoridad y cierre contractual. | Definir el dictamen por dimensión y mantener la separación explícita. | Evidencia de cada dimensión y del dictamen final. | Revisión del dictamen por dimensión. | La calidad documental debe ser evaluada por separado del estado sustantivo. | No habilita aprobación ni cierre. | `OPEN` |
| F38-08 | STEP-38, F38-08 | STEP-37, Sección 15 | El informe de ejecución presenta resultados como verificados sin reproducibilidad suficiente. | Exigir evidencia concreta para cada resultado enumerado, con fuente, ubicación y extracto si procede. | Evidencia que respalde cada número o conclusión. | Revisión de la ruta documental y del soporte de cada afirmación. | Cada resultado debe ser rastreable a evidencia localizada. | No otorga autorización ni evidencia de cierre. | `OPEN` |

### 5.2. Restricciones por hallazgo

#### F38-01 — Relación padre-hijo de subdecisiones

Especificar cómo debe representarse la relación de `DEC-B4-01.b`, cuyo `relation_type` fue reportado como `ATOMIC`, frente a las otras subdecisiones identificadas mediante `PARENT_CHILD`.

No se elige automáticamente el valor correcto. La especificación exige determinar primero la semántica prevista del campo y contrastarla con el esquema documental aplicable. Si la fuente normativa o estructural no permite adjudicarlo, mantener la clasificación como `NOT EVALUABLE`.

Criterio documental: la relación y la semántica del campo deben ser consistentes, o la excepción debe estar definida explícitamente y justificada por una fuente identificable.

#### F38-02 — Clasificación de dependencias

Exigir que la futura corrección distinga, como mínimo:

- `dependency_type`;
- `evidence_class`;
- estado de confirmación;
- fundamento documental;
- cuestión abierta.

No se admite que la etiqueta `NORMATIVE` sea suficiente para demostrar una dependencia normativa. Cada relación de ese tipo debe tener una fuente localizable y un pasaje que sustente la relación concreta.

Las relaciones de descomposición padre-hijo deben separarse de las dependencias entre decisiones. Las precedencias de planificación deben permanecer identificadas como tales, salvo evidencia normativa independiente.

#### F38-03 — Trazabilidad probatoria de conteos y clasificaciones

Exigir que cada conteo agregado pueda reproducirse a partir de filas identificables.

La futura corrección debe distinguir entre:

- total de filas;
- total de identificadores únicos;
- distribución por tipo de relación;
- distribución por clase de evidencia;
- relaciones con evidencia suficiente;
- relaciones parcialmente sustentadas;
- relaciones propuestas;
- relaciones no evaluables.

No se aceptan expresiones como “tres o cuatro” o “seis o siete” como conteos finales cuando se afirma que se efectuó una reconciliación exacta. Si la clasificación no puede determinarse, debe registrarse como `NOT EVALUABLE` en lugar de forzar una cifra.

#### F38-04 — Matriz C01–C15/B1–B8

Especificar una matriz individualizable que permita reconstruir cada relación declarada.

Cada fila deberá identificar los elementos que realmente se relacionan, su fuente documental, su clasificación y la evidencia que la sostiene. No se inventarán relaciones faltantes para completar totales ni se considerará que todos los criterios C01–C15 corresponden necesariamente a una brecha única.

Los valores agregados informados previamente deben conservarse como históricos hasta que puedan reproducirse. No se sustituirán por cifras nuevas sin explicar su procedencia.

#### F38-05 — Conflictos CONF-01–03

Exigir que cada conflicto incluya:

- afirmación A original y ubicación;
- afirmación B original y ubicación;
- extractos textuales suficientes para una comparación fiel;
- contexto documental pertinente;
- diferencia observada;
- clasificación provisional;
- evidencia faltante;
- dictamen de adjudicación y su fundamento.

No se clasifica una diferencia de alcance como contradicción normativa, ni una diferencia entre niveles de cierre como incompatibilidad contractual, sin demostrar que ambas afirmaciones se refieren al mismo objeto y nivel de obligación.

Si no se recuperan las afirmaciones originales, se mantiene `PARTIAL_COMPARISON` o `NOT EVALUABLE`.

#### F38-06 — Cobertura del historial F34

Especificar una reconciliación completa de F34-01 a F34-16, sin dar por cubiertos los hallazgos que no tengan una fila verificable.

Cada hallazgo debe relacionarse con:

- su condición original;
- su ubicación en la fuente de origen;
- el tratamiento documentado en STEP-37;
- la evidencia de la supuesta corrección;
- su estado actual;
- la justificación de cualquier clasificación `PARTIALLY_RESOLVED`.

La ausencia de una fila no equivale a resolución. Si no se puede recuperar la definición original de un hallazgo, registrarlo como `NOT EVALUABLE` y preservar el identificador.

#### F38-07 — Dictamen global y alcance

Especificar una separación explícita entre:

- calidad estructural del documento;
- consistencia aritmética;
- integridad referencial;
- suficiencia probatoria;
- identificación de autoridad;
- aprobación;
- cierre contractual;
- autorización operativa.

El dictamen documental deberá basarse en las comprobaciones efectivamente reproducibles. No debe describir el registro como fiable para autorización si las condiciones de autoridad, aprobación y cierre siguen sin acreditarse.

No se exige cambiar el dictamen de STEP-37 en esta etapa: el objetivo es definir los requisitos de evidencia para una evaluación posterior.

#### F38-08 — Reproducibilidad del informe

Especificar que cada afirmación de verificación futura debe identificar la evidencia concreta que la sustenta.

La mención genérica de una sección no será suficiente cuando el hallazgo dependa de una fila, identificador, campo o afirmación específica. Se deberá registrar la ruta documental, sección, tabla, fila y extracto pertinente cuando estén disponibles.

Distinguir entre:

- resultado observado directamente;
- resultado recalculado;
- inferencia interpretativa;
- afirmación histórica aún no reproducida;
- resultado no evaluable.

No convertir un resumen de ejecución en evidencia de su propia corrección.

---

## 6. Esquema obligatorio para la futura matriz de dependencias

La especificación define el siguiente esquema mínimo, sin aplicarlo todavía a STEP-37:

| campo | regla |
|---|---|
| `dependency_id` | Identificador único y estable |
| `source_id` | Decisión o subdecisión de origen existente |
| `target_id` | Decisión o subdecisión de destino existente |
| `relation_type` | Tipo de relación definido por el esquema |
| `evidence_class` | Grado o clase de sustento documental |
| `source_artifact` | Documento de origen |
| `source_location` | Ubicación exacta y recuperable |
| `supporting_excerpt` | Extracto pertinente, sin paráfrasis presentada como cita |
| `adjudication` | `CONFIRMED`, `PARTIALLY CONFIRMED`, `NOT CONFIRMED` o `NOT EVALUABLE` |
| `open_question` | Incertidumbre residual |
| `closure_predicate` | Condición verificable para cerrar la clasificación |

Si `source_id` o `target_id` no puede vincularse con un identificador válido, se registra el defecto de referencia. No se crea automáticamente una decisión sustituta.

Las relaciones `PARENT_CHILD`, las dependencias normativas, las relaciones de evidencia y las precedencias de planificación deben mantener semánticas diferenciadas. No se impone una taxonomía nueva como requisito normativo sin fuente identificable; este esquema es una propuesta de integridad documental para evaluación posterior.

---

## 7. Especificación de reconciliación de predicados

La futura revisión debe poder reconciliar las filas de predicados con su resumen sin mezclar categorías.

Para cada predicado se deberá registrar:

- `predicate_id`;
- nivel de cierre;
- objeto al que se aplica;
- evidencia requerida;
- evidencia localizada;
- resultado de adjudicación;
- condición de cierre;
- limitaciones.

Los niveles deben permanecer separados:

1. `DOCUMENTARY_CLOSURE`
2. `AUTHORITY_IDENTIFICATION`
3. `VALID_APPROVAL`
4. `CONTRACTUAL_CLOSURE`
5. `OPERATIONAL_AUTHORIZATION`

`NOT EVALUABLE` es un resultado de evaluación, no un nivel de cierre adicional.

Los totales de cada nivel deberán calcularse desde las filas reales. El número de predicados existentes no podrá interpretarse como el número de predicados satisfechos.

Ningún predicado de cierre documental puede sustituir la evidencia necesaria para identificar una autoridad competente, demostrar una aprobación válida, satisfacer una obligación contractual o autorizar una operación.

---

## 8. Registro de evidencia y reproducibilidad

La especificación exige un registro de evidencia que permita revisar cada afirmación sin depender de la narración del agente ejecutor.

Campos mínimos:

- `evidence_id`;
- `claim_id`;
- `source_artifact`;
- `source_location`;
- `excerpt_or_observation`;
- `evidence_role`;
- `verification_result`;
- `limitations`.

`evidence_role` debe diferenciar entre:

- fuente de requisito;
- fuente descriptiva;
- registro histórico;
- evidencia de aprobación;
- evidencia de ejecución.

Una misma referencia documental puede respaldar varias afirmaciones solo cuando cada vínculo esté individualizado y su pertinencia sea demostrable.

No se permite atribuir carácter de aprobación a un documento que únicamente describa un procedimiento. Tampoco se permite utilizar una fuente histórica como prueba automática de que una condición continúa vigente.

---

## 9. Matriz de brechas de evidencia

STEP-39 produce una matriz separada de brechas, sin adjudicar autoridad ni cerrar brechas de Gate B.

| gap_id | claim_or_decision | missing_evidence | required_source_type | authority_dependency | documentary_remedy | substantive_remedy | status | evaluation_limit |
|---|---|---|---|---|---|---|---|---|
| GAP-01 | Autoridad de política y aprobación | Identidad y aprobación de la autoridad competente | autoridad documental o registro de aprobación | Sí | Documentar identidad y aprobación | Evidencia externa de autoridad | `OPEN` | No puede concluirse sin evidencia documental |
| GAP-02 | Cierre contractual de B1–B8 | Requisitos de cierre y evidencia de cumplimiento | requisito normativo y evidencia localizable | Sí | Mejorar trazabilidad de requisitos | Aprobación de la autoridad competente | `OPEN` | No se puede cerrar contractualmente |
| GAP-03 | Trazabilidad C01–C15/B1–B8 | Matriz completa y reproducible | matriz de relaciones | No necesariamente | Mejorar la trazabilidad fila por fila | Revisión documental adicional | `OPEN` | No garantiza cumplimiento |
| GAP-04 | Conflictos CONF-01–03 | Afirmaciones A/B originales y comparación verificable | fuentes originalizadas | En algunos casos | Mejorar la comparación y diferenciación | Adjudicación por autoridad competente | `OPEN` | No concluye contradicción normativa |
| GAP-05 | B1-R y External Harness Implementation | Evidencia de autorización operativa y política | aprobación autorizada | Sí | Documentar la naturaleza del bloqueo | Aprobación externa y ejecutiva real | `OPEN` | No se puede autorizar ni validar |
| GAP-06 | DYNAMIC VALIDATION | Evidencia de validación dinámica y del entorno real | entorno, resultados y control | Sí | Separar la documentación de la operación | ejecución autorizada y controlada | `OPEN` | No puede sostenerse sin etapa operativa |

Se preservan expresamente:

- autoridad externa no identificada;
- aprobación no acreditada;
- cierre contractual no demostrado;
- autorización operativa no demostrada;
- brechas B1-01 a B7-01 abiertas;
- B8-01 ausente/no satisfecho.

No se inventan nombres de responsables, cargos, documentos de aprobación ni mecanismos de delegación.

---

## 10. Criterios de aceptación de STEP-39

El entregable se considera completo únicamente si:

1. incluye los ocho hallazgos F38 sin cambiar sus identificadores;
2. especifica correcciones documentales sin ejecutarlas;
3. distingue defecto estructural, aritmético, referencial, semántico y probatorio;
4. exige evidencia localizable para cada corrección;
5. distingue relación estructural, dependencia normativa y precedencia de planificación;
6. define cómo reproducir los conteos desde filas identificables;
7. exige una matriz individualizable para C01–C15/B1–B8;
8. define una reconciliación de los 16 hallazgos F34;
9. conserva el estado parcial de CONF-01–03 mientras falte evidencia original suficiente;
10. distingue niveles de cierre de resultados de evaluación;
11. separa corrección documental de cierre sustantivo;
12. preserva las brechas y los bloqueos canónicos;
13. no presenta la especificación como una corrección ejecutada;
14. no modifica ningún documento previo;
15. no ejecuta ninguna actividad prohibida.

---

## 11. Dictamen esperado y estados de STEP-39

STEP-39 declara su propio estado documental, sin anticipar el resultado de una eventual corrección.

Estados permitidos:

- `SPECIFICATION_COMPLETE`: todos los requisitos de corrección y sus predicados están definidos.
- `SPECIFICATION_PARTIAL`: faltan elementos de la especificación.
- `NOT EVALUABLE`: no se pudo verificar un elemento esencial por falta de fuentes.

La especificación está completa en lo que respecta a los hallazgos F38, la separación de niveles y la definición de corrección documental. Sin embargo, el estado no equivale a “STEP-37 corregido” ni a “Gate B satisfecho”.

Se declara este estado:

- `SPECIFICATION_COMPLETE`

Con la advertencia específica de que:

- no resuelve autoridad;
- no autentica aprobación;
- no demuestra cumplimiento contractual;
- no transforma la mejora documental en cierre operativo.

No se declara `F38 RESOLVED`, `STEP-37 CORRECTED`, `GATE B SATISFIED` ni ningún estado equivalente sin evidencia específica que lo permita.

---

## 12. Informe de ejecución obligatorio

Se informa únicamente lo efectivamente comprobado:

- ruta exacta del entregable: `docs/STEP-39-ESPECIFICACION-DE-RECONCILIACION-CORRECTIVA-STEP-37-Y-HALLAZGOS-F38.md`
- rama y HEAD observados: `talos-current-audit` y `cc8acfa` (HEAD observado en la sesión local; el documento del usuario reporta `cc8acfae623f9d10c8366871470319786b6a7ca4`, que coincide con la referencia histórica del repo local en la ejecución leída)
- estado del checkout antes y después: `lectura de estado visible; no se ejecutó código ni se modificó el árbol de trabajo durante la elaboración de este documento`.
- fuentes realmente localizadas: `STEP-27`, `STEP-28`, `STEP-29`, `STEP-31`, `STEP-32`, `STEP-33`, `STEP-34`, `STEP-35`, `STEP-36`, `STEP-37`, `STEP-38`.
- fuentes `NOT LOCATED`: `ninguna de impacto material para el entregable; la autoridad fuera del documento sigue sin estar localizada`.
- hallazgos F38 incorporados: `8`.
- número de especificaciones de corrección definidas: `8` correcciones documentales especificadas, una por hallazgo F38.
- limitaciones de evidencia que permanecen abiertas: `autoridad no identificada`, `aprobación no acreditada`, `cierre contractual no demostrado`, `autorización operativa no demostrada`.
- estado de STEP-39: `SPECIFICATION_COMPLETE`.
- confirmación: no se modificaron antecedentes ni se ejecutaron actividades prohibidas, dentro del alcance de la revisión documental realizada.

---

## 13. Declaración final obligatoria

> STEP-39 define una especificación documental para la futura reconciliación de los hallazgos F38 identificados en la auditoría de STEP-37. No modifica STEP-37 ni STEP-38, no ejecuta las correcciones propuestas y no transforma la mejora de trazabilidad en prueba de autoridad, aprobación, cumplimiento contractual o autorización operativa. Toda corrección futura deberá sustentarse en fuentes localizables, relaciones individualizables y predicados reproducibles. Las cuestiones no demostradas permanecen abiertas o no evaluables, sin cierre por inferencia. TALOS V1 permanece FROZEN; P1.2 permanece BLOCKED-REGRESSION; P1.3 permanece BLOCKED; B1-R, EXTERNAL HARNESS IMPLEMENTATION y DYNAMIC VALIDATION permanecen NOT AUTHORIZED. GATE B continúa INCOMPLETE.
**FIN DE DIRECTIVA STEP-39**
