"""SectionExpander: Window Greedy Expansion with Hard-Ceiling for Large Context RAG (Ola 5, E23, E26).

Expands retrieval hits into contiguous chunk sections (±2 chunks using pos_index),
injects explicit position metadata to avoid floating citations (E26), and enforces
a strict hard ceiling of 40,000 tokens (E23).
"""

from dataclasses import dataclass
import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from study_engine.contracts.search import SearchResult
from study_engine.storage.sqlite_engine import SQLiteStorageEngine

from study_engine.config import settings

logger = logging.getLogger(__name__)

HARD_CEILING_TOKENS = settings.max_context_tokens   # BACKLOG-CTX-001: elevado a 5.000 tokens
EXPANSION_WINDOW = 1  # ±1 chunk alrededor de cada hit (era ±2)


@dataclass(frozen=True)
class ExpandedChunk:
    """Represents a chunk within an expanded section with provenance and position metadata."""
    chunk_id: str
    document_id: str
    source_id: str
    source_title: str
    page_start: int
    pos_index: int
    section: str
    content: str
    is_seed_hit: bool
    relevance_score: float
    token_count: int


class SectionExpander:
    """Expands SearchResults into coherent section windows with hard ceiling enforcement."""

    def __init__(self, engine: SQLiteStorageEngine, hard_ceiling_tokens: int = HARD_CEILING_TOKENS) -> None:
        self.engine = engine
        self.hard_ceiling_tokens = hard_ceiling_tokens

    def expand_results(
        self,
        seed_results: List[SearchResult],
        source_meta_cache: Optional[Dict[str, Dict[str, str]]] = None,
        allowed_source_ids: Optional[Set[str] | List[str]] = None,
    ) -> Tuple[List[ExpandedChunk], str]:
        """Expand seed results to contiguous sections and build formatted context.

        Returns:
            Tuple[List[ExpandedChunk], str]: List of expanded chunks and the formatted text pack.
        """
        if not seed_results:
            return [], ""
        if allowed_source_ids is not None and len(allowed_source_ids) == 0:
            return [], ""

        allowed_set: Optional[Set[str]] = set(allowed_source_ids) if allowed_source_ids is not None else None
        if allowed_set is not None:
            seed_results = [res for res in seed_results if getattr(res, "source_id", None) in allowed_set]
            if not seed_results:
                return [], ""

        meta_cache = source_meta_cache or {}

        # 1. Group seed hits by (document_id, section)
        # Identify min and max pos_index for each document group
        doc_ranges: Dict[str, Dict[str, Any]] = {}
        seed_chunk_ids: Set[str] = set()
        seed_scores: Dict[str, float] = {}

        for res in seed_results:
            seed_chunk_ids.add(res.chunk_id)
            seed_scores[res.chunk_id] = float(res.score)
            doc_id = res.document_id
            pos = res.index if res.index is not None else 0

            if doc_id not in doc_ranges:
                doc_ranges[doc_id] = {
                    "source_id": res.source_id,
                    "hit_positions": set(),
                    "windows": [],
                }
            doc_ranges[doc_id]["hit_positions"].add(pos)

        # 2. Compute fused expansion intervals [pos - 2, pos + 2] per document
        all_expanded_chunks: List[ExpandedChunk] = []

        with self.engine.transaction() as conn:
            cursor = conn.cursor()

            for doc_id, data in doc_ranges.items():
                hit_positions = sorted(data["hit_positions"])
                # Build intervals
                raw_intervals: List[Tuple[int, int]] = []
                for p in hit_positions:
                    start_pos = max(0, p - EXPANSION_WINDOW)
                    end_pos = p + EXPANSION_WINDOW
                    raw_intervals.append((start_pos, end_pos))

                # Merge overlapping or touching intervals
                merged_intervals: List[Tuple[int, int]] = []
                for interval in sorted(raw_intervals, key=lambda x: x[0]):
                    if not merged_intervals:
                        merged_intervals.append(interval)
                    else:
                        prev_start, prev_end = merged_intervals[-1]
                        if interval[0] <= prev_end + 1:
                            merged_intervals[-1] = (prev_start, max(prev_end, interval[1]))
                        else:
                            merged_intervals.append(interval)

                # Fetch all chunks in the merged intervals for this document
                for start_idx, end_idx in merged_intervals:
                    if allowed_set is not None:
                        placeholders = ",".join("?" for _ in allowed_set)
                        cursor.execute(
                            f"""
                            SELECT id, document_id, source_id, content, page_start,
                                   pos_index, section, token_count
                            FROM chunks
                            WHERE document_id = ? AND pos_index BETWEEN ? AND ?
                              AND source_id IN ({placeholders})
                            ORDER BY pos_index ASC;
                            """,
                            [doc_id, start_idx, end_idx] + list(allowed_set),
                        )
                    else:
                        cursor.execute(
                            """
                            SELECT id, document_id, source_id, content, page_start,
                                   pos_index, section, token_count
                            FROM chunks
                            WHERE document_id = ? AND pos_index BETWEEN ? AND ?
                            ORDER BY pos_index ASC;
                            """,
                            (doc_id, start_idx, end_idx),
                        )
                    rows = cursor.fetchall()

                    for r in rows:
                        c_id = r[0]
                        d_id = r[1]
                        s_id = r[2]
                        if allowed_set is not None and s_id not in allowed_set:
                            continue
                        content = r[3]
                        p_start = r[4] or 1
                        p_idx = r[5]
                        section = r[6] or ""
                        tok_count = r[7] or (len(content.split()) * 4 // 3)

                        meta = meta_cache.get(s_id, {})
                        src_title = meta.get("title") or s_id

                        is_seed = c_id in seed_chunk_ids
                        score = seed_scores.get(c_id, 0.5 if not is_seed else 0.85)

                        all_expanded_chunks.append(
                            ExpandedChunk(
                                chunk_id=c_id,
                                document_id=d_id,
                                source_id=s_id,
                                source_title=src_title,
                                page_start=p_start,
                                pos_index=p_idx,
                                section=section,
                                content=content,
                                is_seed_hit=is_seed,
                                relevance_score=score,
                                token_count=tok_count,
                            )
                        )

        # 3. Deduplicate across intervals while preserving order
        unique_chunks: Dict[str, ExpandedChunk] = {}
        for ec in all_expanded_chunks:
            if ec.chunk_id not in unique_chunks:
                unique_chunks[ec.chunk_id] = ec

        ordered_chunks = list(unique_chunks.values())

        # 4. Enforce Hard Ceiling (E23)
        # If total tokens exceed hard_ceiling_tokens, prioritize seeds and prune peripheral chunks
        total_tokens = sum(c.token_count for c in ordered_chunks)
        if total_tokens > self.hard_ceiling_tokens:
            logger.warning(
                "Hard ceiling exceeded (%d > %d tokens). Pruning peripheral chunks.",
                total_tokens,
                self.hard_ceiling_tokens,
            )
            # Sort: seeds first by relevance, then neighbors
            ordered_chunks.sort(key=lambda c: (1 if c.is_seed_hit else 0, c.relevance_score), reverse=True)
            accumulated: List[ExpandedChunk] = []
            curr_tokens = 0
            for c in ordered_chunks:
                if curr_tokens + c.token_count <= self.hard_ceiling_tokens:
                    accumulated.append(c)
                    curr_tokens += c.token_count
                else:
                    break
            # Re-sort accumulated by document and pos_index for coherent reading
            ordered_chunks = sorted(accumulated, key=lambda c: (c.document_id, c.pos_index))

        # 5. Format Context with Explicit Chunk Identifiers and Page Numbers (E26)
        formatted_lines: List[str] = []
        for c in ordered_chunks:
            tag = f"[CHUNK {c.pos_index} | Pág {c.page_start} | {c.source_title}]"
            formatted_lines.append(f"{tag}\n{c.content}\n")

        formatted_context = "\n".join(formatted_lines)
        return ordered_chunks, formatted_context
