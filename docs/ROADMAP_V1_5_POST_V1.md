# TALOS — Hoja de Ruta V1.5 y Post-V1 (Preservación de Backlog de Investigación y Plataforma)

**Documento Canónico de Preservación y Gobernanza Arquitectónica**  
**Proyecto:** TALOS (Tutor Adaptativo de Lógica y Operaciones de Seguridad)  
**Fecha de Publicación:** 2026-10-04  
**Subdominio:** Gobernanza de Arquitectura / Roadmap / Post-V1  
**Estado:** CANÓNICO / NORMATIVO / DOCUMENTAL Y DE PRESERVACIÓN  
**Dependencias Metodológicas:** `CP120_STATUS = CLOSED`, `CP121_STATUS = CLOSED`, `CP122_FINAL = PASS`  
**Decisión Arquitectónica Formal:** `ARCHITECTURAL_DECISION = DEFERRED_POST_V1`  
**Integridad de Producción:** `PRODUCTION_STATUS = UNCHANGED` | `DATABASE_CHANGES = 0`  

**Baseline/release conservado:** `V1` (sin nueva decisión de release)

**Documento metodológico V1.5:** [ROADMAP_V1_5_MASTER.md](./ROADMAP_V1_5_MASTER.md)

**Mapa operativo vigente:** [PLAN_MAESTRO_CIERRE_TALOS.md](./PLAN_MAESTRO_CIERRE_TALOS.md)

---

## 0. Declaración Fundamental de Frontera

> [!NOTE]
> ### Vinculación con la Hoja de Ruta Maestra V1.5
> Para la planificación secuencial, matriz de experimentos y dependencias, y protocolo de promoción técnica de V1.5 (Fases 1 a 4: Evidence Retrieval → Pedagogía → Student Evaluation → Visual Explanations), consultar el documento maestro canónico:
> **[docs/ROADMAP_V1_5_MASTER.md](./ROADMAP_V1_5_MASTER.md)**.
> El estado operativo inmediato es `P0=COMPLETE`, `P1=READY/NOT_STARTED`,
> `P2/P3=DEFERRED`; consultar el [mapa maestro operativo](./PLAN_MAESTRO_CIERRE_TALOS.md).
> Este documento y el roadmap experimental preservan arquitectura e historia:
> ninguno sustituye la precedencia operativa vigente.
> 
> El presente documento (`ROADMAP_V1_5_POST_V1.md`) preserva el inventario histórico detallado de investigación, componentes desacoplados y backlog de arquitectura originado en los checkpoints CP114–CP122 y CP127.

> **V1.5 es una hoja de ruta activa de trabajo posterior a V1, no una obligación
> de incorporar todas las líneas listadas ni una autorización general de
> implementación. Su secuencia operativa vigente está en el mapa maestro.**

Este documento constituye el punto de referencia para preservar de manera durable todo el conocimiento, hallazgos empíricos, componentes desconectados y líneas de investigación que han sido deliberadamente diferidas fuera del camino crítico de TALOS V1.

### Principio de Inmutabilidad Operacional
1. **Preservación Estricta:** Esta directiva es exclusivamente documental y de preservación.
2. **Cero Modificación en Runtime:** No se implementan funcionalidades V1.5, no se alteran contratos V1, no se instalan dependencias y no se modifican routers ni pipelines.
3. **Cero Modificación en Bases de Datos:** `knowledge_store.db`, `vector_store.db` y `student_state.db` permanecen estrictamente inmutables (`DATABASE_CHANGES = 0`).
4. **Cero Nuevos Experimentos:** No se reabren experimentos (CP120, CP121, CP122), no se generan nuevos datasets ni heurísticas, y no se autorizan migraciones de corpus o embeddings.
5. **Frontera Nítida:**
   ```text
   V1 = BASELINE / CONTROL CERRADO
   V1.5 = ACTIVE ROADMAP; el estado de las tareas se rige por el mapa operativo
   ```

---

## 1. Estado de Partida y Verificación Criptográfica

El estado del sistema previo a la formalización de este documento se certifica a partir de los dictámenes metodológicos y la verificación byte-a-byte de los almacenes de datos:

```text
CP120_STATUS = CLOSED
CP121_STATUS = CLOSED
CP122 = PASS
CP122_CORR = PASS
CP122_FINAL = PASS

ARCHITECTURAL_DECISION = DEFERRED_POST_V1

PRODUCTION_STATUS = UNCHANGED
DATABASE_CHANGES = 0
```

### Hashes Criptográficos Canónicos de Producción (SHA-256)
- `data/web_state/knowledge_store.db`: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (INTACTA)
- `data/web_state/vector_store.db`:
  - `HISTORICAL_PRE_INCIDENT_HASH`: `013a2462e6de6ca7cf13443338e44b7795dce4b2f7f6117827bd2ccadd0c568f` (CP114–CP122)
  - `V1_CURRENT_CANONICAL_HASH`: `d6d9f8c8eb6e5188e8e600a73cc05bd001d2e389061815d7d0df33f447a9dde4` (Post-CP125/CP126/CP127, 100% vector integrity verified)
- `data/web_state/student_state.db`: `f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` (INTACTA)

Cualquier alteración no autorizada en estos hashes sin una directiva formal de release invalidaría la certificación de integridad de TALOS V1.

---

## 2. Registro Canónico de Líneas Post-V1

A continuación se registran exhaustivamente las líneas de trabajo preservadas para Post-V1, manteniendo la disciplina epistémica exigida por el proyecto.

```text
ID: V15-CONTEXTPACK

STATUS: DEFERRED_POST_V1
CURRENT_RESULT: RESEARCH_HYPOTHESIS
CP120_RESULT: INCONCLUSIVE
CP121_CONTEXT_PACK_EVALUATION: NOT_EVALUATED_BY_CP121
INTEGRATION_AUTHORIZED: FALSE
```

### Síntesis Metodológica y Evidencia Preservada
En CP120 se evaluó la técnica de ContextPack (expansión contextual L0 de hojas a páginas/secciones completas) para enriquecer el contexto provisto al LLM. Los hallazgos empíricos concluyeron:
- En consultas atómicas o focalizadas con alta precisión de recuperación (ej. CASE-01), la expansión aportó los elementos faltantes para fundamentar la respuesta.
- En consultas donde el retrieval inicial recuperó fragmentos parciales o ruidosos, la expansión inyectó tokens irrelevantes (`DISTRACTING`), incrementando la probabilidad de dispersión atencional y consumiendo innecesariamente presupuesto de contexto C3.
- En CP121 no se evaluó ContextPack, sino la viabilidad de un Sufficiency Gate previo.

**Formulación Normativa Obligatoria:**  
Queda explícitamente prohibido afirmar que *"ContextPack funciona"*, *"ContextPack no funciona"* o *"ContextPack fue refutado"*.  
La formulación técnicamente rigurosa es:
> **Hipótesis de investigación pendiente.**

ContextPack permanece como una hipótesis de diseño arquitectónico que requiere un mecanismo de activación condicional de alta precisión antes de poder ser considerado para producción.

---

```text
ID: V15-SUFFICIENCY-GATE

STATUS: DEFERRED_POST_V1
CP121_H1: EVALUATED
H1_RESULT: NOT_SUPPORTED
PRODUCTION_INTEGRATION: FALSE

NO_GENERAL_IMPOSSIBILITY_CLAIM = TRUE
NO_CONTEXT_PACK_REFUTATION = TRUE
NO_V1_INTEGRATION = TRUE
```

