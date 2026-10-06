68  
Fundamentos de programación

2.6. ESCRITURA DE ALGORITMOS

Como ya se ha comentado anteriormente, el sistema para describir (“escribir”) un algoritmo consiste en realizar una 
descripción paso a paso con un lenguaje natural del citado algoritmo. Recordemos que un algoritmo es un método o 
conjunto de reglas para solucionar un problema. En cálculos elementales estas reglas tienen las siguientes propie-
dades:

• deben ir seguidas de alguna secuencia definida de pasos hasta que se obtenga un resultado coherente,
• sólo puede ejecutarse una operación a la vez.

El flujo de control usual de un algoritmo es secuencial; consideremos el algoritmo que responde a la pregunta:

¿Qué hacer para ver la película de Harry Potter?

La respuesta es muy sencilla y puede ser descrita en forma de algoritmo general de modo similar a:

ir al cine
comprar una entrada (billete o ticket)
ver la película
regresar a casa

El algoritmo consta de cuatro acciones básicas, cada una de las cuales debe ser ejecutada antes de realizar la si-
guiente. En términos de computadora, cada acción se codificará en una o varias sentencias que ejecutan una tarea 
particular.

El algoritmo descrito es muy sencillo; sin embargo, como ya se ha indicado en párrafos anteriores, el algoritmo 
general se descompondrá en pasos más simples en un procedimiento denominado refinamiento sucesivo, ya que cada 
acción puede descomponerse a su vez en otras acciones simples. Así, por ejemplo, un primer refinamiento del algo-
ritmo ir al cine se puede describir de la forma siguiente:

1. inicio
2. ver la cartelera de cines en el periódico
3. si no proyectan "Harry Potter" entonces
   3.1. decidir otra actividad
   3.2. bifurcar al paso 7
   si_no
   3.3. ir al cine
   fin_si
4. si hay cola entonces
   4.1. ponerse en ella
   4.2. mientras haya personas delante hacer
        4.2.1. avanzar en la cola
        fin_mientras
   fin_si
5. si hay localidades entonces
   5.1. comprar una entrada
   5.2. pasar a la sala
   5.3. localizar la(s) butaca(s)
   5.4. mientras proyectan la película hacer
        5.4.1. ver la película
        fin_mientras
   5.5. abandonar el cine
   si_no
   5.6. refunfuñar
   fin_si
6. volver a casa
7. fin