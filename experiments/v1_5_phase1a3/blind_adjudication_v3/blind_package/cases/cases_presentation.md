# CASOS DE ADJUDICACIÓN CIEGA V3 — FASE 1A.3 (22 CONSULTAS × 3 PIPELINES)

> **Protocolo:** Evaluación a ciegas estricta ($N=1$). Evalúe cada candidato sin conocer el modelo subyacente ni puntajes de similitud.
> **Versión del Paquete:** `3.0.0-phase1a3` | **Pipelines Adjudicables:** 3 (`Pipeline_Sigma`, `Pipeline_Tau`, `Pipeline_Upsilon`).
> **Universo Evaluado:** 22 consultas × 3 pipelines = 66 celdas candidatas Top-1.

---

## Caso #01 [Q1A2-01] (ARQ-01)

**Consulta:** *"¿Cuál es la estructura general de contenidos y preliminares presentada en el índice de Fundamentos de Programación?"*

- **Páginas de evidencia teórica:** [11, 14]
- **Criterio de Relevancia:** Recupera la descripción o listado de capítulos preliminares de la obra.
- **Criterio de Suficiencia:** Permite contrastar el esquema temático de la obra.

### Pipeline_Sigma (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Longitud de fragmento:** `1980 caracteres`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por
read      write o bien print
Nota 2
Si no se especifica el tipo de dispositivo del cual se leen o escriben datos, los dispositivos de E/S por defecto 
son el teclado y la pantalla.
3.11. ESCRITURA DE ALGORITMOS/PROGRAMAS
La escritura de un algoritmo mediante una herramienta de programación debe ser lo más clara posible y estructurada, 
de modo que su lectura facilite considerablemente el entendimiento del algoritmo y su posterior codificación en un 
lenguaje de programación.
Los algoritmos deben ser escritos en lenguajes similares a los programas. En nuestro libro utilizaremos esencial-
mente ...
```

### Pipeline_Tau (Rank 1 | Pág. 546)
> **Encabezado:** `Joyanes > Página 546`  
> **Longitud de fragmento:** `1501 caracteres`

```text
[Página 546]
516  
Fundamentos de programación
Si los árboles terminaron de recorrerse simultáneamente es que ambos tienen el mismo número de nodos y nunca ha 
sido diferente la información comparada; por tanto, la función devolverá verdad; en cualquier otro caso la función devolverá 
falso.
Diseño del algoritmo
lógico función iguales(E punt: raíz1, raíz2)
inicio
  si raíz1 = nulo entonces
    si raíz2 = nulo entonces
      devolver(verdad)
    fin_si
  si_no
    si raíz2 = nulo entonces
      devolver(falso)
    si_no
      si raíz1→.elemento <> raíz2→.elemento entonces
        devolver(falso)
      si_no
        devolver(iguales(raíz1→.izdo, raíz2→.izdo)
               y iguales(raíz1→.dcho, raíz2→.dcho))
      fin_si
    fin_si
  fin_si
fin_función
CONCEPTOS CLAVE
• Árbol.
• Árbol binar...
```

### Pipeline_Upsilon (Rank 1 | Pág. 500)
> **Encabezado:** `Joyanes > Página 500`  
> **Longitud de fragmento:** `1196 caracteres`

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
  lista: m
  carácter: opcion
inicio
  iniciar(m, vacio)
  inicializar(inic)
  repetir
    escribir('1.- Ventas')
    escribir('2.- Devoluciones')
    escribir('3.- Mostrar lista')
    escribir('4.- Fin')
    escribir('Elija opcion')
    leer(opcion)
    según_sea opcion hacer
     '1':nuevasventas(inic,vacio,m)
     '2':devoluciones(inic,vacio,m)
     '3':recorrer(inic,m)
    fin_según
  hasta_que opcion='4'
fin
procedimiento inicializar(S entero: inic);
 inicio
  inic ← 0
 fin_procedimiento
lógico función vacia(E entero: inic)
 inicio
  devolver(inic = 0)
 fin_función
procedimiento iniciar( E/S lista...
```

---

## Caso #02 [Q1A2-02] (ARQ-08)

**Consulta:** *"¿En qué página y capítulo del índice general se ubican las estructuras de datos y punteros?"*

- **Páginas de evidencia teórica:** [14, 18]
- **Criterio de Relevancia:** Identifica los números de página o capítulos correspondientes a estructuras de datos o punteros.
- **Criterio de Suficiencia:** Proporciona la ubicación precisa en el índice general.

### Pipeline_Sigma (Rank 1 | Pág. 13)
> **Encabezado:** `Joyanes > Página 13`  
> **Longitud de fragmento:** `4091 caracteres`

```text
[Página 13]
Capítulo 11. Ordenación, búsqueda y fusión externa (archivos) .......................................................................................... 
405
INTRODUCCIÓN ......................................................................................................................................................... 
405
11.1. Introducción ....................................................................................................................................................... 
406
11.2. Archivos ordenados ........................................................................................................................................... 
406
11.3. Fusión de archivos ..........................................................................................
```

### Pipeline_Tau (Rank 1 | Pág. 485)
> **Encabezado:** `Joyanes > Página 485`  
> **Longitud de fragmento:** `771 caracteres`

```text
[Página 485]
Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)  455
  procedimiento consultarCima( E punt: cima;
S tipo_elemento: elemento)
   inicio
   si no vacia (cima) entonces
      elemento ← cima→.elemento
   fin_si
   fin_procedimiento
Los elementos se incorporan siempre por un extremo, cima.
    meter(cima, elemento)
xxx
nulo
nulo
yyy
cima
cima
 
cima →
elemento cima
cima →
elemento cima
auxi
auxi
zzz
1.º
2.º
3.º
nulo
cima
cima →
elemento cima
6.º
xxx
yyy
zzz
xxx
yyy
auxi
5.º
4.º
zzz
 
1.º cima apunta al último elemento de la pila.
2.º reservar(auxi).
3.º Introducimos la información en auxi→.elemento.
4.º Hacemos que auxi→.cima apunte a donde cima.
5.º Cambiamos cima para que apunte donde auxi.
6.º La pila tiene un elemento más.
```

### Pipeline_Upsilon (Rank 1 | Pág. 13)
> **Encabezado:** `Joyanes > Página 13`  
> **Longitud de fragmento:** `4091 caracteres`

```text
[Página 13]
Capítulo 11. Ordenación, búsqueda y fusión externa (archivos) .......................................................................................... 
405
INTRODUCCIÓN ......................................................................................................................................................... 
405
11.1. Introducción ....................................................................................................................................................... 
406
11.2. Archivos ordenados ........................................................................................................................................... 
406
11.3. Fusión de archivos ..........................................................................................
```

---

## Caso #03 [Q1A2-03] (ARQ-01)

**Consulta:** *"¿Qué es un algoritmo según Joyanes Aguilar y cuáles son sus características básicas?"*

- **Páginas de evidencia teórica:** [35, 40]
- **Criterio de Relevancia:** Define algoritmo como secuencia finita de pasos o instrucciones no ambiguas.
- **Criterio de Suficiencia:** Detalla las características esenciales (precisión, finitud, definición).

### Pipeline_Sigma (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Longitud de fragmento:** `1980 caracteres`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por
read      write o bien print
Nota 2
Si no se especifica el tipo de dispositivo del cual se leen o escriben datos, los dispositivos de E/S por defecto 
son el teclado y la pantalla.
3.11. ESCRITURA DE ALGORITMOS/PROGRAMAS
La escritura de un algoritmo mediante una herramienta de programación debe ser lo más clara posible y estructurada, 
de modo que su lectura facilite considerablemente el entendimiento del algoritmo y su posterior codificación en un 
lenguaje de programación.
Los algoritmos deben ser escritos en lenguajes similares a los programas. En nuestro libro utilizaremos esencial-
mente ...
```

### Pipeline_Tau (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Longitud de fragmento:** `1980 caracteres`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por
read      write o bien print
Nota 2
Si no se especifica el tipo de dispositivo del cual se leen o escriben datos, los dispositivos de E/S por defecto 
son el teclado y la pantalla.
3.11. ESCRITURA DE ALGORITMOS/PROGRAMAS
La escritura de un algoritmo mediante una herramienta de programación debe ser lo más clara posible y estructurada, 
de modo que su lectura facilite considerablemente el entendimiento del algoritmo y su posterior codificación en un 
lenguaje de programación.
Los algoritmos deben ser escritos en lenguajes similares a los programas. En nuestro libro utilizaremos esencial-
mente ...
```

