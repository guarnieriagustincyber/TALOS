# Checkpoint 063 — resolución documental de provenance

Fecha: 2026-10-01

## 1. Resultado ejecutivo

La resolución documental de este checkpoint reduce los gaps descriptivos de
provenance, pero **no resuelve la autoridad del baseline**:

```text
EXTERNAL_SPEC_ARTIFACT = UNRECOVERED
BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED
```

Resultados principales:

- Los 96 leads `PROVENANCE_RECOVERABLE` de CP057 tienen fuente checkpoint
  explícita por NR/superficie; queda demostrado qué documento los registra,
  no su membership normativa.
- Los 61 `PROVENANCE_PARTIAL` se conservan con provenance histórica parcial.
  Su estado no bloquea un packet que use evidencia semántica independiente;
  sí bloquea un claim de linaje individual si éste es fundamento del packet.
- Los 44 YES condicionales y 23 exclusiones checkpoint-only tienen fuente y
  scope históricos identificados. Su provenance pasa a estar documentada;
  permanecen fuera de la representación canónica completa y no se materializan.
- Los 10 UNKNOWN relacionales tienen fuentes que documentan su estado/razón;
  no existe outcome nuevo.
- El contador `human_adjudicated_candidate_relation_count=63` permanece
  `SCOPE_UNPROVEN`.
- El artefacto externo `f058…` no se pudo identificar entre los archivos
  disponibles: CP052 documenta que no se halló relación hash/blob entre ese
  artefacto y las dos copias locales. Por tanto, el bloqueo de authority para
  cualquier juicio normativo continúa.

Conclusión operativa: `RESOLVE_PROVENANCE` se ejecutó **hasta donde permite la
evidencia local ya referenciada**. Los gaps históricos parciales que quedan no
bloquean de forma general; el siguiente gate dominante es
`RESOLVE_BASELINE_AUTHORITY`, condicionado a evidencia de identidad/
precedencia y sin elección por inferencia.

No se tomó decisión normativa, no se presentó packet, no se modificó canon y
no se ejecutó actividad dinámica.

## 2. Fuentes y estado de partida

Fuentes usadas: CP059–062, CP058 para referencias/listas cerradas, CP057 para
los resultados auditados de los 157 gaps, CP052 para investigación ya hecha
del linaje de las dos specs, CP049 para snapshots/transiciones, CP014/016/019–
024/026/028/033/040/041/046 para las relaciones que CP059–062 citan
explícitamente, `checkpoints/index.md`, manifest, ledger, crosswalk y las dos
copias locales de baseline. No se hicieron búsquedas externas ni se repitió
la arqueología Git de CP052.

Identidad local de los documentos fuente citados; los hashes identifican los
bytes en este workspace y no confieren autoridad normativa:

| Fuente | SHA-256 |
|---|---|
| CP011 | `91e6a581209ce7559b743ce1e4f0a43885e2d5c195edbe3f380f25be41e89b45` |
| CP012 | `9389b61e315301979c319dae3060f8ef483cf265a4ccc97a8edbc90ab1513789` |
| CP014 | `70e1cfc2c7a74b51ecaeaac4f45fa92fee8d4093a26132ee0c07b7f502256c7d` |
| CP016 | `081db47e946026af541a90154c2fe1458069cbe08e1c76dc4766faa7ce33345c` |
| CP019 | `1931a847f03ce5b72f64a4db5e5dda3d493ce3151a2e1bb8d12b2acfd529c9c2` |
| CP020 | `a16688f57f28578d3a51bd2e36296d7790d6fc1a0a58b2fd6a1e436d6e7e4fd4` |
| CP021 | `bb59be5db2384e4375955bcd96ee94f5f02c42693f58e4a9585f46c5ac84a3e3` |
| CP022 | `7ba9938b77fead0f829936190b7a0557cb8fdf711f30b496b7d54720a2946c32` |
| CP023 | `5874fdb8134e238dec58680f4f8424f7b6cc6fb3ff25a146bcdaa19817a6a6ab` |
| CP024 | `d6bf479432d0e522c632a9f352035e9f3653a85698c6f1ad7de081b93e5c7ce0` |
| CP026 | `0868160d6425b065242a85f989c5e6a171c7dc98b1053857789aa2eb3f0ebdef` |
| CP028 | `82bebe3d80b5b76e659d4ca8d637ecd96d7819d6a23ddf4a69c9c0f9f6991561` |
| CP033 | `8b0d4a07e2b449f5700f527d3f47867d53e4e52a3217b23015528869bbd31842` |
| CP034 | `5f73754a9315eb36ef508c8d6a808818cf99885b4234cd4bc0bba2f771b174a9` |
| CP040 | `ce503ec10eac9589621bb4bf60300e70bc7b4e76e2251ea1cde5471f850fb09a` |
| CP041 | `866d7913798c336bee3fd13f46d97e969b8e8c1ed0aac30b1ba19a73f7736abb` |
| CP046 | `64f517ee00a11267697829f9d0c8741036103212d529f1a44facc09387077566` |
| CP049 | `00e0c3dd1f2a4e6840a3a9b76c87e67b7a2bad04e753e22fb53b508c5e02a96c` |
| CP052 | `e1b95546dd386b56884e4fa8e9d3900a872bc14800a79dd6b53b9b40785f7ac6` |
| CP059 | `1bc6f19f0a8616f4cd2236bd3d7f7d7f7673cf7d4c83158150f0e8bbf7c1b649` |
| CP060 | `e704216fe4357bd51317fb7bcb9ba784297b585d7623dd614aaf7e1036c30148` |
| CP061 | `ccea9b43a2693937d41665c8e2263578f10f220a40c04bce15b6397a74668088` |
| CP062 | `e318b0898ed8052b1d52ea3da884ec6b2dce9c914886447281298fbd98a2e701` |

