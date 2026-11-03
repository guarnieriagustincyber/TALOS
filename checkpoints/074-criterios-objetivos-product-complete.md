# Checkpoint 074 — criterios objetivos para `PRODUCT_COMPLETE`

Fecha: 2026-10-01

## 1. Propósito, autoridad y límites

Este checkpoint convierte en criterios verificables la ruta de producto
registrada en el mapa maestro CP073 y en
`docs/PLAN_MAESTRO_CIERRE_TALOS.md`. No implementa, no reevalúa ni cambia
estados de gates. Las expresiones “evidencia faltante” describen lo que falta
para demostrar el criterio, no una nueva ejecución ni una adjudicación.

Se preservan por completo los estados actuales:

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

No se ejecutaron TALOS/FastAPI, tests, benchmarks, VM/workloads, A-PRE-1,
runtime changes ni actividades sobre DB/corpus/modelos/índices. No se ejecutó
E5/Qwen, BENCH-G2, PED-F7 ni Reality Audit/remediaciones.

## 2. Categorías de clasificación

Cada criterio de esta matriz tiene exactamente una categoría:

- `REQUIRED_FOR_PRODUCT`: condición para declarar completo el producto en el
  scope funcional declarado por CP073.
- `REQUIRED_ONLY_FOR_OPTIONAL_CLAIM`: sólo se exige si TALOS hace
  explícitamente esa afirmación adicional.
- `FORMAL_ASSURANCE_ONLY`: condición de garantía/cualificación formal; no es
  condición de cierre funcional si esa garantía queda expresamente fuera.
- `NOT_REQUIRED`: no es requisito de `PRODUCT_COMPLETE` bajo el objetivo actual
  documentado.

La clasificación no afirma que un gate ya haya pasado. Evidencia existente,
evidencia faltante y condición de cierre se reportan por separado.

## 3. Claims incluidos y excluidos del producto actual

