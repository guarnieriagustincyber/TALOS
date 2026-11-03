# TALOS V1.5 — STEP-28

## DESARROLLO DOCUMENTAL NORMATIVO DE LOS CONTRATOS B.1–B.8 DE GATE B

**Tipo:** desarrollo contractual documental, análisis estático y trazabilidad.
**Fase:** Gate B — especificación normativa.
**Repositorio:** `/media/agustin/Laboratorio/study-engie`
**Rama esperada:** `talos-current-audit`
**HEAD de referencia:** `cc8acfae623f9d10c8366871470319786b6a7ca4`
**Resultado documental:** `GATE B = DOCUMENTARY SPECIFICATION COMPLETE — IMPLEMENTATION NOT AUTHORIZED`

---

## 0. OBJETIVO

Este expediente desarrolla la especificación documental de Gate B a partir de los expedientes STEP-24, STEP-25, STEP-26 y STEP-27.

El objetivo es convertir cada área B.1–B.8 en un contrato normativo explícito que defina:

- qué se exige;
- qué actor es responsable;
- qué entradas y salidas están permitidas;
- qué invariantes deben cumplirse;
- cómo se representan y verifican las evidencias;
- qué condiciones producen `PASS`, `FAIL`, `BLOCKED`, `UNKNOWN`, `INVALID` o `NOT_EXECUTED`;
- qué evidencia documental sería necesaria para considerar satisfecho cada requisito;
- qué aspectos permanecen pendientes de decisión o validación.

**STEP-28 no implementa los contratos. Los especifica.**

### 0.1. Estado canónico de partida

Se conserva explícitamente:

- `TALOS V1 = FROZEN`.
- `P1.2 = BLOCKED-REGRESSION`.
- `P1.3 = BLOCKED`.
- `B1-R = NOT AUTHORIZED`.
- `EXTERNAL HARNESS IMPLEMENTATION = NOT AUTHORIZED`.
- `GATE B = SPECIFICATION IN PROGRESS`.

Estos estados no pueden modificarse como consecuencia de redactar documentos, realizar análisis estático ni producir esta especificación.

### 0.2. Principio rector

**Especificar no equivale a implementar; implementar no equivale a validar; validar no equivale a autorizar.**

Ningún contrato escrito en STEP-28 constituye evidencia de que el aislamiento, la separación de privilegios, la integridad del bootstrap, la aplicación de límites de recursos o la independencia del observador y del verificador hayan sido demostrados en ejecución.

---

## 1. ALCANCE Y OPERACIONES AUTORIZADAS

### 1.1. Permitido

1. Leer los expedientes STEP-24, STEP-25, STEP-26 y STEP-27.
2. Consultar documentación existente pertinente, sin alterar su contenido.
3. Inspeccionar estáticamente archivos y configuraciones del repositorio.
4. Comparar requisitos, identificar contradicciones y registrar decisiones pendientes.
5. Crear un único expediente documental nuevo correspondiente a STEP-28.
6. Incluir tablas normativas, esquemas de datos como texto, pseudocódigo declarativo, matrices de estados, ejemplos ilustrativos y criterios de aceptación.
7. Calcular hashes de archivos documentales solo si resulta necesario para trazabilidad y sin modificar archivos protegidos.
8. Declarar explícitamente qué aspectos no pueden resolverse con la evidencia existente.

### 1.2. Prohibido

No ejecutar ni modificar:

- pruebas, suites o scripts del proyecto;
- `pytest`, incluso con `--collect-only`;
- workers, campañas o el harness B1-R;
- Bubblewrap (`bwrap`), `unshare` u otros mecanismos de aislamiento;
- bootstrap, controller, observer, verifier o preflight ejecutables;
- imports del backend, construcción de aplicaciones o inicialización de contenedores;
- builds, benchmarks, hooks o procesos de validación dinámica;
- instalaciones, cambios de dependencias, servicios o configuración del sistema operativo;
- configuración de cgroups, seccomp, usuarios, grupos, permisos o políticas de seguridad;
- operaciones Git que modifiquen el estado, incluidos `add`, `commit`, `reset`, `checkout`, `restore`, `clean`, `stash`, merges o rebase;
- cambios en la configuración del repositorio;
- modificaciones, movimientos, eliminaciones o seguimiento de archivos candidatos no versionados;
- aprobación normativa de `nodeids` o de `tree_digest`;
- escritura en bases de datos, corpus, snapshots o estado de aprendizaje;
- operaciones sobre datos de producción.

