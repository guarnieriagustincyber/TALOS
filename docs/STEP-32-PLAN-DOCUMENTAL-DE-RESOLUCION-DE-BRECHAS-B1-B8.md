# TALOS V1.5 — STEP-32

## PLANIFICACIÓN DOCUMENTAL DE RESOLUCIÓN DE BRECHAS Y CONTRATOS DE AUTORIDAD B1–B8

**Tipo:** planificación documental estática, sin implementación ni autorización operativa.
**Repositorio observado:** `/media/agustin/Laboratorio/study-engie`
**Rama observada:** `talos-current-audit`
**HEAD observado:** `cc8acfae623f9d10c8366871470319786b6a7ca4`
**Entregable único:** `docs/STEP-32-PLAN-DOCUMENTAL-DE-RESOLUCION-DE-BRECHAS-B1-B8.md`

---

## 1. Contexto canónico

STEP-31G declara terminado el ciclo de auditoría documental con brechas abiertas. No corresponde iniciar otra auditoría recursiva de STEP-27–STEP-31G.

El siguiente trabajo debe cambiar de objetivo: pasar de identificar y repetir las insuficiencias a planificar de manera ordenada qué decisiones documentales faltan, quién debe tener autoridad para tomarlas, qué artefactos serían necesarios y qué evidencia futura permitiría adjudicar cada brecha.

Esta etapa no resuelve las brechas. Define un plan verificable para su resolución futura, sin inventar autoridades, aprobar diseños ni conceder permisos.

Estados de partida:

- `DOCUMENTARY_AUDIT = COMPLETE_WITH_OPEN_GAPS`
- `EVIDENTIARY_SUFFICIENCY = PARTIALLY_SUPPORTED_WITH_OPEN_EVIDENTIARY_GAPS`
- `GATE B = INCOMPLETE`

---

## 2. Alcance permitido

Se autoriza exclusivamente:

1. leer los documentos STEP-27, STEP-28, STEP-29, STEP-31, STEP-31B, STEP-31C, STEP-31D, STEP-31E, STEP-31F y STEP-31G;
2. verificar mediante Git de solo lectura la identidad del checkout y el estado actual del árbol;
3. contrastar las brechas ya documentadas con sus requisitos contractuales;
4. diseñar un plan documental de resolución de B1-01 a B8-01;
5. crear únicamente el documento especificado en esta directiva.

No se autoriza:

- ejecutar tests, ni siquiera `pytest --collect-only`;
- ejecutar o importar código del proyecto;
- iniciar backend, aplicación, workers, observers, verifiers, harnesses o preflight;
- acceder a bases de datos, corpus, modelos, proveedores o estado de aprendizaje;
- modificar fuentes previas, código, configuración, tests, snapshots, bases de datos o corpus;
- ejecutar operaciones Git mutativas;
- publicar en GitHub;
- implementar contratos, aprobar diseños, cerrar brechas o autorizar validación dinámica.

Toda información que no pueda verificarse dentro del alcance se identifica como `NOT EVALUABLE` o `AUTHORITY NOT IDENTIFIED`, según corresponda.

---

## 3. Principios de planificación

El plan respeta estos principios:

- `No inventar autoridad`: si los documentos no identifican al responsable legítimo de una decisión, se registra la ausencia.
- `No confundir propuesta con aprobación`: un diseño propuesto no es una decisión autorizada.
- `No confundir documento con evidencia`: una obligación escrita no prueba su cumplimiento.
- `No cerrar por agregación`: una brecha no se cierra porque las demás estén documentadas.
- `No alterar la historia`: conservar las adjudicaciones originales de STEP-29 como antecedentes.
- `No anticipar ejecución`: describir evidencia futura necesaria sin producirla ni afirmar que existe.
- `Mantener separados` los estados de requisito, brecha, afirmación, evidencia, validación y autorización.

---

## 4. Matriz central de resolución de brechas

