# Adjudicación documental — 15 candidaturas pendientes S01

Fecha: 2026-10-01

## 1. Alcance y verificaciones previas

Se procesan sólo las 15 relaciones S01 clasificadas como
`GENUINE_UNREVIEWED_CANDIDATE` en
[checkpoint 045](./045-arqueologia-representacion-candidaturas.md). Antes de
decidir, la lista del checkpoint 045 se comparó con los contextos S01
`UNREVIEWED_CANDIDATE` del manifiesto: coincidencia exacta de 15 pares
syscall/número. Todas tenían `candidate_surface_ids=["S01"]`, disposición
global UNKNOWN y ninguna tenía adjudicación S01 ya registrada.

Las 15 son distintas de las 13 relaciones aceptadas en
[checkpoint 014](./014-adjudicacion-documental-lote-01-s01.md). No hay
reapertura ni coincidencia con `open_by_handle_at` (304), que sigue UNKNOWN.
La comprobación queda acotada a estas 15; no se inicia reconciliación global
ni se reabre S06–S16.

### Doctrina y criterio

Se aplica exclusivamente la regla humana S01: la syscall participa
directamente en resolución, selección, identificación o descubrimiento de un
objeto filesystem como parte de su semántica. No basta con “tocar filesystem”
ni con invocar una syscall con un FD. La evidencia de abajo identifica el
argumento que nombra/selecciona el objeto o la operación directa de
enumeración. El scope de cada YES queda limitado a esa dimensión; no asigna
todo el efecto funcional, no prueba workload/reachability y no cambia la
disposición global UNKNOWN.

## 2. Fichas de las 15 candidaturas

En todas las filas, `YES` significa membresía relacional S01 dentro del scope
expreso. Confianza 9/10 califica la trazabilidad syscall/semántica hacia S01,
no la ejecución, reachability ni enforcement en el target.