Estado protegido:

| Elemento | Estado |
|---|---|
| Filas syscall / nombres / NR | 385 / 385 únicos / 385 únicos |
| Disposition global | 385/385 `UNKNOWN` |
| Leads | 162 tags = 157 abiertos + 5 pares cubiertos por exclusiones |
| UNKNOWN relacionales | 10 |
| Provenance partial | 61: S10=36, S11=22, S15=3 |
| Checkpoint-only | 77: 44 YES, 23 exclusiones, 10 UNKNOWN |
| Contador 63 | `SCOPE_UNPROVEN` |
| Inventory | `frozen=false` |
| A-PRE-0 / A-PRE-1 | `NOT_READY` / `NOT_AUTHORIZED / NOT_EXECUTED` |
| Baseline | `AUTHORITY_UNRESOLVED`; `f058…` `UNRECOVERED` |

## 3. `PROVENANCE_BLOCKER_INVENTORY`

Sólo se incluyen gaps que CP062 conecta a un futuro packet o a un juicio/
cambio normativo. Cada fila describe un claim bloqueado, no una decisión.

| PROV_ID | OBJECT | FAMILY | SCOPE | CURRENT_PROVENANCE | MISSING_PROVENANCE | CLAIM_BLOCKED | DECISION_BLOCKED | LEVEL_BLOCKED | SOURCE_CANDIDATES |
|---|---|---|---|---|---|---|---|---|---|
| `PROV-01` | Artefacto de spec externo esperado con SHA `f058426b…d19a0ad4` | Gate de autoridad; afecta FAM-REL, FAM-GLOBAL, FAM-CRITERIA y contenido de FAM-CHANGE | Path del ledger `/home/agustin/apre-runner/rev4-clean/docs/A_PRE_0_BASELINE_SPEC.md`, overlay v4 declarado por ledger | Ledger registra path, SHA y `present_in_qualified_overlay=false`; CP050–052 repiten la referencia | Bytes/objeto exacto; link verificable entre hash y blob/ruta; precedencia que haga del contenido autoridad normativa | “Una copia local concreta es el artefacto f058” y “este contenido es la autoridad que rige” | Todos los packets cuyo efecto dependa del criterio normativo; no bloquea descripciones históricas literales | L1–L3; L2 para contenido del cambio | Ledger `qualification_identity.current_normative_spec`; CP050–053; Git lineage investigado en CP052; archivos locales `docs/` y `files/` sólo como candidatos distintos |
| `PROV-02` | Linaje individual de las 36 refs S10 clasificadas partial | FAM-REL, sólo si el packet invoca el origen histórico | `(NR,name,S10)` para los 36 miembros de LG10 listados en CP058 §5.1/CP057 §3.2 | CP011/012 acreditan agregado histórico de 38; CP049 identifica 36 refs en snapshots actuales; CP058/059/061 preservan provenance partial | Fuente primaria/cita individual que explique la creación y claim de cada uno de los 36 | “La ref actual se originó o fue justificada por el documento X” | Sólo una decisión que use ese linaje como premisa; no bloquea outcome basado en evidencia independiente | Ninguno para L0; L1 sólo para el claim histórico invocado | CP011/012, snapshots en CP049, lista actual de CP057 §3.2 |
| `PROV-03` | Linaje individual de 22 refs S11 clasificadas partial | FAM-REL, sólo si el packet invoca el origen histórico | `(NR,name,S11)` de los 22 pares de CP057 §3.2; cuatro refs S11 directas (101/310/311/448) quedan fuera de este blocker | CP033 documenta cuatro leads; CP011/012 y CP049 dan soporte agregado/resto actual; CP057 identifica los 22 | Fuente primaria individual para cada uno de los 22; la evidencia de los cuatro no se extiende | “Cada uno de los 22 fue adjudicado/documentado individualmente por CP033/034” | Sólo el packet que dependa de tal atribución | Ninguno para L0; L1 sólo para el claim histórico invocado | CP011/012, CP033/034 para sus propios cuatro miembros, CP049, lista de CP057 §3.2 |
| `PROV-04` | Linaje individual de las 3 refs S15 clasificadas partial | FAM-REL, sólo si el packet invoca el origen histórico | `(185,security,S15)`, `(335,uretprobe,S15)`, `(336,uprobe,S15)` | CP011/012 acredita el agregado de tres; CP049/CP057 identifican lista actual | Documento fuente individual que explica origen de cada ref | “La evidencia de una API/S15 demuestra por qué se originó cada ref” | Sólo el packet que use origen como premisa; no una decisión con evidencia semántica independiente | Ninguno para L0; L1 sólo para el claim histórico invocado | CP011/012, CP049, lista de CP057 §3.2 |
| `PROV-05` | Provenance de source→scope para un change set futuro sobre checkpoint-only | FAM-CHANGE, condicional a que un diff futuro incluya esos pares | Sólo objetos enumerados en ese diff; no el conjunto completo implícitamente | CP014/016/024/026/028, CP046 y CP059/061 identifican decisiones históricas y sus scopes | Validación/hash/locator y correspondencia exacta por objeto antes de autorizar cualquier diff; no falta la existencia general de las fuentes | “El campo que se pretende cambiar reproduce exactamente la fuente y su scope” | Sólo FAM-CHANGE si el change set incluye tales objetos | L2 | Checkpoints fuente enumerados en §8 y CP059/061; crosswalk para estado actual |

