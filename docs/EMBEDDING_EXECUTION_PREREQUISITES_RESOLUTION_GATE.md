# TALOS Embedding Execution Prerequisites Resolution Gate

**Estado:** `OPEN_PARTIALLY_RESOLVED`<br>
**Propósito:** resolver y documentar identidad de artefactos, runtime y
compatibilidad de entrada/salida para los candidatos Qwen-R y E5-R.<br>
**Ejecución de modelos, generación de vectores/índices y blind pool:** no
autorizadas<br>
**Prueba de compatibilidad aislada E5:** ejecutada con textos sintéticos,
localmente y sin cargar corpus ni producción<br>
**Reproductor de padding:** preparado en
[`verify_e5_padding_compatibility.py`](../scripts/verify_e5_padding_compatibility.py),
pero no ejecutado en esta etapa<br>
**Inspección estática E5 ONNX:** ejecutada; archivo FP32 verificado por tipos
Protobuf, sin sesión/inferencia<br>
**Freeze de compatibilidad:** permanece congelado y sin cambios

## Alcance

Este gate separa la resolución de prerrequisitos de la autorización posterior
para ejecutar los candidatos. Permite recopilar y contrastar evidencia
documental, hashes, configuración y código existentes. La prueba offline
aislada de tokenizer y ONNX E5 con textos sintéticos se reportó en el estado
previo. El trabajo actual preparó un reproductor, pero no repitió la prueba;
ejecutarlo y guardar un manifest requiere autorización puntual explícita. No
autoriza:

- descargar/adquirir modelos o dependencias, ni instalar paquetes;
- ejecutar inferencia de corpus, retrieval o generación de embeddings de
  candidatos;
- ejecutar Qwen, E5, retrieval o mediciones operacionales;
- cambiar el provider de producción, contratos congelados o índices;
- generar embeddings, índices experimentales, candidatos o blind pool;
- emitir `vector_space_id` o promover un backend.

La prueba aislada de padding no constituye evidencia de provenance ni de
viabilidad operacional. La identidad de archivo E5 se verificó aparte con la
API pública del Hub. El reproductor preparado no amplía ni renueva la
autorización para ejecutar ONNX.

El estado `VERIFIED` de todos los prerrequisitos sería una condición necesaria,
pero no suficiente, para solicitar autorización de ejecución en un gate
versionado separado.

## Estado de los candidatos

| Candidato | Prerrequisito | Evidencia actual | Estado |
|---|---|---|---|
| Qwen-R | Identidad del modelo/tokenizer | Revisión candidata fijada en el freeze, pero los archivos no están presentes localmente ni tienen manifests SHA-256 vinculados | `BLOCKED_ARTIFACT_BINDING` |
| Qwen-R | Runtime reproducible y carga segura | Transformers/PyTorch no están instalados; falta lock exacto y verificación de carga con `trust_remote_code=False` | `BLOCKED_RUNTIME` |
| Qwen-R | Precisión | FP32 está especificado, pero no hay artefactos locales ni evidencia de ejecución conforme | `SPECIFIED_NOT_VERIFIED` |
| Qwen-R | Índice histórico | No se ha demostrado la pareja exacta documento/query | `HISTORICAL_PAIR_UNVERIFIABLE`; no elegible para comparación primaria |
| E5-R | Identidad/provenance ONNX y tokenizer | La API pública del repositorio `intfloat/multilingual-e5-small` en el commit candidato lista `onnx/model.onnx` y `onnx/tokenizer.json` con tamaños y LFS SHA-256 idénticos a los archivos locales; los sidecars locales apuntan al mismo commit y ETags | `VERIFIED_UPSTREAM_FILE_IDENTITY`; receta histórica no documentada |
| E5-R | Precisión del artefacto | Un parser protobuf estático, fijado en [`inspect_e5_onnx_static.py`](../scripts/inspect_e5_onnx_static.py), inspeccionó el archivo local cuyo SHA coincide con Hub: tensores flotantes y salida `last_hidden_state` en FLOAT (enum 1), único Cast a FLOAT; no se abrió sesión ONNX Runtime | `VERIFIED_STATIC_ONNX_FLOAT32`; kernel/runtime no ejecutados |
| E5-R | Padding | `tokenizer.json` declara `<pad>` id `1`; [`LocalONNXEmbeddingProvider`](../src/study_engine/retrieval/embedding.py) fuerza `pad_id=0`. La prueba aislada previamente reportada encontró salida idéntica con ambos IDs bajo attention-mask mean pooling y L2; aún no hay manifest reproducible | `PARTIALLY_RESOLVED_LOCAL_MASKING` |
| E5-R | Dependencias/runtime reproducible | `requirements.lock` fija paquetes con versiones y hashes, generado por uv para Python 3.10; el entorno observado usa Python 3.12.3, NumPy 2.5.2, ONNX Runtime 1.29.0 y Tokenizers 0.23.1. El lock candidato está identificado, pero no existe un entorno ejecutable coincidente verificado; patch Python, plataforma/ABI y restricciones del host no están cerradas | `LOCK_IDENTIFIED_RUNTIME_UNVERIFIED` |

