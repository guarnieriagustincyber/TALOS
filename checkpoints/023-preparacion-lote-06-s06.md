# Preparación documental — lote 06, S06 anonymous / memfd-backed memory

Fecha: 2026-10-01

## 1. Autoridad, identidad y alcance

Preparación para revisión humana posterior; no adjudica ni materializa ninguna
relación S06. Estado de partida verificado: commit
`f81134fc2293916210d53c8065f3a0049e52b0b4`, tree
`c322e78980ac72f24c66b1396014faefaac074a9`, parent
`b17dd9c4dab098512aa6c148e7d36c613da41c28`, branch `main`.

La fuente canónica de candidaturas, referencias, nombres/números del ABI y
definición vigente de S06 es
[`A_PRE_0_SURFACE_MANIFEST.json`](../files/A_PRE_0_SURFACE_MANIFEST.json),
registrado en el commit de partida. Su syscall table target-bound contiene
385 filas x86_64 y hash
`93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
La preparación S05 y su adjudicación en los checkpoints 021/022 delimitan
S05 como file-backed, y la decisión S03 de 018 limita `fcntl` a los comandos
allí expresados. Las relaciones S06 de este lote siguen **PENDING HUMAN
ADJUDICATION**.

La definición canónica provisional que orienta esta revisión comprende
mecanismos de creación, establecimiento, gestión y lifecycle de memoria no
respaldada por un archivo filesystem convencional, especialmente memoria
anónima y objetos memfd, junto con operaciones directamente necesarias para
ejercer esa capacidad. Es doctrina de trabajo, no decisión final.

## 2. Frontera de recursos

| Recurso | Identidad funcional para esta revisión | Frontera que debe mantenerse |
|---|---|---|
| Anonymous memory | Mapping sin archivo filesystem convencional; puede ser privado o compartido. | `MAP_PRIVATE | MAP_ANONYMOUS` y `MAP_SHARED | MAP_ANONYMOUS` son variantes distintas. No toda `mmap` es anónima ni toda memoria anónima es compartida entre procesos. |
| memfd-backed memory | Objeto RAM anónimo con descriptor, extensible/mappeable como objeto tipo archivo; `memfd_create` y `memfd_secret` tienen semánticas distintas. | Usar un memfd como backing de `mmap` no convierte el objeto en archivo filesystem convencional ni adjudica S03/S05 automáticamente. |
| File-backed mapping | Mapping respaldado por archivo/objeto externo convencional. | Su relación S05 fue adjudicada por separado en el lote 05; no trasladarla a S06 ni resolver aquí las variantes anonymous/memfd. |

`MAP_SHARED`/`MAP_PRIVATE` describen visibilidad/semántica del mapping, no
identifican por sí solos la superficie. Deben leerse junto al backing:
anonymous, memfd o file-backed, además de FD, offset, length, protections y
flags restantes. La misma operación puede cruzar dimensiones distintas sin
que el cruce pruebe membresía.

## 3. Candidaturas S06 existentes

El manifiesto contiene **10 filas candidatas** con S06. En todas las filas la
disposición general sigue `UNKNOWN`; en esta preparación ninguna relación
S06 se acepta ni excluye. En particular, que las seis primeras y
`pkey_mprotect` tengan una adjudicación S05 no resuelve sus relaciones S06.

| NR / syscall | Estado relacional actual pertinente | Variantes, recurso y dependencia que deben decidirse | Pregunta explícita para adjudicación humana |
|---|---|---|---|
| 9 `mmap` | S05 `YES_CONDITIONAL`; S06 sigue sin adjudicar. | Distinguir `MAP_PRIVATE | MAP_ANONYMOUS`, `MAP_SHARED | MAP_ANONYMOUS`, mapping con FD memfd y mapping file-backed. Registrar `MAP_SHARED`/`MAP_PRIVATE`, `MAP_ANONYMOUS`, FD (ignorado/no aplicable para algunas variantes), offset, length, `PROT_*`, flags y backing. El CPU load/store posterior no es el establecimiento del mapping ni una syscall S02. | ¿Qué variantes anonymous y memfd-backed pertenecen a S06? ¿Se incluye anonymous privada confinada a un proceso, además de mappings compartidos, y cómo se separa toda variante file-backed ya adjudicada a S05? |
| 10 `mprotect` | S05 `YES_CONDITIONAL`; S06 sigue sin adjudicar. | Sólo considerar rangos de mappings anonymous o memfd-backed. Particionar `PROT_READ`, `PROT_WRITE`, `PROT_EXEC`, `PROT_NONE`, rango, longitud, alineación y estado previo del mapping. | ¿Cambiar protecciones en esos mappings forma parte del lifecycle S06? ¿Hay límites por backing, protección o rango que requieran subcasos? |
| 11 `munmap` | S05 `YES_CONDITIONAL`; S06 sigue sin adjudicar. | Rango total/parcial y backing anonymous o memfd; diferenciar desmapear de cerrar FD, liberar el objeto cuando quedan otras referencias y terminar el proceso. | ¿Se incluye el desmapeo de mappings S06, y qué tratamiento tienen los rangos parciales y mappings memfd cuyo FD ya fue cerrado? |
| 25 `mremap` | S05 `YES_CONDITIONAL`; S06 sigue sin adjudicar. | Mapping anonymous/memfd; crecimiento, reducción, movimiento, tamaños y flags aplicables, incluidos `MREMAP_MAYMOVE`/`MREMAP_FIXED` y cualquier otro flag disponible en el ABI target. Geometría del mapping no equivale por sí sola a cambiar el tamaño del objeto memfd. | ¿Qué operaciones `mremap` sobre backing S06 se incluyen, y qué variantes/flags o efectos sobre el objeto requieren una partición independiente? |
| 26 `msync` | S05 `YES_CONDITIONAL`; S06 sigue sin adjudicar. | Evaluar separadamente mapping `MAP_ANONYMOUS` y mapping memfd-backed con `MS_SYNC`, `MS_ASYNC`, `MS_INVALIDATE`. Distinguir sincronización del backing memfd de sincronización de un archivo externo y del CPU store previo. | ¿Tiene efecto relevante y pertenece a S06 para algún mapping anonymous o memfd, o el subcaso no tiene semántica S06 suficiente? No trasladar la decisión S05 por similitud del nombre. |
| 72 `fcntl` | S03 está adjudicada sólo para `F_DUPFD`, `F_DUPFD_CLOEXEC`, `F_GETFD`, `F_SETFD`; relación S06 pendiente. | Revisar comandos de file sealing: `F_ADD_SEALS`, `F_GET_SEALS` y seals aplicables (p. ej. `F_SEAL_SEAL`, `F_SEAL_SHRINK`, `F_SEAL_GROW`, `F_SEAL_WRITE`, y extensiones si están disponibles). Relacionar con `MFD_ALLOW_SEALING`, objeto memfd y cambios posteriores de tamaño/write/mapping; conservar argumentos y ABI. | ¿Qué comandos/seals constituyen gestión S06 del objeto memfd? ¿Qué subcasos quedan fuera y cómo se conserva la adjudicación S03 limitada a sus cuatro comandos? |
| 77 `ftruncate` | S04 `YES` para su dimensión adjudicada; relación S06 pendiente. | Distinguir FD a objeto filesystem convencional de FD a memfd. En memfd, el tamaño inicial es cero y puede dimensionarse antes de mapearlo; registrar tamaño, FD/objeto y orden respecto de `mmap`. No reinterpretar ni alterar S04. | ¿La operación sobre un objeto memfd es una dimensión S06 además de la relación S04 ya existente para el objeto pertinente? ¿Qué criterio de tipo de backing evita confundir memfd con archivo filesystem convencional? |
| 319 `memfd_create` | Candidatura S06 existente; S06 sin adjudicar. | Creación del objeto RAM anónimo y del FD; flags `MFD_CLOEXEC`, `MFD_ALLOW_SEALING`, `MFD_HUGETLB`, codificación `MFD_HUGE_*`, `MFD_NOEXEC_SEAL` y `MFD_EXEC` según soporte del ABI/kernel target. Nombre diagnóstico, size inicial, sealing habilitado o sellado por defecto, backing y posterior `ftruncate`/`write`/`mmap` son dimensiones/etapas distintas. | ¿Qué combinaciones de flags y tipos de memfd quedan dentro de S06? ¿`MFD_HUGETLB` conserva la misma frontera de recurso o requiere decidir también su relación con filesystem/hugetlbfs? |
| 329 `pkey_mprotect` | S05 `YES_CONDITIONAL`; S06 sigue sin adjudicar. | Sólo rangos anonymous/memfd-backed; separar `PROT_*`, pkey, rango, alineación/validez y lifecycle de asignación/liberación de la key (`pkey_alloc`/`pkey_free`, actualmente pistas). | ¿La protección por pkey de un mapping S06 pertenece a la superficie, y la gestión de la key queda separada? |
| 447 `memfd_secret` | Candidatura S06 existente; S06 sin adjudicar. | Analizar por separado del memfd convencional: creación de secret-memory backing y FD, `FD_CLOEXEC` documentado para flags, tamaño con `ftruncate`, mapping, accesibilidad a través de procesos con el FD, límites `RLIMIT_MEMLOCK`, swap/hibernación, soporte/configuración y lifecycle. No equiparar flags `MFD_*` o sealing de `memfd_create` sin evidencia. | ¿Qué semántica de `memfd_secret` está presente/soportada en el target, qué flags y restricciones se consideran, y cómo se separa del memfd convencional y del anonymous mapping? |

## 4. `mmap`: partición de variantes que no debe colapsarse

| Variante | Objeto/backing a considerar | Pregunta de límite |
|---|---|---|
| `MAP_PRIVATE | MAP_ANONYMOUS` | Anonymous privado, sin backing FD de archivo. | ¿La capacidad de memoria privada de proceso pertenece al alcance S06 aunque no implique por sí sola sharing/capability externa? |
| `MAP_SHARED | MAP_ANONYMOUS` | Anonymous compartido; analizar proceso creador, `fork`/herencia y consumidores. | ¿La relación se limita al caso realmente compartido y qué mecanismo de sharing/identidad prueba esa condición? |
| `mmap(fd_memfd, ...)` | Descriptor a memfd convencional, memfd huge-page o secretmem; el objeto no es un archivo filesystem convencional. | ¿Cuáles familias de memfd/backings y flags están dentro de S06? Distinguir objeto creado de su uso posterior como backing. |
| `mmap(fd_file, ...)` | Archivo/objeto file-backed convencional. | Es dimensión S05 bajo la decisión del lote 05, no una adjudicación S06 por el hecho de usar la misma syscall. |

En cada variante conservar `MAP_SHARED`/`MAP_PRIVATE`, `MAP_ANONYMOUS`,
`MAP_FIXED`/otras flags pertinentes, FD, offset, length, `PROT_*`, identidad
del objeto, flags de huge pages cuando correspondan y disponibilidad/versiones
del ABI. La presencia de una llamada `mmap` no decide su backing.

## 5. `memfd_create`, `memfd_secret` y `ftruncate`

Cadena posible para memfd convencional:

```text
memfd_create(flags)
    -> FD a objeto RAM anónimo
    -> ftruncate(FD, size) y/o operaciones de payload por FD
    -> mmap(FD, flags, offset, length)
    -> CPU loads/stores
    -> opcionalmente seals/fcntl, compartir FD o lifecycle de mapping
