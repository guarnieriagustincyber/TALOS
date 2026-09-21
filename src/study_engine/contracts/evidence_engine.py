"""Contracts for Subsystem S4.1: Evidence Engine and Context Packer.

These models govern the deterministic classification, provenance attribution,
citation indexing, and epistemic boundaries applied to retrieved candidates
before LLM ingestion.
"""

from enum import Enum
import re
from typing import Dict, List, Optional
from pydantic import ConfigDict, Field, field_validator

from study_engine.contracts.base import BaseContract
from study_engine.contracts.enums import SourceRole

_HEX_64_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class EvidenceEngineError(Exception):
    """Base exception for evidence engine failures."""

    pass


class EvidenceAssessmentError(EvidenceEngineError):
    """Raised when assessed grades violate invariants or reference chunks."""

    pass


class CurricularIsolationError(EvidenceEngineError):
    """Raised when evidence violates authoritative notebook scoping."""

    pass


class BudgetError(EvidenceEngineError):
    """Raised when character budget is invalid or below minimal policy size."""

    pass


class EvidenceGrade(str, Enum):
    """Discrete directness grade for an evidence item."""

    DIRECT = "DIRECT"
    CONTEXTUAL = "CONTEXTUAL"
    UNASSESSED = "UNASSESSED"


class GroundingDecision(str, Enum):
    """Epistemic grounding determination for evidence collection."""

    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNASSESSED_EVIDENCE = "UNASSESSED_EVIDENCE"
    NO_CANDIDATES = "NO_CANDIDATES"


class CoverageStatus(str, Enum):
    """Discrete evidence coverage classification for a sub-topic."""

    SUFFICIENT = "SUFFICIENT"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"


class EpistemicClaimType(str, Enum):
    """Authoritative claim types permissible under pedagogical governance."""

    DIRECT_FACTUAL_ASSERTION = "DIRECT_FACTUAL_ASSERTION"
    CANONICAL_DEFINITION = "CANONICAL_DEFINITION"
    CONTEXTUAL_EXPLANATION = "CONTEXTUAL_EXPLANATION"
    BACKGROUND_OVERVIEW = "BACKGROUND_OVERVIEW"
    CITE_EVIDENCE = "CITE_EVIDENCE"
    QUALIFIED_EXPLANATION = "QUALIFIED_EXPLANATION"


class CitationRecord(BaseContract):
    """Strongly-typed metadata record for a packaged citation."""

    model_config = ConfigDict(frozen=True)

    citation_id: str = Field(
        ...,
        min_length=1,
        description="Deterministic citation key (e.g. 'E1', 'E2')",
    )
    chunk_id: str = Field(..., min_length=1)
    document_id: str = Field(..., min_length=1)
    source_id: str = Field(..., min_length=1)
    source_title: str = Field(..., min_length=1)
    author: Optional[str] = None
    page_start: Optional[int] = Field(default=None, ge=0)
    page_end: Optional[int] = Field(default=None, ge=0)
    source_role: Optional[SourceRole] = Field(
        default=None,
        description="Source role if known (None indicates unassessed role)",
    )
    priority: Optional[int] = Field(
        default=None,
        ge=1,
        description="Source priority if known (None = unassessed)",
    )
    grade: EvidenceGrade = EvidenceGrade.UNASSESSED
    trust_level: str = Field(
        default="canonical",
        description="Provenance trust level ('canonical', 'unverified')",
    )

    content_hash: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="Cryptographic SHA-256 hash of the exact chunk content",
    )

    @field_validator("content_hash")
    @classmethod
    def validate_sha256(cls, v: str) -> str:
        clean = v.strip().lower()
        if not _HEX_64_PATTERN.match(clean):
            raise ValueError(
                f"content_hash must be a valid 64-char hex SHA-256 hash: {v}"
            )
        return clean


class EvaluatedEvidenceItem(BaseContract):
    """Evaluated evidence item before budget selection and citation."""

    model_config = ConfigDict(frozen=True)

    chunk_id: str = Field(..., min_length=1)

    document_id: str = Field(..., min_length=1)
    source_id: str = Field(..., min_length=1)
    source_title: str = Field(..., min_length=1)
    author: Optional[str] = None
    page_start: Optional[int] = Field(default=None, ge=0)
    page_end: Optional[int] = Field(default=None, ge=0)
    source_role: Optional[SourceRole] = None
    priority: Optional[int] = Field(default=None, ge=1)
    grade: EvidenceGrade = EvidenceGrade.UNASSESSED
    trust_level: str = Field(
        default="canonical",
        description="Provenance trust level ('canonical', 'unverified')",
    )
    content_hash: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="Cryptographic SHA-256 hash of the exact chunk content",
    )
    content: str = Field(..., min_length=1)
    retrieval_score: float
    retrieval_rank: int = Field(..., ge=1)
    retrieval_method: str = Field(..., min_length=1)

    @field_validator("content_hash")
    @classmethod
    def validate_sha256(cls, v: str) -> str:
        clean = v.strip().lower()
        if not _HEX_64_PATTERN.match(clean):
            raise ValueError(
                f"content_hash must be a valid 64-char hex SHA-256 hash: {v}"
            )
        return clean


