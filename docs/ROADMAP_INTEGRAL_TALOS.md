# TALOS — Roadmap integral y gobernanza documental

## 1. Identidad y alcance

- Repositorio: `/media/agustin/Laboratorio/study-engie`
- Rama de referencia: `talos-current-audit`
- HEAD de referencia: `032339436639d33d310c437c88fe01d94e977449`
- Estado de edición: creación documental autorizada por la directiva canónica TALOS-ROADMAP-001.
- Alcance: consolidar el estado real del sistema, la evolución de V1.0-elite → V1.5 → reconstrucción documental y validación del corpus → tramo D → V2, sin ejecutar implementación, pruebas ni gates.
- Autoridad documental: este documento coordina referencias y estados documentales; no reemplaza contratos, criterios de aceptación, gates superiores ni el plan maestro. La autoridad efectiva debe contrastarse con los documentos canónicos vigentes, en particular [docs/PLAN_MAESTRO_CIERRE_TALOS.md](./PLAN_MAESTRO_CIERRE_TALOS.md) y [docs/ROADMAP_V1_5_MASTER.md](./ROADMAP_V1_5_MASTER.md).

## 2. Principios de gobernanza

### 2.1 Jerarquía de referencia

1. Contratos, criterios de aceptación y gates normativos aprobados.
2. Plan maestro de cierre y documentos canónicos de las fases correspondientes.
3. Roadmap maestro V1.5 y documentación específica del subproceso.
4. Expedientes de adjudicación con autoridad limitada al caso.
5. Informes de ejecución, reportes de agentes y resultados experimentales.
6. Propuestas y candidatos futuros no aprobados.

Si existe contradicción entre la jerarquía vigente y esta hoja de ruta, se conserva la fuente normativa superior; la discrepancia debe registrarse y no resolverse por inferencia.

### 2.2 Clasificación de evidencia

- VERIFIED: comprobado durante la intervención documental actual.
- REPORTED: comunicado por un agente o informe previo, sin reproducción independiente en esta intervención.
- ADJUDICATED: decisión humana o contractual formalmente registrada.
- BLOCKED: precondición no satisfecha o autoridad insuficiente.
- PENDING: trabajo todavía no realizado o decisión aún no tomada.
- PROPOSED: hipótesis o iniciativa futura no aprobada.

No se promociona una entrada REPORTED a VERIFIED por copiarla a otra documentación. Tampoco una decisión ADJUDICATED equivale automáticamente a un test PASS.

### 2.3 Protección del repositorio

Se preserverá el worktree existente y los cambios preexistentes. No se ejecutarán:

- git reset / git clean / git checkout / git restore / git stash
- cambios de rama, tags o referencias Git
- commits, push, merge, rebase
- código del proyecto, tests, gates, benchmark o validaciones
- modificaciones de bases de datos, corpus, índices, snapshots, modelos o estado del estudiante

## 3. Tramo A — TALOS V1.0-elite, referencia histórica congelada

### 3.1 Estado histórico certificado

- Versión: `TALOS V1.0-elite`
- Commit histórico: `67fa4d32f145b129c2e3a2424cee401da11f0730`
- Tag histórico: `v1.0-elite`
- Resultados reportados en la certificación histórica:
  - 2.441 passed
  - 7 skipped
  - 0 failed
  - Golden Set: 18/18
  - OOD fail-closed: 100%
  - fugas de soluciones: 0 en 361 chunks

Estos valores pertenecen a la certificación histórica y no se presentan como reproducidos durante esta actualización documental.

### 3.2 Invariantes de V1

- V1.0-elite permanece congelado.
- Su certificación histórica no se reabre por una modificación documental.
- V1.5 no hereda automáticamente su certificación.
- Las mejoras futuras deben preservar los invariantes aplicables de V1.
- Cualquier corrección de producto requiere la autorización y certificación correspondientes.

## 4. Tramo B — V1: P1.1–P1.6 y bloqueos

La siguiente matriz refleja el estado documental de referencia, contrastado contra los documentos canónicos vigentes. No reemplaza la matriz normativa del plan maestro; si existe discrepancia, se conserva la autoridad documental superior.

