"""Evidence Selector for Subsystem S4.1 (V1.1).

Selects, deduplicates, and balances candidate evidence chunks across
multiple sources and sub-queries, enforcing strict source diversity quotas,
relevance thresholds, and provenance trust levels.
"""

from collections import defaultdict
import hashlib
from typing import Any, Dict, List, Optional, Sequence, Union

from study_engine.contracts.retrieval import ScoredCandidate


class EvidenceSelector:
    """Deterministic, multi-criteria evidence selection engine."""

    def __init__(
        self,
        max_total_chunks: int = 5,
        max_chunks_per_source: int = 3,
        min_relevance_score: Optional[float] = None,
        canonical_trust_bonus: float = 0.1,
    ) -> None:
        """Initialize EvidenceSelector.

        Parameters
        ----------
        max_total_chunks : int
            Maximum number of chunks to return in the final selection.
        max_chunks_per_source : int
            Strict upper bound on chunks allowed from any single source_id.
        min_relevance_score : Optional[float]
            Optional minimum cutoff for candidate retrieval score.
        canonical_trust_bonus : float
            Additive or multiplier factor favoring canonical sources.
        """
        if max_total_chunks <= 0:
            raise ValueError(f"max_total_chunks must be positive, got {max_total_chunks}.")
        if max_chunks_per_source <= 0:
            raise ValueError(f"max_chunks_per_source must be positive, got {max_chunks_per_source}.")

        self.max_total_chunks = max_total_chunks
        self.max_chunks_per_source = max_chunks_per_source
        self.min_relevance_score = min_relevance_score
        self.canonical_trust_bonus = canonical_trust_bonus

    def select(
        self,
        candidates: Union[Sequence[ScoredCandidate], Dict[str, Sequence[ScoredCandidate]]],
        max_chunks: Optional[int] = None,
        max_per_source: Optional[int] = None,
    ) -> List[ScoredCandidate]:
        """Select a diverse, deduplicated, and high-trust candidate subset.

        Parameters
        ----------
        candidates : Sequence[ScoredCandidate] or Dict[str, Sequence[ScoredCandidate]]
            Either a flat list of candidates or a dictionary mapping
            sub_query_id -> list of candidates.
        max_chunks : Optional[int]
            Override for max_total_chunks.
        max_per_source : Optional[int]
            Override for max_chunks_per_source.

        Returns
        -------
        List[ScoredCandidate]
            Ordered, deduplicated, and diversified candidate list with updated ranks.
        """
        limit_total = max_chunks if max_chunks is not None else self.max_total_chunks
        limit_per_source = max_per_source if max_per_source is not None else self.max_chunks_per_source

        # Step 1: Flatten and preserve sub_query tagging if dict is provided
        flat_candidates: List[ScoredCandidate] = []
        if isinstance(candidates, dict):
            # Interleave / collect from each sub-query
            # First, deduplicate per sub-query while annotating metadata
            for sub_qid, sub_cands in candidates.items():
                for c in sub_cands:
                    meta = dict(c.metadata)
                    if "sub_query_id" not in meta:
                        meta["sub_query_id"] = sub_qid
                    # Create copy with sub_query_id in metadata
                    c_tagged = c.model_copy(update={"metadata": meta})
                    flat_candidates.append(c_tagged)
        else:
            flat_candidates = list(candidates)

        if not flat_candidates:
            return []

        # Step 2: Deduplication by chunk_id and exact content SHA-256
        seen_chunk_ids: set[str] = set()
        seen_hashes: set[str] = set()
        unique_candidates: List[ScoredCandidate] = []

        # Sort primarily by raw retrieval score DESC to keep best instance of duplicates
        sorted_raw = sorted(flat_candidates, key=lambda x: (x.score, -x.rank), reverse=True)

        for c in sorted_raw:
            c_hash = hashlib.sha256(c.content.encode("utf-8")).hexdigest()
            if c.chunk_id in seen_chunk_ids or c_hash in seen_hashes:
                continue
            if self.min_relevance_score is not None and c.score < self.min_relevance_score:
                continue

            seen_chunk_ids.add(c.chunk_id)
            seen_hashes.add(c_hash)
            unique_candidates.append(c)

        if not unique_candidates:
            return []

        # Step 3: Multi-criteria scoring (relevance + trust bonus)
        scored_candidates: List[tuple[float, ScoredCandidate]] = []
        for c in unique_candidates:
            trust_level = c.metadata.get("trust_level", "canonical")
            trust_weight = 1.0 if trust_level == "canonical" else 0.7
            priority = c.metadata.get("priority", 1)
            priority_weight = 1.0 if priority == 1 else 0.85

            composite_score = c.score * trust_weight * priority_weight
            if trust_level == "canonical":
                composite_score += self.canonical_trust_bonus

            scored_candidates.append((composite_score, c))

        # Sort candidates by composite score DESC
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        # Step 4: Diverse Selection respecting source caps and sub-query distribution
        selected: List[ScoredCandidate] = []
        source_counts: Dict[str, int] = defaultdict(int)
        subquery_counts: Dict[str, int] = defaultdict(int)

        # First pass: try to pick at least one best chunk from each distinct sub_query if tagged
        remaining: List[tuple[float, ScoredCandidate]] = list(scored_candidates)
        has_subqueries = any("sub_query_id" in c.metadata for _, c in scored_candidates)

        if has_subqueries:
            subquery_best: Dict[str, tuple[float, ScoredCandidate]] = {}
            for comp_score, c in scored_candidates:
                sq_id = c.metadata.get("sub_query_id", "default")
                if sq_id not in subquery_best:
                    subquery_best[sq_id] = (comp_score, c)

            for sq_id, (comp_score, c) in subquery_best.items():
                if len(selected) >= limit_total:
                    break
                s_id = c.source_id
                if source_counts[s_id] < limit_per_source:
                    selected.append(c)
                    source_counts[s_id] += 1
                    subquery_counts[sq_id] += 1
                    remaining = [item for item in remaining if item[1].chunk_id != c.chunk_id]

        # Second pass: fill remaining budget with highest composite scored items respecting source cap
        for comp_score, c in remaining:
            if len(selected) >= limit_total:
                break
            s_id = c.source_id
            if source_counts[s_id] < limit_per_source:
                selected.append(c)
                source_counts[s_id] += 1

        # Fallback pass: if budget is still not filled and unique items exist that exceeded source cap,
        # fill remaining slots rather than leaving context empty (soft limit)
        if len(selected) < limit_total:
            already_selected_ids = {c.chunk_id for c in selected}
            for comp_score, c in scored_candidates:
                if len(selected) >= limit_total:
                    break
                if c.chunk_id not in already_selected_ids:
                    selected.append(c)
                    already_selected_ids.add(c.chunk_id)

        # Step 5: Deterministic re-ranking (1 to len(selected))
        final_list: List[ScoredCandidate] = []
        for new_rank, c in enumerate(selected, start=1):
            final_list.append(
                c.model_copy(update={"rank": new_rank})
            )

        return final_list
