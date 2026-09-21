"""Deterministic Social and Political Science exercise auditor (FADENA Sociedad y Estado / Doctrinal).

Evaluates:
1. Clear formulation of Central Thesis
2. Structured arguments count (minimum 3 well-developed points)
3. Verified doctrinal/legal citations (e.g. Bobbio, Constitution)
4. Critical thinking, counterpoints and dialectical contrast
"""

import re
from typing import List

from study_engine.pedagogy.auditors.base_auditor import (
    AuditCheck,
    BaseExerciseAuditor,
    ExerciseAuditReport,
)
from study_engine.pedagogy.submission_reader import StudentSubmission


class FADENAExerciseAuditor(BaseExerciseAuditor):
    """Auditor for political science, legal theory and state doctrine essays."""

    def audit(self, submission: StudentSubmission) -> ExerciseAuditReport:
        checks: List[AuditCheck] = []
        observations: List[str] = []

        # 1. Central Thesis
        thesis_text = submission.get_section("tesis_central") or submission.get_section("tesis")
        if not thesis_text:
            checks.append(AuditCheck("thesis", False, "Falta la formulación de la Tesis Central."))
        else:
            words = thesis_text.split()
            if len(words) >= 15:
                checks.append(AuditCheck("thesis", True, f"Tesis central formulada con claridad ({len(words)} palabras)."))
            else:
                checks.append(AuditCheck("thesis", False, "La tesis central es demasiado breve (se esperan >= 15 palabras).", severity="WARNING"))

        # 2. Structured Arguments (>= 3)
        args_text = submission.get_section("argumentos")
        if not args_text:
            checks.append(AuditCheck("arguments", False, "Falta la sección de Argumentos."))
        else:
            # Count H3 headers or numbered arguments
            h3_count = len(re.findall(r"^###\s+", args_text, re.MULTILINE))
            numbered_count = len(re.findall(r"^\d+[\.\)]\s+", args_text, re.MULTILINE))
            arg_count = max(h3_count, numbered_count)

            if arg_count >= 3:
                checks.append(AuditCheck("arguments", True, f"Desarrollo argumental sólido ({arg_count} argumentos estructurados identificados)."))
            elif arg_count > 0:
                checks.append(AuditCheck("arguments", False, f"Se requieren al menos 3 argumentos estructurados (detectados: {arg_count}).", severity="WARNING"))
            else:
                checks.append(AuditCheck("arguments", False, "No se detectaron sub-ejes argumentales claros (usar ### o numeración 1, 2, 3).", severity="WARNING"))

        # 3. Textual / Doctrinal Citations (>= 2)
        citations_text = submission.get_section("citas") or submission.get_section("referencias")
        if not citations_text:
            checks.append(AuditCheck("citations", False, "Falta la sección de Citas bibliográficas y fuentes.", severity="WARNING"))
        else:
            cite_lines = [l.strip() for l in citations_text.splitlines() if l.strip().startswith("-") or re.match(r"^\d+[\.\)]", l.strip())]
            if len(cite_lines) >= 2:
                checks.append(AuditCheck("citations", True, f"Citas bibliográficas autorizadas verificadas ({len(cite_lines)} citas)."))
            elif len(cite_lines) == 1:
                checks.append(AuditCheck("citations", False, "Se recomienda incluir al menos 2 citas de fuentes autorizadas (detectada: 1).", severity="WARNING"))
            else:
                checks.append(AuditCheck("citations", False, "Las citas deben listarse claramente con viñetas o numeración.", severity="WARNING"))

        # 4. Critical Counterpoint and Synthesis
        counter_text = submission.get_section("critica_y_contrapunto") or submission.get_section("contrapunto")
        conclusion_text = submission.get_section("conclusion")
        if not counter_text and not conclusion_text:
            checks.append(AuditCheck("critical_thinking", False, "Falta sección de Crítica/Contrapunto o Conclusión.", severity="WARNING"))
        else:
            combined = (counter_text + " " + conclusion_text).strip()
            if len(combined.split()) >= 30:
                checks.append(AuditCheck("critical_thinking", True, "Análisis crítico dialéctico y síntesis institucional presentes."))
            else:
                checks.append(AuditCheck("critical_thinking", False, "El contrapunto dialéctico debe profundizar en tensiones doctrinales.", severity="WARNING"))

        # Compute Score
        evaluables = [c for c in checks if c.severity in ("ERROR", "WARNING")]
        passed_evaluables = [c for c in evaluables if c.passed]
        score = round((len(passed_evaluables) / len(evaluables) * 100.0), 1) if evaluables else 0.0
        is_passed = score >= 70.0 and any(c.name == "thesis" and c.passed for c in checks)

        # BKT Update
        target_kc = submission.metadata.get("kc_id") or submission.exercise_id
        bkt_updated, p_before, p_after = self.update_bkt_if_eligible(target_kc, is_passed, score)

        return ExerciseAuditReport(
            exercise_id=submission.exercise_id,
            notebook_id=submission.metadata.get("notebook_id", "fadena-sye"),
            score=score,
            passed=is_passed,
            checks=checks,
            bkt_updated=bkt_updated,
            p_L_before=p_before,
            p_L_after=p_after,
            observations=observations,
            next_exercise="ej_02_estado_gobierno" if "01" in submission.exercise_id else None,
        )
