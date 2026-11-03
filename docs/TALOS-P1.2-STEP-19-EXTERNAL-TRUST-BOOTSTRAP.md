# TALOS P1.2 — STEP-19: external trust bootstrap and authorization contract

**Entrada:** `HOST_AUTHORITY_ADJUDICATION_PARTIAL`  
**Estado canónico:** `P1.2 = BLOCKED-REGRESSION`  
**Tipo:** análisis estático  
**Resultado:** `EXTERNAL_TRUST_DESIGN_PARTIAL`

## 1. Identidad y estado observado

- Rama observada: `talos-current-audit`.
- HEAD observado: `cc8acfae623f9d10c8366871470319786b6a7ca4`.
- Al comenzar, Git reportó 1.869 paths staged, 23 unstaged y 69 untracked. Son conteos de estado, no evidencia de autoría ni de quién produjo los cambios.
- El expediente STEP-19 no existía al comenzar. Se creó únicamente este archivo; se preservaron los cambios preexistentes.
- STEP-18 observó la misma rama y HEAD, pero esos datos previos no se trataron como identidad garantizada del estado actual.

## 2. Alcance, fuentes y límites

Fuentes inspeccionadas:

- `scripts/test.sh:1-16`: selección del intérprete e invocación del runner.
- `scripts/quality_gate.py:1-26,569-718,730-928,1218-1245,1473-1605,1788-2052`: imports, perímetro, recolección, preparación host, worker y entrada del gate.
- `scripts/quality_gate_isolation.py:63-101,213-307,309-352,365-430`: validación de raíces, rutas guest, mounts y máscaras.
- `src/study_engine/contracts/trust_root.py:1-62`: ancla del manifiesto protegido.
- `tests/protected/manifest.json:1-10`: alcance del manifiesto citado por la trust root.
- `config/test_perimeter.json:1-135`: clasificaciones de suites; `tests/audit` y `tests/unit` aparecen como `required`.
- `scripts/apre_harness.py:1-90,540-705,700-820` y `scripts/verify_apre_result.py:1-40,250-315`: harness y verificador A-PRE presentes en el checkout.
- `docs/A_PRE_0_BASELINE_SPEC.md:287-320,350-475`: contrato de reporte, wrapper externo propuesto y estado de preflight A-PRE.
- `docs/TEST_CERTIFICATION_PERIMETER.md:255-299`: descripción del supervisor, worker y frontera.
- `docs/TALOS-P1.2-STEP-18-HOST-AUTHORITY-COVERAGE-OWNERSHIP.md:1-70,100-180,191-209`: adjudicación previa y lista de nodeids.

La inspección fue estática. No se consultaron directorios personales o del sistema, `PATH`, servicios de CI ni gestores de claves para buscar instalaciones externas; hacerlo requeriría una consulta del entorno dinámico. No se inspeccionaron propietario ni permisos efectivos de archivos mediante el sistema operativo. Por tanto, la existencia, propiedad, permisos, integridad y disponibilidad de un ejecutable externo instalado quedan **sin verificar**. No se infiere su existencia a partir de una propuesta documental.

No se ejecutaron pytest, nodeids, Quality Gate, `scripts/test.sh`, benchmarks, pruebas de aislamiento ni scripts de preparación. No se accedió a bases/corpus protegidos ni se crearon snapshots. No se modificaron código, tests, configuración, perímetro, trust roots ni expedientes previos.

## 3. Mecanismos de confianza encontrados

### 3.1. Flujo actualmente documentado

`scripts/test.sh` determina `SCRIPT_DIR` y `REPOSITORY_ROOT` a partir del propio checkout. Si existe `.venv/bin/python` en ese checkout, lo elige; de otro modo elige `python3` mediante `PATH`. Luego ejecuta el `scripts/quality_gate.py` del checkout con `--profile release` (`scripts/test.sh:4-16`). Esto identifica una ruta de invocación, no una identidad aprobada independientemente.

