"""Document ingestion: deterministic file extraction into Document domain artifacts."""

import copy
from pathlib import Path
import re
from typing import Any, Dict, Optional, Tuple, Union
import unicodedata

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from study_engine.contracts.document import Document
from study_engine.contracts.enums import IngestionStatus
from study_engine.contracts.ingestion import IngestionError, IngestionResult


def slugify_filename(text: str) -> str:
    """Generate a deterministic, safe, ASCII-compatible slug from a filename stem.

    Rules:
        - Normalizes Unicode characters and strips diacritics.
        - Converts non-alphanumeric characters (excluding underscores/hyphens) to hyphens.
        - Collapses repeated hyphens to single '-' and repeated underscores to single '_'.
        - Strips leading and trailing hyphens and underscores.
        - Lowercases the result.
        - Falls back to 'document' if the resulting slug is empty.
    """
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9_\-]+", "-", normalized)
    slug = re.sub(r"-+", "-", slug)
    slug = re.sub(r"_+", "_", slug)
    slug = slug.strip("-_").lower()
    return slug if slug else "document"


def _validate_target_file(
    file_path: Union[str, Path],
    clean_source_id: str,
    corpus_root: Optional[Union[str, Path]],
) -> Tuple[Optional[Path], Optional[str], Optional[IngestionResult]]:
    """Validate existence, regular file nature, and corpus boundary constraints."""
    if not file_path or not str(file_path).strip():
        return None, None, IngestionResult(
            source_id=clean_source_id,
            status=IngestionStatus.FAILED,
            error=IngestionError(
                code="FILE_NOT_FOUND",
                message="File path cannot be empty.",
            ),
        )

    raw_path = Path(file_path)

    # Validate corpus_root boundary and path traversal
    if corpus_root is not None:
        try:
            corpus_base = Path(corpus_root).resolve()
            resolved_target = raw_path.resolve()
            rel_path_str = str(resolved_target.relative_to(corpus_base))
            target_file = resolved_target
        except ValueError:
            return None, None, IngestionResult(
                source_id=clean_source_id,
                status=IngestionStatus.FAILED,
                error=IngestionError(
                    code="PATH_TRAVERSAL",
                    message=f"File path '{file_path}' escapes corpus root '{corpus_root}'.",
                ),
            )
    else:
        target_file = raw_path
        rel_path_str = str(file_path)

    if not target_file.exists():
        return None, None, IngestionResult(
            source_id=clean_source_id,
            status=IngestionStatus.FAILED,
            error=IngestionError(
                code="FILE_NOT_FOUND",
                message=f"File does not exist: '{file_path}'.",
            ),
        )

    if target_file.is_dir():
        return None, None, IngestionResult(
            source_id=clean_source_id,
            status=IngestionStatus.FAILED,
            error=IngestionError(
                code="IS_DIRECTORY",
                message=f"Path is a directory, not a regular file: '{file_path}'.",
            ),
        )

    if not target_file.is_file():
        return None, None, IngestionResult(
            source_id=clean_source_id,
            status=IngestionStatus.FAILED,
            error=IngestionError(
                code="FILE_NOT_FOUND",
                message=f"Path is not a regular file: '{file_path}'.",
            ),
        )

    return target_file, rel_path_str, None


