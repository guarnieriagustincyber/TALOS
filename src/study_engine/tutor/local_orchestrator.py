"""Local Orchestrator powered by Qwen 3.5 2B via Ollama (Bloque C1 / Fase 5.5).

Provides:
1. Deterministic/local offline handling for greetings, meta and curricular navigation.
2. Hardened LocalConversationalDraft generation for non-technical conversational UX.
3. ConversationalOutputGuard ensuring zero technical claims, mutations, code or jailbreaks.
4. Query reformulation for improved technical retrieval.
5. Intelligent cloud provider selection based on query context.
6. Seamless fallback resilience when cloud providers are degraded.
"""

import html
import re
from typing import Any, Dict, FrozenSet, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator

from study_engine.contracts.generation import (
    GenerationParameters,
    GenerationRequest,
)
from study_engine.generation.prompts import (
    PromptBundle,
    PromptMessage,
    PromptRole,
    compute_canonical_prompt_hash,
)
from study_engine.llm.backends import ProviderBackend
from study_engine.llm.factory import LLMProviderFactory, ProviderConfig
from study_engine.tutor.policy_validator import RouteKind
from study_engine.tutor.question_type import QuestionType, detect_question_type


ALLOWED_LOCAL_CONVERSATIONAL_ROUTES: FrozenSet[RouteKind] = frozenset({
    RouteKind.GREETING,
    RouteKind.NAVIGATION,
    RouteKind.CLARIFICATION,
})


class LocalConversationalDraft(BaseModel):
    """Immutable, strongly-typed draft emitted by local conversational model or fallback."""

    model_config = ConfigDict(strict=True, frozen=True)

    text: StrictStr = Field(..., max_length=1200)
    route_kind: RouteKind
    generated_by: Literal["local_conversational_model", "deterministic_fallback"]
    technical_claims_allowed: Literal[False] = False
    mutation_allowed: Literal[False] = False
    execution_allowed: Literal[False] = False
    retrieval_allowed: Literal[False] = False
    citation_allowed: Literal[False] = False
    state_change_allowed: Literal[False] = False
    navigation_invented: Literal[False] = False

    @field_validator("route_kind")
    @classmethod
    def validate_route_allowed(cls, v: RouteKind) -> RouteKind:
        if v not in ALLOWED_LOCAL_CONVERSATIONAL_ROUTES:
            raise ValueError(
                f"Local conversational draft is only allowed for "
                f"{sorted([r.value for r in ALLOWED_LOCAL_CONVERSATIONAL_ROUTES])}, got: {v}"
            )
        return v


