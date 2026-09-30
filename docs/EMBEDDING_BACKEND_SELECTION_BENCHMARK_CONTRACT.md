# Embedding Backend Selection Evaluation — Benchmark Contract

**Estado:** contrato v1 congelado tras revisión adversarial offline; benchmark
NO ejecutado ni autorizado por este documento.
**Ámbito:** evaluación controlada de Qwen3-Embedding-0.6B y
multilingual-E5-small, sin seleccionar automáticamente un ganador.
**Evidencia de partida:** [Embedding Backend Selection Evidence Gate](./EMBEDDING_BACKEND_SELECTION_EVIDENCE.md).

Este contrato separa la evaluación científica de retrieval de la evaluación
operacional. Las dos deben usar el mismo corpus congelado y contratos de
embedding v2 verificables, pero los resultados se reportan en tablas distintas.
La facilidad de instalación, el tamaño del artefacto o una métrica histórica no
son sustitutos de una comparación controlada.

## 1. Límites de autorización

La preparación y validación de este contrato permite fixtures sintéticos,
revisión de metadatos y validación estructural offline. No autoriza:

- instalar dependencias, descargar modelos o acceder a servicios externos;
- cargar modelos, ejecutar inferencia o realizar benchmarks;
- generar embeddings o crear snapshots de índices candidatos;
- leer, copiar, alterar o reemplazar el índice de producción como parte de un
  benchmark;
- cambiar proveedor, contrato del runtime, configuración, threshold o Colab;
- elegir Qwen o E5 como backend activo.

Una ejecución futura requiere autorización propia, dependencias/artefactos
disponibles y aprobación explícita de los límites operacionales marcados como
pendientes en este contrato.

## 2. Candidatos y separación de espacios

Los candidatos son:

1. **Qwen3-Embedding-0.6B**, candidato `1024d`, con instrucciones/prefijos
   determinados por el contrato v2 que se verifique para la implementación.
2. **multilingual-E5-small**, candidato `384d`, con `query: ` y `passage: `
   aplicados exactamente según el contrato v2 verificado.

Cada candidato debe tener su propio contrato v2, revisión inmutable, manifests
completos de modelo/tokenizer y `vector_space_id` calculado según
[`VECTOR_SPACE_IDENTITY.md`](./VECTOR_SPACE_IDENTITY.md). No se permite
comparar directamente scores, vectores ni índices entre espacios. Se construye
un snapshot temporal por candidato a partir del mismo conjunto congelado de
chunks. Ninguna identidad nueva se atribuye a los índices históricos.

Si no puede verificarse cualquiera de esos elementos, se registra el bloqueo;
no se sustituyen IDs de revisión, digests o transformaciones faltantes por
valores inventados ni por tags mutables.

## 3. Corpus de evaluación

### Inclusión y scope

- La fuente de partida permitida es `data/eval/golden_set_v2_400.json`, con sus
  qrels v2.400, por ser el artefacto local que conserva consultas en múltiples
  scopes. Se congela una **nueva versión derivada**; no se modifica v2.400.
- `golden_set_v2_401.json` y sus qrels no se combinan con v2.400. Todas sus
  consultas están asignadas a `NB-SEC-01-C-PTR`, pese a los problemas de scope
  ya registrados en el runbook de Gate 2.
- Para cada consulta y chunk candidato, se respeta exactamente el
  `notebook_scope` y su ACL aprobada. Qrels o chunks fuera de ese scope son
  error fatal de integridad, no ejemplos negativos.
- La unidad de corpus/qrels/resultados es el par `(notebook_id, chunk_id)`.
  Evita colapsar como duplicados chunks iguales asociados a scopes diferentes.
  Dentro del mismo scope, una repetición del mismo chunk cuenta una sola vez.
- El snapshot debe identificar fuentes, chunks, reglas de chunking, texto
  canónico, IDs, scopes, orden y hashes por contenido. Las fuentes completas
  y chunks que no estén autorizados por scope quedan excluidos.
- El snapshot usado para indexar ambos candidatos debe ser el mismo byte por
  byte. No se permite que una ejecución tenga cobertura parcial distinta de la
  otra.

### Control de contaminación

- Los juicios iniciales se congelan antes de ejecutar Qwen o E5.
- Los jueces reciben consulta, scope y evidencia fuente necesaria, no el nombre
  del backend ni el orden de resultados producido por los candidatos.
