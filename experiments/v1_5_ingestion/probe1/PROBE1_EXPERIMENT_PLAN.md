# TALOS V1.5 — INGESTION INTELLIGENCE LAB
## PROBE-1: PLAN EXPERIMENTAL CANÓNICO (ADAPTIVE STRUCTURAL ROUTING)

**Versión:** 1.0.1-canonical  
**Fecha:** 2026-10-05  
**Fase:** Ingestion Intelligence Lab (v2.0)  
**Experimento:** `PROBE-1: Adaptive Structural Routing`  
**Predecesor Canónico:** Checkpoint 148 (`reports/v1_5_phase1/PROBE_0_EXECUTION_AUDIT_REPORT.md`)  
**Estado de Gobernanza:** `DESIGN_AND_PREFLIGHT_ONLY | EXECUTION_STRICTLY_PROHIBITED`  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`  

---

## 1. PROPÓSITO Y FRONTERA EPISTÉMICA

El propósito de PROBE-1 es investigar si, a partir de características geométricas y estructurales de baja sobrecarga ($< 10	ext{ ms}$) observables directamente en una página PDF, es posible construir un **enrutador determinista, explicable y libre de modelos opacos** (*model-free*) que seleccione entre extractores complementarios:
* `FAST_PATH` (`PyMuPDF` / `pypdf`): para páginas textuales homogéneas.
* `DOCLING_PATH` (`Docling v2`): para páginas con diagramas vectoriales, tablas complejas o código algorítmico anidado.

### 1.1. Delimitación Estricta del Alcance (Control C09)
Las conclusiones del experimento quedan estrictamente circunscritas al dominio evaluado:
$$	ext{Alcance Válido} \equiv 	ext{Capítulo 2 de Joyanes Aguilar (4ta Edición, págs. 75–112)}$$
*Queda prohibido afirmar que el router generaliza universalmente a cualquier PDF o libro técnico.*

### 1.2. Separación Epistémica de PROBE-0 (Control C08)
Los resultados obtenidos en PROBE-0 se declaran exclusivamente como:
$$	ext{PROBE-0} \equiv 	ext{HYPOTHESIS\_GENERATION} \land 	ext{DEVELOPMENT\_REFERENCE}$$
PROBE-1 evalúa la capacidad de generalización sobre un conjunto holdout independiente (`TEST_SET`), sin reutilizar la evidencia patológica de PROBE-0 como validación.

### 1.3. Subordinación del Concepto de Ensemble (Control C11)
El objetivo central es el **Enrutamiento Estructural Adaptativo**. Las combinaciones multi-extractor actúan únicamente como baselines comparativos ($B_0 \dots B_3$) para establecer cotas de calidad y costo.

---

## 2. PREGUNTAS DE INVESTIGACIÓN E HIPÓTESIS

### 2.1. Pregunta Principal
> **¿Puede un conjunto de señales geométricas y sintácticas observables en $< 10	ext{ ms}$ predecir cuándo una página se beneficia materialmente de Docling v2, logrando un trade-off óptimo de calidad y costo frente a extractores lineales rápidos?**

### 2.2. Preguntas Secundarias
* **RQ1 (Detección):** ¿Con qué precisión y recall detecta el router las páginas que contienen tablas densas, código o diagramas de flujo?
* **RQ2 (Seguridad Estructural):** ¿Se mantiene la tasa de omisión crítica (*Missed Escalation Rate*) por debajo del umbral de seguridad $\le 10\%$?
* **RQ3 (Sobrecarga de Cómputo):** ¿Qué sobrecarga de tiempo introduce el paso de inspección en el pipeline de ingestión?
* **RQ4 (Frontera de Pareto):** ¿Alcanza el enrutador adaptativo calidad comparable a $B_2$ (`ALL_DOCLING`) reduciendo el costo total en al menos un $50\%$?
* **RQ5 (Robustez en Holdout):** ¿Mantiene el enrutador su efectividad en el conjunto `TEST_SET` sin degradación respecto a `DEV_SET`?

### 2.3. Hipótesis Preregistradas
* **H1 (Valor Selectivo de Docling):** En páginas con tablas ortogonales, código o diagramas vectoriales, Docling v2 produce una representación estructural superior a PyMuPDF con $\Delta \ge 1.0$ en al menos una dimensión mayor.
* **H2 (Enrutamiento Determinista):** Una política determinista basada en umbrales geométricos simples clasifica correctamente las páginas con beneficio estructural material en $	ext{Recall} \ge 90\%$.
* **H3 (Eficiencia de Pareto):** El sistema adaptativo logra $ar{Q}(B_3) \ge ar{Q}(B_2) - 0.15$ con un costo computacional $\le 0.50 	imes 	ext{Cost}(B_2)$.
* **H4 (Generalización a Holdout):** Las métricas de enrutamiento obtenidas en `TEST_SET` no divergen en más de $15$ puntos porcentuales respecto a `DEV_SET`.

---

## 3. DISEÑO FACTORIAL Y BASELINES

Se comparan cuatro condiciones experimentales sobre las 19 páginas del `TEST_SET`:
* **$B_0$ (`ALL_PYPDF`):** Baseline determinista lineal plano.
* **$B_1$ (`ALL_PYMUPDF`):** Baseline de bloques de texto crudo de TALOS V1.
* **$B_2$ (`ALL_DOCLING`):** Límite superior de cómputo y calidad estructural (Docling v2 en 100% de páginas).
* **$B_3$ (`ADAPTIVE_ROUTER`):** Política condicional adaptativa model-free.

---

## 4. PROTOCOLO EXPERIMENTAL EN DOS FASES (Control C02)

```text
┌────────────────────────────────────────────────────────┐
│ FASE 1: CALIBRACIÓN EN DEV (19 Páginas)                │
│ 1. Extracción de features F1..F6 sobre DEV             │
│ 2. Ajuste fino de umbrales tau                         │
│ 3. Verificación de reglas y generación de hash SHA-256 │
│ 4. DECLARACIÓN FORMAL: ROUTER_FREEZE = TRUE            │
└──────────────────────────┬─────────────────────────────┘
                           │
            BARRERA DE SELLADO INMUTABLE
                           │
