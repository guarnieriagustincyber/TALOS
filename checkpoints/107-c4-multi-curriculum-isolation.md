# CP107 — AUDITORÍA Y CERTIFICACIÓN DE C4: MULTI-CURRICULUM ISOLATION

## 1. Identidad y marco de certificación

```text
CP = 107
GATE = B (Identidad y aislamiento curricular)
CRITERIA = C4 (Multi-Curriculum Isolation)
BASE_COMMIT = f81134fc2293916210d53c8065f3a0049e52b0b4
DATE = 2026-10-02
ROL = Auditor Técnico Senior de Assurance de TALOS
METODOLOGÍA = OBSERVE → MEASURE → CORRELATE → CLASSIFY → CERTIFY
ESTADO ANTERIOR = C4 = PARTIAL / ASSURANCE_PENDING
DICTAMEN FINAL = C4 = PASS / CLOSED
```

### 1.1 Objetivo

Determinar con evidencia empírica ejecutable, reproducible y trazable si el core de TALOS V1 garantiza aislamiento estricto e inviolable entre currículos durante las fases de:

$$\text{selección} \longrightarrow \text{retrieval} \longrightarrow \text{expansión} \longrightarrow \text{ensamblado de evidencia} \longrightarrow \text{compilación de contexto} \longrightarrow \text{prompt} \longrightarrow \text{evaluación} \longrightarrow \text{respuesta}$$

La pregunta rectora de C4 es:
> **Cuando TALOS opera bajo un currículo determinado, ¿puede información perteneciente a otro currículo entrar en la selección, retrieval, contexto, evidencia o respuesta de manera no autorizada?**

---

## 2. Invariantes de auditoría y estabilidad de base de datos

La auditoría se ejecutó bajo modalidad de **estricta solo-lectura sobre el código fuente de producción y sobre el almacenamiento persistido**. No se aplicaron modificaciones sobre `data/web_state/knowledge_store.db`, ni se crearon capacidades experimentales en el runtime.

### 2.1 Verificación criptográfica de la base de datos
```bash
sha256sum data/web_state/knowledge_store.db
# PRE:  fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1
# POST: fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1
```
```text
DATABASE_CHANGES = 0
INTEGRITY_VERIFIED = PASS
```

### 2.2 Artefactos de código y configuración auditados
| Componente / Artefacto | Ruta | Función en C4 |
| :--- | :--- | :--- |
| `l3_authorization_manifest.json` | `config/l3_authorization_manifest.json` | Autoridad normativa de fuentes L3 |
| `notebook_kc_catalog.json` | `config/notebook_kc_catalog.json` | Catálogo de KCs y topología curricular |
| `notebook_source_roles.json` | `config/notebook_source_roles.json` | Roles epistémicos configurados por cuaderno |
| `scope_resolver.py` | `src/study_engine/hierarchy/scope_resolver.py` | Resolución tipada de Scope (Folder vs Notebook) |
| `chat.py` | `src/study_engine/web/routes/chat.py` | Allowlist, ensamble de contexto y pipeline de chat |
| `expansion.py` | `src/study_engine/retrieval/expansion.py` | Expansión seccional con filtro de 4 capas |
| `evidence_assembler.py` | `src/study_engine/pedagogy/evidence_assembler.py` | Ensamblador de evidencia multi-fuente por rol |
| `mem0_manager.py` | `src/study_engine/memory/mem0_manager.py` | Memoria de largo plazo particionada por KC |
| `folder_orchestrator.py` | `src/study_engine/hierarchy/folder_orchestrator.py` | Coordinación de carpetas y deflexión organizacional |

---

## 3. Definición ontológica y operacional de "Currículo" en TALOS V1

En TALOS V1, el concepto de **currículo** no es un módulo abstracto desacoplado, sino que se materializa operativamente a través de la identidad del **Cuaderno Soberano** (`notebook_id`) y su grafo de conocimiento asociado.

