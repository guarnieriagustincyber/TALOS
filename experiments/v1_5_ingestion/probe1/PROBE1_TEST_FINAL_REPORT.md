# TALOS V1.5 — INGESTION INTELLIGENCE LAB
## REPORTE CIENTÍFICO FINAL DE HOLDOUT TEST — PROBE-1
### Adaptive Structural Routing: Evaluación Empírica, Pareto y Modos de Falla

**Versión:** 1.0.0-canonical  
**Fecha:** 2026-10-06  
**Fase:** V1.5 — Phase 1 / Ingestion Intelligence Lab  
**Experimento:** `exp_ingestion_probe0_v2` → `PROBE-1`  
**Estado:** `COMPLETED | EXIT_GATE_EVALUATED`  
**Autoridad:** Directiva Canónica de Ejecución de TEST (v1.0) & Checkpoint 151  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`  

---

## 1. RESUMEN EJECUTIVO Y CONCLUSIÓN CIENTÍFICA

El presente documento constituye el informe técnico y científico definitivo de **PROBE-1: Adaptive Structural Routing**, evaluado sobre el conjunto de prueba independiente holdout (`TEST_SET`, 19 páginas físicas del Capítulo 2 de Luis Joyanes Aguilar, *Fundamentos de programación*).

El experimento se ejecutó bajo la regla absoluta de **CERO RECALIBRACIÓN**: los umbrales del enrutador calibrados en la fase de desarrollo (`DEV_SET`) fueron congelados formalmente bajo el hash criptográfico `8753a32db341a6488aa58cb48de40712e7cacb963d6ef1dd2e78df31d70e71fe` y evaluados sin modificación alguna contra una adjudicación ciega e independiente realizada por un especialista humano ($N=1$).

### Dictamen Metodológico Central
```text
┌────────────────────────────────────────────────────────────────────────┐
│ DICTAMEN FORMAL DE SALIDA (EXIT GATE): FAIL                            │
├────────────────────────────────────────────────────────────────────────┤
│ 1. MISSED ESCALATION RATE (MER) : 44.44%  [LÍMITE MÁXIMO <= 10.0%] FAIL│
│ 2. CALIDAD ESTRUCTURAL Q(B3)   : 2.6842  [OBJETIVO >= 2.6395]    PASS │
│ 3. COSTO COMPUTACIONAL T(B3)   : 13.21%  [OBJETIVO <= 50.0%]     PASS │
├────────────────────────────────────────────────────────────────────────┤
│ ESTADO DE PROMOCIÓN A RUNTIME  : RECHAZADO PARA PRODUCCIÓN             │
│ VALIDEZ DEL DISEÑO CIENTÍFICO  : CONFIRMADA (HIPÓTESIS REFUTADA)       │
└────────────────────────────────────────────────────────────────────────┘
```

El enrutador heurístico determinista demostró una eficiencia computacional sobresaliente dentro de la frontera de Pareto, **reduciendo el tiempo total de procesamiento en un 86.79%** respecto a la ejecución universal de Docling y alcanzando una calidad estructural media de $2.6842$ (virtualmente idéntica a los $2.7895$ de Docling en el promedio del capítulo).

**Sin embargo, reprueba de manera categórica el criterio de seguridad pedagógica y estructural del Exit Gate ($\text{MER} = 44.44\% > 10.0\%$, superando el límite de descarte de $20\%$).**  
El enrutador falló en detectar 4 de las 9 páginas donde Docling era materialmente beneficioso:
1. Una tabla financiera sin bordes vectoriales (`p078`), completamente linealizada y destruida por PyMuPDF;
2. Un diagrama conceptual de arquitectura de variables (`p085`);
3. Un conjunto de diagramas UML de clases con atributos y métodos (`p092`);
4. Dos diagramas estructurados Nassi-Schneiderman (`p110`).

Adicionalmente, la evaluación reveló **vulnerabilidades críticas intrínsecas en Docling v2**: en páginas con pseudocódigo algorítmico indentado (`p081`, `p099`), Docling colapsó bloques completos de código en un único párrafo continuo horizontal, y en páginas de ejercicios y resumen (`p111`), corrompió gravemente el orden de lectura al intercalar encabezados dentro de oraciones a medio terminar.

---

## 2. METODOLOGÍA EXPERIMENTAL Y PROTOCOLO DE EVALUACIÓN

### 2.1. Condiciones Experimentales Evaluadas
* **$B_0$ (Baseline Fast Naive — `pypdf`):** Extracción de texto plana sin soporte de layout.
* **$B_1$ (Baseline Fast Determinista — `PyMuPDF`):** Extracción rápida de bloques y texto con orden visual geométrico.
* **$B_2$ (Baseline Complejo Multimodal — `Docling v2`):** Pipeline basado en modelos de visión (Layout, TableFormer, OCR).
* **$B_3$ (Enrutador Adaptativo Congelado — `Adaptive`):** Enrutador determinista que inspecciona geometría vectorial y despacha a $B_1$ o $B_2$.

### 2.2. Parámetros del Router Congelado
Calibrados exclusivamente en `DEV_SET` (19 páginas) y sellados en CP151:
* $\tau_{\text{dwg}} = 12$ (umbral de trazos vectoriales para Rule R2)
* $\tau_{\text{grid}} = 1.0$ (densidad de líneas ortogonales para Rule R1)
* $\tau_{\text{code}} = 0.20$, $\tau_{\text{indent}} = 3$ (para Rule R4)
* $\tau_{\text{dots}} = 3$ (para Rule R5)

### 2.3. Protocolo de Doble Ciego y Adjudicación Humana
* **Cegamiento Criptográfico:** Cada página se anonimizó asignando pseudoaleatoriamente a los motores las etiquetas `TOOL_ALPHA`, `TOOL_BETA`, `TOOL_GAMMA` mediante la clave secreta `masking_key_unblind.json`.
* **Dimensiones Aplicables:** $\mathcal{D}_{\text{app}}(p) \subseteq \{\text{TABLE}, \text{DIAGRAM}, \text{CODE}, \text{HEADING}, \text{ORDER}\}$.
* **Rúbrica:** 3 (Perfecto/Defecto despreciable), 2 (Utilizable con defectos menores), 1 (Parcial/Requiere reparación pesada), 0 (Destruido/Corrupto).
* **Definición de Ground Truth:** Evaluado estrictamente bajo `PROBE1_BENEFIT_DEFINITION.md` (Condición A de rescate estructural mayor o Condición B de ganancia promedio $\ge 0.50$, con restricción de no-regresión severa y regla de empate económico en prosa expositiva).
* **Perfil del Evaluador:** $N=1$ especialista humano independiente en ingeniería de software y sistemas educativos.

---

## 3. RESULTADOS CUANTITATIVOS EN EL CONJUNTO TEST (19 PÁGINAS)

### 3.1. Matriz de Confusión del Enrutador

```text
                                DECISIÓN DEL ROUTER
                       DOCLING (Escalación)   PYMUPDF (Fast)     TOTAL