| Etapa | Estado de referencia | Restricción |
| --- | --- | --- |
| P1.1 — Terminal SSE | `REPORTED / CLOSED` | Preservar evidencia y cierre existentes |
| P1.2 — Quality Gate, aislamiento y procedencia | `FAIL / DIAGNOSTIC — NOT_CLOSED` | No ejecutar el gate mientras permanezca bloqueado |
| P1.3 — Python/runtime | `PENDING / BLOCKED BY DEPENDENCY` | No iniciar antes del cierre autorizado de P1.2 |
| P1.4 — API | `PENDING` | No adelantar etapas |
| P1.5 — E2E | `PENDING` | Respetar criterios canónicos |
| P1.6 — BKT/SM-2 | `PENDING` | Respetar criterios canónicos |

### 4.1 P1.2 y captura de procedencia

Estado de referencia actual:

- `P1.2 = FAIL / DIAGNOSTIC — NOT_CLOSED`
- `P1.2.B06-RUN = BLOCKED`

La hoja de ruta conserva el bloqueo relacionado con la captura, el aislamiento y la procedencia verificable del snapshot sellado. La evidencia de bloqueo debe mantenerse como evidencia documental y no debe convertirse en verificación independiente.

Invariantes:

- no fabricar atestaciones ni hashes;
- no atribuir a un script de preparación la autoridad de una captura atómica original si el contrato no lo permite;
- no debilitar controles de aislamiento;
- no ejecutar el gate ni pytest mientras las precondiciones canónicas no estén satisfechas;
- no iniciar P1.3 antes del cierre autorizado de P1.2.

### 4.2 Separación entre bloqueo y producto

La existencia de V1.0-elite certificada no autoriza declarar cerrado un gate actual de P1.2. Tampoco se deduce que todos los gates de V1 estén completos a partir de la certificación histórica.

Debe distinguirse:

1. certificación histórica de V1.0-elite;
2. estado de los gates del plan de cierre;
3. bloqueos y precondiciones de las tareas en curso.

## 5. Tramo C — TALOS V1.5: fases canónicas

V1.5 sigue en desarrollo y no está certificada globalmente.

Fases canónicas a preservar:

1. Phase 1 — Evidence Retrieval
2. Phase 2 — Pedagogy
3. Phase 3 — Student Evaluation
4. Phase 4 — Visual Explanations

Para cada fase debe observarse:

- objetivo;
- estado;
- criterios de entrada;
- dependencias;
- criterios de aceptación;
- evidencia exigida;
- condiciones de promoción;
- documento canónico de referencia;
- decisiones aún no adjudicadas.

### 5.1 Fase 1A

La Fase 1A y sus subfases 1A.1, 1A.2 y 1A.3 fueron reportadas como cerradas en la documentación previa. Se conservan sus cierres y referencias sin reabrirlos automáticamente.

La directiva también reconoce que:

- `1A.1` fue reportado como `CROSS-AUDIT COMPLETE`;
- la adjudicación humana ciega V3 y la síntesis factorial de 1A.3 cuentan con resultados reportados;
- no debe asumirse que el cierre documental autoriza comenzar una nueva subfase ni ejecutar experimentos sobre producción.

### 5.2 Invariantes arquitectónicos

Se conservan los principios de TALOS:

- el código determinista tiene prioridad para decisiones reproducibles;
- los modelos pueden proponer resultados, pero no adquieren autoridad sobre evidencia no recuperada;
- las citas deben proceder del contexto autorizado;
- la abstención y el fail-closed deben mantenerse donde los contratos lo exijan;
- los routers no deben modificar el estado pedagógico por su cuenta;
- el narrador no puede inventar evidencia;
- el estado del estudiante y los mecanismos BKT/SM-2 permanecen bajo las reglas del sistema;
- la ayuda pedagógica durante un ejercicio activo debe respetar el pacto pedagógico vigente.

## 6. Tramo D — F2A-012: adjudicación y cierre focal

Expediente canónico: [docs/expedientes/F2A-012-EXPEDIENTE-CANONICO.md](./expedientes/F2A-012-EXPEDIENTE-CANONICO.md)

El expediente declara autoridad limitada al caso F2A-012 y no reemplaza STEP-24, el plan maestro, el roadmap V1.5 ni los contratos superiores.

### 6.1 Alcance técnico focal

Estado documentado:

`F2A-012-FOCAL = COMPLETE — FOCAL TECHNICAL SCOPE`

