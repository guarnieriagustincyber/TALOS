"""Greedy Submodular Marginal Selection Engine for Subsystem S4.1 (E1.1 Specification).

Operates at the paragraph / logical block level (150-400 tokens) to preserve
rhetorical and pedagogical context (arXiv:2607.00725).

Implements density-based marginal gain maximization with 5 terms:
  Gain(c|S) = w_c * ΔC(S∪{c})
            + w_s * ΔSource(S∪{c})
            + w_a * Authority(c, topic)
            - w_r * SoftRedundancy(c, S)
            - w_x * ContradictionRisk(c, S)
  DensityGain(c|S) = Gain(c|S) / tokens(c)^β

Features:
- Global query as dominant anchor facet (w=0.40) + atomic facets (w=0.60)
- Strict separation: τ_pool = 0.40 (evaluation pool) vs τ_admit = 0.70 (admission floor)
- Continuous Soft Redundancy with τ_red = 0.82 (replaces hard thresholding)
- Dialectic Contradiction Detection & Freeze Rule
- Source diversity capping: K_source <= 3
"""

from dataclasses import dataclass, field
import hashlib
import math
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from pydantic import BaseModel, Field

from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.evidence.authority_promotion import TopicAuthorityManager
from study_engine.retrieval.stage_aware_decomposer import AtomicFacet, StageAwareDecomposer


class GreedySelectionResult(BaseModel):
    """Result of greedy submodular marginal selection."""

    selected_chunks: List[ScoredCandidate]
    total_tokens: int
    facet_coverage: Dict[str, float]
    overall_coverage: float
    sources_represented: List[str]
    contradiction_detected: bool = False
    contradiction_pair: Optional[Tuple[str, str]] = None
    selector_gap_occurred: bool = False
    diagnostics: Dict[str, Any] = Field(default_factory=dict)


def count_tokens(text: str) -> int:
    """Approximate token count via whitespace split."""
    return max(1, len(text.split()))


def compute_chunk_similarity(c_a: ScoredCandidate, c_b: ScoredCandidate) -> float:
    """Compute semantic/lexical similarity between two chunks."""
    # Lexical Jaccard on 3+ char words
    toks_a = set(re.findall(r"\w{3,}", c_a.content.lower()))
    toks_b = set(re.findall(r"\w{3,}", c_b.content.lower()))
    if not toks_a or not toks_b:
        return 0.0
    return len(toks_a & toks_b) / len(toks_a | toks_b)


