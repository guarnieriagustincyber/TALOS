# Adjudicación documental — lote 13, S13 Linux native AIO

Fecha: 2026-10-01

## 1. Alcance y baseline

Esta adjudicación resuelve exclusivamente las seis candidaturas centrales de
[`037-preparacion-lote-13-s13.md`](./037-preparacion-lote-13-s13.md), con los
números del inventario target-bound x86_64. No adjudica S14 ni amplía el lote.

Hashes basales verificados antes de editar:

| Artefacto | SHA-256 |
|---|---|
| Manifiesto `files/A_PRE_0_SURFACE_MANIFEST.json` | `dc57a29360efa521342d8824f0ce39bc266eb6bcefd2cf3b80d1144976d4706d` |
| Ledger `files/A_PRE_0_QUALIFICATION_LEDGER.json` | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |

Estado de partida:

- S01–S12 cerradas documentalmente según sus checkpoints.
- S10: 31 YES y 6 NO dentro de 37 relaciones.
- S11: 17 YES.
- S12: exactamente 3 YES (`io_uring_setup` 425, `io_uring_enter` 426,
  `io_uring_register` 427).
- S13: seis candidaturas, todas `UNREVIEWED`.
- Disposiciones globales: 385/385 `UNKNOWN`; 0 finales.
- `inventory.frozen=false`.
- A-PRE-0: `NOT READY`.
- A-PRE-1: `NOT AUTHORIZED / NOT EXECUTED`.

## 2. Doctrina aplicada

> **S13 = interfaz Linux native AIO basada en `io_*`: lifecycle del contexto
> AIO, submission de operaciones, espera/recolección de eventos y cancelación
> de operaciones AIO.**

La membership se decide por la semántica directa de la syscall native AIO,
no porque una biblioteca POSIX AIO pudiera utilizarla indirectamente. Se
mantienen separadas membership S13, cobertura de efectos y disposición
global.

## 3. Decisiones individuales

| NR / syscall | Decisión | Fundamento, condición y límites |
|---|---|---|
| 206 `io_setup` | **YES** | Crea/configura directamente un contexto Linux native AIO. El alcance S13 comprende `nr_events`, el resultado en `ctx_idp`, el contexto creado y sus condiciones de éxito/error. El lifecycle de contexto pertenece a la interfaz native AIO; no se traslada automáticamente el identificador/recurso a S03. La observación histórica de contexto vacío es sólo ese subcaso. |
| 207 `io_destroy` | **YES** | Destruye directamente el contexto identificado por `ctx_id`; considerar validez/estado, solicitudes en vuelo, efectos de destrucción, retorno y errores. Es lifecycle del contexto native AIO, no clasificación de un recurso genérico. El caso observado sólo cubrió un contexto vacío y no limita la semántica de membership. |
| 208 `io_getevents` | **YES** | Espera/obtiene eventos de finalización del contexto AIO. El alcance incluye `ctx_id`, `min_nr`, `nr`, buffer de eventos, timeout y resultados parciales/interrupciones. La falta de un caso exitoso unfiltered no cambia la semántica directa de esta operación. Los eventos representan completions, pero su presencia no hace que la syscall sea S02. |
| 209 `io_submit` | **YES** | Somete solicitudes `iocb` al contexto. El alcance incluye `ctx_id`, `nr`, vector de solicitudes, cantidad efectivamente aceptada, errores parciales y los tipos/opcodes documentados de `iocb` (incluyendo lectura/escritura cuando corresponda). La membership es por la interfaz de submission; los efectos de payload/filesystem/red u otros siguen en sus superficies respectivas. La observación con cero solicitudes no prueba I/O. |
| 210 `io_cancel` | **YES** | Intenta cancelar directamente una operación identificada por `iocb` en un contexto y puede devolver el evento/resultado correspondiente. El alcance incluye `ctx_id`, objetivo, estado/carreras con completion, salida `io_event`, éxito y errores. La cancelación forma parte de la interfaz native AIO aunque no transfiera payload por sí misma. No se infiere que toda solicitud pendiente sea cancelable. |
| 333 `io_pgetevents` | **YES** | Variante de espera/recolección de eventos AIO con integración adicional de máscara de señales. La función principal —esperar/obtener completions— pertenece a S13; `sigset` y `sigsetsize` se conservan como condiciones de espera. Cualquier dimensión de señales/coordinación es un cruce independiente con S10; no se traslada toda la syscall a S10. La observación con mínimo cero sólo cubrió ese subcaso. |

**Resultado:** 6 YES, 0 NO, 0 UNKNOWN. Las seis relaciones S13 YES se
materializan en el manifiesto bajo las filas target-bound correspondientes.
Las disposiciones generales de esas filas permanecen `UNKNOWN`.

## 4. Materialización y separación de superficies

Se agregaron únicamente las seis relaciones humanas S13 YES en
`static_disposition_review.surface_membership_adjudications`, con alcance,
fundamento, referencia a este checkpoint y `disposition_unchanged: UNKNOWN`.
Los contextos S13 se actualizaron a `HUMAN_ADJUDICATED_CANDIDATE`. No se
alteraron las listas declarativas de syscalls por superficie, ni se
modificaron membresías S01–S12.

