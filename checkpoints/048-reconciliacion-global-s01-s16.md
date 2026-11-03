# Directiva 048 — reconciliación global S01–S16: detenida por discrepancia estructural

Fecha: 2026-10-01

## 1. Resultado de la regla de parada

La primera pasada diagnóstica se detuvo al descubrir una discrepancia interna
no explicada entre los contadores globales declarados en
`syscall_disposition_contract` y los registros actualmente serializados en el
manifiesto. La directiva exige detenerse ante diferencias manifest ↔
representación que no se puedan reconciliar sin inferencia. No se actualizan
los contadores, no se normaliza el manifiesto y no se afirma que la
reconciliación global haya concluido.

Se completaron únicamente comprobaciones de estructura, hashes, estados
globales, conteos literales de relaciones/contextos y comparaciones puntuales
con 045–047 y los checkpoints fuente enumerados abajo. **No se construyó ni
validó el crosswalk semántico completo de 385 filas ni se reconciliaron en
detalle todos los checkpoints S01–S16.** Las cifras por superficie de §4 son
mediciones del estado actual del manifiesto y checkpoints ya consultados,
no una certificación de reconciliación global.

## 2. Snapshot y archivos examinados

HEAD: `f81134fc2293916210d53c8065f3a0049e52b0b4`. El worktree ya estaba sucio;
los cambios previos se preservaron.

| Archivo | SHA-256 al iniciar |
|---|---|
| `files/A_PRE_0_SURFACE_MANIFEST.json` | `801f529655f1f4f250a2a374d2afa63f858a9c0875e0e3dc620d112df5f9fd6e` |
| `files/A_PRE_0_QUALIFICATION_LEDGER.json` | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| `docs/A_PRE_0_BASELINE_SPEC.md` | `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` |
| `checkpoints/index.md` | `fc7aa6d3ec4071436cb45ffc9a4690d52ff509e4bbc066bc9f51aa221ac51b20` |
| Checkpoint 014 — S01 | `70e1cfc2c7a74b51ecaeaac4f45fa92fee8d4093a26132ee0c07b7f502256c7d` |
| Checkpoint 016 — S02 exclusiones | `081db47e946026af541a90154c2fe1458069cbe08e1c76dc4766faa7ce33345c` |
| Checkpoint 018 — S03 | `6d2505fee555d78d58caa29bb8655820cd25cdc4bc14872a1e2b91d8ce01195a` |
| Checkpoint 020 — S04 | `a16688f57f28578d3a51bd2e36296d7790d6fc1a0a58b2fd6a1e436d6e7e4fd4` |
| Checkpoint 022 — S05 | `7ba9938b77fead0f829936190b7a0557cb8fdf711f30b496b7d54720a2946c32` |
| Checkpoint 024 — S06 | `d6bf479432d0e522c632a9f352035e9f3653a85698c6f1ad7de081b93e5c7ce0` |
| Checkpoint 026 — S07 | `0868160d6425b065242a85f989c5e6a171c7dc98b1053857789aa2eb3f0ebdef` |
| Checkpoint 028 — S08 | `82bebe3d80b5b76e659d4ca8d637ecd96d7819d6a23ddf4a69c9c0f9f6991561` |
| Checkpoint 030 — S09 | `728a5daf4975769615f5b6f6a6ec36c6b0ca11659cad9ea777f111c44e39f64e` |
| Checkpoint 032 — S10 | `c67abfa815c1a80ff2a8392bb851f00d78ba01d2a2c39d5970dda5a3162a8bc1` |
| Checkpoint 034 — S11 | `5f73754a9315eb36ef508c8d6a808818cf99885b4234cd4bc0bba2f771b174a9` |
| Checkpoint 036 — S12 | `70a9d5ded4ab14c3dfab1e339b1a08e31646b2207980d1072a9c0d16a757393b` |
| Checkpoint 038 — S13 | `bb94d59025b75b5e6a3cf5030023fa5c1ce7e054e680f8b1745866b8bb171856` |
| Checkpoint 039 — S14 | `03d9585bb7e1aa0c4c97d7047854ed61a2467903422c4bc42c2e558d8eb610f4` |
| Checkpoint 040 — S15 | `ce503ec10eac9589621bb4bf60300e70bc7b4e76e2251ea1cde5471f850fb09a` |
| Checkpoint 041 — S16 | `866d7913798c336bee3fd13f46d97e969b8e8c1ed0aac30b1ba19a73f7736abb` |
| Checkpoint 043 — cierre S02 posterior | `be0c2ad34825b823cdb1a8d4d89bb54eef08c33b6ac382bd51e7043dc642bbce` |
| Checkpoint 045 — arqueología | `f8b36c340b9b6b5c1b937bd431316c2dde3c7ccd3aebc5688ab3e430f064df10` |
| Checkpoint 046 — representación | `64f517ee00a11267697829f9d0c8741036103212d529f1a44facc09387077566` |
| Checkpoint 047 — S01 | `5dd675826d759512ccad756dfed6b3c1a3c9030b95a8b7b186cbbc83435efe07` |

