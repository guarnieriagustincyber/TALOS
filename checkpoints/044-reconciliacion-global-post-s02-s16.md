# Reconciliación global A-PRE-0 post-S02/S16 — detenida por regla de parada

Fecha: 2026-10-01

## 1. Estado y alcance alcanzado

Reanudación documental read-only con método `OBSERVE → MEASURE → CORRELATE →
CLASSIFY`. No se modificaron artefactos funcionales, políticas, seccomp ni
disposiciones globales.

**DETENIDA** al encontrar candidaturas `UNREVIEWED_CANDIDATE` persistentes en
el manifiesto, primero en S01. La directiva exige detenerse ante cualquier
candidatura UNREVIEWED, contradicción entre checkpoint/manifiesto o
membership no explicable. Se registran los hallazgos observados hasta ese
punto; no se completa la reconciliación de cruces, effect coverage, paths
alternativos o totalidad de leads. Ninguna cifra marcada *provisional* es un
crosswalk reconciliado ni autoriza inferencias.

S02 sí está cerrado para las 18 candidaturas nucleares en el estado actual:
15 YES, 3 NO, 0 UNKNOWN; las 19 exclusiones de checkpoint 016 permanecen. El
cierre S02 no resuelve los restantes UNREVIEWED ni las inconsistencias
documentales descritas abajo.

## 2. Snapshot e integridad

Snapshot capturado antes de crear este checkpoint:

| Elemento | Valor |
|---|---|
| HEAD | `f81134fc2293916210d53c8065f3a0049e52b0b4` |
| Working tree | Sucio, con modificaciones y archivos no rastreados preexistentes; preservados. |
| Manifiesto | `9e0f2f0f07240a0902598f989380c2febd7f2a1ee5f9314d8de156b08cc69a3e` |
| Ledger | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Índice de checkpoints | `658a799cf530754b74a013c9de5b06293b0015d5257f0837373c401f9cdab0f0` |
| Checkpoint 042 | `aa1b9b9895a6ad6f6af32f81aaa47148148960b0df51e065b3e34e62b96246b8` |
| Checkpoint 043 | `be0c2ad34825b823cdb1a8d4d89bb54eef08c33b6ac382bd51e7043dc642bbce` |

El snapshot de checkpoint 042 tenía manifiesto SHA-256
`866b2dd8cbf88db6918f3091851f2ba7ef3f240ce6e29726650b9065c79a9219`,
ledger `0961b8a2…2144a42`, lock `813454bf…e2f4a70` e índice
`b4d9f305…f251928e`. El cambio de manifiesto registrado desde aquel snapshot
corresponde al cierre S02 documentado en checkpoint 043; ledger y lock siguen
byte-identical. El índice contiene ahora las entradas de 043 y 044. No hay un
snapshot de status inmediatamente posterior a 042 que permita demostrar por
comparación byte/path que *todos* los demás paths cambiaron exclusivamente
por S02/043; el árbol observado conserva modificaciones preexistentes ajenas,
no revertidas.

Digests semánticos disponibles:

- S01–S15 pre-S16: `cd9e375f70062982f5500dd2acc3ad64e00a880f649b00dd75b9df6e177b2378`,
  registrado en checkpoint 041 y también reproducido en 042 para su scope.
- S16 en snapshot 042: `c7d5896cc119ab60651019bb57410ea2c868dd56801a33412b86a6640af60522`.
- No se encontró un digest semántico independiente registrado para cada
  superficie S01–S16. El digest de S01–S15 no acredita las decisiones
  checkpoint-only S06–S08.

## 3. Conteos estructurales medidos — provisionales

El manifiesto parsea como JSON y contiene 385 filas con 385 nombres y 385
números únicos. Todas las 385 disposiciones globales son `UNKNOWN`; hay cero
disposiciones finales; `inventory.frozen=false`. El ledger contiene
A-PRE-0 `NOT_READY`, predicate `false`; A-PRE-1 continúa
`NOT AUTHORIZED / NOT EXECUTED`.

Conteo de decisiones YES explícitas que aparecen en relaciones por fila del
manifiesto (incluye YES condicionales; **no** cuenta decisiones registradas
sólo en checkpoints, ni S14 que es API de biblioteca):

