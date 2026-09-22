"""FastAPI router for sovereign Notebook queries (Domain Distribution & Epistemic Stats)."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field
import pymupdf

from study_engine.utils.pdf_utils import extract_pdf_cover, save_and_hash_uploaded_pdf, validate_and_hash_pdf
from study_engine.web.dependencies import AppContainer, get_container

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notebook", tags=["Notebook"])


@router.get("/{notebook_id}/domain-distribution")
def get_notebook_domain_distribution(
    notebook_id: str,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Retorna la distribución de dominios/KCs en el notebook, calculada desde los chunks indexados.
    
    Enriquece cada entrada con display_name y unidad curricular desde el catálogo JSON.
    """
    clean_id = notebook_id.strip()

    # 1. Verificar si el notebook existe en federation o en el catálogo pedagógico
    is_known = False
    if hasattr(container.notebook_registry, "get_notebook"):
        nb = container.notebook_registry.get_notebook(clean_id)
        if nb:
            is_known = True

    catalog = getattr(container.pedagogical_orchestrator, "_kc_catalog", {})
    if not is_known and clean_id in catalog:
        is_known = True

    if not is_known:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notebook '{clean_id}' not found in sovereign registry.",
        )

    # 2. Calcular distribución desde KnowledgeStore
    source_distribution = container.knowledge_store.compute_domain_distribution(clean_id)
    total_chunks = sum(d["chunk_count"] for d in source_distribution)

    # 3. Enriquecer con KCs y display names desde el catálogo
    nb_catalog_entry = catalog.get(clean_id, {})
    kcs = nb_catalog_entry.get("kcs", [])

    distribution_items: List[Dict[str, Any]] = []

    if kcs:
        kc_counts = container.knowledge_store.compute_domain_distribution(clean_id, kcs=kcs)
        raw_total = sum(item["chunk_count"] for item in kc_counts)
        effective_total = raw_total if raw_total > 0 else total_chunks

        for kc in kcs:
            kc_id = kc.get("kc_id", "")
            display_name = kc.get("display_name") or kc.get("title") or kc_id
            unit_val = kc.get("unit", "")
            unit_str = f"Unidad {unit_val}" if isinstance(unit_val, int) else str(unit_val)

            matched = next((item["chunk_count"] for item in kc_counts if item["kc_id"] == kc_id), 0)
            percentage = round((matched / effective_total) * 100, 1) if effective_total > 0 else 0.0

            distribution_items.append({
                "kc_id": kc_id,
                "kc_display_name": display_name,
                "unit": unit_str,
                "chunk_count": matched,
                "percentage": percentage,
            })
        if raw_total > 0:
            total_chunks = raw_total
    else:
        # Fallback si no hay catálogo de KCs explícito para este notebook
        for item in source_distribution:
            s_id = item["source_id"]
            chunk_count = item["chunk_count"]
            percentage = round((chunk_count / total_chunks) * 100, 1) if total_chunks > 0 else 0.0
            distribution_items.append({
                "kc_id": s_id,
                "kc_display_name": s_id,
                "unit": "General",
                "chunk_count": chunk_count,
                "percentage": percentage,
            })

    return {
        "notebook_id": clean_id,
        "total_chunks": total_chunks,
        "distribution": distribution_items,
    }


