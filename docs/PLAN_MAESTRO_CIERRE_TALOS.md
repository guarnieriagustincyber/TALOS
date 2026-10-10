# Mapa maestro de estado y camino restante de TALOS

**Estado del plan:** hoja de ruta integrada; evidencia y decisiones detalladas
permanecen en sus documentos fuente
**Actualizado:** 2026-10-01 (mapa CP073)
**Snapshot observado:** `HEAD=f81134fc2293916210d53c8065f3a0049e52b0b4`;
worktree con cambios preexistentes tracked y untracked. Este checkout no es
una baseline PRE limpia ni una certificación del estado completo.

> **Documento maestro vigente.** Este archivo ya era la vista integrada
> enlazada desde README; se actualiza aquí en vez de crear un segundo master
> con estado potencialmente divergente. La sección “Mapa maestro CP073”
> contiene la síntesis vigente al 2026-10-01 e integra CP050–CP072. Las
> secciones anteriores con corte 2026-09-30 se conservan como registro del
> estado de ese corte y no prevalecen ante una actualización posterior.

## Propósito y regla de lectura

Esta es la vista única para saber **dónde está TALOS y en qué orden cerrar lo
abierto**. No reemplaza especificaciones, gates ni evidencia histórica enlazada.
Los estados del mapa CP073 reflejan la documentación disponible al corte
indicado, no una nueva ejecución de código. Una pieza existente en código no
equivale a una propiedad aceptada, y una prueba con mocks no equivale a
integración real.

La estrategia es **verificar y cerrar fronteras antes de ampliar o purificar**:

```text
B1-B observado → mini-arqueología → B1-R TECHNICAL PASS
→ A-PRE-0 SPECIFIED → preflight REVIEW REQUIRED → cierre de precondiciones
→ autorización explícita → A-PRE-1
→ identidad/scope (Gate B) → memoria/estado/procedencia (Gate C)
→ decisión de contrato SSE y cierre F6 (Gate D)
→ contexto/dominio B2 → retrieval B3 → pipeline con provider falso
→ HTTP/SSE → React aislado → regresión PRE→POST
→ evaluación pedagógica PED-F7 → experimentos independientes → purificación decidida
```

Conservar los cambios locales existentes. No ejecutar proveedores, corpus,
índices, benchmarks comparativos, migraciones ni operaciones de datos protegidos
sin sus gates y autorización específicos.

## Qué ya existe en TALOS y qué falta demostrar

El texto de referencia sobre harness/context/evals/guardrails/memory es útil
como **marco de auditoría**, no como requerimiento para instalar frameworks o
crear nuevas capacidades. El repositorio ya contiene:

| Capacidad presente en el proyecto | Evidencia en código | Límite actual |
|---|---|---|
| Contexto, selección de evidencia y retrieval | [`ContextPack`](../src/study_engine/context/context_pack.py), [`RetrievalFabric`](../src/study_engine/retrieval/fabric.py), [`chat.py`](../src/study_engine/web/routes/chat.py) | Hay pruebas aisladas y un caso de retrieval con fixture; no está aceptada toda la ruta real multi-cuaderno ni su comportamiento productivo. |
| Política pedagógica, perfiles y protección de evaluación | [`structured_pipeline.py`](../src/study_engine/pedagogy/structured_pipeline.py), [`solution_protection.py`](../src/study_engine/pedagogy/solution_protection.py), [`notebook_kc_catalog.json`](../config/notebook_kc_catalog.json) | H1–H3 y protecciones centrales tienen fixes/pruebas locales; identidad, ACL y aceptación integrada siguen parciales. |
| Memoria de sesión/estudiante y estado BKT | [`SessionMemoryManager`](../src/study_engine/memory/session_memory.py), [`pedagogy/memory/store.py`](../src/study_engine/pedagogy/memory/store.py), [`BKTTracker`](../src/study_engine/student/bkt_tracker.py) | Falta aceptación de aislamiento/procedencia, contaminación y no mutación sin evidencia evaluativa en los casos de F5. |
| Guardas, citas y auditoría | [`security/`](../src/study_engine/security), [`audit/`](../src/study_engine/audit), [`evidence/`](../src/study_engine/evidence) | La presencia de controles no certifica cada camino; quedan pruebas de fallos, límites y rutas de integración. |
| Tests, harnesses y evaluación | [`config/test_perimeter.json`](../config/test_perimeter.json), [`scripts/quality_gate.py`](../scripts/quality_gate.py), `tests/`, benchmark y herramientas Gate 2 | Conteos/documentos de perímetro discrepan; los resultados históricos no son una corrida actual; no hay repetición comparativa autorizada de TALOS vs NotebookLM. |
| Streaming HTTP/SSE y cliente | [`chat.py`](../src/study_engine/web/routes/chat.py), [`chatService.ts`](../kasiu-lab/ui/src/services/chatService.ts) | B1-A/B observó la ruta con dependencias sintéticas. No probó lifespan normal, pipeline/proveedor real ni React conectado a FastAPI. |

**Conclusión sobre el texto adjunto:** no abre una iniciativa o capa transversal
nueva. Sus ideas de contexto necesario y suficiente, aislamiento de autoridad,
verificación, telemetría, límites y evals quedan absorbidas como lentes al
revisar los gates existentes. No añadir otro motor de memoria, guardrails,
agentes, orquestación ni compresión; demostrar primero las piezas que ya
existen.

**Invariante de evidencia:** la existencia de código no certifica una
capacidad; una prueba aislada no certifica integración; una regresión no
certifica producción; y una métrica estática no justifica una eliminación.

### Fixes principales ya realizados

| Hallazgo/línea | Fix ya documentado | Lo que el fix no cierra |
|---|---|---|
| TUT-03 / evaluaciones protegidas | Política de solución completa en práctica no protegida; protección runtime de evaluación activa, fail-closed si falta solucionario y retención de tokens para revisión. | Mismo contrato en TutorPolicy/Study Loop, estado entre workers y detección semántica de paráfrasis. |
| H1–H3 / perfiles | Fallback curricular neutral, selección por identidad exacta, corrección del rótulo `fadena-std`; pruebas de prompt y una integración de fuentes con fixture. | Reconciliación de identidad/fuentes/ACL efectiva y aceptación multi-cuaderno completa. |
| PED-F1…F4 | Contrato por turno, modos/intención, rigor contextual y selección de formato/código implementados con pruebas locales. | Cumplimiento semántico general de un proveedor real y validez en todos los currículos. |
| PED-F5 | Procedencia SSE, referencias de seguimiento y discrepancias de evidencia ampliadas; historial y memoria tienen piezas implementadas. | Criterios completos de scope, memoria y no mutación del estado pedagógico. |
| Consumidor SSE | El commit `b12e340` hace fallar explícitamente ante `truncated`, `stream_aborted` y EOF sin `phase_complete`; hay regresiones Playwright con API/SSE mock. | No valida los eventos terminales que produce FastAPI; B1-B confirma que abstención/clarificación no se interpretan, y truncation requiere acordar semántica. |
| Higiene A-3/A-5 | Métricas de throughput separadas, errores BKT visibles en CLI y mapa de repositorio actualizado. | No cierra certificación A-1/A-2 ni aceptación funcional de F5/F6. |

## Snapshot integrado al 2026-09-30 (histórico)

Este corte precede CP071–CP073. Para el estado vigente, utilizar “Mapa
maestro CP073 — corte documental 2026-10-01” al final de este archivo. Se
conserva esta sección para que no se pierda la secuencia histórica.

