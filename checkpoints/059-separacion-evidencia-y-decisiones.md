# Checkpoint 059 — separación final entre evidencia descriptiva y decisiones normativas

Fecha: 2026-10-01
Base: estado consolidado en CP058; lectura selectiva de fuentes que sostienen
afirmaciones concretas. No adjudica relaciones ni modifica el canon.

## 1. Estado de partida

Se toman como vinculantes los estados consolidados por CP058:

- Crosswalk descriptivo: 385/385 filas; 385 nombres y números únicos.
- Disposición global: 385/385 `UNKNOWN`.
- Leads: 162 tags, con 5 pares ya cubiertos por exclusiones; 157 relaciones
  abiertas.
- UNKNOWN relacionales documentados: 10.
- Relaciones checkpoint-only: 77.
- Pares `PROVENANCE_PARTIAL`: 61.
- Contador `human_adjudicated_candidate_relation_count=63`:
  `SCOPE_UNPROVEN`.
- `BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED`;
  `EXTERNAL_SPEC_ARTIFACT = UNRECOVERED`;
  `STOP_REASON = UNRESOLVED_PROVENANCE`.
- A-PRE-0 `NOT_READY`; A-PRE-1 `NOT_AUTHORIZED / NOT_EXECUTED`;
  `inventory.frozen=false`.

Hashes del snapshot protegido, verificados al cierre:

| Artefacto | SHA-256 |
|---|---|
| Manifest | `801f529655f1f4f250a2a374d2afa63f858a9c0875e0e3dc620d112df5f9fd6e` |
| Ledger | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Baseline spec `docs/` | `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` |
| Baseline spec `files/` | `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0` |

No se reconstruye el crosswalk. Las consultas se limitaron a verificar las
referencias de los diez UNKNOWN, grupos de 77, el estado externo `f058…` y
los invariantes locales. No hubo workloads, probes, TALOS, FastAPI,
benchmarks, pruebas, validadores, lectura/escritura de producción, VM, DB,
corpus o modelos.

## 2. Regla de clasificación

La categoría principal se asigna al problema operativo consolidado, no a
cada mención que aparece en varios artefactos. Una unidad documental puede
estar cerrada descriptivamente mientras la decisión normativa que esa fuente
registra sigue sin autoridad para convertirse en estado canónico.

Se mantienen separadas:

```text
PROVENANCE GAP ≠ SEMANTIC GAP ≠ NORMATIVE GAP
```

- **Provenance gap:** falta demostrar origen/linaje de una referencia
  histórica concreta.
- **Semantic gap:** falta conocer/particionar con evidencia el efecto,
  recurso o variante relevante.
- **Normative gap:** falta decidir si ese efecto/variante pertenece a una
  superficie o satisface el contrato de disposición/readiness.

La existencia de un checkpoint, su fecha, tracking Git, hash local o parecido
semántico no establece por sí sola autoridad normativa. Las clasificaciones
que siguen describen evidencia y dependencias; no son una selección de
baseline.

## 3. Registro consolidado de pendientes y cierres

Cada ID tiene una sola categoría principal. La dependencia indica si la
afirmación descrita (no una elección de conveniencia) requiere resolver la
autoridad de baseline: `YES`, `NO` o `PARTIAL`.

