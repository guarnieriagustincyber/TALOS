# Directiva 046 — reconciliación de representación S06–S08–S15

Fecha: 2026-10-01

## 1. Alcance y regla aplicada

Se correlacionaron exclusivamente las relaciones de S06, S07, S08 y S15 contra
los estados actuales del manifiesto y los checkpoints fuente 024, 026, 028 y
040. Se conservaron las diferencias de superficie aunque una syscall se
repita entre ellas. No se hizo nueva adjudicación semántica ni se modificaron
el manifiesto, ledger o `requirements.lock`.

El conteo de partida requiere una precisión: el resumen de checkpoint 045
contó 45 clasificaciones `ALREADY_ADJUDICATED_MISREPRESENTED` +
`UNKNOWN_REPRESENTATION` en todas las superficies, pero una de las tres
UNKNOWN es `madvise`/S05 y está fuera del alcance 046. Por tanto, los
contextos de 045 que sí corresponden a S06/S07/S08/S15 son 44: S06 10, S07
17, S08 16 y S15 1. Se cotejaron además las dos decisiones S08 documentadas
para setsockopt/getsockopt (54/55) que 045 había señalado por separado, los
tres YES S15 ya representados y el NO S07 de socketpair (53). El inventario
de relaciones revisadas es así de **50**, no 45. Esta aclaración de conteo no
cambia ninguna decisión fuente.

## 2. Snapshot e integridad

| Artefacto | SHA-256 antes de esta pasada |
|---|---|
| `files/A_PRE_0_SURFACE_MANIFEST.json` | `9e0f2f0f07240a0902598f989380c2febd7f2a1ee5f9314d8de156b08cc69a3e` |
| `files/A_PRE_0_QUALIFICATION_LEDGER.json` | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| `checkpoints/index.md` | `1167f604a15795473ef61d464ec77aa9a944ebad6c52c859909bda5152db62ab` |
| Checkpoint 045 | `f8b36c340b9b6b5c1b937bd431316c2dde3c7ccd3aebc5688ab3e430f064df10` |

HEAD al iniciar: `f81134fc2293916210d53c8065f3a0049e52b0b4`. El worktree estaba
sucio por cambios preexistentes; se preservaron. El ledger indica
`readiness.status=NOT_READY`, `predicate_result=false`; el manifiesto informa
385 filas, 0 disposiciones finales y `frozen=false`. A-PRE-1 no tiene campo
en el ledger; su estado documentado en 044/045 sigue
`NOT AUTHORIZED / NOT EXECUTED`.

### Fuentes de decisión

| Fuente | SHA-256 | Alcance usado |
|---|---|---|
| Checkpoint 024 — S06 | `d6bf479432d0e522c632a9f352035e9f3653a85698c6f1ad7de081b93e5c7ce0` | Diez candidaturas; nueve YES condicionales, `msync` UNKNOWN; expresamente no materializadas. |
| Checkpoint 026 — S07 | `0868160d6425b065242a85f989c5e6a171c7dc98b1053857789aa2eb3f0ebdef` | 17 YES IP condicionales; socketpair NO S07 separado; no materializa decisiones. |
| Checkpoint 028 — S08 | `82bebe3d80b5b76e659d4ca8d637ecd96d7819d6a23ddf4a69c9c0f9f6991561` | 18 YES AF_UNIX condicionales, incluidos 54/55; no materializa decisiones. |
| Checkpoint 040 — S15 | `ce503ec10eac9589621bb4bf60300e70bc7b4e76e2251ea1cde5471f850fb09a` | `ioctl` UNKNOWN; bpf, perf_event_open y userfaultfd YES ya materializados. |
| Checkpoint 045 | `f8b36c340b9b6b5c1b937bd431316c2dde3c7ccd3aebc5688ab3e430f064df10` | Provenance de los 60 contextos y observación de la omisión S08 54/55. |

## 3. Tabla completa de reconciliación

`Contexto actual` expresa la relación de esa superficie, no la disposición
global. Todas las disposiciones globales de estas filas siguen UNKNOWN. En
`estado propuesto`, SAFE_TO_MATERIALIZE significa que una pasada posterior
puede registrar exactamente la decisión del checkpoint, con su scope; no es
autorización para modificar el manifiesto en esta pasada.

### S06 — checkpoint 024

