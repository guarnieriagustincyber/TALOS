# P1.2.5 — Paquete de implementación controlada

**Estado:** COMPLETE — paquete de trabajo, no ejecución de fixes  
**Base observada:** `1d072d9`  
**Alcance:** consolidación de las adjudicaciones P1.2.4 B01–B10  
**Resultado de esta fase:** no se modificaron código, tests, fixtures, datos, corpus ni modelos; no se ejecutó el Quality Gate; no se creó ningún commit.

> Este documento prescribe una futura implementación que requiere autorización
> separada. No autoriza ejecutar ninguno de los cambios descritos. Las
> adjudicaciones delimitan lo que se observó; no certifican propiedades más
> amplias que las efectivamente ejercitadas.

## 1. Estado de salida

```text
P1.2.4 = COMPLETE (10/10 blockers adjudicados)
P1.2.5 = COMPLETE (paquete preparado; cambios no implementados)
P1.3   = NOT STARTED

PRODUCT FIXES IMPLEMENTED = NO
TEST/HARNESS FIXES IMPLEMENTED = NO
FIXTURE FIXES IMPLEMENTED = NO
QUALITY GATE RERUN = NO
IMPLEMENTATION COMMIT = NONE
```

## 2. Matriz canónica B01–B10

| ID | Categoría adjudicada | Causa demostrada / alcance | Cambio de producto | Cambio de test/harness/fixture | Evidencia que falta o límite | Dependencia |
|---|---|---|---|---|---|---|
| B01 | C — TEST/HARNESS | El audit hook del test rechaza `os.remove` del probe temporal de `tempfile.gettempdir()` antes de invocar la ruta sintética. | No. | Sí: acotar la observación a mutaciones de estado protegido/relevante y hacer alcanzables las verificaciones posteriores, sin permitir escrituras amplias. | La sterility/repeatability de la ruta TALOS aún no está demostrada. | Aislamiento del harness; realizar antes de cualquier validación de la ruta. |
| B02 | E — PEDAGOGICAL EXPECTATION | `/api/chat/query` produce `evidence_manifest → abstention → EOF` al faltar evidencia suficiente. No es obligatorio emitir tokens o `phase_complete` después de la abstención terminal. | No. | Ajustar la expectativa para aceptar la abstención válida; no exigir generación en ausencia de evidencia suficiente. | Ninguna para adjudicar el resultado observado; la prueba debe seguir cubriendo el contrato SSE declarado. | Contrato P1.1; independiente de B03. |
| B03 | C — TEST/HARNESS | El test usa `get_container()` y falla al construir el `AppContainer` global sin `working_dir`/`use_mock`, antes de crear el cliente o llamar el endpoint. | No. | Sí: proporcionar un container/configuración de test aislados en el consumidor del test. | La respuesta SSE posterior con setup aislado aún no está adjudicada. | Aislamiento del harness; agrupar con B01 solo para secuenciar, no para mezclar sus causas. |
| B04 | D — FIXTURE/MOCK | `MagicMock` produce campos textuales simulados donde el ensamblador espera valores concretos; C5 falla al evaluar cobertura y el manejo fail-closed retorna `RETRIEVAL_FAILURE`. | No, según esta evidencia. | Sí: usar `SearchResult` real o datos tipados equivalentes, con texto, score, fuente, chunk, páginas y metadata válidos. | Retrieval contextual real y requests conversacionales reales no se adjudicaron con esta prueba. | Construir primero fixtures tipadas y completas. |
| B05 | A — FUNCTIONAL DEFECT | En el flujo probado, el rewrite/rescate pierde el antecedente técnico de punteros/swap; la petición genérica “podes detallarme mas?” se vuelve incompatible con el pack previo y termina en abstención. | Sí, limitado a contextual rewrite/rescue. | Añadir pruebas unitarias y de integración sintética separadas; no cambiar la fixture para ocultar el defecto. | La repetibilidad request-to-request real y el retrieval real siguen pendientes. | Resolver semántica de rewrite y rescate; mantener validación real separada. |
| B06 | E — PEDAGOGICAL EXPECTATION | El test llamado “crash” no provoca crash/excepción; el contexto observado termina en abstención legítima antes del provider y la generación. | No. | Si se conserva el test, distinguir abstención pedagógica válida de manejo de crash. Un crash debe probarse mediante excepción controlada, no por consulta sin evidencia. | No hay evidencia de crash del backend/provider en la ejecución adjudicada. | Definir la propiedad concreta de la prueba; mantener separadas abstención y error. |
| B07 | A — FUNCTIONAL DEFECT | En la fixture evaluada, retrieval contextual encuentra evidencia pertinente, pero C5 mide cobertura sobre la consulta original literal y se abstiene (`coverage=0`); la divergencia ocurre en suficiencia, no en FTS5. | Sí, limitado a la relación entre intención contextual/rewrite y evaluación de suficiencia. | Añadir casos positivos y negativos de C5; no retirar el gate ni convertir similitud en suficiencia automática. | No generalizar desde la fixture en memoria a corpus/productivo; no se ejercitó navegación jerárquica padre/hijo en la ruta adjudicada. | Definir el objeto de evaluación de intención antes de cambiar C5; conservar fail-closed. |
| B08 | D — FIXTURE/MOCK | El `OfflineKnowledgeBackend` resuelve la allowlist del notebook y se abstiene porque el mock omite notebook→source; el `search_hybrid` mock configurado no se alcanza. | No. | Sí: representar notebook, enlaces notebook_sources y fuentes autorizadas antes de configurar/revisar resultados de retrieval. | La salida determinista con una ruta de autorización completa debe validarse luego. | Completar primero la fixture de autorización. |
| B09 | D — FIXTURE/MOCK | El test da 30 candidatos sintéticos no suficientes para C5, y el mock ignora `limit=15`; además, preconstruye la diversidad en vez de probar el algoritmo real. | No. | Sí: hacer suficiente el contenido y respetar el límite. Si la intención es validar el algoritmo de diversidad, separarlo en un test de `KnowledgeStore.search_hybrid` real sobre SQLite de test. | No se demostró un defecto del ensamblador ni diversidad real a partir de esa prueba. | Separar ensamblado/C5, límite de retrieval y diversidad real como propiedades distintas. |
| B10 | G — FRAGILE BENCHMARK / TEST-LOCAL | El umbral SQLite p95 <50 ms es local al benchmark; no se encontró evidencia de un SLO normativo vigente. Un resultado superior solo prueba el fallo de esa expectativa de test. | No. | Ningún cambio en esta fase. En otra decisión se podrá conservarlo como informativo o definir su destino; no elevarlo a gate normativo por defecto. | No hay requisito actual de producto incumplido demostrado. | Requiere decisión explícita sobre el rol futuro del benchmark; no optimizar SQLite para forzar PASS. |

