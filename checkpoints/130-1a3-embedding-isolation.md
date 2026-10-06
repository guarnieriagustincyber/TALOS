# CHECKPOINT 130 — TALOS V1.5 FASE 1A.3: AISLAMIENTO DE EMBEDDING Y EFECTO DE REPRESENTACIÓN DE INPUT

**Fecha:** 2026-10-05  
**Fase:** TALOS V1.5 — Fase 1A.3 (Embedding Model Isolation vs. Input Representation Effect)  
**Tipo:** Ejecución Colab-First, Reconciliación Factorial, Adjudicación Humana V3 y Auditoría Causal  
**Subdominio:** Corpus Intelligence / Embedding Geometry / Causal Factor Isolation  
**Autoridad:** Directiva Operativa TALOS V1.5 — Fase 1A.3 / Antigravity Agent  
**Run de Referencia Nativo:** `run_1a2_pilot_joyanes_20261005_061144`  
**Referencia Documental:**
- `reports/v1_5_phase1/EMBEDDING_ISOLATION_AUDIT_V1.md`
- `experiments/v1_5_phase1a3/EXPERIMENT_PLAN_1A3.md`
- `experiments/v1_5_phase1a3/NATIVE_HUMAN_BASELINE.json`
- `experiments/v1_5_phase1a3/C2_HARMONIZED_MANIFEST.jsonl`
- `experiments/v1_5_phase1a3/retrieval_harmonized.json`
- `experiments/v1_5_phase1a3/native_vs_harmonized_reconciliation.json`
- `experiments/v1_5_phase1a3/negative_control_results.json`
- `experiments/v1_5_phase1a3/blind_adjudication_v3/`

---

## 1. ESTADO DE GOBERNANZA MULTIDIMENSIONAL

```text
FASE_1A3_STATUS = COMPLETE
NATIVE_HUMAN_BASELINE = VALID_AND_FROZEN (176 celdas, SHA-256 a70ea23571f7509e4f15b8ac96ff3749bd311e0078d3be0eeda61406a1c346b1)
EMBEDDING_MODEL_EFFECT = ISOLATED
INPUT_REPRESENTATION_EFFECT = OBSERVED
COMMON_INPUT_RETRIEVAL = COMPLETED
HUMAN_ADJUDICATION_V3 = EXECUTED (66 celdas Top-1 evaluadas a ciegas y desenmascaradas)
NEGATIVE_CONTROLS = EVALUATED_AND_ISOLATED (100% None en evaluación humana OOD)
PRODUCTION_SELECTION = NOT_PERFORMED
PRODUCTION_STATUS = UNCHANGED

LOCAL_HEAVY_INFERENCE = STRICTLY_PREVENTED
COLAB_GPU_INFERENCE = COMPLETED (NVIDIA TESLA T4)
DATABASE_CHANGES = 0
V1_RUNTIME_MODIFIED = FALSE
CORPUS_MODIFIED = FALSE
VECTOR_STORE_MODIFIED = FALSE
STUDENT_STATE_MODIFIED = FALSE
```

---

## 2. RESUMEN EJECUTIVO DE LA FASE 1A.3

El **Checkpoint 130** certifica formalmente la finalización del análisis experimental y la evaluación humana de la **Fase 1A.3**, resolviendo la confusión metodológica entre modelo de embedding y representación/truncamiento de entrada mediante la **Condición H (Harmonized Input)** ejecutada en Google Colab:

1. **Congelamiento de Baseline Nativo:** Se preservaron intactos los 176 juicios humanos de la Fase 1A.2 en `NATIVE_HUMAN_BASELINE.json`, ratificando la unicidad factorial de los duplicados `Gamma == Delta` y `Alpha == Theta`.
2. **Construcción Determinista de Condición H (`C2-HARMONIZED`):** Sobre los 64 chunks de C2, se impuso un presupuesto común estricto de <= 512 tokens para los tres tokenizers simultáneamente. 37 chunks fueron recortados por prefijo y 27 chunks quedaron inalterados. Se certificó `implicit_truncation = FALSE` (0/64) en los tres modelos y byte-equivalencia al 100%.
3. **Aislamiento del Efecto de Modelo (Resultado A Confirmado):** Bajo input exactamente idéntico, los modelos divergieron en su candidato Top-1 en el 72.7% a 86.4% de las consultas (coincidencia Top-1 de apenas 13.6% en Qwen vs E5, 18.2% en Qwen vs BGE, y 27.3% en E5 vs BGE). Jaccard@10 se ubicó entre 0.24 y 0.31. Se demuestra que las diferencias de retrieval no eran artefactos de truncamiento diferencial, sino que provienen de representaciones semánticas intrínsecamente divergentes.
4. **Medición del Efecto de Input / Interacción (Resultado C Confirmado):** Al comparar Native vs. Harmonized (`WITHIN_MODEL_INPUT_DIFFERENCE`), Qwen y BGE exhibieron una alta estabilidad en Top-1 (90.9% de retención, Jaccard@10 > 0.86), mientras que E5 cambió su candidato principal en el 27.3% de las consultas (Jaccard@10 = 0.76).
5. **Adjudicación Humana V3 Ejecutada y Desenmascarada:**
   - Evaluador: Adjudicador ciego estricto ($N=1$).
   - Llave desenmascarada: `Pipeline_Sigma` -> `H-QWEN`, `Pipeline_Tau` -> `H-E5`, `Pipeline_Upsilon` -> `H-BGE`.
   - Resultados de Relevancia Humana:
     * `EMB-HARM-QWEN`: **4 / 22 (18.2%) Relevante** (1 High, 3 Partial, 5 Low, 13 None) | **1 / 22 (4.5%) Suficiente** (`Q1A2-39`).
     * `EMB-HARM-BGE`: **3 / 22 (13.6%) Relevante** (1 High, 2 Partial, 2 Low, 17 None) | **0 / 22 (0.0%) Suficiente** (1 Parcialmente Suficiente en `Q1A2-12`).
     * `EMB-HARM-E5`: **2 / 22 (9.1%) Relevante** (0 High, 2 Partial, 3 Low, 17 None) | **0 / 22 (0.0%) Suficiente**.
   - Hallazgo Causal Crucial: La armonización común incrementó la tasa de relevancia humana en los tres modelos en comparación con el C2 Nativo (+13.7% en Qwen, +9.1% en BGE, +9.1% en E5) al eliminar la dilución semántica y el truncamiento de cola; sin embargo, **la jerarquía de calidad relativa (Qwen > BGE > E5) permaneció intacta**.