### Síntesis Metodológica y Evidencia Preservada
En CP121 se evaluó formalmente la hipótesis `CP121_H1 = PRE_LLM_INSUFFICIENCY_DETECTION_UTILITY` bajo un protocolo con aislamiento estricto de inferencia, 60 consultas balanceadas en 12 tipologías, conjunto de evaluación bloqueado (`test.lock`, $N=20$) y adjudicación humana independiente post-inferencia:
- Ninguna de las heurísticas pre-LLM superficiales evaluadas (`TOKEN_LENGTH_HEURISTIC`, `LEXICAL_OVERLAP_HEURISTIC`, `CANDIDATE_COMPOSITE_GATE`) demostró utilidad predictiva operativa para discriminar evidencia suficiente de insuficiente utilizando únicamente `(query, retrieved_evidence)`.
- El baseline de longitud fracasó en la generalización fuera de DEV ($Recall = 14.29\%$).
- La heurística compuesta alcanzó un $Recall = 71.43\%$, pero a costa de un $75.00\%$ de falsas expansiones (`FALSE_EXPANSION_RATE`), violando el techo admisible del $50\%$ e introduciendo riesgo severo de degradación contextual.
- El resultado oficial del experimento fue `H1_RESULT = NOT_SUPPORTED`.

**Límites del Resultado:**
- Este dictamen **no significa** que sea teóricamente imposible construir un evaluador de suficiencia pre-LLM.
- Significa que las políticas pre-LLM evaluadas bajo el protocolo CP121 no demostraron suficiente utilidad predictiva para justificar su incorporación a V1.
- No se autoriza la incorporación de ningún Sufficiency Gate en el runtime de V1.

---

```text
ID: V15-DENSE-RETRIEVAL
ID: V15-RERANKER-INTEGRATION
ID: V15-RETRIEVAL-FABRIC-EXPANSION

STATUS: DEFERRED_POST_V1
PRODUCTION_INTEGRATION: FALSE
```

### Síntesis Metodológica y Evidencia Preservada
1. **Dense Retrieval (`V15-DENSE-RETRIEVAL`):** La búsqueda vectorial densa mediante embeddings en tiempo de consulta se encuentra desacoplada en el flujo interactivo de live chat (`/api/chat/query`). La existencia de código histórico o utilidades de búsqueda híbrida en `knowledge_store.py` no autoriza su activación automática. El retrieval léxico determinista SQLite FTS5 (BM25) responde de manera exhaustiva en ~5-8 ms con 0 MB de memoria RAM adicional, satisfaciendo plenamente los requerimientos de V1.
2. **Reranker Neural (`V15-RERANKER-INTEGRATION`):** `LocalONNXReranker` (`models/reranker/model.onnx`, BGE INT8, ~267 MB) y `JinaReranker` están implementados en el repositorio, pero su invocación dentro del pipeline web principal permanece inactiva por diseño. Los rerankers actúan como selectores de ordenamiento, no como compresores de contexto, por lo que no resuelven la suficiencia factual ni el presupuesto C3 por sí solos.
3. **Retrieval Fabric Expansion (`V15-RETRIEVAL-FABRIC-EXPANSION`):** La orquestación completa de `RetrievalFabricLite` con multi-query rewriters, symbol guards dinámicos y fusion layers avanzados queda preservada como plataforma futura. Toda incorporación futura requerirá revalidación formal contra los contratos de latencia, memoria y presupuesto C3 de TALOS.

---

```text
ID: V15-EMBEDDINGS-REALIGNMENT

STATUS: DEFERRED_POST_V1
PRODUCTION_INTEGRATION: FALSE
```

### Síntesis Metodológica y Evidencia Preservada
En la auditoría arqueológica CP104 se identificó un desacoplamiento entre dos capas de representación vectorial:
- La base de datos SQLite `data/web_state/vector_store.db` (1.3 GB) contiene 287,069 vectores de dimensión 1024 calculados históricamente con `Qwen/Qwen3-Embedding-0.6B`.
- El runtime local en disco `models/multilingual-e5-small/onnx/model.onnx` (449 MB) genera vectores de dimensión 384.
- En el entorno virtual de producción (`.venv`), la librería `sentence_transformers` no está instalada, por lo que el runtime ejecuta el fallback seguro hacia el modelo local de 384d. Al detectar la incompatibilidad dimensional ($1024 \neq 384$), la búsqueda vectorial aborta de forma segura (`return []`) y transfiere la carga transparentemente a FTS5 BM25 sin arrojar excepciones.

