# Checkpoint 064 — auditoría de resolubilidad de baseline authority

Fecha: 2026-10-01

## 1. Pregunta y conclusión

Pregunta examinada: ¿la evidencia documental ya disponible permite demostrar
quién/qué confiere autoridad normativa al baseline y qué artefacto concreto
posee esa autoridad?

```text
BASELINE_AUTHORITY_RESOLVABILITY = NOT_RESOLVABLE_FROM_EXISTING_EVIDENCE
AUTHORITY_RESOLUTION = NOT_DEMONSTRATED
EXTERNAL_SPEC_ARTIFACT = UNRECOVERED
BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED
```

Hay evidencia parcial sobre el **registro esperado**: el ledger nombra un
path, almacena SHA-256 `f058…` y lo llama `current_normative_spec` bajo la
identidad de un overlay; también declara que el hash no está presente en ese
overlay. Hay identidades y genealogías locales conocidas para dos archivos
distintos. No hay evidencia suficiente para enlazar esos archivos con
`f058…`, acreditar quién autorizó la designación del ledger, demostrar
precedencia/sustitución o delimitar el alcance normativo autorizado de una
copia concreta.

Por tanto, `f058…` es **referenciado pero no recuperado**. El resultado no es
una resolución ni una propuesta para escoger `docs/` o `files/`. Para avanzar
haría falta una fuente/artefacto o declaración de autoridad verificable que
no está en la evidencia local examinada.

## 2. Definición operacional estricta

Para esta auditoría, un artefacto posee autoridad normativa sólo si se
demuestran de forma explícita e independiente los cuatro componentes:

1. **Designación:** declaración de que el artefacto es el baseline normativo.
2. **Actor/proceso:** evidencia de que la designación procede del actor o
   proceso con competencia para establecerla.
3. **Identidad:** identidad verificable del artefacto designado (hash, blob u
   otra referencia exacta).
4. **Scope/precedencia:** alcance normativo definido y evidencia de que no
   existe una designación superior o posterior que lo sustituya.

No bastan nombre, path, tracking Git, fecha, hash aislado, existencia local,
completitud textual, similitud semántica ni repetición en checkpoints. Una
huella Git identifica contenido local; no demuestra por sí sola la autoridad
de ese contenido.

## 3. Estado de partida

Se preservan sin reinterpretación los hechos vinculantes:

- CP063 está completo.
- `EXTERNAL_SPEC_ARTIFACT = UNRECOVERED`.
- `BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED`.
- Las dos copias locales tienen hashes, contenido y genealogías diferenciadas;
  ninguna fue establecida como autoridad.
- El ledger referencia el hash externo `f058…`.
- Contador `human_adjudicated_candidate_relation_count=63`:
  `SCOPE_UNPROVEN`.
- 96 pares provenance recoverable; 61 pares históricamente partial.
- 77 relaciones checkpoint-only documentadas según CP063.
- `NEXT_MINIMAL_ACTION = RESOLVE_BASELINE_AUTHORITY`.

También permanecen 385 filas únicas y 385 disposiciones globales `UNKNOWN`,
157 leads abiertos, 10 UNKNOWN relacionales, `inventory.frozen=false`,
A-PRE-0 `NOT_READY` y A-PRE-1 `NOT_AUTHORIZED / NOT_EXECUTED`.

## 4. `BASELINE_AUTHORITY_CLAIMS`

El estado clasifica lo que cada fuente demuestra **respecto de la autoridad
de `A_PRE_0_BASELINE_SPEC.md`**. Una fuente puede contener una afirmación
normativa para otro scope —por ejemplo, el perímetro de pruebas— sin designar
la autoridad del baseline A-PRE-0.

