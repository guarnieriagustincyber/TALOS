# CP081 — cierre de provenance y modelo documental de Gate B

## 1. Alcance, método y estado preservado

Esta pasada estática intenta cerrar solamente:

1. si existe autoridad normativa superior que explique las relaciones
   `notebook_id → source_id` de las 99 asociaciones de los cinco scopes;
2. si el modelo garantiza `document_id → un único source_id` de forma que la
   expansión por `document_id` conserve necesariamente el source de la semilla.

Se inspeccionaron documentación de Gate 2/C4, declaraciones versionadas,
código de inicialización y escritura, DDL, repositorios, expansores y tests
existentes. No se consultaron filas actuales de `documents` ni `chunks`, no se
ejecutó ningún test y no se inició TALOS, FastAPI, retrieval, proveedores,
benchmarks ni migraciones.

Se preservan sin cambio:

```text
RELEASE_SCOPE = 5 currículos (CP077)
FADENA_STD_RELEASE_SCOPE = INCLUDED
CRITERION_1 = BLOCKED
CRITERION_2 = BLOCKED
```

CP080 informó `AUTHORIZATION_PROVENANCE_STATUS = PARTIAL`, en el sentido de
que hay declaraciones versionadas para una parte de las asociaciones. Aplicada
la regla más estricta de esta pasada —`PARTIAL` requiere provenance normativa
de autorización para alguna parte, no solamente declaraciones de configuración
o tratamiento— esa evidencia no satisface el umbral: no se encontró aprobación
positiva para ninguna relación. CP081 registra por ello el estado de
autorización probada como `UNKNOWN`. No cambia la clasificación descriptiva de
CP080 de los conjuntos R/U/P ni afirma que las relaciones estén denegadas.

## 2. Autoridad de release y origen de las relaciones

### 2.1 Artefactos examinados y alcance documental

| Artefacto | Clasificación | Qué prueba | Qué no prueba |
|---|---|---|---|
| `config/notebook_identity_decisions.json` | `SUPPORTED_DECLARATION` de identidad; expresamente audit-only | Decisiones/referencias de identidad. | No concede acceso, no contiene grants source-scoped y no es autoridad de ACL. |
| `config/notebook_source_roles.json` | `SUPPORTED_DECLARATION` versionada de roles | Rol declarado para las parejas notebook/source enumeradas. | Un rol describe el tratamiento/tipo de evidencia; no es aprobación de uso ni grant. |
| `DEFAULT_NOTEBOOKS` en `src/study_engine/federation/notebook_registry.py` | `SUPPORTED_DECLARATION` versionada de scope | Sources listados en cada notebook de registry. | La lista no documenta por sí sola una aprobación humana por source, propósito y versión. |
| `notebook_sources` | `INSTALLATION_STATE` | La allowlist técnica persistida que la aplicación consume. | La existencia de la asociación no prueba su fundamento normativo ni la provenance de su alta. |
| `docs/GATE2_GENERATOR_IMPLEMENTATION_PLAN.md` | `SUPPORTED_DECLARATION` de proceso/propuesta | Trata ACL/scope como entrada; exige decisiones curriculares y revisión humana de propuestas; declara que no modifica la ACL activa. | No aprueba relaciones source/notebook. |
| `docs/PLAN_SUITE_FIX_ESTABILIZACION.md`, C4 | `HISTORICAL_ARTIFACT` de diseño en estado DRAFT | Define cómo sería una evaluación y decisión scoped; separa evidencia, evaluación, aprobación y efecto ACL. El expediente dice que no contiene decisiones `AUTHORIZED_SCOPED`/`NOT_AUTHORIZED_SCOPED` ni solicitudes/intentos ACL. | No es una política publicada/aplicable ni una aprobación ya emitida. |

No se encontró un artefacto de autoridad superior, versionado y aplicable que
apruebe una o más parejas `(notebook_id, source_id, propósito, versión)`.
Tampoco se encontró una cadena de delegación/decisor que convierta las
declaraciones técnicas identificadas en una aprobación de release. Las
referencias a “autorización” de `notebook_sources` describen su papel como
allowlist efectiva en runtime, no sustituyen la aprobación normativa que los
documentos C4 y Gate 2 separan explícitamente.

### 2.2 Origen estático identificable de R/U/P

Notación conservada de CP080:

```text
R(n) = source IDs listados en DEFAULT_NOTEBOOKS[n].sources
U(n) = source IDs con rol en notebook_source_roles.json[n]
P(n) = source IDs persistidos en notebook_sources para n
```

