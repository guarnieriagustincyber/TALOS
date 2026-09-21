from typing import Optional, Tuple, Dict, Literal
from dataclasses import dataclass
from datetime import datetime
from study_engine.contracts.evidence_engine import CitationRecord

@dataclass(frozen=True)
class SocraticQuestion:
    question_id: str
    question_text: str
    
    # "explora", no "evalúa"
    target_dimension: str  # CONCEPTUAL | REASONING | APPLICATION | TRANSFER
    target_dimension_note: str  # "Qué dimensión del conocimiento EXPLORA"
    
    # Evidencia que respalda la respuesta esperada
    evidence_ids: Tuple[str, ...]
    source_ids: Tuple[str, ...]
    
    # Dificultad (1=fácil, 3=desafiante)
    difficulty: int
    
    # Trazabilidad determinista (auditable)
    policy_rule_id: str  # Regla de DialoguePolicy que aprobó esta pregunta
    
    # Metadata del LLM (NO autoridad, solo contexto)
    llm_rationale: Optional[str] = None  # Explicación del modelo, no evidencia

@dataclass(frozen=True)
class DialogueTurn:
    turn_id: str
    episode_id: str
    turn_number: int
    
    # Mensaje del estudiante
    student_message: str
    
    # Propuesta del LLM (antes de validación)
    llm_response_proposal: str
    llm_socratic_question_proposal: Optional[str]
    llm_rationale: Optional[str]  # Metadata del LLM, NO autoridad
    
    # Evidencia que respalda la respuesta
    evidence_used: Tuple[CitationRecord, ...]
    
    # Validación S4.4
    s44_verdict: str  # APPROVED | PARTIAL | REJECTED
    
    # Lo que realmente se presenta (post S4.4 + DialoguePolicy)
    presented_response: Optional[str]
    presented_socratic_question: Optional[SocraticQuestion]
    
    # Señal de comprensión consultiva (NO es BKT, NO es evaluación)
    comprehension_signal: str  # UNDERSTOOD | PARTIALLY_UNDERSTOOD | CONFUSED | UNKNOWN
    
    # Trazabilidad determinista (auditable)
    policy_rule_applied: str
    intent_proposal: str
    intent_validated_as: str
    
    timestamp: datetime

from dataclasses import dataclass, field

@dataclass(frozen=True)
class DialogueState:
    episode_id: str
    turns: Tuple[DialogueTurn, ...] = ()
    turn_count: int = 0
    
    # Comprensión percibida (CONSULTIVA, no BKT, no evaluación)
    perceived_comprehension: Dict[str, str] = field(default_factory=dict)
    
    # Contadores para transiciones deterministas
    reformulation_count: int = 0      # Máximo 3
    confusion_count: int = 0          # Máximo 2
    examples_requested: int = 0       # Máximo 2
    
    # Temas que el estudiante pidió aclarar
    clarification_topics: Tuple[str, ...] = ()
    
    # Si se alcanzó algún límite
    dialogue_limit_reached: bool = False
    limit_reason: Optional[str] = None  # "max_turns" | "max_reformulations" | "max_confusion"

@dataclass(frozen=True)
class StudentIntentProposal:
    """Propuesta de clasificación de intención. NO es autoritativa."""
    
    proposed_intent: str
    # CLARIFICATION | EXAMPLE_REQUEST | REFORMULATION | COMPARISON |
    # WHAT_IF | CHALLENGE | PROCEED_TO_EXERCISE | END_DIALOGUE | OFF_TOPIC
    
    confidence: float  # 0.0 - 1.0
    heuristic_used: str  # Qué heurística o señal detectó
    
    # La DialoguePolicy valida o rechaza esta propuesta
    # Nunca se ejecuta automáticamente

@dataclass(frozen=True)
class DialogueResponse:
    status: Literal["RESPONDED", "ABSTAINED", "REDIRECTED", "LIMIT_REACHED", "SUGGEST_EXERCISE", "CLOSED"]
    
    # Si RESPONDED:
    answer: Optional[str] = None
    socratic_question: Optional[SocraticQuestion] = None
    citations: Tuple[CitationRecord, ...] = ()
    
    # Si ABSTAINED:
    abstention_reason: Optional[str] = None
    
    # Si LIMIT_REACHED:
    limit_reason: Optional[str] = None
    
    # Si SUGGEST_EXERCISE:
    suggestion_text: Optional[str] = None
    exercise_available: bool = False
    
    # Estado actualizado del diálogo
    dialogue_state: Optional[DialogueState] = None
    
    # S4.4
    audit_verdict: Optional[str] = None
