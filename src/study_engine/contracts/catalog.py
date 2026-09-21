"""Catalog contract definitions: SourceRecord and related catalog exceptions."""

from typing import Any, Dict, Optional
from pydantic import Field, model_validator

from study_engine.contracts.base import BaseContract
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.source import Source


class SourceCatalogError(Exception):
    """Base exception for source catalog operations."""


class SourceNotFoundError(SourceCatalogError):
    """Raised when a requested source_id is not found in the catalog."""

    def __init__(self, source_id: str) -> None:
        super().__init__(f"Source '{source_id}' is not registered in the catalog.")
        self.source_id = source_id


class SourceConflictError(SourceCatalogError):
    """Raised when registering a source_id with a conflicting SHA-256 hash or semantic divergence."""

    def __init__(
        self,
        source_id: str,
        existing_sha256: str,
        new_sha256: str,
        reason: Optional[str] = None,
    ) -> None:
        msg = (
            f"Conflict for source '{source_id}': {reason}"
            if reason
            else (
                f"Conflict for source '{source_id}': existing SHA-256 '{existing_sha256}' "
                f"differs from incoming SHA-256 '{new_sha256}'."
            )
        )
        super().__init__(msg)
        self.source_id = source_id
        self.existing_sha256 = existing_sha256
        self.new_sha256 = new_sha256
        self.reason = reason


class DocumentCatalogError(Exception):
    """Base exception for document catalog operations."""


class DocumentNotFoundError(DocumentCatalogError):
    """Raised when a requested document_id is not found in the catalog."""

    def __init__(self, document_id: str) -> None:
        super().__init__(f"Document '{document_id}' is not registered in the catalog.")
        self.document_id = document_id


class DocumentConflictError(DocumentCatalogError):
    """Raised when registering a document_id with conflicting attributes or semantic divergence."""

    def __init__(
        self,
        document_id: str,
        reason: Optional[str] = None,
    ) -> None:
        msg = (
            f"Conflict for document '{document_id}': {reason}"
            if reason
            else f"Conflict for document '{document_id}': incoming document differs from registered document."
        )
        super().__init__(msg)
        self.document_id = document_id
        self.reason = reason


class ChunkCatalogError(Exception):
    """Base exception for chunk storage operations."""


class ChunkNotFoundError(ChunkCatalogError):
    """Raised when a requested chunk_id is not found in storage."""

    def __init__(self, chunk_id: str) -> None:
        super().__init__(f"Chunk '{chunk_id}' is not registered in storage.")
        self.chunk_id = chunk_id


class ChunkConflictError(ChunkCatalogError):
    """Raised when registering chunks with conflicting attributes or semantic divergence."""

    def __init__(
        self,
        chunk_id: str,
        reason: Optional[str] = None,
    ) -> None:
        msg = (
            f"Conflict for chunk '{chunk_id}': {reason}"
            if reason
            else f"Conflict for chunk '{chunk_id}': incoming chunk differs from registered chunk."
        )
        super().__init__(msg)
        self.chunk_id = chunk_id
        self.reason = reason


class NotebookCatalogError(Exception):
    """Base exception for notebook storage and catalog operations."""


class NotebookNotFoundError(NotebookCatalogError):
    """Raised when a requested notebook_id is not found."""

    def __init__(self, notebook_id: str) -> None:
        super().__init__(f"Notebook '{notebook_id}' is not registered.")
        self.notebook_id = notebook_id


class NotebookConflictError(NotebookCatalogError):
    """Raised when registering a notebook with conflicting attributes."""

    def __init__(
        self,
        notebook_id: str,
        reason: Optional[str] = None,
    ) -> None:
        msg = (
            f"Conflict for notebook '{notebook_id}': {reason}"
            if reason
            else f"Conflict for notebook '{notebook_id}': incoming notebook differs from registered notebook."
        )
        super().__init__(msg)
        self.notebook_id = notebook_id
        self.reason = reason






class SourceRecord(BaseContract):
    """Canonical catalog entry binding a logical source_id to its physical manifest."""

    source_id: str = Field(..., min_length=1, description="Canonical logical source identifier")
    manifest: SourceManifest = Field(..., description="Physical file manifest with SHA-256 integrity")
    source: Optional[Source] = Field(default=None, description="Optional conceptual knowledge source metadata")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Catalog-level operational metadata")

    @model_validator(mode="after")
    def validate_source_id_consistency(self) -> "SourceRecord":
        """Enforce strict identity consistency across root, manifest, and conceptual source."""
        if self.source_id != self.manifest.source_id:
            raise ValueError(
                f"SourceRecord source_id '{self.source_id}' does not match manifest.source_id '{self.manifest.source_id}'."
            )
        if self.source is not None and self.source.source_id != self.source_id:
            raise ValueError(
                f"SourceRecord source_id '{self.source_id}' does not match source.source_id '{self.source.source_id}'."
            )
        return self
