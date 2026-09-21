#!/usr/bin/env python3
"""
Sincronizador automático de fuentes locales por cuaderno para TALOS.

Recorre la carpeta `fuentes/<cuaderno_id>/` e indexa/asocia automáticamente
cualquier archivo PDF nuevo al cuaderno correspondiente en el KnowledgeStore.
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "src"))

try:
    import pymupdf
except ImportError:
    print("❌ Error: pymupdf no está instalado en el entorno virtual.")
    sys.exit(1)

from study_engine.web.dependencies import get_container


def sync_all_folders() -> None:
    fuentes_dir = ROOT_DIR / "fuentes"
    if not fuentes_dir.exists():
        print(f"📁 Creando carpeta raíz de fuentes: {fuentes_dir}")
        fuentes_dir.mkdir(parents=True, exist_ok=True)

    container = get_container()
    store = container.knowledge_store
    base_storage = ROOT_DIR / "kasiu-lab" / "storage"
    sources_dir = base_storage / "sources"
    covers_dir = base_storage / "covers"
    sources_dir.mkdir(parents=True, exist_ok=True)
    covers_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("📚 TALOS - Sincronizador de Fuentes por Cuaderno")
    print("=" * 60)

    notebook_dirs = [d for d in fuentes_dir.iterdir() if d.is_dir()]
    if not notebook_dirs:
        print("ℹ️ No se encontraron subcarpetas de cuadernos en fuentes/.")
        return

    total_synced = 0
    for nb_path in sorted(notebook_dirs):
        notebook_id = nb_path.name
        pdf_files = list(nb_path.glob("*.pdf"))
        print(f"\n📂 Cuaderno: [{notebook_id}] ({len(pdf_files)} PDFs)")

        for pdf in pdf_files:
            filename = pdf.name
            try:
                hasher = hashlib.sha256()
                with open(pdf, "rb") as f:
                    while chunk := f.read(1024 * 1024):
                        hasher.update(chunk)
                doc_hash = hasher.hexdigest()

                dest_pdf = sources_dir / f"{doc_hash}.pdf"
                if not dest_pdf.exists():
                    shutil.copy2(pdf, dest_pdf)

                cover_path = covers_dir / f"{doc_hash}.webp"
                doc = pymupdf.open(str(dest_pdf))
                page_count = len(doc)
                if page_count > 0 and not cover_path.exists():
                    try:
                        first_page = doc.load_page(0)
                        pix = first_page.get_pixmap(dpi=120)
                        pix.save(str(cover_path), output="webp")
                    except Exception:
                        pass

                # Verificar si ya existe una fuente canónica para este hash SHA-256
                with store.engine.transaction() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT source_id, title FROM sources WHERE sha256 = ? LIMIT 1;", (doc_hash,))
                    existing_source = cursor.fetchone()

                if existing_source:
                    source_id = existing_source[0]
                    display_title = existing_source[1]
                else:
                    source_id = f"src_{doc_hash[:16]}"
                    display_title = filename.replace(".pdf", "")

                file_size = dest_pdf.stat().st_size
                manifest_obj = {
                    "source_id": source_id,
                    "filename": filename,
                    "byte_size": file_size,
                    "sha256": doc_hash,
                    "file_path": str(dest_pdf),
                    "media_type": "application/pdf",
                    "metadata": {"page_count": page_count, "title": display_title},
                }
                source_contract_obj = {
                    "source_id": source_id,
                    "title": display_title,
                    "author": "Cátedra / Usuario",
                    "type": "pdf",
                    "language": "es",
                    "role": "PRIMARY",
                    "priority": 1,
                    "subject": notebook_id,
                    "metadata": {"filename": filename, "sha256": doc_hash, "page_count": page_count},
                }
                meta_json = json.dumps({"filename": filename, "sha256": doc_hash, "page_count": page_count})

                with store.engine.transaction() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM notebooks WHERE id = ?;", (notebook_id,))
                    if cursor.fetchone() is None:
                        cursor.execute(
                            "INSERT OR IGNORE INTO notebooks (id, name, description, folder_id) VALUES (?, ?, ?, ?);",
                            (notebook_id, notebook_id, "Cuaderno soberano TALOS", "folder_root"),
                        )

                    if not existing_source:
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO sources (
                                source_id, sha256, manifest_json, source_json, title, author, type, language, role, priority, subject, metadata
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                            """,
                            (
                                source_id,
                                doc_hash,
                                json.dumps(manifest_obj),
                                json.dumps(source_contract_obj),
                                display_title,
                                "Cátedra / Usuario",
                                "PDF",
                                "es",
                                "PRIMARY",
                                1,
                                notebook_id,
                                meta_json,
                            ),
                        )

                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO documents (
                            id, source_id, title, content, path, page_count, language, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (doc_hash, source_id, display_title, "", str(dest_pdf), page_count, "es", meta_json),
                    )

                    cursor.execute("SELECT count(*) FROM chunks WHERE document_id = ?;", (doc_hash,))
                    existing_chunks = cursor.fetchone()[0]

                    if existing_chunks == 0:
                        chunk_count = 0
                        for page_num in range(page_count):
                            page_text = doc[page_num].get_text().strip()
                            if not page_text:
                                continue
                            paragraphs = [p.strip() for p in page_text.split("\n\n") if len(p.strip()) > 30]
                            if not paragraphs:
                                paragraphs = [page_text]
                            for p_idx, para in enumerate(paragraphs):
                                chunk_id = f"chk_{doc_hash[:12]}_{page_num+1}_{p_idx+1}"
                                cursor.execute(
                                    """
                                    INSERT OR REPLACE INTO chunks (
                                        id, document_id, source_id, content, page_start, page_end, chapter, section, token_count, pos_index, metadata
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                                    """,
                                    (
                                        chunk_id,
                                        doc_hash,
                                        source_id,
                                        para,
                                        page_num + 1,
                                        page_num + 1,
                                        f"Página {page_num+1}",
                                        f"Sección {p_idx+1}",
                                        len(para.split()),
                                        chunk_count,
                                        "{}",
                                    ),
                                )
                                chunk_count += 1

                    cursor.execute(
                        "INSERT OR IGNORE INTO notebook_sources (notebook_id, source_id) VALUES (?, ?);",
                        (notebook_id, source_id),
                    )

                doc.close()
                print(f"  ✅ {filename} sincronizado ({page_count} págs)")
                total_synced += 1
            except Exception as e:
                print(f"  ❌ Error procesando {filename}: {e}")

    print("\n" + "=" * 60)
    print(f"🎉 Sincronización finalizada: {total_synced} documentos listos.")
    print("=" * 60)


if __name__ == "__main__":
    sync_all_folders()
