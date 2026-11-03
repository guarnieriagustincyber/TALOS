# Adjudicación documental — lote 06, S06 anonymous / memfd-backed memory

Fecha: 2026-10-01

## 1. Identidad, alcance y autoridad

Punto de partida verificado: commit
`f81134fc2293916210d53c8065f3a0049e52b0b4`, tree
`c322e78980ac72f24c66b1396014faefaac074a9`, parent
`b17dd9c4dab098512aa6c148e7d36c613da41c28`, branch `main`. La preparación
aplicable es
[`023-preparacion-lote-06-s06.md`](./023-preparacion-lote-06-s06.md).
El manifiesto y ledger de ese commit enumeran diez candidaturas S06; las
relaciones S06 estaban sin adjudicar y las disposiciones generales eran
`UNKNOWN`.

Este checkpoint registra decisiones documentales de membresía S06 para esas
diez candidaturas solamente. No decide alcanzabilidad, enforcement,
observación, cobertura ni disposición global. La doctrina aplicada es:

> S06 cubre mecanismos de creación, establecimiento, gestión y lifecycle de
> memoria no respaldada por un archivo filesystem convencional,
> especialmente memoria anónima y objetos memfd, junto con operaciones
> directamente necesarias para ejercer esa superficie cuando la operación
> pertenece semánticamente a ella.

Anonymous memory, memfd-backed memory y file-backed mappings son recursos
distintos. En particular, `MAP_SHARED`/`MAP_PRIVATE` se evalúan junto con el
backing, no como regla de membresía. Los mappings respaldados por archivos
convencionales permanecen en S05 según el lote 05. Los stores de CPU no son el
establecimiento del mapping ni una syscall S02.

## 2. Decisiones de las diez candidaturas

