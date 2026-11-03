# Checkpoint 065 — cierre metodológico del bloqueo de baseline authority

Fecha: 2026-10-01

## 1. Resultado y límite del cierre

CP064 concluyó:

```text
BASELINE_AUTHORITY_RESOLVABILITY = NOT_RESOLVABLE_FROM_EXISTING_EVIDENCE
EXTERNAL_SPEC_ARTIFACT = UNRECOVERED
BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED
STOP_REASON = OPEN_EXTERNAL_EVIDENCE_REQUIRED
```

CP065 formaliza ese resultado como **cierre de la investigación con las
fuentes internas disponibles**, no como resolución de autoridad ni como
cierre del blocker normativo:

```text
INTERNAL_AUTHORITY_ARCHAEOLOGY = CLOSED_NO_FURTHER_INTERNAL_RECONSTRUCTION
BASELINE_AUTHORITY_BLOCKER_RECORD.STATUS = OPEN_EXTERNAL_EVIDENCE_REQUIRED
```

No se reabre la comparación de copias ni la búsqueda en las mismas fuentes.
La autoridad permanece irresuelta hasta que aparezca evidencia nueva,
verificable y suficiente según §5. `SCOPE_UNPROVEN` del contador 63 permanece
sin cambio. L0 sigue cerrado; A-PRE-0 sigue `NOT_READY` y A-PRE-1
`NOT_AUTHORIZED / NOT_EXECUTED`.

La auditoría de Directiva 066 detectó que la versión inicial de este
checkpoint no definía el gate de autorización externa y todavía mostraba la
acción heredada `RESOLVE_BASELINE_AUTHORITY`. Se conserva el resultado de
CP064, pero se aclara aquí que la acción inmediata siguiente sólo puede ser
obtener autorización humana para una búsqueda externa; esa autorización no
resuelve la autoridad ni inicia por sí misma la búsqueda.

## 2. Qué quedó demostrado y qué no

### Demostrado con el expediente disponible

- Existen dos copias locales distintas:
  - `docs/A_PRE_0_BASELINE_SPEC.md`, SHA-256
    `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c`;
  - `files/A_PRE_0_BASELINE_SPEC.md`, SHA-256
    `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0`.
- CP052 reconstruyó genealogías locales diferentes. Git demuestra presencia,
  cambios y blobs locales, no una designación normativa.
- El ledger contiene una referencia a
  `/home/agustin/apre-runner/rev4-clean/docs/A_PRE_0_BASELINE_SPEC.md`,
  SHA-256 `f058426b2a7315a90b651eb77d27f2e1c64209105fe8fdc4c1213218d19a0ad4`,
  con `present_in_qualified_overlay=false`.
- CP052–064 no identifican los bytes del artefacto `f058…` ni una relación
  exacta de identidad entre esa referencia y cualquiera de las dos copias.
- La evidencia interna examinada no demuestra una cadena verificable de
  actor autorizado → designación → artefacto exacto → scope/precedencia.
- Por CP053, ninguna de las copias locales fue designada para uso normativo
  actual. `BASELINE_SPEC_AUTHORITY` continúa `AUTHORITY_UNRESOLVED`.

### No demostrado con el expediente disponible

- La identidad exacta del artefacto externo `f058…`.
- Quién lo designó y mediante qué proceso o acto verificable.
- Una declaración competente de autoridad aplicable al baseline.
- El scope normativo autorizado de un artefacto concreto.
- La precedencia o sustitución entre el artefacto externo y las copias locales.

“No demostrado” se refiere al material disponible y examinado por CP052–064;
no afirma que no exista evidencia fuera de ese expediente.

## 3. Afirmación normativa bloqueada

La afirmación mínima que no puede hacerse es:

> **No puede determinarse cuál artefacto concreto posee autoridad normativa
> para fijar el baseline contra el que deben juzgarse el inventario de
> referencia y sus outcomes normativos A-PRE-0.**

Esta limitación no invalida los hechos descriptivos ya verificados sobre
archivos, hashes, genealogías, filas, referencias y estados serializados.
Impide únicamente cerrar como norma las afirmaciones cuyo criterio o
precedencia dependen de ese baseline.

## 4. `BASELINE_AUTHORITY_BLOCKER_RECORD`

