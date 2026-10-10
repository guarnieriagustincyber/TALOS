# STEP-22 — Aggregation and rejection matrix

**Estado:** contrato propuesto; agregador externo no implementado  
**Resultado STEP-22:** `BLOCKED_WITH_EXPLICIT_FINDINGS`  
**Estado canónico:** `P1.2 = BLOCKED-REGRESSION`

Relacionado con [contrato principal STEP-22](./STEP-22-EXTERNAL-HARNESS-EXECUTION-CONTRACT.md) y [matriz de fronteras](./STEP-22-TRUST-BOUNDARY-MATRIX.md).

## 1. Unidades y ownership

1. **Perfil/run:** un `run_id` autorizado delimita un checkout, controller/policy identity, perfil, expected nodeid inventory y tiempo de ejecución.
2. **Nodeid:** cada uno de los once nodeids obligatorios conserva owner estándar pytest, clasificación `required` y exactamente un resultado item por perfil/run. No hay transferencia de ownership en STEP-22.
3. **Subresultado:** worker/controller/verifier/observador/Git emite evidencia con role, identity, `run_id`, item parent, worker/case ID y status. Un child pytest o controller no se cuenta como nodeid padre.
4. **Caso B1-R:** 10 case IDs × 3 repeticiones = 30 observaciones; vinculadas a nodeid B1-R, no son 30 nodeids ni sustituyen los once items.
5. **Suite/perfil:** `tests/unit` y `tests/audit` permanecen `required`; ambas suites deben satisfacerse en los perfiles actuales que las exigen (`required` y `release` según la orden STEP-22). `qualification-required` conserva su semántica release-only y no se usa para reemplazar ni reducir estas obligaciones.

La fuente autoritativa de expected nodeids debe ser el perímetro/policy aprobado fuera del checkout, comparado con la configuración candidate del repo. La versión actual del perímetro muestra las suites `tests/audit` y `tests/unit` como `required`; no se altera. La identidad de la policy y su ancla aún no están aprobadas.

## 2. Inventario de los once nodeids

| # | Nodeid exacto | Obligación | Resultado requerido | Subresultados adicionales |
|---:|---|---|---|---|
| 1 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_maps_host_path_to_mounted_workspace` | `required` | Un item pytest estándar recolectado/ejecutado por owner autorizado. | Ninguna evidencia de aislamiento se infiere de helper. |
| 2 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_rejects_paths_outside_workspace` | `required` | Un item pytest estándar. | Assertion de contención, no aislamiento global. |
| 3 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_bubblewrap_denies_protected_paths_and_allows_derived_workspace` | `required` | Un item parent con boundary real conforme al contrato del test. | Worker/launch evidence vinculada; fake no satisface. |
| 4 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolation_fails_closed_when_bubblewrap_is_unavailable` | `required` | Un item que verifica el fallo al faltar bwrap. | Orquestación/fake no cuenta como aislamiento positivo. |
| 5 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolated_process_exit_code_is_preserved` | `required` | Un item parent y assertion de exit code child. | Child code/identity no es nodeid separado. |
| 6 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_active_virtual_environment_is_available_read_only_in_sandbox` | `required` | Un item con evidencia del entorno montado según assertions. | Runtime/mount evidence; path label no demuestra read-only. |
| 7 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_synthetic_pytest_runs_inside_the_process_boundary` | `required` | Un item parent. | Pytest hijo es subresultado, no reemplazo. |
| 8 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_snapshot_contract_tests_run_without_git_or_production_mounts` | `required` | Un item parent con observaciones del child que efectivamente afirma el test. | Git checkout permanece host-side; no inferir mounts no observados. |
| 9 | `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_focal_binding_is_validated_inside_bubblewrap` | `required` | Un item de boundary real/focal binding. | Evidencia de binding y launcher real; fake no satisface. |
| 10 | `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_isolated_focal_runner_propagates_binding_and_writes_receipt` | `required` | Un item de orquestación simulada. | Resultado mock explícito; no contarlo como boundary real. |
| 11 | `tests/audit/test_b1_route_repeatability.py::test_synthetic_chat_route_is_repeatable_and_sterile` | `required` | Un item compuesto estándar, con 30 observaciones funcionales y todas las dimensiones aplicables. | Worker, artifact/verifier, isolation, Git before/after y aggregate vinculados. |

