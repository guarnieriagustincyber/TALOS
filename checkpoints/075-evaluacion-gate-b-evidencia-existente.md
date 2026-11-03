# Checkpoint 075 — evaluación de Gate B con evidencia existente

## 1. Alcance y fuentes

Esta evaluación contrasta los cinco criterios Gate B de CP074 con evidencia
ya registrada en el repositorio. Es una evaluación documental; no cambia el
estado del gate y no ejecuta código o pruebas.

Marco aplicado:

- `docs/PLAN_MAESTRO_CIERRE_TALOS.md`, “Formalizar identidad y aislamiento
  curricular (ESTAB-G2 / Gate B)” y su mapa CP073.
- `checkpoints/073-mapa-maestro-talOS-y-camino-restante.md`.
- `checkpoints/074-criterios-objetivos-product-complete.md` — éste es el nombre
  real del checkpoint 074; no existe un archivo llamado
  `074-criterios-product-complete.md`.
- `docs/DIAGNOSTICO_MULTICUADERNO_Y_PLAN_DE_CONTINUIDAD.md`, H1–H3 y “Gate B —
  Aceptar el aislamiento de perfiles por cuaderno”.
- Pruebas y configuración citadas individualmente en §3.

No se volvió a inspeccionar SQLite/corpus ni se reabrió la arqueología Gate 2.
La documentación del diagnóstico comunica resultados focalizados del
2026-09-29; esta tarea no los repitió.

Clasificaciones:

- `PASS_EXISTING_EVIDENCE`: el criterio completo está demostrado para el
  scope de release explícito, no sólo para una fixture aislada.
- `PARTIAL_EXISTING_EVIDENCE`: evidencia válida cubre una parte acotada, pero
  queda un gap explícito de alcance, registros, identidad o generalización.
- `NOT_DEMONSTRATED`: no se encontró evidencia que demuestre el criterio.
- `BLOCKED`: falta una decisión, autoridad o prerequisito sin el cual no se
  puede cerrar correctamente.
- `NOT_APPLICABLE`: el criterio no aplica a un scope de release explícitamente
  definido que lo excluye.

## 2. Alcance de release y scope de `fadena-std`

Las fuentes actuales presentan configuraciones para Fase 0/programación,
Lenguajes, Sistemas Operativos II, Tratamiento de Datos y Telecomunicaciones.
`config/notebook_kc_catalog.json`, `config/notebook_source_roles.json`,
`src/study_engine/pedagogy/fase0_seed.py` y la matriz de perfiles de las
pruebas contienen esos perfiles. La documentación multi-cuaderno también
trata `fadena-std` como perfil candidato/canónico y describe un recorrido
integrado aislado para ese scope.

Sin embargo, no se encontró una decisión de release que enumere de forma
cerrada los currículos que se aceptarán como producto completo. Por ello:

```text
RELEASE_SCOPE = NOT_FORMALLY_FIXED
FADENA_STD_IN_CURRENT_CONFIGURED_PROFILE_SET = YES
FADENA_STD_IN_CONFIRMED_RELEASE_SCOPE = UNDETERMINED
```

El criterio 5 no se puede marcar `NOT_APPLICABLE`: no hay una decisión que
excluya `fadena-std`. Tampoco se lo considera aprobado sólo porque exista una
entrada de configuración. Se evalúa como condicionalmente aplicable y
bloqueado hasta fijar el scope y, si se incluye, respaldar su autoridad
curricular.

## 3. Matriz criterio por criterio

### Criterio 1 — IDs canónicos, aliases y `curriculum_id`

**Afirmación evaluada:** para cada currículo del release existe una identidad
canónica reconciliada, un conjunto explícito de aliases (incluida la ausencia
de aliases cuando corresponde) y un `curriculum_id` coherente entre catálogo,
registro/registry y datos persistidos.

**Clasificación: `PARTIAL_EXISTING_EVIDENCE`**

