"""Contracts for Subsystem S3.2: Oracle Benchmark Dataset."""

from enum import Enum, IntEnum
from typing import Any, Dict, List, Set
from pydantic import Field, field_validator, model_validator

from study_engine.contracts.base import BaseContract


class BenchmarkCategory(str, Enum):
    """Closed categories for the retrieval evaluation benchmark."""

    CODE_SYMBOL = "CODE_SYMBOL"
    DEFINITION = "DEFINITION"
    PARAPHRASE = "PARAPHRASE"
    DIACRITICS_VARIANTS = "DIACRITICS_VARIANTS"
    AMBIGUOUS = "AMBIGUOUS"
    CURRICULAR_LEAKAGE = "CURRICULAR_LEAKAGE"


class RelevanceGrade(IntEnum):
    """Discrete relevance grades for benchmark evaluation."""

    PARTIAL = 1
    DIRECT = 2


class RelevantChunk(BaseContract):
    """Reference to an authoritative chunk relevant to an evaluation query."""

    chunk_id: str = Field(
        ...,
        min_length=1,
        description="Physical chunk identifier existing in reference corpus",
    )
    grade: RelevanceGrade = Field(
        ...,
        description="Relevance grade (1 = PARTIAL, 2 = DIRECT)",
    )
    rationale: str = Field(
        ...,
        min_length=1,
        description="Explicit justification for assigning this grade",
    )

    @field_validator("chunk_id", "rationale")
    @classmethod
    def validate_not_blank(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or blank.")
        return cleaned


class OracleQuery(BaseContract):
    """Specification of an evaluation query in the Oracle Benchmark."""

    id: str = Field(
        ...,
        min_length=1,
        description="Unique query identifier (e.g. 'oracle-q01')",
    )
    notebook_id: str = Field(
        ...,
        min_length=1,
        description="Authoritative notebook scope for this query",
    )
    query: str = Field(
        ...,
        min_length=1,
        description="Query string under evaluation",
    )
    category: BenchmarkCategory = Field(
        ...,
        description="Closed benchmark evaluation category",
    )
    relevant: List[RelevantChunk] = Field(
        default_factory=list,
        description="Authoritative relevant chunks",
    )
    rationale: str = Field(
        ...,
        min_length=1,
        description="Detailed pedagogical intent and expected evaluation",
    )

    @field_validator("id", "notebook_id", "query", "rationale")
    @classmethod
    def validate_not_blank(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("String fields cannot be empty or blank.")
        return cleaned

    @model_validator(mode="after")
    def validate_invariants(self) -> "OracleQuery":
        # Invariant 1: No duplicate chunk_ids in relevant list
        seen_chunk_ids: Set[str] = set()
        for r in self.relevant:
            if r.chunk_id in seen_chunk_ids:
                raise ValueError(
                    f"Duplicate chunk_id '{r.chunk_id}' in query '{self.id}'."
                )
            seen_chunk_ids.add(r.chunk_id)

        # Invariant 2: CURRICULAR_LEAKAGE must have relevant == []
        if self.category == BenchmarkCategory.CURRICULAR_LEAKAGE:
            if len(self.relevant) > 0:
                raise ValueError(
                    f"Query '{self.id}' is categorized as CURRICULAR_LEAKAGE "
                    f"but has {len(self.relevant)} relevant chunks. "
                    "Curricular leakage queries must have an empty "
                    "relevant list."
                )

        return self


class OracleDataset(BaseContract):
    """Immutable collection of benchmark queries forming ground truth."""

    version: str = Field(
        ...,
        min_length=1,
        description="Dataset semantic version (e.g. '1.0.0')",
    )
    queries: List[OracleQuery] = Field(
        default_factory=list,
        description="List of evaluation queries",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dataset provenance and environment metadata",
    )

    @field_validator("version")
    @classmethod
    def validate_version_not_blank(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Dataset version cannot be empty or blank.")
        return cleaned

    @model_validator(mode="after")
    def validate_query_id_uniqueness(self) -> "OracleDataset":
        seen_ids: Set[str] = set()
        for q in self.queries:
            if q.id in seen_ids:
                raise ValueError(
                    f"Duplicate query ID '{q.id}' in OracleDataset."
                )
            seen_ids.add(q.id)
        return self
