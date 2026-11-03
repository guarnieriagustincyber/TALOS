# TALOS V1.5 — STEP-27

## ESPECIFICACIÓN CONTRACTUAL DEFINITIVA DE GATE B

**Tipo:** Diseño contractual, análisis estático y documentación
**Predecesora:** STEP-26 — Cierre documental de Gate A
**Gate A:** Cerrado documentalmente, sujeto al alcance y las limitaciones del expediente STEP-26
**Gate B:** En especificación
**Implementación:** NO AUTORIZADA
**Validación dinámica:** NO AUTORIZADA
**Harness externo B1-R:** NO AUTORIZADO

---

## 0. OBJETIVO

Desarrollar la especificación contractual de Gate B para TALOS V1.5, transformando las decisiones D1–D6 de Gate A en requisitos precisos, verificables y trazables.

La especificación debe eliminar ambigüedades en torno a:

1. La raíz de confianza y el artefacto único de política.
2. La identidad de campañas, ejecuciones, casos, workers e intentos.
3. La procedencia, integridad e independencia de la evidencia.
4. La semántica de los estados y su agregación.
5. Los criterios obligatorios del preflight.
6. El inventario normativo de tests y su relación con `tree_digest`.
7. Las repeticiones, fallos, interrupciones y reintentos.
8. La trazabilidad entre requisitos, componentes, evidencias y decisiones.

El resultado debe permitir que una futura fase de implementación reciba un contrato cerrado, sin tener que decidir por su cuenta cuestiones que afectan a la seguridad, la autoridad o los criterios de aprobación.

**STEP-27 no implementa el contrato ni demuestra que los controles estén operativos.** Produce exclusivamente documentación contractual y evidencia estática permitida.

## 1. ESTADO CANÓNICO Y LÍMITES

Conservar sin modificaciones:

- `P1.2 = BLOCKED-REGRESSION`
- `P1.3 = BLOCKED`
- `B1-R = NOT AUTHORIZED`
- `External harness = NOT AUTHORIZED`
- TALOS V1 permanece congelado.
- Playwright permanece limitado a regresión congelada.
- Qwen permanece bloqueado.
- Bases de datos, corpus, snapshots y estado de aprendizaje de producción permanecen protegidos.

STEP-26 reporta el cierre documental de Gate A y el registro por SHA-256 de los archivos untracked identificados en ese expediente. Usar STEP-26 como antecedente documental, sin convertir sus afirmaciones en una verificación independiente del estado actual del repositorio.

Si la inspección de los documentos disponibles revela una inconsistencia, registrar la discrepancia y su evidencia. No reescribir retrospectivamente los expedientes anteriores para ocultarla.

## 2. OPERACIONES AUTORIZADAS Y PROHIBIDAS

### 2.1 Autorizadas

- Lectura de documentación y archivos existentes.
- Inspección estática de código y configuración, cuando sea necesaria para comprender contratos existentes.
- Comparación documental entre STEP-24, STEP-25 y STEP-26.
- Identificación de requisitos no resueltos y contradicciones.
- Elaboración de tablas, esquemas, pseudocódigo no ejecutable y ejemplos documentales.
- Creación de un único expediente documental STEP-27 en una ubicación documental apropiada ya existente.
- Lectura del documento generado para comprobar su integridad documental.

Si el acceso a un antecedente no está disponible, registrar la limitación. No inventar su contenido.

### 2.2 Prohibidas

No ejecutar:

- Tests ni suites.
- `pytest`, incluido `--collect-only`.
- Workers, campañas o componentes del harness.
- Bubblewrap (`bwrap`), `unshare` u otros experimentos de aislamiento.
- Imports del backend, creación de la aplicación, lifespan o inicialización de contenedores.
- Builds, benchmarks, hooks o validaciones dinámicas.
- Instalaciones, actualizaciones de dependencias o cambios de configuración.
- Comandos Git que alteren el repositorio.
- Migraciones o escrituras en bases de datos, corpus, snapshots o estado de aprendizaje.
- Creación de código ejecutable para el bootstrap, controlador, worker, observer o verifier.
- Modificación o incorporación de archivos candidatos untracked.
- Generación o aprobación efectiva del inventario normativo de nodeids.
- Cambios en el perfil seccomp, cgroups, permisos del sistema operativo o política de confianza.