### Pipeline_Upsilon (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Longitud de fragmento:** `1980 caracteres`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por
read      write o bien print
Nota 2
Si no se especifica el tipo de dispositivo del cual se leen o escriben datos, los dispositivos de E/S por defecto 
son el teclado y la pantalla.
3.11. ESCRITURA DE ALGORITMOS/PROGRAMAS
La escritura de un algoritmo mediante una herramienta de programación debe ser lo más clara posible y estructurada, 
de modo que su lectura facilite considerablemente el entendimiento del algoritmo y su posterior codificación en un 
lenguaje de programación.
Los algoritmos deben ser escritos en lenguajes similares a los programas. En nuestro libro utilizaremos esencial-
mente ...
```

---

## Caso #04 [Q1A2-04] (ARQ-04)

**Consulta:** *"¿Cuáles son las fases de resolución de un problema mediante computadora según el texto?"*

- **Páginas de evidencia teórica:** [38, 45]
- **Criterio de Relevancia:** Enumera las etapas principales desde el análisis hasta la verificación del programa.
- **Criterio de Suficiencia:** Permite reconstruir la secuencia completa sin omitir pasos críticos.

### Pipeline_Sigma (Rank 1 | Pág. 148)
> **Encabezado:** `Joyanes > Página 148`  
> **Longitud de fragmento:** `1754 caracteres`

```text
[Página 148]
118  
Fundamentos de programación
3.13. Determinar el mayor de tres números enteros.
Solución
Los pasos a seguir son:
1. Comparar el primero y el segundo entero, deduciendo cuál es el mayor.
2. Comparar el mayor anterior con el tercero y deducir cuál es el mayor. Este será el resultado.
Los pasos anteriores se pueden descomponer en otros pasos más simples en lo que se denomina refinamiento del algo-
ritmo:
1. Obtener el primer número (entrada), denominarlo NUM1.
2. Obtener el segundo número (entrada), denominarlo NUM2.
3. Comparar NUM1 con NUM2 y seleccionar el mayor; si los dos enteros son iguales, seleccionar NUM1. Llamar a este 
número MAYOR.
4. Obtener el tercer número (entrada) y denominarlo NUM3.
5. Comparar MAYOR con NUM3 y seleccionar el mayor; si los dos enteros son i...
```

### Pipeline_Tau (Rank 1 | Pág. 45)
> **Encabezado:** `Joyanes > Página 45`  
> **Longitud de fragmento:** `1891 caracteres`

```text
[Página 45]
Introducción a las computadoras y los lenguajes de programación  15
1.3. REPRESENTACIÓN DE LA INFORMACIÓN EN LAS COMPUTADORAS
Una computadora es un sistema para procesar información de modo automático. Un tema vital en el proceso de fun-
cionamiento de una computadora es estudiar la forma de representación de la información en dicha computadora. Es 
necesario considerar cómo se puede codificar la información en patrones de bits que sean fácilmente almacenables 
y procesables por los elementos internos de la computadora.
Las formas de información más significativas son: textos, sonidos, imágenes y valores numéricos y, cada una de 
ellas presentan peculiaridades distintas. Otros temas importantes en el campo de la programación se refieren a los 
métodos de detección de errores qu...
```

### Pipeline_Upsilon (Rank 1 | Pág. 45)
> **Encabezado:** `Joyanes > Página 45`  
> **Longitud de fragmento:** `1891 caracteres`

```text
[Página 45]
Introducción a las computadoras y los lenguajes de programación  15
1.3. REPRESENTACIÓN DE LA INFORMACIÓN EN LAS COMPUTADORAS
Una computadora es un sistema para procesar información de modo automático. Un tema vital en el proceso de fun-
cionamiento de una computadora es estudiar la forma de representación de la información en dicha computadora. Es 
necesario considerar cómo se puede codificar la información en patrones de bits que sean fácilmente almacenables 
y procesables por los elementos internos de la computadora.
Las formas de información más significativas son: textos, sonidos, imágenes y valores numéricos y, cada una de 
ellas presentan peculiaridades distintas. Otros temas importantes en el campo de la programación se refieren a los 
métodos de detección de errores qu...
```

---

## Caso #05 [Q1A2-05] (ARQ-02)

**Consulta:** *"¿Cuál es la diferencia entre el diseño descendente (top-down) y el refinamiento por pasos?"*

- **Páginas de evidencia teórica:** [40, 45]
- **Criterio de Relevancia:** Explica la descomposición modular y la especificación sucesiva de detalles.
- **Criterio de Suficiencia:** Contrasta adecuadamente ambos conceptos según la metodología expuesta.

### Pipeline_Sigma (Rank 1 | Pág. 148)
> **Encabezado:** `Joyanes > Página 148`  
> **Longitud de fragmento:** `1754 caracteres`

```text
[Página 148]
118  
Fundamentos de programación
3.13. Determinar el mayor de tres números enteros.
Solución
Los pasos a seguir son:
1. Comparar el primero y el segundo entero, deduciendo cuál es el mayor.
2. Comparar el mayor anterior con el tercero y deducir cuál es el mayor. Este será el resultado.
Los pasos anteriores se pueden descomponer en otros pasos más simples en lo que se denomina refinamiento del algo-
ritmo:
1. Obtener el primer número (entrada), denominarlo NUM1.
2. Obtener el segundo número (entrada), denominarlo NUM2.
3. Comparar NUM1 con NUM2 y seleccionar el mayor; si los dos enteros son iguales, seleccionar NUM1. Llamar a este 
número MAYOR.
4. Obtener el tercer número (entrada) y denominarlo NUM3.
5. Comparar MAYOR con NUM3 y seleccionar el mayor; si los dos enteros son i...
```

### Pipeline_Tau (Rank 1 | Pág. 486)
> **Encabezado:** `Joyanes > Página 486`  
> **Longitud de fragmento:** `866 caracteres`

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
   auxi→.cima ← cima
   cima ← auxi
 fin_procedimiento
Los elementos se recuperan en orden inverso a como fueron introducidos
Sacar(cima, elemento)
nulo
xxx
elemento cima
cima →
cima →
yyy
auxi
1.º
2.º
zzz
cima
3.º
cima →
elemento cima
xxx
yyy
4.º
5.º
cima
auxi
zzz
cima →
elemento cima
1.º cima apunta al último elemento de la pila
2.º Hacemos que auxi apunte adonde apuntaba cima
3.º Y que cima pase a apuntar adonde cima→.cima
4.º liberar(auxi)
5.º La pila tiene un elemento menos
procedimiento sacar(E/S punt:cima; S tipo_elemento: elemento)
 var 
   punt: auxi
 inicio
    si no vacia (cima) entonces
      aux...
```

### Pipeline_Upsilon (Rank 1 | Pág. 486)
> **Encabezado:** `Joyanes > Página 486`  
> **Longitud de fragmento:** `866 caracteres`

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
   auxi→.cima ← cima
   cima ← auxi
 fin_procedimiento
Los elementos se recuperan en orden inverso a como fueron introducidos
Sacar(cima, elemento)
nulo
xxx
elemento cima
cima →
cima →
yyy
auxi
1.º
2.º
zzz
cima
3.º
cima →
elemento cima
xxx
yyy
4.º
5.º
cima
auxi
zzz
cima →
elemento cima
1.º cima apunta al último elemento de la pila
2.º Hacemos que auxi apunte adonde apuntaba cima
3.º Y que cima pase a apuntar adonde cima→.cima
4.º liberar(auxi)
5.º La pila tiene un elemento menos
procedimiento sacar(E/S punt:cima; S tipo_elemento: elemento)
 var 
   punt: auxi
 inicio
    si no vacia (cima) entonces
      aux...
```

---

## Caso #06 [Q1A2-06] (ARQ-06)

**Consulta:** *"¿Cómo se describe la estructura jerárquica de un programa estructurado?"*

- **Páginas de evidencia teórica:** [42, 45]
- **Criterio de Relevancia:** Describe la organización modular en niveles de abstracción.
- **Criterio de Suficiencia:** Explica la interacción funcional entre el programa principal y subprogramas.

### Pipeline_Sigma (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Longitud de fragmento:** `1980 caracteres`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por
read      write o bien print
Nota 2
Si no se especifica el tipo de dispositivo del cual se leen o escriben datos, los dispositivos de E/S por defecto 
son el teclado y la pantalla.
3.11. ESCRITURA DE ALGORITMOS/PROGRAMAS
La escritura de un algoritmo mediante una herramienta de programación debe ser lo más clara posible y estructurada, 
de modo que su lectura facilite considerablemente el entendimiento del algoritmo y su posterior codificación en un 
lenguaje de programación.
Los algoritmos deben ser escritos en lenguajes similares a los programas. En nuestro libro utilizaremos esencial-
mente ...
```

### Pipeline_Tau (Rank 1 | Pág. 547)
> **Encabezado:** `Joyanes > Página 547`  
> **Longitud de fragmento:** `1697 caracteres`

