"""Chunk contract."""

from typing import Any, Dict, Optional
from pydantic import Field

from study_engine.contracts.base import BaseContract


class Chunk(BaseContract):
    """Text chunk extracted from a Document for retrieval and context construction."""

    id: str = Field(..., min_length=1, description="Unique chunk identifier")
    document_id: str = Field(..., min_length=1, description="Reference to parent Document ID")
    source_id: str = Field(..., min_length=1, description="Reference to parent Source ID")
    content: str = Field(..., min_length=1, description="Text content of the chunk")
    page_start: Optional[int] = Field(default=None, ge=1, description="Start page number")
    page_end: Optional[int] = Field(default=None, ge=1, description="End page number")
    chapter: Optional[str] = Field(default=None, description="Chapter title or number")
    section: Optional[str] = Field(default=None, description="Section title or number")
    token_count: Optional[int] = Field(default=None, ge=0, description="Estimated token count")
    index: int = Field(default=0, ge=0, description="Position index within document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata")
