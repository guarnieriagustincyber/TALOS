# Checkpoint 073 — mapa maestro y camino restante de TALOS

Fecha: 2026-10-01

## Resultado ejecutivo

```text
PRODUCT_STATUS = IMPLEMENTED_CORE_WITH_OPEN_ACCEPTANCE
VALIDATION_STATUS = PARTIAL
FORMAL_ASSURANCE_STATUS = NOT_COMPLETE

TOTAL_REMAINING_WORKSTREAMS = 12
PRODUCT_BLOCKERS = 6 (dependen del scope/claims de producto acordado)
VALIDATION_BLOCKERS = 4 (dependen de las claims de validación)
FORMAL_BLOCKERS = 1 (A-PRE; incluye dependencias externas y técnicas)
HISTORICAL_ITEMS = 5 grupos de trabajo cerrados en su alcance
NO_LONGER_REQUIRED_ITEMS = 4 grupos fuera del objetivo actual por evidencia disponible

NEXT_CRITICAL_PATH =
  fijar criterios de cierre de producto
  → Gate B / F5-Gate C / decisión F6-Gate D
  → B2–B6 controlados
  → regresión de snapshot reproducible
```

## Fuente maestra y decisión de no duplicar

Ya existía un documento integrado vigente enlazado desde README:
`docs/PLAN_MAESTRO_CIERRE_TALOS.md`. Por ello se actualizó ese documento para
que funcione como mapa maestro al corte CP073, en lugar de crear una segunda
copia paralela en `docs/MASTER_TALOS_STATUS_AND_REMAINING_PATH.md`. El README
ahora enlaza al master actualizado; el corte del 2026-09-30 permanece marcado
como histórico dentro del mismo documento.

## Estado de entrada e invariantes

Base observada: `HEAD=f81134fc2293916210d53c8065f3a0049e52b0b4`, worktree
preexistente no limpio. La inspección fue documental y estática. No se
ejecutaron TALOS, FastAPI, tests, probes, benchmarks, workloads, VM, A-PRE-1,
ni operaciones sobre DB/corpus/modelos/índices.

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

CP072 agotó la búsqueda pública permitida sin resolver authority. Sus
resultados `NOT_FOUND` no prueban `PROVEN_ABSENT`; no se repitió su
investigación.

## Producto, validación y garantía formal

- **Producto:** motor educativo/tutor basado en evidencia para currículo
  técnico/ciberseguridad, con rigor, adaptación pedagógica, práctica y
  protección de evaluación. El core está implementado; no se ha demostrado la
  aceptación integrada completa de los flujos que el producto promete.
- **Validación:** parcial. Hay pruebas unitarias/documentadas y probes
  sintéticos con alcances delimitados. No equivalen a una corrida actual
  completa, al flujo backend/UI real ni a evaluación pedagógica multi-currículo.
- **Garantía formal:** incompleta. A-PRE-0 sigue `NOT_READY`; A-PRE-1 no está
  autorizado ni ejecutado. La authority irresuelta bloquea el cierre formal
  que depende del baseline, pero no todo TALOS ni cada observación operacional.
- **“Terminado”:** las fuentes no fijan un único gate que fusione producto,
  validación y assurance. CP073 los mantiene separados y exige fijar el scope
  de release antes de emitir un cierre binario.

## Mapa funcional y estados

Las clasificaciones siguientes corresponden a las definiciones de §3 del
documento maestro. `PRODUCTION_USED` significa “evidencia explícita de uso
productivo”; que no aparezca en el expediente se interpreta como “no
demostrado”, no como prueba de no uso.

| Área | Estado resumido | Evidencia / límite determinante |
|---|---|---|
| BKT / SM-2 / KC | Implementados con tests locales; aceptación integrada de continuidad/estado incompleta. | Suites BKT, spaced repetition y KC existen; F5/Gate C y Gate B siguen abiertos. |
| Ejercicios adaptativos, MultiKC, BugSpotter y Trace Tables | Implementados con oráculos y casos acotados; `DONE_WITH_KNOWN_LIMITATION` o `IMPLEMENTED_NOT_FULLY_VALIDATED` según componente. | No prueban corrección pedagógica general ni validación en todos los currículos. |
| Struggle Mode, hints, fading, abstención, citas, anti-leakage y Forensic Audit | Controles/componentes implementados; validación amplia incompleta. | Tests focalizados y docs no generalizan a proveedor, currículo ni todos los paths de integración. |
| FTS5, retrieval léxico, QueryRewriter, AdaptiveRouter, Fabric y reranker local | Componentes y tests acotados disponibles. | La calidad end-to-end requiere scopes/qrels y corpus versionados; BENCH-G2 permanece pausado. |
| Embeddings, Jina, E5/Qwen | Backends/candidates con integración o configuración documentada, no runtime completo aceptado. | E5 Path A y Qwen mantienen gates independientes; no se demostró que sean dependencia del runtime productivo actual. |
| ContextPack, CandidatePooler, PresentationFilter y trazabilidad | Implementación presente y tests aislados. | Dependencias de identidad/scope y evidence real no cerradas de extremo a extremo. |
| Persona/style routing, Session Memory/Mem0 y Context Builder | Implementación parcial/extendida. | F5 debe validar procedencia, precedencia de turno, scope, contaminación y no-mutación BKT. |
| FastAPI, SSE y React | Ruta backend y cliente probados sólo por superficies separadas y/o mocks sintéticos. | B1-A/B1-B/B1-R no son una integración real React↔FastAPI ni certifican lifecycle normal. |
| SQLite/persistence, provider registry, circuit breaker/config/runtime | Infraestructura presente. | Container normal accede a stores/corpus; el modo mock no prueba aislamiento. La aceptación operativa está pendiente. |
| Multi-user, clon NotebookLM, offline-only absoluto | `NOT_REQUIRED` para el cierre bajo el objetivo actual revisado. | No aparecen como requisitos vigentes de cierre. Offline-capable/local-first sí aparece como principio, no implica que todas las rutas sean offline. |

