# Preparación documental — lote 07, S07 IP/networking

Fecha: 2026-10-01

## 1. Autoridad, identidad y alcance

Preparación para decisión humana posterior; no adjudica, crea ni materializa
relaciones S07. Punto de partida verificado:

```text
HEAD   f81134fc2293916210d53c8065f3a0049e52b0b4
TREE   c322e78980ac72f24c66b1396014faefaac074a9
PARENT b17dd9c4dab098512aa6c148e7d36c613da41c28
```

El worktree ya contenía cambios ajenos; se preservan intactos. El checkpoint
024 estaba presente como archivo no rastreado del estado de preparación S06;
esta preparación no lo modifica.

El manifiesto target-bound registra **17 candidaturas S07** y sus números bajo
ABI x86_64; todas las relaciones S07 continúan sin adjudicar. El checkpoint
S06, el manifiesto y el ledger se usan como autoridad local de estado; el
manifiesto y ledger no se editan aquí.

Doctrina provisional de trabajo:

> S07 es la superficie de comunicación mediante sockets de red/IP y sus
> operaciones de establecimiento, configuración, conexión, aceptación,
> direccionamiento, transporte y consulta de estado, distinguiendo familia,
> tipo, protocolo, endpoint y operación.

La pertenencia no se infiere del descriptor ni del nombre `socket*`. Toda
variante debe conservar dominio/familia, tipo, protocolo, endpoint/dirección,
connected/unconnected, transporte, flags, resultado y eventual control data.
Las relaciones S07, S08, S09, S02, S03 y S10 pueden coexistir; un cruce no es
adjudicación.

## 2. Frontera de familia y objetos

| Familia / objeto | Tratamiento propuesto para la revisión | Límite |
|---|---|---|
| `AF_INET` | IPv4; distinguir stream/datagram/raw y protocolo concreto, direcciones, interfaz/puerto y peer. | Mantener las variantes dependientes de address, network namespace y opción/protocolo; no asumir que todo socket IPv4 es TCP. |
| `AF_INET6` | IPv6; distinguir stream/datagram/raw, protocolo, address/port, scope/interface y opciones IPv6. | No asumir equivalencia completa con IPv4 ni combinar ambas familias sin conservar el campo family. |
| Otras familias/protocolos que transporten IP | Revisar sólo con evidencia explícita de endpoint IP y semántica de red para el target. | La definición actual de S07 admite expresamente `AF_INET`/`AF_INET6`; otra familia requiere decisión humana y eventual cambio versionado de alcance. `AF_PACKET` ofrece sockets de capa enlace y no se promueve aquí como S07/IP. |
| `AF_UNIX` / `AF_LOCAL` | Comunicación local; pathname, abstract o unnamed endpoint según operación. | No adjudicar a S07 por usar la misma syscall; pertenece al cruce separado S08. Sus pathname pueden interactuar con S01/S04 sin convertir el canal en IP. |
| `socketpair` | Dos sockets conectados sin nombre desde una sola llamada; la documentación de Linux describe `AF_UNIX` y `AF_TIPC`, no `AF_INET`/`AF_INET6`. | El manifiesto lo lista como candidato S08, no S07. Se analiza por separado porque la directiva lo incluye, pero no se añade a S07 ni se decide S08/S10 aquí. |

`SOCK_STREAM`, `SOCK_DGRAM`, `SOCK_SEQPACKET` y `SOCK_RAW` tienen semánticas
distintas; no todos los tipos se implementan para todas las familias. La
dirección puede ser `sockaddr_in`/`sockaddr_in6` o una forma no IP, y el
resultado debe ligarse al tipo/dominio real. Los nombres `AF_LOCAL` y
`AF_UNIX` son sinónimos en Linux.

## 3. Candidaturas S07 existentes — pendientes, no adjudicadas

Las 17 filas siguientes ya contienen `S07` en `candidate_surface_ids`. La
columna de decisión se deja **PENDING HUMAN ADJUDICATION** en todos los casos.
Los números y nombres son los del syscall table target-bound; la semántica
descrita prepara preguntas, no aceptación.