| CLAIM_ID | CLAIM | SOURCE | SOURCE_TYPE | ARTIFACT_REFERENCED | EXPLICIT_OR_INFERRED | SCOPE | AUTHORITY_ASSERTED | CLASSIFICATION | LIMITATIONS |
|---|---|---|---|---|---|---|---|---|---|
| `BAC-01` | El campo `qualification_identity.current_normative_spec` identifica `/home/agustin/apre-runner/rev4-clean/docs/A_PRE_0_BASELINE_SPEC.md`, SHA `f058…`. | Ledger, `qualification_identity.current_normative_spec` | Registro de identidad/qualification | Path y hash externo `f058…` | Explícita como valor/campo; no es una declaración autenticada de designación | Overlay/qualification v4 que el propio ledger describe | El rótulo `current_normative_spec` **afirma** una referencia normativa esperada | `AMBIGUOUS` | No identifica actor autorizante ni acto de designación; bytes no disponibles; `present_in_qualified_overlay=false`; no demuestra scope/precedencia ni que el ledger sea el acto constitutivo de authority. |
| `BAC-02` | El overlay calificado se identifica por path, commit `2b208379…` y tree `d7ae2718…`; la spec `f058…` no está en él. | Ledger, `qualification_identity` | Snapshot/identity record | Overlay v4 y referencia externa `f058…` | Explícita como metadata de identidad | Un overlay calificado particular | Ninguna nueva autoridad; informa identity/absence | `DESCRIPTIVE_ONLY` | La identidad/ausencia declarada no recupera el spec ni explica quién designó el baseline. |
| `BAC-03` | CP012 enumera `files/A_PRE_0_BASELINE_SPEC.md` como artefacto actualizado de documentación A-PRE. | CP012 §“Artefactos actualizados” | Checkpoint/handoff documental | Ruta local `files/` | Explícita como referencia de artefacto | Consolidación de pistas/filas legacy descrita en CP012 | Ninguna declaración de que sea el baseline del overlay | `DESCRIPTIVE_ONLY` | No fija hash ni designa autoridad; prohíbe modificar overlay v4. |
| `BAC-04` | CP029 cita `docs/A_PRE_0_BASELINE_SPEC.md` para preflight y estado A-PRE. | CP029, identidad/preambulo referenciado por CP052 | Checkpoint de preparación | Ruta local `docs/` | Explícita como documento citado | Preparación de lote S09 | Ninguna designación normativa única | `DESCRIPTIVE_ONLY` | Citar/usar el texto no prueba que sea el artefacto esperado por overlay ni quién lo autorizó. |
| `BAC-05` | CP048/049 observaron la spec `docs/` con hash `b458…` durante sus tareas. | CP048/049, según índice y CP052 | Snapshot/observación documental | Copia local `docs/`, hash `b458…` | Explícita como identidad observada | Workspace/snapshot de esas tareas | Ninguna | `DESCRIPTIVE_ONLY` | Hash observado no se compara como identidad con `f058…` ni confiere autoridad. |
| `BAC-06` | CP052 establece dos linajes locales distintos y no encuentra blob/rename/equivalencia con `f058…`. | CP052 §§2–6 | Auditoría documental y Git history | `docs/` `b458…`; `files/` `23e…`; externo `f058…` | Explícita como resultado negativo de la búsqueda local delimitada | Refs/árboles locales disponibles y fuentes documentales examinadas | Expresamente no asigna autoridad | `EXPLICIT_NON_AUTHORITY` | No demuestra que el archivo externo nunca existió: no se accedió al overlay ni a `rev4-clean`. |
| `BAC-07` | CP053 selecciona la opción C: no usar ninguna copia local como autoridad mientras falte instrucción/evidencia. | CP053 §§1–4 | Decisión de manejo actual del gate humano | Ninguna copia local designada; externo `f058…` sigue no recuperado | Explícita | Manejo actual de las copias y STOP | Expresamente niega designación operativa de `docs/` o `files/` en ese gate | `EXPLICIT_NON_AUTHORITY` | Es decisión de no designar actualmente; no prueba cuál autoridad histórica rigió ni quién puede resolverla. |
| `BAC-08` | CP059–063 preservan `AUTHORITY_UNRESOLVED`; CP063 mantiene `f058…` `UNRECOVERED` y concluye que provenance local no resuelve authority. | CP059–063 | Checkpoints de estado y auditorías | Las tres identidades registradas | Explícita | Estado de trabajo y límites de las tareas | No designa artefacto | `EXPLICIT_NON_AUTHORITY` | Son preservación/resultado de bloqueo, no fuente constitutiva de autoridad normativa. |
| `BAC-09` | CP060 dice que elegir por conveniencia una copia y justificarla con conclusiones derivadas sería circular; CP061–063 prohíben elevar checkpoints/refs a autoridad por sí solos. | CP060 §5; CP061 §§2,5; CP063 §§4,12 | Regla metodológica de auditoría/protocolo | Cualquier copia local o checkpoint | Explícita | Evaluación de authority/provenance | Expresamente insuficiente para designar authority | `EXPLICIT_NON_AUTHORITY` | Prohíbe inferencia, no suministra la declaración faltante. |
| `BAC-10` | Los textos locales contienen afirmaciones normativas sobre su propio objeto y scope; `docs/` llama normativa a la fuente `config/test_perimeter.json` para test perimeter y declara autoridad declarativa del proyecto en `pyproject.toml`. | Copia local `docs/` §§2–3; `files/` contiene reglas A-PRE/overlay | Texto de las specs locales | Los propios textos y, en una afirmación, `config/test_perimeter.json`/`pyproject.toml` | Explícita en el texto, pero no designación verificable de la spec como baseline autorizado | Principalmente perímetro de tests/runtime y reglas descritas por cada copia | No se demuestra que el autor/proceso del baseline haya designado esa copia como autoridad A-PRE-0 | `AMBIGUOUS` | Las afirmaciones de fuente normativa tienen scope distinto; la autoclasificación textual no prueba actor, integridad de autoridad ni precedencia de la spec. |
| `BAC-11` | CP012, CP029, CP050–052 y `index.md` contienen paths, etiquetas o narración histórica, no una declaración verificable de actor competente que seleccione una copia concreta como autoridad actual. | Checkpoints 012/029/050–052 e índice, sintetizados en CP052 §4 | Referencias/índice/handoff | Copias locales y path/hash externo | Principalmente explícita como referencia; inferir authority sería inferencia | Contexto de adjudicaciones y snapshots | Ninguna | `DESCRIPTIVE_ONLY` | Frecuencia, cronología y presencia en index no satisfacen la definición de §2. |
| `BAC-12` | La historia Git muestra `files/` persistida en `main` desde `fae0225…`, y un linaje separado de `docs/` cuyo contenido `b458…` aparece en `a3c8e2d…`; no hay rename/precedencia declarada entre ellas. | CP052 §3; historial local `git log` consultado | Git history local | Blob/rutas `files/` y `docs/` | Explícita sobre commits/rutas; cualquier conclusión de autoridad sería inferida | Historia local disponible | Ninguna designación de authority demostrada | `DESCRIPTIVE_ONLY` | Tracking/commit ancestry establece presencia e historia local, no autoridad normativa ni identidad con `f058…`. |

