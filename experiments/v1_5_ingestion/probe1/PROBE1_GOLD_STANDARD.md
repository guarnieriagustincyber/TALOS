# TALOS V1.5 — INGESTION INTELLIGENCE LAB
## PROBE-1: GOLD STANDARD Y CRITERIO DE REFERENCIA INDEPENDIENTE (C05)

**Versión:** 1.0.1-canonical  
**Fecha:** 2026-10-05  
**Fase:** Ingestion Intelligence Lab (v2.0)  
**Experimento:** `PROBE-1: Adaptive Structural Routing`  
**Estado:** `FROZEN_STANDARD`  
**Autoridad:** Directiva Canónica v1.0.1 (Control C05)  
**Aislamiento:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE`  

---

## 1. PREGUNTA FUNDAMENTAL DE REFERENCIA

El Gold Standard de PROBE-1 no es un archivo de salida de ninguna herramienta evaluada. Es la especificación canónica que responde a la pregunta objetiva:

> **¿Qué estructura visual, semántica y jerárquica necesita preservar esta página para que un estudiante o un sistema de recuperación (RAG) pueda reconstruir el conocimiento pedagógico original sin alucinación ni ambigüedad?**

```text
PRINCIPIO DE INDEPENDENCIA EPISTÉMICA:
GOLD_STANDARD ≠ ALL_DOCLING
GOLD_STANDARD ≠ ALL_PYMUPDF
GOLD_STANDARD ≠ ALL_PYPDF
GOLD_STANDARD ≠ DECISIÓN_DEL_ROUTER
```

---

## 2. MECANISMO DE CONSTRUCCIÓN DE LA REFERENCIA

Para cada una de las 38 páginas del Capítulo 2 de Joyanes Aguilar, el Gold Standard se compone de:
1. **Inspección Visual Primaria:** Renderizado de alta resolución a 200 DPI (`data/pages_png/page_XXX.png`) como fuente visual inmutable.
2. **Geometría Vectorial del PDF:** Extracción de coordenadas exactas de líneas ortogonales, polígonos y fuentes tipográficas mediante inspección geométrica directa de bajo nivel.
3. **Inventario Estructural de Elementos Pedagógicos:**
   - *Tablas:* Identificación explícita de filas, columnas, celdas de encabezado y pares clave-valor (ej. Tabla 2.1: Símbolo ANSI vs Significado).
   - *Diagramas de Flujo:* Detección de nodos de decisión (rombos), procesamiento (rectángulos), terminales (óvalos) y flechas de flujo. El estándar exige que el texto dentro del diagrama quede aislado o marcado como bloque gráfico (`<!-- image -->`), sin derramarse sobre la prosa contigua.
   - *Pseudocódigo y Algoritmos:* Declaración formal de sangría anidada (niveles 1, 2, 3), palabras reservadas en mayúsculas/minúsculas y separación de comentarios (`//`).
   - *Encabezados:* Jerarquía documental explícita (`Capítulo 2`, `2.1`, `2.1.1`, etc.).
   - *Flujo de Lectura:* Continuidad lógica de los bloques de prosa sin saltos transversales de columna.

---

## 3. ESPECIFICACIÓN DE DIMENSIONES DE CALIDAD

| Dimensión | Criterio de Éxito (Score 3) | Criterio de Falla Crítica (Score 0) |
|---|---|---|
| `TABLE_STRUCTURE` | Tabla Markdown con sintaxis `\| col \| col \|` alineada, correspondencia $1:1$ celda-fila. | Flujo lineal continuo de texto/números concatenados donde se destruye la relación fila-columna. |
| `FLOWCHART_DIAGRAM_ISOLATION` | Diagrama aislado como bloque visual o imagen; texto algorítmico lineal no contaminado por glifos. | Texto horizontal escaneado atravesando cajas del diagrama, mezclando sentencias paralelas. |
| `CODE_STRUCTURE` | Bloque con triple comilla (\`\`\`), preservando saltos de línea y niveles de sangría. | Texto colapsado en un único párrafo continuo sin indentación. |
| `HEADING_STRUCTURE` | Títulos marcados como `#`, `##` o `###` acordes a la jerarquía tipográfica original. | Títulos confundidos con texto de párrafo ordinario o partidos por saltos de línea arbitrarios. |
| `READING_ORDER` | Párrafos siguen el orden de lectura natural de izquierda a derecha y arriba hacia abajo. | Textos de columnas paralelas leídos alternadamente línea por línea (entrecruzamiento lateral). |

---

## 4. MATRIZ DE REGLAS DE ADJUDICACIÓN

1. **Regla de No-Penalización por Ausencia (`NOT_APPLICABLE`):**
   Si una página carece de tablas, la dimensión `TABLE_STRUCTURE` se marca como `N/A`. Su ausencia **no suma ni resta puntos**, y se excluye del divisor del promedio de calidad.
2. **Regla de Independencia de Herramientas:**
   Si tanto PyMuPDF como Docling cometen errores estructurales graves en una página, ambas herramientas reciben `score = 0` en esa dimensión. Docling no recibe ventaja automática por generar Markdown si el Markdown es alucinatorio o corrompido.
3. **Inmutabilidad del Gold Standard:**
   Los inventarios de elementos estructurales y dimensiones aplicables $\mathcal{D}_{	ext{app}}(p)$ quedan fijados y congelados antes de que comience el proceso de evaluación de los resultados.