```text
[Página 547]
Estructura de datos no lineales (árboles y grafos)  517
presentan estructuras jerárquicas con limitaciones de dos sub-
árboles por cada nodo. Si se eliminan las restricciones de 
que cada nodo puede apuntar a dos nodos —como máxi-
mo— y que cada nodo puede estar apuntado por otro nodo 
—como máximo— nos encontramos con un grafo. Ejem-
plos de grafos en la vida real los tenemos en la red de ca-
rreteras de un estado o región, la red de enlaces ferroviarios 
o aéreos nacionales, etc.
Un grafo G consta de dos conjuntos (G = {V, E}): 
un conjunto V de vértices o nodos y un conjunto E de aris-
tas (parejas de vértices distintos) que conectan los vértices. 
Si las parejas no están ordenadas, G se denomina grafo no 
dirigido; si los pares están ordenados, entonces G se deno-
mina gra...
```

### Pipeline_Upsilon (Rank 1 | Pág. 37)
> **Encabezado:** `Joyanes > Página 37`  
> **Longitud de fragmento:** `2051 caracteres`

```text
[Página 37]
Introducción a las computadoras y los lenguajes de programación  7
1.2. ORGANIZACIÓN FÍSICA DE UNA COMPUTADORA
Los dos componentes principales de una computadora son: hardware y software. Hardware es el equipo físico o los 
dispositivos asociados con una computadora. Sin embargo, para ser útil una computadora necesita además del equipo 
físico, un conjunto de instrucciones dadas. El conjunto de instrucciones que indican a la computadora aquello que 
deben hacer se denomina software o programas y se escriben por programadores. Este libro se centra en la ense-
ñanza y aprendizaje de la programación o proceso de escribir programas.
Una red consta de un número de computadoras conectadas entre sí directamente o a través de otra computadora 
central (llamada servidor), de modo que pu...
```

---

## Caso #07 [Q1A2-07] (ARQ-01)

**Consulta:** *"¿Cómo se define y formaliza la estructura de selección doble (si-entonces-sino) en pseudocódigo?"*

- **Páginas de evidencia teórica:** [135, 142]
- **Criterio de Relevancia:** Presenta la sintaxis o reglas semánticas de la bifurcación lógica doble.
- **Criterio de Suficiencia:** Muestra el pseudocódigo formal y las ramas verdadera/falsa.

### Pipeline_Sigma (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Notas`  
> **Longitud de fragmento:** `981 caracteres`

```text
[Notas]
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algoritmo
    .
    .
    .
  <sentencia Sn>
fin
Notas
1. En ocasiones, la declaración de constantes y variables las omitiremos o se describirán en una tabla de varia-
bles que hace sus mismas funciones.
2. Las cadenas de caracteres se encerrarán entre comillas simples.
3. Utilizar siempre sangrías en los bucles o en aquellas instrucciones que proporcionen legibilidad al programa, 
como inicio y fin.
MODELO PROPUESTO DE ALGORITMO
algoritmo raices
// resuelve una ecuación de 2.º grado
var
  real : a, b, c
inicio
  leer(a, b, c)
  d ← b ^ 2 - 4 * a * c
  si d < 0 entonces
    escribir('raices complej...
```

### Pipeline_Tau (Rank 1 | Pág. 503)
> **Encabezado:** `Joyanes > Página 503`  
> **Longitud de fragmento:** `1809 caracteres`

```text
[Página 503]
Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)  473
procedimiento devoluciones( E/S entero: inic, vacio; E/S lista: m)
 var
  tipo_elemento: elemento
  entero       : posic, anterior
  entero       : cantidad
  lógico       : encontrado
 inicio
   si no vacia(inic) entonces
     escribir('Introduzca un * en el código para terminar')
     escribir('Código: ')
     leer(elemento.cod)
   si_no
     escribir('No hay ventas, no puede haber devoluciones')
   fin_si
   mientras (elemento.cod<>'*' ) y no vacia(inic) hacer
     consultar(inic, posic, anterior, elemento, encontrado, m)
     si encontrado entonces
       repetir
         escribir('Deme cantidad devuelta ')
         leer(cantidad)
         si cantidad > m[posic].elemento.cantidad entonces
      ...
```

### Pipeline_Upsilon (Rank 1 | Pág. 499)
> **Encabezado:** `Joyanes > Página 499`  
> **Longitud de fragmento:** `1861 caracteres`

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
Existen dos variantes de la doble cola:
• Doble cola de entrada restringida: acepta inserciones sólo al final de la cola.
• Doble cola de salida restringida: acepta eliminaciones sólo al frente de la cola.
Inserción
IZQ  =  5
DCHA = 25
Eliminación
x
5
25
x
Los procedimientos de inserción y eliminación de las dobles colas son variantes de los procedimientos estudiados 
para las colas simples y se dejan como ejercicio al lector.
ACTIVIDADES DE PROGRAMACIÓN RESUELTAS
12.1. Una tienda de artículos deportivos desea almacenar en una lista enlazada, con un único elemento por producto, la 
siguiente información sobre...
```

---

## Caso #08 [Q1A2-08] (ARQ-05)

**Consulta:** *"¿Cuál es la sintaxis de la sentencia de selección múltiple según_sea (switch) y cómo se maneja la opción por defecto?"*

- **Páginas de evidencia teórica:** [142, 148]
- **Criterio de Relevancia:** Identifica los bloques de selección múltiple y la cláusula alternativa (de otro modo / default).
- **Criterio de Suficiencia:** Permite reproducir la estructura sintáctica completa sin ambigüedades.

### Pipeline_Sigma (Rank 1 | Pág. 141)
> **Encabezado:** `Joyanes > Nota`  
> **Longitud de fragmento:** `1380 caracteres`

```text
[Nota]
Estructura general de un programa  111
2. Comentarios multilínea (comienzan con los caracteres /* y terminan con los caracteres  */, todo lo encerrado 
entre ambos juegos de caracteres son comentarios)
/* El maestro Mackoy estudió el Bachiller en el mismo Instituto donde dio clase 
Don Antonio Machado, el poeta */   
Java
1. Comentarios de una línea
// comentarios sobre la Ley de Protección de Datos
2. Comentarios multilíneas
/* El pueblo de Mr. Mackoy está en Sierra Mágina, y produce uno 
de los mejores aceites de oliva del mundo mundial             */
3. Documentación de clases 
/**
        Documentación de la clase
*/
Pascal
Los comentarios se encierran entre los símbolos
(*               *)
o bien
{               }
(* autor J.R. Mackoy *)
{subrutina ordenacion}
Modula-2
Los come...
```

### Pipeline_Tau (Rank 1 | Pág. 17)
> **Encabezado:** `Joyanes > Página 17`  
> **Longitud de fragmento:** `3717 caracteres`

```text
[Página 17]
18.10.2. Manual de mantenimiento (documentación para programadores) .................................................. 
680
18.10.3. Reglas de documentación ................................................................................................................ 
681
18.11. Depuración ....................................................................................................................................................... 
681
18.11.1. Localización y reparación de errores ............................................................................................... 
681
18.11.2. Depuración de sentencias si-entonces-sino ..................................................................................... 
682
18.11.3. Los equipos de programación ...............
```

### Pipeline_Upsilon (Rank 1 | Pág. 136)
> **Encabezado:** `Joyanes > Página 136`  
> **Longitud de fragmento:** `1270 caracteres`

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
o si lo prefiere utilizando el signo de asignación (=) de C, C++, Java o C#.
Caso especial
Los lenguajes C, C++, Java y C# permiten realizar múltiples asignaciones en una sola sentencia
a = b = c = d = e = n +35;
Tabla 3.10. Operadores aritméticos de asignación múltiple
Operador de asignación
Ejemplo
Operación
Resultado
Entero a = 3, b= 5, c = 4, d = 6, e = 10
*=
a += 8
a = a+8
a = 11
-=
b -= 5
b = b-5
b = 0
*=
c *= 4
c = c*4
c = 16
/=
d /= 3
d = d/3
d = 2
%=
e %= 9
e = e%9
e = 1
 
3.9.5. Conversión de tipo
En las asignaciones no se pueden asignar valores a una variable de un tipo incompatible al suyo. Se presenta...
```

---

## Caso #09 [Q1A2-09] (ARQ-04)

**Consulta:** *"¿Qué algoritmo o pseudocódigo se presenta para evaluar si un número entero es par o impar?"*

- **Páginas de evidencia teórica:** [138, 145]
- **Criterio de Relevancia:** Recupera el pseudocódigo o lógica que utiliza el operador módulo para determinar paridad.
- **Criterio de Suficiencia:** Proporciona el algoritmo funcional completo.

### Pipeline_Sigma (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Notas`  
> **Longitud de fragmento:** `981 caracteres`

