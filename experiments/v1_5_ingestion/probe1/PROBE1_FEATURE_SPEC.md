# TALOS V1.5 — INGESTION INTELLIGENCE LAB
## PROBE-1: ESPECIFICACIÓN OPERACIONAL Y MATEMÁTICA DE FEATURES (C03)

**Versión:** 1.0.1-canonical  
**Fecha:** 2026-10-05  
**Fase:** Ingestion Intelligence Lab (v2.0)  
**Experimento:** `PROBE-1: Adaptive Structural Routing`  
**Estado:** `FROZEN_SPECIFICATION`  
**Autoridad:** Directiva Canónica v1.0.1 (Control C03)  
**Aislamiento:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE`  

---

## 1. PRINCIPIOS GENERALES DE EXTRACCIÓN RÁPIDA

El enrutador adaptativo evalúa exclusivamente características geométricas, vectoriales y léxicas obtenibles directamente del contenedor PDF mediante inspección determinista de baja sobrecarga (tiempo esperado de inspección: $< 10	ext{ ms/página}$).

Queda terminantemente prohibido:
1. Emplear modelos de lenguaje (LLMs) o redes neuronales para la extracción de features.
2. Calcular embeddings vectoriales densos sobre la página para tomar decisiones de ruteo.
3. Invocar Docling v2 u OCR como parte del proceso de extracción de features (violación de causalidad del enrutador).

---

## 2. CATÁLOGO OPERACIONAL DE FEATURES

### 2.1. Feature 1: `dwg_count` (Recuento de Trazos Vectoriales)

* **Definición Operacional:** Número entero de comandos de dibujo vectorial independientes devueltos por el motor PyMuPDF (`page.get_drawings()`) dentro del *MediaBox* de la página.
* **Fórmula Matemática:**
  $$	ext{dwg\_count}(p) = |\{ d \in 	ext{page.get\_drawings}(p) : 	ext{area}(d[	ext{'rect'}]) > 0 \}|$$
* **Fuente:** `pymupdf.Page.get_drawings()`.
* **Unidades:** Entidades de trazado vectorial / página (adimensional, entero no negativo).
* **Umbral Preliminar en DEV:** $	au_{	ext{dwg}} \ge 15$.
* **Tratamiento de Casos Borde:**
  - *Trazos vacíos:* Comandos con `items` vacíos o rectángulos degenerados ($	ext{width} = 0 \lor 	ext{height} = 0$) son excluidos formalmente.
  - *Overlays decorativos / Marcas de agua:* Rectángulos que abarcan $> 90\%$ del área total de la página se clasifican como bordes de página/fondos y no se computan en el recuento de figuras estructurales.
  - *Páginas rotadas:* PyMuPDF normaliza automáticamente las coordenadas al marco de rotación visual (`page.rect`). Se utiliza el espacio de coordenadas visuales transformadas.
  - *Páginas recortadas:* Se restringen los trazados a la intersección con `page.cropbox`.
* **Referencia de Implementación:**
  ```python
  def compute_dwg_count(page: pymupdf.Page) -> int:
      page_area = page.rect.width * page.rect.height
      valid_dwgs = [
          d for d in page.get_drawings()
          if (d["rect"].width > 0 and d["rect"].height > 0)
          and (d["rect"].width * d["rect"].height < 0.90 * page_area)
      ]
      return len(valid_dwgs)
  ```

---

### 2.2. Feature 2: `table_grid_score` (Densidad de Cuadrícula Tabular Ortogonal)

* **Definición Operacional:** Métrica continua que cuantifica el grado de intersección o coincidencia ortogonal de líneas horizontales y verticales que conforman cuadrículas o celdas de tablas cerradas.
* **Fórmula Matemática:**
  $$	ext{table\_grid\_score}(p) = rac{\min(N_{	ext{horiz}}, N_{	ext{vert}})}{\max(1, \ln(1 + 	ext{char\_count}(p)))} 	imes \mathbf{1}_{\{N_{	ext{intersections}} \ge 4\}}$$
  donde:
  - $N_{	ext{horiz}}$: número de segmentos vectoriales con $|\Delta y| \le 1.5	ext{ pt}$ y longitud $\ge 50	ext{ pt}$.
  - $N_{	ext{vert}}$: número de segmentos vectoriales con $|\Delta x| \le 1.5	ext{ pt}$ y longitud $\ge 20	ext{ pt}$.
  - $N_{	ext{intersections}}$: número de puntos de corte ortogonales entre segmentos horizontales y verticales con tolerancia espacial $\epsilon \le 3.0	ext{ pt}$.
* **Fuente:** Análisis de segmentos de línea en `pymupdf.Page.get_drawings()`.
* **Unidades:** Score adimensional continuo en $[0, \infty)$.
* **Significado de $\ge 1.0$:** Indica la presencia inequívoca de al menos una matriz bidimensional estructurada con múltiples filas y columnas interconectadas.
* **Umbral Preliminar en DEV:** $	au_{	ext{grid}} \ge 1.0$.
* **Tratamiento de Casos Borde:**
  - *Líneas punteadas / Dashed:* Segmentos colineales con separaciones $\le 4	ext{ pt}$ se fusionan en un único segmento continuo antes de evaluar intersecciones.
  - *Reglas horizontales decorativas individuales:* Una única línea horizontal divisoria (ej. separador de encabezado) genera $N_{	ext{vert}} = 0 \implies 	ext{table\_grid\_score} = 0$.
* **Referencia de Implementación:**
  ```python
  def compute_table_grid_score(page: pymupdf.Page) -> float:
      # Segment filtering: horiz vs vert with epsilon tolerance 1.5pt
      # Intersection detection with tolerance 3.0pt
      # Returns continuous score
      ...
  ```

---

### 2.3. Feature 3: `parallel_overlap` (Solapamiento Horizontal Paralelo)

* **Definición Operacional:** Indicador booleano que determina si existen dos o más flujos de información independientes (ej. diagrama de flujo vectorial y pseudocódigo textual) ocupando bandas verticales contiguas y solapadas en el eje horizontal $X$, generando riesgo de entrecruzamiento lineal en PyMuPDF.
* **Fórmula Matemática:**
  $$	ext{parallel\_overlap}(p) = \mathbf{1}_{\left\{ \exists b_{	ext{text}} \in \mathcal{B}_{	ext{text}}, b_{	ext{vec}} \in \mathcal{B}_{	ext{vec}} \;:\; 	ext{IoU}_Y(b_{	ext{text}}, b_{	ext{vec}}) > 0.30 \land |x_{	ext{mid}}(b_{	ext{text}}) - x_{	ext{mid}}(b_{	ext{vec}})| > 100	ext{ pt} ight\}}$$
  donde:
  - $\mathcal{B}_{	ext{text}}$ es el conjunto de cajas de texto con al menos 3 líneas.
  - $\mathcal{B}_{	ext{vec}}$ es el bounding box envolvente de cúmulos de trazos vectoriales.
  - $	ext{IoU}_Y$ es el grado de solapamiento en la proyección vertical del eje $Y$.
* **Fuente:** Bounding boxes combinados de `page.get_text("blocks")` y `page.get_drawings()`.
* **Unidades:** Booleano binario $\{0, 1\}$.
* **Umbral Preliminar en DEV:** `parallel_overlap = TRUE`.
* **Tratamiento de Casos Borde:**
  - *Imágenes incrustadas al pie:* Si $	ext{IoU}_Y \le 0.10$, no se considera disposición paralela.
  - *Texto dentro de figuras:* Bloques textuales contenidos estrictamente dentro de un trazado ($b_{	ext{text}} \subset b_{	ext{vec}}$) se excluyen de la condición de paralelismo horizontal para no confundir etiquetas de diagramas con pseudocódigo paralelo.

---

### 2.4. Feature 4: `code_block_density` (Densidad de Sintaxis Algorítmica)

* **Definición Operacional:** Proporción de líneas de texto de la página que contienen palabras reservadas formales del lenguaje algorítmico UPSAM / pseudocódigo (`inicio`, `fin`, `si`, `entonces`, `sino`, `mientras`, `hacer`, `para`, `hasta`, `escribir`, `leer`, `repetir`).
* **Fórmula Matemática:**
  $$	ext{code\_block\_density}(p) = rac{|\{ l \in 	ext{lines}(p) : 	ext{contains\_keyword}(l, \mathcal{K}_{	ext{algo}}) \}|}{\max(1, |	ext{lines}(p)|)}$$
  donde $\mathcal{K}_{	ext{algo}} = \{	ext{"inicio"}, 	ext{"fin"}, 	ext{"si"}, 	ext{"entonces"}, 	ext{"mientras"}, 	ext{"hacer"}, \dots\}$.
* **Fuente:** Tokenización léxica rápida de líneas obtenidas vía `page.get_text("text").splitlines()`.
* **Unidades:** Ratio continuo acotado en $[0, 1]$.
* **Umbral Preliminar en DEV:** $	au_{	ext{code}} \ge 0.20$ (al menos el $20\%$ de las líneas presentan estructura algorítmica).
* **Tratamiento de Casos Borde:**
  - *Mención aislada en prosa:* Palabras reservadas que aparecen como parte de oraciones normales en párrafos largos (líneas de $> 80$ caracteres) tienen peso amortiguado $0.2	imes$ frente a líneas cortas típicas de código algorítmico ($\le 50$ caracteres).

---

### 2.5. Feature 5: `indented_blocks` (Recuento de Bloques con Sangría Jerárquica)

* **Definición Operacional:** Recuento de bloques de líneas consecutivas cuyo margen izquierdo ($x_0$) presenta una sangría estructural respecto al margen izquierdo base de la página ($\Delta x_0 \ge 18	ext{ pt}$, equivalente a 2 espacios o tabulación típica).
* **Fórmula Matemática:**
  $$	ext{indented\_blocks}(p) = |\{ b \in 	ext{blocks}(p) : x_0(b) - x_{	ext{base}}(p) \ge 18	ext{ pt} \land 	ext{line\_count}(b) \ge 2 \}|$$
* **Fuente:** Coordenadas $x_0$ de bloques en `page.get_text("blocks")`.
* **Unidades:** Entero no negativo (recuento de bloques).
* **Umbral Preliminar en DEV:** $	au_{	ext{indent}} \ge 3$ bloques.
* **Tratamiento de Casos Borde:**
  - *Listas con viñetas:* Viñetas con un solo elemento no configuran bloque algorítmico anidado. Se exige $	ext{line\_count}(b) \ge 2$.

---

### 2.6. Feature 6: `dot_leader_count` (Densidad de Líderes de Puntos)

* **Definición Operacional:** Número de líneas de texto que contienen secuencias continuas de al menos tres puntos tipográficos sucesivos (`...` o `. . .`) con terminación numérica, característicos de tablas de contenidos (TOC) e índices analíticos.
* **Fórmula Matemática:**
  $$	ext{dot\_leader\_count}(p) = |\{ l \in 	ext{lines}(p) : 	ext{regex\_match}(l, 	exttt{r"\.{3,}\s*\d+$"}) \}|$$
* **Fuente:** Análisis de expresiones regulares sobre `page.get_text("text").splitlines()`.
* **Unidades:** Entero no negativo (líneas reconocidas).
* **Umbral Preliminar en DEV:** $	au_{	ext{dots}} \ge 3$ líneas.
* **Tratamiento de Casos Borde:**
  - *Puntos suspensivos narrativos:* Puntos suspensivos que terminan con palabras de prosa narrativa (ej. *"y así sucesivamente..."*) no tienen dígito final y quedan excluidos por la expresión regular.

---

## 3. RESUMEN DE ESPECIFICACIÓN Y PARÁMETROS

| Feature ID | Nombre | Tipo | Rango | Umbral Hipotético (DEV) | Fuente PyMuPDF |
|---|---|---|---|---|---|
| $F_1$ | `dwg_count` | Entero | $[0, \infty)$ | $\ge 15$ | `page.get_drawings()` |
| $F_2$ | `table_grid_score` | Continuo | $[0, \infty)$ | $\ge 1.0$ | `page.get_drawings()` |
| $F_3$ | `parallel_overlap` | Booleano | $\{0, 1\}$ | `TRUE` | `get_text("blocks")` + `get_drawings()` |
| $F_4$ | `code_block_density` | Continuo | $[0, 1]$ | $\ge 0.20$ | `get_text("text")` |
| $F_5$ | `indented_blocks` | Entero | $[0, \infty)$ | $\ge 3$ | `get_text("blocks")` |
| $F_6$ | `dot_leader_count` | Entero | $[0, \infty)$ | $\ge 3$ | `get_text("text")` |

Todas las features están operacionalmente especificadas, son deterministas y computables en tiempo acotado sin acceso a ningún modelo externo.
