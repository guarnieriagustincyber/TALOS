# TALOS V1.5 — INGESTION INTELLIGENCE LAB
## INFORME CANÓNICO DE AUDITORÍA Y PREFLIGHT DE PROBE-1 (ADAPTIVE STRUCTURAL ROUTING)

**Versión:** 1.0.1-canonical  
**Fecha:** 2026-10-05  
**Fase:** Ingestion Intelligence Lab (v2.0) — PROBE-1  
**Tipo de Documento:** INFORME DE AUDITORÍA DE PRE-SELLADO Y PREFLIGHT  
**Predecesor Canónico:** Checkpoint 148 (`reports/v1_5_phase1/PROBE_0_EXECUTION_AUDIT_REPORT.md`)  
**Autoridad:** Directiva Canónica v1.0.1 (Resolución C01–C12)  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`  
**Estado:** **`PROBE_1_DESIGN = COMPLETE | PROBE_1_PREFLIGHT = PASSED | PROBE_1_SEAL = READY_FOR_SEAL | PROBE_1_EXECUTION = NOT_STARTED`**  

---

## 1. RESUMEN EJECUTIVO

En cumplimiento estricto de la **Directiva Final de Corrección y Pre-Sellado v1.0.1**, se ejecutó la auditoría metodológica exhaustiva de la especificación técnica de **PROBE-1: Adaptive Structural Routing**. Se verificaron formalmente los doce controles de rigor (**C01 a C12**), asegurando la total erradicación de fuga de datos (*leakage*), la desvinculación epistémica entre el gold standard y las herramientas evaluadas, la operacionalización matemática de las features de inspección rápida y el blindaje criptográfico de las bases de datos productivas.

```text
==================================================================================================
DICTAMEN GLOBAL DE AUDITORÍA DE PREFLIGHT — PROBE-1
==================================================================================================
DISEÑO METODOLÓGICO             = COMPLETO Y FORMALIZADO (10 Documentos Normativos)
CONTROLES C01–C12               = 12/12 SATISFECHOS Y AUDITADOS (Ledger Cerrado)
PARTICIÓN DEV / TEST            = 19 DEV / 19 TEST (Disjunto, Semilla 42, Zero Leakage)
ROUTER STATUS                   = SPECIFICATION_FROZEN (Pre-Calibración en DEV)
BENCHMARK STATUS                = UNVERIFIED (Retirado de claims confirmados, C10)
PROBE-0 ROLE                    = DEVELOPMENT_REFERENCE / HYPOTHESIS_GENERATION (C08)
ALCANCE DE GENERALIZACIÓN       = ACOTADO A CAPÍTULO 2 DE JOYANES (C09)
EXIT GATE DEFINIDO              = PASS / PARTIAL / FAIL / INCONCLUSIVE
AISLAMIENTO DE PRODUCCIÓN       = 100% INTACTO (DATABASE_CHANGES = 0)
EJECUCIÓN EXPERIMENTAL          = ESTRICTAMENTE NO INICIADA (NOT_STARTED)
==================================================================================================
```

---

## 2. AUDITORÍA DE LOS 16 REQUISITOS METODOLÓGICOS (SECCIÓN 42)

### 2.1. Pregunta Científica Principal
*¿Puede un conjunto de señales estructurales y sintácticas observables en $< 10	ext{ ms}$ predecir cuándo una página se beneficia materialmente de Docling v2, logrando un trade-off óptimo de calidad y costo frente al extractor lineal rápido?*

### 2.2. Hipótesis Preregistradas
* **H1 (Valor Selectivo de Docling):** Docling aporta beneficio material ($\Delta \ge 1.0$) en páginas complejas sin degradación severa en otras dimensiones.
* **H2 (Routing Determinista):** Una política local model-free detecta páginas complejas con $	ext{Recall} \ge 90\%$.
* **H3 (Eficiencia de Pareto):** El enrutador adaptativo preserva calidad ($ar{Q} \ge ar{Q}(B_2) - 0.15$) con una reducción de costo $\le 50\%$.
* **H4 (Generalización a Holdout):** Rendimiento en `TEST_SET` consistente dentro de $\pm 15$ puntos porcentuales respecto a `DEV_SET`.

### 2.3. Dataset Experimental
* **Documento Base:** *Fundamentos de programación* (Luis Joyanes Aguilar, 4ta Ed.), SHA-256: `1217dd5e6038f150f454198b9645b7f4b89929ff88ba3744ca2c446082f4fb47`.
* **Capítulo:** Capítulo 2 (*Metodología de la programación y desarrollo de software*).
* **Páginas Físicas:** 75 a 112 (38 páginas).
* **Páginas Lógicas:** 45 a 82 (38 páginas).
* **Páginas Excluidas:** 0 páginas.
* **Manifest Congelado:** `PROBE1_DATASET_MANIFEST.json` (SHA-256: `1c53a00a89e23abf4aee40e93564aa6290355e734801f90ee65a57d136afac40`).

### 2.4. Partición DEV / TEST (Zero Leakage)
* **DEV_SET (19 páginas):** `[75, 79, 80, 82, 83, 84, 86, 87, 89, 91, 95, 96, 97, 100, 101, 102, 103, 105, 106]`. Contiene las 4 páginas de referencia de PROBE-0 (`100, 102, 103, 105`) etiquetadas como `DEVELOPMENT_REFERENCE`.
* **TEST_SET (19 páginas):** `[76, 77, 78, 81, 85, 88, 90, 92, 93, 94, 98, 99, 104, 107, 108, 109, 110, 111, 112]`. Conjunto holdout 100% virgen (0% solapamiento con PROBE-0 y DEV).

### 2.5. Baselines Obligatorios
* $B_0$: `ALL_PYPDF` (100% pypdf).
* $B_1$: `ALL_PYMUPDF` (100% PyMuPDF).
* $B_2$: `ALL_DOCLING` (100% Docling v2).
* $B_3$: `ADAPTIVE_ROUTER` (Decisión condicional rápida vs estructural).

### 2.6. Enrutador Adaptativo
* Arquitectura determinista, explicable, local y libre de modelos (*model-free*).
* Prioridad de reglas: $R_1$ (Tablas) $	o R_2$ (Diagramas vectoriales) $	o R_3$ (Solapamiento paralelo) $	o R_4$ (Código anidado) $	o R_5$ (Índices) $	o R_0$ (Fast default).
* Protocolo `ROUTER_FREEZE = TRUE` previo a cualquier evaluación en TEST.

### 2.7. Features Operacionales
* $F_1$ (`dwg_count`), $F_2$ (`table_grid_score`), $F_3$ (`parallel_overlap`), $F_4$ (`code_block_density`), $F_5$ (`indented_blocks`), $F_6$ (`dot_leader_count`).
* Especificación matemática completa y manejo de casos borde en `PROBE1_FEATURE_SPEC.md`.

### 2.8. Gold Standard Independiente
* Criterio objetivo basado en renderizados 200 DPI y geometría vectorial del PDF original, desacoplado de las salidas de Docling o PyMuPDF (`PROBE1_GOLD_STANDARD.md`).

### 2.9. Rúbrica Estructural
* 5 dimensiones: `TABLE_STRUCTURE`, `FLOWCHART_DIAGRAM_ISOLATION`, `CODE_STRUCTURE`, `HEADING_STRUCTURE`, `READING_ORDER`.
* Escala discreta $0 \dots 3$ y `NOT_APPLICABLE (N/A)`.

### 2.10. Métricas del Sistema
* Matriz de confusión ($TP, FP, TN, FN$).
* Métrica crítica: $	ext{MISSED\_ESCALATION\_RATE} = rac{FN}{TP + FN}$ (Tolerancia $\le 10\%$, manejo estricto de denominador 0 como `N/A`).
* Calidad media $ar{Q}$, Latencias ($ar{L}, \widetilde{L}, p95$) y evaluación de frontera de Pareto.

### 2.11. Matriz de Control de Factores Confusores

| Factor Confusor | Clasificación | Estrategia de Mitigación / Protocolo |
|---|---|---|
| **1. Renderizado de PDF** | `CONTROLLED` | Renderizado estandarizado a 200 DPI fijado mediante script inmutable. |
| **2. Segmentación de páginas** | `CONTROLLED` | Páginas físicas atómicas 1 a 1 sin solapamiento entre hojas. |
| **3. Versiones de herramientas** | `CONTROLLED` | Pinned exacto: PyMuPDF 1.24.1, pypdf 4.2.0, Docling 2.5.2 (`PROBE1_ENVIRONMENT_SPEC.json`). |
| **4. Versión de modelos Docling** | `CONTROLLED` | Checkpoint granite-docling congelado en bundle de ejecución. |
| **5. Hardware de ejecución** | `MEASURED` | Telemetría exhaustiva de CPU/GPU en Colab, registrada en manifest de salida. |
| **6. CPU Threading / Concurrencia** | `CONTROLLED` | Extracción secuencial por página para evitar contención de reloj. |
| **7. Consumo de Memoria** | `MEASURED` | Monitoreo de memoria pico (`peak_memory_mb`) por página. |
| **8. Paralelismo de procesamiento** | `CONTROLLED` | Batch size = 1, ejecución lineal determinista. |
| **9. Selección del dataset** | `CONTROLLED` | Capítulo 2 completo (38 páginas) sin exclusión selectiva de casos difíciles. |
| **10. Partición DEV / TEST** | `CONTROLLED` | Split estratificado con semilla fija 42; 4 casos PROBE-0 aislados en DEV. |
| **11. Fuga de features (Feature Leakage)** | `CONTROLLED` | Umbrales calibrados exclusivamente sobre DEV antes de evaluar TEST. |
| **12. Sesgo de Adjudicación Humana** | `LIMITATION` | Evaluación enmascarada ciega (`TOOL_ALPHA..GAMMA`); limitación $N=1$ declarada. |

### 2.12. Cadena de Proveniencia Criptográfica
Trazabilidad de extremo a extremo:
$$	ext{PDF SHA-256} 	o 	ext{Manifest} 	o 	ext{Page ID} 	o 	ext{Tool Blind Hash} 	o 	ext{Raw Extraction} 	o 	ext{Adjudication} 	o 	ext{Metrics}$$

### 2.13. Controles de Fuga (Leakage Controls)
* `LEAKAGE_RISK = FALSE` certificado. Ningún umbral ha sido ajustado observando resultados del `TEST_SET`.

### 2.14. Criterio de Salida (Exit Gate)
* `PASS`: $	ext{MISSED\_ESCALATION} \le 10\% \land ar{Q}(B_3) \ge ar{Q}(B_2) - 0.15 \land 	ext{Relative\_Cost} \le 0.50$.
* `PARTIAL`, `FAIL`, `INCONCLUSIVE` formalmente preregistrados en `PROBE1_EXPERIMENT_PLAN.md`.

### 2.15. Invariantes de Producción
* Bases de datos SQLite de producción: $6/6$ inmutables con `DATABASE_CHANGES = 0`.
* Código productivo de TALOS V1: `V1_RUNTIME_MODIFIED = FALSE`.

### 2.16. Estado Final del Preflight y Cumplimiento C01–C12

```text
==================================================================================================
RESOLUCIÓN DE CONTROLES C01–C12 Y HASHES CRIPTOGRÁFICOS DE ARTEFACTOS
==================================================================================================
[RESOLVED] C01 (Procedencia Umbrales)    -> PROBE1_CORRECTION_LEDGER_C01_C12.md (bdfc0136080e...)
[RESOLVED] C02 (Router Freeze)           -> PROBE1_ROUTER_SPEC.md              (eb887f87696b...)
[RESOLVED] C03 (Features Matemáticas)    -> PROBE1_FEATURE_SPEC.md             (0c7d6537baaa...)
[RESOLVED] C04 (DOCLING_BENEFICIAL)      -> PROBE1_BENEFIT_DEFINITION.md       (bc433c16031d...)
[RESOLVED] C05 (Gold Standard Indep.)    -> PROBE1_GOLD_STANDARD.md            (30f9ae06bd40...)
[RESOLVED] C06 (Adjudicación Ciega)      -> PROBE1_HUMAN_ADJUDICATION_PROTOCOL (5fb5b3b06ed9...)
[RESOLVED] C07 (Missed Escalation Rate)  -> PROBE1_METRICS_SPEC.md             (ee853f78a153...)
[RESOLVED] C08 (Separación PROBE-0)      -> PROBE1_EXPERIMENT_PLAN.md          (de36abe472d6...)
[RESOLVED] C09 (Alcance Generalización)  -> PROBE1_EXPERIMENT_PLAN.md          (de36abe472d6...)
[RESOLVED] C10 (Benchmark 3.65ms Status) -> PROBE1_CORRECTION_LEDGER_C01_C12.md (bdfc0136080e...)
[RESOLVED] C11 (Terminología Ensemble)   -> PROBE1_EXPERIMENT_PLAN.md          (de36abe472d6...)
[RESOLVED] C12 (Matriz Cierre Preflight) -> PROBE1_PREFLIGHT_AUDIT_REPORT.md   (este documento)
==================================================================================================
HASHES DE ESPECIFICACIONES CONGELADAS:
experiments/v1_5_ingestion/probe1/PROBE1_BENEFIT_DEFINITION.md:        bc433c16031d9b9978d836acd3e0d4a6fbe654349bcaccecbf50659e2f5cbe7d
experiments/v1_5_ingestion/probe1/PROBE1_CORRECTION_LEDGER_C01_C12.md: bdfc0136080e4f03509cb53e20401f4f381337d9c2db6f251301aacaffe5b713
experiments/v1_5_ingestion/probe1/PROBE1_DATASET_MANIFEST.json:        1c53a00a89e23abf4aee40e93564aa6290355e734801f90ee65a57d136afac40
experiments/v1_5_ingestion/probe1/PROBE1_ENVIRONMENT_SPEC.json:        3a9af5c43ce5a6edaec7436fdf37107f98edb9e74b472e011daca1d8c9e22f95
experiments/v1_5_ingestion/probe1/PROBE1_EXPERIMENT_PLAN.md:          de36abe472d66922d3451a387d1f3405779f95033129fe027717907670570691
experiments/v1_5_ingestion/probe1/PROBE1_FEATURE_SPEC.md:             0c7d6537baaab8561dbed41af0b563a139fded5f3985ea190e22643f4a74f516
experiments/v1_5_ingestion/probe1/PROBE1_GOLD_STANDARD.md:             30f9ae06bd40ada1a7a8fa150aecc574ee8154cfbb7fbfab25dfa465949da177
experiments/v1_5_ingestion/probe1/PROBE1_HUMAN_ADJUDICATION_PROTOCOL:  5fb5b3b06ed90831c9b6ab463a979cb1b367ed1aaa7c9866aa126ef4c7df5896
experiments/v1_5_ingestion/probe1/PROBE1_METRICS_SPEC.md:              ee853f78a15362835b572026201cf604d675553b8566590d737fe0e0dc8b83ee
experiments/v1_5_ingestion/probe1/PROBE1_ROUTER_SPEC.md:               eb887f87696b6874eddc3df09eac2899f8789783267ef25036de88aa9f6c6bba
==================================================================================================
VEREDICTO FINAL DE PREFLIGHT:
PROBE_1_DESIGN       = COMPLETE
PROBE_1_PREFLIGHT    = PASSED
PROBE_1_SEAL         = READY_FOR_SEAL
PROBE_1_EXECUTION    = NOT_STARTED
==================================================================================================
```
