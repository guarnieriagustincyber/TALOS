# Checkpoint 058 — inventario cerrado de pendientes

Fecha: 2026-10-01
Alcance: consolidación de problemas pendientes en una lista sin duplicación; no
adjudica, no cambia estado canónico y no autoriza reparación.

## 1. Estado vinculante e invariantes

| Elemento | Estado |
|---|---|
| HEAD | `f81134fc2293916210d53c8065f3a0049e52b0b4` |
| `BASELINE_SPEC_AUTHORITY` | `AUTHORITY_UNRESOLVED` |
| `STOP_REASON` | `UNRESOLVED_PROVENANCE` |
| Artefacto externo `f058…` | `UNRECOVERED` |
| A-PRE-0 / A-PRE-1 | `NOT_READY` / `NOT_AUTHORIZED / NOT_EXECUTED` |
| Inventory | `frozen=false` |
| Disposición global | 385/385 `UNKNOWN` |
| Tags de lead reportados históricamente | 162 |
| Pares con provenance recoverable / partial | 96 / 61 |
| Stale counters / checkpoint-only / contador 63 | 11 / 77 / `SCOPE_UNPROVEN` |

Hashes protegidos al iniciar y al cerrar:

| Artefacto | SHA-256 |
|---|---|
| Manifest | `801f529655f1f4f250a2a374d2afa63f858a9c0875e0e3dc620d112df5f9fd6e` |
| Ledger | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Baseline spec `docs/` | `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` |
| Baseline spec `files/` | `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0` |

Se consultaron 055–057, el manifest, el ledger, el índice y los checkpoints
fuente imprescindibles entre 011–054. Sólo hubo lectura, recuento y hash
locales. No se ejecutó TALOS, FastAPI, código del proyecto, workloads,
probes, benchmarks, pruebas, validadores, ni actividad dinámica; no se accedió
a VM, DB, corpus o modelos.

## 2. Método de consolidación y unidades

La unidad de pendiente es el problema que necesita una acción distinta, no
cada aparición en un checkpoint ni cada campo repetido en manifest/ledger.
Se separan cuatro clases de unidad:

1. **Estado global por syscall:** cada una de las 385 disposiciones sigue
   `UNKNOWN`; membership de superficie no la sustituye.
2. **Relación syscall-superficie:** candidato, lead o UNKNOWN relacional.
3. **Representación/provenance:** estado histórico no materializado, cita
   parcial o autoridad de la fuente.
4. **Readiness/evidencia:** selector/valor finito, ruta de callsite y
   calificación de controles.

Una relación puede compartir syscall con otra relación o con su disposición
global, pero son preguntas distintas. En cambio, 055/056/057 cuentan varias
veces las mismas menciones y copias de métricas; esas no se suman como
pendientes separados.

## 3. Resultado ejecutivo: decisiones reales versus incidencias

### Reconciliación descriptiva 048

- El crosswalk row-wise está construido en 055 y reconciliado campo por campo
  en 056; 057 explica stale counters, provenance recuperable/parcial,
  transiciones y la anomalía `shutdown`/S07.
- **No queda una nueva decisión semántica necesaria para terminar el
  crosswalk descriptivo.** Los 61 provenance partial pueden permanecer
  explícitamente etiquetados como parciales; no hay que inventar sus citas
  para describir fielmente el snapshot.
- El contador 63 y los 11 stale no bloquean esa operación descriptiva.
- El cierre **normativo/global** de 048 sí queda bloqueado por la autoridad de
  baseline no resuelta y por las decisiones enumeradas en §8. La etiqueta de
  054/053 que dejó 048 bloqueado no se cambia en este checkpoint.

### A-PRE-0

- En el nivel actual no puede evaluarse READY: faltan decisiones globales,
  autoridad normativa recuperada, particiones finitas de cobertura,
  callsite-to-syscall trazable y calificación de enforcement ABI.
- Hay **385 unidades row-level de disposición global** que necesitan outcome
  final para dejar 385/385 `UNKNOWN`; no se afirma que sean 385 deliberaciones
  humanas independientes. Las relaciones de superficie pueden agruparse
  durante la revisión, pero no reemplazan esa unidad de salida.
- Hay **157 relaciones de lead** todavía abiertas (no 162; véase §5), y **10
  UNKNOWN relacionales explícitos**. El total 167 es de pares de relación,
  no de syscalls ni de sesiones de decisión independientes.