El runner importa y ejecuta lógica del checkout antes de Bubblewrap. Carga configuración y módulos desde el checkout, valida el perímetro y el manifiesto, prepara el workspace host y llama a la función de aislamiento (`quality_gate.py:569-718,1218-1245,1473-1605,1996-2023`). El worker pytest corre luego dentro de Bubblewrap; ese límite no autentica retroactivamente el supervisor y sus imports previos.

No se encontró, en las fuentes inspeccionadas, un wrapper instalado fuera del checkout con identidad/versionado verificable, un archivo de aprobación externa, un manifiesto de autorización firmado con verificador y clave ancla independientes, ni un flujo de revocación/actualización aplicable al supervisor del Quality Gate.

### 3.2. Hashes, trust root y evidencia A-PRE

- `trust_root.py` fija un SHA-256 para `tests/protected/manifest.json` y comprueba ese archivo. La constante, el verificador y el runner que los invoca pertenecen al checkout. Su alcance no cubre la autorización del propio `quality_gate.py`, del helper Bubblewrap, del intérprete host o de todos los módulos importados. La etiqueta/comentario “external” no convierte el archivo de ancla en una autoridad situada fuera del checkout.
- El manifiesto protegido enumera artefactos de pruebas protegidas, no una identidad aprobada del supervisor host.
- La especificación A-PRE requiere hashes de inputs y describe un “wrapper externo” que recogería el reporte. Sin embargo, la especificación no identifica en esas líneas una instalación, ruta canónica, owner, versión aprobada, trust anchor, autorizador o mecanismo de revocación de ese wrapper. Su estado de preflight queda `REVIEW REQUIRED / NOT READY` (`A_PRE_0_BASELINE_SPEC.md:406-475`).
- `scripts/apre_harness.py` y `scripts/verify_apre_result.py` implementan partes del harness/reporte/verificación dentro del checkout. El harness genera hashes y ejecuta el verificador (`apre_harness.py:540-705,700-820`); el verificador comprueba que los hashes reportados coincidan con archivos bajo el checkout (`verify_apre_result.py:250-315`). Esto puede detectar inconsistencias del reporte contra esos bytes observados, pero no autentica quién autorizó ejecutar el harness o el verificador, ni impide que el checkout sustituya ambos antes de la ejecución.
- Un resultado serializado fuera del checkout y un verificador separado son propiedades útiles de preservación/validación del artefacto. Por sí solos no acreditan identidad del productor, autoridad del ejecutable host, ni autenticidad de una decisión de aprobación.

**Conclusión de evidencia:** se identifican mecanismos internos de integridad y contratos de reporte, y una propuesta documental de wrapper externo. No se identifica un mecanismo externo concreto, ya desplegado y validable estáticamente, que autorice el supervisor host.

## 4. Comparación de modelos de autorización

| Modelo | Evidencia actual | Contrato que necesitaría | Evaluación |
|---|---|---|---|
| **T1 — Aprobación manual de versión identificada** | No se encontró un registro externo de aprobación de la versión del supervisor ni un proceso de aprobación asociado a este flujo. | Un responsable identificable aprueba fuera del checkout una identidad completa: supervisor, imports host, helper de aislamiento, intérprete/runtime, dependencias, política de mounts, perfil/perímetro relevante y comando. Un verificador/bootstrap confiable compara antes de ejecutar contra esa aprobación, y ejecuta la copia aprobada o evita TOCTOU entre comprobación y uso. Definir vigencia, sustitución, revocación, aprobación de versiones nuevas y registro auditable. | Diseño posible, pero no existente ni validado. Un hash calculado por el propio runner no cumple la verificación previa independiente. |
| **T2 — Harness independiente y versionado** | No se encontró un harness instalado fuera del checkout que sea parte verificable del flujo actual. La especificación A-PRE menciona un wrapper externo sin identidad/ubicación/instalación determinadas. | Harness instalado mediante canal controlado y con identidad anclada independientemente del checkout. Política fija para perfiles, nodeids, raíces protegidas, mounts, workspace y recolección. Datos del checkout se aceptan como inputs no confiables y validados; nunca como código host ejecutable. Definir quién publica, aprueba, actualiza y revoca la versión instalada, y cómo se previenen downgrade y sustitución. | Dirección plausible, pero faltan evidencia de instalación, autoridad, política, actualizaciones y capacidades concretas. |
| **T3 — Verificación mediante firma** | No se encontró manifiesto de autorización firmado para el supervisor, clave pública externa ni verificador de firmas bootstrap independiente. El hash fijo de `trust_root.py` no es una firma ni ancla independiente del checkout. | Firmar una declaración que identifique artefactos exactos y dependencias, perfiles/nodeids permitidos, scope, versión, vigencia y política. La clave privada queda bajo autoridad aprobadora identificada; la clave pública y el verificador se protegen fuera del checkout. Especificar rotación, revocación, expiración, rollback y fallos cerrados. La verificación ocurre antes de cargar/ejecutar cualquier módulo host del checkout. | Diseño posible, pero no se observó la PKI, custodia, bootstrap ni verificador necesarios. No puede afirmarse que exista o sea segura. |
| **T4 — Confianza únicamente en el checkout** | Sí existen comprobaciones internas de hashes y validación de manifiesto/perímetro. | El checkout calcula y evalúa su propio estado. No existe una autoridad distinta que limite qué runner, hash, clave, validador o resultado puede presentar. | No es autorización externa. Una modificación maliciosa o accidental del checkout puede alterar el runner, el import, la constante/hash esperado, el validador y/o el reporte; el mismo código modificado puede declarar éxito. T4 no detecta sustitución unilateral frente a una autoridad externa. |

