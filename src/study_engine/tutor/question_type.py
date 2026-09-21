from enum import Enum
from typing import Optional


class QuestionType(str, Enum):
    GREETING = "greeting"
    CURRICULAR = "curricular"
    TECHNICAL = "technical"
    META = "meta"


def detect_question_type(message: Optional[str]) -> QuestionType:
    msg = (message or "").strip().lower()

    # Saludos primero (alta prioridad)
    if any(g in msg for g in ["hola", "buenos dias", "buenas", "saludos", "hey"]):
        return QuestionType.GREETING

    # Preguntas meta sobre el sistema
    if any(m in msg for m in ["quién te creó", "cómo funcionas", "qué eres", "quién eres", "qué haces"]):
        return QuestionType.META

    # Preguntas curriculares (roadmap, prerequisitos, siguiente nodo)
    if any(c in msg for c in [
        "qué tema sigue",
        "prerrequisito",
        "próximo nodo",
        "qué falta",
        "orden de estudio",
        "roadmap",
        "siguiente paso",
        "qué módulo sigue",
    ]):
        return QuestionType.CURRICULAR

    # Preguntas técnicas (contenido del nodo)
    if any(t in msg for t in [
        "qué es",
        "explica",
        "definición",
        "cómo funciona",
        "cómo se",
        "ejemplo",
        "código",
        "diferencia entre",
        "para qué sirve",
    ]):
        return QuestionType.TECHNICAL

    # Default fallback to technical (most common)
    return QuestionType.TECHNICAL
