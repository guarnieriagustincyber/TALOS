# Blind Pool Generation Authorization Gate

**Estado:** `PENDING`<br>
**Autorización de ejecución:** no concedida<br>
**Propósito:** decidir si se autoriza una fase aislada de candidate generation
para construir el pool de adjudicación humana, sin evaluar ni comparar modelos.<br>
**Contrato de benchmark v1:** congelado y no modificado por este documento.

**Addendum metodológico relacionado:** [aprobado como decisión metodológica](./EMBEDDING_BACKEND_SELECTION_BENCHMARK_CONTRACT_V1_ADDENDUM_BLIND_POOL.md).
**Prerrequisitos operacionales:** [propuestas concretas listas para decisión, aún no aprobadas](./BLIND_POOL_OPERATIONAL_PRECONDITIONS_GATE.md).
**Diseño de experimento full-pipeline:** [aprobado metodológicamente](./EMBEDDING_BACKEND_SELECTION_FULL_PIPELINE_EXPERIMENT_DESIGN.md).
**Especificación técnica:** [congelada para preparación; artifact binding y runtime bloqueados](./EMBEDDING_BACKEND_CANDIDATE_CONTRACTS_PROPOSAL.md).
**Preparación del blind pool:** [autorizada solo documental/read-only](./BLIND_POOL_PREPARATION_GATE.md).

> **Aclaración de alcance:** este gate y su addendum anteceden al diseño
> full-pipeline. La aprobación metodológica del diseño no resuelve los
> contratos técnicos candidatos ni amplía la autorización. El addendum
> anterior solo resuelve la
> excepción de candidate discovery ciego; no autoriza ni especifica generar
> embeddings del corpus, construir un índice E5 experimental, verificar la
> pareja histórica índice-query de Qwen, medir costo local o ejecutar el
> benchmark completo. No solicitar ni conceder autorización de ejecución bajo
> este gate acotado hasta publicar una versión que cubra expresamente los
> contratos candidatos, la construcción necesaria de índices y sus
> prerrequisitos. El estado permanece `PENDING`.

## Decisión solicitada

¿Se autoriza la fase descrita aquí, con sus límites y prerequisitos, para
generar exclusivamente los candidatos necesarios para que jueces ciegos creen
los qrels? La aprobación del addendum resuelve la metodología, pero
**no autoriza la ejecución de esta fase**.

Estados posibles:

- `PENDING`: falta autorización explícita de ejecución.
- `AUTHORIZED`: se registró una autorización explícita que cubre alcance,
  recursos, artefactos y condiciones de parada.
- `REJECTED`: la fase no se ejecutará bajo esta propuesta.
- `BLOCKED_PROTOCOL_CONFLICT`: no se puede ejecutar sin una decisión explícita
  sobre compatibilidad/adenda del contrato congelado.

## Separación de fases

```text
SOURCE_INSUFFICIENT
        ↓
Blind Pool Generation Authorization Gate   ← estado actual: PENDING
        ↓ solo con autorización y prerequisitos satisfechos
Qwen candidates + E5 candidates + lexical candidates
        ↓ union/dedup, sin puntuación comparativa
Pool ciego congelado y hasheado
        ↓
Adjudicación humana independiente
        ↓
Qrels adjudicados y congelados
        ↓ autorización posterior y gate separado
Benchmark comparativo Qwen vs E5
```

La ejecución de esta fase no producirá un resultado de calidad, operación o
selección de backend. Una tabla de retrieval, un ranking inspeccionable o una
métrica no forman parte del entregable.

## Alcance propuesto si se autoriza

1. Fijar el conjunto de consultas y scopes a partir de v2.400 y del snapshot
   elegible. v2.401 queda excluido por sus problemas de scope ya documentados.
2. Para cada consulta y scope autorizado, generar como máximo:
   - top-100 de Qwen (`A`);
   - top-100 de E5 (`B`);
   - top-100 del baseline lexical congelado.
