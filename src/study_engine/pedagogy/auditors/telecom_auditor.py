"""Deterministic Telecommunications exercise auditor (FADENA Telecomunicaciones).

Evaluates:
1. Mathematical formula specification (attenuation, optical link budget, Shannon-Nyquist)
2. Numerical calculations with physical units (dB, dBm, km, Mbps)
3. Quantitative result statement
4. Link feasibility and safety margin analysis
"""

import re
from typing import List

from study_engine.pedagogy.auditors.base_auditor import (
    AuditCheck,
    BaseExerciseAuditor,
    ExerciseAuditReport,
)
from study_engine.pedagogy.submission_reader import StudentSubmission


class TelecomExerciseAuditor(BaseExerciseAuditor):
    """Auditor for Telecommunications link budgets, signal models and networking calculations."""

    UNIT_TOKENS = ["db", "dbm", "km", "m", "hz", "khz", "mhz", "ghz", "bps", "kbps", "mbps", "gbps"]

    def audit(self, submission: StudentSubmission) -> ExerciseAuditReport:
        checks: List[AuditCheck] = []
        observations: List[str] = []

        # 1. Formulas Section
        formula_text = submission.get_section("formulas") or submission.get_section("formula")
        if not formula_text:
            checks.append(AuditCheck("formulas", False, "Falta la sección de Fórmulas teóricas."))
        else:
            has_eq = "=" in formula_text
            if has_eq:
                checks.append(AuditCheck("formulas", True, "Fórmulas teóricas especificadas con variables y operadores."))
            else:
                checks.append(AuditCheck("formulas", False, "Las fórmulas deben incluir relaciones de igualdad explícitas (=).", severity="WARNING"))

        # 2. Calculations with Physical Units
        calc_text = submission.get_section("calculos") or submission.get_section("calculo")
        if not calc_text:
            checks.append(AuditCheck("calculations", False, "Falta la sección de Cálculos numéricos."))
        else:
            calc_lower = calc_text.lower()
            found_units = [u for u in self.UNIT_TOKENS if re.search(rf"\b{u}\b", calc_lower)]
            if len(found_units) >= 2:
                checks.append(AuditCheck("calculations", True, f"Cálculos detallados con unidades físicas identificadas ({', '.join(found_units[:4])})."))
            else:
                checks.append(AuditCheck("calculations", False, "Los cálculos deben incluir unidades de medida físicas explícitas (dB, dBm, km, Mbps).", severity="WARNING"))

        # 3. Explicit Result
        res_text = submission.get_section("resultado")
        if not res_text:
            checks.append(AuditCheck("result", False, "Falta la sección de Resultado explícito.", severity="WARNING"))
        else:
            has_num = bool(re.search(r"\d+", res_text))
            if has_num:
                checks.append(AuditCheck("result", True, "Conclusión cuantitativa del resultado final declarada."))
            else:
                checks.append(AuditCheck("result", False, "El resultado debe declarar el valor numérico obtenido.", severity="WARNING"))

        # 4. Feasibility Analysis
        analysis_text = submission.get_section("analisis") or submission.get_section("analisis_critico")
        if not analysis_text:
            checks.append(AuditCheck("analysis", False, "Falta la sección de Análisis de viabilidad del enlace.", severity="WARNING"))
        else:
            words = analysis_text.split()
            if len(words) >= 20:
                checks.append(AuditCheck("analysis", True, f"Análisis de viabilidad técnica documentado ({len(words)} palabras)."))
            else:
                checks.append(AuditCheck("analysis", False, "El análisis técnico del enlace es demasiado escueto (se esperan >= 20 palabras).", severity="WARNING"))

        # Compute Score
        evaluables = [c for c in checks if c.severity in ("ERROR", "WARNING")]
        passed_evaluables = [c for c in evaluables if c.passed]
        score = round((len(passed_evaluables) / len(evaluables) * 100.0), 1) if evaluables else 0.0
        is_passed = score >= 70.0 and any(c.name == "calculations" and c.passed for c in checks)

        # BKT Update
        target_kc = submission.metadata.get("kc_id") or submission.exercise_id
        bkt_updated, p_before, p_after = self.update_bkt_if_eligible(target_kc, is_passed, score)

        return ExerciseAuditReport(
            exercise_id=submission.exercise_id,
            notebook_id=submission.metadata.get("notebook_id", "fadena-teleco"),
            score=score,
            passed=is_passed,
            checks=checks,
            bkt_updated=bkt_updated,
            p_L_before=p_before,
            p_L_after=p_after,
            observations=observations,
            next_exercise="ej_02_modelo_osi" if "01" in submission.exercise_id else None,
        )
