# Suite de fixes y estabilización previa a Fase 7

**Fecha:** 2026-09-28
**Estado:** punto 0, Gate 1 y protección runtime inicial completados; Gate 2 pendiente
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

- Resolver perfiles por IDs registrados exactos, no por subcadena ambigua.
- Corregir `fadena-std` para que corresponda a Tratamiento de Datos.
- Retirar del contrato fallback fases y analogías específicas de programación;
  usar un contrato neutral si el cuaderno no tiene perfil explícito.
- Limitar supuestos de C/x86-64 a los cuadernos, materiales o pedidos que los
  justifiquen, no al prompt global.
- Verificar el recorrido real de cuaderno/currículum/fuentes hasta contrato y
  prompt final.

**Pruebas de salida:** perfiles de programación, Sistemas Operativos,
Tratamiento de Datos y Telecomunicaciones; assertions positivas de lo propio y
negativas de contaminación cruzada. Un ID desconocido usa un perfil neutral o
falla con un diagnóstico explícito; nunca hereda un perfil parecido.

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
