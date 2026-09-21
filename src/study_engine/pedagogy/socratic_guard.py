"""Socratic Guard with rolling buffer for deterministic code block interception (Fase 5.8 / Refinamiento 2)."""

from dataclasses import dataclass
from typing import List, Optional
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase


@dataclass(frozen=True)
class GuardResult:
    """Result of validating an incoming token or string chunk through SocraticGuard."""

    allowed: bool
    blocked_reason: Optional[str] = None
    emitted_token: str = ""
    replacement_message: Optional[str] = None


class SocraticGuard:
    """Deterministic token-streaming inspector enforcing pedagogical code restrictions."""

    DEFAULT_REPLACEMENT_MESSAGE = (
        "\n\n🛑 **[TALOS SocraticGuard]**\n\n"
        "He bloqueado la generación de código en esta fase. "
        "Recordá nuestro pacto: primero pseudocódigo y diagrama en papel.\n\n"
        "¿Querés que te dé una pista sobre este paso o preferís "
        "intentar el diagrama vos primero?\n\n"
        "*(Si realmente necesitás ver el código, escribí `:solve` o "
        "`DAME LA SOLUCIÓN COMPLETA`)*"
    )

    def __init__(self, contract: PedagogicalContract, window_size: int = 150) -> None:
        self.contract = contract
        self.forbidden_patterns: List[str] = list(contract.forbidden_patterns)
        self.safe_words: List[str] = list(contract.safe_words)
        self.window_size = window_size
        self.buffer: str = ""
        self.is_blocked: bool = False

    def check_user_override(self, user_query: str) -> bool:
        """Check whether the user explicitly used any configured safe word or explicitly requested code/tests."""
        if not user_query:
            return False
        query_upper = user_query.strip().upper()
        for sw in self.safe_words:
            if sw.upper() in query_upper:
                return True

        # Permitir código si el estudiante solicitó expresamente código ejecutable o tests
        import re
        code_request_patterns = [
            r"\b(?:C[OÓ]DIGO|IMPLEMENTACI[OÓ]N|SCRIPT)\s+(?:EN\s+|DE\s+)?(?:PYTHON|C|RUST|BASH)\b",
            r"\b(?:CON\s+)?(?:TESTS?|PYTEST|PRUEBAS?\s+UNITARIAS)\b",
            r"\bC[OÓ]DIGO\s+(?:EN\s+PYTHON\s+)?CON\s+TESTS\b",
            r"\bC[OÓ]DIGO\s+PYTHON\b",
        ]
        for pat in code_request_patterns:
            if re.search(pat, query_upper):
                return True

        return False

    def validate_token(
        self,
        token: str,
        current_phase: ResponsePhase,
        user_query: str,
    ) -> GuardResult:
        """Inspect an incoming token stream.
        
        Maintains a rolling buffer to catch patterns split across arbitrary token boundaries.
        Truncates the stream and injects a socratic intervention upon violation.
        """
        if self.is_blocked:
            return GuardResult(
                allowed=False,
                blocked_reason="STREAM_TERMINATED_AFTER_CODE_BLOCK",
            )

        # If this phase allows code or user has provided a safe word override, permit all tokens
        if current_phase.code_allowed or self.check_user_override(user_query):
            self.buffer += token
            return GuardResult(allowed=True, emitted_token=token)

        self.buffer += token

        # Inspect the buffer for any forbidden pattern
        # Uses full buffer search ensuring patterns spanning arbitrary token slices are caught
        for pattern in self.forbidden_patterns:
            idx = self.buffer.find(pattern)
            if idx != -1:
                self.is_blocked = True
                return GuardResult(
                    allowed=False,
                    blocked_reason="CODE_BLOCK_DETECTED_IN_NON_CODE_PHASE",
                    replacement_message=self.DEFAULT_REPLACEMENT_MESSAGE,
                )

        return GuardResult(allowed=True, emitted_token=token)

    def validate_text(
        self,
        full_text: str,
        current_phase: ResponsePhase,
        user_query: str,
    ) -> GuardResult:
        """Convenience method to inspect a non-streamed full text block."""
        self.reset()
        return self.validate_token(full_text, current_phase, user_query)

    def reset(self) -> None:
        """Reset internal buffer state for a fresh phase or query."""
        self.buffer = ""
        self.is_blocked = False
