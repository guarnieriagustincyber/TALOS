# Preparación documental — lote 09, S09 FD capability passing

Fecha: 2026-10-01

## 1. Objetivo y estado de decisión

Preparar exclusivamente las cinco candidaturas documentales S09 solicitadas,
para adjudicación humana posterior. No adjudicar relaciones, no materializar
membresías canónicas y no cambiar disposiciones globales. La metodología se
mantiene:

> OBSERVE → MEASURE → CORRELATE → CLASSIFY → HUMAN DECISION → FUTURE CHANGE

Este checkpoint es preparación: no propone YES/NO/UNKNOWN como decisión humana
ni convierte la presencia de candidaturas en el manifiesto en membresía
adjudicada. La evidencia documental de semántica se presenta separada de la
falta de evidencia de uso/alcanzabilidad por workload.

## 2. Identidad del punto de partida

Repositorio: `/media/agustin/Laboratorio/study-engie`

```text
HEAD   f81134fc2293916210d53c8065f3a0049e52b0b4
TREE   c322e78980ac72f24c66b1396014faefaac074a9
PARENT b17dd9c4dab098512aa6c148e7d36c613da41c28
```

El worktree ya contenía cambios preexistentes ajenos. Se preservaron sin
limpiar, resetear o modificar. Archivos de referencia presentes al inicio:

- [028-adjudicacion-documental-lote-08-s08.md](./028-adjudicacion-documental-lote-08-s08.md)
  SHA-256 `82bebe3d80b5b76e659d4ca8d637ecd96d7819d6a23ddf4a69c9c0f9f6991561`.
- [027-preparacion-lote-08-s08.md](./027-preparacion-lote-08-s08.md)
  SHA-256 `bcc40808cbc5a42dbb246c6f57fac55fbbfcf56f3948e688ff98c00ce161d871`.
- `files/A_PRE_0_SURFACE_MANIFEST.json` SHA-256
  `bc498e058585341b341f8318fb8a2dd869c5737ebd63fd89f0878cef0793e20e`.
- `files/A_PRE_0_QUALIFICATION_LEDGER.json` SHA-256
  `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42`.
- `docs/A_PRE_0_BASELINE_SPEC.md` establece preflight REVIEW REQUIRED /
  NOT READY FOR A-PRE-1; A-PRE-1 NOT EXECUTED y NOT AUTHORIZED.

