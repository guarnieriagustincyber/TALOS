"""ProgressionPolicy for Unified Study Session (Directiva Final v2).

INVARIANTS:
1. Versioned and testable policy (POLICY_VERSION = "v1.0").
2. BKT does NOT define curriculum order: roadmap + prerequisites determine eligible KCs.
3. BKT only prioritizes WITHIN eligible KCs.
4. Deterministic decision outputs.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple
from study_engine.session.study_session_contracts import ProgressionDecision
from study_engine.student.contracts import BKTState


class ProgressionPolicy:
    """Política de progresión explícita, versionada y testeable.
    
    NO usa umbrales genéricos hardcodeados universales sin justificación.
    El significado de P(L) depende del modelo BKT, parámetros, KC y prerequisitos.
    """

    POLICY_VERSION = "v1.0"

    # Umbrales canónicos de la versión v1.0
    COMPLETION_THRESHOLD = 0.85      # P(L) >= 0.85 -> Dominado / Acreditado
    IN_PROGRESS_THRESHOLD = 0.40     # 0.40 <= P(L) < 0.85 -> En progreso / Consolidación
    PREREQUISITE_MIN_PL = 0.60       # Prerequisito debe tener P(L) >= 0.60 para considerarse habilitante

    def __init__(self, policy_version: str = POLICY_VERSION) -> None:
        self.policy_version = policy_version

    def get_eligible_kcs(
        self,
        curriculum_kcs: List[Dict[str, Any]],
        bkt_states: Dict[str, BKTState],
    ) -> List[str]:
        """Filtra y retorna KCs cuyos prerequisitos están satisfechos deterministamente."""
        eligible = []
        for kc in curriculum_kcs:
            kc_id = kc["kc_id"]
            prereqs = kc.get("prerequisites", [])
            met = True
            for p in prereqs:
                p_bkt = bkt_states.get(p)
                p_val = p_bkt.p_L if p_bkt is not None else 0.0
                if p_val < self.PREREQUISITE_MIN_PL:
                    met = False
                    break
            if met:
                eligible.append(kc_id)
        return eligible

    def select_kc(
        self,
        eligible_kcs: Sequence[str],
        bkt_states: Dict[str, BKTState],
        kc_metadata_map: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str]:
        """Selecciona el KC a estudiar dentro de la lista de elegibles.
        
        Lógica determinista:
        1. Ordenar preservando la secuencia curricular del roadmap (orden en eligible_kcs).
        2. Dentro de KCs del mismo orden/unidad, priorizar aquel con menor P(L)
           (el que más necesita consolidación o inicio).
        3. Si todos tienen P(L) similar o 0, tomar el primero de la secuencia curricular.
        
        Retorna: (kc_id, rationale)
        """
        if not eligible_kcs:
            raise ValueError("No hay KCs elegibles disponibles para seleccionar.")

        meta_map = kc_metadata_map or {}

        # Ordenar KCs: primero los que tienen P(L) < COMPLETION_THRESHOLD,
        # ordenados por menor P(L) (ascendente) y luego por índice curricular.
        scored_kcs: List[Tuple[float, int, str]] = []
        for idx, kc_id in enumerate(eligible_kcs):
            bkt = bkt_states.get(kc_id)
            p_L = bkt.p_L if bkt is not None else 0.0
            scored_kcs.append((p_L, idx, kc_id))

        # Filtrar no completados primero
        non_completed = [item for item in scored_kcs if item[0] < self.COMPLETION_THRESHOLD]
        if non_completed:
            # Seleccionar el primero en el orden curricular que no esté completado
            # Si varios tienen P(L) > 0 pero no completado, priorizar el primero curricularmente
            # que requiere estudio.
            selected = min(non_completed, key=lambda x: (0 if x[0] > 0 else 1, x[1], x[0]))
            selected_kc = selected[2]
            p_L = selected[0]
            if p_L == 0.0:
                rationale = f"Seleccionado '{selected_kc}' por secuencia curricular para iniciar fundamentos."
            else:
                rationale = f"Seleccionado '{selected_kc}' para continuar consolidación (P(L) = {p_L:.2f})."
            return selected_kc, rationale

        # Si todos están completados, seleccionar el de menor P(L) para repaso
        selected = min(scored_kcs, key=lambda x: (x[0], x[1]))
        selected_kc = selected[2]
        return selected_kc, f"Todos los KCs elegibles superan umbral; seleccionado '{selected_kc}' para repaso avanzado."

    def decide(
        self,
        kc: str,
        bkt_state: Optional[BKTState],
        prerequisites_states: Dict[str, Optional[BKTState]],
        eligible_kcs: Sequence[str],
    ) -> ProgressionDecision:
        """Determina la próxima acción pedagógica determinista.
        
        Input:
        - kc: KC actual seleccionado
        - bkt_state: estado BKT del KC actual
        - prerequisites_states: estados BKT de los prerequisitos directos
        - eligible_kcs: KCs elegibles habilitados por el roadmap
        
        Output:
        - ProgressionDecision con acción, rationale y version
        """
        # 1. Verificar si algún prerequisito directo está por debajo del umbral mínimo
        for prereq_id, prereq_bkt in prerequisites_states.items():
            prereq_pl = prereq_bkt.p_L if prereq_bkt is not None else 0.0
            if prereq_pl < self.PREREQUISITE_MIN_PL:
                return ProgressionDecision(
                    action="REVIEW_PREREQUISITE",
                    rationale=f"El prerequisito '{prereq_id}' tiene P(L) = {prereq_pl:.2f} (< {self.PREREQUISITE_MIN_PL:.2f}). Se recomienda repasar.",
                    next_kc=prereq_id,
                    policy_version=self.policy_version,
                )

        p_L = bkt_state.p_L if bkt_state is not None else 0.0
        attempts = bkt_state.attempts if bkt_state is not None else 0

        # 2. Sin observaciones previas -> Iniciar fundamentos
        if attempts == 0 or p_L == 0.0:
            return ProgressionDecision(
                action="START_FOUNDATIONS",
                rationale=f"KC '{kc}' sin observaciones evaluativas registradas. Iniciar fundamentación conceptual.",
                next_kc=kc,
                policy_version=self.policy_version,
            )

        # 3. P(L) completado -> Proponer avanzar al siguiente KC
        if p_L >= self.COMPLETION_THRESHOLD:
            # Buscar el siguiente KC en eligible_kcs
            next_target = None
            try:
                curr_idx = list(eligible_kcs).index(kc)
                if curr_idx + 1 < len(eligible_kcs):
                    next_target = eligible_kcs[curr_idx + 1]
            except ValueError:
                pass

            return ProgressionDecision(
                action="ADVANCE_TO_NEXT",
                rationale=f"KC '{kc}' dominado con P(L) = {p_L:.2f} (>= {self.COMPLETION_THRESHOLD:.2f}). Listo para avanzar.",
                next_kc=next_target,
                policy_version=self.policy_version,
            )

        # 4. En progreso pero con varios intentos -> Sugerir ejercicio para consolidar
        if attempts >= 2 and p_L >= self.IN_PROGRESS_THRESHOLD:
            return ProgressionDecision(
                action="SUGGEST_EXERCISE",
                rationale=f"KC '{kc}' en consolidación madura (P(L) = {p_L:.2f}, {attempts} intentos). Recomendado ejercicio evaluativo.",
                next_kc=kc,
                policy_version=self.policy_version,
            )

        # 5. En consolidación inicial -> Continuar explicación y diálogo socrático
        return ProgressionDecision(
            action="CONTINUE_CONSOLIDATION",
            rationale=f"KC '{kc}' en consolidación (P(L) = {p_L:.2f}). Continuar diálogo conceptual guiado.",
            next_kc=kc,
            policy_version=self.policy_version,
        )