| Representación | Primer origen estático identificable | Transición identificable | Clasificación y límite |
|---|---|---|---|
| `R` | Declaración `DEFAULT_NOTEBOOKS` del registry. | `_seed_curriculum_tree` lee notebooks del registry, intersecta `nb.sources` con los sources existentes y, tanto al crear como al sincronizar un notebook existente, puede insertar las parejas con `INSERT OR IGNORE`. | `SOURCE_DECLARATION → DERIVATION` = `SUPPORTED` como mecanismo de código. El origen efectivo de cada fila local no queda registrado ni puede atribuirse a esta ruta; por fila es `UNKNOWN`. La declaración no es aprobación normativa. |
| `U` | Declaración versionada `notebook_source_roles.json`. | `evidence_assembler.py` intersecta roles declarados con `notebook.sources`; el rol no crea una asociación ni concede permiso. | `SOURCE_DECLARATION → CONSUMPTION` = `SUPPORTED`; `U → autorización` = `UNKNOWN`. Para 33 asignaciones el plan de estabilización documenta una clasificación de roles según tipo de documento; esto explica la clasificación de rol, no un grant. No se identificó origen superior para las demás declaraciones. |
| `P` | Fila de instalación `notebook_sources`, observada y reconciliada en CP079/CP080. | Puede derivar del seed/bridge de registry o de rutas de ingestión; estas rutas insertan asociaciones, pero no registran evento, decisor ni evidencia del origen de cada fila. | `DERIVATION → PERSISTENCE` = `UNKNOWN` por fila. P prueba el estado técnico efectivo, no la autorización de release. |

Las clasificaciones anteriores son de procedencia técnica, no de adjudicación.
La coincidencia `R∩P`, `U∩P`, un rol, una fuente existente o una asociación
runtime no se promueve a grant.

### 2.3 Los 76 roles y las 17 relaciones solo de instalación

CP080 reconcilió las 99 asociaciones como 76 en `U∩P`, 6 en `(R∩P)−U` y 17
en `P−(U∪R)`. Para las 76 relaciones con role, el origen identificable es la
declaración versionada de rol; no se identificó una fuente normativa superior
que otorgue autorización a esas relaciones. La asignación documentada de 33
roles por tipo de documento es provenance de rol, no autorización.

Las 17 relaciones que solo se explican por instalación se mantienen como
`ORIGIN_UNKNOWN`, no se rehabilitan ni se clasifican como legacy sin
evidencia:

| Scope | Cantidad | Relaciones `P−(U∪R)` |
|---|---:|---|
| `fase0-soc` | 12 | `src-guia-2025-c04f44ef`, `src_0bc5d20dcc91895f`, `src_a9a056742dcf69ae`, `src_e9682dece40b58ab`, `src_f009c4e75f5ca3f2`, `src_fadena_prog_arboles`, `src_fadena_prog_archivos`, `src_fadena_prog_lineales`, `src_kurose_computer_networking`, `src_ramalho_fluent_python`, `src_stallings_computer_security`, `src_stallings_os_internals_7ed` |
| `fadena-lenguajes` | 2 | `src_fadena_prog_arboles`, `src_fadena_prog_archivos` |
| `fadena-so2` | 1 | `src_0bc5d20dcc91895f` |
| `fadena-std` | 2 | `src_f3352475bc0cd360`, `src_rosen_matematicas_discretas` |
| `fadena-teleco` | 0 | — |
| **Total** | **17** | **Todas `ORIGIN_UNKNOWN`** |

La documentación de preservación/pendencia encontrada para algunas relaciones
no registra su origen inicial ni equivale a aprobación.
`INSTALLATION_STATE != RELEASE_AUTHORIZATION`.

### 2.4 Dictamen de provenance

Conforme a la regla de CP081:

- `RESOLVED` no aplica: no existe una representación normativa de aprobación
  que explique todas las relaciones del release.
- `PARTIAL` no aplica en sentido de autorización: ninguna relación tiene
  aprobación positiva demostrada. Las 76 declaraciones de role y las seis de
  registry son declaraciones técnicas/de rol, no provenance normativa de
  grants.
- `UNKNOWN` aplica: no puede demostrarse autorización normativa para el
  release completo ni para una parte de las asociaciones.

```text
AUTHORIZATION_PROVENANCE_STATUS = UNKNOWN
```

Esta clasificación estrecha corrige el alcance probatorio de la etiqueta
`PARTIAL` de CP080; no contradice sus conteos ni transforma `UNKNOWN` en
rechazo. Las 99 asociaciones conservan el estado y efecto descritos en CP079 y
CP080. C2 permanece `BLOCKED`.

## 3. Modelo `documents` / `chunks`

### 3.1 Contrato estructural del DDL

El DDL de `src/study_engine/storage/sqlite_engine.py` define:

- `documents` como entidad independiente; `documents.id` es `PRIMARY KEY` y
  `documents.source_id` referencia `sources.source_id`.
- `chunks.document_id` referencia `documents.id`.
- `chunks.source_id` referencia independientemente `sources.source_id`.
- No existe FK compuesta, `UNIQUE` ni `CHECK` que exija
  `chunks.source_id = documents.source_id`.

