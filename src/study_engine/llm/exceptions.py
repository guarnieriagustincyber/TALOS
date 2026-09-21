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
