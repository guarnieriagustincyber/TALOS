# Plan de mejora pedagógica de TALOS

## Propósito y continuidad

Este documento conserva el diagnóstico, las decisiones y el plan de trabajo
para mejorar TALOS como tutor de estudio de ciberseguridad. Sirve como handoff
si la conversación se reinicia: antes de trabajar, leer este documento y
continuar desde la fase pendiente. **No repetir el setup del benchmark ni
reconstruir la comparación ya realizada.**

Fecha de elaboración: 2026-09-28.

### Convención de fases

Las Fases 0–7 de este documento son las **fases del programa de mejora
pedagógica**. No deben confundirse con la nomenclatura de entrega que existe
en [PHASES.md](../PHASES.md): en particular, aquí **Fase 4 — Formato y código**
debe llamarse `F4-formato` en issues, reportes y handoffs; no es `Fase 4-eval`
(Golden Set/evaluación) ni `Fase 4-sec` (red team/seguridad). Verificar y
mantener esta distinción si el roadmap global cambia.

## Contexto y evidencia disponible

- El usuario realizó una comparación de 20 preguntas entre TALOS y NotebookLM.
- Las transcripciones compartidas para su análisis fueron
  `/home/agustin/Escritorio/20TALOS.txt` y
  `/home/agustin/Escritorio/20NotebookLM.txt`. Son archivos locales fuera del
  repositorio; no copiarlos ni agregarlos al control de versiones sin
  autorización.
- El usuario confirmó que las preguntas originales fueron exactamente las
  mismas en ambos sistemas.
- El usuario volvió a proporcionar la lista canónica de las 20 preguntas; está
  preservada íntegramente en la sección **Preguntas canónicas del benchmark**.
- El registro comparativo mostró respuestas más estructuradas y ajustadas al
  estudiante por parte de NotebookLM en los casos disponibles. TALOS presentó
  más detalle técnico en algunas respuestas, pero también se observaron
  problemas reportados de ajuste a pedidos de síntesis, respuestas
  incompletas, demoras y un error 500. Los registros por turno no siempre
  conservan respuestas completas y alineadas, así que no deben usarse para
  asignar puntajes retrospectivos sin cotejo.
- El usuario compartió el prompt original de NotebookLM. Sus principios
  pedagógicos relevantes son: no asumir prerrequisitos; explicar conceptos
  nuevos; guiar en vez de dar soluciones automáticamente; usar formatos
  específicos por tarea; corregir con feedback accionable; cambiar de enfoque
  ante “no entendí”; respetar fuentes; y conectar con ciberseguridad solo
  cuando resulte pertinente.
- Ese prompt estaba orientado a programación desde cero. No copiar literalmente
  sus plantillas de pseudocódigo/Python a todas las materias de TALOS.
- En la inspección previa se identificaron componentes existentes de intención,
  ensamblado de prompts y respuesta pedagógica en
  `src/study_engine/pedagogy/structured_pipeline.py`, además del manejo SSE en
  `src/study_engine/web/routes/chat.py`. Reutilizar estos componentes y
  verificar el estado real del código antes de implementar.

### Interpretación

La comparación es evidencia de una ejecución concreta, no una demostración de
superioridad general de uno de los sistemas. Más detalle técnico no equivale
por sí mismo a mejor enseñanza. La hipótesis de mejora es que TALOS puede
conservar rigor y profundidad, a la vez que mejora claridad, ajuste al pedido,
progresión pedagógica y fiabilidad.

## Preguntas canónicas del benchmark

Esta es la lista textual que el usuario confirma como las 20 preguntas usadas
en la comparación TALOS vs NotebookLM. Usarla para alinear y clasificar el
corpus existente; no volver a ejecutar la comparación ni repetir su setup salvo
que el usuario lo solicite.

1. Hola, quiero empezar a estudiar la Unidad 1 de Sistemas Operativos. ¿Cuáles son los temas principales?
2. Empecemos con la introducción. ¿Qué es un proceso?
3. No entendí muy bien la analogía. ¿Podés explicarlo de otra manera?
4. ¿Y eso por qué es importante?
5. ¿Qué diferencia hay entre un proceso y un programa?
6. ¿Me podés mostrar un ejemplo en C de cómo se crea un proceso?
7. Sí, hagamos el ejercicio.
8. Creo que un proceso es lo mismo que un archivo ejecutable en disco.
9. Ah, entonces un proceso es una instancia de un programa en ejecución, con su propia memoria y estado.
10. ¿Y cómo hace el sistema operativo para manejar varios procesos a la vez?
11. ¿Necesito saber algo de hardware para entender esto?
12. Contame más sobre eso de la memoria.
13. En una frase, ¿qué es lo más importante que debo recordar de un proceso?
14. Si hay 10 procesos corriendo, ¿cómo decide el SO qué hace cada uno?
15. Volviendo a lo anterior: ¿un proceso puede vivir sin programa?
16. ¿Cuál es la diferencia entre proceso y thread?
17. Entonces, el thread es un proceso más pequeño, ¿no?
18. ¿Por qué un navegador tiene varios procesos y no solo uno?
19. Resumí todo lo que aprendimos sobre procesos en 5 líneas.
20. ¿Qué tema te parece que conviene estudiar ahora a partir de esto?

## Objetivo del programa

TALOS debe explicar con rigor los temas de ciberseguridad y sus fundamentos,
adaptando profundidad, representación y formato a la necesidad del estudiante.
Debe poder responder de forma concisa cuando se pide brevedad y desplegar
detalle técnico cuando se solicita profundidad, sin sacrificar exactitud,
contexto, seguridad ni valor pedagógico.

## Principios de diseño acordados

1. **Profundidad disponible, no profundidad obligatoria.** Desplegar las capas
   que pide el estudiante o que hacen falta para contestar bien.
2. **Respuesta directa primero.** Explicar enseguida qué responde la pregunta;
   después desarrollar el razonamiento pertinente.
3. **No asumir conocimientos sin evidencia.** Definir términos necesarios,
   explicar prerrequisitos faltantes y no inferir dominio solo por exposición.
4. **Progresión pedagógica.** Usar explicación, ejemplo trabajado, práctica
   guiada y feedback según tarea y nivel; no convertir cada turno en examen.
5. **Representación apropiada al tema.** Elegir entre prosa, pseudocódigo,
   código, traza, tabla, diagrama, comandos o laboratorio; no forzar Python ni
   comandos Linux en todas las respuestas.
6. **Rigor contextualizado.** Distinguir principios generales de detalles
   específicos de sistema operativo, arquitectura, ABI, lenguaje, versión o
   configuración.
7. **Ciberseguridad orgánica.** Conectar un concepto con amenazas, mitigaciones,
   detección o análisis cuando esa conexión ayude a entenderlo; no añadirla por
   rutina.
8. **Fuentes honestas.** No inventar citas, páginas o contenido de materiales
   no consultados. Separar lo que respalda una fuente de la explicación general.
9. **Preferencia puntual sobre hábito general.** Formato, longitud y objetivo
   explícitos del turno prevalecen sobre la plantilla pedagógica por defecto,
   manteniendo seguridad y exactitud.
10. **Fallos explícitos.** Errores y respuestas incompletas no deben presentarse
    como respuestas completas ni ser ocultados con contenido inventado.

## Jerarquía de instrucciones propuesta

Resolver conflictos antes de formar el prompt final, usando este orden:

1. Seguridad y límites de operación.
2. Exactitud, alcance y honestidad sobre fuentes.
3. Pedido explícito del turno: tarea, formato, longitud y profundidad.
4. Modo pedagógico adecuado a esa tarea.
5. Objetivos, preferencias y contexto del estudiante disponibles.
6. Estilo general y hábitos por defecto de TALOS.

No confiar en añadir un bloque de texto al final como única solución de
prioridad. Consolidar la intención en un contrato de respuesta estructurado y
probar el camino completo desde la entrada del chat hasta la salida mostrada.

## Plan general de trabajo

### Fase 0 — Línea de base y protocolo de evaluación

Establecer corpus emparejado, rúbrica, metadatos y reglas de manejo de datos
antes de cambiar comportamiento pedagógico. El plan detallado está en la
sección **Plan detallado para la Fase 0**.

### Fase 1 — Contrato de respuesta por turno

El plan de implementación detallado y los criterios de aceptación de esta fase
están en la sección **Plan detallado para la Fase 1** más abajo.

### Fase 2 — Modos pedagógicos y profundidad progresiva

Implementar y probar modos diferenciados:

- **Concepto:** respuesta directa, definición, mecanismo, ejemplo pertinente y
  comprobación opcional.
- **Profundo:** intuición, definición formal, pasos, implementación contextual,
  límites, implicación de seguridad y aplicación cuando correspondan.
- **Síntesis:** formato y longitud solicitados, sin secciones adicionales
  obligatorias.
- **Ejercicio guiado:** objetivo, análisis, primer paso y pista; esperar intento
  salvo que se pida solución completa.
- **Corrección:** reconocer lo correcto, precisar el error, explicar por qué y
  ofrecer el siguiente paso.
- **No entendí:** cambiar de representación, simplificar y localizar el
  prerrequisito o paso confuso, en vez de repetir.
- **Laboratorio:** objetivo, entorno, pasos seguros, resultado esperado e
  interpretación.

Las plantillas deben ser adaptables a la materia. La secuencia pseudocódigo y
Python del prompt de NotebookLM aplica a ejercicios de programación, no a todo
el currículo de ciberseguridad.

### Fase 3 — Rigor técnico y conexión con ciberseguridad

- Identificar dependencias de plataforma, arquitectura, ABI, lenguaje,
  compilador, versión y configuración.
- Marcar el contexto en el texto, por ejemplo “en Linux x86-64” o “en este
  ejemplo”.
- Separar hecho, analogía, simplificación didáctica e hipótesis.
- Al explicar una vulnerabilidad: establecer propiedad, precondiciones,
  mecanismo, impacto y mitigación relevantes.