**Frontera Inmutable:**
- Queda diferido a Post-V1: el realineamiento del vector store, la unificación del contrato de embeddings, la validación dinámica de pooling, los benchmarks comparativos y la eventual regeneración de índices vectoriales.
- En V1: **NO modificar `vector_store.db`**, **NO regenerar embeddings** y **NO ejecutar migraciones**.

---

```text
ID: V15-CORPUS-ENGINEERING

STATUS: DEFERRED_POST_V1
PRODUCTION_CORPUS = UNCHANGED
CANDIDATE_IMPORT = NOT_AUTHORIZED
```

### Síntesis Metodológica y Evidencia Preservada
La serie de investigación CP114 a CP122 en el Corpus Intelligence Lab exploró métodos avanzados de preparación documental:
- Comparación entre extracción heurística básica (PyMuPDF) y extracción estructural con preservación de layout, títulos jerárquicos (headings H1-H4), código fuente y tablas estructuradas (Docling).
- Técnicas de chunking estructural jerárquico, trazabilidad de procedencia documental (provenance L3) y benchmarks formales de cobertura (CP116, CP118).
- Análisis de casos patológicos, límites de fragmentación y empaquetamiento de bundles de corpus (`TALOS_CORPUS_BUNDLE_V1`).

**Frontera Inmutable:**
```text
CP114–CP122 = RESEARCH HISTORY
PRODUCTION_CORPUS = UNCHANGED
CANDIDATE_IMPORT = NOT_AUTHORIZED
```
La investigación de corpus no queda desechada; permanece preservada como antecedente metodológico riguroso, completamente separada del camino crítico de release de V1.

---

```text
ID: V15-S6-SANDBOX
ID: V15-LAB-GRADER

STATUS: DEFERRED_POST_V1
PRODUCTION_INTEGRATION: FALSE
```

### Síntesis Metodológica y Evidencia Preservada
1. **S6 Sandbox (`V15-S6-SANDBOX`):** Entorno de ejecución en servidor de código arbitrario con captura de syscalls y aislamiento en contenedores/cgroups. En TALOS V1, el endpoint `/api/practice/evaluate` retorna determinísticamente el estado fail-closed `PRACTICE_UNAVAILABLE` (HTTP 501). La filosofía de V1 prioriza que el estudiante programe y ejecute en su propio entorno local (VSCode / terminal Linux) y que el sistema audite determinísticamente la evidencia producida, evitando la complejidad y los vectores de ataque de un sandbox multi-tenant en el servidor.
2. **LabGraderBridge (`V15-LAB-GRADER`):** La clase `LabGraderBridge` (`src/study_engine/student/lab_observations.py`) califica flags SHA-256 de 5 desafíos de seguridad (Juice Shop, VAmPI, laboratorios C) directamente hacia BKT. El componente se encuentra plenamente implementado y validado en tests unitarios, pero permanece desconectado del servidor web FastAPI (no existe la ruta HTTP `/api/lab/submit`).
3. Ambos componentes quedan diferidos para su eventual integración en Post-V1 / V2, supeditados a la arquitectura de observabilidad práctica.

---

```text
ID: V15-THETA-CALIBRATION

STATUS: DEFERRED_POST_V1
PRODUCTION_BEHAVIOR = UNCHANGED
```

### Síntesis Metodológica y Evidencia Preservada
- Refiere a la calibración empírica y optimización bayesiana del umbral numérico de confianza y abstención ($\theta$) en la compuerta de confianza C5 (`src/study_engine/context/c5_trust.py`).
- En V1, el sistema opera con reglas deterministas estrictas de admisibilidad y abstención fail-closed.
- La recopilación de curvas empíricas de calibración y análisis de sensibilidad estadística queda preservada para Post-V1, manteniendo inmutable el comportamiento de V1.

---

## 3. Future Engineering / Research Candidates

A continuación se inventarían las líneas de investigación, optimización y evolución de plataforma ya identificadas en el historial del proyecto:

1. **`V15-RETRIEVAL-ADVANCED`**: Investigación de estrategias de recuperación híbrida contextual multietapa y expansión basada en Knowledge Components.
2. **`V15-DENSE-RETRIEVAL`**: Reactivación de búsqueda vectorial densa local una vez resuelta la homogenización del sustrato.
3. **`V15-RERANKER-INTEGRATION`**: Integración condicional de reranking neural local INT8 en rutas interactivas con control de latencia estricto (<100 ms).
4. **`V15-CONTEXTPACK`**: Expansión contextual guiada por grafos de conocimiento o dependencias estructurales post-V1.
5. **`V15-SUFFICIENCY-GATE`**: Investigación de evaluadores semánticos livianos (SLM dedicado o validadores de premisas lógicas) para detección de completitud de evidencia.
6. **`V15-CORPUS-ENGINEERING`**: Ingesta e indexación de bundles curriculares con metadatos estructurales completos y tablas Markdown normalizadas.
7. **`V15-EMBEDDINGS-REALIGNMENT`**: Estandarización de dimensiones vectoriales y migración ordenada del almacén vectorial.
8. **`V15-S6-SANDBOX`**: Sandbox de ejecución de código en servidor con auditoría forense de syscalls e integración de contenedores seguros.
9. **`V15-LAB-GRADER`**: Exposición de endpoints HTTP seguros para envío y calificación de flags en entornos CTF / laboratorios prácticos.
10. **`V15-THETA-CALIBRATION`**: Calibración estadística de umbrales de decisión pedagógica y aversión a la alucinación.
11. **`V15-MEMORY-OPTIMIZATIONS`**: Mecanismos de resumen rodante (*rolling conversation summarization*) para turnos largos que superen el buffer de caracteres.
12. **`V15-EMBEDDING-WARMUP`**: Pre-calentamiento asíncrono y pinning en RAM de estructuras de indexación durante el arranque del servicio.
13. **`V15-OBSERVABILITY-METRICS`**: Exportación de métricas OpenTelemetry / Prometheus sobre consumo de tokens por capa C3 y latencias de inferencia multi-proveedor.
14. **`V15-PEDAGOGICAL-ADAPTIVITY`**: Calibración personalizada de parámetros de deslizamiento y adivinanza en BKT según ritmo de aprendizaje del estudiante.
15. **`V15-LEARNING-UI-ENHANCEMENTS`**: Representación interactiva del grafo de dependencias curriculares y visualización en tiempo real del progreso cognitivo.

---

## 4. External Tools / GitHub Candidates

Inventario de herramientas y repositorios de terceros analizados o discutidos durante la arqueología técnica y el laboratorio experimental. Este inventario tiene fines exclusivamente documentales y **no autoriza la integración ni instalación** de ninguna de estas dependencias en V1.

### 1. Docling
- **Nombre:** Docling (IBM Research)
- **URL:** `https://github.com/DS4SD/docling`
- **Propósito:** Parser y convertidor documental avanzado para extracción de PDFs con análisis de layout, detección de jerarquías de encabezados, código y tablas.
- **Problema que podría resolver:** Pérdida de estructura tabular y segmentación semántica deficiente en extractores basados únicamente en cadenas de texto plano.
- **Relación con TALOS:** Evaluado experimentalmente en CP114, CP115 y CP116 como extractor candidato (`docling_structural`) en el Corpus Intelligence Lab.
- **Estado:** `RESEARCH_ONLY`
- **Dependencias:** PyTorch, torchvision, HuggingFace transformers, modelos de visión para segmentación de página, OCR tesseract.
- **Riesgo de integración:** Muy alto consumo de memoria RAM (requiere >2 GB adicionales para inferencia local), dependencias pesadas e incompatibles con el entorno congelado de V1.

### 2. PyMuPDF (fitz)
- **Nombre:** PyMuPDF / fitz
- **URL:** `https://github.com/pymupdf/PyMuPDF`
- **Propósito:** Biblioteca de procesamiento y extracción de texto de alto rendimiento para documentos PDF, XPS y EPUB.
- **Problema que podría resolver:** Extracción ultrarrápida de texto base y metadatos de documentos fuente sin dependencias de deep learning.
- **Relación con TALOS:** Parser base histórico utilizado en la ingesta inicial de las fuentes curriculares de TALOS.
- **Estado:** `DEFERRED`
- **Dependencias:** Binarios compilados C de MuPDF, bindings de Python.
- **Riesgo de integración:** Bajo/Medio en instalación; limitación intrínseca para reconstruir tablas complejas y fórmulas matemáticas.