- Para completar qrels del pool se ejecutan ambos backends bajo aliases ciegos
  A/B y se aplica una regla determinista fijada de antemano:

  ```text
  pool(query) =
      unique_by(notebook_id, chunk_id)(
          top_N(A) ∪ top_N(B) ∪ top_M(lexical_baseline)
      )
  ```

  Los cortes congelados en v1 son `N=100`, `M=100`.
  Se usa lo que cada fuente devuelva si contiene menos que su límite; cero
  resultados de una fuente no es error si se registra el conteo. La unión se
  forma deduplicando primero cada lista por `(notebook_id, chunk_id)` en orden
  de ranking, conservando la primera aparición, y tomando hasta N/M claves
  únicas por fuente. Después se unen las fuentes y se ordena por
  `(notebook_id, chunk_id)` para serializar; se conserva además la lista de
  fuentes/ranuras que aportaron cada candidato. El baseline lexical
  independiente usa corpus/scope idénticos, tie-break por esa misma clave y
  versión/configuración congeladas. Duplicados dentro y entre fuentes colapsan
  a una sola unidad `(notebook_id, chunk_id)` sin perder atribución. Un
  candidato fuera del scope es error fatal de integridad; no se filtra como si
  nunca hubiera aparecido. Los jueces no ven fuente, alias, ranking ni scores;
  los qrels expandidos se congelan y hashean antes de revelar aliases o
  calcular métricas.
- Las consultas qrels, su texto exacto y sus sinónimos de evaluación no se
  agregan como chunks al corpus.
- Las fuentes del corpus se versionan y se hashean antes de generación; toda
  transformación posterior invalida el snapshot y requiere una versión nueva.

## 4. Query set y anotación

La versión congelada debe incluir consultas para cada combinación aplicable de:

- búsqueda conceptual/paráfrasis;
- exact-match y símbolos de código;
- español técnico;
- consultas cortas y largas;
- consultas multi-facet/multi-capítulo;
- categorías curriculares y scopes distintos;
- OOD y controles de abstención.

Cada consulta conserva como mínimo: `query_id` estable, texto exacto, scope(s),
categoría, tags, longitud (caracteres y tokens por tokenizer registrado),
facets requeridas, expectativa de abstención y estado de juicio. Las categorías
son mutuamente excluyentes para las métricas por categoría; los tags/facets
pueden superponerse.

El campo `judgment_status` tiene exactamente estos estados:

| Estado | Significado | Entra a métricas de ranking |
|---|---|---|
| `UNJUDGED` | No hay juicios. No equivale a grado 0. | No |
| `PARTIALLY_JUDGED` | Existe al menos un juicio, pero el pool relevante no está cerrado. | No |
| `EXHAUSTIVELY_JUDGED` | Todos los candidatos de la versión de pool al cutoff están juzgados/adjudicados y el conjunto de relevantes del scope está revisado. | Sí, sujeto a estado de corrida comparable |
| `INCONSISTENT` | Qrels/scopes/juicios contradicen el contrato o entre sí. | No; benchmark inválido hasta nueva versión corregida |

Los qrels iniciales se producen sin ejecutar ningún backend. La expansión pooled
se anota después de obtener candidatos, pero permanece ciega a modelo, orden y
score hasta que el juicio expandido quede adjudicado y congelado:

1. Dos jueces independientes evalúan cada par consulta/chunk dentro del scope.
2. Un tercero adjudica discrepancias; se preservan juicios originales,
   adjudicación y motivo.
3. Relevancia graduada: `0` explícitamente no relevante, `1` evidencia
   marginal/parcial, `2` relevante, `3` altamente relevante. La relevancia debe
   estar sustentada por el contenido del chunk y las facets solicitadas.
4. Un par no juzgado es **unknown**, nunca grado 0 implícito.
5. La versión del benchmark solo queda completa cuando existe un pool de
   candidatos juzgado exhaustivamente hasta el corte evaluado para cada consulta
   positiva. El tamaño del pool, métodos de generación, jueces, adjudicaciones
   y cobertura se registran por query. Si durante la evaluación aparece un
   resultado fuera del pool juzgado, no se lo toma como irrelevante: la corrida
   queda `INCONCLUSIVE`, se amplía el pool con evaluación ciega y se genera una
   nueva versión de qrels antes de puntuar ambos backends.
