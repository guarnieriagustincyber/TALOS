"""PDF Validation, Hashing, and Extraction Utilities."""

import hashlib
import os
from pathlib import Path
import shutil
from typing import Tuple, Union
from fastapi import HTTPException, UploadFile, status
import pymupdf


def validate_and_hash_pdf(file_path: Union[Path, str]) -> str:
    """Validate PDF magic bytes (%PDF-) and calculate SHA-256 hash for a file on disk."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        header = f.read(5)
        if header != b"%PDF-":
            raise ValueError(f"Invalid PDF header in {path}: expected %PDF-")
        hasher.update(header)
        while chunk := f.read(1024 * 1024):
            hasher.update(chunk)

    return hasher.hexdigest()


async def save_and_hash_uploaded_pdf(
    file: UploadFile,
    target_dir: Path,
) -> Tuple[str, Path]:
    """Stream an uploaded file to a temporary file, validating %PDF- header and hashing.

    Returns (sha256_hash, final_path).
    Raises HTTPException(400) if header is invalid.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    temp_path = target_dir / f"temp_{os.urandom(6).hex()}.pdf"
    hasher = hashlib.sha256()

    try:
        with open(temp_path, "wb") as buffer:
            header = await file.read(5)
            if header != b"%PDF-":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Encabezado PDF inválido (%PDF- requerido).",
                )
            buffer.write(header)
            hasher.update(header)
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)
                hasher.update(chunk)

        doc_hash = hasher.hexdigest()
        final_pdf = target_dir / f"{doc_hash}.pdf"

        if not final_pdf.exists():
            shutil.move(temp_path, final_pdf)
        else:
            temp_path.unlink(missing_ok=True)

        return doc_hash, final_pdf
    except Exception:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise


def extract_pdf_cover(
    pdf_path: Path,
    cover_dir: Path,
    doc_hash: str,
    dpi: int = 120,
) -> Tuple[int, Path]:
    """Extract first page cover as .webp image and return (page_count, cover_path)."""
    cover_dir.mkdir(parents=True, exist_ok=True)
    cover_path = cover_dir / f"{doc_hash}.webp"
    doc = pymupdf.open(str(pdf_path))
    try:
        page_count = len(doc)
        if page_count > 0 and not cover_path.exists():
            first_page = doc.load_page(0)
            pix = first_page.get_pixmap(dpi=dpi)
            try:
                pix.save(str(cover_path), output="webp")
            except Exception:
                pix.save(str(cover_path), output="png")
        return page_count, cover_path
    finally:
        doc.close()