def _extract_pdf_content(
    target_file: Path,
    clean_source_id: str,
    file_path: Union[str, Path],
) -> Tuple[Optional[str], int, bool, Dict[str, Any], Optional[IngestionResult]]:
    """Extract full text, page boundaries, and metadata from a PDF file."""
    pdf_metadata: Dict[str, Any] = {}
    try:
        file_size = target_file.stat().st_size
        if file_size == 0:
            return None, 0, False, {}, IngestionResult(
                source_id=clean_source_id,
                status=IngestionStatus.FAILED,
                error=IngestionError(
                    code="EMPTY_FILE",
                    message=f"PDF file is empty (0 bytes): '{file_path}'.",
                ),
            )

        # 1. Base validation and extraction with pypdf (handles encryption, metadata, baseline text)
        reader = PdfReader(str(target_file))
        if reader.is_encrypted:
            try:
                decrypt_status = reader.decrypt("")
                if decrypt_status == 0:
                    return None, 0, False, {}, IngestionResult(
                        source_id=clean_source_id,
                        status=IngestionStatus.FAILED,
                        error=IngestionError(
                            code="ENCRYPTED_PDF",
                            message=f"PDF is encrypted and requires a password: '{file_path}'.",
                        ),
                    )
            except Exception:
                return None, 0, False, {}, IngestionResult(
                    source_id=clean_source_id,
                    status=IngestionStatus.FAILED,
                    error=IngestionError(
                        code="ENCRYPTED_PDF",
                        message=f"PDF is encrypted and requires a password: '{file_path}'.",
                    ),
                )

        if reader.metadata:
            for k, v in reader.metadata.items():
                if v is not None and isinstance(v, (str, int, float, bool)):
                    clean_key = str(k).lstrip("/")
                    pdf_metadata[clean_key] = str(v)

        page_count = len(reader.pages)
        page_texts = []
        page_boundaries = []
        current_char_offset = 0

        for page_idx, page in enumerate(reader.pages, start=1):
            extracted = page.extract_text()
            p_text = extracted if extracted is not None else ""
            page_texts.append(p_text)

            p_len = len(p_text)
            page_boundaries.append({
                "page_number": page_idx,
                "char_start": current_char_offset,
                "char_end": current_char_offset + p_len,
            })
            current_char_offset += p_len + 2  # account for "\n\n" separator

        full_text = unicodedata.normalize("NFC", "\n\n".join(page_texts).strip())
        has_text = bool(full_text)
        pdf_metadata["page_boundaries"] = page_boundaries

        # 2. Try High-Precision AST layout extraction (PyMuPDF) if rich structure or tables are present
        try:
            from study_engine.ingestion.converters.layout_adapter import LayoutAwareConverterAdapter
            layout_adapter = LayoutAwareConverterAdapter()
            layout_res = layout_adapter.convert(target_file)
            # Only use layout markdown if it actually extracted meaningful content
            # (synthetic test PDFs created with hand-crafted streams have no PyMuPDF text)
            if layout_res.markdown_content and layout_res.markdown_content.strip():
                # Check if layout extraction actually extracted text beyond just page headers
                clean_layout_text = unicodedata.normalize("NFC", layout_res.markdown_content.strip())
                # If PyMuPDF found tables or code blocks or has substantial text matching/exceeding pypdf
                if layout_res.tables_count > 0 or layout_res.code_blocks_count > 0 or len(clean_layout_text) >= len(full_text):
                    layout_boundaries = []
                    c_offset = 0
                    for p_num in sorted(layout_res.page_map.keys()):
                        p_txt = layout_res.page_map[p_num]
                        p_l = len(p_txt)
                        layout_boundaries.append({
                            "page_number": p_num,
                            "char_start": c_offset,
                            "char_end": c_offset + p_l,
                        })
                        c_offset += p_l + 2

                    pdf_metadata["page_boundaries"] = layout_boundaries
                    pdf_metadata["tables_count"] = layout_res.tables_count
                    pdf_metadata["code_blocks_count"] = layout_res.code_blocks_count
                    pdf_metadata["headers_count"] = layout_res.headers_count
                    pdf_metadata["formulas_detected"] = layout_res.formulas_detected
                    pdf_metadata["converter_engine"] = "pymupdf_ast"
                    return clean_layout_text, layout_res.page_count, bool(clean_layout_text), pdf_metadata, None
        except Exception:
            pass

        # 3. If no text extracted at all, check local OCR for scanned PDFs if language assets are present
        if not has_text:
            try:
                from study_engine.ingestion.converters.tesseract_fallback import (
                    check_tesseract_availability,
                    TesseractFallbackAdapter,
                )
                if check_tesseract_availability():
                    tess_adapter = TesseractFallbackAdapter()
                    tess_res = tess_adapter.convert(target_file)
                    if tess_res.markdown_content and tess_res.markdown_content.strip():
                        actual_text = "\n".join(
                            line for line in tess_res.markdown_content.splitlines()
                            if not line.strip().startswith("# Page ")
                        ).strip()
                        if actual_text:
                            ocr_text = unicodedata.normalize("NFC", tess_res.markdown_content.strip())
                            pdf_metadata["has_ocr"] = True
                            pdf_metadata["ocr_provenance"] = "local_tesseract"
                            return ocr_text, tess_res.page_count, True, pdf_metadata, None
            except Exception:
                pass

        return full_text, page_count, has_text, pdf_metadata, None

    except (PdfReadError, Exception) as exc:
        return None, 0, False, {}, IngestionResult(
            source_id=clean_source_id,
            status=IngestionStatus.FAILED,
            error=IngestionError(
                code="INVALID_PDF",
                message=f"Failed to parse PDF file '{file_path}': {str(exc)}",
            ),
        )


