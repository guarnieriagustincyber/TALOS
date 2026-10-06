# Adjudicación documental — lote 10, S10 Classic IPC / coordination

Fecha: 2026-10-01

## 1. Alcance, autoridad e invariantes de decisión

Esta adjudicación resuelve únicamente la relación de **37 candidaturas** con
S10. Se aplica la doctrina y el inventario de
[`031-preparacion-lote-10-s10.md`](./031-preparacion-lote-10-s10.md),
SHA-256 `b5dd1719234184c2a38355835e82516f722c2ac540750ea557e5401ef23ae368`.
Las 12 pistas `poll`/`select`/`epoll` quedan expresamente fuera del lote.

Metodología: **OBSERVE → MEASURE → CORRELATE → CLASSIFY → HUMAN DECISION →
FUTURE CHANGE**. La decisión es de membresía de superficie, no adjudica
disposición global, reachability, efecto observado, enforcement ni uso por
TALOS.

> **S10 = mecanismos clásicos de IPC y coordinación entre procesos/hilos cuyo
> efecto propio sea establecer, transportar o sincronizar comunicación/estado
> compartido mediante primitivas IPC del kernel.**

El resultado global no se infiere de las membresías: cada una de las 385 filas
generales permanece `UNKNOWN`.

## 2. Resultado cuantitativo

- Candidaturas centrales adjudicadas: **37**.
- **YES: 31**, siempre dentro del alcance condicional descrito abajo.
- **NO: 6**, limitado a la relación con S10, no a la disposición syscall-wide.
- **UNKNOWN: 0**; la evidencia documental de interfaz permite decidir cada
  relación central sin inferir variantes no documentadas.
- Memberships S10 materializadas: exactamente las **31** relaciones YES.
- No se materializan las 6 relaciones NO, ni se cambian otras superficies.
- Las **12** pistas de readiness permanecen sin adjudicación/promoción.

## 3. Decisiones individuales

### A. Pipes — 2 candidaturas

| NR / syscall | Decisión S10 | Alcance, evidencia y límites |
|---|---|---|
| 22 `pipe` | **YES — condicional** | La llamada exitosa crea un pipe unidireccional y entrega los dos extremos FD: establecimiento de canal IPC, no I/O de bytes. `read`/`write` posteriores quedan fuera de esta relación (S02); lifecycle de los FDs es dimensión S03. Fallos no crean canal. |
| 293 `pipe2` | **YES — condicional** | Igual alcance de creación que `pipe`; flags válidos no cambian la naturaleza IPC. Registrar `O_CLOEXEC`, `O_NONBLOCK`, `O_DIRECT` (packet mode) y `O_NOTIFICATION_PIPE` como variantes; los dos primeros afectan FD/bloqueo, `O_DIRECT` framing y notification pipe especifica mensajes insertados por el kernel. No adjudica esas operaciones posteriores a S10. Flags inválidos/error no establecen el canal. |

### B. Eventfd — 2 candidaturas

| NR / syscall | Decisión S10 | Alcance, evidencia y límites |
|---|---|---|
| 284 `eventfd` | **YES — condicional** | Creación exitosa del objeto eventfd con contador inicial: mecanismo kernel de espera/notificación para coordinación. No incluye leer/consumir ni escribir/incrementar el contador (S02); FD lifecycle separado (S03). |
| 290 `eventfd2` | **YES — condicional** | Mismo objeto/mecanismo, con flags. Conservar `EFD_SEMAPHORE`, `EFD_NONBLOCK` y `EFD_CLOEXEC`; estos modifican semántica de lectura, bloqueo y FD, pero no convierten todo I/O posterior en S10. Error no crea objeto. |

### C. Futex — 2 candidaturas

