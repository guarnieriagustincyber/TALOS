# Adjudicación documental — lote 11, S11 process tree / exec / termination

Fecha: 2026-10-01

## 1. Alcance y doctrina

Esta adjudicación resuelve las **17 candidaturas centrales** de
[`033-preparacion-lote-11-s11.md`](./033-preparacion-lote-11-s11.md), SHA-256
`8b0d4a07e2b449f5700f527d3f47867d53e4e52a3217b23015528869bbd31842`.
Se aplica:

> **S11 = ciclo de vida del proceso/hilo y transición de ejecución: creación,
> clonación, reemplazo de imagen ejecutable, espera/recolección y terminación/
> control directo del proceso.**

La decisión es de membership de superficie, no de disposición syscall-wide,
reachability, efecto observado, enforcement ni uso por TALOS. Metodología:
**OBSERVE → MEASURE → CORRELATE → CLASSIFY → HUMAN DECISION → FUTURE CHANGE**.

## 2. Resultado

- Candidaturas adjudicadas: **17**.
- **YES: 17**, todos condicionales a las variantes/efectos detallados.
- **NO: 0**.
- **UNKNOWN: 0**.
- Se materializan exclusivamente **17 memberships S11 YES**.
- Las disposiciones generales siguen UNKNOWN; las condiciones de variante no
  afirman ocurrencia ni resultado de un evento real.

## 3. Decisiones individuales

### Creación y clonación — 4 YES

| NR / syscall | Decisión y alcance adjudicado |
|---|---|
| 56 `clone` | **YES — condicional a creación exitosa del hijo.** La llamada crea una nueva rama de ejecución; según flags puede ser proceso o thread. Registrar retorno en parent/child y `CLONE_VM`, `CLONE_FILES`, `CLONE_SIGHAND`, `CLONE_THREAD`, `CLONE_PARENT`, `CLONE_VFORK`, `CLONE_PIDFD`, exit signal y TID pointers. Los recursos compartidos/namespace cruzan otras superficies pero no sustituyen el efecto S11. Wrapper libc y syscall raw no deben confundirse. |
| 57 `fork` | **YES — condicional a creación exitosa del proceso hijo.** Conservar relación parent/child, retorno, copy-on-write y fallos. Se adjudica el syscall target-bound, no cualquier implementación/wrapper de libc como si siempre invocara esta entrada. |
| 58 `vfork` | **YES — condicional a creación exitosa del hijo y a la semántica de ejecución restringida.** El padre queda suspendido hasta que el hijo ejecute exec o termine; no reducirlo a `fork` ni absorber el exec/exit posterior en la misma llamada. |
| 435 `clone3` | **YES — condicional a creación exitosa según `clone_args`.** Puede crear proceso o thread según flags; preservar `size`, extensibilidad, `flags`, `exit_signal`, stack/stack_size, `pidfd`, `set_tid`, `cgroup`, TID pointers y resultado. Los flags determinan la variante, no una membresía automática S16/S03. |

### Exec / reemplazo de imagen — 2 YES

| NR / syscall | Decisión y alcance adjudicado |
|---|---|
| 59 `execve` | **YES — sólo reemplazo exitoso de la imagen ejecutable del proceso.** Una llamada fallida no produjo transición. Path/argv/envp, binario/script e interpreter son variantes de selección/correlación. **S01** cubre resolución/identificación cuando aplique; **S03 ya adjudicada** cubre exclusivamente la supervivencia/purga FD por `FD_CLOEXEC`; esta decisión añade S11 por transición de imagen, sin alterar S03. |
| 322 `execveat` | **YES — sólo reemplazo exitoso de la imagen.** Mantener `dirfd`, `AT_FDCWD`, path relativo/absoluto, `AT_EMPTY_PATH`, `AT_SYMLINK_NOFOLLOW`, FD ejecutable, scripts/interpreter y errores separados. La resolución/selección es dimensión S01; la supervivencia/purga de FDs existentes es la decisión S03 previa; la transición de imagen es S11. No se fusionan ni reemplazan. |