3. Aplicar el pooling v1 sin modificarlo:

   ```text
   pool(query) =
       unique_by(notebook_id, chunk_id)(
           top_100(A) ∪ top_100(B) ∪ top_100(lexical_baseline)
       )
   ```

   Respetar el orden de ranking para deduplicar cada lista, conservar hasta
   100 claves únicas por fuente, unir y serializar en orden determinista de
   `(notebook_id, chunk_id)`. Registrar todas las fuentes/ranuras que aportaron
   cada clave en provenance restringida. Si una fuente devuelve menos de 100,
   usar los resultados disponibles y registrar el conteo. No se completan
   resultados faltantes con otra fuente.
4. Tratar cualquier candidato fuera de scope/ACL como fallo fatal de
   integridad; no filtrarlo silenciosamente ni juzgarlo.
5. Generar para cada juez un paquete independiente con consulta, scope, clave
   opaca del caso, candidatos y contenido necesario para revisar relevancia.
   Cambiar orden y aliases entre jueces; fijar y guardar las semillas de
   aleatorización en provenance restringida para que la serialización sea
   reproducible. Ocultar backend, fuente, rank, score, identidades reales de
   chunks y resultados individuales. Incluir solo el contenido/evidencia
   necesaria para juzgar y no metadata de fuente que revele innecesariamente
   procedencia. Los jueces trabajan independientemente y no comparten
   decisiones.
6. Conservar la correspondencia de aliases, semillas, procedencia por
   backend/rank y registros crudos únicamente en un artefacto restringido; no
   incluirla en los paquetes distribuidos.
7. Congelar y hashear pool, corpus/scope, configuración, semillas y paquetes antes de
   cualquier adjudicación. Verificar de forma read-only los conteos, ACL,
   duplicados, IDs, hashes y aislamiento entre entregables.
8. Detenerse tras producir y verificar los paquetes. No calcular métricas ni
   presentar rankings comparativos; no ejecutar el benchmark.

## Límites explícitos

| Actividad | Estado bajo este gate |
|---|---|
| Qwen candidate generation, solo top-100 para pool ciego | No autorizada hasta aprobar |
| E5 candidate generation, solo top-100 para pool ciego | No autorizada hasta aprobar |
| Baseline lexical candidate generation, solo top-100 | No autorizada hasta aprobar |
| Unión, deduplicación, aliases ciegos y paquetes de jueces | No autorizados hasta aprobar |
| Adjudicación humana de los candidatos resultantes | Requiere que existan los paquetes; conserva independencia |
| Métricas de calidad, latencia, RSS/CPU comparativa o evaluación operacional | Prohibidas en esta fase |
| Selección de backend/ganador o conclusión Qwen vs E5 | Prohibida en esta fase |
| Modificar el contrato congelado v1 | Fuera de alcance |
| Cambiar corpus, ACL, qrels históricos o índices productivos | Prohibido |
| Promover/activar un embedding o modificar runtime de producción | Prohibido |

Los resultados intermedios de candidate generation no deben exponerse a jueces
ni a quien adjudique como rankings separados. No se permite ajustar queries,
scopes, thresholds o configuración mirando métricas de calidad: esta fase no
calcula métricas.

## Conflicto de secuencia con el contrato v1

El contrato congelado dice que los **juicios iniciales se congelan antes de
ejecutar Qwen o E5**, y después se anota la expansión pooled. No hay una fuente
independiente suficiente para esos juicios iniciales: resultado documentado
`SOURCE_INSUFFICIENT`.

Por tanto, ejecutar Qwen/E5 para poblar los primeros pares requiere la
excepción de secuencia aprobada en el addendum. Aunque no se calcularan métricas
y el pool fuera ciego, no se debe afirmar que ese procedimiento cumple sin
cambios el orden original. Para considerar habilitada la ejecución se requieren
ambas condiciones:

1. **Cumplida:** aprobación explícita del addendum metodológico versionado.
2. **Pendiente:** autorización operacional explícita del usuario para candidate
   generation únicamente con el alcance y límites de este gate, una vez
   registrados los prerequisitos.

