# EXP-2A-01 — Prerregistro v0.1

**DRAFT — EXPERIMENT_NOT_AUTHORIZED**  
Fecha de preparación: 2026-10-30. Productor: agente OpenCode; propuesta para decisión propietaria, no política aprobada. No hubo ejecución, construcción de brazos ni modificación normativa.

```text
PHASE_1_PROMOTABLE=FALSE
BASELINE_C0_RETAINED
PHASE_2_EXPERIMENTS=BLOCKED
INTEGRITY_UNKNOWN
BASELINE_V1_UNVERIFIED
```

Alcance único: **3-Level Hint (A) vs Direct Hint (B) vs Canned Hint (V1, C)**, según `ROADMAP_V1_5_MASTER.md` §10, EXP-2A-01. §6C.9 define L1 conceptual → L2 direccional → L3 revelación guiada; §6F fija ocho dimensiones; §6G exige comprensión/retención posterior, C1–C5, pacto socrático y primer token ≤1,5 s. Las definiciones operativas siguientes son propuestas, no requisitos históricos nuevos. §5E mantiene el bloqueo; §9 solo habilita preparación conceptual/arqueológica y prohíbe implementación productiva dependiente.

## 1. Identidad de controles: conocido ≠ congelado

**C0 documental histórico:** `FTS5 BM25`, identificado por §5E y CP147 como baseline retenido, sin promover C1–C7. No se recuperó en esta inspección una identidad completa del ejecutable, configuración y snapshot histórico que permita declarar equivalencia exacta. No se abre ni copia el corpus histórico/protegido para suplirla.

**Perfil C0 sintético propuesto, pendiente de aprobación y sellado:** `KnowledgeStore.fts_search` → `search`, únicamente por cuaderno y `source_ids` efectivos L3; `limit=5`, `source_id=None`, `document_id=None`; consulta saneada por `LexicalIndex`; FTS5 `unicode61 remove_diacritics 2`, ranking `-bm25(chunks_fts)` con pesos SQLite por defecto y orden `score DESC, document_id ASC, pos_index ASC`. Sin dense, RRF, reranker, federación, expansión ni recovery adicionales. No usar `search_hybrid` como sustituto implícito. Preservar C3/C5 y abstención; no forzar suficiencia de un pack.

Es un **perfil propuesto de la familia C0**, no una reproducción acreditada del benchmark histórico. El propietario debe aceptar esa distinción o exigir reconstrucción histórica antes de ejecutar.

**Corpus permitido para la futura factibilidad:** solo fixtures sintéticos, con dos cuadernos, fuentes autorizadas distintas, fuente denegada y casos sin evidencia. No existen todavía corpus, ejercicios ni snapshots sellados de EXP-2A-01. Registrar antes del run: texto exacto, IDs fuente/documento/chunk, páginas, hashes, permisos L3, orden de inserción/rowids, esquema/DDL, consultas y resultados esperados. Ningún material académico productivo ni fixture protegido.

**V1 pedagógico:** §10 nombra Canned Hint (V1), pero no identifica su revisión ni su algoritmo. Código recuperable en `603a09754bf140d394f263c8cd8cc241185b91d8:src/study_engine/web/routes/dialogue.py`: ante error, separar `solution_explanation` por puntos, conservar frases de longitud >10, filtrar respuesta literal y similitud `SequenceMatcher >0.70`, devolver primera pista válida o mensaje genérico; respuesta correcta no recibe pista. También devuelve la lista de pistas válidas y registra nivel 1. La ruta actual conserva ese mecanismo. **Esto no demuestra que sea el brazo histórico C**, ni autoriza a sustituirlo por el mensaje genérico. Falta vínculo contractual entre versión, política y control experimental: `BASELINE_V1_UNVERIFIED`.

### Identidades observadas en lectura, no snapshots de ejecución

HEAD observado: `c358f95eee7ebaf7672f401b219dcd43152edabb`, working tree con cambios. SHA-256 calculados directamente sobre bytes locales; no certifican integridad histórica ni fijan todas las dependencias transitivas:

| Objeto | SHA-256 |
|---|---|
| `docs/ROADMAP_V1_5_MASTER.md` | `5953aa2c57716291fa14cfcf98229604e85ee870240873eb86f33de17cacc997` |
| `docs/08-S7-TUTOR-POLICY-SPEC-V1.0.md` | `1cd6ce5e1177512fe7beebd0a3711ab82e4b4597130eca03a47145f9ea5b4360` |
| `src/study_engine/storage/knowledge_store.py` | `da2b56cfb5e15ef5ab6f816422e6a19c9ff345ce39a5dda7a079ad7fc94d115b` |
| `src/study_engine/storage/sqlite_engine.py` | `16df537187828a7b301ceeaff9bf26eeea108899a5a884c2c55ff017b40a9191` |
| `src/study_engine/storage/lexical_index.py` | `c65cae37006525b39199b074c9e9ad3a2171f1d95aac8ee5bdf4e4dd9cda08a7` |
| `src/study_engine/contracts/l3_manifest.py` | `9298a3488e4efad3d8aec867951440c263522b4301ae18b2272b07028864f15d` |
| `src/study_engine/web/routes/dialogue.py` actual | `76a3c8c7e33250c0ec2a8f43ec8460eca7dfd0dd1f04182437e3d0ceb4017853` |
| `603a09754bf140d394f263c8cd8cc241185b91d8:src/study_engine/web/routes/dialogue.py` | `1396a011a4c643f11130343ffa7506fdaa408b5ff82d8d50c47e1d64ff7a82b2` |

Antes de ejecución: conservar copia autorizada read-only de código/dependencias/configuración sintéticos, hashes y versiones Python/SQLite/runtime; comprobar reconstrucción. Los hashes solos no preservan archivos ni garantizan aislamiento. No restaurar/resetear el árbol para obtener un baseline.

## 2. Tres brazos y contrato común

| Brazo | Comportamiento propuesto | Existente / faltante |
|---|---|---|
| A — 3-Level Hint | L1 orienta al concepto; L2 señala relación/dirección; L3 guía un paso intermedio incompleto. Empezar L1; subir solo tras petición explícita y nuevo intento de razonamiento; máximo L3. Nunca revelar clave, artefacto completo ni resolver el ítem. | Hay directivas de fading y pistas; **no hay progresión L1→L3 acreditada**. Faltan controlador, contenidos y oráculo de transición experimentales. No construirlos ahora. |
| B — Direct Hint | Una pista específica indica el siguiente paso, sin escalera adaptativa ni solución final. Mismo texto ante nuevas solicitudes; no sumar contenido oculto. | Selección de primera pista existe en `dialogue.py:430–453`; su equivalencia a este brazo no está acreditada. Faltan contenido sellado y contrato experimental. |
| C — Canned Hint (V1) | Reproducir exactamente la política V1 recuperada y adjudicada, incluidos fallback, repetición y exposición de pistas; sin adaptación añadida. | **BASELINE_V1_UNVERIFIED**. Hay candidato histórico recuperable, no control identificado. La entrega exacta queda PENDING; no inventar una variante. |

**Entrada común:** case_id, cuaderno/KC/ejercicio, intento previo, historial de solicitudes, perfil sintético fijo, pack autorizado con hash y clave/rúbrica oculta al estudiante/generador. **Salida:** texto efectivamente entregado, nivel/posición si aplica, regla aplicada, referencias/hash del pack, tiempo, estado `DELIVERED / ABSTAINED / ERROR / BLOCKED`. Registrar el payload completo: una lista auxiliar también puede revelar contenido.

**Entrega y abstención:** sin petición no entregar pista; no avanzar ni actualizar estado académico por recibirla. Bloquear identidad/ACL/provenance incompleta, evidencia insuficiente, petición de solución protegida, contenido no sustentado o control de seguridad fallido. Reintentos idempotentes no cuentan como nuevas dosis. Mantener idéntico feedback de corrección entre brazos, separado de la pista. Tope propuesto: tres oportunidades de solicitud por trayectoria; cualquier incompatibilidad con V1 exige decisión antes de ejecutar, no adaptación silenciosa del control.