No se encontró claim que cumpla `EXPLICIT_AUTHORITY` bajo la definición de §2.
`BAC-01` es una aserción explícita del ledger sobre qué referencia considera
“current normative spec”; queda `AMBIGUOUS` para autoridad porque no aporta
designador autorizado, acto, objeto recuperable ni regla de precedencia. No
se degrada a ausencia de referencia: la referencia existe, pero su suficiencia
no.

## 5. Cadena de autoridad

| Eslabón | Evidencia disponible | Estado |
|---|---|---|
| `AUTHORIZED_ACTOR` | Ledger/CP052–063 no identifican quién tuvo competencia para designar la autoridad normative ni adjuntan delegación/proceso de aprobación. CP053 registra decisión de manejo actual, no autoridad histórica. | **No demostrado — enlace roto** |
| `AUTHORITY_DECLARATION` | El campo `current_normative_spec` del ledger es una aserción metadata; no se localiza una declaración independiente/firmada o una decisión de designación con scope y precedence. CP053 explícitamente mantiene C. | **No demostrado — enlace roto** |
| `BASELINE_IDENTITY` | El esperado `f058…` se vincula en el ledger a un path, pero bytes/blob no están disponibles. Las dos copias locales sí tienen identidad propia y hashes distintos. | **Parcial para referencia esperada; roto para identidad del artefacto designado** |
| `BASELINE_SCOPE` | Ledger asocia la referencia con `qualified_overlay` y current spec; el contenido esperado no está recuperado y no hay acto de designación que delimite el alcance gobernante. | **Parcial como metadata del overlay; scope normativo autorizado no demostrado** |
| `CURRENT_ARTIFACT` | Se identifican tres registros: `f058…` citado pero ausente/no recuperado; `docs/` `b458…`; `files/` `23e…`. No hay vínculo identidad/autorización entre ellos. | **No demostrado cuál artefacto concreto posee authority** |
| `SUBSTITUTION/PRECEDENCE` | CP052 no encontró sustitución, rename ni enlace de derivación; no existe una declaración que resuelva precedencia entre las copias. | **No demostrado — enlace roto** |

