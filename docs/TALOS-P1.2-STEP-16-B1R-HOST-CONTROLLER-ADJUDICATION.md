# TALOS-P1.2-STEP-16 — ADJUDICACIÓN DEL CONTRATO DE B1-R Y DEL CONTROLADOR HOST

**Entrada:** `A1_COVERAGE_PARTIAL`  
**Estado canónico:** `P1.2 = BLOCKED-REGRESSION`  
**Tipo:** análisis contractual y estático, sin implementación ni pruebas  
**Salida:** `B1R_HOST_CONTRACT_PARTIAL`

## 1. Estado del repositorio

- Rama observada: `talos-current-audit`.
- HEAD observado: `cc8acfae623f9d10c8366871470319786b6a7ca4`.
- Worktree al inicio: 1.863 paths con cambios en el índice, 23 con cambios en el worktree y 66 paths untracked según `git status --porcelain=v1`. Se preservaron todos; los conteos no atribuyen autoría.
- `docs/TALOS-P1.2-STEP-16-B1R-HOST-CONTROLLER-ADJUDICATION.md` no existía antes de esta fase.
- El único archivo creado es este expediente. No se modificaron código, tests, configuración ni expedientes anteriores.

## 2. Fuentes inspeccionadas

- `tests/audit/test_b1_route_repeatability.py:14-16,30-125,128-207,303-417,561-606,678-679`: contrato/casos, test controlador, consulta Git, lanzamiento de worker, guards, repeticiones y escritura del reporte.
- `tests/audit/b1r_contract.json:1-120`: repeticiones, casos esperados, probes y contadores.
- `scripts/verify_b1r_artifact.py:13-167,169-273`: verificaciones del artefacto, códigos de salida y envelope.
- `scripts/quality_gate.py:1013-1044,1218-1230,1473-1602,1630-1685,1788-1885,2025-2034`: selección por perímetro, launch Bubblewrap, workspace host/guest, evidencia de inicio y entrada al worker.
- `scripts/quality_gate_isolation.py:63-101,213-307,309-352,365-430`: validación de roots, mapeo, separación `/tmp`, mounts y máscaras.
- `config/test_perimeter.json:1-3,134-138`: clasificación de `tests/audit` y `tests/unit` como `required`.
- `docs/TALOS-P1.2-STEP-13-STATIC-NESTED-WORKSPACE-ADJUDICATION.md:27-76,98-126,142-173`.
- `docs/TALOS-P1.2-STEP-14-HARNESS-ISOLATION-CONTRACT-DESIGN.md:24-72,74-96,115-172`.
- `docs/TALOS-P1.2-STEP-15-ARCHITECTURE-COVERAGE-ADJUDICATION.md:20-54,86-143`.

La lectura es estática. No se afirma que el test, el Quality Gate o Bubblewrap funcionen en ejecución.

## 3. Adjudicación de alternativas del controlador host

Las alternativas se evalúan respecto al código observado y a los invariantes del contrato. Una alternativa descrita conceptualmente no es una capacidad existente ni una autorización para implementarla.