Por tanto, “decisiones reales” tiene dos respuestas según el cierre:

| Meta | Mínimo pendiente de decisión |
|---|---|
| Completar el crosswalk descriptivo de 385 | **0**; el entregable descriptivo ya existe. Sólo se conserva la incertidumbre explícitamente. |
| Cerrar normativamente 048 | **1 gate de provenance/autoridad** (`BASELINE_SPEC_AUTHORITY`) antes de cualquier resolución que dependa de la norma; después, 157 outcomes de lead y 10 outcomes relacionales UNKNOWN, agrupables por cuestión/superficie sin asumir que sean 167 deliberaciones independientes. |
| Desconocidos globales de A-PRE-0 | **385 outcomes row-level**, además de los outcomes relacionales anteriores, cierre de variantes/cobertura y trazabilidad/evidencia de readiness. No son necesariamente 385 tareas independientes. |

El punto anterior no suma 385+167 como una cifra de “decisiones humanas”:
describe unidades de salida diferentes y parcialmente solapadas. El número
de sesiones de deliberación no se puede derivar sin definir una política de
agrupación que todavía no está autorizada.

## 4. Clasificación principal y set mínimo de pendientes

Cada fila de la tabla tiene exactamente una categoría principal de las cinco
permitidas. Una misma iniciativa puede tener varios subproductos; sólo se
separa cuando exige una acción distinta.

| ID | Pendiente/problema único | Evidencia disponible | Categoría principal | Decisión/acción que faltaría | Bloquea 048 descriptivo | Bloquea 048 normativo | Bloquea A-PRE-0 |
|---|---|---|---|---|---|---|---|
| P01 | Autoridad única de `A_PRE_0_BASELINE_SPEC.md` y origen externo `f058…` | CP051–053, ledger y dos copias con hashes distintos; el ledger identifica `f058…` como ausente del overlay | `PROVENANCE_UNRESOLVED` | Recuperar/establecer por evidencia la fuente y autoridad aplicable; no elegir por intuición | No | Sí | Sí |
| P02 | 157 relaciones de lead aún sin outcome relacional | 96 con referencia documental exacta de lead; 61 con evidencia parcial del lote/superficie; listado completo en §5 | `NORMATIVE_DECISION_REQUIRED` | Decidir outcome de cada par por alcance/variantes bajo autoridad normativa; los 61 mantienen además provenance parcial | No | Sí | Sí |
| P03 | 10 UNKNOWN relacionales explícitos | CP014/022/024/040; 055/056 identifican los 10 pares por superficie y NR | `NORMATIVE_DECISION_REQUIRED` | Resolver o preservar explícitamente cada relación tras decidir bajo norma autorizada | No | Sí | Sí |
| P04 | Disposición global de las 385 filas | Manifest/ledger muestran 385/385 `UNKNOWN`; crosswalk 055 conserva contexto y relaciones por fila | `NORMATIVE_DECISION_REQUIRED` | Obtener outcomes globales por fila, sin inferirlos de memberships YES/NO | No | Sí, para cierre global | Sí |
| P05 | Representación canónica de las 44 relaciones YES checkpoint-only | CP024/026/028 documentan 9+17+18 YES condicionales; 046 confirma que no están todas materializadas | `DOCUMENTARY_REPAIR_REQUIRED` | Tras gate P01 y autorización de cambio, decidir si registrar en la representación canónica exactamente esos outcomes/scope; no es requisito del crosswalk descriptivo | No | Sí para reclamar representación canónica completa | Sí para calificar un snapshot canónico completo |
| P06 | Cierre de las diferencias de conteo/semántica en datos históricos | CP049/056 hacen reproducibles los 11 stale y sus deltas | `NOT_A_BLOCKER` | Ninguna para continuar; no corregir los campos en esta tarea | No | No | No, salvo uso futuro del valor como métrica |
| P07 | Métrica `human_adjudicated_candidate_relation_count=63` | Ledger contiene el valor pero no fórmula, universo o fecha de corte; CP056/057 no recuperan su scope | `NOT_A_BLOCKER` | No usarla como contador de reconciliación; aclarar scope sólo si un consumidor futuro necesita esa métrica | No | No | No como gate independiente |
| P08 | Provenance exacta faltante en los 61 pares parciales | CP011/012 y 049 prueban historia agregada; 055/056 identifican los pares actuales, no el origen primario de cada uno | `PROVENANCE_UNRESOLVED` | Recuperar fuente por par sólo si se requiere atribuir el origen histórico; no rellenar con evidencia general | No para describirlos como parciales | Sí si se pretende basar una decisión o cambio en su origen histórico | Sí cuando una adjudicación/readiness dependa de esa procedencia |
| P09 | Finite selectors/value partitions de las superficies | Manifest contract los exige; freeze blocker registrado en el propio manifest; CP054 distingue descripción de cierre | `NORMATIVE_DECISION_REQUIRED` | Definir/cerrar particiones, variantes y fronteras por superficie según norma autorizada | No | Sí para cierre de cobertura | Sí |
| P10 | Callsite → workload → Python/native/dependency → syscall y cobertura requerida | Manifest freeze blocker; ledger mantiene required units UNKNOWN y no hay binding completo | `NORMATIVE_DECISION_REQUIRED` | Identificar/trazar los callsites y sus rutas/variantes con evidencia admisible; separar evidencia estática de cualquier actividad futura no autorizada | No | No para reconciliar registros históricos; sí para certificar cobertura normativa | Sí |
| P11 | Calificación de enforcement de ABI fuera de alcance (x32/i386) | Ledger: excluidos por scope pero enforcement del launcher no calificado | `NORMATIVE_DECISION_REQUIRED` | Determinar criterio de aceptación y aportar evidencia de que el launcher hace cumplir el scope | No | No | Sí |
| P12 | Predicate/machine validation de A-PRE-0 | Ledger registra que no existe predicate separado machine-validated y `predicate_result=false` | `DOCUMENTARY_REPAIR_REQUIRED` | Definir/implementar y validar el mecanismo de predicate como trabajo posterior autorizado; no evaluar READY por inspección parcial | No | No | Sí |

