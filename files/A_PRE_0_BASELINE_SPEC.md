# A-PRE-0 — Especificación de baseline PRE

**A-PRE-0:** `NOT READY`  
**Preflight:** `REVIEW REQUIRED / NOT READY FOR A-PRE-1`  
**Baseline PRE certificada:** ninguna  
**A-PRE-1:** `NOT EXECUTED`  
**Autorización A-PRE-1:** `PENDING / NOT AUTHORIZED`  
**Alcance:** definir una comparación reproducible y calificar solo mecanismos
sintéticos del harness; no ejecutar TALOS, sus suites ni cambiar código
funcional.

## 1. Identidad del snapshot

La inspección de especificación comenzó sobre la rama `main`, con
`HEAD=b12e34099336760e8fd55455526a580cd479dade`. Ese checkout ya estaba sucio
(13 paths modificados/no comprometidos antes de esta especificación), por lo
que no es una baseline PRE limpia. A-PRE-0 y sus cambios de documentación/
manifiesto también forman parte de ese estado de trabajo; no deben confundirse
con el snapshot que A-PRE-1 certifique.

Actualización de identidad para la calificación del harness (2026-10-01): el
checkout fuente actual es `main` en `a04aa3630521ad21027d38b2e3ac3b83bb0fca3d`
(`A-PRE clean snapshot rev4`), hijo directo del commit histórico `b12e340`.
El checkout conserva ocho paths tracked modificados intencionalmente y un
nuevo módulo de política seccomp sin seguimiento; la copia aislada incorpora
nueve paths modificados respecto de `a04aa36`. La referencia anterior a un
overlay basado en `b12e340` no describe el snapshot actual. Las identidades
sucesivas y el inventario de la copia aislada están registrados externamente
en `/home/agustin/apre-runner/cpython-3.10.21/evidence/a-pre-snapshot-identity-20261001/`.
Ese overlay representa el contenido exacto probado, no es una baseline PRE
limpia de TALOS ni autoriza A-PRE-1.

A-PRE-1 solo podrá ejecutarse desde un commit explícito y un árbol de trabajo
limpio. Su registro de identidad debe incluir:

- repositorio, rama, SHA completo, estado del árbol y diff respecto del commit;
- sistema operativo, arquitectura y versión de kernel;
- intérprete efectivo (`sys.executable`), versión y ABI de Python;
- versión de `uv`, comando exacto, perfil y variables relevantes;
- hashes SHA-256 del manifiesto de perímetro, fuentes de dependencias y
  scripts/contratos que determinan la selección y ejecución de pruebas.

La observación del checkout actual fue Linux x86_64, kernel `7.0.0-34-generic`,
glibc 2.39, CPython 3.12.3 y uv 0.12.10. Es información diagnóstica, no la
identidad del runtime candidato para PRE.

## 2. Perímetro

La fuente normativa es [`config/test_perimeter.json`](../config/test_perimeter.json):
25 suites raíz —22 `required`, 2 `qualification-required` y 1 `support-only`—,
además de 2 módulos `optional` identificados explícitamente por ruta. El perfil
release de [`scripts/test.sh`](../scripts/test.sh) ejecuta `required` y
`qualification-required`; excluye `optional`; `support-only` no se ejecuta como
suite. La clasificación efectiva por archivo en el árbol observado al
actualizar esta especificación es: 438 `required`, 13
`qualification-required`, 2 `optional` (overrides de módulos que pertenecen a
suites `required`) y 1 `support-only`, total 454 archivos `test_*.py`. Después
de añadir los fixtures de reporter/observer y harness, el conteo actual es 456:
440 `required`, 13 `qualification-required`, 2 `optional` y 1 `support-only`.
Por tanto, el perfil release ejecutaría 453 archivos, aparte del
inventario de casos que realmente recolecte pytest.
El número de archivos no sustituye ese inventario.

Conteos de referencia estáticos:

| Snapshot | Archivos `test_*.py` | Interpretación |
|---|---:|---|
| `99bd754` | 447 | 446 módulos ejecutables + `tests/utils/test_registry.py` (`support-only`) |
| `b12e340` | 451 | 450 módulos ejecutables + el mismo helper `support-only` |
| Árbol observado al especificar A-PRE-0 | 453 | 451 versionados + 2 módulos B1-R nuevos en `tests/audit` |
| Árbol actual con reporter, observer y harness A-PRE | 456 | 451 versionados + 2 módulos B1-R + 3 módulos A-PRE de fixtures, no comprometidos |

Los cuatro módulos ejecutables añadidos entre `99bd754` y `b12e340` son:
`tests/unit/diagnostics/test_backend_selection_adjudication_packets.py`,
`test_backend_selection_contract.py`, `test_vector_space_contract.py` y
`test_vector_space_promotion.py`. La cifra histórica 446 excluía el helper; la
diferencia hasta 451 queda explicada por esos cuatro módulos y el helper
`support-only`, no por cinco pruebas cuya eliminación esté autorizada. El
inventario actual se debe recalcular desde el snapshot limpio de A-PRE-1.

Antes de autorizar la ejecución, la validación estática del manifiesto debe
pasar y registrar conteos por clasificación, overrides, módulos recolectados,
errores de colección y skips. Un cambio de perímetro entre PRE y POST invalida
la comparación directa salvo que se documente y se limite explícitamente a un
análisis secundario.

## 3. Dependencias y runtime candidato

La autoridad declarativa del proyecto es `pyproject.toml`. El conjunto pinneado
para reconstruir el entorno completo de verificación es `requirements.lock`,
generado desde el proyecto con `--all-extras` y target Python 3.10. Ese lock
incluye extras como `local-inference` y también está asociado al candidato E5;
usarlo para sincronizar dependencias de la suite TALOS no ejecuta E5, carga un
modelo ni autoriza ese experimento. La receta canónica está documentada en
[`DEPENDENCY_REPRODUCIBILITY.md`](./DEPENDENCY_REPRODUCIBILITY.md). El lock
permanece sin cambios durante A-PRE-0 y A-PRE-1.

Fuentes observadas al especificar:

| Archivo | Rol | SHA-256 |
|---|---|---|
| `pyproject.toml` | configuración declarativa | `6324fc8e95f9e76209fbbe303d9a75676a59c0864206ea8a63ecb6ab3476b708` |
| `requirements.lock` | lock pinneado para verificación completa, target Python 3.10; asociado también al candidato E5 | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| `requirements.txt` | lista parcial obsoleta, no fuente de instalación soportada | `fdd1be3c75641227f6bdca872e97aea400606e8158f071541642273c98e0fa8c` |
| `requirements-audit.in` | inputs de herramientas de auditoría, separado del runtime | `441fda7a986042d25707052a0d808756492ea0cc64eb0f8430d696e43b1c5038` |
| `requirements-audit.lock` | lock de herramientas de auditoría para Python 3.12 | `79ef4d2aeda836e75cd93be0731fe7ced0894cea55a2ecdde369fa469db9af2d` |

El `.venv` observado existe, pero usa CPython 3.12.3 y no satisface el target
Python 3.10 del lock candidato. Su presencia o capacidad de importar paquetes no
lo convierte en runtime PRE reproducible. A-PRE-1 deberá crear/usar un entorno
temporal aislado que cumpla el lock y registrar el Python y las versiones
efectivamente instaladas. El procedimiento reproducible candidato es:

```text
<UV_0_12_20> venv --python <PYTHON_3_10> <PRE_VENV>
<UV_0_12_20> pip sync --python <PRE_VENV>/bin/python requirements.lock
```

`<PRE_VENV>` debe estar fuera del checkout y ser nuevo/vacío. El preflight
ejecutó la creación del venv y solo la sincronización en `--dry-run`; no
instaló paquetes. El `.venv` existente no se reutiliza ni modifica.
`requirements.lock` se lee como input de dependencias y permanece estrictamente
sin cambios; no se ejecuta el modelo E5 ni Qwen.

La inspección preflight encontró un intérprete uv-managed CPython 3.10.21 local.
Con uv 0.12.20, en venvs temporales externos al checkout, la sincronización
dry-run resolvió 61 paquetes y la sincronización real instaló los 61 paquetes
del lock (12 descargados), sin modificar el lock ni el `.venv` del proyecto.
`uv pip check` verificó compatibilidad de los 61 paquetes; imports smoke de
FastAPI/httpx, NumPy, Pydantic, PyMuPDF/PyPDF, YAML, RapidFuzz, SciPy, ONNX
Runtime y Tokenizers pasaron. No se cargó modelo ni artefacto E5/Qwen.

Esto demuestra viabilidad de resolver e instalar dependencias para este
Python/plataforma, no instalación editable de TALOS, imports de la aplicación
ni recolección de sus tests. `scripts/test.sh` prioriza
`$REPOSITORY_ROOT/.venv/bin/python` y seleccionaría Python 3.12; A-PRE-1 usará
directamente `<PRE_VENV>/bin/python scripts/quality_gate.py --profile release`.
Los imports de la aplicación y la colección permanecen pendientes hasta tener
snapshot limpio e inventario de efectos completado. No se actualizará el lock
para acomodar el `.venv` por conveniencia.

