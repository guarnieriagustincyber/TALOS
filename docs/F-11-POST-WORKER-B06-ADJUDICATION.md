# TALOS V1.5 — F-11 adjudicación post-worker B06

**Fecha:** 2026-10-10
**Repositorio:** `/media/agustin/Laboratorio/study-engie`
**Rama / HEAD:** `talos-current-audit` / `032339436639d33d310c437c88fe01d94e977449`
**Gate de release:** `NOT_AUTHORIZED`
**F-11:** `COMPLETED`

## 1. Alcance y preservación

Esta adjudicación contrasta artefactos F-09/F-10, el estado Git, los recibos,
los logs y los contratos/documentos citados. No ejecuta tests, código del
proyecto, servicios, workers ni gates; no modifica snapshots, capturas, bases
fuente, refs ni artefactos históricos.

Al inicio de F-11, antes de crear este informe:

| Propiedad | Observado |
|---|---|
| Repositorio | `/media/agustin/Laboratorio/study-engie` |
| Rama | `talos-current-audit` |
| HEAD | `032339436639d33d310c437c88fe01d94e977449` |
| Staged | 0 |
| Tracked modificados | 22 |
| Untracked | 178 |
| Otros estados | 0 |
| Líneas de `git status --porcelain=v1 -uall` | 200 |
| SHA-256 de esa salida completa | `65bfdfbf722527e82690fb315f985c2f1404e03fe78e5a7619fea8cb13b7a3ce` |

La identidad y el hash del estado coinciden exactamente con `F-10/preflight.json`.
No se atribuye autoría a los cambios preexistentes. La creación de este informe
añade un archivo untracked; no se limpió ni reorganizó ninguno de los estados
observados. HEAD y refs no cambiaron.

## 2. Evidencias examinadas y hashes

Los dos índices originales de hashes se verificaron con `sha256sum -c`; todas
las entradas reportaron coincidencia. Los índices no se modificaron.

### F-09

Directorio: `/media/agustin/Almacenamiento/Facultad/TALOS/historical-evidence/F07-F12/talos-f09-authorization-gUVYAnpn/`

| Evidencia | SHA-256 / digest |
|---|---|
| `SHA256SUMS.txt` | `e94c65cb8b20b36a90a0551fa9591bc5e7113e71f91330b07ad05faa13f83a6b` |
| `F-09-DECISION-RECORD.md` | `b86e82589a08d74a95fc6d371ed5d35248717b265805abfe079f8a585983b819` |
| `F-09-RESULTS.md` | `112009f620cae3927f4b63ca7524503bb19316735a52fb431d8b40980896e80f` |
| `effective-execution-manifest-v2.json` (hash del archivo) | `cec40dfb44e77a8fcbd5e56b5d78844f5bcb506b65ab2d4087c5e5b5056e3916` |
| Manifiesto efectivo canónico | `sha256:14f8d3787aafd11b9eb85912632f104b8c6c960f23bef7b194f7e479a34e5002` |
| Snapshot final `...-v2/manifest.json` | `1985a58de05437b3c0e1e7857438680e85846f9dbd8a374876910ff596feb502` |
| `b06-validation-record-v2.json` | `2417565f8a4ff36975c83c2a889f338b8b7e61161c184e314c4bb46250294e56` |
| Binding de validación F-09 (archivo) | `ecae0dee11a3580dd5f9f315656b513864cb2228a6e482097affb1a4a5af9f45` |
| Digest canónico de ese binding temporal | `sha256:6cf5f691bfad4e3baddd1f86bc6e8b9fb05ac1ce14f42bfbab1990948d6b67dd` |

El resultado de F-09 identifica explícitamente como supersedidos y no
consumibles el manifiesto, snapshot y binding de primera iteración. El registro
del manifiesto v2 también identifica el digest anterior que sustituye. Los
artefactos supersedidos permanecen intactos e indexados; el F-10 preflight
apunta únicamente a los artefactos v2.

Attestation original F-06, fuera del directorio F-09:

- Ruta: `/media/agustin/Almacenamiento/Facultad/TALOS/historical-evidence/B06/talos-v1.5-b06-capture-e9af1327-fe78-416f-a1b6-cc5a41af2369/capture-attestation.json`
- SHA-256 calculado durante F-11: `a8307b20444a325e14e1c99829eb135ebfb96b441a402132c3daf59b0b4329c7`.
- El `capture_id` `492052c7-0c96-48d6-b318-d3873a67b104`, los nueve registros
  de bases/sidecars y el digest de attestation coinciden entre attestation,
  manifest sellado y binding del recibo F-10.

### F-10

Directorio: `/media/agustin/Almacenamiento/Facultad/TALOS/historical-evidence/F07-F12/talos-f10-worker-20261010T1529Z-e9af1327-fe78-416f-a1b6-cc5a41af2369/`

