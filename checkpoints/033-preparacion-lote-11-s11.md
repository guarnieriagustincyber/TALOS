# Preparación documental — lote S11, process tree / exec / termination

Fecha: 2026-10-01

## 1. Objetivo y estado

Preparar candidaturas target-bound para futura adjudicación humana de S11. Este
checkpoint **no asigna YES/NO/UNKNOWN**, no adjudica ni materializa memberships,
no cambia las 385 disposiciones generales y no congela el inventario.

Metodología: **OBSERVE → MEASURE → CORRELATE → CLASSIFY → HUMAN DECISION →
FUTURE CHANGE**.

Estado inicial de cada candidatura y lead: **UNREVIEWED / PENDING HUMAN
ADJUDICATION** en este lote. Una candidatura significa que la semántica merece
decisión; no es una conclusión de pertenencia.

## 2. Baseline verificada

HEAD observado: `f81134fc2293916210d53c8065f3a0049e52b0b4`. Antes de editar se
verificaron los invariantes exigidos para el estado posterior a S10:

- Checkpoint 032 adjudica las **37** candidaturas S10: **31 YES**, **6 NO**,
  **0 UNKNOWN** dentro del lote.
- Las 31 memberships S10 YES están materializadas; las seis relaciones NO no
  están en la lista de S10.
- Las **12** pistas `poll`/`select`/`epoll` están fuera de la lista S10 y sin
  promoción.
- Manifiesto de partida SHA-256:
  `49ec91d7e567bd812860543c4f0262e52fbb4222c81b0ad5a56dd440a69ac7a6`.
- Ledger SHA-256:
  `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42`.
- `requirements.lock` SHA-256:
  `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70`.
- Registro: 385 filas target-bound, **385 UNKNOWN**, **0** disposiciones
  finales; `inventory.frozen=false`; ledger `NOT_READY`.
- A-PRE-0 permanece **NOT READY**. La especificación registra A-PRE-1
  **NOT EXECUTED** y autorización **PENDING / NOT AUTHORIZED**.

El worktree ya tenía cambios ajenos, incluido el índice y manifiesto; no se
limpian ni revierten. El checkpoint se prepara desde la baseline canónica
verificada, no desde una suposición de worktree limpio.

## 3. Doctrina de trabajo S11

> **S11 = creación, clonación, reemplazo/ejecución, espera y terminación del
> árbol de procesos/hilos, incluyendo las transiciones de ejecución asociadas
> al proceso.**

La futura decisión debe clasificar el efecto propio y la variante del syscall.
No atribuir a S11 todas las operaciones realizadas después por un descendiente,
ni convertir un identificador de proceso, señal ordinaria o descriptor en
membresía S11 por nombre.

La superficie S11 existente describe el ciclo de vida de procesos/hilos y el
seguimiento completo de descendientes. Esta preparación distingue candidaturas
centrales de leads de borde para que la adjudicación humana pueda decidirlos
sin ampliar el lote inadvertidamente.

## 4. Candidaturas centrales

Hay **17 candidaturas centrales** para revisión humana: las diez operaciones
core existentes en la definición S11, `pidfd_open` y seis interfaces de envío
de señales cuya variante puede ordenar/controlar directamente el estado o la
terminación de un proceso/hilo. Todas quedan sin decisión.

