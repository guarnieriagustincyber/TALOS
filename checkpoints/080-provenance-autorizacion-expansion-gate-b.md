# Checkpoint 080 — provenance de autorización y frontera de expansión

## 1. Alcance y estado preservado

Esta investigación cubre exclusivamente:

1. el origen/fundamento documental de las relaciones `notebook_id → source_id`
   y los roles de fuentes de los cinco notebooks fijados como release;
2. la propagación del `source_id` desde retrieval semilla hasta la expansión,
   el `ContextPack` y el prompt.

No se adjudica qué source ID debe pertenecer a qué currículo. Se distingue la
allowlist técnica actual de cualquier aprobación curricular o de release.

```text
RELEASE_SCOPE = 5 currículos
FADENA_STD_RELEASE_SCOPE = INCLUDED
CRITERION_1 = BLOCKED
CRITERION_2 = BLOCKED
SOURCE_ROLE_ACL_STATUS = BLOCKED
```

CP078 y CP079 se mantienen como referencia normativa del estado anterior.
CP080 agrega provenance encontrada en el plan maestro y amplía el análisis de
`SectionExpander`; no altera la identidad ni las decisiones de ACL.

## 2. Método y fuentes

La inspección fue estática y de sólo lectura. Se examinó:

- [CP077 — reconciliación de identidad](./077-reconciliacion-identidad-gate-b.md),
  en particular sus inventarios por scope.
- [CP078 — adjudicación de `curriculum_id`](./078-adjudicacion-curriculum-id-gate-b.md).
- [CP079 — roles y ACL](./079-adjudicacion-source-roles-acl-gate-b.md).
- [`config/notebook_source_roles.json`](../config/notebook_source_roles.json).
- [`config/notebook_identity_decisions.json`](../config/notebook_identity_decisions.json).
- [`src/study_engine/federation/notebook_registry.py`](../src/study_engine/federation/notebook_registry.py),
  `DEFAULT_NOTEBOOKS`.
- [`docs/PLAN_SUITE_FIX_ESTABILIZACION.md`](../docs/PLAN_SUITE_FIX_ESTABILIZACION.md),
  pasos de reconciliación Gate 2, matriz piloto de fuentes, expediente
  `fadena-std` y reglas propuestas C4/ACL.
- [`src/study_engine/pedagogy/evidence_assembler.py`](../src/study_engine/pedagogy/evidence_assembler.py).
- [`src/study_engine/web/routes/chat.py`](../src/study_engine/web/routes/chat.py).
- [`src/study_engine/storage/sqlite_engine.py`](../src/study_engine/storage/sqlite_engine.py).
- [`src/study_engine/storage/repositories.py`](../src/study_engine/storage/repositories.py).
- [`src/study_engine/retrieval/expansion.py`](../src/study_engine/retrieval/expansion.py).
- [`src/study_engine/web/routes/notebook.py`](../src/study_engine/web/routes/notebook.py).
- Tests existentes enumerados en §12; no se ejecutaron.
- Estado de asociaciones y existencia de source records en
  `data/web_state/knowledge_store.db`, leído con URI `mode=ro` y
  `PRAGMA query_only=ON`, conforme al cotejo reproducible de CP079. En CP080
  no se leyó contenido de corpus/chunks.

Se usaron estos conjuntos, por notebook `n`:

```text
R(n) = source IDs en DEFAULT_NOTEBOOKS[n].sources
U(n) = source IDs declarados como keys en notebook_source_roles.json[n]
P(n) = source IDs persistidos en notebook_sources para n
S    = source IDs con fila en sources
```

Una fila de `notebook_sources` se clasifica por la declaración versionada más
fuerte encontrada para esa misma pareja. Esta clasificación de provenance no
es una decisión de autorización:

- `U∩P`: declaración versionada por notebook y rol;
- `(R∩P)−U`: declaración versionada de pertenencia al notebook, sin rol
  source-specific;
- `P−(U∪R)`: sólo estado de instalación demostrado;
- si existe sólo un estado o una declaración, la autorización de release sigue
  `UNKNOWN` salvo que haya aprobación/decisión positiva explícita.

## 3. Resultado de búsqueda de autoridad

### 3.1 Hallazgos sobre la autoridad positiva

No se encontró una aprobación directa por relación (notebook, source,
propósito, versión) que conceda autorización curricular para el release.
Tampoco se encontró una decisión documental positiva que reemplace ese
prerrequisito para todas las relaciones existentes.

Sí existe documentación útil, con límites explícitos:

1. `notebook_identity_decisions.json` se autodefine como **audit-only**, dice
   que no concede acceso y no es consumido por runtime. Contiene decisiones de
   identidad, no grants de fuentes.
