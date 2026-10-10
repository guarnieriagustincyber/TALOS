# TALOS-P1.2-STEP-18 — ADJUDICACIÓN DE AUTORIDAD HOST Y PROPIEDAD DE COBERTURA

**Entrada:** `H3_COVERAGE_CONTRACT_PARTIAL`  
**Estado canónico:** `P1.2 = BLOCKED-REGRESSION`  
**Tipo:** análisis contractual estático  
**Resultado:** `HOST_AUTHORITY_ADJUDICATION_PARTIAL`

## 1. Estado del repositorio

- Rama observada: `talos-current-audit`.
- HEAD observado: `cc8acfae623f9d10c8366871470319786b6a7ca4`.
- Al inicio, `git status --porcelain=v1` reportó 1.863 paths con cambios staged, 23 con cambios unstaged y 68 paths untracked.
- Estos conteos describen lo reportado por Git; no prueban autoría. Se preservaron todos los cambios preexistentes.
- El expediente STEP-18 no existía al inicio. Este es el único archivo creado en esta fase.
- No se modificaron código, tests, configuración ni expedientes anteriores.

## 2. Fuentes inspeccionadas

- `scripts/test.sh:1-16`: selección del intérprete e invocación del runner del checkout.
- `scripts/quality_gate.py:1-26,569-718,730-928,971-1154,1218-1250,1473-1602,1630-1685,1788-2052`: imports, perímetro, agregador, preparación host, Bubblewrap y entrada al worker.
- `scripts/quality_gate_isolation.py:63-101,213-307,309-352,365-430`: validación de workspace host, mapeo de ruta guest, mounts y máscaras.
- `src/study_engine/contracts/trust_root.py:1-62`: trust root estática del manifiesto protegido.
- `tests/protected/manifest.json:1-10`: contenido efectivo del manifiesto protegido inspeccionado.
- `config/test_perimeter.json:1-9,120-129,185-215`: clasificación de suites y campos del scope/profile B06.
- `tests/conftest.py:1-118`: fixtures y comportamiento dependiente del entorno aislado.
- `tests/unit/diagnostics/test_quality_gate_isolation.py:26-490`.
- `tests/unit/diagnostics/test_quality_gate_focal_execution.py:667-954`.
- `tests/audit/test_b1_route_repeatability.py:14-125,128-207,303-417,423-606,678-679`.
- `tests/audit/b1r_contract.json:1-120`.
- `scripts/verify_b1r_artifact.py:13-167,169-273`.
- `docs/TEST_CERTIFICATION_PERIMETER.md:1-29,120-131,255-299,320-340`.
- `docs/A_PRE_0_BASELINE_SPEC.md:290-330,390-417`.
- Expedientes STEP-13 a STEP-17, según referencias por sección incluidas en la materia tratada.

No se ejecutaron tests, Quality Gate, scripts de preparación, benchmarks ni pruebas de aislamiento. No se accedió a bases protegidas ni se crearon snapshots.

## 3. Flujo host observado y política de confianza

### 3.1. Qué ejecuta el proceso host antes de Bubblewrap

La invocación oficial documentada por el repositorio es `scripts/test.sh`, que elige primero `.venv/bin/python` del propio checkout y ejecuta `scripts/quality_gate.py --profile release` (`scripts/test.sh:4-16`). También es posible invocar directamente el script Python; su `main()` recibe argumentos y, salvo `--_sandbox-worker`, llega a `run_isolated_gate()` (`quality_gate.py:1788-1810,2025-2048`).

Antes de lanzar Bubblewrap, el proceso actual:

1. Ya está ejecutando el archivo `scripts/quality_gate.py` del checkout como código Python host. El top-level importa módulos estándar (`quality_gate.py:1-26`).
2. Añade el checkout y `src/` a `sys.path`, carga y valida `config/test_perimeter.json`, descubre archivos `test_*.py` y obtiene su clasificación. `validate_perimeter()` descubre paths y resuelve metadatos; la clasificación por suite no es autenticación del código (`quality_gate.py:569-718,1996-2004`).
3. Importa `study_engine.contracts.trust_root` desde el checkout y verifica `tests/protected/manifest.json` (`quality_gate.py:2006-2023`).
4. En modo supervisor importa desde el checkout `scripts.quality_gate_isolation` y `study_engine.diagnostics.test_isolation_snapshots` (`quality_gate.py:1218-1238`).
5. Ejecuta en host validación/provenance de snapshot, obtención de identidad del repositorio, creación de `TemporaryDirectory(dir="/tmp")`, derivación de workspace y verificación pre/post del snapshot, antes de `run_isolated_process()` (`quality_gate.py:1473-1514,1595-1602,1649`).
6. Construye los argumentos/env del worker y lanza Bubblewrap usando el código importado del checkout. El hijo ejecuta `/workspace/repository/scripts/quality_gate.py --_sandbox-worker`; el checkout guest es read-only y `/tmp` guest es un tmpfs separado (`quality_gate.py:1533-1602`; `quality_gate_isolation.py:290-307`).

El proceso pytest normal y sus tests se ejecutan dentro del worker luego del lanzamiento. Esto es una frontera real de proceso en el flujo diseñado, pero no hace que el código Python del supervisor que decide y crea esa frontera sea independiente del checkout.

### 3.2. Imports, datos y capacidades previas al worker

- `quality_gate.py` carga configuración del perímetro, archivos fuente/identidad, trust-root helper y módulos de snapshots del checkout en host.
- `scripts/test.sh` selecciona un intérprete desde `.venv` del checkout si está presente; de lo contrario usa `python3` resuelto por `PATH` (`scripts/test.sh:7-16`). `pyproject.toml:1-48` declara dependencias Python, pero esa declaración no demuestra por sí sola una instalación inmutable o verificada.
- Los módulos importados de `src/` pueden ejecutar código top-level como cualquier import Python. El runner hace imports desde `sys.path` del checkout (`quality_gate.py:1996-2006`); no se halló aislamiento host del intérprete ni un mecanismo externo que certifique esos módulos.
- La suite, `tests/conftest.py`, fixtures, plugins pytest y código de tests se recolectan/ejecutan por pytest en el worker en el flujo del gate. Los hooks/fixtures pueden operar dentro de los permisos guest disponibles; su ubicación bajo `tests/` no los vuelve confiables para host.
- El runner host actual puede leer los paths de snapshot autorizados, leer identidad/estado del checkout y crear/validar workspaces temporales; el proceso no está contenido por Bubblewrap antes de invocar `run_isolated_process()`.
- No se inspeccionó una interfaz en la que los tests envíen requests dinámicos al proceso supervisor. La capacidad del host proviene del código supervisor del checkout, no de una API broker actualmente demostrada.

### 3.3. Qué autentica y qué no autentica la evidencia existente

| Mecanismo observado | Evidencia | Alcance y límite |
|---|---|---|
| Clasificación del perímetro | `config/test_perimeter.json`; `validate_perimeter()` verifica formato, cobertura de módulos y clasificaciones (`quality_gate.py:569-718`). | Define qué suites son `required`, `qualification-required`, etc. No autoriza el código del runner para ejecutarse en host. |
| Trust root de manifiesto protegido | `trust_root.py:14-22,27-62` compara SHA-256 de `tests/protected/manifest.json` con una constante. | Comprueba el manifiesto protegido concreto, no el hash de `quality_gate.py`, `quality_gate_isolation.py`, `test.sh`, `conftest.py` ni el paquete importado como condición previa independiente. El archivo que contiene la constante también pertenece al checkout. |
| Manifiesto protegido actual | `tests/protected/manifest.json:1-10` enumera `test_epistemological_invariants.py`. | No enumera ni fija la identidad del runner del gate o del harness host. |
| Rutas de ejecución efectiva B06 | `config/test_perimeter.json:185-215` incluye paths como `scripts/quality_gate.py`, `quality_gate_isolation.py` y `scripts/test.sh` en un perfil focal; el binding/fingerprint focal se construye y consume en el propio runner (`quality_gate.py:173-325,343-535,1518-1531`). | Es identidad/provenance de ejecución focal bajo ese contrato; no es una autorización externa general del runner host para el gate requerido/release, ni evidencia de trust anchor independiente. |
| Política documental del gate | `TEST_CERTIFICATION_PERIMETER.md:255-299` describe al runner como supervisor y la frontera Bubblewrap. | Documenta el diseño/perímetro; no crea una frontera técnica ni prueba que el ejecutable host sea externo, inmutable o autorizado. |
| A-PRE baseline/report | `A_PRE_0_BASELINE_SPEC.md:290-330,390-417` propone registrar hashes de inputs y un wrapper externo para obtener resultados. | Es una especificación de evidencia; la inspección no encuentra que esos hashes se verifiquen contra una identidad autorizada independiente antes de ejecutar el runner host. No se toma como mecanismo runtime existente. |

