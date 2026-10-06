# Checkpoint 061 — protocolo de decisión humana y efectos acotados

Fecha: 2026-10-01

## 1. Propósito y estado vinculante

Este protocolo convierte las cuatro familias humanas identificadas en CP060
en un formato repetible para adjudicaciones futuras. Define preparación,
validación, pregunta, respuesta, efecto autorizado y verificación. No presenta
ninguna decisión al humano y no elige opciones.

Fuentes de trabajo: CP059, CP060, CP058 para listas y conteos consolidados,
manifest, ledger, las dos baseline specs locales, el crosswalk descriptivo
validado y el índice. No se repitió la arqueología previa.

Se preservan estos estados:

- `BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED`.
- `EXTERNAL_SPEC_ARTIFACT = UNRECOVERED`; el hash externo `f058…` no establece
  por sí mismo identidad ni autoridad.
- 385 filas syscall únicas; 385 disposiciones globales `UNKNOWN`.
- 162 tags `LEAD`, de los cuales 5 se solapan con exclusiones documentadas;
  157 relaciones abiertas.
- 10 UNKNOWN relacionales; 61 `PROVENANCE_PARTIAL`; 77 checkpoint-only.
- `inventory.frozen=false`.
- A-PRE-0 `NOT_READY`; A-PRE-1 `NOT_AUTHORIZED / NOT_EXECUTED`.

No se ejecutó TALOS, FastAPI, workload, probe, benchmark, VM, DB, corpus,
modelo ni código del proyecto. No se hicieron cambios canónicos.

## 2. Las cuatro familias de CP060

Los nombres son exactamente los de CP060 §1 y §12.1; no se fusionan ni
renombran. Los scopes son las unidades contenidas en cada familia, no una
autorización para tomar una decisión global de una vez.

| FAMILY_ID | NAME (CP060) | PURPOSE | SCOPE | EVIDENCE_REQUIRED | BASELINE_DEPENDENCY | AFFECTED_ARTIFACTS | UNLOCKED_LEVELS |
|---|---|---|---|---|---|---|---|
| `FAM-REL` | **outcomes relacionales** | Determinar, por cada par syscall-superficie, el outcome que la evidencia y el criterio autorizado permitan; preservar UNKNOWN cuando no alcance. | Un solo par `syscall NR/name × surface ID` y sólo las variantes/recursos/operaciones expresamente incluidos. Incluye los 157 leads abiertos y 10 UNKNOWN relacionales como sublotes diferenciados, sin presumir outcomes comunes. | Evidencia de efecto e interfaz específica, source/provenance, selector/variante exactos y, si aplica, límite de confianza/ABI. Para 61 pares parciales no atribuir linaje individual ausente. | `REQUIRED` para el outcome normativo. La descripción de un checkpoint existente no depende de baseline como autoridad. | Ningún cambio automático. Si se aprueba un change set, relaciones/campos correspondientes de manifest o ledger. | Contribuye a `L1_GLOBAL_CLOSURE`; por sí sola no cierra una fila global ni L3. |
| `FAM-GLOBAL` | **outcomes globales** | Determinar la disposition global por syscall bajo el contrato y evidencia aplicables, separada de membership de superficie. | Un registro syscall por NR/name de los 385; cada outcome debe poder apuntar a sus propias evidencias y variantes. Una decisión relacional no extiende este scope. | Evidencia de efecto/exclusión para la fila y sus variantes pertinentes; traceability requerida por criterio; authority/contract identificado. | `REQUIRED`. El estado serializado UNKNOWN se describe sin baseline. | Ningún cambio automático. Si se autoriza, disposition/status y refs limitados a filas enumeradas. | `L1_GLOBAL_CLOSURE`; es prerrequisito para L3, no suficiente. |
| `FAM-CRITERIA` | **criterio de cobertura/variantes** | Fijar cómo se interpretan scope, particiones finitas y suficiencia de cobertura bajo una autoridad establecida. | Ejes/particiones aplicables a las superficies: ABI, syscall/interface, argumento/flag, recurso/capability, fase y outcome. Pregunta por criterio explícito; no adjudica automáticamente los miembros. | Contrato autorizado; matriz de particiones con selector, valores incluidos/excluidos, clase de recurso, fase, paths alternos y closure criterion. | `REQUIRED`. La existencia de requisitos en una spec local es evidencia histórica, no autoridad automática. | Contrato de coverage/variant y referencias asociadas, sólo con change authorization cuando implique edición canónica. | Criterio para L1 y prerrequisito de cobertura L3. |
| `FAM-CHANGE` | **autorización de cambio** | Autorizar o rechazar un change set exacto y limitado tras completar sus fundamentos; autorización no crea autoridad normativa. | Diff enumerado: paths, objetos, campos y valores esperados; no “todo lo relacionado” ni cambios abiertos. | Outcomes aprobados, refs de evidencia, authority aplicable cuando el contenido es normativo, diff/hash de revisión y checks de scope. | `PARTIAL`: autorizar el acto de cambio es separado; justificar el contenido canónico requiere autoridad normativa. | Sólo paths/filas/campos listados en el change set aprobado. | `L2_CANONICAL_MODIFICATION`; no desbloquea L3 por sí sola. |