Los filtros existentes de subcadena/similitud no prueban ausencia de revelación conceptual. Todos los textos, incluidos A-L3 y el payload de C, requieren revisión previa independiente. Si V1 expone solución, bloquear ese caso y registrar incompatibilidad; no debilitar seguridad ni llamar V1 a una versión saneada.

## 3. Diseño y mediciones propuestas

**Factibilidad, no eficacia:** 12 casos base sintéticos × tres brazos = 36 trayectorias predefinidas. Seis casos con evidencia suficiente (dos de concepto, dos de mecanismo y dos de transferencia), y seis negativos: evidencia ausente, manifest ausente, fuente denegada, cruce de cuaderno, identidad incompleta y solicitud de solución protegida. Casos positivos incluyen intento inicial incorrecto y hasta tres solicitudes; variantes de respuesta correctas, erróneas y copiadas se fijan de antemano, sin ajustarlas para favorecer un brazo. No hay estudiantes ni simulación generativa del estudiante.

**Unidad:** trayectoria caso×brazo, con comparación pareada por caso; turnos de una trayectoria no son muestras independientes. Permutar orden de A/B/C mediante seed fija `20261030`, balanceando las seis permutaciones, dos casos por orden. Sellar la asignación antes de ver resultados. Cada trayectoria recibe estado temporal nuevo; no comparte memoria, caches ni historial con otra. No acumular aprendizaje sintético entre brazos.

Calcular retrieval una vez por caso y entregar **el mismo pack exacto** a los tres brazos; no consultar nuevamente según el texto de cada pista. Verificar hashes, ranking, citas y permisos en cada consumo. Igualar ejercicio, objetivo, intento inicial, perfil, canal, presupuestos máximos, hardware y entorno. Solo varía la política de pistas; las diferencias de contenido/dosis previstas por ella se registran, no se normalizan después. Generación, si se necesitara, será contenido fixture local prevalidado; ningún proveedor/modelo externo queda autorizado. Esto mide entrega/orquestación, no capacidad generativa de un modelo.

### Understanding % y corrección

Propuesta para una futura medición humana, **no ejecutable bajo esta autorización**:

`Understanding % = 100 × unidades con comprensión demostrada / unidades elegibles asignadas`.

Una unidad demuestra comprensión solo si, **sin nuevas pistas y sin acceso al solucionario**, obtiene simultáneamente: respuesta técnicamente correcta; explicación causal completa (2/2); transferencia correcta a un ítem equivalente no visto con justificación completa (2/2). Rúbrica causal/transferencia: 0 = ausente/contradictoria, 1 = parcial o descriptiva, 2 = mecanismo y relación relevante explícitos sin error crítico. Claves, criterios y equivalencia del ítem de transferencia deben aprobarse antes de asignar condiciones. Acertar el ítem original o repetir la pista no basta.

No respuesta/abandono/abstención de una unidad elegible permanece en el denominador como **comprensión no demostrada**, no como diagnóstico de incomprensión. Informar por separado tasa de medición completa y análisis sobre respuestas observadas; no imputar comprensión. Los casos negativos de seguridad no son unidades elegibles para eficacia.

En factibilidad, esas mismas reglas solo producen `SYNTHETIC_RUBRIC_CONFORMANCE %`: detección de respuestas fixture positivas/negativas por el evaluador. **No calcular ni presentar Understanding humano**, BKT como sustituto, ni significancia sobre respuestas guionadas.