## 3. Registros mínimos de cobertura

### 3.1 Node result

Campos requeridos:

```text
schema_version
run_id
profile_id
perimeter_identity
nodeid
classification
owner_id
execution_mechanism
checkout_identity
controller_identity
worker_id (nullable solo si no hubo launch y status no es PASS)
collected_count
item_status
functional_status
exit_code
timeout_status
subresult_refs[]
started_at
completed_at
diagnostics[]
```

No aceptar dos registros activos para el mismo `(run_id, profile_id, nodeid, owner_id)` salvo retries explícitamente autorizados y representados como intentos separados bajo policy. Un retry no borra un fallo previo ni se usa para ocultar flakiness; la regla de adjudicación de retries debe ser explícita antes de implementación.

### 3.2 Subresult

Campos requeridos:

```text
schema_version
run_id
parent_nodeid
role
producer_identity
consumer_identity
worker_id
case_id / repetition (cuando aplique)
input_refs[]
output_refs[]
status
exit_code / timeout_status (cuando aplique)
evidence_refs[]
limitations[]
diagnostics[]
```

Roles cerrados por policy: `controller`, `worker`, `artifact_verifier`, `isolation_observer`, `git_before`, `git_after`, `aggregator`. Un rol inesperado se rechaza.

### 3.3 Expected inventory y exactly-once

Antes de lanzar workers, el controller/bootstrap obtiene el inventario esperado del policy aprobado. Para cada perfil:

```text
expected_required_nodeids ⊆ observed_nodeids
observed_required_nodeids = expected_required_nodeids
count(run, profile, nodeid, owner) = 1
```

No clasificar como no aplicable un nodeid `required`. Los únicos elementos fuera del expected set deben estar autorizados por las reglas de perfil y clasificaciones vigentes; cualquier resultado inesperado se reporta y bloquea o se procesa según una regla explícita, nunca se descarta silenciosamente. Perfiles incompletos o identidad/perímetro no autenticables => `PREFLIGHT_BLOCKED`/`COVERAGE_INCOMPLETE`.

## 4. B1-R: matriz de 30 observaciones

Antes de ejecutar, derivar exactamente los diez casos desde el contrato B1-R autorizado y formar las 30 claves:

```text
(run_id, B1-R nodeid, case_id, repetition ∈ {1,2,3})
```

Cada clave debe existir exactamente una vez con estado/observación normalizada, worker identity, exit/timeout, artefact refs y diagnostics. Conservar guards, probes, counters y comparaciones normalizadas del test/contrato; no simular assertions ni sustituir el test con solo un reporte controller.

| Requisito | Aceptación propuesta | Rechazo |
|---|---|---|
| Casos | Los diez IDs autorizados presentes, sin extras. | Caso ausente, desconocido o duplicado. |
| Repeticiones | Tres por caso, 30 total, numeradas 1–3. | Menos/más de tres, ordinal repetido o registro ambiguo. |
| Normalización | Comparaciones del contrato aplicada a datos recogidos. | Payload crudo presentado como comparación, parseo ambiguo o dato no comparable. |
| Worker | Todos los resultados enlazados al worker autorizado y al run. | Worker identity mismatch, child desconocido, timeout/error omitido. |
| Artefacto | Archivo exacto permitido, digest verificado y verifier autorizado. | Missing, duplicate, mismatch, unsafe path, verifier inválido/no disponible. |
| Aislamiento | Evidencia independiente de boundary real para la ejecución funcional. | Reporte del worker, fake, `bwrap` instalado o exit 0 usado como sustituto. |
| Git | Dos capturas host-side válidas del mismo checkout/comando/scope; igualdad de estados reportados. | Falta/error/mismatch/diferencia. Igualdad no prueba ausencia de escrituras transitorias. |

B1-R sigue siendo un nodeid y un owner item. Sus 30 filas son cobertura interna del contrato B1-R; no crean 30 items pytest ni satisfacen los otros diez nodeids.

## 5. Matriz de rechazo