| Línea | Estado actual | Lo que falta para cerrar |
|---|---|---|
| Comparación TALOS vs NotebookLM / PED-F0 | **F0 completada como línea de base e instrumento.** De los registros: TALOS tiene 13 respuestas completas localizables, 1 alineación incierta, 2 parciales, 3 incidencias/demoras y 1 no localizable; NotebookLM conserva respuesta completa en los 20 ítems. | Es integridad del registro, no puntuación de calidad. Fuentes/versiones no están plenamente emparejadas y NotebookLM usó prompt pedagógico propio; no demuestra superioridad causal ni aprendizaje. Preparar evaluación nueva y versionada sin reusar transcripts como oráculo. |
| PED-F1 a PED-F4-formato | **Implementadas y con pruebas locales**, con límites sobre proveedores reales y corrección semántica. | La aceptación multi-currículo depende del Gate B y, después, de PED-F7. |
| Gate 1 / política protegida | **Completado parcialmente.** Precedencia práctica no protegida vs. evaluación activa y guarda inicial de chat implementadas. | Alinear TutorPolicy/Study Loop, ciclo de estado entre workers y límites del detector textual; no presentar coincidencia textual como protección semántica completa. |
| ESTAB-G2 / Gate B — perfil por cuaderno | **PARCIAL.** H1–H3 corregidos en su núcleo; existen pruebas de identidad exacta y una prueba integrada de retrieval/ACL con fixture para `fadena-std`. | Reconciliar IDs/aliases, currículos, fuentes y autoridad; confirmar programa oficial de `fadena-std`; ampliar la evidencia integrada sin escribir SQLite ni ampliar ACL por inferencia. |
| PED-F5 / Gate C — fuentes, memoria y continuidad | **Implementación amplia; aceptación abierta.** | Probar historial, memoria, fuentes, precedencia del pedido actual, referencias ambiguas, intentos parciales/ausentes/de otro scope y no mutación indebida de BKT, con stores aislados. |
| PED-F6 / Gate D — streaming y fiabilidad | **Parcial/no aceptada.** B0, B0.5 y B1-A/B están cerrados en el alcance observado. B1-R obtuvo `TECHNICAL PASS` en el contrato objetivo; no es F6 PASS. | A-PRE-0 está especificada, pero A-PRE-1 no está autorizada. Después de Gate B/C, adjudicar contrato terminal y verificar pipeline→HTTP/SSE→cliente. No llamar a esto “backend chat PASS”. |
| PED-F7 / Gate E — evaluación multi-currículo | **Pendiente.** | Congelar matriz de currículos/intenciones, corpus/fuentes permitidos, rúbrica y umbrales; evaluar primero calidad de respuestas. Aprendizaje/retención requiere un protocolo experimental separado. |
| A-1/A-2/A-6 — certificación y dependencias | **A-PRE-0 especificada; preflight `REVIEW REQUIRED`; baseline PRE inexistente.** CPython 3.10.21 + uv 0.12.20 resolvió e instaló los 61 paquetes en venv temporal; `uv pip check` y dependency imports pasaron. | Harness conecta bubblewrap, strace, collector, `result.json` y verifier independiente; fixtures OS pasan para filesystem, red, SQLite y procesos. El host bloquea ptrace (`PTRACE_TRACEME: Operation not permitted`), así que el preflight impide lanzar el gate y el builder fuerza `ERROR`. Snapshot externo regenerado y verificado; el lock compartido de verificación/E5 permanece sin cambios. No tocar `.venv`. |
| A-3/A-4/A-5 | **Implementados según el seguimiento de auditoría.** Métrica QPS separa intentos y éxitos; CLI distingue BKT ausente de error de lectura; README contiene mapa actualizado. | Conservar sus evidencias focalizadas; no reabrirlos sin nuevo hallazgo. |
| BENCH-G2 — scopes/qrels históricos | **Separado, pausado y no canónico.** Hay generador/validadores y fixtures acotadas; la cola histórica reporta consultas y qrels pendientes de adjudicación. | Aceptar decisiones humanas por scope y cada qrel; luego preflight y piloto autorizado. No correr el set completo de 420 ni retrieval ampliado en el estado actual. |
| E5 / Qwen / blind pool | **E5 bloqueado para runtime; Qwen bloqueado por provenance/runtime; blind pool pendiente.** Path A (lock Python 3.10) es la resolución normativa inicial; el `.venv` Python 3.12 no coincide. | Primero viabilidad read-only de Path A; ambiente, harness, benchmark y blind pool requieren gates/autorizaciones separadas. No usar el entorno actual como runtime E5. |
| Reality Audit / purificación | **Observación y medición amplias; decisiones de remediación mayormente pendientes.** B1-B encontró incompatibilidad terminal probable/observable en el slice sintético; clones, complejidad y Vulture siguen como candidatos. | Corregir solo después de aceptación de contratos y baseline; no eliminar código ni refactorizar por métricas estáticas. |

### Estado de A-PRE-0 y siguiente gate

**B1-B ya está terminado como observación experimental acotada.** No queda
pendiente repetir esa observación ni se ha decidido el contrato normativo. La
mini-arqueología está hecha y la validación objetiva B1-R quedó cerrada con
`TECHNICAL PASS`: 10 casos, tres repeticiones semánticamente idénticas por
caso, 9 probes negativos rechazados, 16 mutaciones de criterios detectadas,
cero accesos prohibidos y cero llamadas externas observadas. El contrato está
en [B1R_ACCEPTANCE_CONTRACT.md](./B1R_ACCEPTANCE_CONTRACT.md); el consumidor UI
permanece source-traced, no runtime-tested.

1. **A-PRE-0 está especificada, no ejecutada.** La definición de identidad,
   perímetro, dependencias, artefactos, salidas y comparabilidad está en
   [A_PRE_0_BASELINE_SPEC.md](./A_PRE_0_BASELINE_SPEC.md). La cifra histórica
   446 se reconcilió: 446 módulos ejecutables más el helper `support-only` en
   `99bd754`, cuatro módulos ejecutables añadidos hasta `b12e340`, y dos
   módulos B1-R presentes en el árbol no comprometido observado.
2. **El preflight A-PRE-0 continúa `REVIEW REQUIRED / NOT READY`.** En Python
   3.10.21 + uv 0.12.20 se resolvieron e instalaron los 61 paquetes en un venv
   temporal; `uv pip check` y los imports de dependencias pasaron. No se
   importó TALOS ni se recolectaron suites. El perímetro cuadra: 25 suites,
   456 archivos (440 required, 13 qualification-required, 2 optional, 1
   support-only). `scripts/test.sh` seleccionaría el `.venv` 3.12, por lo que
   el gate eventual invocará `quality_gate.py` desde el intérprete aislado. Ya
   existe un snapshot-overlay externo limpio, hijo del HEAD identificado, con
   manifiesto verificable y object store autocontenido (`git fsck` sin
   alternates); no limpia ni modifica el checkout fuente.
3. **Pre-screen de efectos:** el último barrido medido, sobre un snapshot de
   454 módulos, marcó 100 candidatos; los módulos A-PRE añadidos después no
   están incluidos en ese conteo. Los 99 candidatos anteriores no quedan
   adjudicados por su presencia de mocks/tempfiles y el barrido tampoco cubre
   efectos indirectos. El observer Python está conectado de modo opt-in al
   gate y cualificado con seis fixtures. Se añadieron bubblewrap (filesystem
   read-only y red aislada), un runner que agrega el collector a `result.json`
   y un verifier independiente. Seis fixtures de harness validan controles
   OS y `ERROR` cuando el tracing es incompleto. En este host strace no logra
   adjuntarse (`PTRACE_TRACEME: Operation not permitted`), por lo que la
   cobertura nativa sigue incompleta.
   No modificar `.venv`, `requirements.lock`, datos E5/Qwen,
   bases/corpus/índices protegidos ni blind pool.
4. **Antes de A-PRE-1**: habilitar syscall tracing verificable en un host que
   permita ptrace, resolver la cobertura syscall residual y regenerar el
   snapshot externo. El harness OS y el enlace collector→`result.json` ya
   están conectados, pero el artefacto queda `ERROR` mientras falte cobertura.
   La adjudicación de efectos reales pertenece a A-PRE-1; no ejecutar TALOS
   imports, colección o suites por adelantado para evitar una autorización
   circular.
5. **A-PRE-1 sigue `PENDING / NOT AUTHORIZED`.** Solo después del preflight y
   una autorización operativa explícita podrá ejecutar el perfil acordado y
   guardar statuses, skips, warnings, errores, duraciones, artefactos y hashes
   fuera del checkout.
6. Solo después de PRE aceptado, avanzar a **Gate B** read-only para identidad,
   scope, currículo, fuentes y autoridad; luego **Gate C/F5** con stores
   aislados. La adjudicación formal del contrato SSE y el cierre **Gate D/F6**
   vienen después de esas fronteras.

#### Alcance y matriz de observación B1-R

B1-R no es benchmark de rendimiento, E2E de producción ni adjudicación del
contrato. Está versionado en [test_b1_route_repeatability.py](../tests/audit/test_b1_route_repeatability.py)
y mantiene el boundary sintético: CWD temporal, variables de
credenciales limpiadas, startup/lifespan fail-fast, container/context/pipeline
falsos y prohibición fail-fast de SQLite, acceso a datos/corpus/modelos,
escrituras en el repo, sockets de red, subprocess y threads. No se copian
fixtures productivas; no se usa `AppContainer` real ni Playwright.

| Caso | Observar (sin adjudicar semántica aún) |
|---|---|
| Éxito normal / error sintético | HTTP status, eventos ordenados, cierre y excepción/evento final |
| Abstención / clarificación | Ruta activada, eventos, EOF y presencia/ausencia de `phase_complete` |
| Truncamiento | Orden de `truncated` respecto de auditoría, manifiesto, finalización y cierre |
| Cancelación/abort | Evento, cancelación/exception y cierre; separar cancelación simulada de disconnect real |
| EOF sin terminal / terminal duplicado | Secuencia observada y resultado del observer/consumidor |
| Error después de tokens / cierre abrupto | Texto/eventos parciales, estado final, excepción y cierre |

Cada observación registra caso, eventos/orden, último evento, `phase_complete`,
HTTP status, cierre, excepción sintética, observer UI source-traced y guardas.
Los 10 escenarios se ejecutan tres veces; normalizar secuencia semántica, no
medir throughput. El test pasa técnicamente con trazas coincidentes y cero accesos prohibidos; el
verificador independiente dio `TECHNICAL PASS`. Ese resultado no certifica F6,
dominio, producción ni integración UI.

No hay runner de unit tests existente para el consumidor `chatService`; por eso
su interpretación queda registrada como trazado estático separado del contrato
backend. Playwright permanece congelado y no se fuerza integración UI para
completar la matriz.

#### A-PRE-0 y A-PRE-1

**A-PRE-0** está especificada en
[A_PRE_0_BASELINE_SPEC.md](./A_PRE_0_BASELINE_SPEC.md). Define identidad,
perímetro, dependencias, efectos/artefactos, salida estructurada y
comparabilidad. No es una ejecución ni una baseline PRE.