@router.get("/{notebook_id}/sources")
def get_notebook_sources(
    notebook_id: str,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Retorna la lista detallada de fuentes indexadas para este cuaderno."""
    clean_id = notebook_id.strip()
    sources = container.knowledge_store.get_notebook_sources_detailed(clean_id)
    return {
        "notebook_id": clean_id,
        "total_sources": len(sources),
        "sources": sources,
    }


@router.post("/{notebook_id}/upload-source")
async def upload_source_to_notebook(
    notebook_id: str,
    file: UploadFile = File(...),
    title: Optional[str] = Form(default=None),
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Sube un documento PDF, lo indexa y lo asocia automáticamente al cuaderno."""
    clean_id = notebook_id.strip()
    filename = file.filename or "documento.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se admiten documentos en formato .pdf",
        )

    # Directorio de almacenamiento
    base_storage = Path(__file__).resolve().parents[4] / "kasiu-lab" / "storage"
    sources_dir = base_storage / "sources"
    covers_dir = base_storage / "covers"
    sources_dir.mkdir(parents=True, exist_ok=True)
    covers_dir.mkdir(parents=True, exist_ok=True)

    try:
        doc_hash, final_pdf = await save_and_hash_uploaded_pdf(file, sources_dir)
        page_count, cover_path = extract_pdf_cover(final_pdf, covers_dir, doc_hash)
        doc = pymupdf.open(str(final_pdf))

        # Extraer texto básico por página y generar fragmentos/chunks
        source_id = f"src_{doc_hash[:16]}"
        display_title = title.strip() if title and title.strip() else filename.replace(".pdf", "")

        store = container.knowledge_store
        with store.engine.transaction() as conn:
            cursor = conn.cursor()

            # 0. Asegurar que el notebook existe en la tabla notebooks (jo FK de notebook_sources)
            cursor.execute("SELECT id FROM notebooks WHERE id = ?;", (clean_id,))
            if cursor.fetchone() is None:
                folder_id = "folder_root"
                if "fase0" in clean_id:
                    folder_id = "roadmap_fase0"
                elif "fadena" in clean_id:
                    folder_id = "fadena_1ano_2cuat"
                cursor.execute(
                    "INSERT OR IGNORE INTO notebooks (id, name, description, folder_id) VALUES (?, ?, ?, ?);",
                    (clean_id, clean_id, "Cuaderno soberano TALOS", folder_id),
                )

            # 1. Registrar o actualizar en sources con SourceManifest y Source válidos
            file_stat = final_pdf.stat()
            manifest_obj = {
                "source_id": source_id,
                "filename": filename,
                "byte_size": file_stat.st_size,
                "sha256": doc_hash,
                "file_path": str(final_pdf),
                "media_type": "application/pdf",
                "metadata": {
                    "page_count": page_count,
                    "title": display_title,
                },
            }
            manifest_json = json.dumps(manifest_obj)

            source_contract_obj = {
                "source_id": source_id,
                "title": display_title,
                "author": "Cátedra / Usuario",
                "type": "pdf",
                "language": "es",
                "role": "PRIMARY",
                "priority": 1,
                "subject": clean_id,
                "metadata": {
                    "filename": filename,
                    "sha256": doc_hash,
                    "page_count": page_count,
                },
            }
            source_contract_json = json.dumps(source_contract_obj)

            meta_json = json.dumps({
                "filename": filename,
                "sha256": doc_hash,
                "page_count": page_count,
            })
            cursor.execute(
                """
                INSERT OR REPLACE INTO sources (
                    source_id, sha256, manifest_json, source_json, title, author, type, language, role, priority, subject, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    source_id,
                    doc_hash,
                    manifest_json,
                    source_contract_json,
                    display_title,
                    "Cátedra / Usuario",
                    "PDF",
                    "es",
                    "PRIMARY",
                    1,
                    clean_id,
                    meta_json,
                ),
            )

            # 2. Registrar documento padre (FK requerida por chunks.document_id)
            cursor.execute(
                """
                INSERT OR REPLACE INTO documents (
                    id, source_id, title, content, path, page_count, language, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    doc_hash,
                    source_id,
                    display_title,
                    "",
                    str(final_pdf),
                    page_count,
                    "es",
                    meta_json,
                ),
            )

            # 3. Extraer chunks por página e insertarlos
            chunk_count = 0
            for page_num in range(page_count):
                page_text = doc[page_num].get_text().strip()
                if not page_text:
                    continue
                # Fragmentar por párrafos
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

            # 3. Vincular a notebook_sources
            cursor.execute(
                "INSERT OR IGNORE INTO notebook_sources (notebook_id, source_id) VALUES (?, ?);",
                (clean_id, source_id),
            )

        doc.close()

        return {
            "status": "success",
            "notebook_id": clean_id,
            "source_id": source_id,
            "title": display_title,
            "doc_hash": doc_hash,
            "page_count": page_count,
            "chunk_count": chunk_count,
            "filename": filename,
        }

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al indexar material: {str(e)}",
        )
    finally:
        if "doc" in locals() and doc is not None:
            doc.close()