La recuperación de autoridad/provenance (`GATE-E01` en CP060) no es una quinta
familia de decisión humana. Es un prerrequisito probatorio. La identidad
histórica del artefacto externo no puede establecerse por votación ni por
designar una copia local.

## 3. Siete gates de CP059 referenciados y reconciliados

Los IDs originales se conservan para trazabilidad; no reaparecen como siete
decisiones independientes.

| CP059 | Tratamiento en CP060 | Aplicación en este protocolo |
|---|---|---|
| H01 — autoridad/provenance | Gate de evidencia, no decisión de autoridad histórica | `GATE-E01`: estado debe ser verificado antes de decisiones normativas. Sigue unresolved. |
| H02 — 157 leads | Se consolida con H03 como una familia relacional | `FAM-REL`, sublote `LEADS-157`, una unidad de scope por relación. |
| H03 — 10 UNKNOWN relacionales | Mismo tipo de pregunta que H02, sublote separado | `FAM-REL`, sublote `REL-UNKNOWN-10`; no se deriva outcome de la razón histórica. |
| H04 — 385 global UNKNOWN | Familia separada de outcomes globales | `FAM-GLOBAL`; 385 unidades no equivalen a 385 deliberaciones humanas. |
| H05 — coverage/variants + traceability + enforcement | Desagregado: criterio es decisión; tracing/enforcement son evidencia | Criterio dentro de `FAM-CRITERIA`; evidencia `GATE-E02` y `GATE-E03`; predicate `GATE-E04`. |
| H06 — canonical change | Familia independiente | `FAM-CHANGE`; sólo sobre un diff exacto y aprobado. |
| H07 — predicate/readiness | Validación posterior, no decisión de adjudicación | `GATE-E04` + `GATE-E05`, seguido por revisión L3. No se redefine predicate. |

Los H02/H03 redundantes no se abren de nuevo como decisiones separadas.
Los cinco tags S01/S04 que coinciden con exclusiones quedan fuera de los
157 scopes abiertos.

## 4. Contrato común de una decisión

Cada solicitud de decisión se registra con estos campos. Ninguno puede
quedar implícito; `N/A` exige una razón breve. El registro `HUMAN_RESPONSE`
no actualiza archivos por sí mismo.

| Campo | Requisito |
|---|---|
| `DECISION_ID` | ID estable, único; nunca reutilizado. |
| `FAMILY_ID` | Uno de los cuatro IDs de §2. |
| `QUESTION` | Una pregunta decidible, afirmativa/negativa/indeterminada o selección entre opciones cerradas. |
| `SCOPE` | Identificador legible y exacto de superficie/fila/variante/objeto/versiones aplicables. |
| `SUBJECTS` | Lista cerrada de objetos afectados; para una fila syscall: NR + name + ABI-bound table identity; para relation: NR + name + surface ID. |
| `EVIDENCE_SET` | Lista de `EVIDENCE_ID` y hash de cada fuente; evidencia no enumerada no fundamenta la respuesta. |
| `PROVENANCE_STATUS` | `VERIFIED`, `PARTIAL`, `UNRESOLVED` o `NOT_APPLICABLE`, con explicación. |
| `BASELINE_DEPENDENCY` | `NONE`, `PARTIAL` o `REQUIRED`; incluir la afirmación exacta que queda bloqueada. |
| `ALLOWED_OPTIONS` | Opciones finitas y mutuamente interpretables; incluir `DEFER/UNKNOWN` cuando corresponda. No inferir un default. |
| `HUMAN_RESPONSE` | Opción exacta, identidad/rol del decisor y timestamp; texto libre no sustituye la opción seleccionada. |
| `RATIONALE` | Justificación ligada a evidencia y criterio, separando hecho, inferencia y juicio normativo. |
| `EFFECT_SCOPE` | Lista explícita de campos/objetos que se autoriza cambiar después de aprobación separada. |
| `NON_EFFECT_SCOPE` | Invariantes y objetos expresamente no alterados, incluyendo otras superficies/variantes y disposition global. |
| `DOWNSTREAM_LEVEL` | Máximo nivel al que contribuye: L0, L1, L2 o L3; no implica que lo desbloquee por sí sola. |
| `REVERSIBILITY` | `REVERSIBLE` o `IRREVERSIBLE`, plan/versionado de reversión; no confundir reversión técnica con borrado de historia. |
| `AUDIT_REFERENCE` | CP/issue/registro de aprobación y ubicación del before/after evidence. |

