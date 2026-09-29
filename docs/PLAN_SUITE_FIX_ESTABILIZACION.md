# Suite de fixes y estabilización previa a Fase 7

**Fecha:** 2026-09-28
**Estado:** punto 0, Gate 1 y protección runtime inicial completados; Gate 2
con piloto acotado, fixtures adjudicadas e inventario histórico read-only
**Alcance:** armonizar políticas, contratos multi-cuaderno y fiabilidad antes de
continuar con evaluación pedagógica multi-currículo.

## Objetivo

Corregir defectos y contradicciones que bloquean una evaluación fiable de
TALOS, y demostrar las correcciones mediante pruebas reproducibles. Esto no es
una limpieza general del repositorio, una refactorización amplia ni una nueva
fase de producto. No agregar capacidades fuera de los hallazgos acotados aquí.

La suite se ejecuta sobre cambios pequeños y verificables. Se registran los
fallos preexistentes aparte de los regresivos, y no se modifica ni descarta
trabajo que ya esté en el árbol.

## Punto 0 — Congelar y medir el punto de partida

Antes de tocar código de producción:

1. Guardar y comprometer por separado la documentación de diagnóstico y este
   plan, sin mezclarla con fixes de aplicación.
2. Confirmar rama, commit `HEAD`, árbol limpio y configuración del entorno de
   pruebas.
3. Capturar la suite global existente y los chequeos específicos relevantes
   para F5, SSE/UI y contratos pedagógicos. Registrar comandos, conteos,
   skips, warnings y fallos, sin corregirlos todavía.
4. Identificar por evidencia qué fallos son preexistentes, cuáles se deben a
   entorno/configuración y cuáles aparecen como regresiones durante esta
   suite.
5. Conservar resultados previos como snapshots históricos; la suite global
   previamente reportada (2695 passed, 7 skipped) no sustituye una ejecución
   actual.

**Salida:** baseline fechada, reproducible y asociada al commit inicial de la
suite. Si la suite global no puede ejecutarse, registrar el bloqueo concreto y
usar solo checks alternativos que no se presenten como equivalentes.

### Resultado de baseline — 2026-09-28

- Punto de partida: rama `main`, commit `0e57eea`, árbol limpio antes de las
  pruebas; Python 3.12.3 y pytest 9.1.1 en `.venv`.
- Suite global: `.venv/bin/pytest -q` — **2695 passed, 7 skipped, 0 failed**,
  138 warnings, 313.47 s.
- Suite focalizada de contexto F5, endpoint SSE/UI, rewriter, finish reason,
  pipeline adaptativo y prompt socrático — **100 passed**, 5 warnings,
  7.19 s.
- Sintaxis del consumidor UI: `node --check
  src/study_engine/web/static/js/chat.js` — pasó.
- Las pruebas globales reescribieron cuatro resultados versionados:
  `benchmark/results/evaluation_report.json`,
  `benchmark/results/evaluation_report.md`,
  `benchmark/results/latest_summary.json` y
  `data/experiments/survival/l5_concurrency_race_50.json`. Se restauraron a su
  contenido del commit inicial después de revisar los diffs; el árbol quedó
  limpio. El reporte Fase 4-eval generado durante tests sintéticos mostró
  MRR@5/nDCG@5 de retrieval en cero y estado FAIL, aunque pytest terminó sin
  fallos. Tratar esto como un problema de aislamiento/efectos laterales de la
  suite y no como un resultado de evaluación del producto; no modificar esos
  umbrales ni promocionar ese reporte.

**Conclusión de punto 0:** la base funcional es reproducible en el entorno
actual. Antes de usar repetidamente la suite global como gate, conviene
aislar sus salidas generadas para que no reescriba reportes y evidencia
versionados.

## Gate 1 — Alinear políticas y nomenclatura

**Completado:** se resolvió la contradicción TUT-03. En práctica no protegida
se atiende una solicitud explícita segura de solución completa; para
evaluaciones activas/protegidas no se expone el solucionario canónico. Se fijó
la precedencia normativa y se alinearon los prompts de programación. Además, el
chat aplica protección runtime a referencias exactas con metadatos confiables
del `ContentRegistry`, conserva el ítem por contexto de sesión/cuaderno,
rechaza la solicitud explícita antes del LLM y retiene toda la respuesta para
una comprobación textual del solucionario. La integración equivalente en
TutorPolicy/Study Loop sigue pendiente. Las fases del plan pedagógico se
identifican `PED-F0`…`PED-F7`; se reservan `Fase 4-eval`,
`Fase 4-sec`, `RETR-late-chunking` y `STUDY-F5-ejercicios` para sus respectivas
líneas de trabajo.

**Salida:** reglas de solución, precedencia y nomenclatura coherentes antes de
continuar con cambios de perfiles o nuevas integraciones.

**Criterio runtime incorporado:** metadatos `assessment.protected=true` y
`assessment.status` igual a `active` o `in_progress`, guardados por la
configuración confiable del servidor. Sin solucionario canónico disponible, la
ruta protegida responde fail-closed. Las respuestas generadas para la referencia
activa se retienen hasta la comprobación para impedir fugas parciales por SSE.
La comprobación detecta coincidencias completas normalizadas o fragmentos
textuales sustanciales; no reconoce respuestas parafraseadas semánticamente y
no constituye por sí sola una garantía de integridad académica.

### Verificación de aislamiento y Gate 1 — 2026-09-28

- Se cambió la prueba del benchmark para escribir los reportes bajo `tmp_path`
  y verificar que solo genere los tres archivos esperados allí.
- La prueba de concurrencia L5 persiste telemetría bajo `tmp_path` en vez de
  modificar `data/experiments/survival/`.
- La especificación TUT-03, la jerarquía del plan rector y los prompts de
  programación distinguen práctica no protegida (solución completa explícita
  permitida) de evaluación activa/protegida (solucionario canónico no
  divulgable).
- Se estableció `PED-F0`…`PED-F7` para el programa pedagógico, con nombres
  explícitos para las líneas de Fase 4-eval, Fase 4-sec, retrieval y Study
  Loop.
- Validación focalizada de aislamiento y política: **86 passed, 9 warnings**.
- Suite global: `.venv/bin/pytest -q` — **2696 passed, 7 skipped, 0 failed**,
-  138 warnings, 334.16 s en la ejecución final.
- Una ejecución completa intermedia falló solo en el test de rendimiento
  `test_sqlite_query_latency_p95_under_50ms` (51.95 ms frente al límite
  estricto de 50 ms). El test aislado pasó en 2.27 s y la suite completa
  secuencial posterior pasó; se conserva como señal de variabilidad del test,
  no se ajustó el umbral.
- Tras la suite global, los cuatro artefactos versionados enumerados en la
  baseline permanecieron sin cambios. `git diff --check` y validación de
  enlaces Markdown relativos pasaron.

**Estado:** punto 0 y Gate 1 completados para coherencia normativa,
nomenclatura y protección runtime inicial del chat; Gate 2 pendiente. La
integración en TutorPolicy/Study Loop y la detección semántica de respuestas
equivalentes siguen fuera de alcance.

### Verificación runtime de evaluación protegida — 2026-09-28

- La ruta confía en metadatos del registro `assessment.protected=true` y
  estado `active` o `in_progress`; la solicitud del cliente no activa ni
  desactiva la guarda.
- Rechaza solicitudes explícitas de solución antes de invocar al LLM, conserva
  el ítem para seguimientos del mismo contexto, falla cerrada si falta el
  solucionario y retiene tokens hasta completar la comprobación de salida.
- Pruebas focalizadas de protección, endpoint de chat, prompts y regresión de
  soluciones explícitas no protegidas: **83 passed** (17 warnings).
- Suite global posterior a los cambios: `.venv/bin/pytest -q` —
  **2703 passed, 7 skipped, 0 failed**, 144 warnings, 351.57 s.
- La comparación normalizada detecta coincidencias completas o fragmentos
  textuales; no detecta paráfrasis semánticas y no reemplaza controles de
  evaluación ni revisión humana.

### Registro detallado de la etapa de evaluaciones protegidas

#### Qué se encontró

El cierre de Gate 1 había armonizado la política escrita, pero la ruta de chat
aún no aplicaba una guarda runtime a evaluaciones activas. La intención del
estudiante o una instrucción del prompt no bastan para distinguir una práctica
normal de una evaluación protegida, y una bandera proporcionada por el cliente
sería manipulable. A la vez, prohibir todas las soluciones completas habría
roto las prácticas no protegidas, donde el pedido explícito sí debe respetarse.

El repositorio ya separaba los fragmentos de enunciado de los solucionarios en
`ContentRegistryRepository`, con un accessor específico para las soluciones.
El punto fiable para decidir la protección era el ítem curricular resuelto por
el servidor (`EpistemicContextPack.resolved_item`), no texto libre ni un ID
declarado por el estudiante. El riesgo restante era que el modelo incluyera
parte del solucionario en una respuesta que se transmitía token a token por
SSE: una comprobación posterior al streaming no podría retirar lo ya mostrado.

#### Solución planteada e implementada

Se adoptó un criterio opt-in de servidor: un ítem está protegido solo si sus
metadatos confiables contienen
`assessment.protected=true` y `assessment.status` es `active` o `in_progress`.
La ausencia de marca, un estado distinto (por ejemplo `draft`) o
`protected=false` conserva el comportamiento ordinario de práctica.

La integración está en [`chat.py`](../src/study_engine/web/routes/chat.py) y el
criterio textual compartido en
[`solution_protection.py`](../src/study_engine/pedagogy/solution_protection.py):

1. El chat resuelve el ítem desde el registro del servidor y guarda su
   `content_id` en una caché efímera por contexto de sesión, cuaderno, alcance y
   fuentes, con TTL de una hora. Esto mantiene la protección en seguimientos
   que no repiten la referencia mientras comparten ese contexto y proceso.
2. Carga el solucionario solo mediante `get_solution_chunks()`; no lo añade al
   contexto visible ni al manifiesto de evidencias.
3. Si el solucionario no está disponible, responde fail-closed. Si se solicita
   explícitamente la solución completa, produce una negativa determinista antes
   de llamar al LLM.
4. Para otras consultas, añade una instrucción de protección al `system_prompt`
   y retiene los tokens de la respuesta hasta terminar la fase. Compara el
   texto final normalizado contra las soluciones: una coincidencia completa o
   un fragmento textual sustancial se sustituye por una negativa segura antes
   de emitir SSE.
5. La política pedagógica sigue permitiendo soluciones completas solicitadas
   para prácticas no protegidas. El contrato, los prompts comunes y los
   mensajes de narrador se armonizaron con esa distinción.

La implementación y las pruebas se guardaron en el commit
`d4fc5b3` (`fix(pedagogy): protect active assessments from solution leaks`).
El cambio también aisló los artefactos del benchmark y de la prueba de
concurrencia en `tmp_path`, para que las suites no reescriban evidencia
versionada.

#### Incidencias, correcciones y límites conocidos

- **Artefactos de prueba modificados:** la baseline inicial mostró que el
  benchmark y la prueba de concurrencia podían escribir resultados en rutas
  versionadas. Se corrigieron ambos tests para usar almacenamiento temporal y
  se comprobó que los artefactos versionados permanecieran intactos tras la
  suite final.
- **Variación de latencia preexistente en Gate 1:** una ejecución intermedia
  midió 51.95 ms frente al umbral estricto de 50 ms en
  `test_sqlite_query_latency_p95_under_50ms`. El test aislado y la suite global
  secuencial posterior pasaron; se conservó el umbral y se registró como
  variabilidad de medición, no como regresión de la protección.
- **Cobertura del rechazo seguro:** se añadió una prueba para el caso sin
  solucionario registrado. Confirma que la ruta no invoque al LLM y emita el
  estado explícito `PROTECTED_ASSESSMENT_UNAVAILABLE`.
- **Sin fallos funcionales pendientes en la validación final:** la batería
  focalizada y la suite global terminaron correctamente. Los warnings son
  avisos de deprecación preexistentes de FastAPI/Starlette, no fallos de esta
  etapa.
- **Límite del detector:** normalizar texto y buscar coincidencias literales
  reduce fugas accidentales, pero no detecta una solución parafraseada ni
  demuestra que dos respuestas sean semánticamente equivalentes. El buffering
  también aumenta la latencia percibida para ítems protegidos.
- **Límite de estado:** la caché de ítem activo es en memoria y local al
  proceso; el TTL no es persistencia distribuida. La continuidad entre
  reinicios o workers y las transiciones de sesión deben definirse antes de
  usar este mecanismo como garantía de una evaluación productiva.

#### Estado de la etapa y evidencia de cierre

La protección runtime inicial del endpoint de chat está implementada y
verificada; no significa que todas las evaluaciones de TALOS estén protegidas.
Para aplicar la guarda, cada evaluación debe tener metadatos correctos en el
registro confiable y un solucionario canónico recuperable. La integración en
TutorPolicy/Study Loop, el almacenamiento distribuido de estado y la detección
semántica siguen pendientes.

- Batería focalizada final: **83 passed, 17 warnings**.
- Suite global final: `.venv/bin/pytest -q` — **2703 passed, 7 skipped,
  0 failed**, 144 warnings, 351.57 s.
- `git diff --check` y enlaces Markdown relativos: correctos.
- Los artefactos versionados del benchmark/supervivencia no cambiaron.

#### Siguientes pasos

1. Completar Gate 2: aislar el perfil pedagógico por cuaderno y demostrar
   integración desde currículum y fuentes hasta el prompt final, incluyendo
   controles contra contaminación entre materias.
2. Antes de conectar TutorPolicy/Study Loop, definir un contrato evaluativo
   común: quién activa y cierra una evaluación, estados terminales, autoridad
   que escribe metadatos y comportamiento ante cambios o correcciones del
   registro.
3. Ampliar las pruebas de protección para manipulación de campos cliente,
   `in_progress`, estados inactivos, cambio de ítem/alcance/fuentes, expiración
   del TTL y solucionario ausente o no legible. Aclarar si el estado efímero
   basta o si se necesita almacenamiento compartido entre workers.
4. Mantener el gate de streaming F6 separado: verificar múltiples fases,
   truncamiento, cancelación, error después de tokens y ausencia de un terminal
   exitoso antes de marcar una respuesta completa.
5. Medir falsos positivos y falsos negativos del detector textual con casos
   sintéticos. Si se requiere cobertura semántica, fijar primero el modelo de
   amenaza y los criterios de aceptación; no presentar el detector actual
   como una garantía de integridad.
6. Solo después, avanzar a la evaluación multi-currículo PED-F7 con una rúbrica
   congelada y resultados desglosados por materia e intención.

## Gate 2 — Aislar el perfil pedagógico por cuaderno

**Objetivo:** cada cuaderno debe conservar la política común de tutoría y
recibir únicamente su propio contexto curricular. El perfil debe orientar
cuando el pedido actual no especifica forma, nunca imponer diagramas,
analogías, código o una secuencia didáctica ajena al curso.

### Dictamen de preparación

El inventario/caracterización G2.0 está completado y documentado abajo. Gate 2
está **listo para pasar a decisiones de contrato e implementación controlada**;
no se debe comenzar con cambios amplios de retrieval hasta completar esas
decisiones y congelar las pruebas de calidad/capacidad. La revisión del estado
comprometido en `8f14cd3`
confirma estos defectos concretos:

1. `get_system_prompt_for_notebook()` en
   [`fase0_seed.py`](../src/study_engine/pedagogy/fase0_seed.py) tiene
   adaptaciones para IDs exactos, pero si no encuentra uno prueba coincidencias
   parciales. Dos slugs relacionados o un identificador nuevo pueden heredar el
   texto de otro cuaderno.
2. `fadena-std` aparece en esa adaptación como “Sistemas de Transmisión de
   Datos”, mientras el catálogo curricular, el registro de cuadernos y los
   roles de fuentes lo identifican como Sistema de Tratamiento de Datos /
   Tratamiento de Datos y Bases de Datos. El nombre de materia está confirmado;
   programa, cantidad de módulos y autores deben volver a cotejarse con una
   fuente curricular oficial antes de fijarlos en el prompt.
3. `get_default_contract()` devuelve a IDs no configurados las fases de
   [`FASE0_RESPONSE_PHASES`](../src/study_engine/pedagogy/fase0_seed.py):
   explicación con hardware/transistores y diagrama ASCII, pseudocódigo y fase
   de código Python. También copia analogías de stack frame, guard clauses y
   RAM física. No es solo texto adaptativo: el pipeline selecciona la fase del
   contrato y la utiliza al construir la instrucción de generación.
4. El prompt compartido `TALOS_BASE_SYSTEM_PROMPT` contiene instrucciones
   prescriptivas de x86-64/System V, stack/heap, C y `malloc`. El prompt
   `RIOPLATENSE_SYSTEM_PROMPT` repite supuestos de programación y exige
   analogía, mecanismo físico y diagrama ASCII para preguntas conceptuales.
   No se debe concluir que todo es una ruta activa: antes de tocar el segundo,
   localizar y probar sus consumidores de producción; actualmente la búsqueda
   encontró el narrador y sus tests, pero no un punto de conexión desde la ruta
   principal de chat.
5. Las pruebas existentes verifican presencia de nombres, autores y comandos
   seguros, pero no prueban neutralidad del contrato de fallback ni el prompt
   final que recibe el backend por cada cuaderno. Una prueba del nombre no
   demuestra aislamiento end-to-end.

Los datos existentes permiten preparar perfiles para `fase0-soc`,
`fadena-lenguajes`, `fadena-so2`, `fadena-std` y `fadena-teleco`; los catálogos
incluyen además `fadena-sye`, y `NotebookRegistry` declara aliases heredados
como `fadena-prog`, `fadena-so` y `NB-CYBERSECURITY-V1`. Por lo tanto, antes de
definir una lista cerrada hay que reconciliar las identidades activas y
compatibles en el registro de cuadernos, catálogo KC, catálogo de roles de
fuentes y base SQLite. No se debe usar la subcadena ni `subject` como sustituto
silencioso de una identidad curricular canónica.

### Procedimiento de ejecución propuesto

#### G2.0 — Congelar inventario y comportamiento actual

- Confirmar `HEAD` y árbol limpio tras los commits `d4fc5b3` y `8f14cd3`.
- Inventariar todos los callers de `get_default_contract()`,
  `get_system_prompt_for_notebook()`, `RIOPLATENSE_SYSTEM_PROMPT` y
  `required_analogies`; distinguir las rutas activas del chat de los
  componentes disponibles pero no conectados.
- Construir una tabla de IDs canónicos y aliases comparando
  `DEFAULT_NOTEBOOKS`, `config/notebook_kc_catalog.json`,
  `config/notebook_source_roles.json`, los notebooks provisionados y los
  notebooks persistidos. Para cada ID registrar `subject`, `curriculum_id`,
  unidad/objetivos de muestra y fuentes primarias autorizadas.
- Resolver la autoridad curricular del perfil `fadena-std` consultando el
  programa oficial ya registrado y los manifiestos de fuentes. No deducir el
  número de unidades a partir de la cantidad de KCs, ni reutilizar como
  bibliografía principal la fuente de “Estructuras de Datos y Archivos”.
- Ejecutar las pruebas actuales de perfil, contrato, almacenamiento y endpoint
  pertinentes antes del primer cambio; guardar conteos y fallos como
  caracterización, no como baseline global.

**Salida G2.0:** inventario auditable, lista de rutas efectivas y una matriz de
fuentes para resolver contradicciones curriculares antes de codificar.

#### G2.0 — Resultado de inventario y caracterización — 2026-09-28

**Punto de partida:** `HEAD=8f14cd3` (`docs(pedagogy): document protected
assessment implementation`). El único cambio local preexistente antes de
caracterizar era esta ampliación del plan; no se alteró ni descartó. La prueba
focalizada se corrió contra el código actual, antes de cualquier cambio de
Gate 2.

**Identidades cruzadas** — la diferencia entre “registrado” y “configurado” es
material; no existe una única fuente canónica que contenga hoy todos los campos:

| Fuente | IDs observados | Campo/limitación relevante |
|---|---|---|
| `DEFAULT_NOTEBOOKS` en `federation/notebook_registry.py` | `fase0-soc`, `fadena-lenguajes`, `fadena-so2`, `fadena-std`, `fadena-teleco`, `fadena-prog`, `fadena-so`, `NB-CYBERSECURITY-V1` | Declara `subject`, fuentes y autoridad temática; su modelo no declara `curriculum_id`. `fadena-prog` y `fadena-so` se nombran explícitamente como legacy aliases; `NB-CYBERSECURITY-V1` es una identidad de cuaderno distinta, no alias de esos currículos. |
| `config/notebook_kc_catalog.json` | Los cinco currículos principales más `fadena-sye` | Incluye `curriculum_id` y unidades/KCs. `fadena-sye` no está en `DEFAULT_NOTEBOOKS` ni en roles de fuentes. Un catálogo de KCs no demuestra por sí solo que el mapeo o programa citado sea oficial. |
| `config/notebook_source_roles.json` | `fase0-soc`, `fadena-lenguajes`, `fadena-so2`, `fadena-std`, `fadena-teleco` | Define fuentes/roles para los cinco perfiles actuales; omite `fadena-sye` y aliases legacy. |
| `config/notebooks/` | `fase0-soc`, `fadena-so2`, `fadena-teleco` | Solo esos tres directorios tienen `chapters.json`; faltan Lenguajes y Tratamiento de Datos. |
| `data/web_state/knowledge_store.db` local | 12 IDs, incluidos los cinco perfiles principales, `fadena-sye`, aliases y `NB-SEC-01-C-PTR`, `nb_prog_1`, `nb_prog_basica` | Es estado SQLite local, no fuente versionada de identidad. Las filas de los principales cuadernos muestran `curriculum_id=fadena_v1`, mientras el catálogo KC asigna IDs curriculares específicos por materia. No había contratos pedagógicos custom persistidos en esta base al inspeccionarla. |

Los 12 IDs presentes en esa base local fueron:
`NB-CYBERSECURITY-V1`, `NB-SEC-01-C-PTR`, `fadena-lenguajes`,
`fadena-prog`, `fadena-so`, `fadena-so2`, `fadena-std`, `fadena-sye`,
`fadena-teleco`, `fase0-soc`, `nb_prog_1` y `nb_prog_basica`.

Para los cinco perfiles centrales, los IDs del catálogo son
`roadmap_kasiu_v4_fase0`, `fadena_lenguajes_2026`,
`fadena_so2_2026`, `fadena_std_2026` y `fadena_teleco_2025`,
respectivamente. La base local con el mismo nombre de notebook registra
`fadena_v1` para todos. La diferencia se debe resolver antes de usar
`curriculum_id` persistido como autoridad; no se modificó esa base local.

