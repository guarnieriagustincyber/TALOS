"""Exercise Service (Fase 5.3): propuesta pedagógica de ejercicios en chat.

Selección fail-closed sobre el ExerciseStore certificado:
- SOLO candidatos QUALIFIABLE (is_presentable()).
- Prioriza ejercicios sin submission previa del estudiante ("no vistos").
- Sin ejercicios para el KC -> None (nunca inventa ni fuerza un ejercicio).

No usa LLM para calificar ni para seleccionar: selección determinista.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Tras N turnos consecutivos sobre el mismo KC, se propone ejercicio.
PROPOSAL_STREAK_THRESHOLD = 3


def _seen_exercise_ids(submissions_root: Path) -> set:
    """Exercise IDs con submission existente en disco (el estudiante ya lo vio)."""
    seen: set = set()
    if not submissions_root.exists():
        return seen
    for p in submissions_root.rglob("*.md"):
        if "templates" in p.parts or ".reports" in p.parts:
            continue
        seen.add(p.stem)
    return seen


def select_exercise_for_kc(
    exercise_store: Any,
    kc_id: Optional[str],
    submissions_root: Optional[Path] = None,
) -> Optional[Any]:
    """Devuelve el mejor candidato QUALIFIABLE para el KC, o None."""
    if not kc_id or exercise_store is None:
        return None
    try:
        candidates = [ex for ex in exercise_store.get_exercises_for_kc(kc_id) if ex.is_presentable()]
    except Exception as exc:
        logger.warning("ExerciseStore lookup falló para kc %s: %s", kc_id, exc)
        return None
    if not candidates:
        return None

    seen = _seen_exercise_ids(submissions_root or Path("data/student_submissions"))
    unseen = [c for c in candidates if c.exercise_id not in seen]
    return unseen[0] if unseen else candidates[0]


def should_propose(streak_count: int) -> bool:
    """Regla pedagógica: proponer ejercicio al alcanzar el umbral de turnos."""
    return streak_count >= PROPOSAL_STREAK_THRESHOLD


def to_proposal_payload(exercise: Any) -> Dict[str, Any]:
    """Serializa el ejercicio para el evento SSE/REST sin exponer la clave."""
    return {
        "exercise_id": exercise.exercise_id,
        "kc_id": exercise.kc_id,
        "title": (exercise.prompt or "")[:80],
        "prompt": exercise.prompt,
        "type": getattr(exercise.exercise_type, "value", str(exercise.exercise_type)),
        "options": list(exercise.options) if exercise.options else None,
        # expected_answer NUNCA se expone al frontend en la propuesta
    }