### 4.1 Opciones cerradas por familia

Son opciones de protocolo, no opciones sometidas ahora al usuario:

- `FAM-REL`: `YES_WITH_EXPLICIT_SCOPE`, `NO_WITH_EXPLICIT_SCOPE`,
  `UNKNOWN_INSUFFICIENT_EVIDENCE`, `DEFER`.
- `FAM-GLOBAL`: únicamente los outcomes que el contrato autorizado admita,
  enumerados en el packet; siempre `UNKNOWN/DEFER` si evidencia/criterio no
  alcanza. No asumir que YES/NO relacional equivale a disposition global.
- `FAM-CRITERIA`: `ACCEPT_EXACT_CRITERION`, `REJECT`, `RETURN_FOR_EVIDENCE`,
  `DEFER`; la versión/hash del texto de criterio debe acompañar opciones.
- `FAM-CHANGE`: `AUTHORIZE_EXACT_DIFF`, `REJECT`, `RETURN_FOR_REVISION`,
  `DEFER`; hash y scope del diff obligatorios.

`UNKNOWN_INSUFFICIENT_EVIDENCE` no transforma un estado global o relacional
distinto del `SUBJECTS` indicado. `DEFER` conserva el estado previo y no
produce efectos.

## 5. Formato de evidencia y segregación de etapas

Cada fuente de evidencia tendrá este esquema mínimo:

| Campo | Contenido |
|---|---|
| `EVIDENCE_ID` | ID estable y único. |
| `SOURCE` | Ruta, URI o identificador de documento, con versión/locator. |
| `SOURCE_TYPE` | Checkpoint, spec, manifest, ledger, fuente primaria, traza, prueba de control u otro tipo declarado. |
| `HASH` | SHA-256 del artefacto exacto cuando sea archivo; para fuente no hasheable, método de identidad y motivo. |
| `SCOPE` | Syscall/surface/ABI/variante/objeto y rango que cubre exactamente. |
| `CLAIM_SUPPORTED` | Obligatorio: afirmación concreta que la fuente sí respalda. |
| `CLAIM_NOT_SUPPORTED` | Obligatorio: inferencias/outcomes/variantes que la fuente no demuestra. |
| `PROVENANCE` | Autoría/origen/linaje documentado; `PARTIAL` o `UNRESOLVED` si corresponde. |
| `LIMITATIONS` | Limitaciones de método, snapshot, aplicabilidad, coverage o autoridad. |

No se acepta un packet si `CLAIM_SUPPORTED` o `CLAIM_NOT_SUPPORTED` está
vacío. Una fuente puede probar que CP026 registró una adjudicación, pero no
automáticamente que esa adjudicación sea autoridad canónica ni que otra
variante comparta el outcome.

### 5.1 Pipeline obligatorio

```text
EVIDENCE PREREQUISITES
        ↓
VALIDATION
        ↓
HUMAN DECISION
        ↓
CANONICAL EFFECT (sólo tras autorización de cambio)
        ↓
VERIFICATION
```

| Etapa | Qué hace | No hace |
|---|---|---|
| Prerrequisito de evidencia | Reúne evidencia objetiva del objeto y del claim; identifica gaps. | No adjudica ni declara membership por la existencia de una cita. |
| Validación | Comprueba hashes, provenance declarada, correspondencia del source con el `SUBJECTS`, variantes, no duplicación y autoridad requerida. | No decide verdad semántica ni elige baseline. |
| Decisión humana | Responde una pregunta normativa exacta entre opciones enumeradas y deja rationale. | No modifica canon ni amplía scope. |
| Efecto canónico | Aplica únicamente un diff separado, aprobado por `FAM-CHANGE`, si tal efecto está autorizado. | No es implícito en `HUMAN_DECIDED`; no modifica otros objetos. |
| Verificación | Contrasta hashes, campos, cardinalidad, invariantes y scope before/after. | No transforma por sí misma una decisión en READY. |

## 6. Fronteras `IN_SCOPE` / `OUT_OF_SCOPE`