### Ítems ya cerrados o sin efecto de bloqueo

No se conservan como pendientes:

- `shutdown` 48/S07: `RESOLVED_DESCRIPTIVE_PROVENANCE` por CP026/046
  (057 §2); el flag inconsistente dentro de 055 no contradice la relación
  fuente.
- Once métricas: `STALE_DERIVED_COUNTER` reproducibles; son resúmenes
  históricos/copiados, no contradicciones estructurales.
- Las nueve transiciones históricas: reconstruidas en 057 §7; no son nueve
  cambios pendientes.
- Las decisiones/outcomes históricos de las 77 relaciones checkpoint-only:
  sus 44 YES y 23 exclusiones están documentalmente constatados. Su
  materialización queda como reparación de representación P05, no como 67
  nuevas adjudicaciones. Los diez UNKNOWN son P03, no un segundo grupo.
- La discrepancia del conteo “162 activos”: queda explicada en §5. No se
  modifica 057 ni se promueve/descarta relación alguna.

## 5. Reconciliación de los 162 tags de lead

La suma de etiquetas `LEAD` en el crosswalk 055 es 162. Ese conteo no equivale
a 162 decisiones abiertas: cinco entradas están ya acompañadas por outcomes
relacionales de exclusión en evidencia previa. Por tanto:

`162 tags LEAD - 4 exclusiones S01 - 1 exclusión S04 (umask) = 157 leads abiertos`

Esto corrige la interpretación de “162 leads activos” de 056/057 sin
reclasificar la fuente canónica ni editar aquellos checkpoints. Los 19 S02
de CP016 son exclusiones, no están en el conteo de tags LEAD de 055. El
solapamiento de clasificación en 055 no vuelve a abrir exclusiones ya
documentadas.