No realizar una operación por el solo hecho de que parezca útil para completar la especificación. Si requiere ejecución o modificación, documentarla como pendiente de una autorización posterior.

## 3. REGLAS DE CALIDAD Y PROCEDENCIA

Cada requisito, afirmación o conclusión relevante debe distinguir entre:

- `OBSERVED`: observado directamente mediante una operación permitida.
- `STATICALLY_CONFIRMED`: confirmado en los archivos inspeccionados.
- `INFERRED`: deducción no demostrada directamente.
- `UNKNOWN`: evidencia insuficiente.
- `UNRESOLVED`: cuestión pendiente que no puede resolverse con el material disponible.
- `NOT_EXECUTED`: comprobación que no se realizó.

Cada requisito contractual debe disponer de un identificador estable. Se recomienda la convención `GB-POL-*`, `GB-ID-*`, `GB-EVD-*`, `GB-STATE-*`, `GB-PREFLIGHT-*`, `GB-INV-*`, `GB-CAMPAIGN-*` y `GB-TRACE-*`, según el área.

Cada requisito debe expresar:

1. Qué se exige.
2. Qué componente o autoridad es responsable.
3. Qué condición observable permite aceptarlo.
4. Qué evidencia deberá existir.
5. Qué ocurre cuando no se satisface.
6. Qué cuestiones permanecen fuera del alcance.
7. Qué autorización se necesitará para verificarlo.

No afirmar que un control es efectivo por estar descrito en el contrato o presente en un archivo de configuración.

---

# 4. B.1 — CONTRATO DE POLÍTICA Y RAÍZ DE CONFIANZA

## 4.1 Autoridad

Especificar un único artefacto de política protegido fuera del checkout, bajo la autoridad de la raíz de confianza aprobada en Gate A.

La política debe gobernar, como mínimo:

- Identidad y versión del artefacto.
- Versión mínima aceptada.
- Bootstrap y autorización previa a cualquier importación de código del checkout.
- Mecanismo de anti-rollback.
- Requisitos de identidad y privilegios.
- Preflight obligatorio.
- Requisitos de aislamiento.
- Versión y capacidades requeridas de Bubblewrap.
- Requisitos de cgroups v2 y límites efectivos.
- Perfil seccomp aprobado.
- Política de filesystem, montajes, red y secretos.
- Identidad y requisitos de independencia del observer y del verifier.
- Condiciones de fallo cerrado.
- Procedimiento de actualización, revocación y recuperación.

No distribuir la autoridad entre archivos que puedan aceptar políticas diferentes. Los componentes auxiliares pueden existir, pero no deben constituir raíces de confianza alternativas.

## 4.2 Modelo de privilegios

Formalizar la Rama A:

- El agente y los workers se ejecutan con un usuario de sistema operativo dedicado.
- Ese usuario no tiene `sudo`, privilegios equivalentes ni vías autorizadas de elevación.
- No puede modificar la política protegida ni el bootstrap.
- No puede aprobar sus propias actualizaciones de confianza.
- La autoridad privilegiada y la aprobación de cambios permanecen fuera de su dominio.

El contrato debe especificar las condiciones verificables necesarias para considerar válida esta separación.

No definir como aceptable una mera comprobación nominal del usuario. Deben contemplarse grupos, reglas de elevación, permisos efectivos y mecanismos equivalentes de escalada.

## 4.3 Anti-rollback y actualización

Definir:

- Representación de versión.
- Fuente protegida de la versión mínima.
- Regla de rechazo de versiones anteriores.
- Comportamiento ante estado de versión ausente, corrupto o contradictorio.
- Autoridad que aprueba una actualización.
- Procedimiento de revocación.
- Tratamiento de una actualización interrumpida.
- Evidencia de la decisión de aceptar o rechazar la política.

