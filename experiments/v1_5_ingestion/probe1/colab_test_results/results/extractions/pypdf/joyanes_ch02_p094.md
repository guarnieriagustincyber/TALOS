64  Fundamentos de programación
misma, incluye los mismos principios, sin embargo, dependiendo del coche, en particular, la operación será muy 
diferente, incluirá diferentes acciones en cada caso. Otro ejemplo a considerar y relativo a los operadores “+” y “*” 
aplicados a números enteros o números complejos; aunque ambos son números, en un caso la suma y multiplicación 
son operaciones simples, mientras que en el caso de los números complejos al componerse de parte real y parte ima-
ginaria, será necesario seguir un método específico para tratar ambas partes y obtener un resultado que también será 
un número complejo.
El uso de operadores o funciones de forma diferente, dependiendo de los objetos sobre los que están actuando se 
llama polimorfismo (una cosa con diferentes formas). Sin embargo, cuando un operador existente, tal como + o =, 
se le permite la posibilidad de operar sobre nuevos tipos de datos, se dice entonces que el operador está sobrecarga-
do. La sobrecarga es un tipo de polimorfismo y una característica importante de la POO. En el Capítulo 10 se am-
pliará, también en profundidad, este nuevo concepto.
2.5. CONCEPTO Y CARACTERÍSTICAS DE ALGORITMOS
El objetivo fundamental de este texto es enseñar a resolver problemas mediante una computadora. El programador 
de computadora es antes que nada una persona que resuelve problemas, por lo que para llegar a ser un programador 
eficaz se necesita aprender a resolver problemas de un modo riguroso y sistemático. A lo largo de todo este libro nos 
referiremos a la metodología necesaria para resolver problemas mediante programas , concepto que se denomina 
metodología de la programación. El eje central de esta metodología es el concepto, ya tratado, de algoritmo.
Un algoritmo es un método para resolver un problema. Aunque la popularización del término ha llegado con el 
advenimiento de la era informática, algoritmo proviene —como se comentó anteriormente— de Mohammed al-
KhoWârizmi, matemático persa que vivió durante el siglo IX y alcanzó gran reputación por el enunciado de las reglas 
paso a paso para sumar, restar, multiplicar y dividir números decimales; la traducción al latín del apellido en la pa-
labra algorismus derivó posteriormente en algoritmo. Euclides, el gran mate mático griego (del siglo IV a. C.) que 
inventó un método para encontrar el máximo común divisor de dos números, se considera con Al-Khowârizmi el otro 
gran padre de la algoritmia (ciencia que trata de los algoritmos).
El profesor Niklaus Wirth —inventor de Pascal, Modula-2 y Oberon— tituló uno de sus más famosos libros, Al-
goritmos + Estructuras de datos = Programas, significándonos que sólo se puede llegar a realizar un buen programa 
con el diseño de un algoritmo y una correcta estructura de datos. Esta ecuación será una de las hipótesis fundamen-
tales consideradas en esta obra.
La resolución de un problema exige el diseño de un algoritmo que resuelva el problema propuesto.
Problema Diseño
de algoritmo
Programa
de computadora
Figura 2.14. Resolución de un problema.
Los pasos para la resolución de un problema son:
1. Diseño del algoritmo, que describe la secuencia ordenada de pasos —sin ambigüedades— que conducen a la 
solución de un problema dado. ( Análisis del problema y desarrollo del algoritmo .)
2. Expresar el algoritmo como un programa en un lenguaje de programación adecuado. ( Fase de codifica-
ción.)
3. Ejecución y validación del programa por la computadora.
Para llegar a la realización de un programa es necesario el diseño previo de un algoritmo, de modo que sin algo-
ritmo no puede existir un programa.
Los algoritmos son independientes tanto del lenguaje de programación en que se expresan como de la computa-
dora que los ejecuta. En cada problema el algoritmo se puede expresar en un lenguaje diferente de programación y 
ejecutarse en una computadora distinta; sin embargo, el algoritmo será siempre el mismo. Así, por ejemplo, en una 
analogía con la vida diaria, una receta de un plato de cocina se puede expresar en español, inglés o francés, pero 
cualquiera que sea el lenguaje, los pasos para la elaboración del plato se realizarán sin importar el idioma del coci-
nero.