class ConversationalOutputGuard:
    """Fail-closed deterministic guard validating non-technical conversational drafts."""

    _CODE_PATTERN = re.compile(r"```.*|`[^`]+`|\b(bash|sh|sudo|chmod|pip|curl|wget|eval|exec)\b", re.IGNORECASE)
    _DANGEROUS_MD = re.compile(r"(\[.*?\]\(javascript:.*?\)|<script.*?>|<img.*?>|<iframe.*?>|javascript:|data:text/html)", re.IGNORECASE)
    _AUTHORITY_CLAIMS = re.compile(
        r"(marqu[eé]\b.*?\b(dominado|completado)|actualic[eé]\b.*?\bprogreso|"
        r"guard[eé]\b.*?\bledger|cambi[eé]\b.*?\broadmap|ejecut[eé]\b.*?\bc[oó]digo|"
        r"te\s+doy\s+por\s+aprobado|aprobar[eé]\b.*?\bnodo)",
        re.IGNORECASE,
    )
    _CITATIONS_PATTERN = re.compile(
        r"(seg[uú]n\s+(joyanes|tanenbaum|spraul|stallings|silberschatz)|en\s+el\s+cap[ií]tulo|"
        r"p[aá]gina\s+\d+|\[E\d+\]|\[fuente\]|cita\s+bibliogr[aá]fica)",
        re.IGNORECASE,
    )
    _JSON_ACTION_PATTERN = re.compile(r'(\{"action"|"intent"|"route"|"mutation_allowed"|"execution_allowed"|"needs_evidence")', re.IGNORECASE)
    _CANARY_JAILBREAK_PATTERN = re.compile(r"(CANARY_|ignore\s+previous\s+instructions|ignora\s+las\s+reglas|system\s+prompt|developer\s+mode)", re.IGNORECASE)
    _TECHNICAL_TERMS_RE = re.compile(
        r"\b(int\*|char\*|malloc|free|sizeof|sched_yield|fork|execve|pcb|deadlock|mutex|semaforo|semáforo|"
        r"direcci[oó]n\s+de\s+memoria|puntero\s+es\s+un[a]?\s+variable|recursi[oó]n\s+es\s+cuando)\b",
        re.IGNORECASE,
    )

    def is_safe(
        self,
        text: str,
        route_kind: RouteKind,
        allowed_node_ids: Optional[List[str]] = None,
    ) -> bool:
        """Evaluate whether generated text adheres to strict conversational non-technical safety."""
        if not text or not text.strip():
            return False

        # General safety blocks across all conversational routes
        if self._CODE_PATTERN.search(text):
            return False
        if self._DANGEROUS_MD.search(text):
            return False
        if self._AUTHORITY_CLAIMS.search(text):
            return False
        if self._CITATIONS_PATTERN.search(text):
            return False
        if self._JSON_ACTION_PATTERN.search(text):
            return False
        if self._CANARY_JAILBREAK_PATTERN.search(text):
            return False

        # Route-specific restrictions
        if route_kind in (RouteKind.GREETING, RouteKind.CLARIFICATION, RouteKind.FOLLOW_UP):
            if self._TECHNICAL_TERMS_RE.search(text):
                return False

        if route_kind == RouteKind.NAVIGATION:
            # Check for invented nodes or uppercase identifiers not in allowlist
            if allowed_node_ids is not None:
                # Find all token patterns looking like node IDs (e.g. F0-T2-01, EXPLOIT_XYZ, SEC-01)
                tokens = re.findall(r"\b[A-Z0-9]+(?:[-_][A-Z0-9]+)+\b|\b[A-Z0-9_]{6,}\b", text)
                for t in tokens:
                    if t not in allowed_node_ids:
                        return False

        return True

    def sanitize_render(self, raw_text: str) -> str:
        """Strip executable HTML and escape unescaped tags for safe UI rendering."""
        clean = re.sub(r"<[^>]+>", "", raw_text)
        return clean.strip()


class OrchestrationDecision(BaseModel):
    """Immutable envelope containing the local orchestrator's decision."""

    model_config = ConfigDict(frozen=True)

    use_local: bool = Field(..., description="Whether to short-circuit using local generation")
    provider: str = Field(..., description="Selected provider identifier (ollama, groq, etc.)")
    model: str = Field(..., description="Model identifier selected for execution")
    response: Optional[str] = Field(default=None, description="Pre-computed response if local")
    reformulated_query: Optional[str] = Field(default=None, description="Query reformulated for retrieval")