**Prueba de comportamiento actual del resolver y contrato**, usando
`PYTHONPATH=src .venv/bin/python` y `get_default_contract()`:

| ID consultado | Resultado observado |
|---|---|
| `fase0-soc`, `fadena-lenguajes`, `fadena-so2`, `fadena-std`, `fadena-teleco` | Prompt con adaptación textual nominal para cada uno; los cinco conservan las mismas fases `conceptual`, `pseudocode`, `python_code`, `verification` y analogías de stack frame, guard clause y RAM física. |
| `fadena-so` | Coincide parcialmente con `fadena-so2` y hereda su adaptación de Sistemas Operativos II; este comportamiento accidental se debe a `fadena-so` contenido en `fadena-so2`. |
| `fadena-std-extra` | Hereda la adaptación `fadena-std` por subcadena aunque no sea el ID registrado. |
| `fadena-sye`, `fadena-prog`, `NB-CYBERSECURITY-V1`, `unknown` | No reciben adaptación textual del mapa, pero `get_default_contract()` igual los construye con las fases y analogías de Fase 0, incluido el contrato conceptual de programación. |

Los perfiles especializados también reciben en el texto base x86-64/System V,
reglas C/stack/heap y supuestos de `malloc`; son instrucciones comunes del
contrato, no resultado de una selección por materia. El endpoint principal
obtiene el notebook mediante el scope y luego llama
`store.get_pedagogical_contract(notebook_id)`. En ausencia de fila custom, ese
store deriva en `get_default_contract()`. El límite HTTP ya tiene pruebas
existentes para scopes inexistentes, pero el helper de contrato, considerado
aisladamente, no valida que su argumento sea un notebook registrado.

La búsqueda de callers confirmó que `required_analogies` es campo persistido
del contrato, pero no encontró un consumidor directo que las inserte en el
prompt del pipeline. Aun sin inyección directa, las fases del contrato sí se
seleccionan y se usan en la generación, por lo que ese fallback no es inocuo.
`RIOPLATENSE_SYSTEM_PROMPT` se referencia desde `PersonaNarrator`; el inventario
de instanciaciones en `src/` no encontró un caller productivo del narrador. Se
lo deja como superficie separada, fuera de una refactorización automática del
camino principal.

**Evidencia de `fadena-std`:** el archivo local
`fuentes/fadena-std/UNIDAD1STD.pdf` tiene 48 páginas; su portada identifica
Licenciatura en Ciberdefensa, “Sistemas de Tratamientos de Datos”, año 2026, y
“Conceptos Fundamentales”. Otro material del directorio identifica la misma
materia y 64 horas. Los PDFs versionados/materiales locales también incluyen
fundamentos del modelo relacional, álgebra relacional, diseño de bases de
datos, normalización y SQL; apoyan que la etiqueta “Sistemas de Transmisión de
Datos” del prompt es incorrecta. Al revisar el programa analítico 2026
compartido posteriormente por el usuario, se confirmó que contiene siete
módulos y bibliografía, pero señala 60 horas, en discrepancia con las 64 horas
del plan de estudios público de la carrera y de otro material local. La
identidad y el área quedan corroboradas; la carga horaria requiere
reconciliación documental, no inferencia.

**Caracterización de pruebas:** el primer comando focalizado intentó ejecutar
`tests/pedagogy/test_adaptive_pipeline.py`, ruta inexistente; no llegó a
ejecutar pruebas. Se corrigió a
`tests/unit/pedagogy/test_adaptive_pipeline.py`. El comando corregido,
compuesto por `test_socratic_system_prompt.py`,
`test_pedagogical_contract_persistence.py`,
`test_talos_vs_notebooklm_e2e.py`, `test_f5_context_containment.py`,
`test_chat_sse_endpoint.py`, `test_adaptive_pipeline.py` y
`test_chat_content_registry.py`, terminó con **100 passed, 19 warnings, 0
failed** en 20.85 s. Los warnings son principalmente deprecaciones
FastAPI/Starlette. No se ejecutó suite global durante G2.0 porque no hubo
cambios de producto y la meta era caracterizar el estado anterior al gate.

**Conclusión de G2.0:** los hallazgos H1–H3 se reproducen; H2 queda resuelto
respecto al nombre/área de la materia y pendiente respecto al programa detallado.
Surge un bloqueo adicional de gobernanza curricular: el `curriculum_id` de las
filas SQLite locales difiere de los IDs específicos del catálogo, y el registro
de federación no modela ese campo. Antes de escribir el resolver final se debe
decidir cuál registro es autoridad para cada entorno y si esos notebooks locales
son estado versionado/provisionado o instalaciones históricas. No se deben
sincronizar ni migrar automáticamente.

**Estado al cierre de G2.0:** no se había alterado código de runtime,
catálogos ni filas SQLite; esa entrega cerró únicamente la fase de
inventario/caracterización. Las implementaciones y mediciones posteriores se
registran en las secciones G2.1 y siguientes.

#### Resultado ejecutado — paso 1: identidad y alta — 2026-09-28

Se contrastaron de solo lectura `DEFAULT_NOTEBOOKS`,
`config/notebook_kc_catalog.json`, `config/notebook_source_roles.json` y
`data/web_state/knowledge_store.db`. La reconciliación operativa queda así:

| IDs | Identidad aceptada para Gate 2 | `curriculum_id` de catálogo | Estado SQLite local |
|---|---|---|---|
| `fase0-soc` | Scope Roadmap/Fase 0; identidad canónica exacta | `roadmap_kasiu_v4_fase0` | `fadena_v1` (discordante) |
| `fadena-lenguajes` | Materia FADENA de Lenguajes | `fadena_lenguajes_2026` | `fadena_v1` (discordante) |
| `fadena-so2` | Materia FADENA de Sistemas Operativos II | `fadena_so2_2026` | `fadena_v1` (discordante) |
| `fadena-std` | Materia FADENA de Tratamiento de Datos | `fadena_std_2026` | `fadena_v1` (discordante) |
| `fadena-teleco` | Materia FADENA de Telecomunicaciones | `fadena_teleco_2025` | `fadena_v1` (discordante) |
| `fadena-sye` | Entrada curricular separada; no habilitada como perfil operativo todavía | `fadena_sye_2026` | Hay placeholder local con `curriculum_id` y `subject` nulos, sin asociaciones |
| `fadena-prog`, `fadena-so` | IDs legacy preservados como scopes distintos; no se redirigen ni migran | Sin mapeo confirmado | `fadena_v1` |
| `NB-CYBERSECURITY-V1` | Notebook de Seguridad independiente, no alias FADENA | Sin mapeo confirmado | `fadena_v1` |
| `NB-SEC-01-C-PTR` | Scope del nodo `SEC-01-C-PTR` en `ROADMAP-CYBERSECURITY-V1`; independiente del notebook general de Seguridad | Sin `curriculum_id` de curso declarado en el roadmap | Fila local con subject `Cybersecurity`, currículo nulo, 42 asociaciones (una huérfana) |
| `nb_prog_1`, `nb_prog_basica` | Instalaciones locales/custom sin identidad curricular confirmada | Sin mapeo confirmado | Currículo nulo, sin asociaciones |

El catálogo KC versionado es la fuente de los IDs curriculares de aplicación
para las seis entradas que contiene; eso no certifica por sí mismo que cada
programa o título tenga autoridad académica oficial. La columna persistida en
SQLite representa estado de instalación y no prevalece sobre ese mapeo de
configuración. No se actualizaron `fadena_v1` ni ningún otro dato local. Los
aliases legacy tampoco se colapsan: los bridges versionados los nombran como
scopes distintos y no declaran una identidad curricular canónica equivalente.

La configuración de roles de fuentes cubre únicamente los cinco perfiles
centrales y no constituye autorización de acceso. La allowlist efectiva de
retrieval es la relación `notebook_sources` de SQLite. El bootstrap versionado
puede poblar esa relación a partir de `DEFAULT_NOTEBOOKS.sources`; esa
asociación declarada es distinta del rol (`PRIMARY`, `COMPLEMENTARY`, etc.).
La lista duplicada `Notebook.sources` no coincide en todos los casos con los
roles configurados ni con las asociaciones locales. Por eso, la configuración
de roles por sí sola no autoriza fuentes, no se usa para ampliar el scope y sus
diferencias restantes deben reconciliarse antes de habilitar más currículos.

Se encontró que `POST /api/notebook/{notebook_id}/upload-source` creaba
silenciosamente una fila de notebook si el ID no existía, deduciendo carpeta
por subcadena y dejando `subject`/`curriculum_id` sin validar. El flujo ahora
exige que el notebook esté previamente registrado y responde 404 antes de
guardar o indexar el archivo si falta. Esto conserva carga en notebooks
persistidos, incluidos scopes custom, pero no inventa una identidad curricular.
`sync-sources-folder` aplica la misma condición y tampoco crea filas por
subcadena. El provisionamiento inicial asigna a los IDs presentes en el
catálogo KC su `curriculum_id` por clave exacta; los aliases/custom sin mapeo
quedan sin currículo declarado. Fallos al leer el catálogo, registrar notebooks
o vincular fuentes ya no se silencian durante ese provisionamiento. Las filas
existentes no se reescriben ni migran. Pruebas focalizadas cubren ambas rutas
desconocidas y la resolución exacta de IDs curriculares.

**Ciclo de alta acordado para esta fase:** registrar explícitamente el notebook
y su identidad; asociar solo fuentes autorizadas mediante `notebook_sources`;
definir el rol de cada fuente en el scope; validar que notebook/catálogo/rol y
fuentes existen; luego habilitar la carga. La creación automática desde una
carga queda prohibida. La interfaz administrativa completa para ese ciclo no
existe todavía y es trabajo separado; hasta definirla, un nuevo cuaderno debe
provisionarse explícitamente y no se considera habilitado solo por aparecer en
el catálogo KC.

**Pendientes explícitos de reconciliación:** decidir si `fadena-sye` se habilita
como scope activo y qué fuentes autorizadas tendrá; decidir la asignación
curricular de las instalaciones custom que no tienen `curriculum_id`; reemplazar
o reparar el `fadena_v1` genérico de las cinco filas principales solo después de
un proceso de migración con copia y respaldo; y alinear la lista de fuentes del
registro federado, la configuración de roles y las asociaciones locales sin
otorgar permisos implícitos. No se migró SQLite ni se declaró cerrada la
autoridad oficial de programas/bibliografía.

#### Resultado ejecutado — paso 2: allowlist, fallbacks y scopes — 2026-09-28

Se implementó y probó el primer contrato fail-closed de scope:

- `TwoStageRetriever._fts5_prefilter()` ahora aplica `source_filter` en el SQL
  junto con el join de `notebook_sources`. Si falla el query, registra el error
  y retorna cero candidatos; ya no reintenta leyendo `chunks` sin join de ACL.
  Un allowlist vacío también retorna cero resultados sin consultar el store.
- `MultiSourceEvidenceAssembler` intersecta las fuentes con roles contra las
  asociaciones reales del notebook. Se eliminó el recorrido de `list_sources()`
  global cuando faltan citas. Menos de dos citas autorizadas termina en
  evidencia insuficiente/abstención, en vez de rellenar desde otro cuaderno.
- El chat deriva las fuentes permitidas desde `notebook_sources`; para un scope
  de carpeta enumera solo notebooks de esa carpeta y descendientes. La búsqueda
  híbrida y de resúmenes de capítulo se ejecuta por esos notebooks, no contra
  el corpus global sin filtro. Una fuente curricular compartida con Roadmap
  solo aparece allí cuando hay una asociación explícita al notebook Roadmap.
- `active_sources` se interpreta como restricción, nunca como autorización:
  IDs o hashes solicitados se intersectan con la allowlist de servidor. Una
  lista vacía o que solo contiene IDs/hashes ajenos abstiene antes de invocar
  al backend. La allowlist efectiva se pasa a búsqueda FTS/densa/híbrida y se
  vuelve a aplicar antes de construir citas.
- `KnowledgeStore.search()`, `fts_search()`, `vector_search()` y
  `search_hybrid()` admiten `source_ids`. El vector search restringe los
  candidatos por chunk asociado a notebook y source antes de escoger top-k,
  aunque la carga/cálculo de la matriz completa del notebook sigue pendiente
  del trabajo de capacidad G2.3.

La prueba de frontera entre carpetas se actualizó: una consulta técnica desde
FADENA ya no recibe material de un notebook Roadmap ubicado fuera de esa
carpeta. Una segunda prueba demuestra que el mismo material FADENA sí puede
recuperarse desde Roadmap después de agregar explícitamente el vínculo
`notebook_sources` correspondiente. Esto reemplaza la expectativa anterior de
“acceso global a todos los notebooks” para una consulta desde cualquier
carpeta.

**Verificación focalizada:** el conjunto Gate 2 de scopes, recuperación,
fallbacks, upload/sync y chat terminó con **40 passed, 11 warnings, 0 failed**
en 35.12 s. Una ejecución separada de fallback/context flood/capítulos también
terminó con **23 passed, 2 warnings, 0 failed** en 19.37 s. Los warnings
observados son deprecaciones FastAPI/Starlette. `compileall`,
`git diff --check` y flake8 de errores de sintaxis/nombres (`E9,F63,F7,F82`)
pasaron. El black check integral de módulos preexistentes señala formato
previo fuera de Black; los tests nuevos quedaron formateados. La suite global
se ejecutó después de los cambios de aislamiento y terminó con **2717 passed,
7 skipped, 146 warnings, 0 failed** en 381.40 s. Un test de seguimiento
conversacional requirió completar su fixture con el vínculo explícito de fuente
autorizada; el test corregido pasó y la suite global completa pasó al repetirse.
No se migraron filas locales ni se escribieron embeddings de forma intencional.
Una prueba focalizada de aplicación pudo abrir el vector store local: su
`mtime` avanzó el 2026-09-28 a las 18:24:39 (-0300), manteniendo el tamaño
303.194.112 bytes para knowledge store y 1.369.837.568 bytes para vector store.
Una lectura posterior estrictamente `mode=ro` mostró WAL, 287.075 embeddings y
los mismos conteos por notebook inspeccionados previamente; no había sidecars
WAL/SHM ni procesos de prueba activos. No existe checksum previo para probar
identidad byte a byte, por lo que la base vectorial queda marcada como no
certificada byte a byte desde esa ejecución. Las siguientes pruebas de
aplicación deben usar snapshots temporales.

Comandos focalizados usados:

```bash
.venv/bin/python -m pytest -q \
  tests/unit/web/test_global_scope.py \
  tests/unit/web/test_retrieval_scope_allowlist.py \
  tests/unit/retrieval/test_two_stage_scope.py \
  tests/pedagogy/test_evidence_assembler_isolation.py \
  tests/unit/storage/test_hybrid_search.py \
  tests/security/test_long_context_invariants.py \
  tests/unit/retrieval/test_context_flood.py \
  tests/retrieval/test_hierarchical_rag.py \
  tests/web/test_notebook_upload_identity.py \
  tests/pedagogy/test_chat_sse_endpoint.py

.venv/bin/python -m pytest -q \
  tests/unit/retrieval/test_two_stage_scope.py \
  tests/pedagogy/test_evidence_assembler_isolation.py \
  tests/unit/storage/test_hybrid_search.py \
  tests/unit/web/test_retrieval_scope_allowlist.py \
  tests/unit/retrieval/test_context_flood.py \
  tests/retrieval/test_hierarchical_rag.py
```

**Pendiente dentro de G2.2:** las funciones de importación inicial pueden
seguir poblando associations desde la lista versionada `DEFAULT_NOTEBOOKS`;
debe cerrarse la matriz exacta de fuentes permitidas por curso/Roadmap antes de
dar por reconciliadas todas las asociaciones heredadas. La lógica de permisos
de folder se verificó con fixtures deterministas; falta probar el mismo caso
contra una copia aislada del corpus real, sin modificar `data/web_state`.

#### G2.0b — Currículos recibidos y modelo FADENA ↔ Roadmap SOC

El usuario proporcionó los programas curriculares actuales de FADENA y
`RoadmapV4`. Se consultaron como documentos locales; no se copiaron a este
repositorio. El PDF cubre las materias de Lenguajes de Programación
(10 unidades), Infraestructura de Telecomunicaciones (12), Sistema de
Tratamiento de Datos (7 módulos) y Sistemas Operativos II (6 unidades). Esos
datos permiten validar los conteos que faltaban, las materias y los objetivos
por curso. No convierten automáticamente cada título, autor o rol de fuente
del catálogo existente en metadato oficial: la malla y bibliografía deben
transcribirse desde los documentos y mantener su procedencia.

`RoadmapV4` se define como mapa del dominio y norte estratégico, no como el
programa diario de una materia. Su plan operativo se formula como Roadmap
consolidado Fase 0 + materias FADENA e incluye fases, gateways y habilidades
transversales. La relación de producto adecuada no es elegir entre facultad o
autoaprendizaje:

- **Cuaderno FADENA:** alcance curricular de una materia, programa oficial,
  fuentes de cátedra y referencias aprobadas para esa materia. Por defecto no
  consulta fuentes de otras materias FADENA.
- **Roadmap SOC:** alcance transversal para ver conexiones, prerequisitos,
  secuencia de aprendizaje y proyectos que cruzan materias. Puede consultar
  material de materias FADENA solo mediante una asociación/publicación explícita
  al corpus del Roadmap; no debe convertir el hecho de que los datos existan en
  la misma base en autorización implícita.
- **Compartir no implica duplicar:** SQLite ya modela `notebook_sources` como
  relación muchos-a-muchos entre notebook y source. La opción preferida es
  autorizar la misma fuente/chunks en la colección Roadmap agregando una
  relación explícita, no copiar el PDF ni los chunks. La visibilidad es
  direccional según los vínculos autorizados: compartir una fuente con Roadmap
  no la comparte con todos los otros cuadernos FADENA. **La capa vectorial
  actual sí particiona embeddings por `notebook_id`** (PK `(chunk_id,
  notebook_id)` y `get_vector_matrix()` filtra por notebook); la asociación
  `notebook_sources` por sí sola no comparte embeddings. La ingesta tendría
  que crear registros vectoriales autorizados para cada scope, o se debe
  diseñar y medir una capa de embeddings por source con ACL en la consulta.
  No decidir la estrategia ni el costo de almacenamiento por suposición.

La interacción debería combinar **ruta de estudio**, **autoridad de fuente** y
**tipo de consulta**, sin pedirle al usuario que vuelva a configurar todo en
cada turno:

1. El usuario elige el contexto: una materia FADENA, el Roadmap completo o una
   ruta concreta del Roadmap que cruza materias. Para una ruta, TALOS mantiene
   el nodo/objetivo actual, sus prerequisitos y las materias/fuentes que la
   ruta autoriza.
2. En consulta ordinaria, prioriza la fuente oficial/PRIMARY del curso o nodo
   activo, y completa con fuentes aprobadas cuyo rol y tema correspondan. Las
   referencias secundarias no deben desplazar silenciosamente una discrepancia
   con el programa o material de cátedra.
3. Un selector/intención explícita puede ajustar el conjunto ordenado:
   **seguir programa** (currículo + PRIMARY), **profundizar** (PRIMARY +
   FORMAL/METHODOLOGICAL/COMPLEMENTARY pertinentes), **aplicar/laboratorio**
   (IMPLEMENTATION aprobadas), **comparar fuentes** (mostrar perspectivas y
   discrepancias), o **síntesis de ruta** (nodos de varios currículos y sus
   fuentes autorizadas). Son políticas de retrieval y evidencia; no cambian
   automáticamente la identidad curricular ni los hechos permitidos.
4. La interfaz debe mostrar qué alcance y fuentes efectivas se consultaron,
   permitir acotar o ampliar entre fuentes ya autorizadas para ese alcance y
   hacer que una restricción explícita del turno prevalezca sobre el modo por
   defecto. Un `source_id` enviado por el cliente nunca puede ampliar la lista
   de fuentes autorizadas.

Esta separación hace posible que un pedido “seguí esta ruta” use material
principal de FADENA para el tema puntual y referencias profundas de la ruta
cuando sean pertinentes, mientras la respuesta distingue qué afirma la cátedra
y qué agrega el complemento. Evita tanto la búsqueda indiscriminada en todos
los cuadernos como la falsa elección entre aislamiento estricto y visión
integral.

**Hallazgos de retrieval que se deben tratar antes de ampliar el acceso:**

- `KnowledgeStore.search()` y `search_hybrid()` aceptan `notebook_id` y hacen
  retrieval lexical/denso acotado a fuentes vinculadas a ese notebook. FTS5 y
  `notebook_sources` son una base útil para aislamiento; las matrices densas
  se recuperan por notebook. El retriever híbrido tiene top-k acotado.
- `SQLiteVectorStore` retiene hasta ocho matrices en su LRU (la clave incluye
  notebook/proveedor/modelo). No se midió cuánto ocupa cada matriz ni la RAM
  pico actual. Ese límite ya es una política de caché, pero ocho matrices
  grandes podrían ser significativas; no reducirlo o aumentarlo sin medición.
- `TwoStageRetriever._fts5_prefilter()` captura cualquier excepción de la
  consulta con join de `notebook_sources` y luego reintenta una consulta FTS
  sin el filtro de notebook ni `source_filter`. Si el primer SQL falla, el
  fallback puede devolver chunks de otros cuadernos. Esto es un defecto de
  aislamiento/corrección que debe corregirse o eliminarse antes de aceptar
  fallbacks multi-cuaderno; el comportamiento correcto es fail-closed o un
  fallback que preserve todos los filtros.
- `MultiSourceEvidenceAssembler` busca por rol recorriendo fuentes y lee chunks
  por fuente; si obtiene menos de dos citas salta a `list_sources()` y prueba
  fuentes globales que no están asignadas al notebook. Esa ruta pertenece al
  `PedagogicalOrchestrator`, distinta del chat principal, pero viola el
  aislamiento esperado en esa superficie y puede gastar trabajo innecesario.
  El fallback debe limitarse a fuentes autorizadas del cuaderno/ruta o
  abstenerse.
- En el chat, el `active_sources` opcional se aplica después de obtener
  resultados de búsqueda. El notebook limita el conjunto inicial, pero este
  filtro tardío puede gastar recuperación/reranking en fuentes que finalmente
  se descartan. Al implementar modos de fuente, validar del lado servidor la
  intersección con fuentes autorizadas y empujar el filtro a SQL/vector search
  cuando corresponda, manteniendo fail-closed.

