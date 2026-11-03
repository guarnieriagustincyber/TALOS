# STEP-23C — Adjudicación documental y bloqueos abiertos

**Resultado:** `CONSISTENCY_ADJUDICATED_WITH_OPEN_BLOCKERS`  
**Estado canónico:** `P1.2=BLOCKED-REGRESSION`; `P1.3=BLOCKED`  
**Harness externo:** implementación no autorizada  
**B1-R:** ejecución no autorizada  
**Anomalía histórica:** `UNRESOLVED_HISTORICAL_EVIDENCE`

## 1. Alcance, identidad y expedientes

Se verificó el repositorio `/media/agustin/Laboratorio/study-engie`, rama `talos-current-audit`, HEAD `cc8acfae623f9d10c8366871470319786b6a7ca4`. La rama y HEAD coinciden con lo esperado. El baseline actual, su captura nominal completa y sus límites están registrados en [STEP-23C baseline](./STEP-23C-BASELINE-ACTUAL-Y-PRESERVACION-DEL-ESTADO.md); no se usa para reconstruir los estados históricos de STEP-22.

Los cuatro expedientes reales de STEP-22 fueron leídos íntegramente:

1. [Contrato de ejecución](./STEP-22-EXTERNAL-HARNESS-EXECUTION-CONTRACT.md)
2. [Matriz de fronteras de confianza](./STEP-22-TRUST-BOUNDARY-MATRIX.md)
3. [Matriz de agregación y rechazos](./STEP-22-AGGREGATION-AND-REJECTION-MATRIX.md)
4. [Decisiones y bloqueos](./STEP-22-DECISIONS-AND-BLOCKERS.md)

No hay un expediente STEP-23 general previo persistido; la actividad anterior se suspendió y produjo [STEP-23A](./STEP-23A-GIT-ANOMALY-ADJUDICATION.md) y [STEP-23B](./STEP-23B-HISTORICAL-INDEX-CAPTURE-VALIDATION.md). Estos dos se preservan, incluida la anomalía histórica no resuelta.

Clases epistemológicas usadas: `OBSERVED` = lectura/inspección actual directa; `DOCUMENTED` = afirmación presente en un artefacto; `PROPOSED` = diseño no desplegado; `INFERRED` = conclusión limitada derivada de lo anterior; `UNVERIFIED` = sin evidencia suficiente.

## 2. Matriz de consistencia cruzada STEP-22

Los estados clasifican la relación documental y el estado de provisión; no confieren autoridad. `CONSISTENT` no significa implementado ni demostrado.

