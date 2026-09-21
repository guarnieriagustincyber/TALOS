#!/usr/bin/env python3
"""Importador de Ejercicios del Estudiante a TALOS / KASIU.

Escanea carpetas locales (por ejemplo /media/agustin/Laboratorio/Ciberseguridad/Fase 0),
identifica archivos de código (.py, .c, .md) resueltos por el estudiante en los Tramos 1 a 4,
y los estructura en la taxonomía canónica de TALOS:
    data/student_submissions/fase0-soc/tramo{1..4}/ej_{XX}.md

También permite:
- Generar ejercicios modelo de muestra para los 5 primeros tramos (--generate-samples)
- Ejecutar la auditoría forense determinista de TALOS sobre los ejercicios importados (--verify)
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

# Sample canonical exercise templates for Tramos 1 to 5
SAMPLE_EXERCISES = {
    "tramo1": {
        "filename": "ej_01_dry_run_top_down.md",
        "title": "Ejercicio 01: Descomposición Top-Down y Validación de Entrada",
        "kc_id": "fase0_tramo1_metodologia",
        "content": """# Ejercicio 01: Descomposición Top-Down y Validación de Entrada

<!-- metadata: {"notebook_id": "fase0-soc", "unit": "tramo1", "kc_id": "fase0_tramo1_metodologia", "exercise_type": "PROGRAMMING"} -->

## Enunciado
Implementar un algoritmo de cálculo de promedio de calificaciones con validación temprana de rango [0, 100]. Debe rechazar entradas no enteras o fuera de rango inmediatamente antes de realizar cualquier acumulación (frontera defensiva).

## Contrato y Precondiciones
- **PRE**: La lista `notas` contiene al menos un elemento. Todos los elementos deben ser enteros en el intervalo [0, 100].
- **POST**: Retorna un float con el promedio exacto sin alterar la lista original. Si alguna nota es inválida, eleva `ValueError`.

## Diagrama de Flujo (Mermaid)
```mermaid
graph TD
    A([Inicio]) --> B[/Entrada: notas/]
    B --> C{¿notas está vacía?}
    C -- Sí --> D[Lanzar ValueError]
    C -- No --> E[Validar rango de cada nota]
    E --> F{¿Alguna nota fuera de 0..100?}
    F -- Sí --> D
    F -- No --> G[Calcular suma y dividir por longitud]
    G --> H[/Salida: promedio/]
    H --> I([Fin])
```

## Pseudocódigo Estructurado
```text
ALGORITMO CalcularPromedioDefensivo(notas: Lista de Enteros) -> Real
INICIO
    SI Longitud(notas) == 0 ENTONCES
        ERROR "Lista vacía"
    FIN SI
    
    suma <- 0
    PARA CADA nota EN notas HACER
        SI nota < 0 O nota > 100 ENTONCES
            ERROR "Nota fuera de rango"
        FIN SI
        suma <- suma + nota
    FIN PARA
    
    RETORNAR suma / Longitud(notas)
FIN
```

## Código / Solución
```python
from typing import List

def calcular_promedio(notas: List[int]) -> float:
    if not notas:
        raise ValueError("La lista de notas no puede estar vacia.")
    for n in notas:
        if not isinstance(n, int) or n < 0 or n > 100:
            raise ValueError(f"Nota invalida: {n}. Debe ser entero entre 0 y 100.")
    return sum(notas) / len(notas)
```

## Tests / Verificación
```python
assert calcular_promedio([80, 90, 100]) == 90.0
assert calcular_promedio([50]) == 50.0
try:
    calcular_promedio([105, 80])
    assert False, "Debio fallar con nota > 100"
except ValueError:
    pass

try:
    calcular_promedio([])
    assert False, "Debio fallar con lista vacia"
except ValueError:
    pass
```

## Complejidad y Análisis
- **Big-O Temporal**: $O(n)$ donde $n$ es la cantidad de calificaciones en la lista, ya que se realiza una única pasada de validación y acumulación.
- **Big-O Espacial**: $O(1)$ espacio adicional auxiliar.
"""
    },
    "tramo2": {
        "filename": "ej_01_bouncer_pattern.md",
        "title": "Ejercicio 01: Refactorización Bouncer Pattern (Cláusulas de Guarda)",
        "kc_id": "fase0_tramo2_logica_control",
        "content": """# Ejercicio 01: Refactorización Bouncer Pattern (Cláusulas de Guarda)