## 4. Efectos y artefactos

La ejecución futura se hará desde el snapshot limpio y con sus artefactos en un
directorio de evidencia fuera del checkout. La política es:

| Clase | Política |
|---|---|
| `ALLOWED` | Logs, reporte estructurado, cobertura y temporales creados bajo el directorio de evidencia/temporales aislado de la ejecución. |
| `FORBIDDEN` | Cambios a archivos versionados, datos/corpus/modelos protegidos, blind pool, artefactos E5/Qwen, providers externos o recursos de producción. Una escritura detectada invalida PRE. |
| `EXPECTED-CLEANUP` | Temporales propios de la ejecución bajo su directorio aislado; limpiar al terminar o conservarlos dentro de evidencia si son necesarios para reproducir el fallo. |
| `PROTECTED` | `.venv` existente, base de datos/corpus/modelos existentes, resultados de experimentos, artefactos E5/Qwen y cualquier recurso de producción; no leer para fixtures ni escribir desde suites. `requirements.lock` se lee solo como input de dependencias y nunca se modifica. |

Se conocen antecedentes de suites que reescribían
`benchmark/results/evaluation_report.json`, `evaluation_report.md`,
`latest_summary.json` y `data/experiments/survival/l5_concurrency_race_50.json`;
los fixes posteriores redirigieron esas escrituras a `tmp_path`. Esto es una
señal de riesgo histórico, no prueba de esterilidad de todo el perímetro. Antes
de A-PRE-1 se debe completar el inventario estático pendiente de escrituras,
aperturas de DB, corpus, modelos, red y subprocess por suites; los tests deben
usar fixtures/tempdir o guardas que fallen ante acceso protegido. El estado
`.gitignore` no cuenta como barrera de seguridad.

Al concluir, el wrapper debe comparar el estado del checkout con el manifiesto
de entrada. Toda diferencia inesperada, incluso si está ignorada por Git,
produce `ERROR` y bloquea la certificación. La ejecución de suites no tendrá credenciales de providers ni acceso de salida
a red. Sincronizar el lock de pruebas puede instalar el paquete `onnxruntime`
en el venv temporal, pero no descarga/abre el artefacto E5 ni ejecuta inferencia.
Fuera de alcance explícito están la ejecución/inferencia del modelo E5, su
benchmark, Qwen, blind pool,
BENCH-G2, la comparación TALOS-vs-NotebookLM, DB/corpus/modelos de producción,
providers reales, migraciones y cualquier cambio de datos. Los módulos
`optional` de live-provider nunca forman parte de PRE release.

El checkout observado estaba sucio, por lo que este pre-screen no reemplaza la
adjudicación sobre el commit limpio que se vaya a certificar. Debe revisarse,
por suite, escrituras, DB/SQLite, corpus/modelos, sockets/red y
procesos/subprocesos; cualquier excepción permitida debe nombrar su fixture o
directorio temporal. Este requisito no se considera cumplido por B1-R, que
cubre únicamente su boundary sintético.

Como pre-screen sobre el árbol sucio se parsearon estáticamente los 453 módulos
`test_*.py` con AST y se marcaron llamadas directas a APIs de posible efecto.
Los hallazgos se solapan entre categorías; no implican que la llamada llegue a
ejecutarse ni distinguen por sí solos mocks, `tmp_path` o rutas protegidas:

| Suite | DB | Filesystem mutation | Network | `open` | Process |
|---|---:|---:|---:|---:|---:|
| `adversarial` | 5 | 11 | 2 | 13 | 1 |
| `audit` | 1 | 3 | 1 | 1 | 1 |
| `benchmark` | 0 | 0 | 0 | 1 | 0 |
| `ci` | 0 | 1 | 0 | 1 | 0 |
| `contract` | 0 | 2 | 0 | 7 | 1 |
| `experiments` | 0 | 1 | 0 | 2 | 1 |
| `hierarchy` | 1 | 0 | 0 | 0 | 0 |
| `integration` | 0 | 1 | 1 | 1 | 0 |
| `llm_pool` | 1 | 0 | 1 | 0 | 0 |
| `pedagogy` | 1 | 3 | 0 | 0 | 0 |
| `protected` | 0 | 0 | 0 | 1 | 0 |
| `retrieval` | 1 | 0 | 0 | 0 | 0 |
| `session` | 0 | 0 | 1 | 0 | 0 |
| `storage` | 0 | 1 | 0 | 0 | 0 |
| `survival` | 0 | 2 | 0 | 0 | 0 |
| `unit` | 12 | 33 | 3 | 4 | 1 |
| `web` | 0 | 2 | 0 | 0 | 0 |

El primer barrido histórico de 453 módulos encontró 99 candidatos; al añadir
`tests/audit/test_apre_result.py`, su barrido de 454 módulos marcó 100
candidatos (22 DB, 60 filesystem, 9 network, 31 `open`, 5 process; los totales
por clase se solapan). Esos conteos corresponden a un pre-screen anterior y
no se deben atribuir al snapshot actual.

El 2026-10-01 se volvió a parsear estáticamente el overlay exacto de 456
módulos versionados: 440 `required`, 13 `qualification-required`, 2 `optional`
y 1 `support-only`; no hubo errores de parseo. El pre-screen directo, con
resolución de alias de imports pero sin inferencia de tipos de receptores,
identificó 34 llamadas DB en 22 módulos, 350 candidatos de mutación de
filesystem en 62 módulos, 126 candidatos de lectura de filesystem en 43
módulos, 65 llamadas `open` en 33 módulos y 13 llamadas de procesos en 4
módulos; las categorías pueden solaparse. No encontró llamadas de red que
coincidieran con sus nombres/rutas importadas reconocibles. Este último cero
no prueba ausencia de red: quedan fuera los métodos de objetos cuyo tipo no se
resuelve, wrappers, callbacks, efectos transitivos y llamadas dinámicas. El
pre-screen contextualizó todas las llamadas directas a procesos: son
subprocesses de fixtures bajo `tmp_path`/`TemporaryDirectory`, lecturas de
estado Git, o probes sintéticos cuyo intento de `Popen` se rechaza mediante
audit hook antes de crear el proceso. Esto es una adjudicación estática del
código y sus guardas, no evidencia dinámica de una suite.

Se corrigieron estáticamente dos dependencias no herméticas en los tests:

- `tests/retrieval/test_query_rewriter_inflections.py` ahora crea una fuente
  textual sintética dentro de `tmp_path` con todos los plurales canónicos y
  entrega esa ruta explícitamente a `ingest_benchmark_corpus`; ya no inspecciona
  existencia ni usa fallback hacia `data/benchmark/sources`.
- `tests/pedagogy/test_chat_sse_endpoint.py` ya no copia
  `data/web_state/knowledge_store.db` en su fixture de módulo. La prueba de ACL
  ahora crea notebook, fuente, documento y chunks target/foreign sintéticos en
  la DB de `tmp_path`, conservando las aserciones de aislamiento de búsqueda,
  provenance, SSE y neutralidad del perfil curricular. La condición de skip
  por DB local y los hashes de esa base fueron eliminados.

Ambos archivos pasan parseo sintáctico y el diff whitespace check; se comprobó
estáticamente que no contienen referencias a `data/benchmark/sources`,
`data/web_state/knowledge_store.db`, `original_db`, `source_uri` ni
`shutil.copy2`. Los dos nodos de fixtures herméticos pasaron (`2/2`) y las
pruebas sintéticas focalizadas de harness, builder y verifier pasaron (`33/33`)
bajo CPython 3.10.21. No se ejecutaron suites TALOS, `scripts/test.sh` ni el
gate release.

El inventario completo, el scanner y sus hashes están en
`/home/agustin/apre-runner/cpython-3.10.21/evidence/a-pre-snapshot-identity-20261001/`.
Los hallazgos son candidatos estáticos, no prueba de ejecución, acceso externo
ni contaminación; la adjudicación contextual de filesystem, reads, DB y
barriers sigue pendiente. La esterilidad permanece `UNVERIFIED`, no `PASS`.

### Snapshot limpio reversible

El checkout fuente no se limpia, no recibe stash y no se modifica para obtener
un snapshot. El procedimiento reproducible usa una copia local aislada fuera
del repositorio:

1. Capturar `HEAD`, diff binario contra `HEAD`, lista de estado, inventario de
   hashes de archivos versionados/no ignorados y hash de `requirements.lock`.
2. Clonar localmente sin hardlinks y sin checkout al directorio de evidencia
   externo; fijar el checkout en el `HEAD` capturado.
3. Aplicar el diff versionado y copiar únicamente los archivos no ignorados
   sin seguimiento. No copiar `.git`, `.venv`, secretos ignorados, datos locales
   ni artefactos protegidos ignorados.
4. Crear en esa copia un commit-overlay local cuyo padre sea el `HEAD` fuente.
   Registrar SHA del padre, commit-overlay, tree, diff e inventario de archivos.
5. Si el clone usa object alternates, ejecutar `git repack -a -d`, retirar el
   archivo `objects/info/alternates` de la copia aislada y exigir que
   `git fsck --full --connectivity-only --no-dangling` pase sin alternates.
