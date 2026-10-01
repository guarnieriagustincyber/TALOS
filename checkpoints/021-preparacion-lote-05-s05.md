# Preparación documental — lote 05, S05 file-backed memory mappings

Fecha: 2026-10-01

## 1. Objetivo, identidad y estado de autoridad

Preparar para revisión humana las candidaturas y pistas S05 del manifiesto
target-bound, sin resolver membresías ni modificar la calificación. Punto de
partida: commit `b17dd9c4dab098512aa6c148e7d36c613da41c28`, tree
`57898bccde4f10eb9118427aede7612f9e425e66`, parent
`d5cfacddbdbad286113bcd52cfdf69d52aa1d7a2`, branch `main`.

Alcance de esta preparación: identificar y organizar la evidencia documental
ya disponible, anotar semántica/variantes, cruces y preguntas. Todas las
relaciones en este informe están **PENDING HUMAN ADJUDICATION**. La existencia
de una candidatura es un estado previo del manifiesto, no una decisión de este
lote; una pista potencial tampoco es una candidatura.

## 2. Doctrina provisional S05 — no es una adjudicación

Como criterio de trabajo para la revisión:

> S05 comprende mecanismos mediante los cuales un proceso establece,
> modifica, mantiene, sincroniza o elimina mappings de memoria respaldados por
> un objeto externo/file-backed, incluyendo la relación entre el mapping, el
> objeto de respaldo y sus modos de acceso/visibilidad.

El objeto de respaldo decide la frontera S05/S06: un archivo u otro objeto
file-backed puede ser S05; memoria anónima o memfd se analiza en S06. No toda
invocación de `mmap` es S05. En particular, `MAP_ANONYMOUS` no entra a S05 por
el mero hecho de usar la syscall `mmap`, y `memfd_create` permanece en la
revisión S06 sin trasladarse automáticamente a S05.

Las superficies no son exclusivas:

- S01 selecciona/resuelve objetos; no sustituye la dimensión del mapping.
- S02 cubre transferencia efectiva de payload por FD; stores/loads de CPU y
  sincronización de mapping no se convierten en S02 por analogía.
- S03 cubre el ciclo de vida del FD backing; recibir un FD como argumento no
  adjudica S03 automáticamente.
- S04 cubre mutaciones persistentes del filesystem; crear/modificar un mapping
  no equivale por sí solo a mutar el objeto filesystem.
- S05 cubre el mapping file-backed y su relación con el respaldo.
- S06 cubre memoria anónima/memfd, no el mapping file-backed como tal.
- S10/S11 pueden describir coordinación o lifecycle de proceso; identificar
  esos cruces no adjudica esas relaciones.

## 3. Estado de cola

- **7 candidaturas S05 preexistentes**, todas con `candidate_membership_status
  = UNREVIEWED` y disposición general `UNKNOWN`.
- **17 referencias potenciales S05** sin candidato S05, todas con disposición
  `UNKNOWN`; ninguna se promueve en esta preparación.
- Total filas relevantes: **24**, sin cambiar candidaturas, disposiciones ni
  referencias del manifiesto.
- El manifiesto ya identifica S05 como **File-backed memory mappings**, con
  recurso “File-backed mappings, including mappings of resources outside the
  visible pathname namespace” y ejes de backing FD/objeto, `MAP_SHARED` versus
  `MAP_PRIVATE`, protección/offset/longitud/remap/sync y lifecycle.

## 4. Candidaturas S05 existentes — todas pendientes de decisión humana

Las siete filas ya están en `candidate_surface_ids`; sus relaciones S05 se
presentan para revisión, no se ratifican aquí.

