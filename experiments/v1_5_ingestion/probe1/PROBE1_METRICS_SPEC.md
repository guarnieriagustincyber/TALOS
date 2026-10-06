# TALOS V1.5 — INGESTION INTELLIGENCE LAB
## PROBE-1: ESPECIFICACIÓN MATEMÁTICA DE MÉTRICAS Y EVALUACIÓN PARETO (C07)

**Versión:** 1.0.1-canonical  
**Fecha:** 2026-10-05  
**Fase:** Ingestion Intelligence Lab (v2.0)  
**Experimento:** `PROBE-1: Adaptive Structural Routing`  
**Estado:** `FROZEN_METRICS`  
**Autoridad:** Directiva Canónica v1.0.1 (Control C07)  
**Aislamiento:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE`  

---

## 1. MATRIZ DE CONFUSIÓN DEL ENRUTADOR

Para el conjunto de evaluación holdout $	ext{TEST}$ ($|	ext{TEST}| = 19$ páginas), se define la matriz de confusión respecto a la verdad fundamental $	ext{DOCLING\_BENEFICIAL}$:

| Ground Truth (`DOCLING_BENEFICIAL`) | Decisión del Router = `DOCLING` | Decisión del Router = `FAST` (`PyMuPDF`) | Total Filas |
|---|---|---|---|
| **`TRUE`** (Docling aporta beneficio) | **True Positive ($TP$)** | **Missed Escalation ($FN$)** | $P = TP + FN$ |
| **`FALSE`** (Docling no aporta beneficio) | **False Escalation ($FP$)** | **True Negative ($TN$)** | $N = FP + TN$ |
| **Total Columnas** | $TP + FP$ | $FN + TN$ | $|	ext{TEST}| = P + N$ |

---

## 2. MÉTRICAS CRÍTICAS DE ENRUTAMIENTO

### 2.1. Missed Escalation Rate (Métrica de Seguridad Estructural — CRÍTICA)
Mide la proporción de páginas donde Docling era materialmente beneficioso pero el enrutador falló en detectarlo y las despachó al extractor rápido.

$$	ext{MISSED\_ESCALATION\_RATE} = rac{FN}{TP + FN} = rac{|\{ p \in 	ext{TEST} : 	ext{DOCLING\_BENEFICIAL}(p) = 	ext{TRUE} \land 	ext{ROUTER}(p) = 	ext{FAST} \}|}{|\{ p \in 	ext{TEST} : 	ext{DOCLING\_BENEFICIAL}(p) = 	ext{TRUE} \}|}$$

* **Regla Inviolable de Denominador Cero:** Si $TP + FN = 0$ (es decir, ninguna página del holdout se beneficiaba de Docling):
  $$	ext{MISSED\_ESCALATION\_RATE} = \mathbf{NOT\_APPLICABLE} \; (	ext{N/A})$$
  **Bajo ninguna circunstancia se reportará `0%`.**
* **Umbral de Tolerancia Preregistrado:** $	ext{MISSED\_ESCALATION\_RATE} \le 10.0\%$. Un valor superior a $0.10$ implica rechazo del router por pérdida pedagógica inaceptable.

### 2.2. False Escalation Rate (Métrica de Costo Innecesario)
Mide la proporción de páginas simples despachadas a Docling sin justificación estructural.

$$	ext{FALSE\_ESCALATION\_RATE} = rac{FP}{FP + TN} = rac{|\{ p \in 	ext{TEST} : 	ext{DOCLING\_BENEFICIAL}(p) = 	ext{FALSE} \land 	ext{ROUTER}(p) = 	ext{DOCLING} \}|}{|\{ p \in 	ext{TEST} : 	ext{DOCLING\_BENEFICIAL}(p) = 	ext{FALSE} \}|}$$

* **Regla de Denominador Cero:** Si $FP + TN = 0$, el resultado es estrictamente `NOT_APPLICABLE (N/A)`.

### 2.3. Precisión, Recall y Exactitud del Router

* **Router Accuracy:**
  $$	ext{ACCURACY} = rac{TP + TN}{TP + TN + FP + FN} = rac{TP + TN}{19}$$
* **Router Precision:**
  $$	ext{PRECISION} = egin{cases} rac{TP}{TP + FP} & 	ext{si } TP + FP > 0 \ 	ext{N/A} & 	ext{si } TP + FP = 0 \end{cases}$$
* **Router Recall:**
  $$	ext{RECALL} = egin{cases} rac{TP}{TP + FN} = 1 - 	ext{MISSED\_ESCALATION\_RATE} & 	ext{si } TP + FN > 0 \ 	ext{N/A} & 	ext{si } TP + FN = 0 \end{cases}$$

---

## 3. MÉTRICAS DE CALIDAD ESTRUCTURAL GLOBAL

Para cada condición experimental $S \in \{B_0, B_1, B_2, B_3\}$:
* $B_0$: `ALL_PYPDF`
* $B_1$: `ALL_PYMUPDF`
* $B_2$: `ALL_DOCLING`
* $B_3$: `ADAPTIVE_ROUTER`

Se computa la Calidad Media Estructural ($ar{Q} \in [0, 3]$):
$$ar{Q}(S) = rac{1}{|	ext{TEST}|} \sum_{p \in 	ext{TEST}} \left( rac{1}{|\mathcal{D}_{	ext{app}}(p)|} \sum_{d \in \mathcal{D}_{	ext{app}}(p)} 	ext{Score}(S, p, d) ight)$$

---

## 4. TELEMETRÍA DE RENDIMIENTO Y COSTO COMPUTACIONAL

Para cada condición se reporta:
1. **Latencia Media por Página:** $ar{L}_{	ext{ms}}(S)$.
2. **Latencia Mediana por Página:** $\widetilde{L}_{	ext{ms}}(S)$.
3. **Latencia Percentil 95 ($p95$):** $L_{p95}(S)$.
4. **Costo Relativo de Cómputo vs ALL_DOCLING:**
   $$	ext{Relative\_Cost}(B_3) = rac{T_{	ext{total}}(B_3)}{T_{	ext{total}}(B_2)}$$
   donde $T_{	ext{total}}(B_3) = \sum_{p \in 	ext{TEST}} \left( L_{	ext{inspection}}(p) + L_{	ext{selected\_extractor}}(p) ight)$.

---

## 5. EVALUACIÓN Y FRONTERA DE PARETO

Se construye la curva bidimensional de compensación:
$$	ext{Trade-Off: } 	ext{Calidad Estructural } ar{Q}(S) \quad 	ext{vs} \quad 	ext{Latencia Media } ar{L}_{	ext{ms}}(S)$$

El enrutador adaptativo ($B_3$) se declara **Pareto-Eficiente / Exitoso** si y solo si:
$$ar{Q}(B_3) \ge ar{Q}(B_2) - 0.15 \quad \land \quad T_{	ext{total}}(B_3) \le 0.50 	imes T_{	ext{total}}(B_2)$$
*(Alcanza calidad prácticamente equivalente a ejecutar Docling en todo el capítulo, pero utilizando menos de la mitad del cómputo).*
