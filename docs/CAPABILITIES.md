# Capacidades y Límites del Sistema TALOS (v1.0-elite)

**Fecha de Publicación**: 23 de Septiembre de 2026  
**Versión de Release**: `v1.0-elite.1`  
**Estado de Certificación**: Producción / Cierre de Ciclo

---

## 1. Capacidades Certificadas

TALOS es un entorno de tutoría epistémica adaptativa diseñado para la enseñanza rigurosa de Ingeniería de Software, Arquitectura de Computadoras, Sistemas Operativos y Ciberseguridad.

> [!NOTE]
> **Evolución de la Suite de Pruebas**: Durante el cierre de la Fase B, el release gate consolidó **2.418 tests pasando**. Con la incorporación de la Fase 7 (Retrieval Fabric Lite con 14 tests de router, reranker y fabric) junto a las suites completas de perfil metacognitivo y generación adaptativa, la suite consolidada alcanzó **2.441 tests pasando, 7 skipped, 0 failed**.

### 1.1 Retrieval Fabric Lite (Fase 7)
- **Router Adaptativo Determinista (`AdaptiveRouter`)**:
  - Clasificación en 3 perfiles de recuperación según la naturaleza sintáctico-semántica de la consulta:
    1. `EXACT_LEXICAL`: Activado ante identificadores técnicos y de lenguaje (p. ej., `pthread_mutex_lock`, `SIGSEGV`, `%rax`, `uint32_t`, llamadas al sistema). Desactiva el reranker para evitar penalizaciones léxicas y asegura matching de código exacto.
    2. `CONCEPTUAL_SEMANTIC`: Activado ante preguntas explicativas y teóricas (*"cómo funciona"*, *"definir"*, *"por qué"*). Emplea búsqueda híbrida con reranker activado.
    3. `COMPOSITE_FACETED`: Activado ante consultas comparativas o multiconcepto (*"diferencias entre stack y heap"*).
  - Determinismo estricto: 100 ejecuciones idénticas producen idénticas decisiones de ruteo sin estado mutable.
- **Reranker Local Determinista (`DeterministicLocalReranker`)**:
  - Algoritmo de scoring normalizado en $[0.0, 1.0]$ con correlación de Spearman $\ge 0.70$ contra ordenamientos de referencia:
    $$\text{Score} = 0.4 \times \text{cobertura} + 0.3 \times \text{bigramas} + 0.3 \times \text{posición}$$
- **Reranker Remoto Opcional con Fallback Local (`JinaReranker`)**:
  - Componente opcional que se activa únicamente si se configura una variable de entorno `JINA_API_KEY` y existe conectividad HTTPS saliente. Opera con timeout de $2.0$ segundos y reintentos con jitter.
  - Fallback gracioso transparente: ante ausencia de clave, cortes de red, errores HTTP o latencias elevadas, conmuta automáticamente al `DeterministicLocalReranker` sin propagar excepciones ni degradar la disponibilidad del servicio.
- **Chokepoint Único de Retrieval**:
  - Consolidado en `RetrievalFabricLite.retrieve()` y `RetrievalService.retrieve_evidence()`, asegurando que toda consulta atraviese:
    $$\text{Re-escritura} \longrightarrow \text{Ruteo} \longrightarrow \text{Pooling} \longrightarrow \text{Anti-Leakage} \longrightarrow \text{Reranking} \longrightarrow \text{Top-}K$$

### 1.2 Generación Dinámica Adaptativa (Fase B)
- **Generador Multi-KC Causal**:
  - Selección de combinaciones de 2 a 3 Knowledge Components (KCs) en los que el estudiante exhibe maestría consolidada ($P(L) > 0.6$).
  - Familias causales curadas: Punteros + Memoria Dinámica, Concurrencia + Mutexes, Redes + Buffers, Procesos + Señales.
  - **Oráculo Determinista**: Validación de soluciones mediante suites de pruebas estructurales ejecutables en C/Python, eliminando completamente el juicio heurístico o por LLM.
- **Generador de Desafíos BugSpotter**:
  - 12 plantillas estáticas rigurosamente curadas para las 4 debilidades comunes de software crítico:
    - **CWE-120**: Classic Buffer Overflow (funciones no acotadas `strcpy`/`sprintf`).
    - **CWE-190**: Integer Overflow or Wraparound (aritmética de punteros o asignaciones no validadas).
    - **CWE-362**: Race Condition (accesos concurrentes a memoria compartida sin sincronización atómica).
    - **CWE-416**: Use After Free (desreferenciación posterior a `free()`).
  - Mutación controlada e inyección de bugs pedagógicos con línea de inserción y explicación formal de causa raíz.
