# 09 — ESPECIFICACIÓN EXPERIMENTAL: ESCALA DE 13+ FUENTES (V1.2 EXPERIMENTAL)

> **Estado:** Documento de Especificación Experimental Congelada  
> **Ámbito:** Cuaderno Fase 0 (13 fuentes PDF reales, ~5.850 páginas, ~8.000-9.000 chunks)  
> **Objetivo:** Maximizar *Supported Answer Coverage* (SAC) sin saturación por redundancia ni sesgo de autoridad artificial.

---

## 1. PRINCIPIOS Y CORRECCIONES ARQUITECTÓNICAS

Esta especificación formaliza las cuatro correcciones críticas que previenen métricas artificiales y autoridad indebida:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LAS 4 CORRECCIONES ARQUITECTÓNICAS                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. HEURÍSTICA GREEDY, NO ÓPTIMO MATEMÁTICO:                                │
│    Se define como "Greedy Marginal Evidence Selection". Se reconoce como    │
│    aproximación heurística y se valida empíricamente.                       │
│                                                                             │
│ 2. LA AUTORIDAD DESEMPATA, NUNCA RESCATA IRRELEVANCIA:                      │
│    El bonus de autoridad de fuente por tópico solo aplica si la relevancia  │
│    supera un piso estricto (τ_min). Una fuente oficial mediocre jamás       │
│    desplaza a una fuente secundaria altamente relevante.                    │
│                                                                             │
│ 3. REDUNDANCIA MULTIDIMENSIONAL SOFT (NO JACCARD CIEGO):                    │
│    El solapamiento léxico no penaliza si los fragmentos cumplen roles       │
│    informacionales distintos (ej. definición teórica vs caso base/código).   │
│                                                                             │
│ 4. AFFORDANCE GRADUAL (EVITAR FALSO "IMPOSIBLE"):                           │
│    NO_LEXICAL_SIGNAL → LOW_CORPUS_AFFORDANCE → MISSING_CONFIRMED.           │
│    Permite detectar sinónimos e hiperónimos ("Suricata" → "IDS").           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. FORMULACIÓN FORMAL DE COMPONENTES

### Componente 1: Greedy Marginal Evidence Selection (P1 & P5)

Dado un conjunto de candidatos recuperados $\mathcal{C}$ y una lista de sub-queries priorizadas $\mathcal{Q}$:

Para cada slot disponible en el presupuesto de contexto (hasta $K \le 5$ chunks o presupuesto en caracteres):

$$\text{Score}(C) = \text{Relevance}(C) + \alpha \cdot \text{CoverageGain}(C, \mathcal{S}) + \beta \cdot \text{TopicAuthorityBonus}(C) - \gamma \cdot \text{RedundancyPenalty}(C, \mathcal{S}) - \delta \cdot \text{QualityPenalty}(C)$$

Donde:
1. **$\text{CoverageGain}(C, \mathcal{S})$:**
   $$\text{CoverageGain}(C, \mathcal{S}) = \begin{cases}
   1.0 & \text{si el sub-tema de } C \text{ no tiene chunks en } \mathcal{S} \\
   0.2 & \text{si el sub-tema de } C \text{ tiene exactamente 1 chunk en } \mathcal{S} \\
   0.0 & \text{si el sub-tema de } C \text{ ya tiene } \ge 2 \text{ chunks en } \mathcal{S}
   \end{cases}$$
2. **$\text{TopicAuthorityBonus}(C)$ (Compuerta Estricta de Relevancia):**
   $$\text{TopicAuthorityBonus}(C) = \begin{cases}
   0.15 & \text{si } C \in \text{AuthoritativeSources}(\text{Topic}) \quad \mathbf{Y} \quad \text{Relevance}(C) \ge 0.70 \\
   0.00 & \text{si } \text{Relevance}(C) < 0.70 \quad (\text{La autoridad NO rescata irrelevancia})
   \end{cases}$$
3. **$\text{RedundancyPenalty}(C, \mathcal{S})$ (Multidimensional Soft):**
   Para cada $S \in \mathcal{S}$ que pertenezca al **mismo sub-tema**:
   $$\text{Overlap}(C, S) = \text{SemanticSim}(C, S) \times \mathbb{I}(\text{Role}(C) == \text{Role}(S)) \times \text{LexicalJaccard}(C, S)$$
   $$\text{RedundancyPenalty}(C, \mathcal{S}) = \max_{S \in \mathcal{S}} \text{Overlap}(C, S)$$
   *(Si $C$ es código/implementación y $S$ es definición formal, $\mathbb{I}(\text{Role}(C) == \text{Role}(S)) = 0$, la penalización es nula).*
4. **$\text{QualityPenalty}(C)$:** $0.20$ si el chunk tiene flag `LOW_OCR` o artefactos de escaneo.

---

### Componente 2: Topic-Scoped Authority Mapping (P2)

En la matriz curricular (`data/curriculum/alignment`):
Cada nodo curricular (`node_id`) declara explícitamente el rol específico de sus fuentes vinculadas:

```yaml
node_id: "SEC-01-C-PTR"
sources_alignment:
  - source_id: "src-joyanes-fundamentos"
    topic_role: "PRIMARY_CONCEPTUAL"      # Canónico para fundamentos y tipos
  - source_id: "src-spraul-problem-solving"
    topic_role: "PRIMARY_MENTAL_MODEL"    # Canónico para visualización en memoria
  - source_id: "src-clean-code"
    topic_role: "SUPPLEMENTARY_STYLE"     # Secundario / Guía de estilo
```