### 3. Mem0 (Librería Externa)
- **Nombre:** Mem0 (The Memory Layer for Personalized AI)
- **URL:** `https://github.com/mem0ai/mem0`
- **Propósito:** Capa de memoria longitudinal persistente para agentes conversacionales, basada en grafos o almacenes vectoriales externos.
- **Problema que podría resolver:** Automatización de perfiles de usuario y recuperación semántica de preferencias de largo plazo.
- **Relación con TALOS:** Auditado en CP104. TALOS **no utiliza** la librería externa `mem0`. Diseñó e implementó un subsistema 100% soberano y determinista (`Mem0Manager` en `src/study_engine/memory/mem0_manager.py`) que persiste en SQLite local.
- **Estado:** `REJECTED` (como dependencia de terceros; se mantiene la implementación soberana local).
- **Dependencias:** Requiere almacenes vectoriales externos (Qdrant, Pinecone, Chroma) y llamadas a APIs de LLM externas para extracción.
- **Riesgo de integración:** Inaceptable para V1; compromete la privacidad de datos pedagógicos, incrementa la latencia y genera dependencia de servicios externos.

### 4. SentenceTransformers
- **Nombre:** SentenceTransformers (UKP Lab)
- **URL:** `https://github.com/UKPLab/sentence-transformers`
- **Propósito:** Marco de trabajo para cálculo de representaciones densas de texto y búsqueda semántica.
- **Problema que podría resolver:** Ejecución nativa del modelo `Qwen/Qwen3-Embedding-0.6B` para compatibilizar la dimensión con los 287k vectores existentes en `vector_store.db`.
- **Relación con TALOS:** Auditado en CP104. Ausente en `.venv`, lo que desactiva la búsqueda vectorial y activa el fallback determinista a FTS5 BM25.
- **Estado:** `DEFERRED`
- **Dependencias:** PyTorch, transformers, huggingface-hub (~1.5 GB de huella en disco).
- **Riesgo de integración:** Elevado consumo de RAM y CPU en inferencia local; innecesario en V1 dado el excelente desempeño y cobertura de FTS5 BM25.

### 5. ONNX Runtime
- **Nombre:** ONNX Runtime (Microsoft)
- **URL:** `https://github.com/microsoft/onnxruntime`
- **Propósito:** Motor de inferencia multiplataforma de alto rendimiento para modelos de aprendizaje automático.
- **Problema que podría resolver:** Inferencia local INT8 de modelos de reranking y embeddings en CPU sin necesidad de PyTorch ni GPU dedicada.
- **Relación con TALOS:** Componente presente y validado en `LocalONNXReranker` (BGE-Reranker-Base INT8) y `LocalONNXEmbeddingProvider` (multilingual-e5-small).
- **Estado:** `DEFERRED` (la invocación activa en chat principal queda diferida a Post-V1).
- **Dependencias:** `onnxruntime` (paquete de Python con librerías compartidas C++).
- **Riesgo de integración:** Bajo; ya verificado en el repositorio con latencias de ~80 ms en CPU Ryzen 5 5600GT.

### 6. Jina Reranker / Jina Embeddings API
- **Nombre:** Jina Reranker & Embeddings (Jina AI)
- **URL:** `https://github.com/jina-ai`
- **Propósito:** APIs y modelos remotos para reranking multilingüe y late chunking con ventanas de contexto extendidas.
- **Problema que podría resolver:** Reordenamiento neural de alta precisión sin costo computacional en el hardware local.
- **Relación con TALOS:** Clase cliente implementada en `src/study_engine/retrieval/reranker.py` con fallback transparente a reranker determinista.
- **Estado:** `DEFERRED`
- **Dependencias:** Conexión HTTPS externa, clave de API, tokens de servicio.
- **Riesgo de integración:** Dependencia de conectividad externa y latencia de red; contraviene el principio de operación autónoma y offline de TALOS.

