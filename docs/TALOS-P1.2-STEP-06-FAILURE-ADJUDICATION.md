# TALOS-P1.2-STEP-06 — Failure Adjudication

## 1. Resumen ejecutivo

Este expediente adjudica forensicamente los 15 fallos observados al ejecutar el Quality Gate canónico durante STEP-05. La evidencia primaria es el log original en `/media/agustin/Almacenamiento/Facultad/TALOS/historical-evidence/B06/talos-p1-2-b06-evidence-20261009/quality-gate-output.txt`, corroborado con inspección de los tests, el entorno de aislamiento y el código que implementa los contratos.

No se ejecutaron pruebas ni se repitieron gates durante STEP-06. No se hicieron cambios de código ni de configuración en esta fase. El resultado de la adjudicación es `ADJUDICATION_COMPLETE`.

Conclusión principal:

- Los 15 fallos no son 15 causas independientes; se agrupan en 5 causas raíz claras.
- La causa dominante es un conflicto de contrato entre el entorno de ejecución real del runner y las expectativas de los tests de sandbox/aislamiento.
- El benchmark B06 tampoco puede considerarse responsable directo: las fallas de `data/web_state/*.db` reflejan ausencia de fuente derivada dentro del worker, no corrupción del snapshot capturado.
- Existe un defecto real de producto en `KnowledgeStore`/SQLite URI handling y un defecto de producto en el logger de fabric.
- Existe un defecto de test en `tests/pedagogy/test_chat_sse_endpoint.py` por falta de `import sqlite3`.

## 2. Estado canónico preservado

- P1.1: CLOSED
- P1.2: BLOCKED-REGRESSION
- P1.3–P1.6: pendientes
- Captura B06: preparada y validada bajo policy `quiesced` según STEP-05
- Quality Gate: falló con 15 fallos, 3132 pases y 190 warnings
- No se autorizó ninguna corrección ni re-ejecución durante STEP-06

## 3. Inventario de los 15 fallos

| # | Nodeid | Categoría | Evidencia primaria |
|---|---|---|---|
| 1 | `tests/adversarial/contracts/test_protected_trust_root_adversarial.py::test_attack_4_unsealed_file_injection_fails` | `FIXTURE_OR_HARNESS_DEFECT` | `OSError: [Errno 30] Read-only file system` al escribir `tests/protected/test_rogue_adversarial_injection.py` |
| 2 | `tests/audit/test_b1_route_repeatability.py::test_synthetic_chat_route_is_repeatable_and_sterile` | `CONTRACT_MISMATCH` | `git -C /workspace/repository status ...` devuelve exit 128 porque `.git` no está accesible dentro del runner |
| 3 | `tests/benchmark/test_fase4_eval.py::test_dataset_integrity_error_on_in_domain_abstention` | `ENVIRONMENTAL_DEPENDENCY` | `FileNotFoundError: Vector store database not found: /workspace/repository/data/web_state/vector_store.db` |
| 4 | `tests/benchmark/test_fase4_eval.py::test_math_audit_consistency_and_ood_exclusion` | `ENVIRONMENTAL_DEPENDENCY` | mismo error de DB ausente |
| 5 | `tests/pedagogy/test_chat_sse_endpoint.py::test_fadena_std_real_corpus_isolation_on_temporary_database_copy` | `TEST_DEFECT` | `NameError: name 'sqlite3' is not defined` |
| 6 | `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_focal_binding_is_validated_inside_bubblewrap` | `CONTRACT_MISMATCH` | `Writable Quality Gate workspace must be under /tmp` |
| 7 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_bubblewrap_denies_protected_paths_and_allows_derived_workspace` | `CONTRACT_MISMATCH` | mismo error de raíz de workspace |
| 8 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolation_fails_closed_when_bubblewrap_is_unavailable` | `CONTRACT_MISMATCH` | el runner dispara el mensaje incorrecto: `Writable Quality Gate workspace must be under /tmp` en lugar de `bubblewrap is unavailable` |
| 9 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolated_process_exit_code_is_preserved` | `CONTRACT_MISMATCH` | mismo error de validación de raíz |
| 10 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_active_virtual_environment_is_available_read_only_in_sandbox` | `CONTRACT_MISMATCH` | mismo error de validación de raíz |
| 11 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_synthetic_pytest_runs_inside_the_process_boundary` | `CONTRACT_MISMATCH` | mismo error de validación de raíz |
| 12 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_snapshot_contract_tests_run_without_git_or_production_mounts` | `CONTRACT_MISMATCH` | mismo error de validación de raíz |
| 13 | `tests/unit/retrieval/test_query_rewriter.py::test_knowledge_store_search_hybrid_receives_prerewritten_query` | `PRODUCT_DEFECT` | `Path('sqlite:/workspace/...')` intenta crear un directorio llamado `sqlite:/workspace` |
| 14 | `tests/unit/retrieval/test_query_rewriter.py::test_retrieval_service_is_authoritative_rewriter_chokepoint` | `PRODUCT_DEFECT` | mismo fallo por URI SQLite sin parseo correcto |
| 15 | `tests/unit/retrieval/test_retrieval_fabric.py::test_fabric_trace_logger_rotation_and_json_event_f5` | `PRODUCT_DEFECT` | `assert 0 >= 1` al comprobar que `trace_logger.info` emitió evento JSON |

