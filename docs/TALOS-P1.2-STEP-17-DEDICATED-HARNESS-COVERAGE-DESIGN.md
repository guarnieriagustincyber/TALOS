# TALOS-P1.2-STEP-17 — DISEÑO CONTRACTUAL DEL HARNESS DEDICADO Y DE SU COBERTURA

**Entrada:** `B1R_HOST_CONTRACT_PARTIAL`  
**Estado canónico:** `P1.2 = BLOCKED-REGRESSION`  
**Tipo:** análisis y diseño contractual estático  
**Salida:** `H3_COVERAGE_CONTRACT_PARTIAL`

## 1. Estado del repositorio

- Rama observada: `talos-current-audit`.
- HEAD observado: `cc8acfae623f9d10c8366871470319786b6a7ca4`.
- Al inicio, `git status --porcelain=v1` reportó 1.863 paths con cambios en el índice, 23 con cambios en el worktree y 67 paths untracked. Se preservaron los cambios preexistentes, sin atribuir su autoría.
- Este expediente no existía al comenzar STEP-17.
- El único archivo creado en esta fase es este documento. No se modificaron código, tests, configuración ni expedientes anteriores.

## 2. Fuentes y alcance de inspección

- `config/test_perimeter.json:1-3,8-9,134-138`: suites `tests/audit` y `tests/unit`, ambas `required`.
- `scripts/quality_gate.py:569-718`: carga del perímetro y clasificación de cada módulo descubierto.
- `scripts/quality_gate.py:730-928`: `SuiteResults`, exactitud del nodeid focal, colección, resultados y payload del collector.
- `scripts/quality_gate.py:971-1154`: `run_gate()`, suites activas por perfil, invocación de pytest y resultado agregado.
- `scripts/quality_gate.py:1218-1285,1473-1602,1630-1685`: runner host, workspace, lanzamiento Bubblewrap y recogida/validación de evidencia del worker.
- `scripts/quality_gate_isolation.py:63-101,213-307,309-352,365-430`: validación de roots, traducción host→guest, mounts, `/tmp` y máscaras.
- `tests/unit/diagnostics/test_quality_gate_isolation.py:26-47,50-330,333-490`: tests del helper y de boundaries reales.
- `tests/unit/diagnostics/test_quality_gate_focal_execution.py:667-783,785-954`: test focal dentro de Bubblewrap y test de runner que usa fake.
- `tests/audit/test_b1_route_repeatability.py:14-125,128-207,303-417,423-606,678-679`: controlador B1-R, Git, subprocess, guards, casos/repeticiones y artefacto.
- `tests/audit/b1r_contract.json:1-120`: envelope contractual, diez casos, tres repeticiones, guard probes y contadores.
- `scripts/verify_b1r_artifact.py:13-167,169-273`: validación independiente del contrato y del reporte.
- Expedientes previos: STEP-13 secciones 3–12; STEP-14 secciones 3–8; STEP-15 secciones 3–9; STEP-16 secciones 3–9.

Inspección estática solamente. No se afirma que el diseño funcione, que los tests pasen ni que Bubblewrap haya sido validado dinámicamente.

## 3. Estado efectivo de cobertura

El perímetro vigente registra suites/directorios, no perfiles por nodeid. `validate_perimeter()` descubre los módulos, exige clasificación única y rechaza rutas/suites desconocidas o stale (`quality_gate.py:569-718`). `run_gate()` selecciona suites `required` en ambos perfiles y añade `qualification-required` en `release`; después llama `pytest.main()` con las rutas de suite dentro del worker (`quality_gate.py:971-1044,1080-1097`). `SuiteResults` agrupa por suite y calcula recuentos, mientras que su comprobación de nodeid exacto solo se activa en modo focal (`quality_gate.py:730-810,850-928`).

Consecuencias:

1. Los nodeids de `tests/unit/diagnostics/...` están en `tests/unit` (`required`) y el B1-R está en `tests/audit` (`required`).
2. Ninguno está clasificado `qualification-required`; el perfil `required` y el perfil `release` incluyen esas suites.
3. Hoy, todos se recolectan como parte de pytest dentro del worker estándar del Quality Gate. No hay inventario/perímetro de ejecución de controladores host-side, ni agregador que combine resultados de un perfil dedicado.
4. Ejecutar un nodeid fuera del worker sin retirarlo de forma explícita del plan normal puede duplicar su ejecución; retirarlo del plan normal sin una clasificación/registro equivalente puede hacer desaparecer un test `required`.
5. En particular, la ejecución host-side de todo el test B1-R ejecutaría su código controlador del checkout en host. No se puede asumir que sea seguro por ser `tests/audit`.