## 3. Discrepancia que detiene la reconciliación

El manifiesto declara actualmente:

- `rows_with_candidate_surface_context = 204`;
- `rows_without_surface_candidate_remain_unknown = 181`;
- `rows_without_candidate_surface_membership = 181`.

El recálculo literal de la estructura JSON actual produce:

| Medida derivada | Valor |
|---|---:|
| Filas normativas | 385 |
| Filas únicas con `candidate_surface_context` no vacío | 201 |
| Filas sin contexto de superficie | 184 |
| Contextos syscall↔superficie serializados (suma de contextos) | 239 |
| Filas con `candidate_surface_ids` no vacío | 198 |
| Filas sin `candidate_surface_ids` | 187 |
| Filas con `no_candidate_review` | 191 |
| Referencias `potential_surface_refs` serializadas | 201 |

Los tres registros que tienen contexto pero `candidate_surface_ids=[]` son
exactamente las decisiones `HUMAN_ADJUDICATED_NOT_MEMBER` S02:
`fsync` (74), `fdatasync` (75) y `sync_file_range` (277). Esto explica la
diferencia entre las 201 filas con contexto y las 198 filas con IDs de
candidato, pero **no explica** por qué el manifiesto declara 204 filas con
contexto, ni por qué declara 181 filas sin contexto/membresía en vez de los
recuentos derivados 184/187.

El número declarado 204 coincide con el total histórico de referencias
potenciales anotado en checkpoints tempranos, pero el campo actual se llama
`rows_with_candidate_surface_context`; no hay regla versionada que autorice
reinterpretar ese campo como aristas históricas ni una nota que reconcilie el
delta de tres. El recuento actual de 201 `potential_surface_refs` tampoco
explica por sí solo si tres pistas fueron consumidas, retiradas o si el
resumen es simplemente histórico. No se infiere la causa ni se reescriben
contadores.

**Clasificación:** `PENDIENTE_DE_DECISION` sobre la semántica/actualización de
los contadores de inventario, o de una aclaración documental inequívoca de su
linaje. Hasta resolverlo no se afirma:

- igualdad de métricas derivadas entre manifest y ledger;
- conteo reconciliado definitivo de referencias/leads;
- crosswalk semántico completo;
- estado reconciliado de todas las superficies.

## 4. Medidas estructurales disponibles antes de detenerse

La tabla siguiente describe lo que está materializado/documentado en la
representación presente, no un conteo histórico único de “candidaturas
originales”. `Contexto U` significa que el contexto permanece
`UNREVIEWED_CANDIDATE`; checkpoint 046 documenta algunos YES que no se
materializaron. `NO fuera de array` identifica una decisión documental que no
es una syscall miembro. Leads son conteos de los checkpoints fuente ya
citados; no se han reconciliado exhaustivamente todos los lotes de leads.

