# Blind Pool Operational Preconditions Gate

**Estado:** `PROPOSALS_READY_PENDING_APPROVAL`<br>
**Tipo de trabajo:** definición documental sobre evidencia ya disponible<br>
**Ejecución, descargas, instalaciones y mediciones nuevas:** no realizadas<br>
**Blind Pool Generation Gate:** permanece `PENDING`<br>
**Addendum metodológico:** aprobado; no es autorización operacional.<br>
**Diseño full-pipeline:** aprobado metodológicamente; no hay autorización de ejecución.<br>
**Especificación de compatibilidad:** congelada para preparación; bindings/prerrequisitos bloqueados.<br>
**Preparación de blind pool:** [documental/read-only autorizada](./BLIND_POOL_PREPARATION_GATE.md).

## Objetivo y límite

Este gate convierte los prerrequisitos operacionales del
[Blind Pool Generation Authorization Gate](./BLIND_POOL_GENERATION_AUTHORIZATION_GATE.md)
en un registro verificable. Separa:

- hechos previamente observados;
- valores/configuración propuestos para aprobación;
- datos faltantes que bloquean el cierre.

No instala herramientas, no accede a Internet, no carga modelos, no mide
recursos, no genera candidatos ni cambia archivos de datos o producción. La
existencia de esta especificación **no** cambia ningún gate a `AUTHORIZED`.

Este registro operacional se redactó para candidate generation/pool ciego.
No debe usarse como aprobación de construir embeddings o índices completos.
El diseño aprobado de la pareja índice+consulta Qwen y E5 está en el
[Full-Pipeline Experiment Design](./EMBEDDING_BACKEND_SELECTION_FULL_PIPELINE_EXPERIMENT_DESIGN.md).
Las transformaciones compatibles están congeladas en
[`candidate_contracts_freeze.json`](../reports/backend_selection_adjudication_v1/candidate_contracts_freeze.json);
los bindings de artefacto, runtime y límites operacionales siguen bloqueados.
Las autorizaciones para construir índices, medir costo local y ejecutar el
benchmark requieren gates versionados separados.

## 1. Host y modo de ejecución

| Campo | Evidencia disponible | Propuesta operacional | Estado |
|---|---|---|---|
| Host | La evidencia local anterior registra Linux | Usar únicamente el host TALOS documentado; confirmar identidad antes de una eventual ejecución | `OBSERVED_HOST_CLASS / CONFIRM_BEFORE_RUN` |
| CPU | AMD Ryzen 5 5600GT with Radeon Graphics; 6 cores físicos / 12 lógicos, dato observado durante investigación previa | Modo/hilos permitidos pendientes; si se autoriza, fijar un número de hilos por implementación y registrar límites efectivos | `OBSERVED / THREAD_POLICY_PENDING` |
| GPU | CPU con gráficos Radeon integrados; no hay evidencia registrada de acelerador/runtime GPU utilizable para estos modelos | Disponibilidad y modo permitido pendientes; no instalar drivers/runtime GPU sin autorización | `UNVERIFIED / MODE_PENDING` |
| RAM total del host | 13.52 GiB observados en una instantánea anterior | Volver a confirmar justo antes de ejecutar; la instantánea no es una garantía | `OBSERVED_SNAPSHOT / RECONFIRM` |
| RAM disponible | 7.64 GiB observados en una instantánea anterior | No usar como reserva garantizada ni como RSS de TALOS | `OBSERVED_SNAPSHOT / RECONFIRM` |
| Temperatura/throttling | No hay telemetría actual adjunta a este gate | Definir y aprobar telemetría/condición de parada antes de ejecución; ninguna cifra está aprobada | `NOT_MEASURED / POLICY_PENDING` |

No se selecciona CPU-only ni un máximo de un hilo en esta propuesta: sería una
configuración arbitraria y puede distorsionar innecesariamente el pool. Antes
de ejecutar, decidir modo CPU/GPU y fijar de forma reproducible los hilos de
PyTorch/ONNX Runtime, BLAS/OpenMP y tokenizer para cada backend. Los valores
efectivos deben registrarse y evitar paralelismo externo no controlado. Esto no
es una medición de “bajo consumo”.

