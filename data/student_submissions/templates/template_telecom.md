# Ejercicio: [nombre_del_ejercicio_telecom]

## Enunciado
[Descripción del escenario de telecomunicaciones, enlaces de fibra, radiofrecuencia o protocolos de red]

## Fórmulas
```
Atenuación_total (dB) = (Atenuación_fibra × Distancia) + (Pérdida_conectores × Cantidad) + (Pérdida_empalmes × Cantidad)
Margen_potencia (dB) = Potencia_Tx (dBm) - Sensibilidad_Rx (dBm) - Atenuación_total (dB)
```

## Cálculos
```
Distancia = 15.0 km
Atenuación_fibra = 0.25 dB/km × 15 km = 3.75 dB
Pérdida_conectores = 0.50 dB × 4 = 2.00 dB
Pérdida_empalmes = 0.10 dB × 5 = 0.50 dB
Atenuación_total = 3.75 + 2.00 + 0.50 = 6.25 dB

Potencia_Tx = +3.0 dBm
Sensibilidad_Rx = -28.0 dBm
Margen_potencia = 3.0 - (-28.0) - 6.25 = 24.75 dB
```

## Resultado
El enlace presenta una atenuación acumulada de **6.25 dB** y un margen de seguridad de potencia de **24.75 dB**.

## Análisis
[Evaluación de la viabilidad del enlace frente a los requerimientos de la norma ITU-T, dispersión cromática y degradación ambiental]
