# Adjudicación documental — lote 07, S07 IP/networking

Fecha: 2026-10-01

## 1. Identidad y alcance

Punto de partida verificado:

```text
HEAD   f81134fc2293916210d53c8065f3a0049e52b0b4
TREE   c322e78980ac72f24c66b1396014faefaac074a9
PARENT b17dd9c4dab098512aa6c148e7d36c613da41c28
```

Fuente inmediata de las candidaturas: [`025-preparacion-lote-07-s07.md`](./025-preparacion-lote-07-s07.md).
El manifiesto target-bound de HEAD enumera **17** filas con S07:
`socket` (41), `connect` (42), `accept` (43), `sendto` (44), `recvfrom` (45),
`sendmsg` (46), `recvmsg` (47), `shutdown` (48), `bind` (49), `listen` (50),
`getsockname` (51), `getpeername` (52), `setsockopt` (54), `getsockopt` (55),
`accept4` (288), `recvmmsg` (299) y `sendmmsg` (307).

La lista de ejemplo en la directiva incluye además `socketpair` (53), pero
025 y el manifiesto no lo incluyen entre las 17 candidaturas S07: `socketpair`
tiene candidato S08 solamente. Se respeta el conjunto exacto de 025 y no se
añade una candidatura. Para resolver expresamente la frontera pedida, se
registra más abajo una conclusión documental S07 **NO** para el subcaso
documentado de `socketpair`, separada de las 17 decisiones de membresía y sin
adjudicar ni materializar S08.

La doctrina aplicada es:

> S07 es la superficie de comunicación mediante sockets de red/IP y sus
> operaciones de establecimiento, configuración, conexión, aceptación,
> direccionamiento, transporte y consulta de estado, distinguiendo family,
> type, protocol, endpoint y operación.

Una decisión S07 aquí es relacional; no altera la disposición global de la
syscall, no afirma alcanzabilidad/uso, y no adjudica automáticamente S02, S03,
S08, S09, S10 ni S11. Las decisiones se documentan en este checkpoint; no se
materializan en manifiesto/ledger.

## 2. Decisiones de las 17 candidaturas S07

