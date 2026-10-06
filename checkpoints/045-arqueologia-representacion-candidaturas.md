# Arqueología de representación de candidaturas — S01/S05/S06/S07/S08/S15

Fecha: 2026-10-01

## 1. Alcance y regla de no modificación

Inspección documental del estado `UNREVIEWED_CANDIDATE` señalado en el
[checkpoint 044](./044-reconciliacion-global-post-s02-s16.md). Se rastreó cada
registro contra su preparación/adjudicación, checkpoints posteriores,
manifiesto, ledger e índice.

Este checkpoint **no adjudica ni vuelve a adjudicar memberships** y no cambia
el manifiesto, ledger, políticas, disposiciones globales o las decisiones
fuente. Las categorías siguientes describen la procedencia/representación del
estado observado, no una decisión semántica nueva:

- `GENUINE_UNREVIEWED_CANDIDATE`
- `ALREADY_ADJUDICATED_MISREPRESENTED`
- `HISTORICAL_REFERENCE_ONLY`
- `LEAD_NOT_PROMOTED`
- `DUPLICATE/OVERLAP`
- `CONTRADICTORY_STATE`
- `UNKNOWN_REPRESENTATION`

## 2. Snapshot de lectura

| Elemento | SHA-256 / valor |
|---|---|
| HEAD | `f81134fc2293916210d53c8065f3a0049e52b0b4` |
| Manifiesto antes/después de esta inspección | `9e0f2f0f07240a0902598f989380c2febd7f2a1ee5f9314d8de156b08cc69a3e` |
| Ledger antes/después | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` antes/después | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Índice antes de añadir este checkpoint | `85d2315ad74c878152a5088bc29b23221983be366feba774a4cc63b46cbdd6cb` |
| Índice tras registrar este checkpoint | `1167f604a15795473ef61d464ec77aa9a944ebad6c52c859909bda5152db62ab` |
| Estado del worktree | Sucio, con modificaciones y archivos no rastreados previos; preservados. |

El ledger confirma 385/385 disposiciones globales `UNKNOWN`, cero finales,
`inventory.frozen=false` y A-PRE-0 `NOT_READY`. No se calculó un digest
semántico por cada superficie: los checkpoints de origen no registran uno
comparable para S01/S05–S08/S15. El digest S01–S15 citado por el checkpoint
041 cubre su receta/scope y no codifica las decisiones checkpoint-only de
S06–S08.

## 3. Resultado de clasificación

Se encontraron exactamente **60** contextos de superficie con
`membership_status=UNREVIEWED_CANDIDATE` en las seis superficies
especificadas. Esto no equivale a 60 estados superiores
`candidate_membership_status=UNREVIEWED`: dentro de esos 60 contextos, 44
filas tienen estado superior `UNREVIEWED`, 10
`PARTIALLY_HUMAN_ADJUDICATED_BY_SURFACE` y seis
`HUMAN_ADJUDICATED_CANDIDATE`. El estado superior puede reflejar otra
superficie/dimensión de la misma syscall; no adjudica por sí solo el contexto
Sxx. Las tablas muestran el estado del contexto individual y señalan aparte
el estado superior cuando se cotejó. La clasificación de procedencia es:

| Clasificación | Cantidad | Interpretación |
|---|---:|---|
| `GENUINE_UNREVIEWED_CANDIDATE` | 15 | Candidaturas S01 directas aún no adjudicadas por los lotes inspeccionados. |
| `ALREADY_ADJUDICATED_MISREPRESENTED` | 42 | El checkpoint de adjudicación ya registra YES, pero el contexto canónico de candidatura sigue con estado UNREVIEWED; S06–S08 declaran que no materializan allí las decisiones. |
| `UNKNOWN_REPRESENTATION` | 3 | El checkpoint ya preserva expresamente UNKNOWN; el rótulo UNREVIEWED no representa esa distinción. No se cambia UNKNOWN ni se crea membership. |
| `HISTORICAL_REFERENCE_ONLY` | 0 | Ninguna de las 60 filas se clasifica únicamente como referencia histórica. |
| `LEAD_NOT_PROMOTED` | 0 | Ninguna de las 60 filas es un lead `no_candidate_review`; son contextos de candidaturas. |
| `DUPLICATE/OVERLAP` | 0 | La repetición de syscall entre S07/S08 es legítima por partición de familia IP vs AF_UNIX, no duplicación de una relación idéntica. |
| `CONTRADICTORY_STATE` | 0 en las filas listadas | Hay inconsistencias de representación adicionales (véase §7), pero no convierten estas filas en decisiones contradictorias: sus decisiones fuente son rastreables. |
| **Total** | **60** | Una sola categoría por cada entrada UNREVIEWED. |

## 4. S01 — 15 candidaturas genuinamente pendientes

El checkpoint 014 resuelve las referencias no-candidatas del lote: 13 YES,
cuatro NO y las relaciones UNKNOWN expresas, incluido `open_by_handle_at`
(304). Esas 13 aceptaciones están registradas como candidaturas humanas en
filas distintas; las cuatro exclusiones y siete UNKNOWN pertenecen a la cola
de referencias del lote. Ninguna de las 15 filas abajo aparece en los
adjudicados de checkpoint 014 ni como lead S01 de `no_candidate_review`.
Por eso se clasifican `GENUINE_UNREVIEWED_CANDIDATE`, no se adjudican.

| Superficie | Syscall | NR | Estado del contexto de superficie | Provenance revisada | Clasificación |
|---|---|---:|---|---|---|
| S01 | `open` | 2 | `UNREVIEWED_CANDIDATE` | Candidatura S01 directa preexistente en manifiesto; fuera de las 24 referencias revisadas en checkpoint 014. | `GENUINE_UNREVIEWED_CANDIDATE` |
| S01 | `stat` | 4 | `UNREVIEWED_CANDIDATE` | Igual: contexto/candidatura S01 directa; sin decisión para esta fila en checkpoint 014. | `GENUINE_UNREVIEWED_CANDIDATE` |
| S01 | `fstat` | 5 | `UNREVIEWED_CANDIDATE` | Igual; no confundir con `fstatfs` (138), uno de los YES del checkpoint 014. | `GENUINE_UNREVIEWED_CANDIDATE` |
| S01 | `lstat` | 6 | `UNREVIEWED_CANDIDATE` | Candidatura directa; checkpoint 014 no adjudica esta fila. | `GENUINE_UNREVIEWED_CANDIDATE` |
| S01 | `access` | 21 | `UNREVIEWED_CANDIDATE` | Candidatura directa; no es una de las cuatro exclusiones S01 ni un lead adjudicado en 014. | `GENUINE_UNREVIEWED_CANDIDATE` |
| S01 | `creat` | 85 | `UNREVIEWED_CANDIDATE` | Candidatura directa; sin decisión previa específica encontrada. | `GENUINE_UNREVIEWED_CANDIDATE` |
| S01 | `readlink` | 89 | `UNREVIEWED_CANDIDATE` | Candidatura directa; distinta de `readlinkat` (267), igualmente pendiente. | `GENUINE_UNREVIEWED_CANDIDATE` |
| S01 | `getdents64` | 217 | `UNREVIEWED_CANDIDATE` | No es `getdents` (78), que sí figura entre los 13 YES de checkpoint 014. | `GENUINE_UNREVIEWED_CANDIDATE` |
| S01 | `openat` | 257 | `UNREVIEWED_CANDIDATE` | Candidatura directa; sin adjudicación en checkpoint 014. | `GENUINE_UNREVIEWED_CANDIDATE` |
| S01 | `newfstatat` | 262 | `UNREVIEWED_CANDIDATE` | Candidatura directa; sin adjudicación en checkpoint 014. | `GENUINE_UNREVIEWED_CANDIDATE` |
| S01 | `readlinkat` | 267 | `UNREVIEWED_CANDIDATE` | Candidatura directa; no incluida entre los adjudicados de checkpoint 014. | `GENUINE_UNREVIEWED_CANDIDATE` |
| S01 | `faccessat` | 269 | `UNREVIEWED_CANDIDATE` | Candidatura directa; sin decisión previa específica encontrada. | `GENUINE_UNREVIEWED_CANDIDATE` |
| S01 | `statx` | 332 | `UNREVIEWED_CANDIDATE` | Candidatura directa; sin decisión previa específica encontrada. | `GENUINE_UNREVIEWED_CANDIDATE` |
| S01 | `openat2` | 437 | `UNREVIEWED_CANDIDATE` | Candidatura directa; sin decisión previa específica encontrada. | `GENUINE_UNREVIEWED_CANDIDATE` |
| S01 | `faccessat2` | 439 | `UNREVIEWED_CANDIDATE` | Candidatura directa; sin decisión previa específica encontrada. | `GENUINE_UNREVIEWED_CANDIDATE` |

**Fuentes:** manifiesto actual; checkpoint 014 (13 YES, cuatro NO y UNKNOWN
de las referencias históricas). El estado de 304 `open_by_handle_at` UNKNOWN
es histórico y no es ninguna de estas 15 filas.

## 5. S05 — representación de `madvise`

| Superficie | Syscall | NR | Estado del contexto de superficie | Provenance revisada | Clasificación |
|---|---|---:|---|---|---|
| S05 | `madvise` | 28 | `UNREVIEWED_CANDIDATE` | Checkpoint 021 la incluye entre las siete candidaturas iniciales; checkpoint 022 decide expresamente mantener S05 `UNKNOWN` hasta particionar `MADV_*`; no materializa membership S05. Las otras seis del lote son YES condicionados y están materializadas. | `UNKNOWN_REPRESENTATION` |

No se promueve `madvise`; las 17 pistas S05 de 021 siguen siendo leads
separados y no son parte de estas 60 candidaturas.

## 6. S06 — nueve decisiones YES no reflejadas y un UNKNOWN

Checkpoint 023 identifica diez candidaturas S06; checkpoint 024 registra
nueve YES condicionales y `msync` UNKNOWN. El checkpoint dice expresamente
que no materializa las relaciones en el manifiesto/ledger. Así, las nueve
filas permanecen con contexto `UNREVIEWED_CANDIDATE` en el manifiesto pese a
la decisión documentary YES. `msync` queda UNKNOWN; la relación S05 ya
adjudicada de `msync` no resuelve S06.

| Superficie | Syscall | NR | Decisión fuente S06 | Provenance/condición conservada | Clasificación de la entrada |
|---|---|---:|---|---|---|
| S06 | `mmap` | 9 | YES condicional | Anonymous o memfd/secretmem backing; no file-backed convencional. Cruce S05 por backing. | `ALREADY_ADJUDICATED_MISREPRESENTED` |
| S06 | `mprotect` | 10 | YES condicional | Sólo rango anonymous/memfd-backed; protección/rango/alineación. File-backed es S05. | `ALREADY_ADJUDICATED_MISREPRESENTED` |
| S06 | `munmap` | 11 | YES condicional | Sólo rango anonymous/memfd-backed; distinguir cierre FD y mapping file-backed. | `ALREADY_ADJUDICATED_MISREPRESENTED` |
| S06 | `mremap` | 25 | YES condicional | Sólo mapping anonymous/memfd-backed; preservar tamaño y flags. | `ALREADY_ADJUDICATED_MISREPRESENTED` |
| S06 | `msync` | 26 | UNKNOWN | No se trasladó el YES S05 de mapping file-backed; efecto S06 anonymous/memfd insuficientemente establecido en checkpoint 024. | `UNKNOWN_REPRESENTATION` |
| S06 | `fcntl` | 72 | YES condicional | Sólo `F_ADD_SEALS` sobre memfd sealing-enabled; cuatro comandos FD siguen S03; otros comandos excluidos. | `ALREADY_ADJUDICATED_MISREPRESENTED` |
| S06 | `ftruncate` | 77 | YES condicional | Sólo redimensionamiento del objeto memfd/secretmem; la dimensión filesystem ya adjudicada conserva S04 separada. | `ALREADY_ADJUDICATED_MISREPRESENTED` |
| S06 | `memfd_create` | 319 | YES condicional | Creación de memfd; flags y soporte ABI/kernel siguen como ejes. FD S03 y posterior mapping S05 no se absorben. | `ALREADY_ADJUDICATED_MISREPRESENTED` |
| S06 | `pkey_mprotect` | 329 | YES condicional | Sólo rango anonymous/memfd-backed; lifecycle de pkey no se adjudica. | `ALREADY_ADJUDICATED_MISREPRESENTED` |
| S06 | `memfd_secret` | 447 | YES condicional | Creación secretmem, sujeta a soporte/flags; no equiparar sin prueba a memfd convencional. | `ALREADY_ADJUDICATED_MISREPRESENTED` |

## 7. S07 y S08 — decisiones documentadas, representación pendiente

Checkpoint 026 adjudica 17 YES condicionales S07 para AF_INET/AF_INET6 y
documenta separadamente S07 NO para `socketpair` (53). Afirma que las
decisiones están sólo en el checkpoint y no se materializan en manifiesto ni
ledger. Las 17 candidaturas S07 actuales permanecen como
`UNREVIEWED_CANDIDATE`; se clasifican `ALREADY_ADJUDICATED_MISREPRESENTED`.

Checkpoint 028 adjudica 18 YES condicionales S08: las operaciones socket
documentadas más `socketpair`, limitadas a AF_UNIX/AF_LOCAL y sus variantes
pathname/abstract/unnamed. También declara no materializar membresías. Las
16 entradas S08 actualmente UNREVIEWED coinciden por identidad syscall/NR con
decisiones YES de checkpoint 028; se clasifican
`ALREADY_ADJUDICATED_MISREPRESENTED`, manteniendo la condición AF_UNIX. La
misma syscall en S07 y S08 es un solapamiento semántico legítimo por family,
no una duplicación que deba eliminarse.

| Superficie | Syscall | NR | Clasificación | Provenance/condición |
|---|---|---:|---|---|
| S07 | `socket` | 41 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES sólo AF_INET/AF_INET6; AF_UNIX pertenece a S08. |
| S07 | `connect` | 42 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES sólo peer/destino IP AF_INET/AF_INET6. |
| S07 | `accept` | 43 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES para aceptación IP; FD nuevo sigue cruce S03. |
| S07 | `sendto` | 44 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES para transporte IP; payload efectivo conserva cruce S02. |
| S07 | `recvfrom` | 45 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES para recepción IP; payload efectivo S02 separado. |
| S07 | `sendmsg` | 46 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES sólo comunicación IP; cmsg/SCM_RIGHTS no se absorben. |
| S07 | `recvmsg` | 47 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES sólo IP; payload/cmsg/FD passing separados. |
| S07 | `shutdown` | 48 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES para canal IP; no equivale a close/S03. |
| S07 | `bind` | 49 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES para address local IP. |
| S07 | `listen` | 50 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES para listener IP/type compatible. |
| S07 | `getsockname` | 51 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES para consulta endpoint IP. |
| S07 | `getpeername` | 52 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES para consulta peer IP. |
| S07 | `setsockopt` | 54 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES condicional a IP, `level`/`optname`; no atribuir automáticamente S08. |
| S07 | `getsockopt` | 55 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES condicional a IP y opción concreta. |
| S07 | `accept4` | 288 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES IP; flags `SOCK_CLOEXEC`/`SOCK_NONBLOCK` siguen separados. |
| S07 | `recvmmsg` | 299 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES IP por mensaje/retorno parcial; payload S02 aparte. |
| S07 | `sendmmsg` | 307 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 026 YES IP por mensaje/retorno parcial; payload S02 aparte. |
| S08 | `socket` | 41 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 028 YES sólo AF_UNIX/AF_LOCAL y type/protocol admitidos. |
| S08 | `connect` | 42 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 028 YES AF_UNIX; pathname/abstract, type/peer/state. |
| S08 | `accept` | 43 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 028 YES listener AF_UNIX compatible; descriptor S03 separado. |
| S08 | `sendto` | 44 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 028 YES AF_UNIX; transport separado de payload S02. |
| S08 | `recvfrom` | 45 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 028 YES AF_UNIX; origen/longitud/resultado condicionan el subcaso. |
| S08 | `sendmsg` | 46 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 028 YES AF_UNIX; cmsg y S09 separados. |
| S08 | `recvmsg` | 47 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 028 YES AF_UNIX; payload, control buffer y `SCM_RIGHTS` separados. |
| S08 | `shutdown` | 48 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 028 YES al canal AF_UNIX; close/S03 separado. |
| S08 | `bind` | 49 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 028 YES AF_UNIX pathname o abstract; path filesystem no adjudica S01/S04 automáticamente. |
| S08 | `listen` | 50 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 028 YES AF_UNIX con type/state compatible. |
| S08 | `getsockname` | 51 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 028 YES address AF_UNIX pathname/abstract/autobind/unnamed. |
| S08 | `getpeername` | 52 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 028 YES peer AF_UNIX si type/state lo provee. |
| S08 | `socketpair` | 53 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 028 YES AF_UNIX endpoints unnamed; S07 NO separado; FDs S03. |
| S08 | `accept4` | 288 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 028 YES AF_UNIX; flags descriptor se conservan aparte. |
| S08 | `recvmmsg` | 299 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 028 YES AF_UNIX por entrada/vector; payload y cmsg separados. |
| S08 | `sendmmsg` | 307 | `ALREADY_ADJUDICATED_MISREPRESENTED` | Checkpoint 028 YES AF_UNIX por entrada/vector; payload y cmsg separados. |

### Inconsistencia adicional S08, fuera de las 60 entradas

Checkpoint 028 incluye **18** YES y la tabla adjudica también `setsockopt`
(54) y `getsockopt` (55) para AF_UNIX. El array `surfaces[S08].syscalls`
actual contiene 16 nombres; no incluye 54/55. Tampoco hay un contexto S08
para 54/55 en sus filas, aunque las filas sí tienen contexto S07
`UNREVIEWED_CANDIDATE` y decisiones S07 sólo en checkpoint 026. Así, esos dos
YES S08 son decisiones checkpoint-only sin registro de candidatura/contexto
S08 correspondiente en el manifiesto. No son dos elementos adicionales del
conjunto actual de 60 S08 UNREVIEWED; se registran como
`ALREADY_ADJUDICATED_MISREPRESENTED` fuera de ese conjunto. No se añaden ni
materializan.

## 8. S15 — `ioctl` como UNKNOWN ya documentado

| Superficie | Syscall | NR | Estado del contexto de superficie | Provenance revisada | Clasificación |
|---|---|---:|---|---|---|
| S15 | `ioctl` | 16 | contexto `UNREVIEWED_CANDIDATE`; fila superior `UNREVIEWED` | Checkpoint 040 decide explícitamente UNKNOWN para la familia multiplexada; el único caso `FIONREAD` es effect coverage OBSERVED, no membership de familia. | `UNKNOWN_REPRESENTATION` |

No se modifica esa decisión. El caso `FIONREAD` no se interpreta como un
YES/NO para otros comandos, objetos o ABI.

## 9. Matriz de fuentes y hashes de provenance

| Fuente | Uso en esta reconstrucción | SHA-256 |
|---|---|---|
| Checkpoint 014 S01 | 13 YES, cuatro NO, UNKNOWN de las referencias históricas; distingue 304 y los candidatos directos no incluidos. | `70e1cfc2c7a74b51ecaeaac4f45fa92fee8d4093a26132ee0c07b7f502256c7d` |
| Checkpoint 021 preparación S05 | S05: siete candidaturas y 17 leads separados. | `bb59be5db2384e4375955bcd96ee94f5f02c42693f58e4a9585f46c5ac84a3e3` |
| Checkpoint 022 S05 | Seis YES materializados; `madvise` UNKNOWN. | `7ba9938b77fead0f829936190b7a0557cb8fdf711f30b496b7d54720a2946c32` |
| Checkpoint 023 preparación S06 | Diez candidaturas S06; distingue S05/anonymous/memfd. | `5874fdb8134e238dec58680f4f8424f7b6cc6fb3ff25a146bcdaa19817a6a6ab` |
| Checkpoint 024 S06 | Nueve YES y `msync` UNKNOWN; indica expresamente no materializar. | `d6bf479432d0e522c632a9f352035e9f3653a85698c6f1ad7de081b93e5c7ce0` |
| Checkpoint 025 preparación S07 | Delimita IP frente a AF_UNIX y las 17 candidaturas S07. | `349a5b99dd4fc10e4408897d592143dcace2744f0fd261f0a2393dec83b7f04d` |
| Checkpoint 026 S07 | 17 YES condicionales; explícitamente no materializados; socketpair S07 NO por separado. | `0868160d6425b065242a85f989c5e6a171c7dc98b1053857789aa2eb3f0ebdef` |
| Checkpoint 027 preparación S08 | 18 candidaturas AF_UNIX y sus ejes. | `bcc40808cbc5a42dbb246c6f57fac55fbbfcf56f3948e688ff98c00ce161d871` |
| Checkpoint 028 S08 | 18 YES AF_UNIX; expresamente no materializados; incluye 54/55. | `82bebe3d80b5b76e659d4ca8d637ecd96d7819d6a23ddf4a69c9c0f9f6991561` |
| Checkpoint 039 S14 | Confirma S14 como nueve APIs de biblioteca, fuera de membresías syscall. | `03d9585bb7e1aa0c4c97d7047854ed61a2467903422c4bc42c2e558d8eb610f4` |
| Checkpoint 040 S15 | `ioctl` UNKNOWN de familia; FIONREAD efecto acotado. | `ce503ec10eac9589621bb4bf60300e70bc7b4e76e2251ea1cde5471f850fb09a` |
| Checkpoint 041 S16 | Control de alcance: 51 leads no promovidos; sin impacto en estas decisiones. | `866d7913798c336bee3fd13f46d97e969b8e8c1ed0aac30b1ba19a73f7736abb` |
| Checkpoint 043 S02 | Cierre posterior S02; no cambia las 60 entradas. | `be0c2ad34825b823cdb1a8d4d89bb54eef08c33b6ac382bd51e7043dc642bbce` |
| Checkpoint 044 | Fuente de la lista de 60 y regla de parada previa. | `6f3885a6b70c54a6cf3c754275317716a240b9ce4c679b1b20fa097204fb62dc` |
| Manifiesto de lectura | Estado/candidate contexts y relaciones actuales. | `9e0f2f0f07240a0902598f989380c2febd7f2a1ee5f9314d8de156b08cc69a3e` |
| Ledger de lectura | Readiness/global disposition; sin cambios. | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |

No se encontró un campo de referencia a ledger por cada adjudicación de estas
filas; el ledger conserva estado global/readiness, no resuelve los
desacuerdos de representación de S06–S08.

## 10. Conclusión limitada y estado

- S01: 15 genuinamente pendientes en la representación fuente inspeccionada;
  no reabrir las decisiones distintas de checkpoint 014.
- S05: `madvise` UNKNOWN ya documentado; no promover.
- S06: nueve YES checkpoint-only mal representados como UNREVIEWED; `msync`
  UNKNOWN ya documentado.
- S07: 17 YES checkpoint-only mal representados como UNREVIEWED.
- S08: 16 YES checkpoint-only mal representados como UNREVIEWED; además,
  setsockopt/getsockopt (54/55) son dos YES checkpoint-only sin contexto S08
  en el manifiesto.
- S15: `ioctl` UNKNOWN de familia ya documentado; no cambiar.
- El solapamiento S07/S08 por número es legítimo por familia/variante y no
  se deduplica.
- La clasificación no cambia ninguna de las 60 entradas ni resuelve el
  crosswalk global; no se avanza a reconciliación global ni a A-PRE-1.
- El ledger no contiene un campo A-PRE-1; se conserva el estado documentado
  en checkpoint 044: `NOT AUTHORIZED / NOT EXECUTED`.
- No se ejecutó TALOS, workload, probe, test ni actividad dinámica. No se
  modificaron manifiesto, ledger, `requirements.lock`, código, seccomp,
  E5/Qwen, corpus, modelos o bases protegidas.
