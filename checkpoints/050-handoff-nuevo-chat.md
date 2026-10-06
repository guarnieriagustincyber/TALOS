# Checkpoint 050 — handoff integral para nuevo chat

Fecha: 2026-10-01  
Repositorio: `guarnieriagustincyber/TALOS`  
Checkout observado: `/media/agustin/Laboratorio/study-engie`

## 1. Propósito y punto de reanudación

Este documento conserva el estado observable de la auditoría A-PRE y sus
límites. Es un handoff, no una continuación de la auditoría: no adjudica
pendientes, no corrige representaciones y no declara readiness.

El último checkpoint de trabajo es
[049 — arqueología del delta de contadores](./049-arqueologia-delta-contadores-manifest.md).
La reconciliación global S01–S16 de 048 sigue pendiente. En un chat nuevo leer
primero este handoff y el resumen ejecutivo; después consultar las fuentes
enlazadas aquí. No repetir 045–049 ni asumir que su documentación equivale a
evidencia dinámica.

Principio rector: **OBSERVE → CONSOLIDATE → VERIFY → DOCUMENT → HANDOFF**.

## 2. Identidad Git al crear el handoff

| Dato | Valor |
|---|---|
| Rama | `main` |
| HEAD | `f81134fc2293916210d53c8065f3a0049e52b0b4` |
| Árbol HEAD | `c322e78980ac72f24c66b1396014faefaac074a9` |
| Parent HEAD | `b17dd9c4dab098512aa6c148e7d36c613da41c28` |
| Último commit A-PRE relacionado | `f81134f` — `docs(certification): adjudicate S05 batch 05` |
| Estado antes de crear 050 | 11 paths modificados y 38 no rastreados; sin cambios staged |
| Estado de partida | Worktree ya sucio; no se limpió ni se atribuyó al handoff ningún cambio preexistente |

Al inicio, entre los paths modificados ya estaban `checkpoints/index.md` y
`files/A_PRE_0_SURFACE_MANIFEST.json`. Los checkpoints 015 y 023–049, archivos
de harness/tests y varios documentos también estaban sin seguimiento. Esta
sesión no cambió los artefactos protegidos ni ejecutó código del proyecto.
Los cambios locales ajenos al handoff deben preservarse.

Historial útil:

| Commit | Relación |
|---|---|
| `2ba7811f0d4a1e25f3746efd2ed9a149f8fefa8b` | Arqueología del repositorio y cobertura SSE; antecedente del trabajo B0. |
| `b12e34099336760e8fd55455526a580cd479dade` | Commit fuente de referencia de la especificación A-PRE inicial. |
| `fae02256a82160f0538b42b0cbc9b2534f0e44aa` | Commit persistente de recuperación A-PRE-0; árbol `2b1823eb03e99945f1bfdf38b25c0378161416a9`; parent `b12e34099336760e8fd55455526a580cd479dade`. |
| `9ddeccc00194b29556087b25f7a69ad5767af043` | Guardado de sesión A-PRE. |
| `baceb41`, `f975776`, `d5cfacd`, `b17dd9c`, `f81134f` | Adjudicaciones documentales S01–S05, respectivamente; ver historial completo con `git log`. |

El ledger identifica además un overlay calificado externo:

- Ruta registrada: `/home/agustin/apre-runner/cpython-3.10.21/evidence/a-pre-snapshot-identity-20261001/overlay-async-seccomp-v4`
- Commit: `2b2083795602f9099db43bb7ee35b0c030bdf51b`
- Tree: `d7ae2718c0a969fd1cf8eee0678f0d6f209c59a7`
- El overlay no se validó ni modificó en esta tarea. Su existencia/identidad
  registrada no certifica que incluya la especificación local actual.

No se creó commit 050. El índice ya tenía modificaciones históricas que no se
pueden aislar con seguridad del registro de los checkpoints previos; incluir
el índice completo habría incorporado cambios ajenos al handoff.

## 3. Método y límites de evidencia

Se leyeron el manifiesto, el ledger, las dos copias locales encontradas de la
especificación baseline, `requirements.lock`, el índice, los checkpoints
045–049, checkpoints de superficie citados en ellos, y la documentación de
baseline/coverage/harness. Las comprobaciones de estructura usaron parsing
JSON estándar y hashing SHA-256. `git status`, `git log`, comparación/hash de
archivos y `git diff --check` son las verificaciones de este guardado.