| Medición | Oráculo / protocolo | Alcance |
|---|---|---|
| Corrección | Clave exacta o estado esperado discriminante; razonamiento evaluado aparte. Reportar acierto original y transferencia por separado. | Automática para formatos cerrados; revisión humana para explicación. |
| Grounding/provenance | Identidad y hashes fuente→chunk→pack→pista; ACL vigente; revisión de cada afirmación contra evidencia. | Checks automáticos estructurales + revisión humana factual; citas presentes no prueban soporte. |
| Claridad, profundidad causal, adaptación y accionabilidad | Cada dimensión 0 ausente/incorrecta, 1 parcial, 2 completa: comprensible para perfil fijado; mecanismo explicado; ajuste al perfil sin inventarlo; siguiente paso identificable sin solución, respectivamente. | Juicios humanos sobre artefactos sintéticos, no eficacia humana. |
| No invención / seguridad | Cero hechos no sustentados, cero clave/solución/artefacto protegido en texto o payload; casos negativos deben abstenerse sin exposición. | Comparación automática y revisión de equivalencia conceptual. Violación implica STOP, no compensación por calidad. |
| Primer contenido visible | Reloj monotónico desde solicitud aceptada hasta primera pista académica renderizada, no heartbeat/progress. Registrar total, por brazo, p50/p95 y fracción >1,5 s; sin latencia si abstención, timeout como fallo. | En offline solo tiempo hasta entrega local: proxy, no TTFC del navegador. Browser permanece BLOCKED; no certificar §6G con este proxy. |
| Retención | Futuro ítem paralelo sin pistas a D+7 ±1 día (ventana propuesta, no requisito histórico); misma rúbrica, ausencias explícitas. | Requiere estudiantes, consentimiento y autorización separada; NOT_RUN. |

Las ocho dimensiones de §6F quedan cubiertas: correctitud, grounding, claridad, profundidad causal, adaptación, eficacia (pendiente humana), no-invención y accionabilidad. BKT/SM-2 solo pueden ser inputs sintéticos congelados, nunca endpoints de comprensión.

**Hipótesis:** para un futuro estudio humano, H0-AB: pA≤pB, H1-AB: pA>pB; H0-AC: pA≤pC, H1-AC: pA>pC, con p=proporción de comprensión definida arriba. B–C descriptivo. No realizar inferencia humana con las 36 trayectorias. Tamaño/potencia, efecto mínimo y análisis de multiplicidad del estudio humano quedan pendientes de otro prerregistro; no estimarlos buscando un resultado favorable. Hipótesis de factibilidad: los tres brazos pueden entregarse con identidad/evidencia constantes, semántica de entrega correcta y sin exposición ni efectos académicos; verificar exhaustivamente casos/transiciones, sin p-valores ni adjudicación de superioridad.

**Revisión ciega:** dos revisores humanos puntúan independientemente con rúbrica congelada, IDs opacos y orden aleatorio, sin etiqueta de brazo, BKT, resultados de otros revisores ni hipótesis preferida. Ven ejercicio, perfil pertinente y evidencia, no la clave de asignación. Tercer revisor resuelve discrepancias con razón registrada; si no hay adjudicación, `UNASSESSED`. Conservar juicios originales, acuerdo exacto y desacuerdos. El contenido puede revelar el brazo: registrar sospecha de condición; no afirmar cegamiento perfecto. El evaluador automático nunca es la única autoridad de comprensión causal.

**Exclusiones/fallos:** excluir antes de asignar solo fixtures duplicados, ambiguos o sin clave/equivalencia adjudicada; registrar motivo e ID. No excluir después de conocer el brazo o su resultado. Seguridad negativa = caso válido, no ruido. Manifest inválido/abstención/timeout/error permanecen en resultados con su causa; no repetir hasta verde. Corrupción accidental del fixture invalida el bloque pareado completo, conserva salidas y requiere revisión del protocolo antes de repetir. Sin reemplazo selectivo. Separar número asignado, entregado, abstenido, fallido y evaluable.

## 4. Faltantes reales y condiciones de entrada

