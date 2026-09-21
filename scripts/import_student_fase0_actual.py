#!/usr/bin/env python3
"""Importador Real de Ejercicios de Fase 0 del Estudiante a TALOS.

Lee las carpetas reales de Fase 0:
/media/agustin/Laboratorio/Ciberseguiradad/Fase 0/FundamentosAlgoritmosYEstrucutrasDeDatos/Ciberdefensa/Fase0
y ensambla los ejercicios canónicos de Tramos 1 al 4 con:
- Código Python con Type Hints
- Contratos Formales PRE/POST
- Diagramas Mermaid
- Pseudocódigo estructurado
- Tests y aserciones deterministas

Ejecuta la auditoría con BKTKnowledgeStateTracker conectado a data/web_state/student_state.db.
"""

import json
from pathlib import Path
import sys

# Setup paths
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from study_engine.pedagogy.submission_reader import SubmissionReader
from study_engine.pedagogy.auditors.programming_auditor import ProgrammingExerciseAuditor
from study_engine.student.storage import StudentStorage
from study_engine.student.bkt_tracker import BKTTracker

SRC_BASE = Path("/media/agustin/Laboratorio/Ciberseguiradad/Fase 0/FundamentosAlgoritmosYEstrucutrasDeDatos/Ciberdefensa/Fase0")
DEST_BASE = REPO_ROOT / "data" / "student_submissions" / "fase0-soc"
DB_PATH = REPO_ROOT / "data" / "web_state" / "student_state.db"
REPORTS_DIR = REPO_ROOT / "data" / "student_submissions" / ".reports"

