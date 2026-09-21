"""Evidence set classification for Forensic S4.4 grounding (Ola 5, Fase 5.4, E30).

Defines the 4 EvidenceType classifications:
- DIRECT: Afirmación explícita en la fuente.
- SYNTHESIS: Combinación de >=2 evidencias del ContextPack.
- DERIVED: Deducción lógica o paso conceptual demostrado desde el ContextPack.
- UNSUPPORTED: No demostrable desde el ContextPack (alucinación o conocimiento paramétrico).

Invariant: S4.4 rechaza ÚNICAMENTE UNSUPPORTED. DIRECT, SYNTHESIS y DERIVED son válidos.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set, Tuple


class EvidenceType(str, Enum):
    DIRECT = "direct"
    SYNTHESIS = "synthesis"
    DERIVED = "derived"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class EvidenceClaim:
    """Individual assertion evaluated against the ContextPack."""
    claim_text: str
    evidence_type: EvidenceType
    supporting_chunk_ids: Tuple[str, ...] = ()
    confidence: float = 1.0
    rationale: Optional[str] = None


@dataclass
class EvidenceSet:
    """Set of claims evaluated for S4.4 forensic grounding."""
    claims: List[EvidenceClaim] = field(default_factory=list)

    def add_claim(
        self,
        claim_text: str,
        evidence_type: EvidenceType,
        supporting_chunk_ids: Tuple[str, ...] = (),
        confidence: float = 1.0,
        rationale: Optional[str] = None,
    ) -> None:
        self.claims.append(
            EvidenceClaim(
                claim_text=claim_text,
                evidence_type=evidence_type,
                supporting_chunk_ids=supporting_chunk_ids,
                confidence=confidence,
                rationale=rationale,
            )
        )

    def is_audited_approved(self) -> bool:
        """True only if NO claim is UNSUPPORTED (S4.4 validation)."""
        if not self.claims:
            return True
        return all(c.evidence_type != EvidenceType.UNSUPPORTED for c in self.claims)

    @property
    def unsupported_claims(self) -> List[EvidenceClaim]:
        return [c for c in self.claims if c.evidence_type == EvidenceType.UNSUPPORTED]
