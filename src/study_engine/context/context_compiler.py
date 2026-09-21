"""ContextCompiler: Hierarchical context pack compilation & physical pre-LLM abstention gate (Ola 5, Fase 5.4, E25, INV-W5-1).

Integrates:
- Retrieval across active sources
- SectionExpander for greedy ±2 window expansion
- Source contribution summary & provenance tracking
- Physical Pre-LLM Abstention Gate: 0 chunks returned = immediate abstention without cloud invocation
"""

import logging
from typing import Any, Dict, List, Optional

from study_engine.context.context_pack import (
    ChunkWithProvenance,
    ContextPack,
    ExpandedSection,
    SourceContribution,
)
from study_engine.context.section_expander import SectionExpander
from study_engine.contracts.search import SearchResult

logger = logging.getLogger(__name__)


class ContextCompiler:
    """Compiles complete structural ContextPacks with strict pre-LLM gates."""

    def __init__(
        self,
        expander: Optional[SectionExpander] = None,
        max_context_tokens: int = 40000,
    ) -> None:
        self.expander = expander
        self.max_context_tokens = max_context_tokens

    def build_context_pack(
        self,
        query: str,
        seed_results: List[SearchResult],
        *,
        source_meta_cache: Optional[Dict[str, Dict[str, str]]] = None,
        session_state: Optional[Dict[str, Any]] = None,
        current_kc: Optional[str] = None,
        previous_errors: Optional[List[str]] = None,
        previous_hints: Optional[List[str]] = None,
    ) -> ContextPack:
        """Builds a verified ContextPack.

        Invariant INV-W5-1 / E25: If seed_results is empty or 0 chunks are found,
        triggers the physical pre-LLM abstention gate (0 network calls).
        """
        # Physical Pre-LLM Abstention Gate (E25, INV-W5-1)
        if not seed_results:
            logger.info("[PRE-LLM GATE] 0 chunks in active sources. Physical abstention triggered.")
            return ContextPack(
                session_state=session_state or {},
                current_kc=current_kc,
                previous_errors=previous_errors or [],
                previous_hints=previous_hints or [],
                abstained=True,
                abstention_reason="NO_EVIDENCES_IN_ACTIVE_SOURCES",
                retrieved_evidence=[],
                formatted_text="",
            )

        meta_cache = source_meta_cache or {}

        # If expander is injected, expand sections
        if self.expander is not None:
            expanded_chunks, formatted_text = self.expander.expand_results(
                seed_results=seed_results,
                source_meta_cache=meta_cache,
            )
        else:
            expanded_chunks = []
            formatted_blocks = []
            for res in seed_results:
                src_meta = meta_cache.get(res.source_id, {})
                title = src_meta.get("title", res.source_id)
                pos = res.index if res.index is not None else 0
                page = res.page_start or 1
                c = ChunkWithProvenance(
                    chunk_id=res.chunk_id,
                    document_id=res.document_id,
                    source_id=res.source_id,
                    source_title=title,
                    page_start=page,
                    pos_index=pos,
                    section="General",
                    content=res.content or res.snippet,
                    is_seed_hit=True,
                    relevance_score=float(res.score),
                    token_count=len((res.content or res.snippet).split()),
                )
                expanded_chunks.append(c)
                formatted_blocks.append(f"[CHUNK {pos} | Pág {page} | {title}]\n{c.content}")
            formatted_text = "\n\n".join(formatted_blocks)

        if not expanded_chunks:
            return ContextPack(
                session_state=session_state or {},
                current_kc=current_kc,
                previous_errors=previous_errors or [],
                previous_hints=previous_hints or [],
                abstained=True,
                abstention_reason="NO_EVIDENCES_IN_ACTIVE_SOURCES",
                retrieved_evidence=[],
                formatted_text="",
            )

        # Build source map
        source_map: Dict[str, SourceContribution] = {}
        for c in expanded_chunks:
            if c.source_id not in source_map:
                source_map[c.source_id] = SourceContribution(
                    source_id=c.source_id,
                    source_title=c.source_title,
                    chunk_count=1,
                    total_tokens=c.token_count,
                    pages_covered=[c.page_start],
                )
            else:
                curr = source_map[c.source_id]
                new_pages = list(set(curr.pages_covered + [c.page_start]))
                source_map[c.source_id] = SourceContribution(
                    source_id=c.source_id,
                    source_title=c.source_title,
                    chunk_count=curr.chunk_count + 1,
                    total_tokens=curr.total_tokens + c.token_count,
                    pages_covered=new_pages,
                )

        total_toks = sum(c.token_count for c in expanded_chunks)

        return ContextPack(
            session_state=session_state or {},
            current_kc=current_kc,
            previous_errors=previous_errors or [],
            previous_hints=previous_hints or [],
            source_map=source_map,
            retrieved_evidence=expanded_chunks,
            total_tokens=total_toks,
            expansion_budget_used=total_toks,
            abstained=False,
            abstention_reason=None,
            formatted_text=formatted_text,
        )