| ID | Objeto/pendiente | Evidencia existente | Categoría | Dependencia baseline | ¿Decisión humana? | Crosswalk descriptivo | Cierre normativo/global 048 | Cambio canónico | A-PRE-0 READY |
|---|---|---|---|---|---|---|---|---|---|
| D01 | Autoridad del artefacto normativo `f058…` | Ledger identifica path/hash externo y `present_in_qualified_overlay=false`; CP052 no recupera bytes ni vínculo con las dos copias locales; CP053 conserva C | `PROVENANCE_UNRESOLVED` | `YES` | Sí, para fijar una autoridad aplicable; evidencia de identidad histórica aún no existe | No bloquea | Sí, bloquea resoluciones normativas | Sí, bloquea cambios que se justifiquen como canónicos bajo esa norma | Sí |
| D02 | 44 YES condicionales checkpoint-only (9 S06, 17 S07, 18 S08) | CP024/026/028 especifican syscall y scope; CP046 confirma diferencia de representación | `DOCUMENTARY_REPAIR_REQUIRED` | `PARTIAL`: no para describir el outcome escrito, sí para declararlo la representación normativa canónica | No para describir; sí autorización/cambio controlado si se decide reparar representación | No | No impide el cierre descriptivo; sí impide afirmar representación completa | Sí, si se autoriza materialización; no hacerla aquí | Impide calificar snapshot canónico completo mientras siga requerido |
| D03 | 157 relaciones activas con tag `LEAD` | CP058 §5.1 contiene los pares; 96 con referencia de lead exacta, 61 con provenance parcial | `NORMATIVE_DECISION_REQUIRED` | `YES` para decidir bajo el contrato A-PRE-0 no seleccionado | Sí, por outcome relacional (se pueden agrupar revisiones, no presumir un único outcome) | No | Sí | Sí, si el outcome se serializa después | Sí, según relación/scope requerida |
| D04 | 10 relaciones `UNKNOWN` documentadas | CP014/022/024/040 expresan UNKNOWN y sus límites; ver §5 | `NORMATIVE_DECISION_REQUIRED` | `YES` | Sí; evidencia existente no resuelve semántica/alcance | No | Sí | Sí, si se cambia el estado relacional | Sí, en las unidades requeridas |
| D05 | 385 disposiciones globales `UNKNOWN` | Manifest y ledger conservan el estado; CP058 distingue esta unidad de membresías por superficie | `NORMATIVE_DECISION_REQUIRED` | `YES` | Sí, para outcome por fila, aunque la deliberación se pueda agrupar | No | Sí para cierre global | Sí | Sí |
| D06 | Cierre de variantes/selector y cobertura por superficie | Contrato del manifest exige particiones finitas; blockers del freeze mencionan falta de particiones | `NORMATIVE_DECISION_REQUIRED` | `YES` | Sí, decidir particiones y criterio de suficiencia con evidencia apropiada | No | Sí para cierre normativo de cobertura | Sí, si requiere cambiar contrato/representación | Sí |
| D07 | Trazabilidad callsite → workload → Python/native/dependency → syscall | Manifest marca la trazabilidad estática como freeze blocker; ledger conserva unidades requeridas UNKNOWN | `NORMATIVE_DECISION_REQUIRED` | `PARTIAL`: contrato de qué cuenta depende de baseline; la existencia de rutas/callsites requiere evidencia propia | Sí para aceptar criterio y rutas; además falta evidencia | No | No para crosswalk histórico; sí para certificar cobertura | Sí si se incorpora al canon | Sí |
| D08 | Enforcement del límite ABI x32/i386 | Ledger indica exclusión por scope, pero enforcement del launcher no calificado | `NORMATIVE_DECISION_REQUIRED` | `PARTIAL`: el scope depende del contrato; la verificación de enforcement es evidencia aparte | Sí para criterio de aceptación; requiere evidencia de control | No | No para correlación de registros; sí para cierre de compliance | Sí si el canon/readiness debe registrar evidencia | Sí |
| D09 | Predicate A-PRE-0 machine-validated | Ledger declara `predicate_result=false` y que no existe predicate separado validado por máquina | `DOCUMENTARY_REPAIR_REQUIRED` | `PARTIAL`: su implementación debe representar la especificación autorizada; la ausencia del validador consta ya | Sí para aprobar el mecanismo/criterios; no implica READY | No | No para reconciliar documentos históricos | Sí, si se crea/modifica la validación | Sí |
| D10 | Provenance parcial de 61 pares (S10=36, S11=22, S15=3) | CP011/012 y 049 prueban historia agregada; CP033 aporta contexto S11 pero no origen individual de esos 22; 055 identifica los pares | `NOT_A_BLOCKER` | `NO` para describir el límite; `PARTIAL` si se usa el origen como premisa normativa | No para crosswalk; sí habrá decisión separada D03 | No | No por sí sola; se vuelve requisito sólo si una decisión invoca ese origen | No por sí sola; sí si el cambio afirma provenance histórica específica | No por sí sola |
| D11 | Contador 63 sin unidad/scope | Ledger registra 63 sin fórmula/universo/fecha; CP056/057 no lo reconcilian | `NOT_A_BLOCKER` | `NO` si se excluye de criterios; `PARTIAL` si algún consumidor normativo lo requiere | No para crosswalk/cierre actual; sí aclararlo antes de usarlo como métrica de aceptación | No | No | No | No |
| D12 | 11 stale counters | CP049/056 reproducen las fórmulas, snapshots y deltas | `CLOSED_WITH_EXISTING_EVIDENCE` | `NO` | No | No | No | No corregir en esta tarea | No |
| D13 | 23 exclusiones checkpoint-only (19 S02, 4 S01) | CP016 y CP014 las documentan por syscall y relación | `NOT_A_BLOCKER` | `NO` para describir outcome fuente; `PARTIAL` si se pretende declarar inventario normativo completo | No para descripción; cualquier ampliación/reapertura sí requeriría decisión | No | No bloquea cierre descriptivo | No materializar en esta tarea | No |
| D14 | Flag de provenance `shutdown`/S07 | CP055 ya apunta a CP026; CP026 contiene relación y scope; CP046 lo reconcilia | `CLOSED_WITH_EXISTING_EVIDENCE` | `NO` | No | No | No | No cambiar manifest | No |
| D15 | Nueve transiciones históricas | CP032/034 y CP049/056 describen antes/después y el efecto de representación | `CLOSED_WITH_EXISTING_EVIDENCE` | `NO` para describir la historia; `PARTIAL` si se reclama que es canon actual | No para registrar historia | No | No | No retrotraer/editar | No |