| Alternativa | Código de checkout con visibilidad host | Quién crea/elige workspace | Operaciones host solicitables por worker | Identidad de rutas | Salida, errores y artefactos | Riesgo residual | Evidencia y estado |
|---|---|---|---|---|---|---|---|
| **H1 — Código de test en host** | Pytest importa/ejecuta los módulos de test desde el checkout en el proceso host; fixtures, plugins y helpers de esos tests también corren con la identidad/permisos de ese proceso. Ejecutar desde un test no reduce autoridad. | El propio test puede crear rutas desde `tmp_path`; ese hecho no convierte automáticamente cada ruta o argumento en una raíz autorizada. | Si el test llama `subprocess`, filesystem o API del runner, el código puede solicitar/ejecutar esas operaciones con las capacidades host que tenga el proceso. No hay broker limitador implícito. | Path visible para pytest host; aun así, cada root writable/mount necesita validación canónica host, autorización y scope. No se aceptan strings guest. | Pytest ve excepciones y código del subprocess; artefactos quedan donde el test/harness los escribió. No existe en sí una separación tipada entre error del harness, resultado del worker y evidencia de aislamiento. | Ejecución arbitraria de código del checkout con visibilidad host; riesgo de side effects y de atribuir confianza por procedencia del archivo. Puede omitir Bubblewrap si no se exige el launch real. | El test B1-R contiene código extenso ejecutable (`test_b1_route_repeatability.py:128-606`), y el test llama procesos directamente (`:58-94`). Ningún contrato declara “test del repo = código confiable host”. **`INCOMPATIBLE` como autorización implícita o modalidad general.** Una ejecución host estrictamente allowlisted necesitaría otra adjudicación. |
| **H2 — Harness host limitado** | Solo el harness/launcher host aprobado ejecuta en host la preparación y validación; el worker y su carga funcional corren dentro de Bubblewrap. No ejecutar el código de test completo en host como autoridad general. | Harness host crea un workspace nuevo bajo `/tmp`, asigna un ID/run y conserva ownership. Worker no escoge root ni entrega un path host arbitrario; como máximo expresa una operación/fixture dentro de una interfaz allowlisted. | Solo operaciones finitas autorizadas, por ejemplo seleccionar un perfil/nodeid preaprobado, lanzar un comando fijado por política con argumentos de datos validados, recuperar outputs relativos a un workspace y leer estado Git a través del observador host. Nunca shell/command/paths arbitrarios del worker. | El host resuelve/canoniza roots y valida symlinks, contención, checkout, destino guest y run-id antes de mount. Los paths guest son relativos al mount declarado; no hay traducción guest→host por prefijo/fallback. | El harness registra por separado preparación/validación, spawn/timeout/exit code, stdout/stderr truncados/limitados según política, outputs allowlisted y observación Git. Fallos de validación, broker o Git son error/blocked/unknown, nunca pass. | La API host puede ser confused deputy si un worker la usa para solicitar comandos, montajes o recursos de mayor autoridad. Exige identidad/autorización del caller, allowlist, límites de recursos, prevención de replay y auditoría. | El runner actual ya prepara workspace bajo host `/tmp` y lanza Bubblewrap con checkout RO, workspace limitado y `/tmp` guest tmpfs (`quality_gate.py:1473-1602`; `quality_gate_isolation.py:290-307`). No se encontró una interfaz de request limitada del worker al host, autorización de requests o integración para ejecutar controllers B1-R. **`UNRESOLVED` como arquitectura integrada; viable solo con contrato y autoridad host explícitos.** |
| **H3 — Harness dedicado** | Un harness/profile host dedicado ejecuta el controlador confiable mínimo; la prueba funcional permanece en worker. La identidad del código y del runner dedicado se registra y no se asume confianza por el hecho de ser test. | El harness dedicado crea/posee el workspace host; cada worker recibe solo los mounts explícitos asociados a un run. | Operaciones definidas por el contrato del perfil; worker no adquiere interfaz general del host. Si no necesita solicitar launch, el host puede hacer toda la orquestación. | Manifiesto de ejecución enumera identidad exacta de nodeid, perfil, inputs, root host generada y mountpoint guest. El host valida; outputs guest son recogidos solo desde mounts autorizados. | Reporte dedicado distingue controlador, child, pruebas/assertions, exit codes, artifacts, aislamiento y Git; el agregador del Quality Gate consume cada resultado con su origen. | Divergencia de política respecto del gate normal; duplicación de selección/perímetro; riesgo de nodeid requerido ausente del agregador o que un resultado de helper se confunda con prueba del worker. | El perímetro actual registra suites por directorio y `run_gate()` corre pytest dentro del worker (`config/test_perimeter.json:1-3,134-138`; `quality_gate.py:1013-1044`). No hay perfil host-controller ni contrato de agregación de esa clase demostrado. **`UNRESOLVED` hasta definir selección, resultados y cobertura exacta.** |

