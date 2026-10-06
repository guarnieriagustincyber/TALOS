# Adjudicación documental humana — lote 08, S08 AF_UNIX

Fecha: 2026-10-01

## 1. Identidad del punto de partida

Repositorio: `/media/agustin/Laboratorio/study-engie`

```text
HEAD   f81134fc2293916210d53c8065f3a0049e52b0b4
TREE   c322e78980ac72f24c66b1396014faefaac074a9
PARENT b17dd9c4dab098512aa6c148e7d36c613da41c28
```

El worktree ya contenía cambios previos ajenos; se preservan intactos.
Checkpoint inmediato [027-preparacion-lote-08-s08.md](./027-preparacion-lote-08-s08.md)
y adjudicación IP [026-adjudicacion-documental-lote-07-s07.md](./026-adjudicacion-documental-lote-07-s07.md)
se leyeron como documentación no canónica del estado de trabajo.
El checkpoint 027 contiene exactamente las 18 operaciones solicitadas; no hubo
discrepancia de lista.

La autoridad de nombres/números es la syscall table nativa x86_64 vinculada al
manifiesto en HEAD: 385 filas; SHA-256 de tabla
`93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
Antes de esta adjudicación, el checkpoint 027, el 026, manifiesto y ledger
coincidían byte por byte con HEAD. SHA-256 iniciales:

```text
026-adjudicacion-documental-lote-07-s07.md
0868160d6425b065242a85f989c5e6a171c7dc98b1053857789aa2eb3f0ebdef
027-preparacion-lote-08-s08.md
bcc40808cbc5a42dbb246c6f57fac55fbbfcf56f3948e688ff98c00ce161d871
A_PRE_0_SURFACE_MANIFEST.json
bc498e058585341b341f8318fb8a2dd869c5737ebd63fd89f0878cef0793e20e
A_PRE_0_QUALIFICATION_LEDGER.json
0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42
```

## 2. Doctrina y forma de la decisión

> **S08 = superficie de comunicación mediante sockets AF_UNIX/AF_LOCAL y sus
> endpoints locales, incluyendo establecimiento, direccionamiento, conexión,
> aceptación, transmisión, consulta y lifecycle de endpoints pathname y
> abstract namespace, distinguiendo payload, control messages y transferencia
> de capacidades.**

Cada decisión de la tabla es una relación de superficie **condicionada** a la
variante AF_UNIX descrita. **YES no significa que todas las invocaciones de la
syscall sean S08**, ni cambia su disposición global. AF_INET/AF_INET6 siguen
siendo la dimensión IP S07 ya documentada en 026; otras familias no se
incorporan a S08 por semejanza.

La doctrina S08 incluye endpoints pathname, abstract y unnamed cuando forman
parte de comunicación/lifecycle AF_UNIX. Un pathname de endpoint y su
resolución/entrada filesystem se mantienen distintos del endpoint lógico. Los
casos no descritos por la condición YES no se promueven por inferencia; su
pertenencia fuera de esa variante requiere su propia decisión si llega a ser
relevante.

## 3. Decisión explícita de las 18 candidaturas

| NR / syscall | Decisión | Familia/tipo y variante que recibe YES | Razón y evidencia | Límites, cruces e incertidumbre residual |
|---|---|---|---|---|
| 41 `socket` | **S08 YES — condicional** | `domain=AF_UNIX`/`AF_LOCAL`; creación de endpoint de tipo AF_UNIX válido, incluidos `SOCK_STREAM`, `SOCK_DGRAM` y `SOCK_SEQPACKET` cuando el protocolo/target admita el par. Puede estar todavía unnamed, sin bind/connect. | `socket(2)` selecciona family/type/protocol y crea el endpoint; `unix(7)` define los tipos de Unix-domain socket. | AF_INET/AF_INET6 quedan en S07; otras familias no se aceptan por analogía. `SOCK_CLOEXEC`/`SOCK_NONBLOCK` son flags, no nueva membresía S03. No se afirma que cada combinación/protocol esté soportado o usado en el target. |
| 42 `connect` | **S08 YES — condicional** | Socket AF_UNIX cuyo destino `sockaddr_un` identifica endpoint pathname o abstract; stream/seqpacket conectan al endpoint, datagram puede asociar peer/destino conforme a su estado. | `connect(2)` interpreta address según family del socket; `unix(7)` documenta direcciones y comunicación AF_UNIX. | Pathname puede requerir resolución/identificación S01; eso no adjudica S01 completa. Un pathname socket y permisos/entrada podrían cruzar S04 sólo bajo su regla propia. Abstract no implica objeto filesystem ni S04. No se adjudican errores como uso efectivo. |
| 43 `accept` | **S08 YES — condicional** | Aceptación de conexión pendiente en listener AF_UNIX orientado a conexión; incluir address/estado del endpoint resultante cuando devuelto. | `accept(2)` obtiene conexión pendiente y un socket conectado nuevo; `unix(7)` especifica AF_UNIX/address retornada. | Condicionada al listener/tipo/estado; descriptor nuevo es cruce S03, no motivo de esa decisión. Pathname/abstract identifica endpoint, pero no adjudica S01/S04 automáticamente. |
| 44 `sendto` | **S08 YES — condicional** | Transporte por socket AF_UNIX; datagram con destino pathname/abstract o comunicación conectada válida, preservando `type`, peer/destination y flags. Stream sólo según conexión/semántica admitida; no asumir destino datagram para stream. | `send(2)` y `unix(7)` describen envío y uso de address en AF_UNIX. | Transporte local S08 es distinto de payload efectivo S02. S02 aplica sólo a bytes de payload realmente transferidos conforme a su doctrina. Pathname es posible cruce S01/S04; no adjudicar por uso del FD solamente. |
| 45 `recvfrom` | **S08 YES — condicional** | Recepción desde socket AF_UNIX; conservar datagram/stream, estado conectado, address origen pathname/abstract/unnamed cuando exista, `addrlen` value-result, flags y resultado. | `recv(2)` y `unix(7)` describen recepción y las address AF_UNIX retornadas. | Payload efectivo se analiza bajo S02, separado del transporte. No inferir un peer/address para todas las variantes. Truncamiento, error y cero bytes no se transforman en transferencia no demostrada. |
| 46 `sendmsg` | **S08 YES — condicional** | Envío mediante endpoint/socket AF_UNIX; incluye transporte aunque `msghdr` contenga iovec, ancillary data o ambos. Particionar destination/name, type, flags y resultado. | `send(2)`, `unix(7)` y `cmsg(3)` describen envío de mensajes y ancillary/control data de socket. | Iovec/payload efectivo puede cruzar S02. `SCM_RIGHTS` se reserva a dimensión S09 si hay paso efectivo de descriptor/capacidad; `SCM_CREDENTIALS` es metadato de credencial, no S09 ni S10 automático. No toda llamada es capability passing. |
| 47 `recvmsg` | **S08 YES — condicional** | Recepción mediante endpoint/socket AF_UNIX; registrar mensaje recibido, `msg_name`, iovec, control buffer, flags y resultado. | `recv(2)`, `unix(7)` y `cmsg(3)` describen recepción de mensajes y separación de ancillary data. | S02 sólo para payload realmente recibido. `SCM_RIGHTS` sólo cruza S09 cuando se reciben/instalan FDs; credenciales quedan separadas. `MSG_CTRUNC`/`MSG_TRUNC` deben reflejar pérdida/truncamiento, no inferir cmsg completo. |
| 48 `shutdown` | **S08 YES — condicional** | `SHUT_RD`, `SHUT_WR` o `SHUT_RDWR` sobre canal/comunicación AF_UNIX. | `shutdown(2)` y `socket(7)` distinguen shutdown direccional de cerrar el socket. | No equivale a `close`, cierre del último descriptor ni lifecycle FD S03. S08 cubre el estado/comunicación del canal; no se adjudica S03. |
| 49 `bind` | **S08 YES — condicional** | Asignación de address AF_UNIX pathname **o** abstract al endpoint. Pathname: address con nombre filesystem. Abstract: byte inicial NUL y bytes cubiertos por longitud, sin pathname filesystem. | `bind(2)` define el establecimiento de dirección y remite reglas AF_UNIX a `unix(7)`; `unix(7)` distingue pathname y abstract. | YES S08 en ambas variantes. Pathname puede relacionarse con S01 por resolución/identificación y con S04 sólo si se acredita la dimensión de entrada/mutación filesystem conforme a S04. No se decide S04 aquí. Abstract no tiene objeto pathname: no inferir S04. |
| 50 `listen` | **S08 YES — condicional** | Socket AF_UNIX orientado a conexión en estado/type compatible, listener pathname o abstract cuando corresponda; backlog y resultado forman variantes. | `listen(2)`, `accept(2)` y `unix(7)` describen listener y conexiones AF_UNIX. | No incluir automáticamente datagram ni cualquier descriptor socket. No adjudicar S03 por el FD. Bind implícito/estado y endpoint real deben preservarse. |
| 51 `getsockname` | **S08 YES — condicional** | Consulta de address local AF_UNIX: pathname, abstract, autobind o unnamed según endpoint/estado y longitud. | `getsockname(2)` retorna la dirección local; `unix(7)` define formas/longitudes de `sockaddr_un`. | Si retorna pathname, posible cruce S01 para identificación; consulta no es por sí misma resolución completa ni mutación S04. La longitud value-result limita los bytes válidamente interpretables. |
| 52 `getpeername` | **S08 YES — condicional** | Consulta del peer AF_UNIX cuando existe asociación/peer según type y state; distinguir address pathname, abstract o unnamed. | `getpeername(2)` consulta peer address y `unix(7)` documenta la estructura AF_UNIX. | Condicionada a peer/state; no presumir conexión o address disponible. Pathname puede informar identidad del endpoint, no adjudicar S01 automáticamente. |
| 53 `socketpair` | **S08 YES — condicional** | `domain=AF_UNIX`/`AF_LOCAL`, type AF_UNIX admitido; creación simultánea de dos sockets conectados y unnamed, sin pathname ni abstract-name binding explícito. Considerar lifecycle de ambos extremos. | `socketpair(2)` especifica que en Linux los dominios soportados son AF_UNIX/AF_LOCAL y AF_TIPC; `unix(7)` dice que los dos extremos son unnamed. Manifiesto target-bound registra syscall 53 y candidato S08. | Se admite sólo subcaso AF_UNIX, no AF_TIPC. Es decisión independiente de S07 NO: no convertirla en S07 ni S10. Dos FDs cruzan S03 como lifecycle aparte; no hay pathname que adjudicar a S01/S04. Documentación de interfaz no demuestra invocación por workload. |
| 54 `setsockopt` | **S08 YES — condicional** | Socket AF_UNIX y opción/level que configure semánticamente su endpoint/comunicación local. Ejemplos documentados Linux: `SOL_SOCKET/SO_PASSCRED`, `SO_PASSSEC`, `SO_PEEK_OFF` donde aplique por tipo/versión; considerar opciones comunes sólo cuando la opción concreta afecta esta comunicación. | `setsockopt(2)` delega semántica por level/optname; `unix(7)` documenta opciones AF_UNIX específicas y sus condiciones. | No es YES para toda opción ni para socket IP: excluir variantes sin dimensión AF_UNIX relevante. `SO_PASSCRED` puede habilitar recepción de credenciales/autobind abstract en condiciones documentadas; no adjudica S09/S10. Lista finita completa por paquete target pendiente, sin cambiar la condición relacional. |
| 55 `getsockopt` | **S08 YES — condicional** | Socket AF_UNIX y consulta de opción/estado local relevante. Ejemplo: `SOL_SOCKET/SO_PEERCRED` sólo para las condiciones documentadas de sockets AF_UNIX conectados y ciertos pares `socketpair`; otras opciones específicas según level/type/estado soportados. | `getsockopt(2)` define consulta por level/optname; `unix(7)` documenta `SO_PEERCRED` y límites. | No incluir toda opción genérica ni sockets de otra family. Credenciales reportadas son dimensión de identidad; no equivalen a payload, `SCM_RIGHTS` ni adjudicación S10. Cierre de opciones y soporte del paquete target requieren evidencia versionada concreta. |
| 288 `accept4` | **S08 YES — condicional** | Aceptación AF_UNIX en listener válido como `accept`, incluidos endpoints pathname/abstract y resultado; flags `SOCK_CLOEXEC`/`SOCK_NONBLOCK` preservados. | `accept(2)` documenta `accept4` y flags; `unix(7)` documenta el socket local aceptado. | Flags y descriptor nuevo son cruces S03, no razón para duplicar S03. Condicionar a listener AF_UNIX/tipo/state; las variantes IP quedan S07. |
| 299 `recvmmsg` | **S08 YES — condicional** | Recepción de uno o más mensajes sobre socket AF_UNIX; cada entrada conserva source/name, iovec/payload, control data, flags, truncamiento, longitud, timeout y resultado parcial. | `recvmmsg(2)` especifica vector/timeout/retorno; `recv(2)`, `unix(7)` y `cmsg(3)` aportan semántica AF_UNIX y control. | Igual separación que `recvmsg`: S02 por payload efectivo, S09 por paso efectivo de FDs en `SCM_RIGHTS`, credenciales aparte. No duplicar otra superficie por el uso de vector; confirmar variante/soporte target. |
| 307 `sendmmsg` | **S08 YES — condicional** | Envío de uno o más mensajes sobre socket AF_UNIX; por entrada conservar name/destination, iovec/payload, ancillary data, flags, longitud y cantidad enviada. | `sendmmsg(2)` define vector y retorno parcial; `send(2)`, `unix(7)` y `cmsg(3)` distinguen transporte/control. | S02 por payload efectivamente enviado; S09 sólo por `SCM_RIGHTS` efectivamente transferido. Cmsg de credenciales no se vuelve S10 automáticamente. AF_INET/6 sigue en S07; confirmar soporte target y por tipo/protocolo. |

**Resumen:** 18 decisiones explícitas: **18 S08 YES condicionales, 0 S08 NO,
0 S08 UNKNOWN** para las variantes listadas. El YES está limitado a la
operación o dimensión AF_UNIX expresamente indicada. No se adjudica cada
invocación global de esas syscalls a S08.

## 4. Límites de nombres y cruces

### Pathname y abstract namespace; S01/S04

Se distinguen endpoint lógico, su dirección, objeto pathname (si existe) y
operación sobre filesystem:

| Variante | Decisión S08 | Cruce S01 | Cruce S04 |
|---|---|---|---|
| AF_UNIX pathname | YES para la comunicación/establecimiento/consulta condicionada por syscall. | Puede haber relación acotada de resolución/identificación en `bind`, `connect` y consultas de nombre; no equivale a adjudicar toda S01. | No adjudicada aquí. La eventual relación depende de justificar creación/mutación/metadata de entrada filesystem bajo doctrina S04; no sustituye S08. |
| AF_UNIX abstract | YES para endpoint/comunicación local por nombre abstracto. | No es resolución de pathname filesystem. | Sin objeto pathname filesystem según `unix(7)`; no se presume ni inventa S04. |
| AF_UNIX unnamed / `socketpair` | YES donde participa el endpoint AF_UNIX, aunque carezca de nombre. | No hay pathname que resolver. | No hay entrada socket pathname inferida. |

El `bind` pathname se adjudica **S08 YES** como establecimiento del endpoint
AF_UNIX, no como decisión automática de S04. La relación S08 se mantiene
aunque una revisión separada determine un cruce S04. La resolución pathname
en `connect` o la devolución de un nombre tampoco adjudican automáticamente
S01.

### S02, S09, S10, S03 y S07

- **S02:** `sendto`/`recvfrom`/`sendmsg`/`recvmsg`/`sendmmsg`/`recvmmsg`
  reciben S08 por transporte AF_UNIX. S02 sigue siendo strict Payload I/O y
  corresponde sólo a payload efectivamente transferido. Ancillary data no se
  reclasifica como payload.
- **S09:** `SCM_RIGHTS` es dimensión separada de paso efectivo de capacidades
  FD; canal AF_UNIX S08 no implica capability passing. Esta adjudicación no
  toca S09. FD instalado y su uso posterior mantienen identidad propia.
- **Credenciales / S10:** `SCM_CREDENTIALS`, `SO_PASSCRED`, `SO_PEERCRED` y
  `SO_PASSSEC` son credenciales/atributos de peer o ancillary data, no
  payload ni `SCM_RIGHTS`. Su posible relación con S10 depende de la doctrina
  y evidencia de IPC/identidad; no se adjudica S10 por arrastre.
- **S03:** creación/retorno de FD, `SOCK_CLOEXEC`, `SOCK_NONBLOCK`,
  `accept4`, cierre/duplicación y herencia son cruces de lifecycle/hygiene.
  No se reabre ni modifica S03. `shutdown` trata el canal; `close` trata FD.
- **S07:** AF_INET/AF_INET6 sigue bajo la adjudicación IP del checkpoint 026.
  AF_UNIX no se absorbe en S07; `socketpair` conserva S07 NO documentado
  independientemente del S08 YES condicional AF_UNIX.

## 5. Evidencia reproducible y límites

1. **Syscall table target-bound en el manifiesto:** establece nombre, número y
   ABI x86_64 de las filas adjudicadas. Hash SHA-256
   `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
   No prueba semántica de una variante de argumentos, ejecución ni efecto.
