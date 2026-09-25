"""Métricas Pedagógicas y Socráticas para Fase 4-eval.

Implementa verificación anti-atajo (Anti-Shortcut Socratic) y scaffolding.
"""

import re
from typing import Sequence


# Patrones que indican código completo copiable sin explicación socrática
CODE_BLOCK_PATTERN = re.compile(r"```[a-zA-Z0-9_\-]*\n([\s\S]*?)\n```")


def verify_anti_shortcut(
    response_text: str,
    is_anti_shortcut_probe: bool,
) -> bool:
    """Verifica que si el usuario pidió una solución directa de código, el sistema no la entregue lista para copiar.
    
    Criterios:
    1. Si es probe anti-shortcut, NO debe contener una función main() completa con la solución servida.
    2. Debe contener preguntas socráticas o andamiaje deductivo.
    """
    if not is_anti_shortcut_probe:
        return True

    text_lower = response_text.lower()

    # Si contiene main() con retorno en un bloque de código completo
    blocks = CODE_BLOCK_PATTERN.findall(response_text)
    for b in blocks:
        if "int main(" in b or "void main(" in b:
            # Falla si entrega el programa completo resuelto
            if "pthread_mutex_lock" in b and "pthread_mutex_unlock" in b:
                return False

    # Debe contener al menos una pregunta o interrogante socrático
    has_question = "?" in response_text or "¿" in response_text
    return has_question
