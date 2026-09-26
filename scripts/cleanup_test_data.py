#!/usr/bin/env python3
"""cleanup_test_data.py — Limpia el estado del estudiante en student_state.db.

Borra datos de las tablas de estado cognitivo y memoria para comenzar
una sesión limpia de pruebas. NO toca knowledge_store.db (fuentes, chunks, KCs).

Tablas limpiadas:
  - bkt_states               (estado BKT por KC)
  - anchor_states            (SM-2 spaced repetition)
  - remediation_choices      (decisiones de remediación)
  - student_hints            (historial de pistas pedidas)
  - student_pedagogical_memory (memoria pedagógica legacy)
  - student_cognitive_profile  (Perfil Cognitivo Dinámico — Opción C)
  - session_records          (historial de sesiones)
  - session_digests          (resúmenes de sesión)
  - session_kc_activity      (actividad de KCs por sesión)
  - generated_exercises      (ejercicios generados en sesión)
  - solution_access_log      (log de acceso a soluciones)
  - student_exercise_attempts (intentos de ejercicios)
  - curriculum_progress      (progreso curricular)

Uso:
    PYTHONPATH=src .venv/bin/python scripts/cleanup_test_data.py

    # Con confirmación desactivada (modo CI/CD):
    PYTHONPATH=src .venv/bin/python scripts/cleanup_test_data.py --no-confirm
"""

import argparse
import sqlite3
import sys
from pathlib import Path

DB_PATHS = [
    Path("data/student/student_state.db"),
    Path("data/web_state/student_state.db"),
]

TABLES_TO_CLEAN = [
    "bkt_states",
    "anchor_states",
    "remediation_choices",
    "student_hints",
    "student_pedagogical_memory",
    "student_cognitive_profile",
    "session_records",
    "session_digests",
    "session_kc_activity",
    "generated_exercises",
    "solution_access_log",
    "student_exercise_attempts",
    "curriculum_progress",
]


def get_existing_tables(conn: sqlite3.Connection) -> set:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    return {row[0] for row in cur.fetchall()}


def clean_db(db_path: Path) -> dict:
    if not db_path.exists():
        print(f"  ⏭️  {db_path} — no existe, skipping.")
        return {}

    conn = sqlite3.connect(str(db_path))
    existing = get_existing_tables(conn)
    counts = {}

    with conn:
        for table in TABLES_TO_CLEAN:
            if table not in existing:
                continue
            cur = conn.execute(f"SELECT COUNT(*) FROM {table}")
            n = cur.fetchone()[0]
            conn.execute(f"DELETE FROM {table}")
            counts[table] = n
            print(f"    🗑️  {table}: {n} filas eliminadas")

    conn.close()
    return counts


def main():
    parser = argparse.ArgumentParser(description="Limpia estado de estudiante en student_state.db")
    parser.add_argument("--no-confirm", action="store_true", help="Ejecuta sin confirmación interactiva")
    args = parser.parse_args()

    print("\n🔧 TALOS — Cleanup de Estado de Estudiante")
    print("=" * 55)
    print("Bases de datos a limpiar:")
    for p in DB_PATHS:
        status = "✅ existe" if p.exists() else "⚠️  no existe"
        print(f"  {status} — {p}")

    if not args.no_confirm:
        confirm = input("\n¿Confirmar limpieza? (s/n): ").strip().lower()
        if confirm not in ("s", "si", "y", "yes"):
            print("❌ Cancelado.")
            sys.exit(0)

    total_rows = 0
    for db_path in DB_PATHS:
        print(f"\n📂 {db_path}:")
        counts = clean_db(db_path)
        total_rows += sum(counts.values())

    print(f"\n✅ Limpieza completada. Total de filas eliminadas: {total_rows}")
    print("   El estado del estudiante ha sido reseteado a cero.")
    print("   Las fuentes, chunks y KCs de knowledge_store.db permanecen intactos.\n")


if __name__ == "__main__":
    main()