## 4. Contrato propuesto para un harness dedicado de perfil fijo

Esta sección define condiciones que una decisión posterior tendría que satisfacer; no afirma que exista el harness.

### 4.1. Identidad, autoridad y confianza

- El harness es una capacidad host **fija y allowlisted**, no una consola ni API general. La invocación recibe una identidad de perfil/run predefinida; no acepta comandos, rutas host, mountpoints, variables arbitrarias o scripts elegidos por el worker.
- La identidad aprobada debe incluir al menos: ID y versión del perfil; identidad/hash del propio harness; identidad exacta del checkout/commit/tree de tests y runner; lista cerrada de nodeids; clasificación/perímetro; política de mounts; esquema de outputs; y run-id único.
- La ubicación del harness o de un test dentro del checkout no establece por sí sola confianza. El código que corre con visibilidad host debe ser mínimo, identificable por separado y autorizado por una política externa al simple contenido del archivo.
- El harness crea y es dueño del workspace host bajo `/tmp`, valida su canonicalización, symlinks, contención y separación del checkout, y solo entonces prepara el worker Bubblewrap.
- El worker funcional no elige workspace ni solicita operaciones host dinámicas. H3-A, como opción recomendada conceptualmente, no incorpora broker ni protocolo worker→host. Una eventual captura Git host-side forma parte del perfil fijo del harness.
- Fallos de identidad, autorización, validación, spawn, timeout, recolección o verificación terminan `ERROR`/`BLOCKED`/`UNKNOWN`, no se convierten en pass ni activan fallback.

### 4.2. Ejecución separada y evidencia

Cada ejecución genera objetos relacionados por run-id pero evaluados por separado:

```text
PERFIL FIJO / NODEID EXACTO
  ├── CONTROLADOR / preparación host autorizada
  ├── WORKER FUNCIONAL
  │     resultado, exit code, timeout, stdout/stderr permitido
  ├── EVIDENCIA DE AISLAMIENTO
  │     Bubblewrap invocado, configuración/mounts, assertions de boundary
  ├── ARTEFACTO B1-R
  │     identidad, contenido/huella, contrato y resultado del verifier
  └── OBSERVACIÓN GIT HOST-SIDE
        checkout identity, status inicial/final, códigos y comparación
```

- Worker funcional exitoso no satisface aislamiento.
- Aislamiento observado no demuestra resultado funcional correcto.
- Verifier técnico exitoso demuestra únicamente el contrato mecánico comprobado sobre el artefacto.
- Git inicial/final igual no demuestra ausencia de escritura transitoria ni de efectos externos.
- El agregador del gate consume records y resultados con su productor y scope; no combina resultados por parecido de nombres, una llamada nominal a Bubblewrap ni la existencia de un artefacto.

### 4.3. B1-R bajo el perfil

El contrato de B1-R debe preservar:

- Los diez casos `success`, `error`, `abstention`, `clarification`, `truncated`, `stream_aborted`, `eof_without_terminal`, `duplicate_terminal`, `error_after_tokens` y `abrupt_close`, con tres observaciones por caso (`test_b1_route_repeatability.py:16-27,574-601`; `b1r_contract.json:6-93`).
- La comparación del verifier de observaciones normalizadas y los expected values (`verify_b1r_artifact.py:45-117`).
- Return code cero del worker, captura de stdout/stderr en diagnóstico y timeout explícito de 120 segundos (`test_b1_route_repeatability.py:58-78`).
- Existencia del reporte y resultado exacto del verifier: return code cero y JSON `TECHNICAL PASS` sin findings (`:79-105`). El verifier comprueba el digest del contrato y la conformidad estructural/semántica del reporte; el código inspeccionado no fija una huella autenticada del reporte contra un producer independiente. No sobreinterpretar esto como autenticidad o integridad criptográfica del artefacto.
- Hash/identidad del contrato, envelope, conteos, guard probes, contadores requeridos y prohibición de findings (`test_b1_route_repeatability.py:128-207,303-417,582-606`; `verify_b1r_artifact.py:13-166,207-273`).
- Git status del mismo checkout al inicio y al final, incluyendo untracked según el comando actual, y fallo explícito si no puede observarse (`test_b1_route_repeatability.py:56,106-125`).
- Evidencia independiente de aislamiento real del proceso funcional. El código actual llama `subprocess.run()` directamente para `--worker` y para el verifier (`:58-94`); los audit hooks Python internos (`:303-417`) no sustituyen un boundary de sistema operativo.

