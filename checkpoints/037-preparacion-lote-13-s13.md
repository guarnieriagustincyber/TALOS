# Preparación documental — lote 13, S13 Linux native AIO

Fecha: 2026-10-01

## 1. Objetivo y límites

Preparar para adjudicación humana exclusivamente el lote **S13 — Linux native
AIO**, usando el inventario target-bound x86_64. Esta es una preparación
documental: no adjudica YES/NO/UNKNOWN, no crea relaciones de membership y
no modifica el estado de disposición global de ninguna syscall.

No se ejecutaron TALOS, workloads ni probes; no se modificaron el perfil
seccomp, código funcional ni artefactos protegidos.

## 2. Baseline e invariantes verificados

Hashes verificados antes de editar:

| Artefacto | SHA-256 |
|---|---|
| Manifiesto `files/A_PRE_0_SURFACE_MANIFEST.json` | `dc57a29360efa521342d8824f0ce39bc266eb6bcefd2cf3b80d1144976d4706d` |
| Ledger `files/A_PRE_0_QUALIFICATION_LEDGER.json` | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |

Estado documental de partida:

- S01–S12 están cerradas según sus checkpoints anteriores.
- S12 conserva exactamente tres memberships YES: `io_uring_setup` 425,
  `io_uring_enter` 426 y `io_uring_register` 427.
- S10: 31 YES, 6 NO y 0 UNKNOWN dentro de 37 relaciones.
- S11: 17 YES, 0 NO y 0 UNKNOWN.
- Inventario target-bound: 385 filas; 385/385 disposiciones generales
  `UNKNOWN`; 0 finales.
- `inventory.frozen=false`.
- A-PRE-0: `NOT READY`.
- A-PRE-1: `NOT AUTHORIZED / NOT EXECUTED`.

Los números de syscall consignados abajo se leyeron exclusivamente de las
filas del inventario target-bound vigente.

## 3. Doctrina de trabajo S13 y estado

> **S13 = interfaz Linux native AIO basada en `io_*`: creación/destrucción
> del contexto AIO, envío de operaciones AIO y recolección/espera de eventos
> AIO.**

S13 representa la interfaz native AIO del kernel. No es una clasificación de
todos los efectos que una solicitud pueda producir. Cada candidatura central
queda en estado **`UNREVIEWED / PENDING HUMAN ADJUDICATION`**.

## 4. Candidaturas centrales target-bound

| NR x86_64 | Syscall | Familia / semántica documental | Argumentos, variantes y recursos a revisar | Estado / evidencia registrada |
|---:|---|---|---|---|
| 206 | `io_setup` | Crea un contexto Linux native AIO y devuelve/establece su identificador en `ctx_idp`. | `nr_events`, puntero de contexto de salida, resultado/errores; límite de eventos solicitado y contexto creado. El caso sintético exitoso sólo estableció un contexto vacío. | Candidata S13 `UNREVIEWED`; disposición general `UNKNOWN`. También consta un caso BLOCKED exacto bajo el perfil histórico. |
| 207 | `io_destroy` | Destruye el contexto AIO indicado y afecta solicitudes pendientes conforme a la semántica del kernel. | `ctx_id`; validez/identidad del contexto, solicitudes en vuelo, resultado y errores; distinguir contexto vacío de contexto con I/O pendiente. Caso OBSERVED sólo sobre contexto sintético vacío. | Candidata S13 `UNREVIEWED`; disposición general `UNKNOWN`. También consta un caso BLOCKED exacto bajo el perfil histórico. |
| 209 | `io_submit` | Somete un conjunto de solicitudes AIO (`iocb`) a un contexto. | `ctx_id`, `nr`, vector `iocb**`, cantidad realmente aceptada y errores parciales; opcodes de solicitud como lectura/escritura, FDs, offsets, buffers, prioridades/flags de `iocb` y recursos asociados. El caso OBSERVED tuvo `nr=0` y ningún I/O. | Candidata S13 `UNREVIEWED`; disposición general `UNKNOWN`. También consta un caso BLOCKED exacto bajo el perfil histórico. |
| 208 | `io_getevents` | Espera/recoge eventos de finalización de un contexto. | `ctx_id`, `min_nr`, `nr`, arreglo de eventos y timeout; resultados parciales, cero eventos, interrupción y contexto. No consta llamada exitosa unfiltered en el registro histórico disponible. | Candidata S13 `UNREVIEWED`; disposición general `UNKNOWN`. Consta un caso BLOCKED exacto bajo el perfil histórico. |
| 333 | `io_pgetevents` | Espera/recoge eventos AIO con una máscara de señales proporcionada para la espera. | `ctx_id`, `min_nr`, `nr`, eventos, timeout, `sigset` y tamaño de máscara; disponibilidad/consumo de eventos y semántica de espera/interrupción. La observación histórica fue sólo con mínimo cero. | Candidata S13 `UNREVIEWED`; disposición general `UNKNOWN`. También consta un caso BLOCKED exacto bajo el perfil histórico. |
| 210 | `io_cancel` | Intenta cancelar una solicitud identificada por `iocb` dentro de un contexto y devolver el resultado asociado. | `ctx_id`, puntero/identidad de `iocb`, salida `io_event`, estado de la solicitud, carreras con finalización y resultado/errores; no asumir que cualquier solicitud en vuelo se puede cancelar. | Candidata S13 `UNREVIEWED`; disposición general `UNKNOWN`. Consta un caso BLOCKED exacto bajo el perfil histórico. |