2. `PLAN_SUITE_FIX_ESTABILIZACION.md` establece que `notebook_sources` es la
   ACL técnica efectiva y dispone que las relaciones existentes no se agreguen
   o borren automáticamente. También registra que la mera asociación, una
   entrada de roles, bibliografía o hash no bastan por sí mismos para conceder
   autorización.
3. Ese plan documenta que 33 fuentes de curso que ya estaban asociadas
   recibieron roles por tipo de documento (5 Lenguajes, 5 SO II, 19 STD y 4
   Telecomunicaciones). Es provenance para el cambio de clasificación de rol,
   no aprobación independiente del grant ACL.
4. Para `fadena-std`, el expediente declara expresamente que la autoridad ACL
   está pendiente para sus 30/30 asociaciones. Los estados `BACKED`,
   `REVIEW_PENDING` y `NONEXISTENT` se describen como evidencia, no como
   decisiones de conceder, conservar o revocar.
5. Para las 18 asociaciones de `fase0-soc` sin rol, el plan documenta que se
   preservan porque ya son explícitas en la ACL y deja pendiente validar su
   pertinencia al Roadmap. Es una decisión de no alterar el estado observado,
   no una aprobación curricular individual de esas relaciones.
6. El plan reconoce como pendientes de provenance o tratamiento los dos
   `P−U` de Lenguajes, el `P−U` de SO II y los dos `P−U` de STD. No se
   encontró una adjudicación de autorización para resolverlos.

La expresión del plan “autorizadas” en referencia a filas de
`notebook_sources` describe su función como ACL runtime efectiva. No contradice
el estado de autoridad humana/documental pendiente: la misma documentación
separa la asociación actual de una aprobación para el release.

### 3.2 Clasificación general de evidencia

| Clase | Evidencia encontrada | Alcance probatorio |
|---|---|---|
| `DIRECT_APPROVAL` | Ninguna aprobación directa por relación. | 0 grants demostrados. |
| `DOCUMENTED_DECISION` | Decisiones de no inferir grants, preservar estado sin editar, asignar ciertos roles existentes y dejar authority ACL pendiente. | Documenta el tratamiento del estado; no constituye grant positivo a cada relación. |
| `VERSIONED_DECLARATION` | `notebook_source_roles.json` para relaciones con rol; `DEFAULT_NOTEBOOKS.sources` para relaciones declaradas sólo en registry. | Prueba que la relación/rol fue declarada en archivos versionados; no demuestra aprobación humana ni autoridad académica. |
| `DERIVED_CONFIGURATION` | Hay código que puede asociar fuentes cuando se crea un notebook desde una definición con `sources`. | No se demostró que las filas locales actuales se originaran por esa ruta. No se atribuye provenance derivada a una asociación actual. |
| `INSTALLATION_STATE` | Filas `notebook_sources` consultadas en SQLite. | Prueba sólo el estado de esta instalación y su efecto en la allowlist técnica. |
| `TEST_FIXTURE` | Fixtures con pares sintéticos notebook/source en pruebas de aislamiento. | Sólo evidencia de tests; no es provenance de las relaciones reales. |
| `INFERRED` | No se usó semejanza de materia, título, autor o hash para promover relaciones. | Ninguna relación se clasifica como autorizada por inferencia. |
| `UNKNOWN` | Provenance original y grant de release de las asociaciones actuales. | Es el estado de autorización positiva para las 99 relaciones observadas. |

Las categorías de declaración describen fuentes de evidencia, no estados
exclusivos de autorización. En particular, una relación puede tener
`VERSIONED_DECLARATION` y seguir teniendo `AUTHORIZATION = UNKNOWN`.

## 4. Provenance por conjunto de asociaciones persistidas

El inventario de CP079 contiene los source IDs completos de `R`, `U` y `P`
para cada notebook. El conteo por cada asociación persistida se recalculó con
los conjuntos anteriores y es:

| Notebook | `|P|` | `U∩P`: declaración versionada con rol | `(R∩P)−U`: declaración versionada sólo en registry | `P−(U∪R)`: sólo instalación | Aprobación directa positiva encontrada |
|---|---:|---:|---:|---:|---:|
| `fase0-soc` | 26 | 8 | 6 | 12 | 0 |
| `fadena-lenguajes` | 17 | 15 | 0 | 2 | 0 |
| `fadena-so2` | 14 | 13 | 0 | 1 | 0 |
| `fadena-std` | 30 | 28 | 0 | 2 | 0 |
| `fadena-teleco` | 12 | 12 | 0 | 0 | 0 |
| **Total** | **99** | **76** | **6** | **17** | **0** |