| Syscall | NR | Superficie | Estado actual en manifest | Contexto actual | Decisión documentada | Checkpoint origen | Condición/alcance de la decisión | Estado de representación propuesto | Evidencia exacta | Contradicción |
|---|---:|---|---|---|---|---|---|---|---|---|
| `mmap` | 9 | S06 | `HUMAN_ADJUDICATED_CANDIDATE` en fila | `UNREVIEWED_CANDIDATE` S06; S05 tiene YES separado | YES condicional | 024, tabla §2 fila NR 9 | Anonymous `MAP_ANONYMOUS` o FD memfd/secretmem admitido; excluir archivo convencional; preservar flags/backing/protection/rango/FD/offset | `SAFE_TO_MATERIALIZE` | Decisión y límite escritos para NR 9; coincide identidad syscall/superficie y la condición no absorbe S05 | Ninguna |
| `mprotect` | 10 | S06 | `HUMAN_ADJUDICATED_CANDIDATE` | `UNREVIEWED_CANDIDATE` S06; S05 separa file-backed | YES condicional | 024, §2 fila NR 10 | Sólo rango anonymous o memfd-backed; conservar `PROT_*`, rango, longitud y alineación | `SAFE_TO_MATERIALIZE` | NR 10, checkpoint 024 §2 y tabla de evidencia §3 | Ninguna |
| `munmap` | 11 | S06 | `HUMAN_ADJUDICATED_CANDIDATE` | `UNREVIEWED_CANDIDATE` S06; S05 separado | YES condicional | 024, §2 fila NR 11 | Retirar total/parcialmente rango anonymous o memfd-backed; no implica cerrar FD ni destruir objeto con otras referencias | `SAFE_TO_MATERIALIZE` | NR 11, checkpoint 024 §2; límite de FD y S05 explícito | Ninguna |
| `mremap` | 25 | S06 | `HUMAN_ADJUDICATED_CANDIDATE` | `UNREVIEWED_CANDIDATE` S06 | YES condicional | 024, §2 fila NR 25 | Sólo mappings anonymous/memfd; tamaños, grow/shrink/move, `MREMAP_MAYMOVE`/`MREMAP_FIXED` separados | `SAFE_TO_MATERIALIZE` | NR 25, checkpoint 024 §2 | Ninguna |
| `msync` | 26 | S06 | `HUMAN_ADJUDICATED_CANDIDATE` | `UNREVIEWED_CANDIDATE` S06; S05 YES no resuelve S06 | UNKNOWN | 024, §2 fila NR 26 y §5 | No adjudica S06; separar anonymous shared/memfd y `MS_*`; no copiar decisión S05 | `REQUIRES_HUMAN_DECISION` | UNKNOWN inequívoco en 024 §2 y §5. El manifiesto sólo admite estados contextuales CANDIDATE/NOT_MEMBER, no UNKNOWN; no se inventa ahora un valor/estructura canónica | No semántica; sólo falta elegir representación explícita de UNKNOWN |
| `fcntl` | 72 | S06 | `PARTIALLY_HUMAN_ADJUDICATED_BY_SURFACE` | `UNREVIEWED_CANDIDATE` S06; S03 contiene comandos diferentes | YES condicional | 024, §2 fila NR 72 | Sólo `F_ADD_SEALS` en memfd con sealing habilitado (`MFD_ALLOW_SEALING`); no `F_GET_SEALS` ni otros comandos; comandos S03 permanecen separados | `SAFE_TO_MATERIALIZE` | NR 72, checkpoint 024 §2; scope separa expresamente los cuatro comandos S03 | Ninguna |
| `ftruncate` | 77 | S06 | `PARTIALLY_HUMAN_ADJUDICATED_BY_SURFACE` | `UNREVIEWED_CANDIDATE` S06; decisión S04 preexistente no se reemplaza | YES condicional | 024, §2 fila NR 77 | Sólo resize de objeto memfd/secretmem que establece/gestiona backing S06; no mover objeto a archivo convencional ni absorber S04 | `SAFE_TO_MATERIALIZE` | NR 77, checkpoint 024 §2; cruce S04 reafirmado | Ninguna |
| `memfd_create` | 319 | S06 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S06 | YES condicional | 024, §2 fila NR 319 | Creación de memfd convencional; conservar flags, combinaciones y soporte ABI/kernel; FD/S03 y mapping/S05 separados | `SAFE_TO_MATERIALIZE` | NR 319, checkpoint 024 §2 | Ninguna |
| `pkey_mprotect` | 329 | S06 | `HUMAN_ADJUDICATED_CANDIDATE` | `UNREVIEWED_CANDIDATE` S06 | YES condicional | 024, §2 fila NR 329 | Sólo rango anonymous/memfd; `PROT_*`, pkey, rango/alineación; lifecycle de key no incluido | `SAFE_TO_MATERIALIZE` | NR 329, checkpoint 024 §2 | Ninguna |
| `memfd_secret` | 447 | S06 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S06 | YES condicional | 024, §2 fila NR 447 | Creación secretmem con soporte target; conservar flags, FD y restricciones; no equiparar a memfd convencional | `SAFE_TO_MATERIALIZE` | NR 447, checkpoint 024 §2 | Ninguna |

