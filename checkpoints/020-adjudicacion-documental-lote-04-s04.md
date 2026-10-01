# Adjudicación documental — lote 04, relaciones S04

Fecha: 2026-10-01

## Alcance e identidad

Este checkpoint registra la decisión humana consolidada sobre las 35
candidaturas y seis pistas preparadas en
[`019-preparacion-lote-04-s04.md`](./019-preparacion-lote-04-s04.md), desde
`d5cfacddbdbad286113bcd52cfdf69d52aa1d7a2` (branch `main`). Resuelve sólo la
relación de cada syscall con S04. No adjudica otras superficies, alcanzabilidad,
observación, bloqueo ni disposición global.

## Doctrina aplicada

S04 comprende mutaciones efectivas del estado del filesystem: namespace,
creación/remoción de nodos, tamaño/asignación, permisos, ownership, timestamps
y metadata persistente de objetos filesystem. La pertenencia se determina por
el efecto mutacional y no por el mecanismo de selección del objeto.

Pathname/`dirfd` puede cruzar S01; FD puede cruzar S03; mappings pueden cruzar
S05; memoria anónima/memfd puede cruzar S06. Ningún cruce elimina ni crea por
sí mismo membresía S04. S04 no incluye automáticamente estado de proceso que
sólo condicione mutaciones futuras, consultas, readiness, posicionamiento FD,
coordinación ni estados administrativos filesystem-wide cuya relación siga
sin delimitar.

## Las 35 membresías S04 aceptadas

| NR | Syscall | Decisión y límite de la relación S04 |
|---:|---|---|
| 76 | `truncate` | SÍ — cambio del tamaño del objeto filesystem seleccionado por pathname; la resolución es una dimensión S01 separada. |
| 77 | `ftruncate` | SÍ — cambio del tamaño del objeto filesystem referido por FD. La relación S06 preexistente permanece separada y sin adjudicar. |
| 285 | `fallocate` | SÍ — mutación de asignación/rango del objeto; conservar las particiones por modo/flag y efecto concreto. |
| 82 | `rename` | SÍ — mutación de las entradas del namespace; no equivale a destruir el objeto renombrado o reemplazado. |
| 87 | `unlink` | SÍ — remoción de una entrada del namespace. No implica necesariamente destrucción física del objeto mientras existan otras referencias/enlaces. |
| 86 | `link` | SÍ — creación de una entrada hardlink al objeto seleccionado. |
| 264 | `renameat` | SÍ — mutación de nombres/entradas; mantener origen, destino y resolución por `dirfd` como dimensiones separadas. |
| 263 | `unlinkat` | SÍ — remoción de entrada; conservar `AT_REMOVEDIR`, tipo del objetivo y resolución efectiva. |
| 265 | `linkat` | SÍ — creación de hardlink; conservar flags aplicables y el objeto efectivamente resuelto. |
| 316 | `renameat2` | SÍ — mutación de namespace; conservar `RENAME_NOREPLACE`, `RENAME_EXCHANGE`, `RENAME_WHITEOUT` y otros flags relevantes del ABI target. |
| 83 | `mkdir` | SÍ — creación de directorio/nodo; `umask` que condiciona el mode no queda incluida por esta relación. |
| 84 | `rmdir` | SÍ — remoción de directorio vacío del namespace. |
| 258 | `mkdirat` | SÍ — creación de directorio; `dirfd` selecciona contexto y no adjudica S03 automáticamente. |
| 133 | `mknod` | SÍ — creación de nodo, condicionada al tipo de nodo, mode, device y argumentos aplicables. |
| 259 | `mknodat` | SÍ — creación de nodo; conservar tipo, argumentos, mode/device y resolución por `dirfd`. |
| 88 | `symlink` | SÍ — creación del nodo symlink y almacenamiento de su texto destino. La resolución posterior del symlink pertenece a una dimensión S01 separada. |
| 266 | `symlinkat` | SÍ — creación de symlink; la selección del directorio por `dirfd` es separada y la resolución posterior no se adjudica aquí. |
| 90 | `chmod` | SÍ — mutación de mode/permisos del objeto; la resolución del pathname y el objeto final siguen siendo selectores/variantes. |
| 91 | `fchmod` | SÍ — mutación de mode/permisos del objeto referido por FD; el uso de FD no adjudica S03 automáticamente. |
| 268 | `fchmodat` | SÍ — mutación de mode; conservar condiciones de ABI/flags aplicables a la interfaz target. |
| 452 | `fchmodat2` | SÍ — mutación de mode; conservar particiones por flags y objetivo efectivo. |
| 92 | `chown` | SÍ — mutación de UID/GID propietario; conservar valores especiales, credenciales y objeto final. |
| 93 | `fchown` | SÍ — mutación de ownership del objeto referido por FD; no adjudica S03 por el selector FD. |
| 94 | `lchown` | SÍ — mutación de ownership del symlink mismo, sin trasladar la decisión al objeto destino del enlace. |
| 260 | `fchownat` | SÍ — mutación de ownership; conservar flags, seguimiento/no-seguimiento y objeto final seleccionado. |
| 188 | `setxattr` | SÍ — creación/reemplazo de xattr persistente; conservar nombre/namespace, flags y objeto seleccionado. |
| 189 | `lsetxattr` | SÍ — mutación xattr del symlink mismo bajo semántica no-follow. |
| 190 | `fsetxattr` | SÍ — mutación xattr del objeto referido por FD; el FD es selector, no decisión S03. |
| 197 | `removexattr` | SÍ — remoción de metadata xattr del objeto seleccionado. |
| 198 | `lremovexattr` | SÍ — remoción de xattr del symlink mismo sin seguirlo. |
| 199 | `fremovexattr` | SÍ — remoción de xattr del objeto referido por FD; conservar nombre/namespace y soporte del objeto. |
| 132 | `utime` | SÍ — mutación de atime/mtime; conservar valores, representación y condiciones ABI/legacy aplicables. |
| 235 | `utimes` | SÍ — mutación de atime/mtime; conservar precisión, valores especiales, permisos y objeto final. |
| 261 | `futimesat` | SÍ — mutación de timestamps; conservar la condición legacy y no normalizar ABI/semántica sin evidencia target-bound. |
| 280 | `utimensat` | SÍ — mutación de timestamps; conservar `UTIME_NOW`, `UTIME_OMIT`, `AT_SYMLINK_NOFOLLOW` y demás valores/flags aplicables. |

