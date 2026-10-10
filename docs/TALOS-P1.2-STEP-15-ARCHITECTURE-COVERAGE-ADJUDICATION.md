# TALOS-P1.2-STEP-15 — ADJUDICACIÓN DE ARQUITECTURA Y COBERTURA

**Entrada:** `HARNESS_CONTRACT_DESIGNED`  
**Estado canónico:** `P1.2 = BLOCKED-REGRESSION`  
**Tipo:** revisión y adjudicación estática; sin implementación ni pruebas  
**Salida:** `A1_COVERAGE_PARTIAL`

## 1. Estado del repositorio

- Rama observada: `talos-current-audit`.
- HEAD observado: `cc8acfae623f9d10c8366871470319786b6a7ca4`.
- Worktree sucio al inicio: 1.863 paths con cambio en el índice, 23 con cambio en el worktree y 65 paths untracked, según `git status --porcelain=v1`. Los cambios se preservaron; no se atribuye autoría por estos conteos.
- `docs/TALOS-P1.2-STEP-15-ARCHITECTURE-COVERAGE-ADJUDICATION.md` no existía al iniciar.
- No se modificaron código, tests, configuración ni expedientes previos. Este expediente es el único archivo creado en la fase.

## 2. Archivos y contratos inspeccionados

- `scripts/quality_gate.py`: selección de suites, `--basetemp`, preparación y lanzamiento del worker.
- `scripts/quality_gate_isolation.py`: `_validate_mount_roots()`, `workspace_guest_path()` y mounts Bubblewrap.
- `config/test_perimeter.json`: clasificación de `tests/audit` y `tests/unit` como suites requeridas.
- `tests/unit/diagnostics/test_quality_gate_isolation.py`: tests de mapeo y procesos aislados.
- `tests/unit/diagnostics/test_quality_gate_focal_execution.py`: validación focal real en Bubblewrap y prueba focal con runner simulado.
- `tests/audit/test_b1_route_repeatability.py`: prueba de repetibilidad, artefacto y estado Git.
- `docs/TALOS-P1.2-STEP-13-STATIC-NESTED-WORKSPACE-ADJUDICATION.md`.
- `docs/TALOS-P1.2-STEP-14-HARNESS-ISOLATION-CONTRACT-DESIGN.md`.

El inventario estático de callers encontró `run_isolated_process()` en el runner principal de `scripts/quality_gate.py` y en los siete sitios de test identificados en STEP-13. No apareció otro caller productivo en `scripts/` que establezca una vía separada para estos nodeids.

## 3. Hechos del flujo y alcance de A1

1. El runner principal crea `execution_root` en un `TemporaryDirectory` bajo `/tmp` del host, configura `TALOS_TEST_BASETEMP=/workspace/run/pytest-tmp` y llama `run_isolated_process()` para iniciar el worker.
2. Bubblewrap monta el checkout read-only en `/workspace/repository`, el workspace host writable en `/workspace/run`, y crea un `/tmp` guest independiente mediante `--tmpfs /tmp`.
3. Dentro del worker, el `tmp_path` de pytest se deriva de `/workspace/run/pytest-tmp`; es guest, no una ruta host bajo `/tmp`.
4. `_validate_mount_roots()` valida en el namespace del caller que `workspace_root` sea un directorio host existente bajo `/tmp`, sin symlink ni solapamiento con el checkout. No convierte guest paths en host paths.
5. `run_gate()` selecciona las suites `required` y, para `release`, las `qualification-required`; el perfil completo pasa los paths de suite a pytest en el worker. El perímetro clasifica `tests/unit` y `tests/audit` como `required`, por lo que los nodeids de esta adjudicación se ejecutan en ese worker en el flujo actual.
6. El contrato A1 de STEP-14 puede eliminar el lanzamiento anidado desde un worker solo si un controlador con autoridad host crea/valida el workspace y lanza el proceso que debe aislarse. Ejecutar tests controladores en el host sería una modalidad nueva: el código inspeccionado no tiene un selector host-side para esos nodeids ni demuestra el control de confianza/privilegios de ese proceso.

