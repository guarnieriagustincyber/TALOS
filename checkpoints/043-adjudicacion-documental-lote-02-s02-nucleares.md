# Adjudicación documental — S02, candidaturas nucleares pendientes

Fecha: 2026-10-01

## 1. Alcance y origen

Esta adjudicación resuelve exclusivamente la inconsistencia detectada en
[checkpoint 042](./042-reconciliacion-global-post-s16.md): el cierre histórico
de S02 no había quitado el estado `UNREVIEWED_CANDIDATE` de las 18 operaciones
nucleares que el manifiesto listaba bajo S02. Por tanto, S02 no estaba
documentalmente completo en la representación machine-readable.

Antes de decidir, se enumeraron las filas actuales del manifiesto. El conjunto
encontrado coincidió exactamente con las 18 candidaturas esperadas. No se
añadieron leads ni syscalls. Se aplicó la doctrina S02 ya establecida, sin
alterarla:

> **S02 = strict Payload I/O:** transferencia efectiva de payload entre
> proceso y descriptor o entre descriptores.

Un YES es una relación semántica condicionada a la operación y variante
descritas; no acredita que haya ocurrido una llamada ni que se hayan
transferido bytes en una ejecución concreta. Para effect coverage hace falta
un resultado efectivo con bytes transferidos. Un NO sólo excluye la relación
S02, nunca la disposición global de la syscall.

## 2. Decisiones individuales

| NR | Syscall | Relación propuesta y semántica relevante | Decisión S02 | Condiciones, cruces y límite |
|---:|---|---|---|---|
| 0 | `read` | Proceso ← descriptor: bytes del objeto identificado por `fd` hacia el buffer. | **YES** | Scope de payload entregado; resultado positivo y parcialidad se distinguen de EOF/error. FD lifecycle S03, recursos/mappings S05/S06, sockets S07/S08, IPC S10 y operaciones async S12–S14 no se absorben. |
| 19 | `readv` | Proceso ← descriptor: bytes distribuidos por los iovecs. | **YES** | Conservar orden, count, longitudes, límites y retorno parcial. Buffers no equivalen a mapping S05/S06; FD y transporte conservan sus dimensiones propias. |
| 17 | `pread64` | Proceso ← descriptor: lectura de bytes con offset explícito. | **YES** | Scope de transferencia positiva; offset y count separados, sin implicar cambio del offset compartido. No absorbe S01 ni S03. |
| 295 | `preadv` | Proceso ← descriptor: lectura posicional hacia vector de buffers. | **YES** | Conservar offset, iovec y retorno parcial; backing/mapping y lifecycle FD son cruces, no efectos absorbidos. |
| 327 | `preadv2` | Proceso ← descriptor: lectura posicional vectorial. | **YES** | Flags admitidos (incluidos `RWF_*` sólo cuando correspondan al ABI/kernel), offset, vectores y parcialidad son ejes separados; no se declara cobertura exhaustiva de flags/ABI. |
| 1 | `write` | Proceso → descriptor: bytes del buffer hacia el objeto identificado por `fd`. | **YES** | Sólo la dimensión payload. No convierte cualquier resultado en transferencia efectiva ni absorbe mutación S04, lifecycle S03 o el transporte de socket/IPC. |
| 20 | `writev` | Proceso → descriptor: bytes tomados de iovecs. | **YES** | Preservar orden, longitudes, count y parcialidad. No absorbe filesystem mutation, FD lifecycle ni superficies de red/IPC. |
| 18 | `pwrite64` | Proceso → descriptor: escritura de bytes con offset explícito. | **YES** | Scope de transferencia positiva; offset y retorno parcial separados. Persistencia/writeback no es payload S02; S03/S04 permanecen independientes. |
| 296 | `pwritev` | Proceso → descriptor: escritura posicional desde iovecs. | **YES** | Conservar offset, vectores y retorno parcial; no absorbe sincronización ni backing/mapping. |
| 328 | `pwritev2` | Proceso → descriptor: escritura posicional vectorial. | **YES** | Flags admitidos (p. ej., `RWF_*` según ABI/kernel), offset, iovec y parcialidad se conservan; no se generaliza a variantes no documentadas. |
| 40 | `sendfile` | Descriptor → descriptor: transferencia en kernel desde `in_fd` a `out_fd`. | **YES** | Sólo bytes devueltos como transferidos; conservar `count`, offset opcional y parcialidad. No clasifica adquisición/lifecycle S03 ni absorbe efectos propios del objeto receptor. |
| 275 | `splice` | Descriptor → descriptor: transferencia de bytes con al menos un extremo pipe. | **YES** | Conservar dirección, offsets opcionales, flags `SPLICE_F_*` y retorno parcial. La condición pipe es obligatoria; pipe/coordination S10 y FD lifecycle S03 no se absorben. |
| 276 | `tee` | Descriptor → descriptor: duplica referencias a buffers entre pipes, dejando disponible el contenido del pipe fuente. | **YES** | Scope pipe-to-pipe y bytes efectivamente duplicados; no clasifica la creación/coordination del pipe S10 ni lifecycle S03. |
| 278 | `vmsplice` | Transferencia de bytes entre memoria de usuario y pipe, de acuerdo con la dirección de los iovecs. | **YES** | Conservar dirección, vectores, flags y parcialidad; requiere retorno positivo para efecto observado. Backing/mapping S05/S06, pipe S10 y FD S03 son dimensiones separadas. |
| 326 | `copy_file_range` | Descriptor → descriptor: transferencia de bytes entre `in_fd` y `out_fd`. | **YES** | Conservar offsets opcionales, length, flags admitidos y parcialidad. No se equipara con writeback/sync ni se absorbe automáticamente mutación S04. |
| 74 | `fsync` | Solicita sincronización del estado asociado al descriptor; no transfiere payload en la doctrina S02. | **NO** | Persistencia/writeback no es transferencia proceso↔FD ni FD↔FD. La decisión no adjudica S04/S05 ni una disposición global. |
| 75 | `fdatasync` | Solicita sincronización de datos y metadata necesaria para recuperación; no es operación de transferencia de payload. | **NO** | Diferenciar writeback/persistencia de transporte S02. No se infiere éxito ni se asigna otra superficie. |
| 277 | `sync_file_range` | Solicita control/sincronización de writeback de un rango según flags; no transporta payload. | **NO** | Offset/range/flags describen writeback, no payload. No adjudica automáticamente S05 ni altera la disposición global. |