| Syscall | NR | Firma nativa/relevante | Razón exacta y evidencia documental | Decisión S01 y scope | Cruces conservados sin adjudicar | Fuente y confianza |
|---|---:|---|---|---|---|---|
| `open` | 2 | `open(path, flags, mode?)` | `open(2)` define que abre el archivo especificado por `path`; la resolución/selección del objeto es parte directa de la operación. | **YES** — resolución/selección del target pathname bajo path-resolution y flags. Creación/truncamiento y el FD devuelto no se generalizan a S01. | Rutas alternativas existentes S02/S03/S05/S06 se preservan; I/O, FD y backing posterior siguen independientes. Efectos O_CREAT/O_TRUNC no son adjudicación S04. | `open(2)`; tabla target-bound. 9/10 |
| `stat` | 4 | `stat(path, statbuf)` | `stat(2)` obtiene estado del archivo apuntado por `path`; requiere búsqueda en componentes de ruta. | **YES** — resolver/seleccionar objeto pathname para la consulta de estado; conserva semántica de seguimiento de symlink de `stat`. El resultado metadata no es apertura. | Rutas alternativas existentes S02/S03/S05/S06 intactas; no inferir lectura de payload ni lifecycle. | `stat(2)`; tabla target-bound. 9/10 |
| `fstat` | 5 | `fstat(fd, statbuf)` | `stat(2)` especifica que el objeto sobre el que se obtiene estado se identifica mediante `fd`. Esto satisface la dimensión de identificación/selección del objeto contemplada por el scope S01; no es inferencia por uso incidental del FD. | **YES** — sólo cuando `fd` refiere a un objeto filesystem; identifica el objeto sujeto a la consulta. FDs de otros tipos no quedan incluidos por esta decisión. | S03 conserva procedencia/lifecycle de FD; S02/S05/S06 permanecen independientes. | `stat(2)`; precedentes `fstatfs`/`fgetxattr` S01 del checkpoint 014. 9/10 |
| `lstat` | 6 | `lstat(path, statbuf)` | `stat(2)` define que, si el pathname final es symlink, devuelve el estado del link mismo, no del objeto al que apunta. La selección del objeto symlink está expresamente en la semántica. | **YES** — resolución del pathname y selección del symlink final; no sigue el último link. | Rutas S02/S03/S05/S06 preservadas; el target referenciado no se considera abierto ni adjudicado por S01. | `stat(2)`; tabla target-bound. 9/10 |
| `access` | 21 | `access(path, mode)` | `access(2)` comprueba existencia/permisos del archivo `path`; el check requiere que el target pathname sea resuelto. No se interpreta como apertura. | **YES** — seleccionar el objeto al que se aplica `F_OK`/`R_OK`/`W_OK`/`X_OK`; conserva credenciales reales de `access`. No afirma que una operación posterior esté permitida o vaya a ocurrir. | S03/S05/S06/S02 alternativos del manifiesto quedan intactos y no se deducen de la comprobación de permisos. | `access(2)`; tabla target-bound. 9/10 |
| `creat` | 85 | `creat(path, mode)` | `open(2)` documenta `creat` como operación de apertura/creación sobre el archivo especificado por `path`; el nombre del objeto requiere resolución directa. | **YES** — resolver/seleccionar el target pathname para creación/apertura. La mutación de creación/truncamiento y el FD retornado son dimensiones separadas. | S03 y las rutas alternativas registradas se preservan; no se adjudica otra superficie por los efectos de creación. | `open(2)`; tabla target-bound. 9/10 |
| `readlink` | 89 | `readlink(path, buf, bufsiz)` | `readlink(2)` copia el contenido del symlink nombrado por `path`; para hacerlo, el pathname selecciona el objeto symlink. La página diferencia ese contenido del pathname destino. | **YES** — resolver/seleccionar el symlink mismo y descubrir su texto. No seguir ni adjudicar el objeto al que apunta el texto retornado. | Rutas alternativas S02/S03/S05/S06 preservadas; la ruta-target no se convierte en otra relación S01. | `readlink(2)`; tabla target-bound. 9/10 |
| `getdents64` | 217 | `getdents64(fd, dirp, count)` | `getdents(2)` define que lee entradas del directorio referido por `fd` y devuelve nombres, inode y tipo cuando está disponible. La enumeración/descubrimiento es explícitamente dimensión S01. | **YES** — sólo FD de directorio y entradas devueltas; descubre nombres/entradas, sin afirmar que cada nombre sea todavía resoluble o que el objeto se haya abierto. | S03 para identidad/procedencia del FD; los demás routes declarados quedan intactos, sin promoción. | `getdents(2)`; tabla target-bound. 9/10 |
| `openat` | 257 | `openat(dirfd, path, flags, mode?)` | `open(2)` establece que un path relativo se interpreta respecto del directorio identificado por `dirfd`; path absoluto aplica sus reglas propias. Esa resolución/selección es operación central. | **YES** — resolución/selección por pathname y `dirfd` bajo flags/mode; preservar absolute/relative y `AT_FDCWD`. Creación, FD y usos siguientes quedan fuera del scope S01. | S03 para dirfd/FD; S02/S05/S06 para operaciones/objetos posteriores, sin adjudicación automática. | `open(2)`; tabla target-bound. 9/10 |
| `newfstatat` | 262 | `newfstatat(dirfd, path, statbuf, flags)` | `stat(2)` documenta `fstatat` como consulta del archivo apuntado por `path` y resuelve paths relativos con `dirfd`; la fila nativa target-bound corresponde a `newfstatat`. | **YES** — seleccionar el objeto para status por path/dirfd, conservando flags admitidos, incluidos los subcasos no-follow/empty-path pertinentes. | S03 por FD/dirfd; otros routes de la fila se preservan. La metadata no equivale a abrir objeto. | `stat(2)`; tabla target-bound. 9/10 |
| `readlinkat` | 267 | `readlinkat(dirfd, path, buf, bufsiz)` | `readlink(2)` describe resolución relativa a `dirfd`, path absoluto y el subcaso path vacío que opera sobre symlink referido por `dirfd` con `O_PATH|O_NOFOLLOW`. | **YES** — seleccionar el symlink por pathname relativo/absoluto o variante documentada empty-path; devolver sólo su link text, sin resolver el destino. | S03 para dirfd/FD; demás rutas permanecen sin cambio. | `readlink(2)`; tabla target-bound. 9/10 |
| `faccessat` | 269 | Native x86_64 syscall `faccessat(dirfd, path, mode)` | `access(2)` documenta `faccessat`; el path relativo se resuelve respecto de `dirfd` y el objeto resultante es el sujeto del permission check. La tabla de la ABI target identifica NR 269 `faccessat`. | **YES** — resolver/seleccionar objeto sujeto a check. En este syscall nativo no atribuir el argumento flags de wrapper libc ni el de NR 439; la variante flags-bearing `faccessat2` queda en su fila separada. | S03 para dirfd; S02/S05/S06 genéricos quedan pendientes si aplican; no se adjudican. | `access(2)` y tabla nativa target-bound. 9/10 |
| `statx` | 332 | `statx(dirfd, path, flags, mask, statxbuf)` | `statx(2)` devuelve estado del archivo identificado mediante `dirfd`/`path`, con flags de resolución y máscara de campos. | **YES** — resolver/seleccionar el objeto de status, preservando `AT_*`, mask y value/result. La obtención de metadata no adjudica otras operaciones. | S03 para dirfd; routes S02/S05/S06 siguen separados. | `statx(2)`; tabla target-bound. 9/10 |
| `openat2` | 437 | `openat2(dirfd, path, open_how, size)` | `openat2(2)` la define como apertura del archivo especificado por `path`; paths relativos se anclan a `dirfd`, y `open_how.resolve` regula la resolución. | **YES** — selección/resolución bajo `open_how.flags/mode/resolve`, size y campos/flags soportados por target; no implica uso del FD retornado. | S03 por dirfd/result FD; S02/S05/S06 por operación/backing posterior permanecen aparte. Efectos de creación no adjudican S04 aquí. | `openat2(2)`; tabla target-bound. 9/10 |
| `faccessat2` | 439 | `faccessat2(dirfd, path, mode, flags)` | `access(2)` documenta la syscall flags-bearing `faccessat2`, path relativo a dirfd, y las variantes de flags afectan el target/check. | **YES** — resolución/selección del objeto sujeto a permiso; preservar `mode`, flags y sus efectos de symlink/dirfd. No equivale a abrir/usar el objeto. | S03 para dirfd; rutas alternativas existentes se mantienen sin adjudicación. | `access(2)`; tabla target-bound. 9/10 |