| Superficie | Tags LEAD en 055 | Ya excluidos | Leads abiertos | Familia/agrupación predominante | Evidencia actual | Faltante |
|---|---:|---:|---:|---|---|---|
| S01 | 4 | 4 | 0 | inotify/fanotify setup/removal | CP014 documenta las cuatro exclusiones | Ninguna decisión nueva sobre estos pares |
| S04 | 6 | 1 | 5 | cuotas y atributos filesystem nuevos | CP019/020 describe los leads; CP020 excluye `umask` | Decisión/ABI/efecto para las otras cinco relaciones |
| S05 | 17 | 0 | 17 | residencia, locking, NUMA, remap y protección de mappings | CP021 enumera los 17 | Decisión por operación, backing, argumentos y efecto |
| S06 | 19 | 0 | 19 | heap/anonymous/memfd, residencia, NUMA, shadow stack y memory seal | CP023 enumera los 19 | Decisión por objeto/backing, operación y variante |
| S10 | 36 | 0 | 36 | scheduler/yield, timers/clocks, señal/timer FDs, futex/rseq | CP011/012 prueban el grupo histórico; CP049 identifica refs actuales | Decisión relacional; provenance individual parcial |
| S11 | 26 | 0 | 26 | identidad/scheduler/group, ptrace, cross-process memory, process release | CP033 es específico para 4; 22 sólo cuentan con fuente agregada del lote | Decisión por efecto/target; provenance individual parcial para 22 |
| S15 | 3 | 0 | 3 | interfaces opacas `security`, uprobes | CP011/012 y CP049 permiten ubicar el grupo, no probar origen individual | Decisión por API/operación; provenance individual parcial |
| S16 | 51 | 0 | 51 | identidad/credenciales, kernel/module, namespaces/LSM y controles | CP041 §5 enumera los 51 y preserva su condición de lead | Decisión por API, comando, permisos y efecto |
| **Total** | **162** | **5** | **157** |  | **96 recuperables + 61 parciales** |  |

### 5.1 Lista completa por superficie

`nr:nombre` identifica el par syscall-superficie, no una decisión. Los 96
recuperables son S04 (5), S05 (17), S06 (19), S11 (4) y S16 (51); los 61
parciales son S10 (36), S11 (22) y S15 (3), conforme a 057.

- **S01 — tags con outcome ya documentado, 4 excluidos:** 253 `inotify_init`;
  255 `inotify_rm_watch`; 294 `inotify_init1`; 300 `fanotify_init`.
- **S04 — 5 abiertos; `umask` 95 ya excluida:** 95 `umask`; 179 `quotactl`; 443
  `quotactl_fd`; 463 `setxattrat`; 466 `removexattrat`; 469 `file_setattr`.
- **S05 — 17 abiertos:** 27 `mincore`; 149 `mlock`; 150 `munlock`; 151
  `mlockall`; 152 `munlockall`; 216 `remap_file_pages`; 237 `mbind`; 238
  `set_mempolicy`; 239 `get_mempolicy`; 256 `migrate_pages`; 279
  `move_pages`; 325 `mlock2`; 330 `pkey_alloc`; 331 `pkey_free`; 440
  `process_madvise`; 450 `set_mempolicy_home_node`; 462 `mseal`.
- **S06 — 19 abiertos:** 12 `brk`; 27 `mincore`; 149 `mlock`; 150
  `munlock`; 151 `mlockall`; 152 `munlockall`; 216 `remap_file_pages`; 237
  `mbind`; 238 `set_mempolicy`; 239 `get_mempolicy`; 256 `migrate_pages`;
  279 `move_pages`; 325 `mlock2`; 330 `pkey_alloc`; 331 `pkey_free`; 440
  `process_madvise`; 450 `set_mempolicy_home_node`; 453 `map_shadow_stack`;
  462 `mseal`.
- **S10 — 36 abiertos:** 24 `sched_yield`; 34 `pause`; 35 `nanosleep`; 36
  `getitimer`; 37 `alarm`; 38 `setitimer`; 96 `gettimeofday`; 100 `times`;
  186 `gettid`; 201 `time`; 203 `sched_setaffinity`; 204
  `sched_getaffinity`; 218 `set_tid_address`; 219 `restart_syscall`; 222
  `timer_create`; 223 `timer_settime`; 224 `timer_gettime`; 225
  `timer_getoverrun`; 226 `timer_delete`; 227 `clock_settime`; 228
  `clock_gettime`; 229 `clock_getres`; 230 `clock_nanosleep`; 273
  `set_robust_list`; 274 `get_robust_list`; 282 `signalfd`; 283
  `timerfd_create`; 286 `timerfd_settime`; 287 `timerfd_gettime`; 289
  `signalfd4`; 324 `membarrier`; 334 `rseq`; 454 `futex_wake`; 455
  `futex_wait`; 456 `futex_requeue`; 471 `rseq_slice_yield`.
