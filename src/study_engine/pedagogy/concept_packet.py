"""Generic Multi-Source ConceptPacket for Subsystem S4.2 / S4.4.

INVARIANTS:
1. Dynamic roles per notebook: does NOT hardcode static roles.
2. S4.4 boundary is absolute: ConceptPacket carries the authoritative ForensicAuditReport
   and AuditVerdict.
3. If evidence is ungrounded or audit fails, ConceptResponse is emitted with status ABSTAINED.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

from study_engine.audit.contracts import AuditVerdict, ForensicAuditReport
from study_engine.contracts.evidence_engine import CitationRecord


@dataclass(frozen=True)
class ConceptPacket:
    """Integrated multi-source pedagogical synthesis approved by S4.4."""

    kc_id: str
    notebook_id: str
    objective: str

    # Evidence grouped dynamically by source role ("PRIMARY", "METHODOLOGICAL", "FORMAL", etc.)
    evidence_by_role: Dict[str, List[CitationRecord]]

    # Pedagogical synthesis fields
    core_concept: str  # Grounded in PRIMARY source
    mental_model: str  # Grounded in METHODOLOGICAL source
    reasoning_guidance: str  # Grounded in METHODOLOGICAL source
    formalization: Optional[str]  # Grounded in FORMAL source (if present)
    implementation_guidance: Optional[str]  # Grounded in IMPLEMENTATION source (if present)
    pitfalls: Tuple[str, ...]  # Frequently observed errors and antipatterns

    # Epistemic citations and verification audit
    citations: Tuple[CitationRecord, ...]
    s44_report: Optional[ForensicAuditReport]
    audit_verdict: AuditVerdict
    assembly_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kc_id": self.kc_id,
            "notebook_id": self.notebook_id,
            "objective": self.objective,
            "evidence_by_role": {
                role: [c.model_dump() for c in recs]
                for role, recs in self.evidence_by_role.items()
            },
            "core_concept": self.core_concept,
            "mental_model": self.mental_model,
            "reasoning_guidance": self.reasoning_guidance,
            "formalization": self.formalization,
            "implementation_guidance": self.implementation_guidance,
            "pitfalls": list(self.pitfalls),
            "citations": [c.model_dump() for c in self.citations],
            "audit_verdict": self.audit_verdict.value,
            "assembly_hash": self.assembly_hash,
        }


@dataclass(frozen=True)
class ConceptResponse:
    """Safe, verifiable API response for concept explanation."""

    status: Literal["PRESENTABLE", "ABSTAINED"]
    packet: Optional[ConceptPacket] = None
    abstention_reason: Optional[str] = None
    audit_verdict: Optional[AuditVerdict] = None
    admitted_evidence: Tuple[CitationRecord, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "packet": self.packet.to_dict() if self.packet else None,
            "abstention_reason": self.abstention_reason,
            "audit_verdict": self.audit_verdict.value if self.audit_verdict else None,
            "admitted_evidence": [c.model_dump() for c in self.admitted_evidence],
        }