No se encontró, en las rutas y documentación inspeccionadas, firma del runner, hash esperado mantenido fuera del checkout, mecanismo de instalación inmutable verificado por este flujo, identidad externa de aprobación ni política que autorice una versión específica del código host. Tampoco se encontró un guard que impida que una modificación del checkout cambie `quality_gate.py` para ejecutar otro código antes o en lugar de Bubblewrap. Por tanto, el origen “checkout TALOS” o el nombre “quality gate” no son evidencia suficiente de confianza.

La trust root existente no se debe minimizar: sí verifica una identidad concreta de un manifiesto protegido. Pero su scope observado es más estrecho que la autoridad del runner host y no autentica por sí sola el supervisor o las dependencias que hacen esa verificación.

### 3.4. Opciones de autoridad host

| Opción | Evidencia existente | Supuesto añadido / operaciones host | Riesgo y evaluación |
|---|---|---|---|
| **A. Runner host del checkout** | El flujo actual ejecuta `scripts/quality_gate.py` y módulos importados del checkout en host antes de Bubblewrap (`quality_gate.py:1218-1250,1473-1602,1996-2048`). | Confía en la versión del checkout para preparar inputs, leer estado/snapshot, elegir mounts y ejecutar el aislamiento; código modificado puede controlar la secuencia host. | **`INCOMPATIBLE` como autoridad implícita para ejecutar tests arbitrarios en host o como trust policy ya demostrada.** Describe la arquitectura actual, no una aprobación. Para aceptarla como contrato hace falta identidad externa/versionada y aprobación explícita del runner, dependencias y superficie host. |
| **B. Harness mínimo con identidad autorizada independiente** | No se halló tal harness independiente en el código inspeccionado. El wrapper `scripts/test.sh` vive en checkout y delega al runner del checkout. | Un componente fuera del checkout o instalado de modo controlado tendría una allowlist fija, crearía roots host, invocaría worker Bubblewrap y recogería outputs; el checkout aporta inputs y código ejecutado solo guest. | **`UNRESOLVED` como opción aceptable, no existente.** El límite de menor privilegio es plausible, pero faltan identidad verificable, política de autorización, distribución/actualización, contrato de inputs, perfil y enlace con el perímetro. No se puede declarar implementado. |
| **C. Harness del checkout con autorización externa explícita** | Hay identidad focal/hash de inputs y una trust root de manifest, pero ningún mecanismo observado que verifique una aprobación externa del runner general antes de permitirle autoridad host. | Autorizar un hash/versión de runner y dependencias, bajo límites de privilegios; rechazar cualquier discrepancia antes de ejecutar ese código con autoridad host. | **`UNRESOLVED`.** Podría ser aceptable si la autorización/versionado y su verificador son realmente independientes y fail-closed; ninguna evidencia inspeccionada prueba esa política. Aprobar por ruta, por commit reportado por el propio runner o por un hash auto-publicado no basta. |