Cada uno de los 5 currículos bajo evaluación en Gate B se encuentra formalmente delimitado por:
1. **Identificador canónico de Cuaderno (`notebook_id`)**: ancla de resolución de scope.
2. **Grafo de Knowledge Components (KCs)**: definido en `config/notebook_kc_catalog.json`, gobernando el modelo BKT y la determinación de objetivos pedagógicos.
3. **Roles Epistémicos de Fuentes**: definidos en `config/notebook_source_roles.json` (PRIMARY, FORMAL, METHODOLOGICAL, IMPLEMENTATION, COMPLEMENTARY).
4. **Frontera Normativa L3**: definida en `config/l3_authorization_manifest.json` e intersectada en tiempo de ejecución con `notebook_sources` de SQLite.
5. **Jerarquía Organizacional de Carpetas**:
   - `fase0-soc` pertenece al árbol `roadmap / roadmap_fase0`.
   - `fadena-lenguajes`, `fadena-so2`, `fadena-std` y `fadena-teleco` pertenecen al árbol `fadena / fadena_1ano / fadena_1ano_2cuat`.

### Inventario de los 5 currículos de Gate B:
| # | Scope / Currículo | Nombre Formal del Cuaderno | Materia / Dominio Curricular | Fuentes L3 Efectivas | Catálogo KCs |
| :---: | :--- | :--- | :--- | :---: | :---: |
| 1 | `fase0-soc` | Roadmap KASIU TECH v4 - Fase 0 | Programación y Pensamiento Algorítmico | **25** | 8 KCs |
| 2 | `fadena-lenguajes` | Lenguajes de Programación - FADENA 2026 | Lenguajes de Programación (C / Algoritmos) | **10** | 10 KCs |
| 3 | `fadena-so2` | Sistemas Operativos II - FADENA 2026 | Sistemas Operativos (Procesos, Sincronización) | **9** | 6 KCs |
| 4 | `fadena-std` | Sistema de Tratamiento de Datos - FADENA 2026 | Tratamiento de Datos y Bases de Datos (SQL / ACID) | **27** | 7 KCs |
| 5 | `fadena-teleco` | Infraestructura de Telecomunicaciones - 2025 | Telecomunicaciones y Redes (TCP/IP, Enrutamiento) | **10** | 12 KCs |
| | **TOTALES** | | | **81 grants** | **43 KCs** |

---

## 4. Distinción epistemológica: C2 vs C4

Debe asentarse con absoluta claridad que **C2 y C4 son garantías ortogonales**:

```text
C2 (Roles de fuente y ACL efectiva):
  Pregunta: ¿Está la fuente X autorizada por la política L3 para operar en el cuaderno Y?
  Foco: Autorización de fuentes, eliminación de bypasses intra-documento y roles epistémicos.

C4 (Multi-Curriculum Isolation):
  Pregunta: Cuando el sistema atiende una sesión o turno en el currículo A, ¿existe alguna
            posibilidad de que contenido, fragmentos, citas, prompts o estados de aprendizaje
            del currículo B contaminen la interacción?
  Foco: Estanqueidad runtime entre currículos en selección, retrieval, expansión,
        evidencia, caché, historia conversacional, fallbacks y concurrencia.
```

Un veredicto de `C2 = PASS` **no implica automáticamente** `C4 = PASS`. C4 requiere demostrar que:
1. Una solicitud en el Currículo A jamás admite fuentes foráneas de B, incluso si el usuario las pide explícitamente en el payload (`active_sources`).
2. Una consulta semántica sobre temas exclusivos de B realizada en A jamás recupera fragmentos de B.
3. El `SectionExpander` jamás cruza fronteras curriculares al expandir texto.
4. Las memorias de sesión, buffers de turnos, cachés epistémicas y fallbacks están estrictamente particionados.
5. Peticiones concurrentes entre distintos currículos no sufren condiciones de carrera ni fugas en memoria compartida.

---

## 5. Análisis de fuentes compartidas: Intersección legítima vs Violación de C4

Entre los 5 currículos existen exactamente **8 fuentes físicas que cuentan con grant L3 en más de un cuaderno**:

