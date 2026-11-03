"""Canonical provisional-only contracts for the isolated Colab adapter."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import Field, StrictBool, model_validator
from study_engine.contracts.base import BaseContract

TRUST = dict(trusted_for_rag=False, fidelity_certified=False, production_import_authorized=False)


def check_provisional(value):
    """Reject trust escalation even inside retained export metadata."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key in TRUST and item is not False:
                raise ValueError(f"{key} must be false for provisional packages")
            if key == "human_verified" and item is not False:
                raise ValueError("human_verified must be false")
            check_provisional(item)
    elif isinstance(value, list):
        for item in value:
            check_provisional(item)
    return value


class ProvisionalContract(BaseContract):
    trusted_for_rag: StrictBool = False
    fidelity_certified: StrictBool = False
    production_import_authorized: StrictBool = False

    @model_validator(mode="before")
    @classmethod
    def provisional_only(cls, data):
        return check_provisional(data)


class MultimodalElementType(str, Enum):
    TABLE = "table"
    FIGURE = "figure"
    FORMULA = "formula"
    PAGE = "page"


class CandidateStatus(str, Enum):
    CANDIDATE = "candidate"
    VERIFIED = "verified"
    REJECTED = "rejected"
    UNVERIFIED = "unverified"


class RelationType(str, Enum):
    CONTAINS = "contains"
    REFERENCES = "references"
    ON_SAME_PAGE = "on_same_page"
    CROSS_REFERENCE = "cross_reference"
    EXPLICIT_REFERENCE_CANDIDATE = "explicit_reference_candidate"
    UNKNOWN = "unknown"


class DocumentClassification(str, Enum):
    BODY = "body"
    TOC_OR_FRONT_MATTER = "toc_or_front_matter"
    EXERCISE = "exercise"
    REFERENCE = "reference"
    UNKNOWN = "unknown"


class MultimodalElement(ProvisionalContract):
    element_id: str = Field(min_length=1)
    element_type: MultimodalElementType
    document_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    page: int = Field(ge=1)
    candidate_section_id: Optional[str] = None
    pdf_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: Literal["candidate", "unverified", "CANDIDATE_UNVERIFIED", "PROVISIONAL_UNVERIFIED", "REVIEW_PLAUSIBLE", "REVIEW_AMBIGUOUS"] = "candidate"
    confidence: float = Field(default=0, ge=0, le=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class TableCandidate(MultimodalElement):
    element_type: Literal[MultimodalElementType.TABLE] = MultimodalElementType.TABLE
    table_id: str = Field(min_length=1)
    caption: Optional[str] = None
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    row_count: int = Field(default=0, ge=0)
    col_count: int = Field(default=0, ge=0)
    is_baseline: bool = False
    markdown: Optional[str] = None
    csv_path: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def dimensions(cls, data):
        data = dict(data)
        rows, headers = data.get("rows", []), data.get("headers", [])
        if rows:
            data["row_count"] = len(rows)
            data["col_count"] = len(headers) if headers else len(rows[0])
        return data


class FigureCandidate(MultimodalElement):
    element_type: Literal[MultimodalElementType.FIGURE] = MultimodalElementType.FIGURE
    figure_id: str = Field(min_length=1)
    caption: Optional[str] = None
    image_path: Optional[str] = None
    image_sha256: Optional[str] = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    mime_type: Optional[str] = "image/png"
    width: Optional[int] = Field(default=None, ge=0)
    height: Optional[int] = Field(default=None, ge=0)
    alt_text: Optional[str] = None


class FormulaCandidate(MultimodalElement):
    element_type: Literal[MultimodalElementType.FORMULA] = MultimodalElementType.FORMULA
    formula_id: str = Field(min_length=1)
    latex: str = Field(min_length=1)
    plain_text: Optional[str] = None
    context: Optional[str] = None
    variables: List[str] = Field(default_factory=list)


class PageEvidence(ProvisionalContract):
    page_id: Optional[str] = None
    document_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    page_number: int = Field(ge=1)
    pdf_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    text_content: Optional[str] = None
    chunk_ids: List[str] = Field(default_factory=list)
    table_ids: List[str] = Field(default_factory=list)
    figure_ids: List[str] = Field(default_factory=list)
    formula_ids: List[str] = Field(default_factory=list)
    is_preliminary: bool = False
    classification: Optional[DocumentClassification] = None
    multimodel_confidence: float = Field(default=0, ge=0, le=1)
    text_sha256: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ManifestFile(BaseContract):
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class SourceInputInfo(BaseContract):
    files: int = Field(default=0, ge=0)
    schema_version: Optional[str] = Field(default=None, alias="schema")
    sha256: Optional[str] = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    status: str = "PROVISIONAL_UNVERIFIED"


class ColabPackageManifest(ProvisionalContract):
    schema_version: Literal["TALOS_RECONCILE_PARALLEL_1.0"] = Field(alias="schema")
    status: Literal["PROVISIONAL_UNVERIFIED"] = "PROVISIONAL_UNVERIFIED"
    files: List[ManifestFile] = Field(default_factory=list)
    source_inputs: Dict[str, SourceInputInfo] = Field(default_factory=dict)
    package_id: Optional[str] = None
    created_at: Optional[datetime] = None
    documents_count: int = Field(default=0, ge=0)
    chunks_count: int = Field(default=0, ge=0)
    tables_baseline: int = Field(default=0, ge=0)
    tables_new: int = Field(default=0, ge=0)
    figures_count: int = Field(default=0, ge=0)
    formulas_count: int = Field(default=0, ge=0)
    pages_with_evidence: int = Field(default=0, ge=0)
    source_pdf_sha256: Optional[str] = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    file_sizes: Dict[str, int] = Field(default_factory=dict)
    file_sha256: Dict[str, str] = Field(default_factory=dict)
    quality_report: Dict[str, Any] = Field(default_factory=dict)


class ChunkMultimodalRelation(BaseContract):
    relation_id: str = Field(min_length=1)
    chunk_id: str = Field(min_length=1)
    element_id: str = Field(min_length=1)
    element_type: MultimodalElementType
    relation_type: RelationType
    confidence: float = Field(default=0, ge=0, le=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MultimodalPackage(BaseContract):
    manifest: ColabPackageManifest
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    chunks: List[Dict[str, Any]] = Field(default_factory=list)
    tables: List[TableCandidate] = Field(default_factory=list)
    figures: List[FigureCandidate] = Field(default_factory=list)
    formulas: List[FormulaCandidate] = Field(default_factory=list)
    pages: List[PageEvidence] = Field(default_factory=list)
    relations: List[ChunkMultimodalRelation] = Field(default_factory=list)

    def get_element_by_id(self, element_id):
        return next((e for e in self.tables + self.figures + self.formulas if e.element_id == element_id), None)
