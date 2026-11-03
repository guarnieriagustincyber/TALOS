# Diagnóstico multi-cuaderno de TALOS y plan para continuar

**Fecha:** 2026-09-28
**Base de la inspección inicial:** `main`, commit `ea060ad`
**Propósito:** aclarar el alcance del historial de NotebookLM, auditar las fases
de mejora pedagógica contra el código y definir las correcciones necesarias
antes de avanzar.

Para estado integrado actualizado al 2026-09-30 y secuencia completa de cierre,
consultar el [Plan maestro de estabilización y cierre de TALOS](./PLAN_MAESTRO_CIERRE_TALOS.md).
Este diagnóstico conserva la evidencia detallada de perfiles y sus gates.

## 1. Dictamen ejecutivo

La dirección general es correcta: TALOS ya tiene conceptos de cuaderno,
currículum, fuentes autorizadas, Knowledge Components (KCs), estado del
estudiante y una política común de interacción. También existen configuraciones
curriculares distintas para programación, Sistemas Operativos, Tratamiento de
Datos y Telecomunicaciones.

La inspección inicial encontró brechas en el fallback curricular, los supuestos
del prompt base y la etiqueta de `fadena-std`. La revisión del árbol de trabajo
del 2026-09-29 confirma que **los mecanismos centrales H1–H3 ya se corrigieron
localmente**: el fallback es neutral, la selección exige identidad curricular
exacta y `fadena-std` usa la etiqueta del catálogo. Se añadió una matriz de
perfiles por HTTP/SSE hasta el prompt del backend, además de una prueba de
precedencia del contrato custom y restricciones explícitas del turno. La
separación pedagógica todavía no está aceptada de punta a punta: esas pruebas
usan evidencia simulada; faltan la reconciliación de identidad/fuentes en los
registros efectivos y la integración del retrieval/ACL real con el prompt.

Por lo tanto:

- **F1–F4:** implementadas y con pruebas deterministas de resolver y armado de
  prompts; todavía no se ha probado que un modelo real obedezca todas las
  políticas en distintos currículos.
- **F5:** la implementación de historial, procedencia, referencias y avisos de
  discrepancia está extendida y comprometida; aún falta cerrar los criterios de
  aceptación que dependen de memoria, ejercicios y no mutación de estado.
- **F6:** hay infraestructura previa de streaming y pruebas de componentes,
  pero se identificó un hueco de terminación visible en UI: una respuesta
  truncada puede parecer completada.
- **F7:** pendiente. La evaluación futura debe cubrir varios currículos; una
  sola sesión de programación no valida el comportamiento multi-cuaderno.

**Conclusión actualizada:** no repetir los fixes centrales H1–H3; completar la
aceptación E2E del Gate B, luego cerrar F5 y F6 con sus gates, ejecutar la
regresión consolidada y recién entonces preparar F7. La implementación local
no es aceptación formal ni certificación del producto.

## 2. Cómo interpretar el historial de NotebookLM

El archivo local `chatNotebookLM.txt` corresponde a **un cuaderno y un
currículum concretos: programación y fundamentos de la Fase 0**. Es una
referencia valiosa de la dinámica de estudio que el usuario llevó adelante, no
un contrato universal para cualquier materia ni una autoridad técnica.

Se debe usar para extraer:

- cómo se organiza una secuencia de estudio larga y cómo se retoma un punto
  previo;
- cuándo el estudiante busca una explicación, un ejercicio, una pista, una
  revisión o una solución completa;
- qué tan útil resulta resolver primero en papel, y cuándo introducir
  pseudocódigo, diagramas o Python en **ese** currículo;
- cómo dar feedback accionable, cambiar la explicación cuando el estudiante no
  entiende y evitar saltar prematuramente a desafíos que dependen de
  herramientas aún no estudiadas;
- ejemplos anonimizados que puedan convertirse en casos de regresión
  pedagógica.

No se debe generalizar a otros cuadernos:

| Elemento del historial | Uso válido | No generalizar como regla |
|---|---|---|
| Guía socrática, pistas y corrección concreta | Principios de interacción que pueden transferirse, sujetos al pedido del turno | Prohibir toda respuesta directa o solución completa |
| Secuencia papel → pseudocódigo → Python | Convención posible para ejercicios del currículum de programación | Flujo obligatorio de todas las materias |
| Trazas de memoria, Stack Frames y diagramas de flujo | Representaciones pertinentes a ciertos temas de programación | Analogías o diagramas de RAM en cada explicación |
| Ejercicios de SO y seguridad dentro del curso | Casos de cruce entre materias que pueden evaluarse en contexto | Reetiquetar toda pregunta como programación o ciberseguridad |
| Respuestas de NotebookLM | Evidencia sobre la dinámica y material de prueba, con revisión crítica | Fuente de verdad técnica, cita, página o prueba de aprendizaje |

En particular, el transcript incluye simplificaciones técnicamente engañosas
sobre mutabilidad y paso de parámetros de Python. Sus respuestas no deben
convertirse automáticamente en oráculos. Se deben evaluar con fuentes
autorizadas y criterios técnicos independientes.

El archivo original permanece fuera del repositorio. No copiarlo ni incluir
pasajes extensos, datos personales, material de libros o respuestas completas
en datasets versionados. Conservar solo casos mínimos anonimizados y
metadatos de procedencia cuando se preparen pruebas.

## 3. Modelo de tutoría requerido

TALOS necesita una **política común de interacción** y un **perfil curricular
propio por cuaderno**, ambos subordinados al pedido explícito del turno.

### 3.1 Capas que deben distinguirse

1. **Política común del tutor:** honestidad sobre fuentes, tono claro, respeto
   por el pedido, guía sin sustitución cognitiva no solicitada, feedback
   accionable, manejo de incertidumbre y continuidad honesta.
2. **Perfil curricular del cuaderno:** materia, programa oficial, unidades,
   objetivos, secuencia, prerrequisitos y vocabulario.
3. **Perfil pedagógico/representacional de la materia:** prácticas y
   representaciones que pueden ayudar en ese currículum. Son opciones
   pertinentes, no formatos obligatorios.
4. **Fuentes y autoridad:** corpus activo, fuentes permitidas, rol por materia o
   tema, localizadores y cobertura real.
5. **Estado y preferencias del estudiante:** avance que proviene de evidencia
   válida y preferencias duraderas explícitas. Una preferencia no debe
   reemplazar el pedido puntual.
6. **Contrato del turno actual:** tarea, formato, extensión, profundidad,
   inclusiones y exclusiones que el usuario pidió en este mensaje.

La elección de forma debe obedecer, en este orden, a seguridad y exactitud,
fuentes y alcance curricular, pedido explícito del turno y objetivo de
aprendizaje. El perfil del cuaderno guía solo lo que quede sin especificar; no
debe forzar una plantilla.

Ejemplos de representaciones que podrían ser pertinentes, si los objetivos y
fuentes del cuaderno las respaldan:

- programación: traza, pseudocódigo, diagrama de flujo, estado de variables y
  código en el lenguaje del curso;
- Sistemas Operativos: estados/transiciones de procesos, línea de tiempo de
  planificación, intercalación concurrente y diagramas de recursos;
- Tratamiento de Datos: tablas de ejemplo, esquemas relacionales, modelos
  entidad-relación, transformaciones antes/después y consultas;
- Telecomunicaciones: diagramas de bloques, recorrido de señal, capas,
  temporización o topologías.

No son recetas prefijadas: una pregunta breve puede requerir solo una
respuesta directa, aunque el cuaderno permita diagramas o prácticas.

## 4. Hallazgos de la inspección

Se contrastaron el plan rector, `PHASES.md`, `ROADMAP_v1.1.md`, los contratos de
cuaderno y currículum, la configuración de KCs/fuentes, el prompt/contrato
pedagógico, el flujo SSE y pruebas representativas. Los hallazgos distinguen
evidencia observada de cobertura todavía no demostrada.

### H1 — Fallback curricular y directivas heredadas

**Hallazgo original: corregido en los mecanismos centrales; aceptación E2E pendiente.**

