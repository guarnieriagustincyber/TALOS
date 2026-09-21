"""Deterministic policy for Socratic Dialogue Engine (Fase 7).

INVARIANTS:
1. Pure deterministic evaluation: zero LLM in this layer.
2. Anti-microevaluation: strictly forbids evaluative praise/criticism ('correcto', 'mal', etc.).
3. Exercise answer protection: blocks responses that leak exercise solutions.
4. Turn limits suggest exercises; they never force episode transitions.
"""

from typing import Any, List, Optional, Sequence, Tuple
from dataclasses import dataclass
from study_engine.pedagogy.dialogue_contracts import DialogueState, StudentIntentProposal, SocraticQuestion

FORBIDDEN_MICRO_EVAL_WORDS: Tuple[str, ...] = (
    "correcto",
    "muy bien",
    "excelente",
    "exacto",
    "perfecto",
    "bien hecho",
    "genial",
    "incorrecto",
    "mal",
    "equivocado",
)


@dataclass(frozen=True)
class ValidatedIntent:
    action: str  # PROCEED_DIALOGUE | TRANSITION_TO_SUGGEST_EXERCISE | TRANSITION_TO_CLOSED | REDIRECT_TO_KC
    query_text: str
    proposed_intent: str


@dataclass(frozen=True)
class PolicyVerdict:
    approved: bool
    rejection_reason: Optional[str]
    question_dimension: str
    question_difficulty: int
    rule_id: str


class DialoguePolicy:
    """
    Política determinista que valida TODO en el diálogo.
    Cero LLM en esta capa. Cero evaluación del estudiante.
    """
    FORBIDDEN_WORDS = FORBIDDEN_MICRO_EVAL_WORDS

    def validate_intent(
        self,
        proposal: StudentIntentProposal,
        dialogue_state: DialogueState,
        has_qualifiable_exercises: bool = True,
    ) -> ValidatedIntent:
        """
        Valida la propuesta de intención del estudiante.
        NUNCA auto-ejecuta. Siempre valida antes de actuar.
        """
        intent = proposal.proposed_intent.upper()
        
        if intent == "PROCEED_TO_EXERCISE":
            return ValidatedIntent(
                action="TRANSITION_TO_SUGGEST_EXERCISE",
                query_text="",
                proposed_intent=intent,
            )
        if intent == "END_DIALOGUE":
            return ValidatedIntent(
                action="TRANSITION_TO_CLOSED",
                query_text="",
                proposed_intent=intent,
            )
        if intent == "OFF_TOPIC":
            return ValidatedIntent(
                action="REDIRECT_TO_KC",
                query_text="",
                proposed_intent=intent,
            )
            
        return ValidatedIntent(
            action="PROCEED_DIALOGUE",
            query_text=proposal.proposed_intent,
            proposed_intent=intent,
        )

    def validate_response(
        self,
        response: str,
        socratic_question: Optional[str],
        evidence: Any,
        dialogue_state: DialogueState,
        active_exercise_solution: Optional[str] = None,
    ) -> PolicyVerdict:
        """
        Valida la respuesta propuesta antes de emitirla al estudiante.
        """
        lower_response = response.lower()
        
        # 1. Anti-microevaluación estricta
        for fw in self.FORBIDDEN_WORDS:
            if fw in lower_response:
                return PolicyVerdict(
                    approved=False,
                    rejection_reason=f"Microevaluación detectada: '{fw}'. Prohibido evaluar en el diálogo.",
                    question_dimension="",
                    question_difficulty=0,
                    rule_id="RULE_NO_MICRO_EVAL",
                )

        # 2. Protección contra revelación de soluciones de ejercicios
        if active_exercise_solution:
            sol_clean = str(active_exercise_solution).strip().lower()
            if len(sol_clean) >= 2 and sol_clean in lower_response:
                return PolicyVerdict(
                    approved=False,
                    rejection_reason="La respuesta propuesta revela la solución de un ejercicio calificado.",
                    question_dimension="",
                    question_difficulty=0,
                    rule_id="RULE_NO_EXERCISE_ANSWER",
                )

        # 3. Límite de longitud concisa (máximo 150 palabras)
        word_count = len(response.split())
        if word_count > 150:
            return PolicyVerdict(
                approved=False,
                rejection_reason=f"Respuesta excede el límite de 150 palabras ({word_count}).",
                question_dimension="",
                question_difficulty=0,
                rule_id="RULE_MAX_LENGTH",
            )
            
        # 4. Requiere evidencia verificable
        chunks = getattr(evidence, "chunks", None)
        if not evidence or not chunks:
            return PolicyVerdict(
                approved=False,
                rejection_reason="La respuesta no cuenta con evidencia que la respalde en las fuentes autorizadas.",
                question_dimension="",
                question_difficulty=0,
                rule_id="RULE_NEEDS_EVIDENCE",
            )

        return PolicyVerdict(
            approved=True,
            rejection_reason=None,
            question_dimension="REASONING",
            question_difficulty=2,
            rule_id="RULE_VALID_RESPONSE",
        )

    def validate_socratic_question(
        self,
        question: SocraticQuestion,
    ) -> bool:
        """Verifica que la pregunta socrática explore y tenga respaldo evidencial."""
        if not question.evidence_ids or len(question.evidence_ids) == 0:
            return False
        if not question.source_ids or len(question.source_ids) == 0:
            return False
        if "explora" not in question.target_dimension_note.lower():
            return False
        return True

    def should_suggest_exercise(
        self,
        dialogue_state: DialogueState,
    ) -> Tuple[bool, str]:
        """
        Determina determinísticamente si sugerir pasar al ejercicio.
        La sugerencia NO obliga al estudiante.
        """
        max_turns = 8
        max_reformulations = 3
        max_confusion = 2
        
        if dialogue_state.turn_count >= max_turns:
            return True, "max_turns"
        if dialogue_state.reformulation_count >= max_reformulations:
            return True, "max_reformulations"
        if dialogue_state.confusion_count >= max_confusion:
            return True, "max_confusion"
        return False, ""
