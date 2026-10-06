# CASOS DE ADJUDICACIÓN CIEGA — FASE 1A.2 (PILOTO 22 CONSULTAS)

> **Protocolo:** Evaluación a ciegas ($N=1$). Evalúe cada candidato sin conocer qué modelo, extractor o chunker lo produjo.

---

## Caso #01 [Q1A2-01] (ARQ-01)

**Consulta:** *"¿Cuál es la estructura general de contenidos y preliminares presentada en el índice de Fundamentos de Programación?"*

- **Páginas de evidencia teórica:** [11, 14]
- **Criterio de Relevancia:** Recupera la descripción o listado de capítulos preliminares de la obra.
- **Criterio de Suficiencia:** Permite contrastar el esquema temático de la obra.

### Pipeline_Alpha (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Notas`  
> **Score Coseno (Diagnóstico):** `0.4992`

```text
[Notas]
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algor
```

### Pipeline_Beta (Rank 1 | Pág. 500)
> **Encabezado:** `Joyanes > Página 500`  
> **Score Coseno (Diagnóstico):** `0.5855`

```text
[Página 500]
470  
Fundamentos de programación
  registro : tipo_nodo
    tipo_elemento: elemento
    entero: sig
  fin_registro
  array[1..Max] de tipo_nodo: lista
 var
  entero: inic,vacio
  lista: 
```

### Pipeline_Gamma (Rank 1 | Pág. 149)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5005`

```text
Estructura general de un programa  119
Diagrama de flujo
inicio
leer
NPASOS
NPASOS <= 0
N > 0
escribir
NPASOS
FACT
fin
escribir
ERROR
1
1
sí
no
hacer
FACT ← 10
N ← NPASOS-5
hacer
FACT ← FACT + N * 5
s
```

### Pipeline_Delta (Rank 1 | Pág. 149)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5005`

```text
Estructura general de un programa  119
Diagrama de flujo
inicio
leer
NPASOS
NPASOS <= 0
N > 0
escribir
NPASOS
FACT
fin
escribir
ERROR
1
1
sí
no
hacer
FACT ← 10
N ← NPASOS-5
hacer
FACT ← FACT + N * 5
s
```

### Pipeline_Epsilon (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Notas`  
> **Score Coseno (Diagnóstico):** `0.4992`

```text
[Notas]
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algor
```

### Pipeline_Zeta (Rank 1 | Pág. 547)
> **Encabezado:** `Joyanes > Página 547`  
> **Score Coseno (Diagnóstico):** `0.8373`

```text
[Página 547]
Estructura de datos no lineales (árboles y grafos)  517
presentan estructuras jerárquicas con limitaciones de dos sub-
árboles por cada nodo. Si se eliminan las restricciones de 
que cada
```

### Pipeline_Eta (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Pág 142 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.5133`

```text
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algoritmo
   
```

### Pipeline_Theta (Rank 1 | Pág. 149)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5005`

```text
Estructura general de un programa  119
Diagrama de flujo
inicio
leer
NPASOS
NPASOS <= 0
N > 0
escribir
NPASOS
FACT
fin
escribir
ERROR
1
1
sí
no
hacer
FACT ← 10
N ← NPASOS-5
hacer
FACT ← FACT + N * 5
s
```

### Pipeline_Iota (Rank 1 | Pág. 142)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5251`

```text
112  Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algoritmo
    
```

---

## Caso #02 [Q1A2-02] (ARQ-08)

**Consulta:** *"¿En qué página y capítulo del índice general se ubican las estructuras de datos y punteros?"*

- **Páginas de evidencia teórica:** [14, 18]
- **Criterio de Relevancia:** Identifica los números de página o capítulos correspondientes a estructuras de datos o punteros.
- **Criterio de Suficiencia:** Proporciona la ubicación precisa en el índice general.

### Pipeline_Alpha (Rank 1 | Pág. 13)
> **Encabezado:** `Joyanes > Página 13`  
> **Score Coseno (Diagnóstico):** `0.4372`

```text
[Página 13]
Capítulo 11. Ordenación, búsqueda y fusión externa (archivos) .......................................................................................... 
405
INTRODUCCIÓN .................
```

### Pipeline_Beta (Rank 1 | Pág. 13)
> **Encabezado:** `Joyanes > Página 13`  
> **Score Coseno (Diagnóstico):** `0.5587`

```text
[Página 13]
Capítulo 11. Ordenación, búsqueda y fusión externa (archivos) .......................................................................................... 
405
INTRODUCCIÓN .................
```

### Pipeline_Gamma (Rank 1 | Pág. 13)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5821`

```text
........................................................................................... 
429
12.1. Introducción a las estructuras de datos .........................................................
```

### Pipeline_Delta (Rank 1 | Pág. 13)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5821`

```text
........................................................................................... 
429
12.1. Introducción a las estructuras de datos .........................................................
```

### Pipeline_Epsilon (Rank 1 | Pág. 13)
> **Encabezado:** `Joyanes > Página 13`  
> **Score Coseno (Diagnóstico):** `0.4372`

```text
[Página 13]
Capítulo 11. Ordenación, búsqueda y fusión externa (archivos) .......................................................................................... 
405
INTRODUCCIÓN .................
```

### Pipeline_Zeta (Rank 1 | Pág. 485)
> **Encabezado:** `Joyanes > Página 485`  
> **Score Coseno (Diagnóstico):** `0.8398`

```text
[Página 485]
Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)  455
  procedimiento consultarCima( E punt: cima;
S tipo_elemento: elemento)
   inicio
   si no vacia (cima) ento
```

### Pipeline_Eta (Rank 1 | Pág. 13)
> **Encabezado:** `Joyanes > Pág 13 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.5519`

```text
417
11.5.3. Clasificación por mezcla de secuencias equilibridas .......................................................................... 
421
ACTIVIDADES DE PROGRAMACIÓN RESUELTAS ..................
```

### Pipeline_Theta (Rank 1 | Pág. 13)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5821`

```text
........................................................................................... 
429
12.1. Introducción a las estructuras de datos .........................................................
```

### Pipeline_Iota (Rank 1 | Pág. 13)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5808`

```text
............................................................................................  429
12.1. Introducción a las estructuras de datos ........................................................
```

---

## Caso #03 [Q1A2-03] (ARQ-01)

**Consulta:** *"¿Qué es un algoritmo según Joyanes Aguilar y cuáles son sus características básicas?"*

- **Páginas de evidencia teórica:** [35, 40]
- **Criterio de Relevancia:** Define algoritmo como secuencia finita de pasos o instrucciones no ambiguas.
- **Criterio de Suficiencia:** Detalla las características esenciales (precisión, finitud, definición).

### Pipeline_Alpha (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Score Coseno (Diagnóstico):** `0.4797`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por

```

### Pipeline_Beta (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Score Coseno (Diagnóstico):** `0.5617`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por

```

### Pipeline_Gamma (Rank 1 | Pág. 138)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4838`

```text
-
gramas escritos en el lenguaje de programación estructurado; por ejemplo, Pascal.
Un algoritmo constará de dos componentes: una cabecera de programa y un bloque algoritmo. La cabecera de 
programa e
```

### Pipeline_Delta (Rank 1 | Pág. 138)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4838`

```text
-
gramas escritos en el lenguaje de programación estructurado; por ejemplo, Pascal.
Un algoritmo constará de dos componentes: una cabecera de programa y un bloque algoritmo. La cabecera de 
programa e
```

### Pipeline_Epsilon (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Score Coseno (Diagnóstico):** `0.4797`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por

