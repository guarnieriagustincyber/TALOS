# TALOS-P1.2-STEP-05 — EJECUCIÓN Y ADJUDICACIÓN DEFINITIVA DE B06

## Resumen ejecutivo

```text
P1.2 = P1.2-BLOCKED-REGRESSION
CAPTURE = PREPARED_AND_VALIDATED_UNDER_VERSIONED_QUIESCED_POLICY
CANONICAL_QUALITY_GATE = FAIL
```

La captura local controlada y el snapshot sellado se prepararon usando el
método declarado `quiesced_file_copy`, no como snapshot atómico de filesystem.
La validación estructural, los chequeos SQLite sobre copias, la integridad del
snapshot y las pruebas unitarias focalizadas pasaron. El Quality Gate canónico
se ejecutó con el snapshot y las seis identidades enlazadas, lanzó pytest y
terminó con **15 fallos, 3132 pases y 190 warnings** (`exit 1`). No se repararon
los fallos ni se intentó otra ejecución. P1.2 no se cierra.

## 1. Estado inicial y preservación

- Repositorio: `/media/agustin/Laboratorio/study-engie`
- Rama: `talos-current-audit`
- HEAD inicial/final: `cc8acfae623f9d10c8366871470319786b6a7ca4`
- El worktree ya estaba muy modificado, con cambios staged, unstaged y
  untracked. No se descartaron, limpiaron, restagearon ni sobrescribieron
  cambios preexistentes. No se creó rama.
- La inspección de procesos no encontró procesos TALOS/Uvicorn/Gunicorn activos.
  `lsof` no informó handles abiertos sobre las fuentes B06 inmediatamente
  antes de la captura. Esto acredita el estado observado en esas inspecciones,
  no una garantía universal de ausencia de procesos que pudieran reabrirlas.
- Los archivos pertinentes de contrato y código tenían cambios preexistentes.
  Se trabajó sobre su contenido vigente y se dejaron sus estados staged y
  unstaged como estaban; no se modificó `scripts/quality_gate.py`.

## 2. Fuentes físicas y método

Por la decisión explícita de la directiva delegada, se utilizó el conjunto
runtime web:

| Identidad | Ruta fuente |
|---|---|
| `knowledge_store` | `data/web_state/knowledge_store.db` |
| `vector_store` | `data/web_state/vector_store.db` |
| `student_state` | `data/web_state/student_state.db` |

La política de StudentState fue preservar el estado persistido existente, sin
reconstrucción ni fusión con `data/student/student_state.db`.

Antes de capturar se verificaron ruta, existencia y metadatos de archivos; no
se abrió ninguna base protegida con SQLite. Se comprobó inventario de
sidecars:

| Base | `-wal` | `-shm` | `-journal` |
|---|---|---|---|
| `knowledge_store.db` | presente, 0 bytes | presente, 32768 bytes | ausente |
| `vector_store.db` | presente, 16512 bytes | presente, 32768 bytes | ausente |
| `student_state.db` | presente, 0 bytes | presente, 32768 bytes | ausente |

No se encontraron handles abiertos ni procesos web de TALOS en las
comprobaciones previas. Por tanto, no se detuvieron servicios ni escritores.
Se utilizó una copia de archivos con verificación de no-handle antes y después
y de estabilidad de fingerprints de origen durante la copia. No se declaró
atomicidad a nivel filesystem ni consistencia SQLite transaccional entre las
tres bases.

### Clasificación precisa de la garantía

- Método: `quiesced_file_copy`
- Consistencia declarada: `quiesced`
- Perfil de datos: `talos.b06.snapshot.v1`
- Policy de captura: `talos.b06.quiesced-consistency.v1`
- `read_only=true` significa únicamente que la operación de copia no escribe
  en los archivos fuente. No afirma que un cierre/checkpoint anterior nunca
  hubiera escrito en ellos.
- La copia se rechazó si `lsof` no estaba disponible, si había handles, si la
  inspección era inconclusa o si los fingerprints de origen cambiaban durante
  la ventana.
- Límite residual: ausencia de handles y fingerprints estables no constituyen
  prueba matemática de atomicidad ni autentican externamente la procedencia.

## 3. Cambios acotados

La directiva autorizó un perfil versionado alternativo si no existía un
snapshot atómico aplicable. No se reutilizó ni redefinió
`atomic_filesystem_snapshot`.

- [config/test_perimeter.json](../config/test_perimeter.json): se declaró una
  policy de captura quiesced separada y se incluyó el nuevo capturador entre
  los inputs efectivos del gate.
