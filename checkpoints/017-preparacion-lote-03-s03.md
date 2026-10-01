# Preparación del lote 03 — S03 FD hygiene/lifecycle

Fecha: 2026-10-01

## Alcance e identidad

Preparación documental para revisión humana desde el commit
`f975776ab064e611139c8ec7c904fd7d9cda4dff` (branch `main`). No es una
adjudicación. No se agregan ni aprueban membresías, exclusiones o disposiciones.

La superficie S03 del manifiesto es **Descriptor lifecycle, inheritance, and
acquisition**. Define como recursos las open file descriptions, sockets y
otras capacidades de objetos del kernel en poder del proceso; sus ejes
declarados incluyen comandos `fcntl`, estado `FD_CLOEXEC`, allowlist de FDs al
entrar al sandbox e identidad del descriptor antes/después de duplicar o
adquirirlo. La definición incluye como syscalls `close`, `close_range`, `dup`,
`dup2`, `dup3`, `fcntl`, `execve`, `execveat` y `pidfd_getfd`.

## Hallazgo sobre las referencias pendientes

Tras las adjudicaciones S01 y S02, **no hay filas con `potential_surface_refs`
pendientes que nombren S03**. El conteo pendiente de pistas S03 en la revisión
inicial de filas sin candidata es **0**.

Esto no significa que S03 esté adjudicada o cerrada. Las nueve syscalls de la
definición S03 ya aparecen en las listas canónicas de `syscalls` de esa
superficie y en `candidate_surface_ids`, pero todas siguen con
`candidate_membership_status=UNREVIEWED` y disposición general `UNKNOWN`.
Este lote prepara precisamente esa asociación preexistente para revisión
humana; **no crea ni ratifica esas candidaturas**.

## Inventario para revisión humana

| NR / syscall | Semántica y objeto FD relevante | Variantes/condiciones a revisar | Cruces explícitos | Pregunta de revisión S03 |
|---|---|---|---|---|
| 3 `close` | Libera una referencia de descriptor del proceso; el objeto/open file description puede permanecer vivo si existen duplicados u otras referencias. | Identidad del FD, errores y comportamiento de cierre del ABI/target, referencias duplicadas y cierre durante `exec`. | S02: FD de I/O que deja de estar disponible para este proceso; S07/S09 según el objeto. | ¿La superficie cubre el ciclo de vida del descriptor hasta su cierre y distingue el descriptor de la open file description compartida? |
| 436 `close_range` | Cierra un rango de descriptores, o aplica una operación al rango según flags. | `first`/`last`; `CLOSE_RANGE_UNSHARE`, `CLOSE_RANGE_CLOEXEC`, flags admitidos por el kernel target y errores/rangos límite. | S11 por transición de proceso/exec; S09 si los FDs habían sido recibidos o se comparten como capacidades. | ¿Se cubren por separado cierre efectivo, marcado close-on-exec y separación de la tabla FD? |
| 32 `dup` | Crea un descriptor nuevo que refiere a la misma open file description que el FD fuente. | Selección del FD mínimo disponible; FD resultante; estado close-on-exec del descriptor duplicado. | S02: ambos FDs pueden referir al mismo flujo de I/O; S07/S09 según el objeto. | ¿Se modelan identidad y relación alias entre FD fuente y duplicado, sin confundirlas con una copia del objeto? |
| 33 `dup2` | Hace que `newfd` refiera al objeto de `oldfd`, cerrando atómicamente el destino previo cuando corresponde. | `oldfd == newfd`, sustitución del destino, reutilización del número y semántica close-on-exec. | S02; S07/S09 según el objeto. | ¿Se incluyen la sustitución del FD destino y el caso identidad, además de la duplicación ordinaria? |
| 292 `dup3` | Variante de duplicación a descriptor elegido con flags explícitos. | `O_CLOEXEC`, `oldfd == newfd`, flags inválidos y asignación exacta de `newfd`. | S02; S07/S09 según el objeto; transición a S11 al ejecutar. | ¿Se particionan los flags y el estado de herencia del descriptor nuevo? |
| 72 `fcntl` | Interfaz de control cuyo efecto depende del comando; S03 ya declara las variantes de duplicación y manipulación de descriptor. | Limitar esta revisión S03 a `F_DUPFD`, `F_DUPFD_CLOEXEC`, `F_GETFD` y `F_SETFD`; otros comandos no se resuelven por esta lista. Revisar `FD_CLOEXEC` y el FD asignado. | S06 para comandos/efectos de locking si corresponde; S02 para FD resultante; S11 para herencia por exec. | ¿La decisión de S03 se limita a los comandos de FD declarados sin promover `fcntl` completo ni adjudicar otros comandos? |
| 59 `execve` | Sustituye la imagen del proceso; los FDs sin close-on-exec normalmente sobreviven al cambio de imagen. | Estado `FD_CLOEXEC` de cada descriptor, allowlist al entrar al sandbox, transición y fallos antes de completar exec. | S11: cambio de imagen/ejecución; S02/S07/S09 para capacidades que sobreviven. | ¿Se evalúa el estado FD antes/después de la transición y no se confunde la semántica de exec con origen del descriptor? |
| 322 `execveat` | Ejecuta una imagen mediante `dirfd`/pathname o FD según flags; también produce una transición de imagen. | `AT_EMPTY_PATH`, `AT_SYMLINK_NOFOLLOW`, `dirfd`, objeto ejecutable y `FD_CLOEXEC` cuando se ejecuta desde descriptor. | S01: resolución de ejecutable; S11: cambio de imagen; S02/S07/S09: capacidades que sobreviven. | ¿Se separan la adquisición/resolución del ejecutable, el cambio de imagen y la herencia de los demás FDs? |
| 438 `pidfd_getfd` | Obtiene en el proceso llamante un FD que duplica el descriptor referido en otro proceso identificado por pidfd, sujeto a controles de acceso. | PIDFD, número FD remoto, autorización, identidad del objeto obtenido y flags close-on-exec del FD local. | S09: transferencia/obtención de capacidad entre procesos; S02/S07 según el tipo de objeto. | ¿S03 cubre el ciclo de vida del FD local adquirido mientras S09 trata la transferencia entre procesos? No inferir una decisión conjunta. |

