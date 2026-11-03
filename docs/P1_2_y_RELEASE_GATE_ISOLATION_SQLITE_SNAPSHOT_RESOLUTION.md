# P1.2.y — RELEASE GATE ISOLATION / SQLITE SNAPSHOT RESOLUTION

## 1. Objective

Resolver la frontera de almacenamiento del Release Gate y la preparación de
snapshots SQLite con WAL, sin ejecutar `./scripts/test.sh`, sin ejecutar B06 o
B10 y sin modificar manualmente datos bajo `data/`.

**Estado de salida: BLOCKED.** Se implementó y verificó focalmente el backup
SQLite a destinos temporales, pero una prueba sintética observó cambios en
metadatos del archivo `-shm` al abrir una fuente WAL con conexión read-only.
Además, no se registró una huella previa que permita demostrar la integridad
post-test de los sidecars de producción accedidos durante la primera corrida
focal. No se afirma esterilidad global ni se autoriza el Release Gate.

## 2. Isolation Contract Adopted

Se aplicó el contrato:

```text
protected SQLite source opened with mode=ro
        ↓ SQLite Connection.backup()
temporary standalone database
        ↓
writable test state
```

- **PROVEN (implementación):** el origen se pasa a SQLite mediante URI
  `mode=ro`; el destino se crea en el path entregado por fixture/test.
- **PROVEN (pruebas sintéticas):** la copia contiene el commit presente en WAL,
  se puede escribir en ella y las consultas a la fuente conservan su estado.
- **NOT DEMONSTRATED:** que abrir/cerrar una fuente WAL no cause ningún cambio
  de filesystem en sus sidecars. En particular, el test sintético observó
  cambios de bytes en `-shm`.
- **UNKNOWN:** integridad post-test de los sidecars de producción durante la
  primera validación focal; no se conservaron hashes previos de esos sidecars.

## 3. Files Changed

Cambios de esta directiva:

- `src/study_engine/diagnostics/gate2_snapshots.py`: se hizo reutilizable el
  backup read-only que ya usaba Gate 2 y se añadió rechazo de source/destination
  idénticos.
- `tests/conftest.py`: `web_state_test_copy` y
  `knowledge_store_test_copy` delegan en SQLite backup, sin copiar solamente
  el archivo principal ni bloquear por WAL no vacío.
- `tests/adversarial/test_c5_trust_gate.py`: el fixture C5 usa
  `knowledge_store_test_copy`.
- `tests/unit/diagnostics/test_gate2_snapshots.py`: regresiones sintéticas para
  fuente WAL, destino writable, source/destination inválidos y preservación de
  los bytes del `.db` y `-wal`.
- `tests/e2e/test_study_loop_e2e.py`: los DBs de conocimiento y estudiante se
  snapshottean en vez de copiar solo sus archivos principales.
- `tests/pedagogy/test_chat_sse_endpoint.py`,
  `tests/web/test_chat_fastpath_conversational.py`,
  `tests/integration/test_unified_study_session.py`,
  `tests/adversarial/session/test_unified_session_adversarial.py` y
  `tests/unit/student/test_memory_extractor.py`: cuando copian la base
  persistente para un container writable, parten del snapshot compartido.

`tests/pedagogy/test_chat_sse_endpoint.py` ya tenía cambios locales antes de
esta directiva; se preservaron. No se modificaron producto, runner,
configuración del perímetro, fixtures de producción ni documentación canónica.
No se realizaron escrituras SQL deliberadas ni operaciones manuales sobre
DB/WAL/SHM; el acceso read-only pudo actualizar metadatos de `-shm`, como se
registra en §5 y §11. Este es el único informe manual añadido. `graphify-out/`
ya estaba sin trackear y fue refrescado por `graphify update .` según la
instrucción del repositorio; esos artefactos generados no son cambios de
producto ni se atribuyen al informe.

## 4. Snapshot Mechanism