| Campo | Registro |
|---|---|
| `BLOCKER_ID` | `BA-065-01` |
| `STATUS` | `OPEN_EXTERNAL_EVIDENCE_REQUIRED` |
| `CLAIM_BLOCKED` | Determinar qué artefacto concreto es la autoridad normativa aplicable al baseline A-PRE-0 para el inventario de referencia y sus outcomes normativos. |
| `EVIDENCE_AVAILABLE` | Dos copias locales con identidad/hash/genealogía diferenciadas; referencia ledger `f058…` con path y ausencia declarada del overlay; CP052–064 documentan búsqueda interna delimitada sin vincular el hash externo a una copia y CP053 mantiene no-designación actual. |
| `EVIDENCE_MISSING` | Evidencia verificable suficiente de actor competente, declaración/designación, identidad exacta del artefacto gobernante, scope y precedencia/sustitución. |
| `WHY_INTERNAL_RECONSTRUCTION_IS_INSUFFICIENT` | Los datos locales identifican archivos y hechos históricos, pero no el acto competente que confiere autoridad. Repetir búsquedas en esos mismos registros, derivar autoridad del tracking/nombre/contenido o escoger una copia produciría una inferencia, no la evidencia faltante. CP064 clasificó el conjunto disponible como `NOT_RESOLVABLE_FROM_EXISTING_EVIDENCE`. |
| `AFFECTED_LEVELS` | `L1`: bloquea el cierre normativo/global cuyo criterio requiere autoridad. `L2`: bloquea justificar cambios canónicos dependientes de ese contenido; no impide describir o revisar un diff no normativo independiente. `L3`: baseline/identidad normativa es una condición necesaria, además de los restantes gates de readiness. |
| `NON_AFFECTED_LEVELS` | `L0`: crosswalk descriptivo cerrado. No bloquea documentación descriptiva, auditorías de integridad, provenance histórica delimitada ni preparación metodológica explícitamente independiente de authority. |
| `REOPEN_TRIGGER` | Evidencia nueva, no disponible durante CP064, verificable y suficiente para iniciar una nueva evaluación bajo una de las rutas de §5. La mera repetición/copia de evidencia ya examinada no activa reapertura. |

## 5. Evidencia mínima para reabrir

La reapertura requiere evidencia que satisfaga al menos una ruta. Cada ruta
debe ser verificable y suficiente en sus elementos; no se presume válida
automáticamente por su formato o procedencia declarada.

### Ruta A — artefacto autoritativo recuperado

Reabrir si se presenta:

```text
ARTIFACT_IDENTITY
+ HASH/IDENTITY_PROOF
+ AUTHORITY_DECLARATION
+ SCOPE
```

La identidad debe enlazar exactamente el artefacto recuperado con la
declaración de autoridad; el hash debe poder verificarse sobre los bytes
recuperados o existir otra prueba de identidad equivalente. La declaración
debe cubrir el scope normativo relevante.

### Ruta B — declaración normativa recuperada

Si el artefacto exacto no está disponible, reabrir sólo si una declaración
explícita y verificable identifica:

```text
AUTHORIZED_ACTOR
+ DESIGNATED_BASELINE
+ SCOPE
+ PRECEDENCE
```

La declaración debe permitir identificar inequívocamente el baseline al que
se aplica y su precedencia frente a designaciones concurrentes o posteriores.
No convierte por sí sola bytes no identificados en artefacto recuperado.

### Ruta C — registro de autoridad verificable

Un registro histórico/externo puede ser suficiente para reabrir si establece
inequívocamente:

```text
WHO
+ WHAT
+ WHEN/REVISION
+ SCOPE
+ AUTHORITY
```

Su autenticidad, integridad, competencia del emisor y vínculo con el
artefacto/scope deberán evaluarse antes de considerar autoridad resuelta.

### Insuficiente por sí solo

No activa reapertura ni demuestra autoridad por sí solo:

- copia local sin declaración de autoridad;
- hash aislado;
- nombre de archivo, ruta o fecha;
- Git tracking o commit histórico sin declaración de autoridad;
- similitud textual o coincidencia parcial con `f058…`;
- repetición de una referencia en checkpoints;
- decisión del agente sin autoridad externa/verificable;
- mayor completitud o aparente calidad del contenido.

Una nueva copia de material ya examinado no es evidencia nueva salvo que
aporte información de autoridad antes ausente y verificable.

## 6. Reapertura no equivale a resolución

El proceso queda separado en estas etapas:

```text
CLOSED_BLOCKER
    ↓ NEW_EVIDENCE (meets a reopening route)
REOPENED
    ↓ AUTHORITY_ADJUDICATION (verify identity, actor, declaration, scope, precedence)
RESOLVED / REMAINS_UNRESOLVED
```

La evidencia nueva puede hacer la cuestión `REOPENABLE`; no cambia
automáticamente `BASELINE_SPEC_AUTHORITY`. Después de reabrir, los elementos
de autoridad deben comprobarse y el resultado puede seguir irresuelto. CP065
no ejecuta ni predetermina esa adjudicación.

## 7. `BASELINE_INDEPENDENT_WORK`