H1 queda rechazada como supuesto implícito de seguridad. H2 es el límite contractual más estrecho que podría responder a requests de lanzamiento, pero no existe en el código inspeccionado un canal/protocolo limitado; H3 podría aislar y contabilizar esa función con perfil propio, pero la relación con el gate actual está pendiente. No se selecciona ni autoriza ninguna alternativa.

## 4. B1-R: propiedades, observador y límites

`test_synthetic_chat_route_is_repeatable_and_sterile` crea `cwd`, `home` y `tmp` bajo `tmp_path`, toma estado Git inicial, ejecuta el mismo archivo con `--worker`, valida el reporte con un proceso verificador separado y compara el estado Git al final.

| Propiedad | Evidencia estática exacta | Proceso/autoridad que puede observarla | Assertions que deben conservarse | Límite de la evidencia actual |
|---|---|---|---|---|
| **Repetibilidad de tres ejecuciones** | `REPETITIONS = 3`, diez casos en `CASES` (`test_b1_route_repeatability.py:14-27`); `run_all_cases()` itera cada caso tres veces (`:574-580`); el reporte contiene `case_count`, repeticiones y observaciones (`:582-601`). `verify_artifact()` comprueba cantidad exacta y normaliza/compara observaciones (`verify_b1r_artifact.py:45-117`). | Worker funcional produce observaciones; verificador independiente valida consistencia/cantidad. El código que comprueba las observaciones no requiere leer `.git`. | Diez IDs exactos, tres observaciones por caso, campos esperados y equality entre runs normalizados. Mantener salida no cero cuando falte/cambie un resultado. | La comparación es de observaciones registradas, no una prueba de aislamiento del proceso ni de ausencia de side effects invisibles. No se ejecutó. |
| **Resultado funcional del subprocess** | `subprocess.run([... "--worker", repo_root, report_path], capture_output=True, check=False, timeout=120)` (`test_b1_route_repeatability.py:58-73`) y `assert completed.returncode == 0` (`:74-78`). Worker invoca `asyncio.run(run_all_cases())` y escribe JSON (`:582-606`). | Proceso controlador observa return code/stdout/stderr; proceso worker produce reporte. | Return code cero y diagnóstico stdout/stderr en fallo. Timeout o excepción deben fallar explícitamente. | Es `subprocess.run()` directo, no `run_isolated_process()`/Bubblewrap. El worker tiene audit hooks Python y guards internos, no queda demostrado como proceso OS aislado. |
| **Existencia y validación del artefacto** | `report_path.is_file()` (`:79`); el verificador recibe contract/report como argumentos (`:80-94`), debe terminar cero (`:95-101`) y stdout JSON debe ser exactamente `{"status":"TECHNICAL PASS","findings":[]}` (`:102-105`). Verifier revisa envelope/hash, casos, repeticiones, probes, counters y campos (`verify_b1r_artifact.py:13-166,207-273`). | Worker escribe bajo `tmp_path`; test/controller y verifier leen el artefacto. El controller controla el path de salida. | Mantener existencia, error/código de verifier y status/findings exactos. No aceptar reporte inválido o incompleto. | El status “TECHNICAL PASS” solo significa que el artefacto satisface el contrato mecánico que verifica; no es verdad general, gate result ni aislamiento demostrado. |
| **Git antes/después** | Captura `_git_status(repo_root)` antes (`:56`), compara igualdad después (`:106-108`). `_git_status()` usa `git -C <repo> status --porcelain --untracked-files=all`, captura salida y `check=True` (`:111-125`). | Requiere un observador que pueda leer el `.git` real y el checkout del host evaluado. No puede delegarse al worker actual si `.git` está enmascarado. | Preservar baseline/final del mismo checkout; estado dirty inicial se compara sin limpiar; incluir untracked. Diferencia implica assertion fail. Error del comando propaga `CalledProcessError` y falla la prueba; no se transforma en “sin cambios”. | Es comparación de estados en dos instantes. No prueba que no hubo una escritura temporal luego revertida, ni detecta cualquier side effect externo. Tampoco demuestra quién hizo un cambio concurrente entre capturas. |
| **Errores de observación Git** | `subprocess.run(... check=True)` deja que fallos del comando/ejecución propaguen; no hay catch con fallback (`:111-125`). | Observador host autorizado. Si Git no está disponible, checkout no tiene `.git` visible, o el comando falla, el test/harness debe quedar error/blocked. | No reemplazar excepción por status vacío, skip, pass o igualdad artificial. Reportar el error del observador aparte del worker. | En el Quality Gate el `.git` está enmascarado al worker según STEP-13 y `quality_gate_isolation.py:399-426`; ejecutar `_git_status()` allí no proporciona acceso autoritativo al checkout. |
| **Aislamiento/permisos del proceso funcional** | Worker instala `sys.addaudithook(_audit)` y guards para archivos protegidos/escritura al repo, sqlite, red, subprocesses, threads, providers y startup (`test_b1_route_repeatability.py:128-207,303-417`); usa `TMPDIR` privado (`:45-54,303-310`); tests route internos son ASGITransport en proceso (`:423-459`). El driver, sin embargo, lo lanza mediante `subprocess.run()` ordinario (`:58-73`). | Audit hooks y test funcional operan dentro del proceso Python. Bubblewrap, si se usara, debe ser lanzado/observado por el harness con autoridad de crear y validar mounts. | Mantener todos los guard probes/rechazos, contadores cero y límites funcionales. Aislamiento OS, mounts, namespaces y permisos deben tener evidencia propia; no inferirlos de los hooks. | El source no llama Bubblewrap ni verifica namespace/mount/permisos OS. A-PRE/audit hook no equivale a aislamiento del proceso. Un subprocess ordinario no puede presentarse como worker Bubblewrap. |

