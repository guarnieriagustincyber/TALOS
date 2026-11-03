# Preparación documental — lote S10, Classic IPC / coordination

Fecha: 2026-10-01

## 1. Objetivo y alcance

Preparar las candidaturas documentales S10 para una decisión humana posterior.
Este checkpoint no adjudica relaciones, no asigna YES/NO/UNKNOWN, no promueve
pistas, no materializa memberships y no altera disposiciones globales.

Metodología: **OBSERVE → MEASURE → CORRELATE → CLASSIFY → HUMAN DECISION →
FUTURE CHANGE**.

## 2. Doctrina provisional

> **S10 = mecanismos clásicos de IPC y coordinación entre procesos/hilos cuyo
> efecto principal sea establecer, transportar o sincronizar comunicación/
> estado compartido mediante primitivas IPC del kernel, excluyendo el
> transporte específico de file descriptors de S09 y separando los efectos de
> payload I/O, filesystem, networking y process lifecycle.**

La superficie describe el canal, objeto o mecanismo de sincronización; no
absorbe automáticamente la transferencia de payload, el ciclo de vida de un
descriptor, la identidad de una señal o las consecuencias de un proceso. Un
syscall que puede participar depende de argumentos, flags, objeto y operación.

## 3. Identidad y autoridad documental

