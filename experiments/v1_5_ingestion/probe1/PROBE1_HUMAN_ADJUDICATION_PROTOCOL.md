# TALOS V1.5 — INGESTION INTELLIGENCE LAB
## PROBE-1: PROTOCOLO DE ADJUDICACIÓN HUMANA CIEGA Y EVALUACIÓN ESTRUCTURAL (C06)

**Versión:** 1.0.1-canonical  
**Fecha:** 2026-10-05  
**Fase:** Ingestion Intelligence Lab (v2.0)  
**Experimento:** `PROBE-1: Adaptive Structural Routing`  
**Estado:** `FROZEN_PROTOCOL`  
**Autoridad:** Directiva Canónica v1.0.1 (Control C06)  
**Aislamiento:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE`  

---

## 1. UNIDAD DE EVALUACIÓN FORMAL

La unidad atómica de evaluación se define formalmente como la tupla:
$$\mathcal{U} = (p, d, t)$$
donde:
* $p \in \mathcal{P}$ es la página física del dataset ($|\mathcal{P}| = 38$ páginas).
* $d \in \mathcal{D}_{	ext{app}}(p)$ es una dimensión estructural objetivamente aplicable a la página.
* $t \in \{	ext{TOOL\_ALPHA}, 	ext{TOOL\_BETA}, 	ext{TOOL\_GAMMA}\}$ es el extractor bajo evaluación ciega.

Si una dimensión no está presente en la página ($d 
otin \mathcal{D}_{	ext{app}}(p)$), la celda se marca automáticamente como **`NOT_APPLICABLE (N/A)`** y no requiere juicio subjetivo.

---

## 2. PROTOCOLO DE CEGAMIENTO CRIPTOGRÁFICO

Para erradicar sesgos de confirmación hacia Docling o PyMuPDF:
1. **Generación de Clave de Enmascaramiento:** Se genera una clave secreta aleatoria de 256 bits (`BLINDING_KEY_PROBE1`), cuyo hash SHA-256 se publica previamente en el manifest.
2. **Asignación Aleatoria por Página:** Para cada página $p$, el orden de las tres herramientas se permuta de forma pseudoaleatoria dependiente de la clave:
   $$\pi_p : \{	ext{pypdf}, 	ext{pymupdf}, 	ext{docling}\} 	o \{	ext{TOOL\_ALPHA}, 	ext{TOOL\_BETA}, 	ext{TOOL\_GAMMA}\}$$
3. **Anonimización del Texto:** Se eliminan cabeceras, firmas de software y metadatos que delaten el motor extractor (ej. menciones a `fitz`, `docling-core` o `pypdf-reader`).
4. **Descegado Condicional:** La tabla de mapeo se mantiene inaccesible hasta que el evaluador haya completado el 100% de las celdas y se haya sellado el archivo de adjudicación `HUMAN_ADJUDICATION_BLIND_RAW.json`.

---

## 3. RÚBRICA ESTANDARIZADA DE ADJUDICACIÓN

| Score | Etiqueta Canónica | Criterio Operacional |
|---|---|---|
| **3** | `PERFECT_OR_NEGLIGIBLE_DEFECT` | Estructura completamente preservada. Las relaciones espaciales, tablas o código son directamente consumibles por un LLM/estudiante sin ambigüedad. |
| **2** | `USABLE_MINOR_DEFECTS` | Estructura semánticamente recuperada con defectos menores (ej. espacios adicionales, falta de formato negrita en encabezados, pequeñas variaciones de espaciado que no alteran el significado). |
| **1** | `PARTIAL_HEAVY_REPAIR` | Información recuperada de forma incompleta o desordenada; requiere post-procesamiento heurístico intensivo para ser utilizable. |
| **0** | `DESTROYED_OR_CORRUPT` | Pérdida total de la estructura. Texto linealizado atravesando tablas o diagramas, números de celdas concatenados o código colapsado sin jerarquía. |
| **N/A** | `NOT_APPLICABLE` | Dimensión ausente en la página física (no penaliza ni bonifica). |

---

## 4. PERFIL DEL EVALUADOR Y DECLARACIÓN DE LIMITACIONES

* **Evaluador Especialista:** Especialista humano independiente en arquitectura de sistemas e ingeniería de software pedagógica.
* **Declaración Formal de Limitación:**
  > [!WARNING]
  > **Limitación Metodológica Muestral:** La adjudicación de PROBE-1 se realiza bajo modalidad $N=1$ especialista humano independiente. Por tanto, no se reportarán coeficientes de concordancia inter-evaluador (Kappa de Cohen o Alpha de Krippendorff). Esta limitación queda expresamente preregistrada y no podrá ser ocultada en las conclusiones del experimento.
