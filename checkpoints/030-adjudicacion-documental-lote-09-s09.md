# Adjudicación documental humana — lote 09, S09 FD capability passing

Fecha: 2026-10-01

## 1. Doctrina y alcance

> **S09 = paso o adquisición de una capacidad representada por un file
> descriptor entre procesos, incluyendo el mecanismo explícito de transferencia
> mediante `SCM_RIGHTS` y la adquisición directa de un FD perteneciente a otro
> proceso mediante `pidfd_getfd`.**

Se adjudica únicamente la relación de superficie S09 bajo las condiciones
indicadas por fila. Transporte del descriptor, adquisición/recepción, uso
posterior y efecto producido por el objeto recibido son dimensiones distintas.
Una relación S09 YES no implica reachability, observación, enforcement ni
disposición global final del syscall.

Se parte de la preparación
[029-preparacion-lote-09-s09.md](./029-preparacion-lote-09-s09.md),
SHA-256 `eb9139882d084181e2d2150f56890483a869f6968f509e36b43d9bfcca5b02df`.
Su conjunto de cinco candidaturas coincide exactamente con esta adjudicación.

## 2. Identidad de partida y autoridad

Repositorio: `/media/agustin/Laboratorio/study-engie`

```text
HEAD   f81134fc2293916210d53c8065f3a0049e52b0b4
TREE   c322e78980ac72f24c66b1396014faefaac074a9
PARENT b17dd9c4dab098512aa6c148e7d36c613da41c28
```

