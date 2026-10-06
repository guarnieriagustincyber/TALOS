80  Fundamentos de programación
2.7.3. Diagramas de Nassi-Schneiderman (N-S)
El diagrama N-S de Nassi Schneiderman —también conocido como diagrama de Chapin— es como un diagrama de 
flujo en el que se omiten las flechas de unión y las cajas son contiguas. Las acciones sucesivas se escriben en cajas 
sucesivas y, como en los diagramas de flujo, se pueden escribir diferentes acciones en una caja.
Un algoritmo se representa con un rectángulo en el que cada banda es una acción a realizar.
EJEMPLO
Escribir un algoritmo que lea el nombre de un empleado, las horas trabajadas, el precio por hora y calcule los im-
puestos a pagar (tasa = 25%) y el salario neto.
leer
nombre, horas, precio 
calcular
salario ←  horas * precio
calcular
impuestos ←  0.25 * salario
calcular
neto ←  salario impuestos 
escribir
nombre, salario, impuestos, neto
nombre del algoritmo
<accion 1>
<accion 2>
<accion 3>
...
fin
Figura 2.20. Representación gráfica N-S de un algoritmo.
Otro ejemplo es la representación de la estructura condicional (Figura 2.21).
¿condición?
acción 1 acción 2
¿condición?
<acciones> <acciones>
a) b)
sí no
Figura 2.21. Estructura condicional o selectiva: a ) diagrama de flujo: b ) diagrama N-S.