1. **Decisión normativa expresa** y aprobación del perfil C0 propuesto, sin confundirlo con reproducción histórica.
2. **Identificación/adjudicación del control V1** con fuente, revisión y conducta exacta. Mientras sea UNVERIFIED no puede ejecutarse la comparación de tres brazos; un sustituto necesitaría decisión y nuevo rótulo/prerregistro.
3. Contenidos de A/B, controlador de escalada A y contrato de entrega C; fixtures, claves de transferencia y rúbrica sellados. Su construcción requiere autorización posterior específica: este borrador no la concede.
4. Mecanismo experimental mínimo de entrega/registro y evaluación, aún no implementado ni acreditado; reutilizar piezas existentes sin activar rutas productivas de evaluación que escriben BKT/SM-2.
5. Entorno reconstruible: código/dependencias read-only; bases y perfiles temporales sintéticos; sin host corpus/config/productive DB, secretos ni red externa. Definir límites CPU/memoria/fds/tiempo, análisis de alcanzabilidad, preflight, controles de escape y captura antes de teardown. Sandbox histórico no sustituye evaluación vigente. Detener ante efecto inesperado; recuperación solo autorizada.
6. Sello previo de inputs/configuración/asignación/rúbrica/código; run_id real al ejecutar; outputs completos con lineage, errores y tiempos. Credenciales nunca en evidencia. Ninguna evidencia sintética se incorpora a StudentState, currículo, caches o índices productivos.

La primera prueba futura sería de **factibilidad de entrega y contención**, no un benchmark de aprendizaje: solo después de satisfacer 1–6 y recibir autorización de ejecución para estos recursos exactos. Un validador con fixtures no demuestra eficacia humana ni completa §6G. Retener `S6_ISOLATION_BLOCKED`, `P1.2 NOT_AUTHORIZED`, `CAPTURED_VECTOR_SCHEMA_COMPATIBILITY_UNVERIFIED`, `P12_X6_R2_COLAB_04_FUNCTIONAL_BLOCKED`, `EXTERNAL_NLI_VALIDATION_BLOCKED` y browser BLOCKED. No necesita ni autoriza S6, Colab, corpus protegido o tecnologías visuales.

## 5. Excepción normativa mínima propuesta — NO APLICADA

**Adenda propuesta a §5E, interpretada junto con §9:**

> Sin modificar el cierre ni los dictámenes de Fase 1, podrá autorizarse por decisión expresa del propietario exclusivamente la factibilidad offline de EXP-2A-01 (3-Level Hint, Direct Hint, Canned Hint V1) sobre un perfil C0 congelado y adjudicado, con fixtures y estados sintéticos aislados. Requiere controles C0/V1 identificados, protocolo aprobado, recursos delimitados y verificación vigente de precondiciones de aislamiento. Preparación, construcción experimental y ejecución requieren autorizaciones explícitas según su alcance; esta adenda propuesta no las concede. §9 conserva la prohibición de implementación productiva dependiente. No se permite promoción, modificación del runtime/baseline/estado académico productivos, acreditación de eficacia humana, ni desbloqueo automático de Fases 3–4. Los resultados serán únicamente evidencia de factibilidad sintética, NOT_GATE_ELIGIBLE para promoción. PHASE_1_PROMOTABLE=FALSE y BASELINE_C0_RETAINED permanecen intactos; PHASE_2_EXPERIMENTS=BLOCKED hasta autorización posterior específica de ejecución.

**Decisión solicitada:** aceptar/rechazar esta excepción y las definiciones propuestas; resolver primero la identidad V1 y el alcance C0. No se pide aprobar gates ni ejecutar en esta intervención.

Referencias de implementación: `storage/knowledge_store.py:533–601,712–729`, `storage/sqlite_engine.py:138–145`, `web/routes/dialogue.py:313–340,430–453,513–520`, `pedagogy/student_context.py:247–299`, `pedagogy/observation_admissibility.py:70–92`, `pedagogy/structured_pipeline.py:2272–2285,2371–2385`. Rutas relativas a `src/study_engine/`. Inspección estática y hashes de archivos únicamente; **TEST_NOT_RUN / EXPERIMENT_NOT_RUN**.