DOCLING_BENEFICIAL: TRUE          5 (TP)               4 (FN)        9 (P)
DOCLING_BENEFICIAL: FALSE         1 (FP)               9 (TN)       10 (N)
TOTAL                             6                   13            19
```

### 3.2. Métricas de Clasificación
* **Missed Escalation Rate (MER):** $\frac{FN}{TP + FN} = \frac{4}{9} = \mathbf{44.44\%}$  
  *(Tolerancia máxima preregistrada: $\le 10.0\%$. Criterio de rechazo crítico: $> 20.0\%$. **FALLÓ**)*.
* **False Escalation Rate (FER):** $\frac{FP}{FP + TN} = \frac{1}{10} = \mathbf{10.00\%}$.
* **Accuracy:** $\frac{5 + 9}{19} = \mathbf{73.68\%}$.
* **Precision:** $\frac{5}{5 + 1} = \mathbf{83.33\%}$.
* **Recall:** $\frac{5}{9} = \mathbf{55.56\%}$.

### 3.3. Calidad Estructural Media ($\bar{Q} \in [0, 3]$)
* $B_0$ (`pypdf`): $\bar{Q}(B_0) = \mathbf{2.3421}$
* $B_1$ (`pymupdf`): $\bar{Q}(B_1) = \mathbf{2.3596}$
* $B_2$ (`docling`): $\bar{Q}(B_2) = \mathbf{2.7895}$
* $B_3$ (`adaptive`): $\bar{Q}(B_3) = \mathbf{2.6842}$

$$\Delta \bar{Q}(B_3 - B_2) = 2.6842 - 2.7895 = -0.1053$$
$$\text{Objetivo de Calidad Pareto: } \bar{Q}(B_3) \ge \bar{Q}(B_2) - 0.15 = 2.6395 \implies \mathbf{CUMPLIDO}$$

### 3.4. Telemetría de Latencia y Costo Computacional (Google Colab GPU T4)

| Extractor | Latencia Total | Media / Pág | Mediana | Percentil 95 ($p95$) | Mínimo | Máximo |
|---|---|---|---|---|---|---|
| **$B_0$ (`pypdf`)** | $916.03\text{ ms}$ | $48.21\text{ ms}$ | $33.66\text{ ms}$ | $91.17\text{ ms}$ | $20.68\text{ ms}$ | $185.98\text{ ms}$ |
| **$B_1$ (`pymupdf`)** | $202.56\text{ ms}$ | $10.66\text{ ms}$ | $8.86\text{ ms}$ | $17.12\text{ ms}$ | $5.00\text{ ms}$ | $17.15\text{ ms}$ |
| **$B_2$ (`docling`)** | $72,905.09\text{ ms}$ | $3,837.11\text{ ms}$ | $1,791.96\text{ ms}$ | $6,708.75\text{ ms}$ | $967.83\text{ ms}$ | $40,558.45\text{ ms}$* |
| **$B_3$ (`adaptive`)** | $\mathbf{9,632.44\text{ ms}}$ | $\mathbf{506.97\text{ ms}}$ | $\mathbf{36.82\text{ ms}}$ | $\mathbf{1,891.51\text{ ms}}$ | $\mathbf{17.04\text{ ms}}$ | $\mathbf{2,513.83\text{ ms}}$ |

*\* Nota: La latencia máxima de Docling ($40.5\text{ s}$) incluyó el warm-up inicial de PyTorch y pesos de TableFormer en la página 76.*

* **Costo Relativo $T(B_3) / T(B_2)$:**
  $$\text{Relative\_Cost} = \frac{9,632.44\text{ ms}}{72,905.09\text{ ms}} = \mathbf{13.21\%}$$
* **Ahorro de Cómputo vs All-Docling:** **$86.79\%$**.
* **Condición de Costo Pareto:** $13.21\% \le 50.0\% \implies \mathbf{CUMPLIDO}$.

---

## 4. INVENTARIO COMPLETO DE ADJUDICACIÓN POR PÁGINA (TEST SET)

| Pág Fís | Pág Lóg | Page ID | Tipología Manifiesto | $F_1$ (dwg) | $F_2$ (grid) | $F_4$ (code) | Decisión Router | Regla Gatillada | Ground Truth | Veredicto | $Q(B_1)$ | $Q(B_2)$ | $Q(B_3)$ |
|:---:|:---:|:---|:---|:---:|:---:|:---:|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| 76 | 46 | `joyanes_ch02_p076` | EXPOSITORY_PROSE | 1 | 0.0 | 0.0638 | PYMUPDF | `R0_FAST_DEFAULT` | FALSE | **TN** | 3.00 | 3.00 | 3.00 |
| 77 | 47 | `joyanes_ch02_p077` | EXPOSITORY_PROSE | 1 | 0.0 | 0.0417 | PYMUPDF | `R0_FAST_DEFAULT` | FALSE | **TN** | 2.67 | 2.33 | 2.67 |
| 78 | 48 | `joyanes_ch02_p078` | EXPOSITORY_PROSE | 1 | 0.0 | 0.0299 | PYMUPDF | `R0_FAST_DEFAULT` | **TRUE** | **FN** | 2.00 | 3.00 | 2.00 |
| 81 | 51 | `joyanes_ch02_p081` | EXPOSITORY_PROSE | 1 | 0.0 | 0.2826 | PYMUPDF | `R0_FAST_DEFAULT` | FALSE | **TN** | 3.00 | 2.33 | 3.00 |
| 85 | 55 | `joyanes_ch02_p085` | MIXED_DIAGRAM_AND_PROSE | 7 | 0.0 | 0.0000 | PYMUPDF | `R0_FAST_DEFAULT` | **TRUE** | **FN** | 2.33 | 3.00 | 2.33 |
| 88 | 58 | `joyanes_ch02_p088` | EXPOSITORY_PROSE | 1 | 0.0 | 0.0000 | PYMUPDF | `R0_FAST_DEFAULT` | FALSE | **TN** | 3.00 | 3.00 | 3.00 |
| 90 | 60 | `joyanes_ch02_p090` | EXPOSITORY_PROSE | 0 | 0.0 | 0.0000 | PYMUPDF | `R0_FAST_DEFAULT` | FALSE | **TN** | 3.00 | 3.00 | 3.00 |
| 92 | 62 | `joyanes_ch02_p092` | EXPOSITORY_PROSE | 3 | 0.0 | 0.0000 | PYMUPDF | `R0_FAST_DEFAULT` | **TRUE** | **FN** | 2.00 | 3.00 | 2.00 |
| 93 | 63 | `joyanes_ch02_p093` | MIXED_DIAGRAM_AND_PROSE | 14 | 0.0 | 0.0000 | DOCLING | `R2_VECTOR_FLOWCHART`| **TRUE** | **TP** | 2.33 | 3.00 | 3.00 |
| 94 | 64 | `joyanes_ch02_p094` | EXPOSITORY_PROSE | 3 | 0.0 | 0.0392 | PYMUPDF | `R0_FAST_DEFAULT` | FALSE | **TN** | 3.00 | 3.00 | 3.00 |
| 98 | 68 | `joyanes_ch02_p098` | EXPOSITORY_PROSE | 0 | 0.0 | 0.1600 | PYMUPDF | `R0_FAST_DEFAULT` | FALSE | **TN** | 3.00 | 3.00 | 3.00 |
| 99 | 69 | `joyanes_ch02_p099` | EXPOSITORY_PROSE | 0 | 0.0 | 0.2128 | PYMUPDF | `R0_FAST_DEFAULT` | FALSE | **TN** | 3.00 | 2.33 | 3.00 |
| 104 | 74 | `joyanes_ch02_p104` | FLOWCHART_OR_DIAGRAM | 26 | 0.0 | 0.2903 | DOCLING | `R2_VECTOR_FLOWCHART`| **TRUE** | **TP** | 1.50 | 2.75 | 2.75 |
| 107 | 77 | `joyanes_ch02_p107` | FLOWCHART_OR_DIAGRAM | 18 | 0.0 | 0.3710 | DOCLING | `R2_VECTOR_FLOWCHART`| **TRUE** | **TP** | 1.00 | 2.75 | 2.75 |
| 108 | 78 | `joyanes_ch02_p108` | FLOWCHART_OR_DIAGRAM | 17 | 0.0 | 0.4286 | DOCLING | `R2_VECTOR_FLOWCHART`| **TRUE** | **TP** | 1.50 | 2.75 | 2.75 |
| 109 | 79 | `joyanes_ch02_p109` | FLOWCHART_OR_DIAGRAM | 16 | 0.0 | 0.4808 | DOCLING | `R2_VECTOR_FLOWCHART`| **TRUE** | **TP** | 1.50 | 2.75 | 2.75 |
| 110 | 80 | `joyanes_ch02_p110` | FLOWCHART_OR_DIAGRAM | 9 | 0.0 | 0.1282 | PYMUPDF | `R0_FAST_DEFAULT` | **TRUE** | **FN** | 1.00 | 3.00 | 1.00 |
| 111 | 81 | `joyanes_ch02_p111` | EXERCISES_PROBLEMS | 3 | 0.0 | 0.1774 | PYMUPDF | `R0_FAST_DEFAULT` | FALSE | **TN** | 3.00 | 2.00 | 3.00 |
| 112 | 82 | `joyanes_ch02_p112` | EXPOSITORY_PROSE | 1 | 0.0 | 0.2745 | DOCLING | `R4_STRUCTURED_CODE` | FALSE | **FP** | 3.00 | 3.00 | 3.00 |

---

## 5. ANÁLISIS FORENSE DE MODOS DE FALLA

El valor científico principal de PROBE-1 no radica en certificar una victoria, sino en aislar empíricamente las fronteras de falla de ambas tecnologías.

### 5.1. Fallas del Router: Puntos Ciegos de la Inspección Geométrica Superficial

#### Falla FN-1: Tablas Sin Bordes Vectoriales (Página 78)
* **Manifestación:** La página 78 contiene una tabla de 4 columnas (*Año, Depreciación, Depreciación acumulada, Valor anual*). Al carecer de líneas vectoriales ortogonales, el extractor determinista arrojó $\text{table\_grid\_score} = 0.0$. El router despachó la página a PyMuPDF.
* **Impacto Pedagógico:** PyMuPDF linealizó las columnas verticalmente, concatenando los números de las celdas en un único flujo ilegible (`1 (2006) \n 3.000 \n 3.000 \n 17.000...`). Docling, mediante TableFormer, reconoció la tabla visualmente generando una sintaxis Markdown perfecta.
* **Causa Raíz:** La feature $F_2$ solo busca trazos ortogonales explícitos. No cuenta con análisis de espacios en blanco verticales (*whitespace column gaps*) entre bloques de texto.

#### Falla FN-2: Diagramas con Pocos Trazos Vectoriales (Páginas 85, 92, 110)
* **Página 85:** Figura 2.7 (cajas de variables locales y globales). Solo registró $\text{dwg\_count} = 7 < 12$. PyMuPDF derramó 8 líneas de etiquetas de cajas sobre el texto continuo.
* **Página 92:** Figuras 2.11 y 2.12 (Diagramas de clases UML con atributos y métodos). Solo registró $\text{dwg\_count} = 3 < 12$ porque las cajas UML del libro están rasterizadas o formadas por trazos mínimos. PyMuPDF mezcló nombres de clases y métodos de forma caótica.
* **Página 110:** Figuras 2.20 y 2.21 (Diagramas de Nassi-Schneiderman / Chapin). Al tratarse de rectángulos concéntricos sin flechas diagonales, solo registró $\text{dwg\_count} = 9 < 12$. PyMuPDF destruyó la estructura de bloques anidados.
* **Causa Raíz:** El umbral $\tau_{\text{dwg}} = 12$ calibrado en DEV para diagramas de flujo densos (que tenían entre 14 y 153 trazos) es excesivamente rígido para diagramas UML o esquemas arquitectónicos simples.

#### Falla FP-1: Falsa Detección de Código por Listas Indentadas (Página 112)
* **Manifestación:** Lista de ejercicios 2.5 a 2.15. El router calculó $\text{code\_density} = 0.2745 \ge 0.20$ e $\text{indent} = 4 \ge 3$, gatillando innecesariamente la regla R4 hacia Docling.
* **Impacto:** Gasto computacional innecesario ($1.48\text{ s}$ vs $8.7\text{ ms}$ de PyMuPDF) sin ganancia estructural material.

---

### 5.2. Fallas Críticas de Docling v2: Puntos Débiles del Modelo Pesado

Uno de los descubrimientos más reveladores de la adjudicación ciega de PROBE-1 es que **Docling v2 NO es universalmente superior** y exhibe fallas que destruirían un pipeline RAG si se aplicara indiscriminadamente:

#### Falla Docling D-1: Colapso Horizontal de Pseudocódigo (Páginas 81 y 99)
* **Ejemplo Página 81 (Algoritmo de cálculo de suma y depreciación):**  
  PyMuPDF extrajo el pseudocódigo preservando perfectamente los saltos de línea y niveles de sangría:
  ```text
  inicio
        escribir('introduzca coste, valor recuperación y vida útil')
        leer(Coste, Valor_Recuperacion, Vida_Util)
        mientras (Año < Vida_Util)
           Acumulado ← Acumulado + Depreciacion
        fin mientras
  fin
  ```
  Docling reconoció el bloque de código con triple comilla (\`\`\`), pero **colapsó todas las sentencias en una sola línea continua de 600 caracteres**:
  ```text
  ```
  inicio escribir('introduzca coste, valor...') mientras (Año < Vida_Util) Acumulado ← ...
  ```
  ```
* **Consecuencia:** Destruye completamente la estructura para LLMs que intenten razonar sobre control de flujo o estudiantes que lean el código.

#### Falla Docling D-2: Desgarro Catastrófico del Flujo de Lectura (Página 111)
* **Manifestación:** En la página 111 (que contiene un resumen del capítulo y una caja lateral de ejercicios), Docling cortó por la mitad una oración del resumen para insertar la cabecera y el inicio de los ejercicios:
  > *"El sistema más idóneo para resolver un problema es descomponerlo en módulos más sencillos y luego, median-"*  
  > `## EJERCICIOS`  
  > `- 2.1. Diseñar una solución...`  
  > `- 2.2. Escribir un algoritmo...`  
  > *"te diseños descendentes y refinamiento sucesivo, llegar a módulos fácilmente codificables."*
