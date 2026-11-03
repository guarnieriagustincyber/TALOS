# Adjudicación documental — lote 05, membresías S05

Fecha: 2026-10-01

## Alcance e identidad

Este checkpoint registra la decisión humana del lote 05 presentada en
[`021-preparacion-lote-05-s05.md`](./021-preparacion-lote-05-s05.md), desde el
estado persistido en `b17dd9c4dab098512aa6c148e7d36c613da41c28` (tree
`57898bccde4f10eb9118427aede7612f9e425e66`, parent
`d5cfacddbdbad286113bcd52cfdf69d52aa1d7a2`, branch `main`). La adjudicación
afecta sólo relaciones de membresía con S05 y no cambia disposiciones generales.

## Decisiones humanas

Se aceptan seis relaciones S05, cada una condicionada a que el rango/objeto
afectado sea un mapping file-backed. Se mantiene `madvise` en `UNKNOWN` hasta
particionar sus variantes `MADV_*`. No se promueven las otras 17 pistas.

| ID | NR | Syscall | Decisión S05 | Condición y límites |
|---|---:|---|---|---|
| S05-01 | 9 | `mmap` | YES | Sólo mapping respaldado por objeto file-backed. Excluir de S05 `MAP_ANONYMOUS`, memoria anónima, backing memfd y `memfd_secret`. Conservar `MAP_SHARED`, `MAP_PRIVATE`, FD, offset, length y `PROT_*` como ejes. |
| S05-02 | 10 | `mprotect` | YES | Sólo cuando el rango protegido pertenece a un mapping file-backed. Conservar `PROT_READ`, `PROT_WRITE`, `PROT_EXEC`, `PROT_NONE`, range, length y alignment. El cambio de protección no adjudica S04. |
| S05-03 | 11 | `munmap` | YES | Sólo cuando el rango desmapeado corresponde a un mapping file-backed. Conservar partial unmap, range, length y alignment. No equivale a `close(FD)`, eliminar el objeto filesystem ni mutarlo bajo S04. |
| S05-04 | 25 | `mremap` | YES | Sólo cuando el mapping afectado es file-backed. Conservar growth, shrink, move, `MREMAP_MAYMOVE` y `MREMAP_FIXED`. Cambiar geometría no adjudica S04 ni muta por sí mismo el tamaño del objeto filesystem. |
| S05-05 | 26 | `msync` | YES | Sólo cuando el rango sincronizado pertenece a mapping file-backed. Conservar `MS_SYNC`, `MS_ASYNC`, `MS_INVALIDATE`, `MAP_SHARED` y `MAP_PRIVATE`. Sincronización no es payload I/O S02 ni automáticamente la mutación S04 original; no atribuir a `msync` el store CPU precedente. |
| S05-06 | 28 | `madvise` | UNKNOWN | Relación general pendiente de partición por `MADV_*`; no materializar membresía S05 general ni extender el efecto de una variante a toda la syscall. |
| S05-07 | 329 | `pkey_mprotect` | YES | Sólo cuando el rango protegido pertenece a mapping file-backed. Conservar `PROT_*`, pkey, range, alignment y key validity. La gestión/lifecycle de la key queda separada y no se adjudica automáticamente. |

## Fronteras preservadas

- S05 no absorbe S06: `MAP_ANONYMOUS`, anonymous memory, memfd y
  `memfd_secret` permanecen fuera de las relaciones S05 aprobadas por este
  lote.
- `MAP_SHARED` y `MAP_PRIVATE` son variantes a particionar, no reglas
  automáticas de pertenencia.
- El establecimiento del mapping y los CPU loads/stores sobre ese mapping son
  hechos distintos. Un store no se convierte en syscall S02 por terminar
  afectando bytes; su visibilidad/persistencia se analiza por separado.
- `msync` no adjudica S02 ni S04 por sí mismo.
- `mremap` cambia la geometría del mapping; no implica mutación filesystem.
- `madvise` permanece `UNKNOWN` a nivel general mientras no se adjudiquen sus
  variantes concretas.
- En filas con membresía S06 preexistente, esta decisión adjudica sólo la
  relación S05; no modifica S06 ni ninguna otra superficie.

## Efecto e invariantes

- Membresías S05 aceptadas: **6** (`mmap`, `mprotect`, `munmap`, `mremap`,
  `msync`, `pkey_mprotect`), todas condicionadas por backing/rango file-backed.
- `madvise`: `UNKNOWN`; no se añade otra membresía.
- Las 17 pistas identificadas en 021 permanecen fuera de membresía S05.
- Las disposiciones generales permanecen 385/385 `UNKNOWN`; disposiciones
  finales: **0**. No se genera `OBSERVED` ni `BLOCKED`.
- `inventory.frozen=false`; A-PRE-0 `NOT READY`; A-PRE-1
  `NOT AUTHORIZED / NOT EXECUTED`.
- No se ejecutaron TALOS, probes, tests, suites, workloads, parsers/validadores
  dinámicos ni comandos dinámicos. No se tocaron VM, runtime, overlay,
  `requirements.lock`, corpus, modelos ni bases de datos.

Lote 05/S05 queda materializado sólo en el alcance indicado. No se promueven
las 17 pistas ni se inicia S06.