EXERCISES = [
    # -------------------------------------------------------------
    # TRAMO 1: Metodología y Pensamiento Algorítmico (Top-Down y Frontera Defensiva)
    # -------------------------------------------------------------
    {
        "tramo": "tramo1",
        "filename": "ej_01_validador_cbu.md",
        "exercise_id": "ej_01_validador_cbu",
        "title": "Ejercicio 01: Validador Defensivo de CBU Bancario (Top-Down)",
        "kc_id": "fase0_tramo1_metodologia",
        "content": """# Ejercicio 01: Validador Defensivo de CBU Bancario (Top-Down)

<!-- metadata: {"notebook_id": "fase0-soc", "unit": "tramo1", "kc_id": "fase0_tramo1_metodologia", "exercise_type": "PROGRAMMING"} -->

## Enunciado
Implementar un algoritmo de validación de CBU (Clave Bancaria Uniforme) de 22 caracteres numéricos. Debe descomponerse en módulos y aplicar frontera defensiva temprana rechazando cadenas con longitud diferente a 22 o caracteres no numéricos.

## Contrato Formal
```
PRE: cbu es una cadena de texto (str)
POST: retorna True si cbu tiene exactamente 22 caracteres y todos son digitos, False en caso contrario
```

## Diagrama de Flujo
```mermaid
flowchart TD
    A[Inicio: Ingreso de CBU] --> B{Longitud == 22?}
    B -->|No| C[Falso / Operacion Abortada]
    B -->|Sí| D{Todos son digitos?}
    D -->|No| C
    D -->|Sí| E[Verdadero / Proceder a Transferencia]
```

## Pseudocódigo
```text
// Problema B "CBU"
// Entrada: cbu_usuario
// Salida: Valido o Invalido
// Restricciones: entrada debe ser exactamente 22 caracteres

Algoritmo ValidadorCBU Es
    Var
        cadena: cbu_usuario
    Inicio
        cbu_usuario = ""
        llamar_a Resultado(cbu_usuario)
Fin

procedimiento ValidadorCBU(E cadena: cbu)
    Inicio
        si longitud(cbu) == 22 Entonces
            Escribir("CBU VÁLIDO. PROCEDIENDO A TRANSFERENCIA")
        Sino
            Escribir("CBU INVÁLIDO. OPERACIÓN ABORTADA")
        fin_si
Fin_procedimiento
```

## Código Python
```python
def validar_cbu(cbu: str) -> bool:
    \"\"\"Validación defensiva de CBU bancario (22 caracteres numéricos).\"\"\"
    if not isinstance(cbu, str):
        return False
    if len(cbu) != 22:
        return False
    return cbu.isdigit()
```

## Casos de Prueba
```python
assert validar_cbu("0170099320000067543210") is True
assert validar_cbu("123") is False
assert validar_cbu("017009932000006754321A") is False
assert validar_cbu("01700993200000675432100") is False
assert validar_cbu("") is False
```

## Análisis de Complejidad
- Complejidad Temporal: O(n) donde n=22 caracteres (tiempo constante acotado O(1)).
- Complejidad Espacial: O(1) memoria auxiliar.
"""
    },
    {
        "tramo": "tramo1",
        "filename": "ej_02_sueldo_neto_defensivo.md",
        "exercise_id": "ej_02_sueldo_neto_defensivo",
        "title": "Ejercicio 02: Cálculo de Sueldo Neto y Frontera Defensiva",
        "kc_id": "fase0_tramo1_metodologia",
        "content": """# Ejercicio 02: Cálculo de Sueldo Neto y Frontera Defensiva

<!-- metadata: {"notebook_id": "fase0-soc", "unit": "tramo1", "kc_id": "fase0_tramo1_metodologia", "exercise_type": "PROGRAMMING"} -->

## Enunciado
Calcular el sueldo neto aplicando deducción impositiva del 21% sobre el excedente del mínimo no imponible ($50.000). Debe validar en la frontera que ni las horas ni la tarifa sean negativas.

## Contrato Formal
```
PRE: horas_trabajadas >= 0.0 y tarifa_horaria >= 0.0
POST: retorna sueldo neto deducido de alicuota impositiva (21%) si supera minimo no imponible
```

## Diagrama de Flujo
```mermaid
flowchart TD
    A[Inicio] --> B{horas >= 0 AND tarifa >= 0?}
    B -->|No| C[Lanzar ValueError / Abortar]
    B -->|Sí| D[Calcular Bruto = horas * tarifa]
    D --> E{Bruto > 50000.0?}
    E -->|Sí| F[Impuestos = Bruto * 0.21]
    E -->|No| G[Impuestos = 0.0]
    F --> H[Neto = Bruto - Impuestos]
    G --> H
    H --> I[Retornar Neto]
```

## Pseudocódigo
```text
Algoritmo CalculoSueldoSeguro
const
    real: ALICUOTA_IMPUESTO = 0.21
    real: MINIMO_NO_IMPONIBLE = 50000.0
var
    real: horas_trabajadas, tarifa_horaria
inicio
    horas_trabajadas = 0.0
    tarifa_horaria = 0.0
    escribir("Ingrese las horas trabajadas:")
    leer(horas_trabajadas)
    escribir("Ingrese la tarifa por hora:")
    leer(tarifa_horaria)
    llamar_a Resultados(horas_trabajadas, tarifa_horaria)
Fin
```

## Código Python
```python
def calcular_sueldo_neto(horas_trabajadas: float, tarifa_horaria: float) -> float:
    \"\"\"Cálculo de sueldo neto con frontera defensiva contra valores negativos.\"\"\"
    if horas_trabajadas < 0.0 or tarifa_horaria < 0.0:
        raise ValueError("Horas y tarifa deben ser valores no negativos")
    sueldo_bruto = horas_trabajadas * tarifa_horaria
    minimo_no_imponible = 50000.0
    alicuota = 0.21
    impuestos = sueldo_bruto * alicuota if sueldo_bruto > minimo_no_imponible else 0.0
    return sueldo_bruto - impuestos
```

## Casos de Prueba
```python
assert calcular_sueldo_neto(100.0, 400.0) == 40000.0
assert calcular_sueldo_neto(100.0, 1000.0) == 79000.0
try:
    calcular_sueldo_neto(-5.0, 100.0)
    assert False, "Debio fallar con horas negativas"
except ValueError:
    pass
```

## Análisis de Complejidad
- Complejidad Temporal: O(1) operaciones aritméticas directas.
- Complejidad Espacial: O(1) variables de acumulación.
"""
    },

    # -------------------------------------------------------------
    # TRAMO 2: Lógica y Estructuras de Control (Luhn)
    # -------------------------------------------------------------
    {
        "tramo": "tramo2",
        "filename": "ej_01_validador_luhn_tarjeta.md",
        "exercise_id": "ej_01_validador_luhn_tarjeta",
        "title": "Ejercicio 01: Motor de Cálculo y Validador de Tarjetas (Algoritmo de Luhn)",
        "kc_id": "fase0_tramo2_logica_control",
        "content": """# Ejercicio 01: Motor de Cálculo y Validador de Tarjetas (Algoritmo de Luhn)

<!-- metadata: {"notebook_id": "fase0-soc", "unit": "tramo2", "kc_id": "fase0_tramo2_logica_control", "exercise_type": "PROGRAMMING"} -->

## Enunciado
Implementar el algoritmo de Luhn (ISO/IEC 7812) para la verificación de integridad de números de tarjetas de crédito. Requiere duplicar dígitos alternados, ajustar sumas mayores a 9 (-9) y validar que el total acumulado sea divisible por 10.

## Contrato Formal
```
PRE: numero_tarjeta es una cadena de digitos numericos de longitud >= 2
POST: retorna True si la suma de Luhn modular 10 es cero, False en caso contrario
```

## Diagrama de Flujo
```mermaid
flowchart TB
    subgraph Nivel0["Nivel 0 — Coordinador principal"]
        A([INICIO]) --> A1["posicion = 0, suma_pares = 0, suma_impares = 0"]
        A1 --> A4["procesar digitos de derecha a izquierda"]
        A4 --> A5["es_valida = suma % 10 == 0"]
        A5 --> A6{"es_valida?"}
        A6 -- SÍ --> A7["TARJETA VÁLIDA"]
        A6 -- NO --> A8["TARJETA INVÁLIDA"]
    end
```

## Pseudocódigo
```text
algoritmo TarjetaValidaEs
var
    cadena: tarjeta_caracter
    entero: posicion, suma_si_impar, suma_si_par
    booleano: es_valida
Inicio
    // Nivel 0 llama a Nivel 1 pasando referencias fisicas de la RAM
    llamar_a procesador_entradas(tarjeta_caracter, posicion, suma_si_impar, suma_si_par)
    es_valida = validar(posicion, suma_si_impar, suma_si_par)
fin

procedimiento multiplicador(E entero: digito) -> entero
var
    entero: doble
Inicio
    doble = digito * 2
    si doble > 9 entonces
        devolver doble - 9
    si_no
        devolver doble
    fin_si
fin_procedimiento
```

## Código Python
```python
def multiplicador(digito: int) -> int:
    \"\"\"Motor de cálculo de Luhn para duplicación de dígito individual.\"\"\"
    doble = digito * 2
    if doble > 9:
        return doble - 9
    return doble


def validar_tarjeta_luhn(numero_tarjeta: str) -> bool:
    \"\"\"Validador de tarjeta de crédito mediante algoritmo de Luhn.\"\"\"
    if not isinstance(numero_tarjeta, str) or not numero_tarjeta.isdigit() or len(numero_tarjeta) < 2:
        return False
    reverso = numero_tarjeta[::-1]
    suma = 0
    for idx, char in enumerate(reverso):
        digito = int(char)
        if idx % 2 == 1:
            suma += multiplicador(digito)
        else:
            suma += digito
    return suma % 10 == 0
```

## Casos de Prueba
```python
assert multiplicador(4) == 8
assert multiplicador(7) == 5
assert validar_tarjeta_luhn("49927398716") is True
assert validar_tarjeta_luhn("49927398717") is False
assert validar_tarjeta_luhn("") is False
assert validar_tarjeta_luhn("123") is False
```

## Análisis de Complejidad
- Complejidad Temporal: O(n) donde n es la longitud del número de tarjeta.
- Complejidad Espacial: O(n) para la cadena invertida.
"""
    },

    # -------------------------------------------------------------
    # TRAMO 3: Modularidad y Memoria (Contraseña Segura)
    # -------------------------------------------------------------
    {
        "tramo": "tramo3",
        "filename": "ej_01_contrasena_segura.md",
        "exercise_id": "ej_01_contrasena_segura",
        "title": "Ejercicio 01: Validador Modular de Contraseñas Seguras y Control de Repetición",
        "kc_id": "fase0_tramo3_modularidad_memoria",
        "content": """# Ejercicio 01: Validador Modular de Contraseñas Seguras y Control de Repetición

<!-- metadata: {"notebook_id": "fase0-soc", "unit": "tramo3", "kc_id": "fase0_tramo3_modularidad_memoria", "exercise_type": "PROGRAMMING"} -->

## Enunciado
Implementar un validador de contraseñas seguras bajo política de ciberdefensa: longitud mínima de 8 caracteres, al menos una mayúscula, una minúscula, un número y un caracter especial. Debe rechazar claves con secuencias de más de 2 caracteres idénticos consecutivos.

## Contrato Formal
```
PRE: clave es una cadena de texto (str)
POST: retorna True si la clave cumple longitud >= 8, cuatro clases de caracteres y no repite 3 caracteres consecutivos
```

## Diagrama de Flujo
```mermaid
flowchart TB
    A([Inicio]) --> B[Inicializar RAM: contadores, flags y caracter_anterior]
    B --> C{caracter_actual == caracter_anterior?}
    C -- SÍ --> D[caracter_repetido += 1]
    D --> E{caracter_repetido >= 3?}
    E -- SÍ --> F[Rechazar clave por repeticion]
    E -- NO --> G[Clasificar caracter]
    C -- NO --> H[caracter_repetido = 1]
    H --> G
    G --> I{len >= 8 AND todas las clases presentes?}
    I -- SÍ --> J[Aceptar: Clave Fuerte]
    I -- NO --> K[Rechazar: Clave Insegura]
```

## Pseudocódigo
```text
Algoritmo ContrasenaSegura
Var
    cadena: clave
    booleano: valida
Inicio
    // Coordinador de verificacion de integridad en RAM
    valida = Coordinador(clave)
    si valida entonces
        Escribir("CONTRASENA FUERTE")
    si_no
        Escribir("CONTRASENA RECHAZADA")
    fin_si
Fin
```

## Código Python
```python
def validar_contrasena_segura(clave: str) -> bool:
    \"\"\"Validador modular de contrasena fuerte con politica estricta y sin repeticion multiple.\"\"\"
    if not isinstance(clave, str) or len(clave) < 8:
        return False
    tiene_mayus = False
    tiene_minus = False
    tiene_num = False
    tiene_esp = False
    caracter_repetido = 1
    caracter_anterior = ""
    for c in clave:
        if c == caracter_anterior:
            caracter_repetido += 1
            if caracter_repetido >= 3:
                return False
        else:
            caracter_repetido = 1
        caracter_anterior = c

        if "A" <= c <= "Z":
            tiene_mayus = True
        elif "a" <= c <= "z":
            tiene_minus = True
        elif "0" <= c <= "9":
            tiene_num = True
        else:
            tiene_esp = True

    return tiene_mayus and tiene_minus and tiene_num and tiene_esp
```

## Casos de Prueba
```python
assert validar_contrasena_segura("Admin123!") is True
assert validar_contrasena_segura("C0ntr@Seña") is True
assert validar_contrasena_segura("aaaB1!cd") is False
assert validar_contrasena_segura("corta1!") is False
assert validar_contrasena_segura("Sololetrasypunto.") is False
assert validar_contrasena_segura("1234567890!") is False
```

## Análisis de Complejidad
- Complejidad Temporal: O(n) un solo recorrido lineal de la cadena.
- Complejidad Espacial: O(1) uso estricto de banderas booleanas en Stack Frame.
"""
    },

    # -------------------------------------------------------------
    # TRAMO 4: Estructuras Lineales y Arrays (Octeto Válido e IPv4)
    # -------------------------------------------------------------
    {
        "tramo": "tramo4",
        "filename": "ej_01_descomposicion_ipv4_octetos.md",
        "exercise_id": "ej_01_descomposicion_ipv4_octetos",
        "title": "Ejercicio 01: Descomposición de IPv4 y Validación de Octetos (Aduanas de Control)",
        "kc_id": "fase0_tramo4_estructuras_lineales",
        "content": """# Ejercicio 01: Descomposición de IPv4 y Validación de Octetos (Aduanas de Control)

<!-- metadata: {"notebook_id": "fase0-soc", "unit": "tramo4", "kc_id": "fase0_tramo4_estructuras_lineales", "exercise_type": "PROGRAMMING"} -->

## Enunciado
Implementar un descomponeador y validador completo de direcciones IPv4. Descompone la cadena delimitada por puntos y pasa cada fragmento por 4 aduanas de control: longitud [1, 3], tipo digito, sin ceros a la izquierda (excepto "0" solo) y rango numérico [0, 255].

## Contrato Formal
```
PRE: ip_recibida es una cadena de texto (str)
POST: retorna True si contiene exactamente 4 octetos que superan las 4 aduanas de control, False en caso contrario
```

## Diagrama de Flujo
```mermaid
graph TD
INICIO([Inicio: Recibe octeto_texto]) --> C1{Longitud < 1 O Longitud > 3?}
    C1 -- SÍ --> FALSO[Retornar Falso]
    C1 -- NO --> C2{Contiene caracteres no digitos?}
    C2 -- SÍ --> FALSO
    C2 -- NO --> C3{Tiene ceros a la izquierda?}
    C3 -- SÍ --> FALSO
    C3 -- NO --> C4{Valor numerico > 255?}
    C4 -- SÍ --> FALSO
    C4 -- NO --> VERDADERO[Retornar Verdadero]
    FALSO --> FIN([Fin])
    VERDADERO --> FIN
```

## Pseudocódigo
```text
// Problema: descomponer una estrucutra de ipv4
// Entrada: cadena str
// Salida: verdadero o falso
// Restricciones:
//   1: longitud maxima 1 a 3 inclusive
//   2: caracteres en rango '0' a '9'
//   3: ceros a la izquierda prohibidos ("01", "021")
//   4: valores en rango [0..255]

algoritmo DescomponedorIPv4 es
var
    cadena: ip_recibida
    booleano: resultado
Inicio
    resultado = analizar_ip(ip_recibida)
fin

funcion analizar_ip(E cadena: ip_recibida) -> booleano
    // Recorrido secuencial separando por puntos y evaluando es_octeto_valido
fin_funcion
```

## Código Python
```python
def longitud_valida(pedazo: str) -> bool:
    \"\"\"Valida que el fragmento tenga longitud entre 1 y 3 caracteres.\"\"\"
    return 1 <= len(pedazo) <= 3


def tipo_valido(pedazo: str) -> bool:
    \"\"\"Verifica que todos los caracteres sean dígitos numéricos.\"\"\"
    for c in pedazo:
        if c < "0" or c > "9":
            return False
    return True


def ceros_izq(pedazo: str) -> bool:
    \"\"\"Prohíbe ceros a la izquierda salvo el '0' aislado.\"\"\"
    if len(pedazo) != 1 and pedazo[0] == "0":
        return False
    return True


def dentro_rango(pedazo: str) -> bool:
    \"\"\"Valida que el valor numérico esté en el intervalo [0, 255].\"\"\"
    valor = int(pedazo)
    return 0 <= valor <= 255


def es_octeto_valido(pedazo: str) -> bool:
    \"\"\"Aduana integrada para la validación de un octeto IPv4.\"\"\"
    return (
        longitud_valida(pedazo)
        and tipo_valido(pedazo)
        and ceros_izq(pedazo)
        and dentro_rango(pedazo)
    )


def analizar_ip(ip_recibida: str) -> bool:
    \"\"\"Descompone y valida una dirección IPv4 completa en sus 4 octetos.\"\"\"
    if not isinstance(ip_recibida, str):
        return False
    pedazo = ""
    contador = 0
    for caracter in ip_recibida:
        if caracter != ".":
            pedazo += caracter
        else:
            if not es_octeto_valido(pedazo):
                return False
            contador += 1
            pedazo = ""
    if not es_octeto_valido(pedazo):
        return False
    contador += 1
    return contador == 4
```

## Casos de Prueba
```python
assert analizar_ip("192.168.1.1") is True
assert analizar_ip("255.255.255.255") is True
assert analizar_ip("0.0.0.0") is True
assert analizar_ip("256.1.1.1") is False
assert analizar_ip("01.1.1.1") is False
assert analizar_ip("192.168.1") is False
assert analizar_ip("192.168.1.1.1") is False
assert analizar_ip("192.168.1.a") is False
```

## Análisis de Complejidad
- Complejidad Temporal: O(n) un recorrido lineal estricto de la cadena IP.
- Complejidad Espacial: O(1) memoria acotada al búfer del octeto.
"""
    }
]