| NR / syscall | Semántica relevante | Variantes y condiciones a preservar | Cruces a revisar, no adjudicados | Pregunta para decisión humana |
|---|---|---|---|---|
| 41 `socket` | Crea endpoint y retorna FD. | `domain/family`, `type` base y flags, `protocol`; `AF_INET`/`AF_INET6` frente a `AF_UNIX`; `SOCK_STREAM`, `SOCK_DGRAM`, `SOCK_SEQPACKET`, `SOCK_RAW`; `SOCK_NONBLOCK`, `SOCK_CLOEXEC`; éxito/errores. | S08 por AF_UNIX; S03 por FD y close-on-exec; S10 por socket local/compartido; S11 por herencia. | ¿Qué familias/tipos/protocolos constituyen S07? ¿Se limita a AF_INET/6 y qué se hace con raw o protocolos IP distintos de TCP/UDP? |
| 42 `connect` | Asocia un socket con peer/destino; puede iniciar conexión o configurar peer según familia/tipo. | FD/socket state, `sockaddr`/family/length, peer, stream/datagram, blocking/nonblocking, error/resultado; AF_UNIX pathname/abstract separado. | S08 para endpoint local; S03 FD; S10 coordinación local; S11 por proceso. | ¿Qué destino/protocolo y resultado hacen de `connect` una comunicación S07 y cómo se separa de S08? |
| 49 `bind` | Asigna dirección local/nombre al socket. | Family/address/length; IP local address, port, wildcard, scope/interface; frente a AF_UNIX pathname/abstract y permisos/namespace; éxito/errores. | S08/S01/S04 para pathname local; S03 por FD; S10 si local IPC. | ¿Se admite sólo direccionamiento IP para S07 y se dejan pathname/abstract exclusivamente para revisión S08? |
| 50 `listen` | Marca socket orientado a conexión para aceptar conexiones entrantes. | Family/tipo, previamente bound o implicit bind, backlog, address efectiva y resultado; stream frente a datagram (no asumir que toda combinación habilita listener). | S08 para listener AF_UNIX; S03 FD; S10 para listener local. | ¿Qué familia/tipo y estado previo convierten `listen` en operación S07? |
| 43 `accept` | Acepta conexión pendiente y devuelve un nuevo FD conectado; el listener permanece. | Family del listener/peer, dirección retornada y su longitud value-result, estado blocking/nonblocking heredado, error y FD retornado. | S08 si listener local; S03 por descriptor nuevo, sin decisión automática. | ¿Se limita a conexiones IP aceptadas y se conserva separada la creación/lifecycle del FD? |
| 288 `accept4` | Acepta como `accept` con flags de FD/estado atómicos. | `SOCK_CLOEXEC`, `SOCK_NONBLOCK`, family, listener, peer/address y descriptor retornado. | S08; S03 por flags FD; S11 por herencia al exec. | ¿Misma condición S07 de `accept`, registrando flags como dimensión S03 independiente? |
| 51 `getsockname` | Consulta la dirección local enlazada/efectiva del socket. | Family y sockaddr devuelta, longitud value-result, direcciones wildcard/asignadas dinámicamente, estado previo y errores. | S08 para direcciones AF_UNIX; S03 sólo selector FD. | ¿La consulta del endpoint local pertenece a S07 sólo para sockets IP, y qué significa resultado wildcard/implicit bind? |
| 52 `getpeername` | Consulta peer asociado a socket conectado. | Family/peer sockaddr, longitud, connected state, stream/datagram y error; diferenciar ausencia de peer. | S08 para peer local; S03 FD. | ¿Se incluye como inspección de estado de peer IP, condicionada a family y conexión efectiva? |
| 48 `shutdown` | Deshabilita envío y/o recepción en una conexión/socket; no cierra por sí solo el descriptor. | `SHUT_RD`, `SHUT_WR`, `SHUT_RDWR`; family, dirección afectada, estado/conexión y resultado. | S08 para socket local; S03 para close separado; S11 por teardown de proceso. | ¿Shutdown de una comunicación IP es S07, y cómo se diferencia de `close` o del teardown final? |
| 44 `sendto` | Envía payload por socket, opcionalmente indicando destino. | Family, type/protocol, connected/unconnected, peer/destination sockaddr, buffer/length/flags, blocking, resultado parcial/error. | S02 strict Payload I/O; S08 por AF_UNIX; S09 sólo si la variante admite/control data no debe inferirse aquí. | ¿Se registra simultáneamente S07 para comunicación IP y S02 para payload efectivo, por family y operación? |
| 45 `recvfrom` | Recibe payload y opcionalmente retorna dirección de origen. | Family/type, buffer/length/flags, source sockaddr/length value-result, blocking, retorno/partial/error; connected vs unconnected. | S02 payload recibido; S08 para AF_UNIX; S10 si socket local. | ¿Qué receives IP pertenecen a S07 junto con la dimensión de payload S02? |
| 46 `sendmsg` | Envía uno o más iovec de payload y puede incluir ancillary/control data. | Family/type, destination, iovec, flags, `msg_control`/control length, retorno parcial/error; payload, control y ancillary deben separarse. | S02 payload; S08 AF_UNIX; S09 para `SCM_RIGHTS`; posible credenciales/IPC S10 según decisión humana. | ¿Qué subcasos de payload IP, control messages y cada cmsg se asignan a S07/S02/S09/S10, sin tratar toda llamada como equivalente? |
| 47 `recvmsg` | Recibe payload, dirección y ancillary/control data. | iovec, flags de input/output, `msg_name`, `msg_control`, truncamiento `MSG_TRUNC`/`MSG_CTRUNC`, resultado, cmsg concreto y family. | S02 payload; S08; S09 para FD recibido por `SCM_RIGHTS`; S10 para credenciales/control si corresponde. | ¿Qué variante IP de payload es S07 y cómo se particionan `SCM_RIGHTS`, `SCM_CREDENTIALS` y otros cmsg? |
| 307 `sendmmsg` | Envía un vector de mensajes por socket y retorna número de mensajes procesados. | `mmsghdr` vector, `vlen`, flags, retorno parcial, family/type y destination por mensaje; payload frente ancillary. | S02 por payload de cada mensaje; S08/S09 según family/cmsg; S10 posible. | ¿Se modela como comunicación IP por mensaje y cómo se interpreta envío parcial/ancillary? |
| 299 `recvmmsg` | Recibe múltiples mensajes, con timeout opcional y retorno de cantidad completada. | Vector, `vlen`, flags, timeout (modificación/semántica de ABI), source por mensaje, truncamiento, blocking/nonblocking y retorno parcial. | S02 payload; S08/S09 según family/control data; S10 posible. | ¿Qué resultados de recepción IP, timeout y control data forman la relación S07, sin adjudicar la syscall completa? |
| 54 `setsockopt` | Configura opción sobre socket. | `level` (p. ej. `SOL_SOCKET`, `IPPROTO_IP`, `IPPROTO_IPV6`, protocolo de transporte), `optname`, valor/longitud, family/type y resultado. Distinguir opción IP/transport de opciones comunes y AF_UNIX. | S08 para opciones locales; S03 FD; S10 por opción coordinativa; S11 estado por proceso/socket. | ¿Qué niveles/opciones cambian comportamiento de networking IP suficiente para S07 y cuáles son configuración común/otra superficie? |
| 55 `getsockopt` | Consulta opción/estado de socket. | `level`, `optname`, buffer de valor y longitud value-result, family/type/estado, resultado/error. Separar consulta de configuración mutacional. | S08 para opciones AF_UNIX; S03 FD; S10 según opción. | ¿Qué consultas de estado IP pertenecen a S07 y qué opciones quedan fuera por ser genéricas o específicas de otra familia? |