La inspección inicial encontró que contratos desconocidos heredaban fases de
programación y que el prompt común imponía supuestos técnicos de esa materia.
En el árbol revisado actualmente, `get_default_contract()` usa fases neutrales,
`required_analogies` está vacío y el prompt base no contiene las directivas
x86-64/System V señaladas en el hallazgo. Los perfiles reconocidos se añaden
solo tras validar el `curriculum_id` exacto en
[`fase0_seed.py`](../src/study_engine/pedagogy/fase0_seed.py).

La prueba de perfiles, fallback neutral y mismatch curricular ejecutada durante
esta auditoría pasó **7 tests**. También se amplió la prueba del endpoint SSE:
la matriz de cinco perfiles exactos y un ID parecido desconocido pasó (**6
passed, 5 warnings**) y captura el prompt que recibe el backend. La prueba usa
un paquete de evidencia simulado; verifica la resolución notebook → contrato →
prompt HTTP/SSE, no el retrieval/ACL real ni la correspondencia de fuentes.
Tampoco valida la respuesta de un proveedor real.

### H2 — Identidad curricular de `fadena-std`

**Hallazgo original: etiqueta corregida en el perfil local; fuente curricular y recorrido E2E aún requieren cierre.**

El perfil vigente denomina `fadena-std` **Sistema de Tratamiento de Datos** y
usa `fadena_std_2026`, alineado con el catálogo curricular versionado. La
corrección evita la etiqueta anterior de “Sistemas de Transmisión de Datos”.
Esto no sustituye la evidencia oficial del programa detallado ni acredita que
las fuentes autorizadas y el prompt final entregado al modelo correspondan a
esa identidad en todos los registros persistidos.

### H3 — Resolución exacta del perfil

**Hallazgo original: mecanismo corregido; cobertura de integración pendiente.**

La resolución actual consulta `NOTEBOOK_PROFILES` por ID exacto y exige que el
`curriculum_id` coincida. IDs desconocidos, parecidos o con un currículo
distinto reciben el prompt neutral; no se selecciona un perfil por subcadena.
Sigue pendiente probar identidad, fuentes, contrato y prompt final
integrados por HTTP/SSE para todos los currículos requeridos; por eso H1–H3 no
equivalen al cierre del Gate B.

### H4 — Política de soluciones completas alineada en Gate 1

**Estado de Gate 1: resuelto en política y aplicado inicialmente en la ruta de
chat; la integración runtime en TutorPolicy/Study Loop sigue pendiente.**

La inspección inicial encontró que la especificación
[`08-S7-TUTOR-POLICY-SPEC-V1.0.md`](./08-S7-TUTOR-POLICY-SPEC-V1.0.md)
declaraba en `TUT-03` que nunca se debía entregar la solución completa, en
conflicto con F1/F2 del plan rector y las pruebas de solicitudes explícitas.

Gate 1 resolvió la contradicción: las prácticas de estudio no protegidas pueden
recibir una solución completa si se solicita explícitamente; una evaluación
activa/protegida mantiene oculto su solucionario canónico y ofrece alternativas
pedagógicas. La protección depende del estado/metadato de la actividad, no de
una prohibición general sobre ejercicios o código. La especificación S7 define
ahora esta distinción y la precedencia general; los prompts pedagógicos de
programación ya no contradicen la solicitud segura explícita. El chat protege
referencias exactas con metadatos confiables de evaluación activa, conserva el
ítem por contexto de sesión y cuaderno, rechaza la solución explícita antes del
LLM y retiene toda la salida antes de comparar coincidencias textuales
normalizadas con el solucionario. Esta comprobación no detecta respuestas
parafraseadas semánticamente y no es por sí sola una garantía de integridad
académica. La integración con TutorPolicy/Study Loop y sus estados evaluativos
propios todavía requiere un contrato común.

### H5 — F6 tiene un hueco confirmado entre terminación del pipeline y UI

**Prioridad: P0 para fiabilidad visible; abordar antes de promocionar F6.**

- `StructuredResponsePipeline` emite `truncated` cuando el proveedor termina
  con `finish_reason="length"` y, en su flujo actual, puede emitir luego
  `phase_complete`.
