# Preparación documental — lote 12, S12 io_uring

Fecha: 2026-10-01

## 1. Objetivo y límites

Preparar para adjudicación humana las candidaturas de la interfaz nativa
Linux `io_uring` del inventario target-bound de 385 syscalls x86_64.

Esta preparación **no adjudica YES/NO/UNKNOWN**, no materializa memberships y
no transforma evidencia de efecto en una decisión de pertenencia. No se
ejecutaron TALOS, workloads ni probes; no se cambió el perfil seccomp, código
funcional ni artefacto del manifiesto.

## 2. Baseline e invariantes

Hashes verificados antes de esta edición:

| Artefacto | SHA-256 |
|---|---|
| Manifiesto `files/A_PRE_0_SURFACE_MANIFEST.json` | `efcd4a9898cc088c660d88b41633733745f9cc1fac4fb628f13dbe7e47b97a98` |
| Ledger `files/A_PRE_0_QUALIFICATION_LEDGER.json` | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |

Estado documental de partida:

- S10: 37 relaciones, 31 YES, 6 NO y 0 UNKNOWN; los 12 leads
  poll/select/epoll siguen sin promover.
- S11: 17 YES; sus 14 leads siguen sin promover.
- Disposiciones generales: 385/385 `UNKNOWN`; 0 finales.
- `inventory.frozen=false`.
- A-PRE-0: `NOT READY`.
- A-PRE-1: `NOT AUTHORIZED / NOT EXECUTED`.

La revisión del inventario se limitó a lectura estática. Se verificaron los
hashes basales anteriores y se mantuvieron las decisiones S10/S11 fuera del
alcance de esta preparación.

## 3. Doctrina de trabajo

> **S12 = interfaz nativa Linux io_uring: creación/configuración del ring,
> entrada de operaciones y registro/configuración de recursos mediante la
> familia io_uring.**

La membership, si se adjudica después, se refiere a la interfaz `io_uring`.
No se extiende automáticamente a cada efecto que una operación SQE pueda
producir. Por tanto, payload, filesystem, red, señales o efectos sobre
procesos enviados mediante el ring no se convierten por ello en membresías
S12 ni sustituyen sus superficies propias.

Cada una de las tres filas target-bound aparece actualmente como candidata
S12 `UNREVIEWED`, con disposición global `UNKNOWN`. En esta preparación, las
tres quedan en estado **`UNREVIEWED / PENDING HUMAN ADJUDICATION`**.

## 4. Candidaturas centrales

| NR x86_64 | Syscall | Familia | Semántica y condición que deberá revisar la adjudicación | Variantes, argumentos y recursos relevantes | Evidencia estática actual |
|---:|---|---|---|---|---|
| 425 | `io_uring_setup` | Crear/configurar ring | Solicita crear una instancia ring y devuelve su FD si tiene éxito. La llamada configura la base del ring; no demuestra que se haya enviado ni completado una operación de I/O. | `entries`, `io_uring_params`, `flags`/`IORING_SETUP_*`, features y tamaños/offsets SQ/CQ; ring kernel y FD devuelto, mappings que puedan configurarse después. | Fila target-bound presente; candidata S12 `UNREVIEWED`, disposición `UNKNOWN`. Casos históricos de setup exitoso en fixture sintético vacío y denegación por perfil (detallados en §7). |
| 426 | `io_uring_enter` | Entrada/envío/espera | Opera sobre un ring: puede entrar operaciones SQE, esperar completions o pedir wakeup/progreso según argumentos y estado del ring. El significado de una llamada concreta depende de si somete SQEs, espera o sólo solicita una operación de control. | `fd`, `to_submit`, `min_complete`, `flags` (p. ej. `IORING_ENTER_GETEVENTS`, `IORING_ENTER_SQ_WAKEUP`, extensiones admitidas) y argumentos de sigmask/`ext_arg`; ring, SQ/CQ y SQEs. | Fila target-bound presente; candidata S12 `UNREVIEWED`, disposición `UNKNOWN`. Hay caso histórico de llamada exitosa con cero SQE y caso de denegación por perfil; ninguno adjudica membership. |
| 427 | `io_uring_register` | Registro/configuración de recursos | Registra, desregistra o configura recursos/opciones relacionados con un ring. La operación concreta viene determinada por `opcode`; no todas las operaciones registran el mismo tipo de recurso. | `fd`, `opcode`, `nr_args`, `arg`; variantes de registro/desregistro de buffers, files, eventfd, personalities, restricciones y otras operaciones admitidas por el kernel; recursos y FD del ring. | Fila target-bound presente; candidata S12 `UNREVIEWED`, disposición `UNKNOWN`. Consta una denegación histórica por perfil; el manifiesto no registra variante exitosa/unfiltered para esta syscall. |

