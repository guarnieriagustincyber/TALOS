# TALOS-P1.2-STEP-12 — REVISIÓN ESTÁTICA DE STEP-11

**Entrada:** `WORKSPACE_PATH_FIX_READY_FOR_REVIEW`  
**Gate:** `P1.2 = BLOCKED-REGRESSION`  
**Resultado:** `STATIC_REVIEW_PARTIAL`

## 1. Estado del repositorio

- Rama observada: `talos-current-audit` (coincide con la esperada).
- HEAD observado: `cc8acfae623f9d10c8366871470319786b6a7ca4` (coincide con el esperado).
- El worktree continúa sucio con modificaciones staged, unstaged y untracked preexistentes. Se preservaron.
- No se realizó staging, commit, reset, checkout, limpieza ni modificación de implementación/tests durante STEP-12.

## 2. Archivos inspeccionados y atribución

Se inspeccionaron:

- `scripts/quality_gate.py`
- `scripts/quality_gate_isolation.py`
- `tests/unit/diagnostics/test_quality_gate_isolation.py`
- `docs/TALOS-P1.2-STEP-11-WORKSPACE-GUEST-PATH.md`

| Archivo | Evidencia actual | Atribución posible |
|---|---|---|
| `scripts/quality_gate.py` | Archivo con modificaciones unstaged numerosas; el bloque que deriva `pytest_guest_tmp_root` llama a `workspace_guest_path()` y se usa en `TALOS_TEST_BASETEMP` (`1571-1579`) | El expediente STEP-11 reporta ese bloque como su corrección, pero el diff completo incluye cambios anteriores no atribuibles de forma automática |
| `scripts/quality_gate_isolation.py` | Archivo untracked; contiene `_SANDBOX_WORKSPACE` y el nuevo helper `workspace_guest_path()` (`48-49`, `91-101`) | La presencia del helper coincide con el expediente STEP-11; al ser untracked, no hay comparación con HEAD que demuestre autoría/historial |
| `tests/unit/diagnostics/test_quality_gate_isolation.py` | Archivo untracked; contiene dos tests nuevos (`26-47`) además de los tests previos de aislamiento | El expediente STEP-11 los identifica como nuevos; Git no permite separar históricamente lo añadido en STEP-11 de los contenidos anteriores del archivo |
| `docs/TALOS-P1.2-STEP-11-WORKSPACE-GUEST-PATH.md` | Expediente existente que describe los cambios y restricciones | Es evidencia documental de la fase, no historial Git independiente |

Por ello, el análisis atribuye el bloque de cálculo guest y los dos tests a STEP-11 conforme al expediente; no atribuye automáticamente el resto del contenido de esos archivos.

## 3. Flujo host/guest

### Flujo observado

1. `scripts/quality_gate.py:1473-1480`: crea el `TemporaryDirectory` host en `/tmp`, define `execution_root` y crea `execution_root/pytest-tmp`.
2. `scripts/quality_gate.py:1571-1574`: define `pytest_tmp_root` como hijo del workspace y llama `workspace_guest_path(execution_root, pytest_tmp_root)`.
3. `scripts/quality_gate_isolation.py:91-101`: resuelve ambos paths estrictamente, obtiene el relativo mediante `host_path.relative_to(workspace_root)` y devuelve ese relativo bajo `_SANDBOX_WORKSPACE`.
4. `scripts/quality_gate.py:1579`: pasa la ruta guest calculada por `TALOS_TEST_BASETEMP`.
5. `scripts/quality_gate.py:1024-1026`: el worker toma esa variable y la convierte en `--basetemp=<valor>`.
6. `scripts/quality_gate.py:1595-1598`: el mismo `execution_root` host se entrega a `run_isolated_process`.
7. `scripts/quality_gate_isolation.py:48-49,296-305`: `_SANDBOX_WORKSPACE` vale `/workspace/run`; Bubblewrap monta `execution_root` allí con `--bind`, mientras crea un `/tmp` guest separado mediante `--tmpfs`.

### Evaluación