**Decisión sobre optimización:** sí, Gate 2 debe incluir criterios de memoria,
latencia, candidatos y concurrencia porque el Roadmap tendrá un corpus mayor;
no significa hacer ahora una refactorización general de SQL ni crear un
proceso por cuaderno. Los stores son SQLite local; el motor de almacenamiento y
el vector store usan WAL. El coste dominante que debe medirse incluye
carga/decodificación de la matriz densa, búsqueda sobre los vectores del
notebook, candidatos, reranking y expansión de alcance. La arquitectura
recomendada primero es acotar por notebook/ruta y source allowlist, obtener un
pool pequeño y rerankear solo el pool; definir también cómo evitar duplicar
embeddings donde la semántica de ACL permita compartirlos.

Antes de cualquier optimización, capturar con corpus y consultas fijas:

- latencia p50/p95 de FTS, denso, híbrido y endpoint completo, en frío/caliente;
- RSS/peak RSS en arranque, primera consulta y cambio de notebook/ruta;
- número de fuentes y chunks candidatos antes/después del filtro, y top-k
  retornado;
- número de matrices cargadas/evictadas y bytes estimados según dimensiones;
- comportamiento con consultas sobre una materia, una ruta multi-materia,
  `PRIMARY` únicamente, profundización y cambio de scope;
- aislamiento adversarial: fuente vinculada a otro cuaderno, cliente que pide
  un `source_id` no autorizado, error del join de notebook, y evidencia
  insuficiente que active fallback.

No inventar umbrales de RAM/latencia sin requisito de despliegue: fijar primero
un baseline reproducible en el dispositivo objetivo y luego acordar presupuesto
de memoria y SLA. Sí son invariantes no negociables, aunque la métrica pase:
cero resultados de fuentes no autorizadas, número de candidatos acotado,
ninguna carga de corpus global por consulta ordinaria y citas trazables al
programa/fuente que realmente respalda la respuesta.

#### G2.0c — Capacidad de crecimiento: evidencia local y riesgo

Se hizo una inspección SQLite de solo lectura del estado local en
`data/web_state` el 2026-09-28; no se modificó la base:

| Almacén | Filas | Tamaño del archivo principal |
|---|---:|---:|
| `knowledge_store.db` | 12 notebooks, 76 sources, 115 documents, 105.705 chunks, 151 asociaciones notebook-source | 303.194.112 bytes (~289 MiB) |
| `vector_store.db` | 287.075 embeddings | 1.369.837.568 bytes (~1,28 GiB) |

El vector store contiene siete scopes grandes con Qwen3 de 1.024 dimensiones.
El mayor tiene 105.179 vectores (430.788.608 bytes de BLOBs); otros scopes
también contienen sus propias filas para IDs de chunks compartidos. Aparecen
103.924 IDs de chunk en más de un notebook. Esto confirma que, en el esquema e
ingesta actuales, la proyección M:N de fuentes a notebooks no implica deduplicar
embeddings: `chunk_embeddings` tiene clave `(chunk_id, notebook_id)`. Los
embeddings repetidos por scope pueden dominar el crecimiento del almacén
vectorial.

Estas cifras describen los archivos locales inspeccionados, no un benchmark de
latencia ni una promesa de que todos los despliegues contengan el mismo corpus.
Tampoco incluyen necesariamente WAL/SHM u otros archivos auxiliares. La cabecera
de `two_stage.py` menciona 31.114 chunks y ~15 ms, pero es texto estático del
módulo: no es evidencia de medición vigente para esta base de 105.705 chunks.

Hay dos perfiles de retrieval y no deben confundirse:

- `TwoStageRetriever` mantiene fijo el prefiltrado FTS5 (100 candidatos por
  defecto) y calcula el reranking sobre ese conjunto. Su coste del reranking
  queda acotado respecto del tamaño del corpus, aunque el índice FTS, filtros,
  autorización e ingesta sí crecen.
- `KnowledgeStore.vector_search()` carga la matriz completa del notebook,
  normaliza todas sus filas y calcula similitud para cada vector antes de
  extraer top-k. El coste de cómputo es lineal en `vectores_del_scope ×
  dimensiones`; no se reduce por pedir un `limit` pequeño. Para 105.179
  vectores de 1.024 dimensiones, solo una matriz float32 equivale a unos
  431 MB decimales. Durante una consulta se conserva la matriz cacheada y se
  crea otra matriz normalizada de tamaño comparable; al cargar en frío, la
  lista de BLOBs y la concatenación temporal elevan el pico aún más. La caché
  LRU permite ocho claves por instancia/proceso, de modo que el uso puede
  multiplicarse con scopes grandes y con workers/procesos concurrentes. El
  baseline inicial de abajo ya midió RSS pico para dos scopes principales, pero
  no incluye todavía el mayor scope custom de 105.179 vectores.

**Dictamen:** el sistema puede seguir siendo manejable para el uso local si el
crecimiento se gobierna, pero el código actual no garantiza rendimiento
constante ante crecimiento ilimitado. Más PDFs por sí solos no determinan el
costo: importan páginas útiles, tamaño/solapamiento de chunks, cantidad de
versiones retenidas, dimensiones/modelos de embedding, número de scopes en los
que se replica cada vector, consultas y concurrencia. En particular, un
Roadmap transversal construido replicando vectores por notebook puede crecer
mucho más rápido que el contenido único. No conviene habilitar una ingestión
masiva multi-cuaderno antes de resolverlo.

La secuencia segura de capacidad para G2/Gate de retrieval es:

1. **Congelar un baseline reproducible** sobre la base existente, incluyendo
   consultas reales (FTS, denso e híbrido) en frío/caliente, RSS pico por
   proceso, latencia p50/p95, tasa de aciertos de caché, bytes de matriz,
   número de candidatos y concurrencia representativa. Separar primera carga,
   cambio de notebook y consulta sostenida.
2. **Medir curvas, no solo un punto:** usar copias temporales del corpus para
   probar aproximadamente 1×, 2× y 5× de chunks y scopes; incluir fuentes
   compartidas y una ruta Roadmap multi-materia. Registrar tamaño y tiempo de
   ingesta, archivo SQLite/WAL, tiempo de consulta y memoria. No modificar la
   base de usuario para crear las muestras.
3. **Eliminar el costo no acotado de la ruta densa:** primero filtrar por
   fuentes autorizadas y generar un pool candidato con FTS/índice; puntuar
   densamente solo ese pool. Si se conserva búsqueda densa global, medir y
   documentar su límite de corpus y memoria. Reutilizar la selección
   cacheada/normalizada de forma segura o limitar bytes del LRU (no solo número
   de cuadernos), y contabilizar todos los workers.
4. **Evitar duplicar vectores innecesariamente:** estudiar vector por
   `(source/chunk, provider, model)` compartido, con autorización por las
   asociaciones notebook-source antes de exponer candidatos. Comparar costo y
   complejidad ACL con la proyección por scope actual; aplicar solo con pruebas
   de aislamiento y migración. Mantener versionado/hash idempotente para no
   retener revisiones obsoletas accidentalmente.
5. **Definir un presupuesto del dispositivo objetivo:** fijar máximo de RAM
   disponible para TALOS, latencia aceptable, notebooks activos, consultas
   simultáneas y tamaño esperado del corpus. Usar estos requisitos para los
   gates de aceptación; no inventar un SLA en abstracto.
6. **Escalar tecnología solo por evidencia:** FTS5/SQLite siguen siendo opción
   razonable si el baseline cumple el presupuesto. Si el scan denso, la
   concurrencia de escritura o tamaño de base lo incumplen tras limitar
   candidatos y deduplicar, evaluar un índice ANN/vector store dedicado; no
   migrar ahora por moda ni asumir que SQLite es infinitamente escalable.

#### Resultado ejecutado — baseline de retrieval en hardware destino — 2026-09-28

Se congeló un runner repetible en
[`scripts/benchmark_gate2_retrieval.py`](../scripts/benchmark_gate2_retrieval.py).
El runner crea snapshots SQLite mediante la API de backup en un directorio
temporal, ejecuta los workers contra esas copias y elimina el temporal al salir.
El constructor del vector store nunca abre directamente la base original.
Comandos ejecutados (12 iteraciones calientes por operación; 10 y 20 requests
en cada nivel de concurrencia):

```bash
.venv/bin/python scripts/benchmark_gate2_retrieval.py \
  --notebooks fadena-std --iterations 12 --concurrency 5 10 \
  --allow-concurrent-load
.venv/bin/python scripts/benchmark_gate2_retrieval.py \
  --notebooks fase0-soc --iterations 12 --concurrency 5 10 \
  --allow-concurrent-load
```

Hardware: AMD Ryzen 5 5600GT, 12 CPUs lógicas, 13 GiB RAM, Linux x86_64.
Los dos scopes medidos usan vectores consistentes de 1.024 dimensiones;
`NB-SEC-01-C-PTR`, con dimensiones mezcladas, se excluyó. La búsqueda densa
calcula sobre todas las filas del notebook antes de devolver el top-k. RSS es
peak RSS del proceso worker; incluye Python/NumPy y buffers temporales.

| Scope | Vectores escaneados | Matriz float32 estimada | FTS frío / caliente p50-p95 ms | Denso frío / caliente p50-p95 ms | Híbrido frío / caliente p50-p95 ms | RSS peak FTS / denso / híbrido |
|---|---:|---:|---:|---:|---:|---:|
| `fadena-std` | 46.530 | 190.586.880 B | 5,35 / 4,37-5,43 | 864,85 / 147,12-161,16 | 865,59 / 151,74-164,15 | 60,4 / 621,5 / 622,4 MiB |
| `fase0-soc` | 43.214 | 177.004.544 B | 2,37 / 1,08-1,64 | 805,86 / 134,77-143,79 | 800,02 / 136,95-149,33 | 59,5 / 581,2 / 580,7 MiB |

“Frío” significa caché de matriz SQLite vacía al comenzar el proceso, no
almacenamiento físico frío: el page cache del SO no se vació y puede estar
caliente. La consulta densa usa `DeterministicHashEmbedder(1024)` para aislar
la ruta de puntuación; no mide inferencia del modelo de producción ni calidad
semántica. En estos dos scopes la ruta densa escanea 43-46 mil vectores aunque
el límite final sea 30; por eso el tiempo caliente es ~135-165 ms y el peak RSS
~581-622 MiB por proceso.

En híbrido, carga representativa medida:

| Scope | Workers | QPS | Errores | p50 / p95 ms | Peak RSS del proceso |
|---|---:|---:|---:|---:|---:|
| `fadena-std` | 5 | 8,86 | 0/10 | 222,63 / 1.087,68 | 776,7 MiB |
| `fadena-std` | 10 | 8,70 | 0/20 | 634,69 / 2.141,11 | 1.125,1 MiB |
| `fase0-soc` | 5 | 10,89 | 0/10 | 385,75 / 844,20 | 1.209,6 MiB |
| `fase0-soc` | 10 | 11,22 | 0/20 | 394,97 / 1.715,15 | 1.211,3 MiB |

La tabla conserva resultados del runner anterior, que reportaba intentos por
segundo como `QPS`. Todos los casos de esta tabla tuvieron cero errores, por lo
que esos valores también equivalen a éxitos por segundo. El runner actual
expone `attempt_qps`, `successful_qps` y `error_rate_pct` por separado; no se
volvió a ejecutar el benchmark ni se reescribió esta evidencia histórica.

Es una línea base de **retrieval**, no del endpoint completo: no incluye
resolución de prompt/perfil, compilación de contexto, backend LLM ni inferencia
de embeddings. Las dos consultas son representativas pero no bastan para medir
calidad curricular; los conteos de retorno no equivalen a Recall/MRR. No se
fijaron umbrales de aceptación porque aún falta acordar el presupuesto de RAM
y SLA. El resultado confirma que candidate retrieval acotado es prioritario;
no autoriza aún una migración a ANN ni cambios de ranking. La ruta
multi-materia, el cambio de scope y el baseline de endpoint quedan pendientes.

El runner pasó `compileall`, flake8 selectivo (`E9,F63,F7,F82`), Black para
Python 3.12 y una ejecución smoke sobre un snapshot temporal. La salida
completa se emite a stdout; no deja bases ni resultados generados en el árbol
del repositorio.

La curva sintética 1×/2×/5× se midió con
[`scripts/benchmark_gate2_growth.py`](../scripts/benchmark_gate2_growth.py),
replicando en snapshots descartables los chunks autorizados y sus vectores
1024d. Se ejecutó:

```bash
.venv/bin/python scripts/benchmark_gate2_growth.py \
  --notebooks fadena-std fase0-soc --factors 1 2 5 --iterations 12 \
  --allow-high-load
```

Cada factor vuelve a crear snapshots desde la base original; la duplicación
activa triggers FTS y mantiene las búsquedas/citas conectadas a chunks. Es una
curva de capacidad con contenido repetido: el tiempo SQL de duplicación no
equivale a ingesta real (parseo, embedding y validación), y los resultados no
sirven para evaluar calidad ni diversidad semántica.

| Scope | Factor | Chunks/vectores | Bytes de matriz | DB conocimiento / vector | Tiempo SQL de duplicación | Híbrido caliente p50/p95 | Híbrido primer query | RSS peak híbrido |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `fadena-std` | 1× | 46.530 | 190.586.880 | 303.194.112 / 1.369.837.568 | 0 s | 152,21 / 164,98 ms | 899,30 ms | 621,9 MiB |
| `fadena-std` | 2× | 93.060 | 381.173.760 | 329.932.800 / 1.592.197.120 | 6,626 s | 288,47 / 321,27 ms | 1.680,28 ms | 1.184,5 MiB |
| `fadena-std` | 5× | 232.650 | 952.934.400 | 594.296.832 / 2.259.300.352 | 21,288 s | 729,05 / 764,86 ms | 5.254,17 ms | 2.867,4 MiB |
| `fase0-soc` | 1× | 43.214 | 177.004.544 | 303.194.112 / 1.369.837.568 | 0 s | 133,48 / 143,99 ms | 759,70 ms | 580,8 MiB |
| `fase0-soc` | 2× | 86.428 | 354.009.088 | 319.959.040 / 1.575.890.944 | 5,115 s | 277,17 / 304,37 ms | 1.535,36 ms | 1.103,2 MiB |
| `fase0-soc` | 5× | 216.070 | 885.022.720 | 556.089.344 / 2.194.055.168 | 21,658 s | 672,57 / 714,75 ms | 4.542,22 ms | 2.665,8 MiB |

Los tiempos del primer query mantienen la misma limitación de caché del SO
explicada arriba. El aumento de RAM observado es congruente con escaneo denso
lineal y buffers de carga/normalización; a 5× el proceso ronda 2,6–2,9 GiB.
No correr 5× con concurrencia alta hasta fijar presupuesto de memoria. El FTS
caliente también creció al duplicar chunks (para `fadena-std`, p95 4,97 /
9,30 / 18,43 ms en 1×/2×/5×), pero esta métrica conserva contenido repetido
y no modela con exactitud la distribución de términos de un corpus nuevo.

El runner de crecimiento pasó `compileall`, flake8 selectivo
(`E9,F63,F7,F82`), Black para Python 3.12, un smoke 1×/2× y la corrida completa
1×/2×/5×. Ambos runners emiten la salida a stdout y limpian los snapshots
temporales al salir; no dejan bases ni resultados generados en el repositorio.
Después de la alerta térmica, los defaults se endurecieron: retrieval ahora
ejecuta concurrencia 1 por defecto y requiere `--allow-concurrent-load` para
concurrencia mayor; la curva deja 1×/2× y 4 iteraciones por defecto y requiere
`--allow-high-load` para factor mayor que 2×. No se repitieron mediciones con
esas opciones.

La actualización del `mtime` de la base vectorial se observó después de una
prueba de aplicación focalizada, no durante estos runners. Estos últimos solo
usan snapshots temporales, pero no hay checksum capturado antes de la otra
prueba y no se puede certificar integridad byte a byte retroactivamente.

**Calidad como restricción de diseño, no como optimización posterior.** El
objetivo no es que TALOS responda más rápido usando menos contexto a cualquier
costo; tiene que conservar recuperación amplia de evidencia relevante dentro
del scope autorizado y producir respuestas trazables. El repositorio ya tiene
un `OracleEvaluator` con Recall@1/5, MRR, p50/p95 y detección de candidatos
ilegales, además de benchmarks experimentales con cobertura de subtemas y
fuentes. Esos componentes son una base, pero hay que comprobar qué corpus,
consultas y criterios representan las materias reales antes de usar sus
resultados como garantía.

Todo cambio de indexación, deduplicación, filtros o candidate generation debe
compararse contra el mismo benchmark congelado, antes y después, desglosado por
materia FADENA, Roadmap/ruta, modo (seguir programa, profundizar, aplicar,
comparar) y consultas difíciles. Reportar al menos:

- Recall@5/MRR o métricas de ranking disponibles y cobertura de subtemas/fuentes
  esperadas, tanto globalmente como por curso e intención;
- cero candidatos/fuentes fuera del scope y comportamiento correcto ante
  evidencia insuficiente (abstención, no rellenar con otra materia);
- citas que correspondan a los pasajes recuperados y separación explícita entre
  material PRIMARY/curricular y referencias complementarias;
- evaluación end-to-end de respuestas con una rúbrica humana y casos
  curriculares, no solo métricas de retrieval. Un buen ranking no demuestra por
  sí mismo que la explicación sea exacta, completa y pedagógicamente adecuada.

Un índice aproximado o un pool más pequeño puede bajar latencia y RAM pero
perder evidencia semántica o fuentes minoritarias. Por eso no se acepta una
mejora de capacidad que provoque regresión de calidad fuera de tolerancia; si
hay trade-off, debe hacerse visible por curso/intención y priorizar recuperar
correctamente el contexto autorizado, no ocultar la caída bajo una media
global. Antes de fijar tolerancias nuevas, ejecutar el benchmark real, verificar
si el objetivo documentado de MRR@5 ≥ 0,85 en 400 consultas se aplica al
retriever que se va a cambiar, y congelar los resultados por materia.

**Qué conviene hacer ahora, antes de abrir TALOS al uso amplio:**

1. Cerrar el contrato de scopes/identidad, roles de fuente, asociación
   explícita de corpus al Roadmap, versionado y deduplicación/idempotencia de
   ingesta. Corregir los fallbacks que eliminan el filtro de scope. Esto es
   cimiento funcional y de seguridad; postergarlo encarece migraciones y deja
   ambiguo qué evidencia puede utilizar una respuesta.
2. Construir un benchmark/oráculo de calidad y una rúbrica end-to-end basada en
   los programas actuales de todas las materias más consultas del Roadmap.
   Añadir consultas negativas, sin evidencia, multi-fuente, complementarias y
   de aislamiento. Guardar fixtures/metadatos de origen, no copias privadas
   innecesarias de todos los PDFs.
3. Medir la base actual en el hardware de destino y convertir la memoria,
   latencia, concurrencia y retención de corpus esperado en gates concretos.
4. Refactorizar la ruta densa hacia candidate retrieval acotado autorizado,
   selección vectorial/matriz con límite de bytes y deduplicación solo con ACL
   verificable; cada paso conserva el benchmark de calidad y tiene prueba de
   regresión.
5. Ejecutar pruebas de crecimiento y liberar por etapas. Mantener FTS+ranking
   denso acotado mientras cumpla calidad y capacidad; adoptar ANN/otro motor
   únicamente si las medidas muestran que el diseño acotado todavía incumple
   los presupuestos.

**Respuesta directa a la preocupación de migración:** sí, es preferible hacer
ahora estos cimientos, antes del uso cotidiano y de que los datos activos
dependan de contratos ambiguos. Lo que no sería preferible es anticipar hoy una
migración grande a infraestructura distribuida o seleccionar un ANN sin
baseline, porque puede aumentar complejidad y bajar la calidad sin resolver el
problema real. La base “buena” es scopes correctos + corpus gobernado +
retrieval acotado y evaluable + evidencia de calidad y capacidad; el backend
escalable concreto se decide con esos datos.

#### G2.1 — Fijar el contrato de identidad y fallback

Decisión recomendada para implementar:

- Perfilado primario por ID canónico exacto; aliases heredados solo mediante un
  mapa explícito y revisado. El resolver no debe comparar prefijos,
  subcadenas, nombres de usuario ni aproximaciones.
- Mantener contratos personalizados persistidos como precedencia máxima para
  su `notebook_id`, sujetos a las mismas invariantes de seguridad y aislamiento.
- Para un notebook registrado sin perfil pedagógico propio, usar un contrato
  **neutral**, con una sola fase conceptual general y sin analogías o
  representaciones obligatorias. Un registro inexistente debe conservar el
  error/404 del límite de notebook; no “repararlo” asignándole un perfil similar.
- Mantener el perfil de Fase 0 explícito para `fase0-soc`; no usarlo como
  default universal.
- Los aliases deberán apuntar al mismo perfil solo cuando la identidad,
  materia, currículo y fuentes sean efectivamente equivalentes. Un alias no
  confirmado debe quedar neutral y visible en diagnóstico hasta resolverse.

No migrar automáticamente filas personalizadas de
`pedagogical_contracts` ni reescribir perfiles persistidos: caracterizar antes
su precedencia, formato y compatibilidad con los nuevos defaults.

#### G2.2 — Separar política común de perfil curricular

- Dejar en el prompt base únicamente invariantes universales: honestidad de
  fuentes, respeto del pedido, claridad, adaptación de longitud, no forzar una
  forma y política de solución acordada en Gate 1.
- Mover supuestos de arquitectura/idioma/herramientas —x86-64, ABI, C,
  `malloc`, stack/heap— al perfil o instrucción de turno que corresponda, y
  condicionarlos a material, currículum o pedido verificable. No reemplazar
  una suposición universal por otra (p. ej., SQL en todo Tratamiento de Datos).
- Convertir representaciones del perfil en sugerencias contextuales, no en
  `required_analogies` que obliguen al tutor a usarlas. Los ejemplos admisibles
  pueden documentar opciones por materia: trazas/pseudocódigo para
  programación; estados, planificación e intercalación para SO; modelos y
  transformaciones de datos para Tratamiento de Datos; señales, capas y
  temporización para Telecomunicaciones.
- Corregir la adaptación de `fadena-std` exclusivamente con evidencia
  curricular autorizada. Si el dato no está disponible o es contradictorio,
  dejarlo explícitamente general y registrar la incertidumbre, no fabricar un
  programa preciso.
- Revisar `RIOPLATENSE_SYSTEM_PROMPT` como superficie separada: adaptarlo por
  perfil solo si se confirma un caller productivo multi-cuaderno; de lo
  contrario, registrar que no está en el recorrido principal y crear una tarea
  distinta antes de refactorizarlo.

