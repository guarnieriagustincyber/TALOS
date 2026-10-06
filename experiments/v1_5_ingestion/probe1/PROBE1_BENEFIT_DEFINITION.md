# TALOS V1.5 — INGESTION INTELLIGENCE LAB
## PROBE-1: DEFINICIÓN FORMAL DE DOCLING_BENEFICIAL (C04)

**Versión:** 1.0.1-canonical  
**Fecha:** 2026-10-05  
**Fase:** Ingestion Intelligence Lab (v2.0)  
**Experimento:** `PROBE-1: Adaptive Structural Routing`  
**Estado:** `FROZEN_DEFINITION`  
**Autoridad:** Directiva Canónica v1.0.1 (Control C04)  
**Aislamiento:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE`  

---

## 1. FORMULACIÓN CATEGÓRICA

Se define la variable indicadora categórica binaria:
$$	ext{DOCLING\_BENEFICIAL}(p) \in \{	ext{TRUE}, 	ext{FALSE}\}$$

Esta variable representa la verdad fundamental (*ground truth*) sobre si la página física $p$ obtiene una ventaja pedagógica y estructural material al ser procesada por `Docling v2` en comparación con el baseline rápido determinista `PyMuPDF`.

> [!IMPORTANT]
> **Prohibición Epistémica de Definiciones Circulares:**
> Queda terminantemente prohibido definir `DOCLING_BENEFICIAL` como:
> 1. *"La salida de Docling coincide con lo esperado"*.
> 2. *"El score global de Docling es mayor que el de PyMuPDF"* (sin margen mínimo ni filtro de dimensiones).
> 3. *"El enrutador decidió despachar a Docling"*.

---

## 2. DETERMINACIÓN DE DIMENSIONES APLICABLES

Antes de cualquier comparación entre extractores, se define el conjunto de dimensiones estructurales objetivamente presentes en la página $p$:
$$\mathcal{D}_{	ext{app}}(p) \subseteq \mathcal{D}_{	ext{total}}$$
donde $\mathcal{D}_{	ext{total}} = \{	ext{TABLE}, 	ext{DIAGRAM}, 	ext{CODE}, 	ext{HEADING}, 	ext{ORDER}\}$.

* Si una página consiste exclusivamente en prosa narrativa continua sin tablas, código ni figuras:
  $$\mathcal{D}_{	ext{app}}(p) = \{	ext{HEADING}, 	ext{ORDER}\}$$
  Las dimensiones $	ext{TABLE}$, $	ext{DIAGRAM}$ y $	ext{CODE}$ reciben la etiqueta contractual **`NOT_APPLICABLE (N/A)`** y quedan excluidas de la evaluación.
* Si una página contiene un diagrama de flujo y pseudocódigo paralelo (ej. página 105):
  $$\mathcal{D}_{	ext{app}}(p) = \{	ext{DIAGRAM}, 	ext{CODE}, 	ext{HEADING}, 	ext{ORDER}\}$$

---

## 3. ADJUDICACIÓN DE PUNTAJES POR DIMENSIÓN

Para cada dimensión aplicable $d \in \mathcal{D}_{	ext{app}}(p)$, un evaluador humano ciego asigna puntajes estandarizados:
$$S_{	ext{docling}}(p, d) \in \{0, 1, 2, 3\} \quad 	ext{y} \quad S_{	ext{pymupdf}}(p, d) \in \{0, 1, 2, 3\}$$

conforme a la rúbrica formal:
* **3:** Estructura preservada correctamente sin corrupción.
* **2:** Estructura utilizable con defectos estéticos menores.
* **1:** Estructura parcialmente recuperada (requiere reconstrucción pesada).
* **0:** Estructura destruida o corrupta.

---

## 4. REGLA FORMAL DE BENEFICIO MATERIAL

Se declara formalmente:
$$	ext{DOCLING\_BENEFICIAL}(p) = 	ext{TRUE}$$
si y solo si se satisface al menos una de las dos condiciones siguientes:

### Condición A: Salto Estructural Crítico en Dimensión Mayor
$$\exists d \in \{	ext{TABLE}, 	ext{DIAGRAM}, 	ext{CODE}\} \cap \mathcal{D}_{	ext{app}}(p) \;:\; \left( S_{	ext{docling}}(p, d) - S_{	ext{pymupdf}}(p, d) \ge 1.0 ight) \land \left( S_{	ext{docling}}(p, d) \ge 2 ight)$$
sujeto a la restricción de no-regresión severa:
$$orall d' \in \mathcal{D}_{	ext{app}}(p), \quad S_{	ext{pymupdf}}(p, d') - S_{	ext{docling}}(p, d') \le 1.0$$
*(Interpretación: Docling rescata una tabla, código o diagrama haciéndolo utilizable [score $\ge 2$] donde PyMuPDF lo degradó o destruyó, sin destruir gravemente el orden de lectura ni los encabezados).*

### Condición B: Ganancia Estructural Promedio Significativa
$$ar{\Delta}(p) = rac{1}{|\mathcal{D}_{	ext{app}}(p)|} \sum_{d \in \mathcal{D}_{	ext{app}}(p)} \left( S_{	ext{docling}}(p, d) - S_{	ext{pymupdf}}(p, d) ight) \ge 0.50$$

En cualquier otro caso:
$$	ext{DOCLING\_BENEFICIAL}(p) = 	ext{FALSE}$$

---

## 5. TRATAMIENTO DE EMPATES Y CASOS ESPECIALES

1. **Regla de Empate (Tie-Break):**
   Si $S_{	ext{docling}}(p, d) = S_{	ext{pymupdf}}(p, d)$ para todas las dimensiones aplicables:
   $$	ext{DOCLING\_BENEFICIAL}(p) = 	ext{FALSE}$$
   *Justificación Económica y Metodológica:* Si PyMuPDF genera una representación idéntica o equivalente a Docling (ej. en prosa expositiva continua), el costo computacional de $pprox 20	imes$ de Docling es injustificado. La página NO se beneficia materialmente de Docling.
2. **Ambas herramientas fallan ($S_{	ext{docling}} \le 1 \land S_{	ext{pymupdf}} \le 1$):**
   Si ninguna herramienta logra una representación utilizable ($	ext{score} \ge 2$), Docling no aporta valor pedagógico utilizable:
   $$	ext{DOCLING\_BENEFICIAL}(p) = 	ext{FALSE}$$
3. **Páginas con $\mathcal{D}_{	ext{app}}(p) = \emptyset$:**
   Páginas en blanco o portadillas vacías se adjudican automáticamente como `DOCLING_BENEFICIAL = FALSE`.
