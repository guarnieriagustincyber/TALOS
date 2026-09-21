# GATE REPORT E1 — TALOS/KASIU
commit: 2aa6c3897d83468c8bc32604f9dc9db9cbbf6b25 | benchmark_store_sha256: 03f098189b7049c00b169f7529e7c88fc7e336ec585ad6d68d23bed043b4466a | seed: 42
hw: AMD Ryzen 5 5600GT (12 cores) / 14GB RAM | frozen_E0_definition: TwoStageRetriever(top_k_lexical=100, authority_bonus=0.15, relevance_floor=0.40, alpha_dense=0.50)

| criterion | observed | threshold | pass/fail | evidence_artifact |
|---|---|---|---|---|
| frozen_E0_definition | commit 2aa6c38 (SAC 72.3%, EEU 0.551) | única y re-runnable | pass | scripts/benchmark_phase_e1.py |
| SAC_global | 86.7% | ≥85% | pass | results_phase_e1.json#sac_global |
| SAC_multi_source | 79.7% | ≥82% | CONDICIONAL (Δ causal superado, punto pendiente E2) | ...#by_category.multi_source |
| SAC_multi_topic | 77.1% | ≥80% | CONDICIONAL (Δ causal superado, punto pendiente E2) | ...#by_category.multi_topic |
| EEU_oracle | 0.760 | >0.75 | pass | ...#eeu_oracle |
| EEU_internal | 1.000 | n/a (diagnóstico) | info | ...#eeu_internal |
| redundancy_rate | 0.0% | <10% | pass | ...#redundancy |
| OOD_abstention | 100.0% | =100% | pass | ...#ood |
| FAR | 0.0% | <5% | pass | ...#far |
| FGR_point / CI95_upper | 9.7% / 25.8% | point <10%; CI reportado | pass (diagnóstico) | ...#fgr_ci |
| retrieval_selection_p95 | 32.4 ms | <50 ms | pass | ...#latency_percentiles |
| E1c_minus_E0_multi_source | +19.9 pp | ≥+10 pp | pass | ...#ablation.by_category |
| E1e_vs_E1c | 32.2% < 86.7% (-54.5pp) | E1e < E1c | pass | ...#ablation |
| fallback_rule_installed | true (e1_category_policy.json) | true + test verde | pass | semantic_router.py + test |
| cross_curricular_post_guard | 68.4% (monolítico) | política activa post-guard | pass | data/curriculum/e1_category_policy.json |
| decomposition_fallback_sac | 100.0% | reportado sin degradación | pass | ...#fallback_subset |
| reproducibility | 03f098189b... (match) | matriz re-runnable desde commit | pass | checksums de artefactos |

---
## 🔬 Epistemic Notes on Gate Resolution

1. **Hallazgo A Resuelto (Definición E0 Única):** La línea base E0 queda formalmente congelada en `commit 2aa6c38` (SAC global 72.3%, EEU 0.551, multi_source 59.8%). El salto causal `E1c - E0` en `multi_source` es de **+19.9 pp**, superando holgadamente el criterio de +10 pp.
2. **Hallazgo B Resuelto (EEU No Circular):** `EEU_internal = 1.000` se declara como diagnóstico interno del selector. `EEU_oracle = 0.760` se computa independientemente contra fuentes esperadas y anclas de consulta, pasando el umbral exigente de `> 0.750`.
3. **Hallazgo C Resuelto (Subpotencia Estadística de FGR):** Con n=31 consultas in-domain y k=3 falsos gaps, la estimación puntual es **9.7% (< 10%)** y el intervalo exacto de Clopper-Pearson 95% es **[2.0%, 25.8%]**. Siguiendo el veredicto del co-diseño, FGR se declara formalmente como **diagnóstico** para este gate y se programará como criterio estricto en E2 con golden set ampliado (n ≥ 100).
4. **Hallazgo D Resuelto (Veredictos Condicionales Honestos):** Conforme al rigor del gate, `SAC_multi_source` (79.7% vs ≥82%) y `SAC_multi_topic` (77.1% vs ≥80%) se declaran formalmente como **CONDICIONAL**. Aunque superan con holgura los saltos causales sobre E0 (+19.9 pp y +9.8 pp), el punto absoluto final queda condicionado al presupuesto adaptativo de chunks en E2.
5. **Hallazgo E Resuelto (Decisión Arquitectónica E1a vs E1d):** Se ratifica **E1d** como la línea base conservadora oficial de TALOS para el cierre de E1 por garantizar 0.0% de redundancia cross-book. Se documenta que el costo de compresión (-5.4 pp vs E1a 92.1%) obedece a la rigidez de τ_admit=0.70 y K=8 fijo, pre-registrando para E2 la adopción de Adaptive-K (`clamp(2F+1, 4, 12)`) para alcanzar 90-94% de SAC.
6. **Hallazgo F Resuelto (Medición Post-Guard):** Se mide y reporta explícitamente `cross_curricular_post_guard` (68.4%), documentando la contención de degradación con el evento `REGRESSION_GUARD` registrado y persistido en `e1_category_policy.json`.
7. **Control de Semantic Dilution Confirmado:** La variante control E1e (sin query global en Stage 1) colapsa a **32.2% SAC** (-54.5 pp respecto a E1c/E1d), demostrando de forma contundente la necesidad del ancla global unificada.
8. **Rendimiento CPU Puro:** Latencia p95 de selección y recuperación medida en **32.3 ms** (< 50 ms) sobre 175 ejecuciones calientes.

---
*Gate Report formal emitido el 2026-09-12T22:54:58.918720+00:00 por TALOS/KASIU Benchmark Engine.*