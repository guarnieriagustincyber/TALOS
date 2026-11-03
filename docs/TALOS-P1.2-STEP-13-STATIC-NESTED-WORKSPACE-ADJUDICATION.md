# TALOS-P1.2-STEP-13 — ADJUDICACIÓN ESTÁTICA DE WORKSPACES ANIDADOS

**Entrada:** `STATIC_REVIEW_PARTIAL`  
**Gate:** `P1.2 = BLOCKED-REGRESSION`  
**Tipo:** inspección estática  
**Salida:** `NESTED_WORKSPACE_CONTRACT_CONTRADICTION_FOUND`

## 1. Estado del repositorio

- Rama observada: `talos-current-audit`, coincide con la esperada.
- HEAD observado: `cc8acfae623f9d10c8366871470319786b6a7ca4`, coincide con el esperado.
- El worktree está sucio, con cambios staged, unstaged y untracked preexistentes. Se preservaron.
- `docs/TALOS-P1.2-STEP-13-STATIC-NESTED-WORKSPACE-ADJUDICATION.md` no existía antes de esta fase.
- No se hicieron modificaciones a código, tests, configuración o expedientes anteriores.

## 2. Archivos inspeccionados

- `scripts/quality_gate_isolation.py`
- `scripts/quality_gate.py`
- `tests/conftest.py`
- `tests/unit/diagnostics/test_quality_gate_isolation.py`
- `tests/unit/diagnostics/test_quality_gate_focal_execution.py`
- `docs/TALOS-P1.2-STEP-11-WORKSPACE-GUEST-PATH.md`
- `docs/TALOS-P1.2-STEP-12-STATIC-REVIEW.md`
- Inventario estático de todos los callers de `run_isolated_process()` y `workspace_guest_path()` bajo `scripts/` y `tests/`.

## 3. Diagrama de fronteras host/guest

### Ejecución normal del Quality Gate

```text
Proceso host del runner
  TemporaryDirectory(dir="/tmp")
    └── execution_root
          ├── pytest-tmp
          └── test-data
  run_isolated_process(workspace_root=execution_root)
    └── Bubblewrap:
          --tmpfs /tmp                         # /tmp nuevo del worker
          --bind <host execution_root> /workspace/run
          --ro-bind <checkout> /workspace/repository

Proceso worker dentro de Bubblewrap
  TALOS_TEST_BASETEMP=/workspace/run/pytest-tmp
    └── pytest --basetemp=/workspace/run/pytest-tmp
          └── tmp_path, por ejemplo:
                /workspace/run/pytest-tmp/test_case0
```

El `tmp_path` creado por pytest en esta fase es una **ruta guest** del worker. No es una ruta host bajo `/tmp`; que exista el bind `/workspace/run` no cambia el nombre ni la identidad de namespace de esa ruta.

### Intento de aislamiento anidado dentro de un test

```text
Worker pytest:
  tmp_path = /workspace/run/pytest-tmp/test_case0       # guest
  workspace = tmp_path / "execution"                    # guest
  run_isolated_process(..., workspace_root=workspace)
    └── _validate_mount_roots(..., workspace_root)
          └── requiere workspace_root.is_relative_to("/tmp")
                └── /workspace/run/... no satisface esa condición
```

El validador se ejecuta en el proceso llamante y resuelve la ruta en su filesystem visible; no traduce rutas guest a identidades host. El acceso a Bubblewrap solo se intenta después de `_validate_mount_roots()`.

## 4. Contrato reconstruido

### Rutas y variables