**A-PRE-1** permanece `PENDING / NOT AUTHORIZED`. Sus precondiciones son un
snapshot-overlay limpio identificado, observer probado con fixtures,
preflight estático satisfactorio y entorno temporal Python 3.10 que respete
el lock. Los efectos reales se observarán dentro de A-PRE-1 bajo aislamiento,
no se exige ejecutar antes las suites para su adjudicación.
Cuando se autorice, no modifica `.venv`, E5/Qwen, bases protegidas, corpus,
índices ni blind pool. Guarda status por suite, skips, warnings, errores,
duración, artefactos y hashes para comparación PRE→POST. El resultado no activa
Gate B automáticamente.

## Orden de ejecución y gates de salida

### 1. Cerrar la base de certificación (A-1/A-2)

El manifiesto de 25 suites y la clasificación del perímetro están definidos;
la discrepancia histórica **451 vs. 446** está explicada. Falta fijar el
snapshot PRE limpio, completar el inventario de efectos, validar el perímetro
sin ejecutar suites y demostrar la instalación temporal con el runtime Python
3.10 candidato.

**Gate de salida:** instalación/import soportados reproducibles; perfil de
release con perímetro explícito, reportes por suite y sin cambios a artefactos
protegidos. Los resultados `2695`, `2703`, `2814` u otros de snapshots previos
no sustituyen este PRE.

### 2. Formalizar identidad y aislamiento curricular (ESTAB-G2 / Gate B)

Reconciliar declarativamente IDs canónicos, aliases, `curriculum_id`, perfiles,
roles de fuentes y ACL efectiva. Obtener autoridad curricular para
`fadena-std`. Mantener cualquier diagnóstico sobre SQLite como read-only; toda
migración o cambio de ACL exige decisión separada.

**Gate de salida:** prompts y fuentes correctos desde identidad explícita hasta
el request final, fallback neutral en IDs desconocidos, casos positivos y
negativos por materia, sin contaminación entre currículos. El resultado del
fixture `fadena-std` no se generaliza a producción ni a todos los cuadernos.

### 3. Completar F5 / Gate C con fixtures sintéticas

Usar almacenamiento temporal y escenarios mínimos para probar procedencia,
historial y memoria acotados al scope, preferencia persistente vs. instrucción
del turno, continuidad y ambigüedad, intentos incompletos y estado pedagógico.
Separar memoria de estudiante de evidencia autorizada; probar que interacciones
ordinarias no muten BKT sin evidencia suficiente.

**Gate de salida:** matriz de invariantes F5 aprobada y límites documentados.

### 4. Adjudicar y cerrar F6 / Gate D

La evidencia B1-B ya está registrada y **solo caracteriza las secuencias del
slice sintético probado**, no afirma comportamiento universal de TALOS. B1-R
ahora ofrece trazas repetibles, pero su aceptación sigue pendiente. Después de
Gate B/C y antes de editar cliente o servidor, adjudicar explícitamente el
contrato usando estas observaciones acotadas:

- `abstention` / `clarification`: **en el slice sintético B1-B**, el contexto
  falso activó la rama temprana de la ruta; emitió `evidence_manifest`, luego
  `abstention` o `clarification`, y cerró con EOF sin `phase_complete`. El
  pipeline no fue invocado en esos casos.
- `truncated`: **en el slice sintético**, un pipeline falso emitió la secuencia
  source-traced `phase_start → truncated → audit_verdict →
  evidence_manifest → phase_complete`. El trazado estático indica que el
  pipeline actual puede continuar después del aviso; su ejecución real no se
  probó en B1-B.
- `stream_aborted`: **en el slice sintético**, el pipeline falso emitió
  `stream_aborted` y luego levantó `CancelledError`; la ruta cerró el stream
  sin `phase_complete`. No se simuló un cliente desconectando un socket real.
- `error`: B1-A transformó una excepción sintética del pipeline en SSE `error`
  bajo HTTP 200; no prueba todos los fallos internos o de proveedor.
- `chatService`: el trazado de fuente muestra que el allowlist omite
  `abstention` y `clarification`, y que EOF sin `phase_complete` se rechaza.
  Es un hallazgo de contrato estático correlacionado con el slice, no una
  prueba React↔FastAPI.

No convertir esta lista automáticamente en un fix ni usar una terminación
genérica que borre distinciones. La decisión de contrato es un paso explícito;
si requiere cambios, aplicarlos después con alcance mínimo. Probar terminal
ausente/duplicado, error después de tokens, respuesta parcial, cierre y mensaje
público sin detalles internos.

**Gate de salida:** route real con dependencias sintéticas y consumidor UI
interpretan de forma coherente cada resultado; solo después ejecutar la
integración React↔FastAPI controlada. No incluye proveedor real.

### 5. Reintroducir realidad por capas; luego regresión

Secuencia backend: B2 contexto/dominio con stores sintéticos → B3 retrieval con
fixtures SQLite/corpus sintéticos y aislamiento de scope → B4 pipeline real
con provider falso → B5 request HTTP/SSE integrado → B6 React↔FastAPI aislado.
Cada etapa conserva las guardas, valida las invariantes previas y se detiene
ante acceso no previsto. El lifecycle normal, stores locales y proveedor real
no forman parte de estas fases sintéticas.

**Gate de salida:** matriz de integración cumplida por frontera y regresión
global POST comparada con PRE; test gate/certificación debe incluir condiciones
de hardware/runtime, warnings, skips, side effects y artefactos con hashes.

### 6. Reabrir la evaluación comparativa (PED-F7)

Reutilizar la Fase 0 como antecedente, no como resultado de una versión nueva.
Definir antes de correr: sistemas/versiones/prompts/fuentes, consultas
canónicas, rúbrica, condiciones de ciego, evaluadores, repeticiones y umbrales.
Primero medir calidad de respuesta por currículo e intención; no inferir
aprendizaje de mejores respuestas. Para retención/transferencia, diseñar un
experimento independiente, con controles y autorización.

**Gate de salida:** decisión explícita de mejora/no inferioridad/inconcluso,
con fallos y variabilidad incluidos. Una repetición usa transcripciones/datos
locales solo con alcance y privacidad aprobados.

## Tracks paralelos, no intercambiables

- **BENCH-G2:** continuar solo revisión/adjudicación humana y validadores
  autorizados. La integridad estructural de un paquete no prueba relevancia,
  calidad de ranking o autorización global. El benchmark ampliado depende de
  qrels/scope adjudicados, snapshots y piloto aprobado.
- **E5/Qwen:** Path A requiere factibilidad de Python 3.10; si no es viable, no
  sustituir pins: proponer una decisión Path B versionada. Después se requieren
  dos reconstrucciones limpias coincidentes, identidad SHA de artefactos,
  harness sintético autorizado y validación de padding. Qwen requiere binding
  de modelo/tokenizer y runtime propio. Nada de esto autoriza benchmark ni
  blind pool por sí solo.
- **Reality Audit RA:** mantener la secuencia `OBSERVE → MEASURE → CORRELATE →
  CLASSIFY → HUMAN DECISION → CHANGE`. Resolver candidatos de complejidad,
  clones, dead code y dependencias solo con evidencia de uso y tras los gates
  funcionales. Las ideas Harness/Context/Evals/Guardrails/Memory del adjunto
  son lentes para clasificar brechas existentes, no una nueva ola de features.

## Fuera de alcance hasta gate y autorización

No levantar el lifecycle normal para “probar”; no usar proveedores reales en
tests sintéticos; no modificar bases/ACL/qrels históricos, corpus, índices,
embeddings, modelos o blind pool; no repetir el benchmark TALOS vs NotebookLM
sin protocolo aprobado; no refactorizar funciones complejas ni borrar
candidatos estáticos; no instalar frameworks adicionales. Producción,
E5/Qwen y blind pool permanecen sin cambios y sin autorización de ejecución.

## Documentos fuente y autoridad

Esta hoja es la autoridad para **orden y estado integrado**. La tabla y
secuencia de “Estado integrado al 2026-09-30” son un snapshot histórico; la
sección CP073 a continuación es el estado integrado vigente al 2026-10-01.
Los criterios técnicos detallados siguen en:

- [Plan pedagógico PED-F0…PED-F7](./PLAN_MEJORA_PEDAGOGICA_TALOS.md) y
  [diagnóstico multi-cuaderno / Gates A–E](./DIAGNOSTICO_MULTICUADERNO_Y_PLAN_DE_CONTINUIDAD.md).
- [Suite de estabilización](./PLAN_SUITE_FIX_ESTABILIZACION.md) y
  [perímetro de certificación](./TEST_CERTIFICATION_PERIMETER.md).
- [Fase 0 TALOS vs NotebookLM](./FASE0_LINEA_BASE_TALOS_NOTEBOOKLM.md).
- [Arqueología backend B0–B1-B](./BACKEND_OPERATIONAL_ARCHAEOLOGY.md),
  [reality scorecard](./REALITY_AUDIT_REPORT.md) y
  [backlog de purificación](./REALITY_AUDIT_PURIFICATION_BACKLOG.md).
- [Runbook BENCH-G2](./GATE2_BENCHMARK_SCOPE_RUNBOOK.md) y
  [plan del generador Gate 2](./GATE2_GENERATOR_IMPLEMENTATION_PLAN.md).