## Seis pistas separadas

| NR | Syscall | Decisión S04 | Estado y fundamento |
|---:|---|---|---|
| 95 | `umask` | EXCLUIDA | Modifica estado del proceso que condiciona permisos de creaciones futuras; no muta por sí misma metadata persistente de un objeto filesystem. La mutación posterior corresponde a la operación de creación. No se adjudica ninguna otra superficie. |
| 179 | `quotactl` | UNKNOWN | No agregar a candidatos. Delimitar primero si S04 incluye administración de cuotas filesystem-wide y qué comandos son mutacionales. |
| 443 | `quotactl_fd` | UNKNOWN | No agregar a candidatos. Falta cerrar ABI, comando, recurso seleccionado y efectos concretos. |
| 463 | `setxattrat` | UNKNOWN | No agregar por analogía nominal. Requiere evidencia target-bound sobre ABI, objeto, flags y mutación xattr. |
| 466 | `removexattrat` | UNKNOWN | No agregar por analogía nominal. Requiere evidencia target-bound equivalente sobre ABI, selección y efecto. |
| 469 | `file_setattr` | UNKNOWN | No agregar a candidatos. Requiere fuente versionada que delimite atributos modificables, objeto, flags, ABI y efecto filesystem. |

## Efecto e invariantes

- Se ratifican **35** relaciones candidatas S04 existentes; no se agregan filas
  nuevas a `candidate_surface_ids`.
- Se registra la exclusión unidimensional `umask` → S04; no es exclusión de
  `umask` del inventario ni decisión para otra superficie.
- Las otras cinco pistas permanecen sin candidato S04 y `UNKNOWN`.
- Las disposiciones generales de las 385 filas permanecen `UNKNOWN`; no se
  genera `OBSERVED`, `BLOCKED` ni disposición final.
- `inventory.frozen=false`; A-PRE-0 `NOT READY`; A-PRE-1
  `NOT AUTHORIZED / NOT EXECUTED`.
- No se adjudican automáticamente S01, S03, S05, S06, S07, S09, S10 ni S11.
- No se ejecutaron TALOS, probes, tests, suites, parsers, validadores
  dinámicos, comandos dinámicos ni workloads. No se tocó VM, runtime, overlay,
  `requirements.lock`, corpus, modelos ni bases de datos.

Lote 04/S04 queda cerrado sólo en cuanto a estas 35 aceptaciones y la exclusión
de `umask`; las cinco pistas indicadas continúan abiertas. Ninguna otra
adjudicación queda autorizada por este checkpoint.