La forma interna del perfil puede ser una estructura tipada/configuración
validada que agrupe materia, currículum y sugerencias representacionales. No
duplicar manualmente currículos completos dentro de prompts si existe una
fuente canónica consumible. Los textos del prompt deben derivarse de esa
configuración y la procedencia curricular debe seguir inspeccionable.

#### G2.3 — Implementar el recorrido completo y pruebas de frontera

Trazar y comprobar:

`scope resuelto → notebook_id canónico → contrato personalizado/default →
perfil exacto → evidencia/currículum del cuaderno → prompt final del backend`.

Verificar en código qué información del registry/catalog llega hoy al contrato:
la revisión encontró que `chat.py` solicita el contrato por notebook ID, pero
no agrega automáticamente `Notebook.subject`/`curriculum_id` al prompt. No
declarar que el perfil está ligado a fuentes solo porque existan catálogos
independientes. Si no hay una unión segura entre esas autoridades, añadir una
validación determinista de identidad y cobertura; no fusionar catálogos en
runtime de forma implícita.

### Plan de pruebas y criterios de calidad

| Nivel | Prueba requerida | Evidencia esperada |
|---|---|---|
| Unitario: resolución | Todos los IDs canónicos resuelven por igualdad exacta; aliases explícitos resuelven solo donde están declarados; IDs parecidos y desconocidos no heredan adaptación. | Matriz paramétrica `id solicitado → id de perfil`; casos como `fadena-std-extra`, `mi-fadena-so` y cadena vacía. |
| Unitario: fallback | Notebook válido sin perfil obtiene fase conceptual neutral, `required_analogies=[]` y sin plantillas de pseudocódigo/Python/hardware; notebook inválido no evade el 404 del resolver de scope. | Aserciones de campos del contrato, no solo igualdad de texto del prompt. |
| Unitario: política base | La base conserva reglas comunes (citas, fuente, pedido explícito, brevedad); no contiene reglas prescriptivas de ABI/C/RAM ni formatos de una materia. | Assertions positivas y negativas sobre las instrucciones universales relevantes. |
| Unitario: mapeo curricular | Cada perfil tiene el `notebook_id`, `subject` y `curriculum_id` esperados; `fadena-std` usa la materia de datos y metadatos cotejados con la fuente oficial. | Test contra fixtures/catalog canónico y evidencia enlazada del currículo fuente; no contar KCs como unidades automáticamente. |
| Integración: prompt final | Usar backend falso que capture system/user prompts al llamar `/api/chat/query` por currículo. Verificar que lo curricular propio llega al system prompt y que no aparecen instrucciones específicas de los otros currículos. | Por cada materia, captura estructurada reproducible y assertions de contaminación cruzada en la ruta HTTP/SSE real. |
| Integración: pedido del turno | Un pedido breve/concreto no recibe diagrama/analogía/pseudocódigo forzado; pedido explícito de representación pertinente prevalece sobre sugerencias default. | Pruebas deterministas de ensamblado del prompt, sin depender de salida aleatoria del proveedor. |
| Persistencia/compatibilidad | Contrato custom guardado sigue prevaleciendo; al borrarlo, retorna el default correcto; alias legacy conserva su semántica declarada. | Extender `test_pedagogical_contract_persistence.py` y cubrir campos del nuevo perfil/fallback. |
| Regresión de endpoints | Chat multi-cuaderno, scope global, IDs no existentes, comandos estructurados, fase solicitada y política de protección de evaluación se mantienen. | Suites existentes de endpoint, fases, perfiles y solución protegida sin cambios de status/API no intencionales. |
| Higiene | `git diff --check`; enlaces; artefactos de benchmark/supervivencia sin cambios; build/type-check o linter disponible para los módulos tocados. | Salida de comandos y `git status` limpio de archivos generados no esperados. |

**Pruebas focalizadas iniciales sugeridas** (ajustar los nombres solo tras
confirmar el inventario G2.0):

```text
.venv/bin/pytest -q \
  tests/pedagogy/test_socratic_system_prompt.py \
  tests/pedagogy/test_pedagogical_contract_persistence.py \
  tests/pedagogy/test_talos_vs_notebooklm_e2e.py \
  tests/unit/web/test_f5_context_containment.py \
  tests/pedagogy/test_chat_sse_endpoint.py \
  tests/pedagogy/test_adaptive_pipeline.py \
  tests/unit/web/test_chat_content_registry.py
```

Ejecutarlas por separado o en un solo pytest focalizado, según duración.
Después de estabilizarlas, correr `.venv/bin/pytest -q` una vez como regresión
global y verificar que los artefactos versionados sigan intactos. Esta suite
grande detecta regresiones, pero **no sustituye** las comprobaciones
multi-currículo del prompt final.

### Paquete de evidencia y cierre de Gate 2

Registrar en este plan o en el resultado de gate, sin guardar prompts privados
ni salidas de proveedor como oráculos:

1. commit base y commit que implementa Gate 2;
2. tabla de identidad canónica/aliases, materia y `curriculum_id`;
3. para `fadena-std`, título/versión/autoridad de la fuente curricular que
   justificó la etiqueta y los contenidos, o la incertidumbre que quedó;
4. casos unitarios de ID exacto, perfil desconocido/neutral y aislamiento;
5. matriz compacta por currículo con instrucciones propias presentes e
   instrucciones de otros dominios ausentes en el **prompt final**;
6. comandos de prueba, conteos, skips, warnings, duración y fallo conocido;
7. estado de build/lint/type-check aplicable y verificación de no modificación
   de artefactos versionados;
8. límites: componentes no conectados, proveedor real no probado y cualquier
   perfil que siga pendiente de fuente oficial.

**Criterio de aceptación (todos obligatorios):** ningún ID se resuelve por
subcadena; ningún default hereda fases/analogías de Fase 0; los cuatro dominios
mínimos y programación FADENA/Fase 0 reciben perfiles correctos; el prompt
final no contiene contaminación curricular no solicitada; los pedidos del
turno actual y contratos custom conservan precedencia; el caso global sigue
neutral; los tests focalizados y la suite global pasan o cada excepción tiene
causa y alcance explícitos. Si falla la fuente oficial de `fadena-std`, ese
perfil no se considera cerrado aunque pytest pase.

**Salida:** perfil de programación, Sistemas Operativos, Tratamiento de Datos,
Telecomunicaciones y fallback neutral probados desde contrato hasta prompt
final; evidencia que demuestra tanto lo que sí se añade como lo que no se
filtra desde otros cuadernos.

**Estado al 2026-09-28:** se implementó la primera versión tipada de
`NOTEBOOK_PROFILES` y el default consulta `notebooks.curriculum_id` para ligar
perfil y scope por igualdad exacta. `curriculum_id` es la autoridad; no se
requiere igualdad textual del campo `subject`, porque el registro federado y la
etiqueta curricular publicada difieren en `fadena-so2`, `fadena-std` y
`fadena-teleco`. El perfil emite la etiqueta canónica versionada y sugerencias
opcionales. Sin ID curricular o ante un ID/currículum no reconocido, el
contrato queda neutral. No se migraron los registros locales `fadena_v1`, por
lo que esos cuadernos no reciben perfil hasta completar la migración aprobada.

La política base ya no impone x86-64/System V, C, hardware ni representaciones
de Fase 0. Las fases default no obligan a pseudocódigo, Python, analogías o
diagramas; `required_analogies` está vacío. Se mantienen la política de
solución de Gate 1 y la precedencia de contratos pedagógicos custom.

Pruebas: el comando focalizado de resolución, identidad persistida, contrato
custom y captura del prompt SSE terminó con **23 passed, 5 warnings** antes del
ajuste final para que la autoridad sea exclusivamente `curriculum_id`. Tras
ese ajuste y el formato, la suite liviana
`tests/pedagogy/test_socratic_system_prompt.py` +
`tests/pedagogy/test_pedagogical_contract_persistence.py` terminó con
**16 passed, 3 warnings** en 3.98 s; el caso de captura HTTP/SSE no se volvió a
ejecutar para no repetir carga de inicialización. `compileall`, flake8
selectivo y `git diff --check` pasaron. Falta la matriz final de prompts por
cada currículum desde backend HTTP, especialmente con migraciones canónicas
aplicadas y contratos custom.

Verificación adicional de bajo costo posterior al cambio de autoridad:
selección exacta de perfil, IDs desconocidos/parecidos, identidad persistida y
dos casos de prompt pedagógico terminaron con **7 passed** en 0.13 s; no
inicializaron la aplicación ni abrieron bases de corpus. Black, `git diff
--check`, `compileall` y flake8 selectivo siguen pasando.
La igualdad de los cinco `curriculum_id` de `NOTEBOOK_PROFILES` contra
`config/notebook_kc_catalog.json`, incluidos mismatch neutral y perfiles
exactos, añadió **3 passed** en 0.06 s. `fadena-sye` permanece explícitamente
fuera de perfiles activos hasta validar su habilitación operativa.

### Punto exacto para retomar

Identidad/alta, aislamiento de retrieval y baseline de capacidad están
parcialmente cerrados y documentados arriba. No se modificó ni migró la base
local. Sigue Gate 2; no iniciar Gates 3-5 hasta completar estos pendientes, en
este orden:

1. Reconciliar IDs canónicos/aliases, autoridad de `curriculum_id`,
   roles/fuentes y ciclo explícito de alta. No ampliar autorizaciones por
   inferencia ni migrar la base local durante la reconciliación.
2. Congelar el benchmark curricular/end-to-end con oráculo de calidad: corpus,
   consultas, fuentes esperadas, negativas, casos sin evidencia y rúbrica.
   Las mediciones sintéticas de capacidad 1×/2×/5× no sustituyen esta salida.
3. Completar el recorrido de perfiles hasta el prompt HTTP/SSE final por
   currículo, incluyendo fallback neutral, precedencia de contratos custom,
   pedidos explícitos y pruebas de ausencia de contaminación curricular.
4. Completar el baseline real de capacidad: calidad/Recall-MRR por materia e
   intención, latencia p50/p95, memoria, candidatos, caché, cambio de scope,
   ingesta y concurrencia. Las cargas que puedan reproducir el evento térmico
   se reservarán para un entorno con límites y monitoreo adecuados.
5. Implementar candidate retrieval denso acotado por scope y ACL, y comparar
   calidad, aislamiento, latencia y memoria contra el benchmark congelado.
   Evaluar deduplicación vectorial solo con autorización explícita demostrable;
   no correr 5× concurrente en el hardware local sin presupuesto aprobado.
6. Cerrar Gate 2 con decisiones y evidencia reproducible. Recién después
   continuar Gate 3 (F5), Gate 4 (SSE/UI F6) y Gate 5 (regresión global y
   habilitación PED-F7), respetando esas dependencias.

### Diseño de implementación — paso 1: reconciliar identidad y fuentes

**Objetivo:** producir una matriz revisada de identidad, currículo y fuentes
por notebook que distinga configuración declarativa de autorización efectiva.
Este paso es de inventario y decisión; no modifica filas, embeddings ni
asociaciones de la base local y no habilita automáticamente notebooks nuevos.

#### Entradas y autoridad de cada dato

| Dato | Fuente que se inspecciona | Cómo se usa; qué no debe inferirse |
|---|---|---|
| `notebook_id`, nombre, materia descriptiva y fuentes declaradas | `DEFAULT_NOTEBOOKS` en `src/study_engine/federation/notebook_registry.py` | Define identidades y asociaciones declaradas para bootstrap. La lista de `sources` no es por sí sola la ACL efectiva de runtime. |
| `curriculum_id` y KCs asociados | Claves exactas de `config/notebook_kc_catalog.json` | Fuente del mapeo curricular configurado. No certifica autoridad académica ni permite mapear por similitud de nombres. |
| Rol semántico de una fuente | `config/notebook_source_roles.json` | Describe `PRIMARY`, `COMPLEMENTARY`, etc.; un rol nunca concede acceso. Una fuente con rol pero sin asociación efectiva no se autoriza. |
| Asociaciones efectivas notebook-fuente | Tabla `notebook_sources` de `knowledge_store.db` | Es el límite de autorización que debe preservarse en retrieval. No se amplía uniendo automáticamente esta tabla con las otras listas. |
| Existencia e identidad de las fuentes | Tabla `sources` y manifiestos relacionados en `knowledge_store.db` | Permite detectar referencias inexistentes, hashes/manifiestos y diferencias de identidad. No se usa el contenido del vector store para resolver identidades. |
| Alias o bridge explícito | Configuración versionada de federation/bridges | Solo se acepta una equivalencia declarada y revisada. Si falta evidencia, el ID permanece como scope separado/neutral. |

#### Implementación propuesta

1. **Registrar el punto de partida sin alterarlo.** Capturar `HEAD`, rama y
   `git status` para que el trabajo local preexistente siga distinguible. No
   crear commit, stash, reset ni migración como parte de este paso.
2. **Construir un reconciliador de solo lectura** (preferentemente un comando
   de diagnóstico bajo `scripts/`) que lea los catálogos versionados y haga
   consultas explícitamente read-only a `knowledge_store.db`. No inicializar
   `AppContainer`, no abrir `vector_store.db`, no llamar a métodos de escritura
   ni ejecutar el bootstrap. El comando debe aceptar rutas de entrada para
   poder correr contra fixtures/snapshots y no asumir la base por defecto.
3. **Emitir una matriz determinista**, con una fila por notebook y campos para:
   ID y alias explícito; estado/configuración activa; nombre y materia
   descriptiva; `curriculum_id` configurado y persistido; fuentes declaradas,
   fuentes con rol y fuentes efectivamente asociadas; fuentes faltantes o
   desconocidas; asociaciones locales sin declaración; nivel de confianza/
   evidencia y decisión pendiente. Ordenar IDs y fuentes para que el resultado
   sea estable y revisable en diff.
4. **Clasificar discrepancias sin repararlas.** Como mínimo: ID presente solo
   en una autoridad; `curriculum_id` ausente o discordante; alias ambiguo;
   fuente declarada pero inexistente; rol sin asociación; asociación sin rol;
   asociación local no declarada; notebook activo sin fuentes; y fuente
   compartida entre scopes. Las coincidencias entre `sources`, roles y ACL se
   informan como conjuntos separados; no se toma su unión como permiso.
5. **Resolver explícitamente los casos conocidos con evidencia**, aplicando
   estos defaults seguros mientras no haya decisión documentada:
   - `fase0-soc` mantiene su identidad Roadmap exacta; una fuente FADENA solo
     se considera compartida si existe una asociación explícita.
   - `fadena-sye` no se habilita como perfil/scope operativo hasta confirmar
     fuentes y autoridad curricular.
   - `fadena-prog`, `fadena-so` y `NB-CYBERSECURITY-V1` se conservan separados;
     no se convierten en aliases por nombre o contenido.
   - Notebooks custom sin mapeo siguen válidos como scopes registrados, pero
     neutrales y sin `curriculum_id` inferido.
   - El `fadena_v1` persistido se reporta como discrepancia heredada; el
     catálogo exacto puede orientar el mapeo deseado, pero la reconciliación
     no actualiza SQLite. Cualquier reparación de datos será una operación
     posterior separada, respaldada, revisada y aprobada.
6. **Revisar antes de aplicar.** La salida del diagnóstico será propuesta,
   no una migración. Tras revisar la matriz, registrar decisiones explícitas
   para aliases, estado activo, currículo y fuentes permitidas. Solo cambios
   declarativos aprobados se incorporarán a configuración versionada. No
   insertar ni borrar `notebook_sources` automáticamente desde el reconciliador.

#### Pruebas y condición de salida del paso 1

- Unit tests con fixtures pequeños para cada discrepancia, IDs parecidos,
  aliases explícitos/ambiguos, catálogos incompletos, fuente inexistente,
  fuente compartida y diferencias entre declaración, rol y ACL.
- Verificar que el diagnóstico no escribe: comparar bytes/mtime de los
  fixtures SQLite antes/después y probar conexiones read-only; si una ruta de
  entrada no existe o un catálogo está mal formado, reportar error explícito
  y terminar con estado no-cero, nunca generar un informe de éxito parcial.
- Ejecutar primero sobre fixtures; después, solo sobre una copia/snapshot
  aislado de la base de conocimiento. No arrancar la aplicación ni tocar el
  vector store para producir esta matriz.
- Cerrar el paso cuando cada notebook esté clasificado como canónico,
  alias explícito, legacy independiente o custom; cada discrepancia tenga una
  decisión/evidencia o quede visible como bloqueo; ninguna fuente haya ganado
  autorización implícita; y el estado de las bases originales permanezca
  intacto.

**Fuera de este paso:** migrar `curriculum_id`, cambiar asociaciones en la
base activa, deduplicar embeddings, habilitar `fadena-sye`, inventar mappings
de alias, crear una UI administrativa o refactorizar federation/retrieval en
general. Esas acciones requieren decisiones y pruebas propias; el resultado
del paso 1 será el insumo controlado para las fases posteriores.

#### Ejecución inicial del paso 1 — diagnóstico, 2026-09-28

Se implementó el diagnóstico reproducible de solo lectura:
[`scripts/reconcile_gate2_notebooks.py`](../scripts/reconcile_gate2_notebooks.py),
con lógica testeable en
[`notebook_reconciliation.py`](../src/study_engine/diagnostics/notebook_reconciliation.py).
Las decisiones revisadas de identidad se guardan en
[`notebook_identity_decisions.json`](../config/notebook_identity_decisions.json)
como metadatos de auditoría; no participan en autorización, búsqueda ni
bootstrap.
El comando importa únicamente las declaraciones estáticas del registry; no
arranca la aplicación ni el bootstrap. Abre SQLite con `mode=ro` y
`query_only=ON`, y ofrece salida `summary` o JSON completo. Acepta rutas
explícitas para catálogos y base:

```bash
.venv/bin/python scripts/reconcile_gate2_notebooks.py \
  --knowledge-db /ruta/a/knowledge_store_snapshot.db --format json
```

La corrida se hizo contra un snapshot temporal creado con la API de backup
SQLite desde una conexión de solo lectura. Se verificó que el tamaño y
`mtime_ns` de `knowledge_store.db` original fueran iguales antes y después;
el snapshot se eliminó al terminar. No se abrió `vector_store.db` ni se
ejecutaron escrituras, migraciones o bootstrap.

**Conteo observado:** registry 8 notebooks; catálogo curricular 6; catálogo
de roles 5; base local 12 notebooks, 76 fuentes y 151 asociaciones
notebook-fuente. El diagnóstico emitió 12 filas y encontró discrepancias en
las 12; esto es un inventario para revisión, no significa que toda diferencia
sea automáticamente un permiso incorrecto o que deba corregirse borrando
asociaciones.

#### Decisiones de identidad y tratamiento de discrepancias

La comparación de las tres fuentes versionadas permite decidir identidades,
pero no autoriza por sí sola a cambiar permisos ni a certificar programas
académicos. Se adopta esta clasificación de trabajo:

| ID | Decisión de identidad | Decisión operativa de Gate 2 |
|---|---|---|
| `fase0-soc` | Notebook canónico Roadmap/Fase 0; no alias FADENA. | Mantener `roadmap_kasiu_v4_fase0` como ID curricular deseado por catálogo exacto. No alterar SQLite ni sus fuentes; cada asociación cruzada Roadmap debe conservarse solo como ACL explícita y cotejarse contra la evidencia curricular. |
| `fadena-lenguajes` | Notebook canónico Lenguajes FADENA 2026. | ID deseado `fadena_lenguajes_2026`. Cinco de las siete asociaciones locales sin declaración son archivos dentro del directorio del curso y ahora tienen rol explícito; quedan sin rol `src_fadena_prog_arboles` y `src_fadena_prog_archivos`, cuyo origen/carpeta no se confirmó. |
| `fadena-so2` | Notebook canónico Sistemas Operativos II FADENA 2026, distinto del legacy `fadena-so`. | ID deseado `fadena_so2_2026`. Cinco de las seis asociaciones locales extra son unidades/actividades 2026 del curso y recibieron rol; Stallings 5.ª permanece sin rol por nota de reemplazo por 7.ª. Tres fuentes de roles marcadas faltantes no se autorizan por esa mención. |
| `fadena-std` | Notebook canónico Tratamiento de Datos FADENA 2026. | ID deseado `fadena_std_2026`. Se asignó rol a 19 de las 21 asociaciones locales extra cuyos nombres/metadatos coinciden con materiales del directorio del curso. Rosen permanece pendiente de procedencia y el PDF de soluciones SQL queda sin rol hasta validar su tratamiento de evaluación. |
| `fadena-teleco` | Notebook canónico Infraestructura de Telecomunicaciones FADENA 2025. | ID deseado `fadena_teleco_2025`. Las cuatro asociaciones extra (Unidades 2–5 2026) coinciden con los archivos del directorio del curso y recibieron rol PRIMARY. Tanenbaum de redes está marcado ausente y no tiene asociación. |
| `fadena-sye` | Entrada de catálogo curricular, pero no notebook operativo en `DEFAULT_NOTEBOOKS` ni en roles. Hay una fila SQLite local vacía, con `subject`/`curriculum_id` nulos y cero asociaciones. | Mantener fuera del registry operativo; el placeholder local no lo habilita. El ID de catálogo `fadena_sye_2026` difiere del `NULL` persistido, pero no migrarlo ni asignarle fuentes hasta validar identidad académica y bibliografía primaria. |
| `fadena-prog` | Scope legacy independiente, no alias demostrado de `fadena-lenguajes` ni de Fase 0. | Conservar el ID para compatibilidad, sin redirigirlo. Sus cuatro `source_id` declarados no existen localmente y no hay ACL; no aceptar nuevas asociaciones por inferencia. La etiqueta “Legacy Alias” es descriptiva heredada, no un mapping. |
| `fadena-so` | Scope legacy independiente, no alias demostrado de `fadena-so2`. | Igual que `fadena-prog`: preservar ID, sin redirección; fuentes declaradas ausentes y cero asociaciones locales. |
| `NB-CYBERSECURITY-V1` | Scope independiente de Seguridad, no alias FADENA. | Mantener currículo sin mapear. Sus 10 ACL locales se preservan sin ampliarlas; faltan catálogo de roles y cotejo de que las siete asociaciones no declaradas correspondan a su objetivo. |
| `NB-SEC-01-C-PTR` | Scope canónico de tema dentro de `ROADMAP-CYBERSECURITY-V1`, node `SEC-01-C-PTR` (punteros, aritmética y modelo de memoria en C), confirmado por el roadmap versionado y el golden set. No equivale al notebook general `NB-CYBERSECURITY-V1`. | Mantener la identidad exacta y reconocerlo en el benchmark. No inferir un `curriculum_id` de curso: el roadmap no lo provee. Sus 42 asociaciones son demasiado amplias para el nodo descrito y una apunta a un `source_id` huérfano; queda bloqueado para certificar aislamiento hasta revisión de ACL, sin borrarlas en este paso. |
| `nb_prog_1`, `nb_prog_basica` | Dos filas locales custom sin identidad curricular, fuentes o registry asociado. | Preservar sin borrado; tratarlas como scopes locales no habilitados para decisiones curriculares hasta encontrar procedencia. |