En todas las filas, conservar resultado exitoso frente a error y no asumir
alcanzabilidad por presencia en la syscall table. Address/endpoint incluye
family, bytes y longitud; `sockaddr` pathname no es IP address. Para datagrams,
`connect` puede fijar peer/default destination sin convertir el transporte en
stream; para streams, conexión y aceptación son etapas distintas.

## 4. `socketpair` — revisión separada requerida, no añadir a S07

| NR / syscall | Estado canónico actual | Evidencia y cuestión |
|---|---|---|
| 53 `socketpair` | Candidato S08 solamente; no está en `candidate_surface_ids` de S07. Disposición global permanece `UNKNOWN`. | `socketpair(2)` describe un par conectado/unnamed en el dominio dado; Linux documenta soporte `AF_UNIX` y `AF_TIPC`, no `AF_INET`/`AF_INET6`. `AF_UNIX` cruza S08; el uso como IPC puede cruzar S10; devuelve dos FDs y puede cruzar S03, sin decisión automática. ¿Debe mantenerse fuera de S07 bajo el criterio IP estricto? ¿Qué cruce S08/S10 se decidirá por separado y qué condiciones de dominio/type/protocol se conservan? |

Esta preparación no emite un `NO` canónico ni adjudica S08/S10/S03. Dado el
scope IP de S07, socketpair se presenta para resolver explícitamente su
frontera, pero no se promueve a candidato S07.