**Adjudicación:** no hay evidencia suficiente para seleccionar A/B/C como política de autoridad host. A es la arquitectura observada, pero carece de autorización independiente demostrada. B es la dirección más estrecha para futuros diseños si se define fuera del checkout. C solo puede aceptarse tras evidencia externa de autorización/versionado. Esta fase no selecciona política ni autoriza implementación.

## 4. Propiedad contractual de ejecución de nodeids

### 4.1. Modelos

| Modelo | Regla de propiedad | Duplicados/omisiones/contradicciones | Evaluación estática |
|---|---|---|---|
| **1. Propiedad estándar** | El item exacto recolectado por pytest del perfil es propietario del resultado; se ejecuta una vez en la suite normal. Resultados de procesos hijos son subresultados/afirmaciones del item, no nodeids satisfechos automáticamente. | Conteo por nodeid/profile/run. Missing required, más de un owner o resultado conflictivo bloquea. Un subpytest no satisface el parent a menos que un contrato lo registre como relación child y la assertion del parent lo consuma. | Es el único modelo que el agregador actual representa de forma directa por suite; clasificación de archivos por directorio y outcomes de pytest (`quality_gate.py:730-928,971-1154`). No cubre bien condiciones de ejecución host/guest por nodeid. |
| **2. Propiedad transferida** | Un perfil dedicado asume formalmente la obligación de ejecutar un nodeid, con identidad exacta, clasificación, autorización del perfil, evidencia y resultado consumible por gate. | Perímetro y plan deben declarar un solo owner por profile; normal y dedicado no pueden ambos contar, ni ambos omitir. Perfil no aplicable no satisface `required`. Falta, duplicado o conflicto bloquea. | No existe clasificación/registro/aggregator host-side observado. No se puede transferir un `required` en STEP-18 ni modificar el perímetro. |
| **3. Propiedad compuesta** | El item pytest exacto sigue siendo el owner. El item requiere subresultados explícitos (controller, worker, verifier, Git, boundary) vinculados a un run-id y consume cada uno bajo su contrato. | PASS solo si están todos los subresultados requeridos, únicos, de productores esperados, scope/profile compatible y códigos válidos. Cualquier missing, duplicate, producer mismatch o contradiction falla/cierra el gate. | Es el modelo futuro que mejor expresa boundary y B1-R sin elevar un child a nodeid parent; requiere extender el formato/aggregator y definir trust del controller. No existe en el código actual. |

### 4.2. Modelo aplicable a las clases encontradas

- **Estado actual:** los once nodeids siguientes son propiedad estándar por la clasificación vigente: archivos de `tests/unit` pertenecen a la suite `tests/unit` `required`; B1-R pertenece a `tests/audit` `required`. No hay transferencia autorizada en el perímetro.
- **Helpers puros** (`workspace_guest_path_maps...`, `workspace_guest_path_rejects...`): propiedad estándar. Sus assertions verifican mapeo/contención de paths existentes; no constituyen aislamiento real.
- **Orquestación simulada** (`test_isolated_focal_runner_propagates_binding_and_writes_receipt`): propiedad estándar. El fake permite afirmar el contrato de llamada/receipt simulado; no se admite como subresultado Bubblewrap.
- **Tests que lanzan un child aislado**: propiedad estándar actual del item parent, con el child como subresultado del test. Para el gate actual son estáticamente incompatibles cuando `tmp_path` guest se pasa como root host a `run_isolated_process()`. Un futuro modelo compuesto puede exigir evidencia host-created root/worker real, pero no está implementado.
- **B1-R**: propiedad estándar del item actual; para preservar host Git y ejecución funcional confinada se necesitaría un contrato compuesto del item que obligue worker real, artefacto/verifier y Git host-side. Hoy el worker del test no invoca Bubblewrap y su `_git_status()` corre en el proceso pytest. Transferirlo a un controller host que importe todo el test sería inaceptable sin autorización independiente del código host.
- **Propiedad transferida:** no aplicable a ningún nodeid durante esta fase.