Lectura exacta de las categorías:

- Las **76** filas `U∩P` tienen una declaración versionada por notebook con
  etiqueta de rol en el JSON. Los roles expresan tipo/uso previsto de
  evidencia, no una aprobación independiente de ACL.
- Las **6** filas `(R∩P)−U` están listadas en el registry del notebook pero
  carecen de rol source-specific. La lista del registry demuestra una
  declaración de scope, no el propósito curricular suficiente para convertir
  por sí sola el vínculo en autorización de release.
- Las **17** filas `P−(U∪R)` sólo se pueden atribuir al estado instalado. En
  algunos casos hay una decisión documentada de mantenerlas pendientes o no
  reclasificarlas; esa decisión no añade una declaración source-role ni un
  grant positivo.
- En los **99** casos el estado `notebook_sources` es evidencia de acceso
  técnico efectivo en esa instalación; en ninguno se identificó una aprobación
  positiva por notebook/source/proposito/version que permita afirmar
  autorización curricular demostrada para el release.

## 5. Relaciones compartidas entre scopes

CP079 identificó 23 source IDs repartidos en 48 asociaciones cross-scope.
Para cada relación se indica si existe rol versionado para ese notebook (`U`),
si sólo está listada en registry (`R`), o si la evidencia de esa relación es
únicamente la instalación (`P`). Ninguna categoría implica aprobación.

| Source ID | Asociaciones persistidas y evidencia versionada independiente |
|---|---|
| `src-guia-2025-c04f44ef` | `fase0-soc`: sólo `P`; `fadena-teleco`: rol `METHODOLOGICAL` en `U` y listado `R`. |
| `src_0bc5d20dcc91895f` | `fase0-soc`: sólo `P`; `fadena-so2`: sólo `P`. |
| `src_0fc90b2695369475` | `fase0-soc`: listado `R`, sin rol; `fadena-so2`: rol `PRIMARY` en `U`. |
| `src_a9a056742dcf69ae` | `fase0-soc`: sólo `P`; `fadena-so2`: rol `PRIMARY` en `U`. |
| `src_d253687930308e41` | `fase0-soc`: listado `R`, sin rol; `fadena-so2`: rol `PRIMARY` en `U`. |
| `src_e9682dece40b58ab` | `fase0-soc`: sólo `P`; `fadena-so2`: rol `IMPLEMENTATION` en `U`. |
| `src_f009c4e75f5ca3f2` | `fase0-soc`: sólo `P`; `fadena-so2`: rol `IMPLEMENTATION` en `U`. |
| `src_fadena_prog_arboles` | `fase0-soc`: sólo `P`; `fadena-lenguajes`: sólo `P`. |
| `src_fadena_prog_archivos` | `fase0-soc`: sólo `P`; `fadena-lenguajes`: sólo `P`; `fadena-std`: listado `R` y rol `PRIMARY` en `U`. |
| `src_fadena_prog_lineales` | `fase0-soc`: sólo `P`; `fadena-lenguajes`: listado `R` y rol `PRIMARY` en `U`. |
| `src_fadena_prog_punteros` | `fase0-soc`: listado `R` y roles `IMPLEMENTATION`, `REFERENCE`; `fadena-lenguajes`: listado `R` y rol `COMPLEMENTARY`. |
| `src_fadena_so_concurrencia` | `fase0-soc`: listado `R`, sin rol; `fadena-so2`: listado `R` y roles `PRIMARY`, `METHODOLOGICAL`. |
| `src_fadena_so_memoria` | `fase0-soc`: listado `R`, sin rol; `fadena-so2`: listado `R` y rol `COMPLEMENTARY`. |
| `src_fadena_so_planificacion` | `fase0-soc`: listado `R`, sin rol; `fadena-so2`: listado `R` y rol `PRIMARY`. |
| `src_fadena_so_procesos` | `fase0-soc`: listado `R`, sin rol; `fadena-so2`: listado `R` y rol `PRIMARY`. |
| `src_joyanes_fundamentos` | `fase0-soc`: listado `R`, rol `PRIMARY`; `fadena-lenguajes`: listado `R`, roles `PRIMARY`, `METHODOLOGICAL`. |
| `src_kurose_computer_networking` | `fase0-soc`: sólo `P`; `fadena-teleco`: listado `R`, roles `PRIMARY`, `METHODOLOGICAL`. |
| `src_ramalho_fluent_python` | `fase0-soc`: sólo `P`; `fadena-std`: listado `R` y rol `IMPLEMENTATION`. |
| `src_rosen_matematicas_discretas` | `fase0-soc`: listado `R`, rol `FORMAL`; `fadena-std`: sólo `P`. |
| `src_spraul_think_like_a_programmer` | `fase0-soc`: listado `R`, rol `METHODOLOGICAL`; `fadena-lenguajes`: listado `R`, rol `METHODOLOGICAL`. |
| `src_stallings_computer_security` | `fase0-soc`: sólo `P`; `fadena-so2`: listado `R`, rol `IMPLEMENTATION`; `fadena-teleco`: listado `R`, rol `PRIMARY`. |
| `src_stallings_os_internals_7ed` | `fase0-soc`: sólo `P`; `fadena-so2`: listado `R`, rol `PRIMARY`. |
| `src_sweigart_automate_boring_stuff` | `fase0-soc`: listado `R`, rol `COMPLEMENTARY`; `fadena-lenguajes`: listado `R`, rol `COMPLEMENTARY`. |