| Evidencia | SHA-256 |
|---|---|
| `SHA256SUMS.txt` | `24c7981f5bbcb6968e069ec1834c542e2951fd68e39269d5189fbb41b4ca71ca` |
| `preflight.json` | `808dc8d8b7674074cf976e9d4725e177522a7386d28755f5583c57e908e917d9` |
| `postflight.json` | `5e3ee8bd5f8919609a7f8d67b2c9e9b346fb4f188eafc25bb401c1ac80029495` |
| `worker.stdout.log` | `5f1a9a4ee93788ba126e2de2410b5f68e1da17baddd34b08c7fe13606da402c0` |
| `worker.stderr.log` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `worker.exit-code` | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| `focal-execution-receipt.json` | `e8999a66dbd938d2332c758fb251eabb4d20f7acba53830b8c402124fde937c4` |

`preflight.sha256` y `postflight.sha256` también coinciden con el índice. El
archivo `worker.stderr.log` está vacío; la salida del proceso quedó en
`worker.stdout.log`.

## 3. Adjudicación del resultado focal

El recibo registra:

- Nodeid solicitado: `tests/pedagogy/test_talos_vs_notebooklm_e2e.py::test_p3_debug_query_abstains_without_sufficient_evidence_sse`.
- `collected_nodeids` contiene exactamente ese único nodeid y
  `exactly_one_selected_test=true`.
- `test_outcome=passed`, `pytest_exit_code=0`, `runner_exit_code=0` y
  `worker.exit-code=0`.
- El log primario confirma `1 passed, 4 warnings in 7.79s` y repite el nodeid
  con `collected_exactly_one=True`, `outcome=passed`.
- `execution_mode=focal_test`, `execution_status=PASS`.

El digest canónico del objeto `binding` del recibo fue recalculado sin ejecutar
código del proyecto: `sha256:8380d52bc0f0397bb62b3d5c5391f03d0449760106bac761338e45fbc6cf27bb`.
Coincide con `focal-execution-receipt.json:binding_sha256` y
`result.binding_sha256`; es distinto del digest del binding temporal F-09.
El recibo identifica un workspace nuevo para la ejecución (`/workspace/run/test-data`).

El recibo declara aislamiento `bubblewrap`, con namespaces mount
`mnt:[4026532871]`, network `net:[4026532876]` y PID `pid:[4026532874]`,
además de PID de worker 2. La configuración del boundary vigente incluye
`data/web_state` en sus directorios protegidos, consistente con el acceso por
copias de trabajo aisladas. No se usó el binding temporal F-09.

**Adjudicación:**

```text
B06_FOCAL_RESULT = VALIDATED_TEST_PASS
```

La afirmación se limita a este único test y a esta ejecución. No valida otros
escenarios, la ruta pedagógica completa, todas las rutas SSE ni el sistema.

Las cuatro advertencias que constan en el log son `DeprecationWarning` por
`FastAPI.on_event` en `src/study_engine/web/app.py:94` y en
`fastapi/applications.py:4579` (dos apariciones por ubicación). No son fallos
del test y no hay evidencia de que hayan sido corregidas.

## 4. Adjudicación de B06

| Dimensión | Estado | Evidencia y límite |
|---|---|---|
| Preparación | `VERIFIED` | F-09 manifestó manifiesto de 411 entradas, snapshot v2 sellado e integridad SQLite `ok` en copias descartables. Hashes de ambos artefactos coinciden. |
| Frescura | `VERIFIED_FOR_THIS_RUN` | TTL 3600 s, desde `2026-10-10T14:55:05.217414Z`; preflight a `15:30:04Z` informó 1500 s restantes; postflight informó 1392 s restantes y snapshot `VALID`. |
| Correspondencia | `VERIFIED` | Digest efectivo `sha256:14f8…e5002`, HEAD y snapshot coinciden antes/después; la attestation fuente conserva el mismo capture ID y digest. |
| Binding | `VERIFIED` | Binding F-10 nuevo, digest comprobado entre objeto, receipt y resultado; el digest es distinto del binding temporal F-09. |
| Ejecución | `VERIFIED` | Un único nodeid recolectado y pasado; códigos pytest, runner y proceso todos 0. |
| Aislamiento | `VERIFIED_AS_RECORDED` | Receipt declara bubblewrap y namespaces distintos. Esta adjudicación se limita a la evidencia del runner y sus identificadores. |
| Integridad posterior | `VERIFIED` | `postflight.json` registra snapshot `VALID`; la huella del manifiesto efectivo coincide con preflight. |
| Alcance | `VERIFIED` | La ejecución fue focal; el log reporta un caso pasado. No se ejecutó suite completa ni gate. |
| Bases fuente / refs | `NO_CHANGE_RECORDED` | Preflight y postflight mantienen mismo HEAD y hash del estado Git; no se reportan escrituras a las bases fuente. No hay en F-10 hashes independientes pre/post de los bytes fuente, por lo que una comparación directa de contenido de esas bases es `UNVERIFIED`. |

Adjudicación del alcance autorizado:

```text
B06 = FOCAL_EXECUTION_VALIDATED
```

Este estado no equivale a certificación global. La captura usa
`quiesced_file_copy`, consistencia `quiesced` y `local_integrity_only`: aporta
integridad y trazabilidad locales, pero no prueba atomicidad de filesystem ni
autenticación independiente.

## 5. Adjudicación de B10

La inspección estática confirma que `config/test_perimeter.json` declara como
informativo el nodeid exacto
`tests/performance/test_latency_disaggregated.py::test_sqlite_query_latency_p95_under_50ms`;
no reclasifica el módulo completo. El runner preserva el exit code bruto de
pytest y distingue el estado `INFORMATIVE_FAIL`. Solo clasifica como no
bloqueante un `AssertionError` en `call` para ese nodeid; fallos de setup,
teardown, colección, skip, otras excepciones y fallos de otros tests continúan
bloqueando. Las pruebas sintéticas correspondientes están en
`tests/ci/test_quality_gate_perimeter.py`.

F-09-RESULTS.md — cuyo hash consta en el índice verificado — informa siete
pruebas focalizadas aprobadas y el chequeo Ruff limitado aprobado. Sin embargo,
el directorio de artefactos F-09 no contiene el transcript primario de pytest
ni un registro de los siete nodeids/argumentos ejecutados. El informe
conservado verifica que esa adjudicación fue registrada, no proporciona
reproducción independiente del run.

```text
B10 = PARTIALLY_VERIFIED
```

La clasificación y semántica quedan corroboradas estáticamente; el resultado
de las siete ejecuciones focalizadas queda respaldado por el reporte F-09
verificado por hash, pero sus detalles primarios son `UNVERIFIED`. No se
re-ejecutó ninguna prueba.

## 6. Bloqueos pendientes para una eventual certificación

| Bloqueo | Estado / evidencia | Impacto |
|---|---|---|
| Gate de release | `NOT_AUTHORIZED`; F-11 no ejecutó ni autorizó `scripts/test.sh`, suite completa ni gate. | No hay veredicto de release. |
| P1.2 global | La documentación vigente conserva `FAIL / DIAGNOSTIC` / `BLOCKED-REGRESSION`. El registro histórico STEP-05 reportó 15 fallos en el gate canónico. El PASS focal F-10 no invalida ese resultado ni lo re-adjudica. | P1.2 no está cerrado. |
| Criterios/scope de release | El plan maestro identifica pendiente la definición de `PRODUCT COMPLETE` y el scope verificable de release. | Sin adjudicación global de elegibilidad. |
| Cualificación del candidato actual | F-10 ejecutó solo B06 focal; no ejecutó el resto de los tests requeridos/qualification-required. | Propiedad integral del candidato no evaluada en F-10/F-11. |
| Procedencia de captura | `local_integrity_only`; no atomicidad ni autenticación externa. | Limitación residual, no removida por el snapshot o el PASS. |
| Advertencias FastAPI | Cuatro deprecations observadas en el log focal. | Deuda técnica registrada; no corregida ni bloqueante para este test focal. |
| B10 evidencia primaria | Informe F-09 verificado; transcript y nodeids exactos de los siete tests focalizados no preservados. | Mantener B10 como parcialmente verificado en esta adjudicación. |
| A-PRE formal | El plan maestro registra A-PRE-1 como `NOT_AUTHORIZED / NOT_EXECUTED` y A-PRE-0 como no listo por autoridad/evidencia pendiente. | Bloquea claims de assurance formal que dependan de A-PRE; el plan no lo trata como bloqueo automático de toda funcionalidad. |
| Gates funcionales restantes | El plan maestro enumera aceptación Gate B, F5/Gate C, F6/Gate D, B2–B6 controlados y regresión PRE→POST pendientes o parciales. | Resolver solo según el scope/claims del release que se adjudique; no se reabrieron aquí B01–B05 ni B07–B09. |

Los bloqueos se registran desde los documentos canónicos citados; F-11 no
inició una auditoría de sus causas ni cambió sus estados.

## 7. Operaciones no ejecutadas

No se ejecutaron tests adicionales, benchmark, suite completa, worker adicional,
`scripts/test.sh`, `quality_gate.py` como gate, ni gate de release. No se creó
captura/snapshot, no se accedió a las bases fuente para alterarlas, no se
modificaron corpus/modelos/estado del estudiante, ni se cambiaron commits,
branches, tags, remotos, historial o V1.0-elite. No se modificó B10 ni se
alteraron evidencias F-06–F-10.

## 8. Cierre

```text
B06 = FOCAL_EXECUTION_VALIDATED
B10 = PARTIALLY_VERIFIED
F-11 = COMPLETED
RELEASE_GATE = NOT_AUTHORIZED
```

F-11 adjudica evidencia de una ejecución focal de B06; no certifica TALOS V1.5,
no declara `RELEASE_READY` y no aprueba el release.