No se selecciona T1, T2 ni T3 por inferencia. T4 queda rechazado como solución a la exigencia de confianza independiente.

## 5. Matriz de componentes y autoridad

La integridad de un input responde “¿qué bytes/configuración se consumieron?”. La autorización de ejecución responde “¿quién permitió que este componente ejecutara con esta capacidad?”. Un hash local puede apoyar la primera pregunta; no responde automáticamente la segunda.

| Componente | Uso / autoridad relevante | Clasificación requerida |
|---|---|---|
| Supervisor `scripts/quality_gate.py` | Se ejecuta en host, valida inputs, selecciona suites, crea roots/workspaces y determina el lanzamiento. | Requiere autorización host externa previa. La ruta/nombre/commit/hash producido por sí solo no la aporta. |
| `scripts/quality_gate_isolation.py` | Construye y realiza el lanzamiento Bubblewrap y define parte de los límites efectivos. | Código con autoridad host; debe estar incluido en la identidad autorizada o reemplazado por implementación confiable externa. |
| Intérprete y entorno Python host | `scripts/test.sh` prefiere `.venv` del checkout; si no, usa `python3` de `PATH`. | Identidad, versión, origen y dependencias host deben ser fijados por política independiente. El comportamiento actual no prueba entorno inmutable. |
| Imports antes de Bubblewrap | Incluyen módulos de `scripts/` y `src/` desde el checkout, entre ellos trust-root y snapshot helpers. Un import Python puede ejecutar código top-level. | Todo código cargado con autoridad host requiere autorización o debe evitarse mediante diseño. Una lista de hashes reportada por el mismo runner no basta. |
| Perfil, perímetro y configuración | Determinan suites activas/clasificación/obligaciones. El runner valida estructura/cobertura y luego recolecta (`quality_gate.py:569-718`; `test_perimeter.json`). | Inputs necesitan integridad e identidad de política verificables; el parser/agregador que les da efecto requiere autorización host. Una configuración válida sintácticamente no es aprobación. |
| Definición de mounts, roots protegidas y workspace | Decide qué ve/escribe el worker, qué se enmascara y qué autoridad conserva el host. | La implementación y política efectiva requieren autorización host. Validación de ruta en código no autorizado no es una garantía independiente. |
| Identidad checkout y observación Git | Identifica el árbol observado y, en B1-R, compara estado pre/post. | Separar autoridad del observador/Git ejecutable, identidad del checkout y autorización del runner. Estado/commit/hash describen inputs; no autorizan ejecución. |
| Worker confinado | Ejecuta pytest y código del checkout dentro de Bubblewrap con mounts limitados. | Puede ejecutar el código de tests como input no confiable dentro de los límites autorizados. Su resultado no confiere autorización host ni demuestra por sí mismo el aislamiento. |
| Verificador B1-R | Valida el reporte conforme a un contrato. La implementación actual está en el checkout. | No necesita autoridad host si corre confinada con inputs limitados; si se usa para acreditar un subresultado independiente, su identidad e independencia deben definirse. No se debe cargar arbitrariamente en host. |
| Agregador / owner de cobertura | Decide si suites/nodeids obligatorios se ejecutaron y si los subresultados cumplen el gate. Actualmente `SuiteResults` agrega items pytest por suite dentro del runner (`quality_gate.py:730-928`). | Requiere identidad autorizada y política de cobertura. Debe ser fail-closed frente a outputs de controller/worker/verifier. |

