# TALOS V1.5 — F-12 recuperación de evidencia B10 y reconciliación de bloqueos

**Fecha/hora de inicio:** 2026-10-10 12:42:15 -03:00
**Alcance:** investigación documental y forense, solo lectura, más este informe nuevo.
**Repositorio esperado:** `/media/agustin/Laboratorio/study-engie`
**Gate de release:** `NOT_AUTHORIZED`

## 1. Dictamen ejecutivo

La evidencia primaria original de las siete pruebas focalizadas B10 **no pudo
recuperarse completamente**. Se recuperaron declaraciones firmadas por hash en
el informe F-09 y registros de la sesión del agente que muestran prefijos de
comandos pytest; la captura de sesión disponible trunca las entradas de
herramienta a 200 caracteres y no contiene stdout/stderr, códigos de salida,
lista íntegra de nodeids ni recibo B10.

```text
B10_PRIMARY_EVIDENCE = PARTIALLY_RECOVERED
B10 = PARTIALLY_VERIFIED
B06 = FOCAL_EXECUTION_VALIDATED       (preservado desde F-11)
P1.2 = NOT_CLOSED                     (plan: FAIL / DIAGNOSTIC;
                                      expedientes STEP-22/STEP-05: BLOCKED-REGRESSION)
RELEASE_GATE = NOT_AUTHORIZED
RELEASE_VERDICT = NOT_ISSUED
```

La evidencia estática disponible sustenta que la clasificación `INFORMATIVE`
se limita al nodeid B10 y que la excepción del runner es estrecha y fail-closed.
No transforma el reporte de “7 passed” en evidencia primaria ni demuestra la
ejecución exacta de F-09. La F-10 focal B06 no es evidencia de B10 ni una
re-evaluación del gate global.

## 2. Identidad y preservación

Preflight F-12, antes de crear este archivo:

| Propiedad | Observado |
|---|---|
| Rama | `talos-current-audit` |
| HEAD | `032339436639d33d310c437c88fe01d94e977449` |
| Staged | 0 |
| Tracked modificados | 22 |
| Untracked | 179 |
| Otros estados | 0 |
| Líneas de `git status --porcelain=v1 -uall` | 201 |
| SHA-256 de la salida completa | `52318278133ed55b4e8c1cd5910ec0e555bdb568418f4cf2d18d2c028df3357f` |
| SHA-256 de inventario `git for-each-ref` | `9bd163f687174462441c957fb585be9eab24d93a052444f0c71811793f087beb` |

La comparación agregada con la línea base F-10/F-11 es: HEAD, rama y 22
tracked modificados permanecen iguales; hay una línea y un untracked más que
la base previa a F-11. El informe F-11, creado después de esa base, explica
esa diferencia. No se conserva en los informes previos el listado completo
de la base antigua para un diff exacto de cada ruta; por tanto, esta
reconciliación es de identidad y conteos, no una atribución de los demás
cambios. No había cambios staged.

Se confirmó que el destino
`docs/F-12-RECUPERACION-EVIDENCIA-B10-Y-RECONCILIACION-DE-BLOQUEOS.md` no
existía. No se cambió de rama, HEAD, refs ni checkout de V1.0-elite; no se
descartó, movió ni reordenó trabajo preexistente.

## 3. Búsqueda autorizada de evidencia primaria

La búsqueda se limitó a:

1. El inventario y contenido textual del directorio
   `/media/agustin/Almacenamiento/Facultad/TALOS/historical-evidence/F07-F12/talos-f09-authorization-gUVYAnpn/`, incluidos
   sus informes, índice SHA-256, manifiestos, bindings y registros B06.
2. Los registros de herramienta de la sesión del agente vinculada a esta
   ejecución F-09: sesión
   `agent-host-session://copilotcli/75b6a644-6e2b-49c9-99ac-5589b74e31f8`,
   turno 136.
3. Los informes F-10/F-11 e índice de hashes ya identificados.

En el directorio F-09 se buscaron referencias a pytest, nodeids, comandos,
stdout, exit codes, transcripts, runner y collection; se revisó además el
inventario de archivos. El directorio contiene dos informes F-09, el índice,
manifiestos, bindings, registros/validaciones y snapshots B06. No contiene un
log de pytest B10, recibo B10, lista íntegra de nodeids, archivo de comando ni
stdout/stderr B10. Los manifests/bindings y payload B06 no sustituyen esos
artefactos de ejecución.