```

### Pipeline_Zeta (Rank 1 | Pág. 141)
> **Encabezado:** `Joyanes > Nota`  
> **Score Coseno (Diagnóstico):** `0.8508`

```text
[Nota]
Estructura general de un programa  111
2. Comentarios multilínea (comienzan con los caracteres /* y terminan con los caracteres  */, todo lo encerrado 
entre ambos juegos de caracteres son come
```

### Pipeline_Eta (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Pág 138 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.4798`

```text
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por
read     
```

### Pipeline_Theta (Rank 1 | Pág. 138)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4838`

```text
-
gramas escritos en el lenguaje de programación estructurado; por ejemplo, Pascal.
Un algoritmo constará de dos componentes: una cabecera de programa y un bloque algoritmo. La cabecera de 
programa e
```

### Pipeline_Iota (Rank 1 | Pág. 138)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4751`

```text

gramas escritos en el lenguaje de programación estructurado; por ejemplo, Pascal.
Un algoritmo constará de dos componentes: una cabecera de programa y un bloque algoritmo . La cabecera de 
programa e
```

---

## Caso #04 [Q1A2-04] (ARQ-04)

**Consulta:** *"¿Cuáles son las fases de resolución de un problema mediante computadora según el texto?"*

- **Páginas de evidencia teórica:** [38, 45]
- **Criterio de Relevancia:** Enumera las etapas principales desde el análisis hasta la verificación del programa.
- **Criterio de Suficiencia:** Permite reconstruir la secuencia completa sin omitir pasos críticos.

### Pipeline_Alpha (Rank 1 | Pág. 148)
> **Encabezado:** `Joyanes > Página 148`  
> **Score Coseno (Diagnóstico):** `0.4616`

```text
[Página 148]
118  
Fundamentos de programación
3.13. Determinar el mayor de tres números enteros.
Solución
Los pasos a seguir son:
1. Comparar el primero y el segundo entero, deduciendo cuál es el may
```

### Pipeline_Beta (Rank 1 | Pág. 16)
> **Encabezado:** `Joyanes > Página 16`  
> **Score Coseno (Diagnóstico):** `0.5719`

```text
[Página 16]
17.7.2. Herencia privada .................................................................................................................................. 
640
17.7.3. Herencia protegida.
```

### Pipeline_Gamma (Rank 1 | Pág. 16)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5609`

```text
..................................................................... 
653
 18.1. Abstracción y resolución de problemas ................................................................................
```

### Pipeline_Delta (Rank 1 | Pág. 16)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5609`

```text
..................................................................... 
653
 18.1. Abstracción y resolución de problemas ................................................................................
```

### Pipeline_Epsilon (Rank 1 | Pág. 148)
> **Encabezado:** `Joyanes > Página 148`  
> **Score Coseno (Diagnóstico):** `0.4616`

```text
[Página 148]
118  
Fundamentos de programación
3.13. Determinar el mayor de tres números enteros.
Solución
Los pasos a seguir son:
1. Comparar el primero y el segundo entero, deduciendo cuál es el may
```

### Pipeline_Zeta (Rank 1 | Pág. 45)
> **Encabezado:** `Joyanes > Página 45`  
> **Score Coseno (Diagnóstico):** `0.8465`

```text
[Página 45]
Introducción a las computadoras y los lenguajes de programación  15
1.3. REPRESENTACIÓN DE LA INFORMACIÓN EN LAS COMPUTADORAS
Una computadora es un sistema para procesar información de mod
```

### Pipeline_Eta (Rank 1 | Pág. 148)
> **Encabezado:** `Joyanes > Pág 148 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.4714`

```text
118  
Fundamentos de programación
3.13. Determinar el mayor de tres números enteros.
Solución
Los pasos a seguir son:
1. Comparar el primero y el segundo entero, deduciendo cuál es el mayor.
2. Compar
```

### Pipeline_Theta (Rank 1 | Pág. 16)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5609`

```text
..................................................................... 
653
 18.1. Abstracción y resolución de problemas ................................................................................
```

### Pipeline_Iota (Rank 1 | Pág. 16)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5521`

```text
.......................................................................  653
 18.1. Abstracción y resolución de problemas ..............................................................................
```

---

## Caso #05 [Q1A2-05] (ARQ-02)

**Consulta:** *"¿Cuál es la diferencia entre el diseño descendente (top-down) y el refinamiento por pasos?"*

- **Páginas de evidencia teórica:** [40, 45]
- **Criterio de Relevancia:** Explica la descomposición modular y la especificación sucesiva de detalles.
- **Criterio de Suficiencia:** Contrasta adecuadamente ambos conceptos según la metodología expuesta.

### Pipeline_Alpha (Rank 1 | Pág. 148)
> **Encabezado:** `Joyanes > Página 148`  
> **Score Coseno (Diagnóstico):** `0.4266`

```text
[Página 148]
118  
Fundamentos de programación
3.13. Determinar el mayor de tres números enteros.
Solución
Los pasos a seguir son:
1. Comparar el primero y el segundo entero, deduciendo cuál es el may
```

### Pipeline_Beta (Rank 1 | Pág. 486)
> **Encabezado:** `Joyanes > Página 486`  
> **Score Coseno (Diagnóstico):** `0.5073`

```text
[Página 486]
456  
Fundamentos de programación
procedimiento meter(E/S punt: cima; E tipo_elemento: elemento)
 var 
   punt: auxi
 inicio
   reservar(auxi)
   auxi→.elemento ← elemento
   auxi→.cima ←
```

### Pipeline_Gamma (Rank 1 | Pág. 16)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5125`

```text
..................................................................... 
653
 18.1. Abstracción y resolución de problemas ................................................................................
```

### Pipeline_Delta (Rank 1 | Pág. 16)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5125`

```text
..................................................................... 
653
 18.1. Abstracción y resolución de problemas ................................................................................
```

### Pipeline_Epsilon (Rank 1 | Pág. 148)
> **Encabezado:** `Joyanes > Página 148`  
> **Score Coseno (Diagnóstico):** `0.4266`

```text
[Página 148]
118  
Fundamentos de programación
3.13. Determinar el mayor de tres números enteros.
Solución
Los pasos a seguir son:
1. Comparar el primero y el segundo entero, deduciendo cuál es el may
```

### Pipeline_Zeta (Rank 1 | Pág. 486)
> **Encabezado:** `Joyanes > Página 486`  
> **Score Coseno (Diagnóstico):** `0.8159`

```text
[Página 486]
456  
Fundamentos de programación
procedimiento meter(E/S punt: cima; E tipo_elemento: elemento)
 var 
   punt: auxi
 inicio
   reservar(auxi)
   auxi→.elemento ← elemento
   auxi→.cima ←
```

### Pipeline_Eta (Rank 1 | Pág. 16)
> **Encabezado:** `Joyanes > Pág 16 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.4732`

```text
654
18.1.1. Descomposición procedimental ......................................................................................................... 
654
18.1.2. Diseño descendente .....................
```

### Pipeline_Theta (Rank 1 | Pág. 16)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5125`

```text
..................................................................... 
653
 18.1. Abstracción y resolución de problemas ................................................................................
```

### Pipeline_Iota (Rank 1 | Pág. 16)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.518`

```text
.......................................................................  653
 18.1. Abstracción y resolución de problemas ..............................................................................
```

---

## Caso #06 [Q1A2-06] (ARQ-06)

**Consulta:** *"¿Cómo se describe la estructura jerárquica de un programa estructurado?"*

- **Páginas de evidencia teórica:** [42, 45]
- **Criterio de Relevancia:** Describe la organización modular en niveles de abstracción.
- **Criterio de Suficiencia:** Explica la interacción funcional entre el programa principal y subprogramas.

### Pipeline_Alpha (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Score Coseno (Diagnóstico):** `0.4673`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por

```

### Pipeline_Beta (Rank 1 | Pág. 37)
> **Encabezado:** `Joyanes > Página 37`  
> **Score Coseno (Diagnóstico):** `0.5633`

```text
[Página 37]
Introducción a las computadoras y los lenguajes de programación  7
1.2. ORGANIZACIÓN FÍSICA DE UNA COMPUTADORA
Los dos componentes principales de una computadora son: hardware y software. 
```

### Pipeline_Gamma (Rank 1 | Pág. 11)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5063`

```text
 7.7. Estructuras versus registros ............................................................................................................................... 
265
7.7.1. Registros ...............
```

### Pipeline_Delta (Rank 1 | Pág. 11)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5063`

```text
 7.7. Estructuras versus registros ............................................................................................................................... 
265
7.7.1. Registros ...............
```

### Pipeline_Epsilon (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Score Coseno (Diagnóstico):** `0.4673`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por

```

### Pipeline_Zeta (Rank 1 | Pág. 547)
> **Encabezado:** `Joyanes > Página 547`  
> **Score Coseno (Diagnóstico):** `0.8514`

```text
[Página 547]
Estructura de datos no lineales (árboles y grafos)  517
presentan estructuras jerárquicas con limitaciones de dos sub-
árboles por cada nodo. Si se eliminan las restricciones de 
que cada
```

### Pipeline_Eta (Rank 1 | Pág. 489)
> **Encabezado:** `Joyanes > Pág 489 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.4872`

```text
Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)  459
Programa principal
X
Y
Z
Subprograma
A
Subprograma A
fin _ subprograma A
fin _ subprograma B
fin _ subprograma C
Subprogr
```

### Pipeline_Theta (Rank 1 | Pág. 11)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5063`