## 2. Presupuesto de recursos — decisiones todavía abiertas

### RAM: interpretación propuesta

La formulación original fue “el sistema funcionando completo no debe ocupar
menos de 2 gb de ram”. La evidencia histórica interpretó 2 GiB como techo de
RSS, pero eso invierte el sentido literal. Para avanzar sin convertir esa
hipótesis previa en requisito, se propone interpretar **2 GiB como mínimo de
memoria disponible del host (`MemAvailable`) antes de iniciar y durante la
corrida**, no como mínimo ni como máximo de RSS del proceso.

| Decisión | Propuesta explícita | Estado |
|---|---|---|
| Significado de 2 GiB | `MemAvailable >= 2 GiB`, comprobado al inicio y continuamente | `PROPOSED / PENDING_APPROVAL` |
| RSS máximo de proceso/TALOS completo | 4 GiB para el árbol experimental completo bajo límite de memoria del SO; incluye runtime, modelo, tokenizer, caches y retrieval | `PROPOSED / PENDING_APPROVAL` |
| Acción ante límite | Detener el backend, marcar `FAILED_RESOURCE_LIMIT`, descartar pool parcial y no cambiar configuración para reintentar dentro de la misma versión | `PROPOSED / PENDING_APPROVAL` |
| RSS medida en esta fase | Ninguna | `NOT_MEASURED` |

El límite de 4 GiB es un guardrail experimental propuesto, no se deriva de
mediciones de Qwen/E5 y no afirma que ambos puedan ejecutarse dentro de él. Si
no se puede imponer y verificar un límite RSS del sistema operativo o medir
`MemAvailable`, no ejecutar. Ningún tamaño de artefacto sustituye estas
mediciones.

### CPU, duración, temperatura y almacenamiento

No hay definición aprobada de “bajo consumo”, cuota de CPU o duración. No fijar
un hilo ni un timeout arbitrario. Si se autoriza la ejecución, el modo y el
número de hilos deberán fijarse por runtime de forma determinista y quedar
registrados; el número elegido no debe presentarse como una medición de
rendimiento del hardware. Consultas seriales son una propuesta separada de los
hilos internos. Los guardrails cuantitativos siguen pendientes:

| Medida | Propuesta explícita para aprobación | Estado |
|---|---|---|
| Modo | CPU/GPU pendiente de decidir con capacidades verificadas | `UNDEFINED / BLOCKING` |
| CPU/hilos | Número/mode aún no decidido; fijar variables y límites de cada runtime y registrar el uso efectivo | `PENDING_DECISION` |
| Concurrencia externa | Una consulta a la vez es una propuesta independiente del número de hilos internos; requiere aprobación | `PROPOSED / PENDING_APPROVAL` |
| Timeout por consulta/backend | Valor pendiente; fijar según prueba operacional aprobada, sin convertir latencias externas en SLA | `UNDEFINED / BLOCKING` |
| Inicio/carga de artefactos | Valor pendiente | `UNDEFINED / BLOCKING` |
| Almacenamiento experimental | Valor pendiente según artefactos aprobados y temporales medidos/estimados; sin límite numérico aprobado | `UNDEFINED / BLOCKING` |
| Temperatura | Umbral pendiente, contrastado con límite oficial del CPU/plataforma y telemetría disponible | `UNDEFINED / BLOCKING` |
| Throttling/telemetría | Definir condición de parada y verificar fuente de telemetría antes de ejecutar | `UNDEFINED / BLOCKING` |
| Falla de una fuente | Marcar fuente como fallida; no sustituir sus resultados ni declarar pool completo | `PROPOSED / PENDING_APPROVAL` |

Un error, OOM, timeout, fallo de integridad o interrupción térmica debe dejar el
backend/corrida marcado `FAILED` o `INCOMPLETE`, conservar solo logs
operacionales no sensibles en el directorio aislado, no completar resultados
con otra fuente y no producir un pool apto para jueces. No reintentar con
configuración distinta dentro de la misma versión; cualquier ajuste genera una
nueva versión y hashes. Nunca representar resultados parciales como completos.

