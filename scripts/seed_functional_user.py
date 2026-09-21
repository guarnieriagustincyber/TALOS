#!/usr/bin/env python3
"""
Seed script para crear usuario funcional de prueba en TALOS
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))

from study_engine.storage.sqlite_engine import SQLiteStorageEngine


def ensure_user_tables(conn: sqlite3.Connection) -> None:
    """Crea las tablas para el usuario funcional si no existen."""
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS student_profiles (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            timezone TEXT NOT NULL,
            preferences_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS student_progress (
            student_id TEXT NOT NULL,
            notebook_id TEXT NOT NULL,
            completed_nodes_json TEXT NOT NULL,
            current_node TEXT NOT NULL,
            mastery_percentage REAL NOT NULL,
            study_hours REAL NOT NULL,
            last_session TEXT,
            PRIMARY KEY (student_id, notebook_id)
        );

        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            message_count INTEGER NOT NULL,
            notes_saved INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS student_notes (
            note_id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            node_id TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS kanban_tasks (
            task_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            priority TEXT NOT NULL,
            notebook_id TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS calendar_events (
            event_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            notebook_id TEXT NOT NULL
        );
    """)
    conn.commit()


class FunctionalUserSeeder:
    """Persiste los datos del estudiante de prueba en SQLite."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage = SQLiteStorageEngine(db_path=self.db_path)
        with self.storage.transaction() as conn:
            ensure_user_tables(conn)

    def save_student_profile(self, profile: dict) -> None:
        with self.storage.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO student_profiles (student_id, name, email, timezone, preferences_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    profile["student_id"],
                    profile["name"],
                    profile["email"],
                    profile["timezone"],
                    json.dumps(profile.get("preferences", {})),
                    profile["created_at"],
                ),
            )

    def save_student_progress(self, progress: dict) -> None:
        with self.storage.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO student_progress
                (student_id, notebook_id, completed_nodes_json, current_node, mastery_percentage, study_hours, last_session)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    progress["student_id"],
                    progress["notebook_id"],
                    json.dumps(progress["completed_nodes"]),
                    progress["current_node"],
                    float(progress["mastery_percentage"]),
                    float(progress["study_hours"]),
                    progress.get("last_session", datetime.now(timezone.utc).isoformat()),
                ),
            )

    def save_chat_session(self, session: dict) -> None:
        with self.storage.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO chat_sessions (session_id, topic, message_count, notes_saved, created_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    session["session_id"],
                    session["topic"],
                    session["message_count"],
                    session["notes_saved"],
                    session["created_at"],
                ),
            )

    def save_note(self, note: dict) -> None:
        with self.storage.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO student_notes (note_id, content, node_id, created_at)
                VALUES (?, ?, ?, ?);
                """,
                (
                    note["note_id"],
                    note["content"],
                    note.get("node_id"),
                    note["created_at"],
                ),
            )

    def save_task(self, task: dict) -> None:
        with self.storage.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO kanban_tasks (task_id, title, status, priority, notebook_id)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    task["task_id"],
                    task["title"],
                    task["status"],
                    task["priority"],
                    task["notebook_id"],
                ),
            )

    def save_calendar_event(self, event: dict) -> None:
        with self.storage.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO calendar_events (event_id, title, date, type, notebook_id)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    event["event_id"],
                    event["title"],
                    event["date"],
                    event["type"],
                    event["notebook_id"],
                ),
            )


