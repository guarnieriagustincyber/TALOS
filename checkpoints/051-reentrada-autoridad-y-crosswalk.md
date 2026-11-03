# Checkpoint 051 — reentrada, autoridad y crosswalk

Fecha: 2026-10-01
Repositorio: `guarnieriagustincyber/TALOS`
HEAD inicial observado: `f81134fc2293916210d53c8065f3a0049e52b0b4`

## 1. Resultado y regla de parada

**`STOP_REASON = UNRESOLVED_PROVENANCE`**

La arqueología de los contadores confirma reproduciblemente `STALE_COUNTER`;
sin embargo, la autoridad única de `A_PRE_0_BASELINE_SPEC.md` no se puede
establecer: las dos copias locales tienen contenido y hashes distintos, ambas
tienen referencias documentales y ninguna coincide con el hash de la
especificación que el ledger asocia al overlay v4. El ledger registra además
que esa especificación no está presente en dicho overlay.

Por la regla de parada, no se inició el crosswalk clasificatorio fila por
fila, no se reconcilió globalmente S01–S16, y no se asignaron categorías ni
decisiones nuevas. El registro serializado de 385 filas de 049 §10 permanece
como fuente row-wise ya existente, pero no se declara aquí como un crosswalk
reconciliado ni como evidencia de autoridad para la baseline.

## 2. Estado inicial, identidad y hashes

| Artefacto | SHA-256 inicial declarado y comprobado |
|---|---|
| Manifest: `files/A_PRE_0_SURFACE_MANIFEST.json` | `801f529655f1f4f250a2a374d2afa63f858a9c0875e0e3dc620d112df5f9fd6e` |
| Ledger: `files/A_PRE_0_QUALIFICATION_LEDGER.json` | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Spec en `docs/` | `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` |
| Spec en `files/` | `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0` |

HEAD coincide con el declarado. El worktree estaba sucio antes de esta tarea,
incluidos el índice, el manifest, documentos, scripts y archivos sin
seguimiento. Los cambios preexistentes se preservaron. El checkpoint 051 y
una sola entrada en `checkpoints/index.md` son los únicos cambios de esta
tarea.

La cadena leída en orden fue 048 → 049 → 050: 048 detuvo la reconciliación y
no había completado el crosswalk; 049 reconstruyó los contadores y los
clasificó `STALE_COUNTER`; 050 dejó como pendientes la autoridad de baseline
y el crosswalk. El resumen 050 presenta 204/181 frente a 201/184 y 198/187;
la explicación aritmética completa está en §3–4.

## 3. Autoridad de contadores y diagnóstico `STALE_COUNTER`

El JSON del manifest y el ledger se parsearon sin ejecutar código del
proyecto. Los conteos directos reproducidos sobre el array
`syscall_disposition_contract.rows` son:

- 385 filas, 385 nombres únicos, 385 números únicos;
- 201 filas con `static_disposition_review.candidate_surface_context`
  no vacío; 184 sin contexto;
- 198 filas con `candidate_surface_ids` no vacío; 187 sin IDs;
- 239 relaciones de contexto fila↔superficie;
- 201 aristas `potential_surface_refs` distribuidas en 183 filas;
- 191 filas con `no_candidate_review`;
- 385/385 disposiciones globales `UNKNOWN`.

Fórmulas aplicadas: contexto = número de filas cuyo array de contexto bajo
`static_disposition_review` no está vacío; sin contexto = `385 - contexto`;
con IDs = número de filas cuyo `candidate_surface_ids` no está vacío; sin IDs
= `385 - con IDs`; relaciones = suma de longitudes de los arrays de contexto;
referencias = suma de longitudes de `potential_surface_refs`.

