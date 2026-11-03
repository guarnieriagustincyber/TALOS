# Preparación del lote 04 — S04 filesystem mutations

Fecha: 2026-10-01

## Alcance e identidad

Preparación documental desde el commit
`d5cfacddbdbad286113bcd52cfdf69d52aa1d7a2` (branch `main`). Este informe
prepara para revisión humana las relaciones S04 ya candidatas y las pistas
S04 aún pendientes. No adjudica, aprueba ni excluye ninguna relación.

La superficie S04 vigente es **Filesystem namespace and metadata mutation**.
Su recurso declarado comprende nombres de filesystem, contenido de objetos,
metadata y creación/remoción de nodos; contempla rutas por pathname/dirfd y FD
targeted, resolución sensible a mounts/symlinks/races, y flags/resultados
específicos de operación. Las superficies alternativas declaradas son S02,
S03, S05 y S06.

## Estado resumido de la cola

- **35 filas** ya contienen S04 en `candidate_surface_ids`; sus relaciones
  siguen `UNREVIEWED`.
- **6 filas** contienen una referencia potencial pendiente a S04 y todavía no
  tienen candidato: `umask` (95), `quotactl` (179), `quotactl_fd` (443),
  `setxattrat` (463), `removexattrat` (466) y `file_setattr` (469).
- Las 41 filas anteriores mantienen disposición global `UNKNOWN`.
- El hecho de que una operación use pathname/`dirfd`/FD no decide por sí mismo
  si es membresía S04. Debe evaluarse el efecto de filesystem/metadata y su
  relación con las otras superficies.

## Candidaturas S04 existentes para revisión humana

Estas 35 relaciones ya existen en el manifiesto. La tabla las ordena por
familia semántica como guía de revisión; **no las ratifica**.

| Familia a revisar | NR / syscalls con candidatura S04 | Condición o frontera que requiere revisión |
|---|---|---|
| Tamaño, contenido asignado y espacio | 76 `truncate`; 77 `ftruncate`; 285 `fallocate` | Pathname frente a FD; cambio del tamaño o asignación del objeto frente a asignación de espacio; `ftruncate` también está candidateada para S06, cuya relación debe evaluarse independientemente. |
| Namespace: mover, enlazar y quitar | 82 `rename`; 87 `unlink`; 86 `link`; 264 `renameat`; 263 `unlinkat`; 265 `linkat`; 316 `renameat2` | Fuente y destino, `dirfd`, reemplazo/colisión, symlink, mount, hardlink, flags de `renameat2` y efectos sobre nombres versus objeto. Path resolution cruza S01; FD/dirfd e identidad pueden cruzar S03. |
| Crear o eliminar nodos/directorios | 83 `mkdir`; 84 `rmdir`; 258 `mkdirat`; 133 `mknod`; 259 `mknodat` | `dirfd`, tipo de nodo y mode/device, permisos, umask, mount y resolución del nombre. No asumir que `umask` queda adjudicada con estas operaciones. |
| Symlinks | 88 `symlink`; 266 `symlinkat` | El nuevo enlace guarda un pathname como contenido del symlink; separar creación del enlace de resolución/seguimiento posterior (S01). |
| Permisos y ownership | 90 `chmod`; 91 `fchmod`; 268 `fchmodat`; 452 `fchmodat2`; 92 `chown`; 93 `fchown`; 94 `lchown`; 260 `fchownat` | Pathname/FD/`dirfd`, seguir o no symlink, flags de las variantes nuevas, credenciales, ownership y cambios de mode derivados de ownership. No derivar una membresía S03 sólo por la variante FD. |
| Extended attributes | 188 `setxattr`; 189 `lsetxattr`; 190 `fsetxattr`; 197 `removexattr`; 198 `lremovexattr`; 199 `fremovexattr` | Crear/reemplazar/eliminar nombre xattr, flags, symlink seguido o no, FD frente a pathname y namespace xattr. Lecturas/listado de xattrs aparecen en S01; la operación de mutación es la cuestión separada de S04. |
| Timestamps | 132 `utime`; 235 `utimes`; 261 `futimesat`; 280 `utimensat` | Precisión y valores especiales, pathname/FD/`dirfd`, flags no-follow, resolución de symlink y permisos. `futimesat` es legacy; no normalizarlo a otra variante sin verificar el ABI target. |

Las categorías no son particiones de membresía exclusivas ni decisiones
canónicas. Los números y nombres provienen del registro x86_64 target-bound.

## Referencias potenciales S04 pendientes