Para cada futuro resultado, el reporte tendría que incluir: nodeid completo; clasificación resuelta por el perímetro canónico; profile/obligación (`required` en ambos perfiles actuales; `qualification-required` solo en `release`); owner único; item pytest outcome; child IDs/roles; productor/run-id por evidencia; worker exit/timeout; verifier status; observación de aislamiento y Git en campos separados. El agregador debe comparar contra un conjunto esperado, no aceptar ausencias como si fueran no aplicables. Duplicado, resultado contradictorio, identidad/perfil incorrecto o artifact ausente => `FAIL`/`ERROR`/`BLOCKED`, nunca PASS.

## 5. Matriz de ownership y clasificación de nodeids

Todos los nodeids listados están actualmente `required`. El mecanismo indicado es una clasificación contractual recomendada para una fase futura; no modifica su owner actual, ubicación ni clasificación.

| Nodeid canónico | Clase | Clasificación | Owner actual | Modelo futuro indicado | Evidencia que contaría; lo que NO demuestra |
|---|---|---|---|---|---|
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_maps_host_path_to_mounted_workspace` | Helper puro de rutas | `required` (`tests/unit`) | Item pytest estándar | Estándar; si su contrato exige identidad de workspace host, hacerlo explícito en inputs/context, sin atribuir esa semántica a un guest tmp. | Assertion de path esperado `/workspace/run/pytest-tmp` cuenta para helper; no prueba mount ni Bubblewrap. |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_rejects_paths_outside_workspace` | Helper puro de contención | `required` | Item pytest estándar | Estándar | Excepción por path fuera del workspace; no prueba rechazo de symlink ni validador completo de roots. |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_bubblewrap_denies_protected_paths_and_allows_derived_workspace` | Prueba de boundary real/compuesta | `required` | Item pytest estándar; intenta crear un worker hijo | Compuesto futuro: item dueño + worker Bubblewrap real/subresultados | Resultado de child, denegaciones de paths/SQLite, writes permitidos solo en workspace, fingerprints y namespaces; no basta pytest pass ni JSON sin proveniencia. |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolation_fails_closed_when_bubblewrap_is_unavailable` | Validación fail-closed/orquestación con lookup simulado | `required` | Item pytest estándar | Estándar (no demuestra aislamiento positivo) | `IsolationError` exacto al no encontrar bwrap; no demuestra que bwrap real lance o aísle. |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolated_process_exit_code_is_preserved` | Prueba de ejecución de hijo aislado | `required` | Item pytest estándar; intenta lanzar hijo | Compuesto futuro si requiere probar frontera del runner | El hijo retorna 23 vía invocación Bubblewrap real y el runner conserva `returncode`; no demuestra todas las máscaras/side effects. |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_active_virtual_environment_is_available_read_only_in_sandbox` | Prueba de ejecución de hijo/mount de runtime | `required` | Item pytest estándar; intenta lanzar hijo | Compuesto futuro | Child observa runtime esperado y escribe output autorizado; identidad `/opt/talos-venv` por sí sola no demuestra montaje read-only. |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_synthetic_pytest_runs_inside_the_process_boundary` | Prueba de hijo pytest aislado y datos sintéticos | `required` | Item pytest estándar; inicia pytest hijo | Compuesto futuro | Resultado del pytest hijo, asserts protegida/derivada y fingerprint; el hijo no se cuenta como item parent adicional. |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_snapshot_contract_tests_run_without_git_or_production_mounts` | Prueba compuesta de pytest hijo, checkout sin Git/roots enmascaradas | `required` | Item pytest estándar; inicia pytest hijo | Compuesto futuro; identidad Git del checkout corresponde al supervisor, no al worker | Child result y evidencia de configuración real sin `.git`/roots; exit cero no prueba que todos los paths sensibles estén enmascarados. |
| `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_focal_binding_is_validated_inside_bubblewrap` | Prueba de boundary real y binding | `required` | Item pytest estándar; llama launcher real | Compuesto futuro | Binding/ID correcto y namespaces mount/net/pid distintos, con worker real; no utilizar datos B06 protegidos para esta demostración. |
| `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_isolated_focal_runner_propagates_binding_and_writes_receipt` | Prueba de orquestación simulada/fake | `required` | Item pytest estándar | Estándar, marcada explícitamente como mocked orchestration | Orden, argumentos/env, receipt y secuencia bajo fake; **no** es evidence de aislamiento y no se combina como tal. |
| `tests/audit/test_b1_route_repeatability.py::test_synthetic_chat_route_is_repeatable_and_sterile` | Compuesta: worker funcional, artefacto/verifier y observación Git host-side | `required` (`tests/audit`) | Item pytest estándar; `_git_status()` y subprocess directo viven en ese proceso | Compuesto futuro; controller host debe ser un perfil fijo autorizado, worker real aislado y verifier separado | Diez casos × tres ejecuciones, reporte conforme, Git inicial/final comparable y evidencia de aislamiento independiente. Ningún componente individual satisface al resto. |