Todo packet debe incluir ambas listas. La lista positiva es enumerativa, no
ejemplar. Ningún objeto se añade por semejanza, nombre compartido o
pertenencia a una familia.

```text
IN_SCOPE:
- IDs exactos de filas/relaciones/particiones incluidos en SUBJECTS.
- ABI/table identity y variantes enumeradas por ID/hash.
- claims específicos que pregunta el packet.

OUT_OF_SCOPE:
- toda superficie distinta de la listada;
- toda syscall/relación distinta de SUBJECTS;
- variantes, flags, comandos, backing, objetos, fases o ABI no enumerados;
- evidencia histórica no incluida o de provenance incompatible;
- disposition global salvo que FAM-GLOBAL sea la familia;
- estado de readiness, freeze, A-PRE-1 y artefactos no nombrados.
```

### Reglas de no extrapolación

Una decisión no puede:

- cambiar otra superficie, otro syscall o una variante omitida;
- convertir UNKNOWN fuera de `SUBJECTS`;
- alterar una disposition histórica o reescribir su provenance;
- convertir evidencia positiva de un subcaso en coverage/global outcome;
- materializar un checkpoint-only sin autorización explícita y evidencia
  validada;
- declarar inventario frozen, A-PRE-0 READY o autorizar A-PRE-1.

Una decisión sí puede producir exactamente el efecto enumerado en
`EFFECT_SCOPE`, una vez autorizada por el gate correspondiente; los demás
campos/objetos permanecen byte-for-byte o semánticamente sin cambio según el
control solicitado.

## 7. Relación de los 385 UNKNOWN con decisiones acotadas

No se crean 385 deliberaciones por la existencia de 385 UNKNOWN. La relación
es muchos-a-muchos entre causa, familia, scope y posibles efectos; los
conteos de causas se solapan y no deben sumarse.

| UNKNOWN_GROUP | Qué cubre | DECISION_FAMILY | DECISION_SCOPE | Evidencia que falta | Potencial efecto (no decisión tomada) | UNKNOWN que permanece |
|---|---|---|---|---|---|---|
| `UG-REL-LEADS-157` | Las 157 relaciones abiertas en CP058 §5.1 | `FAM-REL` | Pares syscall-superficie enumerados por LG04/05/06/10/11/15/16; no un outcome común de grupo | Evidencia/variant por operación y authority gate | Sólo el par y variante expresamente seleccionados en cada packet podrían recibir outcome relacional | Las otras relaciones y las 385 globales, siempre |
| `UG-REL-UNKNOWN-10` | 7 S01, 1 S05 `madvise`, 1 S06 `msync`, 1 S15 `ioctl` | `FAM-REL` | Cada par exacto; ioctl por command/object cuando aplique | Selector, efecto, resource/backing/ABI y autoridad | Sólo la relación y variante incluidas; se admite DEFER/UNKNOWN | Otras relaciones del mismo syscall/superficie y todas las globales |
| `UG-GLOBAL-385` | 385 dispositions globales actuales UNKNOWN | `FAM-GLOBAL` | Una o más filas explícitas por packet; no crear packet individual obligatorio por fila | Efecto/exclusión, applicability, relaciones alternativas, trace/coverage según criterio | Sólo dispositions de filas enumeradas, si evidencia y norma permiten | Toda fila fuera del packet y cualquier variante no resuelta |
| `UG-VARIANT-COVERAGE` | Ejes de coverage finita del manifest contract PARTIAL; no hay cardinalidad de unidades cerradas | `FAM-CRITERIA` | Superficie y ejes/valores enumerados; versión de criterio fijada después de authority gate | Autoridad aplicable y particiones con valores/límites/cierre | Fija regla de partición; no adjudica membership ni effect | Outcomes relacionales/globales hasta decisión propia |
| `UG-TRACE-AND-ABI` | Callsite trace freeze blocker; x32/i386 enforcement NOT_QUALIFIED | No constituye familia de decision; usa gates de evidencia y puede informar FAM-GLOBAL | Ruta/snapshot de workload y control/ABI concretos | Traza admisible y evidencia de rechazo/qualification | Actualiza sólo evidencia/qualification record conforme al proceso futuro | Todos los UNKNOWN no tratados por decisiones de las familias |

No hay base para asignar una causa primaria única a cada fila global. Una
misma syscall puede tener UNKNOWN global, una relación YES documentada, otra
relación UNKNOWN y además variantes abiertas. Ninguno de esos hechos se
colapsa.

## 8. Paquetes de leads (157; cinco tags excluidos del set abierto)

