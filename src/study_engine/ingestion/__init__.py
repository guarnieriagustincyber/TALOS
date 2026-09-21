"""Source Ingestion subsystem."""

from study_engine.ingestion.catalog import SourceCatalog
from study_engine.ingestion.chunking import ChunkConfig, chunk_document
from study_engine.ingestion.document_catalog import DocumentCatalog
from study_engine.ingestion.document_ingestion import (
    ingest_document,
    slugify_filename,
)
from study_engine.ingestion.file_ingestion import (
    compute_file_sha256,
    create_source_manifest,
    detect_media_type,
    ingest_file,
)

__all__ = [
    "SourceCatalog",
    "DocumentCatalog",
    "ChunkConfig",
    "chunk_document",
    "compute_file_sha256",
    "create_source_manifest",
    "detect_media_type",
    "ingest_file",
    "ingest_document",
    "slugify_filename",
]
