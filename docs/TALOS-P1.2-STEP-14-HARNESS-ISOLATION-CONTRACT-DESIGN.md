# TALOS-P1.2-STEP-14 — DISEÑO CONTRACTUAL DEL HARNESS Y DEL AISLAMIENTO ANIDADO

**Entrada:** `NESTED_WORKSPACE_CONTRACT_CONTRADICTION_FOUND`  
**Estado canónico:** `P1.2 = BLOCKED-REGRESSION`  
**Tipo:** análisis y diseño estático; sin implementación ni pruebas  
**Salida:** `HARNESS_CONTRACT_DESIGNED`

## 1. Estado del repositorio

- Rama observada: `talos-current-audit`.
- HEAD observado: `cc8acfae623f9d10c8366871470319786b6a7ca4`.
- Worktree sucio: al inicio de esta fase, `git status --porcelain` mostró 1.863 paths con cambios en el índice, 23 con cambios en el worktree y 64 paths untracked. Los conteos describen paths reportados por Git, no una atribución de autoría.
- El expediente de STEP-14 no existía antes de crearlo.
- Se preservaron todos los cambios preexistentes. El único archivo creado en esta fase es este expediente.

## 2. Evidencia de STEP-13 y alcance

STEP-13 concluyó `NESTED_WORKSPACE_CONTRACT_CONTRADICTION_FOUND`. Su inspección estática establece que:

- El runner principal crea `execution_root` debajo de `/tmp` en el host y lo monta en `/workspace/run`; el worker recibe un `/tmp` distinto, creado con `--tmpfs /tmp`.
- El runner asigna `TALOS_TEST_BASETEMP=/workspace/run/pytest-tmp`. Por ello, el `tmp_path` de pytest dentro del worker es una ruta del namespace guest.
- `_validate_mount_roots()` interpreta `workspace_root` en el namespace del proceso que lo invoca y exige un directorio válido bajo `/tmp` antes de buscar/invocar Bubblewrap. No convierte una ruta guest en una identidad host.
- Varios tests de aislamiento construyen `workspace_root` desde ese `tmp_path` e intentan invocar `run_isolated_process()` desde el worker. Eso contradice el contrato host actual.
- El test focal que sustituye `run_isolated_process()` por un fake no demuestra un mount anidado. STEP-13 también identificó que B1-R realiza su comprobación Git en el proceso pytest, donde el `.git` real está enmascarado durante el Quality Gate.
- STEP-13 confirma estáticamente el checkout read-only, el enmascaramiento de `.git` y de raíces protegidas, el rechazo fail-closed de workspaces inválidos y la separación de `/tmp` host/guest. No demuestra comportamiento dinámico.

Referencias: [STEP-13, secciones 3–6 y 8–11](./TALOS-P1.2-STEP-13-STATIC-NESTED-WORKSPACE-ADJUDICATION.md); [quality_gate.py, creación del workspace y configuración del worker](../scripts/quality_gate.py:1473); [quality_gate_isolation.py, validación y mapeo host→guest](../scripts/quality_gate_isolation.py:63); [quality_gate_isolation.py, límites y mounts de Bubblewrap](../scripts/quality_gate_isolation.py:290).

Este expediente propone un contrato para revisión posterior. No elige una arquitectura, no afirma que alguna alternativa ya esté implementada y no altera la clasificación de los casos o nodeids pendientes de STEP-13.

## 3. Contrato común de identidad y autoridad

### 3.1. Roles y ownership

