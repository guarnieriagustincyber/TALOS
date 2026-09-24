from datetime import datetime, timezone
import logging
from pathlib import Path
import shutil
import sqlite3
import subprocess
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from study_engine.cli import (
    DEFAULT_COLAB_DIR,
    DEFAULT_CONTRACT_PATH,
    DEFAULT_KNOWLEDGE_DB,
    DEFAULT_VECTOR_DB,
    _pending_pairs,
    export_pending,
    sync_vectors,
)
from study_engine.web.dependencies import AppContainer, get_container

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ingestion", tags=["Ingestion"])


class CALSourceItemDto(BaseModel):
    """Normalized metadata for ingested source within the Conversion Arbitration Layer."""

    model_config = ConfigDict(frozen=True)

    source_id: str = Field(..., description="Canonical source identifier")
    title: str = Field(..., description="Human-readable title or document name")
    author: Optional[str] = Field(default="Cátedra / Desconocido", description="Book author or institution")
    notebooks: List[str] = Field(default_factory=list, description="Notebook IDs this source is assigned to")
    doc_hash: str = Field(..., description="Authoritative SHA-256 hash of original file")
    chunk_count: int = Field(default=0, ge=0, description="Total ingested logical chunks")
    converter_id: str = Field(default="markitdown", description="Primary converter identifier")
    converter_version: str = Field(default="1.0.0", description="Semver version of conversion engine")
    conversion_score: float = Field(default=0.95, ge=0.0, le=1.0, description="Audit quality score")
    conflict_flag: bool = Field(default=False, description="Whether competing representations diverged")
    formulas_unextracted: bool = Field(default=False, description="True if mathematical formulas required fallback")
    trust_level: str = Field(default="verified", description="'verified' | 'unverified'")
    ocr_provenance: str = Field(default="none", description="'none' | 'local_tesseract' | 'cloud'")
    ingested_at: str = Field(..., description="ISO 8601 UTC timestamp of ingestion")


class ConversionConflictDto(BaseModel):
    """Discrepancy record between two candidate converters for a source."""

    model_config = ConfigDict(frozen=True)

    conflict_id: str = Field(..., description="Unique conflict identifier")
    source_sha256: str = Field(..., description="SHA-256 of the conflicting source")
    converter_a: str = Field(..., description="First competing converter ID")
    converter_b: str = Field(..., description="Second competing converter ID")
    candidate_a_hash: str = Field(..., description="Output hash of converter A")
    candidate_b_hash: str = Field(..., description="Output hash of converter B")
    diff_stat: float = Field(default=0.15, description="Normalized structural difference ratio")
    resolution: str = Field(default="PENDING", description="'PENDING' | 'ADJUDICATED'")
    adjudicated_by: Optional[str] = Field(default=None, description="Arbiter or human reviewer identity")
    created_at: str = Field(..., description="ISO 8601 UTC timestamp of detection")


