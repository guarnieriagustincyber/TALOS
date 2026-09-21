"""Epistemic Evidence Utilization (EEU) Metric Engine (V1.2 Specification).

Formulation:
  EEU = 1.0 if Out-of-Domain AND Verdict == ABSTAINED (Honest abstention is rewarded)
  EEU = 0.0 if Verdict in (REJECTED_HALLUCINATION, REJECTED_INJECTION)
  EEU = utilization_rate * (1 - redundancy_penalty) for APPROVED / PARTIAL answers
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple


def compute_lexical_jaccard(text_a: str, text_b: str) -> float:
    """Compute token-level Jaccard similarity between two texts."""
    tokens_a = set(re.findall(r"\w+", text_a.lower()))
    tokens_b = set(re.findall(r"\w+", text_b.lower()))
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    return len(intersection) / max(1, len(union))


def compute_multidimensional_redundancy(
    chunks: List[Any],
    sub_query_mapping: Optional[Dict[str, str]] = None,
) -> float:
    """Compute multidimensional soft redundancy penalty across selected chunks.
    
    Invariants from V1.2:
      Overlap(C, S) = LexicalJaccard(C, S) * Indicator(SameSubTopic)
      RedundancyPenalty is average of pairwise overlaps above 0.40 threshold.
    """
    if len(chunks) <= 1:
        return 0.0

    overlaps: List[float] = []
    n = len(chunks)

    for i in range(n):
        for j in range(i + 1, n):
            c_a = chunks[i]
            c_b = chunks[j]

            text_a = getattr(c_a, "content", "") or getattr(c_a, "text", "")
            text_b = getattr(c_b, "content", "") or getattr(c_b, "text", "")

            # If chunks come from identical source and adjacent pages, soft overlap
            jaccard = compute_lexical_jaccard(text_a, text_b)

            # Check same sub-query / sub-topic if mapping provided
            cid_a = getattr(c_a, "chunk_id", str(i))
            cid_b = getattr(c_b, "chunk_id", str(j))
            same_subquery = (
                sub_query_mapping.get(cid_a) == sub_query_mapping.get(cid_b)
                if sub_query_mapping
                else True
            )

            if same_subquery and jaccard > 0.35:
                overlaps.append(jaccard)

    if not overlaps:
        return 0.0

    return min(1.0, sum(overlaps) / len(overlaps))


def calculate_eeu(
    chunks_sent: List[Any],
    chunks_cited: List[str],
    audit_verdict: str,
    is_out_of_domain: bool = False,
    sub_query_mapping: Optional[Dict[str, str]] = None,
    min_citations_threshold: int = 1,
) -> float:
    """Calculate Epistemic Evidence Utilization score (0.0 to 1.0).

    Args:
        chunks_sent: Chunks packaged into context and provided to the generation step.
        chunks_cited: Chunk IDs explicitly cited in the final generated answer.
        audit_verdict: S4.4 audit verdict ('APPROVED', 'PARTIAL', 'ABSTAINED', 'REJECTED_...').
        is_out_of_domain: Whether the ground truth query was outside corpus scope.
        sub_query_mapping: Mapping from chunk_id to target sub-query for redundancy grouping.
        min_citations_threshold: Minimum citations required for full utilization score.

    Returns:
        EEU score bounded between 0.0 and 1.0.
    """
    verdict_upper = audit_verdict.upper()

    # 1. Legitimate abstention case (Honest fail-closed)
    if is_out_of_domain:
        if "ABSTAIN" in verdict_upper or verdict_upper == "REJECTED_OUT_OF_DOMAIN":
            return 1.0
        # If system answered an out-of-domain query instead of abstaining: fatal hallucination
        return 0.0

    # 2. Rejection for hallucination or prompt injection
    if "HALLUCINATION" in verdict_upper or "INJECTION" in verdict_upper:
        return 0.0

    # If system abstained on an in-corpus query (False Abstention)
    if "ABSTAIN" in verdict_upper:
        return 0.1

    total_sent = len(chunks_sent)
    if total_sent == 0:
        return 0.0

    # 3. Real citation utilization rate
    # Unique cited chunks that were actually present in chunks_sent
    sent_ids = {getattr(c, "chunk_id", str(c)) for c in chunks_sent}
    valid_cited = {cid for cid in chunks_cited if cid in sent_ids}
    
    # If chunks_cited is empty in retrieval-only evaluation, estimate utilization from coverage
    if not chunks_cited:
        # Standalone retrieval benchmark proxy: high relevance chunks / total sent
        high_rel = [
            c for c in chunks_sent
            if getattr(c, "score", 0.0) >= 0.70 or getattr(c, "lexical_score", 0.0) >= 0.70
        ]
        utilization_rate = len(high_rel) / max(1, total_sent)
    else:
        utilization_rate = len(valid_cited) / max(1, total_sent)

    # 4. Multidimensional Soft Redundancy Penalty
    redundancy_penalty = compute_multidimensional_redundancy(
        chunks=chunks_sent,
        sub_query_mapping=sub_query_mapping,
    )

    # 5. Final EEU Score
    eeu = utilization_rate * (1.0 - (0.5 * redundancy_penalty))
    return max(0.0, min(1.0, round(eeu, 4)))
