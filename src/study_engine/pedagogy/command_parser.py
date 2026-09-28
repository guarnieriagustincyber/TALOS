"""Deterministic Student Command Parser for TALOS Socratic System Prompt.

Detects fixed student commands via regex/keywords and maps them to canonical
output formats (e.g. MAPA DE UNIDAD, EXPLICACIÓN DEL TEMA, EJERCICIO GUIADO,
SOLUCIÓN COMPLETA, TRADUCCIÓN, EXPLICACIÓN DESDE CERO, CAMBIO DE ENFOQUE).
Zero LLM invocation. Deterministic first.
"""

from dataclasses import dataclass
from enum import Enum
import re
from typing import Optional


class CommandType(str, Enum):
    RESUMEN_UNIDAD = "RESUMEN_UNIDAD"
    EMPECEMOS_TEMA = "EMPECEMOS_TEMA"
    DAME_UN_EJERCICIO = "DAME_UN_EJERCICIO"
    DAME_SOLUCION_COMPLETA = "DAME_SOLUCION_COMPLETA"
    VERIFICACION = "VERIFICACION"
    TRADUCCION = "TRADUCCION"
    EXPLICACION_DESDE_CERO = "EXPLICACION_DESDE_CERO"
    NO_ENTENDI = "NO_ENTENDI"
    DIAGNOSTICO = "DIAGNOSTICO"


@dataclass(frozen=True)
class ParsedCommand:
    command_type: CommandType
    target_arg: Optional[str]
    expected_format: str
    max_words: int
    is_structured: bool
    template_instruction: str


# =========================================================================
# GUÍAS DE SALIDA ADAPTABLES POR TAREA
# =========================================================================

TEMPLATE_MAPA_UNIDAD = """Usá un mapa de unidad conciso y ajustá sus apartados al pedido:

**MAPA DE UNIDAD**
- Título de la unidad [E#]
- Idea principal
- Conceptos fundamentales
- Qué conviene recordar o practicar
- Analogías o conexiones solo si son pertinentes y tienen fundamento"""

TEMPLATE_EXPLICACION_TEMA = """Explicá el tema de forma directa y seleccioná solo los elementos que ayuden:

**EXPLICACIÓN DEL TEMA**
1. ¿Qué es este tema? [E#]
2. ¿Por qué importa?
3. Explicación simple sin asumir conocimiento
4. Mecanismo o ejemplo mínimo si aclara la idea
5. Errores comunes o comprobación solo cuando sean útiles

No agregues pseudocódigo ni implementación automáticamente."""

TEMPLATE_EJERCICIO_GUIADO = """Proponé una consigna clara y evaluable, adecuada al tema:

**EJERCICIO GUIADO**
1. Enunciado, objetivo y restricciones pertinentes
2. Un primer paso abordable para que el estudiante continúe

Agregá contratos, diagramas, tests o código solo si se solicitan o son esenciales para la consigna.

No reveles la solución completa antes de que el estudiante la solicite explícitamente."""

TEMPLATE_SOLUCION_COMPLETA = """Entregá la solución completa en el formato y lenguaje pedidos:

**SOLUCIÓN COMPLETA**
1. Resolución y razonamiento suficientes para verificarla
2. Código o pseudocódigo solo si corresponde al pedido y no fue excluido
3. Comprobaciones y casos límite pertinentes, sin imponer otros lenguajes"""

TEMPLATE_VERIFICACION = """Tu salida debe seguir estrictamente este formato:

**VERIFICACIÓN**
- ¿Qué está bien?
- ¿Qué está incompleto o mal?
- ¿Qué concepto faltó?
- ¿Cómo lo pensamos paso a paso?
- ¿Cuál sería el siguiente paso mínimo?
- Si hay error, NO des la solución completa: dá una pista concreta."""

TEMPLATE_TRADUCCION = """Traducí el artefacto disponible al lenguaje destino solicitado:

**TRADUCCIÓN**
1. Código en el lenguaje destino y explicación de las decisiones necesarias
2. Pruebas o casos límite solo si se piden o son pertinentes"""

TEMPLATE_EXPLICACION_DESDE_CERO = """Explicá desde los fundamentos, con extensión y representación proporcionales:

**EXPLICACIÓN DESDE CERO**
- Definición simple
- Términos nuevos explicados
- Ejemplo, analogía o pregunta solo si aportan a la comprensión"""

