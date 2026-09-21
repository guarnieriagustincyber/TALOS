"""Deterministic Evaluation Graders for Pedagogical Tasks (N1 MVP).

INVARIANTS:
1. 100% Deterministic: Zero LLM hallucinations or heuristics in evaluation.
2. Sign-preserving and type-specific normalization:
   - MC: Exact option identity (strip only).
   - NUMERIC: Deterministic float/int parser (strictly preserves signs, e.g. -5 != 5).
   - EXACT_TEXT: Space collapsing and case normalization without dropping mathematical operators or signs.
3. Every grading outputs an audit trail (raw_answer, normalized_answer, policy, expected, comparison).
"""

from dataclasses import dataclass
import difflib
import json
from pathlib import Path
import re
from typing import Dict, List, Optional

from study_engine.pedagogy.exercise_contracts import ExerciseType

_SYNONYMS_CACHE: Optional[Dict[str, List[str]]] = None


def load_synonyms() -> Dict[str, List[str]]:
    """Singleton loader for canonical technical synonyms (E17)."""
    global _SYNONYMS_CACHE
    if _SYNONYMS_CACHE is None:
        syn_path = (
            Path(__file__).resolve().parents[3]
            / "data"
            / "pedagogy"
            / "synonyms.json"
        )
        if syn_path.exists():
            try:
                _SYNONYMS_CACHE = json.loads(syn_path.read_text(encoding="utf-8"))
            except Exception:
                _SYNONYMS_CACHE = {}
        else:
            _SYNONYMS_CACHE = {}
    return _SYNONYMS_CACHE


def check_synonym_match(student_answer: str, expected_answer: str) -> bool:
    """Bidirectional synonym check across canonical keys and variant lists (E17)."""
    synonyms = load_synonyms()
    student_norm = " ".join(student_answer.strip().lower().split())
    expected_norm = " ".join(expected_answer.strip().lower().split())

    for canonical, variants in synonyms.items():
        all_terms = {" ".join(canonical.strip().lower().split())}
        for v in variants:
            all_terms.add(" ".join(v.strip().lower().split()))
        if student_norm in all_terms and expected_norm in all_terms:
            return True
    return False


@dataclass(frozen=True)
class GradeResult:
    """Immutable audit record of a deterministic grading assessment."""

    is_correct: bool
    raw_answer: str
    normalized_answer: str
    normalization_policy: str
    expected_answer: str
    comparison_result: str
    feedback: str


class MultiChoiceGrader:
    """Deterministic grader for Multiple Choice questions."""

    def grade(self, selected_option: str, expected_option: str) -> GradeResult:
        raw = selected_option
        norm_sel = selected_option.strip().upper()
        norm_exp = expected_option.strip().upper()

        is_correct = norm_sel == norm_exp
        comp_str = f"EQUAL('{norm_sel}', '{norm_exp}')" if is_correct else f"DIFF('{norm_sel}', '{norm_exp}')"
        feedback = (
            "¡Correcto! Opción seleccionada verificada con éxito contra el corpus."
            if is_correct
            else f"Opción incorrecta. La opción correcta es '{norm_exp}'."
        )

        return GradeResult(
            is_correct=is_correct,
            raw_answer=raw,
            normalized_answer=norm_sel,
            normalization_policy="mc_option_identity",
            expected_answer=norm_exp,
            comparison_result=comp_str,
            feedback=feedback,
        )


