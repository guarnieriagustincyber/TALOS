62  
Fundamentos de programación

La idea de clases conduce a la idea de herencia. Clases diferentes se pueden conectar unas con otras de modo 
jerárquico. Como ya se ha comentado anteriormente con las relaciones de generalización y especialización, en nues-
tras vidas diarias se utiliza el concepto de clases divididas en subclases. La clase animal se divide en anfibios, 
mamíferos, insectos, pájaros, etc., y la clase vehículo en carros, motos, camiones, buses, etc.

El principio de la división o clasificación es que cada subclase comparte características comunes con la clase de 
la que procede o se deriva. Los carros, motos, camiones y buses tiene ruedas, motores y carrocerías; son las caracte-
rísticas que definen a un vehículo. Además de las características comunes con los otros miembros de la clase, cada 
subclase tiene sus propias características. Por ejemplo los camiones tienen una cabina independiente de la caja que 
transporta la carga; los buses tienen un gran número de asientos independientes para los viajeros que ha de transpor-
tar, etc. En la Figura 2.13 se muestran clases pertenecientes a una jerarquía o herencia de clases.

De modo similar una clase se puede convertir en padre o raíz de otras subclases. En C++ la clase original se de-
nomina clase base y las clases que se derivan de ella se denominan clases derivadas y siempre son una especializa-
ción o concreción de su clase base. A la inversa, la clase base es la generalización de la clase derivada. Esto signifi-
ca que todas las propiedades (atributos y operaciones) de la clase base se heredan por la clase derivada, 
normalmente suplementada con propiedades adicionales.

c) Clase Carro
d) Clases Persona, Carro y Avión

a) Notación completa de un objeto
b) Notación abreviada de una clase

Nombre de la clase

Persona

Nombre de la clase

Atributos

Métodos

Excepciones, etc.

Carro

Marca
Modelo
Año de matrícula
Potencia

Acelerar ( )
Frenar ( )
Girar ( )

Carro

Avión

Figura 2.11. Representación de clases en UML.

Perro

Nombre
Edad
Peso
Altura

Correr ( )
Dormir ( )

Jugador de Baloncesto

Lanzar ( )
Saltar ( )
…

Nombre
Altura
Peso
Edad

Figura 2.12. Representación de clases en UML con atributos y métodos.