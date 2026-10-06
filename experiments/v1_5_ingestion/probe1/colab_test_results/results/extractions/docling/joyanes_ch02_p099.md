En el algoritmo anterior existen diferentes aspectos a considerar. En primer lugar, ciertas palabras reservadas se han escrito deliberadamente en negrita (mientras, si\_no; etc.). Estas palabras describen las estructuras de control fundamentales y procesos de toma de decisión en el algoritmo. Éstas incluyen los conceptos importantes de selección (expresadas por si-entonces-si\_no, if-then-else) y de repetición (expresadas con mientras-hacer o a veces repetir-hasta e iterar-fin\_iterar, en inglés, while-do y repeat-until) que se encuentran en casi todos los algoritmos, especialmente en los de proceso de datos. La capacidad de decisión permite seleccionar alternativas de acciones a seguir o bien la repetición una y otra vez de operaciones básicas.

```
si proyectan la película seleccionada ir al cine si_no ver la televisión, ir al fútbol o leer el periódico mientras haya personas en la cola, ir avanzando repetidamente hasta llegar a la taquilla
```

Otro aspecto a considerar es el método elegido para describir los algoritmos: empleo de indentación (sangrado o justificación) en escritura de algoritmos. En la actualidad es tan importante la escritura de programa como su posterior lectura. Ello se facilita con la indentación de las acciones interiores a las estructuras fundamentales citadas: selectivas y repetitivas. A lo largo de todo el libro la indentación o sangrado de los algoritmos será norma constante.

Para terminar estas consideraciones iniciales sobre algoritmos, describiremos las acciones necesarias para refinar el algoritmo objeto de nuestro estudio; para ello analicemos la acción:

```
Localizar la(s) butaca(s).
```

Si los números de los asientos están impresos en la entrada, la acción compuesta se resuelve con el siguiente algoritmo:

```
1. inicio //algoritmo para encontrar la butaca del espectador 2. caminar hasta llegar a la primera fila de butacas 3. repetir compara número de fila con número impreso en billete si son iguales entonces pasar a la siguiente fila fin_si hasta_que se localice la fila correcta 4. mientras número de butaca no coincida con número de billete hacer avanzar a través de la fila a la siguiente butaca fin_mientras 5. sentarse en la butaca 6. fin
```

En este algoritmo la repetición se ha mostrado de dos modos, utilizando ambas notaciones, repetir... has-ta\_que y mientras... fin\_mientras. Se ha considerado también, como ocurre normalmente, que el número del asiento y fila coincide con el número y fila rotulado en el billete.

## 2.7. REPRESENTACIÓN GRÁFICA DE LOS ALGORITMOS

Para representar un algoritmo se debe utilizar algún método que permita independizar dicho algoritmo del lenguaje de programación elegido. Ello permitirá que un algoritmo pueda ser codificado indistintamente en cualquier lenguaje. Para conseguir este objetivo se precisa que el algoritmo sea representado gráfica o numéricamen te, de modo que las sucesivas acciones no dependan de la sintaxis de ningún lenguaje de programación, sino que la descripción pueda servir fácilmente para su transformación en un programa, es decir, su codificación.

Los métodos usuales para representar un algoritmo son:

1. diagrama de flujo,
2. diagrama N-S (Nassi-Schneiderman),
3. lenguaje de especificación de algoritmos: pseudocódigo,
4. lenguaje español, inglés…
5. fórmulas.