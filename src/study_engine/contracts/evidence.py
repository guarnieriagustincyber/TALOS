"""Evidence contract."""

from typing import Any, Dict, Optional
from pydantic import Field

from study_engine.contracts.base import BaseContract
from study_engine.contracts.enums import EvidenceStatus


class Evidence(BaseContract):
    """Retrieved evidence claim and source grounding."""

    id: str = Field(..., min_length=1, description="Unique evidence identifier")
    claim: str = Field(..., min_length=1, description="Factual claim or question evaluated")
    status: EvidenceStatus = Field(..., description="Grounding status against corpus")
    content: Optional[str] = Field(default=None, description="Extracted quote or textual evidence")
    source_id: Optional[str] = Field(default=None, description="Source ID of the evidence")
    document_id: Optional[str] = Field(default=None, description="Document ID of the evidence")
    chunk_id: Optional[str] = Field(default=None, description="Chunk ID of the evidence")
    page: Optional[int] = Field(default=None, ge=1, description="Page reference")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata")