El cálculo guest y el bind utilizan la misma constante efectiva (`_SANDBOX_WORKSPACE`). El `pytest-tmp` anfitrión se encuentra dentro del workspace writable autorizado y la ruta guest resultante apunta a su ubicación relativa bajo `/workspace/run`. No se observa un montaje alternativo del `/tmp` host ni una ruta hacia el checkout.

Por lo tanto, el mapeo del flujo principal es **estáticamente coherente**. Esto no demuestra que pytest resuelva `tmp_path` así en ejecución ni que Bubblewrap establezca correctamente los mounts.

### Rutas, resolución y symlinks

- Las rutas pasadas por el runner son `Path` del host; el helper las convierte y aplica `resolve(strict=True)`.
- Las rutas relativas, si se proporcionaran, se resolverían respecto del cwd del proceso que llama. El runner actual entrega rutas host absolutas derivadas de `TemporaryDirectory`.
- Un `host_path` que resuelva fuera del workspace no supera `relative_to()` y genera `IsolationError`.
- Un symlink de `host_path` cuyo destino está fuera se resuelve antes de comprobar contención y se rechaza; un symlink cuyo destino continúa dentro del workspace se acepta.
- `workspace_guest_path()` por sí solo resuelve un `workspace_root` symlink en lugar de rechazarlo. En el flujo del runner, `run_isolated_process()` aplica `_validate_mount_roots()` al mismo workspace y rechaza symlinks (`quality_gate_isolation.py:63-79,211-214`). No se debilitó ese control.
- Si `host_path` o el workspace no existen, `resolve(strict=True)` falla; no hay fallback a otra raíz. El helper no convierte todos esos errores de resolución a `IsolationError`, pero la operación falla explícitamente y no continúa con una ruta sustitutiva.

Los tests nuevos cubren contención positiva/negativa simple, no rutas relativas, symlinks ni paths ausentes.

## 4. Compatibilidad con pruebas anidadas

Los tests de aislamiento/focalización invocan `run_isolated_process()` y construyen sus workspaces mediante `tmp_path`:

- `tests/unit/diagnostics/test_quality_gate_isolation.py`:
  - `test_bubblewrap_denies_protected_paths_and_allows_derived_workspace` (`:50`, workspace en `:108`, invocación en `:269`).
  - `test_isolation_fails_closed_when_bubblewrap_is_unavailable` (`:333-346`).
  - `test_isolated_process_exit_code_is_preserved` (`:354-362`).
  - `test_active_virtual_environment_is_available_read_only_in_sandbox` (`:372-385`).
  - `test_synthetic_pytest_runs_inside_the_process_boundary` (`:397-440`).
  - `test_snapshot_contract_tests_run_without_git_or_production_mounts` (`:463-469`).
- `tests/unit/diagnostics/test_quality_gate_focal_execution.py`:
  - `test_focal_binding_is_validated_inside_bubblewrap` crea `execution_root = tmp_path / "execution"` (`:667,706`) y llama `run_isolated_process()` (`:768`).
  - `test_isolated_focal_runner_propagates_binding_and_writes_receipt` reemplaza `run_isolated_process()` por un fake (`:785-930`); no intenta establecer un segundo Bubblewrap real.

Cuando estos tests corren bajo el worker del Quality Gate, el `tmp_path` que pytest recibe está configurado bajo `/workspace/run/pytest-tmp` en el namespace guest. Si pasan un workspace derivado de esa ruta a `run_isolated_process()`, `_validate_mount_roots()` evalúa la ruta en el namespace del proceso llamante y exige que esté bajo `/tmp` (`quality_gate_isolation.py:63-79`). La ruta guest `/workspace/run/...` no cumple ese requisito. Los tests de arriba, salvo el caso con mock, no preparan un workspace host `/tmp` visible desde dentro del worker ni traducen el path guest a una ruta host.

El requisito `/tmp` es una condición sobre el filesystem visible al proceso anfitrión que ejecuta cada `run_isolated_process()`. No hay evidencia estática de que el validador distinga automáticamente una ruta host de una ruta guest. En el worker, el argumento construido desde `tmp_path` es una ruta guest; el validador la resolverá en el namespace actual y la rechazará por no estar bajo `/tmp`. No se debe resolver relajando el validador o ampliando mounts.