### Espera y recolección — 2 YES

| NR / syscall | Decisión y alcance adjudicado |
|---|---|
| 61 `wait4` | **YES — esperar/obtener estado de hijo y, cuando corresponda, recogerlo.** Conservar selector `pid`, estado (exit/stop/continue), `WNOHANG`, `WUNTRACED`, `WCONTINUED`, `rusage`, `EINTR` y retorno. Distinguir observar cambio de estado y reap efectivo; las funciones libc wait/waitpid no son filas target adicionales. |
| 247 `waitid` | **YES — esperar/consultar estados de proceso/hijo.** Registrar `idtype`/`id` (`P_PID`, `P_PGID`, `P_ALL`, `P_PIDFD` cuando esté soportado), `WEXITED`, `WSTOPPED`, `WCONTINUED`, `WNOHANG`, `WNOWAIT`, `siginfo`, consumo/reap frente a observación sin consumir, errores y resultado. Un pidfd es selector/relación S03 aparte. |

### Terminación — 2 YES

| NR / syscall | Decisión y alcance adjudicado |
|---|---|
| 60 `exit` | **YES — terminación del thread llamante por el syscall raw x86_64.** No confundir NR 60 con la función libc `exit()` ni con `_exit()` de libc: en glibc moderno esos wrappers pueden usar `exit_group`. Preservar status y la diferencia entre terminar un thread y terminar el último thread del proceso. |
| 231 `exit_group` | **YES — terminación de todos los threads del thread group.** Registrar status, alcance de grupo y no-retorno; separar notificación/recolección por el padre (`SIGCHLD`/wait) como efectos/eventos posteriores. |

### Referencia de proceso y control mediante señales — 7 YES

| NR / syscall | Decisión y alcance adjudicado |
|---|---|
| 434 `pidfd_open` | **YES — condicional a pid válido y creación exitosa de pidfd para un task/proceso/thread.** El handle kernel estable identifica al task y habilita operaciones de espera/observación/control de ciclo de vida; registrar `PIDFD_NONBLOCK`, `PIDFD_THREAD`, task/zombie y relación de hijo. La creación del descriptor tiene además dimensión S03 pendiente de decisión separada; no se adjudica S03 aquí, ni se implica `pidfd_getfd`/S09. |
| 62 `kill` | **YES — condicional a envío exitoso de señal no nula cuyo efecto efectivo controle directamente estado/terminación del target.** Ejemplos: `SIGKILL`, `SIGSTOP`, `SIGCONT`; para señales capturables, conservar disposición efectiva, pues handler/ignore no equivalen necesariamente a terminar/parar. Separar pid positivo/grupo/0/-1, permiso y retorno. El envío ordinario de coordinación permanece en S10; señal cero es sólo existencia/permisos, no S11. |
| 200 `tkill` | **YES — condicional a entrega efectiva a TID de señal que controla directamente estado/terminación.** Registrar TID, señal y disposición/efecto; `sig=0` y error no son control entregado. Mantener S10 para la dimensión de señalización/IPC. |
| 234 `tgkill` | **YES — condicional a entrega efectiva a TID dentro del TGID con efecto de control directo.** Conservar validación TGID/TID, signal, disposición/efecto, permisos y resultado. La dimensión S10 ya existente permanece aparte. |
| 424 `pidfd_send_signal` | **YES — condicional a señal entregada al task referenciado por pidfd que controle directamente su estado/terminación.** Registrar identidad/validez de pidfd, `sig`, `siginfo`, flags de alcance (thread/thread-group/process-group cuando soportados), namespace, permisos y retorno. El uso de señal como coordinación ya es S10; no modifica esa decisión ni adjudica S03 del descriptor. |
| 129 `rt_sigqueueinfo` | **YES — sólo subcasos de señal encolada que controlen directamente estado/terminación del thread group destino.** `siginfo` no basta para S11: conservar TGID, número y acción efectiva de señal, `si_code`, permisos, límites de cola/errores y retorno. Señales de aplicación usadas sólo para notificación/datos quedan en la relación S10 ya adjudicada. |
| 297 `rt_tgsigqueueinfo` | **YES — sólo subcasos de señal encolada que controlen directamente estado/terminación del thread objetivo.** Preservar TGID/TID, `sig`, acción efectiva, `siginfo`, permisos, saturación y resultado. La notificación/datos ordinarios siguen siendo S10; no sustituir ni alterar su membership. |