- Auditar afirmaciones de bajo nivel; no usar jerga como proxy de exactitud.
- Usar fuentes del curso sin inventar citas ni detalles bibliográficos.

### Fase 4 — Formato y código

Identificador en esta hoja de ruta: **F4-formato** (no confundir con las fases
4-eval ni 4-sec de [PHASES.md](../PHASES.md)).

- Seleccionar representación según tema e intención.
- No emitir código ejecutable salvo petición explícita o necesidad didáctica
  justificada por el modo.
- Cuando el código se pida, explicarlo al nivel adecuado, sin bloquearlo por
  una clasificación genérica de “principiante”.
- Validar la salida completa, no solo la presencia de reglas de formato en el
  prompt.

### Fase 5 — Fuentes, memoria y continuidad

- Probar referencias a turnos anteriores como “eso”, “el segundo punto” y
  “volviendo a lo anterior”.
- Verificar que contexto, historial y recuperación preserven la información
  necesaria para responder seguimientos.
- Tratar perfil y estimaciones de conocimiento como evidencia provisional.
- No inferir dominio por haber recibido una explicación o acertado una sola
  respuesta.
- Diferenciar contenido respaldado por los materiales de la explicación
  general.

### Fase 6 — Streaming y fiabilidad

- Diagnosticar errores 500, latencia, truncamientos y salidas parciales usando
  logs y metadatos, no conjeturas basadas solo en una transcripción.
- Verificar que el texto visible, validado y persistido sea coherente.
- Comprobar que contenido interno no se exponga como respuesta al estudiante.
- Marcar respuestas incompletas y distinguir errores de proveedor, backend y
  frontend.
- No aumentar límites de generación sin evidencia de que la finalización por
  longitud sea la causa.

### Fase 7 — Evaluación y aprendizaje

- Comparar TALOS anterior, TALOS mejorado y NotebookLM con prompts y materiales
  documentados.
- Repetir ejecuciones para medir variabilidad.
- Puntuar respuestas a ciegas con rúbrica previa y, cuando sea posible, dos
  evaluadores.
- Separar calidad de respuesta de aprendizaje efectivo.
- Para aprendizaje, incluir evaluación previa, inmediata y demorada con
  problemas de transferencia; contrabalancear exposición y evitar enseñar dos
  veces el mismo contenido al mismo participante en secuencia.
- Fijar umbrales antes de observar resultados y reportar incertidumbre y fallos.

### Mapa de dependencias y estado

| Fase | Resultado de salida | Dependencia principal | Estado al actualizar este plan |
|---|---|---|---|
| 0 — Línea de base | Evidencia preservada, rúbrica y protocolo | Evidencia de la comparación del usuario | Completada como línea de base; sin puntuación retrospectiva |
| 1 — Contrato por turno | Una decisión tipada de tarea y restricciones que gobierna el prompt | Fase 0; flujo actual del chat | Implementada localmente; 38 pruebas focalizadas pasaron; sin commit |
| 2 — Modos pedagógicos | Estrategias de explicación, práctica, corrección y reexplicación | Fase 1 | Diseñada en este documento; pendiente de implementación |
| 3 — Rigor y ciberseguridad | Afirmaciones técnicas contextualizadas y razonamiento seguro | Fases 1–2 | Diseñada en este documento; pendiente de implementación |
| 4 — Formato y código | Formato fiel al pedido, código controlado y salida usable | Fases 1–3 | Diseñada en este documento; pendiente de implementación |
| 5 — Fuentes y continuidad | Seguimientos coherentes y procedencia de afirmaciones visible | Fases 1–4; recuperación/contexto existentes | Diseñada en este documento; pendiente de implementación |
| 6 — Streaming y fiabilidad | Respuesta visible íntegra o fallo explícito, medible y recuperable | Camino de chat/streaming; instrumentación disponible | Diseñada en este documento; pendiente de implementación |
| 7 — Evaluación y aprendizaje | Evidencia reproducible de calidad y, por separado, aprendizaje | Fases 0–6 estabilizadas | Diseñada en este documento; pendiente de autorización/ejecución |

La secuencia expresa dependencias de producto, no obliga a implementar todo
linealmente: un fallo de fiabilidad que impida observar la salida puede
investigarse antes de Fase 5, pero el diagnóstico debe apoyarse en evidencia y
no debe ampliar el alcance de la fase activa. Cada fase se implementa en un
cambio revisable, con tests, resultados, límites y decisión de salida
registrados aquí. No empezar varias fases en el mismo cambio salvo una
dependencia bloqueante explicada y aceptada.

### Protocolo común de implementación para Fases 2–7

1. Al retomar, leer este plan y la línea de base enlazada; comprobar Git, branch,
   cambios sin commit y los archivos reales antes de confiar en cualquier ruta,
   nombre de test o descripción técnica de este handoff.
2. Tomar una fase por vez. Escribir primero pruebas para el comportamiento
   observable y casos negativos; luego implementar con los patrones existentes.
3. Usar pruebas unitarias para la decisión local y pruebas de integración con
   mocks para el camino de chat. Las pruebas de prompt verifican reglas y
   restricciones; no demuestran por sí solas que un LLM obedecerá.
4. No depender de proveedor externo para gates rutinarios. Una ejecución
   end-to-end con modelo real es una evaluación separada, con configuración,
   consentimiento y registro definidos en Fase 0/7.
5. Proteger las invariantes superiores: seguridad, exactitud, procedencia de
   fuentes, privacidad y fallos explícitos. La personalización pedagógica no las
   rebaja.
6. No tocar estado BKT, auditoría, ejecución, evaluación ni datos de progreso
   del estudiante salvo que una fase los incluya expresamente y el usuario
   apruebe ese alcance. Ninguna de las Fases 2–7 requiere por defecto alterar
   ese estado.
7. Ejecutar el conjunto focalizado y las regresiones relacionadas; revisar
   `git diff --check`, alcance, artefactos y salida final. Registrar comandos
   exactos y resultados reales; no convertir una ejecución no realizada en
   evidencia.
8. Si un test falla antes de editar o una zona protegida está modificada,
   determinar si es preexistente y detenerse para pedir guía cuando no se pueda
   separar con seguridad. No revertir trabajo ajeno.
9. No hacer commit, push, benchmark humano ni modificación destructiva de datos
   salvo solicitud explícita. Mantener las transcripciones originales fuera del
   repositorio.

## Plan detallado para la Fase 0

La Fase 0 quedó completada como línea de base y protocolo de evaluación. La
evidencia, hashes, discrepancias de enunciado, matriz de integridad, taxonomía y
protocolo están documentados en
[FASE0_LINEA_BASE_TALOS_NOTEBOOKLM.md](./FASE0_LINEA_BASE_TALOS_NOTEBOOKLM.md).
No se asignaron puntajes retrospectivos: el protocolo se definió después de la
prueba y los transcripts no documentan todas las condiciones.

### Objetivo

Crear una línea de base reproducible y protegida para medir las fases
posteriores. La Fase 0 no modifica prompts ni comportamiento de TALOS, no repite
el setup de la prueba ya realizada y no ejecuta otra comparación con el estado
del estudiante.

### Alcance

- Registrar y normalizar evidencia existente.
- Crear un corpus de evaluación sin secretos ni datos personales innecesarios.
- Definir rúbrica y protocolo de puntuación.
- Acordar qué metadatos se recogerán en futuras ejecuciones.
- No cambiar backend, estado BKT, prompts de producción ni lógica de evaluación.
- No restaurar ni alterar la base del estudiante como parte de esta fase.

### Tareas

#### F0.1 — Inventariar evidencia existente

1. Confirmar la ubicación y disponibilidad local de los dos transcripts
   existentes.
2. Identificar la fuente exacta de cada pregunta y emparejarla con las
   respuestas correspondientes de ambos sistemas.
3. Para cada una de las 20 preguntas, registrar si cada transcript contiene:
   - respuesta completa;
   - respuesta parcial/truncada;
   - error técnico;
   - demora sin respuesta sustantiva;
   - turno de seguimiento o texto de contexto;
   - evidencia insuficiente para puntuar.
4. Preservar la afirmación del usuario de que las preguntas originales fueron
   idénticas; cualquier desalineación de número de turno se registra como
   problema de transcript, no como diferencia de prompt, salvo evidencia
   contraria.
5. No inferir causas raíz técnicas de los logs narrativos por sí solos.

**Entregable:** matriz de emparejamiento de 20 filas con referencias a fuente,
estado de integridad y notas de atribución.

#### F0.2 — Proteger y normalizar los datos

1. Mantener los transcripts originales fuera del repositorio.
2. Si hace falta un corpus versionado, crear copias normalizadas que excluyan
   identificadores, datos del estudiante, tokens, credenciales, snapshots BKT y
   metadatos privados.
3. No incluir texto de libros con copyright más allá de fragmentos
   estrictamente necesarios; preferir preguntas propias y referencias.
4. Mantener un manifiesto no sensible con identificador de caso, hash de
   archivo, fecha, producto y versión cuando estén disponibles.
5. Guardar los originales y cualquier snapshot privado en almacenamiento local
   protegido, separado del repositorio.

**Entregable:** política de ubicación, minimización y acceso; lista de
artefactos permitidos para el repositorio. No se copia ningún transcript
automáticamente.

#### F0.3 — Definir la rúbrica y anclas

Usar escala de 1 a 5 con descriptores para reducir variación entre evaluadores:

| Dimensión | 1 — Deficiente | 3 — Adecuado | 5 — Excelente |
|---|---|---|---|
| Ajuste al pedido | No responde o contradice formato/intención. | Responde el núcleo, con desvíos menores. | Responde directamente y respeta tema, formato, longitud y nivel. |
| Exactitud técnica | Error central o afirmación engañosa. | Núcleo correcto, con omisiones o matices faltantes. | Correcta, contextualizada y con límites importantes explícitos. |
| Claridad | Difícil de seguir; términos centrales sin explicar. | Comprensible, con organización suficiente. | Secuencia lógica, términos necesarios definidos y foco claro. |
| Profundidad pertinente | Insuficiente o sobrecargada para el pedido. | Nivel razonable, con alguna capa faltante o excedente. | Profundidad adecuada; distingue lo esencial del detalle opcional. |
| Valor pedagógico | No ayuda a razonar ni aplicar. | Incluye explicación o ejemplo útil, con oportunidades de mejora. | Explicación, ejemplo, guía o feedback facilitan transferencia y comprensión. |
| Contexto ciberseguridad | Conexión forzada o técnicamente incorrecta cuando se incluye. | Conexión pertinente pero general, o correctamente omitida si no aplica. | Relación de seguridad precisa y orgánica, con alcance claro. |
| Fiabilidad | Error, truncamiento o salida no utilizable. | Respuesta usable con problema menor. | Completa, sin fallos observables y consistente con la salida final. |

Reglas de puntuación:

- Marcar “no aplicable” cuando una dimensión no corresponda al pedido; no
  penalizar una síntesis por no incluir un ejercicio.
- Registrar por separado presencia de error operativo y calidad conceptual.
- No premiar longitud, jerga, número de secciones o cantidad de comandos por sí
  solos.
- Acompañar cada nota con una justificación breve y evidencia textual/turno.
- Resolver discrepancias entre evaluadores mediante discusión documentada; no
  borrar las puntuaciones iniciales.

**Entregable:** rúbrica versionada y guía de ejemplos/anclas antes de puntuar.

#### F0.4 — Clasificar el conjunto de preguntas

Etiquetar cada pregunta según una o más categorías:

- definición/conocimiento factual;
- explicación de mecanismo;
- comparación;
- síntesis o restricción de formato;
- código o pseudocódigo;
- diagnóstico/corrección de misconception;
- seguimiento contextual;
- transferencia o aplicación;
- pregunta que requiere fuentes del curso.

Registrar además:

- nivel esperado;
- prerrequisitos necesarios;
- formato pedido;
- si la conexión con ciberseguridad es orgánica;
- criterios mínimos de una respuesta aceptable;
- hechos dependientes de plataforma o arquitectura.

**Entregable:** especificación del benchmark y clave de evaluación, sin respuestas
modelo inventadas retrospectivamente.

#### F0.5 — Definir metadatos de futuras ejecuciones

Para cada corrida futura registrar, si está disponible:

- identificador y versión del modelo;
- versión/hash del prompt y del código TALOS;
- fecha y configuración relevante;
- texto exacto del prompt del usuario;
- fuentes suministradas y si fueron seleccionadas;
- salida completa visible al usuario;
- latencia total y, si existe, tiempo al primer token;
- motivo de finalización, número de tokens y estado de streaming;
- error de proveedor/backend/frontend;
- si la respuesta fue puntuada o excluida y por qué.

No almacenar secretos, credenciales, información personal innecesaria ni
contenido interno del modelo. No tratar campos no disponibles como si se
hubieran medido: registrar “no disponible”.

**Entregable:** plantilla de registro de corrida y política de retención.

#### F0.6 — Definir protocolo de evaluación

1. Para puntuación comparativa de respuestas: quitar nombres de sistema,
   aleatorizar orden y conservar identificadores ciegos.
2. Solicitar dos evaluadores independientes para una muestra piloto; decidir
   luego si el volumen requiere dos evaluadores en todo el corpus.
3. Hacer calibración inicial con un pequeño subconjunto y aclarar descriptores
   ambiguos antes de puntuar el resto.
4. Reportar distribución por dimensión, diferencias por categoría y tasa de
   fallos; no solo un promedio global.
5. Distinguir análisis retrospectivo de la corrida ya realizada de futuras
   corridas controladas. No rellenar retroactivamente versiones, prompts o
   latencias desconocidos.
6. Fijar antes de una nueva comparación el criterio de mejora y el margen
   aceptable de no inferioridad de exactitud/seguridad.

**Entregable:** protocolo breve aprobado antes de iniciar Fase 1.

### Criterios de salida de Fase 0

La fase estará completa cuando:

- las 20 preguntas tengan un estado de evidencia y emparejamiento documentado;
- la integridad y limitaciones de cada respuesta estén marcadas;
- los datos privados permanezcan fuera del repositorio;
- la rúbrica, categorías y reglas de “no aplicable” estén definidas antes de
  puntuar;
- haya una plantilla de metadatos para próximas ejecuciones;
- exista un protocolo de evaluación reproducible;
- el informe diferencie observaciones, inferencias e hipótesis;
- no se haya cambiado todavía el comportamiento de TALOS.

### Fuera de alcance de Fase 0

- Arreglar prompts o implementar el override de síntesis.
- Corregir errores 500, latencia, streaming o límites de tokens.
- Declarar ganador global a TALOS o NotebookLM.
- Repetir el benchmark ya ejecutado con estado de estudiante real.
- Cambiar o publicar el estado BKT, snapshots o base de datos.
- Hacer push o incluir datos privados en Git.

## Plan detallado para la Fase 1

### Propósito y límite

Traducir el pedido del turno actual a un contrato de respuesta explícito y
consistente, de modo que las directivas generales de fase o los hábitos
pedagógicos no anulen lo que el estudiante pidió. Esta fase cambia el
enrutamiento/ensamblado de prompts y sus pruebas; no rediseña todavía todas las
plantillas pedagógicas de la Fase 2 ni diagnostica streaming/fiabilidad de la
Fase 6.

### Línea de base observada

En el código inspeccionado para este plan:

- `classify_pedagogical_intent` y `RESPONSE_MODES` viven en
  `src/study_engine/pedagogy/structured_pipeline.py`. El clasificador usa
  reglas de frases/substring y elige una intención principal.
- `build_phase_prompt` calcula `active_mode`, puede sustituir la directiva de
  fase por instrucciones específicas de modo y luego agrega reglas generales de
  salida.
- Hay cierres socráticos obligatorios en instrucciones generales y por fase,
  aunque algunos modos ya indican que no debe forzarse la pregunta.
- El formato básico especial solo se usa bajo condiciones particulares:
  `context_mode == "basic"`, modo `explain_concept`, sin comando estructurado y
  no continuación.
- La clasificación y el armado de prompts ya se prueban, entre otros, en
  `tests/unit/pedagogy/test_adaptive_pipeline.py` y
  `tests/pedagogy/test_socratic_system_prompt.py`.

Antes de implementar, volver a verificar rama, árbol, firmas, callers y tests;
estos son datos del estado inspeccionado, no una garantía de que el código siga
igual. Reutilizar el flujo vigente y no crear un segundo clasificador si ya
existe una modificación posterior.

### Decisión de diseño

Separar dos cosas que hoy pueden confundirse:

- **Tarea/intención:** qué acción educativa pide el estudiante.
- **Restricciones/modificadores:** en qué formato y con qué extensión debe
  responder TALOS.

Contrato conceptual propuesto (los nombres son ilustrativos y deben seguir los
tipos y patrones del repositorio):

| Campo | Semántica |
|---|---|
| `task` | Explicar, sintetizar, comparar, corregir una misconception, evaluar código, dar ejemplo/código, proponer ejercicio, continuar o recomendar próximo tema. |
| `depth` | Breve, estándar, profunda o no especificada. No inferir profundidad no solicitada salvo una política contextual existente y comprobable. |
| `format` | Prosa, lista, tabla, pseudocódigo, código y lenguaje solicitado, traza, diagrama, laboratorio u otro formato explícito. |
| `length_constraint` | Ninguna explícita, o un límite cuantificado de frases, líneas o palabras. No transformar un límite de líneas en solo un máximo genérico de palabras. |
| `include` | Elementos pedidos, como ejemplo, código, analogía, mecanismo o aplicación de seguridad. |
| `exclude` | Restricciones como “sin código”, “no lo resumas” o “sin pregunta al final”. |
| `follow_up` | Incluir una comprobación/pregunta, excluirla o dejarla opcional según tarea y pedido. |
| `confidence` | Grado de certeza sobre intención; si falta información esencial, permitir una aclaración concisa. |

Preferir un objeto interno pequeño y tipado si encaja en la arquitectura actual.
No agregar campos a la API pública ni persistir el contrato si no se demuestra
que hace falta.

### Orden de precedencia

Resolver conflictos una vez antes de ensamblar el prompt:

1. Seguridad y límites de operación, que no se anulan por una solicitud de
   formato.
2. Exactitud, honestidad y requisitos de fuentes.
3. Intención explícita del turno actual y sus límites de formato, longitud,
   inclusiones y exclusiones.
4. Modo pedagógico adecuado a la tarea.
5. Contexto y preferencias duraderas del estudiante, cuando sean pertinentes.
6. Directivas de fase, estilo general y hábitos por defecto de TALOS.

Si se solicita “profundidad en cinco líneas”, respetar las cinco líneas y
concentrar los mecanismos esenciales; si no es posible ser exhaustivo en ese
límite, no afirmar exhaustividad y ofrecer ampliar. Si se pide “solo la
respuesta”, no añadir una pregunta socrática obligatoria. Si se pide código
funcional, el nivel de principiante debe modular la explicación, no bloquear el
código. Una solicitud conceptual no debe activar código solo porque la plantilla
general lo menciona.

### Paquetes de trabajo

#### F1.1 — Trazar el flujo de decisión actual

1. Seguir `user_query` desde la ruta de chat hasta el contrato y prompt final.
2. Determinar si una `pedagogical_mode` externa puede reemplazar la intención
   inferida y cuál es la precedencia efectiva.
3. Revisar convivencia de clasificador, comando estructurado, fase solicitada,
   contexto BKT, continuación, formato y reglas globales.
4. Identificar reglas duplicadas o incompatibles de longitud, código y cierre.
5. Verificar los callers y los tests existentes antes de elegir los puntos de
   modificación.