## Rutas de adquisición y límites del lote

La definición S03 habla de adquisición/origen, pero las rutas de creación o
recepción inicial de FDs no se resuelven por el solo hecho de que devuelvan un
descriptor. El manifiesto ya tiene las siguientes candidaturas en otras
superficies:

| NR / syscall | Candidaturas actuales | Relevancia para S03, no adjudicada |
|---|---|---|
| 2 `open` | S01 | Crea un FD tras resolución/apertura; revisar si S03 requiere cubrir el nacimiento/registro de capacidades. |
| 85 `creat` | S01 | Ruta de creación/apertura que retorna un FD; relación con S03 pendiente de decisión separada. |
| 257 `openat` | S01 | Adquisición mediante `dirfd`/pathname; revisar el límite S01/S03. |
| 437 `openat2` | S01 | Adquisición con `open_how` y restricciones de resolución; revisar el límite S01/S03. |
| 22 `pipe` y 293 `pipe2` | S10 | Crean descriptores de pipe; evaluar origen/creación de FDs y cruces con IPC sin inferir S03. |
| 41 `socket`, 43 `accept`, 288 `accept4` | S07/S08 | Crean o adquieren descriptors de socket; revisar S03 frente a la semántica de red. |
| 47 `recvmsg`, 299 `recvmmsg` | S07/S08/S09 | Pueden recibir capacidades por ancillary data; mantener explícita la frontera de pasaje S09. |
| 53 `socketpair` | S08 | Crea un par de sockets y FDs; relación S03 no adjudicada. |

La lista anterior es una advertencia de cobertura conceptual para la revisión
posterior, no una expansión automática del lote: ninguna de esas relaciones
S03 se acepta o excluye aquí. En particular:

- Que una syscall consuma o retorne un FD no basta por sí solo para adjudicar
  S03.
- `execve*` trata principalmente la transición de proceso, aunque la
  supervivencia de FDs es un eje de S03.
- `pidfd_getfd` cruza claramente con S09; las dimensiones no se colapsan.
- La pertenencia actual a otra superficie no impide una relación superpuesta,
  pero tampoco la prueba.
- Esta revisión no determina si una ruta es alcanzable desde el workload, si
  ocurre en fase WORKLOAD o si un control la permite/deniega.

## Fuentes y límites de evidencia

La fuente local de identidad, números, listas de candidatos y definición S03
es el manifiesto target-bound del commit indicado. Como referencias de
semántica de interfaz para la revisión humana se señalan Linux man-pages:
[`close(2)`](https://man7.org/linux/man-pages/man2/close.2.html),
[`close_range(2)`](https://man7.org/linux/man-pages/man2/close_range.2.html),
[`dup(2)`](https://man7.org/linux/man-pages/man2/dup.2.html),
[`fcntl(2)`](https://man7.org/linux/man-pages/man2/fcntl.2.html),
[`execve(2)`](https://man7.org/linux/man-pages/man2/execve.2.html),
[`execveat(2)`](https://man7.org/linux/man-pages/man2/execveat.2.html),
[`pidfd_getfd(2)`](https://man7.org/linux/man-pages/man2/pidfd_getfd.2.html),
[`open(2)`](https://man7.org/linux/man-pages/man2/open.2.html),
[`pipe(2)`](https://man7.org/linux/man-pages/man2/pipe.2.html),
[`socket(2)`](https://man7.org/linux/man-pages/man2/socket.2.html) y
[`recvmsg(2)`](https://man7.org/linux/man-pages/man2/recvmsg.2.html).
No se pudo recuperar esas páginas desde este entorno durante la preparación;
las referencias son fuentes propuestas para corroboración, no evidencia de una
verificación nueva contra el kernel target. No se consultó ni modificó la VM.

## Estado e invariantes

- Candidaturas existentes a S03 revisadas para preparar este lote: **9**.
- Referencias `potential_surface_refs` pendientes que nombren S03: **0**.
- Membresías S03 nuevas o adjudicadas en esta preparación: **0**.
- No se modificaron manifiesto, ledger, readiness, `inventory.frozen` ni el
  índice de checkpoints.
- Las disposiciones generales siguen `UNKNOWN`; A-PRE-0 sigue `NOT READY` y
  A-PRE-1 sigue `NOT AUTHORIZED / NOT EXECUTED`.
- No se ejecutaron probes, tests, suites, TALOS, parsers, validadores A-PRE ni
  workloads.
- No se tocaron VM, overlay, runtime, `requirements.lock`, corpus, modelos ni
  bases de datos.
- Único cambio de esta preparación: este informe; no se hizo commit.

Siguiente paso: revisión humana de las nueve candidaturas S03 existentes y
decisión explícita sobre si las rutas de adquisición de la sección anterior
requieren ampliar el ámbito de revisión. No materializar cambios canónicos
hasta recibir esa adjudicación.