| Superficie | YES por fila en manifiesto | Candidaturas aún UNREVIEWED | Nota |
|---|---:|---:|---|
| S01 | 13 | 15 | Parada encontrada aquí; array incluye candidatos no adjudicados. |
| S02 | 15 | 0 | 3 NO explícitos; 18 candidaturas nucleares cerradas. |
| S03 | 9 | 0 | Incluye relaciones condicionales. |
| S04 | 35 | 0 | No implica que todos los leads S04 estén cerrados. |
| S05 | 6 | 1 | `madvise` sigue UNREVIEWED. |
| S06 | 0 | 10 | El checkpoint 024 registra YES/UNKNOWN que no están materializados aquí. |
| S07 | 0 | 17 | El checkpoint 026 registra decisiones que declara no materializar. |
| S08 | 0 | 16 | El checkpoint 028 registra decisiones que declara no materializar. |
| S09 | 5 | 0 |  |
| S10 | 31 | 0 | Además, seis decisiones NO. |
| S11 | 17 | 0 |  |
| S12 | 3 | 0 |  |
| S13 | 6 | 0 |  |
| S14 | 0 syscalls | 0 | Nueve memberships YES de interfaz de biblioteca. |
| S15 | 3 | 1 | `ioctl` sigue UNREVIEWED/UNKNOWN como familia. |
| S16 | 33 | 0 | 51 leads no promovidos, enumerados en checkpoint 041. |
| **Total** | **176 syscall-relaciones** | **60** | **Provisional; no reconciliado.** |

La cifra de 176 suma filas S01–S13 y S15–S16, con las condiciones anteriores;
S14 tiene nueve interfaces separadas. Hay **60 candidaturas UNREVIEWED** en
seis superficies: S01 15, S05 1, S06 10, S07 17, S08 16, S15 1.

Si se cuenta solamente el conjunto parcial de YES machine-readable por fila,
se observan provisionalmente 220 syscalls con 0, 154 con 1 y 11 con más de
una relación YES. No son conteos definitivos: S06–S08 carecen de las decisiones
checkpoint-only en ese crosswalk y S01 todavía conserva 15 candidaturas
UNREVIEWED. No se informan como respuesta reconciliada los nombres de “sin
membership” o de “múltiples memberships”, ni un total final de memberships.

## 4. Primera condición de parada y discrepancias observadas

### 4.1 UNREVIEWED en S01 — primera condición de parada

Al recorrer las candidaturas por orden de superficie, la primera pendiente
encontrada fue S01. Sus 15 filas actuales `UNREVIEWED_CANDIDATE` son:

`open` (2), `stat` (4), `fstat` (5), `lstat` (6), `access` (21), `creat` (85),
`readlink` (89), `getdents64` (217), `openat` (257), `newfstatat` (262),
`readlinkat` (267), `faccessat` (269), `statx` (332), `openat2` (437) y
`faccessat2` (439).

El checkpoint 014 acepta 13 relaciones S01, mantiene siete UNKNOWN y excluye
cuatro de sus 24 referencias; el manifiesto todavía tiene 15 candidaturas
S01 unreviewed. La relación entre las 28 filas en el array S01, las decisiones
del checkpoint 014 y el estado por fila requiere reconciliación documental.
No se completó por la regla de parada.

### 4.2 Otras candidaturas UNREVIEWED observadas en la misma lectura

La medición de estado por fila encontró además:

- S05: `madvise` (28), una candidatura `UNREVIEWED_CANDIDATE`.
- S06: `mmap` (9), `mprotect` (10), `munmap` (11), `mremap` (25),
  `msync` (26), `fcntl` (72), `ftruncate` (77), `memfd_create` (319),
  `pkey_mprotect` (329), `memfd_secret` (447): diez pendientes.
- S07: las 17 candidaturas que el checkpoint 026 declara YES condicionales
  siguen `UNREVIEWED_CANDIDATE` en el manifiesto.