No se ejecutaron TALOS, FastAPI, pruebas, collector, parser/validator A-PRE,
workloads, probes, benchmarks, A-PRE-1 ni actividad dinámica. No se accedió a
DB, corpus, modelo, overlay o VM. Las afirmaciones B0–B1 siguientes son
resúmenes de evidencia ya documentada en los informes correspondientes; no se
repitieron sus experimentos.

## 4. Threat model B y baseline target-bound

- Modelo: **B**; workload potencialmente hostil. Base de confianza declarada:
  launcher, VM, kernel e hypervisor. Inyección deliberada de capacidades por
  infraestructura queda fuera del caso normal.
- VM designada: `fadena-lab`; Ubuntu 26.04 LTS (Resolute), x86_64,
  `7.0.0-34-generic`; ABI nativa x86_64; CPython target 3.10.21.
- Universo normativo: syscall table `arch/x86/entry/syscalls/syscall_64.tbl`
  del source package Ubuntu `linux 7.0.0-34.34`; SHA-256
  `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
- La tabla fuente se ligó a la captura read-only de `fadena-lab` y coincide
  por hash con el registro preservado de 385 filas. La firma OpenPGP de la
  fuente **no** fue verificada.
- x32 e i386 compat están excluidos del scope declarado, pero el enforcement
  por launcher no está calificado.
- Una adquisición anterior basada en Noble/Linux Mint permanece auxiliar y
  no atribuida; no sustituye la identidad Resolute designada.

Identidad de snapshot A-PRE registrada en el ledger: overlay v4 arriba. El
ledger también registra que la especificación que espera el overlay es
`/home/agustin/apre-runner/rev4-clean/docs/A_PRE_0_BASELINE_SPEC.md`, hash
`f058426b2a7315a90b651eb77d27f2e1c64209105fe8fdc4c1213218d19a0ad4`, y que
ese archivo **no está presente** en el overlay calificado.

## 5. Artefactos canónicos y hashes observados

| Artefacto | SHA-256 actual |
|---|---|
| `files/A_PRE_0_SURFACE_MANIFEST.json` | `801f529655f1f4f250a2a374d2afa63f858a9c0875e0e3dc620d112df5f9fd6e` |
| `files/A_PRE_0_QUALIFICATION_LEDGER.json` | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `docs/A_PRE_0_BASELINE_SPEC.md` | `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` |
| `files/A_PRE_0_BASELINE_SPEC.md` | `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Tabla de syscalls target-bound | `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455` |

Los hashes del manifiesto, ledger, especificación en `docs/` y lock coinciden
con los registrados por el checkpoint 049. El manifiesto ya estaba modificado
respecto de HEAD al iniciar este handoff; la igualdad con 049 sólo confirma el
snapshot documentado y que 050 no lo alteró. El ledger y el lock no aparecen
modificados en `git status`.

**Anomalía que no se resuelve aquí:** hay dos archivos locales llamados
`A_PRE_0_BASELINE_SPEC.md` y no son idénticos. La copia en `docs/` coincide con
el hash citado por 048/049; la copia en `files/` tiene otro hash y distinto
contenido. Ambas difieren también del hash `f058...` del archivo que el ledger
espera en el overlay. No se eligió ni sincronizó una copia.

SHA-256 de este checkpoint y del resumen ejecutivo se registran en la entrada
050 de `checkpoints/index.md` y en el reporte de cierre; no se auto-incluyen
dentro de su propio contenido.

## 6. Estado estructural verificado

Parsing del manifiesto actual:

- JSON válido.
- 385 filas; 385 `name` únicos; 385 `nr` únicos.
- 385/385 `disposition_status=UNKNOWN`.
- Cero disposiciones finales.
- `inventory.frozen=false`.
- 201 filas tienen `candidate_surface_context` no vacío; 184 no tienen
  contexto serializado.
- 198 filas tienen `candidate_surface_ids` no vacío; 187 no tienen IDs.
- Existen 239 contextos syscall↔superficie serializados.

El ledger declara `readiness.status=NOT_READY`,
`readiness.predicate_result=false`, y
`constraints.a_pre_1_authorized=false`. El campo independiente de estado
A-PRE-1 no existe en el ledger; su estado documental es
`NOT_AUTHORIZED / NOT_EXECUTED`. No se congeló el inventario.

