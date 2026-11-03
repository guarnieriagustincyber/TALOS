# TALOS Embedding Candidate Contracts — Technical Proposal

**Estado:** `COMPATIBILITY_SPEC_FROZEN_ARTIFACT_BINDING_BLOCKED`<br>
**Diseño metodológico full-pipeline:** `APPROVED_METHODOLOGICAL_DESIGN`<br>
**Ejecución, descargas, instalaciones, conversión, inferencia y construcción de índices:** no autorizadas

Las transformaciones y configuraciones compatibles de los candidatos primarios
se congelan en
[`candidate_contracts_freeze.json`](../reports/backend_selection_adjudication_v1/candidate_contracts_freeze.json).
El binding completo de artefactos, `vector_space_id`, pin exacto de runtime y
reproducibilidad operacional continúan bloqueados donde se indica abajo. No se
autoriza producir vectores.

## 1. Regla de comparación

La unidad experimental es una pareja completa:

```text
document encoder + query encoder + tokenizer + transformaciones
    + corpus/chunk snapshot + index artifact + retrieval configuration
```

Qwen solo consulta un índice Qwen cuya identidad compatible se haya
demostrado; E5 solo consulta un índice E5 construido con el mismo contrato.
Cada par tendrá su propio `vector_space_id`. No mezclar, migrar ni comparar
directamente scores entre espacios. Corpus, IDs, scopes/ACL, query set, filtro,
cutoff y criterio de desempate deben coincidir.

La especificación de compatibilidad ya está congelada. Esto no implica que
artefactos, runtime, procedencia o `vector_space_id` estén verificados; los
campos `UNRESOLVED` bloquean la autorización de ejecución.

## 2. Recomendación técnica para el experimento primario

La recomendación es llevar **una configuración primaria por familia**, sin
buscar hiperparámetros después de ver resultados:

| Sistema | Candidato primario | Construcción de índice | Consulta en PC | Estado |
|---|---|---|---|---|
| Qwen | Qwen3-Embedding-0.6B, commit fijado, last-token pooling, L2, query instruction del snapshot, passages sin instrucción, límite TALOS 512, cómputo FP32 | Construir índice Qwen nuevo desde snapshot común salvo que el histórico supere el gate de identidad | Mismos pesos/tokenizer/input/pooling y FP32; CPU en PC | Compatibilidad congelada; artefactos/runtime todavía no vinculados |
| E5 | multilingual-E5-small, commit fijado, `query: `/`passage: `, mean con attention mask, L2, límite 512, FP32 | Construir índice E5 separado usando el ONNX publicado exacto del commit, si supera los prerrequisitos restantes | Mismo ONNX/tokenizer y ONNX Runtime CPU en PC | Identidad de archivos Hub LFS y tipo FP32 del grafo verificados estáticamente; runtime instalado y run reproducible de padding siguen pendientes |

**Por qué este par:** son las configuraciones públicas de retrieval más
directamente sustentadas por sus model cards; conservan la configuración
histórica declarada de 512 tokens sin confundirla con la capacidad máxima de
Qwen; y usan un único contrato completo por sistema. No se compara Qwen index
con E5 query, no se usan nombres/dimensiones como sustituto de identidad y no
se cuantiza solo el encoder local.

Para Qwen, la instrucción del snapshot consultado dice “web search”. La
recomendación primaria es usarla tal cual como línea base reproducible, no
porque sea necesariamente óptima para TALOS. Una instrucción de dominio TALOS
sería una configuración experimental adicional que debe aprobarse/versionarse
antes de candidate generation; no se elige iterativamente mirando qrels o
métricas.

**Política numérica congelada para el primer candidato:** FP32 en inferencia.
Qwen: cargar checkpoint y ejecutar en FP32 tanto en Colab como en CPU local.
E5: aceptar solo una exportación ONNX FP32 y ejecutar ese mismo archivo con
CPUExecutionProvider en Colab y PC. Es una especificación, no evidencia de
viabilidad o cumplimiento de límites. Cambiar precisión, cuantizar o usar
artefactos distintos crea otro candidato y exige nuevo índice/manifest.

Para evitar pooling, prompts o longitud implícitos en Sentence Transformers,
Qwen usa una implementación explícita sobre Transformers: pasar el prompt de
query fijado; tokenizar query/passages con `max_length=512`, truncation side
right y special tokens contados; seleccionar el último token atendido; y
aplicar L2. La generación en Colab y consulta en PC compartirán el adaptador
versionado. El pin de dependencias y su validación siguen pendientes.