Los cinco `curriculum_id` específicos del catálogo son la decisión de mapeo
de configuración para los cinco notebooks canónicos. En SQLite, los cinco
persistidos continúan con `fadena_v1`; eso es una **migración pendiente**, no
una razón para cambiar la autoridad al valor genérico ni permiso para
reescribir las filas. Además, `fadena-sye` tiene un placeholder local con
`curriculum_id=NULL`, que también difiere del catálogo pero no es una
identidad operativa aprobada.

**Decisión de fuentes:** `notebook_sources` se mantiene como la única ACL
efectiva. La lista de `DEFAULT_NOTEBOOKS.sources` describe las fuentes de
bootstrap declaradas; `notebook_source_roles.json` describe función
pedagógica, no permisos. La estructura del repo también ubica materiales bajo
`fuentes/fadena-lenguajes`,
`fuentes/fadena-so2`, `fuentes/fadena-std` y `fuentes/fadena-teleco`. Eso
corrobora procedencia local de varios documentos de curso, pero no prueba por
sí solo su rol académico ni autoriza una asociación nueva. Por tanto:

- asociaciones que ya existen siguen siendo las únicas asociaciones
  autorizantes; no se quitan ni agregan automáticamente;
- para 33 asociaciones ya autorizadas con fuente/archivo de curso coincidente
  (5 Lenguajes, 5 SO II, 19 Tratamiento de Datos, 4 Telecomunicaciones), se
  añadieron roles basados en tipo de documento: clases/unidades `PRIMARY`,
  ejercicios `IMPLEMENTATION`, manual de C `REFERENCE` y material
  complementario identificado como tal. El informe confirmó que los 33 IDs ya
  estaban asociados en `notebook_sources`; esto no añadió ACLs. Sí cambia qué
  evidencia etiquetada por rol puede participar en el ensamblador pedagógico,
  por lo que sus pruebas focalizadas se incluyen en la validación.
- se dejó sin rol `src_fadena_prog_arboles`, `src_fadena_prog_archivos` y
  `src_rosen_matematicas_discretas` para esos scopes donde no hay procedencia
  de carpeta específica suficiente; `src_0bc5d20dcc91895f` (Stallings 5.ª)
  sigue sin rol porque la configuración declara que fue reemplazado por la
  7.ª edición; `src_f3352475bc0cd360` (soluciones SQL) queda sin rol a la
  espera de confirmar su tratamiento respecto de evaluaciones; no se borraron
  sus asociaciones existentes.
- referencias de roles ausentes del almacén (incluidas las marcadas
  `SOURCE_MISSING`) no conceden acceso;
- los 18 vínculos cruzados observados en `fase0-soc` hacia materiales FADENA,
  SO, redes y datos se preservan porque están explícitos en su ACL; su
  pertinencia al Roadmap debe validarse en benchmark y no se replica a otros
  scopes;
- `fadena-prog`/`fadena-so` no reciben asociaciones de `fadena-lenguajes`/
  `fadena-so2` por similitud de contenido.

Se observó un defecto en los metadatos: 41 de 76 registros `sources` tienen
`subject="Cybersecurity"` aunque los títulos/catálogos los asocian a Lenguajes,
SO II, Tratamiento de Datos, Telecomunicaciones y bibliografía general; los 76
registros tienen `course=NULL`. Por eso `sources.subject/course` no son
autoridad suficiente para reconciliar fuentes. Esta inconsistencia ayuda a
explicar por qué los campos del notebook `NB-SEC-01-C-PTR` no se deben usar
para reclasificar automáticamente las fuentes globales. El roadmap exacto sí
confirma la identidad del notebook de tema, pero la ACL amplia necesita una
decisión de acceso separada.

Se examinó localmente la portada/inicio de
[`fuentes/fadena-std/UNIDAD1STD.pdf`](../fuentes/fadena-std/UNIDAD1STD.pdf):
identifica “Licenciatura en Ciberdefensa”, “Sistemas de Tratamientos de
Datos”, “Año 2026” y desarrolla la Unidad 1 sobre dato, información y
conocimiento. Esto respalda la identidad/nombre del curso y la fuente primaria
de Unidad 1; no es el programa completo, así que no certifica la cantidad de
módulos ni la bibliografía oficial del ciclo. No se extrapola un plan de
estudios a partir de este documento.

#### Revalidación de inventario local — 2026-09-29, solo lectura

Se volvió a inspeccionar `data/web_state/knowledge_store.db` mediante SQLite
`mode=ro` y `PRAGMA query_only=ON`, comparando identidades persistidas con
`notebook_kc_catalog.json` y `notebook_source_roles.json`. La consulta no abrió
`vector_store.db` ni ejecutó bootstrap, migraciones o escrituras.

La CLI `scripts/reconcile_gate2_notebooks.py` no pudo ejecutarse en el entorno
actual porque el `.venv` no tiene `pydantic`. Para no instalar dependencias ni
cambiar el entorno, se hizo un resumen acotado con la biblioteca estándar de
Python y se cotejó el registry estático. Por eso esta comprobación confirma los
conteos y discrepancias de base/catálogo/roles que se listan aquí, pero no
sustituye una nueva salida completa del reconciliador oficial.

| ID persistido | Hecho observado: `curriculum_id` DB / catálogo | Hecho observado: asociaciones / sin rol | Decisión requerida | Propuesta preliminar no autorizada |
|---|---|---:|---|---|
| `NB-CYBERSECURITY-V1` | `fadena_v1` / — | 10 / 10 | Determinar si requiere identidad curricular y roles propios. | Tratarlo como scope independiente; no derivar una migración del valor genérico. |
| `NB-SEC-01-C-PTR` | `NULL` / — | 42 / 42 | Resolver el alcance funcional y el bloqueo de BENCH-G2 antes de decidir cualquier ACL. | Mantener sin cambios mientras se resuelve el bloqueo; no es aprobación de las 42 ACL. |
| `fadena-lenguajes` | `fadena_v1` / `fadena_lenguajes_2026` | 17 / 2 | Aprobar si el ID del catálogo debe migrarse a los registros locales. | Considerar el ID específico del catálogo como candidato; migración no aprobada. |
| `fadena-prog` | `fadena_v1` / — | 0 / 0 | Confirmar el tratamiento del scope legacy y el valor genérico persistido. | No inferir alias ni asociaciones por similitud. |
| `fadena-so` | `fadena_v1` / — | 0 / 0 | Confirmar el tratamiento del scope legacy y el valor genérico persistido. | No inferir alias a `fadena-so2` ni asociaciones. |
| `fadena-so2` | `fadena_v1` / `fadena_so2_2026` | 14 / 1 | Aprobar si el ID del catálogo debe migrarse y resolver la fuente sin rol. | Considerar el ID específico del catálogo como candidato; migración no aprobada. |
| `fadena-std` | `fadena_v1` / `fadena_std_2026` | 30 / 2 | Aprobar si el ID del catálogo debe migrarse y resolver las dos fuentes sin rol. | Considerar el ID específico del catálogo como candidato; migración no aprobada. |
| `fadena-sye` | `NULL` / `fadena_sye_2026` | 0 / 0 | Validar identidad/programa y decidir si corresponde habilitarlo. | Mantener la clasificación de placeholder no operativo; no activarlo en esta etapa. |
| `fadena-teleco` | `fadena_v1` / `fadena_teleco_2025` | 12 / 0 | Aprobar si el ID del catálogo debe migrarse a los registros locales. | Considerar el ID específico del catálogo como candidato; migración no aprobada. |
| `fase0-soc` | `fadena_v1` / `roadmap_kasiu_v4_fase0` | 26 / 18 | Decidir qué evidencia justifica cada asociación sin rol y si el ID local debe migrarse. | Mantener el ID de Roadmap como candidato; revisar ACL individualmente, sin autorizar poda. |
| `nb_prog_1` | `NULL` / — | 0 / 0 | Buscar procedencia y decidir si tiene una identidad curricular válida. | Mantener sin mapeo ni fuentes; no inferirlo desde el nombre de carpeta. |
| `nb_prog_basica` | `NULL` / — | 0 / 0 | Buscar procedencia y decidir si tiene una identidad curricular válida. | Mantener sin mapeo ni fuentes; no inferirlo desde el nombre de carpeta. |

Las columnas de “hecho observado” son resultados de lectura; “decisión
requerida” enumera preguntas aún no resueltas; la última columna solo registra
una propuesta preliminar para orientar esa revisión. **Ninguna propuesta de
esta tabla está aprobada**, constituye autoridad curricular, autoriza ACL ni
ordena una migración o modificación de datos.

Conteos revalidados: **12 notebooks**, **76 sources** y **151 asociaciones**
persistidas; **45 source IDs** están asociados a más de un notebook. Los cinco
IDs curriculares específicos de cursos/Roadmap difieren de `fadena_v1` en DB;
`fadena-sye` difiere entre `NULL` y su catálogo, y `NB-CYBERSECURITY-V1`
conserva `fadena_v1` sin una entrada curricular coincidente. Hay **un
source_id huérfano**, dentro de las 42 asociaciones de `NB-SEC-01-C-PTR`.
Los 18 vínculos de `fase0-soc` sin rol y las asociaciones sin rol de otros
scopes siguen siendo asociaciones ya persistidas: la falta de rol no autoriza
a borrarlas ni la presencia de un rol autoriza a crear ACL.

Para `fadena-lenguajes`, las dos asociaciones sin rol son
`src_fadena_prog_arboles` y `src_fadena_prog_archivos`; para `fadena-so2` es
`src_0bc5d20dcc91895f`; para `fadena-std` son `src_f3352475bc0cd360` y
`src_rosen_matematicas_discretas`. Se mantienen pendientes de procedencia,
vigencia o tratamiento curricular según la revisión anterior. Los catálogos de
roles también contienen referencias sin fila de fuente local: **3** para
`fadena-so2`, **1** para `fadena-std` y **1** para `fadena-teleco`; esas
referencias no crean autorización.

**Dictamen de esta revalidación:** inventario local confirmado; no hay base
para una reconciliación automática de `curriculum_id`, para ampliar o podar
ACL, ni para activar scopes locales. El siguiente paso es aprobar por separado
la identidad curricular deseada y el tratamiento de cada grupo de fuentes. En
particular, el narrowing de `NB-SEC-01-C-PTR` sigue bloqueado por la
inconsistencia de scope/qrels de BENCH-G2 descrita abajo. Gate 2 continúa
**PARCIAL** y esta inspección no certifica corpus, programa oficial ni
aislamiento productivo de ningún scope.

#### Matriz de decisiones de identidad — 2026-09-29, solo lectura

Esta matriz separa la identidad del scope de la decisión de modificar
`curriculum_id` persistido. Los estados son un **dictamen técnico para revisión
del usuario**, no una aprobación del usuario ni una autorización operativa:
`APPROVED` indica evidencia explícita suficiente para describir la identidad
del scope; `PENDING` indica que falta evidencia/decisión de autoridad;
`BLOCKED` indica que una operación concreta no debe avanzar mientras subsista
el bloqueo indicado. Una identidad aprobada no implica que deba tener un
`curriculum_id`, ni que un valor persistido deba migrarse.

| Scope | Autoridad y evidencia explícita | Persistido → identidad curricular declarada | Identidad (dictamen técnico) | Decisión de persistencia/mapeo |
|---|---|---|---|---|
| `fase0-soc` | Registry exacto + clave e ID de `notebook_kc_catalog.json`; catálogo define `roadmap_kasiu_v4_fase0`. | `fadena_v1` → `roadmap_kasiu_v4_fase0` | **APPROVED** como notebook exacto de Roadmap/Fase 0; no alias FADENA. | **PENDING**: decidir una migración local del valor genérico; no modificarlo en este paso. |
| `fadena-lenguajes` | Registry exacto + catálogo curricular con ID `fadena_lenguajes_2026`. | `fadena_v1` → `fadena_lenguajes_2026` | **APPROVED** como curso FADENA Lenguajes 2026. | **PENDING**: el ID del catálogo es la identidad declarada; migrar SQLite requiere autorización y plan aparte. |
| `fadena-so2` | Registry exacto + catálogo curricular con ID `fadena_so2_2026`; documentación distingue `fadena-so` legacy. | `fadena_v1` → `fadena_so2_2026` | **APPROVED** como curso FADENA SO II 2026, distinto de `fadena-so`. | **PENDING**: el ID del catálogo es la identidad declarada; migrar SQLite requiere autorización y plan aparte. |
| `fadena-std` | Registry exacto + catálogo curricular con ID `fadena_std_2026`; PDF local identifica curso/año, pero no acredita programa completo. | `fadena_v1` → `fadena_std_2026` | **APPROVED** como curso FADENA Sistema de Tratamiento de Datos 2026; el programa oficial completo sigue sin validar. | **PENDING**: no migrar hasta decisión y plan explícitos. |
| `fadena-teleco` | Registry exacto + catálogo curricular con ID `fadena_teleco_2025`. | `fadena_v1` → `fadena_teleco_2025` | **APPROVED** como curso FADENA Telecomunicaciones 2025. | **PENDING**: el ID del catálogo es la identidad declarada; migrar SQLite requiere autorización y plan aparte. |
| `fadena-prog` | Registry exacto con etiqueta heredada “Legacy Alias”; no hay entrada curricular ni `alias_target`, y decisiones audit-only lo conservan como scope de compatibilidad independiente. | `fadena_v1` → sin ID curricular declarado | **APPROVED** como identidad legacy distinta; no está aprobada equivalencia con `fadena-lenguajes` o Fase 0. | **PENDING**: `fadena_v1` no tiene respaldo como mapping curricular para este scope; no inferir sustituto ni migrar a otro ID. |
| `fadena-so` | Registry exacto con etiqueta heredada “Legacy Alias”; no hay entrada curricular ni `alias_target`; decisiones audit-only y referencias de federation lo mantienen distinto de `fadena-so2`. | `fadena_v1` → sin ID curricular declarado | **APPROVED** como identidad legacy distinta; no es alias de `fadena-so2`. | **PENDING**: `fadena_v1` no tiene respaldo como mapping curricular para este scope; no inferir sustituto ni migrar a otro ID. |
| `NB-CYBERSECURITY-V1` | Registry exacto, nombre/subject de Seguridad y decisión audit-only; no hay clave curricular correspondiente. | `fadena_v1` → sin ID curricular declarado | **APPROVED** como notebook independiente de Seguridad, no FADENA. | **PENDING**: decidir si necesita un curriculum formal; no asignarlo por inferencia desde `fadena_v1`. |
| `NB-SEC-01-C-PTR` | Roadmap `ROADMAP-CYBERSECURITY-V1` asigna este ID exacto al nodo `SEC-01-C-PTR`; identidad corroborada en decisiones audit-only. | `NULL` → scope de nodo sin `curriculum_id` en catálogo KC | **APPROVED** como scope exacto del nodo punteros/memoria; no es el notebook general de Seguridad. | **PENDING** para cualquier mapping curricular de DB. **BLOCKED** solo el cambio de alcance/ACL hasta resolver BENCH-G2; la identidad del nodo no aprueba las 42 asociaciones. |
| `fadena-sye` | Entrada exacta de catálogo KC con ID `fadena_sye_2026`; falta en registry operativo y catálogo de roles; la fila DB es placeholder vacío. | `NULL` → `fadena_sye_2026` | **PENDING**: la entrada del catálogo no demuestra identidad académica operativa ni programa validado. | **BLOCKED** activar el scope; mapping/migración también pendientes hasta validar identidad, fuentes y autoridad académica. |
| `nb_prog_1` | Solo fila local y nombre de carpeta `f_prog`; no hay registry, catálogo curricular ni evidencia que demuestre equivalencia. | `NULL` → sin mapping declarado | **PENDING / UNRESOLVED**. | **PENDING**: no asignar `curriculum_id` ni inferir alias sin procedencia explícita. |
| `nb_prog_basica` | Solo fila local y nombre de carpeta `folder_fase0`; no hay registry, catálogo curricular ni evidencia que demuestre equivalencia. | `NULL` → sin mapping declarado | **PENDING / UNRESOLVED**. | **PENDING**: no asignar `curriculum_id` ni inferir alias sin procedencia explícita. |

**Resultado de clasificación técnica de identidad (12 scopes):** **9
APPROVED**, **3 PENDING**, **0 BLOCKED como identidad semántica**. Los tres
pendientes son `fadena-sye`, `nb_prog_1` y `nb_prog_basica`; la limitación de
`fadena-sye` bloquea su activación, no permite concluir que su identidad
académica ya esté establecida. Hay bloqueos operativos independientes:
cambios ACL/alcance de `NB-SEC-01-C-PTR` por BENCH-G2 y activación de
`fadena-sye` por falta de validación. Esta clasificación técnica queda para
revisión/aprobación explícita del usuario; no equivale a que el usuario haya
aprobado los nueve dictámenes.

**Persistencia en `knowledge_store.db`:** **0 cambios autorizados, 12
pendientes**. Esto incluye los cinco IDs de catálogo ya documentados, los
scopes legacy con `fadena_v1`, `NB-CYBERSECURITY-V1` con `fadena_v1`,
`NB-SEC-01-C-PTR` con `NULL`, el placeholder `fadena-sye` con `NULL` y los dos
scopes custom con `NULL`. La matriz no prescribe una migración masiva ni
asume que cada identidad necesita un `curriculum_id`.

**Impacto runtime verificado en código:**

- `config/notebook_kc_catalog.json` carga el mapping en
  `web/dependencies.py::_load_notebook_curriculum_ids`. El seed
  `_seed_curriculum_tree` aplica ese ID al crear una fila nueva; para filas
  existentes **no actualiza** `curriculum_id` y solo intenta insertar fuentes
  declaradas con `INSERT OR IGNORE`. Reiniciar o volver a ejecutar el seed no
  reconcilia los valores persistidos.
- Los perfiles de `pedagogy/fase0_seed.py` requieren coincidencia exacta entre
  `notebook_id` y `curriculum_id`; si no coincide, producen el prompt base
  neutral. Las rutas de roadmap y pedagogía y el orquestador de sesiones leen
  el mapping desde el catálogo KC; las sesiones guardan ese valor (o
  `curr_<notebook_id>` si no hay entrada).
- **Hay un consumidor runtime directo del valor persistido:** cuando no existe
  un contrato pedagógico custom, `web/routes/chat.py` llama
  `KnowledgeStore.get_pedagogical_contract`; este lee el notebook persistido y
  pasa su `curriculum_id` a `get_default_contract`. Por tanto, un valor local
  genérico como `fadena_v1` no coincide con los perfiles exactos y produce el
  contrato/prompt neutral en ese camino. Un contrato custom persistido evita
  ese fallback. En la DB inspeccionada hay **0 filas en
  `pedagogical_contracts`**, por lo que el camino de fallback está activo para
  los notebooks consultados en este almacén local. Esta dependencia hace que
  una eventual migración pueda cambiar comportamiento de prompts, aunque no
  conceda ACL.
- `KnowledgeStore.get_notebook` lee el campo persistido y
  `create_notebook` lo compara al detectar conflictos e inserta el valor al
  crear filas nuevas. En el código inspeccionado no se encontraron otros
  consumidores de runtime que usen el `curriculum_id` leído de DB; los demás
  perfiles, rutas y sesiones usan el catálogo KC. La búsqueda cubrió los usos
  en `src/study_engine`, no constituye una afirmación sobre consumidores
  externos al repositorio.
- Modificar únicamente `notebooks.curriculum_id` no cambia
  `notebook_sources`, fuentes, roles, chunks, Golden Sets ni qrels. Sí puede
  cambiar el contrato pedagógico de fallback de chat. Por eso, antes de
  cualquier futura escritura se debe comprobar qué notebooks tienen contrato
  custom y validar explícitamente el comportamiento anterior/posterior del
  fallback, además de snapshot/hash, rollback y prueba E2E.

La conclusión de impacto corrige una simplificación importante del inventario
anterior: la DB no es solo metadato sin efecto. El catálogo controla los
perfiles/rutas/sesiones, mientras el valor persistido alimenta el contrato de
fallback de chat. La necesidad y alcance de alinear ambos valores, la
compatibilidad con contratos custom y el tratamiento de sesiones existentes
requieren decisión explícita. No se prepara ni ejecuta aquí transformación,
snapshot, rollback o prueba E2E de migración.

**Impacto por grupo de identidad en el estado observado:**

| Scope(s) | Fuente para perfil/ruta/sesión | Valor persistido observado | Efecto del fallback de chat |
|---|---|---|---|
| `fase0-soc`, `fadena-lenguajes`, `fadena-so2`, `fadena-std`, `fadena-teleco` | Entrada exacta en catálogo KC; perfiles requieren su ID exacto. | `fadena_v1` | No coincide con el perfil específico; con 0 contratos custom, `get_default_contract` devuelve prompt neutral. |
| `fadena-prog`, `fadena-so`, `NB-CYBERSECURITY-V1` | Registry; sin entrada KC/perfil exacto para estos IDs. | `fadena_v1` | No hay perfil exacto que activar; fallback neutral. |
| `NB-SEC-01-C-PTR` | Roadmap de tema; sin entrada KC ni perfil de notebook exacto. | `NULL` | No hay perfil exacto; fallback neutral. El bloqueo BENCH-G2 refiere a alcance/ACL, no a este resultado de identidad. |
| `fadena-sye` | Entrada KC, pero no registry operativo. | `NULL` | No hay perfil registrado para este notebook en `NOTEBOOK_PROFILES`; el catálogo por sí solo no lo activa. |
| `nb_prog_1`, `nb_prog_basica` | Solo filas locales; sin entrada KC ni perfil exacto. | `NULL` | No hay perfil exacto; cualquier ruta que obtenga contrato cae al neutral. |

#### Matriz de impacto hipotético de persistencia — no autorizada

La columna “valor hipotético” modela únicamente el efecto de cambiar el campo
`notebooks.curriculum_id`; no es una instrucción ni una propuesta aprobada de
`UPDATE`. Para filas sin identidad curricular respaldada, el valor correcto
del análisis es “sin cambio decidido”, no inventar un ID. El riesgo describe
el cambio observable en el fallback de contrato de chat; no evalúa aquí otras
integraciones externas.

