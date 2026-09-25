"""Pedagogical tone, empathy scaffolding, and prompt directives for TALOS (Roadmap v1.1 Fase 4).

Governs conversational warmth, emotional scaffolding, visceral analogies ("Feynman de Barrio"),
and epistemic citation rigor without artificial flattery.
"""

from enum import Enum
import re
from typing import Any, Dict, List, Optional


class PedagogicalToneDirective(str, Enum):
    """Core pedagogical tone and scaffolding directives."""

    WARMTH_AND_RECOGNITION = (
        "=== TONO PEDAGÓGICO: RECONOCIMIENTO Y CALIDEZ ===\n"
        "- Si el estudiante razona correctamente, formula una buena hipótesis o avanza en la deducción, "
        "reconocé explícitamente su acierto con sobriedad ('Excelente razonamiento', 'Muy bien planteado', 'Vas muy bien por ahí').\n"
        "- Prohibida la adulación vacía o automática ('¡Qué inteligente!', '¡Qué gran pregunta!'); el elogio debe ser específico a la lógica del estudiante."
    )

    FRUSTRATION_AND_EMPATHY = (
        "=== TONO PEDAGÓGICO: EMPATÍA ANTE DIFICULTAD O FRUSTRACIÓN ===\n"
        "- El estudiante manifiesta bloqueo, desconcierto o frustración con el tema.\n"
        "- Validá primero la dificultad real del concepto con empatía y cercanía ('Es completamente normal que esto confunda al principio; "
        "la diferencia entre X e Y suele prestarse a confusión', 'No te preocupes, vamos a desarmarlo paso a paso').\n"
        "- Bajá el nivel de abstracción inmediatamente: utilizá una analogía concreta y física antes de volver a la teoría formal."
    )

    TANGIBLE_ANALOGIES = (
        "=== DIRECTIVA DE ANALOGÍAS VISCERALES (FEYNMAN DE BARRIO) ===\n"
        "- Conectá los conceptos técnicos abstractos con metáforas cotidianas del mundo físico y tangible "
        "(ej. aduanas, peajes, ventanillas de banco, canillas de paso, odómetros para overflow, estanterías numeradas).\n"
        "- Vinculá siempre la analogía con su correlato estricto en silicio/POSIX (memoria, registros, syscalls).\n"
        "- Evitá analogías burocráticas o académicas abstractas cuando exista una alternativa cotidiana clara."
    )

    EPISTEMIC_RIGOR_RULE = (
        "=== RIGOR EPISTÉMICO MANDATORIO Y GESTIÓN DE EVIDENCIAS (CITAS [E#]) ===\n"
        "- Toda afirmación fáctica basada en las evidencias documentadas del cuaderno DEBE citar su [E#] correspondiente en la misma oración.\n"
        "- Si el material documental del cuaderno no contiene evidencias específicas para la consulta o respondés con base conceptual general de computación, NO inventes etiquetas [E#] ni agregues referencias apócrifas.\n"
        "- La calidez y la empatía dialéctica NUNCA reemplazan la evidencia documental autorizada.\n"
        "- Si el material documental del cuaderno no cubre un detalle requerido por el programa, declará abstención honesta sobre ese punto específico."
    )


# Patrones explícitos de frustración (incluye expresiones rioplatenses)
_FRUSTRATION_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bno\s+(?:entiendo|cacho|pesco|comprendo|caso)\b", re.IGNORECASE),
    re.compile(r"\b(?:me\s+confunde|me\s+pierde|me\s+tiene\s+podrido|me\s+embol[ao])\b", re.IGNORECASE),
    re.compile(r"\b(?:es\s+un\s+(?:quilombo|l[ií]o|desastre|bard[oo]|chino))\b", re.IGNORECASE),
    re.compile(r"\bestoy\s+(?:perdido|hasta\s+las\s+manos|bloqueado|re\s+perdido|en\s+bolas)\b", re.IGNORECASE),
    re.compile(r"\bno\s+(?:me\s+sale|le\s+encuentro\s+la\s+vuelta)\b", re.IGNORECASE),
    re.compile(r"\bme\s+explot[oóa]\s+la\s+cabeza\b", re.IGNORECASE),
    re.compile(r"\bno\s+me\s+entra\s+en\s+la\s+cabeza\b", re.IGNORECASE),
    re.compile(r"\bme\s+hice\s+(?:un\s+)?(?:l[ií]o|quilombo|ensalada)\b", re.IGNORECASE),
]

# Indicadores para fallback de densidad negativa
_NEGATIVE_DIFFICULTY_WORDS = {
    "no", "nunca", "jamas", "jamás", "nada", "dificil", "difícil",
    "complicado", "imposible", "lio", "lío", "quilombo", "desastre",
    "confundido", "confuso", "perdido", "bloqueado", "podrido",
}