- `_readSseResponse()` en [`chat.js`](../src/study_engine/web/static/js/chat.js)
  no interpreta eventos `truncated` ni `stream_aborted`, y devuelve texto
  siempre que exista, sin exigir una terminación exitosa explícita.
- El endpoint SSE captura una excepción y construye el mensaje público
  concatenando `str(e)`. El detalle interno de la excepción puede quedar
  expuesto al cliente.
- Hay pruebas de componentes (incluida propagación de `finish_reason` y
  escenarios de caos) pero no se encontró una prueba UI que certifique estas
  salidas terminales a lo largo del flujo completo.

**Resultado posible:** texto parcial de una explicación se guarda y presenta
como respuesta normal. Separar los estados de contenido y transporte, comunicar
truncamiento/cancelación/error y no convertir fallos en éxito. Mantener
diagnóstico detallado en logs con correlación y una respuesta pública segura.

### H6 — F5 avanzó, pero sus criterios no están cerrados en pruebas

**Prioridad: P1.**

Hay implementación de historial acotado y aislado, metadatos de historia,
procedencia de chunks, resolución de referencias y señalamiento heurístico de
discrepancias. La validación focalizada realizada durante esta revisión fue:

```text
./.venv/bin/pytest -q \
  tests/unit/web/test_f5_context_containment.py \
  tests/pedagogy/test_chat_sse_endpoint.py \
  tests/unit/web/test_chat_ui_sse_contract.py \
  tests/web/test_prepare_context_contract.py \
  tests/unit/retrieval/test_query_rewriter.py \
  tests/unit/llm/test_stream_finish_reason.py
35 passed, 5 warnings
node --check src/study_engine/web/static/js/chat.js
passed
```

Esto verifica contratos seleccionados, no todos los criterios de aceptación de
F5. En particular, agregar o localizar pruebas deterministas para:

- preferencia histórica frente a instrucción puntual incompatible;
- ejercicio aceptado/corregido cuando falta el enunciado o el intento;
- feedback limitado al intento visible;
- no mutación de BKT/perfil por conversación ordinaria;
- precisión y límites de las heurísticas de discrepancia entre fuentes.

La detección de discrepancias actual etiqueta conflictos heurísticos de
polaridad/versión; no determina cuál fuente tiene razón. La UI debe presentarlo
como aviso, no como veredicto factual.

### H7 — La cobertura multi-currículo existe en datos, pero no en la prueba de salida

**Prioridad: P1; requisito de F7.**

Los archivos de configuración describen varios programas, pero la evidencia
inspeccionada no demuestra el recorrido completo para cada cuaderno:
selección del currículum y fuentes → perfil pedagógico correcto → prompt final
→ representación pertinente → evento/UI. Los casos de calibración existentes
en [`golden_set_v1.md`](./golden_set_v1.md) no sustituyen una matriz de
regresión balanceada entre materias.

Diseñar pruebas equivalentes de interacción —explicación, “no entendí”, pedido
de síntesis, ejercicio guiado, corrección, seguimiento ambiguo— en más de un
currículum. Evaluar que la respuesta use los recursos de la materia cuando
ayuden y no filtre la pedagogía de programación en SO, datos o telecom.

### H8 — Hay varias nomenclaturas de “fase” y snapshots históricos desactualizados

**Prioridad: P1 de gobernanza; bajo riesgo inmediato en runtime.**

- `PHASES.md` distingue `Fase 4-eval` de `Fase 4-sec` y documenta otro orden de
  producto.
- El plan pedagógico usa Fases 0–7, donde Fase 5 es continuidad y Fase 6 es
  fiabilidad.
- Otros documentos llaman Fase 5 a Late Chunking o a ejercicios certificados;
  `ROADMAP_v1.1.md` contiene objetivos y umbrales de una línea de trabajo
  distinta.
- El snapshot al final de
  [`PLAN_MEJORA_PEDAGOGICA_TALOS.md`](./PLAN_MEJORA_PEDAGOGICA_TALOS.md)
  conserva el estado anterior a los commits que implementaron resolución de
  referencias y discrepancias.

Los reportes de 2.441 pruebas y certificaciones anteriores son snapshots de
sus respectivas fechas/perímetros, no evidencia del estado actual. Mantenerlos
como históricos y evitar usarlos como gate vigente sin repetir la validación
correspondiente.

