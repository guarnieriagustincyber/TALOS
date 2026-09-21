"""Generation and tutoring contracts for Subsystem S4.2.

Defines immutable data models, closed interaction modes, validation statuses,
epistemic isolation invariants, and protocol boundaries for generation.
"""

from enum import Enum
from typing import Optional, Tuple
from pydantic import ConfigDict, Field, model_validator

from study_engine.contracts.base import BaseContract
from study_engine.contracts.evidence_engine import (
    CurricularIsolationError,
    EvidenceGrade,
    GroundingDecision,
    PackagedContext,
)


class GenerationMode(str, Enum):
    """Closed domain of supported pedagogical generation modes."""

    EXPLANATION = "EXPLANATION"
    SOCRATIC_TUTOR = "SOCRATIC_TUTOR"
    EVALUATION = "EVALUATION"
    PRACTICE_GENERATION = "PRACTICE_GENERATION"


class AbstentionType(str, Enum):
    """Closed domain of structural causes for generation abstention."""

    NO_EVIDENCE = "NO_EVIDENCE"
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"
    CURRICULAR_LEAKAGE = "CURRICULAR_LEAKAGE"
    POLICY_REFUSAL = "POLICY_REFUSAL"


class AbstentionOrigin(str, Enum):
    """Authoritative source that triggered the abstention decision."""

    EVIDENCE_POLICY = "EVIDENCE_POLICY"
    GENERATOR = "GENERATOR"


class ResponseValidationStatus(str, Enum):
    """Structural and contractual validation status of a generated output.

    NOTE: VALID means contractually well-formed and citation-resolvable.
    It does NOT imply epistemic truthfulness or pedagogical correctness,
    which is evaluated downstream by the S4.4 forensic auditor.
    """

    VALID = "VALID"
    INVALID_CITATION_DETECTED = "INVALID_CITATION_DETECTED"
    MALFORMED_OUTPUT = "MALFORMED_OUTPUT"


class ConversationRole(str, Enum):
    """Closed domain of allowed conversational participant roles."""

    STUDENT = "student"
    TUTOR = "tutor"


class ConversationTurn(BaseContract):
    """Immutable single turn in a conversational exchange.

    Epistemic invariant: Conversation history is conversational context only,
    never epistemic evidence. It cannot authorize factual claims, citations,
    curricular content, or student advancement unless explicitly represented
    in PackagedContext.
    """

    model_config = ConfigDict(frozen=True)

    role: ConversationRole = Field(
        ..., description="Conversational role (student or tutor)"
    )
    content: str = Field(
        ..., min_length=1, description="Verbatim message text"
    )


class TokenUsage(BaseContract):
    """Strongly typed, immutable token telemetry."""

    model_config = ConfigDict(frozen=True)

    prompt_tokens: Optional[int] = Field(
        default=None, ge=0, description="Tokens used in prompt"
    )
    completion_tokens: Optional[int] = Field(
        default=None, ge=0, description="Tokens generated in completion"
    )
    total_tokens: Optional[int] = Field(
        default=None, ge=0, description="Total tokens consumed"
    )


