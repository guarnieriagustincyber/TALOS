from collections import OrderedDict
import hashlib
from pathlib import Path
import re
import subprocess
import threading
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field, StrictStr
import pymupdf

from study_engine.utils.pdf_utils import extract_pdf_cover, save_and_hash_uploaded_pdf

router = APIRouter(prefix="/api/sources", tags=["Sources"])

BASE_DIR = Path(__file__).resolve().parents[4] / "kasiu-lab"
STORAGE_DIR = BASE_DIR / "storage"
SOURCES_DIR = STORAGE_DIR / "sources"
COVERS_DIR = STORAGE_DIR / "covers"

SOURCES_DIR.mkdir(parents=True, exist_ok=True)
COVERS_DIR.mkdir(parents=True, exist_ok=True)

HASH_REGEX = re.compile(r"^[a-fA-F0-9]{64}$")


class PageRenderLRUCache:
    """Caché LRU en memoria hilo-segura para imágenes renderizadas de páginas PDF.
    
    Elimina la lectura repetitiva de disco y el re-parseo síncrono de documentos
    canónicos pesados (e.g. Kurose, Tanenbaum, Stallings).
    """

    def __init__(self, max_items: int = 128) -> None:
        self.max_items = max_items
        self._cache: OrderedDict[str, Tuple[bytes, bool, str]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Tuple[bytes, bool, str]]:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            return None

    def set(self, key: str, value: Tuple[bytes, bool, str]) -> None:
        with self._lock:
            self._cache[key] = value
            self._cache.move_to_end(key)
            if len(self._cache) > self.max_items:
                self._cache.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


_PAGE_RENDER_CACHE = PageRenderLRUCache(max_items=128)


class OpenLocalPayload(BaseModel):
    doc_hash: StrictStr = Field(..., description="SHA-256 hash of the document")
    page: int = Field(default=1, ge=1, description="1-based page number")

    model_config = ConfigDict(extra="forbid")