La tabla describe dimensiones para revisión; sus ejemplos de flags y
operaciones no son una partición exhaustiva ni decisiones sobre pertenencia,
reachability o cobertura.

## 5. Leads y contexto no promovido

- **Leads adicionales de syscall S12: 0 promovidos.** El alcance nativo
  solicitado queda identificado en las tres candidaturas centrales 425–427.
- Bibliotecas y wrappers userspace (por ejemplo, `liburing`) son contexto
  posible para alcanzar la interfaz, no syscalls S12 adicionales.
- Mappings de ring/buffers, `eventfd` u otros recursos auxiliares son
  mecanismos/contexto que pueden participar en una ruta; no se promueven
  syscalls del inventario sólo porque puedan ser usados junto con io_uring.
- Las operaciones SQE pueden alcanzar subsistemas adicionales. Esas
  operaciones no amplían por sí solas el conjunto de syscalls que constituye
  la interfaz nativa S12.

## 6. Cruces para revisión (sin adjudicar)

- **S02:** payload I/O que una SQE pueda solicitar; S12 identifica la
  interfaz que acepta/gestiona las operaciones, no adjudica todo el payload.
- **S03:** FD del ring y su adquisición/cierre/herencia; separar lifecycle del
  descriptor de la interfaz io_uring.
- **S05/S06:** mappings, memoria compartida y buffers usados por ring u
  operaciones; los recursos de memoria no hacen que toda operación sea S12.
- **S07/S08:** envío/recepción de red y operaciones sobre sockets mediante
  SQE; mantener la dimensión de red separada de la interfaz.
- **S09:** transferencia de capacidades por mecanismos externos; no inferir
  SCM_RIGHTS ni otra transferencia por usar un ring.
- **S10:** coordinación/asíncronía; no fusionar la interfaz io_uring con
  coordinación o señales.
- **S11:** procesos/hilos que crean, usan o heredan rings; el ciclo de vida
  del proceso permanece separado.
- El manifiesto de candidaturas también enumera rutas alternativas de
  superficie para estas filas. Su presencia requiere resolver cada cruce en
  la adjudicación, no modificar memberships existentes en esta preparación.

## 7. Evidencia dinámica histórica: sólo cobertura de efecto

El manifiesto registra para las tres syscalls S12 estos casos históricos:

| Syscall | Caso | Resultado documentado | Límite |
|---|---|---|---|
| `io_uring_setup` | `io-uring-setup-unfiltered-empty-ring` | `OBSERVED`: setup exitoso en fixture sintético sin filtro. | Sólo setup de ring vacío; no hubo SQE ni operación de I/O. Precede al perfil de denegación. |
| `io_uring_setup` | `io-uring-setup-profile-denial` | `BLOCKED`: `EPERM`. | Sólo la syscall exacta bajo el perfil nombrado. |
| `io_uring_enter` | `io-uring-enter-zero-sqe` | `OBSERVED`: llamada con cero SQE en fixture sintético sin filtro. | No evidencia ejecución de SQE; precede al perfil de denegación. |
| `io_uring_enter` | `io-uring-enter-profile-denial` | `BLOCKED`: `EPERM`. | Sólo la syscall exacta bajo el perfil nombrado. |
| `io_uring_register` | `io-uring-register-profile-denial` | `BLOCKED`: `EPERM`. | Sólo la syscall exacta bajo el perfil nombrado; no consta variante exitosa/unfiltered. |