| Dimensión | Evaluación |
|---|---|
| Evidencia concreta | `tests/pedagogy/test_socratic_system_prompt.py` verifica cinco pares perfil-ID/`curriculum_id`, comparación con `config/notebook_kc_catalog.json`, IDs parecidos desconocidos en fallback neutral y mismatch neutral. `tests/pedagogy/test_pedagogical_contract_persistence.py::test_default_curriculum_profile_requires_exact_persisted_identity` prueba la identidad persistida exacta y el fallback tras alterar `curriculum_id`. `config/notebook_identity_decisions.json` declara decisiones de auditoría por identidad y `alias_target: null`, y explícitamente indica que no da acceso a fuentes ni controla autorización runtime. `src/study_engine/diagnostics/notebook_reconciliation.py` compara catálogo, registry y estado persistido; `tests/unit/diagnostics/test_notebook_reconciliation.py` verifica mismatch y falta de alias sin escribir. |
| Tipo de evidencia | Test unitario; fixture/almacén temporal; test de reconciliación con DB sintética; configuración y documentación estáticas. |
| Cobertura real | El mecanismo de coincidencia exacta, el fallback de identidad desconocida y el reporte de discrepancias están cubiertos. Cinco perfiles de configuración tienen IDs/`curriculum_id` comprobados frente al catálogo. Se documenta que los scopes legacy no se convierten automáticamente en alias. |
| Sin demostrar | No hay en esta evidencia una reconciliación aprobada de las identidades efectivas para todos los currículos del eventual release. La prueba de reconciliación usa notebook, catálogo, roles y DB sintéticos; no verifica la concordancia de los registros activos. El mapeo de aliases de auditoría es `null`, no una aprobación de que todas las identidades históricas estén reconciliadas. El release scope aún no está enumerado. |
| ¿Requiere ejecución futura? | Sí: evaluación read-only del catálogo, DEFAULT_NOTEBOOKS/registry, source-role config e identidades persistidas para cada scope que se declare. Repetir las pruebas focalizadas puede producir evidencia fechada del snapshot evaluado, pero no reemplaza el cotejo de los datos efectivos. |
| ¿Puede cerrarse sin modificar código? | Sí, si las fuentes efectivas concuerdan y las decisiones de alias/scope se documentan; no hay un bug de matching demostrado por la evidencia existente. Si el cotejo revela discrepancias, su resolución requiere decisión separada y no está autorizada por esta evaluación. |
| Dependencia para cierre | Decisión explícita del conjunto de currículos de release y reconciliación read-only de cada identidad/alias/`curriculum_id` efectivo. |

### Criterio 2 — Roles de fuente y ACL efectiva

**Afirmación evaluada:** los roles declarados de cada fuente (por ejemplo,
PRIMARY/COMPLEMENTARY u otros roles existentes) son consistentes con las
asociaciones efectivas del notebook, y la ACL aplicada a retrieval/prompt
permite sólo fuentes autorizadas para el scope.

**Clasificación: `PARTIAL_EXISTING_EVIDENCE`**

