# TALOS-P1.2-STEP-11 — CORRECCIÓN ESTÁTICA DE LA RUTA GUEST

**Entrada:** `DIFF_ADJUDICATION_PARTIAL`  
**Gate:** `P1.2 = BLOCKED-REGRESSION`  
**Salida:** `WORKSPACE_PATH_FIX_READY_FOR_REVIEW`

## 1. Estado del repositorio

- Rama: `talos-current-audit`.
- HEAD: `cc8acfae623f9d10c8366871470319786b6a7ca4`.
- El worktree ya estaba sucio, con cambios staged, unstaged y untracked; esos cambios se preservaron.
- No se hizo staging, commit, reset, checkout ni limpieza.
- Archivos modificados para STEP-11:
  - [scripts/quality_gate_isolation.py](../scripts/quality_gate_isolation.py): helper que deriva el guest path desde el punto de mount del runner y rechaza paths externos al workspace.
  - [scripts/quality_gate.py](../scripts/quality_gate.py): pasa a pytest el guest path calculado, no la ruta host.
  - [tests/unit/diagnostics/test_quality_gate_isolation.py](../tests/unit/diagnostics/test_quality_gate_isolation.py): tests unitarios estáticos para el mapeo y el rechazo de una ruta externa.
  - Este expediente.

## 2. Flujo de rutas antes y después

### Antes

```text
host:
  TemporaryDirectory(dir="/tmp")
    └── execution_root
          └── pytest-tmp

worker:
  /tmp                         = tmpfs separado
  /workspace/run               = bind writable de execution_root
  TALOS_TEST_BASETEMP           = ruta host /tmp/.../execution/pytest-tmp
```

Aunque la ruta host estaba bajo `/tmp`, el worker no veía ese árbol en el mismo lugar: Bubblewrap crea un `/tmp` independiente y monta el workspace anfitrión en `/workspace/run`.

### Después

```text
host:
  TemporaryDirectory(dir="/tmp")
    └── execution_root
          └── pytest-tmp

worker:
  /workspace/run               = bind writable de execution_root
  /workspace/run/pytest-tmp    = misma ruta relativa dentro del bind
  TALOS_TEST_BASETEMP           = /workspace/run/pytest-tmp
```

El cálculo se centraliza en `workspace_guest_path()`, que toma el punto de montaje efectivo definido por `quality_gate_isolation.py`, resuelve el path anfitrión y exige que esté dentro del workspace antes de derivar su ruta guest. No se introduce un fallback al filesystem del host.

## 3. Evidencia estática concreta

En [quality_gate.py](../scripts/quality_gate.py):

- `1473-1480`: el directorio temporal anfitrión se crea con `dir="/tmp"`; `execution_root/pytest-tmp` se crea dentro de él.
- `1571-1574`: el runner invoca `workspace_guest_path(execution_root, pytest_tmp_root)`.
- `1579`: `TALOS_TEST_BASETEMP` recibe el resultado guest.
- `1595-1598`: el mismo `execution_root` es pasado a `run_isolated_process`.
- `1024-1026`: el worker incorpora `TALOS_TEST_BASETEMP` como `--basetemp` de pytest.

En [quality_gate_isolation.py](../scripts/quality_gate_isolation.py):

- `48-49`: se define `_SANDBOX_WORKSPACE = "/workspace/run"`; ese mismo valor controla el destino del bind y el cálculo guest.
- `63-86`: `_validate_mount_roots()` sigue exigiendo workspace existente bajo `/tmp`, sin symlink ni solapamiento con el repositorio.
- `91-101`: `workspace_guest_path()` resuelve ambos paths, exige que el destino sea descendiente del workspace host y devuelve `_SANDBOX_WORKSPACE / relative_path`.
- `296-305`: Bubblewrap mantiene `/tmp` como tmpfs separado, monta el repositorio en solo lectura y monta el workspace anfitrión en `_SANDBOX_WORKSPACE` con escritura.
- `352-384` y `399-426`: las raíces protegidas y `.git` permanecen enmascarados con mounts de solo lectura.

