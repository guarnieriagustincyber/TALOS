"""Fast-Path Conversational Service (Fase 1: Sub-100ms Gatekeeping).

Interprets pure conversational queries (greetings, courtesy, navigation, meta-questions)
and generates empathetic, dynamic, context-aware responses via Micro-LLM or dynamic
deterministic contextual fallback without executing the heavy 3-phase epistemic pipeline.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
import logging
import random
import re
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from study_engine.contracts.generation import GenerationParameters
from study_engine.generation.prompts import (
    PromptBundle,
    PromptMessage,
    PromptRole,
    compute_canonical_prompt_hash,
)
from study_engine.tutor.local_orchestrator import ConversationalOutputGuard
from study_engine.tutor.policy_validator import RouteKind

logger = logging.getLogger(__name__)


# Regex patterns for pure conversational queries (matched against punctuation-stripped query)
_GREETING_PATTERNS = [
    re.compile(
        r"^\s*(?:hola|buenas|buen\s+d[ií]a|buenos\s+d[ií]as|buenas\s+tardes|buenas\s+noches|"
        r"hey|saludos|qu[eé]\s+tal|c[oó]mo\s+est[aá]s|c[oó]mo\s+va|c[oó]mo\s+te\s+va)"
        r"(?:\s+(?:kasiu|talos|tutor))?\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(?:chau|adi[oó]s|hasta\s+luego|hasta\s+la\s+pr[oó]xima|nos\s+vemos)\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(?:gracias|muchas\s+gracias|mil\s+gracias|agradecido|te\s+agradezco|"
        r"genial\s+gracias|perfecto\s+gracias)\s*$",
        re.IGNORECASE,
    ),
]

_NAVIGATION_PATTERNS = [
    re.compile(
        r"^\s*(?:por\s+d[oó]nde\s+(?:empezamos|arrancamos|seguimos)|qu[eé]\s+tema\s+sigue|"
        r"en\s+qu[eé]\s+tema\s+quedamos|cu[aá]l\s+es\s+el\s+(?:pr[oó]ximo|siguiente)\s+(?:paso|nodo|tema)|"
        r"siguiente\s+paso|pr[oó]ximo\s+nodo|qu[eé]\s+vemos\s+hoy|c[oó]mo\s+sigo)\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(?:roadmap|mostrame\s+el\s+roadmap|d[oó]nde\s+estoy\s+parado|cu[aá]l\s+es\s+mi\s+progreso)\s*$",
        re.IGNORECASE,
    ),
]

_META_PATTERNS = [
    re.compile(
        r"^\s*(?:qui[eé]n\s+(?:sos|eres|te\s+cre[oó])|c[oó]mo\s+funcionas|"
        r"qu[eé]\s+(?:sos|eres|haces|pod[eé]s\s+hacer)|para\s+qu[eé]\s+serv[ií]s)\s*$",
        re.IGNORECASE,
    ),
]

_FOLLOW_UP_AFFIRMATION_PATTERNS = [
    re.compile(
        r"^\s*(?:s[ií]|sip|se|yes|yeah|sep|claro|clar[ií]simo|obvio|posta|tal\s+cual|"
        r"dale|de\s+una|joya|buen[ií]simo|de\s+diez|re|totalmente|de\s+acuerdo|va|"
        r"ok|okay|okei|bueno|bien|dale\s+dale|dale\s+con\s+eso|vamos|sigamos|"
        r"contin[uú]a|continuemos|avancemos|next|perfecto|entendido|"
        r"dale\s+(?:vamos|sigamos|avancemos|con\s+eso|buen[ií]simo)|si\s+dale|"
        r"si\s+por\s+favor|dale\s+hacemos\s+eso)\s*$",
        re.IGNORECASE,
    ),
]

_FOLLOW_UP_NEGATION_PATTERNS = [
    re.compile(
        r"^\s*(?:no|nop|nope|nel|nanan?|paso|para\s+nada|por\s+ahora\s+no|"
        r"despu[eé]s|deja|dejalo|dejemos\s+ac[aá]|terminamos\s+por\s+hoy|"
        r"hasta\s+ac[aá]\s+por\s+hoy|no\s+gracias|hoy\s+no|otro\s+d[ií]a)\s*$",
        re.IGNORECASE,
    ),
]

# Strict exclusion: if any of these technical keywords or inquiry structures appear,
# the query is NOT purely conversational and must proceed to the epistemic pipeline.
# NOTE: 'ejercicio', 'practicar' and 'red' deliberately excluded — they appear in
# conversational intents like "dale un ejercicio" or "quiero practicar" and should
# not force a full epistemic pipeline run.
_TECHNICAL_EXCLUSION_PATTERN = re.compile(
    r"\b(?:"
    r"qu[eé]\s+es|c[oó]mo\s+se\s+define|por\s+qu[eé]|definici[oó]n|ejemplo"
    r"|puntero|pointer|stack|heap|memoria|proceso|hilo|thread|mutex|buffer"
    r"|overflow|cpu|registro|instrucci[oó]n|kernel|sistema\s+operativo"
    r"|archivo|socket|c[oó]digo|funci[oó]n|variable|algoritmo"
    r")\b",
    re.IGNORECASE,
)


class FastPathConversationalService:
    """Detects and generates sub-100ms conversational responses."""

    def __init__(self) -> None:
        self.output_guard = ConversationalOutputGuard()

    @classmethod
    def is_affirmation(cls, query: str) -> bool:
        """Check if query is an affirmative follow-up."""
        clean_q = (query or "").strip("¿¡!?. \t\n\r")
        return any(pat.match(clean_q) for pat in _FOLLOW_UP_AFFIRMATION_PATTERNS)

    @classmethod
    def is_negation(cls, query: str) -> bool:
        """Check if query is a negative follow-up / pause."""
        clean_q = (query or "").strip("¿¡!?. \t\n\r")
        return any(pat.match(clean_q) for pat in _FOLLOW_UP_NEGATION_PATTERNS)

    @classmethod
    def detect_conversational_route(cls, query: str) -> Tuple[bool, Optional[RouteKind]]:
        """Determine whether query is pure conversational and return corresponding RouteKind."""
        q = (query or "").strip()
        if not q:
            return True, RouteKind.GREETING

        # Strip Spanish inverted and trailing punctuation (¿ ¡ ! ? .) for robust canonical matching
        clean_q = q.strip("¿¡!?. \t\n\r")
        if not clean_q:
            return True, RouteKind.GREETING

        # If any technical keywords or explanations are requested, disqualify immediately
        if _TECHNICAL_EXCLUSION_PATTERN.search(clean_q):
            return False, None

        # Check follow-ups first (affirmations / negations / short responses < 1ms)
        for pat in _FOLLOW_UP_AFFIRMATION_PATTERNS:
            if pat.match(clean_q):
                return True, RouteKind.FOLLOW_UP

        for pat in _FOLLOW_UP_NEGATION_PATTERNS:
            if pat.match(clean_q):
                return True, RouteKind.FOLLOW_UP

        # Check pure greetings and courtesy
        for pat in _GREETING_PATTERNS:
            if pat.match(clean_q):
                return True, RouteKind.GREETING

        # Check navigation / progress queries
        for pat in _NAVIGATION_PATTERNS:
            if pat.match(clean_q):
                return True, RouteKind.NAVIGATION

        # Check meta / system questions
        for pat in _META_PATTERNS:
            if pat.match(clean_q):
                return True, RouteKind.CLARIFICATION

        return False, None

    def extract_student_context(
        self,
        container: Any,
        target_notebook_id: str,
    ) -> Dict[str, str]:
        """Extract lightweight context (notebook name, active KC) in < 1ms."""
        notebook_title = target_notebook_id
        last_kc_title = ""

        try:
            store = getattr(container, "knowledge_store", None)
            if store and hasattr(store, "get_notebook"):
                nb = store.get_notebook(target_notebook_id)
                if nb and getattr(nb, "name", None):
                    notebook_title = nb.name
        except Exception as e:
            logger.debug("FastPath context: unable to fetch notebook title: %s", e)

        try:
            catalog = getattr(container.pedagogical_orchestrator, "_kc_catalog", {})
            nb_cat = catalog.get(target_notebook_id, {})
            kcs = nb_cat.get("kcs", [])
            if kcs:
                last_kc_title = kcs[0].get("title", "")
        except Exception as e:
            logger.debug("FastPath context: unable to fetch active KC: %s", e)

        pedagogical_directive = ""
        misconceptions = []
        try:
            tracker = getattr(container, "pedagogical_memory_tracker", None)
            if tracker is None and hasattr(container, "student_storage") and container.student_storage:
                from study_engine.student.pedagogical_memory import PedagogicalMemoryTracker
                tracker = PedagogicalMemoryTracker(container.student_storage)
            if tracker:
                pedagogical_directive = tracker.format_tutor_directive(limit=3)
                recent_misc = tracker.storage.get_pedagogical_memories(
                    student_id="default_student",
                    category="misconception",
                    limit=2,
                )
                misconceptions = [m.get("insight", "") for m in recent_misc if m.get("insight")]
        except Exception as e:
            logger.debug("FastPath context: unable to fetch pedagogical memories: %s", e)

        session_briefing = ""
        try:
            gen = getattr(container, "session_briefing_generator", None)
            if gen and hasattr(gen, "generate_briefing"):
                session_briefing = gen.generate_briefing(
                    student_id="default_student",
                    notebook_id=target_notebook_id,
                    student_name="Agustín",
                )
        except Exception as e:
            logger.debug("FastPath context: unable to fetch session briefing: %s", e)

        return {
            "student_name": "Agustín",
            "notebook_title": notebook_title,
            "last_kc_title": last_kc_title,
            "pedagogical_directive": pedagogical_directive,
            "misconceptions": ", ".join(misconceptions),
            "session_briefing": session_briefing,
        }

    async def generate_response(
        self,
        query: str,
        route_kind: RouteKind,
        context: Dict[str, str],
        llm_backend: Optional[Any] = None,
    ) -> str:
        """Generate response via Micro-LLM or dynamic contextual fallback."""
        # 1. Try Micro-LLM generation if backend is available and not offline oracle
        from study_engine.llm.offline_oracle import OfflinePedagogicalBackend

        is_offline = (
            llm_backend is None
            or isinstance(llm_backend, OfflinePedagogicalBackend)
            or getattr(llm_backend, "__class__", None).__name__ == "ReplayMockBackend"
        )

        if not is_offline and hasattr(llm_backend, "complete"):
            try:
                text = await asyncio.wait_for(
                    self._call_micro_llm(query, route_kind, context, llm_backend),
                    timeout=1.5,
                )
                if text and self.output_guard.is_safe(text, route_kind):
                    clean = self.output_guard.sanitize_render(text)
                    if clean:
                        return clean
            except Exception as exc:
                logger.info("FastPath Micro-LLM call bypassed or timed out: %s", exc)

        # 2. Dynamic contextual fallback (deterministic, < 1ms)
        return self._generate_dynamic_fallback(route_kind, context, query)

    async def _call_micro_llm(
        self,
        query: str,
        route_kind: RouteKind,
        context: Dict[str, str],
        llm_backend: Any,
    ) -> str:
        """Execute minimal prompt completion via active LLM backend."""
        student = context.get("student_name", "Agustín")
        nb_title = context.get("notebook_title", "el cuaderno actual")
        last_kc = context.get("last_kc_title", "")
        ped_notes = context.get("pedagogical_directive", "")

        kc_context = f", último concepto visto: '{last_kc}'" if last_kc else ""
        ped_block = f"\n{ped_notes}\n" if ped_notes else ""

        if route_kind == RouteKind.FOLLOW_UP:
            system_prompt = (
                f"Sos KASIU, el tutor pedagógico inteligente y empático de {student} en TALOS.\n"
                f"El estudiante acaba de dar una respuesta breve de confirmación o seguimiento ('{query}').\n"
                f"Tu objetivo es proponer inmediatamente el siguiente paso concreto de estudio en '{nb_title}' "
                "de forma motivadora, cálida y en español rioplatense (máximo 2 oraciones).\n"
                f"{ped_block}"
                "REGLAS CRÍTICAS:\n"
                "- NO formules explicaciones técnicas largas ni código en este turno.\n"
                "- Proponé una acción o pregunta desafiante para continuar el estudio."
            )
        else:
            system_prompt = (
                f"Sos KASIU, el tutor pedagógico inteligente y empático de {student} en TALOS.\n"
                "Tu tarea en este turno es responder a su saludo o interacción conversacional de forma cálida, "
                "breve, natural y motivadora (máximo 2 oraciones) en español rioplatense.\n"
                f"{ped_block}"
                "REGLAS CRÍTICAS:\n"
                "- NO formules explicaciones técnicas ni código en este turno.\n"
                "- Sé fluido y empático, invitándolo a continuar con su estudio."
            )

        user_content = (
            f"Contexto: Cuaderno '{nb_title}'{kc_context}.\n"
            f"Mensaje del estudiante: \"{query}\""
        )

        messages = (PromptMessage(role=PromptRole.USER, content=user_content),)
        params = GenerationParameters(
            temperature=0.7,
            max_output_tokens=85,
        )
        p_hash = compute_canonical_prompt_hash(system_prompt, messages, params)
        bundle = PromptBundle(
            system_prompt=system_prompt,
            messages=messages,
            parameters=params,
            prompt_hash=p_hash,
        )

        # Execute completion in threadpool to keep event loop free
        def _sync_complete() -> str:
            completion = llm_backend.complete(bundle)
            return getattr(completion, "text", "").strip()

        return await asyncio.to_thread(_sync_complete)

    def _generate_dynamic_fallback(
        self,
        route_kind: RouteKind,
        context: Dict[str, str],
        query: str = "",
    ) -> str:
        """Construct warm, diverse, context-aware message deterministically."""
        student = context.get("student_name", "Agustín")
        nb = context.get("notebook_title", "tu cuaderno")
        kc = context.get("last_kc_title", "")

        now_hour = datetime.now().hour
        if 5 <= now_hour < 12:
            time_greeting = "¡Buen día"
        elif 12 <= now_hour < 20:
            time_greeting = "¡Buenas tardes"
        else:
            time_greeting = "¡Buenas noches"

        if route_kind == RouteKind.GREETING:
            briefing = context.get("session_briefing", "")
            if briefing and "la última vez estuviste" in briefing.lower():
                return f"{time_greeting}! {briefing}"

            greetings = [
                f"{time_greeting}, {student}! ¿Cómo estás? Estoy listo para continuar trabajando con {nb}. ¿Por dónde querés arrancar?",
                f"¡Hola {student}! Qué bueno verte por acá. ¿Seguimos avanzando con los conceptos de {nb} o tenés alguna duda puntual?",
                f"{time_greeting}, {student}! Soy KASIU. Todo listo en el cuaderno '{nb}'. ¿Le damos una vuelta a la teoría o preferís practicar?",
            ]
            if kc:
                greetings.append(
                    f"¡Hola {student}! En la sesión anterior estuvimos viendo '{kc}'. ¿Querés que continuemos desde ahí o vemos un tema nuevo?"
                )
            return random.choice(greetings)

        elif route_kind == RouteKind.FOLLOW_UP:
            if self.is_negation(query):
                if kc:
                    return (
                        f"¡Entendido, {student}, sin apuro! Dejamos en pausa '{kc}'. "
                        f"¿Preferís que revisemos otro tema de '{nb}' o tenés alguna duda conceptual que quieras ver?"
                    )
                return (
                    f"¡De acuerdo, {student}! ¿Preferís que veamos otro tema de '{nb}' o hacemos una pausa?"
                )
            else:
                affirmations = [
                    f"¡De una, {student}! Todo listo en '{nb}'. ¿Le damos una vuelta a la teoría o preferís que te plantee un ejercicio?",
                    f"¡Genial! Sigamos adelante. ¿Por dónde querés arrancar en '{nb}'?",
                    f"¡Buenísimo! ¿Querés que pongamos a prueba los conceptos con un desafío rápido o repasamos la bibliografía?",
                ]
                if kc:
                    affirmations.append(
                        f"¡De una, {student}! Estábamos con '{kc}'. ¿Querés que te plantee un ejercicio puntual para afianzarlo o vemos el siguiente tema?"
                    )
                    affirmations.append(
                        f"¡Excelente! Sobre '{kc}': ¿te propongo un desafío rápido de autoevaluación o preferís un ejemplo práctico?"
                    )
                return random.choice(affirmations)

        elif route_kind == RouteKind.NAVIGATION:
            if kc:
                return (
                    f"Actualmente estás ubicado en el cuaderno '{nb}'. "
                    f"El último concepto en tu ruta de aprendizaje fue '{kc}'. "
                    "¿Querés que profundicemos en ese tema o avanzamos al siguiente desafío del roadmap?"
                )
            return (
                f"Estás en el cuaderno '{nb}'. "
                "Podés pedirme repasar los conceptos fundamentales, ver un ejemplo práctico o resolver un ejercicio de autoevaluación."
            )

        elif route_kind == RouteKind.CLARIFICATION:
            return (
                "Soy KASIU, tu tutor pedagógico estructurado en TALOS. "
                "Mi objetivo es guiarte con el método socrático y contrastar cada concepto con la bibliografía oficial de la cátedra. "
                f"¿En qué puedo ayudarte hoy dentro de '{nb}'?"
            )

        return (
            f"¡Hola {student}! ¿En qué te puedo acompañar hoy en tu sesión de estudio?"
        )

    async def stream_fastpath_events(
        self,
        full_text: str,
        route_kind: RouteKind,
    ) -> AsyncGenerator[str, None]:
        """Stream SSE events for conversational fast-path."""
        # 1. Evidence Manifest (conversational = no citations, not abstained)
        manifest = {
            "event_type": "evidence_manifest",
            "payload": {
                "citations": [],
                "facet_coverage": {},
                "abstained": False,
                "abstention_reason": None,
            },
        }
        yield f"data: {json.dumps(manifest)}\n\n"

        # 2. Phase Start
        start_event = {
            "event_type": "phase_start",
            "payload": {
                "phase": "conversational",
                "max_tokens": 120,
                "code_allowed": False,
            },
        }
        yield f"data: {json.dumps(start_event)}\n\n"

        # 3. Stream Words / Tokens
        words = full_text.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            tok_event = {
                "event_type": "phase_token",
                "payload": {
                    "phase": "conversational",
                    "token": token,
                },
            }
            yield f"data: {json.dumps(tok_event)}\n\n"
            await asyncio.sleep(0.008)

        # 4. Phase Complete
        comp_event = {
            "event_type": "phase_complete",
            "payload": {
                "completed_phase": "conversational",
                "next_phases": ["conceptual"],
                "decision": {
                    "action": "conversational_reply",
                    "route_kind": route_kind.value,
                    "message": full_text,
                },
            },
        }
        yield f"data: {json.dumps(comp_event)}\n\n"
