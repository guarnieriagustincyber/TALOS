"""Query Decomposer for Subsystem S4.1 (V1.1).

Decomposes complex student queries into bounded, prioritized sub-queries
under pedagogical governance and curricular isolation constraints.
"""

import logging
import re
from typing import Any, Dict, List, Optional
import unicodedata

from study_engine.contracts.evidence_engine import SubQuery, SubQueryDecomposition

logger = logging.getLogger(__name__)

MAX_SUBQUERIES = 5

# Common clause splitters in Spanish and English pedagogical technical queries
SPLIT_PATTERNS = [
    r",\s*(?:y\s+)?(?:cómo|como|qué|que|cuáles|cuales|por\s+qué|por\s+que|dónde|donde|cuándo|cuando)\b",
    r"\s+y\s+(?:cómo|como|qué|que|cuáles|cuales|por\s+qué|por\s+que|dónde|donde)\b",
    r"\s+además\s+(?:de\s+)?",
    r"\s+frente\s+a\s+",
    r"\s+en\s+comparación\s+con\s+",
    r";\s*",
]
SPLIT_REGEX = re.compile("|".join(SPLIT_PATTERNS), flags=re.IGNORECASE)


class QueryDecomposer:
    """Deterministic and LLM-assisted query decomposition engine."""

    def __init__(
        self,
        max_subqueries: int = MAX_SUBQUERIES,
        llm_client: Optional[Any] = None,
    ) -> None:
        """Initialize QueryDecomposer.

        Parameters
        ----------
        max_subqueries : int
            Maximum number of sub-queries allowed (default 5).
        llm_client : Optional[Any]
            Optional LLM client for semantic decomposition proposals.
        """
        if max_subqueries <= 0:
            raise ValueError(f"max_subqueries must be positive, got {max_subqueries}.")
        self.max_subqueries = max_subqueries
        self.llm_client = llm_client

    def decompose(
        self,
        query: str,
        notebook_id: str,
        node_id: Optional[str] = None,
        registry: Optional[Any] = None,
        mastery: Optional[Dict[str, float]] = None,
    ) -> SubQueryDecomposition:
        """Decompose a query into prioritized sub-queries.

        Parameters
        ----------
        query : str
            Raw student question.
        notebook_id : str
            Authoritative notebook scope.
        node_id : Optional[str]
            Current curricular node ID (e.g. 'SEC-02-OS-PROC').
        registry : Optional[Any]
            CurriculumRegistry for node title and target competencies.
        mastery : Optional[Dict[str, float]]
            Student mastery map by topic.

        Returns
        -------
        SubQueryDecomposition
            Validated and prioritized sub-query collection.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")
        if not notebook_id or not notebook_id.strip():
            raise ValueError("Notebook ID cannot be empty.")

        clean_query = " ".join(unicodedata.normalize("NFC", query).strip().split())

        # Step 1: Generate candidate sub-queries
        candidates: List[SubQuery] = []
        if self.llm_client is not None:
            try:
                candidates = self._decompose_via_llm(clean_query)
            except Exception as e:
                logger.warning("LLM query decomposition failed: %s. Falling back to rule-based.", e)
                candidates = []

        if not candidates:
            candidates = self._decompose_via_rules(clean_query)

        # Fail-closed fallback: if no valid candidates were formed, use original query
        if not candidates:
            fallback_sq = SubQuery(
                sub_query_id="sq-1",
                text=clean_query,
                intent="direct_query",
                priority_score=1.0,
            )
            return SubQueryDecomposition(
                original_query=clean_query,
                sub_queries=[fallback_sq],
                is_fallback=True,
                confidence=1.0,
            )

        # Step 2: Refinement 1 - Prioritize sub-queries deterministically
        prioritized = self._prioritize_subqueries(
            sub_queries=candidates,
            notebook_id=notebook_id,
            node_id=node_id,
            registry=registry,
            mastery=mastery,
        )

        # Enforce max_subqueries
        final_subqueries = prioritized[: self.max_subqueries]

        return SubQueryDecomposition(
            original_query=clean_query,
            sub_queries=final_subqueries,
            is_fallback=(len(final_subqueries) == 1 and final_subqueries[0].text == clean_query),
            confidence=0.9 if len(final_subqueries) > 1 else 1.0,
        )

    def _decompose_via_rules(self, query: str) -> List[SubQuery]:
        """Deterministic rule-based clause decomposition."""
        # Check if query contains question clauses
        parts = SPLIT_REGEX.split(query)
        cleaned_parts = [p.strip(" ?¿.,;:") for p in parts if len(p.strip()) > 5]

        if len(cleaned_parts) <= 1:
            # Check for multiple questions inside string (e.g. "¿Qué es X? ¿Cómo funciona Y?")
            q_matches = re.findall(r"¿([^?]+)\?", query)
            if len(q_matches) > 1:
                cleaned_parts = [m.strip() for m in q_matches if len(m.strip()) > 5]

        if len(cleaned_parts) <= 1:
            # Single unified query
            return [
                SubQuery(
                    sub_query_id="sq-1",
                    text=query,
                    intent="direct_topic",
                    priority_score=1.0,
                )
            ]

        sub_queries: List[SubQuery] = []
        for idx, part in enumerate(cleaned_parts, start=1):
            sq_text = part
            # Ensure it forms an intelligible search query
            if not sq_text.endswith("?"):
                sq_text = f"¿{sq_text}?" if not sq_text.startswith("¿") else sq_text
            sub_queries.append(
                SubQuery(
                    sub_query_id=f"sq-{idx}",
                    text=sq_text,
                    intent=f"subtopic_{idx}",
                    priority_score=0.0,
                )
            )

        return sub_queries

    def _decompose_via_llm(self, query: str) -> List[SubQuery]:
        """LLM-based decomposition proposal."""
        # Untrusted proposal parser
        prompt = (
            "Eres un analizador curricular. Descompón la siguiente consulta técnica "
            "en sub-preguntas atómicas e independientes (máximo 5).\n"
            f"Consulta: {query}\n"
            "Responde estrictamente en formato JSON con la clave 'sub_queries' como lista de strings."
        )
        response_text = ""
        if hasattr(self.llm_client, "generate"):
            resp = self.llm_client.generate(prompt)
            response_text = resp if isinstance(resp, str) else getattr(resp, "content", "")
        elif hasattr(self.llm_client, "complete"):
            response_text = self.llm_client.complete(prompt)

        import json
        # Extract JSON block
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if not json_match:
            return []
        data = json.loads(json_match.group(0))
        raw_list = data.get("sub_queries", [])
        if not isinstance(raw_list, list):
            return []

        sub_queries = []
        for idx, item in enumerate(raw_list[: self.max_subqueries], start=1):
            if isinstance(item, str) and len(item.strip()) > 5:
                sub_queries.append(
                    SubQuery(
                        sub_query_id=f"sq-{idx}",
                        text=item.strip(),
                        intent=f"llm_subtopic_{idx}",
                        priority_score=0.0,
                    )
                )
        return sub_queries

    def _prioritize_subqueries(
        self,
        sub_queries: List[SubQuery],
        notebook_id: str,
        node_id: Optional[str] = None,
        registry: Optional[Any] = None,
        mastery: Optional[Dict[str, float]] = None,
    ) -> List[SubQuery]:
        """Prioritize sub-queries deterministically according to Refinement 1.

        Considers:
        1. Relevance to current curricular node / roadmap.
        2. Pedagogical priority.
        3. Historic mastery penalty (deprioritizes already mastered topics).
        """
        node_keywords: set[str] = set()
        if node_id and registry:
            try:
                node = registry.get_node(node_id)
                if node:
                    desc_words = re.findall(r"\b\w{4,}\b", (node.title + " " + node.description).lower())
                    node_keywords.update(desc_words)
            except Exception:
                pass

        if not node_keywords and node_id:
            node_keywords.update(re.findall(r"\b\w{3,}\b", node_id.lower()))

        mastery_map = mastery or {}

        scored_list: List[SubQuery] = []
        for sq in sub_queries:
            sq_words = set(re.findall(r"\b\w{4,}\b", sq.text.lower()))

            # 1. Curricular relevance score (0.0 - 1.0)
            if node_keywords:
                overlap = len(sq_words & node_keywords)
                rel_score = min(1.0, overlap / max(1, min(len(node_keywords), 4)))
            else:
                rel_score = 0.5  # Neutral when no specific node context

            # 2. Pedagogical priority (foundational vs specific)
            ped_priority = 0.8 if any(w in sq.text.lower() for w in ["qué", "que", "define", "concepto", "cómo"]) else 0.5

            # 3. Historic mastery penalty (0.0 if not mastered, up to 1.0 if fully mastered)
            mastery_score = 0.0
            for topic, score in mastery_map.items():
                if topic.lower() in sq.text.lower():
                    mastery_score = max(mastery_score, score)

            # Refinement 1 Formula:
            # score = 0.5 * rel + 0.3 * ped_prio - 0.2 * mastery
            final_score = (0.5 * rel_score) + (0.3 * ped_priority) - (0.2 * mastery_score)
            final_score = max(0.01, min(1.0, final_score))

            updated_sq = sq.model_copy(update={"priority_score": round(final_score, 4)})
            scored_list.append(updated_sq)

        # Sort descending by priority_score
        return sorted(scored_list, key=lambda x: x.priority_score, reverse=True)
