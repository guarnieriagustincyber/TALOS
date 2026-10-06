# RÚBRICA FORMAL DE ADJUDICACIÓN CIEGA DE RETRIEVAL (V2)

## Escalas Categóricas (0, 1, 2)

### 1. Relevancia Semántica (RELEVANCE)
- **0 (No Relevante):** El fragmento no guarda relación con la consulta o trata un tema completamente ajeno.
- **1 (Parcialmente Relevante):** El fragmento menciona términos o conceptos de la consulta pero de forma tangencial o diluida.
- **2 (Altamente Relevante):** El fragmento aborda directamente el núcleo conceptual o técnico solicitado.

### 2. Suficiencia Informativa (SUFFICIENCY)
- **0 (Insuficiente):** No permite responder la consulta; obligaría a recurrir a conocimiento externo o alucinar.
- **1 (Suficiente con Inferencia):** Contiene la mayor parte de la respuesta pero requiere completar detalles lógicos obvios.
- **2 (Totalmente Autosuficiente):** Proporciona evidencia completa y autónoma para formular una respuesta impecable.

### 3. Potencial de Fundamentación (GROUNDING POTENTIAL)
- **0 (Riesgo Crítico de Alucinación):** Afirmaciones clave quedarían sin sustento en el contexto.
- **1 (Fundamentación Parcial):** Parte de la respuesta se apoya en el fragmento pero existen lagunas de citas.
- **2 (Estrictamente Fundamentado):** Cada afirmación de la respuesta puede citarse textualmente del fragmento.

### 4. Calidad del Contexto (CONTEXT QUALITY)
- **0 (Mutilado / Incoherente):** Oraciones cortadas a la mitad, tablas destruidas o sintaxis rota.
- **1 (Aceptable):** Texto legible pero con encabezados vagos o delimitación subóptima.
- **2 (Estructura Limpia):** Sintaxis íntegra, encabezado descriptivo y límites semánticos naturales.
