# Adjudicación documental — lote 14, S14 POSIX AIO

Fecha: 2026-10-01

## 1. Alcance, fuente de candidaturas y baseline

Esta adjudicación cubre exclusivamente las nueve interfaces de biblioteca
enumeradas previamente en `surfaces[id=S14].library_interfaces` del
manifiesto target-bound. No existía un checkpoint separado de preparación
S14; no se añadieron candidaturas a partir de conjeturas. El binding genérico
“Python POSIX AIO bindings, if present” de la sección de trazabilidad no se
trata como una décima API concreta: su mapping continúa `UNKNOWN`.

Hashes verificados antes de editar:

| Artefacto | SHA-256 |
|---|---|
| Manifiesto `files/A_PRE_0_SURFACE_MANIFEST.json` | `1e4a95988b13e1e7c9d978fc14c268a3b6bc5e03d5541b0b52fa191185d59a83` |
| Ledger `files/A_PRE_0_QUALIFICATION_LEDGER.json` | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |

Estado previo:

- S10: 31 YES / 6 NO.
- S11: 17 YES.
- S12: 3 YES.
- S13: 6 YES.
- Disposiciones globales: 385/385 `UNKNOWN`; cero finales.
- `inventory.frozen=false`.
- A-PRE-0: `NOT READY`.
- A-PRE-1: `NOT AUTHORIZED / NOT EXECUTED`.

## 2. Doctrina S14

S14 es la superficie de API/librería POSIX AIO y wrappers equivalentes
documentados. La membership identifica el uso de la interfaz a ese nivel;
no clasifica como S14 una syscall por el mero hecho de que una implementación
de biblioteca pueda invocarla.

Las nueve interfaces existentes fueron adjudicadas:

| Interfaz | Decisión | Fundamento y límite |
|---|---|---|
| `aio_read` | **YES** | API POSIX AIO que declara una solicitud de lectura asíncrona. La lectura/payload efectivo se atribuye a las superficies syscall correspondientes. |
| `aio_write` | **YES** | API POSIX AIO que declara una solicitud de escritura asíncrona. Payload y mutaciones efectivas no se absorben en S14. |
| `lio_listio` | **YES** | Interfaz de lista para declarar/someter solicitudes AIO; cada operación subyacente se clasifica por separado. |
| `aio_error` | **YES** | Consulta el estado de una solicitud POSIX AIO en la capa de biblioteca; no prueba por sí misma un efecto de payload. |
| `aio_return` | **YES** | Recupera el resultado de una solicitud AIO completada en la capa de biblioteca; no clasifica las syscalls del worker. |
| `aio_suspend` | **YES** | Espera estado/completion de solicitudes a través de la API POSIX AIO. Timeout, señales y mecanismo de espera son dimensiones separadas. |
| `aio_cancel` | **YES** | Expone cancelación a nivel de API POSIX AIO; su resultado depende del estado/implementación y no implica la syscall Linux native `io_cancel`. |
| `aio_fsync` | **YES** | Declara una solicitud asíncrona de sincronización asociada a un descriptor; los efectos de sincronización concretos y sus syscalls permanecen aparte. |
| `aio_init` | **YES** | Interfaz de inicialización de implementación ya listada en S14. Su disponibilidad depende de la libc enlazada; YES no afirma que exista en el runtime target ni que sea alcanzable. |

**Resultado:** 9 YES, 0 NO, 0 UNKNOWN entre las candidaturas explícitas
preexistentes. Se materializaron únicamente estas nueve memberships de
interfaz S14. No se creó membership S14 para una syscall ni se añadió API
adicional.

## 3. Límite entre API, workers y efectos

POSIX AIO no absorbe los efectos de sus workers. Cuando una interfaz S14
produce trabajo, las operaciones observables se atribuyen a las superficies
canónicas correspondientes, según la operación real:

- S02: payload I/O.
- S03: lifecycle/higiene de FDs.
- S04: mutación del filesystem.
- S05: mappings file-backed.
- S06: memoria anónima/memfd.
- S07: red IP.
- S08: AF_UNIX.
- S09: passing de FDs/capacidades.
- S10: IPC, coordinación o señales.
- S11: procesos, exec y terminación de workers.
- S12: interfaz io_uring, sólo si esa interfaz es la que se invoca.
- S13: Linux native AIO, sólo si sus syscalls son las que se invocan.

La lista de S14 sigue siendo la lista previa de nueve interfaces. El
manifiesto registra ahora sus decisiones en
`library_interface_membership_adjudications`; no se generaron filas
syscall S14. El binding Python POSIX AIO genérico conserva su estado de
trazabilidad `UNKNOWN` hasta identificar runtime/dependencia e implementación
concretos. No se adjudicaron syscalls worker por inferencia ni se promovieron
leads.

## 4. Independencia de S13 y evidencia BLOCKED

S13 conserva sus seis memberships YES y su evidencia histórica
`BLOCKED`/`EPERM` únicamente como effect coverage de las syscalls Linux
native AIO probadas bajo `a-pre-native-async-deny-v1` y el hash ya registrado.
Esa evidencia no fundamenta ninguna decisión S14, no se extrapola a POSIX AIO
ni a sus wrappers/libc/workers, y no se afirma que la invocación de una API
S14 haya sido bloqueada.

`aio_cancel` (API S14) y `io_cancel` (syscall S13) son interfaces distintas.
Análogamente, el uso eventual de `io_submit`/`io_getevents` por alguna
implementación no convierte esas syscalls en APIs S14 ni prueba el mecanismo
de una libc determinada.

## 5. Estado posterior y verificaciones

- S14: nueve relaciones YES, materializadas sólo como memberships de
  interfaces de biblioteca.
- S01–S13: sin cambios; hashes semánticos de relaciones previas preservados.
- S10: 31 YES / 6 NO; S11: 17 YES; S12: 3 YES; S13: 6 YES.
- Disposiciones globales: 385/385 `UNKNOWN`; cero finales.
- `inventory.frozen=false`.
- A-PRE-0: `NOT READY`.
- A-PRE-1: `NOT AUTHORIZED / NOT EXECUTED`.
- Ledger y `requirements.lock` permanecen byte-identical.
- No se ejecutaron TALOS, workloads, probes ni actividad dinámica.
- No se modificaron seccomp, código funcional, E5/Qwen, corpus, modelos ni
  bases protegidas.
- No se avanzó a S15.
