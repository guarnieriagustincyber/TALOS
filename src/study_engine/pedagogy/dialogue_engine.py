"""Sovereign DialogueEngine for Socratic Mode (Fase 7).

INVARIANTS:
1. Purely consultive: dialogue never evaluates, never credits mastery, never mutates BKT.
2. S4.4 Frontier intact: all proposed answers must pass S4.4 forensic audit (APPROVED).
3. Retrieval without global pool: confined strictly to ConceptPacket, notebook sources, and authorized bridges.
4. Non-authoritative intent: StudentIntentProposal validated deterministically by DialoguePolicy.
5. Turn limit suggests, never forces: 8 turns suggest exercise without auto-mutating episode phase.
"""

from datetime import datetime, timezone
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
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
from study_engine.audit.contracts import AuditVerdict
from study_engine.audit.claim_extractor import ClaimExtractor
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
        chunk_content_loader: Optional[Callable[[str], Any]] = None,
    ) -> None:
        self.dialogue_policy = dialogue_policy or DialoguePolicy()
        self.state_tracker = state_tracker or DialogueStateTracker()
        self.exercise_selector = exercise_selector
        self.forensic_auditor = forensic_auditor
        self.config = config or dict(DIALOGUE_CONFIG)
        # M1-02 (provenance del diálogo): loader determinista chunk_id -> Chunk
        # del store autorizado. Sin loader (wiring de tests), el Nivel 1 conserva
        # el comportamiento anterior (identidades sin contenido materializado).
        self.chunk_content_loader = chunk_content_loader

    def _load_verified_chunk(self, citation: CitationRecord) -> Optional[Dict[str, Any]]:
        """Materializa el Chunk citado y verifica su identidad (S4.4).

        M1-02: la auditoría generation_adapter exige provenance completa
        (chunk_id, document_id, source_id, source_title) y contenido con hash
        verificable; el Nivel 1 entregaba strings de citation_id sin provenance
        ni contenido (hallazgo live 2026-10-20: REJECTED_AUDIT_ERROR previo a
        generación). El contenido se recupera por chunk_id del store autorizado
        y se verifica sha256(content) == citation.content_hash (cadena de
        identidad con el packet); mismatch → la cita NO se admite (fail-closed,
        la identidad del insumo no es verificable).
        """
        loader = self.chunk_content_loader
        if loader is None:
            return None
        try:
            chunk = loader(citation.chunk_id)
        except Exception:
            logger.warning(
                "Fallo al materializar chunk '%s' (cita %s); cita no admisible.",
                citation.chunk_id, citation.citation_id,
            )
            return None
        content = getattr(chunk, "content", None)
        if not isinstance(content, str) or not content.strip():
            return None
        if hashlib.sha256(content.encode("utf-8")).hexdigest() != citation.content_hash:
            logger.warning(
                "Identidad de chunk '%s' no verificable (hash mismatch) para cita %s; cita no admisible.",
                citation.chunk_id, citation.citation_id,
            )
            return None
        stripped = content.strip()
        return {
            "citation_id": citation.citation_id,
            "id": citation.chunk_id,
            "chunk_id": citation.chunk_id,
            "document_id": citation.document_id,
            "source_id": citation.source_id,
            "source_title": citation.source_title,
            "author": getattr(citation, "author", None) or "",
            "page_start": getattr(citation, "page_start", None),
            "page_end": getattr(citation, "page_end", None),
            # Provenance de la fuente (CHECK_SOURCE_PROVENANCE exige
            # trust_level='canonical'); pass-through del CitationRecord del
            # packet, jamás fabricado aquí.
            "trust_level": getattr(citation, "trust_level", None) or "unverified",
            # El adapter verifica sha256(content.strip()) contra content_hash:
            # se entrega el hash de la forma EXACTA pasada.
            "content": stripped,
            "original_content_hash": citation.content_hash,
            "content_hash": hashlib.sha256(stripped.encode("utf-8")).hexdigest(),
        }

    @staticmethod
    def _bind_answer_citations(answer: str, evidence: EvidenceResult) -> Tuple[CitationRecord, ...]:
        tags = dict.fromkeys(
            tag for claim in ClaimExtractor().extract_claims(answer) for tag in claim.cited_tags
        )
        bound = []
        for tag in tags:
            records = [c for c in evidence.citations if c.citation_id == tag]
            chunks = [c for c in evidence.chunks if isinstance(c, dict) and c.get("citation_id") == tag]
            if len(records) != 1 or len(chunks) != 1:
                raise ValueError("Citation binding is missing or ambiguous")
            record, chunk = records[0], chunks[0]
            content = chunk.get("content")
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Citation has no materialized evidence")
            if any(
                chunk.get(field) != getattr(record, field)
                for field in ("chunk_id", "document_id", "source_id", "source_title", "page_start", "page_end", "trust_level")
            ) or (
                chunk.get("original_content_hash", chunk.get("content_hash")) != record.content_hash
                or chunk.get("content_hash") != hashlib.sha256(content.encode("utf-8")).hexdigest()
            ):
                raise ValueError("Citation identity differs from audited evidence")
            bound.append(record)
        return tuple(bound)

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
        Cadena de evidencia para el diálogo socrático.
        1. ConceptPacket
        2. Notebook Sources
        3. Authorized Bridges
        SIN POOL GLOBAL: si no hay evidencia en estos 3 niveles, se retorna NONE.

        Critically: a notebook/bridge being discoverable is not evidence by itself.
        We only admit evidence when it carries a real content payload and valid
        provenance; otherwise we fail closed and abstain.
        """
        # Nivel 1: ConceptPacket cargado en el episodio
        if concept_packet is not None and concept_packet.citations:
            valid_citations = []
            for c in concept_packet.citations:
                if getattr(c, "content_hash", None) and getattr(c, "content_hash") != "0" * 64:
                    valid_citations.append(c)
            if valid_citations:
                if self.chunk_content_loader is not None:
                    # M1-02: cada cita se materializa y verifica por identidad;
                    # una cita sin contenido o con hash mismatch se excluye
                    # (fail-closed) y el gate min_evidence decide la abstención.
                    materialized = [
                        validated
                        for validated in (
                            self._load_verified_chunk(c) for c in valid_citations
                        )
                        if validated is not None
                    ]
                else:
                    # Ruta legacy (tests / wiring sin loader): identidades
                    # nominales sin contenido materializado.
                    materialized = [
                        getattr(c, "text_snippet", c.citation_id)
                        for c in valid_citations
                    ]
                if materialized:
                    evidence_result = EvidenceResult(
                        chunks=materialized,
                        citations=valid_citations,
                        level="CONCEPT_PACKET",
                    )
                    # Contexto de auditoría para generation_adapter (getattr).
                    evidence_result.query = "dialogue_turn"
                    evidence_result.notebook_id = notebook_id
                    return evidence_result

        # Nivel 2: Fuentes del notebook
        from study_engine.federation.notebook_registry import NotebookRegistry
        reg = NotebookRegistry()
        nb = reg.get_notebook(notebook_id)
        if nb and nb.sources:
            return EvidenceResult(chunks=[], citations=[], level="NONE")

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
                        if not b.get("enabled", True) or b.get("ttl_seconds", 0) is not None and b.get("ttl_seconds", 0) <= 0:
                            return EvidenceResult(chunks=[], citations=[], level="NONE")
                        return EvidenceResult(chunks=[], citations=[], level="NONE")
                except Exception:
                    pass

        # Si no hay evidencia suficiente en niveles 1-3 y no se permite pool global:
        return EvidenceResult(chunks=[], citations=[], level="NONE")

    _FIELD_ROLL: Tuple[str, ...] = (
        "core_concept",
        "mental_model",
        "reasoning_guidance",
        "formalization",
        "implementation_guidance",
    )

    @staticmethod
    def _field_sequence(packet: Optional[ConceptPacket]) -> Tuple[str, ...]:
        if packet is None:
            return ()
        return tuple(
            n for n in DialogueEngine._FIELD_ROLL
            if (getattr(packet, n, None) or "").strip()
        )

    @staticmethod
    def _first_sentence(text: str, max_chars: int = 160) -> str:
        s = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0].strip()
        if len(s) > max_chars:
            s = s[:max_chars].rstrip() + "…"
        return s

    # M1-03 §3: marcadores de posible error conceptual en el turno del
    # estudiante. La detección es lexical y conservadora: TALOS no afirma la
    # autoridad sobre el estado del estudiante (AGENTS.md §19); solo presenta
    # el error documentado del packet (pitfalls, verbatim) junto al claim
    # aprobado e invita a contrastar. La señal de comprensión queda UNKNOWN
    # (no se acredita comprensión por generación).
    _MISCONCEPTION_MARKERS: Tuple[str, ...] = (
        "no es cierto",
        "está mal",
        "incorrecto",
        "al revés",
        "no tiene sentido",
        "no debería",
        "no avanza",
        "no guarda",
        "no usa",
        "no se puede",
        "no es así",
        "no es así como",
        "no funciona así",
        "mentira",
        "me contradice",
    )

    async def _generate_response(
        self,
        intent: ValidatedIntent,
        evidence: EvidenceResult,
        concept_packet: Optional[ConceptPacket],
        dialogue_state: DialogueState,
        student_message: str,
    ) -> LLMDialogueOutput:
        """Genera propuesta dialógica y pregunta socrática fundada en evidencia.

        M1-02 (fundación de la respuesta del turno): el cuerpo factual del
        turno proviene EXCLUSIVAMENTE del ConceptPacket ya APROBADO por S4.4
        (continuidad: no se re-genera ni re-audita contenido ya verificado;
        los pares (premisa, hipótesis) son byte-idénticos a los del concepto
        y reutilizan el veredicto por el cache idempotente). El formato de
        citas es el canónico del pipeline: tag leading `[E#] oración` —
        el ClaimExtractor exige el tag ADELANTADO para asociarlo al claim;
        un tag trailing deja el claim sin cita y CHECK_FACTUAL_GROUNDING
        falla cerrado (hallazgo live 2026-10-20: REJECTED_UNSUPPORTED
        con templates de tag trailing y texto no fundado).

        M1-03 §3 (pregunta auténtica por turno): la pregunta socrática se
        compone determinísticamente desde el contenido del packet aprobado
        (rotación de campos disponibles por número de turno: core_concept →
        mental_model → reasoning_guidance → formalization → implementation),
        citando el pasaje verbatim. Nada de variedad artificial: turnos
        distintos citan pasajes distintos del mismo packet auditado.
        Cuando el mensaje del estudiante contrasta con el contenido (marcador
        lexical de posible error conceptual), el cuerpo incluye los pitfalls
        documentados del packet (verbatim, tag-leading) y la pregunta pide
        identificar la discrepancia — corrección fundada, sin re-auditar
        contenido ya aprobado.
        """
        intent_type = intent.proposed_intent.upper()
        body = concept_packet.core_concept if concept_packet is not None else ""
        reformulation_field = None
        if intent_type == "EXAMPLE_REQUEST" and concept_packet is not None:
            mental_model = concept_packet.mental_model or ""
            if re.search(r"\[E[0-9]+\]", mental_model):
                body = f"{body} {mental_model}".strip()
        elif intent_type == "REFORMULATION" and concept_packet is not None:
            guidance = concept_packet.reasoning_guidance or ""
            mm = concept_packet.mental_model or ""
            m = re.search(r"\[E[0-9]+\]", guidance)
            mm_tagged = re.search(r"\[E[0-9]+\]", mm)
            try:
                _turn = int(getattr(dialogue_state, "turn_count", 0) or 0)
            except (TypeError, ValueError):
                _turn = 0
            if m:
                reformulation_field = "reasoning_guidance"
                body = guidance if _turn == 0 else f"{body} {guidance}".strip()
            elif mm_tagged:
                # PED-F2: change representation on the first request, not one turn later.
                reformulation_field = "mental_model"
                body = mm if _turn == 0 else f"{body} {mm}".strip()

        lowered = " ".join(student_message.lower().split())
        possible_misconception = any(
            mk in lowered for mk in self._MISCONCEPTION_MARKERS
        )
        if possible_misconception and concept_packet is not None:
            tagged_pitfalls = [
                p.strip()
                for p in concept_packet.pitfalls
                if re.match(r"^\[E[0-9]+\]", p.strip())
            ]
            if tagged_pitfalls:
                body = " ".join(tagged_pitfalls[:2])
            core = concept_packet.core_concept or ""
            if core and core not in body:
                body = f"{body} {core}".strip()

        # Pregunta socrática determinista, derivada del packet auditado y del
        # punto del diálogo (rotación de campos por turno disponible).
        fields = self._field_sequence(concept_packet)
        turn_idx = 0
        try:
            turn_idx = int(getattr(dialogue_state, "turn_count", 0) or 0)
        except (TypeError, ValueError):
            turn_idx = 0
        if possible_misconception and concept_packet is not None:
            core = (concept_packet.core_concept or "").strip()
            stance = self._first_sentence(core, 200) if core else ""
            socratic_q = (
                f"La evidencia citada sostiene: “{stance}” — "
                "¿qué parte de tu razonamiento difiere de esa formulación?"
            )
        elif fields and concept_packet is not None:
            field_name = fields[turn_idx % len(fields)]
            field_text = (getattr(concept_packet, field_name, "") or "").strip()
            _FIELD_LABELS = {
                "core_concept": "el concepto central",
                "mental_model": "el modelo mental",
                "reasoning_guidance": "el procedimiento paso a paso",
                "formalization": "la formalización",
                "implementation_guidance": "la implementación práctica",
            }
            label = _FIELD_LABELS.get(field_name, "la evidencia")
            snippet = self._first_sentence(field_text, 200)
            probe = (
                "¿Qué caso concreto ilustra eso?"
                if turn_idx % 3 == 0
                else "¿Qué límite o riesgo revela eso?"
                if turn_idx % 3 == 1
                else "¿Cómo lo aplicarías en la práctica?"
            )
            socratic_q = (
                f"De la evidencia citada ({label}): “{snippet}” {probe}"
            )
        else:
            socratic_q = ""

        if intent_type == "EXAMPLE_REQUEST":
            socratic_q = socratic_q or (
                "¿En qué caso preferirías la alternativa mencionada por la evidencia?"
            )

        rationale = "Explora comprensión sobre el pasaje verbatim del packet aprobado."
        if possible_misconception:
            rationale = "Turno derivado del packet aprobado; posible.error conceptual"
        elif intent_type == "REFORMULATION":
            selection = f"campo={reformulation_field}" if reformulation_field else "sin alternativa citada disponible"
            rationale = f"REFORMULATION solicitada; {selection}; señal consultiva, comprensión UNKNOWN."
        return LLMDialogueOutput(answer=body, socratic_question=socratic_q, rationale=rationale)

    def _execute_s44_audit(self, answer: str, evidence: EvidenceResult) -> str:
        """Ejecuta o consulta el veredicto del ForensicAuditor S4.4 con fail-closed (Fix 0.2, E3, E4)."""
        def validated_verdict(result: Any, attribute: str) -> str:
            verdict = getattr(result, attribute, None)
            verdict = getattr(verdict, "value", verdict)
            valid_verdicts = {candidate.value for candidate in AuditVerdict}
            valid_verdicts.update({"PARTIAL", "REJECTED"})
            if not isinstance(verdict, str) or verdict not in valid_verdicts:
                return "REJECTED_AUDIT_ERROR"
            return verdict

        if self.forensic_auditor is None:
            return "REJECTED_AUDIT_ERROR"
        
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
                attribute = "overall_verdict" if hasattr(res, "overall_verdict") else "verdict"
                return validated_verdict(res, attribute)
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
                return validated_verdict(res, "verdict")
            except (TimeoutError, ConnectionError):
                logger.warning("Timeout o error de conexión en auditoría socrática legacy.")
                return "DEFERRED_RETRY"
            except Exception:
                return "REJECTED_AUDIT_ERROR"

        return "REJECTED_AUDIT_ERROR"

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

        try:
            answer_citations = self._bind_answer_citations(llm_output.answer, evidence)
        except ValueError:
            return DialogueResponse(
                status="ABSTAINED",
                abstention_reason="Las referencias de la respuesta no tienen un binding verificable.",
                audit_verdict=AuditVerdict.REJECTED_INPUT_MISMATCH.value,
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
            citations=answer_citations,
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
