"""Server-owned policy helpers for active protected assessments."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable


def is_protected_assessment(item: Any) -> bool:
    """Return whether trusted registry metadata marks an item as an active assessment."""
    metadata = getattr(item, "metadata", None)
    assessment = metadata.get("assessment") if isinstance(metadata, dict) else None
    if not isinstance(assessment, dict) or assessment.get("protected") is not True:
        return False
    status = assessment.get("status")
    return isinstance(status, str) and status.casefold() in {"active", "in_progress"}


def _normalized_content(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).casefold()
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", normalized)


def contains_protected_solution(response: str, solutions: Iterable[str]) -> bool:
    """Detect full answers and substantial verbatim fragments before protected output is emitted."""
    normalized_response = _normalized_content(response)
    if not normalized_response:
        return False

    minimum_fragment_length = 32
    for solution in solutions:
        normalized_solution = _normalized_content(solution)
        if not normalized_solution:
            continue
        if normalized_solution == normalized_response:
            return True
        if len(normalized_solution) < minimum_fragment_length:
            continue
        if normalized_solution in normalized_response:
            return True
        if any(
            normalized_solution[index : index + minimum_fragment_length] in normalized_response
            for index in range(len(normalized_solution) - minimum_fragment_length + 1)
        ):
            return True
    return False


PROTECTED_ASSESSMENT_REFUSAL = (
    "No puedo proporcionar la respuesta ni el solucionario de una evaluación activa. "
    "Puedo ayudarte con una pista conceptual o revisar tu intento."
)

PROTECTED_ASSESSMENT_UNAVAILABLE = (
    "No puedo continuar con una evaluación protegida porque su solución de referencia "
    "no está disponible para verificar la respuesta. Consultá a tu docente."
)