| Scope | Actual → hipotético | Consumidor y evidencia | Comportamiento actual → hipotético | Riesgo del cambio aislado |
|---|---|---|---|---|
| `fase0-soc` | `fadena_v1` → `roadmap_kasiu_v4_fase0` | `chat.py` → `get_pedagogical_contract` → `get_default_contract`; perfil exacto en `fase0_seed.py`; catálogo KC y prueba de perfiles. | Prompt neutral → perfil Fase 0 validado, con orientación opcional de traza/pseudocódigo cuando corresponda. | **Medio**: habilita guía de perfil antes ausente; no cambia ACL. |
| `fadena-lenguajes` | `fadena_v1` → `fadena_lenguajes_2026` | Mismo fallback; perfil exacto Lenguajes; `get_default_contract` también cambia `forbidden_patterns` a `#include <stdio.h>` y `int main(` cuando el perfil se activa. | Prompt neutral → perfil de Lenguajes; además cambia las restricciones de código del contrato default. | **Alto**: cambia perfil y restricciones del contrato; requiere prueba del comportamiento del chat, no solo comprobar el valor. |
| `fadena-so2` | `fadena_v1` → `fadena_so2_2026` | Mismo fallback; perfil exacto SO II y test de correspondencia con catálogo. | Prompt neutral → orientación opcional de sistemas, estados e intercalaciones, sin presuponer plataforma. | **Medio**: cambia orientación pedagógica observable; no cambia fuentes/ACL por sí solo. |
| `fadena-std` | `fadena_v1` → `fadena_std_2026` | Mismo fallback; perfil exacto Tratamiento de Datos y test de mismatch/exact match. | Prompt neutral → orientación opcional de modelos, transformaciones y consultas de datos; no fuerza SQL. | **Medio**: cambia perfil pedagógico observable; el programa oficial completo sigue sin validarse. |
| `fadena-teleco` | `fadena_v1` → `fadena_teleco_2025` | Mismo fallback; perfil exacto Telecomunicaciones y test de catálogo. | Prompt neutral → orientación opcional sobre señales, capas, protocolos y temporización. | **Medio**: cambia perfil pedagógico observable; no cambia fuentes/ACL por sí solo. |
| `fadena-prog` | `fadena_v1` → sin cambio decidido | Se consulta el valor persistido, pero no hay perfil exacto en `NOTEBOOK_PROFILES` ni ID curricular de catálogo. | Neutral → neutral para el fallback inspeccionado. | **Bajo para este consumidor**, pero no existe un valor alternativo autorizado; no inferir equivalencia por etiqueta legacy. |
| `fadena-so` | `fadena_v1` → sin cambio decidido | Se consulta el valor persistido, pero no hay perfil exacto ni ID curricular de catálogo. | Neutral → neutral para el fallback inspeccionado. | **Bajo para este consumidor**, sin evidencia que autorice un mapping; no mapear a `fadena-so2`. |
| `NB-CYBERSECURITY-V1` | `fadena_v1` → sin cambio decidido | Registry exacto; no hay perfil KC de notebook ni perfil exacto en `NOTEBOOK_PROFILES`. | Neutral → neutral para el fallback inspeccionado. | **Bajo para este consumidor**; inventar un ID podría habilitar otro comportamiento si se añade perfil en el futuro, pero no hay tal cambio contemplado. |
| `NB-SEC-01-C-PTR` | `NULL` → sin cambio decidido | Identidad de nodo proviene del roadmap; no hay perfil KC exacto ni perfil en `NOTEBOOK_PROFILES`. | Neutral → neutral para este fallback. | **Bajo para el campo aislado**; el bloqueo BENCH-G2 sigue aplicando a ACL/alcance y no se resuelve con esta operación. |
| `fadena-sye` | `NULL` → no migrar; ID catálogo `fadena_sye_2026` solo como dato declarativo | Está en catálogo KC pero no en registry operativo/profile map; los tests confirman que no está en `NOTEBOOK_PROFILES`. | Neutral → neutral mientras no se registre un perfil; asignar el ID por sí solo no activa el scope. | **Medio/indeterminado**: no activaría el perfil actual, pero podría crear una falsa apariencia de habilitación o afectar futuras integraciones; identidad/activación pendientes. |
| `nb_prog_1` | `NULL` → sin cambio decidido | No hay entrada KC ni perfil exacto. | Neutral → neutral para el fallback inspeccionado. | **Bajo para este consumidor**; no hay mapping respaldado ni valor candidato. |
| `nb_prog_basica` | `NULL` → sin cambio decidido | No hay entrada KC ni perfil exacto. | Neutral → neutral para el fallback inspeccionado. | **Bajo para este consumidor**; no hay mapping respaldado ni valor candidato. |

La clasificación de riesgo no es una aprobación: incluso los casos “bajo”
siguen sin permiso de escritura. Para los cinco scopes con perfil exacto, el
cambio potencial relevante es habilitar una especialización actualmente
neutral; en `fadena-lenguajes` también altera explícitamente las restricciones
de código del contrato. La prueba unitaria de resolución del perfil acredita
ese comportamiento determinista, pero no demuestra por sí sola la respuesta
observable de Chat ni la calidad pedagógica tras el cambio. Si en el futuro se
aprueba persistencia, validar antes/después el contrato obtenido y el prompt
capturado por Chat para cada scope afectado, además de registrar snapshot/hash,
precondiciones, rollback y postcondiciones. No realizar ese ensayo contra la
DB productiva/local compartida en esta etapa.

**Fuera de alcance de esta matriz:** fuentes/roles/ACL (requieren la matriz
separada `source → notebook → evidencia → decisión`); cambios a Golden Sets o
qrels; habilitación de `fadena-sye`; migraciones de `curriculum_id`; y
certificación de aislamiento productivo. En particular, el bloqueo BENCH-G2
aplica a cambios de alcance/ACL de `NB-SEC-01-C-PTR` y no revoca la evidencia
que identifica su nodo Roadmap. Gate 2 continúa **PARCIAL**.

#### Matriz piloto de fuentes y asociaciones de `fadena-std` — 2026-09-29, solo lectura

Se cruzaron las **30 asociaciones existentes** de `fadena-std` en
`knowledge_store.db` (SQLite `mode=ro`, `PRAGMA query_only=ON`) con las filas
`sources`, sus documentos/chunks, el catálogo de roles y los archivos del
directorio `fuentes/fadena-std`. La pertenencia física se comprobó comparando
SHA-256 del metadata de documento con los PDFs del directorio. No se consultó
ni modificó `vector_store.db`, y no se cambió ninguna ACL ni configuración.

**Hechos agregados:** las 30 asociaciones resuelven a un registro de fuente;
hay **40 documentos y 46.530 chunks** asociados, incluyendo documentos
duplicados/reingestas para algunas fuentes. **27 source IDs** tienen al menos
un documento cuyo SHA-256 coincide con un archivo de `fuentes/fadena-std`.
De esos, 26 tienen rol declarado y uno (`src_f3352475bc0cd360`) no. Dos
asociaciones más sí tienen rol declarado pero no se halló archivo con hash
coincidente en ese directorio (`src_fadena_prog_archivos`,
`src_ramalho_fluent_python`). La segunda asociación sin rol,
`src_rosen_matematicas_discretas`, tampoco coincide con ese directorio y hoy
tiene **0 chunks**. Todos los 30 registros tienen `sources.course=NULL` y
`sources.role=PRIMARY`; ese campo `role` es global a la fuente y **no** el rol
pedagógico por notebook. Diez filas tienen además `sources.subject=Cybersecurity`,
aunque los títulos/archivos corresponden a materias de datos. Esos metadatos
globales no se trataron como prueba de autoridad ni de pertenencia.

| Source ID asociado | Fuente (título corto) | Rol declarado para `fadena-std` | Evidencia local observada | Chunks | Estado de evidencia (no decisión ACL) |
|---|---|---|---|---:|---|
| `src_032c52bff94a0743` | Ejercicios de recursividad | `IMPLEMENTATION` | SHA exacto en `fuentes/fadena-std`; `subject=fadena-std` | 4 | **A — candidato respaldado**; decisión formal pendiente. |
| `src_0960283d5cef8dee` | Álgebra relacional — presentación | `PRIMARY` | SHA exacto en el directorio; `subject=fadena-std` | 19 | **A — candidato respaldado**; decisión formal pendiente. |
| `src_3102eb1e89e2229e` | Ejercicios de estructuras de datos | `IMPLEMENTATION` | SHA exacto en el directorio; `subject=fadena-std` | 8 | **A — candidato respaldado**; confirmar relación con unidades/objetivos oficiales. |
| `src_3e2e8abda5f55c17` | Fundamentos del modelo relacional | `PRIMARY` | SHA exacto en el directorio; `subject=fadena-std` | 20 | **A — candidato respaldado**; decisión formal pendiente. |
| `src_52ff5ff3e07c1da5` | Ejercicios de álgebra relacional | `IMPLEMENTATION` | SHA exacto en el directorio; `subject=fadena-std` | 6 | **A — candidato respaldado**; decisión formal pendiente. |
| `src_53ef2a7243ae3f63` | Álgebra relacional y cálculo relacional | `PRIMARY` | SHA exacto en el directorio; `subject=fadena-std` | 23 | **A — candidato respaldado**; decisión formal pendiente. |
| `src_56cfdbe35123c49e` | SQL — alternativas para entorno interactivo | `IMPLEMENTATION` | SHA exacto en el directorio; `subject=fadena-std` | 11 | **A — candidato respaldado**; revisar que alternativas sean material de práctica vigente. |
| `src_6dbdc8e943261fa7` | Ejercicios de normalización | `IMPLEMENTATION` | SHA exacto en el directorio; `subject=fadena-std` | 8 | **A — candidato respaldado**; decisión formal pendiente. |
| `src_755be6c147ddc5dd` | SQL básico — presentación | `PRIMARY` | SHA exacto en el directorio; `subject=fadena-std` | 27 | **A — candidato respaldado**; decisión formal pendiente. |
| `src_7822bc3cef85c783` | Diseño de bases de datos relacionales | `PRIMARY` | SHA exacto en el directorio; `subject=fadena-std` | 22 | **A — candidato respaldado**; decisión formal pendiente. |
| `src_7ec00a3365f208e6` | Ejercicios de SQL básico | `IMPLEMENTATION` | SHA exacto en el directorio; `subject=fadena-std` | 7 | **A — candidato respaldado**; decisión formal pendiente. |
| `src_9946be0e7d11161a` | Normalización de bases de datos | `PRIMARY` | SHA exacto en el directorio; `subject=fadena-std` | 15 | **A — candidato respaldado**; decisión formal pendiente. |
| `src_9e866bf082e52dd7` | Ejercicios de fundamentos relacionales | `IMPLEMENTATION` | SHA exacto en el directorio; `subject=fadena-std` | 8 | **A — candidato respaldado**; decisión formal pendiente. |
| `src_a01b9809f37fb47b` | Ejercicios de diseño de bases de datos | `IMPLEMENTATION` | SHA exacto en el directorio; `subject=fadena-std` | 11 | **A — candidato respaldado**; decisión formal pendiente. |
| `src_cf46d8f0e018b09e` | Diseño de bases de datos — presentación | `PRIMARY` | SHA exacto en el directorio; `subject=fadena-std` | 19 | **A — candidato respaldado**; decisión formal pendiente. |
| `src_coronel_database_systems_11ed` | Coronel & Morris, Database Systems | `PRIMARY` | SHA exacto de libro en el directorio; DB `subject=Cybersecurity`, no `fadena-std` | 5.462 | **A — candidato respaldado por presencia local**; confirmar que la bibliografía oficial lo autoriza como `PRIMARY`. |
| `src_d7ff8399759d387a` | Estructuras de datos | `COMPLEMENTARY` | SHA exacto en el directorio; `subject=fadena-std` | 36 | **A — candidato respaldado**; rol complementario declarado. |
| `src_d946d1a5a3c32144` | Fundamentos del modelo relacional — presentación | `PRIMARY` | SHA exacto en el directorio; `subject=fadena-std` | 16 | **A — candidato respaldado**; decisión formal pendiente. |
| `src_date_intro_sistemas_bd_7ed` | Date, Introducción a sistemas de BD | `FORMAL` | SHA exacto de libro en el directorio; DB `subject=Cybersecurity`, no `fadena-std` | 7.888 | **A — candidato respaldado por presencia local**; verificar edición/alcance y bibliografía oficial. |
| `src_de275591245abbd3` | Normalización — presentación | `PRIMARY` | SHA exacto en el directorio; `subject=fadena-std` | 18 | **A — candidato respaldado**; decisión formal pendiente. |
| `src_elmasri_navathe_sistemas_bd` | Elmasri & Navathe, Sistemas de BD | `COMPLEMENTARY` | SHA exacto de libro en el directorio; DB `subject=Cybersecurity`, no `fadena-std` | 9.116 | **A — candidato respaldado por presencia local**; confirmar bibliografía/rol complementario. |
| `src_f3352475bc0cd360` | SQL básico — soluciones de ejercicios | **Sin rol** | SHA exacto en el directorio; `subject=fadena-std`; existe y tiene chunks | 8 | **B — revisión requerida**: decidir política de soluciones/evaluaciones y rol; no asignarlo ni quitar ACL automáticamente. |
| `src_f93b8a264e20359c` | SQL básico | `PRIMARY` | SHA exacto en el directorio; `subject=fadena-std` | 26 | **A — candidato respaldado**; decisión formal pendiente. |
| `src_fadena_prog_archivos` | Manejo y persistencia de archivos | `PRIMARY` | Dos documentos bajo almacenamiento/benchmark; no hay SHA coincidente en `fuentes/fadena-std`; DB `subject=Cybersecurity` | 9 | **D — revisión de procedencia/alcance**: el título apunta a programación/archivos y la procedencia local de curso no está demostrada. |
| `src_fadena_std_unidad1` | Tratamiento de Datos — Unidad 1 | `PRIMARY` | SHA(s) coinciden con `UNIDAD1.pdf` y `UNIDAD1STD.pdf`; DB `subject=Cybersecurity` | 205 | **A — candidato respaldado** por material de cátedra; no equivale a programa oficial completo. |
| `src_marques_bases_de_datos` | Marqués, Bases de datos | `COMPLEMENTARY` | SHA exacto de libro en el directorio; DB `subject=Cybersecurity`, no `fadena-std` | 1.028 | **A — candidato respaldado por presencia local**; verificar bibliografía/rol complementario. |
| `src_ramakrishnan_gehrke_dbms` | Ramakrishnan & Gehrke, DBMS | `COMPLEMENTARY` | SHA exacto de libro en `fuentes/fadena-std`; DB `subject=Cybersecurity`, no `fadena-std` | 7.090 | **A — candidato respaldado por presencia local**; confirmar bibliografía/rol complementario, pues `course` está vacío. |
| `src_ramalho_fluent_python` | Ramalho, Fluent Python | `IMPLEMENTATION` | Fuente bajo almacenamiento/benchmark; sin SHA coincidente en el directorio de curso; DB `subject=Cybersecurity` | 5.683 | **D — revisión de pertinencia**: evaluar contra objetivos de formatos/ETL del programa y confirmar por qué se incluye Python; rol declarado no basta. |
| `src_rosen_matematicas_discretas` | Rosen, Matemáticas discretas | **Sin rol** | Dos registros de documento, fuera del directorio del curso; `subject=Cybersecurity`; **0 chunks** | 0 | **B — revisión requerida**: sin procedencia curricular específica ni evidencia recuperable hoy; preservar fila/ACL mientras se decide. |
| `src_silberschatz_fundamentos_bd` | Silberschatz et al., Fundamentos de BD | `PRIMARY` | SHA exacto de libro en el directorio; DB `subject=Cybersecurity`, no `fadena-std` | 9.737 | **A — candidato respaldado por presencia local**; verificar que la autoridad `PRIMARY` concuerde con programa/bibliografía oficial. |

El catálogo de roles contiene además
`src_cairo_guardati_estructuras_datos` como `FORMAL` con estado
`SOURCE_MISSING`; no tiene fila en `sources`, documento, chunks ni asociación
ACL. Se registra como **C — referencia declarada sin fuente local**: no
crear fila ni ACL basándose en esa declaración.

**Cierre de clasificación de evidencia (sin decidir autorización ACL):**

- **BACKED — 26/30:** hash exacto contra archivo local y rol notebook declarado.
  Es evidencia de procedencia, no aprobación normativa.
- **REVIEW_PENDING — 4/30:** dos filas B con rol ausente y dos filas D sin
  coincidencia local del hash; la evidencia actual no basta para decidir su
  pertenencia/rol.
- **NONEXISTENT — 1 referencia separada:** `src_cairo_guardati_estructuras_datos`
  figura en el catálogo de roles como `SOURCE_MISSING`, pero no integra las 30
  asociaciones ni tiene registro/fuente local. No crearla ni asociarla.

**Decisión de autoridad ACL:** permanece `PENDING` para las **30/30**
asociaciones existentes; el estado actual de la ACL no se reinterpreta como
aprobación humana. No hay decisión `REJECT` en este corte: no se revisaron los
contenidos completos ni existe criterio curricular autorizado para rechazar
fuentes. `BACKED`, `REVIEW_PENDING` y `NONEXISTENT` describen evidencia, no
acciones de conceder, conservar o revocar acceso.

La prueba E2E documentada en la sección siguiente confirma el filtrado de una
fuente positiva y una negativa sobre una copia temporal real, incluido
ContextPack/prompt/SSE/provenance. No adjudica las 30 asociaciones, no cubre
todos los scopes ni compara el almacén vectorial. No se modificaron
asociaciones; las 30 ACL permanecen intactas y Gate 2 continúa **PARCIAL**.

#### E2E de aislamiento `fadena-std` sobre copia temporal — 2026-09-29

Se ejecutó
`test_fadena_std_real_corpus_isolation_on_temporary_database_copy` contra una
copia SQLite consistente de `knowledge_store.db`, creada mediante
`Connection.backup()` desde una conexión `mode=ro` para incluir correctamente
el estado confirmado en WAL. La copia pasó `PRAGMA integrity_check` y conservó
las 30 asociaciones de `fadena-std`. El endpoint se ejecutó con backend
capturador (`use_mock=True`); no se inició el lifespan de la aplicación ni se
usó el almacén vectorial productivo.

**Resultado:** `1 passed`. Para la solicitud de `fadena-std`, el retrieval
recibió `src_fadena_std_unidad1` y excluyó `src_fadena_leng_clase2`, aunque
ambos estaban en `active_sources`. El prompt capturado contiene el material de
la fuente positiva y no contiene el ID ni el marcador de la fuente ajena. El
evento SSE `phase_complete` contiene provenance únicamente para
`src_fadena_std_unidad1`, con `citation_id` y `doc_hash`; el backend devolvió
la respuesta esperada con cita `[E1]`. La prueba también verificó que el
`curriculum_id` persistido siguió siendo `fadena_v1`, que no se crearon
contratos custom, que las asociaciones no cambiaron y que los hashes del
archivo original y su WAL permanecieron iguales durante la ejecución.

**Límites y observaciones:** esto demuestra el recorrido integrado de una
fuente positiva y una negativa sobre el snapshot real, no la autorización
normativa de las 30 asociaciones, el aislamiento de todos los scopes, ni el
estado de `vector_store.db`. El backend es un capturador, no un proveedor LLM
real. Como el ID persistido no se migró, `fadena-std` siguió usando el fallback
neutral; no se probó la activación de `fadena_std_2026`. El endpoint registró
un warning porque la copia no contiene la tabla opcional
`curriculum_progress`; el intento de actualizar progreso no tuvo efecto y no
impidió completar el flujo. No se modificaron ACL, `curriculum_id`, qrels ni
Golden Sets. Gate 2 continúa **PARCIAL**.

#### Expediente de evidencia curricular para fuentes pendientes de `fadena-std` — 2026-09-29

Se hizo una revisión read-only de la metadata SQLite, `notebook_source_roles`,
`notebook_kc_catalog`, los documentos/chunks indexados y los archivos bajo
`fuentes/fadena-std`. La revisión inicial no tenía acceso al programa analítico,
pero el usuario compartió después **“Programa Sistema de Tratamientos de Datos
2026”**, de nueve páginas, cuya portada identifica la Licenciatura en
Ciberdefensa, año 2026, y atribuye la materia a Gustavo A. Pereira, Adrián
Chamudis y Mauro Maidana. El documento declara **60 horas**, describe siete
módulos y contiene bibliografía. Se usa como el programa analítico aportado
para el cotejo; el archivo no contiene firma digital verificable. Esto
reemplaza la conclusión anterior de que el programa analítico no estaba
disponible. `UNIDAD1STD.pdf` queda como evidencia local complementaria.

Identificación del PDF aportado: `Programa Sistema de Tratamientos de Datos
2026.pdf`, 9 páginas; SHA-256
`8a759571cbce5ee67814b9e4b4618a684b59bd2e5b8c6bbbaa1ab54859cf88bf`.

