"""CanonicalPromptAssembler: Prompt construction ensuring invariant cache prefixes (Ola 5, E22, E27).

Order of elements strictly enforced:
1. System Prompt Estático del Cuaderno (Cacheable)
2. Corpus Pack / Secciones Expandidas (Cacheable, deterministic ordering)
3. Instrucciones Dinámicas + Session Briefing (No Cacheable, ~500 tokens, E27)
4. Historial de Chat (No Cacheable)
5. Consulta Actual del Estudiante (No Cacheable)
"""

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Sequence

from study_engine.contracts.generation import GenerationParameters
from study_engine.generation.prompts import PromptBundle, PromptMessage, PromptRole

logger = logging.getLogger(__name__)


class CanonicalPromptAssembler:
    """Assembles prompt bundles preserving the static corpus prefix for provider caching."""

    def __init__(self, notebook_id: str, base_system_prompt: str) -> None:
        self.notebook_id = notebook_id
        self.base_system_prompt = base_system_prompt

    def assemble(
        self,
        user_query: str,
        corpus_pack: str,
        dynamic_instructions: Optional[str] = None,
        session_briefing: Optional[str] = None,
        chat_history: Optional[Sequence[Dict[str, str]]] = None,
        parameters: Optional[GenerationParameters] = None,
    ) -> PromptBundle:
        """Constructs a PromptBundle with strict prefix stability for prompt caching.

        Args:
            user_query: The active student question.
            corpus_pack: Formatted text of expanded chunks with [CHUNK X | Pág Y].
            dynamic_instructions: Style or phase directives (e.g. CASUAL_CHAT, FORMAL).
            session_briefing: Episodic memory brief (e.g. 'Last time you struggled with...').
            chat_history: Prior turns in conversation [{'role': 'user'|'assistant', 'content': '...'}].
            parameters: LLM generation parameters.

        Returns:
            PromptBundle: Configured bundle ready for provider consumption.
        """
        # 1. Static Prefix: System prompt + Corpus pack
        # This block is identical across consecutive turns on the same notebook + corpus pack
        static_system_prefix = (
            f"{self.base_system_prompt.strip()}\n\n"
            f"=== EVIDENCIAS DOCUMENTADAS AUTORIZADAS DEL CUADERNO [{self.notebook_id}] ===\n"
            f"{corpus_pack.strip() if corpus_pack else 'NO_EVIDENCE_PACKED'}"
        )

        # 2. Dynamic Post-Corpus block (E27): Briefing + Adaptive instructions
        dynamic_parts: List[str] = []
        if dynamic_instructions and dynamic_instructions.strip():
            dynamic_parts.append(f"=== DIRECTIVA DE ESTILO Y FASE ===\n{dynamic_instructions.strip()}")
        if session_briefing and session_briefing.strip():
            dynamic_parts.append(f"=== RESUMEN EPISÓDICO DE SESIÓN PREVIA ===\n{session_briefing.strip()}")

        dynamic_block = "\n\n".join(dynamic_parts)

        # Build messages sequence
        messages: List[PromptMessage] = []

        # If dynamic instructions exist, inject as system/assistant guidance in the dialogue
        if dynamic_block:
            messages.append(
                PromptMessage(
                    role=PromptRole.ASSISTANT,
                    content=f"[Contexto Operativo del Tutor]:\n{dynamic_block}",
                )
            )

        # 3. Conversational History
        if chat_history:
            for turn in chat_history:
                role_str = turn.get("role", "user").lower()
                role_enum = PromptRole.ASSISTANT if role_str in ("assistant", "tutor") else PromptRole.USER
                content = turn.get("content", "").strip()
                if content:
                    messages.append(PromptMessage(role=role_enum, content=content))

        # 4. Active User Query
        messages.append(PromptMessage(role=PromptRole.USER, content=user_query.strip()))

        # Compute deterministic prompt hash
        h = hashlib.sha256()
        h.update(static_system_prefix.encode("utf-8"))
        for m in messages:
            h.update(f"{m.role.value}:{m.content}".encode("utf-8"))
        prompt_hash = h.hexdigest()

        # Compute static prefix hash for caching verification
        prefix_hash = hashlib.sha256(static_system_prefix.encode("utf-8")).hexdigest()

        params = parameters or GenerationParameters(
            temperature=0.2,
            max_output_tokens=2048,
        )

        bundle = PromptBundle(
            system_prompt=static_system_prefix,
            messages=tuple(messages),
            parameters=params,
            prompt_hash=prompt_hash,
        )
        # Use object.__setattr__ to bypass frozen Pydantic model for internal telemetry
        object.__setattr__(bundle, "prefix_hash", prefix_hash)
        return bundle