6. Exigir que el worktree aislado esté limpio y que el fingerprint del checkout
   fuente antes/después sea idéntico. Si cambia cualquier entrada, abortar y
   no usar la copia.

Esto produce una identidad auditable del contenido observado sin afirmar que
el checkout fuente estaba limpio. La copia se puede retirar eliminando
únicamente su directorio y manifiesto externos; nunca se usa `git clean`,
`stash`, `reset` ni checkout sobre el repositorio fuente. El snapshot vigente y
su manifiesto externo se conservan en el área de sesión, identificados por SHA
del overlay, padre, árbol e integridad autónoma del object store. La copia
calificada solo ejecutó las pruebas sintéticas de harness/result y el
pre-screen AST; no ejecutó imports de TALOS, colección de sus suites, el gate
release ni A-PRE-1.

### Contrato de observación dinámica de efectos

El pre-screen AST no adjudica efectos. `scripts/apre_effects.py` instala un
audit hook Python y se conecta opcionalmente a `quality_gate.py` mediante
`--apre-effects-output` más `--apre-scratch-root`. Seis fixtures sintéticos
cubren rutas temporales/externas, SQLite en memoria, socket/subprocess
sintéticos, atribución por caso y salida externa. El reporte declara
`native_syscalls=false` y `complete=false`.

#### Harness de aislamiento A-PRE-0.5

El runner
[`scripts/apre_harness.py`](../scripts/apre_harness.py) conecta bubblewrap,
strace, collector, emisor y CLI verifier sin ejecutar TALOS por sí mismo.
Requiere snapshot limpio, venv externo CPython 3.10, uv 0.12.20 y directorios
externos vacíos para evidencia y scratch. Recopila hashes de inputs y
artefactos, genera `result.json` completo y ejecuta el CLI verifier
independiente.
Bubblewrap expone el snapshot/runtime como solo lectura, no monta el HOME del
host, crea namespaces de red/PID y deja escribibles únicamente evidencia,
scratch y `/tmp`. La captura propuesta usa `strace -ff -q -ttt -yy -s 0 -e
trace=all`; separa stderr del tracer y del proceso, y solo declara
`trace_complete=true` si todas las trazas por proceso terminan en un marcador
reconocido, no hay llamadas sin reanudación ni diagnósticos del tracer y se
observa `execve`/`execveat`. `-s 0` conserva eventos y resultados sin volcar
payloads de `read`/`write`. Esta propiedad certifica captura de eventos syscall,
no cobertura completa de efectos.

La cobertura de efectos es una dimensión separada. El observer Python actual
declara `native_syscalls=false` y `complete=false`, de modo que los efectos
permanecen `UNKNOWN` y el resultado no puede ser `PASS` aunque la captura
syscall sea íntegra. Si se observa `io_uring_setup`, `io_uring_register`,
`io_uring_enter` o Linux native AIO (`io_setup`, `io_submit`, `io_getevents`,
`io_pgetevents`, `io_cancel`, `io_destroy`), los efectos relevantes también
quedan `UNKNOWN` salvo que se demuestre una barrera preventiva efectiva. El
harness integra el perfil seccomp versionado
`a-pre-native-async-deny-v1` (`scripts/apre_seccomp.py`) en cada invocación de
bwrap. En Linux x86_64 deniega con `EPERM` `io_uring_setup`, `io_uring_enter`,
`io_uring_register`, `io_setup`, `io_destroy`, `io_getevents`, `io_submit`,
`io_cancel` e `io_pgetevents`, incluidas sus variantes x32; otras arquitecturas
fallan cerradas. El filtro es default-allow fuera de esa lista y no resuelve
`ioctl` opacos, stores sobre `MAP_SHARED`, otros mecanismos async ni cobertura
global.

Antes de cualquier gate, el preflight invoca sintéticamente las nueve syscalls
bajo el mismo wrapper `strace → bwrap`, verifica para cada una el retorno
`-1/EPERM` y repite `io_uring_setup` en un proceso hijo. El artefacto
`seccomp-probe.json`, el perfil/hash y el resultado syscall deben coincidir;
el builder y el verifier independiente rechazan `PASS` si falta cualquiera.
Un intento observado se clasifica `BLOCKED` para su familia únicamente cuando
la traza confirma `EPERM` bajo ese perfil. Esto cierra preventivamente las dos
familias async de la lista, pero **no** hace completo el agregado:
`effect_coverage.status` permanece `UNKNOWN` y el preflight no inicia release
mientras queden otros dominios o el observer nativo sin cobertura. No se
sometió I/O real mediante SQE/AIO.
Una operación no clasificable, una salida del perímetro o una laguna del
observer será `UNKNOWN` y no podrá producir esterilidad `PASS`.

Las fixtures sintéticas verifican escritura permitida en scratch, rechazo de
escrituras al snapshot/sistema, SQLite y subprocess dentro del namespace,
acceso a `/proc` del PID aislado y fallo de conexión de red. Esto demuestra
contención de esos probes, no una ejecución de TALOS ni cobertura total de
syscalls. El collector del gate se entrega al emisor vía variables de entorno
privadas del harness (`TALOS_APRE_EFFECTS_OUTPUT`,
`TALOS_APRE_SCRATCH_ROOT`, `TALOS_APRE_COLLECTOR_OUTPUT`), conservando el argv
fijo registrado por el contrato.

Cada evento se adjudicará como `REAL` (recurso no temporal intentado/tocado),
`TEMPORARY` (confinado al scratch), `MOCKED` (dependencia reemplazada y sin
syscall externo), `INDIRECT` (efecto originado en dependencia transitiva),
`NONE` (caso ejecutado con cobertura íntegra y sin evento) o `UNKNOWN`.
`MOCKED` exige evidencia de la sustitución; ausencia de syscall por sí sola no
prueba un mock. El resultado por suite/caso y la cobertura del observer deberán
quedar en artefactos verificables. Esta tarea no ejecuta ni importa TALOS:
la adjudicación de los efectos que realmente produzca TALOS solo puede ocurrir
durante una futura ejecución autorizada A-PRE-1. A-PRE-0 no debe anticipar esos
efectos; sí debe calificar previamente que el instrumento puede observar,
atribuir o bloquear los mecanismos requeridos y que falla cerrado ante lagunas.

## 4.1 Separación normativa entre readiness A-PRE-0 y resultado A-PRE-1

El Modelo B aprobado el 2026-10-01 define el alcance de seguridad de A-PRE-0:
el workload se considera potencialmente hostil; launcher, VM, kernel e
hipervisor son la base confiable; no se considera adversarial el control de esa
base ni la inyección deliberada de capacidades externas por la infraestructura.
Las capacidades externas no declaradas no deben quedar disponibles por vías
alternativas. La contención requerida debe probarse mediante bloqueo efectivo o
evidencia suficiente de observación/atribución. Los estados `OBSERVED`,
`BLOCKED` y `UNKNOWN` conservan los significados de la adjudicación vigente;
`UNKNOWN` no se cierra por ausencia, extrapolación ni inferencia.

### Qué debe demostrar A-PRE-0

A-PRE-0 califica **el instrumento y el perímetro de ejecución**, no los efectos
de TALOS. Sin importar, recolectar ni ejecutar TALOS, debe demostrar mediante
inspección reproducible y fixtures sintéticos que:

1. El snapshot/perímetro, runtime, lock, plataforma y alcance requerido están
   identificados por hashes/manifest y no cambian durante la calificación.
2. El launcher instala obligatoriamente la política y los mounts declarados;
   las capacidades externas no declaradas no entran por filesystem, FD
   heredado, socket conectado, mapping u otro canal requerido por el inventario.
3. Para **cada mecanismo requerido** por el Modelo B y el inventario estático
   fijado al snapshot, se ha demostrado una ruta completa de decisión:
   - una operación positiva sintética permitida produce evidencia atribuible
     suficiente (`OBSERVED`), o
   - una operación sintética no permitida queda impedida por una barrera activa
     (`BLOCKED`), correlacionada con política, recurso y resultado.
   Cuando ambos comportamientos sean relevantes, se necesitan ambos
   controles. Un fixture de syscall exitosa no cierra por sí solo una familia
   con vías alternativas conocidas.
4. Los mecanismos sin cobertura suficiente conservan `UNKNOWN`; los errores de
   sensor, truncamiento, FD/path/peer no resuelto, arquitectura no soportada,
   divergencia de política, evidencia incompleta o artefacto inválido impiden
   el resultado satisfactorio.
5. Collector, builder y verifier independiente concuerdan en el contrato,
   rechazan estados falsos `OBSERVED`/`BLOCKED`, y nunca transforman `UNKNOWN`
   en `PASS` o `NONE`.

Los subcasos previamente medidos (io_uring/Linux AIO, FD regular, `MAP_SHARED`,
AF_UNIX y rutas por pathname) son evidencia de esos subcasos solamente. No
excluyen `UNKNOWN` en otras vías, clases de descriptor o mecanismos.

### Predicate exacto de A-PRE-0 READY

