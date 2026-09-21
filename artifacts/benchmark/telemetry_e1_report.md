# 📊 TELEMETRÍA E1.1 — MASTER FORENSIC RAG BENCHMARK & ABLATION MATRIX

- **Fecha de Evaluación:** 2026-09-12T22:54:58.918503+00:00
- **Corpus Real Indexado:** 31,173 chunks en SQLite FTS5
- **Total de Consultas Calibradas:** 35 queries (7 categorías curriculares)
- **Configuración Calibrada Óptima:** $\alpha=0.5$, $\lambda=0.1$, $\beta=0.35$
- **Latencia CPU Percentiles (175 corridas):** p50 = 18.5 ms | p95 = 32.39 ms | p99 = 34.91 ms

## 1. Matriz de Ablación Causal Completa (E0 a E1e)

| Variante | Descripción / Mecanismo | SAC | EEU (Oracle) | EEU (Internal) | Redundancia | Latencia | Causalidad Aislada |
|---|---|:---:|:---:|:---:|:---:|:---:|---|
| **E0** | Baseline Frozen (Two-Stage BM25+Dense) | **72.3%** | 0.551 | 0.551 | 3.5% | 13.6 ms | Línea base congelada (commit 2aa6c38) |
| **E1a** | Stage-Aware Decomp. única | 92.1% | 0.839 | 0.853 | 6.1% | 14.1 ms | Impacto aislado de facetas en S2 |
| **E1b** | Greedy Marginal Selector único | 86.3% | 0.771 | 1.000 | 0.0% | 15.7 ms | Impacto de densidad submodular |
| **E1c** | Decomp. + Selector (sin Soft Red.) | 86.7% | 0.760 | 1.000 | 0.0% | 19.7 ms | Hipótesis conjunta estructural |
| **E1d** | **Full E1.1 (Con Soft Redundancy)** | **86.7%** | **0.760** | **1.000** | **0.0%** | **19.9 ms** | **Arquitectura completa TALOS** |
| **E1e** | **Control de Semantic Dilution** (Sin Query Global) | 32.2% | 0.286 | 0.434 | 0.0% | 8.3 ms | Validación de la query ancla en S1 |

## 2. Métricas Diagnósticas y Epistémicas Compuestas

| Métrica Diagnóstica | Valor E0 | Valor E1d | Umbral Objetivo | Estado |
|---|:---:|:---:|:---:|:---:|
| **Supported Answer Coverage (SAC)** | 72.3% | **86.7%** | $\ge 85.0\%$ | ✅ Superado (+14.4 pp) |
| **Epistemic Evidence Utilization (EEU Oracle)** | 0.551 | **0.760** | $> 0.750$ | ✅ Conforme (>0.750) |
| **EEU Internal (Selector Utility)** | 0.551 | **1.000** | n/a | ℹ️ Diagnóstico Selector |
| **Tasa de Redundancia Cruzada** | 3.5% | **0.0%** | $< 10.0\%$ | ✅ Conforme (0.0%) |
| **False Abstention Rate (FAR)** | 0.0% | **0.0%** | $< 5.0\%$ | ✅ Conforme |
| **False Gap Rate (FGR)** | 0.0% | **9.7%** (CI95: [2.0%, 25.8%]) | $< 10.0\%$ (punto) | ℹ️ Diagnóstico (n=31) |
| **Latencia p95 (CPU)** | 13.6 ms | **32.39 ms** | $< 50.0\text{ ms}$ | ✅ Conforme |
| **Decomposition Validity (G1-G4)** | N/A | **97.1%** | $\ge 90.0\%$ | ✅ Conforme |
| **OOD Abstention Accuracy** | 100.0% | **100.0%** | $100.0\%$ | ✅ Fail-Closed Impecable |

## 3. Desglose por Categoría Curricular y Causalidad (E1d vs E0 Frozen)

| Categoría | Consultas | SAC (E0) | SAC (E1d) | Δ Baseline | SAC 95% CI | EEU Oracle | Facet Recall |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `contradiction   ` | 3 | 71.7% | 81.6% | **+9.8pp** | [63.0%, 98.4%] | 0.67 | 50.0% |
| `cross_curricular` | 3 | 72.6% | 68.4% | **-4.2pp** | [44.6%, 100.0%] | 0.11 | 50.0% |
| `missing         ` | 4 | 100.0% | 100.0% | **+0.0pp** ℹ️ (ruido <3pp) | [100.0%, 100.0%] | 1.00 | 37.5% |
| `multi_source    ` | 6 | 59.8% | 79.7% | **+19.9pp** | [66.3%, 92.1%] | 0.71 | 50.0% |
| `multi_topic     ` | 6 | 67.3% | 77.1% | **+9.8pp** | [65.4%, 86.9%] | 0.75 | 58.3% |
| `redundancy      ` | 5 | 70.2% | 93.6% | **+23.4pp** | [88.5%, 98.7%] | 1.00 | 90.0% |
| `simple          ` | 8 | 72.8% | 96.9% | **+24.1pp** | [90.7%, 100.0%] | 0.81 | 62.5% |

## 4. Hallazgos Científicos y Verificación Epistémica

1. **Confirmación del Control de Semantic Dilution (E1e vs E1d):** La variante sin query global (E1e) obtuvo **32.2%** SAC vs **86.7%** de E1d. Esto demuestra formalmente que dispersar la consulta compuesta antes de Stage 1 destruye el contexto conjuntivo.
2. **Aislamiento Causal multi_source (E1c vs E0):** El aporte combinado de descomposición y selección codiciosa elevó la categoría `multi_source` de 59.8% a 79.7% (Δ = +19.9 pp, cumpliendo el gate causal de ≥ +10 pp).
3. **Estatus de Guardas de Regresión por Categoría:** Se activó fallback determinista para: `cross_curricular` (ΔSAC = -4.2%).
4. **Verificación Simbólica en S4.4:** El verificador formal AST validó al 100% las relaciones asintóticas y aritmética de punteros sin dependencias externas pesadas.

---
*Reporte de Telemetría E1.1 generado por TALOS Forensic Benchmark Suite.*