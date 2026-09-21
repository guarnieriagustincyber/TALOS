"""Atomic NLI judge protocol, mock, and aggregation logic for S4.4.

Enforces:
- HG-S4.4-07: Atomic Isolation of NLI (premise, hypothesis only).
- HG-S4.4-08: NLI Failure Is Not Approval (fail-safe uncertainty handling).
"""


from typing import Dict, List, Optional, Protocol, runtime_checkable
from pydantic import ConfigDict, Field

from study_engine.contracts.base import BaseContract
from study_engine.audit.contracts import (
    AuditVerdict,
    ClaimSupportVerdict,
    ClaimVerification,
)


class NLIInferenceResult(BaseContract):
    """Immutable inference verdict from an atomic NLI judge."""

    model_config = ConfigDict(frozen=True)

    verdict: ClaimSupportVerdict = Field(
        ..., description="Atomic inferential relationship"
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Observational confidence score (not truth)",
    )
    rationale: Optional[str] = Field(
        default=None, description="Concise rationale for verdict"
    )


@runtime_checkable
class BaseNLIJudge(Protocol):
    """Protocol for atomic Natural Language Inference evaluators."""

    @property
    def judge_id(self) -> str:
        """Unique identifier of the NLI judge backend."""
        ...

    def evaluate_claim(
        self, premise: str, hypothesis: str
    ) -> NLIInferenceResult:
        """Evaluate if premise entails, contradicts, or is neutral."""
        ...


class MockNLIJudge:
    """Hermetic in-memory mock NLI judge for unit and adversarial testing."""

    def __init__(
        self,
        judge_id: str = "mock-nli-v1",
        default_verdict: ClaimSupportVerdict = ClaimSupportVerdict.ENTAILED,
        canned_verdicts: Optional[Dict[str, ClaimSupportVerdict]] = None,
        inject_error: Optional[Exception] = None,
    ) -> None:
        self._judge_id = judge_id
        self._default_verdict = default_verdict
        self._canned_verdicts = canned_verdicts or {}
        self._inject_error = inject_error

    @property
    def judge_id(self) -> str:
        return self._judge_id

    def evaluate_claim(
        self, premise: str, hypothesis: str
    ) -> NLIInferenceResult:
        if self._inject_error is not None:
            raise self._inject_error

        # Check canned substrings
        for key, verdict in self._canned_verdicts.items():
            if key in hypothesis or key in premise:
                return NLIInferenceResult(
                    verdict=verdict,
                    confidence=0.95,
                    rationale=f"Canned mock verdict matched '{key}'",
                )

        return NLIInferenceResult(
            verdict=self._default_verdict,
            confidence=0.90,
            rationale="Default mock NLI evaluation",
        )


class NLIAggregator:
    """Aggregator compiling atomic claim verdicts into overall audit verdict.

    POLICY:
    1. If ANY claim is CONTRADICTED -> REJECTED_CONTRADICTION.
    2. If ANY claim is NOT_ENTAILED -> REJECTED_UNSUPPORTED.
    3. If ANY claim is UNASSESSED (no rejection above) -> FLAGGED_UNASSESSED.
    4. If ALL claims are ENTAILED -> APPROVED (within audited properties).
    """

    def aggregate(

        self, claim_verifications: List[ClaimVerification]
    ) -> AuditVerdict:
        """Determine overall verdict from individual claim evaluations."""
        if not claim_verifications:
            return AuditVerdict.APPROVED

        verdicts = [cv.nli_verdict for cv in claim_verifications]

        if ClaimSupportVerdict.CONTRADICTED in verdicts:
            return AuditVerdict.REJECTED_CONTRADICTION

        if ClaimSupportVerdict.NOT_ENTAILED in verdicts:
            return AuditVerdict.REJECTED_UNSUPPORTED

        if ClaimSupportVerdict.UNASSESSED in verdicts:
            return AuditVerdict.FLAGGED_UNASSESSED

        return AuditVerdict.APPROVED