| NR / syscall | Familia y semántica relevante | Condición/variantes a resolver | Cruces descriptivos |
|---|---|---|---|
| 56 `clone` | Creación de hijo; según flags puede crear proceso o thread y seleccionar recursos de contexto compartidos. | ABI raw target-bound frente al wrapper libc; `CLONE_VM`, `CLONE_FILES`, `CLONE_SIGHAND`, `CLONE_THREAD`, `CLONE_PARENT`, `CLONE_VFORK`, `CLONE_PIDFD`, TID pointers, exit signal, retorno parent/child y errores. | S03 (FD table compartida); S05/S06 (VM/mappings); S10 (futex/signals); S16 (namespace/identity); S11 crea rama. |
| 57 `fork` | Crea un proceso hijo con relación padre/hijo y semántica copy-on-write de address space. | Éxito/retorno en ambas ramas, fallos y estado del hijo; distinguir syscall directa de wrappers o implementación libc alternativa. | S03 (FDs heredados); S05/S06 (mappings/backing); S10 (estado/señales); S11 relación padre/hijo. |
| 58 `vfork` | Crea hijo con relación de ejecución restringida mientras comparte temporalmente address space hasta exec/exit. | Retorno; suspensión del padre; finalización por exec/exit del hijo; restricciones de uso; no equiparar a fork sólo por crear hijo. | S03 (FD inheritance/exec boundary); S05/S06 (espacio compartido temporal); S11 transición hijo→exec/exit. |
| 435 `clone3` | Interfaz moderna de creación/clonación por `struct clone_args`. | `size`, extensibilidad de estructura, `flags`, `exit_signal`, stack/stack_size, `pidfd`, `set_tid`, `cgroup`, parent/child TID y compatibilidad; clasificar por efecto real de flags y retorno. | S03 (FD/pidfd); S05/S06 (VM); S10 (coordinación); S16 (namespace); no inferir S16/S03 desde el syscall base. |
| 59 `execve` | Ejecuta el objeto seleccionado y reemplaza la imagen del proceso; éxito no retorna. | Sólo transición exitosa produce imagen nueva; preservar path, argv/envp, binario vs script/interpreter y errores pre-transición. La resolución/selección es dimensión separada. | S01 (selección/resolución si la ruta lo requiere); S03 ya adjudicada: sólo supervivencia/purga FD por `FD_CLOEXEC`; S10 por reset de signal dispositions como efecto accesorio; otras superficies por actividad posterior, no por arrastre. |
| 322 `execveat` | Reemplaza imagen como execve con selector `dirfd`/path o FD ejecutable. | `AT_EMPTY_PATH`, `AT_SYMLINK_NOFOLLOW`, path absoluto/relativo, `AT_FDCWD`, script/interpreter, éxito/error. Separar resolución, ejecución y cierre FD. | S01: resolución del ejecutable; S03 ya adjudicada condicionalmente: herencia/purga FD; S11: transición de imagen. |
| 61 `wait4` | Espera cambios de estado de hijos y devuelve información/status; puede recoger un hijo terminado. | `pid` selector (hijo específico/grupo/todos), `WNOHANG`, `WUNTRACED`, `WCONTINUED`, `rusage`, estado waitable, recolección de zombie, señal/interrupción y retorno. libc `wait`/`waitpid` pueden mapear a este ABI; no duplicar filas. | S10: señal puede notificar, pero no sustituye wait/reap; S11: estado hijo y recolección. |
| 247 `waitid` | Espera/consulta cambios de estado mediante `idtype`/`id`, incluidos hijos y selector `P_PIDFD` en variantes soportadas. | `P_PID`, `P_PGID`, `P_ALL`, `P_PIDFD`; `WEXITED`, `WSTOPPED`, `WCONTINUED`, `WNOHANG`, `WNOWAIT`; resultado `siginfo`, reap vs observar sin consumir, permisos y errores. | S03 si usa pidfd como FD; S10 por señal/event notification separada; S11 por wait/collection. |
| 60 `exit` | Termina el thread llamante (syscall raw). | No confundir función libc `exit()` con `_exit()` ni con syscall; estado/status, limpieza kernel, último thread y recursos compartidos, señalización a padre y resultado no retorna. | S10 (señal/futex de notificación puede seguir); S11 (terminación del thread/proceso según condición). |
| 231 `exit_group` | Termina todos los threads del thread group. | Distinguir de `exit`; código de salida, alcance de thread group, no retorno, threads concurrentes y observación/espera del padre. | S10 (notificación/wakeups consecuencia); S11 terminación del grupo. |
| 434 `pidfd_open` | Crea un pidfd que refiere a un task/proceso; habilita espera/observación estable y otras operaciones sobre el objetivo. | PID válido, `PIDFD_NONBLOCK`, `PIDFD_THREAD`, task aún vivo/zombie, relación parent/child, identidad estable y uso posterior mediante waitid/señal. Decidir si creación del handle forma parte de control S11 o sólo habilita S03/lifecycle FD. | S03 por el FD creado; S10 si se usa para señalización; S11 por referencia/observación del task y wait, a adjudicar por alcance. |
| 62 `kill` | Envía señal a proceso o grupo; algunas señales alteran estado, detienen o terminan el target. | Relacionar con S11 sólo para señales/objetivos cuyo efecto sea control de ciclo de vida; separar señal cero, señales no terminales, grupos, permisos y envío fallido. Ya tiene S10 condicional para envío como coordinación; no duplicar automáticamente. | S10 adjudicada para envío de señal; S11 potencial sólo por control/terminación; S11 no reemplaza S10. |
| 200 `tkill` | Envío dirigido a un TID; señal puede cambiar estado/terminar el thread. | Target thread, TGID no aportado en esta ABI, signal zero vs entrega efectiva, permisos/errores y estado terminal. Ya S10 condicional. | S10 adjudicada como señalización; posible S11 sólo para la dimensión de control del thread. |
| 234 `tgkill` | Envío de señal a TID verificado dentro de TGID. | TGID/TID y pertenencia, clase de señal con efecto lifecycle/control, señal cero, permiso y resultado. Ya S10 condicional. | S10 adjudicada para coordinación; posible S11 para efecto de control del proceso/thread. |
| 424 `pidfd_send_signal` | Envía señal a task referenciado por pidfd; flags modernos pueden elegir thread/thread-group/process-group. | `pidfd`, `sig`, `siginfo`, flags/scope, pid namespace, `PIDFD_THREAD`, permiso y resultado; condicionar S11 a señal con efecto de control/terminación. Ya S10 condicional. | S03 por pidfd FD; S10 ya adjudicada como señalización; posible S11 para el control lifecycle. |
| 129 `rt_sigqueueinfo` | Encola señal con `siginfo` al thread group destino. | Sólo control S11 cuando la señal no nula/target realmente corresponden a control de lifecycle; validar `si_code`, datos, permisos, límite de cola y resultado. Ya S10 YES condicional. | S10 adjudicada para señal+datos; posible S11 por señal de control/terminación, sin trasladar membresía. |
| 297 `rt_tgsigqueueinfo` | Encola señal y `siginfo` a thread particular dentro de TGID. | Igual criterio de control que `rt_sigqueueinfo`, preservando TGID/TID, señal, `si_code`, permisos, saturación y retorno. Ya S10 YES condicional. | S10 adjudicada para señal+datos; posible S11 por control lifecycle del thread/proceso. |