## 7. Resumen B0, B0.5, B1-A, B1-B y B1-R

Esta línea es una auditoría distinta de la evaluación A-PRE de syscalls:

| Etapa | Resultado documentado | Límite que debe preservarse |
|---|---|---|
| B0 | Arqueología estática del path backend. Se determinó que el `AppContainer(use_mock=True)` normal no es un modo aislado: puede inicializar stores/DB y leer corpus/configuración. | B0 no importó ni inició TALOS. No demuestra uso productivo. |
| B0.5 | Probe guarded en subprocess: import/factory y startup con container sintético; `.env` bloqueado antes de leer contenido, warmup-thread suprimido; sin acceso a DB/corpus/proveedor real. | No califica el container/lifespan normal; confirma que el startup normal requiere otra frontera. |
| B1-A | Ruta real `POST /api/chat/query` en ASGI in-process, dependencias sintéticas; validación, SSE normal y conversión de excepción sintética observadas. | No servidor listening, lifecycle normal, provider, retrieval real ni integración React. |
| B1-B | Cuatro secuencias terminales SSE sintéticas: abstention/clarification sin `phase_complete`, truncated con finalización posterior y abort/cancel sin finalización. | Sólo serialización de ruta con fakes. La incompatibilidad source-traced de `chatService` con abstention/clarification no es prueba de integración UI real ni decisión de contrato. |
| B1-R | Contrato objetivo reporta `TECHNICAL PASS`: diez escenarios × tres repeticiones, guardas negativas y verifier independiente. | Repetibilidad de ruta sintética; no F6 PASS, producto integrado, provider real, real disconnect ni cliente React probado. |

Fuentes: `docs/BACKEND_OPERATIONAL_ARCHAEOLOGY.md`,
`docs/B1R_ACCEPTANCE_CONTRACT.md`, `docs/REALITY_AUDIT_REPORT.md` y
`docs/PLAN_MAESTRO_CIERRE_TALOS.md`. Los harness/tests B1-R actuales están en
el worktree no comprometido. Su `TECHNICAL PASS` no hace A-PRE-0 READY ni
autoriza A-PRE-1.

## 8. Estado de adjudicación documental S01–S16

Los conteos siguientes son decisiones documentadas en checkpoints de origen,
no un conteo global reconciliado ni evidencia de efecto. S14 es una superficie
de interfaces de biblioteca y no se suma a filas syscall. Para S06–S08, una
decisión checkpoint-only no se debe confundir con una relación ya materializada.

| Superficie | Decisiones documentadas | Representación/pending y límites |
|---|---|---|
| S01 | 28 YES: 13 previos + 15 de 047. En referencias históricas: 4 NO y 7 UNKNOWN. | 15/15 candidaturas nuevas cerradas; `open_by_handle_at` 304 conserva UNKNOWN histórico. 047 materializa las 15 nuevas. |
| S02 | 15 YES de payload; 3 NO: `fsync` 74, `fdatasync` 75, `sync_file_range` 277. | 19 exclusiones históricas de 016 preservadas; exclusión de superficie no es NO global. |
| S03 | 9 YES condicionados. | Condiciones por comando/dimensión del checkpoint 018. |
| S04 | 35 YES; `umask` NO/excluido de S04. | Cinco leads UNKNOWN/no promovidos: `quotactl`, `quotactl_fd`, `setxattrat`, `removexattrat`, `file_setattr`. |
| S05 | 6 YES, file-backed. | `madvise` UNKNOWN hasta particionar `MADV_*`; 17 leads no promovidos. No absorber S06. |
| S06 | 9 YES condicionados; `msync` UNKNOWN. | 19 leads preparados. Los 9 YES continúan checkpoint-only/no materializados en la representación descrita por 046. Distinguir anonymous/memfd/secretmem, shared/private y msync/madvise. |
| S07 | 17 YES para IP; `socketpair` NO para S07. | YES checkpoint-only según 026/046; no confundir IP con AF_UNIX. |
| S08 | 18 YES para AF_UNIX, incluidos `setsockopt` 54 y `getsockopt` 55. | 16 contextos aparecen como UNREVIEWED; 54/55 carecen de contexto S08 en el manifest descrito por 046. La decisión está documentada, la materialización quedó pendiente. Separar pathname, abstract y unnamed/socketpair. |
| S09 | 5 YES, SCM_RIGHTS/adquisición interproceso acotada. | Sólo transferencia SCM_RIGHTS; no incluir SCM_CREDENTIALS. |
| S10 | 31 YES y 6 NO. | 12 leads de readiness previos permanecen fuera de promoción. |
| S11 | 17 YES condicionados. | 14 leads de lifecycle/control no promovidos. |
| S12 | 3 YES de io_uring. | Membresía documental y BLOCKED histórico son dimensiones separadas; BLOCKED tiene perfil exacto limitado. |
| S13 | 6 YES de Linux native AIO. | BLOCKED sólo bajo el mismo perfil/hash probado; no extrapolar. |
| S14 | 9 interfaces POSIX AIO YES. | Interfaces de biblioteca; no son filas syscall, workers ni evidencia de ejecución. |
| S15 | `bpf`, `perf_event_open` condicionado y creación `userfaultfd`: 3 YES; `ioctl` UNKNOWN a nivel de familia. | FIONREAD es caso concreto OBSERVED, no adjudicación general de ioctl. Default-deny sigue `NOT_DEMONSTRATED`. |
| S16 | 33 YES materializados documentalmente. | 51 leads no promovidos. |

