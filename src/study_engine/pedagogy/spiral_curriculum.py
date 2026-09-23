"""Currículo en Espiral: Profundización retroactiva de conceptos.

Permite detectar oportunidades pedagógicas para revisitar y profundizar KCs previos
en consolidación cuando el estudiante domina un nuevo concepto causalmente relacionado.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from study_engine.pedagogy.exercise_compiler import HIGH_MASTERY_THRESHOLD

logger = logging.getLogger(__name__)

# Rango de maestría para KCs previos candidatos a profundización retroactiva (E2):
# - Límite inferior (0.4): Si P(L) < 0.4, el estudiante aún no asimiló el concepto
#   básico. Profundizar sería contraproducente (riesgo de sobrecarga cognitiva).
# - Límite superior (0.75): Si P(L) > 0.75, el estudiante ya domina el concepto.
#   No necesita profundización adicional (rendimientos decrecientes).
# - Rango óptimo [0.4, 0.75]: El estudiante tiene bases sólidas pero aún puede
#   beneficiarse de aplicar el concepto en contexto más complejo (Multi-KC).
RETROACTIVE_RANGE_DEFAULT: Tuple[float, float] = (0.4, 0.75)


class SpiralCurriculumEngine:
    """Detecta oportunidades de profundización retroactiva determinista (Currículo en Espiral).

    Flujo:
    1. Estudiante aprende 'punteros' (P(L) = 0.65)
    2. Luego aprende 'race_conditions' (P(L) = 0.72)
    3. Sistema detecta relación causal: race_conditions -> punteros
    4. Sistema sugiere: "Volvamos a punteros con contexto de concurrencia"
    5. Propone Multi-KC: punteros + race_conditions
    """

    # E1: Usar la misma constante canónica que el Multi-KC Generator
    MIN_CURRENT_MASTERY: float = HIGH_MASTERY_THRESHOLD  # 0.6

    # Mapa de relaciones causales entre KCs:
    # Clave: KC nuevo que habilita profundización
    # Valor: KCs previos que pueden profundizarse
    CAUSAL_RELATIONS: Dict[str, List[str]] = {
        "race_conditions": ["punteros", "memoria_compartida", "sincronizacion"],
        "buffer_overflow": ["punteros", "aritmetica_punteros", "stack"],
        "use_after_free": ["punteros", "gestion_memoria", "heap"],
        "deadlock": ["mutex", "semaforos", "concurrencia"],
        "paginacion": ["memoria_virtual", "tlb", "page_faults"],
        "integer_overflow": ["aritmetica_punteros", "tipos_de_datos", "malloc"],
        "toctou": ["sincronizacion", "verificacion", "filesystem"],
    }

    def __init__(self, bkt_tracker: Optional[Any] = None) -> None:
        self.bkt = bkt_tracker

    def _get_mastery(self, student_id: str, kc_id: str) -> float:
        """Extrae el valor p_L de forma polimórfica y segura desde el tracker o mock."""
        if self.bkt is None:
            return 0.0

        # Caso 1: self.bkt es un dict mock directo {kc_id: {'p_L': 0.7}} o {kc_id: 0.7}
        if isinstance(self.bkt, dict):
            entry = self.bkt.get(kc_id, {})
            if isinstance(entry, dict):
                return float(entry.get("p_L", 0.0))
            if isinstance(entry, (int, float)):
                return float(entry)
            return 0.0

        # Caso 2: self.bkt tiene método get_student_state(student_id)
        if hasattr(self.bkt, "get_student_state") and callable(self.bkt.get_student_state):
            try:
                bkt_state = self.bkt.get_student_state(student_id)
                if isinstance(bkt_state, dict):
                    entry = bkt_state.get(kc_id, {})
                    if isinstance(entry, dict):
                        return float(entry.get("p_L", 0.0))
                    return float(getattr(entry, "p_L", 0.0))
            except Exception as err:
                logger.debug("Spiral engine: fallo al consultar get_student_state: %s", err)

        # Caso 3: self.bkt tiene get_state(kc_id) (BKTTracker estándar)
        if hasattr(self.bkt, "get_state") and callable(self.bkt.get_state):
            try:
                state_obj = self.bkt.get_state(kc_id)
                if state_obj is not None:
                    return float(getattr(state_obj, "p_L", 0.0))
            except Exception as err:
                logger.debug("Spiral engine: fallo al consultar get_state: %s", err)

        # Caso 4: storage interno en self.bkt.storage.get_bkt_state(kc_id)
        storage = getattr(self.bkt, "storage", None)
        if storage and hasattr(storage, "get_bkt_state") and callable(storage.get_bkt_state):
            try:
                state_obj = storage.get_bkt_state(kc_id)
                if state_obj is not None:
                    return float(getattr(state_obj, "p_L", 0.0))
            except Exception as err:
                logger.debug("Spiral engine: fallo al consultar storage: %s", err)

        return 0.0

    def detect_spiral_opportunities(
        self,
        current_kc: str,
        student_id: str,
        min_current_mastery: Optional[float] = None,
        retroactive_range: Tuple[float, float] = RETROACTIVE_RANGE_DEFAULT,
    ) -> List[Dict[str, Any]]:
        """Detecta KCs previos que pueden profundizarse con el KC actual.

        Args:
            current_kc: KC que el estudiante acaba de dominar
            student_id: ID del estudiante
            min_current_mastery: P(L) mínimo del KC actual (default: MIN_CURRENT_MASTERY)
            retroactive_range: Rango de P(L) para KCs previos [min, max]

        Returns:
            Lista de oportunidades de profundización retroactiva ordenada por retro_mastery desc.
        """
        if not current_kc or not isinstance(current_kc, str):
            return []

        threshold = self.MIN_CURRENT_MASTERY if min_current_mastery is None else min_current_mastery

        # Verificar que el KC actual esté suficientemente dominado
        current_mastery = self._get_mastery(student_id, current_kc)
        if current_mastery < threshold:
            return []

        # Buscar KCs relacionados causalmente
        related_kcs = self.CAUSAL_RELATIONS.get(current_kc, [])

        # E3: Manejo explícito de KCs sin relación causal definida
        if not related_kcs:
            logger.debug("No causal relations defined for KC: %s", current_kc)
            return []

        opportunities: List[Dict[str, Any]] = []
        for retro_kc in related_kcs:
            retro_mastery = self._get_mastery(student_id, retro_kc)

            # Solo profundizar si el KC previo está en el rango óptimo
            if retroactive_range[0] <= retro_mastery <= retroactive_range[1]:
                opportunities.append({
                    "new_kc": current_kc,
                    "retroactive_kc": retro_kc,
                    "new_mastery": current_mastery,
                    "retro_mastery": retro_mastery,
                    "reason": self._generate_reason(current_kc, retro_kc),
                    "suggested_exercise": self._suggest_exercise(current_kc, retro_kc),
                })

        # Ordenar por relevancia (mayor retro_mastery primero)
        opportunities.sort(key=lambda x: x["retro_mastery"], reverse=True)

        return opportunities

    def _generate_reason(self, new_kc: str, retro_kc: str) -> str:
        """Genera explicación pedagógica fundamentada de la profundización."""
        reasons: Dict[Tuple[str, str], str] = {
            ("race_conditions", "punteros"): (
                "Ahora que entendés race conditions, volvamos a punteros pero con "
                "contexto de concurrencia: ¿qué pasa cuando dos hilos acceden al "
                "mismo puntero sin sincronización?"
            ),
            ("buffer_overflow", "punteros"): (
                "Ya dominás buffer overflow. Profundicemos en punteros: ¿cómo la "
                "aritmética de punteros mal calculada lleva a escribir fuera del buffer?"
            ),
            ("use_after_free", "punteros"): (
                "Use-after-free es crítico. Volvamos a punteros con contexto de ciclo "
                "de vida: ¿qué pasa cuando un puntero sigue vivo después de free()?"
            ),
            ("deadlock", "mutex"): (
                "Entendés deadlock. Profundicemos en mutex: ¿qué condiciones de "
                "adquisición llevan a interbloqueo y cómo prevenirlas?"
            ),
            ("paginacion", "memoria_virtual"): (
                "Paginación dominada. Volvamos a memoria virtual: ¿cómo el TLB "
                "acelera la traducción de direcciones virtuales?"
            ),
            ("integer_overflow", "aritmetica_punteros"): (
                "Integer overflow detectado. Volvamos a aritmética de punteros: ¿cómo "
                "un desbordamiento en el cálculo de offset corrompe memoria?"
            ),
            ("toctou", "sincronizacion"): (
                "Entendés TOCTOU. Profundicemos en sincronización: ¿cómo cerrar la "
                "ventana entre la verificación de permisos y el acceso al recurso?"
            ),
        }

        return reasons.get(
            (new_kc, retro_kc),
            f"Profundizar {retro_kc} aplicando los fundamentos recién adquiridos de {new_kc}.",
        )

    def _suggest_exercise(self, new_kc: str, retro_kc: str) -> Dict[str, Any]:
        """Sugiere la especificación formal del ejercicio Multi-KC."""
        return {
            "type": "multi_kc",
            "kc_ids": [retro_kc, new_kc],
            "difficulty": "advanced",
            "rationale": f"Combinación causal: {retro_kc} + {new_kc}",
        }

    def inject_spiral_directive(self, opportunities: List[Dict[str, Any]]) -> Optional[str]:
        """Genera directiva pedagógica para inyección en el prompt del tutor socrático.

        E4: Preserva la agencia del estudiante estableciendo explícitamente que el tutor
        debe proponer la profundización y solo generar el ejercicio si el alumno acepta.
        """
        if not opportunities:
            return None

        best = opportunities[0]

        directive = f"""
=== PROFUNDIZACIÓN RETROACTIVA (CURRÍCULO EN ESPIRAL) ===

Detecté una oportunidad de profundización:

{best['reason']}

Estado actual:
- {best['new_kc']}: P(L) = {best['new_mastery']:.2f} (dominado)
- {best['retroactive_kc']}: P(L) = {best['retro_mastery']:.2f} (en consolidación)

ACCIÓN RECOMENDADA:
Ofrecer al estudiante un ejercicio Multi-KC combinando ambos conceptos.
Si el estudiante acepta, el tutor debe invocar:
POST /api/student/exercises/generate/multi-kc
con payload: {{"kc_ids": {json.dumps(best['suggested_exercise']['kc_ids'])}}}

IMPORTANTE: NO generar el ejercicio automáticamente. Solo sugerirlo.
El estudiante debe aceptar explícitamente antes de generar.
""".strip()

        return directive