## 3. Artefactos, identidad y dependencias

| Componente | Evidencia local read-only ya registrada | Estado requerido antes de ejecutar |
|---|---|---|
| Qwen | La especificación de compatibilidad fija el modelo/revisión, tokenizer/revisión, 1024d, prompt, last-attended-token, L2, 512/right y FP32; no hay artefactos Qwen locales ni dependencias de inferencia disponibles. | Contrato lógico congelado; adquirir/revisar artefactos, calcular manifests, fijar runtime y verificar carga segura. `ARTIFACT_BINDING / RUNTIME BLOCKED`. |
| E5 | `model.onnx`, 470,268,510 bytes, SHA-256 `ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665`; tokenizer, 17,082,730 bytes, SHA-256 `0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39`. La API pública del repo/commit candidatos lista ambos paths y LFS SHA-256 coincidentes; sidecars locales enlazan esos ETags al commit. | Identidad de los archivos publicados `VERIFIED`; inspector Protobuf estático confirma grafo FP32. Receta histórica de export no documentada, solo necesaria para reconstrucción. El lock de paquetes está identificado; el runtime efectivo no coincide y permanece no verificado. Padding `PARTIALLY_RESOLVED_LOCAL_MASKING`; `onnx/config.json` declara ID 0, `tokenizer.json` ID 1 y `tokenizer_config.json` el token `<pad>`. |
| Tokenizer Qwen/E5 | La revisión/tokenizer del contrato están congelados; E5 local está presente y su identidad se confirma por LFS SHA-256 y ruta en el commit de `intfloat/multilingual-e5-small`; Qwen tokenizer ausente localmente. | Provenance del archivo E5 cerrada al snapshot público fijado; Qwen requiere artefactos/manifests. La diferencia pad ID 0 (config ONNX) vs 1 (tokenizer) aún necesita run manifest reproducible. |
| Contrato vectorial | Transformaciones, prefijos/instrucción, truncamiento, pooling, normalización, dimensiones y precisión candidata están congelados en `candidate_contracts_freeze.json`. | Validar que artefactos/runtime implementen esos valores; no asignar `vector_space_id` hasta verificar identidad completa. |
| `vector_space_id` | No se emite en este gate. | Si el candidate retriever requiere vectores/index temporal, calcular solo desde contratos verificados, aislados y completos; nunca asignarlo a índices históricos o producción. |
| Dependencias/runtime E5 | Lock con hash `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70`, compilado con uv para Python 3.10 y pins/hash de distribución; inventario instalado: Python `3.12.3`, NumPy `2.5.2`, ONNX Runtime `1.29.0`, Tokenizers `0.23.1`. | El lock candidato de dependencias está identificado, pero el entorno instalado no coincide. Patch Python, plataforma/ABI y runtime efectivo no están fijados como unidad reproducible; el run aislado de padding no se ha reproducido bajo el lock. `LOCK_IDENTIFIED_RUNTIME_UNVERIFIED`; instalación aislada no autorizada. |
| Dependencias/runtime Qwen | Metadata del `.venv`: `torch`, `transformers` y `sentence-transformers` no instalados. | Familia Transformers `AutoTokenizer`/`AutoModel` congelada; lock/versiones exactas pendientes. `trust_remote_code=False`; si no se puede cargar así, detenerse y revisar. `MISSING / BLOCKING`. |
| Lexical baseline | Código local [`LexicalRetriever`](../src/study_engine/retrieval/lexical.py) usa SQLite FTS/BM25, stopwords españolas y fallback de prefijos; SHA-256 `9c656c64c4f3106cbf666f4bbb33c8a60bdbc10acfe4aa98304d5144b303e2ff`. Dependencias de ejecución también incluyen [`knowledge_store.py`](../src/study_engine/storage/knowledge_store.py), SHA-256 `5ba709c5ccff3ce029a4dfa92deac0e5cdbca02ad6349a227744c9c85b485a21`, y [`lexical_index.py`](../src/study_engine/storage/lexical_index.py), SHA-256 `c65cae37006525b39199b074c9e9ad3a2171f1d95aac8ee5bdf4e4dd9cda08a7`. | Código actual fingerprinted; falta congelar dependencias SQLite/FTS, snapshot, filtros/tie-break y validar implementación específica top-100. No se ejecutó. |