## 3. Paquetes de trabajo y criterios de aceptación

### 3.1 B01/B03 — Aislamiento y harness

**Archivos candidatos**

- `tests/audit/test_b1_route_repeatability.py`
- `tests/pedagogy/test_socratic_system_prompt.py`
- Fixtures aisladas existentes en `tests/conftest.py`, solo si su contrato permite reutilización sin ampliar el scope.

**No modificar para acomodar los tests:** `src/study_engine/web/dependencies.py` ni el guard de `AppContainer`.

**Criterios de aceptación**

- B01 distingue eventos de mutación sobre estado protegido/relevante de housekeeping temporal dentro del directorio temporal poseído por la prueba; no instala una excepción global para `os.remove`/`unlink`.
- Las verificaciones relevantes se ejecutan aun ante fallo de la ruta y sus resultados no se convierten en PASS por cleanup.
- B03 construye e inyecta un contenedor de test aislado; no usa el singleton productivo ni relaja la protección de producción.
- Una futura prueba de B01 debe alcanzar import → ruta → ejecución sintética → repetición → verificador para poder adjudicar sterility. Hasta entonces, `route sterility = UNPROVEN`.

**Evidencia posterior necesaria:** ejecución focalizada de cada prueba; demostrar que el endpoint fue realmente llamado; registrar efectos observados y preservar las limitaciones.

### 3.2 B04/B08/B09 — Contratos de fixtures y mocks

**Archivos candidatos**

- B04: `tests/pedagogy/test_talos_vs_notebooklm_e2e.py::test_conversational_followup_contextual_retrieval`
- B08: `tests/unit/pedagogy/test_adaptive_pipeline.py::test_offline_knowledge_backend_pure_retrieval`
- B09: `tests/unit/retrieval/test_context_flood.py::test_assemble_epistemic_context_supports_30_chunks_and_diversity`
- Pruebas existentes del algoritmo de store: `tests/unit/storage/test_hybrid_search.py`

**Criterios de aceptación**