- **S11 — 26 abiertos:** 39 `getpid`; 98 `getrusage`; 101 `ptrace`; 109
  `setpgid`; 110 `getppid`; 111 `getpgrp`; 112 `setsid`; 121 `getpgid`;
  124 `getsid`; 140 `getpriority`; 141 `setpriority`; 142 `sched_setparam`;
  143 `sched_getparam`; 144 `sched_setscheduler`; 145 `sched_getscheduler`;
  146 `sched_get_priority_max`; 147 `sched_get_priority_min`; 148
  `sched_rr_get_interval`; 302 `prlimit64`; 309 `getcpu`; 310
  `process_vm_readv`; 311 `process_vm_writev`; 312 `kcmp`; 314
  `sched_setattr`; 315 `sched_getattr`; 448 `process_mrelease`.
- **S15 — 3 abiertos:** 185 `security`; 335 `uretprobe`; 336 `uprobe`.
- **S16 — 51 abiertos:** 63 `uname`; 97 `getrlimit`; 99 `sysinfo`; 102
  `getuid`; 103 `syslog`; 104 `getgid`; 107 `geteuid`; 108 `getegid`; 115
  `getgroups`; 118 `getresuid`; 120 `getresgid`; 134 `uselib`; 135
  `personality`; 139 `sysfs`; 141 `setpriority`; 153 `vhangup`; 154
  `modify_ldt`; 158 `arch_prctl`; 159 `adjtimex`; 160 `setrlimit`; 163
  `acct`; 164 `settimeofday`; 167 `swapon`; 168 `swapoff`; 169 `reboot`;
  170 `sethostname`; 171 `setdomainname`; 172 `iopl`; 173 `ioperm`; 174
  `create_module`; 177 `get_kernel_syms`; 178 `query_module`; 205
  `set_thread_area`; 211 `get_thread_area`; 212 `lookup_dcookie`; 248
  `add_key`; 249 `request_key`; 250 `keyctl`; 251 `ioprio_set`; 252
  `ioprio_get`; 305 `clock_adjtime`; 444 `landlock_create_ruleset`; 445
  `landlock_add_rule`; 446 `landlock_restrict_self`; 457 `statmount`; 458
  `listmount`; 459 `lsm_get_self_attr`; 460 `lsm_set_self_attr`; 461
  `lsm_list_modules`; 467 `open_tree_attr`; 470 `listns`.

S01 y S04 leads superpuestos con exclusiones previas no son añadidos a P02.
Las filas con dos leads (p. ej. S05/S06) son dos relaciones distintas, pero
una sola syscall global UNKNOWN; no se fusionan ni se adjudican por similitud
de familia.

## 6. Los 385 UNKNOWN: disposición frente a relación de superficie

Conteo derivado del manifest y su representación:

| Unidad | Estado actual | Lectura correcta |
|---|---:|---|
| Filas target-bound | 385 | 385 nombres/números únicos |
| Disposición global `UNKNOWN` | 385 | Política actual deliberada; no significa que cada relación de superficie carezca de decisión |
| Contextos syscall-superficie serializados | 239 | No son filas únicas |
| Filas con contexto no vacío | 201 | Complemento: 184 sin contexto |
| Filas con `candidate_surface_ids` no vacío | 198 | Complemento: 187 sin IDs; no equivale a exclusión |
| Contextos `HUMAN_ADJUDICATED_CANDIDATE` | 191 | Decisión/estado relacional existente, no disposición global |
| Contextos `HUMAN_ADJUDICATED_NOT_MEMBER` | 3 | Exclusiones S02 en 74, 75, 277; no disposiciones globales NO |
| Contextos `UNREVIEWED_CANDIDATE` | 45 | 42 corresponden a relaciones con YES documentado checkpoint-only (9 S06, 17 S07, 16 de 18 S08); 3 UNKNOWN relacionales: `madvise` 28/S05, `msync` 26/S06, `ioctl` 16/S15 |
| Relaciones YES checkpoint-only | 44 | 42 tienen contexto U serializado; S08/54 `setsockopt` y S08/55 `getsockopt` están documentados pero sin contexto S08 actual |

Además de los tres UNKNOWN en contexto U, CP014 contiene siete UNKNOWN
relacionales sin contexto candidato actual: 136 `ustat`; 254
`inotify_add_watch`; 301 `fanotify_mark`; 304 `open_by_handle_at`; 464
`getxattrat`; 465 `listxattrat`; 468 `file_getattr`. Con los tres anteriores
son los diez UNKNOWN relacionales de 056/057; no son diez filas globales
adicionales.