| NR / syscall | Decisión S06 | Condición / variantes adjudicadas | Razón y límite |
|---|---|---|---|
| 9 `mmap` | **YES, condicional** | Sólo mappings `MAP_ANONYMOUS` (`MAP_PRIVATE | MAP_ANONYMOUS` y `MAP_SHARED | MAP_ANONYMOUS`) y mappings cuyo backing FD identifique un objeto memfd/secretmem admitido. Conservar `MAP_SHARED`/`MAP_PRIVATE`, `PROT_*`, FD, offset, length y flags. Excluir backing de archivo filesystem convencional. | Establece anonymous o memfd-backed memory. La membresía depende del objeto/flag, no del nombre de la syscall; no incorpora cargas/stores posteriores ni transforma variantes file-backed S05 en S06. |
| 10 `mprotect` | **YES, condicional** | Sólo sobre un rango perteneciente a mapping anónimo o memfd-backed. Particionar `PROT_READ`, `PROT_WRITE`, `PROT_EXEC`, `PROT_NONE`, rango, length y alignment. | Cambia protecciones de memoria S06 ya establecida. No muta por sí mismo el objeto filesystem ni incluye mappings file-backed adjudicados S05. |
| 11 `munmap` | **YES, condicional** | Sólo al retirar total o parcialmente un rango de mapping anónimo o memfd-backed; preservar dirección, length, alignment y backing del rango. | Es lifecycle del mapping S06. No equivale a cerrar el FD, destruir el objeto mientras subsistan referencias, ni a desmontar un mapping file-backed S05. |
| 25 `mremap` | **YES, condicional** | Sólo mapping anónimo o memfd-backed. Mantener growth, shrink, move, tamaños, `MREMAP_MAYMOVE` y `MREMAP_FIXED` por variante/ABI. | Cambia geometría o ubicación de un mapping S06. No se adjudica el cambio del tamaño del objeto memfd por inferencia del tamaño del mapping; esa operación se analiza separadamente bajo `ftruncate`. |
| 26 `msync` | **UNKNOWN** | Sin membresía S06 general en esta decisión. Separar anonymous shared, memfd-backed, `MS_SYNC`, `MS_ASYNC`, `MS_INVALIDATE` y estado del mapping. | La documentación consultada define sincronización de un mapping de archivo hacia filesystem; no basta para establecer el efecto/doctrina específica sobre anonymous mappings o memfd en el target. No copiar la adjudicación S05 ni inferir S06 por el backing “tipo archivo” del memfd. |
| 72 `fcntl` | **YES, condicional** | Sólo `F_ADD_SEALS` aplicado a un memfd creado con sealing habilitado (`MFD_ALLOW_SEALING`), sujeto a seals admitidos y estado del objeto. Los cuatro comandos ya adjudicados a S03 (`F_DUPFD`, `F_DUPFD_CLOEXEC`, `F_GETFD`, `F_SETFD`) permanecen en S03, no se duplican aquí. Otros comandos no quedan incluidos. | Añadir seals cambia las operaciones futuras permitidas sobre el objeto de memoria memfd y forma parte de su gestión. `F_GET_SEALS` es consulta de estado y no se adjudica como membresía S06 por esta decisión. |
| 77 `ftruncate` | **YES, condicional** | Sólo cuando el FD refiere a objeto memfd/secretmem y el cambio de tamaño establece o gestiona ese backing S06. Conservar objeto, tamaño, resultado y orden respecto de mapping. | Dimensionar el objeto anónimo memfd puede ser una etapa necesaria para mapearlo. Su relación S04 ya adjudicada para mutaciones del objeto filesystem pertinente permanece intacta; este YES no traslada memfd a archivo convencional ni altera S04. |
| 319 `memfd_create` | **YES, condicional** | Creación del objeto memfd convencional de RAM; conservar nombre (diagnóstico), flags `MFD_CLOEXEC`, `MFD_ALLOW_SEALING`, `MFD_HUGETLB`, `MFD_HUGE_*`, `MFD_NOEXEC_SEAL`, `MFD_EXEC`, combinaciones y soporte ABI/kernel. | Crea directamente el objeto de memoria S06 y devuelve su descriptor. El descriptor no adjudica S03; compartirlo no adjudica S09; su posterior mapping no adjudica S05. La variante huge-page conserva su flag/recurso como subcaso, sin resolver otras superficies. |
| 329 `pkey_mprotect` | **YES, condicional** | Sólo en rangos de mappings anónimos o memfd-backed. Preservar `PROT_*`, pkey, rango, alignment y validez de key. | Gestiona la protección de un mapping S06. No adjudica el lifecycle de la key (`pkey_alloc`/`pkey_free`, pistas separadas) ni variantes file-backed S05. |
| 447 `memfd_secret` | **YES, condicional** | Sólo la operación de creación de secretmem cuando el ABI/kernel target lo soporte; conservar flags documentados, FD, tamaño posterior, mapping, restricciones de acceso y límites de memoria. No asumir equivalencia con flags/seals de `memfd_create`. | La semántica documentada crea un backing RAM anónimo secretmem con restricciones específicas, distinto de memfd convencional. La membresía se fundamenta en esa semántica, no sólo en devolver un FD; disponibilidad/configuración efectiva del target no se afirma aquí. |

Las decisiones YES de las operaciones de mapping son relaciones condicionadas
por backing; no son una aceptación indiscriminada de todas las llamadas a la
syscall. `msync` queda UNKNOWN porque las fuentes disponibles no cierran la
distinción S06. No se registra `NO` para ninguna de las diez candidaturas.

## 3. Evidencia documental, cruces y cuestiones residuales

