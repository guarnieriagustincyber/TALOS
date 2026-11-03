# TALOS V1.5 — STEP-29

## ADJUDICACIÓN DOCUMENTAL ESTÁTICA Y DETERMINACIÓN DE SUFICIENCIA DE GATE B

**Proyecto:** TALOS V1.5
**Repositorio observado:** `/media/agustin/Laboratorio/study-engie`
**Rama observada:** `talos-current-audit`
**HEAD observado:** `cc8acfae623f9d10c8366871470319786b6a7ca4`
**Documento sometido a adjudicación:** `docs/STEP-28-DESARROLLO-DOCUMENTAL-NORMATIVO-DE-CONTRATOS-B1-B8.md`
**Documento de referencia de criterios:** `STEP-27 — Especificación contractual definitiva de Gate B`
**Tipo:** Adjudicación documental estática, trazabilidad normativa y determinación de suficiencia
**Estado inicial de Gate B:** `INCOMPLETE`
**Implementación:** `NOT AUTHORIZED`
**Validación dinámica:** `NOT AUTHORIZED`

---

## 1. Mandato y alcance

La tarea ejecutada es una adjudicación documental estática y trazable de STEP-28 contra los 15 criterios de aceptación definidos por STEP-27.

**No se reescribió STEP-28.**
**No se implementó nada.**
**No se ejecutaron pruebas, workers, harnesses, preflight, ni validación dinámica.**

El propósito es determinar si STEP-28 define reglas contractuales suficientemente completas, inequívocas y verificables para satisfacer cada criterio de STEP-27, o si siguen existiendo requisitos ausentes, parcialmente especificados, contradictorios o pendientes de decisión de autoridad.

### 1.1. Fuentes examinadas

- STEP-27: documento de criterios y requisitos de aceptación de Gate B.
- STEP-28: documento de especificación contractual de B.1–B.8.
- Antecedentes normativos: STEP-24, STEP-25, STEP-26 y STEP-27, consultados en el historial documental del proyecto y en la evidencia previa del repositorio.

### 1.2. Límites de la evaluación

La adjudicación se restringe a lo observadamente contenido en los documentos de referencia y a los acuerdos normativos que aparecen en ellos. No se utiliza el repositorio como prueba adicional de validación dinámica ni se interpreta el texto como evidencia operativa del sistema.

### 1.3. Corrección documental controlada exigida por STEP-31

La presente revisión es una adjudicación estática de suficiencia documental, no una aprobación contractual ni una certificación operativa del sistema. En consecuencia, la conclusión de `GATE B = INCOMPLETE` debe mantenerse solo como un dictamen de la evidencia disponible y no como un cierre normativo definitivo.

STEP-31 exige corregir tres defectos materiales del expediente original:

1. la matriz de criterios debe ser trazada requisito por requisito contra STEP-27;
2. la prueba documental debe distinguir con claridad entre `OBSERVED`, `STATICALLY_CONFIRMED`, `INFERRED`, `UNKNOWN`, `UNRESOLVED` y `NOT_EXECUTED`;
3. las brechas B.1–B.8 deben transformarse en una matriz contractual de decisiones pendientes y decisiones que requieren autoridad externa.

Con esto, el documento deja de ser un simple resumen y pasa a ser una revisión corregida, que no reemplaza ni valida la implementación, pero sí habilita la siguiente corrección normativa.

---

## 2. Identidad observada del repositorio

**Resultado de inspección estática, no de ejecución:**

- Repositorio: `/media/agustin/Laboratorio/study-engie`
- Rama: `talos-current-audit`
- HEAD: `cc8acfae623f9d10c8366871470319786b6a7ca4`

**Discrepancia posible:** no se observa diferencia con la referencia documental esperada; no se detectan cambios de rama ni modificaciones de HEAD durante la adjudicación documental. La observación es de lectura estática y no se modifica el estado del repositorio.

---

## 3. Método de adjudicación

Para cada criterio de STEP-27 se aplicó este protocolo:

1. Identificar el requisito normativo exacto en STEP-27.
2. Localizar el texto equivalente o relacionado en STEP-28.
3. Determinar si STEP-28 define una regla contractual concreta o solo un requerimiento pendiente.
4. Evaluar si la regla establece autoridad, predicado de aceptación, evidencia, respuesta ante fallo y dependencias.
5. Registrar el resultado según el esquema: `SATISFIED`, `PARTIAL`, `ABSENT`, `CONTRADICTORY`, `NOT EVALUABLE`.
6. Diferenciar claramente entre:
   - `Texto observado`;
   - `Conclusión documental`;
   - `Afirmación no verificada`;
   - `Decision pendiente`.