PROV-02/03/04 no se cuentan como bloqueos universales: su status principal
para el linaje individual es partial, pero su impacto es condicional. PROV-05
es un requisito de validación/provenance para un diff futuro, no una decisión
pendiente ahora.

## 4. Tipos de provenance y regla de identidad

Se aplica la prioridad de identidad de CP063 §5: hash exacto, identidad
Git/blob, ruta+contexto+versión, evidencia parcial, no identificado. La
existencia de nombres/rutas parecidos no permite saltar a igualdad de
artefacto.

| Caso | A. Objeto | B. Evidencia | C. Temporal | D. Transformación | E. Autoridad |
|---|---|---|---|---|---|
| `docs/A_PRE_0_BASELINE_SPEC.md` | Identidad local exacta: SHA `b4581baf…c365c8c`; CP052 registra tamaño y ruta; en HEAD estaba untracked/ausente del tree | Es una copia local concreta; CP052 documenta referencias en docs/plan y CP048/049 observan el hash | CP052 documenta commits/snapshots del linaje `docs/`, última modificación de contenido `a3c8e2d…`; esto fecha el linaje local, no una promulgación | No se encontró rename/derivación demostrada respecto de `files/` o `f058…` | No demostrada |
| `files/A_PRE_0_BASELINE_SPEC.md` | Identidad local exacta: SHA `23e268c1…2750ccd0`; blob local/tracked identificado en CP052 | Checkpoints 012/051/052 y el propio archivo la mencionan; no es automáticamente la spec externa | CP052 ubica persistencia en `fae0225…`; tracking prueba presencia histórica del blob, no autoridad | No se encontró relación de transformación formal con la copia `docs/` o `f058…` | No demostrada |
| Artifact externo `f058…` | No identificado: sólo registro de hash/path en ledger | No hay bytes disponibles en workspace ni relación de blob/hash local demostrada por CP052 | Ledger/CP052 sitúan la referencia en el snapshot/overlay calificado del 2026-10-01; la existencia de la referencia no establece creación del contenido | No se puede reconstruir porque falta el objeto/fuente de transformación | `AUTHORITY_UNRESOLVED` |
| 96 leads recoverable | Pares NR/name/surface identificados por CP057 §3.1 | Checkpoints concretos enumeran explícitamente cada par (ver §7) | Fecha/orden de checkpoint sirve como fecha de registro; claims sólo sobre ese documento | Se prueba “checkpoint lista relación como lead”; no transformación a membership canónica | No |
| 61 leads partial | Par actual identificable en crosswalk y CP057 §3.2 | Soporte histórico agregado y lista actual CP049/CP057 | Snapshot/aggregate datan grupos, no origen individual | No hay transformación individual demostrada | No |
| 44 YES + 23 NO checkpoint-only | Relaciones y superficies identificadas por CP059/061; listas de miembros en §8 | CP fuente contiene outcome y condiciones/scope | Se puede atribuir a CP024/026/028/016/014 | Se demuestra que el checkpoint registró outcome; no que se materializara en manifest | No |

### 4.1 Baseline `f058…`: candidatos auditados

| CANDIDATE | HASH | PATH | GIT_OBJECT | RELATION | IDENTITY_CONFIDENCE | LIMITATIONS |
|---|---|---|---|---|---|---|
| Copia local `docs/` | `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` | `docs/A_PRE_0_BASELINE_SPEC.md` | Linaje Git de snapshots/agentes; el commit de contenido indicado por CP052 es `a3c8e2d…`, no ancestro de HEAD | Hash diferente de `f058…`; sin blob link/rename/declaración explícita de equivalencia | `NOT_IDENTIFIED_AS_F058` | Copia local exacta, pero no identidad del artefacto externo ni autoridad |
| Copia local `files/` | `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0` | `files/A_PRE_0_BASELINE_SPEC.md` | Blob tracked en la línea principal desde `fae0225…`, según CP052 | Hash diferente de `f058…`; sin link/rename/declaración explícita de equivalencia | `NOT_IDENTIFIED_AS_F058` | Tracking y continuidad prueban persistencia, no autoridad ni identidad externa |
| Artefacto externo | `f058426b2a7315a90b651eb77d27f2e1c64209105fe8fdc4c1213218d19a0ad4` | Path esperado del ledger bajo `rev4-clean/docs/` | No hay Git object local identificado en CP052 ni en las fuentes consultadas para CP063 | Referencia explícita de ledger; `present_in_qualified_overlay=false`; bytes no recuperados | `UNIDENTIFIED` | No comparar contenido ni inferir equivalencia semántica |

