# Preparación documental — lote 08, S08 AF_UNIX

Fecha: 2026-10-01

## 1. Identidad, alcance y estado de autoridad

Repositorio: `/media/agustin/Laboratorio/study-engie`

```text
HEAD   f81134fc2293916210d53c8065f3a0049e52b0b4
TREE   c322e78980ac72f24c66b1396014faefaac074a9
PARENT b17dd9c4dab098512aa6c148e7d36c613da41c28
```

El worktree ya estaba sucio antes de esta preparación. No se limpió ni se
modificó ninguno de esos cambios. El checkpoint 026 estaba presente como
documentación no rastreada del estado de trabajo y se conservó intacto:

```text
SHA-256 checkpoints/026-adjudicacion-documental-lote-07-s07.md
0868160d6425b065242a85f989c5e6a171c7dc98b1053857789aa2eb3f0ebdef
```

El manifiesto y el ledger se encuentran byte-idénticos a HEAD al inicio:

```text
A_PRE_0_SURFACE_MANIFEST.json
bc498e058585341b341f8318fb8a2dd869c5737ebd63fd89f0878cef0793e20e
A_PRE_0_QUALIFICATION_LEDGER.json
0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42
```

Doctrina provisional a preparar para decisión humana posterior:

> S08 es la superficie de comunicación mediante sockets AF_UNIX/AF_LOCAL y
> sus endpoints locales, incluyendo establecimiento, direccionamiento,
> conexión, aceptación, transmisión, consulta y lifecycle de endpoints
> pathname y abstract namespace, distinguiendo payload, control messages y
> transferencia de capacidades.

S08 no es una categoría genérica de IPC. Este checkpoint **prepara** relaciones
para adjudicación posterior: no decide S08 YES/NO/UNKNOWN, no añade ni
materializa membresías, no adjudica S01/S02/S03/S04/S07/S09/S10, ni cambia
disposiciones globales.

## 2. Conjunto de revisión y separación de estados

La directiva enumera 18 syscalls para revisión documental S08: las 17
operaciones socket que ya son candidatas S07 y `socketpair` (53). La selección
de una syscall para examinar no implica que toda llamada de esa syscall sea
S08.