| Dimensión | Evaluación |
|---|---|
| Evidencia concreta | `config/notebook_source_roles.json` contiene roles declarativos por notebook/fuente. `tests/unit/web/test_retrieval_scope_allowlist.py` verifica, con SQLite in-memory, la intersección de solicitudes de fuentes/IDs/hash con la allowlist del scope, incluido el caso vacío/desconocido. `tests/pedagogy/test_chat_sse_endpoint.py::test_chat_sse_retrieves_only_sources_authorized_for_notebook_scope` integra endpoint, retrieval del KnowledgeStore temporal y backend capturador: ofrece target y fuente extranjera, y verifica que sólo la fuente asociada al notebook llegue a evidencia/prompt. `tests/storage/test_notebook_isolation.py` prueba aislamiento de fuentes/documentos/chunks entre dos notebooks sintéticos. `src/study_engine/diagnostics/notebook_reconciliation.py` enumera discrepancias entre roles, fuentes declaradas y asociaciones; la prueba correspondiente usa entradas sintéticas y demuestra que el reporte no escribe. |
| Tipo de evidencia | Configuración estática; tests unitarios; fixtures SQLite temporales; integración HTTP/SSE sintética con backend fake y retrieval de fixture. |
| Cobertura real | La lógica de filtrado por notebook/source y un recorrido completo de un caso `fadena-std` prueban que una fuente extranjera ofrecida en `active_sources` no se incorpora si no está asociada al scope. Se prueba también aislamiento básico de storage entre dos notebooks creados para el test. |
| Sin demostrar | No está validada la concordancia entre roles declarados, fuentes existentes y asociaciones efectivas para todos los notebooks/sources del release. La documentación Gate B dice expresamente que la integración usa fixtures temporales, no ACL/registros productivos, y que el caso integrado es sólo `fadena-std`. Que haya roles en configuración no demuestra por sí solo su correspondencia con el estado efectivo ni la autoridad del contenido. |
| ¿Requiere ejecución futura? | Sí: cotejo read-only por scope de source-role declarations, registry, source records y asociaciones efectivas; luego pruebas de aislamiento por cada currículo incluido que cubran fuente autorizada y fuente no autorizada hasta el prompt. No se requiere ejecutar corpus/modelos productivos. |
| ¿Puede cerrarse sin modificar código? | Sí, si el cotejo efectivo está alineado y las pruebas existentes cubren todos los scopes declarados; cualquier ACL/migración debe quedar fuera hasta tener decisión y autorización propias. |
| Dependencia para cierre | Scope de release definido; inventario/reconciliación read-only de roles y asociaciones; ninguna expansión de ACL inferida por nombre o similitud curricular. |

### Criterio 3 — Selección de prompt/perfil por identidad explícita

**Afirmación evaluada:** el perfil de prompt se selecciona sólo si coinciden
el ID explícito del notebook y su `curriculum_id`; IDs desconocidos, parecidos
o con mismatch reciben un perfil neutral. El prompt final no mezcla
representaciones específicas de otro currículo.

**Clasificación: `PARTIAL_EXISTING_EVIDENCE`**

| Dimensión | Evaluación |
|---|---|
| Evidencia concreta | `src/study_engine/pedagogy/fase0_seed.py::get_system_prompt_for_notebook` busca por ID exacto y compara `curriculum_id`; si no coincide, usa `TALOS_BASE_SYSTEM_PROMPT`. `tests/pedagogy/test_socratic_system_prompt.py` comprueba los cinco perfiles configurados, exclusión de pistas ajenas, `fadena-std` mismatch y tres IDs parecidos/vacíos. `tests/pedagogy/test_chat_sse_endpoint.py::test_chat_sse_sends_only_the_exact_curriculum_profile_to_backend` recorre `/api/chat/query` para los cinco perfiles configurados más un ID desconocido con backend capturador. `docs/DIAGNOSTICO_MULTICUADERNO_Y_PLAN_DE_CONTINUIDAD.md` informa que la corrida focalizada histórica pasó sus casos y aclara que el paquete de evidencia usado era simulado. |
| Tipo de evidencia | Código estático; tests unitarios; configuración/casos parametrizados; integración HTTP/SSE sintética con evidence fake y backend fake. |
| Cobertura real | La regla de identidad exacta/mismatch neutral está demostrada para los perfiles codificados; la prueba endpoint observa el prompt que recibe el fake backend y muestra un solo perfil, o fallback neutral para ID desconocido, en los seis casos parametrizados. |
| Sin demostrar | No se demuestra que todos los registros efectivos del release suministren el ID/`curriculum_id` esperado ni que el perfil escogido coincida con fuentes/ACL reales. Tampoco se demuestra la respuesta semántica de un proveedor real. El scope de release está pendiente; los cinco perfiles de configuración no equivalen automáticamente a cinco perfiles aceptados para lanzamiento. |
| ¿Requiere ejecución futura? | Sí: validación fechada de los casos parametrizados/integración dentro de la regresión aceptada y cruce con identidad efectiva de cada scope. La prueba de proveedor real no es necesaria para probar selección determinista de perfil; sólo sería necesaria para claims sobre obediencia semántica de modelo real. |
| ¿Puede cerrarse sin modificar código? | Probablemente sí para la regla determinista de selección, una vez fijado scope y verificados registros efectivos. La evidencia actual no señala un defecto de implementación en esa regla. |
| Dependencia para cierre | Criterio 1 reconciliado para los scopes declarados y prompt/perfil verificado en el flujo aceptado; separar “selección correcta” de “modelo obedece”. |

