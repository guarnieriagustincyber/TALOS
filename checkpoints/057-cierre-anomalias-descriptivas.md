# Checkpoint 057 — cierre de anomalías descriptivas

Alcance: auditoría documental de anomalías del checkpoint 056. No se modifican
artefactos canónicos ni se toman decisiones nuevas de membresía.

## 1. Estado inicial e invariantes

| Elemento | Estado observado |
|---|---|
| HEAD | `f81134fc2293916210d53c8065f3a0049e52b0b4` |
| Manifest SHA-256 | `801f529655f1f4f250a2a374d2afa63f858a9c0875e0e3dc620d112df5f9fd6e` |
| Ledger SHA-256 | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` SHA-256 | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Baseline spec `docs/` SHA-256 | `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` |
| Baseline spec `files/` SHA-256 | `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0` |
| Autoridad de baseline | `BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED`; `STOP_REASON = UNRESOLVED_PROVENANCE` |
| Artefacto externo `f058…` | `EXTERNAL_SPEC_ARTIFACT = UNRECOVERED` |
| A-PRE-0 / A-PRE-1 | `NOT_READY` / `NOT_AUTHORIZED / NOT_EXECUTED` |
| Inventario / disposiciones | `inventory.frozen=false`; 385/385 `UNKNOWN` |
| Leads / UNKNOWN relacionales | 162 activos / 10 documentados |

La inspección se limitó a lecturas de manifest, ledger y checkpoints 011–056,
recuentos y hashes locales. No se ejecutó TALOS, código del proyecto,
FastAPI, pruebas, parser/validator, workload, probe, benchmark o actividad
dinámica; no se accedió a VM, DB, corpus ni modelos.

## 2. Contradicción descriptiva de `shutdown` / S07

| Fuente | Afirmación verificable |
|---|---|
| Crosswalk 055, NR 48 | El addendum describe S07 como `YES_CONDITIONAL`, checkpoint-only, y su provenance apunta a CP026 con scope explícito; sin embargo, el mismo objeto tiene `provenance_status = PROVENANCE_UNRESOLVED`. |
| Checkpoint 026 | La tabla de las 17 candidaturas S07 contiene `shutdown` NR 48 como YES condicional para socket IP, con `SHUT_RD`, `SHUT_WR` y `SHUT_RDWR`; AF_UNIX queda fuera de S07. |
| Checkpoint 046 | La fila S07/48 marca el YES documentado en 026, checkpoint-only y sin contradicción de fuente. S08/48 se documenta por separado en 028. |
| Manifest actual | S07 y S08 siguen como contextos candidatos no revisados; no hay adjudicación S07 serializada para NR 48. Disposición global: `UNKNOWN`. |

**Resultado:** `RESOLVED_DESCRIPTIVE_PROVENANCE`. La evidencia explica la
contradicción como un flag interno inconsistente en la representación de 055:
hay referencia directa, ruta y SHA de CP026 en el propio objeto. CP026 y 046
respaldan la existencia documental de la relación y su alcance, no una decisión
nueva. No se altera el estado S07 del manifest ni se cambia la etiqueta
materializada.

## 3. Revisión de los 157 pares `PROVENANCE_GAP`

Unidad auditada: cada par `(nr, surface_id)` clasificado como gap en 056,
incluyendo relaciones distintas de una syscall cuando tiene más de una
superficie. `PROVENANCE_RECOVERABLE` significa que un checkpoint existente
documenta ese syscall como lead/ref de esa superficie; no confirma
membresía. `PROVENANCE_PARTIAL` significa que existe evidencia histórica del
lote/superficie, pero no permite ligar inequívocamente el origen de cada par.

| Superficie | Pares | `PROVENANCE_RECOVERABLE` | `PROVENANCE_PARTIAL` | Fuente y justificación |
|---|---:|---:|---:|---|
| S04 | 5 | 5 | 0 | CP019 presenta y nombra las cinco refs; CP020 registra su estado relacional abierto/excluido/UNKNOWN sin agregarlas a candidaturas. |
| S05 | 17 | 17 | 0 | CP021 enumera los 17 leads por NR/nombre y superficie. CP022 preserva que no se promueven. |
| S06 | 19 | 19 | 0 | CP023 enumera por NR/nombre los 19 leads S06; CP024 mantiene fuera de la adjudicación las refs no candidatas. |
| S10 | 36 | 0 | 36 | CP011/012 prueban sólo agregados históricos S10 (38 refs); CP049 enumera el conjunto actual de 36, pero no demuestra el origen primario individual de esos pares. |
| S11 | 26 | 4 | 22 | CP033 enumera como leads S11 `ptrace` 101, `process_vm_readv` 310, `process_vm_writev` 311 y `process_mrelease` 448. El resto sólo tiene apoyo agregado/indirecto en 011/012 y la fotografía de 049. |
| S15 | 3 | 0 | 3 | 011/012 registran un total histórico de tres refs S15; 049 identifica las tres refs actuales, sin demostrar una fuente primaria individual. |
| S16 | 51 | 51 | 0 | CP041 §5 enumera expresamente por NR/nombre los 51 leads S16 y declara que no se promueven. |
| **Total** | **157** | **96** | **61** | Cada par se asigna a una única categoría; la evidencia de lead no es una adjudicación normativa. |

### 3.1 Pares recuperables — evidencia exacta de lead/ref

**S04 — CP019/020 (5):** 179 `quotactl`; 443 `quotactl_fd`; 463
`setxattrat`; 466 `removexattrat`; 469 `file_setattr`.

**S05 — CP021 (17):** 27 `mincore`; 149 `mlock`; 150 `munlock`; 151
`mlockall`; 152 `munlockall`; 216 `remap_file_pages`; 237 `mbind`; 238
`set_mempolicy`; 239 `get_mempolicy`; 256 `migrate_pages`; 279 `move_pages`;
325 `mlock2`; 330 `pkey_alloc`; 331 `pkey_free`; 440 `process_madvise`; 450
`set_mempolicy_home_node`; 462 `mseal`.

**S06 — CP023 (19):** 12 `brk`; 27 `mincore`; 149 `mlock`; 150 `munlock`;
151 `mlockall`; 152 `munlockall`; 216 `remap_file_pages`; 237 `mbind`; 238
`set_mempolicy`; 239 `get_mempolicy`; 256 `migrate_pages`; 279 `move_pages`;
325 `mlock2`; 330 `pkey_alloc`; 331 `pkey_free`; 440 `process_madvise`; 450
`set_mempolicy_home_node`; 453 `map_shadow_stack`; 462 `mseal`.

**S11 — CP033 (4):** 101 `ptrace`; 310 `process_vm_readv`; 311
`process_vm_writev`; 448 `process_mrelease`.

**S16 — CP041 §5 (51):** 63 `uname`; 97 `getrlimit`; 99 `sysinfo`; 102
`getuid`; 103 `syslog`; 104 `getgid`; 107 `geteuid`; 108 `getegid`; 115
`getgroups`; 118 `getresuid`; 120 `getresgid`; 134 `uselib`; 135
`personality`; 139 `sysfs`; 141 `setpriority`; 153 `vhangup`; 154
`modify_ldt`; 158 `arch_prctl`; 159 `adjtimex`; 160 `setrlimit`; 163 `acct`;
164 `settimeofday`; 167 `swapon`; 168 `swapoff`; 169 `reboot`; 170
`sethostname`; 171 `setdomainname`; 172 `iopl`; 173 `ioperm`; 174
`create_module`; 177 `get_kernel_syms`; 178 `query_module`; 205
`set_thread_area`; 211 `get_thread_area`; 212 `lookup_dcookie`; 248
`add_key`; 249 `request_key`; 250 `keyctl`; 251 `ioprio_set`; 252
`ioprio_get`; 305 `clock_adjtime`; 444 `landlock_create_ruleset`; 445
`landlock_add_rule`; 446 `landlock_restrict_self`; 457 `statmount`; 458
`listmount`; 459 `lsm_get_self_attr`; 460 `lsm_set_self_attr`; 461
`lsm_list_modules`; 467 `open_tree_attr`; 470 `listns`.

### 3.2 Pares parciales — mapeo sin provenance primaria por par

**S10 — 36:** 24 `sched_yield`; 34 `pause`; 35 `nanosleep`; 36 `getitimer`;
37 `alarm`; 38 `setitimer`; 96 `gettimeofday`; 100 `times`; 186 `gettid`;
201 `time`; 203 `sched_setaffinity`; 204 `sched_getaffinity`; 218
`set_tid_address`; 219 `restart_syscall`; 222 `timer_create`; 223
`timer_settime`; 224 `timer_gettime`; 225 `timer_getoverrun`; 226
`timer_delete`; 227 `clock_settime`; 228 `clock_gettime`; 229 `clock_getres`;
230 `clock_nanosleep`; 273 `set_robust_list`; 274 `get_robust_list`; 282
`signalfd`; 283 `timerfd_create`; 286 `timerfd_settime`; 287
`timerfd_gettime`; 289 `signalfd4`; 324 `membarrier`; 334 `rseq`; 454
`futex_wake`; 455 `futex_wait`; 456 `futex_requeue`; 471 `rseq_slice_yield`.

**S11 — 22:** 39 `getpid`; 98 `getrusage`; 109 `setpgid`; 110 `getppid`;
111 `getpgrp`; 112 `setsid`; 121 `getpgid`; 124 `getsid`; 140 `getpriority`;
141 `setpriority`; 142 `sched_setparam`; 143 `sched_getparam`; 144
`sched_setscheduler`; 145 `sched_getscheduler`; 146
`sched_get_priority_max`; 147 `sched_get_priority_min`; 148
`sched_rr_get_interval`; 302 `prlimit64`; 309 `getcpu`; 312 `kcmp`; 314
`sched_setattr`; 315 `sched_getattr`.

**S15 — 3:** 185 `security`; 335 `uretprobe`; 336 `uprobe`.

### 3.3 No provenance recovery / representation artifact

| Categoría | Total | Resultado |
|---|---:|---|
| `PROVENANCE_UNRESOLVED` | 0 | No queda un par sin siquiera evidencia histórica agregada de su lote/superficie. Los 61 parciales siguen sin provenance exacta por par; no se reclasifican como recuperados. |
| `REPRESENTATION_ARTIFACT` | 0 | Ninguno de los 157 es una mera diferencia de forma ya explicada: cada par sí carece de cita primaria individual en 055. El flag de `shutdown`/S07 es otra anomalía, fuera de estos 157 pares. |

Los 157 gaps, por tanto, no son 157 relaciones normativamente pendientes
adicionales: 96 recuperan evidencia descriptiva de lead y 61 conservan una
limitación de provenance parcial. Ninguno se promueve, elimina o adjudica.

## 4. Contador agregado del ledger sin scope

| Campo | Valor | Unidad/scope demostrado | Resultado |
|---|---:|---|---|
| `ledger.inventory.human_adjudicated_candidate_relation_count` | 63 | El ledger no define fórmula, universo, fecha de corte ni si cuenta filas, pares, decisiones históricas o adjudicaciones serializadas. | `SCOPE_UNPROVEN` |

En el manifest actual se cuentan 239 contextos syscall-superficie, 236 IDs
serializados y 187 registros de adjudicación de relación (169 `YES`, 9
`YES_CONDITIONAL`, 9 `NO`). Ninguna de esas unidades es 63. Tampoco se halló
una definición en los checkpoints revisados que permita comparar 63
inequívocamente con otra métrica. No se etiqueta como stale ni se corrige.

## 5. Los 11 contadores stale de 056

Fuente de los valores históricos, cronología y recálculo: CP049 §§2–4 y tabla
de deltas de CP056. Fórmulas sobre las 385 filas actuales; los tres primeros
valores del ledger repiten los del manifest y no son una derivación
independiente.

| # | Campo | Histórico | Actual derivado | Fórmula actual | Fuente histórica / clasificación |
|---:|---|---:|---:|---|---|
| 1 | manifest `rows_with_candidate_surface_context` | 204 | 201 | Filas con `candidate_surface_context` no vacío | CP049, snapshot pre-S10; `STALE_DERIVED_COUNTER` |
| 2 | manifest `rows_without_surface_candidate_remain_unknown` | 181 | 184 | `385 - filas con contexto` | CP049; `STALE_DERIVED_COUNTER` |
| 3 | manifest `rows_without_candidate_surface_membership` | 181 | 187 | Filas sin `candidate_surface_ids` no vacío | CP049; `STALE_DERIVED_COUNTER` |
| 4 | ledger `rows_with_candidate_surface_context` | 204 | 201 | Misma fórmula que #1 | Copia del manifest; `STALE_DERIVED_COUNTER` |
| 5 | ledger `rows_without_surface_candidate_remain_unknown` | 181 | 184 | Misma fórmula que #2 | Copia del manifest; `STALE_DERIVED_COUNTER` |
| 6 | ledger `rows_without_candidate_surface_membership` | 181 | 187 | Misma fórmula que #3 | Copia del manifest; `STALE_DERIVED_COUNTER` |
| 7 | ledger `no_candidate_rows_reviewed` | 194 | 191 | Filas con `no_candidate_review` no nulo | Resumen ledger/manifest; `STALE_DERIVED_COUNTER` |
| 8 | ledger `no_candidate_potential_existing_surface_lead_rows` | 186 | 183 | Filas con `potential_surface_refs` no vacío | CP011/012 históricos frente a estado actual; `STALE_DERIVED_COUNTER` |
| 9 | ledger `no_candidate_lead_reference_histogram.one_surface_ref` | 168 | 165 | Filas con exactamente una referencia potencial | Histogram histórico vs manifest actual; `STALE_DERIVED_COUNTER` |
| 10 | ledger `no_candidate_lead_surface_reference_counts.S10` | 38 | 36 | Aristas `(fila,S10)` en `potential_surface_refs` | CP011/012 histórico; `STALE_DERIVED_COUNTER` |
| 11 | ledger `no_candidate_lead_surface_reference_counts.S11` | 27 | 26 | Aristas `(fila,S11)` en `potential_surface_refs` | CP011/012 histórico; `STALE_DERIVED_COUNTER` |

Los once son discrepancias de resúmenes históricos/copiados con datos actuales
recalculables; ninguno contradice estructuralmente el manifest. El delta de
contextos 204→201 se explica por las transiciones de §7: seis retiros y tres
incorporaciones, no sólo por las tres exclusiones S02. IDs (198 filas) y
contextos (201 filas) son unidades distintas; las tres exclusiones S02
conservan su contexto.

## 6. Las 77 relaciones checkpoint-only

Unidad de conteo: pares `(nr,surface_id)` de la clasificación de CP056, no
objetos JSON addendum ni syscalls únicas. Se separan outcomes; las decisiones
históricas se citan sin materializarlas.

| Outcome en documento fuente | Total | Estado descriptivo |
|---|---:|---|
| 44 `YES_CONDITIONAL` | 9 S06 en CP024; 17 S07 en CP026; 18 S08 en CP028 | `DOCUMENTED_HISTORICAL_ONLY`; la decisión y el scope están escritos, pero siguen checkpoint-only en manifest. |
| 23 exclusiones | 19 S02 en CP016; cuatro S01 en CP014 | Exclusión relacional histórica documentada, no disposición global ni cambio nuevo. |
| 10 `UNKNOWN` relacionales | S01: 7; S05: 1; S06: 1; S15: 1 | `NORMATIVE_DEPENDENCY` para cualquier paso que pretenda resolver esos UNKNOWN; preservar el estado documentado. |
| **77** | **44 + 23 + 10** | **67 documentadas como outcome histórico; 10 siguen UNKNOWN y requieren autoridad para resolver.** |

Pares YES condicionales:

- **S06/CP024 (9):** 9 `mmap`; 10 `mprotect`; 11 `munmap`; 25 `mremap`;
  72 `fcntl`; 77 `ftruncate`; 319 `memfd_create`; 329 `pkey_mprotect`;
  447 `memfd_secret`.
- **S07/CP026 (17):** 41 `socket`; 42 `connect`; 43 `accept`; 44 `sendto`;
  45 `recvfrom`; 46 `sendmsg`; 47 `recvmsg`; 48 `shutdown`; 49 `bind`;
  50 `listen`; 51 `getsockname`; 52 `getpeername`; 54 `setsockopt`;
  55 `getsockopt`; 288 `accept4`; 299 `recvmmsg`; 307 `sendmmsg`.
- **S08/CP028 (18):** 41 `socket`; 42 `connect`; 43 `accept`; 44 `sendto`;
  45 `recvfrom`; 46 `sendmsg`; 47 `recvmsg`; 48 `shutdown`; 49 `bind`;
  50 `listen`; 51 `getsockname`; 52 `getpeername`; 53 `socketpair`; 54
  `setsockopt`; 55 `getsockopt`; 288 `accept4`; 299 `recvmmsg`; 307
  `sendmmsg`.

Exclusiones: **S02/CP016 (19)** — 7 `poll`; 8 `lseek`; 23 `select`; 73
`flock`; 162 `sync`; 187 `readahead`; 213 `epoll_create`; 214
`epoll_ctl_old`; 215 `epoll_wait_old`; 221 `fadvise64`; 232 `epoll_wait`;
233 `epoll_ctl`; 270 `pselect6`; 271 `ppoll`; 281 `epoll_pwait`; 291
`epoll_create1`; 306 `syncfs`; 441 `epoll_pwait2`; 451 `cachestat`.
**S01/CP014 (4):** 253 `inotify_init`; 255 `inotify_rm_watch`; 294
`inotify_init1`; 300 `fanotify_init`.

UNKNOWN: **S01/CP014 (7)** — 136 `ustat`; 254 `inotify_add_watch`; 301
`fanotify_mark`; 304 `open_by_handle_at`; 464 `getxattrat`; 465
`listxattrat`; 468 `file_getattr`. **S05/CP022:** 28 `madvise`.
**S06/CP024:** 26 `msync`. **S15/CP040:** 16 `ioctl`.

Esta sección sigue el universo 77 de CP056 (44 YES + 23 exclusiones + 10
UNKNOWN). Otras anotaciones de 055 que además tienen representación
serializada en manifest no se agregan a este universo por segunda vez.

## 7. Nueve transiciones históricas

Evidencia consolidada en CP049/056, con decisiones S10 en CP032 y S11 en
CP034. Cada transición se describe como historial, no como cambio autorizado
ahora.

| NR / syscall | Antes | Después documentado | CP y efecto en representación actual | ¿Decisión normativa nueva? |
|---|---|---|---|---|
| 13 `rt_sigaction` | Contexto/candidatura S10 revisada | S10 `NO` relacional; contexto/ID retirados | CP032; deja de contar en contexto e IDs | No para describir la transición; no reabrir su alcance |
| 14 `rt_sigprocmask` | Contexto/candidatura S10 revisada | S10 `NO` relacional; contexto/ID retirados | CP032; deja de contar en contexto e IDs | No |
| 15 `rt_sigreturn` | Contexto/candidatura S10 revisada | S10 `NO` relacional; contexto/ID retirados | CP032; deja de contar en contexto e IDs | No |
| 127 `rt_sigpending` | Contexto/candidatura S10 revisada | S10 `NO` relacional; contexto/ID retirados | CP032; deja de contar en contexto e IDs | No |
| 131 `sigaltstack` | Contexto/candidatura S10 revisada | S10 `NO` relacional; contexto/ID retirados | CP032; deja de contar en contexto e IDs | No |
| 245 `mq_getsetattr` | Contexto/candidatura S10 revisada | S10 `NO` relacional; contexto/ID retirados | CP032; deja de contar en contexto e IDs | No |
| 129 `rt_sigqueueinfo` | Lead potencial S10 | S10 YES documentado/materializado; deja de ser lead | CP032; añade contexto/ID, consume ref S10 | No; preservar alcance de 032 |
| 297 `rt_tgsigqueueinfo` | Lead potencial S10 | S10 YES documentado/materializado; deja de ser lead | CP032; añade contexto/ID, consume ref S10 | No; preservar alcance de 032 |
| 434 `pidfd_open` | Lead potencial S11 | S11 YES documentado/materializado; deja de ser lead | CP034; añade contexto/ID, consume ref S11 | No; preservar alcance de 034 |

El efecto neto sobre el conjunto de contextos es `204 - 6 + 2 + 1 = 201`;
las tres exclusiones S02 (74, 75, 277) retiran IDs, pero no son parte de estas
nueve transiciones de contexto.

## 8. Matriz final de resolución

Los universos de esta tabla no se suman entre sí: los stale son campos
duplicados; los 77 son relaciones checkpoint-only; los 157 son pares con
provenance gap en 055; las nueve son transiciones históricas.

| Anomalía/universo | Total | Resoluble descriptivamente sin nueva decisión | Parcial / normativo / provenance restante |
|---|---:|---:|---|
| Contradicción 055 shutdown/S07 | 1 | 1 `RESOLVED_DESCRIPTIVE_PROVENANCE` | 0 |
| Pares provenance gap | 157 | 96 `PROVENANCE_RECOVERABLE` | 61 `PROVENANCE_PARTIAL`; 0 unresolved; 0 representation artifact |
| Contador ledger `human_adjudicated_candidate_relation_count` | 1 | 0 | 1 `SCOPE_UNPROVEN` |
| Contadores stale | 11 | 11 `STALE_DERIVED_COUNTER` reproducibles | 0 contradicciones estructurales |
| Relaciones checkpoint-only | 77 | 67 con outcome documental histórico (44 YES + 23 NO) | 10 UNKNOWN que no se resuelven sin decisión normativa |
| Transiciones históricas | 9 | 9 reconstruidas con CP032/034 | 0 cambios canónicos autorizados |

## 9. Pendientes reales y estado

- La autoridad única de baseline sigue sin resolverse; la autoridad normativa
  necesaria para evaluar adjudicaciones nuevas continúa bloqueada.
- Quedan 61 pares con provenance sólo parcial; sus fuentes agregadas no
  identifican con certeza el origen individual. No inventar ni rellenar citas.
- El scope de la métrica ledger `63` no está probado.
- Los diez UNKNOWN relacionales, las 385 disposiciones globales UNKNOWN y los
  162 leads activos siguen sin resolverse. Los 96 leads con provenance
  recuperada continúan siendo leads, no YES.
- Las nueve transiciones están explicadas como historia; no solicitan una
  reparación canónica.
- A-PRE-0 permanece `NOT_READY`, `predicate_result=false`; A-PRE-1 permanece
  `NOT_AUTHORIZED / NOT_EXECUTED`; `inventory.frozen=false`.

## 10. Verificación

- Manifest: 385 filas, 385 nombres únicos, 385 números únicos.
- Hashes protegidos registrados en §1; se mantienen sin cambios.
- No se modificaron manifest, ledger, `requirements.lock` ni ninguna baseline
  spec.
- No hubo actividad dinámica ni acceso a VM/DB/corpus/modelos.
- `git diff --check`: verificado tras crear este checkpoint y actualizar el
  índice.
- Sin commit; el worktree tenía cambios previos ajenos que se preservan.
