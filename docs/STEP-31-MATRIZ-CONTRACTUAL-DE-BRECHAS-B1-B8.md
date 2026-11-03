# TALOS V1.5 — STEP-31

## MATRIZ CONTRACTUAL DE BRECHAS B.1–B.8

**Proyecto:** TALOS V1.5  
**Repositorio observado:** `/media/agustin/Laboratorio/study-engie`  
**Rama observada:** `talos-current-audit`  
**HEAD observado:** `cc8acfae623f9d10c8366871470319786b6a7ca4`  
**Fuentes de referencia:** `STEP-27`, `STEP-28`, `STEP-29`, `STEP-30`  
**Tipo:** matriz documental de brechas contractuales y decisiones pendientes  
**Estado inicial de Gate B:** `INCOMPLETE`  
**Implementación del harness:** `NOT AUTHORIZED`  
**Validación dinámica:** `NOT AUTHORIZED`

---

## 1. Propósito

Este expediente reemplaza la matriz resumida por una trazabilidad efectiva entre el requisito de STEP-27, la referencia en STEP-28, el hallazgo registrado en STEP-29 y la brecha que impide la clausura documental de Gate B.

No constituye implementación, aprobación ni ejecución. Su fin es servir de base para la corrección documental y la futura adjudicación autorizada.

## 2. Modelo de registro

Cada fila de la matriz contiene como mínimo:

- `gap_id`
- `contract_id`
- `criterion_id`
- `step27_requirement`
- `step28_reference`
- `step29_finding`
- `evidence_class`
- `current_status`
- `exact_missing_rule`
- `reason_gate_closure_is_blocked`
- `corrective_action`
- `decision_required`
- `decision_authority`
- `dependencies`
- `acceptance_predicate`
- `evidence_required_for_future_adjudication`
- `work_category`
- `implementation_authorization_required`
- `status`

## 3. Matriz contractual de brechas B.1–B.8