| NR / syscall | Evidencia consultada para la relación | Cruces pertinentes (no implican membresía adicional) | Incertidumbre residual |
|---|---|---|---|
| 9 `mmap` | Syscall 9 y candidaturas/backing en el manifiesto target-bound; `mmap(2)` distingue `MAP_ANONYMOUS` y el argumento FD, mientras UAPI v7.0 define `MAP_ANONYMOUS`, `MAP_SHARED` y `MAP_PRIVATE`. | S05 para file-backed excluido; S03 para FD; S09 si se pasa FD; S10 para sharing; S11 para `fork`/lifecycle; S02 no por CPU stores. | Flags/feature support se deben ligar al paquete target antes de cerrar particiones exhaustivas. |
| 10 `mprotect` | Syscall 10 en tabla target-bound; `mprotect(2)` y UAPI `PROT_*`. | S05 por backing file-backed excluido; S10 si el rango es compartido; S11 por el espacio de direcciones del proceso. | `PROT_*`, alineación y rangos válidos conservan particiones ABI/arquitectura. |
| 11 `munmap` | Syscall 11 en tabla target-bound; `mmap(2)` documenta `munmap` y el rango del mapping. | S03 cierre FD separado; S05 file-backed excluido; S10 por mappings compartidos; S11 por teardown de proceso. | Efecto sobre objetos con otras referencias no se resuelve por retirar un rango. |
| 25 `mremap` | Syscall 25 en tabla target-bound; `mremap(2)` documenta remap, tamaños y flags de movimiento. | S05 file-backed excluido; S10 por sharing; S11 por lifecycle del espacio de direcciones. | Otras flags/variantes deben cotejarse con ABI target y source package antes del cierre de variantes. |
| 26 `msync` | Syscall 26 target-bound; `msync(2)` describe flush de mapping de archivo y `MS_SYNC`/`MS_ASYNC`/`MS_INVALIDATE`; no especifica en esa descripción una relación S06 para anonymous/memfd. | S05, sin extrapolar su adjudicación; S02 payload FD distinto; S04 no es el store originario; S10 posible mapping compartido. | Efecto concreto de esas flags en anonymous shared y memfd-backed requiere fuente target-bound adecuada; se mantiene UNKNOWN. |
| 72 `fcntl` | Syscall 72 target-bound; `fcntl(2)` documenta file seals (`F_ADD_SEALS`, `F_GET_SEALS`) y `memfd_create(2)` vincula sealing con `MFD_ALLOW_SEALING`. | S03 sólo los cuatro comandos ya aceptados en 018; S09 transferencia de FD memfd; S10 uso compartido. | Seals/extensiones de flags disponibles en paquete target deben enumerarse por separado; sólo `F_ADD_SEALS` queda dentro del YES aquí. |
| 77 `ftruncate` | Syscall 77 target-bound; `ftruncate(2)` define cambio de tamaño por FD; `memfd_create(2)` señala tamaño inicial cero y sizing con `ftruncate`. La membresía S04 consta en checkpoint 020. | S04 preservada para objeto filesystem; S03 selector FD no implica lifecycle; S05 archivo convencional; S02 transferencias de payload distintas; S10 si el memfd es compartido. | Identidad real del objeto FD y condiciones/resultado deben estar ligadas al subcaso. |
| 319 `memfd_create` | Syscall 319 target-bound; `memfd_create(2)` describe archivo anónimo RAM, FD, flags, seals, huge pages, truncamiento, mappings e herencia; UAPI `linux/memfd.h` v7.0 enumera flags relevantes. | S03 FD lifecycle separado; S05 mapping convencional excluido; S09 pass del descriptor; S10 sharing; S11 herencia `fork`/`exec`; S02 sólo operaciones de payload. | Flags `MFD_EXEC`/`MFD_NOEXEC_SEAL` y compatibilidad con flags antiguos deben confirmarse contra UAPI del paquete target. |
| 329 `pkey_mprotect` | Syscall 329 target-bound; `mprotect(2)` documenta la variante `pkey_mprotect` y protecciones/rango. | S05 file-backed excluido; S11 estado de protección del proceso; lifecycle de key permanece como pista independiente. | Validez/asignación de la key y particularidades de ABI quedan condicionadas. |
| 447 `memfd_secret` | Syscall 447 target-bound; `memfd_secret(2)` documenta creación de secretmem, `FD_CLOEXEC`, tamaño inicial, `ftruncate`, mapping, restricciones, `RLIMIT_MEMLOCK` y condiciones de soporte. | S03 FD separado; S09 sharing del descriptor; S10/IPC sólo si se establece una ruta compartida admisible; S11 herencia/exec; no S05 por el solo uso de `mmap`; S04 no se adjudica por nombre/FD. | Documentación consultada no prueba que secretmem esté habilitado/configurado en el kernel target ni cierra todos los límites de acceso. |

Fuentes versionadas reproducibles y alcance:

- Tabla syscall target-bound, definición/candidaturas y disposición: manifiesto
  en el commit de partida, con hash de la tabla
  `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
- Linux UAPI upstream v7.0:
  [`include/uapi/linux/memfd.h`](https://github.com/torvalds/linux/blob/v7.0/include/uapi/linux/memfd.h)
  y
  [`include/uapi/asm-generic/mman-common.h`](https://github.com/torvalds/linux/blob/v7.0/include/uapi/asm-generic/mman-common.h).
  Son referencias versionadas de flags, no prueba de habilitación/identidad
  exacta del paquete Ubuntu target `7.0.0-34.34`.
- Linux man-pages 6.19, snapshot fechado 2026-09-09, consultado en:
  [`mmap(2)`](https://man7.org/linux/man-pages/man2/mmap.2.html),
  [`mprotect(2)`](https://man7.org/linux/man-pages/man2/mprotect.2.html),
  [`mremap(2)`](https://man7.org/linux/man-pages/man2/mremap.2.html),
  [`msync(2)`](https://man7.org/linux/man-pages/man2/msync.2.html),
  [`fcntl(2)`](https://man7.org/linux/man-pages/man2/fcntl.2.html),
  [`ftruncate(2)`](https://man7.org/linux/man-pages/man2/ftruncate.2.html),
  [`memfd_create(2)`](https://man7.org/linux/man-pages/man2/memfd_create.2.html)
  y
  [`memfd_secret(2)`](https://man7.org/linux/man-pages/man2/memfd_secret.2.html).
  Describen interfaz/semántica general; no sustituyen verificación del kernel
  instalado ni resuelven las variantes UNKNOWN.
- Checkpoints 018, 020, 022 y 023 mantienen las adjudicaciones de superficie
  previas y los límites de evidencia; S06 no altera esas decisiones.

## 4. Relaciones cruzadas y límites de autoridad

- S02: payload transferido por operaciones FD es distinto de CPU loads/stores
  sobre una página mapeada y de `msync`.
- S03: la decisión S06 de `fcntl` no altera la adjudicación S03 de sus cuatro
  comandos ni convierte `memfd_create`/`memfd_secret` en membresías S03.
- S04: `ftruncate` mantiene la relación S04 ya registrada para el objeto
  filesystem pertinente; S06 se limita aquí al caso condicionado de backing
  memfd/secretmem. Ninguna adjudicación S04 se cambia.
- S05: mappings file-backed permanecen en S05; el YES S06 para operaciones
  comunes sólo abarca el backing anonymous/memfd indicado.
- S07: no se identifica un cruce directo de estas diez operaciones de memoria
  con comunicación IP; no se adjudica relación S07.
- S09/S10/S11: FD passing, sharing/coordinación y herencia/lifecycle de proceso
  son dimensiones separadas. No se adjudican por esta decisión.

Las siguientes referencias/candidaturas potenciales permanecen fuera de este
lote y no se promueven: `brk` (12), `mincore` (27), `mlock` (149),
`munlock` (150), `mlockall` (151), `munlockall` (152),
`remap_file_pages` (216), `mbind` (237), `set_mempolicy` (238),
`get_mempolicy` (239), `migrate_pages` (256), `move_pages` (279),
`mlock2` (325), `pkey_alloc` (330), `pkey_free` (331),
`process_madvise` (440), `set_mempolicy_home_node` (450),
`map_shadow_stack` (453) y `mseal` (462). `madvise` (28) continúa sólo como
referencia S06 no promovida; no se adjudica en este lote.

## 5. Estado documental y verificación

Esta directiva pidió detenerse antes de modificar manifiesto/ledger si el
mecanismo canónico existente requiriera esos cambios. Los lotes 03–05 muestran
que la estructura existente registra adjudicaciones relacionales en el
manifiesto y un resumen en el ledger. Por tanto, este checkpoint documenta las
decisiones, pero **no materializa sus relaciones en esos artefactos**: no se
modifican aquí y queda pendiente autorizar/realizar ese paso canónico. No se
inventa un esquema alternativo.

- Candidaturas S06 con decisión documental explícita: **10** (**9 YES
  condicionales**, 0 NO, **1 UNKNOWN**).
- Las **19 pistas S06** de 023 permanecen fuera de la adjudicación y no se
  promueven; `madvise` permanece como referencia no promovida.
- Disposiciones globales: **385/385 UNKNOWN**; disposiciones finales: **0**.
- `inventory.frozen=false`; A-PRE-0 `NOT READY`; A-PRE-1
  `NOT AUTHORIZED / NOT EXECUTED`.
- Manifiesto y ledger sin cambios por esta adjudicación; las disposiciones,
  readiness y membresías S05/S04/S03 no se modifican.
- No se ejecutaron TALOS, FastAPI, probes, tests, pytest, suites, benchmarks,
  workloads, parsers/validadores dinámicos ni A-PRE-1. No se tocaron VM,
  runtime, overlay, `requirements.lock`, corpus, modelos, bases de datos, E5,
  Qwen ni Playwright.
- No se hizo stage ni commit. No se avanzó a S07.
