"""Adaptive Retrieval Router for Dynamic Strategy and Depth Selection (Fase 7 / F1, F7).

Analyzes query structure and technical indicators using deterministic rules (<1ms, 0 LLM)
to decide candidate pool depth, fusion weights, facet extraction, and reranking stage.
"""

from enum import Enum
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RoutingStrategy(str, Enum):
    """Categorized retrieval routing profile."""

    EXACT_LEXICAL = "EXACT_LEXICAL"
    CONCEPTUAL_SEMANTIC = "CONCEPTUAL_SEMANTIC"
    COMPOSITE_FACETED = "COMPOSITE_FACETED"


class RouteDecision(BaseModel):
    """Deterministic routing decision output for downstream retrieval stages."""

    strategy: RoutingStrategy = Field(..., description="Categorized retrieval routing strategy")
    pool_depth: int = Field(..., ge=1, le=100, description="Stage-1 candidate pool depth")
    lexical_weight: float = Field(..., ge=0.0, le=1.0, description="FTS5 lexical score weight")
    dense_weight: float = Field(..., ge=0.0, le=1.0, description="Dense vector score weight")
    enable_rerank: bool = Field(..., description="Whether to trigger Stage-2 reranking")
    use_facets: bool = Field(..., description="Whether to perform stage-aware facet extraction")
    reasons: List[str] = Field(default_factory=list, description="Audit reasoning flags")


# F1: Precompiled patterns for exact identifiers and system/C constructs
EXACT_LEXICAL_PATTERNS = [
    r"\b(pthread_mutex_lock|pthread_mutex_unlock|pthread_mutex_init|pthread_create|pthread_join)\b",
    r"\b(SIGSEGV|SIGKILL|SIGTERM|SIGINT|SIGCHLD|SIGPIPE)\b",
    r"\b(malloc|free|calloc|realloc|memcpy|memset|memmove|strcpy|strncpy)\b",
    r"\b(uint32_t|uint8_t|uint16_t|uint64_t|int32_t|int64_t|size_t|ssize_t)\b",
    r"(?:^|\W)(%rax|%rbx|%rcx|%rdx|%rsi|%rdi|%rbp|%rsp|%eax|%ebx|%ecx|%edx)\b",
    r"\b(NULL|EOF|EXIT_SUCCESS|EXIT_FAILURE)\b",
    r"\b(socket|bind|listen|accept|connect|recv|send|epoll|select)\b",
    r"\b(0x[0-9a-fA-F]+)\b",
]

# F1: Indicators for conceptual or theoretical queries
CONCEPTUAL_SEMANTIC_INDICATORS = [
    r"\b(explicar|definir|qu[eé]\s+es|c[oó]mo\s+funciona|por\s+qu[eé])\b",
    r"\b(concepto|teor[ií]a|principio|fundamento|arquitectura|mecanismo)\b",
    r"\b(intuici[oó]n|analog[ií]a|significado|raz[oó]n)\b",
]

# F1: Indicators for multi-faceted or comparative queries
COMPOSITE_FACETED_INDICATORS = [
    r"\b(diferencia[s]?|comparar|comparaci[oó]n|versus|vs|frente\s+a)\b",
    r"\b(entre\s+.+\s+y\s+.+)\b",
    r"\b(ventajas|desventajas|pros|contras)\b",
    r"\b(además\s+de|por\s+un\s+lado|en\s+relaci[oó]n\s+con)\b",
]

_COMPILED_EXACT = [re.compile(p, re.IGNORECASE) for p in EXACT_LEXICAL_PATTERNS]
_COMPILED_CONCEPTUAL = [re.compile(p, re.IGNORECASE) for p in CONCEPTUAL_SEMANTIC_INDICATORS]
_COMPILED_COMPOSITE = [re.compile(p, re.IGNORECASE) for p in COMPOSITE_FACETED_INDICATORS]


def _count_matches(compiled_patterns: List[re.Pattern], text: str) -> int:
    return sum(len(cp.findall(text)) for cp in compiled_patterns)


class AdaptiveRetrievalRouter:
    """Deterministic, stateless router for adaptive retrieval strategy selection (F1, F7)."""

    def route(self, query: str, context: Optional[Dict[str, Any]] = None) -> RouteDecision:
        """Classify query into an optimal RouteDecision.
        
        Decision Rule (F1):
          - count_matches(EXACT_LEXICAL_PATTERNS) >= 2 -> EXACT_LEXICAL
          - elif count_matches(COMPOSITE_FACETED_INDICATORS) >= 1 -> COMPOSITE_FACETED
          - else -> CONCEPTUAL_SEMANTIC
        """
        clean_query = query.strip() if query else ""
        if not clean_query:
            return RouteDecision(
                strategy=RoutingStrategy.CONCEPTUAL_SEMANTIC,
                pool_depth=10,
                lexical_weight=0.5,
                dense_weight=0.5,
                enable_rerank=False,
                use_facets=False,
                reasons=["EMPTY_QUERY_DEFAULT"],
            )

        exact_count = _count_matches(_COMPILED_EXACT, clean_query)
        composite_count = _count_matches(_COMPILED_COMPOSITE, clean_query)
        conceptual_count = _count_matches(_COMPILED_CONCEPTUAL, clean_query)

        reasons: List[str] = []

        if exact_count >= 2:
            reasons.append(f"EXACT_MATCHES_{exact_count}")
            return RouteDecision(
                strategy=RoutingStrategy.EXACT_LEXICAL,
                pool_depth=20,
                lexical_weight=1.0,
                dense_weight=0.2,
                enable_rerank=False,
                use_facets=False,
                reasons=reasons,
            )
        elif composite_count >= 1:
            reasons.append(f"COMPOSITE_MATCHES_{composite_count}")
            return RouteDecision(
                strategy=RoutingStrategy.COMPOSITE_FACETED,
                pool_depth=50,
                lexical_weight=0.6,
                dense_weight=0.7,
                enable_rerank=True,
                use_facets=True,
                reasons=reasons,
            )
        else:
            if conceptual_count > 0:
                reasons.append(f"CONCEPTUAL_MATCHES_{conceptual_count}")
            else:
                reasons.append("DEFAULT_CONCEPTUAL_PROFILE")
            return RouteDecision(
                strategy=RoutingStrategy.CONCEPTUAL_SEMANTIC,
                pool_depth=30,
                lexical_weight=0.5,
                dense_weight=0.8,
                enable_rerank=True,
                use_facets=False,
                reasons=reasons,
            )