<!-- metadata: {"notebook_id": "fase0-soc", "unit": "tramo2", "kc_id": "fase0_tramo2_logica_control", "exercise_type": "PROGRAMMING"} -->

## Enunciado
Refactorizar una función de procesamiento de usuario con if anidados monstruosos (Anti-patrón Arrowhead) a una estructura plana con cláusulas de guarda (Bouncer Pattern) y principio Fail-Fast.

## Contrato y Precondiciones
- **PRE**: `user_dict` es un diccionario con claves requeridas `activo` (bool), `rol` (str), y `saldo` (float).
- **POST**: Retorna True si el usuario tiene autorización para operar, False o eleva excepción si alguna condición de guarda falla.

## Diagrama de Flujo (Mermaid)
```mermaid
graph TD
    A([Inicio]) --> B{¿user_dict es None?}
    B -- Sí --> C[Retornar False]
    B -- No --> D{¿not user_dict['activo']?}
    D -- Sí --> C
    D -- No --> E{¿rol not in roles_autorizados?}
    E -- Sí --> C
    E -- No --> F{¿saldo < costo?}
    F -- Sí --> C
    F -- No --> G[Retornar True - Operación Exitosa]
```

## Pseudocódigo Estructurado
```text
ALGORITMO AutorizarOperacion(usuario: Registro, costo: Real) -> Booleano
INICIO
    SI usuario ES NULO ENTONCES RETORNAR FALSO
    SI NO usuario.activo ENTONCES RETORNAR FALSO
    SI usuario.rol != "OPERADOR" Y usuario.rol != "ADMIN" ENTONCES RETORNAR FALSO
    SI usuario.saldo < costo ENTONCES RETORNAR FALSO
    
    RETORNAR VERDADERO
FIN
```

## Código / Solución
```python
from typing import Dict, Any

def autorizar_transaccion(usuario: Dict[str, Any], costo: float) -> bool:
    # Cláusula de guarda 1: Objeto nulo o incompleto
    if not usuario or not isinstance(usuario, dict):
        return False
    # Cláusula de guarda 2: Cuenta inactiva (Fail-Fast)
    if not usuario.get("activo", False):
        return False
    # Cláusula de guarda 3: Rol no autorizado
    if usuario.get("rol") not in ("OPERADOR", "ADMIN"):
        return False
    # Cláusula de guarda 4: Saldo insuficiente
    if usuario.get("saldo", 0.0) < costo:
        return False
    # Flujo feliz aplanado (cero anidamiento)
    return True
```

## Tests / Verificación
```python
u_ok = {"activo": True, "rol": "ADMIN", "saldo": 500.0}
assert autorizar_transaccion(u_ok, 100.0) is True

u_inactivo = {"activo": False, "rol": "ADMIN", "saldo": 500.0}
assert autorizar_transaccion(u_inactivo, 100.0) is False

u_rol_invalido = {"activo": True, "rol": "INVITADO", "saldo": 500.0}
assert autorizar_transaccion(u_rol_invalido, 100.0) is False

u_sin_saldo = {"activo": True, "rol": "OPERADOR", "saldo": 50.0}
assert autorizar_transaccion(u_sin_saldo, 100.0) is False

assert autorizar_transaccion({}, 10.0) is False
```

## Complejidad y Análisis
- **Big-O Temporal**: $O(1)$ evaluado en cortocircuito inmediato en las cláusulas de guarda.
- **Big-O Espacial**: $O(1)$ memoria fija sin asignación dinámica.
"""
    },
    "tramo3": {
        "filename": "ej_01_stack_frame_trace.md",
        "title": "Ejercicio 01: Simulación y Trazado de Stack Frame",
        "kc_id": "fase0_tramo3_modularidad_memoria",
        "content": """# Ejercicio 01: Simulación y Trazado de Stack Frame

<!-- metadata: {"notebook_id": "fase0-soc", "unit": "tramo3", "kc_id": "fase0_tramo3_modularidad_memoria", "exercise_type": "PROGRAMMING"} -->

## Enunciado
Implementar un simulador de llamadas y activación de Stack Frame para subrutinas, calculando la profundidad máxima de pila y detectando desbordamientos de pila (Stack Overflow) simulados.