El perfil puede separar las funciones: el harness host autorizado captura Git y crea el workspace; el worker aislado ejecuta la ruta sintética y genera el artefacto; un verifier independiente valida el artefacto. Sin embargo, no se ha determinado estáticamente cómo preservar sin cambios el nodeid padre y el control de las tres ejecuciones al transferir su orquestación a un perfil fijo, sin ejecutar arbitrariamente todo el test del checkout en host. Ese punto afecta la compatibilidad de cobertura.

### 4.4. Semántica precisa de Git y sterility

`_git_status()` ejecuta `git status --porcelain --untracked-files=all` con `check=True`. El test compara la salida capturada antes/después (`test_b1_route_repeatability.py:56,106-125`). Si el comando falla, la excepción se propaga; no hay fallback a estado vacío. La propiedad observada es:

> El estado que reporta ese comando para el checkout en la captura final es igual al que reportó en la captura inicial.

No equivale a:

- “No ocurrió ninguna escritura durante la ejecución.”
- “No hubo cambios que luego se revirtieron.”
- “No hubo escrituras en ignored files, recursos externos, caches fuera del alcance reportado o efectos no visibles para Git.”
- “El proceso fue aislado.”

Una afirmación más fuerte de sterility necesitaría una propiedad preventiva —por ejemplo, checkout efectivamente no escribible para el worker— y/o observación completa de los canales de side effects pertinentes, con límites y cobertura explícitos. El expediente no adjudica cuál mecanismo probaría exhaustivamente esa afirmación; los audit hooks existentes son Python-level y no forman por sí solos una demostración completa.

El contrato de perfil debe preservar el status pre/post del mismo checkout y registrar el exit code/error de cada observación. Error de Git, cambio de identidad del checkout o evidencia incompleta bloquean la evaluación. La comparación Git no se realiza exponiendo `.git` al worker.

## 5. Matriz de cobertura por nodeid

Todos los nodeids de esta matriz son `required`: `tests/unit` para los diez primeros tests unit/focal y `tests/audit` para B1-R. “H3-A perfil” y “H3-C worker estándar” son rutas conceptuales, no implementación aprobada. Ningún controlador host-side cuenta automáticamente como ejecución del worker hijo.