No hay evidencia estática suficiente para saber el propietario/permisos efectivos del intérprete, del checkout o de un eventual wrapper externo. Tampoco se verificó una instalación segura de dependencias. Esos puntos son precondiciones de despliegue, no supuestos.

## 6. Contrato mínimo de autorización previa a autoridad host

Una futura solución solo podría considerarse después de definir y verificar un bootstrap independiente que satisfaga como mínimo:

1. **Autoridad:** identificar persona/organización o mecanismo normativo que puede aprobar el supervisor y su alcance. Registrar decisión fuera del checkout, con identidad del aprobador, fecha/vigencia, motivo y política aplicable.
2. **Identidad exacta:** fijar una identidad de ejecución completa —código ejecutable transitivo pre-Bubblewrap, intérprete/runtime, dependencias, configuración que controla la frontera, política de perfiles y herramientas críticas— no solo el commit informado por el propio checkout.
3. **Verificador previo:** establecer un componente cuya identidad no dependa del checkout evaluado. Antes de ejecutar cualquier código suyo con permisos host, ese componente debe validar la autorización contra una raíz fuera del checkout.
4. **Vinculación check-to-use:** ejecutar los bytes aprobados o impedir cambios/sustituciones entre verificación e import/exec. Hashes calculados antes y después sin control de la copia ejecutada no resuelven por sí solos TOCTOU.
5. **Scope y capacidades:** enumerar operaciones permitidas, perfiles y nodeids; fijar raíces host, mounts, workspace, archivos de salida, ejecución de procesos y acceso a secretos. El worker no puede ampliar este scope mediante paths/comandos arbitrarios.
6. **Fail-closed:** autorización ausente, inválida, expirada, revocada, incompatible, duplicada o contradictoria produce `BLOCKED`/`ERROR`; no hay fallback al runner del checkout ni al `PATH`, modo in-process o subprocess sin Bubblewrap.
7. **Ciclo de vida:** especificar quién aprueba actualizaciones, cómo se publica una nueva identidad, cómo se revoca una anterior, cómo se detectan versiones vencidas/downgrade y dónde se conserva el registro de decisiones.
8. **Evidencia:** conservar autorización, identidad verificada, profile, checkout observado, run-id, comando, identidad de supervisor/worker, cobertura y resultados por separado, en almacenamiento cuya integridad no dependa del checkout.

STEP-19 no identifica quién es la autoridad externa, dónde estaría la raíz bootstrap, qué política aplicaría ni qué sistema revoca autorizaciones. Por ello el contrato es una lista de condiciones necesarias, no un mecanismo seleccionado o validado.

## 7. Cobertura canónica `required`

STEP-18 identifica los siguientes once nodeids. Todos pertenecen a `tests/unit` o `tests/audit`, suites clasificadas actualmente `required`. Permanecen obligatorios en los perfiles actuales `required` y `release`; no se propone modificar `config/test_perimeter.json`, mover ownership ni convertirlos en `qualification-required`.