┌──────────────────────────▼─────────────────────────────┐
│ FASE 2: EVALUACIÓN EN TEST (19 Páginas Holdout)        │
│ 1. Extracción con B0, B1, B2 y B3 congelado            │
│ 2. Adjudicación humana ciega (TOOL_ALPHA..GAMMA)       │
│ 3. Cálculo de métricas preregistradas                  │
│ 4. Adjudicación de Exit Gate                           │
└────────────────────────────────────────────────────────┘
```

---

## 5. CRITERIOS DE SALIDA (EXIT GATE)

| Dictamen | Condición Metodológica |
|---|---|
| **PASS** | $	ext{MISSED\_ESCALATION\_RATE} \le 10\% \land ar{Q}(B_3) \ge ar{Q}(B_2) - 0.15 \land 	ext{Relative\_Cost}(B_3) \le 0.50$ |
| **PARTIAL** | Router eficaz en ciertas tipologías pero $	ext{MISSED\_ESCALATION} \in (10\%, 20\%]$ o reducción de costo $< 50\%$ |
| **FAIL** | $	ext{MISSED\_ESCALATION\_RATE} > 20\%$ o calidad inferior al baseline rápido $B_1$ |
| **INCONCLUSIVE** | Ausencia de celdas válidas en adjudicación o fallo en el cegamiento criptográfico |

---

## 6. INVARIANTES DE PRODUCCIÓN

```text
DATABASE_CHANGES         = 0 (data/web_state/*.db inmutables)
V1_RUNTIME_MODIFIED      = FALSE
PRODUCTION_SELECTION     = NOT_PERFORMED
PROBE_1_EXECUTION        = NOT_STARTED
LOCAL_RUN_PERMITTED      = FALSE (Solo diseño y preflight)
```