### Criterio 4 — Ausencia de contaminación entre currículos

**Afirmación evaluada:** en los currículos incluidos, contexto, perfil,
fuentes/ACL y prompt de un scope no incorporan contenido o perfil de otro
currículo, salvo asociación explícita autorizada.

**Clasificación: `PARTIAL_EXISTING_EVIDENCE`**

| Dimensión | Evaluación |
|---|---|
| Evidencia concreta | `tests/storage/test_notebook_isolation.py` verifica dos notebooks sintéticos con fuentes distintas, cero resultados cruzados y sharing sólo después de asociación explícita. `tests/unit/web/test_global_scope.py` verifica retrieval de carpeta limitado a notebooks descendientes y asociaciones explícitas. `tests/adversarial/crisol_chaos/test_14_cross_notebook_isolation.py` verifica separación de memoria histórica sintética por notebook. `tests/pedagogy/test_chat_sse_endpoint.py::test_chat_sse_retrieves_only_sources_authorized_for_notebook_scope` verifica una ruta completa aislada de fuente permitida y fuente extranjera para `fadena-std`. `test_chat_sse_sends_only_the_exact_curriculum_profile_to_backend` prueba que el prompt no incorpora perfiles curriculares vecinos en los casos configurados. |
| Tipo de evidencia | Tests unitarios/contract/adversariales; stores y datos fixture; integración sintética de endpoint/retrieval/prompt. |
| Cobertura real | Hay evidencia de aislamiento de storage, retrieval, memoria y perfiles en casos escogidos; también hay un caso de alcance carpeta y un caso end-to-end sintético de ACL hasta prompt. |
| Sin demostrar | No hay matriz aceptada que cubra conjuntamente identidad→ACL→retrieval→prompt para cada currículo efectivo del release. No hay ejecución con registros/fuentes productivas, y las fixtures no permiten inferir ausencia de contaminación en todos los notebooks, fuentes, aliases, asociaciones M:N, ACL o rutas alternativas. El plan multi-cuaderno marca expresamente esta aceptación como pendiente. |
| ¿Requiere ejecución futura? | Sí: matriz por cada scope explícito con casos positivos, negativos/cross-scope y asociaciones compartidas sólo cuando estén declaradas; capturar en el límite del prompt las fuentes y el perfil recibidos. Mantener stores/corpus sintéticos o fixtures aislados. |
| ¿Puede cerrarse sin modificar código? | Sí, si el conjunto de casos y la inspección efectiva confirman que los mecanismos ya probados bastan. Si aparece contaminación real, será un hallazgo que requerirá una decisión/cambio posterior; no se corrige aquí. |
| Dependencia para cierre | Scope de release cerrado y criterios 1–3 reconciliados; definición de sharing explícito para cada caso multi-notebook. |

### Criterio 5 — Autoridad curricular de `fadena-std`

**Afirmación evaluada:** sólo si `fadena-std` entra en el scope de release,
su perfil/identidad se apoya en una fuente curricular oficial autorizada para
el programa detallado, y no sólo en nombres/KCs locales.

**Clasificación: `BLOCKED` (aplicabilidad al release pendiente)**

