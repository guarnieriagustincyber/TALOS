"""Learning Patterns Analyzer for Long-Term Student Profiling (Fase 6).

Identifies recurring cognitive friction points, cognitive fatigue signals,
and learning velocity patterns across sessions, storing structured patterns
into `student_pedagogical_memory`.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import re
from typing import Any, Dict, List, Optional

from study_engine.student.storage import StudentStorage

logger = logging.getLogger(__name__)

# Recurrent vulnerability & programming conceptual error signatures
_RECURRENT_ERROR_SIGNATURES = {
    "off_by_one": [
        re.compile(r"\b(off-by-one|fuera\s+por\s+uno|desborde\s+en\s+el\s+borde|menor\s+o\s+igual\s+en\s+vez\s+de\s+menor)\b", re.IGNORECASE),
        "Patrón de error recurrente: tendencia a errores off-by-one en bucles contados e índices de frontera.",
    ],
    "null_pointer": [
        re.compile(r"\b(segfault|puntero\s+nulo|null\s+pointer|desreferencia\s+invalida)\b", re.IGNORECASE),
        "Patrón de error recurrente: omisión de validación defensiva Fail-Fast contra punteros nulos.",
    ],
    "infinite_loop": [
        re.compile(r"\b(bucle\s+infinito|loop\s+infinito|no\s+corta\s+el\s+while|condicion\s+nunca\s+falsa)\b", re.IGNORECASE),
        "Patrón de error recurrente: falta de avance explícito en la variable de control de bucles condicionales.",
    ],
    "buffer_boundary": [
        re.compile(r"\b(buffer\s+overflow|escritura\s+fuera\s+del\s+limite|limite\s+del\s+arreglo)\b", re.IGNORECASE),
        "Patrón de error recurrente: no acotar la longitud máxima de entrada antes de copiar en búferes estáticos.",
    ],
    "base_conversion": [
        re.compile(r"\b(cero\s+a\s+la\s+izquierda|octal|base\s+8|010\s+vs\s+10)\b", re.IGNORECASE),
        "Patrón de fricción: confusión recurrente con literales octales y convención de base 8 en C/POSIX.",
    ],
}


class LearningPatternsTracker:
    """Tracks qualitative student learning patterns and recurring error modes."""

    def __init__(self, storage: Optional[StudentStorage] = None) -> None:
        self.storage = storage or StudentStorage()

    def record_learning_pattern(
        self,
        student_id: str,
        pattern_description: str,
        pattern_type: str = "recurring_error",
        kc_id: Optional[str] = None,
        confidence: float = 0.85,
    ) -> int:
        """Record or refresh a detected learning pattern."""
        clean_text = pattern_description.strip()
        existing = self.storage.get_pedagogical_memories(
            student_id=student_id,
            category=pattern_type,
            kc_id=kc_id,
            limit=10,
        )
        for mem in existing:
            if clean_text.lower() in mem.get("insight", "").lower():
                self.storage.touch_pedagogical_memory(mem["id"])
                return mem["id"]

        return self.storage.save_pedagogical_memory(
            student_id=student_id,
            category=pattern_type,
            kc_id=kc_id,
            insight=clean_text,
            confidence=confidence,
        )

    def analyze_dialogue_turn(
        self,
        student_id: str,
        user_query: str,
        active_kc: Optional[str] = None,
    ) -> List[str]:
        """Scan student messages for recurring vulnerability patterns or cognitive blind spots."""
        detected = []
        for key, (pattern, description) in _RECURRENT_ERROR_SIGNATURES.items():
            if pattern.search(user_query):
                self.record_learning_pattern(
                    student_id=student_id,
                    pattern_description=description,
                    pattern_type="recurring_error",
                    kc_id=active_kc,
                    confidence=0.80,
                )
                detected.append(key)
        return detected

    def get_student_error_patterns(
        self,
        student_id: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Fetch identified recurrent errors for student."""
        return self.storage.get_pedagogical_memories(
            student_id=student_id,
            category="recurring_error",
            limit=limit,
        )

    def format_patterns_directive(
        self,
        student_id: str,
        limit: int = 3,
    ) -> str:
        """Format recognized error patterns as preventive alerts for the tutor prompt."""
        patterns = self.get_student_error_patterns(student_id=student_id, limit=limit)
        if not patterns:
            return ""

        lines = ["=== ALERTAS PEDAGÓGICAS DE PUNTOS CIEGOS RECURRENTES ==="]
        for p in patterns:
            lines.append(f"⚠️ {p['insight']}")
        lines.append("[Instrucción al tutor: Reforzá preventivamente estos puntos ciegos si surgen en la explicación]")
        return "\n".join(lines)
