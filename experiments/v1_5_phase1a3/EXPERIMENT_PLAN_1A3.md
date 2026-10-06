# TALOS V1.5 — FASE 1A.3: PLAN EXPERIMENTAL FORMAL
## AISLAMIENTO DE EMBEDDING Y EFECTO DE REPRESENTACIÓN DE INPUT

**Fecha:** 2026-10-05  
**Fase:** TALOS V1.5 — Fase 1A.3 (Embedding vs. Input Isolation)  
**Dependencia:** FASE 1A.2 — `POST_ADJUDICATION_AUDIT_V2.md`  
**Run de Referencia:** `run_1a2_pilot_joyanes_20261005_061144`  
**Estado:** `PLAN_APPROVED — EXECUTION_PHASE_1_PREPARATION`  
**Entorno de Ejecución Pesada:** Google Colab (Colab-First Obligatorio)  
**Gobernanza:** `DATABASE_CHANGES = 0` | `V1_RUNTIME_MODIFIED = FALSE` | `PRODUCTION_SELECTION = NOT_PERFORMED`

---

## 0. Propósito Científico y Pregunta de Investigación

La Fase 1A.2 resolvió de forma concluyente la pregunta descriptiva del piloto nativo:
*¿Qué ocurrió cuando los modelos operaron sobre sus representaciones nativas de extracción y chunking?*

La Fase 1A.3 tiene por objeto responder a la pregunta causal y factorial aislada:
> **"Cuando Qwen, E5 y BGE reciben exactamente la misma representación textual y tienen exactamente el mismo candidate pool, ¿persisten las diferencias de retrieval observadas?"**

---

## 1. Baseline Humano Oficial Congelado (`NATIVE_HUMAN_BASELINE`)

Los 176 juicios humanos adjudicados en Fase 1A.2 sobre las 22 consultas quedan formalmente congelados como fuente de verdad inmutable en [`experiments/v1_5_phase1a3/NATIVE_HUMAN_BASELINE.json`](NATIVE_HUMAN_BASELINE.json) (SHA-256: `a70ea23571f7509e4f15b8ac96ff3749bd311e0078d3be0eeda61406a1c346b1`):

| Pipeline Ciego | Experimento Real | Configuración Técnica | High | Partial | Low | None | Relevant | Sufficient | Calidad Contexto |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Gamma** | `EXP-CHK-01` | PyMuPDF + C1 + Qwen | 3 | 3 | 4 | 12 | **6/22 (27.3%)** | **0/22 (0.0%)** | Clean/Frag |
| **Delta** | `EXP-EXT-02` | PyMuPDF + C1 + Qwen (DUP) | 3 | 3 | 4 | 12 | **6/22 (27.3%)** | **0/22 (0.0%)** | Idéntico a Gamma |
| **Eta** | `EXP-EXT-01` | pypdf + C1 + Qwen | 3 | 3 | 4 | 12 | **6/22 (27.3%)** | **0/22 (0.0%)** | Idéntico a Gamma |
| **Beta** | `EXP-CHK-03` | PyMuPDF + C3 + Qwen | 1 | 1 | 6 | 14 | **2/22 (9.1%)** | **1/22 (4.5%)** | Clean |
| **Alpha** | `EXP-CHK-02` | PyMuPDF + C2 + Qwen | 1 | 0 | 2 | 19 | **1/22 (4.5%)** | **1/22 (4.5%)** | Clean |
| **Theta** | `EXP-EMB-01` | PyMuPDF + C2 + Qwen (DUP) | 1 | 0 | 2 | 19 | **1/22 (4.5%)** | **1/22 (4.5%)** | Idéntico a Alpha |
| **Zeta** | `EXP-EMB-03` | PyMuPDF + C2 + BGE-M3 | 0 | 1 | 3 | 18 | **1/22 (4.5%)** | **0/22 (0.0%)** | Clean |
| **Epsilon** | `EXP-EMB-02` | PyMuPDF + C2 + E5-small | 0 | 0 | 3 | 19 | **0/22 (0.0%)** | **0/22 (0.0%)** | Fragmented |

### Duplicados Confirmados:
- `Gamma == Delta`: 0 discrepancias humanas en 22 casos (100% concordancia).
- `Alpha == Theta`: 0 discrepancias humanas en 22 casos (100% concordancia).
- En cualquier análisis factorial posterior, cada par duplicado cuenta como una única observación técnica ($N=1$).

---

## 2. Condición H (`C2-HARMONIZED`): Especificación Técnica

Se construye un dataset derivado denominado `C2-HARMONIZED` a partir exclusivamente de los **64 chunks** de C2 (`PyMuPDF + C2`).

