# TALOS-P1.2-STEP-08 — STATIC REVIEW

## 1. Estado del repositorio y diff

- Rama observada: `talos-current-audit`.
- Estado del worktree: sucio y con cambios preexistentes conservados; no se realizó limpieza, staging ni commit.
- Estado del gate: `P1.2 = BLOCKED-REGRESSION` conforme al expediente de STEP-06.
- Se revisó el diff actual de las modificaciones relacionadas con STEP-07:
  - `src/study_engine/storage/sqlite_engine.py`
  - `scripts/quality_gate.py`
  - `tests/pedagogy/test_chat_sse_endpoint.py`
  - `docs/TALOS-P1.2-STEP-07-MINIMAL-FIXES.md`

### Diff relevante

- `sqlite_engine.py`: añadido helper privado `_normalize_sqlite_db_path()` y uso en `SQLiteStorageEngine.__init__`.
- `quality_gate.py`: ajustado `TALOS_TEST_BASETEMP` para apuntar a un directorio derivado bajo `execution_root / "pytest-tmp"`.
- `test_chat_sse_endpoint.py`: añadido `import sqlite3` para corregir el `NameError`.
- `docs/TALOS-P1.2-STEP-07-MINIMAL-FIXES.md`: expediente documental de la fase de corrección mínima.

No se ejecutó ni `pytest`, ni `scripts/test.sh`, ni `scripts/quality_gate.py`, ni `scripts/prepare_test_snapshot.py` durante STEP-08.

## 2. Revisión estática de la normalización SQLite

### 2.1. Ejemplo de semántica observada

El cambio en `src/study_engine/storage/sqlite_engine.py` introduce:

- control exhaustivo de `:memory:`
- normalización de valores tipo `sqlite:///...` y `file://...`
- conversión de URI a `Path` real antes de `mkdir` y conexión

### 2.2. Clasificación por formato

1. `:memory:`
   - Estado: `SUPPORTED_BY_CONTRACT`
   - Evidencia: el helper devuelve `":memory:"` para `":memory:"`, `file::memory:`, `file::memory:?cache=shared` y evita cualquier manipulación de filesystem.
   - Evaluación: mantiene la semántica esperada de SQLite en memoria sin tocar disco ni crear rutas.

2. Rutas de filesystem ordinarias
   - Estado: `SUPPORTED_BY_CONTRACT`
   - Evidencia: si el valor no es URI ni `:memory:`, el código devuelve `Path(value)` y la lógica de `__init__` crea el directorio padre solo si no es memoria.
   - Evaluación: la semántica normal no cambia para rutas existentes y legibles por el sistema.

3. `sqlite:///...` y `sqlite:////...`
   - Estado: `NEW_BEHAVIOR_REQUIRES_JUSTIFICATION`
   - Evidencia: se acepta `sqlite://` y se lee `urlparse(value).path`; luego se convierte a `Path` mediante `url2pathname(unquote(...))`.
   - Evaluación: hay evidencia de que la suite usa convenciones de URI SQLite en tests (`tests/unit/retrieval/test_query_rewriter.py`), pero la API pública de `SQLiteStorageEngine` no documenta explícitamente esta aceptación como contrato canónico. El comportamiento es útil y consistente, pero no queda totalmente respaldado por un contrato público único.

4. `file://...`
   - Estado: `NEW_BEHAVIOR_REQUIRES_JUSTIFICATION`
   - Evidencia: el helper acepta `file:` y transforma la ruta antes de usarla.
   - Evaluación: esto es compatible con la forma en que la capa SQLite de la repo abre bases con uri=True (`file:{...}?mode=ro`), pero sigue requiriendo justificación explícita como política de soporte, no como suposición implícita.

5. URI inválidas o ambiguas
   - Estado: `UNRESOLVED`
   - Evidencia: la función no produce una excepción explícita ni un rechazo informado para inputs `sqlite://...` sintácticamente inválidos. Simplemente los normaliza y los convierte en un path.
   - Evaluación: el caso de entrada vacío o parametrización imposible queda cubierto parcialmente, pero no hay un manejo explícito de “URI inválida” comparable a un contrato de error determinista.

### 2.3. Invariantes de seguridad estáticas revisadas

- `:memory:` mantiene la semántica esperada: sí.
- Rutas de filesystem normales siguen resolviéndose correctamente: sí, según el código.
- `sqlite:///...` y `sqlite:////...` están normalizados con regla explícita: sí, pero no tiene contrato canónico completo.
- `file://...` es compatible con la forma de conexión actual: sí, según usos en la repo.
- Los parámetros de URI no se convierten accidentalmente en nombre de archivo: en la práctica, el `Path` final se deriva de la parte de ruta, no de query string ni de esquema.
- No se crean directorios a partir de literales `sqlite:` o `file:`: la creación de directorio solo ocurre sobre `Path(normalized)`, donde `normalized` ya es un path real de sistema de archivos.
- No se introduce acceso a bases protegidas como fallback: no hay fallback a `data/web_state` ni a `data/student` en el helper.
- Las URI inválidas no se convierten en paths arbitrarios silenciosos: no se realiza una validación explícita; por eso queda `UNRESOLVED`.

### 2.4. Conclusión de la revisión SQLite