**Criterio común de señales:** no es “toda señal = S11” ni “S10 impide S11”.
S11 se limita a la variante que produce control directo de estado/terminación
del proceso o thread destino. La pertenencia no demuestra que la señal fue
entregada o que terminó el target. En señales capturables, el efecto depende
de la disposición; `SIGKILL`/`SIGSTOP` y `SIGCONT` tienen semántica de control
propia. `sig=0` queda fuera. La dimensión de comunicación/señalización queda
intacta en S10.

## 4. Resumen por familia

| Familia | Candidaturas | YES | NO | UNKNOWN |
|---|---:|---:|---:|---:|
| Creación/clonación | 4 | 4 | 0 | 0 |
| Exec | 2 | 2 | 0 | 0 |
| Espera/recolección | 2 | 2 | 0 | 0 |
| Terminación | 2 | 2 | 0 | 0 |
| pidfd/control/señales | 7 | 7 | 0 | 0 |
| **Total** | **17** | **17** | **0** | **0** |

## 5. Cruces S01–S10

Los cruces no crean ni cambian memberships en otras superficies:

- **S01:** resolución/identificación del ejecutable, en especial `execveat`
  mediante path, `dirfd` o FD, separada de transición de imagen.
- **S02:** I/O de procesos/hijos y transferencias de memoria cross-process
  posteriores no se adjudican por creación, exec, wait o señal S11.
- **S03:** las decisiones ya adjudicadas para `execve`/`execveat` sobre
  `FD_CLOEXEC` supervivencia/purga se conservan. `clone*` puede compartir o
  heredar FDs, pero esta adjudicación no agrega S03. `pidfd_open` produce FD;
  S03 lifecycle no se decide aquí. `pidfd_getfd` permanece fuera de lote y sus
  memberships S03/S09 no se tocan.
- **S04:** mutaciones filesystem hechas por el proceso ejecutado o por
  descendientes son operaciones separadas.
- **S05/S06:** address space compartido, copy-on-write, mappings e imagen
  cargada son contexto de proceso, no adjudicaciones automáticas de backing/
  mapping.
- **S07/S08:** sockets IP y AF_UNIX usados/heredados por procesos siguen en
  sus superficies ya adjudicadas; no se reabren.
- **S09:** capability passing por `SCM_RIGHTS` no equivale a fork/exec ni se
  altera. `pidfd_getfd` no se modifica.
- **S10:** las seis relaciones de envío de señales a `kill`, `tkill`, `tgkill`,
  `pidfd_send_signal`, `rt_sigqueueinfo` y `rt_tgsigqueueinfo` permanecen
  exactamente como adjudicadas. S11 cubre sólo el subcaso de control directo
  del proceso/thread; señal como coordinación sigue en S10.

## 6. Los 14 leads permanecen fuera

No se adjudicaron ni promovieron:

1. `pidfd_getfd` 438
2. `set_tid_address` 218
3. `process_mrelease` 448
4. `process_vm_readv` 310
5. `process_vm_writev` 311
6. `prctl` 157
7. `ptrace` 101
8. `unshare` 272
9. `setns` 308
10. `rt_sigaction` 13
11. `rt_sigprocmask` 14
12. `rt_sigpending` 127
13. `rt_sigtimedwait` 128
14. `rt_sigsuspend` 130

Se mantienen como leads `UNREVIEWED / PENDING HUMAN ADJUDICATION`. En
particular, las cuatro últimas conservan sus decisiones S10 previas donde
existan; esta fase no las extiende a S11. No se detectó motivo para detener y
promover alguna de ellas en esta adjudicación.

