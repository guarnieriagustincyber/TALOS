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
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Tras N turnos consecutivos sobre el mismo KC, se propone ejercicio.
PROPOSAL_STREAK_THRESHOLD = 3
# Para KCs no evaluados (cold start), se acelera a 2 turnos para resolver la ambigüedad más rápido.
PROPOSAL_COLD_START_THRESHOLD = 2


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


def should_propose(streak_count: int, attempts: int = 1) -> bool:
    """Regla pedagógica: proponer ejercicio al alcanzar el umbral de turnos.

    Acelera la propuesta a 2 turnos cuando el KC está sin evaluar (attempts == 0)
    para resolver la ambigüedad más rápido.
    """
    threshold = PROPOSAL_COLD_START_THRESHOLD if attempts == 0 else PROPOSAL_STREAK_THRESHOLD
    return streak_count >= threshold


def to_proposal_payload(exercise: Any) -> Dict[str, Any]:
    """Serializa el ejercicio para el evento SSE/REST sin exponer la clave."""
    if isinstance(exercise, dict):  # generado (Fase 6)
        return {
            "exercise_id": exercise["exercise_id"],
            "kc_id": exercise.get("kc_ids", [None])[0],
            "title": exercise.get("prompt", "")[:80],
            "prompt": exercise.get("prompt", ""),
            "type": exercise.get("kind"),
            "options": None,
            "source": "generated",
        }
    return {
        "exercise_id": exercise.exercise_id,
        "kc_id": exercise.kc_id,
        "title": (exercise.prompt or "")[:80],
        "prompt": exercise.prompt,
        "type": getattr(exercise.exercise_type, "value", str(exercise.exercise_type)),
        "options": list(exercise.options) if exercise.options else None,
        # expected_answer NUNCA se expone al frontend en la propuesta
    }


def select_or_generate(
    exercise_store: Any,
    registry: Any,
    kc_id: Optional[str],
    catalog: Optional[Dict[str, Any]] = None,
    submissions_root: Optional[Path] = None,
) -> Optional[Any]:
    """Prioridad: catálogo estático QUALIFIABLE primero (fail-closed).

    Si NO hay cobertura certificada, busca en el registro de generados y,
    como último recurso de composición, propone multi-KC cuando el KC matchea
    una familia de composición.
    """
    static = select_exercise_for_kc(exercise_store, kc_id, submissions_root=submissions_root)
    if static is not None:
        return static

    if registry is not None and kc_id:
        try:
            existing = registry.list_for_kc(kc_id)
            if existing:
                return existing[0]
            # Generación on-the-fly como fallback (Tipo 1 si matchea plantilla)
            from study_engine.pedagogy.exercise_compiler import compose_multi_kc_exercise
            generated = compose_multi_kc_exercise([kc_id], catalog=catalog)
            if generated is not None:
                registry.save(generated)
                return generated
        except Exception as exc:
            logger.debug("Fallback generado falló para kc %s: %s", kc_id, exc)
    return None


# ---------------------------------------------------------------------------
# Protocolo de Lucha (Fase 5.3b / audit pedagógico)
# ---------------------------------------------------------------------------

STRUGGLE_THRESHOLD = 3

STRUGGLE_DIRECTIVE = (
    "=== PROTOCOLO DE LUCHA (STRUGGLE MODE) ===\n"
    "El usuario falló este concepto 3 veces. PROHIBIDO repetir la explicación teórica.\n"
    "1) Nombra el patrón de error observado.\n"
    "2) Cambia radicalmente la modalidad (usa una analogía de aduanas o un "
    "diagrama ASCII de memoria).\n"
    "3) Termina pidiendo al usuario que prediga el estado de la memoria o "
    "registros ANTES de dar la solución."
)


class StruggleTracker:
    """Rastrea fallos consecutivos por KC en la sesión de estudio.

    - record(kc_id, correct=False) incrementa; correct=True resetea ese KC.
    - Un intento sobre OTRO KC resetea el foco (el estudiante cambió de tema).
    - is_struggling(kc_id) es True solo si el KC activo acumuló >=3 fallos.
    """

    def __init__(self, threshold: int = STRUGGLE_THRESHOLD) -> None:
        self.threshold = threshold
        self._lock = threading.Lock()
        self._focus_kc: Optional[str] = None
        self._consecutive_failures = 0

    def record(self, kc_id: str, correct: bool) -> int:
        """Registra un intento y devuelve el conteo de fallos consecutivos."""
        if not kc_id:
            return 0
        with self._lock:
            if self._focus_kc != kc_id:
                # Cambio de KC => resetea la racha previa
                self._focus_kc = kc_id
                self._consecutive_failures = 0
            if correct:
                self._consecutive_failures = 0
            else:
                self._consecutive_failures += 1
            return self._consecutive_failures

    def is_struggling(self, kc_id: Optional[str]) -> bool:
        if not kc_id:
            return False
        with self._lock:
            return self._focus_kc == kc_id and self._consecutive_failures >= self.threshold

    def directive(self, kc_id: Optional[str]) -> str:
        """Directiva de prompt (vacía si no hay lucha activa)."""
        return STRUGGLE_DIRECTIVE if self.is_struggling(kc_id) else ""