El perfil histórico identificado en el ledger es
`a-pre-native-async-deny-v1`, SHA-256
`ff44e7f9573fe503fd023792d1e38c44ba8b4ac53275097559eaece82e0ea9e9`.
Los casos de denegación enlazan el resultado
`seccomp-probe.json` (SHA-256
`350d5d8c40125417a9475ed7caa77fcd1acf15bc49f80da817a1cb17695f9d8b`) y la
traza de aislamiento `isolation.json` (SHA-256
`17d94bac187ca74b008a34e192c29706e170080e25dc626e13e4b9fb81d8226d`).
Estos artefactos son evidencia histórica documentada; no se reejecutaron ni
se revalidaron en esta tarea. El manifiesto indica que no están re-vinculados
a un overlay calificado que contenga la especificación/manifiesto normativo
actual.

El conjunto histórico asociado al perfil contiene **9/9 casos de denegación
EPERM**: las tres syscalls io_uring de este lote y seis syscalls Linux native
AIO (`io_setup`, `io_destroy`, `io_getevents`, `io_submit`, `io_cancel`,
`io_pgetevents`). La clasificación histórica de efecto `BLOCKED` se limita a
esas syscalls/casos bajo ese perfil e identidad de política. Para S12, esto
significa únicamente que cada una de las tres llamadas exactas tuvo un caso
BLOCKED registrado; no demuestra cobertura exhaustiva de variantes ni de
SQE, no se extiende a otros perfiles/rutas/syscalls y **no decide membership
S12**. La evidencia `OBSERVED` de setup vacío y enter con cero SQE también
queda limitada a esos subcasos.

Se preserva estrictamente la separación:

```text
membership documental S12 ≠ cobertura de efectos ≠ disposición global
```

## 8. Pendientes de adjudicación humana

Para cada syscall, revisar semántica de interfaz frente a variantes/flags,
recursos involucrados, rutas alternativas, casos de éxito/bloqueo y la
condición exacta de pertenencia. En particular:

1. Determinar si las variantes de configuración/operación/registro pertenecen
   directamente a la definición de interfaz S12, sin adjudicar todos los
   efectos de las operaciones SQE a S12.
2. Decidir cómo tratar llamadas de `io_uring_enter` que esperan o despiertan
   sin someter SQEs, frente a llamadas que efectivamente someten operaciones.
3. Resolver las operaciones concretas de `io_uring_register` y sus clases de
   recursos sin inferir por nombre.
4. Mantener por separado cada cruce con S02/S03/S05/S06/S07/S08/S09/S10/S11
   y las rutas alternativas identificadas en el manifiesto.
5. Conservar los casos `OBSERVED`/`BLOCKED` dentro de su alcance: no usarlos
   para aceptar/rechazar membership ni para cerrar cobertura global.

Hasta esa revisión, las tres candidaturas permanecen
`UNREVIEWED / PENDING HUMAN ADJUDICATION`; no se registran YES/NO/UNKNOWN
adjudicados ni se materializan memberships.

## 9. Estado de salida

- Inventario: no congelado (`inventory.frozen=false`).
- Disposiciones generales: 385/385 `UNKNOWN`; cero finales.
- A-PRE-0: `NOT READY`.
- A-PRE-1: `NOT AUTHORIZED / NOT EXECUTED`.
- S10 y S11: sin cambios.
- Ledger, manifiesto, `requirements.lock`, E5/Qwen, corpus, modelos y bases
  protegidas: sin cambios en esta tarea.
- No hubo ejecución dinámica, TALOS ni workloads.
- No se avanzó a adjudicación S12.