Por tanto, hay que separar:

```text
COMPATIBILIDAD DE LA PROPIEDAD CON A1
    ≠
COBERTURA YA INTEGRADA EN EL QUALITY GATE
    ≠
AISLAMIENTO DEMOSTRADO EN EJECUCIÓN
```

Los estados `COMPATIBLE` de la matriz son condicionales a una adjudicación explícita de ejecución host-side para el test controlador, con workspace host creado y validado por el harness. No afirman que esa ruta exista ni que haya sido probada. `UNRESOLVED` indica que las fuentes estáticas no demuestran que la propiedad pueda mantenerse dentro del contrato A1 actual sin decisiones adicionales.

## 4. Separación contractual de resultados

Una ejecución futura compatible con A1 debería conservar registros distintos, ligados por identificador de run:

```text
HOST HARNESS
  ├── workspace host autorizado bajo /tmp
  ├── validación host de roots y preparación de mounts
  ├── ejecución del worker Bubblewrap
  ├── resultado de proceso: exit code, stdout/stderr
  ├── artefactos permitidos recogidos desde el workspace
  └── observación Git host-side inicial/final, cuando sea requisito

WORKER AISLADO
  ├── ejecución funcional del nodeid/probe
  ├── evidencia producida dentro del contrato
  └── sin acceso al .git real ni autoridad para elegir workspace host
```

La evidencia funcional de un worker no certifica aislamiento. La evidencia de aislamiento debe provenir de las assertions específicas del proceso/boundary. La observación Git debe leer el checkout host-side y compararse antes/después; no debe fingir que el worker ve `.git`, ni ser sustituida por un mock. Una falta de acceso/error de Git no equivale a un checkout sin cambios.

Para conservar exactamente los nodeids, un futuro plan debe decidir cómo se seleccionan desde el host y cómo se agregan sus resultados al gate; moverlos sin contabilización explícita podría reducir el perímetro requerido sin que el gate lo advierta.

## 5. Matriz de adjudicación

Las filas `COMPATIBLE` expresan viabilidad conceptual en A1 únicamente si el host ejecuta el controlador del test con una identidad de workspace host real y el test conserva sus assertions. En ningún caso equivalen a implementación o validación.