# Patrones de deducción activa o razonamiento estructurado (evita falsos positivos en preguntas directas)
_REASONING_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bsi\s+.+\sentonces\b", re.IGNORECASE),
    re.compile(r"\bpor\s+lo\s+tanto\b", re.IGNORECASE),
    re.compile(r"\beso\s+significa\s+que\b", re.IGNORECASE),
    re.compile(r"\bo\s+sea\s+que\b", re.IGNORECASE),
    re.compile(r"\bentonces\s+.+[\?¿]", re.IGNORECASE),
    re.compile(r"\bentonces\s+(?:el|la|los|las|un|una)\s+.+\s+(?:ser[ií]a|es|apunta|guarda|hace)\b", re.IGNORECASE),
]


def detect_student_frustration(query: str) -> bool:
    """Detecta señales de frustración, desconcierto o bloqueo en la consulta del estudiante.

    Combina patrones idiomáticos explícitos (incluyendo expresiones rioplatenses)
    con un fallback por densidad de términos negativos/dificultad (>= 2 palabras).
    """
    clean_q = (query or "").strip()
    if not clean_q:
        return False

    for pat in _FRUSTRATION_PATTERNS:
        if pat.search(clean_q):
            return True

    words = re.findall(r"\w+", clean_q.lower())
    negative_hits = sum(1 for w in words if w in _NEGATIVE_DIFFICULTY_WORDS)
    return negative_hits >= 2


def detect_student_reasoning_attempt(query: str) -> bool:
    """Detecta si el estudiante está formulando una hipótesis o deducción activa.

    Requiere estructura condicional o ilativa (if-then, por lo tanto, eso significa que),
    descartando preguntas interrogativas directas sin hipótesis previa.
    """
    clean_q = (query or "").strip()
    if not clean_q:
        return False

    for pat in _REASONING_PATTERNS:
        if pat.search(clean_q):
            return True

    return False


def build_pedagogical_tone_directive(
    query: str,
    student_context: Optional[Dict[str, Any]] = None,
    metacognitive_profile: Optional[Dict[str, Any]] = None,
) -> str:
    """Ensambla la directiva de tono conversacional y andamiaje emocional.

    Considera:
    1. Detección emocional de la query (frustración vs. razonamiento activo).
    2. Perfil metacognitivo (nivel de dependencia a soluciones):
       - 'alta': guía firme y empática sin revelar la solución directa.
       - 'baja': tono directo y desafiante evitando sobre-andamiaje.
       - 'moderada': equilibrio estándar.
    3. Mandato epistemológico irrenunciable de citas [E#].
    """
    parts: List[str] = []

    is_frustrated = detect_student_frustration(query)
    is_reasoning = detect_student_reasoning_attempt(query)

    if is_frustrated:
        parts.append(PedagogicalToneDirective.FRUSTRATION_AND_EMPATHY.value)
        parts.append(PedagogicalToneDirective.TANGIBLE_ANALOGIES.value)
    elif is_reasoning:
        parts.append(PedagogicalToneDirective.WARMTH_AND_RECOGNITION.value)

    if metacognitive_profile:
        classification = str(metacognitive_profile.get("classification") or "moderada").lower()
        if classification == "alta":
            parts.append(
                "=== ANDAMIAJE METACOGNITIVO: ALTA DEPENDENCIA ===\n"
                "- El estudiante tiende a solicitar soluciones sin agotar sus intentos propios.\n"
                "- Sé empático pero firme: no reveles la solución directa ni código completo; "
                "guiá con preguntas intermedias y pistas estructuradas."
            )
        elif classification == "baja":
            parts.append(
                "=== ANDAMIAJE METACOGNITIVO: ESTUDIANTE AUTÓNOMO ===\n"
                "- El estudiante demuestra alta autonomía y persistencia propia.\n"
                "- Sé directo y desafiante: evitá sobre-explicar o sobre-andamiar conceptos obvios; "
                "proponé casos de borde y desafíos técnicos profundos."
            )

    parts.append(PedagogicalToneDirective.EPISTEMIC_RIGOR_RULE.value)

    return "\n\n".join(parts)


def validate_three_part_structure(response: str) -> bool:
    """Helper de verificación/auditoría forense para la estructura canónica de 3 partes.

    Verifica heurísticamente:
    1. Presencia de al menos 2 bloques visuales (párrafos no vacíos).
    2. Presencia de citas documentadas [E#].
    3. Cierre con pregunta socrática o reflexiva (termina con '?').
    """
    clean_resp = (response or "").strip()
    if not clean_resp:
        return False

    # 1. Terminación en pregunta reflexiva
    if not clean_resp.endswith("?"):
        return False

    # 2. Citas documentales [E#]
    if not re.search(r"\[E\d+\]", clean_resp):
        return False

    # 3. Al menos 2 párrafos o bloques visuales
    paragraphs = [p.strip() for p in clean_resp.split("\n\n") if p.strip()]
    if len(paragraphs) < 2:
        return False

    return True
