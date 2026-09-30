# TALOS Embedding Backend Selection — Full-Pipeline Experiment Design

**Estado:** `APPROVED_METHODOLOGICAL_DESIGN`<br>
**Ejecución, descargas, instalaciones, embeddings, retrieval y mediciones:** no autorizados<br>
**Benchmark Contract v1:** congelado e intacto<br>
**Blind Pool Generation Gate:** `PENDING`; no ejecutar bajo este borrador

## Aprobación metodológica

El usuario aprobó explícitamente este diseño como marco para comparar dos
pipelines completos: Qwen índice+consulta y E5 índice+consulta, considerando
calidad de recuperación, costo local, reproducibilidad y mantenimiento. Esta
aprobación no selecciona un backend ni una configuración concreta, y no
autoriza descargas, instalaciones, generación de embeddings, construcción de
índices, retrieval, pool generation, mediciones, benchmark ni cambios de
producción.

La aprobación queda registrada en
[`full_pipeline_design_approval.json`](../reports/backend_selection_adjudication_v1/full_pipeline_design_approval.json),
que fija el SHA-256 del diseño aprobado. Los contratos candidatos y las
decisiones operacionales siguen pendientes.

## 1. Propósito

Definir una evaluación de los dos sistemas completos que TALOS podría operar:

```text
Qwen index + Qwen query encoder + TALOS retrieval
E5 index   + E5 query encoder   + TALOS retrieval
```

La pregunta no es cuál modelo gana en abstracto, sino cuál ofrece la mejor
calidad de recuperación y cobertura de las necesidades de TALOS con un costo
local, tamaño, mantenimiento y reproducibilidad aceptables. La calidad y el
costo se informan por separado; no se presupone un ganador ni un score
compuesto.

Este documento es un diseño propuesto, no una autorización. No altera el
contrato v1, el addendum metodológico aprobado, los qrels, el corpus, los
índices existentes ni los gates registrados.

## 2. Preguntas experimentales

### E1 — Adecuación de Qwen como sistema completo

Evaluar retrieval usando un índice Qwen existente **solo como candidato
histórico**, acompañado por el encoder Qwen de consultas que se haya
identificado como compatible. Separadamente medir el costo local de ejecutar
el query encoder y el retrieval en el host TALOS.

No se certifica el índice histórico por su nombre de modelo o dimensión. Su
identidad, origen, corpus, chunking y contrato de embeddings deben verificarse
contra los criterios de la sección 4.

### E2 — Viabilidad de E5 como sistema completo

Sobre el mismo snapshot aprobado de fuentes, chunks y scopes, preparar un
índice E5 experimental, aislado y no productivo, usando un contrato E5
congelado. Evaluar retrieval con el encoder E5 de consultas correspondiente y
medir el costo local de ese sistema.

Crear ese índice requiere generar embeddings de corpus y escribir artefactos
experimentales. Es trabajo nuevo respecto de la mera candidate generation:
no queda autorizado por el addendum de blind pool ni por este diseño.

## 3. Diseño común

Ambos sistemas deben recibir:

- el mismo corpus lógico, con igualdad de contenido canónico, IDs de chunks,
  notebooks, scopes y ACL;
- la misma batería versionada de queries, texto exacto y scope;
- el mismo código de retrieval y filtros, salvo los adaptadores inevitables
  del formato/espacio vectorial;
- el mismo `top_k`, política de abstención evaluable y reglas de desempate;
- los mismos qrels exhaustivos para cada query/cutoff que entre en métricas.

Los contratos de query/documento son específicos de cada modelo. No se fuerza
el mismo pooling, instrucciones, prefijos ni truncamiento entre modelos. Cada
índice solo se compara con queries codificadas bajo el contrato compatible de
ese mismo espacio vectorial. Nunca se comparan directamente vectores o scores
Qwen contra E5.

La comparación de calidad requiere qrels adjudicados, completos y congelados
antes de calcular métricas. `UNJUDGED` y `UNKNOWN` no se convierten en grado 0.
Los controles OOD se miden como abstención/citas y no como queries de ranking
con negativos inventados.

## 4. Elegibilidad del índice Qwen histórico

Antes de tratar el índice existente como candidato del E1, recopilar evidencia
read-only suficiente para establecer:

1. artefacto/revisión de modelo y tokenizer, hashes o una explicación explícita
   de lo que no puede recuperarse;