### S07 — checkpoint 026

Las 17 decisiones son para comunicación IP AF_INET/AF_INET6, no AF_UNIX.
En llamadas de transporte se conserva S02 sólo para payload realmente
transferido; `SCM_RIGHTS` sólo para transferencia efectiva corresponde a S09;
FD/flags, workers y coordinación no se absorben como S03/S10/S11. El
checkpoint no afirma ejecución, efecto observado, política aplicada ni
disposición global.

| Syscall | NR | Superficie | Estado actual en manifest | Contexto actual | Decisión documentada | Checkpoint origen | Condición/alcance de la decisión | Estado de representación propuesto | Evidencia exacta | Contradicción |
|---|---:|---|---|---|---|---|---|---|---|---|
| `socket` | 41 | S07 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S07 y S08 | YES condicional | 026, §2 fila 41 | Sólo domain AF_INET/AF_INET6; conservar type, protocol, flags. AF_UNIX S08 | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 41 delimita explícitamente AF_UNIX a S08 | Ninguna |
| `connect` | 42 | S07 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S07 y S08 | YES condicional | 026, §2 fila 42 | Peer/asociación en socket IP; stream/datagram, sockaddr, estado y retorno/error; AF_UNIX fuera | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 42 | Ninguna |
| `accept` | 43 | S07 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S07 y S08 | YES condicional | 026, §2 fila 43 | Conexión pendiente en listener IP; family/peer, dirección retornada, bloqueo/cola/FD/resultado separados | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 43; FD lifecycle no adjudica S03 | Ninguna |
| `sendto` | 44 | S07 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S07 y S08 | YES condicional | 026, §2 fila 44 | En socket IP; family/type/protocol, peer/destino, flags, bytes y retorno; payload transferido puede cruzar S02 aparte | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 44 | Ninguna |
| `recvfrom` | 45 | S07 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S07 y S08 | YES condicional | 026, §2 fila 45 | Recepción en socket IP; family/type/protocol, buffer/flags, source address, truncamiento/bytes/retorno; payload efectivo S02 separado | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 45 | Ninguna |
| `sendmsg` | 46 | S07 | `PARTIALLY_HUMAN_ADJUDICATED_BY_SURFACE` | `UNREVIEWED_CANDIDATE` S07 y S08 | YES condicional | 026, §2 fila 46 | Comunicación IP; preservar destination, iovec, flags, control/cmsg; S02 payload efectivo; S09 sólo SCM_RIGHTS efectivo | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 46 define cruces y excluye AF_UNIX | Ninguna |
| `recvmsg` | 47 | S07 | `PARTIALLY_HUMAN_ADJUDICATED_BY_SURFACE` | `UNREVIEWED_CANDIDATE` S07 y S08 | YES condicional | 026, §2 fila 47 | Socket IP; source, iovec, flags, truncamiento y cmsg; S02/S09 separados | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 47 | Ninguna |
| `shutdown` | 48 | S07 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S07 y S08 | YES condicional | 026, §2 fila 48 | En socket IP; `SHUT_RD/WR/RDWR`, estado y resultado; no equivale a close/S03 | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 48 | Ninguna |
| `bind` | 49 | S07 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S07 y S08 | YES condicional | 026, §2 fila 49 | Dirección local AF_INET/AF_INET6; family/address/port/scope/interface/length/resultado; AF_UNIX queda S08 | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 49 | Ninguna |
| `listen` | 50 | S07 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S07 y S08 | YES condicional | 026, §2 fila 50 | Sólo listener IP de tipo/estado compatible; family, bind previo/implícito, backlog y resultado | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 50 | Ninguna |
| `getsockname` | 51 | S07 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S07 y S08 | YES condicional | 026, §2 fila 51 | Endpoint local IP; family, address/port/scope, longitud value-result y error | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 51 | Ninguna |
| `getpeername` | 52 | S07 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S07 y S08 | YES condicional | 026, §2 fila 52 | Peer IP establecido; address/port/scope, longitud, estado y error | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 52 | Ninguna |
| `setsockopt` | 54 | S07 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S07; sin contexto S08 | YES condicional | 026, §2 fila 54 | Sólo opción que configura networking IP/transport; conservar `level`, `optname`, family/type/protocol, optval/optlen; no afirmar enumeración completa | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 54 afirma YES IP condicionado y deja la lista target/versionada abierta; S08 se coteja aparte abajo | Ninguna |
| `getsockopt` | 55 | S07 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S07; sin contexto S08 | YES condicional | 026, §2 fila 55 | Sólo consulta de estado/opción IP/transport; conservar level/name/value/length/family/type/protocol; opciones concretas por particionar | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 55 afirma YES IP condicionado y deja la lista target/versionada abierta | Ninguna |
| `accept4` | 288 | S07 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S07 y S08 | YES condicional | 026, §2 fila 288 | Condición IP de accept; `SOCK_CLOEXEC`/`SOCK_NONBLOCK`, peer y FD separados | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 288 | Ninguna |
| `recvmmsg` | 299 | S07 | `PARTIALLY_HUMAN_ADJUDICATED_BY_SURFACE` | `UNREVIEWED_CANDIDATE` S07 y S08 | YES condicional | 026, §2 fila 299 | Socket IP; vector, vlen, payload/control por mensaje, flags, timeout y retorno parcial; S02/S09 aparte | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 299 | Ninguna |
| `sendmmsg` | 307 | S07 | `PARTIALLY_HUMAN_ADJUDICATED_BY_SURFACE` | `UNREVIEWED_CANDIDATE` S07 y S08 | YES condicional | 026, §2 fila 307 | Socket IP; vector, destino, payload/control por mensaje, flags y retorno parcial; S02/S09 aparte | `SAFE_TO_MATERIALIZE` | Tabla §2 NR 307 | Ninguna |
| `socketpair` | 53 | S07 | `UNREVIEWED` en fila; syscall ausente del array S07 | No existe contexto S07; sí existe contexto S08 `UNREVIEWED_CANDIDATE` | NO S07 en el subcaso documentado | 026, §1 y §6–7; checkpoint 028 §3 fila 53 adjudica S08 YES | S07 está limitado a AF_INET/AF_INET6; socketpair Linux documentado para AF_UNIX y AF_TIPC; S08 sólo AF_UNIX/AF_LOCAL, unnamed endpoints | `ALREADY_CORRECT` | El array S07 omite syscall 53 y sus exclusiones reservan AF_UNIX para S08; checkpoints 026 y 028 mantienen las decisiones separadas | Ninguna; NO S07 no contradice YES S08 |