La tabla siguiente resume el plan de resolución futura para B1-01 a B8-01. Se usa como plan documental, no como cierre ni como autorización.

| gap_id | affected_criteria | contractual_requirement | exact_missing_decision | authority_status | documentary_work_required | dependencies | future_evidence_required | closure_predicate | current_status | authorization_boundary |
|---|---|---|---|---|---|---|---|---|---|---|
| B1-01 | C01, C02 | política protegida, trust root, versión mínima, anti-rollback y autoría de la política | definir la raíz de confianza, artefacto protegido, autoridad aprobadora, versión mínima y mecanismo de revocación | `AUTHORITY NOT IDENTIFIED` | cláusula de autoridad, política protegida, condiciones de versión y revocación | none; requiere decisión raíz | artefacto protegido, autoridad aprobadora, reglas de versión y anti-rollback | debe existir un artefacto protegido con autoridad, versión mínima y revocación documentados | `OPEN` | no aprobar ni desplegar ninguna política |
| B2-01 | C03 | identidad inequívoca y relaciones entre campaña, ejecución, caso, worker e intento | definir identidad, unicidad, ciclo de vida y relaciones entre entidades | `AUTHORITY NOT IDENTIFIED` | esquema de identidad, relaciones y reglas de invalidación | B1-01 | especificación documental de identidad, relaciones, alcance y invalidación | cada entidad debe tener identificación única, origen y relación explícita con la siguiente | `OPEN` | no diseñar ni implementar un esquema definitivo |
| B3-01 | C04, C05 | procedencia, autenticidad y separación worker / observer / verifier | definir procedencia de evidencia, flujo de autoridad y separación efectiva entre responsabilidades | `AUTHORITY NOT IDENTIFIED` | matriz de evidencia, permisos, canales y flujo de decisión | B1-01, B2-01 | esquema de evidencia, permisos y flujo de autoridad | cada evidencia debe tener origen, validación y flujo claramente definidos | `OPEN` | no asumir una separación por mera descripción |
| B4-01 | C06 | estados definidos y agregación explícita | definir estados, transiciones, condiciones terminales y regla de agregación | `AUTHORITY NOT IDENTIFIED` | semántica de estados, transiciones, agregación y tratamiento de estados desconocidos | B3-01 | matriz de estados, transición y agregación | cada estado debe tener transición, agregación y consecuencia precisa | `OPEN` | no declarar estados válidos sin autoridad |
| B5-01 | C07, C14 | preflight, prohibiciones, reacción ante fallo | definir control_id, predicado verificable, evidencia requerida y consecuencia ante rechazo | `AUTHORITY NOT IDENTIFIED` | tabla de preflight con reacción y condiciones de rechazo | B1-01, B3-01, B4-01 | preflight formal y cadena de evidencia de no ejecución | cada control debe tener requisito, evidencia y respuesta identificar | `OPEN` | no ejecutar preflight ni certificar ausencia de ejecución |
| B6-01 | C08, C09 | `tree_digest` canónico y par indivisible `(nodeids, tree_digest)` | definir algoritmo, serialización, orden canónico, aprobación, revocación y relación con `nodeids` | `AUTHORITY NOT IDENTIFIED` | algoritmo canónico y firma documental del par | B1-01, B2-01, B5-01 | algoritmo, serialización, aprobación y revocación documental | el par debe ser inseparable, reproducible y aprobado antes de considerar la campaña | `OPEN` | no aprobar la pareja ni el digest por inferencia |
| B7-01 | C10, C12 | campañas, reintentos y contradicciones | definir campañas, reintentos, cierre y resolución de contradicciones | `AUTHORITY NOT IDENTIFIED` | matriz de campañas, contradicciones y autoridad resolución | B2-01, B4-01, B8-01 | protocolo documental de campaña, reintentos y conflicto | cada campaña debe tener ciclo de vida, conflicto y resolución documentados | `OPEN` | no cerrar campañas ni decisiones conflictivas por resumen |
| B8-01 | C11 | trazabilidad completa requisito → decisión → evidencia | construir la matriz final de trazabilidad | `AUTHORITY NOT IDENTIFIED` | matriz requisito → cláusula → decisión → autoridad → evidencia | todas las anteriores | matriz final row-by-row y evidencia asociada | cada requisito debe relacionarse con su decisión, autoridad y evidencia | `ABSENT` | no declarar trazabilidad completa sin la matriz |