| Nodeid canónico | Clasificación actual | Evidencia/subresultados que no deben confundirse |
|---|---|---|
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_maps_host_path_to_mounted_workspace` | `required` | Assertion de mapeo de path; no evidencia de Bubblewrap real. |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_rejects_paths_outside_workspace` | `required` | Assertion de rechazo/contención; no prueba por sí sola el launcher. |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_bubblewrap_denies_protected_paths_and_allows_derived_workspace` | `required` | Item parent y evidencia del hijo/boundary real, vinculados al mismo run. |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolation_fails_closed_when_bubblewrap_is_unavailable` | `required` | Assertion fail-closed con dependencia simulada; no prueba aislamiento positivo. |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolated_process_exit_code_is_preserved` | `required` | Exit code del proceso hijo y assertion parent; no prueba todas las propiedades de mounts. |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_active_virtual_environment_is_available_read_only_in_sandbox` | `required` | Evidencia del mount/runtime dentro del hijo y del modo esperado; nombre de ruta no prueba read-only. |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_synthetic_pytest_runs_inside_the_process_boundary` | `required` | Resultado del pytest hijo como subresultado; no cuenta como otro item parent. |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_snapshot_contract_tests_run_without_git_or_production_mounts` | `required` | Evidencia del hijo y de mounts/ausencias observadas; el exit cero aislado no demuestra todo el boundary. |
| `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_focal_binding_is_validated_inside_bubblewrap` | `required` | Binding y ejecución en boundary real; no sustituible por fake ni por resultado funcional. |
| `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_isolated_focal_runner_propagates_binding_and_writes_receipt` | `required` | Contrato de orquestación bajo fake; conservarlo como test simulado, nunca como evidencia Bubblewrap. |
| `tests/audit/test_b1_route_repeatability.py::test_synthetic_chat_route_is_repeatable_and_sterile` | `required` | Resultado funcional, artefacto/verifier, aislamiento y Git separados; secuencia en §8. |

Contrato mínimo de cobertura/agregación para cualquier etapa futura:

- Mantener un conjunto esperado derivado del perímetro autorizado por perfil; para estos once items, la obligación sigue siendo `required` en ambos perfiles actuales. La regla de `qualification-required` continúa siendo release-only y no se usa como salida para estos items.
- Cada resultado de pytest debe incluir nodeid exacto, clasificación resuelta, profile, run-id, owner/mecanismo ejecutor e identidad autorizada de supervisor y worker. Los subresultados deben añadir rol único (`worker`, `verifier`, `isolation`, `git-before`, `git-after`) y vínculo al item, no reemplazarlo.
- Una obligación `required` ausente, un duplicado, owner no autorizado, profile no aplicable, identidad incompatible, subresultado requerido ausente o error de autenticación/verificación produce `ERROR`/`BLOCKED`, nunca PASS ni “no aplicable”.
- Controlador externo y worker no se cuentan como dos ejecuciones del mismo nodeid. El hijo no satisface por sí solo el item pytest parent. Un esquema de propiedad transferida requeriría una adjudicación y cambio explícito del perímetro/agregador, no está autorizado aquí.
- Resultados incompatibles entre item pytest, worker, verifier, observación de aislamiento y Git se conservan como contradicción y bloquean la composición. No se suman exit codes para fabricar un PASS.
- Los perfiles inexistentes, no autorizados, incompletos o con clasificación/perímetro incompatible no descargan obligaciones. Actualmente `SuiteResults` agrega los nodeids recolectados por suites; no se encontró en las fuentes inspeccionadas un contrato implementado de ingestión de registros de controller/worker como sustitutos de nodeids.

## 8. Límite de confianza y contrato B1-R

La comparación vigente de B1-R es igualdad del texto reportado por `git status --porcelain --untracked-files=all` antes y después. No equivale a demostrar ausencia de escrituras transitorias, cambios ignorados o efectos externos. Los productores y consumidores necesarios son:

| Evidencia | Productor autorizado requerido | Consumidor y regla |
|---|---|---|
| Perfil, identidad del checkout y run-id | Bootstrap/política externa verificada antes de ejecutar supervisor. | Agregador valida perfil autorizado, scope, checkout y run-id. |
| Estado Git inicial y final | Observador host autorizado; mismo checkout identificado y mismo comando/scope en ambos instantes. | Comparador exige ambas observaciones válidas y compara estados reportados. Error Git nunca se convierte en estado vacío/limpio. |
| Workspace y lanzamiento | Harness/supervisor host cuya identidad esté autorizada independientemente; raíz host única, validada y vinculada al mount guest. | Launcher/consumidor valida identidad, contención y vinculación; fallo impide ejecutar o pasar. |
| Ejecución funcional | Worker Bubblewrap real con checkout limitado, sin `.git` real, roots protegidas enmascaradas, `/tmp` guest aislado y sin requests dinámicos de mounts/comandos del worker. | Owner del item valida las diez entradas y tres repeticiones por caso, observaciones normalizadas, probes/guards/counters y exit/diagnósticos. |
| Reporte y artefacto | Worker escribe únicamente en ubicación allowlisted de su workspace/run. | Recolector valida ruta/identidad/tamaño e integridad; ausente, traversal, symlink no autorizado o run mismatch bloquea. |
| Validación del artefacto | Verificador identificado separado del productor; no se acepta `TECHNICAL PASS` como autenticación del productor. | Owner del item conserva resultado/findings del verifier por separado; el resultado no demuestra aislamiento. |
| Aislamiento | Launcher/observador autorizado obtiene evidencia específica de ejecución Bubblewrap y boundary requerido. | Evaluador de aislamiento consume esa evidencia; return code cero, artefacto válido o Git igual no la sustituye. |
| Resultado compuesto del nodeid | Agregador autorizado con contrato de cobertura exacta. | El item B1-R sigue siendo owner estándar `required`; requiere resultados funcional, artefacto, aislamiento y Git enlazados por run-id y evalúa cada uno sin transferencia de autoridad. |

Si Git no puede observarse, si el worker/verifier falla, si falta aislamiento exigido o si cualquier evidencia tiene identidad/scope/run discordante, no se produce un PASS compuesto. No se ejecutó B1-R ni se afirma que este contrato esté implementado.

## 9. Decisión e incertidumbres pendientes

El análisis permite concluir que hashes, validaciones de manifiesto y reportes dentro del checkout no constituyen bootstrap de confianza independiente. También permite conservar contractualmente las once obligaciones `required`, y separar evidencia funcional, de artefacto, de aislamiento y de Git.

No permite responder sin inferencias:

1. **Quién autoriza al supervisor:** no se identificó autoridad externa o registro de aprobación vigente.
2. **Qué identidad exacta se aprueba:** no existe una identidad verificada, cerrada y aprobada para el código host transitivo, runtime/dependencias y política efectiva de mounts.
3. **Qué verifica la aprobación antes de ejecutar:** no se encontró un bootstrap/verificador independiente invocado antes de importar el supervisor.
4. **Por qué el checkout no podría sustituir verificador/autorización:** no hay evidencia de clave/raíz/verificador fuera del checkout ni de ejecución desde una copia aprobada e inmutable.
5. **Cómo se detecta autorización vencida/revocada/contradictoria:** no se identificó registro externo, formato, política de expiración, revocación o resolución de contradicciones.
6. **Cómo se integra evidencia host-side en el agregador actual:** no está implementada la ingestión compuesta de registros externos por nodeid/run-id; no se transfieren owners.
7. **Qué protege el entorno de instalación:** propiedad, permisos, canal de instalación, intérprete efectivo y dependencias del host no están verificados en esta revisión estática.

Antes de proponer implementación se requiere una decisión externa sobre T1/T2/T3, autoridad y custodia; identidad/bootstrap verificable; scope de permisos; ciclo de actualización/revocación; contrato de evidencia y cobertura; y un plan de validación autorizado que mantenga el worker aislado. La falta de estos datos permanece `UNKNOWN`, no se cubre por hashes internos, documentación o éxito de una futura ejecución.

## 10. Cierre

- **Resultado STEP-19:** `EXTERNAL_TRUST_DESIGN_PARTIAL`.
- La rama y HEAD se registraron al inicio; los conteos de paths no establecen autoría.
- Se preservaron cambios staged, unstaged y untracked preexistentes; solo se creó este expediente.
- No se ejecutaron pruebas, gate, scripts, benchmarks ni aislamiento; no hubo acceso a datos protegidos ni snapshots.
- No se autoriza implementación, pruebas, cambios de cobertura ni transición a P1.3.

**Estado final obligatorio:** `P1.2 = BLOCKED-REGRESSION`.