Los grupos de CP060 son índices de preparación de evidencia; no implican un
outcome colectivo. Los miembros exactos siguen en CP058 §5.1.

| LEAD_GROUP_ID | MEMBERS | DECISION_FAMILY | REQUIRED_EVIDENCE | DECISION_SCOPE | POSSIBLE_EFFECT | NON_EFFECT |
|---|---|---|---|---|---|---|
| LG04 / S04 | 179, 443, 463, 466, 469 | `FAM-REL` | API/ABI/args y efecto de cuotas, xattr o file attributes por syscall | Cada par S04 individual y variantes expresas; no fusionar familias de efecto | Outcome sólo de par/variante aprobados | No disposition global ni otras superficies |
| LG05 / S05 | 27, 149, 150, 151, 152, 216, 237, 238, 239, 256, 279, 325, 330, 331, 440, 450, 462 | `FAM-REL` | Backing/resource, advice/flags, NUMA/residency/remap y efecto por operación | Par NR×S05 y selector/variante concreta | Outcome relacional de unidad enumerada | No S06 overlap ni global disposition |
| LG06 / S06 | 12, 27, 149, 150, 151, 152, 216, 237, 238, 239, 256, 279, 325, 330, 331, 440, 450, 453, 462 | `FAM-REL` | Backing anónimo/memfd/heap, NUMA/residency, shadow stack, seal y flags según miembro | Par NR×S06; separar variantes/recursos | Outcome relacional de unidad enumerada | No S05 por mismo NR ni outcome global |
| LG10 / S10 | 24, 34, 35, 36, 37, 38, 96, 100, 186, 201, 203, 204, 218, 219, 222, 223, 224, 225, 226, 227, 228, 229, 230, 273, 274, 282, 283, 286, 287, 289, 324, 334, 454, 455, 456, 471 | `FAM-REL` | Efecto/API y variantes por grupo timer, scheduler, signal/timer FD, futex y rseq; provenance individual sólo si la conclusión depende del origen | Cada par S10, no un YES/NO colectivo | Outcome sólo para miembros y variantes sustentados | No los 36 como conjunto por CP011/012; no global outcomes |
| LG11 / S11 | 39, 98, 101, 109, 110, 111, 112, 121, 124, 140, 141, 142, 143, 144, 145, 146, 147, 148, 302, 309, 310, 311, 312, 314, 315, 448 | `FAM-REL` | Evidencia por identidad/scheduler/ptrace/process_vm/kcmp/release; cuatro refs con fuente directa; provenance parcial en 22 | Cada par S11, sin generalizar desde los cuatro refs respaldados | Outcome por par y variante explícitos | Los 22 no heredan provenance de CP033/034; no S16/global |
| LG15 / S15 | 185, 335, 336 | `FAM-REL` | Evidencia por API/operación `security`, `uretprobe`, `uprobe`; origen histórico si se invoca | Cada par S15 | Outcome por operación cubierta | No transferir por similitud de API ni emitir syscall-wide outcome |
| LG16 / S16 | 63, 97, 99, 102, 103, 104, 107, 108, 115, 118, 120, 134, 135, 139, 141, 153, 154, 158, 159, 160, 163, 164, 167, 168, 169, 170, 171, 172, 173, 174, 177, 178, 205, 211, 212, 248, 249, 250, 251, 252, 305, 444, 445, 446, 457, 458, 459, 460, 461, 467, 470 | `FAM-REL` | API/command/permission/effect por identidad, kernel/module, namespace/LSM/control; variant scope | Cada par S16 y variantes incluidas | Outcome sólo para scope probado | No un outcome de 51 miembros; no global dispositions |

Los cinco tags no abiertos son NR 253/255/294/300 S01 y NR 95 `umask` S04.
Conservan su evidencia de exclusión anterior y no deben reaparecer como
decisiones abiertas. Los NR repetidos entre superficies siguen siendo
relaciones diferentes.

## 9. Provenance de los 61 pares parciales

Los roles describen para qué se necesita la provenance; no califican de nuevo
cada source individual ni infieren una adjudicación.

| Grupo | Cantidad | PROVENANCE_ROLE | ¿Acción necesaria antes de packet? | Límite |
|---|---:|---|---|---|
| S10 | 36 | `HISTORICAL_ONLY` | No, si packet se fundamenta en evidencia semántica independiente y no usa el linaje del lead | No afirmar fuente individual/autoría del lead |
| S11 | 22 | `HISTORICAL_ONLY` | No, bajo el mismo límite; evidencia de otros cuatro leads no se extiende a estos | No atribuirlos a CP033/034 |
| S15 | 3 | `HISTORICAL_ONLY` | No, salvo que la decisión invoque su motivo de origen | No inferir provenance por similitud API |