| NR / syscall | Semántica pertinente para S05 | Backing object y condición | Flags/variantes a mantener separados | Cruces que revisar (no adjudicados) | Pregunta de adjudicación |
|---|---|---|---|---|---|
| 9 `mmap` | Establece un mapping en el espacio virtual; el mapping puede ser file-backed o anónimo. | `fd`, offset, longitud y objeto respaldante; distinguir archivo/otro objeto externo de `MAP_ANONYMOUS` y memfd. No toda invocación pertenece a S05. | `MAP_SHARED`, `MAP_PRIVATE`, `MAP_ANONYMOUS`, protecciones `PROT_READ/WRITE/EXEC/NONE`, offset, longitud, flags adicionales del ABI target. `MAP_SHARED` no representa toda `mmap`. | S01 selección del objeto; S02 transferencia FD vs stores; S03 FD/backing; S04 efecto persistente de stores; S06 anonymous/memfd; S10 sharing/coordinación. | ¿Qué variantes respaldadas por objeto externo pertenecen a S05 y cómo se separan de anonymous/memfd y de la semántica de stores posteriores? |
| 10 `mprotect` | Cambia las protecciones de páginas virtuales de un rango ya mapeado; no es por sí misma una escritura persistente al backing file. | Rango y mapping existente; la pertenencia a S05 depende de que las páginas correspondan a mapping file-backed. | `PROT_READ`, `PROT_WRITE`, `PROT_EXEC`, `PROT_NONE`, longitud, alineación y errores/condiciones ABI; preservar mapping backing. | S06 si el rango es anonymous/memfd; S04 no se infiere porque cambie protección; S10 si intervienen mappings compartidos. | ¿Se limita S05 a aplicar la protección sobre un mapping file-backed identificado, con las variantes de protección expresas? |
| 11 `munmap` | Elimina un mapping/rango del espacio virtual; puede separar parte o todo un mapping. | Dirección y longitud del rango y mapping que lo cubre; backing puede ser file-backed, anonymous o memfd. | Rango, alineación, solapamiento/parcialidad y efecto de retirar/reducir el mapping; distinguir la vida del mapping de la vida del objeto backing. | S03 el FD puede haberse cerrado sin terminar el mapping; S04 no significa borrar/modificar el archivo; S06 para anonymous/memfd. | ¿La relación S05 cubre sólo desmontar rangos de mappings file-backed y conserva separada la liberación del objeto? |
| 25 `mremap` | Cambia geometría/tamaño/ubicación de un mapping existente; puede crecer, reducirse o moverse. | Mapping original, backing object y rango nuevo; no asumir que toda llamada involucra archivo. | Tamaños viejo/nuevo, `MREMAP_MAYMOVE`, `MREMAP_FIXED` y flags admitidos por el ABI target; preservar backing/offset y distinguir geometría de mutación del objeto. | S06 para anonymous/memfd; S03 por posible descriptor backing pero no necesariamente consultado en la operación; S04 no se deduce de cambiar geometría. | ¿Qué remaps file-backed entran en S05 y cómo se conservan las condiciones de backing, movimiento y crecimiento? |
| 26 `msync` | Solicita sincronización del rango mapeado con el backing object o su estado; no es la transferencia S02 definida como payload por FD. | Rango asociado a mapping y objeto respaldante; `MAP_SHARED` es eje especialmente relevante; no asumir que `MAP_PRIVATE` propaga modificaciones del mapping al archivo. | `MS_SYNC`, `MS_ASYNC`, `MS_INVALIDATE`, alineación/rango y mapping vigente; distinguir modificación en memoria de propagación/sincronización al respaldo. | S02 no por movimiento interno de datos; S03 FD inicial no describe toda la vida del mapping; S04 por posible persistencia, pero sincronizar no equivale a la mutación original; S06 si backing anonymous/memfd. | ¿Qué parte de `msync` pertenece a S05 según mapping/backing/flag, y cómo se evita atribuirle el store que originó el contenido? |
| 28 `madvise` | Aplica advice/operaciones a un rango virtual; significado y efecto dependen de `advice`. No todos los advice son equivalentes ni necesariamente modifican el mapping. | Rango del mapping y backing; puede afectar mappings file-backed o anonymous. | `MADV_*` específico, rango y disponibilidad por versión; separar recomendaciones de comportamiento de operaciones con efecto sobre páginas, backing o semántica de acceso. | S06 para anonymous/memfd; S10 si advice afecta shared pages/coordinación; S04 no automática; S02 no por posible actividad de page cache. | ¿Qué advice, si alguno, forma parte de la gestión S05 de mappings file-backed, y cuáles son sólo hints o corresponden a otra dimensión? Mantener subcasos ambiguos abiertos. |
| 329 `pkey_mprotect` | Cambia protecciones de páginas e incorpora una protection key. | Rango de mapping existente y backing file-backed; el objeto subyacente no se selecciona mediante esta syscall. | Protecciones `PROT_*`, `pkey`, validez/asignación de key, rango/alineación y ABI. No confundir protección con contenido persistente. | S06 para anonymous/memfd; gestión de keys/estado de proceso fuera de S05 salvo relación explícita. | ¿Se acepta sólo el efecto de protección en mapping file-backed, manteniendo separada la asignación/lifecycle de protection keys? |