Fuentes de decisión por lotes: checkpoints 014/016/018/020/022/024/026/028/
030/032/034/036/038/039/040/041 y el cierre posterior S02 043. Los conteos
anteriores conservan los alcances escritos en esos checkpoints; no convierten
una adjudicación YES/NO de superficie en disposición global.

## 9. Efectos históricos y coverage

El ledger conserva **27 casos históricos acotados** en 17 filas: **16
OBSERVED** y **11 BLOCKED**. `runtime_effect_disposition_count=0`; ninguno de
esos casos cuenta por sí solo como disposición de syscall completa ni es
elegible para satisfacer el predicate A-PRE-0 actual antes de rebind al
snapshot calificado.

- **io_uring:** BLOCKED sólo para perfil
  `a-pre-native-async-deny-v1`, policy SHA-256
  `ff44e7f9573fe503fd023792d1e38c44ba8b4ac53275097559eaece82e0ea9e9`.
- **Linux native AIO:** BLOCKED sólo bajo ese mismo perfil/hash y alcance
  documentado.
- **FD inheritance:** FD deliberadamente inyectado = OBSERVED de sensibilidad
  del sensor; higiene de FDs del launcher normal = UNKNOWN.
- **MAP_SHARED:** FD/mapping externo inyectado = OBSERVED de capacidad/sensor;
  pathname sin FD = BLOCKED bajo su caso exacto; cobertura MAP_SHARED general
  = UNKNOWN.
- **AF_UNIX:** FD connected inyectado = OBSERVED de sensibilidad; pathname sin
  FD = BLOCKED bajo su caso exacto; cobertura IPC/socket general = UNKNOWN.
- **`sys.addaudithook`:** sensor auxiliar `AUXILIARY_ONLY`/`PARTIAL`; no prueba
  ausencia de efecto nativo.

No extrapolar casos de inyección al path normal del launcher, ni extender un
BLOCKED a una familia más amplia, variante distinta, perfil diferente o
snapshot diferente.

## 10. 045–049 y contador stale

- **045:** clasificó 60 contextos `UNREVIEWED`: 15 candidaturas S01 genuinas,
  42 relaciones ya adjudicadas pero mal representadas, y 3 UNKNOWN ya
  documentados. Registró la ausencia de contexto S08 para 54/55. No modificó
  decisiones ni artefactos canónicos.
- **046:** revisó 50 relaciones S06/S07/S08/S15: 44 `SAFE_TO_MATERIALIZE`,
  4 `ALREADY_CORRECT`, 2 UNKNOWN con formato de representación sin resolver.
  No materializó relaciones ni encontró contradicciones semánticas.
- **047:** adjudicó/materializó las 15 YES pendientes S01; conservó 385
  disposiciones globales UNKNOWN.