## 5. Particiones obligatorias de payload, ancillary y superficies

### S07 frente a S02 — payload

`sendto`, `recvfrom`, `sendmsg`, `recvmsg`, `sendmmsg` y `recvmmsg` pueden
transferir payload sobre socket IP. S07 describe canal/protocolo/peer y
operación de comunicación; S02 describe transferencia efectiva de payload.
Una adjudicación posterior puede aceptar ambas relaciones para la misma
variante, sin que una sustituya a la otra. El hecho de que una syscall sea de
socket no decide por sí solo S02; el hecho de transferir bytes no decide por sí
solo family S07.

### S07 frente a S09 — control messages

En `sendmsg`/`recvmsg` y las variantes multi-message, conservar explícitamente
al menos:

| Clase de contenido | Separación a mantener | Pregunta para la adjudicación |
|---|---|---|
| Payload de red (iovec) | Datos del protocolo de socket; no mezclar con `msg_control`. | ¿La variante IP corresponde a S07 y transferencia efectiva a S02? |
| `SCM_RIGHTS` | Passing de capacidades FD por ancillary data; dimensión conceptual S09 cuando aplique. | ¿S09 se determina por cmsg efectivo y FD pasado/recibido, independientemente de S07/S08? |
| `SCM_CREDENTIALS` | Datos de credenciales/proceso, no payload ordinario ni paso de FD. | ¿Se clasifica como dimensión S10/credenciales u otra, y qué family permite ese cmsg? |
| Otros cmsg | Interpretación depende de family/protocol/level y cmsg type. | ¿Qué tipos requieren una pista aparte en vez de una regla global `sendmsg`/`recvmsg`? |

No asumir que SCM_RIGHTS está disponible para IP sockets igual que para
AF_UNIX; validar family/protocolo y ABI mediante evidencia antes de cualquier
decisión. El checkpoint prepara esa cuestión sin resolverla.

### S07 frente a S03/S08/S10/S11

- S03: `socket`/`accept*` retornan FD y `accept4`/`SOCK_CLOEXEC` pueden
  afectar hygiene; descriptor creado no adjudica S03 automáticamente. `close`
  es lifecycle FD, separado de `shutdown`.
- S08: las syscalls comunes de socket se usan también con AF_UNIX/AF_LOCAL;
  distinguir pathname, abstract y unnamed addresses. No asignar AF_UNIX a
  S07 por nombre de syscall.
- S10: socket local, socketpair o coordinación entre procesos pueden cruzar
  IPC; el mero tipo socket o `MAP_SHARED` no decide IPC.
- S11: herencia a `fork`/`exec`, cambio de proceso y estados por proceso son
  cruces, no la comunicación IP misma.
- S09: transferir un descriptor requiere evidencia de `SCM_RIGHTS` u otra
  ruta de paso; `sendmsg` por sí sola no demuestra capability passing.

