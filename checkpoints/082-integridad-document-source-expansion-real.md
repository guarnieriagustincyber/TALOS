# CP082 — integridad actual document/source y frontera de expansión

## 1. Alcance y estado preservado

Esta inspección responde solo si la base de la instalación consultada contiene
actualmente chunks cuyo `source_id` difiere del `documents.source_id` padre, y
si esos registros serían alcanzables por la expansión estática por
`document_id` descrita en CP081.

No se modificó código, base, ACL, asociaciones, roles, registry, catálogo,
perfiles, retrieval, tests ni fixtures. No se inició TALOS/FastAPI ni se
ejecutaron retrieval, proveedores, pruebas o benchmarks. No se ejecutaron
seeders, reparaciones ni migraciones. No se leyó `content`, título, autor,
bibliografía, corpus, ni embeddings.

Se preservan:

```text
RELEASE_SCOPE = 5
FADENA_STD_RELEASE_SCOPE = INCLUDED
CRITERION_1 = BLOCKED
CRITERION_2 = BLOCKED
AUTHORIZATION_PROVENANCE_STATUS = UNKNOWN
DOCUMENT_SOURCE_CARDINALITY = UNKNOWN
```

## 2. Identidad de base y continuidad

La base examinada es la ruta canónica local referenciada por CP077 y el código
de inicialización:

| Campo | Valor observado |
|---|---|
| `DB_PATH` | `/media/agustin/Laboratorio/study-engie/data/web_state/knowledge_store.db` |
| `DB_FILE_HASH` (SHA-256) | `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` |
| `DB_FILE_SIZE` | `303194112` bytes |
| `DB_MTIME` | `2026-09-25T16:58:14.078984875-03:00` |
| `SQLite_VERSION` | `3.45.1` |
| `PRAGMA user_version` | `6` |
| `PRAGMA schema_version` (cookie SQLite) | `42` |
| `SQLiteStorageEngine.SCHEMA_VERSION` (código) | `6` |
| Journal mode | `wal` |
| WAL sidecar | existe, `0` bytes en la inspección |
| SHM sidecar | existe |

CP077 identifica esta misma ruta como la base de datos leída entonces en
`mode=ro`; CP078–080 remiten a ese cotejo y CP081 no leyó sus filas de
`documents`/`chunks`. Los checkpoints previos no registran hash, tamaño ni
mtime que permitan comparar los bytes históricos. Por ello:

```text
DB_IDENTITY = SAME_CANONICAL_PATH
HISTORICAL_BYTE_IDENTITY = NOT_VERIFIABLE (fingerprint previo no registrado)
```

No se sustituyó la ruta por otra base. Los resultados que siguen describen
factualmente el archivo actual con esa ruta; no afirman identidad byte a byte
con el estado histórico de CP077.

## 3. Método de solo lectura y escrituras

Se abrió SQLite con URI `mode=ro`, se estableció
`PRAGMA query_only = ON` y se verificó `query_only = 1` antes y después de las
consultas. Se consultaron únicamente esquema, conteos, IDs, `source_id`,
`pos_index` y comprobaciones de referencias. No se ejecutó DML ni DDL.

El hash, tamaño y mtime del archivo principal fueron los mismos antes y después
de las consultas:

```text
DB_FILE_HASH_AFTER = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1
DB_FILE_SIZE_AFTER = 303194112
DB_MTIME_AFTER = 2026-09-25T16:58:14.078984875-03:00
PRAGMA_QUERY_ONLY = 1
```

No se realizó ninguna escritura lógica a las tablas ni al archivo principal.
La conexión fue de solo lectura en una base WAL; no se tomó un fingerprint
anterior del sidecar `-shm`, por lo que no se hace una afirmación independiente
de invariancia byte a byte de ese sidecar.

## 4. Conteos actuales

Las consultas no seleccionaron columnas de contenido.

| Métrica | Valor |
|---|---:|
| `documents_total` | 115 |
| `chunks_total` | 105705 |
| `documents_with_chunks` | 112 |
| `documents_without_chunks` | 3 |
| `DOCUMENT_IDS_WITH_MULTIPLE_CHUNK_SOURCES` | 0 |
| `MAX_DISTINCT_CHUNK_SOURCES_PER_DOCUMENT` | 1 |
| `DOCUMENT_IDS_WITH_CHUNK_SOURCE_MISMATCH` | 0 |

Los 112 `document_id` presentes en `chunks` tienen exactamente un valor
distinto de `chunks.source_id` por documento; en todos los casos coincide con
el único `documents.source_id` del padre. Los otros tres documentos no tienen
chunks y, por tanto, no contribuyen a la cardinalidad observada de chunks.

## 5. Comparación efectiva de source

Se compararon exhaustivamente todos los chunks con su documento padre:

```text
chunks.document_id
→ documents.id
→ documents.source_id
```

contra `chunks.source_id`. Resultado:

```text
CURRENT_DATA_CROSS_SOURCE_MIXING = NOT_OBSERVED
CURRENT_DOCUMENT_TO_CHUNK_SOURCE_CARDINALITY = OBSERVED_SINGLETON
Q2 = OBSERVED_CONSISTENT
```

No hubo grupos de discrepancia que enumerar:

```text
MISMATCH_GROUPS = []
MULTI_SOURCE_DOCUMENT_GROUPS = []
```

Por consiguiente, no existen `document_id` afectados ni pares de source A/B,
conteos o rangos de posiciones que detallar. No se inspeccionó contenido para
intentar explicar un caso inexistente.

## 6. Integridad referencial

`PRAGMA foreign_key_check` se ejecutó como consulta de solo lectura. Reportó
una violación en una relación ajena a documents/chunks:

```text
["notebook_sources", rowid 47, "sources", FK 0]
```

No se leyó el source ID de esa fila ni se expandió la investigación a las
asociaciones; no es necesario para esta directiva y no se usa para adjudicar
ACL.

Comprobaciones específicas de las tres relaciones solicitadas:

| Relación | Huérfanos observados | Resultado |
|---|---:|---|
| `chunks.document_id → documents.id` | 0 | `PASS` |
| `chunks.source_id → sources.source_id` | 0 | `PASS` |
| `documents.source_id → sources.source_id` | 0 | `PASS` |

```text
FK_INTEGRITY = FAIL (base completa: una violación en notebook_sources)
TARGET_DOCUMENT_CHUNK_SOURCE_FKS = PASS
```

El fallo global se informa sin ocultarlo; no contradice el resultado de las
tres FK relevantes para document/source.

## 7. Relación con `SectionExpander`

CP081 estableció estáticamente que el expansor consulta chunks por
`document_id`/rango de posición y no añade filtro `source_id = seed.source_id`
ni post-filter source-scoped. Se inspeccionaron aquí los datos, no se ejecutó
`SectionExpander`.

El resultado exhaustivo actual es cero documentos con varios chunk sources y
cero diferencias frente al source del documento. Por tanto no hay en esta
base un caso factual que la consulta estática del expansor pueda atravesar:

```text
EXPANSION_CROSS_SOURCE_PATH = NOT_OBSERVED
EXPANSION_SOURCE_BOUNDARY = UNKNOWN
```

No se eleva a `CONTRADICTORY`: esa conclusión requeriría un mismatch actual
alcanzable por la consulta. Tampoco se eleva a `SUPPORTED`: no observar mezcla
en el snapshot no demuestra una barrera en el expansor ni garantiza estados
futuros.

```text
NO_OBSERVED_MIXING != STRUCTURAL_GUARANTEE
```

El DDL continúa sin imponer `chunks.source_id = documents.source_id`; los
writers SQL directos identificados por CP081 siguen sin proporcionar una
garantía global de esquema. Por tanto:

```text
DOCUMENT_SOURCE_CARDINALITY = UNKNOWN
```

## 8. Relación con RELEASE_SCOPE

Como no se encontró ninguna inconsistencia, no se hizo cotejo de source IDs
contra los cinco scopes ni se consultaron asociaciones para esa finalidad.
Esta inspección no modifica ni interpreta `R`, `U` o `P` y no atribuye
pertenencia curricular a ninguna fuente.

## 9. Dictámenes finales, límites y no-acciones

```text
Q2 = OBSERVED_CONSISTENT
CURRENT_DATA_CROSS_SOURCE_MIXING = NOT_OBSERVED
CURRENT_DOCUMENT_TO_CHUNK_SOURCE_CARDINALITY = OBSERVED_SINGLETON
DOCUMENT_SOURCE_CARDINALITY = UNKNOWN
EXPANSION_CROSS_SOURCE_PATH = NOT_OBSERVED
EXPANSION_SOURCE_BOUNDARY = UNKNOWN
FK_INTEGRITY = FAIL (una violación fuera de documents/chunks)

CRITERION_1 = BLOCKED
CRITERION_2 = BLOCKED
AUTHORIZATION_PROVENANCE_STATUS = UNKNOWN
```

Este resultado es una observación exhaustiva del archivo identificado en §2,
no una prueba de garantía estructural, de estado de otras instalaciones ni de
ausencia futura de discrepancias. La identidad byte a byte histórica no puede
verificarse porque CP077–081 no registraron fingerprint anterior.

CP082 no repara la violación FK reportada ni modifica filas, constraints,
asociaciones, ACL, roles o artefactos. No agrega filtros, no adjudica acceso,
no cierra Gate B y no declara `PRODUCT_COMPLETE`.
