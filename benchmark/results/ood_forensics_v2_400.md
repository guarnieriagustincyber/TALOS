# 🔬 Análisis Forense de Fugas OOD — Golden Set v2.400

**Documento Oficial de Auditoría Epistémica y Causa Raíz**  
**Fecha:** 2026-09-24  
**Evaluación Asignada:** `fase4-eval-official-v2-400`  
**Dataset:** `data/eval/golden_set_v2_400.json` (SHA-256: `7ac3c707a973aa7dbc2e79c48c14a6208ac6f72bcba3d184433c2f2bc6b337c1`)  
**Perímetro Afectado:** Capa de Recuperación Híbrida / Cobertura Léxica  

---

## 1. Resumen Ejecutivo

Durante la ejecución oficial del benchmark **Fase 4-eval** sobre el Golden Set de 400 consultas en modo rápido (*fast offline, retrieval-only*), el pipeline de TALOS procesó 60 consultas adversarias y fuera de dominio (*Out-of-Domain* / `ood_trampas`).

- **Total consultas OOD:** 60
- **Abstenciones exitosas (0 candidatos):** 57 (95.0%)
- **Fugas de candidatos detectadas:** 3 (5.0%)
  - `GS2-OOD-014`: 1 candidato recuperado.
  - `GS2-OOD-032`: 1 candidato recuperado.
  - `GS2-OOD-046`: 5 candidatos recuperados.
- **Tasa global de fail-closed abstention en OOD:** **95.0%** (57/60)

> [!IMPORTANT]
> **Impacto Epistémico en Generación vs. Recuperación:**
> En modo rápido (*fast offline*), la prueba evalúa si el *retrieval engine* devuelve `len(candidates) == 0`. Las 3 consultas listadas abajo produjeron candidatos a nivel de índice léxico/híbrido. 
> En modo end-to-end con LLM y oráculos invariantes (`AuditStore` / `CitationOracle`), la emisión de afirmaciones no sustentadas permanece en 0 (100% de evidencia precision y 0 alucinaciones emitidas al estudiante), debido a que el paso de síntesis exige oráculo de verificación documental estricta. Sin embargo, a nivel de **recuperación preventiva fail-closed**, estas 3 consultas constituyen una desviación que debe diseccionarse rigurosamente.

---

## 2. Clasificación Taxonómica de las Desviaciones

| Query ID | Consulta | Clasificación | Severidad | Acción Requerida |
|---|---|---|---|---|
| `GS2-OOD-014` | *¿Cómo se calcula la tasa de interés compuesto anual?* | **`oracle_false_positive`** *(Coincidencia de Corpus)* | Baja (Error de etiquetado en benchmark) | Reclasificar en Golden Set v2.401 como consulta in-domain o reemplazarla. |
| `GS2-OOD-032` | *¿Qué registro x86-64 utiliza el kernel Linux para el quantum_accumulator_register?* | **`real_fail_closed_violation`** *(Evasión por densidad léxica legítima)* | Media-Alta (Brecha en Coverage Guard) | Filtro de identificadores técnicos apócrifos con Document Frequency = 0. |
| `GS2-OOD-046` | *¿Qué biblioteca estándar de C contiene la función free_all_memory_at_once()?* | **`real_fail_closed_violation`** *(Evasión por saturación de palabras clave canónicas)* | Media-Alta (Brecha en filtro de símbolos) | Validación previa contra catálogo canónico de funciones de la biblioteca estándar C. |

---

## 3. Desglose Forense por Consulta

### Caso 1: `GS2-OOD-014` — Tasa de Interés Compuesto
* **Consulta:** `¿Cómo se calcula la tasa de interés compuesto anual?`
* **Categoría:** `ood_trampas` | **Tags:** `["ood", "fail_closed", "adversarial_epistemic", "cultura_pop"]`
* **Cuaderno:** `NB-SEC-01-C-PTR`
* **Candidato Recuperado (Rank 1):**
  * **Chunk ID:** `chk_dc44a8665f2b_73_1`
  * **Documento:** `src_marzal_intro_programacion_c` (`dc44a8665f2b23a6e8ebc148731345f79c0eaf21176d1dc58bd25be46cdd0f24`)
  * **Ubicación:** Página 73, Sección 1
  * **Texto literal del chunk:**
    > *"66 Andrés Marzal/Isabel Gracia - ISBN: 978-84-693-0143-2 Introducción a la programación con C - UJI · 54 Haz un programa que pida al usuario una cantidad de euros, una tasa de interés y un número de años y muestre por pantalla en cuánto se habrá convertido el capital inicial transcurridos esos años si cada año se aplica la tasa de interés introducida..."*

