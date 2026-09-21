"""Search domain contracts: SearchResult for lexical and hybrid retrieval."""

from typing import Optional
from pydantic import Field

from study_engine.contracts.base import BaseContract


class SearchResult(BaseContract):
    """Canonical search result representing a ranked chunk hit."""

    chunk_id: str = Field(..., min_length=1, description="Unique chunk identifier")
    document_id: str = Field(..., min_length=1, description="Parent document identifier")
    source_id: str = Field(..., min_length=1, description="Parent source identifier")
    score: float = Field(..., description="Relevance score (higher is more relevant)")
    snippet: str = Field(..., description="Highlighted contextual excerpt")
    content: str = Field(..., description="Full text content of the chunk")
    index: int = Field(..., ge=0, description="Positional index within document")
    page_start: Optional[int] = Field(default=None, description="Starting page in physical source")
    page_end: Optional[int] = Field(default=None, description="Ending page in physical source")

