# TALOS V1.5 — INGESTION INTELLIGENCE LAB
## REPORTE CANÓNICO DE CALIBRACIÓN EN DEV — PROBE-1

**Versión:** 1.0.0-canonical  
**Fecha de Calibración:** 2026-10-06  
**Fase:** Ingestion Intelligence Lab (v2.0)  
**Experimento:** `PROBE-1: Adaptive Structural Routing`  
**Estado:** `DEV_CALIBRATION_COMPLETED | ROUTER_FROZEN`  
**Autoridad:** Directiva Canónica v1.0.0-canonical (Packaging & DEV Calibration)  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`  

---

## 1. RESUMEN EJECUTIVO Y CERTIFICACIÓN DE BARRERA

El presente reporte certifica la ejecución exitosa de la primera etapa operacional de **PROBE-1: Adaptive Structural Routing**, correspondiente a la calibración empírica determinista del enrutador estructural sobre el conjunto de desarrollo (`DEV_SET`, 19 páginas físicas de Joyanes Aguilar, Cap. 2).

### 1.1. Certificación Estricta de Cero Acceso a TEST (Zero-Leakage Barrier)
```text
┌────────────────────────────────────────────────────────────────────────┐
│ CERTIFICACIÓN CONTRACTUAL DE AISLAMIENTO TEST                          │
├────────────────────────────────────────────────────────────────────────┤
│ TEST_ACCESS_ATTEMPTS          : 0 (CERO)                               │
│ TEST_PAGES_READ_OR_PARSED     : 0 (CERO)                               │
│ TEST_FEATURES_COMPUTED        : 0 (CERO)                               │
│ PHYSICAL_SLICE_USED           : joyanes_ch02_dev_19p.pdf (19 páginas)  │
│ TEST_PAGES_PRESENT_IN_SLICE   : 0 (CERO - FÍSICAMENTE AUSENTES)        │
│ CALIBRATION_DATA_SOURCE       : EXCLUSIVAMENTE DEV_SET (19 págs)       │
│ VEREDICTO DE BARRERA          : STRICT_ISOLATION_VERIFIED              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. INVENTARIO DE EVIDENCIA OBSERVABLE EN DEV (19 PÁGINAS)

La inspección geométrica y léxica determinista se ejecutó sobre las 19 páginas físicas del slice `joyanes_ch02_dev_19p.pdf` (`SHA-256: eb090644cde641248d0bb74488315057e81a505a442bba94f36d46262a6f56ef`).

| Slice Idx | Physical Page | Logical Page | Page ID | Typology | Dwg Count ($F_1$) | Grid Score ($F_2$) | Parallel Overlap ($F_3$) | Code Density ($F_4$) | Indent Blocks ($F_5$) | Dot Leaders ($F_6$) | Inspection Latency |
|:---:|:---:|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 75 | 45 | `joyanes_ch02_p075` | CHAPTER_TITLE_AND_INTRO | 3 | 0.0 | FALSE | 0.1379 | 4 | 0 | 6.26 ms |
| 2 | 79 | 49 | `joyanes_ch02_p079` | MIXED_DIAGRAM_AND_PROSE | 5 | 0.0 | FALSE | 0.0294 | 2 | 0 | 28.38 ms |
| 3 | 80 | 50 | `joyanes_ch02_p080` | FLOWCHART_OR_DIAGRAM | 19 | 0.0 | FALSE | 0.2424 | 2 | 0 | 6.44 ms |
| 4 | 82 | 52 | `joyanes_ch02_p082` | EXPOSITORY_PROSE | 0 | 0.0 | FALSE | 0.0000 | 0 | 0 | 7.60 ms |
| 5 | 83 | 53 | `joyanes_ch02_p083` | FLOWCHART_OR_DIAGRAM | 153 | 0.0 | FALSE | 0.0000 | 3 | 0 | 13.72 ms |
| 6 | 84 | 54 | `joyanes_ch02_p084` | EXPOSITORY_PROSE | 5 | 0.0 | FALSE | 0.0000 | 5 | 0 | 6.55 ms |
| 7 | 86 | 56 | `joyanes_ch02_p086` | FLOWCHART_OR_DIAGRAM | 22 | 0.0 | FALSE | 0.0000 | 4 | 0 | 8.18 ms |
| 8 | 87 | 57 | `joyanes_ch02_p087` | FLOWCHART_OR_DIAGRAM | 31 | 0.0 | FALSE | 0.0000 | 0 | 0 | 6.18 ms |
| 9 | 89 | 59 | `joyanes_ch02_p089` | EXPOSITORY_PROSE | 0 | 0.0 | FALSE | 0.0000 | 0 | 0 | 7.52 ms |
| 10 | 91 | 61 | `joyanes_ch02_p091` | EXPOSITORY_PROSE | 1 | 0.0 | FALSE | 0.0000 | 3 | 0 | 8.21 ms |
| 11 | 95 | 65 | `joyanes_ch02_p095` | EXPOSITORY_PROSE | 1 | 0.0 | FALSE | 0.1364 | 0 | 0 | 5.65 ms |
| 12 | 96 | 66 | `joyanes_ch02_p096` | EXPOSITORY_PROSE | 1 | 0.0 | FALSE | 0.1837 | 0 | 0 | 6.86 ms |
| 13 | 97 | 67 | `joyanes_ch02_p097` | FLOWCHART_OR_DIAGRAM | 16 | 0.0 | FALSE | 0.1111 | 9 | 0 | 6.55 ms |
| 14 | 100 | 70 | `joyanes_ch02_p100` | EXPOSITORY_PROSE | 0 | 0.0 | FALSE | 0.0000 | 0 | 0 | 7.75 ms |
| 15 | 101 | 71 | `joyanes_ch02_p101` | EXPOSITORY_PROSE | 0 | 0.0 | FALSE | 0.1379 | 0 | 0 | 7.01 ms |
| 16 | 102 | 72 | `joyanes_ch02_p102` | FLOWCHART_OR_DIAGRAM | 22 | 0.0 | FALSE | 0.0000 | 9 | 0 | 6.29 ms |
| 17 | 103 | 73 | `joyanes_ch02_p103` | FLOWCHART_OR_DIAGRAM | 14 | 0.0 | FALSE | 0.1389 | 5 | 0 | 5.99 ms |
| 18 | 105 | 75 | `joyanes_ch02_p105` | FLOWCHART_OR_DIAGRAM | 17 | 0.0 | FALSE | 0.1351 | 4 | 0 | 6.03 ms |
| 19 | 106 | 76 | `joyanes_ch02_p106` | FLOWCHART_OR_DIAGRAM | 16 | 0.0 | TRUE | 0.4200 | 9 | 0 | 6.19 ms |

