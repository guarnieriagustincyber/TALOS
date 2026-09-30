# Backend Selection — Real Dataset / Qrels Adjudication Gate

**Estado:** adjudicación humana ciega autorizada; juicios pendientes.<br>
**Decisión de backend:** ninguna.<br>
**Ejecución de retrieval/embeddings:** no realizada.<br>
**Producción e índices:** sin cambios.

## Autorización vigente

El usuario autorizó únicamente la adjudicación humana ciega de los dos paquetes
existentes. La autorización no cambia su contenido ni sus hashes; queda
registrada por separado en
[`human_adjudication_authorization.json`](../reports/backend_selection_adjudication_v1/human_adjudication_authorization.json).

**Permitido:** entregar a cada juez únicamente su paquete (`reviewer_a.json` o
`reviewer_b.json`), conservar independencia, juzgar dentro de los scopes
indicados y registrar disposiciones de intención/scope. Si se proporciona un
par consulta/chunk mediante un procedimiento ciego aprobado, pueden asignar
`0/1/2/3` o `UNKNOWN` con evidencia y justificación. `UNKNOWN` y pares sin
juicio nunca se convierten automáticamente en grado 0. La comparación, el
acuerdo o la discrepancia se procesan solo después de que ambos jueces hayan
devuelto sus revisiones.

**Limitación operativa detectada:** los paquetes actuales contienen cero pares
consulta/chunk y cero contenido de chunks. Por sí solos permiten revisar texto
de consulta y scope, pero no producir juicios de relevancia graduada. No se debe
rellenar `pair_judgments` ni declarar cobertura exhaustiva sin una vía ciega
autorizada que entregue evidencia de chunks. La autorización vigente no crea
esa vía ni autoriza generación automática de candidatos.

**No autorizado:** entregar el mapa restringido a los jueces; revelar IDs,
qrels heredados, categoría/oráculo previo o backend de origen; ejecutar
retrieval para generar candidatos, embeddings, descargar/instalar modelos,
crear índices, ejecutar el benchmark o cambiar producción. Si un juez detecta
problemas de scope, corpus, candidatos o paquete, se detiene esa adjudicación;
no se edita sobre la marcha ni se congela el resultado. Se requiere corregir la
fuente y emitir una nueva versión con hashes.

La autorización no equivale a adjudicación realizada: no se han recibido
decisiones humanas, no existe consenso calculado y no hay qrels congelados.
La adjudicación de pares está bloqueada por falta de candidatos/chunks en los
paquetes actuales.
Estados siguientes posibles: `HUMAN_ADJUDICATION_IN_PROGRESS`,
`QRELS_ADJUDICATED` y `QRELS_FROZEN`; ninguno se presume por esta autorización.

El bloqueo ahora se rastrea como **`ADJUDICATION_BLOCKED_NO_CANDIDATE_PAIRS`**.
Antes de producir un paquete nuevo debe cerrarse el
[Initial Qrels Candidate Source Gate](./INITIAL_QRELS_CANDIDATE_SOURCE_GATE.md).
Ese gate no modifica el contrato congelado ni autoriza generación de candidatos.

## Alcance de esta etapa

Preparar el dataset real para adjudicación independiente, sin reutilizar los
qrels históricos como ground truth y sin mostrar a los jueces sus grados,
categorías, tags, oráculos o IDs originales. El paquete no completa los juicios
humanos ni certifica el benchmark.

## Fuentes congeladas para el paquete

| Entrada | Versión | SHA-256 |
|---|---|---|
| [`golden_set_v2_400.json`](../data/eval/golden_set_v2_400.json) | v2.400 | `7ac3c707a973aa7dbc2e79c48c14a6208ac6f72bcba3d184433c2f2bc6b337c1` |
| [`golden_set_v2_400.qrels.json`](../data/eval/qrels/golden_set_v2_400.qrels.json) | v2.400 | `68af7033fcd4e607b830245901774d2daac610d909763cb0b999b024b1ed7abc` |
| Snapshot lógico de fuentes/chunks scoped | SQLite `knowledge_store.db` actual | `7831a012bf437623eb8c510f0c6b780202dd45ee37307e2a8f69d1519d4959fa` |