| Nodeid exacto | Propiedad y assertions que deben conservarse | Proceso orquestador propuesto | Workspace y autoridad | Evidencia Git requerida | Compatibilidad conceptual con A1 | Cambios hipotéticos (no aplicados) | Riesgo residual | Estado |
|---|---|---|---|---|---|---|---|---|
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_maps_host_path_to_mounted_workspace` | Mapeo host workspace → `/workspace/run/...`; mantener el resultado exacto `/workspace/run/pytest-tmp`. El path de entrada debe ser host, no `tmp_path` guest. | Harness host ejecuta el nodeid controlador, fuera del worker estándar. | `tmp_path` debe ser creado por pytest host bajo `/tmp`; el harness es dueño del workspace. No aceptar guest path como identidad host. | No requerida por el test. Si se ejecuta el nodeid fuera del worker, cualquier baseline Git es responsabilidad separada del harness, no de este test. | Sí, bajo el host-controller explícito. En el worker actual, solo valida una transformación de strings/paths guest y no acredita identidad host. | Perímetro/plan de suites para ejecución host-side; eventualmente identidad explícita del test. | Host execution de tests necesita una frontera de confianza y permisos definidos; el gate no tiene hoy esa vía separada. | `COMPATIBLE` |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_rejects_paths_outside_workspace` | Rechazo explícito con `IsolationError` si el path no está contenido en el workspace. | Harness host ejecuta el nodeid controlador. | Dos paths host hermanos creados bajo `/tmp`; validador del helper debe rechazar el externo al workspace, no traducirlo. | No requerida por el test. | Sí, condicionado a host-side pytest para que las rutas modelen realmente inputs host. | Igual que fila anterior; conservar assertion de excepción/mensaje. | El caso actual no demuestra symlinks ni la política completa de `_validate_mount_roots()`. | `COMPATIBLE` |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_bubblewrap_denies_protected_paths_and_allows_derived_workspace` | Mantener todos los rechazos de lectura/apertura/escritura/SQLite sobre roots protegidos y alias; denegación de symlink/traversal/unmount; capabilities cero; secreto ausente; workspace derivado writable; hashes/sidecars de origen sin cambios; namespaces distintos. | Harness host ejecuta el controlador y este lanza un único worker Bubblewrap para el probe. No hay segundo worker anidado desde el gate worker. | Repositorio y datos son sintéticos, creados bajo `tmp_path` host; workspace host validado bajo `/tmp`, bind limitado a `/workspace/run`. | El test compara hashes de sus datos sintéticos; no requiere `.git`. No sustituye observación Git global del checkout. | Sí, el cuerpo ya define un worker aislado y datos sintéticos. A1 puede darle workspace host desde el padre; no se requiere traducción guest→host. | Selección host-side explícita del nodeid; mantener probe, resultado y assertions completos. | El controlador ejecutado en host conserva capacidad host mientras prepara/lanzamiento; su privilegio y alcance no están definidos. | `COMPATIBLE` |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolation_fails_closed_when_bubblewrap_is_unavailable` | Cuando `shutil.which("bwrap")` no encuentra Bubblewrap, debe lanzarse `IsolationError` con “bubblewrap is unavailable”; no debe haber éxito/fallback. | Harness host ejecuta el controlador, que monkeypatchea el lookup y llama el validador. | Repository/workspace sintéticos host bajo `/tmp`; la comprobación de root debe pasar antes de llegar al caso monkeypatcheado. | No requerida. | Sí, si el controlador se ejecuta host-side; en el gate worker actual el workspace guest no satisface primero el requisito host `/tmp`. | Selección host-side; preservar tanto el orden de fail-closed como la assertion exacta de error. | La prueba simula ausencia del ejecutable mediante monkeypatch; no demuestra por sí sola el comportamiento real del entorno. | `COMPATIBLE` |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolated_process_exit_code_is_preserved` | El hijo que sale con código 23 debe regresar `returncode == 23`; no colapsar error/código en éxito. | Harness host ejecuta el controlador y lanza el child Bubblewrap. | Workspace temporal host bajo `/tmp`, propiedad del harness; workspace writable child limitado al bind autorizado. | No requerida. | Sí, conceptualmente, porque el test valida el resultado del hijo aislado y A1 puede ser dueño de la raíz host. | Selección host-side; mantener caso de salida 23 y la política de Bubblewrap ausente. | El test depende del runtime real de Bubblewrap; esta inspección no lo ejecutó. | `COMPATIBLE` |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_active_virtual_environment_is_available_read_only_in_sandbox` | El proceso aislado debe poder importar pytest y escribir `runtime.txt` solo en el workspace; salida empieza con `/opt/talos-venv:`. | Harness host ejecuta el controlador y lanza el child Bubblewrap. | Workspace host bajo `/tmp`; virtualenv se monta read-only según el runner. El test no debe convertir su `tmp_path` guest en raíz de otro launch. | No requerida. | Sí, conceptualmente, con ejecución del controlador host-side y child bajo el boundary actual. | Selección host-side y preservación de assertion de runtime; no ampliar mounts. | La disponibilidad del virtualenv y mounts reales requiere verificación dinámica posterior autorizada. | `COMPATIBLE` |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_synthetic_pytest_runs_inside_the_process_boundary` | Pytest hijo debe pasar el test sintético; las rutas de DB protegida real y montada deben fallar read/write/SQLite; DB derivada debe ser writable; fingerprint del origen sintético no cambia. | Harness host ejecuta el controlador; el controlador crea fixture sintético en workspace host y lanza pytest hijo aislado. | Repository, DB sintética, test y workspace host bajo `/tmp`; el child ve `/workspace/run` y checkout/roots según contrato. | Fingerprint de la fuente sintética preservado. No depende de Git. | Sí, el subprocess pytest ya es el boundary objeto de la propiedad; trasladar el controlador al host evita anidar namespaces. | Selección host-side; preservar contenido del test generado, nodeid interno, asserts del resultado y fingerprint. | Se desconoce cómo contabilizar el subtest y el controlador dentro de la suite required; sin reporte explícito podría perderse cobertura. | `COMPATIBLE` |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_snapshot_contract_tests_run_without_git_or_production_mounts` | pytest hijo sobre `test_test_isolation_snapshots.py` debe pasar con checkout sin `.git` y roots productivos enmascarados; mantener propagación de stdout/stderr y exit code. | Harness host calcula identidad inicial y ejecuta el nodeid controlador; este lanza pytest en Bubblewrap read-only sobre el checkout. | Workspace temporal host bajo `/tmp`; checkout real read-only; `.git` y roots protegidos enmascarados para pytest hijo. `_repository_identity()` del controlador se calcula host-side. | El proceso hijo no necesita Git real; el controlador puede consultar la identidad/estado del checkout host si el contrato del gate lo exige. | Sí, conceptualmente, preservando que el test snapshot corre dentro de un boundary real y no bajo un fake. | Selección host-side y agregación del resultado del pytest hijo como salida del nodeid padre; mantener tests snapshot completos. | Debe definirse si una salida `1 passed/...` del pytest hijo es evidencia del nodeid padre o reporte separado; no hay contrato actual de agregación. | `COMPATIBLE` |
| `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_focal_binding_is_validated_inside_bubblewrap` | La validación debe ocurrir en un proceso Bubblewrap real; preservar igualdad de `nodeid`/`run_id` y namespaces mount/net/pid distintos del host. Los inputs son manifiesto/binding sintéticos. | Harness host crea inputs y workspace, después lanza el worker hijo. | `tmp_path` host bajo `/tmp`; workspace host derivado; checkout read-only y paths focales canónicos en `/workspace/run`. No se usa snapshot B06 real. | El test usa identidad de checkout y hashes sintéticos; Git observable, si se exige como guard global, corresponde al host y no al worker. | Sí, el test ya define el proceso aislado objeto; A1 puede eliminar la anidación cambiando el proceso que ejecuta el controlador, sin reducir la assertion de namespace. | Ejecución host-side específica y captura host de identidad del repo; conservar el child real y todas las assertions. | La selección host-side de este test focal, y su compatibilidad con perfiles `required`/`release`, no está expresada en el perímetro actual. | `COMPATIBLE` |
| `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_isolated_focal_runner_propagates_binding_and_writes_receipt` | Mantener validación/derivación/verify en orden, captura de comando y env, receipt focal, digest, nodeid, binding, `exactly_one` y secuencia de eventos. El fake no debe declararse prueba de aislamiento real. | Puede continuar como pytest en el worker estándar; el monkeypatch intercepta `run_isolated_process()` y no intenta crear un child Bubblewrap. | Sus archivos `tmp_path` son artefactos de test guest; no se pasan como `workspace_root` al validador real. | No requiere consultar el `.git` real; usa repositorio sintético monkeypatcheado/identidad simulada según el test. | Sí para la cobertura de orquestación/unidad. No es evidencia del proceso Bubblewrap; esa propiedad queda en el nodeid focal anterior. | Ningún cambio es necesario para la contradicción nested específica; cualquier clasificación/reporting debe mantener separado fake/unit de real isolation. | La assertion de receipt indica mecanismo nominal, no demuestra aislamiento. No agrupar su pass con el resultado de aislamiento real. | `COMPATIBLE` |
| `tests/audit/test_b1_route_repeatability.py::test_synthetic_chat_route_is_repeatable_and_sterile` | Mantener tres repeticiones, resultado funcional del subprocess, existencia/validación independiente del artefacto y assertion de que `_git_status(repo_root)` antes/después es igual. | A1 puede asignar al harness host la captura Git pre/post y el control del child; no puede dejar la observación a un pytest worker al que se le enmascara `.git`. | El repo apunta al checkout real; los directorios child son host `tmp_path` hoy. Si el child se aísla bajo A1, necesitaría checkout guest read-only y outputs en workspace host autorizado, con path identities explícitas. | Sí: observación Git inicial/final del checkout host exacto, incluyendo untracked; error de Git o estado no comparable debe fallar/bloquear, no significar “sin cambios”. | No se determina que A1, tal como está especificado y actualmente implementado, preserve simultáneamente el límite del child y la assertion Git. Un controlador host podría hacerlo, pero el test usa `subprocess.run()` directo, no Bubblewrap; no se identifica un mecanismo A1 existente para separar Git host-side del child y correlacionar sus outputs. | Podrían requerirse ejecución host-side del controlador, lanzamiento del worker a través del harness, workspace/output mapping y captura Git host-side. No omitir ni mockear `_git_status()`. | Correr código de test/subprocess con visibilidad host presenta riesgo si no se confina; envolver el child podría cambiar semántica. Falta decidir si Git-delta es solo observación post hoc o si el child debe tener checkout read-only. | `UNRESOLVED` |