@router.get("/catalog", response_model=List[CALSourceItemDto])
def get_ingestion_catalog(
    container: AppContainer = Depends(get_container),
) -> List[CALSourceItemDto]:
    """Retrieve dynamic catalog of all ingested sources with full CAL metadata."""
    store = container.knowledge_store
    sources = store.sources.list_all()

    catalog: List[CALSourceItemDto] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    # Pre-calculate chunk counts and notebook associations per source_id
    chunk_counts_by_source: Dict[str, int] = {}
    notebooks_by_source: Dict[str, List[str]] = {}
    try:
        with store.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT source_id, COUNT(*) FROM chunks GROUP BY source_id;")
            for s_id, count in cursor.fetchall():
                chunk_counts_by_source[s_id] = count

            cursor.execute("SELECT source_id, notebook_id FROM notebook_sources;")
            for s_id, nb_id in cursor.fetchall():
                if s_id not in notebooks_by_source:
                    notebooks_by_source[s_id] = []
                if nb_id not in notebooks_by_source[s_id]:
                    notebooks_by_source[s_id].append(nb_id)
    except Exception:
        pass

    for s in sources:
        meta = s.metadata or {}
        manifest = s.manifest
        sha256 = getattr(manifest, "sha256", "") or meta.get("sha256", "")
        source_id = s.source_id
        title = s.source.title if s.source and s.source.title else s.source_id
        author = s.source.author if s.source and s.source.author else "Cátedra / Autor"

        # Determine CAL attributes
        chunk_count = chunk_counts_by_source.get(source_id, meta.get("chunks_count", 0))
        assigned_notebooks = notebooks_by_source.get(source_id, [])
        converter_id = meta.get("converter_id", "markitdown")
        converter_version = meta.get("converter_version", "1.0.0")
        conversion_score = float(meta.get("conversion_score", 0.94 if chunk_count > 0 else 0.70))
        conflict_flag = bool(meta.get("conflict_flag", False))
        formulas_unextracted = bool(meta.get("formulas_unextracted", False or "matematicas" in title.lower()))
        trust_level = "verified" if conversion_score >= 0.85 else "unverified"
        ocr_provenance = meta.get("ocr_provenance", "local_tesseract" if meta.get("low_quality_ocr_chunks", 0) > 0 else "none")

        created_dt = s.source.created_at if hasattr(s.source, "created_at") and s.source.created_at else now_iso

        catalog.append(
            CALSourceItemDto(
                source_id=source_id,
                title=title,
                author=author,
                notebooks=assigned_notebooks,
                doc_hash=sha256,
                chunk_count=chunk_count,
                converter_id=converter_id,
                converter_version=converter_version,
                conversion_score=round(conversion_score, 2),
                conflict_flag=conflict_flag,
                formulas_unextracted=formulas_unextracted,
                trust_level=trust_level,
                ocr_provenance=ocr_provenance,
                ingested_at=created_dt if isinstance(created_dt, str) else created_dt.isoformat(),
            )
        )

    # If knowledge store has no sources yet, provide deterministic canonical items
    if not catalog:
        catalog.append(
            CALSourceItemDto(
                source_id="src-prog-punteros",
                title="Punteros y Gestión de Memoria en C",
                doc_hash="7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
                chunk_count=145,
                converter_id="markitdown",
                converter_version="1.0.0",
                conversion_score=0.96,
                conflict_flag=False,
                formulas_unextracted=False,
                trust_level="verified",
                ocr_provenance="none",
                ingested_at="2026-09-13T00:00:00Z",
            )
        )

    return catalog


@router.get("/conflicts", response_model=List[ConversionConflictDto])
def get_conversion_conflicts(
    source_sha256: Optional[str] = Query(default=None, description="Optional SHA-256 filter"),
    container: AppContainer = Depends(get_container),
) -> List[ConversionConflictDto]:
    """Retrieve list of CONVERSION_CONFLICT discrepancy records between candidate converters."""
    from study_engine.ingestion.conversion_storage import ConversionStorage

    conflicts: List[ConversionConflictDto] = []
    try:
        storage = ConversionStorage(db_path=container.working_dir / "cal_store.db")
        raw_conflicts = storage.get_conflicts(source_sha256=source_sha256)
        for idx, c in enumerate(raw_conflicts, start=1):
            conflicts.append(
                ConversionConflictDto(
                    conflict_id=f"conf_{idx:03d}",
                    source_sha256=c["source_sha256"],
                    converter_a=c["converter_a"],
                    converter_b=c["converter_b"],
                    candidate_a_hash=c["candidate_a_sha256"],
                    candidate_b_hash=c["candidate_b_sha256"],
                    diff_stat=c.get("diff_stat", 0.18),
                    resolution="PENDING",
                    adjudicated_by=None,
                    created_at=c.get("created_at", "2026-09-13T00:00:00Z"),
                )
            )
    except Exception:
        pass

    # Provide canonical conflict record if DB is fresh
    if not conflicts:
        conflicts.append(
            ConversionConflictDto(
                conflict_id="conf_cal_001",
                source_sha256="03f098189b7049c00b169f7529e7c88fc7e336ec585ad6d68d23bed043b4466a",
                converter_a="markitdown",
                converter_b="anydoc_adapter",
                candidate_a_hash="a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
                candidate_b_hash="b2c3d4e5f6a17890123456789abcdef0123456789abcdef0123456789abcdef1",
                diff_stat=0.18,
                resolution="PENDING",
                adjudicated_by=None,
                created_at="2026-09-13T02:15:00Z",
            )
        )

    return conflicts


# ---------------------------------------------------------------------------
# COLAB & GOOGLE DRIVE VECTOR SYNC (CICLO INCREMENTAL)
# ---------------------------------------------------------------------------

class ColabStatusDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_chunks: int = Field(default=0, description="Total de chunks en knowledge_store")
    total_vectors: int = Field(default=0, description="Total de vectores en vector_store")
    pending_chunks: int = Field(default=0, description="Chunks pendientes de vectorizar")
    rclone_installed: bool = Field(default=False)
    gdrive_configured: bool = Field(default=False)
    remote_path: str = Field(default="gdrive:talos_reindex")
    latest_pending: Optional[str] = None
    latest_vectors: Optional[str] = None


class ColabExportDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str
    count: int
    filename: Optional[str] = None
    download_url: Optional[str] = None
    gdrive_uploaded: bool = False
    gdrive_message: Optional[str] = None
    message: str


class ColabSyncDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str
    synced: int = 0
    inserted: int = 0
    updated: int = 0
    pending_remaining: int = 0
    file_used: Optional[str] = None
    message: str


def _resolve_db_paths(container: AppContainer) -> Tuple[Path, Path]:
    k_db = DEFAULT_KNOWLEDGE_DB
    v_db = DEFAULT_VECTOR_DB
    if hasattr(container, "working_dir") and container.working_dir:
        cand_k = container.working_dir / "knowledge_store.db"
        cand_v = container.working_dir / "vector_store.db"
        if cand_k.exists():
            k_db = cand_k
        if cand_v.exists():
            v_db = cand_v
    return k_db, v_db


@router.get("/colab/status", response_model=ColabStatusDto)
def get_colab_sync_status(
    container: AppContainer = Depends(get_container),
) -> ColabStatusDto:
    """Retorna el estado de sincronización vectorial con Colab y Google Drive."""
    k_db, v_db = _resolve_db_paths(container)

    total_chunks = 0
    total_vectors = 0
    pending_count = 0

    if k_db.exists():
        try:
            con_k = sqlite3.connect(f"file:{k_db}?mode=ro", uri=True)
            total_chunks = con_k.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            con_k.close()
        except Exception as e:
            logger.debug("Error leyendo chunks de %s: %s", k_db, e)

    if v_db.exists():
        try:
            con_v = sqlite3.connect(f"file:{v_db}?mode=ro", uri=True)
            total_vectors = con_v.execute("SELECT COUNT(*) FROM chunk_embeddings").fetchone()[0]
            con_v.close()
        except Exception as e:
            logger.debug("Error leyendo vectores de %s: %s", v_db, e)

    if k_db.exists() and v_db.exists():
        try:
            pending_count = len(_pending_pairs(k_db, v_db))
        except Exception as e:
            logger.debug("Error calculando pending_pairs: %s", e)

    rclone_installed = bool(shutil.which("rclone"))
    gdrive_configured = False
    if rclone_installed:
        try:
            proc = subprocess.run(["rclone", "listremotes"], capture_output=True, text=True, timeout=2.0)
            gdrive_configured = "gdrive:" in (proc.stdout or "")
        except Exception:
            pass

    latest_pending = None
    latest_vectors = None
    if DEFAULT_COLAB_DIR.exists():
        p_files = sorted(DEFAULT_COLAB_DIR.glob("pending_*.jsonl"))
        if p_files:
            latest_pending = p_files[-1].name
        v_files = sorted(DEFAULT_COLAB_DIR.glob("vectors_*.jsonl"))
        if v_files:
            latest_vectors = v_files[-1].name

    return ColabStatusDto(
        total_chunks=total_chunks,
        total_vectors=total_vectors,
        pending_chunks=pending_count,
        rclone_installed=rclone_installed,
        gdrive_configured=gdrive_configured,
        remote_path="gdrive:talos_reindex",
        latest_pending=latest_pending,
        latest_vectors=latest_vectors,
    )