| gap_id | contract_id | criterion_id | step27_requirement | step28_reference | step29_finding | evidence_class | current_status | exact_missing_rule | reason_gate_closure_is_blocked | corrective_action | decision_required | decision_authority | dependencies | acceptance_predicate | evidence_required_for_future_adjudication | work_category | implementation_authorization_required | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B1-01 | B.1 | C01 | política protegida fuera del checkout con autoridad raíz y anti-rollback | STEP-28 §3.1–§3.4 | C01 = `PARTIAL` | `STATICALLY_CONFIRMED` | `PARTIAL` | se requiere un artefacto protegido, versión mínima, revocación y mapeo de downgrade | no hay una autoridad raíz ni una política protegida cerrada en los documentos | cerrar la política protegida y la autoridad de aprobación | definir autoridad raíz, versión mínima y revocación | `AUTHORITY NOT IDENTIFIED` | C02, C08, C09 | debe existir un artefacto protegido con autoridad autorizada, versión mínima y procedimiento de revocación | evidencia documental de la política y de la autoridad aprobadora | `A — DOCUMENTARY_CORRECTION` | `NO` | `OPEN` |
| B2-01 | B.2 | C03 | identidad inequívoca para campaña, ejecución, caso, worker e intento | STEP-28 §4.1–§4.3 | C03 = `PARTIAL` | `STATICALLY_CONFIRMED` | `PARTIAL` | deben definirse formato, unicidad, vida útil y relaciones entre objetos | la identidad no está especificada ni asignada con suficiente rigor | cerrar el esquema de identidad y sus relaciones | decidir formato, unicidad y relaciones | `AUTHORITY NOT IDENTIFIED` | B1-01, B3-01, B7-01 | cada objeto debe tener identidad única, origen y relación explícita con el siguiente | esquema documental de identidad y reglas de generación | `A — DOCUMENTARY_CORRECTION` | `NO` | `OPEN` |
| B3-01 | B.3 | C04, C05 | evidencia con procedencia, conjunto de campos y separación worker–observer–verifier | STEP-28 §5.1–§5.4 | C04 = `PARTIAL`; C05 = `PARTIAL` | `STATICALLY_CONFIRMED` | `PARTIAL` | deben existir campos obligatorios, opcionales, reglas de validación y separación de flujo de evidencia | la evidencia no define integridad, procedencia ni separación de permisos de forma cerrada | redactar la matriz de evidencia y la separación de flujo | decidir autoridad del esquema y permisos del verifier | `AUTHORITY NOT IDENTIFIED` | B1-01, B2-01, B5-01 | cada evidencia debe tener origen, validación y flujo de transmisión claramente definidos | matriz de evidencia con permisos y canales autorizados | `A — DOCUMENTARY_CORRECTION` | `NO` | `OPEN` |
| B4-01 | B.4 | C06 | estados definidos con agregación explícita | STEP-28 §6.1–§6.4 | C06 = `PARTIAL` | `STATICALLY_CONFIRMED` | `PARTIAL` | debe existir una matriz de agregación por control, evidencia, intención, campaña y gate | sin matriz de agregación no puede resolverse el criterio de estados | cerrar la semántica de estados y sus transiciones | decidir la semántica de agregación por nivel | `AUTHORITY NOT IDENTIFIED` | B3-01, B5-01, B7-01 | cada estado debe tener transición, regla de agregación y consecuencia precisa | matriz de estados y agregación completa | `A — DOCUMENTARY_CORRECTION` | `NO` | `OPEN` |
| B5-01 | B.5 | C07 | preflight con control_id, predicado y consecuencia | STEP-28 §7.1–§7.3 | C07 = `PARTIAL` | `STATICALLY_CONFIRMED` | `PARTIAL` | debe existir una matriz de preflight con control, evidencia, predicado y fallo | no se cierra el preflight ni la reacción ante un fallo | cerrar la tabla de preflight y su respuesta | decidir los controles obligatorios y su prueba documental | `AUTHORITY NOT IDENTIFIED` | B1-01, B3-01, B4-01 | cada control debe tener requisito, evidencia y respuesta ante fallo | tabla de preflight verificable documentalmente | `A — DOCUMENTARY_CORRECTION` | `NO` | `OPEN` |
| B6-01 | B.6 | C08, C09 | `tree_digest` canónico y par indivisible `(nodeids, tree_digest)` | STEP-28 §8.1–§8.5 | C08 = `PARTIAL`; C09 = `PARTIAL` | `STATICALLY_CONFIRMED` | `PARTIAL` | debe existir algoritmo, serialización, orden canónico, aprobación y revocación | sin ello no puede cerrarse la aprobación del inventario ni del digest | definir el algoritmo y la aprobación del par | decidir el algoritmo y la autoridad aprobadora | `AUTHORITY NOT IDENTIFIED` | B1-01, B2-01, B5-01 | el par debe ser inseparable, reproducible y aprobado antes de aceptar la campaña | algoritmo canónico y propuesta de aprobación documental | `B — DESIGN_DECISION_REQUIRED` | `NO` | `OPEN` |
| B7-01 | B.7 | C10, C12 | campañas, repeticiones, reintentos y contradicciones documentadas | STEP-28 §9.1–§9.4; §11–§12 | C10 = `PARTIAL`; C12 = `PARTIAL` | `STATICALLY_CONFIRMED` | `PARTIAL` | deben existir reglas de repetición, cancelación, cierre y registro de contradicciones | el modelo de la campaña y las contradicciones pendientes no están cerradas | definir campaña, reintentos y conflicto | decidir regla de reintentos, cierre y autoridad de resolución | `AUTHORITY NOT IDENTIFIED` | B2-01, B4-01, B8-01 | cada campaña debe tener intento, repetición, cierre y conflicto documentado | matriz de reintentos, conflicto y cierre de campaña | `B — DESIGN_DECISION_REQUIRED` | `NO` | `OPEN` |
| B8-01 | B.8 | C11 | trazabilidad completa requisito → contrato → evidencia → decisión | STEP-28 §10.1–§10.4 | C11 = `ABSENT` | `STATICALLY_CONFIRMED` | `ABSENT` | debe existir matriz final con filas sustantivas y dependencias | el cierre de Gate B no puede sostenerse sin trazabilidad completa | construir la matriz de trazabilidad final | decidir la estructura final de la matriz y las autoridades de cada decisión | `AUTHORITY NOT IDENTIFIED` | todas las anteriores | cada requisito debe vincularse con su decisión, autoridad y evidencia | matriz final row-by-row de trazabilidad | `A — DOCUMENTARY_CORRECTION` | `NO` | `OPEN` |

