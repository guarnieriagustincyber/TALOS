48  Fundamentos de programación
  depreciación anual por año 
Salida { depreciación acumulada en cada año 
  valor del automóvil en cada año
  depreciación acumulada
Proceso { cálculo de la depreciación acumulada cada año 
  cálculo del valor del automóvil en cada año
La tabla siguiente muestra la salida solicitada
Año Depreciación Depreciación acumulada Valor anual
1 (2006) 3.000  3.000 17.000
2 (2007) 3.000  6.000 14.000
3 (2008) 3.000  9.000 11.000
4 (2009) 3.000 12.000  8.000
5 (2010) 3.000 15.000  5.000
6 (2011) 3.000 18.000  2.000
2.1.2. Diseño del algoritmo
En la etapa de análisis del proceso de programación se determina qué hace el programa. En la etapa de diseño se de-
termina cómo hace el programa la tarea solicitada. Los métodos más eficaces para el proceso de diseño se basan en el 
conocido divide y vencerás . Es decir, la resolución de un problema complejo se realiza dividiendo el problema en 
subproblemas y a continuación dividiendo estos subproblemas en otros de nivel más bajo, hasta que pueda ser imple-
mentada una solución en la computadora. Este método se conoce técnicamente como diseño descendente (top-down) 
o modular. El proceso de romper el problema en cada etapa y expresar cada paso en forma más detallada se denomi-
na refinamiento sucesivo.
Cada subprograma es resuelto mediante un módulo (subprograma) que tiene un solo punto de entrada y un solo 
punto de salida.
Cualquier programa bien diseñado consta de un programa principal (el módulo de nivel más alto) que llama a 
subprogramas (módulos de nivel más bajo) que a su vez pueden llamar a otros subprogramas. Los programas estruc-
turados de esta forma se dice que tienen un diseño modular y el método de romper el programa en módulos más 
pequeños se llama programación modular. Los módulos pueden ser planeados, codificados, comprobados y depura-
dos independientemente (incluso por diferentes programadores) y a continuación combinarlos entre sí. El proceso 
implica la ejecución de los siguientes pasos hasta que el programa se termina:
1. Programar un módulo.
2. Comprobar el módulo.
3. Si es necesario, depurar el módulo.
4. Combinar el módulo con los módulos anteriores.
El proceso que convierte los resultados del análisis del problema en un diseño modular con refinamientos sucesivos 
que permitan una posterior traducción a un lenguaje se denomina diseño del algoritmo.
El diseño del algoritmo es independiente del lenguaje de programación en el que se vaya a codificar posterior-
mente.
2.1.3. Herramientas de programación
Las dos herramientas más utilizadas comúnmente para diseñar algoritmos son: diagramas de flujo y pseudocódigos.
Un diagrama de flujo (flowchart) es una representación gráfica de un algoritmo. Los símbolos utilizados han sido 
normalizados por el Instituto Norteamericano de Normalización (ANSI), y los más frecuentemente empleados se muestran 
en la Figura 2.2, junto con una plantilla utilizada para el dibujo de los diagramas de flujo (Figura 2.3). En la Figura 2.4 
se representa el diagrama de flujo que resuelve el Problema 2.1.