Resultado obligatorio:

```text
EXTERNAL_SPEC_ARTIFACT = UNRECOVERED
BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED
```

No se usa tracking, fecha, path, nombre, hash aislado o similitud textual
como sustituto de evidencia explícita de autoridad.

## 5. Revisión de los 61 `PROVENANCE_PARTIAL`

Cada grupo recibe exactamente una clasificación nueva respecto a su impacto
en la preparación, y preserva el estado histórico:

| PROV_ID | OLD_STATUS | NEW_STATUS | EVIDENCE | LIMITATION | IMPACT |
|---|---|---|---|---|---|
| `PROV-02 / S10 (36)` | `PROVENANCE_PARTIAL` | `PROVENANCE_NOT_BLOCKING` | CP011/012: agregado histórico 38; CP049: 36 refs actuales; CP057 lista exacta; CP061 define que el linaje sólo es prerrequisito si se invoca | Sigue sin fuente primaria por par; no se afirma qué checkpoint originó cada uno | No bloquea preparar una pregunta basada en evidencia semántica independiente. Si se usa la provenance individual como rationale, vuelve a `PROVENANCE_BLOCKED` hasta recuperar source |
| `PROV-03 / S11 (22)` | `PROVENANCE_PARTIAL` | `PROVENANCE_NOT_BLOCKING` | CP011/012 agregados, CP049 lista actual y CP057 distingue 22; CP033 acredita otros cuatro pares, no estos | Origen de los 22 no demostrado y no atribuible a CP033/034 | Igual: no bloquea evidencia independiente; bloquea claim de origen individual |
| `PROV-04 / S15 (3)` | `PROVENANCE_PARTIAL` | `PROVENANCE_NOT_BLOCKING` | CP011/012 agregado de tres, CP049/057 identifica NR 185/335/336 | No hay fuente individual que explique cada origen; similitud de API no sirve | No bloquea evidencia independiente; bloquea claim de origen |

`PROVENANCE_NOT_BLOCKING` describe el impacto general en decision packet, no
una recuperación artificial del linaje. Los 61 siguen **históricamente
partial**. Resultado por causa:

- **Objeto:** identificado en las refs actuales/crosswalk.
- **Qué afirma el registro:** se conoce; “es una ref/lead actual con
  provenance partial y apoyo agregado”.
- **Quién/qué produjo cada ref:** no demostrado.
- **Autoridad normativa:** no la aporta el aggregate, y la falta de origen
  individual no la decide.
- **Impacto real:** trazabilidad histórica. Sólo bloquea si se usa el origen
  como premisa de outcome o cambio.

No se promovió lead ni membership.

## 6. Leads y provenance por grupo

Los grupos y members son los de CP059–061; no se recontaron ni se agregaron
los cinco overlaps de exclusión.

| LEAD_GROUP_ID | PROVENANCE_BEFORE | PROVENANCE_AFTER | DECISION_STILL_BLOCKED | REASON |
|---|---|---|---|---|
| LG04 / S04 (5) | `PROVENANCE_RECOVERABLE` | `PROVENANCE_RESOLVED` para claim “CP019/020 enumeran estos cinco leads” | YES | CP019/020 documentan los NR 179, 443, 463, 466, 469; la decisión sobre efecto/ABI/args sigue dependiendo de autoridad y evidencia de cada miembro |
| LG05 / S05 (17) | `PROVENANCE_RECOVERABLE` | `PROVENANCE_RESOLVED` para claim “CP021 enumera estas refs S05” | YES | Lista exacta en CP021/022; backing, flags/efecto y normatividad no quedan resueltos por la lista |
| LG06 / S06 (19) | `PROVENANCE_RECOVERABLE` | `PROVENANCE_RESOLVED` para claim “CP023 enumera estas refs S06” | YES | CP023/024 es fuente explícita; no hace membership ni outcome global |
| LG10 / S10 (36) | `PROVENANCE_PARTIAL` | `PROVENANCE_PARTIALLY_RESOLVED` | YES | Aggregate 38 + snapshot actual de 36 identifica el lote; origen individual faltante no se sustituye. `NORMATIVE_DECISION_REQUIRED` para cada scope decidido |
| LG11 / S11 (26) | 4 recoverable + 22 partial | 4 `PROVENANCE_RESOLVED`; 22 `PROVENANCE_PARTIALLY_RESOLVED` | YES | CP033 enumera 101/310/311/448; los restantes 22 sólo tienen apoyo agregado. `NORMATIVE_DECISION_REQUIRED`; no heredar source |
| LG15 / S15 (3) | `PROVENANCE_PARTIAL` | `PROVENANCE_PARTIALLY_RESOLVED` | YES | Aggregate de tres más lista actual, sin origen individual. `NORMATIVE_DECISION_REQUIRED` |
| LG16 / S16 (51) | `PROVENANCE_RECOVERABLE` | `PROVENANCE_RESOLVED` para claim “CP041 §5 lista estas 51 refs” | YES | CP041 §5 las enumera, declara que no se promueven; el outcome sigue sin decidir bajo autoridad y evidencia suficiente |