```text
1. fase0-soc <-> fadena-so2 (7 fuentes compartidas):
   - src_stallings_os_internals_7ed
   - src_0bc5d20dcc91895f (Clase SO2)
   - src_0fc90b2695369475 (Clase SO2)
   - src_a9a056742dcf69ae (Clase SO2)
   - src_d253687930308e41 (Clase SO2)
   - src_e9682dece40b58ab (Clase SO2)
   - src_f009c4e75f5ca3f2 (Clase SO2)

2. fase0-soc <-> fadena-teleco (1 fuente compartida):
   - src_kurose_computer_networking (Computer Networking A Top-Down Approach)

3. Intersecciones restantes (8 pares posibles):
   - fadena-lenguajes <-> fadena-so2:    0 fuentes compartidas (100% disjuntas)
   - fadena-lenguajes <-> fadena-std:    0 fuentes compartidas (100% disjuntas)
   - fadena-lenguajes <-> fadena-teleco: 0 fuentes compartidas (100% disjuntas)
   - fadena-lenguajes <-> fase0-soc:     0 fuentes compartidas (100% disjuntas)
   - fadena-so2 <-> fadena-std:          0 fuentes compartidas (100% disjuntas)
   - fadena-so2 <-> fadena-teleco:       0 fuentes compartidas (100% disjuntas)
   - fadena-std <-> fadena-teleco:       0 fuentes compartidas (100% disjuntas)
   - fadena-std <-> fase0-soc:           0 fuentes compartidas (100% disjuntas)
```

### Dictamen sobre fuentes compartidas:
* **Naturaleza jurídica**: La coexistencia de grants L3 para estas 8 fuentes fue adjudicada y ratificada formalmente por decisión humana en CP092 y CP101. Constituye una reutilización legítima de bibliografía formativa transversal (Sistemas Operativos y Redes).
* **Criterio de aislamiento C4**:
  - Las 8 fuentes compartidas son válidas **únicamente** cuando se opera dentro de los dos currículos que las autorizan explícitamente.
  - Cuando se opera en `fadena-lenguajes` o `fadena-std`, **ninguna de las 8 fuentes puede ingresar bajo ninguna circunstancia**.
  - Cuando se opera en `fadena-so2`, `src_kurose_computer_networking` **está estrictamente prohibida**.
  - Cuando se opera en `fadena-teleco`, `src_stallings_os_internals_7ed` **está estrictamente prohibida**.
  - Las 17 fuentes de programación exclusivas de `fase0-soc` (Joyanes, Spraul, Sweigart, etc.) **jamás pueden ingresar a `fadena-lenguajes`**, habiendo sido expresamente excluidas en la decisión D2-A.

---

## 6. Resultados de la Matriz de Aislamiento 5x5

Se ejecutó la matriz combinatoria completa de 25 celdas evaluando todas las combinaciones $(C_{\text{target}}, C_{\text{foreign}})$ bajo tres modalidades adversariales por celda:
1. **Subtest 1 (Inyección Activa Foránea)**: El cliente solicita en `active_sources` el conjunto completo de fuentes de $C_{\text{foreign}}$ mientras consulta $C_{\text{target}}$.
2. **Subtest 2 (Ensamble bajo fuentes foráneas)**: Se evalúa si el ensamblado epistémico produce abstención limpia (`NO_AUTHORIZED_ACTIVE_SOURCES` / `abstained=True`) y 0 fragmentos recuperados.
3. **Subtest 3 (Cross-Query Temática)**: Se somete a $C_{\text{target}}$ a una consulta semánticamente alienígena (propia del temario de $C_{\text{foreign}}$) sin indicar `active_sources`.

| $C_{\text{target}} \ \backslash \ C_{\text{foreign}}$ | `fase0-soc` | `fadena-lenguajes` | `fadena-so2` | `fadena-std` | `fadena-teleco` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`fase0-soc`** | **ALLOW** (15 chk, 0 foráneo) | **DENIED** (10 drop, 0 leak) | **DENIED** (2 drop, 0 leak) | **DENIED** (27 drop, 0 leak) | **DENIED** (9 drop, 0 leak) |
| **`fadena-lenguajes`** | **DENIED** (25 drop, 0 leak) | **ALLOW** (15 chk, 0 foráneo) | **DENIED** (9 drop, 0 leak) | **DENIED** (27 drop, 0 leak) | **DENIED** (10 drop, 0 leak) |
| **`fadena-so2`** | **DENIED** (18 drop, 0 leak) | **DENIED** (10 drop, 0 leak) | **ALLOW** (15 chk, 0 foráneo) | **DENIED** (27 drop, 0 leak) | **DENIED** (10 drop, 0 leak) |
| **`fadena-std`** | **DENIED** (25 drop, 0 leak) | **DENIED** (10 drop, 0 leak) | **DENIED** (9 drop, 0 leak) | **ALLOW** (15 chk, 0 foráneo) | **DENIED** (10 drop, 0 leak) |
| **`fadena-teleco`** | **DENIED** (24 drop, 0 leak) | **DENIED** (10 drop, 0 leak) | **DENIED** (9 drop, 0 leak) | **DENIED** (27 drop, 0 leak) | **ALLOW** (15 chk, 0 foráneo) |

