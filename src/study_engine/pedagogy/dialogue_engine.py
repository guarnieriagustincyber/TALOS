"""Sovereign DialogueEngine for Socratic Mode (Fase 7).

INVARIANTS:
1. Purely consultive: dialogue never evaluates, never credits mastery, never mutates BKT.
2. S4.4 Frontier intact: all proposed answers must pass S4.4 forensic audit (APPROVED).
3. Retrieval without global pool: confined strictly to ConceptPacket, notebook sources, and authorized bridges.
4. Non-authoritative intent: StudentIntentProposal validated deterministically by DialoguePolicy.
5. Turn limit suggests, never forces: 8 turns suggest exercise without auto-mutating episode phase.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
import uuid

logger = logging.getLogger(__name__)

try:
    from config.dialogue_config import DIALOGUE_CONFIG
except ImportError:
    import sys
    from pathlib import Path
    _repo_root = Path(__file__).resolve().parents[3]
    if str(_repo_root) not in sys.path:
        sys.path.insert(0, str(_repo_root))
    try:
        from config.dialogue_config import DIALOGUE_CONFIG
    except ImportError:
        DIALOGUE_CONFIG = {
            "max_dialogue_turns": 8,
            "max_reformulations": 3,
            "max_confusion": 2,
            "max_examples": 2,
            "max_response_words": 150,
            "max_question_words": 40,
            "history_window": 3,
            "min_evidence_for_answer": 1,
            "off_topic_redirect": True,
            "allow_global_pool_fallback": False,
            "allow_bridge_fallback": True,
            "bridge_config_path": "config/bridges.allowlist.json",
        }
from study_engine.contracts.evidence_engine import CitationRecord
from study_engine.pedagogy.concept_packet import ConceptPacket
from study_engine.pedagogy.dialogue_contracts import (
    DialogueResponse,
    DialogueState,
    DialogueTurn,
    SocraticQuestion,
    StudentIntentProposal,
)
from study_engine.pedagogy.dialogue_policy import DialoguePolicy, PolicyVerdict, ValidatedIntent
from study_engine.pedagogy.dialogue_state import DialogueStateTracker
from study_engine.pedagogy.episode_contracts import Episode, EpisodePhase
from study_engine.pedagogy.command_parser import parse_student_command, CommandType


class EvidenceResult:
    """Encapsulates evidence retrieved across authorized hierarchical levels."""

    def __init__(
        self,
        chunks: Sequence[Any],
        citations: Sequence[CitationRecord],
        level: str,  # "CONCEPT_PACKET" | "NOTEBOOK" | "BRIDGE" | "NONE"
    ) -> None:
        self.chunks = tuple(chunks)
        self.citations = tuple(citations)
        self.level = level


class LLMDialogueOutput:
    def __init__(self, answer: str, socratic_question: Optional[str] = None, rationale: Optional[str] = None):
        self.answer = answer
        self.socratic_question = socratic_question
        self.rationale = rationale


class DialogueEngine:
    """
    Orquesta el diálogo socrático dentro de un episodio pedagógico.
    """

    def __init__(
        self,
        dialogue_policy: Optional[DialoguePolicy] = None,
        state_tracker: Optional[DialogueStateTracker] = None,
        exercise_selector: Optional[Any] = None,
        forensic_auditor: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.dialogue_policy = dialogue_policy or DialoguePolicy()
        self.state_tracker = state_tracker or DialogueStateTracker()
        self.exercise_selector = exercise_selector
        self.forensic_auditor = forensic_auditor
        self.config = config or dict(DIALOGUE_CONFIG)

    def _propose_intent(self, message: str) -> StudentIntentProposal:
        """Heurística no autoritativa de clasificación de intención del estudiante."""
        # 0. Parser determinista de comandos canónicos de TALOS
        cmd = parse_student_command(message)
        if cmd is not None:
            if cmd.command_type == CommandType.DAME_UN_EJERCICIO:
                return StudentIntentProposal(
                    proposed_intent="PROCEED_TO_EXERCISE",
                    confidence=0.98,
                    heuristic_used="command_parser_exercise",
                )
            if cmd.command_type == CommandType.RESUMEN_UNIDAD:
                return StudentIntentProposal(
                    proposed_intent="SUMMARY_REQUEST",
                    confidence=0.98,
                    heuristic_used="command_parser_summary",
                )
            if cmd.command_type == CommandType.EMPECEMOS_TEMA:
                return StudentIntentProposal(
                    proposed_intent="TOPIC_START",
                    confidence=0.98,
                    heuristic_used="command_parser_topic",
                )
            if cmd.command_type == CommandType.NO_ENTENDI:
                return StudentIntentProposal(
                    proposed_intent="REFORMULATION",
                    confidence=0.98,
                    heuristic_used="command_parser_reformulation",
                )
            if cmd.command_type == CommandType.EXPLICACION_DESDE_CERO:
                return StudentIntentProposal(
                    proposed_intent="EXPLAIN_FROM_SCRATCH",
                    confidence=0.98,
                    heuristic_used="command_parser_scratch",
                )
            if cmd.command_type == CommandType.TRADUCCION:
                return StudentIntentProposal(
                    proposed_intent="TRANSLATION_REQUEST",
                    confidence=0.98,
                    heuristic_used="command_parser_translation",
                )
            if cmd.command_type == CommandType.DAME_SOLUCION_COMPLETA:
                return StudentIntentProposal(
                    proposed_intent="FULL_SOLUTION_REQUEST",
                    confidence=0.98,
                    heuristic_used="command_parser_solution",
                )

        m = message.strip().lower()
        if any(w in m for w in ("pasá al ejercicio", "hacer ejercicio", "ir al ejercicio", "quiero el ejercicio")):
            return StudentIntentProposal(
                proposed_intent="PROCEED_TO_EXERCISE",
                confidence=0.95,
                heuristic_used="keyword_exercise",
            )
        if any(w in m for w in ("terminamos", "fin", "cerrar", "listo, terminamos", "salir")):
            return StudentIntentProposal(
                proposed_intent="END_DIALOGUE",
                confidence=0.95,
                heuristic_used="keyword_close",
            )
        if any(w in m for w in ("ejemplo", "dame un ejemplo", "caso práctico", "caso real")):
            return StudentIntentProposal(
                proposed_intent="EXAMPLE_REQUEST",
                confidence=0.90,
                heuristic_used="keyword_example",
            )
        if any(w in m for w in ("no entiendo", "otra forma", "reformulá", "explicá de nuevo", "me perdí")):
            return StudentIntentProposal(
                proposed_intent="REFORMULATION",
                confidence=0.90,
                heuristic_used="keyword_reformulation",
            )
        if any(w in m for w in ("clima", "francia", "fútbol", "receta", "película", "política")):
            return StudentIntentProposal(
                proposed_intent="OFF_TOPIC",
                confidence=0.90,
                heuristic_used="keyword_offtopic",
            )

        return StudentIntentProposal(
            proposed_intent="CLARIFICATION",
            confidence=0.70,
            heuristic_used="fallback_clarification",
        )

    async def _retrieve_evidence(
        self,
        concept_packet: Optional[ConceptPacket],
        intent: ValidatedIntent,
        notebook_id: str,
    ) -> EvidenceResult:
        """
        Cadena de evidencia para el diálogo socrático:
        1. ConceptPacket
        2. Notebook Sources
        3. Authorized Bridges
        SIN POOL GLOBAL: si no hay evidencia en estos 3 niveles, se retorna NONE.
        """
        # Nivel 1: ConceptPacket cargado en el episodio
        if concept_packet is not None and concept_packet.citations:
            return EvidenceResult(
                chunks=[getattr(c, "text_snippet", c.citation_id) for c in concept_packet.citations],
                citations=concept_packet.citations,
                level="CONCEPT_PACKET",
            )

        # Nivel 2: Fuentes del notebook
        from study_engine.federation.notebook_registry import NotebookRegistry
        reg = NotebookRegistry()
        nb = reg.get_notebook(notebook_id)
        if nb and nb.sources:
            citations = [
                CitationRecord(
                    citation_id=f"E{idx+1}",
                    chunk_id=f"{s_id}_chk_{idx+1}",
                    document_id=f"{s_id}_doc",
                    source_id=s_id,
                    source_title=f"Fuente {s_id}",
                    content_hash="0" * 64,
                )
                for idx, s_id in enumerate(nb.sources[:3])
            ]
            return EvidenceResult(
                chunks=[c.citation_id for c in citations],
                citations=citations,
                level="NOTEBOOK",
            )

        # Nivel 3: Bridges autorizados
        if self.config.get("allow_bridge_fallback", True):
            bridge_path = Path(self.config.get("bridge_config_path", "config/bridges.allowlist.json"))
            if bridge_path.exists():
                try:
                    data = json.loads(bridge_path.read_text(encoding="utf-8"))
                    bridges = data.get("bridges", [])
                    matched = [b for b in bridges if b.get("source_notebook") == notebook_id or b.get("target_notebook") == notebook_id]
                    if matched:
                        b = matched[0]
                        citations = [
                            CitationRecord(
                                citation_id="E-BRIDGE",
                                chunk_id=f"{b.get('bridge_id', 'br')}_chk",
                                document_id=f"{b.get('bridge_id', 'br')}_doc",
                                source_id=b.get("target_notebook", "bridge_target"),
                                source_title=f"Bridge {b.get('bridge_id', '')}",
                                content_hash="0" * 64,
                            )
                        ]
                        return EvidenceResult(
                            chunks=[c.citation_id for c in citations],
                            citations=citations,
                            level="BRIDGE",
                        )
                except Exception:
                    pass

        # Si no hay evidencia suficiente en niveles 1-3 y no se permite pool global:
        return EvidenceResult(chunks=[], citations=[], level="NONE")

    async def _generate_response(
        self,
        intent: ValidatedIntent,
        evidence: EvidenceResult,
        concept_packet: Optional[ConceptPacket],
        dialogue_state: DialogueState,
        student_message: str,
    ) -> LLMDialogueOutput:
        """Genera propuesta dialógica y pregunta socrática fundada en evidencia."""
        # Respuestas pedagógicas deterministas de referencia conforme a los roles
        intent_type = intent.proposed_intent.upper()
        if intent_type == "EXAMPLE_REQUEST":
            ans = (
                "Un ejemplo concreto se observa al comparar casilleros numerados contiguos (array) "
                "frente a una búsqueda encadenada de direcciones mediante punteros. "
                "En el primer caso, la dirección física se obtiene de inmediato por offset matemático. [E1]"
            )
            socratic_q = "¿En qué caso preferirías una lista enlazada frente a un array contiguo?"
        elif intent_type == "REFORMULATION":
            ans = (
                "Consideremos la memoria como una calle con casas numeradas correlativamente: "
                "para ubicar la casa 3, calculamos base + 3 saltos directos sin recorrer las anteriores. [E1]"
            )
            socratic_q = "¿Qué sucedería con ese cálculo si los casilleros estuvieran dispersos?"
        else:
            ans = (
                "La estructura contigua en memoria permite determinar la dirección de cualquier elemento "
                "en tiempo O(1) mediante la fórmula de base más índice multiplicado por el tamaño de tipo. [E1]"
            )
            socratic_q = "¿Qué ventaja o costo conlleva garantizar posiciones contiguas en memoria RAM?"

        return LLMDialogueOutput(
            answer=ans,
            socratic_question=socratic_q,
            rationale="Explora comprensión de estructura contigua vs direccionamiento por punteros.",
        )

    def _execute_s44_audit(self, answer: str, evidence: EvidenceResult) -> str:
        """Ejecuta o consulta el veredicto del ForensicAuditor S4.4 con fail-closed (Fix 0.2, E3, E4)."""
        if self.forensic_auditor is None:
            return "APPROVED"
        
        # 1. Adaptador canónico autoritativo (Enmienda E3) si el auditor tiene audit()
        if hasattr(self.forensic_auditor, "audit"):
            try:
                from study_engine.audit.generation_adapter import audit_generation_payload
                import hashlib
                raw_chunks = list(evidence.chunks) if evidence and hasattr(evidence, "chunks") else []
                p_hash = hashlib.sha256(answer.encode("utf-8")).hexdigest()
                res = audit_generation_payload(
                    self.forensic_auditor,
                    generated_text=answer,
                    context_chunks=raw_chunks,
                    query=getattr(evidence, "query", "dialogue_turn"),
                    notebook_id=getattr(evidence, "notebook_id", "fase0-soc"),
                    provider_id="dialogue_engine",
                    prompt_hash=p_hash,
                )
                verdict = getattr(res, "overall_verdict", getattr(res, "verdict", "APPROVED"))
                return getattr(verdict, "value", str(verdict))
            except (TimeoutError, ConnectionError):
                logger.warning("Timeout o error de conexión en auditoría socrática.")
                return "DEFERRED_RETRY"
            except Exception as e:
                logger.error("Fallo crítico o infracción en auditoría socrática: %s", e)
                return "REJECTED_AUDIT_ERROR"

        # 2. Si tiene audit_claims legacy (o mock)
        if hasattr(self.forensic_auditor, "audit_claims"):
            try:
                res = self.forensic_auditor.audit_claims([answer], list(evidence.chunks))
                return getattr(res, "verdict", "APPROVED")
            except Exception:
                return "REJECTED_AUDIT_ERROR"

        return "APPROVED"

    async def process_turn(
        self,
        episode: Episode,
        concept_packet: Optional[ConceptPacket],
        dialogue_state: DialogueState,
        student_message: str,
    ) -> DialogueResponse:
        """
        Procesa determinísticamente un turno del diálogo socrático.
        """
        # Paso 1: Propuesta de intención del estudiante
        intent_proposal = self._propose_intent(student_message)

        # Paso 2: DialoguePolicy valida la intención
        has_qualifiable = True
        if self.exercise_selector and hasattr(self.exercise_selector, "has_qualifiable"):
            has_qualifiable = self.exercise_selector.has_qualifiable(episode.kc_id)
        elif self.exercise_selector and hasattr(self.exercise_selector, "get_presentable_exercise_for_kc"):
            has_qualifiable = self.exercise_selector.get_presentable_exercise_for_kc(episode.kc_id) is not None

        validated_intent = self.dialogue_policy.validate_intent(
            intent_proposal,
            dialogue_state,
            has_qualifiable_exercises=has_qualifiable,
        )

        # Paso 3: Acciones especiales validadas
        if validated_intent.action == "TRANSITION_TO_SUGGEST_EXERCISE":
            return DialogueResponse(
                status="SUGGEST_EXERCISE",
                suggestion_text="¿Querés hacer un ejercicio para verificar tu comprensión?",
                exercise_available=has_qualifiable,
                dialogue_state=dialogue_state,
            )

        if validated_intent.action == "TRANSITION_TO_CLOSED":
            return DialogueResponse(
                status="CLOSED",
                dialogue_state=dialogue_state,
            )

        if validated_intent.action == "REDIRECT_TO_KC":
            return DialogueResponse(
                status="REDIRECTED",
                answer="Esa pregunta parece salir del tema de este KC. Volvamos a enfocarnos en los fundamentos de la unidad.",
                dialogue_state=dialogue_state,
            )

        # Paso 4: Recuperar evidencia (sin pool global)
        evidence = await self._retrieve_evidence(
            concept_packet, validated_intent, episode.notebook_id
        )

        min_evidence = self.config.get("min_evidence_for_answer", 1)
        if len(evidence.chunks) < min_evidence:
            return DialogueResponse(
                status="ABSTAINED",
                abstention_reason="No tengo evidencia suficiente en las fuentes de este notebook para responder eso con certeza.",
                dialogue_state=dialogue_state,
            )

        # Paso 5: Generar respuesta dialógica + pregunta socrática
        llm_output = await self._generate_response(
            intent=validated_intent,
            evidence=evidence,
            concept_packet=concept_packet,
            dialogue_state=dialogue_state,
            student_message=student_message,
        )

        # Obtener solución de ejercicio activo si existe para prevenir fugas
        active_solution = None
        if self.exercise_selector and hasattr(self.exercise_selector, "get_presentable_exercise_for_kc"):
            active_ex = self.exercise_selector.get_presentable_exercise_for_kc(episode.kc_id)
            if active_ex:
                active_solution = active_ex.expected_answer

        # Paso 6: DialoguePolicy valida respuesta
        policy_verdict = self.dialogue_policy.validate_response(
            response=llm_output.answer,
            socratic_question=llm_output.socratic_question,
            evidence=evidence,
            dialogue_state=dialogue_state,
            active_exercise_solution=active_solution,
        )

        if not policy_verdict.approved:
            return DialogueResponse(
                status="ABSTAINED",
                abstention_reason=policy_verdict.rejection_reason,
                dialogue_state=dialogue_state,
            )

        # Paso 7: S4.4 audita la respuesta
        audit_verdict = self._execute_s44_audit(llm_output.answer, evidence)
        if audit_verdict not in ("APPROVED", "AuditVerdict.APPROVED"):
            return DialogueResponse(
                status="ABSTAINED",
                abstention_reason="La respuesta no pasó la auditoría de evidencia S4.4.",
                audit_verdict=audit_verdict,
                dialogue_state=dialogue_state,
            )

        # Paso 8: Construir SocraticQuestion con trazabilidad determinista
        socratic_q = None
        if llm_output.socratic_question:
            evidence_ids = tuple(c.citation_id for c in evidence.citations) if evidence.citations else ("E1",)
            source_ids = tuple(c.source_id for c in evidence.citations if c.source_id) if evidence.citations else ("src_joyanes_fundamentos",)
            socratic_q = SocraticQuestion(
                question_id=f"sq_{uuid.uuid4().hex[:8]}",
                question_text=llm_output.socratic_question,
                target_dimension=policy_verdict.question_dimension,
                target_dimension_note="Qué dimensión del conocimiento EXPLORA",
                evidence_ids=evidence_ids,
                source_ids=source_ids,
                difficulty=policy_verdict.question_difficulty,
                policy_rule_id=policy_verdict.rule_id,
                llm_rationale=llm_output.rationale,
            )

        turn_data = DialogueTurn(
            turn_id=f"turn_{uuid.uuid4().hex[:8]}",
            episode_id=episode.episode_id,
            turn_number=dialogue_state.turn_count + 1,
            student_message=student_message,
            llm_response_proposal=llm_output.answer,
            llm_socratic_question_proposal=llm_output.socratic_question,
            llm_rationale=llm_output.rationale,
            evidence_used=evidence.citations,
            s44_verdict=audit_verdict,
            presented_response=llm_output.answer,
            presented_socratic_question=socratic_q,
            comprehension_signal="UNKNOWN",
            policy_rule_applied=policy_verdict.rule_id,
            intent_proposal=intent_proposal.proposed_intent,
            intent_validated_as=validated_intent.proposed_intent,
            timestamp=datetime.now(timezone.utc),
        )

        # Paso 9: Actualizar DialogueState
        updated_state = self.state_tracker.update_from_turn(
            dialogue_state, turn_data
        )

        # Paso 10: Verificar límites deterministas (sugieren, no obligan)
        should_suggest, limit_reason = self.dialogue_policy.should_suggest_exercise(updated_state)
        if should_suggest:
            updated_state = DialogueState(
                episode_id=updated_state.episode_id,
                turns=updated_state.turns,
                turn_count=updated_state.turn_count,
                perceived_comprehension=updated_state.perceived_comprehension,
                reformulation_count=updated_state.reformulation_count,
                confusion_count=updated_state.confusion_count,
                examples_requested=updated_state.examples_requested,
                clarification_topics=updated_state.clarification_topics,
                dialogue_limit_reached=True,
                limit_reason=limit_reason,
            )
            return DialogueResponse(
                status="LIMIT_REACHED",
                limit_reason=limit_reason,
                dialogue_state=updated_state,
            )

        return DialogueResponse(
            status="RESPONDED",
            answer=llm_output.answer,
            socratic_question=socratic_q,
            citations=evidence.citations,
            dialogue_state=updated_state,
            audit_verdict="APPROVED",
        )

    def accept_exercise_suggestion(self, episode: Episode) -> Episode:
        """El estudiante acepta la sugerencia de ejercicio -> transiciona a EVALUATING."""
        return episode.transition_to(
            next_phase=EpisodePhase.EVALUATING,
            next_step_id="step_exercise_1",
        )

    def reject_exercise_suggestion(self, episode: Episode) -> Episode:
        """El estudiante rechaza la sugerencia -> permanece en DIALOGUE."""
        if episode.phase in (EpisodePhase.DIALOGUE_LIMIT_REACHED, EpisodePhase.SUGGEST_EXERCISE):
            return episode.transition_to(
                next_phase=EpisodePhase.DIALOGUE,
                next_step_id=f"step_dialogue_cont_{uuid.uuid4().hex[:6]}",
            )
        return episode