**Regla aplicada:** una regla que dicte “deberá definirse” o “debe incluirse” no se considera satisfecha si el contenido concreto no aparece realmente en el documento disponible.

---

## 4. Matriz obligatoria de los 15 criterios

| criterion_id | step27_requirement | step28_reference | adjudication | evidence_class | reason_for_status | gap_blocking_higher_status | authority_required |
|---|---|---|---|---|---|---|---|
| C01 | Política protegida con autoridad, versión, integridad y anti-rollback | STEP-27 §13.1; STEP-28 §3.1–§3.4 | `PARTIAL` | `STATICALLY_CONFIRMED` | El documento exige la política protegida y el anti-rollback, pero no define autoridad concreta, versión mínima, downgrade ni revocación | falta la política protegida cerrada y su autoridad | `authority` |
| C02 | Rama A y privilegios verificables | STEP-27 §13.2; STEP-28 §3.2–§3.3 | `PARTIAL` | `STATICALLY_CONFIRMED` | Se menciona el modelo de privilegios, pero no se ofrecen predicados verificables ni evidencia de permisos efectivos | falta diseño documental del usuario dedicado, privilegios y condiciones de fallo | `authority` |
| C03 | Identificadores inequívocos y relaciones | STEP-27 §13.3; STEP-28 §4.1–§4.3 | `PARTIAL` | `STATICALLY_CONFIRMED` | Se mencionan los identificadores, pero falta el esquema exacto, la unicidad y el ciclo de vida | falta el contrato completo de identidad y relaciones | `design` |
| C04 | Procedencia campo por campo de la evidencia | STEP-27 §13.4; STEP-28 §5.1–§5.4 | `PARTIAL` | `STATICALLY_CONFIRMED` | Hay una referencia a procedencia y validación, pero no aparece la matriz de campos, validación y rechazo | falta la matriz de evidencia con autoridad y rechazo | `design` |
| C05 | Separación verificable worker–observer–verifier | STEP-27 §13.5; STEP-28 §5.1–§5.3 | `PARTIAL` | `STATICALLY_CONFIRMED` | Se declara la separación, pero no hay un contrato que cierre permisos, canales, autoridad ni independencia | falta la separación efectiva y el contrato de flujo | `authority` + `design` |
| C06 | Estados definidos con agregación explícita | STEP-27 §13.6; STEP-28 §6.1–§6.4 | `PARTIAL` | `STATICALLY_CONFIRMED` | Existe semántica básica, pero faltan la matriz de agregación y los casos de conflicto por nivel | falta la agregación completa del estado por nivel | `design` |
| C07 | Preflight con predicado y respuesta por cada control | STEP-27 §13.7; STEP-28 §7.1–§7.3 | `PARTIAL` | `STATICALLY_CONFIRMED` | Se enumeran familias de controles, pero no aparece la matriz completa de control_id, predicado y consecuencia | falta el preflight cerrado con evidencias y rechazo | `design` |
| C08 | `tree_digest` determinista y sin ambigüedad | STEP-27 §13.8; STEP-28 §8.1–§8.5 | `PARTIAL` | `STATICALLY_CONFIRMED` | Se exige determinismo, pero no aparece el algoritmo canónico ni la serialización exacta | falta el algoritmo de digest y la política de reconocimiento | `authority` + `design` |
| C09 | Aprobación indivisible de `(nodeids, tree_digest)` | STEP-27 §13.9; STEP-28 §8.1–§8.5 | `PARTIAL` | `STATICALLY_CONFIRMED` | Se menciona la indivisibilidad, pero no hay procedimiento de aprobación ni de revocación | falta la aprobación del par y el manejo del cambio del árbol | `authority` |
| C10 | Trazabilidad de campañas, repeticiones e intentos | STEP-27 §13.10; STEP-28 §9.1–§9.4 | `PARTIAL` | `STATICALLY_CONFIRMED` | Hay semántica general, pero no se cierra el conjunto de reglas para reintentos, cancelación y comparabilidad | falta el contrato de campaña y cierre de intentos | `authority` + `design` |
| C11 | Matriz de trazabilidad de requisitos y decisiones | STEP-27 §13.11; STEP-28 §10.1–§10.4 | `ABSENT` | `STATICALLY_CONFIRMED` | El documento menciona la matriz, pero no incluye la matriz efectiva con filas sustantivas | la trazabilidad del requisito a decisión no existe como evidencia documental | `design` |
| C12 | Registro de contradicciones, decisiones pendientes y preguntas al operador | STEP-27 §13.12; STEP-28 §11–§12 | `PARTIAL` | `STATICALLY_CONFIRMED` | Hay un reconocimiento del problema, pero no hay una mesa de contradicciones con responsables y condiciones de resolución | falta el registro completo de contradicciones y decisiones pendientes | `authority` |
| C13 | Ningún control debe presentarse como validado dinámicamente | STEP-27 §13.13; STEP-28 §0, §1.2, §2, §7.3, §14 | `SATISFIED` | `STATICALLY_CONFIRMED` | El documento divide claramente especificación de validación y prohíbe que la primera sustituya a la segunda | no hay brecha sustantiva en este criterio | `none` |
| C14 | Respeto del alcance y operaciones prohibidas | STEP-27 §13.14; STEP-28 §1.2, §2.2, §14.3 | `PARTIAL` | `STATICALLY_CONFIRMED` | El documento enumera prohibiciones, pero no aporta evidencia independiente de la ausencia de ejecución ni de la cadena de custodia | falta la diferenciación entre “declarado” y “demostrado” | `authority` + `future operational validation` |
| C15 | Preservación de bloqueos y estados canónicos | STEP-27 §13.15; STEP-28 §0.1, §14.4 | `SATISFIED` | `STATICALLY_CONFIRMED` | El documento preserva los estados canónicos y los bloqueos, sin introducir un cierre operativo indebido | no hay brecha sustantiva en este criterio | `none` |