Las relaciones S01–S16 ya adjudicadas (incluidas S01–S05, S09–S16 donde
serializadas) siguen coexistiendo con 385 disposiciones globales UNKNOWN por
contrato. Los YES condicionales checkpoint-only S06–S08 también son
relacionales, no cierres globales. A la inversa, `candidate_surface_ids`
vacío no expresa NO: incluye relaciones sin revisar y exclusiones acotadas.

S14 es API POSIX AIO, no syscall; sus nueve interfaces no añaden filas ni
outcomes al universo 385. El trabajo de workers no se traslada por inferencia
a superficies syscall.

## 7. Los 61 `PROVENANCE_PARTIAL`

Los 61 pares son exactamente los leads S10 (36), S11 (22) y S15 (3) de §5.
Para cada uno, la manifest/055 identifica el par que se examina; CP011/012 y
CP049 acreditan agregados históricos por superficie y CP033 añade evidencia
directa para cuatro leads S11. No existe cita primaria individual suficiente
para los otros pares, según la auditoría de 057.

| Grupo | Provenance que sí existe | Qué falta | ¿Bloquea describir el par? | ¿Puede rellenarse con evidencia revisada? |
|---|---|---|---|---|
| S10, 36 | Conteo agregado histórico (38) y pertenencia actual a refs S10 (36); cronología de 049 | Fuente primaria individual del lead por syscall | No; registrar `PROVENANCE_PARTIAL` | No con la evidencia actualmente localizada; recuperar sólo si una decisión futura depende del origen |
| S11, 22 | Conteo agregado de lote; CP033/034 da contexto general S11 y evidencia directa para otros leads separados | Fuente primaria individual para estos 22 pares | No; registrar `PROVENANCE_PARTIAL` | No con la evidencia actualmente localizada |
| S15, 3 | Conteo agregado histórico (3) y lista individual actual 185/335/336 en manifest/055/049 | Fuente primaria individual de por qué cada ref fue creada | No; registrar `PROVENANCE_PARTIAL` | No con la evidencia actualmente localizada |

La parte faltante es una limitación de procedencia histórica, no prueba de
que el lead no exista ni de que la superficie sea correcta. Para el
crosswalk descriptivo basta informar la representación actual y la
limitación. Si la decisión humana futura usa la razón/origen de una antigua
adición como premisa, la fuente debe recuperarse antes de apoyarse en ella.
No se fabrican citas y no se convierten estos 61 en una nueva tarea de
adjudicación adicional a los 157 leads.

## 8. Reconciliación de las 77 relaciones checkpoint-only

La unidad es el par syscall-superficie que 056/057 identifican como
checkpoint-only. Los outcomes se mantienen en sus categorías históricas; no
se suman como nuevas decisiones ni se materializan.

| Grupo | Cantidad | Evidencia/outcome | Efecto en el set final |
|---|---:|---|---|
| S06 YES condicional, CP024 | 9 | La decisión y scope están escritos; 046 los llama no materializados | Cerrados como historia; P05 sólo si se autoriza reparación canónica |
| S07 YES condicional, CP026 | 17 | Decisión IP condicional por syscall/variante; 046 confirma checkpoint-only | Cerrados como historia; P05 sólo si se autoriza reparación canónica |
| S08 YES condicional, CP028 | 18 | Decisión AF_UNIX condicional; 046 incluye los dos S08/54–55 ausentes del contexto manifest | Cerrados como historia; P05 sólo si se autoriza reparación canónica |
| S02 exclusiones, CP016 | 19 | Exclusiones relacionales históricas, no disposiciones globales | No requieren una nueva decisión; no se materializan |
| S01 exclusiones, CP014 | 4 | Exclusiones relacionales de `inotify_init`, `inotify_rm_watch`, `inotify_init1`, `fanotify_init` | No requieren una nueva decisión; explican cuatro tags LEAD redundantes |
| UNKNOWN relacionales | 10 | S01 7, S05 1, S06 1, S15 1 | P03; preservar hasta decisión autorizada |
| **Total** | **77** | **44 + 23 + 10** | **67 outcomes históricos documentados + 10 relaciones UNKNOWN** |

44 YES + 23 NO documentados se pueden describir sin editar el manifest. Una
decisión de materialización no es parte de la reconciliación descriptiva:
requiere cambio controlado, y cualquier uso de norma/autoridad sigue sujeto a
P01. Los diez UNKNOWN ya están contados en P03, no vuelven a sumarse aquí.