La resolución de provenance recuperable demuestra la existencia y scope de
lo documentado. En todos los siete grupos la decisión normativa sigue
bloqueada: para los 96 recuperables por autoridad/evidencia semántica; para
los 61 parciales se suma un blocker de provenance **sólo cuando el packet
quiera afirmar su origen histórico individual**.

## 7. Las 77 relaciones checkpoint-only

Estado de la transición descriptiva:

```text
CHECKPOINT_ONLY → PROVENANCE_DOCUMENTED
```

No se ejecuta:

```text
CHECKPOINT_ONLY → CANONICAL
```

En las tablas siguientes “provenance documented” significa que es
reproducible qué checkpoint contiene la afirmación y cuál es su scope
descrito. El estado canónico del manifest no cambia.

### 7.1 44 YES condicionales: fuente y scope por miembro

| CP / surface | Miembro NR/name | Evidencia de relación y scope que puede afirmarse | Estado tras CP063 |
|---|---|---|---|
| CP024 / S06 | 9 `mmap` | CP024 lista YES condicional S06 para el par; CP046 lo clasifica checkpoint-only | `PROVENANCE_DOCUMENTED` |
| CP024 / S06 | 10 `mprotect` | Igual: afirmación CP024 limitada al scope descrito allí | `PROVENANCE_DOCUMENTED` |
| CP024 / S06 | 11 `munmap` | Igual | `PROVENANCE_DOCUMENTED` |
| CP024 / S06 | 25 `mremap` | Igual | `PROVENANCE_DOCUMENTED` |
| CP024 / S06 | 72 `fcntl` | Igual; no se amplía a comandos no incluidos en el scope fuente | `PROVENANCE_DOCUMENTED` |
| CP024 / S06 | 77 `ftruncate` | Igual; no se extrapola a otros backing/operaciones | `PROVENANCE_DOCUMENTED` |
| CP024 / S06 | 319 `memfd_create` | Igual; no declara disposición global | `PROVENANCE_DOCUMENTED` |
| CP024 / S06 | 329 `pkey_mprotect` | Igual; scope acotado al caso/documento fuente | `PROVENANCE_DOCUMENTED` |
| CP024 / S06 | 447 `memfd_secret` | Igual | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 41 `socket` | CP026 lista YES condicional IP; no se transfiere a AF_UNIX/S08 | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 42 `connect` | Igual; sólo scope IP descrito | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 43 `accept` | Igual | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 44 `sendto` | Igual | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 45 `recvfrom` | Igual | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 46 `sendmsg` | Igual; ancillary/variantes fuera de lo explicitado no se añaden | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 47 `recvmsg` | Igual | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 48 `shutdown` | CP026/057 prueba YES condicional IP S07; AF_UNIX se trata por separado en S08 | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 49 `bind` | Scope IP descrito | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 50 `listen` | Scope IP descrito | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 51 `getsockname` | Scope IP descrito | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 52 `getpeername` | Scope IP descrito | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 54 `setsockopt` | Scope IP descrito; no completar variantes ausentes | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 55 `getsockopt` | Scope IP descrito; no completar variantes ausentes | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 288 `accept4` | Scope IP descrito | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 299 `recvmmsg` | Scope IP descrito | `PROVENANCE_DOCUMENTED` |
| CP026 / S07 | 307 `sendmmsg` | Scope IP descrito | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 41 `socket` | CP028 lista YES condicional AF_UNIX; no se transfiere a S07/IP | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 42 `connect` | Scope AF_UNIX descrito | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 43 `accept` | Scope AF_UNIX descrito | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 44 `sendto` | Scope AF_UNIX descrito | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 45 `recvfrom` | Scope AF_UNIX descrito | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 46 `sendmsg` | Scope AF_UNIX descrito; ancillary scope sólo si lo expresa CP028 | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 47 `recvmsg` | Scope AF_UNIX descrito | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 48 `shutdown` | CP028/057 separa AF_UNIX S08 de IP S07 | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 49 `bind` | Scope AF_UNIX descrito | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 50 `listen` | Scope AF_UNIX descrito | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 51 `getsockname` | Scope AF_UNIX descrito | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 52 `getpeername` | Scope AF_UNIX descrito | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 53 `socketpair` | Scope AF_UNIX descrito | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 54 `setsockopt` | CP028 y CP046 registran afirmación S08; CP046 nota que falta contexto S08 actual | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 55 `getsockopt` | CP028 y CP046 registran afirmación S08; CP046 nota que falta contexto S08 actual | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 288 `accept4` | Scope AF_UNIX descrito | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 299 `recvmmsg` | Scope AF_UNIX descrito | `PROVENANCE_DOCUMENTED` |
| CP028 / S08 | 307 `sendmmsg` | Scope AF_UNIX descrito | `PROVENANCE_DOCUMENTED` |

Los checkpoints fuente y CP046/059 identifican cada par y la diferencia
respecto del manifest. Para este checkpoint eso basta para la afirmación
histórica. La validación de hash/field mapping queda como prerequisite de un
diff futuro (`PROV-05`), no se simula como hecha. Cada entrada sigue
checkpoint-only en la representación del manifest y no cambia dispositions
globales.