En el manifiesto, la tabla de syscalls es target-bound x86_64, 385 filas, con
hash `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
Las relaciones S08 presentes allí son **candidaturas/referencias estáticas no
revisadas**, no membresías adjudicadas. Por ejemplo, `socket` (41) tiene
candidatos S07 y S08 con estado `UNREVIEWED`; `socketpair` (53) tiene candidato
S08 con estado `UNREVIEWED`; ambas filas mantienen `disposition_status=UNKNOWN`.
El checkpoint 026 adjudicó la dimensión IP S07 para variantes AF_INET/AF_INET6,
no la dimensión AF_UNIX.

## 3. Candidaturas y semántica por operación — todas pendientes

| NR / syscall | Decisión S08 | Pregunta semántica y variantes que preservar | Evidencia documental y límite |
|---|---|---|---|
| 41 `socket` | **PENDING — no adjudicar** | ¿Pertenece la creación si `domain=AF_UNIX`/`AF_LOCAL` y el par `type`/`protocol` es válido? Particionar `SOCK_STREAM`, `SOCK_DGRAM`, `SOCK_SEQPACKET`; registrar flags `SOCK_NONBLOCK`/`SOCK_CLOEXEC` como ejes separados. AF_INET/AF_INET6 queda en partición S07; otras familias no se incorporan por analogía. | `socket(2)`, `unix(7)`, UAPI `linux/un.h` y `socket.h`. El nombre de la syscall, FD devuelto o familia por sí solos no demuestran una relación global. |
| 42 `connect` | **PENDING — no adjudicar** | Separar dirección pathname, abstract y demás address válida; conexión de stream/seqpacket frente a asociación por datagrama; connected state, longitud sockaddr, blocking/nonblocking y error (incluidos permisos/resolución/no listener). | `connect(2)` y `unix(7)` describen family del sockaddr, permisos y errores AF_UNIX. Resolver/localizar un pathname no equivale a toda la superficie S01. |
| 49 `bind` | **PENDING — no adjudicar** | Separar `sockaddr_un` pathname que establece endpoint con nombre y abstract address que no representa pathname. Conservar `sun_path`, longitud suministrada, terminador, colisiones, resultado y lifecycle. | `bind(2)` delega las reglas por family a `unix(7)`; `unix(7)` describe socket pathname y abstract namespace. La relación S04 por creación de entrada filesystem queda abierta. |
| 50 `listen` | **PENDING — no adjudicar** | Listener AF_UNIX de tipo orientado a conexión; estado/bind, backlog, pathname/abstract/unnamed si aplica, errores. No asumir semántica listener para datagram. | `listen(2)`, `accept(2)` y `unix(7)`. La pertenencia depende de family y tipo/estado, no del FD aislado. |
| 43 `accept` | **PENDING — no adjudicar** | Aceptación en listener AF_UNIX; conservar address de peer y `addrlen` value-result, tipo/estado, blocking, descriptor nuevo y errores. | `accept(2)` y `unix(7)` cubren aceptación y direcciones retornadas. Crear un FD no adjudica por sí mismo S03. |
| 288 `accept4` | **PENDING — no adjudicar** | Igual frontera AF_UNIX que `accept`; particionar `SOCK_CLOEXEC`, `SOCK_NONBLOCK`, dirección devuelta y nuevo descriptor. | `accept(2)` documenta `accept4`/flags; S03 FD hygiene queda como cruce, no como conclusión S08/S03. |
| 44 `sendto` | **PENDING — no adjudicar** | Comunicación AF_UNIX, especialmente datagram con destino pathname/abstract; distinguir socket conectado y address omitida/indicada, type, flags, payload efectivo, resultado parcial/error. | `send(2)` y `unix(7)`. AF_UNIX transport, payload S02 y path lookup no son conceptos intercambiables. |
| 45 `recvfrom` | **PENDING — no adjudicar** | Recepción AF_UNIX; tipo/estado, buffer/flags, origen pathname/abstract/unnamed y `addrlen` value-result, truncamiento, bytes recibidos y error. | `recv(2)` y `unix(7)` documentan address y resultado; sólo payload efectivamente transferido plantea cruce S02. |
| 46 `sendmsg` | **PENDING — no adjudicar** | Socket AF_UNIX; mantener separados `msg_iov`/payload, destination/name, flags y cada control message (`cmsg_level`, `cmsg_type`, longitud/datos). | `send(2)`, `unix(7)`, `cmsg(3)`; la API admite ancillary data, pero uso de `sendmsg` no demuestra FD passing ni credenciales. |
| 47 `recvmsg` | **PENDING — no adjudicar** | Socket AF_UNIX; separar payload, origen, control buffer, `MSG_CTRUNC`/`MSG_TRUNC`, cmsg efectivamente entregados, descriptores instalados, flags y resultado. | `recv(2)`, `unix(7)`, `cmsg(3)`. El tamaño insuficiente/flags y el contenido realmente recibido son parte de la partición. |
| 307 `sendmmsg` | **PENDING — no adjudicar** | Considerar mensajes AF_UNIX por entrada/vector; conservar `vlen`, address, iovec, control data, longitud por mensaje, retorno parcial y error. | `sendmmsg(2)` más semántica AF_UNIX de `send(2)`/`unix(7)`. Verificar soporte exacto de familia/protocolo/versión target antes de cerrar subvariantes. |
| 299 `recvmmsg` | **PENDING — no adjudicar** | Considerar mensajes AF_UNIX por entrada/vector; source address, payload y cmsg de cada entrada; timeout, flags, truncamiento, número de mensajes, retorno parcial y error. | `recvmmsg(2)` y `recv(2)`/`unix(7)`. No atribuir contenido de cmsg ni payload que no se recibió efectivamente. |
| 51 `getsockname` | **PENDING — no adjudicar** | Consultar endpoint local AF_UNIX y distinguir pathname, abstract, autobind y unnamed; address devuelta, longitud value-result y estado. | `getsockname(2)` y `unix(7)`. La consulta puede identificar un endpoint sin realizar resolución S01 completa ni mutación S04. |
| 52 `getpeername` | **PENDING — no adjudicar** | Consultar peer AF_UNIX; distinguir connected stream/seqpacket, datagram association y peer/address sin nombre; conservar length/error. | `getpeername(2)` y `unix(7)`. No asumir que existe peer utilizable para todo tipo/estado. |
| 48 `shutdown` | **PENDING — no adjudicar** | Shutdown de canal AF_UNIX por `SHUT_RD`, `SHUT_WR` o `SHUT_RDWR`; distinguirlo de `close`, cierre del último descriptor y destrucción del endpoint. | `shutdown(2)`, `socket(7)` y `unix(7)`. Comunicación/lifecycle S08 y lifecycle del FD S03 son ejes diferentes. |
| 54 `setsockopt` | **PENDING — no adjudicar** | Particionar por AF_UNIX, `level`, `optname`, type, optval/optlen y resultado. Revisar opciones Linux locales como `SO_PASSCRED`, `SO_PASSSEC`, `SO_PEEK_OFF`; separar opciones comunes `SOL_SOCKET` que no expresan semántica local específica. | `unix(7)` y `socket(7)` describen opciones; no adjudicar indiscriminadamente todas las opciones ni inferir su soporte target sólo desde documentación general. |
| 55 `getsockopt` | **PENDING — no adjudicar** | Igual partición por level/name/type; revisar consultas AF_UNIX como `SO_PEERCRED` y opciones locales con condición de estado/tipo, longitud y resultado. | `unix(7)` y `getsockopt(2)`. `SO_PEERCRED` está documentado para determinados sockets AF_UNIX conectados/socketpair; no se generaliza a todos los endpoints. |
| 53 `socketpair` | **PENDING — no adjudicar** | Crear simultáneamente dos endpoints AF_UNIX conectados y unnamed; conservar domain, type, protocol, ambos FDs, retorno/error y lifecycle independiente. AF_TIPC documentado para Linux no es AF_UNIX/S08. | `socketpair(2)` limita dominios Linux documentados a AF_UNIX/AF_LOCAL y AF_TIPC; `unix(7)` dice que los dos extremos son unnamed. La evidencia no adjudica AF_UNIX; el resultado previo S07 NO para dominios documentados no implica S08 YES. |

Los `protocol`, familias soportadas, flags válidos y resultados deben ligarse a
la versión target. La documentación general de Linux da semántica de interfaz;
no prueba que toda combinación sea válida, alcanzable o usada por TALOS.

## 4. Endpoints pathname y abstract namespace

| Atributo | Pathname AF_UNIX | Abstract AF_UNIX |
|---|---|---|
| Representación | `sun_path` con pathname y longitud que incluye/expresa su terminación conforme a la regla Linux documentada. | Primer byte de `sun_path` NUL; el nombre son bytes dentro de `addrlen`, incluidos NUL interiores con significado de byte. |
| `bind` | Establece endpoint asociado a una entrada tipo socket en el filesystem; reglas de path traversal, permisos/directorios, namespace y colisión son relevantes. | Establece nombre en namespace abstracto del kernel; no representa una ruta filesystem. |
| `connect`/direccionamiento | Resuelve endpoint por pathname; pathname y permisos pueden determinar éxito/error. | Localiza por bytes de dirección abstracta; no ejecutar resolución de pathname filesystem. |
| Lifecycle | La entrada pathname tiene lifecycle filesystem propio; eliminación de nombre (por ejemplo, unlink) y referencias abiertas al endpoint deben distinguirse. | Sin objeto filesystem correspondiente; `unix(7)` documenta que desaparece al cerrar todas las referencias abiertas. |
| Cruce posible | S08 endpoint; posible relación S01 por selección/resolución y S04 sólo si una operación/mutación filesystem real cae dentro de su doctrina. No adjudicado. | S08 endpoint; no asignar S04 por el mero hecho de que `sun_path` contenga bytes. |

Niveles que la futura adjudicación debe mantener separados:

1. endpoint lógico AF_UNIX;
2. dirección pathname o abstract que lo identifica;
3. entrada/inode pathname del filesystem, si existe;
4. mutación filesystem concreta que crea, cambia o elimina esa entrada.

La pregunta S04 queda abierta: ¿el `bind` pathname, por el objeto socket que
establece en el namespace filesystem, satisface una relación S04, o se reconoce
S08 y se registra un cruce sólo donde exista mutación filesystem conforme a
S04? La respuesta requiere aplicar explícitamente la doctrina S04; este
checkpoint no la decide. El abstract namespace no tiene pathname/entrada
filesystem por analogía.

## 5. Ancillary data y cruces

### Payload — S02

Para `sendto`, `recvfrom`, `sendmsg`, `recvmsg`, `sendmmsg` y `recvmmsg`,
preparar dos dimensiones independientes: transporte AF_UNIX (candidatura S08)
y transferencia efectiva de payload (posible S02 bajo strict Payload I/O).
Los iovec/carga, cantidad de bytes efectivamente enviados/recibidos, retorno
parcial, truncamiento y error determinan qué ocurrió; invocation por sí sola
no equivale a payload transferido.

### `SCM_RIGHTS` — S09

`SCM_RIGHTS` en cmsg transporta descriptores mediante `sendmsg`/`recvmsg`
(potencialmente las variantes mmsg). Separar:

1. AF_UNIX como canal/transport;
2. cmsg `SCM_RIGHTS` como transferencia de capacidad FD;
3. identidad y uso posterior de cada descriptor recibido.

La segunda y tercera dimensión corresponden a revisión S09 separada. No se
adjudica S09 en esta preparación. Un mensaje sin `SCM_RIGHTS` no se clasifica
como capability passing por usar `sendmsg`; los bytes de un FD tampoco son un
descriptor pasado.

### `SCM_CREDENTIALS`, `SO_PASSCRED`, `SO_PEERCRED`

Las credenciales son metadatos/identidad de peer, no `SCM_RIGHTS` ni payload.
`unix(7)` documenta `SO_PASSCRED` para recepción de `SCM_CREDENTIALS` y
`SO_PEERCRED` para ciertos sockets conectados/socketpair. Registrar actor,
momento, fuente/validez de las credenciales y mecanismo. Es un eje para
analizar autenticación/identificación y posible S10; credenciales no adjudican
S10 automáticamente y esta preparación no adjudica S09.

Otros cmsg (incluido `SCM_SECURITY`) deben quedar particionados por
`cmsg_level`, `cmsg_type`, socket state y soporte; no inventar relación de
superficie. `cmsg(3)` describe que ancillary data es distinta del payload.

## 6. Cruces de superficies que quedan separados

| Superficie | Cruce que debe resolver la adjudicación futura | Lo que esta preparación no decide |
|---|---|---|
| S01 | Resolución/selección del pathname para `bind`, `connect`, y consultas de nombre. | No convierte endpoint AF_UNIX en adjudicación completa S01 ni aplica S01 a abstract names. |
| S02 | Payload efectivamente transferido en operaciones de datos AF_UNIX. | No duplica strict Payload I/O ni cuenta control messages como payload. |
| S03 | FDs creados/aceptados/recibidos, `SOCK_CLOEXEC`, `SOCK_NONBLOCK`, `close`/`dup`, herencia. | No hace S08 equivalente a higiene/lifecycle FD; `shutdown` no es `close`. |
| S04 | Entrada socket pathname, permisos/propiedad y mutaciones filesystem concretas, incluida eventual retirada del pathname. | No adjudica `bind` automáticamente a S04 ni extiende S04 al abstract namespace. |
| S07 | Partición de familia ya revisada: AF_INET/AF_INET6 como IP; AF_UNIX queda en frontera local. | El YES condicional S07 del checkpoint 026 no decide estas relaciones S08. No se reabre ni amplía S07. |
| S09 | `SCM_RIGHTS` y descriptor/capacidad transferida; identidad/uso posterior. | No adjudica S09 por `sendmsg`/`recvmsg` ni por AF_UNIX. |
| S10 | IPC/coordinación local; canales, sincronización/semántica de actores, según doctrina propia. | AF_UNIX y `socketpair` no se convierten automáticamente en S10. |

## 7. Pistas adicionales sin promover

| Mecanismo | Clasificación de preparación | Límite |
|---|---|---|
| `unlink`/operaciones de nombre y metadata sobre socket pathname | Pista relevante S04/S01 para lifecycle pathname. | Revisar sólo mutaciones/resolución realmente justificadas; no añadir como candidatura S08 por ser syscalls filesystem. |
| `umask`, permisos, `chmod`/`chown` | Pistas de política/metadata del socket pathname; `umask` no afecta abstract namespace según `unix(7)`. | Mantener doctrina S04 y no duplicar como membresía S08. |
| `read`/`write`/`readv`/`writev` sobre FD socket | Ruta posible de payload AF_UNIX. | La syscall genérica no prueba identidad AF_UNIX; requiere FD/endpoint y payload efectivo. No promover. |
| `poll`/`select`/`epoll*` | Pista de readiness/estado de canal local. | Esperar readiness no equivale a transportar payload ni a establecer endpoint; no promover. |
| `io_uring` y SQE de socket | Ruta alternativa de ejecución para operaciones socket. | Mantener separada la superficie/interfaz io_uring y analizar operación/endpoint; no adjudicar por opcode no documentado. |
| `SCM_RIGHTS` | Pista fuerte de transferencia de capacidad por canal AF_UNIX. | Revisar bajo S09; no es una syscall ni membresía S08 en sí misma. |
| `SCM_CREDENTIALS`, `SO_PEERCRED`, `SO_PASSCRED` | Pista de identidad/autenticación de peer y potencial cruce S10. | Semántica y actor deben evaluarse; no adjudicar S10 automáticamente. |
| `socketcall` (102) | Fuera del syscall table nativo x86_64 target-bound. | No importar una ABI/arquitectura distinta. |
| Tipos de sockets de otras familias (incluido AF_TIPC) | Fuera de la doctrina AF_UNIX S08 o requiere nueva evidencia/decisión versionada. | No expandir S08 desde similitud funcional. |

Ninguna pista se promueve ni se agrega al manifiesto/ledger.

## 8. Preguntas para adjudicación humana posterior

1. ¿Cada operación genérica de socket se relaciona con S08 sólo cuando el
   endpoint/domain efectivo es AF_UNIX/AF_LOCAL, y qué subcasos de tipo/
   protocolo se admiten?
2. ¿`socket` pertenece por creación AF_UNIX aunque todavía no tenga endpoint
   con nombre, distinguiendo `SOCK_STREAM`, `SOCK_DGRAM`, `SOCK_SEQPACKET` y
   protocol?
3. ¿Qué diferencia explícita se adopta entre pathname, abstract, autobind y
   unnamed endpoints?
4. ¿`bind` a pathname cruza S04 por establecer una entrada tipo socket o sólo
   cuando se demuestra una mutación filesystem conforme a S04? ¿Qué operaciones
   de retirada/metadata cuentan?
5. ¿La resolución de pathname en `connect`/`bind`/consultas genera una relación
   S01 acotada sin absorber toda la doctrina de resolución?
6. ¿Cómo se cierra el lifecycle de endpoint pathname frente a referencias FD,
   y el lifecycle abstract cuando se cierran todas las referencias?
7. ¿`listen`, `accept`/`accept4`, `getsockname`, `getpeername` y `shutdown`
   tienen pertenencia condicionada por type/state/address, separada de S03?
8. ¿`sendto`/`recvfrom`/mmsg se incluyen para cada tipo AF_UNIX soportado,
   incluyendo datagram, connected/unconnected y errores/retornos parciales?
9. ¿Se acepta S08 para `sendmsg`/`recvmsg` por transporte AF_UNIX aunque el
   contenido sea sólo ancillary, sólo payload o ambos? ¿Cómo se representa
   control buffer truncado?
10. ¿`SCM_RIGHTS` queda exclusivamente como cruce S09 para transferencia
    efectiva; qué evidencia delimita FD recibido/instalado y uso posterior?
11. ¿`SCM_CREDENTIALS`/`SO_PASSCRED`/`SO_PEERCRED` representan identidad y
    posible S10 bajo condiciones específicas, sin inferir S09/S10 por nombre?
12. ¿Qué opciones exactas `setsockopt`/`getsockopt` se admiten bajo S08 por
    `level`/`optname`, type y estado, especialmente opciones específicas Linux?
13. ¿`socketpair` AF_UNIX entra en S08 por crear el par local unnamed e
    implícitamente conectado? ¿Cómo se conserva lifecycle de ambos FDs y se
    excluye AF_TIPC?
14. ¿Qué evidencia de headers/paquete target se requiere para dar por
    soportados flags, cmsg, mmsg y opciones, sin confundir documentación
    upstream con target-bound support?

## 9. Fuentes y límites

- **Syscall table target-bound:** manifiesto en HEAD verificado; ABI x86_64,
  385 entradas, SHA-256
  `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
  Autoridad para número/nombre/entrada ABI y estado estático; no demuestra
  efecto runtime, uso por workload ni adjudicación de superficie.
