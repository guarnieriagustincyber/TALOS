# TALOS V1.5 — checkpoint canónico de continuidad

**ID:** `TALOS-V15-CHECKPOINT-2026-10-13`
**Corte:** 2026-10-13; registro de continuidad, no aceptación ni release.
**Repositorio:** `/media/agustin/Laboratorio/study-engie`
**Git verificado por consultas de solo lectura:** rama `talos-current-audit`; HEAD `032339436639d33d310c437c88fe01d94e977449`; worktree **dirty**, con cambios rastreados y no rastreados. Este documento nuevo también queda no rastreado hasta una decisión Git posterior. No hubo cambio de rama, reset, limpieza ni commit.

## 1. Identidad y alcance

TALOS (KASIU / Study Engine) es un sistema personal de estudio de ciberseguridad basado en evidencia: corpus y retrieval con provenance, generación sometida a auditoría, evaluación pedagógica determinista, BKT/SM-2, estado de sesión y transporte HTTP/SSE con interfaz web. La arquitectura relaciona contratos curriculares y de fuentes, almacenamiento SQLite/FTS5 y vectores, retrieval, auditoría S4.4, orquestación pedagógica, ledger/estado y UI. El principio rector es **“Deterministic code first. AI second.”** El agente trabaja sobre TALOS; no sustituye las autoridades de verdad, progreso, aislamiento ni release ([AGENTS.md](../../AGENTS.md)).

V1.5 busca completar las capacidades y gates estipulados sin reducir su alcance unilateralmente. El cierre de una fase documental, un paquete focal o una prueba sintética no equivale a aceptación global. La versión histórica `v1.0-elite` es una línea base distinta, no una certificación transferible a V1.5.

## 2. Fuentes rectoras y procedencia

| Fuente | Ubicación y condición | Alcance / cautela |
|---|---|---|
| Core normativo | [AGENTS.md](../../AGENTS.md), archivo rastreado | Autoridad, fail-closed, límites y no-escalada de evidencia. |
| Mapa operativo de cierre | [PLAN_MAESTRO_CIERRE_TALOS.md](../PLAN_MAESTRO_CIERRE_TALOS.md), archivo rastreado pero modificado localmente | P0–P3; su portada observada está fechada 2026-10-07 y refiere otro HEAD. **No es** el plan T01–T20. |
| Especificación/roadmap metodológico V1.5 | [ROADMAP_V1_5_MASTER.md](../ROADMAP_V1_5_MASTER.md), rastreado y modificado; [TALOS_ROADMAP_V1_V1_5_V2.md](../TALOS_ROADMAP_V1_V1_5_V2.md), rastreado y modificado; [ROADMAP_INTEGRAL_TALOS.md](../ROADMAP_INTEGRAL_TALOS.md), no rastreado | Fases metodológicas, fronteras V1/V1.5/V2 y estados históricos. No sustituyen una nueva adjudicación del checkout. |
| Informe maestro histórico de continuidad | [INFORME_CONTINUIDAD_HANDOFF_TECH_LEAD.md](../audits/INFORME_CONTINUIDAD_HANDOFF_TECH_LEAD.md), rastreado | Handoff de septiembre de 2026; sus cifras y certificados son históricos, no revalidados aquí. |
| Contratos documentales Gate B | [STEP-28](../STEP-28-DESARROLLO-DOCUMENTAL-NORMATIVO-DE-CONTRATOS-B1-B8.md) y [STEP-46](../STEP-46-ACTA-FINAL-DE-CIERRE-DOCUMENTAL-Y-CONTROL-DE-EVIDENCIA.md), archivos físicos no rastreados | Especificación y cierre **documental** con brechas, no Gate B aceptado. |
| Plan Maestro de Finalización V1.5 de **20 paquetes T01–T20**, enmienda de ejecución y auditoría integral de consolidación | **Antecedentes aportados en la conversación; no se localizaron como archivos físicos verificables en las rutas documentales inspeccionadas.** | Se conservan sus identificadores, dependencias comunicadas y decisiones del responsable; no se atribuyen a un archivo o commit inexistente. Antes de usar nombres/criterios completos de cada paquete, recuperar el texto autorizado. |