**Cotejo de fuentes institucionales públicas:** la página oficial de
[Licenciatura en Ciberdefensa de FADENA](https://undef.edu.ar/fadena/carreras-de-grado/licciberdefensa/)
y el [plan de estudios oficial enlazado (PDF)](https://undef.edu.ar/fadena/wp-content/uploads/2026/02/Licenciatura-en-Ciberdefensa.pdf)
corroboran la materia en el segundo cuatrimestre con **64 horas**; la
[oferta académica de UNDEF para FADENA](https://undef.edu.ar/oferta-academica/oferta-academica-fadena/)
corrobora que la carrera pertenece a esa facultad. El PDF lista “Sistemas de
Tratamiento de Datos” en el segundo cuatrimestre con **64 horas**.
El programa analítico compartido declara **60 horas**, y el handout local de
soluciones SQL declara 64 h: se registra la discrepancia sin escoger una
versión como autoritativa ni editar datos.
`RDN-13-1.pdf` es el número 13 (agosto de 2026) de una publicación de UNDEF,
no un reglamento curricular ni el programa analítico; no se usa para adjudicar
las fuentes.

El programa analítico cubre estructuras de datos y sistemas de archivos/SGBD
(Módulo 1); SQL y bases relacionales (Módulos 2–4); CSV, XML, JSON, YAML, logs
y REGEX (Módulo 5); y ETL/Big Data (Módulo 7). Su bibliografía enumera
Coronel & Morris, Cairo & Guardati, Silberschatz et al., Date, Kroenke,
Elmasri & Navathe, Ramakrishnan & Gehrke y Marqués. Seis títulos bibliográficos
corresponden a sources asociados existentes en la matriz; Cairo & Guardati
figura en el programa, pero su source declarado en configuración
(`src_cairo_guardati_estructuras_datos`) sigue sin fila/fuente local ni ACL.
No enumera Rosen, Joyanes ni Ramalho. La coincidencia temática por sí sola no
prueba adopción bibliográfica.

Los otros programas compartidos (Telecomunicaciones 2025, Lenguajes de
Programación 2026, Sistemas Operativos II 2026 y Sociedad y Estado 2026) son
fuentes primarias de sus propias asignaturas, no de las ACL de `fadena-std`.
Que Lenguajes trate Python o Sistemas Operativos incluya sistemas de archivos
no autoriza trasladar fuentes entre notebooks.

| Fuente asociada | Evidencia a favor | Límites / evidencia contradictoria | Estado de adjudicación |
|---|---|---|---|
| `src_f3352475bc0cd360` — SQL Básico, soluciones | SHA-256 exacto con el handout `6 - SQL Básico - Soluciones Ejercicios.pdf` en `fuentes/fadena-std`; la portada identifica la carrera, asignatura y año 2026. El programa analítico incluye SQL en Módulo 3. | No tiene rol en `notebook_source_roles.json` ni cita bibliográfica propia; `sources.course` está vacío y `sources.role=PRIMARY` es global. El handout declara 64 h, frente a las 60 h del programa analítico (el plan de carrera público declara 64 h). No se ha definido la política pedagógica para exponer soluciones. | **Pertenencia material al curso: fuerte y corroborada. Rol/uso y ACL: `PENDING`.** No asignar rol ni alterar ACL automáticamente. |
| `src_rosen_matematicas_discretas` — Rosen, Matemáticas discretas | La fuente existe y está asociada a cuatro notebooks (`NB-CYBERSECURITY-V1`, `NB-SEC-01-C-PTR`, `fadena-std`, `fase0-soc`). | No hay SHA coincidente en `fuentes/fadena-std`, no tiene rol declarado para este scope y sus dos documentos suman 0 chunks. El programa analítico no lista Rosen ni incluye un módulo de Matemática Discreta. | **`UNRESOLVED` — no hay evidencia de pertenencia a esta asignatura.** No equivale a una decisión de rechazo o revocación. |
| `src_fadena_prog_archivos` — Manejo y persistencia de archivos | El metadata de rol lo describe como material de cátedra “Estructuras de Datos y Archivos” atribuido a Pereira/Chamudis/Maidana, los mismos docentes que figuran en el programa. Este incluye estructuras de datos y sistemas de archivos/SGBD en Módulo 1. | No hay SHA coincidente con `fuentes/fadena-std`; `course` está vacío y `subject=Cybersecurity`. El contenido indexado trata operaciones de archivos en un fragmento de Fundamentos de Programación; no se identificó portada de apunte de cátedra ni autoría del archivo. El programa lista Cairo & Guardati para estructuras de datos, pero no este título ni Joyanes. También está asociado a tres scopes ajenos. La relación temática y los nombres de docentes en metadata no prueban que este artefacto sea material del curso. | **`UNRESOLVED` — afinidad curricular real, procedencia del documento no establecida.** Rol y ACL `PENDING`. |
| `src_ramalho_fluent_python` — Luciano Ramalho, Fluent Python | El programa analítico cubre CSV, XML, JSON, YAML, logs y REGEX en Módulo 5, y ETL en Módulo 7; la metadata describe relación con parte de esos contenidos. | La fuente real es el libro general *Fluent Python* (2.ª ed., Python 3.10; 1.011 páginas), no un apunte limitado a formatos/REGEX. No hay SHA coincidente con `fuentes/fadena-std`, no está en la bibliografía del programa, `course` está vacío y `subject=Cybersecurity`. Sus 5.683 chunks abarcan el libro; hay afinidad de algunos temas, no validación de bibliografía o procedencia. Está compartido con otros tres scopes. | **`UNRESOLVED` — relevancia temática parcial confirmada, adopción/procedencia no acreditada.** Rol y ACL `PENDING`. |

**Conclusión del cotejo:** el programa analítico compartido mejora y diferencia
la evidencia:

- `src_f3352475bc0cd360`: material de curso claramente identificado, pero
  pendiente de rol pedagógico y política sobre las soluciones.
- `src_fadena_prog_archivos`: su tema y los docentes indicados en metadata son
  compatibles con el programa, pero no se ha demostrado la procedencia del
  archivo específico.
- `src_ramalho_fluent_python`: varios temas coinciden expresamente con módulos
  del programa, pero Ramalho/Fluent Python no aparece en la bibliografía ni se
  acreditó el uso de ese libro como material de cátedra.
- `src_rosen_matematicas_discretas`: sin tema equivalente ni entrada
  bibliográfica en el programa.

Así, el programa analítico aportado permite resolver la correspondencia
temática de algunas fuentes, pero no convierte todas las asociaciones
existentes en ACL autorizadas. La discrepancia 60 h/64 h queda pendiente de
reconciliación documental. Las 30 asociaciones siguen sin decisión ACL humana;
no se cambió ninguna fila, rol, `curriculum_id`, fuente, qrel ni Golden Set.
Gate 2 continúa **PARCIAL**.

**Congelamiento actualizado del expediente — 2026-09-29:** el programa
analítico provisto por el usuario es evidencia primaria nueva y reemplaza la
conclusión anterior de que faltaba localizarlo. Se cierra la recopilación sobre
las cuatro fuentes con este baseline:

| Dimensión | Estado congelado |
|---|---|
| Asociaciones existentes de `fadena-std` | 30, sin cambios |
| Procedencia local respaldada por hash y rol declarado | 26 `BACKED`; evidencia, no aprobación |
| Casos restantes | 4 `REVIEW_PENDING`: una fuente de curso con rol/uso pendiente; tres con temas ausentes o afinidad sin procedencia/bibliografía demostrada |
| Referencia sin fila/fuente/asociación | 1 `NONEXISTENT`: `src_cairo_guardati_estructuras_datos`; ahora respaldada como entrada bibliográfica del programa, pero sigue sin objeto fuente local ni ACL. No crear ni asociar automáticamente |
| Aislamiento E2E | `PASS` para el caso positivo/negativo probado en snapshot real; no generaliza a las 30 asociaciones ni a todos los scopes |
| Fuente curricular | Programa analítico aportado para 2026, con siete módulos y bibliografía (60 h); plan público de carrera y handout local indican 64 h |
| Decisión ACL / migración | `PENDING`; cero escrituras autorizadas |
| Gate 2 | **PARCIAL** |

Este congelamiento es documental, no una decisión de conservar, conceder o
revocar ninguna asociación. El siguiente trabajo de esta línea requiere
reconciliar la discrepancia de carga horaria y definir autoridad/rol para
materiales no listados en la bibliografía; el registro `src_cairo...` requiere
una decisión separada sobre cómo materializar una referencia bibliográfica que
actualmente carece de fuente local. No inferir cambios de ACL por afinidad
temática.

#### Revisión de ACL de `NB-SEC-01-C-PTR` y plan de implementación

La revisión se realizó sobre un snapshot temporal read-only de
`knowledge_store.db`; no se consultó ni modificó `vector_store.db` y no se
cambió ninguna asociación persistida.

**Estado observado:**

- `notebook_sources` contiene **42 asociaciones únicas** para
  `NB-SEC-01-C-PTR`: **41** resuelven a una fila `sources` y **1**
  (`src_Stallings.William.-.Sistemas.Operativos.5ed.pdf`) es huérfana: no tiene
  registro en `sources` ni chunks en `chunks`.
- Las 41 fuentes existentes representan **105.179 chunks** unidos al scope.
  Esto coincide con el scope grande de la medición de capacidad; cualquier
  narrowing puede modificar tanto relevancia/calidad como memoria y latencia.
- Las 41 filas existentes tienen `sources.role=PRIMARY`,
  `sources.subject=Cybersecurity` y `sources.course=NULL`. Ese `role` es el
  metadato general de la fila fuente, no rol validado para el nodo; el
  `subject` está contradicho por títulos y carpetas de materias. Ninguno de
  esos campos justifica mantener una ACL.
- La mezcla incluye materiales de redes/telecomunicaciones, bases de datos,
  Lenguajes, FADENA SO II, estructuras de datos, seguridad y programación en C.
  Ejemplos claramente ajenos al nodo de punteros/C: fuentes de bases de datos,
  Telecomunicaciones, concurrencia/planificación de SO y el roadmap
  `src_roadmap_nuevo_horizonte`.
- La ACL amplia no coincide con el límite explícito del roadmap:
  `SEC-01-C-PTR` se describe como “Punteros, Aritmética y Modelo de Memoria en
  C”, con competencias `COMP-C-POINTERS` y `COMP-MEMORY-LAYOUT`. Los nodos
  posteriores del mismo roadmap separan procesos, gestión de memoria/
  vulnerabilidades, concurrencia y seguridad binaria.

**Bloqueo de calidad que impide una poda inmediata:** los **420 de 420**
registros de `data/eval/golden_set_v2_401.json` asignan su `notebook_scope`
exclusivamente a `NB-SEC-01-C-PTR`, pese a que la rúbrica incluye otras
materias/nodos. Entre los `kc_ids` aparecen `so2_gestion_memoria` (347
apariciones), `so2_procesos` (160), `so2_concurrencia` (80) y
`aritmetica_punteros` (77). Por tanto, ese golden set parece una evaluación
del corpus de ciberseguridad/sistemas completo alojada bajo el scope del nodo
SEC-01, no un oráculo limpio de su ACL. Podar fuentes de SO, bases de datos o
seguridad antes de separar/corregir esa asignación causaría una regresión
artificial en el benchmark; conservarlas solo por ese benchmark perpetuaría
contaminación de scope. El golden set debe revisarse/versionarse antes del
cambio ACL y ninguna métrica actual se interpreta como autorización.

**Propuesta de alcance de referencia, no allowlist aprobada todavía:**

| Tratamiento propuesto | Fuentes/criterio |
|---|---|
| Candidatas núcleo para una ACL estricta SEC-01 | `src_fadena_prog_punteros`, `src_fadena_leng_clase2`, `src_marzal_intro_programacion_c`, `src_urrutia_programacion_c_principiantes`, `src_stallman_gnu_c_manual` y `src_joyanes_fundamentos`. Sus identidades apuntan directamente a punteros, programación en C o fundamentos de programación; antes de retener cada una, verificar chunks esperados/reales para las competencias SEC-01. |
| Candidatas secundarias que requieren decisión curricular | `src_fadena_prog_lineales`, `src_fadena_leng_clase1`, `src_bel_algoritmos_estructuras_python`, `src_goodrich_dsa_python` y `src_spraul_think_like_a_programmer`. Pueden aportar estructuras/algoritmos, pero no deben mantenerse automáticamente en el nodo por ser programación general. |
| Fuentes que deberían salir de la ACL estricta SEC-01, salvo una justificación por contenido y objetivo | Fuentes de bases de datos; Telecomunicaciones/redes; SO II, planificación y concurrencia; archivos; Roadmap Nuevo Horizonte; y material general de seguridad/redes. Esos contenidos deben quedar en el scope curricular/nodo que corresponda, no copiarse aquí por similitud temática. |
| Registro huérfano | `src_Stallings.William.-.Sistemas.Operativos.5ed.pdf`: no es recuperable como fuente hoy (sin fila ni chunks). Retirar solo su vínculo huérfano en una transacción posterior; no borrar ni actualizar otras fuentes y comprobar el vector store por separado antes de la operación. |

La lista núcleo es una **propuesta para validar**, no una aprobación final:
los títulos no sustituyen revisar los chunks específicos ni confirmar si el
notebook pretende representar solo SEC-01 o agrupar varios nodos de
ciberseguridad. Los capítulos de overflow/heap/seguridad pueden pertenecer a
SEC-03/SEC-05 y necesitan mapping a esos nodos, no una expansión silenciosa de
SEC-01.

**Plan de implementación seguro:**

1. **Resolver el contrato funcional antes de borrar ACL:** corregir o versionar
   el golden set con scopes que correspondan a cada nodo/curso y fijar
   explícitamente si `NB-SEC-01-C-PTR` es únicamente SEC-01 o un cuaderno
   agregado. Conservar el archivo actual como histórico; no sobreescribirlo
   sin registro de procedencia y nueva versión.
2. **Congelar propuesta de fuentes por objetivo:** para cada fuente candidata,
   mapear source ID → archivo/hash → fragmentos que sustentan punteros,
   aritmética C o modelo de memoria → rol y nodo propietario. Cualquier fuente
   sin correspondencia demostrable queda fuera de la propuesta núcleo y
   visible como decisión pendiente.
3. **Generar un diff ACL de solo lectura:** comparar los 42 links actuales con
   la allowlist aprobada y producir listas exactas de conservar, retirar,
   reubicar (solo con destino explícito) y huérfanas. No usar la unión de
   `DEFAULT_NOTEBOOKS.sources`, roles o nombres de carpeta para crear
   asociaciones.
4. **Probar en fixtures y snapshot:** crear pruebas que impongan coincidencia
   exacta de ACL; consultas positivas de punteros/C y modelo de memoria;
   negativas de bases de datos, redes, Telecomunicaciones y temas SO no
   autorizados; abstención con evidencia insuficiente; preservación de
   asociaciones compartidas que otros notebooks todavía requieran; y
   verificación de que el vector store no habilite chunks sin una asociación
   válida en `notebook_sources`.
5. **Medir antes/después en el benchmark corregido:** Recall/MRR/cobertura por
   `kc_id` y scope, cero candidatos fuera de ACL, p50/p95, candidatos y RSS.
   La evaluación debe incluir tanto el nodo SEC-01 como los scopes separados
   que reciban material reubicado. Si los resultados no cumplen, detener el
   cambio y revisar la allowlist, no ampliar el fallback.
6. **Aplicar como migración separada y reversible:** crear y verificar backup
   consistente; ejecutar primero el diff sobre una copia; validar integridad,
   conteos, citas, FTS y retrieval; preparar transacción idempotente para
   borrar únicamente links aprobados y la asociación huérfana; conservar filas
   de `sources`, chunks y embeddings, especialmente cuando sean compartidos.
   Aplicar a la base activa solo con aprobación explícita, ventana de
   mantenimiento y procedimiento de rollback documentado.
7. **Cerrar con evidencia:** registrar hash/backup, diff de links antes/
   después, salida de integrity checks, pruebas, benchmark y confirmación de
   que scopes hermanos no perdieron fuentes. La base activa actual no se
   modifica durante esta revisión.

**Dictamen:** se confirma la ACL como excesivamente amplia para el nodo SEC-01
y con una asociación huérfana; no se ejecuta aún la poda. El mapeo erróneo de
los 420 casos de golden set al mismo notebook bloquea una reducción segura.
El siguiente trabajo es separar intención de benchmark por nodo y validar la
allowlist propuesta; después se puede implementar y probar la migración sobre
snapshot antes de decidir cualquier aplicación sobre la base activa.

El diagnóstico no encontró un mapping explícito `alias → notebook_id`. Los
bridges autorizan cruces temáticos, no identidad; aliases dentro de KCs son
sinónimos de conceptos, no IDs de notebook. Se corrigió también la
clasificación para que un notebook presente solo en el catálogo (como
`catalog-only` en el fixture) no reporte falsamente
`CURRICULUM_ID_MISMATCH`, y para que los dos IDs cuyo nombre contiene
“Legacy Alias” se clasifiquen explícitamente como scopes legacy sin destino de
alias. `fadena-sye` sí se reporta como mismatch entre catálogo y su placeholder
SQLite nulo; esa diferencia no se interpreta como aprobación para activarlo.

La nueva matriz auditable vive en
[`config/notebook_identity_decisions.json`](../config/notebook_identity_decisions.json).
Corrige dos conclusiones preliminares del primer informe: `NB-SEC-01-C-PTR`
no es un custom desconocido sino un scope de tema referido por el roadmap
versionado; y los únicos notebooks SQLite sin registry/catálogo curricular
con procedencia aún indeterminada son `nb_prog_1` y `nb_prog_basica`. Sus
carpetas antiguas (“Carrera Programación” y “Fase 0 - Ciberseguridad”) son
indicios, no equivalencias canónicas, por lo que se preservan sin mapear.

La configuración de roles se completó para 33 fuentes que ya estaban
asociadas y cuyo `subject`/nombre de archivo coincide con el scope y la
carpeta de materia. El script verificó sobre snapshot que las 33 entradas
están dentro de su ACL existente. Se excluyeron deliberadamente las soluciones
SQL, Stallings 5.ª edición reemplazada, fuentes de programación/Rosen sin
carpeta de materia inequívoca y las fuentes faltantes declaradas. No cambió
ninguna fila de `notebook_sources`.

Se detectó además que el campo `sources.subject` no es consistente como
identidad académica: tiene 41 filas con `Cybersecurity`, mientras otras filas
usan slugs de materia; `course` es NULL en las 76. Varias fuentes con
`subject=Cybersecurity` también están explícitamente asociadas a cuadernos
FADENA. Se conservan los campos en el informe como contexto, no se usan para
inferir permisos o alias.

No se aplicaron cambios a `notebook_sources`. Se actualizaron únicamente
metadatos de roles para 33 fuentes ya asociadas y cotejadas con sus
carpetas/subject de curso. Los roles restantes no se ampliaron por falta de
procedencia inequívoca o por riesgo (soluciones). Los mappings curriculares
quedan resueltos como destino declarativo para los cinco cursos canónicos,
pero su persistencia requiere una migración separada con copia, revisión y
aprobación. La autoridad del programa de `fadena-std` aún debe cotejarse. La
ACL de `NB-SEC-01-C-PTR` es el bloqueo principal de alcance; no se altera sin
una lista de fuentes esperadas revisada.

**Validación revisada:** reconciliación más aislamiento del ensamblador
pedagógico — **11 passed**; la matriz más reciente reporta seis discrepancias de
`curriculum_id` (cinco filas canónicas con `fadena_v1` y el placeholder
`fadena-sye` con `NULL`); Black para Python 3.12 y flake8 selectivo
(`E9,F63,F7,F82`) pasaron; `git diff --check` pasó. Las pruebas cubren
desacuerdos de `curriculum_id`, catálogos incompletos, IDs ausentes, roles
sin asociaciones, fuentes locales no declaradas, fuentes compartidas por ACL
explícita, JSON inválido y ausencia de escrituras (hash y `mtime_ns` del
fixture sin cambios).

**Estado del paso 1: identidad decidida; autorización de fuentes y migración
pendientes.** Se confirmó `NB-SEC-01-C-PTR` como scope de roadmap, se separó
de `NB-CYBERSECURITY-V1`, y se identificaron solo dos scopes custom sin
procedencia (`nb_prog_1`, `nb_prog_basica`); `fadena-sye` es un placeholder
sin asociaciones. Los IDs legacy no son aliases. Los cinco mappings
curriculares del catálogo son destinos declarativos, mientras las seis filas
persistidas discordantes requieren migración separada. Para completar el
cierre operativo falta acordar las fuentes autorizadas y roles de las
asociaciones adicionales —especialmente el scope SEC-01— contra la
bibliografía/programa; las asociaciones actuales permanecen intactas. No
ejecutar reparación sobre la base activa sin snapshot, respaldo y procedimiento
separado.

## Gate 3 — Cerrar criterios de aceptación de F5

Añadir o completar pruebas deterministas para:

- una instrucción puntual que contradice una preferencia histórica;
- referencias y ejercicios cuando falta el antecedente, enunciado o intento;
- feedback limitado al intento visible y su contexto;
- ausencia de mutación BKT/perfil por conversación ordinaria sin evidencia
  evaluativa;
- alcance y límites de los avisos heurísticos de discrepancia entre fuentes.

**Salida:** continuidad aislada, trazable y basada en evidencia, sin inferir
aprendizaje o dominio a partir de la mera conversación.

## Gate 4 — Cerrar F6 de extremo a extremo

- Definir estados terminales distintos para éxito completo, truncamiento,
  cancelación, error y abstención/clarificación cuando corresponda.
- No guardar ni presentar como completa una respuesta que no tenga una
  terminación exitosa explícita; conservar y rotular texto parcial como
  incompleto cuando sea útil.
- Manejar truncamiento, aborto, EOF sin terminal, terminal duplicado y error
  posterior a texto en la UI.
- Separar mensajes públicos seguros de detalles de excepción internos.
- Probar el flujo endpoint SSE → consumidor UI con dobles deterministas;
  mantener separada cualquier validación con proveedor real.

**Salida:** ningún camino probado convierte una respuesta incompleta o fallida
en éxito silencioso.

## Gate 5 — Regresión global y habilitación de F7

- Ejecutar pruebas focalizadas después de cada gate y la suite global una vez
  integrados los cambios.
- Construir una matriz equilibrada de currículos e intenciones: explicar,
  resumir, “no entendí”, ejercicio, corrección y seguimiento.
- Fijar la rúbrica y los criterios de aceptación antes de puntuar respuestas.
- Reportar resultados por currículo e intención, con límites y fallos visibles.
- Mantener evaluación de respuestas separada de cualquier afirmación de
  retención o transferencia del estudiante.

**Salida:** decisión documentada de aceptar, iterar o declarar inconclusa la
evaluación; comenzar F7 solo cuando los gates anteriores sean satisfactorios.

## Criterio global de cierre

La suite queda cerrada cuando:

1. las políticas y la nomenclatura son coherentes;
2. ningún cuaderno recibe por fallback pedagogía de otro currículum;
3. los criterios pendientes de F5 están cubiertos por pruebas;
4. los estados de SSE/UI no presentan truncamientos o fallos como éxito;
5. las pruebas focalizadas y globales pasan, o cada excepción tiene causa,
   alcance e impacto documentados sin ocultar un fallo;
6. los documentos describen exactamente lo implementado y validado.

## Límites

- No repetir la comparación TALOS/NotebookLM de 20 preguntas sin solicitud
  explícita y protocolo registrado.
- No copiar al repositorio el historial privado de NotebookLM.
- No modificar umbrales, límites de tokens ni timeouts sin evidencia medida.
- No tratar datos curriculares configurados como prueba suficiente del
  comportamiento de extremo a extremo.
- No iniciar refactorizaciones ajenas a estos gates durante la suite.

## Documentos de contexto

- [Diagnóstico multi-cuaderno y plan de continuidad](./DIAGNOSTICO_MULTICUADERNO_Y_PLAN_DE_CONTINUIDAD.md)
- [Plan rector de mejora pedagógica](./PLAN_MEJORA_PEDAGOGICA_TALOS.md)

## Auditoría de scopes del benchmark v2.401 — 2026-09-28

Se comparó `golden_set_v2_401.json` con su fuente anterior
`golden_set_v2_400.json`, sus qrels y la ACL persistida. La comprobación fue
read-only: no se ejecutó retrieval, no se abrió `vector_store.db` y no se
modificó ninguna base.

**Resultado:** v2.401 no se puede usar como benchmark de referencia para podar
la ACL de SEC-01 ni basta con restaurar el campo `notebook_scope`.

- v2.400 asignaba 70 de sus 400 casos a cinco scopes secundarios
  (`NB-CYBERSECURITY-V1`, `fadena-so2`, `fadena-lenguajes`,
  `fadena-teleco` y `fadena-std`). En v2.401, los 420 casos —incluidos los 20
  casos nuevos de depuración— quedaron asignados a `NB-SEC-01-C-PTR`.
- Para los 70 casos reasignados, los qrels actuales de v2.401 tienen 330
  referencias a chunks. **224/330** apuntan a fuentes no autorizadas por el
  scope secundario que esos casos tenían en v2.400. Por lo tanto, revertir solo
  `notebook_scope` generaría un conjunto internamente inconsistente.
- v2.400 conserva 352 expectativas de abstención, incluidas 292 consultas que
  no pertenecen a la categoría `ood_trampas`. El runner actual rechaza esas
  expectativas para categorías no-OOD. El generador v2.401 las normaliza
  forzando `abstention=false` y recuperando evidencia bajo SEC-01; eso oculta
  pruebas negativas de scope en vez de modelarlas en el contrato del runner.
- El metadata v2.401 declara 320 consultas de notebooks primarios y 100 de
  secundarios, pero el dataset asigna las 420 a SEC-01.

La evidencia y el bloqueo estructurado también están registrados en
`config/notebook_identity_decisions.json`, dentro de la decisión de
`NB-SEC-01-C-PTR`.

El procedimiento operativo y los criterios para ejecutar la reparación y el
piloto de forma segura están en
[GATE2_BENCHMARK_SCOPE_RUNBOOK.md](./GATE2_BENCHMARK_SCOPE_RUNBOOK.md).

**Siguiente implementación segura:**

1. ~~Definir una nueva versión del benchmark que preserve los scopes previstos
   y distinga consultas positivas, OOD globales y negativas por scope
   autorizado.~~ **Completado en contrato de fixtures — 2026-09-28.**
2. ~~Ajustar la validación del runner para aceptar solo la forma explícita y
   etiquetada de oráculos negativos por scope; mantener el rechazo de
   abstenciones accidentales y de qrels vacíos para consultas positivas.~~
   **Completado para validación y scoring livianos — 2026-09-28.**
3. Regenerar qrels por scope en ejecución controlada sobre snapshots/copia,
   nunca sobre la base activa; mantener límites de carga y no correr aquí un
   benchmark pesado por el antecedente de temperatura/CPU.
4. ~~Derivar los conteos del metadata desde los registros finales y probar:
   unicidad/completitud de query IDs, correspondencia exacta con qrels,
   pertenencia de todos los chunks qrel a la ACL declarada y separación entre
   scopes antes de considerar cualquier poda.~~ **Completado con fixtures
   pequeños — 2026-09-28.**

### Implementación del contrato Gate 2 — 2026-09-28

Se añadieron [gate2_oracle.py](../src/study_engine/contracts/gate2_oracle.py)
y su validador/scorer
[gate2_oracle.py](../src/study_engine/retrieval/gate2_oracle.py). El contrato
solo acepta `positive_in_scope`, `ood_global` y `negative_by_scope`, exige
qrels no vacíos para positivas, qrels vacíos para las dos clases negativas,
verifica IDs completos, chunks existentes en el fixture y pertenencia a la
ACL declarada. Los cambios de scope requieren una decisión explícita.

La evaluación simulada trata una respuesta vacía como fallo para una positiva
y separa los conteos por tipo de oráculo. Las pruebas en
[test_gate2_oracle.py](../tests/unit/retrieval/test_gate2_oracle.py) cubren
también metadata inconsistente, chunks fuera de ACL y citas/candidatos
indebidos en oráculos negativos. Validación focalizada:
`.venv/bin/pytest -q tests/unit/retrieval/test_gate2_oracle.py
tests/unit/diagnostics/test_notebook_reconciliation.py` — **17 passed**.
No se ejecutó retrieval, no se abrieron las bases reales y no se modificaron
ACL activas ni golden sets históricos.

Hasta completar y aprobar esa nueva versión, no cambiar la ACL de SEC-01 ni
tratar las métricas v2.401 como baseline fiable para ella.

### Auditoría offline posterior al piloto Gate 2 — 2026-09-28

Se corrigió la pérdida de `topic_anchors` al normalizar el dataset: el contrato
`Gate2Query` y el generador ahora conservan los anclajes, con una prueba que
verifica el round-trip. Para la auditoría del piloto existente se usó el
dataset versionado del propio piloto con anclajes específicos; no se repitió
retrieval ni se abrieron las bases en escritura. La coincidencia es lexical y
sirve solo para priorizar revisión humana.

Resultados de `candidate-audit.json`:

- `GS2-VULN-004`: el candidato nuevo de Stallings y el qrel histórico
  `chk_0aa9aa4cc0b2_428_1` contienen el ancla `race condition`; ambos son
  recomendaciones de conservar/incluir sujetas a revisión humana. El qrel
  histórico `chk_07e0f6d0fb24_58_1` de Spraul no coincide con anclas temáticas;
  se recomienda revisar su retiro. No se cambió ningún qrel histórico.
- `GS2-OOD-001`: el pasaje de Joyanes sobre la comunidad informática mundial
  no coincide con anclas específicas del Mundial de México 1986; permanece
  como falso positivo lexical del retrieval y no como respuesta relevante.
- `G2-PILOT-NEG-001`: el pasaje de Joyanes no contiene Round Robin ni quantum;
  es falso positivo lexical. No se detectaron candidatos fuera de ACL.

La auditoría registra el hash de la base de conocimiento y mantiene su
conexión SQLite en solo lectura. El reporte del piloto confirma que los hashes
pre/post de las bases activa de conocimiento y vectorial coinciden y que los
snapshots temporales se limpiaron. Las anclas más específicas evitan contar
la mención genérica de “mundial” como soporte OOD.

Se completó una adjudicación técnica de un solo revisor, aceptada por el
usuario, en
[el formulario](../reports/gate2_pilot_v2_402_pilot1/gate2_v2.402-pilot1.qrel-adjudication.json):
el pasaje de checksum se propone excluir; el ejemplo de lockfile se clasifica
como evidencia parcial; el pasaje de archivo temporal se clasifica como
evidencia directa. La
[propuesta de pertenencia a qrels](../reports/gate2_pilot_v2_402_pilot1/gate2_v2.402-pilot1.qrel-membership-proposal.json)
conserva ambos chunks pertinentes y excluye el no pertinente. Incluye una
rúbrica semántica aprobada (3 directa, 2 sustancial pero parcial, 1 marginal,
0 irrelevante omitido) y qrels aceptados 2/3.

La inspección del generador histórico encontró que 3/2/1 se asignaban según
posición de retrieval (primero/segundo/restantes), no según una rúbrica
semántica documentada. La nueva rúbrica semántica fue aceptada explícitamente.
La revisión fue asistida por un solo asistente de IA, no ciega ni doble. No se
alteraron qrels históricos ni ACL activa.

El usuario aceptó las tres decisiones y la rúbrica. Se generó el paquete
[v2.402-pilot1-adjudicated](../reports/gate2_pilot_v2_402_adjudicated/) en
modo fixture, sin retrieval, con qrels OOD/negativa vacíos y el qrel positivo
adjudicado. La comprobación estructural y ACL en SQLite read-only pasó; v2.400,
v2.401 y ACL activa no se modificaron. El benchmark completo y la evaluación
end-to-end de abstención/citas continúan pendientes.

Como gate antes de ampliar retrieval se implementó
[`validate_gate2_segments.py`](../scripts/validate_gate2_segments.py). El
[reporte segmentado](../reports/gate2_pilot_v2_402_adjudicated/gate2_v2.402-pilot1-adjudicated.segment-validation.json)
pasó para tres segmentos por scope/oráculo: la positiva tiene dos qrels
autorizados (grados 2 y 3), OOD y negativa tienen qrels vacíos. Consulta solo
SQLite read-only para ACL y chunks referenciados; retrieval no ejecutado.
Las 17 pruebas focalizadas de validador, contrato y generador pasaron.

Se avanzó esa preparación en
[v2.402-positive-segments-review](../reports/gate2_positive_segments_v2_402/):
se seleccionó Deadlock (`GS2-VULN-018`) para SEC-01 y una consulta defensiva
de mitigaciones (`GS2-VULN-007`) para `fadena-so2`. La inspección local
read-only permite proponer un pasaje grado 2 por consulta; ambas decisiones
siguen pendientes del usuario. El gate estructural/ACL pasó y reporta
`release_eligible=false`. Se registraron bloqueos de `fadena-lenguajes`
(qrels de atributo GNU C incompatibles), `fadena-teleco` (qrels de overflow
para pregunta de heap/stack lifecycle) y `fadena-std` (sin positivos). No se
ejecutó retrieval.

Siguiente: el usuario acepta o corrige las dos propuestas y la exclusión del
duplicado. Luego se genera un paquete aprobado y se reejecuta el gate; solo
después se considera un piloto retrieval en snapshot por scope, sin saltar a
los 420 casos.

### Gate 2 — Publicación de los segmentos adjudicados — 2026-09-28

El usuario aceptó las dos adjudicaciones: `GS2-VULN-018` conserva el chunk
`chk_92876e0f2bc2_425_1` con grado 2 y excluye el duplicado; `GS2-VULN-007`
conserva `chk_0aa9aa4cc0b2_385_1` con grado 2 y excluye los cuatro candidatos
restantes. Se corrigió además una discrepancia en el ID de la decisión de la
negativa (`G2-PILOT-NEG-001`) antes de generar el paquete.

El paquete
[v2.402-positive-segments-adjudicated](../reports/gate2_positive_segments_v2_402_adjudicated/)
se generó en modo fixture, con retrieval desactivado. La
[validación estructural y ACL](../reports/gate2_positive_segments_v2_402_adjudicated/gate2_v2.402-positive-segments-adjudicated.segment-validation.json)
pasó con `release_eligible=true` y sin adjudicaciones pendientes: cinco
consultas, tres positivas, una OOD global y una negativa por scope; cuatro
qrels positivos grado 2/3. Se consultó la ACL y existencia de chunks en
SQLite read-only; el hash de `data/web_state/knowledge_store.db` coincide con
el del piloto previo. Los golden sets históricos y la ACL no se modificaron.

Pruebas focalizadas de contrato, generador, CLI, snapshot y validador:
**22 passed**. Este resultado acredita integridad estructural y pertenencia a
ACL, no ranking, calidad de retrieval ni abstención generativa. Siguiente:
revisar evidencia local para los scopes bloqueados (`fadena-lenguajes`,
`fadena-teleco`, `fadena-std`) y elegir un segmento positivo justificable.
No ejecutar retrieval adicional ni el benchmark de 420 consultas hasta ese
gate.

#### Auditoría local de scopes bloqueados — 2026-09-28

Se inspeccionó la ACL persistida y evidencia local mediante consultas SQLite
read-only, sin ejecutar el pipeline de retrieval, embeddings, reranking ni
generación. El
[reporte de auditoría](../reports/gate2_scope_evidence_audit_2026-09-28.md)
documenta los chunks y las limitaciones:

- `fadena-lenguajes`: los resultados para `clone()` corresponden al atributo
  GNU C *function cloning*, no al syscall Linux; permanece bloqueado y sin
  qrels propuestos.
- `fadena-teleco`: aparecen pasajes marginales de Stack/Heap sobre frames,
  disposición de memoria y asignación/liberación dinámica. Se proponen tres
  candidatos grado 1, pero no cubren velocidad de asignación ni toda la
  comparación; no se agregaron qrels.
- `fadena-std`: aparecen pasajes de mutex y semáforo contador en *Fluent
  Python*, propuestos grado 2. La propiedad del mutex no está explícita y el
  semáforo se desarrolla con `asyncio`; ambos siguen pendientes de adjudicación
  y no se agregaron qrels.

La búsqueda no cambia `v2.402-positive-segments-adjudicated`, sus decisiones
ni su elegibilidad. La puerta siguiente es adjudicar explícitamente los
candidatos parciales de `fadena-teleco` y `fadena-std` o mantenerlos
bloqueados; `fadena-lenguajes` requiere fuente autorizada pertinente o una
decisión curricular separada. No ejecutar retrieval de benchmark ni ampliar a
420 consultas en esta etapa.

#### Adjudicación de cinco candidatos y fixture std — 2026-09-28

El usuario adjudicó los cinco candidatos individualmente: los tres de
`fadena-teleco` (chunks `chk_0aa9aa4cc0b2_365_1`,
`chk_0aa9aa4cc0b2_366_1` y `chk_0aa9aa4cc0b2_416_1`) quedaron grado 1 y
excluidos de qrels; `chk_db97c77518c6_729_1` quedó grado 1 y excluido porque
no acredita ownership del mutex; `chk_db97c77518c6_821_1` quedó grado 2 y
aceptado como evidencia parcial del semáforo. El registro formal está en
[la adjudicación](../reports/gate2_scope_candidate_adjudication_2026-09-28.json).

Se generó una fixture nueva, sin sobrescribir el paquete anterior:
[v2.402-positive-segments-std-mutex-adjudicated](../reports/gate2_scope_candidate_adjudicated_v2_402/).
Añade `GS2-CMP-011` en `fadena-std` con el único qrel nuevo
`chk_db97c77518c6_821_1: 2`. El
[validador segmentado](../reports/gate2_scope_candidate_adjudicated_v2_402/gate2_v2.402-positive-segments-std-mutex-adjudicated.segment-validation.json)
pasó (`release_eligible=true`, seis consultas, cinco chunks qrel, cero
pendientes). El manifiesto confirma generación fixture sin retrieval.

Los otros cuatro candidatos no aparecen en qrels. El paquete
`v2.402-positive-segments-adjudicated`, ACL activa y golden sets históricos
permanecen intactos. `fadena-lenguajes` continúa bloqueado por mismatch
semántico; esta fixture no autoriza retrieval ni benchmark completo.

#### Inventario de readiness e impacto — 2026-09-28

Se comparó la fixture actual de seis consultas contra las 400 consultas de
v2.400, las 420 de v2.401 y la ACL persistida. El
[reporte de impacto](../reports/gate2_scope_readiness_impact_v2_402.md)
concluye que la fixture cubre cinco de los seis scopes v2.400, pero solo
5/400 IDs históricos (el control de aislamiento es nuevo). `fadena-teleco` no
está representado y `fadena-lenguajes` aparece solo con una negativa por scope,
sin positivo para `clone()`.

Ambos scopes siguen bloqueados para positivos: `fadena-lenguajes` por mismatch
entre function-cloning GNU C y el syscall Linux; `fadena-teleco` porque los
candidatos de Stack/Heap fueron adjudicados grado 1 y excluidos. Los otros
cuatro scopes contienen slices positivos estructuralmente válidos, pero no
cobertura aprobada de sus conjuntos históricos. Por tanto,
`release_eligible=true` solo califica a la fixture de seis consultas; el Gate 2
global y la reparación de v2.401 siguen bloqueados. No se ejecutó retrieval ni
se modificaron ACL o golden sets.

### Inventario de cobertura y validez de v2.400 — 2026-09-28

Se implementó `scripts/build_gate2_v2400_coverage_inventory.py` y sus pruebas
con fixtures SQLite/JSON pequeñas. El artefacto estructurado
[JSON](../reports/gate2_v2400_coverage_inventory_2026-09-28.json) y su
[vista auditable](../reports/gate2_v2400_coverage_inventory_2026-09-28.md)
inventarían las 400 consultas y las 165 referencias qrel de v2.400. Los
estados semánticos solo derivan del
[registro explícito de decisiones](../reports/gate2_v2400_explicit_decision_register_2026-09-28.json);
la membresía ACL se consultó en SQLite read-only y no se interpreta como
validación semántica.

Conteos derivados: 1 `APPROVED_OOD`, 3 `PARTIALLY_VALID`, 3
`BLOCKED_SEMANTIC`, 111 `PENDING_ADJUDICATION` y 282 `NO_VALID_QREL`; no hay
consultas `APPROVED_POSITIVE` o `APPROVED_NEGATIVE` bajo este registro
conservador. Por referencia: 1 `VALID`, 2 `PARTIAL`, 13 `INVALID` y 149
`PENDING`; 352 consultas carecen de referencias qrel históricas. El estado
`ABSENT` es por consulta y no se cuenta como referencia. Los estados
`INVALID` registran decisiones sobre referencias concretas, no una inferencia
automática sobre todas las referencias de su consulta.

La referencia de auditoría v2.401 sigue marcada `canonical_for_repair=false`,
`historical_evidence=true`, `action=NONE`: la comparación reproduce 70
cambios de scope, 330 referencias qrel asociadas y 224 fuera de la ACL del
scope correspondiente de v2.400; cero IDs faltantes. En el resumen por scope,
`NB-SEC-01-C-PTR` registra 70 consultas y 330 qrels importados por v2.401. Es
un hallazgo de integridad, no una decisión curricular. La ACL actual no
reconstruye la ACL histórica.

Verificación: pruebas focalizadas **7 passed**; `py_compile` y
`git diff --check` pasaron. No se ejecutaron retrieval, embeddings, reranking,
generación ni benchmarks; golden sets históricos, ACL y bases activas no se
modificaron.

**Siguiente paso:** preparar lotes pequeños de adjudicación manual a partir del
inventario, revisando primero la intención/oráculo de cada consulta y luego
cada par query/qrel pendiente por separado. Mantener `v2.401` solo como
referencia y no reparar los 224 casos ni ejecutar retrieval hasta contar con
decisiones explícitas.

#### Primer lote de adjudicación por consulta

El conteo del inventario distingue 111 consultas con estado
`PENDING_ADJUDICATION`; 42 tienen referencias qrel históricas y forman el
primer lote basado en evidencia existente. Las otras 69 no tienen qrels y
quedan para una etapa posterior de revisión de intención/oráculo; no se
convierten en negativas. El lote de 42 contiene 150 referencias: 149 siguen
pendientes individualmente y una ya tiene una decisión registrada, que se
conserva como tal. Por eso “42 consultas con qrels pendientes” no significa
que haya exactamente 42 consultas en el estado agregado `PENDING` ni 42 qrels.

La [cola de revisión JSON](../reports/gate2_v2400_query_adjudication_queue_2026-09-28.json)
y su [vista Markdown](../reports/gate2_v2400_query_adjudication_queue_2026-09-28.md)
son paquetes no decisionales derivados del inventario. Incluyen consulta,
scope, oráculo histórico e IDs de qrel, pero no copian texto de chunks. El
[constructor](../scripts/build_gate2_v2400_query_adjudication_queue.py) valida
el vínculo y conteo de referencias y rehúsa sobrescribir salidas existentes.
La cola no reemplaza ni modifica el registro de decisiones explícitas.

Verificación focalizada del inventario y la cola: **11 passed**;
`py_compile` y `git diff --check` pasaron. No se adjudicó contenido, no se
modificaron qrels/ACL/base SQLite y no se ejecutó retrieval.

### Reconciliación de H1–H3 y estado de Gate 2 curricular — 2026-09-29

La inspección del árbol actual confirma que los mecanismos centrales de los
hallazgos H1–H3 del diagnóstico ya están implementados: perfiles por ID exacto
con `curriculum_id` coincidente, fallback neutral para identidades desconocidas
o inconsistentes, contratos default sin analogías obligatorias y perfil
`fadena-std` etiquetado como Sistema de Tratamiento de Datos. Esto corrige la
descripción de defectos vigentes en el snapshot inicial de Gate 2; no debe
interpretarse como cierre formal del gate.

Validación ejecutada durante esta reconciliación:

```text
./.venv/bin/pytest -q tests/pedagogy/test_socratic_system_prompt.py \
  -k 'notebook_specializations_all_five or profiles_match_versioned_curriculum_catalog or unknown_and_legacy_like_ids_are_neutral or curriculum_mismatch_falls_back_to_neutral_contract or all_notebook_contracts_have_universal_safe_commands'
7 passed, 6 deselected
```

Es evidencia unitaria del contrato/perfil. Para cerrar Gate 2 siguen pendientes
la fuente curricular oficial del programa detallado de `fadena-std`, reconciliar
identidades y roles de fuentes con los registros efectivos, resolver cualquier
migración con autorización explícita y probar notebook → fuentes → contrato →
prompt HTTP/SSE con retrieval real para todos los currículos. La matriz HTTP/SSE
actual cubre cinco perfiles y fallback neutral con evidencia simulada; incluye
también precedencia de contratos custom y restricciones explícitas del turno.
Después se amplió el
test SSE para verificar cinco perfiles exactos y un ID parecido desconocido:
`test_chat_sse_sends_only_the_exact_curriculum_profile_to_backend` terminó con
**6 passed, 5 warnings**. El backend captura el prompt final, pero el contexto
de fuentes está simulado; el test no demuestra recuperación ni ACL reales. No
se ejecutó la suite global ni un proveedor real, no se migró la base local y no
se modificaron ACL, bases protegidas, Golden Sets ni qrels. Además,
`test_chat_sse_preserves_custom_contract_and_explicit_turn_request` pasó
(**1 passed, 5 warnings**) y comprobó la precedencia del contrato custom y la
preservación de una restricción explícita del estudiante. La corrida focalizada
combinada final de contratos de perfil, persistencia, endpoint SSE, allowlist
de fuentes y retrieval aislado terminó con **24 passed, 5 warnings**. La prueba
de allowlist es unitaria; el nuevo test SSE ejecuta retrieval real en una
fixture temporal.
`test_chat_sse_retrieves_only_sources_authorized_for_notebook_scope` añade
un caso `fadena-std` con fuentes, ACL relacional y chunks de fixture en el
KnowledgeStore temporal. El endpoint ejecuta retrieval real y el test verifica
que una fuente incluida en `active_sources` pero autorizada solo para otro
notebook no aparezca en el contexto/prompt ni en la procedencia SSE. El test no
usa corpus o ACL de producción; por eso Gate 2 permanece **PARCIAL**. Black y
`git diff --check` pasaron. No se ejecutó la suite global ni un proveedor real,
no se migró la base local y no se modificaron ACL, bases protegidas, Golden
Sets ni qrels.

La matriz requisito → test → datos → alcance demostrado → límite/pending está
en la sección **“Matriz de evidencia Gate B”** del
[diagnóstico multi-cuaderno](./DIAGNOSTICO_MULTICUADERNO_Y_PLAN_DE_CONTINUIDAD.md).
No iniciar reconciliaciones con escritura ni migraciones hasta registrar
primero la autoridad de cada identidad/fuente y la decisión explícita sobre los
registros locales discrepantes.