```text
 7.7. Estructuras versus registros ............................................................................................................................... 
265
7.7.1. Registros ...............
```

### Pipeline_Iota (Rank 1 | Pág. 11)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5006`

```text
 7.7. Estructuras versus registros ...............................................................................................................................  265
7.7.1. Registros ...............
```

---

## Caso #07 [Q1A2-07] (ARQ-01)

**Consulta:** *"¿Cómo se define y formaliza la estructura de selección doble (si-entonces-sino) en pseudocódigo?"*

- **Páginas de evidencia teórica:** [135, 142]
- **Criterio de Relevancia:** Presenta la sintaxis o reglas semánticas de la bifurcación lógica doble.
- **Criterio de Suficiencia:** Muestra el pseudocódigo formal y las ramas verdadera/falsa.

### Pipeline_Alpha (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Notas`  
> **Score Coseno (Diagnóstico):** `0.4755`

```text
[Notas]
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algor
```

### Pipeline_Beta (Rank 1 | Pág. 499)
> **Encabezado:** `Joyanes > Página 499`  
> **Score Coseno (Diagnóstico):** `0.5265`

```text
[Página 499]
Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)  469
Frente
Fondo
Eliminación
Eliminación
Inserción
Inserción
Figura 12.18. Doble cola (bicola).
Existen dos vari
```

### Pipeline_Gamma (Rank 1 | Pág. 142)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4624`

```text
imples.
3. Utilizar siempre sangrías en los bucles o en aquellas instrucciones que proporcionen legibilidad al programa, 
como inicio y fin.
MODELO PROPUESTO DE ALGORITMO
algoritmo raices
// resuelve 
```

### Pipeline_Delta (Rank 1 | Pág. 142)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4624`

```text
imples.
3. Utilizar siempre sangrías en los bucles o en aquellas instrucciones que proporcionen legibilidad al programa, 
como inicio y fin.
MODELO PROPUESTO DE ALGORITMO
algoritmo raices
// resuelve 
```

### Pipeline_Epsilon (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Notas`  
> **Score Coseno (Diagnóstico):** `0.4755`

```text
[Notas]
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algor
```

### Pipeline_Zeta (Rank 1 | Pág. 503)
> **Encabezado:** `Joyanes > Página 503`  
> **Score Coseno (Diagnóstico):** `0.8505`

```text
[Página 503]
Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)  473
procedimiento devoluciones( E/S entero: inic, vacio; E/S lista: m)
 var
  tipo_elemento: elemento
  entero  
```

### Pipeline_Eta (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Pág 142 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.4729`

```text
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algoritmo
   
```

### Pipeline_Theta (Rank 1 | Pág. 142)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4624`

```text
imples.
3. Utilizar siempre sangrías en los bucles o en aquellas instrucciones que proporcionen legibilidad al programa, 
como inicio y fin.
MODELO PROPUESTO DE ALGORITMO
algoritmo raices
// resuelve 
```

### Pipeline_Iota (Rank 1 | Pág. 141)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5101`

```text
seccion de declaraciones
```

---

## Caso #08 [Q1A2-08] (ARQ-05)

**Consulta:** *"¿Cuál es la sintaxis de la sentencia de selección múltiple según_sea (switch) y cómo se maneja la opción por defecto?"*

- **Páginas de evidencia teórica:** [142, 148]
- **Criterio de Relevancia:** Identifica los bloques de selección múltiple y la cláusula alternativa (de otro modo / default).
- **Criterio de Suficiencia:** Permite reproducir la estructura sintáctica completa sin ambigüedades.

### Pipeline_Alpha (Rank 1 | Pág. 141)
> **Encabezado:** `Joyanes > Nota`  
> **Score Coseno (Diagnóstico):** `0.3938`

```text
[Nota]
Estructura general de un programa  111
2. Comentarios multilínea (comienzan con los caracteres /* y terminan con los caracteres  */, todo lo encerrado 
entre ambos juegos de caracteres son come
```

### Pipeline_Beta (Rank 1 | Pág. 135)
> **Encabezado:** `Joyanes > Página 135`  
> **Score Coseno (Diagnóstico):** `0.4554`

```text
[Página 135]
Estructura general de un programa  105
3.9.1. Asignación aritmética
Las expresiones en las operaciones de asignación son aritméticas:
AMN ← 3 + 14 + 8 
 se evalúa la expresión 3 + 14 + 8 
```

### Pipeline_Gamma (Rank 1 | Pág. 141)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4124`

```text
eccion de declaraciones

```

### Pipeline_Delta (Rank 1 | Pág. 141)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4124`

```text
eccion de declaraciones

```

### Pipeline_Epsilon (Rank 1 | Pág. 141)
> **Encabezado:** `Joyanes > Nota`  
> **Score Coseno (Diagnóstico):** `0.3938`

```text
[Nota]
Estructura general de un programa  111
2. Comentarios multilínea (comienzan con los caracteres /* y terminan con los caracteres  */, todo lo encerrado 
entre ambos juegos de caracteres son come
```

### Pipeline_Zeta (Rank 1 | Pág. 17)
> **Encabezado:** `Joyanes > Página 17`  
> **Score Coseno (Diagnóstico):** `0.8218`

```text
[Página 17]
18.10.2. Manual de mantenimiento (documentación para programadores) .................................................. 
680
18.10.3. Reglas de documentación ...............................
```

### Pipeline_Eta (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Pág 142 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.3995`

```text
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algoritmo
   
```

### Pipeline_Theta (Rank 1 | Pág. 141)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4124`

```text
eccion de declaraciones

```

### Pipeline_Iota (Rank 1 | Pág. 141)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5028`

```text
seccion de declaraciones
```

---

## Caso #09 [Q1A2-09] (ARQ-04)

**Consulta:** *"¿Qué algoritmo o pseudocódigo se presenta para evaluar si un número entero es par o impar?"*

- **Páginas de evidencia teórica:** [138, 145]
- **Criterio de Relevancia:** Recupera el pseudocódigo o lógica que utiliza el operador módulo para determinar paridad.
- **Criterio de Suficiencia:** Proporciona el algoritmo funcional completo.

### Pipeline_Alpha (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Notas`  
> **Score Coseno (Diagnóstico):** `0.4914`

```text
[Notas]
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algor
```

### Pipeline_Beta (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Score Coseno (Diagnóstico):** `0.525`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por

```

### Pipeline_Gamma (Rank 1 | Pág. 150)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5054`

```text
120  
Fundamentos de programación
Diagrama de flujo
escribir
S
X <= 50
fin
sí
inicio
X ← 1
no
S ← 0
S ← S + X
X ← X + 1
3.16. Escribir un algoritmo que calcule el producto de los n primeros números na
```

### Pipeline_Delta (Rank 1 | Pág. 150)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5054`

```text
120  
Fundamentos de programación
Diagrama de flujo
escribir
S
X <= 50
fin
sí
inicio
X ← 1
no
S ← 0
S ← S + X
X ← X + 1
3.16. Escribir un algoritmo que calcule el producto de los n primeros números na
```

### Pipeline_Epsilon (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Notas`  
> **Score Coseno (Diagnóstico):** `0.4914`

```text
[Notas]
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algor
```

### Pipeline_Zeta (Rank 1 | Pág. 149)
> **Encabezado:** `Joyanes > Página 149`  
> **Score Coseno (Diagnóstico):** `0.8458`

```text
[Página 149]
Estructura general de un programa  119
Diagrama de flujo
inicio
leer
NPASOS
NPASOS <= 0
N > 0
escribir
NPASOS
FACT
fin
escribir
ERROR
1
1
sí
no
hacer
FACT ← 10
N ← NPASOS-5
hacer
FACT ← F
```

### Pipeline_Eta (Rank 1 | Pág. 150)
> **Encabezado:** `Joyanes > Pág 150 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.5074`