```text
[Notas]
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algoritmo
    .
    .
    .
  <sentencia Sn>
fin
Notas
1. En ocasiones, la declaración de constantes y variables las omitiremos o se describirán en una tabla de varia-
bles que hace sus mismas funciones.
2. Las cadenas de caracteres se encerrarán entre comillas simples.
3. Utilizar siempre sangrías en los bucles o en aquellas instrucciones que proporcionen legibilidad al programa, 
como inicio y fin.
MODELO PROPUESTO DE ALGORITMO
algoritmo raices
// resuelve una ecuación de 2.º grado
var
  real : a, b, c
inicio
  leer(a, b, c)
  d ← b ^ 2 - 4 * a * c
  si d < 0 entonces
    escribir('raices complej...
```

### Pipeline_Tau (Rank 1 | Pág. 148)
> **Encabezado:** `Joyanes > Página 148`  
> **Longitud de fragmento:** `1754 caracteres`

```text
[Página 148]
118  
Fundamentos de programación
3.13. Determinar el mayor de tres números enteros.
Solución
Los pasos a seguir son:
1. Comparar el primero y el segundo entero, deduciendo cuál es el mayor.
2. Comparar el mayor anterior con el tercero y deducir cuál es el mayor. Este será el resultado.
Los pasos anteriores se pueden descomponer en otros pasos más simples en lo que se denomina refinamiento del algo-
ritmo:
1. Obtener el primer número (entrada), denominarlo NUM1.
2. Obtener el segundo número (entrada), denominarlo NUM2.
3. Comparar NUM1 con NUM2 y seleccionar el mayor; si los dos enteros son iguales, seleccionar NUM1. Llamar a este 
número MAYOR.
4. Obtener el tercer número (entrada) y denominarlo NUM3.
5. Comparar MAYOR con NUM3 y seleccionar el mayor; si los dos enteros son i...
```

### Pipeline_Upsilon (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Longitud de fragmento:** `1980 caracteres`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por
read      write o bien print
Nota 2
Si no se especifica el tipo de dispositivo del cual se leen o escriben datos, los dispositivos de E/S por defecto 
son el teclado y la pantalla.
3.11. ESCRITURA DE ALGORITMOS/PROGRAMAS
La escritura de un algoritmo mediante una herramienta de programación debe ser lo más clara posible y estructurada, 
de modo que su lectura facilite considerablemente el entendimiento del algoritmo y su posterior codificación en un 
lenguaje de programación.
Los algoritmos deben ser escritos en lenguajes similares a los programas. En nuestro libro utilizaremos esencial-
mente ...
```

---

## Caso #10 [Q1A2-10] (ARQ-07)

**Consulta:** *"¿Por qué es necesario delimitar explícitamente las estructuras de control anidadas en programación estructurada?"*

- **Páginas de evidencia teórica:** [140, 150]
- **Criterio de Relevancia:** Explica la resolución de ambigüedad del 'else colgante' o delimitación de bloques.
- **Criterio de Suficiencia:** Aporta justificación conceptual sólida según el texto.

### Pipeline_Sigma (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Longitud de fragmento:** `1980 caracteres`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por
read      write o bien print
Nota 2
Si no se especifica el tipo de dispositivo del cual se leen o escriben datos, los dispositivos de E/S por defecto 
son el teclado y la pantalla.
3.11. ESCRITURA DE ALGORITMOS/PROGRAMAS
La escritura de un algoritmo mediante una herramienta de programación debe ser lo más clara posible y estructurada, 
de modo que su lectura facilite considerablemente el entendimiento del algoritmo y su posterior codificación en un 
lenguaje de programación.
Los algoritmos deben ser escritos en lenguajes similares a los programas. En nuestro libro utilizaremos esencial-
mente ...
```

### Pipeline_Tau (Rank 1 | Pág. 547)
> **Encabezado:** `Joyanes > Página 547`  
> **Longitud de fragmento:** `1697 caracteres`

```text
[Página 547]
Estructura de datos no lineales (árboles y grafos)  517
presentan estructuras jerárquicas con limitaciones de dos sub-
árboles por cada nodo. Si se eliminan las restricciones de 
que cada nodo puede apuntar a dos nodos —como máxi-
mo— y que cada nodo puede estar apuntado por otro nodo 
—como máximo— nos encontramos con un grafo. Ejem-
plos de grafos en la vida real los tenemos en la red de ca-
rreteras de un estado o región, la red de enlaces ferroviarios 
o aéreos nacionales, etc.
Un grafo G consta de dos conjuntos (G = {V, E}): 
un conjunto V de vértices o nodos y un conjunto E de aris-
tas (parejas de vértices distintos) que conectan los vértices. 
Si las parejas no están ordenadas, G se denomina grafo no 
dirigido; si los pares están ordenados, entonces G se deno-
mina gra...
```

### Pipeline_Upsilon (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Longitud de fragmento:** `1980 caracteres`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por
read      write o bien print
Nota 2
Si no se especifica el tipo de dispositivo del cual se leen o escriben datos, los dispositivos de E/S por defecto 
son el teclado y la pantalla.
3.11. ESCRITURA DE ALGORITMOS/PROGRAMAS
La escritura de un algoritmo mediante una herramienta de programación debe ser lo más clara posible y estructurada, 
de modo que su lectura facilite considerablemente el entendimiento del algoritmo y su posterior codificación en un 
lenguaje de programación.
Los algoritmos deben ser escritos en lenguajes similares a los programas. En nuestro libro utilizaremos esencial-
mente ...
```

---

## Caso #11 [Q1A2-11] (ARQ-01)

**Consulta:** *"¿Cuál es la función del operador de dirección & y del operador de indirección * en punteros de C?"*

- **Páginas de evidencia teórica:** [485, 492]
- **Criterio de Relevancia:** Distingue entre obtener la dirección en memoria (&) y acceder al valor apuntado (*).
- **Criterio de Suficiencia:** Define con precisión la semántica de ambos operadores en C.

### Pipeline_Sigma (Rank 1 | Pág. 136)
> **Encabezado:** `Joyanes > Página 136`  
> **Longitud de fragmento:** `1270 caracteres`

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
o si lo prefiere utilizando el signo de asignación (=) de C, C++, Java o C#.
Caso especial
Los lenguajes C, C++, Java y C# permiten realizar múltiples asignaciones en una sola sentencia
a = b = c = d = e = n +35;
Tabla 3.10. Operadores aritméticos de asignación múltiple
Operador de asignación
Ejemplo
Operación
Resultado
Entero a = 3, b= 5, c = 4, d = 6, e = 10
*=
a += 8
a = a+8
a = 11
-=
b -= 5
b = b-5
b = 0
*=
c *= 4
c = c*4
c = 16
/=
d /= 3
d = d/3
d = 2
%=
e %= 9
e = e%9
e = 1
 
3.9.5. Conversión de tipo
En las asignaciones no se pueden asignar valores a una variable de un tipo incompatible al suyo. Se presenta...
```

### Pipeline_Tau (Rank 1 | Pág. 136)
> **Encabezado:** `Joyanes > Página 136`  
> **Longitud de fragmento:** `1270 caracteres`

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
o si lo prefiere utilizando el signo de asignación (=) de C, C++, Java o C#.
Caso especial
Los lenguajes C, C++, Java y C# permiten realizar múltiples asignaciones en una sola sentencia
a = b = c = d = e = n +35;
Tabla 3.10. Operadores aritméticos de asignación múltiple
Operador de asignación
Ejemplo
Operación
Resultado
Entero a = 3, b= 5, c = 4, d = 6, e = 10
*=
a += 8
a = a+8
a = 11
-=
b -= 5
b = b-5
b = 0
*=
c *= 4
c = c*4
c = 16
/=
d /= 3
d = d/3
d = 2
%=
e %= 9
e = e%9
e = 1
 
3.9.5. Conversión de tipo
En las asignaciones no se pueden asignar valores a una variable de un tipo incompatible al suyo. Se presenta...
```

### Pipeline_Upsilon (Rank 1 | Pág. 136)
> **Encabezado:** `Joyanes > Página 136`  
> **Longitud de fragmento:** `1270 caracteres`

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
o si lo prefiere utilizando el signo de asignación (=) de C, C++, Java o C#.
Caso especial
Los lenguajes C, C++, Java y C# permiten realizar múltiples asignaciones en una sola sentencia
a = b = c = d = e = n +35;
Tabla 3.10. Operadores aritméticos de asignación múltiple
Operador de asignación
Ejemplo
Operación
Resultado
Entero a = 3, b= 5, c = 4, d = 6, e = 10
*=
a += 8
a = a+8
a = 11
-=
b -= 5
b = b-5
b = 0
*=
c *= 4
c = c*4
c = 16
/=
d /= 3
d = d/3
d = 2
%=
e %= 9
e = e%9
e = 1
 
3.9.5. Conversión de tipo
En las asignaciones no se pueden asignar valores a una variable de un tipo incompatible al suyo. Se presenta...
```

---

## Caso #12 [Q1A2-12] (ARQ-05)