### S08 — checkpoint 028

Las 18 decisiones son para AF_UNIX/AF_LOCAL; preservan pathname, abstract y
unnamed según corresponda. La lista finita de opciones 54/55 no quedó cerrada
en 028, pero la decisión relacional es un YES condicional explícito. Se puede
registrar sólo el scope delimitado por esa condición, manteniendo pendiente la
partición exhaustiva de opciones. Los cruces filesystem/pathname no adjudican
automáticamente S01/S04; payload no absorbe S02; FD/capacidades y control
messages conservan S03/S09/S10 independientes.

| Syscall | NR | Superficie | Estado actual en manifest | Contexto actual | Decisión documentada | Checkpoint origen | Condición/alcance de la decisión | Estado de representación propuesto | Evidencia exacta | Contradicción |
|---|---:|---|---|---|---|---|---|---|---|---|
| `socket` | 41 | S08 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S08 y S07 | YES condicional | 028, §3 fila 41 | Domain AF_UNIX/AF_LOCAL y tipo/protocolo admitidos; unnamed permitido; IP queda S07 | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 41 | Ninguna |
| `connect` | 42 | S08 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S08 y S07 | YES condicional | 028, §3 fila 42 | Socket AF_UNIX; sockaddr pathname/abstract; stream/seqpacket/datagram según estado | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 42; pathname S01/S04 separado y abstract no filesystem | Ninguna |
| `accept` | 43 | S08 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S08 y S07 | YES condicional | 028, §3 fila 43 | Listener AF_UNIX orientado a conexión y compatible; FD nuevo/S03 separado | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 43 | Ninguna |
| `sendto` | 44 | S08 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S08 y S07 | YES condicional | 028, §3 fila 44 | Transporte AF_UNIX; datagram destination o comunicación conectada válida; tipo/peer/flags preservados | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 44; payload efectivo es S02 separado | Ninguna |
| `recvfrom` | 45 | S08 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S08 y S07 | YES condicional | 028, §3 fila 45 | Recepción AF_UNIX; type/state/origen pathname/abstract/unnamed/addrlen/flags/resultado | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 45; S02 sólo payload efectivo | Ninguna |
| `sendmsg` | 46 | S08 | `PARTIALLY_HUMAN_ADJUDICATED_BY_SURFACE` | `UNREVIEWED_CANDIDATE` S08 y S07 | YES condicional | 028, §3 fila 46 | Transporte por endpoint AF_UNIX; iovec/cmsg/flags/result separados; S02 payload y S09 SCM_RIGHTS sólo si efectivos | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 46 | Ninguna |
| `recvmsg` | 47 | S08 | `PARTIALLY_HUMAN_ADJUDICATED_BY_SURFACE` | `UNREVIEWED_CANDIDATE` S08 y S07 | YES condicional | 028, §3 fila 47 | Recepción AF_UNIX; name/iovec/control/truncamiento/result; S02/S09 separados | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 47 | Ninguna |
| `shutdown` | 48 | S08 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S08 y S07 | YES condicional | 028, §3 fila 48 | `SHUT_RD/WR/RDWR` en canal AF_UNIX; distinto de close/S03 | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 48 | Ninguna |
| `bind` | 49 | S08 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S08 y S07 | YES condicional | 028, §3 fila 49 | Address AF_UNIX pathname o abstract; pathname no decide S01/S04; abstract no es filesystem | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 49 | Ninguna |
| `listen` | 50 | S08 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S08 y S07 | YES condicional | 028, §3 fila 50 | Socket AF_UNIX orientado a conexión, type/state compatible, backlog/result | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 50 | Ninguna |
| `getsockname` | 51 | S08 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S08 y S07 | YES condicional | 028, §3 fila 51 | Address local AF_UNIX pathname/abstract/autobind/unnamed según estado y longitud | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 51; retorno pathname no adjudica S01/S04 | Ninguna |
| `getpeername` | 52 | S08 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S08 y S07 | YES condicional | 028, §3 fila 52 | Peer AF_UNIX cuando exista según type/state; pathname/abstract/unnamed | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 52 | Ninguna |
| `socketpair` | 53 | S08 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S08; no contexto S07 | YES condicional | 028, §3 fila 53 | Sólo AF_UNIX/AF_LOCAL y type admitido; dos endpoints conectados unnamed; sin pathname; S07 NO permanece aparte | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 53 y delimitación expresa frente a S07 | Ninguna |
| `setsockopt` | 54 | S08 | `UNREVIEWED` en fila; sólo contexto S07 | No existe contexto S08; `UNREVIEWED_CANDIDATE` en S07 | YES condicional | 028, §3 fila 54 | Socket AF_UNIX y opción/level que configura endpoint/comunicación local; sólo opciones concretas relevantes; lista exhaustiva target/versionada pendiente | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 54 afirma S08 YES, da ejemplos y excluye opciones sin dimensión AF_UNIX; checkpoint 045 confirma que no hay contexto S08 ni decisión posterior contradictoria | Ninguna; falta de contexto no contradice la decisión explícita |
| `getsockopt` | 55 | S08 | `UNREVIEWED` en fila; sólo contexto S07 | No existe contexto S08; `UNREVIEWED_CANDIDATE` en S07 | YES condicional | 028, §3 fila 55 | Socket AF_UNIX y consulta de opción/estado local relevante; p. ej. `SO_PEERCRED` en condiciones aplicables; particionar por level/type/state; enumeración completa pendiente | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 55 afirma S08 YES y define su condición; checkpoint 045 confirma ausencia de contexto S08 | Ninguna; falta de contexto no contradice la decisión explícita |
| `accept4` | 288 | S08 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S08 y S07 | YES condicional | 028, §3 fila 288 | Aceptación AF_UNIX compatible; preservar `SOCK_CLOEXEC`/`SOCK_NONBLOCK` y lifecycle FD/S03 separado | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 288 | Ninguna |
| `recvmmsg` | 299 | S08 | `PARTIALLY_HUMAN_ADJUDICATED_BY_SURFACE` | `UNREVIEWED_CANDIDATE` S08 y S07 | YES condicional | 028, §3 fila 299 | AF_UNIX; vector, retorno parcial, payload/control y flags; S02/S09 separados | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 299 | Ninguna |
| `sendmmsg` | 307 | S08 | `PARTIALLY_HUMAN_ADJUDICATED_BY_SURFACE` | `UNREVIEWED_CANDIDATE` S08 y S07 | YES condicional | 028, §3 fila 307 | AF_UNIX; vector, retorno parcial, payload/control y flags; S02/S09 separados | `SAFE_TO_MATERIALIZE` | Tabla §3 NR 307 | Ninguna |

