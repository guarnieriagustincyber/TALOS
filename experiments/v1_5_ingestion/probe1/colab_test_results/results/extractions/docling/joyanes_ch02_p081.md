## EJEMPLO 2.2

Calcular el valor de la suma 1+2+3+...+100.

## algoritmo

Se utiliza una variable Contador como un contador que genere los sucesivos números enteros, y Suma para almacenar las sumas parciales 1, 1+2, 1+2+3…

```
1. Establecer Contador a 1 2. Establecer Suma a 0 3. mientras Contador <= 100 hacer Sumar Contador a Suma Incrementar Contador en 1 fin_mientras 4. Visualizar Suma
```

## 2.1.4. Codificación de un programa

La codificación es la escritura en un lenguaje de programación de la representación del algoritmo desarrollada en las etapas precedentes. Dado que el diseño de un algoritmo es independiente del lenguaje de progra mación utilizado para su implementación, el código puede ser escrito con igual facilidad en un lenguaje o en otro.

Para realizar la conversión del algoritmo en programa se deben sustituir las palabras reservadas en español por sus homónimos en inglés, y las operaciones/instrucciones indicadas en lenguaje natural por el lenguaje de programación correspondiente.

```
{Este programa obtiene una tabla de depreciaciones acumuladas y valores reales de cada año de un determinado producto} algoritmo primero Real: Coste, Depreciacion, Valor_Recuperacion Valor_Actual, Acumulado Valor_Anual; entero: Año, Vida_Util; inicio escribir('introduzca coste, valor recuperación y vida útil') leer(Coste, Valor_Recuperacion, Vida_Util) escribir('Introduzca año actual') leer(Año) Valor_Actual ← Coste; Depreciacion ← (Coste-Valor_Recuperacion)/Vida_Util Acumulado ← 0 escribir('Año Depreciación Dep. Acumulada') mientras (Año < Vida_Util) Acumulado ← Acumulado + Depreciacion Valor_Actual ← Valor_Actual - Depreciacion escribir('Año, Depreciacion, Acumulado') Año ← Año + 1; fin mientras fin
```