| Nodeid canónico | Clasificación | Mecanismo previsto / controller y worker | Qué cuenta como ejecución del nodeid | Evidencia/artefactos requeridos | Agregación y duplicado/ausencia/error/perfil | Estado |
|---|---|---|---|---|---|---|
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_maps_host_path_to_mounted_workspace` | `required` | H3-A: perfil fijo ejecuta esta assertion con paths host en `/tmp`; no requiere worker Bubblewrap. Controller es el runner allowlisted, no el propio `tmp_path` guest del worker general. H3-C alternativo: test helper dentro del worker, pero semánticamente no prueba path host. | Solo pytest ejecutó el item con exactamente este nodeid y assertion sobre path host; “el worker pasó el test” no convierte paths guest en host. | Item outcome/collection y perfil+identidad del path context; no requiere artefacto de worker aislado. | El gate registra una ocurrencia exacta. Duplicado o ausente en perfil aplicable = error; perfil no aplicable no satisface required. | `UNRESOLVED` |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_rejects_paths_outside_workspace` | `required` | H3-A con workspace y path hermano host; no requiere child aislado. H3-C solo prueba contención en paths guest del worker, no host mapping. | Item exacto ejecutado y error de containment esperado observado. | Resultado/assertion del item; identidad y tipo host de fixtures. | Igual: una ejecución exacta, cero/dos no pass; error de fixture/host = error, no skip satisfactorio. | `UNRESOLVED` |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_bubblewrap_denies_protected_paths_and_allows_derived_workspace` | `required` | H3-A: controller allowlisted host crea repo/DBs sintéticas y workspace; lanza un worker Bubblewrap real. H3-C anidado actual intenta hacerlo desde guest `tmp_path`. | El nodeid controlador debe pasar sus assertions completas sobre un child Bubblewrap real, no un fake ni únicamente una salida de pytest. | Child exit/result JSON, pruebas de denegación read/write/SQLite/symlink/traversal/unmount, hashes/sidecars de origen, capabilities, secreto y namespaces. | Agregador registra controller item y child result vinculados; falta cualquiera, duplicado o error de mount = error/fail. Perfil no aplicable no cuenta. | `UNRESOLVED` |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolation_fails_closed_when_bubblewrap_is_unavailable` | `required` | H3-A controller en proceso host valida el root temporal host y monkeypatchea lookup solo en su proceso; no necesita lanzar child. | Item exacto alcanza el error esperado de Bubblewrap no disponible después de validar el root. | Assertion exacta `IsolationError`; diagnóstico de fallo. No es por sí sola evidencia de boundary real. | Cuenta como test unitario, separado del nodeid que demuestra Bubblewrap disponible. Falla de validación previa debe fallar este item; no convertir en skip. | `UNRESOLVED` |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolated_process_exit_code_is_preserved` | `required` | H3-A controller host crea root `/tmp`, lanza un child Bubblewrap real que termina en 23. | Item exacto y returncode child igual a 23 tras la ruta real de aislamiento. | exit code original y evidencia de spawn/boundary. | Collector asocia child code al item; timeout/spawn failure/ausencia/doble ejecución impiden PASS. | `UNRESOLVED` |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_active_virtual_environment_is_available_read_only_in_sandbox` | `required` | H3-A controller host; child Bubblewrap real ejecuta Python/pytest y escribe en workspace permitido. | Assertion exacta de retorno cero y `runtime.txt` con prefijo `/opt/talos-venv:`. | Child exit/stdout/stderr y contenido runtime bajo workspace autorizado. La modalidad read-only debe derivarse del mount real, no de nombre. | Falta de runtime, artifact o child = fail/error; un resultado de controller sin child no cuenta. Perfil aplicable debe ejecutar una vez. | `UNRESOLVED` |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_synthetic_pytest_runs_inside_the_process_boundary` | `required` | H3-A controller host crea fixture sintético y lanza pytest hijo bajo Bubblewrap real. | Nodeid padre pasa, pytest hijo reporta el test sintético esperado y se conservan todas las assertions de acceso y escritura. | exit code/stdout del pytest hijo, origen protegido sintético sin cambio, DB derivada writable; el test hijo no cuenta como nodeid `required` adicional salvo que el perímetro lo declare. | Parent y child son resultados distintos; sin child/pass/artifacts el parent no pasa. No duplicar el nodeid child en suite aggregate. | `UNRESOLVED` |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_snapshot_contract_tests_run_without_git_or_production_mounts` | `required` | H3-A controller host prepara root y lanza pytest hijo Bubblewrap con checkout read-only, `.git` y raíces protegidas enmascaradas. | Nodeid padre pasa únicamente si el pytest hijo de snapshot completa y su exit code es cero; child tests no se confunden con parent ni extienden authority. | Exit/stdout/stderr del pytest hijo y evidencia de mounts/máscaras configurados; identidad de checkout calculada host-side si requerida. | Se registra un parent required y un subresult child referenciado. Falta de child, resultado ambiguo, error de mount o duplicado parent = no pass. | `UNRESOLVED` |
| `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_focal_binding_is_validated_inside_bubblewrap` | `required` | H3-A controller host crea binding/manifiesto sintéticos y lanza worker Bubblewrap real; no usa B06 protegido. H3-C ejecución actual desde worker crea tmp guest incompatible con raíz host. | Parent item pasa con `nodeid`, `run_id` correctos y namespaces mount/net/pid del worker distintos del host. | Binding y digest, outputs del worker, tres namespace observations, código de salida; origen sintético. | Resultado del controller solo es PASS si el worker real produce outputs completos; errores/missing/duplicate bloquean. | `UNRESOLVED` |
| `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_isolated_focal_runner_propagates_binding_and_writes_receipt` | `required` | H3-C: test de unidad en pytest worker con fake de `run_isolated_process`; no requiere worker Bubblewrap. H3-A sería posible para un test controlador, pero no se necesita por la contradicción de nested launch. | Exacto item PASS valida secuencia, env, receipt, binding y eventos mockeados. No cuenta como aislamiento real. | Receipt/assertions exactas y registro explícito de `execution_kind=mocked-orchestration-test`, no isolation proof. | Agregar a cobertura normal de `tests/unit`; no fusionar con focal real. Duplicado/missing/error sigue fallando required. | `COMPATIBLE` para mantenerlo como prueba de unidad normal; **no** para evidencia de aislamiento. |
| `tests/audit/test_b1_route_repeatability.py::test_synthetic_chat_route_is_repeatable_and_sterile` | `required` | H3-A recomendado conceptualmente: controller fijo autorizado captura Git y lanza worker funcional Bubblewrap real con workspace host propio; verifier independiente valida reporte. H3-B añadiría worker→broker dinámico no necesario demostrado. H3-C mantendría todo en worker pero no puede consultar `.git` real; tampoco hay Bubblewrap actual en `subprocess.run()`. | El nodeid padre debe reconocerse como una ejecución exacta del perfil. Debe controlar tres repeticiones de diez casos; retorno funcional cero, artefacto y verifier válidos, Git pre/post igual y evidencia Bubblewrap separada. Controlador pass sin resultados de worker/verifier/Git no cuenta. | Run/profile/nodeid; worker outputs y diagnóstico; reporte/hash y contrato; verifier return/status/findings; Git baseline/final de mismo checkout + códigos; datos independientes del launch y boundary real. | En `required` se agrega exactamente una ejecución por nodeid, cuyos componentes se enlazan por run-id. Duplicado, componente faltante, error/timeouts/verifier/Git o worker ausente = ERROR/FAIL/BLOCKED. En `required` y `release` debe quedar presente; perfil que no aplica no borra cobertura. | `UNRESOLVED` |