| NR / syscall | Evidencia disponible y objeto/estado afectado | Variante, condición o incertidumbre | Cruces y pregunta para revisión humana | Relación propuesta (no adjudicada) |
|---:|---|---|---|---|
| 95 `umask` | Cambia la máscara del proceso aplicada al mode de futuras creaciones; no muta directamente un objeto filesystem existente. | Valor de máscara y relación temporal con `mkdir*`, `open*`, `mknod*` y otras creaciones. Debe distinguirse estado del proceso del efecto final de cada creación. | S04 por su efecto condicionante en metadata de nuevos nodos; S11/proceso por estado del proceso. ¿El límite S04 incluye controles previos de metadata aunque no modifiquen por sí solos el filesystem? | Resolver si S04 cubre esta dimensión condicionante o si permanece fuera/UNKNOWN; no tratar pathname inexistente como prueba. |
| 179 `quotactl` | Interfaz de control de cuotas, con operación y argumentos que dependen del comando; puede afectar configuración/estado de cuotas del filesystem. | Comando, tipo de cuota, identificador, ruta/dispositivo y privilegios; no inferir la semántica exacta por el nombre. | Posible cruce con metadata/política del filesystem y con superficies de control; ¿el recurso y efectos caben en S04 o exceden su alcance de mutaciones de objeto/namespace? | Mantener la relación abierta hasta delimitar comando, objeto y efecto bajo una fuente versionada. |
| 443 `quotactl_fd` | Variante que incorpora un FD en la selección del contexto de cuotas; el nombre no basta para concluir efecto ni ABI completo. | Identidad/clase del FD, comandos, flags, versión del kernel y alcance filesystem-wide frente a objeto. | S03 por uso de FD; posible S04 por configuración/consulta de cuotas. El FD selector no es por sí mismo mutación filesystem S04. | Revisar semántica y particiones antes de decidir S04; no inferir una membresía por el argumento FD. |
| 463 `setxattrat` | Nombre/tabla sugieren establecer un extended attribute mediante una interfaz relativa a directorio; aún falta cierre documental de argumentos y semántica exactos del target. | `dirfd`, pathname, flags, follow/no-follow, namespace xattr, creación/reemplazo y estructura/ABI. | S01 para resolución/selección; S03 para FD/dirfd; S04 si el efecto confirmado modifica xattr. ¿Qué objeto se altera y bajo qué flags? | Referencia sustantiva a revisar; no convertirla en miembro sólo por similitud nominal con `setxattr`. |
| 466 `removexattrat` | Nombre/tabla sugieren retirar un extended attribute mediante interfaz relativa a directorio; falta confirmar la semántica exacta del syscall target. | `dirfd`, pathname, selección del symlink, namespace/nombre xattr y ABI/flags. | S01 para resolución; S03 por `dirfd`; S04 si el efecto confirmado elimina metadata xattr del objeto seleccionado. | Mantener como lead pendiente hasta contar con evidencia de interfaz target-bound. |
| 469 `file_setattr` | Nombre/tabla sugieren modificar atributos de un objeto file, pero no identifican por sí solos los campos admitidos ni la interfaz del kernel target. | Objeto seleccionado, máscara de atributos, flags, permisos, estructura/versionado y posible ruta por FD/handle. | S04 si muta metadata; S03 si recibe una capacidad; S01 si usa resolución de objeto. ¿Qué atributos y recursos quedan bajo la llamada exacta? | `UNKNOWN` hasta revisar fuente ABI/versionada y campos modificables; no inferir por nombre. |

Las seis referencias no cambian la lista de 35 candidaturas existentes. Una
relación aceptada para una fila tampoco adjudicaría automáticamente otras
superficies ni la disposición general.

## Límites intersuperficie a conservar

- **S01:** resolución/selección de objeto por pathname, symlink o `dirfd`.
  S04 pregunta por la mutación resultante; no toda resolución es mutación.
- **S03:** identidad, origen y ciclo de vida de capacidades FD. Una forma
  `f*`/`*at` exige revisar descriptor/`dirfd`, pero no decide S04 por sí sola.
- **S05:** mappings file-backed. `truncate`/`ftruncate`/`fallocate` pueden
  interactuar con archivos mapeados; no se adjudica por ello una relación S05
  adicional ni se confunde con la mutación S04.
- **S06:** objetos anónimos/memfd. El cruce explícito `ftruncate` (77) debe
  permanecer abierto por separado; una adjudicación S04 no adjudica S06.
- Xattrs de consulta en S01 y xattrs de mutación en S04 son efectos distintos;
  no trasladar automáticamente membresía entre ellos.
- Hardlink, symlink, rename y unlink cambian relaciones del namespace y pueden
  tener efectos distintos sobre la identidad/vida del objeto. Registrar
  variante y resultado, no reducirlos a “path syscall”.

## Fuentes y límites de evidencia

La fuente autoritativa local para números, `candidate_surface_ids`,
`potential_surface_refs`, estados actuales y definiciones de S01/S03/S04/S05/S06
es el manifiesto target-bound en el commit indicado. Las fuentes Linux
man-pages sugeridas para cotejar interfaces incluyen `umask(2)`,
`quotactl(2)`, `quotactl_fd(2)` si está disponible, `setxattr(2)`,
`removexattr(2)`, y las páginas de las operaciones de namespace, permisos,
ownership, timestamps y asignación mencionadas en la tabla de candidaturas.
No se declara verificación nueva contra man-pages ni fuente versionada del
kernel 7.0 en esta preparación; en especial, las interfaces nuevas
`quotactl_fd`, `setxattrat`, `removexattrat` y `file_setattr` requieren fuente
target-bound adecuada antes de afirmar su ABI/particiones.

## Estado e invariantes

- Relaciones S04 ya candidatas: **35**, todas `UNREVIEWED`.
- Referencias potenciales pendientes S04: **6**, todas sin adjudicar.
- Nuevas membresías/exclusiones: **0**.
- Las 385 disposiciones generales siguen `UNKNOWN`; `inventory.frozen=false`;
  A-PRE-0 `NOT READY`; A-PRE-1 `NOT AUTHORIZED / NOT EXECUTED`.
- Manifiesto, ledger e índice no se modifican en esta preparación.
- No se ejecutaron probes, pruebas, suites, parsers, validadores, comandos
  dinámicos, TALOS ni workloads. No se tocó VM, overlay, runtime,
  `requirements.lock`, corpus, modelos ni bases de datos.
- Único archivo creado por este lote: este informe; no se hace commit.

Siguiente paso: revisión humana de las 35 relaciones candidatas existentes y
las seis referencias potenciales, atendiendo primero a las fronteras de
resolución/path/FD/mapping y a la evidencia insuficiente para las interfaces
nuevas. No materializar cambios canónicos hasta recibir decisiones explícitas.