| NR / syscall | Decisión S07 | Condición y variantes | Justificación y evidencia | Cruces y límites / incertidumbre residual |
|---|---|---|---|---|
| 41 `socket` | **YES, condicional** | Endpoint creado con `AF_INET` o `AF_INET6`; conservar `SOCK_STREAM`, `SOCK_DGRAM`, `SOCK_SEQPACKET`, `SOCK_RAW` cuando el par family/type sea válido, protocol explícito/por defecto y flags `SOCK_NONBLOCK`, `SOCK_CLOEXEC`. | Crea un endpoint de comunicación y selecciona family/type/protocol; `socket(2)` separa familias y semánticas de tipo. | `AF_UNIX`/`AF_LOCAL` queda fuera de S07 y se reserva a S08; otras familias no-IP no entran por analogía. FD/flags no adjudican S03; sharing puede cruzar S10/S11. El soporte de protocolo/family del paquete target no se presume más allá de la tabla/headers disponibles. |
| 42 `connect` | **YES, condicional** | Sólo conexión/asociación de peer en socket IP `AF_INET`/`AF_INET6`; distinguir stream de datagram, sockaddr family/length, peer y retorno/error, incluidas operaciones no bloqueantes. | Asocia el endpoint al peer de red; `connect(2)`, `ip(7)` e `ipv6(7)` describen dirección/protocolo de Internet. | `AF_UNIX` pathname/abstract es S08, no S07; FD permanece una dimensión S03 y comunicación local puede cruzar S10. Los resultados de conexión y errores no son evidencia de uso efectivo por workload. |
| 43 `accept` | **YES, condicional** | Aceptar conexión pendiente en listener IP; family del listener/peer y sockaddr retornada; distinguir blocking/nonblocking, cola, dirección/longitud value-result, éxito/error y nuevo FD. | Extrae una conexión pendiente y crea socket conectado según `accept(2)`. | `AF_UNIX` es S08; retorno de FD no adjudica S03. La aceptación y lifecycle del FD son dimensiones separadas; readiness (poll/epoll) no se decide aquí. |
| 44 `sendto` | **YES, condicional** | En socket IP; registrar family/type/protocol, conectado o no conectado, destino sockaddr (si se proporciona), flags, bytes/retorno parcial/error. | Transmite mediante un endpoint IP a peer/destino; `send(2)` describe `sendto` y sus flags/destino. | S02 puede aplicar separadamente al payload efectivamente transferido; S08 para AF_UNIX. La decisión S07 no amplía ni redefine S02. No se infiere S09 por la mera llamada. |
| 45 `recvfrom` | **YES, condicional** | En socket IP; family/type/protocol, connected/unconnected, buffer y flags, source address/length value-result, bytes devueltos, truncamiento/error. | Recibe datos de un socket y puede proporcionar el origen; `recv(2)` documenta retorno y argumentos de origen. | S02 corresponde a payload efectivamente recibido; S08 para AF_UNIX; S10 sólo si otra decisión lo justifica. Un retorno cero/partial/error conserva semántica propia del protocolo. |
| 46 `sendmsg` | **YES, condicional** | Socket `AF_INET`/`AF_INET6` y operación de comunicación de red. Conservar type/protocol, destination, iovec/payload, flags, `msg_control`, cmsg y retorno. | Envía mensaje por socket; `sendmsg(2)` distingue payload vectorial y ancillary/control data. | S02 sólo para payload efectivo; `SCM_RIGHTS` cruza S09 si realmente transfiere FD; `SCM_CREDENTIALS` y otros cmsg requieren su propia semántica/family. No se adjudica S09 por usar `sendmsg`; AF_UNIX queda S08. |
| 47 `recvmsg` | **YES, condicional** | Socket IP, con partición de family/type/protocol, peer/source, iovec, flags, `MSG_TRUNC`/`MSG_CTRUNC`, payload y cmsg recibido. | Recibe mensaje y metadatos de origen/control; `recvmsg(2)` describe `msghdr`, flags y control data. | S02 para payload efectivo; S09 sólo por transferencia efectiva de capacidad como `SCM_RIGHTS`; credenciales/control no equivalen a payload ni FD passing. AF_UNIX es S08. |
| 48 `shutdown` | **YES, condicional** | En socket IP; conservar `SHUT_RD`, `SHUT_WR`, `SHUT_RDWR`, estado conectado, family y resultado. | Deshabilita envío y/o recepción de una comunicación asociada al socket, según `shutdown(2)`. | Control de comunicación no es `close`/`close_range`; S03 no se adjudica. AF_UNIX queda S08. Otros resultados/fallos se mantienen separados. |
| 49 `bind` | **YES, condicional** | Asignación de dirección IP local a socket `AF_INET`/`AF_INET6`; family, sockaddr, address/port, wildcard, scope/interface, length y resultado. | Asocia dirección local de red al endpoint; `bind(2)`, `ip(7)` e `ipv6(7)` documentan las reglas por family. | AF_UNIX pathname/abstract queda en S08; su pathname puede cruzar S01/S04 en otra decisión. FD no adjudica S03. Conflictos, ephemeral ports, permisos y namespace son condiciones, no una decisión de reachability. |
| 50 `listen` | **YES, condicional** | Sólo listener IP de tipo/estado compatible con conexión; registrar family/type, dirección previa o bind implícito, backlog y resultado. No asumir pertenencia por syscall indiscriminada sobre cualquier socket. | Marca un socket como pasivo para recibir conexiones; `listen(2)` y `accept(2)` describen la secuencia de endpoint/listener. | AF_UNIX pertenece a la dimensión S08; FD/lifecycle S03 separado; estado de readiness queda fuera. Las condiciones exactas dependen del protocolo y del target. |
| 51 `getsockname` | **YES, condicional** | Consulta de endpoint local para socket `AF_INET`/`AF_INET6`; family devuelta, dirección/puerto/scope, length value-result, truncamiento y error. | Recupera dirección a la que está enlazado el socket; `getsockname(2)` describe el sockaddr y length retornados. | AF_UNIX es S08; descriptor como selector no adjudica S03. La consulta no es configuración ni prueba de que el endpoint sea accesible. |
| 52 `getpeername` | **YES, condicional** | Consulta del peer de socket IP con peer establecido; family/address/port/scope, length, estado conectado y error. | Recupera el nombre/dirección del peer asociado; `getpeername(2)` define el resultado. | Peer AF_UNIX es S08; FD no adjudica S03. Socket sin peer y errores permanecen subcasos distintos. |
| 54 `setsockopt` | **YES, condicional** | Sólo opciones que configuran comportamiento de networking IP/transport en socket `AF_INET`/`AF_INET6`; conservar `level`, `optname`, family/type/protocol, optval/optlen y resultado. | La operación asigna una opción identificada por level/name al socket/protocolo; `setsockopt(2)` delega la interpretación al nivel/protocolo pertinente. | No incluir indiscriminadamente todo `SOL_SOCKET` ni opciones AF_UNIX/otras familias. S08 para opción local; FD S03 separado. La inclusión exacta requiere tabla de opciones target/versionada; no se afirma una enumeración cerrada aquí. |
| 55 `getsockopt` | **YES, condicional** | Sólo consultas de opción/estado de networking IP/transport para socket `AF_INET`/`AF_INET6`; `level`, `optname`, optval y optlen value-result, family/type/protocol y resultado. | Consulta opción de nivel socket/protocolo; `getsockopt(2)` comparte la semántica por level/name y describe el buffer value-result. | Excluir consultas genéricas o AF_UNIX salvo decisión separada. No convertir consulta en mutación. S08 y S03 siguen independientes; opciones concretas requieren partición target/versionada. |
| 288 `accept4` | **YES, condicional** | Igual condición IP de `accept`, con `SOCK_CLOEXEC` y `SOCK_NONBLOCK` separados, family/peer address, nuevo FD y retorno/error. | Acepta conexión y crea endpoint conectado; `accept(2)` documenta `accept4` y flags. | S03 puede cubrir la dimensión FD/flags por una decisión separada, pero no se importa aquí; AF_UNIX es S08; herencia process S11 no adjudicada. |
| 299 `recvmmsg` | **YES, condicional** | Recepción de mensajes en socket IP; preservar `mmsghdr` vector, `vlen`, por-mensaje source/payload/control, flags, `MSG_WAITFORONE`, timeout, retorno de cantidad y partial/error. | Extiende `recvmsg` a múltiples mensajes; `recvmmsg(2)` especifica vector, timeout y retorno de mensajes procesados. | S02 para payload efectivamente recibido; S09 sólo para `SCM_RIGHTS` recibido; AF_UNIX es S08. Timeout/ancillary/truncamiento no se colapsan y requieren partición por elemento. |
| 307 `sendmmsg` | **YES, condicional** | En socket IP; preservar vector `mmsghdr`, `vlen`, destino y payload/control por mensaje, flags, longitud por mensaje, retorno parcial y error. | Extiende `sendmsg` a múltiples mensajes; `sendmmsg(2)` define longitud transmitida por entrada y número de entradas enviadas. | S02 para payload efectivamente enviado; S09 sólo si hay paso real de FD por cmsg; AF_UNIX es S08. Fallo posterior a mensajes enviados puede retornar éxito parcial y no se confunde con el resultado por mensaje. |