No asumir que un contador almacenado en un archivo modificable por el agente proporciona anti-rollback.

Si el material disponible no permite determinar un mecanismo seguro y compatible con las restricciones de la Rama A, registrar la decisión técnica pendiente. No inventar un mecanismo supuestamente efectivo.

## 4.4 Contrato de integridad del artefacto

Definir qué significa que la política sea válida:

- Identidad esperada.
- Versión autorizada.
- Integridad verificable.
- Esquema válido.
- Campos obligatorios.
- Autoridad de actualización válida.

Definir el comportamiento ante cada incumplimiento. Los errores de política deben impedir el inicio de una futura ejecución protegida.

**Entregable B.1:** contrato del artefacto de política, modelo de autoridad, reglas de actualización y matriz de aceptación y rechazo.

---

# 5. B.2 — IDENTIDAD DE CAMPAÑAS, EJECUCIONES Y OBSERVACIONES

## 5.1 Entidades

Especificar los siguientes identificadores:

- `campaign_id`: identifica una campaña autorizada.
- `run_id`: identifica una ejecución lógica dentro de la campaña.
- `case_id`: identifica un caso autorizado.
- `nodeid`: identifica el test concreto dentro del inventario aprobado.
- `repetition_index`: identifica la repetición prevista de un caso.
- `attempt_id`: identifica un intento concreto, incluidos los fallidos o interrumpidos.
- `worker_id`: identifica una instancia de worker.
- `tree_digest`: identifica el árbol de código autorizado conforme al algoritmo contractual.

Si se necesita un identificador adicional para una observación, un artefacto o una sesión del observer, justificarlo y especificar su relación con las entidades anteriores.

## 5.2 Reglas de unicidad y relación

Definir formalmente:

1. Qué autoridad crea cada identificador.
2. En qué momento se asigna.
3. Qué campos son inmutables.
4. Qué combinaciones deben ser únicas.
5. Cómo se representan las relaciones entre campaña, caso, repetición e intento.
6. Cómo se distingue una nueva repetición de un reintento.
7. Cómo se identifica un worker reutilizado, si el diseño llegara a permitirlo.
8. Cómo se rechazan identificadores ausentes, duplicados, malformados o contradictorios.

Los identificadores proporcionados por un worker no pueden sustituir sin validación los asignados por la autoridad de campaña.

No elegir formatos de UUID, ULID, secuencias o marcas temporales por preferencia estética. Establecer primero los requisitos de unicidad, orden, trazabilidad y generación segura; después justificar la representación seleccionada.

## 5.3 Vinculación al árbol autorizado

Toda observación aceptable debe quedar vinculada al `tree_digest` aprobado para la campaña.

No aceptar observaciones de árboles distintos como si pertenecieran a una misma campaña autorizada.

**Entregable B.2:** esquema de identidad, relaciones, invariantes de unicidad y ejemplos documentales de identidades válidas e inválidas.

---

# 6. B.3 — CONTRATO DE EVIDENCIA DEL OBSERVER Y DEL VERIFIER

## 6.1 Separación de autoridad

Definir la procedencia de la evidencia mediante una matriz que distinga:

- Evidencia generada por el worker.
- Evidencia observada externamente.
- Evidencia de autorización emitida por el controlador.
- Evidencia de validación emitida por el verifier.
- Evidencia auxiliar que no puede determinar por sí sola el resultado.

El worker no puede ser la autoridad única sobre su propio estado, cumplimiento, aislamiento o resultado.

## 6.2 Canal de evidencia

La especificación debe exigir:

- Un canal controlado para los registros del observer.
- Lectura del canal por el verifier mediante la vía aprobada.
- Ausencia de acceso del worker a ese canal, tanto de lectura como de escritura.
- Protección frente a sustitución, eliminación, duplicación y modificación indirecta.
- Detección de registros ausentes, parciales o contradictorios.
- Vinculación de cada registro con su procedencia e identidad de campaña.
- Tratamiento definido de interrupciones del observer o verifier.

