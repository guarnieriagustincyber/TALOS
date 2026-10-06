74  Fundamentos de programación
El primer paso a dar en el desarrollo del algoritmo es descomponer el problema en una serie de pasos secuencia-
les. Para calcular una media se necesita sumar y contar los valores. Por consiguiente, nuestro algoritmo en forma 
descriptiva sería:
1. Inicializar contador de números C y variable suma S.
2. Leer un número.
3.  Si el número leído es cero:
• calcular la media;
• imprimir la media;
• fin del proceso.
Si el número leído no es cero:
• calcular la suma;
• incrementar en uno el contador de números;
• ir al paso 2.
4. Fin.
El refinamiento del algoritmo conduce a los pasos sucesivos necesarios para realizar las operaciones de lectura, 
verificación del último dato, suma y media de los datos.
Si el primer dato leído es 0, la división S/C produciría un error si el algoritmo se ejecutara en una computadora, 
ya que en ella no está permitida la división por cero.
Terminal
C - contador de números
S - sumador de números
C 0
S 0
leer dato
dato <> 0
 C C + 1
S S + dato
media       S/C
Imprimir
media
Fin
Si el primer dato leído es 0, la
división s/c producirá un error si
el algoritmo se ejecutara en una
computadora, ya que en ella no
está permitida la división por cero.
entero: dato, C
Real: Media, S
C ← 0
S ← 0
escribir('Datos numéricos; 
     para finalizar se introduce 0')
repetir
  leer(dato)
  si dato <> = 0 entonces
     C ← C + 1
     S ← S + dato
  fin_si
hasta dato = 0
{Calcula la media y la escribe}
si (C > 0) entonces
    Media ← S/C
    escribir (Media)
fin_si
PseudocódigoDiagrama de flujo
 