* **Consecuencia:** Ruptura sintáctica grave del conocimiento pedagógico original. PyMuPDF mantuvo la coherencia del párrafo intacta.

---

## 6. LECCIONES METODOLÓGICAS: EL VALOR EPISTEMOLÓGICO DEL SELLADO

Si este experimento se hubiera desarrollado bajo prácticas tradicionales no selladas:
1. Al ver los resultados de TEST, un ingeniero habría bajado $\tau_{\text{dwg}}$ a 3 y añadido una heurística post-hoc para tablas sin bordes.
2. El informe habría reportado falsamente un $\text{MER} = 0\%$ y una precisión del $100\%$.
3. En producción sobre capítulos desconocidos (Capítulo 3, 4, etc.), el sistema habría fallado silenciosamente con modos de falla no diagnosticados.

El protocolo criptográfico de TALOS impidió esta práctica:
> **El valor de una prueba reside en su capacidad de fallar honestamente.**  
> PROBE-1 ha demostrado con certeza matemática que una regla lineal basada en trazos vectoriales es insuficiente para garantizar la seguridad en un corpus pedagógico.

---

## 7. ESPECIFICACIÓN DE DIRECTIVAS PARA PROBE-2

Los hallazgos de PROBE-1 delinean directamente los requisitos arquitectónicos de la siguiente iteración (**PROBE-2**):