## 5. Separación de `mmap` y efectos de contenido

Mantener como unidades distintas:

```text
mmap(MAP_SHARED, file-backed fd)
    → establecer mapping            [posible dimensión S05]
CPU store sobre páginas mapeadas
    → efecto de contenido/backing   [clasificar por evidencia aparte]
msync(...)
    → petición de sincronización    [S05 a revisar; no S02 por analogía]
truncate(...)
    → cambio de tamaño filesystem  [S04 adjudicado en lote 04]
```

Para `MAP_PRIVATE`, modificación/visibilidad a través del mapping no debe
equipararse automáticamente a persistencia en el backing. Para `MAP_SHARED`,
el tipo de objeto, permisos, estado del mapping, stores y sincronización son
dimensiones distintas. El informe no determina causalidad, contenido final ni
enforcement.

## 6. Referencias potenciales S05 — pistas, no candidaturas

Las 17 filas siguientes sólo contienen referencias `potential_surface_refs`;
no se añaden a `candidate_surface_ids`. Todas las relaciones permanecen
**PENDING HUMAN ADJUDICATION**.

| NR / syscall | Semántica/interés posible | Objeto y variante a esclarecer | Cruces posibles | Pregunta para revisión humana |
|---|---|---|---|---|
| 27 `mincore` | Consulta residencia de páginas de un rango; por sí misma es observacional, no establece ni muta un mapping. | Dirección/longitud y mapping existente; file-backed, anonymous o memfd. | S06 según backing; no equiparar consulta de residencia con gestión/mutación S05. | ¿La observación de estado de páginas pertenece al alcance S05 o debe quedar fuera? No decidir por el hecho de consultar un rango mapeado. |
| 149 `mlock` | Solicita que páginas de un rango permanezcan residentes/bloqueadas en memoria. | Rango mapeado y tipo de backing; comportamiento de resource limits/privilegios. | S06 si anonymous/memfd; posible S10 para páginas compartidas. | ¿El pinning/residencia de páginas forma parte del lifecycle de mapping file-backed S05? |
| 150 `munlock` | Libera el bloqueo/residencia solicitada previamente para páginas de rango. | Rango, páginas bloqueadas y mapping/backing actual. | S06 según backing; no confundir liberar páginas residentes con `munmap`. | ¿La gestión de residencia entra en S05 aunque no establezca ni elimine el mapping? |
| 151 `mlockall` | Bloquea páginas actuales y/o futuras del proceso conforme a flags. | Conjunto de mappings del proceso; flags de alcance current/future y límites. | S06 para memoria anónima; S11/estado de proceso por alcance; S10 según páginas compartidas. | ¿El alcance global sobre mappings heterogéneos cabe en S05, o requiere partición por backing? |
| 152 `munlockall` | Desbloquea páginas previamente bloqueadas del proceso. | Estado agregado de páginas actuales; tipo de mapping variable. | S06, S11/estado de proceso. | ¿Se modela por mapping/backing en S05 o queda fuera de su frontera file-backed? |
| 216 `remap_file_pages` | Interfaz legacy de remapeo de páginas de un mapping; requiere verificar vigencia/semántica target y relación con `mmap` moderno. | Mapping y rangos/páginas, flags y ABI versionado; no inferir por nombre que remapea cualquier archivo. | S05 por mapping; S06 dependiendo del respaldo. | ¿Qué efecto/ABI sigue aplicando en el kernel target y constituye una dimensión S05 diferenciada? |
| 237 `mbind` | Establece política NUMA para páginas de un rango de memoria. | Rango, nodos y policy flags; file-backed vs anonymous y flags como migración/preferred policy deben particionarse. | S06 para anonymous/memfd; S10 si páginas compartidas; coordinación/afinidad no equivale a mapping lifecycle. | ¿Política de colocación de páginas pertenece a S05 o es una dimensión de memoria separada? |
| 238 `set_mempolicy` | Cambia política NUMA del proceso para futuras asignaciones. | Mode, nodemask y flags; afecta asignaciones según política/contexto, no necesariamente mapping ya existente. | S06 y estado de proceso; S11 por política del proceso. | ¿Estado de proceso que condiciona mappings futuros queda fuera de S05 provisional? |
| 239 `get_mempolicy` | Consulta política NUMA global o asociada a una dirección, según flags. | Dirección opcional, mode/nodemask y flags; query frente a política de rango. | S06 por memoria; no mutación de mapping ni del backing. | ¿Consulta de política entra en S05 o se conserva como pista de memoria/estado? |
| 256 `migrate_pages` | Solicita migración de páginas entre nodos para procesos identificados. | PID, nodos origen/destino, páginas y permisos; puede abarcar mappings de distintos backings. | S11 por proceso objetivo; S06 y S10 según tipos/shared memory. | ¿Migración de páginas file-backed se considera “mantener mapping” S05, o es otra capa de gestión física? |
| 279 `move_pages` | Consulta o cambia ubicación NUMA de páginas de un proceso, según argumentos/modo. | PID, direcciones, nodos destino y status; posible modo query. | S11 por PID; S06/compartida según backing; distinguir consulta de migración. | ¿Qué subcasos mutacionales y de consulta, si alguno, pertenecen a S05? |
| 325 `mlock2` | Variante de bloqueo de páginas con flags adicionales y posible bloqueo bajo demanda. | Rango, `MLOCK_ONFAULT` y límites; backing file-backed vs anonymous. | S06; S10 para memoria compartida. | ¿Se incluye residency/on-fault en S05 o se excluye como gestión física separada? |
| 330 `pkey_alloc` | Asigna una protection key para usar con protección de páginas; no cambia por sí misma un mapping concreto. | Flags y access rights iniciales; recurso de key y estado de proceso/threads. | Puede preceder `pkey_mprotect`; no es necesariamente S05 mapping; estado de proceso. | ¿Asignación de key pertenece a lifecycle de mapping o queda como recurso de protección separado? |
| 331 `pkey_free` | Libera una protection key; el efecto respecto de páginas ya asignadas debe delimitarse por ABI/kernel. | Key ID, mappings que la usaban y comportamiento ante liberar. | S11/proceso y `pkey_mprotect`; posible interacción S05, no equivalencia con `munmap`. | ¿Hay efecto directo suficiente sobre mappings file-backed para S05 o sólo gestión de key? |
| 440 `process_madvise` | Aplica advice a rangos de otro proceso vía pidfd y vectores de iovec, según operación/permiso. | PIDFD, rangos remotos, advice, flags/versión y objeto respaldante de cada rango. | S11 por proceso objetivo; S03 por pidfd; S06/S10 según memoria. | ¿Qué advice tiene efecto sobre mappings file-backed y debe relacionarse con S05, manteniendo target-process y autorización aparte? |
| 450 `set_mempolicy_home_node` | Configura home node para un rango de direcciones bajo reglas de política de memoria. | Rango, home node, flags/privilegios y mapping/backing. | S06; estado/política de memoria; S11 si se aplica a otro proceso (no asumirlo por nombre). | ¿Política de nodo para un rango es gestión S05 o capa NUMA independiente? Requiere evidencia de efecto/backing. |
| 462 `mseal` | Sella un rango virtual contra ciertas operaciones futuras; el conjunto exacto de operaciones/flags debe ligarse al ABI target. | Rango, flags/semántica de seal y tipo de mapping; puede impedir cambios de mapping/protección. | S06 si el rango es anonymous/memfd; S11 por lifecycle del proceso/rango. | ¿Sellar un rango constituye mantenimiento/protección del mapping S05 cuando es file-backed, y cómo se particiona por seal/objeto? |