| Puede continuar sin baseline authority | Continúa bloqueado por baseline authority cuando la afirmación dependa de ella |
|---|---|
| Documentación descriptiva del estado y sus límites | Cierre normativo/global L1 y outcomes que requieran criterio autorizado |
| Crosswalk descriptivo y reconciliaciones de representación explícitamente no normativas | Cambios canónicos L2 cuyo contenido/justificación normativa dependa del baseline |
| Auditorías de integridad, hashes y estructura sin elevarlos a autoridad | Claims de completitud normativa que requieran aplicar la baseline |
| Documentación de provenance histórica con scope y límites explícitos | Evaluación `READY` de A-PRE-0 mientras baseline/snapshot autorizado sea prerrequisito |
| Preparación metodológica y mantenimiento de checkpoints | Cualquier adjudicación de outcomes cuyo criterio aplicable siga dependiendo de authority |
| Análisis no normativo e independiente del baseline | No quedan bloqueados los hechos descriptivos sobre las copias, hashes o registros por el solo hecho de que authority siga unresolved |

`AUTHORITY_UNRESOLVED` **no significa que todo TALOS esté inválido ni que
toda actividad documental deba detenerse**. Significa exclusivamente que las
afirmaciones que requieren esa autoridad no pueden cerrarse normativamente.
Se preserva la separación entre `DESCRIPTIVE_TRUTH` y
`NORMATIVE_AUTHORITY`.

## 8. `LEVEL_BLOCKER_MATRIX`

| Nivel | Estado preservado | Dependencia exacta de autoridad | Efecto de CP065 |
|---|---|---|---|
| `L0_DESCRIPTIVE_CROSSWALK` | `CLOSED` | Ninguna para describir filas, referencias y discrepancias ya delimitadas. | Sin cambio; el blocker no invalida el cierre descriptivo. |
| `L1_GLOBAL_CLOSURE` | `BLOCKED` para cierre normativo | Requiere baseline/criterio autorizado para cerrar outcomes globales y su regla de cierre. Los facts/estados descriptivos pueden seguir documentándose sin esa autoridad. | No cambia estado; define condición de reapertura del blocker. |
| `L2_CANONICAL_MODIFICATION` | `BLOCKED` para cambios dependientes de norma; no hay change set aquí | La justificación del contenido canónico afectado requiere autoridad. La autorización procesal de un diff no crea autoridad normativa. | No crea ni autoriza cambios. Work documental/descriptivo independiente puede continuar. |
| `L3_A_PRE_0_READINESS` | `NOT_READY` | Requiere identidad de overlay/spec/snapshot autorizados, además de L1, disposiciones, cobertura/variantes, trazabilidad, enforcement y predicate validado. Resolver authority sería necesario donde el baseline sea condición, pero no garantizaría readiness. | Sigue `NOT_READY`; no modifica predicate ni habilita A-PRE-1. |

L0 continúa cerrado. La dependencia de baseline no se extiende a L0 ni se
extrapola a toda actividad del proyecto.

## 9. Familias de decisión CP060–061

Los cuatro family IDs y scopes se conservan literalmente; ningún packet se
presenta. “Puede preparar” significa trabajo preparatorio de evidencia/scope,
no que la familia esté lista para adjudicación normativa.

| FAMILY | CURRENT_STATUS (CP062) | BASELINE_BLOCKED | PROVENANCE_BLOCKED | CAN_PREPARE_WITHOUT_BASELINE |
|---|---|---|---|---|
| `FAM-REL` — outcomes relacionales, por par syscall NR/name × surface ID y variantes incluidas | No listo; evidence + authority bloquean los outcomes normativos | Sí, para fijar/outcome según criterio normativo | Parcial: 61 linajes siguen parciales; provenance recuperable de otros no sustituye evidencia de efecto/variante | Sí, se puede organizar scope y documentar evidencia/provenance existente; no adjudicar outcome. |
| `FAM-GLOBAL` — outcomes globales, una unidad por cada una de las 385 syscalls | No listo; evidencia de outcome y authority pendientes | Sí, para determinar outcomes globales bajo contrato aplicable | El manifest actual es identificable; provenance del baseline sigue separada | Sí, se puede verificar/describir estructura, filas y gaps de evidencia; no cerrar disposition global. |
| `FAM-CRITERIA` — cobertura/variantes: ABI, interfaz, argumentos, recurso, fase y outcomes aplicables | `BASELINE_AUTHORITY_BLOCKED`; criterio completo no establecido | Sí, es dependencia directa: criterio y suficiencia requieren fuente autorizada | Sí, la spec externa no está recuperada y las copias locales difieren | Sólo preparación metodológica/descriptiva; no fijar criterio normativo ni packet adjudicable. |
| `FAM-CHANGE` — change set exacto de paths/objetos/campos/valores | `NOT_A_DECISION` ahora; no existe change set | Parcial/condicional: autorizar acto de proceso es distinto, pero el contenido normativo requiere authority | Depende de la provenance de cada elemento del eventual diff | Puede mantenerse el protocolo y describirse un diff si existiera por motivo independiente; no existe ni se propone diff aquí, y no se autoriza modificación. |