### Lectura del conjunto

- **Cerrado descriptivamente con evidencia:** D12, D14, D15.
- **No bloquea ninguna operación descriptiva pendiente:** D10, D11, D13.
- **Reparación documental si se pretende una representación canónica completa:**
  D02, D09.
- **Requiere decisión normativa/criterio:** D03–D08.
- **Bloqueo puro de provenance/autoridad:** D01.
- No se suman las filas D02–D15 como decisiones independientes: D02 contiene
  outcomes históricos ya escritos; D03/D04 son relaciones; D05 son outcomes
  globales; D06–D09 son gates de cobertura/readiness.

## 4. Grupos de leads — 162 tags sin duplicar cinco outcomes ya excluidos

Las cinco coincidencias entre tags `LEAD` y exclusiones relacionales son:
253 `inotify_init`/S01, 255 `inotify_rm_watch`/S01, 294 `inotify_init1`/S01,
300 `fanotify_init`/S01 y 95 `umask`/S04. Se cuentan como tags históricos
(4+1), pero no como relaciones abiertas:

```text
162 tags - 5 pares con EXCLUSION documentada = 157 leads abiertos
```

No se descartan ni se promueven esos tags. Sólo se evita volver a contarlos
como decisiones pendientes. Los leads S02 ya clasificados como exclusiones
(19) no forman parte de los 162 tags activos.

| LEAD_GROUP_ID | Miembros | Causa común / evidencia actual | Dependencia baseline | Decisión humana | Cambio canónico |
|---|---|---|---|---|---|
| LG00 | Los cinco pares excluidos de arriba | Outcome relacional existente en CP014/020 | `NO` para describir; `PARTIAL` si se reabre | No para continuar; no reabrir por defecto | No |
| LG04 | S04: 179, 443, 463, 466, 469 | CP019/020 los identifica como leads; fuentes específicas nuevas/no cerradas para argumentos/efectos | `YES` | Sí; decisión por relación y semántica específica | Sólo después de la decisión |
| LG05 | S05: 27, 149, 150, 151, 152, 216, 237, 238, 239, 256, 279, 325, 330, 331, 440, 450, 462 | CP021 lista los 17; falta decidir backing, alcance y efecto para cada interfaz | `YES` | Sí; agrupación logística por superficie, no outcome colectivo supuesto | Sólo después de la decisión |
| LG06 | S06: 12, 27, 149, 150, 151, 152, 216, 237, 238, 239, 256, 279, 325, 330, 331, 440, 450, 453, 462 | CP023 lista 19; se distinguen memoria anónima/memfd, residencia, NUMA y otras operaciones | `YES` | Sí; mantener particiones por recurso/operación | Sólo después de la decisión |
| LG10 | S10: 24, 34, 35, 36, 37, 38, 96, 100, 186, 201, 203, 204, 218, 219, 222, 223, 224, 225, 226, 227, 228, 229, 230, 273, 274, 282, 283, 286, 287, 289, 324, 334, 454, 455, 456, 471 | CP011/012 agregan 38 históricas; CP049 registra 36 actuales. No hay provenance primaria por par según CP057 | `YES` para outcome; provenance individual no se debe inferir | Sí por relación/operación; evidencia semántica adicional cuando la fuente no delimite | Sólo con outcome y fuente adecuados |
| LG11 | S11: 39, 98, 101, 109, 110, 111, 112, 121, 124, 140, 141, 142, 143, 144, 145, 146, 147, 148, 302, 309, 310, 311, 312, 314, 315, 448 | CP033 da provenance exacta para 101, 310, 311, 448; para los otros 22 sólo existe apoyo agregado de lote/snapshot (D10) | `YES` para outcome; `PARTIAL` si se usa la historia individual | Sí por relación/operación; no hay un outcome S11 colectivo ya decidido | Sólo con outcome y fuente adecuados |
| LG15 | S15: 185, 335, 336 | CP011/012 y 049 permiten ubicar el grupo, no el origen primario de cada ref | `YES` para outcome; provenance individual `PARTIAL` | Sí, considerando si cada API opaca pertenece; no inferir por nombre | Sólo con outcome y fuente adecuados |
| LG16 | S16: 63, 97, 99, 102, 103, 104, 107, 108, 115, 118, 120, 134, 135, 139, 141, 153, 154, 158, 159, 160, 163, 164, 167, 168, 169, 170, 171, 172, 173, 174, 177, 178, 205, 211, 212, 248, 249, 250, 251, 252, 305, 444, 445, 446, 457, 458, 459, 460, 461, 467, 470 | CP041 §5 identifica los 51 pares y mantiene su estado no promovido; evidencia específica/variant scope aún necesaria | `YES` | Sí por relación y efecto; no convertir el grupo S16 en una sola decisión | Sólo con outcome y fuente adecuados |

