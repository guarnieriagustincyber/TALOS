"""Performance level contracts and pedagogical scales for Subsystem S5.4.

INVARIANTS:
1. PerformanceLevel is an IntEnum with strictly ordered values 1..4.
2. N1 < N2 < N3 < N4 with deterministic ordinal comparisons.
3. No aliases; exactly 4 discrete levels.
4. S5.4 defines expected levels declaratively;
   it does NOT assign levels to students.
"""

from enum import IntEnum


class PerformanceLevel(IntEnum):
    """Pedagogical competency scale for cybersecurity curriculum."""

    N1_INSUFFICIENT = 1
    N2_BASIC = 2
    N3_COMPETENT = 3
    N4_EXCELLENT = 4

    @property
    def label(self) -> str:
        """Return short label representation (e.g. 'N1', 'N3')."""
        return self.name.split("_")[0]

    @property
    def description(self) -> str:
        """Pedagogical descriptor of the performance level."""
        if self == PerformanceLevel.N1_INSUFFICIENT:
            return "Insufficient: code does not run, explanation absent"
        if self == PerformanceLevel.N2_BASIC:
            return "Basic: runs with minor defects, standard explanation"
        if self == PerformanceLevel.N3_COMPETENT:
            return "Competent: fully meets spec, formal invariant reasoning"
        if self == PerformanceLevel.N4_EXCELLENT:
            return "Excellent: perturbation prediction, deep foundations"
        return "Unknown"

    @classmethod
    def from_label(cls, label: str) -> "PerformanceLevel":
        """Parse performance level from label ('N1', 'N2', 'N3', 'N4')."""
        clean = label.strip().upper()
        mapping = {
            "N1": cls.N1_INSUFFICIENT,
            "N2": cls.N2_BASIC,
            "N3": cls.N3_COMPETENT,
            "N4": cls.N4_EXCELLENT,
        }
        if clean not in mapping:
            raise ValueError(
                f"Invalid performance level label: '{label}'. "
                f"Must be one of N1, N2, N3, N4."
            )
        return mapping[clean]