2. dimensiones, pooling, normalización, instrucciones/prefijos, truncamiento,
   tokenización y cualquier transformación aplicada a query y passage;
3. procedencia del índice, versión de generador, fechas/ejecución y relación
   entre el contrato de ingestión y el encoder de consulta disponible;
4. corpus, chunking, claves `(notebook_id, chunk_id)`, cobertura y scopes/ACL
   representados en ese índice;
5. integridad verificable del artefacto existente sin escribirlo ni migrarlo.

El actual [`embedding_contract.json`](../data/colab/embedding_contract.json)
es una declaración histórica descriptiva: declara Qwen 1024d, `max_length=512`,
mean pooling, normalización L2 y prefijos vacíos; su revisión no es un pin
inmutable. La documentación primaria consultada para un snapshot público
específico muestra last-token pooling y ejemplos con instrucción, pero eso no
demuestra qué produjo el índice de TALOS. Esta discrepancia debe resolverse con
provenance del artefacto, no suponiendo que la implementación pública actual
equivale a la histórica.

Resultados de elegibilidad:

- `HISTORICAL_PAIR_VERIFIED`: existe evidencia suficiente de compatibilidad
  índice-query y del corpus; el índice puede usarse como candidato de E1, aún
  sin certificación productiva.
- `HISTORICAL_PAIR_PARTIALLY_VERIFIED`: se conocen límites; cualquier claim de
  comparación afectado debe declararse no comparable y no puntuarse como si
  fuera una pareja verificada.
- `HISTORICAL_PAIR_UNVERIFIABLE`: no se compara el índice con queries de una
  configuración inferida. Requeriría una decisión metodológica/versionada
  separada para reconstruir también Qwen sobre el snapshot común o excluir el
  E1; no se decide ni ejecuta automáticamente.

Si el índice Qwen existente no comparte la misma cobertura de chunks/scope que
el snapshot común, las queries/chunks ausentes no se tratan como irrelevantes.
Se detiene la comparación afectada; no se repara ni completa el índice
silenciosamente.

## 5. Construcción de E5 aislado

La preparación futura de E5 debe:

- congelar primero el snapshot común de chunks, texto, IDs, scopes y ACL;
- fijar revisión inmutable y hashes del modelo/tokenizer, licencia, formato
  ONNX/runtime, dimensiones y contrato completo de query/passage;
- generar embeddings de todos y solo los chunks del snapshot mediante un
  proceso reproducible y aprobado;
- escribir únicamente a un directorio experimental nuevo, nunca al índice
  productivo, `vector_store.db`, `knowledge_store.db` ni rutas de runtime;
- verificar conteos, dimensiones, hashes de contenido/IDs, cobertura y
  compatibilidad antes de retrieval;
- registrar fallo parcial como corrida inválida; no rellenar resultados con
  otro backend ni presentar un índice parcial como equivalente.

La dimensión esperada de 384d de multilingual-E5-small no basta para probar
identidad del artefacto o compatibilidad. El ONNX/tokenizer locales con hashes
observados tienen origen/revisión pendientes.

## 6. Qrels y candidate discovery ciego

La auditoría de fuentes iniciales dio `SOURCE_INSUFFICIENT`. La forma prevista
de obtener juicios útiles sigue siendo una unión ciega de candidatos Qwen, E5
y lexical, adjudicada por humanos antes de la evaluación. El addendum aprobado
resuelve metodológicamente la excepción de secuencia para candidate discovery,
pero **no** autoriza ejecutar ni define por sí solo la construcción completa
de los índices de ambos sistemas.

Secuencia propuesta:

```text
Design review
    ↓
freeze corpus/query/scope + resolve Qwen historical-pair eligibility
    ↓
freeze complete Qwen and E5 pipeline contracts
    ↓
separate operational authorization for required index/query candidate work
    ↓
blinded union of candidates from complete compatible pairs + lexical source
    ↓
human adjudication; qrels frozen and hashed
    ↓
separate benchmark authorization
    ↓
quality evaluation of Qwen pair and E5 pair against the same qrels
    ↓
separate, controlled local operational measurements
```

For pool construction, use the already frozen v1 cutoffs and scope/ACL rules
unless a new versioned methodological decision explicitly changes them.
Judges must not see backend, score, rank, source, or provenance. The pool is
candidate-discovery material only; it is not a quality result or evidence that
one backend is better. The lexical source helps coverage but is not an
additional model candidate for backend selection unless separately specified.

