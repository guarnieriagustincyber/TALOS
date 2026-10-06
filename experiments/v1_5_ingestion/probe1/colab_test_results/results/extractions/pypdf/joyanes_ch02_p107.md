Metodología de la programación y desarrollo de software   77
Una variante también válida del diagrama de flujo anterior es:
Diagrama de flujo Pseudocódigo
Inicio
HORAS < = 40
Leer
HORAS, PRECIO_HORA
NOMBRE
SALARIO =
HORAS*
PRECIO HORA
SALARIO =
40* PRECIO HORA +
1,5* PRECIO HORA
(HORAS – 40)
¿más datos?
SALARIO
Fin
sí
sí no
no
Escribir
real: horas, precioHora, salario
cadena: nombre
caracter: masDatos
inicio
masDatos ← 'S';
escribir (' Introducir horas, precio hora y 
nombre')
mientras ( masDatos = 'S' o masDatos = 's')
hacer
  escribir ('Nombre')
  leer (nombre)
  escribir ('Horas trabajadas')
  leer (horas)
  escribir ('Precio hora')
  leer (PrecioHora)
  si horas <= 40 entonces
     salario ← horas * precioHora
  sino
      salario ← 40 * precioHora + 1.5 * 
(horas – 40) * precioHora
  fin si
  escribir ('Salario de', nombre, salario)
  escribir ('Mas trabajadores (S/N)')
  leer (masDatos)
fin mientras
fin
 
EJEMPLO 2.10
La escritura de algoritmos para realizar operaciones sencillas de conteo es una de las primeras cosas que una com-
putadora puede aprender.
Supongamos que se proporciona una secuencia de números, tales como
5 3 0 2 4 4 0 0 2 3 6 0 2
y desea contar e imprimir el número de ceros de la secuencia .
El algoritmo es muy sencillo, ya que sólo basta leer los números de izquierda a derecha, mientras se cuentan los 
ceros. Utiliza como variable la palabra NUMERO para los números que se examinan y TOTAL para el número de ce-
ros encontrados. Los pasos a seguir son:
1. Establecer TOTAL a cero.
2. ¿Quedan más numeros a examinar?
3. Si no quedan numeros, imprimir el valor de TOTAL y fin.