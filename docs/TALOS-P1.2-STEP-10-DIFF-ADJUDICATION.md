# TALOS-P1.2-STEP-10 — ADJUDICACIÓN DEL DIFF

**Estado de entrada:** `MINIMAL_CORRECTIONS_PARTIAL`  
**Estado del gate:** `P1.2 = BLOCKED-REGRESSION`  
**Tipo:** inspección estática; sin ejecución de pruebas  
**Resultado:** `DIFF_ADJUDICATION_PARTIAL`

## 1. Estado efectivo del repositorio

- Rama observada: `talos-current-audit`.
- HEAD observado: `cc8acfae623f9d10c8366871470319786b6a7ca4`.
- El worktree ya estaba sucio y contiene cambios staged, unstaged y untracked en múltiples áreas.
- Estado de los archivos clave en la inspección:

| Archivo | Estado observado | Consecuencia para atribución |
|---|---|---|
| `scripts/quality_gate.py` | unstaged modificado | El diff actual es visible, pero no prueba cuándo ni quién introdujo cada bloque |
| `scripts/quality_gate_isolation.py` | untracked | No hay comparación con HEAD que permita establecer origen histórico |
| `src/study_engine/storage/sqlite_engine.py` | unstaged modificado | El helper URI está en el diff actual; los expedientes STEP-07/08 ya lo describían antes de STEP-10 |
| `src/study_engine/retrieval/fabric.py` | sin cambio reportado | No se corrobora una corrección nueva del productor de eventos en el diff actual |
| `tests/pedagogy/test_chat_sse_endpoint.py` | staged y unstaged | El archivo tiene cambios en ambas capas; no todo puede atribuirse a una única fase |
| `tests/unit/retrieval/test_retrieval_fabric.py` | staged modificado | El diff visto trata autenticación del endpoint, no el test de logging F5 |
| `tests/unit/retrieval/test_query_rewriter.py` | sin cambio reportado | Las construcciones `sqlite:///...` están en el archivo actual, no en un diff de esta fase |
| Tests B1, B2 y `test_fase4_eval` | sin cambio reportado | No se observó una solución nueva en esos tests |
| Tests de aislamiento/focalización | untracked | No es posible atribuirlos a STEP-07 o STEP-09 solo con Git |

Los expedientes STEP-08 y STEP-09 describen varios cambios como ya existentes en esas fases. La inspección actual confirma parte de su presencia, pero no permite demostrar por sí sola su autoría. En particular, la afirmación de STEP-09 de que se corrigió `fabric.py` no queda corroborada por el estado/diff actual: el archivo no aparece modificado y el código de emisión observado no constituye un cambio actual.

## 2. Grupo A — raíces temporales y aislamiento

### Flujo observado

1. `scripts/quality_gate.py:1473-1477` crea un `TemporaryDirectory` con `dir="/tmp"` y construye `execution_root` como subdirectorio.
2. `scripts/quality_gate.py:1480` crea `execution_root/pytest-tmp`.
3. `scripts/quality_gate.py:1570-1575` calcula `pytest_tmp_root = execution_root / "pytest-tmp"` y lo entrega como valor de `TALOS_TEST_BASETEMP`.
4. `scripts/quality_gate.py:1591-1594` pasa `execution_root` como workspace a `run_isolated_process`.
5. `scripts/quality_gate_isolation.py:63-79` resuelve y valida ese workspace; rechaza de forma fail-closed los que no estén bajo `/tmp`, los symlinks y la superposición con el repositorio.
6. `scripts/quality_gate_isolation.py:283-292` crea un `/tmp` nuevo dentro del sandbox, monta el repositorio de solo lectura en `/workspace/repository` y monta el `execution_root` anfitrión con escritura en `/workspace/run`.
7. `scripts/quality_gate_isolation.py:399-412` reemplaza `.git` dentro del worker por un directorio vacío de solo lectura. Las raíces protegidas también se sustituyen por mounts vacíos de solo lectura (`:352-384`).
8. `scripts/quality_gate.py:1024-1026` pasa el valor de `TALOS_TEST_BASETEMP` directamente como `--basetemp` de pytest.