## 6. Lectura de la cobertura y decisión sobre A1

### 6.1. Qué demuestra la inspección estática

- Los seis nodeids de aislamiento con `_validate_mount_roots()` y el nodeid focal real dependen hoy de workspaces derivados de `tmp_path`; bajo Quality Gate esos paths son guest. El validador espera host `/tmp`, por lo que no se puede tomar el flujo actual como compatible.
- A1 ofrece una salida conceptual para esas assertions: ejecutar el controlador en un proceso host autorizado, con `tmp_path` host bajo `/tmp`, y que ese controlador lance exactamente el proceso/probe Bubblewrap esperado. Las assertions funcionales de los hijos podrían permanecer intactas. Esto no requiere montar el `/tmp` host dentro del guest ni traducir guest→host.
- Las dos pruebas de `workspace_guest_path()` también obtienen semántica host real solo cuando sus inputs se crean en el host.
- La prueba focal simulada no requiere launch anidado, pero sigue siendo una prueba de orquestación/unidad, no una demostración de aislamiento.
- B1-R requiere mantener dos observaciones separadas: worker funcional/artefacto y estado Git del checkout host. STEP-13 documenta la consulta Git dentro de pytest worker; el `.git` real está enmascarado ahí. El código del test usa subprocesses directos y la evidencia inspeccionada no demuestra cómo A1 podría controlar de forma segura esos procesos y, a la vez, atribuir la comparación Git al host.