`A_PRE_0_READY` es verdadero si y solo si se satisfacen **todas** estas
condiciones con evidencia persistida, verificable e identificada con el mismo
snapshot:

```text
A_PRE_0_READY =
    snapshot_identity_verified
  AND runtime_lock_platform_verified
  AND target_kernel_and_syscall_table_identity_verified
  AND compatibility_ABIs_explicitly_included_or_excluded
  AND perimeter_and_threat_model_frozen
  AND required_mechanism_inventory_frozen
  AND launcher_boundary_and_policy_verified
  AND trace_integrity_and_sensor_fail_closed_verified
  AND collector_builder_independent_verifier_verified
  AND for_every_required_mechanism(
        required_path_inventory_frozen
        AND every_required_case_status IN {OBSERVED, BLOCKED}
        AND alternative_paths_accounted_for
        AND evidence_matches_snapshot_policy_resource_and_process
      )
  AND sensor_requirements_qualified_without_auxiliary_telemetry_as_surface_coverage
  AND launcher_descriptor_hygiene_at_entry_verified
  AND no_required_case_or_path_is_UNKNOWN
  AND no_required_evidence_is_missing_invalid_or_contradictory
  AND talos_execution_or_collection_during_A_PRE_0_qualification == 0
```

Los estados de cada caso en este predicate se refieren a la calificación
sintética del mecanismo/instrumento en A-PRE-0; no equivalen a declarar que el
workload real produjo ese efecto. Deben representarse en un ledger indexado por
mecanismo y vía/caso, separado del `effect_coverage` del resultado de una
ejecución. Un caso `OBSERVED` solo cubre el alcance expresamente demostrado; si
queda una vía requerida sin observación ni bloqueo probado, esa vía es
`UNKNOWN` y el predicate es falso.

### Ledger de calificación y verificación independiente

La propuesta de inventario canónico está materializada en
[`A_PRE_0_SURFACE_MANIFEST.json`](./A_PRE_0_SURFACE_MANIFEST.json), y el
registro separado de calificación en
[`A_PRE_0_QUALIFICATION_LEDGER.json`](./A_PRE_0_QUALIFICATION_LEDGER.json).
El manifiesto separa superficies del workload, requisitos de sensor,
controles y relaciones. Sustituye la agrupación de mecanismos de las 17 filas
históricas sin borrar su evidencia ni sus adjudicaciones acotadas. La antigua
fila `sys.addaudithook` se conserva como requisito de telemetría auxiliar, no
como superficie del workload. Los probes con FD regular o socket AF_UNIX
deliberadamente inyectado se clasifican como controles de sensibilidad del
sensor; no son prueba de que el launcher normal entregue esas capacidades.
La obligación de Modelo B es la higiene de descriptores del launcher en el
ingreso al sandbox y sigue `UNKNOWN` fuera de los casos negativos medidos.

La identidad declarada sigue siendo Linux x86_64, Ubuntu 26.04 LTS, kernel
`7.0.0-34-generic`, ABI nativa x86_64. Sin embargo, la inspección local de
solo lectura encontró Linux Mint 22.3 (Zena), base Ubuntu Noble 24.04, y
paquetes instalados `linux-image-7.0.0-34-generic`,
`linux-modules-7.0.0-34-generic` y
`linux-headers-7.0.0-34-generic`, todos versión
`7.0.0-34.34~24.04.1`. El binario imagen declara fuente
`linux-signed-hwe-7.0`; módulos y headers declaran `linux-hwe-7.0`.
`uname -r` coincide con el nombre de kernel declarado, pero distribución y
build no coinciden con el perfil Resolute. **No se sustituye el target
documental**: esta discrepancia impide declarar la fuente observada como la
normativa del target hasta una decisión humana.

La designación de la VM es `fadena-lab`; el checkpoint 001 distingue
`agustin-desktop`/Linux Mint como otra máquina. Una captura nueva de solo
lectura por SSH, identificador
`A-PRE0-SYSCALL-TABLE-20261001-01`, registró `fadena-lab`, Ubuntu 26.04 LTS
(Resolute), `x86_64`, `uname` `7.0.0-34-generic`, arquitectura dpkg `amd64` y
paquetes instalados `linux-image-7.0.0-34-generic`,
`linux-modules-7.0.0-34-generic` y `linux-headers-7.0.0-34-generic`, todos
`7.0.0-34.34`. Los dos últimos identifican como fuente `linux 7.0.0-34.34`;
la imagen identifica `linux-signed` de la misma versión.

Se descargaron localmente del endpoint de archivos fuente de Launchpad el
descriptor `linux_7.0.0-34.34.dsc` (7,787 bytes, SHA-256
`03239d912d2204cee96216f4006d654ec3d9b4d8882488ca9200c26196c641fc`), el
upstream `linux_7.0.0.orig.tar.gz` (254,937,830 bytes, SHA-256
`c6343795c8c7e4feff55f5b309365c8e0eaf49cd6abcb412e32315313f149536`) y la
delta Ubuntu `linux_7.0.0-34.34.diff.gz` (2,451,375 bytes, SHA-256
`9627f3f544b518adf1b9cb3eac9895398303018948b34fbd7b9b194ef3019cc1`). Los
tres hashes locales coinciden con los checksums publicados por Launchpad. No
se verificó la firma OpenPGP del descriptor. Se extrajo por streaming el
miembro upstream `linux-7.0/arch/x86/entry/syscalls/syscall_64.tbl`; la delta
Ubuntu no contiene parche para esa ruta. Su SHA-256 es
`93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.

Ese hash coincide con el hash registrado para la tabla que alimentó las 385
filas. Por identidad de contenido, el registro se conserva y se reutiliza sin
re-enumeración, ahora vinculado a la fuente del kernel de la VM designada; no
se infiere que la adquisición histórica Mint/Noble fuera ejecutada en esa VM.
La adquisición Mint/Noble previa queda preservada como evidencia auxiliar no
atribuida. El header UAPI instalado desde
`linux-headers-7.0.0-34-generic 7.0.0-34.34` tiene SHA-256
`fb345c85da52add8c7eb5b64274a8d8282975f0a3dd33f9aa172d4be8e95070a`.

La cadena de fuente observada es `linux-hwe-7.0 7.0.0-34.34~24.04.1` →
`linux-image-unsigned-7.0.0-34-generic` de la misma versión →
`linux-signed-hwe-7.0` de la misma versión. La metadata dpkg local confirma
imagen, módulos y headers instalados en esa versión; el `.dsc` de Launchpad
confirma la relación exacta de build. Los artefactos fuente se descargaron
temporalmente y sus SHA-256 locales coincidieron con los publicados:

| Artefacto | Tamaño | SHA-256 publicado y verificado localmente |
|---|---:|---|
| `linux-hwe-7.0_7.0.0-34.34~24.04.1.dsc` | 8,121 bytes | `e9cc83d88922aecea0a7c1d170539baab02d4aa431ce184a867aac7a2ba2b88f` |
| `linux-hwe-7.0_7.0.0.orig.tar.gz` | 254,937,830 bytes | `c6343795c8c7e4feff55f5b309365c8e0eaf49cd6abcb412e32315313f149536` |
| `linux-hwe-7.0_7.0.0-34.34~24.04.1.diff.gz` | 2,455,837 bytes | `81b9d83f6863ea9d41bde191923134fe6bf4261bfcf94a376b85c094fafd6c32` |
| `linux-signed-hwe-7.0_7.0.0-34.34~24.04.1.dsc` | 2.7 KiB | `6c390b22c14288b1d05aff0714419b49abdb717a9b67504c39326ca091f81c1f` (publicado) |
| `linux-signed-hwe-7.0_7.0.0-34.34~24.04.1.tar.xz` | 13,612 bytes | `f5b7be51b8ddef58218ce007cc8ebf30ec82458aff517e3416fb6dea12f71160` (publicado) |

Fuentes: los listados oficiales de
[Launchpad/linux-hwe-7.0](https://launchpad.net/ubuntu/+source/linux-hwe-7.0/7.0.0-34.34~24.04.1/+files)
y [Launchpad/linux-signed-hwe-7.0](https://launchpad.net/ubuntu/+source/linux-signed-hwe-7.0/7.0.0-34.34~24.04.1/+files).
Los dos artefactos `linux-signed-hwe-7.0` se registran con checksum publicado;
no se descargaron para esta revisión. El `.dsc` del source kernel incluye
firma OpenPGP, pero `dpkg-source`/`gpgv` no la verificó porque no hay una clave
pública aceptable instalada. La fuente fue extraída; no se compiló ni ejecutó.

El archivo Ubuntu aplicado
`arch/x86/entry/syscalls/syscall_64.tbl` tiene SHA-256 local
`93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`, igual al
hash de ese archivo en el tarball upstream. La comparación byte a byte no
encontró delta Ubuntu en la tabla. El archivo UAPI generado instalado
`/usr/src/linux-headers-7.0.0-34-generic/arch/x86/include/generated/uapi/asm/unistd_64.h`
pertenece al paquete de headers de la misma versión/source y tiene SHA-256
`fb345c85da52add8c7eb5b64274a8d8282975f0a3dd33f9aa172d4be8e95070a`.
La tabla contiene 443 líneas físicas y 421 entradas en total: 338 `common`,
47 `64` y 36 `x32`. La tabla native x86_64 queda enumerada como las 385 filas
`common` + `64`; las 36 x32 quedan excluidas según la decisión de alcance.

El manifiesto registra una fila explícita por cada una de esas 385 syscalls.
**Las 385 están `UNKNOWN`; cero tienen disposición final.** En 191 filas se
anotan memberships de superficie candidatas sin aprobar; 194 no tienen aún
superficie candidata. Los 191 nombres syscall de las listas de superficie
existentes aparecen en la tabla native, pero esa coincidencia no cierra
ninguna fila. Esto satisface la enumeración 1:1 sin fingir clasificación.
`inventory.frozen=false` sigue vigente por las disposiciones pendientes, las
particiones finitas y la trazabilidad. La identidad de la tabla target ya no
es un bloqueo: la evidencia fuente nueva queda ligada a `fadena-lab`, y el
registro anterior coincide byte a byte por SHA-256.

### Cruce estático 1:1 de syscalls

Cada una de las 385 filas del registro tiene ahora un `static_disposition_review`
con: estado `UNKNOWN`; la candidatura de superficie (191 filas) o la ausencia
de candidata (194 filas); recurso y ejes de variante declarados por las
superficies; referencias de variante y rutas alternativas relacionadas;
evidencia disponible (presencia de la entrada en la tabla target-bound); y
requisitos específicos que faltan para cerrar esa fila. El hash de tabla
referenciado es
`93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.