La syscall table objetivo se registra como ABI nativa x86_64 de 385 filas,
SHA-256 `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
Los cinco números/nombres solicitados aparecen en las filas target-bound:
46 `sendmsg`, 47 `recvmsg`, 299 `recvmmsg`, 307 `sendmmsg`, 438
`pidfd_getfd`.

## 3. Doctrina provisional S09

> **S09 = paso o adquisición de una capacidad representada por un file
> descriptor entre procesos, incluyendo el mecanismo explícito de transferencia
> (`SCM_RIGHTS`) y la adquisición directa de un FD perteneciente a otro proceso
> (`pidfd_getfd`).**

S09 no equivale a cualquier uso de `sendmsg`/`recvmsg`, socket o IPC; tampoco
equivale a lectura/escritura posterior, herencia por exec ni duplicación local
del descriptor. La cuestión a decidir es el paso/adquisición de capacidad
interprocesos bajo las condiciones documentadas. El descriptor recibido puede
referir a un objeto de kernel distinto; el tipo/identidad del objeto y el uso
posterior se deben rastrear como dimensiones separadas.

## 4. Estado canónico previo y alcance de candidaturas

En el manifiesto, `sendmsg` (46), `recvmsg` (47), `recvmmsg` (299) y
`sendmmsg` (307) tienen candidato S09 dentro del contexto de syscall de
socket; la relación figura `UNREVIEWED_CANDIDATE`, con disposición global
`UNKNOWN`. Los ejes S09 del manifiesto incluyen `SCM_RIGHTS` y la identidad
del descriptor recibido, marcan `SCM_CREDENTIALS` como metadato de peer/no
transferencia de FD y requieren correlacionar objeto transferido y uso
posterior. No se cambia ese estado.

`pidfd_getfd` (438) tiene candidato S09 también **UNREVIEWED**. Su dimensión
S03 sí cuenta con decisión humana previa: [018-adjudicacion-documental-lote-03-s03.md](./018-adjudicacion-documental-lote-03-s03.md)
aceptó, bajo condición de autorización, la adquisición en el proceso llamante
de un FD local que refiere al objeto del FD remoto. La misma decisión declara
obligatorio el cruce S09/IPC-Processes, pero no adjudica S09. La fila global
sigue `UNKNOWN`; no se reabre S03 en este lote.

## 5. Análisis por candidatura — decisiones S09 reservadas

| NR / syscall | Estado de relación S09 actual | Semántica candidata y condiciones a examinar | Pregunta para adjudicación humana | Cruces descriptivos; no adjudicados aquí |
|---|---|---|---|---|
| 46 `sendmsg` | Candidata `UNREVIEWED`; disposición global `UNKNOWN` | Envío de `msghdr` sobre socket; la variante pertinente lleva cmsg `SOL_SOCKET/SCM_RIGHTS` que identifica uno o más FDs. Registrar proceso emisor, socket/domino/peer, número y valores FD en control buffer, resultado y si la operación se completó. El envío de payload/iovec solo no equivale a paso de FD. Emisor normalmente conserva sus propios FDs; no confundir duplicación de referencia con “move” que los cierra. | ¿Se acepta S09 sólo para envío efectivo de `SCM_RIGHTS` que introduce capacidad en otro proceso, y qué evidencia correlaciona receptor y descriptor finalmente instalado? ¿Qué resultado parcial/error cuenta como transferencia? | S02: payload separado. S03: FD origen/lifecycle separado. S05: objeto file-backed posible por tipo de FD, no por llamada. S06: memfd/objeto de memoria posible. S07/S08: transporte por dominio IP/AF_UNIX; `SCM_RIGHTS` necesita mecanismo socket/documentar restricción del protocolo (Linux `unix(7)` para UNIX sockets). S10: coordinación local potencial, no automática. S11: emisor/receptor/proceso y fase. |
| 47 `recvmsg` | Candidata `UNREVIEWED`; disposición global `UNKNOWN` | Recepción de cmsg `SCM_RIGHTS` a través de `msghdr`; diferenciar cmsg presente, FDs representados, buffer ancillary suficiente/truncado, FDs instalados en receptor, cantidad/identidad y resultado. Considerar `MSG_CMSG_CLOEXEC`, que documenta `FD_CLOEXEC` para FD recibido en UNIX domain. Recibir payload sin rights no constituye S09 por sí solo. | ¿Qué condición de recepción confirma adquisición de capacidad S09 —cmsg recibido, FD instalado, o ambos— y cómo tratar `MSG_CTRUNC`, errores y cierres durante el procesamiento? | S02: payload independiente. S03: instalación, `FD_CLOEXEC`, close/dup y lifecycle de receptor. S05/S06: backing/resource del FD recibido. S07/S08: socket y transporte de origen; el uso de `recvmsg` sobre IP no implica por sí mismo `SCM_RIGHTS`. S10: proceso/IPC no automático. S11: proceso receptor, credenciales/atribución y fase. |
| 299 `recvmmsg` | Candidata `UNREVIEWED`; disposición global `UNKNOWN` | Extensión vectorial de `recvmsg`: revisar cada `mmsghdr.msg_hdr.msg_control` y el/los cmsg por mensaje, `vlen`, número realmente recibido, retorno parcial, `msg_len`, truncamiento y posibles FDs instalados por entrada. No propagar a todos los mensajes una transferencia vista en una sola entrada. | ¿S09 aplica por mensaje que efectivamente contiene y entrega `SCM_RIGHTS`? ¿Cuál es la unidad de evidencia para correlacionar cada entrada con sus FDs y resultado? | Igual partición que `recvmsg` para S02/S03/S05/S06/S07/S08/S10/S11. Vector/timeout/retorno parcial son dimensiones de `recvmmsg`, no superficie nueva. Debe verificarse soporte de variante por target; existencia de la syscall no demuestra uso. |
| 307 `sendmmsg` | Candidata `UNREVIEWED`; disposición global `UNKNOWN` | Extensión vectorial de `sendmsg`: examinar `mmsghdr.msg_hdr.msg_control` y `SCM_RIGHTS` por entrada, cantidad de mensajes enviados y retorno parcial. Distinguir entrada preparada de mensaje efectivamente enviado; un error tras éxitos parciales puede devolver cantidad enviada. | ¿S09 aplica sólo a entradas confirmadas como enviadas y cómo se correlaciona cada envío con la recepción/instalación en proceso destinatario? | Igual separación que `sendmsg` para S02/S03/S05/S06/S07/S08/S10/S11. El vector no convierte mensaje sin rights en capability passing. El soporte preciso del ancillary por mensaje queda sujeto a evidencia target-bound. |
| 438 `pidfd_getfd` | S09 candidata `UNREVIEWED`; S03 ya adjudicada YES acotado; disposición global `UNKNOWN` | Con `pidfd` de otro proceso, `targetfd` abierto allí y `flags=0`, la syscall documentada asigna un nuevo FD en el caller que refiere al mismo open file description. Retorno es nuevo FD; `FD_CLOEXEC` queda establecido. Requiere comprobación de acceso ptrace `PTRACE_MODE_ATTACH_REALCREDS`; errores incluyen `EBADF`, `EINVAL`, `EMFILE`, `ENFILE`, `EPERM`, `ESRCH`. A diferencia de `SCM_RIGHTS`, no necesita cooperación ni socket UNIX entre procesos. | ¿La definición S09 incluye explícitamente esta adquisición directa, aunque la syscall duplique/obtenga referencia y no realice protocolo `SCM_RIGHTS`? ¿Cuál es el límite entre dimensión S03 ya aceptada (FD local adquirido) y S09 (transferencia/adquisición interproceso)? | S03: YES previo para adquisición/lifecycle FD; no volver a adjudicar. S05/S06: depende del open file description/objeto. S07/S08: el FD adquirido puede ser socket; no es mecanismo de transporte S07/S08. S02: sólo uso posterior de payload. S10: interacción entre procesos puede ser relevante, no adjudicada. S11: identidad/lifecycle del proceso del pidfd; permisos/credenciales como condiciones. |

La tabla orienta preguntas y evidencia; no decide si alguna relación es S09
YES, NO o UNKNOWN. En particular, `sendmsg`/`recvmsg` sin `SCM_RIGHTS` y
`SCM_CREDENTIALS` no se clasifican automáticamente como S09; la definición
provisional excluye credenciales como mecanismo de transferencia de FD.

## 6. Núcleo `SCM_RIGHTS`: trazabilidad del evento de capacidad

La futura decisión debe conservar como mínimo esta secuencia, sin tratarla
como un único hecho indiferenciado:

1. **Preparación/envío:** emisor, socket, tipo/familia/peer, cmsg
   `SOL_SOCKET/SCM_RIGHTS`, longitud y FDs locales señalados.
2. **Transporte:** operación real de `sendmsg` o entrada enviada de
   `sendmmsg`; resultado/errores. La syscall permite ancillary data, pero una
   invocación sin cmsg rights no demuestra paso de FD.
3. **Recepción/adquisición:** proceso receptor, `recvmsg`/entrada de
   `recvmmsg`, cmsg decodificado, truncamiento, FDs instalados y flags como
   `MSG_CMSG_CLOEXEC`.
4. **Identidad del recurso:** correspondencia entre FD emisor, objeto/open
   file description transferido y descriptor local instalado; considerar
   que el entero FD remoto no es el mismo número necesariamente.
5. **Uso posterior:** operaciones realizadas sobre el FD recibido, bajo la
   superficie del recurso/operación correspondiente; el uso no se adjudica
   por inferencia dentro de S09.

`unix(7)` documenta paso de file descriptors como ancillary data de
Unix-domain sockets. Por ello, la familia/domain y el peer/route son ejes
críticos: no extrapolar el soporte de `SCM_RIGHTS` a cualquier llamada de
`sendmsg` sobre cualquier socket/familia. `SCM_CREDENTIALS` transporta
credenciales/identidad y no un descriptor; su análisis de atribución puede
cruzar S10/S11, pero requiere decisión propia.

## 7. `pidfd_getfd`: adquisición interproceso separada

Documentación `pidfd_getfd(2)` describe que:

- toma `pidfd`, `targetfd` del proceso referido y `flags` reservado (actualmente
  cero);
- en éxito crea un nuevo descriptor en el proceso llamante que duplica el
  descriptor remoto y refiere al mismo open file description;
- los dos FDs comparten file status flags y file offset;
- el FD retornado tiene `FD_CLOEXEC`;
- acceso está sujeto a `PTRACE_MODE_ATTACH_REALCREDS`;
- el mecanismo se parece a `SCM_RIGHTS` en el efecto de obtener referencia,
  pero no requiere socket UNIX ni cooperación del proceso dueño del FD.

La consecuencia documental es que la syscall constituye una candidatura S09
distinta del transporte SCM: un mecanismo de adquisición directa con autorización.
La decisión S09, sin embargo, queda reservada a la persona revisora. El
checkpoint 018 ya aceptó sólo la dimensión S03 de adquisición local del FD;
esa aceptación no se extiende ni se copia a S09. Deben quedar separadas:

```text
FD remoto referenciado → adquisición/duplicación local → uso posterior → lifecycle local
          └──────── dimensión interproceso S09 pendiente ────────┘