- [Decisión de runtime E5](./E5_RUNTIME_CANDIDATE_DECISION.md),
  [gate de prerrequisitos E5/Qwen](./EMBEDDING_EXECUTION_PREREQUISITES_RESOLUTION_GATE.md)
  y [gates de blind pool](./BLIND_POOL_GENERATION_AUTHORIZATION_GATE.md).

Los reportes previos con estados distintos son snapshots históricos; no
reemplazarlos ni combinar sus cifras como si fueran una corrida única.

---

# Mapa maestro CP073 — corte documental 2026-10-01

## 1. Resumen ejecutivo y límites

```text
PRODUCT_STATUS = IMPLEMENTED_CORE_WITH_OPEN_ACCEPTANCE; PRODUCT_COMPLETE_NOT_DEMONSTRATED
VALIDATION_STATUS = PARTIAL
FORMAL_ASSURANCE_STATUS = NOT_COMPLETE

BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED
EXTERNAL_SPEC_ARTIFACT = UNRECOVERED
PATH_A = INVESTIGATED / NOT_RESOLVED
GATE_EXTERNAL_EVIDENCE_AUTHORIZATION = AUTHORIZED
A_PRE_0 = NOT_READY
A_PRE_1 = NOT_AUTHORIZED / NOT_EXECUTED
```

- **Hecho:** el repositorio contiene un producto amplio de tutoría, pedagogía,
  retrieval y evaluación determinista, con implementación y pruebas locales
  documentadas.
- **Límite:** no existe evidencia suficiente para llamar a todo ese conjunto
  un producto integrado, aceptado end-to-end o certificado en producción.
- **Cierre de producto:** queda pendiente aceptar y demostrar las fronteras
  funcionales actuales (identidad/scope, continuidad/memoria, contrato
  HTTP/SSE/UI y regresión integrada). El mapa no afirma que el código esté
  roto; afirma que no hay evidencia de aceptación completa.
- **Cierre de validación:** además exige evidencia reproducible del perímetro
  de pruebas y evaluación pedagógica acorde al alcance de las claims.
- **Garantía formal:** A-PRE-0 sigue bloqueada. CP072 realizó búsqueda pública
  autorizada y clasificó `NOT_RESOLVED`; `NOT_FOUND` no es `PROVEN_ABSENT`.
  La autorización de búsqueda no es resolución ni readiness.

La base observada es HEAD `f81134fc2293916210d53c8065f3a0049e52b0b4` más un
worktree con cambios existentes. No se ejecutó TALOS, tests, workloads,
benchmark, runtime, VM, DB, corpus ni modelos para producir este mapa. Las
afirmaciones de “probado” son resultados históricos citados por sus fuentes,
no una corrida actual.

## 2. Objetivo actual y significado de producto

El README define TALOS como motor de estudio/tutoría basado en evidencia y
arquitectura multicapa. El plan pedagógico concreta el objetivo como tutor de
estudio en ciberseguridad y fundamentos de ingeniería: responder directamente,
adaptar profundidad y representación al estudiante, progresar entre explicación
y práctica, preservar rigor contextual, citar honestamente y evitar entregar
soluciones en evaluaciones protegidas. El límite declarado es curricular, no
asistente general.

| Interpretación | Estado respecto del objetivo actual |
|---|---|
| Tutoría educativa basada en fuentes, adaptación pedagógica y feedback | Esencial al propósito declarado. |
| Rigor epistémico, abstención, separación de evidencia y soluciones protegidas | Esencial a las claims de fiabilidad/seguridad pedagógica; la aceptación completa de todos los paths sigue abierta. |
| BKT, generación de ejercicios, evaluación determinista y representación técnica | Capacidades distintivas existentes; la validación integral multi-currículo no está cerrada. |
| Operación offline-only como requisito de cierre | No establecido por el objetivo actual como condición de release. “Local-first/offline-capable” aparece como principio/atributo arquitectónico; servicios remotos opcionales como Jina impiden equiparar esto a que toda ruta sea estrictamente offline. |
| Multi-user | No está establecido como requisito vigente de cierre en las fuentes rectoras revisadas; no añadirlo como criterio implícito. |
| Clon de NotebookLM | No requerido. La comparación es antecedente/evaluación, no especificación de paridad de producto. |
| Context Engine 2.0 / ColBERT / 400-query benchmark del roadmap v1.1 | Propuestas históricas/de evolución. No son requisitos automáticos de cierre mientras no exista una decisión vigente que los adopte. |

“Terminado” no tiene una única interpretación binaria demostrada por un gate
vigente que fusione producto, validación y garantía formal. Este documento
separa los tres niveles en §10 en vez de inventar esa equivalencia.

## 3. Clasificaciones

Cada fila de capacidades de §4 utiliza exactamente una clasificación:

| Estado | Significado en este mapa |
|---|---|
| `DONE_VERIFIED` | El requisito acotado tiene evidencia directa suficiente y el resultado corresponde a ese alcance. No implica que toda la aplicación esté certificada. |
| `DONE_WITH_KNOWN_LIMITATION` | El comportamiento acotado tiene evidencia, con límites conocidos que impiden generalizar. |
| `IMPLEMENTED_NOT_FULLY_VALIDATED` | Hay implementación y alguna prueba/inspección, pero faltan validación de integración, dominio, runtime o producción. |
| `PARTIALLY_IMPLEMENTED` | Hay mecanismos, pero partes del comportamiento o contrato requerido faltan. |
| `PLANNED` | Está descrito como trabajo futuro, sin evidencia de implementación aceptada. |
| `BLOCKED` | No puede completarse hasta resolver una dependencia explícita o gate/autorización. |
| `DEPRECATED` | La fuente declara que el componente/requisito se retiró o sustituyó. |
| `NOT_REQUIRED` | No es requisito para el objetivo de cierre actual según las fuentes rectoras revisadas. |
| `UNKNOWN` | Evidencia insuficiente para clasificar sin inferir. |

La existencia de código no basta para `DONE_VERIFIED`. `DOCUMENTED`,
`IMPLEMENTED`, `TESTED`, `INTEGRATED` y `PRODUCTION_USED` son ejes separados:
un módulo puede estar implementado y unit-tested, pero no integrado; una
integración sintética no demuestra uso productivo. “No hay evidencia de uso
productivo” se registra como no demostrado, no como prueba de que no se usa.

## 4. Inventario funcional por capacidad

El nivel de prueba indicado es el máximo explícitamente respaldado por las
fuentes revisadas. No se ejecutaron pruebas en CP073.

### Pedagogía y evaluación

| Capacidad | Implementación y evidencia registrada | Probado / integración / uso productivo | Límite y dependencia | Estado |
|---|---|---|---|---|
| BKT | `student/bkt_tracker.py`; suite unitaria de BKT y prueba de concurrencia citadas en README/inventario de tests. | Implementación y pruebas unitarias; aceptación de mutación y continuidad dentro de F5 no cerrada. Uso productivo no demostrado por este expediente. | Debe probarse con evidencia evaluativa autorizada; turnos ordinarios no deben alterar dominio sin fundamento. Depende de F5/Gate C. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| SM-2 / spaced repetition | `student/spaced_repetition.py`; suite unitaria dedicada. | Implementado y probado unitariamente según presencia de pruebas; integración pedagógica/operativa no demostrada aquí. | No es gate independiente de cierre funcional salvo que se formule como claim de producto. | `DONE_WITH_KNOWN_LIMITATION` |
| Knowledge Components, catálogo y matching | Catálogo/configuración curricular, `curriculum/`, herramientas KC y pruebas de matching/aliases/deícticos. | Tests locales de matching y perfiles; Gate B integrado permanece parcial. | Identidad exacta, aliases, fuentes y ACL efectiva deben reconciliarse; una prueba `fadena-std` con fixture no generaliza. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| Ejercicios adaptativos y generador MultiKC | `generation/` y política/generadores; CAPABILITIES documenta combinaciones de 2–3 KCs y oráculo determinista. | Pruebas locales/documentadas; validación de corrección y adaptación en varios currículos no establecida. | Requiere estado BKT/KC fiable, sources/scope aceptados y casos de regresión. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| Struggle Mode, hints socráticos y fading | `web/`, `pedagogy/` y suite `test_struggle_protocol.py`; documentos PED-F1…F4 declaran contrato/prompt localmente probado. | Implementación y pruebas acotadas; obediencia semántica de proveedor real no demostrada de forma general. | F5/F7 deben validar continuidad, turno y calidad, no sólo forma del prompt. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| BugSpotter | Generación/mutación pedagógica documentada para CWE-120/190/362/416. | Implementación reportada con tests de oráculo/plantillas; validación multi-currículo y uso productivo no demostrado. | Los casos sintéticos no establecen cobertura de vulnerabilidades reales. | `DONE_WITH_KNOWN_LIMITATION` |
| Trace Tables x86-64 | Intérprete didáctico documentado con conjunto acotado de instrucciones, flags, memoria flat y límite de pasos. | Implementado y cubierto por pruebas locales según release docs; no es emulador general ni ejecución de hardware. | Limitado al ISA subset/documentado. | `DONE_WITH_KNOWN_LIMITATION` |
| Prevención de solution leak / protección de evaluación | `ContentRegistry`, `solution_protection.py`, rutas administrativas; tests protected/security y fixes TUT-03 reportados. | Controles y pruebas locales; coherencia TutorPolicy/Study Loop, workers y resistencia a paráfrasis no están aceptadas totalmente. | No extender una protección basada en referencia/token exacto a equivalencia semántica universal. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| Abstención / EpistemicController / CoverageGuard | `pedagogy/epistemic_controller.py`, seguridad/retrieval; invariantes fail-closed descritos por docs y suites adversariales/survival. | Pruebas locales y B1 observan sólo paths sintéticos específicos; tasas de falsos positivos/negativos multi-currículo no demostradas. | Requiere cobertura y contexto correcto; evidencia vacía o fuera de scope debe seguir explícita. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| Citations, ContextPack y separación de oracle | `evidence/`, `context/context_pack.py`, filtrado de soluciones y pruebas de aislamiento. | Hay pruebas aisladas; no aceptación integral real multi-cuaderno del recorrido retrieval→fuente→respuesta. | Dependencias: Gate B (identidad/fuentes), Gate C (continuidad/provenance), F7 (calidad). | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| Forensic Auditor / auditoría de interacciones | Paquetes `audit/`, trazas de retrieval y controles de procedencia están documentados. | Hay componentes/test perimeter; no se documenta aquí aceptación de todos los eventos, retención, sanitización y fallos. | No confundir log/traza con evidencia de que el auditor cubre todos los caminos. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |

### Retrieval y memoria conversacional

| Capacidad | Implementación y evidencia registrada | Probado / integración / uso productivo | Límite y dependencia | Estado |
|---|---|---|---|---|
| FTS5 / búsqueda léxica exacta | Knowledge Store SQLite y rutas de recuperación léxica; tests de retrieval. | Pruebas locales y fixtures; operación end-to-end con bases de producción no se reejecutó ni se certifica aquí. | El lifecycle normal puede leer/escribir DB/corpus; fixtures existentes no son estrictamente no-read. | `DONE_WITH_KNOWN_LIMITATION` |
| Embeddings / vector retrieval | Vector store y adapters/modelos presentes; E5/Qwen están registrados como candidates/experimentos separados. | Hay estructura e integración documentada, pero E5 runtime no reproducible/aceptado y Qwen con bloqueo de provenance/runtime. | Las candidaturas E5/Qwen no prueban que un backend específico sea runtime productivo. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| Retrieval Fabric, CandidatePooler, PresentationFilter | Pipeline de reescritura, routing, pooling, filtro anti-leak y ranking documentado; tests `test_retrieval_fabric.py`. | Componentes probados en local; aceptación del path real multi-scope incompleta. | Depends on identity/ACL, data snapshot and provider-independent retrieval fixtures. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| QueryRewriter y AdaptiveRouter | Módulos dedicados y tests de rewriter/router; CAPABILITIES describe perfiles lexical, semantic y faceted. | Determinismo de componentes probado; calidad de recuperación global no concluida por eso. | No reemplaza benchmark/qrels válidos. | `DONE_WITH_KNOWN_LIMITATION` |
| Reranker local determinista / fallback | Reranker local y fallback descritos; tests locales y contrato de operación sin red. | Pruebas acotadas documentadas; el valor de ranking contra ground truth no es un PASS actual. | Umbral/orden útil debe evaluarse con qrels adjudicados. | `DONE_WITH_KNOWN_LIMITATION` |
| Jina remoto opcional | Adaptador API opcional con fallback reportado. | No se realizó llamada remota en esta tarea; uso real no demostrado. | No requisito para operación local ni cierre de producto actual. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| Retrieval exact/semantic/composite y deterministic fallback | Clasificación y rutas documentadas en Fabric/Router. | Decisión de ruteo determinista probada; efectividad end-to-end no establecida. | Necesita corpus/versiones/scope y evaluación controlada. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| Citations/retrieval trace | Trace logger JSON/forensic y referencias de evidence están en documentación. | Estructuras presentes; cobertura, integridad y uso real no quedaron calificados transversalmente. | Rastro de retrieval no equivale a validez/corrección de respuesta. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| Conversation router, PersonaNarrator, style routing | Rutas de chat, structured pipeline y contratos pedagógicos presentes. | Pruebas de prompt/ruta acotadas; no prueba de conducta consistente de un proveedor real. | PED-F7 y Gate D pendientes. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| Context Builder / ContextPack | `context/context_pack.py` y preparación de contexto en ruta chat. | B1-A/B1-R sustituyeron dependencias con fakes; no califican contexto/retrieval real. | B2/B3 y Gate B/C son dependencias. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| Session Memory / Mem0 | Gestión de session memory y store pedagógico presentes; memoria de largo plazo figura en arquitectura. | Piezas de historial/procedencia existen; aceptación de scope, contaminación y precedencia actual pendiente F5. | Usar stores aislados; separar memoria de evidencia autorizada. | `PARTIALLY_IMPLEMENTED` |
| Provider abstraction / circuit breaker | Adaptadores LLM, selección de backend y controles de resiliencia aparecen en código/documentación. | No se usaron proveedores en CP073; B1 usa fakes. Uso productivo/semántica de fallos no demostrado. | Validación real requiere gate/autorización aparte. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |

### Infraestructura y transporte

| Capacidad | Implementación y evidencia registrada | Probado / integración / uso productivo | Límite y dependencia | Estado |
|---|---|---|---|---|
| FastAPI endpoints | `web/app.py`, routers y route `POST /api/chat/query`; B1-A ejercitó la ruta ASGI in-process con deps sintéticas. | HTTP route acotada probada sin servidor listening ni container/lifespan normal. | `AppContainer(use_mock=True)` no es modo seguro de datos; no iniciar lifecycle en este mapa. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| SSE backend/client | B1-A/B observó secuencias fakes; UI `chatService` tuvo fixes de fail-closed ante truncation/abort/EOF con tests Playwright mockeados. | Separadamente probado en backend sintético y cliente mock; React↔FastAPI real no probado. | Abstention/clarification y semántica terminal aún requieren decisión/aceptación Gate D. | `PARTIALLY_IMPLEMENTED` |
| React UI | `kasiu-lab/ui`; Playwright shell/chat mock test reportados por auditoría. | UI aislada con API/SSE mock; no integrada con backend real. | No declarar experiencia E2E. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| Persistence SQLite / stores | Knowledge, vector y student state stores; tests de storage. | Tests/fixtures locales; el container real puede leer/escribir DB y corpus en init. | Integración de stores aislados y fronteras de datos siguen pendientes. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| Configuración, provider registry, runtime | `pyproject`, Settings, adapters, `quality_gate.py`, contenedor. | Reproducibilidad de dependencias documentada parcialmente; A-PRE runtime/ptrace no resuelto y E5 separado. | El `.venv` local no prueba runtime objetivo. | `IMPLEMENTED_NOT_FULLY_VALIDATED` |
| Multi-user | No hay requisito actual identificado en los documentos rectores leídos. | Sin claim de implementación o certificación en este mapa. | No incorporar a cierre sin decisión de producto explícita. | `NOT_REQUIRED` |
| Clon de NotebookLM | No es la misión declarada. Comparación de 20 preguntas es línea base, no paridad contractual. | No aplica. | No crear backlog de features para alcanzar paridad. | `NOT_REQUIRED` |
| Offline-only absoluto | No establecido como requisito de cierre; local-first/offline-capable se documenta como principio/capacidad deseada. | La opción Jina es remota y opcional. | Si offline-only se convierte en requisito, requiere decisión y matriz de rutas/proveedores. | `NOT_REQUIRED` |

## 5. Qué ocurrió después de v1.0-elite

| Origen | Problema / cambio solicitado | Cambio y evidencia documentados | Estado actual |
|---|---|---|---|
| TALOS v1.0-elite.1 | Línea base de producto con BKT, generación adaptativa, retrieval y suites reportadas históricamente. | `CAPABILITIES.md` y `ARCHITECTURE.md` describen capacidades/certificación del corte 2026-09-23. Conteos como 2,441 passing pertenecen a ese corte; no son corrida CP073. | Snapshot histórico, no certificación actual. |
| Comparación TALOS–NotebookLM / PED-F0 | 20 preguntas revelaron en registros parciales demora, salida truncada, error 500 y desajustes de seguimiento; NotebookLM tuvo respuestas completas en registro. | Fase 0 fijó procedencia, wording, límites y no causalidad. No asigna score de calidad retrospectivo ni vuelve a ejecutar comparación. | Línea base cualitativa/integridad documental, no benchmark causal ni evidencia de aprendizaje. |
| PED-F1…F4 / TUT-03 / H1–H3 | Ajuste de respuesta, currículo, política de solución y formatos. | Fixes de fallback neutral, identidad exacta, perfil `fadena-std`, prompts/formatos, protección runtime y tests focalizados documentados. | Incorporados en el worktree según fuentes; aceptación amplia de proveedor/currículos queda abierta. No reabrir fixes ya aplicados salvo evidencia nueva. |
| PED-F5 / Gate C | Continuidad, fuentes/memoria, historial, intentos y no-mutación de estado. | Procedencia SSE y componentes de memoria/historial existen; tests/decisiones parciales. | Aceptación abierta. |
| PED-F6 / B0–B1 | Fronteras de runtime, ruta chat, streaming y cliente. | B0 estático; B0.5 guarded con container sintético; B1-A route ASGI y B1-B secuencias SSE con fakes; `chatService` fail-closed con mocks; B1-R 10 escenarios × 3 repeticiones y verifier reportados `TECHNICAL PASS`. | Observaciones cerradas sólo dentro de cada scope. No equivalen a backend integrado ni F6 PASS. |
| Reality Audit | Inventario estático de clones, complejidad, dead candidates y ruta real. | Reportes registran métricas y candidatos; ningún candidato se elimina por conteo estático. | Remediación requiere evidencia/decisión posterior; limpieza masiva no forma parte de cierre actual. |
| A-PRE / CP050–CP058 | Reconciliar 385 syscalls, contadores, provenance, manifest/ledger y criterios. | CP055–058 documentaron crosswalk/reconciliación descriptiva, stale counters, provenance/gaps; se conservaron UNKNOWN y `inventory.frozen=false`. | Descriptivo completado según checkpoints; no equivale a disposición normativa ni efecto observado. |
| CP059–CP072 / Camino A | Separar evidencia de decisiones y determinar la dependencia de authority. | CP070 concluyó autoridad material para cierre normativo/A-PRE-0; CP071 autorizó búsqueda futura; CP072 buscó públicamente con resultado `NOT_RESOLVED`. | `BASELINE_SPEC_AUTHORITY=AUTHORITY_UNRESOLVED`; no repetir arqueología ni búsqueda pública igual sin evidencia nueva. |