### 7.2 23 exclusiones: fuente y alcance relacional

| CP / surface | Miembro NR/name | Afirmación demostrable | Estado tras CP063 |
|---|---|---|---|
| CP016 / S02 | 7 `poll` | CP016 registra exclusión relacional S02, no disposition global | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 8 `lseek` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 23 `select` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 73 `flock` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 162 `sync` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 187 `readahead` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 213 `epoll_create` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 214 `epoll_ctl_old` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 215 `epoll_wait_old` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 221 `fadvise64` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 232 `epoll_wait` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 233 `epoll_ctl` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 270 `pselect6` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 271 `ppoll` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 281 `epoll_pwait` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 291 `epoll_create1` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 306 `syncfs` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 441 `epoll_pwait2` | Igual | `PROVENANCE_DOCUMENTED` |
| CP016 / S02 | 451 `cachestat` | Igual | `PROVENANCE_DOCUMENTED` |
| CP014 / S01 | 253 `inotify_init` | CP014 registra exclusión relacional S01; no global disposition | `PROVENANCE_DOCUMENTED` |
| CP014 / S01 | 255 `inotify_rm_watch` | Igual | `PROVENANCE_DOCUMENTED` |
| CP014 / S01 | 294 `inotify_init1` | Igual | `PROVENANCE_DOCUMENTED` |
| CP014 / S01 | 300 `fanotify_init` | Igual | `PROVENANCE_DOCUMENTED` |

No requieren una decisión nueva por figurar checkpoint-only. Las cuatro S01
siguen siendo los overlaps excluidos del conteo de 157.

### 7.3 10 UNKNOWN: provenance de la afirmación UNKNOWN

| CP / surface | Miembro NR/name | Afirmación demostrable | Afirmación no demostrada |
|---|---|---|---|
| CP014 / S01 | 136 `ustat` | CP014 conserva relación UNKNOWN y razón de alcance | Outcome futuro o disposition global |
| CP014 / S01 | 254 `inotify_add_watch` | CP014 conserva UNKNOWN y frontera por resolver | Membresía normativa |
| CP014 / S01 | 301 `fanotify_mark` | CP014 conserva UNKNOWN y efectos/scope no resueltos | YES/NO por nombre/parecido |
| CP014 / S01 | 304 `open_by_handle_at` | CP014/047 conserva UNKNOWN; no se extiende `name_to_handle_at` | Outcome de la relación |
| CP014 / S01 | 464 `getxattrat` | CP014 conserva UNKNOWN y falta de evidencia específica | Resultado por inferencia |
| CP014 / S01 | 465 `listxattrat` | CP014 conserva UNKNOWN y límite análogo documentado | Resultado por analogía |
| CP014 / S01 | 468 `file_getattr` | CP014 conserva UNKNOWN por falta de delimitación | Resultado por nombre |
| CP022 / S05 | 28 `madvise` | CP022 conserva UNKNOWN pendiente de partición `MADV_*` | Transferencia a S06 o outcome global |
| CP024 / S06 | 26 `msync` | CP024 conserva UNKNOWN por backing/flags | Transferencia desde S05 |
| CP040 / S15 | 16 `ioctl` | CP040 conserva UNKNOWN a nivel de familia; FIONREAD es subcaso | Outcome syscall-wide desde subcaso |

Estos diez ahora tienen provenance suficiente para afirmar “el checkpoint
indicado documenta UNKNOWN”, no para producir packet normativo con una opción
YES/NO. Permanecen en FAM-REL y siguen bloqueados por authority/evidence.

## 8. Estado de provenance de los 157 leads

Las categorías nuevas expresan si el vínculo documental está demostrado, no
si el lead es correcto:

- `PROVENANCE_RESOLVED`: checkpoint enumera por identidad el objeto/scope de
  lead indicado.
- `PROVENANCE_PARTIALLY_RESOLVED`: aggregate/snapshot permite identificar el
  grupo actual, pero no el origen individual.
- `PROVENANCE_UNRESOLVED`: no se halló evidencia suficiente siquiera para
  el claim documental acotado.
- `PROVENANCE_NOT_BLOCKING`: gap histórico individual no se necesita para el
  claim/packet actual; el linaje queda parcial si se invoca.