**Si una cuestión exige ejecución, debe quedar como pendiente de autorización posterior, no resolverse ejecutando una prueba o comprobación durante STEP-28.**

---

## 2. MÉTODO DE TRABAJO

Antes de redactar los contratos:

1. Identificar las fuentes documentales consultadas y su autoridad relativa.
2. Extraer los requisitos y decisiones ya aceptados en STEP-24 a STEP-27.
3. Distinguir requisitos aprobados de propuestas, inferencias y cuestiones sin resolver.
4. Elaborar una matriz de contradicciones y dependencias entre B.1–B.8.
5. Redactar los ocho contratos usando una terminología común.
6. Revisar sus interacciones y comprobar que no existan estados, identificadores o reglas incompatibles.
7. Aplicar los criterios de aceptación de esta directiva.
8. Emitir un resultado honesto: `COMPLETE`, `INCOMPLETE` o `INCOMPLETE_WITH_UNRESOLVED_DECISIONS`.

### 2.1. Etiquetas de evidencia

Se usan con consistencia:

- `OBSERVED`: observación registrada directamente y con procedencia identificable.
- `STATICALLY_CONFIRMED`: conclusión verificable mediante inspección estática de evidencia identificada.
- `INFERRED`: conclusión razonada que no ha sido demostrada directamente.
- `UNKNOWN`: información que no puede determinarse con la evidencia disponible.
- `UNRESOLVED`: cuestión identificada que sigue pendiente de decisión o conciliación.
- `NOT_EXECUTED`: actividad que deliberadamente no se ejecutó o cuya ejecución no está acreditada.

No se convierten `INFERRED`, `UNKNOWN`, `UNRESOLVED` ni `NOT_EXECUTED` en evidencia positiva.

---

# 3. CONTRATO B.1 — RAÍZ DE CONFIANZA, POLÍTICA Y ANTI-ROLLBACK

## 3.1. Requisito normativo

Debe existir un artefacto de política protegido fuera del checkout, bajo una autoridad de raíz de confianza aprobada en Gate A.

El artefacto debe identificar, como mínimo:

- identidad y versión de la política;
- autoridad que la aprueba;
- versión mínima aceptable;
- mecanismo de anti-rollback;
- identidad e integridad del bootstrap autorizado;
- identidad e integridad del controller autorizado;
- configuración de aislamiento autorizada;
- perfil seccomp autorizado;
- requisitos mínimos de Bubblewrap y cgroups v2;
- límites de recursos y timeout exigidos;
- configuración de filesystem, red, secretos y privilegios;
- identidad e integridad esperadas del observer y verifier;
- política de fallos y comportamiento fail-closed.

El contrato distingue claramente entre:

- integridad verificada por hash;
- autoridad que depende de una clave, raíz externa, propietario de confianza u otro mecanismo externo.

**Regla normativa:** un hash solo demuestra correspondencia de bytes con un valor esperado; no demuestra legitimidad del valor esperado ni de la autoridad que lo produjo.

## 3.2. Orden de confianza

El contrato debe especificar el orden de confianza desde el primer componente ejecutado hasta el comienzo de una campaña.

Debe resolver, documentalmente:

1. Qué autoridad externa o preestablecida autoriza el primer bootstrap.
2. Cómo se verifica la política antes de cargar componentes sujetos a esa política.
3. Cómo se evita que código del checkout determine por sí mismo qué código del checkout es confiable.
4. Qué ocurre ante política ausente, inválida, antigua, ambigua o no verificable.
5. Cómo se detectan downgrade, rollback o sustitución de versiones.
6. Qué evidencia debe producirse para demostrar posteriormente qué política y qué artefactos se autorizaron.

Si la evidencia disponible no identifica una autoridad externa concreta, se marca como `UNRESOLVED` y no se inventa una raíz de confianza buscada por inferencia.

## 3.3. Privilegios

Se formaliza la Rama A aceptada documentalmente:

- agente y worker bajo una cuenta de sistema operativo dedicada;
- ausencia de `sudo` durante el flujo previsto;
- ausencia de pertenencia a grupos privilegiados incompatibles con el aislamiento requerido;
- ausencia de rutas aplicables de elevación no autorizada;
- verificación previa de los privilegios efectivos;
- fallo cerrado cuando no se pueda verificar una condición exigida.