| Dimensión | Evaluación |
|---|---|
| Evidencia concreta | `src/study_engine/pedagogy/fase0_seed.py` define el perfil local `Sistema de Tratamiento de Datos` con `fadena_std_2026`. `config/notebook_kc_catalog.json` contiene ese `curriculum_id` y KCs con `contextual_status` que dice “Programa Oficial (Pereira/Chamudis/Maidana)”. `config/notebook_identity_decisions.json` lo clasifica como candidato canónico e indica que existe material bajo `fuentes/fadena-std`, pero también dice que el programa académico y referencias de fuentes faltantes aún requieren validación. El diagnóstico multi-cuaderno §H2 y §Gate B afirma que la etiqueta fue corregida, pero requiere la fuente curricular oficial para respaldar el programa detallado. |
| Tipo de evidencia | Configuración y documentación estáticas; referencias a material local no inspeccionado en esta tarea. No se aporta aquí verificación documental primaria del programa oficial. |
| Cobertura real | Está demostrada la existencia del identificador/perfil en la configuración local y una corrección del rótulo del perfil. No está demostrada la autoridad de la designación curricular por la sola metadata `contextual_status`. |
| Sin demostrar | No hay decisión final de si `fadena-std` pertenece al scope de release. Si se incluye, falta la referencia oficial verificable y el vínculo entre esa fuente, el programa detallado, `curriculum_id`, fuentes autorizadas y el perfil. Si se excluye, la exclusión debe ser explícita en el scope de release; no se infiere de la falta de evidencia. |
| ¿Requiere ejecución futura? | La autoridad requiere localizar/verificar una fuente documental curricular autorizada, no ejecutar TALOS. La clasificación de aplicación requiere primero la decisión del scope. Ninguna fuente PDF fue abierta en esta evaluación. |
| ¿Puede cerrarse sin modificar código? | Sí si el scope excluye expresamente `fadena-std`; o, si se incluye, si la fuente autorizada respalda la identidad y los registros/perfil coinciden. Cualquier discrepancia de perfil/ACL queda para decisión separada. |
| Dependencia para cierre | Decisión de release scope. Si se incluye: fuente curricular oficial verificable y reconciliación de su identidad, `curriculum_id`, materiales y roles/ACL. |

## 4. Conclusión del estado Gate B

```text
GATE_B_STATUS = PARTIAL_EXISTING_EVIDENCE
CRITERIA:
  1 IDs / aliases / curriculum_id = PARTIAL_EXISTING_EVIDENCE
  2 source roles / effective ACL = PARTIAL_EXISTING_EVIDENCE
  3 explicit identity → profile / prompt = PARTIAL_EXISTING_EVIDENCE
  4 cross-curriculum isolation = PARTIAL_EXISTING_EVIDENCE
  5 fadena-std authority = BLOCKED (conditional on unresolved release scope)
PRODUCT_SCOPE = NOT_FORMALLY_FIXED
```

Los criterios 1, 3 y partes de 2 y 4 tienen evidencia real de comportamiento
acotado: pruebas unitarias, stores sintéticos y una integración endpoint con
retrieval fixture/fake backend. No están demostrados para todos los registros
efectivos ni para el conjunto completo de currículos de un release. La
evidencia no es meramente estática, pero su mayor alcance es fixture/
integración sintética; no hay runtime real de proveedor ni base productiva
evaluados aquí.

Por tanto, la fracción **demostrada hoy** es:

- regla exacta perfil-ID/`curriculum_id` y fallback neutral para los perfiles
  configurados, dentro de tests locales/fakes;
- exclusión de una fuente extranjera en un scope `fadena-std` de fixture,
  desde asociación/allowlist hasta contexto/prompt;
- aislamiento sintético de storage, retrieval de carpetas, memoria y perfil
  en varios casos separados.

La fracción no demostrada que impide cerrar Gate B es:

1. scope finito de release con lista de currículos y decisión sobre
   `fadena-std`;
2. reconciliación read-only de cada ID/alias/`curriculum_id` efectivo contra
   catálogo, registry, configuración de roles y asociaciones;
3. roles/ACL efectivos y existencia/procedencia de fuentes por currículo,
   correlacionados con lo que llega al prompt;
4. matriz de positivos/negativos de no-contaminación a través del camino
   integrado para cada currículo incluido;
5. si `fadena-std` se incluye, autoridad curricular verificable para el
   programa detallado y su relación con el perfil/fuentes.

Los gaps descritos son principalmente de definición de scope, reconciliación
de evidencia y cobertura; la evidencia existente no demuestra que se necesite
modificar código. Si la evaluación read-only encuentra discrepancias, deben
quedar reportadas para una decisión separada, no repararse por inferencia.

## 5. Evidencia mínima/ejecución futura para cerrar Gate B

En el orden mínimo:

1. **Fijar scope de release:** decisión explícita con los currículos incluidos.
   Registrar si `fadena-std` está incluido o excluido. No usar la existencia
   de configuración como sustituto de esta decisión.
2. **Reconciliar identidad sin escribir:** para cada notebook incluido,
   cotejar ID canónico, aliases explícitos/no-alias, `curriculum_id`,
   catalog entry, registry y registro persistido. Emitir discrepancias y
   procedencia; no modificar la base/ACL durante la auditoría.
3. **Reconciliar roles/ACL efectivas:** para cada scope y fuente, comparar
   roles declarados, registro de source, asociación efectiva y fuentes
   finalmente seleccionables. Registrar hashes/identidad de configuración y
   de los datos examinados. Mantener el diagnóstico en read-only.
4. **Ejecutar validación sintética focalizada ya existente:** repetir, bajo
   autorización futura, el test de identidad/perfil para todos los IDs
   incluidos y el flujo endpoint/retrieval/prompt con fuentes autorizadas y
   extranjeras. Añadir escenarios sólo si la matriz revelara una dimensión del
   contrato CP074 que la cobertura existente no toque. Proveedor real no es
   requerido para la selección determinista ni para las fixtures aisladas.
5. **Cerrar no-contaminación para el scope:** por cada currículo incluido,
   documentar casos positivos/negativos de fuentes y perfil y verificar el
   límite del prompt; para asociación compartida, demostrar vínculo explícito
   y que no se extienda a scopes no asociados.
6. **Resolver autoridad de `fadena-std`, sólo si está incluido:** referencia
   curricular oficial verificable y decisión que la vincule al nombre,
   programa, año, `curriculum_id` y fuentes/roles pertinentes. Si no se
   obtiene, no declarar ese currículo aceptado; excluirlo sólo mediante
   decisión explícita de scope.
7. **Registrar el resultado del gate:** cada criterio con evidencia,
   limitación, fuente/artefacto/hash y resultado. Gate B puede cerrarse sin
   modificar código si las verificaciones confirman que el comportamiento y
   datos efectivos ya satisfacen los criterios. Cualquier cambio de datos o
   código requiere gate/decisión aparte.

Los pasos 2–5 necesitan una futura inspección/ejecución focalizada y
autorizada según sus recursos, pero no autorizan ejecutar TALOS/FastAPI en su
lifecycle normal, consultar proveedor real ni modificar DB/corpus/ACL.

## 6. Invariantes y no-acciones

- No se ejecutaron tests ni se usaron runtimes para esta evaluación.
- No se modificaron código, configuraciones, DB, corpus, modelos, índices,
  gates ni artefactos A-PRE.
- No se reabrió CP072.
- A-PRE/authority permanecen exactamente según §1; este checkpoint no afecta
  `PRODUCT_COMPLETE` ni declara TALOS completo.
- Las fixtures existentes se conservan como evidencia acotada; no se
  generalizan a todos los currículos, fuentes o entornos.