**PROVEN:** `backup_read_only_database()` reutiliza la ruta SQLite ya presente
en `gate2_snapshots.py`: valida que el origen exista y difiera del destino,
abre el origen mediante URI `mode=ro`, y usa `Connection.backup()` a la base
temporal. Las conexiones se cierran en `finally`; los errores SQLite se
propagan como `Gate2SnapshotError`.

El uso compartido por las fixtures evita una segunda implementación de
snapshot. La función no ejecuta SQL de escritura sobre el origen ni crea
destinos bajo `data/` por sí misma; cada fixture entrega un destino temporal.

**NOT DEMONSTRATED:** una transacción de backup sobre una fuente que está
cambiando concurrentemente por otro proceso no se probó. El API SQLite
proporciona una copia consistente; esta tarea no certifica comportamiento
bajo escritores concurrentes.

## 5. WAL Handling

La regresión sintética creó una base temporal, habilitó WAL, dejó un WAL no
vacío con una fila confirmada, generó el snapshot y verificó:

- **PROVEN (prueba focal):** la fila confirmada del WAL está en el snapshot.
- **PROVEN (prueba focal):** el destino acepta una escritura que no aparece en
  la fuente.
- **PROVEN (prueba focal):** los bytes del archivo principal y del `-wal`
  permanecen iguales durante la operación.
- **OBSERVED:** cambió el contenido del `-shm` durante el acceso SQLite
  read-only. El archivo SHM contiene coordinación/índice compartido de WAL;
  este cambio no alteró la fila consultada ni los bytes del `.db` o `-wal`,
  pero sí impide afirmar ausencia total de escrituras físicas a sidecars.

No se hizo checkpoint, VACUUM, eliminación ni copia manual de sidecars. La
prueba no declara `-shm` byte-inmutable.

## 6. web_state_test_copy Resolution

**PROVEN (código):** la fixture requiere ambas DBs, crea un directorio de
pytest temporal y crea cada destino con `backup_read_only_database`. Ya no
rechaza una fuente solo porque su WAL no esté vacío y no copia el main file
aisladamente.

**PROVEN (prueba sintética del mecanismo compartido):** el backup maneja una
fuente sintética con WAL no vacío.

**NOT DEMONSTRATED:** no se ejecutó B06 y no se afirma que el flujo pedagógico
de B06 pase. La prueba `test_context_flood` que usa esta fixture pasó durante
la primera corrida focal, pero esa corrida también abrió fuentes persistentes;
no se considera autorización ni demostración de esterilidad.

## 7. C5 Isolation Resolution

**PROVEN (código):** el fixture `store` de
`tests/adversarial/test_c5_trust_gate.py` construye `KnowledgeStore` desde
`knowledge_store_test_copy`, no desde `data/web_state/knowledge_store.db`.
Las aserciones del test no fueron alteradas.

El test focal `test_fixture_c5_a_ood_detection` pasó en la primera corrida
focal usando el snapshot. Esa corrida abrió las fuentes persistentes en
read-only para crear el snapshot; no se tomaron hashes previos de los
sidecars de producción.

**NOT DEMONSTRATED:** integridad física de los sidecars de producción después
de esa ejecución; tampoco se demuestra que todos los caminos del perfil release
estén libres de efectos externos.

## 8. Session Isolation Verification

**PROVEN (código existente):** `AppContainer` con `working_dir` explícito
inyecta `SessionStore(working_dir / "sessions.db")`; la ruta por defecto de
`SessionStore` no se utiliza en ese camino.

**PROVEN (prueba focal):** `test_app_container_session_store_uses_working_dir_and_rehydrates`
pasó; escribe/reabre la sesión bajo `tmp_path` y comprueba que el path no es
`data/student/sessions.db`. No se accedió a la DB real.

La regresión de aislamiento de sesiones preexistente se preservó; no se añadió
otra política de almacenamiento.

## 9. Focused Test Results

No se ejecutaron `./scripts/test.sh`, el perfil release, B06 ni B10.