- **Man-pages Linux 6.19**, snapshot identificado en 025 como obtenido
  2026-09-09; referencia semántica Linux consultada para esta preparación:
  [`socket(2)`](https://man7.org/linux/man-pages/man2/socket.2.html),
  [`socketpair(2)`](https://man7.org/linux/man-pages/man2/socketpair.2.html),
  [`bind(2)`](https://man7.org/linux/man-pages/man2/bind.2.html),
  [`connect(2)`](https://man7.org/linux/man-pages/man2/connect.2.html),
  [`listen(2)`](https://man7.org/linux/man-pages/man2/listen.2.html),
  [`accept(2)`](https://man7.org/linux/man-pages/man2/accept.2.html),
  [`send(2)`](https://man7.org/linux/man-pages/man2/send.2.html),
  [`recv(2)`](https://man7.org/linux/man-pages/man2/recv.2.html),
  [`sendmmsg(2)`](https://man7.org/linux/man-pages/man2/sendmmsg.2.html),
  [`recvmmsg(2)`](https://man7.org/linux/man-pages/man2/recvmmsg.2.html),
  [`getsockname(2)`](https://man7.org/linux/man-pages/man2/getsockname.2.html),
  [`getpeername(2)`](https://man7.org/linux/man-pages/man2/getpeername.2.html),
  [`shutdown(2)`](https://man7.org/linux/man-pages/man2/shutdown.2.html),
  [`setsockopt(2)`](https://man7.org/linux/man-pages/man2/setsockopt.2.html),
  [`getsockopt(2)`](https://man7.org/linux/man-pages/man2/getsockopt.2.html),
  [`unix(7)`](https://man7.org/linux/man-pages/man7/unix.7.html),
  [`socket(7)`](https://man7.org/linux/man-pages/man7/socket.7.html) y
  [`cmsg(3)`](https://man7.org/linux/man-pages/man3/cmsg.3.html).
  Estas páginas documentan interfaz Linux, no prueban soporte de toda
  combinación en la VM/workload target ni reemplazan headers empaquetados.
- **UAPI upstream Linux v7.0**, previamente identificada en 025:
  [`include/uapi/linux/un.h`](https://github.com/torvalds/linux/blob/v7.0/include/uapi/linux/un.h),
  [`include/uapi/linux/socket.h`](https://github.com/torvalds/linux/blob/v7.0/include/uapi/linux/socket.h).
  Referencia de símbolos/estructuras; no es prueba de identidad exacta del
  paquete target ni de configuración/habilitación.
- **Fuentes internas:** checkpoints 025 y 026 para frontera S07/S08, lista
  candidata y doctrina de superficies cruzadas; el manifiesto conserva S08
  como referencias `UNREVIEWED`, no como decisiones.

No se consultó ni modificó la VM. La evidencia documental no demuestra
reachability, ejecución, enforcement, endpoints efectivos o flujo de datos.

## 10. Estado e invariantes

- Conjunto preparado: **18 syscalls** (17 operaciones socket compartidas con
  la revisión S07 más `socketpair`), todas sin adjudicación S08.
- Las candidaturas S08 previas del manifiesto permanecen en estado
  `UNREVIEWED`; ninguna se promueve ni materializa.
- S07 conserva su revisión IP del checkpoint 026; no se cambia ni se amplía.
- S01/S02/S03/S04/S09/S10 no se adjudican ni se modifican.
- Pistas adicionales promovidas: **0**.
- Manifiesto y ledger permanecen byte-idénticos a HEAD; no se modifica ninguna
  disposición ni membresía canónica.
- Disposiciones: **385/385 UNKNOWN**, **0** disposiciones finales;
  `inventory.frozen=false`; A-PRE-0 `NOT READY`; A-PRE-1 `NOT AUTHORIZED /
  NOT EXECUTED`.
- Se crea este checkpoint y se actualiza el índice. Sin stage ni commit; los
  cambios preexistentes ajenos permanecen intactos.
- No se ejecutaron TALOS, FastAPI, probes, tests, pytest, benchmarks,
  workloads, A-PRE-1 ni parsers/validadores dinámicos. No se tocaron VM,
  runtime, overlay, lock, corpus, modelos, bases de datos, E5/Qwen, Playwright
  ni código de producto.
- No se avanza a adjudicación S08 ni a S09.
