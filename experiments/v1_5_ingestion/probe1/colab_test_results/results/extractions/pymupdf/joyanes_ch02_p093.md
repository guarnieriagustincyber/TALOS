Metodología de la programación y desarrollo de software  63

2.4.7 Reusabilidad

Una vez que una clase ha sido escrita, creada y depurada, se puede distribuir a otros programadores para utilizar en 
sus propios programas. Esta propiedad se llama reusabilidad 4 o reutilización. Su concepto es similar a las funciones 
incluidas en las bibliotecas de funciones de un lenguaje procedimental como C que se pueden incorporar en diferen-
tes programas.

En C++, el concepto de herencia proporciona una extensión o ampliación al concepto de reusabilidad. Un pro-
gramador puede considerar una clase existente y sin modificarla, añadir competencias y propiedades adicionales a 
ella. Esto se consigue derivando una nueva clase de una ya existente. La nueva clase heredará las características de 
la clase antigua, pero es libre de añadir nuevas características propias.

La facilidad de reutilizar o reusar el software existente es uno de los grandes beneficios de la POO: muchas em-
presas consiguen con la reutilización de clase en nuevos proyectos la reducción de los costes de inversión en sus 
presupuestos de programación. ¿En esencia cuáles son las ventajas de la herencia? Primero, se utiliza para consisten-
cia y reducir código. Las propiedades comunes de varias clases sólo necesitan ser implementadas una vez y sólo 
necesitan modificarse una vez si es necesario. La otra ventaja es que el concepto de abstracción de la funcionalidad 
común está soportada.

2.4.8. Polimorfismo

Además de las ventajas de consistencia y reducción de código, la herencia, aporta también otra gran ventaja: facilitar 
el polimorfismo. Polimorfismo es la propiedad de que un operador o una función actúen de modo diferente en función 
del objeto sobre el que se aplican. En la practica, el polimorfismo significa la capacidad de una operación de ser 
interpretada sólo por el propio objeto que lo invoca. Desde un punto de vista práctico de ejecución del programa, el 
polimorfismo se realiza en tiempo de ejecución ya que durante la compilación no se conoce qué tipo de objeto y por 
consiguiente qué operación ha sido llamada. En el Capítulo 14 se describirá en profundidad la propiedad de polimor-
fismo y los diferentes modos de implementación del polimorfismo.

La propiedad de polimorfismo es aquella en que una operación tiene el mismo nombre en diferentes clases, pero 
se ejecuta de diferentes formas en cada clase. Así, por ejemplo, la operación de abrir se puede dar en diferentes cla-
ses: abrir una puerta, abrir una ventana, abrir un periódico, abrir un archivo, abrir una cuenta corriente en un banco, 
abrir un libro, etc. En cada caso se ejecuta una operación diferente aunque tiene el mismo nombre en todos ellos 
“abrir”. El polimorfismo es la propiedad de una operación de ser interpretada sólo por el objeto al que pertenece. 
Existen diferentes formas de implementar el polimorfismo y variará dependiendo del lenguaje de programación.

Veamos el concepto con ejemplos de la vida diaria.
En un taller de reparaciones de automóviles existen numerosos carros, de marcas diferentes, de modelos diferen-
tes, de tipos diferentes, potencias diferentes, etc. Constituyen una clase o colección heterogénea de carros (coches). 
Supongamos que se ha de realizar una operación común “cambiar los frenos del carro”. La operación a realizar es la

4 El término proviene del concepto ingles reusability. La traducción no ha sido aprobada por la RAE, pero se incorpora al texto por su gran 
uso y difusión entre los profesionales de la informática.

Animal

Mamífero
Reptil
Anfibio

Rana
Caballo
Serpiente

Figura 2.13. Herencia de clases en UML.