| Superficie | Representación actual observada | Decisiones fuente conocidas | Diferencia/documentación |
|---|---|---|---|
| S01 | 28 contextos YES, cero U | 13 YES de 014 + 15 YES de 047; 304 UNKNOWN histórico | `RESUELTO_DOCUMENTALMENTE` para el cierre 047; cruces de otras superficies no reabiertos. |
| S02 | 15 YES + 3 NO contextuales | 15 YES + 3 NO en 043; 19 relaciones históricas excluidas en 016 | Las 19 exclusiones no son NO global. `sync` = 162; `truncate` = 76. |
| S03 | 9 contextos YES | 9 decisiones condicionadas en 018 | Las condiciones viven en 018; se requiere cotejo fila-a-fila completo posterior a la parada. |
| S04 | 35 contextos YES; metadato excluye `umask` (95) | 35 YES; cinco pistas permanecen UNKNOWN/no promovidas: `quotactl`, `quotactl_fd`, `setxattrat`, `removexattrat`, `file_setattr` | `umask` es relación S04 excluida, no NO global. La cifra “seis leads” puede incluir esa exclusión como una sexta pista del lote; 020 distingue 1 exclusión + 5 UNKNOWN. |
| S05 | 6 contextos YES + `madvise` U | 6 YES file-backed; `madvise` UNKNOWN; 17 leads históricos | No absorber backing anonymous/memfd de S06. |
| S06 | 10 contextos U | 024: 9 YES condicionados, `msync` UNKNOWN; 19 leads preparados | 046 permite proponer materializar los 9 YES, pero aún no están materializados. |
| S07 | 17 contextos U | 026: 17 YES IP condicionados; `socketpair` NO S07 separado | Documentado en 046 como decisión checkpoint-only; IP separado de AF_UNIX. |
| S08 | 16 contextos U | 028: 18 YES AF_UNIX, incluidos 54/55 | 046 identifica 54/55 sin contexto S08 actual y los clasifica seguros para una futura materialización condicionada. |
| S09 | 5 contextos YES | 5 YES condicionados a `SCM_RIGHTS` o adquisición interproceso | `SCM_CREDENTIALS` permanece fuera de S09. |
| S10 | 31 contextos YES | 31 YES + 6 NO en 032; 12 leads de readiness anteriores | NO S10 no es disposición global; no se derivan leads adicionales aquí. |
| S11 | 17 contextos YES | 17 YES condicionados; 14 leads preparados | Mantener condiciones y no promover leads. |
| S12 | 3 contextos YES | 3 YES de io_uring; evidencia histórica BLOCKED acotada | Membership y BLOCKED son dimensiones separadas. |
| S13 | 6 contextos YES | 6 YES native AIO; casos BLOCKED exactos documentados | No extrapolar fuera de perfil/hash probado. |
| S14 | 9 interfaces de biblioteca, cero filas syscall | 9 interfaces YES en 039 | No sumar como memberships syscall ni con el conteo de 385 filas. |
| S15 | 3 contextos YES + `ioctl` U | `bpf` YES, `perf_event_open` YES condicional, creación `userfaultfd` YES; `ioctl` familia UNKNOWN | `FIONREAD` es sólo effect case OBSERVED. Proposed default-deny permanece `NOT_DEMONSTRATED`. |
| S16 | 33 contextos YES | 33 YES condicionados + 51 leads no promovidos en 041 | Leads preservados, no memberships. |

Esta tabla no resuelve la diferencia de contadores del §3 y no debe usarse
como la tabla global definitiva solicitada por la Directiva 048.

## 5. Conteo canónico que sí puede afirmarse antes de la parada

Recuento derivado directamente de los contextos actuales:

- 191 contextos `HUMAN_ADJUDICATED_CANDIDATE`;
- 3 contextos `HUMAN_ADJUDICATED_NOT_MEMBER`;
- 45 contextos `UNREVIEWED_CANDIDATE`;
- 239 contextos syscall↔superficie en total.

Estas son **relaciones de contexto serializadas**, no el total de todas las
decisiones históricas. En particular no incluyen como contexto S07 el NO de
`socketpair`, el NO S04 de `umask`, los 44 YES checkpoint-only S06–S08, ni
las dos decisiones S08 54/55 ausentes del contexto actual. Por ello no se
presentan como conteo global reconciliado de YES/NO/UNKNOWN.

Conteo derivado de registros de adjudicación por fila actualmente serializados:

- 178 decisiones YES/YES_CONDITIONAL con referencia explícita en
  `surface_membership_adjudications`;
- 9 decisiones NO con referencia explícita en esa estructura;
- 15 YES S01 se representan en los estados agregados/contextos y en el array
  S01, con scope y referencia al checkpoint 047, pero no como objeto dentro
  de `surface_membership_adjudications` (su ubicación sigue el patrón
  heredado de 014).

Las decisiones checkpoint-only de 024/026/028 no se suman a las materializadas.
La representación heredada de S01 está explicada por 014/047, pero la
estructura relacional no es uniforme entre lotes. No se cambia durante esta
pasada.

## 6. Filas normativas e invariantes que sí se verificaron

Se parseó el manifiesto JSON y se midió:

- 385 filas;
- 385 nombres únicos;
- 385 números únicos;
- 385/385 `disposition_status=UNKNOWN`;
- cero disposiciones globales finales;
- `inventory.frozen=false`;
- ledger `readiness.status=NOT_READY` y `predicate_result=false`;
- ledger referencia `A_PRE_0_SURFACE_MANIFEST.json#syscall_disposition_contract`;
- `candidate_surface_ids` no coincide con el conjunto de contextos sólo en
  tres filas: las exclusiones S02 explícitas 74/75/277 ya señaladas;