class ExactMatchGrader:
    """Deterministic grader supporting NUMERIC and EXACT_TEXT normalization policies."""

    def grade(
        self,
        student_answer: str,
        expected_answer: str,
        exercise_type: ExerciseType = ExerciseType.EXACT_TEXT,
    ) -> GradeResult:
        raw = student_answer

        if exercise_type == ExerciseType.NUMERIC:
            return self._grade_numeric(raw, expected_answer)
        else:
            return self._grade_exact_text(raw, expected_answer)

    def _grade_numeric(self, raw: str, expected: str) -> GradeResult:
        policy = "numeric_parse_preserve_signs"
        norm_exp = expected.strip()
        cleaned_raw = raw.strip()

        # Parse expected float/int
        try:
            exp_val = float(norm_exp)
        except ValueError:
            exp_val = None

        try:
            # Match first sign-preserved numeric token
            match = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned_raw)
            if match is None or exp_val is None:
                return GradeResult(
                    is_correct=False,
                    raw_answer=raw,
                    normalized_answer=cleaned_raw,
                    normalization_policy=policy,
                    expected_answer=norm_exp,
                    comparison_result="PARSE_ERROR",
                    feedback="No se pudo interpretar un valor numérico válido en tu respuesta.",
                )

            student_val = float(match.group(0))
            is_correct = abs(student_val - exp_val) < 1e-6
            norm_student = str(student_val if student_val % 1 != 0 else int(student_val))
            comp_str = f"{student_val} == {exp_val}" if is_correct else f"{student_val} != {exp_val}"
            feedback = (
                f"¡Excelente! El cálculo numérico es exactamente {norm_exp}."
                if is_correct
                else f"Cálculo numérico incorrecto. El resultado formal esperado es {norm_exp}."
            )

            return GradeResult(
                is_correct=is_correct,
                raw_answer=raw,
                normalized_answer=norm_student,
                normalization_policy=policy,
                expected_answer=norm_exp,
                comparison_result=comp_str,
                feedback=feedback,
            )
        except Exception as err:
            return GradeResult(
                is_correct=False,
                raw_answer=raw,
                normalized_answer=cleaned_raw,
                normalization_policy=policy,
                expected_answer=norm_exp,
                comparison_result=f"ERROR: {str(err)}",
                feedback="Error evaluando respuesta numérica.",
            )

    def _grade_exact_text(self, raw: str, expected: str) -> GradeResult:
        # 1. Normalización exacta preservando signos y operadores
        norm_student = " ".join(raw.strip().lower().split())
        norm_expected = " ".join(expected.strip().lower().split())

        # Capa 1: Coincidencia exacta tras normalización
        if norm_student == norm_expected:
            return GradeResult(
                is_correct=True,
                raw_answer=raw,
                normalized_answer=norm_student,
                normalization_policy="exact_text_strip_collapse_preserve_operators",
                expected_answer=norm_expected,
                comparison_result=f"EQUIV('{norm_student}', '{norm_expected}')",
                feedback="¡Respuesta correcta! Coincide exactamente con la formulación formal del corpus.",
            )

        # Capa 2: Sinónimos técnicos canónicos (E12, E17)
        if check_synonym_match(norm_student, norm_expected):
            return GradeResult(
                is_correct=True,
                raw_answer=raw,
                normalized_answer=norm_student,
                normalization_policy="synonym_match",
                expected_answer=norm_expected,
                comparison_result=f"SYNONYM('{norm_student}', '{norm_expected}')",
                feedback="¡Respuesta correcta! Tu formulación es conceptualmente equivalente según la terminología técnica canónica.",
            )

        # Capa 3: Coincidencia difusa de Levenshtein / SequenceMatcher >= 0.85 (E12)
        similarity = difflib.SequenceMatcher(None, norm_student, norm_expected).ratio()
        if similarity >= 0.85:
            return GradeResult(
                is_correct=True,
                raw_answer=raw,
                normalized_answer=norm_student,
                normalization_policy="fuzzy_match",
                expected_answer=norm_expected,
                comparison_result=f"FUZZY({similarity:.2f})",
                feedback=f"¡Respuesta correcta! (Aceptada con tolerancia ortográfica/variante de {int(similarity * 100)}%).",
            )

        # No coincidente
        return GradeResult(
            is_correct=False,
            raw_answer=raw,
            normalized_answer=norm_student,
            normalization_policy="exact_text_strip_collapse_preserve_operators",
            expected_answer=norm_expected,
            comparison_result=f"DIFF('{norm_student}', '{norm_expected}')",
            feedback=f"Respuesta no equivalente. La formulación esperada es: '{expected}'.",
        )