| Claim | Clasificación | Evidencia existente | Evidencia faltante | Gate responsable / condición objetiva |
|---|---|---|---|---|
| TALOS es un tutor educativo técnico basado en evidencia, para los currículos de ingeniería/ciberseguridad actualmente declarados; responde con rigor y ajusta explicación/formato al pedido. | `REQUIRED_FOR_PRODUCT` | README, plan pedagógico y CP073 declaran el propósito; PED-F1…F4 y pruebas locales documentan formato, modos y prompt. | Aceptación de flujos integrados y evidencia de que formato/intención/contexto llegan de forma coherente al usuario en el scope de release. | Gate B, Gate D y B2–B6; el flujo integrado debe producir una respuesta que respete pedido y contexto, con evidencia de prueba trazable al snapshot. |
| TALOS conserva scope curricular/fuentes explícitos, distingue evidencia recuperada de conocimiento general y se abstiene o declara límites cuando falta contexto/evidencia. | `REQUIRED_FOR_PRODUCT` | Mecanismos de scope, citas, abstención y filtrado existen; hay pruebas aisladas y observaciones sintéticas. | Aceptación del recorrido identidad/fuentes/ACL→retrieval/contexto→respuesta para los currículos incluidos, incluidos casos negativos. | Gate B/C y B2–B5; positivos/negativos por scope deben respetar fuentes autorizadas, y ausencia/ambigüedad debe producir abstención/aclaración honesta, no invención. |
| TALOS brinda práctica y feedback educativo cuando esa ruta se ofrece, sin revelar soluciones canónicas durante evaluaciones protegidas. | `REQUIRED_FOR_PRODUCT` | Generadores MultiKC/BugSpotter/Trace Tables y protección anti-leak implementados con pruebas locales documentadas. | Evidencia integrada de generación/feedback y protección bajo el flujo pedagógico real del scope; límites de los controles ya documentados. | Gate C/D y regresión de contratos existentes; casos cubiertos deben verificar feedback para el intento realmente presente y ausencia de solución protegida al estudiante. |
| TALOS mantiene continuidad de turno y, cuando se usa, memoria/estado adaptativo con procedencia y sin mutar mastery sin evidencia suficiente. | `REQUIRED_FOR_PRODUCT` | Componentes Session Memory, historial, BKT y procedencia existen; hay pruebas unitarias/focalizadas. | Aceptación de contexto, continuidad, límites de memoria, aislamiento y no-mutación BKT/perfil en los casos F5. | F5/Gate C; debe pasar la matriz F5 de §5 con stores aislados y conservar las invariantes descritas. |
| El flujo conversacional termina de forma inequívoca y el cliente no presenta truncamientos/errores como respuesta completa. | `REQUIRED_FOR_PRODUCT` | B1-A/B1-R cubren ruta/slices sintéticos; UI tiene pruebas mockeadas para fallos de stream. | Adjudicación formal del contrato terminal y validación route→SSE→cliente. | F6/Gate D; cada outcome cubierto tiene estado terminal inequívoco, sin falso éxito, mensaje duplicado, cierre perdido ni persistencia canónica engañosa. |
| TALOS está integrado como aplicación dentro del scope aceptado (contexto/retrieval/pipeline/HTTP-SSE/UI), con regresión reproducible. | `REQUIRED_FOR_PRODUCT` | Componentes y pruebas de fronteras aisladas existen; B1-R `TECHNICAL PASS` está limitado a su harness. | Integración controlada B2–B6 y comparación PRE→POST sobre snapshot identificable. | B2–B6 y regresión final; cada frontera pasa su matriz de integración y los resultados son reproducibles y vinculados a código/configuración. |
| El checkout está certificado formalmente en aislamiento según A-PRE. | `FORMAL_ASSURANCE_ONLY` | A-PRE spec/ledger, harnesses, evidencia parcial y CP050–CP072. | Authority, preflight, coverage/tracing, disposition/predicate, autorización operacional y A-PRE-1. | A-PRE-0/A-PRE-1; sólo se declara si se satisfacen sus propios requisitos/gates; no se incluye en el umbral mínimo de producto funcional. |
| TALOS supera una evaluación pedagógica multi-currículo o demuestra mejora/no inferioridad. | `REQUIRED_ONLY_FOR_OPTIONAL_CLAIM` | PED-F0 es línea base documental de 20 preguntas con límites; no es evaluación causal ni multi-currículo. | Protocolo, rúbrica, currículos/intenciones, fuentes/prompts, evaluadores, umbrales, ejecuciones y análisis de variabilidad. | PED-F7; sólo necesario si se hace esa claim, no para afirmar funcionalidad básica. |
| TALOS obtiene métricas válidas de ranking/retrieval en BENCH-G2. | `REQUIRED_ONLY_FOR_OPTIONAL_CLAIM` | Runbook, herramientas/fixtures y adjudicación histórica parcial. | Qrels/scopes adjudicados, dataset versionado consistente y piloto aceptado/autorizado. | BENCH-G2; sólo necesario para claims de ranking o comparación retrieval. |
| El producto usa E5/Qwen como runtime reproducible, optimizado o preferido. | `REQUIRED_ONLY_FOR_OPTIONAL_CLAIM` | Candidates y decisiones de investigación documentados; E5 Path A elegido como ruta de factibilidad, no como runtime probado. | Factibilidad/reconstrucción según contratos, identidad de artifacts y autorización/harness; Qwen requiere provenance/runtime propio. | Gates E5/Qwen; no son requisito si no se hace la claim ni se incluye ese backend en el release. |
| TALOS es superior, equivalente o mejor que NotebookLM. | `REQUIRED_ONLY_FOR_OPTIONAL_CLAIM` | PED-F0 registra la comparación de 20 preguntas y limitaciones de versiones/fuentes/prompt/alineación. | Nuevo protocolo comparativo versionado, controles equivalentes, rúbrica y autorización de datos; no inferir causalidad de la comparación anterior. | Evaluación comparativa separada/PED-F7 según scope; no necesario para cierre de producto TALOS por sí solo. |
| TALOS es multi-user, offline-only absoluto o un clon de NotebookLM. | `NOT_REQUIRED` | No figuran como criterios actuales de cierre en las fuentes maestras revisadas; el producto se define por su objetivo de tutoría. | Ninguna para `PRODUCT_COMPLETE` bajo scope actual; si se adoptaran, requerirían decisión de producto aparte. | Fuera de los gates mínimos. No convertir principios local-first/offline-capable en requisito absoluto sin decisión. |

