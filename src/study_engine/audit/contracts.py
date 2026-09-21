"""Authoritative contracts and data models for Subsystem S4.4 Forensic Auditor.

REGLA DE ORO DE S4.4:
S4.4 no certifica verdad ontológica. Certifica ausencia de violaciones
detectables dentro de un dominio de auditoría explícitamente definido.
"""

from enum import Enum
from typing import Any, Dict, Optional, Tuple
from pydantic import ConfigDict, Field

from study_engine.contracts.base import BaseContract
from study_engine.contracts.generation import (
    GenerationRequest,
    GenerationResponse,
)


class AuditVerdict(str, Enum):
    """Overall verdict of the forensic audit."""

    APPROVED = "APPROVED"
    FLAGGED_UNASSESSED = "FLAGGED_UNASSESSED"
    UNVERIFIED_SOURCE = "UNVERIFIED_SOURCE"
    REJECTED_UNSUPPORTED = "REJECTED_UNSUPPORTED"
    REJECTED_CONTRADICTION = "REJECTED_CONTRADICTION"
    REJECTED_ABSTENTION_VIOLATION = "REJECTED_ABSTENTION_VIOLATION"
    REJECTED_INJECTION_DETECTED = "REJECTED_INJECTION_DETECTED"
    REJECTED_POLICY_VIOLATION = "REJECTED_POLICY_VIOLATION"
    REJECTED_INPUT_MISMATCH = "REJECTED_INPUT_MISMATCH"


class CheckStatus(str, Enum):
    """Execution status of an individual audit check."""

    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


class CheckSeverity(str, Enum):
    """Severity level of an audit check failure."""

    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFORMATIONAL = "INFORMATIONAL"


class ClaimType(str, Enum):
    """Structural classification of a segmented claim/sentence."""

    FACTUAL = "FACTUAL"
    PEDAGOGICAL = "PEDAGOGICAL"
    QUESTION = "QUESTION"
    CONVERSATIONAL = "CONVERSATIONAL"
    UNCLASSIFIED = "UNCLASSIFIED"


class ClaimSupportVerdict(str, Enum):
    """NLI inference verdict on a single claim against cited chunk."""

    ENTAILED = "ENTAILED"
    CONTRADICTED = "CONTRADICTED"
    NOT_ENTAILED = "NOT_ENTAILED"
    UNASSESSED = "UNASSESSED"


class LexicalAnomalyStatus(str, Enum):
    """Status of lexical and technical entity diagnostics."""

    NO_ANOMALY = "NO_ANOMALY"
    LEXICAL_ANOMALY = "LEXICAL_ANOMALY"
    INCONCLUSIVE = "INCONCLUSIVE"


class LexicalDiagnostics(BaseContract):
    """Diagnostic metrics on lexical and entity containment.

    RULE: Lexical diagnostics provide anomaly detection telemetry;
    they do NOT constitute semantic proof of truth or falsehood.
    """

    model_config = ConfigDict(frozen=True)

    status: LexicalAnomalyStatus = Field(
        ..., description="Overall status of lexical diagnostic scan"
    )
    token_overlap_ratio: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Lexical token overlap ratio between claim and chunk",
    )
    technical_entities_found: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="Technical entities found in both claim and chunk",
    )
    technical_entities_missing: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="Technical entities in claim missing from chunk",
    )
    numeric_matches: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="Numeric/hex constants validated against chunk",
    )


class DeterministicAuditCheck(BaseContract):
    """Immutable result of a single deterministic audit check."""

    model_config = ConfigDict(frozen=True)

    check_id: str = Field(
        ..., min_length=1, description="Unique check identifier"
    )
    status: CheckStatus = Field(
        ..., description="Result of check execution"
    )
    severity: CheckSeverity = Field(
        default=CheckSeverity.CRITICAL,
        description="Severity level if check fails",
    )
    reason: str = Field(
        ..., min_length=1, description="Explanatory finding details"
    )
    evidence_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional diagnostic data payload"
    )


class ClaimVerification(BaseContract):
    """Detailed verification record for a segmented claim/sentence."""

    model_config = ConfigDict(frozen=True)

    claim_index: int = Field(
        ..., ge=0, description="Sequential index of claim in response text"
    )
    claim_text: str = Field(
        ..., min_length=1, description="Exact segmented claim text"
    )
    claim_type: ClaimType = Field(
        ..., description="Structural classification of claim"
    )
    cited_tags: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="Evidence tags [E#] cited in this claim",
    )
    lexical_diagnostics: LexicalDiagnostics = Field(
        ..., description="Lexical and entity containment telemetry"
    )
    nli_verdict: ClaimSupportVerdict = Field(
        ..., description="NLI inferential support verdict"
    )
    nli_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Observational judge confidence (not a truth metric)",
    )
    nli_rationale: Optional[str] = Field(
        default=None, description="Concise reasoning provided by NLI judge"
    )


class ForensicAuditInput(BaseContract):
    """Authoritative input container for forensic auditing.

    Preserves S4.2/S4.3 frozen boundary while supplying prompt_hash when known.
    """

    model_config = ConfigDict(frozen=True)

    request: GenerationRequest = Field(
        ..., description="Authoritative generation request"
    )
    response: GenerationResponse = Field(
        ..., description="Authoritative generation response to audit"
    )
    prompt_hash: Optional[str] = Field(
        default=None,
        min_length=64,
        max_length=64,
        description="Optional SHA-256 prompt hash from S4.3",
    )


class ForensicAuditReport(BaseContract):
    """Authoritative, frozen forensic audit certification report."""

    model_config = ConfigDict(frozen=True)

    audit_id: str = Field(
        ..., min_length=1, description="Unique audit report identifier"
    )
    request_id: str = Field(
        ..., min_length=1, description="Audited GenerationRequest identifier"
    )
    notebook_id: str = Field(
        ..., min_length=1, description="Target course notebook identifier"
    )
    overall_verdict: AuditVerdict = Field(
        ..., description="Final composite verdict of the audit"
    )
    deterministic_checks: Tuple[DeterministicAuditCheck, ...] = Field(
        default_factory=tuple,
        description="Results of all Layer 1 deterministic checks",
    )
    claim_verifications: Tuple[ClaimVerification, ...] = Field(
        default_factory=tuple,
        description="Granular verification records per claim",
    )
    nli_executed: bool = Field(
        default=False,
        description="True if Layer 2 NLI was invoked; False if fail-closed",
    )
    nli_judge_id: Optional[str] = Field(
        default=None,
        description="Identifier of NLI judge backend if executed",
    )
    prompt_hash: Optional[str] = Field(
        default=None,
        description="Cryptographic SHA-256 prompt hash if provided",
    )
    evidence_hashes: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="Hashes of all chunks participating in audit",
    )
    audit_latency_ms: float = Field(
        ...,
        ge=0.0,
        description="Total audit execution latency in milliseconds",
    )

    auditor_backend: str = Field(
        ..., min_length=1, description="Audit engine version/identifier"
    )