**Decisión específica 54/55 (alternativas A/B/C):** A. Las dos filas del
checkpoint 028 nombran exactamente `setsockopt` (54) y `getsockopt` (55),
identifican S08 y especifican una relación YES AF_UNIX condicionada a opciones
locales relevantes. El checkpoint 045 confirma que faltan únicamente en la
representación S08 del manifiesto. No hay una adjudicación posterior
contradictoria. La categoría es `SAFE_TO_MATERIALIZE`, conservando la
condición y dejando pendiente enumeración exhaustiva de opciones; no se
extiende el YES a todas las opciones ni a AF_INET/AF_INET6.

### S15 — checkpoint 040

| Syscall | NR | Superficie | Estado actual en manifest | Contexto actual | Decisión documentada | Checkpoint origen | Condición/alcance de la decisión | Estado de representación propuesto | Evidencia exacta | Contradicción |
|---|---:|---|---|---|---|---|---|---|---|---|
| `ioctl` | 16 | S15 | `UNREVIEWED` | `UNREVIEWED_CANDIDATE` S15 | UNKNOWN a nivel de familia | 040, §2 fila ioctl y §3 | `FIONREAD 0x541B` sólo effect coverage OBSERVED para pipe sintético; no adjudica membership general ni otras operaciones | `REQUIRES_HUMAN_DECISION` | 040 establece UNKNOWN inequívoco; no existe en el manifiesto un estado de contexto UNKNOWN ni una decisión UNKNOWN en `surface_membership_adjudications` | No semántica; sólo falta decidir representación canónica para UNKNOWN |
| `bpf` | 321 | S15 | `HUMAN_ADJUDICATED_CANDIDATE` | Contexto S15 `HUMAN_ADJUDICATED_CANDIDATE` | YES | 040, §2 fila bpf | Entrada de API kernel; particionar `cmd`, attrs/size y objeto; sin allowlist/efecto/bloqueo inferido | `ALREADY_CORRECT` | El contexto S15 ya está adjudicado y la relación JSON contiene scope y referencia al checkpoint 040 | Ninguna |
| `perf_event_open` | 298 | S15 | `HUMAN_ADJUDICATED_CANDIDATE` | Contexto S15 `HUMAN_ADJUDICATED_CANDIDATE` | YES condicional | 040, §2 fila perf_event_open | API condicionada a type/config, sample/read format, pid/cpu/group/flags, objeto, permisos y resultado; no implica evento/efecto observado | `ALREADY_CORRECT` | Contexto S15 del manifiesto ya es HUMAN_ADJUDICATED_CANDIDATE con scope y ref 040 | Ninguna |
| `userfaultfd` | 323 | S15 | `HUMAN_ADJUDICATED_CANDIDATE` | Contexto S15 `HUMAN_ADJUDICATED_CANDIDATE` | YES para creación | 040, §2 fila userfaultfd | Sólo `userfaultfd(flags)`; configuración/features, UFFDIO registro/eventos, memoria S05/S06 y procesos S11 permanecen separados | `ALREADY_CORRECT` | Contexto S15 del manifiesto ya es HUMAN_ADJUDICATED_CANDIDATE con scope y ref 040 | Ninguna |

