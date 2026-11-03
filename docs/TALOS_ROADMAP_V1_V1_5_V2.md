# Hoja de Ruta Oficial de TALOS: V1 → V1.5 → V2

**Documento Canónico de Arquitectura y Frontera de Versiones**  
**Proyecto**: TALOS (Tutor Adaptativo de Lógica y Operaciones de Seguridad)  
**Fecha de Publicación**: 2026-10-02  
**Estado**: OFICIAL / NORMATIVO (Corregido tras CP106.1)  
**Referencia de Transición**: CP104, CP105, CP106, CP106.1  

> **Mapa integral de navegación:** este documento relaciona V1, V1.5, el
> trabajo futuro del corpus y los destinos de herramientas. No sustituye los
> documentos que gobiernan estado y criterios: el
> [plan operativo de cierre V1](./PLAN_MAESTRO_CIERRE_TALOS.md) gobierna P0–P3;
> el [master metodológico V1.5](./ROADMAP_V1_5_MASTER.md) gobierna sus fases
> experimentales. Los estados resumidos en §8 son una vista fechada con sus
> límites de evidencia, no una nueva fuente de certificación.

---

## 0. Resumen Ejecutivo y Propósito

Este documento establece la arquitectura oficial, los límites conceptuales y operacionales, y la secuencia obligatoria de evolución de **TALOS** a lo largo de sus tres iteraciones canónicas:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        TALOS V1 — NÚCLEO CONGELADO                     │
│  Knowledge Components, BKT Oficial, Evaluación Determinista, RAG,     │
│  Autoridad Epistemológica, Abstención, Forensic Auditor, Socratic Pedagogy,│
│  Invariantes Certificadas de Aislamiento y ACL L3 (CP097, CP102).      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ sustrato
┌───────────────────────────────────▼────────────────────────────────────┐
│         TALOS 1.5 — PLATAFORMA Y RUNTIME (ARQUITECTURA CANDIDATA)      │
│  Memoria Longitudinal Jerárquica [P], Context Budgeting C3 [P],        │
│  Continuidad, Retrieval Fabric Lite, Dual Embeddings, Multi-Cloud USD 0,│
│  Infraestructura de Evidencia Externa [P], Presupuesto Desktop [H].    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ orquestación
┌───────────────────────────────────▼────────────────────────────────────┐
│      TALOS V2 — CUADERNO DE LABORATORIO Y PRÁCTICA (FUTURO / NO IMPL)  │
│  Observación de Práctica Externa (VMs, CTFs, IDEs, Terminal),           │
│  Evidence Processor, Pedagogical Assessor, Shadow BKT, Learning Events,│
│  Transferencia Controlada, Retención sin suplantar herramientas.       │
└────────────────────────────────────────────────────────────────────────┘
```
*(Nota de nomenclatura epistemológica: `[P]` = Propuesta arquitectónica no decidida; `[H]` = Hipótesis a medir).*

### Regla Fundamental de Frontera
> **V1.5 no reemplaza a V1. V2 no reemplaza a V1. V1 permanece siempre como el núcleo epistemológico y pedagógico del sistema.**
> Ninguna etapa posterior se implementa sobre un baseline anterior cuyo aseguramiento de calidad (*assurance*) permanezca ambiguo o incompleto.

## 8. Mapa integral de trabajo y estado observado

**Corte documental:** 2026-10-09. Esta sección integra referencias y estados
existentes; no modifica criterios de aceptación, cierres certificados ni
autoriza las etapas listadas.

### 8.1 Autoridad y precedencia

| Dominio | Documento que gobierna | Límite de este mapa |
|---|---|---|
| Estado operativo, orden y cierre de V1 | [PLAN_MAESTRO_CIERRE_TALOS.md](./PLAN_MAESTRO_CIERRE_TALOS.md) | No reemplaza sus adjudicaciones ni sus criterios. |
| Metodología, evidencia y promotion gates de V1.5 | [ROADMAP_V1_5_MASTER.md](./ROADMAP_V1_5_MASTER.md) | No promueve candidatos ni autoriza implementación. |
| Frontera de versiones V1/V1.5/V2 | Este documento y sus antecedentes | No confiere autoridad sobre los mapas operativos o metodológicos. |
| Perímetro del quality gate | [TEST_CERTIFICATION_PERIMETER.md](./TEST_CERTIFICATION_PERIMETER.md) | No se altera mediante esta hoja de ruta. |

Si dos fuentes discrepan, conservar la discrepancia con fecha y scope; no
resolverla mediante esta síntesis.

### 8.2 Tramo A — Cierre técnico V1

| Etapa | Estado para este mapa | Condición / dependencia | Evidencia y autoridad |
|---|---|---|---|
| V1 baseline | `BASELINE / CONTROL CERRADO` reportado | Preservar como control; este mapa no emite nueva certificación. | [PLAN_MAESTRO_CIERRE_TALOS.md](./PLAN_MAESTRO_CIERRE_TALOS.md) y los artefactos CP127 que ese plan cita. |
| P1.1 — terminal SSE | `COMPLETE` reportado | Preservar su cierre; no reabrir por esta integración. | Plan operativo V1, tabla P1. |
| P1.2 — quality gate | `BLOCKED — SNAPSHOT PROVENANCE` en la observación del 2026-10-09; el fallo funcional histórico sigue sin causa adjudicada | La ejecución canónica observada terminó con `exit 2` antes de pytest porque faltaban las seis variables de procedencia del snapshot. Esto no es un resultado funcional PASS/FAIL de suites ni resuelve el fallo histórico. | [TEST_CERTIFICATION_PERIMETER.md](./TEST_CERTIFICATION_PERIMETER.md), [config/test_perimeter.json](../config/test_perimeter.json), [scripts/quality_gate.py](../scripts/quality_gate.py). La salida del 2026-10-09 fue observada en la sesión y no se encontró un informe de ejecución persistido. |
| P1.3 — Python/runtime | `NOT_STARTED` | Mantener detenida hasta que P1.2 alcance su criterio de salida bajo el plan operativo. | [PLAN_MAESTRO_CIERRE_TALOS.md](./PLAN_MAESTRO_CIERRE_TALOS.md), tabla P1. |
| P1.4 — API | `NOT_STARTED` | Respetar las dependencias documentadas del plan. | Plan operativo V1, tabla P1. |
| P1.5 — E2E acotado | `NOT_STARTED` | El plan exige P1.1–P1.4, fixtures/datos, credenciales, proveedor, aislamiento y autorización explícitos. | Plan operativo V1, tabla P1. |
| P1.6 — estado pedagógico | `NOT_STARTED` | Respetar el orden P1 y no modificar StudentState real sin autorización y evidencia aplicables. | Plan operativo V1, tabla P1. |
| P2 | `DEFERRED` | Depende del cierre y aceptación de P1 conforme al plan operativo. | Plan operativo V1, sección P2/P3. |
| P3 | `DEFERRED` | Revalidación final y adjudicación; no equivale a release automático. | Plan operativo V1, sección P2/P3. |

**Discrepancia temporal que debe permanecer visible:** el plan operativo
conserva el resumen histórico `1 failed, 3100 passed, 190 warnings` y describe
un fallo pedagógico; el intento canónico observado el 2026-10-09 quedó
bloqueado antes de pytest por ausencia de provenance. Son observaciones
distintas. La segunda no demuestra que el fallo histórico se haya resuelto.
README y el master V1.5 contienen además estados fechados anteriores
(`P1 = READY / NOT_STARTED`, corte 2026-10-07). Este mapa no reescribe esas
fuentes: requiere que el dueño operativo reconcilie sus etiquetas en el
documento de autoridad cuando corresponda.

#### Bloqueo P1.2 y siguiente acción

El perfil B06 exige el scope `talos.b06.snapshot.v1` y las identidades
`knowledge_store=knowledge_store.db`, `vector_store=vector_store.db` y
`student_state=student_state.db`, además de registrar la presencia o ausencia
de `-wal`, `-shm` y `-journal` para cada base. La interfaz
[prepare_test_snapshot.py](../scripts/prepare_test_snapshot.py) consume una
captura externa ya obtenida; no la produce.

La siguiente acción operativa es resolver con un operador autorizado la fuente
de estado, el mecanismo externo de captura atómica y read-only, y la autoridad
que entregará por canal independiente el digest de `capture-attestation.json`.
No fabricar ni inferir hashes, attestations o identidades. Si la captura exige
detener escritores, obtener autorización específica antes de realizar esa
acción. Hasta resolverlo, no ejecutar `scripts/test.sh` ni pytest; P1.3 y las
etapas que dependen de P1.2 permanecen detenidas.

### 8.3 Tramo B — Fases canónicas V1.5

La secuencia metodológica es **Evidence Retrieval → Pedagogy → Student
Evaluation → Visual Explanations**. Los criterios completos, gates y
evidencias requeridas permanecen en [ROADMAP_V1_5_MASTER.md](./ROADMAP_V1_5_MASTER.md);
esta tabla no crea otros.

| Fase | Objetivo y estado | Entrada y dependencias | Criterio de aceptación, evidencia y promoción |
|---|---|---|---|
| 1 — Evidence / Retrieval | Fuente, corpus, retrieval y evidencia. `CLOSED`; `PHASE_1_PROMOTABLE=FALSE`; `PROMOTION=NOT_AUTHORIZED`; C0 retenido, según CP147. | Evidencia de fuente y baseline bajo el protocolo de fases 1A–1E del master. | Cierre documentado de subfases y adjudicación 1E; el cierre no equivale a promoción. Evidencia: CP131–CP147 y artefactos vinculados en la [sección 5](./ROADMAP_V1_5_MASTER.md). El gate 1E no autorizó promoción; no iniciar Fase 2. |
| 2 — Pedagogy / Explanation Quality | Medir calidad de intervención pedagógica. `BLOCKED / NOT_AUTHORIZED` según CP147. | Entrada condicionada a la secuencia metodológica y a promoción autorizada de Fase 1; esa condición no está satisfecha. | Benchmark contra V1, evidencia de retención/comprensión, cumplimiento C1–C5 y pacto socrático, y latencia al primer token ≤1.5 s; ver [sección 6 y gate 6G](./ROADMAP_V1_5_MASTER.md). No comenzar mientras siga bloqueada. |
| 3 — Student Evaluation | Diagnóstico confiable del aprendizaje. Fase definida; ejecución/estado actual no confirmado por la evidencia consultada. | Posterior a Fase 2; no adelantar sobre una fase previa no autorizada. | Evidencia de desempeño frente a oráculo experto, tasas de falsos positivos/negativos, robustez y determinismo; gate de promoción en [sección 7E](./ROADMAP_V1_5_MASTER.md). La fuente consultada no prueba entrada ni promoción de esta fase. |
| 4 — Visual Explanations | Medir valor pedagógico de representaciones visuales. Fase definida; ejecución/estado actual no confirmado por la evidencia consultada. | Posterior a Fase 3, según secuencia metodológica. | Comparación controlada texto vs. texto+visual y evidencia de corrección, comprensión/retención y carga cognitiva; promoción solo donde exista beneficio medible, según [sección 8D](./ROADMAP_V1_5_MASTER.md). La fuente consultada no prueba entrada ni promoción de esta fase. |

La Fase 1 incluye subfases 1A–1E y un cierre global reportado. Se preserva ese
cierre; `PROMOTION=NOT_AUTHORIZED` no se convierte en promoción. El
Ingestion Intelligence Lab y sus probes son una línea distinta: el master
registra Probe-1 cerrado con exit gate fallido y Probe-2 no iniciado/prohibido.
No los confundir con el cierre o autorización de las cuatro fases.

### 8.4 Tramo C — Corpus e ingesta en Google Colab

**Frontera operativa indicada por esta hoja de ruta:** la ingesta documental
autorizada se ejecutará en Google Colab; la máquina local se reserva para
auditar artefactos, analizar resultados y evaluar recuperación conforme a sus
contratos. Esta declaración de destino no levanta el freeze vigente.

La reconstrucción y promoción del corpus siguen `FROZEN UNTIL P3` según el
plan operativo. Cuando exista autorización específica, la secuencia prevista
es: auditar pipeline y artefactos → diseñar piloto controlado en Colab →
comparar contra baseline → auditar localmente los resultados → evaluar
recuperación, provenance y utilidad pedagógica → registrar limitaciones y
decisión → solicitar autorización separada para promover o sustituir corpus.

Las dimensiones 384, 1024 y 2560 observadas en auditorías anteriores son un
riesgo a revalidar contra contratos y evidencia vigentes, no la afirmación de
un defecto activo ni una selección de embedding.

### 8.5 Tramo D — Herramientas y destino

Estas asignaciones son **destinos de evaluación**, no adopciones ni
dependencias aprobadas:

| Herramienta / familia | Destino de evaluación | Límite |
|---|---|---|
| Laya | Candidata auxiliar para TALOS | No autoridad de evidencia, StudentState, BKT/SM-2, rúbricas ni gates; integración no autorizada. |
| OpenClaw | Investigación de orquestación para TALOS V2 | Fuera de V1/V1.5 runtime; no instalar ni integrar por esta hoja de ruta. |
| OpenQodex | Asistencia de desarrollo en VS Code | No es componente del producto; toda revisión respeta scope y permisos existentes. |
| Vela 2.0 / vLLM-SR | Candidata de investigación para el pipeline de Colab | Capacidades y ajuste al caso por verificar; no adoptar por anticipado. |
| Hyper-Extract | Candidata de investigación para extracción estructurada y relaciones/provenance en Colab | Capacidad no adjudicada; no establecer como dependencia. |
| CocoIndex Code | Candidata de investigación para búsqueda del código del pipeline en Colab | Adecuación no verificada; no crear una fuente de verdad paralela. |

No se seleccionan herramientas, se instalan dependencias ni se transfieren
datos a servicios externos como parte de la planificación.

### 8.6 Tramo E — Validación y adopción

Toda futura adopción debe conservar la secuencia de evidencia del documento
metodológico: problema concreto → baseline reproducible → experimento aislado
→ métricas y criterios previamente definidos → comparación → costes y riesgos
→ compatibilidad contractual → revisión de regresiones → decisión documentada
→ autorización de integración. El principio se mantiene:

> **El modelo propone → TALOS valida → TALOS decide.**

La ruta integral de referencia es: **cerrar V1 según su plan operativo →
continuar V1.5 según sus gates metodológicos → levantar autorizadamente el
freeze del corpus y validar en Colab → evaluar herramientas en sus destinos →
integrar solo mejoras demostradas y aprobadas → investigar V2 en su propia
frontera**. Es una relación de dependencias, no una autorización para ejecutar
las etapas.

## 9. Fuentes de estado y límites de evidencia

- [PLAN_MAESTRO_CIERRE_TALOS.md](./PLAN_MAESTRO_CIERRE_TALOS.md): estado
  operativo P0–P3 y dependencias V1.
- [ROADMAP_V1_5_MASTER.md](./ROADMAP_V1_5_MASTER.md): fases, metodología,
  criterios experimentales y decisiones de promoción V1.5.
- [TEST_CERTIFICATION_PERIMETER.md](./TEST_CERTIFICATION_PERIMETER.md):
  procedimiento y límites del quality gate.
- [Checkpoint 147](../checkpoints/147-fase-1-sintesis-global-y-cierre-canonico.md):
  cierre de Fase 1 y no autorización de promoción/Fase 2.
- [Checkpoint 154](../checkpoints/154-p1-2-b06-capture-strategy-checkpoint.md):
  bloqueo de captura B06 y gaps de evidencia.

La existencia de un estado en esta tabla no equivale a una verificación nueva.
Los informes históricos conservan el alcance y limitaciones de su ejecución;
las observaciones no persistidas se identifican como tales. Cualquier
contradicción de autoridad, alcance o temporalidad debe mantenerse visible y
adjudicarse por el documento propietario, no por inferencia de este mapa.

---

## 1. Tabla Epistemológica Canónica del Proyecto

Para evitar la confusión sistemática entre hechos existentes, mediciones, propuestas y decisiones pendientes, el estado oficial de los componentes del proyecto se clasifica formalmente como:

| Elemento | Estado Epistémico Oficial | Justificación / Checkpoint |
|---|:---:|---|
| **V1 core** | **CERTIFIED / FROZEN** | Núcleo pedagógico y algorítmico completado y certificado. |
| **C1 (Curriculum IDs / Aliases)** | **PASS / CLOSED** | Certificado materialmente en CP097. |
| **C2 (Source Roles / ACL L3)** | **PASS / CLOSED** | Certificado materialmente en CP102 (99 relaciones). |
| **C3 (Hard Context Ceiling)** | **AUDITED / BLOCKED** | Auditado en CP103 y CP106; bloqueado por decisiones D_C3_1 a D_C3_3. |
| **C4 (Multi-Curriculum Isolation)** | **PARTIAL / PENDING** | Clasificación corregida en CP095; pendiente de certificación CP107. |
| **C5 (Abstention & Trust Gate)** | **BLOCKED / PENDING** | Bloqueador formal de Gate B; previsto CP108. |
| **CP104 archaeology** | **COMPLETED** | Arqueología de memoria, embeddings y herramientas. |
| **CP105 archaeology** | **COMPLETED** | Arqueología de frontera V1.5 → V2 e inventario de capacidades. |
| **CP106 C3 audit** | **COMPLETED** | Call-graph end-to-end y clasificación de fallbacks. |
| **V1.5 architecture** | **NOT YET DECIDED** | Área de evolución prevista / espacio de diseño no adjudicado. |
| **V1.5 implementation** | **NOT STARTED** | Prohibido iniciar hasta cerrar el assurance de V1 (Gate B). |
| **V2 architecture** | **CONCEPTUAL** | Principios y ciclo de vida diseñados teóricamente. |
| **V2 implementation** | **NOT STARTED** | Futuro; posterior a V1.5. |
| **Límite de 2.2 GB RAM** | **UNAPPROVED HYPOTHESIS** | Hipótesis previa no aprobada; sujeta a medición empírica. |
| **Layered context quotas** | **PROPOSAL** | Opción C propuesta para D_C3_1; requiere decisión humana. |
| **Hierarchical pruning** | **PROPOSAL** | Opción A propuesta para D_C3_2; requiere decisión humana. |
| **Exact tokenization method** | **PENDING DECISION** | Método de medición D_C3_3 sujeto a adjudicación humana. |

---

## 2. TALOS V1 — El Núcleo Epistémico y Pedagógico (Frozen Core)

### 2.1. Propósito
TALOS V1 resuelve el problema fundamental del modelado de conocimiento y la tutoría socrática estricta en dominios técnicos de alta rigurosidad (ciberseguridad, programación de sistemas y arquitectura de computadoras). Establece la cadena de causalidad pedagógica determinista:

```text
Knowledge Base (Corpus Autorizado)
        ↓
