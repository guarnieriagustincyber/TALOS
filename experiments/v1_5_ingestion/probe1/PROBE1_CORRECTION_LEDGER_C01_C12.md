# TALOS V1.5 — INGESTION INTELLIGENCE LAB
## PROBE-1: CORRECTION LEDGER C01–C12

**Versión:** 1.0.1-canonical  
**Fecha:** 2026-10-05  
**Fase:** Ingestion Intelligence Lab (v2.0)  
**Experimento:** `PROBE-1: Adaptive Structural Routing`  
**Estado:** `CORRECTIONS_REGISTERED | AUDIT_IN_PROGRESS`  
**Predecesor Canónico:** Checkpoint 148 (`reports/v1_5_phase1/PROBE_0_EXECUTION_AUDIT_REPORT.md`)  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`  

---

## 1. PROPÓSITO DEL LEDGER

Este documento establece el registro canónico de resolución de los doce controles metodológicos obligatorios (**C01 a C12**) formulados en la Directiva Final de Corrección y Pre-Sellado v1.0.1. Su objetivo es garantizar la reproducibilidad epistemológica absoluta de PROBE-1, erradicar cualquier fuga de datos (*leakage*), desvincular el gold standard de las herramientas bajo evaluación y asegurar que ningún veredicto sea declarado sin auditoría previa.

---

## 2. RESOLUCIÓN DETALLADA DE CONTROLES C01–C12

### C01 — PROCEDENCIA DE CADA UMBRAL DEL ROUTER

```text
=================================================================================================================================
REGISTRO FORMAL DE PROCEDENCIA DE UMBRALES DEL ENRUTADOR (CONTROL C01)
=================================================================================================================================
```

| FEATURE | THRESHOLD | UNIT | ORIGIN | SOURCE_DATASET | SELECTION_METHOD | DEV_ONLY? | TEST_VISIBLE? | PROBE_0_EVIDENCE? | PREVIOUSLY_FROZEN? | LEAKAGE_RISK | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `dwg_count` | >= 15 | dibujos vectoriales / pág | Hipótesis exploratoria preliminar | PROBE-0 (Casos 2.7, 2.8) & DEV_SET | Inspección de densidad vectorial en diagramas de flujo ANSI | SÍ | NO | SÍ (p.103, 105) | NO (Sujeto a sellado) | FALSE | `HYPOTHESIS_PENDING_DEV_FREEZE` |
| `table_grid_score` | >= 1.0 | score adimensional [0, inf) | Hipótesis exploratoria preliminar | PROBE-0 (Tablas 1.6, 2.1) & DEV_SET | Detección de intersección ortogonal de líneas en celdas | SÍ | NO | SÍ (p.50, 102) | NO (Sujeto a sellado) | FALSE | `HYPOTHESIS_PENDING_DEV_FREEZE` |
| `parallel_overlap` | TRUE | booleano {0, 1} | Hipótesis exploratoria preliminar | PROBE-0 (Ejemplo 2.8) & DEV_SET | Solapamiento horizontal de bounding boxes entre texto y vectores | SÍ | NO | SÍ (p.105) | NO (Sujeto a sellado) | FALSE | `HYPOTHESIS_PENDING_DEV_FREEZE` |
| `code_block_density` | >= 0.20 | fracción de líneas [0, 1] | Hipótesis exploratoria preliminar | PROBE-0 (p.142) & DEV_SET | Ratio de líneas con palabras clave algorítmicas UPSAM | SÍ | NO | SÍ (p.142) | NO (Sujeto a sellado) | FALSE | `HYPOTHESIS_PENDING_DEV_FREEZE` |
| `indented_blocks` | >= 3 | recuento de bloques indentados | Hipótesis exploratoria preliminar | PROBE-0 (p.142) & DEV_SET | Recuento de bloques de texto con margen izquierdo desplazado | SÍ | NO | SÍ (p.142) | NO (Sujeto a sellado) | FALSE | `HYPOTHESIS_PENDING_DEV_FREEZE` |
| `dot_leader_count` | >= 3 | líneas con puntos continuos | Hipótesis exploratoria preliminar | PROBE-0 (Índice p.12, 14) & DEV_SET | Detección de patrones de líderes de puntos (TOC / Tablas de contenido) | SÍ | NO | SÍ (p.12, 14) | NO (Sujeto a sellado) | FALSE | `HYPOTHESIS_PENDING_DEV_FREEZE` |

#### Dictamen de Gobernanza sobre C01:
1. **Origen Epistémico:** Ningún umbral fue derivado observando datos del `TEST_SET`. Los umbrales provienen de los arquetipos cualitativos observados en PROBE-0 (utilizados exclusivamente como `DEVELOPMENT_REFERENCE`) y observaciones preliminares en páginas de desarrollo.
2. **Clasificación Formal:** Todos los umbrales se declaran formalmente como **`HYPOTHESIS_PENDING_DEV_FREEZE`**.
3. **Protocolo Inviolable:** Los umbrales definitivos deberán re-calibrarse y congelarse formalmente utilizando **exclusivamente el conjunto de 19 páginas de `DEV_SET`**, antes de que se produzca cualquier acceso, inspección o evaluación sobre las páginas del `TEST_SET`.
4. **Riesgo de Fuga:** `LEAKAGE_RISK = FALSE` certificado documentalmente.

---

### C02 — CONGELAMIENTO DEL ROUTER ANTES DEL TEST

Se formaliza el protocolo estricto de dos fases secuenciales:

```text
FASE 1: DESARROLLO Y CALIBRACIÓN (DEV ONLY)
┌─────────────────────────────────────────────────────────────┐
│ 19 páginas DEV_SET (incluye 4 páginas ref PROBE-0)         │
│  ↓                                                          │
│ Análisis de distribución de features                        │
│  ↓                                                          │
│ Ajuste y verificación empírica de umbrales sobre DEV        │
│  ↓                                                          │
│ Congelamiento de especificación (Fórmulas, Umbrales, Código)│
│  ↓                                                          │
│ GENERACIÓN DE HASH CRIPTOGRÁFICO: ROUTER_FREEZE = TRUE      │
└─────────────────────────────────────────────────────────────┘
                              │
                    BARRERA DE SELLADO
                              │