@router.post("/upload")
async def upload_source(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload a source PDF, compute its SHA256 digest, extract cover, and store it deterministically."""
    filename = file.filename or "unknown.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se admiten documentos en formato canónico .pdf",
        )

    try:
        doc_hash, final_pdf = await save_and_hash_uploaded_pdf(file, SOURCES_DIR)
        page_count, cover_path = extract_pdf_cover(final_pdf, COVERS_DIR, doc_hash)

        return {
            "doc_hash": doc_hash,
            "filename": filename,
            "page_count": page_count,
            "cover_url": f"/storage/covers/{doc_hash}.webp",
            "file_path": str(final_pdf.resolve()),
            "size_bytes": final_pdf.stat().st_size,
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fallo en procesamiento del documento fuente.",
        )


@router.get("", response_model=List[Dict[str, Any]])
def list_sources() -> List[Dict[str, Any]]:
    """Retrieve catalog of indexed canonical sources."""
    results: List[Dict[str, Any]] = []
    seen_hashes: set[str] = set()

    if SOURCES_DIR.exists():
        for item in sorted(SOURCES_DIR.iterdir()):
            if item.is_file() and item.suffix.lower() == ".pdf" and not item.name.startswith("temp_"):
                doc_hash = item.stem
                if HASH_REGEX.match(doc_hash):
                    seen_hashes.add(doc_hash)
                    page_count = 0
                    try:
                        doc = pymupdf.open(str(item))
                        page_count = len(doc)
                        doc.close()
                    except Exception:
                        pass

                    title = item.name
                    if doc_hash == "7599e188b2645104576b5502400565aff7892ef02abb866ed6899ef9b5865a9a":
                        title = "Computer Networking: A Top-Down Approach"
                        author = "James W. Kurose, Keith W. Ross"
                        category = "curriculares"
                        year = "2021"
                        theme = "kurose"
                        desc = "Texto canónico de redes de computadoras con enfoque de capa de aplicación a enlace físico."
                    elif doc_hash == "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069":
                        title = "Transmission Control Protocol (RFC 793)"
                        author = "Information Sciences Institute (USC) / Postel"
                        category = "rfc"
                        year = "1981"
                        theme = "rfc"
                        desc = "Estándar fundacional que define la máquina de estados finitos (FSM) de 3 vías y el reloj ISN."
                    else:
                        author = "Cátedra / Autoridad"
                        category = "curriculares"
                        year = "2026"
                        theme = "fadena"
                        desc = f"Documento canónico indexado ({doc_hash[:12]}…)"

                    results.append({
                        "id": f"src-{doc_hash[:8]}",
                        "title": title,
                        "subtitle": f"SHA-256: {doc_hash[:16]}…",
                        "author": author,
                        "category": category,
                        "pages": page_count,
                        "year": year,
                        "docHash": doc_hash,
                        "doc_hash": doc_hash,
                        "coverImage": f"/api/sources/{doc_hash}/page-render?page=1",
                        "cover_url": f"/api/sources/{doc_hash}/page-render?page=1",
                        "theme": theme,
                        "description": desc,
                    })

    if "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069" not in seen_hashes:
        results.append({
            "id": "b-rfc793",
            "title": "Transmission Control Protocol (RFC 793)",
            "subtitle": "DARPA Internet Program Protocol Specification",
            "author": "Information Sciences Institute (USC) / Postel",
            "category": "rfc",
            "pages": 85,
            "year": "1981",
            "docHash": "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
            "doc_hash": "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
            "coverImage": "/api/sources/7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069/page-render?page=1",
            "cover_url": "/api/sources/7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069/page-render?page=1",
            "theme": "rfc",
            "description": "Estándar fundacional que define la máquina de estados finitos (FSM) de 3 vías y el reloj ISN.",
        })

    return results


ROOT_PROJECT_DIR = Path(__file__).resolve().parents[4]
BENCHMARK_SOURCES_DIR = ROOT_PROJECT_DIR / "data" / "benchmark" / "sources"
DATA_SOURCES_DIR = ROOT_PROJECT_DIR / "data" / "sources"
ALLOWED_SOURCE_DIRS = [
    SOURCES_DIR.resolve(),
    BENCHMARK_SOURCES_DIR.resolve(),
    DATA_SOURCES_DIR.resolve(),
]

def _resolve_source_pdf(clean_hash: str) -> Optional[Path]:
    """Resolve a canonical PDF file by SHA-256 hash safely across allowed directories."""
    # 1. Direct match in SOURCES_DIR
    direct = SOURCES_DIR / f"{clean_hash}.pdf"
    if direct.exists():
        resolved = direct.resolve()
        if any(resolved.is_relative_to(d.resolve()) for d in ALLOWED_SOURCE_DIRS):
            return resolved

    # 2. Match in BENCHMARK_SOURCES_DIR
    if BENCHMARK_SOURCES_DIR.exists():
        direct_bench = BENCHMARK_SOURCES_DIR / f"{clean_hash}.pdf"
        if direct_bench.exists():
            resolved_bench = direct_bench.resolve()
            if any(resolved_bench.is_relative_to(d.resolve()) for d in ALLOWED_SOURCE_DIRS):
                return resolved_bench

        for candidate in BENCHMARK_SOURCES_DIR.glob("*.pdf"):
            if candidate.name.startswith("temp_"):
                continue
            if candidate.stem.lower() == clean_hash:
                resolved_cand = candidate.resolve()
                if any(resolved_cand.is_relative_to(d.resolve()) for d in ALLOWED_SOURCE_DIRS):
                    return resolved_cand

    # 3. Match in DATA_SOURCES_DIR (recursive for scoped subjects and general)
    if DATA_SOURCES_DIR.exists():
        for candidate in DATA_SOURCES_DIR.rglob("*.pdf"):
            if candidate.name.startswith("temp_"):
                continue
            if candidate.stem.lower() == clean_hash:
                resolved_cand = candidate.resolve()
                if any(resolved_cand.is_relative_to(d.resolve()) for d in ALLOWED_SOURCE_DIRS):
                    return resolved_cand

    # 4. Fallback lookup via SQLite knowledge_store documents/sources table
    db_path = ROOT_PROJECT_DIR / "data" / "web_state" / "knowledge_store.db"
    if db_path.exists():
        try:
            import sqlite3
            with sqlite3.connect(str(db_path)) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT d.path FROM documents d
                    LEFT JOIN sources s ON d.source_id = s.source_id
                    WHERE s.sha256 = ? OR d.id = ? OR d.id LIKE ? OR s.source_id = ?
                    LIMIT 1;
                    """,
                    (clean_hash, clean_hash, f"%{clean_hash}%", f"src_{clean_hash[:16]}"),
                )
                row = cur.fetchone()
                if row and row[0]:
                    doc_p = Path(row[0])
                    if doc_p.exists():
                        resolved_doc = doc_p.resolve()
                        if any(resolved_doc.is_relative_to(d.resolve()) for d in ALLOWED_SOURCE_DIRS):
                            return resolved_doc
        except Exception:
            pass

    return None