El desglose de las 48 relaciones compartidas es: 26 tienen rol versionado en
el scope correspondiente; 6 tienen sólo declaración registry; 16 sólo están
respaldadas por su asociación SQLite en el scope correspondiente. Para cada
pareja sin declaración independiente, el motivo de uso en ese notebook queda
`UNKNOWN`. Los IDs, autores o títulos compartidos no completan esa provenance.

## 6. Diferencias entre `P`, `U` y `R`

### 6.1 `P−U`: asociación sin rol

El estado de autorización del release para todas estas 23 relaciones es
`UNKNOWN`, no `AUTHORIZED_WITHOUT_ROLE`, `UNAUTHORIZED` ni `LEGACY`. Que una
fila opere como allowlist runtime no resuelve su fundamento curricular.

| Scope | Relaciones `P−U` | Evidencia/documentación encontrada | Clasificación de autorización |
|---|---|---|---|
| `fase0-soc` | 18 IDs listados en CP079 §5.1. | El plan documenta su preservación como ACL existente; su pertinencia al Roadmap se declara pendiente. Seis de los 18 también aparecen en `R`, sin rol source-specific; los otros doce carecen de `R` y `U`. | `UNKNOWN` en las 18; preservar ≠ aprobar. |
| `fadena-lenguajes` | `src_fadena_prog_arboles`, `src_fadena_prog_archivos`. | El plan dice que su origen/carpeta no quedó confirmado y los deja sin rol; CP077 registra ambos como asociación sin role. | `UNKNOWN` para ambas. |
| `fadena-so2` | `src_0bc5d20dcc91895f`. | El plan/configuración la identifica como Stallings 5.ª ed. reemplazada por 7.ª para el rol; su asociación existente no se eliminó. No hay decisión de autorización curricular positiva. | `UNKNOWN`; edición antigua documentada, no se deduce estado ACL `LEGACY`. |
| `fadena-std` | `src_f3352475bc0cd360`, `src_rosen_matematicas_discretas`. | El primero es material de soluciones: uso pedagógico/ACL pendiente. Rosen: procedencia específica pendiente y cero chunks según expediente del plan. La autoridad ACL de las 30 relaciones de STD permanece `PENDING`. | `UNKNOWN` para ambas. |
| `fadena-teleco` | Ninguna. | — | — |

### 6.2 `U−P`: rol declarado, no asociado

| Scope | Source ID | Evidencia | Clasificación de disponibilidad/provisionamiento |
|---|---|---|---|
| `fase0-soc` | `src_tori_hacking_etico` | Entrada de role config y source record presente; no está en `P`. | `INTENDED_BUT_NOT_PROVISIONED` describe la diferencia declarativa; no crea autorización ni permite asumir que la omisión fue accidental. |
| `fadena-so2` | `src_rudareanu_linux_sysadmins`, `src_silberschatz_so_7ed`, `src_tanenbaum_so_modernos_3ed` | Entries de roles marcadas `SOURCE_MISSING`; no hay source record ni asociación. | `MISSING_SOURCE`. |
| `fadena-std` | `src_cairo_guardati_estructuras_datos` | Entry de rol `SOURCE_MISSING`; sin source record ni asociación. | `MISSING_SOURCE`. |
| `fadena-teleco` | `src_tanenbaum_computer_networks` | Entry de rol `SOURCE_MISSING`; sin source record ni asociación. | `MISSING_SOURCE`. |
| `fadena-lenguajes` | Ninguna. | — | — |

### 6.3 `R−U`: registry sin role

Las seis relaciones `R−U` son de `fase0-soc` y, en el estado observado,
también pertenecen a `P`: `src_0fc90b2695369475`,
`src_d253687930308e41`, `src_fadena_so_concurrencia`,
`src_fadena_so_memoria`, `src_fadena_so_planificacion` y
`src_fadena_so_procesos`.