| Entidad | Identidad de rutas | Autoridad propuesta dentro del contrato | No puede hacer |
|---|---|---|---|
| Harness host | Rutas visibles en el namespace host, por ejemplo `/tmp/.../execution` | Crear y poseer cada workspace host; validar sus raíces; preparar mounts; lanzar Bubblewrap; recoger resultado y artefactos autorizados; observar el estado Git del checkout cuando corresponda | Tratar una cadena guest como ruta host; aceptar una ruta del worker como autorización de mount |
| Worker aislado | Rutas guest, incluyendo `/workspace/repository`, `/workspace/run` y el `/tmp` privado del worker | Ejecutar el trabajo funcional de la prueba y producir únicamente resultados/artefactos permitidos por su contrato | Crear o certificar workspaces host; acceder al `.git` real; ampliar sus propios mounts; convertir rutas guest a host por inferencia |
| Worker anidado eventual | Su propio namespace guest, distinto del host y del worker padre | Ejecutar una tarea si un harness con autoridad host crea, valida y lanza su frontera | Usar el `tmp_path` guest del padre como `workspace_root` host o lanzar un bind privilegiado sobre una ruta host no verificada |
| Directorio temporal de pytest | Guest si pytest corre dentro del worker; host si pytest corre en el harness host | Alojar temporales dentro del namespace y workspace definidos para esa ejecución | Implicar, por nombre o prefijo, que el directorio es host-owned |
| Workspace host autorizado | Ruta host canónica, existente, no symlink según el validador, bajo `/tmp` y separada del checkout | Ser el origen host de un bind writable deliberado y limitado | Ser sustituido por una ruta guest o incluir el checkout/raíces protegidas |
| Ruta guest | Ruta absoluta dentro del filesystem Bubblewrap, derivada del destino explícito del mount | Identificar el objeto visible al proceso guest | Ser usada como identidad host o resolverse mediante fallback en el filesystem del host |

El proceso que crea un workspace también debe establecer su identidad y conservar su ownership hasta el cierre de la ejecución. La validación de una ruta host debe ejecutarse en el harness host que la ve como tal y antes de construir el mount. El worker no gana autoridad host por conocer una ruta, tener un sufijo similar o escribirla en un mensaje.

### 3.2. Correspondencia explícita host/guest

La relación se expresa como dos identidades tipadas y una relación de mount, no como una igualdad de strings:

```text
HostWorkspace(run_id, canonical_host_root)
    -- bind writable explícito -->
GuestMount(run_id, guest_mountpoint)

pytest_tmp = GuestMount.guest_mountpoint / relative_tmp_path
```

Para el runner principal observado, `canonical_host_root` es el `execution_root` bajo `/tmp` y `guest_mountpoint` es `/workspace/run`. `TALOS_TEST_BASETEMP` debe nombrar una ubicación guest dentro de ese mount. Esta asociación es válida para esa invocación y ese `run_id`; no convierte un path derivado posteriormente por pytest en una identidad host.

La operación documentada por `workspace_guest_path()` es host→guest, relativa a un workspace host existente. No debe interpretarse como una función inversa. No hay en la evidencia de STEP-13 un protocolo de resolución guest→host, una identidad de mount transferible o un broker de launches anidados.

### 3.3. Contrato de fallos

- Rechazar explícitamente paths host ausentes, symlinks o fuera de la raíz autorizada antes de construir mounts.
- No traducir paths guest a host por prefijo, coincidencia de sufijo, inspección de `/proc`, variables heredadas ni fallback al filesystem host.
- Un request de launch que carezca de identidad, autorización, workspace host o mountpoint inequívocos debe terminar `BLOCKED`/error, sin fallback.
- Preservar stdout/stderr, timeout y código de salida del proceso hijo según el contrato del runner; una falla de validación o launch no debe parecer un éxito funcional.
- Mantener separado el estado de proceso (`TEST_PASS`/`TEST_FAIL`/error) de la evaluación de aislamiento y de cualquier adjudicación del gate.

## 4. Comparación de arquitecturas conceptuales

Las alternativas son mutuamente comparables, no decisiones aprobadas. “Compatible” describe únicamente compatibilidad estática con los invariantes enumerados, no disponibilidad en el código actual ni validez de ejecución.