Por tanto, el DDL garantiza que cada fila `documents` tenga un único valor
`source_id` por su PK, pero no que el `source_id` de una fila `chunks` coincida
con el de su documento padre. Las dos FK de `chunks` solo acreditan que ambos
IDs referencian filas existentes; no conectan entre sí esos dos valores.
`PRAGMA foreign_keys = ON` preserva las FK declaradas, no añade la igualdad
ausente.

### 3.2 Inventario estático de writers

| Writer / ruta | Escritura de documento | Escritura de chunk | Relación document/source |
|---|---|---|---|
| `SQLiteDocumentRepository.save()` (`storage/repositories.py`) | Inserta un `Document` tras comprobar source existente; si el ID ya existe, solo acepta idempotencia exacta y en otro caso lanza conflicto. | — | Protege su propia inserción/idempotencia; no crea una constraint de esquema. |
| `SQLiteChunkRepository.save_chunks()` (`storage/repositories.py`) | — | Inserta chunks tras comprobar que los documentos y sources existen. | Comprueba explícitamente que el `source_id` de cada chunk coincide con el del documento padre. Es un guard en este camino de escritura. |
| `KnowledgeStore.store_ingestion_bundle()` (`storage/knowledge_store.py`) | Llama al repositorio de documentos. | Llama al repositorio de chunks. | Hereda los guards de ambos repositorios en este camino. |
| Ingesta de notebook, rutas SQL directas (`web/routes/notebook.py`, ambos caminos de indexación) | `INSERT OR REPLACE` directo de documents. | `INSERT OR REPLACE` directo de chunks. | Asigna ambos desde la misma variable `source_id`, pero omite la validación cruzada del repositorio y no materializa una constraint persistente. No se eleva la práctica del camino a garantía global. |
| `scripts/sync_fuentes.py` | `INSERT OR REPLACE` directo de documents. | Inserta chunks directos si no existen chunks para el documento. | Usa la misma variable `source_id` para la pareja durante la carga; no declara ni verifica una constraint transversal independiente. No se ejecutó. |
| `scripts/benchmark_gate2_growth.py` | No crea documentos; opera sobre un conjunto base de chunks. | Duplica filas de chunks conservando `document_id` y `source_id` existentes, en la base de benchmark. | No es writer de ingestión/documentos ni prueba una invariante normativa de la instalación. No se ejecutó. |
| Tests y fixtures | SQL/objetos sintéticos en stores de test. | SQL/objetos sintéticos. | Evidencia de fixtures únicamente; no son rutas de escritura productivas. |

No se encontró directorio de migraciones ni archivo SQL de migración del
esquema en la búsqueda estática del repositorio; el DDL encontrado está
centralizado en `sqlite_engine.py`. No se ejecutaron inicializadores ni
migraciones.

Resultado de cobertura: hay un guard explícito en el repositorio normal de
chunks y caminos de bundle que lo usan; existen rutas SQL directas que no
invocan ese guard. Ninguna constraint del DDL puede respaldar la igualdad
independientemente de cuál writer se use. La asignación actual de una misma
variable en los caminos directos es una propiedad de esos fragmentos de código,
no una garantía impuesta por el modelo.

```text
DOCUMENT_SOURCE_CARDINALITY = UNKNOWN
Q1 — garantía estructural global = NO DEMOSTRADA
```

El resultado no afirma que una fila inconsistente exista. Describe la falta de
garantía global en el DDL y la coexistencia de writers con y sin el guard del
repositorio.

### 3.3 Q2 — cardinalidad de la instalación actual

No se consultaron filas ni contenido de `documents` o `chunks`, conforme al
límite explícito de esta pasada. No se infiere cardinalidad real desde el
código, los tests ni las asociaciones source/notebook.

```text
Q2 = NOT_ESTABLISHED
```

## 4. `SectionExpander` y frontera de source

El flujo examinado en `src/study_engine/web/routes/chat.py` y
`src/study_engine/retrieval/expansion.py` es:

```text
seed SearchResult (document_id, source_id)
→ SectionExpander agrupa/consulta por document_id y rango pos_index
→ SELECT devuelve cada chunk.source_id
→ chunks expandidos/contexto con el source_id leído
```

La consulta de expansión filtra por `document_id` y posiciones; no añade
`source_id = seed.source_id`, no recibe una allowlist y no hay post-filter
posterior de source. Se encontró otro `SectionExpander` en
`src/study_engine/context/section_expander.py` con el mismo patrón de consulta
por `document_id`; tampoco compara el source de cada fila devuelta con el de la
semilla. La clasificación aplica a ambos expansores.

Como la igualdad seed/document/chunk no está garantizada por el esquema y no
existe post-filter source-scoped, el análisis estático no demuestra la frontera
de aislamiento. Esto no prueba contaminación en el estado instalado.