6. Consultas OOD se evalúan por rechazo/no rechazo y citas o chunks devueltos.
   No se convierten en consultas de ranking con qrels positivos artificiales.

Los 352 casos v2.400 sin qrels positivos se dividen en 60 controles OOD y 292
consultas no-OOD sin juicio positivo. Las 292 consultas no-OOD deben permanecer
`UNJUDGED` hasta adjudicación; no deben tratarse como negativas por defecto.
Los 60 controles OOD se evalúan por su oráculo de abstención, no como consultas
de ranking ni como qrels negativos.
El micro-fixture incluido es sintético y prueba el formato, no completa ni
reemplaza anotación humana del benchmark real.

## 5. Contrato machine-readable para datos congelados

La versión derivada debe tener:

- `schema`: versión explícita del contrato de benchmark;
- `benchmark_id` y `parent_version`;
- hashes SHA-256 de dataset, corpus/chunks, qrels, scopes/ACL, configuración,
  contratos/model artifacts y snapshot de cada índice;
- inventario único de queries, corpus, y qrels;
- estado y cobertura de juicio por query;
- lista de métricas, cortes `k`, método estadístico y semilla;
- estado de aprobación de límites RAM/CPU;
- registro de runtime/hardware y procedimiento de ejecución.

El fixture está en
[`backend_selection/miniature_queries.json`](../tests/fixtures/backend_selection/miniature_queries.json)
y
[`backend_selection/miniature_qrels.json`](../tests/fixtures/backend_selection/miniature_qrels.json).
Sus strings y IDs son ilustrativos; los valores de backend, corpus e índice
reales no deben copiarse desde el fixture.

## 6. Métricas de calidad

Los resultados de ranking se calculan solo para queries con estado
`EXHAUSTIVELY_JUDGED` y qrels
completos para el pool/cutoff; se informa el denominador en cada tabla. El pool
unido se juzga con aliases ciegos y se congela antes de revelar modelos. Un
resultado top-k fuera del pool produce `RUN=INCONCLUSIVE`; no se le asigna grado
0, no se puntúa esa ejecución y no se “parchean” los qrels de la versión
existente. Ampliar el pool exige nuevos juicios ciegos y nueva versión de
benchmark/qrels; se vuelven a evaluar ambos candidatos bajo la versión nueva.

- **Recall@k por query:** resultados con grado adjudicado `>=2` recuperados
  hasta `k` / total de claves
  relevantes distintas `(notebook_id, chunk_id)` adjudicadas en la unión de los
  scopes autorizados de esa query. El denominador se construye por query tras
  unir solo qrels de sus scopes permitidos; nunca se usa el total relevante de
  todo el corpus ni se promedian scopes sin respetar ACL. La agregación reporta
  media macro sobre queries elegibles con al menos un relevante y muestra sus
  denominadores.
- **Precision@k:** resultados con grado `>=2` recuperados hasta `k` / `k`;
  posiciones faltantes
  se consideran no relevantes solo si el pool de evaluación está completo.
- **MRR:** media del recíproco del rango del primer resultado con grado >= 2.
- **nDCG@k:** DCG con gain `2^grade - 1`, normalizado por ranking ideal,
  usando grados adjudicados `0..3`; el ideal se calcula con todos y solo los
  juicios del pool exhaustivo de esa query y scopes autorizados.
- **Facet coverage@k:** facets requeridas que aparecen en al menos un chunk con
  grado >= 2 entre los primeros `k`, dividido por facets requeridas. Informar
  media por query y por facet; no reemplaza Recall/nDCG.
- **Exact-match/symbol retrieval:** Recall@k y MRR de consultas etiquetadas con
  identificadores/símbolos exactos; normalización de símbolos se fija antes de
  ejecutar y se reporta aparte del score semántico.
- **OOD/abstención:** tasa correcta de abstención, tasa de falsas citas,
  resultados no autorizados por scope y distribución de scores/candidatos.
  Umbrales de abstención permanecen congelados durante la comparación; si el
  threshold existente no tiene provenance/contrato válido, se informa como
  no comparable y se reportan curvas, no un threshold transferido entre modelos.

Mostrar resultados globales y desgloses por scope/notebook, categoría, longitud,
facets, consultas positivas y OOD. Para diferencias pareadas se informa un
intervalo bootstrap percentil del 95% sobre queries (10.000 remuestreos,
semilla fija almacenada en el manifest), sin ocultar conteos pequeños ni
combinar categorías para cubrir huecos. No hay score agregado ni
regla que proclame ganador.