| NR / syscall | Decisión S10 | Alcance, evidencia y límites |
|---|---|---|
| 202 `futex` | **YES — condicional** | Las operaciones kernel de wait/wake y variantes de sincronización sobre una palabra futex participan directamente en coordinación de hilos/procesos. Preservar comando, flags, valor esperado, bitset, timeout, resultado e interrupción. `FUTEX_PRIVATE_FLAG` limita el caso a threads del mismo proceso; futex shared requiere palabra en memoria compartida. Los accesos/atomics userspace no son por esto syscalls S10 ni se adjudican. |
| 449 `futex_waitv` | **YES — condicional** | Espera sobre vector de palabras futex y retorno del índice despertado: coordinación S10 cuando una entrada habilita el wait sobre el valor esperado y la operación tiene resultado de espera/wake documentado. Conservar cada `uaddr`, `val`, flags private/shared, clock, timeout, índice/error. La vectorización cambia la correlación por waiter, no la clase conceptual. No extiende a primitivas userspace. |

### D. SysV semaphores — 4 candidaturas

`semctl` se acepta sólo para comandos que mutan/administran el conjunto; las
consultas puras no se cuentan como coordinación S10.

| NR / syscall | Decisión S10 | Alcance, evidencia y límites |
|---|---|---|
| 64 `semget` | **YES — condicional** | Creación u obtención de un conjunto SysV por key; registrar `IPC_CREAT`, `IPC_EXCL`, `nsems`, permisos, namespace y resultado `semid`. La mera identidad de key o error no demuestra un conjunto recién creado. |
| 65 `semop` | **YES — condicional** | Ejecución atómica del vector `sembuf` de decremento/incremento/wait-for-zero sobre el conjunto: operación de sincronización S10. Conservar cantidad/orden, `IPC_NOWAIT`, `SEM_UNDO`, espera, interrupción, `EIDRM` y retorno; `SEM_UNDO` no es lifecycle S11. |
| 66 `semctl` | **YES — condicional** | S10 sólo para comandos de control que cambian/administran estado del conjunto, p. ej. `IPC_SET`, `IPC_RMID`, `SETVAL`, `SETALL`; `IPC_RMID` despierta waiters con error. `IPC_STAT`, `GETVAL`, `GETALL`, `IPC_INFO` y otras lecturas puras quedan fuera de esta relación. Registrar `semid`, `semnum`, comando, argumento, permisos y resultado. |
| 220 `semtimedop` | **YES — condicional** | Las operaciones son las de `semop` y conservan su atomicidad/sincronización; el timeout finito o NULL, `EAGAIN`, `EINTR`, vector y `SEM_UNDO` son ejes propios. Adjudicación independiente de `semop`, no analogía general para syscalls temporizadas. |

### E. SysV shared memory — 4 candidaturas

| NR / syscall | Decisión S10 | Alcance, evidencia y límites |
|---|---|---|
| 29 `shmget` | **YES — condicional** | Creación u obtención del segmento SysV por key/tamaño/flags: establecimiento/identificación del objeto IPC. Preservar `IPC_CREAT`, `IPC_EXCL`, permisos, tamaño, namespace y `shmid`; no incluye acceso posterior a memoria. |
| 30 `shmat` | **YES — condicional; S10 solamente** | Attach exitoso de un segmento SysV al espacio del proceso es el mecanismo que hace utilizable esa memoria IPC; se clasifica S10 por el segmento/relación compartida, no como mapping file-backed S05 ni como memfd/anonymous capability S06. Registrar `shmid`, dirección solicitada/devuelta, `SHM_RND`, `SHM_RDONLY`, `SHM_REMAP`, `SHM_EXEC`, permisos y resultado. No materializa S05/S06. El contenido leído/escrito después no es automáticamente S10. |
| 67 `shmdt` | **YES — condicional** | Detach exitoso de la región previamente adjunta modifica la relación de acceso al segmento compartido; pertenece a la gestión del mecanismo SysV IPC. Registrar dirección devuelta por `shmat`, contadores/estado del segmento y error. No es lifecycle de FD ni un `munmap` genérico adjudicado a S05. |
| 31 `shmctl` | **YES — condicional** | S10 para comandos que administran o mutan el segmento, p. ej. `IPC_RMID`, `IPC_SET`, `SHM_LOCK`/`SHM_UNLOCK`; comandos de consulta como `IPC_STAT`, `SHM_STAT` e información del sistema no son por sí mismos coordinación S10. Registrar comando, `shmid`, permisos, estado delete-marked y retorno. No adjudica superficies de mapping/backing. |