- [test_isolation_snapshots.py](../src/study_engine/diagnostics/test_isolation_snapshots.py):
  se mantuvo el formato atómico v2 y se agregó el formato v3 quiesced,
  aceptado únicamente bajo la policy declarada, con método, consistencia,
  run/gate/policy, inventario y verificación compatibles.
- [capture_quiesced_test_sources.py](../scripts/capture_quiesced_test_sources.py):
  se agregó una CLI limitada al conjunto B06, que usa lectura `O_NOATIME`,
  exige UUIDv4, verifica handles y estabilidad, copia sin escribir en las
  fuentes y emite una attestation que identifica la captura como quiesced.
- [prepare_test_snapshot.py](../scripts/prepare_test_snapshot.py): se ajustó
  la descripción de la CLI para no presentarla como consumidora exclusiva de
  snapshots atómicos.
- [test_test_isolation_snapshots.py](../tests/unit/diagnostics/test_test_isolation_snapshots.py):
  se añadieron pruebas sintéticas de aceptación del perfil quiesced, rechazo
  de policy desconocida, rechazo ante handles y preservación de fuentes.
- [TEST_CERTIFICATION_PERIMETER.md](./TEST_CERTIFICATION_PERIMETER.md): se
  documentaron alcance y límites de la policy local.

No se modificaron lógica pedagógica, BKT, SM-2, retrieval ni APIs de usuario.
Los cambios no se staged ni committed. La confianza local explícita no es
autenticación criptográfica independiente ni certificación de tercero.

## 4. Captura, attestation y snapshot

- Directorio externo de captura:
  `/media/agustin/Almacenamiento/Facultad/TALOS/historical-evidence/B06/talos-p1-2-b06-capture-20261009`
- `capture_id`:
  `670eb410-815a-4629-9fd7-98c5dee8bc85`
- `run_id`:
  `745edebe-1428-4e17-bcf4-7470b44c4339`
- Scope: `talos.b06.snapshot.v1`
- Gate: `talos-p1.2-b06-quality-gate-v1`
- Policy: `talos.b06.quiesced-consistency.v1`
- Frescura: 3600 segundos desde `created_at` de la captura.
- Attestation: método `quiesced_file_copy`, consistencia `quiesced`,
  `read_only=true`, autoridad declarada
  `project-delegated-local-executor`, modelo
  `local_integrity_only`.
- SHA-256 de la attestation:
  `sha256:a3184c5a34f9c01dff1c4ec981eef5fa69366a2ccb129afe6546e09640cc01fa`
- El digest se calculó mediante un proceso local separado y se guardó fuera
  del directorio de captura. Esto aporta integridad y trazabilidad local, no
  autenticación criptográfica independiente.
- Registro externo:
  `/media/agustin/Almacenamiento/Facultad/TALOS/historical-evidence/B06/talos-p1-2-b06-evidence-20261009/attestation-verification.txt`

La CLI oficial preparó:

- Snapshot:
  `/media/agustin/Almacenamiento/Facultad/TALOS/historical-evidence/B06/talos-p1-2-b06-snapshot-20261009`
- Formato de manifest: 3
- Método/consistencia: `quiesced_file_copy` / `quiesced`
- SHA-256 del manifiesto:
  `sha256:0a69d377a2bb18651a0f2203d0a38ea3bf2c365b1c6e0958bb0bc4f1463028f2`
- `PRAGMA integrity_check` en copias del payload: `passed` para las tres DB.
- Estados WAL/SHM/journal del snapshot: coinciden con el inventario mostrado
  arriba.
- Verificación independiente posterior: `validate_snapshot=VALID` y
  `verify_sealed_snapshot` completó sin error. El snapshot volvió a validarse
  después del gate y permaneció `VALID`.
- Los archivos de captura y payload sellado quedaron con permisos read-only;
  captura/snapshot están fuera del repositorio.

## 5. Verificación de código

- Pruebas focalizadas:
  `.venv/bin/python -m pytest tests/unit/diagnostics/test_test_isolation_snapshots.py -q`
  → **14 passed**.
- Ruff sobre los nuevos surfaces y test:
  → **All checks passed**.
- Ruff `--select F` sobre `test_isolation_snapshots.py`:
  → **All checks passed**.
- `py_compile` sobre el capturador, preparador y módulo snapshot:
  → exit 0.
- `git diff --check`:
  → exit 0.

## 6. Quality Gate canónico

Comando ejecutado: `./scripts/test.sh`, con:

```text
TALOS_TEST_SNAPSHOT_ROOT=/media/agustin/Almacenamiento/Facultad/TALOS/historical-evidence/B06/talos-p1-2-b06-snapshot-20261009
TALOS_TEST_SNAPSHOT_MANIFEST_SHA256=sha256:0a69d377a2bb18651a0f2203d0a38ea3bf2c365b1c6e0958bb0bc4f1463028f2
TALOS_TEST_SNAPSHOT_SCOPE=talos.b06.snapshot.v1
TALOS_TEST_RUN_ID=745edebe-1428-4e17-bcf4-7470b44c4339
TALOS_TEST_GATE_ID=talos-p1.2-b06-quality-gate-v1
TALOS_TEST_POLICY_ID=talos.b06.quiesced-consistency.v1
```

- Inicio: `2026-10-09T15:49:19-03:00`
- Fin: `2026-10-09T15:59:58-03:00`
- Salida: `15 failed, 3132 passed, 190 warnings in 587.72s`
- Exit code: `1`
- Resultado del gate: `TEST GATE FAIL — release qualification is not established.`
- No hubo pruebas omitidas en las suites requeridas; las dos pruebas de
  integración de red/modelo real quedaron fuera por ser opcionales según el
  perímetro.
- El nodeid focal B06 no aparece en la lista completa de fallos; su suite
  (`tests/pedagogy`) reportó 114 pasadas y un fallo en otro test. El gate
  completo, sin embargo, falló y no permite cerrar P1.2.
- Salida íntegra preservada fuera del repositorio en
  `/media/agustin/Almacenamiento/Facultad/TALOS/historical-evidence/B06/talos-p1-2-b06-evidence-20261009/quality-gate-output.txt`.

### Fallos del gate

1. `tests/adversarial/contracts/test_protected_trust_root_adversarial.py::test_attack_4_unsealed_file_injection_fails` intentó crear un archivo bajo
   `/workspace/repository/tests/protected`, montado read-only.
2. `tests/audit/test_b1_route_repeatability.py::test_synthetic_chat_route_is_repeatable_and_sterile` falló al consultar
   `git status` en `/workspace/repository` dentro del entorno aislado.
3. Dos pruebas de `tests/benchmark/test_fase4_eval.py` no encontraron
   `/workspace/repository/data/web_state/vector_store.db` en el sandbox.
4. `tests/pedagogy/test_chat_sse_endpoint.py::test_fadena_std_real_corpus_isolation_on_temporary_database_copy` falló con `NameError: sqlite3 is not defined`.
5. Siete pruebas de `tests/unit/diagnostics/test_quality_gate_isolation.py`
   y `tests/unit/diagnostics/test_quality_gate_focal_execution.py` fallaron
   porque el `tmp_path` del entorno fue `/workspace/run/pytest-tmp/...`, fuera
   de la ruta `/tmp` que exigen esos tests.
6. Dos pruebas de `tests/unit/retrieval/test_query_rewriter.py` trataron una
   ruta `sqlite:/workspace/...` como ruta de filesystem y fallaron al crear
   directorios en el mount read-only.
7. `tests/unit/retrieval/test_retrieval_fabric.py::test_fabric_trace_logger_rotation_and_json_event_f5` también falló; el traceback
   completo se conserva en el log externo.

Los resultados revelan fallos fuera del alcance de cambios permitido
(aislamiento del harness, supuestos del entorno, test de pedagogy y benchmark
no disponible bajo el sandbox). No se modificaron esas áreas ni se repitió el
gate. No se adjudica causa raíz común a los quince fallos.

## 7. Protección y restauración

- No se detuvieron servicios ni escritores.
- No se abrió ninguna base original con SQLite; la validación SQLite fue
  únicamente sobre copias temporales del snapshot.
- La preparación del workspace del gate fue derivada del snapshot. Los
  originales no fueron montados como workspace de pytest según el contrato del
  runner.
- Metadatos no invasivos post-gate de las nueve rutas fuente/sidecar
  conservaron tamaño, mtime, ctime e inode observados antes de la captura.
  No se hizo una nueva lectura de contenido de las DB para esa comprobación.
- No había procesos TALOS web que restaurar antes ni después.
- La captura, el snapshot y los logs se preservaron; no se limpiaron.

## 8. Incidencias residuales y cierre

La captura y el snapshot están verificados según la policy local quiesced
versionada. Esto no equivale a un snapshot atómico ni a autenticación externa.
El Quality Gate canónico falló con 15 pruebas; la suite completa no quedó
calificada y P1.2 no se cierra.

```text
P1.2-BLOCKED-REGRESSION
```

El primer bloqueo posterior a la preparación fue el resultado no-cero del
Quality Gate. El siguiente paso permitido es revisión humana del informe y del
log preservado. No se aplicaron correcciones ni se inició P1.3.