## 7. Protocolo científico de retrieval

Para cada backend:

1. Validar contrato, revisión, manifests e igualdad de identidad calculada por
   implementación A/B antes de generar.
2. Crear embeddings para exactamente el mismo corpus, en un almacenamiento
   temporal separado y descartable; fijar batching, truncamiento y fallo
   parcial.
3. Verificar conteos, dimensiones, hashes/IDs, coverage y ausencia de mezcla
   antes de evaluar. Un snapshot incompleto invalida esa ejecución.
4. Ejecutar queries con igual scope/ACL, k, filtro, distancia/similitud y
   política de abstención comparable. Aplicar prefijos y transformaciones
   correspondientes al contrato propio de cada modelo, no imponer el mismo
   preprocesamiento incompatible.
5. Guardar rankings crudos, qrels versionados, métricas por query y logs
   necesarios para reproducir el reporte. Separar runs y artefactos por
   `vector_space_id`.

## 8. Benchmark operacional (independiente)

Calidad y operación se miden y publican en secciones separadas. Medir ambos
candidatos con igual hardware, límites de threads, carga, duración y política
de concurrencia:

- Medir baseline TALOS sin backend de embeddings bajo igual escenario, después
  TALOS+backend A y TALOS+backend B. Informar `RSS_baseline`,
  `RSS_total_backend` y `ΔRSS_backend = RSS_total_backend - RSS_baseline` para
  cold, peak y steady-state, siempre en la misma unidad y método de medición.
  `ΔRSS` es descriptivo; el límite total aplica a `RSS_total_backend`, no a la
  diferencia. No restar procesos medidos bajo cargas distintas.
- RSS máxima del árbol completo de procesos de TALOS: servidor, runtime,
  tokenizer, proveedor, caches y retrieval; informar frío, pico de carga y
  steady-state. Preferir memoria del cgroup del servicio/PSS agregado cuando
  esté disponible; evitar sumar RSS compartida dos veces.
- CPU-segundos por query y por lote, CPU promedio/p95, tiempo de pared y
  throughput; fijar `intra_op`, `inter_op`, BLAS y threads externos.
- Latencia p50/p95 de startup, carga de modelo, primera query, queries warm y
  operación end-to-end; separar tokenización, inferencia y búsqueda cuando sea
  posible.
- Tamaño total de pesos, tokenizer, dependencias y almacenamiento indexado;
  registrar RAM de proceso base sin modelo como baseline.
- Comportamiento offline, necesidad de GPU/Internet, reproducibilidad de
  descarga/artefactos, licencias/restricciones y complejidad de mantenimiento.
- Termalización/throttling observables y errores/cold-start. No habilitar
  concurrencia superior al perfil solicitado para ahorrar CPU.
- Para cualquier claim de capacidad operacional, el host objetivo es el TALOS
  local registrado en la evidencia de selección (Ryzen 5 5600GT, 6C/12T, Linux).
  Colab/GPU puede usarse en un futuro gate autorizado para producir un snapshot
  de embeddings, pero no puede sustentar un claim de RSS/CPU/latencia del runtime
  TALOS local. Registrar host, kernel, governor/frecuencia, hardware y
  disponibilidad de acelerador para cada medida.

### Presupuestos aún pendientes

```text
RAM_LIMIT:
  status: PENDING_CONFIRMATION
  provisional_value: 2 GiB RSS máximo
  scope: subsistema TALOS completo

CPU_LIMIT:
  status: UNDEFINED
  value: null
```

El valor 2 GiB se conserva como hipótesis provisional, no como requisito
ratificado ni como resultado medido. No declarar cumplimiento de “bajo consumo
de CPU” hasta que exista límite numérico acordado (por ejemplo, CPU-segundos por
query y/o CPU promedio bajo carga definida). Reportar mediciones crudas aun
cuando no haya límite aprobado; no convertirlas a PASS/FAIL ni escoger ganador
por ese criterio.

## 9. Criterios de validez del experimento

Una ejecución solo es comparable si:

- ambas versiones de corpus, queries y qrels están congeladas y hasheadas;
- qrels y scopes son consistentes y adjudicados; pares sin juicio no participan
  como negativos;
- el corpus candidato es idéntico para ambos backends y ningún vector/query
  cruza espacios;
