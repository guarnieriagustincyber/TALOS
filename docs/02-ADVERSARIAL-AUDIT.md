DOCUMENTO 2 — ESPECIFICACIÓN TÉCNICA V1.0
Study Engine — Sistema Personal de Aprendizaje Basado en Evidencia

Estado: V1.0 — Especificación congelada
Tipo: Technical Specification / Engineering Contract
Objetivo: definir exactamente qué se construye, cómo funciona, cómo se valida y cuándo un componente puede considerarse terminado.

1. Propósito

El sistema tiene como objetivo construir un entorno personal de aprendizaje asistido por IA, capaz de convertir un conjunto de fuentes educativas —libros, PDFs, apuntes, programas analíticos y documentación— en un sistema estructurado de estudio.

El sistema debe permitir:

organizar conocimiento;
determinar una secuencia de estudio;
conversar sobre las fuentes;
explicar conceptos con profundidad;
comparar fuentes;
detectar prerequisitos;
generar ejercicios;
evaluar respuestas;
evaluar ejercicios;
detectar debilidades;
adaptar la dificultad;
registrar progreso;
mantener trazabilidad hacia las fuentes;
y utilizar el mismo conocimiento tanto para enseñar como para evaluar.

La IA no reemplaza el proceso intelectual del estudiante.

El sistema debe facilitar el aprendizaje, no automatizarlo.

2. Problema que resuelve

El problema principal no es la falta de información.

Es la fricción cognitiva y organizativa causada por exceso de información.

Por ejemplo, para aprender ciberseguridad pueden existir simultáneamente:

un roadmap;
libros;
documentación;
materias universitarias;
programas analíticos;
apuntes;
ejercicios;
estándares;
documentación técnica;
material complementario.

El estudiante debe decidir constantemente:

qué estudiar → en qué orden → con qué fuente → cuánto profundizar → qué prerequisitos faltan → qué practicar → cómo comprobar si realmente entendió.

El Study Engine debe asumir esa orquestación pedagógica, sin asumir el aprendizaje mismo.

3. Principio rector
Deterministic First → AI Second

Toda tarea que pueda resolverse determinísticamente debe resolverse mediante software determinista.

La IA se utiliza únicamente cuando aporta capacidades como:

comprensión lingüística;
explicación;
comparación;
contextualización;
generación de preguntas;
evaluación conceptual;
interpretación;
razonamiento.

El sistema nunca debe delegar en un LLM:

memoria;
recuperación de documentos;
orden estructural del roadmap;
ejecución de código;
decisión automática de avance;
validación determinista de resultados.
4. Arquitectura conceptual

El sistema se divide en seis capas:

┌──────────────────────────────────────────────┐
│              INTERFAZ DE ESTUDIO             │
│                    CHAT                      │
├──────────────────────────────────────────────┤
│          MODOS PEDAGÓGICOS / AGENTES         │
│ Tutor · Planificador · Tester · Auditor     │
├──────────────────────────────────────────────┤
│              CONTEXT ENGINE                  │
│ Context Packer + Student State + Contracts  │
├──────────────────────────────────────────────┤
│                RAG ENGINE                    │
│ Retrieval + Ranking + Evidence              │
├──────────────────────────────────────────────┤
│             KNOWLEDGE LAYER                  │
│ Libros · PDFs · Roadmaps · Materias         │
├──────────────────────────────────────────────┤
│          DETERMINISTIC ENGINE                │
│ Python · pytest · schemas · validators      │
└──────────────────────────────────────────────┘
5. Concepto fundamental: Cuaderno

El sistema no tendrá una única gigantesca base de conocimiento.

La unidad organizativa principal será el:

Notebook

Un Notebook representa un dominio de aprendizaje independiente.

Ejemplos:

Ciberdefensa
Programación
Matemática
Redes
Sistemas Operativos
Materia_X
Materia_Y

Cada Notebook puede contener:

roadmap;
libros;
PDFs;
documentación;
ejercicios;
programa analítico;
estado del estudiante;
configuración pedagógica.