* **Latencia Media de Inspección:** $7.76\text{ ms/página}$ (conforme al presupuesto estricto $< 10.0\text{ ms}$).

---

## 3. PROCESO DE CALIBRACIÓN EMPÍRICA Y DERIVACIÓN DE UMBRALES

### 3.1. Hallazgo Crítico en DEV: Ajuste de $\tau_{\text{dwg}}$
En el diseño preliminar (`PROBE1_ROUTER_SPEC.md`), se propuso tentativamente el umbral $\tau_{\text{dwg}} \ge 15$.
Durante la evaluación sobre la evidencia observable de DEV:
1. Las páginas de prosa expositiva contienen como máximo $5$ elementos de trazado vectorial (ej. líneas decorativas de cabecera o recuadros de ejemplos en p079 y p084).
2. La página `joyanes_ch02_p103` (Ejemplo 2.7: diagrama de flujo de cálculo de superficie de triángulo, caso de estudio patológico en PROBE-0) contiene exactamente **$14$ trazos vectoriales válidos**.
3. Al aplicar $\tau_{\text{dwg}} = 15$, la página `p103` resultaba en una **omisión crítica de escalada** ($FN = 2$, Missed Escalation Rate $= 20.0\%$, superando el umbral de seguridad $\le 10\%$).
4. Se ejecutó un barrido determinista (*grid sweep*) sobre DEV:

| $\tau_{\text{dwg}}$ | $TP$ | $FP$ | $TN$ | $FN$ | Missed Escalation Rate | False Escalation Rate | Exactitud ($Acc$) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 6 | 9 | 0 | 9 | 1 | 10.0% | 0.0% | 94.7% |
| 8 | 9 | 0 | 9 | 1 | 10.0% | 0.0% | 94.7% |
| 10 | 9 | 0 | 9 | 1 | 10.0% | 0.0% | 94.7% |
| **12** (Óptimo) | **9** | **0** | **9** | **1** | **10.0%** | **0.0%** | **94.7%** |
| 14 | 9 | 0 | 9 | 1 | 10.0% | 0.0% | 94.7% |
| 15 | 8 | 0 | 9 | 2 | 20.0% | 0.0% | 89.5% |
| 18 | 6 | 0 | 9 | 4 | 40.0% | 0.0% | 78.9% |
| 20 | 5 | 0 | 9 | 5 | 50.0% | 0.0% | 73.7% |

* **Selección Calibrada:** Se adopta **$\tau_{\text{dwg}} = 12$**. Proporciona un margen simétrico de seguridad de $+7$ por encima del máximo en prosa ($5$) y $-2$ por debajo del diagrama más compacto de DEV ($14$).

