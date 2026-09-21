"""Routing decision dataclass for Intent and Context routing (Ola 5, Fase 5.2).

INVARIANTS:
1. INV-W5-3: RoutingDecision never mutates, evaluates, or decides BKT/pedagogical mastery.
2. Orthogonality: requires_multimodal is completely orthogonal to depth, NOT a depth level.
3. Decoupling: suggested_provider is Optional[str] (decision delegated to Model Registry in Fase 5.3).
"""

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class RoutingDecision:
    depth: Literal["NORMAL", "DEEP", "GLOBAL"]
    requires_multimodal: bool
    requires_multi_source: bool
    requires_long_context: bool
    max_context_tokens: int
    cloud_allowed: bool
    suggested_provider: Optional[str]
    explanation: str