La evaluación de rutas/validación de root puede ejecutarse como lógica pura, pero un proceso host que carga arbitrario pytest/test code no se transforma por ello en harness autorizado. Quien cree la raíz usada por un child Bubblewrap debe tener autoridad host explícita. Un worker guest no obtiene esa autoridad por tener un `tmp_path` writable.

## 6. B1-R: secuencia contractual con productores, consumidores y fallos

La secuencia mantiene la semántica existente del test —igualdad de los estados reportados por `git status --porcelain --untracked-files=all` antes y después— sin declarar ausencia de escrituras transitorias.

| # | Operación / productor | Permisos e inputs | Output consumido | Error que bloquea |
|---|---|---|---|---|
| 1 | **Resolver perfil** — política de gate/harness externa al test | Identity de profile predefinida, allowlist del nodeid B1-R, clasificación `tests/audit=required`, checkout/run ID. No se acepta comando o ruta del worker. | `ExecutionIdentity` con profile, nodeid, checkout identity y run-id, consumida por supervisor/agregador. | Perfil desconocido, clasificación no verificada, identidad incompleta o política de autoridad ausente => BLOCKED. La política externa no está demostrada ahora. |
| 2 | **Git inicial** — observador host identificado | Solo checkout canónico identificado; ejecutar el mismo comando/alcance del test, incluyendo `--untracked-files=all`. | stdout/exit/stderr + identidad checkout/run; consumido por comparación final. | Git ausente/error, checkout no es el esperado, salida no interpretable => ERROR/UNKNOWN; jamás sustituir por cadena vacía. |
| 3 | **Workspace** — supervisor host autorizado | Generar raíz única bajo `/tmp`; canonicalizar, validar no-symlink/contención/no-solapamiento con repo y asignar mountpoint guest. | `HostWorkspace(run_id, root)` y relación bind a guest; consumida por launcher. | Root inválida, symlink, checkout overlap, identidad duplicada o permisos inesperados => BLOCKED, sin fallback. |
| 4 | **Lanzar worker funcional** — harness identificado invoca `run_isolated_process()` o mecanismo aprobado | Checkout solo lectura en `/workspace/repository`; `.git`/raíces protegidas enmascaradas; workspace limitado; `/tmp` guest tmpfs. Worker no recibe `.git` ni autoridad para pedir mounts. | Proceso Bubblewrap y exit/timeout/stdout/stderr, consumidos separadamente por test item y evaluador de aislamiento. | bwrap ausente, validación/mount falla, timeout, código no cero, evidencia de boundary faltante => FAIL/ERROR/BLOCKED. No subprocess sin sandbox como recovery. |
| 5 | **Casos** — worker ejecuta la ruta sintética | Contrato B1-R; diez IDs exactos, tres iteraciones cada uno; hooks/guards existentes activos. | 30 observaciones normalizadas y counters/probes; consumidos por verifier. | Caso/repetición faltante, guard no rechaza, contador distinto, excepción no representada o worker incompleto => FAIL. |
| 6 | **Reporte** — worker escribe artefacto en output allowlisted del workspace | Solo destino relativo previamente definido y writable por bind. El worker no especifica destino host libre. | Reporte recogido por host desde el workspace vinculado al run. | Ausente, extra, symlink/path traversal, fuera del workspace, esquema/hash de contract incoherente => ERROR/FAIL. |
| 7 | **Verificación** — verifier independiente identificado | Bytes del contrato y reporte exactos; invocación separada del worker o en namespace permitido con inputs RO; no accede a `.git` real. | Exit/status/findings y alcance de checks; consumidor es el owner del item compuesto. | Verifier no disponible/no cero, review required, findings, envelope/hash incorrecto => FAIL/ERROR. `TECHNICAL PASS` solo afirma conformidad del artefacto con ese verifier. |
| 8 | **Git final** — mismo observador host | Mismo checkout, run, comando y alcance de paso 2. | Segundo status/exit/stderr; comparador requiere baseline/final ambos válidos. | Error, identidad de checkout cambiada, evidencia faltante o status diferente => ERROR/UNKNOWN/FAIL. No se infiere igualdad. |
| 9 | **Evaluaciones separadas** — consumidores con jurisdicción explícita | Worker result, verifier, aislamiento observado y Git pair, cada uno con productor, scope y run-id. | Functional result; artifact-verification result; isolation assessment; Git comparison. | No componer PASS funcional en aislamiento, verifier pass en verdad, Git equality en sterility ni aislamiento en Git equality. Cualquier input inválido/contradictorio queda flagged/blocked. |
| 10 | **Agregación nodeid** — Quality Gate | Exact nodeid, clasificación, owner, profile, ejecuciones y subresults; un único registro de cobertura por item. | Resultado B1-R atribuido a suite `tests/audit` `required`, más evidencia derivada independiente. | Missing/duplicated item, subresult ausente/duplicado, producer mismatch, contradicción o profile no aplicable a required => ERROR/FAIL/BLOCKED. No sumar solamente el exit code del controller. |