**Frontera S05/S06:** aunque `shmat` produce una región mapeada, SysV shared
memory no es por ese hecho un objeto file-backed de S05 ni memfd/anonymous
capability de S06. Su relación adjudicada aquí es S10; mappings o recursos
distintos requieren evidencia y decisión propias.

### F. SysV message queues — 4 candidaturas

| NR / syscall | Decisión S10 | Alcance, evidencia y límites |
|---|---|---|
| 68 `msgget` | **YES — condicional** | Creación u obtención de una cola kernel SysV; registrar key, `IPC_CREAT`/`IPC_EXCL`, permisos, IPC namespace y resultado. |
| 69 `msgsnd` | **YES — condicional** | Envío efectivo de un mensaje a una SysV queue es transporte IPC S10. Conservar `msqid`, tipo, tamaño, `IPC_NOWAIT`, bloqueo/timeout indirecto, errores y resultado. El payload no cambia la clasificación primaria del mecanismo queue; no es socket, AF_UNIX ni `SCM_RIGHTS`, y no se crea una membership S02. |
| 70 `msgrcv` | **YES — condicional** | Recepción efectiva desde SysV queue es transporte IPC S10. Conservar tipo/selector, tamaño, `IPC_NOWAIT`, `MSG_NOERROR`, `MSG_EXCEPT`, `MSG_COPY` cuando soporte/versionado aplique, retorno/truncamiento/error. No adjudica el payload a S02 por analogía con FD I/O. |
| 71 `msgctl` | **YES — condicional** | Sólo comandos que administran o mutan la cola, p. ej. `IPC_SET` e `IPC_RMID`; consultas (`IPC_STAT`, `MSG_STAT`/`MSG_INFO`) quedan fuera de la relación S10. Registrar comando, permisos, queue state y resultado; `IPC_RMID` afecta waiters pero no es lifecycle de proceso. |

### G. Signals — 11 candidaturas iniciales

El envío/recepción de una señal es una primitiva de notificación/coordination
cuando la variante efectivamente comunica con otro proceso/hilo. Configurar
estado local o consultar estado no se vuelve S10 por estar relacionado con
señales. El efecto secundario de terminar/parar un proceso no convierte esta
adjudicación en S11.