**Nota de señalización:** las seis llamadas de envío anteriores son candidatas
S11 únicamente para subcasos en los que la señal sea un control directo del
estado/terminación (por ejemplo señales con acción de parar/continuar/terminar)
y la llamada apunte al target pertinente. El resto de su uso de coordinación
permanece en el alcance S10 ya adjudicado. Señal enviada no demuestra entrega,
recepción, terminación ni recolección.

**Nota de exec y memberships previas:** `execve` ya tiene S03 condicional sólo
para supervivencia/purga FD mediante `FD_CLOEXEC` en exec exitoso;
`execveat` ya tiene S03 para supervivencia/purga y selector ejecutable
condicionado. Este lote propone únicamente la dimensión S11 de ejecución/
reemplazo de imagen. Para `execveat`, S01 (resolución), S03 (FD inheritance) y
S11 (transición) son preguntas diferentes. No cambiar ni sustituir S03.

## 5. Leads separados

Estos leads no cuentan entre las 17 candidaturas centrales. Se enumeran para
revisión humana futura; no se agregan a la lista S11, no se promueven ni se
declaran NO. Estado: **UNREVIEWED / PENDING HUMAN ADJUDICATION**.

| NR / syscall | Motivo del lead y pregunta pendiente | Frontera / superficie alternativa |
|---|---|---|
| 438 `pidfd_getfd` | Adquiere un FD remoto en el caller, pero su efecto directo es capability acquisition, no creación, espera ni terminación. ¿Existe una razón separada para S11 por referenciar un proceso? | S03 y S09 ya adjudicadas; no cambiarlas ni extender a S11 por nombre `pidfd_*`. |
| 218 `set_tid_address` | Configura `clear_child_tid`; al terminar un thread el kernel puede escribir cero y hacer futex wake. Determinar si la syscall de configuración debe cruzar S11 o si sólo la terminación posterior pertenece ahí. | S10/futex para el wake; S11 posible sólo como configuración ligada al evento de terminación. |
| 448 `process_mrelease` | Opera sobre memoria de un proceso en estado de salida para acelerar liberación de recursos. Determinar si liberar memoria de un proceso ya dying es S11 o una operación de memoria/gestión posterior. | Memoria/proceso, posible S05/S06; no equivale a terminar ni recoger el proceso. |
| 310 `process_vm_readv`; 311 `process_vm_writev` | Acceso de memoria cross-process requiere target y autorización, pero el efecto principal es transferir bytes, no ciclo de vida. Delimitar si son sólo S02/otra superficie o tienen una relación S11 por targeting. | S02 payload; memoria S05/S06 según backing; no adjudicar S11 por target PID. |
| 157 `prctl` | Multiplexor: comandos como `PR_SET_CHILD_SUBREAPER` o `PR_SET_PDEATHSIG` pueden cambiar relaciones/eventos de hijos; otros sólo consultan/configuran atributos. Delimitar por comando antes de considerar S11. | S16 ya candidato; no promover `prctl` completo. |
| 101 `ptrace` | Control de ejecución/stop/resume y observación de tracees podría afectar estados de procesos. Requiere partición command-by-command y target/permission; no equivale a process creation/wait ordinario. | Depuración/control de proceso; relación S11 por subcomandos por decidir, no syscall-wide. |
| 272 `unshare`; 308 `setns` | Cambian namespaces asociados al calling process/thread o lo mueven a namespaces de otro proceso; no crean ni terminan por sí mismos el proceso. | S16/namespace identity; revisar sólo si doctrina S11 incorpora cambios del árbol/namespace. |
| 13 `rt_sigaction` | `SIGCHLD`, `SIG_IGN` o `SA_NOCLDWAIT` pueden cambiar si el hijo genera notificación o queda zombie/esperable. La syscall configura disposición y ya tiene S10 NO; preguntar si un subcaso cambia recolección S11. | No modificar el NO S10; S11 sólo como posible efecto de wait/reap, no como señalización. |
| 14 `rt_sigprocmask`; 127 `rt_sigpending` | Bloquear/consultar `SIGCHLD` puede afectar observabilidad de notificación, pero no crea, espera ni recoge directamente un hijo. | Estado de señal; no reabrir las decisiones S10 (NO para máscara/consulta). |
| 128 `rt_sigtimedwait`; 130 `rt_sigsuspend` | Pueden esperar/recibir `SIGCHLD`; no hacen wait/reap ni identifican necesariamente un hijo. Determinar si recepción de notificación de salida tiene una dimensión S11 aparte de coordinación S10. | S10 ya adjudicada donde corresponde; no duplicar automáticamente como S11. |