**Consulta:** *"¿Cómo se declara un puntero a una estructura struct y cómo se accede a sus miembros con el operador flecha ->?"*

- **Páginas de evidencia teórica:** [490, 498]
- **Criterio de Relevancia:** Muestra la notación `ptr->campo` o `(*ptr).campo` para structs.
- **Criterio de Suficiencia:** Incluye ejemplo de sintaxis en lenguaje C según el texto.

### Pipeline_Sigma (Rank 1 | Pág. 492)
> **Encabezado:** `Joyanes > Página 492`  
> **Longitud de fragmento:** `1608 caracteres`

```text
[Página 492]
462  
Fundamentos de programación
• Acceder al primer elemento de la cola.
• Añadir un elemento al final de cola.
• Eliminar el primer elemento de la cola.
• Vaciar la cola.
• Verificar el estado de la cola: vacía o llena.
Implementación con estructuras dinámicas
Aunque, como posteriormente veremos, las colas se pueden simular mediante un array y dos variables numéricas 
(frente, final), deberemos, si el lenguaje lo permite, implementarlas mediante punteros.
En una cola las eliminaciones se realizarán por el extremo denominado frente y las inserciones por el final.
Para la manipulación de una cola necesitaremos los subprogramas: inicializar o crear, consultarPrime-
ro, poner o meter, quitar o sacar y vacia o colaVacia y los siguientes tipos de datos:
tipo
 puntero_a nodo : pun...
```

### Pipeline_Tau (Rank 1 | Pág. 545)
> **Encabezado:** `Joyanes > Página 545`  
> **Longitud de fragmento:** `1542 caracteres`

```text
[Página 545]
Estructura de datos no lineales (árboles y grafos)  515
        raíz ← auxi
      si_no
        si mayor(a[ant].elemento, elemento) entonces
          a[ant].izdo ← auxi
        si_no
          a[ant].dcho ← auxi
        fin_si
      fin_si
    fin_si
  fin_si
fin_procedimiento
procedimiento listado (E arr: a; E entero: raíz)
var
  entero: cont
inicio
  escribir ('inorden: ')
  cont ← 0
  inorden (a, raíz, cont)
  escribir('El número de nodos es ', cont)
fin_procedimiento
13.4. Escribir un procedimiento que permita contar las hojas de un árbol mediante estructuras dinámicas.
Análisis del problema
Recorrer el árbol, contando, únicamente, los nodos que no tienen hijos.
Diseño del algoritmo
procedimiento contarhojas(E punt: raíz;  E/S entero: cont)
inicio
  si raíz <> nulo entonc...
```

### Pipeline_Upsilon (Rank 1 | Pág. 485)
> **Encabezado:** `Joyanes > Página 485`  
> **Longitud de fragmento:** `771 caracteres`

```text
[Página 485]
Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)  455
  procedimiento consultarCima( E punt: cima;
S tipo_elemento: elemento)
   inicio
   si no vacia (cima) entonces
      elemento ← cima→.elemento
   fin_si
   fin_procedimiento
Los elementos se incorporan siempre por un extremo, cima.
    meter(cima, elemento)
xxx
nulo
nulo
yyy
cima
cima
 
cima →
elemento cima
cima →
elemento cima
auxi
auxi
zzz
1.º
2.º
3.º
nulo
cima
cima →
elemento cima
6.º
xxx
yyy
zzz
xxx
yyy
auxi
5.º
4.º
zzz
 
1.º cima apunta al último elemento de la pila.
2.º reservar(auxi).
3.º Introducimos la información en auxi→.elemento.
4.º Hacemos que auxi→.cima apunte a donde cima.
5.º Cambiamos cima para que apunte donde auxi.
6.º La pila tiene un elemento más.
```

---

## Caso #13 [Q1A2-13] (ARQ-04)

**Consulta:** *"¿Cómo se asigna memoria dinámica mediante malloc y cómo se libera con free en C según Joyanes?"*

- **Páginas de evidencia teórica:** [495, 505]
- **Criterio de Relevancia:** Describe la llamada a malloc con sizeof y la posterior invocación de free.
- **Criterio de Suficiencia:** Explica el ciclo de reserva y liberación de memoria.

### Pipeline_Sigma (Rank 1 | Pág. 492)
> **Encabezado:** `Joyanes > Página 492`  
> **Longitud de fragmento:** `1608 caracteres`

```text
[Página 492]
462  
Fundamentos de programación
• Acceder al primer elemento de la cola.
• Añadir un elemento al final de cola.
• Eliminar el primer elemento de la cola.
• Vaciar la cola.
• Verificar el estado de la cola: vacía o llena.
Implementación con estructuras dinámicas
Aunque, como posteriormente veremos, las colas se pueden simular mediante un array y dos variables numéricas 
(frente, final), deberemos, si el lenguaje lo permite, implementarlas mediante punteros.
En una cola las eliminaciones se realizarán por el extremo denominado frente y las inserciones por el final.
Para la manipulación de una cola necesitaremos los subprogramas: inicializar o crear, consultarPrime-
ro, poner o meter, quitar o sacar y vacia o colaVacia y los siguientes tipos de datos:
tipo
 puntero_a nodo : pun...
```

### Pipeline_Tau (Rank 1 | Pág. 497)
> **Encabezado:** `Joyanes > Página 497`  
> **Longitud de fragmento:** `1629 caracteres`

```text
[Página 497]
Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)  467
2.º Reestructuración.
 
Cuando final llega al máximo de elementos se desplazan las componentes ocupadas hacia atrás las posicio-
nes necesarias para que el principio coincida con el principio de la tabla.
3.º Mediante un array circular.
 
Un array circular es aquel en el que se considera que la componente primera sigue a la componente última.
Esta implementación obliga a dejar siempre una posición libre para separar el principio y el final del array.
Evidentemente, seguirá existiendo la limitación de que pueda llenarse completamente el array, Max-1 
posiciones ocupadas.
12.8.2. Aprovechamiento de la memoria
El mejor método para evitar el desaprovechamiento de espacio es el diseño de la cola mediante...
```

### Pipeline_Upsilon (Rank 1 | Pág. 502)
> **Encabezado:** `Joyanes > Página 502`  
> **Longitud de fragmento:** `1839 caracteres`

```text
[Página 502]
472  
Fundamentos de programación
procedimiento liberar(E/S entero: posic; E/S lista: m;
                      E/S entero: vacio)
 inicio
  m[posic].sig ← vacio
  vacio ← posic
 fin_procedimiento
procedimiento suprimir(E/S entero: inic, anterior, posic; 
                       E/S lista: m; E/S entero: vacio)
 inicio
  si anterior=0 entonces
     inic ← m[posic].sig
  si_no
     m[anterior].sig ← m[posic].sig
  fin_si
  liberar(posic,m,vacio)
  anterior ← 0
  posic ← inic
 fin_procedimiento
procedimiento nuevasventas(E/S entero: inic, vacio; E/S lista: m)
 var
  tipo_elemento: elemento
  lógico: encontrado
  entero: anterior, posic
 inicio
   repetir
     escribir('Introduzca * en el código para terminar')
     escribir('Código:   ')
     leer(elemento.cod)
     si elemento.co...
```

---

## Caso #14 [Q1A2-14] (ARQ-03)

**Consulta:** *"¿En qué se diferencia el paso de parámetros por valor del paso por referencia mediante punteros?"*

- **Páginas de evidencia teórica:** [488, 496]
- **Criterio de Relevancia:** Explica que el paso por valor copia el dato mientras que por referencia pasa la dirección.
- **Criterio de Suficiencia:** Demuestra el impacto en la modificación de la variable original.

### Pipeline_Sigma (Rank 1 | Pág. 146)
> **Encabezado:** `Joyanes > Página 146`  
> **Longitud de fragmento:** `1470 caracteres`

```text
[Página 146]
116  
Fundamentos de programación
3.8. Cómo se intercambian los valores de dos variables, A y B.
Solución
Con el ejercicio se ha visto cómo se pueden intercambiar los valores de una variable mediante las  instrucciones:
A ← B
B ← A
El procedimiento para conseguir intercambiar los valores de dos variables entre sí debe recurrir a una variable AUX y a 
las instrucciones de asignación siguientes:
AUX ← A
  A ← B
  B ← AUX
Veámoslo con un ejemplo:
a ← 10
B ← 5
Instrucción
A
B
AUX
Observaciones
  A ← 10
10
--
--
  B ← 5
10
5
--
AUX ← A
10
5
10
La variable AUX toma el valor de A
  A ← B
5
5
10
A toma el valor de B, 5
  B ← AUX
 5
10
10
B toma el valor inicial de A, 10
Ahora A = 5 y B = 10.
3.9. Deducir el valor que toma la variable tras la ejecución de las instrucciones:
A ← 4
B ← A...
```

