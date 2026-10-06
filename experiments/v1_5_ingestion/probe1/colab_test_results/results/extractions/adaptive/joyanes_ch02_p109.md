## EJEMPLO 2.11

Dados tres números, determinar si la suma de cualquier pareja de ellos es igual al tercer número. Si se cumple esta condición, escribir "Iguales" y, en caso contrario, escribir "Distintas".

En el caso de que los números sean: 3 9 6

la respuesta es "Iguales", ya que 3 + 6 = 9. Sin embargo, si los números fueran:

2 3 4

el resultado sería "Distintas".

Para resolver este problema, se puede comparar la suma de cada pareja con el tercer número. Con tres números solamente existen tres parejas distintas y el algoritmo de resolución del problema será fácil.

```
1. Leer los tres valores, A, B y C. 2. Si A + B = C escribir "Iguales" y parar. 3. Si A + C = B escribir "Iguales" y parar. 4. Si B + C = A escribir "Iguales" y parar. 5. Escribir "Distintas" y parar.
```

El diagrama de flujo y la codificación en pseudocódigo correspondiente es la Figura 2.19.

## Diagrama de flujo

## Pseudocódigo

Figura 2.19. Diagrama de flujo y codificación en pseudocódigo (Ejemplo 2.11).

<!-- image -->