- **048:** detuvo la reconciliación global al comparar los contadores del
  manifest (204 contexto / 181 sin contexto) con los recálculos serializados
  (201 / 184); además 198 filas con IDs y 187 sin IDs. Los tres contextos sin
  IDs son S02 `fsync` 74, `fdatasync` 75 y `sync_file_range` 277, pero no
  explican el delta completo 204→201. No terminó el crosswalk de 385 filas.
- **049:** reconstruyó los snapshots y clasificó el caso **`STALE_COUNTER`**.
  204/181 eran correctos antes de S10; seis NO S10 y tres promociones S10/S11
  dan 201/184; luego tres NO S02 retiran IDs sin retirar los contextos y
  dejan 198/187. 201 context rows, 198 ID rows y 201 referencias potenciales
  son universos distintos. La explicación está resuelta documentalmente; el
  estado/formalización canónica del contador sigue pendiente.

Hashes SHA-256 de checkpoints actuales:

| Checkpoint | SHA-256 |
|---|---|
| 045 | `f8b36c340b9b6b5c1b937bd431316c2dde3c7ccd3aebc5688ab3e430f064df10` |
| 046 | `64f517ee00a11267697829f9d0c8741036103212d529f1a44facc09387077566` |
| 047 | `5dd675826d759512ccad756dfed6b3c1a3c9030b95a8b7b186cbbc83435efe07` |
| 048 | `c6694f961981145fae01471aa1c90398b2ddf5fd4c861d6ada25555318b06ffe` |
| 049 | `00e0c3dd1f2a4e6840a3a9b76c87e67b7a2bad04e753e22fb53b508c5e02a96c` |

## 11. Predicado A-PRE-0

Ledger: predicate `A_PRE_0_READY` v2, `result=false`. El resultado no se
recalcula ni se cambia en un handoff. Los siguientes estados reflejan el
ledger/checkpoints existentes:

| Requisito | Estado | Evidencia / motivo |
|---|---|---|
| Snapshot identity | `PARTIAL / FAIL` | VM y tabla target-bound; overlay v4 registrado. La especificación esperada no está en overlay; el checkout de trabajo está sucio. |
| Runtime / lock / platform | `PARTIAL` | Identidad declarada; lock hash preservado. El runtime/lock del overlay no se revalidó en esta tarea. |
| Target-bound syscall inventory | `PASS` estructural, no readiness | 385 filas únicas, tabla fuente hasheada; firma de source no verificada. |
| Perimeter / model | `UNKNOWN / FAIL` | Inventario de superficies/casos y variantes incompleto; B no elimina rutas UNKNOWN. |
| Required inventory | `FAIL` | 385 disposiciones globales UNKNOWN; no hay finales. |
| Launcher / policy | `UNKNOWN / FAIL` | Enforcer de x32/i386 y launcher normal no calificados; propuesta default-deny S15 no es prueba. |
| Integrity / fail-closed | `UNKNOWN / FAIL` | Collector, builder y verifier no validaron independientemente el ledger/predicate A-PRE en este snapshot; harness sintético no basta. |
| Collector | `UNKNOWN` | No ejecutado en esta tarea; no hay resultado TALOS. |
| Builder | `UNKNOWN` para A-PRE válido | Builder/harness sintético documentado; sin evidencia completa de una corrida A-PRE. |
| Verifier | `UNKNOWN` para A-PRE válido | Verifier sintético no sustituye ledger/schema validation independiente. |
| Independent valid evidence | `FAIL` | El ledger marca 0 casos históricos elegibles para el predicate actual. |
| Alternate paths | `UNKNOWN / FAIL` | Variantes, callsite/dependency traceability y rutas alternativas incompletas. |
| Ausencia de UNKNOWN relevantes | `FAIL` | 385 disposiciones globales permanecen UNKNOWN; required units y domains pendientes. |

Resultado: **A-PRE-0 `NOT_READY` / `predicate_result=false`**. A-PRE-1:
**`NOT_AUTHORIZED / NOT_EXECUTED`**. La documentación B1-R `TECHNICAL PASS`
no altera este resultado.

## 12. Estado: resuelto, pendiente y no autorizado

### HECHO / RESUELTO DOCUMENTALMENTE

- Adjudicaciones documentales progresivas S01–S16.
- Arqueología 045 y reconciliación de representación 046 con límites y estados
  descritos arriba.