6. **Invarianza de Controles Negativos:** En `Q1A2-37` y `Q1A2-38`, los tres modelos recuperaron los mismos chunks que en nativo. El suelo anisotrópico de E5 (>0.824) persistió idéntico bajo Condición H, demostrando que la falta de rango dinámico de E5 es una propiedad geométrica intrínseca independiente de la longitud del contexto. La evaluación humana adjudicó 100% `None` a todos los casos OOD.

---

## 3. MATRIZ COMPARATIVA DE CALIDAD HUMANA (NATIVE VS. HARMONIZED C2)

| Pipeline / Tratamiento | Configuración | High | Partial | Low | None | Relevante (High+Part) | Suficiente (Estricto) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Qwen3-0.6B (Nativo C2)** | `Alpha` / `Theta` | 1 | 0 | 2 | 19 | **1 / 22 (4.5%)** | **1 / 22 (4.5%)** |
| **Qwen3-0.6B (Harmonized H)** | `Pipeline_Sigma` | 1 | 3 | 5 | 13 | **4 / 22 (18.2%)** | **1 / 22 (4.5%)** |
| **BAAI/bge-m3 (Nativo C2)** | `Zeta` | 0 | 1 | 3 | 18 | **1 / 22 (4.5%)** | **0 / 22 (0.0%)** |
| **BAAI/bge-m3 (Harmonized H)** | `Pipeline_Upsilon` | 1 | 2 | 2 | 17 | **3 / 22 (13.6%)** | **0 / 22 (0.0%)** |
| **multilingual-e5-small (Nativo C2)** | `Epsilon` | 0 | 0 | 3 | 19 | **0 / 22 (0.0%)** | **0 / 22 (0.0%)** |
| **multilingual-e5-small (Harmonized H)** | `Pipeline_Tau` | 0 | 2 | 3 | 17 | **2 / 22 (9.1%)** | **0 / 22 (0.0%)** |

---

## 4. DICTAMEN DE CIERRE DE CHECKPOINT

```text
TALOS V1.5 — PHASE 1A.3

PHASE STATUS:
COMPLETE

NATIVE HUMAN BASELINE:
VALID (176 cells frozen, SHA-256 a70ea23571f7509e4f15b8ac96ff3749bd311e0078d3be0eeda61406a1c346b1)

EMBEDDING MODEL EFFECT:
ISOLATED (Cross-model Top-1 agreement under identical input is only 13.6% to 27.3%; Jaccard@10 <= 0.313)

INPUT REPRESENTATION EFFECT:
OBSERVED (Within-model Top-1 stability is 90.9% for Qwen and BGE, but drops to 72.7% for E5; interaction verified; input harmonization improves human relevance across all models by eliminating dilution and tail truncation)

COMMON-INPUT RETRIEVAL:
COMPLETED (64 C2-Harmonized chunks, <=512 tokens common budget, zero implicit truncation across all 3 models)

HUMAN ADJUDICATION V3:
EXECUTED (66 Top-1 candidate cells evaluated blindly; H-Qwen 4/22 relevant [1 suff], H-BGE 3/22 relevant [0 suff, 1 part-suff], H-E5 2/22 relevant [0 suff])

NEGATIVE CONTROLS:
EVALUATED_AND_ISOLATED (Identical Top-1 chunks retrieved under Condition H; E5 anisotropy floor >0.824 invariant to input trimming; 100% human rating None on OOD cases)

CAUSAL CLAIMS:
ONLY EXPLICITLY SUPPORTED CLAIMS (Confirmed: intrinsic embedding geometries differ under identical input; interaction with input length observed; cross-model absolute cosine comparison prohibited; input harmonization improves relevance but preserves relative model hierarchy)

PRODUCTION SELECTION:
NOT_PERFORMED

REMAINING UNCERTAINTIES:
- Impact of multi-page context expansion (ContextPack) when decoupling precision chunking from context retrieval.
- Generalizability to larger corpus slices (Tanenbaum and full Joyanes 1600+ pages).

NEXT AUTHORIZED STEP:
PHASE_1A_FINAL_SYNTHESIS_AND_REPORTING
```