```text
AUTHORITY_CHAIN = BROKEN
```

No se completa ningún enlace por el hecho de que el ledger tenga un nombre de
campo normativo, de que una copia esté tracked o de que una ruta sea más
reciente/completa.

## 6. `BASELINE_ARTIFACT_COMPARISON`

Hashes completos y genealogía se toman de CP052 y se verifican localmente
para las dos copias presentes. El estado `GIT_STATUS` se refiere a HEAD
`f81134fc2293916210d53c8065f3a0049e52b0b4`, no a autoridad.

| ARTIFACT | HASH | PATH | GIT_STATUS | GENEALOGY | REFERENCES | RELATION_TO_F058 | AUTHORITY_EVIDENCE |
|---|---|---|---|---|---|---|---|
| Copia local `docs/` | `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` | `docs/A_PRE_0_BASELINE_SPEC.md` | Untracked; no existe en tree HEAD | CP052 registra linaje separado; última modificación del contenido observado en `a3c8e2d…`/refs de agentes; su SHA no coincide con el blob tracked de `files/` | CP029 la cita sin hash/authority; CP048/049 observan hash; docs de planificación enlazan relativo | No coincide con `f058…`; no se encontró blob/rename/link | Ninguna declaración de autoridad identificada |
| Copia local `files/` | `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0` | `files/A_PRE_0_BASELINE_SPEC.md` | Tracked en HEAD; blob Git `d100484bc9abfe37dd47a305b9c03d84247ba80b` según CP052; hash de worktree coincide con la copia documentada | Persistida en `main` por `fae02256…`; CP052 no encuentra modificación posterior que la ligue a `f058…` | CP012 la lista como artefacto actualizado; su texto alude a overlay/rev4 | No coincide con `f058…`; no rename/derivation explícito | Tracking/persistencia no es autoridad |
| Referencia externa ledger `f058…` | `f058426b2a7315a90b651eb77d27f2e1c64209105fe8fdc4c1213218d19a0ad4` | `/home/agustin/apre-runner/rev4-clean/docs/A_PRE_0_BASELINE_SPEC.md` | No se identificó objeto en historia local consultada; path externo | Sólo el ledger registra el path/hash; CP052 revisó historia/refs locales y no halló igualdad; no se accedió al checkout externo | Ledger `current_normative_spec`; CP050–053 repiten y acotan la referencia | Es la referencia no recuperada; ninguna copia local tiene ese hash | La etiqueta del ledger es una afirmación ambigua; no hay fuente/actor/proceso que establezca autoridad |

Contenido: CP052 documenta que `docs/` y `files/` son byte y
semánticamente distintos; `docs/` abre `SPECIFIED` y la copia `files/` abre
`NOT READY` e incluye material adicional de readiness/ledger/crosswalk. Esa
diferencia demuestra que no son copias byte-identical; no establece cuál debe
gobernar. No se utiliza completitud o aparente evolución como criterio de
autoridad.

Resultado de comparación: **identidad local conocida; autoridad desconocida**.

## 7. Examen focalizado de `f058…`

Resultado seleccionado:

```text
F058_RESULT = REFERENCED_BUT_NOT_RECOVERED
```

Cadena disponible:

```text
f058… (valor SHA/path en ledger)
    ↓  el ledger afirma que identifica current_normative_spec
path externo rev4-clean/docs/A_PRE_0_BASELINE_SPEC.md
    ↓  bytes declarados ausentes del overlay; no disponibles localmente
artifact identity verificable
    ↓  NO
authorized authority declaration
    ↓  NO
scope and precedence
    ↓  NO
```

CP052 ya documenta una búsqueda limitada a rutas/blobs/historia locales
disponibles en ese análisis: no se halló contenido con hash `f058…`, rename
ni vínculo de blob con `b458…` o `23e…`. CP064 no repite esa arqueología ni
busca afuera. Esto no demuestra que el archivo externo nunca existiera; sólo
que no está identificado por la evidencia permitida aquí. No se descargó,
reconstruyó ni fabricó el artefacto.

## 8. Matriz de identidad y autoridad

Los estados contestan dimensiones distintas:

| Pregunta | Estado | Evidencia/alcance |
|---|---|---|
| ¿Existe una referencia a un baseline? | **Sí** | Ledger nombra una referencia `current_normative_spec` con path/hash `f058…`; esto establece una referencia registrada. |
| ¿Existe un artefacto referenciado identificable por contenido disponible? | **No** | Los bytes `f058…` no están disponibles; el objeto externo sigue `UNRECOVERED`. |
| ¿Existe hash verificable del artefacto externo? | **No, no desde sus bytes** | El ledger almacena una cadena SHA-256; no puede recalcularse sobre el artefacto no recuperado. Los hashes de las copias locales sí son verificables y distintos. |
| ¿Puede reconstruirse su genealogía? | **No** | CP052 no encuentra el blob/path exacto en la historia local examinada; la ruta externa/overlay no se consultó. |
| ¿Existe una declaración explícita de autoridad? | **No suficiente** | Existe la etiqueta metadata `current_normative_spec`, pero no una designación verificable por actor/proceso autorizado. CP053 selecciona mantener autoridad irresuelta. |
| ¿Puede demostrarse scope normativo autorizado? | **No** | El ledger describe relación con overlay; no prueba el scope/alcance completo que una declaración competente habría autorizado. |
| ¿Puede demostrarse sustitución/precedencia? | **No** | No hay acto de versionado/precedencia ni relación demostrada entre las dos copias y `f058…`. |
| ¿Se identifica alguna copia local exacta? | **Sí, dos** | `docs/`=`b458…`; `files/`=`23e…`; identidad conocida no equivale a autoridad. |

## 9. Contador 63 y relevancia para authority

Campo: `ledger.inventory.syscall_dispositions.human_adjudicated_candidate_relation_count=63`.
Resultado heredado: `SCOPE_UNPROVEN`.

```text
SCOPE_IMPACT = DOCUMENTARY_ONLY
```

No hay fórmula/universo/fecha de corte que demuestre qué mide 63. Según CP057,
no coincide de forma demostrada con 239 contextos, 236 IDs ni 187 relaciones
serializadas. Es una limitación de interpretación métrica. No identifica
actor, artefacto, designación, scope del baseline ni precedencia; no cambia
la evaluación de `BASELINE_SPEC_AUTHORITY`. Se mantiene literalmente 63 y no
bloquea L0. No se modifica el ledger.

## 10. Test de suficiencia y bloqueo mínimo

La prueba exige:

```text
AUTHORIZED_ACTOR
+ AUTHORITY_DECLARATION
+ ARTIFACT_IDENTITY
+ SCOPE
```

Estado: **0 de 4 completos** como cadena de autoridad verificable. Hay datos
parciales sobre la referencia esperada y el scope de overlay registrado, pero
no reemplazan ninguno de los cuatro requisitos faltantes. La clasificación
es `NOT_DEMONSTRATED`; como el faltante no puede completarse legítimamente
con las fuentes locales existentes, la resolubilidad global es
`NOT_RESOLVABLE_FROM_EXISTING_EVIDENCE`, no una selección implícita.

### `BASELINE_AUTHORITY_BLOCKER`