No hay decisiones `NO` entre las 17 candidaturas preexistentes: cada fila tiene
una relación semántica con networking IP bajo la condición indicada. Las
condiciones no autorizan las variantes AF_UNIX ni otras familias no-IP.

## 3. `socketpair` (53): discrepancia resuelta fuera de las 17 candidaturas

`socketpair` **no está entre las 17 filas S07 de 025**; en el manifiesto
target-bound figura sólo como candidato S08. La referencia documental Linux
`socketpair(2)` indica que los dominios soportados en Linux son `AF_UNIX`
(`AF_LOCAL`) y `AF_TIPC`, sin `AF_INET`/`AF_INET6`. Bajo la definición S07
acotada a sockets IP, la conclusión de frontera para esta preparación es:

> **S07 NO — subcaso `socketpair` con los dominios Linux documentados
> (`AF_UNIX`/`AF_LOCAL`, `AF_TIPC`); no es una de las 17 candidaturas S07.**

Esto no cambia `candidate_surface_ids`, no registra una adjudicación S08 y no
resuelve S10/S03. Si una fuente target-bound futura contradice el conjunto de
dominios, debe reabrirse la frontera mediante cambio versionado; no se infiere
una variante IP no documentada.

## 4. Cruces explícitos de superficies

### S07 / S08