- S08: 16 candidaturas del array siguen `UNREVIEWED_CANDIDATE`; el checkpoint
  028 declara 18 YES para otro conjunto de 18 y dice expresamente que no
  materializa membresías. El array S08 contiene 16 tokens, excluye
  `setsockopt`/`getsockopt` 54/55 y mantiene `socketpair` 53; el checkpoint
  adjudica 18 YES incluidas 54/55.
- S15: `ioctl` (16) permanece UNREVIEWED/UNKNOWN a nivel de familia; el caso
  concreto FIONREAD no cierra esta candidatura general.

La observación de S07/S08 confirma contradicción entre decisión documental
registrada y relación machine-readable pendiente. No se materializó nada ni
se reinterpretó como hecho.

### 4.3 S02 y preservación de las exclusiones

S02 ya no tiene candidaturas nucleares UNREVIEWED. Checkpoint 043 registra 15
YES y 3 NO entre las 18 filas inspeccionadas. Las 19 exclusiones del
checkpoint 016 se preservan con digest semántico
`88f38627709f11d1a4f163449620b2ff27844cbc42f4d2c2b89910cf3bc1b608`.
`sync` continúa siendo syscall 162; `truncate` es 76.

## 5. Leads: medición de referencias, sin adjudicación

El campo `no_candidate_review` aparece en 191 filas; se encontraron 201
referencias potenciales de superficie debido a referencias solapadas.
Distribución observada por superficie:

| Superficie potencial | Referencias |
|---|---:|
| S01 | 24 |
| S02 | 19 |
| S04 | 6 |
| S05 | 17 |
| S06 | 19 |
| S10 | 36 |
| S11 | 26 |
| S15 | 3 |
| S16 | 51 |
| **Total** | **201** |

Los 51 leads S16 se conservan sin promover; la lista individual, su número,
estado y texto original están en [checkpoint 041](./041-adjudicacion-documental-lote-16-s16.md)
y en `no_candidate_review` del manifiesto. Los otros leads aparecen en las
filas `no_candidate_review` del manifiesto; no se reprodujo ni adjudicó aquí
esa lista porque la reconciliación se detuvo ante S01 UNREVIEWED. Su estado,
motivo, evidencia necesaria y relación con memberships existentes no fueron
reclasificados en este checkpoint.

## 6. UNKNOWN separados

- **Membership UNKNOWN / sin decidir:** además de las 60 candidaturas
  UNREVIEWED descritas arriba, S01 conserva las siete relaciones UNKNOWN
  expresas de su checkpoint; S05 mantiene `madvise` sin decisión; S15 mantiene
  `ioctl` UNKNOWN a nivel de familia. S06–S08 tienen decisiones checkpoint-only
  que no resuelven la discrepancia machine-readable.
- **Global disposition UNKNOWN:** 385/385. Esto es distinto de membership y
  no se convierte en OBSERVED/BLOCKED por un YES semántico.
- **Evidence UNKNOWN:** las filas indican falta de observación correlacionada
  o de denegación por fila cuando así se registra. No se elaboró una lista
  exhaustiva: la parada impidió el inventario de scope/hash de cada caso.
  El ledger indica effect coverage actual `UNKNOWN` e incompleta.

## 7. Cruces, effect coverage y alternate paths

**No reconciliados por la regla de parada.** No se afirma cierre de ninguna
frontera S01↔S04, S02↔S03/S05/S06, S03↔S09/S11, S04↔S05, S05↔S06,
S07↔S08, sockets↔S09, S09↔S10/S11, S10↔S11, AIO, S14 workers, S15 o S16.
Los límites y condiciones de los checkpoints fuente continúan aplicando; no
se absorbe payload, FD, pathname, mapping, namespace, worker, proceso ni
API multiplexada en otra superficie.

El manifiesto conserva 27 casos históricos (16 `OBSERVED`, 11 `BLOCKED`) en
17 filas; cero son elegibles para el predicate A-PRE-0 actual. No se hizo el
inventario por caso requerido (variante, efecto, perfil/hash, scope y
limitación), porque eso exigiría continuar tras la condición de parada. Se
preservan sin extrapolar los límites ya registrados en checkpoints 036–040:
io_uring/native AIO BLOCKED sólo bajo sus perfiles/hashes probados; FD
injection y `MAP_SHARED` con FD inyectado como sensor-sensitivity; AF_UNIX
inherited-FD sólo para el caso registrado; `ioctl(FIONREAD)` OBSERVED sólo
para el pipe sintético y comando concretos; sin evidencia BLOCKED global
para bpf/perf_event_open/userfaultfd.