### 7. OWASP Juice Shop & VAmPI
- **Nombre:** OWASP Juice Shop / VAmPI (Entornos de Práctica Vulnerable)
- **URL:** `https://github.com/juice-shop/juice-shop`, `https://github.com/erev0s/VAmPI`
- **Propósito:** Aplicaciones web y APIs intencionalmente vulnerables para entrenamiento en seguridad ofensiva y defensiva.
- **Problema que podría resolver:** Provisión de retos prácticos reales donde el estudiante extrae flags SHA-256.
- **Relación con TALOS:** Mapeados en `config/lab_kc_map.json` para validación de flags en `LabGraderBridge`.
- **Estado:** `DEFERRED` (la integración y exposición web de entrega de flags pertenece a Post-V1 / V2).
- **Dependencias:** Docker, contenedores aislados, orquestación de red local.
- **Riesgo de integración:** Alto requerimiento de orquestación de infraestructura; ajeno al núcleo epistémico de tutoría socrática de V1.

### 8. SLM Local Generativo para Poda de Contexto
- **Nombre:** Compresor Semántico de Contexto Basado en SLM (ej. tipo "Laya" / Qwen-0.5B)
- **URL:** `IDENTITY_UNVERIFIED`
- **Propósito:** Inferencia con modelo generativo liviano local para sintetizar turnos antiguos y podar evidencia antes de despachar al LLM principal.
- **Problema que podría resolver:** Reducción semántica del prompt frente a recortes heurísticos lineales.
- **Relación con TALOS:** Evaluado conceptualmente en CP104 y CP122.
- **Estado:** `REJECTED` (como mecanismo para la garantía C3).
- **Dependencias:** Runtime generativo local (llama.cpp / vLLM / ONNX GenAI).
- **Riesgo de integración:** La garantía de Hard-Ceiling de contexto (C3) debe ser matemática, determinista e inviolable. Un modelo generativo introduce variabilidad estocástica, riesgo de alucinación y una latencia inadmisible (+150-500 ms) en CPU local.

---

## 5. Matriz de Prioridad V1.5

La siguiente matriz clasifica el estado de todas las líneas de evolución diferidas a Post-V1, consolidando la evidencia actual, el próximo paso requerido y la confirmación expresa de que ninguna forma parte de V1:

| ID | Línea | Estado | Evidencia Actual | Próximo Paso | V1 |
|---|---|:---:|---|---|:---:|
| **`V15-CONTEXTPACK`** | ContextPack (Expansión L0) | `DEFERRED` | CP120 inconcluso; trade-offs mixtos observados | Nueva hipótesis de activación condicional | **NO** |
| **`V15-SUFFICIENCY`** | Sufficiency Gate Pre-LLM | `DEFERRED` | CP121 H1 not supported (FER=75% o bajo recall) | Nueva investigación de evaluadores semánticos | **NO** |
| **`V15-DENSE`** | Dense Retrieval | `DEFERRED` | Disparidad de dimensiones; FTS5 BM25 suficiente | Realineamiento de sustrato vectorial | **NO** |
| **`V15-RERANKER`** | Reranker Neural en Chat | `DEFERRED` | Implementado pero desconectado de `/api/chat/query` | Validación de latencia en flujo interactivo | **NO** |
| **`V15-CORPUS`** | Corpus Engineering Estructural | `DEFERRED` | CP114–CP122 completados como historial científico | Benchmark comparativo futuro | **NO** |
| **`V15-S6`** | S6 Sandbox de Syscalls | `DEFERRED` | No disponible en servidor (`PRACTICE_UNAVAILABLE`) | Validación de aislamiento en contenedores | **NO** |
| **`V15-LAB`** | LabGrader (Flags SHA-256) | `DEFERRED` | Implementado en Python; sin endpoint HTTP en FastAPI | Validación de endpoint `/api/lab/submit` | **NO** |
| **`V15-THETA`** | Theta Calibration (C5 Trust) | `DEFERRED` | Reglas deterministas activas; pendiente empírico | Calibración empírica de curvas ROC | **NO** |
| **`V15-EMBEDDINGS`** | Embeddings Realignment | `DEFERRED` | Incompatibilidad 1024d vs 384d en SQLite | Migración y reindexación formal de vectores | **NO** |
| **`V15-MEMORY`** | Memoria Longitudinal Avanzada | `DEFERRED` | Mem0 soberano con regex; sin rolling summarizer | Diseño de sintetizador rodante de turnos | **NO** |
| **`V15-OBSERVABILITY`** | Telemetría y Métricas C3 | `DEFERRED` | Traces locales en archivos JSON rotativos | Instrumentación OpenTelemetry / Prometheus | **NO** |
| **`V15-PEDAGOGY`** | Parámetros BKT Dinámicos | `DEFERRED` | Priors estáticos certificados en catálogo KC | Calibración bayesiana adaptativa | **NO** |