`getpid`/`gettid` son consultas de identidad y no se elevan a leads por sí
solas. `wait`/`waitpid` son interfaces libc cuyo syscall subyacente debe
atribuirse a `wait4`/`waitid` según la ruta/ABI; no son filas target-bound
adicionales en esta lista.

## 6. Cruces S01–S10

Los cruces son descriptivos y quedan sin adjudicar en este lote:

| Superficie | Frontera relevante con S11 |
|---|---|
| S01 — resolución/selección | `execveat` puede seleccionar por path/`dirfd` o FD con `AT_EMPTY_PATH`; resolver el objeto ejecutable es distinto de ejecutar/reemplazar imagen. |
| S02 — payload I/O | Hijos/descendientes pueden realizar I/O después de crearse/ejecutarse; el efecto de payload no se adjudica por S11. `process_vm_readv/writev` queda como lead de bytes cross-process. |
| S03 — FD lifecycle/inheritance | `execve` y `execveat` ya tienen decisiones S03 acotadas sobre supervivencia/purga FD. `clone` puede compartir/copiar tabla con `CLONE_FILES`; conservar ambas dimensiones, sin modificar S03. `pidfd_open` retorna un FD, posible dimensión S03 no decidida aquí. |
| S04 — filesystem mutation | El ejecutable, script o descendiente puede producir mutaciones filesystem; no pertenecen a S11 por la transición de proceso. |
| S05 — file-backed mapping | Fork/clone/exec cambian o comparten address spaces; backing/mapping debe clasificarse por objeto/operación, no por la syscall de lifecycle. |
| S06 — anonymous/memfd | Memoria compartida entre clone/fork y capacidades memfd heredadas pueden cruzar; no son efecto propio de process create/exec. |
| S07 — IP networking | Descendientes pueden establecer/usar sockets IP después de clone/exec; reachability y operación de red se mantienen separadas. |
| S08 — AF_UNIX | Herencia/compartición de sockets locales por fork/clone/exec no adjudica nuevamente la operación AF_UNIX ni reabre S08. |
| S09 — FD capability passing | `SCM_RIGHTS` ya adjudicado S09 no equivale a herencia por fork/exec. `pidfd_getfd` conserva sus S03/S09 existentes, sin añadir S11 automáticamente. |
| S10 — IPC/coordination | Las seis syscalls de envío de señales ya tienen S10 condicional. S11 sólo consideraría el subcaso de control/terminación; señales como coordinación permanecen en S10 y no se trasladan. Wait/reap no equivale a recibir señal `SIGCHLD`. |

