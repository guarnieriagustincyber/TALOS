"""Epistemological Chain Contracts for Subsystem S5.5.

Formalizes the 5 distinct epistemological stages of evidence progression
and their respective sovereign authorities:

    Observation (S6/S7)
        != AssessmentResult (S9/S10)
        != EvidenceRecord (S5.2.A)
        != GatewayVerdictRecord (GatewayDecisionAuthority)
        != StudentState (S5.2.C)

Zero double-authority: Each stage is governed exclusively by its designated
subsystem. Direct shortcuts or authority bypasses are strictly forbidden.
"""

from enum import Enum
from typing import Dict, FrozenSet


class EpistemologicalStage(str, Enum):
    """The 5 discrete epistemological stages in Study Engine."""

    OBSERVATION = "OBSERVATION"
    ASSESSMENT_RESULT = "ASSESSMENT_RESULT"
    EVIDENCE_RECORD = "EVIDENCE_RECORD"
    GATEWAY_VERDICT = "GATEWAY_VERDICT"
    STUDENT_STATE = "STUDENT_STATE"


class EpistemologicalAuthority(str, Enum):
    """The designated sovereign authorities for each epistemological stage."""

    EXECUTION_PLANE = "S6_EXECUTION_PLANE"
    ORAL_DEFENSE = "S7_ORAL_DEFENSE"
    ASSESSMENT_ENGINE = "S9_S10_ASSESSMENT_ENGINE"
    EVIDENCE_POLICY = "S5_2_A_EVIDENCE_POLICY"
    GATEWAY_DECISION_AUTHORITY = "GATEWAY_DECISION_AUTHORITY"
    STATE_ENGINE = "S5_2_C_STATE_ENGINE"


STAGE_AUTHORITY_MAPPING: Dict[
    EpistemologicalStage, FrozenSet[EpistemologicalAuthority]
] = {
    EpistemologicalStage.OBSERVATION: frozenset(
        {
            EpistemologicalAuthority.EXECUTION_PLANE,
            EpistemologicalAuthority.ORAL_DEFENSE,
        }
    ),
    EpistemologicalStage.ASSESSMENT_RESULT: frozenset(
        {EpistemologicalAuthority.ASSESSMENT_ENGINE}
    ),
    EpistemologicalStage.EVIDENCE_RECORD: frozenset(
        {EpistemologicalAuthority.EVIDENCE_POLICY}
    ),
    EpistemologicalStage.GATEWAY_VERDICT: frozenset(
        {EpistemologicalAuthority.GATEWAY_DECISION_AUTHORITY}
    ),
    EpistemologicalStage.STUDENT_STATE: frozenset(
        {EpistemologicalAuthority.STATE_ENGINE}
    ),
}


class EpistemologicalAuthorityViolationError(Exception):
    """Raised when unauthorized component attempts to emit a stage record."""

    pass


def validate_epistemological_authority(
    stage: EpistemologicalStage,
    authority: EpistemologicalAuthority,
) -> None:
    """Validate that the given authority is permitted to emit the stage.

    Args:
        stage: The epistemological stage being produced.
        authority: The claiming authority component.

    Raises:
        EpistemologicalAuthorityViolationError: If authority is not permitted.
    """
    allowed_authorities = STAGE_AUTHORITY_MAPPING.get(stage, frozenset())
    if authority not in allowed_authorities:
        msg = (
            f"Epistemological authority violation: Authority "
            f"'{authority.value}' is forbidden from emitting stage "
            f"'{stage.value}'. Allowed authorities: "
            f"{[a.value for a in allowed_authorities]}."
        )
        raise EpistemologicalAuthorityViolationError(msg)