| Archivo/campo | Declarado | Recalculable y fórmula | Origen/fecha | Actual o snapshot | Autoridad documental |
|---|---:|---:|---|---|---|
| Manifest, `syscall_disposition_contract.rows_with_candidate_surface_context` | 204 | 201; filas con array `candidate_surface_context` no vacío | Contador correcto en snapshots previos a S10; checkpoints 048/049, 2026-10-01 | Campo actual stale; 204 es histórico | Las filas del manifest son fuente primaria; campo agregado no prevalece frente al recálculo de esas filas |
| Manifest, `rows_without_surface_candidate_remain_unknown` | 181 | 184; complemento `385 - 201` | Se originó como complemento del contador de contexto; snapshots pre-S10 | Campo actual stale | Métrica complementaria histórica; no es el total actual de filas UNKNOWN |
| Manifest, `rows_without_candidate_surface_membership` | 181 | 187; complemento de filas con IDs no vacíos | Se mantuvo sincronizado con el contador 204/181 histórico; 049 | Campo actual stale | Datos por fila son primarios; este agregado no representa una categoría semántica |
| Ledger, `inventory.syscall_dispositions.rows_with_candidate_surface_context` | 204 | 201 mediante la fórmula del manifest | Copia del resumen manifest; 049, 2026-10-01 | Serializado actualmente, pero stale | No es un cálculo independiente: el ledger referencia el manifest |
| Ledger, `inventory.syscall_dispositions.rows_without_surface_candidate_remain_unknown` | 181 | 184 mediante `385 - contexto` | Copia del resumen manifest | Serializado actualmente, pero stale | No independiente ni autoritativo sobre filas fuente |
| Ledger, `inventory.syscall_dispositions.rows_without_candidate_surface_membership` | 181 | 187 mediante `385 - filas con IDs` | Copia del resumen manifest | Serializado actualmente, pero stale | No independiente ni autoritativo sobre filas fuente |
| Manifest, `no_candidate_review.potential_surface_refs` en filas | No hay campo agregado equivalente actual; 049 registra 204 aristas históricas | 201 aristas actuales; suma de longitudes de arrays | Checkpoints 011/012 registraban 204 aristas históricas; 032/034 consumieron tres aristas | Métrica informativa de referencias, no contador de filas | Aristas fila-superficie; universo distinto de contexto e IDs |
| Manifest, relaciones `candidate_surface_context` | — | 239; suma de relaciones en las 385 filas | Snapshot actual, 049 | Métrica estructural actual | No equivale a 239 filas ni a 239 adjudicaciones independientes |
| Manifest, `rows_with_historical_case_evidence` / `historical_case_count` | 17 filas / 27 casos | 17 filas / 27 casos según el resumen compartido en manifest y ledger | Snapshot actual; 048/049 | Snapshot actual informado | Métrica histórica de casos, no filas con candidato ni disposición global |
| Manifest, `runtime_effect_disposition_count` | 0 | 0 en el estado serializado | Snapshot actual; 048/049 | Actual | Métrica de efectos; no se transforma en disposición estática |

La cronología reproducida de hashes de snapshots del manifest verifica el
origen temporal del stale:

| Snapshot | SHA-256 del manifest | Contexto: recalculado / declarado | IDs: recalculado / declarado | Referencias | Resultado |
|---|---|---:|---:|---:|---|
| `fae02256a8` | `64daf1399ae980b1d20fa5f1cc51224ee303a61beb7d1afdce1409809cc3b718` | 191 / 191 | 191 / 194 | 204 edges | Snapshot de recuperación |
| `2c3a0b5795` | `80c819a6be06603985dd6bbb4fb94724ed8dab0a4f94f2afa2a03c4dcc13369e` | 204 / 204 | 204 / 181 | 204 edges | Primer snapshot donde el resumen 204/181 coincide con contexto/IDs según 049; las fuentes describen además 204 referencias |
| `8711e67314` | `1e94d1dd65fb4f962e2f4d2db803822dc862c7dee7ee868a0af6bbf30ccdd110` | 204 / 204 | 204 / 181 | 204 edges | Pre-S10 |
| `32cc89dc6e` | `49ec91d7e567bd812860543c4f0262e52fbb4222c81b0ad5a56dd440a69ac7a6` | 200 / 204 | 200 / 181 | 202 edges | Seis salidas S10 y dos promociones S10; resumen no se actualiza |
| `1a8300da95` | `efcd4a9898cc088c660d88b41633733745f9cc1fac4fb628f13dbe7e47b97a98` | 201 / 204 | 201 / 181 | 201 edges | Promoción S11 de `pidfd_open` |
| `97e3296459` | `9e0f2f0f07240a0902598f989380c2febd7f2a1ee5f9314d8de156b08cc69a3e` | 201 / 204 | 198 / 181 | 201 edges | Tres exclusiones S02 retiran IDs y conservan contexto |
| Actual / `2080ce1cfa` | `801f529655f1f4f250a2a374d2afa63f858a9c0875e0e3dc620d112df5f9fd6e` | 201 / 204 | 198 / 181 | 201 edges | Mismo resultado estructural que el snapshot final de 049 |

**Conclusión:** `STALE_COUNTER` de 049 queda demostrado por recálculo de los
arrays del JSON actual y por comparación reproducible de los snapshots
históricos. El manifest y el ledger conservan 204/181; esos valores no se
corrigen aquí. La igualdad numérica histórica entre 204 filas con contexto y
204 aristas de referencia no vuelve equivalentes sus definiciones.

## 4. Reconciliación exacta de los deltas de 048

Comparación directa entre snapshot pre-S10 `8711e67314` y el manifest actual:

| Delta | Filas exactas | Explicación documentada |
|---|---|---|
| Contexto: sale | 13 `rt_sigaction`; 14 `rt_sigprocmask`; 15 `rt_sigreturn`; 127 `rt_sigpending`; 131 `sigaltstack`; 245 `mq_getsetattr` | Seis decisiones NO S10, checkpoint 032 |
| Contexto: entra | 129 `rt_sigqueueinfo`; 297 `rt_tgsigqueueinfo` | Promociones YES S10, checkpoint 032 |
| Contexto: entra | 434 `pidfd_open` | Promoción YES S11, checkpoint 034 |
| IDs: sale además | 74 `fsync`; 75 `fdatasync`; 277 `sync_file_range` | Tres exclusiones NO S02, checkpoint 043; el contexto `HUMAN_ADJUDICATED_NOT_MEMBER` se conserva |
| Referencias potenciales: salen | `(129, S10)`; `(297, S10)`; `(434, S11)` | Las relaciones pasan a decisiones/contextos documentados en checkpoints 032/034 |

Por tanto, `204 - 6 + 3 = 201` filas con contexto. Las tres exclusiones S02
**no** explican ese delta: no eliminan contexto; únicamente explican que
`201` filas con contexto contengan `198` filas con IDs. El cambio de IDs desde
el snapshot pre-S10 es `204 - 6 - 3 + 3 = 198`; su complemento es
`181 + 6 + 3 - 3 = 187`. Los números `198 - 187 = 11` son la diferencia
aritmética de los tamaños complementarios, no un grupo identificable de once
syscalls.

Esto separa los tres deltas sin inferencia:

- `204 → 201` contexto: seis salidas S10, tres entradas S10/S11, neto −3.
- `204 → 198` filas con IDs: seis salidas S10, tres salidas S02, tres
  entradas S10/S11, neto −6.
- `204 → 201` referencias: tres aristas consumidas; las referencias son
  relaciones pendientes, no filas ni IDs actuales.

## 5. Autoridad y provenance de las baseline specs

Las dos copias fueron comparadas por SHA-256, tamaño, estructura y contenido.
No son copias byte-identical ni revisiones semánticamente equivalentes:

| Artefacto | SHA-256 | Referenciado por | Rol documental observado | Autoridad |
|---|---|---|---|---|
| `docs/A_PRE_0_BASELINE_SPEC.md` | `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` | 048/049 registran su hash; handoff 050 compara esta copia; documentación en `docs/` la enlaza como spec. | 27,283 bytes / 474 líneas; cabecera `A-PRE-0: SPECIFIED`; especificación concisa PRE. El blob exacto aparece en la historia disponible desde `a3c8e2dab269d7a98184e36f2a7f6511b4a17ac9` (2026-09-30 16:27-03:00), reaparece en snapshots posteriores y está presente en el snapshot independiente `e33c5b521df631b7cb10150378149cb09d791889`. El commit más antiguo consultado con esa ruta, `ded3ccf20b4b3ab7379e0d709acc5ee8653612df`, contiene una revisión distinta (SHA-256 `2c9c3743f2b4a00b5edb478b9aa6cd36492d700dddcbd9c47c002a00d2a47a45`). En el worktree observado el archivo actual no está rastreado. | Referenciada, pero no demostrada como especificación normativa única |
| `files/A_PRE_0_BASELINE_SPEC.md` | `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0` | Checkpoint 012 cita esta ruta; la copia se versionó como artefacto de recuperación. Handoff 050 registra ambas copias. | 67,288 bytes / 1,105 líneas; cabecera `A-PRE-0: NOT READY`; amplía la spec con requisitos de readiness, predicate, ledger, cruce 1:1, ABI, adjudicaciones y revisión de filas sin candidata. Está rastreada en el checkout. Commit persistente de recuperación `fae02256a82160f0538b42b0cbc9b2534f0e44aa`; snapshot independiente `e33c5b521df631b7cb10150378149cb09d791889` contiene este blob también. | Referenciada, pero no demostrada como especificación normativa única |
| Spec externa esperada por overlay v4 | `f058426b2a7315a90b651eb77d27f2e1c64209105fe8fdc4c1213218d19a0ad4` | `files/A_PRE_0_QUALIFICATION_LEDGER.json`, `qualification_identity.current_normative_spec` | El ledger registra esa ruta como `current_normative_spec` y `present_in_qualified_overlay=false`. No se accedió al overlay ni a la ruta externa; no se puede comparar su contenido. | No es ninguna de las dos copias locales por hash; contenido/autoridad no verificables aquí |

La comparación semántica muestra cambios materiales de alcance/estado, no
sólo formato: `SPECIFIED` frente a `NOT READY`; la copia `files/` incorpora
secciones 4.1 y posteriores de predicate de readiness, verificación
independiente, crosswalk y adjudicaciones que no aparecen en la copia `docs/`.
La copia `docs/` exacta puede rastrearse a `a3c8e2d`; una revisión anterior
del mismo path en `ded3ccf` tenía otro hash. El snapshot independiente
`e33c5b5` contiene ambas copias actuales; la copia `files/` fue persistida en
los artefactos de recuperación por `fae0225`. Esta relación temporal explica
que existan versiones evolucionadas, pero no decide cuál tiene autoridad
para el snapshot/overlay calificado.