@router.post("/{notebook_id}/sync-sources-folder")
def sync_sources_folder_to_notebook(
    notebook_id: str,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Escanea data/benchmark/sources e indexa/vincula automáticamente los PDFs de la carpeta al cuaderno."""
    clean_id = notebook_id.strip()
    root_dir = Path(__file__).resolve().parents[4]
    nb_sources_dir = root_dir / "data" / "sources" / clean_id
    general_dir = root_dir / "data" / "sources" / "general"
    legacy_dir = root_dir / "data" / "benchmark" / "sources"

    covers_dir = root_dir / "kasiu-lab" / "storage" / "covers"
    covers_dir.mkdir(parents=True, exist_ok=True)

    # Buscar PDFs específicos del cuaderno (recursivo, admitiendo subcarpetas por clase/unidad)
    pdf_files: List[Path] = []
    if nb_sources_dir.exists():
        pdf_files.extend([p for p in nb_sources_dir.rglob("*.pdf") if p.is_file()])

    # Si es fase0 o seguridad transversal, incorporar los libros canónicos de general/
    if clean_id in ("fase0-soc", "NB-CYBERSECURITY-V1") and general_dir.exists():
        pdf_files.extend([p for p in general_dir.rglob("*.pdf") if p.is_file()])

    # fase0-soc es una bóveda completa: hereda también de TODAS las carpetas fadena-*
    if clean_id == "fase0-soc":
        sources_root = root_dir / "data" / "sources"
        if sources_root.exists():
            for subject_dir in sorted(sources_root.iterdir()):
                if subject_dir.is_dir() and subject_dir.name.startswith("fadena-"):
                    pdf_files.extend([p for p in subject_dir.rglob("*.pdf") if p.is_file()])

    if not pdf_files:
        nb_sources_dir.mkdir(parents=True, exist_ok=True)
        return {
            "status": "success",
            "notebook_id": clean_id,
            "message": f"Carpeta data/sources/{clean_id}/ vacía. Podés colocar apuntes o PDFs allí.",
            "linked_count": 0,
            "new_indexed_count": 0,
            "total_files": 0,
        }

    store = container.knowledge_store
    linked_count = 0
    new_indexed_count = 0

    with store.engine.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM notebooks WHERE id = ?;", (clean_id,))
        if cursor.fetchone() is None:
            folder_id = "folder_root"
            if "fase0" in clean_id:
                folder_id = "roadmap_fase0"
            elif "fadena" in clean_id:
                folder_id = "fadena_1ano_2cuat"
            cursor.execute(
                "INSERT OR IGNORE INTO notebooks (id, name, description, folder_id) VALUES (?, ?, ?, ?);",
                (clean_id, clean_id, "Cuaderno soberano TALOS", folder_id),
            )

        for pdf_path in pdf_files:
            try:
                doc_hash = validate_and_hash_pdf(pdf_path)
                source_id = f"src_{doc_hash[:16]}"
                filename = pdf_path.name
                display_title = filename.replace(".pdf", "").replace("_", " ")

                cursor.execute("SELECT source_id FROM sources WHERE sha256 = ? OR source_id = ?;", (doc_hash, source_id))
                existing_src = cursor.fetchone()

                if not existing_src:
                    page_count, _ = extract_pdf_cover(pdf_path, covers_dir, doc_hash)
                    doc = pymupdf.open(str(pdf_path))

                    file_stat = pdf_path.stat()
                    manifest_json = json.dumps({
                        "source_id": source_id,
                        "filename": filename,
                        "byte_size": file_stat.st_size,
                        "sha256": doc_hash,
                        "file_path": str(pdf_path),
                        "media_type": "application/pdf",
                        "metadata": {"page_count": page_count, "title": display_title},
                    })
                    source_contract_json = json.dumps({
                        "source_id": source_id,
                        "title": display_title,
                        "author": "Cátedra / Autor",
                        "type": "pdf",
                        "language": "es",
                        "role": "PRIMARY",
                        "priority": 1,
                        "subject": clean_id,
                        "metadata": {"filename": filename, "sha256": doc_hash, "page_count": page_count},
                    })
                    meta_json = json.dumps({"filename": filename, "sha256": doc_hash, "page_count": page_count})

                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO sources (
                            source_id, sha256, manifest_json, source_json, title, author, type, language, role, priority, subject, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (source_id, doc_hash, manifest_json, source_contract_json, display_title, "Cátedra / Autor", "PDF", "es", "PRIMARY", 1, clean_id, meta_json),
                    )

                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO documents (
                            id, source_id, title, content, path, page_count, language, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (doc_hash, source_id, display_title, "", str(pdf_path), page_count, "es", meta_json),
                    )

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
                                (chunk_id, doc_hash, source_id, para, page_num + 1, page_num + 1, f"Página {page_num+1}", f"Sección {p_idx+1}", len(para.split()), chunk_count, "{}"),
                            )
                            chunk_count += 1

                    doc.close()
                    new_indexed_count += 1
                else:
                    source_id = existing_src[0]

                cursor.execute(
                    "SELECT 1 FROM notebook_sources WHERE notebook_id = ? AND source_id = ?;",
                    (clean_id, source_id),
                )
                if cursor.fetchone() is None:
                    cursor.execute(
                        "INSERT OR IGNORE INTO notebook_sources (notebook_id, source_id) VALUES (?, ?);",
                        (clean_id, source_id),
                    )
                    linked_count += 1
            except Exception as item_err:
                print(f"Error procesando {pdf_path.name}: {item_err}")
                continue

    return {
        "status": "success",
        "notebook_id": clean_id,
        "total_files": len(pdf_files),
        "new_indexed_count": new_indexed_count,
        "linked_count": linked_count,
        "message": f"Sincronización completada: {linked_count} fuentes vinculadas, {new_indexed_count} nuevas indexadas.",
    }


@router.get("/{notebook_id}/curriculum-progress")
def get_curriculum_progress(
    notebook_id: str,
    session_id: Optional[str] = None,
    container: AppContainer = Depends(get_container),
) -> List[Dict[str, Any]]:
    """Retorna el progreso por unidad y subtema del programa curricular oficial."""
    clean_id = notebook_id.strip()

    # 1. Cargar catálogo de KCs para este notebook
    catalog = getattr(container.pedagogical_orchestrator, "_kc_catalog", {})
    if not catalog:
        kc_path = Path("config/notebook_kc_catalog.json")
        if kc_path.exists():
            try:
                catalog = json.loads(kc_path.read_text(encoding="utf-8"))
            except Exception:
                catalog = {}

    nb_entry = catalog.get(clean_id, {})
    kcs = nb_entry.get("kcs", [])

    # 2. Consultar estados BKT de student_storage
    bkt_map: Dict[str, Any] = {}
    if hasattr(container, "student_storage") and container.student_storage:
        try:
            bkt_states = container.student_storage.list_bkt_states()
            for b in bkt_states:
                bkt_map[b.kc_id] = b
        except Exception:
            pass

    # 3. Consultar tabla curriculum_progress
    tracked_map: Dict[str, Dict[str, Any]] = {}
    if hasattr(container, "student_storage") and container.student_storage:
        try:
            conn = container.student_storage._get_connection()
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS curriculum_progress (
                        notebook_id TEXT NOT NULL,
                        kc_id TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        evidence_count INTEGER NOT NULL DEFAULT 0,
                        last_updated TEXT NOT NULL,
                        PRIMARY KEY (notebook_id, kc_id)
                    );
                    """
                )
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT kc_id, status, evidence_count FROM curriculum_progress WHERE notebook_id = ?;",
                    (clean_id,),
                )
                for r in cursor.fetchall():
                    tracked_map[r[0]] = {"status": r[1], "evidence_count": r[2]}
        except Exception:
            pass

    # 4. Agrupar por unidades temáticas
    units_dict: Dict[str, Dict[str, Any]] = {}

    for kc in kcs:
        kc_id = kc.get("kc_id", "")
        title = kc.get("display_name") or kc.get("title") or kc_id
        unit_val = kc.get("unit", 1)
        unit_label = f"Unidad {unit_val}" if isinstance(unit_val, int) else str(unit_val)

        # Estado cognitivo BKT
        bkt = bkt_map.get(kc_id)
        p_L = getattr(bkt, "p_L", 0.0) if bkt else 0.0
        attempts = getattr(bkt, "attempts", 0) if bkt else 0

        # Determinar estado: tracked -> BKT -> pending
        tr = tracked_map.get(kc_id)
        if tr:
            status_val = tr["status"]
            ev_count = tr["evidence_count"]
        elif attempts > 0 and p_L >= 0.85:
            status_val = "mastered"
            ev_count = max(1, attempts)
        elif attempts > 0 or p_L > 0.3:
            status_val = "covered"
            ev_count = max(1, attempts)
        else:
            status_val = "pending"
            ev_count = 0

        if unit_label not in units_dict:
            units_dict[unit_label] = {
                "unit": unit_label,
                "unit_name": title,
                "subtopics": [],
            }

        subtopics_list = kc.get("subtopics", [])
        if subtopics_list:
            for idx, st_item in enumerate(subtopics_list):
                st_name = st_item if isinstance(st_item, str) else st_item.get("name", str(st_item))
                st_id = f"{kc_id}_st_{idx+1}"
                sub_tr = tracked_map.get(st_id)
                sub_status = sub_tr["status"] if sub_tr else status_val
                sub_ev = sub_tr["evidence_count"] if sub_tr else ev_count
                units_dict[unit_label]["subtopics"].append({
                    "id": st_id,
                    "name": st_name,
                    "status": sub_status,
                    "evidence_count": sub_ev,
                })
        else:
            units_dict[unit_label]["subtopics"].append({
                "id": kc_id,
                "name": title,
                "status": status_val,
                "evidence_count": ev_count,
            })

    if not units_dict:
        units_dict["Unidad 1"] = {
            "unit": "Unidad 1",
            "unit_name": "Fundamentos y Contenidos Doctrinales",
            "subtopics": [
                {
                    "id": f"{clean_id}_general",
                    "name": "Conceptos Generales del Cuaderno",
                    "status": "pending",
                    "evidence_count": 0,
                }
            ],
        }

    return list(units_dict.values())