Describir las garantías exigidas, no fingir que una implementación concreta ya las proporciona.

## 6.3 Esquema mínimo de evidencia

Especificar los campos obligatorios, su autoridad y su validación. Como mínimo, considerar:

- Versión del esquema.
- Identidad de campaña, ejecución, caso, repetición e intento.
- `nodeid` autorizado.
- `worker_id`.
- `tree_digest`.
- Identidad de la política aprobada.
- Resultado del preflight.
- Controles obligatorios evaluados.
- Estado observado del proceso.
- Resultado y código de salida, cuando sean observables.
- Inicio y fin, con semántica temporal definida.
- Referencias a logs y artefactos.
- Estado de integridad de la evidencia.
- Identidad de la fuente que produjo cada campo.

Determinar qué campos son obligatorios, opcionales o condicionales. La ausencia de un campo obligatorio no puede interpretarse como éxito.

## 6.4 Integridad y duplicados

Especificar cómo detectar:

- Registros duplicados.
- Claves JSON duplicadas.
- Campos desconocidos no permitidos, cuando el esquema requiera rechazo estricto.
- Tipos incorrectos.
- Referencias a artefactos inexistentes.
- Identidades contradictorias.
- Secuencias imposibles.
- Registros incompletos.
- Evidencia producida por una fuente no autorizada.

La canonicalización, los hashes, las firmas o los mecanismos de encadenamiento solo deben exigirse si se define qué amenaza mitigan, qué autoridad los valida y cómo se manejan las claves. Un hash aislado no demuestra por sí mismo autenticidad ni independencia.

## 6.5 Verifier

Definir el contrato de entrada y salida del verifier:

- Entradas aceptadas.
- Esquemas admitidos.
- Validaciones obligatorias.
- Condiciones de rechazo.
- Resultados posibles.
- Tratamiento de errores.
- Evidencia de la decisión.
- Independencia respecto del worker y del código que está verificando.

El verifier no debe aceptar una conclusión de éxito simplemente porque la produjo el controlador o el worker. Debe evaluar las evidencias exigidas por el contrato.

**Entregable B.3:** esquema de evidencia, matriz de procedencia por campo, reglas de validación y contrato de entrada/salida del verifier.

---

# 7. B.4 — SEMÁNTICA DE ESTADOS Y AGREGACIÓN

## 7.1 Estados normativos

Definir explícitamente:

- `PASS`
- `FAIL`
- `BLOCKED`
- `UNKNOWN`
- `INVALID`
- `NOT_EXECUTED`

No introducir sin justificación otros estados terminales. Si se necesitan estados intermedios, distinguirlos de los resultados de adjudicación.

## 7.2 Definiciones mínimas

- `PASS`: evidencia válida, suficiente y de procedencia adecuada demuestra que se satisface el criterio.
- `FAIL`: evidencia válida demuestra que se incumple un criterio obligatorio.
- `BLOCKED`: una condición identificada impide autorizar o iniciar una fase.
- `UNKNOWN`: la evidencia disponible no permite determinar si se satisface el criterio.
- `INVALID`: la observación o la evidencia incumple el contrato y no puede aceptarse como válida.
- `NOT_EXECUTED`: la comprobación no se realizó.

Una observación puede ser inválida sin demostrar que el comportamiento sometido a prueba haya fallado. El contrato debe preservar esta distinción.

## 7.3 Precedencia y agregación

Definir reglas explícitas para agregar estados por:

1. Control individual.
2. Preflight.
3. Observación.
4. Intento.
5. Repetición.
6. Caso.
7. Campaña.
8. Gate.

Resolver, como mínimo:

- Qué ocurre si existe un `FAIL` junto con observaciones válidas y exitosas.
- Qué ocurre si falta una repetición obligatoria.
- Qué ocurre si una evidencia es `INVALID`.
- Qué ocurre si el estado de una observación es `UNKNOWN`.
- Qué ocurre si el entorno bloquea el inicio.
- Qué ocurre si observer y verifier discrepan.
- Qué ocurre si una observación está duplicada.
- Qué ocurre si se detecta un cambio de `tree_digest`.
- Qué ocurre si el propio verifier falla o no produce resultado.

