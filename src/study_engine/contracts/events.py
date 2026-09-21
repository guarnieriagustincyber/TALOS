"""Operational event, trust level, and data classification contracts (S5.5).

INVARIANTS:
1. OperationalEvent is structured telemetry with correlation and causation IDs
   for distributed tracing and forensic auditing.
2. OperationalEvent is strictly distinct from EvidenceRecord. It NEVER enters
   the Evidence Ledger or drives Student State projection.
3. TrustLevel describes epistemological provenance status, NOT an
   operational authorization or trust score. No TrustLevel authorizes mastery.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict
from pydantic import Field

from study_engine.contracts.base import BaseContract


class TrustLevel(str, Enum):
    """Epistemological status and provenance tier of domain data.

    CRITICAL INVARIANT:
    TrustLevel is descriptive, NOT authorizing. Having
    TrustLevel.AUDITED_OUTPUT does not grant mastery. Having
    TrustLevel.CRYPTOGRAPHIC_ARTIFACT does not constitute evidence.
    """

    UNTRUSTED_INPUT = "UNTRUSTED_INPUT"
    AUTHORITATIVE_SOURCE = "AUTHORITATIVE_SOURCE"
    DERIVED_RETRIEVAL = "DERIVED_RETRIEVAL"
    GENERATIVE_HYPOTHESIS = "GENERATIVE_HYPOTHESIS"
    AUDITED_OUTPUT = "AUDITED_OUTPUT"
    INSTRUMENTAL_OBSERVATION = "INSTRUMENTAL_OBSERVATION"
    CRYPTOGRAPHIC_ARTIFACT = "CRYPTOGRAPHIC_ARTIFACT"
    EVALUATED_ASSESSMENT = "EVALUATED_ASSESSMENT"
    OFFICIAL_EVIDENCE = "OFFICIAL_EVIDENCE"
    PROJECTED_STATE = "PROJECTED_STATE"


class DataClassification(str, Enum):
    """Data confidentiality and sanitization tiers."""

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    STUDENT_DATA = "STUDENT_DATA"
    SENSITIVE = "SENSITIVE"
    SECRET = "SECRET"


class OperationalEvent(BaseContract):
    """Structured telemetry, logging, and distributed tracing event.

    INVARIANT:
    OperationalEvent is purely operational. It carries correlation_id and
    causation_id for tracing. It must NEVER enter the Evidence Ledger.
    """

    event_id: str = Field(..., min_length=1, description="Unique event ID")
    correlation_id: str = Field(
        ..., min_length=1, description="Interaction correlation trace ID"
    )
    causation_id: str = Field(
        ..., min_length=1, description="Triggering command or event ID"
    )
    event_type: str = Field(
        ..., min_length=1, description="Category of operational event"
    )
    component: str = Field(
        ..., min_length=1, description="Emitting subsystem identifier"
    )
    trust_level: TrustLevel = Field(
        default=TrustLevel.INSTRUMENTAL_OBSERVATION,
        description="Epistemological provenance status",
    )
    data_classification: DataClassification = Field(
        default=DataClassification.INTERNAL,
        description="Confidentiality classification",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of event creation",
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict, description="Structured operational payload"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Extensible telemetry metadata"
    )