El registry es una declaración versionada de source IDs del notebook, pero no
asigna un rol source-specific a esas seis entradas. No se encontró una regla
que demuestre `ROLE_NOT_REQUIRED`, ni que resuelva si falta clasificación.
Resultado por relación: `UNKNOWN` respecto a la necesidad del rol y a la
autorización curricular; se puede describir su estado documental como
`REGISTRY_ONLY_FOR_ROLE_PURPOSE`, no como “sólo registry” en el sentido de
ausencia de asociación. No cambiar `P`, `R` o `U`.

## 7. `SOURCE_MISSING` y `SOURCE_PENDING_OCR`

### 7.1 `SOURCE_MISSING`

- **Dónde aparece:** campo `status` dentro de las entradas de
  `config/notebook_source_roles.json` para las cinco referencias enumeradas en
  §6.2.
- **Consumidores:** la búsqueda estática del runtime no encontró código que
  lea ese `status`. `MultiSourceEvidenceAssembler` lee role keys, roles y
  títulos, y usa `Notebook.sources`; no filtra por `status`.
- **Retrieval/evidencia hoy:** esos cinco IDs carecen de source record y de
  asociación persistida. Por ello no entran en la allowlist efectiva ni se
  solicitan en el ensamblador actual. Esa indisponibilidad deriva de ausencia
  de registro/asociación, no de una barrera que consuma `SOURCE_MISSING`.
- **Qué ocurriría si se crearan después:** el campo `status`, por sí mismo, no
  impediría que el código los considere; no se ejecutó ninguna operación para
  probarlo.
- **Regla de release:** no se encontró una política runtime que defina si un
  source con ese status puede pertenecer al release. La documentación sólo
  dice que una referencia faltante no concede acceso.

### 7.2 `SOURCE_PENDING_OCR`

- **Dónde aparece:** `src_rosen_matematicas_discretas`, rol `FORMAL` de
  `fase0-soc`; está en `U` y en `P`, y tiene source record.
- **Consumidores:** no se encontró lector runtime del campo `status`. El
  ensamblador pedagógico no consulta `status`.
- **Retrieval/evidencia:** no hay un bloqueo explícito por el estado OCR. No
  se inspeccionó el corpus/chunks en CP080, por lo que no se afirma que haya
  contenido recuperable ni se ejecutó retrieval.
- **Regla de release:** no se encontró criterio documentado que determine si
  pending OCR permite incluir la fuente en el release. El rol declarado y la
  asociación persistida no resuelven esa decisión.

En ambos casos, disponibilidad y autorización permanecen como dimensiones
separadas; `status` es metadata declarativa sin enforcement observado.

## 8. Flujo estático de autorización y retrieval semilla

```text
decisión de autorización por relación
        ↓
notebook_sources persistido (P)
        ↓
allowlist del scope en chat
        ↓
retrieval semilla con notebook/source IDs
        ↓
candidatos
```

- No se encontró la primera transición —approval/documented grant por
  relación— para las 99 filas. La existencia del estado `P` no llena ese gap.
- `_authorized_sources_for_scope()` deriva la allowlist del chat desde
  `notebook_sources`. `_filter_requested_sources()` intersecta las fuentes
  activas pedidas con ella. La entrada `notebook_source_roles.json` no concede
  acceso en ese camino.
- Las ramas relevantes de búsqueda reciben source IDs filtrados y/o vuelven
  a filtrar los resultados semilla por `source_id`; el código soporta
  aislamiento por allowlist. La prueba integrada existente documentada para
  STD cubre una positiva/negativa sobre una copia local, pero no las 99
  relaciones ni todos los scopes.
- En el ensamblador pedagógico de concepto, las role keys se intersectan con
  `Notebook.sources`. Si falla la resolución del notebook, retorna sin
  evidencia; si no reúne el mínimo de citas, no recurre a fuentes globales.
  Esto es otro recorrido, no la allowlist del chat.

## 9. Contrato estático de `document_id` y source ID

### 9.1 Esquema y escrituras

- `documents.id` es `PRIMARY KEY` global y `documents.source_id` es
  `NOT NULL`. Una fila `documents` identifica, en el esquema, un solo valor
  `source_id`.
- `chunks` tiene `document_id` y `source_id` separados, cada uno con su propia
  foreign key; el esquema no expresa una foreign key compuesta que obligue a
  que el source del chunk coincida con el source de su documento.
- `SQLiteDocumentRepository.save()` trata un `document_id` existente como
  idempotente sólo si los campos coinciden; una segunda asignación diferente
  se rechaza con `DocumentConflictError`.