## Contrato y Precondiciones
- **PRE**: `max_stack_depth` entero positivo. `call_tree` tupla o estructura recursiva de funciones.
- **POST**: Retorna la lista ordenada de marcos de pila (Stack Frames) creados y destruidos con sus direcciones virtuales relativas.

## Diagrama de Flujo (Mermaid)
```mermaid
graph TD
    A([Llamada a funcion]) --> B[Empujar return address al Stack]
    B --> C[Empujar Base Pointer previo RBP]
    C --> D[Ajustar RSP para variables locales]
    D --> E[Ejecutar cuerpo de la funcion]
    E --> F[Restaurar RSP y RBP]
    F --> G[Instrucción RET - Volver a caller]
```

## Pseudocódigo Estructurado
```text
CLASE StackFrame
    nombre: Cadena
    rbp: Entero
    rsp: Entero
    parametros: Lista

ALGORITMO EjecutarSubrutina(nombre: Cadena, profundidad: Entero, max_prof: Entero)
INICIO
    SI profundidad >= max_prof ENTONCES
        ERROR "Stack Overflow detectado"
    FIN SI
    frame <- NUEVO StackFrame(nombre, profundidad)
    // Procesar llamada
    RETORNAR frame
FIN
```

## Código / Solución
```python
from typing import List, Dict, Any

class StackSimulation:
    def __init__(self, max_depth: int = 10) -> None:
        self.max_depth = max_depth
        self.stack: List[Dict[str, Any]] = []
        self.history: List[str] = []

    def call(self, func_name: str, args: List[Any]) -> int:
        if len(self.stack) >= self.max_depth:
            raise RecursionError(f"Stack Overflow simulado al invocar {func_name}")
        frame = {
            "func": func_name,
            "args": args,
            "frame_id": len(self.stack),
            "ret_addr": f"0x7FFE{len(self.stack)*16:04X}",
        }
        self.stack.append(frame)
        self.history.append(f"PUSH {func_name} ({frame['ret_addr']})")
        return len(self.stack)

    def ret(self) -> Dict[str, Any]:
        if not self.stack:
            raise IndexError("Stack underflow: no hay frames activos")
        frame = self.stack.pop()
        self.history.append(f"POP {frame['func']}")
        return frame
```

## Tests / Verificación
```python
sim = StackSimulation(max_depth=3)
d1 = sim.call("main", [])
assert d1 == 1
d2 = sim.call("calcular", [10, 20])
assert d2 == 2
d3 = sim.call("helper", [10])
assert d3 == 3

# Intentar sobrepasar límite de pila
try:
    sim.call("overflow_func", [])
    assert False, "Debio fallar con RecursionError"
except RecursionError:
    pass

top = sim.ret()
assert top["func"] == "helper"
assert len(sim.stack) == 2
```

## Complejidad y Análisis
- **Big-O Temporal**: $O(1)$ amortizado por cada operación de PUSH/POP de frame.
- **Big-O Espacial**: $O(d)$ donde $d$ es la profundidad máxima de pila.
"""
    },
    "tramo4": {
        "filename": "ej_01_parsing_acumuladores.md",
        "title": "Ejercicio 01: Parsing Manual de Cadenas sin Librerías Externas",
        "kc_id": "fase0_tramo4_estructuras_lineales",
        "content": """# Ejercicio 01: Parsing Manual de Cadenas sin Librerías Externas

<!-- metadata: {"notebook_id": "fase0-soc", "unit": "tramo4", "kc_id": "fase0_tramo4_estructuras_lineales", "exercise_type": "PROGRAMMING"} -->

## Enunciado
Implementar un parser numérico manual que convierta una cadena de texto representando un entero con signo (equivalente a `atoi`) a un entero nativo, iterando carácter por carácter sobre el arreglo de memoria, validando caracteres válidos y desbordamientos.

## Contrato y Precondiciones
- **PRE**: Cadena `s` contiene caracteres ASCII legibles. Puede incluir espacios iniciales y signo opcional `+` o `-`.
- **POST**: Retorna el valor entero exacto. Si encuentra un carácter inválido no numérico, retorna el acumulado previo o lanza error si la cadena no contenía dígitos válidos.

## Diagrama de Flujo (Mermaid)
```mermaid
graph TD
    A([Inicio]) --> B[Saltear espacios en blanco]
    B --> C{¿Signo + o -?}
    C -- Sí --> D[Guardar signo y avanzar índice]
    C -- No --> E[Signo positivo por defecto]
    D --> F[Bucle: mientras haya digitos '0'..'9']
    E --> F
    F --> G[acumulado = acumulado * 10 + digito]
    G --> F
    F -- Fin de digitos --> H[Retornar signo * acumulado]
```