| Syscall | S07 | S08 | Condición de partición |
|---|---|---|---|
| `socket` | YES condicional | No decidido aquí | `domain=AF_INET/AF_INET6` frente a `AF_UNIX/AF_LOCAL`; type/protocol válidos. |
| `connect` | YES condicional | No decidido aquí | Family del endpoint y sockaddr/peer; IP address frente a pathname/abstract/unnamed local. |
| `bind` | YES condicional | No decidido aquí | Family y estructura/address; IP/port frente a pathname/abstract. |
| `listen` | YES condicional | No decidido aquí | Family/type del listener y estado de conexión. |
| `accept`, `accept4` | YES condicional | No decidido aquí | Family del listener/peer y address retornada; FD/flags no cambian la familia. |
| `sendto`, `recvfrom` | YES condicional | No decidido aquí | Family efectiva del socket y address destino/origen. |
| `sendmsg`, `recvmsg` | YES condicional | No decidido aquí | Family efectiva, protocolo y separación payload/control/cmsg; cmsg no convierte AF_UNIX en IP. |
| `socketpair` (53) | **NO** en el subcaso documentado, fuera de las 17 | Sin adjudicación | Los dominios Linux documentados son AF_UNIX/AF_LOCAL y AF_TIPC; no se añade candidatura S07. |

No se adjudica S08 con esta tabla. La dirección IP no se deduce de que el FD
sea un socket; se conserva el `sa_family` efectivo y el tipo de endpoint.

### S07 / S02

`sendto`, `recvfrom`, `sendmsg`, `recvmsg`, `sendmmsg` y `recvmmsg` tienen
**S07 YES condicional** para operación de red IP, independientemente de que
una variante transfiera payload. S02 es la dimensión de transferencia efectiva
de payload bajo su doctrina strict Payload I/O. Un S07 YES no crea ni modifica
S02; cuando bytes de payload se transfieren efectivamente, las dos dimensiones
pueden coexistir. Consulta de dirección, error o llamada sin payload efectivo
no se cuenta por analogía como transferencia S02.

### S07 / S09: `SCM_RIGHTS`, `SCM_CREDENTIALS` y control data

| Contenido `sendmsg`/`recvmsg`/mmsg | Tratamiento en esta decisión S07 | Relación separada |
|---|---|---|
| iovec/payload | S07 YES si el socket/familia es IP; S02 sólo por payload efectivo. | Las dos relaciones no se sustituyen. |
| `SCM_RIGHTS` | No cambia la decisión S07 del socket; conservar como ancillary/control, no como payload. | S09 cuando haya paso efectivo de capacidad FD, sujeto a su adjudicación propia. |
| `SCM_CREDENTIALS` | No convierte por sí solo la llamada en S07; la relación S07 sigue dependiendo de family/IP. | Credenciales/control se mantienen aparte; no se adjudica S09 por analogía. |
| Otros cmsg | Mantener type/level, family, protocolo y resultado por mensaje. | No se asigna superficie automáticamente; requiere semántica específica. |

La disponibilidad/validez de cada cmsg para una familia dada se debe verificar
por protocolo y documentación target; no se presupone que los cmsg propios de
AF_UNIX sean aplicables a IP.

### S03 / S10 / S11

- S03: creación/retorno de FD, `SOCK_CLOEXEC`, `SOCK_NONBLOCK`, cierre y
  duplicación siguen dimensiones FD; la membresía S07 no las adjudica.
- S10: comunicación local/socket coordination puede motivar revisión IPC
  separada; crear un socket o `socketpair` no adjudica S10 por analogía.
- S11: herencia de FDs y lifecycle del proceso no se resuelven con esta
  decisión de networking.

## 5. Pistas adicionales

Se conservan sin promover las pistas/rutas adicionales de 025: `socketpair`
(53) permanece candidato S08 fuera de S07; `sendfile` (40), `splice` (275),
`io_uring` (425) y `read`/`write` genéricos sobre socket FD siguen como rutas
potenciales que requieren traceabilidad/decisión propia; `poll`, `select`,
`epoll*` permanecen consultas de readiness, no comunicación S07 por sí solas;
`socketcall` (102) está fuera de la tabla nativa x86_64 target-bound. No se
promueve ninguna pista ni se modifica el inventario de candidaturas.

## 6. Evidencia y límites