Las listas en esta tabla son NR del manifest target-bound; la asociación
`nr:name` y el inventario expandido están en CP058 §5.1. S05/S06 o S11/S16
pueden repetir un NR con superficies diferentes: son relaciones distintas,
no duplicados. Las 61 provenance partial (LG10=36, LG11=22, LG15=3) son
subconjuntos de estas mismas 157 relaciones y no se vuelven a sumar como
leads adicionales.

### 4.1 Qué no se puede afirmar de los 61 provenance partial

| Grupo | Extremo demostrado | Extremo no demostrado | Afirmación que no se puede hacer | Efecto del gap |
|---|---|---|---|---|
| S10 (36) | Aggregate histórico S10=38 y pertenencia actual de 36 refs según snapshot/CP049 | Documento primario que originó cada uno de los 36 pares | No afirmar qué fuente individual introdujo/justificó cada ref | Trazabilidad histórica solamente, salvo que una decisión use esa historia como premisa |
| S11 (22) | Conteos agregados y contexto general de lote; CP033 sí cita otros cuatro leads S11 recuperables | Origen individual para estos 22 pares | No atribuirlos a CP033 ni a una adjudicación que no los enumera | Trazabilidad histórica solamente bajo el registro actual |
| S15 (3) | Aggregate histórico S15=3 y lista actual NR 185/335/336 | Documento primario que explique el origen de cada ref | No declarar provenance individual recuperada por similitud de API | Trazabilidad histórica solamente bajo el registro actual |

Los 61 gaps **no** impiden describir el estado serializado, determinar que la
provenance está parcial, ni decidir una relación basándose en evidencia
semántica nueva e independiente. Sí impiden afirmar un linaje individual o
usar ese linaje como premisa de una modificación canónica. No son por sí
solos un bloqueo directo de A-PRE-0; una unidad requerida por el criterio
normativo aún necesita evidencia suficiente y trazabilidad apropiada. No se
rellena provenance por analogía.

## 5. Los 10 UNKNOWN relacionales

La revisión de fuente confirma que cada uno conserva un UNKNOWN explícito;
no se halló un outcome posterior que lo cierre. Las referencias semánticas
de estos documentos describen por qué quedó abierto, no son una decisión
implícita.