## 4. Flujo funcional mínimo end-to-end

Para el scope de producto declarado, el flujo mínimo que debe demostrarse es:

```text
identidad explícita del currículo/cuaderno
  → selección de perfil, fuentes y ACL para ese scope
  → recepción de pregunta/seguimiento/práctica del estudiante
  → recuperación y ensamblado de contexto/evidencia autorizados
  → respuesta o ejercicio con formato pedagógico adecuado
  → citas/localizadores sólo para evidencia realmente recuperada
  → feedback referido al intento/enunciado realmente disponibles
  → actualización de memoria/estado sólo cuando corresponda y con provenance
  → eventos HTTP/SSE con resultado terminal inequívoco
  → presentación/persistencia del mismo estado por el cliente
```

| Criterio | Clasificación | Evidencia existente | Evidencia faltante | Gate / condición objetiva |
|---|---|---|---|---|
| Una solicitud mantiene la identidad curricular y el scope desde entrada hasta prompt/fuentes. | `REQUIRED_FOR_PRODUCT` | H1–H3, selección exacta y pruebas de fixtures están documentados. | Aceptación integrada de todos los currículos/scope que se incluyan en release. | Gate B; cada ID/alias permitido resuelve al perfil/scope definido; desconocidos usan fallback neutral; positivos y negativos no contaminan otros currículos. |
| El contexto y las referencias reflejan únicamente historial/material realmente disponible y recuperado. | `REQUIRED_FOR_PRODUCT` | ContextPack, retrieval, citas y tests aislados existen. | Aceptación de trazabilidad fuente→contexto→prompt/respuesta y casos sin historial/documento. | Gate C/B2/B3; la salida debe resolver con antecedente disponible o pedir aclaración/declarar falta, nunca inventar historial, fuente o página. |
| La respuesta/práctica refleja pedido, nivel y material autorizado sin eludir protección de evaluación. | `REQUIRED_FOR_PRODUCT` | Políticas/prompts y protección canónica tienen fixes/pruebas locales. | Prueba del recorrido integrado y de casos de evaluación protegida. | Gate C/D; los casos cubiertos deben dar respuesta directa/feedback apropiado y no exponer `solution` protegida. |
| Transporte y cliente coinciden en texto, estado terminal y persistencia. | `REQUIRED_FOR_PRODUCT` | Ruta y cliente tienen pruebas sintéticas/mock independientes. | Integración HTTP/SSE→React y cobertura de outcomes terminales acordados. | Gate D/B5/B6; exactamente un outcome válido es interpretado igual por backend, consumer y estado visible/persistido; EOF sin terminal no es éxito. |

No se exige en este flujo proveedor real, corpus/modelos externos o lifecycle
productivo: el plan maestro permite B2–B6 controlados con stores sintéticos y
provider fake. Si se incluyera una dependencia real en el scope del release,
requeriría un gate distinto, no una extrapolación desde este flujo.

## 5. Criterios objetivos de Gate B — identidad y aislamiento curricular

