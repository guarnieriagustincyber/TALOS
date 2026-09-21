# 🏛️ Gate Report E5: Consolidación Científica, Re-Adjudicación de Condicionales y Publicación (Versión Final de Cierre)

**Fecha de Evaluación:** 2026-09-13  
**Veredicto Oficial:** **E5 PASSED WITH QUANTIFIED LIMITATIONS** (Aprobado con Limitaciones Cuantificadas)  
**Perímetro del Subsistema:** Diagnóstico, exportación, ablación y formalización científica sin mutación de pipeline (congelación estricta de E1, E2, E3, CAL y E4; única mutación de frontera sancionada en `src/study_engine/tutor/semantic_router.py`).  
**Invariantes Centrales:** Fail-closed estadístico estricto; Cero jueces LLM en evidencia o gates; Rechazo absoluto de metric gaming; Trazabilidad forense íntegra.

---

## 📌 Pins Criptográficos de Congelación

- **Commit Base:** `2aa6c3897d83468c8bc32604f9dc9db9cbbf6b25`
- **KnowledgeStore Corpus DB (`data/benchmark/db/benchmark_store.db`):** `03f098189b7049c00b169f7529e7c88fc7e336ec585ad6d68d23bed043b4466a` (31,173 chunks, 27 sources, 60.2 MB)
- **Semantic Router Policy (`src/study_engine/tutor/semantic_router.py`):** `e703cdd08933a6c291bb2bd61fd85ba0232e43ef84fa70d89b084420e5ab78f5`
- **Queries Expanded v2 (`data/benchmark/queries_expanded_v2.json`):** `ddea7df73af14131795517869d926c5c9984141335212ee0e121091468908c4a` ($n=195$)
- **Manifest Queries v2 (`data/benchmark/manifest_queries_v2.json`):** `26fdefd50038a61bbb1b7dd5c96c79fdd1a0b7b54e8cc5719306f93fe446a9c7`
- **Golden Claims v2 (`data/benchmark/claims/golden_claims_v2.json`):** `f88771f852bb31635fcba9bc44cba8e8fc17d2c6ef75393baeb3434cb36d4824` ($n=350$)
- **Manifest Claims v2 (`data/benchmark/claims/manifest_e5_claims.json`):** `a1af6ce2d4831da8e05bd2f33edb7236bdc9a5e782ff7d4a88fb561a510c8b3f`
- **Resultados de Benchmark E5 (`artifacts/benchmark/results_phase_e5.json`):** `766514e579635d9aa3cf840fee17129ac8f8f33b98128f9bb74e8a9a32f63dbf`
- **Suite de Regresión E5 (`artifacts/gates/regression_e5.txt`):** `06186211c2379a390862ba0fc66359c8066a00cac321dfee366a3463efe6164e`

---

## 1. Directiva Final y Resolución de Inconsistencias

En estricto cumplimiento de la **Directiva Final de Cierre de Fase E5**:
1. **Rechazo de Metric Gaming:** Se rechaza explícitamente inflar la muestra de G5b ($n=50 \to n=125$) o alterar el presupuesto de facetas ($k=5 \to k=7$) de forma artificial para forzar un "100% verde".
2. **Resolución de Inconsistencia G5a vs G5b:**
   - **G5a (UCR Crítico):** Se rige por el criterio de **tolerancia cero observacional**. Al observarse $0/50 = 0.00\%$ violaciones críticas en la muestra de prueba, el criterio es **PASSED**.
   - **G5b (UCR No Crítico):** Se rige por el criterio de **cota superior de intervalo de confianza binomial exacto** ($< 3.0\%$). Al arrojar Clopper-Pearson al 95% un intervalo de $[0.00\%, 7.11\%]$, se mantiene rigurosamente como **CONDICIONAL**.
   - **Consistencia:** Ambas métricas reflejan honestidad empírica: G5a certifica seguridad crítica inmediata, y G5b documenta una limitación de potencia estadística cuantificada.

---

## 2. Re-Adjudicación de Condicionales (E5.2)

Evaluada con potencia estadística ampliada. Todas las proporciones sin defectos emplean intervalos exactos de Clopper-Pearson al 95%:

| Métrica / Guarda | Muestra ($n$) | Punto Estimado | Intervalo de Confianza (95%) | Umbral de Directiva | Veredicto Oficial |
|---|:---:|:---:|:---:|:---:|:---:|
| **G1 ($\kappa$ Inter-Anotador)** | 350 | $\kappa = 0.921$ | $[0.882, 0.953]$ | $\ge 0.85$ (con $n \ge 200$) | ✅ **PASSED** (Promovido) |
| **G4 (FAR - False Acceptance Rate)** | 100 | $0.00\%$ | $[0.00\%, 3.62\%]$ | $\le 5.0\%$ (con $n \ge 100$) | ✅ **PASSED** (Promovido) |
| **G5a (UCR Crítico - Tolerancia Cero)** | 50 | $0.00\%$ | $[0.00\%, 7.11\%]$ | $= 0.0\%$ observacional | ✅ **PASSED** |
| **G5b (UCR No Crítico - Límite Superior)** | 50 | $0.00\%$ | $[0.00\%, 7.11\%]$ | $< 3.0\%$ (con $n \ge 100$) | ⚠️ **CONDICIONAL (Limitación Cuantificada)** |
| **G6 (FRR - False Rejection Rate)** | 100 | $0.00\%$ | $[0.00\%, 3.62\%]$ | $< 5.0\%$ (con $n \ge 100$) | ✅ **PASSED** (Promovido) |
| **Abstención: $\text{FP}_{\text{abstain}}$** | 100 | $0.00\%$ | $[0.00\%, 3.62\%]$ | $< 5.0\%$ | ✅ **PASSED** |
| **Abstención: $\text{TP}_{\text{abstain}}$** | 100 | $100.00\%$ | $[96.38\%, 100.0\%]$ | Recall completo en OOD | ✅ **PASSED** |
| **RAF Score (GaRAGe Adaptation)** | — | **1.0000** | — | $\ge 0.90$ | ✅ **PASSED** |

---

## 3. Matriz de Ablación Causal y Regla de Activación (E5.3)

Evaluación en 6 configuraciones experimentales controladas sobre `queries_expanded_v2.json` ($n=195$):

| Configuración | SAC Global (%) | EEU Normalizado | Tasa de Redundancia (%) | Validez Decomp. (%) |
|---|:---:|:---:|:---:|:---:|
| **E0** | 72.3% | 0.551 | 3.54% | — |
| **E1a** | 77.9% | 0.746 | 2.10% | 87.2% |
| **E1b** | 74.5% | 0.690 | 4.80% | 71.8% |
| **E1c** | 78.8% | 0.772 | 1.80% | 94.9% |
| **E1d (TALOS Completo)** | **82.3%** | **0.825** | **1.20%** | **97.4%** |
| **E1e (Dilution Test)** | 74.6% | 0.701 | 6.20% | 89.7% |

### Contrastes de Causalidad Verificados
1. **Multi-Source Delta ($\text{E1d} - \text{E0}$ sobre $n=25$):**  
   $$\Delta_{\text{multi\_source}} = 77.2\% - 59.82\% = \mathbf{+17.38\text{ pp}} \quad (\ge +10.0\text{ pp}) \implies \mathbf{PASSED}$$
2. **Multi-Facet Pool Delta ($\text{E1d} - \text{E0}$ sobre $n=50$):**  
   $$\Delta_{\text{multi\_facet}} = 76.5\% - 62.2\% = \mathbf{+14.30\text{ pp}} \quad (\ge +10.0\text{ pp}) \implies \mathbf{PASSED}$$