## 6. Pistas adicionales fuera de la lista inicial

No se encontraron filas sin candidato con `potential_surface_refs` a S07 en
el crosswalk actual. Las siguientes son rutas/temas para decidir si requieren
una pista documental posterior; no se agregan a `candidate_surface_ids` ni se
adjudican:

| Syscall / mecanismo | Clasificación de pista | Razón y límite |
|---|---|---|
| `socketpair` (53) | **Pista relevante; estado canónico S08 solamente.** | Revisión explícita independiente; Linux documenta AF_UNIX/AF_TIPC, sin evidencia de familia IP para S07. No añadir a S07. |
| `sendfile` (40), `splice` (275) | **Pistas dudosas de ruta de payload.** | Algunas rutas pueden usar un socket FD como destino/origen; semántica central es transferencia entre FD/file/pipe y cruza S02. Requiere evidencia de endpoint IP y decisión específica; no inferir S07 por FD. |
| `io_uring` (425) y operaciones de SQE de socket | **Ruta alternativa relevante; fuera de estas candidaturas.** | El syscall de entrada puede someter operaciones connect/accept/send/recv por una interfaz async; `io_uring` es su propia superficie/candidatura S12. Revisar el cruce S12/S07 sin duplicar una membresía global a partir de opcode. |
| `read`/`write` genéricos sobre socket FD | **Pista dudosa.** | Pueden transferir bytes si FD resulta ser socket; son syscalls genéricas y S02 ya delimita payload. Exigir identidad del objeto/peer y no promover por posibilidad abstracta. |
| `poll`, `select`, `epoll*` y readiness | **Fuera de S07 provisional / pista de consulta de readiness.** | Espera/consulta de disponibilidad no equivale a establecer endpoint ni transferir payload; no se adjudica networking por observar un FD socket. |
| `socketcall` (102) | **Fuera del inventario x86_64 target-bound.** | No aparece como syscall `socketcall` en el registro de 385 syscalls nativas del target. No importar ABI de otra arquitectura ni añadir la syscall al alcance. |

## 7. Preguntas concretas para la decisión humana

1. ¿S07 se limita a `AF_INET`/`AF_INET6` como indica la definición actual, y
   cómo se tratan protocolos IP raw, SCTP/UDPLite u otras variantes
   target-supported?
2. Para cada syscall común con S08, ¿se adjudica sólo según family/domain
   efectiva, además de tipo, protocolo, endpoint, flags y resultado?
3. ¿`socketpair(53)` queda explícitamente fuera de S07 por falta de familia
   IP, conservando sólo su candidatura S08 pendiente y posibles cruces S10/S03?
4. ¿`setsockopt`/`getsockopt` se limitan a niveles/opciones IP y transporte
   seleccionados, o incluyen opciones comunes de socket cuando el objeto es
   AF_INET/AF_INET6?
5. Para `send*`/`recv*`, ¿se adjudica S07 a comunicación por socket IP en
   paralelo a S02 sólo para payload efectivamente transferido? ¿Cómo se
   particionan retorno parcial, `MSG_TRUNC`, `MSG_CTRUNC`, timeout y errores?
6. ¿Qué family/transport permite cada cmsg? ¿`SCM_RIGHTS` se reserva a S09
   cuando haya transferencia FD efectiva, mientras `SCM_CREDENTIALS` queda
   como dimensión distinta sin adjudicar por analogía?
7. ¿`shutdown` es S07 sólo para shutdown de comunicación de socket y siempre
   distinto del `close`/close_range S03?
8. ¿Los flags `SOCK_CLOEXEC`, `SOCK_NONBLOCK`, `accept4` y estado heredado de
   FD son condiciones S03 separadas, no membresía S07 por sí mismas?
9. ¿Las rutas `sendfile`/`splice`, genéricas read/write y SQE `io_uring`
   necesitan preparación aparte como referencias S07, o permanecen fuera
   hasta encontrar una ruta de endpoint del workload?
10. ¿Qué límites/versiones del ABI target, protocolos, opciones y family se
    requieren para cerrar cada relación sin introducir combinaciones
    artificiales?

