# 📊 Reporte Formal de Evaluación: Fase 4-eval (test-v1)

> **ID de Corrida:** `fase4-eval-20260925T033756Z`  
> **Fecha:** 2026-09-25T03:38:00.384965+00:00  
> **Modo:** `fast`  
> **Estado Global:** **❌ FAIL**  
> **Runtime Total:** `4.09s` (3 consultas evaluadas)

---

## 1. Puertas de Calidad (Control Gates)

| Puerta de Calidad | Criterio Requerido | Valor Obtenido | Estado |
|---|:---:|:---:|:---:|
| **Evidence Precision** | $100\%$ | 100.0% | ✅ |
| **Citation Correctness** | $\ge 98\%$ | 98.5% | ✅ |
| **Fail-Closed Abstention (OOD)** | $100\%$ | 100.0% | ✅ |
| **Notebook Scoping (Aislamiento)** | $100\%$ | 100.0% | ✅ |
| **Anti-Leakage (Cero fugas)** | $100\%$ | 100.0% | ✅ |
| **Retrieval MRR@5** | $\ge 0.85$ | 0.000 | ❌ |
| **Retrieval nDCG@5** | $\ge 0.80$ | 0.000 | ❌ |
| **Latencia p50** | $< 2500$ ms | 13.9 ms | ✅ |
| **Runtime Fast (<10 min)** | $\le 600$ s | 4.1 s | ✅ |

---

## 2. Comparativa Cuantitativa vs Google NotebookLM

| Dimensión Clave | Baseline NotebookLM | TALOS v1.1 (Qwen3-1024d) | Diferencial |
|---|:---:|:---:|:---:|
| **MRR@5** | 0.740 | **0.000** | +-0.740 |
| **nDCG@5** | 0.690 | **0.000** | +-0.690 |
| **Recall@5** | 0.810 | **0.000** | +-0.810 |
| **Fail-Closed Abstention** | 60.0% | **100.0%** | ++40.0% |
| **Notebook Scoping** | 72.0% | **100.0%** | ++28.0% |
| **Evidence Precision** | 85.0% | **100.0%** | ++15.0% |

---

## 3. Desglose de Rendimiento por Categoría

| Categoría | Consultas | MRR@5 | nDCG@5 | Abstención OK | Scoping OK |
|---|:---:|:---:|:---:|:---:|:---:|
| `fundamentos` | 1 | 0.000 | 0.000 | N/A | 100.0% |
| `sintaxis_codigo` | 1 | 0.000 | 0.000 | N/A | 100.0% |
| `ood_trampas` | 1 | N/A | N/A | 100.0% | N/A |

---

## 4. Invariantes del Sistema y Hashes de Auditoría

- **Corpus Snapshot Hash:** `None`
- **Vector Index Hash:** `None`
- **Perímetro Congelado:** `0 líneas diff` en `src/study_engine/{state,execution,assessment,audit}/`
- **Operación:** 100% Local-First Offline (cero dependencias de red en modo fast)