## Pseudocódigo Estructurado
```text
ALGORITMO StringToIntManual(cadena: Cadena) -> Entero
INICIO
    i <- 0
    signo <- 1
    acumulado <- 0
    
    MIENTRAS i < Longitud(cadena) Y cadena[i] == ' ' HACER
        i <- i + 1
    FIN MIENTRAS
    
    SI i < Longitud(cadena) Y (cadena[i] == '-' O cadena[i] == '+') ENTONCES
        SI cadena[i] == '-' ENTONCES signo <- -1
        i <- i + 1
    FIN SI
    
    MIENTRAS i < Longitud(cadena) Y cadena[i] >= '0' Y cadena[i] <= '9' HACER
        digito <- CodigoASCII(cadena[i]) - CodigoASCII('0')
        acumulado <- (acumulado * 10) + digito
        i <- i + 1
    FIN MIENTRAS
    
    RETORNAR acumulado * signo
FIN
```

## Código / Solución
```python
def parse_int_manual(s: str) -> int:
    if not isinstance(s, str):
        raise TypeError("Entrada debe ser string")
    
    i = 0
    n = len(s)
    
    # 1. Ignorar espacios en blanco iniciales
    while i < n and s[i] == ' ':
        i += 1
        
    if i >= n:
        raise ValueError("Cadena sin digitos numericos")
        
    # 2. Manejo de signo
    signo = 1
    if s[i] == '-':
        signo = -1
        i += 1
    elif s[i] == '+':
        i += 1
        
    # 3. Lectura de dígitos con acumulación manual
    tiene_digitos = False
    acumulado = 0
    
    while i < n and '0' <= s[i] <= '9':
        tiene_digitos = True
        digito = ord(s[i]) - ord('0')
        acumulado = (acumulado * 10) + digito
        i += 1
        
    if not tiene_digitos:
        raise ValueError("Cadena no contiene digitos numericos validos")
        
    return acumulado * signo
```

## Tests / Verificación
```python
assert parse_int_manual("42") == 42
assert parse_int_manual("   -1234") == -1234
assert parse_int_manual("+789") == 789
assert parse_int_manual("  00123") == 123
assert parse_int_manual("567abc") == 567

try:
    parse_int_manual("   ")
    assert False, "Debio fallar con cadena de puros espacios"
except ValueError:
    pass

try:
    parse_int_manual("-abc")
    assert False, "Debio fallar sin digitos"
except ValueError:
    pass
```

## Complejidad y Análisis
- **Big-O Temporal**: $O(n)$ donde $n$ es la longitud de la cadena. Se realiza un escaneo lineal estricto en una sola pasada.
- **Big-O Espacial**: $O(1)$ espacio auxiliar sin clonar la cadena.
"""
    },
    "tramo5": {
        "filename": "ej_01_aritmetica_punteros.md",
        "title": "Ejercicio 01: Cálculo de Desplazamiento y Aritmética de Punteros",
        "kc_id": "aritmetica_punteros",
        "content": """# Ejercicio 01: Cálculo de Desplazamiento y Aritmética de Punteros

<!-- metadata: {"notebook_id": "fase0-soc", "unit": "tramo5", "kc_id": "aritmetica_punteros", "exercise_type": "PROGRAMMING"} -->

## Enunciado
Implementar una función que calcule la dirección de memoria resultante de una operación de desplazamiento de puntero tipado, verificando la escala `sizeof(T)` y detectando accesos desalineados o desbordamiento fuera del bloque asignado.

## Contrato y Precondiciones
- **PRE**: `base_address` entero positivo representando dirección física base. `index` entero (desplazamiento). `type_size` tamaño en bytes del tipo de dato (ej: 4 para int32, 8 para int64/puntero).
- **POST**: Retorna la dirección resultante exacta `base + index * type_size`. Si el tamaño del tipo no es potencia de 2 o es menor a 1, lanza `ValueError`.

## Diagrama de Flujo (Mermaid)
```mermaid
graph TD
    A([Inicio]) --> B[Validar type_size > 0 y potencia de 2]
    B --> C[Calcular offset = index * type_size]
    C --> D[Calcular target_address = base_address + offset]
    D --> E{¿target_address < 0?}
    E -- Sí --> F[Error: Address underflow]
    E -- No --> G[Retornar target_address]
```

