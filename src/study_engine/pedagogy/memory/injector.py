"""ProfileInjector — Deterministic Injection of Cognitive Profile (Opción C).

Design & Invariants:
- Strictly <120 tokens: Compact structured XML representation (<student_cognitive_profile>).
- Anti-saturation: Caps at max 10 active items, prioritizes recurring misconceptions & weaknesses.
- Socratic enforcement: If a KC has ≥3 recorded failures (occurrences ≥ 3), forces an explicit
  remedial warning so the model does NOT give away the direct answer.
- Zero footprint if empty: Returns empty string if the student has no profile items.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from study_engine.pedagogy.memory.store import CognitiveProfileStore

logger = logging.getLogger(__name__)

# Hard token cap safeguard (~4 chars per token)
_MAX_CHAR_BUDGET = 500


class ProfileInjector:
    """Injects high-signal cognitive traits into system prompt under 120 tokens."""

    def __init__(self, store: CognitiveProfileStore) -> None:
        self.store = store

    def build_injection_block(
        self,
        student_id: str,
        active_kc: Optional[str] = None,
        notebook_kcs: Optional[List[str]] = None,
    ) -> str:
        """Builds concise <student_cognitive_profile> XML block for system prompt."""
        items = self.store.get_for_injection(
            user_id=student_id,
            notebook_kc_ids=notebook_kcs,
            max_items=8,
        )

        if not items:
            return ""

        lines: List[str] = ["<student_cognitive_profile>"]

        # Check for 3-failures rule on active KC
        severe_blocker = False
        if active_kc:
            for it in items:
                if it.get("kc_id") == active_kc and it.get("occurrences", 1) >= 3:
                    severe_blocker = True
                    lines.append(
                        f"  <alert rule=\"3_failures_remedial\" kc=\"{active_kc}\">"
                        "El estudiante falló este concepto ≥3 veces. "
                        "PROHIBIDO dar la solución directa; usar analogía concreta y guiar socráticamente paso a paso."
                        "</alert>"
                    )
                    break

        # Group items cleanly
        for it in items:
            cat = it.get("category", "")
            kc = it.get("kc_id", "")
            desc = it.get("description", "").replace("<", "&lt;").replace(">", "&gt;")
            occ = it.get("occurrences", 1)
            occ_attr = f" occurrences=\"{occ}\"" if occ > 1 else ""

            if cat == "RECURRING_MISCONCEPTION":
                lines.append(f"  <misconception kc=\"{kc}\"{occ_attr}>{desc}</misconception>")
            elif cat == "WEAKNESS":
                lines.append(f"  <weakness kc=\"{kc}\"{occ_attr}>{desc}</weakness>")
            elif cat == "PREFERENCE":
                lines.append(f"  <preference>{desc}</preference>")
            elif cat == "ANALOGY_AFFINITY":
                lines.append(f"  <affinity kc=\"{kc}\">{desc}</affinity>")
            elif cat == "STRENGTH":
                lines.append(f"  <mastery kc=\"{kc}\">{desc}</mastery>")

        lines.append("</student_cognitive_profile>")
        block = "\n".join(lines)

        # Enforce character budget to guarantee <120 tokens
        if len(block) > _MAX_CHAR_BUDGET:
            # Cut gracefully before closing tag
            block = block[:_MAX_CHAR_BUDGET - 30].rsplit("\n", 1)[0] + "\n</student_cognitive_profile>"

        return block