| Dimensión / requisito | Documentos | Estado | Evidencia y evaluación | Acción pendiente |
|---|---|---|---|---|
| Aprobación, revocación y actualización | Contrato §§2–3, trust matrix §§1–4, decisions B-01/B-06 | `UNRESOLVED_AUTHORITY` | `DOCUMENTED`: todas las piezas requieren una autoridad externa y un registro. `OBSERVED`: los documentos indican que no está identificada. No hay contradicción de roles, pero no existe actor autorizado designado. | Decisión externa que designe autoridad, alcance, delegados/proceso y registro verificable; definir quién revisa independientemente. |
| Bootstrap externo y ancla independiente | Contrato §§2–4, trust matrix §§1–2, decisions B-02 | `UNRESOLVED_AUTHORITY` | `DOCUMENTED`: debe autenticar antes de código del checkout. `OBSERVED`: los propios expedientes dicen que no existe/ no se halló bootstrap desplegado ni trust anchor elegido. | Autoridad debe aprobar identidad, distribución, custodia y ciclo de vida del bootstrap/ancla. |
| Identidad e integridad de controller, intérprete, dependencias y módulos | Contrato §§3–4, trust matrix filas controller/runtime, decisions B-03 | `NOT_IMPLEMENTED` | `PROPOSED`: cubrir la cadena transitiva pre-worker, configuración y herramientas. `UNVERIFIED`: no existe inventario aprobado o controller desplegado en la evidencia de STEP-22. | Fijar inventario reproducible y procedencia; aprobar componentes y demostrar que los bytes ejecutados son los autorizados. |
| Protección TOCTOU y sustitución check-to-use | Contrato §3.3, trust matrix filas bootstrap/controller, decisions B-04 | `UNDERSPECIFIED` | `DOCUMENTED`: ejecutar bytes verificados exactos y rechazar cambio/rollback. Se sugieren copia/ubicación protegida o handle inmutable, sin elección aprobada ni procedimiento completo. | Seleccionar mecanismo y fijar prueba de sustitución entre comprobación y uso, errores y rollback. |
| Separación de responsabilidades host/worker | Contrato §§2, 5, trust matrix §2, aggregation §1/§3 | `CONSISTENT` | `PROPOSED`: controller host observa Git, crea workspace y lanza; worker ejecuta tests no confiables, no ve `.git`/roots por defecto ni decide autoridad; children no reemplazan nodeids padre. Las cuatro piezas mantienen esa separación. No está implementada. | Preservar el contrato en el diseño y demostrarlo en una fase autorizada. |
| Comandos, roots, mounts, workspace y recursos | Contrato §§3.1, 5.1–5.2, trust matrix filas configuración/workspace/worker, decisions B-05/B-10 | `UNDERSPECIFIED` | `PROPOSED`: argv y allowlists cerradas, checkout RO, roots/mounts y workspace limitados. `DOCUMENTED`: límites de recursos presentados como propuesta; valores y política exacta siguen pendientes. No hay contradicción de principio. | Aprobar perfiles, paths, mounts, capacidades, límites, timeout/retries y versionado; impedir ampliación desde checkout. |
| Provenance e integridad de entradas, resultados y artefactos | Contrato §§4, 6.1–6.3, trust matrix filas artefactos/evidencia, aggregation §§3–5 | `CONSISTENT` | `PROPOSED`: IDs/run, hashes, scope, productor/consumidor, paths permitidos, schema versionado, verificación de mismos bytes y fallos explícitos. No equivale a verdad ni está provisionado. | Definir schemas normativos, identidad productora, preservación externa y prueba de ingestión/validación. |
| Verificación independiente de artefactos | Contrato §§2, 6.3, 8; trust matrix fila verifier; aggregation §5; decisions B-08/B-09 | `UNRESOLVED_AUTHORITY` | Los rechazos por artefacto ausente, hash, path y verifier inválido son compatibles. `OBSERVED` en STEP-18: el verifier actual pertenece al checkout; independencia externa y su identidad aprobada no están demostradas. | Designar e identificar verifier independiente; verificar el mismo artefacto y su vinculación a run/nodeid. |
| Evidencia efectiva de aislamiento | Contrato §§5.2, 6.2, 8; trust matrix fila observador; aggregation §4–6; decisions B-08/B-11 | `NOT_IMPLEMENTED` | `CONSISTENT` en que worker/fake/`bwrap` instalado no se auto-certifican y falta evidencia de boundary real. `UNVERIFIED`: no se ejecutó ni demostró esta arquitectura en STEP-22/23C. | Autorizar y ejecutar evaluación independiente del boundary real, sin usar el resultado funcional como sustituto. |
| Observación Git pre/post | Contrato §7, trust matrix fila Git, aggregation §§4–5 | `CONSISTENT` | `PROPOSED`: mismo checkout, comando/scope, registros antes y después; error/no parseo/diferencia bloquea. Se declara que igualdad no demuestra ausencia de escrituras transitorias. | Fijar identidad del observador/comando en policy; probar manejo de errores y preservar ambas capturas. |
| Agregación, error, timeout, omisión, duplicado, contradicción | Contrato §§6, 9–10; aggregation §§3–6; trust matrix fila agregador | `CONSISTENT` | `PROPOSED`: inventario exacto, exactly-once, estados distintos, rechazo ante entradas ausentes/duplicadas/contradictorias y precedencia que conserva causas. El agregador externo no está implementado. | Precisar las reglas finales en schema/policy y validarlas con casos negativos autorizados. |
| Caducidad, revocación, actualización y rollback | Contrato §§3.1–3.3, trust matrix filas autoridad/bootstrap, decisions B-01/B-02/B-06 | `UNRESOLVED_AUTHORITY` | Los documentos concuerdan en que deben existir vigencia, revocación y anti-rollback. El mecanismo, actor, formato y operación offline no están elegidos ni desplegados. | Decisión de gobernanza y evidencia del mecanismo de lifecycle; no completar con una clave/servicio supuesto. |
| Responsables y criterios de salida | Decisions §§4–6, trust matrix §§1–4, contrato §§10–11 | `UNRESOLVED_AUTHORITY` | Los roles requeridos y blockers B-01..B-11 son explícitos; sus identidades se dejaron vacías de forma deliberada. Los criterios son propuestos, no aprobaciones. | Actores autorizados asignan responsabilidades y aceptan criterios por escrito. |
| Máquina de estados y correspondencia estados/transiciones | Contrato §9, aggregation §6 | `UNDERSPECIFIED` | Las tablas enumeran estados de resultado, mientras el diagrama también emplea etiquetas de etapa (`AUTHORIZATION_CHECK`, `WORKERS_RUNNING`, `RESULTS_VALIDATION`, etc.) sin declarar con precisión si son estados persistidos o transiciones. No impide entender el flujo conceptual, pero requiere semántica inequívoca antes del schema. | Definir estados, transiciones, terminalidad y estados simultáneos de causas en un modelo normativo. |