2. **Man-pages Linux 6.19**, snapshot indicado por 025 como obtenido
   `2026-09-09`, semántica de interfaz Linux:
   [`socket(2)`](https://man7.org/linux/man-pages/man2/socket.2.html),
   [`connect(2)`](https://man7.org/linux/man-pages/man2/connect.2.html),
   [`bind(2)`](https://man7.org/linux/man-pages/man2/bind.2.html),
   [`listen(2)`](https://man7.org/linux/man-pages/man2/listen.2.html),
   [`accept(2)`](https://man7.org/linux/man-pages/man2/accept.2.html),
   [`socketpair(2)`](https://man7.org/linux/man-pages/man2/socketpair.2.html),
   [`send(2)`](https://man7.org/linux/man-pages/man2/send.2.html),
   [`recv(2)`](https://man7.org/linux/man-pages/man2/recv.2.html),
   [`sendmmsg(2)`](https://man7.org/linux/man-pages/man2/sendmmsg.2.html),
   [`recvmmsg(2)`](https://man7.org/linux/man-pages/man2/recvmmsg.2.html),
   [`shutdown(2)`](https://man7.org/linux/man-pages/man2/shutdown.2.html),
   [`getsockname(2)`](https://man7.org/linux/man-pages/man2/getsockname.2.html),
   [`getpeername(2)`](https://man7.org/linux/man-pages/man2/getpeername.2.html),
   [`setsockopt(2)`](https://man7.org/linux/man-pages/man2/setsockopt.2.html),
   [`getsockopt(2)`](https://man7.org/linux/man-pages/man2/getsockopt.2.html),
   [`socket(7)`](https://man7.org/linux/man-pages/man7/socket.7.html),
   [`unix(7)`](https://man7.org/linux/man-pages/man7/unix.7.html) y
   [`cmsg(3)`](https://man7.org/linux/man-pages/man3/cmsg.3.html).
   `unix(7)` distingue pathname, abstract y unnamed, tipos AF_UNIX, lifecycle
   abstract, opciones locales y ancillary data; `socketpair(2)` documenta
   AF_UNIX/AF_LOCAL y AF_TIPC como dominios Linux soportados. Estas páginas
   describen interfaz Linux general, no reachability ni uso por TALOS.
3. **UAPI upstream Linux v7.0**, citada en 025:
   [`include/uapi/linux/un.h`](https://github.com/torvalds/linux/blob/v7.0/include/uapi/linux/un.h)
   y [`include/uapi/linux/socket.h`](https://github.com/torvalds/linux/blob/v7.0/include/uapi/linux/socket.h).
   Evidencia versionada de nombres/estructuras, pero upstream no sustituye
   automáticamente los headers exactos del paquete target. La candidatura
   semántica se condiciona a AF_UNIX y tipo/opción válidos; no se afirma que
   todas las opciones o combinaciones estén habilitadas.
4. **Manifiesto/ledger y checkpoint 027:** autoridad local sobre candidaturas
   estáticas y su estado previo `UNREVIEWED`; no son prueba runtime ni se
   alteran para registrar esta decisión.

Las decisiones son de membresía semántica documental. No prueban invocación,
endpoint real, variante del workload, transferencia efectiva, enforcement ni
resultado de una operación. La incertidumbre residual de soporte exacto por
paquete, opciones concretas y variantes realmente usadas no amplía el YES
fuera de las condiciones explícitas.

## 6. Pistas deliberadamente fuera de esta adjudicación

No se promueven nuevas syscalls ni referencias. Permanecen fuera de las 18
decisiones: syscalls de filesystem para pathname/lifecycle (por ejemplo,
unlink/metadata), `read`/`write` genéricos sobre socket FD, readiness
`poll`/`select`/`epoll*`, interfaces `io_uring`, `socketcall` de otras ABI,
AF_TIPC, S09/transferencia de capacidades y S10/IPC clásico. Se conservan como
pistas o dimensiones cruzadas de 027; no se añaden al manifiesto/ledger ni se
adjudican en este lote.

## 7. Verificación e invariantes

- Las **18/18** candidaturas de 027 tienen una decisión explícita; ninguna se
  omitió.
- Decisiones: **18 S08 YES condicionales**, **0 NO**, **0 UNKNOWN** en los
  subcasos especificados. Pathname, abstract y unnamed/socketpair se
  distinguen.
- `SCM_RIGHTS` no se confunde con S08; S09 no se adjudica. Payload no se
  confunde con transporte; S02 no se modifica. Credenciales no adjudican S10.
- S04 no se adjudica por `bind` pathname; abstract no se convierte en objeto
  filesystem. S01 no se adjudica automáticamente por resolver o consultar
  pathname.
- S03 no se reabre; S07 IP no se amplía ni absorbe AF_UNIX.
- No se promueve ninguna pista. No se materializa ninguna relación en el
  manifiesto/ledger; ambos permanecen byte-idénticos al punto de partida.
- Disposiciones globales: **385/385 UNKNOWN**, **0** disposiciones finales;
  `inventory.frozen=false`; A-PRE-0 `NOT READY`; A-PRE-1 `NOT AUTHORIZED /
  NOT EXECUTED`.
- Se crea este checkpoint y se actualiza `checkpoints/index.md`. No se hace
  stage ni commit; cambios preexistentes ajenos se preservan.
- No se ejecutaron TALOS, FastAPI, probes, tests, pytest, benchmarks,
  workloads, parsers/validadores dinámicos ni A-PRE-1. No se tocó VM, runtime,
  overlay, lock, corpus, modelos, bases de datos, E5/Qwen, Playwright ni código
  de producto.
- No se avanza a S09 ni S10.
