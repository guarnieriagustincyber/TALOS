# Adjudicación documental — lote 02, relaciones S02

Fecha: 2026-10-01

## Alcance e identidad

Este checkpoint registra la decisión humana consolidada sobre las 19
referencias S02 inventariadas en
[`015-preparacion-lote-02-s02.md`](./015-preparacion-lote-02-s02.md), partiendo
del estado persistido en `baceb4112f9dd3ac448eca8275ad70cc1c9f5d37` (branch
`main`). La adjudicación resuelve únicamente la relación de cada syscall con
S02; no asigna membresías a otras superficies ni cierra sus variantes.

La directiva mencionó `sync (76)`, pero la tabla x86_64 target-bound y el
manifiesto identifican `sync` como syscall **162**. La decisión se materializa
para `sync (162)`, no para la fila 76 (`truncate`).

## Doctrina aplicada y decisión humana

S02 se limita a **Payload I/O efectivo**:

- transferencia efectiva de payload entre espacio de usuario y un descriptor;
- transferencia efectiva de payload entre pares de descriptores.

Readiness/multiplexación, cambios de offset, locks, sincronización/writeback y
avisos o consultas de page cache no transportan payload bajo esta definición.
Por decisión humana explícita, se excluye de S02 la relación de cada una de
estas 19 filas:

| NR | Syscall | Decisión respecto de S02 | Motivo resumido |
|---:|---|---|---|
| 7 | `poll` | EXCLUIDA | Espera readiness; no transfiere payload. |
| 8 | `lseek` | EXCLUIDA | Cambia/consulta offset; no transfiere payload. |
| 23 | `select` | EXCLUIDA | Espera readiness; no transfiere payload. |
| 73 | `flock` | EXCLUIDA | Gestiona locks; no transfiere payload. |
| 162 | `sync` | EXCLUIDA | Sincroniza writeback global; no es transporte por FD. |
| 187 | `readahead` | EXCLUIDA | Programa prefetch a page cache; no entrega payload al proceso. |
| 213 | `epoll_create` | EXCLUIDA | Crea recurso de readiness; no transfiere payload. |
| 214 | `epoll_ctl_old` | EXCLUIDA | La función relevante es configuración de readiness, no payload. |
| 215 | `epoll_wait_old` | EXCLUIDA | La función relevante es espera/retorno de readiness, no payload. |
| 221 | `fadvise64` | EXCLUIDA | Emite advice sobre page cache; no transporta payload. |
| 232 | `epoll_wait` | EXCLUIDA | Espera readiness; no transfiere payload. |
| 233 | `epoll_ctl` | EXCLUIDA | Configura readiness; no transfiere payload. |
| 270 | `pselect6` | EXCLUIDA | Espera readiness/señales; no transfiere payload. |
| 271 | `ppoll` | EXCLUIDA | Espera readiness/señales; no transfiere payload. |
| 281 | `epoll_pwait` | EXCLUIDA | Espera readiness/señales; no transfiere payload. |
| 291 | `epoll_create1` | EXCLUIDA | Crea recurso de readiness/FD; no transfiere payload. |
| 306 | `syncfs` | EXCLUIDA | Sincroniza writeback del filesystem; no es transporte por FD. |
| 441 | `epoll_pwait2` | EXCLUIDA | Espera readiness/señales; no transfiere payload. |
| 451 | `cachestat` | EXCLUIDA | Consulta estado de page cache; no transfiere payload. |

La incertidumbre histórica sobre el ABI de `epoll_ctl_old` y
`epoll_wait_old` no impide esta adjudicación acotada: no se afirma aquí su ABI
ni equivalencia con la API moderna; se resuelve solamente que esa relación no
pertenece a la superficie S02, definida por transporte efectivo de payload.

## Límites y cruces

La exclusión es unidimensional: significa **NO S02**, no exclusión del
inventario de syscalls ni adjudicación automática a otra superficie. Los
cruces a S03 (FD/ciclo de vida), S04 (filesystem/writeback), S05 (mappings y
page cache), S07 (red), S09 (pasaje de FDs) o S10 (IPC/coordinación) permanecen
como dimensiones separadas y deberán adjudicarse en sus lotes respectivos.
En particular, esta decisión no asigna por inferencia ninguna de las 19 filas
a esas superficies.

Las 19 filas permanecen en el inventario general con `disposition_status:
UNKNOWN`. Ninguna se agrega a `candidate_surface_ids` de S02. Las referencias
originales se conservan como procedencia histórica de la revisión; su estado
de relación adjudicada se registra por fila en el manifiesto y en este
checkpoint. Esta decisión no produce `OBSERVED`, `BLOCKED`, cobertura ni
evidencia de alcanzabilidad.

## Invariantes que permanecen

- 385/385 disposiciones generales continúan `UNKNOWN`.
- `inventory.frozen=false`.
- A-PRE-0 permanece `NOT READY`.
- A-PRE-1 permanece `NOT AUTHORIZED / NOT EXECUTED`.
- No cambia readiness ni se adjudican las demás superficies.
- No se ejecutaron probes, pruebas, suites, TALOS, parsers, validadores A-PRE
  ni workloads.
- No se modificaron VM, overlay, runtime, `requirements.lock`, corpus,
  modelos ni bases de datos.

El resumen de la cola inicial de 204 referencias se conserva como procedencia
histórica; estas 19 relaciones S02 ya no son pendientes de adjudicación. La
exclusión de relación no se cuenta como disposición global ni como
`explicit_exclusions` de syscalls.

## Siguiente paso

Lote 02/S02 queda cerrado documentalmente. El siguiente lote es la preparación
y revisión de S03 — FD hygiene/lifecycle; ninguna membresía S03 se infiere en
este checkpoint.