**Contradicciones:** no se encontró contradicción material directa entre los cuatro documentos en el contrato propuesto. Esto no cierra los puntos `UNDERSPECIFIED`, no resuelve `UNRESOLVED_AUTHORITY` y no convierte el diseño en despliegue.

## 3. B1-R: inventario y adjudicación

`OBSERVED` por inspección estática: [contrato B1-R](../tests/audit/b1r_contract.json) declara `repetitions_per_case: 3` y presenta exactamente diez claves en `expected_cases`. El test estático contiene la misma tupla de diez nombres y `REPETITIONS = 3`. Por tanto, el contrato prevé **10 × 3 = 30 observaciones**; no se ejecutó B1-R y no se afirma que existan 30 observaciones producidas.

Inventario exacto:

1. `success`
2. `error`
3. `abstention`
4. `clarification`
5. `truncated`
6. `stream_aborted`
7. `eof_without_terminal`
8. `duplicate_terminal`
9. `error_after_tokens`
10. `abrupt_close`

`DOCUMENTED/PROPOSED`: la clave de correlación futura es `(run_id, nodeid B1-R, case_id, repetition ∈ {1,2,3})`; cada clave debe existir exactamente una vez. La matriz de rechazo contempla ausencias, extras/duplicados, repetición incorrecta, identidad de run/checkout/profile inconsistente, resultado funcional fallido, timeout/terminación anormal, schema inválido, artefacto no verificable, verifier no autorizado, evidencia de aislamiento insuficiente, Git ausente/no interpretable/diferente y subresultados contradictorios. La evidencia funcional, artefacto, aislamiento y Git se mantienen como dimensiones separadas.

**Límite importante:** el artefacto que describe el contrato/test actual contiene listas de observaciones por caso y el verifier contrasta tres elementos y su repetibilidad. La especificación futura añade `run_id`, identidad de worker y una repetición ordinal explícita en la clave. La correspondencia exacta entre esos campos futuros y el esquema/artifact actual no está implementada; el test actual declara `SOURCE_TRACED_NOT_RUNTIME_TESTED`. Clasificación de esta conexión actual/futura: `UNDERSPECIFIED` / `UNVERIFIED`, no contradicción.

Las 30 observaciones previstas no prueban aislamiento, una ejecución real, la validez del artefacto en esta fase ni la existencia de un controller o verifier externo.

## 4. Conservación de los once nodeids

Fuentes de clasificación:

- `config/test_perimeter.json` clasifica las suites `tests/unit` y `tests/audit` como `required`.
- `docs/TEST_CERTIFICATION_PERIMETER.md` define `required` para los perfiles `required` y `release`.
- STEP-18 y STEP-22 enumeran los once nodeids y declaran que cada uno conserva `required`; el inventario estático de tests confirma los nombres de función listados.

La configuración canónica enumera suites, no nodeids individuales. Por tanto, la clasificación `required` está verificada por herencia de suite y la lista nominal está verificada como inventario documental/staticamente presente; no existe en `config/test_perimeter.json` una lista individual que funcione como registry autoritativo de los once IDs. Para una autorización externa futura, el expected inventory debe fijarse en una policy autorizada fuera del checkout. Esta limitación se conserva, no se infiere autoridad externa.

| # | Nodeid | Suite y clasificación | Resultado del cotejo |
|---:|---|---|---|
| 1 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_maps_host_path_to_mounted_workspace` | `tests/unit` — `required` | Conservado; inventario STEP-18/22 y nombre estático presente. |
| 2 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_rejects_paths_outside_workspace` | `tests/unit` — `required` | Conservado; inventario STEP-18/22 y nombre estático presente. |
| 3 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_bubblewrap_denies_protected_paths_and_allows_derived_workspace` | `tests/unit` — `required` | Conservado; sin transferencia de ownership. |
| 4 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolation_fails_closed_when_bubblewrap_is_unavailable` | `tests/unit` — `required` | Conservado; sin transferencia de ownership. |
| 5 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolated_process_exit_code_is_preserved` | `tests/unit` — `required` | Conservado; el child sigue siendo subresultado del padre. |
| 6 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_active_virtual_environment_is_available_read_only_in_sandbox` | `tests/unit` — `required` | Conservado; sin reclasificación. |
| 7 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_synthetic_pytest_runs_inside_the_process_boundary` | `tests/unit` — `required` | Conservado; pytest child no sustituye el item parent. |
| 8 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_snapshot_contract_tests_run_without_git_or_production_mounts` | `tests/unit` — `required` | Conservado; sin reclasificación. |
| 9 | `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_focal_binding_is_validated_inside_bubblewrap` | `tests/unit` — `required` | Conservado; sin transferencia de ownership. |
| 10 | `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_isolated_focal_runner_propagates_binding_and_writes_receipt` | `tests/unit` — `required` | Conservado; el fake no se presenta como evidencia de aislamiento. |
| 11 | `tests/audit/test_b1_route_repeatability.py::test_synthetic_chat_route_is_repeatable_and_sterile` | `tests/audit` — `required` | Conservado; las 30 observaciones siguen siendo internas a un único item. |

**Adjudicación:** no se observó modificación de configuración/perímetro durante STEP-23C; los once nodeids y su obligación de suite continúan documentados como `required`. No se ejecutaron ni se aprobó una excepción, transferencia, exclusión o degradación.

## 5. Bloqueos por categoría

### A. Gobernanza externa

- Designar quién aprueba, vence, revoca y actualiza controller/policy/run.
- Definir la identidad verificable del responsable, su scope, delegaciones y registro de decisiones.
- Designar quién custodia y puede verificar el bootstrap/trust anchor; definir revisión independiente.
- Aprobar la política de checkout, perfiles, nodeids, roots, límites y ciclo de vida.

Ningún actor se nombra ni se considera autorizado por esta adjudicación.

### B. Diseño documental

- Cerrar el mecanismo check-to-use/TOCTOU y anti-rollback.
- Fijar schemas, identidad de cada productor/consumidor y enlace entre el artifact B1-R actual y la clave futura de 30 observaciones.
- Hacer inequívocos los estados/transiciones, retries, cardinalidades y precedencia de fallos.
- Fijar comandos/argv, mounts, roots, límites de recursos, paths de salida y política de parsing exacta.
- Definir la evidencia mínima y preservación externa para verifier, observador de aislamiento, Git y agregador.