## 7. Fuentes y límites

- **Target-bound:** `files/A_PRE_0_SURFACE_MANIFEST.json`, tabla nativa x86_64
  de 385 filas y su hash registrado
  `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
  Establece números/nombres y ABI; no demuestra reachability, uso,
  autorización, resultado o efecto observado.
- **Linux man-pages 6.19, snapshot 2026-09-09** para semántica general:
  [`clone(2)`/`clone3(2)`](https://man7.org/linux/man-pages/man2/clone.2.html),
  [`execve(2)`](https://man7.org/linux/man-pages/man2/execve.2.html),
  [`execveat(2)`](https://man7.org/linux/man-pages/man2/execveat.2.html),
  [`wait(2)`/`wait4(2)`/`waitid(2)`](https://man7.org/linux/man-pages/man2/wait.2.html),
  [`exit` syscall via `_exit(2)`](https://man7.org/linux/man-pages/man2/_exit.2.html),
  [`pidfd_open(2)`](https://man7.org/linux/man-pages/man2/pidfd_open.2.html),
  [`pidfd_send_signal(2)`](https://man7.org/linux/man-pages/man2/pidfd_send_signal.2.html),
  [`kill(2)`](https://man7.org/linux/man-pages/man2/kill.2.html),
  [`rt_sigqueueinfo(2)`/`rt_tgsigqueueinfo(2)`](https://man7.org/linux/man-pages/man2/rt_sigqueueinfo.2.html),
  [`set_tid_address(2)`](https://man7.org/linux/man-pages/man2/set_tid_address.2.html),
  [`ptrace(2)`](https://man7.org/linux/man-pages/man2/ptrace.2.html),
  [`prctl(2)`](https://man7.org/linux/man-pages/man2/prctl.2.html),
  [`process_vm_readv(2)`](https://man7.org/linux/man-pages/man2/process_vm_readv.2.html).
- Estas páginas describen interfaces Linux, no disponibilidad exacta de cada
  flag/opción en el kernel target ni los efectos de una llamada real. En
  adjudicación se deben cotejar variantes con UAPI/kernel versionado 7.0 y
  conservar límites del source package target.
- **Historial canónico de decisiones a preservar:** checkpoint 018 para las
  dimensiones S03 de `execve`/`execveat` y `pidfd_getfd`; checkpoint 030 para
  S09 `pidfd_getfd`; checkpoint 032 para las decisiones S10 de señales. Las
  citas describen límites, no habilitan cambios en esas memberships.
- Se registra como evidencia documental, no como prueba dinámica. No se
  extrapola de observaciones/probes anteriores.

## 8. Pendientes para adjudicación humana

1. ¿Los 17 candidatos centrales pertenecen a S11 bajo los alcances/condiciones
   indicados, especialmente `pidfd_open` como handle de task?
2. ¿Qué variantes de `clone`/`clone3` representan proceso frente a thread, y
   cómo conservar flags de recursos compartidos, parentage, namespaces y
   `CLONE_PIDFD` sin crear relaciones por flag no ejecutado?
3. ¿Qué cuenta como transición exec exitosa; cómo correlacionar binario,
   scripts/interpreters, `execveat` selector, fallo antes de reemplazo y
   supervivencia/purga S03?
4. ¿Qué resultados de `wait4`/`waitid` significan observar estado frente a
   recoger/reap; cómo particionar `WNOWAIT`, `P_PIDFD`, stop/continue y
   `WNOHANG`?
5. ¿`exit` y `exit_group` requieren memberships separadas por thread y
   thread-group? ¿Qué significa terminar thread vs último thread/proceso?
6. Para señales ya S10, ¿qué señales, targets y resultados califican como
   control/terminación S11, sin duplicar usos de coordinación?
7. ¿Qué pidfd operations adicionales, si alguna, forman parte directa de S11?
   En particular, ¿`pidfd_getfd` debe quedar como lead/exclusión de scope?
8. ¿Algún lead (`set_tid_address`, `process_mrelease`, `ptrace`, comandos
   `prctl`, configuración/espera SIGCHLD) merece candidatura en lote posterior?

## 9. Invariantes y verificación posterior a la preparación

- S10 permanece exactamente: **37** candidaturas cerradas (31 YES, 6 NO,
  0 UNKNOWN); las 12 pistas poll/select/epoll no promovidas siguen fuera.
- Candidaturas centrales S11: **17**, todas sin decisión; leads separados:
  **14** entradas, sin promoción ni disposición.
- Manifiesto, ledger y `requirements.lock` no se modifican en esta preparación;
  el manifiesto conserva hash de baseline
  `49ec91d7e567bd812860543c4f0262e52fbb4222c81b0ad5a56dd440a69ac7a6`;
  ledger permanece `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42`;
  lock permanece `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70`.
- No se alteran memberships S01–S10, incluidas las decisiones preexistentes
  S03/S09 de exec y `pidfd_getfd`, ni las S10 de señales.
- Disposiciones generales: **385/385 UNKNOWN**, **0** finales;
  `inventory.frozen=false`; A-PRE-0 **NOT READY**; A-PRE-1
  **NOT AUTHORIZED / NOT EXECUTED**.
- No se ejecutaron TALOS, FastAPI, workloads, probes, providers, benchmarks,
  tests, suites, VM, runtime o actividad dinámica. No se modificó código
  funcional, E5/Qwen, corpus, modelos ni bases protegidas.
- Sólo se crea este checkpoint y se añade su entrada al índice. No hay staging
  ni commit; cambios preexistentes ajenos se preservan.
- Estado: **listo para adjudicación humana**. No adjudicar S11 ni avanzar a
  otra superficie en este checkpoint.