| Grupo | Miembros | Provenance antes → después | Decision still blocked | Reason |
|---|---:|---|---|---|
| LG04 / S04 | 5 | `PROVENANCE_RECOVERABLE` → `PROVENANCE_RESOLVED` | YES | CP019/020 enumera 179, 443, 463, 466, 469 por S04; adjudicación normativa y evidencia de efecto pendientes |
| LG05 / S05 | 17 | `PROVENANCE_RECOVERABLE` → `PROVENANCE_RESOLVED` | YES | CP021/022 enumera los 17; la existencia como lead no decide backing/efecto |
| LG06 / S06 | 19 | `PROVENANCE_RECOVERABLE` → `PROVENANCE_RESOLVED` | YES | CP023/024 enumera los 19; no extiende a S05/global |
| LG10 / S10 | 36 | `PROVENANCE_PARTIAL` → `PROVENANCE_PARTIALLY_RESOLVED`; `PROVENANCE_NOT_BLOCKING` para packet que no invoque el origen | YES | CP011/012 agregado + CP049 current refs; origen individual no probado. `NORMATIVE_DECISION_REQUIRED` para outcome |
| LG11 / S11 | 4 + 22 | 4 `PROVENANCE_RECOVERABLE` → `PROVENANCE_RESOLVED`; 22 `PROVENANCE_PARTIAL` → `PROVENANCE_PARTIALLY_RESOLVED`/`PROVENANCE_NOT_BLOCKING` condicional | YES | CP033 enumera exactamente 101/310/311/448; los otros 22 quedan aggregate-only; `NORMATIVE_DECISION_REQUIRED` |
| LG15 / S15 | 3 | `PROVENANCE_PARTIAL` → `PROVENANCE_PARTIALLY_RESOLVED`; `PROVENANCE_NOT_BLOCKING` salvo claim de origen | YES | Aggregate tres + snapshot exacto actual; no source individual; outcome sigue decisión normativa |
| LG16 / S16 | 51 | `PROVENANCE_RECOVERABLE` → `PROVENANCE_RESOLVED` | YES | CP041 §5 enumera NR/name de los 51 y dice que no se promueven; decision normativa/effect evidence permanece pendiente |

Conteos conservados: 96 vínculos exactos recuperables (5+17+19+4+51); 61
linajes individuales parciales (36+22+3). Ninguna categoría se convierte en
YES/NO/membership.

## 9. Contador 63

| Campo | Valor actual | Resultado provenance | Evidencia examinada | Claim permitido | Claim no demostrado |
|---|---:|---|---|---|---|
| `ledger.inventory.syscall_dispositions.human_adjudicated_candidate_relation_count` | 63 | `SCOPE_UNPROVEN` | Ledger contiene valor; CP057 §4 registra falta de fórmula/universo/fecha; CP058–062 lo excluyen de métricas de reconciliación | El ledger almacena literalmente el valor 63 | Qué unidad cuenta, qué snapshot/periodo, qué subset o si representa relaciones, decisiones históricas o serialization |

El valor no coincide de modo demostrado con los 239 contextos, 236 IDs ni 187
relaciones serializadas citadas por CP057. No hay referencia que permita
reconstituir fórmula o scope; el valor no se modifica y no bloquea L0 ni un
packet cuyo claim no lo use.

## 10. `PROVENANCE_IMPACT_MATRIX`

Valores de impacto limitados a `UNBLOCKED`, `BLOCKED`,
`PARTIALLY_BLOCKED`, `NOT_RELEVANT`.

| PROV_ID | PROVENANCE_STATUS | DESCRIPTIVE_CROSSWALK | DECISION_PACKET | L1_GLOBAL_CLOSURE | L2_CANONICAL_MODIFICATION | L3_A_PRE_0 |
|---|---|---|---|---|---|---|
| `PROV-01` externo `f058…` | `PROVENANCE_UNRESOLVED` | `UNBLOCKED` | `BLOCKED` para cualquier packet normativo; un packet exclusivamente histórico no requiere autoridad | `BLOCKED` | `BLOCKED` para justificar contenido normativo | `BLOCKED` |
| `PROV-02` S10 36 linajes | `PROVENANCE_PARTIALLY_RESOLVED` | `UNBLOCKED` | `PARTIALLY_BLOCKED`: bloqueado sólo si claim usa origen individual | `PARTIALLY_BLOCKED` por mismo límite; authority aparte bloquea outcomes normativos | `PARTIALLY_BLOCKED` si diff usa historia de origen | `NOT_RELEVANT` por sí solo; evidencia/authority global aún required |
| `PROV-03` S11 22 linajes | `PROVENANCE_PARTIALLY_RESOLVED` | `UNBLOCKED` | `PARTIALLY_BLOCKED` bajo claim de linaje | `PARTIALLY_BLOCKED` bajo claim de linaje; authority aparte | `PARTIALLY_BLOCKED` si diff depende de linaje | `NOT_RELEVANT` por sí solo |
| `PROV-04` S15 3 linajes | `PROVENANCE_PARTIALLY_RESOLVED` | `UNBLOCKED` | `PARTIALLY_BLOCKED` bajo claim de linaje | `PARTIALLY_BLOCKED` bajo claim de linaje; authority aparte | `PARTIALLY_BLOCKED` si diff depende de linaje | `NOT_RELEVANT` por sí solo |
| `PROV-05` mapping source→scope de future diff | `PROVENANCE_DOCUMENTED`; diff no existe | `UNBLOCKED` para crosswalk histórico | `NOT_RELEVANT` ahora; `BLOCKED` si packet autoriza diff sin validación | `NOT_RELEVANT` al cierre documental | `BLOCKED` si future diff no valida mapping | `NOT_RELEVANT` por sí solo |
| `LEAD-96` fuentes exactas por lead | `PROVENANCE_RESOLVED` para existencia del lead | `UNBLOCKED` | `BLOCKED` para outcome normativo por `PROV-01`/evidence; source identity no es autoridad | `BLOCKED` por authority/evidence, no provenance de lead | `BLOCKED` sin authority/change approval | `NOT_RELEVANT` por provenance sola |
| `PC-44` YES condicionales | `PROVENANCE_DOCUMENTED` | `UNBLOCKED` como historia | `UNBLOCKED` para reportar fuente; `BLOCKED` para packet que trate la relación como nueva decisión | `BLOCKED` para usarlos como canon sin authority | `BLOCKED` hasta authority + mapping/change approval | `PARTIALLY_BLOCKED`; no cambian global UNKNOWN |
| `PC-23` exclusiones | `PROVENANCE_DOCUMENTED` | `UNBLOCKED` | `NOT_RELEVANT`; no nueva decisión | `NOT_RELEVANT` para describirlas como relación | `PARTIALLY_BLOCKED` sólo si un diff futuro las incluye | `NOT_RELEVANT` por sí solas |
| `PC-10` UNKNOWN relacionales | `PROVENANCE_DOCUMENTED` para el estado UNKNOWN | `UNBLOCKED` | `BLOCKED` para outcome normativo por authority/evidence; source de “UNKNOWN” no es blocker | `BLOCKED` para cerrar outcome | `BLOCKED` para materializar outcome | `PARTIALLY_BLOCKED`, global UNKNOWN/otros gates permanecen |
| `COUNTER-63` | `SCOPE_UNPROVEN` | `NOT_RELEVANT` | `NOT_RELEVANT` salvo que una pregunta lo use | `NOT_RELEVANT` bajo inventario CP058–062 | `NOT_RELEVANT` salvo que change altere esa métrica | `NOT_RELEVANT` |