```text
120  
Fundamentos de programación
Diagrama de flujo
escribir
S
X <= 50
fin
sí
inicio
X ← 1
no
S ← 0
S ← S + X
X ← X + 1
3.16. Escribir un algoritmo que calcule el producto de los n primeros números na
```

### Pipeline_Theta (Rank 1 | Pág. 150)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5054`

```text
120  
Fundamentos de programación
Diagrama de flujo
escribir
S
X <= 50
fin
sí
inicio
X ← 1
no
S ← 0
S ← S + X
X ← X + 1
3.16. Escribir un algoritmo que calcule el producto de los n primeros números na
```

### Pipeline_Iota (Rank 1 | Pág. 544)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4996`

```text
514  Fundamentos de programación
lógico función árbollleno(E entero: vacío)
inicio
  si vacío = 0 entonces
    devolver(verdad)
  si_no
    devolver(falso)
  fin_si
fin_función
procedimiento inorden(E
```

---

## Caso #10 [Q1A2-10] (ARQ-07)

**Consulta:** *"¿Por qué es necesario delimitar explícitamente las estructuras de control anidadas en programación estructurada?"*

- **Páginas de evidencia teórica:** [140, 150]
- **Criterio de Relevancia:** Explica la resolución de ambigüedad del 'else colgante' o delimitación de bloques.
- **Criterio de Suficiencia:** Aporta justificación conceptual sólida según el texto.

### Pipeline_Alpha (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Notas`  
> **Score Coseno (Diagnóstico):** `0.4187`

```text
[Notas]
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algor
```

### Pipeline_Beta (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Score Coseno (Diagnóstico):** `0.5151`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por

```

### Pipeline_Gamma (Rank 1 | Pág. 14)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4708`

```text
............................. 
554
15.1.1. Limitaciones de la programación estructurada ................................................................................... 
554
15.1.2. Modelado de obj
```

### Pipeline_Delta (Rank 1 | Pág. 14)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4708`

```text
............................. 
554
15.1.1. Limitaciones de la programación estructurada ................................................................................... 
554
15.1.2. Modelado de obj
```

### Pipeline_Epsilon (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Notas`  
> **Score Coseno (Diagnóstico):** `0.4187`

```text
[Notas]
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algor
```

### Pipeline_Zeta (Rank 1 | Pág. 547)
> **Encabezado:** `Joyanes > Página 547`  
> **Score Coseno (Diagnóstico):** `0.8418`

```text
[Página 547]
Estructura de datos no lineales (árboles y grafos)  517
presentan estructuras jerárquicas con limitaciones de dos sub-
árboles por cada nodo. Si se eliminan las restricciones de 
que cada
```

### Pipeline_Eta (Rank 1 | Pág. 14)
> **Encabezado:** `Joyanes > Pág 14 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.4689`

```text
553
INTRODUCCIÓN ......................................................................................................................................................... 
553
15.1. Programación estru
```

### Pipeline_Theta (Rank 1 | Pág. 14)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4708`

```text
............................. 
554
15.1.1. Limitaciones de la programación estructurada ................................................................................... 
554
15.1.2. Modelado de obj
```

### Pipeline_Iota (Rank 1 | Pág. 14)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4754`

```text
.................................  554
15.1.1. Limitaciones de la programación estructurada ...................................................................................  554
15.1.2. Modelado de
```

---

## Caso #11 [Q1A2-11] (ARQ-01)

**Consulta:** *"¿Cuál es la función del operador de dirección & y del operador de indirección * en punteros de C?"*

- **Páginas de evidencia teórica:** [485, 492]
- **Criterio de Relevancia:** Distingue entre obtener la dirección en memoria (&) y acceder al valor apuntado (*).
- **Criterio de Suficiencia:** Define con precisión la semántica de ambos operadores en C.

### Pipeline_Alpha (Rank 1 | Pág. 136)
> **Encabezado:** `Joyanes > Página 136`  
> **Score Coseno (Diagnóstico):** `0.4531`

```text
[Página 136]
106  
Fundamentos de programación
y es equivalente a:
variable operador ← expresión
EJEMPLO
c ← c + 5 
equivale a 
 
c +← 5
a ← a * (b + c) 
equivale a 
 
a *← b + c
o si lo prefiere util
```

### Pipeline_Beta (Rank 1 | Pág. 136)
> **Encabezado:** `Joyanes > Página 136`  
> **Score Coseno (Diagnóstico):** `0.5665`

```text
[Página 136]
106  
Fundamentos de programación
y es equivalente a:
variable operador ← expresión
EJEMPLO
c ← c + 5 
equivale a 
 
c +← 5
a ← a * (b + c) 
equivale a 
 
a *← b + c
o si lo prefiere util
```

### Pipeline_Gamma (Rank 1 | Pág. 135)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4834`

```text
ador ← . Así se puede usar el operador de asignación (←) precedido por cualquiera de 
los siguientes operadores aritméticos: +, –, *, /, %. La sintaxis es la siguiente:
<nombre_variable> ← <variable> 
```

### Pipeline_Delta (Rank 1 | Pág. 135)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4834`

```text
ador ← . Así se puede usar el operador de asignación (←) precedido por cualquiera de 
los siguientes operadores aritméticos: +, –, *, /, %. La sintaxis es la siguiente:
<nombre_variable> ← <variable> 
```

### Pipeline_Epsilon (Rank 1 | Pág. 136)
> **Encabezado:** `Joyanes > Página 136`  
> **Score Coseno (Diagnóstico):** `0.4531`

```text
[Página 136]
106  
Fundamentos de programación
y es equivalente a:
variable operador ← expresión
EJEMPLO
c ← c + 5 
equivale a 
 
c +← 5
a ← a * (b + c) 
equivale a 
 
a *← b + c
o si lo prefiere util
```

### Pipeline_Zeta (Rank 1 | Pág. 136)
> **Encabezado:** `Joyanes > Página 136`  
> **Score Coseno (Diagnóstico):** `0.8382`

```text
[Página 136]
106  
Fundamentos de programación
y es equivalente a:
variable operador ← expresión
EJEMPLO
c ← c + 5 
equivale a 
 
c +← 5
a ← a * (b + c) 
equivale a 
 
a *← b + c
o si lo prefiere util
```

### Pipeline_Eta (Rank 1 | Pág. 136)
> **Encabezado:** `Joyanes > Pág 136 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.4631`

```text
106  
Fundamentos de programación
y es equivalente a:
variable operador ← expresión
EJEMPLO
c ← c + 5 
equivale a 
 
c +← 5
a ← a * (b + c) 
equivale a 
 
a *← b + c
o si lo prefiere utilizando el sig
```

### Pipeline_Theta (Rank 1 | Pág. 135)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4834`

```text
ador ← . Así se puede usar el operador de asignación (←) precedido por cualquiera de 
los siguientes operadores aritméticos: +, –, *, /, %. La sintaxis es la siguiente:
<nombre_variable> ← <variable> 
```

### Pipeline_Iota (Rank 1 | Pág. 136)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4918`

```text
106  Fundamentos de programación
y es equivalente a:
variable operador ← expresión
EJEMPLO
c ← c + 5  equivale a  c +← 5
a ← a * (b + c)  equivale a  a *← b + c
o si lo prefiere utilizando el signo de
```

---

## Caso #12 [Q1A2-12] (ARQ-05)

**Consulta:** *"¿Cómo se declara un puntero a una estructura struct y cómo se accede a sus miembros con el operador flecha ->?"*

- **Páginas de evidencia teórica:** [490, 498]
- **Criterio de Relevancia:** Muestra la notación `ptr->campo` o `(*ptr).campo` para structs.
- **Criterio de Suficiencia:** Incluye ejemplo de sintaxis en lenguaje C según el texto.

### Pipeline_Alpha (Rank 1 | Pág. 492)
> **Encabezado:** `Joyanes > Página 492`  
> **Score Coseno (Diagnóstico):** `0.4831`

```text
[Página 492]
462  
Fundamentos de programación
• Acceder al primer elemento de la cola.
• Añadir un elemento al final de cola.
• Eliminar el primer elemento de la cola.
• Vaciar la cola.
• Verificar e
```

### Pipeline_Beta (Rank 1 | Pág. 485)
> **Encabezado:** `Joyanes > Página 485`  
> **Score Coseno (Diagnóstico):** `0.5094`