```text
RESUMEN MATRIZ 5x5:
- Celdas Intra-Curriculares (Diagonales): 5/5 PASS (100% fuentes autorizadas)
- Celdas Cruzadas (Fuera de diagonal):   20/20 PASS (0 fragmentos foráneos filtrados)
- Bypasses de inyección observados:      0
- Fugas de contenido foráneo:            0
```

---

## 7. Batería de Fixtures Adversariales Especializados (Fixtures D–G)

### 7.1 Fixture D — Límites seccionales en `SectionExpander`
* **Hipótesis adversarial**: Un chunk semilla proveniente de un currículo foráneo ($C_{\text{foreign}}$) es inyectado al motor de expansión seccional bajo el contexto de un currículo objetivo ($C_{\text{target}}$).
* **Prueba**: Se presentaron 3 chunks semilla de `fadena-teleco` (`src_kurose_computer_networking`) a `SectionExpander` configurado con la allowlist de `fadena-lenguajes`.
* **Resultado**:
  - Nivel 1 de Defense in Depth descartó el 100% de las semillas foráneas previo a cualquier consulta SQL.
  - Fragmentos expandidos resultantes: **0**.
  - Texto seccional generado: **`""` (cadena vacía)**.
* **Veredicto**: `SECTION_EXPANDER_CROSS_CURRICULUM = PASS / BLOCKED`.

### 7.2 Fixture E — Ensamblado de Evidencia Epistémica (`MultiSourceEvidenceAssembler`)
* **Hipótesis adversarial**: La resolución de evidencia socrática por roles de fuentes recupera o cita fuentes ajenas al catálogo normativo del cuaderno.
* **Prueba**: Se ejecutó `assemble_evidence_for_kc()` sobre los 5 cuadernos con consultas abiertas.
* **Resultado**:
  - `fase0-soc`: 12 citas ensambladas, 100% dentro de las 25 fuentes autorizadas.
  - `fadena-lenguajes`: 20 citas ensambladas, 100% dentro de las 10 fuentes autorizadas (0 citas de Joyanes, Spraul, etc.).
  - `fadena-so2`: 16 citas ensambladas, 100% dentro de las 9 fuentes autorizadas (0 citas de Kurose ni de fuentes de BD).
  - `fadena-std`: 52 citas ensambladas, 100% dentro de las 27 fuentes autorizadas (0 citas de SO ni de redes).
  - `fadena-teleco`: 20 citas ensambladas, 100% dentro de las 10 fuentes autorizadas (0 citas de Stallings ni de programación).
* **Veredicto**: `EVIDENCE_ASSEMBLER_ISOLATION = PASS`.

### 7.3 Fixture F — Aislamiento de Memoria, Historial y Fallbacks
* **Caché Epistémica (`_LAST_EPISTEMIC_PACK`)**:
  - La clave de caché `_epistemic_cache_key` incorpora canónicamente:
    `[session_id, scope_type, scope_id, notebook_id, requested_scope_id, active_sources]`
  - Una clave de `fase0-soc` produce un hash disjunto de `fadena-lenguajes` aun compartiendo el mismo `session_id`.
  - Se verificó que una inyección de pack sintético en `fase0-soc` no puede ser leída ni rescatada por un turno de fallback en `fadena-lenguajes`.
* **Buffer de Turnos e Historia Activa**:
  - `_CONV_TURN_BUFFER` se encuentra particionado por `context_cache_key` (específico del cuaderno).
  - `_ACTIVE_TURN_HISTORIES` se indexa explícitamente mediante `f"{session_id}:{target_notebook_id}"`.
* **Memoria de Largo Plazo (Mem0)**:
  - Las directivas de conceptos erróneos (`misconceptions`) se filtran estrictamente por `kc_id=matched_kc_id`.
  - El matching de KC (`_match_context_kc_id`) se restringe exclusivamente al catálogo del cuaderno activo (`nb_catalog.get("kcs", [])`).
  - No existe fuga de errores conceptuales entre materias distintas.
