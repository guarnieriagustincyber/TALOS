# Fase 0 — Línea de base TALOS vs NotebookLM

**Estado:** completada como línea de base y protocolo

**Fecha:** 2026-09-28
**Plan rector:** [Plan de mejora pedagógica de TALOS](./PLAN_MEJORA_PEDAGOGICA_TALOS.md)

## Propósito

Preparar una línea de base trazable para evaluar mejoras pedagógicas de TALOS.
Este documento registra evidencia existente y define cómo evaluarla. No ejecuta
otra sesión comparativa, no repite el setup del benchmark y no modifica prompts
ni comportamiento de producción.

## Evidencia existente e integridad

Los siguientes archivos están fuera del repositorio y no deben copiarse ni
subirse sin autorización:

| Evidencia | Ubicación local | Líneas | Bytes | SHA-256 |
|---|---|---:|---:|---|
| Transcripción TALOS | `/home/agustin/Escritorio/20TALOS.txt` | 1066 | 76101 | `90a3dbfba4b0696d4ec8f6cd8a2257db94efbab3d6583c2016e7b8cf65439628` |
| Transcripción NotebookLM | `/home/agustin/Escritorio/20NotebookLM.txt` | 1235 | 79539 | `51f4be987cc05a6e435d9687bd9ba7c2268669d09f795664ae6cc651085dfd78` |

Los hashes fijan la versión inspeccionada en esta Fase 0; no prueban por sí
solos la integridad del contenido antes de su recepción. Si cualquiera de los
archivos cambia, recalcular el hash y revisar qué versión se está evaluando.

El benchmark versionado existente es
[`benchmark_questions.json`](../benchmark/comparative_session/benchmark_questions.json),
SHA-256 `e7f715ba16936f03590aa54ea19900897e27609065e8d423a8eb1e495ea5c4c6`.
Especifica preguntas, categorías y comportamientos esperados, pero su texto no
coincide literalmente en todos los casos con la lista que el usuario confirmó
como la realmente utilizada. **La lista del usuario, guardada en el plan rector,
es la fuente autoritativa de los 20 enunciados del experimento.** No modificar
retroactivamente el JSON; registrar la discrepancia para mantener procedencia.

## Condiciones pedagógicas conocidas

- El usuario confirmó que se usaron las mismas 20 preguntas para ambos
  sistemas.
- NotebookLM recibió un prompt pedagógico personalizado, compartido por el
  usuario. Incluía, entre otras, estas instrucciones: no asumir conocimientos
  previos; explicar conceptos nuevos; guiar ejercicios sin entregar la solución
  completa por defecto; cambiar de analogía o escala cuando el estudiante no
  entiende; dar corrección estructurada; respetar el contenido de los libros; y
  no forzar la conexión con ciberseguridad.
- Ese prompt estaba dirigido a estudiar programación desde cero y prescribía
  pseudocódigo/Python para tareas concretas. No se debe tratar como una
  configuración neutral ni copiar literalmente todos esos formatos a TALOS.
- La existencia del prompt de NotebookLM no demuestra por sí sola causalidad en
  la diferencia observada; sí es una condición relevante que debe registrarse al
  interpretar la comparación.
- No se confirmó una configuración pedagógica equivalente para TALOS, ni
  versiones exactas de modelo, controles de generación, fuentes cargadas,
  latencias instrumentadas o logs técnicos completos. No inferir valores
  ausentes.

## Discrepancias de enunciado con el benchmark versionado