No se clasificaron exhaustivamente pathname, dirfd, FD heredado/duplicado,
SCM_RIGHTS, pidfd, mappings, workers/libc, APIs multiplexadas, flags, ABI o
namespace routes en `COVERED`/`BLOCKED`/`UNKNOWN`/`NOT_APPLICABLE`. En ausencia
de cierre documentado para un caso concreto, la cobertura requerida sigue
UNKNOWN. No se ejecutaron pruebas para completar esas rutas.

## 8. Predicate A-PRE-0 y bloqueos observados

Sin cambiar el predicate formal versión 2, el ledger conserva `result=false`
y `readiness=NOT_READY`. El predicate requiere inventario congelado e
identidad target; scope ABI y launcher enforcement; conjunto exacto de
superficies; cada caso/ruta con estado y hash válidos; prueba de OBSERVED o
BLOCKED para su scope; alternate paths explícitos; snapshot/policy/platform
consistentes; sensores separados; higiene FD del launcher independientemente
calificada; cero UNKNOWN y contradicciones; collector/builder/verifier
fail-closed; y cero TALOS durante A-PRE-0.

Bloqueos registrados en el ledger:

- `INVENTORY_GAP`: `inventory.frozen=false`; 385 disposiciones globales UNKNOWN.
- `DOCUMENTATION_GAP`: 60 candidaturas UNREVIEWED y contradicciones de
  representación S01/S06/S07/S08.
- `EVIDENCE_GAP`: effect coverage UNKNOWN/incompleta; 27 casos históricos no
  elegibles para el predicate actual.
- `ALTERNATE_PATH_GAP`: callsite/dependency traceability y rutas alternativas
  incompletas.
- `LAUNCHER_GAP` / `POLICY_GAP`: enforcement de ABI compat no calificado,
  source signature no verificada y límites de política que permanecen sin
  certificación.
- `COLLECTOR_GAP` / `VERIFIER_GAP` / `INDEPENDENT_EVIDENCE_GAP`: falta de
  validador ejecutable independiente del ledger según las causas false
  registradas; se conserva además el bloqueo de syscall tracing/collector de
  la especificación.

**Mínimo conjunto que impide READY, sin resolverlo:** (1) cerrar y hacer
consistente el crosswalk documental de candidaturas/checkpoints (comenzando
por S01 UNREVIEWED y reconciliando S06–S08 sin asumir materialización);
(2) establecer evidencia independiente, válida y correlacionada para cada
unidad/ruta requerida y cerrar alternate paths; (3) satisfacer los checks de
identidad/inventario/ABI/launcher/policy e integridad del collector/verifier.
Además, bajo el predicate actual, el inventario debe cumplir el requisito de
congelación. No se ordenan acciones de ejecución ni se resuelven estos gaps.

## 9. Estado y verificaciones

Verificado en el snapshot:

- JSON parseable; 385 nombres/números únicos.
- 385/385 global `UNKNOWN`; cero disposiciones finales.
- `inventory.frozen=false`; A-PRE-0 `NOT_READY`; A-PRE-1 no autorizado/no
  ejecutado.
- S02 nuclear sin candidaturas UNREVIEWED; 15 YES / 3 NO.
- 19 exclusiones S02 originales preservadas.
- 51 leads S16 presentes.
- Ledger y `requirements.lock` idénticos a sus hashes de baseline.
- No se editaron seccomp, código funcional, E5/Qwen, corpus, modelos ni bases
  protegidas en esta tarea.
- `git diff --check` se ejecuta después de crear este checkpoint; `git status
  --short` registra también modificaciones preexistentes.

No se ejecutó TALOS, workload, probe, test, A-PRE-1 ni actividad dinámica.
La reconciliación se detuvo en las candidaturas UNREVIEWED; este checkpoint no
la declara cerrada.
