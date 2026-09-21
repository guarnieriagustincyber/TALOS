"""Ingestion contracts: source manifest, error detail, and ingestion result."""

from typing import Any, Dict, Optional
from pydantic import Field, model_validator

from study_engine.contracts.base import BaseContract
from study_engine.contracts.document import Document
from study_engine.contracts.enums import IngestionStatus


class SourceManifest(BaseContract):
    """Manifest representing physical file identity and integrity for a source."""

    source_id: str = Field(..., min_length=1, description="Associated conceptual Source identifier")
    filename: str = Field(..., min_length=1, description="Physical filename or logical relative name")
    byte_size: int = Field(..., ge=0, description="Size in bytes of the physical artifact (>= 0)")
    sha256: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[a-fA-F0-9]{64}$",
        description="SHA-256 hexadecimal hash string (64 hex characters)",
    )
    file_path: Optional[str] = Field(default=None, description="Optional path relative to study corpus root")
    media_type: Optional[str] = Field(default="application/pdf", description="MIME or media type of the file")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible operational or extraction metadata")


class IngestionError(BaseContract):
    """Structured error descriptor for failed ingestion operations."""

    code: str = Field(..., min_length=1, description="Machine-readable error category or code")
    message: str = Field(..., min_length=1, description="Human-readable diagnostic error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Optional structured context or parameters")


class IngestionResult(BaseContract):
    """Result and operational status descriptor for a source or document ingestion process."""

    source_id: str = Field(..., min_length=1, description="Identifier of the Source being ingested")
    status: IngestionStatus = Field(..., description="Current status of the ingestion process")
    manifest: Optional[SourceManifest] = Field(default=None, description="Source manifest descriptor if available")
    document_id: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Identifier of resulting Document artifact if ingestion completed",
    )
    document: Optional[Document] = Field(
        default=None,
        description="Resulting Document domain artifact if document ingestion completed",
    )
    error: Optional[IngestionError] = Field(
        default=None,
        description="Structured error details if ingestion failed",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Operational metadata")

    @model_validator(mode="after")
    def validate_status_invariants(self) -> "IngestionResult":
        """Enforce semantic consistency between ingestion status, errors, and generated artifacts."""
        if self.status == IngestionStatus.COMPLETED:
            if self.error is not None:
                raise ValueError("COMPLETED ingestion status cannot contain an error descriptor.")
            if self.document is not None:
                if self.document_id is not None and self.document_id != self.document.id:
                    raise ValueError(
                        f"document_id '{self.document_id}' does not match document.id '{self.document.id}'."
                    )
        elif self.status == IngestionStatus.FAILED:
            if self.error is None:
                raise ValueError("FAILED ingestion status requires an error descriptor.")
            if self.document_id is not None:
                raise ValueError("FAILED ingestion status cannot reference a generated document_id.")
            if self.document is not None:
                raise ValueError("FAILED ingestion status cannot reference a generated document.")
        elif self.status in (IngestionStatus.PENDING, IngestionStatus.PROCESSING):
            if self.error is not None:
                raise ValueError(f"{self.status.value} ingestion status cannot contain an error descriptor.")
            if self.document_id is not None:
                raise ValueError(
                    f"{self.status.value} ingestion status cannot reference a generated document_id before completion."
                )
            if self.document is not None:
                raise ValueError(
                    f"{self.status.value} ingestion status cannot reference a generated document before completion."
                )
        return self