No confundir “el documento menciona un informe” con “el informe fue recuperado”. Las fuentes físicas anteriores se inspeccionaron selectivamente; no se reprodujeron sus experimentos.

## 3. Historia preservada, sin reapertura

| Hito | Estado conservado y límite | Fuente física |
|---|---|---|
| Fase 1A | Cierre experimental de PDF→corpus; 242 juicios humanos consolidados en ese piloto; no selección productiva ni generalización demostrada. | [CP131](../../checkpoints/131-fase-1a-final-synthesis.md) |
| Fase 1B | Cierre canónico de corpus→evidencia y adjudicación focal de relevancia/suficiencia; no sustituye el producto completo. | [CP140](../../checkpoints/140-reconciliacion-canonica-fase-1b.md) |
| Fase 1C | Frontera corpus↔runtime adjudicada en su scope; no prueba todos los recorridos presentes del checkout. | [CP142](../../checkpoints/142-fase-1c-ejecucion-frontera-corpus-runtime.md) |
| Fase 1D | Benchmark y adjudicación reconciliados/cerrados en el alcance experimental. | [CP145-R1](../../checkpoints/145-r1-reconciliacion-dictamen-fase-1d.md) |
| Fase 1E / síntesis | Gate de promoción cerrado: `PHASE_1_PROMOTABLE = FALSE`; ningún candidato denso promovido; C0/FTS5 retenido. | [CP146-R1](../../checkpoints/146-r1-phase-1e-promotion-gate.md), [CP147](../../checkpoints/147-fase-1-sintesis-global-y-cierre-canonico.md) |
| F2A-012 | Alcance técnico focal cerrado; C-03d sigue reservado para decisión contractual independiente. | [Expediente F2A-012](../expedientes/F2A-012-EXPEDIENTE-CANONICO.md) |
| B06 / B10 | B06: `FOCAL_EXECUTION_VALIDATED`; B10: `PARTIALLY_VERIFIED`, sin transcript primario completo de siete nodeids. Ninguno cierra P1.2. | [F-11](../F-11-POST-WORKER-B06-ADJUDICATION.md), [F-12](../F-12-RECUPERACION-EVIDENCIA-B10-Y-RECONCILIACION-DE-BLOQUEOS.md) |
| STEP-28 / STEP-46 | Contratos B1–B8 desarrollados documentalmente; ciclo documental cerrado con limitaciones; Gate B incompleto. | [STEP-28](../STEP-28-DESARROLLO-DOCUMENTAL-NORMATIVO-DE-CONTRATOS-B1-B8.md), [STEP-46](../STEP-46-ACTA-FINAL-DE-CIERRE-DOCUMENTAL-Y-CONTROL-DE-EVIDENCIA.md) |
| `v1.0-elite` / CP127 | Cierre histórico V1; separado de implementación y aceptación V1.5. | [CP127](../../checkpoints/127-v1-release-integrity.md) |

Los expedientes AUDIT-014–AUDIT-028 y sus adjudicaciones G1/G2 constan como antecedentes conversacionales en este corte; no se localizaron aquí como un conjunto físico completo. Conservar sus estados indicados abajo, sin atribuir una nueva revisión independiente.

## 4. Paquetes implementados recientemente