| syscall / NR / superficie | Decisión documental previa suficiente | Evidencia y estado actual | Clasificación | Autoridad / siguiente paso |
|---|---|---|---|---|
| `ustat` / 136 / S01 | No | CP014 mantiene UNKNOWN: consulta por device, alcance S01 no delimitado | `NORMATIVE_DECISION_REQUIRED` | Decidir si S01 incluye consultas filesystem-wide; autoridad baseline requerida |
| `inotify_add_watch` / 254 / S01 | No | CP014 mantiene UNKNOWN: path selecciona objeto, pero efecto de vigilancia y frontera S01/S10 no resueltos | `NORMATIVE_DECISION_REQUIRED` | Definir frontera de superficie con norma autorizada |
| `fanotify_mark` / 301 / S01 | No | CP014 mantiene UNKNOWN: marca objeto/filesystem/mount; monitoreo/intercepción excede el scope no decidido | `NORMATIVE_DECISION_REQUIRED` | Delimitar por operación/efecto; autoridad baseline requerida |
| `open_by_handle_at` / 304 / S01 | No | CP014 y CP047 preservan UNKNOWN; `name_to_handle_at` YES no se extiende por analogía | `NORMATIVE_DECISION_REQUIRED` | Decisión S01 separada; evidencia sobre selección por handle y alcance |
| `getxattrat` / 464 / S01 | No | CP014 mantiene UNKNOWN: faltaba fuente específica para ABI/resolución/flags | `NORMATIVE_DECISION_REQUIRED` | Además de decisión, hace falta evidencia de interfaz target-bound |
| `listxattrat` / 465 / S01 | No | CP014 mantiene UNKNOWN por la misma insuficiencia de semántica/ABI | `NORMATIVE_DECISION_REQUIRED` | Además de decisión, evidencia de interfaz target-bound |
| `file_getattr` / 468 / S01 | No | CP014 mantiene UNKNOWN; nombre no determina objeto/campos/selector | `NORMATIVE_DECISION_REQUIRED` | Evidencia específica y decisión de alcance |
| `madvise` / 28 / S05 | No | CP022 conserva UNKNOWN pendiente de partición por `MADV_*` | `NORMATIVE_DECISION_REQUIRED` | Particionar advice/backing y decidir; autoridad baseline requerida |
| `msync` / 26 / S06 | No | CP024 conserva UNKNOWN; documentación de S05 no resuelve anonymous/memfd | `NORMATIVE_DECISION_REQUIRED` | Decidir si hay subcaso S06; no trasladar S05 por analogía |
| `ioctl` / 16 / S15 | No | CP040 conserva UNKNOWN a nivel de familia; FIONREAD no resuelve otros comandos/FDs | `NORMATIVE_DECISION_REQUIRED` | Si se revisa, decisión por comando/objeto, no syscall-wide por inferencia |

Ninguno puede marcarse `CLOSED_WITH_EXISTING_EVIDENCE`: sí hay evidencia
suficiente para describir la razón del UNKNOWN, pero no para decidir el
outcome relacional. No son diez decisiones globales adicionales; las filas
siguen incluidas dentro de las 385 disposiciones globales `UNKNOWN`.

## 6. Matriz de las 77 relaciones checkpoint-only

`Representación canónica` describe el manifest actual. La acción indicada es
la única etiqueta operativa para cada grupo, no autorización para ejecutarla.

| Relaciones (miembros) | Evidencia checkpoint | Representación canónica actual | Autoridad requerida para cualquier cambio | Acción |
|---|---|---|---|---|
| **9 S06 YES condicionales:** 9 `mmap`; 10 `mprotect`; 11 `munmap`; 25 `mremap`; 72 `fcntl`; 77 `ftruncate`; 319 `memfd_create`; 329 `pkey_mprotect`; 447 `memfd_secret` | CP024; CP046 confirma checkpoint-only y scope por syscall | S06 no serializada como adjudicación; disposiciones globales siguen UNKNOWN | Baseline authority + autorización explícita para canónico; no para reproducir lo escrito | `DOCUMENTARY_REPAIR_REQUIRED` |
| **17 S07 YES condicionales:** 41 `socket`; 42 `connect`; 43 `accept`; 44 `sendto`; 45 `recvfrom`; 46 `sendmsg`; 47 `recvmsg`; 48 `shutdown`; 49 `bind`; 50 `listen`; 51 `getsockname`; 52 `getpeername`; 54 `setsockopt`; 55 `getsockopt`; 288 `accept4`; 299 `recvmmsg`; 307 `sendmmsg` | CP026; CP046 confirma alcance IP y checkpoint-only | S07 mantiene contextos candidatos sin decision serializada | Baseline authority + autorización si se reclama canon | `DOCUMENTARY_REPAIR_REQUIRED` |
| **18 S08 YES condicionales:** 41 `socket`; 42 `connect`; 43 `accept`; 44 `sendto`; 45 `recvfrom`; 46 `sendmsg`; 47 `recvmsg`; 48 `shutdown`; 49 `bind`; 50 `listen`; 51 `getsockname`; 52 `getpeername`; 53 `socketpair`; 54 `setsockopt`; 55 `getsockopt`; 288 `accept4`; 299 `recvmmsg`; 307 `sendmmsg` | CP028; CP046 incluye 54/55 aunque no tengan contexto S08 serializado | 16 contextos S08 candidatos; 54/55 sin contexto S08; ninguna decisión S08 materializada | Baseline authority + autorización si se reclama canon; inclusión de 54/55 exige reparación de representación además | `DOCUMENTARY_REPAIR_REQUIRED` |
| **19 S02 exclusiones:** 7 `poll`; 8 `lseek`; 23 `select`; 73 `flock`; 162 `sync`; 187 `readahead`; 213 `epoll_create`; 214 `epoll_ctl_old`; 215 `epoll_wait_old`; 221 `fadvise64`; 232 `epoll_wait`; 233 `epoll_ctl`; 270 `pselect6`; 271 `ppoll`; 281 `epoll_pwait`; 291 `epoll_create1`; 306 `syncfs`; 441 `epoll_pwait2`; 451 `cachestat` | CP016 registra NO relacional, no disposición global | No se exige reproducir estas exclusiones en cada fila para crosswalk descriptivo; algunas quedan como historial de lead | Sin cambio no se requiere; una declaración de canon completo requiere gate y autorización | `NOT_A_BLOCKER` |
| **4 S01 exclusiones:** 253 `inotify_init`; 255 `inotify_rm_watch`; 294 `inotify_init1`; 300 `fanotify_init` | CP014 registra exclusiones de relación S01 | Aparecen también como tags históricos de lead, sin outcome global | No para describir; no reabrir ni editar sin autorización | `NOT_A_BLOCKER` |
| **7 UNKNOWN S01:** 136 `ustat`; 254 `inotify_add_watch`; 301 `fanotify_mark`; 304 `open_by_handle_at`; 464 `getxattrat`; 465 `listxattrat`; 468 `file_getattr` | CP014 | Ninguna decisión materializada; UNKNOWN por relación en documentación | Autoridad normativa y, en interfaces nuevas, evidencia específica | `NORMATIVE_DECISION_REQUIRED` |
| **1 UNKNOWN S05:** 28 `madvise` | CP022 | Candidatura/lead permanece pendiente; no outcome S05 final | Autoridad normativa y partición `MADV_*` | `NORMATIVE_DECISION_REQUIRED` |
| **1 UNKNOWN S06:** 26 `msync` | CP024 | Relación S06 candidata, sin decisión | Autoridad normativa; partición por backing y flags | `NORMATIVE_DECISION_REQUIRED` |
| **1 UNKNOWN S15:** 16 `ioctl` | CP040 | Candidato de familia; sin relación materializada | Autoridad normativa; evidencia y decisión por comando/objeto | `NORMATIVE_DECISION_REQUIRED` |