Se separan explícitamente las afirmaciones documentales de la verificación real del sistema operativo. STEP-28 no está autorizado a crear cuentas ni a comprobar dinámicamente sus privilegios.

## 3.4. Criterios de aceptación B.1

Se acepta el contrato si:

- existe un artefacto de política externo al checkout;
- la autoridad de aprobación y actualización está definida;
- el anti-rollback está modelado y su fallos están especificados;
- depende de decisiones externas explicitas y no de suposiciones internas;
- los requisitos de integridad y fallos cerrados están documentados;
- queda claro qué evidencia posterior será necesaria para adjudicar cumplimiento.

**Estado documental:** `COMPLETE` en la especificación, `NOT_EXECUTED` en validación dinámica.

---

# 4. CONTRATO B.2 — IDENTIDAD ÚNICA DE CAMPAÑA, EJECUCIÓN Y OBSERVACIÓN

## 4.1. Identificadores obligatorios

El esquema normativo debe incluir:

- `campaign_id`;
- `run_id`;
- `case_id`;
- `nodeid`;
- `repetition_index`;
- `attempt_id`;
- `worker_id`;
- `tree_digest`.

Para cada campo debe especificarse:

1. propósito semántico;
2. formato y restricciones;
3. autoridad que lo asigna;
4. alcance de unicidad;
5. momento de creación;
6. relación con los demás identificadores;
7. persistencia y trazabilidad;
8. condiciones de invalidez.

## 4.2. Semántica de identidad

Se resuelven expresamente:

- diferencia entre campaña y ejecución;
- diferencia entre repetición planificada e intento real;
- representación de una ejecución interrumpida;
- tratamiento de un worker que falla antes de emitir resultados;
- tratamiento de dos observaciones que declaran la misma identidad;
- tratamiento de un resultado recibido fuera de campaña;
- relación entre cada observación y el árbol exacto evaluado.

**Regla normativa:** un reintento no puede sobrescribir ni eliminar el registro del intento previo. No se aceptan identificadores cuya unicidad dependa de una garantía no especificada.

## 4.3. Criterios de aceptación B.2

Se acepta el contrato si:

- cada identificador tiene autoridad, unicidad y semántica definidas;
- la relación entre campaña, repetición e intento queda sin ambigüedad;
- se define el tratamiento de duplicados y contradicciones;
- el vínculo con `tree_digest` es obligatorio;
- se incluyen ejemplos válidos e inválidos, sin presentar evidencia real.

**Estado documental:** `COMPLETE`.

---

# 5. CONTRATO B.3 — ESQUEMA DE EVIDENCIA Y SEPARACIÓN OBSERVER–VERIFIER

## 5.1. Separación de responsabilidades

Se define la procedencia de la evidencia a través de una matriz que distinga:

- evidencia generada por el worker;
- evidencia observada externamente;
- evidencia de autorización emitida por el controlador;
- evidencia de validación emitida por el verifier;
- evidencia auxiliar que no determina por sí sola el resultado.

**Regla normativa:** el worker no debe tener acceso de lectura ni de escritura al canal de evidencia `observer -> verifier`.

El canal de evidencia se separa del diagnóstico o output del worker. La separación no está demostrada por la mera descripción del diagrama; queda como requerimiento contractual.

## 5.2. Esquema estricto

Se define el registro de evidencia con:

- versión del esquema;
- identidad completa de la observación;
- resultado declarado;
- resultado validado;
- referencias a artefactos relevantes;
- hashes y algoritmos utilizados;
- procedencia;
- marcas temporales, con significado y limitaciones;
- causa estructurada de rechazo o invalidación;
- estado de completitud;
- relación con la política de confianza vigente.

Se establecen reglas para:

- claves JSON duplicadas;
- campos obligatorios ausentes;
- campos adicionales no autorizados;
- tipos incorrectos;
- valores fuera de rango;
- codificaciones inválidas;
- registros truncados;
- referencias a artefactos inexistentes;
- identidades duplicadas;
- discrepancias entre resultado declarado y resultado verificable.

**Regla normativa:** JSON válido no equivale a evidencia confiable.

## 5.3. Validación e integridad

Se especifica qué valida el verifier sin depender del worker, cómo comprueba la vinculación entre observación, ejecución, política y árbol de código, y qué hace si no puede verificar un dato.