@router.get("/{doc_hash}/page-render")
def render_page_image(
    doc_hash: str,
    page: int = 1,
    highlight: Optional[str] = None,
    bbox: Optional[str] = None,
    dpi: int = 140,
) -> Response:
    """Render a specific PDF page to PNG image with optional highlighted text snippet (Enmiendas E8 y E9)."""
    clean_hash = doc_hash.split(":")[-1].lower()
    if not HASH_REGEX.match(clean_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Digest de documento inválido o malformado.",
        )

    file_path = _resolve_source_pdf(clean_hash)
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo PDF no encontrado en el almacén forense.",
        )

    if not any(file_path.resolve().is_relative_to(d.resolve()) for d in ALLOWED_SOURCE_DIRS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado.",
        )

    # Clamping DPI to safe range
    clamped_dpi = max(72, min(dpi, 300))

    # Enmienda E8 & LRU Cache: Clave unívoca por hash, página, DPI y resaltado
    highlight_hash = hashlib.md5((highlight or "").strip().encode("utf-8")).hexdigest()[:8]
    bbox_hash = hashlib.md5((bbox or "").strip().encode("utf-8")).hexdigest()[:6]
    etag = f'"{clean_hash[:16]}-p{page}-dpi{clamped_dpi}-h{highlight_hash}-b{bbox_hash}"'
    cache_key = f"{clean_hash}:{page}:{clamped_dpi}:{highlight_hash}:{bbox_hash}"

    # Verificación en caché LRU en memoria (Fast-path < 1ms)
    cached = _PAGE_RENDER_CACHE.get(cache_key)
    if cached is not None:
        img_bytes, has_match, cached_etag = cached
        headers = {
            "Content-Type": "image/png",
            "Cache-Control": "public, max-age=86400, immutable" if not highlight else "public, max-age=3600",
            "ETag": cached_etag,
            "X-Highlight-Matched": "true" if has_match else "false",
            "X-Render-Cache": "HIT",
        }
        return Response(content=img_bytes, media_type="image/png", headers=headers)

    try:
        doc = pymupdf.open(str(file_path))  # type: ignore[no-untyped-call]
        page_idx = max(0, min(page - 1, len(doc) - 1))
        page_obj = doc.load_page(page_idx)  # type: ignore[no-untyped-call]

        matched_rects = []

        # Enmienda E9: Cascada de 3 etapas para búsqueda y resaltado
        # Etapa 1: Si se proveyó bbox explícito (e.g. "x0,y0,x1,y1")
        if bbox:
            try:
                coords = [float(v.strip()) for v in bbox.split(",") if v.strip()]
                if len(coords) == 4:
                    matched_rects.append(pymupdf.Rect(*coords))
            except Exception:
                pass

        # Etapa 2: Si no hubo match por bbox y hay snippet highlight
        if not matched_rects and highlight and highlight.strip():
            raw_target = highlight.strip()
            # 2.1 Búsqueda exacta inicial
            rects = page_obj.search_for(raw_target)
            if rects:
                matched_rects.extend(rects)
            else:
                # 2.2 Normalización de espacios y saltos de línea (colapso de whitespace y guiones)
                normalized_target = " ".join(raw_target.split())
                rects = page_obj.search_for(normalized_target)
                if rects:
                    matched_rects.extend(rects)
                else:
                    # 2.3 Si es un párrafo largo con posibles particiones de línea o ligaduras,
                    # buscar fragmentos significativos (primeras 6-8 palabras o substrings)
                    words = [w for w in normalized_target.split() if len(w) > 3]
                    if len(words) >= 4:
                        sub_phrase = " ".join(words[:5])
                        sub_rects = page_obj.search_for(sub_phrase)
                        if sub_rects:
                            matched_rects.extend(sub_rects)

        # Si hubo matches válidos, agregar anotación de resaltado
        if matched_rects:
            for r in matched_rects[:10]:  # Limitar para evitar saturación visual
                annot = page_obj.add_highlight_annot(r)
                if annot:
                    # Tono ámbar/cian pedagógico (RGB)
                    annot.set_colors(stroke=(0.96, 0.62, 0.07))
                    annot.update()

        # Etapa 3 (E9): Si no hubo match o falló el resaltado, degradación elegante:
        # renderiza la página limpia con HTTP 200 (nunca 404 ni 500).
        pix = page_obj.get_pixmap(dpi=clamped_dpi)
        img_bytes = pix.tobytes(output="png")
        doc.close()  # type: ignore[no-untyped-call]

        # Almacenar en caché LRU para próximas consultas
        has_match = bool(matched_rects)
        _PAGE_RENDER_CACHE.set(cache_key, (img_bytes, has_match, etag))

        headers = {
            "Content-Type": "image/png",
            "Cache-Control": "public, max-age=86400, immutable" if not highlight else "public, max-age=3600",
            "ETag": etag,
            "X-Highlight-Matched": "true" if has_match else "false",
            "X-Render-Cache": "MISS",
        }

        return Response(content=img_bytes, media_type="image/png", headers=headers)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al renderizar página del documento.",
        )


@router.post("/open-local")
def open_in_system_viewer(payload: OpenLocalPayload) -> Dict[str, str]:
    """Open document in the OS default desktop PDF viewer."""
    clean_hash = payload.doc_hash.split(":")[-1].lower()
    if not HASH_REGEX.match(clean_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Digest SHA-256 inválido o malformado.",
        )

    file_path = _resolve_source_pdf(clean_hash)
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no hallado en el almacén forense.",
        )

    if not any(file_path.resolve().is_relative_to(d.resolve()) for d in ALLOWED_SOURCE_DIRS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado fuera del directorio seguro.",
        )

    try:
        subprocess.Popen(["xdg-open", str(file_path)], close_fds=True)
        return {"status": "SUCCESS", "message": f"Abriendo {file_path.name}"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fallo invocando visor local del sistema operativo.",
        )