### 4.1. Reconciliación aritmética de los 15 criterios

- `SATISFIED`: 2
- `PARTIAL`: 12
- `ABSENT`: 1
- `CONTRADICTORY`: 0
- `NOT EVALUABLE`: 0

**Resultado final de la matriz:** `GATE B = INCOMPLETE`

### 4.2. Criterio C11: resolución obligada

`C11` debe adjudicarse como `ABSENT` porque STEP-28 no contiene la matriz final de trazabilidad. La mención de una matriz futura no constituye la matriz y no puede elevar la clasificación por mera intención documental.

### 4.3. Criterios C13 y C14: separación de afirmaciones

Para C13 se exige separar claramente la especificación documental de la validación dinámica real. El documento cumple esta separación documental.

Para C14 el criterio exige distinguir entre:

1. una prohibición declarada;
2. una afirmación de no ejecución;
3. la evidencia independiente que verifica la ausencia de ejecución.

El texto de STEP-28 cumple la declarativa, pero no demuestra la tercera parte. Por eso C14 queda en `PARTIAL`, no en `SATISFIED`.

---

## 5. Auditoría transversal obligatoria de B.1–B.8

### 5.1. B.1 — Trust root y anti-rollback

**Estado documental:** `PARTIAL`

**Lo que está cubierto:**
- se exige un artefacto de política protegido;
- se exige que haya autoridad raíz y anti-rollback;
- se separan hash y autoridad;
- se exige un orden de confianza;
- se exige tratar fallos cerrados.

**Lo que falta:**
- una definición concreta del artefacto;
- una autoridad raíz identificada;
- un procedimiento de versión mínima y downgrade;
- una regla de actualización, revocación y recuperación;
- una forma de distinguir política válida, corrupta, ausente o incompatible.

**Conclusión:** no se cierra un contrato de trust root que pueda sostener la aceptación documental del criterio C01.

### 5.2. B.2 — Identificadores y relaciones

**Estado documental:** `PARTIAL`

**Lo que está cubierto:**
- se enumeran los identificadores obligatorios;
- se mencionan relaciones semánticas y no sobrescritura.

**Lo que falta:**
- formato real y restricciones;
- autoridad de generación;
- unicidad de cada combinación;
- inmutabilidad y persistencia;
- distinción de repetición e intento;
- tratamiento de duplicados y malformaciones.

**Conclusión:** el esquema no es cerrado ni completamente verificable.

### 5.3. B.3 — Evidencia y procedencia

**Estado documental:** `PARTIAL`

**Lo que está cubierto:**
- distinción entre fuentes de evidencia;
- separación observer–verifier;
- campos a incluir en el esquema.