## 7. Variantes transversales y ambigüedades abiertas

La revisión humana debería mantener separadas, cuando sean relevantes:

- backing file/objeto externo, FD backing, anonymous, memfd y objetos no
  persistentes;
- `MAP_SHARED`, `MAP_PRIVATE`, `MAP_ANONYMOUS` y otros flags del ABI target;
- `PROT_READ`, `PROT_WRITE`, `PROT_EXEC`, `PROT_NONE`, offsets y longitudes;
- lifecycle de mapping frente a load/store, persistencia del contenido o
  mutación filesystem;
- geometría `mremap` (crecimiento, reducción, movimiento) frente a tamaño del
  objeto filesystem;
- `msync` (rango, `MS_SYNC`/`MS_ASYNC`/`MS_INVALIDATE`) frente al store que
  produjo los bytes y frente a transferencia S02;
- cada `MADV_*` por su semántica concreta: advice/hint, operación sobre
  páginas, efecto sobre backing y disponibilidad por versión;
- rango parcial, alineación, objeto, flags, permisos y resultado observado.

Las preguntas que siguen abiertas incluyen si protecciones/unmap/remap sobre
mapping file-backed son candidaturas S05 condicionadas por backing; si las
interfaces de residencia, NUMA, page-residency query y protection keys
pertenecen a S05 o a una dimensión separada; y qué efectos de `madvise` son
advisory frente a operaciones específicas. Ninguna de estas cuestiones se
resuelve por este informe.