| Paquete | Implementación y evidencia focal | Límite de cierre |
|---|---|---|
| **T01 — Identidad del informe S4.4** | Implementación completada. **50 tests focales PASS** en la ejecución autorizada anterior. | El perímetro de imports no se verificó completamente: la inicialización web efectuó dos llamadas `mkdir(exist_ok=True)` sobre `src/study_engine/web/static/` y `kasiu-lab/storage/`. T15 debe adjudicar esos efectos. `T01 = IMPLEMENTED_PENDING_VALIDATION`; no cierra P1.2. Código relevante: [generation_adapter.py](../../src/study_engine/audit/generation_adapter.py), [structured_pipeline.py](../../src/study_engine/pedagogy/structured_pipeline.py), [chat.py](../../src/study_engine/web/routes/chat.py); tests: [test_audit_verdict_honesty.py](../../tests/unit/pedagogy/test_audit_verdict_honesty.py), [test_generation_adapter.py](../../tests/unit/audit/test_generation_adapter.py). |
| **T04 — Identidad ejercicio/KC** | Implementación completada; **32 tests focales PASS** bajo entorno temporal. Valida identidad/tipo/opciones de la fuente del servidor antes de BKT/SM-2/ledger en las rutas focales. | Integración de `exercise_id` en [ChatMessages.tsx](../../kasiu-lab/ui/src/presentation/features/chat/components/ChatMessages.tsx) pendiente de T12; no hay aceptación integrada. Código: [dialogue.py](../../src/study_engine/web/routes/dialogue.py), [exercise_store.py](../../src/study_engine/pedagogy/exercise_store.py), [generated_registry.py](../../src/study_engine/pedagogy/generated_registry.py), [chat.py](../../src/study_engine/web/routes/chat.py); tests: [test_socratic_ux_and_dialogue.py](../../tests/unit/pedagogy/test_socratic_ux_and_dialogue.py), [test_t04_exercise_identity.py](../../tests/unit/web/test_t04_exercise_identity.py). |
| **T07 — Identidad vectorial** | Implementación completada. Primera ejecución: **25 PASS / 3 FAIL**; defecto de retorno en `DenseRetriever.retrieve` corregido en T07-R1; segunda ejecución única: **28 PASS / 0 FAIL**. Identidades incompatibles y `UNKNOWN` rechazadas en los escenarios focales; fallback FTS5 sintético aprobado. **No sumar ambas ejecuciones como 53 tests actuales aprobados.** | Baseline C0 completo e integración productiva pendientes; índices legacy no migrados, candidato denso no promovido. Código: [vector_identity.py](../../src/study_engine/retrieval/vector_identity.py), [vector_store.py](../../src/study_engine/retrieval/vector_store.py), [embedding.py](../../src/study_engine/retrieval/embedding.py), [indexer.py](../../src/study_engine/retrieval/indexer.py), [dense.py](../../src/study_engine/retrieval/dense.py), [knowledge_store.py](../../src/study_engine/storage/knowledge_store.py). Tests: [test_t07_vector_identity.py](../../tests/unit/retrieval/test_t07_vector_identity.py), [test_dense.py](../../tests/unit/retrieval/test_dense.py), [test_indexer.py](../../tests/unit/retrieval/test_indexer.py), [test_numpy_blas_vector_search.py](../../tests/unit/retrieval/test_numpy_blas_vector_search.py). |

Los recuentos anteriores proceden de ejecuciones focales de la sesión, no de una suite integral ni de una certificación independiente de aislamiento. El worktree dirty contiene código y tests todavía sin versionar; el HEAD por sí solo no reproduce T01/T04/T07.

## 5. Plan T01–T20 conservado y secuencia enmendada

El plan de 20 paquetes y su enmienda **no están físicamente recuperados** en este corte. El siguiente cuadro preserva solo nombres/dependencias comunicados; “pendiente de conciliación” no significa que no exista código previo.

| ID | Estado de continuidad verificable en este corte |
|---|---|
| T01 | Implementado; 50 PASS focales; perímetro/imports pendiente de T15. |
| T02 | Pendiente de conciliación con el texto íntegro del plan; no declarar completo. |
| T03 | Pendiente de conciliación con el texto íntegro del plan; no declarar completo. |
| T04 | Implementado; 32 PASS focales; UI/T12 e integración pendientes. |
| T05 | Pendiente; no incluido en la autorización T04. |
| T06 | Pendiente; requiere base de persistencia **T13a** antes de validación integrada; no abrir por inferencia. |
| T07 | Implementado; 28 PASS en la segunda ejecución focal; integración y C0 completo pendientes. |
| T08 | Pendiente; próximo paquete bajo revisión de nueva propuesta de ingesta. Sin autorización de implementación/ejecución en este checkpoint. |
| T09 | Pendiente; reconciliar con T08 y propuesta multimodal sin alterar corpus actual. |
| T10 | Pendiente; no adelantar implementación antes de dependencias **T08/T14**. |
| T11 | Pendiente; integración de historiales/progreso después de base **T13** pertinente. |
| T12 | Pendiente; incluye integración UI de `exercise_id` de T04. |
| T13 | Desglosado **T13a → T06 → T13b** para eliminar dependencia circular. |
| T14 | Pendiente/partes independientes de runtime/API pueden prepararse conforme al plan autorizado, no por este checkpoint. |
| T15 | Preparación documental de aislamiento puede avanzar en paralelo; efectos de import T01 y perímetro de validación pendientes. |
| T16 | Integración/aceptación progresiva **T16a–T16d**, no una sola corrida monolítica. |
| T17 | Fase metodológica restante; alcance/criterios íntegros pendientes de consultar en el plan no localizado. |
| T18 | Hitos internos **T18a–T18c**; no equivalen a capacidad aceptada por el solo cierre del expediente. |
| T19 | Hitos internos **T19a–T19c**; misma separación entre investigación y capacidad de producto. |
| T20 | Cierre final; pendiente de integración, gates y aceptación humana, sin release inferido. |