# ---------------------------------------------------------------------------
# Fase 5.1 — Administración manual del syllabus (KCs) y currícula por cuaderno
# (rutas plurales dedicadas, independientes del router /api/notebook)
# ---------------------------------------------------------------------------

admin_router = APIRouter(prefix="/api/notebooks", tags=["Curriculum Admin"])


class KCCreatePayload(BaseModel):
    """Payload para alta manual de un Knowledge Component."""

    model_config = ConfigDict(strict=True)

    kc_id: str = Field(..., min_length=3, max_length=64, description="Identificador estable del KC (slug).")
    title: str = Field(..., min_length=3, max_length=200)
    prerequisites: Optional[List[str]] = Field(default=None)
    subtopics: Optional[List[str]] = Field(default=None)
    estimated_time: Optional[int] = Field(default=None, ge=5, le=600, description="Minutos estimados.")
    difficulty: Optional[str] = Field(default=None, description="basico|intermedio|avanzado")


def _kc_effective_kcs(container: AppContainer, notebook_id: str) -> List[Dict[str, Any]]:
    """Catálogo efectivo del cuaderno (JSON canónico + KCs manuales ya fundidos)."""
    catalog = getattr(container.pedagogical_orchestrator, "_kc_catalog", {})
    entry = catalog.get(notebook_id, {}) if isinstance(catalog, dict) else {}
    kcs = entry.get("kcs", []) if isinstance(entry, dict) else []
    return kcs if isinstance(kcs, list) else []