## 4. Matriz de clasificación causal

### 4.1. Causa raíz 1: conflicto de contrato del sandbox y del directorio temporal

**Fallas implicadas:** 6, 7, 8, 9, 10, 11, 12

**Evidencia directa:**

- `scripts/quality_gate_isolation.py` exige que el workspace writable sea un subdirectorio de `/tmp`.
- `run_isolated_process()` valida `workspace_root` con `_validate_mount_roots()` y lanza `IsolationError("Writable Quality Gate workspace must be under /tmp")`.
- El log de ejecución muestra que los tests crean `tmp_path` bajo `/workspace/run/pytest-tmp/...` y no bajo `/tmp/...`.
- El runner del gate-interno fija `TALOS_TEST_BASETEMP=/workspace/run/pytest-tmp` y crea `execution_root` bajo `/workspace/run`.

**Causalidad reproducible:**

Las pruebas usan `tmp_path` según el entorno del proceso actual; el contrato del sandbox exige un directorio writable dedicado bajo `/tmp` y, además, protege `.git` y las rutas de producción. El comportamiento de los tests está por tanto desalineado con el contrato del runner.

**Regla contractual que debería aplicarse:**

- Las pruebas de sandbox deben generar el workspace derivado bajo `/tmp` o un subdirectorio autorizado de `/tmp`.
- El repo protected, `.git` y `data/web_state` no deben exponerse dentro del worker.

**Por qué no es otra categoría:**

No es un fallo de `bwrap` en sí; no es un fallo de regresión de seguridad; es un desajuste entre el espacio de pruebas y la implementación del contrato de aislamiento.

### 4.2. Causa raíz 2: producción y guardas de aislamiento impiden acceso a bases protegidas o derivadas

**Fallas implicadas:** 1, 2, 3, 4

**Evidencia directa:**

- #1 intenta escribir en `tests/protected/test_rogue_adversarial_injection.py` y recibe `OSError: [Errno 30] Read-only file system`.
- #2 ejecuta `git -C /workspace/repository status ...` y falla con `exit 128` porque el worker no expone `.git`.
- #3 y #4 llaman a `run_benchmark`, que intenta abrir `data/web_state/vector_store.db` en lectura y recibe `FileNotFoundError`.
- `scripts/quality_gate_isolation.py` explícitamente enmascara `data/web_state` y `.git` dentro del sandbox.

**Causalidad reproducible:**

El worker de calidad está configurado para tener un checkout protegido / no montado. Los tests o benchmark que esperan acceder directamente a `.git` o a DBs protegidas están asumiendo una vista no autorizada del repositorio.

**Regla contractual que debería aplicarse:**

- No se debe acceder a `.git` ni a `data/web_state` directamente desde el worker.
- Las pruebas deben usar un workspace derivado/sintético o una copia controlada, no la fuente protegida.

**Por qué no es otra categoría:**

No se trata de un defecto de producto del sistema de seguridad; es una expectativa incorrecta de acceso a recursos protegidos por el propio contrato de aislamiento.

### 4.3. Causa raíz 3: error del test de pedagogía, no de código de producción

**Fallas implicadas:** 5

**Evidencia directa:**

- El traceback muestra `NameError: name 'sqlite3' is not defined` en `tests/pedagogy/test_chat_sse_endpoint.py:880`.
- El módulo no contiene `import sqlite3` en el bloque visible y el error ocurre al invocar `sqlite3.connect(copied_db)`.

**Causalidad reproducible:**

El test intenta hacer una conexión SQLite sin importar el módulo.

**Regla contractual que debería aplicarse:**

- Los tests deben importarse con los módulos necesarios antes de invocar APIs de SQLite.

**Por qué no es otra categoría:**

Es una falla directa del test; no hay evidencia de un defecto de producción en la conexión SQLite ni en el runtime.

