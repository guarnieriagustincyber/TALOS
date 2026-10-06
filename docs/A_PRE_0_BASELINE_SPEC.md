# A-PRE-0 — Especificación de baseline PRE

**A-PRE-0:** `SPECIFIED`  
**Preflight:** `REVIEW REQUIRED / NOT READY FOR A-PRE-1`  
**Baseline PRE certificada:** ninguna  
**A-PRE-1:** `NOT EXECUTED`  
**Autorización A-PRE-1:** `PENDING / NOT AUTHORIZED`  
**Alcance:** definir una comparación reproducible; no ejecutar suites ni cambiar código funcional.

## 1. Identidad del snapshot

La inspección de especificación comenzó sobre la rama `main`, con
`HEAD=b12e34099336760e8fd55455526a580cd479dade`. Ese checkout ya estaba sucio
(13 paths modificados/no comprometidos antes de esta especificación), por lo
que no es una baseline PRE limpia. A-PRE-0 y sus cambios de documentación/
manifiesto también forman parte de ese estado de trabajo; no deben confundirse
con el snapshot que A-PRE-1 certifique.

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

En la unión del primer barrido de 453 módulos había 99 candidatos; al añadir
`tests/audit/test_apre_result.py`, el inventario de ese snapshot de 454 módulos
marcó 100 candidatos (22 DB, 60 filesystem, 9 network, 31 `open`, 5 process;
los totales por clase se solapan). El segundo fixture A-PRE del observer se
añadió después y ese pre-screen no se ha repetido: sus llamadas sintéticas no
deben contabilizarse como adjudicación dinámica. Los 99 candidatos del árbol
previo siguen pendientes de adjudicación. El barrido no encontró estas APIs
en los demás módulos, lo que no descarta efectos indirectos por código de
producción importado, aliases, callbacks ni llamadas construidas
dinámicamente. El inventario AST es un pre-screen histórico; la esterilidad
permanece `UNVERIFIED`, no `PASS`.

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
del overlay, padre, árbol e integridad autónoma del object store. Este snapshot
no ejecutó imports, colección, pruebas ni gates.

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
scratch y `/tmp`. El tracing solicita las clases `%file,%network,%process,
%ipc,%memory`; sus logs se conservan fuera del snapshot. La cobertura sigue
marcada incompleta porque excluye syscalls `read`/`write` con datos y porque el
host actual rechaza `PTRACE_TRACEME` con `Operation not permitted`. El harness
ejecuta primero un probe sintético de strace y no inicia el gate release a
menos que el tracing esté adjunto y completo. Debe emitir `ERROR`, nunca
`PASS`, si strace no se adjunta o la cobertura sigue incompleta. Una operación
no clasificable, una salida del perímetro o una laguna del observer será
`UNKNOWN` y no podrá producir esterilidad `PASS`.

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
la adjudicación dinámica real solo se produce durante una futura ejecución
autorizada; no es una precondición que obligue a ejecutar el benchmark antes
de A-PRE-1.

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
| Salidas del PRE definidas | `RUNNER + INDEPENDENT CLI FIXTURE-TESTED` | 14 pruebas de reporter, 6 de observer y 6 de harness pasan. El builder genera un artefacto completo desde collector/fixtures y el verifier independiente lo acepta; rechaza como aceptable el caso con tracing incompleto. No se generó resultado TALOS. |
| Efectos laterales | `OS FIXTURES PASS; SYSCALL TRACE BLOCKED` | Bubblewrap contuvo fixtures sintéticas: filesystem del snapshot y `/etc` read-only, scratch/SQLite/proceso permitidos, conexión de red denegada y `/proc` aislado. `strace` no puede adjuntarse en este host (`PTRACE_TRACEME: Operation not permitted`); su cobertura sigue incompleta. |
| Snapshot | `CLEAN ISOLATED OVERLAY REGENERATED AND VERIFIED` | Overlay externo derivado del HEAD `b12e340...` con el working tree observado aplicado; incluye harness y corrección del descubrimiento bajo rutas padre ocultas. Worktree limpio, object store autónomo y `git fsck` correcto; checkout fuente preservado. |
| Límites y exclusiones | `PASS WITH PRECONDITION` | E5/Qwen, blind pool, BENCH-G2, NotebookLM, producción, providers reales y migraciones excluidos. Sin acceso a datos no puede certificarse esterilidad solo desde la especificación. |

**Resultado del preflight:** `REVIEW REQUIRED / NOT READY FOR A-PRE-1`. No se
encontró inconsistencia no resoluble en el perímetro ni en la instalación
aislada de dependencias. Se fijó la invocación del gate para no seleccionar el
`.venv` 3.12. El reporter independiente pasó catorce fixtures y el observer
seis fixtures sintéticos. Se añadió el runner completo de evidencia y el
aislamiento bubblewrap; fixtures sintéticas validan el límite OS y el builder
produce/valida `result.json` sin ejecutar TALOS. Aún falta un entorno que
permita syscall tracing confiable: este host bloquea ptrace y el contrato
declara incompleta la cobertura. El snapshot externo limpio se regeneró luego
del harness y de corregir el filtro de rutas ocultas; su verificación es parte
de la evidencia externa. Por ello el preflight sigue
`REVIEW REQUIRED / NOT READY`. La adjudicación de efectos reales quedará en el
resultado de la futura ejecución A-PRE-1; exigirla antes de autorizar esa
primera ejecución sería circular. No ejecutar imports, colección o suites
TALOS por adelantado ni autorizar A-PRE-1 hasta cerrar la instrumentación y el
collector.

## Gate de salida A-PRE-0

- **Especificación:** completa en los seis bloques anteriores.
- **Validación realizada:** inspección estática, validación del perímetro,
  resolución e instalación de 61 paquetes con uv 0.12.20 en venv temporal,
  `uv pip check`, imports smoke de dependencias, 14 fixtures del
  emisor/verificador, 6 fixtures de observer y 6 fixtures de harness (26
  pruebas en total); probes bubblewrap para filesystem/red/SQLite/proceso; no
  se ejecutó suite
  de TALOS, no se recolectaron suites y no se invocó `scripts/test.sh`.
- **Pendiente antes de A-PRE-1:** resolver el bloqueo de ptrace/cobertura
  syscall; el snapshot externo actual fue regenerado, el runner,
  aislamiento OS y el contrato `result.json` ya están conectados y probados
  con fixtures. La inspección/import/colección
  de TALOS y adjudicación de efectos reales no se anticipan fuera del gate
  autorizado.
- **Autorización:** `PENDING / NOT AUTHORIZED`. Este documento no es una
  autorización ni un resultado PRE; E5/Qwen, producción, DB/corpus y blind pool
  continúan intactos y fuera de ejecución.
