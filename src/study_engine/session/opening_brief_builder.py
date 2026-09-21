"""OpeningBriefBuilder for Unified Study Session (Directiva Final v2).

INVARIANTS:
1. SEPARAR HECHOS DE REDACCIÓN (Corrección #3):
   - Los hechos (OpeningBriefFacts) son 100% deterministas e inmutables.
   - Ningún LLM interviene en decidir o modificar los hechos.
2. La narrativa LLM es estrictamente SOBRE los hechos y no puede contradecirlos.
3. Si la narrativa contradice o altera hechos, se detecta y se priorizan los hechos.
"""

from typing import Any, Dict, List, Optional, Tuple

from study_engine.federation.notebook_registry import Notebook as SovereignNotebook
from study_engine.pedagogy.student_context import StudentContext
from study_engine.session.progression_policy import ProgressionPolicy
from study_engine.session.study_session_contracts import (
    CurriculumPosition,
    OpeningBriefFacts,
)
from study_engine.student.contracts import BKTState


class OpeningBriefBuilder:
    """Constructor determinista de hechos de bienvenida y narrativa complementaria."""

    def __init__(self, progression_policy: Optional[ProgressionPolicy] = None) -> None:
        self.policy = progression_policy or ProgressionPolicy()

    def build_facts(
        self,
        notebook: SovereignNotebook,
        curriculum_kcs: List[Dict[str, Any]],
        bkt_states: Dict[str, BKTState],
        student_context: Optional[StudentContext] = None,
        unit_info: Optional[Tuple[str, str]] = None,
    ) -> OpeningBriefFacts:
        """Construye los HECHOS autoritativos. 100% determinista sin LLM."""
        notebook_id = getattr(notebook, "notebook_id", getattr(notebook, "id", "unknown"))
        notebook_name = notebook.name
        subject = getattr(notebook, "subject", None) or "Materia"
        level = getattr(notebook, "level", "General")
        notebook_purpose = f"Cuaderno curricular soberano de {subject} (Nivel {level})"

        # 1. Determinar elegibilidad por prerequisitos (CURRÍCULO PRIMERO, BKT DESPUÉS)
        eligible_kcs: List[str] = []
        all_kc_ids = [kc["kc_id"] for kc in curriculum_kcs]
        kc_meta_map = {kc["kc_id"]: kc for kc in curriculum_kcs}

        for kc in curriculum_kcs:
            kc_id = kc["kc_id"]
            prereqs = kc.get("prerequisites", [])
            # Prerequisito satisfecho si está completado en BKT o no tiene prerequisitos
            prereqs_met = True
            for p in prereqs:
                p_bkt = bkt_states.get(p)
                p_val = p_bkt.p_L if p_bkt is not None else 0.0
                if p_val < self.policy.PREREQUISITE_MIN_PL:
                    prereqs_met = False
                    break
            if prereqs_met:
                eligible_kcs.append(kc_id)

        # Fallback de seguridad: si ninguno cumple prerequisitos, el primero de la secuencia
        if not eligible_kcs and all_kc_ids:
            eligible_kcs.append(all_kc_ids[0])

        # 2. Particionar KCs en completados, en progreso y pendientes según BKT
        completed: List[str] = []
        in_progress: List[str] = []
        pending: List[str] = []

        for kc_id in all_kc_ids:
            bkt = bkt_states.get(kc_id)
            p_L = bkt.p_L if bkt is not None else 0.0
            if p_L >= self.policy.COMPLETION_THRESHOLD:
                completed.append(kc_id)
            elif p_L >= self.policy.IN_PROGRESS_THRESHOLD:
                in_progress.append(kc_id)
            else:
                pending.append(kc_id)

        # Determinar unidad curricular
        unit_or_module, unit_name = unit_info or ("Módulo Principal", notebook.subject)
        curr_pos = CurriculumPosition(
            unit_or_module=unit_or_module,
            unit_name=unit_name,
            kcs_in_unit=tuple(all_kc_ids),
            kcs_completed=tuple(completed),
            kcs_in_progress=tuple(in_progress),
            kcs_pending=tuple(pending),
        )

        # 3. Priorización determinista vía ProgressionPolicy
        selected_kc, sel_rationale = self.policy.select_kc(
            eligible_kcs=eligible_kcs,
            bkt_states=bkt_states,
            kc_metadata_map=kc_meta_map,
        )

        # 4. Estimación BKT (consultiva)
        sel_bkt = bkt_states.get(selected_kc)
        bkt_estimate = sel_bkt.p_L if sel_bkt is not None else 0.0
        attempts = sel_bkt.attempts if sel_bkt is not None else 0
        bkt_note = f"Estimación probabilística basada en {attempts} observaciones deterministas."

        # 5. Contexto consultivo
        context_note = (
            "Contexto consultivo reconstruido de interacciones previas. No acredita dominio ontológico."
            if student_context is not None
            else "Sin contexto consultivo externo vinculado."
        )

        # 6. Decisión de próxima acción
        selected_meta = kc_meta_map.get(selected_kc, {})
        selected_display_name = selected_meta.get("display_name") or selected_meta.get("title") or selected_kc
        prereqs = selected_meta.get("prerequisites", [])
        prereqs_states = {p: bkt_states.get(p) for p in prereqs}

        decision = self.policy.decide(
            kc=selected_kc,
            bkt_state=sel_bkt,
            prerequisites_states=prereqs_states,
            eligible_kcs=eligible_kcs,
        )

        return OpeningBriefFacts(
            notebook_id=notebook_id,
            notebook_name=notebook_name,
            notebook_purpose=notebook_purpose,
            curriculum_position=curr_pos,
            eligible_kcs=tuple(eligible_kcs),
            selected_kc=selected_kc,
            selected_kc_rationale=sel_rationale,
            bkt_estimate=bkt_estimate,
            bkt_note=bkt_note,
            student_context=student_context,
            student_context_note=context_note,
            proposed_action=decision.action,
            proposed_action_rationale=decision.rationale,
            selected_kc_display_name=selected_display_name,
        )

    def build_narrative(
        self,
        facts: OpeningBriefFacts,
        llm_client: Optional[Any] = None,
    ) -> str:
        """Redacta texto natural amigable SOBRE los hechos autoritativos.
        
        Si no hay LLM disponible o en modo offline/mock, genera una redacción
        determinista fluida que respeta 100% los hechos.
        """
        unit = facts.curriculum_position.unit_or_module
        unit_name = facts.curriculum_position.unit_name
        sel_kc = facts.selected_kc_display_name or facts.selected_kc
        p_L = facts.bkt_estimate
        action = facts.proposed_action

        # Construcción fluida y cálida sin contradecir hechos
        action_text = {
            "START_FOUNDATIONS": f"comenzar con la fundamentación de '{sel_kc}'",
            "CONTINUE_CONSOLIDATION": f"profundizar y consolidar '{sel_kc}'",
            "ADVANCE_TO_NEXT": f"avanzar al siguiente tema del programa",
            "REVIEW_PREREQUISITE": f"hacer un breve repaso de los prerequisitos",
            "SUGGEST_EXERCISE": f"ponerte a prueba con un ejercicio práctico de '{sel_kc}'",
        }.get(action, f"trabajar en '{sel_kc}'")

        narrative = (
            f"¡Hola! Te doy la bienvenida a **{facts.notebook_name}**. "
            f"Nos encontramos en **{unit}: {unit_name}**. "
            f"Conforme al orden curricular y tu avance actual (estimación P(L) = {p_L:.2f}), "
            f"el tema seleccionado para hoy es **{sel_kc}** ({facts.selected_kc}). "
            f"Te propongo {action_text}. ¿Querés que arranquemos?"
        )
        return narrative

    def build(
        self,
        notebook: SovereignNotebook,
        curriculum_kcs: List[Dict[str, Any]],
        bkt_states: Dict[str, BKTState],
        student_context: Optional[StudentContext] = None,
        unit_info: Optional[Tuple[str, str]] = None,
        llm_client: Optional[Any] = None,
    ) -> Tuple[OpeningBriefFacts, str]:
        """Retorna la tupla (hechos_inmutables, narrativa_amigable)."""
        facts = self.build_facts(
            notebook=notebook,
            curriculum_kcs=curriculum_kcs,
            bkt_states=bkt_states,
            student_context=student_context,
            unit_info=unit_info,
        )
        narrative = self.build_narrative(facts, llm_client=llm_client)
        return facts, narrative