### Adjudicación

El `execution_root` anfitrión sí se crea bajo `/tmp`, y `_validate_mount_roots()` conserva la validación estricta. El repositorio no es writable dentro del worker, `.git` no se expone con su contenido, y las fuentes protegidas no se montan allí.

Sin embargo, `TALOS_TEST_BASETEMP` contiene la ruta anfitriona completa, por ejemplo `/tmp/talos-quality-gate-…/execution/pytest-tmp`. En el worker, `/tmp` es un `tmpfs` independiente; el directorio anfitrión se expone por el mount en `/workspace/run`, no por la misma ruta `/tmp/...`. No se observa una traducción de ese valor a `/workspace/run/pytest-tmp`. Por tanto, la ruta configurada no identifica estáticamente el directorio derivado que el runner montó: pytest puede resolver/crear un árbol homónimo dentro del tmpfs del worker, pero no sería el directorio anfitrión creado en `execution_root`.

- **Resultado requerido:** `STATICALLY_INCONSISTENT` respecto de la relación `TALOS_TEST_BASETEMP`–workspace montado.
- **Estado de implementación:** `PARTIAL`.
- **Contrato relevante:** workspace anfitrión bajo `/tmp`; mount writable limitado a `execution_root`; checkout y `.git` no writable ni visibles como recurso de escritura.
- **Riesgo residual:** la ubicación efectiva de `tmp_path` y su relación con el workspace del harness no se puede confirmar sin ejecución, y el valor de basetemp no está traducido a la identidad guest del mount.
- **No afirmado:** no se declara que el aislamiento haya sido demostrado dinámicamente.

## 3. Grupo B — checkout, Git y benchmark

### B1. Escritura adversarial

El fixture `protected_dir` de `tests/adversarial/contracts/test_protected_trust_root_adversarial.py:26-29` devuelve la ruta real `repo_root/tests/protected`. El caso `test_attack_4_unsealed_file_injection_fails` (`:118-135`) escribe `test_rogue_adversarial_injection.py` directamente allí, lee el manifest y borra el archivo en `finally`.

No hay en el test inspeccionado un fixture sintético/desechable para esa operación ni una assertion que espere una denegación de escritura. El objetivo nominal —demostrar que el archivo no sellado no integra el manifest— no justifica mutar el checkout real; con el checkout protegido de solo lectura, la escritura falla antes de evaluar esa propiedad.

- **Clasificación:** `NOT_IMPLEMENTED`.
- **Estado de implementación:** `NOT_IMPLEMENTED`.
- **Contrato:** no escribir en el checkout protegido; un intento adversarial debe dirigirse a una representación sintética desechable y mantener una assertion explícita sobre la denegación que se pretende demostrar.
- **Riesgo residual:** ejecutar este caso en el runner real continúa intentando escribir en `tests/protected`.
- **Validación pendiente:** nodeid #1 de la lista de STEP-06, tras una solución que pruebe la propiedad sin tocar el checkout.

### B2. Repetibilidad y Git

`tests/audit/test_b1_route_repeatability.py:30-108` realiza ambas comprobaciones:

- La ruta sintética se ejecuta en un subprocess con cwd, HOME y TMPDIR separados (`:34-73`); se valida el artefacto funcional y su resultado (`:79-105`).
- La prueba también obtiene el estado Git antes y después con `_git_status(repo_root)` (`:56`, `:106-108`); el helper ejecuta `git -C <repo_root> status --porcelain --untracked-files=all` (`:111-125`).

El subprocess funcional está aislado en un cwd temporal, pero la llamada a Git sigue siendo parte del proceso pytest, que durante el Quality Gate corre dentro del worker. No se trasladó esta comprobación a una capa host/harness ni se separó documentalmente su evidencia de la repetibilidad funcional. El estado Git y la repetibilidad son propiedades distintas: comparar el artefacto cubre la primera; la comparación del status cubre efectos sobre el checkout.