---

## 5. Plan por brecha

### B1-01 — Política protegida, trust root y autoridad

**Criterios relacionados:** C01, C02.

**Decisiones documentales pendientes**
- fuente de confianza;
- protección de la política;
- versión mínima aceptada y anti-rollback;
- autoridad para aprobar, sustituir o revocar la política;
- Rama A y límites de privilegios.

**Trabajo documental requerido**
- cláusula de autoridad de la política;
- artefacto protegido y condiciones de operación;
- definición de versión mínima y condiciones de rechazo;
- separación documental entre política, implementación y validación.

**Dependencias**
- ninguna de las anteriores depende de ejecución real; dependen de decisión de autoridad y especificación.

**Evidencia futura requerida**
- artefacto protegido con identidad y versión;
- decisión de aprobación explícita;
- reglas de revocación y anti-rollback.

**Estado**
- Brecha documentada, no cerrada.
- No existe autoridad identificada para resolverla dentro del alcance actual.

### B2-01 — Identidad y relaciones entre entidades

**Criterio relacionado:** C03.

**Decisiones documentales pendientes**
- distinguir campañas, trabajos, workers, intentos, ejecuciones, evidencias y decisiones;
- definir relaciones, unicidad, ciclo de vida y invalidación.

**Trabajo documental requerido**
- esquema de identidad y relaciones;
- regla de invalidación y caducidad;
- matriz de entidades y dependencias.

**Dependencias**
- B1-01 define autoridad y contexto de confianza.

**Evidencia futura requerida**
- esquema documental final y índices de identidad;
- reglas para generación e invalidación.

**Estado**
- Documentado como requisito; aún no cerrado.

### B3-01 — Procedencia de evidencia y separación de responsabilidades

**Criterios relacionados:** C04, C05.

**Decisiones documentales pendientes**
- procedencia y autenticidad de evidencia;
- identidad de quien produce y revisa la evidencia;
- separación entre worker, observer y verifier;
- permisos de flujo y acceso;
- vinculación entre evidencia, resultado y decisión.

**Trabajo documental requerido**
- modelo de procedencia y validación;
- diagrama o esquema de flujo de evidencia;
- matriz de permisos y roles;
- reglas de rechazo y custodia.

**Dependencias**
- B1-01 y B2-01.

**Evidencia futura requerida**
- evidencia de flujo autorizada, roles y permisos de cada actor.

**Estado**
- Definido como obligación; aún no resuelto como diseño completo.

### B4-01 — Estados y agregación

**Criterio relacionado:** C06.

**Decisiones documentales pendientes**
- estados válidos;
- transiciones permitidas;
- condiciones terminales;
- tratamiento de errores, ausencias o contradicciones;
- regla de agregación por nivel.

**Trabajo documental requerido**
- tabla de estados y transiciones;
- regla de agregación determinista;
- definición de estados desconocidos o inconclusos.

**Dependencias**
- B3-01 para evidencias y flujo;
- B5-01 para preflight y consecuencias.

**Evidencia futura requerida**
- política de estados y agregación asociada a cada criterio.

**Estado**
- requisito identificado; no cerrada la semántica final.

### B5-01 — Preflight, prohibiciones y consecuencias

**Criterios relacionados:** C07, C14.

**Decisiones documentales pendientes**
- control_id;
- predicado verificable;
- evidencia exigida;
- rechazo y consecuencia;
- aún no se puede certificar cumplimiento operativo.