En el historial de sesión aparecen tres intentos/comandos pytest del turno
136: una invocación `python -m pytest` y dos invocaciones
`.venv/bin/python -m pytest` dirigidas a `tests/ci/test_quality_gate_perimeter.py`.
Los registros disponibles cortan cada argumento de herramienta a 200
caracteres. En ellos se ven el prefijo del selector de descubrimiento del
perímetro y el comienzo del selector
`test_informative_test_failure_is_reported_but_does_not_block`; no se pueden
recuperar los selectores restantes ni determinar a partir del log la lista
completa final de siete nodeids. El historial contiene una respuesta posterior
del agente que afirma que las pruebas pasaron, pero no contiene la salida
primaria de esas invocaciones. La exportación consultada no aporta hash,
stdout/stderr, exit code ni recibo que vincule los resultados con el candidato.

### Inventario probatorio B10

| Artefacto/fuente | Función probatoria | Integridad comprobada | Limitación |
|---|---|---|---|
| F-09 `F-09-RESULTS.md` | Declara siete pruebas focalizadas aprobadas (`7 passed in 0.19s`) y resume el contrato B10. | SHA-256 `112009f620cae3927f4b63ca7524503bb19316735a52fb431d8b40980896e80f`; coincide con la entrada vista en el índice F-09. | Informe de resultados, no transcript primario: no enumera los siete nodeids, comando completo, cwd/config, salida individual ni códigos crudos. |
| F-09 `F-09-DECISION-RECORD.md` | Identifica decisión, nodeid autorizado y alcance de cambios B10. | SHA-256 `b86e82589a08d74a95fc6d371ed5d35248717b265805abfe079f8a585983b819`; coincide con la entrada vista en el índice F-09. | Es registro de decisión, no evidencia de ejecución. |
| F-09 `SHA256SUMS.txt` | Índice existente de artefactos F-09. | No se regeneró ni modificó; sus entradas para ambos informes coinciden con los SHA-256 calculados durante F-12. | El índice no enumera log/recibo de ejecución B10; sus hashes de snapshot B06 no demuestran la ejecución B10. |
| Registros de herramienta de sesión, turno 136 | Acreditan que el agente registró invocaciones pytest dirigidas al archivo de regresiones B10. | Leídos desde el historial de sesión asociado; no se ofrece hash verificable para una captura íntegra del registro. | Entradas truncadas a 200 caracteres; no incluyen resultado crudo, exit code, entorno completo ni lista final completa de nodeids. |
| F-10 `worker.stdout.log` y `focal-execution-receipt.json` | Evidencia primaria de la ejecución focal B06 que F-11 adjudicó. | Los SHA-256 concuerdan con el índice F-10 y los registrados por F-11. | Corresponden al nodeid pedagógico B06, no a la ejecución B10. No reparan la ausencia de evidencia primaria F-09 B10. |
| F-11 adjudicación | Conserva la limitación ya señalada: los siete resultados se reportaron, pero faltaba transcript primario. | SHA-256 `a1b001a2aba79b5c9bf704138aa5abad03704efc54e4bec49484704365ee8507`. | Es adjudicación documental previa; no genera una fuente primaria nueva. |

**Clasificación de recuperación:**

```text
RECOVERY_STATUS = PARTIALLY_RECOVERED
```

Hay evidencia útil de decisión, contenido implementado y prefijos de
invocaciones, pero no los artefactos primarios necesarios para reconstruir
íntegramente la ejecución F-09. Esto no demuestra que las pruebas fallaran ni
que sus artefactos no existan en ningún otro lugar; la conclusión se limita a
las ubicaciones autorizadas examinadas.

## 4. Reconciliación técnica B10

El nodeid aprobado es
`tests/performance/test_latency_disaggregated.py::test_sqlite_query_latency_p95_under_50ms`.