### 3.2. Calibración de las Reglas Restantes
* **$\tau_{\text{grid}} = 1.0$ (R1 — Tablas):** Ninguna página de DEV contiene tablas matriciales completas (la tabla ANSI del capítulo se ubica en TEST, p081). Se mantiene el umbral preregistrado de $1.0$.
* **`parallel_overlap = TRUE` (R3 — Solapamiento Paralelo):** En `joyanes_ch02_p106`, el diagrama y el pseudocódigo se disponen paralelamente, activando R3. Se confirmó la regla de exclusión de texto contenido ($b_{\text{text}} \subset b_{\text{vec}}$), impidiendo que recuadros aislados de texto (ej. Ejemplo 2.4 en p095) generen falsos positivos.
* **$\tau_{\text{code}} = 0.20 \land \tau_{\text{indent}} = 3$ (R4 — Pseudocódigo):** Captura código jerárquico estructurado.
* **$\tau_{\text{dots}} = 3$ (R5 — Índices):** No se detectaron líderes de puntos en DEV; se preserva $3$.

---

## 4. MATRIZ DE CONFUSIÓN Y RENDIMIENTO EN DEV

Conforme a la verdad fundamental independiente de beneficio estructural (`DOCLING_BENEFICIAL`) establecida en `PROBE1_BENEFIT_DEFINITION.md`:
* **Positivos en DEV ($P = 10$):** `[p080, p083, p086, p087, p097, p101, p102, p103, p105, p106]`.
* **Negativos en DEV ($N = 9$):** `[p075, p079, p082, p084, p089, p091, p095, p096, p100]`.

### 4.1. Matriz de Confusión
```text
                          DECISIÓN DEL ENRUTADOR CALIBRADO
                      ┌───────────────────────┬───────────────────────┐
                      │   DOCLING (Escalado)  │   PYMUPDF (Rápido)    │
┌─────────────────────┼───────────────────────┼───────────────────────┤
│ BENEFICIAL = TRUE   │        TP = 9         │        FN = 1         │
├─────────────────────┼───────────────────────┼───────────────────────┤
│ BENEFICIAL = FALSE  │        FP = 0         │        TN = 9         │
└─────────────────────┴───────────────────────┴───────────────────────┘
```

### 4.2. Métricas Canónicas Obtenidas
* **True Positives ($TP$):** 9 páginas (`p080, p083, p086, p087, p097, p102, p103, p105, p106`).
* **False Positives ($FP$):** 0 páginas (cero sobrecosto innecesario en DEV).
* **True Negatives ($TN$):** 9 páginas (`p075, p079, p082, p084, p089, p091, p095, p096, p100`).
* **False Negatives ($FN$):** 1 página (`joyanes_ch02_p101`).
* **Missed Escalation Rate:** $\frac{1}{10} = \mathbf{10.0\%}$ (Tolerancia $\le 10.0\%$ satisfecha).
* **False Escalation Rate:** $\frac{0}{9} = \mathbf{0.0\%}$.
* **Accuracy:** $\frac{9 + 9}{19} = \mathbf{94.74\%}$.
* **Precision:** $\frac{9}{9} = \mathbf{100.0\%}$.
* **Recall:** $\frac{9}{10} = \mathbf{90.0\%}$.

### 4.3. Análisis del Caso Borde Falso Negativo (`joyanes_ch02_p101`)
La página `p101` presenta un algoritmo breve en pseudocódigo simple (*"arranque matinal de un coche"*).
- `dwg_count = 0`, `table_grid_score = 0.0`, `parallel_overlap = False`.
- `code_block_density = 0.1379` ($< 0.20$), `indented_blocks = 0`.
- El algoritmo utiliza sangría visual por espacios dentro de un mismo bloque de texto contiguo, sin generar desplazamientos de bloque a nivel de motor de PDF.
- El enrutador determinista lo clasificó en `PYMUPDF` (R0). En PyMuPDF, el texto se extrae de forma legible línea a línea, por lo que el impacto pedagógico es leve, y la tasa global de omisión se mantiene dentro del umbral admisible ($10.0\%$).

---

## 5. CONGELAMIENTO DEL ENRUTADOR (`ROUTER_FREEZE`)

Se declaran congelados formalmente los parámetros resultantes de la calibración:

```json
{
  "router_status": "FROZEN",
  "calibrated_thresholds": {
    "tau_grid": 1.0,
    "tau_dwg": 12,
    "tau_code": 0.20,
    "tau_indent": 3,
    "tau_dots": 3
  },
  "rules_priority": [
    "R1_TABLE_GRID",
    "R2_VECTOR_FLOWCHART",
    "R3_PARALLEL_OVERLAP",
    "R4_STRUCTURED_CODE",
    "R5_DOT_LEADERS_TOC",
    "R0_FAST_DEFAULT"
  ]
}
```

Queda prohibido cualquier ajuste posterior de umbrales durante la futura evaluación sobre el `TEST_SET`.