6. Registrar comportamiento actual de los casos de prueba abajo con mocks y
   prompts ensamblados; no llamar al proveedor ni ejecutar otra sesión con el
   estado del estudiante.

**Entregable:** mapa breve del flujo real y lista de puntos únicos de decisión
que se modificarán.

#### F1.2 — Especificar el contrato y el resolvedor

1. Definir el tipo interno mínimo que separa la tarea de sus modificadores.
2. Diferenciar señales explícitas de inferidas/defaults cuando esa distinción
   afecte la prioridad o el fallback.
3. Mantener el clasificador actual como base, extendiéndolo para extraer
   restricciones en vez de crear un detector de palabras independiente.
4. Procesar frases completas y su contexto: negaciones, límites cuantificados,
   solicitudes mixtas y cambios de tema.
5. Fallback conservador: ante ambigüedad, conservar el modo conceptual general,
   respetar instrucciones literales inequívocas y no inventar formato o
   profundidad.
6. No agregar una llamada extra a un LLM para clasificar cada turno en esta fase,
   salvo justificación concreta con medición de latencia/costo y necesidad
   arquitectónica.

**Entregable:** contrato, precedencia, fallback y ejemplos límite documentados
en tests.

#### F1.3 — Integrar el contrato en el ensamblador

1. Construir las instrucciones desde el contrato resuelto para que no compitan
   reglas generales contradictorias.
2. Respetar límites explícitos por unidad correcta: frase, línea o palabra;
   eliminar del camino aplicable solo las reglas globales que entren en
   conflicto probado.
3. Aplicar `follow_up`: permitir/suprimir preguntas finales según el pedido y la
   tarea, sin hacer que el sistema deje de usar comprobaciones cuando sí ayudan.
4. Mantener el contenido autorizado, seguridad, contexto BKT y comandos
   estructurados excepto cuando exista un conflicto demostrado y resuelto por
   la jerarquía acordada.
5. Dejar el diseño completo de las plantillas de explicación, ejercicio y
   feedback para Fase 2; Fase 1 decide qué modo y restricciones aplican.
6. Mantener el comportamiento conceptual estándar por defecto cuando no hay
   señales explícitas, salvo cambio respaldado por un test de regresión.

**Entregable:** contrato consumido por el ensamblador real y prompt sin
contradicciones conocidas para los casos cubiertos.

#### F1.4 — Añadir pruebas unitarias deterministas

Ampliar los módulos existentes para clasificador y pipeline (rutas actuales:
`tests/unit/pedagogy/test_adaptive_pipeline.py` y
`tests/pedagogy/test_socratic_system_prompt.py`, a reconfirmar antes de editar).
Cubrir como mínimo:

| Caso | Entrada representativa | Aserción de comportamiento |
|---|---|---|
| Una frase | “En una frase, ¿qué es un proceso?” | Contrato conciso; no pregunta final obligatoria ni secciones añadidas. |
| Cinco líneas | “Resumí todo en 5 líneas.” | Límite de líneas preservado hasta las instrucciones finales. |
| Negación | “No lo resumas; explicá el mecanismo paso a paso.” | No activa la tarea de síntesis; mantiene la explicación. |
| Profundo | “Explicá en profundidad cómo funciona la planificación.” | Activa detalle pertinente sin inventar código ni límite breve. |
| Profundo + límite | “Explicalo en profundidad, en 5 líneas.” | Conserva cinco líneas, prioriza mecanismos y no promete exhaustividad. |
| Código pedido | “Mostrame un ejemplo en C de cómo se crea un proceso.” | Código C permitido; no activa anti-atajo solo por pedir código. |
| Sin código | “Explicame `fork()` sin código.” | No exige ni inserta un bloque de código desde la plantilla. |
| Aceptar ejercicio | “Sí, hagamos el ejercicio.” con historial pertinente. | Resuelve la continuación con contexto; no exige repetir el tema. |
| No entendí | “No entendí la analogía; probá de otra manera.” | Selecciona re-explicación/cambio de enfoque, no respuesta breve accidental. |
| Próximo tema | “¿Qué tema conviene estudiar ahora?” | Recomendación breve sin afirmar progreso no observado ni forzar quiz. |
| Pregunta ordinaria | “¿Qué es un proceso?” | Conserva el modo general conceptual, sin falso `quick_answer`. |
| Excluir cierre | “Definilo en una frase y no hagas una pregunta.” | La instrucción final suprime el cierre socrático. |

Los tests deben validar el contrato resuelto y la política final presente/ausente
en el prompt; no depender de respuesta textual exacta de un LLM. Una aserción
de que existe una frase en el prompt no es suficiente para probar la prioridad
o el comportamiento.

#### F1.5 — Probar la ruta de chat con mocks

1. Usar backend determinista/mock y verificar el paso de consulta a contrato y
   prompt.
2. Comprobar salida sintética capturada, evento de finalización e historial
   cuando aplique.
3. Verificar que la ruta real no agregue una pregunta o apéndice después de la
   respuesta breve.
4. Probar solicitud explícita de código y negación de código por la misma ruta.
5. Añadir no regresión para evidencia autorizada, abstención y comandos
   estructurados si comparten el ensamblador.
6. No mutar BKT, base del estudiante ni depender de servicios externos.

**Entregable:** cobertura de integración de la ruta de chat sin red/proveedor.

#### F1.6 — Gate offline contra la línea de base

1. Usar los casos de la [línea de base Fase 0](./FASE0_LINEA_BASE_TALOS_NOTEBOOKLM.md),
   con atención a #6, #7, #13, #19 y #20 para solicitudes/modificadores, y #3,
   #8, #9, #11 y #12 para corrección, contexto y continuación.
2. Comparar prompts/contratos antiguos y nuevos mediante mocks o snapshots
   deterministas, sin repetir el benchmark ni llamar a APIs.
3. Confirmar que las diferencias son intencionales y limitadas a intención,
   longitud, formato o cierre.
4. Verificar que fuentes, seguridad, fase, contexto pedagógico y abstención no
   cambian salvo los casos de precedencia documentados.
5. Reservar una nueva corrida humana/modelo para la fase de evaluación
   correspondiente, con condiciones y consentimiento documentados.

**Entregable:** resumen de casos cubiertos, prompts comparados, regresiones y
limitaciones.

### Criterios de aceptación

- Hay una sola precedencia implementada y documentada para pedido actual, modo,
  fase, contexto y defaults.
- Tarea y modificadores de salida son distinguibles en los casos cubiertos.
- Negaciones explícitas no activan falsamente síntesis ni otro modo.
- Límites de una frase/cinco líneas no reciben apéndices ni preguntas forzadas.
- Código explícitamente pedido sigue permitido; “sin código” se respeta.
- Continuaciones como “Sí, hagamos el ejercicio” usan el contexto disponible.
- Seguridad, exactitud, fuentes y abstención no pueden ser anuladas por formato.
- Pasan las pruebas unitarias y de integración afectadas y la selección de
  pruebas pedagógicas pertinente.
- No se ejecutan llamadas externas ni se repite la comparación en el gate.
- El diff se limita al resolvedor/ensamblador y sus tests; no toca áreas
  congeladas.

### Fuera de alcance

- Rediseñar todas las plantillas de enseñanza y feedback (Fase 2).
- Cambiar modelo/proveedor o hacer fine-tuning.
- Subir límites de tokens sin evidencia.
- Arreglar incidentes independientes de proveedor/streaming (Fase 6).
- Copiar literalmente el prompt de NotebookLM a todos los notebooks.
- Alterar BKT, datos de estudiantes, fuentes o políticas de seguridad.
- Hacer push o ejecutar otra prueba comparativa externa.

### Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Keyword detector activa modo por negación o mención incidental. | Extraer tarea y modificadores separadamente; probar negaciones y falsos positivos. |
| Override amplio invalida exactitud o fuentes. | Resolver prioridad estructuralmente y mantener invariantes superiores. |
| Código se bloquea por perfil principiante. | El nivel adapta explicación; no cancela formato pedido. |
| Síntesis elimina un matiz esencial. | Ser conciso sin afirmar exhaustividad; ofrecer ampliar si es necesario. |
| Cambia comportamiento ordinario no solicitado. | Fallback, snapshots de prompt y regresiones con preguntas estándar. |
| Se pierde tema en un seguimiento breve. | Pruebas con historial mediante la ruta mockeada. |
| Tests verifican texto de instrucción, no comportamiento. | Afirmar campos y precedencia resuelta y probar la integración real. |

### Secuencia recomendada de ejecución

1. Revisar branch, diff, firmas y callers; preservar cambios preexistentes.
2. Añadir primero pruebas deterministas para el contrato y casos límite.
3. Implementar el contrato interno mínimo y el resolvedor de precedencia,
   reutilizando la clasificación vigente.
4. Integrar el resultado en un solo lugar del ensamblador; retirar únicamente
   reglas que entren en conflicto demostrado.
5. Añadir pruebas de ruta de chat y no regresión.
6. Ejecutar pruebas focalizadas y resumir diff, resultados y límites.
7. Actualizar este handoff y comprobar cada criterio de aceptación; no proclamar
   superioridad comparativa sin evaluación posterior.

## Plan detallado para las Fases 2–7

Las tareas y rutas de test indicadas a continuación son una guía de
implementación, no una afirmación de que los módulos ya existan con esos
nombres. Antes de cada fase, localizar el punto real de integración y adaptar
las rutas al diseño vigente sin crear abstracciones paralelas. Mantener cada
fase acotada y actualizada en su registro de ejecución.

## Fase 2 — Modos pedagógicos y profundidad progresiva

### Objetivo y fundamento

Convertir la intención ya resuelta por Fase 1 en estrategias de enseñanza
distintas. La evidencia metodológica disponible es el prompt de NotebookLM
aportado por el usuario y los casos del benchmark: guía de ejercicios, feedback
ante una respuesta incorrecta, reparación de una confusión, seguimiento como
“no entendí”, síntesis y recomendación del siguiente tema. Esa evidencia
justifica diseñar modos explícitos; no demuestra qué modo causó por sí solo una
diferencia de calidad.