**Conteo:** 18 candidaturas: **15 YES / 3 NO / 0 UNKNOWN**.

## 3. Materialización y límites

- Se actualizaron las 18 relaciones S02 en sus filas: YES como
  `HUMAN_ADJUDICATED_CANDIDATE`; NO como
  `HUMAN_ADJUDICATED_NOT_MEMBER`. Cada relación cita este checkpoint.
- El array de membresías S02 conserva sólo las 15 relaciones YES. Las tres
  operaciones de sync permanecen como adjudicaciones NO, no como memberships.
- Cada una de las 18 filas mantiene `disposition_status=UNKNOWN` y
  `classification_status=UNKNOWN`. No se creó OBSERVED/BLOCKED ni se cerró
  ninguna partición global.
- No se modificaron relaciones ni decisiones de S01 o S03–S16.
- Las rutas por descriptor, pathname/dirfd, backing/mapping, sockets,
  `SCM_RIGHTS`, IPC y wrappers/async siguen perteneciendo a sus propias
  dimensiones. Este lote no adjudica otras relaciones por los cruces citados.
- La evidencia histórica de `read` por FD inyectado continúa limitada a
  `SENSOR_SENSITIVITY`; no se utilizó para inferir membership ni effect
  coverage normal del workload.

## 4. Preservación del checkpoint 016

Las 19 exclusiones S02 del checkpoint 016 se preservan exactamente:
`poll` (7), `lseek` (8), `select` (23), `flock` (73), `sync` (162),
`readahead` (187), `epoll_create` (213), `epoll_ctl_old` (214),
`epoll_wait_old` (215), `fadvise64` (221), `epoll_wait` (232),
`epoll_ctl` (233), `pselect6` (270), `ppoll` (271), `epoll_pwait` (281),
`epoll_create1` (291), `syncfs` (306), `epoll_pwait2` (441) y `cachestat`
(451).

El registro de sus 19 revisiones `no_candidate_review` tuvo SHA-256
`88f38627709f11d1a4f163449620b2ff27844cbc42f4d2c2b89910cf3bc1b608`
antes y después de materializar estas 18 decisiones. Se conserva
explícitamente `sync=162`; la fila 76 es `truncate` y no se alteró.

## 5. Estado global y hashes

Estado posterior:

- 385 syscalls target-bound, con nombres/números únicos.
- 385/385 disposiciones globales `UNKNOWN`; cero disposiciones finales.
- `inventory.frozen=false`; A-PRE-0 `NOT READY`.
- A-PRE-1 `NOT AUTHORIZED / NOT EXECUTED`.
- S02: 15 YES materializadas, 3 NO explícitas, 0 UNKNOWN entre estas 18.
- Las 19 exclusiones previas permanecen intactas.
- No se retomó la reconciliación global post-S16.

| Artefacto | SHA-256 |
|---|---|
| Manifiesto `files/A_PRE_0_SURFACE_MANIFEST.json` posterior | `9e0f2f0f07240a0902598f989380c2febd7f2a1ee5f9314d8de156b08cc69a3e` |
| Ledger `files/A_PRE_0_QUALIFICATION_LEDGER.json` | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Checkpoint 016, sin cambios | `081db47e946026af541a90154c2fe1458069cbe08e1c76dc4766faa7ce33345c` |
| Exclusiones S02 del checkpoint 016, representación semántica | `88f38627709f11d1a4f163449620b2ff27844cbc42f4d2c2b89910cf3bc1b608` |
| `checkpoints/index.md` posterior | `658a799cf530754b74a013c9de5b06293b0015d5257f0837373c401f9cdab0f0` |

## 6. Verificación y no ejecución

La comprobación final debe confirmar JSON válido, unicidad de las 385 filas,
385 disposiciones globales UNKNOWN y cero finales, inventario no congelado,
readiness no listo, cierre de las 18 candidaturas, preservación de las 19
exclusiones, inmutabilidad del ledger y lock y limpieza de `git diff --check`.
También debe verificar que sólo cambió semánticamente S02 en el manifiesto.

No se ejecutaron TALOS, workloads, probes, tests, suites, A-PRE-1 ni actividad
dinámica. No se modificaron seccomp, E5/Qwen, corpus, modelos ni bases
protegidas. No se avanzó la reconciliación global.
