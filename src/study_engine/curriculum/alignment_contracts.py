"""Curricular Alignment Matrix contracts for Epistemic Isolation.

INVARIANTS:
1. Curricular alignment defines the authoritative epistemic boundary for each node.
2. Retrieval operations for a node MUST strictly be constrained to the allowed
   document scopes defined in this matrix (Fail-Closed).
3. Canonical matrix ID is an immutable 64-char SHA-256 digest of its canonical content.
4. All contracts are strictly frozen and immutable (frozen=True, extra="forbid").
"""

import hashlib
import json
from typing import Any, Dict, Tuple
from pydantic import ConfigDict, Field, model_validator

from study_engine.contracts.base import BaseContract


class CurricularDocumentScope(BaseContract):
    """Scoped document range authorized for a specific curricular node."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document_id: str = Field(
        ..., min_length=1, description="Unique identifier of authorized document"
    )
    page_start: int = Field(
        ..., ge=1, description="1-indexed inclusive starting page"
    )
    page_end: int = Field(
        ..., ge=1, description="1-indexed inclusive ending page"
    )
    is_primary: bool = Field(
        default=True,
        description="True if primary theoretical source; False if supplementary",
    )

    @model_validator(mode="after")
    def validate_page_boundaries(self) -> "CurricularDocumentScope":
        """Ensure page_end is greater than or equal to page_start."""
        if self.page_end < self.page_start:
            raise ValueError(
                f"page_end ({self.page_end}) must be >= page_start ({self.page_start}) "
                f"for document '{self.document_id}'."
            )
        return self


class CurricularNodeAlignment(BaseContract):
    """Mapping of a single curricular node to its authorized document scopes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    node_id: str = Field(
        ..., min_length=1, description="Roadmap node identifier (S5.1)"
    )
    allowed_documents: Tuple[CurricularDocumentScope, ...] = Field(
        ..., min_length=1, description="Ordered collection of authorized document scopes"
    )


def compute_canonical_matrix_id(
    matrix_id: str,
    roadmap_id: str,
    version: str,
    alignments: Dict[str, CurricularNodeAlignment],
) -> str:
    """Compute deterministic SHA-256 digest of alignment matrix content."""
    canonical_dict: Dict[str, Any] = {
        "matrix_id": matrix_id,
        "roadmap_id": roadmap_id,
        "version": version,
        "alignments": {
            k: {
                "node_id": alignments[k].node_id,
                "allowed_documents": [
                    {
                        "document_id": doc.document_id,
                        "page_start": doc.page_start,
                        "page_end": doc.page_end,
                        "is_primary": doc.is_primary,
                    }
                    for doc in sorted(
                        alignments[k].allowed_documents,
                        key=lambda d: (d.document_id, d.page_start, d.page_end),
                    )
                ],
            }
            for k in sorted(alignments.keys())
        },
    }
    encoded = json.dumps(
        canonical_dict,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class CurricularAlignmentMatrix(BaseContract):
    """Authoritative matrix binding a roadmap to epistemic document boundaries."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    matrix_id: str = Field(
        ..., min_length=1, description="Unique alignment matrix identifier"
    )
    roadmap_id: str = Field(
        ..., min_length=1, description="Associated roadmap identifier"
    )
    version: str = Field(
        ..., min_length=1, description="Semantic version string (e.g. 1.0.0)"
    )
    alignments: Dict[str, CurricularNodeAlignment] = Field(
        ..., min_length=1, description="Node alignments indexed by node_id"
    )
    canonical_matrix_id: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="Immutable 64-char SHA-256 digest of canonical matrix content",
    )

    @model_validator(mode="after")
    def validate_integrity(self) -> "CurricularAlignmentMatrix":
        """Verify internal consistency and canonical hash correctness."""
        for nid, alignment in self.alignments.items():
            if nid != alignment.node_id:
                raise ValueError(
                    f"Alignment key '{nid}' does not match node_id '{alignment.node_id}'."
                )

        expected_hash = compute_canonical_matrix_id(
            matrix_id=self.matrix_id,
            roadmap_id=self.roadmap_id,
            version=self.version,
            alignments=self.alignments,
        )
        if self.canonical_matrix_id != expected_hash:
            raise ValueError(
                f"canonical_matrix_id mismatch in '{self.matrix_id}'. "
                f"Declared: {self.canonical_matrix_id}, Expected: {expected_hash}"
            )
        return self