No permitir que una repetición posterior borre el registro de un intento fallido anterior.

No reducir todos los errores a `FAIL` ni convertir toda ausencia de evidencia en `BLOCKED`. La clasificación debe corresponder a la causa y al nivel de agregación.

## 7.4 Matriz de decisión

Incluir una tabla con entradas, condición, resultado asignado, alcance del resultado y consecuencia sobre la campaña.

Debe cubrir las combinaciones relevantes y explicar los casos no combinables o contradictorios.

**Entregable B.4:** taxonomía de estados, matriz de transición y reglas de agregación desde controles hasta campaña.

---

# 8. B.5 — PREFLIGHT Y CRITERIOS DE ACEPTACIÓN

## 8.1 Contrato de cada control

Cada requisito de preflight debe disponer de:

- `control_id`.
- Objetivo de seguridad.
- Fuente de autoridad.
- Predicado de aceptación.
- Evidencia necesaria.
- Componente responsable de observarlo.
- Condición de fallo.
- Estado ante evidencia ausente.
- Consecuencia sobre la autorización de inicio.
- Dependencias de otros controles.

## 8.2 Familias obligatorias

### A. Identidad y privilegios

Definir cómo se comprobarán la identidad efectiva, los grupos, las reglas de elevación y las capacidades del usuario ejecutor.

### B. Política y bootstrap

Definir cómo se comprobarán la integridad, la autoridad, la versión, el anti-rollback y la autorización previa a cualquier importación del checkout.

### C. Bubblewrap y aislamiento

Definir las capacidades y condiciones requeridas. La presencia del ejecutable o de una línea de comandos no demuestra aislamiento efectivo.

### D. Recursos

Definir los límites de CPU, memoria, procesos y tiempo, así como las condiciones que permiten demostrar que son efectivos. Incluir almacenamiento si el threat model y el diseño lo requieren.

### E. cgroups v2

Definir los controladores requeridos, cómo se verifica su disponibilidad y qué ocurre si no pueden aplicarse los límites.

### F. seccomp

Definir la identidad del perfil aprobado, su vínculo con la política protegida, las condiciones de aplicación y las evidencias requeridas para demostrar que se aplica según lo previsto.

### G. Filesystem, red y secretos

Definir los accesos permitidos y prohibidos, los montajes, los namespaces y las reglas de exposición de secretos.

### H. Observer y verifier

Definir las condiciones mínimas para garantizar el canal protegido, la separación de accesos y la disponibilidad del mecanismo de evidencia.

## 8.3 Regla de autorización

El preflight debe finalizar en un resultado explícito.

Si un control obligatorio falla o no puede verificarse, no se autoriza el inicio de la campaña protegida. La especificación debe diferenciar un incumplimiento demostrado de una condición que no puede determinarse.

No ejecutar ni simular el preflight bajo STEP-27.

**Entregable B.5:** matriz completa de preflight y criterios de aceptación, con referencias a B.1–B.4.

---

# 9. B.6 — INVENTARIO NORMATIVO Y `tree_digest`

## 9.1 Unidad de aprobación

El inventario normativo debe ser la pareja indivisible:

`(nodeids, tree_digest)`

Ninguna lista de nodeids es normativa sin su digest aprobado. Ningún digest constituye por sí solo prueba de cobertura.

## 9.2 Definición del árbol

Especificar documentalmente:

- Raíz exacta del árbol.
- Rutas incluidas.
- Rutas excluidas y su justificación.
- Tratamiento de archivos regulares.
- Tratamiento de enlaces simbólicos.
- Tratamiento de directorios vacíos, si corresponde.
- Tratamiento de archivos generados y metadatos relevantes.
- Codificación de rutas.
- Orden canónico.
- Separación inequívoca de entradas.
- Algoritmo de hash.
- Tratamiento de errores de lectura y cambios concurrentes.