### 4.4. Causa raíz 4: defectos reales de producto en SQLite URI handling

**Fallas implicadas:** 13, 14

**Evidencia directa:**

- `tests/unit/retrieval/test_query_rewriter.py` crea `KnowledgeStore(f"sqlite:///{tmp_path}/test_ks.db")`.
- `src/study_engine/storage/sqlite_engine.py` convierte cualquier valor distinto de `":memory:"` en `Path(db_path)`.
- Si `db_path` es `sqlite:/workspace/run/...`, el constructor intenta hacer `self.db_path.parent.mkdir(...)` sobre una ruta tipo `PosixPath('sqlite:/workspace')`, causando `OSError: [Errno 30] Read-only file system`.

**Causalidad reproducible:**

El productor intenta aceptar un URI SQLite de estilo `sqlite:///...`, pero la implementación no lo parsea; trata el literal como path del sistema de archivos.

**Regla contractual que debería aplicarse:**

- `KnowledgeStore`/`SQLiteStorageEngine` deben soportar URIs SQLite válidos o convertirlos a paths reales antes de crear el directorio padre.

**Por qué no es otra categoría:**

La prueba está validando una propiedad lógica claramente esperada del storage; la falla está en la implementación del producto y no en la configuración ni en el runner.

### 4.5. Causa raíz 5: defecto real de producto en el logger del retrieval fabric

**Falla implicada:** 15

**Evidencia directa:**

- `tests/unit/retrieval/test_retrieval_fabric.py` monkeypatcha `trace_logger.info` y luego ejecuta `RetrievalFabricLite.retrieve(...)` esperando al menos un evento.
- El log de prueba termina con `assert 0 >= 1` (`len(logged_lines) == 0`).
- El código del productor en `src/study_engine/retrieval/fabric.py` intenta registrar eventos JSON con `self.trace_logger.info(json.dumps(...))` al final del pipeline, pero la condición del test indica que el evento no se emitió en este escenario.

**Causalidad reproducible:**

El mecanismo de trace logging no produce la estructura esperada bajo las condiciones del test. Esto no parece ser un problema del sandbox; es un fallo del propio pipeline de observabilidad.

**Regla contractual que debería aplicarse:**

- La trazabilidad del retrieval debe producir un payload JSON estructurado y debidamente serializado cuando el pipeline ejecuta una recuperación válida.

**Por qué no es otra categoría:**

No hay corrección de runner ni un problema de entorno en la evidencia observada; es una falla en la implementación del trace logger.

## 5. Adjudicación específica del `NameError` de `sqlite3`

**Nodeid:** `tests/pedagogy/test_chat_sse_endpoint.py::test_fadena_std_real_corpus_isolation_on_temporary_database_copy`

**Evidencia relevante:**

- Log del gate: `NameError: name 'sqlite3' is not defined`
- En el bloque de prueba visible, la sentencia `sqlite3.connect(copied_db)` se ejecuta sin el import `sqlite3` en ese módulo.

**Conclusión:**

Es un defecto del test, no de la API de SQLite ni del runner. La corrección mínima propuesta es importar `sqlite3` al inicio del módulo antes de ejecutar la conexión.

**Prueba de regresión sugerida:**

- Reejecutar solo el nodeid del test con `pytest -q tests/pedagogy/test_chat_sse_endpoint.py -k fadena_std_real_corpus_isolation_on_temporary_database_copy`.

**Criterio de aceptación:**

- El test debe crear la copia del DB, abrir la conexión con `sqlite3.connect`, y completar sin `NameError`.

## 6. Relación entre causas primarias y secundarias

### 6.1. Grupo primario de aislamiento/sandbox

- `#6-#12` son fallos primarios del contrato de sandbox.
- Sus efectos se extienden a `#1` y `#2` porque el entorno que debería proteger el repo y ocultar `.git`/DBs no está alineado con la expectativa del test.

### 6.2. Grupo de dependencias ambientales

- `#3-#4` son fallos de acceso a recursos esperados (`data/web_state/vector_store.db`) bajo una vista protegida del repositorio.
- Estos no son fallos del snapshot B06 ni del manifest; son fallos de preparación del entorno del test dentro del runner.

### 6.3. Grupo de defectos de productos reales

- `#13-#15` son defectos demostrados en la implementación del producto.
- No dependen del runner para ser válidos.

## 7. Separación explícita entre problemas B06 y problemas del resto de la suite

### 7.1. Problemas que no implican directamente la captura B06

Los nodeids `#6-#12` y `#1-#2` son tests de aislamiento y verificación del runner, no pruebas específicas del snapshot B06 ni del contenido del manifiesto. Aun así, bloquean el gate porque el gate canónico exige que estos tests pasen.