def _kc_status(container: AppContainer, notebook_id: str, kc_id: str) -> str:
    """Estado del KC: mastered (p_L>=0.8) / in_progress (p_L>=0.4) / not_started.

    El umbral refleja el criterio BKT ya usado por el curriculum view; es una
    lectura derivada del tracker, no una mutación.
    """
    try:
        p_l = container.bkt_tracker.get_state(kc_id).p_L
    except Exception:
        return "not_started"
    if p_l >= 0.8:
        return "mastered"
    if p_l >= 0.4:
        return "in_progress"
    return "not_started"


@admin_router.get("/{notebook_id}/curriculum")
def get_notebook_curriculum(
    notebook_id: str,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Lista los KCs del cuaderno (JSON canónico + manuales). Lista vacía si no hay."""
    clean_id = notebook_id.strip()
    kcs = _kc_effective_kcs(container, clean_id)
    return {
        "notebook_id": clean_id,
        "total": len(kcs),
        "kcs": [
            {
                "kc_id": k.get("kc_id"),
                "title": k.get("title") or k.get("display_name") or k.get("kc_id"),
                "prerequisites": k.get("prerequisites") or [],
                "estimated_time": k.get("estimated_time"),
                "difficulty": k.get("difficulty"),
                "status": _kc_status(container, clean_id, k.get("kc_id", "")),
            }
            for k in kcs
        ],
    }


@admin_router.post("/{notebook_id}/knowledge-components", status_code=status.HTTP_201_CREATED)
def create_knowledge_component(
    notebook_id: str,
    payload: KCCreatePayload,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Alta manual de KC: valida duplicados, persiste y refresca el catálogo en memoria."""
    clean_id = notebook_id.strip()
    if not container.knowledge_store.contains_notebook(clean_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notebook '{clean_id}' no existe.",
        )

    from study_engine.curriculum.kc_admin import DuplicateKCError

    existing = _kc_effective_kcs(container, clean_id)
    try:
        rec = container.kc_admin.add_kc(
            notebook_id=clean_id,
            kc_id=payload.kc_id,
            title=payload.title,
            prerequisites=payload.prerequisites,
            subtopics=payload.subtopics,
            estimated_time=payload.estimated_time,
            difficulty=payload.difficulty,
            existing_kcs=existing,
        )
    except DuplicateKCError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    # Invalidar el catálogo cacheado en memoria: el matcher de BKT (chat) y el
    # curriculum view ven el KC nuevo sin reiniciar. BKT por KC no guarda caché
    # propia — el estado BKT del KC nuevo arranca en p_L0 como corresponde.
    catalog = getattr(container.pedagogical_orchestrator, "_kc_catalog", None)
    if isinstance(catalog, dict):
        entry = catalog.setdefault(clean_id, {"kcs": []})
        if isinstance(entry.get("kcs"), list) and all(
            k.get("kc_id") != rec["kc_id"] for k in entry["kcs"]
        ):
            entry["kcs"].append(rec)
    logger.info("KC manual creado: notebook=%s kc_id=%s", clean_id, rec["kc_id"])
    return rec