## 5. Estado de fases: implementación frente a aceptación

| Fase pedagógica | Estado a la fecha | Evidencia y límite |
|---|---|---|
| **F0 — línea de base** | Completada como protocolo | Los 20 turnos comparativos tienen limitaciones explícitas; no prueban causalidad ni aprendizaje. El transcript Fase 0 de programación es evidencia de dinámica, no benchmark multi-materia. |
| **F1 — contrato por turno** | Implementada y validada localmente | Resolver y prompt ensamblado tienen pruebas. No equivale a cumplimiento perfecto de un proveedor real. |
| **F2 — modos pedagógicos** | Implementada y validada localmente | Ejercicio, feedback, reparación, reexplicación, síntesis y solución explícita probados en el pipeline. Pendiente evaluar resultados reales en varios cuadernos. |
| **F3 — rigor técnico** | Implementada y validada localmente | Reduce supuestos y conexiones de seguridad forzadas en instrucciones; no verifica verdad factual de cada salida. El hallazgo H1 sobre el prompt base fue corregido; la aceptación curricular E2E sigue en Gate B. |
| **F4 — formato/código** | Implementada, con tests de pipeline/UI | Validación de reglas y renderer no prueba corrección semántica del contenido. Añadir no-contaminación curricular multi-cuaderno. |
| **F5 — fuentes/memoria/continuidad** | Implementación amplia; aceptación abierta | Las adiciones están comprometidas y los tests focalizados indicados arriba pasan. Cerrar los casos faltantes de H6 y mantener la naturaleza heurística de discrepancias visible. |
| **F6 — streaming/fiabilidad** | Parcial, no aceptada | Hay contratos y pruebas de componentes; H5 demuestra trabajo pendiente en el consumidor SSE y manejo seguro de errores. |
| **F7 — evaluación/aprendizaje** | Pendiente | Congelar evaluación de respuestas por currículo; mantenerla separada de un estudio de retención/transferencia. |

El último resultado de suite global disponible en el handoff previo es
**2695 passed, 7 skipped, 0 failures**. No se repitió esa suite completa en
esta revisión. La ejecución actual fue focalizada, con 35 pruebas aprobadas.

## 6. Plan de corrección y gates para continuar

No conviene agregar más reglas generales de prompt hasta corregir el contrato
curricular de fallback y validar su selección. Orden propuesto:

### Gate A — Alinear política y gobernanza (antes de nuevas integraciones)

1. **Completado en Gate 1:** resolver la contradicción `TUT-03` entre solución
   completa solicitada y evaluación protegida.
2. **Completado en Gate 1:** identificar las fases pedagógicas como
   `PED-F0`…`PED-F7`; usar `PED-F5-continuidad`, `PED-F6-fiabilidad` y
   `PED-F7-evaluación`. Reservar `Fase 4-eval`, `Fase 4-sec`,
   `RETR-late-chunking` y `STUDY-F5-ejercicios` para sus líneas de trabajo.
3. Marcar reportes previos como snapshots fechados y actualizar el handoff
   rector para que describa los commits actuales, el transcript añadido como
   evidencia de dinámica y los límites de aceptación.

**Salida:** precedencia y nomenclatura definidas; el chat tiene protección
runtime para referencias exactas con estado activo. La integración de la misma
política en TutorPolicy/Study Loop sigue pendiente.

### Gate B — Aceptar el aislamiento de perfiles por cuaderno (parcial)

**Implementación central observada:** H1–H3 están corregidos localmente: el
fallback y los contratos default son neutrales, los perfiles requieren
coincidencia exacta de ID y `curriculum_id`, y `fadena-std` usa la etiqueta
Sistema de Tratamiento de Datos del catálogo. La validación focalizada ejecutada
durante esta auditoría pasó **7 tests** de perfil exacto, desconocidos y
mismatch curricular.

**Pendiente para cerrar el gate:**

1. Respaldar el perfil `fadena-std` con la fuente curricular oficial para el
   programa detallado; no inferir unidades, autores o contenidos desde KCs.