La preparación metodológica no cambia `UNKNOWN`, no crea membership ni
disposition, no convierte ausencia en exclusión y no eleva evidencia histórica
a autoridad.

## 10. Contador 63

```text
human_adjudicated_candidate_relation_count = 63
SCOPE_UNPROVEN
```

- No se ha demostrado que resolver este contador requiera autoridad del
  baseline: el gap registrado es falta de fórmula, universo, fecha de corte y
  unidad de medida.
- Su interpretación podría resolverse independientemente si apareciera una
  fuente documental que establezca esos elementos; CP063–064 no hallaron esa
  base en el expediente disponible. CP065 no reinicia esa búsqueda.
- El valor no tiene impacto demostrado en L0–L3 ni en la autoridad del
  baseline, salvo que una afirmación futura lo use como evidencia; tal claim
  de scope continúa sin sustento mientras siga `SCOPE_UNPROVEN`.
- No se altera el valor ni se propone una nueva métrica.

## 11. `REOPEN CONDITION`

El problema solamente se reabre cuando aparece **evidencia nueva, verificable
y no disponible en CP064** que permita demostrar al menos uno de:

1. identidad inequívoca del baseline autoritativo;
2. declaración explícita de autoridad;
3. cadena verificable actor → designación → artefacto → scope;
4. registro normativo equivalente con precedencia demostrable.

La evidencia debe satisfacer una ruta de §5 y ser atribuible al artefacto y
scope relevantes. Una nueva copia de los mismos bytes/referencias no cuenta
por sí sola. La reapertura inicia evaluación; no resuelve autoridad, no elige
entre copias y no autoriza cambios.

## 12. `GATE_EXTERNAL_EVIDENCE_AUTHORIZATION`

```text
GATE_EXTERNAL_EVIDENCE_AUTHORIZATION = AUTHORIZED
NEXT_MINIMAL_ACTION = OPEN_SEPARATE_EXTERNAL_EVIDENCE_INVESTIGATION
STOP_REASON = OPEN_EXTERNAL_EVIDENCE_REQUIRED
```

Pregunta exclusiva del gate:

> ¿Existe autorización humana para buscar evidencia externa destinada a
> intentar resolver la autoridad del baseline?

El gate no decide cuál es la autoridad del baseline ni qué decisión normativa
corresponde a los 385 syscalls. No solicita ni presenta un decision packet.
CP067 registró que entonces no había autorización afirmativa disponible;
ese estado fue supersedido por la autorización explícita posterior registrada
en CP071. Se autoriza una tarea de investigación externa futura y separada,
pero no se inicia búsqueda en CP071. La autorización para buscar no equivale
a encontrar evidencia suficiente ni resolver authority.

Estado de ejecución:

```text
GATE_EXECUTED = YES (authorization status recorded; no search initiated)
EXTERNAL_SEARCH_EXECUTED = NO
BASELINE_AUTHORITY_RESOLVED = NO
```

No se contactó a personas, no se consultaron servicios/repositorios externos
y no se identificó por inferencia al autor de `f058…`. Continúan vigentes
`EXTERNAL_SPEC_ARTIFACT = UNRECOVERED`,
`BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED`,
A-PRE-0 `NOT_READY`, A-PRE-1 `NOT_AUTHORIZED / NOT_EXECUTED` e
`inventory.frozen = false`.

## 13. Verificación e invariantes preservados

| Check | Resultado |
|---|---|
| Filas/nombres/números únicos | 385 / 385 / 385 |
| Disposiciones globales | 385 `UNKNOWN` |
| Leads | 157 abiertos; 162 tags reconciliados, cinco solapados con exclusiones documentadas |
| Provenance partial | 61, sin reclasificación |
| Relaciones checkpoint-only | 77, documentadas, sin materialización |
| Contador 63 | `SCOPE_UNPROVEN`; valor sin cambio |
| Artefacto externo / authority | `UNRECOVERED` / `AUTHORITY_UNRESOLVED` |
| Inventory | `frozen=false` |
| A-PRE-0 / A-PRE-1 | `NOT_READY` / `NOT_AUTHORIZED / NOT_EXECUTED` |
| Gate externo al cierre de CP065 | `NOT_AUTHORIZED` en ese momento; luego supersedido por autorización explícita CP071. Búsqueda no ejecutada |
| Canon y baseline specs | Manifest, ledger, ambas specs, crosswalk e `requirements.lock` no modificados por CP065 |
| Actividad dinámica / búsquedas externas | Ninguna |
| `git diff --check` | Verificado tras la escritura |