Verificación de cardinalidad: `9 + 17 + 18 + 19 + 4 + 7 + 1 + 1 + 1 = 77`.
Las primeras tres filas (44 relaciones) documentan decisiones YES ya
expresadas históricamente; acción de reparación significa sólo que una
futura representación canónica, si se autoriza, necesitaría registrar esos
scopes. Las últimas tres filas UNKNOWN adicionales a S01 suman 10 UNKNOWN
totales y ya están en D04. No se materializa ninguna relación.

## 7. `BASELINE_DEPENDENCY_MATRIX`

`depends_on_baseline_authority` califica la afirmación concreta. `PARTIAL`
significa que la descripción del registro puede concluirse sin autoridad,
pero un juicio de completitud/readiness o un cambio normativo adicional sí
depende de ella.

| claim_id | claim | supported_by_current_evidence | depends_on_baseline_authority | reason | can_close_without_baseline | effect_if_unresolved |
|---|---|---|---|---|---|---|
| B01 | Existe un crosswalk descriptivo con 385 filas únicas | Sí, CP055/056 y validación estructural | `NO` | Describe el snapshot y su tabla target-bound, sin decidir membership | Sí | Ninguno sobre el cierre descriptivo |
| B02 | Los campos descriptivos de 055 coinciden semánticamente con manifest | Sí; CP056 registra cero diferencias semánticas en las 385 filas | `NO` | Proyección de campos y defaults ausentes declarados | Sí | No impide crosswalk |
| B03 | Once counters son stale y tienen fórmulas/deltas reproducibles | Sí, CP049/056/057 | `NO` | Derivación aritmética de arrays y snapshots; no interpretación normative | Sí | No impide reconciliación descriptiva; no se corrigen |
| B04 | Las 77 relaciones/outcomes están documentadas checkpoint-only o UNKNOWN | Sí, CP056/057, lotes fuente y CP046 | `NO` para describir exactamente qué dicen los checkpoints | Existencia de la afirmación documental no demuestra autoridad canónica | Sí | No se puede declarar canon completo |
| B05 | Los 157 leads, 96 recuperables y 61 parciales están identificados | Sí, CP055–058 y CP057 | `NO` para el inventario descriptivo | Provenance status puede reportarse sin elevarlo a decisión | Sí | No decide outcomes semánticos |
| B06 | Los 385 outcomes globales actuales son UNKNOWN | Sí, manifest y ledger; hash protegido | `NO` | Afirmación sobre valores serializados actuales | Sí | Persiste el bloqueo normativo/A-PRE-0 |
| B07 | Los cinco tags overlap ya tienen exclusión relacional escrita | Sí, CP014 y CP020; contadores de CP058 | `NO` para registrar que existe un NO relacional histórico | No equivale a una disposición global ni abre/cierra otras superficies | Sí | No contarlos como leads abiertos |
| B08 | CP026 respalda el YES condicional S07 de `shutdown` y explica el flag de 055 | Sí, CP026/046/055/057 | `NO` para el hecho documental | El estado manifest sigue sin decision materializada | Sí | No cambia canon |
| B09 | El contador ledger 63 tiene un scope determinado | No | `NO` para concluir solamente `SCOPE_UNPROVEN`; `PARTIAL` si se quiere usar la métrica | El ledger no define unidad/fórmula/fecha | Sí como dato excluido; no como métrica probatoria | No utilizar como criterio de cierre |
| B10 | La autoridad normativa prevista para el overlay es el artefacto `f058…` | Sólo el ledger afirma path/hash y ausencia; bytes no recuperados | `YES` | No se puede conocer su contenido, vincular copias locales ni fijar precedencia sin el artefacto/provenance | No | Mantener `AUTHORITY_UNRESOLVED` |
| B11 | La interpretación normativa del inventario/superficies es correcta y completa | No | `YES` | Exige saber qué contrato gobierna y verificar reglas sobre alcance/cobertura | No | No cerrar normativamente 048 |
| B12 | Las memberships de superficie están completas | Sólo hay memberships registradas, leads, UNKNOWN y outcomes checkpoint-only | `YES` | La existencia de decisiones previas no demuestra cierre exhaustivo según contrato | No | Sin completitud no hay cierre normativo |
| B13 | Las variantes/selector y unidades de cobertura están cerradas | No; el manifest declara particiones incompletas | `YES` | La suficiencia y finitud se evalúan contra el contrato normativo | No | No freeze ni readiness |
| B14 | Se pueden convertir UNKNOWN globales/relacionales en outcomes normativos | No; hoy sólo se prueba que el valor actual es UNKNOWN | `YES` | El estado no define outcome; requiere regla, evidencia y decisión | No | Permanecen 385 globales y 10 relacionales UNKNOWN |
| B15 | Se puede congelar inventario | No; `frozen=false` y freeze blockers abiertos | `YES` | Freeze es juicio de suficiencia respecto del contrato, variantes y trazabilidad | No | `inventory.frozen=false` |
| B16 | Una edición canónica futura refleja correctamente el snapshot normativo aplicable | Parcial: existe evidencia documental para contenido histórico, no autoridad/provenance única | `PARTIAL` | Autoridad, decisión explícita y autorización de cambio son requisitos distintos | No, no como cambio canónico legítimo | No modificar manifest/ledger |
| B17 | A-PRE-0 puede evaluarse como READY | No; ledger `NOT_READY`, predicate false, spec declarada ausente del overlay y required units UNKNOWN | `YES` | Se requiere baseline autorizado/identificado y evidencias de cobertura, trazabilidad, enforcement y predicate | No | Seguir `NOT_READY` |
| B18 | A-PRE-1 está autorizado | No; ledger informa `a_pre_1_authorized=false` y gate vigente lo prohíbe | `PARTIAL` | Es estado de autorización separado; esta tarea no puede inferir ni conceder permiso | No | Continúa `NOT_AUTHORIZED / NOT_EXECUTED` |

