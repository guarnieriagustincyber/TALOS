# Embedding Backend Selection — Evidence Gate

**Estado:** investigación read-only iniciada; selección inconclusa.
**Decisión de recursos usada para el análisis:** interpretar el requisito del
usuario como un presupuesto máximo de **2 GiB de RSS para el subsistema TALOS
completo** (proceso(s) de servicio, proveedor/modelo, tokenizer, matrices
cacheadas y búsqueda), con uso de CPU bajo. Se eligió el límite superior por
ser la interpretación conservadora coherente con “bajo consumo”; confirmar o
ajustar ese presupuesto antes de ejecutar la prueba de capacidad.

Este gate compara la evidencia disponible para Qwen 0.6B y multilingual-E5-small.
No elige proveedor, crea índice, genera embeddings, instala dependencias,
modifica runtime ni toca datos. El índice Qwen histórico sigue
`LEGACY / UNRESOLVED`; los shards E5 no se consideran su procedencia ni un
reemplazo autorizado.

## Resumen ejecutivo

No hay evidencia comparable suficiente para declarar ganador:

- E5 tiene artefactos ONNX locales. El entorno dispone de ONNX Runtime,
  Tokenizers y NumPy, pero sus versiones y Python difieren del lock y no
  permiten declarar el runtime candidato reproducible.
- Qwen no tiene artefactos locales y no están disponibles
  `sentence-transformers` ni `torch`; no se pudo ejecutar localmente ni
  verificar que quepa en el presupuesto.
- Los E5 shards existentes solo resuelven 15 de los 76 pares positivos
  `(notebook_scope, chunk_id)` del benchmark v2.400. El índice Qwen principal
  resuelve los 76; usar los shards tal como están produciría una comparación
  sesgada por cobertura.
- El benchmark v2.400 es un punto de partida utilizable tras completar/adjudicar
  labels: contiene qrels positivos en 48 de 400 consultas; sus 352 consultas sin
  qrels no OOD no se deben interpretar automáticamente como irrelevantes.
- El benchmark v2.401 contiene 420 consultas y más qrels, pero el scope está
  normalizado a `NB-SEC-01-C-PTR` para todas. Los análisis existentes documentan
  inconsistencias de scopes/qrels; no se debe usar como base de selección hasta
  una revisión versionada.

**Resultado actual:** candidato E5 más sencillo de materializar localmente;
Qwen conserva evidencia previa de uso/calibración, pero sin pipeline local
reproducible. Ninguna de estas observaciones sustituye calidad comparativa ni
prueba que el requisito de 2 GiB se cumpla.

## Evidencia inspeccionada

### Hardware observado

Lectura puntual del host durante esta investigación:

| Recurso | Observación |
|---|---|
| CPU | AMD Ryzen 5 5600GT with Radeon Graphics |
| CPU lógicas / físicas | 12 / 6 |
| Frecuencia máxima observada en sysfs | 4.66875 GHz |
| RAM del host | 13.52 GiB |
| RAM disponible en la instantánea | 7.64 GiB |
| Presupuesto para TALOS | 2 GiB máximo asumidos; no medido con backend activo |

La memoria disponible es una instantánea del host, no una garantía estable ni
el presupuesto del servicio. La prueba futura debe medir el árbol de procesos
de TALOS completo, tanto en frío como en régimen estable, incluyendo búsqueda
del índice. No basta con informar tamaño del archivo ONNX o RSS del proceso
aislado de embeddings.

### Candidatos y capacidad de ejecución local