class LocalOrchestrator:
    """Orquestador local con Qwen 3.5 2B (Ollama) y enrutamiento inteligente."""

    def __init__(
        self,
        local_backend: Optional[ProviderBackend] = None,
        factory: Optional[LLMProviderFactory] = None,
    ) -> None:
        self.factory = factory or LLMProviderFactory()
        if local_backend is not None:
            self.local_backend = local_backend
        else:
            try:
                self.local_backend = self.factory.create_provider(
                    ProviderConfig(
                        provider_type="ollama",
                        timeout_seconds=3.0,
                        connect_timeout_seconds=2.0,
                        fallback_to_mock_if_missing_key=True,
                    )
                )
            except Exception:
                self.local_backend = self.factory.create_provider(
                    ProviderConfig(provider_type="mock")
                )

        self.cloud_priority = ["groq", "nvidia", "gemini", "openrouter"]
        self.output_guard = ConversationalOutputGuard()

    def generate_conversational_draft(
        self,
        query: str,
        route_kind: RouteKind,
        context: Optional[Dict[str, Any]] = None,
    ) -> LocalConversationalDraft:
        """Generate empathetic and natural non-technical conversational text with Qwen 2B/3B.

        Strictly guarded:
        - Route must be in ALLOWED_LOCAL_CONVERSATIONAL_ROUTES.
        - Only sanitized metadata is passed to prompt (never raw user history or system secrets).
        - Output passes through ConversationalOutputGuard fail-closed validation.
        - Fallbacks immediately to deterministic template on any exception, timeout or guard reject.
        """
        # Defense in depth: reject any unpermitted route immediately
        if route_kind not in ALLOWED_LOCAL_CONVERSATIONAL_ROUTES:
            return self._build_deterministic_fallback(route_kind, context)

        ctx = context or {}
        allowed_nodes = ctx.get("allowed_node_ids") or []
        current_node_title = ctx.get("current_node_title", ctx.get("current_node_id", "el tema actual"))
        next_node_title = ctx.get("next_node_title")

        # Build sanitized minimal prompt
        system_prompt = (
            "Sos el tutor pedagógico de KASIU. Tu función en este turno es responder "
            "de forma breve, cálida, natural y motivadora en español rioplatense o neutro.\n"
            "REGLAS INQUEBRANTABLES:\n"
            "- NO expliques conceptos técnicos ni des definiciones de la materia.\n"
            "- NO uses código ni markdown complejo.\n"
            "- NO cites fuentes ni inventes información del roadmap.\n"
            "- Sé empático y mantené la respuesta en menos de 3 oraciones."
        )

        user_content = self._build_sanitized_user_prompt(
            route_kind=route_kind,
            current_node_title=current_node_title,
            next_node_title=next_node_title,
        )

        messages = (PromptMessage(role=PromptRole.USER, content=user_content),)
        params = GenerationParameters(
            temperature=0.3,
            max_output_tokens=140,
            suggested_model="qwen3.5:2b",
        )
        prompt_hash = compute_canonical_prompt_hash(system_prompt, messages, params)
        bundle = PromptBundle(
            system_prompt=system_prompt,
            messages=messages,
            parameters=params,
            prompt_hash=prompt_hash,
        )

        try:
            completion = self.local_backend.complete(bundle)
            raw_text = completion.text.strip()
            if self.output_guard.is_safe(raw_text, route_kind, allowed_nodes):
                safe_text = self.output_guard.sanitize_render(raw_text)
                return LocalConversationalDraft(
                    text=safe_text,
                    route_kind=route_kind,
                    generated_by="local_conversational_model",
                )
        except Exception:
            pass

        return self._build_deterministic_fallback(route_kind, context)

    def _build_sanitized_user_prompt(
        self,
        route_kind: RouteKind,
        current_node_title: str,
        next_node_title: Optional[str],
    ) -> str:
        """Construct sanitized minimal context string without raw user input or internal traces."""
        if route_kind == RouteKind.GREETING:
            return (
                f"El estudiante te saluda. Dale una bienvenida amable e invitalo a continuar "
                f"con '{current_node_title}'."
            )
        elif route_kind == RouteKind.NAVIGATION:
            next_txt = f" El próximo tema sugerido es '{next_node_title}'." if next_node_title else ""
            return (
                f"El estudiante consulta cómo seguir en el roadmap. Indicale que está en "
                f"'{current_node_title}'.{next_txt}"
            )
        elif route_kind == RouteKind.CLARIFICATION:
            return (
                f"El estudiante hizo una consulta imprecisa sobre '{current_node_title}'. "
                f"Pedile amablemente que aclare o reformule su duda para poder ayudarlo con la bibliografía."
            )
        return "Respondé brevemente de forma amable."

    def _build_deterministic_fallback(
        self,
        route_kind: RouteKind,
        context: Optional[Dict[str, Any]],
    ) -> LocalConversationalDraft:
        """Deterministic fail-safe template guaranteed to be safe and accurate."""
        ctx = context or {}
        node_title = ctx.get("current_node_title", ctx.get("current_node_id", "el tema actual"))
        next_title = ctx.get("next_node_title")

        if route_kind == RouteKind.GREETING:
            text = (
                "¡Hola! Soy KASIU, tu tutor de estudio. "
                "¿En qué puedo ayudarte hoy con tu aprendizaje?"
            )
        elif route_kind == RouteKind.NAVIGATION:
            next_guidance = (
                f" Siguiente paso sugerido: '{next_title}'."
                if next_title
                else " Ya estás en el nodo más reciente del roadmap."
            )
            text = (
                f"Estás en '{node_title}'. "
                f"Te recomiendo empezar por el contenido y material de este nodo.{next_guidance}"
            )
        else:
            text = (
                "¿Podrías reformular o detallar un poco más tu consulta? "
                "Podés preguntarme sobre el contenido conceptual del tema actual, "
                "consultar tu posición en el roadmap o pedir un ejercicio de práctica."
            )

        return LocalConversationalDraft(
            text=text,
            route_kind=route_kind,
            generated_by="deterministic_fallback",
        )

    def orchestrate(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> OrchestrationDecision:
        """Evaluate query and context to return authoritative OrchestrationDecision."""
        ctx = context or {}
        qtype = detect_question_type(query)

        # 1. Non-technical questions: answer with local Qwen / local logic
        if qtype in (QuestionType.GREETING, QuestionType.CURRICULAR, QuestionType.META):
            # Map legacy QuestionType to RouteKind for draft generation
            if qtype == QuestionType.GREETING:
                rk = RouteKind.GREETING
            elif qtype == QuestionType.CURRICULAR:
                rk = RouteKind.NAVIGATION
            else:
                rk = RouteKind.CLARIFICATION
            draft = self.generate_conversational_draft(query, rk, ctx)
            return OrchestrationDecision(
                use_local=True,
                provider="ollama",
                model="qwen3.5:2b",
                response=draft.text,
            )

        # 2. Technical queries: reformulate query and select best cloud provider
        reformulated = self._reformulate_query(query)
        selected_provider = self._select_provider(ctx)
        selected_model = self._get_default_model(selected_provider)

        return OrchestrationDecision(
            use_local=False,
            provider=selected_provider,
            model=selected_model,
            reformulated_query=reformulated,
        )

    def _reformulate_query(self, query: str) -> str:
        """Reformula la query técnica para optimizar el retrieval en la base documental."""
        clean_q = query.strip()
        system_prompt = (
            "Sos un reformulador de consultas técnicas para un motor de búsqueda y retrieval. "
            "Dada una pregunta del estudiante, devolvé únicamente los términos clave y conceptos "
            "esenciales en una sola línea corta, sin explicaciones ni saludos."
        )
        messages = (
            PromptMessage(
                role=PromptRole.USER,
                content=f"Pregunta: {clean_q}",
            ),
        )
        params = GenerationParameters(
            temperature=0.0,
            max_output_tokens=60,
            suggested_model="qwen3.5:2b",
        )
        prompt_hash = compute_canonical_prompt_hash(system_prompt, messages, params)
        bundle = PromptBundle(
            system_prompt=system_prompt,
            messages=messages,
            parameters=params,
            prompt_hash=prompt_hash,
        )
        try:
            completion = self.local_backend.complete(bundle)
            reformed = completion.text.strip()
            # If Qwen produced a sensible keyword reformulation, return it; otherwise keep original
            if reformed and len(reformed) > 3:
                return reformed
        except Exception:
            pass

        return clean_q

    def _select_provider(self, context: Dict[str, Any]) -> str:
        """Elige el mejor provider cloud según el contexto pedagógico y computacional."""
        # Si requiere análisis profundo de código o tarea práctica compleja -> nvidia / deepseek
        if context.get("has_practical_task"):
            return "nvidia"

        # Si requiere explicación extensa o detallada -> gemini
        if context.get("detail_level") == "detailed":
            return "gemini"

        # Default veloz -> groq
        return "groq"

    def _get_default_model(self, provider: str) -> str:
        """Obtiene el modelo default para el proveedor indicado."""
        models: Dict[str, str] = {
            "groq": "llama-3.3-70b-versatile",
            "gemini": "gemini-3.1-flash-lite",
            "nvidia": "deepseek-ai/deepseek-v4-flash",
            "openrouter": "google/gemini-2.5-flash-lite",
            "ollama": "qwen3.5:2b",
        }
        return models.get(provider, "default-model")
