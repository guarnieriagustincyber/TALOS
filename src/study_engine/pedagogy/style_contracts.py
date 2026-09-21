"""Style Contracts for Conversational Style Router (Ola 6, Fase 6.2).

Defines the 6 conversational styles, structural format rules, and prompt directives:
1. CASUAL_CHAT: Fluent rioplatense prose, NO markdown headers (###), 2-3 paragraphs.
2. ANALOGY_REQUEST: Extended analogy + markdown mapping table.
3. FORMAL_EXPLANATION: Tri-layer structure (Intuición, Mecanismo Formal, Nivel de Máquina).
4. VERIFICATION: Direct verdict (SÍ/NO/DEPENDE) + factual justification + citations.
5. PRACTICE: Socratic exercise dispatch loop.
6. CROSS_SOURCE: Dialectic multi-source synthesis + confrontation section.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ConversationStyle(str, Enum):
    CASUAL_CHAT = "CASUAL_CHAT"
    ANALOGY_REQUEST = "ANALOGY_REQUEST"
    FORMAL_EXPLANATION = "FORMAL_EXPLANATION"
    VERIFICATION = "VERIFICATION"
    PRACTICE = "PRACTICE"
    CROSS_SOURCE = "CROSS_SOURCE"

    # Compatibility aliases
    NORMAL = "normal"
    DEEP = "deep"
    CASUAL = "casual"


@dataclass(frozen=True)
class StyleContract:
    """Formal structural and rhetorical contract for a conversational style."""
    style: ConversationStyle
    name: str
    description: str
    allow_headers: bool
    tri_layer_required: bool
    directive: str
    min_paragraphs: int = 1
    max_paragraphs: int = 4
    required_sections: Tuple[str, ...] = ()


STYLE_DIRECTIVES: Dict[ConversationStyle, str] = {
    ConversationStyle.CASUAL_CHAT: (
        "MODO CONVERSACIONAL NATURAL:\n"
        "- Respondé con prosa fluida y tono rioplatense natural ('mirá', 'fijate', 'che').\n"
        "- ESTRICTAMENTE PROHIBIDO usar headers Markdown ('### 1. Intuición', '### 2.', etc.).\n"
        "- Estructura en 2 a 3 párrafos claros y directos.\n"
        "- Cerrá con una pregunta breve de reflexión o guía hacia el siguiente paso.\n"
        "- La explicación debe ser contundente y explayada; nunca recortes para ahorrar tokens."
    ),
    ConversationStyle.ANALOGY_REQUEST: (
        "MODO ANALOGÍA CONCEPTUAL:\n"
        "- Presentá una analogía extendida, vívida y concreta de la vida cotidiana.\n"
        "- Incluí una tabla Markdown de correspondencia entre los elementos de la analogía y el concepto técnico formal.\n"
        "- Remití a las evidencias del libro para validar dónde termina la analogía y empieza el mecanismo real.\n"
        "- Sin rodeos ni felicitaciones por la pregunta."
    ),
    ConversationStyle.FORMAL_EXPLANATION: (
        "MODO EXPLICACIÓN TÉCNICA FORMAL (TRI-CAPA):\n"
        "- Desglosá la respuesta con rigor técnico en tres dimensiones complementarias usando headers Markdown obligatorios:\n"
        "  ### 1. Intuición Conceptual\n"
        "  ### 2. Mecanismo Formal\n"
        "  ### 3. Nivel de Máquina\n"
        "- Citas rigurosas [E#] respaldando cada afirmación sustantiva.\n"
        "- Cierre con un desafío socrático de profundización."
    ),
    ConversationStyle.VERIFICATION: (
        "MODO VERIFICACIÓN PRECISA:\n"
        "- Comenzá directamente con un veredicto inequívoco: 'SÍ', 'NO', o 'DEPENDE DEL CONTEXTO'.\n"
        "- Explicá en 1 o 2 párrafos la justificación formal con cita precisa a la fuente [E#].\n"
        "- Señalá condiciones de borde o casos donde la afirmación no se cumple."
    ),
    ConversationStyle.CROSS_SOURCE: (
        "MODO SÍNTESIS DIALÉCTICA MULTI-FUENTE:\n"
        "- Compará y contrastá las perspectivas documentadas en las distintas fuentes del cuaderno.\n"
        "- Dedicá una sección obligatoria '### Confrontación de perspectivas' destacando acuerdos y discrepancias operativas.\n"
        "- Presentá las diferencias sin tomar partido arbitrario; citá cada autor con su postura técnica [E#]."
    ),
    ConversationStyle.PRACTICE: (
        "MODO PRÁCTICA SOCRÁTICA:\n"
        "- Despacho determinista de ejercicio certificado QUALIFIABLE.\n"
        "- No reveles la solución. Guiá socráticamente al estudiante con preguntas de andamiaje."
    ),
}

# Add directives for aliases
STYLE_DIRECTIVES[ConversationStyle.NORMAL] = STYLE_DIRECTIVES[ConversationStyle.FORMAL_EXPLANATION]
STYLE_DIRECTIVES[ConversationStyle.DEEP] = STYLE_DIRECTIVES[ConversationStyle.FORMAL_EXPLANATION]
STYLE_DIRECTIVES[ConversationStyle.CASUAL] = STYLE_DIRECTIVES[ConversationStyle.CASUAL_CHAT]


STYLE_CONTRACTS: Dict[ConversationStyle, StyleContract] = {
    ConversationStyle.CASUAL_CHAT: StyleContract(
        style=ConversationStyle.CASUAL_CHAT,
        name="Casual Chat",
        description="Natural fluent prose without headers for casual questions or short interactions",
        allow_headers=False,
        tri_layer_required=False,
        directive=STYLE_DIRECTIVES[ConversationStyle.CASUAL_CHAT],
        min_paragraphs=2,
        max_paragraphs=3,
        required_sections=(),
    ),
    ConversationStyle.ANALOGY_REQUEST: StyleContract(
        style=ConversationStyle.ANALOGY_REQUEST,
        name="Analogy Request",
        description="Extended analogy with Markdown mapping table",
        allow_headers=True,
        tri_layer_required=False,
        directive=STYLE_DIRECTIVES[ConversationStyle.ANALOGY_REQUEST],
        min_paragraphs=2,
        max_paragraphs=4,
        required_sections=("Tabla de correspondencia",),
    ),
    ConversationStyle.FORMAL_EXPLANATION: StyleContract(
        style=ConversationStyle.FORMAL_EXPLANATION,
        name="Formal Explanation",
        description="Tri-layer deep explanation (Intuición, Mecanismo Formal, Nivel de Máquina)",
        allow_headers=True,
        tri_layer_required=True,
        directive=STYLE_DIRECTIVES[ConversationStyle.FORMAL_EXPLANATION],
        min_paragraphs=3,
        max_paragraphs=5,
        required_sections=(
            "### 1. Intuición Conceptual",
            "### 2. Mecanismo Formal",
            "### 3. Nivel de Máquina",
        ),
    ),
    ConversationStyle.VERIFICATION: StyleContract(
        style=ConversationStyle.VERIFICATION,
        name="Verification",
        description="Direct verdict followed by citation-backed justification and edge cases",
        allow_headers=True,
        tri_layer_required=False,
        directive=STYLE_DIRECTIVES[ConversationStyle.VERIFICATION],
        min_paragraphs=1,
        max_paragraphs=2,
        required_sections=(),
    ),
    ConversationStyle.PRACTICE: StyleContract(
        style=ConversationStyle.PRACTICE,
        name="Practice",
        description="Socratic exercise dispatch without leaking solutions",
        allow_headers=True,
        tri_layer_required=False,
        directive=STYLE_DIRECTIVES[ConversationStyle.PRACTICE],
        min_paragraphs=1,
        max_paragraphs=3,
        required_sections=(),
    ),
    ConversationStyle.CROSS_SOURCE: StyleContract(
        style=ConversationStyle.CROSS_SOURCE,
        name="Cross-Source Synthesis",
        description="Dialectic comparison across multiple sources with confrontation section",
        allow_headers=True,
        tri_layer_required=False,
        directive=STYLE_DIRECTIVES[ConversationStyle.CROSS_SOURCE],
        min_paragraphs=2,
        max_paragraphs=4,
        required_sections=("### Confrontación de perspectivas",),
    ),
}

STYLE_CONTRACTS[ConversationStyle.NORMAL] = STYLE_CONTRACTS[ConversationStyle.FORMAL_EXPLANATION]
STYLE_CONTRACTS[ConversationStyle.DEEP] = STYLE_CONTRACTS[ConversationStyle.FORMAL_EXPLANATION]
STYLE_CONTRACTS[ConversationStyle.CASUAL] = STYLE_CONTRACTS[ConversationStyle.CASUAL_CHAT]