- B04 emplea `SearchResult` o un objeto tipado equivalente con valores reales y concatenables para los campos que consume el pipeline; cubre los datos requeridos por la evaluación de cobertura.
- B08 modela el camino completo notebook → `notebook_sources` → allowlist efectiva → retrieval, conservando el comportamiento fail-closed cuando no exista autorización.
- B09 define explícitamente si prueba ensamblado de evidencia o diversidad del retrieval. La fixture de ensamblado cubre los términos críticos de su query; el mock respeta `limit=15`. Una prueba de diversidad de producción llama al `KnowledgeStore.search_hybrid` real sobre SQLite temporal/autónomo y comprueba el resultado del algoritmo, no una lista ya diversificada.
- Ninguna fixture accede a datos de producción ni elimina controles de autorización, anti-leakage o suficiencia.

**Evidencia posterior necesaria:** tests focalizados de cada contrato; verificar que cada prueba alcanza la capa que afirma probar y que el mock no reemplaza precisamente el algoritmo bajo prueba.

### 3.3 B05 — Contextual rewrite y rescue

**Archivos candidatos**

- `src/study_engine/retrieval/query_rewriter.py`
- `src/study_engine/web/routes/chat.py` (preparación contextual y llamada a rescate)
- `src/study_engine/context/c5_trust.py` (compatibilidad del rescate, únicamente si la inspección de implementación confirma que ahí corresponde)
- `tests/pedagogy/test_talos_vs_notebooklm_e2e.py::test_repeated_followups_and_client_turns_and_rescue_pack`
- Pruebas unitarias existentes de rewrite y compatibilidad/rescate.

**Diseño requerido**

La transformación debe preservar conjuntamente la intención conversacional, el antecedente técnico (punteros/swap en C) y una query determinista utilizable para retrieval. No basta con borrar o ignorar “detallarme”; no basta con aceptar cualquier pack previo por similitud superficial.

**Criterios de aceptación**

1. Test unitario de contextual rewrite para el follow-up genérico y el antecedente.
2. Test específico de compatibilidad/rescue que acepta evidencia previa realmente pertinente y rechaza packs de otro tema.
3. Test de reutilización de evidencia pertinente sin fingir una nueva búsqueda satisfactoria.
4. Validación sintética request-to-request sobre la ruta correspondiente, si puede mantenerse aislada; reportarla aparte de unit tests.
5. No declarar demostrada la repetibilidad multi-request real si la validación solo siembra estado interno directamente.

### 3.4 B07 — Suficiencia C5 para consulta contextual

**Archivos candidatos**

- `src/study_engine/web/routes/chat.py` (separación de consulta original, intención contextual y query de retrieval)
- `src/study_engine/context/c5_trust.py` (solo la decisión determinista de cobertura/suficiencia que se demuestre necesaria)
- `tests/retrieval/test_hierarchical_rag.py::test_deictic_rewritten_hierarchical_retrieval`
- `tests/adversarial/test_c5_trust_gate.py` y pruebas específicas de solución/leakage pertinentes.

**Diseño requerido**

Determinar primero qué representación es la autoridad adecuada para suficiencia: query original, query reescrita, query canónica o intención resuelta. El retrieval puede expandir la expresión, pero no puede fabricar una intención nueva ni introducir evidencia ajena al scope.

**Criterios de aceptación**

- Positivo: paráfrasis contextual con vocabulario diferente recupera evidencia que cubre la intención y pasa C5.
- Negativo: una expansión que deriva a otro concepto no fabrica suficiencia.
- OOD permanece en abstención, sin llamada al provider.
- Se comprueba que query original y contextual expandida equivalentes pueden evaluarse sin exigir coincidencia literal.
- Se mantiene filtrado de fuentes autorizadas, fail-closed y prevención de solution leaks.

No usar solamente el caso B07 para afirmar calidad general de retrieval; documentar que el caso adjudicado usaba store en memoria/FTS5 y no acreditaba navegación jerárquica en corpus real.

### 3.5 B02/B06 — Expectativas SSE y pedagógicas

**Archivos candidatos**

- B02: `tests/integration/test_web_api.py::test_socratic_practice_dispatch_endpoint`
- B06: `tests/pedagogy/test_talos_vs_notebooklm_e2e.py::test_p3_debug_crash_sse_e2e_streaming`
- Cobertura existente de terminales SSE y error controlado: `tests/pedagogy/test_chat_sse_endpoint.py`
- Contrato/runtime SSE existente en `src/study_engine/web/routes/chat.py`.

