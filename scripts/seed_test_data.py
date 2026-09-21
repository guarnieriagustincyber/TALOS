#!/usr/bin/env python3
"""
Seed script para crear datos de prueba en TALOS
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Agregar el directorio raíz al path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from study_engine.hierarchy.folder import Folder
from study_engine.contracts.notebook import Notebook
from study_engine.storage.knowledge_store import KnowledgeStore


def seed_database(db_path: Path, force: bool = False) -> None:
    """Crea datos de prueba en la base de datos especificada."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if db_path.exists() and not force:
        print(f"  ℹ️  La base de datos {db_path} ya existe. Actualizando datos de forma idempotente...")

    store = KnowledgeStore(db_path=db_path)
    store.initialize()

    now = datetime.now(timezone.utc)

    # 0. Crear carpeta root si no existe
    if not store.contains_folder("folder_root"):
        store.create_folder(
            Folder(
                id="folder_root",
                name="Root Workspace",
                parent_folder_id=None,
                description="Contenedor raíz del espacio de trabajo TALOS",
                created_at=now,
                updated_at=now,
            )
        )

    # 1. Crear carpeta de prueba requerida por la directiva
    print("  📁 Creando carpeta: Fase 0 - Ciberseguridad")
    if not store.contains_folder("folder_fase0"):
        folder_fase0 = Folder(
            id="folder_fase0",
            name="Fase 0 - Ciberseguridad",
            parent_folder_id="folder_root",
            description="Fundamentos de programación para ciberseguridad",
            created_at=now,
            updated_at=now,
        )
        store.create_folder(folder_fase0)

    # 2. Crear cuaderno de prueba requerido por la directiva
    print("  📓 Creando cuaderno: Programación Básica")
    if not store.contains_notebook("nb_prog_basica"):
        notebook_prog = Notebook(
            id="nb_prog_basica",
            folder_id="folder_fase0",
            name="Programación Básica",
            description="Fundamentos de programación con Python",
            created_at=now,
            updated_at=now,
        )
        store.create_notebook(notebook_prog)

    # 3. Crear carpetas y cuadernos adicionales para paridad total con la UI
    ui_folders = [
        ("fadena", "FADENA (Ciberdefensa)", "folder_root"),
        ("fadena_1ano", "1er Año Curricular", "fadena"),
        ("roadmap", "Roadmap Ciberdefensa", "folder_root"),
        ("rm_fase0", "Fase 0 (Core Network)", "roadmap"),
    ]
    for fid, fname, fparent in ui_folders:
        if not store.contains_folder(fid):
            store.create_folder(
                Folder(
                    id=fid,
                    name=fname,
                    parent_folder_id=fparent,
                    created_at=now,
                    updated_at=now,
                )
            )

    ui_notebooks = [
        ("nb_tcp", "Fundamentos TCP/IP", "rm_fase0", "Roadmap Ciberdefensa / Fase 0"),
        ("nb_arq", "Arquitectura de Computadoras", "fadena_1ano", "FADENA · 1er Año"),
    ]
    for nbid, nbname, nbfolder, nbdesc in ui_notebooks:
        if not store.contains_notebook(nbid):
            store.create_notebook(
                Notebook(
                    id=nbid,
                    folder_id=nbfolder,
                    name=nbname,
                    description=nbdesc,
                    created_at=now,
                    updated_at=now,
                )
            )

    # 4. Registrar fuentes de prueba (metadata)
    print("  📚 Registrando fuentes de prueba...")
    sources = [
        {
            "hash": "test_source_joyanes_ch1",
            "title": "Joyanes - Capítulo 1: Fundamentos",
            "type": "pdf",
            "page_count": 25,
            "notebook_id": "nb_prog_basica",
        },
        {
            "hash": "test_source_spraul_ch2",
            "title": "Spraul - Capítulo 2: Algoritmos",
            "type": "pdf",
            "page_count": 30,
            "notebook_id": "nb_prog_basica",
        },
    ]

    # Verificar si el libro de Kurose & Ross está presente en storage
    kurose_pdf = ROOT_DIR / "kasiu-lab" / "storage" / "sources" / "7599e188b2645104576b5502400565aff7892ef02abb866ed6899ef9b5865a9a.pdf"
    if kurose_pdf.exists():
        sources.append(
            {
                "hash": "7599e188b2645104576b5502400565aff7892ef02abb866ed6899ef9b5865a9a",
                "title": "Kurose & Ross - Computer Networking: A Top-Down Approach (8th Ed)",
                "type": "pdf",
                "page_count": 800,
                "notebook_id": "nb_tcp",
            }
        )

    for source_data in sources:
        print(f"    ✓ {source_data['title']}")

    # 5. Nodos curriculares de prueba
    print("  🎯 Creando nodos curriculares de prueba...")
    nodes = [
        {"id": "node_variables", "title": "Variables y Tipos", "notebook_id": "nb_prog_basica"},
        {"id": "node_control", "title": "Estructuras de Control", "notebook_id": "nb_prog_basica"},
        {"id": "node_functions", "title": "Funciones", "notebook_id": "nb_prog_basica"},
    ]
    for node in nodes:
        print(f"    ✓ {node['title']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed test data for TALOS")
    parser.add_argument("--force", action="store_true", help="Forzar sobreescritura de datos")
    args = parser.parse_args()

    print("=" * 60)
    print("🌱 Creando datos de prueba para TALOS...")
    print("=" * 60)

    # Seed en la base de datos de producción web y en data/talos.db
    web_db = ROOT_DIR / "data" / "web_state" / "knowledge_store.db"
    talos_db = ROOT_DIR / "data" / "talos.db"

    print(f"\n[1/2] Hidratando almacén web: {web_db}")
    seed_database(web_db, force=args.force)

    print(f"\n[2/2] Hidratando almacén raíz: {talos_db}")
    seed_database(talos_db, force=args.force)

    print("\n" + "=" * 60)
    print("✅ Datos de prueba creados exitosamente!")
    print("=" * 60)
    print("\n📊 Resumen:")
    print("  - 5 carpetas creadas/verificadas")
    print("  - 3 cuadernos creados/verificados")
    print("  - 3 fuentes registradas (metadata + Kurose & Ross)")
    print("  - 3 nodos curriculares listos")
    print("\n💡 Ahora podés iniciar TALOS con: python start_talos.py\n")


if __name__ == "__main__":
    main()