Los fixes de la comparación se han incorporado como mejoras/fixes en los
tracks PED-F1…F6 descritos arriba; **no constituyen una lista paralela de
trabajo pendiente**. Sólo permanecen los criterios de aceptación/validación
que la documentación identifica explícitamente como abiertos.

## 6. Gates, evidencia y efecto de cierre

`DOES_IT_BLOCK_PRODUCT_CLOSURE?` distingue cierre funcional de validación y
garantía formal. “No” no significa que el gate carezca de valor; significa que
no se ha demostrado una dependencia necesaria con producto funcional bajo el
objetivo actual.

| Gate / track | Propósito y estado documentado | Evidencia / blocker restante | Tipo de bloqueo | ¿Bloquea cierre de producto funcional? |
|---|---|---|---|---|
| B0 | Arqueología estática de backend: hecha. | Identificó efectos normales de container; no usó app real. | `HISTORICAL_GATE` | No por sí sola. |
| B0.5 | Probe guarded import/factory/startup sintético: cerrado para ese scope. | No califica lifecycle/container normal. | `HISTORICAL_GATE` | No; acota cómo validar con seguridad. |
| B1-A | HTTP/SSE ASGI route con dependencias sintéticas: observado/pasó en casos reportados. | No listening server, provider ni retrieval real. | `HISTORICAL_GATE` | No aisladamente. |
| B1-B | Secuencias terminales con fakes: observadas. | Contrato de abstention/clarification/truncated/abort aún requiere adjudicación; no E2E. | `AUDIT_BLOCKER` para claims de streaming | Sí para declarar integración conversacional aceptada; no demuestra fallo universal. |
| B1-R | Repeatability harness: `TECHNICAL PASS` documentado. | No F6, runtime productivo ni cliente real. | `HISTORICAL_GATE` | No por sí sola. |
| A-1/A-2 / A-PRE-0 | Base de certificación, identidad, perímetro y preflight. | A-PRE-0 `NOT_READY`; autoridad unresolved, coverage/385 dispositions UNKNOWN, tracing incompleto/host ptrace bloqueado, predicate false. | `FORMAL_BLOCKER` | No demostrado como requisito del producto funcional; sí bloquea cierre formal A-PRE. |
| A-PRE-1 | Medición PRE bajo aislamiento. | `NOT_AUTHORIZED / NOT_EXECUTED`; requiere preflight y autorización operativa específica, además de host con tracing verificable. | `AUDIT_BLOCKER` / `FORMAL_BLOCKER` | No para la afirmación básica de producto; sí para garantía formal que depende de A-PRE. |
| Gate B / ESTAB-G2 | Identidad curricular, sources, aliases, perfiles y ACL. | H1–H3 fixes locales; aceptación multi-cuaderno/read-only y autoridad curricular incompleta. | `PRODUCT_BLOCKER` para claims multi-cuaderno confiables | Sí, si el cierre afirma aislamiento/selección correcta multi-currículo. |
| F5 / Gate C | Continuidad, memoria, provenance, estado pedagógico. | Aceptación con stores aislados pendiente. | `PRODUCT_BLOCKER` para claims de continuidad/adaptación longitudinal | Sí para esas claims, no para un demo de turno único limitado. |
| F6 / Gate D | Contrato terminal y fiabilidad backend/SSE/UI. | Requiere decisión de contrato y coherencia pipeline→HTTP/SSE→cliente. | `PRODUCT_BLOCKER` para afirmar flujo de chat integrado fiable | Sí para tal afirmación; pendiente integración controlada. |
| B2 / B3 / B4–B6 | Reintroducción sintética por capas: contexto, retrieval, pipeline con provider fake, HTTP/SSE, React↔FastAPI. | Plan de secuencia; las etapas integradas finales no constan como completadas en fuentes revisadas. | `PRODUCT_BLOCKER` de integración | Sí para cierre como aplicación integrada; no se requiere proveedor real. |
| PED-F7 / Gate E | Evaluación pedagógica multi-currículo. | Pendiente matriz/rúbrica/umbrales y evaluación controlada; aprendizaje/retención separado. | `VALIDATION_BLOCKER` | No prueba funcional automática; sí bloquea claims de calidad/mejora validadas. |
| BENCH-G2 | Validar scopes/qrels/ranking. | Pausado/no canónico; revisión pendiente de consultas/qrels; el runbook indica 111 consultas y 149 qrels pendientes de juicio individual en lote inicial. | `BENCHMARK_BLOCKER` | No, salvo claims de ranking comparativo que dependen de él. |
| E5 | Viabilidad y reproducibilidad del runtime candidato de embeddings. | Path A elegido, factibilidad/read-only y dos reconstrucciones limpias pendientes; ejecución de entorno/harness no autorizada. | `OPTIONAL_ENHANCEMENT` / `BENCHMARK_BLOCKER` | No está demostrado como runtime productivo requerido. |
| Qwen | Binding provenance/model/tokenizer y runtime propios. | Independiente y bloqueado; E5 decision no lo resuelve. | `OPTIONAL_ENHANCEMENT` / `BENCHMARK_BLOCKER` | No demostrado como dependencia del producto actual. |
| Blind pool | Preparación/generación de evaluación ciega. | Gates de autorización/precondiciones pendientes. | `BENCHMARK_BLOCKER` | No. |
| Reality Audit purificación | Decidir remediación de clones, complejidad, dead-code candidates. | Métricas son candidatos; no hay adjudicación de seguridad/uso para eliminación. | `OPTIONAL_ENHANCEMENT` | No; no refactorizar por métricas solas. |

## 7. A-PRE / aislamiento: estado integrado CP050–CP072

```text
BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED
EXTERNAL_SPEC_ARTIFACT = UNRECOVERED
PATH_A = INVESTIGATED / NOT_RESOLVED
GATE_EXTERNAL_EVIDENCE_AUTHORIZATION = AUTHORIZED
385 rows = unique
385 global dispositions = UNKNOWN
inventory.frozen = false
SCOPE_UNPROVEN = preserved
A_PRE_0 = NOT_READY
A_PRE_1 = NOT_AUTHORIZED / NOT_EXECUTED
```

La investigación CP072 no recuperó `f058…` ni una designación equivalente en
fuentes públicas accesibles. No existe evidencia para determinar si el
artefacto o la autoridad están ausentes fuera de esas fuentes.

**Bloqueo exacto:** no se puede identificar y aplicar un criterio normativo
autorizado vinculado al snapshot/inventario requerido, ni afirmar que sus
385 outcomes/cobertura satisfacen el contrato A-PRE-0. Las 385 dispositions
globales siguen `UNKNOWN`; no se congeló inventory. Además existen blockers
independientes de authority (tracing nativo incompleto, requisitos/units y
predicate false); resolver autoridad por sí sola tampoco haría READY A-PRE-0.

**Clasificación de A-PRE:** `FORMAL_ASSURANCE_CRITICAL`. Está ligada a claims
de aislamiento y calificación formal, no se demuestra en la misión funcional
educativa como requisito indispensable para un cierre de producto limitado.
No debe excluirse si se pretende anunciar garantía/certificación formal de
aislamiento; tampoco debe usarse para decir que todo TALOS está bloqueado.
Las sources actuales no justifican convertir A-PRE-0 en blocker de toda
funcionalidad educativa.

No reabrir CP050–CP072 ni reconstruir el crosswalk salvo que llegue evidencia
verificable nueva o una decisión humana nueva. La autorización permanece
registrada; búsqueda ya realizada no equivale a resolución.

## 8. BENCH-G2, E5/Qwen y evidencia de código actual

### BENCH-G2

- Terminado: metodología/runbook, generador/validadores y fixtures acotadas
  documentadas; el trabajo se separó de los artefactos canónicos.
- Pendiente: adjudicación humana del scope y qrels; luego integridad de una
  versión nueva y piloto explícitamente autorizado con snapshots/corpus
  compatibles.