### 6.2. Por qué A1 no queda aceptada como cobertura completa

El Quality Gate no tiene una fase o lista de nodeids host-side: `run_gate()` elige suites requeridas y corre pytest dentro del worker. Cambiar algunos nodeids a ejecución host-side afecta la confianza y la cobertura:

- Si pytest controlador corre en host, los tests ejecutan código del checkout con visibilidad host; no está documentado un allowlist/control de confianza ni una frontera para ese controlador.
- Si se ejecuta el test completo en el guest, vuelve el conflicto de namespace y B1 no puede consultar el `.git` real.
- Si se crea un driver separado o un harness específico, falta definir cómo conserva el nodeid, las assertions, el resultado del pytest hijo y la contabilidad en el gate; esa opción empieza a requerir la decisión/harness de A3 u otra extensión explícita de A1.

Por ello, A1 puede preservar conceptualmente la mayoría de las propiedades si se autoriza un controlador host con límites explícitos. La evidencia estática actual no demuestra que esa modalidad sea segura ni que conserve automáticamente el conjunto de nodeids required. B1-R además necesita diseño de ejecución para distinguir aislamiento del worker y Git host-side sin cambiar silenciosamente la propiedad. La arquitectura A1 queda **parcialmente adjudicada**, no aprobada.

## 7. Cambios hipotéticos por archivo (no aplicados)

