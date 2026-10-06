# 📦 Especificación del Formato: TALOS Corpus Bundle v1 (`talos-corpus-bundle-v1`)

**Estado:** Especificación Normativa de Intercambio  
**Versión de Schema:** `talos-corpus-bundle-v1` (CP114-PRE v4.1)  
**Propósito:** Artefacto de transferencia autocontenido, determinista y criptográficamente auditable entre el entorno de procesamiento (Colab / cloud) y el núcleo de autoridad local de TALOS.

---

## 1. Taxonomía de Responsabilidades por Archivo

Para erradicar cualquier ambigüedad epistémica, cada archivo del bundle tiene una categoría ontológica y una responsabilidad inequívoca:

| Archivo | Categoría de Información | Responsabilidad y Garantía |
| :--- | :--- | :--- |
| `manifest.json` | **SOURCE FACT / PROCESSING METADATA** | Inventario exhaustivo de fuentes, hashes SHA-256 de entrada y versiones de extractores. |
| `pipeline.json` | **PROCESSING METADATA** | Configuración determinista, hiperparámetros, bibliotecas, hardware y semillas de ejecución. |
| `documents.jsonl` | **SOURCE FACT / STRUCTURAL OUTLINE** | Registro por documento: títulos, conteo de páginas, esquema de secciones (AST). |
| `chunks.jsonl` | **SOURCE FACT (Texto e Identidad)** | Unidades canónicas de evidencia textual, tipo de bloque (`table`, `code`, `paragraph`, `composite`) y jerarquía. |
| `metadata.jsonl` | **METADATA SEPARATION** | Estricta separación entre atributos de la fuente (`source_metadata`) y anotaciones sintéticas (`generated_metadata`). |
| `provenance.jsonl` | **PROVENANCE** | Linaje criptográfico exacto: hash SHA-256 del PDF original, páginas, bounding box (`bbox = null` si no está disponible) y extractor. |
| `embeddings/` | **EMBEDDING CONTRACT & VECTORS** | Especificación del contrato de espacio vectorial y vectores serializados por chunk. |
| `diagnostics.json` | **DIAGNOSTIC** | Métricas empíricas de calidad estructural, tasas de preservación, alertas OCR y fragmentación léxica. |
| `benchmark.json` | **BENCHMARK** | Medición comparativa en consultas canónicas de control bajo la taxonomía CP113-R1. |
| `checksums.sha256` | **INVARIANT CRIPTOGRÁFICO** | Sumas SHA-256 de cada archivo individual del bundle para validación de transporte. |
| `README.md` | **DOCUMENTAL / RESUMEN** | Resumen legible por humanos para inspección rápida previa al gate. |

> [!IMPORTANT]
> **Separación Epistémica de Evidencia:**  
> Los campos de `generated_metadata` (ej. resúmenes generados por LLM, palabras clave sintéticas) **NUNCA** constituyen evidencia documental primaria de cátedra ni pueden usarse como sustitutos del texto de origen en la verificación de verdad C1/C5.

---

## 2. Convención Canónica de Identidad

### 2.1 Identidad de Documento
La identidad de un documento fuente se define exclusivamente por su hash criptográfico SHA-256 de 64 caracteres en minúsculas:
```text
document_id = "sha256:<64_hex_chars>"
```
Ejemplo:
```text
document_id = "sha256:76e248a6297405e32be963dbdfc8d5dc745e1ea160533fc1bb8114f260383187"
```

### 2.2 Identidad de Chunk
La identidad canónica de cada chunk es determinista, inmutable y reproducible dentro de una versión dada del pipeline:
```text
chunk_id = "<document_id>:p<page_start>-<page_end>:c<stable_index>"
```
Reglas:
- Si el chunk reside en una sola página: `p<page>-<page>` o `p<page>` según estabilidad de representación; la norma canónica estandarizada para rango inclusivo es:
  `sha256:76e2...3187:p137-137:c0004` (o para chunks multipágina: `sha256:76e2...3187:p137-138:c0005`).
- El `<stable_index>` es un entero secuencial formateado con ceros a la izquierda (ej. `c0004`), estable frente a ejecuciones idénticas del pipeline.
- **Prohibición:** Los hashes truncados (ej. `sha256:76e248a62974:...`) quedan prohibidos como identificador canónico en el bundle; pueden utilizarse únicamente como representación auxiliar en logs visuales legibles por humanos.

---

## 3. Especificación de Schemas y Formatos

### 3.1 `manifest.json`
```json
{
  "schema": "talos-corpus-bundle-v1",
  "bundle_id": "bundle_20261002T193000Z_pilot",
  "created_at": "2026-10-02T19:30:00Z",
  "pipeline_version": "1.5.0-exp",
  "extractor": {
    "candidate": "docling_structural",
    "version": "2.0.1",
    "layout_parser": "tableformer_v2"
  },
  "sources": [
    {
      "document_id": "sha256:76e248a6297405e32be963dbdfc8d5dc745e1ea160533fc1bb8114f260383187",
      "filename": "Operating Systems - Internals and Design Principles 7th.pdf",
      "sha256": "76e248a6297405e32be963dbdfc8d5dc745e1ea160533fc1bb8114f260383187",
      "byte_size": 7090215,
      "page_count": 820,
      "chunks_count": 3120
    }
  ]
}
```

