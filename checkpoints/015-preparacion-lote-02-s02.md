# Preparación del lote 02 — referencias potenciales S02

Fecha: 2026-10-01

## Alcance e invariantes

Se enumeran las referencias `potential_surface_refs` pendientes que nombran
S02 en el estado persistido en `baceb4112f9dd3ac448eca8275ad70cc1c9f5d37`
(branch `main`). Es un informe documental para revisión humana, no una
adjudicación ni una decisión de membresía.

La definición vigente de S02 es **Data transfer through descriptors**:

- recurso: bytes transferidos por descriptores regulares, anónimos, pipe o
  socket;
- ejes declarados: identidad de FD de origen/destino; cantidad solicitada
  frente a retorno completado; offsets, vectores, flags y transferencias
  parciales; clase de recurso y omisión intencional de payload;
- rutas alternativas declaradas: S03, S05, S06, S07, S08, S09, S10, S12, S13 y
  S14.

Las pistas S02 de este lote son mayormente operaciones adyacentes al I/O (offset,
prefetch, advice, writeback, readiness y sincronización), no todas
transferencias de bytes. Ese límite se señala en cada fila; no se fuerza un
encaje sólo porque una operación mencione un FD o I/O.

## Inventario completo

La cola contiene **19 referencias**. Las 19 filas tienen actualmente
`candidate_surface_ids=[]`, `candidate_membership_status=UNREVIEWED` y
`disposition_status=UNKNOWN`. “Relación propuesta” indica la cuestión a
considerar por quienes revisen el lote; no equivale a un “SÍ”, “NO” o
`UNKNOWN` adjudicado.

