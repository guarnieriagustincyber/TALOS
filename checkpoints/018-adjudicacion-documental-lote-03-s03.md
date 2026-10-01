# Adjudicación documental — lote 03, membresías S03

Fecha: 2026-10-01

## Alcance e identidad

Este checkpoint registra la decisión humana consolidada sobre las nueve
candidaturas S03 preparadas en
[`017-preparacion-lote-03-s03.md`](./017-preparacion-lote-03-s03.md), desde el
estado persistido en `f975776ab064e611139c8ec7c904fd7d9cda4dff` (branch
`main`). Se aprueba únicamente la relación por superficie S03 y los alcances
condicionales especificados abajo. La decisión no extiende una relación a
todos los comandos o efectos de una syscall multiplexora.

## Decisiones humanas

| NR | Syscall | Decisión | Alcance taxativo de la relación S03 |
|---:|---|---|---|
| 3 | `close` | SÍ | Cierre y ciclo de vida de la entrada FD del proceso. No implica que el objeto compartido se destruya si quedan otras referencias. |
| 436 | `close_range` | SÍ | Saneamiento de rango de descriptores y efectos de flags; distinguir cierre, `CLOSE_RANGE_CLOEXEC` y `CLOSE_RANGE_UNSHARE`. |
| 32 | `dup` | SÍ | Duplicación/aliasing de una entrada FD con la misma open file description. |
| 33 | `dup2` | SÍ | Duplicación hacia FD elegido, reemplazo del destino y caso `oldfd == newfd`. |
| 292 | `dup3` | SÍ | Duplicación hacia FD elegido y control de herencia mediante `O_CLOEXEC`; conservar condiciones de igualdad/flags. |
| 72 | `fcntl` | SÍ CONDICIONAL | Sólo `F_DUPFD`, `F_DUPFD_CLOEXEC`, `F_GETFD` y `F_SETFD`. Los otros comandos `fcntl` no quedan adjudicados a S03. |
| 59 | `execve` | SÍ CONDICIONAL | Sólo la frontera de supervivencia/purga de FDs mediante `FD_CLOEXEC` a través de una transición `exec` exitosa. La ejecución/cambio de imagen cruza con S11/Procesos. |
| 322 | `execveat` | SÍ CONDICIONAL | Supervivencia/purga de los FDs existentes a través de `exec`; además, resolución/selección del ejecutable mediante `dirfd` o FD ejecutable según variante. El `dirfd` cruza S01 y el cambio de imagen cruza S11/Procesos; son dimensiones distintas. |
| 438 | `pidfd_getfd` | SÍ | Adquisición en el proceso llamante de un FD que refiere al objeto asociado al FD remoto, sujeta a autorización. Cruce mandatorio con IPC/Procesos y S09; no colapsar las superficies. |

Las nueve relaciones se registran como candidaturas humanas S03. Las
condiciones anteriores delimitan el alcance y no afirman trazabilidad desde el
workload, alcanzabilidad, enforcement ni cierre de particiones. Para filas con
otras superficies candidatas, sólo queda adjudicada S03; las demás relaciones
continúan pendientes.

## Efecto documental

- Las nueve filas ya tenían `S03` en `candidate_surface_ids`; se conserva ese
  conjunto y se cambia el estado de la relación S03 a adjudicado.
- La definición de S03 explicita los comandos `fcntl`, la dimensión de
  herencia de `execve*`, la resolución del ejecutable en `execveat` y el cruce
  IPC/Procesos de `pidfd_getfd`.
- Las otras relaciones candidatas de `fcntl` (S06), `execve`/`execveat`
  (S11) y `pidfd_getfd` (S09) no se adjudican por esta decisión.
- Las disposiciones generales de las nueve filas, y de las 385 filas del
  registro, permanecen `UNKNOWN`. Una membresía candidata no es
  `OBSERVED`, `BLOCKED`, cobertura ni readiness.
- `inventory.frozen` permanece `false`; A-PRE-0 permanece `NOT READY`;
  A-PRE-1 permanece `NOT AUTHORIZED / NOT EXECUTED`.

## Invariantes de contención

No se ejecutaron probes, suites, parsers, validadores, comandos dinámicos,
TALOS ni workloads. No se modificaron VM, overlay, runtime,
`requirements.lock`, corpus, modelos ni bases de datos. No se cambió readiness,
el gate ni el estado de congelamiento.

## Siguiente paso

Lote 03/S03 queda adjudicado documentalmente. Las rutas de adquisición y
recepción de FD que se listan en 017 no se incorporan con esta decisión; su
posible relación S03 requiere revisión humana separada. No comenzar otra
adjudicación ni materializar relaciones adicionales sin una decisión explícita.
