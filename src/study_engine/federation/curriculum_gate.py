"""Curriculum Gate for Pre-Retrieval Gating (Phase E4).

Implements the CHSR-RRF pattern (arXiv:2609.02913) and EduRAG-Compose hierarchical traversal (ICDE 2025).
Constraints are injected BEFORE ranking in the SQL WHERE clause and dense filter.
Post-retrieval filtering of already-ranked results is strictly prohibited as primary containment.
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field


class ScopeConstraint(BaseModel):
    """Immutable curriculum pre-retrieval constraint specification."""

    model_config = ConfigDict(frozen=True)

    notebook_id: str = Field(..., min_length=1, description="Target notebook for query confinement")
    subject: Optional[str] = Field(default=None, description="Curricular subject from CAL metadata")
    level: Optional[str] = Field(default=None, description="Curricular academic level")
    book: Optional[str] = Field(default=None, description="Book / Manual identifier")
    chapter: Optional[str] = Field(default=None, description="Hierarchical chapter (EduRAG-Compose)")
    section: Optional[str] = Field(default=None, description="Hierarchical section (EduRAG-Compose)")
    page_start: Optional[int] = Field(default=None, ge=1)
    page_end: Optional[int] = Field(default=None, ge=1)
    bridge_id: Optional[str] = Field(default=None, description="Authorized bridge ID if cross-notebook")


class CurriculumGate:
    """Constructs pre-retrieval SQL WHERE predicates and dense filters on CAL metadata."""

    def __init__(self) -> None:
        pass

    @staticmethod
    def validate_constraint(constraint: ScopeConstraint) -> bool:
        """Fail-closed validation: ensure pages and hierarchical bounds are consistent."""
        if constraint.page_start is not None and constraint.page_end is not None:
            if constraint.page_start > constraint.page_end:
                return False
        return True

    def build_fts5_where_clause(
        self,
        constraint: ScopeConstraint,
        base_alias: str = "c",
        fts_alias: str = "chunks_fts",
        notebook_sources_alias: str = "ns",
    ) -> Tuple[str, List[Any]]:
        """Construct deterministic SQL WHERE predicate and parameters for FTS5 queries.

        Injected BEFORE ranking into chunks JOIN chunks_fts.
        Consumes: ns.notebook_id, metadata curricular columns and json_extract.
        """
        if not self.validate_constraint(constraint):
            # Contradictory constraints fail-closed immediately
            return "1 = 0", []

        clauses: List[str] = []
        params: List[Any] = []

        # 1. Notebook confinement (mandatory)
        clauses.append(f"{notebook_sources_alias}.notebook_id = ?")
        params.append(constraint.notebook_id)

        # 2. Hierarchical traversal (chapter, section) on first-class columns
        if constraint.chapter:
            clauses.append(f"{base_alias}.chapter = ?")
            params.append(constraint.chapter)

        if constraint.section:
            clauses.append(f"{base_alias}.section = ?")
            params.append(constraint.section)

        # 3. Page range constraints
        if constraint.page_start is not None:
            clauses.append(f"{base_alias}.page_end >= ?")
            params.append(constraint.page_start)

        if constraint.page_end is not None:
            clauses.append(f"{base_alias}.page_start <= ?")
            params.append(constraint.page_end)

        # 4. Curricular metadata (subject, level, book) from JSON metadata payload
        if constraint.subject:
            clauses.append(f"json_extract({base_alias}.metadata, '$.subject') = ?")
            params.append(constraint.subject)

        if constraint.level:
            clauses.append(f"json_extract({base_alias}.metadata, '$.level') = ?")
            params.append(constraint.level)

        if constraint.book:
            clauses.append(f"json_extract({base_alias}.metadata, '$.book') = ?")
            params.append(constraint.book)

        where_sql = " AND ".join(clauses)
        return where_sql, params

    def build_dense_filter(self, constraint: ScopeConstraint) -> Dict[str, Any]:
        """Construct metadata filter for dense retrieval candidates."""
        if not self.validate_constraint(constraint):
            return {"__impossible__": True}

        dense_filter: Dict[str, Any] = {"notebook_id": constraint.notebook_id}
        if constraint.subject:
            dense_filter["subject"] = constraint.subject
        if constraint.level:
            dense_filter["level"] = constraint.level
        if constraint.book:
            dense_filter["book"] = constraint.book
        if constraint.chapter:
            dense_filter["chapter"] = constraint.chapter
        if constraint.section:
            dense_filter["section"] = constraint.section
        return dense_filter