La inspección inicial omitió el directorio oculto y los symlinks del
intérprete; por eso su conclusión de que no había `.venv` ni paquetes locales
fue incorrecta. La verificación directa confirmó que `./.venv` sí existe y
contiene Python 3.12.3, NumPy 2.5.2, ONNX Runtime 1.29.0 y Tokenizers 0.23.1.
Su ejecutable Python enlaza con `/usr/bin/python3`; el entorno incluye `uv`
0.12.10. Estas versiones no coinciden con los pins E5 del lock
(NumPy 2.2.6, ONNX Runtime 1.23.2, Tokenizers 0.23.2), así que el venv
existente no satisface el runtime bloqueado. No se instaló, creó ni modificó
ningún entorno.

Las referencias y los valores congelados se mantienen en
[`candidate_contracts_freeze.json`](../reports/backend_selection_adjudication_v1/candidate_contracts_freeze.json).
La consulta read-only a la API pública del Hub para
[`intfloat/multilingual-e5-small` en la revisión fijada](https://huggingface.co/api/models/intfloat/multilingual-e5-small/tree/614241f622f53c4eeff9890bdc4f31cfecc418b3?recursive=true&expand=false)
lista ambos archivos bajo `onnx/` con tamaños y SHA-256 LFS que coinciden
exactamente con los bytes locales:

| Archivo upstream | Tamaño API | SHA-256 LFS API | SHA-256 local | Resultado |
|---|---:|---|---|---|
| `onnx/model.onnx` | 470,268,510 | `ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665` | `ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665` | Coincide |
| `onnx/tokenizer.json` | 17,082,730 | `0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39` | `0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39` | Coincide |

Esto vincula de forma verificable los bytes locales con las rutas publicadas
por el repositorio y commit candidatos; ya no depende solo de los sidecars.
Los sidecars locales confirman que ambas descargas registraron ese mismo
commit y esos ETags. La identidad del archivo ONNX publicado queda resuelta,
pero no la receta/toolchain histórica con que fue creado. La inspección
estática de los tipos flotantes se registra en la subsección siguiente; no
mide la precisión numérica efectiva de los kernels. Si el candidato utiliza
exactamente este archivo publicado, no hace falta reconstruir el export para
identificarlo; una reconstrucción sí requeriría fijar receta/toolchain.

El JSON
[`candidate_contracts_freeze.json`](../reports/backend_selection_adjudication_v1/candidate_contracts_freeze.json)
conserva su estado original (`local_artifact_upstream_provenance=NOT_VERIFIED`,
precisión pendiente) como registro del freeze. No se reescribió: la evidencia
read-only posterior queda asentada en este gate y en
[`operational_preconditions_proposal.json`](../reports/backend_selection_adjudication_v1/operational_preconditions_proposal.json).

Los archivos de configuración publicados en la misma revisión añaden contexto:
[`onnx/config.json`](https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/config.json)
declara `hidden_size: 384`, `max_position_embeddings: 512` y
`pad_token_id: 0`; [`onnx/tokenizer_config.json`](https://huggingface.co/intfloat/multilingual-e5-small/resolve/614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/tokenizer_config.json)
declara `pad_token: "<pad>"` y `model_max_length: 512`. El `tokenizer.json`
local vinculado al mismo commit asocia `<pad>` con ID `1`. Por lo tanto, el ID
0 del provider coincide con la configuración ONNX publicada, mientras que el
tokenizer declara ID 1: deben conservarse ambas observaciones y no inferir de
ellas, sin el run manifest, equivalencia general de semántica.

| Sidecar local | Contenido relevante | SHA-256 del sidecar |
|---|---|---|
| `models/multilingual-e5-small/.cache/huggingface/download/onnx/model.onnx.metadata` | revisión `614241f622f53c4eeff9890bdc4f31cfecc418b3`; ETag `ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665`; timestamp `1788380447.6242104` | `01ef1b7cd4dda84f7a27a9af9621d4debaf06c76e27632aaaae4b6b380477687` |
| `models/multilingual-e5-small/.cache/huggingface/download/onnx/tokenizer.json.metadata` | revisión `614241f622f53c4eeff9890bdc4f31cfecc418b3`; ETag `0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39`; timestamp `1788380450.8129516` | `16e5f97c7636dfcb0e4f1afd054c3cd2bb771497f24bbe6f7489df00fde6cb67` |

Los hashes de sidecar hacen reproducibles las observaciones locales. La
asociación con repositorio/ruta se apoya adicionalmente en el registro público
LFS del commit exacto; no se afirma que los sidecars sean una atestación
firmada de origen.

### Precisión del grafo ONNX: inspección estática

Se inspeccionó el Protobuf del archivo de 470,268,510 bytes directamente con
[`inspect_e5_onnx_static.py`](../scripts/inspect_e5_onnx_static.py), un lector
estático que verifica antes el SHA-256 esperado y no importa `onnx`,
`onnxruntime`, ni crea una sesión. Resultado para SHA-256
`ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665`:

| Componente Protobuf | Tipos ONNX encontrados |
|---|---|
| Initializers | 197 `FLOAT` (FP32), 1 `INT64` |
| Tensor attributes | 100 `FLOAT` (FP32), 184 `INT64` |
| Inputs | `input_ids`, `attention_mask`, `token_type_ids`: `INT64` |
| Output | `last_hidden_state`: `FLOAT` (FP32) |
| Nodos `Cast` | 1; target `FLOAT` (enum 1) |
| `FLOAT16`, `BFLOAT16`, otros tipos flotantes | Ninguno en initializers/atributos inspeccionados |

SHA-256 del inspector estático:
`8273236f503fa8c85d503b9abe4aca5ca5fb9ee6c701236617c90bf438281409`.
La conclusión se limita al tipo numérico serializado en este grafo ONNX
publicado e identificado: sus cómputos flotantes declarados son FP32. No es
una medición de precisión numérica del kernel CPU ni un test de tolerancia.
El inspector observó además `producer_name=pytorch`,
`producer_version=2.0.1`, opset ONNX 11, 1,243 nodos y cero `value_info`
intermedios. La ausencia de `value_info` se conserva como limitación: la
conclusión FP32 combina todos los tensores constantes enumerados, el tipo
declarado de salida y los targets `Cast`; no afirma que se haya ejecutado
inferencia.

## Resolución requerida: E5 padding

### Hallazgo local reportado; reproducción pendiente

El provider configura manualmente `pad_id=0`, mientras la metadata del
tokenizer local asocia `<pad>` con id `1`. La configuración ONNX publicada en
el mismo commit fija además `pad_token_id: 0`, y el `tokenizer_config.json`
publicado declara `pad_token: "<pad>"` y longitud máxima 512. Esto es evidencia
de dos fuentes de configuración distintas, no prueba por sí sola que el ID 0
sea intercambiable con el ID 1 en cualquier ruta. Se ejecutó una prueba local aislada
con el tokenizer y la sesión ONNX del artefacto E5 presente en el repositorio:

- `tokenizer_pad_id=1`
- `literal_pad_encoding=[1]`
- `attention_mask_identical=true`
- `valid_input_ids_identical=true`
- `max_abs_delta_batch_pad0_vs_pad1=0`
- `l2_norms=[1.0, 1.0, 1.0]`

La prueba reportada observó que, para esa sesión ONNX y el esquema de mean
pooling con máscara, los slots de padding quedaron enmascarados y no cambiaron
la salida final ni la normalización L2. La diferencia `0 vs 1` no modificó el
vector final en esa ejecución con textos sintéticos; la ausencia de manifest
impide reproducirla ahora como evidencia independiente.

El resultado previo es una observación reportada, no todavía un artefacto
reproducible del workspace. El script
[`verify_e5_padding_compatibility.py`](../scripts/verify_e5_padding_compatibility.py)
fija tres fixtures sintéticos, verifica hashes locales de modelo, tokenizer y
sidecars, compara ambas variantes de padding y produce un manifest JSON con el
resultado, las versiones del runtime y el hash del script. SHA-256 actual del
reproductor: `31b46489b74a0098eb7ed160885e52a6b8ae08893691b62a4d8ca6a3994ad6b4`.
**No se ejecutó durante esta etapa.** Ejecutarlo cargaría el ONNX e inferiría
solo esos textos sintéticos; no debe hacerse sin autorización puntual explícita.

### Lo que sigue sin cerrarse

La procedencia de los bytes del ONNX y tokenizer ya está vinculada al archivo
publicado en el commit candidato. Sin embargo, la prueba de padding reportada
no tiene aún un manifest reproducible y no cierra la compatibilidad normativa
de entrada. La receta de exportación solo sería necesaria para reconstruir el
artefacto, no para identificar el archivo publicado y fijado por hash. Siguen
pendientes el runtime efectivo compatible con el lock y la reproducción
autorizada que permita seleccionar y documentar el ID de padding del adaptador
experimental, manteniendo juntos el tokenizer, el ONNX y la máscara.

### Criterio para cerrar el prerrequisito

Antes de considerar E5 verificado, un adaptador **experimental aislado** debe:

1. comparar el ID `0` declarado por la configuración ONNX con el ID derivado
   del tokenizer vinculado por hash, y documentar cuál utiliza el adaptador
   experimental; no modificar el provider de producción;
2. demostrar con los artefactos fijados cómo interactúan los IDs de entrada,
   el ONNX y la máscara de atención;
3. verificar entradas de longitudes diferentes, IDs insertados en padding,
   máscara (padding enmascarado) y salida finita de 384 dimensiones;
4. demostrar que el pooling `mean-attention-mask-v1` excluye posiciones
   rellenadas y que la normalización L2 produce vectores de norma unitaria
   dentro de tolerancia predefinida;
5. ejecutar el reproductor bajo un runtime autorizado y conservar el manifest
   JSON junto con el hash del script y las versiones efectivas.

La prueba aislada local indica que la discrepancia `0 vs 1` no altera el
vector final bajo el esquema observado de enmascarado, pero no reemplaza un run
manifest reproducible ni la verificación del runtime fijado. El tipo FP32 del
grafo sí se verificó estáticamente; la precisión numérica efectiva de los
kernels no se midió. El binding de los archivos publicados también queda
registrado por separado.

El reproductor permite repetir y registrar la prueba, pero aún no existe un
manifest de ejecución producido por él. La evidencia de padding sigue como
resultado local reportado y `PARTIALLY_RESOLVED_LOCAL_MASKING`.

## Evidencia requerida para artifact binding y runtime

### Qwen-R

- archivos del checkpoint y tokenizer identificados por revisión inmutable y
  manifests SHA-256 completos;
- dependencias exactas, Python/plataforma y política de carga fijados en un
  lock reproducible;
- confirmar mediante evidencia documental/código que el adaptador implementa
  prompt, 512/right, last-attended-token y L2 del freeze;
- demostrar que la carga no requiere código remoto; si requiere
  `trust_remote_code`, parar y abrir revisión separada;
- fijar la política FP32. Cualquier incompatibilidad o cambio de precisión
  requiere revisión del candidato antes de ejecución.

### E5-R

- conservar como evidencia de artifact binding la coincidencia de LFS SHA-256,
  tamaño, ruta y commit mostrada en la API pública;
- FP32 del archivo publicado está verificado estáticamente por el inspector
  protobuf; no extender esta afirmación a ejecuciones ni a diferencias
  numéricas de kernels;
- si se pretende reconstruir el ONNX en lugar de consumir el archivo publicado,
  fijar además una receta y toolchain reproducibles;
- resolver padding según el criterio anterior en un adaptador aislado;
- fijar versiones exactas de runtime/tokenizer y un entorno que satisfaga el
  lock; el `.venv` actualmente observado no lo satisface;
- confirmar estáticamente los prefijos, truncamiento 512/right, mean pooling
  enmascarado y L2 del contrato congelado.

La inspección estática, los manifests de archivos, la revisión de dependencias
y la compatibilidad funcional son evidencias distintas; ninguna sustituye las
otras. No declarar `VERIFIED` por nombre de modelo, dimensión, tamaño de
archivo o hash local aislado.

## Cierre posible sin inferencia ni cambios de entorno

La revisión read-only no permite cerrar ambos candidatos:

- **E5 identidad de artefactos:** sí. Los sidecars enlazan localmente el
  commit candidato y los hashes, y la API pública confirma repo, commit, ruta,
  tamaño y LFS SHA-256; la identidad del archivo ONNX/tokenizer publicado sí
  está cerrada. No está documentada la receta/toolchain para reconstruir ese
  ONNX, pero esto no impide identificar ni consumir el artefacto publicado.
- **E5 tipo numérico del artefacto:** sí, estáticamente: todos los tensores
  flotantes inspeccionados y el output son `FLOAT` y el único Cast termina en
  `FLOAT`. No se probó ejecución ni precisión numérica efectiva de kernels.
- **E5 dependencias:** el `requirements.lock` fija paquetes/versiones/hashes
  para un objetivo Python 3.10, pero el `.venv` existente usa Python 3.12.3,
  NumPy 2.5.2, ONNX Runtime 1.29.0 y Tokenizers 0.23.1, por lo que no satisface
  los pins E5. `uv` 0.12.10 está disponible en ese entorno. El lock no fija
  patch de Python ni demuestra el wheel/plataforma seleccionado; tampoco están
  decididas la política efectiva de CPU/hilos ni las restricciones de recursos.
- **E5 padding:** el reproductor ya está preparado, pero producir un manifest
  requiere volver a cargar ONNX e inferir sobre fixtures sintéticos. No se hizo
  aquí y requiere autorización puntual explícita.
- **Qwen:** no. No hay artefactos locales/manifests, y tampoco está fijado el
  lock de runtime necesario para verificar la pareja.

Por ello, el contrato de compatibilidad continúa congelado solo como
especificación metodológica/técnica candidata; ninguno de los contratos se
considera todavía vinculante para ejecución.

## Condiciones de cierre

Qwen-R o E5-R solo podrá pasar a `VERIFIED` cuando toda la evidencia de su
familia esté registrada y las pruebas autorizadas de compatibilidad hayan
pasado. El gate global no se cierra hasta que ambos candidatos estén
`VERIFIED`; cualquier desviación del contrato congelado exige proponer una
nueva versión antes de continuar.

Incluso tras cerrar este gate:

- la autorización de ejecución seguirá pendiente de una decisión explícita y
  separada;
- el gate de Blind Pool Generation seguirá `PENDING`;
- no se autoriza construir índices, generar candidatos ni medir consumo;
- producción, índices históricos y `v1.0-elite` permanecen intactos.

## Registro actual de decisión

```text
Qwen artifact binding/runtime          BLOCKED
E5 upstream file identity              VERIFIED
E5 static ONNX FP32                    VERIFIED
E5 locked runtime execution            BLOCKED
E5 padding compatibility               PARTIALLY_RESOLVED_LOCAL_MASKING
Compatibility specification           FROZEN; unchanged
Prerequisites resolution gate         OPEN_PARTIALLY_RESOLVED
Model execution                       NOT AUTHORIZED
Blind Pool Generation                  PENDING
Vector-space IDs                      NOT ISSUED
Production/index                      UNCHANGED
```

Nota: el estado parcial de provenance E5 se basa en sidecars locales cuyo
commit coincide con la revisión candidata y cuyos ETags coinciden con los
hashes; la API pública del Hub confirma además el repositorio, rutas y LFS
SHA-256 de los dos archivos publicados. La identidad de esos archivos sí está
verificada y la inspección estática confirma FP32 del grafo; runtime y padding
reproducible permanecen pendientes.
La autorización de ejecución sigue requiriendo una decisión explícita y
separada. El JSON de freeze conserva el estado del momento en que se congeló;
este registro posterior no cambia el contrato ni el estado de autorización.