| Criterio | Evidencia estática revisada | Adjudicación |
|---|---|---|
| Clasificación exacta | [`test_perimeter.json`](../config/test_perimeter.json#L152) contiene una única entrada `informative_tests` para el nodeid completo; la suite `tests/performance` no queda reclasificada. | Corroborado en el contenido actual. |
| Umbral y cálculo | [`test_latency_disaggregated.py`](../tests/performance/test_latency_disaggregated.py#L243) mantiene el benchmark local; calcula p95 con `np.percentile(latencies, 95)` y exige `<50.0` en las líneas 258–259. El archivo no presenta diff respecto del HEAD actual. | La semántica actual conserva `<50 ms`; F-09 también declara que no modificó el test. No hubo ejecución en F-12. |
| Elegibilidad del fallo informativo | [`quality_gate.py`](../scripts/quality_gate.py#L790) reconoce `AssertionError`; en la fase `call` y para el nodeid registrado, [`SuiteResults`](../scripts/quality_gate.py#L850) clasifica el resultado como `informative_failed`. | La excepción visible en código se limita al test exacto, fase `call` y clase de fallo admitida. |
| Bloqueo de otras condiciones | La misma clase contabiliza fallos fuera de `call` como fallos no-call; skips, errores de colección y otros nodeids quedan fuera del conjunto exclusivo de fallos informativos. `gate_result` requiere fallos informativos aislados y exit code pytest `1` para devolver `PASS_WITH_INFORMATIVE_FAILURES` ([`quality_gate.py`](../scripts/quality_gate.py#L961), [`quality_gate.py`](../scripts/quality_gate.py#L987)). | Semántica fail-closed sustentada por el flujo estático; no es evidencia de ejecución de F-09. |
| Resultado crudo y visibilidad | Los payloads incluyen `pytest_exit_code` y separan `gate_exit_code` ([`quality_gate.py`](../scripts/quality_gate.py#L1017)); el reporte imprime el fallo informativo sin ocultarlo ([`quality_gate.py`](../scripts/quality_gate.py#L1376)). | Sustentado por el código/documentación actual; no demuestra el contenido de un reporte F-09 no preservado. |
| Regresiones sintéticas | [`test_quality_gate_perimeter.py`](../tests/ci/test_quality_gate_perimeter.py#L173) comprueba fallo informativo visible/no bloqueante; [L228](../tests/ci/test_quality_gate_perimeter.py#L228) fallo de test obligatorio; [L266](../tests/ci/test_quality_gate_perimeter.py#L266) fallo de setup; [L320](../tests/ci/test_quality_gate_perimeter.py#L320) excepción de runtime. | Los casos están implementados; su ejecución F-09 solo está documentada en el informe sin output primario completo. |
| Contrato documental | [`TEST_CERTIFICATION_PERIMETER.md`](../docs/TEST_CERTIFICATION_PERIMETER.md#L24) limita la excepción, conserva el código pytest y distingue el estado del gate; [L114](../docs/TEST_CERTIFICATION_PERIMETER.md#L114) identifica la métrica local. | Coherente con el código revisado. |

Se compararon bytes actuales contra
`effective-execution-manifest-v2.json` de F-09: los hashes de
`config/test_perimeter.json` (`704a0672e541acf6a001c9fb982a2ef06500988bc6420e8a9c4d7a4da3469c69`)
y `scripts/quality_gate.py`
(`055508ff684a2c10bfb22eb6c9d00c32ded7538a46d8e2a4c6ba9402799caa3d`)
coinciden con las entradas del manifiesto. Las entradas de
`tests/ci/test_quality_gate_perimeter.py`,
`docs/TEST_CERTIFICATION_PERIMETER.md` y
`tests/performance/test_latency_disaggregated.py` no están presentes en ese
manifiesto; por tanto, dicho manifiesto no da una identidad de bytes F-09
para esos tres archivos. Sus contenidos se revisaron estáticamente en el
checkout actual.

Adjudicación:

```text
B10 = PARTIALLY_VERIFIED
```

La semántica de clasificación y bloqueo estática queda corroborada en las
fuentes vigentes. La ejecución focal de F-09 continúa sin corroboración
primaria íntegra. No se eleva a `VERIFIED` ni se re-ejecuta para sustituir la
evidencia histórica faltante.

## 5. Reconciliación de bloqueos

Los estados siguientes conservan sus scopes documentados. “Pendiente de
verificación” no significa fallo; “no autorizado” no significa satisfecho.

| Área | Fuente/estado registrado | Adjudicación F-12 y clase |
|---|---|---|
| B06 | [F-11 §4](./F-11-POST-WORKER-B06-ADJUDICATION.md#L127) adjudica `FOCAL_EXECUTION_VALIDATED`. La atestación conserva `local_integrity_only`. | **Preservar.** Solo ejecución focal B06; no certificación integral. La procedencia no demuestra autenticación independiente ni atomicidad del filesystem. |
| B10 | F-09 reporta siete pruebas; F-11 deja la falta de salida primaria. | **`PARTIALLY_VERIFIED`.** No hay evidencia nueva que cambie esa limitación. |
| P1.2 | El [`plan maestro`](./PLAN_MAESTRO_CIERRE_TALOS.md#L94) lo registra `FAIL / DIAGNOSTIC`; su registro de ejecución reporta un test fallido ([líneas 100–112](./PLAN_MAESTRO_CIERRE_TALOS.md#L100)). [`STEP-22`](./STEP-22-DECISIONS-AND-BLOCKERS.md#L4) conserva `BLOCKED-REGRESSION`. | **Bloqueo demostrado / gate no cerrado.** Los registros difieren en etiqueta y contexto de ejecución, pero ambos impiden declarar P1.2 aprobado. F-12 no ejecutó un gate ni efectuó una transición de estado. |
| STEP-05 histórico | [`TALOS-P1.2-STEP-05-B06-EXECUTION.md`](./TALOS-P1_2-STEP-05-B06-EXECUTION.md#L1) reporta el gate en otro expediente/checkout, HEAD `cc8acfae623f9d10c8366871470319786b6a7ca4`, con 15 fallos, 3132 pases y 190 warnings. | **Antecedente histórico, no resultado del código actual.** No se afirma que esos 15 fallos describan el HEAD actual ni se usa como corrida nueva. |
| `PRODUCT COMPLETE` | El plan maestro pide definir un scope verificable de producto terminado ([líneas 888–891](./PLAN_MAESTRO_CIERRE_TALOS.md#L888)). | **Pendiente de decisión/verificación.** Falta scope de aceptación y evidencia de los flujos que ese scope prometa; no equivale a un fallo técnico específico demostrado por F-12. |
| Scope de release | El plan maestro condiciona la aceptación a claims y fronteras funcionales del release. | **Pendiente.** No hay adjudicación de elegibilidad global; F-10 fue solo un worker focal B06. |
| Gate B, F5/Gate C, F6/Gate D | El plan maestro identifica su aceptación para las claims incluidas en el release como trabajo restante ([líneas 889–891](./PLAN_MAESTRO_CIERRE_TALOS.md#L889)). | **Pendiente de aceptación/evidencia** en el scope que se decida; F-12 no los ejecutó ni los declara fallidos. |
| B2–B6 y regresión PRE→POST | El plan maestro pide integración controlada y regresión de snapshot limpia (línea 891 y líneas 936–941). | **Pendiente de verificación integrada.** No se presume satisfecha por B06 focal. |
| A-PRE-0 | El plan maestro registra autoridad de baseline y cierre formal sin resolver: CP072 `NOT_RESOLVED`; `f058…` no recuperado (línea 897). | **Bloqueado para assurance formal.** No se adjudicó ni resolvió en F-12. |
| A-PRE-1 | El plan maestro conserva `NOT_AUTHORIZED / NOT_EXECUTED` y precondiciones técnicas pendientes (línea 899). | **No autorizado y no ejecutado.** No autorizarlo ni ejecutarlo durante F-12. |
| PED-F7 / BENCH-G2 | El plan maestro los condiciona a claims de calidad multi-currículo o ranking comparativo. | **Condicionales al scope**, no requisitos universales inventados por F-12. |
| Deprecations FastAPI | [F-11 §3](./F-11-POST-WORKER-B06-ADJUDICATION.md#L88) documenta cuatro `DeprecationWarning` de `FastAPI.on_event`. | **Deuda informativa observada**, no fallo B06 ni reparación hecha; no consta corregida. |
| Gate de release | F-09–F-11 y la directiva F-12 mantienen `NOT_AUTHORIZED`. | **No autorizado; no ejecutado.** No hay veredicto de release. |

No se reabrieron B01–B05 ni B07–B09. No se transformaron resultados históricos
de otras fases en evidencia de estado actual.

## 6. Evidencia, evaluación, incertidumbre y decisión

**Evidencia observada**

- F-09 reporta siete pruebas focalizadas pasadas; los SHA-256 de sus informes
  coinciden con el índice que se conserva.
- El historial relacionado registra comandos pytest, pero con argumentos
  truncados y sin resultado primario.
- Los bytes actuales de `config/test_perimeter.json` y `scripts/quality_gate.py`
  coinciden con sus entradas del manifiesto efectivo F-09.
- El código y contrato actuales preservan el fallo informativo como fallo
  visible y restringen el no-bloqueo al `AssertionError` de fase `call` del
  nodeid exacto.

**Inferencias limitadas**

- Los registros de sesión son evidencia de que se invocaron comandos con ese
  prefijo; no permiten inferir que terminaron correctamente ni que se
  recolectaron exactamente siete pruebas.
- La consistencia estática entre código/perímetro y el informe respalda la
  implementación descrita, pero no demuestra el resultado observado de una
  ejecución concreta.
- No encontrar recibo B10 en las ubicaciones autorizadas examinadas no prueba
  su inexistencia en todo el sistema.

**Incertidumbres que permanecen**

- Lista completa de siete nodeids, comando final completo, cwd/configuración de
  pytest, salida, código de salida y vínculo autenticado a una ejecución F-09.
- Identidad de bytes F-09 para los tres archivos ausentes del manifiesto
  efectivo (tests B10, test de latencia y documentación).
- Estado actual de aceptación global fuera de los expedientes consultados.

**Decisión**

- Mantener `B10 = PARTIALLY_VERIFIED`.
- Mantener `B06 = FOCAL_EXECUTION_VALIDATED` con su scope y limitación de
  procedencia.
- Mantener P1.2 sin cerrar y el gate de release `NOT_AUTHORIZED`.

## 7. Cuestiones pendientes y siguiente paso propuesto

1. Si el responsable necesita acreditar **la ejecución histórica F-09**, buscar
   únicamente sus outputs originales en el almacenamiento autorizado de esa
   ejecución. Si no se recuperan, conservar esta adjudicación parcial; un
   rerun futuro sería evidencia de una ejecución nueva, no recuperación ni
   reemplazo de la evidencia histórica.
2. Sujeto a una directiva/autorización separada, una ejecución focal nueva
   podría preservar el comando íntegro, cwd, configuración, los siete nodeids,
   stdout/stderr, exit codes, resultado por test, identidad del candidato y
   hashes en un recibo verificable.
3. Antes de cualquier gate global, resolver el scope y criterios de
   `PRODUCT COMPLETE`, las dependencias de integración aplicables y las
   precondiciones formales requeridas por ese scope. No se solicita ni se
   presume autorización para tales operaciones.

## 8. Operaciones no ejecutadas y postflight

Durante F-12 no se ejecutó ningún test, benchmark, worker, servicio, gate,
`scripts/test.sh` ni `scripts/quality_gate.py`. No se consumió el snapshot B06;
no se abrió, copió, modificó ni migró ninguna base de producción o corpus. No
se modificaron código, configuración, fixtures, documentación existente,
índices SHA, artefactos F-06–F-11, branches, tags, commits, remotos ni el
checkout V1.0-elite.

El único cambio escrito por F-12 fue este informe nuevo. El postflight
comprobó que rama y HEAD permanecen iguales, que no hay staged y que el único
path nuevo respecto del preflight es este informe; no se revirtió ningún
cambio ajeno. El SHA-256 final del informe se comunica fuera de este archivo
para evitar autorreferencia ambigua.

## 9. Dictamen de liberación

```text
F-12 = COMPLETED
B06 = FOCAL_EXECUTION_VALIDATED
B10 = PARTIALLY_VERIFIED
B10_PRIMARY_EVIDENCE = PARTIALLY_RECOVERED
P1.2 = FAIL / DIAGNOSTIC (plan maestro);
       BLOCKED-REGRESSION (STEP-22/STEP-05, registros no equivalentes a una corrida actual)
PRODUCT COMPLETE = PENDING
RELEASE_GATE = NOT_AUTHORIZED
RELEASE_VERDICT = NOT_ISSUED
TESTS_EXECUTED = NONE
WORKERS_EXECUTED = NONE
GATES_EXECUTED = NONE
PRODUCTION_DB_OR_CORPUS_MODIFIED = NO
EXISTING_FILES_MODIFIED = NO
```

F-12 es una adjudicación documental limitada. No acredita certificación de
TALOS V1.5 ni aprobación de release.
