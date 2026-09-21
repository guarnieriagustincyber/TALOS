"""Domain contracts for Subsystem S3: Hybrid Retrieval Pipeline."""

from enum import Enum
import math
from typing import Any, Dict, List, Optional
from pydantic import Field, field_validator, model_validator

from study_engine.contracts.base import BaseContract


class RetrievalStrategy(str, Enum):
    """Execution strategy for knowledge retrieval."""

    LEXICAL = "lexical"
    DENSE = "dense"
    HYBRID = "hybrid"


class RetrievalRequest(BaseContract):
    """Specification of a retrieval query scoped to an authoritative notebook."""

    query: str = Field(..., min_length=1, description="Search query string in natural language or technical code")
    notebook_id: str = Field(..., min_length=1, description="Mandatory notebook identifier enforcing curricular isolation")
    top_k: int = Field(default=10, ge=1, le=100, description="Maximum number of candidate chunks to retrieve")
    source_ids: Optional[List[str]] = Field(default=None, description="Optional filter to restrict retrieval to specific sources")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional filter to restrict retrieval to specific documents")
    strategy: RetrievalStrategy = Field(default=RetrievalStrategy.LEXICAL, description="Retrieval strategy to apply")

    @field_validator("query")
    @classmethod
    def validate_query_not_blank(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Query string cannot be empty or contain only whitespace.")
        return cleaned

    @field_validator("notebook_id")
    @classmethod
    def validate_notebook_not_blank(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Notebook ID cannot be empty or contain only whitespace.")
        return cleaned

    @field_validator("source_ids", "document_ids")
    @classmethod
    def validate_id_lists(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        cleaned_list: List[str] = []
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("Filter ID lists cannot contain empty or blank strings.")
            cleaned_list.append(item.strip())
        return cleaned_list


class ScoredCandidate(BaseContract):
    """An individual chunk candidate ranked and scored by the retrieval pipeline."""

    chunk_id: str = Field(..., min_length=1, description="Unique chunk identifier")
    document_id: str = Field(..., min_length=1, description="Parent document identifier")
    source_id: str = Field(..., min_length=1, description="Parent source identifier")
    notebook_id: str = Field(..., min_length=1, description="Authoritative notebook to which this candidate belongs")
    rank: int = Field(..., ge=1, description="1-indexed deterministic ordinal position in the final ranking")
    score: float = Field(
        ...,
        description="Ranking/fusion score. Scale is strategy-dependent and NOT guaranteed to be bounded to [0, 1].",
    )
    content: str = Field(..., min_length=1, description="Exact textual content of the chunk")
    lexical_score: Optional[float] = Field(default=None, description="Raw BM25 score if lexical retrieval was executed")
    dense_score: Optional[float] = Field(default=None, description="Raw vector similarity score if dense retrieval was executed")
    retrieval_method: str = Field(..., min_length=1, description="Algorithmic method that produced this candidate (e.g., 'lexical', 'dense', 'fusion_rrf')")
    page_start: Optional[int] = Field(default=None, ge=0, description="Starting page in physical source document")
    page_end: Optional[int] = Field(default=None, ge=0, description="Ending page in physical source document")
    pos_index: Optional[int] = Field(default=None, ge=0, description="Ordinal chunk sequence index within parent document")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata (chapter, section, tags, etc.)")

    @property
    def text(self) -> str:
        """Alias for content to support downstream consumers expecting .text."""
        return self.content

    @field_validator("score", "lexical_score", "dense_score")
    @classmethod
    def validate_finite_scores(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (math.isnan(v) or math.isinf(v)):
            raise ValueError("Scores must be finite numbers (NaN and Inf are forbidden).")
        return v


class RetrievalDiagnostics(BaseContract):
    """Execution telemetry and candidate metrics for a retrieval operation."""

    lexical_candidates_count: Optional[int] = Field(default=None, ge=0, description="Number of candidates considered by lexical retriever")
    dense_candidates_count: Optional[int] = Field(default=None, ge=0, description="Number of candidates considered by dense retriever")
    unique_candidates_count: int = Field(default=0, ge=0, description="Number of unique candidates evaluated during ranking/fusion")
    latencies_ms: Dict[str, float] = Field(default_factory=dict, description="Latency breakdown in milliseconds (e.g. {'lexical_ms': 1.2, 'total_ms': 3.4})")
    rejection_reason: Optional[str] = Field(default=None, description="Reason for zero candidates returned (e.g. 'QUERY_ALL_STOPWORDS')")


class RetrievalResponse(BaseContract):
    """Complete, verified response from the retrieval pipeline."""

    query: str = Field(..., min_length=1, description="Original cleaned query")
    notebook_id: str = Field(..., min_length=1, description="Authoritative notebook identifier")
    strategy_used: RetrievalStrategy = Field(..., description="Actual retrieval strategy applied")
    items: List[ScoredCandidate] = Field(default_factory=list, description="Ordered candidate chunks (sorted by rank ASC)")
    diagnostics: RetrievalDiagnostics = Field(default_factory=RetrievalDiagnostics, description="Performance and candidate telemetry")

    @model_validator(mode="after")
    def validate_invariants(self) -> "RetrievalResponse":
        # Invariant 1: Curricular Isolation Guarantee (every candidate must match response notebook_id)
        for idx, candidate in enumerate(self.items):
            if candidate.notebook_id != self.notebook_id:
                raise ValueError(
                    f"Curricular isolation violated at index {idx}: candidate '{candidate.chunk_id}' "
                    f"has notebook_id '{candidate.notebook_id}', which does not match response notebook_id '{self.notebook_id}'."
                )

            # Invariant 2: Deterministic 1-indexed ordinal ranks
            expected_rank = idx + 1
            if candidate.rank != expected_rank:
                raise ValueError(
                    f"Ranking sequence invariant violated at index {idx}: candidate '{candidate.chunk_id}' "
                    f"has rank {candidate.rank}, expected rank {expected_rank}."
                )

        return self