Este estado se limita a los casos focales adjudicados:

- A-01
- C-01
- C-03a
- C-03b
- C-03c
- C-03e

Los resultados técnicos asociados fueron recibidos como reportes del agente local. No deben presentarse como ejecuciones independientes realizadas durante la actualización del roadmap.

### 6.2 C-03d — adjudicación contractual final

Estado adjudicado:

`C-03d = CLOSED — NOT APPLICABLE TO CURRENT CONTRACT`

Clasificación:

`NOT APPLICABLE TO CURRENT CONTRACT — CONTRACTUAL ADJUDICATION CLOSED`

Fundamento reportado:

- El contrato `CrossNotebookBridge` no define un campo independiente `enabled`, `disabled` o equivalente.
- La autorización efectiva depende de la allowlist, la dirección, el topic permitido y el TTL.
- La ausencia de autorización produce rechazo fail-closed.
- No se identificó una obligación contractual aprobada que exija un estado independiente de habilitación.
- No se requiere modificar el contrato vigente para cerrar la adjudicación.

C-03d no debe clasificarse como PASS. La adjudicación establece que el requisito no resulta aplicable al contrato actual, no que se haya ejecutado un test de aprobación.

Se conserva el historial anterior de C-03d como antecedente legítimo. No se reescribe retroactivamente la decisión previa.

### 6.3 R8 y R8-A — consolidación documental

Los informes locales reportaron:

- `R8`: revisión documental del expediente satisfactoria.
- `R8-A`: búsqueda complementaria de referencias contradictorias satisfactoria.

La búsqueda reportada se realizó en todo el repositorio para tres patrones exactos:

- `C-03d = PENDING`
- `PENDING — SEPARATE CONTRACTUAL ADJUDICATION`
- `NOT PART OF CURRENT CONTRACT — TEST REQUIREMENT UNADJUDICATED`

Se encontró la tercera expresión dentro del historial de adjudicación anterior del expediente canónico, clasificada como antecedente histórico legítimo. No se reportaron contradicciones actuales bajo esos patrones.

Estos resultados se registran como `PASS — REPORTED`, salvo que una verificación posterior independiente aporte evidencia nueva.

### 6.4 R9 — autoridad de la matriz de seguimiento

Estado final:

`MATRIX AUTHORITY UNRESOLVED`

La inspección reportada no identificó una matriz de seguimiento de F2A-012 con autoridad inequívoca. El expediente canónico existente es un registro de trazabilidad, no una matriz formal de seguimiento.

Consecuencias:

- no crear una matriz nueva por inferencia;
- no modificar el expediente para simular que es una matriz operativa;
- no actualizar el plan maestro ni el roadmap para resolver R9 sin una decisión documental específica;
- no reabrir F2A-012 por la falta de una matriz de seguimiento;
- no confundir la autoridad de un expediente con la autoridad de un gate de release.

### 6.5 Alcance global

F2A-012 no equivale a certificación del producto. Se mantiene:

- `PRODUCT COMPLETE`: no demostrado.
- `P1.2.B06-RUN`: `BLOCKED`.
- `P1.2`: `FAIL / DIAGNOSTIC — NOT_CLOSED`.
- Certificación TALOS V1.5: no emitida.
- B — cambio de scope y continuidad de permisos: diferido.

## 7. Tramo E — GIT-03, reconstrucción y DB-0/DB-1

### 7.1 GIT-03 — adjudicación de autoridad Git

La inspección GIT-03 fue reportada como actividad de solo lectura para adjudicar la relación entre `talos-current-audit` y `main`, preservando el worktree.

Resultado reportado en el corte de octubre de 2026:

- `talos-current-audit` tenía cambios staged, unstaged y untracked.
- `main` divergía de la rama de trabajo.
- No se modificaron referencias Git durante la inspección.
- No se demostró una fuente canónica ni una base de datos que pudiera declararse autoritativa sin adjudicación adicional.
- Persistían discrepancias entre la matriz de autorización y el estado observado en disco.
- Los contratos de embeddings de 384, 1024 y 2560 dimensiones seguían sin resolver.

Estas observaciones son evidencia histórica reportada, no un estado actual que debe copiarse sin comprobar el repositorio.

### 7.2 Preservación de ramas y worktree

