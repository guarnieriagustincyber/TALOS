"""Student Pedagogical Context (Consultive, Non-Authoritative).

INVARIANTS:
1. StudentContext is CONSULTIVE ONLY.
2. It NEVER mutates BKT mastery states.
3. It NEVER certifies ontological mastery.
4. Used exclusively by explanation builders to select initial starting points,
   tailor physical analogies, avoid redundant rudimentary explanations,
   and highlight recurring error patterns (pitfalls).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class StudentContext:
    """Consultive pedagogical context reflecting prior student interactions."""

    student_id: str
    notebook_id: str
    current_position: str
    topics_seen: Tuple[str, ...] = field(default_factory=tuple)
    topics_practiced: Tuple[str, ...] = field(default_factory=tuple)
    topics_evaluated: Tuple[str, ...] = field(default_factory=tuple)
    errors_recurring: Tuple[str, ...] = field(default_factory=tuple)
    strengths: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, object]:
        return {
            "student_id": self.student_id,
            "notebook_id": self.notebook_id,
            "current_position": self.current_position,
            "topics_seen": list(self.topics_seen),
            "topics_practiced": list(self.topics_practiced),
            "topics_evaluated": list(self.topics_evaluated),
            "errors_recurring": list(self.errors_recurring),
            "strengths": list(self.strengths),
        }


# Authoritative consultive trajectory reconstructed from NotebookLM for Fase 0
FASE0_NOTEBOOKLM_CONTEXT = StudentContext(
    student_id="agustin",
    notebook_id="fase0-soc",
    current_position="Tramo 5: Hito 1 — Aritmética de punteros y memoria contigua",
    topics_seen=(
        "metodologia_resolucion_problemas",
        "fisica_ram_asignacion",
        "logica_proposicional",
        "clean_code_guard_clauses",
        "control_flujo_bucles",
        "modularidad_stack_frame",
        "parsing_acumuladores",
        "aritmetica_punteros",
        "arrays_direccionamiento_contiguo",
    ),
    topics_practiced=(
        "metodologia_resolucion_problemas",
        "fisica_ram_asignacion",
        "logica_proposicional",
        "clean_code_guard_clauses",
        "control_flujo_bucles",
        "modularidad_stack_frame",
        "parsing_acumuladores",
    ),
    topics_evaluated=(
        "logica_proposicional",
        "clean_code_guard_clauses",
        "control_flujo_bucles",
        "modularidad_stack_frame",
        "parsing_acumuladores",
    ),
    errors_recurring=(
        "Invocar funciones sin parámetros ni paréntesis",
        "Duplicar acumulador en strings (pedazo += pedazo + caracter)",
        "Olvidar validar el 'elemento colgante' fuera del bucle de acumulación",
        "Doble incremento involuntario en contadores de bucle",
        "Off-by-one entre delimitadores y entidades en parsing",
        "Lógica invertida en validación de rangos (devolver False cuando está en rango)",
        "Comparar tipos incompatibles sin conversión explícita",
    ),
    strengths=(
        "Modelado de memoria física con analogía de casilleros/oficina",
        "Estructuración de cláusulas de guarda tempranas",
        "Diseño paso a paso en pseudocódigo antes de codificar",
    ),
)


def get_student_context(notebook_id: str, student_id: str = "agustin") -> StudentContext:
    """Retrieve consultive context for the student and notebook."""
    if notebook_id.strip() == "fase0-soc":
        return FASE0_NOTEBOOKLM_CONTEXT

    # Default baseline context for other notebooks (empty history, no false mastery)
    return StudentContext(
        student_id=student_id,
        notebook_id=notebook_id.strip(),
        current_position="Inicio de cursada / Unidad 1",
        topics_seen=(),
        topics_practiced=(),
        topics_evaluated=(),
        errors_recurring=(),
        strengths=(),
    )


def determine_pedagogical_context_mode(
    target_kc_id: Optional[str],
    bkt_tracker: Optional[Any],
    kc_catalog: Optional[Dict[str, Any]] = None,
    notebook_id: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """Determina el modo de contexto pedagógico según maestría BKT y estado de prerrequisitos (Fix S4.2).

    Reglas:
    1. Si algún prerrequisito tiene P(L) < 0.50 -> 'prerequisite_reinforcement'
    2. Si P(L) > 0.80 -> 'advanced' (matices, edge cases, optimización a bajo nivel)
    3. Si P(L) < 0.30 -> 'basic' (analogías cotidianas, desglose paso a paso)
    4. En otro caso (0.30 <= P(L) <= 0.80) -> 'intermediate' (consolidación estándar)
    """
    if not target_kc_id:
        return "intermediate", {
            "context_mode": "intermediate",
            "target_kc_id": None,
            "p_L": 0.5,
            "prerequisites": [],
            "unmet_prerequisites": [],
        }

    # 1. Resolver prerrequisitos del catálogo si existe
    prerequisites: List[str] = []
    if kc_catalog:
        kcs = []
        if notebook_id and notebook_id in kc_catalog:
            kcs = kc_catalog[notebook_id].get("kcs", [])
        else:
            for nb_entry in kc_catalog.values():
                if isinstance(nb_entry, dict) and "kcs" in nb_entry:
                    kcs.extend(nb_entry["kcs"])
        
        target_meta = next((k for k in kcs if k.get("kc_id") == target_kc_id), None)
        if target_meta:
            prerequisites = list(target_meta.get("prerequisites", []))

    # 2. Evaluar prerrequisitos en BKT
    unmet_prereqs: List[Tuple[str, float]] = []
    if bkt_tracker is not None:
        for prereq in prerequisites:
            try:
                p_state = bkt_tracker.get_state(prereq)
                p_val = float(getattr(p_state, "p_L", 0.1))
            except Exception:
                p_val = 0.1
            if p_val < 0.50:
                unmet_prereqs.append((prereq, p_val))

    # 3. Evaluar P(L) del KC objetivo
    p_L = 0.1
    if bkt_tracker is not None:
        try:
            target_state = bkt_tracker.get_state(target_kc_id)
            p_L = float(getattr(target_state, "p_L", 0.1))
        except Exception:
            p_L = 0.1

    # 4. Decisión pedagógica jerárquica
    if unmet_prereqs:
        mode = "prerequisite_reinforcement"
    elif p_L > 0.80:
        mode = "advanced"
    elif p_L < 0.30:
        mode = "basic"
    else:
        mode = "intermediate"

    meta = {
        "context_mode": mode,
        "target_kc_id": target_kc_id,
        "p_L": p_L,
        "prerequisites": prerequisites,
        "unmet_prerequisites": unmet_prereqs,
    }
    return mode, meta


def build_bkt_adaptation_directive(mode: str, meta: Dict[str, Any]) -> str:
    """Genera la directiva pedagógica para guiar al LLM según el estado BKT (Fix S4.2)."""
    p_L = meta.get("p_L", 0.5)
    target_kc = meta.get("target_kc_id") or "concepto consultado"

    if mode == "prerequisite_reinforcement":
        unmet = meta.get("unmet_prerequisites", [])
        unmet_str = ", ".join([f"{p} (P(L)={v:.2f})" for p, v in unmet])
        return (
            "=== ADAPTACIÓN PEDAGÓGICA BKT: REFUERZO DE PRERREQUISITOS FALTANTES ===\n"
            f"- ALERTA PEDAGÓGICA: El estudiante presenta lagunas en prerrequisitos clave: {unmet_str}.\n"
            "- Antes de profundizar en el tema consultado, incluí un breve andamiaje conceptual que conecte y refuerce "
            "la base del prerrequisito necesario para garantizar un aprendizaje significativo sin disonancia cognitiva.\n"
        )
    elif mode == "advanced":
        return (
            f"=== ADAPTACIÓN PEDAGÓGICA BKT: NIVEL AVANZADO / MAESTRÍA (P(L)={p_L:.2f}) ===\n"
            f"- El estudiante ya domina los fundamentos canónicos de '{target_kc}' (P(L) > 0.80).\n"
            "- NUNCA expliques definiciones elementales ni reiteres analogías introductorias desde cero.\n"
            "- Enfocate directamente en matices avanzados, casos de borde (edge cases), impacto a nivel de registros/kernel, "
            "trade-offs de diseño en producción y optimizaciones de bajo nivel.\n"
        )
    elif mode == "basic":
        return (
            f"=== ADAPTACIÓN PEDAGÓGICA BKT: NIVEL INICIAL / CONCEPTUAL (P(L)={p_L:.2f}) ===\n"
            f"- El estudiante está comenzando a explorar este tema (P(L)={p_L:.2f} < 0.30).\n"
            "- Partí obligatoriamente de analogías cotidianas accesibles e intuiciones visuales antes de formalizar.\n"
            "- Desglosá la explicación paso a paso y evitá sobrecargar con jerga técnica compleja sin definirla previamente.\n"
        )
    else:  # intermediate
        return (
            f"=== ADAPTACIÓN PEDAGÓGICA BKT: NIVEL INTERMEDIO / CONSOLIDACIÓN (P(L)={p_L:.2f}) ===\n"
            f"- El estudiante posee nociones fundamentales en proceso de afianzamiento (P(L)={p_L:.2f}).\n"
            "- Desarrollá una síntesis equilibrada entre intuición conceptual clara y mecanismos formales rigurosos.\n"
        )