Este cruce es una clasificación documental del registro, no una disposición
final de efectos: la pertenencia candidata no demuestra que la syscall pueda
ser invocada por el workload bajo una variante concreta, que se haya observado
un efecto o que una política la bloquee. Ninguna fila pasa a `OBSERVED` o
`BLOCKED`; no se añade evidencia runtime. Permanecen pendientes la adjudicación
de cada relación o exclusión, las particiones finitas argumento/recurso,
callsite → dependencia/extensión nativa → syscall y evidencia técnica
correlacionada. Las filas sin candidata requieren asignación justificada o
exclusión explícita; no se fuerza una superficie por el nombre syscall.

Las particiones de variantes siguen `PARTIAL_UNKNOWN`. Se fijaron los ejes
documentales pendientes, sin inferir cobertura: `mmap` (objeto/FD, shared vs
private, anonymous, protections, placement y lifecycle); `clone`/`clone3`
(proceso/hilo, flags, namespaces, versión/tamaño de `clone_args`, pidfd/set_tid/
cgroup y fase); sockets (family/type/protocol/operación/ancillary data);
`fcntl` (comando y clase de FD); `ioctl` (request y clase de objeto);
mount/namespaces (API, flags, recursos y fase); y `seccomp`/`prctl`
(operación, flags, herencia y transición efectiva). No están enumerados los
conjuntos finitos de valores y combinaciones. Todo selector no enumerado
continúa `UNKNOWN`; default-deny de `ioctl`, `bpf`, `perf_event_open` y
`userfaultfd` sigue siendo intención normativa, no denegación demostrada.
`ioctl(FIONREAD)` es solo sensibilidad del sensor; no hay operación ioctl
admitida al workload.

La trazabilidad Python → nativo → syscall sigue en nivel de familia candidata,
no de callsite. El AST v4 no proporciona un mapeo completo desde cada callsite
del snapshot exacto, pasando por versiones precisas de CPython/libc/extensiones/
dependencias, hasta una fila de tabla y partición de argumentos. Dispatch
dinámico, efectos transitivos, ctypes/cffi, callbacks y extensiones nativas
arbitrarias se mantienen `UNKNOWN`. `STATIC_CANDIDATE` no es evidencia de
ejecución, ausencia ni cobertura.

El manifiesto enumera nombres de syscalls, no wrappers de biblioteca: en
x86_64 `send()`/`recv()` no son entradas independientes de la tabla syscall;
sus operaciones se atribuyen a llamadas como `sendto`, `recvfrom`, `sendmsg` o
`recvmsg`, según corresponda. Las llamadas compartidas entre superficies (por
ejemplo `clone` y `execve`) tienen relaciones explícitas, no comodines.

El ledger mantiene 16 superficies de workload: 2 están `BLOCKED` únicamente
para las llamadas async enumeradas bajo el perfil esperado, y 14 permanecen
`UNKNOWN`, aunque algunas tengan subcasos sintéticos `OBSERVED` o `BLOCKED`.
El sensor Python `sys.addaudithook` tiene estado propio `PARTIAL` y no puede
cerrar ninguna superficie nativa. Ninguna referencia histórica es actualmente
elegible para satisfacer readiness porque el overlay v4 calificado no
contiene la revisión normativa de esta especificación ni la identidad del
manifiesto propuesto.

Cada superficie requerida lleva un estado agregado, casos con estado individual
(`OBSERVED`, `BLOCKED` o `UNKNOWN`), referencias de evidencia con hash y
alcance, más vías requeridas aún no calificadas. Una vía sin cierre se
representa explícitamente como `UNKNOWN`; no se elimina del inventario ni se
oculta tras un caso positivo. El estado agregado de una superficie es
`OBSERVED` o `BLOCKED` solamente si todas sus vías requeridas tienen un estado
admisible, evidencia válida y sin contradicción; si no, su agregado es
`UNKNOWN`.
Una familia puede contener casos positivos y negativos sin que ello implique
que la familia completa esté cerrada.

El manifiesto contiene 16 superficies canónicas y un grafo explícito de
relaciones: S05/S06 se separan por objeto respaldante (archivo frente a
memoria anónima/memfd); S08/S09 separan el endpoint AF_UNIX del paso de
capacidades SCM_RIGHTS; S10 conserva IPC clásico, memoria compartida y
coordinación sin confundirlos con transferencia de FD; S03 representa ciclo
de vida/ingreso de descriptores; y S11/S16 distinguen seguimiento de procesos
de cambios de aislamiento/privilegio. Una syscall que aparece en más de una
semántica se define canónicamente en las superficies indicadas por el grafo,
sin borrar las relaciones alternativas.

`workload_surfaces`, `sensor_requirements` y controles tienen contratos y
estados distintos. La superficie usa `OBSERVED`/`BLOCKED`/`UNKNOWN`; el estado
del sensor usa `QUALIFIED`/`PARTIAL`/`UNQUALIFIED` y su categoría puede ser
`AUXILIARY_ONLY`; un control describe una barrera y su estado de evidencia, no
una propiedad inferida de la existencia de una regla. El estado `PARTIAL` de
`sys.addaudithook` solo
documenta telemetría Python auxiliar y nunca cierra una superficie nativa.
Los casos de inyección deliberada deben etiquetarse
`test_purpose=sensor_sensitivity`; el verificador no puede contarlos como
evidencia de contención del launcher.

El control requerido de descriptores en Modelo B es
`C-LAUNCHER-FD-HYGIENE`: al entrar al sandbox, el launcher solo conserva los
FDs declarados y hace inaccesibles los demás. La evidencia negativa existente
prueba un FD regular en una ruta concreta, no la propiedad general. El control
positivo de FD/socket inyectado calibra sensibilidad/atribución del sensor y
no redefine al adversario de Modelo B ni acredita la higiene normal del
launcher.

### Identidad de ABI, unidades de cobertura y trazabilidad estática

El alcance propuesto es **Linux x86_64 con ABI nativa x86_64 únicamente**.
`x32` e i386 compat quedan explícitamente fuera de este manifiesto: no son
parte del runtime objetivo que se pretende calificar. Esta exclusión define el
alcance; no afirma que el launcher ya impida esos ejecutables. La calificación
deberá demostrar que el launcher rechaza ambas ABI alternativas, o incorporar
cada una como ABI separada en una revisión versionada antes de atribuirle
cobertura. Una arquitectura/ABI observada distinta de la declarada falla
cerrado.

La identidad declarada y capturada de `fadena-lab` es Ubuntu 26.04 LTS
(Resolute), kernel `7.0.0-34-generic`, paquete `linux 7.0.0-34.34`. La
observación previa Mint 22.3/Noble con HWE
`7.0.0-34.34~24.04.1` carece de atribución de hostname/sesión y permanece
separada como evidencia auxiliar. No se transfirió su identidad: una nueva
adquisición del source exacto Resolute produjo el mismo SHA-256 de tabla que
el registro existente, habilitando su reutilización por identidad de bytes.
La tabla target tiene 385 entradas nativas `common`/`64` y 36 x32 excluidas;
cada fila nativa permanece `UNKNOWN`. La ausencia de una llamada solo puede
registrarse `NOT_APPLICABLE` si la tabla exacta bound al target demuestra la
ausencia.

Una unidad de cobertura es la tupla:

```text
(surface_id, syscall_or_library_interface, ABI,
 argument_or_flag_partition, resource_or_capability_class,
 execution_phase, outcome_class)
```