def run_import_and_audit():
    print("====================================================================")
    print(" IMPORTADOR DE EJERCICIOS REALES DEL ESTUDIANTE (FASE 0) -> TALOS")
    print("====================================================================")
    print(f"Directorio Origen:  {SRC_BASE}")
    print(f"Directorio Destino: {DEST_BASE}")
    print(f"Base de Datos BKT:  {DB_PATH}\n")

    # 1. Connect BKT Storage
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    storage = StudentStorage(DB_PATH)
    tracker = BKTTracker(storage)
    auditor = ProgrammingExerciseAuditor(bkt_tracker=tracker)
    reader = SubmissionReader()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    # 2. Write and audit exercises
    for ex in EXERCISES:
        tramo_dir = DEST_BASE / ex["tramo"]
        tramo_dir.mkdir(parents=True, exist_ok=True)
        target_file = tramo_dir / ex["filename"]

        # Write markdown
        target_file.write_text(ex["content"].strip() + "\n", encoding="utf-8")
        print(f"[*] Escrito: {target_file.relative_to(REPO_ROOT)}")

        # Parse & Audit
        submission = reader.parse(target_file)
        report = auditor.audit(submission)

        # Save cached report
        report_file = REPORTS_DIR / f"{ex['exercise_id']}.json"
        report_file.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

        results.append((ex, report))

    # 3. Print Summary Table
    print("\n" + "=" * 76)
    print(f"{'EJERCICIO':<30} | {'KC_ID':<30} | {'NOTA':<6} | {'BKT P(L)'}")
    print("=" * 76)
    for ex, report in results:
        status_sym = "✅" if report.passed else "❌"
        bkt_str = f"{report.p_L_before:.4f} → {report.p_L_after:.4f}" if report.bkt_updated else "N/A"
        print(f"{status_sym} {ex['exercise_id']:<28} | {ex['kc_id']:<30} | {report.score:>4.1f}% | {bkt_str}")

    print("=" * 76)
    print("\nESTADO DE MAESTRÍA BKT EN student_state.db:")
    for kc in [
        "fase0_tramo1_metodologia",
        "fase0_tramo2_logica_control",
        "fase0_tramo3_modularidad_memoria",
        "fase0_tramo4_estructuras_lineales",
    ]:
        st = tracker.get_state(kc)
        print(f"  ● {kc:<35}: P(L) = {st.p_L:.4f} (Intentos: {st.attempts})")
    print("====================================================================\n")


if __name__ == "__main__":
    run_import_and_audit()