**Trabajo documental requerido**
- tabla de preflight;
- cláusulas de prohibición y evidencia de cumplimiento;
- regla de separación entre declaración y demostración.

**Dependencias**
- B1-01, B3-01, B4-01.

**Evidencia futura requerida**
- preflight formal y regla de rechazo con evidencia de cumplimiento o ausencia de ejecución.

**Estado**
- obligación escrita; cierre no alcanzado.

### B6-01 — `tree_digest` y aprobación indivisible

**Criterios relacionados:** C08, C09.

**Decisiones documentales pendientes**
- entradas del digest;
- normalización y serialización;
- algoritmo de hash;
- orden canónico;
- aprobación y revocación del par `(nodeids, tree_digest)`;
- tratamiento de cambios concurrentes.

**Trabajo documental requerido**
- definición formal del algoritmo y serialización;
- cláusula de aprobación del par;
- regla de revocación y invalidación.

**Dependencias**
- B1-01, B2-01, B5-01.

**Evidencia futura requerida**
- algoritmo canónico documentado;
- aprobación explícita del par y reglas de invalidación.

**Estado**
- requisito conocido; cierre pendiente.

### B7-01 — Campañas, reintentos y contradicciones

**Criterios relacionados:** C10, C12.

**Decisiones documentales pendientes**
- identidad y límites de una campaña;
- reglas de reintento;
- idempotencia;
- terminación y cierre;
- contradicciones y resolución de autoridad.

**Trabajo documental requerido**
- protocolo de campaña;
- registro de contradicciones;
- reglas de reintento y autoridad de resolución.

**Dependencias**
- B2-01, B4-01, B8-01.

**Evidencia futura requerida**
- escenario de campaña, decisiones críticas y autoridad resolutiva.

**Estado**
- brecha identificada y documentada; no cerrada.

### B8-01 — Trazabilidad completa

**Criterio relacionado:** C11.

**Decisiones documentales pendientes**
- construir la matriz final requisito → cláusula → decisión → autoridad → evidencia → adjudicación;
- distinguir evidencia directa, inferencia, ausencia y no evaluable.

**Trabajo documental requerido**
- matriz de trazabilidad row-by-row;
- mapeo de requisitos a decisiones y evidencia.

**Dependencias**
- todas las anteriores, porque cada requisito debe poder mapearse a su decisión y a la evidencia de la decisión.

**Evidencia futura requerida**
- matriz final con cobertura completa, decisión de autoridad y evidencias asociadas.

**Estado**
- `ABSENT` conforme a la evidencia documental disponible.

---

## 6. Dependencias y orden de resolución

La secuencia recomendada es una hipótesis de planificación y debe validarse contra las fuentes. El objetivo es convertir una colección de brechas abiertas en una secuencia de decisiones documentales administrables.

Orden recomendado:

1. B1-01: autoridad, política y trust root.
2. B2-01: identidad y relaciones.
3. B3-01: procedencia y separación de responsabilidades.
4. B4-01: estados y agregación.
5. B5-01: preflight y consecuencias.
6. B6-01: `tree_digest` y par `(nodeids, tree_digest)`.
7. B7-01: campañas, reintentos y contradicciones.
8. B8-01: trazabilidad completa.

**Nota de planificación:** este orden no es una aprobación ni un cierre. Es una recomendación de secuencia documental para reducir ambigüedad y acotar decisiones que dependen de autoridad.

---

## 7. Condiciones de cierre futuro

Cada cierre futuro debe requerir condiciones observables y documentadas, no actividades genéricas. Ejemplos del nivel requerido:

- No: “definir la política”.
- Sí: “la cláusula aplicable identifica a la autoridad competente, el artefacto protegido, las reglas de versión y las condiciones de aprobación y revocación”.
- No: “mejorar la trazabilidad”.
- Sí: “cada requisito contractual aplicable dispone de una relación verificable con la decisión correspondiente, la autoridad y la evidencia que la sustenta, o de una ausencia expresamente adjudicada”.

