# Adjudicación documental — lote 15, S15 APIs opacas del kernel

Fecha: 2026-10-01

## 1. Alcance y baseline

Esta adjudicación se limita a las cuatro candidaturas syscall S15 ya
presentes en el manifiesto target-bound: `ioctl` 16, `perf_event_open` 298,
`bpf` 321 y `userfaultfd` 323. No se agregaron comandos ni syscalls nuevos.
La decisión sobre `ioctl` permanece acotada/UNKNOWN a nivel de familia; el
único comando concreto documentado, `FIONREAD` sobre pipe sintético, sigue
siendo un caso de efecto y no se promueve por sí mismo como membership.

Hashes verificados antes de editar:

| Artefacto | SHA-256 |
|---|---|
| Manifiesto `files/A_PRE_0_SURFACE_MANIFEST.json` | `f69bd3e6535fe6bb7ff238e69a190673b46b8b5ecc33421722be200566750e57` |
| Ledger `files/A_PRE_0_QUALIFICATION_LEDGER.json` | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Relaciones/superficies S01–S14 (digest semántico pre-edición) | `e66de4b6622683ccedf49b6c44e0b6a8f4f76341358823236339067e5c507840` |

SHA-256 del manifiesto posterior a materializar las tres relaciones S15 YES:
`11de7646449809ba82f9f75835ea682ec1959d21c9f0f75ee723baca4b21480f`.

Estado previo: 385/385 disposiciones generales `UNKNOWN`, 0 finales,
`inventory.frozen=false`, A-PRE-0 `NOT READY`, A-PRE-1
`NOT AUTHORIZED / NOT EXECUTED`. S10 = 31 YES/6 NO; S11 = 17 YES; S12 = 3
YES; S13 = 6 YES; S14 = 9 YES.

## 2. Decisiones individuales

| Candidatura | Decisión | Fundamento, alcance y condición |
|---|---|---|
| `ioctl` — NR 16 | **UNKNOWN** (familia); sin membership materializada | `ioctl(fd, request, arg)` multiplexa comandos que dependen de ABI, objeto/FD y argumentos. El único comando concreto de S15 documentado aquí es `FIONREAD` (`0x541B`) sobre un pipe sintético; su semántica y efecto observados no cierran la familia ni constituyen por sí solos decisión de membership. No se extrapola a otros comandos ni objetos. Requiere adjudicación command-by-command con FD/objeto, argumentos y efecto separados. |
| `perf_event_open` — NR 298 | **YES**, condicionado a la operación seleccionada | Es la entrada directa a la API kernel de perf events. La relación S15 comprende la interfaz `perf_event_open`; cada operación sigue particionada por `perf_event_attr` (tipo/configuración, sample/read format), `pid`, CPU, grupo/flags, objeto objetivo, permisos/capacidades y resultado efectivo. No se adjudica un tipo de evento concreto, no se afirma ocurrencia, reachability, bloqueo ni default-deny efectivo. |
| `bpf` — NR 321 | **YES**, condicionado a `cmd`/objeto | Es la entrada syscall directa a la API de comandos BPF del kernel. La membership es de la interfaz, no una adjudicación uniforme de todos los comandos: conservar `cmd`, atributos/`size` específicos y objeto afectado (por ejemplo programa, mapa o link) como particiones independientes. No se acepta una allowlist de comandos ni se afirma efecto, reachability o bloqueo. |
| `userfaultfd` — NR 323 | **YES**, para creación del mecanismo | La syscall crea el mecanismo/descriptor userfaultfd con `flags`. Limitar esta relación a creación. Configuración de features, operaciones UFFDIO de registro de rangos y recepción/procesamiento de eventos son dimensiones/operaciones posteriores que deben seguir identificadas por separado. La interacción con memoria no se absorbe en S15 (S05/S06) ni las consecuencias sobre procesos en S11. No se afirma disponibilidad, uso ni bloqueo. |

**Resultado:** 3 YES, 0 NO, 1 UNKNOWN. Sólo se materializaron las tres
relaciones S15 YES. `ioctl` permanece sin relación materializada; su
incertidumbre de familia queda registrada aquí y el caso FIONREAD permanece
sin cambios en el registro de evidencia.

## 3. Membership, effect coverage y propuesta de política

