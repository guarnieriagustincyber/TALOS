"""Fusion strategy contracts and implementations for hybrid retrieval."""

import math
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import Field, field_validator

from study_engine.contracts.base import BaseContract
from study_engine.contracts.retrieval import ScoredCandidate


class FusedCandidate(BaseContract):
    """An intermediate fused candidate tracking full algorithmic provenance."""

    chunk_id: str = Field(..., min_length=1)
    document_id: str = Field(..., min_length=1)
    source_id: str = Field(..., min_length=1)
    notebook_id: str = Field(..., min_length=1)
    score: float = Field(..., description="Combined fusion score")
    content: str = Field(..., min_length=1)
    lexical_rank: Optional[int] = Field(default=None, ge=1)
    dense_rank: Optional[int] = Field(default=None, ge=1)
    lexical_score: Optional[float] = Field(default=None)
    dense_score: Optional[float] = Field(default=None)
    page_start: Optional[int] = Field(default=None, ge=0)
    page_end: Optional[int] = Field(default=None, ge=0)
    pos_index: Optional[int] = Field(default=None, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("score", "lexical_score", "dense_score")
    @classmethod
    def validate_finite_score(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and (math.isnan(v) or math.isinf(v)):
            raise ValueError("Scores must be finite numbers.")
        return v


@runtime_checkable
class FusionStrategy(Protocol):
    """Protocol for fusing candidate rankings from retrieval sources."""

    def fuse(

        self,
        lexical_items: List[ScoredCandidate],
        dense_items: List[ScoredCandidate],
        top_k: int,
    ) -> List[FusedCandidate]:
        """Fuse lexical and dense candidate lists into an ordered ranking."""
        ...


class ReciprocalRankFusion:
    """Scale-agnostic fusion strategy using Reciprocal Rank Fusion (RRF).

    Formula:
        RRF(d) = sum(w_m / (k + rank_m(d))) for all retrieval streams m
        where d appears. If d does not appear in a stream, its rank in that
        stream is None and contributes 0 to the score (no arbitrary penalty).
    """

    def __init__(
        self,
        k: int = 60,
        lexical_weight: float = 1.0,
        dense_weight: float = 1.0,
    ) -> None:
        if k <= 0:
            raise ValueError(f"RRF smoothing constant k must be > 0, got {k}.")
        if lexical_weight < 0.0 or dense_weight < 0.0:
            raise ValueError("Weights cannot be negative.")
        if lexical_weight == 0.0 and dense_weight == 0.0:
            raise ValueError("At least one weight must be positive.")

        self.k = k
        self.lexical_weight = lexical_weight
        self.dense_weight = dense_weight

    def fuse(
        self,
        lexical_items: List[ScoredCandidate],
        dense_items: List[ScoredCandidate],
        top_k: int,
    ) -> List[FusedCandidate]:
        """Fuse candidates deterministically using RRF."""
        if top_k <= 0:
            return []

        # Accumulate score and metadata per chunk_id
        entry_map: Dict[str, Dict[str, Any]] = {}

        # 1. Process Lexical Stream
        for item in lexical_items:
            cid = item.chunk_id
            reciprocal = self.lexical_weight / (self.k + item.rank)
            entry_map[cid] = {
                "chunk_id": cid,
                "document_id": item.document_id,
                "source_id": item.source_id,
                "notebook_id": item.notebook_id,
                "content": item.content,
                "page_start": item.page_start,
                "page_end": item.page_end,
                "pos_index": item.pos_index,
                "metadata": dict(item.metadata),
                "score": reciprocal,
                "lexical_rank": item.rank,
                "dense_rank": None,
                "lexical_score": item.score,
                "dense_score": None,
            }

        # 2. Process Dense Stream
        for item in dense_items:
            cid = item.chunk_id
            reciprocal = self.dense_weight / (self.k + item.rank)
            if cid in entry_map:
                entry = entry_map[cid]
                entry["score"] += reciprocal
                entry["dense_rank"] = item.rank
                entry["dense_score"] = item.score
            else:
                entry_map[cid] = {
                    "chunk_id": cid,
                    "document_id": item.document_id,
                    "source_id": item.source_id,
                    "notebook_id": item.notebook_id,
                    "content": item.content,
                    "page_start": item.page_start,
                    "page_end": item.page_end,
                    "pos_index": item.pos_index,
                    "metadata": dict(item.metadata),
                    "score": reciprocal,
                    "lexical_rank": None,
                    "dense_rank": item.rank,
                    "lexical_score": None,
                    "dense_score": item.score,
                }

        # 3. Deterministic Sorting
        # Primary: Score DESC
        # Secondary: Lexical Rank ASC (prefer exact match on ties)
        # Tertiary: Dense Rank ASC
        # Quaternary: chunk_id ASC (pure lexicographical determinism)
        def sort_key(e: Dict[str, Any]) -> Any:
            lex_r = (
                e["lexical_rank"]
                if e["lexical_rank"] is not None
                else float("inf")
            )
            dense_r = (
                e["dense_rank"]
                if e["dense_rank"] is not None
                else float("inf")
            )
            return (-e["score"], lex_r, dense_r, e["chunk_id"])

        sorted_entries = sorted(entry_map.values(), key=sort_key)

        top_entries = sorted_entries[:top_k]

        return [FusedCandidate.model_validate(entry) for entry in top_entries]