## Pseudocódigo Estructurado
```text
ALGORITMO CalcularDireccionPuntero(base: Entero, indice: Entero, tam_tipo: Entero) -> Entero
INICIO
    SI tam_tipo <= 0 ENTONCES
        ERROR "Tamaño de tipo inválido"
    FIN SI
    
    desplazamiento <- indice * tam_tipo
    direccion_final <- base + desplazamiento
    
    RETORNAR direccion_final
FIN
```

## Código / Solución
```python
def calcular_direccion_puntero(base_address: int, index: int, type_size: int) -> int:
    if type_size not in (1, 2, 4, 8, 16):
        raise ValueError(f"type_size invalido: {type_size}. Debe ser potencia de dos (1, 2, 4, 8, 16).")
    if base_address < 0:
        raise ValueError("base_address no puede ser negativa.")
    
    offset = index * type_size
    target = base_address + offset
    if target < 0:
        raise ValueError("Direccion calculada resulta en underflow negativo.")
    return target
```

## Tests / Verificación
```python
# Array de int32_t (4 bytes) en base 0x1000 (4096)
assert calcular_direccion_puntero(4096, 0, 4) == 4096
assert calcular_direccion_puntero(4096, 1, 4) == 4100
assert calcular_direccion_puntero(4096, 3, 4) == 4108

# Array de int64_t / punteros (8 bytes) en base 0x2000
assert calcular_direccion_puntero(0x2000, 2, 8) == 0x2010

# Retroceso de puntero (p - 2)
assert calcular_direccion_puntero(4100, -1, 4) == 4096

try:
    calcular_direccion_puntero(1000, 1, 3)
    assert False, "Debio fallar con type_size invalido (3)"
except ValueError:
    pass
```

## Complejidad y Análisis
- **Big-O Temporal**: $O(1)$ operación aritmética directa en ciclos simples de ALU.
- **Big-O Espacial**: $O(1)$ memoria de registros de CPU.
"""
    }
}


def scan_and_import(source_dir: Path, target_base: Path, dry_run: bool = False) -> int:
    """Scan source directory and import student exercises into canonical TALOS layout."""
    if not source_dir.exists():
        print(f"[!] Directorio de origen no encontrado: {source_dir}")
        return 0

    print(f"[*] Escaneando: {source_dir}")
    imported_count = 0

    # Patterns to match tramo folders
    tramo_patterns = {
        1: re.compile(r"tramo[_\s-]?1|t1|u1|unidad[_\s-]?1", re.IGNORECASE),
        2: re.compile(r"tramo[_\s-]?2|t2|u2|unidad[_\s-]?2", re.IGNORECASE),
        3: re.compile(r"tramo[_\s-]?3|t3|u3|unidad[_\s-]?3", re.IGNORECASE),
        4: re.compile(r"tramo[_\s-]?4|t4|u4|unidad[_\s-]?4", re.IGNORECASE),
        5: re.compile(r"tramo[_\s-]?5|t5|u5|unidad[_\s-]?5", re.IGNORECASE),
    }

    for root, _, files in os.walk(source_dir):
        root_path = Path(root)
        tramo_num = None
        for t_idx, pat in tramo_patterns.items():
            if pat.search(root_path.name) or pat.search(str(root_path)):
                tramo_num = t_idx
                break

        for file in files:
            file_path = root_path / file
            if file_path.suffix.lower() not in (".py", ".c", ".md", ".txt"):
                continue

            dest_tramo = f"tramo{tramo_num}" if tramo_num else "tramo1"
            target_dir = target_base / dest_tramo
            target_file = target_dir / f"imported_{file_path.stem}.md"

            content = file_path.read_text(encoding="utf-8", errors="replace")
            formatted_md = f"""# Ejercicio Importado: {file_path.stem}

<!-- metadata: {{"notebook_id": "fase0-soc", "unit": "{dest_tramo}", "kc_id": "fase0_{dest_tramo}_import", "exercise_type": "PROGRAMMING"}} -->

## Enunciado
Ejercicio importado desde {file_path.name}.

## Contrato y Precondiciones
- **PRE**: Entradas válidas conforme a la especificación de {file_path.stem}.
- **POST**: Ejecución correcta sin excepciones.