| Criterio | Clasificación | Evidencia existente | Evidencia faltante | Condición objetiva de cierre |
|---|---|---|---|---|
| IDs canónicos, aliases y `curriculum_id` reconciliados declarativamente para cada currículo incluido en el release. | `REQUIRED_FOR_PRODUCT` | Fallback neutral, selección exacta y prueba fixture `fadena-std` se reportan corregidos. | Reconciliación de todos los IDs/aliases/perfiles relevantes del scope. | La matriz aprobada lista identidad canónica y alias permitidos; cada caso positivo resuelve el currículo esperado y cada ID desconocido toma fallback neutral, sin herencia accidental. |
| Roles de fuente y ACL efectiva consistentes desde selección hasta retrieval y prompt. | `REQUIRED_FOR_PRODUCT` | Pruebas de fuente/ACL fixture aisladas; mecanismos de retrieval y filtrado presentes. | Correlación integrada contra identidad y fuentes efectivas para cada currículo incluido. | En casos positivos sólo se seleccionan/evidencian fuentes autorizadas; en negativos/out-of-scope ninguna fuente no autorizada alcanza el prompt/resultado y se observa la respuesta de límite prevista. |
| Selección de prompt/perfil sigue la identidad explícita, no inferencias ambiguas ni aliases no reconciliados. | `REQUIRED_FOR_PRODUCT` | Tests de perfil/selección exacta y precedencia reportados. | Pruebas integradas request→resolver→prompt para la matriz declarada. | Para cada entrada de la matriz el prompt/perfil resultante coincide con su fila; entradas desconocidas no adoptan un currículo por defecto de contenido. |
| Casos multi-currículo sin contaminación entre materias/cuadernos. | `REQUIRED_FOR_PRODUCT` | Configuraciones distintas y pruebas locales con fixtures. | Aceptación integrada de positivos y negativos, más de una identidad sólo dentro del conjunto declarado para release. | Una suite/matriz versionada verifica rutas positivas y negativas por materia y no observa contenido, profile o ACL del scope vecino. |
| Autoridad curricular para `fadena-std`, si se incluye en el producto/release. | `REQUIRED_FOR_PRODUCT` | El fixture tiene prueba integrada limitada; el master advierte que no demuestra autoridad oficial. | Evidencia de autoridad curricular y aceptación de su perfil/fuentes. | La designación del programa/fuentes está respaldada por referencia autorizada; de no contar con ella, `fadena-std` se excluye explícitamente del scope de producto que se declara completo. |

**Cierre de Gate B:** todos los criterios anteriores pasan para el conjunto
finito de currículos declarado en el scope de release; ningún resultado del
fixture único se generaliza a currículos no incluidos.

## 6. Criterios objetivos de F5 / Gate C — continuidad, evidencia y estado

Los casos son los ya indicados en F5.1–F5.4 del plan pedagógico; no se agregan
familias de requisitos nuevas.