**Invariante:** Ninguna fuente es globalmente canónica para todo el cuaderno; la autoridad está delimitada al nodo curricular activo.

---

### Componente 3: Adaptive Retry con Exclusión de Fuentes y Affordance Gradual (P3)

Si tras la primera pasada de recuperación un sub-tema $q$ resulta `PARTIAL`:

```
                           SUB-TEMA PARTIAL
                                  ↓
                        AFFORDANCE GRADIENTE
   1. Lexical Check: ¿Existen términos clave en el vocabulario del cuaderno?
         ├── SÍ  → CONTINUAR A RETRY
         └── NO  → [NO_LEXICAL_SIGNAL]
                   ↓
   2. Dense Check: ¿Existe embedding con similitud >= 0.60 en el cuaderno?
         ├── SÍ  → CONTINUAR A RETRY (Posible sinónimo o concepto afín)
         └── NO  → [LOW_CORPUS_AFFORDANCE]
                   ↓
                   ABORTAR RETRY (Gasto: 0ms)
                   Declarar MISSING_CONFIRMED con transparencia pedagógica
```

Si el sub-tema tiene soporte de affordance:
- Se ejecuta la búsqueda dirigida excluyendo las fuentes que ya aportaron chunks para ese sub-tema:
  $$\text{TargetedQuery}(q) \implies \text{retrieve}(q, \text{exclude\_sources}=\text{SourcesAlreadySampled}(q), \text{top\_k}=2)$$
- Esto fuerza al retriever a buscar en las restantes 12 fuentes del cuaderno en lugar de traer los ranks secundarios del mismo libro que saturó la búsqueda inicial.

---

### Componente 4: Ingesta Heterogénea y Versionado Criptográfico (P4)

1. **Auditoría de Capa de Texto en Ingesta:**
   - Para cada página PDF:
     - Si `caracteres_legibles / total_caracteres < 0.75` o `len(texto) < 40`:
       - Se marca el chunk con `metadata["low_quality_ocr"] = True`.
2. **Inmutabilidad y Versionado de Documentos Vivos:**
   - Para documentos actualizables (`GUIA_2025.pdf`):
     - Se genera `source_id = "src-guia-2025-" + sha256(pdf_bytes)[:8]`.
     - El cuaderno apunta al `active_source_id`.
     - Las sesiones y auditorías S4.4 históricas mantienen su cita exacta e inmutable a la versión previa sin colisiones.

---

## 3. EL TABLERO DE MÉTRICAS EXPERIMENTALES

Reemplazamos el conteo plano de fuentes por la métrica epistemológica central:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 MÉTRICA REINA: SUPPORTED ANSWER COVERAGE (SAC)               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                        Σ Facetas Respaldadas [E#]                           │
│             SAC = ────────────────────────────────────                      │
│                           Total Facetas de la Query                         │
│                                                                             │
│ Ejemplo: Consulta con 4 facetas (Concepto, Mecanismo, Ejemplo, Seguridad)   │
│ - Si 3 facetas tienen evidencia DIRECT/CONTEXTUAL verificada: SAC = 75%     │
│ - Si el detalle de seguridad no está en los libros: reportado como MISSING  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tabla de Validación por Etapa:

| Etapa | Intervención | Métrica de Control | Umbral Esperado |
|---|---|---|---|
| **E0** | Ingesta 13 fuentes | Chunks totales indexados | ~7.000 - 9.000 chunks |
| **E1** | P4 (Calidad/Versionado) | `low_quality_ocr_rate` detectado | Reporte verificado en telemetría |
| **E2** | P2 (Topic Authority) | `topic_authority_precision` | $\ge 80\%$ chunks provienen de la fuente líder del tópico |
| **E3** | P1/P5 (Marginal Selection) | `inter_book_redundancy` | $< 5\%$ duplicados conceptuales |
| **E4** | P3 (Retry con Exclusión) | `dead_end_retry_rate` | $< 10\%$ reintentos estériles |
| **FINAL** | Pipeline Completo V1.2 | **Supported Answer Coverage (SAC)** | **$\ge 85\%$ en preguntas curriculares** |

---

## 4. SECUENCIA EXPERIMENTAL RECOMENDADA

```text
[13 Fuentes Reales Cargadas]
            ↓
     MEDICIÓN BASELINE (SAC, redundancia, autoridad)
            ↓
  PASO 1: P4 (Calidad de Ingesta y Versionado de Guía 2025)
            ↓
          Medir
            ↓
  PASO 2: P2 (Topic-Scoped Authority en Curriculum Registry)
            ↓
          Medir
            ↓
  PASO 3: P1/P5 (Greedy Marginal Evidence Selection en EvidenceSelector)
            ↓
          Medir
            ↓
  PASO 4: P3 (Affordance Gradiente + Retry con Exclusión de Fuentes)
            ↓
          Medir
            ↓
     RED TEAM FORENSE (Pruebas adversariales con 13 libros)
            ↓
     CERTIFICACIÓN E2E (1.763 tests verdes intactos)
```

---

## 5. LO QUE KASIU ES FRENTE A NOTEBOOKLM

> **NotebookLM:**  
> *"Acá tenés todo este corpus; hacé preguntas y te busco fragmentos afines."*
>
> **KASIU:**  
> *"Acá tenés todo el corpus. Sé exactamente qué parte es pertinente para tu objetivo curricular actual, qué libro tiene la máxima autoridad sobre cada concepto, qué fragmentos son redundantes entre autores, qué evidencias se complementan y con qué certeza afirmo lo que sé y declaro con transparencia lo que no está documentado."*