Los 61 requieren **TRACEABILITY** únicamente si un argumento o cambio depende
del origen histórico de un par. Ninguno es `BASELINE_AUTHORITY` o
`CANONICAL_AUTHORITY`; esos roles aplican a la procedencia de la autoridad
normativa, no a estos leads. Si una decisión propuesta usa esa historia como
prerrequisito, marcar el packet `PROVENANCE_STATUS=PARTIAL` y no elevarlo a
`READY_FOR_HUMAN` hasta obtener la fuente necesaria o retirar esa premisa.
Así se evita bloquear decisiones independientes sin degradar gaps que sí
afectarían el fundamento.

## 10. Las 77 checkpoint-only: estado operativo sin reabrir outcomes

Las clases se aplican a cada miembro de los grupos nombrados en CP059 §6;
“documentary only” no equivale a canon. Las cuatro opciones se asignan así:

| Relaciones | Estado por relación | Evidencia | Si existe decisión nueva | Efecto no permitido |
|---|---|---|---|---|
| 9 S06 YES: 9 `mmap`, 10 `mprotect`, 11 `munmap`, 25 `mremap`, 72 `fcntl`, 77 `ftruncate`, 319 `memfd_create`, 329 `pkey_mprotect`, 447 `memfd_secret` | `DOCUMENTARY_ONLY` | CP024/046 | No reabrir outcome histórico para describirlo; si L2 exige registro, incluir cada par en change set con scope/provenance | No materializar por checkpoint ni cerrar global UNKNOWN |
| 17 S07 YES: 41 `socket`, 42 `connect`, 43 `accept`, 44 `sendto`, 45 `recvfrom`, 46 `sendmsg`, 47 `recvmsg`, 48 `shutdown`, 49 `bind`, 50 `listen`, 51 `getsockname`, 52 `getpeername`, 54 `setsockopt`, 55 `getsockopt`, 288 `accept4`, 299 `recvmmsg`, 307 `sendmmsg` | `DOCUMENTARY_ONLY` | CP026/046 | Igual: preservar que la fuente histórica contiene YES condicional IP; cambio canónico requiere FAM-CHANGE | No derivar S08 ni global outcome |
| 18 S08 YES: 41 `socket`, 42 `connect`, 43 `accept`, 44 `sendto`, 45 `recvfrom`, 46 `sendmsg`, 47 `recvmsg`, 48 `shutdown`, 49 `bind`, 50 `listen`, 51 `getsockname`, 52 `getpeername`, 53 `socketpair`, 54 `setsockopt`, 55 `getsockopt`, 288 `accept4`, 299 `recvmmsg`, 307 `sendmmsg` | `DOCUMENTARY_ONLY` | CP028/046 | Preservar scope AF_UNIX; los contextos S08/54–55 ausentes se tratan como diferencia de representación al validar change set | No completar otras filas/contextos por inferencia |
| 19 S02 exclusiones: 7 `poll`, 8 `lseek`, 23 `select`, 73 `flock`, 162 `sync`, 187 `readahead`, 213 `epoll_create`, 214 `epoll_ctl_old`, 215 `epoll_wait_old`, 221 `fadvise64`, 232 `epoll_wait`, 233 `epoll_ctl`, 270 `pselect6`, 271 `ppoll`, 281 `epoll_pwait`, 291 `epoll_create1`, 306 `syncfs`, 441 `epoll_pwait2`, 451 `cachestat` | `NON_BLOCKING` | CP016; relación NO, no disposition global | No decisión nueva en protocolo; sólo documentar outcome histórico | No convertir NO relacional en global NO |
| 4 S01 exclusiones: 253 `inotify_init`, 255 `inotify_rm_watch`, 294 `inotify_init1`, 300 `fanotify_init` | `NON_BLOCKING` | CP014; excluidos también del set de 157 leads | No decisión nueva | No reabrir ni contar duplicado |
| 7 UNKNOWN S01: 136 `ustat`, 254 `inotify_add_watch`, 301 `fanotify_mark`, 304 `open_by_handle_at`, 464 `getxattrat`, 465 `listxattrat`, 468 `file_getattr` | `DECISION_REQUIRED` | CP014/047 registra UNKNOWN y sus límites | FAM-REL; requiere evidencia específica/authority antes de READY | No asumir YES/NO por función o nombre parecido |
| S05 NR 28 `madvise` | `DECISION_REQUIRED` | CP022; pendiente por `MADV_*`/backing | FAM-REL con particiones relevantes en scope | No copiar outcome de otra superficie |
| S06 NR 26 `msync` | `DECISION_REQUIRED` | CP024; UNKNOWN por backing/flags | FAM-REL, variante explícita | No transferir criterio de S05 sin autoridad/evidencia |
| S15 NR 16 `ioctl` | `DECISION_REQUIRED` | CP040; familia UNKNOWN, FIONREAD sólo subcaso | FAM-REL por command/object si se presenta | No inferir resultado syscall-wide desde FIONREAD |