### Resolución de la parte crítica

Puede cerrarse sin conocer `f058…`: existencia del crosswalk, correspondencia
descriptiva, fórmulas stale, lista de relaciones checkpoint-only, inventario
de gaps y estado serializado de UNKNOWN, hashes comprobados, `shutdown/S07`
como metadato inconsistente explicado. No puede cerrarse sin autoridad:
significado normativo, completitud de memberships, cierre de variantes,
transición de UNKNOWN, freeze y readiness. Los cambios canónicos tienen
dependencia **parcial**: el diff puede describirse/autorizarse como operación,
pero su contenido no puede justificarse como representación normativa
correcta mientras no haya autoridad y una aprobación de cambio separada.

No se infiere autoridad de ninguna copia local, path, antigüedad, tracking,
hash conocido o semejanza textual. Incluso si una persona designara una copia
como referencia **operativa futura**, eso no demostraría que la copia sea
históricamente idéntica al artefacto externo `f058…`.

## 8. `MINIMUM_HUMAN_DECISION_SET`

No se puede derivar un número único de deliberaciones humanas sin fijar una
política de agrupación. El mínimo de **gates**, no de respuestas syscall, es:

| Gate | Decisión mínima | Prerrequisito/resultado |
|---|---|---|
| H01 | Resolver autoridad/provenance del baseline antes de cualquier cierre normativo | Recuperar evidencia del artefacto esperado o registrar explícitamente una elección operativa prospectiva autorizada, sin declarar identidad histórica no probada |
| H02 | Decidir outcomes de las 157 relaciones de lead activas | Puede agruparse por superficie y causa; cada relación necesita outcome/evidencia propia. No contar los cinco pares excluidos |
| H03 | Decidir outcomes de los 10 UNKNOWN relacionales | No pueden cerrarse mediante la existencia de sus checkpoints |
| H04 | Emitir outcome global para las 385 filas si se persigue cierre A-PRE-0 | 385 unidades de resultado; no necesariamente 385 deliberaciones independientes, ni se infieren de memberships |
| H05 | Aprobar criterio de completitud/variantes, trazabilidad y evidencia de enforcement requerida | Requiere autoridad normativa; además necesita evidencia técnica/documental que no está en estos checkpoints |
| H06 | Autorizar cualquier reparación/materialización canónica | Aprobación de cambio separada; no se deriva de los 44 YES históricos |
| H07 | Aprobar predicate machine-validated/readiness review | Posterior a H01–H05 y a la evidencia exigida; no implica que pase |

