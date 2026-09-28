"""Preference Tracker for Student Pedagogical Context (Fase 6).

Tracks explicit and implicit student learning preferences, formatting affinities,
and pedagogical styles, persisting insights in the sovereign `student_pedagogical_memory` table.

Invariants:
- Thread-safe persistence via StudentStorage.
- Normalized scoring and confidence tracking.
- Deduplication and recency weighting (touch_pedagogical_memory).
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from study_engine.student.storage import StudentStorage

logger = logging.getLogger(__name__)

# Heuristic patterns for explicit format/style preferences
_STYLE_PATTERNS = {
    "mermaid_diagrams": [
        re.compile(r"\b(diagrama(?:s)?(?:\s+de\s+flujo)?(?:\s+en\s+mermaid)?|mermaid)\b", re.IGNORECASE),
        "Prefiere diagramas interactivos de flujo en Mermaid para modelar decisiones lógicas y estados.",
    ],
    "memory_ascii_boxes": [
        re.compile(r"\b(mapa\s+de\s+memoria|esquema\s+de\s+memoria|cajas\s+unicode|dibujo\s+de\s+caja)\b", re.IGNORECASE),
        "Prefiere esquemas visuales de memoria y stack frames dibujados con cajas Unicode estructuradas.",
    ],
    "real_code_examples": [
        re.compile(r"\b(c[oó]digo\s+real|ejemplo\s+pr[aá]ctico|implementaci[oó]n\s+en\s+c|c[oó]digo\s+python)\b", re.IGNORECASE),
        "Prefiere ejemplos de código real y ejecutable por sobre explicaciones puramente teóricas.",
    ],
    "comparative_tables": [
        re.compile(r"\b(tabla\s+comparativa|cuadro\s+comparativo|en\s+una\s+tabla|comparaci[oó]n)\b", re.IGNORECASE),
        "Prefiere tablas Markdown comparativas para contrastar pros, contras y trade-offs entre conceptos.",
    ],
    "hardware_physical_analogies": [
        re.compile(r"\b(bajo\s+nivel|silicio|hardware|registros|transistores|como\s+funciona\s+f[ií]sicamente)\b", re.IGNORECASE),
        "Afinidad alta con analogías mecánicas y aterrizaje a nivel de hardware, transistores y registros de CPU.",
    ],
    "analogy_driven_explanations": [
        re.compile(r"\b(analog[íi]a|analogías|met[áa]fora|met[áa]foras|ejemplificar)\b", re.IGNORECASE),
        "Prefiere que los conceptos se expliquen anclados en analogías y metáforas concretas.",
    ],
}

_EXPLICIT_PREFERENCE_PATTERN = re.compile(
    r"\b(?:yo\s+)?(?:prefiero|me\s+sirve\s+m[aá]s|me\s+ayuda\s+m[aá]s)\b",
    re.IGNORECASE,
)
_NEGATED_PREFERENCE_PATTERN = re.compile(
    r"\bno\s+(?:yo\s+)?(?:prefiero|me\s+sirve\s+m[aá]s|me\s+ayuda\s+m[aá]s)\b",
    re.IGNORECASE,
)


def is_explicit_preference_statement(user_query: str) -> bool:
    """Return whether the student positively states their own learning preference."""
    query = user_query or ""
    return bool(_EXPLICIT_PREFERENCE_PATTERN.search(query)) and not bool(
        _NEGATED_PREFERENCE_PATTERN.search(query)
    )


class PreferenceTracker:
    """Detects, updates, and retrieves student learning preferences."""

    def __init__(self, storage: Optional[StudentStorage] = None) -> None:
        self.storage = storage or StudentStorage()

    def record_explicit_preference(
        self,
        student_id: str,
        preference_text: str,
        confidence: float = 1.0,
        kc_id: Optional[str] = None,
    ) -> int:
        """Record or reinforce an explicit preference in pedagogical memory."""
        clean_pref = preference_text.strip()
        existing = self.storage.get_pedagogical_memories(
            student_id=student_id,
            category="preference",
            kc_id=kc_id,
            limit=10,
        )
        for mem in existing:
            if clean_pref.lower() in mem.get("insight", "").lower():
                self.storage.touch_pedagogical_memory(mem["id"])
                return mem["id"]

        return self.storage.save_pedagogical_memory(
            student_id=student_id,
            category="preference",
            kc_id=kc_id,
            insight=clean_pref,
            confidence=confidence,
        )

    def scan_query_for_preferences(
        self,
        student_id: str,
        user_query: str,
    ) -> List[str]:
        """Persist preferences only when the student explicitly states a preference."""
        if not is_explicit_preference_statement(user_query):
            return []

        detected = []
        for key, (pattern, canonical_insight) in _STYLE_PATTERNS.items():
            if pattern.search(user_query):
                self.record_explicit_preference(
                    student_id=student_id,
                    preference_text=canonical_insight,
                    confidence=0.90,
                )
                detected.append(key)
        return detected

    def get_active_preferences(
        self,
        student_id: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Fetch the most recently used learning preferences for student."""
        return self.storage.get_pedagogical_memories(
            student_id=student_id,
            category="preference",
            limit=limit,
        )

    def format_preferences_directive(
        self,
        student_id: str,
        limit: int = 3,
    ) -> str:
        """Format preferences into a compact prompt injection block."""
        prefs = self.get_active_preferences(student_id=student_id, limit=limit)
        if not prefs:
            return ""

        lines = ["=== PREFERENCIAS DIDÁCTICAS HISTÓRICAS DEL ESTUDIANTE ==="]
        for p in prefs:
            lines.append(f"- {p['insight']}")
        return "\n".join(lines)