La corrección es razonable y mínima, pero la aceptación de `sqlite://` / `file://` requiere una decisión explícita de contrato. No es un defecto crítico en sí, pero sí un punto de decisión pendiente para la siguiente fase de validación autorizada.

## 3. Revisión del import de `sqlite3`

Archivo revisado: `tests/pedagogy/test_chat_sse_endpoint.py`

- Estado: `IMPLEMENTED_UNVALIDATED`
- Evidencia:
  - En la cabeza del módulo el cambio añade `import sqlite3`.
  - La llamada `sqlite3.connect(copied_db)` ya no falla por `NameError` en el alcance del módulo.
- Evaluación:
  - El cambio es válido y no duplica importaciones existentes.
  - No altera el resto del test ni introduce nuevas dependencias.
  - La corrección es apropiada para la causa raíz adjudicada en STEP-06, pero sigue sin validación dinámica.

## 4. Matriz de los cinco grupos causales

| Grupo | Estado | Evidencia / archivos | Observación |
|---|---|---|---|
| A. sandbox, workspace y raíces temporales | `PARTIAL` | `scripts/quality_gate.py` ajustó `TALOS_TEST_BASETEMP` a `execution_root / "pytest-tmp"`; no hay evidencia de revalidación del aislamiento ni del contrato de `_validate_mount_roots()` | Se corrige una parte del problema de raíz, pero la corrección no está validada ni cerrada con evidencia dinámica |
| B. escritura adversarial en checkout, acceso a `.git` y preparación del benchmark | `NOT_IMPLEMENTED` | No hubo cambios en tests adversariales ni en benchmark/harness que toquen checkout protegido ni `.git` | El grupo causal sigue vigente; no se relajó el perímetro ni se habilitó acceso |
| C. import de `sqlite3` | `IMPLEMENTED_UNVALIDATED` | `tests/pedagogy/test_chat_sse_endpoint.py` | El `NameError` quedó corregido estáticamente; falta validación ejecutada |
| D. contrato y normalización de URI SQLite | `PARTIAL` | `src/study_engine/storage/sqlite_engine.py` | Hay soporte nuevo y útil, pero requiere decisión explícita sobre alcance del contrato de URI SQLite |
| E. emisión del evento JSON del retrieval fabric | `NOT_IMPLEMENTED` | No hubo cambio en `src/study_engine/retrieval/fabric.py` ni en `tests/unit/retrieval/test_retrieval_fabric.py` | El problema de trazabilidad permanece sin corrección aplicada |

## 5. Invariantes de seguridad revisadas

Se verificó estáticamente que las modificaciones no:

- habilitan escritura sobre el checkout protegido;
- exponen `.git` ni bases originales dentro del worker;
- relajan `_validate_mount_roots()` ni el comportamiento fail-closed;
- añaden fallbacks silenciosos a bases de producción;
- debilitan assertions o convierten fallos en `skip`/`xfail`;
- modifican el contrato de captura B06 ni la policy `quiesced`;
- alteran BKT, SM-2 ni la lógica pedagógica.

## 6. Dudas y pendientes

1. Requiere justificación explícita si la API pública debe aceptar `sqlite://` y `file://` en `SQLiteStorageEngine`.
2. Requiere validación de integración para confirmar que el `TALOS_TEST_BASETEMP` nuevo sigue respetando el contrato del guest workspace y del checkout protegido.
3. Requiere validación dinámica del `RetrievalFabricLite` para comprobar el evento JSON y la trazabilidad.
4. El grupo B sigue sin corrección; las pruebas adversariales y del benchmark que apuntan a checkout protegido, `.git` y acceso a producción deben permanecer bloqueadas hasta revisión humana.

## 7. Cambios pendientes exactos

- Definir si `sqlite://` es soporte público o solo una compatibilidad de test.
- Determinar si `file://` debe ser soportado para toda la API o solo para conectores de lectura.
- Añadir validación explícita de URI inválidas y su tratamiento determinista.
- Corregir y validar el grupo A con un test de aislamiento específico usando la policy y el runner canónicos.
- Corregir y validar el grupo E en `RetrievalFabricLite` y en `tests/unit/retrieval/test_retrieval_fabric.py`.
- Revalidar con pruebas focalizadas después de autorización explícita, sin reabrir el gate completo aún.

## 8. Nodeids previstos para regresión autorizada

Se recomienda revisar en la siguiente fase, si se autoriza la regresión:

- `tests/unit/diagnostics/test_quality_gate_isolation.py::test_bubblewrap_denies_protected_paths_and_allows_derived_workspace`
- `tests/unit/retrieval/test_query_rewriter.py::test_knowledge_store_search_hybrid_receives_prerewritten_query`
- `tests/unit/retrieval/test_query_rewriter.py::test_retrieval_service_is_authoritative_rewriter_chokepoint`
- `tests/pedagogy/test_chat_sse_endpoint.py::test_fadena_std_real_corpus_isolation_on_temporary_database_copy`
- `tests/unit/retrieval/test_retrieval_fabric.py::test_fabric_trace_logger_rotation_and_json_event_f5`

## 9. Estado de salida

`STATIC_REVIEW_COMPLETE`

P1.2 permanece `BLOCKED-REGRESSION`.

La revisión estática demuestra que el diff puede ser inspeccionado con evidencia suficiente, pero que no puede asumirse corrección dinámica ni cierre del gate sin ejecutar la siguiente fase de regresión autorizada.