**Lo que falta:**
- matriz de autoridad y procedencia campo por campo;
- campos obligatorios, opcionales y condicionales;
- reglas de validación y rechazo detalladas;
- contrato del verifier con entrada/salida;
- protección real del canal observer→verifier.

**Conclusión:** la evidencia no está formalizada lo bastante para cerrar el requisito C04 y C05.

### 5.4. B.4 — Estados y agregación

**Estado documental:** `PARTIAL`

**Lo que está cubierto:**
- seis estados; semántica básica; prohibición de que un PASS borre un FAIL previo.

**Lo que falta:**
- matriz de agregación completa;
- nivel control/preflight/observación/intento/repetición/caso/campaña/gate;
- casos de conflicto entre observer y verifier, digest alterado, evidencia inválida, ausencia de repeticiones y fallos del verifier.

**Conclusión:** no hay una semántica de agregación cerrada para todas las capas.

### 5.5. B.5 — Preflight

**Estado documental:** `PARTIAL`

**Lo que está cubierto:**
- familias de controles;
- estructura del control;
- regla general de no aprobación por omisión.

**Lo que falta:**
- una matriz completa de controles con `control_id`, autoridad, predicado y consecuencia;
- respuesta ante ausencia de evidencia;
- requisitos específicos de cgroups, seccomp, filesystem, red y secretos;
- definición concreta de aceptación y bloqueo.

**Conclusión:** la etapa de preflight queda representada, no cerrada.

### 5.6. B.6 — `tree_digest` y `nodeids`

**Estado documental:** `PARTIAL`

**Lo que está cubierto:**
- la pareja indivisible `(nodeids, tree_digest)`;
- los elementos que deben incluirse en la definición;
- la exclusión de candidatos no versionados.

**Lo que falta:**
- un algoritmo canónico reproducible;
- una serialización exacta y un orden canónico;
- decisión de inclusión/exclusión de metadatos y enlaces simbólicos;
- procedimiento de aprobación final del par;
- tratamiento de cambios concurrentes y archivos inesperados.

**Conclusión:** la definición es conceptual, no definitiva.

### 5.7. B.7 — Repeticiones, intentos y reintentos

**Estado documental:** `PARTIAL`

**Lo que está cubierto:**
- distingue campaña, repetición, intento y observación;
- prohíbe reintentos silenciosos;
- reconoce la presencia de 30 observaciones planificadas y 10 casos.

**Lo que falta:**
- máximo de intentos por repetición;
- reglas de cierre y cancelación;
- decisión exacta de reintento autorizado;
- comparabilidad de repeticiones;
- preservación del intento fallido y trato de interrupciones.

**Conclusión:** la política de campaña queda planteada, no cerrada.

### 5.8. B.8 — Trazabilidad y decisiones

**Estado documental:** `ABSENT` en la práctica

**Lo que está cubierto:**
- se exige la matriz de trazabilidad.

**Lo que falta:**
- las filas reales de trazabilidad;
- las referencias de requisitos a contratos;
- el mapeo entre autoridad, evidencia y decisión pendiente;
- una matriz legítima de dependencias y contradictorias.

**Conclusión:** no aparece la prueba documental de la matriz final exigida por STEP-27.

---

## 6. Contradicciones y decisiones pendientes

### 6.1. Contradicciones o ambigüedades documentales

1. Step-28 afirma que el trabajo es completo y documentado, pero la forma en que explica los requisitos quedó también como trabajo abierto. No hay una regla que transforme “deberá especificarse” en “ya está especificado”.
2. Hay una fuerte separación entre especificación y ejecución, pero el texto no prohíbe que una parte del documento sea interpretada como si hubiera validado un control apenas por describirlo.
3. El documento presenta a `B.8` como obligatorio, pero no incluye la matriz completa requerida. Esa discrepancia es relevante para el cierre del Gate.
4. Ciertas decisiones de autoridad aparecen como “pendientes” o “requeridas”, pero no se especifica quién las resuelve ni en qué momento.

### 6.2. Decisiones que requieren autoridad externa

- autoridad de la raíz de confianza y del artefacto protegido;
- aprobación de la política mínima y del mecanismo anti-rollback;
- autoridad del inventario de nodeids y del digest del árbol;
- autoridad que aprueba la separación entre worker, observer y verifier;
- autoridad que cierra reglas de campaña, reintentos y cancelación;
- autoridad que resuelve contradicciones entre procedimientos y evidencia.