Dependencias corregidas comunicadas: **T13a → T06 → T13b**; T10 no se implementa antes de T08/T14; T11 espera la base T13; T15 documental corre en paralelo; T16/T18/T19 se fraccionan como se indica. Esta tabla **no sustituye** los criterios completos del plan T01–T20. No marcar BKT/SM-2, corpus, embeddings, benchmarks, Gate B, F5/Gate C, F6/Gate D, P2 o P3 como opcionales por inferencia.

## 6. Gates, autorizaciones y decisiones

```text
G0 = DOCUMENTALLY_CLOSED_WITH_LIMITATIONS
G1 = APPROVED_DOCUMENTALLY  # contrato, no eficacia de contención
G2 = NOT_APPROVED
G3 = NOT_AUTHORIZED
G5 = NOT_AUTHORIZED
DEC-A06 = PENDING_HUMAN_DECISION
P1.2 = OPEN
B1-R = FAIL
RELEASE = NOT_AUTHORIZED
```

`DialogueEngine` sigue como ruta independiente provisional en el inventario; su canonicalidad productiva no está demostrada ni DEC-A06 resuelta. Las autorizaciones **focales** de modificación/ejecución T01, T04 y T07 y el retest T07-R1 fueron consumidas en sus alcances. No aprueban G3/G5 globales, P1.2 ni release. El documento [STEP-46](../STEP-46-ACTA-FINAL-DE-CIERRE-DOCUMENTAL-Y-CONTROL-DE-EVIDENCIA.md) registra `B1-R = NOT AUTHORIZED` en su corte histórico; el resultado posterior `B1-R = FAIL` proviene del expediente posterior informado en la conversación. Conservar la diferencia temporal, no fusionarla silenciosamente.

## 7. Punto exacto de continuidad

El desarrollo está **pausado antes de T08/T09**. El responsable aportará una nueva estrategia de ingesta de PDF en Google Colab con extracción multimodal, embeddings y modelos generativos. Debe reconciliarse con T08/T09 y sus dependencias sin repetir la auditoría integral ni descartar el plan T01–T20. El responsable considera insuficiente el corpus actual; **no existe todavía una medición integral recuperada en este corte que cuantifique su deterioro**. La propuesta no autoriza reemplazo de corpus, promoción densa, ejecución Colab/rclone, red ni migraciones. La restricción histórica de Colab en el [plan operativo](../PLAN_MAESTRO_CIERRE_TALOS.md) requiere adjudicación explícita antes de cualquier operación; este checkpoint no la levanta.

## 8. Preservación Git y reproducibilidad

No hay staging previo (`git diff --cached --name-only` vacío al inspeccionar). El diff de [chat.py](../../src/study_engine/web/routes/chat.py) contiene múltiples hunks de trabajos anteriores además del cambio T04; otros archivos compartidos y [tests/conftest.py](../../tests/conftest.py) también están modificados. [vector_identity.py](../../src/study_engine/retrieval/vector_identity.py), [test_t07_vector_identity.py](../../tests/unit/retrieval/test_t07_vector_identity.py), [test_t04_exercise_identity.py](../../tests/unit/web/test_t04_exercise_identity.py) y [test_generation_adapter.py](../../tests/unit/audit/test_generation_adapter.py) son no rastreados relevantes. Su omisión impediría reproducir plenamente los paquetes correspondientes. Existen, además, documentos no rastreados y cambios ajenos, artefactos generados `graphify-out/` y recursos operativos que **no** deben incorporarse por una operación indiscriminada.