### Pipeline_Tau (Rank 1 | Pág. 42)
> **Encabezado:** `Joyanes > Página 42`  
> **Longitud de fragmento:** `1786 caracteres`

```text
[Página 42]
12  
Fundamentos de programación
la cual se puede acceder a la posición para almacenar o recuperar información. La información almacenada en una 
posición de memoria es su contenido. La Figura 1.5 muestra una memoria de computadora que consta de 1.000 po-
siciones en memoria con direcciones de 0 a 999 en código decimal. El contenido de estas direcciones o posiciones 
de memoria se llaman palabras, que como ya se ha comentado pueden ser de 8, 16, 32 y 64 bits. Por consiguiente, 
si trabaja con una máquina de 32 bits, significa que en cada posición de memoria de su computadora puede alojar 
32 bits, es decir 32 dígitos, bien ceros o unos.
.
.
.
325
999
998
997
3
2
1
0
Direcciones
Contenido de la
dirección 997
Figura 1.5. Memoria central de una computadora.
Las direcciones de memo...
```

### Pipeline_Upsilon (Rank 1 | Pág. 136)
> **Encabezado:** `Joyanes > Página 136`  
> **Longitud de fragmento:** `1270 caracteres`

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
o si lo prefiere utilizando el signo de asignación (=) de C, C++, Java o C#.
Caso especial
Los lenguajes C, C++, Java y C# permiten realizar múltiples asignaciones en una sola sentencia
a = b = c = d = e = n +35;
Tabla 3.10. Operadores aritméticos de asignación múltiple
Operador de asignación
Ejemplo
Operación
Resultado
Entero a = 3, b= 5, c = 4, d = 6, e = 10
*=
a += 8
a = a+8
a = 11
-=
b -= 5
b = b-5
b = 0
*=
c *= 4
c = c*4
c = 16
/=
d /= 3
d = d/3
d = 2
%=
e %= 9
e = e%9
e = 1
 
3.9.5. Conversión de tipo
En las asignaciones no se pueden asignar valores a una variable de un tipo incompatible al suyo. Se presenta...
```

---

## Caso #15 [Q1A2-15] (ARQ-01)

**Consulta:** *"¿Cuál es la definición formal de la notación asintótica O-grande (Big-O) para la complejidad de algoritmos?"*

- **Páginas de evidencia teórica:** [540, 545]
- **Criterio de Relevancia:** Define la cota superior del tiempo de ejecución en función del tamaño de entrada n.
- **Criterio de Suficiencia:** Presenta la formulación matemática o conceptual rigurosa.

### Pipeline_Sigma (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Notas`  
> **Longitud de fragmento:** `981 caracteres`

```text
[Notas]
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algoritmo
    .
    .
    .
  <sentencia Sn>
fin
Notas
1. En ocasiones, la declaración de constantes y variables las omitiremos o se describirán en una tabla de varia-
bles que hace sus mismas funciones.
2. Las cadenas de caracteres se encerrarán entre comillas simples.
3. Utilizar siempre sangrías en los bucles o en aquellas instrucciones que proporcionen legibilidad al programa, 
como inicio y fin.
MODELO PROPUESTO DE ALGORITMO
algoritmo raices
// resuelve una ecuación de 2.º grado
var
  real : a, b, c
inicio
  leer(a, b, c)
  d ← b ^ 2 - 4 * a * c
  si d < 0 entonces
    escribir('raices complej...
```

### Pipeline_Tau (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Longitud de fragmento:** `1980 caracteres`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por
read      write o bien print
Nota 2
Si no se especifica el tipo de dispositivo del cual se leen o escriben datos, los dispositivos de E/S por defecto 
son el teclado y la pantalla.
3.11. ESCRITURA DE ALGORITMOS/PROGRAMAS
La escritura de un algoritmo mediante una herramienta de programación debe ser lo más clara posible y estructurada, 
de modo que su lectura facilite considerablemente el entendimiento del algoritmo y su posterior codificación en un 
lenguaje de programación.
Los algoritmos deben ser escritos en lenguajes similares a los programas. En nuestro libro utilizaremos esencial-
mente ...
```

### Pipeline_Upsilon (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Longitud de fragmento:** `1980 caracteres`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por
read      write o bien print
Nota 2
Si no se especifica el tipo de dispositivo del cual se leen o escriben datos, los dispositivos de E/S por defecto 
son el teclado y la pantalla.
3.11. ESCRITURA DE ALGORITMOS/PROGRAMAS
La escritura de un algoritmo mediante una herramienta de programación debe ser lo más clara posible y estructurada, 
de modo que su lectura facilite considerablemente el entendimiento del algoritmo y su posterior codificación en un 
lenguaje de programación.
Los algoritmos deben ser escritos en lenguajes similares a los programas. En nuestro libro utilizaremos esencial-
mente ...
```

---

## Caso #16 [Q1A2-16] (ARQ-03)

**Consulta:** *"¿Cuál es la diferencia de eficiencia y crecimiento entre un algoritmo O(n log n) y uno O(n^2)?"*

- **Páginas de evidencia teórica:** [543, 548]
- **Criterio de Relevancia:** Contrasta el crecimiento casi lineal con el crecimiento cuadrático ante entradas grandes.
- **Criterio de Suficiencia:** Aporta justificación analítica sobre la escalabilidad de ambos tipos de algoritmo.

### Pipeline_Sigma (Rank 1 | Pág. 546)
> **Encabezado:** `Joyanes > Página 546`  
> **Longitud de fragmento:** `1501 caracteres`

```text
[Página 546]
516  
Fundamentos de programación
Si los árboles terminaron de recorrerse simultáneamente es que ambos tienen el mismo número de nodos y nunca ha 
sido diferente la información comparada; por tanto, la función devolverá verdad; en cualquier otro caso la función devolverá 
falso.
Diseño del algoritmo
lógico función iguales(E punt: raíz1, raíz2)
inicio
  si raíz1 = nulo entonces
    si raíz2 = nulo entonces
      devolver(verdad)
    fin_si
  si_no
    si raíz2 = nulo entonces
      devolver(falso)
    si_no
      si raíz1→.elemento <> raíz2→.elemento entonces
        devolver(falso)
      si_no
        devolver(iguales(raíz1→.izdo, raíz2→.izdo)
               y iguales(raíz1→.dcho, raíz2→.dcho))
      fin_si
    fin_si
  fin_si
fin_función
CONCEPTOS CLAVE
• Árbol.
• Árbol binar...
```

### Pipeline_Tau (Rank 1 | Pág. 541)
> **Encabezado:** `Joyanes > Página 541`  
> **Longitud de fragmento:** `910 caracteres`

```text
[Página 541]
Estructura de datos no lineales (árboles y grafos)  511
Un grafo no dirigido de orden N con A arcos requiere N entradas en el directorio y 2*A entradas de listas enlaza-
das, excepto si existen bucles que reducen el número de listas enlazadas en 1.
Un grafo dirigido de orden N con A arcos requiere N entradas en el directorio y A entradas de listas enlazadas.
3
6
NULO
2
2
5
3
NULO
1
2
3
4
5
6
NULO
NULO
NULO
NULO
DIRECTORIO
Figura 13.30.
EJEMPLO 13.12
La lista de adyacencia del grafo del Ejemplo 13.10 es
SF
LA
LV
KC
NY
LA
1000
SF
1000
LA
390
LA
2000
SF
1500
LV
390
KC
3000
LV
3000
KC
3500
KC
2000
NY
2500
La elección de la representación depende del algoritmo particular que se vaya a implementar y si el grafo es 
“disperso” o “denso”. Un grafo disperso es uno en el que el número d...
```

### Pipeline_Upsilon (Rank 1 | Pág. 541)
> **Encabezado:** `Joyanes > Página 541`  
> **Longitud de fragmento:** `910 caracteres`

```text
[Página 541]
Estructura de datos no lineales (árboles y grafos)  511
Un grafo no dirigido de orden N con A arcos requiere N entradas en el directorio y 2*A entradas de listas enlaza-
das, excepto si existen bucles que reducen el número de listas enlazadas en 1.
Un grafo dirigido de orden N con A arcos requiere N entradas en el directorio y A entradas de listas enlazadas.
3
6
NULO
2
2
5
3
NULO
1
2
3
4
5
6
NULO
NULO
NULO
NULO
DIRECTORIO
Figura 13.30.
EJEMPLO 13.12
La lista de adyacencia del grafo del Ejemplo 13.10 es
SF
LA
LV
KC
NY
LA
1000
SF
1000
LA
390
LA
2000
SF
1500
LV
390
KC
3000
LV
3000
KC
3500
KC
2000
NY
2500
La elección de la representación depende del algoritmo particular que se vaya a implementar y si el grafo es 
“disperso” o “denso”. Un grafo disperso es uno en el que el número d...
```

---

## Caso #17 [Q1A2-17] (ARQ-01)

