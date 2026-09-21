"""Federated Query Planner with G1-G4 Anti-Error Guardrails (Phase E4, Amendments E4-4, E4-5, E4-R1).

Decomposes cross-curricular user queries across sovereign notebooks using:
1. Active Notebook Confinement: Default isolation unless authorized bridge exists.
2. CurriculumGate Pre-Retrieval predicates (CHSR-RRF pattern).
3. Guardrails G1-G4:
   - G1: Topic coverage validation via Notebook Authority Matrix.
   - G2: Bridge authorization, directionality, and fail-closed TTL (BRIDGE_EXPIRED).
   - G3: Anti-cycle loop prevention across traversal paths.
   - G4: Empty or malformed topic rejection (fail-closed, PLAN_UNSUPPORTED).
4. Deterministic Deduplication:
   - Tie-breaking key: (-authority_weight, doc_id, chunk_id)
5. DecompositionValidity evaluation metric (E4-R1 >= 90%).
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, ConfigDict, Field

from study_engine.federation.notebook_registry import Notebook, NotebookRegistry
from study_engine.federation.curriculum_gate import CurriculumGate, ScopeConstraint
from study_engine.federation.bridge_registry import BridgeRegistry, CrossNotebookBridge


class FederatedSubQuery(BaseModel):
    """Sub-query targeted at a specific sovereign notebook."""

    model_config = ConfigDict(frozen=True)

    subquery_id: str = Field(..., min_length=1)
    target_notebook_id: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    query_text: str = Field(..., min_length=1)
    bridge_id: Optional[str] = Field(default=None)
    scope_constraint: ScopeConstraint
    authority_weight: float = Field(default=1.0, ge=0.1, le=2.0)


class FederatedPlan(BaseModel):
    """Execution plan for federated cross-notebook retrieval."""

    model_config = ConfigDict(frozen=True)

    plan_id: str = Field(..., min_length=1)
    active_notebook_id: str = Field(..., min_length=1)
    original_query: str = Field(default="")
    subqueries: List[FederatedSubQuery] = Field(default_factory=list)
    is_cross_curricular: bool = Field(default=False)
    status: str = Field(default="READY")  # READY, PLAN_UNSUPPORTED, GUARDRAIL_REJECTED
    rejection_reason: Optional[str] = Field(default=None)
    guardrail_code: Optional[str] = Field(default=None)  # G1, G2, G3, G4


class FederatedRetrievalCandidate(BaseModel):
    """Retrieved candidate chunk enriched with federation provenance."""

    model_config = ConfigDict(frozen=True)

    chunk_id: str
    doc_id: str
    notebook_id: str
    content: str
    content_hash: str
    authority_weight: float
    retrieval_score: float
    bridge_id: Optional[str] = None
    stale_bridge_result: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FederatedQueryPlanner:
    """Plans and executes deterministic cross-notebook federated retrieval."""

    def __init__(
        self,
        notebook_registry: NotebookRegistry,
        bridge_registry: BridgeRegistry,
        curriculum_gate: Optional[CurriculumGate] = None,
    ) -> None:
        self.notebook_registry = notebook_registry
        self.bridge_registry = bridge_registry
        self.curriculum_gate = curriculum_gate or CurriculumGate()

    def plan_query(
        self,
        active_notebook_id: str,
        query_text: str,
        topics: Optional[List[str]] = None,
        now: Optional[datetime] = None,
    ) -> FederatedPlan:
        """Construct a federated query execution plan with G1-G4 guardrails."""
        current_time = now or datetime.now(timezone.utc)
        clean_query = query_text.strip()
        plan_id = f"plan-{hashlib.sha256(f'{active_notebook_id}:{clean_query}:{current_time.isoformat()}'.encode()).hexdigest()[:12]}"

        # Guardrail G4: Empty or malformed topic / query check
        if not clean_query or (topics is not None and len(topics) == 0):
            return FederatedPlan(
                plan_id=plan_id,
                active_notebook_id=active_notebook_id,
                original_query=clean_query,
                status="PLAN_UNSUPPORTED",
                rejection_reason="G4: Query or topic list is empty.",
                guardrail_code="G4",
            )

        # Validate active notebook existence
        active_nb = self.notebook_registry.get_notebook(active_notebook_id)
        if not active_nb or not active_nb.is_active:
            return FederatedPlan(
                plan_id=plan_id,
                active_notebook_id=active_notebook_id,
                original_query=clean_query,
                status="PLAN_UNSUPPORTED",
                rejection_reason=f"G1: Active notebook '{active_notebook_id}' is not registered or active.",
                guardrail_code="G1",
            )

        # Detect relevant topics from text if not explicitly provided
        extracted_topics = topics if topics is not None else self._detect_topics(clean_query)
        if not extracted_topics:
            # Confinement to active notebook with generic topic
            sub_id = f"sub-{active_notebook_id}-generic"
            constraint = ScopeConstraint(notebook_id=active_notebook_id)
            subquery = FederatedSubQuery(
                subquery_id=sub_id,
                target_notebook_id=active_notebook_id,
                topic="generic",
                query_text=clean_query,
                scope_constraint=constraint,
                authority_weight=1.0,
            )
            return FederatedPlan(
                plan_id=plan_id,
                active_notebook_id=active_notebook_id,
                original_query=clean_query,
                subqueries=[subquery],
                is_cross_curricular=False,
                status="READY",
            )

        # Decompose across notebooks
        subqueries: List[FederatedSubQuery] = []
        is_cross = False
        visited_notebooks: Set[str] = {active_notebook_id}

        # Subquery for active notebook
        for t in extracted_topics:
            t_clean = t.lower().strip()
            auth = self.notebook_registry.get_authority_weight(active_notebook_id, t_clean)
            constraint = ScopeConstraint(notebook_id=active_notebook_id)
            subqueries.append(
                FederatedSubQuery(
                    subquery_id=f"sub-{active_notebook_id}-{t_clean}",
                    target_notebook_id=active_notebook_id,
                    topic=t_clean,
                    query_text=clean_query,
                    scope_constraint=constraint,
                    authority_weight=auth,
                )
            )

        # Evaluate external notebooks for cross-curricular topics
        other_notebooks = [nb for nb in self.notebook_registry.list_notebooks() if nb.notebook_id != active_notebook_id]

        for ext_nb in other_notebooks:
            for t in extracted_topics:
                t_clean = t.lower().strip()
                # Check if target notebook has topical authority for this topic
                if t_clean in ext_nb.authority_matrix_ref:
                    # Guardrail G3: Cyclic loop prevention
                    if ext_nb.notebook_id in visited_notebooks and ext_nb.notebook_id != active_notebook_id:
                        continue

                    # Guardrail G2: Bridge authorization and TTL check
                    auth_ok, reason, bridge = self.bridge_registry.is_bridge_authorized(
                        source_nb=active_notebook_id,
                        target_nb=ext_nb.notebook_id,
                        topic=t_clean,
                        now=current_time,
                    )
                    if not auth_ok:
                        if "expired" in (reason or "").lower():
                            return FederatedPlan(
                                plan_id=plan_id,
                                active_notebook_id=active_notebook_id,
                                original_query=clean_query,
                                status="GUARDRAIL_REJECTED",
                                rejection_reason=f"G2: Cross-notebook bridge expired ({reason})",
                                guardrail_code="G2",
                            )
                        # Not authorized; strict isolation applies (ignore target notebook)
                        continue

                    # Authorized bridge exists
                    is_cross = True
                    visited_notebooks.add(ext_nb.notebook_id)
                    ext_auth = ext_nb.authority_matrix_ref.get(t_clean, 1.0)
                    constraint = ScopeConstraint(
                        notebook_id=ext_nb.notebook_id,
                        bridge_id=bridge.bridge_id if bridge else None,
                    )
                    subqueries.append(
                        FederatedSubQuery(
                            subquery_id=f"sub-{ext_nb.notebook_id}-{t_clean}",
                            target_notebook_id=ext_nb.notebook_id,
                            topic=t_clean,
                            query_text=clean_query,
                            bridge_id=bridge.bridge_id if bridge else None,
                            scope_constraint=constraint,
                            authority_weight=ext_auth,
                        )
                    )

        return FederatedPlan(
            plan_id=plan_id,
            active_notebook_id=active_notebook_id,
            original_query=clean_query,
            subqueries=subqueries,
            is_cross_curricular=is_cross,
            status="READY",
        )

    def _detect_topics(self, query_text: str) -> List[str]:
        """Deterministic topic detection based on registered notebook authorities."""
        clean = query_text.lower()
        detected: List[str] = []
        for nb in self.notebook_registry.list_notebooks():
            for topic in nb.authority_matrix_ref.keys():
                if topic in clean and topic not in detected:
                    detected.append(topic)
        return detected

    def deduplicate_candidates(
        self,
        candidates: List[FederatedRetrievalCandidate],
    ) -> List[FederatedRetrievalCandidate]:
        """Deduplicate candidates deterministically across federated subqueries (Amendment E4-5).

        When identical content or content_hash appears from multiple notebooks/sources:
        Tie-breaking key: (-authority_weight, doc_id, chunk_id)
        """
        # Filter out stale bridge results first (Amendment E4-2)
        valid_candidates = [c for c in candidates if not c.stale_bridge_result]

        # Group by content_hash
        groups: Dict[str, List[FederatedRetrievalCandidate]] = {}
        for c in valid_candidates:
            h = c.content_hash
            if h not in groups:
                groups[h] = []
            groups[h].append(c)

        deduped: List[FederatedRetrievalCandidate] = []
        for h, group in groups.items():
            # Sort group by (-authority_weight, doc_id, chunk_id)
            sorted_group = sorted(
                group,
                key=lambda x: (-x.authority_weight, x.doc_id, x.chunk_id),
            )
            deduped.append(sorted_group[0])

        # Final ordering by authority-adjusted score
        deduped.sort(key=lambda x: (-x.retrieval_score * x.authority_weight, x.doc_id, x.chunk_id))
        return deduped

    def evaluate_decomposition_validity(self, plans: List[FederatedPlan]) -> float:
        """Calculate DecompositionValidity (E4-R1 >= 90%).

        Measures fraction of queries with valid, non-empty, sound subquery partitions.
        """
        if not plans:
            return 1.0
        valid_count = 0
        for p in plans:
            if p.status == "READY" and len(p.subqueries) > 0:
                # Ensure all subqueries have non-empty targets and constraints
                if all(sq.target_notebook_id and sq.scope_constraint for sq in p.subqueries):
                    valid_count += 1
        return valid_count / len(plans)