def _extract_text_content(
    target_file: Path,
    clean_source_id: str,
    file_path: Union[str, Path],
) -> Tuple[Optional[str], int, bool, Dict[str, Any], Optional[IngestionResult]]:
    """Extract full text from plain text or markdown files."""
    try:
        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            full_text = unicodedata.normalize("NFC", f.read().strip())
        return full_text, 1, bool(full_text), {}, None
    except Exception as exc:
        return None, 0, False, {}, IngestionResult(
            source_id=clean_source_id,
            status=IngestionStatus.FAILED,
            error=IngestionError(
                code="READ_ERROR",
                message=f"Failed to read text file '{file_path}': {str(exc)}",
            ),
        )


def ingest_document(
    file_path: Union[str, Path],
    source_id: str,
    title: Optional[str] = None,
    document_id: Optional[str] = None,
    corpus_root: Optional[Union[str, Path]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> IngestionResult:
    """Ingest a physical file (PDF, TXT, MD) and produce a Document artifact.

    Deterministic Pipeline:
        1. Validate source_id and input paths.
        2. Verify filesystem constraints (existence, regular file, corpus boundary).
        3. Extract text content and page count deterministically.
        4. Construct and return an IngestionResult containing the Document domain model.

    Returns:
        IngestionResult: COMPLETED with Document on success, FAILED with structured IngestionError on expected failures.

    Raises:
        ValueError: If source_id is empty, whitespace, or invalid type.
    """
    if not source_id or not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must be a non-empty string identifier.")

    clean_source_id = source_id.strip()

    target_file, rel_path_str, err_result = _validate_target_file(
        file_path=file_path,
        clean_source_id=clean_source_id,
        corpus_root=corpus_root,
    )
    if err_result is not None:
        return err_result

    # Determine document identity
    if document_id is not None and isinstance(document_id, str) and document_id.strip():
        final_doc_id = document_id.strip()
    else:
        slug = slugify_filename(target_file.stem)
        final_doc_id = f"{clean_source_id}:{slug}"

    suffix = target_file.suffix.lower()
    if suffix == ".pdf":
        full_text, page_count, has_text, pdf_metadata, err = _extract_pdf_content(
            target_file=target_file,
            clean_source_id=clean_source_id,
            file_path=file_path,
        )
        if err is not None:
            return err
    elif suffix in (".txt", ".md", ".markdown"):
        full_text, page_count, has_text, pdf_metadata, err = _extract_text_content(
            target_file=target_file,
            clean_source_id=clean_source_id,
            file_path=file_path,
        )
        if err is not None:
            return err
    else:
        return IngestionResult(
            source_id=clean_source_id,
            status=IngestionStatus.FAILED,
            error=IngestionError(
                code="UNSUPPORTED_MEDIA_TYPE",
                message=f"Unsupported format for document ingestion: '{suffix}'.",
            ),
        )

    # Determine title
    if title is not None and isinstance(title, str) and title.strip():
        final_title = title.strip()
    elif "Title" in pdf_metadata and pdf_metadata["Title"].strip():
        final_title = pdf_metadata["Title"].strip()
    else:
        final_title = target_file.stem

    # Build metadata with deep defensive copying
    combined_metadata = copy.deepcopy(metadata) if metadata else {}
    combined_metadata["has_text"] = has_text
    if pdf_metadata:
        combined_metadata["pdf_metadata"] = pdf_metadata

    doc = Document(
        id=final_doc_id,
        source_id=clean_source_id,
        title=final_title,
        content=full_text,
        path=rel_path_str,
        page_count=page_count,
        language="es",
        metadata=combined_metadata,
    )

    return IngestionResult(
        source_id=clean_source_id,
        status=IngestionStatus.COMPLETED,
        document_id=doc.id,
        document=doc.model_copy(deep=True),
    )