**Consulta:** *"¿En qué página del índice general se lista el apartado de 'Resolución de problemas con computadoras'?"*

- **Páginas de evidencia teórica:** [11, 16]
- **Criterio de Relevancia:** Localiza el epígrafe dentro del bloque denso del índice.
- **Criterio de Suficiencia:** Indica el número de página exacto asociado al epígrafe.

### Pipeline_Sigma (Rank 1 | Pág. 14)
> **Encabezado:** `Joyanes > Página 14`  
> **Longitud de fragmento:** `4370 caracteres`

```text
[Página 14]
13.5. Grafos ................................................................................................................................................................ 
506
13.5.1. Terminología de grafos ........................................................................................................................ 
506
13.5.2. Representación de grafos .................................................................................................................... 
509
ACTIVIDADES DE PROGRAMACIÓN RESUELTAS .............................................................................................. 
512
CONCEPTOS CLAVE ..................................................................................................................................................
```

### Pipeline_Tau (Rank 1 | Pág. 36)
> **Encabezado:** `Joyanes > Página 36`  
> **Longitud de fragmento:** `2071 caracteres`

```text
[Página 36]
6  
Fundamentos de programación
estilo de una TV o un equipo de música. Sin embargo, conviene recordar que el PC, tal como se le conoce en la ac-
tualidad, no fue la primera computadora personal ya que le precedieron otras máquinas con microprocesadores de 
8 bits, muy populares en su tiempo, tales como Apple II, Pet CBM, Atari, TRS-80, etc., y el mítico ZX Spectrum, 
de los diferentes fabricantes citados en el párrafo anterior. 
El término PC se utiliza indistintamente con el término genérico de computadora de escritorio o computadora 
portátil (desktop) o (laptop)5.
1.1.2. Clasificación de las computadoras
Las computadoras modernas se pueden clasificar en computadoras personales, servidores, minicomputadoras, gran-
des computadoras (mainframes) y supercomputadoras. 
Las compu...
```

### Pipeline_Upsilon (Rank 1 | Pág. 13)
> **Encabezado:** `Joyanes > Página 13`  
> **Longitud de fragmento:** `4091 caracteres`

```text
[Página 13]
Capítulo 11. Ordenación, búsqueda y fusión externa (archivos) .......................................................................................... 
405
INTRODUCCIÓN ......................................................................................................................................................... 
405
11.1. Introducción ....................................................................................................................................................... 
406
11.2. Archivos ordenados ........................................................................................................................................... 
406
11.3. Fusión de archivos ..........................................................................................
```

---

## Caso #18 [Q1A2-18] (ARQ-04)

**Consulta:** *"¿Qué subsecciones componen el capítulo de algoritmos según la jerarquía detallada en el índice de contenidos?"*

- **Páginas de evidencia teórica:** [13, 16]
- **Criterio de Relevancia:** Recupera la secuencia de subapartados del capítulo de algoritmos.
- **Criterio de Suficiencia:** Permite observar la integridad de jerarquía en el bloque denso de índice.

### Pipeline_Sigma (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Longitud de fragmento:** `1980 caracteres`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por
read      write o bien print
Nota 2
Si no se especifica el tipo de dispositivo del cual se leen o escriben datos, los dispositivos de E/S por defecto 
son el teclado y la pantalla.
3.11. ESCRITURA DE ALGORITMOS/PROGRAMAS
La escritura de un algoritmo mediante una herramienta de programación debe ser lo más clara posible y estructurada, 
de modo que su lectura facilite considerablemente el entendimiento del algoritmo y su posterior codificación en un 
lenguaje de programación.
Los algoritmos deben ser escritos en lenguajes similares a los programas. En nuestro libro utilizaremos esencial-
mente ...
```

### Pipeline_Tau (Rank 1 | Pág. 138)
> **Encabezado:** `Joyanes > Nota 1`  
> **Longitud de fragmento:** `1980 caracteres`

```text
[Nota 1]
108  
Fundamentos de programación
Nota 1
Si se utilizaran las palabras reservadas en inglés, como suele ocurrir en los lenguajes de programación, se de-
berá sustituir
leer      escribir
por
read      write o bien print
Nota 2
Si no se especifica el tipo de dispositivo del cual se leen o escriben datos, los dispositivos de E/S por defecto 
son el teclado y la pantalla.
3.11. ESCRITURA DE ALGORITMOS/PROGRAMAS
La escritura de un algoritmo mediante una herramienta de programación debe ser lo más clara posible y estructurada, 
de modo que su lectura facilite considerablemente el entendimiento del algoritmo y su posterior codificación en un 
lenguaje de programación.
Los algoritmos deben ser escritos en lenguajes similares a los programas. En nuestro libro utilizaremos esencial-
mente ...
```

### Pipeline_Upsilon (Rank 1 | Pág. 13)
> **Encabezado:** `Joyanes > Página 13`  
> **Longitud de fragmento:** `4091 caracteres`

```text
[Página 13]
Capítulo 11. Ordenación, búsqueda y fusión externa (archivos) .......................................................................................... 
405
INTRODUCCIÓN ......................................................................................................................................................... 
405
11.1. Introducción ....................................................................................................................................................... 
406
11.2. Archivos ordenados ........................................................................................................................................... 
406
11.3. Fusión de archivos ..........................................................................................
```

---

## Caso #19 [Q1A2-37] (ARQ-11)

**Consulta:** *"¿Cómo se gestiona el vector de interrupciones en el controlador programable APIC en modo protegido x86?"*

- **Páginas de evidencia teórica:** None
- **Criterio de Relevancia:** Ningún fragmento de Joyanes debe considerarse relevante (control negativo de dominio).
- **Criterio de Suficiencia:** El sistema debe abstenerse o arrojar puntajes de similitud bajos (<0.40).

### Pipeline_Sigma (Rank 1 | Pág. 43)
> **Encabezado:** `Joyanes > Página 43`  
> **Longitud de fragmento:** `1760 caracteres`

```text
[Página 43]
Introducción a las computadoras y los lenguajes de programación  13
incluye Celeron y Xeon), Opteron de AMD, SPARC de Sun Microsystemas, Crusoe de Transmeta, Centrino Core 2 
y Centro Core 2 Duo de Intel que se instalan en portátiles, etc.
Todas las UCP tienen una velocidad de trabajo, regulada por un pequeño cristal de cuarzo, y que se conoce como 
frecuencia de reloj. El cristal vibra a un elevado número de ciclos de reloj. Con cada ciclo de reloj se envía un impul-
so a la UCP, y en principio, cada pulsación puede hacer realizar una o más tareas a la UCP. El número de ciclos de 
reloj por segundo se mide en hertzios. El cristal de la UCP vibra millones de veces por segundo y por esta razón la 
velocidad del reloj se calcula en millones de oscilaciones (megahercios o MHz) o m...
```

### Pipeline_Tau (Rank 1 | Pág. 17)
> **Encabezado:** `Joyanes > Página 17`  
> **Longitud de fragmento:** `3717 caracteres`

```text
[Página 17]
18.10.2. Manual de mantenimiento (documentación para programadores) .................................................. 
680
18.10.3. Reglas de documentación ................................................................................................................ 
681
18.11. Depuración ....................................................................................................................................................... 
681
18.11.1. Localización y reparación de errores ............................................................................................... 
681
18.11.2. Depuración de sentencias si-entonces-sino ..................................................................................... 
682
18.11.3. Los equipos de programación ...............
```

### Pipeline_Upsilon (Rank 1 | Pág. 489)
> **Encabezado:** `Joyanes > Página 489`  
> **Longitud de fragmento:** `1415 caracteres`

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
fin _ subprograma C
Subprograma C
Subprograma B
Subprograma
B
Subprograma
C
Puntero de pila
Pila de direcciones
de retorno
Programa principal
llamar _ a A 
         
llamar _ a B
direccion X
direccion Y
direccion Z
llamar a C
fin
Cuando un subprograma termina, debe retornar a la dirección siguiente a la instrucción que le llamó (llamar_a). 
Cada vez que se invoca un subprograma, la dirección siguiente (X, Y o Z) se introduce en la pila. El vaciado de la 
pila se realizará por los sucesivos retornos, decrementándose el puntero de pila que queda libre apuntando a la si-
guiente dirección de retorno.
← Puntero ...
```

---

## Caso #20 [Q1A2-38] (ARQ-11)

**Consulta:** *"¿Cómo implementa el núcleo NT el algoritmo WSClock para el conjunto de trabajo de páginas en memoria virtual?"*

- **Páginas de evidencia teórica:** None
- **Criterio de Relevancia:** Ningún fragmento de Joyanes debe considerarse relevante (control negativo de dominio).
- **Criterio de Suficiencia:** El sistema debe abstenerse o arrojar puntajes de similitud bajos (<0.40).

