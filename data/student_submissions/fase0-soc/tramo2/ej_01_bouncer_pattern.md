# Ejercicio 01: Refactorización Bouncer Pattern (Cláusulas de Guarda)

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