```

## 8. Exclusiones conceptuales y cuestiones UNKNOWN para revisión

No son S09 automáticamente por nombre o mecanismo superficial:

- `sendmsg`/`recvmsg` sin control `SCM_RIGHTS`;
- `SCM_CREDENTIALS` o datos ancillary que no transfieren FD;
- sockets IP/AF_UNIX sin paso de descriptor;
- payload S02 enviado/recibido por mensaje;
- uso posterior del FD después de la transferencia;
- FD heredado por `fork`/`exec` sin transferencia/adquisición de esta clase;
- duplicación local ordinaria, salvo que la semántica interproceso de la
  operación específica satisfaga la definición;
- descriptor ya presente en el proceso desde el inicio.

Esto enumera límites conceptuales; **no adjudica S09 NO** a una fila completa
ni cierra subvariantes. Las decisiones humanas deben resolver explícitamente:

1. ¿`sendmsg` y `sendmmsg` son YES sólo para `SCM_RIGHTS` efectivamente
   enviado, o el modelo de superficie registra también el mecanismo preparado
   cuando el resultado falla?
2. ¿`recvmsg`/`recvmmsg` requieren recepción de cmsg y FD instalado para YES,
   o se distingue adquisición intentada/fallida?
3. ¿Cómo se representa cardinalidad, cmsg truncado, varios FDs por cmsg y
   varios mensajes por mmsg?
4. ¿Qué evidencia basta para ligar sender, receiver, objeto/open file
   description y posterior uso, sin inferir a partir de igualdad de números FD?
5. ¿Se incluye `pidfd_getfd` en S09 bajo la definición amplia de “adquisición”
   pese a que es duplicación directa, no `SCM_RIGHTS`, y qué límite precisa
   respecto de S03 ya adjudicada?
6. ¿Qué restricciones del pidfd, namespace/proceso, ptrace access check,
   flags y resultado se deben convertir en particiones finitas?
7. ¿Qué cmsg/variantes están soportadas por el paquete target y ABI elegida?
   No inferir soporte target desde documentación de otra arquitectura o
   versión upstream.
8. ¿Cuándo `SCM_CREDENTIALS` es sólo atribución del evento y cuándo, si acaso,
   habilita análisis S10/S11 independiente? No lo convertir a transferencia
   S09.

El estado canónico de las relaciones S09 permanece no adjudicado; por ello
estos casos siguen abiertos para decisión humana. No se agregan nuevos
candidatos ni se promueven pistas.

## 9. Cruces de superficie

| Superficie | Cruce que debe mantenerse independiente | Límite para S09 |
|---|---|---|
| S02 — payload I/O | Bytes iovec/payload efectivamente transmitidos o recibidos. | Payload no es capacidad FD ni `SCM_RIGHTS`. |
| S03 — FD lifecycle/hygiene | Descriptor de origen, FD local instalado/adquirido, `FD_CLOEXEC`, close/dup y estado local. `pidfd_getfd` tiene S03 YES acotado preexistente. | No re-adjudicar S03 ni confundir FD local resultante con decisión S09. |
| S05 — file-backed mapping | El objeto del FD puede ser archivo/mappeable y uso posterior puede afectar mapping. | No inferir backing file ni mapping desde el mecanismo de transferencia. |
| S06 — anonymous/memfd | Descriptor transferido puede referir a memfd/objeto memoria. | El tipo de objeto y operación posterior se clasifican por separado. |
| S07 — IP networking | `sendmsg`/mmsg pueden usar sockets IP para payload; el canal/familia es eje distinto. | La candidata S09 por `SCM_RIGHTS` no convierte IP networking en S09; el soporte cmsg debe verificarse por familia. |
| S08 — AF_UNIX | Unix-domain socket es canal documentado para SCM_RIGHTS; checkpoint 028 adjudica AF_UNIX S08 condicional. | S08 es transporte local; S09 es transferencia/adquisición del objeto FD. Un canal sin rights no se vuelve S09. |
| S10 — IPC/coordination | Interacción entre procesos y credenciales podría ser contexto/otra relación. | No adjudicar S10 por usar socket, pidfd o `SCM_CREDENTIALS`. |
| S11 — process/exec | Identidad del emisor/receptor, pidfd y herencia/exec pueden contextualizar el evento. | No confundir adquisición S09 con herencia por exec; `FD_CLOEXEC` es eje FD separado. |

## 10. Evidencia y límites

- **Autoridad ABI/número:** syscall table x86_64 target-bound preservada en el
  manifiesto, hash `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
  Prueba que las cinco entradas están presentes con sus nombres/números/ABI;
  no prueba ejecución ni efecto.