El documento maestro contiene la matriz detallada por capacidad, incluyendo
implementación, evidencia, límites, dependencias y un estado único. La
presencia de código no se eleva a `DONE_VERIFIED`.

## Gates y dependencias relevantes

| Grupo | Resultado registrado | Lo que falta | Clase |
|---|---|---|---|
| B0 / B0.5 / B1-A / B1-B | Arqueología y observaciones sintéticas cerradas en sus scopes. | No generalizar a lifecycle, stores, provider o cliente real. | Históricos |
| B1-R | `TECHNICAL PASS` en harness repetible documentado. | No es F6 PASS ni A-PRE readiness. | Histórico acotado |
| Gate B / ESTAB-G2 | H1–H3 corregidos localmente; fixtures de identidad y retrieval. | Aceptar identidad curricular, fuente/ACL y comportamiento multi-cuaderno. | Producto condicional |
| F5 / Gate C | Piezas de memoria/historial/provenance implementadas. | Matriz de aceptación con stores aislados y no-mutación correcta de BKT. | Producto condicional |
| F6 / Gate D | Evento SSE observado sintéticamente; cliente mock maneja algunos outcomes fail-closed. | Adjudicar contrato terminal y validar coherencia ruta→SSE→cliente. | Producto/integración |
| B2–B6 | Plan de integración controlada por fronteras. | Contexto, retrieval, pipeline fake, HTTP/SSE, UI y regresión. | Producto/integración |
| PED-F7 | Pendiente. | Protocolo, rúbrica, currículos y evaluación reproducible. | Validación |
| A-PRE-0 / A-PRE-1 | `NOT_READY` / `NOT_AUTHORIZED / NOT_EXECUTED`. | Autoridad, inventory/outcomes, coverage/tracing, predicate, preflight y autorización operativa. | Formal assurance |
| BENCH-G2 | Pausado/no canónico. | Adjudicación humana de scopes/qrels y gates de piloto. | Benchmark |
| E5 / Qwen / blind pool | Candidates experimentales con prerequisites y autorizaciones propias. | Reproducibilidad, provenance y gates de ejecución correspondientes. | Opcional/benchmark |
| Reality Audit | Métricas de clones/complexity/dead candidates. | Adjudicación individual antes de cualquier cambio. | Opcional/mantenimiento |

## Cronología post-v1.0-elite

1. **v1.0-elite.1:** los docs CAPABILITIES/ARCHITECTURE registran un corte
   histórico de release y pruebas; sus conteos no son estado de CP073.
2. **PED-F0 / comparación 20 preguntas:** línea base de transcripciones con
   limitaciones de alineación/versionado. Sirve para análisis, no para scoring
   causal ni aprendizaje.
3. **PED-F1…F4 y TUT-03/H1–H3:** fixes de formato, perfiles, política de
   soluciones y fallbacks ya reportados con tests locales; no quedan como una
   lista independiente de fixes pendientes.
4. **F5/F6:** aparecen implementaciones y correcciones SSE/memoria; la
   aceptación continúa abierta en los límites expresamente registrados.
5. **Reality Audit y B0–B1-R:** observaciones estáticas/sintéticas por
   frontera, incluida la repetibilidad B1-R; ninguna equivale a integración o
   certificación global.
6. **A-PRE CP050–058:** crosswalk/provenance/contadores y estado de 385 rows se
   consolidaron descriptivamente; no se cambió disposition.
7. **CP059–072:** separación evidencia/decisión, bloqueo formal y búsqueda
   externa autorizada `NOT_RESOLVED`; la authority sigue abierta.
