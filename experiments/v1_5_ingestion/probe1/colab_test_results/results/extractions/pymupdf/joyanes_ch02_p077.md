Metodología de la programación y desarrollo de software  47

Un algoritmo debe producir un resultado en un tiempo finito. Los métodos que utilizan algoritmos se denominan 
métodos algorítmicos, en oposición a los métodos que implican algún juicio o interpretación que se denominan mé-
todos heurísticos. Los métodos algorítmicos se pueden implementar en computadoras; sin embargo, los procesos 
heurísticos no han sido convertidos fácilmente en las computadoras. En los últimos años las técnicas de inteligencia 
artificial han hecho posible la implementación del proceso heurístico en computadoras.

Ejemplos de algoritmos son: instrucciones para montar en una bicicleta, hacer una receta de cocina, obtener el 
máximo común divisor de dos números, etc. Los algoritmos se pueden expresar por fórmulas, diagramas de flujo o 
N-S y pseudocódigos. Esta última representación es la más utilizada para su uso con lenguajes estructurados como 
Pascal.

2.1.1. Análisis del problema

La primera fase de la resolución de un problema con computadora es el análisis del problema. Esta fase requiere una 
clara definición, donde se contemple exactamente lo que debe hacer el programa y el resultado o solución deseada.

Dado que se busca una solución por computadora, se precisan especificaciones detalladas de entrada y salida. La 
Figura 2.1 muestra los requisitos que se deben definir en el análisis.

Análisis

del
problema

Resolución

de un
problema

Diseño

del
algoritmo

Resolución del

problema con

computadora

Figura 2.1. Análisis del problema.

Para poder identificar y definir bien un problema es conveniente responder a las siguientes preguntas:

• ¿Qué entradas se requieren? (tipo de datos con los cuales se trabaja y cantidad).
• ¿Cuál es la salida deseada? (tipo de datos de los resultados y cantidad).
• ¿Qué método produce la salida deseada?
• Requisitos o requerimientos adicionales y restricciones a la solución.

PROBLEMA 2.1

Se desea obtener una tabla con las depreciaciones acumuladas y los valores reales de cada año, de un automóvil 
comprado por 20.000 euros en el año 2005, durante los seis años siguientes suponiendo un valor de recuperación o 
rescate de 2.000. Realizar el análisis del problema, conociendo la fórmula de la depreciación anual constante D 
para cada año de vida útil.

D = coste – valor de recuperación

vida útil

D = 20.000 – 2.000

6
 = 18.000

6
 = 3.000

coste original 
Entrada { vida útil
 
 valor de recuperación