- `SQLiteChunkRepository.save_chunks()` carga el source del documento y
  rechaza cada chunk cuyo `source_id` difiera del source del padre.
- Hay rutas en `web/routes/notebook.py` que insertan documentos y chunks
  mediante SQL directo, evitando esa validación de `save_chunks()`. En esas
  rutas observadas, el mismo `source_id` local se escribe al documento y sus
  chunks; esto es evidencia del comportamiento de esas escrituras concretas,
  no una garantía de integridad general de la base.
- No se inspeccionaron las filas de `documents` o `chunks` de la base local en
  CP080; no se afirma presencia o ausencia real de un mismo `document_id` con
  múltiples source IDs en chunks.

### 9.2 Comportamiento de `SectionExpander`

`_assemble_epistemic_context()` determina `retrieval_source_ids`; busca
semillas y filtra `search_results` por `source_id` contra ese conjunto antes
de expandir. `SectionExpander.expand_results()`:

1. agrupa semillas sólo por `document_id` y posiciones;
2. no recibe `retrieval_source_ids`;
3. consulta `chunks` por `document_id` y rango `pos_index`, sin predicado de
   notebook ni de source;
4. toma el `source_id` de cada fila expandida y lo conserva en el objeto
   `ExpandedChunk`;
5. calcula y devuelve `expanded_context_text`.

No compara el source ID de cada vecino con el source ID de su semilla. Después
de la expansión, `chat.py` aplica un filtro adicional de chunks de soluciones
sobre la lista `expanded_chunks`, pero no una intersección con
`retrieval_source_ids`; tampoco reconstruye el texto expandido con una
allowlist por source. El `ContextPack.formatted_context` prefiere
`expanded_context_text` cuando está disponible, y el paquete se pasa al
pipeline de respuesta. La comprobación posterior del conjunto de citas
provenance se construye desde resultados semilla; no impone un source scope
post-expansión sobre el texto ya calculado.

La expansión conserva el `source_id` fáctico de las filas de chunks, pero
conservarlo como metadata no equivale a comprobar que esté autorizado. La
relación `document_id → exactamente un source_id` se cumple en los writes
normales que pasan por `SQLiteChunkRepository`, pero no es una invariante
demostrada para todas las escrituras/filas: el esquema no codifica la igualdad
compuesta y hay rutas SQL directas. Tampoco se encontró una post-filter de
allowlist sobre `expanded_chunks`/`expanded_context_text`.

No se afirma que exista en la base un documento real con chunks de varios
source IDs ni se califica el hallazgo como vulnerabilidad confirmada. Para
establecer la frontera del release a partir de evidencia estática disponible,
la conclusión permanece `UNKNOWN`.

## 10. Matriz de frontera de confianza

| Transición | Estado | Evidencia y límite |
|---|---|---|
| Autorización aprobada → relación de configuración/ACL | `UNKNOWN` | No hay approval por relación para las 99 asociaciones. Hay declaraciones y decisiones de preservación/no inferencia, pero no grants positivos suficientes. |
| Estado persistido `P` → allowlist del chat | `SUPPORTED` | Helper de chat obtiene los IDs de `notebook_sources`; filtro intersecta IDs/SHA solicitados. Es enforcement técnico, no provenance de autorización humana. |
| Allowlist → retrieval semilla por source | `SUPPORTED` | Las ramas de búsqueda de chat reciben filtros y el código vuelve a filtrar resultados semilla por `source_id`. Pruebas existentes cubren fixtures y un caso temporal de STD, no todos los scopes. |
| Retrieval semilla → candidatos de expansión | `OBSERVED` | `search_results` ya pasó por el filtro de source y esos objetos se entregan al expander. |
| Candidato semilla → vecinos por `document_id` | `OBSERVED` | El expander amplía por documento/rango y carga el `source_id` de cada vecino, pero no comprueba igualdad con la semilla ni recibe la allowlist. |
| Vecinos expandidos → post-filter de allowlist | `UNKNOWN` | No existe intersección explícita `expanded_chunks ∩ retrieval_source_ids`; el filtro visible después de expandir trata chunks de soluciones, no source scope. |
| Texto expandido → `ContextPack`/prompt | `OBSERVED` | El texto expandido se usa como `formatted_context` cuando existe y el `ContextPack` llega al pipeline. No hay validación de allowlist entre ambos. |

El primer punto sin evidencia suficiente es la autorización positiva de cada
relación. Independientemente, la garantía de aislamiento por source se vuelve
desconocida al cargar vecinos por documento y no aplicar una barrera posterior
demostrada.

## 11. Dictamen de la frontera de expansión

Se descartan los dos estados soportados:

- **No `SUPPORTED`:** no se demuestra que todo chunk con un `document_id`
  coincida siempre con el `source_id` semilla. La clave de documento es única
  y el repositorio normal valida la igualdad, pero el esquema no la exige y
  existen rutas SQL directas.
- **No `SUPPORTED_BY_POSTFILTER`:** el flujo no intersecta explícitamente
  chunks/texto expandidos con `retrieval_source_ids` antes del `ContextPack`.

Estado:

```text
EXPANSION_SOURCE_BOUNDARY = UNKNOWN
```

Esto es una brecha probatoria del límite estático. Sin observar una violación
en datos reales o una ejecución, no se afirma que un documento almacenado
mezcle sources ni que haya ocurrido contaminación.

## 12. Tests existentes y límites

Los siguientes tests fueron inspeccionados, no ejecutados:

| Test | Input/superficie | Invariante que prueba | ¿Source boundary? | Caso negativo y límite |
|---|---|---|---|---|
| `tests/context/test_section_expander.py::test_expansion_merges_contiguous`, `test_expansion_window_pm2` | Stores en memoria; cada documento/chunk usa un source ID. | Ventanas contiguas y límites de expansión. | No. | Sin chunks de source distinto bajo el mismo `document_id`; no recibe allowlist. |
| `tests/context/test_section_expander.py::test_expansion_respects_ceiling`, `test_expansion_cuts_by_relevance` | Fixture de un documento/source. | Techo de tokens, prioridad de semillas y relevancia. | No. | No verifica scope ni vecino foráneo. |
| `tests/context/test_section_expander.py::test_context_pack_has_provenance`, `test_no_floating_citations` | Fixture de un documento/source. | Metadata de source/document/page y formato de cita. | No. | Verifica presencia de provenance, no que el source sea permitido. |
| `tests/retrieval/test_section_expansion_ceiling.py::test_section_expander_fuses_windows_and_formats_explicit_metadata` | Fixtures de fuente/documento/chunks todos del mismo source. | Ventanas fusionadas y tags de contexto. | No. | Sin caso multi-source ni allowlist. |
| `tests/retrieval/test_section_expansion_ceiling.py::test_section_expander_strictly_enforces_hard_ceiling` | Fixture de un source. | Presupuesto de tokens. | No. | Ninguna aserción de source scope. |
| `tests/pedagogy/test_evidence_assembler_isolation.py` | Fake store con un source permitido y otro sólo configurado como role. | Intersección `U∩P`, ausencia de enumeración global y abstención. | Parcial para el ensamblador, no expander/chat. | El no asociado no se consulta; es fixture de un notebook. |
| `tests/unit/web/test_retrieval_scope_allowlist.py` | SQLite sintética de dos notebooks y dos source IDs. | Derivación de allowlist por folder y filtro de active source ID/SHA. | No para vecinos expandidos. | Fuente de otro scope es negativa en helper; no se construye `SectionExpander`. |
| `tests/unit/web/test_global_scope.py` | Dos notebooks/folders, documentos separados. | Retrieval limitado a notebooks descendientes y asociaciones explícitas. | No para un mismo `document_id`; no cubre expansión por source. | Negativo cross-folder; fixture sintética. |
| `tests/pedagogy/test_chat_sse_endpoint.py::test_chat_sse_retrieves_only_sources_authorized_for_notebook_scope` | Fuentes temporales asociadas a notebooks distintos. | El prompt conserva target y excluye una fuente foránea solicitada. | Parcial para retrieval/chat, no frontera del expander. | El source foráneo es de otro notebook y documento; no prueba vecino cross-source con ID de documento compartido. |
| `tests/pedagogy/test_chat_sse_endpoint.py::test_fadena_std_real_corpus_isolation_on_temporary_database_copy` | Prueba documentada en el plan contra una copia local temporal de DB, backend capturador. | Un source positivo y uno de otro notebook negativo; source filter, prompt y SSE provenance. | No demostrado para expansión: no hay aserción de `expanded_chunks` ni fixture con dos source IDs en un documento. | Es un caso real/sintético de STD, no generaliza a los cinco scopes ni prueba documentos multi-source. CP080 no la volvió a ejecutar. |
| `tests/storage/test_notebook_isolation.py` | Stores aislados temporales. | Búsqueda por notebook, asociaciones explícitas, scopes inexistentes. | No para SectionExpander. | Aislamiento en consultas del store; no vecinos por `document_id`. |
| `tests/retrieval/test_presentation_filter.py` | SearchResults con IDs de chunks de enunciado/solución. | Exclusión de solución protegida. | No. | No es autorización por notebook/source. |