Los argumentos y ejemplos de solicitudes/flags son ejes documentales para la
adjudicación, no una partición exhaustiva ni una determinación de membership.
Las llamadas de setup/destroy no acreditan I/O; submission, espera y
cancelación deben correlacionarse con sus contextos y solicitudes concretas.

## 5. Evidencia dinámica histórica BLOCKED — sólo effect coverage

El manifiesto documenta seis casos Linux native AIO `BLOCKED` con `EPERM`,
uno por syscall central, bajo el perfil:

- `a-pre-native-async-deny-v1`
- SHA-256: `ff44e7f9573fe503fd023792d1e38c44ba8b4ac53275097559eaece82e0ea9e9`
- `seccomp-probe.json`: SHA-256
  `350d5d8c40125417a9475ed7caa77fcd1acf15bc49f80da817a1cb17695f9d8b`
- `isolation.json`: SHA-256
  `17d94bac187ca74b008a34e192c29706e170080e25dc626e13e4b9fb81d8226d`

El conjunto combinado contiene **9/9 denegaciones históricas EPERM**:
seis native AIO (`io_setup`, `io_destroy`, `io_submit`, `io_getevents`,
`io_pgetevents`, `io_cancel`) y las tres llamadas S12 (`io_uring_setup`,
`io_uring_enter`, `io_uring_register`).

Para S13, cada BLOCKED sólo se atribuye a su syscall/caso exacto bajo el
perfil e identidad indicados. El resultado de una llamada no se extiende a
otra syscall AIO ni a todo el dominio S13. El caso se mantiene separado de la
pregunta semántica de membership. Los casos OBSERVED asociados al lote sólo
cubren: setup de contexto sin solicitudes, destrucción de contexto vacío,
submit con cero solicitudes y `io_pgetevents` con mínimo cero; no demuestran
una solicitud AIO completada. No se registró un caso exitoso unfiltered de
`io_getevents` o `io_cancel`. Los artefactos históricos no están re-vinculados
al overlay calificado actual. No se reejecutaron ni validaron probes.

```text
membership documental S13 ≠ effect coverage ≠ disposición global
```

## 6. Cruces con otras superficies (sin adjudicar)

- **S02:** efectos de payload de lectura/escritura realizados por solicitudes
  AIO; S13 cubre la interfaz y no todos los payloads.
- **S03:** FDs usados por `iocb` y el identificador/contexto AIO; separar
  lifecycle de FD/contexto de la interfaz.
- **S05/S06:** buffers, memoria y mappings; no se promueven por aparecer como
  recursos de una solicitud.
