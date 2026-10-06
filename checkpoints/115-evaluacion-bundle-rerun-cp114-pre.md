# CP115-R1 — Corrección de Gobernanza del Rerun CP114-PRE v4.2 y Bloqueo de Selección Prematura

**Tipo:** Auditoría de Artefactos de Extracción + Evaluación de Import Gate + Bloqueo de Selección Prematura  
**Subdominio:** Corpus Intelligence / Ingestión Pre-V1  
**Precondición:** CP114-PRE v4.2 Rerun = COMPLETED  
**Integridad de Datos:** `DATABASE_CHANGES = 0`  
- `BASELINE_KNOWLEDGE_DB_SHA256 = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (`data/web_state/knowledge_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_VECTOR_DB_SHA256    = 013a2462e6de6ca7cf13443338e44b7795dce4b2f7f6117827bd2ccadd0c568f` (`data/web_state/vector_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_STUDENT_DB_SHA256   = f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` (`data/web_state/student_state.db` READ-ONLY / UNCHANGED)  
- `BASELINE_DATE                = 2026-10-03T17:40:00-03:00`  

**Estado Canónico Registrado:**
```text
TECHNICAL_PIPELINE_VALIDATION = PASS

SOURCE_TRACEABILITY = PASS

COMPARATIVE_PAGE_COVERAGE = PASS
# baseline y B/C/D = 1.623 páginas

VECTOR_CONTRACT_VALIDATION = PASS

STRUCTURAL_DIAGNOSTICS = AVAILABLE

STRUCTURAL_GOLDEN_SET = NOT_AVAILABLE

RETRIEVAL_EXECUTION = PASS
# las consultas exploratorias pudieron ejecutarse

EXPLORATORY_COMPARISON = AVAILABLE

CP113_R1_ORACLE = NOT_AVAILABLE_IN_COLAB

CP113_R1_OFFICIAL_STATUS = BLOCKED

CP113_R1_ADJUDICATION = PENDING

CANDIDATE_SELECTION = NOT_AUTHORIZED

HUMAN_ACCEPTANCE = PENDING

PRODUCTION_IMPORT = FORBIDDEN