```text
[Página 485]
Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)  455
  procedimiento consultarCima( E punt: cima;
S tipo_elemento: elemento)
   inicio
   si no vacia (cima) ento
```

### Pipeline_Gamma (Rank 1 | Pág. 486)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4872`

```text
456  
Fundamentos de programación
procedimiento meter(E/S punt: cima; E tipo_elemento: elemento)
 var 
   punt: auxi
 inicio
   reservar(auxi)
   auxi→.elemento ← elemento
   auxi→.cima ← cima
   cima
```

### Pipeline_Delta (Rank 1 | Pág. 486)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4872`

```text
456  
Fundamentos de programación
procedimiento meter(E/S punt: cima; E tipo_elemento: elemento)
 var 
   punt: auxi
 inicio
   reservar(auxi)
   auxi→.elemento ← elemento
   auxi→.cima ← cima
   cima
```

### Pipeline_Epsilon (Rank 1 | Pág. 492)
> **Encabezado:** `Joyanes > Página 492`  
> **Score Coseno (Diagnóstico):** `0.4831`

```text
[Página 492]
462  
Fundamentos de programación
• Acceder al primer elemento de la cola.
• Añadir un elemento al final de cola.
• Eliminar el primer elemento de la cola.
• Vaciar la cola.
• Verificar e
```

### Pipeline_Zeta (Rank 1 | Pág. 545)
> **Encabezado:** `Joyanes > Página 545`  
> **Score Coseno (Diagnóstico):** `0.8318`

```text
[Página 545]
Estructura de datos no lineales (árboles y grafos)  515
        raíz ← auxi
      si_no
        si mayor(a[ant].elemento, elemento) entonces
          a[ant].izdo ← auxi
        si_no
   
```

### Pipeline_Eta (Rank 1 | Pág. 11)
> **Encabezado:** `Joyanes > Pág 11 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.4956`

```text
 7.7. Estructuras versus registros ............................................................................................................................... 
265
7.7.1. Registros ...............
```

### Pipeline_Theta (Rank 1 | Pág. 486)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4872`

```text
456  
Fundamentos de programación
procedimiento meter(E/S punt: cima; E tipo_elemento: elemento)
 var 
   punt: auxi
 inicio
   reservar(auxi)
   auxi→.elemento ← elemento
   auxi→.cima ← cima
   cima
```

### Pipeline_Iota (Rank 1 | Pág. 486)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4938`

```text
456  Fundamentos de programación
procedimiento meter(E/S punt: cima; E tipo_elemento: elemento)
 var 
   punt: auxi
 inicio
   reservar(auxi)
   auxi→.elemento ← elemento
   auxi→.cima ← cima
   cima 
```

---

## Caso #13 [Q1A2-13] (ARQ-04)

**Consulta:** *"¿Cómo se asigna memoria dinámica mediante malloc y cómo se libera con free en C según Joyanes?"*

- **Páginas de evidencia teórica:** [495, 505]
- **Criterio de Relevancia:** Describe la llamada a malloc con sizeof y la posterior invocación de free.
- **Criterio de Suficiencia:** Explica el ciclo de reserva y liberación de memoria.

### Pipeline_Alpha (Rank 1 | Pág. 492)
> **Encabezado:** `Joyanes > Página 492`  
> **Score Coseno (Diagnóstico):** `0.4765`

```text
[Página 492]
462  
Fundamentos de programación
• Acceder al primer elemento de la cola.
• Añadir un elemento al final de cola.
• Eliminar el primer elemento de la cola.
• Vaciar la cola.
• Verificar e
```

### Pipeline_Beta (Rank 1 | Pág. 502)
> **Encabezado:** `Joyanes > Página 502`  
> **Score Coseno (Diagnóstico):** `0.49`

```text
[Página 502]
472  
Fundamentos de programación
procedimiento liberar(E/S entero: posic; E/S lista: m;
                      E/S entero: vacio)
 inicio
  m[posic].sig ← vacio
  vacio ← posic
 fin_proce
```

### Pipeline_Gamma (Rank 1 | Pág. 500)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5351`

```text
 fin_desde
  m[Max].sig ← 0
 fin_procedimiento
procedimiento reservar(S entero: auxi; E lista: m; E/S entero: vacio)
 inicio
  si vacio = 0 entonces
     escribir('Memoria agotada')
     auxi  ←  0
  
```

### Pipeline_Delta (Rank 1 | Pág. 500)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5351`

```text
 fin_desde
  m[Max].sig ← 0
 fin_procedimiento
procedimiento reservar(S entero: auxi; E lista: m; E/S entero: vacio)
 inicio
  si vacio = 0 entonces
     escribir('Memoria agotada')
     auxi  ←  0
  
```

### Pipeline_Epsilon (Rank 1 | Pág. 492)
> **Encabezado:** `Joyanes > Página 492`  
> **Score Coseno (Diagnóstico):** `0.4765`

```text
[Página 492]
462  
Fundamentos de programación
• Acceder al primer elemento de la cola.
• Añadir un elemento al final de cola.
• Eliminar el primer elemento de la cola.
• Vaciar la cola.
• Verificar e
```

### Pipeline_Zeta (Rank 1 | Pág. 497)
> **Encabezado:** `Joyanes > Página 497`  
> **Score Coseno (Diagnóstico):** `0.8521`

```text
[Página 497]
Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)  467
2.º Reestructuración.
 
Cuando final llega al máximo de elementos se desplazan las componentes ocupadas haci
```

### Pipeline_Eta (Rank 1 | Pág. 492)
> **Encabezado:** `Joyanes > Pág 492 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.4852`

```text
462  
Fundamentos de programación
• Acceder al primer elemento de la cola.
• Añadir un elemento al final de cola.
• Eliminar el primer elemento de la cola.
• Vaciar la cola.
• Verificar el estado de l
```

### Pipeline_Theta (Rank 1 | Pág. 500)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5351`

```text
 fin_desde
  m[Max].sig ← 0
 fin_procedimiento
procedimiento reservar(S entero: auxi; E lista: m; E/S entero: vacio)
 inicio
  si vacio = 0 entonces
     escribir('Memoria agotada')
     auxi  ←  0
  
```

### Pipeline_Iota (Rank 1 | Pág. 500)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5205`

```text
fin_desde
  m[Max].sig ← 0
 fin_procedimiento
procedimiento reservar(S entero: auxi; E lista: m; E/S entero: vacio)
 inicio
  si vacio = 0 entonces
     escribir('Memoria agotada')
     auxi  ←  0
  s
```

---

## Caso #14 [Q1A2-14] (ARQ-03)

**Consulta:** *"¿En qué se diferencia el paso de parámetros por valor del paso por referencia mediante punteros?"*

- **Páginas de evidencia teórica:** [488, 496]
- **Criterio de Relevancia:** Explica que el paso por valor copia el dato mientras que por referencia pasa la dirección.
- **Criterio de Suficiencia:** Demuestra el impacto en la modificación de la variable original.

### Pipeline_Alpha (Rank 1 | Pág. 146)
> **Encabezado:** `Joyanes > Página 146`  
> **Score Coseno (Diagnóstico):** `0.4`

```text
[Página 146]
116  
Fundamentos de programación
3.8. Cómo se intercambian los valores de dos variables, A y B.
Solución
Con el ejercicio se ha visto cómo se pueden intercambiar los valores de una varia
```

### Pipeline_Beta (Rank 1 | Pág. 136)
> **Encabezado:** `Joyanes > Página 136`  
> **Score Coseno (Diagnóstico):** `0.4551`

```text
[Página 136]
106  
Fundamentos de programación
y es equivalente a:
variable operador ← expresión
EJEMPLO
c ← c + 5 
equivale a 
 
c +← 5
a ← a * (b + c) 
equivale a 
 
a *← b + c
o si lo prefiere util
```

### Pipeline_Gamma (Rank 1 | Pág. 146)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4169`

```text
116  
Fundamentos de programación
3.8. Cómo se intercambian los valores de dos variables, A y B.
Solución
Con el ejercicio se ha visto cómo se pueden intercambiar los valores de una variable mediante 
```

### Pipeline_Delta (Rank 1 | Pág. 146)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4169`

```text
116  
Fundamentos de programación
3.8. Cómo se intercambian los valores de dos variables, A y B.
Solución
Con el ejercicio se ha visto cómo se pueden intercambiar los valores de una variable mediante 
```