`proposed_policy.default=DENY` para operaciones S15 específicas tiene
`enforcement_status=NOT_DEMONSTRATED`. Es propuesta de policy, no decisión
BLOCKED ni prueba de enforcement. No cambia las cuatro clasificaciones.

## 4. Resultado por clasificación

| Clasificación | Cantidad | Relaciones |
|---|---:|---|
| `SAFE_TO_MATERIALIZE` | 44 | S06: 9 YES; S07: 17 YES; S08: 18 YES (16 contextos existentes y los dos casos explícitos 54/55 ausentes). |
| `REQUIRES_HUMAN_DECISION` | 2 | S06 `msync` UNKNOWN y S15 `ioctl` UNKNOWN: decisión semántica ya existente; falta decidir cómo representarla en el esquema canónico, que hoy no ofrece estado de membership UNKNOWN. |
| `ALREADY_CORRECT` | 4 | S15 `bpf`, `perf_event_open`, `userfaultfd` ya representados como candidatos adjudicados; S07 `socketpair` excluido del array S07, separado de su YES S08. |
| `CONTRADICTORY` | 0 | No se encontró checkpoint posterior que contradiga las decisiones fuente ni incompatibilidad entre los scopes IP y AF_UNIX. |
| `UNRESOLVED` | 0 | Las condiciones residuales ya están delimitadas en sus decisiones; no se las convierte en nuevas decisiones. |
| **Total** | **50** | Relaciones individuales syscall/superficie; overlaps legítimos cuentan por superficie. |