- Estado: `BLOCKED` para afirmar métricas válidas del benchmark actual; no
  requisito de producto funcional ni permiso para ejecutar el set de 420.
- No sustituir qrels pendientes por títulos/tema, ni regenerar sobre bases
  activas.

### E5/Qwen

- E5: Path A seleccionado para explorar runtime Python 3.10 conforme al lock;
  no equivale a reproducible. Factibilidad read-only, doble reconstrucción
  autorizada, evidencia de artefactos y harness autorizado son gates separados.
- Qwen: bloqueo separado de artefact provenance/runtime; no queda resuelto por
  la decisión E5.
- Ningún documento revisado establece que estos candidates estén integrados
  como ruta obligatoria del runtime real actual de TALOS. Clasificarlos como
  experimentales/benchmark candidates; no detener cierre de producto por su
  falta ni afirmar que son producción usada.

### Código y evidencia de pruebas

| Afirmación | Qué está documentado | Qué no se puede afirmar |
|---|---|---|
| Repositorio amplio con módulos pedagógicos, retrieval, memoria, API, UI y tests | README, arquitectura, CAPABILITIES, source paths y tests específicos citados. | Integración de todas las partes por mera presencia de archivos. |
| Test perimeter | `config/test_perimeter.json` es la fuente del perímetro; `quality_gate.py` lo valida. Los conteos documentales se deben recalcular en el snapshot que se cualifique. | Los resultados de 2,441, 2,695, 2,947 u otros cortes antiguos como corrida actual. |
| Gates sintéticos B0.5/B1/B1-R | Evidencia acotada y reproducible descrita en auditorías/checkpoints. | Lifecycle normal, uso de DB/corpus real, proveedor real, rendimiento, uso productivo o aceptación E2E. |
| Playwright/UI | Tests aislados con API/SSE mock. | Compatibilidad con backend FastAPI real o una sesión productiva. |
| Producción | Documentación v1.0 llama certificado a un snapshot histórico. | Que el checkout de CP073 sea ese artefacto, que esté desplegado o que siga teniendo ese estado. |

Si una claim depende de ejecución actual, debe registrarse como
`RUNTIME_EVIDENCE_REQUIRED`; no ejecutar esa evidencia como parte de CP073.

## 9. Deuda técnica clasificada

| Clase | Elementos y criterio |
|---|---|
| Crítica para cierre del producto bajo las claims actuales | Gate B/C y Gate D/integración controlada para afirmar comportamiento curricular, continuidad y chat fiable de extremo a extremo. No se ha demostrado que todo el producto carezca de esas funciones; falta aceptación/evidencia de frontera. |
| Crítica para garantía formal, no automáticamente para producto | A-PRE-0/A-PRE-1: autoridad unresolved; 385 UNKNOWN y `inventory.frozen=false`; tracing y predicate/coverage no cerrados. |
| Importante / validación | PED-F7 multi-currículo con protocolo; cerrar condiciones de release/perímetro y generar una baseline reproducible; adjudicar BENCH-G2 si se sostienen claims de ranking. |
| Importante, experimental condicionado | E5/Qwen, blind pool, embeddings candidatos: avanzar sólo con sus precondiciones/autorizaciones separadas y si el objetivo requiere esos claims. |
| Menor / no bloqueante | Complejidad alta, clones, candidatos dead-code; revisar uno por uno sólo con evidencia de uso/impacto, no refactor general. |
| Histórica/resuelta o supersedida | Fixes de TUT-03/H1–H3 y fixes de UI mockeados ya reportados; discrepancias/counters de 048–049 reconciliados documentalmente; bloque de authority interno agotado y búsqueda pública CP072 efectuada con `NOT_RESOLVED`. No reabrir sin evidencia nueva. |
| No-action / fuera de objetivo | No construir clone de NotebookLM, multi-user u offline-only absoluto por inferencia; no añadir frameworks, nueva memoria, ColBERT o graph retrieval sólo por aparecer en roadmaps/recomendaciones. |

## 10. Tres niveles distintos de “terminado”

### PRODUCT COMPLETE

Para decir que TALOS funciona como producto educativo para el objetivo actual,
debe existir una declaración de aceptación de producto acotada y evidencia de
que el flujo de aprendizaje que esa declaración incluye funciona: selección de
currículo/fuentes, respuesta pedagógica ajustada, ejercicio/feedback cuando
corresponda, manejo de continuidad/estado si se reclama, y contrato estable
backend/SSE/UI. El plan actual exige cerrar Gate B, Gate C/F5, Gate D/F6 y las
fronteras sintéticas hasta la integración que se acepte. La evidencia
disponible es parcial; no declarar `PRODUCT_COMPLETE=YES` hoy. Esto no requiere
por sí mismo equivalencia NotebookLM, multi-user, offline-only absoluto,
benchmarks E5/Qwen, BENCH-G2 completo ni A-PRE formal, salvo que el producto
declare esas propiedades como requisitos.

### VALIDATION COMPLETE

Requiere un snapshot PRE identificable y limpio, perímetro reproducible, suite
de cualificación contextualizada, regresión integrada por frontera y
evaluaciones con protocolo/rúbrica válidos para cada claim importante. Para
afirmar mejora pedagógica multi-currículo, PED-F7 debe cerrarse; para ranking,
BENCH-G2 necesita qrels/scope adjudicados y piloto aceptado. La validación
actual es `PARTIAL`; números históricos no son una corrida unificada actual.

### FORMAL ASSURANCE COMPLETE

Requiere resolver authority (identidad, actor/designación, scope, precedence y
relación al snapshot), completar los prerrequisitos del ledger/predicate,
resolver tracing/coverage y unidades UNKNOWN según la regla autorizada,
obtener preflight válido y autorización operacional, ejecutar A-PRE-1 bajo
aislamiento y revisar evidencia/artefactos. A-PRE-0 está `NOT_READY`;
A-PRE-1 no está autorizado. El mapa CP073 no resuelve ni ejecuta estos pasos.

## 11. Dependencias y caminos de cierre

```text
PRODUCT PATH
  decisión explícita de criterios de aceptación del producto
    → Gate B: identidad curricular / fuentes / ACL
    → Gate C / F5: continuidad, provenance, memoria y estado
    → Gate D / F6: adjudicación del contrato terminal
    → B2 contexto sintético → B3 retrieval sintético
    → B4 pipeline con provider fake → B5 HTTP/SSE
    → B6 React↔FastAPI aislado → regresión de los contratos aceptados
    → PRODUCT COMPLETE (sólo para el scope declarado)

VALIDATION PATH (paralelo, claims dependientes)
  PRE snapshot/perimeter reproducible → suite/cualificación
  PED-F7 protocolo → evaluación multi-currículo
  BENCH-G2 scopes/qrels adjudicados → preflight → piloto autorizado
  E5/Qwen runtime candidates → gates de identidad/reproducibilidad/autorización

FORMAL ASSURANCE PATH (independiente del cierre funcional)
  nueva evidencia primaria de autoridad
    → adjudicación posterior de BASELINE_SPEC_AUTHORITY
    → resolver otros gaps A-PRE-0 (coverage, tracing, inventory, predicate)
    → preflight listo + autorización explícita
    → A-PRE-1
    → revisión de artefactos/evidencia
    → FORMAL ASSURANCE COMPLETE
```

Las ramas de validación/experimentación no son prerequisites automáticos para
la rama funcional, salvo cuando la claim de producto depende de sus resultados.
Authority A-PRE tampoco bloquea L2 operacional por sí misma; sí bloquea el
cierre formal cuyo contrato la requiere.

## 12. Trabajo restante

No se estiman plazos. `STATUS` usa la taxonomía de §3; clase de bloqueo e
impacto son dimensiones distintas.