La resolución del provenance documental reduce sólo los claims históricos:
CP026/CP024/CP028, etc. pueden citarse con scope probado; no desbloquea
adjudicación normativa, porque `PROV-01` sigue abierto y falta evidencia de
efecto/variants.

## 11. Niveles y efecto real sobre la preparación

- **L0 descriptive crosswalk:** sin cambios; ya está `CLOSED`.
- **L1 global closure:** continúa bloqueado por `PROV-01`/authority y por la
  evidencia semántica y criterio aplicable que CP062 identifica. Los 96
  vínculos recuperados y los 61 parciales no emiten outcomes.
- **L2 canonical modification:** no hay change set exacto; `PROV-05` será
  validación necesaria si un futuro diff incluye relaciones documentadas.
  Sin authority/autorización FAM-CHANGE no se materializa nada.
- **L3 A-PRE-0:** permanece `NOT_READY`: dispositions UNKNOWN, criterio/
  variants, traceability, ABI enforcement, predicate e identidad del snapshot
  permanecen gates separados.

Provenance reduce la incertidumbre sobre “qué documento afirmó qué y para
qué scope”, pero no resuelve “qué debería pertenecer”, “qué disposition
corresponde” ni “qué demuestra readiness”.

## 12. `NEXT_MINIMAL_ACTION`

```text
NEXT_MINIMAL_ACTION = RESOLVE_BASELINE_AUTHORITY
```

Justificación: ya se agotó en los documentos citados la recuperación local
de provenance que puede cerrarse sin inferencias. Los 61 linajes parciales
son no bloqueantes si no se invocan; su recuperación no es prerequisito
general. El gap residual material para presentar un packet **normativo** es
establecer authority sobre evidencia documental explícita. El artefacto
`f058…` no está recuperado, y CP052 no demuestra igualdad con ninguna copia
local. No se ejecuta `RESOLVE_BASELINE_AUTHORITY` en este checkpoint; si no
aparece evidencia explícita, el estado sigue unresolved y no se elige un
sustituto.

Las faltas de evidencia semántica de los leads/global outcomes siguen
pendientes en paralelo, pero no son provenance y no justifican escoger una
baseline. Una vez que haya criterio/authority evaluable, cada packet aún
deberá satisfacer evidencia y validación de scope propias. No se recomienda
ni se presenta una opción.

## 13. Verificación

| Check | Resultado |
|---|---|
| 385 filas/nombres/NR únicos | Confirmado en manifest |
| 385 dispositions globales `UNKNOWN` | Confirmado; sin modificación |
| Leads | 162 tags = 157 abiertos + 5 overlaps; sin doble conteo |
| UNKNOWN relacionales | 10; sin outcome nuevo |
| Provenance partial | Los 61 evaluados por grupos S10=36, S11=22, S15=3; los 61 siguen con linaje histórico partial |
| 77 checkpoint-only | Los 44 YES, 23 NO y 10 UNKNOWN tienen fuente/scope registrados; siguen no canónicos/no materializados |
| Contador 63 | `SCOPE_UNPROVEN`; sin cambio |
| Baseline | `EXTERNAL_SPEC_ARTIFACT=UNRECOVERED`; `BASELINE_SPEC_AUTHORITY=AUTHORITY_UNRESOLVED` |
| Inventory/readiness | `frozen=false`; A-PRE-0 `NOT_READY`; A-PRE-1 `NOT_AUTHORIZED / NOT_EXECUTED` |
| Hashes | Manifest `801f529655f1f4f250a2a374d2afa63f858a9c0875e0e3dc620d112df5f9fd6e`; ledger `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42`; lock `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70`; spec `files/` `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0`; spec `docs/` `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` |
| Cambios canónicos | Ninguno |
| Actividad dinámica | Ninguna |
| `git diff --check` | Limpio |