| Criterio | A1 — Harness host controla cada worker | A2 — Harness host administra launches anidados | A3 — Clase de tests con harness específico |
|---|---|---|---|
| **Arquitectura / identificador** | A1. El harness host crea, valida y lanza el worker; el worker no lanza Bubblewrap directamente. | A2. El harness host mantiene autoridad exclusiva y acepta requests explícitos de launch anidado de un worker. | A3. Los tests que requieren un segundo boundary se declaran como clase/perfil aparte, ejecutada bajo un harness diseñado para esa frontera. |
| **Autoridad host** | Harness host dueño del `execution_root` y de cada directorio de ejecución. | Harness host/broker autenticado dueño de todos los workspaces host; el worker solicitante no los posee. | Harness específico en host dueño de workspace, política y lifecycle de esos tests. |
| **Quién crea y controla el workspace** | El host asigna workspace host nuevo bajo `/tmp`; el worker recibe solo su mount guest. | El host/broker asigna un workspace host nuevo por request y run; nunca adopta directamente el `tmp_path` guest recibido. | El harness de la clase de prueba asigna un workspace host por ejecución; temporales pytest permanecen en su namespace declarado. |
| **Frontera de procesos / quién lanza a quién** | Host → worker. No hay worker → Bubblewrap anidado. Para comprobar un segundo proceso, el host orquesta una ejecución separada. | Host → worker padre; worker padre → request limitado; host/broker → worker hijo. El worker no invoca un launcher privilegiado local. | Host → harness de prueba → worker(s) explícitamente definidos. La clase no se ejecuta con semántica implícita distinta dentro del worker estándar. |
| **Identidad de rutas** | Cada run contiene identidad host y guest separadas, correlacionadas por run-id y mountpoint. | Request tipado con acción, run-id, política y artefactos relativos; el host genera la ruta host. No acepta paths host arbitrarios suministrados por guest. | El perfil identifica rutas host/guest y el tipo de pytest que las origina; no hay conversión guest→host implícita. |
| **Git** | Harness host captura `git status` antes/después del worker cuando el contrato lo requiera; worker produce resultado funcional/artefactos, no estado Git. | Igual que A1; el broker no delega la consulta Git al worker ni expone `.git`. | El harness dedicado realiza la observación Git host-side independientemente del proceso funcional, manteniendo correlación con el test/run. |
| **Mounts** | Checkout read-only en `/workspace/repository`; `.git` y raíces protegidas enmascaradas; un único workspace host autorizado bind-mounted en `/workspace/run`; `/tmp` guest independiente. | Mismos mounts para cada hijo; cada workspace es host-owned, nuevo y validado. El protocolo no debe convertir el workspace del padre en un bind arbitrario. | Mismos invariantes por cada ejecución de la clase. Cualquier mount adicional requiere autorización y validación explícita y mínima. |
| **Errores y códigos de salida** | El host registra la terminación del worker y propaga su código; rechazo de root o falta de Bubblewrap bloquea. | El broker autentica/autorización y valida request antes de launch; rechazos, timeout y exit code del hijo se informan como resultados distintos, sin fallback. | El harness específico reporta por separado errores de preparación, resultado funcional del worker y resultado de aislamiento; un error del harness no se convierte en test pass. |
| **Invariantes de seguridad** | Conservables. Elimina el lanzamiento anidado directo desde el worker. | Conservables solo con un broker host estrecho y fail-closed; una interfaz permisiva sería una ruta de escalada/confused deputy. | Conservables si es aislamiento real y no un mock; riesgo de divergencia entre perfil dedicado y gate normal. |
| **Compatibilidad estática actual** | Compatible con la autoridad del runner principal observada; no resuelve por sí sola tests que esperan launch anidado desde dentro del worker. | No resuelto: el repositorio inspeccionado no demuestra broker, protocolo, autenticación/autorización ni lifecycle de workspaces hijos. | No resuelto: no se demostró el mecanismo actual para declarar, seleccionar o adjudicar esta clase sin perder cobertura exigida por el gate. |
| **Cambios potenciales (solo inventario)** | Podrían afectar runner/harness, definición de perfiles/nodeids y contratos de resultados; no se ha decidido ningún cambio. | Podrían afectar runner, módulo de aislamiento, protocolo host-worker, autorización, recolección de artefactos y tests; cada pieza requiere contrato propio. | Podrían afectar configuración/perfil del gate, clasificación de tests, harness dedicado y reportes; la cobertura y agregación requerirían decisión. |
| **Archivos hipotéticos** | `scripts/quality_gate.py`, `scripts/quality_gate_isolation.py`, tests bajo `tests/unit/diagnostics/` y documentación contractual. | Los mismos más el componente de broker/protocolo si existiera o fuese aprobado. | `scripts/quality_gate.py`, configuración/perfil de suites, tests de diagnostics y documentación de gate/harness. |
| **Incertidumbres** | Si la suite permite comprobar el comportamiento deseado mediante procesos separados orquestados por el host y cómo se correlacionarían los artefactos. | Si una petición desde el worker es necesaria; cómo se autenticaría, limitaría y auditaría; cómo evitar doble interpretación de path y confused deputy. | Qué tests deben pertenecer a la clase; si el gate admite perfiles de harness diferenciados; cómo impedir que una clase fuera del gate sea confundida con cobertura equivalente. |
| **Estado** | `COMPATIBLE` para el modelo de ownership del runner; `NO RESUELTO` para la cobertura de las pruebas anidadas. | `NO RESUELTO`. | `NO RESUELTO`. |