### Lectura de la matriz

- Los dos tests `workspace_guest_path_*` son helpers de transformación/contención, no evidencia de aislamiento.
- `test_isolated_focal_runner_propagates_binding_and_writes_receipt` usa `fake_isolated_process`; su pass no es un worker real.
- Los nodeids con “Bubblewrap”, “process_boundary”, “inside_bubblewrap” o “without_git” requieren que las assertions actuales permanezcan ligadas a una ejecución real donde así lo especifican; mover solo la función padre al host no prueba por sí mismo el child.
- Todos los nodeids de la tabla son requeridos por clasificación de suite. Que el perfil dedicado exista no los quita de esa obligación.

## 6. Comparación de arquitecturas

| Criterio | H3-A — Perfil fijo host, sin requests del worker | H3-B — Perfil con broker host limitado | H3-C — Mantener tests en worker y rediseñar casos anidados |
|---|---|---|---|
| **Superficie de ataque** | Más acotada conceptualmente: invocación predefinida y allowlist de profile/nodeids; el código ejecutado en host debe ser un launcher mínimo identificado, no todos los tests arbitrarios. Riesgo permanece si se autoriza una ruta de test que corre libremente en host. | Mayor superficie: IPC, autenticación, replay, parsing de request y confused-deputy. Aceptable conceptualmente solo con API finita, inputs de datos y operación/arguments fijados; no generic command/path broker. | No añade interfaz host, pero tests en worker no tienen autoridad host. Deben dejar de depender de host tmp/mount y seguir observando el boundary por el mecanismo real. |
| **Identidad de ejecución** | Fija identidad de profile/version, harness code hash, checkout identity, nodeids exactos y política. Worker hereda run ID inmutable. | Igual más identidad del principal solicitante, autorización, nonce/run binding y payload schema. | Nodeid/perfil se mantienen en suite estándar; identidad host de `tmp_path` desaparece del test. |
| **Workspace** | Creado/validado/poseído por host bajo `/tmp`; path guest derivado del punto bind. Worker no selecciona root. | Host crea workspace por request; nunca adopta path host proporcionado por worker. | `/workspace/run` del worker es guest; ningún test lo presenta como root host. Si necesita child Bubblewrap, el nuevo mecanismo debe ser determinista y permitido sin host delegation. |
| **Observación Git** | Directa host-side pre/post sobre mismo checkout, sin exponer `.git`; errores bloquean. | Git solo a través de operación host limitada; requiere evitar que worker seleccione repository/path. | El worker no ve `.git`; requiere separar la assertion Git de B1-R en el harness host o B1-R no satisface su contrato actual. |
| **Aislamiento real** | Harness lanza Bubblewrap real; `.git`/roots protegidas ocultas, checkout RO, workspace write limitado, `/tmp` guest tmpfs. Controller host no se considera aislado por el hecho de usar el perfil. | Puede lograr lo mismo si cada launch lo valida host-side; el worker no puede configurar montajes. | Las pruebas actuales que llaman `run_isolated_process()` con guest tmp fallan estáticamente en root validation; rediseño debe conservar prueba de boundary real sin relajar controles. |
| **Agregación/cobertura** | Necesita plan allowlisted de nodeids/perfiles y aggregate por item + subresults. Código actual no tiene esa capa. | Necesita además correlación de requests y outputs child para item requerido. | El agregador actual por suite puede seguir contando los tests si todos permanecen en el worker, pero B1-R no puede observar Git real; test anidados tienen conflicto de namespace. |
| **Duplicados/ausencias** | Perfil fijo debe detectar ejecución normal + dedicada duplicada y falta de nodeid; faltantes required bloquean. | También debe deduplicar solicitudes/replays y registrar exactamente un resultado. | El agregador actual controla colección/resultados por nodeid, pero no modela controladores externos ni nested child results. |
| **Complejidad** | Media: launcher/profile estático + resultados agregados y separación de Git/worker/verifier. | Alta: protocolo broker, autoridad, lifecycle, IPC y auditoría. | Media para adaptar pruebas, pero algunas propiedades requieren orquestación fuera del namespace guest; B1-R especialmente no se resuelve solo manteniendo su proceso en worker. |
| **Compatibilidad con evidencia actual** | Intención compatible con invariantes; no existe perfil/aggregator y no se ha demostrado que el controller autorizado pueda ser mínimo sin ejecutar test checkout general en host. | No existe broker/protocolo y no se necesita inferirlo como requisito. | Compatible con unit tests sin nested process, incluida la prueba fake; incompatible con B1-R Git desde worker y no resuelve nested host workspace bajo contrato actual. |
| **Estado** | `UNRESOLVED`, opción preferible para diseño posterior por menor superficie si se puede evitar ejecución general de tests en host. | `UNRESOLVED`, superficie/autoridad todavía más compleja; no justificado por evidencia actual. | `UNRESOLVED` para cobertura completa; no resuelve por sí sola Git/Bubblewrap. |

