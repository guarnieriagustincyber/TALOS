"""Contracts for the lightweight Gate 2 scope-aware benchmark."""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import Field, field_validator, model_validator

from study_engine.contracts.base import BaseContract


class Gate2OracleType(str, Enum):
    """The only oracle classes accepted by the Gate 2 benchmark."""

    POSITIVE_IN_SCOPE = "positive_in_scope"
    OOD_GLOBAL = "ood_global"
    NEGATIVE_BY_SCOPE = "negative_by_scope"


class Gate2Query(BaseContract):
    """A query with an explicit scope and evaluation oracle."""

    query_id: str = Field(..., min_length=1)
    scope: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)
    oracle_type: Gate2OracleType
    previous_scope: Optional[str] = None
    scope_decision: Optional[str] = None
    qrels_status: str = "pending"
    qrels_provenance: str = "historical"
    reviewer: Optional[str] = None
    notes: Optional[str] = None
    kc_ids: List[str] = Field(default_factory=list)
    topic_anchors: List[str] = Field(default_factory=list)
    scope_decision_id: Optional[str] = None

    @field_validator("query_id", "scope", "query", "previous_scope", "scope_decision")
    @classmethod
    def validate_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Text fields cannot be blank")
        return value

    @model_validator(mode="after")
    def validate_scope_change(self) -> "Gate2Query":
        if self.previous_scope and self.previous_scope != self.scope:
            if not self.scope_decision:
                raise ValueError(
                    f"Query {self.query_id!r} changes scope without a decision"
                )
        return self


class Gate2Dataset(BaseContract):
    """Versioned query records; qrels are validated separately."""

    version: str = Field(..., min_length=1)
    queries: List[Gate2Query] = Field(default_factory=list)
    metadata: Dict[str, object] = Field(default_factory=dict)

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Dataset version cannot be blank")
        return value

    @model_validator(mode="after")
    def validate_unique_query_ids(self) -> "Gate2Dataset":
        ids = [query.query_id for query in self.queries]
        if len(ids) != len(set(ids)):
            raise ValueError("Dataset contains duplicate query IDs")
        return self