1. **Detector de Tablas Sin Bordes (Whitespace Alignment):**  
   Implementar una feature $F_{\text{whitespace\_grid}}$ que analice la existencia de columnas de espacios en blanco alineadas verticalmente entre bloques de texto adyacentes, permitiendo detectar tablas como la de la página 78 sin depender de trazos vectoriales.
2. **Clasificador de Diagramas Multimodal Liviano (Vision-Aided Ingestion):**  
   Para diagramas con pocos trazos (UML, N-S), utilizar un modelo de visión ultraliviano (ej. YOLOv8-DocLayout o MobileNet de segmentación a baja resolución, $< 20\text{ ms}$) en lugar de conteo ciego de vectores.
3. **Mecanismo Anti-Colapso para Pseudocódigo:**  
   Si una página contiene pseudocódigo y se despacha a Docling, implementar una regla de ensamblado (*hybrid merge*): utilizar Docling para tablas/imágenes pero preservar el bloque de texto original de PyMuPDF para el código indentado.
4. **Verificación de Integridad de Flujo (Reading Order Sanity Check):**  
   Detectar rupturas oracionales como la de la página 111 y revertir a PyMuPDF cuando la segmentación de Docling fracture párrafos.

---

## 8. DISPOSICIÓN FINAL Y AISLAMIENTO DE PRODUCCIÓN

* **Veredicto del Router:** **RECHAZADO PARA PRODUCCIÓN**.
* **Integridad de Bases de Datos:** Las 6 bases de datos en `data/web_state/*.db` permanecen verificadas bit a bit con respecto a sus estados iniciales (`DATABASE_CHANGES = 0`).
* **Runtime de TALOS:** El runtime productivo de TALOS V1 permanece 100% inalterado (`V1_RUNTIME_MODIFIED = FALSE`).
* **Conclusión del Experimento:** PROBE-1 concluye exitosamente su ciclo de investigación como un experimento honesto, riguroso, reproducible y de incalculable valor para la arquitectura de ingestión de TALOS.