| NR / syscall | Decisión S10 | Alcance, evidencia y límites |
|---|---|---|
| 62 `kill` | **YES — condicional** | S10 cuando envía señal no nula al proceso/grupo objetivo; registrar semántica de `pid` positivo, cero, -1 o menor de -1, permisos, señal y retorno. `sig=0` sólo comprueba existencia/permisos y queda fuera del YES. Señales que causan terminación pueden cruzar S11 por el efecto, no por esta decisión. |
| 200 `tkill` | **YES — condicional** | Envío efectivo de señal a TID para notificación entre hilos/procesos; excluir `sig=0` de la transferencia de señal, correlacionar TID/actor, permisos, resultado y errores. No generalizar a lifecycle S11. |
| 234 `tgkill` | **YES — condicional** | Envío efectivo a TID dentro del TGID indicado; registrar ambos IDs, señal no nula, validación de pertenencia, permisos y retorno. Señal nula como comprobación no es coordinación transmitida. |
| 424 `pidfd_send_signal` | **YES — condicional** | Envío de señal al proceso/thread referenciado por pidfd; conservar identidad estable del pidfd, `sig`, `siginfo`, flags/scope (incluidos flags de thread/group cuando target ABI los admite), PID namespace, autorización y resultado. `sig=0` o error no demuestra señal entregada. |
| 13 `rt_sigaction` | **NO — S10** | Examina/cambia la disposición de señal por proceso; configura cómo reaccionar a una futura entrega, no envía ni espera una comunicación. `SA_SIGINFO`, `SA_ONSTACK`, `SA_RESTART`, `SIGCHLD` y el handler son estado/configuración; su efecto posterior no se atribuye a esta llamada. |
| 14 `rt_sigprocmask` | **NO — S10** | Consulta/modifica máscara de señales del thread llamante (`SIG_BLOCK`, `SIG_UNBLOCK`, `SIG_SETMASK`); estado local de scheduling/entrega, no mecanismo interproceso por sí mismo. Puede preparar una espera, que se analiza en syscall separada. |
| 127 `rt_sigpending` | **NO — S10** | Consulta el conjunto de señales pending del llamante. Informa estado local; no envía, recibe ni sincroniza por sí mismo una señal. El origen potencial de las pendientes requiere correlación aparte. |
| 128 `rt_sigtimedwait` | **YES — condicional** | Espera y consume una señal pending del conjunto indicado, con timeout; es recepción/coordination S10 cuando esa señal es el evento intercambiado con otro actor. Registrar conjunto bloqueado, origen/`siginfo` si disponible, timeout, señal devuelta, poll de timeout, `EINTR` y resultado. Una señal generada localmente no prueba intercambio interproceso. |
| 129 `rt_sigqueueinfo` | **YES — condicional; membership S10 nueva** | Envía señal y datos asociados al thread group/TGID objetivo; S10 para envío exitoso a otro actor con señal efectiva no nula. Registrar TGID, señal, `siginfo`/`si_code`, permisos, límites de cola (`EAGAIN`) y retorno. `sig=0` sólo comprueba; llamadas propias no demuestran comunicación entre procesos. |
| 297 `rt_tgsigqueueinfo` | **YES — condicional; membership S10 nueva** | Como `rt_sigqueueinfo`, dirigido al TID concreto dentro del TGID. Relación S10 sólo para señal/datos enviados efectivamente a otro actor; preservar TGID/TID, `siginfo`, reglas de `si_code`, permisos, saturación/errores y resultado. |
| 131 `sigaltstack` | **NO — S10** | Configura/consulta stack alternativo local del thread para ejecutar handlers; `SS_DISABLE`/`SS_AUTODISARM`, dirección y tamaño son estado de proceso/thread, no transporte ni sincronización IPC. La pila/handler no promueven la syscall a S10. |

### H. Candidaturas adicionales — 9 candidaturas

| NR / syscall | Decisión S10 | Alcance, evidencia y límites |
|---|---|---|
| 240 `mq_open` | **YES — condicional** | Creación/apertura de POSIX message queue nombrada; establecer objeto IPC compartible por nombre. Distinguir `O_CREAT`, `O_EXCL`, flags `O_NONBLOCK`, mode/atributos, queue descriptor y errores. El FD resultante/lifecycle se mantiene aparte en S03. |
| 241 `mq_unlink` | **YES — condicional** | Remueve el nombre del objeto POSIX queue para futuras aperturas; la cola existente puede persistir mientras esté abierta. Es administración del canal IPC, no close/lifecycle FD ni mutación filesystem S04. |
| 242 `mq_timedsend` | **YES — condicional** | Envío efectivo de mensaje/prioridad a la POSIX queue; registrar descriptor, bytes, prioridad, timeout, `O_NONBLOCK`, `EINTR`, `ETIMEDOUT`, retorno. Payload de cola no crea membership S02 automáticamente. |
| 243 `mq_timedreceive` | **YES — condicional** | Recepción efectiva desde POSIX queue; registrar descriptor, buffer/tamaño, prioridad retornada, timeout, `O_NONBLOCK`, errores y longitud efectivamente recibida. Es transporte por mecanismo IPC S10; descriptor lifecycle S03 separado. |
| 244 `mq_notify` | **YES — condicional** | Registro/cancelación de notificación de llegada de mensaje a cola vacía: mecanismo de coordinación S10. Conservar `sigevent`, modo thread/signal, ownership del registro, carrera de notificación, descriptor/queue y resultado. No confundir el signal usado como aviso con process lifecycle S11. |
| 245 `mq_getsetattr` | **NO — S10** | Consulta/actualiza atributos de una cola ya abierta; principalmente observa/configura estado de la descripción de cola (en especial `O_NONBLOCK`), no crea, transporta ni sincroniza un evento de comunicación por sí mismo. El modo que habilita un send/receive posterior es variante de esas llamadas, no de ésta. FD/status-flag es cruce descriptivo S03, no adjudicado aquí. |
| 130 `rt_sigsuspend` | **YES — condicional** | Sustituye temporalmente la máscara y suspende el thread hasta entrega de una señal no bloqueada: recepción/wait S10 si la señal es evento de coordinación recibido. Registrar máscara temporal, señal/actor si correlacionable, retorno normalmente interrumpido y errores. La modificación/estado de máscara no es una segunda membership aparte. |
| 15 `rt_sigreturn` | **NO — S10** | Restaura el contexto previamente guardado al retornar de handler/trampoline. Es retorno de ABI/contexto de ejecución, no envío, recepción ni sincronización IPC; no clasificarlo por aparecer tras una señal. |