El criterio central es adecuación a la tarea, no maximizar longitud ni usar una
plantilla fija. Una pregunta factual debe recibir respuesta directa; un pedido
de ejercicio debe preservar el trabajo cognitivo del estudiante; una solicitud
de solución completa puede recibirla si el usuario la pide; “no entendí” debe
cambiar de enfoque; y un límite de extensión del contrato de Fase 1 sigue
prevaleciendo sobre cualquier modo.

### Alcance

- Definir estrategias por tarea para explicación, profundización, síntesis,
  ejercicio guiado, feedback, corrección de misconception, reexplicación y
  laboratorio conceptual.
- Diferenciar modo de enseñanza de perfil/nivel estimado del estudiante.
- Incorporar principios útiles del prompt NotebookLM sin copiar sus formatos
  de programación a otras materias.
- No cambiar el modelo, entrenarlo ni introducir un segundo clasificador LLM.
- No cambiar BKT ni afirmar aprendizaje a partir de señales de conversación.

### Paquetes de trabajo

#### F2.1 — Inventariar las plantillas y sus conflictos

1. Localizar el selector de modos, plantillas de fase, cierres socráticos,
   guardas anti-solución, formatos por nivel y callers actuales.
2. Para cada modo, registrar entrada, salida esperada, requisitos obligatorios,
   partes opcionales y reglas que debe suprimir.
3. Identificar repeticiones y conflictos con el contrato de Fase 1: por
   ejemplo, un cierre obligatorio incompatible con una frase solicitada, o una
   plantilla de principiante que impida entregar código expresamente pedido.
4. No reemplazar prompts enteros sin una matriz de casos que muestre qué regla
   actual falla y qué comportamiento nuevo se espera.

**Entregable:** inventario breve modo → plantilla → conflicto → test.

#### F2.2 — Especificar los modos observables

Definir una política compacta por modo, manteniendo la respuesta natural y
adaptable:

| Modo | Contrato pedagógico mínimo | Evitar |
|---|---|---|
| Concepto | Respuesta directa; definición de términos necesarios; mecanismo o ejemplo cuando aporte | Secciones obligatorias no pedidas |
| Profundización | Capas conceptuales y formales pertinentes, dependencias y límites | Confundir extensión con rigor o inventar detalles |
| Síntesis | Núcleo correcto en la forma/límite pedido | Introducción, cierre o quiz que rompan el límite |
| Ejercicio guiado | Objetivo, datos/condiciones, primer paso o pregunta accionable; esperar intento salvo pedido de solución | Revelar solución completa por defecto |
| Solución completa solicitada | Solución completa en formato requerido, con explicación proporcional y verificaciones | Aplicar paternalistamente la regla de no resolver |
| Feedback/corrección | Separar aciertos, error exacto, razón y siguiente paso | Etiquetar al estudiante o repetir la solución entera innecesariamente |
| Reexplicación | Reconocer la dificultad brevemente; cambiar analogía, escala o representación; aislar prerrequisito | Repetir literalmente la misma explicación |
| Recomendación/continuación | Proponer siguiente paso conectado al contenido observado; expresar incertidumbre sobre dominio | Afirmar progreso o mastery no medido |
| Laboratorio | Objetivo, entorno, precondiciones, pasos seguros, resultado e interpretación | Instrucciones dañinas o ejecutar acciones reales implícitamente |

Los componentes son mínimos, no una plantilla fija. La longitud y forma
solicitadas en Fase 1 recortan o reorganizan el modo. Una respuesta puede omitir
analogía, código o pregunta de comprobación si no se pidieron y no son
necesarios.

#### F2.3 — Resolver la política de ejercicio socrático

1. Diferenciar ofrecer un ejercicio, continuar un ejercicio aceptado, revisar
   el intento y entregar la solución completa solicitada.
2. Si solo se pidió “hagamos el ejercicio”, mostrar el enunciado y un siguiente
   paso abordable; no asumir que el estudiante quiere respuesta final.
3. Si ya existe intento, referirse a la parte concreta del intento usando solo
   historial disponible.
4. Si el estudiante pide explícitamente solución completa, respetar esa
   solicitud, salvo políticas de seguridad o límites de integridad académica
   vigentes que deban verificarse en el repositorio.
5. Probar respuestas correctas, parcialmente correctas, erróneas, vacías y
   ausencia de contexto. No inventar el intento faltante.

#### F2.4 — Implementar y probar los modos

- Reutilizar el contrato tipado de Fase 1; no reparsear el mensaje en cada
  plantilla.
- Mantener las plantillas en los módulos/repositorios de prompts existentes y
  usar helpers comunes si ya los hay.
- Añadir tests unitarios de la estrategia y tests de integración del prompt
  ensamblado para: conceptos, “no entendí”, intento erróneo, ejercicio
  aceptado, solución completa explícita, síntesis y recomendación.
- Usar doubles deterministas para probar flujo e historial. No exigir que el
  modelo genere una frase literal exacta.
- Añadir pruebas de no regresión entre materias: un ejemplo de programación y
  un ejemplo de SO/redes/seguridad deben recibir representaciones adecuadas a
  su tema.

### Criterios de aceptación

- Cada tarea del alcance tiene una política identificable y fallback
  conservador.
- Una negativa a entregar solución completa solo se aplica al ejercicio
  guiado cuando no hay solicitud explícita de solución completa y ninguna
  política superior exige otra cosa.
- Un pedido de reexplicación cambia realmente la estrategia señalada en el
  prompt, no solo añade un encabezado.
- Una solicitud de profundidad no se convierte automáticamente en una respuesta
  interminable; una síntesis no pierde el hecho central.
- No se infiere dominio a partir de una respuesta aislada ni se modifica BKT.
- Pasan pruebas unitarias, integración mockeada y regresiones de los modos
  afectados; el diff queda acotado a política/plantillas/tests.

### Riesgos, mitigaciones y fuera de alcance

- **Riesgo:** el “estilo socrático” retiene información que el estudiante pide.
  **Mitigación:** intención explícita en Fase 1 prevalece; test de solución
  completa explícita.
- **Riesgo:** plantilla demasiado rígida crea respuestas repetitivas.
  **Mitigación:** definir requisitos semánticos mínimos, no formato textual fijo.
- **Fuera de alcance:** estimar mastery, cambiar algoritmos BKT, añadir
  personalización persistente o ejecutar evaluación humana.

### Registro de salida requerido

Anotar los modos creados/ajustados, archivos exactos, tests ejecutados,
incidencias conocidas, comportamiento no cubierto y decisión de salida. No
marcar la fase completada solo porque se haya añadido texto a un prompt.

## Fase 3 — Rigor técnico y conexión con ciberseguridad

### Objetivo y fundamento

Elevar la precisión sin convertir cada respuesta en una lista de jerga o
amenazas. La evidencia de Fase 0 es deliberadamente mixta: en algunas
respuestas TALOS mostró profundidad, mientras que hay casos de alineación
incierta, interrupción y error operativo; la transcripción no permite comprobar
toda afirmación ni inferir causa. Por ello, esta fase transforma el rigor en
requisitos verificables y contexto explícito, no en “más capas” por defecto.

### Alcance

- Controlar afirmaciones técnicas dependientes de entorno.
- Separar definición, mecanismo, analogía, simplificación, ejemplo y
  consecuencia de seguridad.
- Hacer conexiones de ciberseguridad únicamente cuando haya relación causal o
  didáctica defendible.
- Mejorar abstención/localización de incertidumbre y trazabilidad a fuentes
  autorizadas cuando estén disponibles.
- No inventar una base nueva de hechos, citas o referencias.

### Paquetes de trabajo

#### F3.1 — Crear una taxonomía de afirmaciones de riesgo

Clasificar las afirmaciones generadas o las reglas de prompt relevantes en:

1. Hechos conceptuales relativamente estables.
2. Detalles dependientes de OS, distribución, arquitectura, ABI, compilador,
   versión, configuración o privilegios.
3. Comportamientos de herramienta/API que requieren fuente/versionado.
4. Afirmaciones de vulnerabilidad, CVE, impacto o explotabilidad.
5. Analogías y simplificaciones que necesitan marcar sus límites.
6. Consejos de mitigación/detección que deben respetar contexto defensivo.

Priorizar casos presentes en temario y benchmark; no intentar enumerar toda
ciberseguridad en un prompt global.

#### F3.2 — Definir un patrón de explicación técnica

Para un tema de mecanismo, usar las capas pertinentes, no todas
obligatoriamente:

1. Respuesta directa / idea central.
2. Definición de términos que el estudiante necesite.
3. Secuencia causal: actores, estado, transición y resultado.
4. Ejemplo, traza o representación ajustada al asunto.
5. Condiciones de validez y variantes del entorno.
6. Implicación de seguridad, defensa o análisis si aporta al objetivo.
7. Fuente o nivel de incertidumbre cuando la afirmación dependa de evidencia.

Expresar contexto de manera concreta (“en Linux x86-64 con X”, si se sabe).
Si no se sabe, formular el principio general y declarar la dependencia; no
rellenar el entorno suponiendo una plataforma.

#### F3.3 — Revisar casos de ciberseguridad con criterio de evidencia

Cuando se explique una vulnerabilidad o mitigación, especificar lo necesario
entre:

- activo o propiedad afectada;
- precondiciones;
- mecanismo causal;
- impacto plausible y límites;
- mitigación/defensa y trade-offs;
- fuente confiable y versión/fecha para afirmaciones cambiantes.

No exigir la lista completa en una explicación breve. No elevar una anécdota,
CVE o caso histórico a prueba universal. Para información actualizada, comprobar
si el repositorio dispone de fuentes integradas antes de añadir dependencia
externa; no afirmar que se consultó una fuente no consultada.