El hash `f058…` no coincide con ninguna copia local y el ledger lo declara
ausente del overlay v4. No es lícito atribuirle el contenido de una copia por
parecido, ruta o secuencia temporal. No se reemplazó, editó ni eligió ninguna
copia.

El manifest no contiene un hash de baseline spec; su campo de control enlaza
el ledger/contrato de disposiciones, no una de estas copias. Los checkpoints
048 y 049 registran `b458…`; el handoff 050 registra `b458…` y `23e…`; el
ledger registra `f058…`. La búsqueda del índice no encontró hash de baseline
spec: `checkpoints/index.md` sólo registra la secuencia de checkpoints. La
copia `files/` también aparece por ruta en 012. No hay una referencia local
que ate inequívocamente una de las dos copias al hash `f058…`.

**`BASELINE_SPEC_AUTHORITY = UNRESOLVED`**

## 6. Crosswalk de 385 filas — detenido antes de clasificar

La comprobación estructural del registro del manifest da 385 filas únicas
por número y nombre; todas conservan disposición global `UNKNOWN`. El
registro row-wise de manifest y la tabla raw de 385 filas ya escrita en 049
§10 permiten inspeccionar números, nombres, contextos, IDs, referencias y
provenance serializada. En la representación actual se cuentan 201 filas con
contexto, 198 con IDs, 201 aristas de referencia y 239 relaciones de
contexto.

No se genera aquí el crosswalk solicitado con exactamente una categoría por
fila. La fase 4 estaba condicionada a que las fases 2–3 no produjeran un
bloqueo; la autoridad de la baseline quedó `UNRESOLVED`, por lo que completar
orígenes, adjudicaciones, exclusiones, leads, UNKNOWN y diferencias de
materialización fila por fila dependería de una base documental con autoridad
no establecida. Asignar cualquiera de las siete categorías en estas
condiciones podría convertir diferencias de representación o evidencia
histórica en adjudicaciones nuevas. Las categorías no se asignan; 049 §10 se
cita como inventario serializado preexistente, no como sustituto del
crosswalk ni como verificación de decisiones globales.

## 7. Contradicciones y decisión de reanudación

1. La explicación histórica `STALE_COUNTER` sí es reproducible; no hay motivo
   para reescribir contadores en esta tarea.
2. Las dos baseline specs locales difieren byte y semánticamente. Ambas tienen
   referencias documentales, mientras que el ledger usa un tercer hash y
   declara ausente su archivo en el overlay calificado.
3. No se puede demostrar qué copia gobierna el crosswalk 048 ni si cualquiera
   de ellas corresponde al hash `f058…`.
4. En consecuencia, **048 no puede reanudarse** en esta tarea. No se cierra
   la reconciliación de representación, leads, exclusiones o relaciones
   checkpoint-only.

## 8. Estado final e invariantes

| Estado | Resultado |
|---|---|
| A-PRE-0 | `NOT_READY`; `predicate_result=false` |
| A-PRE-1 | `NOT_AUTHORIZED / NOT_EXECUTED`; ledger: `constraints.a_pre_1_authorized=false` |
| Inventory frozen | `false` |
| Disposiciones globales | 385/385 `UNKNOWN`; ninguna disposición final |
| Crosswalk / global dispositions | Crosswalk clasificatorio 385-row detenido; no se modifican disposiciones |
| Dynamic execution | Ninguna; no se ejecutó TALOS, FastAPI, endpoints, tests, workloads, probes, benchmarks ni acceso a VM, DB, corpus o modelos |

No se congeló inventory, no se promovieron leads, no se convirtió UNKNOWN en
YES/NO, no se ejecutó actividad dinámica y no se cambió manifest, ledger,
baseline spec ni `requirements.lock`.

## 9. Verificación final

| Comprobación | Resultado |
|---|---|
| JSON válido | Manifest y ledger parsean correctamente |
| Filas/nombres/números únicos | 385 / 385 / 385 |
| Cambios canónicos no autorizados | 0; ninguno de los artefactos protegidos fue editado |
| Manifest inicial = final | `801f529655f1f4f250a2a374d2afa63f858a9c0875e0e3dc620d112df5f9fd6e` |
| Ledger inicial = final | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` inicial = final | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Baseline `docs/` inicial = final | `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` |
| Baseline `files/` inicial = final | `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0` |
| `git diff --check` | Passed |
| Actividad dinámica | Ninguna |