El fingerprint del corpus cubre las filas de fuentes y chunks visibles por cada
scope en `notebook_sources` al momento de generar el paquete. No reconstruye ACL
históricas ni sustituye una copia inmutable del corpus; cualquier cambio de
contenido o membresía requiere un fingerprint y paquete nuevos.

## Cobertura observada

- **400** consultas en seis scopes.
- **165** referencias qrel heredadas en **48** consultas; todas existen bajo al
  menos uno de los scopes actuales autorizados inspeccionados.
- **352** consultas sin qrels positivos: **60 OOD** y **292 no-OOD sin juicio
  positivo**. Los 292 permanecen `UNJUDGED`; ausencia de qrel no equivale a
  irrelevancia. Los 60 OOD se juzgan mediante su oráculo de abstención.
- Distribución de consultas por scope:

| Scope | Consultas | Chunks scoped en snapshot |
|---|---:|---:|
| `NB-SEC-01-C-PTR` | 330 | 105.179 |
| `NB-CYBERSECURITY-V1` | 10 | 36.847 |
| `fadena-so2` | 10 | 12.371 |
| `fadena-lenguajes` | 20 | 15.459 |
| `fadena-teleco` | 20 | 27.475 |
| `fadena-std` | 10 | 46.530 |

Se corrigió en el contrato el conteo impreciso que antes describía los 352
casos sin qrels como no-OOD: la división comprobada es 60 OOD y 292 no-OOD.

## Reutilización de Gate 2

Se conservaron como evidencia los artefactos existentes:

- [`gate2_v2400_coverage_inventory_2026-09-28.json`](../reports/gate2_v2400_coverage_inventory_2026-09-28.json)
- [`gate2_v2400_query_adjudication_queue_2026-09-28.json`](../reports/gate2_v2400_query_adjudication_queue_2026-09-28.json)
- [`gate2_v2400_explicit_decision_register_2026-09-28.json`](../reports/gate2_v2400_explicit_decision_register_2026-09-28.json)

El inventario explícito reconoce **1** qrel `VALID`, **2** `PARTIAL` y **13**
`INVALID`; otros **149** siguen pendientes de adjudicación semántica. Hay cuatro
decisiones explícitas sobre consultas (una OOD aprobada y tres bloqueos
semánticos). Esos registros se preservan como antecedente, pero no satisfacen
por sí solos el protocolo nuevo de dos jueces independientes más adjudicación
de discrepancias. Por ello no se importan como qrels adjudicados del benchmark
de backend.

## Paquetes generados

El generador
[`build_backend_selection_adjudication_packets.py`](../scripts/build_backend_selection_adjudication_packets.py)
produjo el directorio local
`reports/backend_selection_adjudication_v1/`:

- `reviewer_a.json`: 400 casos, aliases opacos y orden independiente.
- `reviewer_b.json`: 400 casos, aliases y orden distintos.
- `restricted_reconciliation_map.json`: mapeo de aliases a IDs de origen;
  **restringido, no distribuir a los jueces**.
- `evidence_manifest.json`: hashes de entradas y paquetes, fingerprint del
  corpus, conteos y limitaciones.

Los paquetes de jueces solo incluyen texto de consulta, scope autorizado y
campos vacíos de juicio. No incluyen qrels previos, query IDs, categorías, tags
ni expectativas anteriores. Cada caso empieza como `UNJUDGED`; una lista vacía
de pares no expresa grado 0. El generador usa SQLite `mode=ro`, rechaza
referencias qrel faltantes/fuera del scope actual y no sobrescribe un paquete
existente.

## Resultado del gate

**`READY_FOR_HUMAN_ADJUDICATION`**, no `BENCHMARK_READY`. Hace falta completar
las revisiones humanas independientes de ambos paquetes y resolver discrepancias
antes de congelar los juicios iniciales. Luego se podrá generar el pool ciego
de candidatos y adjudicarlo exhaustivamente; solo entonces serán elegibles las
métricas de ranking.

No se instalaron dependencias de modelos, no se ejecutaron backends y no se
generaron embeddings. El umbral provisional de RAM (2 GiB) y el umbral de CPU
indefinido no bloquean la adjudicación; deben resolverse antes del benchmark
operacional.