Esto permite escalar el sistema a distintas materias sin mezclar conocimiento.

6. Roadmap: autoridad estructural

El roadmap es la raíz estructural del aprendizaje.

No es simplemente otro PDF.

Define:

fases;
módulos;
submódulos;
secuencia;
dependencias;
objetivos;
competencias;
gateways.

El sistema debe tratarlo como:

STRUCTURAL AUTHORITY

pero no como autoridad absoluta de conocimiento.

Esto es fundamental.

El roadmap responde:

"¿Qué debería estudiar y en qué estructura?"

Las fuentes responden:

"¿Qué debo aprender sobre ese tema?"

7. Jerarquía de fuentes

Cada fuente posee un rol.

Ejemplo:

source:
  id: joyanes
  role: primary_learning_source
  priority: 100

Otra:

source:
  id: spraul
  role: conceptual_complement
  priority: 80

Otra:

source:
  id: clean_code
  role: engineering_complement
  priority: 60

La prioridad no significa:

"Joyanes siempre tiene razón."

Significa:

"Para esta función pedagógica concreta, esta fuente tiene mayor peso."

8. Principio de selección de fuentes

El sistema no debe quedar ciego ante un único autor.

El director pedagógico debe poder detectar:

"La fuente principal cubre este concepto, pero existe una laguna."

Y recomendar:

FUENTE ADICIONAL RECOMENDADA

Concepto:
Recursión

Problema detectado:
La fuente principal presenta la definición,
pero no desarrolla suficientemente:

- casos base;
- profundidad de llamada;
- análisis de complejidad.

Fuente disponible:
Spraul

Acción:
Utilizar Spraul como complemento.

Estado:
COMPLEMENTARY_SOURCE

Si ninguna fuente existente cubre suficientemente el concepto:

FUENTE FALTANTE

No existe evidencia suficiente en el corpus actual.

Recomendación:
Agregar una fuente especializada.

Motivo:
El concepto requiere profundidad adicional.

Esto es una función central del sistema, no un accesorio.

9. Modelo de conocimiento

Cada documento ingerido debe conservar, cuando sea posible:

document_id
title
author
language
source_role
priority
chapter
section
page
chunk_id
content

La metadata incompleta es válida.

No se bloqueará una fuente porque no pueda determinarse perfectamente:

capítulo;
sección;
página;
etc.

La fidelidad se prioriza sobre la perfección artificial de metadata.

10. Motor RAG

El RAG debe trabajar en varias etapas:

Pregunta
   ↓
Interpretación
   ↓
Identificación del Notebook
   ↓
Identificación del tema
   ↓
Retrieval
   ↓
Ranking
   ↓
Selección de evidencia
   ↓
Context Pack
   ↓
LLM
   ↓
Output Validator
11. Retrieval

La V1 debe priorizar:

Búsqueda semántica

Para encontrar conceptos equivalentes aunque utilicen palabras diferentes.

Búsqueda léxica

Para encontrar:

términos exactos;
funciones;
nombres;
sintaxis;
conceptos específicos.
Ranking por prioridad

La relevancia final debe considerar también el rol de la fuente.

Conceptualmente:

FinalScore =
    semantic_score
    + lexical_score
    + source_priority
    + topic_relevance

No se confiará exclusivamente en embeddings.

12. Evidencia

Toda respuesta relacionada con conocimiento documental debe poder clasificarse.

Estados V1:

[SUPPORTED]
[PARTIALLY_SUPPORTED]
[COMPLEMENT]
[NO_EVIDENCE]
SUPPORTED

La afirmación está directamente respaldada.

PARTIALLY_SUPPORTED

La fuente respalda solamente una parte.

COMPLEMENT

La información proviene de una fuente secundaria/complementaria.

NO_EVIDENCE

No existe evidencia suficiente en el corpus.

13. Regla de abstención

El sistema debe preferir decir "no tengo evidencia suficiente" antes que completar un hueco mediante conocimiento general no solicitado.

Esto es especialmente importante para:

definiciones;
procedimientos;
afirmaciones técnicas;
comparación de autores;
evaluación de respuestas.
14. Context Packer