class CitationManifest(BaseContract):
    """Immutable registry of all citations packaged for an interaction."""

    model_config = ConfigDict(frozen=True)

    records: Dict[str, CitationRecord] = Field(default_factory=dict)


class PackagedEvidenceUnit(BaseContract):
    """Individual verified evidence unit prepared for context packaging."""

    model_config = ConfigDict(frozen=True)

    citation: CitationRecord
    content: str = Field(..., min_length=1)
    retrieval_score: float
    retrieval_rank: int = Field(..., ge=1)
    retrieval_method: str = Field(..., min_length=1)


class SubQuery(BaseContract):
    """Individual decomposed sub-query representing a discrete semantic sub-topic."""

    model_config = ConfigDict(frozen=True)

    sub_query_id: str = Field(..., min_length=1, description="Unique sub-query identifier (e.g. 'sq-1')")
    text: str = Field(..., min_length=1, description="Decomposed search query string")
    intent: str = Field(default="", description="Pedagogical intent or sub-topic name")
    priority_score: float = Field(default=0.0, description="Pedagogical priority score")


class SubQueryDecomposition(BaseContract):
    """Proposal collection of decomposed sub-queries emitted by QueryDecomposer."""

    model_config = ConfigDict(frozen=True)

    original_query: str = Field(..., min_length=1)
    sub_queries: List[SubQuery] = Field(default_factory=list)
    is_fallback: bool = False
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class SubQueryCoverage(BaseContract):
    """Quality and depth evaluation of evidence coverage for a sub-query."""

    model_config = ConfigDict(frozen=True)

    sub_query_id: str = Field(..., min_length=1)
    sub_query_text: str = Field(..., min_length=1)
    status: CoverageStatus
    quality_score: float = Field(..., ge=0.0, le=1.0)
    chunks_count: int = Field(default=0, ge=0)
    source_ids: List[str] = Field(default_factory=list)


class EvidenceCoverageReport(BaseContract):
    """Pedagogical evidence coverage report indicating what can and cannot be grounded."""

    model_config = ConfigDict(frozen=True)

    sub_queries: List[SubQuery] = Field(default_factory=list)
    coverage: List[SubQueryCoverage] = Field(default_factory=list)
    overall_coverage_ratio: float = Field(default=1.0, ge=0.0, le=1.0)

    @property
    def has_missing(self) -> bool:
        return any(c.status == CoverageStatus.MISSING for c in self.coverage)

    @property
    def has_partial(self) -> bool:
        return any(c.status == CoverageStatus.PARTIAL for c in self.coverage)


class EvidencePacket(BaseContract):
    """Evaluated evidence collection emitted by EvidenceEngine."""

    model_config = ConfigDict(frozen=True)

    original_query: str = Field(..., min_length=1)
    normalized_query: str = Field(..., min_length=1)
    notebook_id: str = Field(..., min_length=1)
    grounding_decision: GroundingDecision
    evidence_items: List[EvaluatedEvidenceItem] = Field(default_factory=list)
    allowed_claims: List[EpistemicClaimType] = Field(default_factory=list)
    unsupported_claims: List[EpistemicClaimType] = Field(default_factory=list)
    abstention_required: bool = False
    abstention_reason: Optional[str] = None
    has_full_provenance: bool = False
    coverage_report: Optional[EvidenceCoverageReport] = None


class PackagedContext(BaseContract):
    """Final immutable prompt context emitted by ContextPacker."""

    model_config = ConfigDict(frozen=True)

    packet: EvidencePacket
    citation_manifest: CitationManifest
    packaged_units: List[PackagedEvidenceUnit] = Field(default_factory=list)
    formatted_context_block: str
    total_characters: int = Field(..., ge=0)
    was_truncated: bool = False
    excluded_units_count: int = Field(default=0, ge=0)
    epistemic_policy: str = Field(..., min_length=1)
    coverage_report: Optional[EvidenceCoverageReport] = None