Los valores 512, prompts e instrucciones son decisiones candidatas para una
primera comparación controlada, no declaraciones de óptimo. Si la longitud
real de chunks exige otra opción, cambiarla antes de freeze y construir ambos
lados de la pareja con esa versión.

## 3. Qwen3-Embedding-0.6B

### Evidencia pública y límites

La revisión fijada consultada de
[`Qwen/Qwen3-Embedding-0.6B`](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/tree/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3)
publica 1024 dimensiones máximas y configura Sentence Transformers con
last-token pooling más normalización. Su `config_sentence_transformers.json`
declara el prompt `query`:

```text
Instruct: Given a web search query, retrieve relevant passages that answer the query
Query:
```

El ejemplo oficial muestra longitud de 8192, mientras que la ficha anuncia
capacidad de 32K. Ninguno de esos valores determina el límite de entrada del
experimento TALOS. La revisión es una fuente candidata pinneable, pero no
prueba que el índice histórico local se generara con ese snapshot.

El contrato histórico local
[`embedding_contract.json`](../data/colab/embedding_contract.json) declara
Qwen 1024d, `max_length=512`, mean pooling, L2 y entradas sin prefijos. La
revisión declarada allí es texto descriptivo, no pin inmutable. Por tanto, la
configuración histórica y la configuración pública fijada son dos identidades
distintas hasta que haya evidencia de equivalencia.

Además, el provider
[`SentenceTransformerEmbeddingProvider`](../src/study_engine/retrieval/embedding.py)
actual limpia query/passage y llama `model.encode(...,
normalize_embeddings=True)`, pero no pasa `prompt_name="query"` ni configura
`max_seq_length` o mean pooling explícitamente. Si ese provider fuera el usado
en una corrida histórica, el pooling/longitud procederían de los módulos y
defaults cargados por Sentence Transformers, no de la declaración JSON por sí
sola. El código disponible no prueba qué versión produjo el índice Qwen local.

### Especificación congelada Qwen-R (reconstrucción reproducible)

| Campo | Propuesta candidata | Estado/nota |
|---|---|---|
| Modelo | `Qwen/Qwen3-Embedding-0.6B` | `FROZEN_SPEC`; revisión `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` |
| Tokenizer | Tokenizer del mismo repositorio y revisión | `FROZEN_SPEC`; hash/manifest pendiente de adquisición autorizada |
| Dimensiones | 1024 | `FROZEN_SPEC`, documentado por hidden size/config pública |
| Pooling | Último token atendido (`last-attended-token-v1`) | `FROZEN_SPEC`; implementación explícita pendiente de validación |
| Normalización | L2 | `FROZEN_SPEC` |
| Query instruction | Exacta: `Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery:` seguida por el texto de query normalizado | `FROZEN_SPEC`; una adaptación TALOS sería otro candidato |
| Passage instruction | Vacía | `FROZEN_SPEC` |
| Longitud máxima | 512 tokens totales, incluidos special tokens; truncamiento right | `FROZEN_SPEC`; decisión TALOS, no límite oficial del modelo |
| Dtype/precisión de inferencia | FP32 en Colab y PC; cargar checkpoint con cast explícito a float32 | `FROZEN_SPEC`; runtime CPU y costo no medidos |
| Runtime | Transformers `AutoTokenizer` + `AutoModel`, pooling last-token/input formatting explícitos, sin defaults de Sentence Transformers | `FROZEN_RUNTIME_FAMILY`; versiones exactas y si basta `trust_remote_code=False` siguen `BLOCKING` |
| Identidad índice histórico | No atribuida | Solo elegible si se recupera provenance compatible con la pareja query-documento |

La instrucción oficial `web search` es una línea base documental, no una
afirmación de que sea la mejor instrucción para cuadernos técnicos TALOS.
Probar una instrucción TALOS distinta crea una configuración candidata
distinta: debe quedar elegida y congelada antes de qrels/métricas, sin
seleccionarla mirando resultados.

### Evidencia adicional del pipeline histórico

El notebook
[`talos_reindex_colab.ipynb`](../data/colab/talos_reindex_colab.ipynb) confirma
que se fijó `MAX_SEQ_LENGTH = 512` y que la carga pidió `torch.float16` en ese
notebook. Sin embargo:

- carga el nombre mutable del modelo sin un commit de Hub fijado;
- instala con `pip install -U` paquetes sin lock ni hashes;
- llama `model.encode(texts, normalize_embeddings=True)` para passages, sin
  seleccionar explícitamente el prompt de query (esperable para passages) ni
  implementar explícitamente el `mean` declarado en el `_meta`;
- escribe `pooling: "mean"` en el contrato serializado aunque la operación
  observada del notebook delega pooling al módulo/default de
  Sentence Transformers;
- llama `trust_remote_code=True`, y el JSON de salida no incluye la revisión
  efectiva, hashes de artefactos ni versiones de librerías.

Por ello, el notebook es evidencia de intención/flujo, no evidencia suficiente
para reconstruir el contrato exacto del índice materializado. La diferencia
entre pooling declarado y ejecutado no se resuelve suponiendo que el módulo
subyacente siguió el JSON.

### Regla para el índice Qwen existente

1. Intentar identificar read-only el artefacto y el contrato efectivos que
   generaron el índice, incluido pooling/instrucción/truncamiento/tokenizer,
   corpus/chunking y cobertura de scope; contrastar también la implementación
   de provider invocada y los parámetros realmente fijados.
2. Si se demuestra que corresponde exactamente al candidato Qwen-R, puede
   entrar como índice histórico sin modificarlo.
3. Si demuestra otro contrato, solo puede compararse con su encoder de consulta
   homólogo y como un candidato Qwen-H separado; no se mezcla con Qwen-R.
4. Si la pareja no puede identificarse, marcar
   `HISTORICAL_PAIR_UNVERIFIABLE`. No ejecutar queries codificadas con una
   configuración inferida. Para la comparación primaria, la recomendación es
   asumir este resultado en ausencia de manifiestos/logs del run y crear luego
   un índice nuevo Qwen-R desde el snapshot común, con artefactos fijados y
   aislados. Esa reconstrucción requiere alcance y autorización explícitos.

En consecuencia, no asumir que la descripción previa “Qwen 0.6B/1024d”
identifica por sí sola el índice actual.

## 4. multilingual-E5-small

### Evidencia oficial y local