Se preservan expresamente estos cruces, sin adjudicar nuevas relaciones:

- **S02:** payload I/O ejecutado por solicitudes AIO.
- **S03:** FDs utilizados por `iocb`/operaciones y recursos asociados; no
  absorber el lifecycle de contexto como una clasificación FD genérica.
- **S05/S06:** buffers, memoria y mappings.
- **S07/S08:** operaciones de networking sobre sockets.
- **S09:** passing/acquisition de capacidades mediante mecanismos externos.
- **S10:** coordinación/eventos y la máscara de señales de `io_pgetevents`.
- **S11:** procesos/hilos/ejecución asíncrona; no es la interfaz AIO.
- **S12:** io_uring conserva sus tres memberships y es una interfaz distinta.
- **S14:** POSIX AIO/library workers, sin membership creada en este lote.

## 5. POSIX AIO / S14 fuera de esta adjudicación

Se mantienen fuera de S13 `aio_read`, `aio_write`, `aio_fsync`,
`aio_suspend`, `aio_error`, `aio_return`, `lio_listio`, wrappers libc y
workers internos. Son interfaces de biblioteca/contexto para el análisis
separado S14 cuando corresponda; las syscalls subyacentes se atribuyen a sus
superficies canónicas. No se creó ninguna membership S14.

## 6. Evidencia histórica BLOCKED: cobertura exacta, no fundamento

El perfil histórico es `a-pre-native-async-deny-v1`, SHA-256
`ff44e7f9573fe503fd023792d1e38c44ba8b4ac53275097559eaece82e0ea9e9`.
Los artefactos registrados son `seccomp-probe.json` (SHA-256
`350d5d8c40125417a9475ed7caa77fcd1acf15bc49f80da817a1cb17695f9d8b`) y
`isolation.json` (SHA-256
`17d94bac187ca74b008a34e192c29706e170080e25dc626e13e4b9fb81d8226d`).

El manifiesto contiene un caso histórico BLOCKED `EPERM` para cada syscall
de este lote:

| Syscall | Caso documentado | Alcance exacto registrado |
|---|---|---|
| `io_setup` 206 | `linux-aio-setup-profile-denial` | Sólo la syscall exacta bajo el perfil nombrado; la identidad de política debe estar activa en el snapshot evaluado. |
| `io_destroy` 207 | `linux-aio-destroy-profile-denial` | Sólo la syscall exacta bajo el perfil nombrado; la identidad de política debe estar activa en el snapshot evaluado. |
| `io_getevents` 208 | `linux-aio-getevents-profile-denial` | Sólo la syscall exacta bajo el perfil; no consta llamada exitosa unfiltered. |
| `io_submit` 209 | `linux-aio-submit-profile-denial` | Sólo la syscall exacta bajo el perfil nombrado; la identidad de política debe estar activa en el snapshot evaluado. |
| `io_cancel` 210 | `linux-aio-cancel-profile-denial` | Sólo la syscall exacta bajo el perfil; no consta llamada exitosa unfiltered. |
| `io_pgetevents` 333 | `linux-aio-pgetevents-profile-denial` | Sólo la syscall exacta bajo el perfil nombrado; la identidad de política debe estar activa en el snapshot evaluado. |

Estos seis casos componen, junto a los tres casos io_uring, el conjunto
histórico de 9/9 denegaciones EPERM. La clasificación `BLOCKED` sólo describe
las llamadas/casos indicados bajo ese perfil/hash. No se extrapola de una
syscall AIO a otra, a otros perfiles/rutas ni al dominio S13 completo. No se
usó como fundamento de las decisiones YES.

También constan observaciones sintéticas limitadas: setup de contexto vacío,
destroy de contexto vacío, submit con cero solicitudes y `io_pgetevents` con
mínimo cero. No se infiere de ellas una operación AIO completada. Estos
artefactos históricos no están re-vinculados al overlay calificado actual y
no se reejecutaron ni validaron en esta tarea.

```text
membership documental S13 ≠ effect coverage ≠ disposición global
```

## 7. Leads e invariantes

- No se promovieron leads adicionales; las seis candidaturas centrales
  permanecen como el alcance de S13.
- `eventfd`/`eventfd2` son contexto posible de notificación, no operaciones
  de la interfaz native AIO ni candidaturas nuevas.
- Las filas `io_uring_*` permanecen bajo S12; syscalls generales de I/O,
  scheduler o memoria no se añaden a S13 por proximidad.
- Disposiciones generales: 385/385 `UNKNOWN`; cero finales.
- `inventory.frozen=false`.
- A-PRE-0: `NOT READY`.
- A-PRE-1: `NOT AUTHORIZED / NOT EXECUTED`.
- S10 sigue en 31 YES / 6 NO; S11 conserva 17 YES; S12 conserva 3 YES.
- Ledger y `requirements.lock` byte-identical.
- No hubo ejecución de TALOS, workloads, probes ni actividad dinámica.
- No se modificaron seccomp, código funcional, E5/Qwen, corpus, modelos o
  bases protegidas.
- Los leads de S10/S11 y S13 permanecen sin promoción adicional.
- No se avanzó a S14.