## 4. Clasificación de brechas por tipo

### 4.1. `A — DOCUMENTARY_CORRECTION`

Estas brechas pueden corregirse con evidencia documental ya disponible si se aplica la jerarquía de fuentes correcta.

- B1-01
- B2-01
- B3-01
- B4-01
- B5-01
- B8-01

### 4.2. `B — DESIGN_DECISION_REQUIRED`

Estas brechas requieren una decisión explícita de diseño antes de escribir la regla final.

- B6-01
- B7-01

### 4.3. `C — FUTURE_OPERATIONAL_VALIDATION`

Estas mismas brechas pueden requerir validación operativa futura una vez que la decisión de autoridad y el contrato estén cerrados, pero no se supone que ya exista evidencia operacional de ello.

- B1-01
- B3-01
- B5-01
- B6-01
- B7-01

## 5. Trazabilidad cruzada de criterios

| criterion_id | step27_requirement | step28_reference | step29_finding | gap_id | corrective_action | acceptance_predicate | evidence_required_for_future_adjudication | authority | status |
|---|---|---|---|---|---|---|---|---|---|
| C01 | política protegida, autoridad y anti-rollback | STEP-28 §3.1–§3.4 | `PARTIAL` | B1-01 | cerrar política y autoridad de aprobación | artefacto protegido con autoridad, versión mínima y revocación documentados | evidencia documental de política y autoridad | `AUTHORITY NOT IDENTIFIED` | `OPEN` |
| C02 | privilegios verificables | STEP-28 §3.2–§3.3 | `PARTIAL` | B1-01 | cerrar usuario dedicado y permisos efectivos | predicado de privilegios y fallo cerrado documentados | evidencia de permisos y entorno | `AUTHORITY NOT IDENTIFIED` | `OPEN` |
| C03 | identificadores y relaciones | STEP-28 §4.1–§4.3 | `PARTIAL` | B2-01 | cerrar identidad y relaciones | esquemas y formato con unicidad documentados | evidencia documental del esquema | `AUTHORITY NOT IDENTIFIED` | `OPEN` |
| C04 | procedencia de evidencia | STEP-28 §5.1–§5.4 | `PARTIAL` | B3-01 | cerrar matriz de evidencia | campos, validación y rechazo documentados | matriz de evidencia y validación | `AUTHORITY NOT IDENTIFIED` | `OPEN` |
| C05 | separación worker–observer–verifier | STEP-28 §5.1–§5.3 | `PARTIAL` | B3-01 | cerrar flujo y permisos | separación documental y permisos definidos | esquema de flujo y autoridad | `AUTHORITY NOT IDENTIFIED` | `OPEN` |
| C06 | estados y agregación | STEP-28 §6.1–§6.4 | `PARTIAL` | B4-01 | cerrar estados y agregación | matriz de estados y agregación documentada | prueba documental de transición y agregación | `AUTHORITY NOT IDENTIFIED` | `OPEN` |
| C07 | preflight | STEP-28 §7.1–§7.3 | `PARTIAL` | B5-01 | cerrar tabla de preflight | tabla con control_id, predicado y reacción definida | evidencia documental del preflight | `AUTHORITY NOT IDENTIFIED` | `OPEN` |
| C08 | `tree_digest` | STEP-28 §8.1–§8.5 | `PARTIAL` | B6-01 | cerrar algoritmo y serialización | algoritmo canónico definido | algoritmo y orden documentado | `AUTHORITY NOT IDENTIFIED` | `OPEN` |
| C09 | `(nodeids, tree_digest)` indivisible | STEP-28 §8.1–§8.5 | `PARTIAL` | B6-01 | cerrar aprobación del par | aprobación documental del par | evidencia de aprobación y revocación | `AUTHORITY NOT IDENTIFIED` | `OPEN` |
| C10 | campaña, reintento y cierre | STEP-28 §9.1–§9.4 | `PARTIAL` | B7-01 | cerrar reglas de campaña | modelo de intento, reintento y cierre documentado | evidencia documental del flujo de campaña | `AUTHORITY NOT IDENTIFIED` | `OPEN` |
| C11 | trazabilidad final | STEP-28 §10.1–§10.4 | `ABSENT` | B8-01 | construir la matriz final | matriz de trazabilidad row-by-row documentada | matriz final y dependencias | `AUTHORITY NOT IDENTIFIED` | `OPEN` |
| C12 | contradicciones y decisiones pendientes | STEP-28 §11–§12 | `PARTIAL` | B7-01 | registrar contradicciones y responsables | matriz de contradicción, decisión y autoridad documentada | evidencia documental de decisiones pendientes | `AUTHORITY NOT IDENTIFIED` | `OPEN` |
| C13 | separación de especificación y validación | STEP-28 §0, §1.2, §2, §7.3, §14 | `SATISFIED` | — | mantener la separación | no debe existir ninguna afirmación de validación dinámica sin ejecución | no requiere validación operativa en esta fase | `none` | `CLOSED` |
| C14 | alcance y prohibiciones | STEP-28 §1.2, §2.2, §14.3 | `PARTIAL` | B5-01 / B3-01 | separar “declarado” de “demostrado” | la prohibición y la evidencia de no ejecución deben quedar diferenciadas | evidencia documental de no ejecución y cadena de custodia | `AUTHORITY NOT IDENTIFIED` | `OPEN` |
| C15 | preservación de bloqueos y estados | STEP-28 §0.1, §14.4 | `SATISFIED` | — | preservar estados | bloqueos y estados canónicos no deben modificarse | evidencia documental de continuidad | `none` | `CLOSED` |