Cada cierre futuro debe requerir:

1. artefacto documental identificable;
2. cláusula o sección exacta;
3. decisión de autoridad, cuando corresponda;
4. evidencia que satisfaga el predicado de cierre;
5. adjudicación explícita y trazable;
6. verificación de que no se confundió el cierre documental con la validación operativa.

---

## 8. Riesgos de dependencia y bloqueos

Los riesgos principales ya documentados son:

- autoridad no identificada;
- requisitos ambiguos o contradictorios;
- dependencia entre contratos;
- evidencia que aún no existe;
- imposibilidad de verificar preservación histórica;
- riesgo de declarar cierre a partir de una matriz incompleta;
- riesgo de convertir una especificación en autorización implícita.

**Efecto principal**
Estos riesgos impiden cualquier cierre legítimo de Gate B o de las brechas B1–B8 sin una decisión de autoridad y una evidenciación explícita.

---

## 9. Entregables posteriores posibles

STEP-32 no crea ni autoriza automáticamente los siguientes documentos. Solo recomienda una etapa futura si la dependencia está clara y la brecha aún no ha sido resuelta.

Los posibles entregables posteriores pudieran ser:

- una matriz de decisiones y autoridades pendientes;
- un registro formal de decisiones contractuales;
- una especificación documental revisada de contratos concretos;
- una matriz de trazabilidad requisito → decisión → evidencia;
- una futura adjudicación estática de suficiencia documental.

La selección debe depender de los hallazgos reales y del alcance autorizado. No se inicia una nueva secuencia por defecto ni se generan documentos redundantes.

Cualquier etapa posterior requerirá una directiva independiente y deberá respetar los bloqueos vigentes.

---

## 10. Estados canónicos obligatorios

Se registran sin modificación:

- `TALOS V1 = FROZEN`
- `P1.2 = BLOCKED-REGRESSION`
- `P1.3 = BLOCKED`
- `B1-R = NOT AUTHORIZED`
- `EXTERNAL HARNESS IMPLEMENTATION = NOT AUTHORIZED`
- `DYNAMIC VALIDATION = NOT AUTHORIZED`
- `GATE B = INCOMPLETE`

Declaración explícita:

> STEP-32 transforma las brechas documentadas en un plan de resolución futura. No resuelve las brechas, no aprueba contratos, no identifica por inferencia autoridades inexistentes, no valida el sistema y no autoriza implementación ni ejecución.

---

## 11. Entregable único

Se creó únicamente:

`docs/STEP-32-PLAN-DOCUMENTAL-DE-RESOLUCION-DE-BRECHAS-B1-B8.md`

No se modificaron documentos previos.

---

## 12. Informe de cierre

- Ruta exacta del documento creado: `docs/STEP-32-PLAN-DOCUMENTAL-DE-RESOLUCION-DE-BRECHAS-B1-B8.md`
- Identidad observada del checkout: `talos-current-audit` / `cc8acfae623f9d10c8366871470319786b6a7ca4`
- Estado del árbol observado: sin modificaciones atribuibles a esta etapa; no se atribuye una preservación histórica que no haya sido demostrada.
- Brechas planificadas: 8 (`B1-01` a `B8-01`)
- Autoridad aún no identificada: `AUTHORITY NOT IDENTIFIED` para la mayoría de decisiones críticas.
- Orden de resolución recomendado: B1-01 → B2-01 → B3-01 → B4-01 → B5-01 → B6-01 → B7-01 → B8-01.
- Dependencias críticas: B1-01, B2-01, B3-01, B4-01, B5-01, B6-01, B7-01 y B8-01 interactúan en secuencia y no pueden cerrarse por inferencia de la secuencia documental.
- Confirmación: no se ejecutaron tests ni código del proyecto.
- Confirmación: no hubo operaciones Git mutativas.
- Confirmación: `GATE B = INCOMPLETE` y no se concedió autorización operativa.

**FIN DE STEP-32**