FASE 2: EVALUACIÓN EN HOLDOUT (TEST ONLY)
┌─────────────────────────────────────────────────────────────┐
│ 19 páginas TEST_SET (100% ciegas, 0% vistas en PROBE-0/DEV) │
│  ↓                                                          │
│ Ejecución del Router congelado (sin modificar ni un umbral) │
│  ↓                                                          │
│ Evaluación de Métricas de Holdout                           │
└─────────────────────────────────────────────────────────────┘
```

* **Regla de Inmutabilidad:** Prohibida terminantemente cualquier modificación del router una vez sellado (`ROUTER_FREEZE = TRUE`). Cualquier variación posterior requerirá un experimento separado (`PROBE-2`).

---

### C03 — DEFINICIÓN MATEMÁTICA DE TODAS LAS FEATURES

Se define la especificación matemática completa, operacional y reproducible en el documento contractual [`PROBE1_FEATURE_SPEC.md`](file:///media/agustin/Laboratorio/study-engie/experiments/v1_5_ingestion/probe1/PROBE1_FEATURE_SPEC.md). Cada feature posee fórmula explícita, unidades del SI / escala geométrica, tratamiento de geometrías rotadas, tolerancia espacial y referencias de implementación.

---

### C04 — DEFINICIÓN FORMAL DE `DOCLING_BENEFICIAL`

Se introduce formalmente la variable categórica:
$$	ext{DOCLING\_BENEFICIAL} \in \{	ext{TRUE}, 	ext{FALSE}\}$$

Definida de manera independiente de cualquier heurística o decisión del router en el documento contractual [`PROBE1_BENEFIT_DEFINITION.md`](file:///media/agustin/Laboratorio/study-engie/experiments/v1_5_ingestion/probe1/PROBE1_BENEFIT_DEFINITION.md).
* Solo se evalúan las dimensiones aplicables: $\mathcal{D}_{	ext{app}}(p) \subseteq \{	ext{TABLE}, 	ext{DIAGRAM}, 	ext{CODE}, 	ext{HEADING}, 	ext{ORDER}\}$.
* Se exige un beneficio material medible: $\Delta_{	ext{score}} \ge 1.0$ en al menos una dimensión crítica sin degradar severamente el resto, o una ganancia promedio acumulada $ar{\Delta} \ge 0.5$.
* Los empates se adjudican estrictamente como `DOCLING_BENEFICIAL = FALSE` (principio de economía computacional: si el baseline rápido empata en calidad, no hay justificación para escalar a Docling).

---

### C05 — GOLD STANDARD INDEPENDIENTE

Se formaliza el criterio de referencia en el documento [`PROBE1_GOLD_STANDARD.md`](file:///media/agustin/Laboratorio/study-engie/experiments/v1_5_ingestion/probe1/PROBE1_GOLD_STANDARD.md):
* El Gold Standard **NO es Docling**, **NO es PyMuPDF** y **NO es la decisión del router**.
* El Gold Standard es la representación estructural fidedigna del contenido pedagógico del documento original, fundamentada en inspección visual de alta resolución (200 DPI) y análisis de geometría vectorial intrínseca del PDF.

---

### C06 — ADJUDICACIÓN HUMANA Y UNIDAD DE EVALUACIÓN

Se formaliza el protocolo ciego en el documento [`PROBE1_HUMAN_ADJUDICATION_PROTOCOL.md`](file:///media/agustin/Laboratorio/study-engie/experiments/v1_5_ingestion/probe1/PROBE1_HUMAN_ADJUDICATION_PROTOCOL.md):
* **Unidad de Adjudicación:** $	ext{PAGE} 	imes 	ext{DIMENSION} 	imes 	ext{TOOL}$.
* **Cegamiento Criptográfico:** Las salidas de `pypdf`, `pymupdf` y `docling` se presentan con identificadores anónimos enmascarados mediante hash SHA-256 (`TOOL_ALPHA`, `TOOL_BETA`, `TOOL_GAMMA`).
* **Rúbrica Estandarizada:** Escala formal $0 \dots 3$ y `NOT_APPLICABLE`.
* **Declaración de Limitación:** Se registra formalmente que la adjudicación cuenta con $N=1$ especialista humano independiente, constituyendo una limitación muestral explícita.

---

### C07 — DEFINICIÓN DE MISSED ESCALATION RATE Y MÉTRICAS

Se establecen las fórmulas matemáticas con denominadores inequívocos en [`PROBE1_METRICS_SPEC.md`](file:///media/agustin/Laboratorio/study-engie/experiments/v1_5_ingestion/probe1/PROBE1_METRICS_SPEC.md):
$$	ext{MISSED\_ESCALATION\_RATE} = rac{|\{p \in 	ext{TEST} : 	ext{DOCLING\_BENEFICIAL}(p) = 	ext{TRUE} \land 	ext{ROUTER}(p) = 	ext{FAST}\}|}{|\{p \in 	ext{TEST} : 	ext{DOCLING\_BENEFICIAL}(p) = 	ext{TRUE}\}|}$$
* **Regla de Cero Denominador:** Si el denominador es 0, el resultado es estrictamente **`NOT_APPLICABLE (N/A)`**, **NUNCA `0%`**.
* **Tolerancia Preregistrada:** $	ext{MISSED\_ESCALATION\_RATE} \le 10\%$.

---

### C08 — SEPARACIÓN EPISTÉMICA PROBE-0 / PROBE-1

* **Clasificación Canónica:** Toda la evidencia empírica obtenida en PROBE-0 se reclasifica formalmente como:
  $$	ext{PROBE-0} \equiv 	ext{DEVELOPMENT\_REFERENCE} \land 	ext{HYPOTHESIS\_GENERATION}$$
* **Prohibición Epistémica:** Queda terminantemente prohibido utilizar los resultados de PROBE-0 como "validación" o "confirmación" del rendimiento de PROBE-1. PROBE-1 es un experimento de generalización en holdout con validez independiente.

---

### C09 — ALCANCE Y LÍMITES DE GENERALIZACIÓN

* **Frontera de Inferencia:** Las conclusiones de PROBE-1 están circunscritas única y exclusivamente a:
  $$	ext{Alcance Válido} \equiv 	ext{Joyanes Aguilar (4ta Edición), Capítulo 2 (Páginas 75–112)}$$
* **Declaraciones Prohibidas:** No se permitirá afirmar que el enrutador funciona para "PDFs en general", "libros técnicos en general" ni que el router es "production-ready".
* Toda extrapolación fuera de este capítulo se declarará como hipótesis no testeada para etapas posteriores.

---

### C10 — PROVENIENCIA DEL BENCHMARK DE LATENCIA (3.65 ms)

```text
=================================================================================================================================
REGISTRO DE PROVENIENCIA Y AUDITORÍA DEL BENCHMARK DE LATENCIA (CONTROL C10)
=================================================================================================================================
benchmark_id            = bench_pymupdf_fast_inspection_diag_20261005
date                    = 2026-10-05T23:32:30-03:00
hardware                = x86_64 CPU (Local Linux Host)
OS                      = Linux 6.8.0 / Ubuntu
Python                  = 3.12.3 (.venv)
PyMuPDF_version         = 1.24.1
input_pages             = 38 páginas (Capítulo 2 Joyanes, p.75-112)
iterations              = 1 (single diagnostic pass)
warmup                  = NO
cold_start              = TRUE
cache_state             = UNCONTROLLED (OS page cache activo)
measurement_method      = time.perf_counter()
timer                   = monotonic system timer
observed_mean           = 3.65 ms / página
STATUS                  = UNVERIFIED / EXPLORATORY DIAGNOSTIC ONLY
=================================================================================================================================
```

#### Dictamen de Gobernanza sobre C10:
La cifra de $3.65	ext{ ms/página}$ corresponde exclusivamente a un sondeo exploratorio de una sola iteración ejecutado en la CPU local durante la fase de análisis. **NO constituye un benchmark científico verificado**.
* **Acción Correctiva:** Se clasifica formalmente como **`STATUS = UNVERIFIED`**.
* **Retiro de Claims:** Se retira de cualquier afirmación confirmada de rendimiento en la especificación.
* **Protocolo para Ejecución:** En la ejecución autorizada de PROBE-1 en Colab, la latencia de inspección se medirá formalmente bajo protocolo de múltiples iteraciones ($K \ge 5$), con warmup explícito y reporte de media, mediana, p95 y desviación estándar.

---

### C11 — TERMINOLOGÍA DE ENSEMBLE SUBORDINADA

* **Título Conceptual Canónico:** **`PROBE-1 — ADAPTIVE STRUCTURAL ROUTING`** (Enrutamiento Estructural Adaptativo).
* **Delimitación de Ensemble:** El término "ensemble" no representa una combinación de voto en runtime productivo, sino un análisis comparativo auxiliar multi-herramienta ($B_0 \dots B_3$) para establecer cotas superiores e inferiores de fidelidad estructural.

---

### C12 — GATE DE CIERRE Y MATRIZ DE EVIDENCIA PRE-SELLADO

| ID | Control de Rigor Metodológico | Evidencia Documental Requerida | Estado de Resolución |
|---|---|---|---|
| **C01** | Procedencia de umbrales | Tabla formal de origen, clasificación como hipótesis sobre DEV | **RESOLVED** (Sección C01 de este Ledger) |
| **C02** | Congelamiento previo a TEST | Protocolo en 2 fases con hash criptográfico previo a TEST | **RESOLVED** (`PROBE1_ROUTER_SPEC.md`) |
| **C03** | Especificación matemática de features | Fórmulas, geometrías, tolerancias y casos borde | **RESOLVED** (`PROBE1_FEATURE_SPEC.md`) |
| **C04** | Definición formal de `DOCLING_BENEFICIAL` | Criterio categórico formal con margen $\Delta \ge 1.0$ | **RESOLVED** (`PROBE1_BENEFIT_DEFINITION.md`) |
| **C05** | Gold Standard independiente | Criterio estructural fidedigno independiente de herramientas | **RESOLVED** (`PROBE1_GOLD_STANDARD.md`) |
| **C06** | Adjudicación humana y unidad | Unidad $P 	imes D 	imes T$, protocolo ciego, $N=1$ declarado | **RESOLVED** (`PROBE1_HUMAN_ADJUDICATION_PROTOCOL.md`) |
| **C07** | Missed Escalation Rate | Fórmulas con denominador explícito, manejo de $0$ como $N/A$ | **RESOLVED** (`PROBE1_METRICS_SPEC.md`) |
| **C08** | Separación epistémica PROBE-0 | Reclasificación de PROBE-0 como hipótesis exploratoria | **RESOLVED** (Sección C08 de este Ledger) |
| **C09** | Alcance de generalización | Acotado estrictamente al Capítulo 2 de Joyanes | **RESOLVED** (`PROBE1_EXPERIMENT_PLAN.md`) |
| **C10** | Proveniencia de latencia (3.65 ms) | Clasificado como `UNVERIFIED` y retirado de claims confirmados | **RESOLVED** (Sección C10 de este Ledger) |
| **C11** | Terminología de Ensemble | Subordinado a Adaptive Structural Routing | **RESOLVED** (Sección C11 de este Ledger) |
| **C12** | Matriz de evidencia completa | Los 12 controles formalmente satisfechos y auditables | **RESOLVED** (Tabla C12 de este Ledger) |

---

## 3. CONCLUSIÓN Y DICTAMEN DE PRE-SELLADO

Habiéndose registrado y formalizado la resolución exhaustiva de los doce controles metodológicos C01 a C12:
```text
PROBE_1_CORRECTIONS_STATUS  = ALL_C01_TO_C12_RESOLVED
LEAKAGE_RISK                = ZERO_CERTIFIED
PREFLIGHT_READINESS          = READY_FOR_PREFLIGHT_AUDIT
PROBE_1_EXECUTION           = STRICTLY_NOT_STARTED
DATABASE_CHANGES            = 0
```