#### Alternativas incompatibles

No son soluciones aceptables bajo este contrato:

- Montar el `/tmp` host entero dentro del worker o aceptar que `tmp_path` guest identifique una raíz host.
- Ampliar el bind writable al checkout, `.git`, bases protegidas o roots no autorizadas.
- Quitar/rebajar la comprobación de `/tmp`, symlinks, solapamiento con checkout o errores de validación.
- Hacer que el worker elija rutas host arbitrarias o resolverlas con fallback.
- Reemplazar la ejecución de Bubblewrap por mocks y declarar demostrada la propiedad de aislamiento.
- Omitir la observación Git porque el worker no ve `.git`.

## 5. Contrato de verificación del estado Git

La observación del checkout es una propiedad del harness host autorizado, separada de la ejecución funcional:

```text
Harness host:
  captura identidad del checkout y estado Git inicial
  ejecuta el worker aislado con checkout read-only y .git enmascarado
  recoge resultado funcional y artefactos permitidos desde el workspace
  captura estado Git final desde el mismo checkout host
  compara baseline/final y registra evidencia ligada al run

Worker:
  produce resultado funcional, stdout/stderr y artefactos autorizados
  no lee .git real ni emite una afirmación autoritativa sobre Git
```

Contrato propuesto:

1. El observador Git corre fuera del worker y usa la identidad de checkout del host aprobada para la ejecución. El `.git` real no se monta ni se hace visible al worker.
2. Captura inicial y final se comparan contra el mismo checkout, scope y mecanismo; la comprobación debe detectar también paths untracked según la propiedad evaluada. Un baseline sucio preexistente es estado inicial válido para la comparación, no motivo para limpiarlo.
3. Cada observación identifica run, checkout/commit, momento, comando/alcance y resultado; los artefactos del worker se identifican aparte y no sustituyen la evidencia Git.
4. Error al consultar Git, cambio de checkout durante la ejecución, estado final distinto o evidencia incompleta no se traduce en “sin cambios”: produce `FAIL`, `BLOCKED` o `UNKNOWN` conforme a la política pendiente.
5. El test conserva dos assertions distintas: éxito/resultado funcional del worker y ausencia de delta no autorizado en el checkout. La segunda no se mockea ni se omite.

STEP-13 demuestra la tensión actual: B1-R llama `_git_status()` desde el proceso pytest, pero dentro del Quality Gate `.git` está enmascarado. No se ha demostrado que el runner actual haga la captura host-side pre/post para esa prueba. Por tanto, el flujo anterior es un contrato propuesto, no comportamiento existente ni evidencia de que el test esté resuelto.

## 6. Límites de confianza y mounts que deben permanecer

Para todas las alternativas aceptables:

| Límite | Contrato a conservar | Evidencia estática de STEP-13 |
|---|---|---|
| Checkout | Solo lectura para el worker, montado en `/workspace/repository`. | `quality_gate_isolation.py:300-305` |
| `.git` | Contenido real no disponible dentro del worker; observación Git host-side separada. | `quality_gate_isolation.py:399-426` |
| Raíces protegidas | Mantenerlas enmascaradas y no crear mounts writable hacia ellas. | `quality_gate_isolation.py:352-384`; STEP-13 sección 8 |
| Workspace writable | Limitarlo al workspace host derivado, validado bajo `/tmp`, distinto del checkout. | `quality_gate_isolation.py:63-86,303-305` |
| `/tmp` | No montar el `/tmp` host; mantener el tmpfs guest independiente. | `quality_gate_isolation.py:296-305` |
| Validación | Ejecutar validación host antes de launch; rechazar entradas inválidas fail-closed. | `quality_gate_isolation.py:63-86,211-225` |
| Bases protegidas | No exponerlas por bind, fallback, copia ni vía de escritura guest. | STEP-13 sección 8; mounts y máscaras en `quality_gate_isolation.py:352-396` |
| Artefactos | Permitir solo paths relativos/outputs explícitos dentro de un workspace autorizado; la salida no adquiere autoridad por venir del worker. | STEP-13 sección 6; cualquier detalle adicional queda por diseñar si se elige A2/A3. |

La necesidad funcional de probar aislamiento no justifica debilitar ningún límite. Si alguna alternativa requiere hacerlo, queda fuera de contrato y debe rechazarse, no ponderarse como un trade-off aceptable.

## 7. Riesgos residuales y decisiones explícitas pendientes

Antes de diseñar una implementación futura, el revisor/operador debe decidir:

1. Si se adopta A1, A2 o A3; esta fase no selecciona ninguna.
2. Si las pruebas que actualmente intentan un launch anidado deben ser orquestadas desde el host, servidas por un broker host estrecho o declaradas dentro de un harness/perfil específico.
3. Quién autoriza un eventual broker y cuál es su protocolo mínimo, identidad de caller, allowlist de operación, control de recursos, correlación de run, límites de output y auditoría. Sin estas decisiones, A2 permanece `NO RESUELTO`.
4. Qué nodeids deben quedar cubiertos por el gate y qué evidencia probaría que una separación de clase/harness no reduce el scope. Sin ello, A3 permanece `NO RESUELTO`.
5. Cómo se lleva la observación Git antes/después al harness host sin cambiar su significado ni destruir el estado dirty preexistente. La salida debe distinguir error de observación de estado sin cambios.
6. Qué interfaz autoritativa transmite artefactos del worker al harness y qué rutas guest pueden recogerse desde el bind host sin convertir una ruta arbitraria del worker en permiso de acceso.
7. Qué verificación futura, autorizada por separado, sería apropiada para demostrar cada propiedad en ejecución. Este expediente no autoriza dicha ejecución.

Riesgo común: una implementación que solo conserve los nombres de variables o paths, sin preservar sus identidades de namespace y ownership, podría recrear la misma confusión host/guest. En A2 existe además riesgo de confused deputy; en A3 existe riesgo de que el perfil especializado omita inadvertidamente tests requeridos; en A1 existe riesgo de dejar sin una vía contractual los casos que hoy esperan aislamiento anidado. Son riesgos a adjudicar, no hallazgos dinámicos.

## 8. Estado de salida y límites

- `HARNESS_CONTRACT_DESIGNED`: se define el ownership host/guest, el contrato de fallo, la separación Git y una matriz de tres arquitecturas con incertidumbres concretas para revisión futura.
- No se selecciona ni implementa arquitectura.
- No se declaran `STATICALLY_VALIDATED`, `TEST_PASS`, `ISOLATION_DEMONSTRATED`, `GATE_SATISFIED` ni release eligibility.
- No se autoriza STEP-15, pruebas, ejecución de aislamiento ni reapertura del Quality Gate.
- No se ejecutaron `pytest`, nodeids, `scripts/test.sh`, Quality Gate, scripts de preparación, benchmarks ni pruebas de aislamiento.
- No se accedió a bases protegidas ni se crearon snapshots.
- No se hizo staging, commit, reset, checkout ni limpieza.
- No se modificaron código, tests, configuración ni expedientes previos.

**Salida:** `HARNESS_CONTRACT_DESIGNED`  
**Estado canónico obligatorio:** `P1.2 = BLOCKED-REGRESSION`