| Criterio/casos F5 | Clasificación | Evidencia existente | Evidencia faltante | Condición objetiva de cierre |
|---|---|---|---|---|
| Recorrido de mensajes, resumen, notebook/materiales, perfil/progreso hasta ruta y prompt; registrar persistencia, ventanas y truncamiento. | `REQUIRED_FOR_PRODUCT` | Historial, provenance, referencias y ContextPack tienen implementación/documentación. | Tabla de origen→transformación→consumidor→persistencia y verificación de sus casos/límites. | Entregable F5.1 cubre cada fuente usada en el scope; los límites ausentes se representan como no disponibles, no se presumen. |
| Referencias a antecedente único, ambigüedad, historial truncado/ausente, intento parcial y cambio/corrección de tema. | `REQUIRED_FOR_PRODUCT` | Pruebas focalizadas de contexto/pedagogía y componentes de historial. | Matriz de aceptación F5 aislada completa. | Antecedente único correcto se usa; ambigüedad material pregunta; contexto ausente se declara; respuesta/ejercicio no inventa un intento anterior; corrección y cambio de tema se distinguen en casos definidos. |
| Fuentes, citas, discrepancias y ausencia de documentos. | `REQUIRED_FOR_PRODUCT` | Mecanismos de citas, metadatos y avisos de discrepancia presentes; pruebas aisladas. | Evidencia end-to-end de recuperación/localizador y manejo de conflictos/ausencias. | Cada cita apunta a fuente efectivamente recuperada con localizador existente; no se asigna fuente no consultada ni página aproximada; discrepancias se señalan sin fusionar versiones; ausencia produce límite honesto. |
| Preferencia estable vs. instrucción puntual del turno. | `REQUIRED_FOR_PRODUCT` | Precedencia del contrato custom y restricciones explícitas del turno probadas localmente. | Aceptación en continuidad/memoria integrada. | El pedido puntual permitido prevalece sobre preferencia persistente contradictoria para el turno; preferencia no cambia indebidamente. |
| Memoria y datos de progreso separados de evidencia autorizada; privacidad/persistencia respetadas. | `REQUIRED_FOR_PRODUCT` | Stores y módulos de memoria/provenance presentes. | Matriz de aislamiento/no escritura sensible en stores de prueba. | La evidencia de curso no se sustituye por memoria; no hay escrituras persistentes sensibles no autorizadas dentro de los casos cubiertos. |
| No mutación de BKT/perfil en turno ordinario sin evidencia evaluativa suficiente. | `REQUIRED_FOR_PRODUCT` | BKT probado en suites propias; plan pedagógico ya establece no inferir dominio de una respuesta aislada. | Verificación integrada de invariancia en los escenarios F5. | Snapshot de BKT/perfil antes/después permanece idéntico en turnos ordinarios definidos; sólo eventos evaluativos admitidos por el contrato pueden mutarlo. |

**Cierre F5/Gate C:** matriz F5 offline/mockeada aprobada para los escenarios
de arriba, con respuesta ensamblada y metadatos/citas visibles cuando aplique;
límites de retención/persistencia documentados. Esto no constituye validación
de calidad de retrieval ni prueba de aprendizaje/retención.

## 7. Criterios objetivos de F6 / Gate D — contrato de respuesta y transporte

| Criterio | Clasificación | Evidencia existente | Evidencia faltante | Condición objetiva de cierre |
|---|---|---|---|---|
| Adjudicar semántica observable para aceptación, progreso parcial, finalización, cancelación, timeout, error proveedor/interno, truncamiento, salida vacía/abstención. | `REQUIRED_FOR_PRODUCT` | B1-A/B/B1-R observaron rutas sintéticas; existen hallazgos source-traced de client. | Decisión explícita de contrato, sin convertir observación en fix automático. | Cada estado tiene una representación terminal documentada y diferenciada entre transporte y contenido. |
| Cada ruta terminal produce un estado inequívoco que backend y cliente interpretan igual. | `REQUIRED_FOR_PRODUCT` | Fakes backend y API/SSE mocks UI probados separadamente. | Tests de coherencia route real con deps sintéticas y consumer UI. | Éxito requiere terminación válida; abstention/clarification, error, abort, timeout y truncamiento se reconocen según contrato adjudicado; EOF sin terminal nunca se muestra completa. |
| Cubrir fallos previos/posteriores al primer token, finalización normal, cancelación, timeout, truncamiento, malformed, terminal ausente/duplicado y error tras texto parcial. | `REQUIRED_FOR_PRODUCT` | B1-R cubrió diez escenarios con tres repeticiones según reporte; alcance de contrato sigue limitado. | Aceptación según contrato y pruebas consumidor/backend coherentes para los casos relevantes. | Cada escenario definido pasa y no hay éxito falso, duplicación de respuesta, cierre perdido ni mutación doble. |
| Texto recibido, renderizado, persistido y reutilizado mantiene identidad/estado; texto parcial no se marca completo. | `REQUIRED_FOR_PRODUCT` | Client rechaza ciertos streams incompletos en mocks; auditoría reporta controles de finish. | Trazabilidad integrada de backend→SSE→UI→historial/persistencia. | El contenido persistido/reutilizado queda asociado al mismo terminal; parcial se etiqueta incompleto y no se canoniza como respuesta completa. |
| Errores públicos seguros y telemetría mínima sin secretos/datos sensibles; política de retención definida. | `REQUIRED_FOR_PRODUCT` | Seguridad/logging y categorización están presentes parcialmente. | Verificación de F6 para outcomes/error en las fronteras aceptadas y definición/confirmación de retención. | Detalles internos quedan en logs controlados; UI recibe error seguro; telemetría incluye sólo campos disponibles permitidos y marca no disponible cuando falten. |
| Cancelación y reintento no duplican respuestas/mutaciones; retries acotados e idempotentes donde el contrato actual los use. | `REQUIRED_FOR_PRODUCT` | Observación sintética de abort/cancel existe. | Casos F6 de cancelación/retry en ruta y persistencia aisladas. | La matriz muestra término de trabajo cuando corresponde y cero duplicación/mutación doble en escenarios cubiertos. |