- Repositorio: `/media/agustin/Laboratorio/study-engie`.
- HEAD observado: `f81134fc2293916210d53c8065f3a0049e52b0b4`.
- La tabla nativa x86_64 target-bound registrada contiene 385 filas; SHA-256
  declarado: `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
- Los números y nombres de abajo se transcriben del
  `syscall_disposition_contract.rows` del manifiesto existente. Es autoridad
  de identidad target-bound para este inventario; no demuestra reachability,
  uso por TALOS ni efecto observado.
- El índice ya tenía cambios preexistentes ajenos. Se conserva su contenido y
  se añade únicamente una línea para este checkpoint.

## 4. Candidaturas iniciales

Hay **28 candidaturas iniciales** en la directiva. La lista siguiente preserva
las familias y separa sus preguntas documentales; las agrupaciones no son
adjudicaciones.

| Familia | NR / syscall | Pregunta documental / variantes que pueden cambiar la relación |
|---|---|---|
| Pipes | 22 `pipe`; 293 `pipe2` | ¿La creación del canal/los dos extremos constituye S10? Distinguir syscall de creación, resultado FD y posterior `read`/`write`. Para `pipe2`, registrar `O_CLOEXEC` y `O_NONBLOCK`, flags válidos y resultado/error. |
| Eventfd | 284 `eventfd`; 290 `eventfd2` | Separar creación del objeto contador de las lecturas/escrituras que consumen o incrementan su contador. Revisar valor inicial, `EFD_SEMAPHORE`, `EFD_NONBLOCK`, `EFD_CLOEXEC`, operación bloqueante y resultado. |
| Futex | 202 `futex`; 449 `futex_waitv` | Delimitar wait/wake/requeue y operaciones atómicas pertinentes; distinguir `FUTEX_PRIVATE_FLAG` frente a futex compartido, dirección/valor observado, vector de waitv, timeout, bitset y retorno/error. No extrapolar a atomics o locks enteramente userspace. |
| SysV semaphores | 64 `semget`; 65 `semop`; 66 `semctl` | Separar identificación/creación de conjunto, operaciones atómicas y control. Registrar key/semid, número de semáforos, comandos/flags, vector `sembuf`, `IPC_CREAT`/`IPC_EXCL`, permisos, `SEM_UNDO`, `IPC_RMID` y errores. |
| SysV shared memory | 29 `shmget`; 30 `shmat`; 67 `shmdt`; 31 `shmctl` | Separar creación/selección del segmento, attach, detach y control (`IPC_RMID`, `IPC_STAT`, flags de attach y dirección/resultado). El acceso posterior a memoria no es por sí mismo S10. |
| SysV message queues | 68 `msgget`; 69 `msgsnd`; 70 `msgrcv`; 71 `msgctl` | Distinguir creación/identificación, envío, recepción y control. Registrar key/msqid, permisos y flags, tipo de mensaje, tamaño solicitado/retornado, `IPC_NOWAIT`, `MSG_NOERROR`, `MSG_EXCEPT`, `MSG_COPY` si aplica, tiempos y errores. |
| Señales: envío | 62 `kill`; 200 `tkill`; 234 `tgkill`; 424 `pidfd_send_signal` | ¿Cuándo el envío dirigido a proceso o hilo constituye coordinación S10? Registrar identificador/objetivo, señal (incluida señal nula si pertinente), `tgid`/`tid`, pidfd, `siginfo`, flags y retorno. No inferir creación/terminación del proceso. |
| Señales: disposición, máscara y estado | 13 `rt_sigaction`; 14 `rt_sigprocmask`; 127 `rt_sigpending`; 131 `sigaltstack` | Separar instalar/consultar handlers, bloquear/desbloquear señales, consultar pendientes y configurar stack alternativo. Distinguir configuración local del proceso de intercambio/coordinación entre participantes; registrar `how`, sets, flags, old/new values, stack y errores. |
| Señales: espera y cola | 128 `rt_sigtimedwait`; 129 `rt_sigqueueinfo`; 297 `rt_tgsigqueueinfo` | La espera/recepción de señales difiere de la configuración; los dos `queueinfo` aparecen en la tabla target-bound aunque no están actualmente listados en la matriz S10 del manifiesto. Analizar si la señal se dirige a proceso/hilo y si `siginfo` cambia la semántica; preservar timeout, señal bloqueada, target y resultado. |

### 4.1 Señales fuera de la lista inicial y fronteras

`rt_sigprocmask` y `rt_sigtimedwait` dan contexto para bloqueo/espera; no
justifican por analogía incorporar toda syscall `rt_sig*`. La tabla S10 actual
del manifiesto contiene también `rt_sigsuspend` (130) y `rt_sigreturn` (15);
se retienen como **pistas existentes adicionales**, sin decidirlas. En
particular, `rt_sigreturn` es una transición de retorno desde el contexto de
señal y puede no ser una primitiva de coordinación; requiere una decisión
expresa y evidencia de ABI antes de incluirla.

## 5. Candidaturas adicionales vistas en el inventario

La matriz S10 existente enumera candidaturas adicionales que deben quedar
visibles para la futura revisión, sin promoverlas ni completar variantes por
analogía:

| NR / syscall | Motivo para presentar a revisión | Límite / posible cruce |
|---|---|---|
| 220 `semtimedop` | Variante temporizada de operaciones SysV semaphore relacionada con `semop`. | Debe cerrarse como syscall/variante propia; timeout, retorno parcial e interrupción pueden cambiar lo que se mide. S10 candidato preexistente, no nueva membresía. |
| 240 `mq_open`; 241 `mq_unlink`; 242 `mq_timedsend`; 243 `mq_timedreceive`; 244 `mq_notify`; 245 `mq_getsetattr` | API POSIX message queue: establecimiento/eliminación del objeto, envío/recepción, notificación y atributos. | Distinguir creación (`O_CREAT`/`O_EXCL`), nombre y atributos, `O_NONBLOCK`, prioridades, timeout, notificación/señal y unlink frente a cierre de la cola. Son candidatos S10 preexistentes; revisar su condición/entidad sin adjudicar toda la familia de una vez. |
| 130 `rt_sigsuspend`; 15 `rt_sigreturn` | Ya aparecen en la lista S10 del manifiesto, aunque fuera de la lista mínima pedida. | `rt_sigsuspend` espera señales desbloqueadas; `rt_sigreturn` restaura contexto de señal. La segunda no equivale automáticamente a coordinación entre procesos; diferenciar comportamiento del ABI y mecanismo de retorno. |

La presencia en la lista `surfaces[].syscalls` o en
`candidate_surface_ids` es únicamente contexto candidato. En este snapshot las
filas S10 anteriores indican `UNREVIEWED`; no es una adjudicación ni un estado
de observación.

## 6. Pistas adicionales de coordinación por readiness

Estas syscalls son pistas dudosas, no se agregan a la lista de candidaturas
adjudicables en esta preparación. Una interfaz de readiness informa
disponibilidad de objetos ya existentes; no establece necesariamente IPC ni
transfiere payload. Se señalan para que una futura decisión de alcance no las
omita ni las trate como S10 por defecto.

| NR / syscall | Clasificación de la pista | Pregunta / límite |
|---|---|---|
| 7 `poll`; 23 `select`; 270 `pselect6`; 271 `ppoll` | Pista dudosa | Espera/multiplexación de readiness de FDs; separar timeout, máscara de señales en variantes `p*`, eventos devueltos y recurso vigilado. Posible S10 sólo si la doctrina incluye coordinación de eventos genérica. |
| 213 `epoll_create`; 214 `epoll_ctl_old`; 215 `epoll_wait_old`; 232 `epoll_wait`; 233 `epoll_ctl`; 281 `epoll_pwait`; 291 `epoll_create1`; 441 `epoll_pwait2` | Pista dudosa; ABI `old` requiere tratamiento propio | Separar creación de instancia/FD, actualización de interest list y espera de readiness. Para las variantes `old`, no inferir estructura ABI de la API moderna; para las demás, considerar flags de creación, edge/level, timeout, máscara de señales y FDs registrados. |

`flock` (73) es una pista relacionada con coordinación/contención entre
procesos sobre un archivo, pero su objeto principal es un advisory lock
file-backed. Se clasifica aquí como **fuera de S10 provisionalmente / frontera
con filesystem**, no como candidatura del lote: no convertir este apunte en
una adjudicación ni abrir un lote S04.

## 7. Distinciones y cruces obligatorios

| Familia / dimensión | Cruces que describir en la futura adjudicación | Separación requerida |
|---|---|---|
| `pipe`/`pipe2` y `eventfd*` | S02 para payload/operaciones `read`/`write`; S03 para creación y lifecycle del FD. | Canal/objeto de coordinación no es la transferencia de payload ni el `close`/`dup`/`fcntl`/herencia posterior. |
| Futex | S10 y memoria compartida; S05/S06 sólo si evidencia específica establece un mapeo o backing file/memfd relevante; S11 si una transición de proceso es parte del caso. | La palabra “memoria” no adjudica S05/S06: separar dirección, backing y ownership. |
| SysV shared memory | S10 para gestión/attach del segmento; S05/S06 como distinciones de backing/mapping cuando sean pertinentes. | No clasificar el acceso genérico posterior como IPC ni confundir segmento SysV con file-backed mapping o memfd. |
| SysV/POSIX message queues y semáforos | S02 sólo por una dimensión de transferencia efectiva de bytes que el alcance S02 admita; S03 si hay FD POSIX queue; S11 si aparece transición/identidad de proceso. | Los mensajes y operaciones de semáforo no son `SCM_RIGHTS`; no inferir la superficie por la presencia de un objeto de cola. |
| Señales | S11 por proceso/ejecución/terminación si aplica; S10 sólo por la dimensión de notificación/espera coordinadora que se decida. | Envío, recepción, estado/configuración de señal y lifecycle del proceso son preguntas separadas. |
| AF_UNIX / sockets | S08 para el endpoint AF_UNIX ya adjudicado; S07 para red IP según la adjudicación previa. | No reabrir `socketpair` ni adjudicar sockets como S10 por el hecho de servir IPC. |
| Paso de FDs | S09 para `SCM_RIGHTS` en las variantes ya adjudicadas; S08 puede describir el transporte AF_UNIX. | No reetiquetar `sendmsg`/`recvmsg`/mmsg ni el paso de capacidades como S10. Cruce descriptivo no crea membership adicional. |

`S03` tampoco se deduce porque una operación produzca un FD; requiere separar
creación de recurso y lifecycle/hygiene posterior. `read`/`write` sobre pipe,
eventfd o cola no se incluyen aquí por inferencia: payload I/O pertenece a la
dimensión S02. Señales no implican automáticamente S11, y S11 no implica S10.

## 8. Exclusiones y límites de candidatura

- No reabrir S08: `socketpair` y las operaciones AF_UNIX pertenecen al
  expediente ya adjudicado S08; el canal AF_UNIX no transforma S09 ni S08 en
  S10 automáticamente.
- No reabrir S09: `SCM_RIGHTS` y `sendmsg`/`recvmsg`/`sendmmsg`/`recvmmsg`
  cuando transportan FDs son capability passing S09 según la adjudicación
  existente, no una nueva candidatura S10.
- `SCM_CREDENTIALS` no transfiere capacidades FD; tampoco basta para decidir
  coordinación S10.
- No incorporar syscalls de proceso, filesystem, networking o readiness por
  mera proximidad. Las pistas del apartado 6 quedan separadas de las 37
  candidaturas centrales.
- No extrapolar entre `pipe`/`pipe2`, `eventfd`/`eventfd2`, futex wait/wake,
  los comandos de control SysV, variantes temporizadas/vectorizadas, ni las
  señales dirigidas a proceso/hilo.
- Los errores, interrupciones, retornos parciales, bloqueos, permisos, flags
  inválidos y estados del objeto deben conservarse como variantes; un nombre
  de syscall no demuestra que se estableció o transmitió comunicación.

## 9. Ejes de variantes para adjudicación humana

Registrar sólo ejes que puedan alterar pertenencia o resultado: syscall/ABI y
variante; operación/command; objeto y namespace/ID; peer, proceso o hilo;
flags y permisos; creación frente a uso/control; dirección de transferencia;
payload frente a sincronización; FD retornado y su estado inicial; backing de
memoria; wait/wake y estado compartido; timeout/interrupción; retorno,
transferencia parcial y error. No construir el producto cartesiano de todos
los ejes.

## 10. Evidencia, fuentes y límites

- **Target-bound:** `files/A_PRE_0_SURFACE_MANIFEST.json`, tabla nativa x86_64
  target-bound y listas actuales de candidatos. El manifiesto registra la
  adquisición de tabla de fuente Ubuntu/Linux 7.0.0-34 y hash correspondiente;
  la verificación de firma del paquete de fuente consta como no realizada.
  Números/nombres se usan sólo para identificar candidatos.
- **Man-pages como referencias semánticas a cotejar:** `pipe(2)`,
  `eventfd(2)`, `futex(2)`, `futex_waitv(2)` si está disponible en la versión
  de man-pages del target, `semget(2)`, `semop(2)`, `semctl(2)`,
  `shmget(2)`, `shmat(2)`, `shmop(2)`, `shmctl(2)`, `msgget(2)`,
  `msgop(2)`, `msgctl(2)`, `mq_overview(7)`, `mq_open(3)`, `mq_send(3)`,
  `mq_receive(3)`, `mq_notify(3)`, `signal(7)`, `kill(2)`,
  `pidfd_send_signal(2)`, `rt_sigaction(2)`/`sigaction(2)`,
  `sigprocmask(2)`, `sigwaitinfo(2)`, `sigaltstack(2)`, `poll(2)`,
  `select(2)`, `epoll(7)` y páginas específicas por syscall.
- **Kernel/UAPI versionados a cotejar:** Linux v7.0 target source para números,
  wrappers, estructuras y variantes; el source table por sí solo no acredita
  comportamiento de kernel, permisos ni configuración disponible.
- Las referencias a páginas manuales son una guía de verificación de la fase
  de adjudicación; este checkpoint no afirma una nueva recuperación ni
  validación de esas páginas. La semántica resumida es orientación documental,
  no evidencia dinámica ni de uso real por TALOS.
- No se infiere soporte efectivo de SysV/POSIX IPC, familias, flags,
  reachability desde workload, fase, resultado, enforcement o interacción
  entre procesos de una mera entrada en la tabla.

## 11. Preguntas concretas para decisión humana

1. ¿La creación de pipe/eventfd pertenece a S10 independientemente de que haya
   I/O posterior, y qué condiciones de éxito/flags deben conservarse?
2. ¿Qué operaciones futex/waitv califican como coordinación inter-hilo o
   interproceso, y cómo se evidencia private/shared sin inferir por dirección?
3. ¿Se acepta SysV shared memory dentro de S10 para create/attach/control,
   separando explícitamente los accesos y backing posteriores?
4. ¿Qué variantes de SysV y POSIX message queues/semaphores entran, incluidos
   timeouts, waits, notificación, namespaces y control/destrucción?
5. ¿Qué clases de señales se consideran mecanismo de coordinación: send,
   queue, wait/receive, pending, mask/disposition, suspend y stack?
6. ¿`rt_sigreturn` queda excluida como retorno de contexto o requiere otra
   relación acotada? ¿Qué evidencia del ABI target permite resolverlo?
7. ¿Readiness genérico (`poll`/`select`/`epoll`) es S10 o permanece como pista
   separada? ¿Cómo tratar los syscalls epoll `old` sin analogía ABI?
8. Para cada cruce, ¿qué observación distingue establecimiento del mecanismo,
   transmisión/recepción de payload, adquisición/lifecycle FD, señal enviada
   y efecto producido?
9. ¿Qué límites por resultado, error, interrupción, timeout, permisos,
   operación y versión bastan para cerrar una variante sin cerrar familias
   enteras?

## 12. Conteos e invariantes A-PRE-0

- **28** candidaturas iniciales de la directiva.
- **9** candidaturas adicionales derivadas del inventario S10 ya existente:
  `semtimedop`, seis syscalls POSIX message queue, `rt_sigsuspend` y
  `rt_sigreturn`.
- **37** candidaturas centrales presentadas para futura adjudicación; todas
  quedan sin decisión en este documento.
- **12** pistas dudosas de readiness (poll/select/pselect6/ppoll y ocho
  syscalls epoll, incluyendo las dos variantes `old`) quedan fuera de ese
  conteo y sin promoción.
- `rt_sigqueueinfo` (129) y `rt_tgsigqueueinfo` (297) se incluyen por la
  directiva como candidaturas iniciales; el manifiesto target-bound no las
  lista actualmente en la matriz de superficie S10.
- Disposiciones globales: **385/385 UNKNOWN**, cero disposiciones finales.
- `inventory.frozen=false`; A-PRE-0 **NOT READY**; A-PRE-1
  **NOT AUTHORIZED / NOT EXECUTED**.
- Manifiesto y ledger no se modifican; no se adjudican memberships y no se
  alteran recursos protegidos.
- Sin TALOS, FastAPI, workloads, proveedores, corpus, benchmarks, bases de
  datos protegidas, probes, VM, runtime, suites, tests ni ejecución dinámica.
- Estado final de este lote: **listo para adjudicación humana**; no avanzar a
  la adjudicación S10 ni a otra superficie sin la directiva correspondiente.