No definir el digest como una concatenación ambigua de nombres y contenidos. La especificación debe permitir que dos implementaciones conformes produzcan el mismo digest para el mismo árbol autorizado.

No inventar exclusiones para obtener un digest conveniente.

## 9.3 Aprobación de nodeids

Definir la autoridad que propone y aprueba el inventario, y cómo se vincula la lista al digest exacto del árbol revisado.

El procedimiento futuro deberá comparar exactamente:

- Nodeids esperados y aprobados.
- Nodeids obtenidos del árbol autorizado.
- Nodeids ejecutados y reportados.

Especificar el tratamiento de ausencias, adicionales, duplicados, errores de colección y casos no ejecutados.

La coincidencia de nombres no sustituye la identidad del árbol. Un cambio de digest invalida la aprobación anterior salvo que una política explícita y previamente aprobada disponga lo contrario; no crear esa excepción implícitamente.

## 9.4 Exclusión de candidatos actuales

Los archivos untracked registrados en STEP-26 no se vuelven normativos por estar hasheados. Permanecen excluidos hasta que una fase separada autorice su revisión e incorporación.

**Entregable B.6:** algoritmo documental de digest, política de inclusiones/exclusiones y procedimiento de aprobación de `(nodeids, tree_digest)`.

---

# 10. B.7 — CAMPAÑA, REPETICIONES Y REINTENTOS

## 10.1 Diseño previsto

La campaña de referencia contempla:

- 10 casos.
- 3 repeticiones planificadas por caso.
- 30 observaciones planificadas.

Esta cantidad define el diseño previsto, no demuestra que exista un inventario aprobado ni autoriza la ejecución.

## 10.2 Independencia

Definir qué condiciones hacen independientes las tres repeticiones:

- Identidad y ciclo de vida del worker.
- Aislamiento del workspace.
- Estado inicial permitido.
- Dependencias compartidas.
- Recursos compartidos.
- Artefactos de entrada.
- Política y digest comunes.
- Evidencia que permite demostrar la independencia.

No afirmar independencia únicamente porque existan tres registros o tres identificadores distintos.

## 10.3 Ciclo de vida de una observación

Especificar las transiciones desde la planificación hasta el cierre:

- Planificada.
- Autorizada.
- Preflight aprobado o rechazado.
- Iniciada.
- Finalizada, interrumpida o fallida.
- Evidencia recibida.
- Evidencia validada o invalidada.
- Resultado adjudicado.

Distinguir estado del proceso, estado de la evidencia y resultado de adjudicación.

## 10.4 Reintentos

No se permiten reintentos automáticos silenciosos.

Definir:

- Quién puede autorizar un reintento.
- Qué motivo debe registrarse.
- Cómo se asigna un nuevo `attempt_id`.
- Cómo se relaciona con el intento anterior.
- Cómo se preserva la evidencia de ambos intentos.
- Cómo se evita contar un reintento como una nueva repetición independiente.
- Qué fallos bloquean la campaña.
- Qué circunstancias requieren una nueva campaña y una nueva aprobación.

Los intentos fallidos o interrumpidos no deben desaparecer del registro ni quedar sustituidos por el resultado de un intento posterior.

## 10.5 Cierre de campaña

Definir las condiciones para declarar la campaña completa, incompleta, bloqueada, inválida o no concluyente.

El cierre debe comprobar cobertura, identidad, integridad, procedencia y estados de todas las observaciones obligatorias.

**Entregable B.7:** protocolo de campaña, máquina de estados de observación e intento, reglas de independencia y condiciones de cierre.

---

# 11. B.8 — MATRIZ DE TRAZABILIDAD Y REVISIÓN CONTRACTUAL

## 11.1 Matriz obligatoria

Crear una fila por requisito contractual, con estas columnas:

- `requirement_id`
- `gate_a_decision`
- `requirement`
- `authority`
- `component`
- `acceptance_predicate`
- `required_evidence`
- `failure_behavior`
- `current_status`
- `verification_gate`
- `authorization_required`
- `dependencies`