### 4.1. Contrato para conservar B1-R

Separar y correlacionar cuatro records, sin sustituir uno por otro:

```text
RUN_ID / NODEID / checkout identity / policy identity
  ├── FUNCTIONAL_WORKER_RESULT
  │     return code, timeout/error, stdout/stderr y ruta/identidad del reporte
  ├── ARTIFACT_VERIFICATION
  │     contract hash, verifier exit code, status y findings
  ├── ISOLATION_OBSERVATION
  │     mecanismo invocado, identidad de mounts/namespaces observados,
  │     resultado/limitaciones de assertions de boundary
  └── HOST_GIT_OBSERVATION
        status inicial/final del mismo checkout, exit codes y comparación
```

- La observación Git la ejecuta el harness host autorizado en el checkout host identificado para el run, no el worker.
- La captura Git debe conservar stdout exacto/resultado comparable, código de salida, stderr de error, identidad del checkout, alcance (`--untracked-files=all`) y run-id. Si no se puede observar, registrar fallo/blocked/unknown.
- Una igualdad Git satisfecha no demuestra ausencia de acceso, ausencia de escrituras transitorias ni aislamiento; el worker exitoso no demuestra Git limpio; ambos tampoco demuestran que Bubblewrap limitó el proceso.
- Si B1-R requiere que el proceso funcional opere bajo un boundary OS, el harness debe lanzar el worker real con Bubblewrap y mantener `.git` oculto. La autoridad host que consulta Git permanece fuera de ese worker.
- STEP-16 no cambia el test ni decide si el subprocess funcional actual debe transformarse, envolverse o conservarse como propiedad distinta.

## 5. Contrato de cobertura del Quality Gate

Para ejecutar un controlador fuera del worker estándar sin disminuir la cobertura, un contrato futuro tendría que registrar y verificar al menos:

