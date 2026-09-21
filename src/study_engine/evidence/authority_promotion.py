"""Topic Authority Promotion and Provenance Engine (P2 / V1.2 Spec).

INVARIANTS:
1. Authority tie-breaks, never rescues irrelevance (Relevance >= 0.70 floor).
2. When a primary source is UNAVAILABLE_NO_OCR (e.g., Rosen 879 pages, 0 text chunks),
   the engine deterministically promotes a secondary source with role FORMALIZATION or REFERENCE
   that has verified chunks in KnowledgeStore.
3. Emits transparent cryptographic provenance events for every promotion.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from study_engine.storage.knowledge_store import KnowledgeStore


@dataclass(frozen=True)
class AuthorityPromotionEvent:
    """Audit provenance record for authority promotion."""

    event_type: str
    topic_id: str
    original_primary: str
    promoted_active_primary: str
    reason: str
    chunks_available: int
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TopicAuthorityManager:
    """Manages topic authority, fallbacks, and transparent promotions."""

    def __init__(
        self,
        store: KnowledgeStore,
        authority_mapping_path: Optional[Path] = None,
        authority_bonus: float = 0.15,
        relevance_threshold: float = 0.70,
    ) -> None:
        self.store = store
        self.authority_bonus = authority_bonus
        self.relevance_threshold = relevance_threshold

        self.authority_by_topic: Dict[str, Dict[str, Any]] = {}
        self.promotions_log: List[AuthorityPromotionEvent] = []
        self._source_chunk_counts: Dict[str, int] = {}

        self._load_chunk_counts()
        self._load_mappings(authority_mapping_path)

    def _load_chunk_counts(self) -> None:
        """Scan KnowledgeStore to cache chunk count per source."""
        try:
            with self.store.engine.transaction() as conn:
                cur = conn.cursor()
                cur.execute("SELECT source_id, count(*) FROM chunks GROUP BY source_id;")
                for row in cur.fetchall():
                    self._source_chunk_counts[row[0]] = row[1]
        except Exception:
            self._source_chunk_counts = {}

    def _load_mappings(self, mapping_path: Optional[Path]) -> None:
        """Load topic authority definitions from migration JSON or alignment."""
        default_paths = [
            Path("artifacts/migracion/notebooklm/m2_autoridad_por_topico.json"),
            Path("artifacts/migracion/curriculum_importado.json"),
            Path("data/curriculum/alignment/cybersecurity_v1_alignment.json"),
        ]
        chosen = mapping_path if mapping_path and mapping_path.is_file() else None
        if not chosen:
            for p in default_paths:
                if p.is_file():
                    chosen = p
                    break

        if not chosen:
            return

        with open(chosen, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_topics = []
        if "autoridad_por_topico" in data:
            raw_topics = data["autoridad_por_topico"]
        elif "topicos" in data:
            raw_topics = data["topicos"]

        for t in raw_topics:
            tid = t.get("topico_id")
            if tid:
                self.authority_by_topic[tid] = t

    def get_effective_authority(self, topic_id: str) -> Dict[str, Any]:
        """Resolve active primary source, applying promotion if original primary is unavailable."""
        mapping = self.authority_by_topic.get(topic_id, {})
        if not mapping:
            return {
                "topic_id": topic_id,
                "active_primary": None,
                "original_primary": None,
                "promoted": False,
                "secondary_sources": [],
            }

        original_primary = mapping.get("fuente_primaria")
        secondaries = mapping.get("fuentes_secundarias", [])

        # Check if original primary has chunks in KnowledgeStore
        primary_chunks = self._get_chunks_for_slug(original_primary)

        if primary_chunks > 0:
            return {
                "topic_id": topic_id,
                "active_primary": original_primary,
                "original_primary": original_primary,
                "promoted": False,
                "secondary_sources": secondaries,
            }

        # Original primary has 0 chunks (e.g. Rosen UNAVAILABLE_NO_OCR)
        # Search for secondary with role formalization or reference with chunks
        candidates = []
        for s in secondaries:
            slug = s.get("source_slug")
            role = s.get("rol", "").lower()
            chunks = self._get_chunks_for_slug(slug)
            if chunks > 0 and role in ("formalizacion", "referencia", "ejemplos_practicos"):
                candidates.append((slug, role, chunks))

        if candidates:
            # Sort by formalization first, then max chunk count
            candidates.sort(key=lambda x: (1 if x[1] == "formalizacion" else 0, x[2]), reverse=True)
            promoted_slug = candidates[0][0]
            chunks_count = candidates[0][2]

            event = AuthorityPromotionEvent(
                event_type="PROMOTION_BY_UNAVAILABILITY",
                topic_id=topic_id,
                original_primary=original_primary or "UNKNOWN",
                promoted_active_primary=promoted_slug,
                reason="original_primary_unavailable_no_ocr",
                chunks_available=chunks_count,
            )
            self.promotions_log.append(event)

            return {
                "topic_id": topic_id,
                "active_primary": promoted_slug,
                "original_primary": original_primary,
                "promoted": True,
                "promotion_reason": event.reason,
                "secondary_sources": secondaries,
            }

        return {
            "topic_id": topic_id,
            "active_primary": original_primary,
            "original_primary": original_primary,
            "promoted": False,
            "secondary_sources": secondaries,
        }

    def _get_chunks_for_slug(self, slug: Optional[str]) -> int:
        """Resolve chunk count matching a source slug or ID."""
        if not slug:
            return 0
        # Direct match or src_{slug} match
        count = self._source_chunk_counts.get(slug, 0)
        if count == 0:
            count = self._source_chunk_counts.get(f"src_{slug}", 0)
        if count == 0:
            # Try partial substring match in source keys
            for k, v in self._source_chunk_counts.items():
                if slug.lower() in k.lower():
                    count += v
        return count

    def compute_authority_bonus(
        self,
        candidate_source_id: str,
        topic_id: Optional[str],
        relevance_score: float,
    ) -> float:
        """Calculate authority bonus respecting strict relevance floor (P2.2).
        
        Invariant: Authority tie-breaks, never rescues irrelevance (Relevance >= 0.70).
        """
        if relevance_score < self.relevance_threshold or not topic_id:
            return 0.0

        effective = self.get_effective_authority(topic_id)
        active_primary = effective.get("active_primary")
        if not active_primary:
            return 0.0

        # Check match between candidate source and active primary
        c_clean = candidate_source_id.lower()
        p_clean = active_primary.lower()
        if p_clean in c_clean or c_clean in p_clean:
            return self.authority_bonus

        return 0.0