El LLM será tratado como stateless.

Por lo tanto:

Si algo no está incluido en el contexto enviado, para el modelo no existe.

Python construirá el contexto.

Ejemplo conceptual:

<context>

  <roadmap>
    ...
  </roadmap>

  <current_topic>
    ...
  </current_topic>

  <prerequisites>
    ...
  </prerequisites>

  <evidence>
    ...
  </evidence>

  <source_hierarchy>
    ...
  </source_hierarchy>

  <student_state>
    ...
  </student_state>

  <mode_contract>
    ...
  </mode_contract>

</context>

La IA no decide qué documentos recuperar.

El sistema los recupera y se los entrega.

15. Modos pedagógicos

La interfaz debe comportarse como un chat normal.

El usuario no necesita trabajar desde consola para estudiar.

La consola queda para:

administración;
debugging;
desarrollo;
ejecución de tests;
herramientas de ingeniería.

La experiencia cotidiana será:

┌───────────────────────────────────────┐
│ Notebook: Programación                │
│ Modo: Tutor                           │
├───────────────────────────────────────┤
│                                       │
│ Usuario: No entiendo qué es una      │
│ función.                              │
│                                       │
│ Tutor: ...                            │
│                                       │
├───────────────────────────────────────┤
│ Escribí tu pregunta...               │
└───────────────────────────────────────┘
16. Tutor

El Tutor debe:

explicar;
profundizar;
comparar;
utilizar analogías;
generar ejemplos;
detectar prerequisitos;
hacer preguntas;
adaptar la explicación;
mantener el tema actual;
citar evidencia.

No debe:

resumir excesivamente;
asumir conocimientos;
inventar contenido;
saltarse prerequisitos;
resolver automáticamente ejercicios pedagógicos.
17. Director / Planner

Este es uno de los componentes más importantes.

Su función es transformar:

ROADMAP
+
FUENTES
+
PREREQUISITOS
+
ESTADO DEL ESTUDIANTE

en:

PLAN DE ESTUDIO

Ejemplo:

FASE 0
 └── Módulo 1
      ├── 1.1 Variables
      │    ├── prerequisito: ninguno
      │    └── estado: dominado
      │
      ├── 1.2 Tipos de datos
      │    ├── prerequisito: variables
      │    └── estado: en progreso
      │
      └── 1.3 Estructuras
           ├── prerequisito: tipos
           └── bloqueado
18. Director y múltiples fuentes

El Director debe poder decidir:

Caso A

La fuente principal alcanza.

→ continuar.

Caso B

La fuente principal necesita complemento.

→ utilizar otra fuente existente.

Caso C

Las fuentes disponibles no alcanzan.

→ recomendar nueva fuente.

Caso D

Hay contradicción.

→ presentar la contradicción.

Nunca debe ocultarla.

19. Tester

El Tester comparte exactamente la misma base documental.

Pero cambia el comportamiento pedagógico.

Flujo:

Tema actual
     ↓
Conocimiento recuperado
     ↓
Estado del estudiante
     ↓
Pregunta
     ↓
Respuesta
     ↓
Evaluación
     ↓
Debilidad
     ↓
Nueva pregunta

Debe poder:

generar preguntas;
generar ejercicios;
evaluar respuestas;
detectar errores conceptuales;
detectar razonamiento superficial;
aumentar dificultad;
reducir dificultad;
generar casos límite;
detectar prerequisitos faltantes;
registrar debilidades.
20. Regla socrática

El Tester no debe convertirse en solucionador.

Si el estudiante falla:

ERROR
 ↓
PISTA
 ↓
NUEVO INTENTO
 ↓
EVALUACIÓN

No:

ERROR
 ↓
SOLUCIÓN COMPLETA

salvo solicitud explícita.

21. Evaluación

La evaluación debe medir más que una respuesta correcta.

Se deben poder distinguir:

Memorización
Comprensión
Aplicación
Razonamiento
Transferencia

Por ejemplo:

"Definí una lista."

es insuficiente para demostrar dominio.