El worktree ya contenía cambios ajenos; se preservaron. Al inicio, el
manifiesto, ledger y `requirements.lock` coincidían con HEAD. La tabla nativa
x86_64 target-bound registrada en el manifiesto comprende 385 filas; SHA-256
de la tabla `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.

## 3. Decisiones humanas por candidatura

| NR / syscall | Decisión S09 | Condición exacta | Justificación y límite |
|---|---|---|---|
| 46 `sendmsg` | **YES — condicional** | Sólo la variante cuyo `msghdr.msg_control` incluye cmsg `SOL_SOCKET/SCM_RIGHTS` con uno o más FDs, como mecanismo de paso de esas capacidades a otro proceso por un socket que soporte esa semántica. Un resultado fallido no demuestra transferencia efectiva; el resultado y recepción se correlacionan aparte. | `sendmsg(2)` admite ancillary data; `unix(7)` documenta el paso de FDs con `SCM_RIGHTS`. Payload-only y `SCM_CREDENTIALS`-only quedan fuera de S09. El YES no cubre todos los usos de `sendmsg`, todas las familias ni afirma que el peer recibió/instaló el FD. |
| 47 `recvmsg` | **YES — condicional** | Sólo recepción de ancillary `SOL_SOCKET/SCM_RIGHTS`; adquisición efectiva cuando el kernel instala uno o más FDs en el proceso receptor. Preservar cmsg, número/identidad de FDs y flags, incluido `MSG_CMSG_CLOEXEC`; tratar `MSG_CTRUNC` y errores como variantes distintas. | `recvmsg(2)` describe control data recibido y `MSG_CMSG_CLOEXEC` para FDs de UNIX-domain `SCM_RIGHTS`; `unix(7)` describe la transferencia. Payload-only/credenciales-only no son S09. Un cmsg truncado no autoriza inferir los FDs no recibidos. |
| 299 `recvmmsg` | **YES — condicional, por entrada** | Sólo cada `mmsghdr` cuya `msg_hdr` recibe cmsg `SCM_RIGHTS` y cuyos FDs son instalados en el receptor. Evaluar cantidad de mensajes retornada, control buffer, truncamiento y descriptors por entrada; no propagar la decisión a otros elementos del vector. | `recvmmsg(2)` define `mmsghdr.msg_hdr` como `msghdr` y lo describe como extensión de `recvmsg(2)`; la semántica de rights deriva de la entrada individual. No adjudicar payload-only ni elementos que no recibieron rights. |
| 307 `sendmmsg` | **YES — condicional, por entrada** | Sólo cada elemento transmitido cuya `msg_hdr.msg_control` contiene `SCM_RIGHTS` con uno o más FDs. Preservar `vlen`, cantidad retornada y éxito/error parcial por elemento; un elemento no enviado no prueba paso efectivo. | `sendmmsg(2)` define cada `mmsghdr.msg_hdr` como `msghdr` y es extensión de `sendmsg(2)`; los ancillary data se evalúan por mensaje efectivamente enviado. Payload-only/credenciales-only no son S09. |
| 438 `pidfd_getfd` | **YES — condicional; cross-membership S03/S09** | El caller tiene un `pidfd` válido del proceso objetivo, `targetfd` abierto en ese proceso y `flags=0`; se satisface autorización `PTRACE_MODE_ATTACH_REALCREDS`; syscall exitosa devuelve en caller un nuevo FD al mismo open file description del FD objetivo y establece `FD_CLOEXEC`. | `pidfd_getfd(2)` especifica explícitamente la adquisición de una copia de un FD de otro proceso, con referencia compartida a la misma open file description y el check ptrace. Bajo la doctrina S09, es adquisición interproceso de capacidad aunque no use `SCM_RIGHTS` ni requiera cooperación/socket. La decisión S03 YES existente permanece separada e intacta; S09 sólo cubre la dimensión interproceso. El uso posterior y lifecycle local del FD no se incorporan a esta relación. |

**Conteo:** 5 decisiones explícitas: **5 YES condicionales, 0 NO, 0 UNKNOWN**
para las condiciones de variante enumeradas. No se cierra todo uso de estas
syscalls: payload-only, credenciales-only, mensajes sin rights y entradas mmsg
sin transferencia quedan fuera del YES. Las llamadas fallidas, los resultados
parciales, la recepción truncada y la correspondencia sender/receiver requieren
correlación por evento; no se infiere una transferencia efectiva si no ocurrió.

## 4. `SCM_RIGHTS` y `SCM_CREDENTIALS`

### `SCM_RIGHTS`

`SCM_RIGHTS` es el mecanismo de transferencia de FDs documentado por Linux
Unix-domain sockets. Para el envío/recepción se mantiene la cadena:

1. FD local de origen referenciado por el cmsg;
2. envío de mensaje y resultado del `sendmsg` o entrada exitosa de `sendmmsg`;
3. recepción y cmsg devuelto por `recvmsg` o entrada de `recvmmsg`;
4. FD nuevo realmente instalado en el proceso receptor, posiblemente con
   `FD_CLOEXEC`;
5. identidad del objeto/open file description y cualquier uso posterior.

El número entero de FD de origen no es identidad suficiente del FD nuevo.
Transporte, descriptor adquirido y uso posterior no se colapsan en una sola
observación. La relación S09 se mantiene separada de la superficie de socket
que transporta el cmsg.

### `SCM_CREDENTIALS`

`SCM_CREDENTIALS` transmite datos de credenciales/identidad; **no transfiere
FDs** y no es por sí mismo S09. La presencia de `SCM_CREDENTIALS` puede ser
necesaria para atribuir emisor/receptor y analizar una relación distinta, pero
no se convierte en `SCM_RIGHTS`, S09 o S10 por analogía. Payload ordinario
tampoco es capacidad FD.

## 5. `pidfd_getfd`: S03 y S09 coexisten

La documentación Linux `pidfd_getfd(2)` indica que la syscall asigna un
descriptor en el proceso llamante que duplica el descriptor `targetfd` del
proceso referido por `pidfd`, refiriendo ambos al mismo open file description.
El FD obtenido puede usarse por el caller; la operación requiere
`PTRACE_MODE_ATTACH_REALCREDS` y actualmente `flags` debe ser cero.

La conclusión S09 es una **cross-membership**, no sustitución de S03:

- **S03 YES existente:** adquisición y lifecycle de la entrada FD local,
  incluyendo el `FD_CLOEXEC` devuelto, bajo la decisión registrada en
  [018-adjudicacion-documental-lote-03-s03.md](./018-adjudicacion-documental-lote-03-s03.md).
- **S09 YES de este lote:** adquisición interproceso de la capacidad asociada
  al FD remoto, sujeta a pidfd, targetfd y autorización.
- **Fuera de esta adjudicación:** uso posterior del recurso, efectos S02/S05/
  S06/S07/S08 y fases/relaciones S10/S11.

La ausencia de `SCM_RIGHTS` no excluye S09 en este caso: la definición S09
incluye expresamente la adquisición directa documentada mediante
`pidfd_getfd`.

## 6. Cruces de superficie

Los cruces siguientes describen dimensiones independientes; sólo S09 recibe
una decisión en este lote. No se crean nuevas membresías en las demás
superficies.

| Candidatura YES | S02 payload I/O | S03 FD lifecycle | S05 file-backed mapping | S06 anonymous/memfd | S07 IP | S08 AF_UNIX | S10 IPC/coordination | S11 process/exec |
|---|---|---|---|---|---|---|---|---|
| `sendmsg` 46 | iovec/payload es independiente de ancillary rights. | FD origen y flags/lifecycle del descriptor se mantienen aparte. | Objeto pasado puede ser FD file-backed; depende del objeto, no del syscall. | Puede pasarse FD memfd; no adjudica S06. | Socket IP puede ser contexto de socket, sin inferir que rights esté soportado en esa familia. | `unix(7)` documenta UNIX-domain socket como mecanismo SCM_RIGHTS; transporte AF_UNIX separado de capability pass. | Coordinación/proceso peer no vuelve cada mensaje S10. | Identidad/fase del emisor y peer para correlación; no es herencia exec. |
| `recvmsg` 47 | Payload recibido es independiente de FDs. | FD instalado, `MSG_CMSG_CLOEXEC`, close/dup e identidad local son dimensión S03. | FD recibido puede apuntar a archivo mapeable; mapping/uso posterior queda aparte. | FD puede ser memfd; no adjudica S06. | Socket IP no convierte uso en S09 si no se satisface rights; soporte por familia no se extrapola. | AF_UNIX canal documentado para recepción SCM_RIGHTS; no se confunde S08 con la capacidad. | El origen/IPC puede contextualizarse; S10 no se adjudica por ancillary. | Proceso receptor/credenciales y fase son datos de correlación, no herencia. |
| `recvmmsg` 299 | Payload por cada mensaje recibido va por S02 si se transfiere. | Descriptores instalados por entrada y su lifecycle local se separan. | Posible tipo del objeto recibido, no decidido aquí. | Posible objeto memfd, no decidido aquí. | Family del socket es contexto; el rights debe probarse por entrada. | AF_UNIX cuando soportado; transporte por entrada y adquisición no se colapsan. | Varios mensajes no adjudican IPC/coordination adicional. | Receptor/peer/fase se correlacionan por entrada. |
| `sendmmsg` 307 | Payload por mensaje permanece en S02. | Descriptores de origen/lifecycle no se cierran por enviar SCM_RIGHTS. | Posible FD de archivo; no adjudica S05. | Posible FD memfd; no adjudica S06. | Family del socket es contexto; no inferir paso por cualquier socket IP. | AF_UNIX cuando la variante soportada lo permite; S08 y S09 son dimensiones distintas. | No adjudica S10 por envío múltiple. | Emisor/peer/fase se correlacionan por mensaje; no es herencia exec. |
| `pidfd_getfd` 438 | Sólo uso posterior que efectivamente transfiera payload podría cruzar S02. | S03 YES ya adjudicado para FD local resultante; no se modifica. | Depende del objeto/file-backed asociado al FD; no inferir mapping. | Depende del objeto, incluido posible memfd; no inferir S06. | FD obtenido podría referir a socket IP, pero pidfd_getfd no es networking S07. | FD obtenido podría referir a AF_UNIX, pero pidfd_getfd no es transporte S08. | Relación entre procesos relevante; no sustituye a S09 ni adjudica S10. | PIDFD, proceso referenciado y fase importan; no es herencia por exec. |

## 7. Exclusiones y UNKNOWN residuales

- Payload-only `sendmsg`/`sendmmsg` y recepción payload-only
  `recvmsg`/`recvmmsg`: **fuera de S09**, pues no pasan/adquieren FD.
- `SCM_CREDENTIALS` sin `SCM_RIGHTS`: **fuera de S09**; es dato de
  credenciales, no capability FD.
- Uso posterior del FD recibido: no queda adjudicado por S09 y debe cruzarse
  con la superficie de operación/recurso correspondiente.
- Emisor exitoso pero receptor no correlacionado, `MSG_CTRUNC`, mensajes
  múltiples con retorno parcial y fallos: la relación semántica condicional
  no afirma resultado de transferencia de cada evento.
- Variantes de `SCM_RIGHTS` fuera de la familia/condiciones documentadas,
  opciones/cmsgs no revisados y reachability/uso del workload quedan
  **UNKNOWN para cierre operativo**, sin ampliar o retirar las cinco
  relaciones S09 adjudicadas.
- No hay decisión **S09 NO** para una fila completa en este lote: excluir
  subvariantes payload-only/credential-only no equivale a excluir la syscall
  como un todo.

## 8. Materialización canónica

La convención existente materializa membresías aceptadas en
`A_PRE_0_SURFACE_MANIFEST.json` mediante `static_disposition_review`:

- `candidate_membership_status` queda
  `PARTIALLY_HUMAN_ADJUDICATED_BY_SURFACE`;
- el contexto de superficie S09 queda
  `HUMAN_ADJUDICATED_CANDIDATE` y contiene decisión YES y alcance;
- `surface_membership_adjudications` registra relación, rationale,
  referencia a este checkpoint y `disposition_unchanged: UNKNOWN`.

Se materializaron exclusivamente las cinco relaciones S09 decididas arriba.
Las demás superficies candidatas de esas filas no se alteraron. En
`pidfd_getfd` se preservó la adjudicación S03 previa y se añadió S09 como
cross-membership separada. `static_disposition_review.classification_status`
y todas las disposiciones generales permanecen `UNKNOWN`. No se modificó el
ledger, porque la convención observada registra estas decisiones por fila en
el manifiesto; el ledger mantiene el conteo y estado global.

## 9. Evidencia y límites

- **Syscall table target-bound:** manifiesto, ABI nativa x86_64; hash
  `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
  Establece presencia/nombre/número de las filas, no su efecto.