#### F3.4 — Implementar guardas de rigor proporcionadas

- Mejorar instrucciones existentes o validadores solo cuando una regresión
  concreta lo justifique.
- Considerar metadatos internos opcionales para entorno/fuente si la
  arquitectura ya los soporta; no crear una ontología nueva en esta fase.
- Crear tests para contexto ausente, contexto conocido, afirmación histórica,
  afirmación CVE, analogía limitada y vínculo de ciberseguridad no pertinente.
- Para afirmaciones factuales sensibles, añadir tests con criterios semánticos
  o revisión humana documentada; no usar coincidencia de strings como prueba
  de verdad.
- Si una comprobación requiere fuentes externas, separarla del gate offline y
  registrar fecha, fuente y alcance.

### Criterios de aceptación

- Las respuestas cubiertas distinguen principio general y detalle contextual
  cuando la diferencia es importante.
- No se fuerzan conexiones de seguridad en conceptos donde distraen o inducen
  causalidad falsa.
- Las afirmaciones de vulnerabilidad no presentan como universal lo que depende
  de versión/configuración; incertidumbre y ausencia de fuente son explícitas.
- Tests detectan al menos regresiones representativas de contexto conocido y
  desconocido, manteniendo respuestas breves si así lo pide Fase 1.
- La fase no agrega referencias bibliográficas inventadas ni dependencia de
  consulta externa no declarada.

### Riesgos y límites

- **Riesgo:** requerir demasiadas capas hace las respuestas densas.
  **Mitigación:** selección por tarea y contrato; pruebas con pregunta breve y
  pregunta profunda.
- **Riesgo:** prompt dice “sé exacto” pero el modelo igualmente se equivoca.
  **Mitigación:** no contar una regla de prompt como validación factual; usar
  revisión de contenido, fuentes y abstención en los casos de riesgo.
- **Fuera de alcance:** certificación formal de seguridad, asesoramiento
  operativo sobre objetivos reales, garantía de ausencia de alucinaciones o
  cobertura universal del dominio.

## Fase 4 — Formato, pseudocódigo y código

### Objetivo y fundamento