- **Estado candidato canónico:** `A_PRE_0_SURFACE_MANIFEST.json` en HEAD:
  candidaturas S09 para las cinco; `sendmsg`, `recvmsg`, `sendmmsg` y
  `recvmmsg` permanecen `UNREVIEWED`; en `pidfd_getfd`, S03 tiene aceptación
  acotada documentada en checkpoint 018 y S09 sigue `UNREVIEWED`. Las filas
  mantienen `disposition_status=UNKNOWN`.
- **Man-pages Linux 6.19**, snapshot registrado en checkpoints previos como
  obtenido `2026-09-09`:
  [`sendmsg(2)`](https://man7.org/linux/man-pages/man2/sendmsg.2.html),
  [`recvmsg(2)`](https://man7.org/linux/man-pages/man2/recvmsg.2.html),
  [`sendmmsg(2)`](https://man7.org/linux/man-pages/man2/sendmmsg.2.html),
  [`recvmmsg(2)`](https://man7.org/linux/man-pages/man2/recvmmsg.2.html),
  [`unix(7)`](https://man7.org/linux/man-pages/man7/unix.7.html),
  [`cmsg(3)`](https://man7.org/linux/man-pages/man3/cmsg.3.html),
  [`pidfd_getfd(2)`](https://man7.org/linux/man-pages/man2/pidfd_getfd.2.html)
  y [`ptrace(2)`](https://man7.org/linux/man-pages/man2/ptrace.2.html).
  `sendmsg`/`recvmsg` definen `msghdr`/control data; `MSG_CMSG_CLOEXEC`
  controla CLOEXEC de FD recibido en `recvmsg`; `sendmmsg`/`recvmmsg` son
  extensiones vectoriales de `sendmsg`/`recvmsg`; `unix(7)` describe
  `SCM_RIGHTS` y credenciales; `pidfd_getfd(2)` define adquisición, open file
  description compartido y ptrace check. Estas referencias establecen
  semántica Linux documentada, no el uso del workload ni cada subvariante
  habilitada en el paquete target.
- **Fuentes locales A-PRE:** manifiesto/ledger y checkpoints 018, 026, 028
  son evidencia de ABI/estado/crosswalk/documentación previa. No aportan
  observación runtime ni autorización A-PRE-1.

Límite metodológico: no se ejecutaron pruebas ni probes para convertir
semántica documentada en evidencia de uso. No se extrapola desde otra ABI o
arquitectura. Antes de cerrar variante target-specific puede requerirse
contrastar headers/source exactos del paquete objetivo; ese contraste no debe
ser sustituido por la mera presencia en una tabla de syscall.

## 11. Invariantes y estado de preparación

- Candidaturas preparadas: **5 exactas** — 46 `sendmsg`, 47 `recvmsg`, 299
  `recvmmsg`, 307 `sendmmsg`, 438 `pidfd_getfd`.
- Decisiones humanas S09 realizadas en este checkpoint: **0**. Relaciones
  candidatas siguen sin adjudicar; `pidfd_getfd` conserva solamente la
  adjudicación S03 previa, no extendida a S09.
- `SCM_RIGHTS` se identifica como mecanismo central candidato; `SCM_CREDENTIALS`
  queda explícitamente separado como credencial/identidad, no transferencia FD.
- Se describen cruces S02/S03/S05/S06/S07/S08/S10/S11 sin adjudicarlos.
- No se materializan relaciones; manifiesto y ledger quedan intactos.
- Disposiciones generales: **385/385 UNKNOWN**; **0** disposiciones finales
  nuevas; `inventory.frozen=false`; A-PRE-0 **NOT READY**; A-PRE-1
  **NOT AUTHORIZED / NOT EXECUTED**.
- No se ejecutaron TALOS, FastAPI, workloads reales, proveedores, corpus,
  benchmarks, probes dinámicos, bases de datos de producción ni A-PRE-1.
- `requirements.lock`, E5/Qwen, modelos, corpus, DBs protegidas, VM, runtime,
  overlay, Playwright y código funcional no se modifican.
- No se hace stage ni commit. Los cambios ajenos preexistentes se preservan.
- Resultado: **preparado para adjudicación humana S09; no se avanza a S10**.