Knowledge Components (KCs atómicos y formalizados)
        ↓
Retrieval Determinista (FTS5 BM25 + Reranker ONNX)
        ↓
Evidence Assembly (Allowlist L3 + Filtrado Anti-Fuga)
        ↓
Assessment Determinista (Rúbricas Hoare, 0 LLM en BKT)
        ↓
Student State (Persistencia relacional en SQLite)
        ↓
BKT / Retention (Actualización probabilística p_L + SM-2)
        ↓
Pedagogical Response (Andamiaje socrático, fases conceptuales)
```

### 2.2. Componentes Incluidos en el Core V1
El núcleo congelado de V1 comprende:
1. **Catálogo Canónico de Knowledge Components**: Descomposición formal de habilidades atómicas (`notebook_kc_catalog.json`).
2. **Bayesian Knowledge Tracing (BKT) Oficial**: Fórmulas probabilísticas exactas ($p(L_0), p(T), p(S), p(G)$) aplicadas de forma determinista para computar la maestría del estudiante.
3. **Spaced Repetition (SM-2)**: Algoritmo de intervalos óptimos de revisión y factores de facilidad.
4. **Student State Relacional**: Esquema relacional de trazabilidad de estados y fallas en `student_state.db`.
5. **RAG Epistémico de Alta Fidelidad**: Búsqueda léxica indexada (FTS5) combinada con reranking neural local INT8 (`models/reranker/model.onnx`).
6. **Validación Epistémica y Abstención**: Detección de consultas fuera de alcance o carentes de evidencia documental, activando respuestas de abstención pedagógica sin alucinación (*fail-closed*).
7. **Forensic Auditor y Trazabilidad**: Registro inmutable de citas, orígenes documentales y justificaciones.
8. **Andamiaje Socrático y Fading**: Reglas de respuesta que proporcionan pistas escalonadas sin entregar la solución directa (*anti-solution leakage*).
9. **Autoridad Normativa y ACL L3**: Aislamiento formal de fuentes curriculares mediante el manifiesto de autorización (`config/l3_authorization_manifest.json`), blindado a nivel de búsqueda, expansión y ensamblaje (CP101/CP102).
10. **Dynamic Cognitive Profile**: Perfil del estudiante inferido a partir de su historial de maestría y bloqueos conceptuales.

### 2.3. Estado Canónico
```text
ESTADO: V1 CORE = CERTIFIED / FROZEN
```
El núcleo conceptual y algorítmico de V1 está **terminado**. No se encuentra en desarrollo activo ni sujeto a rediseños.

### 2.4. Cierre de Assurance de V1 (Gate B)
Los trabajos en curso sobre V1 no corresponden a la creación de nuevas funcionalidades, sino al **cierre formal de aseguramiento de calidad (Assurance Closure)** bajo los cinco criterios de Gate B:

| Criterio Gate B | Descripción Normativa | Estado Oficial | Checkpoint de Referencia |
|---|---|:---:|---|
| **C1** | Reconciliación estricta de IDs curriculares, aliases y namespaces | **PASS / CLOSED** | CP096, CP097 |
| **C2** | Roles de fuentes, allowlist técnica y ACL efectiva L3 | **PASS / CLOSED** | CP098, CP101, CP102 |
| **C3** | Hard Context Ceiling terminal por llamada al backend LLM | **BLOCKED / ASSURANCE BLOCKER** | CP103, CP104, CP106 |
| **C4** | Aislamiento multi-curricular en ejecución concurrente | **PARTIAL / EXISTING EVIDENCE** | CP095, CP107 (previsto) |
| **C5** | Compuerta de abstención estricta y confianza epistémica | **BLOCKED / ASSURANCE BLOCKER** | CP108 (previsto) |

> **Nota Crítica de Alcance:** Cerrar C3, C4 y C5 no significa refactorizar V1; significa certificar formalmente que el runtime de V1 cumple rigurosamente con sus garantías de seguridad, presupuesto y aislamiento.

---

## 3. TALOS 1.5 — Área de Evolución Prevista / Arquitectura Candidata

### 3.1. Definición Epistemológica de TALOS 1.5
> **TALOS 1.5 representa la siguiente etapa prevista del proyecto: una capa de infraestructura cognitiva y runtime destinada a permitir que el core V1 opere longitudinalmente con memoria, contexto, retrieval, providers, herramientas y gestión de recursos más coherentes. Sus componentes concretos todavía deben pasar por investigación, decisión y validación.**

TALOS 1.5 **no es una arquitectura ya decidida** ni cerrada, sino un espacio de diseño propuesto. Tampoco es TALOS V2, pues no incorpora la observabilidad de prácticas externas ni laboratorios de seguridad.

### 3.2. Clasificación Explícita de Elementos de TALOS 1.5

| Elemento | Clasificación Epistémica | Estado Actual |
|---|---|---|
| **Memoria longitudinal** | DIRECCIÓN DE DISEÑO / PENDING VALIDATION | En investigación tras CP104 |
| **Memoria jerárquica** | PROPUESTA | Modelo conceptual propuesto en CP105 |
| **Contextual Memory Bubble** | CONCEPTO PROPUESTO | Mecanismo hipotético de activación de contexto |
| **Context budgeting** | NECESIDAD OBSERVADA + SOLUCIÓN PENDIENTE | Diagnóstico demostrado en CP103/CP106 |
| **Budget Allocator** | PROPUESTA | Interceptor pre-LLM propuesto, no implementado |
| **Multi-provider fallback** | CAPACIDAD EXISTENTE PARCIAL + EVOLUCIÓN PROPUESTA | `MultiFallbackBackend` activo; mejoras propuestas |
| **Tool → Evidence → Context → LLM** | PRINCIPIO ARQUITECTÓNICO PROPUESTO | Frontera conceptual para ingesta de datos |
| **Curriculum espiral transversal** | DIRECCIÓN PEDAGÓGICA | Conexión con catálogo formal de KCs propuesta |
| **Practice observability** | DIRECCIÓN V2 / PREPARACIÓN 1.5 | Relevamiento preliminar en CP105 |
| **Desktop resource budget** | HIPÓTESIS A MEDIR | Meta cualitativa de baja interferencia |
| **Límite de 2.2 GB RAM** | NO APROBADO / UNAPPROVED HYPOTHESIS | Cifra propuesta en CP105 sin adjudicación humana |
| **Valores concretos de CPU/RAM** | NO APROBADOS | Pendientes de benchmark en escenario real |
| **Proveedores concretos / cuotas** | SUJETOS A VERIFICACIÓN | Variaciones de Free Tier de proveedores cloud |
| **Arquitectura final V1.5** | NO DECIDIDA | Requiere adjudicación del paquete D105-01 a D105-08 |

### 3.3. Áreas de Plataforma Propuestas (Espacio de Diseño Candidato)

#### A. Memoria Longitudinal (Propuesta)
- Exploración de estructuración jerárquica de preconceptos, brechas cognitivas y fortalezas demostradas.
- Resúmenes dinámicos de sesión (*Session Digests*) que condensen la trayectoria sin almacenar transcripciones brutas.
- Concepto de activación contextual con decaimiento temporal y descarte de ruido irrelevante.

#### B. Gestión de Contexto (Necesidad Observada — Solución Propuesta)
- Necesidad demostrada empíricamente: imposición de un límite físico terminal al prompt despachado al LLM.
- Propuesta de Budget Allocator para distribuir cuotas de tokens entre directivas del sistema, evidencia RAG, memoria reciente y query del usuario.
- Algoritmos de poda jerárquica o fail-closed sujetos a adjudicación humana.

#### C. Estructura Curricular Longitudinal (Dirección Pedagógica)
- Exploración de la jerarquía: Fase $\rightarrow$ Unidad $\rightarrow$ Tema $\rightarrow$ Subtema $\rightarrow$ KC.
- Modelado de prerrequisitos duros y blandos con cálculo dinámico de frontera de aprendizaje.

#### D. Sustrato de Retrieval y Embeddings (Capacidad Parcial Existente)
- Coexistencia actual de FTS5 BM25 de latencia ultra-baja y embeddings densos ONNX locales (384d INT8).
- Evaluación futura sobre la conveniencia de regenerar el vector store a 384d vs mantener FTS5 principal.

#### E. Enrutamiento Multi-Cloud USD 0 y Resiliencia (Capacidad Parcial Existente)
- Router existente con circuit breakers thread-safe a través de capas gratuitas (*Free Tiers*).
- Degradación determinista offline (`OfflinePedagogicalBackend`) activa como salvaguarda final.

#### F. Ingesta de Evidencia de Herramientas (Principio Propuesto)
- Principio propuesto:
  $$\text{Herramienta Externa} \xrightarrow{\text{salida bruta}} \text{Evidence Filter} \xrightarrow{\text{hechos relevantes}} \text{Context Budget Allocator} \xrightarrow{} \text{LLM}$$
- Invariante anti-agente: TALOS no ejecuta acciones destructivas ni resuelve retos por el estudiante.

#### G. Huella de Recursos en el Desktop (Hipótesis a Medir)
- **Principio Rector**: TALOS debe aspirar a tener una huella de recursos suficientemente baja como para no interferir con el entorno de estudio y trabajo del usuario (máquinas virtuales, navegadores, IDEs).
- **Estado de Cifras Cuantitativas**: Cualquier límite cuantitativo previo (como la cifra hipotética de 2.2 GB RAM o porcentajes fijos de CPU) constituye una **hipótesis no aprobada** (`UNAPPROVED HYPOTHESIS`). Los límites cuantitativos finales deberán surgir de mediciones empíricas formales y de una decisión humana posterior.

---

## 4. TALOS V2 — El Cuaderno de Laboratorio y Aprendizaje Práctico

### 4.1. Definición y Estado
```text
ESTADO: V2 = FUTURE / NOT IMPLEMENTED
```
TALOS V2 representa la capa de **observabilidad y evaluación del aprendizaje práctico**. Su propósito es transformar la experiencia técnica externa (ejecución de comandos, retos en VMs, explotación controlada en CTFs, análisis forense) en evidencia pedagógica estructurada, evaluable socráticamente y transferible, sin suplantar el rol de las herramientas del profesional de seguridad.

Todas sus hipótesis arquitectónicas deberán validarse formalmente antes de incorporarse al sistema.

### 4.2. Principios Conceptuales de V2
1. **Orquestar, no competir**: TALOS no sustituye a la terminal, al debugger ni al hypervisor; observa las interacciones y guía la reflexión pedagógica.
2. **Evidencia sobre actividad**: Ejecutar 100 comandos no demuestra aprendizaje; la evidencia radica en la comprensión causal de las transiciones de estado del sistema auditado.
3. **Mínima fricción de captura**: La recolección de evidencia no debe interrumpir el flujo de concentración técnica del estudiante.
4. **Shadow BKT**: Ninguna observación práctica cruda muta directamente el BKT oficial de V1; se procesa primero en un espacio de sombra experimental hasta demostrar retención y consistencia.
5. **Validación previa a la complejidad**: Toda nueva instrumentación debe pasar por compuertas criptográficas de integridad y auditoría humana antes de ser integrada al modelo.

### 4.3. Flujo Conceptual Propuesto para Laboratorios

```text
Selección del Desafío (Lab Registry / Catalog)
        ↓