1. Corrida focal inicial:
   - comando: `.venv/bin/python -m pytest -q tests/unit/diagnostics/test_gate2_snapshots.py tests/session/test_app_container_session_store_isolation.py tests/unit/retrieval/test_context_flood.py tests/adversarial/test_c5_trust_gate.py::test_fixture_c5_a_ood_detection`
   - **OBSERVED:** `1 failed, 7 passed, 2 warnings`.
   - El fallo fue la aserción inicialmente más estricta que requería bytes
     idénticos también en `-shm`; el output mostró el cambio de ese sidecar en
     una fuente sintética. No se ocultó como resultado positivo.
2. Corrida focal posterior, limitada a snapshots sintéticos y sesión temporal:
   - comando: `.venv/bin/python -m pytest -q tests/unit/diagnostics/test_gate2_snapshots.py::test_read_only_backup_captures_wal_without_changing_database_or_wal tests/unit/diagnostics/test_gate2_snapshots.py::test_read_only_backup_rejects_missing_source_and_same_destination tests/session/test_app_container_session_store_isolation.py`
   - **OBSERVED:** `3 passed, 2 warnings`.
3. B06 y B10: **NOT RUN**.

La segunda corrida verde no anula la limitación del SHM observada en la primera.
Focused PASS no equivale a Quality Gate PASS.

## 10. Static Safety Checks

- **PASS:** `git diff --check`.
- **PROVEN (búsqueda estática focal):** no quedó la construcción directa
  `KnowledgeStore("data/web_state/knowledge_store.db")` en C5 ni el patrón
  `SessionStore()` dentro de los tests localizados.
- **PROVEN (inspección):** los demás tests localizados que preparaban bases
  writable desde `data/web_state` usan ahora snapshot SQLite compartido o
  `backup_read_only_database`; el test SSE de copia de corpus también delega
  ahora en el helper compartido.
- **UNKNOWN:** ausencia global de cualquier acceso protegido writable en los
  cientos de módulos del perfil. La inspección fue estática y focal sobre
  `KnowledgeStore`, `SessionStore`, conexiones/copias SQLite y los caminos
  identificados; no se hizo auditoría exhaustiva módulo por módulo ni
  instrumentación dinámica.
- **NOT DEMONSTRATED:** aislamiento de todos los efectos del proceso pytest;
  el runner no fue modificado y no se le añadió sandbox en esta tarea.

## 11. Production Integrity

- **OBSERVED:** no se ejecutaron comandos SQL ni escrituras deliberadas contra
  `data/`; destinos de snapshot y escrituras de tests fueron temporales.
- **OBSERVED:** la primera corrida focal accedió a las fuentes de conocimiento
  persistentes mediante la nueva conexión SQLite `mode=ro` para crear los
  snapshots usados por C5 y `test_context_flood`.
- **UNKNOWN:** si los archivos `-shm` de producción cambiaron durante esos
  accesos; no había una huella previa que permita resolverlo y no se inspeccionó
  ni restauró ningún recurso de producción.
- **NO se afirma:** `production paths touched = NO`, `production untouched` o
  integridad integral de DB/WAL/SHM. La vía read-only evita escrituras SQL en
  el origen, pero el comportamiento SHM observado impide certificar
  inmutabilidad física de sidecars.

