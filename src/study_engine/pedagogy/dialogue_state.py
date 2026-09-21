from typing import Dict
from study_engine.pedagogy.dialogue_contracts import DialogueState, DialogueTurn, StudentIntentProposal

class DialogueStateTracker:
    """
    Rastrea señales de comprensión/confusión del estudiante.
    
    CONSULTIVO: No actualiza BKT. No evalúa. No acredita.
    Solo adapta la conversación (nivel de lenguaje, ejemplos, profundidad).
    """
    
    def update_from_turn(
        self,
        state: DialogueState,
        turn: DialogueTurn,
    ) -> DialogueState:
        """
        Actualiza contadores y señales.
        """
        new_turn_count = state.turn_count + 1
        new_confusion_count = state.confusion_count
        new_reformulation_count = state.reformulation_count
        new_examples_requested = state.examples_requested
        
        intent = turn.intent_validated_as
        
        if intent == "CONFUSION":
            new_confusion_count += 1
        elif intent == "REFORMULATION":
            new_reformulation_count += 1
        elif intent == "EXAMPLE_REQUEST":
            new_examples_requested += 1
            new_reformulation_count += 1
            
        new_perceived_comprehension = dict(state.perceived_comprehension)
        if turn.comprehension_signal != "UNKNOWN":
            new_perceived_comprehension["latest"] = turn.comprehension_signal

        return DialogueState(
            episode_id=state.episode_id,
            turns=state.turns + (turn,),
            turn_count=new_turn_count,
            perceived_comprehension=new_perceived_comprehension,
            reformulation_count=new_reformulation_count,
            confusion_count=new_confusion_count,
            examples_requested=new_examples_requested,
            clarification_topics=state.clarification_topics,
            dialogue_limit_reached=False,
            limit_reason=None
        )