---

## 6. V1 IS NOT BLOCKED BY V1.5

> **Las líneas V1.5/Post-V1 son investigaciones o mejoras deliberadamente diferidas. Su ausencia no constituye un defecto de V1 mientras los contratos y criterios de aceptación de V1 permanezcan satisfechos.**

> **No debe utilizarse la existencia de una mejora futura como justificación para reabrir componentes V1 ya cerrados, salvo que aparezca evidencia concreta de incumplimiento de un requisito V1.**

### Fundamentación de Cierre
TALOS V1 resuelve de manera completa, determinista y matemáticamente demostrable el problema de la tutoría socrática epistémica:
- Cuenta con un modelo BKT oficial certificado y persistente en SQLite.
- Dispone de un catálogo canónico de Knowledge Components (`notebook_kc_catalog.json`).
- Implementa retrieval determinista mediante SQLite FTS5 BM25 blindado por Allowlist L3 y filtrado anti-fuga de soluciones.
- Dispone de un enrutador multi-cloud USD 0 con circuit breakers y degradación determinista offline.
- Cuenta con compuertas de aislamiento y garantías de seguridad formalmente auditadas.

La aspiración de incorporar capacidades más complejas (búsqueda vectorial densa híbrida, reranking neural interactivo, expansión contextual automática, ejecución remota de binarios en contenedores o memoria longitudinal basada en grafos) constituye una dirección legítima de evolución, pero **no condiciona ni posterga la entrega y certificación de TALOS V1**.

---

## 7. Continuación de V1 y Próximos Pasos

El proyecto retorna formal e inmediatamente al camino crítico del release de V1.

```text
CURRENT_RELEASE_TARGET = V1
V1_WORK_CONTINUES = TRUE
V1.5_IMPLEMENTATION = FALSE
V1.5_RESEARCH_EXECUTION = FALSE
```

El siguiente trabajo después de la presente directiva se concentra exclusivamente en:

```text
NEXT_V1_WORK =
    E2E_STUDY_LOOP_INTEGRATION
```

seguido por:

```text
RELEASE_INTEGRITY_AND_DOCUMENTATION_SYNC
```

---

## 8. Prohibición Expresa de Reapertura Experimental

Queda terminantemente prohibido como parte de las actividades de cierre de V1:

```text
CP120 rerun
CP121 rerun
CP122 rerun
new ContextPack experiment
new Sufficiency Gate heuristic
new dataset
new qrels
new human adjudication
new embedding benchmark
new corpus benchmark
```

Toda la investigación experimental de Corpus Intelligence Lab permanece sellada, inmutable y disponible como referencia documental histórica.

---

## 9. Bloque Canónico de Cierre

```text
V15_ROADMAP_CREATED = TRUE
V15_IMPLEMENTATION = FALSE
V15_RESEARCH_EXECUTION = FALSE

CP120_STATUS = CLOSED
CP121_STATUS = CLOSED
CP122_FINAL = PASS

CONTEXT_PACK_STATUS = DEFERRED_POST_V1
SUFFICIENCY_GATE_STATUS = DEFERRED_POST_V1

PRODUCTION_STATUS = UNCHANGED
DATABASE_CHANGES = 0

V1_WORK_CONTINUES = TRUE
NEXT_V1_WORK = E2E_STUDY_LOOP_INTEGRATION
```