### 2.1 Presupuesto Común y Regla del Texto Común
- **Presupuesto Estricto:** `COMMON_BUDGET = 512 tokens`.
- **Regla Determinista:** Para cada chunk $i \in \{1..64\}$, la cadena armonizada $H_i$ es el prefijo de caracteres más largo del texto original de C2 que cumpla simultáneamente:
  $$\text{Tokens}_{\text{Qwen}}(H_i) \le 512 \quad \land \quad \text{Tokens}_{\text{E5}}(H_i) \le 512 \quad \land \quad \text{Tokens}_{\text{BGE}}(H_i) \le 512$$
- **Byte-Equivalencia:** $H_i$ es idéntica carácter por carácter y byte por byte para los tres modelos.
- **Prohibiciones de Procesamiento:** Queda terminantemente prohibido resumir, reescribir, reordenar, limpiar o inyectar metadatos artificiales en $H_i$.
- **Cero Truncamiento Implícito:** Los modelos recibirán $H_i$ sin que se active el truncamiento silencioso del motor de inferencia (`implicit_truncation = FALSE`). Si un modelo trunca, la fase se declara `BLOCKED`.

---

## 3. Pipeline de Ejecución Colab-First

Toda la ejecución pesada se delega a Google Colab mediante el bundle `drive_upload_1a3/`:

1. **Input Fixture:**
   - 64 chunks C2 originales (`chunks_c2_source.jsonl`).
   - 22 benchmark queries canónicas (`benchmark_queries_pilot.json`).
2. **Modelos Evaluados en Colab:**
   - `Qwen/Qwen3-Embedding-0.6B` (dim 1024)
   - `intfloat/multilingual-e5-small` (dim 384)
   - `BAAI/bge-m3` (dim 1024)
3. **Retrieval Exacto:**
   - Búsqueda exhaustiva por producto interno / similitud coseno sobre los 64 vectores normalizados.
   - Prohibido el uso de índices aproximados (ANN) o reordenadores (cross-encoders).
4. **Artefactos a Producir en Colab:**
   - `C2_HARMONIZED_MANIFEST.jsonl`
   - `EMBEDDING_RUN_MANIFEST.json`
   - `retrieval_harmonized.json` (Top-10 por modelo para las 22 consultas)
   - `negative_control_results.json` (Resultados aislados para `Q1A2-37` y `Q1A2-38`)

---

## 4. Matriz de Comparaciones Factoriales

### 4.1 Comparación Primaria (Cross-Model bajo Input Idéntico)
- `H-QWEN` vs. `H-E5` vs. `H-BGE` sobre los mismos 64 chunks $H_i$.
- Métricas: Top-1 identity, Jaccard@3, Jaccard@5, Jaccard@10, Exact Top-10 match, desplazamiento promedio de ranking.
- **Objetivo:** Aislar el comportamiento intrínseco del modelo de embedding cuando se anula por completo la disparidad de contexto y truncamiento.

### 4.2 Comparación Secundaria (Within-Model: Native vs. Harmonized)
- `Native Qwen` vs. `H-Qwen`
- `Native E5` vs. `H-E5`
- `Native BGE` vs. `H-BGE`
- **Objetivo:** Medir cuantitativamente la sensibilidad de cada arquitectura vectorial a la reducción de contexto (`WITHIN_MODEL_INPUT_DIFFERENCE`).

---

## 5. Protocolo de Evaluación Humana Incremental (`BLIND_ADJUDICATION_V3`)

- **Principio:** No se re-adjudica el baseline nativo congelado (176 celdas ya resueltas).
- **Alcance V3:** 22 consultas $\times$ 3 modelos armonizados = **66 celdas Top-1**.
- **Enmascaramiento Ciego:** Asignación aleatoria de etiquetas ciegas (`Pipeline_Sigma`, `Pipeline_Tau`, `Pipeline_Upsilon`) con semilla criptográfica aislada en `key/pipeline_mapping_v3.json`.
- **Rúbrica:** Aplicación de la misma rúbrica estándar (Relevance 0..2, Sufficiency 0..2, Grounding, Context Quality).

---

## 6. Prohibiciones Metodológicas Expresas

1. `PRODUCTION_SELECTION = NOT_PERFORMED`: Ningún modelo será seleccionado para reemplazar el baseline de producción de TALOS V1.
2. `COSINE_INTERPRETATION = DIAGNOSTIC_ONLY`: Se prohíbe inferir mayor calidad a partir de valores absolutos de coseno entre modelos diferentes.
3. `LOCAL_PROCESSING = FORBIDDEN`: La vectorización y tokenización masiva no se ejecutan en el runtime local.