**Criterios de aceptación**

- B02 acepta el terminal `abstention` cuando falta evidencia y comprueba que no se emitieron tokens ni se invocó generación en ese camino; mantiene las aserciones de contrato SSE que sí correspondan.
- B06 declara si el objetivo es abstención válida o manejo de crash. Para crash, inyecta una excepción controlada y comprueba `error` y terminación correspondiente. Para abstención, comprueba su evento pedagógico terminal. No llamar “crash” a una consulta que solo resulta insuficientemente respaldada.
- Ningún cambio contradice la semántica terminal P1.1 ni convierte abstención/aclaración en errores genéricos.

### 3.6 B10 — Destino del benchmark

**Archivo candidato:** `tests/performance/test_latency_disaggregated.py::test_sqlite_query_latency_p95_under_50ms`; revisar también la configuración de selección del gate solo si una decisión posterior cambia el carácter gating del benchmark.

**No hacer:** cambiar threshold, queries, índices, fixture de datos ni runtime para forzar PASS.

**Criterios para una decisión futura:** declarar si es informativo/no gating o si existe un SLO normativo con autoridad, scope, ambiente y operación medible definidos. La adjudicación B10 no encuentra tal SLO; por lo tanto, no presentar `<50 ms` como requisito vigente ni clasificar el fallo como defecto de producto.

## 4. Orden recomendado y dependencias

El orden es de preparación/validación; no autoriza iniciar los cambios:

1. **B01/B03:** aislar correctamente el harness y confirmar que ambas pruebas alcanzan sus objetivos declarados. B01 continúa sin demostrar sterility hasta completar el flujo real sintético.
2. **B04/B08/B09:** reemplazar mocks incompletos por fixtures que respeten los contratos de tipos, autorización, suficiencia y límites. Separar las propiedades cuando la misma prueba intente certificar más de una.
3. **B05/B07:** corregir los dos defectos de producto de forma independiente, con tests independientes. No hacer un refactor genérico de “contextual retrieval” que mezcle rewrite/rescue (B05) con suficiencia C5 (B07).
4. **B02/B06:** ajustar las expectativas o dividir las pruebas según la terminación pedagógica que pretenden verificar.
5. **B10:** decidir separadamente el destino del benchmark; no bloquear ni alterar producto para cumplir un threshold no normativo.
6. Ejecutar primero las verificaciones focalizadas anteriores; luego, y solo si una autorización posterior lo pide, revalidaciones ampliadas y el Quality Gate declarado.

Dependencias entre clases: harness aislado es precondición para evidencia de endpoint confiable; fixtures tipadas/autorizadas son precondición para interpretar sus asserts; solo después deben usarse esos tests como evidencia sobre B05/B07. B02/B06 no requieren fixes de producto para aceptar sus terminales pedagógicos. B10 no es prerequisite técnico para esos cambios.

## 5. Tests que pueden ajustarse y tests que no deben debilitarse

**Posibles cambios, solo en una fase autorizada:** los tests B01–B09 enumerados arriba, limitados a la propiedad adjudicada por fila. En B05/B07, los tests deben añadir guardas negativas junto a los positivos. En B02/B06, ajustar expectativas no autoriza borrar la comprobación de terminales/error.

**No cambiar para obtener PASS:**

- Tests protegidos de C5, autorización de fuentes, anti-leakage/solution-leak, aislamiento o contrato SSE, salvo una directiva explícita que autorice una refactorización semánticamente preservada.
- Threshold de B10 ni pruebas/contratos de rendimiento no relacionados.
- Asserts que detectan exposición de datos, provider calls sin evidencia suficiente o modificaciones a datos protegidos.
- Fixtures congeladas o bases versionadas de producción para acomodar resultados.

Los nombres candidatos no garantizan que sigan presentes o idénticos en una fase futura; antes de implementar debe revisarse el código actual y cualquier diferencia conservarse como evidencia, no resolverse silenciosamente.

## 6. Archivos candidatos

La lista identifica superficies a inspeccionar/modificar potencialmente en una fase futura; no es autorización para cambiarlas.

**Tests/harness/fixtures**

