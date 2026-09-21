"""High-level qualitative pedagogical memory tracker for students (Fase 3).

Captures misconceptions, explanation preferences, and recurrent learning patterns
in SQLite without external vector databases or high-latency dependencies.
"""

from typing import Any, Dict, List, Optional
from study_engine.student.storage import StudentStorage


class PedagogicalMemoryTracker:
    """Manages student qualitative insights and generates context directives."""

    def __init__(self, storage: Optional[StudentStorage] = None) -> None:
        self.storage = storage or StudentStorage()

    def record_misconception(
        self,
        student_id: str,
        kc_id: str,
        misconception: str,
        confidence: float = 0.9,
    ) -> int:
        """Record an identified conceptual misconception or confusion pattern."""
        return self.storage.save_pedagogical_memory(
            student_id=student_id,
            category="misconception",
            kc_id=kc_id,
            insight=misconception.strip(),
            confidence=confidence,
        )

    def record_preference(
        self,
        student_id: str,
        preference_text: str,
        confidence: float = 1.0,
    ) -> int:
        """Record pedagogical explanation preference (e.g. 'prefers mechanical analogies')."""
        return self.storage.save_pedagogical_memory(
            student_id=student_id,
            category="preference",
            kc_id=None,
            insight=preference_text.strip(),
            confidence=confidence,
        )

    def record_analogy_affinity(
        self,
        student_id: str,
        domain: str,
        confidence: float = 0.95,
    ) -> int:
        """Record domain affinity for analogies (e.g. 'hardware / electronics', 'urban traffic')."""
        insight = f"Afinidad alta con analogías basadas en '{domain}'."
        return self.storage.save_pedagogical_memory(
            student_id=student_id,
            category="analogy_affinity",
            kc_id=None,
            insight=insight,
            confidence=confidence,
        )

    def get_tutor_guidance_notes(
        self,
        student_id: str = "default_student",
        kc_id: Optional[str] = None,
        max_notes: int = 3,
    ) -> str:
        """Format qualitative insights as a concise pedagogical directive for generation prompts."""
        memories = self.storage.get_pedagogical_memories(
            student_id=student_id,
            kc_id=kc_id,
            limit=max_notes,
        )
        if not memories and kc_id:
            # Fallback to general preferences if no KC-specific misconceptions exist
            memories = self.storage.get_pedagogical_memories(
                student_id=student_id,
                category="preference",
                limit=max_notes,
            )

        if not memories:
            return ""

        lines = ["NOTAS DE APRENDIZAJE PREVIO DEL ESTUDIANTE:"]
        for idx, m in enumerate(memories, 1):
            category = m.get("category", "")
            insight = m.get("insight", "")
            lines.append(f"{idx}. [{category.upper()}] {insight}")

        return "\n".join(lines)

    def format_tutor_directive(
        self,
        student_id: str = "default_student",
        kc_id: Optional[str] = None,
        limit: int = 3,
    ) -> str:
        """Convenience alias for get_tutor_guidance_notes matching tutor pipeline conventions."""
        return self.get_tutor_guidance_notes(
            student_id=student_id,
            kc_id=kc_id,
            max_notes=limit,
        )
