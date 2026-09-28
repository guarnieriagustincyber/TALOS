# Suite de fixes y estabilización previa a Fase 7

**Fecha:** 2026-09-28
**Estado:** punto 0, Gate 1 y protección runtime inicial completados; inventario y
análisis de preparación G2.0 documentados; implementación de Gate 2 pendiente
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
Datos” del prompt es incorrecta. No se encontró un programa analítico completo
que permita confirmar de forma independiente la cantidad exacta de unidades,
los siete módulos ni toda la nómina de autores que afirma la adaptación previa.
El catálogo lista siete KCs numeradas como unidades, pero eso no sustituye el
documento del programa. Por tanto, queda confirmado el nombre/área de la
materia; programa oficial, conteo total y bibliografía por unidad quedan
**pendientes de fuente**.

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

**Cambios de Gate 2 todavía no iniciados:** no se alteró el código de runtime,
los catálogos ni las filas SQLite; esta entrega cierra solo la fase de
inventario/caracterización. El procedimiento G2.1–G2.3 sigue vigente, con el
bloqueo de reconciliación de identidad/currículum añadido como prerrequisito.

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
  multiplicarse con scopes grandes y con workers/procesos concurrentes. No se
  midió RSS pico: los tamaños de matriz son estimaciones aritméticas, no una
  medición de RAM del proceso.

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

### Punto exacto para retomar

El análisis curricular y de crecimiento quedó documentado en G2.0b/G2.0c. No
se modificó código ni la base local. El siguiente trabajo es continuar Gate 2,
en este orden:

1. Reconciliar IDs canónicos/aliases, autoridad de `curriculum_id`, roles de
   fuentes y ciclo de alta para cuadernos nuevos; no migrar filas SQLite por
   suposición.
2. Fijar el contrato de scope y allowlist: FADENA aislado por materia y Roadmap
   transversal únicamente con asociaciones explícitas. Corregir los fallbacks
   que pierden aislamiento y probar el caso de fuentes insuficientes.
3. Congelar benchmark curricular y calidad end-to-end, y capturar baseline de
   rendimiento/RAM con el hardware de destino antes de refactorizar vector
   search.
4. Implementar perfiles/prompts exactos, resolver y validar el prompt final por
   cuaderno; luego abordar candidate retrieval acotado y deduplicación vectorial
   con pruebas comparativas de calidad, aislamiento y capacidad.
5. Cerrar Gate 2 y recién entonces continuar Gate 3 (F5), Gate 4 (F6) y Gate 5
   (regresión global/habilitación PED-F7) según sus criterios de salida.

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