### Pipeline_Epsilon (Rank 1 | Pág. 146)
> **Encabezado:** `Joyanes > Página 146`  
> **Score Coseno (Diagnóstico):** `0.4`

```text
[Página 146]
116  
Fundamentos de programación
3.8. Cómo se intercambian los valores de dos variables, A y B.
Solución
Con el ejercicio se ha visto cómo se pueden intercambiar los valores de una varia
```

### Pipeline_Zeta (Rank 1 | Pág. 540)
> **Encabezado:** `Joyanes > Nota`  
> **Score Coseno (Diagnóstico):** `0.8172`

```text
[Nota]
510  
Fundamentos de programación
EJEMPLO 13.10
Deducir la matriz de adyacencia del grafo siguiente:
La matriz de adyacencia resultante de este grafo, cuyos vértices representan ciudades y los 
```

### Pipeline_Eta (Rank 1 | Pág. 146)
> **Encabezado:** `Joyanes > Pág 146 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.4075`

```text
116  
Fundamentos de programación
3.8. Cómo se intercambian los valores de dos variables, A y B.
Solución
Con el ejercicio se ha visto cómo se pueden intercambiar los valores de una variable mediante 
```

### Pipeline_Theta (Rank 1 | Pág. 146)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4169`

```text
116  
Fundamentos de programación
3.8. Cómo se intercambian los valores de dos variables, A y B.
Solución
Con el ejercicio se ha visto cómo se pueden intercambiar los valores de una variable mediante 
```

### Pipeline_Iota (Rank 1 | Pág. 146)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4155`

```text
116  Fundamentos de programación
3.8. Cómo se intercambian los valores de dos variables, A y B.
Solución
Con el ejercicio se ha visto cómo se pueden intercambiar los valores de una variable mediante l
```

---

## Caso #15 [Q1A2-15] (ARQ-01)

**Consulta:** *"¿Cuál es la definición formal de la notación asintótica O-grande (Big-O) para la complejidad de algoritmos?"*

- **Páginas de evidencia teórica:** [540, 545]
- **Criterio de Relevancia:** Define la cota superior del tiempo de ejecución en función del tamaño de entrada n.
- **Criterio de Suficiencia:** Presenta la formulación matemática o conceptual rigurosa.

### Pipeline_Alpha (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Notas`  
> **Score Coseno (Diagnóstico):** `0.4265`

```text
[Notas]
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algor
```

### Pipeline_Beta (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Score Coseno (Diagnóstico):** `0.472`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por

```

### Pipeline_Gamma (Rank 1 | Pág. 150)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4122`

```text
120  
Fundamentos de programación
Diagrama de flujo
escribir
S
X <= 50
fin
sí
inicio
X ← 1
no
S ← 0
S ← S + X
X ← X + 1
3.16. Escribir un algoritmo que calcule el producto de los n primeros números na
```

### Pipeline_Delta (Rank 1 | Pág. 150)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4122`

```text
120  
Fundamentos de programación
Diagrama de flujo
escribir
S
X <= 50
fin
sí
inicio
X ← 1
no
S ← 0
S ← S + X
X ← X + 1
3.16. Escribir un algoritmo que calcule el producto de los n primeros números na
```

### Pipeline_Epsilon (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Notas`  
> **Score Coseno (Diagnóstico):** `0.4265`

```text
[Notas]
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algor
```

### Pipeline_Zeta (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Score Coseno (Diagnóstico):** `0.826`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por

```

### Pipeline_Eta (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Pág 142 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.4271`

```text
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algoritmo
   
```

### Pipeline_Theta (Rank 1 | Pág. 150)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4122`

```text
120  
Fundamentos de programación
Diagrama de flujo
escribir
S
X <= 50
fin
sí
inicio
X ← 1
no
S ← 0
S ← S + X
X ← X + 1
3.16. Escribir un algoritmo que calcule el producto de los n primeros números na
```

### Pipeline_Iota (Rank 1 | Pág. 150)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4086`

```text
120  Fundamentos de programación
Diagrama de flujo
escribir
SX <= 50 fin
sí
inicio
X ← 1
no
S ← 0
S ← S + X
X ← X + 1
3.16. Escribir un algoritmo que calcule el producto de los n primeros números natu
```

---

## Caso #16 [Q1A2-16] (ARQ-03)

**Consulta:** *"¿Cuál es la diferencia de eficiencia y crecimiento entre un algoritmo O(n log n) y uno O(n^2)?"*

- **Páginas de evidencia teórica:** [543, 548]
- **Criterio de Relevancia:** Contrasta el crecimiento casi lineal con el crecimiento cuadrático ante entradas grandes.
- **Criterio de Suficiencia:** Aporta justificación analítica sobre la escalabilidad de ambos tipos de algoritmo.

### Pipeline_Alpha (Rank 1 | Pág. 546)
> **Encabezado:** `Joyanes > Página 546`  
> **Score Coseno (Diagnóstico):** `0.4032`

```text
[Página 546]
516  
Fundamentos de programación
Si los árboles terminaron de recorrerse simultáneamente es que ambos tienen el mismo número de nodos y nunca ha 
sido diferente la información comparada;
```

### Pipeline_Beta (Rank 1 | Pág. 541)
> **Encabezado:** `Joyanes > Página 541`  
> **Score Coseno (Diagnóstico):** `0.4813`

```text
[Página 541]
Estructura de datos no lineales (árboles y grafos)  511
Un grafo no dirigido de orden N con A arcos requiere N entradas en el directorio y 2*A entradas de listas enlaza-
das, excepto si e
```

### Pipeline_Gamma (Rank 1 | Pág. 542)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4404`

```text
 algoritmo que cree el árbol y nos informe sobre su número de nodos.

```

### Pipeline_Delta (Rank 1 | Pág. 542)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4404`

```text
 algoritmo que cree el árbol y nos informe sobre su número de nodos.

```

### Pipeline_Epsilon (Rank 1 | Pág. 546)
> **Encabezado:** `Joyanes > Página 546`  
> **Score Coseno (Diagnóstico):** `0.4032`

```text
[Página 546]
516  
Fundamentos de programación
Si los árboles terminaron de recorrerse simultáneamente es que ambos tienen el mismo número de nodos y nunca ha 
sido diferente la información comparada;
```

### Pipeline_Zeta (Rank 1 | Pág. 541)
> **Encabezado:** `Joyanes > Página 541`  
> **Score Coseno (Diagnóstico):** `0.8485`

```text
[Página 541]
Estructura de datos no lineales (árboles y grafos)  511
Un grafo no dirigido de orden N con A arcos requiere N entradas en el directorio y 2*A entradas de listas enlaza-
das, excepto si e
```

### Pipeline_Eta (Rank 1 | Pág. 17)
> **Encabezado:** `Joyanes > Pág 17 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.398`

```text
687
18.14.1. Eficiencia versus legibilidad (claridad) ........................................................................................... 
689
18.15. Transportabilidad ........................
```

### Pipeline_Theta (Rank 1 | Pág. 542)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4404`

```text
 algoritmo que cree el árbol y nos informe sobre su número de nodos.

```

### Pipeline_Iota (Rank 1 | Pág. 542)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4152`

```text
algoritmo que cree el árbol y nos informe sobre su número de nodos.
```

---

## Caso #17 [Q1A2-17] (ARQ-01)

**Consulta:** *"¿En qué página del índice general se lista el apartado de 'Resolución de problemas con computadoras'?"*

- **Páginas de evidencia teórica:** [11, 16]
- **Criterio de Relevancia:** Localiza el epígrafe dentro del bloque denso del índice.
- **Criterio de Suficiencia:** Indica el número de página exacto asociado al epígrafe.

### Pipeline_Alpha (Rank 1 | Pág. 14)
> **Encabezado:** `Joyanes > Página 14`  
> **Score Coseno (Diagnóstico):** `0.3931`

```text
[Página 14]
13.5. Grafos ................................................................................................................................................................ 
506
13.5.1. T
```

### Pipeline_Beta (Rank 1 | Pág. 13)
> **Encabezado:** `Joyanes > Página 13`  
> **Score Coseno (Diagnóstico):** `0.5441`

```text
[Página 13]
Capítulo 11. Ordenación, búsqueda y fusión externa (archivos) .......................................................................................... 
405
INTRODUCCIÓN .................
```

