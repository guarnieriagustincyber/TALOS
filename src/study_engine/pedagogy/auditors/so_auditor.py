"""Deterministic Operating Systems exercise auditor (FADENA SO II y Sistemas Operativos).

Evaluates:
1. Mermaid state diagram completeness (New, Ready, Running, Waiting, Terminated)
2. State transition coverage and causality explanation
3. Numerical scheduling and resource allocation calculations
4. Depth and rigor of critical analysis
"""

import re
from typing import List

from study_engine.pedagogy.auditors.base_auditor import (
    AuditCheck,
    BaseExerciseAuditor,
    ExerciseAuditReport,
)
from study_engine.pedagogy.submission_reader import StudentSubmission


class SOExerciseAuditor(BaseExerciseAuditor):
    """Auditor for Operating Systems practical assignments and models."""

    REQUIRED_STATES = ["new", "ready", "running", "waiting", "terminated"]
    CORE_TRANSITIONS = ["ready", "running", "waiting"]

    def audit(self, submission: StudentSubmission) -> ExerciseAuditReport:
        checks: List[AuditCheck] = []
        observations: List[str] = []

        # 1. State Diagram Validation
        diagram_text = submission.get_code_block("mermaid") or submission.get_section("diagrama_de_estados")
        if not diagram_text:
            checks.append(AuditCheck("diagram", False, "Falta el Diagrama de Estados en formato Mermaid."))
        else:
            is_state_diag = "statediagram" in diagram_text.lower()
            if not is_state_diag:
                checks.append(AuditCheck("diagram", False, "El diagrama debe ser un 'stateDiagram-v2' de Mermaid."))
            else:
                # Check coverage of states
                diag_lower = diagram_text.lower()
                found_states = [s for s in self.REQUIRED_STATES if s in diag_lower or (s == "waiting" and "blocked" in diag_lower)]
                if len(found_states) >= 4:
                    checks.append(AuditCheck("diagram", True, f"Diagrama de estados completo ({len(found_states)}/5 estados canónicos presentes)."))
                else:
                    checks.append(AuditCheck("diagram", False, f"Diagrama incompleto: detectados {len(found_states)}/5 estados requeridos."))

        # 2. Transition Explanation
        trans_text = submission.get_section("explicacion_de_transiciones") or submission.get_section("transiciones")
        if not trans_text:
            checks.append(AuditCheck("transitions", False, "Falta la sección de Explicación de Transiciones.", severity="WARNING"))
        else:
            trans_lower = trans_text.lower()
            covered = sum(1 for t in ["ready", "running", "waiting", "terminated"] if t in trans_lower)
            if covered >= 3:
                checks.append(AuditCheck("transitions", True, f"Explicación detallada de transiciones de proceso ({covered} analizadas)."))
            else:
                checks.append(AuditCheck("transitions", False, "Falta detallar transiciones clave (Ready->Running, Running->Waiting).", severity="WARNING"))

        # 3. Numerical Calculations
        calc_text = submission.get_section("calculos") or submission.get_section("calculo")
        if not calc_text:
            checks.append(AuditCheck("calculations", True, "Sin cálculos numéricos requeridos para este ejercicio.", severity="INFO"))
        else:
            # Check for numbers, formulas or arithmetic
            has_numbers = bool(re.search(r"\d+", calc_text))
            has_math = any(sym in calc_text for sym in ["=", "+", "/", "-", "*"])
            if has_numbers and has_math:
                checks.append(AuditCheck("calculations", True, "Cálculos numéricos presentes y estructurados con fórmulas explícitas."))
            else:
                checks.append(AuditCheck("calculations", False, "La sección de cálculos debe contener operaciones aritméticas verificables.", severity="WARNING"))

        # 4. Critical Analysis
        analysis_text = submission.get_section("analisis_critico") or submission.get_section("analisis")
        if not analysis_text:
            checks.append(AuditCheck("analysis", False, "Falta la sección de Análisis Crítico.", severity="WARNING"))
        else:
            words = analysis_text.split()
            if len(words) >= 30:
                checks.append(AuditCheck("analysis", True, f"Análisis crítico fundamentado ({len(words)} palabras)."))
            else:
                checks.append(AuditCheck("analysis", False, "El análisis crítico es demasiado breve (se esperan >= 30 palabras).", severity="WARNING"))

        # Compute Score
        evaluables = [c for c in checks if c.severity in ("ERROR", "WARNING")]
        passed_evaluables = [c for c in evaluables if c.passed]
        score = round((len(passed_evaluables) / len(evaluables) * 100.0), 1) if evaluables else 0.0
        is_passed = score >= 70.0 and any(c.name == "diagram" and c.passed for c in checks)

        # BKT Update
        target_kc = submission.metadata.get("kc_id") or submission.exercise_id
        bkt_updated, p_before, p_after = self.update_bkt_if_eligible(target_kc, is_passed, score)

        return ExerciseAuditReport(
            exercise_id=submission.exercise_id,
            notebook_id=submission.metadata.get("notebook_id", "fadena-so2"),
            score=score,
            passed=is_passed,
            checks=checks,
            bkt_updated=bkt_updated,
            p_L_before=p_before,
            p_L_after=p_after,
            observations=observations,
            next_exercise="ej_02_scheduling_sjf" if "01" in submission.exercise_id else None,
        )