- **S07/S08:** solicitudes AIO sobre FDs de red o AF_UNIX; la dimensión de
  red/socket permanece separada.
- **S09:** passing/acquisition de capacidades por mecanismos externos; no
  inferir transferencia de FD desde AIO.
- **S10:** coordinación/espera/eventos; distinguirla de la API native AIO
  que produce/consume eventos.
- **S11:** procesos/hilos, contexto de ejecución y trabajadores; la mera
  ejecución asíncrona no traslada lifecycle de proceso a S13.
- **S12:** io_uring es otra interfaz asíncrona, ya adjudicada por separado;
  no combinar sus syscalls con `io_*`.
- **S14:** POSIX AIO y workers administrados por biblioteca, también
  separados (véase §7).

Los cruces/rutas alternas S02, S12 y S14 constan asimismo en los contextos
S13 del manifiesto. Se registran para adjudicación posterior y no cambian
ninguna membership existente.

## 7. Separación de POSIX AIO / S14

- **S13:** syscalls Linux native AIO del kernel enumeradas en §4.
- **S14:** interfaces de biblioteca como `aio_read`, `aio_write`,
  `lio_listio`, `aio_error`, `aio_return`, `aio_suspend`, `aio_cancel`,
  `aio_fsync` y `aio_init`, y la correlación de workers/syscalls subyacentes.

Las funciones POSIX AIO no son syscalls S13 adicionales. Wrappers libc,
workers internos y rutas de implementación se registran sólo como contexto
S14 o relación auxiliar; sus syscalls subyacentes se atribuyen a sus
superficies canónicas según corresponda. No se fusionan S13/S14 ni se
promueven bibliotecas a candidaturas target-bound.

## 8. Leads fuera del lote

- **Leads adicionales de syscall S13: 0 promovidos.** El inventario muestra
  exactamente las seis candidaturas S13 de §4.
- `eventfd`/`eventfd2` pueden ser contexto de notificación de completions,
  pero son mecanismos auxiliares, no operaciones de la familia Linux native
  AIO; no se promueven aquí.
- Las nueve filas `io_*`/`io_uring_*` vistas en el inventario se separan en
  estas seis native AIO y las tres io_uring adjudicadas como S12.
- Syscalls generales de lectura/escritura, scheduler, señales o memoria no
  se convierten en S13 por proximidad funcional.
- Interfaces `aio_*`, wrappers y workers quedan como contexto S14, no como
  syscalls adicionales ni memberships S13.

## 9. Pendientes de adjudicación humana

Para las seis candidaturas, decidir si la semántica de la syscall pertenece
directamente a la interfaz S13 y fijar el alcance por contexto, solicitudes,
opcodes, FDs/buffers, resultado parcial, espera/cancelación y errores. Resolver
los cruces de §6 sin usar los casos BLOCKED como prueba de membership. Las
seis candidaturas permanecen **`UNREVIEWED / PENDING HUMAN ADJUDICATION`**:
no hay decisiones YES/NO/UNKNOWN adjudicadas ni memberships materializadas.

## 10. Estado de salida

- Manifiesto sin cambios; las seis filas S13 continúan candidatas
  `UNREVIEWED` y con disposición general `UNKNOWN`.
- Disposiciones globales: 385/385 `UNKNOWN`; cero finales.
- `inventory.frozen=false`.
- A-PRE-0: `NOT READY`.
- A-PRE-1: `NOT AUTHORIZED / NOT EXECUTED`.
- S01–S12, incluidas las tres memberships S12, sin cambios.
- S10: 31 YES / 6 NO; sus 12 leads de poll/select/epoll no se promueven.
- S11: 17 YES; sus 14 leads no se promueven.
- Ledger y `requirements.lock` sin cambios.
- No se ejecutaron TALOS, workloads, probes ni otra actividad dinámica.
- No se modificaron seccomp, código funcional, E5/Qwen, corpus, modelos ni
  bases protegidas.
- No se avanzó a adjudicación S13.