class GenerationParameters(BaseContract):
    """Immutable generation hyperparameters."""

    model_config = ConfigDict(frozen=True)

    temperature: float = Field(
        default=0.2, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_output_tokens: int = Field(
        default=1024, ge=1, description="Maximum completion tokens"
    )
    stop_sequences: Tuple[str, ...] = Field(
        default_factory=tuple, description="Optional stop sequences"
    )
    seed: Optional[int] = Field(
        default=None, description="Optional deterministic seed"
    )
    suggested_model: Optional[str] = Field(
        default=None, description="Suggested target model identifier"
    )


class ParsedCitation(BaseContract):
    """Immutable citation reference parsed from generation output."""

    model_config = ConfigDict(frozen=True)

    citation_id: str = Field(
        ..., min_length=2, description="Citation tag (e.g. 'E1')"
    )
    in_manifest: bool = Field(
        ..., description="True if citation exists in request CitationManifest"
    )
    chunk_id: Optional[str] = Field(
        default=None, description="Authoritative chunk ID if in manifest"
    )
    source_id: Optional[str] = Field(
        default=None, description="Authoritative source ID if in manifest"
    )
    grade: Optional[EvidenceGrade] = Field(
        default=None, description="Directness grade if in manifest"
    )


class AbstentionDetails(BaseContract):
    """Authoritative structural record for generation abstentions."""

    model_config = ConfigDict(frozen=True)

    origin: AbstentionOrigin = Field(
        ..., description="Origin of abstention (EVIDENCE_POLICY or GENERATOR)"
    )
    abstention_type: AbstentionType = Field(
        ..., description="Specific structural reason for abstention"
    )
    reason: str = Field(
        ..., min_length=1, description="Pedagogical explanation for abstention"
    )
    suggested_action: Optional[str] = Field(
        default=None, description="Suggested next step for student"
    )


class GenerationRequest(BaseContract):
    """Authoritative, immutable request for pedagogical generation.

    Epistemic invariant: notebook_id must strictly match the notebook_id
    governing the packaged_context.
    """

    model_config = ConfigDict(frozen=True)

    request_id: str = Field(

        ..., min_length=1, description="Unique generation request identifier"
    )
    notebook_id: str = Field(
        ..., min_length=1, description="Authoritative curricular notebook ID"
    )
    query: str = Field(
        ..., min_length=1, description="Student question or query"
    )
    packaged_context: PackagedContext = Field(
        ..., description="Frozen, budget-governed context from Subsystem S4.1"
    )
    mode: GenerationMode = Field(
        default=GenerationMode.EXPLANATION,
        description="Target pedagogical interaction mode",
    )
    parameters: GenerationParameters = Field(
        default_factory=GenerationParameters,
        description="Immutable generation hyperparameters",
    )
    history: Tuple[ConversationTurn, ...] = Field(
        default_factory=tuple,
        description="Prior conversational turns (conversational context only)",
    )
    generation_profile_id: Optional[str] = Field(
        default=None,
        description="Optional closed system profile ID (no prompt overrides)",
    )

    @model_validator(mode="after")
    def _verify_curricular_isolation(self) -> "GenerationRequest":
        """Enforce strict curricular scope match between request and context.
        """
        context_nb = self.packaged_context.packet.notebook_id

        if self.notebook_id != context_nb:
            raise CurricularIsolationError(
                f"GenerationRequest notebook_id '{self.notebook_id}' does not "
                f"match PackagedContext notebook_id '{context_nb}'."
            )
        return self


class RawGenerationResult(BaseContract):
    """Unvalidated, raw output emitted by an S4.3 generation engine.

    Represents the output boundary of S4.3 before deterministic parsing.
    """

    model_config = ConfigDict(frozen=True)

    raw_content: str = Field(
        ..., min_length=1, description="Verbatim raw text produced by model"
    )
    generator_abstained: bool = Field(
        default=False,
        description="True if model explicitly signaled abstention",
    )
    latency_ms: Optional[float] = Field(
        default=None, ge=0.0, description="Inference latency in milliseconds"
    )
    tokens_used: Optional[TokenUsage] = Field(
        default=None, description="Token usage statistics"
    )
    model: Optional[str] = Field(
        default=None, description="Exact model identifier that produced output"
    )


class GenerationResponse(BaseContract):
    """Authoritative, certified generation response produced by S4.2 Parser.

    RULE: This model MUST NOT be instantiated by any S4.3 generator.
    It is an S4.2 parser-owned artifact.
    """

    model_config = ConfigDict(frozen=True)

    response_id: str = Field(

        ..., min_length=1, description="Unique generation response identifier"
    )
    request_id: str = Field(
        ..., min_length=1, description="Identifier matching GenerationRequest"
    )
    notebook_id: str = Field(
        ..., min_length=1, description="Authoritative curricular notebook ID"
    )
    mode: GenerationMode = Field(
        ..., description="Pedagogical mode under which response was generated"
    )
    text: str = Field(
        ..., description="Student-facing response content"
    )
    raw_content: str = Field(
        ..., min_length=1, description="Verbatim output from generator"
    )
    citations: Tuple[ParsedCitation, ...] = Field(
        default_factory=tuple,
        description="All citation tags parsed in text in order of appearance",
    )
    phantom_citations: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="Citation tags cited in text but absent from manifest",
    )
    validation_status: ResponseValidationStatus = Field(
        ..., description="Contractual validation status"
    )
    is_abstention: bool = Field(
        ..., description="True if response represents an abstention"
    )
    abstention_details: Optional[AbstentionDetails] = Field(
        default=None, description="Detailed abstention metadata if applicable"
    )
    grounding_decision: GroundingDecision = Field(
        ..., description="Epistemic grounding decision from PackagedContext"
    )
    tokens_used: Optional[TokenUsage] = Field(
        default=None, description="Token usage telemetry"
    )
    latency_ms: Optional[float] = Field(
        default=None, ge=0.0, description="Latency in milliseconds"
    )
    model: Optional[str] = Field(
        default=None, description="Model identifier reported by generator"
    )


class GenerationContractError(Exception):
    """Base exception for all generation contract violations."""


class MalformedOutputError(GenerationContractError):
    """Raised when generator output is blank, whitespace-only, or invalid."""


class InvalidGenerationModeError(GenerationContractError):
    """Raised when an unsupported or invalid generation mode is requested."""