1. **Identidad exacta:** nodeid canónico completo, hash/identidad del archivo y run-id; la selección host-side debe ser allowlisted y rechazar cero, múltiples o distintos nodeids si se espera exactamente uno.
2. **Clasificación vigente:** derivar `required`/`qualification-required` del perímetro canónico. Un test `required` no puede desaparecer del worker sin que el reporte lo registre como ejecutado por el perfil host-controller. `qualification-required` conserva su gate de release, no se promueve silenciosamente a required ni se omite.
3. **Relación controller/child:** identificar controller test, comando hijo permitido, padre/hijo, argv normalizado, workspace/run, timeout y conexión entre resultado funcional y assertions del controller. Ejecutar controlador no significa ejecutar el nodeid hijo como otro test.
4. **Workspace/mount identity:** workspace host creado por el harness bajo `/tmp`; root canónica validada en host; punto guest explícito; checkout read-only, `.git` y raíces protegidas enmascaradas, `/tmp` guest separado. El worker no puede pedir paths/commands arbitrarios.
5. **Resultados y errores:** códigos de salida separados para pytest controlador, worker Bubblewrap, pytest hijo y verifier; distinguir timeout, error de preparación, error de validación, test fail y bloqueo de aislamiento. Ninguno se convierte en cero por fallback.
6. **Artefactos:** solo outputs esperados y relativos a mounts autorizados; registrar identidad/hash/tamaño y resultado del verifier. Rechazar symlink/path traversal, artefacto ausente, extra o ambiguo según contrato. No aceptar el artefacto del worker como evidencia del host.
7. **Agregación:** reporte del gate enumera cada nodeid y origen de ejecución, clasificaciones, resultado y evidencia; `required` debe satisfacer su política exactamente una vez según regla explícita. Faltantes, duplicados o perfiles no aplicables mantienen gate bloqueado/unknown.
8. **Separación epistemológica:** `TEST_PASS` del worker, `ISOLATION_OBSERVATION`, `HOST_GIT_OBSERVATION` y `ARTIFACT_VERIFICATION` son dimensiones distintas; la agregación no deriva aislamiento desde pass funcional ni gate pass desde status Git.
9. **Autoridad del controlador:** código host ejecutable, APIs, privilegios, entorno, inputs, red, filesystem, comandos y dependencias quedan definidos por una política explícita y estrecha. La pertenencia al repositorio no es la validación de confianza.

El `test_perimeter.json` actual clasifica suites/directorios, y `run_gate()` selecciona esos directorios y los corre en pytest dentro del sandbox worker. No se encontró evidencia de una tabla host-controller, resultados por nodo host-side o agregador que contabilice una clase de launch anidado. Cambiar esta arquitectura sin registro de cobertura podría omitir o duplicar nodeids required.

## 6. Análisis de seguridad y cobertura

### Invariantes conservables por contrato

- Workspace host creado/poseído/validado exclusivamente por el harness con autoridad host.
- Checkout read-only, `.git` y raíces protegidas ocultas al worker; `/tmp` host separado de `/tmp` guest.
- Launch sin fallback a ejecución no aislada cuando Bubblewrap/validación falla.
- Observación Git host-side sin exponer `.git` al worker.
- Artefactos recuperados únicamente desde el workspace autorizado.
- Resultados funcionales, aislamiento, artefacto y Git permanecen objetos/evaluaciones separados.

### Conflictos o incertidumbres

- **H1** entra en conflicto con el principio de mínimo privilegio si se interpreta como permiso general para ejecutar tests del checkout en host. El riesgo no se resuelve por ser un test; para aceptar una modalidad limitada necesitaría allowlist, autorización, scope y análisis de side effects propios.
- **H2** no presenta conflicto conceptual con los invariantes si el worker solo envía requests limitados y el host mantiene toda la decisión sobre comandos/mounts/roots. Sigue `UNRESOLVED`: código actual no demuestra una interfaz autenticada y limitada ni controla su superficie de ataque.
- **H3** permite un perímetro/profile explícito, pero puede crear una ruta paralela de gate. Sin matriz de nodeids y agregación verificable no demuestra preservación de cobertura; `UNRESOLVED`.
- El Git status compara puntos antes/después. No prueba que no hubo una mutación reversible intermedia, y por sí solo no es un isolation verdict.
- Los audit hooks B1-R son checks a nivel de Python; no equivalen a una frontera de sistema operativo.