| Tarea | Por qué existe | Dependencia / evidencia de salida | Bloqueo | Impacto producto | Status |
|---|---|---|---|---|---|
| Declarar criterios de PRODUCT COMPLETE y scope de release | No hay una definición única que fusione todas las líneas. | Decisión humana sobre currículos, rutas y claims requeridas; checklist aceptable. | Ninguno técnico; decisión de scope pendiente. | Directo: evita declarar completion ambiguo. | `BLOCKED` |
| Cerrar aceptación Gate B | Claim de selección/aislamiento por currículo. | Identidad canónica, aliases, sources, authority curricular, ACL efectiva; casos positivos/negativos. | Reconciliación/aceptación multi-currículo. | Directo para producto multi-cuaderno. | `PARTIALLY_IMPLEMENTED` |
| Cerrar F5 / Gate C | Claim de continuidad y adaptación con memoria/estado. | Matriz de escenarios aislados para history, provenance, scope, turno actual, intentos parciales y no-mutación BKT. | Aceptación integrada pendiente. | Directo para continuidad reclamada. | `PARTIALLY_IMPLEMENTED` |
| Adjudicar contrato F6 / Gate D | Eventos terminales observados no bastan para especificar el contrato. | Decisión sobre abstention/clarification/truncated/abort/error/EOF y evidencia backend-consumer coherente. | Depende de las decisiones de contrato; no imponer fix por observación. | Directo para chat fiable integrado. | `BLOCKED` |
| Completar B2–B6 controlados | Conectar capas sin usar datos/proveedores productivos. | Fixtures sintéticas/contexto, retrieval, fake provider, route HTTP/SSE, React; guardas y regression. | Orden tras B/C/D; no autoriza lifecycle real. | Directo para demostrar integración acotada. | `PLANNED` |
| Cerrar regresión PRE→POST del producto | Verificar que integración/fixes no rompan el perímetro aceptado. | PRE limpio, salida/hash, suite requerida y condiciones registradas. | Snapshot/worktree no limpio y preflight. | Directo para afirmar estabilidad del release. | `BLOCKED` |
| Cerrar PED-F7 | Afirmar calidad pedagógica en más de un currículo. | Protocolo, currículos/intenciones, fuentes/prompts, rúbrica, umbrales, evaluación y limitaciones. | Preparación y ejecución con gates/privacy aprobados. | Claim de validación, no requisito funcional automático. | `PLANNED` |
| Reabrir benchmark comparativo TALOS–NotebookLM sólo si se requiere | La comparación de 20 preguntas no prueba causalidad/calidad general. | Dataset/versiones/prompts/fuentes equivalentes, control/ciego, rúbrica; autorización de datos. | Protocolo + autorización futura. | Opcional para producto; necesario para claim comparativo. | `BLOCKED` |
| Adjudicar BENCH-G2 si se quieren claims de retrieval | Qrels/scopes no están listos como evidencia canónica. | Decisiones por query y qrel, dataset versionado, fixtures y piloto autorizado. | Cola humana y gates de ejecución. | No bloquea producto funcional sin claim de ranking. | `BLOCKED` |
| Resolver runtime E5/Qwen si se adoptan candidates | Hoy son tracks experimentales no establecidos como runtime obligatorio. | E5 Path A factibilidad + dos reconstrucciones; Qwen provenance/runtime independiente; autorización de harness. | Gates de runtime/artifacts. | No bloquea producto core según evidencia actual. | `BLOCKED` |
| Completar formal A-PRE-0/A-PRE-1 si se requiere assurance | La especificación/ledger exige autoridad y evidencia vinculada. | Fuente primaria authority, gaps §7, tracing host capable, predicate/units, autorización A-PRE-1 y artefactos verificables. | `AUTHORITY_UNRESOLVED`; otros gaps A-PRE; A-PRE-1 no autorizada. | Formal assurance; no toda función TALOS. | `BLOCKED` |
| Remediar candidatos Reality Audit | Medidas estáticas no demuestran defectos ni dead code. | Adjudicación individual por evidencia de ejecución/uso/impacto y decisión humana. | No hay cambio aceptado ni evidencia de impacto. | En general mantenimiento/calidad; no gate de producto por conteos. | `PLANNED` |

## 13. Done, remaining, blocked, optional e histórico

### DONE (alcance específico demostrado/documentado)

- Línea base documental PED-F0 de 20 preguntas y su procedencia/límites.
- Fixes PED-F1…F4/H1–H3 y políticas de solución reportados implementados con
  pruebas locales dentro de su alcance.
- B0/B0.5/B1-A/B1-B y B1-R cerrados como observaciones/harnesses sintéticos
  acotados; B1-R `TECHNICAL PASS`.
- Crosswalk y reconciliación descriptiva de las 385 filas documentados en
  CP055–058; no se cambiaron las 385 disposiciones.
- Investigación de autoridad externa CP072 ejecutada según autorización,
  resultado `NOT_RESOLVED`.

### REMAINING (para producto/validación)

- Definir un scope verificable de producto terminado.
- Aceptar Gate B, F5/Gate C y F6/Gate D para las claims que constituyen el
  release funcional actual.
- Completar integración por B2–B6 y una regresión de snapshot limpia.
- Completar PED-F7 si se afirmará validación de calidad multi-currículo.
- BENCH-G2 sólo si se afirmarán métricas de ranking/retrieval comparativo.

### BLOCKED

- Autoridad de baseline y cierre formal A-PRE-0: CP072 `NOT_RESOLVED`;
  `f058…` sigue no recuperado.
- A-PRE-1: no autorizado/no ejecutado y prerrequisitos técnicos sin resolver.
- E5/Qwen, benchmark ampliado y blind pool: sólo avanzar con sus gates y
  autorizaciones específicas.

### OPTIONAL

- Benchmark TALOS vs NotebookLM con protocolo nuevo.
- E5/Qwen, blind pool, late chunking/ColBERT/graph retrieval si una decisión
  futura los convierte en objetivos.
- Refactor/cleanup de clones, complejidad/dead-code candidates después de
  evidencia y decisión.

### HISTORICAL / NO LONGER REQUIRED

- No repetir el setup o análisis de la misma comparación de 20 preguntas, ni
  presentarla como prueba causal.
- No repetir B0.5/B1-R/CP051–CP072 ni la arqueología interna ya cerrada salvo
  evidencia nueva o cambio de scope.
- No trasladar los roadmaps antiguos (offline-only absoluto, 300–500 queries,
  ColBERT, nuevos motores) a requisitos del release por su sola presencia.
- No reabrir fixes de benchmark ya incorporados como backlog separado.
- No inferir trabajo por los conteos históricos de tests; se requiere nueva
  baseline si se quiere un resultado vigente.

## 14. Respuesta a “¿qué falta realmente para terminar TALOS?”

| Categoría | Qué falta / puede quedar fuera |
|---|---|
| Necesario para producto | Acordar criterios de cierre y demostrar los flujos aceptados: Gate B (si multi-cuaderno), F5/Gate C (si continuidad/adaptación), F6/Gate D y la integración controlada/regresión correspondiente. Esas fronteras son las brechas funcionales actuales en el plan de cierre. |
| Necesario para validación | PRE reproducible/clean y pruebas contextualizadas; PED-F7 para claims de calidad multi-currículo; BENCH-G2 sólo para claims de ranking. Evidencia histórica no equivale a corrida actual. |
| Necesario para garantía formal | Resolver autoridad baseline y los demás blockers A-PRE; sólo entonces preflight/permiso/ejecución formal y revisión. A-PRE-1 no se ejecuta ahora. |
| Opcional | Comparativa nueva, E5/Qwen, blind pool, roadmap retrieval v1.1 y purificación estática, salvo adopción explícita de esos objetivos. |
| Bloqueado | Formal A-PRE por authority unresolved y gaps técnicos; E5/Qwen/benchmarks por prerequisitos/autoridad/autorizaciones específicas. |
| No necesario por evidencia actual | Ser clon de NotebookLM, soportar multi-user como requisito, garantizar offline-only absoluto o implementar toda idea de roadmap. |

**Si mañana quisiéramos cerrar TALOS, sin hacer trampa**, tendríamos que
primero fijar qué scope de producto se está cerrando; luego cerrar y verificar
las fronteras funcionales Gate B, F5/Gate C y F6/Gate D que ese scope promete,
integrarlas por la ruta sintética B2–B6 y producir una regresión PRE/POST
reproducible. Si se afirma calidad pedagógica multi-currículo, habría que
completar PED-F7; si se afirma ranking, BENCH-G2. Para decir que TALOS tiene
garantía formal de aislamiento, además habría que resolver authority y los
bloqueos de A-PRE-0, obtener autorización operacional y completar A-PRE-1.
Podemos dejar fuera sin engaño el clon de NotebookLM, el requisito
multi-user, offline-only absoluto, E5/Qwen y purificación por métricas estáticas
si no se declaran como promesas del producto. Lo que no podemos hacer es
presentar una evidencia sintética, un contador histórico o código presente
como aceptación integrada o certificación actual.

## 15. Fuentes y trazabilidad del mapa

Este mapa consolida, sin sustituirlos, los documentos rectores vigentes y
evidencias históricas:

- Producto/capacidades: `README.md`, `docs/CAPABILITIES.md`,
  `docs/ARCHITECTURE.md`, `docs/PLAN_MEJORA_PEDAGOGICA_TALOS.md`.
- Comparación/fixes: `docs/FASE0_LINEA_BASE_TALOS_NOTEBOOKLM.md`,
  `docs/DIAGNOSTICO_MULTICUADERNO_Y_PLAN_DE_CONTINUIDAD.md`,
  `docs/PLAN_SUITE_FIX_ESTABILIZACION.md`.
- Runtime/gates: `docs/BACKEND_OPERATIONAL_ARCHAEOLOGY.md`,
  `docs/B1R_ACCEPTANCE_CONTRACT.md`, `docs/TEST_CERTIFICATION_PERIMETER.md`,
  `docs/REALITY_AUDIT_REPORT.md`, `docs/REALITY_AUDIT_PURIFICATION_BACKLOG.md`.
- Benchmarks/runtimes: `docs/GATE2_BENCHMARK_SCOPE_RUNBOOK.md`,
  `docs/E5_RUNTIME_CANDIDATE_DECISION.md`,
  `docs/EMBEDDING_EXECUTION_PREREQUISITES_RESOLUTION_GATE.md` y gates blind pool.
- A-PRE: checkpoints CP050–CP072, en especial CP065, CP070, CP071, CP072,
  además del manifest/ledger que mantienen su estado canónico sin modificación.

No se inspeccionaron bases de datos, corpus, modelos, índices ni contenido de
transcripciones externas. No se ejecutaron TALOS, tests, benchmarks, workloads,
probes, FastAPI, VM ni A-PRE-1.