Fase Pre-Lab (Activación de conceptos previos vía Core V1)
        ↓
Práctica Externa (VMs, CTF, Terminal, Scripts, IDE)
        ↓
Captura de Evidencia (Telemetry Ingestion: CLI, logs, artifacts SHA-256)
        ↓
Procesamiento de Evidencia (Evidence Filter / Sanitizer / Deduplicator)
        ↓
Evaluación Socrática Post-Lab (Cuestionamiento causal de decisiones)
        ↓
Actualización en Shadow BKT (Modelado provisional de competencia)
        ↓
Pruebas de Transferencia (Variaciones de contexto para validar solidez)
        ↓
Promoción al BKT Oficial de V1 (Certificación de maestría duradera)
```

---

## 5. Fronteras Canónicas y Clasificación de Responsabilidades

| Dimensión | TALOS V1 (Core Epistémico Congelado) | TALOS 1.5 (Plataforma y Runtime — Candidata) | TALOS V2 (Práctica y Laboratorio — Futuro) |
|---|---|---|---|
| **Modelo Cognitivo** | BKT Oficial determinista, catálogo KC, SM-2 | Perfil dinámico de fortalezas y brechas longitudinales [P] | Shadow BKT, matrices de competencia práctica [P] |
| **Memoria** | Registros relacionales en SQLite (`bkt_states`) | Memoria longitudinal jerárquica y resúmenes rodantes [P] | Bitácora de proyectos, errores causales de terminal [P] |
| **Presupuesto Contextual**| Techo declarativo por modo de respuesta | **Hard-Ceiling C3 terminal y Budget Allocator** [P] | Poda y compresión de telemetría de herramientas [P] |
| **Espacio Vectorial / RAG**| FTS5 BM25 + Reranker ONNX + Allowlist L3 | Dual runtime ONNX/FTS5 y caché matricial LRU [P] | RAG sobre documentación técnica externa y write-ups [P] |
| **Despacho a Modelos** | Prompts de fase congelados, evaluación sin LLM | Multi-Cloud Router USD 0, Circuit Breakers | Enrutamiento por complejidad de tarea técnica [P] |
| **Práctica de Seguridad** | Conceptos teóricos y verificación analítica | Ingesta segura de artefactos en reposo [P] | Observabilidad de terminal, grading de flags SHA-256 [P] |
| **Garantía Principal** | Verdad epistémica y rigor metodológico | Estabilidad operacional y presupuesto acotado [P] | Causalidad práctica y transferencia demostrada [P] |

*(Nomenclatura: `[P]` = Propuesta sujeta a decisión humana y validación).*

---

## 6. Regla Canónica de Transición y Secuencia de Checkpoints

Queda formalmente establecido el siguiente orden cronológico y metodológico:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ PASO 1: CIERRE FORMAL DE ASSURANCE DE TALOS V1 (GATE B)                │
│                                                                        │
│   CP106: Auditoría de Readiness y Preparación de Decisión de C3        │
│     ↓                                                                  │
│   Decisión Humana C3 (Adjudicación de D_C3_1, D_C3_2, D_C3_3)          │
│     ↓                                                                  │
│   CP107: Auditoría y Certificación de C4 (Multi-Curriculum Isolation)  │
│     ↓                                                                  │
│   CP108: Auditoría y Certificación de C5 (Abstention & Trust Gate)     │
│     ↓                                                                  │
│   CP109: Cierre Definitivo de Gate B y Congelamiento de Release V1     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PASO 2: DISEÑO FORMAL Y ARQUITECTURA DE TALOS 1.5                      │
│                                                                        │
│   Adjudicación del Paquete de Decisiones Humanas D105-01 a D105-08     │
│     ↓                                                                  │
│   Especificación Formal de Contratos de Plataforma (Budget / Memoria)  │
│     ↓                                                                  │
│   Implementación de Componentes Aprobados y Medición Empírica Desktop  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ PASO 3: DESARROLLO DEL CUADERNO DE LABORATORIO TALOS V2                │
│                                                                        │
│   Diseño formal del Lab Registry y Normalizador de Telemetría Externa │
│     ↓                                                                  │
│   Implementación de Shadow BKT y Validación de Transferencia Práctica  │
└────────────────────────────────────────────────────────────────────────┘
```