Los documentos STEP-22 avanzan propuestas sustantivas, pero no todos esos detalles tienen valores aprobados o un contrato cerrado. No se presentan como implementación.

### C. Provisión y validación futura

- Proveer y verificar bootstrap/ancla independientes.
- Implementar controller y cadena de dependencias identificados fuera del checkout.
- Demostrar aislamiento efectivo con observador y evidencia independientes.
- Implementar y validar verifier/agregador autorizados.
- Ejecutar B1-R completo (30 observaciones) y resolver los once nodeids por perfil solo tras autorización específica.
- Preservar artefactos con identidad, provenance y resultados reproducibles.

Todo lo anterior sigue no implementado/no verificado mediante este trabajo documental; no puede cerrarse con documentación solamente.

## 6. Criterios verificables antes de una fase técnica futura

1. Decisión de gobernanza identificable que designa autoridad, alcance, revocación, actualización y revisión independiente.
2. Bootstrap/ancla instalada fuera del checkout, identidad/procedencia comprobables y pruebas fail-closed contra ausencia, invalidez, expiración, revocación, rollback y TOCTOU.
3. Inventario aprobado del controller/runtime/dependencias/configuración pre-worker y demostración de que los bytes validados son los bytes ejecutados.
4. Policy versionada con profiles, once nodeids requeridos, roots/mounts/capacidades, workspace, commands y límites; no ampliable desde el checkout.
5. Protocolo de host/worker/verifier/observador/agregador con schemas cerrados, run IDs, cardinalidad, retry/failure semantics y vínculo de artifacts.
6. Capturas Git host-side válidas y evidencia separada de escrituras/transitorios cuando se requiera una afirmación más fuerte que igualdad pre/post.
7. Evidencia independiente y reproducible del boundary de aislamiento efectivo; ni `bwrap` disponible, ni test pass, ni reporte del worker son suficientes.
8. Cobertura exacta: una obligación `required` por cada nodeid padre y perfil aplicable, sin permitir que children sustituyan al padre.
9. B1-R conserva los diez nombres y las tres repeticiones, con 30 claves únicas, artifacts verificados y rechazos probados; ninguna corrida se inicia sin autorización específica.
10. Revisión/adjudicación autorizada de resultados y contradicciones, conservando `UNKNOWN`/`BLOCKED` como tales.

La satisfacción documental de estos criterios no autoriza por sí sola ejecución, implementación, reapertura de P1.2 ni transición a P1.3.

## 7. Decisión final y límites demostrados

**Resultado:** `CONSISTENCY_ADJUDICATED_WITH_OPEN_BLOCKERS`.

La adjudicación cruzada de los cuatro documentos pudo realizarse: no se identificó contradicción directa que impida sostener el contrato propuesto. Se preservaron los aspectos underspecified y los blockers de autoridad/provisión; los documentos no se declaran completos ni desplegados. B1-R conserva su contrato 10 × 3 y las once obligaciones continúan documentadas como `required` por la clasificación autoritativa de sus suites, con el límite de que el JSON de perímetro no enumera nodeids individuales.

`OBSERVED`: rama/HEAD, presencia de documentos, clasificación de las dos suites, nombres estáticos de los once tests y contenido documental leído. `DOCUMENTED`: requisitos y blockers STEP-22 y estados históricos STEP-23A/B. `PROPOSED`: harness, protocolo y agregación futura. `UNVERIFIED`: ejecución de B1-R, aislamiento efectivo, bootstrap, autoridad externa, integridad del runtime y la reconciliación histórica del índice.

No se ejecutaron tests, scripts, hooks, builds, workers, Quality Gate ni código del repositorio. No se modificaron código, índice, configuración, refs ni perímetro. Solo se crearon los dos expedientes STEP-23C autorizados. El baseline actual no cambia `UNRESOLVED_HISTORICAL_EVIDENCE`.

**Estado canónico final:** `P1.2=BLOCKED-REGRESSION`; `P1.3=BLOCKED`. La implementación del harness y la ejecución de B1-R siguen no autorizadas.
