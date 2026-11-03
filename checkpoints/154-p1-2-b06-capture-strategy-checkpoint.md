# Checkpoint 154 — P1.2 B06 Capture Strategy

**Fecha:** 2026-10-08  
**Tipo:** checkpoint de continuidad y handoff  
**Alcance:** preservar decisiones, bloqueos, evidencia existente y próximo paso de B06; no resolver pendientes.

## Identidad del repositorio

```text
PATH = /media/agustin/Laboratorio/study-engie
BRANCH = talos-current-audit
HEAD = cc8acfae623f9d10c8366871470319786b6a7ca4
WORKTREE = deliberadamente dirty; no limpiar
```

El último estado conocido antes de este checkpoint registró 1895 entradas en
`git status --short` y el fingerprint
`c171a9f906805da016c7fe621cfc9e0af85b126febf51dd142bb1de559b0bc31`.
Ese mismo número y fingerprint se observaron antes y después de la operación
de reevaluación de estrategia, y nuevamente antes de crear este checkpoint.
El fingerprint es una observación del estado de `git status --short`, no un
sello criptográfico del repositorio completo.

## Estado B06

```text
B06-CONTRACT = COMPLETE
B06-IMPLEMENT = COMPLETE
B06-RUN = BLOCKED
P1.2 = BLOCKED
```

Test focal:

```text
tests/pedagogy/test_talos_vs_notebooklm_e2e.py::
test_p3_debug_query_abstains_without_sufficient_evidence_sse
```

Comportamiento contractual esperado:

```text
evidence_manifest:
  abstained = true
  trust_status = RELATED_INSUFFICIENT

abstention:
  abstention_code = QUERY_OUT_OF_SCOPE

stream termina en EOF
sin phase_start, phase_token, phase_complete ni error
```

El perfil canónico vigente `b06-snapshot-v1` sigue exigiendo
`knowledge_store.db`, `vector_store.db` y `student_state.db`. No se elimina ni
relaja ese requisito en este checkpoint.

## Adjudicación de captura segura

```text
P1.2.B06-SAFE-CAPTURE = BLOCKED-IMMUTABILITY
```

Resultados de experimentos previos realizados únicamente con datos sintéticos:

- `Connection.backup()` capturó el estado lógico confirmado en WAL y pasó
  `integrity_check`, pero cambió el contenido del SHM sintético. **REJECTED.**
- `immutable=1` no cambió los archivos observados, pero no mostró el esquema ni
  el estado que residían exclusivamente en WAL. **REJECTED.**
- Copiar secuencialmente DB/WAL/SHM funcionó en el caso quieto, pero no demostró
  atomicidad ante escrituras concurrentes. **REJECTED.**

No existe un mecanismo demostrado que satisfaga simultáneamente coherencia
WAL, cero mutación y atomicidad. El entorno previamente inspeccionado era
ext4 sobre `/dev/sda2`; no se verificó un backend de snapshot atómico
disponible. No repetir esta investigación salvo que aparezca infraestructura
nueva y verificable.

## Reevaluación de estrategia

```text
P1.2.B06-CAPTURE-STRATEGY-REASSESSMENT = COMPLETE
FINAL CLASSIFICATION = BLOCKED-EVIDENCE-GAP
B06 DEPENDENCY TYPE = MIXTA
```

La prueba afirma un resultado lógico/funcional del endpoint; no exige igualdad
byte a byte de las DB. El estado actual solo es históricamente indispensable
si la certificación pretende referirse exactamente a ese estado. Aunque el
test no consume directamente toda la información de las tres DB, el perfil
vigente las exige y no está autorizado a cambiarse aquí.

Existen referencias históricas de hashes, pero un hash identifica un estado y
no reconstruye su contenido lógico. Está documentada una discrepancia para
`vector_store.db`:

```text
CP119 / CP121 = 013a2462…
CP127          = d6d9f8c8…
```

No se adjudica cuál representa el estado correcto sin evidencia adicional.
Referencias: [119-corpus-processing-decision.md](./119-corpus-processing-decision.md),
[121-data-execution.md](./121-data-execution.md) y
[127-v1-release-integrity.md](./127-v1-release-integrity.md).

## Reconstrucción y Colab

El proyecto contempla Colab como entorno de cómputo para trabajo posterior,
no como autoridad de certificación:

```text
COLAB RECONSTRUCTION = NO DETERMINABLE COMO CANÓNICA
COLAB = ENTORNO DE CÓMPUTO, NO AUTORIDAD DE CERTIFICACIÓN
```

Material de reconstrucción parcial identificado:

- `data/benchmark/sources`
- `scripts/ingest_corpus.py`
- `config/l3_authorization_manifest.json`
- `requirements.lock`
- `docs/DEPENDENCY_REPRODUCIBILITY.md`
- `docs/TALOS_CORPUS_BUNDLE_V1.md`
- notebooks Colab y JSONL de embeddings existentes

Esto no demuestra que pueda reconstruirse exactamente el estado actual de
`fase0-soc`.

### Bloqueador de reproducibilidad: contratos vectoriales

Se observaron contratos distintos, sin adjudicación sobre cuál es correcto:

```text
data/colab/embedding_contract.json = Qwen 0.6B, 1024 dimensiones
scripts/reindex_embeddings.py    = Qwen 4B, 2560 dimensiones
proveedor ONNX local             = E5-small, 384 dimensiones
```

No está demostrado cuál corresponde al estado histórico, qué modelo y
tokenizer generaron las filas actuales, qué espacio vectorial utilizó B06 ni
qué combinación podría reproducirse canónicamente. No corregir ni escoger
entre esos contratos en este checkpoint.

## Evidence gaps abiertos

1. No existe snapshot/manifest/attestation que preserve la estructura lógica
   actual de las tres DB.
2. No existe inventario verificable completo del estado actual de `fase0-soc`.
3. No existe receipt de B06 vinculado a las identidades históricas de las DB.
4. No está demostrada la cobertura completa de los artefactos Colab.
5. Modelos, tokenizers y runtime de Colab no están fijados suficientemente
   para una reconstrucción canónica.
6. No está resuelta la correspondencia entre los contratos vectoriales.
7. No está demostrada la equivalencia entre el estado actual y uno
   reconstruido.

## Decisión pendiente y próximo paso

No elegir todavía entre:

```text
A — PRESERVE CURRENT STATE
B — RECONSTRUCT
C — HYBRID
```

La decisión pendiente es si B06 certificará el baseline actual o un nuevo
estado canónico reconstruido. Próxima directiva recomendada:

```text
P1.2.B06-RECONSTRUCTION-SPEC
```

Su objetivo será identificar entradas, transformaciones, modelos, tokenizers,
configuraciones, parámetros y artefactos requeridos para una reconstrucción
reproducible, y determinar primero si `RECONSTRUCTION-SUFFICIENT` o
`HISTORICAL STATE REQUIRED`. Solo después se decidirá si hace falta
infraestructura de snapshot.

## Límites de esta operación

Este checkpoint no abre DB/WAL/SHM, no crea snapshots, no ejecuta B06/B10,
release gate, P1.3 ni notebooks, no genera embeddings ni reconstruye DB, y no
modifica código o configuración de producto. No se hicieron operaciones Git
de staging, commit, reset, clean o checkout destructivo. El working tree
deliberadamente sucio se preservó.