### 6.1. Qué prueba B1-R ahora y qué no

El código actual ejecuta `git status` antes/después con `check=True` y compara strings (`test_b1_route_repeatability.py:56,106-125`). Si falla la observación, el proceso comunica error; no existe success-shaped fallback. El test exige return code cero del subprocess y del verifier, artefacto presente y respuesta técnica exacta (`:58-105`).

El worker es lanzado por `subprocess.run()` directamente (`:58-73`); la lógica de guards usa audit hooks/monkeypatches a nivel Python (`:303-417`). En el código inspeccionado de ese test no aparece `run_isolated_process()`, comprobación de namespaces o validación de mounts. Por tanto:

- **Sí afirma contractualmente:** para el checkout leído, `git status --porcelain --untracked-files=all` reporta lo mismo en las dos capturas; el worker tuvo el resultado esperado; y el artefacto satisfizo los checks del verifier.
- **No afirma ni demuestra:** que no hubo escrituras temporales luego revertidas; que ignored files o todo efecto externo fueron detectados por ese `git status`; que el worker estuvo aislado por Bubblewrap; que un report/hash fue autenticado por un producer externo solo por pasar el verifier.
- Para una afirmación más fuerte de sterility se necesitaría prevención/observación adicional explícita. No se eleva la equality Git a tal afirmación.

## 7. Matriz de decisión de propiedad