* **Veredicto**: `STATE_AND_MEMORY_ISOLATION = PASS`.

### 7.4 Fixture G — Concurrencia Multi-Hilo y Ausencia de Race Conditions
* **Hipótesis adversarial**: Sesiones simultáneas que consultan currículos distintos provocan entrecruzamiento de variables de contexto o corrupción de allowlists compartidas.
* **Prueba**: Se instanciaron 20 workers en paralelo (`ThreadPoolExecutor(max_workers=10)`) disparando consultas asincrónicas aleatorizadas sobre los 5 currículos simultáneamente.
* **Resultado**:
  - Total de solicitudes ejecutadas: **20/20**.
  - Errores de concurrencia / excepciones: **0**.
  - Fragmentos foráneos observados en cualquier hilo: **0**.
* **Veredicto**: `CONCURRENCY_ASSURANCE = PASS`.

---

## 8. Auditoría Estática de Superficie de Exposición (Rutas Web vs Low-Level Store)

Se analizó la totalidad de los 20 archivos de rutas web (`src/study_engine/web/routes/*.py`) para identificar si alguna función o endpoint expone acceso directo a primitivas de almacenamiento de chunks (`store.get_chunk`, `store.chunks.list_by_source`, `store.get_document`) sin validación de cuaderno:

```text
SEARCH_TERMS:       ['get_chunk', 'get_document', 'list_by_source', 'get_chunks_for_source', 'search_hybrid', 'search(']
FILES_SCANNED:      20 archivos en web/routes/
MATCHES TOTALES:    24
RELEVANT MATCHES:   24
FALSE POSITIVES:    0
UNPROTECTED ACCESS: 0
```

### Hallazgos de la auditoría estática:
1. **`chat.py`**: Todos los accesos a `store.search_hybrid` o `store.search` están gobernados por `retrieval_source_ids` y `_source_ids_for_notebook`, con verificación cruzada contra el manifiesto L3.
2. **`retrieval.py` (`/api/retrieval/fabric/inspect`)**: Endpoint protegido por `X-Admin-Token` y rate-limiting (10 req/min). Exige `notebook_id` explícito y no es accesible a estudiantes no autenticados.
3. **`sources.py`**: Sirve páginas y metadatos de documentos basándose estrictamente en el hash SHA-256 del documento físico, sin exponer capacidades de búsqueda cruzada de fragmentos entre cuadernos.
4. **`curriculum.py`**: Endpoint `/api/curriculum/roadmap` devuelve el grafo de KCs correspondiente al `notebook_id` solicitado; si no se provee, recurre al catálogo por defecto.
5. **Cero accesos desprotegidos**: No existe ninguna ruta web que permita a un cliente extraer fragmentos de texto arbitrarios eludiendo la frontera del cuaderno.

---

## 9. Análisis del Alcance de Carpetas (`FolderOrchestrator` y `folder_root`)

TALOS implementa una jerarquía de dos niveles mediante `ScopeResolver` (`ScopeType.FOLDER` vs `ScopeType.NOTEBOOK`):

```text
                        folder_root (Workspace Global)
                         /                          \
                     roadmap                       fadena
                        |                             |
                  roadmap_fase0                   fadena_1ano
                        |                             |
                   [fase0-soc]                 fadena_1ano_2cuat
                                           /      /       \      \
                                     [leng]     [so2]   [std]  [teleco]
```

### Comportamiento ante consultas en carpetas:
1. **Consultas organizacionales** ("materias que tengo", "avance", "resumen de estado"):
   - Son interceptadas inmediatamente por `FolderOrchestrator`.
   - Devuelven metadatos de progreso o coordinación sin invocar recuperación técnica ni llamadas LLM.
2. **Consultas técnicas bajo una subcarpeta**:
   - `ScopeResolver` resuelve los cuadernos descendientes mediante `_notebook_ids_for_folder()`.
   - Para la carpeta `fadena` (o `fadena_1ano_2cuat`), la allowlist se expande únicamente a los 4 cuadernos FADENA (`lenguajes`, `so2`, `std`, `teleco`). `fase0-soc` queda **completamente excluida**.
   - Para la carpeta `roadmap` (o `roadmap_fase0`), la allowlist se restringe únicamente a `fase0-soc`.
   - Por tanto, la jerarquía de carpetas respeta de forma estricta las fronteras curriculares entre ramas independientes.