**Cierre F6/Gate D:** decisión documentada y tests de ruta con dependencias
sintéticas y consumidor UI coherentes en outcomes adjudicados. Sólo después
B5/B6 demuestra la integración aislada. No requiere proveedor real.

## 8. Qué deben demostrar B2–B6

| Frontera | Clasificación | Evidencia existente | Evidencia faltante | Condición objetiva de cierre |
|---|---|---|---|---|
| B2 — contexto/dominio con stores sintéticos. | `REQUIRED_FOR_PRODUCT` | B1 route sustituye la preparación de contexto por fakes; ContextPack existe. | Prueba real de la frontera de contexto con store sintético y guardas. | Identidad, historial/contexto disponible, límites y fuentes del caso atraviesan la frontera sin leer datos de proyecto; invariantes B/C se preservan. |
| B3 — retrieval con fixtures SQLite/corpus sintético y scope aislado. | `REQUIRED_FOR_PRODUCT` | Retrieval unitario/fabric aislado y filtrado presentes. | Integración de fixtures con scope/fuentes y resultado trazable. | Casos positivos recuperan la evidencia fixture esperada, casos negativos excluyen fuentes no autorizadas; cites/metadata apuntan sólo a resultados reales. |
| B4 — pipeline con provider fake. | `REQUIRED_FOR_PRODUCT` | Pipeline y providers/adapters presentes; probes previos usaron fakes a nivel route. | Cruce retrieval/contexto→pipeline con fake bajo contrato pedagógico/anti-leak. | Prompt/contexto sólo contiene material autorizado; respuesta mock sigue modo/intención y no revela solución protegida en casos aceptados. |
| B5 — HTTP/SSE integrado. | `REQUIRED_FOR_PRODUCT` | ASGI route sintética B1-A/B1-R. | Integración de ruta con fronteras B2–B4 y secuencias completas terminales. | Solicitud HTTP atraviesa la ruta integrada; status/event sequence/terminal y estado de contenido corresponden al contrato D; guardas impiden red, DB/corpus productivo, subprocess/thread no permitido y escritura fuera de scope. |
| B6 — React↔FastAPI aislado. | `REQUIRED_FOR_PRODUCT` | UI Playwright contra mock API/SSE y backend ASGI probado separadamente. | Ejecución integrada controlada de React y FastAPI sintético, bajo las guardas previstas. | UI muestra progreso/resultado/error/incompleto según outcome real del SSE; no declara éxito para streams inválidos; texto/estado persistido coincide; sin proveedor real ni datos productivos. |
| Matriz global de fronteras y guardas. | `REQUIRED_FOR_PRODUCT` | Las fronteras B0.5/B1-R tienen guardas/harness documentados para alcances parciales. | Resultado consolidado por B2–B6. | Cada frontera tiene caso positivo/negativo relevante, artefacto de resultado, guardas cumplidas y no hay salto desde evidencia fake a claims de producción. |