Cardinalidad conservada: 44 `DOCUMENTARY_ONLY` + 23 `NON_BLOCKING` +
10 `DECISION_REQUIRED` = 77. Ninguna fila se materializa aquí.
`ALREADY_CANONICAL` no aplica a los 77 conforme a la definición checkpoint-only
consolidada; no se fuerza esa categoría.

## 11. Máquina de estados de decisión

Estados permitidos y transición:

```text
UNPREPARED
  ├──> EVIDENCE_PENDING
  ├──> READY_FOR_HUMAN
  └──> BLOCKED

EVIDENCE_PENDING
  ├──> READY_FOR_HUMAN       sólo al satisfacer evidencia y validación
  └──> BLOCKED

READY_FOR_HUMAN
  ├──> HUMAN_DECIDED         respuesta explícita dentro de opciones/scope
  ├──> EVIDENCE_PENDING      humano solicita evidencia faltante; sin outcome
  └──> BLOCKED

HUMAN_DECIDED
  ├──> CANON_PENDING         sólo con autorización FAM-CHANGE exacta
  ├──> VERIFIED              sólo si el efecto es documental/no canónico y
  │                           una verificación del registro de decisión basta
  └──> BLOCKED

CANON_PENDING
  ├──> CANON_APPLIED         diff exactamente igual al change set autorizado
  └──> BLOCKED

CANON_APPLIED
  ├──> VERIFIED              controles before/after y scope pasan
  └──> BLOCKED               cualquier delta inesperado o check fallido

BLOCKED
  ├──> EVIDENCE_PENDING      sólo al registrar el impedimento removido
  └──> UNPREPARED            si el packet se retira/reinicia con audit trail
```

No existe transición automática `HUMAN_DECIDED → VERIFIED`. Para un outcome
no canónico puede registrarse/verificarse el acta y marcarse que no hubo
efecto de canon; eso verifica el registro de la decisión, no la verdad
normativa ni A-PRE-0. Un cambio de criterio/scope/evidencia invalida el
packet preparado y requiere revisión antes de volver a `READY_FOR_HUMAN`.

## 12. Plantilla futura del decision packet

No completar ni circular ahora. En la futura solicitud al humano incluir sólo
lo necesario para esa decisión:

```text
DECISION_ID:
FAMILY:
QUESTION:
SCOPE:
  IN_SCOPE:
  OUT_OF_SCOPE:
SUBJECTS:
EVIDENCE:
  EVIDENCE_ID / SOURCE / SOURCE_TYPE / HASH / SCOPE
  CLAIM_SUPPORTED:
  CLAIM_NOT_SUPPORTED:
  PROVENANCE:
  LIMITATIONS:
BASELINE:
  AUTHORITY_STATUS:
  BASELINE_DEPENDENCY: NONE | PARTIAL | REQUIRED
  BLOCKED_CLAIM:
OPTIONS:
  [opciones enumeradas y consecuencias por opción]
DEPENDENCIES:
HUMAN_CHOICE:
RATIONALE:
AUTHORITY:
EFFECT:
NON_EFFECT:
DOWNSTREAM_LEVEL:
REVERSIBILITY:
AUDIT_REFERENCE:
VERIFICATION:
```

Se rechazan como respuesta suficiente frases no mapeables al scope/opción,
incluyendo “sí, parece correcto”, “aplicar en general” o “cerrar todos los
casos relacionados”. El packet debe pedir que se elija una opción identificada
o `DEFER`, y el rationale debe explicar cualquier diferencia entre la opción
y la evidencia.

El decision packet presenta solamente pregunta, scope, evidencia, límites,
opciones, consecuencias, dependencias, estado de baseline y efecto posterior.
La historia que no soporte la pregunta concreta queda en `AUDIT_REFERENCE`,
no se presenta como ruido deliberativo.

## 13. Efecto canónico y verificación posterior

`HUMAN_DECIDED` sólo registra una respuesta. Para cambiar manifest/ledger se
requiere:

1. decisión con status `HUMAN_DECIDED`, evidencia validada y scope congelado
   en el packet;