### 3.2 `chunks.jsonl`
```json
{
  "chunk_id": "sha256:76e248a6297405e32be963dbdfc8d5dc745e1ea160533fc1bb8114f260383187:p137-137:c0004",
  "document_id": "sha256:76e248a6297405e32be963dbdfc8d5dc745e1ea160533fc1bb8114f260383187",
  "page_start": 137,
  "page_end": 137,
  "heading_path": ["Chapter 3 Process Description and Control", "3.2 Process States", "Reasons for Process Creation"],
  "block_type": "table",
  "content": "| Reason for Creation | Description |\n| :--- | :--- |\n| New batch job | The OS is provided with a batch job control stream... |\n| Interactive log-on | A user at a terminal logs on to the system. |\n| Created by OS | The OS creates a process to perform a service... |",
  "char_count": 1280,
  "token_count": 285
}
```

### 3.3 `metadata.jsonl` (Separación de Autoridad)
```json
{
  "chunk_id": "sha256:76e248a6297405e32be963dbdfc8d5dc745e1ea160533fc1bb8114f260383187:p137-137:c0004",
  "source_metadata": {
    "book_title": "Operating Systems: Internals and Design Principles",
    "author": "William Stallings",
    "edition": "7th",
    "subject": "Operating Systems",
    "is_table": true,
    "table_rows": 4,
    "table_cols": 2
  },
  "generated_metadata": {
    "generated": true,
    "generator_model": "Qwen/Qwen2.5-7B-Instruct",
    "keywords": ["process creation", "batch job", "spawning"],
    "summary": "Tabla con las causas fundamentales de creación de procesos en sistemas operativos."
  }
}
```

### 3.4 `provenance.jsonl`
Garantiza el linaje inverso desde cualquier afirmación/cita hasta el documento original:
```text
chunk ──► source PDF (SHA-256) ──► page ──► block/region ──► extractor ──► pipeline_version
```
```json
{
  "chunk_id": "sha256:76e248a6297405e32be963dbdfc8d5dc745e1ea160533fc1bb8114f260383187:p137-137:c0004",
  "source_sha256": "76e248a6297405e32be963dbdfc8d5dc745e1ea160533fc1bb8114f260383187",
  "source_filename": "Operating Systems - Internals and Design Principles 7th.pdf",
  "page_number": 137,
  "bbox": [54.0, 120.5, 480.0, 310.2],
  "extractor": "docling_structural",
  "extraction_timestamp": "2026-10-02T19:35:12Z",
  "pipeline_version": "1.5.0-exp"
}
```

> [!CAUTION]
> **Política de Bounding Box (`bbox`):**  
> Si el motor extractor no genera coordenadas espaciales precisas para un bloque de texto, el campo debe ser explícitamente:
> ```json
> "bbox": null
> ```
> **Queda estrictamente prohibido inventar o estimar coordenadas ficticias.** La ausencia de bounding box debe registrarse de forma transparente y honesta.

### 3.5 `embeddings/embedding_contract.json`
Define el contrato exacto de espacio vectorial. Qwen3-Embedding-0.6B es el **contrato histórico de referencia**; cualquier modelo alternativo (ej. BGE-M3) debe registrar sus parámetros exactos sin asumir compatibilidad de espacio con modelos distintos:
```json
{
  "schema": "talos-embedding-contract-v1",
  "model_id": "Qwen/Qwen3-Embedding-0.6B",
  "model_revision": "main",
  "provider_id": "sentence_transformers",
  "dimensions": 1024,
  "max_length": 512,
  "normalize_l2": true,
  "pooling": "mean",
  "dtype": "float16",
  "prefixes": {
    "query": "",
    "passage": ""
  }
}
```

---

## 4. Invariantes del Bundle

1. **Integridad Criptográfica:** Todo bundle debe incluir `checksums.sha256`. Cualquier discrepancia de hash provoca el rechazo inmediato e incondicional en el Import Gate.
2. **Indivisibilidad de Estructuras Atómicas:** Las tablas y bloques de código deben mantenerse íntegros en una única unidad de evidencia siempre que sea físicamente viable dentro del presupuesto de contexto, evitando fracturas por conteo arbitrario de caracteres.
3. **Identidad Canónica Exhaustiva:** Los identificadores `document_id` y `chunk_id` deben contener el hash SHA-256 completo de 64 caracteres.
4. **Fail-Closed de Procedencia:** Todo chunk en `chunks.jsonl` debe tener un registro exactamente correspondiente en `provenance.jsonl` que enlace con un PDF custodiado en `fuentes/`.