El addendum metodológico fue aprobado y hasheado por separado; el conflicto de
secuencia queda resuelto únicamente en el alcance específico allí descrito. El
gate de ejecución sigue `PENDING`: esa aprobación no cambia su estado a
`AUTHORIZED` ni autoriza descargas, instalaciones, retrieval, candidate
generation o creación del pool.

## Prerequisitos que deben registrarse antes de ejecutar

El registro detallado está en el
[Blind Pool Operational Preconditions Gate](./BLIND_POOL_OPERATIONAL_PRECONDITIONS_GATE.md),
actualmente `PROPOSALS_READY_PENDING_APPROVAL`. Las cifras están propuestas,
no acordadas:

- Hardware/host de ejecución y modo CPU/GPU.
- Artefactos exactos de Qwen, E5 y tokenizer: revisión, hashes y procedencia.
- Dependencias/entorno reproducible y si requiere descarga o instalación.
- Snapshot idéntico del corpus, chunks, scopes/ACL y configuración; hashes
  verificados antes y después.
- Directorio aislado de entrada/salida. Sin escrituras a bases, índices o
  reportes productivos.
- Límites operacionales aprobados para RSS, CPU, temperatura, concurrencia y
  duración, con supervisión y condiciones de parada.
- Semillas/configuración determinista donde aplique y orden/tie-break fijados.
- Tie-break determinista de resultados por clave `(notebook_id, chunk_id)` para
  puntuaciones iguales; registrar precisión/configuración de score y cualquier
  no determinismo de runtime como limitación, sin usarlo para ordenar por
  backend.
- Procedimiento de aliases ciegos, control de acceso a provenance y entrega
  separada a jueces.
- Política de conservación/eliminación de rankings crudos y artefactos
  temporales.

La interpretación anterior de 2 GiB como límite máximo RSS fue una hipótesis
no aprobada. El registro operacional actual propone tratar 2 GiB como mínimo de
`MemAvailable` y, por separado, limitar el árbol experimental a 4 GiB RSS,
junto con CPU-only y cuota de 1 CPU lógica; todos esos valores siguen
`PROPOSED_NOT_APPROVED`. Ver el
[Operational Preconditions Gate](./BLIND_POOL_OPERATIONAL_PRECONDITIONS_GATE.md).
No se declara que Qwen/E5 quepan en esos límites.

La evidencia actual vincula los artefactos E5 locales al archivo upstream del
commit fijado por ruta, tamaño y LFS SHA-256, y una inspección Protobuf
estática confirma tipos FLOAT en los tensores flotantes/salida. El entorno
instalado sigue sin coincidir con el lock candidato y falta un run manifest
reproducible del padding. Qwen no tiene artefactos locales ni runtime
Transformers/PyTorch confirmados. La adquisición/instalación, si fuese
necesaria, debe estar expresamente cubierta por autorización operacional
posterior; no está autorizada aquí.

## Registro de autorización

| Campo | Valor |
|---|---|
| Estado actual | `PENDING` |
| Addendum metodológico | `APPROVED_METHODOLOGICAL_ADDENDUM` |
| Conflicto de secuencia v1 | Resuelto por el addendum, solo para el alcance descrito |
| Prerrequisitos operacionales | `PROPOSALS_READY_PENDING_APPROVAL` |
| Autorización de Qwen/E5/lexical candidate generation | No |
| Autorización de descargas/instalaciones | No |
| Requisitos hardware/recursos aprobados | No |
| Benchmark/métricas autorizados | No |
| Producción/índices modificables | No |

La transición a `AUTHORIZED` requiere una confirmación explícita que se refiera
a una versión revisada del alcance, posterior a la revisión del diseño
full-pipeline y al registro de los prerrequisitos. Este gate, en su versión
actual, no cubre construcción/reconstrucción de índices ni medición de costo
local. Una futura autorización para generar el pool tampoco autorizará
benchmark, métricas ni activación.