## 11.2 Revisión cruzada

Verificar documentalmente que:

- Todo requisito de D1–D6 aparece en al menos un requisito contractual.
- Ningún requisito de seguridad carece de criterio de aceptación.
- Ningún criterio de aceptación depende de una autoridad no identificada.
- Ningún `PASS` puede emitirse sin evidencia válida y suficiente.
- La ausencia de evidencia no puede transformarse implícitamente en éxito.
- El worker no es la autoridad de su propia evidencia.
- El preflight, el verifier y la campaña aplican una semántica coherente de estados.
- `tree_digest` es consistente entre inventario, observaciones y campaña.
- Los fallos y reintentos conservan su trazabilidad.
- Los archivos candidatos siguen excluidos del inventario normativo.
- Ninguna especificación se presenta como implementación ya realizada.

## 11.3 Contradicciones y cuestiones pendientes

Crear un registro explícito de:

- Contradicciones encontradas.
- Decisiones técnicas todavía no aprobadas.
- Requisitos que no pueden formularse de forma verificable con la evidencia disponible.
- Dependencias externas no identificadas.
- Riesgos residuales.
- Preguntas que requieren una decisión del operador.

No resolver silenciosamente una cuestión de autoridad, seguridad o aceptación mediante una preferencia del agente.

**Entregable B.8:** matriz de trazabilidad, informe de coherencia y registro de decisiones pendientes.

---

# 12. ESTRUCTURA DEL EXPEDIENTE STEP-27

Crear un único documento nuevo con una estructura equivalente a:

1. Identificación, alcance y estado canónico.
2. Fuentes consultadas y límites de evidencia.
3. Contrato de política y raíz de confianza.
4. Identidad de campañas y observaciones.
5. Esquema de evidencia y contrato del verifier.
6. Semántica de estados y agregación.
7. Preflight y criterios de aceptación.
8. `tree_digest` e inventario normativo.
9. Campaña, repeticiones y reintentos.
10. Matriz de trazabilidad.
11. Revisión de consistencia.
12. Decisiones pendientes y riesgos residuales.
13. Operaciones realizadas y no realizadas.
14. Estado final de Gate B.

No sobrescribir STEP-24, STEP-25 ni STEP-26. No modificar código, configuración, tests ni documentación canónica existente.

Si no existe una ubicación documental apropiada y segura, detenerse y reportar la limitación en lugar de crear archivos fuera del alcance autorizado.

---

# 13. CRITERIOS DE ACEPTACIÓN DE STEP-27

STEP-27 solo puede declararse `GATE B = SPECIFIED` si se satisfacen documentalmente todos los puntos siguientes:

1. Existe un contrato de política con autoridad, versionado, integridad y anti-rollback definidos.
2. La Rama A y sus criterios de verificación están formalizados.
3. El contrato de identidad impide ambigüedades entre campañas, repeticiones e intentos.
4. El esquema de evidencia distingue procedencia y autoridad de cada campo.
5. La separación worker–observer–verifier está expresada como una obligación verificable.
6. La semántica de estados y su agregación están definidas sin conversiones implícitas.
7. Cada control obligatorio del preflight tiene un criterio de aceptación y una respuesta ante fallo.
8. El procedimiento de `tree_digest` es determinista y está especificado sin ambigüedades materiales.
9. El inventario normativo se aprueba como pareja `(nodeids, tree_digest)`.
10. Las repeticiones, los reintentos y los intentos fallidos conservan identidad y procedencia.
11. La matriz de trazabilidad cubre D1–D6 y todos los requisitos nuevos.
12. Las contradicciones y decisiones que requieren aprobación del operador están identificadas.
13. No se presenta ningún control como verificado dinámicamente.
14. No se han ejecutado operaciones prohibidas.
15. Los bloqueos canónicos permanecen intactos.

Si falta un punto, declarar `GATE B = INCOMPLETE` e indicar el identificador del requisito pendiente. No rebajar un criterio para forzar el cierre.