- no se cambió disposition global por ninguna relación superficial.

No se generó el listado exhaustivo de 385 filas con provenance, ni se declaró
que cada decisión histórica esté reconciliada. Queda pendiente tras resolver
§3.

## 7. Cobertura de efectos y A-PRE-0 (alcance parcial)

El ledger registra 27 casos históricos acotados —16 `OBSERVED`, 11
`BLOCKED`, distribuidos en 17 filas— y declara que ninguno es elegible para
el predicate actual hasta rebinding al snapshot/overlay calificado. Los
estados de relación S12/S13 no se convierten en BLOCKED. La evidencia de
inyección de FD, MAP_SHARED y AF_UNIX no prueba containment normal-path;
`sys.addaudithook` está en `AUXILIARY_ONLY`/`PARTIAL`. Estos son límites
documentados, no reconciliación de cada case/profile/hash.

El predicate ledger enumera 17 checks requeridos y tiene `result=false`.
Entre las causas expresas están `inventory.frozen=false`, disposiciones y
particiones nativas incompletas, callsite traceability incompleta, scope de
ABI compat sin enforcement calificado, normativa ausente del overlay
calificado, paths/domains UNKNOWN, cobertura runtime incompleta y ausencia
de validator independiente.

| Requisito | Estado en esta pasada | Evidencia/razón |
|---|---|---|
| Inventario target-bound | `PASS` estructural, no readiness | Tabla target/source package y hash están ligados en manifest; 385 filas únicas. |
| Contadores manifest ↔ estructura | `FAIL / DETENIDO` | Delta no explicado del §3. |
| Snapshot/runtime/platform + lock | `UNKNOWN` para readiness | Ledger contiene identidad/lock; no se revalidó el overlay, no se ejecutó entorno. |
| Perimeter/model y required inventory | `UNKNOWN` | No se reconciliaron las unidades/casos del spec con evidencia elegible. |
| Launcher/policy e integridad/fail-closed | `UNKNOWN` | El ledger enumera calificación de enforcement pendiente; la propuesta S15 no es enforcement. |
| Collector/builder/verifier | `UNKNOWN` | No se ejecutaron; el predicate registra falta de validator independiente. |
| Independent valid evidence | `FAIL` para el predicate actual | Ledger declara que ningún caso histórico es elegible antes de rebinding. |
| Alternate paths | `UNKNOWN` | No se hizo el crosswalk completo; siguen declarados como gaps. |
| Ausencia de UNKNOWN relevantes | `FAIL` | 385 disposiciones UNKNOWN y required paths/domains UNKNOWN. |
| A-PRE-0 | `FAIL` / `NOT_READY` | Predicate registrado `false`; no se altera. |
| A-PRE-1 | `NOT AUTHORIZED / NOT EXECUTED` | Estado documental preservado; no ejecutado. |

No se alteran las disposiciones de cobertura. No se reporta una evaluación
completa PASS/FAIL por cada uno de los 17 checks porque la parada impidió
reconciliar la evidencia detallada requerida.

## 8. Archivos cambiados, preservación y actividad

Sólo se creó este checkpoint y se añadió una línea a `checkpoints/index.md`.
No se modificaron manifest, ledger, `requirements.lock` ni baseline spec.
Hashes de manifest, ledger y lock al cierre iguales al snapshot de §2.
El índice fue actualizado únicamente para registrar este punto de parada;
su SHA-256 posterior es
`8b763f055757a948ac054d1d2038e9a329613639652df884692c448461bee68c`.
Los hashes finales de manifest, ledger y `requirements.lock` son,
respectivamente, los de §2. El ledger conserva
`constraints.a_pre_1_authorized=false`.

`git diff --check` pasó. No se ejecutaron TALOS, FastAPI, workloads, probes,
benchmarks, tests, corpus, modelos, operaciones de base de datos ni A-PRE-1.
No hubo actividad dinámica. No se hizo commit.

## 9. Próximo paso permitido

Detener la reconciliación global. Se requiere aclarar la semántica/provenance
de `rows_with_candidate_surface_context` y de los dos contadores derivados
antes de continuar con el crosswalk 385×S01–S16. No modificar esos valores
por aproximación ni reanudar automáticamente la consolidación.