## 6. Contradicciones y decisiones pendientes

| conflict_id | source_a | source_b | conflicting_statements | normative_priority | resolution_status | resolution_authority | required_action |
|---|---|---|---|---|---|---|---|
| CONF-01 | STEP-27 | STEP-28 | STEP-27 exige cierre documental y aceptación por criterios; STEP-28 incluye requisitos sin su cierre completo | STEP-27 > STEP-28 | `UNRESOLVED` | `AUTHORITY NOT IDENTIFIED` | completar los requisitos faltantes en la documentación |
| CONF-02 | STEP-28 | STEP-29 | STEP-28 presenta una especificación que sugiere completitud; STEP-29 concluye que la especificación no está cerrada | STEP-27 > STEP-28 > STEP-29 | `UNRESOLVED` | `AUTHORITY NOT IDENTIFIED` | aclarar qué parte es requisito y qué parte es obligación pendiente |
| CONF-03 | STEP-29 | STEP-31 | STEP-29 hace una adjudicación de 15 criterios; la matriz STEP-31 debe vincular esos criterios con brechas reales | STEP-27 > STEP-28 > STEP-29 > STEP-31 | `UNRESOLVED` | `AUTHORITY NOT IDENTIFIED` | completar la trazabilidad cruzada y el vínculo criterio → brecha |

## 7. Estado de cierre documental

**Estado del Gate B:** `INCOMPLETE`

**Estado de la matriz de brechas:** `OPEN_WITH_VALIDATED_GAPS`

**Estado de autorización:** `NOT AUTHORIZED`

**Estado operativo:** `NOT EXECUTED`

## 8. Conclusión

La matriz de brechas B.1–B.8 queda corregida y trazable respecto de STEP-27 y STEP-29. No obstante, los huecos no resueltos siguen bloqueando el cierre documental del Gate B y no convierten la descripción en una autorización para implementación ni validación dinámica.

La corrección documental ha permitido separar claramente:

- lo que ya está suficientemente documentado;
- lo que requiere decisión de diseño;
- lo que requiere decisión de autoridad;
- lo que no puede demostrarse sin fase operativa autorizada.

**Estado canónico preservado:**

- `P1.2 = BLOCKED-REGRESSION`
- `P1.3 = BLOCKED`
- `GATE B = INCOMPLETE`
- `IMPLEMENTATION = NOT AUTHORIZED`
- `DYNAMIC VALIDATION = NOT AUTHORIZED`