El [model card oficial de `intfloat/multilingual-e5-small`](https://huggingface.co/intfloat/multilingual-e5-small)
documenta 384 dimensiones, prefijos `query: ` y `passage: ` para retrieval,
truncamiento a 512 tokens, mean pooling con attention mask y normalización L2.
El API del repositorio reportó la revisión
`614241f622f53c4eeff9890bdc4f31cfecc418b3`; esta revisión es una referencia
candidata para un manifest futuro, no una verificación de los artefactos ONNX
locales.

En TALOS hay un modelo ONNX y tokenizer locales con hashes ya registrados en
el gate operacional. La consulta read-only a la
[API pública del repositorio fijado](https://huggingface.co/api/models/intfloat/multilingual-e5-small/tree/614241f622f53c4eeff9890bdc4f31cfecc418b3?recursive=true&expand=false)
lista `onnx/model.onnx` y `onnx/tokenizer.json` con LFS SHA-256 y tamaños
idénticos a los bytes locales. Los sidecars de caché locales también registran
ese commit y ETags coincidentes. Por tanto, la identidad de los dos archivos
publicados queda verificada contra la revisión candidata; la receta/toolchain
histórica del ONNX no está documentada, pero no es necesaria para identificar
y consumir el archivo ONNX publicado exacto. Sí sería necesaria para
reconstruir el export. La implementación
[`LocalONNXEmbeddingProvider`](../src/study_engine/retrieval/embedding.py)
actual aplica prefijos, truncamiento 512, mean pooling con `attention_mask`,
L2 y provider CPU. Esto es evidencia del código y su ruta local; la API pública
confirma la identidad de los archivos, pero no demuestra por sí sola que
runtime y adaptador cumplan todos los parámetros congelados.
La lectura estática del `tokenizer.json` declara `<pad>` id `1`; la
configuración ONNX publicada en esa revisión declara `pad_token_id: 0`, y el
`tokenizer_config.json` publica `pad_token: "<pad>"` con longitud 512. El
provider actual configura
`enable_padding(pad_id=0, pad_token="<pad>")`. La prueba aislada registrada en
el gate de prerrequisitos encontró salida idéntica para ambos IDs al aplicar
attention-mask mean pooling y L2 con estos artefactos locales; esto resuelve
parcialmente el comportamiento de padding, no su reproducibilidad ni la
configuración normativa del candidato.

Un reproductor aislado con fixtures sintéticos está preparado en
[`verify_e5_padding_compatibility.py`](../scripts/verify_e5_padding_compatibility.py).
No se ha ejecutado en esta etapa: el resultado de padding sigue siendo una
observación reportada hasta generar y conservar un manifest bajo el runtime
autorizado.

### Especificación congelada E5-R (ONNX publicado identificado; ejecución bloqueada)

| Campo | Propuesta candidata | Estado/nota |
|---|---|---|
| Modelo lógico | `intfloat/multilingual-e5-small` | `FROZEN_SPEC`; revisión candidata fijada `614241f622f53c4eeff9890bdc4f31cfecc418b3` |
| Dimensiones | 384 | `FROZEN_SPEC`, coherente con model card |
| Query input | Literal `query: ` + texto normalizado | `FROZEN_SPEC` |
| Passage input | Literal `passage: ` + texto normalizado | `FROZEN_SPEC` |
| Tokenizer | Snapshot upstream `intfloat/multilingual-e5-small` en commit fijado; copia exacta del snapshot para Colab/PC | `FROZEN_SPEC`; ruta, tamaño y LFS SHA-256 en la API del commit coinciden con el archivo local |
| Truncamiento | 512 tokens totales después de prefijo y special tokens; lado right | `FROZEN_SPEC`; verificar tokenizer/export concretos |
| Pooling | `mean-attention-mask-v1` | `FROZEN_SPEC` |
| Normalización | L2 después del pooling | `FROZEN_SPEC` |
| Precisión/export | ONNX FP32; mismo artefacto en Colab CPU y PC CPU | `FROZEN_SPEC`; la identidad del ONNX publicado está verificada y su Protobuf declara FLOAT para pesos flotantes/salida y para el único Cast; no se midieron diferencias numéricas de kernels |
| Runtime | ONNX Runtime CPU, `intra_op_num_threads=4`, `inter_op_num_threads=1` | Configuración del provider congelada como candidato; exact dependency pins/host acceptance siguen bloqueados |
| Identidad del ONNX | Archivo publicado `onnx/model.onnx` del commit fijado | `UPSTREAM_FILE_IDENTITY_VERIFIED` por coincidencia de ruta, tamaño y LFS SHA-256; receta histórica de export no publicada |
| Tipo del grafo | Pesos/constantes flotantes y salida | `STATIC_FP32_VERIFIED` por inspección protobuf del artefacto con SHA esperado; sin crear sesión ONNX Runtime |

La regla de binding para E5 queda congelada:

- el artefacto candidato debe derivarse del commit upstream fijado y tener
  manifest/hashes completos;
- la coincidencia de la API del repositorio fijado, ruta, tamaño y LFS
  SHA-256 cierra la identidad de los archivos ONNX/tokenizer locales respecto
  del artefacto publicado;
- la receta/toolchain del export solo es bloqueante si se decide reconstruir
  el ONNX; el uso del ONNX publicado no debe describirse como un export
  reproducido localmente;
- si se usa el archivo publicado exacto, no se atribuye una reconstrucción
  local del export; cualquier conversión alternativa requerirá un candidato y
  provenance propios.

No intercambiar pesos ONNX ni tokenizer con otra revisión. La instalación y cualquier descarga quedan sin autorizar. No se realizará una
conversión local mientras el artefacto publicado exacto sea el candidato.

**Selección congelada:** ONNX CPU en ambos lados, misma exportación FP32 y
tokenizer; no usar GPU para un lado de la pareja. La identidad del archivo
publicado y el tipo FP32 del grafo están verificados; el runtime reproducible
y la validación aislada del padding siguen bloqueantes.

## 5. Arquitectura Colab → PC

Para cada sistema, la futura corrida de indexación en Colab debe consumir un
snapshot exportado e inmutable de chunks (ID, notebook/scope, texto canónico y
hash), con el modelo/tokenizer fijados. Debe escribir un artefacto de índice
nuevo, independiente del `vector_store.db` productivo, junto a un manifest que
incluya al menos:

- IDs/orden y hashes del snapshot de corpus/chunks;
- model/tokenizer revisions, manifests SHA-256, contrato v2 y
  `vector_space_id`;
- implementación de carga, pooling, normalización, max length y precisión;
- versiones de dependencias, dispositivo y configuración del proceso;
- conteos esperados/reales, filas omitidas/fallidas y checksum del índice;
- revisión del index builder y formato de almacenamiento.

La PC necesita únicamente el artefacto de consulta local (Qwen completo o E5
ONNX/tokenizer), el manifest coincidente y acceso de solo lectura al índice
experimental exportado. El retrieval debe filtrar scope/ACL antes de exponer
candidatos. Una discrepancia de `vector_space_id`, manifest o corpus invalida
la pareja. Transferir el índice no transfiere autorización ni lo convierte en
índice activo.

Al medir consulta local, registrar cold-load, primera query y queries warm,
RSS del árbol completo y memoria disponible, CPU-segundos, wall latency,
longitud en tokens, precisión/hilos, errores y observación térmica. Las
mediciones de construcción en Colab se reportan aparte; no se usan como
estimación de costo en la PC.

## 6. Bloqueo crítico del reindexador existente

No usar el script
[`reindex_embeddings.py`](../scripts/reindex_embeddings.py) para construir el
índice experimental ni para modificar producción. La inspección estática
muestra que:

- sus constantes de metadatos declaran `MODEL_ID = "Qwen3-Embedding-4B"` y
  `DIMENSIONS = 2560`;
- el worker instancia [`LocalONNXEmbeddingProvider`](../src/study_engine/retrieval/embedding.py),
  que carga `multilingual-e5-small`, emite 384 dimensiones y aplica el
  contrato E5;
- sus rutas por defecto incluyen el `vector_store.db` activo y el flujo final
  reemplaza `chunk_embeddings`.

Hay, por tanto, una discrepancia identidad/dimensión y un riesgo de escritura
productiva si se ejecuta con defaults. No se ejecutó. Hasta que exista una
herramienta separada, aislada y validada contra un contrato congelado, el
reindexado de ambos índices queda bloqueado. Este documento no modifica el
script ni autoriza corregirlo como efecto colateral.

## 7. Binding y verificación pendientes

La especificación de compatibilidad está congelada. El binding de artefactos y
la verificación operacional siguen pendientes; no se puede calcular un
`vector_space_id` ni habilitar ejecución hasta cerrar:

- archivos exactos de modelo/tokenizer, manifests SHA-256 completos y
  provenance entre artefactos locales y revisiones upstream;
- lock de runtime y versiones exactas de código/model loading; confirmar que
  Qwen carga con `trust_remote_code=False`;
- compatibilidad del tokenizer con los artefactos, incluyendo IDs de padding,
  special-token accounting y truncamiento;
- implementación del pooling congelado, su máscara/índice de token y orden de
  normalización, mediante revisión/test aislado;
- provider/runtime, Python, dispositivo y precisión como provenance; el FP32
  especificado aún no está verificado en los artefactos ni en el host;
- compatibilidad verificada query-index con fixtures de entrada/salida no
  productivos cuando la ejecución sea autorizada;
- dataset/chunk snapshot, index builder/version y retrieval metric/tie-break.

Aplicar el esquema de
[`VECTOR_SPACE_IDENTITY.md`](./VECTOR_SPACE_IDENTITY.md). No completar digests
con nombres de modelo o tags mutables. Un artefacto cuantizado/conversionado
debe tener identidad de artefacto propia.

## 8. Recomendación de avance

Orden propuesto, todo aún sin ejecución:

1. Recuperar read-only la procedencia del índice Qwen y clasificarlo
   `VERIFIED`, `PARTIALLY_VERIFIED` o `UNVERIFIABLE`.
2. Adoptar para diseño la estrategia recomendada: índice Qwen nuevo si el
   histórico no queda verificado; no reutilizarlo por defecto.
3. Crear un environment lock aislado de Qwen y verificar el runtime explícito,
   incluida la política de código remoto, sin ejecutar el modelo.
4. Confirmar si los artefactos E5 locales corresponden al commit fijado;
   mantener su hash como artefacto local no atribuido hasta probar la relación.
5. Diseñar/validar estáticamente una ruta de construcción de índices
   exclusivamente experimental que no pueda escribir las bases productivas.
6. Congelar manifests y `vector_space_id` para cada sistema.
7. Actualizar las autorizaciones de candidate pool, adjudicación, benchmark y
   medición local para cubrir expresamente las fases necesarias. Ninguna
   autorización anterior se amplía por inferencia.

**Estado resultante:** especificación de compatibilidad de ambos candidatos
congelada; identidad del índice Qwen histórico y procedencia ONNX E5 sin
cerrar; runtime de Qwen ausente y entorno E5 actual no coincide con el lock;
`vector_space_id` y prerrequisitos operacionales no verificados; generación de
candidatos, construcción de índices, mediciones y benchmark continúan no
autorizados.