- ambos manifests y contratos v2 son verificables y el snapshot tiene cobertura
  completa;
- las métricas reportan el mismo denominador, política de ranking, ACL y corte;
- las capturas de RSS/CPU/latencia incluyen la configuración y hardware exactos;
- se conserva el reporte de errores, exclusiones y muestras insuficientes;
- no hay cambios a datos de producción ni resultados incompletos presentados
  como ganadores.

Si falla un criterio, resultado `INCONCLUSIVE`; no reparar los artefactos
históricos in-place ni relajar criterios después de ver resultados.

El resultado agregado de selección es una matriz/vectores de evidencia, no un
score único. Estados válidos incluyen `TRADEOFF` (calidad y coste favorecen
candidatos distintos), `INCONCLUSIVE` (evidencia, cobertura o presupuesto no
permite afirmar), y `COMPARABLE_NO_CLEAR_DIFFERENCE`. Ninguno activa un backend
automáticamente; la elección requiere decisión humana explícita.

## 10. Estado actual

| Elemento | Estado |
|---|---|
| Evidencia read-only de candidatos | Recopilada; ver reporte de evidencia |
| Contrato de evaluación | v1 congelado tras revisión adversarial offline |
| Pooling v1 | `top_100(A) ∪ top_100(B) ∪ top_100(lexical)`; clave/orden deterministas, fuentes preservadas |
| Micro-fixtures de queries/qrels | Sintéticos; estructura, scopes, unknown/graded/OOD validados |
| Fixtures adversariales | 15 casos declarados; validación offline PASS |
| Qrels reales adjudicados suficientes | Pendiente; 292 consultas no-OOD sin juicio positivo siguen `UNJUDGED` |
| Revisión de scope de v2.401 | Pendiente; no incorporada |
| Manifests/revisiones v2 de modelos candidatos | Pendientes de evidencia verificable |
| RAM máxima de 2 GiB | Pendiente de confirmación; valor provisional solamente |
| Límite numérico de CPU | No definido |
| Instalación, generación, inferencia y benchmark | No autorizados por este contrato |
| Ganador / backend activo | Ninguno; decisión no tomada |

El siguiente gate de ejecución deberá autorizar separadamente la adjudicación
de qrels, la obtención de artefactos/dependencias y la generación de snapshots
temporales. Este contrato no autoriza esos pasos.

## 11. Revisión adversarial v1 — resultado offline

El validator
[`validate_backend_selection_contract_fixtures.py`](../scripts/validate_backend_selection_contract_fixtures.py)
comprueba fixtures sintéticos para los casos enumerados en
[`adversarial_cases.json`](../tests/fixtures/backend_selection/adversarial_cases.json).
La prueba específica es
[`test_backend_selection_contract.py`](../tests/unit/diagnostics/test_backend_selection_contract.py).
Se verificó:

| Invariante adversarial | Resultado |
|---|---|
| Query sin positivos | Se excluye de ranking; no se inventan negativos |
| OOD | Se evalúa por abstención/falsas citas, separado de ranking |
| Query multi-scope | Recall usa solo pares relevantes en scopes autorizados |
| Candidato fuera del pool | `RUN=INCONCLUSIVE`; grado sigue unknown |
| Duplicados A/B/lexical | Se deduplican por scope+chunk y preservan fuentes |
| Juicio parcial o ausente | Se excluye de métricas |
| Scope/qrels/resultados no autorizados | Benchmark/corrida inválidos; no se convierten en negativos |
| Ranking más corto que `k` | Precision usa denominador `k`, bajo pool exhaustivo |
| Recall | Denominador por query sobre relevantes de scopes autorizados |
| RSS | Se informan baseline, total y delta bajo escenario equivalente |
| CPU sin threshold ratificado | Solo medición; `UNASSESSED`, sin PASS/FAIL |
| Qrels inconsistentes | `INVALID_BENCHMARK` |

Comandos validados:

```bash
.venv/bin/python scripts/validate_backend_selection_contract_fixtures.py
.venv/bin/python -m pytest tests/unit/diagnostics/test_backend_selection_contract.py -q
```

Ambos pasan. Esta revisión congela las reglas metodológicas v1; no congela una
selección de modelo ni convierte los límites RAM/CPU pendientes en criterios
aprobados. No autoriza benchmark, adjudicación real de qrels, instalación,
descargas ni cambios de runtime/datos.