8. **CP073:** correlaciona esas líneas y define caminos restantes sin
   implementar ni reabrir investigación.

## Qué significa cierre y camino crítico

```text
PRODUCT COMPLETE
  criterios de release
  → Gate B → F5/Gate C → decisión F6/Gate D
  → B2/B3/B4/B5/B6 controlados → regresión reproducible

VALIDATION COMPLETE
  PRE/perímetro reproducible
  + PED-F7 para claims pedagógicas multi-currículo
  + BENCH-G2 sólo si claims de ranking lo requieren

FORMAL ASSURANCE COMPLETE
  autoridad baseline
  → demás gaps A-PRE-0 (inventory, coverage, tracing, predicate)
  → preflight y autorización
  → A-PRE-1 → revisión de resultados/artefactos
```

La rama formal no es dependencia automática de la rama funcional educativa.
No afirmar assurance formal sin ella; no detener todo producto funcional por
un blocker limitado a assurance.

## Trabajo restante enumerado

| # | Trabajo | Dependencia/evidencia de salida | Impacto | Estado |
|---:|---|---|---|---|
| 1 | Acordar criteria y scope de PRODUCT COMPLETE | Decisión de release y rutas/claims incluidas. | Producto | `BLOCKED` |
| 2 | Cerrar aceptación Gate B | Identidad, curriculum, source/ACL y casos multi-cuaderno. | Producto para claims multi-currículo | `PARTIALLY_IMPLEMENTED` |
| 3 | Cerrar F5/Gate C | Continuidad, provenance, memoria, scope, BKT. | Producto para claims longitudinales | `PARTIALLY_IMPLEMENTED` |
| 4 | Adjudicar F6/Gate D | Contrato SSE terminal y consumer coherente. | Producto para chat integrado fiable | `BLOCKED` |
| 5 | Completar B2–B6 sintéticos | Integración gradual context/retrieval/pipeline/HTTP/UI. | Producto integrado | `PLANNED` |
| 6 | Regresión sobre PRE/snapshot limpio | Perímetro, artefactos y reportes reproducibles. | Producto/validación | `BLOCKED` |
| 7 | Completar PED-F7 si se afirma calidad multi-currículo | Protocolo, rúbrica, evaluación reproducible. | Validación | `PLANNED` |
| 8 | Repetir comparación sólo con nuevo protocolo si se requiere | Versiones, prompts, fuentes, ciego y autorización de datos. | Claim comparativo opcional | `BLOCKED` |
| 9 | Adjudicar BENCH-G2 si hay claims de ranking | Scopes/qrels, dataset versionado y piloto autorizado. | Benchmark | `BLOCKED` |
| 10 | Resolver E5/Qwen si se adoptan como runtime | Gates de runtime/provenance/harness con autorización específica. | Experimental/benchmark | `BLOCKED` |
| 11 | Completar assurance formal A-PRE | Authority + gaps técnicos + autorización de A-PRE-1. | Formal | `BLOCKED` |
| 12 | Adjudicar candidatos de Reality Audit antes de remediar | Evidencia de uso/impacto por candidato y decisión. | Mantenimiento | `PLANNED` |

### Done

- Fixes PED-F1…F4/H1–H3 y protección de soluciones en el alcance reportado.
- Observaciones B0–B1-R dentro de los límites de sus probes/harnesses.
- Crosswalk/reconciliación descriptiva de 385 filas en CP055–058.
- Investigación externa CP072, concluida `NOT_RESOLVED`.

### Histórico o no requerido

- No repetir la comparación PED-F0 como si fuera evaluación nueva ni como
  evidencia causal.
- No rehacer B0–B1-R o CP051–CP072 salvo evidencia nueva/cambio de scope.
- No asumir que roadmap v1.1, 300–500 queries, ColBERT, multi-user,
  NotebookLM clone u offline-only son requisitos de release actuales.
- No reabrir fixes ya incorporados como trabajo separado.
- No borrar/refactorizar candidatos de auditoría por métricas estáticas.

## Respuesta final

Para cerrar TALOS con el objetivo educativo actual hacen falta criterios de
release explícitos, aceptación de las fronteras funcionales prometidas
(Gate B, F5/Gate C, F6/Gate D), integración controlada B2–B6 y una regresión
reproducible. Para afirmar calidad validada multi-currículo se agrega PED-F7;
para ranking, BENCH-G2 adjudicado. Para afirmar garantía formal se requiere
resolver authority y cerrar A-PRE-0/A-PRE-1 bajo gates y autorizaciones
separados. Se pueden dejar fuera clon NotebookLM, multi-user, offline-only
absoluto, E5/Qwen, blind pool y purificación estática si no se declaran como
claims/requisitos del producto. La autoridad A-PRE unresolved no significa
“todo TALOS bloqueado”, y el código/historial de pruebas tampoco permite
declarar hoy que todo esté integrado o terminado.