class GreedyMarginalSelector:
    """Submodular Greedy Evidence Selector with token density marginal gain."""

    def __init__(
        self,
        tau_pool: float = 0.40,
        tau_admit: float = 0.70,
        tau_red: float = 0.82,
        max_chunks: int = 8,
        max_tokens: int = 2000,
        max_per_source: int = 3,
        beta_cost_exponent: float = 0.50,
        marginal_threshold_delta: float = 0.0,
        w_coverage: float = 0.45,
        w_source: float = 0.15,
        w_authority: float = 0.15,
        w_redundancy: float = 0.15,
        w_contradiction: float = 0.10,
        authority_manager: Optional[TopicAuthorityManager] = None,
    ) -> None:
        self.tau_pool = tau_pool
        self.tau_admit = tau_admit
        self.tau_red = tau_red
        self.max_chunks = max_chunks
        self.max_tokens = max_tokens
        self.max_per_source = max_per_source
        self.beta = beta_cost_exponent
        self.delta = marginal_threshold_delta

        # Weights
        self.w_c = w_coverage
        self.w_s = w_source
        self.w_a = w_authority
        self.w_r = w_redundancy
        self.w_x = w_contradiction

        self.authority_manager = authority_manager

    def select(
        self,
        candidates: Sequence[ScoredCandidate],
        global_query: str,
        facets: Optional[Sequence[AtomicFacet]] = None,
        topic_id: Optional[str] = None,
        known_contradiction_pairs: Optional[List[Tuple[str, str]]] = None,
    ) -> GreedySelectionResult:
        """Execute greedy submodular selection over candidate evidence pool."""
        # 1. Filter candidates by tau_pool and deduplicate
        pool: List[ScoredCandidate] = []
        seen_hashes: Set[str] = set()

        for c in candidates:
            if c.score < self.tau_pool:
                continue
            c_hash = hashlib.sha256(c.content.encode("utf-8")).hexdigest()
            if c_hash in seen_hashes:
                continue
            seen_hashes.add(c_hash)
            pool.append(c)

        if not pool:
            return GreedySelectionResult(
                selected_chunks=[],
                total_tokens=0,
                facet_coverage={},
                overall_coverage=0.0,
                sources_represented=[],
                selector_gap_occurred=False,
                diagnostics={"reason": "EMPTY_POOL_ABOVE_TAU_POOL"},
            )

        # 2. Build Facets with Global Query Anchor
        all_facets: List[AtomicFacet] = []
        f_global = AtomicFacet(
            facet_id="f-global",
            text=global_query,
            anchor_terms=[],
            weight=0.40 if facets else 1.0,
        )
        all_facets.append(f_global)

        if facets:
            m = len(facets)
            facet_weight = 0.60 / max(1, m)
            for f in facets:
                f_copy = f.model_copy(update={"weight": facet_weight})
                all_facets.append(f_copy)

        # 3. Initialize Selection State
        selected: List[ScoredCandidate] = []
        source_counts: Dict[str, int] = {}
        total_tokens_used = 0
        current_facet_cov: Dict[str, float] = {f.facet_id: 0.0 for f in all_facets}

        contra_pairs = known_contradiction_pairs or [
            ("joyanes_fundamentos", "ramalho_fluent_python"),
            ("joyanes_fundamentos", "goodrich_dsa_python"),
            ("joyanes_fundamentos", "martin_clean_code"),
        ]
        contra_detected = False
        detected_pair: Optional[Tuple[str, str]] = None

        # Track valid evidence in pool to diagnose SelectorGap
        has_valid_in_pool = any(c.score >= self.tau_admit for c in pool)

        # 4. Greedy Selection Loop
        remaining = list(pool)

        while remaining and len(selected) < self.max_chunks and total_tokens_used < self.max_tokens:
            best_cand: Optional[ScoredCandidate] = None
            best_density_gain: float = -float("inf")
            best_delta_cov: float = 0.0

            for cand in remaining:
                cand_source = getattr(cand, "source_id", "unknown")
                if source_counts.get(cand_source, 0) >= self.max_per_source:
                    continue

                # Ensure candidate meets admission threshold or has high potential
                if cand.score < self.tau_pool:
                    continue

                # Term 1: Marginal Coverage Gain ΔC(S ∪ {c})
                delta_c = 0.0
                for f in all_facets:
                    cand_f_cov = StageAwareDecomposer.score_facet_coverage(cand.content, f)
                    old_cov = current_facet_cov[f.facet_id]
                    new_cov = min(1.0, max(old_cov, cand_f_cov))
                    delta_c += f.weight * (new_cov - old_cov)

                # Term 2: Source Novelty Bonus ΔSource(S ∪ {c})
                delta_source = 1.0 if cand_source not in source_counts else 0.0

                # Term 3: Authority Bonus
                auth_bonus = 0.0
                if self.authority_manager:
                    auth_bonus = self.authority_manager.compute_authority_bonus(
                        candidate_source_id=cand_source,
                        topic_id=topic_id,
                        relevance_score=cand.score,
                    )

                # Term 4: Continuous Soft Redundancy Penalty (τ_red = 0.82)
                soft_red = 0.0
                for s in selected:
                    sim = compute_chunk_similarity(cand, s)
                    if sim > self.tau_red:
                        soft_red += (sim - self.tau_red)

                # Term 5: Contradiction Risk
                contra_risk = 0.0
                for s in selected:
                    s_source = getattr(s, "source_id", "unknown")
                    for pair in contra_pairs:
                        if (cand_source == pair[0] and s_source == pair[1]) or (
                            cand_source == pair[1] and s_source == pair[0]
                        ):
                            contra_risk = 1.0
                            break

                # Net Marginal Gain
                net_gain = (
                    (self.w_c * delta_c)
                    + (self.w_s * delta_source)
                    + (self.w_a * auth_bonus)
                    - (self.w_r * soft_red)
                    - (self.w_x * contra_risk)
                )

                # Density Gain: Gain / tokens^β
                c_tokens = count_tokens(cand.content)
                cost_term = math.pow(max(1, c_tokens), self.beta)
                density_gain = net_gain / cost_term

                if density_gain > best_density_gain:
                    best_density_gain = density_gain
                    best_cand = cand
                    best_delta_cov = delta_c

            # Check stopping criteria
            if best_cand is None or best_density_gain < self.delta:
                break

            # Check if adding best_cand exceeds token budget
            best_tokens = count_tokens(best_cand.content)
            if total_tokens_used + best_tokens > self.max_tokens and selected:
                break

            # Check Contradiction Freeze Rule
            best_source = getattr(best_cand, "source_id", "unknown")
            for s in selected:
                s_source = getattr(s, "source_id", "unknown")
                for pair in contra_pairs:
                    if (best_source == pair[0] and s_source == pair[1]) or (
                        best_source == pair[1] and s_source == pair[0]
                    ):
                        if best_cand.score >= self.tau_admit:
                            contra_detected = True
                            detected_pair = pair

            # Commit best candidate
            selected.append(best_cand)
            source_counts[best_source] = source_counts.get(best_source, 0) + 1
            total_tokens_used += best_tokens
            remaining.remove(best_cand)

            # Update coverage
            for f in all_facets:
                cand_f_cov = StageAwareDecomposer.score_facet_coverage(best_cand.content, f)
                current_facet_cov[f.facet_id] = min(1.0, max(current_facet_cov[f.facet_id], cand_f_cov))

            # If contradiction detected, freeze set to preserve both dialectic poles
            if contra_detected:
                break

            # Stop if all facets reached SUFFICIENT (>= 0.70)
            if all(cov >= 0.70 for cov in current_facet_cov.values()):
                break

        # Filter final selected list with tau_admit if not dialectic
        admitted = [c for c in selected if c.score >= self.tau_admit or contra_detected]
        if not admitted and selected:
            # If none reached tau_admit, keep top candidate if above tau_pool to avoid hard gap
            admitted = [selected[0]]

        # Re-rank admitted items
        for rank_idx, c in enumerate(admitted, start=1):
            c.rank = rank_idx

        # Calculate final overall coverage
        overall_cov = sum(all_facets[i].weight * current_facet_cov[all_facets[i].facet_id] for i in range(len(all_facets)))

        # Diagnose Selector Gap: Valid evidence existed in pool (>= tau_admit) but 0 chunks admitted
        selector_gap = has_valid_in_pool and len(admitted) == 0

        sources_rep = list(set(getattr(c, "source_id", "unknown") for c in admitted))

        return GreedySelectionResult(
            selected_chunks=admitted,
            total_tokens=total_tokens_used,
            facet_coverage={fid: round(val, 4) for fid, val in current_facet_cov.items()},
            overall_coverage=round(overall_cov, 4),
            sources_represented=sources_rep,
            contradiction_detected=contra_detected,
            contradiction_pair=detected_pair,
            selector_gap_occurred=selector_gap,
            diagnostics={
                "pool_size": len(pool),
                "admitted_count": len(admitted),
                "tokens_budget_used": total_tokens_used,
                "contradiction_freeze": contra_detected,
            },
        )
