"""Subsystem S4.4: Forensic Auditor.

REGLA DE ORO DE S4.4:
S4.4 no certifica verdad ontológica. Certifica ausencia de violaciones
detectables dentro de un dominio de auditoría explícitamente definido.
"""

from study_engine.audit.contracts import (
    AuditVerdict,
    CheckSeverity,
    CheckStatus,
    ClaimSupportVerdict,
    ClaimType,
    ClaimVerification,
    DeterministicAuditCheck,
    ForensicAuditInput,
    ForensicAuditReport,
    LexicalAnomalyStatus,
    LexicalDiagnostics,
)
from study_engine.audit.claim_extractor import (
    ClaimExtractor,
    ExtractedClaim,
)
from study_engine.audit.citation_verifier import CitationVerifier
from study_engine.audit.lexical_guard import LexicalGuard
from study_engine.audit.policy_guard import PolicyGuard
from study_engine.audit.injection_guard import InjectionGuard
from study_engine.audit.engine import (
    DeterministicAuditEngine,
    DeterministicEngineResult,
)
from study_engine.audit.nli import (
    BaseNLIJudge,
    MockNLIJudge,
    NLIAggregator,
    NLIInferenceResult,
)
from study_engine.audit.auditor import ForensicAuditor

__all__ = [
    "AuditVerdict",
    "CheckStatus",
    "CheckSeverity",
    "ClaimType",
    "ClaimSupportVerdict",
    "LexicalAnomalyStatus",
    "LexicalDiagnostics",
    "DeterministicAuditCheck",
    "ClaimVerification",
    "ForensicAuditInput",
    "ForensicAuditReport",
    "ExtractedClaim",
    "ClaimExtractor",
    "CitationVerifier",
    "LexicalGuard",
    "PolicyGuard",
    "InjectionGuard",
    "DeterministicAuditEngine",
    "DeterministicEngineResult",
    "BaseNLIJudge",
    "MockNLIJudge",
    "NLIAggregator",
    "NLIInferenceResult",
    "ForensicAuditor",
]