> **Secuencia Operativa Inmutable**: No se implementa TALOS 1.5 ni TALOS V2 hasta que el Gate B de TALOS V1 esté completamente cerrado y certificado.

---

## 7. Metodología de Ingeniería Obligatoria

Toda evolución dentro del repositorio TALOS debe ceñirse estrictamente al estándar:

$$\text{OBSERVE} \longrightarrow \text{MEASURE} \longrightarrow \text{CORRELATE} \longrightarrow \text{CLASSIFY} \longrightarrow \text{HUMAN DECISION} \longrightarrow \text{FUTURE CHANGE}$$

Queda expresamente prohibido implementar modificaciones basadas en apreciaciones subjetivas ("esto parece mejor") sin haber completado la fase probatoria previa ni contar con la decisión humana correspondiente.

Toda afirmación técnica, arquitectura o especificación debe acompañarse de su clasificación epistémica:
- **FACT / EXISTING**: Comprobado materialmente en el código fuente o base de datos actual.
- **MEASURED**: Cuantificado con instrumental empírico reproducible (bytes, tokens, milisegundos).
- **INFERRED**: Deducido lógicamente a partir de la correlación de hechos observados.
- **PROPOSED**: Diseño arquitectónico sujeto a análisis.
- **HUMAN DECISION**: Adjudicación soberana exclusiva del propietario del proyecto.
- **IMPLEMENTED**: Código introducido bajo control de versiones cumpliendo contratos Hoare.
- **VALIDATED**: Certificado mediante pruebas de regresión adversariales reproducibles.
