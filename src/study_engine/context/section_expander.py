"""SectionExpander: Window Greedy Expansion with Hard-Ceiling for Large Context RAG (Ola 5, Fase 5.4, E23, E26).

Expands retrieval hits into contiguous chunk sections (±2 chunks using pos_index),
injects explicit position metadata to avoid floating citations (E26), and enforces
a strict hard ceiling (40,000 tokens for NORMAL/DEEP, up to 150K-1M for GLOBAL) (E23).
Cuts by BM25/vectorial relevance ranking upon exceeding budget.
"""

from dataclasses import dataclass
import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from study_engine.context.context_pack import ChunkWithProvenance, ExpandedSection
from study_engine.contracts.search import SearchResult
from study_engine.storage.sqlite_engine import SQLiteStorageEngine

logger = logging.getLogger(__name__)

HARD_CEILING_TOKENS = 40000
EXPANSION_WINDOW = 2  # ±2 chunks around each hit


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
    ) -> Tuple[List[ChunkWithProvenance], str]:
        """Expand seed results to contiguous sections and build formatted context.

        Returns:
            Tuple[List[ChunkWithProvenance], str]: List of expanded chunks and the formatted text pack.
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
                    "min_pos": max(0, pos - EXPANSION_WINDOW),
                    "max_pos": pos + EXPANSION_WINDOW,
                    "seed_positions": {pos},
                }
            else:
                doc_ranges[doc_id]["min_pos"] = min(doc_ranges[doc_id]["min_pos"], max(0, pos - EXPANSION_WINDOW))
                doc_ranges[doc_id]["max_pos"] = max(doc_ranges[doc_id]["max_pos"], pos + EXPANSION_WINDOW)
                doc_ranges[doc_id]["seed_positions"].add(pos)

        # 2. Fetch all contiguous chunks within ranges from SQLite storage
        expanded_chunks: List[ChunkWithProvenance] = []

        with self.engine.transaction() as conn:
            cur = conn.cursor()
            for doc_id, r_info in doc_ranges.items():
                min_p = r_info["min_pos"]
                max_p = r_info["max_pos"]
                src_id = r_info["source_id"]

                src_meta = meta_cache.get(src_id, {})
                src_title = src_meta.get("title") or src_id

                if allowed_set is not None:
                    placeholders = ",".join("?" for _ in allowed_set)
                    cur.execute(
                        f"""
                        SELECT id, document_id, source_id, content, page_start, pos_index, section, token_count
                        FROM chunks
                        WHERE document_id = ? AND pos_index >= ? AND pos_index <= ?
                          AND source_id IN ({placeholders})
                        ORDER BY pos_index ASC
                        """,
                        [doc_id, min_p, max_p] + list(allowed_set),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, document_id, source_id, content, page_start, pos_index, section, token_count
                        FROM chunks
                        WHERE document_id = ? AND pos_index >= ? AND pos_index <= ?
                        ORDER BY pos_index ASC
                        """,
                        (doc_id, min_p, max_p),
                    )
                rows = cur.fetchall()

                for row in rows:
                    c_id, d_id, s_id, content, p_start, p_idx, sec, tok_cnt = row
                    if allowed_set is not None and s_id not in allowed_set:
                        continue
                    is_seed = (c_id in seed_chunk_ids) or (p_idx in r_info["seed_positions"])
                    score = seed_scores.get(c_id, 0.70 if is_seed else 0.50)

                    expanded_chunks.append(
                        ChunkWithProvenance(
                            chunk_id=c_id,
                            document_id=d_id,
                            source_id=s_id,
                            source_title=src_title,
                            page_start=int(p_start or 1),
                            pos_index=int(p_idx or 0),
                            section=sec or "General",
                            content=content or "",
                            is_seed_hit=is_seed,
                            relevance_score=score,
                            token_count=int(tok_cnt or len(content.split())),
                        )
                    )

        # 3. Sort chunks: prioritize seed hits and high relevance if pruning is required
        total_tokens = sum(c.token_count for c in expanded_chunks)
        if total_tokens > self.hard_ceiling_tokens:
            logger.info(
                f"[EXPANSION CEILING] Total tokens ({total_tokens}) exceeds hard ceiling ({self.hard_ceiling_tokens}). Pruning by relevance."
            )
            # Sort by relevance score descending to prioritize most relevant chunks
            sorted_by_relevance = sorted(
                expanded_chunks,
                key=lambda x: (x.is_seed_hit, x.relevance_score),
                reverse=True,
            )
            retained: List[ChunkWithProvenance] = []
            curr_tokens = 0
            for chk in sorted_by_relevance:
                if curr_tokens + chk.token_count <= self.hard_ceiling_tokens:
                    retained.append(chk)
                    curr_tokens += chk.token_count
                else:
                    break

            # Re-sort retained chunks by natural reading order (document_id, pos_index)
            expanded_chunks = sorted(retained, key=lambda x: (x.document_id, x.pos_index))

        # 4. Invariant E26: Explicit position metadata [CHUNK X | Pág Y | Source]
        formatted_blocks: List[str] = []
        for chk in expanded_chunks:
            tag = f"[CHUNK {chk.pos_index} | Pág {chk.page_start} | {chk.source_title}]"
            formatted_blocks.append(f"{tag}\n{chk.content}")

        formatted_text = "\n\n".join(formatted_blocks)
        return expanded_chunks, formatted_text
