78  
Fundamentos de programación

4. Si existen mas numeros, ejecutar los pasos 5 a 8.
5. Leer el siguiente numero y dar su valor a la variable NUMERO.
6. Si NUMERO = 0, incrementar TOTAL en 1.
7. Si NUMERO <> 0, no modificar TOTAL.
8. Retornar al paso 2.

El diagrama de flujo y la codificación en pseudocódigo correspondiente es:

Diagrama de flujo
Pseudocódigo

Total
0

Inicio

TOTAL
TOTAL + 1

NÚMERO = 0

Escribir

TOTAL

Fin

Leer
NÚMERO

¿más números?
no

sí

no

sí

entero: numero, total
caracter: mas Datos;

inicio
escribir ('Cuenta de ceros leidos del teclado')
mas Datos ← 'S';
total ← 0

mientras ( mas Datos = 'S') o (mas Datos = 's') hacer
  leer (numero)
  si (numero = 0)
      total ← total + 1
  fin si
  escribir ('Mas números 'S/N'')
  leer (mas Datos)
fin mientras
escribir ('total de ceros =', total)
fin