| Clase | Propiedad actual | Modelo requerido si se conserva el alcance solicitado | Razón / límite |
|---|---|---|---|
| Helpers de `workspace_guest_path()` | Standard item `required` | Standard | Operación pura de path/contención; no usa Bubblewrap. No traslada propiedad. |
| `test_isolated_focal_runner_propagates_binding_and_writes_receipt` | Standard item `required` | Standard, tipo de evidencia “mocked orchestration” | Tiene fake; sus assertions siguen siendo valiosas como contrato unitario, pero no prueba boundary real. |
| Tests de denegación, child exit, virtualenv, synthetic pytest, snapshot child y focal binding en bwrap | Standard item `required` | Composite si un perfil futuro los mantiene con children host-created | Parent nodeid es owner; child exit/namespace/outputs son subresults. Hoy sus `tmp_path` guest como workspace host son incompatibles en el gate; mover a host directamente ejecutaría código de tests con authority no aprobada. |
| B1-R | Standard item `required` | Composite con worker, verifier, isolation y Git observers enlazados | Necesita Git host-side, worker realmente confinado si el contrato lo exige y verifier independiente. Sin harness autorizado y refactor contractual no se completa. |
| Cualquier nodeid transferido a perfil dedicado | Ninguno transferido | Modelo transferido solo tras decisión/perímetro explícitos | Nunca basta ejecutar un script hijo. Requeriría owner único, clasificación vigente, exactly-once y agregación fail-closed. |

Con estas reglas, las suites siguen obligatorias en `required` y `release`. La semántica de `qualification-required` permanece “release only” según `TEST_CERTIFICATION_PERIMETER.md:10-23` y no se usa como salida para los nodeids analizados.

## 8. Resultado de STEP-18 y decisiones pendientes

La evidencia estática permite:

- describir el supervisor host y los imports/operaciones que actualmente preceden a Bubblewrap;
- afirmar que el runner y el aislamiento se cargan desde el checkout;
- constatar una trust root de scope limitado para el manifiesto protegido;
- fijar la propiedad estándar actual de los nodeids por clasificación del perímetro;
- especificar cómo se distinguirían item, controller, worker, verifier, aislamiento y Git; y
- preservar las fronteras requeridas para una futura integración.

La evidencia **no** permite:

1. seleccionar A, B o C como política de confianza host aprobada;
2. afirmar que una modificación del checkout no puede cambiar el comportamiento pre-Bubblewrap del runner;
3. transferir nodeids `required` a un perfil sin un mecanismo de cobertura/aggregator vigente;
4. afirmar que B1-R conserva la semántica pedida bajo Bubblewrap con el test/código actual;
5. atribuir autenticidad independiente al runner, al artefacto B1-R o a la observación Git por el mero uso de hashes/status local.

Decisiones/evidencia externa requeridas:

- identidad y autoridad del componente que puede ejecutar con visibilidad host;
- política de aprobación/versionado independiente para runner, dependencia/interpreter y profile, o identidad de harness externa al checkout;
- allowlist exacta de operación/nodeids y autorización de cualquier controller code;
- contrato de transferencia/composición y reporte por nodeid que detecte falta, duplicación y contradicción;
- refactor contractual autorizado de B1-R para conservar assertions con Git host-side y worker Bubblewrap real, sin exponer `.git`;
- definición precisa de evidencia de aislamiento y de límites de la claim de sterility.

**Resultado:** `HOST_AUTHORITY_ADJUDICATION_PARTIAL`. La arquitectura del runner host sí existe; su política independiente de autorización no está demostrada. Se mantiene la cobertura canónica sin transferir nodeids ni presentar subresultados como nodeids ejecutados.

## 9. Cierre

- No se afirma que el harness funcione en ejecución ni que Bubblewrap esté validado dinámicamente.
- No se ejecutaron `pytest`, nodeids, Quality Gate, scripts de preparación, benchmarks ni pruebas de aislamiento.
- No se accedió a bases protegidas, no se crearon snapshots y no se alteraron corpus/modelos.
- No se hizo staging, commit, reset, checkout ni limpieza.
- Los cambios preexistentes staged/unstaged/untracked se preservaron; sus conteos no prueban autoría.
- No se modificaron código, tests, configuración ni expedientes anteriores.
- STEP-18 no autoriza implementación, pruebas ni transición a P1.3.

**Estado final obligatorio:** `P1.2 = BLOCKED-REGRESSION`