- `scripts/quality_gate.py:1473-1480`: el runner anfitrión crea un directorio temporal bajo `/tmp`, luego `execution_root` y `execution_root/pytest-tmp`.
- `scripts/quality_gate.py:1571-1579`: calcula `pytest_guest_tmp_root` con `workspace_guest_path()` y configura `TALOS_TEST_BASETEMP`.
- `scripts/quality_gate.py:1024-1026`: el worker usa ese valor como `--basetemp`.
- `scripts/quality_gate.py:1595-1598`: el runner pasa `execution_root` host a `run_isolated_process()`.
- `scripts/quality_gate_isolation.py:48-49,296-305`: `/workspace/run` es el punto guest del bind writable; `/tmp` dentro del worker es un tmpfs separado.
- `scripts/quality_gate_isolation.py:63-86`: `_validate_mount_roots()` exige workspace existente, directorio, no symlink, bajo `/tmp` y sin solapamiento con el checkout.
- `scripts/quality_gate_isolation.py:91-101`: `workspace_guest_path()` traduce un path host relativo al workspace al punto de montaje guest.

### Implicación

El helper de STEP-11 corrige el path de `pytest-tmp` del runner principal. No convierte los directorios de `tmp_path` generados por pytest dentro del worker en directorios host ni autoriza usarlos como `workspace_root` de un segundo `run_isolated_process()`. No hay en el código inspeccionado una traducción inversa guest→host o una política distinta para workers anidados.

## 5. Matriz de adjudicación

Los resultados siguientes se refieren al caso en que esos tests se ejecuten dentro del worker del Quality Gate, que recibe `TALOS_TEST_BASETEMP=/workspace/run/pytest-tmp`. Si se ejecutaran directamente en un pytest anfitrión no aislado, `tmp_path` podría estar bajo `/tmp`; ese contexto distinto no corrige la incompatibilidad dentro del gate.