| Criterio | Qwen3-Embedding-0.6B | multilingual-E5-small |
|---|---|---|
| Evidencia de identidad local | Contrato Colab v1 declara nombre, 1024d, 512 tokens, mean, L2 y prefijos vacíos; revisión es texto descriptivo, no pin inmutable | ONNX local de 470,268,510 bytes y tokenizer de 17,082,730 bytes |
| Runtime local disponible en este entorno | No: faltan `torch` y `sentence-transformers`; no hay carpeta local Qwen | `.venv` incluye Python 3.12.3, NumPy 2.5.2, ONNX Runtime 1.29.0 y Tokenizers 0.23.1; no coincide con los pins del lock para Python 3.10, por lo que no es el runtime candidato reproducible |
| Implementación inspeccionada | Sentence Transformers, `trust_remote_code=True`, normalización L2 | ONNX Runtime CPU, tokenizer local, truncamiento configurado a 512, pooling mean con attention mask, L2 |
| Control de hilos observado en código | No se encontró fijado en el proveedor Sentence Transformers examinado | `intra_op_num_threads=4`, `inter_op_num_threads=1` |
| Índice histórico disponible | `data/web_state/vector_store.db`: 46,530 filas Qwen/1024 para `fadena-std`; no tiene identidad v2 ni binding de generación | Shards separados; cobertura del benchmark insuficiente y provenance histórica no demostrada |
| RSS/CPU de inferencia medidos | No | No |
| Cumplimiento del techo de 2 GiB probado | No | No |

El proveedor ONNX existente usa prefijos E5 `query: ` y `passage: `, igual
pooling mean y normalización L2. Son observaciones del código actual, no
certificación de que todos los vectores E5 de los shards se generaran con esta
implementación/configuración. Su configuración de hilos (`4 + 1`) tampoco prueba
que sea de bajo consumo; tendrá que medirse y compararse bajo el mismo límite
de hilos para ambos backends.

### Benchmark y qrels disponibles

El resumen de los artefactos locales es:

| Dataset | Consultas | Qrels positivos | Consultas con qrels positivos | Observación |
|---|---:|---:|---:|---|
| v2.400 | 400 | 165 pares | 48 | 60 OOD sin positivos; 292 consultas no OOD también carecen de qrels positivos |
| v2.401 | 420 | 1,704 pares | 360 | Las 420 consultas apuntan al mismo scope `NB-SEC-01-C-PTR`; ya hay problemas de scope documentados |

En v2.400, las categorías y cobertura positiva observada son:

| Categoría | Consultas | Consultas con positivo |
|---|---:|---:|
| `ood_trampas` | 60 | 0 (esperado para abstención) |
| `vulnerabilidades` | 60 | 7 |
| `sintaxis_codigo` | 80 | 22 |
| `multi_capitulo` | 80 | 9 |
| `fundamentos` | 120 | 10 |

El inventario Qwen resuelve 76/76 pares positivos por scope del v2.400. Los
shards E5 existentes resuelven 15/76; son un inventario parcial y no deben
usarse como índice de comparación contra Qwen. La evaluación justa deberá
re-embeddar el mismo snapshot de corpus en almacenamiento temporal, por separado
para cada contrato, sin modificar las bases actuales.

Los datos históricos de `benchmark_results.json` informan Recall/MRR y latencia,
pero `scripts/benchmark_gate2_retrieval.py` usa `DeterministicHashEmbedder`.
Esos resultados no comparan Qwen y E5. Además,
`data/config/retrieval_config.json` atribuye la calibración del umbral a Qwen,
mientras que `data/experiments/hito6/relevance_calibration_report.json` reporta
el proveedor `local_onnx`/E5. Resolver esa discrepancia antes de reutilizar
umbrales; no transferir el threshold 0.84 entre modelos.

### Límites de la evidencia actual

- La evidencia de v2.400 sugiere evaluación de recuperación, pero qrels ausentes
  en consultas no OOD son “sin juicio” hasta adjudicación, no negativos
  implícitos. Reportar Recall/MRR solo sobre consultas juzgadas y abstención OOD
  como métrica separada.
- v2.401 no es intercambiable con v2.400 y no se deben combinar sus qrels para
  aumentar artificialmente cobertura. Si se corrige, conservar la versión
  histórica y producir un nuevo dataset/qrels con scopes reconciliados y hashes.
- Un modelo puede tener mejor Recall pero peor latencia/RSS. La elección exige
  reportar métricas por categoría y por consulta, recursos, y resultados con
  el mismo corpus, tokenizer/prefix contract, top-k, ACL y configuración.
- La evaluación debe cubrir consultas cortas/largas, español técnico, símbolos
  de código, exact-match, paráfrasis, multi-capítulo, facets y OOD; el tamaño
  actual de v2.400 no garantiza cobertura suficiente en cada subgrupo.

## Protocolo propuesto para completar la selección