### Pipeline_Gamma (Rank 1 | Pág. 43)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4689`

```text
do se apaga la computadora.

```

### Pipeline_Delta (Rank 1 | Pág. 43)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4689`

```text
do se apaga la computadora.

```

### Pipeline_Epsilon (Rank 1 | Pág. 14)
> **Encabezado:** `Joyanes > Página 14`  
> **Score Coseno (Diagnóstico):** `0.3931`

```text
[Página 14]
13.5. Grafos ................................................................................................................................................................ 
506
13.5.1. T
```

### Pipeline_Zeta (Rank 1 | Pág. 14)
> **Encabezado:** `Joyanes > Página 14`  
> **Score Coseno (Diagnóstico):** `0.8232`

```text
[Página 14]
13.5. Grafos ................................................................................................................................................................ 
506
13.5.1. T
```

### Pipeline_Eta (Rank 1 | Pág. 12)
> **Encabezado:** `Joyanes > Pág 12 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.4212`

```text
383
10.4. Intercalación ...................................................................................................................................................... 
388
ACTIVIDADES DE PROGR
```

### Pipeline_Theta (Rank 1 | Pág. 43)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4689`

```text
do se apaga la computadora.

```

### Pipeline_Iota (Rank 1 | Pág. 14)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4565`

```text
.............................  570
RESUMEN .............................................................................................................................................................
```

---

## Caso #18 [Q1A2-18] (ARQ-04)

**Consulta:** *"¿Qué subsecciones componen el capítulo de algoritmos según la jerarquía detallada en el índice de contenidos?"*

- **Páginas de evidencia teórica:** [13, 16]
- **Criterio de Relevancia:** Recupera la secuencia de subapartados del capítulo de algoritmos.
- **Criterio de Suficiencia:** Permite observar la integridad de jerarquía en el bloque denso de índice.

### Pipeline_Alpha (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Score Coseno (Diagnóstico):** `0.5114`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por

```

### Pipeline_Beta (Rank 1 | Pág. 13)
> **Encabezado:** `Joyanes > Página 13`  
> **Score Coseno (Diagnóstico):** `0.5684`

```text
[Página 13]
Capítulo 11. Ordenación, búsqueda y fusión externa (archivos) .......................................................................................... 
405
INTRODUCCIÓN .................
```

### Pipeline_Gamma (Rank 1 | Pág. 138)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5618`

```text
-
gramas escritos en el lenguaje de programación estructurado; por ejemplo, Pascal.
Un algoritmo constará de dos componentes: una cabecera de programa y un bloque algoritmo. La cabecera de 
programa e
```

### Pipeline_Delta (Rank 1 | Pág. 138)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5618`

```text
-
gramas escritos en el lenguaje de programación estructurado; por ejemplo, Pascal.
Un algoritmo constará de dos componentes: una cabecera de programa y un bloque algoritmo. La cabecera de 
programa e
```

### Pipeline_Epsilon (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Score Coseno (Diagnóstico):** `0.5114`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por

```

### Pipeline_Zeta (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Score Coseno (Diagnóstico):** `0.8609`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por

```

### Pipeline_Eta (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Pág 138 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.5071`

```text
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por
read     
```

### Pipeline_Theta (Rank 1 | Pág. 138)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5618`

```text
-
gramas escritos en el lenguaje de programación estructurado; por ejemplo, Pascal.
Un algoritmo constará de dos componentes: una cabecera de programa y un bloque algoritmo. La cabecera de 
programa e
```

### Pipeline_Iota (Rank 1 | Pág. 138)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5563`

```text

gramas escritos en el lenguaje de programación estructurado; por ejemplo, Pascal.
Un algoritmo constará de dos componentes: una cabecera de programa y un bloque algoritmo . La cabecera de 
programa e
```

---

## Caso #19 [Q1A2-37] (ARQ-11)

**Consulta:** *"¿Cómo se gestiona el vector de interrupciones en el controlador programable APIC en modo protegido x86?"*

- **Páginas de evidencia teórica:** None
- **Criterio de Relevancia:** Ningún fragmento de Joyanes debe considerarse relevante (control negativo de dominio).
- **Criterio de Suficiencia:** El sistema debe abstenerse o arrojar puntajes de similitud bajos (<0.40).

### Pipeline_Alpha (Rank 1 | Pág. 43)
> **Encabezado:** `Joyanes > Página 43`  
> **Score Coseno (Diagnóstico):** `0.4036`

```text
[Página 43]
Introducción a las computadoras y los lenguajes de programación  13
incluye Celeron y Xeon), Opteron de AMD, SPARC de Sun Microsystemas, Crusoe de Transmeta, Centrino Core 2 
y Centro Core
```

### Pipeline_Beta (Rank 1 | Pág. 489)
> **Encabezado:** `Joyanes > Página 489`  
> **Score Coseno (Diagnóstico):** `0.4665`

```text
[Página 489]
Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)  459
Programa principal
X
Y
Z
Subprograma
A
Subprograma A
fin _ subprograma A
fin _ subprograma B
fin _ subprogra
```

### Pipeline_Gamma (Rank 1 | Pág. 488)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4024`

```text
amos que tenemos tres subprogramas llamados A, B y C, y supongamos también que A invoca a B y B 
invoca a C. Entonces B no terminará su trabajo hasta que C haya terminado y devuelto su control a B. De
```

### Pipeline_Delta (Rank 1 | Pág. 488)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4024`

```text
amos que tenemos tres subprogramas llamados A, B y C, y supongamos también que A invoca a B y B 
invoca a C. Entonces B no terminará su trabajo hasta que C haya terminado y devuelto su control a B. De
```

### Pipeline_Epsilon (Rank 1 | Pág. 43)
> **Encabezado:** `Joyanes > Página 43`  
> **Score Coseno (Diagnóstico):** `0.4036`

```text
[Página 43]
Introducción a las computadoras y los lenguajes de programación  13
incluye Celeron y Xeon), Opteron de AMD, SPARC de Sun Microsystemas, Crusoe de Transmeta, Centrino Core 2 
y Centro Core
```

### Pipeline_Zeta (Rank 1 | Pág. 17)
> **Encabezado:** `Joyanes > Página 17`  
> **Score Coseno (Diagnóstico):** `0.8255`

```text
[Página 17]
18.10.2. Manual de mantenimiento (documentación para programadores) .................................................. 
680
18.10.3. Reglas de documentación ...............................
```

### Pipeline_Eta (Rank 1 | Pág. 43)
> **Encabezado:** `Joyanes > Pág 43 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.3862`

```text
Introducción a las computadoras y los lenguajes de programación  13
incluye Celeron y Xeon), Opteron de AMD, SPARC de Sun Microsystemas, Crusoe de Transmeta, Centrino Core 2 
y Centro Core 2 Duo de In
```

### Pipeline_Theta (Rank 1 | Pág. 488)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4024`

```text
amos que tenemos tres subprogramas llamados A, B y C, y supongamos también que A invoca a B y B 
invoca a C. Entonces B no terminará su trabajo hasta que C haya terminado y devuelto su control a B. De
```

### Pipeline_Iota (Rank 1 | Pág. 502)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.3903`

```text
 = '*'
 fin_procedimiento
```

---

## Caso #20 [Q1A2-38] (ARQ-11)

**Consulta:** *"¿Cómo implementa el núcleo NT el algoritmo WSClock para el conjunto de trabajo de páginas en memoria virtual?"*

- **Páginas de evidencia teórica:** None
- **Criterio de Relevancia:** Ningún fragmento de Joyanes debe considerarse relevante (control negativo de dominio).
- **Criterio de Suficiencia:** El sistema debe abstenerse o arrojar puntajes de similitud bajos (<0.40).

### Pipeline_Alpha (Rank 1 | Pág. 43)
> **Encabezado:** `Joyanes > Página 43`  
> **Score Coseno (Diagnóstico):** `0.3867`

```text
[Página 43]
Introducción a las computadoras y los lenguajes de programación  13
incluye Celeron y Xeon), Opteron de AMD, SPARC de Sun Microsystemas, Crusoe de Transmeta, Centrino Core 2 
y Centro Core
```

### Pipeline_Beta (Rank 1 | Pág. 42)
> **Encabezado:** `Joyanes > Página 42`  
> **Score Coseno (Diagnóstico):** `0.528`