## 8. Fuentes y límites

- **Autoridad target-bound local:** `A_PRE_0_SURFACE_MANIFEST.json` en el
  commit identificado arriba para número, nombre, ABI, candidaturas existentes,
  definiciones S07/S08/S09/S10/S11, estado y hash de la syscall table. La tabla
  tiene 385 filas nativas x86_64; su SHA-256 registrado es
  `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
- **Man-pages 6.19**, snapshot publicado 2026-09-09, consultado como
  referencia general de semántica Linux:
  [`socket(2)`](https://man7.org/linux/man-pages/man2/socket.2.html),
  [`socketpair(2)`](https://man7.org/linux/man-pages/man2/socketpair.2.html),
  [`sendmsg(2)`](https://man7.org/linux/man-pages/man2/sendmsg.2.html),
  [`socket(7)`](https://man7.org/linux/man-pages/man7/socket.7.html),
  [`ip(7)`](https://man7.org/linux/man-pages/man7/ip.7.html),
  [`ipv6(7)`](https://man7.org/linux/man-pages/man7/ipv6.7.html) y
  [`unix(7)`](https://man7.org/linux/man-pages/man7/unix.7.html). Las páginas
  `send(2)`, `recv(2)`, `accept(2)`, `bind(2)`, `connect(2)`, `listen(2)`,
  `shutdown(2)`, `getsockname(2)`, `getpeername(2)`, `socket(7)` y
  `cmsg(3)` son fuentes específicas a contrastar por variante durante la
  futura adjudicación.
- UAPI upstream versionado Linux v7.0, como fuentes para verificar símbolos,
  valores y estructuras:
  [`include/uapi/linux/socket.h`](https://github.com/torvalds/linux/blob/v7.0/include/uapi/linux/socket.h),
  [`include/uapi/linux/in.h`](https://github.com/torvalds/linux/blob/v7.0/include/uapi/linux/in.h),
  [`include/uapi/linux/in6.h`](https://github.com/torvalds/linux/blob/v7.0/include/uapi/linux/in6.h)
  y [`include/uapi/linux/un.h`](https://github.com/torvalds/linux/blob/v7.0/include/uapi/linux/un.h).
  Upstream v7.0 no sustituye los headers empaquetados del Ubuntu target ni
  demuestra que una familia/protocolo esté habilitado en la VM.
- Checkpoint 017 describe rutas FD/sockets y advierte que crear/retornar un FD
  no basta para S03. Checkpoints 016, 018, 019 y 024 delimitan respectivamente
  S02, S03, cruces y estado de preparación previa; no adjudican S07.

Las fuentes de sistema de llamadas y man-pages son evidencia documental, no
evidencia de reachability, uso por TALOS, enforcement, resultado de red ni
apertura de endpoints en el entorno target. No se consultó ni modificó VM.

## 9. Estado de preparación e invariantes

- Candidaturas S07 preexistentes presentadas: **17**, todas pendientes de
  decisión humana.
- `socketpair(53)` revisada como contraste, pero se conserva como candidata
  S08 preexistente; membresías candidatas nuevas: **0**.
- Pistas adicionales promovidas: **0**; no se agregan ni eliminan filas.
- S08 y S09 permanecen sin adjudicación por esta preparación.
- Disposiciones generales: **385/385 UNKNOWN**; disposiciones finales: **0**.
- `inventory.frozen=false`; A-PRE-0 `NOT READY`; A-PRE-1
  `NOT AUTHORIZED / NOT EXECUTED`.
- Manifiesto y ledger no se modifican; no se materializa ninguna membresía.
- Se crea este checkpoint y se actualiza el índice; no se hace stage ni
  commit.
- No se ejecutaron TALOS, FastAPI, probes, tests, pytest, suites, benchmarks,
  workloads, parsers/validadores dinámicos ni A-PRE-1. No se tocaron VM,
  runtime, overlay, `requirements.lock`, corpus, modelos o bases de datos.
- No se avanza a adjudicación S07 ni a S08.