- **Clasificación:** `PARTIAL`.
- **Estado de implementación:** `PARTIAL`.
- **Contrato:** `.git` no se expone al worker; no debilitar el aislamiento para que el test consulte Git.
- **Riesgo residual:** el test conserva una dependencia de `.git` dentro del entorno donde se ejecuta pytest.
- **Validación pendiente:** nodeid #2; una solución debe preservar tanto la assertion funcional como una verificación del estado Git realizada fuera del worker por un componente autorizado.

### B3. `test_fase4_eval`

Los dos nodeids exactos adjudicados son:

- `tests/benchmark/test_fase4_eval.py::test_dataset_integrity_error_on_in_domain_abstention`
- `tests/benchmark/test_fase4_eval.py::test_math_audit_consistency_and_ood_exclusion`

El primero invoca `run_benchmark()` en `tests/benchmark/test_fase4_eval.py:222-258`; el segundo lo invoca con `output_dir=tmp_path` en `:308-347`. `output_dir` redirige resultados, no las bases que usa el benchmark. En `benchmark/run_fase4_eval.py:98-125`, `run_benchmark()` inicializa `KnowledgeStore` con `data/web_state/knowledge_store.db` y `SQLiteVectorStore` con `data/web_state/vector_store.db` antes de procesar el dataset.

En los bloques de test revisados no aparece un fixture sintético/derivado para esas dos bases. La inspección no abrió ni copió dichas bases.

- **Clasificación:** `NOT_IMPLEMENTED`.
- **Estado de implementación:** `NOT_IMPLEMENTED`.
- **Contrato:** los tests no deben requerir acceso a producción; no añadir un fallback silencioso a esas rutas.
- **Riesgo residual:** ambos casos llaman al benchmark contra las rutas del repositorio y fallan si esos recursos no están presentes en el perímetro autorizado.
- **Validación pendiente:** nodeids #3 y #4. Hace falta fixture sintético fiel a las propiedades probadas o una decisión documentada de que esos casos no son ejecutables en este perímetro; no se puede asumir equivalencia del fixture.

## 4. Grupo C — import de `sqlite3`

En `tests/pedagogy/test_chat_sse_endpoint.py:7` existe ahora `import sqlite3`; la referencia que lo requiere está en `:881`, en el ámbito del test que ejecuta `sqlite3.connect(copied_db)`. El diff sustituye el import local anterior por el import del módulo y usa `knowledge_store_test_copy`; no se observa duplicación de `sqlite3`.

La dependencia de fixture también reemplaza el acceso/copia directa desde `data/web_state/knowledge_store.db` por la copia de test. Esa modificación está en el diff actual, pero no se atribuye exclusivamente a STEP-10; STEP-08 ya registraba el import.