## 7. Recomendación fundamentada

Recomendar **H3-A únicamente como dirección de diseño a evaluar**, no como arquitectura adjudicada: un harness fijo, con identidad independiente del checkout, invocación cerrada por perfil/nodeids y sin requests dinámicos del worker, tiene menor superficie y evita delegar authority host. El harness debe ejecutar solo lógica mínima autorizada; no se debe ejecutar automáticamente el cuerpo entero de los tests del checkout en host ni confiar en él por su ubicación.

No se recomienda H3-B con evidencia actual: ningún requisito inspeccionado demuestra que el worker necesite pedir dinámicamente lanzamientos al host, y un broker añade superficie de autoridad significativa. H3-C es apropiada para conservar unit tests que no requieren host (por ejemplo el test focal con fake), pero no basta para cerrar B1-R: el worker no debe acceder `.git`, y el subprocess funcional actual no tiene Bubblewrap. Por tanto H3-C por sí sola no preserva todas las propiedades solicitadas.

La preferencia conceptual por H3-A no cumple aún condición de aceptación para implementación. En particular, falta determinar cómo:

- ejecutar el controlador con visibilidad host sin hacer confiable todo el código del test;
- conservar los nodeids required y agregarlos exactamente una vez;
- mantener los workers Bubblewrap reales y el verificador independiente;
- capturar Git pre/post en el mismo checkout y distinguirlo de aislamiento;
- impedir que un resultado de subpytest/controller sea contabilizado como otro nodeid o como prueba de boundary no ejecutada.

Por ello el resultado es `H3_COVERAGE_CONTRACT_PARTIAL`; no `H3_FIXED_PROFILE_CONTRACT_READY`.

## 8. Riesgos, incompatibilidades y decisiones no resueltas

