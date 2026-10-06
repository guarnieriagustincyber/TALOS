# Reconciliación global A-PRE-0 post-S16 — detenida por discrepancia

Fecha: 2026-10-01

## 1. Alcance, modo y regla de parada

Reconciliación iniciada en modo documental/read-only: `OBSERVE → MEASURE →
CORRELATE → CLASSIFY`. No se adjudicaron relaciones, no se promovieron leads,
no se cambió el predicate, ni se ejecutó TALOS, A-PRE-1, workloads, probes,
tests o actividad dinámica.

**Estado: DETENIDA antes de completar el crosswalk global.** El manifiesto
contradice el estado de partida respecto de S02: las 18 syscalls que componen
la lista nuclear de S02 permanecen como `UNREVIEWED_CANDIDATE`, sin decisión
S02 en sus adjudicaciones por fila. El checkpoint 016 adjudica como EXCLUDED
19 relaciones adicionales, no esas 18 relaciones nucleares. La contradicción
se registra sin resolverla por inferencia. No se deben usar los conteos
parciales siguientes como un crosswalk completo de las 385 syscalls.

## 2. Snapshot de integridad

Snapshot tomado antes de crear este checkpoint:

| Elemento | Valor |
|---|---|
| HEAD | `f81134fc2293916210d53c8065f3a0049e52b0b4` |
| Working tree | Sucio; se preservaron todos los cambios preexistentes. |
| Manifiesto SHA-256 | `866b2dd8cbf88db6918f3091851f2ba7ef3f240ce6e29726650b9065c79a9219` |
| Ledger SHA-256 | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` SHA-256 | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| `checkpoints/index.md` SHA-256 | `b4d9f305ad3bed13d44d395553d0cb011da9b00216bb647be5d2f7c6f251928e` |

El hash del manifiesto coincide con el valor posterior a materializar S16
registrado en [checkpoint 041](./041-adjudicacion-documental-lote-16-s16.md).
Ledger y lock coinciden con sus hashes baseline allí registrados. El índice
no tenía hash previo registrado para comparación; el hash de arriba es el
observado. Las decisiones S06–S08 que no aparecen como membresías
materializadas en el manifiesto están documentadas como deliberadamente no
materializadas en sus respectivos checkpoints; no se corrigieron.

Digest semántico S01–S15, con la metodología de checkpoint 041:
`cd9e375f70062982f5500dd2acc3ad64e00a880f649b00dd75b9df6e177b2378`
(coincide con el valor registrado antes de S16). Fingerprint semántico
calculado para S16 en este snapshot:
`c7d5896cc119ab60651019bb57410ea2c868dd56801a33412b86a6640af60522`.
No hay un digest semántico previo por superficie con el que comparar S16.

## 3. Estado global medido y discrepancia S02

El JSON del manifiesto se pudo parsear. El contrato y ledger registran:

- 385 filas nativas; 385 nombres y números únicos.
- 385/385 disposiciones globales `UNKNOWN`; cero disposiciones finales.
- `inventory.frozen=false`; `runtime_effect_disposition_count=0`.
- A-PRE-0 `NOT_READY`; A-PRE-1 `NOT AUTHORIZED / NOT EXECUTED`.
- Resumen histórico en el manifiesto: 27 casos, 16 `OBSERVED`, 11 `BLOCKED`,
  17 filas con casos y cero casos elegibles para el predicate actual.

### Discrepancia objetiva registrada — S02

Las 18 syscalls del array `surfaces[S02].syscalls` son:
`read` (0), `readv` (19), `pread64` (17), `preadv` (295), `preadv2` (327),
`write` (1), `writev` (20), `pwrite64` (18), `pwritev` (296), `pwritev2`
(328), `fsync` (74), `fdatasync` (75), `sync_file_range` (277), `sendfile`
(40), `splice` (275), `tee` (276), `vmsplice` (278) y `copy_file_range`
(326). En las 18 filas, el contexto S02 sigue siendo
`UNREVIEWED_CANDIDATE`; no existe una decisión S02 YES/NO por fila.

El [checkpoint 016](./016-adjudicacion-documental-lote-02-s02.md) adjudica
EXCLUDED 19 referencias S02 distintas (p. ej. readiness, offset, locks,
writeback y page-cache); especifica que esa exclusión no asigna las filas a
otras superficies. No resuelve las 18 relaciones nucleares enumeradas arriba.
Por tanto, el enunciado de que S02 está cerrado no concuerda con el estado
machine-readable. No adjudicar ni materializar esas relaciones en esta
reconciliación.

### Decisiones documentales no materializadas

Los checkpoints 024, 026 y 028 declaran expresamente que no materializan sus
decisiones en el manifiesto:

- S06: 9 YES condicionales y una relación `UNKNOWN`; el manifiesto conserva
  candidaturas S06 sin decisión en fila.
- S07: 17 YES condicionales; decisiones documentadas en checkpoint, no
  materializadas.
- S08: 18 YES condicionales en checkpoint; decisiones documentadas, no
  materializadas. El array actual `surfaces[S08].syscalls` tiene 16 elementos
  (incluye `socketpair` 53, no `setsockopt` 54 ni `getsockopt` 55). El
  checkpoint 028 revisa las 17 operaciones S07 más `socketpair` y documenta
  18 YES, incluidos 54 y 55. La no materialización fue explícita; se registra
  como límite de la representación canónica y no se “sincroniza” aquí.

Estas diferencias requieren mantener separadas la decisión documental en
checkpoint y la relación machine-readable materializada. Su agregación no se
completó por la regla de parada.

El contrato conserva los valores históricos `rows_with_candidate_surface_context=204`
y `rows_without_surface_candidate_remain_unknown=181`. No se reinterpretan ni
actualizan durante esta tarea.

## 4. Crosswalk de memberships — parcial, no total global

Los conteos siguientes son decisiones YES registradas por superficie, no
disposiciones de syscall ni certificación de cobertura. Se contabilizan
S06–S08 desde sus checkpoints aunque no estén materializadas en el manifiesto.
S02 se deja en cero YES documentados y con sus 18 relaciones nucleares
UNKNOWN, no porque se haya decidido NO. S14 cuenta interfaces de biblioteca,
no filas syscall.

| Superficie | YES registrados | Estado/límite que impide tratarlo como crosswalk completo |
|---|---:|---|
| S01 | 13 | 4 relaciones NO y 7 UNKNOWN documentadas en checkpoint 014; restantes referencias no se reabren. |
| S02 | 0 | 18 relaciones nucleares permanecen `UNREVIEWED_CANDIDATE`; 19 exclusiones son leads distintos (checkpoint 016). |
| S03 | 9 | Decisiones YES con alcance condicional según checkpoint 018. |
| S04 | 35 | 5 leads siguen UNKNOWN; `umask` excluido (checkpoint 020). |
| S05 | 6 | `madvise` permanece UNKNOWN; otras rutas no promovidas (checkpoint 022). |
| S06 | 9 | Decisiones del checkpoint 024; no materializadas en manifiesto. |
| S07 | 17 | Decisiones del checkpoint 026; no materializadas en manifiesto. |
| S08 | 18 | Decisiones del checkpoint 028; no materializadas; representación array de 16, véase §3. |
| S09 | 5 | YES condicionados (checkpoint 030). |
| S10 | 31 | Además 6 NO; condiciones de comando/operación en checkpoint 032. |
| S11 | 17 | YES condicionados; otros leads permanecen sin promover (checkpoint 034). |
| S12 | 3 | YES; límites de interfaz/operación en checkpoint 036. |
| S13 | 6 | YES; evidencia BLOCKED independiente y acotada en checkpoint 038. |
| S14 | 9 interfaces | API/librería; no son memberships syscall (checkpoint 039). |
| S15 | 3 | `ioctl` permanece UNKNOWN a nivel familia (checkpoint 040). |
| S16 | 33 | YES condicionales materializados; 51 leads siguen no promovidos (checkpoint 041). |
| **Suma documental parcial** | **205 syscall-relaciones + 9 interfaces S14** | **No es total adjudicado completo mientras S02 y las diferencias de representación no estén resueltas documentalmente.** |

No se informa un número autoritativo de syscalls únicas con una o varias
memberships, ni de syscalls sin membership: esos totales dependerían de
resolver la discrepancia S02 y de consolidar consistentemente decisiones
checkpoint-only sin materializarlas por inferencia. El conteo global queda
**UNKNOWN / no reconciliado**. Las condiciones por flags, ABI, recursos,
familia de socket, comandos multiplexados y backing object se mantienen en
las adjudicaciones fuente; no se aplanan a decisiones genéricas aquí.

## 5. Leads S16 no promovidos (51)

Los 51 elementos abajo aparecen en `no_candidate_review` con estado
`POTENTIAL_EXISTING_SURFACE_REQUIRES_SCOPE_CONFIRMATION` y referencia S16.
Clasificación común: **`DOCUMENTED_UNPROMOTED`**. La base es comparación
estática por nombre, no una adjudicación. En cada caso el bloqueo actual es
confirmar semántica, argumentos/recursos, rutas alternativas, fase y
aplicabilidad al threat model; se necesita evidencia documental target-bound
de esos ejes. Las referencias adicionales a otras superficies, si las hay,
son sólo las registradas en el manifiesto y no se convierten en membership.

| NR | Syscall/API | Origen y superficie potencial | Estado / motivo / evidencia requerida |
|---:|---|---|---|
| 63 | `uname` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 97 | `getrlimit` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 99 | `sysinfo` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 102 | `getuid` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 103 | `syslog` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 104 | `getgid` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 107 | `geteuid` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 108 | `getegid` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 115 | `getgroups` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 118 | `getresuid` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 120 | `getresgid` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 134 | `uselib` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 135 | `personality` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 139 | `sysfs` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 141 | `setpriority` | `no_candidate_review` / S16 (también refiere S11) | `DOCUMENTED_UNPROMOTED`; referencias no adjudicadas. Confirmar alcance por superficie y evidencia indicada arriba. |
| 153 | `vhangup` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 154 | `modify_ldt` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 158 | `arch_prctl` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 159 | `adjtimex` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 160 | `setrlimit` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 163 | `acct` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 164 | `settimeofday` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 167 | `swapon` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 168 | `swapoff` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 169 | `reboot` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 170 | `sethostname` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 171 | `setdomainname` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 172 | `iopl` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 173 | `ioperm` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 174 | `create_module` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 177 | `get_kernel_syms` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 178 | `query_module` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 205 | `set_thread_area` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 211 | `get_thread_area` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 212 | `lookup_dcookie` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 248 | `add_key` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 249 | `request_key` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 250 | `keyctl` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 251 | `ioprio_set` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 252 | `ioprio_get` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 305 | `clock_adjtime` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 444 | `landlock_create_ruleset` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 445 | `landlock_add_rule` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 446 | `landlock_restrict_self` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 457 | `statmount` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 458 | `listmount` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 459 | `lsm_get_self_attr` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 460 | `lsm_set_self_attr` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 461 | `lsm_list_modules` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 467 | `open_tree_attr` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |
| 470 | `listns` | `no_candidate_review` / S16 | `DOCUMENTED_UNPROMOTED`; confirmar relación semántica, argumentos/recursos, rutas, fase y threat model. |

No se generó una membership por ninguno de estos 51 leads. Cuando una
referencia nombra otra superficie, la relación se mantiene sólo como lead;
no implica que esa superficie ya lo haya adjudicado.

## 6. UNKNOWN, cobertura histórica y rutas alternativas

Se mantienen separados:

- **Membership UNKNOWN:** la pertenencia de una syscall/API a una superficie
  no tiene decisión suficiente. Casos relevantes identificados antes de
  detenerse: las 18 syscalls nucleares S02; `ioctl` como familia S15; y los
  UNKNOWN expresos de S01, S04, S05 y S15 en sus checkpoints.
- **Disposición global UNKNOWN:** 385/385 filas continúan sin disposición
  final, incluso cuando existe una relación de superficie YES.

Cobertura histórica: únicamente el registro ya existente (27 casos: 16
`OBSERVED`, 11 `BLOCKED`, ninguno elegible para el predicate actual). No se
repitió ni amplió evidencia. Deben preservarse los scopes originales, en
particular:

- `ioctl(FIONREAD=0x541B)` `OBSERVED` sólo para el pipe sintético indicado en
  checkpoint 040; no cierra la familia `ioctl`.
- La evidencia native AIO/io_uring `BLOCKED` continúa limitada a syscall,
  variante, perfil/hash y scope ya documentados en checkpoints 036/038; no se
  extrapola.
- La evidencia de FD injection y `MAP_SHARED` inyectado sigue etiquetada
  como sensor-sensitivity; no demuestra higiene normal del launcher.
- No hay evidencia `BLOCKED` global para `bpf`, `perf_event_open` o
  `userfaultfd`; propuestas default-deny no son enforcement probado.
- Resultados históricos AF_UNIX con FD heredado no se generalizan a otras
  familias, rutas ni adquisición de FD.

No se completó la tabla exhaustiva de effect coverage ni la clasificación por
ruta alternativa. Pathname/dirfd, FD heredado/duplicado, `SCM_RIGHTS`,
pidfd, mappings, namespaces, workers/libc, APIs multiplexadas y variantes
ABI/flags permanecen con sus condiciones en los checkpoints fuente; donde no
exista evidencia específica, su estado para cobertura/readiness sigue
`UNKNOWN`. Esta sección es una limitación registrada, no un cierre.

## 7. Predicate formal A-PRE-0 y primer bloqueo

Predicate del ledger: `A_PRE_0_READY`, versión 2, `result=false`. Sus checks
requieren, entre otros, inventario congelado e identidad target; alcance ABI
y enforcement de compat excluidos; set de superficies exacto; cada caso/ruta
con estado `OBSERVED`/`BLOCKED` y referencias válidas; prueba para el scope
declarado; rutas alternativas explícitas; snapshot/policy/platform
consistentes; evaluación de sensors por separado; higiene FD del launcher
independientemente calificada; cero UNKNOWN; evidencia no faltante/inválida/
contradictoria; collector/builder/verifier fail-closed; y cero ejecución/
colección TALOS durante A-PRE-0.

El ledger registra actualmente causas false: `inventory.frozen=false`;
firma OpenPGP de la fuente no verificada; disposiciones syscall y particiones
finitas incompletas; trazabilidad estática de callsites/dependencias
incompleta; enforcement de ABI compat no calificado; hash de especificación
normativa ausente del overlay calificado; dominios/rutas requeridas UNKNOWN;
effect coverage UNKNOWN/incompleta; y falta de validador ejecutable
independiente del ledger.

**Primer bloqueo objetivo por orden del predicate:** `inventory.frozen is
true` falla: bloqueo de tipo **inventory gap**. También permanece el gap de
disposición global 385/385 UNKNOWN. No se intenta resolverlo aquí.

- A-PRE-0 permanece `NOT READY`.
- A-PRE-1 permanece `NOT AUTHORIZED / NOT EXECUTED`.
- El cierre de S01–S16 no cambia el predicate ni autoriza ejecución.

## 8. Cruces y condición de reanudación

No se terminó la auditoría de todas las fronteras solicitadas (S01↔S04,
S02↔S03, rutas de mappings, sockets/FD passing, procesos/IPC, AIO y S15/S16).
Las relaciones ya explícitas en el manifiesto y los límites de los
checkpoints permanecen vigentes; no se atribuyeron efectos de worker,
pathname, FD, mapping, namespace o API multiplexada a otra superficie sin
decisión específica.

**Condición para reanudar:** reconciliar documentalmente, sin inferencia, el
estado de las 18 candidaturas nucleares S02 con su autoridad de decisión y
registrar cómo se representa esa decisión en el crosswalk canónico. No
materializar cambios como parte de este checkpoint. Hasta entonces, la tabla
global de superficies únicas/múltiples/sin membership, el cierre integral de
UNKNOWN y las rutas alternativas se consideran no finalizados.

## 9. Verificaciones y límites de esta captura

En la inspección read-only el manifiesto y ledger se parsearon como JSON. El
snapshot previo a este checkpoint conserva los hashes de ledger y
`requirements.lock` de sus baselines y el digest semántico S01–S15 de
checkpoint 041. Las verificaciones finales requeridas (`git diff --check`,
estado final del árbol y recuentos) se ejecutan después de registrar este
checkpoint. No se modificaron el manifiesto, ledger, `requirements.lock`,
seccomp, código funcional, E5/Qwen, corpus, modelos ni bases protegidas.

No se ejecutó TALOS, suite, parser dinámico, workload, probe, A-PRE-1 ni
actividad dinámica.