El sistema debería eventualmente poder preguntar:

"¿Qué ocurriría si...?"

o:

"Aplicá este concepto a un problema que no sea idéntico al ejemplo."

Esto evita confundir reconocimiento con dominio.

22. Estado del estudiante

El sistema mantendrá un estado estructurado.

Ejemplo:

topic: estructuras_de_datos

status: developing

confidence: medium

strengths:
  - listas
  - recorridos

weaknesses:
  - complejidad
  - casos límite

recurring_errors:
  - confunde índice con valor

last_evaluated:
  ...

recommended_action:
  - reinforcement

Este estado será generado/modificado mediante reglas controladas.

El LLM no posee memoria libre.

23. Código: Deterministic Layer

Cuando el aprendizaje incluya programación:

Student Code
     ↓
pytest
     ↓
resultado determinista
     ↓
Tester

El LLM nunca determina:

"tu código funciona".

Python lo determina.

La IA puede interpretar:

"Tu solución funciona para estos casos, pero conceptualmente presenta este problema."

24. VS Code

VS Code seguirá siendo deliberadamente manual.

No se busca convertirlo en Cursor.

El estudiante:

escribe;
piensa;
ejecuta;
depura.

El Study Engine puede recibir:

código
+
tests
+
resultado pytest
+
tema
+
evidencia documental

y realizar la evaluación.

Pero no editará automáticamente el código del estudiante en V1.

25. Context Packer del laboratorio

El paquete podrá contener:

<laboratory>

  <exercise>
  ...
  </exercise>

  <student_code>
  ...
  </student_code>

  <tests>
  ...
  </tests>

  <pytest_result>
  ...
  </pytest_result>

  <student_state>
  ...
  </student_state>

</laboratory>

Esto permite que el Tester razone sobre evidencia real.

26. Quality Engineering

Todo componente del sistema debe pasar por un Quality Gate antes de ser considerado terminado.

No existe:

"funciona en mi PC".

Existe:

"cumple su contrato".

27. Tipos de pruebas

Cada subsistema debe tener, cuando corresponda:

Unit tests

Componentes individuales.

Integration tests

Interacción entre componentes.

Contract tests

Validación de interfaces y schemas.

Regression tests

Evitar que una corrección rompa algo anterior.

Failure tests

Comportamiento ante errores.

Edge-case tests

Casos extremos.

Security tests

Como mínimo:

secrets;
validación de entradas;
aislamiento;
fuga accidental de información.
Performance tests

Como métrica, no necesariamente como hard gate.

RAG benchmark

Medición de recuperación y grounding.

28. Protected Tests

Existirá una categoría:

tests/protected/

Estos tests no podrán modificarse silenciosamente para hacer pasar el sistema.

El mecanismo de protección será determinista mediante:

Git;
hooks;
checks;
checksum o mecanismo equivalente.

La regla es:

Un fallo debe resolverse en el producto, no en el juez.

29. Debug Agent

Cuando un subsistema falle, el agente de ingeniería podrá:

leer el error;
investigar el origen;
inspeccionar el código;
reproducir el problema;
formular hipótesis;
aplicar una corrección;
ejecutar tests;
analizar regresiones;
repetir.

Pero:

no puede declarar el subsistema aprobado.

El agente ejecuta la reparación.

El Quality Gate determina la certificación.

30. Criterio de certificación

No habrá:

"92% de calidad".

La V1 utilizará:

HARD GATES

Todos deben pasar.

Unit tests             PASS
Integration tests      PASS
Contract tests         PASS
Protected tests        PASS
Regression tests       PASS
Critical security      PASS
Schema validation      PASS

Si uno falla:

NOT CERTIFIED
31. Soft Metrics

Se podrán registrar:

coverage;
latencia;
consumo RAM;
tokens;
coste;
retrieval rate;
grounding;
benchmark pedagógico.

Pero una métrica promedio nunca puede ocultar un hard failure.

32. K-RAG Benchmark

Antes de confiar en el RAG:

30–50 preguntas reales

creadas manualmente.

Cada pregunta tendrá:

question:
expected_source:
expected_topic:
expected_evidence:
acceptable_answer:
forbidden_claims:

El benchmark funcionará como oráculo externo.

El propio sistema no decide unilateralmente que su RAG es bueno.

33. Benchmark por capas

Primero:

Question
 ↓
Retrieval
 ↓
¿Encontró evidencia correcta?

Después:

Question
 ↓
Retrieval
 ↓
LLM
 ↓
Answer
 ↓
¿Grounded?

Y finalmente:

¿La respuesta además es pedagógicamente correcta?

Esto permite identificar dónde está el fallo.

34. Manejo de contradicciones

Si dos fuentes contradicen una afirmación:

SOURCE A
"X"

SOURCE B
"Y"

CONFLICT DETECTED

El sistema no debe fusionarlas arbitrariamente.

Debe:

identificar la contradicción;
citar ambas fuentes;
explicar el contexto;
indicar cuál tiene prioridad para el objetivo actual, si corresponde;
dejar visible la diferencia.
35. Materias universitarias

Los PDFs de las materias tendrán su propio espacio dentro del Notebook correspondiente.

Por ejemplo:

CIBERDEFENSA
│
├── ROADMAP
│
├── FASE 0
│   ├── Joyanes
│   ├── Spraul
│   └── ...
│
└── UNIVERSIDAD
    ├── Materia 1
    │   ├── Programa analítico
    │   ├── Clase 01
    │   ├── Clase 02
    │   └── Bibliografía
    │
    └── Materia 2
        ├── Programa analítico
        └── Clases

El programa analítico puede actuar como estructura local de esa materia.

El roadmap general continúa siendo la estructura superior cuando corresponda.

36. Separación pedagógica

El sistema debe distinguir:

ROADMAP
↓
qué estudiar

PROGRAMA ANALÍTICO
↓
qué exige la materia

LIBROS
↓
conocimiento profundo

APUNTES / CLASES
↓
contexto académico

EJERCICIOS
↓
aplicación

STUDENT STATE
↓
qué domina el estudiante

Esta separación evita convertir todos los documentos en una sopa documental.

37. Interfaz V1

La interfaz principal debe ofrecer conceptualmente:

┌─────────────────────────────────────┐
│ LIBROS / FUENTES                    │
├─────────────────────────────────────┤
│ CUADERNOS                           │
├─────────────────────────────────────┤
│ PLAN DE ESTUDIO                     │
├─────────────────────────────────────┤
│ MODOS                               │
│  • Tutor                            │
│  • Tester                           │
│  • Director                         │
├─────────────────────────────────────┤
│ CHAT                                │
│                                     │
│                                     │
└─────────────────────────────────────┘

La consola no será la interfaz de estudio.

38. Formato de salida

El sistema deberá poder renderizar:

Markdown;
tablas;
listas;
bloques de código;
pseudocódigo;
LaTeX;
ecuaciones;
citas;
metadata de evidencia.

Por lo tanto, sí:

Las explicaciones matemáticas podrán verse en LaTeX.

Ejemplo:

$$ O(n) $$

o:

$$ T(n)=T(n-1)+O(1) $$

La interfaz será responsable de renderizarlo correctamente.

39. Qué NO entra en V1

Queda explícitamente fuera:

aplicación móvil;
sistema multiusuario;
SaaS;
marketplace;
monetización;
multi-agent complejo;
autonomía total;
modificación automática del código;
Obsidian como integración activa;
automatización profunda de AppFlowy;
entrenamiento de modelos;
fine-tuning;
infraestructura cloud propia;
sistema de producción empresarial.
40. Obsidian

No forma parte del producto V1.

Pero V1 debe producir datos suficientemente estructurados para que posteriormente pueda existir:

Study Engine
      ↓
JSON / YAML / Markdown
      ↓
Obsidian
      ↓
Dataview
      ↓
tablas
gráficos
progreso
grafos

Obsidian será consumidor de telemetría, no fuente de verdad pedagógica.

Tus apuntes manuales permanecen separados.

41. Filosofía de datos

