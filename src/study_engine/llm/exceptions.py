"""Authoritative exceptions for LLM backends in Subsystem S4.3."""


class LLMError(Exception):
    """Base exception for all LLM subsystem failures."""

    pass


class LLMBackendError(LLMError):
    """Raised when an external or local generation backend fails."""

    pass


class LLMTimeoutError(LLMBackendError):
    """Raised when backend inference exceeds configured timeout."""

    pass


class LLMConnectionError(LLMBackendError):
    """Raised when backend connection cannot be established."""

    pass


class ContextBudgetExceededError(LLMError):
    """Raised when context payload exceeds C3 effective hard ceiling (4761 tokens)."""

    def __init__(
        self,
        message: str,
        estimated_tokens: int = 0,
        effective_ceiling: int = 4761,
        raw_characters: int = 0,
    ) -> None:
        super().__init__(message)
        self.estimated_tokens = estimated_tokens
        self.effective_ceiling = effective_ceiling
        self.raw_characters = raw_characters

