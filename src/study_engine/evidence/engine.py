"""Evidence Engine for Subsystem S4.1.

Governs curricular isolation, provenance attribution, cryptographic hashing,
evidence grade assignment, and epistemic claim authorization on retrieved
candidates before context packaging.
"""

import hashlib
from typing import Any, Dict, List, Optional
import unicodedata

from study_engine.contracts.enums import SourceRole
from study_engine.contracts.evidence_engine import (
    CurricularIsolationError,
    EpistemicClaimType,
    EvaluatedEvidenceItem,
    EvidenceAssessmentError,
    EvidenceCoverageReport,
    EvidenceGrade,
    EvidencePacket,
    GroundingDecision,
)
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.storage.knowledge_store import KnowledgeStore


class EvidenceEngine:
    """Evaluates raw retrieval candidates into an authorized EvidencePacket."""

    def evaluate_candidates(
        self,
        query: str,
        notebook_id: str,
        candidates: List[ScoredCandidate],
        store: Optional[KnowledgeStore] = None,
        assessed_grades: Optional[Dict[str, EvidenceGrade]] = None,
        coverage_report: Optional[EvidenceCoverageReport] = None,
    ) -> EvidencePacket:
        """Evaluate candidates under deterministic governance rules.

        Parameters
        ----------
        query : str
            Student query.
        notebook_id : str
            Authoritative curriculum scope.
        candidates : List[ScoredCandidate]
            Retrieved candidates from S3.
        store : Optional[KnowledgeStore]
            Authoritative knowledge store for full relational provenance.
        assessed_grades : Optional[Dict[str, EvidenceGrade]]
            Explicit external assessments (fixtures, benchmark evaluators).
            If None, candidates default to EvidenceGrade.UNASSESSED.

        Returns
        -------
        EvidencePacket
            Immutable evaluated evidence packet.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")
        if not notebook_id or not notebook_id.strip():
            raise ValueError("Notebook ID cannot be empty.")

        original_query = query
        normalized_query = " ".join(
            unicodedata.normalize("NFC", query).strip().split()
        )

        # Step 1: Isolation verification (fail-closed)
        linked_source_ids: Optional[set[str]] = None
        sources_map: Dict[str, Any] = {}
        if store is not None:
            sources = store.list_notebook_sources(notebook_id)
            linked_source_ids = {s.source_id for s in sources}
            sources_map = {s.source_id: s for s in sources}

        for c in candidates:
            if c.notebook_id != notebook_id:
                raise CurricularIsolationError(
                    f"Candidate chunk '{c.chunk_id}' belongs to foreign "
                    f"notebook '{c.notebook_id}', expected '{notebook_id}'."
                )
            if (
                linked_source_ids is not None
                and c.source_id not in linked_source_ids
            ):
                raise CurricularIsolationError(
                    f"Candidate chunk '{c.chunk_id}' source '{c.source_id}' "
                    f"is not linked to notebook '{notebook_id}'."
                )

        # Step 2: Validate assessed_grades subset invariant
        if assessed_grades is not None:
            candidate_ids = {c.chunk_id for c in candidates}
            if not assessed_grades.keys() <= candidate_ids:
                unknown = sorted(
                    list(set(assessed_grades.keys()) - candidate_ids)
                )
                raise EvidenceAssessmentError(
                    f"assessed_grades contains unknown chunk IDs: {unknown}"
                )

        # Step 3: Candidate provenance enrichment and hashing

        evaluated_items: List[EvaluatedEvidenceItem] = []
        for c in candidates:
            content_hash = hashlib.sha256(
                c.content.encode("utf-8")
            ).hexdigest()

            source_title: str = c.metadata.get("source_title", c.source_id)
            author: Optional[str] = c.metadata.get("author")
            source_role: Optional[SourceRole] = None
            priority: Optional[int] = None
            s_rec = None

            if store is not None and c.source_id in sources_map:
                s_rec = sources_map[c.source_id]
                source_title = s_rec.manifest.filename
                author = s_rec.manifest.metadata.get("author")
                raw_role = s_rec.manifest.metadata.get("role")
                if raw_role in SourceRole._value2member_map_:
                    source_role = SourceRole(raw_role)
                raw_prio = s_rec.manifest.metadata.get("priority")
                if raw_prio is not None:
                    try:
                        priority = int(raw_prio)
                    except (ValueError, TypeError):
                        priority = None
            else:
                raw_role = c.metadata.get("source_role")
                if raw_role in SourceRole._value2member_map_:
                    source_role = SourceRole(raw_role)
                raw_prio = c.metadata.get("priority")
                if raw_prio is not None:
                    try:
                        priority = int(raw_prio)
                    except (ValueError, TypeError):
                        priority = None

            # Grade resolution (never guess based on score!)
            if assessed_grades is not None and c.chunk_id in assessed_grades:
                grade = assessed_grades[c.chunk_id]
            else:
                grade = EvidenceGrade.UNASSESSED

            # Extract trust_level
            trust_level = "canonical"
            if s_rec is not None:
                trust_level = s_rec.manifest.metadata.get("trust_level", "canonical")
            elif "trust_level" in c.metadata:
                trust_level = str(c.metadata["trust_level"])

            evaluated_items.append(
                EvaluatedEvidenceItem(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    source_id=c.source_id,
                    source_title=source_title,
                    author=author,
                    page_start=c.page_start,
                    page_end=c.page_end,
                    source_role=source_role,
                    priority=priority,
                    grade=grade,
                    trust_level=trust_level,
                    content_hash=content_hash,
                    content=c.content,
                    retrieval_score=c.score,
                    retrieval_rank=c.rank,
                    retrieval_method=c.retrieval_method,
                )
            )

        # Step 4: Grounding Decision & Epistemic Claim Authorization
        if not evaluated_items:
            decision = GroundingDecision.NO_CANDIDATES
            abstain = True
            reason: Optional[str] = (
                f"No authoritative evidence candidates retrieved "
                f"within notebook '{notebook_id}'."
            )
            allowed = []
            unsupported = list(EpistemicClaimType)
        else:
            has_direct = any(
                it.grade == EvidenceGrade.DIRECT for it in evaluated_items
            )
            has_contextual = any(
                it.grade == EvidenceGrade.CONTEXTUAL for it in evaluated_items
            )

            if has_direct:

                decision = GroundingDecision.SUPPORTED
                abstain = False
                reason = None
                allowed = [
                    EpistemicClaimType.DIRECT_FACTUAL_ASSERTION,
                    EpistemicClaimType.CANONICAL_DEFINITION,
                    EpistemicClaimType.CITE_EVIDENCE,
                    EpistemicClaimType.CONTEXTUAL_EXPLANATION,
                    EpistemicClaimType.BACKGROUND_OVERVIEW,
                    EpistemicClaimType.QUALIFIED_EXPLANATION,
                ]
                unsupported = []
            elif has_contextual:
                decision = GroundingDecision.PARTIALLY_SUPPORTED
                abstain = False
                reason = None
                allowed = [
                    EpistemicClaimType.CONTEXTUAL_EXPLANATION,
                    EpistemicClaimType.BACKGROUND_OVERVIEW,
                    EpistemicClaimType.CITE_EVIDENCE,
                    EpistemicClaimType.QUALIFIED_EXPLANATION,
                ]
                unsupported = [
                    EpistemicClaimType.DIRECT_FACTUAL_ASSERTION,
                    EpistemicClaimType.CANONICAL_DEFINITION,
                ]
            else:
                decision = GroundingDecision.UNASSESSED_EVIDENCE
                abstain = False
                reason = None
                allowed = [
                    EpistemicClaimType.CITE_EVIDENCE,
                    EpistemicClaimType.QUALIFIED_EXPLANATION,
                    EpistemicClaimType.CONTEXTUAL_EXPLANATION,
                ]
                unsupported = [
                    EpistemicClaimType.DIRECT_FACTUAL_ASSERTION,
                    EpistemicClaimType.CANONICAL_DEFINITION,
                ]

        return EvidencePacket(
            original_query=original_query,
            normalized_query=normalized_query,
            notebook_id=notebook_id,
            grounding_decision=decision,
            evidence_items=evaluated_items,
            allowed_claims=allowed,
            unsupported_claims=unsupported,
            abstention_required=abstain,
            abstention_reason=reason,
            has_full_provenance=(store is not None),
            coverage_report=coverage_report,
        )