| Test/nodeid | Proceso de origen y `tmp_path` | Ruta entregada / tipo | Validador invocado | Mount esperado | Resultado estático | Evidencia | Riesgo |
|---|---|---|---|---|---|---|---|
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_bubblewrap_denies_protected_paths_and_allows_derived_workspace` | pytest dentro del worker; `tmp_path` proviene del `--basetemp` guest de pytest | `workspace=tmp_path/"execution"`; guest `/workspace/run/pytest-tmp/.../execution` | `run_isolated_process()` → `_validate_mount_roots()` | Pretende montar workspace como `/workspace/run`, pero la validación host exige `/tmp` antes del mount | `INCOMPATIBLE` en gate | test `:50-109,269-273`; runner `quality_gate.py:1571-1598`; validador `quality_gate_isolation.py:63-86,211-214` | Rechazo de raíz antes de comprobar las denegaciones de paths |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolation_fails_closed_when_bubblewrap_is_unavailable` | pytest dentro del worker; `tmp_path` guest | `workspace=tmp_path/"execution"`; guest | `run_isolated_process()` → `_validate_mount_roots()` antes de `shutil.which("bwrap")` | No llega al mount; el test espera el error por Bubblewrap ausente | `INCOMPATIBLE` en gate | test `:333-352`; orden de validación `quality_gate_isolation.py:211-225` | Obtiene primero error de raíz fuera de `/tmp`, no el mensaje esperado de Bubblewrap |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolated_process_exit_code_is_preserved` | pytest dentro del worker; `tmp_path` guest | `workspace=tmp_path/"execution"`; guest | `_validate_mount_roots()` | Espera bind writable del workspace al worker anidado | `INCOMPATIBLE` en gate | test `:354-370`; validator `quality_gate_isolation.py:63-86` | Se detiene en la política host `/tmp`, antes de propagar exit code |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_active_virtual_environment_is_available_read_only_in_sandbox` | pytest dentro del worker; `tmp_path` guest | `workspace=tmp_path/"execution"`; guest | `_validate_mount_roots()` | Espera bind de workspace anidado | `INCOMPATIBLE` en gate | test `:372-395`; validator `quality_gate_isolation.py:63-86` | No alcanza a inspeccionar el runtime dentro de Bubblewrap |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_synthetic_pytest_runs_inside_the_process_boundary` | pytest exterior crea `tmp_path` guest; el test crea archivos allí y solicita otro proceso aislado | `workspace=tmp_path/"execution"`; guest | `_validate_mount_roots()` | Espera que el directorio de ejecución se monte como `/workspace/run` en el worker anidado | `INCOMPATIBLE` en gate | test `:397-440`; validador `quality_gate_isolation.py:63-86` | No alcanza a ejecutar el pytest sintético |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_snapshot_contract_tests_run_without_git_or_production_mounts` | pytest dentro del worker; `tmp_path` guest | `workspace=tmp_path/"execution"`; guest | `_validate_mount_roots()` | Espera mount workspace anidado; checkout se entrega como repositorio read-only | `INCOMPATIBLE` en gate | test `:463-483`; validador `quality_gate_isolation.py:63-86` | No alcanza a probar el aislamiento del test de snapshot |
| `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_focal_binding_is_validated_inside_bubblewrap` | pytest dentro del worker; `tmp_path` guest | `execution_root=tmp_path/"execution"` se pasa como `workspace_root`; guest | `run_isolated_process()` → `_validate_mount_roots()` | Espera bind de ese execution root a `/workspace/run` | `INCOMPATIBLE` en gate | test `:667-706,768-773`; validador `quality_gate_isolation.py:63-86` | No alcanza a comprobar binding ni namespaces |
| `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_isolated_focal_runner_propagates_binding_and_writes_receipt` | pytest dentro del worker; `tmp_path` guest | La prueba usa `tmp_path` para inputs/output; reemplaza `run_isolated_process()` por `fake_isolated_process` | No invoca el validador real en el bloque fake | No hay mount anidado real en esta prueba | `COMPATIBLE` respecto del conflicto específico; mock no prueba aislamiento anidado | test `:785-930` | No valida Bubblewrap ni la ruta host/guest; no debe interpretarse como prueba de aislamiento |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_maps_host_path_to_mounted_workspace` | pytest dentro del worker; `tmp_path` guest | `workspace=tmp_path/"execution"` y `pytest_tmp` hijo; ambos guest | `workspace_guest_path()` solamente | Devuelve ruta bajo `/workspace/run`; no lanza proceso | `COMPATIBLE` como test del cálculo relativo; no prueba host mapping | test `:26-35`; helper `quality_gate_isolation.py:91-101` | En el worker prueba una operación sobre paths guest con el mismo helper; no demuestra identidad host |
| `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_rejects_paths_outside_workspace` | pytest dentro del worker; `tmp_path` guest | `workspace` e `outside` hermanos dentro de `tmp_path`; guest | `workspace_guest_path()` solamente | No hay mount ni invocación de `run_isolated_process()` | `COMPATIBLE` como caso de contención relativa | test `:38-47`; helper `quality_gate_isolation.py:91-101` | No cubre conversión de guest a host ni mount |
| `tests/audit/test_b1_route_repeatability.py::test_synthetic_chat_route_is_repeatable_and_sterile` (patrón contextual citado en STEP-12) | pytest host/worker; subprocess funcional con cwd/HOME/TMPDIR temporales; `tmp_path` contiene artefactos | El subprocess recibe repo root como argumento de datos; no llama `run_isolated_process()` | Git status se ejecuta por `_git_status()` en el proceso pytest | El child funcional no recibe `.git`; el proceso pytest del Quality Gate tampoco ve el `.git` real, enmascarado por el sandbox | `INCOMPATIBLE` para verificación Git dentro del Quality Gate; no es un workspace anidado | test `:30-108,111-125`; sandbox en `quality_gate_isolation.py:399-426` | La verificación del checkout no se traslada a un harness host externo al worker; no modificar ni omitir esa propiedad |

## 6. Proceso responsable de verificar resultados

- En los seis tests de `test_quality_gate_isolation.py` y el test focal de Bubblewrap, el proceso pytest dentro del worker intenta iniciar un segundo boundary. El validador corre en ese mismo proceso guest y recibe un path guest derivado de `tmp_path`.
- `test_isolated_focal_runner_propagates_binding_and_writes_receipt` reemplaza la función de aislamiento por un fake. Su verificación de llamada/artefactos no demuestra un mount real.
- En B1-R, la ruta funcional se ejecuta en un subprocess temporal (`test_b1_route_repeatability.py:58-73`), pero las consultas Git antes y después (`:56,106-108`) se hacen desde el proceso que ejecuta pytest. Dentro del worker del Quality Gate ese proceso no tiene el `.git` original. La verificación del estado del repositorio debe conservarse como propiedad separada; esta inspección no cambia el test ni adjudica una nueva autorización de harness.

## 7. Adjudicación H1–H6

| Hipótesis | Estado | Evidencia y alcance |
|---|---|---|
| H1: el test entrega una ruta guest donde se espera host | `SUPPORTED` | Dentro del Quality Gate, `--basetemp` es `/workspace/run/pytest-tmp`; los tests usan `tmp_path` para crear el workspace y lo pasan a `run_isolated_process()`. Ese validador interpreta su argumento en el namespace del proceso llamante y exige `/tmp`. |
| H2: `tmp_path` se crea bajo una raíz que no satisface la política host `/tmp` | `SUPPORTED` | `quality_gate.py:1575,1024-1026` configura basetemp guest; pytest `tmp_path` deriva de ese basetemp. El path `/workspace/run/...` no es descendiente de `/tmp`. |
| H3: el test intenta anidar un workspace/worker incompatible con el contrato | `SUPPORTED` | Los tests listados invocan `run_isolated_process()` desde el worker y entregan un workspace construido desde `tmp_path`; el runner del nested worker vuelve a requerir un directorio host bajo `/tmp`. |
| H4: el test mezcla comprobaciones del worker con una comprobación de harness que requiere checkout/Git | `SUPPORTED` para B1-R | B1-R ejecuta Git antes/después desde el proceso pytest (`:56,106-125`), no dentro del subprocess funcional. En el Quality Gate ese proceso pytest se encuentra en el worker, donde `.git` se enmascara (`quality_gate_isolation.py:399-426`). No se adjudica aquí cómo debe reestructurarse el harness. |
| H5: STEP-11 no cubre todos los patrones de invocación existentes | `SUPPORTED` | STEP-11 traduce el `pytest-tmp` del runner principal. El helper no traduce rutas guest de `tmp_path` a rutas host para nested workers; sus dos nuevos tests solo comprueban contención/mapeo del helper y no invocan aislamiento anidado. |
| H6: la evidencia no permite decidir entre las hipótesis | `REJECTED` para la contradicción de ruta en los casos directos enumerados; `SUPPORTED` para comportamiento dinámico | Las fuentes estáticas bastan para demostrar el desajuste de namespace y el rechazo por la condición `/tmp`. No permiten afirmar resultados dinámicos de Bubblewrap/pytest ni proponer sin aprobación una arquitectura alternativa. |

## 8. Invariantes de seguridad

| Invariante | Estado estático | Evidencia |
|---|---|---|
| Checkout en solo lectura | Conservado | `quality_gate_isolation.py:300-305` usa `--ro-bind` para `/workspace/repository` |
| `.git` no expuesto con su contenido al worker | Conservado | `quality_gate_isolation.py:399-426` monta directorio vacío de solo lectura |
| Raíces protegidas enmascaradas | Conservado | `quality_gate_isolation.py:352-384` |
| Workspaces inválidos rechazados fail-closed | Conservado | `quality_gate_isolation.py:63-86`; validación ocurre antes del lookup de Bubblewrap (`:211-225`) |
| `/tmp` host separado del guest | Conservado | `quality_gate_isolation.py:296-305` usa `--tmpfs /tmp`; no se monta `/tmp` host |
| Worker sin acceso a bases de producción | Conservado estáticamente | raíces protegidas enmascaradas; no aparece mount writable de bases protegidas |
| Sin fallback al filesystem host | Conservado en el código revisado | `workspace_guest_path()` rechaza destino fuera del workspace; no se observa traducción inversa ni fallback |

La investigación no propone ampliar binds, montar el `/tmp` host, exponer `.git`/bases protegidas, relajar la política de `/tmp`, desactivar validaciones, silenciar errores o sustituir aislamiento real por mocks.

## 9. Alternativas arquitectónicas conceptuales

Estas son categorías posibles para una adjudicación posterior, no recomendaciones ni autorización de cambio:

1. Un harness host autorizado podría ser dueño explícito del workspace host y del lanzamiento de cada worker, manteniendo fuera del worker la creación y validación de roots host.
2. El contrato de ejecución podría distinguir tipos de identidad de ruta (host frente a guest) y definir de manera explícita qué componente puede traducir entre ellos, sin aceptar paths arbitrarios.
3. Los tests de worker anidado podrían requerir una frontera de prueba diferente, declarada por el contrato, donde el padre conserve la autoridad de crear y validar los mounts.
4. Las comprobaciones funcionales del worker y la verificación Git del checkout podrían seguir siendo dos observaciones separadas, producidas por el worker y el harness host respectivamente.

Cada opción necesita diseño/aprobación explícitos. No se elige una en STEP-13.

## 10. Casos no resueltos y evidencia faltante

- No se conoce una forma autorizada de que un test ejecutado dentro del worker obtenga un workspace host bajo `/tmp` sin montar el `/tmp` del host ni delegar el lanzamiento al host harness.
- No existe contrato estático para traducir paths guest de `tmp_path` a una identidad host; el helper actual solo traduce host workspace → guest path.
- No se ha inspeccionado una ejecución posterior autorizada que confirme el comportamiento real de pytest/Bubblewrap; STEP-13 no debía ejecutarla.
- La verificación de Git B1-R sigue en el proceso pytest. Falta una decisión de arquitectura que preserve esa comprobación sin exponer `.git` al worker.
- Los tests nuevos de `workspace_guest_path()` no cubren paths simbólicos, inexistentes ni el uso desde el worker; no se ejecutaron.

## 11. Nodeids afectados pendientes

- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_bubblewrap_denies_protected_paths_and_allows_derived_workspace`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolation_fails_closed_when_bubblewrap_is_unavailable`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolated_process_exit_code_is_preserved`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_active_virtual_environment_is_available_read_only_in_sandbox`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_synthetic_pytest_runs_inside_the_process_boundary`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_snapshot_contract_tests_run_without_git_or_production_mounts`
- `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_focal_binding_is_validated_inside_bubblewrap`
- `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_isolated_focal_runner_propagates_binding_and_writes_receipt`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_maps_host_path_to_mounted_workspace`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_rejects_paths_outside_workspace`
- `tests/audit/test_b1_route_repeatability.py::test_synthetic_chat_route_is_repeatable_and_sterile`

La lista no autoriza ejecución ni reapertura del Quality Gate.

## 12. Declaración de no ejecución y estado canónico

- No se ejecutaron `pytest`, nodeids, `scripts/test.sh`, `scripts/quality_gate.py`, `scripts/prepare_test_snapshot.py`, benchmarks ni pruebas de aislamiento.
- No se accedió a bases protegidas ni se generaron snapshots B06.
- No se modificó código, pruebas, configuración o expedientes previos.
- No se hizo staging, commit, reset, checkout ni limpieza del worktree.

**Resultado:** `NESTED_WORKSPACE_CONTRACT_CONTRADICTION_FOUND`  
**Estado canónico:** `P1.2 = BLOCKED-REGRESSION`

La contradicción estática identificada no resuelve el bloqueo de P1.2. No autoriza STEP-14, ejecución de tests ni reapertura del Quality Gate.