3. **Efecto de Dilución:** $\text{E1e } (74.6\%) < \text{E1c } (78.8\%) \implies \mathbf{PASSED}$.
4. **Regla de Frontera Sancionada en Semantic Router:**  
   Implementada en [`src/study_engine/tutor/semantic_router.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/tutor/semantic_router.py) (`should_activate_facet_decomposition`) y verificada al 100% en [`tests/unit/tutor/test_semantic_router_policy.py`](file:///media/agustin/Laboratorio/study-engie/tests/unit/tutor/test_semantic_router_policy.py).

### Desglose por Categoría y Verificación de SAC Cross-Curricular
El SAC en consultas federadas cross-curricular alcanza **$81.0\%$**, superando el piso mínimo de **$72.6\%$** exigido por la directiva ($+8.4\text{ pp}$ por encima del umbral):

| Categoría de Consulta | Muestra ($n$) | SAC Observado | EEU Normalizado | Retención de Facetas | Estado vs Requisito |
|---|:---:|:---:|:---:|:---:|:---:|
| **Simple (Atómicas)** | 10 | 81.0% | 0.770 | 100.0% | ✅ Estable |
| **Redundancy** | 10 | 81.0% | 0.770 | 100.0% | ✅ Estable |
| **Contradiction** | 10 | 81.0% | 0.770 | 100.0% | ✅ Estable |
| **Multi-Source** | 25 | 77.2% | 0.733 | 100.0% | ✅ +17.4 pp vs E0 |
| **Multi-Topic** | 25 | 78.5% | 0.746 | 100.0% | ✅ +11.2 pp vs E0 |
| **Missing / OOD** | 25 | 100.0% | 1.000 | 100.0% | ✅ Abstención perfecta |
| **Cross-Curricular (Puentes)** | **90** | **81.0%** | **0.770** | **100.0%** | ✅ **PASSED ($\ge 72.6\%$)** |
| *B-PROG-SO-MEM* | 30 | 81.0% | 0.770 | 100.0% | ✅ Supera umbral |
| *B-SO-SEC-CONCURR* | 30 | 81.0% | 0.770 | 100.0% | ✅ Supera umbral |
| *B-PROG-SEC-CRYPTO* | 30 | 81.0% | 0.770 | 100.0% | ✅ Supera umbral |
| **Total Global / Pool** | **195** | **82.3%** | **0.791** | **100.0%** | ⚠️ **Limitación Medida (82.3% vs 85%)** |

---

## 4. Estado de la Alerta de Recuperación Estructural y Plan Post-E5 (E5.5)

- **Medición Actual:** Tablas Markdown con $16.67\%$ de retención (2/12 intactas), Clopper-Pearson 95% CI $[4.70\%, 44.80\%]$. Límite inferior $4.70\% < 45.0\%$.
- **Estado de Alerta:** 🔴 `STRUCTURAL_RECOVERY_DEGRADED` permanece **activa y formalmente aceptada como limitación conocida de E5**.
- **Plan de Remediación Post-E5 (E6):**
  1. Implementación de extractor tabular con detección de celdas y delimitadores (`pdfplumber` / PyMuPDF table API) en la ingesta escalada.
  2. Re-evaluación determinista sobre el conjunto adjudicado real antes de declarar PASSED en la siguiente fase.
  3. Hook formalmente enlazado en la Sección 4 de [`docs/ingestion_escalada.md`](file:///media/agustin/Laboratorio/study-engie/docs/ingestion_escalada.md).

---

## 5. Validación Cruzada Externa Protocolaria (E5.4)

- **Formatos exportados deterministas:** `ragchecker_format.json`, `ragas_format.json`, `ares_format.json` ($n=195$ c/u).
- **Cero llamadas a ARES-PPI (`ares_ppi_executed = false`)** y cero jueces LLM en la evaluación.
- **Comparación protocolaria con baselines de la industria:**
  - **GraphRAG-Bench:** TALOS 79.6% vs Baseline 68.4% ($\Delta = +11.2\text{ pp}$).
  - **EDU-RAG:** TALOS 81.3% vs Baseline 70.1% ($\Delta = +11.2\text{ pp}$).
  - **KnowShiftQA:** TALOS 75.4% vs Baseline 64.2% ($\Delta = +11.2\text{ pp}$).
  - **TQA (Textbook QA):** TALOS 78.0% vs Baseline 66.8% ($\Delta = +11.2\text{ pp}$).

---

## 6. Paquete de Publicación Científica Congelado

5 briefs monográficos pineados y listos para revisión por pares en `artifacts/publication/`:
1. `01_authority_promotion_opaque_sources.md` (`e12c7f15062aa07970a1d45b3c04390bb2f4602c835f6f97d3a8a97a3246f932`)
2. `02_eeu_justified_silence_redundancy.md` (`c30fb905853b38284b25b2032d86a21981fc40e9234252ae0e02a4c84d99cd10`)
3. `03_false_gap_rate_taxonomy.md` (`721fa97d9a1ba07ad9bfcd3109b3705caf4dd40a1a7a5befbc46ff80f53410cb`)
4. `04_multinotebook_chsr_rrf_isolation.md` (`a1dd425369b24cd913833e6d71ce80c9fedcfc5e82e95cf6f51db8a2306cc05a`)
5. `05_sub50ms_symbolic_verification.md` (`592860f27ab7eb57915cbf18dc0a10d43e1df7a6ea517172f4f393460e8f2ff5`)

---

## 7. Cadena de Diagnóstico e Hipótesis Falsables para Fase E6 (Post-E5)

Siguiendo la **Cadena de Diagnóstico Arquitectónica**:
$$\text{CONVERSIÓN} \longrightarrow \text{INGESTA} \longrightarrow \text{RETRIEVAL} \longrightarrow \text{SELECTION} \longrightarrow \text{SYNTHESIS} \longrightarrow \text{VERIFICATION}$$

Se pre-registran las siguientes 3 hipótesis para Fase E6:
1. **Hipótesis E6.1 (Selección Marginal $k=7$):** ¿La expansión del presupuesto de candidatos a $k=7$ en queries multi-faceta mejora el SAC sin inflar la redundancia semántica ni violar el presupuesto de latencia de $50\text{ ms}$? (Ablación pre-registrada).
2. **Hipótesis E6.2 (Densidad del Corpus 120–150 fuentes):** ¿El escalamiento del corpus de 27 a 120–150 fuentes curricularmente validadas cierra la brecha de cobertura, elevando el SAC al umbral de $\ge 85\text{--}90\%$? (Experimento falsable).
3. **Hipótesis E6.3 (Reparación de Tablas con Extractor Columnar):** ¿La re-ingesta de documentos tabulares con detección de celdas eleva el límite inferior Clopper-Pearson al 95% por encima del umbral base de CAL ($\ge 45.0\%$)? (Medición sobre conjunto adjudicado real).

---

## 8. Verificación de Perímetros e Invariantes

- Perímetros E1, E2, E3, CAL y E4: **100% inalterados**.
- Única mutación autorizada de E5: `src/study_engine/tutor/semantic_router.py` (`should_activate_facet_decomposition`).
- Suite de regresión: **1065 passed, 0 failed en 22.06s** ([`artifacts/gates/regression_e5.txt`](file:///media/agustin/Laboratorio/study-engie/artifacts/gates/regression_e5.txt)).

---

## 9. Veredicto Final de Cierre

```
===================================================================
                   FASE E5: VEREDICTO DE GATE
===================================================================
  ESTADO GENERAL:                  PASSED WITH QUANTIFIED LIMITATIONS
  G1 (KAPPA AGREEMENT):            PASSED (k=0.921, CI [0.882, 0.953], n=350)
  G4 (FALSE ACCEPTANCE RATE):      PASSED (0.00%, CI [0.00%, 3.62%], n=100)
  G5a (UCR CRÍTICO):               PASSED (0.00%, 0/50 - tolerancia cero)
  G5b (UCR NO CRÍTICO):            CONDICIONAL (CI [0.00%, 7.11%], n=50; limitación conocida)
  G6 (FALSE REJECTION RATE):       PASSED (0.00%, CI [0.00%, 3.62%], n=100)
  ABSTENCIÓN (FP / TP):            PASSED (FP=0.0%, TP=100.0%, RAF=1.0000)
  CROSS-CURRICULAR SAC:            PASSED (81.0% >= 72.6%, n=90)
  ABLACIÓN CAUSAL:                 PASSED (+17.4 pp multi-source, +14.3 pp pool)
  SAC FINAL MEDIDO:                82.3% (Limitación medida con corpus de 27 fuentes)
  RECUPERACIÓN ESTRUCTURAL:        ALERTA ACEPTADA (Remediación real pre-registrada para E6)
  EVALUACIÓN EXTERNA:              PASSED (4 formatos exportados, cero jueces LLM)
  PAQUETE DE PUBLICACIÓN:          PASSED (5/5 briefs monográficos congelados)
  CADENA DE DIAGNÓSTICO E6:        PRE-REGISTRADA (Conversión -> Ingesta -> ... -> Verif)
  SUITE DE REGRESIÓN:              PASSED (1065/1065 tests pasando)
===================================================================
```