**Resultado de compatibilidad:** `UNRESOLVED / incompatibilidad estática probable` para esos tests en el perfil del Quality Gate. El contrato del path principal queda coherente, pero la compatibilidad de las invocaciones anidadas no queda establecida.

## 5. Invariantes de seguridad

| Invariante | Estado estático | Evidencia / límite |
|---|---|---|
| Checkout montado de solo lectura | Conservado | `quality_gate_isolation.py:300-305` |
| `.git` enmascarado | Conservado | `quality_gate_isolation.py:399-426` |
| Raíces protegidas enmascaradas | Conservado | `quality_gate_isolation.py:352-384`; fuentes protegidas no se hacen mounts writable |
| Workspaces inválidos rechazados fail-closed | Conservado | `_validate_mount_roots()` sigue rechazando workspace inexistente/no directorio, fuera de `/tmp`, symlink y solapamiento con repositorio (`:63-86`) |
| `/tmp` host separado del `/tmp` worker | Conservado | `--tmpfs /tmp` y bind separado de `execution_root` (`:296-305`) |
| Sin acceso a bases originales desde worker | Conservado estáticamente | rutas protegidas sustituidas por mounts vacíos de solo lectura (`:352-384`); las bases no se montan como acceso writable |

La inspección estática confirma que STEP-11 no debilitó esos controles. No demuestra comportamiento efectivo en ejecución.

## 6. Adjudicación de los tests nuevos

1. `test_workspace_guest_path_maps_host_path_to_mounted_workspace` (`test_quality_gate_isolation.py:26-35`):
   - Comprueba que una ruta existente `execution/pytest-tmp`, hija del workspace, se mapea a `/workspace/run/pytest-tmp`.
   - Expresa correctamente el caso positivo simple respecto al mount definido por el helper.
2. `test_workspace_guest_path_rejects_paths_outside_workspace` (`:38-47`):
   - Comprueba que una ruta existente hermana, fuera del workspace, genera `IsolationError`.
   - Expresa correctamente el rechazo de una ruta externa.

Limitaciones: no prueban rutas relativas, symlinks, workspace symlink ni error de ruta inexistente, ni ejercitan el mount de Bubblewrap. La inspección no equivale a ejecución.

## 7. Riesgos residuales y nodeids pendientes

Además de los nodeids de STEP-11, queda pendiente la compatibilidad anidada para:

- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_bubblewrap_denies_protected_paths_and_allows_derived_workspace`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolation_fails_closed_when_bubblewrap_is_unavailable`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolated_process_exit_code_is_preserved`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_active_virtual_environment_is_available_read_only_in_sandbox`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_synthetic_pytest_runs_inside_the_process_boundary`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_snapshot_contract_tests_run_without_git_or_production_mounts`
- `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_focal_binding_is_validated_inside_bubblewrap`
- `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_isolated_focal_runner_propagates_binding_and_writes_receipt` (la invocación de aislamiento se reemplaza por fake; su flujo de runner sigue pendiente)

También quedan pendientes de validación autorizada:

- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_maps_host_path_to_mounted_workspace`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_rejects_paths_outside_workspace`

La lista no autoriza su ejecución.

## 8. No ejecución y salida

Durante STEP-12 no se ejecutaron pruebas, nodeids, `scripts/test.sh`, `scripts/quality_gate.py`, `scripts/prepare_test_snapshot.py`, benchmarks ni pruebas de aislamiento. No se accedió a bases protegidas ni se generaron snapshots B06. No se modificó código o tests ni se alteró staging, rama o HEAD.

**Resultado:** `STATIC_REVIEW_PARTIAL`  
**Estado:** `P1.2 = BLOCKED-REGRESSION`

El mapeo principal host/guest está estáticamente coherente. La compatibilidad de los tests anidados que derivan workspaces desde `tmp_path` permanece sin resolver en el worker, por lo que esta revisión no acepta completamente STEP-11 ni autoriza STEP-13, validación dinámica o reapertura del Quality Gate.