## 14. SEPARACIÓN ENTRE ESPECIFICACIÓN E IMPLEMENTACIÓN

El cierre de Gate B significará exclusivamente que el contrato documental se considera suficientemente preciso para ser revisado.

No significa que:

- El bootstrap exista o sea confiable.
- La política esté protegida.
- El anti-rollback funcione.
- El usuario dedicado esté correctamente configurado.
- Bubblewrap proporcione el aislamiento esperado.
- Los límites de recursos sean efectivos.
- seccomp esté aplicado.
- El observer sea independiente.
- El verifier sea confiable.
- La cobertura de tests esté demostrada.
- La campaña B1-R sea ejecutable o esté autorizada.

Cada afirmación sobre efectividad requerirá evidencia apropiada en una fase posterior.

---

# 15. INFORME FINAL OBLIGATORIO

Al finalizar, informar:

- Ruta exacta del expediente STEP-27.
- Rama y HEAD observados al inicio y al final, si se inspeccionaron.
- Documentos y archivos consultados.
- Entregables B.1–B.8 completados.
- Criterios de aceptación satisfechos y pendientes.
- Contradicciones o decisiones que requieren adjudicación del operador.
- Estado final de Gate B.
- Confirmación de que no se modificó código ni configuración.
- Confirmación de que no se ejecutaron tests, `--collect-only`, workers, Bubblewrap, `unshare` ni componentes del backend.
- Confirmación de que no se modificaron archivos candidatos ni se alteraron datos de producción.
- Confirmación de que no se realizaron operaciones Git mutables.
- Confirmación de que se preservaron todos los bloqueos canónicos.

La respuesta debe diferenciar claramente el trabajo documental realizado de cualquier comprobación que no se haya ejecutado.

## 16. PROHIBICIÓN DE AUTORIZACIÓN IMPLÍCITA

La finalización de STEP-27 no autoriza:

- Implementar el harness.
- Construir el bootstrap, controlador, worker, observer o verifier.
- Instalar o configurar mecanismos de aislamiento.
- Ejecutar el preflight operativo.
- Ejecutar `pytest` o `--collect-only`.
- Crear o aprobar la pareja normativa `(nodeids, tree_digest)`.
- Ejecutar campañas de repetición.
- Iniciar B1-R.
- Modificar archivos candidatos o incorporarlos a Git.
- Alterar TALOS V1 o datos de producción.

Toda implementación, validación dinámica, aprobación de inventario o ejecución posterior requerirá una directiva separada y autorización explícita del operador.

**Fin de STEP-27.**

---

## Estado documental operativo

**Estado observado en esta documentación:** `GATE B = SPECIFICATION IN PROGRESS`.

**Observaciones permitidas en esta fase:**

- Se realizó lectura estática de la directiva STEP-27 y de los antecedentes STEP-24, STEP-25 y STEP-26.
- Se conservó el estado canónico del repositorio y la prohibición de ejecutar código del proyecto.
- No se ejecutaron pruebas, workers, preflight, ni operaciones Git mutables.

**Límites de esta fase:**

- No se autorizó ni se implementó el bootstrap ni el controlador.
- No se verificó dinámicamente aislamiento, seccomp ni anti-rollback.
- No se creó ni aprobó inventario normativo de `nodeids`/`tree_digest`.
- No se inició B1-R ni ninguna campaña protegida.

**Estado canónico preservado:**

- `P1.2 = BLOCKED-REGRESSION`
- `P1.3 = BLOCKED`
- `B1-R = NOT AUTHORIZED`
- `External harness = NOT AUTHORIZED`
- `TALOS V1 = FROZEN`

**Referencia de checkout usada para esta documentación:**

- Repositorio: `/media/agustin/Laboratorio/study-engie`
- Rama: `talos-current-audit`
- HEAD observado: `cc8acfae623f9d10c8366871470319786b6a7ca4`

**Nota de procedencia:**

Este documento se genera como un expediente documental y normativo; no sustituye ninguna aprobación operacional ni ninguna ejecución futura de preflight, bootstrap o B1-R.
