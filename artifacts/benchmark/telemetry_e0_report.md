# 📊 TELEMETRÍA E0 — BENCHMARK DE SELECCIÓN DE EVIDENCIA (31.114 CHUNKS)

- **Fecha de Ejecución:** 2026-09-12T17:37:00.601100+00:00
- **Corpus Real Indexado:** 31,114 chunks en SQLite KnowledgeStore
- **Total de Consultas Evaluadas:** 35 queries (7 categorías curriculares)
- **Tiempo Total de Benchmark:** 0.51s (Promedio: 12.69 ms/query)

## 1. Métricas Globales E0 (Línea Base Real)

| Parámetro / Métrica | Valor Obtenido E0 | Umbral Objetivo V1.2 | Estado Epistémico |
|---|---|---|---|
| **Supported Answer Coverage (SAC)** | **92.5%** | $\ge 85\%$ | ✅ Superado |
| **Epistemic Evidence Utilization (EEU)** | **0.542** | $> 0.75$ | ℹ️ Baseline E0 |
| **Diversidad de Fuentes** | **1.8 fuentes/query** | $\ge 2.5$ | ⚠️ Concentrado |
| **Tasa de Redundancia Cruzada** | **6.1%** | $< 10\%$ | ✅ Baja Redundancia |
| **Precisión de Abstención (OOD)** | **100.0%** | $100\%$ | ✅ Fail-Closed Impecable |
| **Latencia de Recuperación Híbrida** | **12.69 ms** | $< 50$ ms | ⚡ Óptimo (Two-Stage FTS5+Dense) |

## 2. Desglose Detallado por Categoría Curricular

| Categoría | Consultas | Cobertura (SAC) | EEU | Diversidad Fuentes | Redundancia | Latencia |
|---|---|---|---|---|---|---|
| `contradiction   ` | 3 | 95.7% | 0.50 | 2.0 | 0.0% | 16.31 ms |
| `cross_curricular` | 3 | 82.4% | 0.50 | 3.0 | 0.0% | 10.24 ms |
| `missing         ` | 4 | 100.0% | 1.00 | 2.5 | 0.0% | 8.92 ms |
| `multi_source    ` | 6 | 85.0% | 0.50 | 1.8 | 0.0% | 12.14 ms |
| `multi_topic     ` | 6 | 90.3% | 0.43 | 2.0 | 27.4% | 10.96 ms |
| `redundancy      ` | 5 | 95.3% | 0.50 | 1.2 | 0.0% | 17.24 ms |
| `simple          ` | 8 | 96.7% | 0.48 | 1.1 | 6.2% | 13.01 ms |

## 3. Hallazgos Epistemológicos Críticos de la Fase A

1. **Rendimiento Two-Stage comprobado:** La combinación de pre-filtro FTS5 (~4ms) y re-ranking denso con embeddings (~5ms) permitió evaluar 35 preguntas complejas contra **31.114 chunks en menos de 1 segundo de CPU pura**.
2. **Promoción de Autoridad Operativa:** El caso Rosen (`rosen_matematicas_discretas`) promovió automáticamente a `goodrich_dsa_python` y `joyanes_fundamentos` sin emitir falsos vacíos de evidencia.
3. **Abstención Honesta (Fail-Closed):** Las 4 consultas fuera de dominio (Kubernetes, Active Directory GPO, Computación Cuántica, Exploit x86) alcanzaron **100% de abstención legítima**, arrojando EEU de 1.0 y evitando alucinaciones ontológicas.
4. **Foco para la Fase B:** Las contradicciones documentadas (Joyanes vs Ramalho en mutabilidad, Joyanes vs Goodrich en listas dinámicas) recuperaron con éxito los dos polos opuestos de evidencia en los top-3 ranks.

---
*Reporte de Telemetría E0 generado automáticamente por TALOS Benchmark Suite.*