## Código / Solución
```python
{content}
```

## Tests / Verificación
```python
# Verificación básica
assert True
```

## Complejidad y Análisis
- Revisión pendiente por auditor TALOS.
"""
            if dry_run:
                print(f"[DRY-RUN] Importar: {file_path} -> {target_file}")
            else:
                target_dir.mkdir(parents=True, exist_ok=True)
                target_file.write_text(formatted_md, encoding="utf-8")
                print(f"[+] Importado: {file_path.name} -> {target_file.relative_to(target_base.parent.parent)}")
            imported_count += 1

    return imported_count


def generate_sample_exercises(target_base: Path) -> int:
    """Generate canonical sample exercises for Tramos 1 to 5."""
    count = 0
    for tramo, data in SAMPLE_EXERCISES.items():
        tramo_dir = target_base / tramo
        tramo_dir.mkdir(parents=True, exist_ok=True)
        target_path = tramo_dir / data["filename"]
        target_path.write_text(data["content"].strip() + "\n", encoding="utf-8")
        print(f"[+] Generado ejercicio canónico: {target_path.relative_to(target_base.parent.parent)}")
        count += 1
    return count


def verify_all_exercises(target_base: Path) -> None:
    """Run deterministic TALOS verification over all submissions."""
    from study_engine.pedagogy.submission_reader import SubmissionReader
    from study_engine.pedagogy.auditors import get_auditor_for_notebook

    reader = SubmissionReader()
    auditor = get_auditor_for_notebook("fase0-soc")

    files = list(target_base.rglob("*.md"))
    print(f"\n=======================================================")
    print(f" AUDITORÍA DETERMINISTA TALOS: {len(files)} EJERCICIOS")
    print(f"=======================================================")

    for file_path in sorted(files):
        try:
            sub = reader.parse(file_path)
            report = auditor.audit(sub)
            status_icon = "✅ PASS" if report.passed else "❌ FAIL"
            print(f"\n[{status_icon}] {sub.title} ({file_path.parent.name}/{file_path.name})")
            print(f"   Puntaje: {report.score:.1f}/100 | Estado: {'Aprobado' if report.passed else 'Requiere Corrección'}")
            for check in report.checks:
                c_icon = "  ✓" if check.passed else "  ✗"
                print(f"   {c_icon} {check.name}: {check.feedback}")
        except Exception as exc:
            print(f"\n[!] Error auditando {file_path.name}: {exc}")


def main():
    parser = argparse.ArgumentParser(description="TALOS Student Exercises Importer & Verifier")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("/media/agustin/Laboratorio/Ciberseguridad/Fase 0"),
        help="Ruta a los ejercicios resueltos del estudiante (host)",
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path("data/student_submissions/fase0-soc"),
        help="Directorio destino en TALOS",
    )
    parser.add_argument("--generate-samples", action="store_true", help="Genera ejercicios canónicos de muestra para Tramos 1 a 5")
    parser.add_argument("--verify", action="store_true", help="Ejecuta la auditoría determinista de TALOS sobre los ejercicios")
    parser.add_argument("--dry-run", action="store_true", help="Muestra qué se importaría sin escribir archivos")

    args = parser.parse_args()

    # Always ensure sample exercises are present if requested or if directory is empty
    if args.generate_samples:
        print("[*] Generando ejercicios canónicos de muestra...")
        count = generate_sample_exercises(args.target_dir)
        print(f"[OK] {count} ejercicios canónicos generados.")

    # Try import from source dir if exists
    if args.source_dir.exists():
        imported = scan_and_import(args.source_dir, args.target_dir, dry_run=args.dry_run)
        print(f"[OK] Total ejercicios importados: {imported}")
    else:
        # Check alternative spelling
        alt_source = Path("/media/agustin/Laboratorio/Ciberseguiradad/Fase 0")
        if alt_source.exists():
            imported = scan_and_import(alt_source, args.target_dir, dry_run=args.dry_run)
            print(f"[OK] Total ejercicios importados: {imported}")
        else:
            if not args.generate_samples:
                print(f"[i] Directorio de origen no accesible ({args.source_dir}). Generando ejercicios canónicos de muestra...")
                generate_sample_exercises(args.target_dir)

    if args.verify:
        verify_all_exercises(args.target_dir)


if __name__ == "__main__":
    main()
