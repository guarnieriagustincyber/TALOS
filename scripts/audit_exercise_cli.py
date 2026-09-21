#!/usr/bin/env python3
"""CLI Auditor de Ejercicios TALOS para VSCode.

Uso:
    python3 scripts/audit_exercise_cli.py <ruta_al_ejercicio.md>
"""

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from study_engine.pedagogy.submission_reader import SubmissionReader
from study_engine.pedagogy.auditors.programming_auditor import ProgrammingExerciseAuditor
from study_engine.pedagogy.auditors.so_auditor import SOExerciseAuditor
from study_engine.pedagogy.auditors.telecom_auditor import TelecomExerciseAuditor
from study_engine.pedagogy.auditors.fadena_auditor import FADENAExerciseAuditor
from study_engine.student.storage import StudentStorage
from study_engine.student.bkt_tracker import BKTTracker

AUDITORS = {
    "PROGRAMMING": ProgrammingExerciseAuditor,
    "SO": SOExerciseAuditor,
    "TELECOM": TelecomExerciseAuditor,
    "FADENA": FADENAExerciseAuditor,
}

def main():
    parser = argparse.ArgumentParser(description="Auditor Forense TALOS para VSCode")
    parser.add_argument("file", help="Ruta al archivo Markdown del ejercicio")
    args = parser.parse_args()

    file_path = Path(args.file).resolve()
    if not file_path.exists():
        print(f"\033[91m[ERROR]\033[0m El archivo no existe: {file_path}")
        sys.exit(1)

    if not file_path.name.endswith(".md"):
        print(f"\033[93m[AVISO]\033[0m El archivo debe ser un cuaderno Markdown de ejercicio (.md): {file_path.name}")
        sys.exit(1)

    print(f"\033[96m======================================================================\033[0m")
    print(f"\033[96m🏛️  TALOS / KASIU AUDITOR FORENSE DETERMINISTA\033[0m")
    print(f"Archivo: \033[1m{file_path.name}\033[0m")
    print(f"Ruta:    {file_path}")
    print(f"\033[96m======================================================================\033[0m")

    # 1. Leer y parsear sumisión
    reader = SubmissionReader()
    try:
        submission = reader.parse(file_path)
    except Exception as e:
        print(f"\033[91m[ERROR AL PARSEAR]\033[0m {e}")
        sys.exit(1)

    # 2. Conectar BKT Tracker
    db_path = REPO_ROOT / "data" / "web_state" / "student_state.db"
    storage = StudentStorage(db_path=db_path)
    bkt = BKTTracker(storage=storage)

    # 3. Determinar auditor e instanciarlo con bkt_tracker
    ex_type = submission.metadata.get("exercise_type", "PROGRAMMING").upper()
    auditor_cls = AUDITORS.get(ex_type, ProgrammingExerciseAuditor)
    auditor = auditor_cls(bkt_tracker=bkt)

    # 4. Auditar
    result = auditor.audit(submission)

    # 5. Guardar reporte
    reports_dir = REPO_ROOT / "data" / "student_submissions" / ".reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_file = reports_dir / f"{file_path.stem}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    # 6. Salida visual de terminal
    status_color = "\033[92m" if result.passed else "\033[91m"
    status_icon = "✅" if result.passed else "❌"
    status_text = "APROBADO" if result.passed else "REQUIERE REVISIÓN"

    print(f"\nResultado:     {status_icon} {status_color}\033[1m{status_text}\033[0m")
    print(f"Calificación:  \033[1m{result.score:.1f} / 100\033[0m")
    print(f"Tipo Evaluado: {ex_type}")
    print(f"KC Asociado:   {submission.metadata.get('kc_id') or 'No especificado'}")

    print(f"\n\033[94m--- Desglose de Verificaciones Forenses ---\033[0m")
    for chk in result.checks:
        chk_icon = "✅" if chk.passed else ("⚠️" if chk.severity == "WARNING" else "❌")
        chk_color = "\033[92m" if chk.passed else ("\033[93m" if chk.severity == "WARNING" else "\033[91m")
        print(f"  {chk_icon} {chk_color}{chk.name:<26}\033[0m: {chk.feedback}")

    if result.observations:
        print(f"\n\033[93m--- Observaciones y Dictamen Pedagógico ---\033[0m")
        for obs in result.observations:
            print(f"  • {obs}")

    kc_id = submission.metadata.get("kc_id")
    if kc_id and result.bkt_updated:
        print(f"\n\033[95m--- Estado Cognitivo BKT (Actualizado en Base de Datos) ---\033[0m")
        print(f"  Dominio de Conocimiento: \033[1m{kc_id}\033[0m")
        print(f"  Probabilidad de Maestría: \033[1m{result.p_L_before:.4f} → {result.p_L_after:.4f}\033[0m")

    print(f"\n\033[92mReporte forense guardado en: {report_file.relative_to(REPO_ROOT)}\033[0m")
    print(f"\033[96m======================================================================\033[0m\n")

if __name__ == "__main__":
    main()