## 7. Materialización

Se materializan exclusivamente las 17 relaciones S11 YES en las filas
target-bound correspondientes:

`clone` 56, `fork` 57, `vfork` 58, `clone3` 435, `execve` 59, `execveat` 322,
`wait4` 61, `waitid` 247, `exit` 60, `exit_group` 231, `pidfd_open` 434,
`kill` 62, `tkill` 200, `tgkill` 234, `pidfd_send_signal` 424,
`rt_sigqueueinfo` 129 y `rt_tgsigqueueinfo` 297.

Cada registro conserva `disposition_unchanged: UNKNOWN`, el alcance, rationale
y la referencia a este checkpoint. Se agrega contexto S11 a las dos señales
queueinfo y `pidfd_open`, ausentes de la lista S11 previa. En filas con S10,
S03 o S16 se preservan los contextos y decisiones previas sin cambios. No se
modifica S01–S10 ni se alteran disposiciones globales.

## 8. Evidencia y límites

- **Identidad target-bound:** manifiesto A-PRE-0, tabla x86_64 de 385 filas,
  SHA-256 `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
  Fija número/nombre/ABI, no ocurrencia ni efecto.
- **Linux man-pages 6.19, snapshot 2026-09-09:** [`clone(2)`/`clone3(2)`](https://man7.org/linux/man-pages/man2/clone.2.html),
  [`execve(2)`](https://man7.org/linux/man-pages/man2/execve.2.html),
  [`execveat(2)`](https://man7.org/linux/man-pages/man2/execveat.2.html),
  [`wait(2)`](https://man7.org/linux/man-pages/man2/wait.2.html),
  [`_exit(2)`](https://man7.org/linux/man-pages/man2/_exit.2.html),
  [`pidfd_open(2)`](https://man7.org/linux/man-pages/man2/pidfd_open.2.html),
  [`pidfd_send_signal(2)`](https://man7.org/linux/man-pages/man2/pidfd_send_signal.2.html),
  [`kill(2)`](https://man7.org/linux/man-pages/man2/kill.2.html),
  [`rt_sigqueueinfo(2)`/`rt_tgsigqueueinfo(2)`](https://man7.org/linux/man-pages/man2/rt_sigqueueinfo.2.html)
  y [`signal(7)`](https://man7.org/linux/man-pages/man7/signal.7.html).
  Describen interfaces Linux generales; las flags/versiones y ABI deben
  cotejarse con UAPI/kernel target para cierre operativo.
- **Decisiones previas preservadas:** checkpoint 018 (S03 execve/execveat),
  checkpoint 030 (S03/S09 pidfd_getfd) y checkpoint 032 (S10 señales).
- La adjudicación no se basa en probes, pruebas dinámicas, workloads,
  ejecución de TALOS ni datos de producción. No afirma que se usara ninguna
  syscall ni que el control permita/deniegue un evento.

## 9. Invariantes finales

- 17 decisiones: **17 YES, 0 NO, 0 UNKNOWN** en las relaciones S11 centrales.
- Sólo esas 17 memberships S11 se materializan; S01–S10 no se modifican.
- Los 14 leads siguen fuera y sin promoción.
- S10 continúa con 37 decisiones (31 YES/6 NO/0 UNKNOWN); las 12 pistas
  `poll`/`select`/`epoll` siguen sin promoción.
- Disposiciones generales: **385/385 UNKNOWN**, **0** finales;
  `inventory.frozen=false`; A-PRE-0 **NOT READY**; A-PRE-1
  **NOT AUTHORIZED / NOT EXECUTED**.
- Ledger y `requirements.lock` intactos; E5/Qwen, corpus, modelos, bases
  protegidas, infraestructura y código funcional sin modificación.
- No hubo TALOS, workloads, probes, FastAPI, proveedores, benchmarks, tests,
  suites, VM/runtime ni actividad dinámica.
- Sin staging ni commit; cambios preexistentes ajenos preservados. No avanzar
  a S12.