- **Autoridad de número/ABI y conjunto:** `A_PRE_0_SURFACE_MANIFEST.json` en
  HEAD verificado; syscall table target-bound x86_64, 385 filas, hash
  `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
  La tabla acredita nombres/números/ABI, no alcanzabilidad ni uso.
- **Man-pages Linux 6.19**, snapshot identificado en 025 como obtenido
  2026-09-09:
  [`socket(2)`](https://man7.org/linux/man-pages/man2/socket.2.html),
  [`socketpair(2)`](https://man7.org/linux/man-pages/man2/socketpair.2.html),
  [`connect(2)`](https://man7.org/linux/man-pages/man2/connect.2.html),
  [`bind(2)`](https://man7.org/linux/man-pages/man2/bind.2.html),
  [`listen(2)`](https://man7.org/linux/man-pages/man2/listen.2.html),
  [`accept(2)`](https://man7.org/linux/man-pages/man2/accept.2.html),
  [`shutdown(2)`](https://man7.org/linux/man-pages/man2/shutdown.2.html),
  [`getsockname(2)`](https://man7.org/linux/man-pages/man2/getsockname.2.html),
  [`getpeername(2)`](https://man7.org/linux/man-pages/man2/getpeername.2.html),
  [`send(2)`](https://man7.org/linux/man-pages/man2/send.2.html),
  [`recv(2)`](https://man7.org/linux/man-pages/man2/recv.2.html),
  [`sendmmsg(2)`](https://man7.org/linux/man-pages/man2/sendmmsg.2.html),
  [`recvmmsg(2)`](https://man7.org/linux/man-pages/man2/recvmmsg.2.html),
  [`getsockopt(2)`](https://man7.org/linux/man-pages/man2/getsockopt.2.html),
  [`socket(7)`](https://man7.org/linux/man-pages/man7/socket.7.html),
  [`ip(7)`](https://man7.org/linux/man-pages/man7/ip.7.html),
  [`ipv6(7)`](https://man7.org/linux/man-pages/man7/ipv6.7.html) y
  [`unix(7)`](https://man7.org/linux/man-pages/man7/unix.7.html).
  Aportan semántica de interfaz Linux general; no prueban uso en workload ni
  sustituyen los headers/fuentes exactos del paquete Ubuntu target.
- **UAPI upstream Linux v7.0** citado en 025:
  `include/uapi/linux/socket.h`, `include/uapi/linux/in.h`,
  `include/uapi/linux/in6.h`, `include/uapi/linux/un.h`. Es referencia
  versionada de símbolos/estructuras, no identidad del paquete target ni
  prueba de que todos los protocolos estén habilitados.
- **Opciones de socket:** `setsockopt(2)`/`getsockopt(2)` asignan interpretación
  por `level`/`optname` y protocolo; por eso su decisión queda condicional y
  la lista exhaustiva de opciones no está cerrada aquí.
- Checkpoint 025 proporciona la partición doctrinal S07/S08/S09/S02 y la
  clasificación de pistas adicionales; no constituye prueba de runtime.

## 7. Estado y verificación

- Candidaturas S07 de 025 adjudicadas documentalmente: **17** — **17 YES
  condicionales, 0 NO, 0 UNKNOWN**.
- `socketpair` (53): conclusión documental separada **S07 NO** para los
  dominios Linux documentados; no se cuenta como candidatura S07 ni como
  adjudicación S08.
- Pistas adicionales promovidas: **0**. S08 y S09 no se adjudican por este
  lote; la mención de S09 sólo delimita el cmsg `SCM_RIGHTS`.
- Disposiciones globales siguen **385/385 UNKNOWN**, con **0** disposiciones
  finales; `inventory.frozen=false`; A-PRE-0 `NOT READY`; A-PRE-1
  `NOT AUTHORIZED / NOT EXECUTED`.
- Manifiesto y ledger no se modifican; ninguna membresía se materializa en
  esos canónicos. S02/S03/S08/S09/S10/S11 y disposiciones globales no cambian.
- Se crea este checkpoint y se actualiza el índice. No se hizo stage ni
  commit; los cambios preexistentes ajenos del worktree permanecen intactos.
- No se ejecutaron TALOS, FastAPI, probes, tests, pytest, benchmarks,
  workloads, parsers dinámicos ni A-PRE-1. No se tocó VM, runtime, overlay,
  `requirements.lock`, corpus, modelos, bases de datos, E5/Qwen ni Playwright.
- No se avanza a S08 ni S09.