2. change set exacto de `FAM-CHANGE`, con archivos/filas/campos old→new;
3. aprobación explícita del change set;
4. aplicación del diff sin ejecutar actividad fuera del alcance autorizado;
5. verificación independiente de §13.1.

No se redefine el predicate A-PRE-0 y no se asume que un cambio a canon sea
readiness pass.

### 13.1 Registro post-change obligatorio

| Campo | Verificación |
|---|---|
| `BEFORE_HASH` | SHA-256 de cada artefacto en el scope antes de aplicar. |
| `AFTER_HASH` | SHA-256 tras aplicar; registrar sin reemplazar el before. |
| `CHANGED_FIELDS` | Lista exacta de paths/keys/NR/surface ID y valores. |
| `EXPECTED_CHANGES` | Comparación literal con `EFFECT_SCOPE` autorizado. |
| `UNEXPECTED_CHANGES` | Debe ser vacío. |
| `SCOPE_CHECK` | Debe demostrar que cada cambio pertenece al scope y ninguno lo excede. |
| `COUNT_CHECK` | Recalcular cardinalidades afectadas sin “arreglar” otros contadores. |
| `INVARIANT_CHECK` | Confirmar invariantes del packet y estado no afectado. |
| `VERIFICATION` | `PASS` sólo si todos los checks pasan; si no, `FAIL` y estado `BLOCKED`. |

Si aparece cualquier cambio fuera de scope: `VERIFICATION=FAIL`, estado
`BLOCKED`; no continuar a otro nivel. No revertir a ciegas; documentar el diff
observado y detenerse para revisión autorizada.

### 13.2 No extrapolación y A-PRE-0

```text
HUMAN_DECISION ≠ CANONICAL_CHANGE ≠ A_PRE_0_READY
```

Una decisión puede contribuir únicamente a su nivel declarado. Ni un outcome
relacional, ni una disposition individual, ni una reparación documental
resuelve automáticamente las otras filas, variantes, traceability, ABI
enforcement, predicate o identidad del snapshot. A-PRE-0 sólo podrá evaluarse
cuando se cumplan las condiciones ya fijadas por el predicate existente; este
checkpoint no lo redefine ni predice su resultado. A-PRE-1 continúa fuera de
autorización.

## 14. Resumen de preparación para el siguiente tramo

- Las cuatro familias no se fusionan: `FAM-REL`, `FAM-GLOBAL`,
  `FAM-CRITERIA`, `FAM-CHANGE`.
- Los scopes internos de relation/global se conservan; 157 + 10 relaciones y
  385 outcomes son unidades, no un conteo de deliberaciones humanas.
- Los siete gates de CP059 se mapean en §3; H02/H03 no reaparecen como gates
  redundantes.
- `GATE-E01` a `GATE-E05` son prerrequisitos/verificaciones, no decisiones.
- Los 61 provenance partial no bloquean decisiones independientes de su
  linaje; si el linaje se usa como premisa, se convierte en prerequisito del
  packet concreto.
- Los 77 checkpoint-only se clasifican sin reabrir outcomes históricos ni
  materializarlos.
- No se crea ni presenta un decision packet concreto a un humano en esta
  tarea.

## 15. Verificación final

| Check | Resultado |
|---|---|
| Cuatro familias de CP060 preservadas | Sí |
| Scopes separados dentro de FAM-REL/FAM-GLOBAL/FAM-CRITERIA/FAM-CHANGE | Sí |
| H01–H07 de CP059 referenciados | Sí |
| H02/H03 redundantes no reaparecen como gates independientes | Sí |
| 385 filas/nombres/NR únicos; 385 global UNKNOWN | Sí, comprobación estructural local del manifest |
| 162 tags reconciliados = 157 abiertos + 5 overlaps | Sí, según CP058/060; no recontado desde evidencia dinámica |
| 10 UNKNOWN relacionales / 61 partial / 77 checkpoint-only | Sí, conservados según CP058–060 |
| Baseline | `AUTHORITY_UNRESOLVED`; `f058…` `UNRECOVERED` |
| `inventory.frozen` | `false` |
| A-PRE-0 / A-PRE-1 | `NOT_READY` / `NOT_AUTHORIZED / NOT_EXECUTED` |
| Manifest, ledger, specs, crosswalk, `requirements.lock` | Sin cambios por esta tarea |
| Hashes protegidos | Manifest `801f…fd6e`; ledger `0961…4a42`; lock `8134…4a70`; specs `23e2…ccd0` y `b458…5c8c` |
| Actividad dinámica | Ninguna |