- **Trace Tables x86-64**:
  - Micro-intérprete en Python puro para trazabilidad didáctica de ejecución en ensamblador x86-64.
  - Soporte de 8 instrucciones base (`MOV`, `ADD`, `SUB`, `XOR`, `CMP`, `JMP`, `JZ`, `JNZ`).
  - Emulación de registros de 64 y 32 bits (`rax/eax`, `rbx/ebx`, `rcx/ecx`, `rdx/edx`, `rsi/esi`, `rdi/edi`, `rsp/esp`, `rbp/ebp`).
  - Gestión determinista de flags de CPU (`ZF`, `SF`, `OF`), puntero de pila y memoria flat con límite `MAX_STEPS=100` para prevenir loops infinitos.

### 1.3 Perfil Metacognitivo y Andamiaje Adaptativo (Perfil Metacognitivo)
- **Detección Formal de Evasión y Sobreconfianza**:
  - **Evasión**: $\text{intentos} \ge 2 \land (\text{soluciones} / \text{intentos}) > 0.5$.
  - **Sobreconfianza**: $\text{intentos} \ge 3 \land \text{intentos exitosos} = 0 \land \text{soluciones} = 0$.
- **Índice de Autonomía Normalizado**:
  - Cold start ($< 3$ intentos): $0.5$ (neutral).
  - Cero consultas de solución con intentos $\ge 3$: $1.0$ (autonomía plena).
  - Tasa general: $\min\left(1.0, \frac{\text{intentos exitosos}}{\text{soluciones consultadas} \times 10}\right)$.
- **Andamiaje Dinámico en 3 Niveles con Fading**:
  - *Dependencia Alta*: Directiva de andamiaje estricto (micro-preguntas socráticas paso a paso).
  - *Dependencia Moderada*: Pistas conceptuales intermedias y verificación de hipótesis.
  - *Autonomía Plena*: Retiro de andamios (*fading*), desafiando al estudiante a liderar el razonamiento formal.
- **Prioridad Inviolable del Protocolo de Lucha (*Struggle Mode*)**:
  - Si el estudiante se encuentra en estado de lucha activa ante un problema, el sistema suspende las directivas metacognitivas habituales y prioriza la contención pedagógica según el protocolo de remediación.

### 1.4 Seguridad Perimetral y Anti-Leakage
- **Perímetro Congelado**:
  - Los módulos nucleares de estado, ejecución, evaluación y auditoría (`src/study_engine/{state,execution,assessment,audit}/`) permanecen en 0 líneas de diff respecto a la línea base certificada.
- **Filtro Universal Anti-Leakage**:
  - Desacoplamiento criptográfico y de presentación de soluciones canónicas en el `ContentRegistry`.
  - El estudiante nunca tiene acceso a fragmentos etiquetados como `solution` durante la exploración pedagógica o generación de ejercicios.
- **Autenticación Administrativa y Control de Tasa**:
  - Los endpoints de inspección y oráculo (`/fabric/inspect`, `/api/exercises/generate?include_oracle=true`) exigen el header `X-Admin-Token` (retornando `403 Forbidden` sin credenciales válidas).
  - Rate limiting en memoria fijado en 10 requests por minuto por cliente IP en endpoints de inspección intensiva (`429 Too Many Requests`).
- **Rotación Forense de Trazas**:
  - Logs forenses estructurados en JSON (`RotatingFileHandler`) limitados a 10 MB por archivo con hasta 5 backups históricos en `logs/retrieval_trace.json`.

### 1.5 Context Engine 2.0: Late Chunking (Fase 5 - v1.1)
- **Late Chunking opcional**: Preserva contexto semántico global del documento antes de dividir en chunks, evitando que funciones de código y conceptos queden partidos al medio.
- **Modelo**: `jinaai/jina-embeddings-v3` (8k tokens de contexto) / multi-backend local ONNX (`multilingual-e5-small`) y fallback determinista.
- **Activación**: Config flag `ENABLE_LATE_CHUNKING=true`.
- **Fallback automático**: Si el documento excede `max_document_tokens` o el modelo no está disponible, usa chunking tradicional.
- **Detección de contexto**: Identifica si el chunk es código (`code`), prosa (`prose`) o mixto (`mixed`) para optimizar búsqueda semántica e interoperabilidad con contratos `Chunk`.

---

## 2. Límites Conocidos del Sistema

Para garantizar transparencia y confiabilidad operativa, se documentan los límites actuales de TALOS v1.0:

### 2.1 Presupuesto de Contexto en Sesiones Extendidas (BACKLOG-CTX-001)
- **Estado**: CERRADO (Fecha de cierre: 23 de septiembre de 2026).
- **Métrica observada**: Durante turnos socráticos de alta densidad documental, el percentil 99 de consumo de tokens alcanza **$3.688$ tokens** (máximo observado: $3.877$ tokens).
- **Resolución**: Presupuesto elevado a **$5.000$ tokens** (+28% de holgura sobre el máximo observado de $3.877$ tokens), asegurando holgura operativa suficiente y eliminando el riesgo de truncamiento en sesiones extendidas (10-15 turnos) sin degradación de latencia ($p90 < 2.500$ ms).

### 2.2 Dependencias Externas Opcionales y Red
- El componente `JinaReranker` es **estrictamente opcional**. Si el entorno se ejecuta en aislamiento de red o sin clave de API, el sistema opera con el `DeterministicLocalReranker` de forma predeterminada sin requerir intervención manual ni conexión a Internet.
- La generación de respuestas socráticas puede operar con modelos locales o mockeados, reservando los adaptadores LLM para entornos donde se provean credenciales.

### 2.3 Ámbito Curricular Estricto (Abstención por Diseño)
- TALOS **no es un asistente de propósito general**. No responderá consultas sobre cultura general, temas ajenos a la ingeniería informática o disciplinas no incluidas en los cuadernos del estudiante.
- Cualquier consulta fuera de alcance curricular activa el evento SSE `abstention` por diseño arquitectónico deliberado.

### 2.4 Alcance de la Comparativa Externa
- Las comparaciones cualitativas con Gemini Notebook y Gemini Study Notebooks están **basadas en documentación pública y análisis funcional de producto**, no en un benchmark empírico ciego directo a gran escala (el cual está proyectado para el Roadmap v1.1).

---

## 3. Filosofía de Diseño

TALOS se construyó bajo cuatro principios rectores:

1. **Local-First con operación offline-capable**:
   - Todo el estado pedagógico, las matrices de conocimiento (BKT) y las anotaciones del alumno residen en bases de datos SQLite locales (`student_state.db`, `knowledge_store.db`).
   - El estudiante es el dueño absoluto de sus datos, los cuales pueden exportarse, auditarse o transportarse sin intermediación obligatoria de servidores de terceros.
2. **Rigor Epistémico (Fail-Closed)**:
   - Es preferible abstenerse que inventar. Una respuesta técnica incorrecta o no respaldada por bibliografía universitaria canónica perjudica el aprendizaje; por ende, toda afirmación debe rastrearse a fuentes autorizadas mediante citas formales.
3. **Determinismo Pedagógico y Oráculos de Código**:
   - La corrección de código, las pruebas de software y las tablas de traza se evalúan mediante compilación, ejecución e inspección algorítmica real. Un LLM no actúa como juez de si un código es correcto o tiene fugas de memoria.
4. **Andamiaje con Fading Progresivo**:
   - El propósito del tutor no es suministrar la solución de inmediato, sino guiar al estudiante a través de la zona de desarrollo próximo, retirando progresivamente el soporte para forjar autonomía y pensamiento crítico.

---

## 4. Matriz Comparativa Sintética: TALOS vs Gemini Notebook / Study Notebooks

| Capacidad | TALOS v1.0-elite | Gemini Notebook | Gemini Study Notebooks |
|---|---|---|---|
| **Modelo del Estudiante (BKT)** | ✅ Sí (probabilidad de maestría $P(L)$ por KC) | ❌ No | ❌ No |
| **Detección de Evasión / Sobreconfianza** | ✅ Sí (fórmulas empíricas de tracking) | ❌ No | ❌ No |
| **Abstención Epistémica Rigurosa** | ✅ Sí (CoverageGuard determinista en protocolo) | ⚠️ Parcial (heurística de grounding) | ⚠️ Parcial |
| **Generación de Ejercicios con Oráculo** | ✅ Sí (Multi-KC, BugSpotter, Trace x86) | ❌ No | ❌ No (solo preguntas textuales) |
| **Micro-intérprete Ensamblador x86-64** | ✅ Sí (8 mnemónicos, flags y stack) | ❌ No | ❌ No |
| **Protección Criptográfica Anti-Leakage** | ✅ Sí (ContentRegistry, separación de soluciones) | ❌ No | ❌ No |
| **Operación Offline / Local-First** | ✅ Sí (SQLite local, reranker local determinista) | ❌ No (cloud-dependent) | ❌ No (cloud-dependent) |
| **Fluidez y Narrativa Estilística** | ⚠️ Conciso / Técnico / Socrático | ✅ Excepcional / Prosa extendida | ✅ Didáctica / Audio overviews |
| **Generación de Podcasts / Audio** | ❌ No disponible | ✅ Sí (Audio Overviews) | ✅ Sí |
| **Trazabilidad Forense de Retrieval** | ✅ Sí (JSON rotativo con latencias y scores) | ❌ No disponible para usuario | ❌ No disponible para usuario |