### Relación checkpoint → decisión → representación

- 024 → nueve YES S06 condicionados → contextos S06 todavía
  `UNREVIEWED_CANDIDATE`; son `SAFE_TO_MATERIALIZE`. Su scope preserva
  backing anonymous/memfd y separa S05/S03/S04.
- 024 → `msync` S06 UNKNOWN → contexto S06 sigue UNREVIEWED; no crear
  membership YES/NO. La forma canónica de registrar explícitamente UNKNOWN
  requiere decisión humana; detener esa entrada.
- 026 → 17 YES S07 AF_INET/AF_INET6 → contextos S07 todavía UNREVIEWED;
  `SAFE_TO_MATERIALIZE` con scopes por syscall. AF_UNIX se mantiene separado.
- 026 → `socketpair` NO S07 → no existe contexto ni entrada en array S07;
  el array y su exclusión de AF_UNIX concuerdan, `ALREADY_CORRECT`. No se
  traslada el NO a S08.
- 028 → 18 YES S08 AF_UNIX → 16 contextos S08 UNREVIEWED más dos filas
  (54/55) sin contexto S08; todos pueden materializarse bajo la condición
  exacta de cada decisión. Para opciones 54/55, la enumeración total queda
  pendiente; la relación S08 condicional ya fue decidida.
- 040 → `ioctl` S15 UNKNOWN y FIONREAD coverage acotada → no convertir la
  observación en membership; decidir sólo formato explícito de UNKNOWN.
- 040 → tres YES S15 → ya cuentan con contexto S15 humano adjudicado,
  referencia y scope en manifiesto; conservarlos sin modificación.

## 5. Estado posterior y verificaciones de integridad

| Verificación | Resultado |
|---|---|
| Manifiesto JSON válido | Sí |
| Filas/nombres/números únicos | 385 / 385 / 385 |
| Disposiciones globales UNKNOWN | 385/385 |
| Disposiciones globales finales | 0 |
| `inventory.frozen` | `false` |
| A-PRE-0 | `NOT_READY` (`predicate_result=false`) |
| A-PRE-1 | `NOT AUTHORIZED / NOT EXECUTED` (estado documental preservado de 044/045; no existe campo A-PRE-1 en ledger) |
| Hash manifiesto antes/después | Idéntico: `9e0f2f0f07240a0902598f989380c2febd7f2a1ee5f9314d8de156b08cc69a3e` |
| Hash ledger antes/después | Idéntico: `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| Hash `requirements.lock` antes/después | Idéntico: `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| `git diff --check` | Limpio |

Sólo se creó este checkpoint y se actualizó `checkpoints/index.md`. No se
modificaron manifest, ledger, lock, otras superficies ni políticas. No se
ejecutaron TALOS, FastAPI, workloads, probes, benchmarks, tests, A-PRE-1 ni
ninguna actividad dinámica. No se cargaron corpus/modelos ni se tocaron
bases, seccomp, E5/Qwen, VM o overlay.

## 6. Parada

La clasificación documental queda cerrada para las 50 relaciones listadas.
No materializar todavía las 44 relaciones SAFE en el manifiesto. Resolver con
decisión humana exclusivamente la forma canónica para representar los dos
UNKNOWN antes de cualquier modificación. No avanzar a S01 ni reanudar la
reconciliación global.