Se crea una unidad distinta cuando cambia el significado de seguridad o la
capacidad de observar/denegar: por ejemplo, `mmap` con backing file frente a
`MAP_ANONYMOUS`, `socket` con AF_INET frente a AF_UNIX, `sendmsg` con
`SCM_RIGHTS` frente a datos ordinarios, `ioctl` con comando específico, o
`clone` durante bootstrap frente a un `clone` del workload que pide namespaces.
El manifiesto debe enumerar para cada unidad el selector, valores incluidos,
valores excluidos y razón, clase de recurso, fase, rutas alternativas y
criterio de cierre. Un valor no enumerado es `UNKNOWN`; no se agrupa en una
categoría “otros” que pueda pasar silenciosamente.

Las syscalls se definen canónicamente una sola vez; cuando una syscall
participa en varias superficies (p. ej. `clone`, `execve`, `mmap` o
`sendmsg`), el grafo de relaciones vincula esas unidades sin duplicar ni
eliminar su cobertura. En APIs opacas la propuesta es no admitir operaciones:
`ioctl`, `bpf`, `perf_event_open` y `userfaultfd` quedan default-deny para el
workload. `FIONREAD` solo figura como subcaso sintético de calibración del
sensor, no como operación permitida. Esa intención no es `BLOCKED`: se requiere
evidencia posterior de política cargada y denegación correlacionada. Seccomp
no puede, por sí solo, vincular un número de FD a un tipo de objeto ni
inspeccionar estructuras apuntadas; no se aceptará una allowlist que dependa
de esas propiedades salvo que otra barrera las demuestre.

La trazabilidad Python→nativo→syscall del manifiesto es una **preclasificación
por familias de API**, no un call graph ni evidencia de ejecución. Se apoya en
el inventario AST estático de la copia v4: 456 módulos parseados, con 350
candidatos de mutación de filesystem, 126 de lectura de filesystem, 65 de
`open`, 13 de procesos y cero coincidencias para los nombres de red que ese
scanner reconoce. Las categorías se solapan; cero coincidencias no prueba
ausencia de red. Ese scan no resuelve dispatch dinámico, tipos de receiver,
wrappers de libc, código transitivo, dependencias nativas o callbacks.

El mapa candidato del manifiesto relaciona `open`/`io`/`pathlib` con `_io`,
`os` y S01–S03; mutaciones `os.*` con S04; `mmap` con S05/S06; `socket` con
S07–S09; `subprocess` y `os.exec*` con S03/S11/S16; y threading/multiprocessing
con S10/S11. Para cada ruta los syscalls candidatos dependen de la versión de
CPython, libc, kernel y dependencias. `ctypes`, `cffi`, extensiones C,
callbacks y bibliotecas cargadas dinámicamente permanecen `UNKNOWN` salvo que
se mapeen estáticamente en el snapshot. Antes de congelar se necesita
reconciliar los candidatos por sitio y las entradas nativas/dependencias con
las superficies; el inventario agregado no permite afirmar que la relación
esté completa.

El cierre del inventario requiere además adjudicar estáticamente cada entrada
de la tabla nativa x86_64 fijada: asignarla a una o más superficies canónicas,
o excluirla con una justificación Modelo B que indique qué clases de efecto no
puede alcanzar. Una syscall nueva en una tabla/kernel futuro, o una llamada
sin disposición, invalida la identidad del manifiesto y queda `UNKNOWN` hasta
una revisión versionada. Esta regla establece una frontera finita y evita
ampliaciones ad hoc durante los probes.

Por tanto, la exclusión explícita de ABI ya está definida, pero no está
calificada; la definición de unidades y la trazabilidad aportan un contrato
revisable, no exhaustividad. Siguen bloqueando el congelamiento la identidad
exacta del source/table syscall, la disposición de cada syscall de esa tabla,
la reconciliación del mapa por sitio y la especificación finita de algunas
particiones de argumentos/fases. Mantener
`inventory.frozen=false` hasta resolverlos documentalmente. Congelar el
inventario no requiere cerrar `UNKNOWN` de calificación y nunca cambia por sí
solo A-PRE-0 a READY.

Un verificador independiente del emisor debe reconstruir la decisión desde el
manifiesto, el ledger y los artefactos (sin importar TALOS) y rechazar, como
mínimo: superficies o casos omitidos; inventario no congelado; ABI o tabla de
syscalls sin identidad; exclusión de x32/i386 sin enforcement calificado;
syscall sin disposición; `UNKNOWN`; hashes ausentes/incorrectos; identidad de
snapshot, plataforma, modelo de amenaza o política divergente; telemetría
auxiliar contada como cobertura; control de sensibilidad contado como
contención; contradicción entre controles; estado
`OBSERVED` sin operación/recurso/PID/
resultado atribuibles; estado `BLOCKED` sin política activa y denegación
correlacionada; trace incompleto o fallo de sensor; y schema/version
desconocido. La implementación debe tener pruebas de mutación que introduzcan
cada defecto por separado y demuestren `A_PRE_0_READY=false`, además de un
ledger enteramente sintético válido que ejercite la rama positiva del
verificador sin calificar el snapshot real. La implementación y esas pruebas
siguen pendientes; no se afirma que el predicate ya haya sido implementado ni
validado independientemente.

El `effect_coverage_qualification_passes()` actual evalúa un artefacto de
aislamiento y exige `complete=true`, estado agregado `OBSERVED` o `BLOCKED` y
política seccomp válida; hoy el harness emite cobertura agregada
`UNKNOWN`/`complete=false`, por lo que ese predicate devuelve falso. No debe
reinterpretarse para afirmar readiness. La separación mecánica entre el ledger
de calificación A-PRE-0 y la cobertura por ejecución debe implementarse y
probarse antes de poder satisfacer el predicate anterior.

`A_PRE_0_READY` solo significa **instrumento calificado para solicitar una
decisión de autorización A-PRE-1**. No ejecuta ni autoriza automáticamente
A-PRE-1, no declara que TALOS sea estéril y no predice el resultado de sus
efectos.

Esta reconciliación modifica la especificación del checkout fuente
`rev4-clean`; no modifica retroactivamente el overlay v4 ni su evidencia. Una
calificación posterior bajo este predicate deberá incluir la especificación
revisada en la identidad del snapshot que efectivamente se califique.

### Evidencia reservada a A-PRE-1 y condiciones NOT READY

Solo A-PRE-1 puede aportar la evidencia de qué casos se recolectaron, qué
efectos concretos produjo el workload, qué destinos/FDs usó en esa ejecución y
si esos efectos fueron `REAL`, `TEMPORARY`, `MOCKED`, `INDIRECT`, `NONE` o
`UNKNOWN`. Esa adjudicación no es una precondición de A-PRE-0 y exigirla antes
de la primera ejecución sería circular. A-PRE-0 sí es precondición de readiness
del instrumento y debe preceder cualquier solicitud de autorización A-PRE-1.

A-PRE-0 permanece `NOT READY` si falla cualquier término del predicate,
incluyendo, sin limitarse a:

- inventario requerido no congelado o un mecanismo relevante omitido/sin
  justificación;
- política default-allow o launcher no demostrado para un mecanismo requerido;
- cualquier mecanismo requerido `UNKNOWN`, incluso cuando otros subcasos
  estén `OBSERVED` o `BLOCKED`;
- cobertura de sensor incompleta, resultado contradictorio o fallo que no
  produzca rechazo;
- builder/verifier que acepte `UNKNOWN`, datos incompletos o falsa evidencia;
- falta de identidad, hash, artefacto reproducible o vinculación a la política
  activa.

En A-PRE-1, cualquier efecto requerido `UNKNOWN`, traza incompleta, política
inválida, discrepancia de integridad o fallo de verificación impide `PASS`.
`UNKNOWN` no se convierte por sí solo en `FAIL` semántico del workload, pero
sí bloquea `PASS` y la liberación hasta su resolución explícita. No se permite
degradarlo a `NONE`, `OBSERVED` o `BLOCKED` por inferencia.

## 5. Registro de salida

A-PRE-1 debe conservar fuera del checkout, como mínimo, un `result.json`
conforme a este contrato:

```json
{
  "schema_version": 1,
  "run_id": "unique-id",
  "global_status": "PASS | FAIL | ERROR",
  "started_at": "RFC3339 timestamp",
  "duration_seconds": 0,
  "identity": {
    "repository": "owner/name",
    "branch": "branch",
    "commit": "full-sha",
    "working_tree_clean": true,
    "working_tree_diff_sha256": "sha256-of-empty-diff",
    "platform": "OS/architecture/kernel"
  },
  "runtime": {
    "python_executable": "absolute path",
    "python_version": "3.10.x",
    "uv_version": "version",
    "input_hashes": {
      "pyproject.toml": "sha256",
      "requirements.lock": "sha256",
      "config/test_perimeter.json": "sha256",
      "scripts/quality_gate.py": "sha256",
      "scripts/apre_result.py": "sha256",
      "scripts/verify_apre_result.py": "sha256"
    }
  },
  "command": ["python", "scripts/quality_gate.py", "--profile", "release"],
  "profile": "release",
  "exit_code": 0,
  "collections": {
    "collected": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "collection_errors": 0
  },
  "suites": [
    {
      "path": "tests/example",
      "classification": "required",
      "status": "PASS | FAIL | SKIP | WARNING | ERROR",
      "collected": 0,
      "passed": 0,
      "failed": 0,
      "skipped": 0,
      "collection_errors": 0,
      "skip_reasons": [],
      "duration_seconds": 0,
      "warnings": [],
      "errors": []
    }
  ],
  "optional_modules": [{"path": "tests/example.py", "status": "SKIP", "reason": "manifest reason"}],
  "artifacts": [{"path": "relative-to-evidence-dir", "sha256": "sha256"}],
  "sterility": {
    "before_state_sha256": "sha256",
    "after_state_sha256": "sha256",
    "unexpected_changes": []
  },
  "warnings": [],
  "errors": []
}
```