```

Cada flecha es una dependencia/relación que debe evaluarse; no convierte toda
la secuencia en una sola membresía. `MFD_CLOEXEC` cruza la dimensión de
herencia/lifecycle del FD; `MFD_ALLOW_SEALING` habilita una etapa de seals;
huge-page y executable/no-executable flags modifican subcasos que requieren
ABI/target support exactos.

Cadena separada para secretmem:

```text
memfd_secret(flags)
    -> FD a objeto de secret memory
    -> ftruncate(FD, size)
    -> mmap(FD, ...)
    -> acceso desde proceso(s) autorizado(s) y restricciones propias
    -> cierre/desmapeo/exec y liberación final
```

La documentación consultada describe secretmem como backing RAM con
restricciones específicas de acceso desde kernel/user, locking/no-swap y
hibernación; no es una promesa absoluta de inaccesibilidad. Soporte del
kernel/arquitectura, opción de configuración y límites de memoria son
condiciones; la preparación no las verifica en la VM.

`ftruncate(77)` mantiene su relación S04 ya adjudicada por separado. Para la
revisión S06 la condición relevante es que el FD identifique un objeto
memfd/secretmem, no un archivo filesystem convencional. La pregunta de
solapamiento S04/S06 se deja abierta sin editar la adjudicación S04.

## 6. Lifecycle, advice y sincronización

- `munmap`, `mremap`, `mprotect` y `pkey_mprotect` se deben analizar con backing
  anonymous/memfd; cerrar el FD no es sinónimo de `munmap`, y retirar el
  mapping no prueba que el objeto memfd ya no tenga otras referencias.
- `madvise` (28) no forma parte de las 10 candidaturas S06 existentes; el
  manifiesto la conserva como candidata S05 y referencia potencial S06. No
  promoverla. Particionar por `MADV_*`: advice de patrón/pre-carga; discard o
  liberación como `MADV_DONTNEED`/`MADV_FREE`; cambios que pueden tocar backing
  como `MADV_REMOVE`; herencia `MADV_DONTFORK`/`MADV_DOFORK` y wipe/keep-on-fork;
  pageout/huge-page/populate/guard u otras variantes del UAPI target. El efecto
  puede variar entre anonymous, memfd y file-backed, y algunas variantes
  cruzan S04 o S11.
- `msync` ya tiene una relación S05 condicionada a mapping file-backed; eso
  no demuestra que sincronice o tenga relevancia S06 sobre anonymous o memfd.
  Separar `MS_SYNC`, `MS_ASYNC`, `MS_INVALIDATE`, tipo de backing y mapping.
  No clasificarlo como payload I/O S02 ni atribuirle el store CPU precedente.

## 7. Pistas S06 actuales — no candidatas

El manifiesto registra **19 referencias potenciales S06** sin agregar estas
filas a `candidate_surface_ids`. Permanecen leads, no decisiones. Diecisiete
son también pistas potenciales S05; las dos referencias sólo S06 son `brk` y
`map_shadow_stack`.

| NR / syscall | Pista documental y cuestión abierta |
|---|---|
| 12 `brk` | Ajuste del límite del heap tradicional; ¿es mecanismo de memoria anónima dentro de S06 o una dimensión separada de heap/lifecycle? |
| 27 `mincore` | Consulta de residencia de páginas; no establecer mapping ni asumir que query pertenece a S06. |
| 149 `mlock` / 150 `munlock` | Bloqueo/desbloqueo de rango; revisar anonymous/memfd, límites y si residency forma parte del lifecycle S06. |
| 151 `mlockall` / 152 `munlockall` | Alcance sobre mappings actuales/futuros heterogéneos; ¿qué parte puede atribuirse a S06 y cómo se separa estado de proceso? |
| 216 `remap_file_pages` | Interfaz de remap legacy; requiere ABI/target-version y efecto concreto antes de decidir si opera en mappings S06. |
| 237 `mbind` / 238 `set_mempolicy` / 239 `get_mempolicy` | Política NUMA de rango/proceso y consulta; distinguir memory placement de establecimiento/lifecycle del objeto S06. |
| 256 `migrate_pages` / 279 `move_pages` | Migración o consulta de páginas de proceso; rango/backing puede ser mixto, y la operación puede cruzar S11. |
| 325 `mlock2` | Bloqueo de rango con flags como `MLOCK_ONFAULT`; distinguir anonymous/memfd y límites de memoria. |
| 330 `pkey_alloc` / 331 `pkey_free` | Lifecycle de protection keys, no necesariamente mapping específico; relación con `pkey_mprotect` necesita decisión propia. |
| 440 `process_madvise` | Advice sobre proceso/rangos remotos vía pidfd; particionar por advice/backing y distinguir autorización, S03, S11 y efectos de memoria. |
| 450 `set_mempolicy_home_node` | Política home-node de rango; no inferir pertenencia S06 por ser memory policy. |
| 453 `map_shadow_stack` | Crea shadow stack; ¿es anonymous memory S06 o mecanismo especializado de control-flow/lifecycle? Revisar flags y ABI target. |
| 462 `mseal` | Sella un rango contra operaciones futuras; revisar backing, flags/operaciones bloqueadas y cruce con lifecycle/protección. |

`madvise` merece además una cuestión separada: aunque no está en esta lista
como candidatura S06, sí tiene una referencia S06 y candidatura S05. Eso no
autoriza a añadirla al lote como candidata ni a resolverla por analogía.

## 8. Cruces documentales — no son membresías

| Superficie | Cruce que revisar para S06 | Límite |
|---|---|---|
| S02 | `read`/`write` u otra transferencia de payload hacia/desde FD memfd. | CPU loads/stores en mapping no son syscall S02 ni payload transferido por el mero hecho de cambiar bytes. |
| S03 | FD creado por memfd, `MFD_CLOEXEC`, `fcntl`, cierre/duplicación/herencia. | Descriptor presente no adjudica por sí solo lifecycle S03; la relación `fcntl` S03 ya aceptada es sólo para los cuatro comandos especificados en 018. |
| S04 | `ftruncate` y potencial mutación de objeto con aspecto de archivo; `MADV_REMOVE`/hugetlbfs requieren partición. | No modificar S04 adjudicada ni equiparar automáticamente objeto RAM memfd con archivo filesystem convencional. |
| S05 | Mappings file-backed, ya delimitados condicionalmente en 022. | No trasladar adjudicaciones S05 a anonymous/memfd ni asumir que S05 implica S06 o viceversa. |
| S06 | Anonymous mappings, memfd/secretmem y operaciones directamente ligadas al recurso. | La relación exacta depende de backing, flags, variante y semántica; se decide por syscall. |
| S09 | Compartir descriptor memfd por capability passing (p. ej. transferencia de FD). | La transferencia es una ruta separada; crear el memfd no adjudica S09. |
| S10 | `MAP_SHARED` anonymous/memfd, consumidores y coordinación interproceso. | Un mapping privado o descriptor no compartido no prueba IPC; evaluar participantes/ruta. |
| S11 | `fork`, `exec`, herencia/close-on-exec y lifecycle de mappings/proceso. | Estado de proceso y supervivencia de FD/mapping son dimensiones separadas de crear/gestionar el objeto. |

## 9. Dependencias que la adjudicación deberá resolver

1. ¿La pertenencia recae en la operación que crea la capacidad (`mmap`,
   `memfd_create`, `memfd_secret`) o incluye operaciones de extensión,
   protección, advice, sincronización y destrucción sólo en ciertas variantes?
2. ¿Qué backing/flags hacen que una operación pertenezca a S06: anonymous
   privada, anonymous compartida, memfd convencional, huge memfd o secretmem?
3. ¿Qué operaciones posteriores son requisitos de una unidad de capacidad y
   cuáles son superficies/cruces independientes (`ftruncate`, payload FD,
   `fcntl` seals, FD passing, CPU access, `munmap`)?
4. ¿Cómo se particiona `ftruncate` para evitar borrar la relación S04 ya
   registrada mientras se analiza su uso en memfd?
5. ¿Qué soporte/configuración/versiones del ABI target deben probarse
   documentalmente antes de afirmar flags o disponibilidad, especialmente
   `MFD_EXEC`/`MFD_NOEXEC_SEAL`, secretmem y flags nuevos de `MADV_*`?
6. ¿`msync`, `madvise` y advice con cambio observable tienen subcasos S06,
   quedan fuera o requieren `UNKNOWN` por variante?
7. ¿Qué leads se mantienen separados como consultas, NUMA, page residency,
   protection-key lifecycle, shadow stack o memory sealing?

## 10. Fuentes consultadas y límites

- Manifiesto target-bound y ledger en el HEAD verificado: fuente de autoridad
  local para números/candidaturas/estado/definición; no son evidencia de
  alcance de runtime para cada variante.
- UAPI upstream versionado Linux `v7.0`:
  [`include/uapi/linux/memfd.h`](https://github.com/torvalds/linux/blob/v7.0/include/uapi/linux/memfd.h)
  (flags `MFD_*`) y
  [`include/uapi/asm-generic/mman-common.h`](https://github.com/torvalds/linux/blob/v7.0/include/uapi/asm-generic/mman-common.h)
  (flags comunes `MAP_*`, `PROT_*`, `MS_*`, `MADV_*`). Sirve como
  corroboración versionada upstream, no prueba que cada flag/feature esté
  habilitado o idéntico en el paquete Ubuntu target `7.0.0-34.34`.
- Syscall table upstream versionada:
  [`arch/x86/entry/syscalls/syscall_64.tbl`](https://github.com/torvalds/linux/blob/v7.0/arch/x86/entry/syscalls/syscall_64.tbl).
  La identidad numérica target-bound de este lote sigue siendo la registrada
  en el manifiesto, no una sustitución por upstream.
- Linux man-pages:
  [`memfd_create(2)`](https://man7.org/linux/man-pages/man2/memfd_create.2.html)
  y [`memfd_secret(2)`](https://man7.org/linux/man-pages/man2/memfd_secret.2.html).
  Corroboran semántica general, FD, tamaño inicial, seals, ftruncate, mapping
  y restricciones secretmem; son documentación consultada, no documentación
  atada al paquete/kernel target ni verificación de soporte/configuración en
  la VM.
- Checkpoints del proyecto 011, 018, 019, 021 y 022 delimitan leads,
  relaciones previas y cruces. Ninguno autoriza una decisión S06 en esta
  preparación.

No se consultó ni modificó la VM, ni se obtuvo nueva evidencia de ejecución.
No se atribuye runtime effect, reachability, enforcement, cobertura o readiness
a la existencia de candidaturas o referencias.

## 11. Resultado de preparación e invariantes

- Candidaturas S06 existentes presentadas: **10**.
- Referencias potenciales S06 separadas: **19**, sin promoción; incluyen
  `madvise` sólo como pista S06 además de su candidatura S05.
- Decisiones S06 YES/NO/final UNKNOWN: **0**; membresías/exclusiones
  materializadas: **0**.
- Disposiciones generales: **385/385 UNKNOWN**; disposiciones finales: **0**.
- `inventory.frozen=false`; A-PRE-0 `NOT READY`; A-PRE-1
  `NOT AUTHORIZED / NOT EXECUTED`.
- Manifiesto y ledger no se modifican; sólo se crea este checkpoint y se
  enlaza en el índice.
- No se ejecutaron TALOS, FastAPI, probes, tests, pytest, suites, benchmarks,
  workloads, parsers/validadores dinámicos ni A-PRE-1. No se tocaron VM,
  runtime, overlay, `requirements.lock`, corpus, modelos ni bases de datos.
- No se hace stage ni commit. No se avanza a S07.