Los tamaños de archivo son observaciones de presencia, no hashes ni revisiones
de modelo. No se debe descargar ni instalar ningún componente para completar
este inventario; la instalación/adquisición necesitará autorización operacional
explícita separada.

El entorno y contrato congelado para preparación se registran en
[`candidate_contracts_freeze.json`](../reports/backend_selection_adjudication_v1/candidate_contracts_freeze.json).
La preparación documental del blind pool está autorizada; la verificación de
prerrequisitos operacionales y la generación siguen pendientes.

### Qwen: verificación documental primaria

Read-only se revisó la [ficha del modelo Qwen3-Embedding-0.6B fijada al commit
`97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/tree/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3),
su [`config.json`](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/blob/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3/config.json),
el [README oficial en la misma revisión](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/blob/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3/README.md)
y [`1_Pooling/config.json`](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B/blob/97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3/1_Pooling/config.json).
Esto describe ese snapshot público, no prueba qué artefacto produjo el índice
histórico de TALOS.

| Evidencia primaria | Qué permite afirmar | Qué no permite afirmar |
|---|---|---|
| `config.json`: `max_position_embeddings=32768`, `hidden_size=1024`, dtype publicado `bfloat16`; ficha: 0.6B parámetros, dimensión de hasta 1024 y contexto 32K | Es capacidad/configuración documentada del snapshot. El 32K no obliga a usar esa longitud. | No determina el `max_length` de TALOS, RSS, latencia, CPU, temperatura, throughput ni compatibilidad operacional con el host. |
| README: ejemplo Transformers con last-token pooling, normalización L2, instrucción para query y `max_length=8192`; ejemplo Sentence Transformers ofrece prompt de consulta | Son ejemplos de uso oficiales para el modelo publicado. | No constituyen el contrato de ejecución de TALOS ni requieren adoptar 8192/32K. |
| `1_Pooling/config.json`: last-token pooling activo y mean pooling inactivo | Pooling configurado en ese snapshot Sentence Transformers. | No identifica la configuración usada en una ejecución histórica que no tenga revisión/hash vinculados. |
| [`embedding_contract.json`](../data/colab/embedding_contract.json): 1024 dimensiones, `max_length=512`, `pooling=mean`, normalización L2 y prefijos query/passage vacíos | Declaración local histórica de TALOS. 512 se puede mantener como límite experimental si se decide explícitamente. | Su campo `revision` es descriptivo, no un pin inmutable; no demuestra el artefacto/pooling que produjo embeddings históricos. |

**Discrepancia bloqueante:** el contrato local declarado (`mean`, sin
instrucción, 512) difiere del pooling y del uso con instrucción que documenta
el snapshot público consultado. No cambiar el contrato congelado ni resolver la
diferencia por suposición. Antes de generar candidatos, se debe decidir y
versionar la configuración del candidato Qwen, identificar revisión/tokenizer/
archivos con hashes y validar que query y passage cumplen el contrato elegido.
El contexto máximo documentado de 32K es distinto del `max_length=512`
histórico; no se debe dimensionar la corrida como si TALOS usara 32K.

Las afirmaciones externas sobre tiempo por consulta, RAM adicional, tamaño
cuantizado, uso de todos los hilos o compatibilidad por conteo de parámetros no
se incorporan: dependen de versión, dtype, cuantización, runtime, batch,
secuencia y configuración, y no son mediciones de TALOS. No se investigaron
Jina, Gemma ni otros modelos.

```text
documentación primaria del modelo
        ≠ configuración histórica ejecutada por TALOS
        ≠ medición local de TALOS
        ≠ límite operacional aprobado
```

## 4. Reproducibilidad y pool

Una ejecución futura deberá congelar, antes de iniciar:

- IDs/textos/scopes del conjunto v2.400 y hashes fuente registrados en el
  contrato; no mezclar v2.401.
- Snapshot idéntico de chunks/ACL y fingerprint antes y después; accesos SQLite
  read-only para el corpus y ninguna escritura en datos activos.
- Candidatos por query/scope: top-100 Qwen, top-100 E5 y top-100 lexical.
- Lexical baseline: implementación y configuración congeladas; código actual no
  basta para declarar identidad de ejecución.
- Deduplicación por `(notebook_id, chunk_id)`, fallo ante cualquier candidato
  fuera de scope, tie-break `(notebook_id, chunk_id)` y serialización ordenada.
- Provenance backend/rank/score y aliases conservados fuera de los paquetes de
  jueces; salida de jueces con aliases y orden separados.
- Semillas fijas y guardadas en provenance restringida para aleatorización y
  serialización reproducible; si un runtime no es determinista, registrar esa
  limitación e invalidar cualquier divergencia que afecte identidad/cobertura.
- `top_k=100` por cada candidato A/B/lexical, según el contrato congelado.
  La inferencia debe estar en modo evaluación, sin generación estocástica;
  el tie-break de puntuaciones iguales será `(notebook_id, chunk_id)`.
- Semilla propuesta `20260929` para orden aleatorio de paquetes; separar
  semillas por juez con derivación determinista y guardar valores solo en
  provenance restringida. Estado: `PROPOSED / PENDING_APPROVAL`.
- Congelar versiones de Python, PyTorch/ONNX Runtime, Tokenizers, NumPy,
  tokenizer y bibliotecas SQLite/FTS. Resolver versiones fuera del lock
  existente constituye una nueva decisión, no un ajuste silencioso.
- Hashes SHA-256 de entradas, artefactos, configuraciones, pool, contenido de
  candidatos y paquetes; validar que los paquetes no incluyan backend, scores,
  ranks, IDs fuente o provenance restringida.
- No calcular métricas ni conservar vistas de ranking para jueces. Tras crear
  y verificar pool/paquetes, detenerse en adjudicación humana.

**No hay ejecución realizada:** no se midieron latencia, throughput, CPU,
temperatura, RSS del modelo, RSS del árbol completo, tiempos de carga ni
almacenamiento temporal. No inferir estos resultados del código o de tamaños de
artefactos.

## 5. Contención de archivos y datos

### Red e instalación (propuesta; no aprobada)

- Red deshabilitada durante la ejecución de retrieval. No enviar consultas,
  chunks, scores ni provenance a servicios externos.
- Descarga inicial de artefactos: no incluida en la presente definición y no
  autorizada. Antes de habilitarla se debe aprobar origen/repo y revisión
  exactos, licencia, archivos esperados, SHA-256 y máximo de bytes; descargar
  solo esos artefactos a un cache aislado y verificar hashes antes de cargar.
- Instalación de dependencias: usar un entorno virtual aislado del experimento,
  solo paquetes/versiones/hashes previamente aprobados. Para E5, preferir los
  pins con hashes del lock del repositorio si la compatibilidad se valida. Para
  Qwen, no hay lock completo; preparar propuesta de dependencias, no instalar.
- Las herramientas de instalación pueden requerir conexión a índices de
  paquetes; cualquier habilitación de red será una ventana acotada a hosts
  aprobados, sin acceso de red durante inferencia. Si esto no se puede aislar,
  no ejecutar.

Si los prerrequisitos llegaran a aprobarse:

- toda dependencia/modelo nuevo iría a un entorno/cache explícitamente aislado
  y autorizado; no escribir en entornos globales;
- toda salida iría a un directorio nuevo, versionado y fuera de rutas
  productivas;
- no escribir ni reemplazar `knowledge_store.db`, `vector_store.db`, índices,
  golden sets, qrels existentes, paquetes actuales o configuración del runtime;
- no crear índice persistente/activo. Cualquier estructura vectorial temporal
  estrictamente necesaria para candidate retrieval debe quedar bajo una ruta
  efímera de experimento, tener hash y eliminarse según política aprobada;
- registrar bytes libres y espacio utilizado antes/después; si se excede el
  máximo aprobado, detener y marcar fallido;
- almacenar provenance sensible y resultados crudos con acceso restringido,
  separada de los paquetes ciegos;
- al producir y validar los paquetes del pool, parar; no benchmark, selección,
  promoción ni activación.

Ninguna de estas condiciones está ejecutándose o autorizada actualmente.

## 6. Tabla de cierre del gate

| Prerrequisito | Estado |
|---|---|
| Host observado y propuesto | `RECORDED; CONFIRM_BEFORE_RUN` |
| CPU/GPU mode and thread policy | `PENDING_DECISION; no single-thread assumption` |
| 2 GiB RAM semantics | `MINIMUM_HOST_MemAvailable; PROPOSED_NOT_APPROVED` |
| Maximum experimental RSS | `4 GiB process-tree cap; PROPOSED_NOT_APPROVED` |
| CPU cap/thread count | `UNDECIDED; fix per runtime if execution is authorized` |
| Timeout/query + backend + load | `UNDEFINED; BLOCKING` |
| Scratch storage | `UNDEFINED; BLOCKING` |
| Temperature/throttling stop | `UNDEFINED; BLOCKING` |
| Qwen artifact/revision/hash | `MISSING; BLOCKING` |
| Qwen pooling/instruction/length discrepancy | `UNRESOLVED; BLOCKING` |
| E5 artifact/revision/hash | `UPSTREAM_FILE_IDENTITY_VERIFIED_BY_PATH_SIZE_AND_LFS_SHA256; STATIC_GRAPH_FP32_VERIFIED; RUNTIME UNVERIFIED` |
| Tokenizer/vector contracts | `E5 tokenizer identity verified; padding run manifest and executable pair contract pending` |
| E5 dependency versions | `requirements.lock pins identified; installed compatibility unverified` |
| Qwen dependency lock | `MISSING; BLOCKING` |
| Internet/download/install policy | `NO ACCESS AUTHORIZED; BLOCKING` |
| Lexical code fingerprints | `RECORDED; execution config and FTS snapshot NOT_FROZEN` |
| Output isolation and no-production-write policy | `DEFINED; APPROVAL_REQUIRED` |
| Stop condition at frozen pool | `DEFINED; APPROVAL_REQUIRED` |
| Operational preconditions approved | **No** |
| Blind pool execution authorized | **No — `PENDING`** |

## Criterio de salida

Este gate no se considera cerrado operacionalmente mientras existan celdas
`PENDING`, `UNDEFINED`, `MISSING`, `UNPINNED` o `BLOCKING`. Su contenido queda
definido para que se puedan tomar las decisiones sin ejecutar nada, pero la
aprobación debe ocurrir después de presentar al usuario:

1. aprobar/modificar la interpretación propuesta de 2 GiB y decidir si se
   aprueba el guardrail RSS separado de 4 GiB;
2. decidir CPU/GPU y número de hilos fijo por runtime, sin imponer un solo hilo
   por defecto;
3. acordar timeouts, almacenamiento, temperatura/throttling con evidencia
   específica del host, no con cifras externas genéricas;
4. decidir la configuración candidata Qwen ante la discrepancia documental;
   identificar revisión/tokenizer/origen/hash y aprobar el lock requerido;
5. confirmar origen/revisión/licencia de los artefactos E5 pese a sus hashes
   locales;
6. aprobar la política de descargas/red e instalaciones aisladas o mantenerlas
   deshabilitadas;
7. cerrar configuración del lexical baseline y hash del snapshot FTS;
8. confirmar los guardrails en el host objetivo justo antes de la eventual
   ejecución.

Solo con esos valores aprobados podrá actualizarse el registro operacional.
Una aprobación de prerrequisitos tampoco equivale a la autorización final de
ejecución: el Blind Pool Generation Gate seguirá separado hasta que reciba
autorización operacional explícita.
