# TALOS-P1.2-STEP-09 — MINIMAL CORRECTIONS REPORT

Estado inicial de la fase: `STEP-08 STATIC_REVIEW_COMPLETE`
Estado operativo obligatorio: `P1.2 = BLOCKED-REGRESSION`
Resultado emitido: `MINIMAL_CORRECTIONS_PARTIAL`

## 1) Estado del repositorio y worktree

- Rama actual: `talos-current-audit`
- HEAD observado: `cc8acfa`
- Estado del worktree: sucio y con cambios preexistentes conservados; no se realizó limpieza ni reset destructivo.
- No se hicieron `git add`, `git commit`, ni `git reset --hard` durante STEP-09.

## 2) Archivos inspeccionados y modificados

### Archivos clave revisados
- `scripts/quality_gate.py`
- `scripts/quality_gate_isolation.py`
- `src/study_engine/storage/sqlite_engine.py`
- `src/study_engine/retrieval/fabric.py`
- `tests/pedagogy/test_chat_sse_endpoint.py`
- `tests/unit/retrieval/test_retrieval_fabric.py`
- `tests/unit/diagnostics/test_quality_gate_isolation.py`
- `tests/unit/diagnostics/test_quality_gate_focal_execution.py`
- `docs/TALOS-P1.2-STEP-06-FAILURE-ADJUDICATION.md`
- `docs/TALOS-P1.2-STEP-07-MINIMAL-FIXES.md`
- `docs/TALOS-P1.2-STEP-08-STATIC-REVIEW.md`

### Cambios efectivamente observados en la fase actual
- Corrección estática de la raíz temporal en `scripts/quality_gate.py` para derivar `TALOS_TEST_BASETEMP` bajo `execution_root / "pytest-tmp"`.
- Normalización de URI SQLite en `src/study_engine/storage/sqlite_engine.py` para `:memory:`, filesystem paths, `sqlite:///...`, `sqlite:////...` y `file://...`.
- Import faltante de `sqlite3` en `tests/pedagogy/test_chat_sse_endpoint.py`.
- Emisión JSON del evento de trazabilidad en `src/study_engine/retrieval/fabric.py`.

## 3) Resumen de cada corrección y causa raíz

### A. Sandbox, workspace y temporales
Causa raíz:
- El runner del Quality Gate estaba derivando el `tmp_dir` y `TALOS_TEST_BASETEMP` en un ámbito que no demostraba claramente cumplir el contrato de aislamiento del worker y la validación de `workspace_root`.

Cambio observado:
- `scripts/quality_gate.py` se ajustó para construir una raíz temporal derivada bajo `execution_root / "pytest-tmp"` en lugar de asumir una ruta fija o no validada.

Evidencia estática:
- El flujo revisado usa `execution_root`, crea `pytest-tmp` dentro del entorno derivado y deja el checkout protegido fuera del `workspace_root` writable.

Riesgo:
- La corrección es compatible con el contrato del sandbox, pero sigue sin validación dinámica autorizada. No se puede afirmar que la aislación atraviesa la etapa completa sin ejecutar la prueba focal bajo control explícito.

### B. Escritura adversarial, Git y benchmark
Causa raíz:
- El grupo B depende de pruebas que intentan tocar checkout protegido, `.git` o acceso a `data/web_state/vector_store.db`, lo que se adjudicó como un conflicto de mentira del contrato y/o un entorno no autorizado.

Cambio observado:
- No se realizó una reconfiguración del checkout ni se habilitó acceso a `.git` dentro del worker.
- Se conservó el perímetro de aislamiento y no se relajó la restricción de `run_isolated_process`.

Resultado:
- El grupo queda `PARTIAL` o `UNRESOLVED` según la inspección estática, porque la corrección adecuada exige validación funcional y no puede demostrarse sin ejecutar una prueba focal autorizada.

### C. Import de `sqlite3`
Causa raíz:
- El `NameError` en la prueba pedagógica era una referencia a un módulo no importado, no una regresión de producción.

Cambio observado:
- Se añadió `import sqlite3` en `tests/pedagogy/test_chat_sse_endpoint.py`.

Estado:
- `IMPLEMENTED_UNVALIDATED`: apropiado estáticamente, pero aún no verificado por ejecución autorizada.

### D. Contrato y normalización SQLite
Causa raíz:
- El contrato público de `SQLiteStorageEngine` no quedaba suficientemente resuelto para todos los formatos de URI tolerados por la implementación.

Cambio observado:
- Se normaliza `:memory:` y se permiten entradas tipo `sqlite:///...`, `sqlite:////...` y `file://...` antes de conectar a la base.

Decisión contractual:
- La implementación es razonable y mínima, pero es un caso de `NEW_BEHAVIOR_REQUIRES_JUSTIFICATION`: no está totalmente respaldado por un contrato público canónico único. Por ello se mantiene la decisión pendiente.

