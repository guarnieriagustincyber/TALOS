"""Document contract."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import Field

from study_engine.contracts.base import BaseContract


class Document(BaseContract):
    """Document representation belonging to a Source."""

    id: str = Field(..., min_length=1, description="Unique document identifier")
    source_id: str = Field(..., min_length=1, description="Reference to parent Source ID")
    title: str = Field(..., min_length=1, description="Document title")
    content: Optional[str] = Field(default=None, description="Full text content if loaded in memory")
    path: Optional[str] = Field(default=None, description="File path relative to corpus or workspace")
    page_count: Optional[int] = Field(default=None, ge=0, description="Total page count")
    language: Optional[str] = Field(default="es", description="Language code")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