Se mantienen separados:

Conocimiento

Los libros, PDFs y documentos.

Estado

Lo que el sistema sabe sobre el proceso de aprendizaje.

Evidencia

Lo que las fuentes realmente dicen.

Telemetría

Lo que el sistema hizo.

Producción humana

Lo que el estudiante escribió y pensó.

Esta separación es fundamental.

42. Seguridad y privacidad V1

El sistema debe asumir que los documentos pueden ser privados.

Regla:

No enviar información sensible a una API externa innecesariamente.

Además:

API keys fuera del repositorio;
.env excluido;
secrets scanning;
logs controlados;
no almacenar credenciales en prompts;
separación entre datos de estudio y configuración.
43. Arquitectura de modelos

La arquitectura no dependerá de un único LLM.

Conceptualmente:

             CONTEXT PACK
                   │
          ┌────────┴────────┐
          │                 │
       TUTOR             TESTER
          │                 │
      modelo A           modelo B

Los modelos son intercambiables.

La calidad del sistema debe depender principalmente de:

Retrieval
+
Context
+
Contracts
+
Validation

y no de perseguir permanentemente el modelo "más inteligente".

44. Principio de independencia

Ningún componente pedagógico debe asumir:

"este modelo siempre estará disponible."

Debe existir una interfaz abstracta:

LLMProvider

que permita cambiar:

Groq
Gemini
OpenRouter
DeepSeek
modelo local

sin reescribir el sistema pedagógico.

45. Estado de desarrollo

Cada subsistema tendrá un estado:

PLANNED
    ↓
IMPLEMENTING
    ↓
TESTING
    ↓
FAILED
    ↓
FIXING
    ↓
RETESTING
    ↓
CERTIFIED

Solo:

CERTIFIED

permite considerarlo terminado.

46. Regla de integración

Un componente nuevo no se integra a la rama principal simplemente porque funciona.

Debe cumplir:

SPEC
 ↓
IMPLEMENTATION
 ↓
TESTS
 ↓
ADVERSARIAL TESTING
 ↓
FIX
 ↓
REGRESSION
 ↓
QUALITY GATE
 ↓
CERTIFIED
 ↓
INTEGRATION

Esto será obligatorio para todo el proyecto.

47. Definición de V1 terminada

V1 no estará terminada cuando:

"podamos chatear con PDFs."

Estará terminada cuando podamos demostrar reproduciblemente que:

1.

Podemos crear un Notebook.

2.

Podemos cargar fuentes.

3.

Podemos definir un roadmap.

4.

Podemos asociar fuentes al roadmap.

5.

Podemos recuperar evidencia.

6.

Podemos citarla.

7.

Podemos abstenernos cuando no exista evidencia.

8.

Podemos conversar con esa evidencia.

9.

Podemos generar un plan de estudio.

10.

Podemos utilizar el mismo conocimiento para evaluar.

11.

Podemos evaluar respuestas del estudiante.

12.

Podemos ejecutar ejercicios mediante Python/pytest.

13.

Podemos enviar los resultados al Tester.

14.

Podemos registrar estado del estudiante.

15.

Podemos detectar debilidades.

16.

Todo esto pasa por tests reproducibles.

17.

Los componentes críticos están certificados.

48. Criterio final de éxito

La pregunta que debe responder V1 es:

"¿Puedo darle al sistema mi roadmap + mis fuentes y, en lugar de pasar horas decidiendo qué estudiar, obtener una trayectoria pedagógica rigurosa, conversar profundamente sobre cada concepto y luego ser evaluado utilizando exactamente el mismo conocimiento?"

Si la respuesta es sí, la V1 cumplió su misión.

49. Principio final

El sistema no pretende ser:

"una IA que sabe mucho."

Pretende ser:

un sistema que sabe exactamente qué conocimiento tiene, dónde está, por qué lo está utilizando, cómo enseñarlo, cómo evaluarlo y cuándo no tiene evidencia suficiente.

Y esa diferencia es la que convierte el proyecto de un simple chat con PDFs en una verdadera herramienta de aprendizaje.