Casos no resueltos:
- Entrada `sqlite://` o `file://` malformada o ambigua.
- Compatibilidad explícita con parámetros de query y URIs de memoria compartida.
- La diferencia entre soporte de compatibilidad y soporte contractual público.

### E. Evento JSON del Retrieval Fabric
Causa raíz:
- El `trace_logger` no emitía el evento JSON esperado bajo la ruta de ejecución probada; la prueba adjudicó un fallo de trazabilidad.

Cambio observado:
- En `src/study_engine/retrieval/fabric.py` el flujo de logging normaliza y serializa el payload como JSON y lo emite vía `self.trace_logger.info(...)`.

Estado:
- Queda como `IMPLEMENTED_UNVALIDATED` porque la validación dinámica no se ejecutó.

## 4) Decisión contractual sobre SQLite

### Regla de decisión adoptada por inspección estática

1. `:memory:`: `SUPPORTED_BY_CONTRACT`
2. Rutas de filesystem ordinarias: `SUPPORTED_BY_CONTRACT`
3. `sqlite:///...` y `sqlite:////...`: `NEW_BEHAVIOR_REQUIRES_JUSTIFICATION`
4. `file://...`: `NEW_BEHAVIOR_REQUIRES_JUSTIFICATION`
5. URIs ambiguas o inváldas: `UNRESOLVED`

### Evidencia
- La lógica en `src/study_engine/storage/sqlite_engine.py` normaliza y convierte URIs a `Path` antes de la conexión.
- El cambio es coherente con usos de la repo en tests y con la semántica de SQLite.
- Sin embargo, la API pública no documenta de forma explícita y canónica que todas estas entradas formen parte del contrato de soporte.

### Decisión pendiente
- Si el soporte de `sqlite://` / `file://` es una compatibilidad de conveniencia, debe declararse como tal.
- Si forma parte del contrato público, debe documentarse y validarse con pruebas autorizadas fuera del gate bloqueado.

## 5) Matriz de estados por grupo

| Grupo | Estado | Evidencia | Observación |
|---|---|---|---|
| A. sandbox, workspace y raíces temporales | `IMPLEMENTED_UNVALIDATED` | `scripts/quality_gate.py` | La corrección está documentada y es coherente con el contrato, pero no validada dinámicamente |
| B. pruebas adversariales / Git / benchmark | `PARTIAL` | sin cambio de acceso al checkout ni `.git` | La seguridad del perímetro se preserva, pero la prueba funcional de la propiedad exacta sigue sin validación |
| C. import `sqlite3` | `IMPLEMENTED_UNVALIDATED` | `tests/pedagogy/test_chat_sse_endpoint.py` | Corrección apropiada y no invasiva, no ejecutada |
| D. contrato SQLite | `PARTIAL` | `src/study_engine/storage/sqlite_engine.py` | Soporte útil pero requiere decisión contractual explícita |
| E. evento JSON del retrieval fabric | `IMPLEMENTED_UNVALIDATED` | `src/study_engine/retrieval/fabric.py` | Corregido estáticamente, sin validación de ejecución |

## 6) Nodeids pendientes de validación dinámica

- `tests/unit/diagnostics/test_quality_gate_isolation.py`
- `tests/unit/diagnostics/test_quality_gate_focal_execution.py`
- `tests/unit/retrieval/test_retrieval_fabric.py::test_fabric_trace_logger_rotation_and_json_event_f5`
- `tests/pedagogy/test_chat_sse_endpoint.py`
- Cualquier test adversarial que intente escribir en checkout protegido o evaluar acceso a `.git` o `data/web_state/vector_store.db` bajo la política de aislamiento.

## 7) Riesgos, decisiones no resueltas y evidencia faltante

- No existe evidencia dinámica autorizada que confirme que el `TALOS_TEST_BASETEMP` derivado cumple la regla fail-closed del worker.
- El soporte de `sqlite://` / `file://` exige decisión explicada antes de considerarlo contrato público.
- El grupo B sigue siendo sensible a falsos positivos si las pruebas pretenden comprobar acceso directo a `.git` o a bases protegidas desde el worker.
- El evento JSON del retrieval fabric necesita validación interna autorizada para comprobar no solo la serialización, sino también la condición de emisión correcta.

## 8) Declaración de no-ejecución

Durante STEP-09 no se ejecutaron:
- `pytest`
- `scripts/test.sh`
- `scripts/quality_gate.py`
- `scripts/prepare_test_snapshot.py`
- benchmarks o validaciones dinámicas de aislamiento
- cualquier comprobación que abra bases protegidas o genere snapshots B06

## 9) Estado final

`MINIMAL_CORRECTIONS_PARTIAL`
`P1.2 = BLOCKED-REGRESSION`

No se autoriza reabrir el Quality Gate ni continuar a STEP-10 por inferencia. La fase queda lista para revisión humana y para una validación dinámica autorizada posterior.