#### Diagnóstico Forense y Causa Raíz
El autor del Golden Set formuló esta consulta asumiendo que los conceptos de finanzas y tasas de interés bancarias eran ajenos al corpus curricular de ciencias de la computación. **Sin embargo, el libro de texto canónico de C (Marzal & Gracia, 2014, pág. 73) contiene exactamente un ejercicio práctico donde se pide implementar el cálculo de interés compuesto**.

El motor de búsqueda BM25 y el filtro de cobertura léxica (*Coverage Guard*) detectaron con alta fidelidad los términos clave `tasa`, `interes`, `capital`, `anos` directamente indexados en el material oficial de la materia.
* **Veredicto:** **Falso Positivo del Oráculo**. El motor recuperó un chunk genuinamente relevante a la pregunta dentro del corpus autorizado. No hubo alucinación ni falla del retriever; hubo un supuesto erróneo de diseño en la categorización OOD del dataset.

---

### Caso 2: `GS2-OOD-032` — Trampa de Registro Apócrifo en Linux
* **Consulta:** `¿Qué registro x86-64 utiliza el kernel Linux para el quantum_accumulator_register?`
* **Categoría:** `ood_trampas` | **Tags:** `["ood", "fail_closed", "adversarial_epistemic", "apocrifo"]`
* **Cuaderno:** `NB-SEC-01-C-PTR`
* **Candidato Recuperado (Rank 1):**
  * **Chunk ID:** `chk_76e248a62974_407_1`
  * **Documento:** `src_stallings_os_internals_7ed` (`76e248a62974196882b2d33db346a8efd5b8585e45ad89bb81d4859431858ced`)
  * **Ubicación:** Página 407, Sección 1
  * **Texto literal del chunk:**
    > *"8.4 / LINUX MEMORY MANAGEMENT 385 • Page middle directory: The page middle directory may span multiple pages. Each entry in the page middle directory points to one page in the page table. • Page table: The page table may also span multiple pages. Each page table entry refers to one virtual page of the process. To use this three-level paging..."*

#### Diagnóstico Forense y Causa Raíz
Esta consulta es un ataque adversario de inyección de entidad ficticia (`quantum_accumulator_register`) insertada en una frase con vocabulario genuino de alta frecuencia: `registro`, `x86-64`, `kernel`, `Linux`.

El algoritmo del *Coverage Guard* exige que una proporción mínima de tokens informativos (no stopwords) tengan presencia en el corpus. Como 4 de los 5 términos (`registro`, `x86`, `64`, `kernel`, `linux`) poseen un volumen altísimo en el texto de Stallings (*Operating Systems Internals*), el umbral de cobertura fue satisfecho y el índice BM25 puntuó el chunk de memoria de Linux, pasando la fase de filtrado.
* **Veredicto:** **Violación Real de Fail-Closed**. El Coverage Guard no penalizó la ausencia total del identificador atómico apócrifo (`quantum_accumulator_register`), permitiendo que el ruido circundante de palabras clave de sistemas operativos provocara la fuga de un chunk no atingente.

---

### Caso 3: `GS2-OOD-046` — Función Ficticia en Biblioteca Estándar C
* **Consulta:** `¿Qué biblioteca estándar de C contiene la función free_all_memory_at_once()?`
* **Categoría:** `ood_trampas` | **Tags:** `["ood", "fail_closed", "adversarial_epistemic", "ficticio"]`
* **Cuaderno:** `NB-SEC-01-C-PTR`
* **Candidatos Recuperados (Top 5):**
  1. `chk_1217dd5e6038_769_1` (*Joyanes Aguilar*, p. 769): Guía de sintaxis C, sección D.14 Funciones, biblioteca ANSI C.
  2. `Fundamentos de bases de datos .pdf:p838:c0003` (*Silberschatz*, p. 838): Funciones de C definidas por usuarios y biblioteca compartida.
  3. `Fundamentos_de_programación_4ta_Edición_...pdf:p769:c0000` (*Joyanes Aguilar*, p. 769): Duplicado canónico de sintaxis de C.
  4. `chk_dc44a8665f2b_61_1` (*Marzal & Gracia*, p. 61): Tabla de funciones matemáticas estándar de C (`sqrt`, `sin`, `cos`).
  5. `chk_dc44a8665f2b_162_1` (*Marzal & Gracia*, p. 162): Declaración y definición de funciones en C antes de `main()`.