### Pipeline_Sigma (Rank 1 | Pág. 43)
> **Encabezado:** `Joyanes > Página 43`  
> **Longitud de fragmento:** `1760 caracteres`

```text
[Página 43]
Introducción a las computadoras y los lenguajes de programación  13
incluye Celeron y Xeon), Opteron de AMD, SPARC de Sun Microsystemas, Crusoe de Transmeta, Centrino Core 2 
y Centro Core 2 Duo de Intel que se instalan en portátiles, etc.
Todas las UCP tienen una velocidad de trabajo, regulada por un pequeño cristal de cuarzo, y que se conoce como 
frecuencia de reloj. El cristal vibra a un elevado número de ciclos de reloj. Con cada ciclo de reloj se envía un impul-
so a la UCP, y en principio, cada pulsación puede hacer realizar una o más tareas a la UCP. El número de ciclos de 
reloj por segundo se mide en hertzios. El cristal de la UCP vibra millones de veces por segundo y por esta razón la 
velocidad del reloj se calcula en millones de oscilaciones (megahercios o MHz) o m...
```

### Pipeline_Tau (Rank 1 | Pág. 12)
> **Encabezado:** `Joyanes > Página 12`  
> **Longitud de fragmento:** `4183 caracteres`

```text
[Página 12]
9.5. Operaciones sobre archivos ............................................................................................................................... 
317
9.5.1. Creación de un archivo .......................................................................................................................... 
318
9.5.2. Consulta de un archivo .......................................................................................................................... 
318
9.5.3. Actualización de un archivo .................................................................................................................. 
319
9.5.4. Clasificación de un archivo ................................................................................................................... 
...
```

### Pipeline_Upsilon (Rank 1 | Pág. 42)
> **Encabezado:** `Joyanes > Página 42`  
> **Longitud de fragmento:** `1786 caracteres`

```text
[Página 42]
12  
Fundamentos de programación
la cual se puede acceder a la posición para almacenar o recuperar información. La información almacenada en una 
posición de memoria es su contenido. La Figura 1.5 muestra una memoria de computadora que consta de 1.000 po-
siciones en memoria con direcciones de 0 a 999 en código decimal. El contenido de estas direcciones o posiciones 
de memoria se llaman palabras, que como ya se ha comentado pueden ser de 8, 16, 32 y 64 bits. Por consiguiente, 
si trabaja con una máquina de 32 bits, significa que en cada posición de memoria de su computadora puede alojar 
32 bits, es decir 32 dígitos, bien ceros o unos.
.
.
.
325
999
998
997
3
2
1
0
Direcciones
Contenido de la
dirección 997
Figura 1.5. Memoria central de una computadora.
Las direcciones de memo...
```

---

## Caso #21 [Q1A2-39] (ARQ-12)

**Consulta:** *"manejo de pila y almacenamiento"*

- **Páginas de evidencia teórica:** [485, 505]
- **Criterio de Relevancia:** Evalúa si recupera pila como memoria de ejecución (stack) o como estructura de datos abstracta.
- **Criterio de Suficiencia:** Identifica la discriminación de contexto semántico según el capítulo.

### Pipeline_Sigma (Rank 1 | Pág. 490)
> **Encabezado:** `Joyanes > Página 490`  
> **Longitud de fragmento:** `1588 caracteres`

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
  elemento ← leercar
  mientras (codigo(elemento)<> 26) y no llena(cima1) y no
           llena(cima2)y no llena(cima3) hacer
     {saldremos del bucle en cuanto se llene alguna de las pilas o
           pulsemos ^Z}
     si (elemento >= 'A') y (elemento <= 'Z') o (elemento >= 'a') y
        (elemento >= 'z')entonces
       meter (cima1, pilaletras, elemento)
     si_no
        si (elemento>= '0') y (elemento<='9') entonces
           meter (cima2, piladigitos, elemento)
        si_no 
           meter (cima3, pilaotroscaracteres, elemento)
        fin_si
     fin_si
     elemento ← leercar
  fin_mientras...
```

### Pipeline_Tau (Rank 1 | Pág. 13)
> **Encabezado:** `Joyanes > Página 13`  
> **Longitud de fragmento:** `4091 caracteres`

```text
[Página 13]
Capítulo 11. Ordenación, búsqueda y fusión externa (archivos) .......................................................................................... 
405
INTRODUCCIÓN ......................................................................................................................................................... 
405
11.1. Introducción ....................................................................................................................................................... 
406
11.2. Archivos ordenados ........................................................................................................................................... 
406
11.3. Fusión de archivos ..........................................................................................
```

### Pipeline_Upsilon (Rank 1 | Pág. 503)
> **Encabezado:** `Joyanes > Página 503`  
> **Longitud de fragmento:** `1809 caracteres`

```text
[Página 503]
Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)  473
procedimiento devoluciones( E/S entero: inic, vacio; E/S lista: m)
 var
  tipo_elemento: elemento
  entero       : posic, anterior
  entero       : cantidad
  lógico       : encontrado
 inicio
   si no vacia(inic) entonces
     escribir('Introduzca un * en el código para terminar')
     escribir('Código: ')
     leer(elemento.cod)
   si_no
     escribir('No hay ventas, no puede haber devoluciones')
   fin_si
   mientras (elemento.cod<>'*' ) y no vacia(inic) hacer
     consultar(inic, posic, anterior, elemento, encontrado, m)
     si encontrado entonces
       repetir
         escribir('Deme cantidad devuelta ')
         leer(cantidad)
         si cantidad > m[posic].elemento.cantidad entonces
      ...
```

---

## Caso #22 [Q1A2-40] (ARQ-12)

**Consulta:** *"condición de fin y salida de bloque"*

- **Páginas de evidencia teórica:** [135, 150]
- **Criterio de Relevancia:** Evalúa si recupera condiciones lógicas de estructuras condicionales vs bucles.
- **Criterio de Suficiencia:** Determina la especificidad del contexto ante términos polisémicos.

### Pipeline_Sigma (Rank 1 | Pág. 142)
> **Encabezado:** `Joyanes > Notas`  
> **Longitud de fragmento:** `981 caracteres`

```text
[Notas]
112  
Fundamentos de programación
var tipo de datos : lista de identificadores
const lista de identificadores = valor
inicio
  <sentencia S1>
  <sentencia S2>               // cuerpo del algoritmo
    .
    .
    .
  <sentencia Sn>
fin
Notas
1. En ocasiones, la declaración de constantes y variables las omitiremos o se describirán en una tabla de varia-
bles que hace sus mismas funciones.
2. Las cadenas de caracteres se encerrarán entre comillas simples.
3. Utilizar siempre sangrías en los bucles o en aquellas instrucciones que proporcionen legibilidad al programa, 
como inicio y fin.
MODELO PROPUESTO DE ALGORITMO
algoritmo raices
// resuelve una ecuación de 2.º grado
var
  real : a, b, c
inicio
  leer(a, b, c)
  d ← b ^ 2 - 4 * a * c
  si d < 0 entonces
    escribir('raices complej...
```

### Pipeline_Tau (Rank 1 | Pág. 496)
> **Encabezado:** `Joyanes > Página 496`  
> **Longitud de fragmento:** `1754 caracteres`

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
El procedimiento para la inserción de un nuevo elemento deberá verificar, en primer lugar, que la cola no está 
totalmente llena y, por consiguiente, no se producirá error de desbordamiento. La condición de desbordamiento se 
produce cuando final = Max 
procedimiento meter( E/S entero: final; S entero: frente;
E/S 
arr: c; E tipo_elemento: elemento)
 inicio
  si final = 0 entonces
     frente ← 1
  fin_si
  final ← final + 1
  c[final] ← elemento
 fin_procedimiento
Para eliminar un elemento será preciso verificar, en primer lugar, que la cola no está vacía.
procedimiento sacar( E/S entero: fren...
```

### Pipeline_Upsilon (Rank 1 | Pág. 487)
> **Encabezado:** `Joyanes > Página 487`  
> **Longitud de fragmento:** `1202 caracteres`

```text
[Página 487]
Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)  457
      liberar(auxi)
      {liberar es un procedimiento para la eliminación de
      variables dinámicas}
    fin_si
 fin_procedimiento
Implementación con arrays
Necesitaremos un array y una variable numérica cima que apunte al último elemento colocado en la pila.
La inserción o extracción de un elemento se realizará siempre por la parte superior.
Su implementación mediante arrays limita el máximo número de elementos que la pila puede contener y origina 
la necesidad de una función más.
Llena(...)  de resultado lógico
cima ←0
Inicializar(cima)
cima 
1
Meter(cima,p,elemento)
cima ← 2
xxxxxxxx
xxxxxxxx
xxxxxxxx
cima ← 1
xxxxxxxx
Sacar(cima,p,elemento)
Max
...
...
3
2
1
xxxxxxxx
←
 const Max = <expresió...
```

---