```text
[Página 42]
12  
Fundamentos de programación
la cual se puede acceder a la posición para almacenar o recuperar información. La información almacenada en una 
posición de memoria es su contenido. La Fi
```

### Pipeline_Gamma (Rank 1 | Pág. 43)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4279`

```text
Introducción a las computadoras y los lenguajes de programación  13
incluye Celeron y Xeon), Opteron de AMD, SPARC de Sun Microsystemas, Crusoe de Transmeta, Centrino Core 2 
y Centro Core 2 Duo de In
```

### Pipeline_Delta (Rank 1 | Pág. 43)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4279`

```text
Introducción a las computadoras y los lenguajes de programación  13
incluye Celeron y Xeon), Opteron de AMD, SPARC de Sun Microsystemas, Crusoe de Transmeta, Centrino Core 2 
y Centro Core 2 Duo de In
```

### Pipeline_Epsilon (Rank 1 | Pág. 43)
> **Encabezado:** `Joyanes > Página 43`  
> **Score Coseno (Diagnóstico):** `0.3867`

```text
[Página 43]
Introducción a las computadoras y los lenguajes de programación  13
incluye Celeron y Xeon), Opteron de AMD, SPARC de Sun Microsystemas, Crusoe de Transmeta, Centrino Core 2 
y Centro Core
```

### Pipeline_Zeta (Rank 1 | Pág. 140)
> **Encabezado:** `Joyanes > Página 140`  
> **Score Coseno (Diagnóstico):** `0.825`

```text
[Página 140]
110  
Fundamentos de programación
Las variables de caracteres se declaran de dos modos:
1. Almacenar un solo carácter.
var carácter : nombre, inicial, nota, letra
 
Se declaran nombre, in
```

### Pipeline_Eta (Rank 1 | Pág. 43)
> **Encabezado:** `Joyanes > Pág 43 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.38`

```text
Introducción a las computadoras y los lenguajes de programación  13
incluye Celeron y Xeon), Opteron de AMD, SPARC de Sun Microsystemas, Crusoe de Transmeta, Centrino Core 2 
y Centro Core 2 Duo de In
```

### Pipeline_Theta (Rank 1 | Pág. 43)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4279`

```text
Introducción a las computadoras y los lenguajes de programación  13
incluye Celeron y Xeon), Opteron de AMD, SPARC de Sun Microsystemas, Crusoe de Transmeta, Centrino Core 2 
y Centro Core 2 Duo de In
```

### Pipeline_Iota (Rank 1 | Pág. 43)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.4226`

```text
Introducción a las computadoras y los lenguajes de programación   13
incluye Celeron y Xeon), Opteron de AMD, SPARC de Sun Microsystemas, Crusoe de Transmeta, Centrino Core 2 
y Centro Core 2 Duo de I
```

---

## Caso #21 [Q1A2-39] (ARQ-12)

**Consulta:** *"manejo de pila y almacenamiento"*

- **Páginas de evidencia teórica:** [485, 505]
- **Criterio de Relevancia:** Evalúa si recupera pila como memoria de ejecución (stack) o como estructura de datos abstracta.
- **Criterio de Suficiencia:** Identifica la discriminación de contexto semántico según el capítulo.

### Pipeline_Alpha (Rank 1 | Pág. 490)
> **Encabezado:** `Joyanes > Página 490`  
> **Score Coseno (Diagnóstico):** `0.4988`

```text
[Página 490]
460  
Fundamentos de programación
  pila        : pilaletras, piladigitos, pilaotroscaracteres
  carácter    : elemento
inicio
  crear (cima1)
  crear (cima2)
  crear (cima3)
  elemento ←
```

### Pipeline_Beta (Rank 1 | Pág. 503)
> **Encabezado:** `Joyanes > Página 503`  
> **Score Coseno (Diagnóstico):** `0.5672`

```text
[Página 503]
Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)  473
procedimiento devoluciones( E/S entero: inic, vacio; E/S lista: m)
 var
  tipo_elemento: elemento
  entero  
```

### Pipeline_Gamma (Rank 1 | Pág. 489)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.558`

```text
arácter:pila
var
  entero      : cima1, cima2, cima3

```

### Pipeline_Delta (Rank 1 | Pág. 489)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.558`

```text
arácter:pila
var
  entero      : cima1, cima2, cima3

```

### Pipeline_Epsilon (Rank 1 | Pág. 490)
> **Encabezado:** `Joyanes > Página 490`  
> **Score Coseno (Diagnóstico):** `0.4988`

```text
[Página 490]
460  
Fundamentos de programación
  pila        : pilaletras, piladigitos, pilaotroscaracteres
  carácter    : elemento
inicio
  crear (cima1)
  crear (cima2)
  crear (cima3)
  elemento ←
```

### Pipeline_Zeta (Rank 1 | Pág. 13)
> **Encabezado:** `Joyanes > Página 13`  
> **Score Coseno (Diagnóstico):** `0.8462`

```text
[Página 13]
Capítulo 11. Ordenación, búsqueda y fusión externa (archivos) .......................................................................................... 
405
INTRODUCCIÓN .................
```

### Pipeline_Eta (Rank 1 | Pág. 493)
> **Encabezado:** `Joyanes > Pág 493 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.5374`

```text
Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)  463
final →
elemento
xxx
yyy
final
auxi
zzz
5.º
sig
xxx
yyy
final
auxi
nulo
nulo
nulo
nulo
zzz
6.º
auxi →
elemento si g
xxx
f
```

### Pipeline_Theta (Rank 1 | Pág. 489)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.558`

```text
arácter:pila
var
  entero      : cima1, cima2, cima3

```

### Pipeline_Iota (Rank 1 | Pág. 489)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5651`

```text
 carácter:pila
var
  entero      : cima1, cima2, cima3
```

---

## Caso #22 [Q1A2-40] (ARQ-12)

**Consulta:** *"condición de fin y salida de bloque"*

- **Páginas de evidencia teórica:** [135, 150]
- **Criterio de Relevancia:** Evalúa si recupera condiciones lógicas de estructuras condicionales vs bucles.
- **Criterio de Suficiencia:** Determina la especificidad del contexto ante términos polisémicos.

### Pipeline_Alpha (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Notas`  
> **Score Coseno (Diagnóstico):** `0.4923`

```text
[Notas]
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algor
```

### Pipeline_Beta (Rank 1 | Pág. 487)
> **Encabezado:** `Joyanes > Página 487`  
> **Score Coseno (Diagnóstico):** `0.5021`

```text
[Página 487]
Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)  457
      liberar(auxi)
      {liberar es un procedimiento para la eliminación de
      variables dinámicas}
   
```

### Pipeline_Gamma (Rank 1 | Pág. 502)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5562`

```text
d = '*'
 fin_procedimiento

```

### Pipeline_Delta (Rank 1 | Pág. 502)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5562`

```text
d = '*'
 fin_procedimiento

```

### Pipeline_Epsilon (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Notas`  
> **Score Coseno (Diagnóstico):** `0.4923`

```text
[Notas]
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algor
```

### Pipeline_Zeta (Rank 1 | Pág. 496)
> **Encabezado:** `Joyanes > Página 496`  
> **Score Coseno (Diagnóstico):** `0.8758`

```text
[Página 496]
466  
Fundamentos de programación
Cuando la cola esté vacía frente ← 0    final ← 0
procedimiento inicializar(S entero: frente,final)
 inicio
  frente ← 0
  final ← 0
 fin_procedimiento
E
```

### Pipeline_Eta (Rank 1 | Pág. 140)
> **Encabezado:** `Joyanes > Pág 140 > Código/Párrafo`  
> **Score Coseno (Diagnóstico):** `0.5146`

```text
1. Comentarios de una línea (comienzan con el carácter //)
// Programa 5.0 realizado por el Señor Mackoy
// en  Carchelejo (Jaén)en las Fiestas de Agosto 
// de Moros y Cristiano

```

### Pipeline_Theta (Rank 1 | Pág. 502)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.5562`

```text
d = '*'
 fin_procedimiento

```

### Pipeline_Iota (Rank 1 | Pág. 502)
> **Encabezado:** `Documento`  
> **Score Coseno (Diagnóstico):** `0.6164`

```text
 = '*'
 fin_procedimiento
```

---