2. Reconciliar identidad canónica/aliases, `curriculum_id`, roles de fuentes y
   ciclo de alta en los registros efectivos. Cualquier migración de la base
   local requiere autorización y evidencia previa; no ampliar ACL por
   inferencia.
3. Extender la cobertura HTTP/SSE con retrieval real y fixtures de almacén
   controladas. Ya hay una matriz de identidad/perfil que usa evidencia
   simulada para cinco perfiles y un caso `fadena-std` que pasa por asociación
   explícita de fuentes, allowlist de scope, retrieval real y prompt final. La
   precedencia del contrato custom y la conservación de una restricción
   explícita del turno también tienen pruebas integradas.
4. Cotejar la identidad curricular y roles de fuentes efectivos para
   `fase0-soc`, `fadena-so2`, `fadena-std`, `fadena-teleco` y un currículo
   adicional operativo; no inferir una asociación desde el nombre del curso.

### Matriz de evidencia Gate B

| Requisito | Prueba/evidencia | Datos usados | Qué demuestra | Qué no demuestra / pendiente |
|---|---|---|---|---|
| Fallback neutral, perfil exacto y currículo coincidente | `test_socratic_system_prompt.py` (7 casos seleccionados) y `test_default_curriculum_profile_requires_exact_persisted_identity` | Configuración de perfiles y `KnowledgeStore` temporal | ID desconocido/parecido o mismatch no hereda un perfil; identidad persistida exacta selecciona el perfil previsto | No recorre retrieval, ACL ni endpoint SSE. |
| Matriz de identidad → perfil → prompt SSE | `test_chat_sse_sends_only_the_exact_curriculum_profile_to_backend` (6 casos) | Cinco perfiles configurados y un ID desconocido, cuadernos de test y evidencia simulada | Prompt capturado por el backend contiene el perfil correcto y excluye las otras materias; fallback desconocido queda neutral | No demuestra fuentes autorizadas ni retrieval real para esos cinco casos. |
| Precedencia de contrato custom y restricción explícita del turno | `test_chat_sse_preserves_custom_contract_and_explicit_turn_request` | Contrato custom temporal/persistido en el store de test y evidencia simulada | El prompt custom prevalece sobre el perfil default y conserva una restricción explícita del estudiante | No prueba el comportamiento de cada contrato custom productivo ni de un proveedor real. |
| Fuente asociada al notebook y exclusión de fuente de otro scope hasta el prompt | `test_chat_sse_retrieves_only_sources_authorized_for_notebook_scope` | Dos `SourceRecord`, documentos y chunks de fixture; asociación ACL relacional en el `KnowledgeStore` temporal; ambas fuentes solicitadas por `active_sources` | Retrieval real del endpoint entrega al contexto/prompt solo la fuente autorizada por el notebook y la procedencia SSE solo contiene esa fuente | No usa corpus, ACL o registros productivos; el caso integrado es `fadena-std` y no prueba todas las fuentes/currículos reales. |
| Allowlist de fuentes por scope | `test_retrieval_scope_allowlist.py` | SQLite `:memory:` con scopes y asociaciones sintéticas | Intersección entre fuentes solicitadas y autorización del scope, incluyendo IDs/hash y fuentes desconocidas | Es prueba unitaria, no consulta la base productiva. |
| Identidad curricular y fuentes efectivas | Pendiente; inventario y autoridad documentados en el runbook de Gate 2 | Registros y configuración operativa autorizados, aún no reconciliados/aprobados | — | Confirmar aliases/IDs/`curriculum_id`, roles de fuente, discrepancias y fuente oficial del programa detallado de `fadena-std`; decidir migraciones antes de escribir. |
| Gate 2 formal | Pendiente | Evidencia anterior más reconciliación aprobada y matriz integrada suficiente | — | Gate permanece **PARCIAL** hasta cerrar criterios, documentar decisiones y validar sin modificar artefactos protegidos. |

La corrida focalizada combinada del 2026-09-29 terminó con **24 passed, 5
warnings**; Black y `git diff --check` pasaron. No se usó proveedor real. La
prueba de ACL integrada opera sobre fixtures temporales, de modo que esta
evidencia cierra la pregunta de si el recorrido puede probarse end-to-end, pero
no acredita que los registros, las fuentes autorizadas ni la ACL productiva
sean correctos. Gate B permanece **PARCIAL** por esos pendientes, no por falta
abstracta de una prueba de retrieval hasta el prompt.