### 7.2. Problemas que sí reflejan defectos de código del repositorio

- `#13-#14`: defectos de `KnowledgeStore`/SQLite path handling.
- `#15`: problema de trazabilidad del retrieval fabric.

### 7.3. Qué no se concluye

La presencia de estos fallos no invalida la captura B06 ni el expediente STEP-05 por sí sola. Lo que sí queda demostrado es que el Quality Gate canónico no está verde en este repositorio y que la causa raíz no es una sola regresión de negocio, sino una combinación de:

- contrato de aislamiento no alineado,
- acceso indebido a recursos protegidos,
- defectos de tests y de implementación.

## 8. Propuesta mínima de corrección por causa

| Causa | Archivos afectados | Objetivo | Riesgo | Prueba de regresión necesaria | Criterio de aceptación |
|---|---|---|---|---|---|
| Contrato sandbox / temp path mismatch | `scripts/quality_gate_isolation.py`, `tests/unit/diagnostics/test_quality_gate_isolation.py`, `scripts/quality_gate.py`, `tests/conftest.py` | Alinear `tmp_path` del runner con la política de `/tmp` o ajustar el contrato del worker | Reducir seguridad del sandbox si se relaja demasiado | Ejecutar solo el conjunto de tests de aislamiento | Los tests de aislamiento deben pasar sin exponer `.git`, DBs protegidas ni rutas de producción |
| Incorrecto uso de `.git` / accesos protegidos en tests | `tests/audit/test_b1_route_repeatability.py`, `tests/adversarial/contracts/test_protected_trust_root_adversarial.py`, `benchmark/run_fase4_eval.py` | Reforzar uso de workspace derivado o fixture sintético | Cambiar la intención de seguridad del gate | Ejecutar nodeids específicos de isolation / B1 / benchmark | Los tests deben verificar denegación o uso de workspace derivado, no acceso directo al repo |
| `sqlite3` import missing | `tests/pedagogy/test_chat_sse_endpoint.py` | Añadir `import sqlite3` | Mínimo | Ejecutar el nodeid del test pedagógico | El test debe abrir la copia de DB sin `NameError` |
| SQLite URI parsing defect | `src/study_engine/storage/sqlite_engine.py`, `src/study_engine/storage/knowledge_store.py` | Parsear `sqlite:///...` o manejar URIs de forma segura y determinista | Cambiar la semántica de la ruta para otros callers | Ejecutar `tests/unit/retrieval/test_query_rewriter.py` | Los `KnowledgeStore` creados con URI SQLite deben normalizarse a un path válido |
| Retrieval trace logger defect | `src/study_engine/retrieval/fabric.py`, `tests/unit/retrieval/test_retrieval_fabric.py` | Garantizar emisión JSON del evento `RETRIEVAL_FABRIC_TRACE` | Cambios de trazado sin afectar la lógica de recuperación | Ejecutar solo el nodeid F5 | Debe producir una entrada JSON con los campos esperados |

## 9. Estado de salida

`ADJUDICATION_COMPLETE`

Criterio cumplido:

- Los 15 fallos tienen una clasificación respaldada por evidencia suficiente.
- Se describieron causas primarias y secundarias.
- Se documentó qué parte corresponde a sandbox/contrato, qué parte a entorno/harness, qué parte a test defectuoso y qué parte a producto.
- P1.2 permanece `BLOCKED-REGRESSION`.

## 10. Evidencia de no modificación ni re-ejecución

Durante STEP-06 no se ejecutó `pytest`, `scripts/test.sh`, `scripts/quality_gate.py`, ni `scripts/prepare_test_snapshot.py`, no se modificó código, configuración, documentación canónica ni el worktree, y no se abrió la base protegida. La investigación constó exclusivamente de inspección en modo lectura de:

- `quality-gate-output.txt`
- `scripts/quality_gate.py`
- `scripts/quality_gate_isolation.py`
- `tests/conftest.py`
- `config/test_perimeter.json`
- `benchmark/run_fase4_eval.py`
- `tests/unit/retrieval/test_query_rewriter.py`
- `tests/unit/retrieval/test_retrieval_fabric.py`
- `tests/pedagogy/test_chat_sse_endpoint.py`
- `src/study_engine/storage/sqlite_engine.py`
- `src/study_engine/storage/knowledge_store.py`
- `src/study_engine/retrieval/fabric.py`

Este expediente queda listo para revisión humana y para que el responsable decida el próximo paso operativo sin reabrir el gate ni modificar código en esta fase.