## 3. Cruces y límites

Los 15 registros ya incluían `S01` en `candidate_surface_ids` y el array
`S01.syscalls`; esos índices se conservaron. Cada fila tenía rutas alternativas
de manifiesto `S02`, `S03`, `S05`, `S06`. Se preservaron íntegramente y no se
adjudicaron por esta decisión. En particular:

- usar un FD como identificador de objeto no adjudica procedencia/lifecycle
  S03;
- una futura operación de payload no se incluye por abrir, consultar o
  descubrir un objeto;
- backing/mapping file-backed o anonymous sigue siendo eje S05/S06 de su
  operación específica;
- create/truncate de `open`/`creat` y otros flags no se convierten en
  decisiones de mutación S04;
- symlink path de `lstat`/`readlink` y pathname devuelto por readlink no son
  la misma selección de objeto;
- la firma de libc `faccessat` no se sustituye por la syscall nativa ni por
  `faccessat2` (439).

Ninguna relación cambia la disposición general del syscall: 385/385 siguen
`UNKNOWN`. Las decisiones S01 previas del checkpoint 014, las S02–S16, y las
evidencias `OBSERVED`/`BLOCKED` quedan intactas.

## 4. Materialización limitada

Por cada una de las 15 filas se cambió únicamente el estado agregado de
candidatura, el estado del contexto S01 y se añadió el registro de relación
S01 con `decision=YES`, scope y referencia a este checkpoint. No se cambiaron
`candidate_surface_ids`, arrays de syscalls de superficie, otros contextos,
otras relaciones, rutas alternativas ni el ledger. Se retiró de las filas
afectadas la frase obsoleta que decía que la membership seguía siendo sólo
un puntero UNREVIEWED, sustituyéndola por el límite S01 y los cierres aún
pendientes. `disposition_status` y `pending_reason` permanecen en UNKNOWN.

| Medida | Antes | Después |
|---|---:|---:|
| Contextos S01 de las 15 pendientes en estado `UNREVIEWED_CANDIDATE` | 15 | 0 |
| Contextos S01 de estas 15 `HUMAN_ADJUDICATED_CANDIDATE` | 0 | 15 |
| Relaciones S01 materiales en este lote | 0 | 15 YES |
| Disposiciones globales UNKNOWN | 385 | 385 |
| Disposiciones globales finales | 0 | 0 |
| `inventory.frozen` | false | false |
| A-PRE-0 | NOT_READY | NOT_READY |
| A-PRE-1 | NOT AUTHORIZED / NOT EXECUTED | NOT AUTHORIZED / NOT EXECUTED |

## 5. Integridad y verificación

| Artefacto | SHA-256 antes | SHA-256 después |
|---|---|---|
| Manifiesto | `9e0f2f0f07240a0902598f989380c2febd7f2a1ee5f9314d8de156b08cc69a3e` | `801f529655f1f4f250a2a374d2afa63f858a9c0875e0e3dc620d112df5f9fd6e` |
| Ledger | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| `checkpoints/index.md` | `9f8d57fb9f043f2dbc8322db6c1cfc0ba3fd4287684e2a562ce846faa281f61e` | `fc7aa6d3ec4071436cb45ffc9a4690d52ff509e4bbc066bc9f51aa221ac51b20` |

Verificaciones completadas:

- JSON parseable; 385 filas, nombres únicos 385/385 y números únicos 385/385.
- 385/385 `disposition_status=UNKNOWN`; cero disposiciones finales.
- `inventory.frozen=false`; ledger `readiness.status=NOT_READY` y
  `predicate_result=false`.
- Las 15 filas tienen relación S01 `HUMAN_ADJUDICATED_CANDIDATE` con
  referencia a este checkpoint; sus disposiciones globales siguen UNKNOWN.
- Las candidaturas S01 `UNREVIEWED_CANDIDATE` bajaron de 15 a 0.
- Ledger y `requirements.lock` permanecieron byte-identical; el ledger apunta
  al manifiesto canónico y su readiness refleja las 385 disposiciones UNKNOWN.
- `git diff --check` limpio.

No se ejecutaron TALOS, FastAPI, workloads, probes, benchmarks, tests,
validadores, A-PRE-1 ni actividad dinámica. No se cargaron corpus/modelos ni
se tocaron bases, seccomp, E5/Qwen, VM, overlay o runtime. No se inició la
reconciliación global posterior.

## 6. Resultado y parada

**15/15 procesadas: 15 YES, 0 NO, 0 UNKNOWN.** Las 15 memberships S01 quedan
materializadas con sus scopes individuales. Pendientes de S01 previas a esta
directiva —incluido `open_by_handle_at` 304— no se tocaron. No se realizó
commit.