- Adjudicación/materialización de las 15 S01 nuevas en 047.
- Diagnóstico de parada de 048.
- Causa histórica del delta del contador en 049: `STALE_COUNTER`.
- Invariantes estructurales actuales: 385 filas únicas y UNKNOWN; inventario
  no congelado; readiness falso.

### PENDIENTE

- Decidir cómo representar/recalcular formalmente los contadores stale sin
  perder provenance ni confundir contextos, IDs, referencias y decisiones.
- Aclarar cuál especificación baseline local es la autoridad y su relación con
  el hash que el overlay v4 espera.
- Completar crosswalk fila por fila de las 385 syscalls con surface,
  provenance y estado; reconciliar en definitiva S01–S16, diferencias de
  materialización, leads, overlaps y referencias históricas.
- Reevaluar el predicate A-PRE-0 sólo con evidencia existente válida y los
  requisitos completos; la consolidación documental no prueba efectos.

### NO AUTORIZADO

- A-PRE-1 y cualquier ejecución TALOS.
- Workloads reales, probes nuevos, suites, benchmarks o recolección.
- Cambios de corpus, modelos, DB, VM, overlay, runtime, seccomp o migraciones.
- Cambios a `requirements.lock`, manifest, ledger o decisiones semánticas sin
  autorización y evidencia correspondientes.

## 13. Invariantes que no deben romperse

1. Una referencia, lead, candidatura o membership de superficie no equivale a
   disposición global ni a efecto observado/bloqueado.
2. Mantener las 385 disposiciones globales UNKNOWN hasta una decisión/evidencia
   válida; no congelar `inventory`.
3. Mantener S05/file-backed separado de S06/anonymous/memfd/secretmem.
   `MAP_SHARED`/`MAP_PRIVATE`, `msync` y `madvise` siguen particiones distintas.
4. Mantener S07/IP separado de S08/AF_UNIX; preservar pathname/abstract/
   unnamed/socketpair y los límites de 54/55.
5. S09 es SCM_RIGHTS solamente; no incorporar SCM_CREDENTIALS.
6. S12/S13 memberships no son BLOCKED; BLOCKED requiere el hash/profile exacto.
7. S14 son interfaces de biblioteca, no syscalls.
8. FD/MAP_SHARED/AF_UNIX injection es sensibilidad del sensor, no higiene ni
   contención de la ruta normal.
9. `sys.addaudithook` es AUXILIARY_ONLY/PARTIAL.
10. No considerar el `TECHNICAL PASS` B1-R como A-PRE readiness, F6 pass ni
    permiso para A-PRE-1.
11. Preservar worktree preexistente; nunca resetear, limpiar o descartar
    cambios ajenos.

## 14. Próximo paso recomendado e instrucciones de reanudación

En un chat nuevo:

1. Verificar rama/HEAD/worktree e identidad de los artefactos y hashes de §2–5;
   no suponer que los archivos untracked del handoff están ya en HEAD.
2. Leer 049 y resolver en una decisión documental separada la semántica/
   representación futura de los contadores; resolver también la discrepancia
   entre copias de baseline sin sobrescribir ninguna por inferencia.
3. Sólo después, reanudar 048 con un crosswalk verificable de 385 filas. No
   declarar la reconciliación acabada hasta reconciliar provenance y
   materialización por superficie.
4. Mantener la separación documental/dinámica y volver a evaluar readiness
   sin ejecutar nada no autorizado.

Este checkpoint no inicia esos pasos; el handoff termina aquí.

## 15. Verificación de este handoff

- `git diff --check`: limpio después de crear los archivos.
- Artefactos protegidos: no modificados por esta tarea. El manifest tenía
  modificación preexistente desde el inicio; su hash al cierre debe seguir
  coincidiendo con `801f...`.
- `requirements.lock`: sin cambios; SHA-256 preservado.
- No se modificaron ledger, corpus, modelos, bases de datos, VM, overlay o
  runtime; no hubo actividad dinámica y no se ejecutaron TALOS ni A-PRE-1.
- Commit: `NOT_CREATED`; el worktree/index de partida contenía cambios ajenos
  y no fue posible aislar sólo las tres rutas autorizadas sin incorporar
  modificaciones previas.
- El archivo 049 ya existía pero no tenía entrada en el índice al iniciar
  050; el índice ahora registra 049 y ambos documentos 050.