3. **Workspace Global (`folder_root`)**:
   - Diseñado exclusivamente para el modo explícito de búsqueda transversal sobre todo el workspace de desarrollo.
   - Cuando un estudiante ingresa a estudiar una materia, el frontend y la API fijan `scope_type="notebook"` y `scope_id=target_notebook_id`, confinando la sesión de forma irreversible a dicho currículo.

---

## 10. Matriz de Cumplimiento de C4

| # | Dimensión de Aislamiento | Mecanismo de Control | Resultado Empírico | Dictamen |
| :---: | :--- | :--- | :---: | :---: |
| 1 | **Selección / Inyección Activa** | Intersección con allowlist en `_filter_requested_sources` | 20/20 denegados; 0 fugas | **CUMPLE** |
| 2 | **Retrieval Léxico y Semántico** | Filtrado SQL por `ns.notebook_id = ?` y `source_id IN (...)` | 20/20 consultas cruzadas confinadas | **CUMPLE** |
| 3 | **Expansión Seccional** | Defense in Depth Nivel 0 a 3 en `SectionExpander` | 0 fragmentos expandidos fuera de scope | **CUMPLE** |
| 4 | **Ensamblado de Evidencia** | Restricción por rol y L3 en `MultiSourceEvidenceAssembler` | 100% de citas pertenecientes al currículo | **CUMPLE** |
| 5 | **Caché Epistémica y Fallback** | `_epistemic_cache_key` particionado por `notebook_id` | Cero rescate de packs entre materias | **CUMPLE** |
| 6 | **Historial Conversacional** | `history_key = f"{session_id}:{notebook_id}"` | Turnos aislados por cuaderno | **CUMPLE** |
| 7 | **Memoria a Largo Plazo** | Mem0 filtra misconceptions por `kc_id` del catálogo local | Sin fuga de fallas conceptuales cruzadas | **CUMPLE** |
| 8 | **Concurrencia Multi-Turno** | Inmutabilidad de estado de turno y aislamiento por sesión | 20 workers simultáneos sin race condition | **CUMPLE** |
| 9 | **Superficie de Exposición Web** | Cero rutas HTTP desprotegidas con acceso a chunks | 20 archivos de rutas auditados (0 fugas) | **CUMPLE** |
| 10 | **Integridad de Base de Datos** | Comprobación de SHA-256 pre y post ejecución | `DATABASE_CHANGES = 0` | **CUMPLE** |

---

## 11. Dictamen Definitivo de C4

Habiéndose verificado empíricamente la estanqueidad absoluta entre los 5 currículos de Gate B en todas las capas del pipeline (selección, retrieval, expansión, evidencia, memoria, fallbacks y concurrencia), habiéndose cumplido las 25 combinaciones de la matriz 5x5 sin una sola fuga ni bypass, y habiéndose preservado bit-a-bit la base de datos de producción:

```text
================================================================================
DICTAMEN FORMAL DE GATE B — CRITERIO 4:
C4 = PASS / CLOSED
================================================================================
```

---

## 12. Estado Consolidado de Gate B

```text
C1 (IDs / aliases / curriculum_id) = PASS / CLOSED  (CP097)
C2 (Roles de fuente y ACL efectiva) = PASS / CLOSED  (CP102)
C3 (Hard-ceiling de contexto)       = AUDITED / BLOCKED (HUMAN_DECISION_PENDING en CP106)
C4 (Multi-Curriculum Isolation)     = PASS / CLOSED  (CP107)
C5 (Gate de abstención y confianza) = BLOCKED / ASSURANCE_BLOCKER

Gate B = NOT YET CLOSED (Pendiente cierre de C3 y C5)
```

Con la certificación material de **C4**, Gate B cuenta con tres (3) de sus cinco garantías formalmente cerradas (`C1`, `C2` y `C4`). Los pendientes para alcanzar la certificación integral de Gate B quedan estrictamente delimitados a la adjudicación humana y corrección de **C3** (Hard-Ceiling de contexto) y el cierre de **C5** (Abstención y Confianza).