```text
EXPANSION_SOURCE_BOUNDARY = UNKNOWN
```

## 5. Tests existentes — solo inspección

No se ejecutaron tests.

| Área | Evidencia inspeccionada | Clasificación |
|---|---|---|
| `tests/context/test_section_expander.py` | Fixtures de un source por documento; ventana, presupuesto, metadata/provenance y citas. No hay un mismo `document_id` con chunks de distinto source ni verificación de allowlist. | `GENERIC_EXPANSION_TEST` |
| `tests/retrieval/test_section_expansion_ceiling.py` | Fixtures de expansión y límite de contexto con source uniforme. | `GENERIC_EXPANSION_TEST` |
| `tests/contract/storage/test_storage_contract.py` | Comprueba FK/referential integrity para source y document; inserta documentos/chunks con sources coincidentes. No ensaya source de chunk distinto del source del padre. | `NO_RELEVANT_TEST` para igualdad document/source |
| `SQLiteChunkRepository.save_chunks()` | Código de guard explícito, pero su presencia estática no sustituye un test de expansión de aislamiento. | No constituye por sí solo `STRUCTURAL_INVARIANT_TEST` ni `EXPANSION_ISOLATION_TEST` |

```text
STRUCTURAL_INVARIANT_TEST = NO_RELEVANT_TEST
EXPANSION_ISOLATION_TEST = NO_RELEVANT_TEST
```

## 6. Matriz final

| Pregunta | Evidencia | Estado |
|---|---|---|
| ¿Existe autoridad normativa de release? | Ninguna aprobación por relación encontrada; C4 está documentado como DRAFT y el plan Gate 2 no altera ACL. | `UNKNOWN` |
| ¿Los 76 roles tienen origen superior? | Hay declaración versionada; 33 roles tienen provenance documental de clasificación, no de autorización; no se encontró origen normativo superior. | `UNKNOWN` como autorización |
| ¿Las 17 installation-only tienen provenance? | No aparecen en registry ni roles; su único soporte es la asociación instalada. | `ORIGIN_UNKNOWN` |
| ¿`documents` tiene `source_id`? | Columna `NOT NULL`, FK independiente a `sources`. | Sí |
| ¿`chunks` tiene `source_id`? | Columna `NOT NULL`, FK independiente a `sources`. | Sí |
| ¿Existe FK `chunk → document`? | `chunks.document_id → documents.id`, `ON DELETE CASCADE`. | Sí |
| ¿Existe constraint de igualdad source? | No; FKs independientes, sin FK compuesta/CHECK. | No |
| ¿Todos los writers preservan la relación? | El repositorio valida; los writers SQL directos no llaman al guard ni imponen constraint. | No demostrado |
| ¿`document_id → source_id` está garantizado globalmente? | El esquema no garantiza la igualdad chunk/document; solo hay guard en una ruta. | `UNKNOWN` (garantía global no demostrada) |
| ¿Existe post-filter en expansión? | No en los dos expansores inspeccionados ni en el flujo citado. | No |
| ¿Existe test de aislamiento? | Tests inspeccionados usan un source por documento; no prueban caso cross-source. | No demostrado |
| ¿La instalación actual mezcla sources bajo un document ID? | No se leyeron filas de `documents`/`chunks`. | `NOT_ESTABLISHED` |

## 7. Dictámenes y siguiente evidencia

```text
AUTHORIZATION_PROVENANCE_STATUS = UNKNOWN
DOCUMENT_SOURCE_CARDINALITY = UNKNOWN
EXPANSION_SOURCE_BOUNDARY = UNKNOWN
CRITERION_1 = BLOCKED
CRITERION_2 = BLOCKED
```

La evidencia que falta para reabrir estos dictámenes es, respectivamente:

1. una decisión/política aplicable, versionada y emitida por autoridad
   designada, con scope, source, propósito y versión para las relaciones que
   se pretenda autorizar; las declaraciones R/U y la ACL persistida no la
   sustituyen;
2. un contrato de igualdad impuesto de forma global por esquema o un inventario
   completo de writers con guard demostrable, si se pretende sostener la
   cardinalidad por camino de escritura;
3. una decisión posterior que establezca qué evidencia de estado instalado
   puede consultarse; Q2 continúa `NOT_ESTABLISHED` en CP081 y no se responde
   por inferencia;
4. para demostrar aislamiento de expansión, una frontera source-scoped
   verificable o evidencia futura específica que la pruebe, sin que CP081
   prescriba ni implemente una reparación.

CP081 no adjudica sources, no cambia ACL, no inspecciona contenido de corpus,
no cambia código ni esquema, no ejecuta tests y no cierra Gate B ni declara
`PRODUCT_COMPLETE`.