- **Man-pages Linux 6.19**, snapshot consignado en checkpoints previos como
  obtenido `2026-09-09`:
  [`sendmsg(2)`](https://man7.org/linux/man-pages/man2/sendmsg.2.html),
  [`recvmsg(2)`](https://man7.org/linux/man-pages/man2/recvmsg.2.html),
  [`sendmmsg(2)`](https://man7.org/linux/man-pages/man2/sendmmsg.2.html),
  [`recvmmsg(2)`](https://man7.org/linux/man-pages/man2/recvmmsg.2.html),
  [`unix(7)`](https://man7.org/linux/man-pages/man7/unix.7.html),
  [`cmsg(3)`](https://man7.org/linux/man-pages/man3/cmsg.3.html) y
  [`pidfd_getfd(2)`](https://man7.org/linux/man-pages/man2/pidfd_getfd.2.html).
  Documentan ancillary data, `SCM_RIGHTS`, separación de credenciales,
  extensiones `mmsghdr`, `MSG_CMSG_CLOEXEC` y adquisición directa con check de
  permisos. Son semántica general de Linux, no prueba de uso por TALOS o de
  cada variante presente en el workload.
- **A-PRE local:** filas candidatas, ABI/estado global y crosswalk de S03
  `pidfd_getfd` en el manifiesto; checkpoint 018 para decisión S03. La
  adjudicación S03 no se reutilizó como evidencia suficiente para S09; el
  fundamento S09 es semántica directa del syscall más la definición dada.

No se ejecutaron TALOS, FastAPI, probes ni workloads para inferir semántica.
No se extrapoló desde otra ABI.

## 10. Invariantes y verificación final

- Candidaturas adjudicadas: **5**; **5 YES**, **0 NO**, **0 UNKNOWN** en el
  alcance relacional definido. Subvariantes sin evidencia de transferencia
  efectiva, soporte específico, correlación o uso no se declaran observadas.
- Membresías S09 materializadas en manifiesto: `sendmsg` 46, `recvmsg` 47,
  `recvmmsg` 299, `sendmmsg` 307 y `pidfd_getfd` 438.
- Cross-membership `pidfd_getfd`: S03 YES previo preservado + S09 YES nuevo.
- `SCM_CREDENTIALS` no se clasifica como S09; S02/S03/S05/S06/S07/S08/S10/S11
  no se modifican ni adjudican por arrastre.
- Disposiciones generales: **385/385 UNKNOWN**, **0** disposiciones finales;
  `inventory.frozen=false`; A-PRE-0 **NOT READY**; A-PRE-1
  **NOT AUTHORIZED / NOT EXECUTED**.
- No se modificaron ledger ni `requirements.lock`; E5/Qwen, modelos, corpus,
  bases de datos protegidas, producción e infraestructura permanecen intactos.
- No hubo ejecución TALOS ni actividad dinámica de producción. No se ejecutó
  FastAPI, workload, provider, benchmark, probe, tests o A-PRE-1.
- Sin staging ni commit; cambios ajenos del worktree preservados.
- Resultado: Lote S09 adjudicado documentalmente; no avanzar a S10 hasta
  revisión/cierre de este checkpoint.