TEMPLATE_NO_ENTENDI = """Tu salida debe aplicar un CAMBIO DE ENFOQUE pedagógico:
- NO repitas exactamente lo mismo.
- Elegí otra representación, analogía o escala si ayuda a destrabar la confusión.
- Dividí el problema en partes más chicas.
- Usá un ejemplo más simple solo si es pertinente y compatible con el formato pedido.
- Hacé una pregunta precisa para detectar dónde se trabó el estudiante."""

TEMPLATE_DIAGNOSTICO = """Tu salida debe emitir un INFORME DE DIAGNÓSTICO COGNITIVO estructurado:
**DIAGNÓSTICO COGNITIVO DEL ESTUDIANTE**
1. Estado Actual de Conocimiento (KCs evaluados y nivel de dominio)
2. Brechas y Misconceptions Recurrentes (errores persistentes detectados en memoria)
3. Fortalezas Demostradas (conceptos asimilados sólidamente)
4. Plan de Acción y Próximo Ejercicio Recomendado"""


# =========================================================================
# UNIVERSAL SAFE COMMANDS (Para SocraticGuard en todos los cuadernos)
# =========================================================================

UNIVERSAL_SAFE_COMMANDS = [
    ":solve",
    "RESUMEN UNIDAD",
    "RESUMEN CAPÍTULO",
    "RESUMEN CAPITULO",
    "EMPECEMOS CON EL TEMA",
    "LEÍ EL CAPÍTULO",
    "LEI EL CAPITULO",
    "DAME UN EJERCICIO",
    "TRADUCÍ ESTO A C",
    "TRADUCI ESTO A C",
    "TRADUCÍ ESTO A PYTHON",
    "TRADUCI ESTO A PYTHON",
    "TRADUCÍ ESTO",
    "TRADUCI ESTO",
    "EXPLICÁ COMO SI NO SUPIERA NADA",
    "EXPLICA COMO SI NO SUPIERA NADA",
    "NO ENTENDÍ",
    "NO ENTENDI",
    "OTRA FORMA",
    "REFORMULÁ",
    "REFORMULA",
    "DAME LA SOLUCIÓN COMPLETA",
    "DAME LA SOLUCION COMPLETA",
    "SOLUCIÓN COMPLETA",
    "SOLUCION COMPLETA",
]


# =========================================================================
# REGEX MATCHER
# =========================================================================

_RE_RESUMEN_UNIDAD = re.compile(
    r"^\s*RESUMEN\s+(?:DE\s+LA\s+|DEL\s+)?(?:UNIDAD|CAP[IÍ]TULO)\s+([A-Za-z0-9_.-]+)",
    re.IGNORECASE,
)
_RE_EMPECEMOS_TEMA = re.compile(
    r"^\s*(?:EMPECEMOS\s+CON\s+EL\s+TEMA|LE[IÍ]\s+(?:EL\s+)?CAP[IÍ]TULO,?\s*EMPECEMOS\s+CON\s+EL\s+PUNTO)\s+([A-Za-z0-9_.-]+)",
    re.IGNORECASE,
)
_RE_DAME_EJERCICIO = re.compile(
    r"^\s*(?:(?:/|:)?(?:PRACTICAR|PRACTICE|EJERCICIO)|(?:DAME|QUIERO|PROPON[EÉ])\s+(?:UN\s+)?EJERCICIO)(?:\s+(?:DE|SOBRE)?\s*([A-Za-z0-9_.\-\s]+))?",
    re.IGNORECASE,
)
_RE_SOLUCION_COMPLETA = re.compile(
    r"^\s*(?:DAME\s+LA\s+SOLUCI[OÓ]N\s+COMPLETA|SOLUCI[OÓ]N\s+COMPLETA)",
    re.IGNORECASE,
)
_RE_TRADUCIR = re.compile(
    r"^\s*TRADUC[IÍ]\s+(?:ESTO\s+)?A\s+([A-Za-z0-9_+#]+)",
    re.IGNORECASE,
)
_RE_DESDE_CERO = re.compile(
    r"^\s*EXPLIC[AÁ]\s+(?:ESTO\s+)?COMO\s+SI\s+NO\s+SUPIERA\s+NADA",
    re.IGNORECASE,
)
_RE_NO_ENTENDI = re.compile(
    r"^\s*(?:NO\s+ENTEND[IÍ](?!\s+POR\s*QU[EÉ]|\s+C[OÓ]MO)|NO\s+ENTIENDO(?!\s+POR\s*QU[EÉ]|\s+C[OÓ]MO)|OTRA\s+FORMA|REFORMUL[AÁ]|ME\s+PERD[IÍ])",
    re.IGNORECASE,
)
_RE_DIAGNOSTICO = re.compile(
    r"^\s*(?:>>\s*(?:dia|diagnostico)|(?:MI\s+)?DIAGN[OÓ]STICO(?:\s+COGNITIVO)?)\b",
    re.IGNORECASE,
)