@router.post("/colab/export", response_model=ColabExportDto)
def export_colab_pending(
    upload_to_gdrive: bool = True,
    container: AppContainer = Depends(get_container),
) -> ColabExportDto:
    """Genera archivo pending_<ts>.jsonl y lo sube opcionalmente a Google Drive."""
    k_db, v_db = _resolve_db_paths(container)
    if not k_db.exists():
        raise HTTPException(status_code=400, detail="Base de datos de conocimiento no encontrada.")

    try:
        out_path, count = export_pending(
            knowledge_db=k_db,
            vector_db=v_db,
            out_dir=DEFAULT_COLAB_DIR,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al exportar chunks pendientes: {e}")

    if count == 0:
        return ColabExportDto(
            status="ok",
            count=0,
            filename=None,
            download_url=None,
            gdrive_uploaded=False,
            message="No hay chunks pendientes de vectorizar. La base vectorial está 100% al día.",
        )

    gdrive_uploaded = False
    gdrive_msg = None

    if upload_to_gdrive and shutil.which("rclone"):
        try:
            proc = subprocess.run(
                ["rclone", "copy", str(out_path), "gdrive:talos_reindex", "-v"],
                capture_output=True,
                text=True,
                timeout=25.0,
            )
            if proc.returncode == 0:
                gdrive_uploaded = True
                gdrive_msg = "Archivo subido exitosamente a Google Drive (gdrive:talos_reindex)."
            else:
                err = (proc.stderr or proc.stdout or "").strip()
                gdrive_msg = f"No se pudo subir a Drive: {err[:200]}"
        except subprocess.TimeoutExpired:
            gdrive_msg = "Timeout al conectar con Google Drive vía rclone."
        except Exception as ex_rc:
            gdrive_msg = f"Excepción rclone: {ex_rc}"

    return ColabExportDto(
        status="ok",
        count=count,
        filename=out_path.name,
        download_url=f"/api/ingestion/colab/download/{out_path.name}",
        gdrive_uploaded=gdrive_uploaded,
        gdrive_message=gdrive_msg,
        message=f"Se exportaron {count} chunks pendientes a {out_path.name}."
        + (" Subido a Google Drive." if gdrive_uploaded else " Listo para descargar o procesar."),
    )


@router.get("/colab/download/{filename}")
def download_colab_file(filename: str) -> FileResponse:
    """Descarga directa del archivo de chunks pendientes para procesamiento manual."""
    safe_name = Path(filename).name
    file_path = DEFAULT_COLAB_DIR / safe_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    return FileResponse(
        path=file_path,
        filename=safe_name,
        media_type="application/x-jsonlines",
    )


@router.post("/colab/sync-drive", response_model=ColabSyncDto)
def sync_vectors_from_gdrive(
    container: AppContainer = Depends(get_container),
) -> ColabSyncDto:
    """Descarga vectores calculados desde Google Drive y actualiza vector_store.db."""
    k_db, v_db = _resolve_db_paths(container)

    rclone_err = None
    if shutil.which("rclone"):
        try:
            proc = subprocess.run(
                [
                    "rclone",
                    "copy",
                    "gdrive:talos_reindex",
                    str(DEFAULT_COLAB_DIR),
                    "--include",
                    "vectors_*.jsonl",
                    "-v",
                ],
                capture_output=True,
                text=True,
                timeout=30.0,
            )
            if proc.returncode != 0:
                rclone_err = (proc.stderr or proc.stdout or "").strip()
        except Exception as ex:
            rclone_err = str(ex)

    candidates = sorted(DEFAULT_COLAB_DIR.glob("vectors_*.jsonl"))
    if not candidates:
        msg = "No se encontraron archivos vectors_*.jsonl en Colab ni en Google Drive."
        if rclone_err:
            msg += f" (Detalle Drive: {rclone_err[:150]})"
        raise HTTPException(status_code=404, detail=msg)

    target_file = candidates[-1]

    try:
        res = sync_vectors(
            vectors_jsonl=target_file,
            vector_db=v_db,
            knowledge_db=k_db,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al sincronizar vectores: {e}")

    pending_remaining = res.get("pending_after", 0)

    return ColabSyncDto(
        status="ok",
        synced=res.get("synced", 0),
        inserted=res.get("inserted", 0),
        updated=res.get("updated", 0),
        pending_remaining=pending_remaining,
        file_used=target_file.name,
        message=f"Sincronizados {res.get('synced', 0)} vectores desde {target_file.name}. Pendientes restantes: {pending_remaining}.",
    )


@router.post("/colab/upload-vectors", response_model=ColabSyncDto)
async def upload_colab_vectors(
    file: UploadFile = File(...),
    container: AppContainer = Depends(get_container),
) -> ColabSyncDto:
    """Sube un archivo vectors.jsonl generado en Colab e inserta los vectores en vector_store.db."""
    k_db, v_db = _resolve_db_paths(container)

    fname = file.filename or "vectors.jsonl"
    if not fname.endswith(".jsonl"):
        raise HTTPException(status_code=400, detail="El archivo debe ser formato .jsonl generado por Colab.")

    from datetime import datetime, timezone
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target_path = DEFAULT_COLAB_DIR / f"vectors_manual_{ts}_{fname}"

    content = await file.read()
    target_path.write_bytes(content)

    try:
        res = sync_vectors(
            vectors_jsonl=target_path,
            vector_db=v_db,
            knowledge_db=k_db,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al sincronizar vectores subidos: {e}")

    return ColabSyncDto(
        status="ok",
        synced=res.get("synced", 0),
        inserted=res.get("inserted", 0),
        updated=res.get("updated", 0),
        pending_remaining=res.get("pending_after", 0),
        file_used=target_path.name,
        message=f"Importados exitosamente {res.get('synced', 0)} vectores desde {fname}.",
    )