1. **Congelar el set de evaluación.** Tomar v2.400 como fuente, verificar sus
   hashes, scopes y referencias, y preparar una nueva versión de evaluación con
   juicios positivos adjudicados para consultas relevantes no OOD. No editar
   v2.400/v2.401 in-place. Mantener consulta, scope/ACL, qrels graduados y
   categoría/tags; registrar corpus, chunking y hash de cada artefacto.
2. **Fijar contratos candidatos separados.** Crear contratos v2 sintéticos
   completos para Qwen y E5 solo cuando se disponga de revisiones inmutables y
   manifests verificables. No asignar esos IDs a índices históricos. Verificar
   prefixing, truncamiento, pooling y normalización de la implementación real.
3. **Construir snapshots efímeros iguales.** Re-embed todos los mismos chunks
   de evaluación para cada candidato en almacenes temporales separados. Respetar
   scope/ACL idénticos; usar top-k, métrica y filtros iguales; nunca consultar
   por similitud entre espacios.
4. **Medir calidad.** Informar Recall@1/5/10, Precision@k, MRR, nDCG@k con
   qrels graduados, cobertura de facets/exact-match y abstención/false positives
   OOD. Desglosar por categoría, longitud y tipo de consulta; incluir intervalos
   o diferencias pareadas cuando proceda. No establecer un ganador por promedio
   global solamente.
5. **Medir recursos en el hardware destino.** Incluir carga fría y warm-up,
   consulta única y carga representativa, con límite idéntico de threads.
   Registrar RSS máximo del árbol de procesos completo TALOS, CPU-segundos por
   query, CPU promedio/p95, p50/p95 de latencia, throughput y temperatura si es
   accesible. Aceptación obligatoria: pico total <= 2 GiB. “Bajo CPU” queda
   registrado como requisito, pero requiere una cifra acordada; reportar primero
   mediciones comparables y evaluar un perfil single-thread antes de elevar
   concurrencia.
6. **Cerrar con matriz, no selección automática.** Comparar calidad,
   reproducibilidad/artefactos, RAM, CPU, latencia, disponibilidad local y coste
   operativo. Publicar limitaciones y decisión humana posterior. Solo entonces
   iniciar el gate aparte de diseño de nacimiento v2; rebuild y activación siguen
   requiriendo autorizaciones separadas.

## Estado y conclusión

| Dimensión | Estado |
|---|---|
| Evidencia del índice Qwen histórico | `LEGACY / UNRESOLVED`; fuera de la comparación como provenance |
| Evidencia de artefactos E5 locales | Identidad del modelo/tokenizer vinculada a los LFS SHA-256 del commit fijado; inspección protobuf confirma tipos flotantes/output FLOAT; la receta de export no se requiere para el archivo publicado exacto |
| Benchmark comparable actual | No listo; v2.400 necesita tratamiento de qrels sin juicio y v2.401 no es base válida sin reparación |
| Calidad Qwen vs E5 | No medida |
| RAM <= 2 GiB | No verificada para ninguno |
| Bajo consumo de CPU | No medido ni cuantificado |
| Selección de backend | **NO DECIDIDA** |
| Cambios de datos/runtime | Ninguno |

No se ejecutó inferencia de corpus, benchmark, instalación de paquetes ni
escritura en índices. Posteriormente se registró una prueba aislada local de
compatibilidad del padding E5 con textos sintéticos; su alcance y limitaciones
están documentados en
[EMBEDDING_EXECUTION_PREREQUISITES_RESOLUTION_GATE.md](./EMBEDDING_EXECUTION_PREREQUISITES_RESOLUTION_GATE.md).
El gate de selección queda **inconcluso / sin ganador**. El protocolo está
congelado como v1 tras revisión adversarial offline en
[EMBEDDING_BACKEND_SELECTION_BENCHMARK_CONTRACT.md](./EMBEDDING_BACKEND_SELECTION_BENCHMARK_CONTRACT.md),
con fixtures sintéticos. Antes de cualquier prueba de corpus/calidad/capacidad
quedan por adjudicar/fijar los qrels reales, confirmar el límite provisional
de RAM y definir la unidad numérica de bajo consumo de CPU.