- No fusionar `main` con `talos-current-audit`.
- No asumir que `main` es la fuente canónica.
- No asumir que `talos-current-audit` es automáticamente la autoridad de todos los datos.
- No descartar, sobrescribir o limpiar cambios locales.
- No inferir autoridad de una base de datos únicamente por su nombre o ubicación.
- No inventar procedencia para resolver discrepancias.

### 7.3 Secuencia documental autorizada

1. GIT-03 — adjudicación de autoridad Git en modo de solo lectura.
2. `B06-RECONSTRUCTION-SPEC` — especificación documental de reconstrucción.
3. DB-0 — inventario y caracterización de fuentes y bases.
4. DB-1 — continuación de la adjudicación e inspección conforme al contrato aprobado.
5. Diseño de un piloto aislado de tres libros en Google Colab, cuando sus precondiciones y autorización estén satisfechas.

Los nombres, alcances y dependencias exactos deben contrastarse con el plan maestro. No se crea un contrato nuevo solo porque un documento todavía no exista.

### 7.4 Estado de B06

`P1.2.B06-RUN = BLOCKED`

La especificación documental y los inventarios de solo lectura no autorizan la ejecución del B06 real ni la reconstrucción canónica.

## 8. Tramo F — auditoría de aislamiento y construcción sintética

La auditoría de backend B0/B0.5 queda como antecedente técnico; sus resultados solo son válidos si siguen vigentes en la autoridad documental actual.

Estado reportado previamente:

- B0: `COMPLETE`
- B0.5: siguiente paso previsto
- B1: bloqueado por B0.5
- B2–B5: no iniciados o diferidos
- Playwright: regresión congelada, no expansión de alcance
- bases de producción y corpus: sin cambios autorizados
- Qwen: sin modificaciones autorizadas

Invariantes:

- `use_mock=True` no significa aislamiento absoluto.
- no utilizar el contenedor de producción como sustituto de un contenedor sintético.
- no iniciar B1 sin satisfacer sus precondiciones.
- no ejecutar HTTP, lifespan o proveedores reales si la directiva correspondiente prohíbe esas operaciones.

## 9. Tramo G — corpus e ingesta mediante Google Colab

### 9.1 Restricción arquitectónica

La ingesta documental se realiza en Google Colab. No se procesa documentación para su ingesta en la máquina local.

La máquina local puede utilizarse para:

- inspeccionar documentación y código;
- auditar artefactos exportados;
- analizar resultados;
- evaluar recuperación;
- ejecutar pruebas permitidas por los contratos y autorizaciones vigentes.

### 9.2 Estado del corpus

El corpus, bases de datos, índices, modelos y estado del estudiante deben permanecer protegidos mientras la reconstrucción no esté autorizada.

Las dimensiones 384, 1024 y 2560 siguen siendo un punto pendiente de compatibilidad, salvo evidencia posterior.

### 9.3 Secuencia de validación

1. adjudicar las fuentes y la autoridad de los artefactos;
2. completar la especificación documental de reconstrucción;
3. realizar DB-0 y DB-1 en el alcance autorizado;
4. diseñar el piloto de tres libros en Colab;
5. comparar la línea base con la canalización experimental;
6. auditar localmente los artefactos exportados;
7. evaluar recuperación, trazabilidad y utilidad pedagógica;
8. documentar resultados, limitaciones y regresiones;
9. solicitar autorización explícita antes de promover o sustituir el corpus.

La planificación de este proceso no autoriza la ejecución del piloto ni la promoción de artefactos.

### 9.4 V5.1.3 — estado experimental reportado

**Estado reportado:** `EXECUTION_OK; STRUCTURAL_MAP_PARTIAL; FIDELITY_UNVERIFIED; NOT_READY_FOR_PRODUCTIVE_RAG`.

Este registro conserva los resultados de la auditoría V5.1.3 aportada por el responsable del proyecto. No implica que esta actualización haya vuelto a inspeccionar el ZIP, los PDF originales o el runtime de Colab. El snapshot y sus resultados deben permanecer inmutables; cualquier iteración se producirá en una versión experimental nueva, sin reescribir retrospectivamente V5.1.3.

Avances reportados que se conservan como evidencia experimental, no como aceptación productiva:

- El JSONL de 97 registros tiene IDs únicos y hashes de texto consistentes con los chunks; los registros se mantienen `provisional_unverified`.
- Se produjo un mapa inicial de entradas de índice para ambos libros y se detectaron coincidencias candidatas entre índice impreso y marcadores PDF.
- Se separaron salidas multimodales no verificadas y se mantuvo su estado `verified=false` / `trusted_for_rag=false`.
- La extracción focal mostró recuperación útil de algunos bloques SQL y tablas, pero con defectos que impiden tratarlos como contenido canónico.

Bloqueos y límites que mantienen el resultado en `NOT_READY_FOR_PRODUCTIVE_RAG`:

- La cobertura del índice de Ramakrishnan es incompleta: la extracción reportada termina en el capítulo 11 y no representa el índice de todo el libro.
- El índice de Coronel combina entradas de marcadores PDF e índice impreso con duplicaciones; las coincidencias son candidatas, no mapeos certificados.
- `section_end` permanece sin certificar; los candidatos calculados no son límites aceptados y ninguna sección consta como verificada por una persona.
- Falta un vínculo estructural validado `section_id` entre capítulos, secciones, páginas y chunks; los artefactos paralelos no constituyen por sí solos un grafo navegable coherente.
- El fallback OCR de portadas está incompleto: se reportaron portadas con OCR disponible que aun así no producen chunks.
- Persisten errores de clasificación y fidelidad en tablas, SQL y diagramas: tablas espurias derivadas de diagramas/SQL, tablas degradadas, posibles pérdidas o corrupciones de caracteres y relaciones visuales incompletas.
- Los hashes y la integridad estructural del export no demuestran fidelidad frente a los PDF completos, cuya inspección integral no se reportó.

### 9.5 V5.1.4 — reconciliación estructural y extracción conservadora

**Estado:** `PROPOSED / EXPERIMENTAL / NOT_IMPLEMENTED / NOT_AUTHORIZED`. Es el siguiente objetivo experimental de la línea V5, no un paquete operativo T01–T20 ni una autorización de trabajo. No altera la secuencia vigente ni habilita integración con TALOS productivo.

Prioridades propuestas:

1. Reconstruir y revisar el índice jerárquico completo de cada libro, conservando por separado las fuentes (marcadores PDF e índice impreso) y haciendo explícita su deduplicación.
2. Validar la correspondencia entre páginas físicas y números impresos; conservar ambigüedad y provenance cuando no pueda resolverse.
3. Determinar límites de capítulos y secciones con criterios verificables; mantenerlos desconocidos cuando la evidencia no alcance.
4. Vincular cada chunk con su sección correspondiente solo después de validar el mapeo estructural y su alcance.
5. Corregir el fallback OCR de portadas y preservar método, alternativas, decisiones de selección y provenance por página y chunk.
6. Establecer pruebas de aceptación focales contra páginas de los documentos originales, distinguiendo texto, tablas, código y diagramas; las pruebas sintéticas no sustituyen el cotejo documental.

No incorporar modelos OCR, VLM ni embeddings nuevos en esta etapa. V5.1.4 no debe reprocesar libros completos por defecto, promover artefactos al RAG canónico ni modificar TALOS, Colab V5.1.3, sus checkpoints o resultados. La implementación, ejecución de modelos y cualquier promoción requieren autorizaciones posteriores, separadas y explícitas.

## 10. Tramo H — herramientas externas y destinos

Las herramientas externas deben distinguirse por destino autorizado:

- TALOS productivo: solo si está autorizado y aislado.
- V2 / investigación: solo si queda claramente fuera del runtime actual.
- desarrollo experimental: solo bajo límites documentados.
- ingesta de corpus: solo en Colab y bajo condiciones de autorización.

OpenClaw queda en investigación para V2 según la clasificación vigente de herramientas. La evolución de V2 no debe degradar los contratos pedagógicos, de evidencia y de seguridad de TALOS ni convertir la experimentación en una dependencia obligatoria del producto actual.

## 11. Orden de ejecución y próxima acción autorizada

### Prioridad 1 — Preservar la autoridad y el worktree

Verificar el estado real de Git y respetar los resultados de GIT-03. No fusionar ramas ni declarar una fuente canónica por inferencia.

### Prioridad 2 — Continuar la reconstrucción documental

La siguiente secuencia de referencia es:

`GIT-03 → B06-RECONSTRUCTION-SPEC → DB-0 → DB-1 → diseño del piloto aislado de tres libros en Colab`

GIT-03 ya fue reportado como inspección de solo lectura. No repetirlo sin una necesidad concreta. Contrastar los resultados existentes y continuar desde el primer artefacto que siga pendiente.

### Prioridad 3 — Mantener bloqueado el gate real

`P1.2.B06-RUN = BLOCKED`

No ejecutar el gate ni iniciar P1.3 mientras las precondiciones canónicas de P1.2 no estén satisfechas.

### Prioridad 4 — Preservar V1.5 y F2A-012

No reabrir la Fase 1A ni repetir F2A-012 por la actualización del roadmap.

C-03d permanece adjudicado como no aplicable al contrato vigente. R9 no autoriza crear una matriz de seguimiento nueva ni modificar un documento sin autoridad identificada.

### Prioridad 5 — Preparar futuras evaluaciones

La investigación de herramientas y la mejora del corpus se realizarán únicamente cuando estén autorizadas y aisladas. No instalar ni integrar componentes en esta tarea.

### Capacidades futuras posteriores a la estabilización de V1.5 — propuesta

Esta subsección registra una oportunidad de evolución, no una etapa operativa,
un compromiso de producto ni una autorización. Solo podrá evaluarse después de
estabilizar V1.5 y satisfacer sus dependencias aplicables. No altera la
secuencia P0–P3, las fases metodológicas V1.5 ni los paquetes T01–T20. El
checkpoint de continuidad conserva la secuencia T01–T20 comunicada y sus
enmiendas; el plan completo no se vuelve a crear ni se sustituye aquí
([checkpoint V1.5 del 2026-10-14](./checkpoints/TALOS_V15_CHECKPOINT_2026-10-14.md)).

#### TALOS Learning Interactives — práctica interactiva

**Estado:** `PROPOSED / POST_V1_5 / NOT_IMPLEMENTED / NOT_AUTHORIZED`.

**Objetivo:** investigar si actividades interactivas, respaldadas por
contenido verificable, pueden complementar la tutoría explicativa y los
ejercicios de TALOS. La iniciativa debe respetar “Deterministic code first. AI
second”: objetivos, reglas de evaluación y transiciones deterministas no se
delegan a texto generado; la representación visual tampoco constituye una
fuente independiente de verdad.

Capacidades a investigar, sin prometer disponibilidad en producto:

- **LI-01 — Objetivos explícitos:** competencia, conocimientos previos y
  condiciones observables de éxito por actividad.
- **LI-02 — Desafíos progresivos:** niveles graduados que comprueben aplicación
  conceptual, no solo recuerdo.
- **LI-03 — Pistas escalonadas:** orientación gradual conectada en el futuro
  con la política/pipeline pedagógica vigente; no modificarlo en esta fase.
- **LI-04 — Feedback contextual:** explicación del error, conceptos
  relacionados y reintentos; usar oráculos deterministas cuando la respuesta
  admita verificación determinista.
- **LI-05 — Representaciones controladas:** estudiar componentes React/SVG
  predefinidos y contratos de datos estructurados. No ejecutar JavaScript
  arbitrario generado por modelos.
- **LI-06 — Validación de actividades:** estudiar solvabilidad, corrección de
  reglas/resultados, valores extremos, estados/transiciones, controles y
  consistencia pedagógica.
- **LI-07 — Seguimiento:** evaluar una integración futura con BKT, SM-2 y
  competencias solo bajo sus contratos y autorizaciones. Una interacción
  visual no demuestra por sí misma dominio.
- **LI-08 — Accesibilidad:** navegación accesible, equivalente textual,
  adaptación a pantallas pequeñas y alternativa sin animación cuando aplique.

#### Candidatos visuales — evaluación pendiente