1. **Trust del controlador:** falta identidad criptográfica/política de quién autoriza el binario/código mínimo host, cómo vincula hash de harness y checkout, y qué privilegios exactos recibe.
2. **Cobertura por nodeid:** falta un contrato de resultado por nodeid host-side; el agregador actual agrupa suites y solo exige nodeid exacto en su modo focal. No hay ownership de ejecución cruzada.
3. **Una ejecución vs dos:** mover nodeid fuera del worker sin retirar explícita y normativamente su colección estándar puede duplicarlo; retirarlo sin registrar owner/profile puede ocultar el incumplimiento `required`.
4. **B1-R Git:** El `git status --porcelain --untracked-files=all` pre/post demuestra igualdad de estado final que ese comando reporta; no demuestra ausencia de escrituras transitorias ni informa archivos ignored como parte de ese status. Falta decidir si el contrato exige solo esa comparación o sterility más fuerte y qué evidencia soportaría tal claim.
5. **B1-R isolation:** el código actual lanza worker y verifier mediante subprocess directo. Ningún mecanismo Bubblewrap ni assertion de namespaces en B1-R aparece en el test inspeccionado. La evidencia de audit hooks no cubre el boundary OS.
6. **Verificador:** un verifier técnico independiente comprueba el payload contra contract; no valida que el productor estuviera aislado ni que Git fuera observado.
7. **Focal binding:** tests focales usan bindings y recibos específicos, pero no existe una regla inspeccionada que integre los resultados de estos nodeids controller en el profile dedicado.
8. **No apropiación de autoridad:** harness no puede convertir datos del worker, strings de path, exit code o status Git en una autoridad distinta de la que efectivamente demuestra cada observación.
9. **Fallback:** si harness, Bubblewrap, verifier, Git o artefactos fallan, el resultado debe permanecer error/blocked/unknown; ninguna opción admite ejecución desnuda como recuperación silenciosa.

## 9. Cambios hipotéticos por archivo (sin aplicar)

- `scripts/quality_gate.py`: posible modelo explícito de profiles host-controller, vínculo con perímetro, listado de nodeids exactos y agregación fail-closed; actualmente no existe.
- `scripts/quality_gate_isolation.py`: solo si un contrato posterior define una interfaz fija host-side; conservar validación host `/tmp`, checkout RO, máscaras y `/tmp` guest aislado; no aceptar paths o commands del worker.
- `config/test_perimeter.json`: cualquier evolución tendría que mantener clasificación requerida y registrar explícitamente modo/perfil; no se edita ni se propone exclusión.
- `tests/audit/test_b1_route_repeatability.py`: futura separación del controller, worker Bubblewrap, verifier y observador Git manteniendo todos los casos/assertions, o documentar con autorización una nueva estructura equivalente.
- `tests/audit/b1r_contract.json`: solo si se autoriza ampliar el schema para identidad de run, observación Git y evidencia de aislamiento, distinguiendo status pre/post de sterility.
- `scripts/verify_b1r_artifact.py`: cambios eventuales únicamente para validar el envelope adicional autorizado; no elevar `TECHNICAL PASS` a aislamiento, sterility o gate verdict.
- `tests/unit/diagnostics/test_quality_gate_isolation.py` y `tests/unit/diagnostics/test_quality_gate_focal_execution.py`: mantener separados helpers, unit mocks y tests de boundary real; cualquier clasificación/perfil explícito debe conservar nodeids/assertions.
- Reporte/documentación del gate: matriz requerida, resultado por nodeid, perfil, controller/worker child, evidencias separadas, perfiles no aplicables y errores.

Esta lista es inventario conceptual, no autorización de cambio.

## 10. Cierre y estado

- Salida: `H3_COVERAGE_CONTRACT_PARTIAL`.
- La arquitectura H3-A queda recomendada solo como dirección menos permisiva para diseño posterior; no se declara viable/integrada ni se selecciona.
- H3-B no se justifica con la evidencia actual; H3-C no resuelve por sí misma Git host-side y nested workspace.
- No se afirma que el diseño funcione en ejecución o que Bubblewrap haya sido validado dinámicamente.
- No se ejecutaron `pytest`, nodeids, Quality Gate, scripts de preparación, benchmarks ni pruebas de aislamiento.
- No se accedió a bases protegidas, no se crearon snapshots y no se alteraron corpus o modelos.
- No se hizo staging, commit, reset, checkout ni limpieza.
- Se preservaron cambios staged/unstaged/untracked preexistentes sin atribuir autoría.
- No se modificaron código, tests, configuración ni expedientes anteriores.
- STEP-17 no autoriza implementación ni pruebas; cualquier trabajo de ese tipo requiere adjudicación explícita posterior.

**Estado final obligatorio:** `P1.2 = BLOCKED-REGRESSION`