- **Estado máximo:** `IMPLEMENTED_UNVALIDATED`.
- **Contrato:** fixture derivado y sin lectura directa de la base protegida; el import está en el scope requerido.
- **Riesgo residual:** no hay confirmación dinámica del caso ni del nuevo encadenamiento del fixture.
- **Validación pendiente:** `tests/pedagogy/test_chat_sse_endpoint.py::test_fadena_std_real_corpus_isolation_on_temporary_database_copy` (nodeid #5).

## 5. Grupo D — contrato y normalización SQLite

### Evidencia del contrato y callers

- `SQLiteStorageEngine.__init__` acepta `Union[str, Path]` y usa `:memory:` por defecto (`src/study_engine/storage/sqlite_engine.py:279-286`); `KnowledgeStore` publica la misma forma de argumento (`src/study_engine/storage/knowledge_store.py:112-115`).
- La documentación visible de estas interfaces no define sintaxis de URI.
- Los tests `tests/unit/retrieval/test_query_rewriter.py:123,148` pasan `sqlite:///...` a `KnowledgeStore`, pero la presencia en tests no adjudica por sí sola el contrato público.
- `src/study_engine/config.py:31` define `database_url` con default `sqlite:///./data/storage/knowledge.db`, pero la búsqueda de consumidores en `src/` solo encontró esa declaración; no se halló un flujo que lo pase a `SQLiteStorageEngine`.
- La CLI usa URIs `file:...?...mode=ro` directamente con `sqlite3.connect(..., uri=True)` (`src/study_engine/cli.py:82,206,363`), no a través de `SQLiteStorageEngine`. Esto demuestra uso de URI en el conector directo, no soporte de URI en esta API.

### Comportamiento estático por formato

| Formato | Transformación observada | Evidencia contractual / resultado |
|---|---|---|
| `:memory:` | Se mantiene como `":memory:"`; `connect()` usa `sqlite3.connect(":memory:")` (`sqlite_engine.py:18-23,307`) | Semántica en memoria visible y sin ruta de disco; compatible con la interfaz actual |
| Ruta normal | Se transforma en `Path(value)` (`:36`) y el engine conecta con `str(self.db_path)` (`:323`) | Compatible con interfaz `str | Path` |
| `sqlite:///...` | `urlparse(value).path` pasa a `url2pathname(unquote(...))`, y luego a `Path` (`:25-34`) | Aparece en tests, pero no hay contrato documentado suficiente; `UNRESOLVED` |
| `sqlite:////...` | Utiliza igualmente `parsed.path`; no hay regla separada que adjudique autoridad o normalización de barra inicial | Tratamiento de ruta absoluta no especificado contractualmente; `UNRESOLVED` |
| `file://...` | Extrae `parsed.path` y lo convierte a `Path` (`:25-34`) | Las URI `file:` del CLI pertenecen al uso directo de `sqlite3`, no prueban soporte de esta API; `UNRESOLVED` |
| URI con query | `urlparse` separa query y el helper no la incorpora al path ni configura `uri=True` en la conexión del engine (`:25-34,323`) | Parámetros no preservados/interpretados por el engine; sin contrato para aceptarlos |
| URI de memoria compartida | Las dos cadenas exactas de memoria compartida se mapean a `":memory:"` (`:22-23`) | No preserva la semántica compartida entre conexiones; comportamiento silencioso distinto |
| Vacía o malformada | Cadena vacía retorna `":memory:"` (`:17-19`); URI sin candidato también puede retornar `":memory:"` (`:31-34`) | No rechaza explícita ni determinísticamente; riesgo de sustituir entrada inválida por almacenamiento volátil |

### Decisión contractual

**Decisión:** `UNRESOLVED`.

La evidencia no basta para declarar `FILESYSTEM_PATHS_ONLY` (hay callers de test y un default configurativo con URI), ni `FILESYSTEM_PATHS_AND_SQLITE_URIS` (no hay documentación de API ni consumidor de producción confirmado que vincule el default URI con este engine). La decisión requiere aprobación del responsable del contrato de almacenamiento, incluyendo semántica de query, URI de memoria compartida y errores de entrada inválida.

- **Estado de implementación:** `UNRESOLVED`; el helper existe en el diff actual, pero el alcance admitido no está adjudicado y su comportamiento para entradas ambiguas no es fail-closed.
- **Riesgo residual:** query params ignorados, URI shared-memory reducida a memoria privada y cadena vacía convertida en memoria.
- **Validación pendiente:** nodeids #13 y #14, después de resolver el contrato; no se valida aquí.

## 6. Grupo E — evento JSON de Retrieval Fabric

### Flujo estático

1. `get_retrieval_trace_logger()` obtiene el logger nombrado `study_engine.retrieval.fabric` (`src/study_engine/retrieval/fabric.py:35-54`); `RetrievalFabricLite.__init__` guarda ese resultado (`:77`).
2. En el retorno anticipado de Symbol Guard se construye un evento `SYMBOL_GUARD_BLOCKED` y se llama a `self.trace_logger.info(json.dumps(...))` (`:106-123`).
3. En el recorrido normal se construye `RETRIEVAL_FABRIC_TRACE` en `:165-179`; no hay una condición explícita de habilitación del logging alrededor de esa llamada. La ruta está dentro de un `try`; errores se capturan y se envían a `logger.debug` (`:180-181`).
4. `get_retrieval_trace_logger()` configura un `RotatingFileHandler` de 10 MiB y cinco backups (`:38-53`).
5. El test obtiene el mismo logger mediante `get_retrieval_trace_logger()`, sustituye `trace_logger.info` por `mock_info` y acumula el argumento en `logged_lines` (`tests/unit/retrieval/test_retrieval_fabric.py:129-143`).
6. La assertion documentada como fallida es `assert len(logged_lines) >= 1` (`:157`), antes de parsear el JSON y comprobar su estructura (`:158-165`).

El diff actual no modifica `src/study_engine/retrieval/fabric.py`. El cambio observado en `tests/unit/retrieval/test_retrieval_fabric.py` añade una configuración sintética de token administrativo y actualiza el test del endpoint de inspección; no modifica el test F5 ni su observación mediante monkeypatch. Por tanto, no se corrobora que STEP-09 haya corregido la causa.

Estáticamente, el test y el constructor parecen obtener el logger del mismo nombre y la ruta normal llama a `info`; no obstante, la existencia de esa llamada no demuestra que el caso concreto llegue a ella ni explica el resultado previo vacío. La evidencia disponible tampoco permite adjudicar si el fallo original fue producción, logger/handler, instrumentación del test o una condición anterior en la ejecución.

- **Clasificación:** `UNRESOLVED`.
- **Estado de implementación:** `UNRESOLVED` (no hay cambio de productor corroborado en el diff actual).
- **Contrato:** evento estructurado JSON, preservando rotación y campos esperados; no fabricar llamadas/eventos ni reducir assertions.
- **Riesgo residual:** permanece el fallo original registrado; la ruta de ejecución concreta no se puede establecer de manera concluyente solo por inspección.
- **Validación pendiente:** nodeid #15, solo en una fase autorizada posterior.

## 7. Matriz final

| Grupo | Estado de implementación | Evidencia exacta | Contrato relevante | Riesgo residual | Validación dinámica pendiente |
|---|---|---|---|---|---|
| A | `PARTIAL` — `STATICALLY_INCONSISTENT` | `quality_gate.py:1473-1480,1570-1594`; `quality_gate_isolation.py:63-79,283-292` | workspace anfitrión bajo `/tmp`; guest tmpfs y mount `/workspace/run` separados | `TALOS_TEST_BASETEMP` no está traducido a la ruta guest del workspace montado | nodeids #6–12 |
| B1 | `NOT_IMPLEMENTED` | test adversarial `:26-29,118-135` escribe en el checkout real | no escribir en checkout; adversarial sobre recurso sintético/desechable | el escenario falla al escribir en checkout read-only y no verifica la denegación como resultado esperado | nodeid #1 |
| B2 | `PARTIAL` | B1-R `:30-108,111-125` verifica artefacto y también ejecuta Git desde pytest | no exponer `.git` al worker; preservar ambas propiedades separadamente | consulta de Git permanece dentro del proceso de test | nodeid #2 |
| B3 | `NOT_IMPLEMENTED` | test `:222-258,308-347`; benchmark `:98-125` usa rutas `data/web_state` | no acceder a DB protegida ni fallback de producción | no hay fixture sintético en esos casos | nodeids #3–4 |
| C | `IMPLEMENTED_UNVALIDATED` | chat SSE `:7,881`; diff de `knowledge_store_test_copy` | import correcto y fixture derivado, sin DB protegida directa | falta ejecución del test y verificación del fixture | nodeid #5 |
| D | `UNRESOLVED` | engine `sqlite_engine.py:12-36,279-323`; `KnowledgeStore:112-115`; callers documentados arriba | decisión pública sobre paths/URI pendiente; entradas inválidas no deben degradarse silenciosamente | query descartada, memoria compartida no preservada, entrada vacía convertida a memoria | nodeids #13–14 tras adjudicación |
| E | `UNRESOLVED` | `fabric.py:35-54,77,106-123,165-181`; test `test_retrieval_fabric.py:129-165` | evento JSON y rotación sin debilitar observabilidad/assertions | causa previa no adjudicada; diff actual no modifica productor ni test F5 | nodeid #15 |

`IMPLEMENTED_UNVALIDATED` no equivale a `VALIDATED`; ningún grupo dependiente de ejecución queda validado en STEP-10.

## 8. Nodeids pendientes de validación dinámica

Se conservan los nodeids exactos del inventario STEP-06. No se sustituyeron ni se ejecutaron:

1. `tests/adversarial/contracts/test_protected_trust_root_adversarial.py::test_attack_4_unsealed_file_injection_fails`
2. `tests/audit/test_b1_route_repeatability.py::test_synthetic_chat_route_is_repeatable_and_sterile`
3. `tests/benchmark/test_fase4_eval.py::test_dataset_integrity_error_on_in_domain_abstention`
4. `tests/benchmark/test_fase4_eval.py::test_math_audit_consistency_and_ood_exclusion`
5. `tests/pedagogy/test_chat_sse_endpoint.py::test_fadena_std_real_corpus_isolation_on_temporary_database_copy`
6. `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_focal_binding_is_validated_inside_bubblewrap`
7. `tests/unit/diagnostics/test_quality_gate_isolation.py::test_bubblewrap_denies_protected_paths_and_allows_derived_workspace`
8. `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolation_fails_closed_when_bubblewrap_is_unavailable`
9. `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolated_process_exit_code_is_preserved`
10. `tests/unit/diagnostics/test_quality_gate_isolation.py::test_active_virtual_environment_is_available_read_only_in_sandbox`
11. `tests/unit/diagnostics/test_quality_gate_isolation.py::test_synthetic_pytest_runs_inside_the_process_boundary`
12. `tests/unit/diagnostics/test_quality_gate_isolation.py::test_snapshot_contract_tests_run_without_git_or_production_mounts`
13. `tests/unit/retrieval/test_query_rewriter.py::test_knowledge_store_search_hybrid_receives_prerewritten_query`
14. `tests/unit/retrieval/test_query_rewriter.py::test_retrieval_service_is_authoritative_rewriter_chokepoint`
15. `tests/unit/retrieval/test_retrieval_fabric.py::test_fabric_trace_logger_rotation_and_json_event_f5`

La lista procede del expediente STEP-06; no constituye autorización para ejecutar estos casos.

## 9. Límites observados y estado de salida

Durante STEP-10:

- No se modificó código, tests, configuración ni documentos previos.
- No se ejecutó `pytest`, `scripts/test.sh`, `scripts/quality_gate.py`, `scripts/prepare_test_snapshot.py`, benchmarks ni validaciones dinámicas.
- No se abrieron, copiaron ni consultaron bases protegidas.
- No se generó snapshot B06.
- No se realizaron staging, commits, resets ni limpieza del worktree.
- No se modificaron la rama, HEAD ni el índice. Este expediente nuevo queda como cambio documental no staged en el worktree.

**Salida:** `DIFF_ADJUDICATION_PARTIAL`  
**Gate:** `P1.2 = BLOCKED-REGRESSION`

La adjudicación queda parcial porque siguen sin resolverse la relación guest/host de `TALOS_TEST_BASETEMP`, el contrato URI público, la preparación funcional de B1–B3 y la causa del evento F5. No se autoriza STEP-11 ni la ejecución de pruebas por inferencia.
