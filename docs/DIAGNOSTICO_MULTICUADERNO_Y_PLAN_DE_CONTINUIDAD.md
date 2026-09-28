# Diagnóstico multi-cuaderno de TALOS y plan para continuar

**Fecha:** 2026-09-28
**Base inspeccionada:** `main`, commit `ea060ad`
**Propósito:** aclarar el alcance del historial de NotebookLM, auditar las fases
de mejora pedagógica contra el código y definir las correcciones necesarias
antes de avanzar.

## 1. Dictamen ejecutivo

La dirección general es correcta: TALOS ya tiene conceptos de cuaderno,
currículum, fuentes autorizadas, Knowledge Components (KCs), estado del
estudiante y una política común de interacción. También existen configuraciones
curriculares distintas para programación, Sistemas Operativos, Tratamiento de
Datos y Telecomunicaciones.

Sin embargo, **la separación entre política pedagógica común y pedagogía
específica del cuaderno todavía no está asegurada de punta a punta**. El
fallback actual crea contratos para cuadernos nuevos copiando fases y analogías
de la Fase 0 de programación; el prompt base conserva supuestos explícitos de
C/x86-64; y las pruebas actuales no demuestran que el prompt final de cada
cuaderno esté libre de directivas pedagógicas ajenas a su materia. Se encontró,
además, una etiqueta de materia incorrecta para `fadena-std`.

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

**Conclusión:** antes de considerar cerrada la implementación pedagógica o
promocionar F5–F7, hay que corregir el perfil de fallback por cuaderno, eliminar
supuestos de programación del camino común, resolver las contradicciones de
política y terminar el gate de streaming. Después, la evaluación debe medir
adaptación curricular además de calidad de respuesta.

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

### H1 — El contrato de fallback hereda directivas de programación a otros cuadernos

**Prioridad: P0 — corregir antes de cerrar adaptación multi-cuaderno.**

- `Notebook` ofrece campos para `subject`, `curriculum_id`, fuentes y metadata
  en [`contracts/notebook.py`](../src/study_engine/contracts/notebook.py).
- Existen catálogos distintos en
  [`notebook_kc_catalog.json`](../config/notebook_kc_catalog.json) y
  [`notebook_source_roles.json`](../config/notebook_source_roles.json), entre
  ellos `fase0-soc`, `fadena-so2`, `fadena-std` y `fadena-teleco`.
- `get_system_prompt_for_notebook()` añade una adaptación textual por ID en
  [`fase0_seed.py`](../src/study_engine/pedagogy/fase0_seed.py).
- Pero `get_default_contract()` reutiliza para cualquier ID las
  `FASE0_RESPONSE_PHASES` y copia el campo `required_analogies` de
  `FASE0_CONTRACT`. Por eso, una adaptación de tema puede coexistir con fases
  que piden transistores, diagramas ASCII, pseudocódigo defensivo y
  pseudocódigo → Python. No encontré un consumidor que inyecte
  `required_analogies` directamente en el prompt; su efecto runtime debe
  tratarse como no demostrado hasta cubrirlo en la prueba de contrato/prompt
  final.
- El mismo prompt base todavía incluye una sección que asume x86-64 System V y
  reglas específicas de stack, heap y `malloc` como supuestos predeterminados.
  Esto entra en tensión con la instrucción más nueva de no asumir plataforma
  cuando no está provista.

**Impacto:** un cuaderno puede tener buenos KCs y fuentes propias, pero recibir
un contrato de generación diseñado para programación. La adaptación nominal
del prompt no alcanza si las fases y las reglas base siguen prescribiendo otra
materia.

**Verificación faltante:** las pruebas inspeccionadas comprueban que ciertas
adaptaciones contienen nombres de programas o fuentes y que existen comandos
universales; no comprueban que el contrato completo ni el prompt final de cada
cuaderno queden libres de instrucciones ajenas.

### H2 — La adaptación de `fadena-std` describe una materia distinta

**Prioridad: P0 — corregir junto con H1.**

En `NOTEBOOK_ADAPTATIONS`, `fadena-std` se describe como “Sistemas de
Transmisión de Datos” y refiere a un programa de siete módulos. En cambio,
`notebook_kc_catalog.json` y `notebook_source_roles.json` identifican
`fadena-std` como **Sistema de Tratamiento de Datos** y lo vinculan con bases
de datos, SQL, formatos semiestructurados, ETL y fuentes relacionadas.

