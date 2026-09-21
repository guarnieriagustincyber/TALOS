"""Evidence Coverage Evaluator for Subsystem S4.1 (V1.1).

Computes continuous quality scores across retrieved evidence chunks for each
decomposed sub-query and establishes pedagogical coverage status:
- SUFFICIENT (quality >= 0.7)
- PARTIAL (0.4 <= quality < 0.7)
- MISSING (quality < 0.4 or 0 chunks)
"""

import re
from typing import Any, Dict, List, Optional, Sequence, Union

from study_engine.contracts.evidence_engine import (
    CoverageStatus,
    EvidenceCoverageReport,
    SubQuery,
    SubQueryCoverage,
)
from study_engine.contracts.retrieval import ScoredCandidate

# Keywords that indicate pedagogical explanatory clarity in technical textbooks
CLARITY_KEYWORDS = [
    "ejemplo", "definición", "define", "consiste", "significa", "función",
    "permite", "estructura", "algoritmo", "proceso", "código", "demostración",
    "illustration", "example", "definition", "overview"
]


class EvidenceCoverageEvaluator:
    """Continuous quality score evaluator and pedagogical coverage reporter."""

    def __init__(
        self,
        sufficient_threshold: float = 0.70,
        partial_threshold: float = 0.40,
        min_depth_tokens: int = 150,
    ) -> None:
        """Initialize EvidenceCoverageEvaluator.

        Parameters
        ----------
        sufficient_threshold : float
            Minimum quality score required to declare SUFFICIENT coverage.
        partial_threshold : float
            Minimum quality score required to declare PARTIAL coverage.
        min_depth_tokens : int
            Target tokens threshold for full depth score.
        """
        self.sufficient_threshold = sufficient_threshold
        self.partial_threshold = partial_threshold
        self.min_depth_tokens = min_depth_tokens

    def calculate_quality_score(
        self,
        chunks: Sequence[ScoredCandidate],
        sub_query: Optional[SubQuery] = None,
    ) -> float:
        """Calculate continuous quality score for a set of chunks (Refinement 2).

        Formula:
        Quality = 0.4 * Depth + 0.3 * Relevance + 0.2 * Trust + 0.1 * Clarity

        Parameters
        ----------
        chunks : Sequence[ScoredCandidate]
            Retrieved candidate chunks associated with the sub-query.
        sub_query : Optional[SubQuery]
            The evaluated sub-query for topical matching.

        Returns
        -------
        float
            Continuous score in [0.0, 1.0].
        """
        if not chunks:
            return 0.0

        # 1. Depth score (tokens informative depth)
        total_tokens = sum(len(c.content.split()) for c in chunks)
        depth_score = min(1.0, total_tokens / float(self.min_depth_tokens))

        # 2. Relevance score (average or normalized score of chunks)
        avg_score = sum(c.score for c in chunks) / len(chunks)
        # Normalize score into [0.0, 1.0]
        relevance_score = max(0.0, min(1.0, avg_score))

        # If sub_query is given, check keyword overlap
        if sub_query is not None:
            sq_words = set(re.findall(r"\b\w{4,}\b", sub_query.text.lower()))
            if sq_words:
                combined_content = " ".join(c.content.lower() for c in chunks)
                overlap = sum(1 for w in sq_words if w in combined_content)
                overlap_ratio = overlap / len(sq_words)
                # Combine retrieval score with literal term overlap
                relevance_score = (0.6 * relevance_score) + (0.4 * overlap_ratio)

        # 3. Trust score (canonical vs unverified)
        trust_scores = [
            1.0 if c.metadata.get("trust_level", "canonical") == "canonical" else 0.5
            for c in chunks
        ]
        trust_score = max(trust_scores) if trust_scores else 0.5

        # 4. Pedagogical clarity score
        clarity_hits = 0
        for c in chunks:
            content_lower = c.content.lower()
            if any(kw in content_lower for kw in CLARITY_KEYWORDS):
                clarity_hits += 1
        clarity_score = clarity_hits / len(chunks)

        # Refinement 2 continuous formula:
        quality = (
            (0.4 * depth_score)
            + (0.3 * relevance_score)
            + (0.2 * trust_score)
            + (0.1 * clarity_score)
        )

        return round(max(0.0, min(1.0, quality)), 4)

    def evaluate_coverage(
        self,
        sub_queries: Sequence[SubQuery],
        selected_chunks: Union[Sequence[ScoredCandidate], Dict[str, Sequence[ScoredCandidate]]],
    ) -> EvidenceCoverageReport:
        """Evaluate coverage across all sub-queries.

        Parameters
        ----------
        sub_queries : Sequence[SubQuery]
            Prioritized sub-queries from QueryDecomposer.
        selected_chunks : Sequence[ScoredCandidate] or Dict[str, Sequence[ScoredCandidate]]
            Either a flat list of selected candidates (with metadata['sub_query_id'])
            or a dictionary mapping sub_query_id to candidate chunks.

        Returns
        -------
        EvidenceCoverageReport
            Authoritative coverage report detailing what is SUFFICIENT, PARTIAL, or MISSING.
        """
        # Map sub_query_id to its candidates
        chunks_by_sq: Dict[str, List[ScoredCandidate]] = {sq.sub_query_id: [] for sq in sub_queries}

        if isinstance(selected_chunks, dict):
            for sq_id, cands in selected_chunks.items():
                if sq_id in chunks_by_sq:
                    chunks_by_sq[sq_id].extend(cands)
                else:
                    chunks_by_sq[sq_id] = list(cands)
        else:
            for c in selected_chunks:
                sq_id = c.metadata.get("sub_query_id")
                if sq_id and sq_id in chunks_by_sq:
                    chunks_by_sq[sq_id].append(c)
                else:
                    # If candidate has no sub_query_id, assign to first or all
                    if len(sub_queries) == 1:
                        chunks_by_sq[sub_queries[0].sub_query_id].append(c)
                    else:
                        # Assign to the sub_query with highest word overlap
                        c_text_lower = c.content.lower()
                        best_sq_id = sub_queries[0].sub_query_id
                        best_overlap = -1
                        for sq in sub_queries:
                            words = set(re.findall(r"\b\w{4,}\b", sq.text.lower()))
                            overlap = sum(1 for w in words if w in c_text_lower)
                            if overlap > best_overlap:
                                best_overlap = overlap
                                best_sq_id = sq.sub_query_id
                        chunks_by_sq[best_sq_id].append(c)

        coverage_items: List[SubQueryCoverage] = []
        sufficient_count = 0

        for sq in sub_queries:
            assigned = chunks_by_sq.get(sq.sub_query_id, [])
            quality = self.calculate_quality_score(assigned, sub_query=sq)

            if quality >= self.sufficient_threshold:
                status = CoverageStatus.SUFFICIENT
                sufficient_count += 1
            elif quality >= self.partial_threshold:
                status = CoverageStatus.PARTIAL
            else:
                status = CoverageStatus.MISSING

            source_ids = list({c.source_id for c in assigned})

            coverage_items.append(
                SubQueryCoverage(
                    sub_query_id=sq.sub_query_id,
                    sub_query_text=sq.text,
                    status=status,
                    quality_score=quality,
                    chunks_count=len(assigned),
                    source_ids=source_ids,
                )
            )

        overall_ratio = (
            sufficient_count / len(sub_queries) if sub_queries else 1.0
        )

        return EvidenceCoverageReport(
            sub_queries=list(sub_queries),
            coverage=coverage_items,
            overall_coverage_ratio=round(overall_ratio, 4),
        )