Son categorías distintas:

```text
membership S15 ≠ effect coverage ≠ propuesta de política ≠ disposición global
```

### Caso `ioctl(FIONREAD)`

El manifiesto registra `pipe-fionread` como `OBSERVED`: llamada sintética
exitosa `ioctl(FIONREAD)` sobre un pipe local sintético, retorno 0 y valor 19.
El scope explícito es sólo FIONREAD en ese pipe; los demás comandos y clases
de objeto siguen abiertos. Referencias históricas existentes:

- `EFFECT-COVERAGE-ADJUDICATION.md`: SHA-256
  `35da5881e1eb37fbb865a6573b6e00e06456b2625de4a27171369a88202579e2`.
- `isolation.json`: SHA-256
  `8ce33214167055695eaf9674299cb236a766616b25e91d0792bb40ee5d6fcb68`.
- `probe.json`: SHA-256
  `c71fa4367804b2396c4a2347e4f5b448085a3a240a4c49adb674c8dd1d4e2b6c`.

El caso cuenta únicamente como effect coverage de esa llamada/objeto
sintético; no demuestra política de producción, cobertura de decoder,
denegación global, cierre de ioctl ni membership. No se repitió ni revalidó.

### Propuestas default-deny

La definición S15 contiene una `proposed_policy` con `default: DENY`,
`admitted_operations: []`, operaciones sensitivity-only y
`enforcement_status: NOT_DEMONSTRATED`. La declaración propone default-deny
para ioctl (incluido FIONREAD), bpf, perf_event_open y userfaultfd; no acredita
implementación, enforcement, bloqueo ni membership. Esta adjudicación no
cambia esos campos ni los convierte en hechos.

### Evidencia por syscall

En las filas de `bpf`, `perf_event_open` y `userfaultfd` no hay casos
históricos específicos `OBSERVED` o `BLOCKED`; sus campos indican que no se
registró evidencia por fila. No se atribuye la propuesta de política como
evidencia. El `BLOCKED` de S13/Linux native AIO no se extrapola a S15.

## 4. Cruces preservados (sin adjudicar otras superficies)

- **S02:** payload I/O que puedan realizar operaciones posteriores.
- **S03:** FD lifecycle/hygiene de descriptores y handles.
- **S04:** mutaciones de filesystem que puedan resultar de operaciones
  posteriores.
- **S05:** memoria/mappings file-backed; rangos gestionados por userfaultfd
  no se convierten por ello en membership S05 adjudicada aquí.
- **S06:** memoria anónima/memfd y buffers.
- **S07:** IP networking.
- **S08:** AF_UNIX.
- **S09:** passing/acquisition de capacidades.
- **S10:** IPC, coordinación y señales, incluida cualquier coordinación
  asociada a procesamiento de eventos.
- **S11:** procesos, workers, exec y terminación.
- **S12:** io_uring permanece como interfaz distinta.
- **S13:** Linux native AIO permanece como interfaz distinta; sus seis YES y
  sus casos BLOCKED exactos no se alteran.
- **S14:** POSIX AIO permanece como interfaz de biblioteca distinta.
- Variantes de `perf_event_open`, comandos BPF, comandos `ioctl` y operaciones
  UFFDIO deben correlacionar cada objeto y efecto con su superficie canónica;
  no se promueven relaciones cruzadas en este lote.

## 5. Invariantes posteriores

- Candidaturas S15: 4; YES 3, NO 0, UNKNOWN 1.
- Relaciones S15 materializadas: sólo YES de `bpf`, `perf_event_open` y
  creación `userfaultfd`.
- Disposiciones globales: 385/385 `UNKNOWN`; 0 finales.
- `inventory.frozen=false`.
- A-PRE-0: `NOT READY`.
- A-PRE-1: `NOT AUTHORIZED / NOT EXECUTED`.
- S01–S14 preservadas semánticamente; S10 = 31 YES/6 NO, S11 = 17 YES,
  S12 = 3 YES, S13 = 6 YES, S14 = 9 YES.
- Ledger y `requirements.lock` byte-identical.
- No se ejecutaron TALOS, workloads, probes ni actividad dinámica.
- No se modificaron seccomp, código funcional, E5/Qwen, corpus, modelos ni
  bases protegidas.
- No se avanzó a S16.