## 9. Regresión reproducible final

| Criterio | Clasificación | Evidencia existente | Evidencia faltante | Condición objetiva de cierre |
|---|---|---|---|---|
| Snapshot PRE limpio e identificable, con código/configuración/perímetro vinculados. | `REQUIRED_FOR_PRODUCT` | Plan de cierre especifica baseline PRE; existen identidades de snapshots históricos. | PRE limpio para el candidato a cierre; worktree observado en CP073 no lo es. | Registrar commit/snapshot, identidad de entorno/dependencias y hashes de artefactos relevantes; el snapshot de comparación no incluye cambios no identificados. |
| Test perimeter explícito y reproducible. | `REQUIRED_FOR_PRODUCT` | `config/test_perimeter.json` y `quality_gate.py` son fuente/validador del perímetro; documentación indica clases required/qualification/optional/support-only. | Recalcular estructura/conteos en el snapshot PRE y ejecutar el perfil acordado en su gate autorizado. | Suite requerida pasa; suites de cualificación reportan su contexto; optional/support-only aparecen como tales; cada skip/warning/failure queda explicado; ningún conteo histórico sustituye resultado. |
| Comparación PRE→POST vinculada a la misma frontera y condiciones registradas. | `REQUIRED_FOR_PRODUCT` | El plan pide regresión PRE→POST con artefactos/hashes. | Corridas de referencia y posterior sobre snapshots comparables autorizados. | Diferencias de resultados, skips, warnings, errores, duración, condiciones de hardware/runtime, side effects y artifacts tienen reporte/hash; anomalías quedan adjudicadas antes del cierre. |
| Invariantes protegidas sin cambios no declarados. | `REQUIRED_FOR_PRODUCT` | Contratos de perímetro y artefactos protegidos están documentados. | Evidencia de integridad asociada a las corridas de producto. | Comparar hashes/estado de outputs protegidos según contrato, informar todos los side effects; cero cambios no autorizados o no explicados. |
| Runtime real/productivo, rendimiento general, suite de garantía formal o proveedores externos. | `NOT_REQUIRED` | Plan distingue integración sintética, proveedores reales, A-PRE, benchmarks y runtime experimental. | Ninguna para el scope mínimo de producto; serían evidencias específicas de claims. | No se requiere para `PRODUCT_COMPLETE` si esos claims quedan fuera y el flujo mínimo está cubierto por las fronteras aisladas descritas. |

Esta regresión de producto no se denomina “certificación formal”, no habilita
A-PRE-1 ni cambia readiness. El test runner/perímetro sólo puede ejecutarse
en una futura tarea con la autorización y precondiciones pertinentes.

## 10. Claims adicionales y clasificación