Los 61 provenance partial no agregan un gate humano separado para cerrar el
crosswalk descriptivo. Su recuperación pasa a ser prerrequisito sólo para una
afirmación/cambio que dependa de su linaje histórico individual. El contador
63 y los 11 stale tampoco forman parte del mínimo.

## 9. Efectos por nivel y criterio de reanudación

| Nivel | Qué puede afirmarse/hacerse con lo actual | Mínimo para avanzar | No autorizado/limitación |
|---|---|---|---|
| 1 — Crosswalk descriptivo | Ya completo: 385/385; reportar campo, relación y provenance tal como constan | Ninguna decisión nueva | Mantener 61 parciales, 10 UNKNOWN y 385 UNKNOWN; no reparar fuentes |
| 2 — Cierre descriptivo de 048 | Evidencia suficiente para publicar/documentar correlación descriptiva y stale/checkpoint-only/gaps | Ninguna decisión normativa; registrar expresamente alcance descriptivo y dejar intacto el STOP normativo de CP053 | No declarar reconciliación normativa global resuelta |
| 2b — Cierre normativo/global de 048 | No está listo | H01, luego H02/H03 y resolver cuestiones de representación sólo si se exige canon completo | No inferir outcome ni resolver spec por preferencia |
| 3 — Cambio legítimo de manifest/ledger | Se puede diseñar un cambio controlado, no aplicarlo | H01 + H06; evidencia por cada campo/relación, y definir qué hacer con las 44 checkpoint-only | No corregir stale/63 automáticamente ni materializar por aparición en checkpoint |
| 4 — Evaluación A-PRE-0 | No evaluable como READY | H01; outcomes necesarios H02–H04; criterio/variantes/trazabilidad/enforcement H05; predicate H07; verificar el snapshot/overlay autorizado | Aunque se resuelvan los gates, READY exige evidencia y predicate pass; no se declara aquí |

## 10. Estado final

- `BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED`;
  `EXTERNAL_SPEC_ARTIFACT = UNRECOVERED`;
  `STOP_REASON = UNRESOLVED_PROVENANCE`.
- Crosswalk descriptivo 385/385 completo; disposiciones globales
  385/385 `UNKNOWN`; 157 leads abiertos; 10 UNKNOWN relacionales.
- 61 provenance partial descritos sin completar; 77 checkpoint-only sin
  materialización; contador 63 sigue `SCOPE_UNPROVEN`.
- A-PRE-0 `NOT_READY`; A-PRE-1 `NOT_AUTHORIZED / NOT_EXECUTED`;
  `inventory.frozen=false`.
- No se adjudicó, promovió, convirtió UNKNOWN, cerró variante, editó canon,
  evaluó readiness ni seleccionó una baseline spec.

## 11. Verificación

- 385 filas, nombres y números: todos únicos; 385 outcomes siguen UNKNOWN.
- Manifest, ledger, `requirements.lock` y ambas baseline specs conservan los
  hashes de §1.
- `git diff --check` verificado para cambios rastreados y el checkpoint nuevo.
- Sólo se modifican este documento y la entrada de índice; no se creó commit.
- Sin actividad dinámica ni acceso a producción, VM, DB, corpus o modelos.