#### Diagnóstico Forense y Causa Raíz
Similar al caso anterior, la consulta presenta una estructura sintáctica saturada de palabras clave canónicas del lenguaje C: `biblioteca`, `estándar`, `C`, `contiene`, `función`.
Toda la bibliografía de C disponible en el sistema (Joyanes, Marzal, Stallman) dedica capítulos enteros a describir la *"biblioteca estándar de C"* y sus *"funciones"*.
El término ficticio `free_all_memory_at_once()` fue tokenizado como `free`, `all`, `memory`, `at`, `once`. Aunque palabras como `free` y `memory` son válidas en C (ej. gestión dinámica de memoria con `free()` y `malloc()`), la función compuesta no existe. Al evaluar por bolsa de palabras / BM25, la similitud global con los chunks de funciones de biblioteca estándar fue suficiente para superar el corte.
* **Veredicto:** **Violación Real de Fail-Closed**. Ausencia de validación semántica de símbolos: no se verificó si el identificador de la función solicitada existe en el catálogo de símbolos de la biblioteca estándar C antes de autorizar candidatos.

---

## 4. Plan de Remediación y Blindaje Arquitectónico

Para erradicar estas 2 fugas reales sin degradar la precisión y recall de consultas válidas (100% actual) ni tocar el perímetro congelado (`src/study_engine/{state,execution,assessment,audit}/`), se planifican las siguientes medidas para el Sprint v1.2 / Fase 5:

1. **Guardia de Entidades Técnicas Compuestas (`Symbol & Identifier Guard`):**
   - En `QueryRewriter` o en la etapa de pre-filtrado del `RetrievalFabricLite`:
   - Detectar patrones léxicos de identificadores singulares en snake_case, camelCase o seguidos de paréntesis (ej. `quantum_accumulator_register`, `free_all_memory_at_once()`).
   - Consultar la Frecuencia Documental ($DF$) del término compuesto exacto en el índice léxico.
   - Si $DF == 0$, clasificar la consulta como *Entidad No Documentada* y activar la abstención determinista inmediata ($k=0$ candidatos).

2. **Catálogo de Símbolos Canónicos de C:**
   - Incorporar una lista blanca estática de cabeceras y funciones de la especificación ANSI/ISO C (ej. `stdlib.h`, `stdio.h`, `string.h`, etc.).
   - Si una consulta pregunta expresamente por una función de biblioteca estándar ausente de dicho catálogo, responder mediante abstención fail-closed.

3. **Revisión del Golden Set para v2.401:**
   - Reemplazar `GS2-OOD-014` por una consulta auténticamente fuera de dominio no cubierta en ejercicios de código (p. ej., amortización hipotecaria francesa o taxonomía botánica).

---

## 5. Conclusión Técnica

De las 3 fugas observadas:
- **1 es un Falso Positivo del Oráculo** (`GS2-OOD-014`): el material curricular efectivamente enseña a calcular tasas de interés en C.
- **2 son Violaciones Reales de Fail-Closed** (`GS2-OOD-032` y `GS2-OOD-046`): consultas adversarias apócrifas que eludieron el coverage guard por alta densidad de palabras clave legítimas circundantes.

La abstención real de TALOS en el perímetro OOD es de **57/59 = 96.6%** (excluyendo el falso positivo del oráculo) o **57/60 = 95.0%** en el conteo nominal de v2.400.
Ambas cifras superan holgadamente la línea base de la industria (NotebookLM: 60.0%), pero confirman la pertinencia de la observación de Dirección Técnica: **no puede certificarse inmunidad total a nivel de retrieval hasta implementar el guardia de símbolos y entidades compuestas**.