| Elemento | Categoría | Evidencia existente | Evidencia faltante si se reclama | Gate/condición |
|---|---|---|---|---|
| PED-F7: calidad pedagógica multi-currículo. | `REQUIRED_ONLY_FOR_OPTIONAL_CLAIM` | Línea base PED-F0 y fixes pedagógicos documentados, pero no evaluación nueva. | Matriz de currículo/intención, fuentes/prompts, rúbrica/umbrales, evaluadores y resultados/variabilidad. | PED-F7; sólo necesario para claim de calidad/mejora validada, no para que funcionen las rutas producto. |
| BENCH-G2: ranking/retrieval comparativo válido. | `REQUIRED_ONLY_FOR_OPTIONAL_CLAIM` | Runbook, validadores, fixtures y revisión parcial de scopes/qrels. | Adjudicar queries/qrels, versionar dataset/snapshot y completar piloto aprobado. | BENCH-G2; no necesario sin claim de ranking. No ejecutar en esta tarea. |
| A-PRE: aislamiento/calificación formal. | `FORMAL_ASSURANCE_ONLY` | CP050–CP073, manifest/ledger y harnesses previos con límites. | Authority resuelta; predicate, inventory, UNKNOWN, tracing/coverage, preflight y autorización/ejecución A-PRE-1. | Camino formal A-PRE separado. La autoridad no resuelta no bloquea `PRODUCT_COMPLETE` si no se hace claim formal. |
| E5/Qwen: runtime de embedding específico reproducible/validado. | `REQUIRED_ONLY_FOR_OPTIONAL_CLAIM` | E5 Path A y bloqueos Qwen documentados; candidates, no runtime obligatorio probado. | E5 runtime/harness/artifact validation y Qwen provenance/runtime según sus gates. | Gates E5/Qwen y autorización propia. No necesario si no se incluye en el release ni se reclama. |
| Comparación con NotebookLM: superioridad, equivalencia o mejora causal. | `REQUIRED_ONLY_FOR_OPTIONAL_CLAIM` | Fase 0: 20 preguntas, condiciones desiguales/no completamente emparejadas y límites de registro. | Estudio versionado y comparable con protocolo/rúbrica/controles; autorización de datos. | Estudio separado/PED-F7 en el scope correspondiente. La comparación histórica no sirve para claim causal. |
| Multi-user, NotebookLM clone, offline-only absoluto, ColBERT/graph retrieval y roadmap v1.1. | `NOT_REQUIRED` | Roadmaps/capabilities contienen ideas y principios, pero CP073 no los determina como requisitos de release. | Ninguna para el scope actual; exigiría decisión nueva para convertirse en promesa del producto. | Fuera del criterio de PRODUCT_COMPLETE. |

## 11. Condiciones suficientes para `PRODUCT_COMPLETE` con A-PRE abierto

Puede declararse `PRODUCT_COMPLETE` aunque A-PRE formal permanezca abierto,
si y sólo si se cumplen todas estas condiciones:

1. El scope de producto/release se declara explícitamente: currículos, flujos y
   claims incluidos; las exclusiones de autoridad/A-PRE y claims opcionales
   quedan visibles.
2. Los criterios `REQUIRED_FOR_PRODUCT` de Gate B, F5/Gate C, F6/Gate D y
   B2–B6 pasan dentro de ese scope, con resultados verificables y sin
   extrapolar fixtures/slices a dominios no probados.
3. La regresión final identifica PRE/POST, entorno, perímetro, hashes,
   outcomes de suites, skips, warnings, errores, side effects y discrepancias;
   no hay anomalía abierta que invalide el contrato de producto declarado.
4. No se hace una claim de aislamiento formal, A-PRE readiness, certificación
   de syscall/sandbox, superioridad frente a NotebookLM, benchmark ranking ni
   runtime E5/Qwen sin satisfacer su criterio adicional correspondiente.
5. Los estados canónicos A-PRE se conservan exactamente como están; el cierre
   de producto funcional no altera membership/disposition, congela inventory,
   declara A-PRE-0 `READY` ni autoriza A-PRE-1.

La condición 4 es delimitación honesta del alcance, no una excepción que
permita omitir un requisito funcional de las filas clasificadas
`REQUIRED_FOR_PRODUCT`.

## 12. Cómo leer “exactamente qué falta”

Este checkpoint define el **conjunto objetivo de aceptación** para el producto
actual. Todavía no adjudica los criterios como PASS/FAIL y no altera los
estados de gates existentes. La transición es:

```text
CP073: mapa de caminos
  → CP074: checklist objetiva de PRODUCT_COMPLETE
  → futura evaluación de cada criterio contra evidencia
  → cierre de gate sólo mediante su propio resultado/autorización
  → PRODUCT_COMPLETE para el scope explícito (o lista precisa de criterios fallidos)
```

La tabla §3 define claims del producto y exclusiones; §§4–9 definen el flujo y
criterios funcionales; §10 separa claims adicionales; §11 especifica la
condición para declarar producto completo con assurance formal todavía
pendiente.
