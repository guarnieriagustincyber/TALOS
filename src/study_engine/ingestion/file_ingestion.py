"""File ingestion component: physical file identity, SHA-256 integrity, and manifest generation."""

import hashlib
import mimetypes
from pathlib import Path
from typing import Any, Dict, Optional, Union


from study_engine.contracts.enums import IngestionStatus
from study_engine.contracts.ingestion import (
    IngestionError,
    IngestionResult,
    SourceManifest,
)

KNOWN_MEDIA_TYPES: Dict[str, str] = {
    ".pdf": "application/pdf",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".txt": "text/plain",
    ".json": "application/json",
    ".yaml": "application/yaml",
    ".yml": "application/yaml",
    ".html": "text/html",
    ".htm": "text/html",
    ".csv": "text/csv",
    ".rst": "text/x-rst",
    ".py": "text/x-python",
    ".c": "text/x-c",
    ".cpp": "text/x-c++",
    ".h": "text/x-c",
    ".epub": "application/epub+zip",
}

DEFAULT_CHUNK_SIZE: int = 65536  # 64 KB streaming buffer


def detect_media_type(file_path: Union[str, Path]) -> str:
    """Deterministically determine the media/MIME type for a file path.

    Uses an explicit mapping for standard domain document types, falling back to
    mimetypes.guess_type and finally 'application/octet-stream'.
    """
    path_obj = Path(file_path)
    ext = path_obj.suffix.lower()
    if ext in KNOWN_MEDIA_TYPES:
        return KNOWN_MEDIA_TYPES[ext]

    guessed, _ = mimetypes.guess_type(str(file_path))
    if guessed:
        return guessed

    return "application/octet-stream"


def compute_file_sha256(file_path: Union[str, Path], chunk_size: int = DEFAULT_CHUNK_SIZE) -> str:
    """Calculate SHA-256 hexadecimal hash reading the file in chunks to optimize memory."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer (> 0)")

    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def _resolve_relative_path(
    resolved_file: Path,
    corpus_root: Optional[Union[str, Path]],
) -> Optional[str]:
    """Calculate relative path safely if corpus_root is provided."""
    if corpus_root is None:
        return None

    resolved_root = Path(corpus_root).resolve()
    if not resolved_file.is_relative_to(resolved_root):
        raise ValueError(f"Path '{resolved_file}' is outside corpus root '{resolved_root}'")

    return str(resolved_file.relative_to(resolved_root))


def create_source_manifest(
    file_path: Union[str, Path],
    source_id: Optional[str] = None,
    corpus_root: Optional[Union[str, Path]] = None,
    media_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> SourceManifest:
    """Validate a physical file and construct a SourceManifest.

    Raises:
        ValueError: If file_path is empty, chunk_size <= 0, or attempts path traversal outside corpus_root.
        FileNotFoundError: If the target path does not exist.
        IsADirectoryError: If the target path is a directory.
        PermissionError: If read permissions are denied.
        OSError: If an I/O error occurs.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer (> 0)")

    if not file_path or not str(file_path).strip():
        raise ValueError("File path cannot be empty.")


    raw_path = Path(file_path)
    if not raw_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not raw_path.is_file():
        raise IsADirectoryError(f"Path is not a regular file: {file_path}")

    resolved_path = raw_path.resolve()
    rel_path = _resolve_relative_path(resolved_path, corpus_root)

    byte_size = resolved_path.stat().st_size
    sha256_hash = compute_file_sha256(resolved_path, chunk_size=chunk_size)
    resolved_media_type = media_type or detect_media_type(resolved_path)
    effective_source_id = source_id or resolved_path.stem or "source"

    return SourceManifest(
        source_id=effective_source_id,
        filename=resolved_path.name,
        file_path=rel_path or str(file_path),
        byte_size=byte_size,
        sha256=sha256_hash,
        media_type=resolved_media_type,
        metadata=metadata or {},
    )


def ingest_file(
    file_path: Union[str, Path],
    source_id: Optional[str] = None,
    corpus_root: Optional[Union[str, Path]] = None,
    media_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> IngestionResult:
    """Ingest a physical file safely, returning an IngestionResult.

    Never raises unhandled file system exceptions; encapsulates all validation,
    I/O, and path resolution errors into structured IngestionResult with status=FAILED.
    """
    effective_source_id = source_id or (
        Path(file_path).stem if file_path and str(file_path).strip() else "unknown_source"
    )


    if not file_path or not str(file_path).strip():
        return IngestionResult(
            source_id=effective_source_id,
            status=IngestionStatus.FAILED,
            error=IngestionError(
                code="EMPTY_PATH",
                message="File path cannot be empty.",
                details={"file_path": str(file_path)},
            ),
            metadata=metadata or {},
        )

    try:
        manifest = create_source_manifest(
            file_path=file_path,
            source_id=source_id,
            corpus_root=corpus_root,
            media_type=media_type,
            metadata=metadata,
            chunk_size=chunk_size,
        )
        return IngestionResult(
            source_id=manifest.source_id,
            status=IngestionStatus.COMPLETED,
            manifest=manifest,
            metadata=metadata or {},
        )
    except FileNotFoundError as exc:
        return IngestionResult(
            source_id=effective_source_id,
            status=IngestionStatus.FAILED,
            error=IngestionError(
                code="FILE_NOT_FOUND",
                message=str(exc),
                details={"file_path": str(file_path)},
            ),
            metadata=metadata or {},
        )
    except IsADirectoryError as exc:
        return IngestionResult(
            source_id=effective_source_id,
            status=IngestionStatus.FAILED,
            error=IngestionError(
                code="NOT_A_FILE",
                message=str(exc),
                details={"file_path": str(file_path)},
            ),
            metadata=metadata or {},
        )
    except PermissionError as exc:
        return IngestionResult(
            source_id=effective_source_id,
            status=IngestionStatus.FAILED,
            error=IngestionError(
                code="PERMISSION_DENIED",
                message=str(exc),
                details={"file_path": str(file_path)},
            ),
            metadata=metadata or {},
        )
    except ValueError as exc:
        if "outside corpus root" in str(exc):
            code = "PATH_TRAVERSAL_DETECTED"
        elif "chunk_size" in str(exc):
            code = "INVALID_CHUNK_SIZE"
        else:
            code = "INVALID_PATH"
        return IngestionResult(
            source_id=effective_source_id,
            status=IngestionStatus.FAILED,
            error=IngestionError(
                code=code,
                message=str(exc),
                details={"file_path": str(file_path), "corpus_root": str(corpus_root) if corpus_root else None},
            ),
            metadata=metadata or {},
        )

    except OSError as exc:
        return IngestionResult(
            source_id=effective_source_id,
            status=IngestionStatus.FAILED,
            error=IngestionError(
                code="IO_ERROR",
                message=f"I/O error during file ingestion: {exc}",
                details={"file_path": str(file_path)},
            ),
            metadata=metadata or {},
        )