| Candidato | Función potencial en TALOS | Modalidad propuesta | Estado y cautela |
| --- | --- | --- | --- |
| [Pele](https://pele.run/) | Renderizado de diagramas Mermaid a SVG tematizable para diagramas sencillos. | Renderizador controlado; evaluar el contrato de entrada/salida, seguridad y accesibilidad. | Candidato; no integrado ni aprobado. |
| [Diagram Design](https://github.com/cathrynlavery/diagram-design) | Referencia para diagramas editoriales y representaciones estructurales reutilizables. | Generación/diseño de recursos revisables; evaluar si conviene reutilizar estilos, formatos o ideas sin convertir una skill de agente en dependencia runtime. | Candidato; licencia, mantenimiento, proceso de generación y adecuación al producto requieren revisión. |
| [Anatomy](https://github.com/wheresryan22/anatomy) — perfil conceptual **Anatomy Lite** | Ilustraciones conceptuales SVG e interacciones sencillas para sistemas/estructuras. | Perfil futuro restringido: SVG preferido, baja complejidad visual, interacciones justificadas y componentes reutilizables. | Candidato opcional, no dependencia obligatoria. Excluir por defecto WebGL/3D y simulaciones físicas complejas; revisar seguridad, accesibilidad y licencia antes de cualquier uso. |

Las referencias describen candidatos, no integraciones evaluadas dentro de
TALOS. Pele se presenta como renderizador Mermaid→SVG tematizable; el
repositorio Diagram Design ofrece recursos de diseño de diagramas para agentes;
Anatomy describe generación de ilustraciones SVG con efectos WebGL/3D
opcionales. La compatibilidad, licencia aplicable, seguridad, mantenimiento y
adecuación pedagógica requieren revisión propia antes de seleccionar cualquiera
de ellos.

#### Flujo conceptual y fronteras

```text
contenido recuperado y verificado
  → objetivo de aprendizaje
  → diseño de actividad
  → selección de representación
  → validación
  → interacción del estudiante
  → feedback y seguimiento
```

Mantener separadas: (1) conocimiento y evidencia, (2) lógica del ejercicio,
(3) representación visual, (4) evaluación de respuestas y (5) adaptación
pedagógica. La representación visual presenta el modelo definido por las
capas autorizadas; no establece hechos curriculares ni sustituye evidencia,
reglas o veredicto pedagógico.

Ejemplos conceptuales para una eventual evaluación —no funcionalidades
prometidas—:

| Dominio | Competencia posible | Comportamiento observable a validar |
| --- | --- | --- |
| Algoritmos y estructuras de datos | Explicar y aplicar recorridos de árboles u ordenamientos. | Secuencia de estados y resultado del algoritmo para entradas dadas. |
| Bases de datos | Razonar sobre consultas, relaciones, claves y normalización. | Resultado de consultas conceptuales y detección de restricciones/inconsistencias. |
| Sistemas operativos | Analizar planificación, memoria o sincronización. | Transiciones de proceso/recurso y detección de estados inválidos bajo reglas explícitas. |
| Redes | Explicar encapsulación, rutas y protocolos. | Recorrido de paquetes/capas y resultado de decisiones de encaminamiento. |
| Matemáticas | Explorar funciones, grafos y parámetros. | Cambios de representación y propiedades calculables al variar parámetros. |

#### Dependencias, riesgos y criterios preliminares

Dependencias previas: identidad e integridad documental; ingesta y retrieval
confiables; evidencia/citas verificables; backend y frontend estabilizados;
validación del pipeline pedagógico; y resolución de los gates que resulten
aplicables al alcance futuro. La investigación de corpus V5.1.2 y cualquier
integración con V1.5 conservan sus estados y autorizaciones independientes.

Riesgos a evaluar: contenido o instrucciones no confiables en entradas
generadas; reglas o feedback incorrectos; actividad insoluble o con estados
inalcanzables; discrepancia entre fuente y visualización; JavaScript/SVG
inseguro; acceso o registro indebido de StudentState; inaccesibilidad,
rendimiento y coste; dependencia externa/mantenimiento; y confundir interacción
con evidencia de aprendizaje. Fail-closed ante validación ausente o inválida.

Una investigación o prototipo futuro deberá evaluar, sin umbrales numéricos
prejuzgados: exactitud conceptual, utilidad pedagógica demostrable,
complejidad, coste de generación/ejecución, reutilización, accesibilidad,
seguridad del contenido generado, integración con estado de aprendizaje,
rendimiento/recursos y mantenibilidad. Criterios mínimos preliminares:
objetivos y oráculo explícitos; procedencia verificable; estados y límites
validados, incluidos extremos; feedback conforme a la política; accesibilidad
y equivalente textual; ausencia de ejecución arbitraria; y evidencia de
beneficio pedagógico antes de cualquier promoción.

**Gobernanza:** no crear T21 ni ampliar T01–T20. No cambiar paquetes, gates,
prioridades operativas ni G5. Cualquier investigación, prototipo, instalación,
integración o cambio de estado requerirá autorización específica posterior.

## 12. Artefactos canónicos y referencias

Documento integral previsto:

`docs/ROADMAP_INTEGRAL_TALOS.md`

Antes de crearlo, se verificó la ausencia de un documento equivalente con autoridad suficiente. El documento nuevo está diseñado para enlazar las referencias de autoridad y las dependencias de la evolución de TALOS, sin alterar los contratos o los estados de release.

Referencias relevantes:

- [docs/PLAN_MAESTRO_CIERRE_TALOS.md](./PLAN_MAESTRO_CIERRE_TALOS.md)
- [docs/ROADMAP_V1_5_MASTER.md](./ROADMAP_V1_5_MASTER.md)
- [docs/expedientes/F2A-012-EXPEDIENTE-CANONICO.md](./expedientes/F2A-012-EXPEDIENTE-CANONICO.md)

## 13. Control de alcance de esta directiva

Autorizado:

- inspección documental de solo lectura;
- creación o actualización de la hoja de ruta integral, según autoridad;
- incorporación de referencias documentales justificadas;
- consolidación de estados, dependencias, decisiones y bloqueos;
- comparación documental antes y después.

No autorizado:

- modificar código;
- ejecutar tests, gates o benchmarks;
- modificar contratos o criterios de aceptación;
- cambiar ramas, commits, tags o referencias;
- ejecutar B06-RUN;
- iniciar P1.3;
- ejecutar reconstrucción material de bases de datos;
- tocar corpus, índices, snapshots, modelos o estado del estudiante;
- procesar documentos para ingesta local;
- instalar o integrar herramientas;
- promover artefactos a producción;
- cambiar los estados de release;
- declarar certificada TALOS V1.5.

## 14. Validación y entrega

El informe final debe incluir:

1. rama, HEAD y estado del worktree antes y después;
2. documentos de autoridad inspeccionados;
3. documento integral creado o actualizado;
4. archivos modificados y justificación de cada uno;
5. diff documental completo o resumen preciso;
6. matriz de estados de V1 y V1.5 con referencias;
7. estado de F2A-012, incluido C-03d y R9;
8. estado de GIT-03, B06-RECONSTRUCTION-SPEC, DB-0 y DB-1;
9. bloqueos de P1.2 y B06-RUN;
10. destino asignado a cada herramienta externa;
11. conflictos de autoridad encontrados y no resueltos;
12. confirmación de que no se modificó código;
13. confirmación de que no se ejecutaron tests ni gates;
14. confirmación de que no se tocaron datos, corpus, snapshots ni configuraciones protegidas;
15. diferencias entre evidencia verificada y resultados reportados.

## 15. Criterio de aceptación

La directiva queda satisfecha cuando el repositorio contiene una hoja de ruta integral inequívoca, vinculada a la documentación autorizada, que permita responder:

1. ¿Qué está certificado históricamente y qué no?
2. ¿Qué etapas de V1 siguen bloqueadas?
3. ¿Qué fases de V1.5 tienen cierres documentados?
4. ¿Qué significa exactamente el cierre focal de F2A-012?
5. ¿Por qué C-03d está cerrado como no aplicable al contrato vigente?
6. ¿Por qué R9 no autoriza crear una matriz nueva?
7. ¿Cuál es la secuencia de reconstrucción documental autorizada?
8. ¿Qué impide ejecutar B06-RUN e iniciar P1.3?
9. ¿Cómo se preservan la autoridad Git y los cambios preexistentes?
10. ¿Dónde se realizará la ingesta y bajo qué condiciones?
11. ¿Qué herramientas son candidatas para TALOS, cuáles para V2, cuáles para desarrollo y cuáles para ingesta?
12. ¿Qué evidencia y autorización hacen falta para avanzar?

Resultado esperado: una hoja de ruta integral actualizada que incorpore los logros reales, preserve las adjudicaciones, exponga las dependencias pendientes y evite que futuras sesiones o agentes reabran trabajo cerrado, inventen autoridad o adelanten fases bloqueadas.