## 4. Cruces y exclusiones

Los cruces son descriptivos y no adjudican otras superficies:

- **S02:** `read`/`write` posterior en pipe/eventfd es transferencia payload
  separada; las llamadas de establecimiento aquí adjudicadas no absorben ese
  I/O. Los mensajes SysV/POSIX son payload transportado por la propia primitiva
  IPC S10; no se trasladan automáticamente a la doctrina S02 de payload I/O
  por descriptor.
- **S03:** FDs de pipes, eventfd y POSIX MQ requieren seguimiento de FD aparte.
  Crear/abrir el objeto no adjudica close/dup/fcntl/exec ni transforma todas
  estas llamadas en S03.
- **S05/S06:** `shmat` mapea segmento SysV, pero no es por ello file-backed ni
  memfd; no se materializan relaciones S05/S06. Backing de otras regiones
  futex se decide por el objeto y evidencia concreta, no por futex.
- **S07/S08:** estas colas, pipes, señales y shared memory no son socket IP ni
  endpoint AF_UNIX. `socketpair`/AF_UNIX permanecen bajo adjudicación S08
  existente y no se reabren.
- **S09:** ninguna de estas 37 decisiones adjudica `SCM_RIGHTS`. El paso de FDs
  continúa en S09; presencia de AF_UNIX tampoco crea S10 automáticamente.
- **S11:** señales enviadas pueden terminar/parar/reanudar objetivos y las
  señales de hijo reflejan eventos de proceso. Esta relación S10 es sólo la
  primitiva de señalización/espera; creación/exec/terminación siguen separadas.

## 5. Pistas `poll`/`select`/`epoll` conservadas

Las **12** pistas siguen sin decisión ni promoción, sin membresía S10 nueva:

- `poll` 7, `select` 23, `pselect6` 270, `ppoll` 271;
- `epoll_create` 213, `epoll_ctl_old` 214, `epoll_wait_old` 215,
  `epoll_wait` 232, `epoll_ctl` 233, `epoll_pwait` 281,
  `epoll_create1` 291, `epoll_pwait2` 441.

Readiness de un objeto no equivale a establecer/transmitir IPC. Las dos
variantes epoll `old` requieren ABI específico; no se infiere equivalencia con
la interfaz moderna. Se conserva íntegra la decisión de analizarlas después.

## 6. Materialización y límites del checkpoint

El manifiesto recibe únicamente las 31 relaciones S10 YES, con `scope`,
`rationale`, referencia a este checkpoint y `disposition_unchanged: UNKNOWN`,
siguiendo la convención de adjudicación por fila. `rt_sigqueueinfo` 129 y
`rt_tgsigqueueinfo` 297 se agregan a S10 porque estaban expresamente incluidas
entre las 28 candidaturas de preparación/directiva y reciben YES; no son una
promoción incidental. Las seis decisiones NO se registran aquí como
decisiones relacionales, sin convertirlas en exclusiones syscall-wide. No se
crean relaciones para las 12 pistas ni para superficies cruzadas.

Las disposiciones generales no cambian a YES/NO/OBSERVED/BLOCKED. Cada
`disposition_status` sigue UNKNOWN. Esta adjudicación no cierra reachability,
finite partitions, efectos de evento, permisos en el target o rutas del
workload.

## 7. Evidencia documental y límites de fuente