| BLOCKER | MISSING_FACT | WHY_REQUIRED | AVAILABLE_EVIDENCE | INSUFFICIENT_EVIDENCE | IMPACT |
|---|---|---|---|---|---|
| No existe cadena verificable de autoridad para el baseline A-PRE-0. | Actor/proceso competente y acto explícito de designación; identidad exacta del objeto designado; scope y regla de precedencia/sustitución. | Sin esos hechos no se puede distinguir una especificación local/contextual de la norma que rige una decisión o readiness. | Ledger registra path/hash `f058…`, la etiqueta `current_normative_spec` y su ausencia del overlay; CP052 conoce las dos copias locales y sus linajes; CP053 mantiene C; CP059–063 preservan el unresolved. | El hash no es verificable sin bytes; copias locales no coinciden; Git history sólo demuestra genealogía/tracking local; checkpoints identifican contenido/scope histórico, no un designador autorizado. | **L1:** bloqueado para cierre normativo. **L2:** bloqueado para justificar contenido canónico normativo (el acto de cambio, por sí solo, no crea authority). **L3:** bloqueado para evaluación A-PRE-0 contra baseline/snapshot con autoridad demostrada. **L0:** no afectado; permanece cerrado descriptivamente. |

Este bloqueo no dice que no exista autoridad fuera de la evidencia accesible;
dice que no se demuestra desde los artefactos permitidos. Si se aporta
posteriormente una fuente original o declaración competente, su identidad,
scope, actor y precedencia deben validarse por separado.

## 11. Resultado de resolubilidad

```text
BASELINE_AUTHORITY_RESOLVABILITY =
NOT_RESOLVABLE_FROM_EXISTING_EVIDENCE

AUTHORITY_CHAIN = BROKEN
BROKEN_AT = AUTHORIZED_ACTOR + AUTHORITY_DECLARATION
             + EXACT_ARTIFACT_IDENTITY + SCOPE/PRECEDENCE
```

Hay provenance documental parcial de la **referencia**, dos copias locales
identificadas y un acta explícita de no-designación actual (CP053). No hay
autoridad normativa demostrada para ninguna de ellas. La única afirmación
positiva directa (`current_normative_spec`) no satisface la comprobación del
actor/proceso ni la identidad y precedencia necesarias.

## 12. `NEXT_MINIMAL_ACTION`

```text
NEXT_MINIMAL_ACTION = RESOLVE_BASELINE_AUTHORITY
```

El trabajo futuro necesitaría una fuente/artefacto original recuperable o una
declaración de autoridad de un actor/proceso competente que identifique
artefacto, scope y precedencia. Ese insumo no está disponible en el estado
actual del repositorio ni en las fuentes históricas enumeradas. CP064 no
realiza búsqueda externa, no pide/elige una copia, no presenta decisión ni
ejecuta esa acción.

## 13. Verificación e invariantes

| Check | Resultado |
|---|---|
| Filas / nombres / NR | 385 / 385 únicos / 385 únicos |
| Disposiciones globales | 385/385 `UNKNOWN` |
| Leads | 157 abiertos; 162 tags reconciliados (5 overlaps excluidos) |
| Provenance | 96 recoverable; 61 históricamente partial |
| Checkpoint-only | 77 documentadas según CP063 |
| Contador 63 | `SCOPE_UNPROVEN`; `SCOPE_IMPACT=DOCUMENTARY_ONLY` |
| Baseline externo/authority | `UNRECOVERED` / `AUTHORITY_UNRESOLVED`; sin reclasificación |
| Inventory | `frozen=false` |
| A-PRE-0 / A-PRE-1 | `NOT_READY` / `NOT_AUTHORIZED / NOT_EXECUTED` |
| Hashes protegidos | Manifest `801f529655f1f4f250a2a374d2afa63f858a9c0875e0e3dc620d112df5f9fd6e`; ledger `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42`; lock `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70`; spec `files/` `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0`; spec `docs/` `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` |
| Canon | Ningún cambio a manifest, ledger, specs, crosswalk o lock |
| Actividad dinámica | Ninguna |
| `git diff --check` | Limpio |