| Condición observada | Estado mínimo | Acción del agregador |
|---|---|---|
| No hay autorización externa aplicable | `NOT_AUTHORIZED` | No ejecutar supervisor/worker con autoridad host; global `BLOCKED`. |
| Autorización inválida, vencida, revocada, replay o contradicción | `AUTHORIZATION_INVALID` | Rechazar antes del checkout code; preservar causa. |
| Controller/bootstrap/runtime/policy no coincide | `PREFLIGHT_BLOCKED` | No iniciar workers; no fallback al runner del checkout. |
| Perfil no allowlisted o no aplicable | `PREFLIGHT_BLOCKED` | Perfil no satisface obligaciones `required`. |
| Uno o más nodeids `required` ausentes | `COVERAGE_INCOMPLETE` | Bloquear perfil/global; nunca contar child como padre. |
| Nodeid esperado duplicado / múltiples owners | `RESULT_INVALID` y `COVERAGE_INCOMPLETE` | Mantener todos los registros; no escoger uno favorable. |
| Nodeid inesperado/no autorizado | `RESULT_INVALID` | Rechazar o bloquear según policy, no ocultar. |
| Checkout/run/profile/controller identity contradictorios | `RESULT_INVALID` | No componer evidencias de identidades distintas. |
| Worker no inició | `WORKER_NOT_STARTED` | Item no PASS; conservar error de launch. |
| Worker falla, aborta, termina por señal o timeout | `WORKER_FAILED` / `WORKER_TIMED_OUT` | No interpretar output parcial como éxito. |
| Functional assertion falla | `FAIL` | Resultado funcional FAIL; no compensable por Git o verifier. |
| Caso B1-R ausente/duplicado/repetición insuficiente | `COVERAGE_INCOMPLETE` | Rechazar B1-R aunque exit code sea cero. |
| JSON inválido/campo crítico desconocido/schema no soportado/size overflow | `RESULT_INVALID` | Rechazar envelope completo con diagnostics. |
| Output truncado requerido para decisión | `RESULT_INVALID` | No reconstruir defaults; status no satisfactorio. |
| Artefacto ausente, extra, symlink/path traversal o digest incorrecto | `ARTIFACT_VERIFICATION_FAILED` | Rechazar artefacto y bloquear nodeid compuesto. |
| Verificador no autorizado/no disponible/error/findings | `ARTIFACT_VERIFICATION_FAILED` | No aceptar self-attestation del worker. |
| Evidencia aislamiento ausente/incompleta/solo fake | `ISOLATION_UNVERIFIED` | No PASS global. |
| Observación Git falla, output no interpretable o falta lado | `OBSERVATION_FAILED` | Nunca sustituir por empty/clean. |
| Git pre/post status difiere | `CHECKOUT_CHANGED` | Adjudicar como no PASS; diferencia no se normaliza. |
| Subresultados contradictorios | `RESULT_INVALID` o `BLOCKED` con contradiction record | Preservar ambos; no seleccionar silenciosamente. |
| Item requerido marcado `NOT_APPLICABLE` sin policy válida | `COVERAGE_INCOMPLETE` | Rechazar. |
| Mocks presentados como aislamiento real | `ISOLATION_UNVERIFIED` | Clasificar mocks solo como evidencia de orquestación simulada. |
| Controller/agregador falla o falta registro externo | `BLOCKED` | No usar resultados del worker como sustituto. |

## 6. Precedencia y estado final

Se conservan múltiples causas. Como mínimo:

1. Autorización/identidad inválida bloquea antes de launch.
2. Error de evidencia, aislamiento, Git o cobertura impide PASS aunque funcional sea PASS.
3. Assertion funcional fallida produce `FAIL`; error de autoridad/evidencia produce `BLOCKED`/`ERROR` según policy.
4. Solo el agregador autorizado puede producir el estado profile/global.

`PASS` requiere autorización válida, identidad/scope exactos, items esperados completos, ausencia de resultados duplicados/contradictorios, propiedades funcionales requeridas satisfechas, artefactos verificados, aislamiento demostrado donde corresponda, observaciones Git exitosas e iguales cuando el contrato lo exige y toda evidencia vinculada al mismo run. `PASS` debe ser inalcanzable ante inputs `UNKNOWN` o bloqueados.

## 7. Non-evidence warning

The current `SuiteResults` in `scripts/quality_gate.py` aggregates pytest outcomes by suite and collection, not authenticated external controller evidence. STEP-18 documents no implemented ingest path for composite external subresults. This matrix specifies a future protocol only. It does not establish that the current gate detects every listed condition.