- **Identidad target-bound:** el manifiesto preserva la tabla nativa x86_64
  target-bound de 385 filas y hash
  `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
  Esa evidencia fija nombres/números del target, no demuestra ejecución,
  configuración de kernel ni efecto observado.
- **Linux man-pages 6.19, snapshot publicado 2026-09-09**, consultado para
  semántica de interfaz general: [`pipe(2)`](https://man7.org/linux/man-pages/man2/pipe.2.html),
  [`eventfd(2)`](https://man7.org/linux/man-pages/man2/eventfd.2.html),
  [`futex(2)`](https://man7.org/linux/man-pages/man2/futex.2.html),
  [`futex_waitv(2)`](https://man7.org/linux/man-pages/man2/futex_waitv.2.html),
  [`semget(2)`](https://man7.org/linux/man-pages/man2/semget.2.html),
  [`semop(2)`](https://man7.org/linux/man-pages/man2/semop.2.html),
  [`semctl(2)`](https://man7.org/linux/man-pages/man2/semctl.2.html),
  [`shmget(2)`](https://man7.org/linux/man-pages/man2/shmget.2.html),
  [`shmat(2)`/`shmdt(2)`](https://man7.org/linux/man-pages/man2/shmop.2.html),
  [`shmctl(2)`](https://man7.org/linux/man-pages/man2/shmctl.2.html),
  [`msgget(2)`](https://man7.org/linux/man-pages/man2/msgget.2.html),
  [`msgsnd(2)`/`msgrcv(2)`](https://man7.org/linux/man-pages/man2/msgop.2.html),
  [`msgctl(2)`](https://man7.org/linux/man-pages/man2/msgctl.2.html),
  [`mq_overview(7)`](https://man7.org/linux/man-pages/man7/mq_overview.7.html),
  [`mq_getsetattr(2)`](https://man7.org/linux/man-pages/man2/mq_getsetattr.2.html),
  [`mq_notify(3)`](https://man7.org/linux/man-pages/man3/mq_notify.3.html),
  [`kill(2)`](https://man7.org/linux/man-pages/man2/kill.2.html),
  [`pidfd_send_signal(2)`](https://man7.org/linux/man-pages/man2/pidfd_send_signal.2.html),
  [`rt_sigqueueinfo(2)`/`rt_tgsigqueueinfo(2)`](https://man7.org/linux/man-pages/man2/rt_sigqueueinfo.2.html),
  [`sigaction(2)`](https://man7.org/linux/man-pages/man2/sigaction.2.html),
  [`rt_sigprocmask(2)`](https://man7.org/linux/man-pages/man2/rt_sigprocmask.2.html),
  [`rt_sigtimedwait(2)`](https://man7.org/linux/man-pages/man2/sigtimedwait.2.html),
  [`sigaltstack(2)`](https://man7.org/linux/man-pages/man2/sigaltstack.2.html).
- Los manuales describen interfaces Linux generales. No sustituyen UAPI/kernel
  source versionados para flags, ABI, soporte y configuración target; los
  límites de versión/operación quedan expresos en cada relación.
- No se consultaron probes históricos ni datos dinámicos para adjudicar estas
  relaciones. No se afirma reachability ni uso por TALOS.

## 8. Invariantes y verificación final

- 37 candidaturas: **31 YES, 6 NO, 0 UNKNOWN**.
- Sólo 31 memberships S10 YES materializadas; seis NO permanecen como
  decisiones de superficie, sin exclusión syscall-wide.
- 12 pistas `poll`/`select`/`epoll`: preservadas sin promoción.
- Disposiciones generales: **385/385 UNKNOWN**; **0** disposiciones finales.
- `inventory.frozen=false`; A-PRE-0 **NOT READY**; A-PRE-1
  **NOT AUTHORIZED / NOT EXECUTED**.
- Ledger sin cambios; `requirements.lock`, E5/Qwen, corpus, modelos, bases
  protegidas, código funcional e infraestructura sin modificación.
- No hubo TALOS, FastAPI, workload, proveedor, benchmark, probe, test, suite,
  VM, runtime ni otra actividad dinámica.
- No se avanzó a S11. Lote S10 cerrado documentalmente bajo estos alcances.