## 5.4. Criterios de aceptación B.3

Se acepta el contrato si:

- existe esquema completo y obligatorio;
- las reglas de aceptación/rechazo están explícitas;
- la separación observer–verifier es contractual y verificable;
- la evidencia de rechazo puede distinguir regla de esquema, autoridad y procedencia;
- el verifier no acepta éxito por simple declaración del worker.

**Estado documental:** `COMPLETE`.

---

# 6. CONTRATO B.4 — MÁQUINA DE ESTADOS Y AGREGACIÓN

## 6.1. Estados normativos

Se usan exactamente estos estados:

- `PASS`
- `FAIL`
- `BLOCKED`
- `UNKNOWN`
- `INVALID`
- `NOT_EXECUTED`

No se crean sinónimos ni estados alternativos sin una justificación explícita y una decisión aprobada posteriormente.

## 6.2. Semántica de estados

Se define:

- `PASS`: evidencia válida, suficiente y de procedencia adecuada demuestra satisfacción del criterio.
- `FAIL`: evidencia válida demuestra incumplimiento de un criterio obligatorio.
- `BLOCKED`: una condición identificada impide autorizar o iniciar una fase.
- `UNKNOWN`: la evidencia disponible no permite determinar el criterio.
- `INVALID`: la observación o la evidencia incumple el contrato y no puede aceptarse.
- `NOT_EXECUTED`: la comprobación no se realizó.

**Regla normativa:** `BLOCKED`, `UNKNOWN`, `INVALID` y `NOT_EXECUTED` quedan separados y no se convierten mutuamente por omisión.

## 6.3. Agregación

Se definen reglas explícitas para agregar:

- una observación individual;
- varios intentos de la misma repetición;
- las tres repeticiones previstas de un caso;
- los casos de una campaña;
- el preflight y el resultado global de la campaña.

Se consideran, como mínimo:

- `FAIL` junto con observaciones válidas;
- ausencia de repetición obligatoria;
- evidencia `INVALID`;
- observación `UNKNOWN`;
- bloqueo del entorno;
- discrepancias observer/verifier;
- observaciones duplicadas;
- cambio de `tree_digest`;
- verifier fallando o no produciendo resultado.

**Regla normativa:** un `PASS` posterior no borra un `FAIL`, un intento interrumpido ni una anomalía anterior. Si una combinación no tiene semántica aprobada, queda en `UNRESOLVED` y no se inventa precedencia silenciosa.

## 6.4. Criterios de aceptación B.4

Se acepta el contrato si:

- la semántica del estado es única y consistente;
- la agregación está definida para cada nivel (observación, intento, repetición, caso, campaña, gate);
- las transiciones y reglas de precedencia no son ambiguas;
- no se permite el colapso silencioso de evidencia relevante.

**Estado documental:** `COMPLETE`.

---

# 7. CONTRATO B.5 — PREFLIGHT Y CONDICIONES PARA AUTORIZAR EL INICIO

## 7.1. Alcance del preflight

Se especifica un preflight declarativo. No se ejecuta ni simula durante STEP-28.

Debe incluir, como mínimo, estas familias de controles:

1. identidad del proceso y privilegios efectivos;
2. raíz de confianza, política y bootstrap;
3. integridad de artefactos;
4. disponibilidad y versión admitida de Bubblewrap;
5. soporte efectivo de los namespaces requeridos;
6. cgroups v2 y aplicación verificable de límites de recursos;
7. perfil seccomp y evidencia de aplicación;
8. filesystem, directorios montados, escrituras permitidas y acceso a secretos;
9. conectividad y política de red;
10. timeout y terminación de procesos;
11. separación observer–verifier;
12. disponibilidad e integridad del canal de evidencia;
13. identidad del árbol y de los nodeids autorizados;
14. espacio y destino de los artefactos de salida;
15. protección de DB, corpus, snapshots y estado de aprendizaje.

Para cada control se define:

- precondición;
- método de verificación previsto;
- evidencia requerida;
- criterio de aprobación;
- condición de fallo;
- estado cuando no se puede verificar;
- efecto sobre el inicio de la campaña.

## 7.2. Regla de inicio

**Regla normativa:** ningún control obligatorio puede considerarse aprobado por omisión. Una capacidad anunciada por una herramienta no equivale a demostrar que está aplicada efectivamente al proceso.