| NR / syscall | Evidencia documental de semántica | Recurso/objeto | Variante o condición relevante | Cruces relevantes | Relación propuesta con S02 |
|---|---|---|---|---|---|
| 7 `poll` | Espera que un conjunto de FDs esté listo para una operación de I/O; devuelve bits `revents`, no transfiere el contenido. [`poll(2)`](https://man7.org/linux/man-pages/man2/poll.2.html) | FDs de archivos/canales vigilados y array de eventos | `events`/`revents`, timeout, readiness según tipo de FD; regular files pueden reportar ready de inmediato | S03 (identidad FD), S07/S08 (sockets), S10 (espera/eventos) | **Frontera dudosa:** readiness habilita I/O posterior, pero no es por sí una transferencia de bytes según la definición actual de S02. Evaluar si S02 lo excluye o si hace falta modelar readiness aparte; no adjudicado. |
| 8 `lseek` | Reposiciona el offset de una open file description; `SEEK_DATA`/`SEEK_HOLE` pueden consultar regiones con datos/huecos. [`lseek(2)`](https://man7.org/linux/man-pages/man2/lseek.2.html) | Open file description de un archivo, identificado por FD | `SEEK_SET/CUR/END/DATA/HOLE`, offset antes/después, archivo regular u objeto no seekable | S03 (open-file-description y descriptor); S05 (interacción con offset/archivo mapeado) | **Adyacente y estrechamente ligado a S02:** no mueve bytes, pero modifica el estado de offset que determina futuras lecturas/escrituras. Revisar como estado de I/O del FD, sin inferir transferencia. |
| 23 `select` | Espera readiness de varios FDs para lectura/escritura/excepción y devuelve los sets listos. [`select(2)`](https://man7.org/linux/man-pages/man2/select.2.html) | Sets de descriptores y estructuras de timeout | `readfds`/`writefds`/`exceptfds`, `nfds`, `FD_SETSIZE`, timeout; `select` modifica los sets in-place | S03 (FDs), S07/S08 (socket readiness), S10 (wait/coordination) | **Frontera dudosa:** multiplexación de readiness, no transferencia. Similar a `poll`; relación con S02 sólo si el alcance de S02 incluye selección/espera anterior a I/O. |
| 73 `flock` | Aplica, cambia o quita un lock advisory sobre un archivo abierto identificado por FD. [`flock(2)`](https://man7.org/linux/man-pages/man2/flock.2.html) | Archivo/open file description y estado de lock | `LOCK_SH`, `LOCK_EX`, `LOCK_UN`, `LOCK_NB`; bloqueo, duplicación, herencia y cierre de todos los FDs | S03 (open-file-description/duplicados), S10 (coordinación entre procesos) | **Relación S02 débil/ambigua:** afecta acceso concurrente a un objeto usado para I/O, pero no mueve bytes. Priorizar la revisión S03/S10; mantener como lead S02 sin afirmar membresía. |
| 162 `sync` | Fuerza escrituras pendientes de datos de archivo cacheados y metadata hacia filesystem/dispositivos subyacentes. [`sync(2)`](https://man7.org/linux/man-pages/man2/sync.2.html) | Cachés y modificaciones pendientes de todos los filesystems visibles al proceso | Operación global sin argumento FD; semántica de finalización de Linux; no identifica cada archivo causante | S04 (efecto filesystem/persistencia), S10 (operación global/coordinación) | **Adyacencia S02 por persistencia de datos**, pero el alcance global y metadata no encajan limpiamente con “bytes transferidos por descriptores”. Requiere resolver el límite de superficie y no inferir endpoints/bytes. |
| 187 `readahead` | Programa lectura anticipada de un rango de archivo por FD hacia page cache para que lecturas posteriores puedan evitar I/O bloqueante. [`readahead(2)`](https://man7.org/linux/man-pages/man2/readahead.2.html) | Archivo y páginas de page cache, seleccionados por FD | Offset, count, alineación/rounding por página, FD legible; no cambia el offset compartido | S03 (FD); S05 (page cache/mapping); potencial S07 si el objeto resulta ser un tipo con semántica de I/O admitida | **Lead S02 sustantivo:** provoca lectura/prefetch de datos de archivo, aunque no devuelve el payload al proceso en esa syscall. Determinar si “transferencia” incluye prefetch; no adjudicado. |
| 213 `epoll_create` | Crea una instancia epoll en kernel y devuelve un FD para las operaciones epoll posteriores. [`epoll_create(2)`](https://man7.org/linux/man-pages/man2/epoll_create.2.html) | Objeto de instancia epoll y FD resultante | `size` ignorado desde Linux 2.6.8 pero debe ser positivo; recurso liberado al cerrar todos los FDs | S03 (creación/ciclo de vida FD), S10 (coordinación por eventos) | **No es transferencia de bytes:** es creación de recurso/descriptor de readiness. El lead S02 requiere revisión de frontera; sus ejes primarios parecen S03/S10. |
| 214 `epoll_ctl_old` | La tabla lo identifica como syscall “old”; la interfaz epoll documentada registra, modifica o elimina FDs de la lista de interés, pero esta fuente no demuestra equivalencia exacta del ABI antiguo del target. [`epoll_ctl(2)`](https://man7.org/linux/man-pages/man2/epoll_ctl.2.html), [`epoll(7)`](https://man7.org/linux/man-pages/man7/epoll.7.html) | Instancia epoll, FD observado y configuración de eventos | ABI/estructura de la variante `old` aún requiere verificación específica contra la fuente versionada del target; `ADD/MOD/DEL` como guía de la API moderna | S03 (FDs y referencias a open-file descriptions), S10 (gestión de interest list) | **Frontera S02 dudosa:** la API configura readiness, no transfiere datos. No equiparar `epoll_ctl_old` con la interfaz moderna sin verificar el ABI; revisión primaria S03/S10. |
| 215 `epoll_wait_old` | La API epoll espera eventos de una instancia y devuelve registros de readiness; la documentación moderna no basta para probar equivalencia exacta del syscall `old`. [`epoll_wait(2)`](https://man7.org/linux/man-pages/man2/epoll_wait.2.html), [`epoll(7)`](https://man7.org/linux/man-pages/man7/epoll.7.html) | FD de instancia epoll y buffer de eventos de readiness | Variante `old`, tamaño/estructura ABI y timeout deben contrastarse con fuente del kernel target | S03 (FD de instancia), S10 (espera/eventos), S07/S08 según los FDs notificados | **Frontera S02 dudosa:** entrega metadatos de readiness, no payload de I/O. No adjudicado y ABI antiguo sin cerrar. |
| 221 `fadvise64` | La interfaz de advice declara patrones futuros sobre un rango del archivo referido por FD; `WILLNEED` puede iniciar lectura no bloqueante y `DONTNEED` intentar liberar páginas cacheadas. [`posix_fadvise(2)`](https://man7.org/linux/man-pages/man2/posix_fadvise.2.html) | Archivo y región de datos en page cache, seleccionados por FD | advice, offset/size, alineación de páginas y versión del kernel; los hints no son binding | S03 (FD); S05 (page cache); solapa conceptualmente con S02 I/O y S05 mappings | **Lead S02 adyacente:** controla preparación/retención de datos, no es en general transferencia de bytes al proceso. Revisar si los efectos `WILLNEED`/`DONTNEED` se modelan en S02, S05 o ambas. |
| 232 `epoll_wait` | Espera eventos en una instancia epoll y devuelve registros de readiness para FDs en su interest list. [`epoll_wait(2)`](https://man7.org/linux/man-pages/man2/epoll_wait.2.html) | Instancia epoll, FDs observados y buffer de eventos | Número máximo devuelto, timeout, modo edge/level configurado, máscara de señales sólo en variantes `pwait` | S03, S10; S07/S08 según tipo de FD observado | **Frontera S02 dudosa:** observación de disponibilidad de I/O no transferencia efectiva de datos. Relación sólo si S02 se amplía explícitamente a readiness. |
| 233 `epoll_ctl` | Añade, modifica o elimina un FD en la interest list de la instancia epoll; define los eventos que se reportarán. [`epoll_ctl(2)`](https://man7.org/linux/man-pages/man2/epoll_ctl.2.html) | Instancia epoll, FD target y configuración `epoll_event` | `EPOLL_CTL_ADD/MOD/DEL`; flags de evento, referencia a open file description y campo `data` que luego retorna `epoll_wait` | S03 (FD/open-file-description); S10 (gestión/coord. de eventos); S07/S08 para targets socket | **Frontera S02 dudosa:** configura notificación de readiness, no transfiere los bytes listos. Revisar prioritariamente con S03/S10. |
| 270 `pselect6` | Variante de multiplexación que espera readiness de sets de FDs y permite actualizar atómicamente la máscara de señales durante la espera. [`select(2)`](https://man7.org/linux/man-pages/man2/select.2.html) | FDs en read/write/exception sets y estado de señal | Timeout de alta resolución en `timespec`; máscara de señales y estructura ABI del argumento final de syscall | S03 (FDs), S10 (wait/señales), S07/S08 según FD | **Frontera S02 dudosa:** espera readiness, no transferencia. La variante de señal/timeout refuerza la dimensión de coordinación (S10). |
| 271 `ppoll` | Espera readiness de un array `pollfd`; variante con timeout de mayor resolución y máscara de señales. [`poll(2)`](https://man7.org/linux/man-pages/man2/poll.2.html) | FDs en array `pollfd` y resultados `revents` | `nfds`, eventos solicitados/devueltos, timeout y `sigmask` | S03, S10, S07/S08 según FD | **Frontera S02 dudosa:** readiness antes de I/O, no transferencia. No adjudicado. |
| 281 `epoll_pwait` | `epoll_wait` con cambio atómico de máscara de señales durante la espera. [`epoll_wait(2)`](https://man7.org/linux/man-pages/man2/epoll_wait.2.html) | FD epoll, FDs observados, buffer de eventos y señales | Timeout, `maxevents`, máscara de señales; preserva la semántica readiness de epoll | S03, S10, S07/S08 según FD | **Frontera S02 dudosa:** retorno de eventos/ready status, no payload. Cruce fuerte con coordinación S10. |
| 291 `epoll_create1` | Crea instancia epoll y retorna un FD; `EPOLL_CLOEXEC` modifica el flag de close-on-exec del nuevo FD. [`epoll_create(2)`](https://man7.org/linux/man-pages/man2/epoll_create.2.html) | Instancia epoll y nuevo FD | Flags, especialmente `EPOLL_CLOEXEC`; ciclo de vida al cerrar todos los descriptores | S03 (adquisición, flags y ciclo de vida FD), S10 (recurso de readiness) | **No es transferencia de bytes:** creación y adquisición de FD. El lead S02 parece principalmente S03/S10, sujeto a decisión de límites. |
| 306 `syncfs` | Sincroniza datos cacheados y metadata del filesystem que contiene el archivo referido por FD. [`sync(2)`](https://man7.org/linux/man-pages/man2/sync.2.html) | Filesystem seleccionado indirectamente por el objeto abierto en FD | Identidad del FD/filesystem; errores de writeback; alcance filesystem-wide, no sólo el archivo señalado | S03 (FD); S04 (filesystem/persistencia); S02 por writeback de datos | **Lead S02 adyacente fuerte:** hay writeback de datos, pero el alcance incluye todo un filesystem y metadata. La relación superpuesta requiere particionar recurso y efectos. |
| 441 `epoll_pwait2` | Variante de `epoll_pwait` con timeout `timespec` de resolución nanosegundo. [`epoll_wait(2)`](https://man7.org/linux/man-pages/man2/epoll_wait.2.html) | Instancia epoll y FDs/eventos observados | Timeout de precisión superior, máscara de señales y buffer de eventos | S03, S10, S07/S08 según FD | **Frontera S02 dudosa:** readiness/event notification, no transferencia. No adjudicado. |
| 451 `cachestat` | Consulta conteos de páginas cacheadas, sucias, en writeback y eviction en un rango de archivo mediante FD. [`cachestat(2)`](https://man7.org/linux/man-pages/man2/cachestat.2.html) | Estado de page cache de un archivo y rango de bytes | Offset/len, flags reservados a cero, tipo de archivo soportado; valores son snapshot potencialmente obsoleto | S03 (FD), S05 (page cache/mapping), potencial S02 por relación con datos I/O | **Relación S02 débil/ambigua:** consulta metadata de cache; no transfiere bytes. Evaluar S05 como dimensión primaria y si S02 necesita incluir observación de estado de cache. |

## Lectura por grupos para la revisión humana

1. **Readiness, no transferencia directa (12 referencias):** `poll` (7),
   `select` (23), `epoll_create` (213), `epoll_ctl_old` (214),
   `epoll_wait_old` (215), `epoll_wait` (232), `epoll_ctl` (233),
   `pselect6` (270), `ppoll` (271), `epoll_pwait` (281),
   `epoll_create1` (291) y `epoll_pwait2` (441). Las definiciones disponibles
   apuntan a S03/S10 y potencialmente S07/S08 según los FDs; su inclusión en
   S02 depende de si S02 cubre readiness y creación/configuración del
   mecanismo, además de transferir bytes. Los dos syscalls `old` necesitan
   confirmar el ABI exacto contra una fuente versionada del kernel target.
2. **Offset/locking y coordinación de I/O (2 referencias):** `lseek` (8) y
   `flock` (73). El primero cambia el offset que condiciona I/O posterior; el
   segundo sincroniza acceso mediante locks asociados a open-file descriptions.
   Cruces importantes S03 y S10; ninguno transfiere bytes en sí.
3. **Cache/read/writeback (5 referencias):** `sync` (162), `readahead` (187),
   `fadvise64` (221), `syncfs` (306) y `cachestat` (451). Aquí sí hay efectos
   sobre lectura anticipada, páginas cacheadas o writeback de datos, pero sus
   alcances, FDs y relación con S05/S04 varían. No asumir una sola clasificación
   común.

Las cifras de los grupos suman 19. Los grupos son una guía de revisión, no
decisiones de membresía ni exclusiones.

## Fuentes y límites de evidencia

La fuente primaria del lote para las identidades, números, referencias,
definición de S02, rutas alternativas y UNKNOWN existentes es el manifiesto
target-bound en el commit indicado. La semántica de interfaz se contrastó con
Linux man-pages:

- [`poll(2)`](https://man7.org/linux/man-pages/man2/poll.2.html),
  [`select(2)`](https://man7.org/linux/man-pages/man2/select.2.html),
  [`epoll(7)`](https://man7.org/linux/man-pages/man7/epoll.7.html),
  [`epoll_create(2)`](https://man7.org/linux/man-pages/man2/epoll_create.2.html),
  [`epoll_ctl(2)`](https://man7.org/linux/man-pages/man2/epoll_ctl.2.html),
  [`epoll_wait(2)`](https://man7.org/linux/man-pages/man2/epoll_wait.2.html);
- [`lseek(2)`](https://man7.org/linux/man-pages/man2/lseek.2.html),
  [`flock(2)`](https://man7.org/linux/man-pages/man2/flock.2.html);
- [`sync(2)`](https://man7.org/linux/man-pages/man2/sync.2.html),
  [`readahead(2)`](https://man7.org/linux/man-pages/man2/readahead.2.html),
  [`posix_fadvise(2)`](https://man7.org/linux/man-pages/man2/posix_fadvise.2.html),
  [`sync_file_range(2)`](https://man7.org/linux/man-pages/man2/sync_file_range.2.html),
  [`cachestat(2)`](https://man7.org/linux/man-pages/man2/cachestat.2.html).

Las páginas describen interfaces Linux, pero no prueban alcanzabilidad desde el
workload, selección de esos syscalls por CPython/dependencias, fase, política
activa, transferencia efectiva ni enforcement en el overlay. En particular,
documentación de la API epoll moderna se usa para orientar la lectura de las
variantes `old`, no para afirmar identidad de ABI.

## Estado tras preparar el lote

- Referencias S02 encontradas: **19**.
- Membresías S02 agregadas: **0**.
- Decisiones/exclusiones adjudicadas: **0**.
- Las 19 filas mantienen `candidate_surface_ids=[]` y disposición `UNKNOWN`.
- Manifiesto, ledger, índice, readiness e `inventory.frozen` no se modificaron.
- No se ejecutaron TALOS, probes, suites, parsers, validadores A-PRE ni
  workloads; no se tocó VM, runtime, overlay, lock, corpus, modelos o bases.
- Único archivo creado: este informe. No se hizo commit.

Siguiente paso: revisión humana del criterio de alcance para readiness,
offsets/locks y cache/writeback, seguida de decisiones explícitas por syscall.