### Gate C — Cerrar F5 con criterios observables

1. Completar los casos listados en H6 con mocks y almacenes aislados.
2. Confirmar que historial, fuentes y memorias mantienen el scope del cuaderno
   y que el pedido del turno puede contradecir una preferencia duradera.
3. Probar intentos presentes, parciales, ausentes y de otro contexto.
4. Asegurar que mensajes ordinarios no produzcan cambios de dominio/BKT que
   carezcan de evidencia evaluativa.

**Salida:** criterios de F5 probados; no declarar que resolver una referencia
demuestra memoria de largo plazo.

### Gate D — Cerrar F6 antes de promoción

1. Definir un contrato terminal entre pipeline SSE y UI: éxito completo,
   truncado, cancelado, error y abstención/clarificación.
2. Exigir evento terminal exitoso para marcar/guardar una respuesta como
   completa. Si hubo tokens y luego truncamiento, indicarlo claramente como
   incompleto.
3. Manejar `truncated` y `stream_aborted` en el consumidor; probar EOF sin
   terminal, terminal duplicado y error después de texto.
4. Separar mensaje público seguro del detalle interno de excepción.
5. Añadir pruebas de integración con generadores falsos desde endpoint SSE
   hasta consumidor UI. Mantener separado el gate con proveedor real.
6. Instrumentar latencia/correlación sin almacenar prompt o datos personales
   por defecto; no cambiar límites de tokens/timeouts sin medida que lo
   justifique.

**Salida:** sin éxito falso, pérdida silenciosa de truncamiento ni exposición
de detalles internos en las rutas cubiertas.

### Gate E — Evaluar F7 en varios currículos

Construir una matriz versionada, sin copiar el transcript privado, que cubra:

| Eje | Mínimo de cobertura |
|---|---|
| Currículos | Programación, Sistemas Operativos, Tratamiento de Datos y otra materia disponible. |
| Intenciones | Concepto, síntesis, ejercicio, intento erróneo, “no entendí”, seguimiento y formato explícito. |
| Adecuación curricular | Consistencia con unidad/objetivo/prerrequisito y fuentes activas. |
| Representación | Elección pertinente y ausencia de formatos prescritos por otro cuaderno. |
| Continuidad | Antecedente único, ambiguo, faltante y cambio de tema. |
| Exactitud y evidencia | Citas/localizadores reales cuando correspondan; incertidumbre y abstención honestas. |
| Operación | Éxito, truncamiento, error y latencia medidos aparte de calidad conceptual. |

Usar el historial de Fase 0 para crear ejemplos de interacción de programación,
no para definir el comportamiento en todas las materias. Añadir pares de
pruebas de no-contaminación en los otros currículos. Fijar rúbrica y criterios
antes de puntuar. Una evaluación de respuestas no debe formular conclusiones
de aprendizaje; retención y transferencia requieren un estudio separado.

**Salida:** resultados desglosados por currículo e intención, limitaciones
declaradas y decisión de aceptar/iterar/inconcluso.

## 7. Orden recomendado de trabajo

1. **Bloqueante inmediato:** completar Gate B — evidencia integrada de perfiles
   curriculares, identidad y fuentes.
2. **Siguiente:** Gate C — completar aceptación de F5.
3. **Después:** Gate D — reparar y certificar estados finales de streaming.
4. **Luego:** Gate E — congelar y ejecutar evaluación multi-currículo con
   condiciones registradas.
5. **Solo tras esa evidencia:** decidir si hace falta otro cambio de prompt,
   retrieval, memoria, interfaz o arquitectura.

No es necesario instalar Repomix para este trabajo ni copiar el historial
completo al repo. La revisión actual fue estática más una suite focalizada; no
es certificación de seguridad, auditoría línea por línea de los 424 archivos
de prueba ni evaluación de salidas de proveedor real.

## 8. Evidencia consultada y límites

Documentos y código contrastados:

- [`PLAN_MEJORA_PEDAGOGICA_TALOS.md`](./PLAN_MEJORA_PEDAGOGICA_TALOS.md)
- [`FASE0_LINEA_BASE_TALOS_NOTEBOOKLM.md`](./FASE0_LINEA_BASE_TALOS_NOTEBOOKLM.md)
- [`PHASES.md`](../PHASES.md) y [`ROADMAP_v1.1.md`](./ROADMAP_v1.1.md)
- [`fase0_seed.py`](../src/study_engine/pedagogy/fase0_seed.py)
- [`contract.py`](../src/study_engine/pedagogy/contract.py) y
  [`structured_pipeline.py`](../src/study_engine/pedagogy/structured_pipeline.py)
- [`notebook.py`](../src/study_engine/contracts/notebook.py) y
  [`registry.py`](../src/study_engine/curriculum/registry.py)
- [`notebook_kc_catalog.json`](../config/notebook_kc_catalog.json) y
  [`notebook_source_roles.json`](../config/notebook_source_roles.json)
- [`chat.py`](../src/study_engine/web/routes/chat.py) y
  [`chat.js`](../src/study_engine/web/static/js/chat.js)
- Pruebas focalizadas de F5/SSE, `test_socratic_system_prompt.py`,
  `test_adaptive_pipeline.py` y pruebas de streaming/truncamiento.

El historial completo fue consultado como referencia local proporcionada por el
usuario y no se incorporó a este documento. Los hallazgos sobre rutas
multi-cuaderno se limitan a lo que se pudo comprobar en el contrato, el prompt,
la configuración y las pruebas inspeccionadas; el Gate B incluye el test de
integración que falta para cerrar el recorrido completo.

## 9. Ejecución de la suite de estabilización

El plan ejecutable para armonizar políticas, aislar perfiles por cuaderno,
cerrar los criterios pendientes de F5/F6 y capturar la baseline está en
[Suite de fixes y estabilización previa a Fase 7](./PLAN_SUITE_FIX_ESTABILIZACION.md).
La baseline debe capturarse después de guardar la documentación y antes de
cualquier cambio de producción; no confundirla con resultados históricos.

## Actualización de estado — 2026-09-29

La lectura del árbol de trabajo actualiza el dictamen de los hallazgos H1–H3:
sus mecanismos centrales están corregidos y cuentan con pruebas unitarias,
pero el Gate B sigue parcial por falta de evidencia integrada. Se ejecutaron
los casos de perfiles exactos, fallback neutral, IDs desconocidos y mismatch
curricular de `tests/pedagogy/test_socratic_system_prompt.py`: **7 passed**,
6 deselected. La prueba de SSE se amplió a cinco perfiles exactos y un ID
parecido desconocido:
`test_chat_sse_sends_only_the_exact_curriculum_profile_to_backend` terminó con
**6 passed, 5 warnings** y verificó los prompts capturados en backend. Usa un
paquete de evidencia simulado, por lo que no prueba retrieval ni ACL reales.
El test `test_chat_sse_preserves_custom_contract_and_explicit_turn_request`
pasó (**1 passed, 5 warnings**) y comprobó la precedencia del contrato custom
y una restricción explícita en el prompt de usuario. En la corrida combinada
con persistencia curricular y allowlist de fuentes por scope: **23 passed, 5
warnings**. Después se añadió
`test_chat_sse_retrieves_only_sources_authorized_for_notebook_scope`: usa
retrieval real con fuentes y chunks de fixture en el almacén temporal y verifica
que una fuente de otro notebook no llegue al prompt/contexto ni a la
procedencia SSE. La suite focalizada combinada final terminó con **24 passed,
5 warnings**; Black y `git diff --check` pasaron. La prueba no lee ni altera
las ACL o bases protegidas. No se probó un proveedor real.

La cobertura ya demuestra ese trayecto con una fixture aislada para
`fadena-std`, no para todos los currículos ni contra corpus/ACL de producción.
Tampoco autoriza migrar registros curriculares locales ni cambiar ACL. La
aceptación pendiente y los siguientes pasos de F5/F6/F7 permanecen como están
descritos arriba.