- `scripts/quality_gate.py`: hipotéticamente podría requerir un plan de ejecución que seleccione/registre nodeids controladores fuera del worker y agregue sus resultados al mismo gate sin omitirlos del perímetro.
- `scripts/quality_gate_isolation.py`: solo si el contrato seleccionado requiere que el host controle esos launches; no relajar `_validate_mount_roots()`, ni aceptar guest paths, ni ampliar binds.
- `config/test_perimeter.json`: solo mediante decisión explícita de clasificación/selección, preservando que todos los nodeids requeridos siguen gateados.
- `tests/unit/diagnostics/test_quality_gate_isolation.py`: potencial ajuste futuro para expresar claramente los casos host-controller y conservar cada assertion de aislamiento.
- `tests/unit/diagnostics/test_quality_gate_focal_execution.py`: mantener separada la prueba focal real de la prueba de propagación simulada; cualquier cambio debe preservar binding/receipt assertions.
- `tests/audit/test_b1_route_repeatability.py`: eventual separación explícita de worker funcional, artefacto/verificador y observación Git host-side. No borrar ni mockear `_git_status()`; no cambiar el significado del delta Git sin decisión.
- Documentación contractual del Quality Gate/harness: ownership, confianza del controlador host, nodeids, evidencia y reglas de bloqueo.

El listado es inventario conceptual, no instrucciones de edición ni autorización para modificar esos archivos.

## 8. Decisiones explícitas y evidencia faltante

1. **Controlador host:** determinar si se autoriza ejecutar nodeids controladores de código del repositorio en host, con qué identidad/privilegios, allowlist exacta y protección frente a side effects. Sin esto, los nodeids marcados `COMPATIBLE` solo lo son conceptualmente.
2. **Cobertura del gate:** especificar cómo se seleccionan y reportan nodeids host-side y cómo se prueba que el mismo conjunto `required` sigue cubierto. El perímetro actual incluye directorios, no un contrato de fase host-side.
3. **B1-R:** decidir si el proceso funcional debe tener checkout read-only y workspace de outputs separado, cómo el host captura el estado Git antes/después y qué resultado se emite si no puede observar Git.
4. **Subpytest:** definir cómo se relaciona el resultado de un pytest hijo con el nodeid padre y con el reporte agregado del gate, sin elevar `TEST_PASS` a evidencia de aislamiento.
5. **Alcance del run:** determinar cómo el harness host coordina suites y runners focales `required`/`release` y mantiene identidad de commit, bindings y policy.
6. **Validación posterior:** cualquier evidencia de funcionamiento Bubblewrap/pytest necesita autorización y fase separada; este expediente no la suple.

## 9. Estado de salida

- **Resultado:** `A1_COVERAGE_PARTIAL`.
- A1 presenta un patrón conceptual plausible para los tests que requieren lanzar un worker: el host conserva ownership del workspace y controla el launch. No se ha demostrado su integración segura ni la contabilidad completa de nodeids en el gate actual.
- B1-R queda `UNRESOLVED` respecto a si A1 puede conservar el límite del subprocess y la verificación Git sin una decisión de harness adicional.
- No se autoriza STEP-16, implementación, ejecución de pruebas ni reapertura del Quality Gate.
- No se ejecutaron `pytest`, nodeids, `scripts/test.sh`, Quality Gate, scripts de preparación, benchmarks ni pruebas de aislamiento.
- No se accedió a bases protegidas ni se crearon snapshots.
- No se hizo staging, commit, reset, checkout ni limpieza del worktree.
- No se modificó código, tests, configuración ni expedientes previos.

**Estado canónico obligatorio:** `P1.2 = BLOCKED-REGRESSION`