El ejemplo define nombres y tipos; los valores marcadores no son resultados
reales. Las rutas de artefactos son relativas al directorio de evidencia y no
pueden apuntar fuera de él. El emisor/verificador de este contrato está
implementado en [`scripts/apre_result.py`](../scripts/apre_result.py) y
[`scripts/verify_apre_result.py`](../scripts/verify_apre_result.py), con catorce
tests de fixtures en
[`tests/audit/test_apre_result.py`](../tests/audit/test_apre_result.py). El
emisor valida y escribe un objeto de reporte proporcionado; las pruebas
parsean ese artefacto con el CLI y verifican rechazo de corrupción,
incompletitud y mutaciones. El CLI contiene una implementación separada, no
importa ni invoca la validación del emisor. El harness transforma el collector
del gate en un `result.json` completo, agrega identidad/runtime/hashes,
stdout/stderr, observer, trazas, aislamiento y fingerprints del snapshot, y
ejecuta el CLI verifier independiente. Las fixtures de harness prueban el
formato serializado y fuerzan `ERROR` cuando la cobertura de syscalls es
incompleta; no generan un resultado PRE de TALOS.

A-PRE-1 conservará, además del `result.json`:

- stdout/stderr íntegros, exit code y duración total y por suite;
- estado, conteos recolectados/pasados/fallidos/skipped/error por suite;
- warnings, skips y razones explícitas; fallos de importación/colección;
- hash de cada artefacto y resultado de la comprobación de esterilidad antes/
  después.

Para suites ejecutables, `PASS` significa que se recolectó al menos un caso
sin skips, fallos ni errores de colección; `WARNING` significa que los casos
no fallaron, pero hay skips individuales acompañados por razones explícitas.
`FAIL` es una assertion fallida; `ERROR` indica colección fallida, evidencia
inválida, entorno/herramienta incorrectos o contaminación. `SKIP` solo se usa
para suites `support-only` y módulos/suites excluidos por el perfil, siempre
con motivo. Cada suite debe satisfacer
`collected = passed + failed + skipped`; `collection_errors` se registra aparte.
Los skips no forman parte de `passed`.

La agregación es determinista: global `ERROR` prevalece ante integridad de
evidencia, entorno, herramienta, colección o esterilidad inválidos; en su
ausencia, global `FAIL` si algún test falla o una suite activa tiene un skip
sin excepción permitida; en su ausencia, global `PASS`. Warnings no cambian el
status global, pero deben aparecer en ambas ubicaciones (`suites[].warnings`
cuando aplica y `warnings` global). Suite `optional` o `support-only` recibe
`SKIP` con razón; una suite `qualification-required` cuenta como activa en
perfil release. El status global no puede ser `PASS` si falta cualquier suite
activa o no se ejecutó ningún caso de una suite activa.

`scripts/test.sh` elige primero `$REPOSITORY_ROOT/.venv/bin/python`, por lo que
en el checkout actual usarlo activaría Python 3.12 aunque exista el runtime
3.10 temporal. A-PRE-1 invocará el gate directamente con el intérprete aislado:
`<PRE_VENV>/bin/python scripts/quality_gate.py --profile release`. Esto conserva
el mismo validador/perfil release y evita modificar el wrapper general o usar
el `.venv` actual. Un wrapper externo capturará el reporte, añadirá métricas y
esterilidad y producirá el JSON anterior sin escribir en el checkout.

## 6. Comparabilidad PRE → POST

Una comparación directa solo es válida cuando ambos registros coinciden en:

1. manifiesto/perfil, suites seleccionadas, overrides, reglas de colección y
   definición de los estados;
2. versión de Python, lock y hashes de inputs de dependencias, plataforma y
   condiciones relevantes;
3. comando, flags, variables de entorno controladas y política de artefactos;
4. formato/schema del reporte y tratamiento de skips, warnings y errores.

Cada ejecución registra su propio commit, árbol y hashes; el código fuente
puede diferir intencionalmente entre PRE y POST y se compara como el cambio
evaluado, no como requisito de igualdad. Cualquier diferencia no prevista en
los puntos 1–4 marca la pareja `NOT DIRECTLY COMPARABLE`; no se normaliza ni se
compensa retrospectivamente. Cambio de runtime, lock, perímetro o criterios
requiere baseline nueva o un análisis separado. Los resultados de PRE y POST
deben mantenerse inmutables y enlazados por identificador de comparación.

## Revisión de preflight A-PRE-0

| Pregunta | Resultado | Evidencia / pendiente |
|---|---|---|
| Runtime candidato viable | `PASS FOR LOCKED DEPENDENCIES` | CPython 3.10.21 con uv 0.12.20; 61 paquetes instalados en venv temporal; `uv pip check` y dependency imports pasaron. No se importó TALOS ni se recolectaron sus suites; quedan para el gate de ejecución autorizado. |
| Perímetro internamente consistente | `PASS` | 25 suites = 22 required + 2 qualification-required + 1 support-only; 456 archivos = 440 required + 13 qualification-required + 2 optional + 1 support-only. Validador estático pasó sin ejecutar suites. |
| Salidas del PRE definidas | `RUNNER + INDEPENDENT CLI FIXTURE-TESTED` | 14 pruebas de reporter, 6 de observer y 33 pruebas sintéticas focalizadas de harness/builder/verifier pasan bajo CPython 3.10.21. Se valida el rechazo de trazas incompletas y de falsos `BLOCKED`; no se generó resultado TALOS. |
| Efectos laterales | `OS FIXTURES PASS; SYSCALL CAPTURE FIXTURE-PASS; ASYNC FAMILIES BLOCKED; A-PRE-0 INSTRUMENT QUALIFICATION INCOMPLETE` | Bubblewrap contiene fixtures sintéticas y el perfil seccomp obligatorio `a-pre-native-async-deny-v1` bloquea nueve syscalls de io_uring/Linux AIO con `EPERM`. Los probes posteriores también observaron subcasos de FD regular, `MAP_SHARED` y AF_UNIX inyectados, y el rechazo de path/FD no pasado por el launcher. No cierran esas familias: observer nativo incompleto, stores de CPU no observables por syscall, APIs opacas, IPC general, namespaces/credenciales/seccomp y otros canales siguen pendientes. |
| Snapshot | `EXACT ISOLATED OVERLAY; SYNTHETIC TESTS + AST PRE-SCREEN VERIFIED` | La identidad vigente del overlay derivado de `a04aa3630521ad21027d38b2e3ac3b83bb0fca3d`, sus nueve paths modificados y el inventario AST se registran en el informe externo de identidad vigente. No es una baseline PRE limpia ni autoriza A-PRE-1. |
| Límites y exclusiones | `PASS WITH PRECONDITION` | E5/Qwen, blind pool, BENCH-G2, NotebookLM, producción, providers reales y migraciones excluidos. Sin acceso a datos no puede certificarse esterilidad solo desde la especificación. |

**Resultado del preflight:** `REVIEW REQUIRED / NOT READY FOR A-PRE-1`.
Runtime, perímetro, reporter, observer y harness tienen las validaciones
enumeradas arriba; los probes sintéticos adicionales no ejecutaron TALOS. Sin
embargo, `A_PRE_0_READY=false`: la matriz mantiene mecanismos requeridos en
`UNKNOWN`, el observer declara `native_syscalls=false`/`complete=false` y aún
no existe un ledger separado que satisfaga el predicate de calificación del
instrumento. Esto impide declarar que el instrumento está listo; no se debe
confundir con la adjudicación de efectos de una ejecución TALOS, que solo puede
producirse durante A-PRE-1. La ausencia de resultados reales A-PRE-1 no bloquea
por sí misma A-PRE-0; sí la bloquea cualquier incertidumbre sobre la capacidad
del instrumento para observar/atribuir o impedir los mecanismos requeridos.
No ejecutar imports, colección ni suites TALOS por adelantado, ni autorizar
A-PRE-1 mientras el predicate A-PRE-0 sea falso.

## Gate de salida A-PRE-0

- **Predicate normativo:** véase §4.1. Es una conjunción necesaria y
  suficiente; el estado actual es `false`.
- **Validación realizada:** inspección estática, validación del perímetro,
  resolución e instalación de 61 paquetes con uv 0.12.20 en venv temporal,
  `uv pip check`, imports smoke de dependencias, 14 fixtures del
  emisor/verificador, 6 fixtures de observer y 6 fixtures de harness (26
  pruebas en total); probes bubblewrap para filesystem/red/SQLite/proceso; no
  se ejecutó suite
  de TALOS, no se recolectaron suites y no se invocó `scripts/test.sh`.