Garantizar que la forma de salida ayude a entender el tema y respete el pedido.
La prueba original incluyó una petición explícita de ejemplo en C (#6) y
peticiones de síntesis estricta (#13 y #19); el usuario también reportó en el
diagnóstico previo fugas de etiquetas de pseudocódigo y código ejecutable
imprevisto. Estas últimas son señales reportadas, no una causa raíz ya
demostrada; reproducirlas y comprobar sus superficies antes de fijar el test.

### Alcance y distinciones

- Elegir prosa, tabla, lista, pseudocódigo, diagrama, código, traza o laboratorio
  de acuerdo al contrato y al mecanismo explicado.
- Mantener petición explícita de código y de lenguaje como restricción de salida,
  no como una oportunidad para producir un proyecto mayor.
- Separar ejemplo ejecutable de pseudocódigo/algoritmo conceptual.
- Validar la respuesta final visible, además de las instrucciones del prompt.
- Esta fase no implementa un parser general de código ni reemplaza controles de
  seguridad.

### Paquetes de trabajo

#### F4.1 — Inventariar productores y consumidores de formato

1. Buscar plantillas de formato, extracción de bloques, markdown, diagramas,
   código, pseudocódigo, sanitización y renderizado en frontend.
2. Verificar qué lenguajes autoriza cada ruta, cómo se expresa “sin código” y
   si respuestas en varias fases podrían volver a agregar bloques prohibidos.
3. Seguir los datos hasta el cliente: prompt ensamblado → streaming → respuesta
   final → renderizado.
4. Reproducir las salidas reportadas de `pseudocircle` y código inesperado con
   fixtures/salidas simuladas, si existe evidencia; no atribuirlas al servidor o
   renderer sin trazado.

#### F4.2 — Definir política de selección de representación

- Un pedido literal de formato prevalece, excepto límites de seguridad,
  exactitud y factibilidad; explicar si un formato no puede cumplirse.
- Sin pedido literal, escoger la representación mínima que modele el concepto.
- Un diagrama solo cuando aclare relaciones/flujo; un bloque de lenguaje
  ejecutable solo con pedido explícito o necesidad didáctica clara permitida por
  el contrato.
- El pseudocódigo debe etiquetarse con un identificador soportado y consistente
  (`text` o `pseudocode`, según el renderer actual); nunca emitir una etiqueta
  inventada como `pseudocircle`.
- No tratar una etiqueta de bloque como garantía de que el contenido sea
  pseudocódigo: comprobar que no filtre sintaxis ejecutable cuando ese sea el
  requisito.
- Si el usuario pide C, Python u otro lenguaje, no sustituirlo automáticamente
  por pseudocódigo por su nivel principiante.

#### F4.3 — Implementar control de formato sin pérdida de datos

1. Reutilizar el `ResponseIntent`/extracción estructural ya implementado; evitar
   reglas divergentes para misma intención.
2. Consolidar conflictos entre reglas generales de pseudocódigo y bloques
   explícitos C/Python/SQL. Una petición de lenguaje específico debe permitir
   ese lenguaje; una exclusión de código debe eliminar directivas que lo
   requieran.
3. Validar únicamente invariantes comprobables de salida: etiqueta permitida,
   límite de bloques cuando esté especificado, no aparición de bloques
   ejecutables en modo sin código, formato y longitud cuando sea posible.
4. No reescribir silenciosamente una salida si el validador no puede corregirla
   de manera segura. Si falla, hacer un reintento limitado solo si el sistema ya
   tiene un patrón seguro, o devolver estado de error/incompleto explícito.
5. No declarar “sanitización” si el código únicamente añade una instrucción de
   prompt.

#### F4.4 — Crear matriz de regresión de formato

Cubrir al menos:

- solicitud de ejemplo en C, lenguaje correcto y bloque parseable;
- explicación conceptual sin código: cero bloques ejecutables;
- solicitud de pseudocódigo: etiqueta aprobada y estructura de control clara;
- contenido que menciona “código C” para preguntar qué es, sin solicitar que se
  genere código;
- solicitud de texto/prosa;
- Mermaid/diagrama pedido y no pedido;
- respuesta en una línea/frase/cinco líneas junto a un bloque de cierre;
- salida con etiqueta inválida o lenguaje ejecutable filtrado;
- seguridad: payloads o instrucciones en ejemplos que no deben convertirse en
  acciones contra sistemas reales.

Usar fixtures deterministas y pruebas del renderer existentes. Si no hay
validador del contenido semántico, documentar el límite en vez de presumirlo.

### Criterios de aceptación

- El contrato decide si se permite código y qué lenguaje/formato se pidió; no
  hay directivas contradictorias en el prompt ensamblado para los casos probados.
- “Sin código” no produce un bloque ejecutable ni por plantilla común ni por
  fases posteriores de respuesta.
- Pseudocódigo usa formato soportado y no se confunde con C/Python disfrazado.
- Peticiones explícitas de código funcional se respetan cuando son seguras.
- Los tests atraviesan ensamblado y, cuando exista, parsing/renderizado final.
- Los errores de validación no se ocultan detrás de una respuesta que parezca
  completa.

### Riesgos y fuera de alcance

- La detección regex de bloques no prueba semántica del código; no utilizarla
  para certificar corrección.
- Un renderer puede aceptar una etiqueta mientras su representación visual sea
  incorrecta; comprobar las dos superficies.
- No ejecutar código generado automáticamente en entorno del estudiante.
- No fijar etiquetas no soportadas por la interfaz antes de verificar el
  renderer y el contrato de Markdown del proyecto.

## Fase 5 — Fuentes, memoria y continuidad

### Objetivo y fundamento

Responder seguimientos coherentemente sin inventar qué antecedente refiere el
estudiante ni exagerar lo que recuerdan TALOS, el perfil o las fuentes. Las
preguntas #3–#5, #7–#9, #12 y #15–#20 del benchmark dependen en distinto grado
del tema anterior, de referencias como “eso”/“volviendo a lo anterior” y del
estado real de la conversación. Los transcripts existentes permiten localizar
seguimientos por contenido/orden, pero no miden de forma controlada la
recuperación interna.

### Alcance

- Preservar en contexto la información necesaria para resolver referencias y
  continuidad de tareas.
- Distinguir historial conversacional, perfil/preferencia, estado de dominio y
  contexto recuperado de fuentes.
- Marcar procedencia de afirmaciones cuando responden a documentos del curso.
- No inferir dominio estable ni escribir memoria permanente a partir de una
  respuesta aislada.
- No incorporar una nueva base vectorial/Mem0 u otro almacén si la fase no
  demuestra una necesidad y el usuario no aprueba cambios de arquitectura/datos.

### Paquetes de trabajo

#### F5.1 — Trazar el contexto disponible de extremo a extremo

1. Seguir mensajes previos, resumen de conversación, notebook/materiales,
   perfil y datos de progreso desde sus productores a la ruta de chat y al
   prompt/contexto final.
2. Registrar límites actuales de ventana, truncamiento y orden; no asumir que
   cada canal persiste lo mismo.
3. Determinar si citas y referencias de fuente provienen de documentos
   recuperados o de conocimiento general.
4. Identificar qué datos son efímeros y qué datos se guardan; revisar privacidad
   y retención antes de proponer persistencia nueva.

**Entregable:** diagrama o tabla de origen → transformación → consumidor →
persistencia, con huecos confirmados.

#### F5.2 — Definir reglas para referencias y turnos incompletos

- Resolver “eso”, “la anterior”, “el segundo punto” o “volviendo a…” con el
  antecedente relevante más cercano disponible.
- Si hay más de un antecedente plausible, preguntar de forma breve en vez de
  elegir silenciosamente.
- Si falta el historial, declararlo y solicitar el fragmento mínimo necesario.
- Continuar ejercicios a partir del enunciado e intento efectivamente presentes;
  nunca fabricar una respuesta previa del estudiante.
- Distinguir corrección de la explicación anterior de cambio de tema.
- Si una pregunta requiere contexto del libro/documento y no se recuperó, decir
  que no se ve la fuente; no inventar página, cita ni definición textual.

#### F5.3 — Definir política de fuentes y evidencia

1. Distinguir (a) documento disponible, (b) fragmento recuperado, (c)
   interpretación del sistema y (d) conocimiento general.
2. Vincular citas/referencias con evidencia recuperada real, preservando
   localizador del sistema si existe.
3. Evitar citas decorativas o referencias sin soporte. No generar números de
   página por aproximación.
4. Si fuentes discrepan, señalar la discrepancia y su alcance; no fusionar
   versiones sin resolver.
5. Mantener las reglas de seguridad y privacidad sobre documentos del curso;
   no persistir texto con copyright innecesario.

#### F5.4 — Probar continuidad y memoria

Crear tests offline y mockeados para:

- antecedente único y claro;
- dos posibles antecedentes (debe aclarar);
- historial truncado/ausente;
- aceptación de ejercicio con y sin enunciado visible;
- corrección del intento real frente a uno parcialmente correcto;
- documento recuperado con localizador;
- ausencia de documento;
- fuente contradictoria/versión;
- preferencia estable existente vs. petición puntual que la contradice;
- no mutación de BKT/perfil en un turno ordinario.

Verificar tanto respuesta ensamblada como citas/metadatos visibles cuando
aplique. Tests de strings no prueban calidad de retrieval: para retrieval,
medir recall/precisión con documentos y queries etiquetados en el corpus de
evaluación de Fase 7.

### Criterios de aceptación

- Seguimientos definidos preservan antecedente correcto usando solo datos
  disponibles.
- Ambigüedad material o ausencia de contexto generan aclaración/declaración
  honesta, no alucinación de historial.
- Las citas apuntan a fuentes efectivamente presentes/recuperadas y ninguna
  fuente no vista se atribuye como consultada.
- Preferencia duradera no anula pedido puntual y una interacción no cambia
  automáticamente el nivel de dominio persistente.
- Sin nuevas escrituras/persistencia sensible no autorizadas.

### Riesgos y fuera de alcance

- Más contexto puede aumentar coste, latencia y exposición de datos; medir antes
  de ampliar ventanas o persistencia.
- Resúmenes de contexto pueden omitir negaciones o límites; incluirlos en tests.
- No afirmar que resolver referencias prueba memoria a largo plazo.
- No migrar stores, cambiar ranking global ni instrumentar perfil persistente
  sin fase aprobada y plan de datos.

## Fase 6 — Streaming, errores y fiabilidad de extremo a extremo

### Objetivo y fundamento

Separar calidad de contenido de la capacidad de entregarlo íntegramente. La
línea de base documenta un error 500 explícito, una respuesta parcial, una
demora anotada y una respuesta de síntesis no localizable en el log TALOS; esas
observaciones no identifican si falló frontend, backend, proveedor, timeout o
registro. La fase debe seguir la transacción completa y medir antes de cambiar
timeouts, límites o reintentos.

### Alcance

- Diagnosticar transporte, cancelación, errores, latencia y truncamiento en las
  rutas reales.
- Garantizar estados finales inequívocos y coherencia entre texto mostrado y
  texto persistido.
- Exponer solo errores seguros al estudiante; mantener detalles internos en
  logs apropiados sin secretos.
- No modificar auditoría/ejecución/evaluación protegidas ni cambiar máximos de
  tokens como remedio especulativo.

### Paquetes de trabajo

#### F6.1 — Mapear los estados de una respuesta

Seguir el flujo ruta SSE/HTTP → generador por fases → proveedor/mock →
eventos → cliente → almacenamiento/historial, verificando nombres reales y
contratos. Definir estados observables como:

- inicio aceptado;
- fase/texto parcial en progreso;
- completada correctamente;
- cancelada por usuario/cliente;
- timeout;
- error de proveedor;
- error interno;
- salida terminada por límite;
- salida vacía/abstención.

Separar estado de transporte de estado del contenido. No marcar como completa
una respuesta cuando el stream se interrumpió sin evento terminal válido.

#### F6.2 — Definir telemetría mínima y segura

Para cada solicitud, recoger únicamente datos operativos necesarios y
disponibles:

- identificador de correlación no personal;
- marca temporal/latencia por etapa y total;
- primer token si ya es medible;
- motivo terminal, tokens/finish reason cuando el proveedor los ofrezca;
- error categorizado por capa;
- si la respuesta se mostró, persistió y finalizó;
- versión de código/prompt si está disponible.

No registrar tokens de autenticación, cuerpos completos por defecto, datos
personales ni contenido interno. Cualquier logging del texto visible requiere
política de retención, minimización y autorización. Registrar “no disponible”
para medidas ausentes.

#### F6.3 — Hacer el diagnóstico causal con instrumentación

1. Reproducir cada clase de fallo con mocks y fixtures: excepción previa al
   primer token, caída después de tokens, cancelación, fin normal, timeout,
   truncamiento y evento malformado.
2. Correlacionar frontend/backend/proveedor con ID y estados terminales.
3. Verificar que cancelación detenga trabajo/coste cuando el contrato actual lo
   permita.
4. Confirmar que el consumidor del SSE distingue error, abortado, completado y
   texto parcial.
5. Con evidencia, decidir si corregir parser/eventos, timeout, retry,
   backpressure o persistencia; no cambiar varios knobs simultáneamente sin
   experimento que permita atribución.
6. Los reintentos deben ser acotados, idempotentes donde corresponda y no
   duplicar mensajes ni mutaciones de estudiante.

#### F6.4 — Validar coherencia y experiencia de error

- El texto renderizado debe corresponder a eventos recibidos en orden.
- Solo una terminación correcta produce estado completado.
- Si hubo texto parcial, comunicar explícitamente que la respuesta quedó
  incompleta y permitir recuperación segura, sin presentarla como explicación
  completa.
- Las excepciones se registran con clasificación y correlación, sin hacer
  catch-all que convierta fallo en respuesta exitosa.
- Reconciliar el texto visible y el que se guarda/reutiliza en contexto; no
  guardar como respuesta canónica una generación truncada sin indicarlo.

### Criterios de aceptación

- Cada ruta de terminación produce un estado terminal inequívoco y testeado.
- Fixtures prueban fallos antes/después del primer token, finalización,
  cancelación, timeout y truncamiento.
- No hay éxito falso, duplicación de respuesta, cierre perdido o mutación
  doble bajo los casos cubiertos.
- Métricas no contienen secretos/datos sensibles y tienen una política de
  retención.
- Los ajustes de latencia/timeout/token se basan en logs medidos y registran
  antes/después.
- Tests unitarios, SSE/cliente y persistencia relacionada pasan sin proveedor
  externo; integración real, si se requiere, es gate separado.

### Riesgos, mitigación y fuera de alcance

- **Riesgo:** instrumentación conserva datos sensibles.
  **Mitigación:** métricas por defecto sin contenido, minimización y revisión
  del esquema.
- **Riesgo:** retry causa respuesta duplicada o gasto inesperado.
  **Mitigación:** no retry automático sin idempotencia, límite y test.
- **Fuera de alcance:** prometer latencia SLA antes de definir carga, proveedor
  y métricas; aumentar tokens para ocultar truncamiento; cambios a auditoría
  protegida.

## Fase 7 — Evaluación, comparación y aprendizaje

### Objetivo y fundamento

Determinar si las fases mejoran respuestas y, en un estudio separado, si
mejoran aprendizaje. La comparación original consta de una corrida del usuario
con condiciones incompletas y transcripts de integridad desigual. Es una línea
de base cualitativa valiosa, no un experimento causal ni evidencia suficiente
para declarar ganador. Los puntajes no deben asignarse retrospectivamente como
si la rúbrica hubiese existido antes.

### Alcance y dos preguntas de investigación

**Evaluación de respuesta:** ¿la versión TALOS candidata entrega respuestas
más ajustadas, exactas, claras, pertinentes y fiables en los casos de uso
definidos?

**Evaluación de aprendizaje:** ¿los estudiantes retienen y transfieren mejor
lo aprendido después de usar TALOS? Esto no se responde puntuando textos ni con
el benchmark de 20 preguntas.

Mantener ambos estudios separados. La evaluación comparativa con NotebookLM
requiere condiciones explícitas de prompts, materiales y modelos; no atribuir
diferencias a TALOS si los recursos no están controlados. El diseño de
aprendizaje requiere consentimiento y un protocolo ético apropiado si se recogen
datos de participantes.

### Paquetes de trabajo

#### F7.1 — Congelar el conjunto y la especificación

1. Mantener los 20 enunciados canónicos del usuario como corpus original; no
   sustituirlos por variantes del JSON sin versionar y documentar el cambio.
2. Mantener separado un Golden Set futuro, ampliado y curado por materia,
   intención, dificultad, restricción, plataforma y riesgo técnico.
3. Para cada ítem añadir criterios mínimos de respuesta aceptable, condiciones
   que hacen la respuesta incorrecta y referencias autorizadas si exige fuentes.
4. No publicar transcripts privados, material con copyright, prompts secretos
   ni respuestas del estudiante.
5. Eliminar duplicados/contaminación y separar desarrollo de evaluación ciega
   para no optimizar prompts contra las respuestas de test.

**Entregable:** manifiesto versionado del set, schema, procedencia y criterios
de inclusión/exclusión, con corpus sensible separado.

#### F7.2 — Definir comparaciones que respondan preguntas distintas

1. **Antes/después TALOS:** mismo conjunto, mismo entorno disponible,
   configuración registrada; informar el cambio de código/prompt.
2. **NotebookLM vs TALOS:** documentar configuración conocida de ambos,
   material compartido, prompts y fecha. Si no puede igualarse, reportar como
   comparación de productos/ecológica, no causal.
3. **Repeticiones:** ejecutar varias corridas independientes con misma
   configuración para medir variabilidad de generación; definir cantidad y
   análisis antes de correr.
4. **Evaluación de salida:** para comparación ciega, anonimizar el sistema y
   aleatorizar orden. Mantener IDs de pares de pregunta sin revelar la
   identidad.
5. No ejecutar ninguna nueva corrida de benchmark ni usar estado real del
   estudiante hasta que el usuario la solicite/apruebe y se registren las
   condiciones. La preparación documental/offline sí puede avanzar.

#### F7.3 — Fijar métricas y umbrales antes de ver resultados

Usar la rúbrica de Fase 0 por dimensión: ajuste, exactitud, claridad,
profundidad pertinente, valor pedagógico, pertinencia de ciberseguridad y
fiabilidad. Para cada respuesta conservar nota, justificación y evidencia.

Antes de recoger nuevas salidas, preregistrar:

- métrica primaria y dimensiones secundarias;
- unidad de análisis (respuesta, conversación o participante);
- manejo de N/A, errores, respuestas truncadas y exclusiones;
- umbral de mejora mínima relevante;
- margen de no inferioridad para exactitud técnica y seguridad;
- número de casos/corridas y análisis de incertidumbre;
- regla para resolver discrepancias y detener la evaluación.

No fijar cifras arbitrarias sin conocer variación y volumen del benchmark.
Reportar medianas/distribuciones por dimensión, categoría e incidencia; no solo
promedio agregado. Para n pequeño, describir límites y evitar afirmaciones
estadísticas fuertes.

#### F7.4 — Puntuar con evaluadores y control de sesgo

1. Calibrar evaluadores con ejemplos ajenos al test ciego o con subconjunto
   piloto separado.
2. Tener dos evaluadores independientes cuando sea viable y conservar
   calificaciones originales.
3. Registrar acuerdo y adjudicación sin borrar desacuerdos.
4. Evaluar exactitud con criterios/fuentes verificables para detalles técnicos;
   fluidez o preferencia estética no sustituye verificación.
5. Informar conflictos de interés, límites del cegamiento y cualquier ítem
   donde la identidad del sistema sea inferible.

#### F7.5 — Evaluar aprendizaje por separado

Si se desea afirmar que TALOS mejora aprendizaje:

1. Definir resultados de aprendizaje específicos, prerrequisitos y prueba
   transferible que no repita literalmente el material practicado.
2. Usar evaluación previa, post inmediata y demorada con intervalo definido.
3. Diseñar asignación/contrabalanceo para evitar que aprender el tema con un
   sistema sesgue después al otro; no enseñar dos veces el mismo contenido al
   mismo participante en secuencia ingenua.
4. Controlar exposición, material, tiempo y apoyo; registrar pérdidas de
   seguimiento y datos faltantes.
5. Definir consentimiento, minimización, anonimización, retención y análisis
   antes de reclutar o usar datos.
6. No interpretar auto-reporte de confianza, likes o BKT como prueba suficiente
   de retención/transferencia.

Este subestudio no es requisito para desplegar una corrección de bug, pero sí
para la afirmación de que TALOS enseña mejor o causa mejores resultados de
aprendizaje.

#### F7.6 — Analizar, decidir y preservar el resultado

Producir un informe con:

- pregunta e hipótesis preregistradas;
- hashes/versiones de código, prompts, corpus y modelo, si disponibles;
- condiciones y metadatos faltantes;
- resultados por rúbrica/categoría y variabilidad;
- fallos operativos y respuestas excluidas con motivo;
- adjudicación, incertidumbre y limitaciones;
- decisión por fase: aceptar, iterar o revertir;
- cambios recomendados con trazabilidad a casos concretos.

No copiar las transcripciones originales al repositorio. Añadir solo agregados
no sensibles, citas mínimas necesarias o identificadores de casos anonimizados.

### Criterios de aceptación

- Set y rubric versionados antes de puntuar resultados.
- No se cambian enunciados canónicos silenciosamente ni se mezclan con
  variantes.
- Las métricas operativas y conceptuales se reportan por separado.
- Hay puntuación ciega, aleatorización y acuerdo de evaluadores según protocolo,
  o limitaciones explícitas si no fue viable.
- Umbral primario y no inferioridad de exactitud/seguridad están definidos antes
  de mirar resultados.
- No se afirma aprendizaje con solo un benchmark de respuestas.
- No se declara ganador general por una sola sesión o promedio que oculte
  fallos.
- Cualquier repetición real tuvo aprobación, configuración/metadatos y
  resguardo de privacidad.

### Decisión de salida

La Fase 7 produce una decisión basada en evidencia, no una aprobación
automática. Puede concluir “mejora en ajuste a síntesis, evidencia insuficiente
para aprendizaje”, “no inferior en exactitud con mejora de claridad”, “sin
mejora reproducible” o “inconcluso”. Si falla no inferioridad de exactitud o
seguridad, la candidata no debe promocionarse aunque mejore estilo o latencia.

## Cierre del programa y handoff entre LLMs

Al cerrar una fase, actualizar la tabla de dependencias y agregar un registro
con plantilla:

```text
Fase:
Estado: no iniciada / en curso / bloqueada / implementada / aceptada
Fecha:
Branch y commit base:
Archivos cambiados:
Decisión de diseño:
Pruebas ejecutadas (comandos exactos):
Resultados y warnings:
Evidencia revisada:
Áreas no inspeccionadas:
Riesgos/limitaciones conocidos:
Datos/servicios externos utilizados:
Confirmación de privacidad/perímetro:
Decisión de salida y siguiente fase:
Cambios sin commit / push:
```

El siguiente LLM debe abrir este documento y
[FASE0_LINEA_BASE_TALOS_NOTEBOOKLM.md](./FASE0_LINEA_BASE_TALOS_NOTEBOOKLM.md),
revisar estado Git y leer solo los archivos fuente/tests necesarios para la
fase activa. No repetir setup, no reconstruir desde cero la evidencia, no
ejecutar el benchmark con transcripciones locales ni asumir que una fase está
aceptada por la existencia de este plan. Si el handoff y el árbol de trabajo
discrepan, manda el árbol verificado; actualizar el handoff con la discrepancia.

### Registro de implementación

- Estado: implementada en el árbol de trabajo; aún sin commit.
- `structured_pipeline.py` ahora define `ResponseIntent`, separa tarea y
  modificadores explícitos, resuelve síntesis/negación/profundidad/formato,
  límites de frase/línea/palabras, código/no código, elementos solicitados y
  continuidad de ejercicio.
- La intención resuelta alimenta el modo de generación, el permiso efectivo de
  código y los prompts de usuario y de sistema cuando hay restricciones
  explícitas. El contrato prevalece sobre reglas generales de fase sin anular
  exactitud, seguridad ni requisitos de fuentes.
- Se eliminó una reasignación posterior que reemplazaba el modo resuelto por el
  clasificador anterior. La extracción estructural ya no vuelve a habilitar
  bloques C/Python/SQL si el usuario excluyó código.
- Las pruebas nuevas cubren síntesis, negación, límites, profundidad con
  restricción, formato tabla, código/no código, cierre socrático, ejercicio
  contextual y permiso de código en generación.
- Validación focalizada: `38 passed` en
  `tests/unit/pedagogy/test_adaptive_pipeline.py`,
  `tests/pedagogy/test_socratic_system_prompt.py`,
  `tests/pedagogy/test_chat_sse_endpoint.py` y
  `tests/pedagogy/test_structured_pipeline_phases.py`.
- La ejecución produjo cinco warnings deprecatorios relacionados con
  `FastAPI.on_event` y `starlette.testclient`.
- `git diff --check` pasó. Black y flake8 informan problemas de formato/líneas
  largas en el estilo preexistente de estos módulos; no se aplicó un formateo
  masivo ajeno a la tarea.
- No se llamó a proveedores externos, no se repitió el benchmark y no se tocó
  estado del estudiante.

## Estado de ejecución

El plan está guardado en un checkpoint local. La Fase 0 está completada como
línea de base; consultar
[FASE0_LINEA_BASE_TALOS_NOTEBOOKLM.md](./FASE0_LINEA_BASE_TALOS_NOTEBOOKLM.md)
para los hallazgos, límites y protocolo. No repetir setup ni lanzar otra
ejecución del benchmark sin solicitud explícita. Antes de continuar, comprobar
el estado actual de Git; no asumir que ramas o cambios descritos en handoffs
anteriores siguen vigentes. La Fase 1 está implementada y validada con las
pruebas focalizadas mencionadas; los cambios están sin commit y no hubo push.
Las Fases 2–7 tienen ahora diseño detallado en este documento; esto no significa
que estén implementadas, aprobadas para evaluación externa ni aceptadas.

### Snapshot de handoff verificado el 2026-09-28

- Branch observada: `main`; HEAD observado: `f1cf8f8`.
- Git reportó `main...origin/main [adelante 6]` en esa verificación. Es una
  observación puntual; volver a consultar remotos antes de cualquier operación
  de sincronización.
- Hay cambios locales sin commit en:
  - `docs/FASE0_LINEA_BASE_TALOS_NOTEBOOKLM.md` — actualización local de la
    evidencia de Fase 0.
  - `docs/PLAN_MEJORA_PEDAGOGICA_TALOS.md` — plan rector y handoff.
  - `src/study_engine/pedagogy/structured_pipeline.py` — implementación de
    Fase 1.
  - `tests/unit/pedagogy/test_adaptive_pipeline.py` — regresiones de Fase 1.
- No hubo commit ni push de estos cambios en el snapshot. No descartar, resetear
  ni sobrescribirlos al retomar; inspeccionar el diff actual porque puede haber
  cambiado.
- Siguiente acción segura: cerrar/revisar el diff de Fase 1 y sus documentos;
  no empezar una implementación de Fase 2 hasta que el árbol y el alcance se
  hayan revisado.