HEAD antes/después: `cc8acfae623f9d10c8366871470319786b6a7ca4`.
`git status --short` antes de la tarea mostró 26 archivos tracked modificados
(`.env.example`, `PHASES.md`, `README.md`, `docs/PLAN_MAESTRO_CIERRE_TALOS.md`,
los dos `docs/ROADMAP_V1_5_*`, `kasiu-lab/ui/src/styles/tactical.css`,
`pyproject.toml`, `requirements.lock`, `src/study_engine/pedagogy/auditors/programming_auditor.py`,
`src/study_engine/retrieval/embedding.py`, `src/study_engine/retrieval/late_chunking.py`,
las cuatro rutas web modificadas y 10 tests preexistentes modificados:
`tests/pedagogy/test_chat_sse_endpoint.py`,
`tests/pedagogy/test_socratic_system_prompt.py`,
`tests/pedagogy/test_talos_vs_notebooklm_e2e.py`,
`tests/unit/retrieval/test_embedding.py`,
`tests/unit/retrieval/test_late_chunking.py`,
`tests/unit/retrieval/test_retrieval_fabric.py`,
`tests/unit/web/test_exercise_generation_leak.py`,
`tests/unit/web/test_metacognitive_endpoint.py`,
`tests/web/test_colab_sync_endpoints.py` y
`tests/web/test_student_exercises_api.py`) y 10 rutas no versionadas (`.agents/`, `.opencode/`,
`AGENTS.md`, `TALOS_OPENCODE_TOOLCHAIN_AUDIT.md`,
`docs/P1_2_5_IMPLEMENTATION_PACKAGE.md`, `docs/architecture/`,
`graphify-out/`, `src/study_engine/web/admin_auth.py`,
`tests/pedagogy/test_programming_auditor_sandbox.py` y
`tests/unit/web/test_student_exercises_admin_auth.py`). Se preservaron todos.
`tests/conftest.py` estaba limpio antes de esta tarea.

`git status --short` después conservó esas rutas y añadió los cambios de esta
directiva listados en §3, más sus cambios focales en
`tests/adversarial/session/test_unified_session_adversarial.py`,
`tests/integration/test_unified_study_session.py`,
`tests/unit/student/test_memory_extractor.py` y
`tests/web/test_chat_fastpath_conversational.py`. No hubo commits. Los únicos
cambios atribuibles a esta directiva son los listados en §3 y este informe.

## 12. Remaining Blockers

1. **Sidecar SHM:** no se ha demostrado que el mecanismo satisfaga la condición
   estricta de no cambiar ningún archivo fuente en `data/` al leer una base con
   WAL activo. El cambio sintético en SHM debe adjudicarse antes de poder
   afirmar `production untouched`.
2. **Integridad post-test:** faltan hashes/evidencia previa y posterior de
   producción para la corrida focal ya efectuada; no se deben inventar ni
   reconstruir retroactivamente.
3. **Cobertura estática total:** no se demostró `PROTECTED_WRITABLE = 0` para
   todo el perímetro effective release; queda auditoría focal/módulo por módulo
   pendiente.
4. **Release runner:** no se demostró sandbox del proceso ni contención global
   de efectos secundarios.
5. **B06:** no se ejecutó; solo se probó el helper genérico con fuente
   sintética. El test B06 permanece `BLOCKED` hasta una validación autorizada.

No se propone cleanup ni una solución adicional en esta directiva.

## 13. Release Gate Authorization Status

```text
./scripts/test.sh = NOT AUTHORIZED
P1.2 = BLOCKED
B06 = BLOCKED — ENVIRONMENT / SNAPSHOT PRECONDITION
B10 = NOT RUN
```

El runner no debe ejecutarse hasta adjudicar explícitamente el efecto de SHM,
obtener una estrategia aceptable que preserve la frontera protegida, completar
la revisión estática del perímetro y satisfacer las demás precondiciones del
gate. Este informe no autoriza ninguna ejecución posterior.

## 14. P1.2 Status

```text
P1.2 = BLOCKED
P1.3 = NOT STARTED
```

### Evidencia mínima

```text
HEAD before = cc8acfae623f9d10c8366871470319786b6a7ca4
HEAD after  = cc8acfae623f9d10c8366871470319786b6a7ca4
git diff --check = PASS
focused tests = 3 passed on synthetic/temp-only rerun
initial focused run = 1 failed, 7 passed (SHM byte-change observed)
B06 = NOT RUN
B10 = NOT RUN
production paths opened read-only for snapshot = YES
production data integrity after that access = UNKNOWN
```