- **Pendiente para que A-PRE-0 pueda ser READY:** congelar el inventario
  requerido según Modelo B; calificar cada mecanismo mediante el ledger
  sintético separado; resolver los `UNKNOWN` de instrumento/contención;
  implementar y verificar la separación entre ese ledger y
  `effect_coverage` por ejecución; preservar rechazo independiente de
  resultados incompletos o `UNKNOWN`.
- **Reservado a A-PRE-1:** imports, colección y ejecución autorizada de TALOS,
  además de la adjudicación de sus efectos reales por caso. Estos resultados
  no se anticipan ni se exigen para calificar el instrumento en A-PRE-0.
- **Autorización:** `PENDING / NOT AUTHORIZED`. Este documento no es una
  autorización ni un resultado PRE; E5/Qwen, producción, DB/corpus y blind pool
  continúan intactos y fuera de ejecución.

## Adjudicación documental de casos históricos por syscall

El manifiesto registra ahora 27 resultados históricos acotados en 17 filas
individuales del universo nativo de 385 syscalls: 16 casos `OBSERVED` y 11
`BLOCKED`. Estos son estados de **caso/variante/ruta**, no disposiciones de la
fila syscall completa. Las 385 filas conservan `disposition_status=UNKNOWN`;
ninguna de estas anotaciones cambia `inventory.frozen=false`, A-PRE-0
`NOT READY` ni A-PRE-1 `NOT AUTHORIZED / NOT EXECUTED`.

La adjudicación se limita a los casos siguientes:

- **`OBSERVED` (16):** `read` únicamente con un FD regular deliberadamente
  inyectado (sensibilidad del sensor, fuera del crédito Model B); fixtures
  sintéticos exactos de `openat`, `renameat`, `mmap(MAP_SHARED)`,
  `msync(MS_SYNC)`, `connect(AF_UNIX)` e `ioctl(FIONREAD)`; `sendto` con un
  socket AF_UNIX conectado deliberadamente inyectado (sensibilidad); además,
  `io_uring_setup`, `io_uring_enter` con cero SQE, `io_setup`, `io_submit` con
  cero requests, `io_pgetevents` con mínimo cero e `io_destroy` en un contexto
  vacío, en el fixture sintético anterior a la barrera.
- **`BLOCKED` (11):** `mmap` no llegó a invocarse cuando el pathname externo
  no estaba disponible y el FD no se pasó; `connect` al pathname AF_UNIX
  externo probado devolvió `ENOENT` sin FD heredado; y las nueve syscalls
  async (`io_uring_setup`, `io_uring_enter`, `io_uring_register`, `io_setup`,
  `io_destroy`, `io_getevents`, `io_submit`, `io_cancel`, `io_pgetevents`)
  devolvieron `EPERM` bajo el perfil exacto
  `a-pre-native-async-deny-v1`.

Solo 11 casos reciben crédito para el **subcaso Model B exacto**: los dos
controles de frontera launcher/path y las nueve denegaciones del perfil async.
Los positivos con capacidad inyectada son controles `sensor_sensitivity`, no
contención Model B. Los fixtures sintéticos restantes demuestran únicamente
los eventos acotados que describen. Ninguno de los 27 casos es elegible para el
predicate actual A-PRE-0 READY: sus resultados históricos no están re-vinculados
a un overlay cualificado que incluya esta revisión normativa y del manifiesto.

La relación con la syscall se registra solo donde la evidencia disponible
nombra la syscall concreta y su resultado. Por ejemplo, la transferencia de
19 bytes en el fixture de pipe no se imputa aquí a una fila `read` o `write`
sin una referencia de traza específica que cierre esa relación. Las variantes
no ensayadas permanecen abiertas: no se generaliza `MAP_SHARED`, un comando
`ioctl`, un `sendto`, ni una llamada async de conteo cero a toda su familia.
Tampoco se considera que estos fixtures completen la trazabilidad
Python/interface → extensión/dependencia → syscall para el workload.

La matriz por fila, los hashes de los artefactos citados, los límites por caso
y los conteos agregados están en
`A_PRE_0_SURFACE_MANIFEST.json#syscall_disposition_contract` y
`A_PRE_0_QUALIFICATION_LEDGER.json#inventory.syscall_dispositions`. No se
ejecutaron probes, TALOS, suites, parser/validador A-PRE ni readiness validator
para producir esta adjudicación.

## Revisión estática de filas sin candidata, variantes y trazabilidad

Se hizo una revisión documental de las **194 filas que no tenían superficie
candidata**. En 186 se registraron una o más referencias potenciales a las 16
superficies existentes, únicamente como pistas semánticas derivadas del nombre
de la syscall y de las definiciones actuales. No se alteró
`candidate_surface_ids`, no se aceptó ninguna relación, no se agregó una
superficie y no se emitió una exclusión. Las ocho filas sin una relación
existente suficientemente justificada son:
`_sysctl`, `afs_syscall`, `getpmsg`, `getrandom`, `nfsservctl`, `putpmsg`,
`tuxcall` y `vserver`. Para ellas siguen sin resolverse, según el caso, la
semántica legacy/de subsistema, el soporte efectivo en el kernel objetivo o
la relación con el modelo de amenaza. No se infiere que estén ausentes,
inofensivas o fuera de alcance. Por tanto, las 194 filas siguen sin membresía
canónica y `UNKNOWN`; incluso las 186 pistas requieren una decisión normativa.

También se revisaron los siete grupos de selectores ya enumerados. Solo tres
grupos enlazan subcasos históricos exactos: mappings (`mmap`/`msync`), sockets
(`connect`/`sendto`) e `ioctl(FIONREAD)`. Los casos disponibles siguen limitados
a sus argumentos, recursos y rutas registrados. No se completó ninguna
partición finita de valores/combinaciones. Para `clone`/`clone3`/fork,
`fcntl`, mount/namespaces y `seccomp`/`prctl`, los resultados históricos
existentes no adjudican los selectores del grupo. En particular, que el
launcher configure namespaces/seccomp o que una política bloquee syscalls
async no prueba que las llamadas de namespace, mount, `seccomp` o `prctl` del
workload estén bloqueadas. Todo selector y combinación todavía no acotado
permanece `UNKNOWN`.

La trazabilidad conserva diez mapeos a nivel de familias de interfaz: seis
`STATIC_CANDIDATE` y cuatro `UNKNOWN`. Hay **cero** cadenas que unan un callsite
del snapshot exacto con una versión concreta de CPython/libc/extensión/
dependencia, una emisión de syscall y su partición de argumentos. Los conteos
AST y los nombres de wrapper solo orientan la investigación; no prueban
alcanzabilidad ni ausencia. Quedan abiertos los callsites del workload exacto,
las implementaciones pinneadas, la emisión nativa y el dispatch dinámico,
efectos transitivos, ctypes/cffi, callbacks y extensiones.

El detalle por fila, los grupos de variantes, los bloqueos y los conteos están
en `A_PRE_0_SURFACE_MANIFEST.json` bajo `syscall_disposition_contract.no_candidate_row_review`,
`argument_variant_review.documentary_review_summary` y
`python_native_traceability.documentary_adjudication`, con los totales
replicados en el ledger. Se mantienen `inventory.frozen=false`,
A-PRE-0 `NOT READY` y A-PRE-1 `NOT AUTHORIZED / NOT EXECUTED`.

### Consolidación de pistas de las 194 filas sin candidata

La revisión documental se consolidó sin cambiar membresías canónicas ni disposiciones. Las 204 referencias potenciales corresponden a 186 filas: **168 filas tienen una referencia** a una superficie existente y **18 filas tienen dos referencias solapadas**. La distribución de referencias por superficie es: S01=24, S02=19, S04=6, S05=17, S06=19, S07=0, S08=0, S09=0, S10=38, S11=27, S15=3 y S16=51. Estas cifras describen el volumen de revisión, no cobertura ni alcanzabilidad.

Las ocho filas sin una relación existente suficientemente justificada permanecen explícitamente `UNKNOWN`: `_sysctl` (interfaz legacy sin aplicabilidad efectiva establecida), `afs_syscall` (AFS legacy sin dependencia del workload), `getpmsg`/`putpmsg` (STREAMS legacy sin ruta aplicable), `getrandom` (posible relación con inicialización/estado de seguridad, pero sin callsite ni partición trazados), `nfsservctl` (control legacy de servidor NFS sin aplicabilidad), `tuxcall` (interfaz legacy sin disponibilidad/relación establecida) y `vserver` (Linux-VServer legacy sin disponibilidad/relación establecida). No se registró exclusión normativa: cada caso requiere una decisión explícita o permanece `UNKNOWN`.

La salida de esta consolidación es únicamente una cola de adjudicación: para cada pista debe decidirse membresía canónica, exclusión justificada por el modelo de amenaza o `UNKNOWN`, usando argumentos, recursos, fase y trazabilidad del workload. La revisión por nombre no puede cerrar una fila.