PRODUCTION_STATUS = UNCHANGED
```

---

## 0. Resumen Ejecutivo

La ejecución controlada de **CP114-PRE v4.2 Rerun** en Google Colab (GPU Tesla T4) produjo el bundle canónico:

`reports/talos_corpus_bundle_20261003T162052Z.zip` (74,09 MB / SHA-256: `137586fe3ba99685774cc9804794d596baa2cf021234a8272a38e3eb62960e4a`).

El rerun resolvió de manera demostrable el problema de comparabilidad de la corrida anterior al ejecutar el **baseline histórico `pypdf` sobre las 1.623 páginas completas** (9.426 chunks), igualando la cobertura de las estrategias B (4.265 chunks), C (2.405 chunks) y D (1.736 chunks).

Sin embargo, el benchmark oficial CP113-R1 **no pudo ejecutarse** debido a que `benchmark_oracle.json` no estuvo disponible dentro del entorno de Colab. En consecuencia, el Import Gate opera bajo **Fail-Closed estricto**:
* `CP113_R1_OFFICIAL_STATUS = BLOCKED`.
* Se prohíbe declarar ganadores, seleccionar candidatos o importar ninguna representación a producción.
* Las consultas de control se clasifican rigurosamente como `NON_OFFICIAL_EXPLORATORY_RESULT`.

---

## 1. Verificación Criptográfica y de Transporte (Niveles 1, 2 y 3)

1. **Checksums Criptográficos:**
   - 30 archivos contenidos en el bundle verificados contra `checksums.sha256`.
   - Coincidencia: **30 / 30 (100% OK)**.
2. **Esquemas y Alineación de Registros:**
   - Cumplimiento de `talos-corpus-bundle-v1`.
   - **Alineación 1:1:1:1 estricta por candidato:**
     - `baseline`: 9.426 chunks = 9.426 metadatos = 9.426 provenance = 9.426 vectores.
     - `strategy_b`: 4.265 chunks = 4.265 metadatos = 4.265 provenance = 4.265 vectores.
     - `strategy_c`: 2.405 chunks = 2.405 metadatos = 2.405 provenance = 2.405 vectores.
     - `strategy_d`: 1.736 chunks = 1.736 metadatos = 1.736 provenance = 1.736 vectores.
   - Total de vectores generados y certificados: **17.832 vectores** (1024d, L2 normalizados, pooling `lasttoken`).
3. **Trazabilidad de Fuentes:**
   - Hashes SHA-256 de los 3 PDFs canónicos coincidentes al 100% con los custodiados en `fuentes/`.

---

## 2. Diagnóstico Estructural Comparativo (STRUCTURAL_DIAGNOSTICS)

La evidencia estructural sobre las 1.623 páginas completas arrojó los siguientes datos empíricos:

| Dimensión / Métrica | Baseline Histórico (`pypdf` Completo) | Estrategia B (Estructural Corto) | Estrategia C (Estructural Medio) | Estrategia D (Estructural Amplio) |
| :--- | :--- | :--- | :--- | :--- |
| **Páginas Procesadas** | **1.623 págs (100%)** | **1.623 págs (100%)** | **1.623 págs (100%)** | **1.623 págs (100%)** |
| **Total de Chunks** | 9.426 | 4.265 | 2.405 | 1.736 |
| **Tamaño Medio (chars)** | 430,2 | 1.011,8 | 1.795,9 | 2.488,8 |
| **Mediana (chars)** | 459,0 | 884,0 | 1.673,0 | 2.466,0 |
| **P10 / P90 (chars)** | 329,0 / 494,0 | 511,0 / 1.031,0 | 896,0 / 1.835,0 | 679,0 / 2.658,0 |
| **Tablas Detectadas** | 0 estructuradas (planas rotas) | **391 estructuradas** | **391 estructuradas** | **391 estructuradas** |
| **Integridad de Tablas** | N/A | **93,35%** | **93,35%** | **93,35%** |
| **Bloques de Código** | 0 sintácticos | **1.486 sintácticos** | **1.486 sintácticos** | **1.486 sintácticos** |
| **Cobertura de Headings** | **0,00%** (Texto plano) | **99,91%** | **99,88%** | **99,88%** |
| **Fragmentación Léxica** | **42,90%** | **0,66%** | **1,08%** | **1,56%** |

* **Evidencia Diagnóstica Observada:**
  - El baseline histórico presenta una fragmentación léxica medida del 42,90% de sus chunks a lo largo de todo el corpus y carece de reconocimiento de tablas y jerarquía sintáctica.
  - Las estrategias estructurales (B, C, D) detectaron 391 tablas estructuradas y 1.486 bloques de código con cobertura de headings de ~99,9%.
  - La fragmentación léxica medida fue de 0,66% en B, 1,08% en C y 1,56% en D.
  - Estos datos permanecen catalogados estrictamente como `STRUCTURAL_DIAGNOSTICS` y no constituyen adjudicación global de calidad.

---

## 3. Retrieval Execution y Comparación Exploratoria (NON_OFFICIAL_EXPLORATORY_RESULT)

```text
Status:
RETRIEVAL_EXECUTION = PASS
EXPLORATORY_COMPARISON = AVAILABLE
OFFICIAL_CP113_R1 = BLOCKED
HUMAN_ADJUDICATION = PENDING
```

* **Similitud Top-1 Exploratoria:**
  - `baseline`: 0,5684
  - `strategy_b`: 0,5878
  - `strategy_c`: 0,5456
  - `strategy_d`: 0,5323
* **Declaración Normativa:** Strategy B mostró mejores valores de similitud Top-1 que el baseline en las cuatro consultas exploratorias ejecutadas, pero este resultado no constituye adjudicación CP113-R1.
* Ningún candidato está validado ni aprobado oficialmente por CP113-R1.

---

## 4. Auditoría de Outlier (47.627 caracteres)

* **Ubicación:** Joyanes Aguilar, Página 15 (`block_type: table`).
* **Causa Raíz:** Índice General (Tabla de Contenidos) de 25 páginas agrupado por Docling como una única tabla Markdown.
* **Diagnóstico Formal:**
  ```text
  CHUNKING_OUTLIER_STATUS = ISSUE_FOUND
  OUTLIER_HANDLING = DIAGNOSTIC_ONLY
  OUTLIER_RESOLUTION = PENDING
  ```
* **Hechos Técnicos:**
  1. El bloque estructural fue detectado por el extractor.
  2. Fue preservado íntegramente en el bundle para auditoría técnica.
  3. El chunker actual lo trató como unidad atómica indivisible.
  4. Supera ampliamente el límite de contexto efectivo del embedding (512 tokens / ~2.000 chars).
  5. El modelo Qwen3 lo truncó durante la vectorización.
  6. Todavía no existe una solución validada para este caso (diferida a TALOS V1.5).

---

## 5. Inmutabilidad de Producción

Se certificó mediante SHA-256 que las bases de datos de producción permanecen estrictamente inmutadas (`DATABASE_CHANGES = 0`):
- `data/web_state/knowledge_store.db`: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (UNCHANGED)
- `data/web_state/vector_store.db`:    `013a2462e6de6ca7cf13443338e44b7795dce4b2f7f6117827bd2ccadd0c568f` (UNCHANGED)
- `data/web_state/student_state.db`:   `f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` (UNCHANGED)

---

## 6. Decisión Humana — No Disponible Todavía

```text
DECISIÓN HUMANA — NO DISPONIBLE TODAVÍA

Actualmente ninguna representación está autorizada para selección o importación.

El rerun demostró comparabilidad estructural y generó evidencia exploratoria útil.

Sin embargo, el benchmark oficial CP113-R1 permanece bloqueado por ausencia del oracle en el entorno de ejecución y las adjudicaciones humanas todavía están pendientes.

Por lo tanto:

- Strategy B = CANDIDATE / NOT_SELECTED
- Strategy C = CANDIDATE / NOT_SELECTED
- Strategy D = CANDIDATE / NOT_SELECTED
- Baseline = EXISTING PRODUCTION REPRESENTATION
- Import = FORBIDDEN
```

---

## 7. Próximo Paso Requerido

```text
NEXT REQUIRED ACTION:

Obtener / hacer accesible el fixture oficial:
data/benchmark/benchmark_oracle.json

y ejecutar el benchmark oficial sobre los candidatos YA GENERADOS:

baseline
strategy_b
strategy_c
strategy_d
```

* **Reglas para la Próxima Evaluación:**
  - No volver a extraer los PDFs.
  - No volver a generar embeddings.
  - No volver a ejecutar Docling.
  - No volver a ejecutar pypdf.
  - Reutilizar los candidatos ya generados en `reports/talos_corpus_bundle_20261003T162052Z.zip`.
  - No iniciar las adjudicaciones humanas hasta que el oráculo oficial esté resuelto y evaluado.
