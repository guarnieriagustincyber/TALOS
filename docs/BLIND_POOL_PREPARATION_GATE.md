# TALOS Full-Pipeline Blind-Pool Preparation Gate

**Estado:** `PREPARATION_AUTHORIZED_EXECUTION_PENDING`<br>
**Autorización:** preparación documental/read-only autorizada por el usuario<br>
**Generación de candidatos, embeddings o índices:** no autorizada<br>
**Blind Pool Generation Authorization Gate existente:** `PENDING`<br>
**Resolución de prerrequisitos de ejecución:** [gate abierto, bloqueado hasta verificación](./EMBEDDING_EXECUTION_PREREQUISITES_RESOLUTION_GATE.md)

## Alcance autorizado ahora

Esta autorización permite únicamente:

- congelar la especificación de compatibilidad de los candidatos Qwen y E5;
- inspeccionar hashes/metadata existentes y versiones instaladas sin cargar
  modelos;
- preparar manifests, checklist de procedencia y especificación de pool;
- diseñar la separación Colab index-build / PC query-only;
- verificar estáticamente que outputs y rutas futuras no escriban producción.

No permite descargas, instalaciones, conversiones ONNX, ejecución de modelos,
tokenización/inferencia del corpus, generación de embeddings, retrieval,
reindexación, mediciones operacionales, construcción de índices, creación de
paquetes con candidatos reales, adjudicación, métricas o benchmark.

## Contratos congelados para preparación

La especificación de compatibilidad se registra en
[`candidate_contracts_freeze.json`](../reports/backend_selection_adjudication_v1/candidate_contracts_freeze.json)
y se desarrolla en
[Candidate Contracts Proposal](./EMBEDDING_BACKEND_CANDIDATE_CONTRACTS_PROPOSAL.md).
Esto congela la receta lógica, no las identidades vectoriales efectivas:

- Qwen: revisión/tokenizer fijados, last-attended-token, instrucción de query
  explícita, sin instrucción passage, 1024 dimensiones, 512 tokens, L2, FP32.
- E5: revisión/tokenizer upstream fijados, prefijos E5, mean attention-mask,
  384 dimensiones, 512 tokens, L2, ONNX FP32/CPU.
- Ambos: mismo orden de normalización Unicode/strip; una pareja de encoder
  query+documento por espacio; ningún vector Qwen/E5 se mezcla.

No se calcula `vector_space_id` hasta que manifests completos de modelos,
tokenizers y cualquier conversión estén disponibles y validados.

## Estado de verificación y bloqueos

| Prerrequisito | Observación read-only | Estado |
|---|---|---|
| Qwen revision | Commit público fijado `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3` | Documentación fijada; artefactos locales ausentes |
| Qwen runtime | `torch`, `transformers` y `sentence-transformers` no instalados en el entorno inspeccionado | `BLOCKED`; lock exacto no preparado |
| E5 upstream revision | Commit candidato `614241f622f53c4eeff9890bdc4f31cfecc418b3` | Documentación fijada |
| E5 local artifacts | ONNX/tokenizer tienen SHA-256 y sus rutas, tamaños y LFS SHA-256 coinciden con el commit upstream fijado; inspección Protobuf estática del ONNX confirma tensores flotantes/salida FLOAT | Identidad upstream y tipo FP32 del grafo verificados; compatibilidad de inferencia no ejecutada. Padding previo reportado, con run manifest reproducible pendiente |
| Runtime E5 candidato/instalado | `requirements.lock` fija paquetes con versiones/hash para Python 3.10; instalado: Python 3.12.3, NumPy 2.5.2, ORT 1.29.0, Tokenizers 0.23.1 | Lock de dependencias identificado, pero el entorno de ejecución candidato no fue reproducido/verificado |
| Precisión/compatibilidad | Inspección Protobuf estática confirma grafo con tensores flotantes y salida `FLOAT`; no se cargó sesión ONNX | `STATIC_GRAPH_FP32_VERIFIED`; ejecución/compatibilidad no probadas |
| Índice histórico Qwen | No hay manifest/run provenance que demuestre la pareja | No usar como primario hasta prueba suficiente |
| Reindexador local | E5 384d se etiqueta como Qwen 4B/2560d y default apunta a store activo | Prohibido para este experimento |
| Límites operacionales | RAM/CPU/timeout/storage/temperatura no aprobados | `BLOCKED` |

## Candidato a blind pool

Cuando existan artefactos íntegramente vinculados y una futura autorización
operacional expresa, la preparación de candidatos deberá usar:

1. mismo snapshot de chunks/scope/ACL para ambos índices;
2. índices Qwen-R y E5-R completos y compatibles, o fallo cerrado si una
   pareja no se puede construir;
3. top-100 por Qwen, top-100 por E5 y top-100 lexical, bajo la regla ya
   congelada en el benchmark v1 y su addendum;
4. unión/deduplicación determinista y provenance restringida;
5. paquetes A/B ciegos sin backend, score, rank ni procedencia;
6. validación de scope/ACL, hashes y serialización, y parada al congelar los
   paquetes.

El pool no es un benchmark ni resultado de calidad. Qrels deben adjudicarse y
congelarse antes de cualquier comparación. Cualquier fuente que no tenga una
pareja completa compatible no puede rellenarse con otro backend ni etiquetarse
como resultado de ese backend.

## Transición requerida

Primero cerrar el
[Embedding Execution Prerequisites Resolution Gate](./EMBEDDING_EXECUTION_PREREQUISITES_RESOLUTION_GATE.md)
para ambos candidatos; ese cierre tampoco autoriza ejecución.

No mover el gate de generación a `AUTHORIZED` mientras:

- runtime E5 fijado y compatibilidad reproducible del padding sigan pendientes;
- la discrepancia de `pad_token_id` del provider E5 no esté resuelta en un
  adaptador aislado y validado;
- el runtime/lock Qwen no esté definido y aprobado;
- los límites operacionales sigan pendientes;
- el índice Qwen histórico o el plan de reconstrucción Qwen-R no esté resuelto;
- el corpus/scope snapshot y el directorio aislado no estén hasheados/verificados.

Tras cerrar estos puntos, crear una autorización operacional versionada que
distinga explícitamente adquisición/instalación, construcción de índices,
candidate retrieval y stop-after-pool. La autorización actual solo abre esta
preparación y no satisface ese gate.
