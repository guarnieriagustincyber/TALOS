"""SessionBriefingGenerator: Deterministic episodic memory brief generation (Ola 6, Fase 6.3).

Generates a 3-5 sentence brief at the start of a session combining:
1. Weak KCs (P(L) < 0.50) from BKT
2. Requested hints from Hint Ledger
3. Pending reviews from SpacedRepetitionScheduler (SM-2)
4. Last topic & next topic from SessionHistory

Invariants:
- INV-W6-2: The generator NEVER mutates BKT. Only reads current cognitive state.
- INV-W5-3: Never decides KCs or pedagogical transitions; strictly informative.
- Natural Rioplatense tone with direct address ("Agustín, la última vez estuviste...").
- Enmienda E27: Briefing is injected after the static Corpus Pack to preserve 32K+ cache.
"""

from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional, Sequence

from study_engine.memory.session_history import SessionHistory, SessionRecord
from study_engine.student.contracts import BKTState
from study_engine.student.storage import StudentStorage

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WeakKCInfo:
    kc_id: str
    title: str
    p_L: float


class SessionBriefingGenerator:
    """Generates an episodic briefing summarizing prior student trajectory without mutating state."""

    def __init__(
        self,
        bkt_tracker: Optional[Any] = None,
        hint_ledger: Optional[Any] = None,
        sm2_scheduler: Optional[Any] = None,
        session_history: Optional[SessionHistory] = None,
        student_storage: Optional[StudentStorage] = None,
        cognitive_profile_store: Optional[Any] = None,
    ) -> None:
        self.bkt_tracker = bkt_tracker
        self.hint_ledger = hint_ledger
        self.sm2_scheduler = sm2_scheduler
        self.session_history = session_history or SessionHistory()
        self.student_storage = student_storage
        self.cognitive_profile_store = cognitive_profile_store

    def generate_briefing(
        self,
        student_id: str = "default_student",
        notebook_id: str = "default_notebook",
        student_name: str = "Agustín",
    ) -> str:
        """Generates a 3-5 sentence personalized opening briefing (INV-W6-2)."""
        # 1. Fetch last session from SessionHistory (per-notebook isolation)
        last_session: Optional[SessionRecord] = None
        if self.session_history:
            last_session = self.session_history.get_last(notebook_id=notebook_id, student_id=student_id)

        # 2. Query weak KCs (P(L) < 0.50) without mutation (INV-W6-2)
        weak_kcs = self._get_weak_kcs(student_id=student_id, threshold=0.50)

        # 3. Query hints requested in recent exercises
        recent_hints_count = self._get_recent_hints_count(student_id=student_id, last_session=last_session)

        # 4. Query pending reviews from SM-2
        due_reviews = self._get_due_reviews(student_id=student_id)

        # 5. Build 3-5 sentences natural Rioplatense brief
        briefing_lines: List[str] = []

        # Sentence 1: Last session context
        if last_session and last_session.topic:
            briefing_lines.append(f"{student_name}, la última vez estuviste trabajando en {last_session.topic}.")
        else:
            briefing_lines.append(f"{student_name}, bienvenido a una nueva sesión de estudio.")

        # Sentence 2: Weak KC alert (if any)
        if weak_kcs:
            top_weak = weak_kcs[0]
            briefing_lines.append(f"Tu P(L) en '{top_weak.title}' es {top_weak.p_L:.2f} (todavía débil).")

        # Sentence 3: Hint usage reflection (if any)
        if recent_hints_count > 0:
            briefing_lines.append(f"Pediste {recent_hints_count} pistas en el último ejercicio.")

        # Sentence 4: SM-2 spaced repetition alert (if any)
        if len(due_reviews) > 0:
            briefing_lines.append(f"Hoy tenés {len(due_reviews)} repasos pendientes.")

        # Sentence 5: Pedagogical forward choice
        next_topic = last_session.next_topic if (last_session and last_session.next_topic) else "el siguiente módulo"
        briefing_lines.append(f"¿Arrancamos con un ejercicio de reforzamiento o preferís avanzar a {next_topic}?")

        return "\n".join(briefing_lines)

    def generate_with_cognitive_profile(
        self,
        student_id: str = "default_student",
        notebook_id: str = "default_notebook",
        student_name: str = "Agustín",
    ) -> str:
        """Generates briefing enriched with cognitive profile items (Enmienda E-C3)."""
        base_brief = self.generate_briefing(student_id=student_id, notebook_id=notebook_id, student_name=student_name)
        if not self.cognitive_profile_store:
            return base_brief

        try:
            items = self.cognitive_profile_store.get_for_injection(user_id=student_id, max_items=3)
            if not items:
                return base_brief

            cognitive_notes = []
            for it in items:
                cat = it.get("category", "")
                desc = it.get("description", "")
                kc = it.get("kc_id", "")
                occ = it.get("occurrences", 1)
                if cat in ("RECURRING_MISCONCEPTION", "WEAKNESS"):
                    occ_str = f" ({occ} veces)" if occ > 1 else ""
                    cognitive_notes.append(f"Atención en '{kc}': {desc}{occ_str}.")

            if cognitive_notes:
                extra_block = "\n" + " ".join(cognitive_notes)
                return base_brief + extra_block
        except Exception as exc:
            logger.warning("[SESSION_BRIEFING] Error incorporating cognitive profile: %s", exc)

        return base_brief

    def _get_weak_kcs(self, student_id: str, threshold: float = 0.50) -> List[WeakKCInfo]:
        """Consults BKT states and identifies concepts below mastery threshold (INV-W6-2)."""
        weak_list: List[WeakKCInfo] = []

        # Check bkt_tracker first if custom get_weak_kcs method is present
        if self.bkt_tracker and hasattr(self.bkt_tracker, "get_weak_kcs"):
            try:
                res = self.bkt_tracker.get_weak_kcs(student_id, threshold=threshold)
                if res:
                    for item in res:
                        weak_list.append(
                            WeakKCInfo(
                                kc_id=getattr(item, "kc_id", str(item)),
                                title=getattr(item, "title", getattr(item, "kc_id", str(item))),
                                p_L=getattr(item, "p_L", getattr(item, "p_l", 0.40)),
                            )
                        )
                    return weak_list
            except Exception:
                pass

        # Check storage
        storage = self.student_storage
        if not storage and self.bkt_tracker and hasattr(self.bkt_tracker, "storage"):
            storage = self.bkt_tracker.storage

        if storage and hasattr(storage, "get_all_bkt_states"):
            try:
                states = storage.get_all_bkt_states()
                for kc_id, state in states.items():
                    if state.p_L < threshold:
                        weak_list.append(
                            WeakKCInfo(
                                kc_id=kc_id,
                                title=kc_id.replace("_", " "),
                                p_L=round(state.p_L, 2),
                            )
                        )
            except Exception as exc:
                logger.warning(f"[SESSION_BRIEFING] Failed to read BKT states: {exc}")

        return weak_list

    def _get_recent_hints_count(
        self,
        student_id: str,
        last_session: Optional[SessionRecord] = None,
    ) -> int:
        """Reads recent hints requested without mutating state."""
        # 1. Direct hint ledger method
        if self.hint_ledger is not None:
            if hasattr(self.hint_ledger, "get_recent"):
                try:
                    res = self.hint_ledger.get_recent(student_id, limit=5)
                    return len(res) if res else 0
                except Exception:
                    pass
            if isinstance(self.hint_ledger, (list, tuple)):
                return len(self.hint_ledger)
            if isinstance(self.hint_ledger, int):
                return self.hint_ledger

        # 2. Check session record
        if last_session and last_session.hints_requested > 0:
            return last_session.hints_requested

        # 3. Check storage hints
        storage = self.student_storage
        if storage and hasattr(storage, "count_hints") and last_session:
            try:
                return storage.count_hints(last_session.session_id)
            except Exception:
                pass

        return 0

    def _get_due_reviews(self, student_id: str) -> List[str]:
        """Queries due SM-2 reviews for the current student/session."""
        if self.sm2_scheduler is not None:
            if hasattr(self.sm2_scheduler, "get_due_today"):
                try:
                    return list(self.sm2_scheduler.get_due_today(student_id))
                except Exception:
                    pass
            if hasattr(self.sm2_scheduler, "get_due_anchors"):
                try:
                    return list(self.sm2_scheduler.get_due_anchors())
                except Exception:
                    pass
            if isinstance(self.sm2_scheduler, (list, tuple)):
                return list(self.sm2_scheduler)

        return []