Las pruebas de ventana, presupuesto y provenance de citas no prueban aislamiento
de source. La única prueba integrada documentada para una base de curso examina
un positivo y un negativo de notebook en STD; no cubre el límite de expansión
planteado.

## 13. Gaps y evidencia necesaria

### Provenance/autorización

1. No hay grant documental aprobado por cada relación ni registro de
   `(notebook_id, source_id, scope, purpose/role, versión)` con autoridad
   positiva para las 99 asociaciones.
2. 76 relaciones tienen roles versionados, pero éstos no son approval.
3. 6 asociaciones de Fase 0 tienen declaración de registry sin role
   source-specific; 17 sólo se explican por instalación.
4. Quedan 23 relaciones `P−U`, 6 `U−P`, y 6 `R−U` sin adjudicación completa,
   con los tratamientos particulares descritos en §6.
5. La provenance de cada una de las 48 relaciones cross-scope sólo es
   independiente en 26 casos de rol; seis tienen declaración registry sin
   rol y dieciséis dependen de estado instalado.
6. Se deben conservar los dictámenes pendientes existentes sobre autoridad
   ACL, incluida la pendiente explícita de 30/30 relaciones de `fadena-std`.

### Frontera de expansión

Para convertir `UNKNOWN` a `SUPPORTED`, haría falta evidencia de una
invariante fuerte y aplicada a todas las rutas de escritura/filas que garantice
que todos los chunks de un `document_id` tienen el source del documento y de
la semilla. Alternativamente, un checkpoint futuro, autorizado por separado,
podría aportar evidencia de un post-filter explícito de todos los chunks y del
texto que entra al `ContextPack`. CP080 no propone ni implementa ninguna
reparación.

Una validación futura de estado real requeriría autorización específica para
leer las tablas `documents`/`chunks`; una validación dinámica requeriría
autorización independiente para ejecutar una prueba aislada. Ninguna se hizo
en este checkpoint.

## 14. Dictámenes conjuntos

```text
AUTHORIZATION_PROVENANCE_STATUS = PARTIAL
AUTHORIZATION_GRANTS_DEMONSTRATED = 0 / 99
VERSIONED_ROLE_DECLARATIONS = 76
VERSIONED_REGISTRY_ONLY_DECLARATIONS = 6
INSTALLATION_STATE_ONLY = 17
AUTHORIZATION_FOR_ALL_CURRENT_P_RELATIONS = UNKNOWN

EXPANSION_SOURCE_BOUNDARY = UNKNOWN
CRITERION_2_EVIDENCE_STATUS = PARTIAL
CRITERION_2 = BLOCKED
```

`AUTHORIZATION_PROVENANCE_STATUS = PARTIAL` significa que hay declaraciones
versionadas y decisiones documentadas de preservación/no inferencia que
explican parte del estado, pero no el origen/aprobación positiva de todas las
relaciones del release. No equivale a acceso autorizado.

`CRITERION_2_EVIDENCE_STATUS = PARTIAL` describe que existe evidencia de
implementación y de declaraciones versionadas en parte del inventario. C2
permanece `BLOCKED`: no se integraron provenance y autorización de los cinco
scopes con una prueba de retrieval→expansión→ContextPack para cada uno.

## 15. Invariantes y no-acciones

- Se preservan `RELEASE_SCOPE = 5`, `FADENA_STD_RELEASE_SCOPE = INCLUDED`,
  `CRITERION_1 = BLOCKED` y `CRITERION_2 = BLOCKED`.
- No se concedió ni revocó ACL; no se cambió `notebook_sources`.
- No se modificaron roles, registry, catálogo, perfiles, retrieval,
  `SectionExpander`, `ContextPack`, tests, fixtures, DB, corpus, modelos o
  índices.
- La lectura SQLite previa/de referencia fue de sólo lectura; CP080 no leyó
  filas de chunks/documentos ni contenido.
- No se ejecutaron TALOS/FastAPI, retrieval, tests, providers, benchmarks,
  workloads, seeders ni migraciones.
- No se reabrió CP072, no se reinterpretó `fadena_v1` y no se cambiaron gates
  A-PRE.
- No se declaró Gate B cerrado ni `PRODUCT_COMPLETE`.
- Los cambios preexistentes del worktree se preservan.

## Estado final

```text
RELEASE_SCOPE = 5 currículos
FADENA_STD_RELEASE_SCOPE = INCLUDED
CRITERION_1 = BLOCKED
CRITERION_2 = BLOCKED
AUTHORIZATION_PROVENANCE_STATUS = PARTIAL
EXPANSION_SOURCE_BOUNDARY = UNKNOWN
CRITERION_2_EVIDENCE_STATUS = PARTIAL
GATE_B_IDENTITY_STATUS = BLOCKED
```