**Estas decisiones no se sustituyen por una especificación interna del documento.**

---

## 7. Resultado de Gate B

### 7.1. Criterio de cierre de STEP-27

STEP-27 exige que los 15 criterios sean `SATISFIED` para declarar `GATE B = SPECIFIED`.

### 7.2. Estado de la adjudicación

**Conteo por estado del conjunto de 15 criterios:**

- `SATISFIED`: 2
- `PARTIAL`: 12
- `ABSENT`: 1
- `CONTRADICTORY`: 0
- `NOT EVALUABLE`: 0

### 7.3. Dictamen

**DICTAMEN FINAL:** `GATE B = INCOMPLETE`

**Justificación documental:**
- STEP-28 contiene un marco sintáctico completo y una organización útil de los contratos B.1–B.8.
- Sin embargo, la evidencia textual disponible no demuestra que el conjunto de requisitos exigidos por STEP-27 esté completamente especificado, cerrado y verificable documentalmente.
- La diferencia entre “describir un requisito” y “cerrar un requisito” sigue siendo decisiva.
- No se puede cerrar Gate B sin una especificación operativa completa de la raíz de confianza, la identidad contractual, el preflight, la firma de inventario y la trazabilidad final.

**No se autoriza por esta adjudicación:**
- implementación del harness;
- ejecución de preflight;
- validación dinámica;
- aprobación de `(nodeids, tree_digest)`;
- apertura de B1-R o cualquier fase técnica posterior.

---

## 8. Brechas documentales críticas

1. **Raíz de confianza y anti-rollback no cerrados**: falta una autoridad que apruebe y certifique la política protegida.
2. **Identidad sin esquema completo**: no hay un esquema normativo cerrado de identidad, unicidad y relaciones.
3. **Evidencia y separación no cerradas**: falta la matriz de campos y la definición de permisos entre worker, observer y verifier.
4. **Agregación incompleta**: no existe la matriz completa de agregación para todos los niveles de la campaña.
5. **Preflight incompleto**: faltan predicados concretos y consecuencias de fallo por control.
6. **`tree_digest` no canónico**: falta un algoritmo reproducible y completo.
7. **Trazabilidad B.8 absent**: no aparece la matriz de trazabilidad exigida fila por fila.
8. **Reglas de campaña todavía abiertas**: no están cerrados reintentos, cancelación, comparabilidad y cierre de campaña.

---

## 9. Estado canónico preservado

Se conserva sin modificación:

- `TALOS V1 = FROZEN`
- `P1.2 = BLOCKED-REGRESSION`
- `P1.3 = BLOCKED`
- `B1-R = NOT AUTHORIZED`
- `EXTERNAL HARNESS IMPLEMENTATION = NOT AUTHORIZED`
- `DYNAMIC VALIDATION = NOT AUTHORIZED`
- `GATE B = INCOMPLETE`

Se preservan además los bloqueos B06, la anomalía histórica Git no resuelta y la exclusión de candidatos no versionados del inventario aprobado.

---

## 10. Próxima acción documental recomendada

La siguiente acción recomendada no es una implementación ni una ejecución; es una corrección documental dirigida a cerrar los 8 huecos críticos antes de intentar un segundo cierre de Gate B.

Se recomienda:

1. cerrar la definición definitiva del artefacto de política y su autoridad;
2. definir la identidad contractual de campaña, repetición e intento con formato y restricciones;
3. cerrar la matriz de evidencia campo por campo y la separación worker–observer–verifier;
4. cerrar la matriz de agregación de estados por nivel;
5. cerrar la matriz de preflight con control_id, predicado y fallo;
6. cerrar el algoritmo y la aprobación del par `(nodeids, tree_digest)`;
7. cerrar la matriz de trazabilidad exigida por B.8;
8. registrar las contradicciones y decisiones pendientes en una tabla de autoridad explícita.

**No se autoriza ninguna fase técnica ni dinámica como consecuencia de STEP-29.**

---

## 11. Conclusión final

La adjudicación estática del material disponible indica que STEP-28 es una base contractualmente útil, pero no suficiente para cerrar Gate B conforme a STEP-27. El texto demuestra una intención y una estructura, pero no una especificación contractual completa y cerrada para cada criterio de aceptación.

**Resultado final de STEP-29:** `GATE B = INCOMPLETE`.