## 7. Cambios hipotéticos por archivo (no aplicados)

- `scripts/quality_gate_isolation.py`: si una decisión futura define un host harness/broker, solo agregar interfaz limitada, validación de caller/request y ownership host claros. No aceptar guest paths como roots, no ampliar binds y no hacer fallback.
- `scripts/quality_gate.py`: hipotético registro/aggregator explícito de nodeids ejecutados fuera del worker estándar, con clasificación, resultados por fase y errores fail-closed.
- `config/test_perimeter.json`: solo una modificación autorizada de contrato para identificar perfiles/clases; nunca excluir silenciosamente `tests/audit` o `tests/unit`.
- `tests/audit/test_b1_route_repeatability.py`: separar explícitamente invocación worker, artifact verifier y Git observer host-side preservando todas las assertions. No retirar Git status ni sustituirlo por mock.
- `scripts/verify_b1r_artifact.py` y `tests/audit/b1r_contract.json`: únicamente si una decisión normativa añade campos/identidad para run, worker, aislamiento o evidencia Git; el verifier no debe adjudicar más autoridad que el contrato.
- Tests de `tests/unit/diagnostics/`: si se adopta una clase host-controller, preservar nodeids/assertions y especificar qué prueba real de Bubblewrap ejecuta cada uno. Los fakes no se elevan a evidencia de aislamiento.
- Documentación de harness/gate: registrar autorización, perfiles, trust boundaries, limitaciones y matriz de cobertura.

Este inventario es conceptual, no autorización ni plan de implementación aprobado.

## 8. Decisiones pendientes

1. Rechazar expresamente H1 como permiso host general o definir su allowlist/autoridad excepcional.
2. Decidir si H2 requiere un broker host; en ese caso, establecer identidad/autenticación del solicitante, operaciones allowlisted, límites de args/recursos, lifecycle del workspace, protocolo de outputs, timeout, anti-replay, auditoría y fail-closed.
3. Decidir si H3 es la clase contractual para pruebas con controlador y definir cómo aparece en el perímetro/reporte del gate sin perder o duplicar nodeids.
4. Adjudicar si B1-R debe tener un worker Bubblewrap real, dado que actualmente ejecuta subprocess directo con controles Python internos.
5. Especificar quién captura Git baseline/final, qué sucede con cambios concurrentes y si el requisito cubre solo estado final o también escrituras transitorias. No inferir sterility desde el `status` final.
6. Definir formato/provenance del bundle combinado controller, worker, verifier, isolation y Git, manteniendo sus resultados separados.
7. Determinar la evidencia de ejecución que eventualmente sería necesaria; cualquier ejecución necesita autorización separada.

## 9. Resultado y estado canónico

- **Resultado:** `B1R_HOST_CONTRACT_PARTIAL`.
- H1 se rechaza como supuesto de confianza general.
- H2 y H3 permanecen sin resolver respecto de la integración y la cobertura real del Quality Gate.
- B1-R conserva repetibilidad, salida funcional, artefacto/verifier y Git status como assertions distintas; el error de observación Git propaga y no es un éxito vacío.
- La ejecución funcional observada no usa Bubblewrap; no se puede presentar el subprocess/audit hook como equivalente a worker aislado.
- No se autoriza implementación ni STEP-17.
- No se ejecutaron pytest, nodeids, Quality Gate, scripts de preparación, benchmarks ni pruebas de aislamiento.
- No se accedió a bases protegidas ni se crearon snapshots.
- No se hizo staging, commit, reset, checkout ni limpieza.
- No se modificaron código, tests, configuración ni expedientes anteriores.

**Salida:** `B1R_HOST_CONTRACT_PARTIAL`  
**Estado obligatorio:** `P1.2 = BLOCKED-REGRESSION`