**Selección de commit de código: pendiente de revisión por archivo y por hunk**; no se hizo `git add`, commit, tag ni push. Un eventual commit solo de este documento preservaría decisiones, **no** el código de T01/T04/T07. No publicar un hash de checkpoint de código mientras las implementaciones permanezcan fuera de él. Antes de cualquier staging, inspeccionar contenido exacto, dependencias, untracked y secretos, y aprobar una lista explícita.

**Lista candidata explícita, NO aprobada para staging** (las rutas de `chat.py` y tests compartidos requieren revisión por hunk):

- Documento: `docs/checkpoints/TALOS_V15_CHECKPOINT_2026-10-13.md`.
- T01: `src/study_engine/audit/generation_adapter.py`, `src/study_engine/pedagogy/structured_pipeline.py`, `src/study_engine/web/routes/chat.py` (solo hunks T01), `tests/unit/pedagogy/test_audit_verdict_honesty.py`, `tests/unit/audit/test_generation_adapter.py`.
- T04: `src/study_engine/pedagogy/exercise_store.py`, `src/study_engine/pedagogy/generated_registry.py`, `src/study_engine/web/routes/dialogue.py`, `src/study_engine/web/routes/chat.py` (solo hunks T04), `tests/unit/pedagogy/test_socratic_ux_and_dialogue.py`, `tests/unit/web/test_t04_exercise_identity.py`.
- T07: `src/study_engine/retrieval/vector_identity.py`, `src/study_engine/retrieval/vector_store.py`, `src/study_engine/retrieval/embedding.py`, `src/study_engine/retrieval/indexer.py`, `src/study_engine/retrieval/dense.py`, `src/study_engine/storage/knowledge_store.py`, `tests/unit/retrieval/test_t07_vector_identity.py`, `tests/unit/retrieval/test_dense.py`, `tests/unit/retrieval/test_indexer.py`, `tests/unit/retrieval/test_numpy_blas_vector_search.py`.

**Fuera de esta selección y aún por adjudicar:** cambios preexistentes en `tests/conftest.py`, `src/study_engine/storage/sqlite_engine.py`, `src/study_engine/pedagogy/dialogue_engine.py`, `src/study_engine/tutor/fastpath_service.py`, `config/test_perimeter.json`, documentación histórica no rastreada y UI/T12; algunos pueden ser dependencias de reproducción, por lo que el conjunto candidato **no está certificado como autocontenido**. Quedan expresamente fuera `.env`, credenciales, bases/corpus/modelos reales, cachés, `graphify-out/` y artefactos generados. No se leyó ni copió ningún secreto.

## 9. Instrucciones para la siguiente sesión o agente

1. Leer este checkpoint y después el [plan operativo](../PLAN_MAESTRO_CIERRE_TALOS.md), el [roadmap V1.5](../ROADMAP_V1_5_MASTER.md) y, cuando se aporte como fuente, el plan T01–T20 con su enmienda.
2. Verificar rama, HEAD, staged/untracked y diff real con Git de solo lectura; no asumir que este corte sigue vigente.
3. No repetir auditorías generales ni reabrir paquetes validados focalmente sin evidencia nueva; conservar sus límites de integración.
4. No ejecutar tests, código, servicios o proveedores ni modificar datos/código sin autorización aplicable.
5. Mantener separados implementación, resultado focal, aislamiento, integración, aceptación, gate y release.
6. Continuar desde la revisión de la propuesta de T08/T09 y las dependencias reales, no desde el comienzo de V1.5.

**Integridad del checkpoint:** síntesis documental del checkout inspeccionado y antecedentes conversacionales identificados como tales. No constituye snapshot reproducible del worktree, certificación de seguridad, aprobación de un gate ni autorización operativa.
