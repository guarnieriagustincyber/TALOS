"""Domain exercise auditors package (VSCode + TALOS)."""

from typing import Any, Optional

from study_engine.pedagogy.auditors.base_auditor import (
    AuditCheck,
    BaseExerciseAuditor,
    ExerciseAuditReport,
)
from study_engine.pedagogy.auditors.fadena_auditor import FADENAExerciseAuditor
from study_engine.pedagogy.auditors.programming_auditor import ProgrammingExerciseAuditor
from study_engine.pedagogy.auditors.so_auditor import SOExerciseAuditor
from study_engine.pedagogy.auditors.telecom_auditor import TelecomExerciseAuditor


def get_auditor_for_notebook(notebook_id: str, bkt_tracker: Optional[Any] = None) -> BaseExerciseAuditor:
    """Factory creating domain auditor specialized by notebook identifier."""
    nb = notebook_id.lower().strip()
    if "so2" in nb or "operativo" in nb:
        return SOExerciseAuditor(bkt_tracker=bkt_tracker)
    elif "teleco" in nb or "redes" in nb:
        return TelecomExerciseAuditor(bkt_tracker=bkt_tracker)
    elif "sye" in nb or "sociedad" in nb or "estado" in nb:
        return FADENAExerciseAuditor(bkt_tracker=bkt_tracker)
    elif "fase0" in nb or "lenguajes" in nb or "prog" in nb:
        return ProgrammingExerciseAuditor(bkt_tracker=bkt_tracker)
    # Default to programming
    return ProgrammingExerciseAuditor(bkt_tracker=bkt_tracker)


__all__ = [
    "AuditCheck",
    "BaseExerciseAuditor",
    "ExerciseAuditReport",
    "FADENAExerciseAuditor",
    "ProgrammingExerciseAuditor",
    "SOExerciseAuditor",
    "TelecomExerciseAuditor",
    "get_auditor_for_notebook",
]
