# Plan de mejora pedagógica de TALOS

## Propósito y continuidad

Este documento conserva el diagnóstico, las decisiones y el plan de trabajo
para mejorar TALOS como tutor de estudio de ciberseguridad. Sirve como handoff
si la conversación se reinicia: antes de trabajar, leer este documento y
continuar desde la fase pendiente. **No repetir el setup del benchmark ni
reconstruir la comparación ya realizada.**

Fecha de elaboración: 2026-09-28.

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

- Reutilizar la clasificación de intención y el ensamblado existentes.
- Representar tarea, nivel, formato, extensión, profundidad, necesidad de
  ejemplo/código/ejercicio y posibles ambigüedades.
- Manejar negaciones y peticiones mixtas; no activar modos solo por palabras
  aisladas.
- Hacer que una restricción explícita de longitud gane a las plantillas
  generales, sin permitir que anule exactitud o seguridad.
- No forzar una pregunta socrática en respuestas donde contradiga el pedido.

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

## Plan detallado para la Fase 0

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

## Estado de ejecución

Este archivo documenta un plan, no acredita que la Fase 0 ya se haya
completado. Próximo paso: ejecutar F0.1–F0.6 con la evidencia local existente,
respetando el alcance y los criterios anteriores. Antes de hacerlo, comprobar
el estado actual de Git y del repositorio; no asumir que las ramas o cambios
descritos en handoffs anteriores siguen vigentes.