## 9. Contadores, `shutdown/S07` y demás cierres

| Elemento | Conclusión | Categoría operativa |
|---|---|---|
| 11 stale counters | CP049/056 demuestra fórmula y deltas; ninguno es contradicción estructural | `NOT_A_BLOCKER` |
| Ledger `human_adjudicated_candidate_relation_count=63` | Unidad/scope no probado; no coincide con 239 contextos, 236 IDs, ni 187 decisiones serializadas; no usar como reconciliación | `NOT_A_BLOCKER` |
| `shutdown` 48/S07 | CP026 y 046 respaldan la referencia ya presente en 055; estado manifest sigue U; anomalía de metadata explicada | `CLOSED_WITH_EXISTING_EVIDENCE` |
| Nueve transiciones | CP032/034 y 049 explican antes/después y efecto de representación | `CLOSED_WITH_EXISTING_EVIDENCE` |
| 055/057 conteo de leads | Los 162 son tags LEAD; cinco coexisten con exclusiones S01/S04; el set abierto es 157 | `CLOSED_WITH_EXISTING_EVIDENCE` por esta reconciliación; no reescribir 055/057 aquí |

No se exige aclarar el scope 63 para cerrar el crosswalk o la reconciliación
descriptiva. Si se usa como métrica de progreso, deberá definirse primero, sin
cambiarlo en esta tarea.

## 10. Criterios mínimos para reanudar por nivel

| Nivel | Trabajo que puede/queda por hacer | Set mínimo |
|---|---|---|
| 1 — Crosswalk descriptivo | 055/056 proporcionan las 385 filas; 057/058 consolidan gaps y límites | No requiere decisiones nuevas. Mantener explícitos 61 `PROVENANCE_PARTIAL`, 63 `SCOPE_UNPROVEN` y `UNKNOWN`; no corregir fuentes |
| 2 — Cierre descriptivo de 048 | Presentar la reconciliación como descripción completa, sin resolver semántica, 385 UNKNOWN o autoridad | No requiere nuevas decisiones normativas. Debe delimitarse expresamente como cierre descriptivo; el STOP normativo de 053 permanece |
| 2 — Cierre normativo/global de 048 | Resolver las diferencias cuya verdad depende del contrato | P01 primero; luego P02/P03 y los asuntos de representación P05 que se pretendan llamar canónicos |
| 3 — Edición legítima de manifest/ledger | Cambio controlado de serialización o métricas | P01 y autorización explícita de cambio; evidencia fuente por campo/relación; especificar si 44 YES se materializan. Los 11 stale y 63 no se corrigen automáticamente |
| 4 — Evaluar A-PRE-0 | Satisfacer predicate y evidencia de qualification, sin declararlo READY aquí | P01; outcomes de P02/P03 y las 385 disposiciones P04; finite partitions P09; trazabilidad/cobertura P10; enforcement ABI P11; predicate validado P12; preservar las condiciones del ledger/overlay |

La dependencia de 61 pares parciales sólo eleva a bloqueo de provenance una
decisión que pretenda basarse en su origen histórico; el crosswalk puede
registrar el límite sin detenerse. El contador 63 y stale no forman parte del
set mínimo de ningún nivel mientras no se usen como criterio de cierre.

## 11. Estado final

- `BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED`;
  `STOP_REASON = UNRESOLVED_PROVENANCE`; `f058… = UNRECOVERED`.
- A-PRE-0 `NOT_READY`, `predicate_result=false`; A-PRE-1
  `NOT_AUTHORIZED / NOT_EXECUTED`.
- `inventory.frozen=false`; 385/385 disposiciones globales `UNKNOWN`.
- Ningún lead promovido, relación adjudicada, UNKNOWN convertido, variante
  cerrada o archivo canónico editado.

## 12. Verificación

- Manifest: 385 filas, 385 nombres únicos y 385 números únicos.
- Manifest, ledger, `requirements.lock` y ambas baseline specs mantienen los
  hashes de §1.
- Sólo se crean este checkpoint y su entrada en `checkpoints/index.md`.
- `git diff --check` verificado; sin commit. El worktree tenía cambios
  preexistentes ajenos, preservados.
- Sin actividad dinámica y sin acceso a VM, DB, corpus o modelos.