def parse_student_command(message: str) -> Optional[ParsedCommand]:
    """Determines if the message matches any of the canonical student commands.
    
    Returns ParsedCommand with template, expected_format, and token/word bounds,
    or None if it's a standard conversational query.
    """
    if not message:
        return None
    raw = message.strip()

    # Si el mensaje viene dentro de un prompt bundle estructurado, aislar la consulta real
    if "=== CONSULTA DEL ESTUDIANTE ===" in raw:
        part = raw.split("=== CONSULTA DEL ESTUDIANTE ===")[1]
        if "=== INSTRUCCIÓN" in part:
            raw = part.split("=== INSTRUCCIÓN")[0].strip()
        else:
            raw = part.strip()

    # 1. Solución completa (Prioridad alta para no confundir con ejercicio)
    if _RE_SOLUCION_COMPLETA.search(raw):
        return ParsedCommand(
            command_type=CommandType.DAME_SOLUCION_COMPLETA,
            target_arg=None,
            expected_format="SOLUCIÓN COMPLETA",
            max_words=500,
            is_structured=True,
            template_instruction=TEMPLATE_SOLUCION_COMPLETA,
        )

    # 2. Resumen de Unidad / Capítulo
    m_resumen = _RE_RESUMEN_UNIDAD.search(raw)
    if m_resumen:
        arg = m_resumen.group(1).strip()
        return ParsedCommand(
            command_type=CommandType.RESUMEN_UNIDAD,
            target_arg=arg,
            expected_format="MAPA DE UNIDAD",
            max_words=500,
            is_structured=True,
            template_instruction=TEMPLATE_MAPA_UNIDAD,
        )

    # 3. Empecemos con el tema
    m_tema = _RE_EMPECEMOS_TEMA.search(raw)
    if m_tema:
        arg = m_tema.group(1).strip()
        return ParsedCommand(
            command_type=CommandType.EMPECEMOS_TEMA,
            target_arg=arg,
            expected_format="EXPLICACIÓN DEL TEMA",
            max_words=500,
            is_structured=True,
            template_instruction=TEMPLATE_EXPLICACION_TEMA,
        )

    # 4. Dame un ejercicio / Practicar
    m_ej = _RE_DAME_EJERCICIO.search(raw)
    if m_ej:
        raw_topic = m_ej.group(1).strip() if m_ej.group(1) else None
        return ParsedCommand(
            command_type=CommandType.DAME_UN_EJERCICIO,
            target_arg=raw_topic if raw_topic else None,
            expected_format="EJERCICIO GUIADO",
            max_words=500,
            is_structured=True,
            template_instruction=TEMPLATE_EJERCICIO_GUIADO,
        )

    # 5. Traducí a lenguaje
    m_trad = _RE_TRADUCIR.search(raw)
    if m_trad:
        lang = m_trad.group(1).strip().upper()
        return ParsedCommand(
            command_type=CommandType.TRADUCCION,
            target_arg=lang,
            expected_format="TRADUCCIÓN",
            max_words=500,
            is_structured=True,
            template_instruction=TEMPLATE_TRADUCCION,
        )

    # 6. Explicá como si no supiera nada
    if _RE_DESDE_CERO.search(raw):
        return ParsedCommand(
            command_type=CommandType.EXPLICACION_DESDE_CERO,
            target_arg=None,
            expected_format="EXPLICACIÓN DESDE CERO",
            max_words=500,
            is_structured=True,
            template_instruction=TEMPLATE_EXPLICACION_DESDE_CERO,
        )

    # 7. No entendí / Otra forma
    if _RE_NO_ENTENDI.search(raw):
        return ParsedCommand(
            command_type=CommandType.NO_ENTENDI,
            target_arg=None,
            expected_format="CAMBIO DE ENFOQUE",
            max_words=400,
            is_structured=True,
            template_instruction=TEMPLATE_NO_ENTENDI,
        )

    # 8. Diagnóstico cognitivo (>>dia / >>diagnostico)
    if _RE_DIAGNOSTICO.search(raw):
        return ParsedCommand(
            command_type=CommandType.DIAGNOSTICO,
            target_arg=None,
            expected_format="DIAGNÓSTICO COGNITIVO",
            max_words=600,
            is_structured=True,
            template_instruction=TEMPLATE_DIAGNOSTICO,
        )

    return None