El usuario confirmó los enunciados canónicos en el
[plan rector](./PLAN_MEJORA_PEDAGOGICA_TALOS.md#preguntas-canónicas-del-benchmark).
El JSON de benchmark contiene variantes de redacción, entre ellas:

| Pregunta | Lista canónica del usuario | Variante en `benchmark_questions.json` |
|---|---|---|
| 7 | “Sí, hagamos el ejercicio.” | Añade “para comprobar si entendí qué es un proceso”. |
| 14 | Pregunta por 10 procesos “corriendo” y qué hace cada uno. | Pregunta por 10 procesos “listos para ejecutarse” y cuál usa el procesador. |
| 15 | Pregunta si un proceso “puede vivir sin programa”. | Pregunta si puede existir sin que el programa esté ejecutándose. |
| 17 | “Entonces, el thread es un proceso más pequeño, ¿no?” | “Entonces, ¿el thread es un proceso más pequeño?” |
| 20 | “¿Qué tema te parece que conviene estudiar ahora a partir de esto?” | Omite “te parece”. |

No asumir que esas variantes fueron las preguntas usadas. Alinear las respuestas
con los enunciados canónicos confirmados y anotar que algunas diferencias
pequeñas o grandes pueden afectar el comportamiento esperado, especialmente en
la pregunta 14.

## Matriz de correspondencia e integridad por pregunta

La lista canónica completa está en el plan rector para evitar duplicación. Esta
matriz debe registrar, sin puntuar calidad, qué respuesta conservan los logs y
si es posible cotejarla con el turno. No atribuir causas técnicas a un texto de
error o una anotación de demora sin logs de backend/proveedor.

| N.º | TALOS: estado del registro / localizador | NotebookLM: estado del registro / localizador | ¿Cotejable? / nota |
|---:|---|---|---|
| 1 | Líneas 1–10: completa; apertura de la unidad. | Líneas 1–34: completa; apertura de la unidad. | Correspondencia probable por orden/contenido. |
| 2 | Líneas 11–93: completa; explicación de proceso. | Líneas 35–133: completa; explicación de proceso. | Correspondencia probable por orden/contenido. |
| 3 | Líneas 94–126: completa; bloque “Validación Cognitiva y Cambio de Enfoque” y analogía del restaurante/mozo. | Líneas 134–186: completa; analogía “Partitura vs. Concierto en vivo”. | Ambas conservan una segunda analogía; TALOS no reproduce el prompt exacto, así que la atribución es por secuencia/contenido. |
| 4 | Líneas 127–202: bloque completo sobre sincronización/concurrencia. | Líneas 187–222: respuesta sobre importancia del concepto. | TALOS trata la importancia de sincronización, no queda claro que responda directamente a “¿Y eso por qué es importante?” referido al proceso; registrar alineación como incierta, no como error confirmado. |
| 5 | Líneas 203–293: completa; programa versus proceso. | Líneas 223–310: completa; programa versus proceso. | Correspondencia probable por orden/contenido. |
| 6 | Líneas 294–410: completa; ejemplo en C/`fork()`. | Líneas 311–429: completa; ejemplo en C/`fork()`. | Correspondencia por contenido. |
| 7 | Líneas 411–434: parcial; aparece ejercicio, no se localiza respuesta sustantiva al “Sí, hagamos el ejercicio”. | Líneas 430–506: completa; ejercicio de verificación. | NotebookLM deja ejercicio utilizable; TALOS, con este registro, no permite evaluar el seguimiento completo. |
| 8 | Líneas 435–445: error operativo explícito, API 500 y generación detenida. | Líneas 507–530: completa; corrige la confusión y propone reintento. | Resultado operativo TALOS frente a respuesta sustantiva NotebookLM; no es comparación de exactitud conceptual. |
| 9 | Líneas 446–493: completa; valida la comprensión. | Líneas 531–554: completa; verificación y consolidación. | Correspondencia probable por orden/contenido. |
| 10 | Líneas 494–570: completa; multiprogramación/planificación. | Líneas 555–661: completa; planificación de CPU. | Correspondencia probable por orden/contenido. |
| 11 | Líneas 571–648: completa; prerrequisitos de hardware. | Líneas 662–714: completa; hardware/kernel. | Correspondencia probable por orden/contenido. |
| 12 | Líneas 649–664: parcial/truncada; respuesta sobre memoria interrumpida. | Líneas 715–813: completa; memoria de procesos. | Comparación limitada por salida incompleta de TALOS. |
| 13 | Líneas 665–678: demora indicada como “más de 40 segundos”; no hay respuesta de una frase localizable. | Líneas 814–821: completa; responde en una frase (“Un proceso es la instancia activa de un programa en ejecución…”). | NotebookLM conserva respuesta sustantiva; TALOS no conserva una respuesta localizable. |
| 14 | Líneas 679–760: completa; elección entre procesos listos. | Líneas 822–901: completa; Round Robin/planificación. | Alineación de contenido; considerar wording canónico distinto del JSON. |
| 15 | Líneas 761–813: completa; responde sobre proceso/programa. | Líneas 902–984: completa; distinción proceso/programa. | Correspondencia probable; conservar el wording canónico del usuario. |
| 16 | Líneas 814–854: completa; proceso versus hilo. | Líneas 985–1093: completa; proceso versus hilo. | Correspondencia probable por orden/contenido. |
| 17 | Líneas 855–873: completa; corrige la idea de “proceso más pequeño”. | Líneas 1094–1119: completa; verificación de la misma misconception. | Correspondencia por contenido; conservar el wording canónico del usuario. |
| 18 | Líneas 874–966: completa; navegador multiproceso. | Líneas 1120–1199: completa; navegador multiproceso. | Correspondencia probable por orden/contenido. |
| 19 | Líneas 967–976: demora indicada como “más de 40 segundos”; resumen en cinco líneas no localizable. | Líneas 1200–1206: completa; presenta explícitamente un resumen numerado en cinco puntos. | NotebookLM conserva resumen sustantivo; TALOS no conserva una respuesta localizable. |
| 20 | Líneas 977–1066: no se localiza recomendación sustantiva de siguiente tema. | Líneas 1207–1235: completa; recomendación de siguiente paso. | TALOS no evaluable con el registro disponible; NotebookLM sí conserva recomendación. |

Los rangos y la descripción se refieren a las copias identificadas por hash en
esta línea de base. La asociación se hizo por orden y contenido, no por
numeración ciega: en TALOS hay un desplazamiento/ausencia de turno, y los logs
no reproducen siempre el enunciado del usuario. El usuario confirmó que el
texto de las preguntas originales fue idéntico entre sistemas; esto no elimina
las limitaciones del registro de respuestas.

Estados permitidos: `respuesta completa`, `parcial/truncada`, `error
operativo`, `demora sin respuesta sustantiva`, `turno contextual`, `no
localizable`, `no evaluable con el registro disponible`. Un error operativo
cuenta como resultado de fiabilidad, no como evidencia de calidad conceptual de
una respuesta que no fue entregada.

## Taxonomía del benchmark

Las preguntas canónicas cubren, al menos, estas funciones pedagógicas:

| N.º | Función principal |
|---:|---|
| 1 | Inicio en frío / orientación a la unidad |
| 2 | Introducción conceptual |
| 3 | Manejo de confusión / segunda explicación |
| 4 | Seguimiento deíctico / relevancia |
| 5 | Comparación conceptual |
| 6 | Solicitud explícita de código |
| 7 | Aceptación de ejercicio / continuidad |
| 8 | Corrección de concepción errónea |
| 9 | Consolidación de respuesta correcta |
| 10 | Explicación de mecanismo en contexto |
| 11 | Detección de prerrequisitos |
| 12 | Pregunta ambigua sobre memoria en contexto |
| 13 | Restricción estricta a una frase |
| 14 | Planificación con wording canónico del usuario |
| 15 | Seguimiento retrospectivo / distinción programa-proceso |
| 16 | Comparación proceso-thread |
| 17 | Reparación de misconception |
| 18 | Transferencia a caso real (navegador multiproceso) |
| 19 | Síntesis con límite de cinco líneas |
| 20 | Recomendación del siguiente tema sin sobreinferir progreso |

## Rúbrica propuesta para futuras evaluaciones

Escala ordinal 1–5. Puntuar por dimensión y acompañar cada nota con evidencia;
no convertir el promedio en “ganador” sin reportar distribución y limitaciones.
Usar `N/A` cuando la dimensión no aplique a la tarea.

| Dimensión | 1 — Deficiente | 3 — Adecuado | 5 — Excelente |
|---|---|---|---|
| Ajuste al pedido | No responde o contradice la tarea/formato. | Responde el núcleo con desvíos menores. | Responde directamente y respeta tarea, formato, longitud y nivel. |
| Exactitud técnica | Error central o afirmación engañosa. | Núcleo correcto, con omisiones o matices pendientes. | Correcta, contextualizada y con límites relevantes explícitos. |
| Claridad | Difícil de seguir; conceptos clave sin explicar. | Comprensible y razonablemente ordenada. | Progresión lógica, foco y términos necesarios claros. |
| Profundidad pertinente | Insuficiente o sobrecargada para el pedido. | Nivel utilizable, aunque con alguna capa faltante/excedente. | Profundidad alineada al objetivo; distingue núcleo de extensión. |
| Valor pedagógico | No promueve comprensión o aplicación. | Explicación/ejemplo/feedback útil pero mejorable. | Ayuda a razonar, aplicar o corregir de manera específica. |
| Pertinencia de ciberseguridad | Conexión errónea o forzada cuando se incluye. | Vínculo adecuado pero general, o se omite bien cuando no aplica. | Vínculo preciso y orgánico, con alcance bien contextualizado. |
| Fiabilidad observable | Error, truncamiento o salida no utilizable. | Utilizable con incidencia menor. | Completa, sin incidencia visible y coherente con la salida final. |

Reglas de uso:

- Puntuar aparte operación y contenido. Si no hubo respuesta por error, marcar
  fiabilidad como fallo y calidad conceptual como `N/A`.
- No premiar longitud, jerga, secciones, analogías ni comandos por su mera
  presencia.
- Para preguntas con límite explícito, evaluar el cumplimiento del límite bajo
  ajuste al pedido.
- Las puntuaciones retrospectivas a los logs existentes son exploratorias:
  no asignarlas a ciegas ni inventar condiciones que no se registraron.

## Plantilla de metadatos para futuras corridas

```text
run_id:
fecha_hora_y_zona:
sistema/producto:
modelo_y_version (si disponible):
version/hash_prompt:
version/hash_codigo (TALOS):
prompt_exacto_del_usuario:
fuentes_disponibles_y_seleccionadas:
configuracion_conocida:
salida_completa_visible:
latencia_total / tiempo_al_primer_token:
finish_reason / tokens (si disponible):
estado_streaming:
errores_proveedor-backend-frontend:
incluida_o_excluida_de_evaluacion_y_motivo:
datos_no_disponibles:
```

No registrar secretos, credenciales, identificadores personales innecesarios,
estado BKT privado ni contenido interno del modelo. Cuando un dato no esté
disponible, escribir `no disponible`; nunca reconstruirlo como si hubiera sido
medido.

## Protocolo de puntuación

1. Acordar la versión de la rúbrica y criterios de respuesta antes de puntuar.
2. Para futuras corridas, anonimizar la identidad del sistema y aleatorizar
   orden; mantener los pares de pregunta comparables.
3. Hacer una calibración entre evaluadores en casos piloto y documentar
   cualquier cambio de definición antes de evaluar el resto.
4. Usar dos evaluadores cuando sea viable; conservar sus puntuaciones
   independientes y resolver discrepancias con nota.
5. Reportar dimensión y categoría, promedio/mediana según corresponda,
   dispersión, tasa de incidencias y casos excluidos.
6. Separar calidad de respuesta de aprendizaje efectivo. Este benchmark de
   logs mide la primera; afirmar aprendizaje requiere pruebas pre/post/demoradas
   y tareas de transferencia.
7. Fijar por adelantado el umbral de mejora y la no inferioridad aceptable de
   exactitud y seguridad.

## Prompt pedagógico de NotebookLM compartido por el usuario

Se conserva aquí el prompt completo que el usuario pegó en la conversación, para
que el contexto metodológico no dependa solo del historial del chat. Su inclusión
no implica que TALOS deba copiarlo literalmente; fue escrito para programación
desde cero.

```text
Actuá como mi tutor socrático de programación y pensamiento algorítmico.

Mi objetivo es aprender programación desde cero para luego orientarme a ciberseguridad, pero no quiero que fuerces la conexión con ciberseguridad en todo momento. Quiero una base sólida de programación, lógica y algoritmos.

Estoy estudiando principalmente con:
1. "Fundamentos de Programación" de Luis Joyanes Aguilar.
2. "Piensa como un programador" de V. Anton Spraul.
3. "Book of Proof" de Richard Hammack, solo cuando haga falta matemática discreta o lógica.

Tu trabajo no es darme respuestas cerradas ni código completo de entrada. Tu trabajo es enseñarme a pensar.

REGLAS PRINCIPALES:

1. No asumas conocimiento previo.
   Si usás un concepto nuevo, primero explicalo de forma simple.
   Si yo no lo conozco, frená y explicalo antes de continuar.

2. No sintetices en exceso.
   Prefiero una explicación clara, paso a paso, antes que un resumen demasiado compacto.
   Si un concepto requiere tres pasos, explicame los tres pasos.

3. No inventes contenido del libro.
   Si no tenés acceso exacto a una sección, decilo claramente.
   No alucines ejemplos, páginas o definiciones exactas.
   Si necesitás un fragmento del libro, pedímelo.

4. Primero pseudocódigo, después Python.
   Cuando trabajemos ejercicios, primero pensamos el algoritmo en pseudocódigo o español estructurado.
   Después lo traducimos a Python.

5. No me des la solución completa de un ejercicio si estoy aprendiendo.
   Guiame con preguntas, pasos pequeños y verificaciones.
   Solo darme la solución completa si yo digo explícitamente:
   "DAME LA SOLUCIÓN COMPLETA".

6. Explicaciones prácticas.
   Siempre que puedas, usá:
   - Una analogía simple.
   - Una definición clara.
   - Un ejemplo en pseudocódigo.
   - Un ejemplo en Python.
   - Una pregunta para verificar si entendí.

7. Conexión con ciberseguridad solo cuando sea orgánica.
   No fuerces la relación con ciberseguridad si no viene al caso.
   Si el tema tiene relación natural, mencionarlo brevemente.

8. Metodología de estudio.
   Vamos a trabajar por capítulos y puntos.
   Primero te puedo pedir un resumen contextual de un capítulo.
   Después vamos punto por punto, con ejercicios o desarrollo práctico.

FORMATOS DE SALIDA QUE DEBÉS USAR:

Cuando yo diga:
"RESUMEN CAPÍTULO X"

Tu salida debe ser:

MAPA DE CAPÍTULO
- Título del capítulo.
- Idea principal del capítulo.
- Qué conceptos son fundamentales.
- Qué cosas son cultura general y se pueden leer rápido.
- Qué puntos conviene marcar para practicar después.
- Analogía principal para entender el capítulo.
- Conexión con programación general, si existe.
- Conexión con ciberseguridad, solo si es natural.

Cuando yo diga:
"LEÍ EL CAPÍTULO, EMPECEMOS CON EL PUNTO X.Y"

Tu salida debe ser:

EXPLICACIÓN DEL PUNTO
1. ¿Qué es este punto?
2. ¿Por qué importa?
3. Explicación simple sin asumir conocimiento.
4. Analogía.
5. Ejemplo en pseudocódigo.
6. Ejemplo en Python.
7. Error común de principiante.
8. Pregunta para verificar si entendí.

Cuando yo diga:
"DAME UN EJERCICIO"

Tu salida debe ser:

EJERCICIO GUIADO
1. Enunciado del ejercicio.
2. Análisis del problema.
3. Entradas esperadas.
4. Salidas esperadas.
5. Restricciones.
6. Primer paso en pseudocódigo.
7. Pregunta para que yo continúe.

No resuelvas todo el ejercicio salvo que yo lo pida explícitamente.

Cuando yo responda un ejercicio, corregime así:

VERIFICACIÓN
- ¿Qué está bien?
- ¿Qué está incompleto o mal?
- ¿Qué concepto faltó?
- ¿Cómo lo pensamos paso a paso?
- ¿Cuál sería el siguiente paso mínimo?
- Si hay error, no me des la solución completa: dame una pista concreta.

Cuando yo diga:
"TRADUCÍ ESTO A PYTHON"

Tu salida debe ser:

TRADUCCIÓN A PYTHON
1. Pseudocódigo original.
2. Explicación de la traducción.
3. Código Python.
4. Cómo probarlo.
5. Qué cambiaría si la entrada fuera inválida.

Cuando yo diga:
"EXPLICÁ COMO SI NO SUPIERA NADA"

Tu salida debe ser:

EXPLICACIÓN DESDE CERO
- Definición simple.
- Analogía cotidiana.
- Ejemplo mínimo.
- Palabras clave explicadas.
- Error común.
- Pregunta de verificación.

Cuando yo diga:
"NO ENTENDÍ"

No repitas exactamente lo mismo.
Cambiar el enfoque:
- Usá otra analogía.
- Dividí el problema en partes más chicas.
- Mostrá un ejemplo más simple.
- Hacé una pregunta para detectar dónde me trabé.

ESTILO DE ENSEÑANZA:

Sé claro, paciente y práctico.
Usa español rioplatense si es natural.
No seas excesivamente académico.
Priorizá que yo entienda el razonamiento, no que memorice.

Cuando estemos trabajando con Joyanes, respetá su enfoque de:
- Análisis del problema.
- Diseño del algoritmo.
- Codificación.
- Prueba/verificación.
- Documentación/mantenimiento.

Cuando estemos trabajando con "Piensa como un programador", reforzá:
- Tener un plan.
- Replantear el problema.
- Dividir el problema.
- Empezar con lo que sé.
- Reducir el problema.
- Buscar analogías.
- No frustrarse.

Cuando estemos trabajando con Hammack, usalo solo para:
- Lógica.
- Conjuntos.
- Funciones.
- Inducción.
- Demostraciones simples.
- Base matemática para algoritmos.

ANTI-ERRORES:

No digas "esto es fácil" si puede ser difícil para principiante.
No saltees pasos.
No asumas que sé qué es una variable, función, bucle, array, objeto, memoria, compilador o pseudocódigo si todavía no quedó claro.
No uses jerga sin explicarla.
No me des una solución avanzada si todavía no tengo la base.
No resumas tanto que pierda el razonamiento.

SIEMPRE que te pida trabajar un concepto de programación, empezá por la idea conceptual antes de darme código.

Para comenzar, preguntame:
"¿Con qué libro, capítulo y punto querés arrancar?"

(estoy estudiando para ciberseguridad, el roadmap.txt es mi meta)
```

## Observaciones, inferencias y desconocidos

### Observaciones documentadas

- El usuario confirmó que los enunciados fueron iguales entre sistemas y
  proporcionó su texto canónico.
- Existe un prompt pedagógico personalizado para NotebookLM, compartido por el
  usuario.
- El benchmark de repositorio contiene variaciones de wording frente a la lista
  canónica.
- Se tienen dos archivos de transcript locales con los hashes y tamaños arriba.

### Inferencias razonables, no causales

- El prompt de NotebookLM probablemente influyó en estilo y estructura, pero
  esta comparación no permite aislar cuánto corresponde al prompt, modelo,
  interfaz o fuentes.
- Las notas de errores y demoras son evidencia de problemas observados en esa
  ejecución; por sí solas no identifican la causa raíz.

### Datos ausentes que no se deben inventar

- Modelo/versiones exactas de ambos sistemas, salvo que aparezcan verificables
  en la evidencia local.
- Parámetros de generación, tiempos instrumentados y finish reason.
- Igualdad de fuentes o materiales efectivamente disponibles en ambas
  interfaces.
- Evaluación independiente o puntuación previa a la Fase 0.

## Progreso y criterios de salida

- [x] Punto de control local del plan creado antes de iniciar esta fase.
- [x] Lista canónica de 20 preguntas capturada desde el usuario.
- [x] Disponibilidad, longitud, tamaño y hashes de ambos transcripts
      registrados sin copiarlos al repositorio.
- [x] Benchmark versionado inspeccionado; detectadas diferencias de wording.
- [x] Rúbrica, taxonomía, plantilla de metadatos y protocolo documentados.
- [x] Cotejo por contenido/orden de los 20 turnos en ambos transcripts, con
      localizadores y estados de integridad.
- [x] Revisión de privacidad: solo se conservaron rangos de línea, estados y
      fragmentos breves no identificatorios; los transcripts permanecen fuera
      del repositorio.
- [x] Observaciones, inferencias y datos no disponibles separados explícitamente.
- [x] No se modificaron prompts ni se repitió el benchmark.
- [x] Fase 0 completada como línea de base e instrumento de evaluación; no se
      asignaron puntajes retrospectivos.

**Resultado:** la matriz registra 14 respuestas TALOS completas localizables,
2 parciales, 3 incidencias operativas/demoras y 1 respuesta no localizable.
Para NotebookLM registra respuestas sustantivas completas en los 20 ítems
localizados por contenido/orden. En TALOS, la alineación semántica de la fila 4
queda incierta, y la matriz declara expresamente esa limitación. Esto describe
integridad del registro, **no** es una puntuación de calidad ni demuestra por sí
solo superioridad general. Los puntajes retrospectivos quedan sin asignar
porque el protocolo se definió después de la prueba y los transcripts no
documentan todas las condiciones.