- `tests/audit/test_b1_route_repeatability.py`
- `tests/pedagogy/test_socratic_system_prompt.py`
- `tests/pedagogy/test_talos_vs_notebooklm_e2e.py`
- `tests/integration/test_web_api.py`
- `tests/unit/retrieval/test_context_flood.py`
- `tests/unit/pedagogy/test_adaptive_pipeline.py`
- `tests/retrieval/test_hierarchical_rag.py`
- `tests/unit/storage/test_hybrid_search.py` (posible test complementario de diversidad real, no necesariamente cambiar test existente)
- `tests/pedagogy/test_chat_sse_endpoint.py` (referencia/cobertura complementaria; modificar solo si un gap concreto lo exige)
- `tests/conftest.py` (solo si se necesita una fixture aislada reutilizable y su scope queda limitado)
- `tests/performance/test_latency_disaggregated.py` (solo ante decisión explícita futura sobre su rol)

**Producto, solo B05/B07**

- `src/study_engine/retrieval/query_rewriter.py`
- `src/study_engine/web/routes/chat.py`
- `src/study_engine/context/c5_trust.py`

**Contratos de referencia; no ampliar ni relajar por los fallos de fixture**

- `src/study_engine/contracts/search.py`
- `src/study_engine/web/dependencies.py`
- `src/study_engine/retrieval/presentation_filter.py`
- `src/study_engine/storage/knowledge_store.py`
- `src/study_engine/llm/offline_oracle.py`

## 7. Archivos/estados explícitamente fuera de alcance

No modificar para este paquete ni inferir autorización sobre:

- `data/student/`, `data/web_state/`, sus WAL/SHM, corpus, modelos, índices o datos reales;
- `.env`, credenciales, providers o configuración de producción;
- BKT, SM-2, StudentState o estado real de estudiantes;
- Retrieval Fabric/arquitectura de retrieval, salvo el punto B07 delimitado y luego autorizado;
- migraciones, Colab, MCP, E2E con provider externo o gate Quality Gate completo;
- límites/thresholds de producto para hacer pasar pruebas;
- los blockers B02/B06/B10 como defectos funcionales.

## 8. Validación futura y respuesta ante fallo

Cada cambio futuro debe tener primero tests focalizados que prueben la propiedad exacta y un caso negativo que proteja los límites indicados. Registrar comando, resultado, warnings, ruta realmente ejercitada, precondiciones y limitaciones. No inferir producto verde de un mock, ni aislamiento demostrado de un test PASS.

Si una corrección no pasa:

1. detener esa línea de cambio; no debilitar assertions ni ampliar allowlists para forzar PASS;
2. preservar diff, salida y estado del entorno; no restaurar trabajo previo ni datos;
3. clasificar si el nuevo resultado contradice la adjudicación o revela una limitación adicional;
4. solicitar/adquirir autorización explícita para ampliar alcance antes de cambiar otro componente;
5. dejar gates y fases posteriores como `BLOCKED`/`UNKNOWN` cuando corresponda.

El Quality Gate completo queda para una directiva posterior y solo después de concluir verificaciones focalizadas y confirmar que su perímetro es válido. No se exige ni se afirma en P1.2.5.

## 9. Riesgos que deben permanecer visibles

- B01 puede seguir sin evidencia de sterility real aunque el harness ya no bloquee el import.
- B05 tiene defecto observado en el flujo sintético adjudicado, pero no validación real multi-request.
- B07 es una divergencia de cobertura C5 en la fixture investigada; cambiar la query evaluada puede crear falsos positivos si no existen negativos.
- Un mock que reproduce una salida deseada no prueba diversidad, autorización ni ranking del producto.
- Aceptar cualquier `MagicMock` o relajar tipado puede ocultar errores en lugar de arreglar la fixture.
- Una ruta de abstención pedagógica no prueba manejo de excepción/crash.
- El fallo del benchmark B10 no establece por sí solo una violación de rendimiento del producto.

## 10. Registro de integridad de P1.2.5

En la verificación de inicio y cierre:

- HEAD observado: `1d072d9`.
- El worktree ya contenía modificaciones y archivos no versionados, entre ellos documentación, tests y código; se preservaron, sin atribuirlos a esta fase.
- `git diff --check` pasó antes y después de añadir este informe.
- No se consultaron ni modificaron DB, WAL/SHM, corpus o modelos durante P1.2.5. Al cierre se verificaron los hashes de las DB protegidas y coincidieron con los valores registrados antes en B09; existencia y contenido de WAL/SHM también coincidieron.
- No se ejecutaron tests, benchmarks ni Quality Gate en esta fase.
- Único archivo añadido por P1.2.5: `docs/P1_2_5_IMPLEMENTATION_PACKAGE.md`.