def seed_database_with_user(db_path: Path) -> None:
    """Ejecuta el seed del usuario funcional sobre la ruta dada."""
    seeder = FunctionalUserSeeder(db_path)
    now = datetime.now(timezone.utc)

    # 1. Crear perfil de estudiante
    print("  ✓ Creando perfil: Agustín (Test)")
    student_profile = {
        "student_id": "student_agustin_test",
        "name": "Agustín (Test)",
        "email": "agustin.test@talos.local",
        "created_at": now.isoformat(),
        "timezone": "America/Argentina/Buenos_Aires",
        "preferences": {
            "theme": "dark",
            "language": "es-AR",
            "notifications_enabled": True,
        },
    }
    seeder.save_student_profile(student_profile)

    # 2. Crear progreso en cuaderno
    print("  ✓ Configurando progreso en Programación Básica")
    progress = {
        "student_id": "student_agustin_test",
        "notebook_id": "nb_prog_basica",
        "completed_nodes": ["node_variables", "node_control"],
        "current_node": "node_functions",
        "mastery_percentage": 65,
        "study_hours": 12.5,
        "last_session": (now - timedelta(hours=3)).isoformat(),
    }
    seeder.save_student_progress(progress)

    # 3. Crear historial de conversaciones (3 sesiones previas)
    print("  ✓ Creando 3 sesiones de chat previas")
    sessions = [
        {
            "session_id": "sess_001",
            "topic": "Variables y tipos de datos",
            "message_count": 5,
            "notes_saved": 2,
            "created_at": (now - timedelta(days=5)).isoformat(),
        },
        {
            "session_id": "sess_002",
            "topic": "Estructuras de control",
            "message_count": 8,
            "notes_saved": 3,
            "created_at": (now - timedelta(days=3)).isoformat(),
        },
        {
            "session_id": "sess_003",
            "topic": "Funciones básicas",
            "message_count": 3,
            "notes_saved": 0,
            "created_at": (now - timedelta(days=1)).isoformat(),
        },
    ]
    for session in sessions:
        seeder.save_chat_session(session)

    # 4. Crear notas ancladas (5 notas realistas)
    print("  ✓ Creando 5 notas ancladas")
    notes = [
        {
            "note_id": "note_001",
            "content": "Las variables son contenedores de datos en memoria RAM. Cada variable tiene un nombre, un tipo y un valor.",
            "node_id": "node_variables",
            "created_at": (now - timedelta(days=5)).isoformat(),
        },
        {
            "note_id": "note_002",
            "content": "if/elif/else = estructura de decisión secuencial. Siempre evaluar de arriba hacia abajo.",
            "node_id": "node_control",
            "created_at": (now - timedelta(days=3)).isoformat(),
        },
        {
            "note_id": "note_003",
            "content": "Las funciones deben tener UN solo propósito (Clean Code). Si hace más de una cosa, dividirla.",
            "node_id": "node_functions",
            "created_at": (now - timedelta(days=1)).isoformat(),
        },
        {
            "note_id": "note_004",
            "content": "Evitar variables globales. Usar parámetros y return para comunicación entre funciones.",
            "node_id": "node_functions",
            "created_at": (now - timedelta(days=1)).isoformat(),
        },
        {
            "note_id": "note_005",
            "content": "Siempre documentar con docstrings. Explicar QUÉ hace, no CÓMO lo hace.",
            "node_id": "node_functions",
            "created_at": (now - timedelta(hours=2)).isoformat(),
        },
    ]
    for note in notes:
        seeder.save_note(note)

    # 5. Crear tareas en Kanban (4 tareas)
    print("  ✓ Creando 4 tareas en Kanban")
    tasks = [
        {
            "task_id": "task_001",
            "title": "Resolver ejercicio 3.5 del libro",
            "status": "pendiente",
            "priority": "P2",
            "notebook_id": "nb_prog_basica",
        },
        {
            "task_id": "task_002",
            "title": "Implementar validador de IPv4",
            "status": "haciendo",
            "priority": "P1",
            "notebook_id": "nb_prog_basica",
        },
        {
            "task_id": "task_003",
            "title": "Completar capítulo 2",
            "status": "finalizada",
            "priority": "P2",
            "notebook_id": "nb_prog_basica",
        },
        {
            "task_id": "task_004",
            "title": "Estudiar punteros (capítulo 5)",
            "status": "futuro",
            "priority": "P3",
            "notebook_id": "nb_prog_basica",
        },
    ]
    for task in tasks:
        seeder.save_task(task)

    # 6. Crear eventos en calendario (2 eventos)
    print("  ✓ Creando 2 eventos en calendario")
    events = [
        {
            "event_id": "event_001",
            "title": "Parcial Programación",
            "date": "2026-02-15",
            "type": "examen",
            "notebook_id": "nb_prog_basica",
        },
        {
            "event_id": "event_002",
            "title": "Entrega Proyecto Final",
            "date": "2026-03-01",
            "type": "entrega",
            "notebook_id": "nb_prog_basica",
        },
    ]
    for event in events:
        seeder.save_calendar_event(event)


def seed_functional_user() -> None:
    """Crea un usuario funcional con datos realistas en los almacenes SQLite."""
    print("=" * 60)
    print("👤 Creando usuario funcional de prueba en TALOS...")
    print("=" * 60)

    # Hidratar ambos almacenes: web_state y raíz
    web_db = ROOT_DIR / "data" / "web_state" / "knowledge_store.db"
    talos_db = ROOT_DIR / "data" / "talos.db"

    print(f"\n[1/2] Hidratando usuario en: {web_db}")
    seed_database_with_user(web_db)

    print(f"\n[2/2] Hidratando usuario en: {talos_db}")
    seed_database_with_user(talos_db)

    print("\n" + "=" * 60)
    print("✅ Usuario funcional creado exitosamente!")
    print("=" * 60)
    print("\n📊 Resumen:")
    print("  - 1 perfil de estudiante")
    print("  - Progreso: 65% completado (2/3 nodos en 'Programación Básica')")
    print("  - 3 sesiones de chat previas")
    print("  - 5 notas ancladas")
    print("  - 4 tareas en Kanban")
    print("  - 2 eventos en calendario")
    print("\n💡 Credenciales de prueba:")
    print("  Email: agustin.test@talos.local")
    print("  (Sin contraseña - acceso directo)\n")


if __name__ == "__main__":
    seed_functional_user()