## 8. Evidencia histórica y límite de inferencia

El ledger documenta dos subcasos históricos acotados de mappings: una
sensibilidad de sensor con `mmap(MAP_SHARED)`, flush y lectura externa, y un
caso `BLOCKED` de mapping compartido con FD no pasado, limitado al path probado.
El CPU store no fue un evento de syscall; `MAP_PRIVATE` y otras variantes
permanecen abiertas. Esos subcasos no adjudican las membresías S05 de este
lote, no cierran la superficie y no alteran las 385 disposiciones generales
`UNKNOWN`.

La evidencia primaria de identidad, números, candidaturas, leads y
definiciones usada aquí es el manifiesto target-bound y el ledger en el commit
indicado. La especificación A-PRE-0 local mantiene la separación S05/S06 por
objeto backing y limita el crédito de mappings a casos exactos. No se consultó
ni modificó la VM, ni se ejecutaron herramientas para obtener nueva evidencia.

## 9. Resultado y estado normativo

- 7 candidaturas existentes para S05, todas **PENDING HUMAN ADJUDICATION**.
- 17 pistas S05 separadas, todas **PENDING HUMAN ADJUDICATION** y sin
  promoción a `candidate_surface_ids`.
- Adjudicaciones YES/NO: **0**.
- Membresías o exclusiones materializadas: **0**.
- 385/385 disposiciones generales `UNKNOWN`; disposiciones finales: **0**.
- `inventory.frozen=false`; A-PRE-0 `NOT READY`; A-PRE-1
  `NOT AUTHORIZED / NOT EXECUTED`.
- Manifiesto y ledger no se modifican; no cambia gate ni readiness.
- No se ejecutaron TALOS, probes, tests, pytest, suites, parsers/validadores
  dinámicos, benchmarks, workloads ni proveedores. No se tocaron VM, runtime,
  overlay, `requirements.lock`, corpus, modelos ni bases de datos.

## 10. Preguntas para la revisión humana

1. ¿La relación de `mmap` con S05 se limita a backings file-backed y qué
   tratamiento reciben `MAP_SHARED`, `MAP_PRIVATE` y `MAP_ANONYMOUS`?
2. ¿Se aceptan `mprotect`, `pkey_mprotect`, `munmap` y `mremap` sólo cuando
   operan sobre rangos cuyo backing es S05, y qué particiones de protección,
   movimiento y lifecycle son necesarias?
3. ¿Qué unidades de `msync` están dentro de S05, particularmente por flags,
   tipo de mapping y relación con el objeto backing, sin atribuir el store ni
   clasificarlo como S02?
4. ¿`madvise` queda como candidatura completa, se restringe a advice
   determinados o algunas operaciones permanecen UNKNOWN?
5. Para las 17 pistas, ¿cuáles son membresías, exclusiones unidimensionales o
   UNKNOWN, y qué evidencia concreta respalda cada decisión?
6. ¿Page locking, NUMA policy/migration, `mincore`, protection-key allocation y
   `mseal` pertenecen a S05 sólo cuando se vinculan a mapping file-backed, o
   corresponden a una dimensión separada?
7. ¿Qué variantes del ABI/kernel target requieren mantenerse abiertas por
   falta de evidencia específica?

## 11. Archivos y verificación de preparación

Este lote crea este checkpoint y agrega su referencia al índice de
checkpoints. No modifica manifiesto ni ledger. Las relaciones anteriores
permanecen **PENDING HUMAN ADJUDICATION**.