En [test_quality_gate_isolation.py](../tests/unit/diagnostics/test_quality_gate_isolation.py):

- `26-35`: el caso positivo expresa que `execution/pytest-tmp` se mapea a `/workspace/run/pytest-tmp`.
- `38-47`: el caso negativo exige `IsolationError` para una ruta fuera del workspace.

Estos tests fueron añadidos como expresión del contrato; **no se ejecutaron**.

## 4. Adjudicación estática posterior

| Invariante | Resultado estático | Evidencia |
|---|---|---|
| Workspace anfitrión dentro de `/tmp` | Cumple | `TemporaryDirectory(..., dir="/tmp")`; `_validate_mount_roots()` conserva su rechazo |
| Directorio temporal dentro del workspace autorizado | Cumple | `pytest-tmp` es hijo de `execution_root` |
| Ruta de pytest existente conceptualmente en guest | Cumple estáticamente | Se deriva bajo el mismo mount guest que recibe `execution_root`; el directorio existe antes de lanzar el worker |
| `tmp_path` de pytest queda dentro del mount autorizado | Configurado para quedar bajo `/workspace/run/pytest-tmp` | `--basetemp` recibe el guest path; la escritura queda en el bind writable del workspace |
| No se requiere `/tmp` del host dentro del worker | Cumple | `/tmp` sigue siendo tmpfs aislado; el runner no lo monta desde el host |
| Checkout no writable | Cumple estáticamente | El repositorio se monta `--ro-bind` |
| `.git` y bases protegidas no expuestas al worker | Sin cambio; permanece la máscara | mounts vacíos de solo lectura para `.git` y recursos protegidos |
| Rechazo fail-closed de raíz inválida | Sin cambio | `_validate_mount_roots()` mantiene las verificaciones existentes |

La correspondencia de rutas queda demostrada por la construcción común de `workspace_guest_path()` y el destino del bind. Esto es una conclusión estática del flujo de variables; no demuestra el comportamiento en ejecución de Bubblewrap o pytest.

## 5. Límites y riesgo residual

- No se afirma que Bubblewrap funcione correctamente en ejecución.
- No se afirma que las pruebas de aislamiento o la suite pasen.
- Los tests que anidan `run_isolated_process()` y construyen su workspace desde el `tmp_path` del worker podrían interactuar con la regla host `/tmp` del validador; esa propiedad requiere validación posterior y no se amplió en este cambio.
- No se modificaron los grupos B, C, D o E.
- P1.2 continúa `BLOCKED-REGRESSION`.

## 6. Nodeids que requieren validación posterior

Nodeids afectados por el contrato de aislamiento, según el inventario previo:

- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_bubblewrap_denies_protected_paths_and_allows_derived_workspace`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolation_fails_closed_when_bubblewrap_is_unavailable`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolated_process_exit_code_is_preserved`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_active_virtual_environment_is_available_read_only_in_sandbox`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_synthetic_pytest_runs_inside_the_process_boundary`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_snapshot_contract_tests_run_without_git_or_production_mounts`
- `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_focal_binding_is_validated_inside_bubblewrap`
- `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_isolated_focal_runner_propagates_binding_and_writes_receipt`

Nuevos casos unitarios añadidos, pendientes de ejecución autorizada:

- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_maps_host_path_to_mounted_workspace`
- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_rejects_paths_outside_workspace`

Esta lista no constituye autorización para ejecutarlos ni para reabrir el Quality Gate.

## 7. Declaración de no-ejecución

Durante STEP-11 no se ejecutaron:

- `pytest` ni nodeids individuales;
- `scripts/test.sh`;
- `scripts/quality_gate.py`;
- `scripts/prepare_test_snapshot.py`;
- benchmarks ni pruebas de aislamiento.

No se accedió a bases protegidas, no se generaron snapshots B06 y no se hicieron staging, commits, resets ni limpieza del worktree.

## 8. Estado final

`WORKSPACE_PATH_FIX_READY_FOR_REVIEW`  
`P1.2 = BLOCKED-REGRESSION`

La corrección queda lista para revisión estática humana. No autoriza validación dinámica, reapertura del gate ni STEP-12 por inferencia.
