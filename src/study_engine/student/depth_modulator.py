"""Pedagogical Depth Modulator for Subsystem E3 (Student Cognitive Layer).

Injects pedagogical instructions into prompts based on student mastery P(L).
INVARIANTS:
1. Consultative: Modulates ONLY pedagogical directives in prompt construction.
2. Zero mutation of admitted evidence chunks, relevance scores, or source authority.
3. Completely deterministic based on P(L) thresholds: >= 0.80 (Advanced), >= 0.50 (Standard), < 0.50 (Foundations).
"""

from typing import Any, List, Optional

from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.storage import StudentStorage


class DepthModulator:
    """Computes prompt directives reflecting the student's mastery of the active topic."""

    def __init__(
        self,
        bkt: BKTTracker,
        storage: Optional[StudentStorage] = None,
    ) -> None:
        self.bkt = bkt
        self.storage = storage or getattr(bkt, "storage", None) or StudentStorage(db_path=":memory:")

    def get_directives(self, topic_id: str) -> List[str]:
        """Generate pedagogical prompt directives according to BKT mastery P(L)."""
        if not topic_id or not topic_id.strip():
            raise ValueError("topic_id cannot be empty or whitespace")

        state = self.bkt.get_state(topic_id.strip())
        p_L = state.p_L

        directives: List[str] = []

        if p_L >= 0.80:
            directives = [
                f"El estudiante domina este tema (P(L)={p_L:.2f}).",
                "Podés usar terminología técnica sin definir.",
                "Incluí ejemplos avanzados y edge cases.",
                "Evitá analogías básicas.",
            ]
        elif p_L >= 0.50:
            directives = [
                f"El estudiante tiene noción básica (P(L)={p_L:.2f}).",
                "Definí términos técnicos la primera vez.",
                "Incluí 1-2 analogías del mundo físico.",
                "Ejemplos intermedios.",
            ]
        else:
            directives = [
                f"El estudiante está aprendiendo desde cero (P(L)={p_L:.2f}).",
                "Definí TODOS los términos técnicos.",
                "Usá múltiples analogías del mundo físico.",
                "Ejemplos simples y graduales.",
                "Evitá jerga innecesaria.",
            ]

        # Check if student has active DUAL_TRACK choices for this topic (H6)
        remediations = self.storage.get_remediation_choices(topic_id=topic_id.strip())
        dual_track_active = any(r.get("chosen_option") == "DUAL_TRACK" for r in remediations)
        if dual_track_active:
            directives.append(
                "MODALIDAD DUAL-TRACK ACTIVA: Incluí un breve puente conceptual con el prerequisito en refuerzo paralelo."
            )

        return directives

    def format_pedagogical_block(self, topic_id: str) -> str:
        """Format directives as a formatted prompt section."""
        directives = self.get_directives(topic_id)
        formatted_body = "\n".join(f"- {d}" for d in directives)
        return (
            "=== DIRECTIVAS PEDAGÓGICAS (ADAPTACIÓN DE PROFUNDIDAD SEGÚN MAESTRÍA) ===\n"
            f"{formatted_body}\n"
        )