Esta divergencia puede producir una directiva curricular equivocada aunque la
recuperación documental se aisle correctamente. Corregir el mapeo contra la
fuente oficial del programa antes de ajustar el resto del perfil.

### H3 — La adaptación por subcadena puede seleccionar un perfil no exacto

**Prioridad: P1.**

`get_system_prompt_for_notebook()` intenta resolver IDs desconocidos buscando
coincidencias parciales de subcadena contra las claves de `NOTEBOOK_ADAPTATIONS`.
No hay evidencia en las pruebas revisadas de que los IDs ambiguos o similares
se rechacen de forma segura. Un fallback accidental puede asociar el prompt del
cuaderno incorrecto.

Resolver el perfil desde un registro explícito con ID exacto. Si no existe
configuración, usar un perfil neutral sin supuestos de dominio, o emitir un
error de configuración visible en la creación del contrato; no seleccionar el
primer parecido.

### H4 — Política de soluciones completas contradictoria entre especificaciones

**Prioridad: P1 — resolver antes de conectar TutorPolicy/Study Loop.**

La especificación
[`08-S7-TUTOR-POLICY-SPEC-V1.0.md`](./08-S7-TUTOR-POLICY-SPEC-V1.0.md)
declara en `TUT-03` que nunca se debe entregar la solución completa. En cambio,
las fases F1/F2 del plan rector y sus pruebas recientes preservan una solicitud
explícita y segura de solución completa.

La política correcta debe distinguir, como mínimo, entre práctica de estudio
libre y una tarea certificada/evaluada cuyo solucionario está protegido. La
regla de anti-leakage de una evaluación no debe convertirse en una prohibición
global paternalista, ni el pedido de solución debe permitir acceso al
solucionario canónico de un ítem protegido.

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
| **F3 — rigor técnico** | Implementada y validada localmente | Reduce supuestos y conexiones de seguridad forzadas en instrucciones; no verifica verdad factual de cada salida. Revisar H1 por las instrucciones heredadas del prompt base. |
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

1. Resolver la contradicción `TUT-03` entre solución completa solicitada y
   evaluación protegida.
2. Adoptar nombres inequívocos para las líneas de trabajo; por ejemplo,
   `PED-F5-continuidad`, `PED-F6-fiabilidad`, `PED-F7-evaluación`,
   `RETR-late-chunking` y `STUDY-F5-ejercicios`.
3. Marcar reportes previos como snapshots fechados y actualizar el handoff
   rector para que describa los commits actuales, el transcript añadido como
   evidencia de dinámica y los límites de aceptación.

**Salida:** una precedencia de políticas única y estados de fase no ambiguos.

### Gate B — Reparar el aislamiento de perfiles por cuaderno (bloqueante)

1. Corregir `fadena-std` contra el programa oficial de Tratamiento de Datos.
2. Sustituir el fallback que copia `FASE0_RESPONSE_PHASES` y analogías de
   Fase 0 por:
   - contrato explícito propio para los cuadernos soportados; o
   - contrato neutral común que no prescriba formato ni contenido de una
     materia, si no hay perfil registrado.
3. Mover las suposiciones de programación/x86-64 fuera del prompt global y
   aplicarlas únicamente cuando el cuaderno, la consulta o el material activo
   establezcan ese entorno.
4. Resolver cuaderno/perfil por ID registrado exacto; eliminar la selección
   por subcadena ambigua.
5. Auditar la asociación de `Notebook.curriculum_id`, catálogo de KCs,
   alineación de fuentes y contrato pedagógico en el camino real de chat.

**Tests de salida:** contrato y prompt final para `fase0-soc`, `fadena-so2`,
`fadena-std` y al menos un cuaderno adicional; assertions positivas de los
elementos propios y negativas de directivas ajenas. Un ID desconocido debe
tomar el fallback neutral o fallar con diagnóstico explícito, nunca heredar un
perfil parecido.

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

1. **Bloqueante inmediato:** Gate A y Gate B — coherencia normativa y perfiles
   curriculares reales.
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