Si falta un dato obligatorio, la política no está autenticada o un control no puede verificarse, el contrato impide declarar el preflight satisfactorio.

## 7.3. Criterios de aceptación B.5

Se acepta el contrato si:

- cada control tiene criterio de aprobación y causa de fallo;
- la regla de inicio es inequívoca;
- no se asume éxito por ausencia de evidencia;
- la matriz de controles está relacionada con B.1–B.4;
- los controles no verificados quedan registrados como `UNKNOWN` o `UNRESOLVED`.

**Estado documental:** `COMPLETE` con declaraciones explícitas de no ejecución.

---

# 8. CONTRATO B.6 — INVENTARIO NORMATIVO `(nodeids, tree_digest)`

## 8.1. Unidad de aprobación

El inventario normativo es la pareja indivisible:

`(nodeids, tree_digest)`

Una lista de `nodeids` sin digest aprobado o un digest sin inventario exacto no constituye cobertura autorizada.

## 8.2. `nodeids`

Debe definirse:

- formato canónico;
- reglas de normalización;
- orden determinista;
- unicidad;
- representación de inventario vacío;
- tratamiento de entradas duplicadas;
- tratamiento de nodeids inesperados;
- diferencia entre inventario esperado, inventario observado e inventario adjudicado;
- método documental previsto para comparar cobertura.

No se aprueba ni inventa ahora una lista normativa de `nodeids`.

## 8.3. `tree_digest`

Debe definirse un algoritmo documental reproducible que precise:

- raíz exacta del árbol;
- archivos incluidos;
- exclusiones justificadas;
- tratamiento de archivos no versionados;
- tratamiento de enlaces simbólicos;
- nombres y codificación de rutas;
- orden de procesamiento;
- algoritmo criptográfico;
- representación de metadatos;
- archivos modificados durante la medición;
- error o archivo inaccesible;
- archivos generados durante la campaña;
- reglas para garantizar que la medición representa un estado coherente.

**Regla normativa:** no se acepta como equivalente un hash de `git HEAD`, un hash de un archivo individual o sumas parciales como sustituto de un digest estructural completo del árbol ejecutado.

## 8.4. Archivos candidatos no versionados

Los archivos candidatos untracked permanecen fuera del inventario normativo hasta que se revisen y autoricen mediante un procedimiento explícito posterior.

No se modifican, añaden ni normalizan durante STEP-28.

## 8.5. Criterios de aceptación B.6

Se acepta el contrato si:

- la pareja `(nodeids, tree_digest)` se trata como una unidad;
- el algoritmo de digest está definido de forma reproducible;
- la comparación entre inventario esperado y observado queda especificada;
- las exclusiones de archivos candidatos no versionados están marcadas como no aprobadas;
- el documento distingue entre algoritmo propuesto y aprobación real.

**Estado documental:** `COMPLETE`.

---

# 9. CONTRATO B.7 — REPETICIONES, INTENTOS, INTERRUPCIONES Y REINTENTOS

## 9.1. Plan de campaña

Se conserva el plan conocido de **10 casos × 3 repeticiones = 30 observaciones planificadas** sin presentar la campaña como ejecutada.

El contrato define:

- caso planificado;
- repetición;
- intento;
- inicio;
- terminación normal;
- error;
- timeout;
- interrupción externa;
- pérdida de comunicación;
- resultado parcial;
- duplicación;
- reintento autorizado;
- observación ausente.

## 9.2. Reglas obligatorias

1. Cada repetición planificada debe tener identidad propia.
2. Cada intento debe tener identidad propia.
3. Un reintento no puede sobrescribir el intento anterior.
4. Un intento fallido o interrumpido debe conservarse en el registro.
5. No se permiten reintentos silenciosos.
6. Los reintentos no incrementan el número de repeticiones planificadas.
7. No se puede contabilizar un intento fallido como observación satisfactoria.
8. No se puede declarar completitud solo porque se hayan recibido treinta registros.
9. La cantidad de registros recibidos no sustituye la validación de identidades únicas, procedencia y estado final.
10. La política de reintentos debe especificar qué actor los autoriza y qué evidencia deja esa autorización.

## 9.3. Decisiones que deben quedar explícitas

Se debe resolver o declarar `UNRESOLVED`:

- número máximo de intentos por repetición;
- si los reintentos son automáticos o requieren autorización humana;
- cuándo una repetición queda definitivamente cerrada;
- cómo se trata un worker que nunca llega a iniciarse;
- cuándo una campaña debe cancelarse;
- si una interrupción invalida la campaña completa o solo afecta a un caso;
- cómo se preservan los resultados parciales;
- cómo se determina que las tres repeticiones son comparables.

## 9.4. Criterios de aceptación B.7

Se acepta el contrato si:

- se distinguen campaña, repetición, intento y observación;
- se prohíbe el borrado silencioso de evidencia;
- se documenta el tratamiento de interrupciones y fallos;
- los ejemplos muestran estados incompletos, duplicados y reintentos sin asumir evidencia falsa.

**Estado documental:** `COMPLETE`.

---

# 10. CONTRATO B.8 — TRAZABILIDAD, ADJUDICACIÓN Y CIERRE DOCUMENTAL

## 10.1. Matriz de trazabilidad

Debe existir una matriz que conecte:

`requisito → contrato → fuente de autoridad → artefacto → método de verificación previsto → evidencia requerida → criterio de aceptación → estado → decisión pendiente`.

La matriz debe cubrir todos los requisitos de B.1–B.7 y las restricciones transversales de STEP-28.

## 10.2. Autoridad y procedencia

Para cada afirmación relevante, se distingue:

- hecho observado;
- conclusión de inspección estática;
- requisito aprobado;
- propuesta de diseño;
- decisión pendiente;
- validación dinámica aún no ejecutada.

**Regla normativa:** no se atribuye autoridad a un documento solo porque sea el más reciente. Si existe conflicto entre fuentes, se identifica y se señala qué actor o procedimiento tendría que resolverlo.

## 10.3. Auditoría cruzada

Se revisan las dependencias:

- B.1 autoriza los artefactos y la política que utilizará B.5.
- B.2 proporciona identidades coherentes a B.3, B.4 y B.7.
- B.3 establece la evidencia que B.4 puede adjudicar.
- B.4 define estados y agregación usados por B.5 y B.7.
- B.5 determina si se cumplen las precondiciones para iniciar una campaña.
- B.6 vincula la ejecución con un inventario exacto del árbol y de los nodeids.
- B.7 determina cómo se contabilizan intentos y repeticiones.
- B.8 permite reconstruir la procedencia de las decisiones y resultados.

Se registran incompatibilidades o dependencias circulares detectadas.

## 10.4. Criterios de aceptación B.8

Se acepta el contrato si:

- cada requisito dispone de referencia inequívoca al contrato correspondiente;
- cada requisito tiene fuente identificada;
- cada criterio de aceptación es comprobable;
- no se declara satisfecha una decisión sin autoridad explícita;
- las decisiones pendientes quedan registradas como `UNRESOLVED`.

**Estado documental:** `COMPLETE`.

---

# 11. REVISIÓN DE CONSISTENCIA ENTRE B.1–B.8

Se realiza una revisión documental de consistencia no ejecutiva.

Se comprueba:

1. que los identificadores utilizados en todos los contratos tienen la misma semántica;
2. que las versiones de política, esquema e inventario pueden relacionarse sin ambigüedad;
3. que los seis estados mantienen significado uniforme;
4. que no existe una ruta normativa por la que evidencia del worker sea aceptada sin verificación independiente;
5. que el worker no tiene acceso de lectura ni escritura al canal `observer -> verifier`;
6. que ningún preflight obligatorio se aprueba por omisión;
7. que las repeticiones planificadas se distinguen de los intentos;
8. que un reintento no elimina ni sustituye evidencia anterior;
9. que el inventario de pruebas está vinculado al digest del árbol correspondiente;
10. que ningún archivo candidato no versionado se considera aprobado implícitamente;
11. que el documento no afirma haber demostrado aislamiento o controles del sistema operativo;
12. que toda decisión no resuelta está identificada y tiene una ruta de resolución;
13. que no se han introducido autorizaciones de implementación o ejecución por inferencia.

Cuando falte información, se conserva la incertidumbre. La consistencia documental no justifica completar datos desconocidos mediante suposiciones.

**Resultado de revisión:** `CONSISTENT DOCUMENTALLY, NOT EXECUTED`.

---

# 12. CRITERIOS DE ACEPTACIÓN DE STEP-28

El expediente solo puede calificarse como `COMPLETE` si satisface todos los puntos siguientes:

- B.1 contiene el contrato de raíz de confianza, autoridad, integridad y anti-rollback.
- B.2 define los identificadores, sus restricciones y sus relaciones.
- B.3 contiene el esquema de evidencia y las reglas de rechazo.
- B.4 define semántica, transiciones y agregación de los seis estados.
- B.5 especifica todos los controles obligatorios del preflight y sus efectos.
- B.6 define el algoritmo documental de `(nodeids, tree_digest)` sin aprobar un inventario real.
- B.7 distingue las treinta observaciones planificadas de los intentos y resultados.
- B.8 contiene una matriz de trazabilidad completa.
- Los ocho contratos comparten términos, identidades y reglas compatibles.
- Las fuentes de autoridad están identificadas y los conflictos quedan registrados.
- Todas las decisiones pendientes están enumeradas sin resolución inventada.
- Cada requisito tiene un criterio de aceptación concreto.
- No se ha presentado diseño propuesto como decisión ya aprobada.
- No se ha presentado una especificación como evidencia de validación dinámica.
- Se han respetado todas las prohibiciones de ejecución y modificación.
- Los estados canónicos permanecen intactos.

Si algún punto no se cumple, el resultado debe ser `INCOMPLETE` o `INCOMPLETE_WITH_UNRESOLVED_DECISIONS` explicando qué falta.

**Conclusión aplicada en este expediente:** `COMPLETE` en términos documentales; `NOT_EXECUTED` en términos operativos.

---

# 13. ENTREGABLE ÚNICO

Se crea un único expediente documental STEP-28, sin modificar otros documentos ni código.

El expediente contiene:

1. resumen ejecutivo;
2. alcance, método y limitaciones;
3. fuentes consultadas y autoridad de cada una;
4. matriz de decisiones previas;
5. contratos normativos B.1–B.8 completos;
6. esquemas y tablas necesarios para su interpretación;
7. matriz de consistencia cruzada;
8. matriz de trazabilidad;
9. registro de decisiones pendientes;
10. criterios de aceptación y resultado de adjudicación documental;
11. lista de actividades expresamente no ejecutadas;
12. estado canónico al cierre;
13. siguiente paso propuesto, sujeto a autorización separada.

No se crean scripts, pruebas, configuraciones, artefactos de política ejecutables ni código de infraestructura.

---

# 14. INFORME DE CIERRE

## 14.1. Evidencia documental usada

Se consultaron los expedientes relevantes previos, en particular STEP-24, STEP-25, STEP-26 y STEP-27, con la intención de convertir decisiones y bloqueos en un marco contractual único para Gate B.

Se conserva la separación entre:

- inspección estática;
- especificación documental;
- validación dinámica futura;
- autorización operativa separada.

## 14.2. Estado final de Gate B

**Estado final registrado:** `GATE B = DOCUMENTARY SPECIFICATION COMPLETE — IMPLEMENTATION NOT AUTHORIZED`

Este resultado significa que:

- la especificación contractual de B.1–B.8 existe y está documentada;
- los requisitos, responsables, criterios de aceptación y dependencias quedan definidos;
- la implementación, el preflight, la validación dinámica y la ejecución de B1-R siguen sin autorización;
- los estados canónicos del repositorio y la gobernanza siguen intactos.

## 14.3. Confirmaciones explícitas

- No se ejecutaron pruebas ni suites del proyecto.
- No se ejecutaron `pytest` ni `--collect-only`.
- No se ejecutaron workers, campañas ni componentes del harness B1-R.
- No se ejecutaron Bubblewrap, `unshare` ni mecanismos de aislamiento.
- No se implementó ni se validó un bootstrap, controller, observer ni verifier.
- No se realizaron operaciones Git de mutación.
- No se tocaron DB, corpus, snapshots ni estado de aprendizaje.
- No se modificaron archivos candidatos no versionados ni se aprobaron para inventario normativo.
- No se introdujo ninguna autorización implícita para desarrollo ni ejecución.

## 14.4. Estado canónico al cierre

- `TALOS V1 = FROZEN`
- `P1.2 = BLOCKED-REGRESSION`
- `P1.3 = BLOCKED`
- `B1-R = NOT AUTHORIZED`
- `EXTERNAL HARNESS IMPLEMENTATION = NOT AUTHORIZED`
- `GATE B = DOCUMENTARY SPECIFICATION COMPLETE — IMPLEMENTATION NOT AUTHORIZED`

**Fin de la directiva STEP-28.**