Any source whose full pipeline cannot be executed with a compatible index and
query contract cannot silently contribute candidates under its backend label.
The treatment of that condition must be fixed before opening the blind pool.

## 7. Quality evaluation

After qrels are adjudicated, exhaustively judged for the evaluated pool/cutoff,
frozen, and hashed, evaluate each complete pair on the same versioned inputs.
Apply the existing v1 metric definitions and scope/ACL rules. Report
denominators and eligibility per query; do not score incomplete qrels as
negative labels.

Report the results separately by:

- global eligible queries and scopes/notebooks;
- Spanish technical, conceptual/paraphrase, exact-match/symbol, multi-facet,
  query length, and other pre-registered categories;
- positive ranking queries versus OOD abstention controls.

If any evaluated system returns a result outside the judged pool at a scored
cutoff, mark the run inconclusive, expand the blinded judgment pool, freeze new
qrels/version, and rerun both systems. Do not calculate a metric for that run
by treating the unseen candidate as irrelevant.

## 8. Operational evaluation

Quality and operational cost are different result sets. Local PC measurements
are made on the TALOS host under separately approved, fixed hardware/runtime
conditions. A Colab index-generation run does not measure local query cost.

For each backend, distinguish:

1. **Index creation cost:** embedding generation time/resources in the
   environment that builds the index; report separately for Colab or local
   host, as applicable.
2. **Index footprint:** model/tokenizer/dependency sizes and serialized index
   size, with index corpus and format identified.
3. **Local query cost:** startup/model-load, first query, warm query p50/p95,
   query encoder CPU-seconds, end-to-end retrieval latency, peak/steady RSS,
   CPU use, errors and thermal observations on the TALOS PC.
4. **Maintenance/reproducibility:** pinned artifacts, rebuild procedure,
   update cost, offline requirements, dependency/license constraints, and
   ability to reproduce the index/query pair.

Use baseline TALOS resource use and common measurement methods. Record
concurrency, intra/inter-op threads, numerical precision, batch and input token
length distribution. Do not assume 32K input length from model capacity; measure
and declare the actual contract-limited inputs. Do not convert third-party
latency/memory claims into TALOS measurements.

No operational limits have been approved yet. This section does not approve
CPU/GPU mode, thread counts, RAM/RSS, timeout, storage, temperature, downloads,
dependency installation or measurement execution.

## 9. Decision framework — no automatic winner

Present the evidence as a quality-versus-cost trade-off, not an opaque scalar:

| Dimension | Qwen full pair | E5 full pair |
|---|---|---|
| Retrieval quality under identical frozen qrels | Measure | Measure |
| Facet/category performance and abstention | Measure | Measure |
| Local query RSS/CPU/latency | Measure | Measure |
| Index footprint/build/update cost | Measure | Measure |
| Pair identity/reproducibility confidence | Establish | Establish |
| Maintenance, offline behavior and operational constraints | Document | Document |

Adoption requires a later explicit decision against TALOS requirements. A
larger model is not assumed better; a smaller model is not assumed sufficient.
If Qwen's measured cost is acceptable and quality is suitable, retaining it is
a valid outcome. If neither backend satisfies requirements, report that without
forcing a winner.

## 10. Current status and explicitly prohibited actions

| Activity | Current status |
|---|---|
| Methodological design in this document | Approved; recorded separately |
| Candidate technical contracts | Proposed; pending technical freeze |
| Read-only identity/source inspection already recorded | Permitted; no new broad audit implied |
| Download/install models or dependencies | Not authorized |
| Re-embed corpus or build E5/Qwen index | Not authorized |
| Query inference, retrieval or blind-pool generation | Not authorized |
| Human adjudication of newly generated pool | Not started |
| Quality/operational metrics or model comparison | Not authorized |
| Modify production corpus, qrels, indexes or runtime | Prohibited |
| Select/promote backend | Not authorized |

The candidate contracts are frozen as compatibility specifications; read-only
evidence subsequently verified E5's published model/tokenizer file identity
and the ONNX graph's FLOAT32 types. Qwen identity/runtime remain blocked; E5
runtime and reproducible padding evidence remain open. Each execution phase
retains its own explicit authorization. The prior blind-pool authorization gate
remains `PENDING`; its earlier addendum approval and this full-pipeline design
approval do not authorize the broader experiment.
